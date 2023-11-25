"""
Unit tests for mlb.schedule.
"""
import json
import unittest

from unittest.mock import Mock, patch
from datetime import date, datetime

from mlb import schedule
from mlb.schedule import Schedule

import logging
logger = logging.getLogger()


class MockStatsapiSchedule:
    """
    MockStatsapiSchedule mocks the json that would be returned from the mlb.statsapi.get_schedule() function,
    and provides easy access to some of its frequently used items.

    Presumably this will be loaded from some saved file for testing purposes.

    Attributes:
        game_days (list[dict]): A list of game day dictionaries.
            Each game day dictionary holds that day's game dictionaries.
    """
    def __init__(self, game_days: list[dict]):
        self.game_days = game_days

    @property
    def first_day_of_games(self) -> dict:
        return self.game_days[0]

    @property
    def first_game_date(self) -> date:
        return datetime.strptime(self.first_day_of_games["date"], "%Y-%m-%d").date()

    @property
    def first_game(self) -> dict:
        return self.first_day_of_games["games"][0]

    @property
    def season(self) -> int:
        return int(self.first_game["season"])

    @property
    def midseason_date(self) -> date:
        day_num = (len(self.game_days) // 2) + (len(self.game_days) % 2)
        return datetime.strptime(self.game_days[day_num]["date"], "%Y-%m-%d").date()

    @property
    def last_day_of_games(self) -> dict:
        return self.game_days[-1]

    @property
    def last_game_date(self) -> date:
        return datetime.strptime(self.last_day_of_games["date"], "%Y-%m-%d").date()

    @property
    def schedule_dates(self) -> list[str]:
        return [game_day["date"] for game_day in self.game_days]


def load_mock_statsapi_schedule_from_file(file_path: str) -> MockStatsapiSchedule:
    """Loads a MockStatsapiSchedule object from a json file."""
    with open(file_path, "rb") as f:
        data = json.load(f)
        return MockStatsapiSchedule(data["dates"])


class TestScheduleInvalidParams(unittest.TestCase):
    @patch("schedule.statsapi.is_valid_mlb_season")
    def test_schedule_init_invalid_season(self, mock):
        mock.return_value = False
        with self.assertRaises(ValueError):
            Schedule(2023, "W")

    @patch("schedule.statsapi.game_type_str")
    def test_schedule_init_invalid_game_code(self, mock):
        mock.return_value = "Unknown"
        with self.assertRaises(ValueError):
            Schedule(2023, "W")


@patch("schedule.statsapi.is_valid_mlb_season", return_value=True)
@patch("schedule.statsapi.game_type_str", return_value="WorldSeries")
class TestScheduleValidParams(unittest.TestCase):
    def setUp(self):
        self.mock_statsapi_schedule = load_mock_statsapi_schedule_from_file("..\\statsapi_resp_schedule_2023_ws.json")

    def test_schedule_init(self, mock_statsapi_is_valid_mlb_season, mock_statsapi_game_type_str):
        with patch("schedule.statsapi.get_season_schedule", return_value=self.mock_statsapi_schedule.game_days):
            s = Schedule(self.mock_statsapi_schedule.season, "R")
            self.assertEqual(s.season, self.mock_statsapi_schedule.season)
            self.assertEqual(s.schedule, self.mock_statsapi_schedule.game_days)
            self.assertEqual(s.opening_day_date, self.mock_statsapi_schedule.first_game_date)

    def test_schedule_init_during_season(self, mock_statsapi_is_valid_mlb_season, mock_statsapi_game_type_str):
        mock_today = self.mock_statsapi_schedule.midseason_date
        with patch("schedule.statsapi.get_season_schedule", return_value=self.mock_statsapi_schedule.game_days):
            with patch("schedule.datetime.date") as mock_date:
                mock_date.today.return_value = mock_today
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                self.assertEqual(
                    schedule.datetime.date.today(),
                    mock_today,
                    "Failed to properly mock datetime.date.today()"
                )

                s = Schedule(self.mock_statsapi_schedule.season, "W")
                self.assertNotEqual(set(s.completed_game_date_isos), set(self.mock_statsapi_schedule.schedule_dates))
                self.assertNotEqual(s.most_recent_game_date, self.mock_statsapi_schedule.last_game_date)

    def test_schedule_init_after_season(self, mock_statsapi_is_valid_mlb_season, mock_statsapi_game_type_str):
        mock_today = date(self.mock_statsapi_schedule.season, 12, 31)
        with patch("schedule.statsapi.get_season_schedule", return_value=self.mock_statsapi_schedule.game_days):
            with patch("schedule.datetime.date") as mock_date:
                mock_date.today.return_value = mock_today
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                self.assertEqual(
                    schedule.datetime.date.today(),
                    mock_today,
                    "Failed to properly mock datetime.date.today()"
                )

                s = Schedule(self.mock_statsapi_schedule.season, "R")
                self.assertEqual(set(s.completed_game_date_isos), set(self.mock_statsapi_schedule.schedule_dates))
                self.assertEqual(s.most_recent_game_date, self.mock_statsapi_schedule.last_game_date)


if __name__ == "__main__":
    unittest.main()
