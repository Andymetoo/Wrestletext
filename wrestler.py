from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from cards import Card, Deck


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
    "Fight For Control",
    "Shove Off",
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

    # Card archetype (affects deck distribution)
    archetype: str = "BALANCED"  # "JOBBER" | "BALANCED" | "SUPERSTAR"

    # AI personality
    mistake_prob: float = 0.05

    # Character identity
    moveset: list[str] | None = None
    finisher: str | None = None

    hp: int = MAX_HEALTH
    state: WrestlerState = WrestlerState.STANDING
    grit: int = 20
    max_grit: int = 20

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
    next_damage_taken_multiplier: float = 1.0

    # One-shot card modifier (Hype Shop)
    next_card_bonus: int = 0

    # Card system
    deck: Deck | None = None
    hand: list[Card] | None = None

    def __post_init__(self) -> None:
        if self.body_parts is None:
            self.body_parts = {"HEAD": 100, "BODY": 100, "LEGS": 100}

        if self.moveset is None:
            self.moveset = list(DEFAULT_BRAWLER_MOVESET)

        if self.finisher is None:
            # Reasonable default for the brawler archetype.
            self.finisher = "Powerbomb" if "Powerbomb" in self.moveset else (self.moveset[-1] if self.moveset else "Powerbomb")

        if self.deck is None:
            self.deck = Deck(self.archetype)
        if self.hand is None:
            self.hand = []
        # Phase 2: start at full grit.
        self.grit = int(self.max_grit)
        self.draw_to_full()

        # AI personality defaults by archetype.
        arch = str(self.archetype or "BALANCED").upper()
        if arch == "JOBBER":
            self.mistake_prob = 0.40
        elif arch == "SUPERSTAR":
            self.mistake_prob = 0.05
        else:
            self.mistake_prob = 0.15

    def has_doubles_in_hand(self) -> bool:
        if not self.hand:
            return False
        seen: set[int] = set()
        for c in self.hand:
            v = int(c.value)
            if v in seen:
                return True
            seen.add(v)
        return False

    def has_low_card(self, *, max_value: int = 5) -> bool:
        if not self.hand:
            return False
        return any(int(c.value) <= int(max_value) for c in self.hand)

    def strength_current(self) -> int:
        """Total remaining strength in the undealt pile + current hand.

        Excludes discard pile (spent cards).
        """
        total = 0
        if self.deck is not None:
            total += sum(int(c.value) for c in self.deck.cards)
        if self.hand is not None:
            total += sum(int(c.value) for c in self.hand)
        return int(total)

    def strength_max(self) -> int:
        if self.deck is None:
            return 0
        return int(getattr(self.deck, "max_strength", 0))

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
        """Legacy hook.

        Phase 2: grit economy is card-driven, so this is a no-op.
        """
        return 0

    def spend_grit(self, amount: int) -> bool:
        if amount <= 0:
            return True
        if self.grit < amount:
            return False
        self.grit -= amount
        return True

    # --- Card helpers ---
    def draw_to_full(self, *, hand_size: int = 5) -> None:
        if self.hand is None or self.deck is None:
            return
        need = max(0, int(hand_size) - len(self.hand))
        if need <= 0:
            return
        self.hand.extend(self.deck.draw(need))
        self.hand.sort(key=lambda c: c.value)

    def deck_remaining(self) -> int:
        if self.deck is None:
            return 0
        return self.deck.remaining()

    def can_afford_cards(self, cards: list[Card], *, ignore_cost: bool = False) -> bool:
        if ignore_cost:
            return True
        total_cost = sum(c.grit_cost() for c in cards)
        return self.grit >= total_cost

    def apply_grit_from_cards(self, cards: list[Card], *, ignore_cost: bool = False) -> int:
        """Apply card-driven grit economy.

        - Cards 6-10: cost 2 grit each
        - Cards 1-5: regen +1 grit each
        """
        before = self.grit
        cost = 0 if ignore_cost else sum(c.grit_cost() for c in cards)
        regen = sum(c.grit_regen() for c in cards)
        self.grit = max(0, min(self.max_grit, self.grit - cost + regen))
        return self.grit - before

    def discard_cards(self, cards: list[Card]) -> None:
        if self.hand is None or self.deck is None:
            return
        for c in cards:
            if c in self.hand:
                self.hand.remove(c)
                self.deck.discards.append(c)

    def take_damage(self, amount: int, *, target_part: str | None = None, limb_scale: float = 2.0) -> int:
        """Apply HP damage and (optionally) limb damage.

        Limb damage is a scaled version of HP damage and is applied to the provided target_part.
        """
        amount = max(0, int(amount))
        amount = int(round(amount * float(self.next_damage_taken_multiplier)))
        self.next_damage_taken_multiplier = 1.0
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
