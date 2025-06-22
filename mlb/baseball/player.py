from dataclasses import dataclass

from mlb.baseball.position import Position


@dataclass
class Player:
    mlb_id: int
    full_name: str = ""
    link: str = ""
    first_name: str = ""
    last_name: str = ""
    birth_date_str: str = ""
    current_age: float = None
    height_str: str = ""
    weight: float = None
    use_first_name: str = ""
    use_last_name: str = ""
    middle_name: str = ""
    boxscore_name: str = ""
    name_first_last: str = ""
    nameSlug: str = ""
    first_last_name: str = ""
    last_first_name: str = ""
    last_init_name: str = ""
    init_last_name: str = ""
    full_fml_name: str = ""
    full_lfm_name: str = ""
    strike_zone_top: float = None
    strike_zone_bottom: float = None
    bat_side_code: str = ""
    bat_side_description: str = ""
    pitch_hand_code: str = ""
    pitch_hand_description: str = ""
    name_matrilineal: str = ""
    primary_position: Position = None

    @classmethod
    def build_from_mlb_player_json(cls, player: dict):
        return cls(
            player['id'],
            full_name = player['fullName'],
            link = player['link'],
            first_name = player['firstName'],
            last_name = player['lastName'],
            birth_date_str = player['birthDate'],
            current_age = float(player['currentAge']) if player.get('currentAge', None) else None,
            height_str = player['height'],
            weight = float(player['weight']) if player.get('weight', None) else None,
            use_first_name = player['useName'],
            use_last_name = player['useLastName'],
            middle_name = player['middleName'],
            boxscore_name = player['boxscoreName'],
            name_first_last = player['nameFirstLast'],
            nameSlug = player['nameSlug'],
            first_last_name = player['firstLastName'],
            last_first_name = player['lastFirstName'],
            last_init_name = player['lastInitName'],
            init_last_name = player['initLastName'],
            full_fml_name = player['initLastName'],
            full_lfm_name = player['fullLFMName'],
            strike_zone_top = float(player['strikeZoneTop']) if player.get('strikeZoneTop', None) else None,
            strike_zone_bottom = float(player['strikeZoneBottom']) if player.get('strikeZoneBottom', None) else None,
            bat_side_code = player['batSide_code'],
            bat_side_description = player['batSide_description'],
            pitch_hand_code = player['pitchHand_code'],
            pitch_hand_description = player['pitchHand_description'],
            name_matrilineal = player['nameMatrilineal'],
            primary_position = Position(
                code = player['primaryPosition_code'],
                name = player['primaryPosition_name'],
                type = player['primaryPosition_type'],
                abbreviation = player['primaryPosition_abbreviation']
            )
        )
