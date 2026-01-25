import tkinter as tk
from tkinter import messagebox, ttk
import random

# --- CONFIGURATION ---
MAX_HEALTH = 100
MAX_STAMINA = 100

class Wrestler:
    def __init__(self, name, is_player):
        self.name = name
        self.hp = MAX_HEALTH
        self.stamina = MAX_STAMINA
        self.heat_bonus = 0
        self.state = "NEUTRAL"
        self.move_history = [] 

    def record_move(self, move_name):
        self.move_history.append(move_name)
        if len(self.move_history) > 5:
            self.move_history.pop(0)

    def get_stale_penalty(self, move_name):
        count = self.move_history.count(move_name)
        if count == 0: return 0.0
        if count == 1: return 0.1
        if count == 2: return 0.4
        return 0.8

class GameEngine:
    def __init__(self, root):
        self.root = root
        self.root.title("Squared Circle: Definitive V6")
        self.root.geometry("400x850") 
        self.root.configure(bg="#121212")

        self.player = Wrestler("Player", True)
        self.cpu = Wrestler("CPU", False)
        
        self.game_over = False
        
        # QTE Vars
        self.qte_active = False
        self.qte_value = 0
        self.qte_speed = 5
        self.qte_target_move = None

        # Minigame vars
        self.mini_game_score = {"p": 0, "c": 0}
        self.sub_target = 5
        self.banned_numbers = []
        self.escape_attempts = 0

        self.create_widgets()
        self.set_neutral_state()

    def create_widgets(self):
        # --- 1. HUD ---
        self.hud_frame = tk.Frame(self.root, bg="#222", pady=5)
        self.hud_frame.pack(fill="x")

        self.p_stat_frame = tk.Frame(self.hud_frame, bg="#222")
        self.p_stat_frame.pack(side="left", padx=5, fill="x", expand=True)
        tk.Label(self.p_stat_frame, text="YOU", fg="#4f4", bg="#222", font=("Impact", 10)).pack(anchor="w")
        self.p_hp_bar = ttk.Progressbar(self.p_stat_frame, length=100, maximum=MAX_HEALTH)
        self.p_hp_bar.pack(fill="x")
        
        self.state_label = tk.Label(self.hud_frame, text="NEUTRAL", fg="white", bg="#444", font=("Impact", 14))
        self.state_label.pack(side="left", padx=5)

        self.c_stat_frame = tk.Frame(self.hud_frame, bg="#222")
        self.c_stat_frame.pack(side="right", padx=5, fill="x", expand=True)
        tk.Label(self.c_stat_frame, text="CPU", fg="#f44", bg="#222", font=("Impact", 10)).pack(anchor="e")
        self.c_hp_bar = ttk.Progressbar(self.c_stat_frame, length=100, maximum=MAX_HEALTH)
        self.c_hp_bar.pack(fill="x")

        self.heat_label = tk.Label(self.root, text="", fg="orange", bg="#121212", font=("Arial", 10, "bold"))
        self.heat_label.pack()

        # --- 2. LOG ---
        self.log_frame = tk.Frame(self.root, bg="black", bd=2, relief="sunken")
        self.log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text = tk.Text(self.log_frame, bg="black", fg="#0f0", font=("Courier New", 12), state="disabled", height=10)
        self.log_text.pack(fill="both", expand=True)

        # --- 3. QTE BAR ---
        self.qte_frame = tk.Frame(self.root, bg="#222", pady=5)
        self.qte_frame.pack(fill="x", padx=10)
        tk.Label(self.qte_frame, text="TIMING BAR (Hit Green Zone 70-95%)", fg="#888", bg="#222", font=("Arial", 8)).pack()
        self.qte_bar = ttk.Progressbar(self.qte_frame, length=300, maximum=100, mode='determinate')
        self.qte_bar.pack(fill="x")

        # --- 4. CONTROLS ---
        self.control_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.control_frame.pack(fill="x", side="bottom", pady=5, padx=5)
        self.control_frame.columnconfigure(0, weight=1)
        self.control_frame.columnconfigure(1, weight=1)

        self.buttons = {}
        self.create_btn("btn_00", 0, 0)
        self.create_btn("btn_01", 0, 1)
        self.create_btn("btn_10", 1, 0)
        self.create_btn("btn_11", 1, 1)
        self.create_btn("btn_20", 2, 0)
        self.create_btn("btn_21", 2, 1)

    def create_btn(self, name, r, c):
        btn = tk.Button(self.control_frame, text="...", font=("Arial", 10, "bold"), height=3, bg="#333", fg="white")
        btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
        self.buttons[name] = btn

    def log(self, text):
        if self.game_over: return
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"> {text}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def clear_buttons(self):
        if self.game_over: return
        for btn in self.buttons.values():
            btn.config(text="", command=None, state="disabled", bg="#222")

    # ==========================================
    #           QTE SYSTEM (GRAVITY)
    # ==========================================
    def start_qte(self, move_name, damage, speed=5):
        self.player.state = "QTE"
        self.state_label.config(text="TIMING!", bg="#ffffff", fg="black")
        self.log(f"Setting up {move_name}...")
        
        self.qte_active = True
        self.qte_value = 0
        self.qte_speed = speed
        self.qte_target_move = {"name": move_name, "dmg": damage}
        
        self.clear_buttons()
        self.buttons["btn_10"].config(text="!!! EXECUTE !!!", bg="#0f0", fg="black", state="normal", command=self.resolve_qte)
        self.buttons["btn_11"].config(text="!!! EXECUTE !!!", bg="#0f0", fg="black", state="normal", command=self.resolve_qte)

        self.run_qte_loop()

    def run_qte_loop(self):
        if not self.qte_active or self.game_over: return
        self.qte_value += self.qte_speed
        if self.qte_value > 100: self.qte_value = 0
        self.qte_bar['value'] = self.qte_value
        self.root.after(50, self.run_qte_loop)

    def resolve_qte(self):
        self.qte_active = False
        val = self.qte_value
        move = self.qte_target_move
        
        if val > 95:
            self.log(f"BOTCHED! (Timing: {val}%)")
            self.log("You slipped and fell!")
            self.player.hp -= 10
            self.update_ui()
            self.root.after(1500, self.set_neutral_state)
        elif val >= 70:
            crit = int(move['dmg'] * 1.5)
            self.log(f"PERFECT! (Timing: {val}%)")
            self.log(f"CRITICAL HIT! {crit} DMG")
            self.cpu.hp -= crit
            self.update_ui()
            self.root.after(1500, self.set_neutral_state)
        elif val >= 40:
            self.log(f"GOOD HIT (Timing: {val}%)")
            self.cpu.hp -= move['dmg']
            self.update_ui()
            self.root.after(1500, self.set_neutral_state)
        else:
            self.log(f"WEAK... (Timing: {val}%)")
            self.log("They shrugged it off.")
            self.cpu.hp -= int(move['dmg'] / 2)
            self.update_ui()
            self.cpu_attacks_logic()

    # ==========================================
    #           NEUTRAL / OFFENSE STATES
    # ==========================================

    def set_neutral_state(self):
        if self.game_over: return
        self.player.state = "NEUTRAL"
        self.state_label.config(text="NEUTRAL", bg="#555", fg="white")
        self.clear_buttons()
        self.qte_bar['value'] = 0

        self.buttons["btn_00"].config(text="LOCK UP\n(Push Luck)", bg="#44f", fg="white", state="normal", 
                                      command=lambda: self.start_struggle("TIE_UP"))
        
        # Strike Staleness Logic
        penalty = self.player.get_stale_penalty("Strike")
        risk_txt = "Safe" if penalty == 0 else f"Risk {int(penalty*100)}%"
        col = "#a44" if penalty < 0.5 else "#622"
        self.buttons["btn_01"].config(text=f"STRIKE\n({risk_txt})", bg=col, fg="white", state="normal", 
                                      command=self.attempt_strike)
        
        self.buttons["btn_10"].config(text="RUNNING ATK\n(Risk -> Ground)", bg="#a44", fg="white", state="normal", 
                                      command=self.attempt_running_attack)
        self.buttons["btn_11"].config(text="TAUNT\n(+Dmg Buff)", bg="#444", fg="white", state="normal", 
                                      command=self.attempt_taunt)
        self.buttons["btn_20"].config(text="REST\n(+Stamina)", bg="#444", fg="white", state="normal", 
                                      command=lambda: self.log("You circle and breathe..."))

    def player_wins_control(self):
        self.player.state = "CONTROL"
        self.state_label.config(text="IN CONTROL", bg="#0f0", fg="black")
        self.clear_buttons()
        self.qte_bar['value'] = 0
        
        self.buttons["btn_00"].config(text="QUICK STRIKE", bg="#aa0", fg="black", state="normal", 
                                      command=self.attempt_strike)
        self.buttons["btn_01"].config(text="GRAPPLE MOVES", bg="#00a", fg="white", state="normal", 
                                      command=self.set_grapple_menu)

    def set_grapple_menu(self):
        self.log("Select a move to attempt...")
        self.clear_buttons()
        self.buttons["btn_00"].config(text="SUPLEX\n(Dmg 15 | Med)", bg="#a00", fg="white", state="normal", 
                                      command=lambda: self.start_qte("Suplex", 15, speed=5))
        self.buttons["btn_01"].config(text="POWERBOMB\n(Dmg 25 | Fast)", bg="#a00", fg="white", state="normal", 
                                      command=lambda: self.start_qte("Powerbomb", 25, speed=8))
        self.buttons["btn_10"].config(text="PILEDRIVER\n(Dmg 35 | Insane)", bg="#500", fg="white", state="normal", 
                                      command=lambda: self.start_qte("Piledriver", 35, speed=12))
        self.buttons["btn_21"].config(text="CANCEL", bg="#444", fg="white", state="normal", 
                                      command=self.player_wins_control)

    def set_ground_state(self):
        self.player.state = "GROUND"
        self.state_label.config(text="ENEMY DOWN", bg="#880088", fg="white")
        self.clear_buttons()
        self.log("They are down! Finish it!")

        self.buttons["btn_00"].config(text="STOMP\n(Safe)", bg="#aa0", fg="black", state="normal", 
                                      command=lambda: self.resolve_ground_hit(5))
        self.buttons["btn_01"].config(text="ELBOW DROP\n(Risk)", bg="#a44", fg="white", state="normal", 
                                      command=lambda: self.resolve_ground_hit(12, risk=0.4))
        self.buttons["btn_10"].config(text="SUBMISSION\n(Minigame)", bg="#00a", fg="white", state="normal", 
                                      command=self.start_submission_game_offense)
        self.buttons["btn_11"].config(text="PICK UP\n(Reset)", bg="#444", fg="white", state="normal", 
                                      command=self.set_neutral_state)

    # ==========================================
    #           SUBMISSION SYSTEM
    # ==========================================
    def start_submission_game_offense(self):
        self.player.state = "OFFENSE_SUB"
        self.state_label.config(text="SUBMISSION", bg="#0000ff", fg="white")
        self.sub_target = random.randint(2, 9)
        self.banned_numbers = [self.sub_target]
        self.log(f"Applying hold! Pressure: {self.sub_target}")
        self.update_submission_ui(is_defense=False)

    def start_submission_game_defense(self):
        self.player.state = "DEFENSE_SUB"
        self.state_label.config(text="ESCAPE!", bg="#ff0000", fg="white")
        self.sub_target = random.randint(2, 9)
        self.banned_numbers = [self.sub_target]
        self.escape_attempts = 0
        self.log(f"IN HOLD! Pressure: {self.sub_target}")
        self.log("Guess correctly 3 times to escape!")
        self.update_submission_ui(is_defense=True)

    def update_submission_ui(self, is_defense):
        self.clear_buttons()
        self.buttons["btn_00"].config(text="LOWER\n( < X )", bg="#44f", fg="white", state="normal", 
                                      command=lambda: self.resolve_submission("LOWER", is_defense))
        self.buttons["btn_01"].config(text="HIGHER\n( > X )", bg="#f44", fg="white", state="normal", 
                                      command=lambda: self.resolve_submission("HIGHER", is_defense))
        if not is_defense:
            self.buttons["btn_10"].config(text="RELEASE", bg="#444", fg="white", state="normal", 
                                          command=self.set_ground_state)

    def resolve_submission(self, guess, is_defense):
        new_val = random.randint(1, 10)
        while new_val in self.banned_numbers: new_val = random.randint(1, 10)
        
        self.banned_numbers.append(new_val)
        if len(self.banned_numbers) > 3: self.banned_numbers.pop(0)

        success = (guess == "HIGHER" and new_val > self.sub_target) or \
                  (guess == "LOWER" and new_val < self.sub_target)

        self.log(f"Next: {new_val} (Prev: {self.sub_target})")
        self.sub_target = new_val

        if is_defense:
            if success:
                self.escape_attempts += 1
                self.log(f"Escaping... ({self.escape_attempts}/3)")
                if self.escape_attempts >= 3:
                    self.log("YOU BROKE FREE!")
                    self.set_neutral_state()
                else: self.update_submission_ui(True)
            else:
                self.log("Wrong! You take damage!")
                self.player.hp -= 8
                self.update_ui()
                if not self.game_over: self.update_submission_ui(True)
        else:
            if success:
                self.log("Hold tightened! (10 dmg)")
                self.cpu.hp -= 10
                self.update_ui()
                self.update_submission_ui(False)
            else:
                self.log("They kicked you off!")
                self.set_neutral_state()

    # ==========================================
    #           DEFENSE STATES
    # ==========================================
    def cpu_attacks_logic(self):
        roll = random.random()
        if roll < 0.3:
            self.log("CPU lands a clean strike!")
            self.player.hp -= 5
            self.update_ui()
            self.root.after(1000, self.set_neutral_state)
        elif roll < 0.7:
            self.log("CPU attempts a grapple!")
            self.set_defense_grapple_state()
        else:
            self.log("CPU drags you to the ground!")
            self.start_submission_game_defense()

    def set_defense_grapple_state(self):
        self.state_label.config(text="DEFEND!", bg="#ff0000", fg="white")
        self.clear_buttons()
        self.buttons["btn_00"].config(text="BLOCK\n(Safe)", bg="#666", fg="white", state="normal", 
                                      command=lambda: self.resolve_defense("BLOCK"))
        self.buttons["btn_01"].config(text="REVERSAL\n(Risk)", bg="#f44", fg="white", state="normal", 
                                      command=lambda: self.resolve_defense("REVERSE"))

    def resolve_defense(self, choice):
        if choice == "BLOCK":
            if random.random() > 0.2:
                self.log("You blocked the grapple.")
                self.root.after(1000, self.set_neutral_state)
            else:
                self.log("Block failed! Suplexed!")
                self.player.hp -= 10
                self.update_ui()
                self.root.after(1000, self.set_neutral_state)
        elif choice == "REVERSE":
            if random.random() > 0.6:
                self.log("REVERSAL! You stole the move!")
                self.cpu.hp -= 5
                self.player_wins_control()
            else:
                self.log("Reversal failed! DDT!")
                self.player.hp -= 15
                self.update_ui()
                self.root.after(1000, self.set_neutral_state)

    # ==========================================
    #           LOGIC & ACTIONS
    # ==========================================
    def attempt_strike(self):
        penalty = self.player.get_stale_penalty("Strike")
        self.player.record_move("Strike")
        
        fail_chance = 0.2 + penalty
        if random.random() > fail_chance:
            dmg = 5 + self.player.heat_bonus
            self.log(f"Strike lands! ({dmg} dmg)")
            self.cpu.hp -= dmg
            self.player.heat_bonus = 0
            self.update_ui()
            if random.random() > 0.6: self.player_wins_control()
            else: self.set_neutral_state()
        else:
            if penalty > 0: self.log(f"PREDICTABLE! (Penalty)")
            else: self.log("Strike blocked!")
            self.cpu_attacks_logic()

    def attempt_running_attack(self):
        self.log("You hit the ropes...")
        if random.random() > 0.5:
            self.log("CLOTHESLINE! They are down!")
            self.cpu.hp -= (10 + self.player.heat_bonus)
            self.player.heat_bonus = 0
            self.update_ui()
            self.set_ground_state()
        else:
            self.log("You crashed and burned!")
            self.player.hp -= 5
            self.cpu_attacks_logic()

    def attempt_taunt(self):
        if random.random() > 0.4:
            self.player.heat_bonus += 5
            self.log(f"Crowd cheers! (+{self.player.heat_bonus} Heat)")
            self.heat_label.config(text=f"HEAT: +{self.player.heat_bonus}")
            self.cpu_attacks_logic()
        else:
            self.log("Caught taunting!")
            self.player.hp -= 5
            self.cpu_attacks_logic()

    def resolve_ground_hit(self, damage, risk=0.1):
        if random.random() < risk:
            self.log("Missed!")
            self.set_neutral_state()
        else:
            final = damage + self.player.heat_bonus
            self.log(f"Ground hit! ({final} dmg)")
            self.cpu.hp -= final
            self.player.heat_bonus = 0
            self.update_ui()

    def start_struggle(self, context):
        self.player.state = context
        self.mini_game_score = {"p": 0, "c": 0}
        self.state_label.config(text="LOCK UP", bg="#ffaa00", fg="black")
        self.log("LOCK UP! Push to 15!")
        self.struggle_hit("p")
        self.clear_buttons()
        self.buttons["btn_00"].config(text="PUSH", bg="#0a0", fg="white", state="normal", command=lambda: self.struggle_hit("p"))
        self.buttons["btn_01"].config(text="HOLD", bg="#a00", fg="white", state="normal", command=self.struggle_stand)

    def struggle_hit(self, who):
        if self.game_over: return
        card = random.randint(1, 6)
        self.mini_game_score[who] += card
        name = "YOU" if who == "p" else "CPU"
        if who == "p": self.log(f"You push: {self.mini_game_score['p']} (Max 15)")

        if self.mini_game_score[who] > 15:
            self.log(f"{name} BUSTED!")
            if who == "p": self.cpu_attacks_logic()
            else: self.player_wins_control()

    def struggle_stand(self):
        if self.game_over: return
        self.log(f"Hold at {self.mini_game_score['p']}")
        while self.mini_game_score['c'] < 12:
             self.struggle_hit("c")
             if self.mini_game_score['c'] > 15: return 

        if self.mini_game_score['p'] >= self.mini_game_score['c']: self.player_wins_control()
        else: self.cpu_attacks_logic()

    def update_ui(self):
        if self.game_over: return
        self.p_hp_bar['value'] = self.player.hp
        self.c_hp_bar['value'] = self.cpu.hp
        self.heat_label.config(text=f"HEAT: +{self.player.heat_bonus}")
        
        if self.cpu.hp <= 0:
            self.game_over = True
            messagebox.showinfo("WIN", "Opponent Tapped Out!")
            self.root.destroy()
        elif self.player.hp <= 0:
            self.game_over = True
            messagebox.showinfo("LOSS", "You were PINNED!")
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameEngine(root)
    root.mainloop()
