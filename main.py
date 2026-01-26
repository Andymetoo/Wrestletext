from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk

from mechanics import grapple_qte_minigame, lockup_minigame, pin_minigame, submission_minigame
from moves_db import MOVES
from wrestler import MAX_HEALTH, Wrestler, WrestlerState


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

        bars = tk.Frame(self.hud, bg="#1b1b1b")
        bars.pack(fill="x")

        # Player side
        left = tk.Frame(bars, bg="#1b1b1b")
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="YOU", fg="#67ff8a", bg="#1b1b1b", font=("Impact", 10)).pack(anchor="w")
        self.p_hp = ttk.Progressbar(left, maximum=MAX_HEALTH)
        self.p_hp.pack(fill="x", padx=(0, 8))
        self.p_grit = ttk.Progressbar(left, maximum=self.player.max_grit)
        self.p_grit.pack(fill="x", padx=(0, 8), pady=(4, 0))
        self.p_nums = tk.Label(left, text="", fg="#aaa", bg="#1b1b1b", font=("Arial", 9))
        self.p_nums.pack(anchor="w", pady=(2, 0))

        # CPU side
        right = tk.Frame(bars, bg="#1b1b1b")
        right.pack(side="right", fill="x", expand=True)
        tk.Label(right, text="CPU", fg="#ff6b6b", bg="#1b1b1b", font=("Impact", 10)).pack(anchor="e")
        self.c_hp = ttk.Progressbar(right, maximum=MAX_HEALTH)
        self.c_hp.pack(fill="x", padx=(8, 0))
        self.c_grit = ttk.Progressbar(right, maximum=self.cpu.max_grit)
        self.c_grit.pack(fill="x", padx=(8, 0), pady=(4, 0))
        self.c_nums = tk.Label(right, text="", fg="#aaa", bg="#1b1b1b", font=("Arial", 9))
        self.c_nums.pack(anchor="e", pady=(2, 0))

        # Turn label
        self.turn_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 10, "bold"),
            fg="#ffd166",
            bg="#101010",
        )
        self.turn_label.pack(fill="x", padx=8)

        # Log
        log_frame = tk.Frame(self.root, bg="#000", bd=2, relief="sunken")
        log_frame.pack(fill="both", expand=True, padx=8, pady=8)
        log_scroll = tk.Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")
        self.log_text = tk.Text(
            log_frame,
            bg="#000",
            fg="#b6ffb6",
            font=("Consolas", 11),
            height=12,
            state="disabled",
            wrap="word",
            yscrollcommand=log_scroll.set,
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)

        # Log coloring
        self.log_text.tag_configure("you", foreground="#67ff8a", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("cpu", foreground="#5aa7ff", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("move", foreground="#ffd166", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("dmg", foreground="#ff6b6b")
        self.log_text.tag_configure("grit", foreground="#c77dff")
        self.log_text.tag_configure("sys", foreground="#cccccc")

        # Moves / context menu
        self.moves_frame = tk.Frame(self.root, bg="#101010")
        self.moves_frame.pack(fill="x", padx=8, pady=(0, 8))
        self.moves_title = tk.Label(
            self.moves_frame,
            text="Moves",
            font=("Arial", 10, "bold"),
            fg="#f2f2f2",
            bg="#101010",
        )
        self.moves_title.pack(anchor="w", pady=(0, 6))
        # Scrollable move area so options never get cut off.
        self.moves_canvas = tk.Canvas(self.moves_frame, bg="#101010", highlightthickness=0, height=240)
        self.moves_scroll = tk.Scrollbar(self.moves_frame, orient="vertical", command=self.moves_canvas.yview)
        self.moves_canvas.configure(yscrollcommand=self.moves_scroll.set)
        self.moves_scroll.pack(side="right", fill="y")
        self.moves_canvas.pack(side="left", fill="both", expand=True)

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
        self.state_line.config(
            text=f"YOU: {self.player.state.value}  |  CPU: {self.cpu.state.value}"
        )
        self.turn_label.config(text=f"TURN: {'YOU' if self.turn == 'player' else 'CPU'}")

        self.p_hp["value"] = self.player.hp
        self.c_hp["value"] = self.cpu.hp
        self.p_grit["value"] = self.player.grit
        self.c_grit["value"] = self.cpu.grit

        self.p_nums.config(text=f"HP {self.player.hp}/{MAX_HEALTH}  |  Grit {self.player.grit}/{self.player.max_grit}")
        self.c_nums.config(text=f"HP {self.cpu.hp}/{MAX_HEALTH}  |  Grit {self.cpu.grit}/{self.cpu.max_grit}")

    # --- Moves filtering ---
    def _move_is_legal(self, move_name: str, user: Wrestler, target: Wrestler) -> bool:
        move = MOVES[move_name]
        ru = move["req_user_state"]
        rt = move["req_target_state"]
        if ru != "ANY" and ru != user.state.value:
            return False
        if rt != "ANY" and rt != target.state.value:
            return False
        return True

    def _available_moves(self, user: Wrestler, target: Wrestler) -> list[str]:
        names = [n for n in MOVES.keys() if n != "Rest" and self._move_is_legal(n, user, target)]

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

        top = tk.Toplevel(self.root)
        top.title("Choose Grapple")
        top.transient(self.root)
        top.grab_set()
        top.resizable(False, False)

        tk.Label(top, text="Pick a grapple to execute:", font=("Arial", 11, "bold")).pack(padx=12, pady=(12, 8))

        chosen = {"value": None}

        for name in options[:6]:
            mv = MOVES[name]
            cost = int(mv["cost"])
            dmg = int(mv["damage"])
            btn = ttk.Button(
                top,
                text=f"{name} (Cost {cost}, Dmg {dmg})",
                command=lambda n=name: (chosen.__setitem__("value", n), top.destroy()),
            )
            btn.pack(fill="x", padx=12, pady=4)

        ttk.Button(top, text="Cancel", command=top.destroy).pack(fill="x", padx=12, pady=(10, 12))
        self._position_modal_bottom(top, bottom_padding=28)
        top.wait_window()
        return chosen["value"]

    def _refresh_player_buttons(self) -> None:
        for child in list(self.moves_grid.winfo_children()):
            child.destroy()

        if self.game_over or self.turn != "player":
            return

        moves = self._available_moves(self.player, self.cpu)
        affordable = [m for m in moves if MOVES[m]["cost"] <= self.player.grit]
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
            cost = int(move["cost"])
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
            self.root.after(700, self._cpu_take_turn)

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
        self._execute_move(attacker=self.player, defender=self.cpu, move_name=move_name)
        if self.game_over:
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

        self._start_turn("cpu")

    # --- CPU action ---
    def _cpu_choose_move(self) -> str:
        options = self._available_moves(self.cpu, self.player)
        affordable = [m for m in options if MOVES[m]["cost"] <= self.cpu.grit]
        if not affordable:
            return "Rest"

        def score(name: str) -> float:
            mv = MOVES[name]
            base = float(mv["damage"])
            t = mv["type"]
            if t == "Pin" and self.player.state == WrestlerState.GROUNDED:
                base += 25.0 * (1.0 - self.player.hp_pct())
            if t == "Submission" and self.player.state == WrestlerState.GROUNDED:
                base += 20.0 * (1.0 - self.player.hp_pct())
            if mv.get("set_target_state") == "GROUNDED":
                base += 6.0
            if mv.get("set_target_state") == "RUNNING":
                base += 3.0
            # Slightly prefer cheaper moves when low on grit.
            base -= 0.15 * int(mv["cost"])
            # Add small randomness so it doesn't play identical.
            return base + random.random() * 1.5

        affordable.sort(key=score, reverse=True)
        return affordable[0]

    def _cpu_take_turn(self) -> None:
        if self.game_over or self.turn != "cpu":
            return
        move_name = self._cpu_choose_move()
        self._execute_move(attacker=self.cpu, defender=self.player, move_name=move_name)
        if not self.game_over:
            self._start_turn("player")

    # --- Reaction interrupts ---
    def _reaction_menu(self, incoming_damage: int) -> dict:
        """Returns {choice:str}. Choice in {'BRACE','DODGE','REVERSAL'}.

        Grit is spent inside this dialog for DODGE/REVERSAL.
        """
        top = tk.Toplevel(self.root)
        top.title("React!")
        top.transient(self.root)
        top.grab_set()
        top.resizable(False, False)

        tk.Label(
            top,
            text=f"CPU attacks! Incoming damage: {incoming_damage}",
            font=("Arial", 11, "bold"),
        ).pack(padx=12, pady=(12, 6))
        grit_lbl = tk.Label(top, text=f"Your Grit: {self.player.grit}", font=("Arial", 9), fg="#555")
        grit_lbl.pack(padx=12, pady=(0, 10))

        result = {"chosen": False, "choice": "BRACE"}

        def choose_brace() -> None:
            if result["chosen"]:
                return
            result["chosen"] = True
            result["choice"] = "BRACE"
            top.destroy()

        def choose_dodge() -> None:
            if result["chosen"]:
                return
            if not self.player.spend_grit(2):
                return
            result["chosen"] = True
            result["choice"] = "DODGE"
            top.destroy()

        def choose_reversal() -> None:
            if result["chosen"]:
                return
            if not self.player.spend_grit(4):
                return
            result["chosen"] = True
            result["choice"] = "REVERSAL"
            top.destroy()

        btns = tk.Frame(top)
        btns.pack(padx=12, pady=(0, 12), fill="x")

        b1 = ttk.Button(btns, text="Brace (0 Grit) – Take 50%", command=choose_brace)
        b1.pack(fill="x", pady=4)

        b2 = ttk.Button(btns, text="Dodge (2 Grit) – 50% take 0", command=choose_dodge)
        b2.pack(fill="x", pady=4)
        if self.player.grit < 2:
            b2.state(["disabled"])

        b3 = ttk.Button(btns, text="Reversal (4 Grit) – 30% reverse", command=choose_reversal)
        b3.pack(fill="x", pady=4)
        if self.player.grit < 4:
            b3.state(["disabled"])

        top.protocol("WM_DELETE_WINDOW", choose_brace)
        self._position_modal_bottom(top, bottom_padding=28)
        top.wait_window()
        return result

    def _reaction_skill_check(self) -> float:
        """Return a performance score 0..1 based on a random minigame."""
        choice = random.choice(["qte", "lockup", "overunder"])
        if choice == "qte":
            out = grapple_qte_minigame(
                self.root,
                title="React Timing",
                prompt="React! Nail the timing to improve your odds.",
                duration_ms=2600,
            )
            tier = out["tier"]
            if tier == "CRIT":
                return 1.0
            if tier == "HIT":
                return 0.75
            if tier == "WEAK":
                return 0.4
            return 0.0
        if choice == "lockup":
            ok = lockup_minigame(self.root, title="React Struggle", prompt="React! PUSH/HOLD to improve your odds.")
            return 1.0 if ok else 0.0
        ok = submission_minigame(
            self.root,
            title="React Read",
            prompt="React! Call HIGHER/LOWER correctly to improve your odds.",
            victim_hp_pct=self.player.hp_pct(),
        )
        return 1.0 if ok else 0.0

    # --- Core move execution ---
    def _execute_move(self, *, attacker: Wrestler, defender: Wrestler, move_name: str) -> None:
        if self.game_over:
            return

        if move_name != "Rest" and not self._move_is_legal(move_name, attacker, defender):
            self._log(f"{attacker.name} tried {move_name}, but it wasn't legal.")
            return

        move = MOVES[move_name]
        cost = int(move["cost"])
        if not attacker.spend_grit(cost):
            self._log(f"{attacker.name} doesn't have enough Grit for {move_name}.")
            return

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
            return

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
            return

        mtype = move["type"]

        # Lock-up (push/hold) creates a grapple opportunity.
        if move_name == "Lock Up":
            player_won = lockup_minigame(
                self.root,
                title="Lock Up",
                prompt="Tie-up! PUSH or HOLD to fight for position.",
            )

            attacker_won = player_won if attacker.is_player else (not player_won)
            if attacker_won:
                self._log(f"{attacker.name} wins the tie-up!")
                if attacker.is_player:
                    follow = self._choose_grapple_followup(attacker, defender)
                    if follow is None:
                        self._log("No grapple available (or not enough Grit).")
                    else:
                        self._execute_move(attacker=attacker, defender=defender, move_name=follow)
                else:
                    options = [m for m in self._available_grapple_finishes(attacker, defender) if MOVES[m]["cost"] <= attacker.grit]
                    if options:
                        self._execute_move(attacker=attacker, defender=defender, move_name=random.choice(options))
            else:
                self._log(f"{defender.name} fights you off and breaks the tie-up!")

            self._update_hud()
            return

        # Pin / Submission resolve match-ending conditions.
        if mtype == "Pin":
            if attacker.is_player:
                ok = pin_minigame(
                    self.root,
                    title="Pin Attempt",
                    prompt="PIN! Stop the marker in the green window to score the fall.",
                    victim_hp_pct=defender.hp_pct(),
                )
                if ok:
                    self._end_match("YOU", "PINFALL")
                else:
                    self._log("They kicked out!")
            else:
                ok = pin_minigame(
                    self.root,
                    title="Kick Out!",
                    prompt="KICK OUT! Stop the marker in the green window to survive.",
                    victim_hp_pct=defender.hp_pct(),
                )
                if ok:
                    self._log("You kicked out!")
                else:
                    self._end_match("CPU", "PINFALL")
            self._update_hud()
            return

        if mtype == "Submission":
            if attacker.is_player:
                ok = submission_minigame(
                    self.root,
                    title="Submission Attempt",
                    prompt="Finish it! Call HIGHER or LOWER correctly.",
                    victim_hp_pct=defender.hp_pct(),
                )
                if ok:
                    self._end_match("YOU", "SUBMISSION")
                else:
                    self._log("They fought out of the hold!")
            else:
                ok = submission_minigame(
                    self.root,
                    title="Escape Submission!",
                    prompt="Escape! Call HIGHER or LOWER correctly to survive.",
                    victim_hp_pct=defender.hp_pct(),
                )
                if ok:
                    self._log("You escaped the submission!")
                else:
                    self._end_match("CPU", "SUBMISSION")
            self._update_hud()
            return

        # Grapple QTE (player only) – restores the old timing minigame feel.
        if mtype == "Grapple" and attacker.is_player and int(move.get("damage", 0)) > 0:
            outcome = grapple_qte_minigame(
                self.root,
                title="Grapple Timing",
                prompt=f"{move_name}! Hit the timing window.",
            )
            tier = outcome["tier"]
            timing = int(outcome["timing"])
            mult = float(outcome["multiplier"])

            if tier == "BOTCH":
                self._log(f"BOTCH! (Timing {timing}%) You crash and burn!")
                self.player.take_damage(6)
            else:
                final = max(1, int(int(move["damage"]) * mult))
                if tier == "CRIT":
                    self._log(f"PERFECT! (Timing {timing}%)")
                elif tier == "HIT":
                    self._log(f"GOOD HIT! (Timing {timing}%)")
                else:
                    self._log(f"WEAK... (Timing {timing}%)")
                defender.take_damage(final)
                self._log(f"{defender.name} takes {final} damage.")

            # Apply state transitions after QTE resolution if not botched.
            if tier != "BOTCH":
                if "set_user_state" in move:
                    attacker.set_state(WrestlerState(move["set_user_state"]))
                if "set_target_state" in move:
                    defender.set_state(WrestlerState(move["set_target_state"]))

            if defender.hp == 0:
                self._log(f"{defender.name} is exhausted (0 HP) — they're very vulnerable to Pin/Submission.")

            self._update_hud()
            return

        raw_damage = int(move["damage"])
        negated = False

        # Fluid Momentum: Player gets a reaction menu when CPU attacks.
        if (not attacker.is_player) and raw_damage > 0:
            reaction = self._reaction_menu(raw_damage)
            self._update_hud()
            choice = reaction.get("choice", "BRACE")

            if choice == "BRACE":
                dmg = int((raw_damage + 1) // 2)
                self.player.take_damage(dmg)
                self._log_parts([(self.player.name, "you"), (" braces and takes ", "sys"), (f"{dmg}", "dmg"), (" damage.", "sys")])
            elif choice == "DODGE":
                score = self._reaction_skill_check()
                chance = 0.8 if score >= 0.6 else 0.2
                if random.random() < chance:
                    negated = True
                    self._log("You dodge it!")
                else:
                    self.player.take_damage(raw_damage)
                    self._log_parts([(self.player.name, "you"), (" takes ", "sys"), (f"{raw_damage}", "dmg"), (" damage.", "sys")])
            else:  # REVERSAL
                score = self._reaction_skill_check()
                chance = 0.6 if score >= 0.6 else 0.1
                if random.random() < chance:
                    negated = True
                    self._log("REVERSAL! You turn it around!")
                    back = max(1, int(raw_damage * 0.8))
                    self.cpu.take_damage(back)
                    self._log_parts([(self.cpu.name, "cpu"), (" takes ", "sys"), (f"{back}", "dmg"), (" damage back.", "sys")])
                else:
                    self.player.take_damage(raw_damage)
                    self._log_parts([(self.player.name, "you"), (" takes ", "sys"), (f"{raw_damage}", "dmg"), (" damage.", "sys")])
        else:
            # Normal damage application (player attacking CPU, or non-damaging CPU move)
            if raw_damage > 0:
                if move_name == "Desperation Slap" and attacker.is_player and (not defender.is_player):
                    if random.random() < 0.75:
                        self._log_parts([(defender.name, "cpu"), (" easily avoids the lazy shot.", "sys")])
                        raw_damage = 0
                        negated = True

                defender.take_damage(raw_damage)
                dtag = "you" if defender.is_player else "cpu"
                if raw_damage > 0:
                    self._log_parts([(defender.name, dtag), (" takes ", "sys"), (f"{raw_damage}", "dmg"), (" damage.", "sys")])

        # State transitions only happen if the hit wasn't fully negated (dodge/reversal).
        if not negated:
            if move_name == "Possum":
                # Small chance to trip the opponent.
                if random.random() < 0.35:
                    defender.set_state(WrestlerState.GROUNDED)
                    self._log("It worked! They stumble and hit the mat.")

            if "set_user_state" in move:
                attacker.set_state(WrestlerState(move["set_user_state"]))
            if "set_target_state" in move:
                defender.set_state(WrestlerState(move["set_target_state"]))

        # If someone is at 0 HP, it only affects pin/sub difficulty.
        if defender.hp == 0:
            self._log(f"{defender.name} is exhausted (0 HP) — they're very vulnerable to Pin/Submission.")

        self._update_hud()


if __name__ == "__main__":
    root = tk.Tk()
    app = TacticalWrestlingApp(root)
    root.mainloop()
