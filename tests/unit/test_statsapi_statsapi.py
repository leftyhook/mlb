"""
Unit tests for mlb.statsapi.statsapi.
"""
import json
import requests
from datetime import date

import unittest
from unittest.mock import Mock, patch

from mlb.statsapi.statsapi import game_type_str
from mlb.statsapi.statsapi import is_valid_mlb_season
from mlb.statsapi.statsapi import get_all_players_for_season
from mlb.statsapi.statsapi import get_teams_for_season
from mlb.statsapi.statsapi import get_schedule
from mlb.statsapi.statsapi import get_schedule_by_date_range
from mlb.statsapi.statsapi import get_team_roster

from mlb.statsapi.statsapi import FIRST_MLB_YEAR

from mlb.statsapi.statsapi import DEFAULT_PARAMS

from mlb.statsapi.statsapi import GAME_TYPE_CODE_PRESEASON
from mlb.statsapi.statsapi import GAME_TYPE_CODE_REGULAR
from mlb.statsapi.statsapi import GAME_TYPE_CODE_WILDCARD
from mlb.statsapi.statsapi import GAME_TYPE_CODE_DIV_SERIES
from mlb.statsapi.statsapi import GAME_TYPE_CODE_LCS
from mlb.statsapi.statsapi import GAME_TYPE_CODE_WS

from mlb.statsapi.statsapi import ROSTER_TYPE_ACTIVE
from mlb.statsapi.statsapi import ROSTER_TYPE_FULL


def load_statsapi_resp_from_file(file_path: str) -> dict:
    """Loads from disk a saved json response from the api."""
    with open(file_path, "rb") as f:
        return json.load(f)


class TestUtilFunctions(unittest.TestCase):
    def test_game_type_str(self):
        self.assertEqual(game_type_str(GAME_TYPE_CODE_PRESEASON), "Preseason")
        self.assertEqual(game_type_str(GAME_TYPE_CODE_REGULAR), "Regular")
        self.assertEqual(game_type_str(GAME_TYPE_CODE_WILDCARD), "Wildcard")
        self.assertEqual(game_type_str(GAME_TYPE_CODE_DIV_SERIES), "DivisionSeries")
        self.assertEqual(game_type_str(GAME_TYPE_CODE_LCS), "LeagueChampionshipSeries")
        self.assertEqual(game_type_str(GAME_TYPE_CODE_WS), "WorldSeries")
        self.assertEqual(game_type_str("anything else"), "Unknown")

    def test_is_valid_mlb_season(self):
        this_year = date.today().year
        for season in range(FIRST_MLB_YEAR, date.today().year + 2):
            self.assertTrue(is_valid_mlb_season(season))

        self.assertFalse(is_valid_mlb_season(FIRST_MLB_YEAR - 1))
        self.assertFalse(is_valid_mlb_season(this_year + 2))


@patch("mlb.statsapi.statsapi._get_api_payload")
class TestGetAllPlayersForSeason(unittest.TestCase):
    """
    Tests for statsapi.get_all_players_for_season().

    Tests to verify:
        What happens when _get_payload() raises error?
        What happens when season is invalid?
        What happens when season is valid?
    """

    def test_get_all_players_for_season_invalid_season(self, mock_payload):
        """
        What happens when season is invalid?
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_all_players_2023.json")
        with self.assertRaises(ValueError):
            get_all_players_for_season(1800)

    def test_get_all_players_for_season_valid_season(self, mock_payload):
        """
        What happens when season is valid amd the api returns a response?
        """
        season = 2020
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_all_players_2023.json")
        players = get_all_players_for_season(season)
        self.assertIsInstance(players, list)

        player_ids = [player.get("id", 0) for player in players]
        self.assertIn(
            683002,
            player_ids,
            (
                f"The mocked api response for the {season} should instead contain players from the "
                f"2023 season, but a player who did not play in {season} but did in the 2023 "
                f"season was not found. Your mock did not work properly."
            )
        )

    def test_get_all_players_for_season_none(self, mock_payload):
        """
        What happens when season is valid amd the api returns a response?
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_all_players_2020.json")
        players = get_all_players_for_season()
        self.assertIsInstance(players, list)

        player_ids = [player.get("id", 0) for player in players]
        self.assertNotIn(
            683002,
            player_ids,
            (
                f"The mocked api response should contain players from the 2020 season instead of the "
                f"most recent one, but a player who played in the most recent season and not in 2020 was found. "
                f"Your mock did not work properly."
            )
        )

    def test_get_all_players_for_season_error_response(self, mock_payload):
        """
        What happens when _get_payload() raises an error?
        """
        mock_payload.side_effect = requests.HTTPError(Mock(status=404), 'Not Found')
        with self.assertRaises(requests.HTTPError):
            get_all_players_for_season(2020)


@patch("mlb.statsapi.statsapi._get_api_payload")
class TestGetAllTeamsForSeason(unittest.TestCase):
    """
    Tests for statsapi.get_all_players_for_season().

    Tests to verify:
        What happens when _get_payload() raises error?
        What happens when season is invalid?
        What happens when season is valid?
        What happens when season is None?
    """
    def test_get_all_teams_for_season_error_response(self, mock_payload):
        """
        What happens when _get_payload() raises an error?
        """
        mock_payload.side_effect = requests.HTTPError(Mock(status=404), 'Not Found')
        with self.assertRaises(requests.HTTPError):
            get_teams_for_season(2020)

    def test_get_all_teams_for_season_invalid_season(self, mock_payload):
        """
        What happens when season is invalid?
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_teams_1995.json")
        with self.assertRaises(ValueError):
            get_teams_for_season(1800)

    def test_get_all_teams_for_season_invalid_type(self, mock_payload):
        """
        What happens when season is invalid type?
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_teams_1995.json")
        with self.assertRaises(TypeError):
            get_teams_for_season("1800")

    def test_get_all_teams_for_season_valid_season(self, mock_payload):
        """
        What happens when season is valid amd the api returns a response?
        """
        season = 2022
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_teams_1995.json")
        teams = get_teams_for_season(season)
        self.assertIsInstance(teams, list)

        team_names = [team.get("name", "") for team in teams]
        self.assertIn(
            "Florida Marlins",
            team_names,
            (
                f"The mocked api response for the {season} should instead contain teams from the "
                f"1995 season, but a team who existed in {season} and not in 2022 was not found. "
                f"Your mock did not work properly."
            )
        )

    def test_get_all_teams_for_season_none(self, mock_payload):
        """
        What happens when season is valid amd the api returns a response?
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_teams_1995.json")
        teams = get_teams_for_season()
        self.assertIsInstance(teams, list)

        team_names = [team.get("name", "") for team in teams]
        self.assertNotIn(
            "Arizona Diamondbacks",
            team_names,
            (
                f"The mocked api response should contain teams from the 1995 season instead of the "
                f"most recent one, but a team who did not exist in 1995 but did in the most recent "
                f"season was found. Your mock did not work properly."
            )
        )

@patch("mlb.statsapi.statsapi._get_api_payload")
class TestScheduleFunctions(unittest.TestCase):
    """
    Tests for functions that call the api's 'schedule' endpoint.

    Tests to verify:
        What happens when _get_payload() raises error?
        What happens when params is None?
        What happens when params includes lang=abcdefg? -> should return results in english
        What happens when params includes sportId=2? -> should return an empty schedule
        What happens when params includes sportId='abc'? -> should return
            {"messageNumber":11,"message":"Invalid Request with value: abc","timestamp":"2023-11-21T22:32:17.919189197Z","traceId":null}
        What happens when params includes someparam=abc? -> someparam will be ignored
        What happens when params are normal?
    """
    def test_get_schedule(self, mock_payload):
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_schedule_2023_ws.json")
        self.assertIsInstance(get_schedule(params=DEFAULT_PARAMS), list)

    def test_get_schedule_error_response(self, mock_payload):
        """
        What happens when _get_payload() raises an error?
        """
        mock_payload.side_effect = requests.HTTPError(Mock(status=404), 'Not Found')
        with self.assertRaises(requests.HTTPError):
            get_schedule()

        with self.assertRaises(requests.HTTPError):
            get_schedule(params=DEFAULT_PARAMS)

    def test_get_schedule_params_none(self, mock_payload):
        """
        What happens when get_schedule() is called with no params, or params = None?
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_schedule_2023_ws.json")
        self.assertIsInstance(get_schedule(None), list)

    def test_get_schedule_invalid_lang_param(self, mock_payload):
        """
        What happens when get_schedule() is called with params["lang"] = "abcdefg"?

        Expect the api will proceed without error. The bogus lang setting will be
        ignored, and a default setting used instead.
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_schedule_2023_ws.json")
        self.assertIsInstance(get_schedule(params={"lang": "abcedfg"}), list)

    def test_get_schedule_meaningless_sportId_param(self, mock_payload):
        """
        What happens when params includes sportId=2?

        Expect an empty schedule will be returned, with no error.
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_schedule_2023_ws.json")
        self.assertIsInstance(get_schedule(params={"sportId": 2}), list)

    def test_get_schedule_invalid_sportId_param(self, mock_payload):
        """
        What happens when params includes sportId='abc'?

        Expect a valid json response will be returned, but without the key we need.
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_schedule_bad_param_val.json")
        with self.assertRaises(KeyError):
            get_schedule(params={"sportId": "abc"})

    def test_get_schedule_unrecognized_param(self, mock_payload):
        """
        What happens when get_schedule() is called with a param not recognized by the api?

        Expect the api will proceed without error. The bogus param
        will be ignored, and a default setting used instead.
        """
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_schedule_2023_ws.json")
        self.assertIsInstance(get_schedule(params={"bogusparam": "abcedfg"}), list)

    def test_get_schedule_by_date_range_end_date_before_start_date(self, mock_payload):
        mock_payload.return_value = load_statsapi_resp_from_file("../statsapi_resp_schedule_bad_param_val.json")
        with self.assertRaises(KeyError):
            get_schedule_by_date_range(
                start_date=date(2023, 8, 17),
                end_date=date(2023, 8, 16)
            )


if __name__ == "__main__":
    unittest.main()
