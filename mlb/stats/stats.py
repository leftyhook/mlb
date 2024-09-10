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


def combine_stats(stats1: Stats, stats2: Stats) -> Stats:
    combined_stats = Stats()
    combined_stats.pitches = stats1.pitches + stats2.pitches
    combined_stats.balls = stats1.balls + stats2.balls
    combined_stats.called_strikes = stats1.called_strikes + stats2.called_strikes
    combined_stats.swinging_strikes = stats1.swinging_strikes + stats2.swinging_strikes
    combined_stats.fouls = stats1.fouls + stats2.fouls
    combined_stats.missed_bunts = stats1.missed_bunts + stats2.missed_bunts
    combined_stats.two_strike_pitches = stats1.two_strike_pitches + stats2.two_strike_pitches
    combined_stats.plate_appearances = stats1.plate_appearances + stats2.plate_appearances
    combined_stats.at_bats = stats1.at_bats + stats2.at_bats
    combined_stats.singles = stats1.singles + stats2.singles
    combined_stats.doubles = stats1.doubles + stats2.doubles
    combined_stats.triples = stats1.triples + stats2.triples
    combined_stats.home_runs = stats1.home_runs + stats2.home_runs
    combined_stats.walks = stats1.walks + stats2.walks
    combined_stats.hit_by_pitches = stats1.hit_by_pitches + stats2.hit_by_pitches
    combined_stats.strikeouts = stats1.strikeouts + stats2.strikeouts
    combined_stats.fly_balls = stats1.fly_balls + stats2.fly_balls
    combined_stats.ground_balls = stats1.ground_balls + stats2.ground_balls
    combined_stats.line_drives = stats1.line_drives + stats2.line_drives
    combined_stats.popups = stats1.popups + stats2.popups
    combined_stats.woba_value = stats1.woba_value + stats2.woba_value
    combined_stats.woba_denom = stats1.woba_denom + stats2.woba_denom
    combined_stats.wobacon_value = stats1.wobacon_value + stats2.wobacon_value
    combined_stats.wobacon_denom = stats1.wobacon_denom + stats2.wobacon_denom
    combined_stats.xwobacon_value = stats1.xwobacon_value + stats2.xwobacon_value
    combined_stats.estimated_ba_using_speedangle = (
            stats1.estimated_ba_using_speedangle + stats2.estimated_ba_using_speedangle
    )
    combined_stats.estimated_woba_using_speedangle = (
            stats1.estimated_woba_using_speedangle + stats2.estimated_woba_using_speedangle
    )
    combined_stats.hard_hit_balls = stats1.hard_hit_balls + stats2.hard_hit_balls
    combined_stats.lsa_weak = stats1.lsa_weak + stats2.lsa_weak
    combined_stats.lsa_topped = stats1.lsa_topped + stats2.lsa_topped
    combined_stats.lsa_under = stats1.lsa_under + stats2.lsa_under
    combined_stats.lsa_flare_burner = stats1.lsa_flare_burner + stats2.lsa_flare_burner
    combined_stats.lsa_solid = stats1.lsa_solid + stats2.lsa_solid
    combined_stats.lsa_barrel = stats1.lsa_barrel + stats2.lsa_barrel
    combined_stats.stolen_bases = stats1.stolen_bases + stats2.stolen_bases
    combined_stats.caught_stealing = stats1.caught_stealing + stats2.caught_stealing

    return combined_stats
