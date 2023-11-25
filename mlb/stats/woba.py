import csv

from dataclasses import dataclass
from datetime import datetime, date

from mlb.fangraphs import fangraphs
from mlb.utils.file_utils import is_file_stale


@dataclass
class SeasonWOBAConstants:
    """Data class holding the WOBA constants for a single season."""
    season: int
    league_woba: float
    woba_scale: float
    weight_BB: float
    weight_HBP: float
    weight_1B: float
    weight_2B: float
    weight_3B: float
    weight_HR: float

    @classmethod
    def load_from_dict(cls, season_constants: dict):
        return cls(
            season=int(season_constants["Season"]),
            league_woba=float(season_constants["wOBA"]),
            woba_scale=float(season_constants["wOBAScale"]),
            weight_BB=float(season_constants["wBB"]),
            weight_HBP=float(season_constants["wHBP"]),
            weight_1B=float(season_constants["w1B"]),
            weight_2B=float(season_constants["w2B"]),
            weight_3B=float(season_constants["w3B"]),
            weight_HR=float(season_constants["wHR"]),
        )

    def constant_from_event(self, event: str) -> float:
        """Return the WOBA factor corresponding to the given event"""
        if event == "walk":
            return self.weight_BB

        if event == "hit_by_pitch":
            return self.weight_HBP

        if event == "single":
            return self.weight_1B

        if event == "double":
            return self.weight_2B

        if event == "triple":
            return self.weight_3B

        if event == "home_run":
            return self.weight_HR

        return 0.0


@dataclass
class WOBAConstantHistory:
    """
    Data class holding a dictionary of historical WOBA constants,
    with years as dict keys.
    """
    seasons: dict[str, SeasonWOBAConstants]

    @classmethod
    def load_from_file(
            cls,
            file_path: str,
            stale_by_date: date = date.today(),
            use_fangraphs: bool = True
    ):
        """
        Takes a file with a table of historical WOBA constants (one row per year)
        and loads it into a new instance of this class.

        Parameters:
            file_path (str): The path to the data file to load.
            stale_by_date (datetime.date): A file is considered to be stale if it was created on or before this date.
            use_fangraphs (bool): Optional. Indicates whether to use fangraphs as the source of the
                data. It should pretty much always be the case that this is True, but we allow for the
                possibility that a user might want to supply their own data. If True and the file is stale, we
                will go out to fangraphs and download a fresh set of data to our file. Defaults to True.
        Returns:
            WOBAConstantHistory: The new historical WOBA constants object
        """
        if not file_path:
            raise ValueError((
                "A path to a WOBA constants file must be provided in order to load WOBA constants."
                "Hint: If the provided path does not exist and the 'use_fangraphs' flag is set to True, a"
                "new file will be created from fangraphs data."
            ))

        if use_fangraphs:
            if is_file_stale(file_path, stale_by_date):
                fangraphs.download_woba_and_fip_constants(file_path)

        with open(file_path) as f:
            csv_reader = csv.DictReader(f)
            season_constants = list(csv_reader)

            return cls(
                seasons={
                    row["Season"]: SeasonWOBAConstants.load_from_dict(row)
                    for row in season_constants
                 }
            )

    def get_constant_for_event(self, season: str, event: str):
        """Given an mlb season and an event, return the corresponding WOBA constant"""
        return self.seasons[season].constant_from_event(event)
