from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk

from cards import HEX_COLORS
from mechanics import lockup_minigame
from moves_db import MOVES
from wrestler import GrappleRole, MAX_HEALTH, Wrestler, WrestlerState


MOVE_TYPE_FG: dict[str, str] = {
    "Strike": HEX_COLORS.get("RED", "#f2f2f2"),
    "Grapple": HEX_COLORS.get("BLUE", "#f2f2f2"),
    "Submission": HEX_COLORS.get("GREEN", "#f2f2f2"),
    "Pin": HEX_COLORS.get("GREEN", "#f2f2f2"),
    "Aerial": HEX_COLORS.get("YELLOW", "#f2f2f2"),
    "Setup": "#f2f2f2",
}


class TacticalWrestlingApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WrestleText: State-Based Tactical Simulation")
        # Responsive sizing: on small/phone-like screens, use full screen size.
        # Otherwise default to a compact desktop window.
        self._screen_w = 460
        self._screen_h = 820
        try:
            self._screen_w = int(self.root.winfo_screenwidth())
            self._screen_h = int(self.root.winfo_screenheight())
        except tk.TclError:
            pass

        is_phoneish = (self._screen_w <= 640) or (self._screen_h <= 900) or (self._screen_h / max(1, self._screen_w) > 1.35)
        if is_phoneish:
            self.root.geometry(f"{self._screen_w}x{self._screen_h}")
        else:
            self.root.geometry("460x820")

        # Android wrappers often have a bottom nav bar that overlaps the lowest pixels.
        # Reserve a small "safe area" so the Hand/SUBMIT can't be covered.
        self._safe_bottom = max(12, min(72, int(self._screen_h * 0.04)))
        self._hand_h_collapsed = max(72, min(160, int(self._screen_h * 0.11)))
        self._hand_h_expanded = max(140, min(280, int(self._screen_h * 0.20)))

        self.player = Wrestler("YOU", True)
        self.cpu = Wrestler("CPU", False)
        self.turn = "player"  # "player" | "cpu"
        self.game_over = False
        self._player_bonus_available = False  # legacy (Phase 2 no longer uses momentum)
        self._in_grapple_followup_picker = False
        self._last_turn_banner: str | None = None
        self._after_ids: list[str] = []

        # Phase 2: card/clash state
        self.selected_move_name: str | None = None
        self._selected_card_idxs: set[int] = set()
        self._hand_selecting: bool = False
        self._survival_mode: dict | None = None
        self._survival_labels: dict[str, tk.Label] = {}

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
        # Center content is packed AFTER the bottom Hand so the Hand always
        # reserves screen space (pack order matters on some mobile/HiDPI builds).
        self.center_frame = tk.Frame(self.root, bg="#101010")

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
        # NOTE: Text.scan_dragto differs from Canvas.scan_dragto; Text expects (x, y).
        self.log_text.bind("<B1-Motion>", lambda e: self.log_text.scan_dragto(e.x, e.y))

        # Log coloring
        self.log_text.tag_configure("you", foreground="#67ff8a", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("cpu", foreground="#5aa7ff", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("move", foreground="#ffd166", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("dmg", foreground="#ff6b6b")
        self.log_text.tag_configure("grit", foreground="#c77dff")
        self.log_text.tag_configure("sys", foreground="#cccccc")

        # Moves / context menu (bigger + scrollable)
        # NOTE: We pack the bottom Hand bar *before* packing this frame.
        # Tk's pack geometry allocates space in pack order; if a big expand=True
        # widget is packed first, later bottom widgets can end up clipped.
        self.moves_frame = tk.Frame(self.center_frame, bg="#101010")
        self.moves_title = tk.Label(
            self.moves_frame,
            text="Moves",
            font=("Arial", 10, "bold"),
            fg="#f2f2f2",
            bg="#101010",
        )
        self.moves_title.pack(anchor="w", pady=(0, 6))
        # Scrollable move area so options never get cut off.
        # Do not hard-code height; let it flex with the window.
        self.moves_canvas = tk.Canvas(self.moves_frame, bg="#101010", highlightthickness=0)
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

        # Scrollable modal content so embedded minigames/buttons can't fall below
        # the visible area on small screens.
        self.modal_canvas = tk.Canvas(self.modal_body, bg="#0b0b0b", highlightthickness=0)
        self.modal_scroll = tk.Scrollbar(self.modal_body, orient="vertical", command=self.modal_canvas.yview)
        self.modal_canvas.configure(yscrollcommand=self.modal_scroll.set)
        self.modal_scroll.pack(side="right", fill="y")
        self.modal_canvas.pack(side="left", fill="both", expand=True)

        # Inner content area for embedded modals.
        self.modal_content = tk.Frame(self.modal_canvas, bg="#0b0b0b")
        self._modal_window_id = self.modal_canvas.create_window((0, 0), window=self.modal_content, anchor="nw")

        def on_modal_content_configure(_e: tk.Event) -> None:
            try:
                self.modal_canvas.configure(scrollregion=self.modal_canvas.bbox("all"))
            except tk.TclError:
                return

        def on_modal_canvas_configure(e: tk.Event) -> None:
            try:
                self.modal_canvas.itemconfigure(self._modal_window_id, width=e.width)
            except tk.TclError:
                return

        self.modal_content.bind("<Configure>", on_modal_content_configure)
        self.modal_canvas.bind("<Configure>", on_modal_canvas_configure)

        def on_modal_mousewheel(e: tk.Event) -> None:
            try:
                self.modal_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except tk.TclError:
                return

        self.modal_canvas.bind_all("<MouseWheel>", on_modal_mousewheel)
        self.modal_canvas.bind("<ButtonPress-1>", lambda e: self.modal_canvas.scan_mark(e.x, e.y))
        self.modal_canvas.bind("<B1-Motion>", lambda e: self.modal_canvas.scan_dragto(e.x, e.y, 1))

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

        # ------------------------------------------------------------------
        # Hand (Phase 2 card engine)
        # ------------------------------------------------------------------
        self.hand_frame = tk.Frame(self.root, bg="#000", height=self._hand_h_collapsed, bd=2, relief="ridge")
        # Pack early so it's always visible.
        self.hand_frame.pack(fill="x", side="bottom", padx=8, pady=(0, self._safe_bottom))
        self.hand_frame.pack_propagate(False)

        top_row = tk.Frame(self.hand_frame, bg="#000")
        top_row.pack(fill="x")
        self.hand_hint = tk.Label(
            top_row,
            text="Pick a move above.",
            fg="#aaa",
            bg="#000",
            font=("Arial", 9, "bold"),
        )
        self.hand_hint.pack(side="left")
        self.deck_label = tk.Label(
            top_row,
            text="",
            fg="#aaa",
            bg="#000",
            font=("Arial", 9),
        )
        self.deck_label.pack(side="right")

        self.cards_row = tk.Frame(self.hand_frame, bg="#000")
        self.cards_row.pack(fill="x", expand=True)

        self.card_widgets: list[dict] = []
        for i in range(5):
            border = tk.Frame(self.cards_row, bg="#222", bd=2, relief="flat")
            border.pack(side="left", expand=True, fill="both", padx=3, pady=3)
            lbl = tk.Label(border, text="", bg="#111", fg="#f2f2f2", font=("Impact", 12))
            lbl.pack(fill="both", expand=True)
            border.bind("<Button-1>", lambda _e, idx=i: self._on_card_click(idx))
            lbl.bind("<Button-1>", lambda _e, idx=i: self._on_card_click(idx))
            self.card_widgets.append({"frame": border, "label": lbl, "selected": False})

        self.submit_btn = tk.Button(
            top_row,
            text="SUBMIT",
            font=("Arial", 10, "bold"),
            bg="#44ff44",
            fg="#000",
            activebackground="#66ff66",
            activeforeground="#000",
            command=self._submit_cards,
            state="disabled",
        )
        # Only shown while selecting cards.
        self.submit_btn.pack_forget()

        # Pack center AFTER the hand so the hand can't be pushed off-screen.
        self.center_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Now pack the moves frame so it uses the remaining space above the hand.
        self.moves_frame.pack(fill="both", expand=True, pady=(0, 8))

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
        # Keep it above the phone nav-bar safe area.
        self.sys_btn.place(x=6, y=-(self._safe_bottom + 6), anchor="sw", relx=0.0, rely=1.0)

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

        self.selected_move_name = None
        self._selected_card_idxs = set()
        self._hand_selecting = False
        self._survival_mode = None
        self._survival_labels = {}

        # Ensure HUD bars match new wrestler caps.
        self.p_grit.configure(maximum=self.player.max_grit)
        self.c_grit.configure(maximum=self.cpu.max_grit)

        self._clear_log()
        self._log("Match restarted. Win only by Pinfall or Submission.")
        self._update_hud()
        self._refresh_hand_ui()
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
        for w in list(self.modal_content.winfo_children()):
            w.destroy()
        try:
            self.modal_canvas.yview_moveto(0.0)
        except tk.TclError:
            pass
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

        p_str = f"Str {self.player.strength_current()}/{self.player.strength_max()}"
        c_str = f"Str {self.cpu.strength_current()}/{self.cpu.strength_max()}"
        self.p_nums.config(text=f"HP {self.player.hp}/{MAX_HEALTH}  |  Grit {self.player.grit}/{self.player.max_grit}  |  Hype {self.player.hype}/100  |  {p_str}")
        self.c_nums.config(text=f"HP {self.cpu.hp}/{MAX_HEALTH}  |  Grit {self.cpu.grit}/{self.cpu.max_grit}  |  Hype {self.cpu.hype}/100  |  {c_str}")

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

        # Phase 2: don't hard-restrict defender choices to a single legacy move.

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

        if self.game_over:
            return

        if self._survival_mode is not None:
            return

        moves_to_show = self._available_moves(self.player, self.cpu)
        if len(moves_to_show) == 0:
            moves_to_show = ["Rest"]

        max_buttons = 16
        moves_to_show = moves_to_show[:max_buttons]

        # In Phase 2, player can change the selected move while picking cards.
        # (We keep moves disabled only during survival mode.)
        disable_moves = bool(self._survival_mode is not None)
        for idx, name in enumerate(moves_to_show):
            move = MOVES[name]
            dmg = int(move["damage"])
            mtype = str(move.get("type", ""))
            label = f"{name}\n{mtype}"
            if dmg > 0:
                label += f" | {dmg}"

            is_selected = (self.selected_move_name == name)
            bg = "#3a3a5a" if is_selected else "#2f2f2f"
            fg = MOVE_TYPE_FG.get(mtype, "#f2f2f2")
            disabled_fg = "#666" if disable_moves else fg

            r, c = divmod(idx, 2)
            btn = tk.Button(
                self.moves_grid,
                text=label,
                height=2,
                font=("Arial", 10, "bold"),
                bg=bg,
                fg=fg,
                disabledforeground=disabled_fg,
                activebackground="#444",
                activeforeground="#fff",
                command=lambda n=name: self._select_move(n),
                state=("disabled" if disable_moves else "normal"),
            )
            btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

    # --- Phase 2: Card UI / Clash flow ---
    def _set_hand_selecting(self, selecting: bool, *, hint: str | None = None) -> None:
        self._hand_selecting = bool(selecting)
        if hint is None:
            hint = "Pick a move above." if not selecting else "Select a card." 
        try:
            self.hand_hint.config(text=hint)
        except tk.TclError:
            pass

        if selecting:
            try:
                self.hand_frame.config(height=self._hand_h_expanded)
            except tk.TclError:
                pass
            if not self.submit_btn.winfo_ismapped():
                try:
                    self.deck_label.pack_forget()
                except tk.TclError:
                    pass
                self.submit_btn.pack(side="right", padx=6, pady=6)
                try:
                    self.deck_label.pack(side="right")
                except tk.TclError:
                    pass
        else:
            try:
                self.hand_frame.config(height=self._hand_h_collapsed)
            except tk.TclError:
                pass
            try:
                self.submit_btn.pack_forget()
            except tk.TclError:
                pass
            # Ensure deck label is visible on the right.
            try:
                if not self.deck_label.winfo_ismapped():
                    self.deck_label.pack(side="right")
            except tk.TclError:
                pass
            self._selected_card_idxs = set()
            for w in getattr(self, "card_widgets", []):
                w["selected"] = False
            try:
                self.submit_btn.config(state="disabled")
            except tk.TclError:
                pass

        self._refresh_hand_ui()

    def _refresh_hand_ui(self) -> None:
        # Defensive: ensure the hand is actually populated before rendering.
        try:
            self.player.draw_to_full()
        except Exception:
            pass
        hand = list(self.player.hand or [])
        for i, widget in enumerate(self.card_widgets):
            frame: tk.Frame = widget["frame"]
            label: tk.Label = widget["label"]
            if i < len(hand):
                card = hand[i]
                fg = HEX_COLORS.get(card.color, "#777777")
                selected = i in self._selected_card_idxs
                border = "#ffffff" if selected else "#222"
                frame.config(bg=border)
                label.config(text=str(card.value), fg=fg, bg="#111", font=("Impact", 18 if self._hand_selecting else 12))
            else:
                frame.config(bg="#000")
                label.config(text="", bg="#000")

        try:
            self.deck_label.config(
                text=(
                    f"Deck: {self.player.deck_remaining()}"
                    f"  |  Str: {self.player.strength_current()}/{self.player.strength_max()}"
                    f"  |  Grit: {self.player.grit}/{self.player.max_grit}"
                )
            )
        except tk.TclError:
            pass

        self._update_submit_state()

    def _select_move(self, move_name: str) -> None:
        if self.game_over:
            return
        if self._survival_mode is not None:
            return

        # Special case: Lock Up is the only remaining "minigame" action.
        # It resolves immediately and sets grapple control.
        if move_name == "Lock Up":
            self.selected_move_name = None
            self._selected_card_idxs = set()
            self._set_hand_selecting(False)
            self._refresh_player_buttons()

            hand_was_mapped = bool(self.hand_frame.winfo_ismapped())
            if hand_was_mapped:
                try:
                    self.hand_frame.pack_forget()
                except tk.TclError:
                    hand_was_mapped = False
            self._show_modal("Lock Up")
            try:
                player_won = lockup_minigame(
                    self.root,
                    title="Lock Up",
                    prompt="PUSH or HOLD to win control.",
                    host=self.modal_content,
                )
            finally:
                self._hide_modal()
                if hand_was_mapped:
                    try:
                        self.hand_frame.pack(fill="x", side="bottom", padx=8, pady=(0, self._safe_bottom))
                    except tk.TclError:
                        pass

            if bool(player_won):
                self._log("You win the lock up and take control!")
                self.player.set_state(WrestlerState.GRAPPLE_WEAK)
                self.cpu.set_state(WrestlerState.GRAPPLE_WEAK)
                self.player.grapple_role = GrappleRole.OFFENSE
                self.cpu.grapple_role = GrappleRole.DEFENSE
            else:
                self._log("CPU wins the lock up and takes control!")
                self.player.set_state(WrestlerState.GRAPPLE_WEAK)
                self.cpu.set_state(WrestlerState.GRAPPLE_WEAK)
                self.player.grapple_role = GrappleRole.DEFENSE
                self.cpu.grapple_role = GrappleRole.OFFENSE

            self._update_hud()
            self._refresh_player_buttons()
            return

        self.selected_move_name = move_name
        self._selected_card_idxs = set()
        for w in getattr(self, "card_widgets", []):
            w["selected"] = False

        # If already selecting, treat this as "change move" rather than stacking selections.
        if self._hand_selecting:
            self._log_parts([("Move changed: ", "sys"), (move_name, "move")])
        else:
            self._log_parts([("Selected move: ", "sys"), (move_name, "move")])

        self._set_hand_selecting(True, hint=f"Pick 1 card (or doubles) for {move_name}.")
        self._refresh_player_buttons()

    def _on_card_click(self, index: int) -> None:
        if self.game_over:
            return

        # Cards are only clickable while selecting for a clash or during survival mode.
        if not self._hand_selecting and self._survival_mode is None:
            return

        hand = list(self.player.hand or [])
        if index < 0 or index >= len(hand):
            return

        if index in self._selected_card_idxs:
            self._selected_card_idxs.remove(index)
        else:
            self._selected_card_idxs.add(index)

        # Enforce selection rules: max 2; 2 must be doubles.
        if len(self._selected_card_idxs) > 2:
            # Remove the most recent add.
            self._selected_card_idxs.remove(index)
            self._log("Max 2 cards.")
        elif len(self._selected_card_idxs) == 2:
            i1, i2 = sorted(self._selected_card_idxs)
            if hand[i1].value != hand[i2].value:
                # Not doubles; undo.
                self._selected_card_idxs.remove(index)
                self._log("Two cards must be doubles (same value).")

        self._refresh_hand_ui()

    def _update_submit_state(self) -> None:
        # Hidden button doesn't need state updates.
        if not self.submit_btn.winfo_ismapped():
            return

        if self._survival_mode is not None:
            enabled = len(self._selected_card_idxs) in {1, 2}
        else:
            enabled = bool(self.selected_move_name) and (len(self._selected_card_idxs) in {1, 2})

        cards = self._selected_player_cards()
        if enabled and cards:
            ignore_cost = (self.selected_move_name == "Rest") and (self._survival_mode is None)
            if not self.player.can_afford_cards(cards, ignore_cost=ignore_cost):
                enabled = False

        self.submit_btn.config(state=("normal" if enabled else "disabled"))

    def _selected_player_cards(self) -> list:
        hand = list(self.player.hand or [])
        idxs = sorted(self._selected_card_idxs)
        cards = [hand[i] for i in idxs if 0 <= i < len(hand)]
        # Enforce doubles-only for 2 cards.
        if len(cards) == 2 and cards[0].value != cards[1].value:
            return []
        return cards

    def _calc_clash_score(self, move_name: str, cards: list) -> int:
        # Doubles rule: if you play 2 matching cards, you get +5 and the base
        # counts the value once (not twice).
        if len(cards) == 2 and int(cards[0].value) == int(cards[1].value):
            base = int(cards[0].value) + 5
        else:
            base = sum(int(c.value) for c in cards)

        move_type = str(MOVES.get(move_name, {}).get("type", "Setup"))
        # Color bonus: +1 when color matches move type.
        # For doubles, treat it as a single play (max 1 bonus).
        if len(cards) == 2 and int(cards[0].value) == int(cards[1].value):
            base += max(int(cards[0].color_bonus(move_type)), int(cards[1].color_bonus(move_type)))
        else:
            base += sum(int(c.color_bonus(move_type)) for c in cards)
        return int(base)

    def _cards_log_suffix(self, cards: list) -> str:
        if not cards:
            return ""
        vals = [str(int(c.value)) for c in cards]
        if len(vals) == 2 and vals[0] == vals[1]:
            return f" (cards {vals[0]}+{vals[1]} DOUBLES)"
        if len(vals) == 2:
            return f" (cards {vals[0]}+{vals[1]})"
        return f" (card {vals[0]})"

    def _cpu_choose_cards(self, *, move_name: str) -> list:
        hand = list(self.cpu.hand or [])
        if not hand:
            return []

        best_cards: list = []
        best_score = -1

        ignore_cost = (move_name == "Rest")

        # Singles.
        for c in hand:
            if self.cpu.can_afford_cards([c], ignore_cost=ignore_cost):
                s = self._calc_clash_score(move_name, [c])
                if s > best_score:
                    best_score = s
                    best_cards = [c]

        # Doubles (pairs with same value).
        by_val: dict[int, list] = {}
        for c in hand:
            by_val.setdefault(int(c.value), []).append(c)
        for v, cs in by_val.items():
            if len(cs) >= 2:
                pair = [cs[0], cs[1]]
                if self.cpu.can_afford_cards(pair, ignore_cost=ignore_cost):
                    s = self._calc_clash_score(move_name, pair)
                    if s > best_score:
                        best_score = s
                        best_cards = pair

        if best_cards:
            return best_cards

        # Fallback: play the lowest card.
        hand.sort(key=lambda c: c.value)
        return [hand[0]]

    def _submit_cards(self) -> None:
        if self.game_over:
            return

        # Survival mode takes priority.
        if self._survival_mode is not None:
            if bool(self._survival_mode.get("defender_is_player")):
                self._survival_submit()
            return

        if not self.selected_move_name:
            self._log("Pick a move first.")
            return

        # Re-validate legality at submit time (states can change between selection
        # and resolution on some flows like Lock Up / grapple transitions).
        if not self._move_is_legal(self.selected_move_name, self.player, self.cpu):
            self._log(f"{self.selected_move_name} is no longer legal. Pick a different move.")
            self.selected_move_name = None
            self._selected_card_idxs = set()
            self._set_hand_selecting(False)
            self._refresh_player_buttons()
            return

        p_cards = self._selected_player_cards()
        if not p_cards:
            self._log("Select 1 card (or doubles).")
            return

        ignore_p_cost = (self.selected_move_name == "Rest")
        if not self.player.can_afford_cards(p_cards, ignore_cost=ignore_p_cost):
            self._log("Not enough grit to play those card(s).")
            return

        p_move = str(self.selected_move_name)
        c_move = self._cpu_choose_move()
        c_cards = self._cpu_choose_cards(move_name=c_move)
        ignore_c_cost = (c_move == "Rest")
        if c_cards and (not self.cpu.can_afford_cards(c_cards, ignore_cost=ignore_c_cost)):
            # Should be rare; degrade to single lowest.
            self.cpu.hand.sort(key=lambda c: c.value)
            c_cards = [self.cpu.hand[0]] if self.cpu.hand else []

        p_score = self._calc_clash_score(p_move, p_cards)
        c_score = self._calc_clash_score(c_move, c_cards)

        self._log_parts(
            [("YOU ", "you"), (p_move, "move"), (f" [{p_score}]", "sys"), (self._cards_log_suffix(p_cards), "sys")]
        )
        self._log_parts(
            [("CPU ", "cpu"), (c_move, "move"), (f" [{c_score}]", "sys"), (self._cards_log_suffix(c_cards), "sys")]
        )

        # Tie resolution:
        # 1) Higher remaining deck strength wins
        # 2) If also tied, run the PUSH/HOLD tie-break.
        if p_score == c_score:
            p_str = self.player.strength_current()
            c_str = self.cpu.strength_current()
            if p_str != c_str:
                if p_str > c_str:
                    self._log(f"TIE on score; YOU win by higher remaining strength ({p_str}>{c_str}).")
                    winner, loser = self.player, self.cpu
                    w_move, w_cards, w_score = p_move, p_cards, p_score
                else:
                    self._log(f"TIE on score; CPU wins by higher remaining strength ({c_str}>{p_str}).")
                    winner, loser = self.cpu, self.player
                    w_move, w_cards, w_score = c_move, c_cards, c_score
            else:
                # Hide the hand during the tie-break so PUSH/HOLD can't be covered.
                self._set_hand_selecting(False)
                hand_was_mapped = bool(self.hand_frame.winfo_ismapped())
                if hand_was_mapped:
                    try:
                        self.hand_frame.pack_forget()
                    except tk.TclError:
                        hand_was_mapped = False
                self._show_modal("Tie Break")
                try:
                    player_won = lockup_minigame(
                        self.root,
                        title="Tie Break",
                        prompt="TIE! PUSH or HOLD to win the clash.",
                        host=self.modal_content,
                    )
                finally:
                    self._hide_modal()
                    if hand_was_mapped:
                        try:
                            self.hand_frame.pack(fill="x", side="bottom", padx=8, pady=(0, self._safe_bottom))
                        except tk.TclError:
                            pass
                if bool(player_won):
                    winner, loser = self.player, self.cpu
                    w_move, w_cards, w_score = p_move, p_cards, p_score
                else:
                    winner, loser = self.cpu, self.player
                    w_move, w_cards, w_score = c_move, c_cards, c_score
        elif p_score > c_score:
            winner, loser = self.player, self.cpu
            w_move, w_cards, w_score = p_move, p_cards, p_score
        else:
            winner, loser = self.cpu, self.player
            w_move, w_cards, w_score = c_move, c_cards, c_score

        # Apply card-driven grit + discard/draw for both sides.
        self.player.apply_grit_from_cards(p_cards, ignore_cost=ignore_p_cost)
        self.player.discard_cards(p_cards)
        self.player.draw_to_full()

        self.cpu.apply_grit_from_cards(c_cards, ignore_cost=ignore_c_cost)
        self.cpu.discard_cards(c_cards)
        self.cpu.draw_to_full()

        # Execute the winning move.
        self._execute_move(attacker=winner, defender=loser, move_name=w_move, allow_reaction=False, clash_score=w_score)

        # Utility moves that should still resolve when the winner did not deal damage
        # (e.g., you should be able to stand up while the opponent taunts).
        always_resolve = {"Rest", "Taunt", "Kip-up", "Slow Stand Up"}
        winner_damage = int(MOVES.get(w_move, {}).get("damage", 0))

        if winner_damage <= 0:
            if winner is self.player:
                loser_move_name = c_move
                loser_attacker = self.cpu
                loser_defender = self.player
            else:
                loser_move_name = p_move
                loser_attacker = self.player
                loser_defender = self.cpu

            if loser_move_name in always_resolve and self._move_is_legal(loser_move_name, loser_attacker, loser_defender):
                self._execute_move(attacker=loser_attacker, defender=loser_defender, move_name=loser_move_name, allow_reaction=False)

        # Reset UI for next clash.
        self.selected_move_name = None
        self._selected_card_idxs = set()
        self._set_hand_selecting(False)
        self._refresh_hand_ui()
        self._update_hud()
        self._refresh_player_buttons()

    # --- Finish / survival rules ---
    def _finisher_requirement(self, victim_hp_pct: float) -> int:
        # 100% HP -> 15 (needs very strong control)
        # 0% HP -> 6
        v = 6 + int(round(9.0 * max(0.0, min(1.0, victim_hp_pct))))
        return max(6, min(15, int(v)))

    def _escape_threshold(self, victim_hp_pct: float) -> int:
        # 100% HP -> 1 (easy escape)
        # 0% HP -> 20 (hard escape)
        v = 1 + int(round(19.0 * (1.0 - max(0.0, min(1.0, victim_hp_pct)))))
        return max(1, min(20, int(v)))

    def _begin_survival(self, *, attacker: Wrestler, defender: Wrestler, kind: str) -> None:
        threshold = self._escape_threshold(defender.hp_pct())
        self._survival_mode = {
            "kind": kind,
            "threshold": threshold,
            "total": 0,
            "tries_left": 3,
            "attacker_is_player": bool(attacker.is_player),
            "defender_is_player": bool(defender.is_player),
        }

        if defender.is_player:
            title = "Kick Out!" if kind == "PINFALL" else "Escape!"
            self._show_modal(title)
            self._survival_labels = {}
            tk.Label(
                self.modal_content,
                text=f"{title} Discard cards to reach the escape total.",
                fg="#f2f2f2",
                bg="#0b0b0b",
                font=("Arial", 11, "bold"),
                justify="left",
                anchor="w",
            ).pack(fill="x", pady=(0, 6))

            self._survival_labels["status"] = tk.Label(
                self.modal_content,
                text="",
                fg="#aaa",
                bg="#0b0b0b",
                font=("Arial", 10),
                justify="left",
                anchor="w",
            )
            self._survival_labels["status"].pack(fill="x", pady=(0, 6))

            tk.Label(
                self.modal_content,
                text="Pick 1 card (or doubles), then press SUBMIT. You redraw after each play.",
                fg="#aaa",
                bg="#0b0b0b",
                font=("Arial", 9),
                justify="left",
                anchor="w",
                wraplength=420,
            ).pack(fill="x")

            self._update_survival_labels()
            self._refresh_player_buttons()
            self._set_hand_selecting(True, hint=f"{title} Select cards to escape.")
        else:
            # CPU defending: simulate instantly.
            success = self._cpu_survival(defender=defender, threshold=threshold)
            if success:
                self._log(f"CPU survives the {kind.lower()} attempt!")
                self._survival_mode = None
                self._survival_labels = {}
            else:
                self._end_match("YOU", kind)

    def _update_survival_labels(self) -> None:
        if not self._survival_mode:
            return
        if "status" not in self._survival_labels:
            return
        t = int(self._survival_mode["threshold"])
        total = int(self._survival_mode["total"])
        tries = int(self._survival_mode["tries_left"])
        self._survival_labels["status"].config(text=f"Escape Total: {total}/{t}   |   Tries left: {tries}")

    def _survival_submit(self) -> None:
        if not self._survival_mode:
            return
        cards = self._selected_player_cards()
        if not cards:
            self._log("Select 1 card (or doubles).")
            return
        if not self.player.can_afford_cards(cards):
            self._log("Not enough grit to play those card(s).")
            return

        gained = sum(int(c.value) for c in cards)
        self.player.apply_grit_from_cards(cards)
        self.player.discard_cards(cards)
        self.player.draw_to_full()

        self._survival_mode["total"] = int(self._survival_mode["total"]) + int(gained)
        self._survival_mode["tries_left"] = int(self._survival_mode["tries_left"]) - 1

        self._selected_card_idxs = set()
        for w in getattr(self, "card_widgets", []):
            w["selected"] = False
        self._refresh_hand_ui()

        if int(self._survival_mode["total"]) >= int(self._survival_mode["threshold"]):
            kind = str(self._survival_mode.get("kind", "PINFALL"))
            self._log(f"You survive the {kind.lower()} attempt!")
            self._survival_mode = None
            self._survival_labels = {}
            self._hide_modal()
            self._set_hand_selecting(False)
            self._refresh_player_buttons()
            return

        if int(self._survival_mode["tries_left"]) <= 0:
            kind = str(self._survival_mode.get("kind", "PINFALL"))
            self._end_match("CPU", kind)
            return

        self._update_survival_labels()
        self._set_hand_selecting(True)

    def _cpu_survival(self, *, defender: Wrestler, threshold: int) -> bool:
        total = 0
        tries = 3
        while tries > 0:
            tries -= 1
            defender.draw_to_full()
            hand = list(defender.hand or [])
            if not hand:
                break

            # Choose best single or doubles by value while respecting grit.
            best_cards: list = []
            best_sum = -1
            for c in hand:
                if defender.can_afford_cards([c]) and int(c.value) > best_sum:
                    best_sum = int(c.value)
                    best_cards = [c]

            by_val: dict[int, list] = {}
            for c in hand:
                by_val.setdefault(int(c.value), []).append(c)
            for v, cs in by_val.items():
                if len(cs) >= 2:
                    pair = [cs[0], cs[1]]
                    if defender.can_afford_cards(pair) and (2 * v) > best_sum:
                        best_sum = 2 * v
                        best_cards = pair

            if not best_cards:
                best_cards = [hand[0]]

            total += sum(int(c.value) for c in best_cards)
            defender.apply_grit_from_cards(best_cards)
            defender.discard_cards(best_cards)
            defender.draw_to_full()

            if total >= int(threshold):
                return True
        return False

    # --- Turn flow ---
    def _start_turn(self, who: str) -> None:
        if self.game_over:
            return
        # Phase 2: player always initiates the clash; CPU responds instantly.
        self.turn = "player"

        # Draw hands back to 5 for both sides.
        self.player.draw_to_full()
        self.cpu.draw_to_full()

        # Clear any previous selection.
        self.selected_move_name = None
        self._selected_card_idxs = set()
        self._set_hand_selecting(False)

        # Round banner.
        banner = "CLASH"
        if self._last_turn_banner != banner:
            self._last_turn_banner = banner
            self._log("".ljust(34, "-"))
            self._log_parts([("NEW CLASH", "move")])

        self._refresh_hand_ui()
        self._update_hud()
        self._refresh_player_buttons()

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
        if not options:
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

            if name == "Fight For Control" and self.cpu.is_in_grapple():
                base += 5.0
            if t == "Pin" and self.player.state == WrestlerState.GROUNDED:
                base += 25.0 * (1.0 - self.player.hp_pct())
            if t == "Submission" and self.player.state == WrestlerState.GROUNDED:
                base += 20.0 * (1.0 - self.player.hp_pct())
            if mv.get("set_target_state") == "GROUNDED":
                base += 6.0
            if mv.get("set_target_state") == "RUNNING":
                base += 3.0
            # Add small randomness so it doesn't play identical.
            return base + random.random() * 1.5

        options.sort(key=score, reverse=True)
        return options[0]

    def _cpu_take_turn(self) -> None:
        # Phase 2: CPU does not take a separate timed turn.
        # The CPU response is resolved instantly during `_submit_cards`.
        return

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

            # Phase 2: reaction interrupts are not used.
            # Keep the dialog manual-only if reached.

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
    def _execute_move(
        self,
        *,
        attacker: Wrestler,
        defender: Wrestler,
        move_name: str,
        allow_reaction: bool = True,
        clash_score: int | None = None,
    ) -> bool:
        """Execute the move's effects.

        Phase 2: clash/cards determine who executes a move; move DB 'cost' is ignored.
        Old QTE/reaction minigames are disabled (lockup push/hold is used only as a tie-break).
        """
        if self.game_over:
            return False

        if move_name != "Rest" and not self._move_is_legal(move_name, attacker, defender):
            self._log(f"{attacker.name} tried {move_name}, but it wasn't legal.")
            return False

        move = MOVES[move_name]
        mtype = str(move.get("type", "Setup"))
        attacker_tag = "you" if attacker.is_player else "cpu"

        self._log_parts(
            [
                (attacker.name, attacker_tag),
                (" uses ", "sys"),
                (move_name, "move"),
                ("! ", "sys"),
                (str(move.get("flavor_text", "")), "sys"),
            ]
        )

        # Utility moves
        if move_name == "Rest":
            before = attacker.grit
            attacker.grit = min(attacker.max_grit, attacker.grit + 2)
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

        if move_name == "Fight For Control":
            if attacker.is_in_grapple() and defender.is_in_grapple():
                attacker.grapple_role = GrappleRole.OFFENSE
                defender.grapple_role = GrappleRole.DEFENSE
                self._log_parts([(attacker.name, attacker_tag), (" secures the better position!", "sys")])
            else:
                self._log_parts([(attacker.name, attacker_tag), (" reaches for control, but there's no tie-up.", "sys")])
            self._update_hud()
            return False

        if move_name == "Slow Stand Up":
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

        # Pin/Submission trigger the Survival Loop (3 plays, redraw after each play).
        if mtype in {"Pin", "Submission"}:
            needed = self._finisher_requirement(defender.hp_pct())
            had = int(clash_score or 0)
            if had < needed:
                self._log(f"Not enough control to finish (need {needed}, had {had}).")
                self._update_hud()
                return False

            kind = "PINFALL" if mtype == "Pin" else "SUBMISSION"
            self._begin_survival(attacker=attacker, defender=defender, kind=kind)
            self._update_hud()
            return False

        # Damage
        raw_damage = int(move.get("damage", 0))
        if raw_damage > 0:
            defender.take_damage(raw_damage, target_part=str(move.get("target_part", "BODY")))
            dtag = "you" if defender.is_player else "cpu"
            self._log_parts([(defender.name, dtag), (" takes ", "sys"), (f"{raw_damage}", "dmg"), (" damage.", "sys")])

        # Hype
        attacker.add_hype(int(move.get("hype_gain", 0)))

        # State transitions
        if "set_user_state" in move:
            attacker.set_state(WrestlerState(move["set_user_state"]))
        if "set_target_state" in move:
            defender.set_state(WrestlerState(move["set_target_state"]))

        # Grapple roles: when both are in a grapple tier, attacker is offense.
        if attacker.is_in_grapple() and defender.is_in_grapple():
            attacker.grapple_role = GrappleRole.OFFENSE
            defender.grapple_role = GrappleRole.DEFENSE

        self._clear_grapple_roles_if_exited(attacker, defender)

        if defender.hp == 0:
            self._log(f"{defender.name} is exhausted (0 HP) — very vulnerable to Pin/Submission.")

        self._update_hud()
        return False


if __name__ == "__main__":
    root = tk.Tk()
    app = TacticalWrestlingApp(root)
    root.mainloop()
