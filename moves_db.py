"""Move registry for the state-based tactical wrestling simulation.

Each move entry contains the required fields:
- damage: int
- cost: int (Grit)
- type: one of (Strike, Grapple, Aerial, Submission, Pin, Setup)
- req_user_state: one of (STANDING, GROUNDED, TOP_ROPE, RUNNING, GRAPPLE_WEAK, GRAPPLE_STRONG, GRAPPLE_BACK, ANY)
- req_target_state: one of (STANDING, GROUNDED, TOP_ROPE, RUNNING, GRAPPLE_WEAK, GRAPPLE_STRONG, GRAPPLE_BACK, ANY)
- flavor_text: str

N64 additions:
- target_part: one of (HEAD, BODY, LEGS, NONE)
- hype_gain: int (0-100). Applied only on successful execution.
- is_finisher: bool

Optional fields used by the engine:
- set_user_state: str
- set_target_state: str
- notes: str (non-functional metadata)
"""

from __future__ import annotations

"""Move registry for the state-based tactical wrestling simulation.

Refactored for AKI-style Hierarchy:
STANDING -> GRAPPLE_WEAK -> GRAPPLE_STRONG
                         -> GRAPPLE_BACK
"""

from __future__ import annotations

from typing import Any, Dict


Move = Dict[str, Any]


MOVES: Dict[str, Move] = {
    # =========================================================================
    # UNIVERSAL / UTILITY
    # =========================================================================
    "Rest": {
        "damage": 0,
        "cost": 0,
        "type": "Setup",
        "req_user_state": "ANY",
        "req_target_state": "ANY",
        "target_part": "NONE",
        "hype_gain": 0,
        "is_finisher": False,
        "flavor_text": "You create space and breathe...",
        "notes": "High regen handled by engine.",
    },
    "Taunt": {
        "damage": 0,
        "cost": 0,
        "type": "Setup",
        "req_user_state": "STANDING",
        "req_target_state": "ANY",
        "target_part": "NONE",
        "hype_gain": 35,
        "is_finisher": False,
        "flavor_text": "You showboat to the crowd and fire up!",
    },
    "Slow Stand Up": {
        "damage": 0,
        "cost": 0,
        "type": "Setup",
        "req_user_state": "GROUNDED",
        "req_target_state": "ANY",
        "target_part": "NONE",
        "hype_gain": 0,
        "is_finisher": False,
        "flavor_text": "They crawl toward the ropes and try to rise...",
        "set_user_state": "STANDING",
    },
    "Kip-up": {
        "damage": 0,
        "cost": 2,
        "type": "Setup",
        "req_user_state": "GROUNDED",
        "req_target_state": "ANY",
        "target_part": "NONE",
        "hype_gain": 4,
        "is_finisher": False,
        "flavor_text": "You spring to your feet with a kip-up!",
        "set_user_state": "STANDING",
    },

    # =========================================================================
    # NEUTRAL (STANDING)
    # =========================================================================
    "Lock Up": {
        "damage": 0,
        "cost": 2,
        "type": "Setup",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "set_user_state": "GRAPPLE_WEAK",  # <--- THE GATEWAY
        "set_target_state": "GRAPPLE_WEAK",
        "target_part": "NONE",
        "hype_gain": 2,
        "is_finisher": False,
        "flavor_text": "You step in and tie up with them!",
        "notes": "Engine runs neutral RPS; triggers entry to WEAK state.",
    },
    "Jab": {
        "damage": 5,
        "cost": 2,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "target_part": "HEAD",
        "hype_gain": 4,
        "is_finisher": False,
        "flavor_text": "A quick jab snaps their head back!",
    },
    "Front Kick": {
        "damage": 7,
        "cost": 3,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "target_part": "BODY",
        "hype_gain": 6,
        "is_finisher": False,
        "flavor_text": "A stiff kick to the midsection doubles them over!",
    },
    "Desperation Slap": {
        "damage": 1,
        "cost": 0,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "target_part": "HEAD",
        "hype_gain": 1,
        "is_finisher": False,
        "flavor_text": "A tired slap—more annoyance than impact.",
    },

    # =========================================================================
    # GRAPPLE TIER 1: WEAK GRAPPLE (Quick moves & Transitions)
    # =========================================================================
    "Deepen Hold": {
        "damage": 0,
        "cost": 0,
        "type": "Setup",
        "req_user_state": "GRAPPLE_WEAK",
        "req_target_state": "GRAPPLE_WEAK",
        "set_user_state": "GRAPPLE_STRONG",  # <--- TIER UP
        "set_target_state": "GRAPPLE_STRONG",
        "target_part": "NONE",
        "hype_gain": 0,
        "is_finisher": False,
        "flavor_text": "You shift your weight to secure a deeper hold...",
        "notes": "Triggers chain wrestling minigame.",
    },
    "Go Behind": {
        "damage": 0,
        "cost": 2,
        "type": "Setup",
        "req_user_state": "GRAPPLE_WEAK",
        "req_target_state": "GRAPPLE_WEAK",
        "set_user_state": "GRAPPLE_BACK",  # <--- FLANK
        "set_target_state": "GRAPPLE_BACK",
        "target_part": "NONE",
        "hype_gain": 2,
        "is_finisher": False,
        "flavor_text": "You duck the arm and slip behind them!",
    },
    "Irish Whip": {
        "damage": 0,
        "cost": 3,
        "type": "Grapple",
        "req_user_state": "GRAPPLE_WEAK",
        "req_target_state": "GRAPPLE_WEAK",
        "set_user_state": "STANDING",
        "set_target_state": "RUNNING",
        "target_part": "LEGS",
        "hype_gain": 5,
        "is_finisher": False,
        "flavor_text": "Sends them to the ropes with an Irish Whip!",
    },
    "Snap Suplex": {
        "damage": 11,
        "cost": 5,
        "type": "Grapple",
        "req_user_state": "GRAPPLE_WEAK",
        "req_target_state": "GRAPPLE_WEAK",
        "set_user_state": "STANDING",
        "set_target_state": "GROUNDED",
        "target_part": "BODY",
        "hype_gain": 10,
        "is_finisher": False,
        "flavor_text": "Hooks the waist and snaps them down!",
    },
    "Arm Drag": {
        "damage": 8,
        "cost": 3,
        "type": "Grapple",
        "req_user_state": "GRAPPLE_WEAK",
        "req_target_state": "GRAPPLE_WEAK",
        "set_user_state": "STANDING",
        "set_target_state": "GROUNDED",
        "target_part": "BODY",
        "hype_gain": 6,
        "is_finisher": False,
        "flavor_text": "Fluid motion—over they go with an arm drag!",
    },
    "Chain Wrestle": {
        "damage": 0,
        "cost": 0,
        "type": "Setup",
        "req_user_state": "GRAPPLE_WEAK",
        "req_target_state": "GRAPPLE_WEAK",
        "target_part": "NONE",
        "hype_gain": 5,
        "is_finisher": False,
        "flavor_text": "You fight for better positioning...",
        "notes": "Stays in Weak state to build hype/grit.",
    },

    # =========================================================================
    # GRAPPLE TIER 2: STRONG GRAPPLE (Heavy Hitters)
    # =========================================================================
    "DDT": {
        "damage": 16,
        "cost": 6,
        "type": "Grapple",
        "req_user_state": "GRAPPLE_STRONG",
        "req_target_state": "GRAPPLE_STRONG",
        "set_user_state": "STANDING",
        "set_target_state": "GROUNDED",
        "target_part": "HEAD",
        "hype_gain": 15,
        "is_finisher": True,
        "flavor_text": "Front facelock... DDT! Spiked to the canvas!",
    },
    "Powerbomb": {
        "damage": 22,
        "cost": 8,
        "type": "Grapple",
        "req_user_state": "GRAPPLE_STRONG",
        "req_target_state": "GRAPPLE_STRONG",
        "set_user_state": "STANDING",
        "set_target_state": "GROUNDED",
        "target_part": "BODY",
        "hype_gain": 20,
        "is_finisher": True,
        "flavor_text": "Hoists them up... POWERBOMB! The ring shakes!",
    },
    "Piledriver": {
        "damage": 20,
        "cost": 7,
        "type": "Grapple",
        "req_user_state": "GRAPPLE_STRONG",
        "req_target_state": "GRAPPLE_STRONG",
        "set_user_state": "STANDING",
        "set_target_state": "GROUNDED",
        "target_part": "HEAD",
        "hype_gain": 18,
        "is_finisher": False,
        "flavor_text": "Head between the legs... PILEDRIVER! That neck is compressed!",
    },
    "Bearhug": {
        "damage": 12,
        "cost": 5,
        "type": "Submission",
        "req_user_state": "GRAPPLE_STRONG",
        "req_target_state": "GRAPPLE_STRONG",
        "set_user_state": "GRAPPLE_STRONG",
        "set_target_state": "GRAPPLE_STRONG",
        "target_part": "BODY",
        "hype_gain": 10,
        "is_finisher": False,
        "flavor_text": "Squeezing the life out of them with a Bearhug!",
        "notes": "Does not break the hold; stays in Strong state.",
    },

    # =========================================================================
    # GRAPPLE TIER 3: BACK GRAPPLE
    # =========================================================================
    "German Suplex": {
        "damage": 18,
        "cost": 7,
        "type": "Grapple",
        "req_user_state": "GRAPPLE_BACK",
        "req_target_state": "GRAPPLE_BACK",
        "set_user_state": "GROUNDED",
        "set_target_state": "GROUNDED",
        "target_part": "HEAD",
        "hype_gain": 16,
        "is_finisher": True,
        "flavor_text": "Waistlock from behind... GERMAN SUPLEX! High angle bridge!",
    },
    "Backbreaker": {
        "damage": 14,
        "cost": 5,
        "type": "Grapple",
        "req_user_state": "GRAPPLE_BACK",
        "req_target_state": "GRAPPLE_BACK",
        "set_user_state": "STANDING",
        "set_target_state": "GROUNDED",
        "target_part": "BODY",
        "hype_gain": 12,
        "is_finisher": False,
        "flavor_text": "Lifts them up... and drops them knee-first on the spine!",
    },
    "Schoolboy Pin": {
        "damage": 0,
        "cost": 4,
        "type": "Pin",
        "req_user_state": "GRAPPLE_BACK",
        "req_target_state": "GRAPPLE_BACK",
        "target_part": "NONE",
        "hype_gain": 10,
        "is_finisher": False,
        "flavor_text": "Quickly rolls them up for a Schoolboy Pin!",
    },

    # =========================================================================
    # RUNNING / COUNTERS
    # =========================================================================
    "Clothesline": {
        "damage": 10,
        "cost": 4,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "RUNNING",
        "set_target_state": "GROUNDED",
        "target_part": "HEAD",
        "hype_gain": 10,
        "is_finisher": False,
        "flavor_text": "CLOTHESLINE! They flip inside-out!",
    },
    "Back Body Drop": {
        "damage": 12,
        "cost": 4,
        "type": "Grapple",
        "req_user_state": "STANDING",
        "req_target_state": "RUNNING",
        "set_target_state": "GROUNDED",
        "target_part": "BODY",
        "hype_gain": 12,
        "is_finisher": False,
        "flavor_text": "Catches them charging in... BACK BODY DROP!",
    },
    "Stop Short": {
        "damage": 0,
        "cost": 1,
        "type": "Setup",
        "req_user_state": "RUNNING",
        "req_target_state": "ANY",
        "set_user_state": "STANDING",
        "target_part": "NONE",
        "hype_gain": 0,
        "is_finisher": False,
        "flavor_text": "You put on the brakes and reset your stance!",
    },
    "Rebound Lariat": {
        "damage": 9,
        "cost": 4,
        "type": "Strike",
        "req_user_state": "RUNNING",
        "req_target_state": "STANDING",
        "set_user_state": "STANDING",
        "set_target_state": "GROUNDED",
        "target_part": "HEAD",
        "hype_gain": 12,
        "is_finisher": False,
        "flavor_text": "Off the ropes... REBOUND LARIAT!",
    },

    # =========================================================================
    # GROUND OFFENSE
    # =========================================================================
    "Stomp": {
        "damage": 6,
        "cost": 2,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "GROUNDED",
        "target_part": "BODY",
        "hype_gain": 4,
        "is_finisher": False,
        "flavor_text": "Boots down—no mercy!",
    },
    "Pick Up": {
        "damage": 0,
        "cost": 1,
        "type": "Setup",
        "req_user_state": "STANDING",
        "req_target_state": "GROUNDED",
        "set_target_state": "STANDING",
        "target_part": "NONE",
        "hype_gain": 0,
        "is_finisher": False,
        "flavor_text": "You haul them back up to their feet.",
    },
    "Pin": {
        "damage": 0,
        "cost": 3,
        "type": "Pin",
        "req_user_state": "STANDING",
        "req_target_state": "GROUNDED",
        "target_part": "NONE",
        "hype_gain": 6,
        "is_finisher": False,
        "flavor_text": "Hooks the leg! Going for the cover!",
    },
    "Submission Hold": {
        "damage": 0,
        "cost": 4,
        "type": "Submission",
        "req_user_state": "STANDING",
        "req_target_state": "GROUNDED",
        "target_part": "BODY",
        "hype_gain": 8,
        "is_finisher": True,
        "flavor_text": "You cinch it in deep—nowhere to go!",
    },
    "Possum": {
        "damage": 0,
        "cost": 3,
        "type": "Setup",
        "req_user_state": "GROUNDED",
        "req_target_state": "STANDING",
        "set_user_state": "STANDING",
        "target_part": "NONE",
        "hype_gain": 5,
        "is_finisher": False,
        "flavor_text": "You play possum... then explode with a cheap roll-up threat!",
    },

    # =========================================================================
    # TOP ROPE
    # =========================================================================
    "Climb Turnbuckle": {
        "damage": 0,
        "cost": 2,
        "type": "Setup",
        "req_user_state": "STANDING",
        "req_target_state": "ANY",
        "set_user_state": "TOP_ROPE",
        "target_part": "NONE",
        "hype_gain": 2,
        "is_finisher": False,
        "flavor_text": "You scale the turnbuckles and steady your footing...",
    },
    "Climb Down": {
        "damage": 0,
        "cost": 0,
        "type": "Setup",
        "req_user_state": "TOP_ROPE",
        "req_target_state": "ANY",
        "set_user_state": "STANDING",
        "target_part": "NONE",
        "hype_gain": 0,
        "is_finisher": False,
        "flavor_text": "They climb back down to the mat.",
    },
    "Shove Off Turnbuckle": {
        "damage": 8,
        "cost": 4,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "TOP_ROPE",
        "set_target_state": "GROUNDED",
        "target_part": "BODY",
        "hype_gain": 10,
        "is_finisher": False,
        "flavor_text": "A nasty shove sends them crashing down!",
    },
    "Superplex": {
        "damage": 22,
        "cost": 10,
        "type": "Grapple",
        "req_user_state": "TOP_ROPE",
        "req_target_state": "TOP_ROPE",
        "set_user_state": "GROUNDED",
        "set_target_state": "GROUNDED",
        "target_part": "BODY",
        "hype_gain": 25,
        "is_finisher": True,
        "flavor_text": "Hooks them up top—SUPERPLEX! Both bodies hit hard!",
    },
    "Moonsault": {
        "damage": 16,
        "cost": 7,
        "type": "Aerial",
        "req_user_state": "TOP_ROPE",
        "req_target_state": "GROUNDED",
        "set_user_state": "STANDING",
        "target_part": "BODY",
        "hype_gain": 22,
        "is_finisher": True,
        "flavor_text": "MOONSAULT! Picture-perfect rotation!",
    },
    "Diving Elbow": {
        "damage": 13,
        "cost": 6,
        "type": "Aerial",
        "req_user_state": "TOP_ROPE",
        "req_target_state": "GROUNDED",
        "set_user_state": "STANDING",
        "target_part": "BODY",
        "hype_gain": 18,
        "is_finisher": False,
        "flavor_text": "You soar through the air—DIVING ELBOW!",
    },
}
