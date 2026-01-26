from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


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
    """Higher/Lower number guessing game.

    Returns True if player wins within limited attempts.
    Lower victim HP => more attempts for the aggressor / easier finish.
    """
    victim_hp_pct = _clamp(victim_hp_pct, 0.0, 1.0)
    secret = random.randint(1, 20)
    attempts = 3 + int((1.0 - victim_hp_pct) * 3)  # 3..6
    attempts = max(3, min(6, attempts))

    top = tk.Toplevel(parent)
    top.title(title)
    top.transient(parent)
    top.grab_set()
    top.resizable(False, False)

    tk.Label(top, text=prompt, font=("Arial", 11, "bold")).pack(padx=12, pady=(12, 6))
    status = tk.Label(top, text=f"Attempts left: {attempts}", font=("Arial", 9), fg="#555")
    status.pack(padx=12, pady=(0, 10))

    entry = ttk.Entry(top)
    entry.pack(padx=12, pady=(0, 8), fill="x")
    entry.focus_set()

    hint = tk.Label(top, text="Guess a number 1–20.", font=("Arial", 9))
    hint.pack(padx=12, pady=(0, 10))

    result = {"done": False, "success": False}

    def submit() -> None:
        nonlocal attempts
        if result["done"]:
            return
        try:
            guess = int(entry.get().strip())
        except ValueError:
            hint.config(text="Enter a whole number.", fg="#b00")
            return

        if guess < 1 or guess > 20:
            hint.config(text="Range is 1–20.", fg="#b00")
            return

        if guess == secret:
            result["done"] = True
            result["success"] = True
            top.destroy()
            return

        attempts -= 1
        if attempts <= 0:
            result["done"] = True
            result["success"] = False
            top.destroy()
            return

        if guess < secret:
            hint.config(text="Higher.", fg="#333")
        else:
            hint.config(text="Lower.", fg="#333")
        status.config(text=f"Attempts left: {attempts}")
        entry.delete(0, tk.END)

    btn = ttk.Button(top, text="SUBMIT", command=submit)
    btn.pack(padx=12, pady=(0, 12), fill="x")
    top.bind("<Return>", lambda _e: submit())

    top.wait_window()
    return bool(result["success"])
