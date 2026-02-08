from __future__ import annotations

import random
from dataclasses import dataclass, field

# Card Colors / Suits
# GRAY: Neutral (no bonus)
# RED: Strike
# BLUE: Grapple
# GREEN: Submission/Pin/Aerial
# YELLOW: Wild (matches any attack type)
COLORS: list[str] = ["GRAY", "RED", "BLUE", "GREEN", "YELLOW"]
HEX_COLORS: dict[str, str] = {
    "GRAY": "#777777",
    "RED": "#ff4444",
    "BLUE": "#4488ff",
    "GREEN": "#44ff44",
    "YELLOW": "#ffff44",
}


@dataclass(frozen=True, slots=True)
class Card:
    value: int  # 1-10
    color: str  # one of COLORS
    uid: int = field(default_factory=lambda: random.randint(0, 1_000_000))

    def grit_cost(self) -> int:
        """Cards 6-10 cost a flat 1 grit each. Cards 1-5 cost 0."""
        return 0 if self.value <= 5 else 1

    def grit_regen(self) -> int:
        """Cards 1-5 regen +1 grit each (cap handled by Wrestler). Cards 6-10 regen 0."""
        return 1 if self.value <= 5 else 0

    def color_bonus(self, move_type: str) -> int:
        """Returns +1 if the card color matches the move type.

        GRAY cards never provide a bonus (GRAY means no bonus).
        """
        if self.color == "GRAY":
            return 0
        # Wild cards: match any attack-type move.
        if self.color == "YELLOW":
            return 1 if move_type in {"Strike", "Grapple", "Submission", "Aerial", "Pin"} else 0
        mapping = {
            "Strike": "RED",
            "Grapple": "BLUE",
            "Submission": "GREEN",
            "Aerial": "GREEN",
            "Pin": "GREEN",
            # NOTE: Setup moves do not get a color bonus.
        }
        return 1 if mapping.get(move_type) == self.color else 0


class Deck:
    def __init__(self, archetype: str = "BALANCED"):
        self.cards: list[Card] = []
        self.discards: list[Card] = []
        self._build(archetype)
        # Total value of a full 50-card deck (constant for a given build).
        self.max_strength: int = sum(int(c.value) for c in self.cards)
        self.shuffle()

    def _build(self, archetype: str) -> None:
        # Value distribution (50 cards total)
        if archetype == "JOBBER":
            dist = {1: 8, 2: 8, 3: 8, 4: 6, 5: 6, 6: 5, 7: 4, 8: 2, 9: 2, 10: 1}
            gray_chance = 0.55
        elif archetype == "SUPERSTAR":
            dist = {1: 3, 2: 3, 3: 4, 4: 5, 5: 6, 6: 6, 7: 6, 8: 6, 9: 6, 10: 5}
            gray_chance = 0.20
        else:  # BALANCED
            dist = {1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 6: 5, 7: 5, 8: 5, 9: 5, 10: 5}
            gray_chance = 0.40

        cards: list[Card] = []
        for val, count in dist.items():
            for _ in range(count):
                if random.random() < gray_chance:
                    color = "GRAY"
                else:
                    # Make wild (YELLOW) rarer than the main type colors.
                    pool = ["RED", "BLUE", "GREEN", "YELLOW"]
                    weights = [40, 40, 40, 8]
                    color = random.choices(pool, weights=weights, k=1)[0]
                cards.append(Card(value=int(val), color=color))

        # Ensure exactly 50 cards.
        while len(cards) > 50:
            cards.pop()
        while len(cards) < 50:
            cards.append(Card(value=random.randint(1, 5), color="GRAY"))

        self.cards = cards

    def shuffle(self) -> None:
        self.cards.extend(self.discards)
        self.discards.clear()
        random.shuffle(self.cards)

    def draw(self, amount: int = 1) -> list[Card]:
        drawn: list[Card] = []
        for _ in range(int(amount)):
            if not self.cards:
                self.shuffle()
            if not self.cards:
                break
            drawn.append(self.cards.pop())
        return drawn

    def remaining(self) -> int:
        return len(self.cards)
