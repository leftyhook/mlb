from dataclasses import dataclass

from mlb.baseball.roster import Roster


@dataclass
class Team:
    abbreviation: str = "",
    team_name: str = "",
    location_name: str = "",
    venue_name: str = "",
    wins: int = 0,
    losses: int = 0,
    roster: Roster = Roster()
