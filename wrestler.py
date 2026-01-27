from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


MAX_HEALTH = 100


DEFAULT_BRAWLER_MOVESET: list[str] = [
    # Neutral
    "Jab",
    "Front Kick",
    "Desperation Slap",
    "Lock Up",
    "Taunt",
    "Rest",
    # In-grapple
    "Chain Wrestle",
    "Snap Suplex",
    "DDT",
    "Powerbomb",
    "Irish Whip",
    # Running / counters
    "Clothesline",
    "Back Body Drop",
    "Stop Short",
    "Rebound Lariat",
    # Grounded / finish
    "Stomp",
    "Pick Up",
    "Pin",
    "Submission Hold",
    # Recovery / positioning
    "Kip-up",
    "Slow Stand Up",
    # Top rope
    "Climb Turnbuckle",
    "Climb Down",
    "Diving Elbow",
    "Moonsault",
    "Shove Off Turnbuckle",
    "Superplex",
]


class WrestlerState(str, Enum):
    STANDING = "STANDING"
    GROUNDED = "GROUNDED"
    TOP_ROPE = "TOP_ROPE"
    RUNNING = "RUNNING"
    # Grapple tiers (AKI-style)
    GRAPPLE_WEAK = "GRAPPLE_WEAK"  # initial tie-up (light moves, whip, go-behind)
    GRAPPLE_STRONG = "GRAPPLE_STRONG"  # deep control (big throws, specials)
    GRAPPLE_BACK = "GRAPPLE_BACK"  # behind opponent (back suplexes, schoolboy)


class GrappleRole(str, Enum):
    OFFENSE = "OFFENSE"
    DEFENSE = "DEFENSE"


@dataclass
class Wrestler:
    name: str
    is_player: bool

    # Character identity
    moveset: list[str] | None = None
    finisher: str | None = None

    hp: int = MAX_HEALTH
    state: WrestlerState = WrestlerState.STANDING
    grit: int = 10
    max_grit: int = 15

    # N64-style meters/systems
    hype: int = 0  # 0..100
    flow_turns_remaining: int = 0  # when >0: costs are 0 and grit regen doubles

    # Limb health (0..100)
    body_parts: dict[str, int] = None  # set in __post_init__

    # Grapple control (only meaningful while in a grapple tier)
    grapple_role: GrappleRole | None = None

    # Status
    stun_turns: int = 0

    # One-shot combat modifiers
    next_damage_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if self.body_parts is None:
            self.body_parts = {"HEAD": 100, "BODY": 100, "LEGS": 100}

        if self.moveset is None:
            self.moveset = list(DEFAULT_BRAWLER_MOVESET)

        if self.finisher is None:
            # Reasonable default for the brawler archetype.
            self.finisher = "Powerbomb" if "Powerbomb" in self.moveset else (self.moveset[-1] if self.moveset else "Powerbomb")

    def hp_pct(self) -> float:
        return max(0.0, min(1.0, self.hp / MAX_HEALTH))

    def limb_pct(self, part: str) -> float:
        v = int(self.body_parts.get(part, 100))
        return max(0.0, min(1.0, v / 100.0))

    def is_flow(self) -> bool:
        return self.flow_turns_remaining > 0

    def is_critical_head(self) -> bool:
        return int(self.body_parts.get("HEAD", 100)) < 25

    def is_critical_body(self) -> bool:
        return int(self.body_parts.get("BODY", 100)) < 25

    def is_critical_legs(self) -> bool:
        return int(self.body_parts.get("LEGS", 100)) < 25

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

        # Body damage reduces stamina recovery.
        if self.is_critical_body():
            gain = max(0, gain // 2)

        # Flow state: grit regen doubles.
        if self.is_flow():
            gain *= 2

        before = self.grit
        self.grit = min(self.max_grit, self.grit + gain)
        return self.grit - before

    def spend_grit(self, amount: int) -> bool:
        # Flow state: all costs are 0.
        if self.is_flow():
            return True
        if amount <= 0:
            return True
        if self.grit < amount:
            return False
        self.grit -= amount
        return True

    def take_damage(self, amount: int, *, target_part: str | None = None, limb_scale: float = 2.0) -> int:
        """Apply HP damage and (optionally) limb damage.

        Limb damage is a scaled version of HP damage and is applied to the provided target_part.
        """
        amount = max(0, int(amount))
        self.hp = max(0, self.hp - amount)
        if target_part in {"HEAD", "BODY", "LEGS"} and amount > 0:
            self.damage_limb(target_part, int(round(amount * limb_scale)))
        return amount

    def damage_limb(self, part: str, amount: int) -> int:
        if part not in {"HEAD", "BODY", "LEGS"}:
            return 0
        before = int(self.body_parts.get(part, 100))
        after = max(0, before - max(0, int(amount)))
        self.body_parts[part] = after
        return before - after

    def set_state(self, new_state: WrestlerState) -> None:
        self.state = new_state

    def is_in_grapple(self) -> bool:
        return self.state in {
            WrestlerState.GRAPPLE_WEAK,
            WrestlerState.GRAPPLE_STRONG,
            WrestlerState.GRAPPLE_BACK,
        }

    def clear_grapple(self) -> None:
        self.grapple_role = None
        if self.is_in_grapple():
            self.state = WrestlerState.STANDING

    def add_hype(self, amount: int) -> None:
        if amount <= 0:
            return
        self.hype = min(100, self.hype + int(amount))
        if self.hype >= 100 and not self.is_flow():
            self.flow_turns_remaining = 3

    def on_turn_end(self) -> None:
        if self.flow_turns_remaining > 0:
            self.flow_turns_remaining -= 1
            if self.flow_turns_remaining <= 0:
                self.flow_turns_remaining = 0
                self.hype = 0
