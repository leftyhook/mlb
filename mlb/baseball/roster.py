from mlb.baseball.player import Player


class Roster:
    players: dict[int, Player]

    def __init__(self, players: dict[int, Player] = None):
        if not players:
            players = {}

        self.players = players

    def add_player(self, player: Player):
        self.players[player.mlb_id] = player

    def _player_id_list_by_postion_type(self, position_type: str) -> list[int]:
        return [
            self.players[p].mlb_id
            for p in self.players
            if self.players[p].primary_position.type.lower() == position_type.lower()
        ]

    def _player_dict_from_ids(self, player_ids: list[int]) -> dict[int, Player]:
        return {self.players[p].mlb_id: self.players[p] for p in player_ids}

    def pitcher_ids(self) -> list[int]:
        return self._player_id_list_by_postion_type("Pitcher")

    def pitchers(self) -> dict[int, Player]:
        return self._player_dict_from_ids(self.pitcher_ids())

    def catcher_ids(self) -> list[int]:
        return self._player_id_list_by_postion_type("Catcher")

    def catchers(self) -> dict[int, Player]:
        return self._player_dict_from_ids(self.catcher_ids())

    def infielder_ids(self) -> list[int]:
        return self._player_id_list_by_postion_type("Infielder")

    def infielders(self) -> dict[int, Player]:
        return self._player_dict_from_ids(self.infielder_ids())

    def outfielder_ids(self) -> list[int]:
        return self._player_id_list_by_postion_type("Outfielder")

    def outfielders(self) -> dict[int, Player]:
        return self._player_dict_from_ids(self.outfielder_ids())

    def designated_hitter_ids(self) -> list[int]:
        return self._player_id_list_by_postion_type("Designated Hitter")

    def designated_hitters(self) -> dict[int, Player]:
        return self._player_dict_from_ids(self.designated_hitter_ids())

    def two_way_player_ids(self) -> list[int]:
        return self._player_id_list_by_postion_type("Two-Way Player")

    def two_way_players(self) -> dict[int, Player]:
        return self._player_dict_from_ids(self.two_way_player_ids())
