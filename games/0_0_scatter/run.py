#!/usr/bin/env python3
"""Main file for generating results for sample ways-pay game."""

import shutil
from pathlib import Path

from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs


def sync_lookup_tables(game_root: Path) -> None:
    """Copy freshly generated lookup tables into publish_files for RGS verification."""
    src_dir = game_root / "library" / "lookup_tables"
    dst_dir = game_root / "library" / "publish_files"
    if not src_dir.exists() or not dst_dir.exists():
        return
    for src in src_dir.glob("lookUpTable_*.csv"):
        target = dst_dir / f"{src.stem}_0.csv"
        shutil.copy2(src, target)

if __name__ == "__main__":

    num_threads = 32
    rust_threads = 64
    batching_size = 12500
    compression = True
    profiling = False

    sims_per_mode = 400_000
    num_sim_args = {
        "base": sims_per_mode,
        "bonus_hunt": sims_per_mode,
        "bonus": sims_per_mode,
        "super_bonus": sims_per_mode,
    }

    run_conditions = {
        "run_sims": True,
        "run_optimization": False,
        "run_analysis": False,
        "run_format_checks": True,
    }
    target_modes = ["base", "bonus_hunt", "bonus", "super_bonus"]

    game_root = Path(__file__).parent.resolve()

    config = GameConfig()
    OptimizationSetup(config)
    gamestate = GameState(config)

    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        sync_lookup_tables(game_root)
        execute_all_tests(config)
