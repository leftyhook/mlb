import datetime
import os
import logging
import numpy
import pandas
import requests

from io import BytesIO

from mlb.statcast.statcast_search import STATCAST_SEARCH_MAX_ROWS

from mlb.statcast.statcast_search import SeasonTypesParam
from mlb.statcast.statcast_search import PitchResultTypesParam
from mlb.statcast.statcast_search import StatcastSearchParams
from mlb.statcast.statcast_search import StatcastSearch

from mlb.statcast.statcast_search import run_pitch_count_search
from mlb.statcast.statcast_search import run_pitch_data_search


from mlb.statsapi import statsapi
from mlb.stats import woba
from mlb.utils.file_utils import is_file_stale
from mlb.utils.file_utils import csv_row_count_check
from mlb.schedule import Schedule


FILE_PREFIX_PITCH_DATA = "PitchData"

all_pitches_param = PitchResultTypesParam(batted_ball_events_only=False)
bbe_only_param = PitchResultTypesParam(batted_ball_events_only=True)


def get_pitch_count_data(search_params: StatcastSearchParams) -> pandas.DataFrame:
    """
    Runs a statcast pitch count search and loads the results into a sorted dataframe

    Parameters:
        search_params(StatcastSearchParams): The search parameters
    Returns:
        pandas.DataFrame: The pitch count data, sorted by game id
    """
    pitch_count_data = run_pitch_count_search(search_params)
    df = pandas.read_csv(BytesIO(pitch_count_data))
    df.sort_values(
        by="game_pk",
        ascending=True,
        inplace=True,
    )
    return df


def get_pitch_counts_by_date(search_params: StatcastSearchParams) -> pandas.DataFrame:
    """
    Summarizes pitch count data by game date, giving us the total number of pitch events for each day

    Parameters:
        search_params(StatcastSearchParams): The search parameters

    Returns:
        pandas.DataFrame: The summarized pitch count data, sorted by game date
    """
    df = get_pitch_count_data(search_params)
    game_dates_df = (
        df.groupby(["game_date"])["pitches"].sum().reset_index()
    )
    game_dates_df.sort_values(by="game_date", inplace=True)

    return game_dates_df


def build_pitch_count_summary(
        start_date_iso: str,
        end_date_iso: str,
        season_types_param: SeasonTypesParam
) -> pandas.DataFrame:
    """
    Generates a dataframe that includes counts of non-batted ball and
    batted ball events for each game date from start_date to end_date.

    Parameters:
        start_date_iso (str): The iso-formatted first date we want data for
        end_date_iso (str): The iso-formatted last date we want data for
        season_types_param (SeasonTypesParam): The 'Season Types' we want to include in our results.
            Note that without this, a date range which includes the date of the All-Star Game would
            have the All-Star Game pitch count included in the results.

    Returns:
        pandas.DataFrame: The pitch count summary table
    """
    params = StatcastSearchParams(
        start_date_iso,
        end_date_iso,
        season_types_param,
        all_pitches_param
    )

    game_date_pitch_counts_df = get_pitch_counts_by_date(params)

    params.pitch_result_types = bbe_only_param
    game_date_bbe_counts_df = get_pitch_counts_by_date(params)
    game_date_bbe_counts_df.rename(columns={"pitches": "bbe"}, inplace=True)

    return pandas.merge(game_date_pitch_counts_df, game_date_bbe_counts_df, how="left")


def download_game_pitch_counts(
        file_path: str,
        search_params: StatcastSearchParams
):
    """
    Run a statcast pitch count search and save the results to a csv file.

    Parameters:
        file_path (str): The file path to save the csv to.
        search_params (StatcastSearchParams): The statcast search parameters.
    """
    df = get_pitch_count_data(search_params)
    df.to_csv(file_path, index=False)


def load_daily_pitch_count_summary(file_path: str) -> pandas.DataFrame:
    """
    Load a csv file of pitch counts per team per game into a dataframe,
    summarize by game date and pitch count, sort and return the frame.

    Parameters:
        file_path (str): The path to the csv file.

    Returns:
        pandas.DataFrame: The sorted, summarized dataframe.
    """
    df = pandas.read_csv(file_path)
    game_dates_df = (
        df.groupby(["game_date"])["pitches"].sum().reset_index()
    )
    game_dates_df.sort_values(by="game_date", inplace=True)

    return game_dates_df


def clean_pitch_data(pitch_data_df: pandas.DataFrame, woba_const_history: woba.WOBAConstantHistory):
    """
    Update data retrieved from statcast search for accuracy.

    The 'woba_value' column in the statcast search results contains rounded, static estimates
    which vary by a few decimal places from the woba constants actually used to calculate a
    player's wOBA and wOBACon. These values need to be updated with accurate constants from
    a trusted source - which will probably always be fangraphs.

    Data cleaning steps to implement, in order:
    1. Replace blank woba_denom with 1 where woba_value >= 0
    2. Replace woba_denom with 0 for catcher's interference events
    3. Replace woba_value with constants from woba_const_history
    4. Replace woba_value with 0 where 'events' not in ['walk', 'hit_by_pitch', 'single','double','triple','home_run']
    5. Update 'estimated_woba_using_speedangle' to woba constants for 'events' in ['walk', 'hit_by_pitch']

    The data set could theoretically be quite large, so we are updating the
    dataframe in-place rather than making a copy and returning it.

    Parameters:
        pitch_data_df (pandas.DataFrame): The pitch data to clean. We are somewhat lazily assuming that the
            dataframe does indeed include pitch data retrieved from statcast search, and that all columns
            referenced in the code below are actually present.
        woba_const_history (woba.WOBAConstantHistory): The typical use case will only be searching for data
            from a single season, but date ranges spanning multiple seasons are possible.
            We therefore make WOBA constants from all MLB seasons available.
    """
    pitch_data_df.loc[(pitch_data_df["woba_value"] >= 0) & (pitch_data_df["woba_denom"].isnull()), "woba_denom"] = 1
    pitch_data_df.loc[(pitch_data_df["events"].eq("catcher_interf")), "woba_denom"] = 0

    get_const_vec = numpy.vectorize(woba_const_history.get_constant_for_event)
    pitch_data_df["woba_value"] = get_const_vec(pitch_data_df["game_date"].str[0:4], pitch_data_df["events"])

    pitch_data_df["estimated_woba_using_speedangle"] = numpy.where(
        numpy.isin(pitch_data_df["events"], ["walk", "hit_by_pitch"]),
        pitch_data_df["woba_value"],
        pitch_data_df["estimated_woba_using_speedangle"],
    )


class PitchDataDownloadManager:
    """
    The PitchDataDownloadManager class organizes and executes the statcast pitch data search
    requests required to obtain all pitch data (organized as a single cumulative batted ball
    event file and one non-batted ball event file per individual game date) between two dates.

    Note that the batted ball event file may contain event data from other dates outside our
    date range, but only the data for our date range will be updated by this class.

    Attributes:
        start_date_iso (str): The iso-formatted first date we want data for.
        end_date_iso (str): The last date we want data for.
        stale_by_date (datetime.date): A file is considered to be stale if it was created on or before this date.
        pitch_data_dir (str): The directory where all our non-BBE files will be written.
        bbe_data_file_path (str): The fully qualified path to the master BBE data file.
            There is no reason this file cannot reside in the pitch_data_dir.
        season_types_param (SeasonTypesParam): The 'Season Types' we want game data for.
        pitch_count_summary_df (pandas.DataFrame): A dataframe that includes counts of non-batted ball and
            batted ball events for each game date from start_date to end_date, delivered from statcast. This
            tells us how many rows we should expect to be returned for each game date in our pitch data search results.
    """

    def __init__(
            self,
            start_date: datetime.date,
            end_date: datetime.date,
            stale_by_date: datetime.date,
            pitch_data_dir: str,
            bbe_data_file_path: str,
            season_types_param: SeasonTypesParam
    ):
        """
        Initialize the PitchDataDownloadManager class.

        Parameters:
            start_date (datetime.date): The first date we want data for.
            end_date (datetime.date): The last date we want data for.
            stale_by_date (datetime.date): A file is considered to be stale if it was created on or before this date.
            pitch_data_dir (str): The directory where all our non-BBE files will be written.
            bbe_data_file_path (str): The fully qualified path to the master BBE data file.
                There is no reason this file cannot reside in the pitch_data_dir.
            season_types_param (SeasonTypesParam): The 'Season Types' we want game data for.
        """
        if not os.path.exists(pitch_data_dir):
            raise FileNotFoundError("The provided pitch data directory '%s' does not exist." % pitch_data_dir)

        self.start_date = start_date
        self.start_date_iso = start_date.isoformat()
        self.end_date = end_date
        self.end_date_iso = end_date.isoformat()
        self.stale_by_date = stale_by_date
        self.pitch_data_dir = pitch_data_dir
        self.bbe_data_file_path = bbe_data_file_path
        self.season_types_param = season_types_param
        self.pitch_count_summary_df = build_pitch_count_summary(
            self.start_date_iso, self.end_date_iso, season_types_param
        )

        logging.debug(
            "PitchDataDownloadManager object created for dates from %s to %s. Season type param "
            "is %s. Pitch data directory is %s. Batted ball event file path is %s" %
            (
                self.start_date_iso,
                self.end_date_iso,
                self.season_types_param.to_string(),
                self.pitch_data_dir,
                self.bbe_data_file_path
            )
        )

    def bbe_download_summary(self) -> dict[str, int]:
        """
        Loads the batted ball event file and counts the number of rows per game date.
        If the batted ball event file is stale, we declare no data to have been downloaded.

        Returns:
            dict[str, int]: Dictionary with game date strings as keys and pitch counts as values.
        """
        summary = {}
        if os.path.exists(self.bbe_data_file_path):
            if not is_file_stale(self.bbe_data_file_path, self.stale_by_date):
                df = pandas.read_csv(self.bbe_data_file_path)
                summary_df = df.groupby(["game_date"])["game_pk"].count().reset_index(name="bbe")
                summary = dict(zip(summary_df["game_date"], summary_df["bbe"]))

        return summary

    def non_bbe_file_path(self, game_date_str: str) -> str:
        """
        Returns a standardized path to a non-batted ball event file
        in the pitch data directory for a given game date.

        Parameters:
            game_date_str (str): A game date string

        Returns:
            str: The fully qualified file path.
        """
        return os.path.join(self.pitch_data_dir, f"{FILE_PREFIX_PITCH_DATA}.NonBBE.{game_date_str}.csv")

    def valid_non_bbe_files_by_date(self) -> pandas.DataFrame:
        """
        The full file path to each valid non-BBE file, listed by date.

        Checking the status of non-BBE downloads is a time-consuming operation.
        Each non-bbe file gets opened and has its row count checked to ensure it aligns
        with the pitch counts statcast says it's supposed to have. A date with a missing
        non-bbe file or incorrect row count will be marked as not having a file.

        Returns:
            pandas.DataFrame: a dataframe of game dates in our date range and the
                full file path to the non-BBE data for that date, if such a file
                exists and contains the expected number of rows.
        """
        df = self.pitch_count_summary_df[["game_date", "pitches", "bbe"]]
        df["non_bbe_file"] = df.apply(
            lambda x: self.non_bbe_file_path(x["game_date"])
            if csv_row_count_check(
                self.non_bbe_file_path(x["game_date"]), x["pitches"] - x["bbe"]
            ) else None,
            axis=1
        )
        return df[["game_date", "non_bbe_file"]]

    def non_bbe_file_list(self):
        """Returns a list of all valid and up-to-date non-batted ball event files for our date range."""
        df = self.valid_non_bbe_files_by_date()
        return df.loc[df["non_bbe_file"].notnull(), "non_bbe_file"].tolist()

    def game_date_download_status(self) -> pandas.DataFrame:
        """
        Presents the download status of batted and non-batted ball
        events for all dates from our start_date to our end_date.

        Status of non-BBE downloads is determined by examining the list
        of available valid non-BBE files.

        Checking the status of BBE data is done by examining the batted ball
        event download summary, and comparing the event counts to the counts
        statcast_search says we should have for each date.

        Returns:
            pandas.DataFrame: A dataframe including columns for game_date, file path to
                              non-BBE data for that date (if it exists), and true/false
                              values denoting whether BBE data has been downloaded for each date.
        """
        df = self.pitch_count_summary_df.copy(deep=True)

        bbe_summary = self.bbe_download_summary()
        df["bbe_downloaded"] = df.apply(lambda x: x["bbe"] == bbe_summary.get(x["game_date"], 0), axis=1)

        non_bbe_files = self.valid_non_bbe_files_by_date()
        return pandas.merge(df, non_bbe_files, how="left", on="game_date")

    def game_date_download_plan(self) -> pandas.DataFrame:
        """
        Building off of the 'game date download status' dataframe, this function determines if any of
        the game dates needs to have any of 'all pitches' or batted ball events downloaded.

        Downloading all pitches for a date will include batted ball event data as well,
        so a separate batted ball event search does not need to be run for that date.

        Returns:
             pandas.DataFrame: A dataframe with a row for each game date. Includes boolean columns
                'download_all' and 'download_bbe'.
        """
        df = self.game_date_download_status()

        df["download_all"] = df.apply(lambda x: x["non_bbe_file"] is None, axis=1)
        df["download_bbe"] = ((~df["download_all"]) & ~df["bbe_downloaded"])

        return df

    def download_pitch_data(
            self,
            search_params: StatcastSearchParams,
            statcast_search: StatcastSearch = StatcastSearch()
    ):
        """
        Run a pitch data search with the given parameters, and dump the results to the
        appropriate file(s) based on whether the data is for batted ball events or not.

        Parameters:
            search_params (StatcastSearchParams): The statcast search parameters.
            statcast_search (StatcastSearch): Optional, defaults to new instance.
                The user may wish to reuse an existing requests Session.
        """
        pitch_data = run_pitch_data_search(search_params, statcast_search)

        df = pandas.read_csv(BytesIO(pitch_data))
        df.sort_values(
            by=["game_pk", "at_bat_number", "pitch_number"],
            ascending=[False, True, True],
            inplace=True,
        )

        game_dates = df["game_date"].unique().tolist()

        # Dump non-BBE data to a file for each date
        if not search_params.pitch_result_types.batted_ball_events_only:
            for game_date in game_dates:
                game_date_df = df.loc[(df["game_date"] == game_date) & df["description"].ne("hit_into_play")]
                game_date_df.to_csv(self.non_bbe_file_path(game_date), index=False)

        # Add BBE data to the master BBE file, replacing any existing data for each date
        bbe_df = df.loc[(df["description"].eq("hit_into_play"))]
        if os.path.exists(self.bbe_data_file_path):
            master_bbe_df = pandas.read_csv(self.bbe_data_file_path)
            bbe_df = pandas.concat([master_bbe_df.loc[~(master_bbe_df["game_date"].isin(game_dates))], bbe_df])

        bbe_df.sort_values(
            by=["game_pk", "at_bat_number", "pitch_number"],
            ascending=[False, True, True],
            inplace=True,
        )
        bbe_df.to_csv(self.bbe_data_file_path, index=False)

    def execute(self):
        """
        Download the pitch data necessary to complete the data set for our date range.

        Unless we can figure out how to recalculate xWOBA daily by implementing a reasonable
        version of the calculation described here...
        https://technology.mlblogs.com/an-introduction-to-expected-weighted-on-base-average-xwoba-29d6070ba52b
        ...we need to refresh batted ball event data from statcast every day, as their calculation
        of 'estimated_woba_using_speedangle' will update as more batted ball events are
        recorded over the course of the season. Non-batted ball event data, however, should
        only need to be downloaded once and saved locally for future access. We optimize our
        statcast searches accordingly.

        If this program is being run daily throughout the course of an MLB season, with no days
        missed, then we will see each day only one new file created (for the previous day's non-BBE data),
        and the master BBE data file rebuilt from the ground up with the most up-to-date
        statcast 'expected'/'estimated' measurements.

        As an added wrinkle, statcast caps the amount of rows it returns at 25,000, which
        will prevent us from downloading all pitches for date ranges wider than about 5-6 days
        (~300 pitches/game x ~15 games/day x 5 days = 22,500 pitches) at one time.
        In order to retrieve our full data set, we will need to divide our date range into
        a set of smaller ranges and run a search for each one, and combine all the
        smaller data sets into one at the end.
        We do this with the added goal of making as few HTTP requests as possible.
        """
        plan_df = self.game_date_download_plan()

        if len(plan_df.loc[plan_df["download_all"] | plan_df["download_bbe"]]) == 0:
            logging.info("No new data to download.")
            return

        logging.debug(
            "PitchDataDownloadManager download plan for dates from %s to %s:\n %s" %
            (self.start_date_iso, self.end_date_iso, plan_df.to_string())
        )

        search_plans = [
            {
                "download_col": "download_all",
                "pitch_count_col": "pitches",
                "pitch_count": 0,
                "params": StatcastSearchParams(
                    start_date_iso="",
                    end_date_iso="",
                    season_types=self.season_types_param,
                    pitch_result_types=all_pitches_param,
                )
            },
            {
                "download_col": "download_bbe",
                "pitch_count_col": "bbe",
                "pitch_count": 0,
                "params": StatcastSearchParams(
                    start_date_iso="",
                    end_date_iso="",
                    season_types=self.season_types_param,
                    pitch_result_types=bbe_only_param,
                )
            }
        ]

        download_errors = 0
        with (StatcastSearch(use_session=True) as statcast_search):
            for day_num in range(len(plan_df)):
                for plan in search_plans:
                    pitch_count_col = plan["pitch_count_col"]
                    try:
                        if plan_df.loc[day_num, plan["download_col"]]:
                            if (
                                    plan["pitch_count"] +
                                    plan_df.loc[day_num, pitch_count_col] >
                                    STATCAST_SEARCH_MAX_ROWS
                            ):
                                self.download_pitch_data(plan["params"], statcast_search)

                                plan["pitch_count"] = plan_df.loc[day_num, pitch_count_col]
                                plan["params"].start_date_iso = plan_df.loc[day_num, "game_date"]
                            else:
                                plan["pitch_count"] += plan_df.loc[day_num, pitch_count_col]

                            plan["params"].end_date_iso = plan_df.loc[day_num, "game_date"]
                            if not plan["params"].start_date_iso:
                                plan["params"].start_date_iso = plan["params"].end_date_iso

                            if day_num == len(plan_df) - 1:
                                self.download_pitch_data(plan["params"], statcast_search)

                        elif plan["params"].start_date_iso:
                            self.download_pitch_data(plan["params"], statcast_search)

                            plan["pitch_count"] = 0
                            plan["params"].start_date_iso = ""
                            plan["params"].end_date_iso = ""
                    except requests.RequestException as req_exc:
                        download_errors += 1
                        logging.error("Statcast search raised exception %s." % req_exc)
                        logging.error("Logging error and proceeding with any remaining searches.")

        if download_errors:
            raise RuntimeError("PitchDataDownloadManager download execution plan completed, "
                               "but with errors. See previous log entries.")

    def combine_all_data(self) -> pandas.DataFrame:
        """
        Assembles all downloaded data for the date range into a single data frame
        """
        frames = [pandas.read_csv(file_path) for file_path in self.non_bbe_file_list()]

        bbe_data = pandas.read_csv(self.bbe_data_file_path)
        frames.append(
            bbe_data[
                bbe_data["game_date"].between(self.start_date_iso, self.end_date_iso)
            ]
        )
        full_df = pandas.concat(frames)

        full_df.sort_values(
            by=["game_pk", "at_bat_number", "pitch_number"],
            ascending=[False, True, True],
            inplace=True,
        )
        return full_df


class SeasonPitchData:
    """
    The SeasonPitchData class enables a user to acquire the statcast pitch data for a given MLB season.

    Attributes:
        season (int): The year of the MLB season.
        game_type_code (str): A game type code from the statsapi module.
        game_type (str): The game type code translated to a word. Used for file naming.
        season_types_param (SeasonTypesParam): A SeasonTypesParam derived from the game_type_code.
            Used for all searches.
        schedule (schedule.Schedule): The schedule for the season and game_type_code.
        stale_by_date (datetime.date): A file is considered to be stale if it was created on or before this date.
        pitch_data_dir (str): The directory where all our files will be written.
        pitch_data_file_name (str): The name of the master pitch data file.
        pitch_data_file_path (str): The fully qualified path to the master pitch data file.
        bbe_data_file_name (str): The name of the file where batted ball event data will be written.
        bbe_data_file_path (str): The fully qualified path to the master BBE data file.
        download_manager (PitchDataDownloadManager): The PitchDataDownloadManager responsible for acquiring the data.
    """

    def __init__(self, season: int, game_type_code: str, pitch_data_dir: str):
        """
        Initialize the SeasonPitchData class, ultimately constructing the PitchDataDownloadManager
        that will execute our statcast searches and write the results to files.

        Parameters:
            season (int): The year of the MLB season.
            game_type_code (str): A game type code from the statsapi module.
            pitch_data_dir (str): The directory where all our files will be written.
        """
        if not statsapi.is_valid_mlb_season(season):
            raise ValueError("%d is not a valid MLB season.")

        if statsapi.game_type_str(game_type_code) == "Unknown":
            raise ValueError("%s is not a recognized game type code." % game_type_code)

        if not os.path.exists(pitch_data_dir):
            raise FileNotFoundError("The provided pitch data directory '%s' does not exist." % pitch_data_dir)

        self.season = season
        self.game_type_code = game_type_code
        self.game_type = statsapi.game_type_str(self.game_type_code)
        self.season_types_param = SeasonTypesParam.build_from_game_type_code(self.game_type_code)
        self.schedule = Schedule(season, game_type_code)
        self.stale_by_date = self.schedule.most_recent_game_date
        self.pitch_data_dir = pitch_data_dir
        self.pitch_data_file_name = f"{FILE_PREFIX_PITCH_DATA}.{self.season}.{self.game_type}.csv"
        self.pitch_data_file_path = os.path.join(self.pitch_data_dir, self.pitch_data_file_name)
        self.bbe_data_file_name = f"{FILE_PREFIX_PITCH_DATA}.BBE.{self.season}.{self.game_type}.csv"
        self.bbe_data_file_path = os.path.join(self.pitch_data_dir, self.bbe_data_file_name)

        self.download_manager = PitchDataDownloadManager(
            self.schedule.opening_day_date,
            self.schedule.most_recent_game_date,
            self.stale_by_date,
            self.pitch_data_dir,
            self.bbe_data_file_path,
            self.season_types_param
        )

        logging.debug(
            "SeasonPitchData object created for the %d season. "
            "Season type is '%s'. Pitch data directory is %s" %
            (self.season, self.game_type, self.pitch_data_dir)
        )

    def refresh(self, woba_const_history: woba.WOBAConstantHistory):
        """
        Refresh the pitch data in the pitch data directory.

        Parameters:
            woba_const_history (woba.WOBAConstantHistory): The WOBA values to overwrite the rounded
                'estimated_woba' column data with.
        """
        logging.info("Refreshing data for the %d season." % self.season)
        try:
            self.download_manager.execute()
        except Exception as exc:
            logging.error(exc)
            logging.error("Aborting remaining SeasonPitchData refresh steps.")
            raise

        logging.info("%d pitch data download complete. Generating master data file." % self.season)
        full_df = self.download_manager.combine_all_data()
        clean_pitch_data(full_df, woba_const_history)
        full_df.to_csv(self.pitch_data_file_path, index=False)
        logging.info("%d pitch data written to %s" % (self.season, self.pitch_data_file_path))
