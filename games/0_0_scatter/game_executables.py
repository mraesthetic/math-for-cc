"""

"""

from copy import copy

from game_calculations import GameCalculations
from src.calculations.scatter import Scatter
from game_events import send_mult_info_event
from src.events.events import (
    set_win_event,
    set_total_event,
    fs_trigger_event,
    update_tumble_win_event,
    update_global_mult_event,
    update_freespin_event,
)


class GameExecutables(GameCalculations):
    """Game specific executable functions. Used for grouping commonly used/repeated applications."""

    def set_end_tumble_event(self):
        """After all tumbling events have finished, multiply tumble-win by sum of mult symbols."""
        if self.gametype == self.config.freegame_type:  # Only multipliers in freegame
            board_mult, mult_info = self.get_board_multipliers()
            base_tumble_win = copy(self.win_manager.spin_win)
            self.win_manager.set_spin_win(base_tumble_win * board_mult)
            if self.win_manager.spin_win > 0 and len(mult_info) > 0:
                send_mult_info_event(
                    self,
                    board_mult,
                    mult_info,
                    base_tumble_win,
                    self.win_manager.spin_win,
                )
                update_tumble_win_event(self)

        if self.win_manager.spin_win > 0:
            set_win_event(self)
        set_total_event(self)

    def update_freespin_amount(self, scatter_key: str = "scatter"):
        """Update current and total freespin number and emit event."""
        if self.pending_bonus_type == "super" or self.betmode == self.config.bonus_mode_names["super_bonus_buy"]:
            self.tot_fs = self.config.super_bonus_initial_spins
        elif (
            self.pending_bonus_type == "normal"
            or self.betmode == self.config.bonus_mode_names["bonus_buy"]
            or self.betmode == self.config.bonus_mode_names["bonus_hunt"]
            or self.betmode == self.config.bonus_mode_names["base"]
        ):
            self.tot_fs = self.config.standard_bonus_initial_spins
        else:
            self.tot_fs = self.config.standard_bonus_initial_spins

        if self.gametype == self.config.basegame_type:
            basegame_trigger, freegame_trigger = True, False
        else:
            basegame_trigger, freegame_trigger = False, True
        fs_trigger_event(self, basegame_trigger=basegame_trigger, freegame_trigger=freegame_trigger)

    def get_scatterpays_update_wins(self):
        """Return the board since we are assigning the 'explode' attribute."""
        self.win_data = Scatter.get_scatterpay_wins(
            self.config, self.board, global_multiplier=self.global_multiplier
        )  # Evaluate wins, self.board is modified in-place
        Scatter.record_scatter_wins(self)
        self.win_manager.tumble_win = self.win_data["totalWin"]
        self.win_manager.update_spinwin(self.win_data["totalWin"])  # Update wallet

    def update_freespin(self) -> None:
        """Called before a new reveal during freegame."""
        self.fs += 1
        update_freespin_event(self)
        # Reset global multiplier every spin; bombs reapply per tumble
        self.global_multiplier = 1
        update_global_mult_event(self)
        self.win_manager.reset_spin_win()
        self.tumblewin_mult = 0
        self.win_data = {}

    # --- Scatter helpers -------------------------------------------------
    def get_symbol_positions(self, target_symbol: str) -> list:
        positions = []
        for reel in range(len(self.board)):
            for row in range(len(self.board[reel])):
                if self.board[reel][row].name == target_symbol:
                    positions.append((reel, row))
        return positions

    def replace_symbol(self, reel: int, row: int, target_symbol: str) -> None:
        self.board[reel][row] = self.create_symbol(target_symbol)

    def count_regular_scatters(self) -> int:
        return sum(1 for reel in self.board for sym in reel if sym.name == "S")

    def count_super_scatters(self) -> int:
        return len(self.special_syms_on_board.get("super_scatter", []))

    def _ensure_regular_scatter_count(self, target_count: int, fill_symbol: str = "L1") -> list:
        """Adjust board to contain exactly target_count regular scatters."""
        positions = self.get_symbol_positions("S")
        while len(positions) < target_count:
            placed = False
            for reel in range(len(self.board)):
                for row in range(len(self.board[reel])):
                    sym = self.board[reel][row]
                    if sym.name not in ("S", self.config.super_scatter_symbol):
                        self.replace_symbol(reel, row, "S")
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                break
            positions = self.get_symbol_positions("S")
        if len(positions) > target_count:
            for reel, row in positions[target_count:]:
                self.replace_symbol(reel, row, fill_symbol)
            positions = self.get_symbol_positions("S")
        return positions

    def force_super_scatter_on_board(self) -> None:
        """Ensure super bonus buys visually show exactly 3 S + 1 BS before UI render."""
        if self.betmode != self.config.bonus_mode_names["super_bonus_buy"]:
            return
        for reel, row in self.get_symbol_positions(self.config.super_scatter_symbol):
            self.replace_symbol(reel, row, "S")
        scatter_positions = self._ensure_regular_scatter_count(4)
        if len(scatter_positions) < 4:
            return
        reel, row = scatter_positions[0]
        self.replace_symbol(reel, row, self.config.super_scatter_symbol)
        self.get_special_symbols_on_board()

    def force_regular_scatter_on_board(self) -> None:
        """Guarantee regular bonus buys always show exactly four regular scatters and no BS."""
        if self.betmode != self.config.bonus_mode_names["bonus_buy"]:
            return
        for reel, row in self.get_symbol_positions(self.config.super_scatter_symbol):
            self.replace_symbol(reel, row, "L1")
        self._ensure_regular_scatter_count(4)
        self.get_special_symbols_on_board()

    def should_trigger_super_bonus(self) -> bool:
        if self.betmode == self.config.bonus_mode_names["super_bonus_buy"]:
            return True
        if self.gametype != self.config.basegame_type:
            return False
        if self.count_super_scatters() == 0:
            return False
        return self.count_regular_scatters() >= self.config.super_bonus_regular_requirement

    def check_fs_condition(self, scatter_key: str = "scatter") -> bool:
        if self.should_trigger_super_bonus():
            self.pending_bonus_type = "super"
            return True
        if self.gametype == self.config.basegame_type:
            if self.count_regular_scatters() < self.config.normal_bonus_requirement:
                return False
            result = super().check_fs_condition(scatter_key)
            if result:
                self.pending_bonus_type = "normal"
            return result

        return super().check_fs_condition(scatter_key)

    def update_fs_retrigger_amt(self, scatter_key: str = "scatter") -> None:
        """Retriggers award a flat amount of spins when 3 regular scatters land."""
        if self.count_regular_scatters() >= 3:
            self.tot_fs += self.config.bonus_retrigger_increment
            fs_trigger_event(self, freegame_trigger=True, basegame_trigger=False)
