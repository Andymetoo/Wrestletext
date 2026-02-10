"""Roster and AI profile data.

This is intentionally separated from the UI/game engine so the roster can grow
without bloating Main_kivy.py.
"""

from __future__ import annotations

# NOTE: Profiles are lightweight dictionaries consumed by Wrestler(profile=...).
# They can be expanded over time (archetype, moveset, stats, cosmetics, etc.).

ROSTER: dict[str, dict] = {
    # NOTE: Roster keys are slugs (stable IDs). Displayed names live in profile fields.
    "mr_user": {
        "name": "Mr. User",
        "short_name": "User",
        "archetype": "BALANCED",
        "weight_class": "Heavy",
        "style": "Balanced",
        "finisher": "grap_superplex",
        "ai_traits": {"GREED": 60, "GOOD": 20, "BAD": 10, "RND": 10},
        "bio": "A solid all-rounder. No excuses—just results.",
    },
    "johnny_cpu": {
        "name": "Johnny CPU",
        "short_name": "CPU",
        "archetype": "BALANCED",
        "weight_class": "Heavy",
        "style": "Brawler",
        "finisher": "grap_powerbomb",
        "ai_traits": {"GREED": 60, "GOOD": 20, "BAD": 10, "RND": 10},
        "bio": "A no-nonsense bruiser built to punish mistakes.",
    },
    "technical_tim": {
        "name": "Technical Tim",
        "short_name": "Tim",
        "archetype": "BALANCED",
        "weight_class": "Cruiser",
        "style": "Technician",
        "finisher": "sub_submission_hold",
        "ai_traits": {"GREED": 10, "GOOD": 70, "BAD": 10, "RND": 10},
        "bio": "Fast hands, faster brain. Will take an inch and turn it into a hold.",
    },

    # New selectable wrestlers
    "brad_vantage": {
        "name": "Brad Vantage",
        "short_name": "Brad",
        "archetype": "BALANCED",
        "weight_class": "Heavy",
        "style": "Striker",
        "finisher": "strike_haymaker",
        "ai_traits": {"GREED": 45, "GOOD": 35, "BAD": 10, "RND": 10},
        "bio": "A crisp striker with a mean right hand. Loves to keep it simple and sharp.",
    },
    "floyd_conflict_jr": {
        "name": "Floyd Conflict Jr.",
        "short_name": "Floyd",
        "archetype": "BALANCED",
        "weight_class": "Heavy",
        "style": "Grappler",
        "finisher": "grap_belly_to_belly",
        "ai_traits": {"GREED": 55, "GOOD": 25, "BAD": 10, "RND": 10},
        "bio": "Second-generation scrapper who thrives in tight quarters and ugly grapples.",
    },
    "super_delicious_brent": {
        "name": "Super-Delicious Brent",
        "short_name": "Brent",
        "archetype": "SUPERSTAR",
        "weight_class": "Cruiser",
        "style": "Showman",
        "finisher": "air_frog_splash",
        "ai_traits": {"GREED": 35, "GOOD": 45, "BAD": 10, "RND": 10},
        "bio": "All flash, all gas. The crowd loves him—and he knows it.",
    },
    "neon_casarrubias": {
        "name": "Neon Casarrubias",
        "short_name": "Neon",
        "archetype": "BALANCED",
        "weight_class": "Cruiser",
        "style": "Technician",
        "finisher": "sub_ankle_lock",
        "ai_traits": {"GREED": 20, "GOOD": 60, "BAD": 10, "RND": 10},
        "bio": "A slick tactician with a nasty streak for limbs. Precision over power.",
    },
    "malice_anderson": {
        "name": "\"Malice\" Anderson",
        "short_name": "Malice",
        "archetype": "BALANCED",
        "weight_class": "Heavy",
        "style": "Brawler",
        "finisher": "strike_spinning_backfist",
        "ai_traits": {"GREED": 65, "GOOD": 15, "BAD": 10, "RND": 10},
        "bio": "A streetfight specialist who turns exchanges into disasters—especially for you.",
    },
    "fatal_mcguire": {
        "name": "Fatal McGuire",
        "short_name": "Fatal",
        "archetype": "SUPERSTAR",
        "weight_class": "Super Heavy",
        "style": "Giant",
        "finisher": "grap_powerbomb",
        "ai_traits": {"GREED": 70, "GOOD": 15, "BAD": 10, "RND": 5},
        "bio": "A crushing super heavyweight. If you're fresh, you're probably not lifting him.",
    },
}

DEFAULT_PLAYER_PROFILE = "mr_user"
DEFAULT_CPU_PROFILE = "johnny_cpu"
