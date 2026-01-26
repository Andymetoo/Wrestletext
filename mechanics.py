from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _apply_embedded_theme(container: tk.Misc) -> dict[str, str]:
    """Apply a high-contrast theme for embedded widgets.

    On some Tk builds (notably Android/Pydroid3), default fg/bg can make
    text/buttons effectively invisible on dark hosts.
    """
    bg = "#0b0b0b"
    fg = "#f2f2f2"
    subfg = "#b0b0b0"
    try:
        container.configure(bg=bg)
    except tk.TclError:
        pass
    try:
        style = ttk.Style(container)
        style.configure("Embed.TButton", padding=8)
        style.configure("Embed.TFrame", background=bg)
        style.configure("Embed.TLabel", background=bg, foreground=fg)
    except tk.TclError:
        pass
    return {"bg": bg, "fg": fg, "subfg": subfg}


def _embedded_content_width(container: tk.Misc, *, default: int = 320) -> int:
    """Return a conservative content width for embedded UIs.

    Some mobile wrappers only show the left part of a large Tk window.
    Clamping to a phone-ish width keeps centered UIs from rendering off-screen.
    """
    try:
        container.update_idletasks()
        w = int(container.winfo_width())
    except tk.TclError:
        return default
    if w <= 1:
        return default
    # Subtract a bit for padding/scrollbars.
    # Do not hard-clamp to a phone-ish width here; the host container (Moves panel)
    # is already sized by the app/window, and clamping makes embedded UIs feel squished.
    return max(240, w - 24)


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
    host: tk.Misc | None = None,
) -> bool:
    """Shrinking-window timing check.

    Window size scales with victim HP: lower HP => easier (larger window).
    Returns True if player stops the marker inside the window.
    """
    victim_hp_pct = _clamp(victim_hp_pct, 0.0, 1.0)

    if host is None:
        top = tk.Toplevel(parent)
        top.title(title)
        top.transient(parent)
        top.grab_set()
        top.resizable(False, False)
        container: tk.Misc = top
    else:
        container = host
        for w in list(container.winfo_children()):
            w.destroy()
        colors = _apply_embedded_theme(container)

    if host is None:
        colors = {"bg": None, "fg": None, "subfg": "#555"}

    embedded = host is not None
    content_w = _embedded_content_width(container) if embedded else 320

    tk.Label(
        container,
        text=prompt,
        font=("Arial", 11, "bold"),
        bg=colors["bg"],
        fg=colors["fg"],
        justify=("left" if embedded else "center"),
        anchor=("w" if embedded else "center"),
        wraplength=(content_w if embedded else 0),
    ).pack(padx=12, pady=(12, 6), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))
    tk.Label(
        container,
        text="Stop the moving marker inside the green window.",
        font=("Arial", 9),
        bg=colors["bg"],
        fg=colors["subfg"],
        justify=("left" if embedded else "center"),
        anchor=("w" if embedded else "center"),
        wraplength=(content_w if embedded else 0),
    ).pack(padx=12, pady=(0, 10), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    width = content_w
    height = 50
    canvas = tk.Canvas(container, width=width, height=height, bg="#111", highlightthickness=0)
    canvas.pack(padx=12, pady=(0, 10), anchor="w")

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
    done_var = tk.BooleanVar(value=False)
    start = {"t": None}
    speed_px = 7

    def stop() -> None:
        if result["done"]:
            return
        coords = canvas.coords(marker)
        marker_center = (coords[0] + coords[2]) / 2.0
        result["success"] = window_x0 <= marker_center <= window_x1
        result["done"] = True
        if host is None:
            top.destroy()
        done_var.set(True)

    def tick(now_ms: int = 0) -> None:
        if result["done"]:
            return
        if start["t"] is None:
            start["t"] = now_ms
        elapsed = now_ms - start["t"]
        if elapsed >= duration_ms:
            result["done"] = True
            result["success"] = False
            if host is None:
                top.destroy()
            done_var.set(True)
            return

        coords = canvas.coords(marker)
        x0, y0, x1, y1 = coords
        x0 += speed_px
        x1 += speed_px
        if x1 >= width:
            x0 = 0
            x1 = 8
        canvas.coords(marker, x0, y0, x1, y1)
        parent.after(16, lambda: tick(elapsed + 16))

    btn = ttk.Button(container, text="STOP!", command=stop, style=("Embed.TButton" if host is not None else "TButton"))
    btn.pack(padx=12, pady=(0, 12), fill="x")
    if host is None:
        top.bind("<space>", lambda _e: stop())

    if host is None:
        _position_modal_bottom(parent, top, bottom_padding=28)

    tick(0)
    if host is None:
        top.wait_window()
    else:
        parent.wait_variable(done_var)
    return bool(result["success"])


def submission_minigame(
    parent: tk.Misc,
    *,
    title: str,
    prompt: str,
    victim_hp_pct: float,
    timeout_ms: int = 12000,
    host: tk.Misc | None = None,
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

    if host is None:
        top = tk.Toplevel(parent)
        top.title(title)
        top.transient(parent)
        top.grab_set()
        top.resizable(False, False)
        container: tk.Misc = top
    else:
        container = host
        for w in list(container.winfo_children()):
            w.destroy()
        colors = _apply_embedded_theme(container)

    if host is None:
        colors = {"bg": None, "fg": None, "subfg": "#555"}

    embedded = host is not None
    content_w = _embedded_content_width(container) if embedded else 320

    tk.Label(
        container,
        text=prompt,
        font=("Arial", 11, "bold"),
        bg=colors["bg"],
        fg=colors["fg"],
        justify=("left" if embedded else "center"),
        anchor=("w" if embedded else "center"),
        wraplength=(content_w if embedded else 0),
    ).pack(padx=12, pady=(12, 6), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    status = tk.Label(
        container,
        text=f"Streak: {streak}/{required}",
        font=("Arial", 9),
        bg=colors["bg"],
        fg=colors["subfg"],
    )
    status.pack(padx=12, pady=(0, 8), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    current_lbl = tk.Label(container, text=f"CURRENT: {current}", font=("Arial", 18, "bold"), bg=colors["bg"], fg=colors["fg"])
    current_lbl.pack(padx=12, pady=(0, 10), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    hint = tk.Label(container, text="Will the NEXT number be higher or lower?", font=("Arial", 9), bg=colors["bg"], fg=colors["fg"])
    hint.pack(padx=12, pady=(0, 10), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    result = {"done": False, "success": False}
    done_var = tk.BooleanVar(value=False)

    def timeout() -> None:
        if result["done"]:
            return
        result["done"] = True
        result["success"] = False
        if host is None:
            top.destroy()
        done_var.set(True)

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

        hint.config(text=f"NEXT: {nxt} (was {current})", fg=(colors["subfg"] if embedded else "#333"))
        current = nxt
        current_lbl.config(text=f"CURRENT: {current}")

        if ok:
            streak += 1
            status.config(text=f"Streak: {streak}/{required}")
            if streak >= required:
                result["done"] = True
                result["success"] = True
                if host is None:
                    top.destroy()
                done_var.set(True)
        else:
            result["done"] = True
            result["success"] = False
            if host is None:
                top.destroy()
            done_var.set(True)

    # Auto-resolve to avoid indefinite waits on mobile.
    parent.after(timeout_ms, timeout)

    btns = tk.Frame(container, bg=colors["bg"])
    btns.pack(padx=12, pady=(0, 12), fill="x")

    b1 = ttk.Button(btns, text="LOWER", command=lambda: choose("LOWER"), style=("Embed.TButton" if host is not None else "TButton"))
    b1.pack(fill="x", pady=4)
    b2 = ttk.Button(btns, text="HIGHER", command=lambda: choose("HIGHER"), style=("Embed.TButton" if host is not None else "TButton"))
    b2.pack(fill="x", pady=4)

    if host is None:
        _position_modal_bottom(parent, top, bottom_padding=28)

    if host is None:
        top.wait_window()
    else:
        parent.wait_variable(done_var)
    return bool(result["success"])


def lockup_minigame(
    parent: tk.Misc,
    *,
    title: str,
    prompt: str,
    timeout_ms: int = 12000,
    host: tk.Misc | None = None,
) -> bool:
    """Push-your-luck lock-up (PUSH/HOLD).

    Returns True if the human player wins the struggle.
    Bust rule: if you push past 15, you lose.
    HOLD ends your pushing and lets CPU respond.
    """
    if host is None:
        top = tk.Toplevel(parent)
        top.title(title)
        top.transient(parent)
        top.grab_set()
        top.resizable(False, False)
        container: tk.Misc = top
    else:
        container = host
        for w in list(container.winfo_children()):
            w.destroy()
        colors = _apply_embedded_theme(container)

    if host is None:
        colors = {"bg": None, "fg": None, "subfg": "#555"}

    embedded = host is not None
    content_w = _embedded_content_width(container) if embedded else 320

    tk.Label(
        container,
        text=prompt,
        font=("Arial", 11, "bold"),
        bg=colors["bg"],
        fg=colors["fg"],
        justify=("left" if embedded else "center"),
        anchor=("w" if embedded else "center"),
        wraplength=(content_w if embedded else 0),
    ).pack(padx=12, pady=(12, 6), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))
    tk.Label(
        container,
        text="Get closer to 15 without going over.",
        font=("Arial", 9),
        bg=colors["bg"],
        fg=colors["subfg"],
        justify=("left" if embedded else "center"),
        anchor=("w" if embedded else "center"),
        wraplength=(content_w if embedded else 0),
    ).pack(padx=12, pady=(0, 10), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    scores = {"p": 0, "c": 0}
    result = {"done": False, "success": False}
    done_var = tk.BooleanVar(value=False)

    status = tk.Label(container, text="YOU: 0   |   CPU: 0", font=("Arial", 12, "bold"), bg=colors["bg"], fg=colors["fg"])
    status.pack(padx=12, pady=(0, 10), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    log = tk.Label(container, text="", font=("Arial", 9), bg=colors["bg"], fg=colors["subfg"])
    log.pack(padx=12, pady=(0, 10), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

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
        if host is None:
            top.after(450, top.destroy)
        done_var.set(True)

    def timeout() -> None:
        if result["done"]:
            return
        finish(False, "Time's up—position lost!")

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

    btns = tk.Frame(container, bg=colors["bg"])
    btns.pack(padx=12, pady=(0, 12), fill="x")
    ttk.Button(btns, text="PUSH", command=push, style=("Embed.TButton" if host is not None else "TButton")).pack(fill="x", pady=4)
    ttk.Button(btns, text="HOLD", command=hold, style=("Embed.TButton" if host is not None else "TButton")).pack(fill="x", pady=4)

    refresh()
    parent.after(timeout_ms, timeout)
    if host is None:
        _position_modal_bottom(parent, top, bottom_padding=28)
        top.wait_window()
    else:
        parent.wait_variable(done_var)
    return bool(result["success"])


def grapple_qte_minigame(
    parent: tk.Misc,
    *,
    title: str,
    prompt: str,
    duration_ms: int = 3800,
    host: tk.Misc | None = None,
) -> dict:
    """Grapple QTE timing bar.

    Timing tiers (by percent):
    - BOTCH: >95
    - CRIT: 70-95
    - HIT: 40-69
    - WEAK: <40

    Returns dict: {"tier": str, "timing": int, "multiplier": float}
    """
    if host is None:
        top = tk.Toplevel(parent)
        top.title(title)
        top.transient(parent)
        top.grab_set()
        top.resizable(False, False)
        container: tk.Misc = top
    else:
        container = host
        for w in list(container.winfo_children()):
            w.destroy()
        colors = _apply_embedded_theme(container)

    if host is None:
        colors = {"bg": None, "fg": None, "subfg": "#555"}

    embedded = host is not None
    content_w = _embedded_content_width(container) if embedded else 320

    tk.Label(
        container,
        text=prompt,
        font=("Arial", 11, "bold"),
        bg=colors["bg"],
        fg=colors["fg"],
        justify=("left" if embedded else "center"),
        anchor=("w" if embedded else "center"),
        wraplength=(content_w if embedded else 0),
    ).pack(padx=12, pady=(12, 6), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))
    tk.Label(
        container,
        text="Stop in the green zone (70–95). Over 95 is a botch.",
        font=("Arial", 9),
        bg=colors["bg"],
        fg=colors["subfg"],
        justify=("left" if embedded else "center"),
        anchor=("w" if embedded else "center"),
        wraplength=(content_w if embedded else 0),
    ).pack(padx=12, pady=(0, 10), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    width = content_w
    height = 56
    canvas = tk.Canvas(container, width=width, height=height, bg="#111", highlightthickness=0)
    canvas.pack(padx=12, pady=(0, 10), anchor="w")

    def pct_to_x(p: float) -> int:
        return int(_clamp(p, 0.0, 100.0) / 100.0 * (width - 1))

    # Draw tier regions.
    canvas.create_rectangle(pct_to_x(70), 14, pct_to_x(95), height - 14, fill="#2aa84a", outline="")
    canvas.create_rectangle(pct_to_x(96), 14, pct_to_x(100), height - 14, fill="#a82a2a", outline="")

    marker = canvas.create_rectangle(0, 10, 8, height - 10, fill="#f2f2f2", outline="")

    result = {"done": False, "timing": 0}
    done_var = tk.BooleanVar(value=False)
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
        if host is None:
            top.destroy()
        done_var.set(True)

    def tick(now_ms: int = 0) -> None:
        if result["done"]:
            return
        if start["t"] is None:
            start["t"] = now_ms
        elapsed = now_ms - start["t"]
        if elapsed >= duration_ms:
            result["done"] = True
            result["timing"] = 0
            if host is None:
                top.destroy()
            done_var.set(True)
            return

        x0, y0, x1, y1 = canvas.coords(marker)
        x0 += speed_px
        x1 += speed_px
        if x1 >= width:
            x0 = 0
            x1 = 8
        canvas.coords(marker, x0, y0, x1, y1)
        parent.after(16, lambda: tick(elapsed + 16))

    btn = ttk.Button(container, text="EXECUTE!", command=stop, style=("Embed.TButton" if host is not None else "TButton"))
    btn.pack(padx=12, pady=(0, 12), fill="x")
    if host is None:
        top.bind("<space>", lambda _e: stop())

    tick(0)
    if host is None:
        _position_modal_bottom(parent, top, bottom_padding=28)
        top.wait_window()
    else:
        parent.wait_variable(done_var)

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


def chain_wrestling_game(
    parent: tk.Misc,
    *,
    title: str,
    prompt: str,
    host: tk.Misc | None = None,
) -> dict:
    """Blind RPS between POWER, SPEED, TECHNICAL.

    Rules:
    - POWER beats SPEED
    - SPEED beats TECHNICAL
    - TECHNICAL beats POWER

    Returns dict: {"result": "WIN"|"TIE"|"LOSS", "player": str, "cpu": str}
    """
    choices = ["POWER", "SPEED", "TECHNICAL"]
    beats = {
        "POWER": "SPEED",
        "SPEED": "TECHNICAL",
        "TECHNICAL": "POWER",
    }

    if host is None:
        top = tk.Toplevel(parent)
        top.title(title)
        top.transient(parent)
        top.grab_set()
        top.resizable(False, False)
        container: tk.Misc = top
    else:
        container = host
        for w in list(container.winfo_children()):
            w.destroy()
        colors = _apply_embedded_theme(container)

    if host is None:
        colors = {"bg": None, "fg": None, "subfg": "#555"}

    embedded = host is not None
    content_w = _embedded_content_width(container) if embedded else 320

    tk.Label(
        container,
        text=prompt,
        font=("Arial", 11, "bold"),
        bg=colors["bg"],
        fg=colors["fg"],
        justify=("left" if embedded else "center"),
        anchor=("w" if embedded else "center"),
        wraplength=(content_w if embedded else 0),
    ).pack(padx=12, pady=(12, 6), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))
    tk.Label(
        container,
        text="Choose blindly. No hints.",
        font=("Arial", 9),
        bg=colors["bg"],
        fg=colors["subfg"],
        justify=("left" if embedded else "center"),
        anchor=("w" if embedded else "center"),
        wraplength=(content_w if embedded else 0),
    ).pack(padx=12, pady=(0, 10), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    result = {"done": False, "player": "", "cpu": "", "result": "TIE"}
    done_var = tk.BooleanVar(value=False)

    def timeout() -> None:
        if result["done"]:
            return
        # Auto-pick for player to keep match moving.
        pick(random.choice(choices))

    status = tk.Label(container, text="", font=("Arial", 10, "bold"), bg=colors["bg"], fg=colors["fg"])
    status.pack(padx=12, pady=(0, 10), fill=("x" if embedded else "none"), anchor=("w" if embedded else "center"))

    def finish(msg: str) -> None:
        status.config(text=msg)
        if host is None:
            top.after(550, top.destroy)
        done_var.set(True)

    def pick(player_choice: str) -> None:
        if result["done"]:
            return
        cpu_choice = random.choice(choices)
        result["player"] = player_choice
        result["cpu"] = cpu_choice
        if cpu_choice == player_choice:
            result["result"] = "TIE"
            result["done"] = True
            finish(f"Tie! You both chose {player_choice}.")
            return
        if beats[player_choice] == cpu_choice:
            result["result"] = "WIN"
            result["done"] = True
            finish(f"Win! {player_choice} beats {cpu_choice}.")
            return
        result["result"] = "LOSS"
        result["done"] = True
        finish(f"Loss! {cpu_choice} beats {player_choice}.")

    btns = tk.Frame(container, bg=colors["bg"])
    btns.pack(padx=12, pady=(0, 12), fill="x")
    for c in choices:
        ttk.Button(btns, text=c, command=lambda cc=c: pick(cc), style=("Embed.TButton" if host is not None else "TButton")).pack(
            fill="x", pady=4
        )

    parent.after(12000, timeout)

    if host is None:
        _position_modal_bottom(parent, top, bottom_padding=28)
        top.wait_window()
    else:
        parent.wait_variable(done_var)

    return {"result": result["result"], "player": result["player"], "cpu": result["cpu"]}
