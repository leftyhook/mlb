"""
Module of functions for retrieving MLB data via their publicly available statsapi.

Disclaimer:
    The author of this source code is not affiliated with Major League Baseball in any way.
    The use of data delivered from statsapi.mlb.com is subject to all copyright notices included therein.
"""
import logging
import json
import requests
import datetime

from os import path
from requests.compat import urljoin


URL = "https://statsapi.mlb.com/api/v1/"
WS_URL = "https://ws.statsapi.mlb.com/"

FIRST_MLB_YEAR = 1876
THIS_YEAR = datetime.date.today().year

DEFAULT_PARAMS = {
    "lang": "en",
    "sportId": 1,
}

GAME_TYPE_CODE_PRESEASON = "S"
GAME_TYPE_CODE_REGULAR = "R"
GAME_TYPE_CODE_WILDCARD = "F"
GAME_TYPE_CODE_DIV_SERIES = "D"
GAME_TYPE_CODE_LCS = "L"
GAME_TYPE_CODE_WS = "W"

ROSTER_TYPE_FULL = "fullRoster"
ROSTER_TYPE_ACTIVE = "active"


def game_type_str(game_type_code: str) -> str:
    """Convert a single-letter game type code to its full word value"""
    if game_type_code == GAME_TYPE_CODE_PRESEASON:
        return "Preseason"

    if game_type_code == GAME_TYPE_CODE_REGULAR:
        return "Regular"

    if game_type_code == GAME_TYPE_CODE_WILDCARD:
        return "Wildcard"

    if game_type_code == GAME_TYPE_CODE_DIV_SERIES:
        return "DivisionSeries"

    if game_type_code == GAME_TYPE_CODE_LCS:
        return "LeagueChampionshipSeries"

    if game_type_code == GAME_TYPE_CODE_WS:
        return "WorldSeries"

    return "Unknown"


def is_valid_mlb_season(season: int) -> bool:
    """
    Checks that an integer is a valid MLB year.

    The api will have no data to return for any year beyond next year.

    Returns:
        bool: True if the season falls in the range of MLB history, or next year.
    """
    return FIRST_MLB_YEAR <= season <= THIS_YEAR + 1


def _get_api_payload(url: str, params: dict = None) -> dict:
    """
    Make an HTTP request to a specified url and return its json response.
    There is no validation of the provided inputs happening here. The url
    and params are assumed to be valid before making the 'get' request.

    Parameters:
        url (str): The url, presumably including an api endpoint.
        params (dict): Optional. url query params to include in the api request.

    Raises:
        HTTPError if the HTTP response has an error code.
    """
    resp = requests.get(url, params=params)
    logging.debug("Response received from %s with status code %d" % (resp.url, resp.status_code))

    if resp.status_code == 200:
        return resp.json()
    else:
        resp.raise_for_status()


def get_team_roster(team_id: int, season: int = None, roster_type: str = None) -> list[dict]:
    endpoint = f"teams/{team_id}/roster"
    url = urljoin(URL, endpoint)
    params = {"hydrate": "person"}

    if season:
        if not is_valid_mlb_season(season):
            raise ValueError(f"{season} is not a valid MLB season. ")

        params["season"] = season

    if roster_type == ROSTER_TYPE_FULL or roster_type == ROSTER_TYPE_ACTIVE:
        params["rosterType"] = roster_type

    payload = _get_api_payload(url, params)
    return payload["roster"]


def get_all_players_for_season(season: int = None) -> list[dict]:
    """
    Get a list of the players that were on MLB 40-man rosters in a given season.

    Parameters:
        season (int): Optional. A year value. If omitted, the api will return the players from the current year.
    Raises:
        ValueError if an invalid season is provided.
    Returns:
        list[dict]: A list of dictionaries containing player information. The list
            is extracted directly from the api payload json without modification.
    """
    endpoint = "sports/1/players"
    url = urljoin(URL, endpoint)
    params = {"hydrate": "person"}

    if season:
        if not is_valid_mlb_season(season):
            raise ValueError(f"{season} is not a valid MLB season. ")

        params["season"] = season

    payload = _get_api_payload(url, params)
    return payload["people"]


def get_teams_for_season(season: int = None) -> list[dict]:
    """
    Get a list of the teams that comprised mlb for a given season.

    Parameters:
        season (int): Optional. A year value. If omitted, the api will return the current mlb teams.
    Raises:
        ValueError if an invalid season is provided.
    Returns:
        list[dict]: A list of dictionaries containing team information. The list
            is extracted directly from the api payload json without modification.
    """
    endpoint = "teams"
    url = urljoin(URL, endpoint)
    params = DEFAULT_PARAMS

    if season:
        if not is_valid_mlb_season(season):
            raise ValueError(f"{season} is not a valid MLB season. ")

        params["season"] = season

    payload = _get_api_payload(url, params)
    return payload["teams"]


def current_mlb_season() -> int:
    """
    We consider the current season to be the one in progress or,
    if there is no season currently in progress, then the most
    recently completed season.

    Returns:
        int: The calculated current mlb season.
    """
    today_iso = datetime.date.today().isoformat()
    schedule = get_season_schedule(THIS_YEAR)
    return THIS_YEAR if today_iso >= schedule[0]["date"] else THIS_YEAR - 1


def get_schedule(params: dict = None) -> list[dict]:
    """
    Retrieve the schedule for the timeframe dictated by params.
    The api endpoint returns today's schedule  by default when the
    params do not specify a season or date range.

    Parameters:
        params (dict): A dictionary of URL params to send to the api request

    Returns:
        list[dict]: A list of dictionaries containing date and game information. The list
            is extracted directly from the api payload json without modification.
    """
    endpoint = "schedule"
    url = requests.compat.urljoin(URL, endpoint)

    if params is None:
        params = {}

    if "lang" not in params:
        params["lang"] = DEFAULT_PARAMS.get("lang", "en")

    if "sportId" not in params:
        params["sportId"] = DEFAULT_PARAMS.get("sportId", 1)

    payload = _get_api_payload(url, params)
    return payload["dates"]


def get_season_schedule(season: int, game_type_code: str = None) -> list[dict]:
    """
    Gets the schedule for a given mlb season. A request for an invalid mlb season
    will simply return an empty list.

    Parameters:
        season (int): The year of the mlb season.
        game_type_code (str): Optional. A statsapi game type code. If omitted, all games scheduled
            for the season, including preseason and playoffs, will be returned.

    Returns:
        list[dict]: A list of dictionaries containing date and game information. The list
            is extracted directly from the api payload json without modification.
    """
    params = {"season": season}

    if game_type_code:
        params["gameType"] = game_type_code

    return get_schedule(params)


def get_schedule_by_date_range(
        start_date: datetime.date,
        end_date: datetime.date,
        game_type_code: str = None
) -> list[dict]:
    """
    Gets the schedule of games between 2 dates. A request for an invalid mlb season
    will simply return an empty list.

    Parameters:
        start_date (date): The first date in the date range.
        end_date (date): The first date in the date range.
        game_type_code (str): Optional. A statsapi game type code. If omitted, all games scheduled
            for the season, including preseason and playoffs, will be returned.

    Returns:
        list[dict]: A list of dictionaries containing date and game information. The list
            is extracted directly from the api payload json without modification.
    """
    params = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
    }

    if game_type_code:
        params["gameType"] = game_type_code

    return get_schedule(params)


def get_game_feed_from_schedule_game(game: dict) -> dict:
    """
    Each game in a schedule has a link to a game feed, which provides
    all details of every event that happened in a game. This function
    retrieves those details and returns them in their unedited json format.

    Parameters:
        game (dict): A game dictionary taken from a schedule json.

    Returns:
         dict: The game feed json.
    """
    url = urljoin(WS_URL, game["link"])
    return _get_api_payload(url)


def download_season_game_feeds(target_dir: str, season: int, game_type_code: str = None):
    """
    Download every previously un-downloaded game feed for an entire mlb season to date.

    Parameters:
        target_dir (str): Where to look for previously downloaded files, and write new files to.
        season (int): The year of the mlb season.
        game_type_code (str): Optional. A statsapi game type code. If omitted, all games scheduled
            for the season, including preseason and playoffs, will be downloaded.
    """
    teams = get_teams_for_season(season)
    team_map = {team["id"]: team["abbreviation"] for team in teams}

    today_iso = datetime.date.today().isoformat()
    schedule = get_season_schedule(season, game_type_code)
    for game_date in schedule:
        if game_date["date"] < today_iso:
            break

        for game in game_date["games"]:
            game_date = game["officialDate"].replace("-", "")
            game_pk = game["gamePk"]
            away_id = game["teams"]["away"]["team"]["id"]
            home_id = game["teams"]["home"]["team"]["id"]
            file_name = f"{game_date}.{game_pk}.{team_map[away_id]}@{team_map[home_id]}.json"
            file_path = path.join(target_dir, file_name)
            if not path.exists(file_path):
                payload = get_game_feed_from_schedule_game(game)
                with open(file_path, "w") as file:
                    json.dump(payload, file)


def monitor_gameday_feed(game_id: int):
    """
    AN IDEA FOR MONITORING A LIVE GAMEDAY FEED. REQUIRES FURTHER RESEARCH BEFORE IMPLEMENTING.

    A websockets connection can be opened to subscribe to gameday updates for a game.
    Sample URL: wss://ws.statsapi.mlb.com/api/v1/game/push/subscribe/gameday/748534

    Updates are delivered in the form of:
        {
            "timeStamp":"20231102_012727",
            "gamePk":"748534",
            "updateId":"b9877311-e35d-4f21-ac78-8fd6a5e4fc7e",
            "wait":10,
            "logicalEvents":["countChange","count21"],
            "gameEvents":["ball"],
            "changeEvent":{"type":"new_entry"}
        }

    Upon receiving an update, live updates of the game in progress can be captured
    by using this data to form a separate HTTP request in the form of:
    https://ws.statsapi.mlb.com/api/v1.1/game/748534/feed/live/diffPatch?language=en&startTimecode=20231102_012727&pushUpdateId=b9877311-e35d-4f21-ac78-8fd6a5e4fc7e

    [SPECULATION, UNVERIFIED]
    For the purposes of being notified when a starting lineup is available for the game in question,
    we can use the message received from the websocket connection as a signal to make an HTTP call
    to the feed/live endpoint, disregarding the diffPatch:
    https://ws.statsapi.mlb.com/api/v1.1/game/716353/feed/live?language=en

    TBD: is there a "logicalEvents" or "changeEvent" value that
    explicitly alerts us to lineup publication or change?

    [OBSERVATIONS]
    When testing with the websockets interactive client in PowerShell during live game action...

    PS C:\Program Files\Python311> .\python -m websockets wss://ws.statsapi.mlb.com/api/v1/game/push/subscribe/gameday/748534

    ...observed that the connection was brittle and easily dropped, raising:

    websockets.exceptions.ConnectionClosedError: no close frame received or sent

    When monitoring for lineup updates, this exception will need to be explicitly handled and the connection reopened.
    """
    pass
