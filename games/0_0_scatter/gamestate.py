from game_override import GameStateOverride
from src.calculations.scatter import Scatter


class GameState(GameStateOverride):
    """Gamestate for a single spin"""

    def apply_board_rules(self, apply_hunt_boost: bool = False):
        """Apply mode-specific board adjustments after draws/tumbles."""
        if apply_hunt_boost:
            self.maybe_apply_bonus_hunt_boost()
        self.enforce_super_scatter_rules()
        self.get_special_symbols_on_board()

    def run_spin(self, sim: int, simulation_seed=None):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board()
            self.force_super_scatter_on_board()
            self.force_regular_scatter_on_board()
            self.apply_board_rules(
                apply_hunt_boost=self.betmode == self.config.bonus_mode_names["bonus_hunt"]
            )

            self.get_scatterpays_update_wins()
            self.emit_tumble_win_events()  # Transmit win information

            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                self.tumble_game_board()
                self.enforce_super_scatter_rules()
                self.get_special_symbols_on_board()
                self.get_scatterpays_update_wins()
                self.emit_tumble_win_events()  # Transmit win information

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition() and self.check_freespin_entry():
                self.bonus_type = self.pending_bonus_type or "normal"
                self.run_freespin_from_base()
                self.pending_bonus_type = None
                self.bonus_type = "none"

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()
        while self.fs < self.tot_fs:
            # Resets global multiplier at each spin
            self.update_freespin()
            self.draw_board()
            self.apply_board_rules(apply_hunt_boost=False)

            self.get_scatterpays_update_wins()
            self.emit_tumble_win_events()  # Transmit win information

            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                self.tumble_game_board()
                self.enforce_super_scatter_rules()
                self.get_special_symbols_on_board()
                self.get_scatterpays_update_wins()
                self.emit_tumble_win_events()  # Transmit win information

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

        self.end_freespin()
