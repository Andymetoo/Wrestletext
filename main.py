from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk

from mechanics import (
    chain_wrestling_game,
    grapple_qte_minigame,
    lockup_minigame,
    pin_minigame,
    submission_minigame,
)
from moves_db import MOVES
from wrestler import GrappleRole, MAX_HEALTH, Wrestler, WrestlerState


class TacticalWrestlingApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WrestleText: State-Based Tactical Simulation")
        self.root.geometry("460x820")

        self.player = Wrestler("YOU", True)
        self.cpu = Wrestler("CPU", False)
        self.turn = "player"  # "player" | "cpu"
        self.game_over = False
        self._player_bonus_available = False
        self._in_grapple_followup_picker = False
        self._last_turn_banner: str | None = None
        self._after_ids: list[str] = []

        self._build_ui()
        self._log("Match start. Win only by Pinfall or Submission.")
        self._start_turn("player")

    # --- UI ---
    def _build_ui(self) -> None:
        self.root.configure(bg="#101010")

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TProgressbar", troughcolor="#2a2a2a", background="#3aa655")
        # ttk resolves style names as 'Horizontal.<style>' for horizontal progressbars.
        try:
            style.layout("Horizontal.Hype.TProgressbar", style.layout("Horizontal.TProgressbar"))
        except tk.TclError:
            pass
        style.configure("Horizontal.Hype.TProgressbar", troughcolor="#2a2a2a", background="#ffd166")

        self.hud = tk.Frame(self.root, bg="#1b1b1b")
        self.hud.pack(fill="x", padx=8, pady=8)

        self.state_line = tk.Label(
            self.hud,
            text="",
            font=("Arial", 11, "bold"),
            fg="#f2f2f2",
            bg="#1b1b1b",
        )
        self.state_line.pack(fill="x", pady=(4, 8))

        # Bars (use grid so both sides stay centered/aligned)
        bars = tk.Frame(self.hud, bg="#1b1b1b")
        bars.pack(fill="x")
        bars.columnconfigure(0, weight=1, uniform="col")
        bars.columnconfigure(1, weight=1, uniform="col")

        # Player side
        left = tk.Frame(bars, bg="#1b1b1b")
        left.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tk.Label(left, text="YOU", fg="#67ff8a", bg="#1b1b1b", font=("Impact", 10)).pack(anchor="w")
        self.p_hp = ttk.Progressbar(left, maximum=MAX_HEALTH)
        self.p_hp.pack(fill="x")
        self.p_grit = ttk.Progressbar(left, maximum=self.player.max_grit)
        self.p_grit.pack(fill="x", pady=(4, 0))
        self.p_hype = ttk.Progressbar(left, maximum=100, style="Horizontal.Hype.TProgressbar")
        self.p_hype.pack(fill="x", pady=(4, 0))
        self.p_nums = tk.Label(left, text="", fg="#aaa", bg="#1b1b1b", font=("Arial", 9))
        self.p_nums.pack(anchor="w", pady=(2, 0))
        self.p_limbs = tk.Label(left, text="", fg="#aaa", bg="#1b1b1b", font=("Arial", 9))
        self.p_limbs.pack(anchor="w")

        # CPU side
        right = tk.Frame(bars, bg="#1b1b1b")
        right.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        tk.Label(right, text="CPU", fg="#ff6b6b", bg="#1b1b1b", font=("Impact", 10)).pack(anchor="e")
        self.c_hp = ttk.Progressbar(right, maximum=MAX_HEALTH)
        self.c_hp.pack(fill="x")
        self.c_grit = ttk.Progressbar(right, maximum=self.cpu.max_grit)
        self.c_grit.pack(fill="x", pady=(4, 0))
        self.c_hype = ttk.Progressbar(right, maximum=100, style="Horizontal.Hype.TProgressbar")
        self.c_hype.pack(fill="x", pady=(4, 0))
        self.c_nums = tk.Label(right, text="", fg="#aaa", bg="#1b1b1b", font=("Arial", 9))
        self.c_nums.pack(anchor="e", pady=(2, 0))
        self.c_limbs = tk.Label(right, text="", fg="#aaa", bg="#1b1b1b", font=("Arial", 9))
        self.c_limbs.pack(anchor="e")

        # Turn label
        self.turn_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 10, "bold"),
            fg="#ffd166",
            bg="#101010",
        )
        self.turn_label.pack(fill="x", padx=8)

        # Log (always visible)
        self.center_frame = tk.Frame(self.root, bg="#101010")
        self.center_frame.pack(fill="x", padx=8, pady=8)

        # Log (kept small so moves are prominent)
        self.log_frame = tk.Frame(self.center_frame, bg="#000", bd=2, relief="sunken")
        self.log_frame.pack(fill="x", expand=False)
        log_scroll = tk.Scrollbar(self.log_frame)
        log_scroll.pack(side="right", fill="y")
        self.log_text = tk.Text(
            self.log_frame,
            bg="#000",
            fg="#b6ffb6",
            font=("Consolas", 11),
            height=10,
            state="disabled",
            wrap="word",
            yscrollcommand=log_scroll.set,
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)

        # Allow finger/drag scrolling on the log.
        self.log_text.bind("<ButtonPress-1>", lambda e: self.log_text.scan_mark(e.x, e.y))
        # Some Tk builds (e.g., Pydroid3) don't accept 'gain' as a keyword.
        self.log_text.bind("<B1-Motion>", lambda e: self.log_text.scan_dragto(e.x, e.y, 1))

        # Log coloring
        self.log_text.tag_configure("you", foreground="#67ff8a", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("cpu", foreground="#5aa7ff", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("move", foreground="#ffd166", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("dmg", foreground="#ff6b6b")
        self.log_text.tag_configure("grit", foreground="#c77dff")
        self.log_text.tag_configure("sys", foreground="#cccccc")

        # Moves / context menu (bigger + scrollable)
        self.moves_frame = tk.Frame(self.root, bg="#101010")
        self.moves_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.moves_title = tk.Label(
            self.moves_frame,
            text="Moves",
            font=("Arial", 10, "bold"),
            fg="#f2f2f2",
            bg="#101010",
        )
        self.moves_title.pack(anchor="w", pady=(0, 6))
        # Scrollable move area so options never get cut off.
        self.moves_canvas = tk.Canvas(self.moves_frame, bg="#101010", highlightthickness=0, height=420)
        self.moves_scroll = tk.Scrollbar(self.moves_frame, orient="vertical", command=self.moves_canvas.yview)
        self.moves_canvas.configure(yscrollcommand=self.moves_scroll.set)
        self.moves_scroll.pack(side="right", fill="y")
        self.moves_canvas.pack(side="left", fill="both", expand=True)

        # Embedded modal panel (replaces moves list temporarily)
        self.modal_frame = tk.Frame(self.moves_frame, bg="#0b0b0b", bd=2, relief="sunken")
        self.modal_title = tk.Label(
            self.modal_frame,
            text="",
            font=("Arial", 11, "bold"),
            fg="#f2f2f2",
            bg="#0b0b0b",
        )
        self.modal_title.pack(fill="x", padx=10, pady=(10, 6))
        self.modal_body = tk.Frame(self.modal_frame, bg="#0b0b0b")
        self.modal_body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Inner content area for embedded modals.
        # Keep it left-anchored and let it fill the Moves panel width.
        # (We handle off-screen/cropping issues inside mechanics by anchoring
        # widgets left and respecting the host width.)
        self.modal_content = tk.Frame(self.modal_body, bg="#0b0b0b")
        self.modal_content.pack(fill="both", expand=True, anchor="nw")

        self.moves_grid = tk.Frame(self.moves_canvas, bg="#101010")
        self.moves_grid.columnconfigure(0, weight=1)
        self.moves_grid.columnconfigure(1, weight=1)
        self._moves_window_id = self.moves_canvas.create_window((0, 0), window=self.moves_grid, anchor="nw")

        def on_grid_configure(_e: tk.Event) -> None:
            self.moves_canvas.configure(scrollregion=self.moves_canvas.bbox("all"))

        def on_canvas_configure(e: tk.Event) -> None:
            self.moves_canvas.itemconfigure(self._moves_window_id, width=e.width)

        self.moves_grid.bind("<Configure>", on_grid_configure)
        self.moves_canvas.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(e: tk.Event) -> None:
            self.moves_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        self.moves_canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Allow finger/drag scrolling in the moves list.
        self.moves_canvas.bind("<ButtonPress-1>", lambda e: self.moves_canvas.scan_mark(e.x, e.y))
        self.moves_canvas.bind("<B1-Motion>", lambda e: self.moves_canvas.scan_dragto(e.x, e.y, 1))

        # Small system button (bottom-left) for restart without quitting.
        self.sys_btn = tk.Button(
            self.root,
            text="S",
            width=2,
            height=1,
            font=("Arial", 9, "bold"),
            bg="#222",
            fg="#f2f2f2",
            activebackground="#333",
            activeforeground="#fff",
            bd=1,
            relief="raised",
            command=self._open_system_menu,
        )
        self.sys_btn.place(x=6, y=-6, anchor="sw", relx=0.0, rely=1.0)

    def _schedule(self, ms: int, func) -> None:
        """Schedule a callback and keep track so restart can cancel it."""
        try:
            after_id = self.root.after(ms, func)
            self._after_ids.append(after_id)
        except tk.TclError:
            return

    def _cancel_scheduled(self) -> None:
        for after_id in list(self._after_ids):
            try:
                self.root.after_cancel(after_id)
            except tk.TclError:
                pass
        self._after_ids.clear()

    def _clear_log(self) -> None:
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _restart_match(self) -> None:
        """Reset the match state without exiting (useful on mobile wrappers)."""
        self._cancel_scheduled()
        self._hide_modal()

        self.player = Wrestler("YOU", True)
        self.cpu = Wrestler("CPU", False)
        self.turn = "player"
        self.game_over = False
        self._player_bonus_available = False
        self._in_grapple_followup_picker = False
        self._last_turn_banner = None

        # Ensure HUD bars match new wrestler caps.
        self.p_grit.configure(maximum=self.player.max_grit)
        self.c_grit.configure(maximum=self.cpu.max_grit)

        self._clear_log()
        self._log("Match restarted. Win only by Pinfall or Submission.")
        self._update_hud()
        self._start_turn("player")

    def _open_system_menu(self) -> None:
        if getattr(self, "_sys_menu_open", False):
            return
        self._sys_menu_open = True

        top = tk.Toplevel(self.root)
        top.title("System")
        top.transient(self.root)
        top.grab_set()
        top.resizable(False, False)

        wrap = tk.Frame(top, bg="#111")
        wrap.pack(fill="both", expand=True)

        tk.Label(wrap, text="System", font=("Arial", 12, "bold"), fg="#f2f2f2", bg="#111").pack(
            padx=14, pady=(14, 8)
        )

        ttk.Button(wrap, text="Restart Match", command=lambda: (top.destroy(), self._restart_match())).pack(
            fill="x", padx=14, pady=6
        )
        ttk.Button(wrap, text="Close", command=top.destroy).pack(fill="x", padx=14, pady=(0, 14))

        def on_close() -> None:
            try:
                top.destroy()
            finally:
                self._sys_menu_open = False

        top.protocol("WM_DELETE_WINDOW", on_close)
        top.bind("<Escape>", lambda _e: on_close())
        self._position_modal_bottom(top, bottom_padding=28)
        top.wait_window()
        self._sys_menu_open = False

    def _show_modal(self, title: str) -> None:
        self.modal_title.config(text=title)
        # Some flows previously packed widgets directly into modal_body.
        # Clear everything except the fixed modal_content container.
        for w in list(self.modal_body.winfo_children()):
            if w is self.modal_content:
                continue
            w.destroy()
        for w in list(self.modal_content.winfo_children()):
            w.destroy()
        # Hide the normal moves list UI.
        try:
            self.moves_title.pack_forget()
        except tk.TclError:
            pass
        try:
            self.moves_canvas.pack_forget()
        except tk.TclError:
            pass
        try:
            self.moves_scroll.pack_forget()
        except tk.TclError:
            pass

        # Overlay the modal to guarantee full-width alignment.
        # (Pack-based stacking can leave the modal squeezed or shifted if a
        # scrollbar/widget remains packed unexpectedly.)
        try:
            self.modal_frame.place(in_=self.moves_frame, x=0, y=0, relwidth=1.0, relheight=1.0)
            self.modal_frame.lift()
        except tk.TclError:
            # Fallback
            self.modal_frame.pack(fill="both", expand=True)

    def _hide_modal(self) -> None:
        try:
            self.modal_frame.place_forget()
        except tk.TclError:
            pass
        if self.modal_frame.winfo_ismapped():
            try:
                self.modal_frame.pack_forget()
            except tk.TclError:
                pass
        if not self.moves_title.winfo_ismapped():
            self.moves_title.pack(anchor="w", pady=(0, 6))
        if not self.moves_scroll.winfo_ismapped():
            self.moves_scroll.pack(side="right", fill="y")
        if not self.moves_canvas.winfo_ismapped():
            self.moves_canvas.pack(side="left", fill="both", expand=True)

    def _log(self, msg: str) -> None:
        if self.game_over:
            return
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"> {msg}\n", ("sys",))
        self.log_text.see("end")
        self.log_text.yview_moveto(1.0)
        self.log_text.config(state="disabled")

    def _log_parts(self, parts: list[tuple[str, str]]) -> None:
        if self.game_over:
            return
        self.log_text.config(state="normal")
        self.log_text.insert("end", "> ", ("sys",))
        for text, tag in parts:
            self.log_text.insert("end", text, (tag,))
        self.log_text.insert("end", "\n", ("sys",))
        self.log_text.see("end")
        self.log_text.yview_moveto(1.0)
        self.log_text.config(state="disabled")

    def _position_modal_bottom(self, top: tk.Toplevel, *, bottom_padding: int = 20) -> None:
        try:
            self.root.update_idletasks()
            top.update_idletasks()
            pw = self.root.winfo_width()
            ph = self.root.winfo_height()
            px = self.root.winfo_rootx()
            py = self.root.winfo_rooty()
            tw = top.winfo_width()
            th = top.winfo_height()
            x = px + max(0, (pw - tw) // 2)
            y = py + max(0, ph - th - bottom_padding)
            top.geometry(f"+{x}+{y}")
        except tk.TclError:
            return

    def _update_hud(self) -> None:
        def role(w: Wrestler) -> str:
            if (not w.is_in_grapple()) or w.grapple_role is None:
                return ""
            return f" ({w.grapple_role.value})"

        def flow(w: Wrestler) -> str:
            if not w.is_flow():
                return ""
            return f" [FLOW {w.flow_turns_remaining}]"

        self.state_line.config(text=f"YOU: {self.player.state.value}{role(self.player)}{flow(self.player)}  |  CPU: {self.cpu.state.value}{role(self.cpu)}{flow(self.cpu)}")
        self.turn_label.config(text=f"TURN: {'YOU' if self.turn == 'player' else 'CPU'}")

        self.p_hp["value"] = self.player.hp
        self.c_hp["value"] = self.cpu.hp
        self.p_grit["value"] = self.player.grit
        self.c_grit["value"] = self.cpu.grit
        self.p_hype["value"] = self.player.hype
        self.c_hype["value"] = self.cpu.hype

        self.p_nums.config(text=f"HP {self.player.hp}/{MAX_HEALTH}  |  Grit {self.player.grit}/{self.player.max_grit}  |  Hype {self.player.hype}/100")
        self.c_nums.config(text=f"HP {self.cpu.hp}/{MAX_HEALTH}  |  Grit {self.cpu.grit}/{self.cpu.max_grit}  |  Hype {self.cpu.hype}/100")

        self.p_limbs.config(
            text=f"H:{self.player.body_parts['HEAD']}  B:{self.player.body_parts['BODY']}  L:{self.player.body_parts['LEGS']}"
        )
        self.c_limbs.config(
            text=f"H:{self.cpu.body_parts['HEAD']}  B:{self.cpu.body_parts['BODY']}  L:{self.cpu.body_parts['LEGS']}"
        )

    # --- Moves filtering ---
    def _move_is_legal(self, move_name: str, user: Wrestler, target: Wrestler) -> bool:
        move = MOVES[move_name]
        if move.get("only_in_grapple_followup") and not self._in_grapple_followup_picker:
            return False
        ru = move["req_user_state"]
        rt = move["req_target_state"]

        # Back-compat: older move DBs may still use the generic token 'GRAPPLED'.
        if ru != "ANY":
            if ru in {"GRAPPLED", "GRAPPLE_ANY"}:
                if not user.is_in_grapple():
                    return False
            elif ru != user.state.value:
                return False

        if rt != "ANY":
            if rt in {"GRAPPLED", "GRAPPLE_ANY"}:
                if not target.is_in_grapple():
                    return False
            elif rt != target.state.value:
                return False
        return True

    def _is_universal_action(self, move_name: str) -> bool:
        # Requested universal actions, plus a few safety/escape options to avoid soft-locks.
        return move_name in {
            "Rest",
            "Taunt",
            "Lock Up",
            "Slow Stand Up",
            "Kip-up",
            "Climb Down",
            "Stop Short",
        }

    def _passes_moveset(self, wrestler: Wrestler, move_name: str) -> bool:
        if self._is_universal_action(move_name):
            return True
        if wrestler.moveset is None:
            return True
        return move_name in set(wrestler.moveset)

    def _available_moves(self, user: Wrestler, target: Wrestler) -> list[str]:
        names = [n for n in MOVES.keys() if self._move_is_legal(n, user, target) and self._passes_moveset(user, n)]

        # Neutral restrictions: standing (neutral) only allows strikes, attempt grapple, and taunts.
        if user.state == WrestlerState.STANDING and target.state == WrestlerState.STANDING:
            allowed_names = {"Lock Up", "Taunt"}
            names = [n for n in names if MOVES[n].get("type") == "Strike" or n in allowed_names]
            if self._move_is_legal("Rest", user, target) and self._passes_moveset(user, "Rest"):
                names.append("Rest")

        # Grapple restrictions: in the WEAK tie-up, the defender mostly fights for control.
        # (Other grapple tiers will later get dedicated reversals/strikes.)
        if (
            user.state == WrestlerState.GRAPPLE_WEAK
            and target.state == WrestlerState.GRAPPLE_WEAK
            and user.grapple_role == GrappleRole.DEFENSE
        ):
            defensive_names = [n for n in names if n == "Chain Wrestle"]
            if defensive_names:
                names = defensive_names

        def key(n: str) -> tuple[int, int, str]:
            t = MOVES[n]["type"]
            type_order = {"Setup": 0, "Strike": 1, "Grapple": 2, "Aerial": 3, "Submission": 4, "Pin": 5}
            return (type_order.get(t, 99), int(MOVES[n]["cost"]), n)

        return sorted(names, key=key)

    def _available_grapple_finishes(self, user: Wrestler, target: Wrestler) -> list[str]:
        moves = self._available_moves(user, target)
        return [m for m in moves if MOVES[m].get("type") == "Grapple"]

    def _choose_grapple_followup(self, user: Wrestler, target: Wrestler) -> str | None:
        options = [m for m in self._available_grapple_finishes(user, target) if MOVES[m]["cost"] <= user.grit]
        if not options:
            return None

        self._in_grapple_followup_picker = True
        try:
            self._show_modal("Choose Grapple")
            chosen_var: tk.StringVar = tk.StringVar(value="")
            done_var: tk.BooleanVar = tk.BooleanVar(value=False)

            tk.Label(
                self.modal_content,
                text="Pick a grapple follow-up:",
                fg="#f2f2f2",
                bg="#0b0b0b",
                font=("Arial", 10, "bold"),
            ).pack(
                anchor="w", pady=(0, 8)
            )

            for name in options[:10]:
                mv = MOVES[name]
                cost = int(mv["cost"])
                dmg = int(mv["damage"])
                ttk.Button(
                    self.modal_content,
                    text=f"{name} (Cost {cost}, Dmg {dmg})",
                    command=lambda n=name: (chosen_var.set(n), done_var.set(True)),
                ).pack(fill="x", pady=4)

            ttk.Button(self.modal_content, text="Cancel", command=lambda: done_var.set(True)).pack(fill="x", pady=(10, 0))
            self.root.wait_variable(done_var)
            val = chosen_var.get().strip() or None
            return val
        finally:
            self._in_grapple_followup_picker = False
            self._hide_modal()

    def _refresh_player_buttons(self) -> None:
        for child in list(self.moves_grid.winfo_children()):
            child.destroy()

        if self.game_over or self.turn != "player":
            return

        moves = self._available_moves(self.player, self.cpu)
        affordable = [m for m in moves if (0 if self.player.is_flow() else MOVES[m]["cost"]) <= self.player.grit]
        if len(affordable) == 0:
            moves_to_show = ["Rest"]
        else:
            moves_to_show = moves
            # Only show Rest as fallback when you can't afford anything.

        if len(moves_to_show) == 0:
            moves_to_show = ["Rest"]

        max_buttons = 16
        moves_to_show = moves_to_show[:max_buttons]

        for idx, name in enumerate(moves_to_show):
            move = MOVES[name]
            base_cost = int(move["cost"])
            cost = 0 if self.player.is_flow() else base_cost
            dmg = int(move["damage"])
            label = f"{name}\nCost {cost}"
            if dmg > 0:
                label += f" | Dmg {dmg}"

            r, c = divmod(idx, 2)
            btn = tk.Button(
                self.moves_grid,
                text=label,
                height=2,
                font=("Arial", 10, "bold"),
                bg="#2f2f2f",
                fg="#f2f2f2",
                activebackground="#444",
                activeforeground="#fff",
                command=lambda n=name: self._player_take_action(n),
            )
            btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

            if name != "Rest" and cost > self.player.grit:
                btn.config(state="disabled", bg="#222", fg="#777")

    # --- Turn flow ---
    def _start_turn(self, who: str) -> None:
        if self.game_over:
            return
        self.turn = who
        active = self.player if who == "player" else self.cpu

        # Turn banner to separate actions in the log.
        banner = "YOU" if who == "player" else "CPU"
        if self._last_turn_banner != banner:
            self._last_turn_banner = banner
            self._log("".ljust(34, "-"))
            self._log_parts([(f"{banner} TURN", "move")])

        # Stun: skip the turn.
        if active.stun_turns > 0:
            active.stun_turns = max(0, active.stun_turns - 1)
            tag = "you" if active.is_player else "cpu"
            self._log_parts([(active.name, tag), (" is stunned and can't act!", "sys")])
            self._update_hud()
            active.on_turn_end()
            nxt = "cpu" if who == "player" else "player"
            if nxt == "cpu":
                self._schedule(700, lambda: self._start_turn("cpu"))
            else:
                self._schedule(350, lambda: self._start_turn("player"))
            return

        if who == "player":
            self._player_bonus_available = True

        gained = active.regen_grit()
        if gained > 0:
            tag = "you" if active.is_player else "cpu"
            self._log_parts([(active.name, tag), (" regains ", "sys"), (f"{gained} Grit", "grit"), (".", "sys")])

        self._update_hud()

        if who == "player":
            self._refresh_player_buttons()
        else:
            for child in list(self.moves_grid.winfo_children()):
                child.destroy()
            self._schedule(700, self._cpu_take_turn)

    def _end_match(self, winner: str, reason: str) -> None:
        if self.game_over:
            return
        self.game_over = True
        self._update_hud()
        messagebox.showinfo("Match End", f"{winner} wins by {reason}!")
        self.root.destroy()

    # --- Player action ---
    def _player_take_action(self, move_name: str) -> None:
        if self.game_over or self.turn != "player":
            return
        before = self.cpu.state
        keep_turn = self._execute_move(attacker=self.player, defender=self.cpu, move_name=move_name)
        if self.game_over:
            return

        if keep_turn:
            self._update_hud()
            self._refresh_player_buttons()
            return

        move = MOVES.get(move_name, {})
        knocked_down = (
            self._player_bonus_available
            and move.get("set_target_state") == "GROUNDED"
            and before != WrestlerState.GROUNDED
            and self.cpu.state == WrestlerState.GROUNDED
        )

        if knocked_down:
            self._player_bonus_available = False
            self._log("Momentum! You keep control for one more action.")
            self._update_hud()
            self._refresh_player_buttons()
            return
        self.player.on_turn_end()
        self._start_turn("cpu")

    # --- CPU action ---
    def _cpu_choose_move(self) -> str:
        options = self._available_moves(self.cpu, self.player)
        affordable = [m for m in options if self._effective_cost(self.cpu, m) <= self.cpu.grit]
        if not affordable:
            return "Rest"

        def score(name: str) -> float:
            mv = MOVES[name]
            base = float(mv.get("damage", 0))
            t = mv["type"]
            base += float(int(mv.get("hype_gain", 0))) * 0.10

            # --- Grapple tier awareness (AKI-style) ---
            if self.cpu.state == WrestlerState.GRAPPLE_WEAK:
                # CPU wants to tier up when it has resources.
                if name == "Deepen Hold":
                    if self.cpu.grit > 8 or self.cpu.hype > 70:
                        base += 18.0
                    else:
                        base -= 4.0

                # When low on grit, prefer cheaper, safer weak options.
                if self.cpu.grit <= 5:
                    cost = float(self._effective_cost(self.cpu, name))
                    if cost <= 3 and float(mv.get("damage", 0)) > 0:
                        base += 4.0
                    if cost >= 6:
                        base -= 2.0

            elif self.cpu.state == WrestlerState.GRAPPLE_STRONG:
                # In strong holds, prioritize big damage and finishers.
                if t == "Grapple":
                    base += 4.0
                if bool(mv.get("is_finisher")):
                    base += 6.0
                # If opponent is softened up, pressing for a finisher is even better.
                if bool(mv.get("is_finisher")) and self.player.hp_pct() < 0.40:
                    base += 6.0

            # Neutral grappling pressure.
            if name == "Lock Up" and self.cpu.state == WrestlerState.STANDING and self.player.state == WrestlerState.STANDING:
                base += 6.0
            if name == "Taunt" and self.cpu.hype < 80:
                base += 3.0

            if name == "Chain Wrestle" and self.cpu.is_in_grapple():
                base += 5.0
            if t == "Pin" and self.player.state == WrestlerState.GROUNDED:
                base += 25.0 * (1.0 - self.player.hp_pct())
            if t == "Submission" and self.player.state == WrestlerState.GROUNDED:
                base += 20.0 * (1.0 - self.player.hp_pct())
            if mv.get("set_target_state") == "GROUNDED":
                base += 6.0
            if mv.get("set_target_state") == "RUNNING":
                base += 3.0
            # Slightly prefer cheaper moves when low on grit.
            base -= 0.15 * self._effective_cost(self.cpu, name)
            # Add small randomness so it doesn't play identical.
            return base + random.random() * 1.5

        affordable.sort(key=score, reverse=True)
        return affordable[0]

    def _cpu_take_turn(self) -> None:
        if self.game_over or self.turn != "cpu":
            return
        move_name = self._cpu_choose_move()
        keep_turn = self._execute_move(attacker=self.cpu, defender=self.player, move_name=move_name)
        if self.game_over:
            return
        if keep_turn:
            self._update_hud()
            self._schedule(450, self._cpu_take_turn)
            return
        self.cpu.on_turn_end()
        self._start_turn("player")

    # --- Reaction interrupts ---
    def _reaction_menu(self, incoming_damage: int) -> dict:
        """Returns {choice:str}. Choice in {'BRACE','DODGE','REVERSAL'}.

        Grit is spent inside this dialog for DODGE/REVERSAL.
        """
        self._show_modal("React!")
        try:
            tk.Label(
                self.modal_content,
                text=f"CPU attacks! Incoming damage: {incoming_damage}",
                fg="#f2f2f2",
                bg="#0b0b0b",
                font=("Arial", 11, "bold"),
            ).pack(pady=(0, 6))
            tk.Label(
                self.modal_content,
                text=f"Your Grit: {self.player.grit}",
                fg="#aaa",
                bg="#0b0b0b",
                font=("Arial", 9),
            ).pack(pady=(0, 10))

            choice_var: tk.StringVar = tk.StringVar(value="BRACE")
            done_var: tk.BooleanVar = tk.BooleanVar(value=False)

            def timeout() -> None:
                if bool(done_var.get()):
                    return
                choice_var.set("BRACE")
                done_var.set(True)

            def pick(choice: str) -> None:
                choice_var.set(choice)
                done_var.set(True)

            ttk.Button(self.modal_content, text="Brace (0 Grit) – Take 50%", command=lambda: pick("BRACE")).pack(fill="x", pady=4)

            b2 = ttk.Button(self.modal_content, text="Dodge (2 Grit) – Skill check", command=lambda: pick("DODGE"))
            b2.pack(fill="x", pady=4)
            if self.player.grit < 2:
                b2.state(["disabled"])

            b3 = ttk.Button(self.modal_content, text="Reversal (4 Grit) – Skill check", command=lambda: pick("REVERSAL"))
            b3.pack(fill="x", pady=4)
            if self.player.grit < 4:
                b3.state(["disabled"])

            # Auto-resolve to BRACE if the device doesn't register the tap.
            self.root.after(12000, timeout)

            self.root.wait_variable(done_var)
            choice = choice_var.get()

            # Spend grit here (so player sees it immediately in HUD after returning)
            if choice == "DODGE":
                self.player.spend_grit(2)
            elif choice == "REVERSAL":
                self.player.spend_grit(4)

            return {"chosen": True, "choice": choice}
        finally:
            self._hide_modal()

    def _reaction_skill_check(self) -> float:
        """Return a performance score 0..1 based on a random minigame."""
        choice = random.choice(["qte", "lockup", "overunder"])
        if choice == "qte":
            self._show_modal("React Timing")
            try:
                out = grapple_qte_minigame(
                    self.root,
                    title="React Timing",
                    prompt="React! Nail the timing to improve your odds.",
                    duration_ms=2600,
                    host=self.modal_content,
                )
            finally:
                self._hide_modal()
            tier = out["tier"]
            if tier == "CRIT":
                return 1.0
            if tier == "HIT":
                return 0.75
            if tier == "WEAK":
                return 0.4
            return 0.0
        if choice == "lockup":
            self._show_modal("React Struggle")
            try:
                ok = lockup_minigame(
                    self.root,
                    title="React Struggle",
                    prompt="React! PUSH/HOLD to improve your odds.",
                    host=self.modal_content,
                )
            finally:
                self._hide_modal()
            return 1.0 if ok else 0.0
        self._show_modal("React Read")
        try:
            ok = submission_minigame(
                self.root,
                title="React Read",
                prompt="React! Call HIGHER/LOWER correctly to improve your odds.",
                victim_hp_pct=self.player.hp_pct(),
                host=self.modal_content,
            )
        finally:
            self._hide_modal()
        return 1.0 if ok else 0.0

    # --- N64 helpers ---
    def _effective_cost(self, w: Wrestler, move_name: str) -> int:
        base = int(MOVES[move_name]["cost"])
        return 0 if w.is_flow() else base

    def _enter_grapple(self, *, offense: Wrestler, defense: Wrestler) -> None:
        # Phase 1 mapping: entering a grapple starts in GRAPPLE_WEAK.
        offense.set_state(WrestlerState.GRAPPLE_WEAK)
        defense.set_state(WrestlerState.GRAPPLE_WEAK)
        offense.grapple_role = GrappleRole.OFFENSE
        defense.grapple_role = GrappleRole.DEFENSE

    def _clear_grapple_roles_if_exited(self, a: Wrestler, b: Wrestler) -> None:
        if (not a.is_in_grapple()) or (not b.is_in_grapple()):
            a.grapple_role = None
            b.grapple_role = None

    def _cpu_neutral_intent(self) -> str:
        """Return CPU intent in neutral: STRIKE | GRAPPLE | PASSIVE."""
        # Bias toward strikes when it can afford them; grapple sometimes; passive rarely.
        if self.cpu.grit <= 1:
            weights = [("STRIKE", 0.35), ("GRAPPLE", 0.25), ("PASSIVE", 0.40)]
        else:
            weights = [("STRIKE", 0.55), ("GRAPPLE", 0.35), ("PASSIVE", 0.10)]
        r = random.random()
        acc = 0.0
        for name, w in weights:
            acc += w
            if r <= acc:
                return name
        return "STRIKE"

    def _simulated_player_intent(self) -> str:
        """When CPU initiates, simulate the player's neutral intent."""
        if self.player.grit <= 1:
            weights = [("STRIKE", 0.35), ("GRAPPLE", 0.30), ("PASSIVE", 0.35)]
        else:
            weights = [("STRIKE", 0.50), ("GRAPPLE", 0.40), ("PASSIVE", 0.10)]
        r = random.random()
        acc = 0.0
        for name, w in weights:
            acc += w
            if r <= acc:
                return name
        return "STRIKE"

    def _pick_interrupt_strike(self, attacker: Wrestler, defender: Wrestler) -> str:
        """Pick a legal standing strike for an interrupt."""
        options = [n for n, mv in MOVES.items() if mv.get("type") == "Strike" and self._move_is_legal(n, attacker, defender)]
        # Prefer affordable; otherwise fall back to cheapest.
        affordable = [n for n in options if self._effective_cost(attacker, n) <= attacker.grit]
        pool = affordable if affordable else options
        if not pool:
            return "Desperation Slap"
        pool.sort(key=lambda n: (self._effective_cost(attacker, n), -int(MOVES[n]["damage"])))
        return pool[0]

    def _pin_victim_hp_pct(self, victim: Wrestler) -> float:
        base = victim.hp_pct()
        if victim.hp == 0:
            base = min(base, 0.15)
        # Depth update: damaged head makes pin timing harder.
        if victim.is_critical_head():
            base = min(1.0, base + 0.20)
        return max(0.0, min(1.0, base))

    # --- Core move execution ---
    def _execute_move(self, *, attacker: Wrestler, defender: Wrestler, move_name: str, allow_reaction: bool = True) -> bool:
        if self.game_over:
            return False

        if move_name != "Rest" and not self._move_is_legal(move_name, attacker, defender):
            self._log(f"{attacker.name} tried {move_name}, but it wasn't legal.")
            return False

        move = MOVES[move_name]
        cost = int(move["cost"])
        if not attacker.spend_grit(cost):
            self._log(f"{attacker.name} doesn't have enough Grit for {move_name}.")
            return False

        attacker_tag = "you" if attacker.is_player else "cpu"
        self._log_parts(
            [
                (attacker.name, attacker_tag),
                (" uses ", "sys"),
                (move_name, "move"),
                ("! ", "sys"),
                (move["flavor_text"], "sys"),
            ]
        )

        # Rest is special: high regen.
        if move_name == "Rest":
            bonus = 5
            before = attacker.grit
            attacker.grit = min(attacker.max_grit, attacker.grit + bonus)
            self._log_parts(
                [
                    (attacker.name, attacker_tag),
                    (" recovers (", "sys"),
                    (f"+{attacker.grit - before} Grit", "grit"),
                    (").", "sys"),
                ]
            )
            self._update_hud()
            return False

        if move_name == "Slow Stand Up":
            # 0-cost, low-reliability get-up.
            base = 0.55 if attacker.hp_pct() > 0.25 else 0.4
            if random.random() < base:
                attacker.set_state(WrestlerState.STANDING)
                self._log_parts([(attacker.name, attacker_tag), (" makes it back to their feet.", "sys")])
            else:
                attacker.set_state(WrestlerState.GROUNDED)
                self._log_parts([(attacker.name, attacker_tag), (" can't quite stand yet...", "sys")])
            self._update_hud()
            return False

        if move_name == "Taunt":
            attacker.add_hype(int(move.get("hype_gain", 0)))
            self._log_parts([(attacker.name, attacker_tag), (" gets fired up!", "sys")])
            self._update_hud()
            return False

        mtype = move["type"]

        # Lock Up: Neutral RPS vs opponent intent.
        if move_name == "Lock Up":
            intent = self._simulated_player_intent() if defender.is_player else self._cpu_neutral_intent()
            if defender.stun_turns > 0:
                intent = "PASSIVE"

            if intent == "STRIKE":
                strike = self._pick_interrupt_strike(defender, attacker)
                strike_mv = MOVES[strike]
                strike_dmg = int(strike_mv.get("damage", 0))

                # Break-through logic: a hot/healthy wrestler can eat the shot and still secure the tie-up.
                # Base 20% + (PlayerHype - CPUHype)% + (PlayerHealth% - CPUHealth%)/2
                # (Generalized to attacker/defender.)
                break_chance = 0.20
                break_chance += (float(attacker.hype) - float(defender.hype)) / 100.0
                break_chance += (float(attacker.hp_pct()) - float(defender.hp_pct())) / 2.0
                break_chance = max(0.0, min(0.95, break_chance))

                if random.random() < break_chance:
                    self._log(f"{defender.name} nails an interrupt, but {attacker.name} powers through!")
                    half = max(1, int(round(strike_dmg * 0.5))) if strike_dmg > 0 else 0
                    if half > 0:
                        attacker.take_damage(half, target_part=str(strike_mv.get("target_part", "BODY")))
                    # Still proceed to lock-up clash.
                    intent = "GRAPPLE"
                else:
                    self._log(f"{defender.name} stuffs the lock-up attempt!")
                    # Interrupt hit: no reaction menu.
                    self._execute_move(attacker=defender, defender=attacker, move_name=strike, allow_reaction=False)
                    self._update_hud()
                    return False

            if intent == "PASSIVE":
                self._log(f"{defender.name} is caught flat-footed — grapple secured!")
                self._enter_grapple(offense=attacker, defense=defender)
                attacker.add_hype(int(move.get("hype_gain", 0)))
                self._update_hud()
                return True

            # GRAPPLE: lock-up clash.
            if attacker.is_player:
                self._show_modal("Lock Up")
                try:
                    player_won = lockup_minigame(
                        self.root,
                        title="Lock Up",
                        prompt="Clash! PUSH or HOLD to win position.",
                        host=self.modal_content,
                    )
                finally:
                    self._hide_modal()
                attacker_won = bool(player_won)
            else:
                # CPU turn: simulate the tie-up.
                attacker_won = random.random() < 0.5

            if attacker_won:
                self._log(f"{attacker.name} wins the clash and takes control!")
                self._enter_grapple(offense=attacker, defense=defender)
                attacker.add_hype(int(move.get("hype_gain", 0)))
                self._update_hud()
                return True

            self._log(f"{defender.name} wins the clash and turns it around!")
            self._enter_grapple(offense=defender, defense=attacker)
            defender.add_hype(int(move.get("hype_gain", 0)))
            self._update_hud()
            return False

        # Chain Wrestling (in-grapple) – blind RPS for control.
        if move_name == "Chain Wrestle":
            if attacker.is_player:
                self._show_modal("Chain Wrestling")
                try:
                    out = chain_wrestling_game(
                        self.root,
                        title="Chain Wrestling",
                        prompt="POWER / SPEED / TECHNICAL",
                        host=self.modal_content,
                    )
                finally:
                    self._hide_modal()
                result = str(out.get("result", "TIE"))
            else:
                # CPU: simulate blind RPS.
                player = random.choice(["POWER", "SPEED", "TECHNICAL"])
                cpu = random.choice(["POWER", "SPEED", "TECHNICAL"])
                beats = {"POWER": "SPEED", "SPEED": "TECHNICAL", "TECHNICAL": "POWER"}
                if player == cpu:
                    result = "TIE"
                elif beats[player] == cpu:
                    result = "WIN"
                else:
                    result = "LOSS"

            if result == "WIN":
                attacker.next_damage_multiplier = 1.25
                self._log(f"{attacker.name} maintains control! Next move hits harder.")
                attacker.add_hype(int(move.get("hype_gain", 0)))
            elif result == "LOSS":
                self._log(f"{defender.name} reverses the hold and takes control!")
                attacker.grapple_role = GrappleRole.DEFENSE
                defender.grapple_role = GrappleRole.OFFENSE
                defender.add_hype(int(move.get("hype_gain", 0)))
            else:
                self._log("Stalemate—still tied up!")

            self._update_hud()
            return False

        # Grapple Gateway: tier-up from WEAK -> STRONG.
        # This is the AKI-style struggle point.
        if move_name == "Deepen Hold":
            # Only meaningful from a weak tie-up.
            if attacker.state != WrestlerState.GRAPPLE_WEAK or defender.state != WrestlerState.GRAPPLE_WEAK:
                self._log("No opening to deepen the hold.")
                self._update_hud()
                return False

            if attacker.is_player:
                self._show_modal("Deepen Hold")
                try:
                    out = chain_wrestling_game(
                        self.root,
                        title="Deepen Hold",
                        prompt="Secure the hold: POWER / SPEED / TECHNICAL",
                        host=self.modal_content,
                    )
                finally:
                    self._hide_modal()
                outcome = str(out.get("result", "TIE"))
            else:
                # CPU: simulate blind RPS.
                player = random.choice(["POWER", "SPEED", "TECHNICAL"])
                cpu = random.choice(["POWER", "SPEED", "TECHNICAL"])
                beats = {"POWER": "SPEED", "SPEED": "TECHNICAL", "TECHNICAL": "POWER"}
                if player == cpu:
                    outcome = "TIE"
                elif beats[player] == cpu:
                    outcome = "WIN"
                else:
                    outcome = "LOSS"

            # WIN: allow the move DB's state changes to apply below.
            if outcome == "WIN":
                self._log(f"{attacker.name} secures a strong hold!")
            # LOSS: break the grapple completely.
            elif outcome == "LOSS":
                self._log(f"{defender.name} pushes them away! Grapple broken.")
                attacker.set_state(WrestlerState.STANDING)
                defender.set_state(WrestlerState.STANDING)
                self._clear_grapple_roles_if_exited(attacker, defender)
                self._update_hud()
                return False
            # TIE: remain in GRAPPLE_WEAK and prevent tier-up.
            else:
                self._log("Stalemate! Still in a weak clinch.")
                self._update_hud()
                return False

        # Pin / Submission resolve match-ending conditions.
        if mtype == "Pin":
            if attacker.is_player:
                self._show_modal("Pin Attempt")
                try:
                    ok = pin_minigame(
                        self.root,
                        title="Pin Attempt",
                        prompt="PIN! Stop the marker in the green window to score the fall.",
                        victim_hp_pct=self._pin_victim_hp_pct(defender),
                        host=self.modal_content,
                    )
                finally:
                    self._hide_modal()
                if ok:
                    self._end_match("YOU", "PINFALL")
                else:
                    self._log("They kicked out!")
            else:
                self._show_modal("Kick Out")
                try:
                    ok = pin_minigame(
                        self.root,
                        title="Kick Out!",
                        prompt="KICK OUT! Stop the marker in the green window to survive.",
                        victim_hp_pct=self._pin_victim_hp_pct(defender),
                        host=self.modal_content,
                    )
                finally:
                    self._hide_modal()
                if ok:
                    self._log("You kicked out!")
                else:
                    self._end_match("CPU", "PINFALL")
            self._update_hud()
            return False

        if mtype == "Submission":
            if attacker.is_player:
                self._show_modal("Submission")
                try:
                    ok = submission_minigame(
                        self.root,
                        title="Submission Attempt",
                        prompt="Finish it! Call HIGHER or LOWER correctly.",
                        victim_hp_pct=defender.hp_pct(),
                        host=self.modal_content,
                    )
                finally:
                    self._hide_modal()
                if ok:
                    self._end_match("YOU", "SUBMISSION")
                else:
                    self._log("They fought out of the hold!")
            else:
                self._show_modal("Escape Submission")
                try:
                    ok = submission_minigame(
                        self.root,
                        title="Escape Submission!",
                        prompt="Escape! Call HIGHER or LOWER correctly to survive.",
                        victim_hp_pct=defender.hp_pct(),
                        host=self.modal_content,
                    )
                finally:
                    self._hide_modal()
                if ok:
                    self._log("You escaped the submission!")
                else:
                    self._end_match("CPU", "SUBMISSION")
            self._update_hud()
            return False

        # Running failure: bad legs can cause a trip on running offense.
        if (
            move.get("req_user_state") == "RUNNING"
            and attacker.state == WrestlerState.RUNNING
            and attacker.is_critical_legs()
            and move_name not in {"Stop Short"}
            and random.random() < 0.50
        ):
            self._log(f"{attacker.name} stumbles—bad legs! They trip and go down!")
            attacker.set_state(WrestlerState.GROUNDED)
            attacker.take_damage(2)
            self._update_hud()
            return False

        # Grapple QTE (player only) – timing affects damage on grapple finishers.
        if mtype == "Grapple" and attacker.is_player and int(move.get("damage", 0)) > 0:
            self._show_modal("Grapple Timing")
            try:
                outcome = grapple_qte_minigame(
                    self.root,
                    title="Grapple Timing",
                    prompt=f"{move_name}! Hit the timing window.",
                    host=self.modal_content,
                )
            finally:
                self._hide_modal()
            tier = outcome["tier"]
            timing = int(outcome["timing"])
            mult = float(outcome["multiplier"])

            # One-shot chain wrestling buff.
            buff = float(attacker.next_damage_multiplier)
            attacker.next_damage_multiplier = 1.0

            if tier == "BOTCH":
                self._log(f"BOTCH! (Timing {timing}%) You crash and burn!")
                self.player.take_damage(6, target_part="BODY")
            else:
                base_dmg = int(move["damage"])
                final = max(1, int(base_dmg * mult * buff))
                if tier == "CRIT":
                    self._log(f"PERFECT! (Timing {timing}%)")
                elif tier == "HIT":
                    self._log(f"GOOD HIT! (Timing {timing}%)")
                else:
                    self._log(f"WEAK... (Timing {timing}%)")
                defender.take_damage(final, target_part=str(move.get("target_part", "BODY")))
                self._log(f"{defender.name} takes {final} damage.")

                attacker.add_hype(int(move.get("hype_gain", 0)))

                if str(move.get("target_part", "BODY")) == "HEAD" and defender.is_critical_head() and random.random() < 0.25:
                    defender.stun_turns += 1
                    self._log(f"{defender.name} looks rocked!")

            # Apply state transitions after QTE resolution if not botched.
            if tier != "BOTCH":
                if "set_user_state" in move:
                    attacker.set_state(WrestlerState(move["set_user_state"]))
                if "set_target_state" in move:
                    defender.set_state(WrestlerState(move["set_target_state"]))

            self._clear_grapple_roles_if_exited(attacker, defender)
            attacker.take_damage(2, target_part="LEGS")
            if defender.hp == 0:
                self._log(f"{defender.name} is exhausted (0 HP) — they're very vulnerable to Pin/Submission.")

            self._update_hud()
            return False

        raw_damage = int(move["damage"])
        negated = False

        # One-shot chain wrestling buff.
        dmg_mult = float(attacker.next_damage_multiplier)
        attacker.next_damage_multiplier = 1.0

        # Fluid Momentum: Player gets a reaction menu when CPU attacks.
        if (not attacker.is_player) and raw_damage > 0 and allow_reaction:
            final_incoming = max(1, int(raw_damage * dmg_mult))
            reaction = self._reaction_menu(final_incoming)
            self._update_hud()
            choice = reaction.get("choice", "BRACE")

            if choice == "BRACE":
                dmg = int((final_incoming + 1) // 2)
                self.player.take_damage(dmg, target_part=str(move.get("target_part", "BODY")))
                self._log_parts([(self.player.name, "you"), (" braces and takes ", "sys"), (f"{dmg}", "dmg"), (" damage.", "sys")])
                attacker.add_hype(int(move.get("hype_gain", 0)))
            elif choice == "DODGE":
                score = self._reaction_skill_check()
                chance = 0.8 if score >= 0.6 else 0.2
                if random.random() < chance:
                    negated = True
                    self._log("You dodge it!")
                else:
                    self.player.take_damage(final_incoming, target_part=str(move.get("target_part", "BODY")))
                    self._log_parts([(self.player.name, "you"), (" takes ", "sys"), (f"{final_incoming}", "dmg"), (" damage.", "sys")])
                    attacker.add_hype(int(move.get("hype_gain", 0)))
            else:  # REVERSAL
                score = self._reaction_skill_check()
                chance = 0.6 if score >= 0.6 else 0.1
                if random.random() < chance:
                    negated = True
                    self._log("REVERSAL! You turn it around!")
                    back = max(1, int(final_incoming * 0.8))
                    self.cpu.take_damage(back, target_part="BODY")
                    self._log_parts([(self.cpu.name, "cpu"), (" takes ", "sys"), (f"{back}", "dmg"), (" damage back.", "sys")])
                else:
                    self.player.take_damage(final_incoming, target_part=str(move.get("target_part", "BODY")))
                    self._log_parts([(self.player.name, "you"), (" takes ", "sys"), (f"{final_incoming}", "dmg"), (" damage.", "sys")])
                    attacker.add_hype(int(move.get("hype_gain", 0)))
        else:
            # Normal damage application (player attacking CPU, or non-damaging CPU move)
            if raw_damage > 0:
                if move_name == "Desperation Slap" and attacker.is_player and (not defender.is_player):
                    if random.random() < 0.75:
                        self._log_parts([(defender.name, "cpu"), (" easily avoids the lazy shot.", "sys")])
                        raw_damage = 0
                        negated = True

                final_damage = 0 if negated or raw_damage <= 0 else max(1, int(raw_damage * dmg_mult))
                if final_damage > 0:
                    defender.take_damage(final_damage, target_part=str(move.get("target_part", "BODY")))
                    dtag = "you" if defender.is_player else "cpu"
                    self._log_parts([(defender.name, dtag), (" takes ", "sys"), (f"{final_damage}", "dmg"), (" damage.", "sys")])

                if not negated:
                    attacker.add_hype(int(move.get("hype_gain", 0)))
                    if str(move.get("target_part", "BODY")) == "HEAD" and defender.is_critical_head() and random.random() < 0.25:
                        defender.stun_turns += 1
                        self._log(f"{defender.name} looks rocked!")

        # State transitions only happen if the hit wasn't fully negated (dodge/reversal).
        if not negated:
            if move_name == "Possum":
                # Small chance to trip the opponent.
                if random.random() < 0.35:
                    defender.set_state(WrestlerState.GROUNDED)
                    self._log("It worked! They stumble and hit the mat.")

            if raw_damage == 0:
                attacker.add_hype(int(move.get("hype_gain", 0)))

            if "set_user_state" in move:
                attacker.set_state(WrestlerState(move["set_user_state"]))
            if "set_target_state" in move:
                defender.set_state(WrestlerState(move["set_target_state"]))

            self._clear_grapple_roles_if_exited(attacker, defender)

        # If someone is at 0 HP, it only affects pin/sub difficulty.
        if defender.hp == 0:
            self._log(f"{defender.name} is exhausted (0 HP) — they're very vulnerable to Pin/Submission.")

        self._update_hud()
        return False


if __name__ == "__main__":
    root = tk.Tk()
    app = TacticalWrestlingApp(root)
    root.mainloop()
