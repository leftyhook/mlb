class Stats:
    pitches: list[dict]

    def __init__(self):
        self.pitches = []
        self.balls = 0
        self.called_strikes = 0
        self.swinging_strikes = 0
        self.fouls = 0
        self.missed_bunts = 0
        self.two_strike_pitches = 0
        self.plate_appearances = 0
        self.at_bats = 0
        self.singles = 0
        self.doubles = 0
        self.triples = 0
        self.home_runs = 0
        self.walks = 0
        self.hit_by_pitches = 0
        self.strikeouts = 0
        self.fly_balls = 0
        self.ground_balls = 0
        self.line_drives = 0
        self.popups = 0
        self.woba_value = 0.0
        self.woba_denom = 0
        self.wobacon_value = 0.0
        self.wobacon_denom = 0
        self.xwobacon_value = 0.0
        self.estimated_ba_using_speedangle = 0.0
        self.estimated_woba_using_speedangle = 0.0
        self.hard_hit_balls = 0
        self.lsa_weak = 0
        self.lsa_topped = 0
        self.lsa_under = 0
        self.lsa_flare_burner = 0
        self.lsa_solid = 0
        self.lsa_barrel = 0
        self.stolen_bases = 0
        self.caught_stealing = 0

    def number_of_pitches(self):
        return len(self.pitches)

    def swings(self):
        return self.number_of_pitches() - self.balls - self.called_strikes

    def hits(self):
        return self.singles + self.doubles + self.triples + self.home_runs

    def batting_average(self):
        return self.hits() / self.at_bats

    def batted_ball_events(self):
        return self.fly_balls + self.ground_balls + self.line_drives + self.popups

    def expected_batting_average(self):
        return self.estimated_ba_using_speedangle / self.at_bats

    def slugging_percentage(self):
        return (self.singles + (self.doubles * 2) + (self.triples * 3) + (self.home_runs * 4)) / self.at_bats

    def weighted_on_base_average(self):
        return self.woba_value / self.woba_denom

    def expected_weighted_on_base_average(self):
        return self.estimated_woba_using_speedangle / self.woba_denom

    def wobacon(self):
        return self.wobacon_value / self.wobacon_denom

    def xwobacon(self):
        return self.estimated_woba_using_speedangle / self.wobacon_denom

    def isolated_power(self):
        return self.slugging_percentage() - self.batting_average()

    def walk_percentage(self):
        return self.walks / self.plate_appearances

    def strikeout_percentage(self):
        return self.strikeouts / self.plate_appearances

    def swinging_strike_percentage(self):
        return self.swinging_strikes / self.number_of_pitches()

    def whiff_rate(self):
        return self.swinging_strikes / self.swings()

    def hard_contact_percentage(self):
        return self.hard_hit_balls / self.batted_ball_events()

    def barrel_rate(self):
        return self.lsa_barrel / self.batted_ball_events()

    def barrels_per_plate_appearance(self):
        return self.lsa_barrel / self.plate_appearances

    def good_contact_percentage(self):
        return (self.lsa_barrel + self.lsa_solid + self.lsa_flare_burner) / self.batted_ball_events()

    def bad_contact_percentage(self):
        return (self.lsa_weak + self.lsa_topped + self.lsa_under) / self.batted_ball_events()

    def _increment_lsa_type(self, lsa_value: int):
        if lsa_value:
            if lsa_value == 1:
                self.lsa_weak += 1
            elif lsa_value == 2:
                self.lsa_topped += 1
            elif lsa_value == 3:
                self.lsa_under += 1
            elif lsa_value == 4:
                self.lsa_flare_burner += 1
            elif lsa_value == 5:
                self.lsa_solid += 1
            elif lsa_value == 6:
                self.lsa_barrel += 1

    def _increment_batted_ball_type(self, bb_type_value: str):
        if bb_type_value:
            val = bb_type_value.replace("_", "").replace(" ", "").lower()
            if val == "flyball":
                self.fly_balls += 1
            elif val == "groundball":
                self.ground_balls += 1
            elif val == "linedrive":
                self.line_drives += 1
            elif val == "popup":
                self.popups += 1

    def add_pitch(self, pitch):
        self.pitches.append(pitch)

        # A batter does not receive a plate appearance if a runner is thrown out on the bases to end the inning while
        # he is at bat, or if the game-winning run scores on a balk, wild pitch, or passed ball while he is at bat.
        if pitch["events"] and ("caught_stealing" not in pitch["events"] and
                                "pickoff" not in pitch["events"] and
                                "stolen_base" not in pitch["events"] and
                                pitch["events"] not in ["balk", "passed_ball", "wild_pitch"]):
            self.plate_appearances += 1

            if (pitch["events"] != "catcher_interf" and "sac_bunt" not in pitch["events"]
                    and "sac_fly" not in pitch["events"]):

                self.at_bats += 1

        if pitch["type"] == "B":
            self.balls += 1
            if pitch["events"] == "walk":
                self.walks += 1
        elif pitch["type"] == "S":
            if "strikeout" in pitch["events"]:
                self.strikeouts += 1

            if pitch["description"] in ["bunt_foul_tip", "foul", "foul_bunt", "foul_tip"]:
                self.fouls += 1
            elif pitch["description"] in ["called_strike", "unknown_strike"]:
                self.called_strikes += 1
            elif "swinging_strike" in pitch["description"]:
                self.swinging_strikes += 1
            elif pitch["description"] == "missed_bunt":
                self.missed_bunts += 1

        if pitch["strikes"] == 2:
            self.two_strike_pitches += 1

        if pitch["events"] == "single":
            self.singles += 1
        elif pitch["events"] == "double":
            self.doubles += 1
        elif pitch["events"] == "home_run":
            self.home_runs += 1
        if pitch["events"] == "hit_by_pitch":
            self.hit_by_pitches += 1
        elif pitch["events"] == "triple":
            self.triples += 1

        if pitch["launch_speed"]:
            try:
                if float(pitch["launch_speed"]) > 95:
                    self.hard_hit_balls += 1
            except ValueError:
                pass

        self.woba_value += 0 if not pitch["woba_value"] else float(pitch["woba_value"])
        self.woba_denom += 0 if not pitch["woba_denom"] else int(float(pitch["woba_denom"]))

        if "strikeout" not in pitch["events"]:
            self.wobacon_value += 0 if not pitch["woba_value"] else float(pitch["woba_value"])
            self.wobacon_denom += 0 if not pitch["woba_denom"] else int(float(pitch["woba_denom"]))

            if pitch["estimated_woba_using_speedangle"]:
                self.xwobacon_value += float(pitch["estimated_woba_using_speedangle"])
                self.estimated_woba_using_speedangle += float(pitch["estimated_woba_using_speedangle"])

            if pitch["estimated_ba_using_speedangle"]:
                self.estimated_ba_using_speedangle += float(pitch["estimated_ba_using_speedangle"])

        self._increment_batted_ball_type(pitch["bb_type"])
        self._increment_lsa_type(pitch["launch_speed_angle"])


def combine_stats(stats: list[Stats]) -> Stats:
    combined_stats = Stats()

    for s in stats:
        combined_stats.pitches.extend(s.pitches)
        combined_stats.balls += s.balls
        combined_stats.called_strikes += s.called_strikes
        combined_stats.swinging_strikes += s.swinging_strikes
        combined_stats.fouls += s.fouls
        combined_stats.missed_bunts += s.missed_bunts
        combined_stats.two_strike_pitches += s.two_strike_pitches
        combined_stats.plate_appearances += s.plate_appearances
        combined_stats.at_bats += s.at_bats
        combined_stats.singles += s.singles
        combined_stats.doubles += s.doubles
        combined_stats.triples += s.triples
        combined_stats.home_runs += s.home_runs
        combined_stats.walks += s.walks
        combined_stats.hit_by_pitches += s.hit_by_pitches
        combined_stats.strikeouts += s.strikeouts
        combined_stats.fly_balls += s.fly_balls
        combined_stats.ground_balls += s.ground_balls
        combined_stats.line_drives += s.line_drives
        combined_stats.popups += s.popups
        combined_stats.woba_value += s.woba_value
        combined_stats.woba_denom += s.woba_denom
        combined_stats.wobacon_value += s.wobacon_value
        combined_stats.wobacon_denom += s.wobacon_denom
        combined_stats.xwobacon_value += s.xwobacon_value
        combined_stats.estimated_ba_using_speedangle += s.estimated_ba_using_speedangle
        combined_stats.estimated_woba_using_speedangle += s.estimated_woba_using_speedangle
        combined_stats.hard_hit_balls += s.hard_hit_balls
        combined_stats.lsa_weak += s.lsa_weak
        combined_stats.lsa_topped += s.lsa_topped
        combined_stats.lsa_under += s.lsa_under
        combined_stats.lsa_flare_burner += s.lsa_flare_burner
        combined_stats.lsa_solid += s.lsa_solid
        combined_stats.lsa_barrel += s.lsa_barrel
        combined_stats.stolen_bases += s.stolen_bases
        combined_stats.caught_stealing += s.caught_stealing

    return combined_stats
