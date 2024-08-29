from dataclasses import dataclass

from mlb.baseball.position import Position


@dataclass
class Player:
    mlb_id: int
    last_name: str = None
    first_name: str = None
    throws: str = None
    bats: str = None
    primary_position: Position = Position()
