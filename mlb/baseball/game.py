from dataclasses import dataclass

from team import Team


@dataclass
class Game:
    game_date: str = ""
    game_time: str = ""
    away_team: Team = Team()
    home_team: Team = Team()
    mlb_game_id: int = -1
