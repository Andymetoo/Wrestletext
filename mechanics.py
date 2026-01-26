from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _position_modal_bottom(parent: tk.Misc, top: tk.Toplevel, *, bottom_padding: int = 20) -> None:
    """Position a modal near the bottom-center of the parent window."""
    try:
        parent.update_idletasks()
        top.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        tw = top.winfo_width()
        th = top.winfo_height()
        x = px + max(0, (pw - tw) // 2)
        y = py + max(0, ph - th - bottom_padding)
        top.geometry(f"+{x}+{y}")
    except tk.TclError:
        # Safe fallback: let the window manager decide.
        return


def pin_minigame(
    parent: tk.Misc,
    *,
    title: str,
    prompt: str,
    victim_hp_pct: float,
    duration_ms: int = 4500,
) -> bool:
    """Shrinking-window timing check.

    Window size scales with victim HP: lower HP => easier (larger window).
    Returns True if player stops the marker inside the window.
    """
    victim_hp_pct = _clamp(victim_hp_pct, 0.0, 1.0)

    top = tk.Toplevel(parent)
    top.title(title)
    top.transient(parent)
    top.grab_set()
    top.resizable(False, False)

    tk.Label(top, text=prompt, font=("Arial", 11, "bold")).pack(padx=12, pady=(12, 6))
    tk.Label(
        top,
        text="Stop the moving marker inside the green window.",
        font=("Arial", 9),
        fg="#555",
    ).pack(padx=12, pady=(0, 10))

    width = 320
    height = 50
    canvas = tk.Canvas(top, width=width, height=height, bg="#111", highlightthickness=0)
    canvas.pack(padx=12, pady=(0, 10))

    # Lower HP => bigger success window.
    min_window = 22
    max_window = 120
    window_w = int(min_window + (max_window - min_window) * (1.0 - victim_hp_pct))
    window_w = max(min_window, min(max_window, window_w))
    window_x0 = (width - window_w) // 2
    window_x1 = window_x0 + window_w
    canvas.create_rectangle(window_x0, 12, window_x1, height - 12, fill="#2aa84a", outline="")

    marker = canvas.create_rectangle(0, 8, 8, height - 8, fill="#f2f2f2", outline="")

    result = {"done": False, "success": False}
    start = {"t": None}
    speed_px = 7

    def stop() -> None:
        if result["done"]:
            return
        coords = canvas.coords(marker)
        marker_center = (coords[0] + coords[2]) / 2.0
        result["success"] = window_x0 <= marker_center <= window_x1
        result["done"] = True
        top.destroy()

    def tick(now_ms: int = 0) -> None:
        if result["done"]:
            return
        if start["t"] is None:
            start["t"] = now_ms
        elapsed = now_ms - start["t"]
        if elapsed >= duration_ms:
            result["done"] = True
            result["success"] = False
            top.destroy()
            return

        coords = canvas.coords(marker)
        x0, y0, x1, y1 = coords
        x0 += speed_px
        x1 += speed_px
        if x1 >= width:
            x0 = 0
            x1 = 8
        canvas.coords(marker, x0, y0, x1, y1)
        top.after(16, lambda: tick(elapsed + 16))

    btn = ttk.Button(top, text="STOP!", command=stop)
    btn.pack(padx=12, pady=(0, 12), fill="x")
    top.bind("<space>", lambda _e: stop())

    _position_modal_bottom(parent, top, bottom_padding=28)

    tick(0)
    top.wait_window()
    return bool(result["success"])


def submission_minigame(
    parent: tk.Misc,
    *,
    title: str,
    prompt: str,
    victim_hp_pct: float,
) -> bool:
    """Higher/Lower sequence guessing game (classic over/under).

    You must correctly predict whether the next number will be HIGHER or LOWER.
    Lower victim HP => fewer required correct guesses (easier finish).
    """
    victim_hp_pct = _clamp(victim_hp_pct, 0.0, 1.0)

    # Lower HP => easier: require fewer consecutive correct calls.
    required = 4
    if victim_hp_pct < 0.25:
        required = 2
    elif victim_hp_pct < 0.75:
        required = 3

    current = random.randint(2, 9)
    banned = [current]
    streak = 0

    top = tk.Toplevel(parent)
    top.title(title)
    top.transient(parent)
    top.grab_set()
    top.resizable(False, False)

    tk.Label(top, text=prompt, font=("Arial", 11, "bold")).pack(padx=12, pady=(12, 6))

    status = tk.Label(top, text=f"Streak: {streak}/{required}", font=("Arial", 9), fg="#555")
    status.pack(padx=12, pady=(0, 8))

    current_lbl = tk.Label(top, text=f"CURRENT: {current}", font=("Arial", 18, "bold"))
    current_lbl.pack(padx=12, pady=(0, 10))

    hint = tk.Label(top, text="Will the NEXT number be higher or lower?", font=("Arial", 9))
    hint.pack(padx=12, pady=(0, 10))

    result = {"done": False, "success": False}

    def next_val() -> int:
        nonlocal banned
        v = random.randint(1, 10)
        while v in banned:
            v = random.randint(1, 10)
        banned.append(v)
        if len(banned) > 3:
            banned.pop(0)
        return v

    def choose(direction: str) -> None:
        nonlocal current, streak
        if result["done"]:
            return
        nxt = next_val()
        ok = (direction == "HIGHER" and nxt > current) or (direction == "LOWER" and nxt < current)

        hint.config(text=f"NEXT: {nxt} (was {current})", fg="#333")
        current = nxt
        current_lbl.config(text=f"CURRENT: {current}")

        if ok:
            streak += 1
            status.config(text=f"Streak: {streak}/{required}")
            if streak >= required:
                result["done"] = True
                result["success"] = True
                top.destroy()
        else:
            result["done"] = True
            result["success"] = False
            top.destroy()

    btns = tk.Frame(top)
    btns.pack(padx=12, pady=(0, 12), fill="x")

    b1 = ttk.Button(btns, text="LOWER", command=lambda: choose("LOWER"))
    b1.pack(fill="x", pady=4)
    b2 = ttk.Button(btns, text="HIGHER", command=lambda: choose("HIGHER"))
    b2.pack(fill="x", pady=4)

    _position_modal_bottom(parent, top, bottom_padding=28)

    top.wait_window()
    return bool(result["success"])


def lockup_minigame(
    parent: tk.Misc,
    *,
    title: str,
    prompt: str,
) -> bool:
    """Push-your-luck lock-up (PUSH/HOLD).

    Returns True if the human player wins the struggle.
    Bust rule: if you push past 15, you lose.
    HOLD ends your pushing and lets CPU respond.
    """
    top = tk.Toplevel(parent)
    top.title(title)
    top.transient(parent)
    top.grab_set()
    top.resizable(False, False)

    tk.Label(top, text=prompt, font=("Arial", 11, "bold")).pack(padx=12, pady=(12, 6))
    tk.Label(top, text="Get closer to 15 without going over.", font=("Arial", 9), fg="#555").pack(
        padx=12, pady=(0, 10)
    )

    scores = {"p": 0, "c": 0}
    result = {"done": False, "success": False}

    status = tk.Label(top, text="YOU: 0   |   CPU: 0", font=("Arial", 12, "bold"))
    status.pack(padx=12, pady=(0, 10))

    log = tk.Label(top, text="", font=("Arial", 9), fg="#333")
    log.pack(padx=12, pady=(0, 10))

    def refresh() -> None:
        status.config(text=f"YOU: {scores['p']}   |   CPU: {scores['c']}")

    def cpu_push_once() -> None:
        scores["c"] += random.randint(1, 6)
        refresh()

    def finish(player_won: bool, msg: str) -> None:
        if result["done"]:
            return
        result["done"] = True
        result["success"] = player_won
        log.config(text=msg)
        top.after(450, top.destroy)

    def push() -> None:
        if result["done"]:
            return
        scores["p"] += random.randint(1, 6)
        refresh()
        if scores["p"] > 15:
            finish(False, "You over-committed and slipped!")

    def hold() -> None:
        if result["done"]:
            return
        log.config(text=f"You hold at {scores['p']}... CPU responds.")

        # CPU pushes until it reaches 12+ or busts.
        while scores["c"] < 12:
            cpu_push_once()
            if scores["c"] > 15:
                finish(True, "CPU over-committed! You win the tie-up!")
                return

        if scores["p"] >= scores["c"]:
            finish(True, "You win position!")
        else:
            finish(False, "CPU muscles you around and takes control!")

    btns = tk.Frame(top)
    btns.pack(padx=12, pady=(0, 12), fill="x")
    ttk.Button(btns, text="PUSH", command=push).pack(fill="x", pady=4)
    ttk.Button(btns, text="HOLD", command=hold).pack(fill="x", pady=4)

    _position_modal_bottom(parent, top, bottom_padding=28)

    refresh()
    top.wait_window()
    return bool(result["success"])


def grapple_qte_minigame(
    parent: tk.Misc,
    *,
    title: str,
    prompt: str,
    duration_ms: int = 3800,
) -> dict:
    """Grapple QTE timing bar.

    Timing tiers (by percent):
    - BOTCH: >95
    - CRIT: 70-95
    - HIT: 40-69
    - WEAK: <40

    Returns dict: {"tier": str, "timing": int, "multiplier": float}
    """
    top = tk.Toplevel(parent)
    top.title(title)
    top.transient(parent)
    top.grab_set()
    top.resizable(False, False)

    tk.Label(top, text=prompt, font=("Arial", 11, "bold")).pack(padx=12, pady=(12, 6))
    tk.Label(
        top,
        text="Stop in the green zone (70–95). Over 95 is a botch.",
        font=("Arial", 9),
        fg="#555",
    ).pack(padx=12, pady=(0, 10))

    width = 320
    height = 56
    canvas = tk.Canvas(top, width=width, height=height, bg="#111", highlightthickness=0)
    canvas.pack(padx=12, pady=(0, 10))

    def pct_to_x(p: float) -> int:
        return int(_clamp(p, 0.0, 100.0) / 100.0 * (width - 1))

    # Draw tier regions.
    canvas.create_rectangle(pct_to_x(70), 14, pct_to_x(95), height - 14, fill="#2aa84a", outline="")
    canvas.create_rectangle(pct_to_x(96), 14, pct_to_x(100), height - 14, fill="#a82a2a", outline="")

    marker = canvas.create_rectangle(0, 10, 8, height - 10, fill="#f2f2f2", outline="")

    result = {"done": False, "timing": 0}
    start = {"t": None}
    speed_px = 9

    def stop() -> None:
        if result["done"]:
            return
        coords = canvas.coords(marker)
        marker_center = (coords[0] + coords[2]) / 2.0
        timing = int(round(_clamp(marker_center / (width - 1) * 100.0, 0.0, 100.0)))
        result["timing"] = timing
        result["done"] = True
        top.destroy()

    def tick(now_ms: int = 0) -> None:
        if result["done"]:
            return
        if start["t"] is None:
            start["t"] = now_ms
        elapsed = now_ms - start["t"]
        if elapsed >= duration_ms:
            result["done"] = True
            result["timing"] = 0
            top.destroy()
            return

        x0, y0, x1, y1 = canvas.coords(marker)
        x0 += speed_px
        x1 += speed_px
        if x1 >= width:
            x0 = 0
            x1 = 8
        canvas.coords(marker, x0, y0, x1, y1)
        top.after(16, lambda: tick(elapsed + 16))

    btn = ttk.Button(top, text="EXECUTE!", command=stop)
    btn.pack(padx=12, pady=(0, 12), fill="x")
    top.bind("<space>", lambda _e: stop())

    _position_modal_bottom(parent, top, bottom_padding=28)

    tick(0)
    top.wait_window()

    timing = int(result["timing"])
    if timing > 95:
        tier = "BOTCH"
        mult = 0.0
    elif timing >= 70:
        tier = "CRIT"
        mult = 1.5
    elif timing >= 40:
        tier = "HIT"
        mult = 1.0
    else:
        tier = "WEAK"
        mult = 0.5

    return {"tier": tier, "timing": timing, "multiplier": mult}
