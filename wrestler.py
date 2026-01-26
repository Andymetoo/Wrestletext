from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


MAX_HEALTH = 100


class WrestlerState(str, Enum):
    STANDING = "STANDING"
    GROUNDED = "GROUNDED"
    TOP_ROPE = "TOP_ROPE"
    RUNNING = "RUNNING"


@dataclass
class Wrestler:
    name: str
    is_player: bool

    hp: int = MAX_HEALTH
    state: WrestlerState = WrestlerState.STANDING
    grit: int = 10
    max_grit: int = 15

    def hp_pct(self) -> float:
        return max(0.0, min(1.0, self.hp / MAX_HEALTH))

    def regen_grit(self) -> int:
        """Regenerate grit at the start of this wrestler's turn.

        If HP > 75%: +3
        If HP 25-75%: +2
        If HP < 25%: +1
        """
        pct = self.hp_pct()
        if pct > 0.75:
            gain = 3
        elif pct >= 0.25:
            gain = 2
        else:
            gain = 1

        before = self.grit
        self.grit = min(self.max_grit, self.grit + gain)
        return self.grit - before

    def spend_grit(self, amount: int) -> bool:
        if amount <= 0:
            return True
        if self.grit < amount:
            return False
        self.grit -= amount
        return True

    def take_damage(self, amount: int) -> int:
        amount = max(0, int(amount))
        self.hp = max(0, self.hp - amount)
        return amount

    def set_state(self, new_state: WrestlerState) -> None:
        self.state = new_state
