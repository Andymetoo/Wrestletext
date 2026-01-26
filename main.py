from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk

from mechanics import pin_minigame, submission_minigame
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
        self.log_text = tk.Text(
            log_frame,
            bg="#000",
            fg="#b6ffb6",
            font=("Consolas", 11),
            height=12,
            state="disabled",
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True)

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
        self.moves_grid = tk.Frame(self.moves_frame, bg="#101010")
        self.moves_grid.pack(fill="x")
        self.moves_grid.columnconfigure(0, weight=1)
        self.moves_grid.columnconfigure(1, weight=1)

    def _log(self, msg: str) -> None:
        if self.game_over:
            return
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"> {msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

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

        max_buttons = 8
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
                height=3,
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
            self._log(f"{active.name} regains {gained} Grit.")

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
        """Returns {damage:int, negated:bool, reversed:bool, reversal_damage:int}."""
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

        result = {"chosen": False, "damage": incoming_damage, "negated": False, "reversed": False, "reversal_damage": 0}

        def choose_brace() -> None:
            if result["chosen"]:
                return
            result["chosen"] = True
            result["damage"] = int((incoming_damage + 1) // 2)
            top.destroy()

        def choose_dodge() -> None:
            if result["chosen"]:
                return
            if not self.player.spend_grit(2):
                return
            result["chosen"] = True
            if random.random() < 0.5:
                result["damage"] = 0
                result["negated"] = True
            top.destroy()

        def choose_reversal() -> None:
            if result["chosen"]:
                return
            if not self.player.spend_grit(4):
                return
            result["chosen"] = True
            if random.random() < 0.3:
                result["damage"] = 0
                result["negated"] = True
                result["reversed"] = True
                result["reversal_damage"] = max(1, int(incoming_damage * 0.8))
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
        top.wait_window()
        return result

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

        self._log(f"{attacker.name} uses {move_name}! {move['flavor_text']}")

        # Rest is special: high regen.
        if move_name == "Rest":
            bonus = 5
            before = attacker.grit
            attacker.grit = min(attacker.max_grit, attacker.grit + bonus)
            self._log(f"{attacker.name} recovers (+{attacker.grit - before} Grit).")
            self._update_hud()
            return

        mtype = move["type"]

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
                    prompt="Finish it! Guess the secret number.",
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
                    prompt="Escape! Guess the secret number before you tap.",
                    victim_hp_pct=defender.hp_pct(),
                )
                if ok:
                    self._log("You escaped the submission!")
                else:
                    self._end_match("CPU", "SUBMISSION")
            self._update_hud()
            return

        raw_damage = int(move["damage"])
        negated = False

        # Fluid Momentum: Player gets a reaction menu when CPU attacks.
        if (not attacker.is_player) and raw_damage > 0:
            reaction = self._reaction_menu(raw_damage)
            self._update_hud()
            dmg = int(reaction["damage"])
            negated = bool(reaction["negated"])
            if dmg == 0:
                if reaction.get("reversed"):
                    self._log("REVERSAL! You turn it around!")
                    self.cpu.take_damage(int(reaction["reversal_damage"]))
                    self._log(f"CPU takes {int(reaction['reversal_damage'])} damage back.")
                else:
                    self._log("You avoid the hit!")
            else:
                self.player.take_damage(dmg)
                self._log(f"You take {dmg} damage.")
        else:
            # Normal damage application (player attacking CPU, or non-damaging CPU move)
            if raw_damage > 0:
                defender.take_damage(raw_damage)
                self._log(f"{defender.name} takes {raw_damage} damage.")

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
