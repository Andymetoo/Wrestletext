from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path
from pprint import pformat
import sys


def _snake(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "move"


PREFIX_BY_TYPE = {
    "Strike": "strike",
    "Grapple": "grap",
    "Aerial": "air",
    "Submission": "sub",
    "Pin": "pin",
    "Setup": "util",
    "Defensive": "def",
}

# Explicit overrides for readability / future stability.
# (Keyed by display name.)
PREFIX_OVERRIDE = {
    "Lock Up": "grap",
    "Fight For Control": "grap",
    "Shove Off": "grap",
    "Climb Turnbuckle": "air",
    "Climb Down": "air",
}


def build_slug_map(moves: dict[str, dict]) -> dict[str, str]:
    used: set[str] = set()
    mapping: dict[str, str] = {}

    for name, mv in moves.items():
        mtype = str(mv.get("type", "Setup"))
        prefix = PREFIX_OVERRIDE.get(name) or PREFIX_BY_TYPE.get(mtype, "util")
        base = _snake(name)
        slug = f"{prefix}_{base}"
        if slug in used:
            n = 2
            while f"{slug}_{n}" in used:
                n += 1
            slug = f"{slug}_{n}"
        used.add(slug)
        mapping[name] = slug

    return mapping


def rewrite_moves_db() -> None:
    # Ensure project root is importable when running from tools/.
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    import moves_db  # type: ignore

    old_moves: dict[str, dict] = dict(moves_db.MOVES)
    mapping = build_slug_map(old_moves)

    new_moves: "OrderedDict[str, dict]" = OrderedDict()

    for old_name, mv in old_moves.items():
        slug = mapping[old_name]
        new_mv = OrderedDict()
        new_mv["name"] = old_name
        for k, v in mv.items():
            if k == "chain_next" and isinstance(v, str) and v in mapping:
                new_mv[k] = mapping[v]
            else:
                new_mv[k] = v
        new_moves[slug] = new_mv

    header = (
        '"""Move registry for the state-based tactical wrestling simulation.\n\n'
        'Refactored for AKI-style Hierarchy:\n'
        'STANDING -> GRAPPLE_WEAK -> GRAPPLE_STRONG -> GRAPPLE_BACK\n\n'
        'NOTE: Keys are stable slugs (IDs). Use move["name"] for display.\n'
        '"""\n'
        'from __future__ import annotations\n\n'
        'from typing import Any, Dict\n\n'
        'Move = Dict[str, Any]\n\n'
        'MOVES: Dict[str, Move] = '
    )

    body = pformat(dict(new_moves), width=120, sort_dicts=False)
    content = header + body + "\n"

    root.joinpath("moves_db.py").write_text(content, encoding="utf-8")
    root.joinpath("slug_map.json").write_text(
        json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    rewrite_moves_db()
    print("Wrote moves_db.py and slug_map.json")
