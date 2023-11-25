"""
Tools for extracting data from statcast.mlb.com

Disclaimer:
    The author of this source code is not affiliated with Major League Baseball in any way.
    The use of statcast.mlb.com is subject to any terms and conditions posted on statcast.mlb.com.

Note the following with regard to function names used throughout this module:
    Function names prefixed with...
    'get_' are used to make HTTP GET calls to retrieve data from a web resource.
    'download_' are used to (directly or indirectly) call a 'get_' function,
        modify the content if necessary, and save it to a file.
    'load_' are used to load saved web content from a file into a python object.
"""
import datetime
import logging
import requests

from dataclasses import dataclass
from urllib.parse import urlencode, urljoin

from mlb.statsapi import statsapi


URL = "https://baseballsavant.mlb.com"
STATCAST_SEARCH_MAX_ROWS = 25000


@dataclass
class SeasonTypesParam:
    """
    Class representation of the 'Season Type' filters on the statcast_search website.

    Each 'Season Type' value is represented as a boolean attribute of the class.
    All attributes being set to False is equivalent to no filters being selected on the
    website interface - which is functionally equivalent to all attributes being set to True.
    """
    regular: bool = False
    playoffs: bool = False
    wildcard: bool = False
    division_series: bool = False
    league_championship: bool = False
    world_series: bool = False
    spring_training: bool = False

    @classmethod
    def build_from_game_type_code(cls, game_type_code: str):
        """
        Builds a new instance of a SeasonTypesParam class, with a single season type.

        Parameters:
            game_type_code (str): A game type code from the statsapi module. An invalid
                game type code will have the effect of setting all game type attributes
                in the new class instance to False - which means no 'Season Type' filter
                will be applied if this param is used for a statcast search.
        """
        return cls(
            regular=(game_type_code == statsapi.GAME_TYPE_CODE_REGULAR),
            playoffs=False,
            wildcard=(game_type_code == statsapi.GAME_TYPE_CODE_WILDCARD),
            division_series=(game_type_code == statsapi.GAME_TYPE_CODE_DIV_SERIES),
            league_championship=(game_type_code == statsapi.GAME_TYPE_CODE_LCS),
            world_series=(game_type_code == statsapi.GAME_TYPE_CODE_WS),
            spring_training=(game_type_code == statsapi.GAME_TYPE_CODE_PRESEASON)
        )

    def to_string(self):
        """Generate the query param value to be included in the request url"""
        delimiter = "|"
        val = ""
        if self.regular:
            val = f"{statsapi.GAME_TYPE_CODE_REGULAR}{delimiter}"

        if self.playoffs:
            # There is no statsapi gameType parameter for 'playoffs'
            val = f"{val}PO{delimiter}"

        if self.wildcard:
            val = f"{val}{statsapi.GAME_TYPE_CODE_WILDCARD}{delimiter}"

        if self.division_series:
            val = f"{val}{statsapi.GAME_TYPE_CODE_DIV_SERIES}{delimiter}"

        if self.league_championship:
            val = f"{val}{statsapi.GAME_TYPE_CODE_LCS}{delimiter}"

        if self.world_series:
            val = f"{val}{statsapi.GAME_TYPE_CODE_WS}{delimiter}"

        if self.spring_training:
            val = f"{val}{statsapi.GAME_TYPE_CODE_PRESEASON}{delimiter}"

        return val


@dataclass
class PitchResultTypesParam:
    """
    Class representation of the 'Pitch Result' filters on the statcast_search website.

    The site offers 16 different result types. The url generated when all are selected will include this:

    hfPR=foul%7Cfoul%5C.%5C.bunt%7Cbunt%5C.%5C.foul%5C.%5C.tip%7Cfoul%5C.%5C.pitchout%7Cpitchout%7Chit%5C.%5C.by%5C.%5C.pitch%7Cintent%5C.%5C.ball%7Cmissed%5C.%5C.bunt%7Cfoul%5C.%5C.tip%7Cswinging%5C.%5C.pitchout%7Cswinging%5C.%5C.strike%7Cswinging%5C.%5C.strike%5C.%5C.blocked%7C&

    Note however that the above is functionally equivalent to having selected NONE of the result types, eg, "hfPR=&".
    This gets tricky to represent in terms of individual class attributes being set to True or False.
    As of this writing though, for our purposes, we are only interested in getting either 'all pitches' or
    'batted ball events only' so we'll design for that simple use case.
    """

    batted_ball_events_only: bool = False
    # hit_into_play: bool = False
    # ball: bool = False
    # ball_in_dirt: bool = False
    # called_strike: bool = False

    def to_string(self):
        """Generate the query param value to be included in the request url"""
        delimiter = "|"
        val = ""
        if self.batted_ball_events_only:
            val = f"hit\\.\\.into\\.\\.play{delimiter}"

        # if self.ball:
        #     val = f"{val}ball{delimiter}"
        #
        # if self.ball_in_dirt:
        #     # "blocked%5C.%5C.ball%7C"
        #     val = f"{val}blocked\\.\\.ball{delimiter}"
        #
        # if self.called_strike:
        #     # "called%5C.%5C.strike%7C"
        #     val = f"{val}called\\.\\.strike{delimiter}"

        return val


@dataclass
class StatcastSearchParams:
    """
    Statcast search url query params class.

    The https://baseballsavant.mlb.com/statcast_search web page offers many search parameters,
    which then get translated into url query params for the HTTP request sent to the server
    to execute the search. The initial design of this class only accommodates a limited set of basic
    search use cases. If new use cases for more searches arise, the class can be extended to
    accommodate them.

    Parameter values can be determined by visiting the statcast_search web page and observing
    the urls that are generated after clicking the "Search" button. Those urls include all
    the search parameters that were sent to the server.
    For example, suppose you want to run a search from the web page for "Season Type" = "Regular Season".
    Select "Regular Season" for "Season Type", run the search, and note the url after the
    results are returned. You will find among the query parameters "hfGT=R%7C". "hfGT" is the code
    for "Season Type". "R" is the value code for "Regular Season", and "%7C" is the url-encoded "|" delimiter.
    This class will generate a dictionary of UNENCODED query params from more human-readable class attributes.

    Here are all url query params available from the website:
        'all'
        'hfPT'
        'hfAB'
        'hfGT'
        'hfPR'
        'hfZ'
        'stadium'
        'hfBBL'
        'hfNewZones'
        'hfPull'
        'hfC'
        'hfSea'
        'hfSit'
        'player_type'
        'hfOuts'
        'opponent'
        'pitcher_throws'
        'batter_stands'
        'hfSA'
        'game_date_gt'
        'game_date_lt'
        'hfInfield'
        'team'
        'position'
        'hfOutfield'
        'hfRO'
        'home_road'
        'hfFlag'
        'hfBBT'
        'metric_1'
        'hfInn'
        'min_pitches'
        'min_results'
        'group_by'
        'sort_col'
        'player_event_sort'
        'sort_order'
        'min_pas'
        'type'
    """

    def __init__(
            self,
            start_date_iso: str,
            end_date_iso: str,
            season_types: SeasonTypesParam,
            pitch_result_types: PitchResultTypesParam,
            group_by: str = "",
            result_type: str = ""
    ):
        try:
            if start_date_iso:
                datetime.datetime.strptime(start_date_iso, "%Y-%m-%d")

            if end_date_iso:
                datetime.datetime.strptime(end_date_iso, "%Y-%m-%d")
        except ValueError as exc:
            logging.error(exc)
            raise

        self.start_date_iso = start_date_iso
        self.end_date_iso = end_date_iso
        self.season_types = season_types
        self.pitch_result_types = pitch_result_types
        self.group_by = group_by
        self.result_type = result_type

    def to_dict(self):
        """Collect the string representations of all of our parameters into a dictionary"""
        return {
            "all": "true",
            "game_date_gt": self.start_date_iso,
            "game_date_lt": self.end_date_iso,
            "hfGT": self.season_types.to_string(),
            "hfPR": self.pitch_result_types.to_string(),
            "group_by": self.group_by,
            "type": self.result_type
        }


class StatcastSearch:
    """
    Class to execute statcast searches via HTTP request.
    Implemented as a context manager to enable the user to use in a 'with'
    statement without concern for tear down.
    """
    def __init__(self, use_session: bool = False):
        """
        Initialize the class. The user has the option to use a requests Session,
        which may be ideal for making repeated requests.

        Parameters
            use_session (bool): Optional, defaults to False
        """
        self.session = None
        self.get = requests.get

        if use_session:
            self.session = requests.Session()
            self.get = self.session.get

    def __enter__(self):
        """Implement the context manager protocol"""
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Implement the context manager protocol. Ensure the session object is closed."""
        if self.session:
            self.session.close()

    def __del__(self):
        """Ensure the session object gets closed when the class instance is disposed"""
        if self.session:
            self.session.close()

    def get_statcast_search_data(self, search_params: StatcastSearchParams, max_retries: int = 0) -> bytes:
        """
        Execute a statcast search via HTTP request and return the byte content.

        Parameters:
            search_params (StatcastSearchParams): the search parameters
            max_retries (int): Optional, defaults to 0. The maximum number of times to retry a request if it fails.

        Raises:
            HTTPError if request returns an unsuccessful status code, and we've reached maximum number of retries.

        Returns:
            bytes: Response byte content
        """
        url = f"{urljoin(URL, 'statcast_search/csv')}?{urlencode(search_params.to_dict())}"
        attempt = 0

        while True:
            attempt += 1
            logging.info("Sending statcast search request to %s. Attempt %d of %d." % (url, attempt, max_retries + 1))
            resp = self.get(url)
            if resp.status_code == 200:
                return resp.content
            else:
                if resp.status_code == 524 and attempt <= max_retries:
                    logging.warning("Request to %s failed with status_code 524. Retrying." % url)
                else:
                    resp.raise_for_status()


def run_pitch_data_search(
        search_params: StatcastSearchParams,
        statcast_search: StatcastSearch = StatcastSearch()
) -> bytes:
    """
    Configure and execute a statcast pitch data search, which returns individual pitch events.

    Parameters:
        search_params (StatcastSearchParams): The search parameters
        statcast_search (StatcastSearch): Optional, defaults to new instance.
                                          The user may wish to reuse an existing requests Session.

    Returns:
        The search results, as byte content returned from the HTTP call
    """
    search_params.group_by = ""
    search_params.result_type = "details"

    return statcast_search.get_statcast_search_data(search_params, max_retries=2)


def run_pitch_count_search(
        search_params: StatcastSearchParams,
        statcast_search: StatcastSearch = StatcastSearch()
) -> bytes:
    """
    Configure and execute a statcast pitch count search, which returns total
    pitch counts aggregated by team and game.

    Parameters:
        search_params (StatcastSearchParams): The statcast search parameters.
        statcast_search (StatcastSearch): Optional, defaults to new instance.
                                          The user may wish to reuse an existing requests Session.

    Returns:
        The search results, as byte content returned from the HTTP call
    """
    search_params.group_by = "team-date"
    search_params.result_type = ""
    return statcast_search.get_statcast_search_data(search_params)
