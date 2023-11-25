"""Module for MLB schedule class and any related methods"""
import datetime

from mlb.statsapi import statsapi


class Schedule:
    """
    The Schedule class represents an MLB schedule for a given year
    and game type (eg, 'Regular', 'World Series', etc.).

    Attributes:
        season (int): The schedule year.
        schedule (dict): The json schedule returned by the mlb statsapi for the year and game type.
        opening_day_date (datetime.date): The date of the first game of the season.
        completed_game_date_isos (list[str]): A list of all game dates, iso-formatted,
            in the schedule that have already elapsed.
        most_recent_game_date (datetime.date): The most recently completed game date
    """

    def __init__(self, season: int, game_type_code: str):
        """
        Initialize the Schedule class by retrieving the json schedule from statsapi,
        and assigning key dates to attributes.

        Parameters:
            season (int): The schedule year.
            game_type_code (str): The statsapi-recognized game type code.

        Raises:
            ValueError: If either season or game_type_code are invalid values.
        """
        if statsapi.game_type_str(game_type_code) == "Unknown":
            raise ValueError("'%s' is not a recognized game type code" % game_type_code)
        elif not statsapi.is_valid_mlb_season(season):
            raise ValueError("%d is not a valid MLB season" % season)

        self.season = season
        self.schedule = statsapi.get_season_schedule(season, game_type_code)
        self.opening_day_date = datetime.datetime.strptime(self.schedule[0]["date"], "%Y-%m-%d").date()

        today_iso = datetime.date.today().isoformat()

        self.completed_game_date_isos = [
            game_date["date"] for game_date in self.schedule
            if game_date["date"] < today_iso
        ]

        self.most_recent_game_date = datetime.datetime.strptime(
            self.completed_game_date_isos[-1], "%Y-%m-%d"
        ).date()
