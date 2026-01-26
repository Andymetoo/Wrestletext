"""Move registry for the state-based tactical wrestling simulation.

Each move entry contains the required fields:
- damage: int
- cost: int (Grit)
- type: one of (Strike, Grapple, Aerial, Submission, Pin, Setup)
- req_user_state: one of (STANDING, GROUNDED, TOP_ROPE, RUNNING, ANY)
- req_target_state: one of (STANDING, GROUNDED, TOP_ROPE, RUNNING, ANY)
- flavor_text: str

Optional fields used by the engine:
- set_user_state: str
- set_target_state: str
- notes: str (non-functional metadata)
"""

from __future__ import annotations

from typing import Any, Dict


Move = Dict[str, Any]


MOVES: Dict[str, Move] = {
    # --- Universal / economy ---
    "Rest": {
        "damage": 0,
        "cost": 0,
        "type": "Setup",
        "req_user_state": "ANY",
        "req_target_state": "ANY",
        "flavor_text": "You create space and breathe...",
        "notes": "High regen handled by engine.",
    },

    # --- Standing basics ---
    "Lock Up": {
        "damage": 0,
        "cost": 2,
        "type": "Setup",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "flavor_text": "Collar-and-elbow tie-up—fight for position!",
        "notes": "Triggers push/hold minigame; winner earns a grapple follow-up.",
    },
    "Jab": {
        "damage": 5,
        "cost": 2,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "flavor_text": "A quick jab snaps their head back!",
    },
    "Front Kick": {
        "damage": 7,
        "cost": 3,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "flavor_text": "A stiff kick to the midsection doubles them over!",
    },
    "Snap Suplex": {
        "damage": 11,
        "cost": 5,
        "type": "Grapple",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "flavor_text": "You hook the waist and snap them down!",
        "set_target_state": "GROUNDED",
    },
    "DDT": {
        "damage": 14,
        "cost": 6,
        "type": "Grapple",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "flavor_text": "Front facelock—DDT! Spiked to the canvas!",
        "set_target_state": "GROUNDED",
    },
    "Powerbomb": {
        "damage": 20,
        "cost": 8,
        "type": "Grapple",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "flavor_text": "You hoist them up—POWERBOMB! The ring shakes!",
        "set_target_state": "GROUNDED",
    },

    # --- State transitions / momentum ---
    "Irish Whip": {
        "damage": 0,
        "cost": 3,
        "type": "Setup",
        "req_user_state": "STANDING",
        "req_target_state": "STANDING",
        "flavor_text": "You send them to the ropes with an Irish Whip!",
        "set_target_state": "RUNNING",
    },
    "Clothesline": {
        "damage": 10,
        "cost": 4,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "RUNNING",
        "flavor_text": "CLOTHESLINE! They flip inside-out and crash to the mat!",
        "set_target_state": "GROUNDED",
    },
    "Climb Turnbuckle": {
        "damage": 0,
        "cost": 2,
        "type": "Setup",
        "req_user_state": "STANDING",
        "req_target_state": "ANY",
        "flavor_text": "You scale the turnbuckles and steady your footing...",
        "set_user_state": "TOP_ROPE",
    },
    "Shove Off Turnbuckle": {
        "damage": 8,
        "cost": 4,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "TOP_ROPE",
        "flavor_text": "A nasty shove sends them crashing down!",
        "set_target_state": "GROUNDED",
    },
    "Kip-up": {
        "damage": 0,
        "cost": 2,
        "type": "Setup",
        "req_user_state": "GROUNDED",
        "req_target_state": "ANY",
        "flavor_text": "You spring to your feet with a kip-up!",
        "set_user_state": "STANDING",
    },
    "Possum": {
        "damage": 0,
        "cost": 3,
        "type": "Setup",
        "req_user_state": "GROUNDED",
        "req_target_state": "STANDING",
        "flavor_text": "You play possum... then explode with a cheap roll-up threat!",
        "set_user_state": "STANDING",
        "notes": "Engine applies a small chance to trip the opponent grounded.",
    },

    # --- If you get whipped / forced into motion ---
    "Stop Short": {
        "damage": 0,
        "cost": 1,
        "type": "Setup",
        "req_user_state": "RUNNING",
        "req_target_state": "ANY",
        "flavor_text": "You put on the brakes and reset your stance!",
        "set_user_state": "STANDING",
    },
    "Rebound Lariat": {
        "damage": 9,
        "cost": 4,
        "type": "Strike",
        "req_user_state": "RUNNING",
        "req_target_state": "STANDING",
        "flavor_text": "Off the ropes—REBOUND LARIAT!",
        "set_user_state": "STANDING",
        "set_target_state": "GROUNDED",
    },

    # --- Grounded offense / finish attempts ---
    "Stomp": {
        "damage": 6,
        "cost": 2,
        "type": "Strike",
        "req_user_state": "STANDING",
        "req_target_state": "GROUNDED",
        "flavor_text": "Boots down—no mercy!",
    },
    "Pick Up": {
        "damage": 0,
        "cost": 1,
        "type": "Setup",
        "req_user_state": "STANDING",
        "req_target_state": "GROUNDED",
        "flavor_text": "You haul them back up to their feet.",
        "set_target_state": "STANDING",
    },
    "Pin": {
        "damage": 0,
        "cost": 3,
        "type": "Pin",
        "req_user_state": "STANDING",
        "req_target_state": "GROUNDED",
        "flavor_text": "Hooks the leg! Going for the cover!",
    },
    "Submission Hold": {
        "damage": 0,
        "cost": 4,
        "type": "Submission",
        "req_user_state": "STANDING",
        "req_target_state": "GROUNDED",
        "flavor_text": "You cinch it in deep—nowhere to go!",
    },

    # --- Top rope offense ---
    "Moonsault": {
        "damage": 16,
        "cost": 7,
        "type": "Aerial",
        "req_user_state": "TOP_ROPE",
        "req_target_state": "GROUNDED",
        "flavor_text": "MOONSAULT! Picture-perfect rotation!",
        "set_user_state": "STANDING",
    },
    "Diving Elbow": {
        "damage": 13,
        "cost": 6,
        "type": "Aerial",
        "req_user_state": "TOP_ROPE",
        "req_target_state": "GROUNDED",
        "flavor_text": "You soar through the air—DIVING ELBOW!",
        "set_user_state": "STANDING",
    },
}
