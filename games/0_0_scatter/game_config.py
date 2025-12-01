import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Load all game specific parameters and elements"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "0_0_scatter"
        self.game_name = "candy_carnage_1000"
        self.provider_numer = 0
        self.working_name = "Candy Carnage 1000"
        self.wincap = 25000.0
        self.win_type = "scatter"
        self.rtp = 0.9600
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 6
        # Optionally include variable number of rows per reel
        self.num_rows = [5] * self.num_reels
        # Board and Symbol Properties
        t1, t2, t3 = (8, 9), (10, 11), (12, 36)
        scatter_5, scatter_6 = (5, 5), (6, 36)
        pay_group = {
            (t1, "H1"): 10.0,
            (t2, "H1"): 25.0,
            (t3, "H1"): 50.0,
            (t1, "H2"): 2.5,
            (t2, "H2"): 10.0,
            (t3, "H2"): 25.0,
            (t1, "H3"): 2.0,
            (t2, "H3"): 5.0,
            (t3, "H3"): 15.0,
            (t1, "H4"): 1.5,
            (t2, "H4"): 2.0,
            (t3, "H4"): 12.0,
            (t1, "L1"): 1.0,
            (t2, "L1"): 1.5,
            (t3, "L1"): 10.0,
            (t1, "L2"): 0.8,
            (t2, "L2"): 1.2,
            (t3, "L2"): 8.0,
            (t1, "L3"): 0.5,
            (t2, "L3"): 1.0,
            (t3, "L3"): 5.0,
            (t1, "L4"): 0.4,
            (t2, "L4"): 0.9,
            (t3, "L4"): 4.0,
            (t1, "L5"): 0.25,
            (t2, "L5"): 0.75,
            (t3, "L5"): 2.0,
            (scatter_5, "S"): 5.0,
            (scatter_6, "S"): 100.0,
        }
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True
        self.super_scatter_symbol = "BS"
        self.special_symbols = {
            "wild": [],
            "scatter": ["S", self.super_scatter_symbol],
            "super_scatter": [self.super_scatter_symbol],
            "multiplier": ["M"],
        }
        self.symbol_aliases = {self.super_scatter_symbol: "S"}
        self.bonus_mode_names = {
            "base": "base",
            "bonus_hunt": "bonus_hunt",
            "bonus_buy": "bonus",
            "super_bonus_buy": "super_bonus",
        }
        self.bonus_hunt_scatter_boost_chance = 0.0
        self.normal_bonus_requirement = 4
        self.standard_bonus_initial_spins = 10
        self.super_bonus_initial_spins = 10
        self.bonus_retrigger_increment = 5
        self.super_bonus_regular_requirement = 3
        normal_bonus_mult_weights = {
            2: 380,
            3: 320,
            4: 270,
            5: 230,
            6: 190,
            8: 140,
            10: 120,
            12: 100,
            15: 80,
            20: 60,
            25: 45,
            50: 15,
            100: 3,
            500: 0.6,
            1000: 0.12,
        }
        super_bonus_mult_weights = {
            20: 260,
            25: 220,
            50: 140,
            75: 80,
            100: 40,
            500: 8,
            1000: 1.5,
        }
        self.normal_bonus_mult_weights = normal_bonus_mult_weights
        self.super_bonus_mult_weights = super_bonus_mult_weights

        self.freespin_triggers = {
            self.basegame_type: {
                4: self.standard_bonus_initial_spins,
                5: self.standard_bonus_initial_spins,
                6: self.standard_bonus_initial_spins,
            },
            self.freegame_type: {
                3: self.bonus_retrigger_increment,
                4: self.bonus_retrigger_increment,
                5: self.bonus_retrigger_increment,
                6: self.bonus_retrigger_increment,
            },
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
            self.freegame_type: min(self.freespin_triggers[self.freegame_type].keys()) - 1,
        }
        # Reels
        reels = {
            "BR0": "BR0.csv",
            "BRH0": "BR_HUNT.csv",
            "FR0": "FR0.csv",
            "WCAP": "WCAP.csv",
        }
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["FR0"]
        def build_reel_weights(base_strip: str):
            return {
                self.basegame_type: {base_strip: 1},
                                self.freegame_type: {"FR0": 1, "WCAP": 5},
        }

        base_reel_weights = build_reel_weights("BR0")
        bonus_hunt_reel_weights = build_reel_weights("BRH0")
        standard_mult_values = {
            self.basegame_type: self.normal_bonus_mult_weights,
            self.freegame_type: self.normal_bonus_mult_weights,
        }

        def build_base_distributions(reel_weights: dict, zero_quota: float, freegame_quota: float):
            base_only_weights = {self.basegame_type: reel_weights[self.basegame_type].copy()}
            return [
                    Distribution(
                        criteria="freegame",
                    quota=freegame_quota,
                        conditions={
                        "reel_weights": reel_weights,
                            "scatter_triggers": {4: 5, 5: 1},
                        "mult_values": standard_mult_values,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                    quota=zero_quota,
                        win_criteria=0.0,
                        conditions={
                        "reel_weights": base_only_weights,
                        "mult_values": standard_mult_values,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                    quota=0.9 - zero_quota - freegame_quota,
                        conditions={
                        "reel_weights": base_only_weights,
                        "mult_values": {self.basegame_type: self.normal_bonus_mult_weights},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
            ]

        buy_reel_weights = {
            self.basegame_type: {"BR0": 1},
            self.freegame_type: {"FR0": 1},
        }
        self.bet_modes = [
            BetMode(
                name=self.bonus_mode_names["base"],
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=build_base_distributions(base_reel_weights, zero_quota=0.05, freegame_quota=0.15),
            ),
            BetMode(
                name=self.bonus_mode_names["bonus_hunt"],
                cost=3.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=build_base_distributions(
                    bonus_hunt_reel_weights, zero_quota=0.05, freegame_quota=0.55
                ),
            ),
            BetMode(
                name=self.bonus_mode_names["bonus_buy"],
                cost=100.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="freegame",
                        quota=1.0,
                        conditions={
                            "reel_weights": buy_reel_weights,
                            "scatter_triggers": {4: 1},
                            "mult_values": standard_mult_values,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    )
                ],
            ),
            BetMode(
                name=self.bonus_mode_names["super_bonus_buy"],
                cost=500.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="freegame",
                        quota=1.0,
                        conditions={
                            "reel_weights": buy_reel_weights,
                            "scatter_triggers": {4: 1},
                            "mult_values": standard_mult_values,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    )
                ],
            ),
        ]
