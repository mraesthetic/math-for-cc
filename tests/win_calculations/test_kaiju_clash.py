"""Targeted tests for Kaiju Clash math helpers."""

from pathlib import Path
import sys

import pytest

# Ensure Kaiju Clash modules are importable (game directory lacks package __init__).
GAME_DIR = Path(__file__).resolve().parents[2] / "games" / "0_0_kaiju_clash"
if str(GAME_DIR) not in sys.path:
    sys.path.insert(0, str(GAME_DIR))

import game_config  # type: ignore  # pylint: disable=import-error
import gamestate  # type: ignore  # pylint: disable=import-error
import vs_logic  # type: ignore  # pylint: disable=import-error


def test_vs_multiplier_application_stacks_properly():
    """apply_vs_to_wins should multiply wins per involved VS reel."""
    win_data = {
        "totalWin": 50.0,
        "wins": [
            {
                "positions": [
                    {"reel": 0, "row": 0},
                    {"reel": 1, "row": 0},
                    {"reel": 2, "row": 0},
                ],
                "win": 20.0,
                "meta": {"lineIndex": 1, "multiplier": 1},
            },
            {
                "positions": [
                    {"reel": 0, "row": 1},
                    {"reel": 1, "row": 1},
                    {"reel": 4, "row": 1},
                ],
                "win": 30.0,
                "meta": {"lineIndex": 2, "multiplier": 1},
            },
        ],
    }
    vs_reels = {
        1: {"reel": 1, "character": "megazor", "multiplier": 3},
        4: {"reel": 4, "character": "volcron", "multiplier": 5},
    }

    result = vs_logic.apply_vs_to_wins(win_data, vs_reels)

    assert result["wins"][0]["win"] == pytest.approx(60.0)
    assert result["wins"][0]["meta"]["baseAmount"] == pytest.approx(20.0)
    assert result["wins"][0]["meta"]["multiplier"] == 3

    assert result["wins"][1]["win"] == pytest.approx(450.0)
    assert result["wins"][1]["meta"]["baseAmount"] == pytest.approx(30.0)
    assert result["wins"][1]["meta"]["multiplier"] == 15

    assert result["totalWin"] == pytest.approx(510.0)


def test_determine_bonus_mode_honours_forced_distribution():
    """Forced distributions should dictate the Clash mode even with 3 scatters."""
    config = game_config.GameConfig()
    state = gamestate.GameState(config)
    state.betmode = "base"

    state.criteria = "super_clash"
    assert state.determine_bonus_mode(3) == "super"

    state.criteria = "regular_clash"
    assert state.determine_bonus_mode(3) == "regular"

    state.criteria = "base_spin"
    assert state.determine_bonus_mode(4) == "super"
    assert state.determine_bonus_mode(3) == "regular"


def test_free_spin_trigger_event_contains_bonus_mode_and_zero_index_positions():
    """Kaiju free-spin trigger metadata should match blueprint expectations."""
    config = game_config.GameConfig()
    state = gamestate.GameState(config)
    state.betmode = "base"
    state.criteria = "regular_clash"
    state.gametype = state.config.basegame_type
    state.active_bonus_mode = "regular"
    state.refresh_special_syms()
    state.special_syms_on_board["scatter"] = [
        {"reel": 0, "row": 0},
        {"reel": 2, "row": 1},
        {"reel": 4, "row": 2},
    ]

    state.update_freespin_amount()
    event = state.book.events[-1]

    assert event["type"] == "freeSpinTrigger"
    assert event["totalFs"] == 10
    assert event["bonusMode"] == "regular"
    assert all(pos["row"] in range(state.config.num_rows[pos["reel"]]) for pos in event["positions"])

