"""Set conditions/parameters for optimization program program"""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructFenceBias,
    ConstructConditions,
    verify_optimization_input,
)


class OptimizationSetup:
    """Handle all game mode optimization parameters."""

    def __init__(self, game_config):
        self.game_config = game_config
        def payout_range(low: float, high: float) -> tuple[int, int]:
            high_val = high if high is not None else 25000
            return (int(low * 100), int(high_val * 100))

        def build_spin_scaling(criteria: str):
            spin_buckets = [
                ((0, 0.5), 0.5, 0.20),
                ((0.5, 1), 0.8, 0.15),
                ((1, 5), 1.0, 0.25),
                ((5, 20), 1.2, 0.20),
                ((20, 50), 1.4, 0.10),
                ((50, 100), 1.6, 0.10),
            ]
            return [
                {
                    "criteria": criteria,
                    "scale_factor": scale,
                    "win_range": payout_range(low, high),
                    "probability": weight,
                }
                for (low, high), scale, weight in spin_buckets
            ]

        def build_regular_fs_scaling(criteria: str):
            fs_buckets = [
                ((0.1, 20), 0.7, 0.15),
                ((20, 50), 0.9, 0.20),
                ((50, 100), 1.1, 0.20),
                ((100, 250), 1.3, 0.20),
                ((250, 500), 1.5, 0.15),
                ((500, 1000), 1.7, 0.07),
                ((1000, 2500), 1.9, 0.03),
            ]
            return [
                {
                    "criteria": criteria,
                    "scale_factor": scale,
                    "win_range": payout_range(low, high),
                    "probability": weight,
                }
                for (low, high), scale, weight in fs_buckets
            ]

        def build_super_fs_scaling(criteria: str):
            fs_buckets = [
                ((0.1, 50), 0.8, 0.10),
                ((50, 100), 1.0, 0.15),
                ((100, 250), 1.2, 0.20),
                ((250, 500), 1.4, 0.20),
                ((500, 1000), 1.6, 0.15),
                ((1000, 2500), 1.8, 0.10),
                ((2500, 25000), 2.0, 0.10),
            ]
            return [
                {
                    "criteria": criteria,
                    "scale_factor": scale,
                    "win_range": payout_range(low, high),
                    "probability": weight,
                }
                for (low, high), scale, weight in fs_buckets
            ]

        base_spin_scaling = build_spin_scaling("basegame")
        regular_fs_scaling = build_regular_fs_scaling("freegame")
        super_fs_scaling = build_super_fs_scaling("freegame")

        def build_base_distributions(reel_weights: dict, zero_quota: float):
            base_only_weights = {self.basegame_type: reel_weights[self.basegame_type].copy()}
            return [
                Distribution(
                    criteria="freegame",
                    quota=0.1,
                    conditions={
                        "reel_weights": reel_weights,
                        "scatter_triggers": {4: 5, 5: 1},
                        "mult_values": {
                            self.basegame_type: self.normal_bonus_mult_weights,
                            self.freegame_type: self.normal_bonus_mult_weights,
                        },
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
                        "mult_values": {
                            self.basegame_type: self.normal_bonus_mult_weights,
                            self.freegame_type: self.normal_bonus_mult_weights,
                        },
                        "force_wincap": False,
                        "force_freegame": False,
                    },
                ),
                Distribution(
                    criteria="basegame",
                    quota=0.9 - zero_quota,
                    conditions={
                        "reel_weights": base_only_weights,
                        "mult_values": {self.basegame_type: self.normal_bonus_mult_weights},
                        "force_wincap": False,
                        "force_freegame": False,
                    },
                ),
            ]

        self.game_config.opt_params = {
            "base": {
                "conditions": {
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.44, hr=260, search_conditions={"symbol": "scatter"}
                    ).return_dict(),
                    "basegame": ConstructConditions(rtp=0.52, hr=3.2).return_dict(),
                },
                "scaling": ConstructScaling(base_spin_scaling + regular_fs_scaling).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=1.8,
                    max_m2m=8.0,
                    pmb_rtp=self.game_config.rtp,
                    sim_trials=5000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                    max_trial_dist=15,
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["basegame"],
                    bias_ranges=[(1.2, 8.0)],
                    bias_weights=[0.5],
                ).return_dict(),
            },
            "bonus_hunt": {
                "conditions": {
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.51, hr=150, search_conditions={"symbol": "scatter"}
                    ).return_dict(),
                    "basegame": ConstructConditions(rtp=0.45, hr=2.2).return_dict(),
                },
                "scaling": ConstructScaling(base_spin_scaling + regular_fs_scaling).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=2.0,
                    max_m2m=10.0,
                    pmb_rtp=self.game_config.rtp,
                    sim_trials=5000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                    max_trial_dist=15,
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["basegame"],
                    bias_ranges=[(1.8, 12.0)],
                    bias_weights=[0.5],
                ).return_dict(),
            },
            "bonus": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.01, av_win=25000, search_conditions=25000).return_dict(),
                    "freegame": ConstructConditions(rtp=0.95, hr="x").return_dict(),
                },
                "scaling": ConstructScaling(regular_fs_scaling).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=1.5,
                    max_m2m=15.0,
                    pmb_rtp=self.game_config.rtp,
                    sim_trials=5000,
                    test_spins=[10, 20, 50],
                    test_weights=[0.6, 0.2, 0.2],
                    score_type="rtp",
                    max_trial_dist=15,
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["freegame"],
                    bias_ranges=[(90.0, 150.0)],
                    bias_weights=[0.1],
                ).return_dict(),
            },
            "super_bonus": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.01, av_win=25000, search_conditions=25000).return_dict(),
                    "freegame": ConstructConditions(rtp=0.95, hr="x").return_dict(),
                },
                "scaling": ConstructScaling(super_fs_scaling).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=1.5,
                    max_m2m=18.0,
                    pmb_rtp=self.game_config.rtp,
                    sim_trials=5000,
                    test_spins=[10, 20, 50],
                    test_weights=[0.6, 0.2, 0.2],
                    score_type="rtp",
                    max_trial_dist=15,
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["freegame"],
                    bias_ranges=[(250.0, 500.0)],
                    bias_weights=[0.2],
                ).return_dict(),
            },
        }

        verify_optimization_input(self.game_config, self.game_config.opt_params)
