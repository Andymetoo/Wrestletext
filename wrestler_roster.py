"""Roster and AI profile data.

This is intentionally separated from the UI/game engine so the roster can grow
without bloating Main_kivy.py.
"""

from __future__ import annotations

# NOTE: Profiles are lightweight dictionaries consumed by Wrestler(profile=...).
# They can be expanded over time (archetype, moveset, stats, cosmetics, etc.).

ROSTER: dict[str, dict] = {
    "Mr. User": {
        "name": "Mr. User",
        "finisher": "grap_superplex",
        "ai_traits": {},  # User controlled
    },
    "Johnny CPU": {
        "name": "Johnny CPU",
        "finisher": "grap_powerbomb",
        "ai_traits": {"GREED": 60, "GOOD": 20, "BAD": 10, "RND": 10},
    },
    "Technical Tim": {
        "name": "Technical Tim",
        "finisher": "sub_submission_hold",
        "ai_traits": {"GREED": 10, "GOOD": 70, "BAD": 10, "RND": 10},
    },
}

DEFAULT_PLAYER_PROFILE = "Mr. User"
DEFAULT_CPU_PROFILE = "Johnny CPU"
