import random

from game_executables import *
from src.events.events import update_freespin_event, update_global_mult_event
from src.calculations.statistics import get_random_outcome


class GameStateOverride(GameExecutables):
    """
    This class is is used to override or extend universal state.py functions.
    e.g: A specific game may have custom book properties to reset
    """

    def reset_book(self):
        # Reset global values used across multiple projects
        super().reset_book()
        # Reset parameters relevant to local game only
        self.tumble_win = 0
        self.pending_bonus_type = None
        self.bonus_type = "none"

    def reset_fs_spin(self):
        super().reset_fs_spin()
        self.global_multiplier = 1

    def assign_special_sym_function(self):
        self.special_symbol_functions = {"M": [self.assign_mult_property]}

    def assign_mult_property(self, symbol):
        """Assign multiplier values only while in freegames."""
        if self.gametype != self.config.freegame_type:
            return

        weights = self.config.super_bonus_mult_weights if self.bonus_type == "super" else self.config.normal_bonus_mult_weights
        multiplier_value = get_random_outcome(weights)
        symbol.assign_attribute({"multiplier": multiplier_value})

    def check_game_repeat(self):
        """Verify final win matches required betmode conditions."""
        if self.repeat == False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

    # --- Board utilities -------------------------------------------------
    def maybe_apply_bonus_hunt_boost(self):
        if self.betmode != self.config.bonus_mode_names["bonus_hunt"]:
            return
        if self.gametype != self.config.basegame_type:
            return
        if random.random() >= self.config.bonus_hunt_scatter_boost_chance:
            return

        regular_scatters = self.get_symbol_positions("S")
        if len(regular_scatters) >= self.config.normal_bonus_requirement:
            return

        eligible_positions = [
            (reel, row)
            for reel in range(len(self.board))
            for row in range(len(self.board[reel]))
            if not self.board[reel][row].special
        ]
        if not eligible_positions:
            return

        reel, row = random.choice(eligible_positions)
        self.replace_symbol(reel, row, "S")
        self.get_special_symbols_on_board()

    def enforce_super_scatter_rules(self):
        super_symbol = self.config.super_scatter_symbol
        if self.gametype == self.config.freegame_type:
            # Freegames never show BS; convert to standard scatter if present
            for reel, row in self.get_symbol_positions(super_symbol):
                self.replace_symbol(reel, row, "S")
            self.get_special_symbols_on_board()
            return

        positions = self.get_symbol_positions(super_symbol)
        if len(positions) > 1:
            # Keep the earliest occurrence, convert the rest
            for reel, row in positions[1:]:
                self.replace_symbol(reel, row, "S")
            self.get_special_symbols_on_board()
            positions = self.get_symbol_positions(super_symbol)

        if self.betmode == self.config.bonus_mode_names["super_bonus_buy"]:
            # Guarantee exactly one BS when buying the super bonus
            if not positions:
                scatter_positions = self.get_symbol_positions("S")
                if scatter_positions:
                    reel, row = scatter_positions[0]
                    self.replace_symbol(reel, row, super_symbol)
            self.get_special_symbols_on_board()
