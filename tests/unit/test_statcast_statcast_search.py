from requests import Response, HTTPError
from datetime import date
from dataclasses import dataclass
import unittest
from unittest.mock import Mock, patch

from mlb.statcast.statcast_search import SeasonTypesParam
from mlb.statcast.statcast_search import PitchResultTypesParam
from mlb.statcast.statcast_search import StatcastSearchParams
from mlb.statcast.statcast_search import StatcastSearch

from mlb.statcast.statcast_search import run_pitch_count_search
from mlb.statcast.statcast_search import run_pitch_data_search
from mlb.statcast.statcast_search import StatcastSearch


@dataclass
class MockRequestsResponse:
    def __init__(self, status_code: int, content: bytes):
        self.status_code = status_code
        self._content = content

    @classmethod
    def new(cls, status_code: int, content: bytes):
        return cls(status_code, content)

    @property
    def status_code(self) -> int:
        return self._status_code

    @status_code.setter
    def status_code(self, value):
        self._status_code = value

    @property
    def content(self) -> bytes:
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    def raise_for_status(self):
        raise HTTPError(f"HTTP error code {self.status_code}")


class TestStatcastSearch(unittest.TestCase):
    """Test the methods of the StatcastSearch class"""
    def test_statcastsearch_init_no_session(self):
        self.assertIsNone(StatcastSearch().session)

    def test_statcastsearch_init_with_session(self):
        self.assertIsNotNone(StatcastSearch(use_session=True).session)

    def test_get_statcast_search_data_failure(self):
        search_params = StatcastSearchParams(
            start_date_iso='2023-03-30',
            end_date_iso='2023-04-05',
            season_types=SeasonTypesParam.build_from_game_type_code("R"),
            pitch_result_types=PitchResultTypesParam()
        )
        with patch("requests.get") as mock_get:
            mock_get.side_effect = [MockRequestsResponse.new(400, bytes("I failed", "utf-8"))]
            statcast_search = StatcastSearch()
            self.assertRaises(HTTPError, statcast_search.get_statcast_search_data, search_params=search_params)

    def test_get_statcast_search_data_success_after_retry(self):
        search_params = StatcastSearchParams(
            start_date_iso='2023-03-30',
            end_date_iso='2023-04-05',
            season_types=SeasonTypesParam.build_from_game_type_code("R"),
            pitch_result_types=PitchResultTypesParam()
        )
        failure = bytes("I failed", "utf-8")
        success = bytes("I succeeded", "utf-8")
        responses = [
            MockRequestsResponse.new(524, failure),
            MockRequestsResponse.new(200, success)
        ]

        with patch("requests.get") as mock_get:
            mock_get.side_effect = responses
            statcast_search = StatcastSearch()
            self.assertEqual(statcast_search.get_statcast_search_data(search_params, max_retries=1), success)

        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = responses
            statcast_search = StatcastSearch(use_session=True)
            self.assertEqual(statcast_search.get_statcast_search_data(search_params, max_retries=1), success)

    def test_get_statcast_search_data_failure_after_retry(self):
        search_params = StatcastSearchParams(
            start_date_iso='2023-03-30',
            end_date_iso='2023-04-05',
            season_types=SeasonTypesParam.build_from_game_type_code("R"),
            pitch_result_types=PitchResultTypesParam()
        )
        failure = bytes("I failed", "utf-8")
        failure2 = bytes("I failed for the 2nd time", "utf-8")
        success = bytes("I succeeded", "utf-8")

        responses = [
            MockRequestsResponse.new(524, failure),
            MockRequestsResponse.new(524, failure2),
            MockRequestsResponse.new(200, success)
        ]

        with patch("requests.get") as mock_get:
            mock_get.side_effect = responses
            statcast_search = StatcastSearch()
            self.assertRaises(
                HTTPError,
                statcast_search.get_statcast_search_data,
                search_params=search_params,
                max_retries=1
            )

        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = responses
            statcast_search = StatcastSearch(use_session=True)
            self.assertRaises(
                HTTPError,
                statcast_search.get_statcast_search_data,
                search_params=search_params,
                max_retries=1
            )


if __name__ == "__main__":
    unittest.main()