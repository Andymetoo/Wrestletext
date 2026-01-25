import tkinter as tk
from tkinter import messagebox, ttk
import random

# --- IMPORT MODULES ---
from wrestler import Wrestler, MAX_HEALTH
import moves # Importing our new narrative database
from mechanics import QTEManager, SubmissionManager

class GameEngine:
    def __init__(self, root):
        self.root = root
        self.root.title("Squared Circle: Narrative Edition")
        self.root.geometry("400x850") 
        self.root.configure(bg="#121212")

        self.player = Wrestler("Player", True)
        self.cpu = Wrestler("CPU", False)
        self.qte_sys = QTEManager()
        self.sub_sys = SubmissionManager()
        
        self.game_over = False
        self.mini_game_score = {"p": 0, "c": 0}

        self.create_widgets()
        self.set_neutral_state()
        self.game_loop()

    def create_widgets(self):
        # HUD
        self.hud_frame = tk.Frame(self.root, bg="#222", pady=5)
        self.hud_frame.pack(fill="x")

        # Player Bars
        self.p_stat = tk.Frame(self.hud_frame, bg="#222")
        self.p_stat.pack(side="left", padx=5, fill="x", expand=True)
        tk.Label(self.p_stat, text="YOU", fg="#4f4", bg="#222", font=("Impact", 10)).pack(anchor="w")
        self.p_hp_bar = ttk.Progressbar(self.p_stat, length=100, maximum=MAX_HEALTH)
        self.p_hp_bar.pack(fill="x")
        
        # State Text
        self.state_label = tk.Label(self.hud_frame, text="NEUTRAL", fg="white", bg="#444", font=("Impact", 14))
        self.state_label.pack(side="left", padx=5)

        # CPU Bars
        self.c_stat = tk.Frame(self.hud_frame, bg="#222")
        self.c_stat.pack(side="right", padx=5, fill="x", expand=True)
        tk.Label(self.c_stat, text="CPU", fg="#f44", bg="#222", font=("Impact", 10)).pack(anchor="e")
        self.c_hp_bar = ttk.Progressbar(self.c_stat, length=100, maximum=MAX_HEALTH)
        self.c_hp_bar.pack(fill="x")

        self.heat_label = tk.Label(self.root, text="", fg="orange", bg="#121212", font=("Arial", 10, "bold"))
        self.heat_label.pack()

        # Log
        self.log_frame = tk.Frame(self.root, bg="black", bd=2, relief="sunken")
        self.log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text = tk.Text(self.log_frame, bg="black", fg="#0f0", font=("Courier New", 12), state="disabled", height=8)
        self.log_text.pack(fill="both", expand=True)

        # QTE Bar
        self.qte_frame = tk.Frame(self.root, bg="#222", pady=5)
        self.qte_frame.pack(fill="x", padx=10)
        tk.Label(self.qte_frame, text="TIMING BAR", fg="#888", bg="#222", font=("Arial", 8)).pack()
        self.qte_bar = ttk.Progressbar(self.qte_frame, length=300, maximum=100)
        self.qte_bar.pack(fill="x")

        # Buttons
        self.control_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.control_frame.pack(fill="x", side="bottom", pady=5, padx=5)
        self.control_frame.columnconfigure(0, weight=1)
        self.control_frame.columnconfigure(1, weight=1)

        self.buttons = {}
        for r in range(3):
            for c in range(2):
                name = f"btn_{r}{c}"
                btn = tk.Button(self.control_frame, text="...", font=("Arial", 10, "bold"), height=3, bg="#333", fg="white")
                btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                self.buttons[name] = btn

    # --- ENGINE UTILS ---
    def game_loop(self):
        if self.game_over: return
        if self.qte_sys.active:
            self.qte_sys.update()
            self.qte_bar['value'] = self.qte_sys.value
        self.root.after(50, self.game_loop)

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

    # --- STATE: NEUTRAL ---
    def set_neutral_state(self):
        self.player.state = "NEUTRAL"
        self.state_label.config(text="NEUTRAL", bg="#555", fg="white")
        self.clear_buttons()
        self.qte_bar['value'] = 0

        self.buttons["btn_00"].config(text="LOCK UP", bg="#44f", fg="white", state="normal", 
                                      command=lambda: self.start_struggle("TIE_UP"))
        
        penalty = self.player.get_stale_penalty("Strike")
        risk_txt = "Safe" if penalty == 0 else f"Risk {int(penalty*100)}%"
        self.buttons["btn_01"].config(text=f"STRIKE\n({risk_txt})", bg="#a44", fg="white", state="normal", 
                                      command=self.attempt_strike)
        
        self.buttons["btn_10"].config(text="RUNNING ATK", bg="#a44", fg="white", state="normal", 
                                      command=self.attempt_running_attack)
        
        self.buttons["btn_11"].config(text="TAUNT", bg="#444", fg="white", state="normal", 
                                      command=self.attempt_taunt)

    # --- STATE: GRAPPLE ---
    def player_wins_control(self):
        self.player.state = "CONTROL"
        self.state_label.config(text="IN CONTROL", bg="#0f0", fg="black")
        self.clear_buttons()
        
        move_keys = list(moves.GRAPPLE_MOVES.keys())
        for i in range(3): 
            if i < len(move_keys):
                m_name = move_keys[i]
                m_data = moves.GRAPPLE_MOVES[m_name]
                r, c = (0,0) if i==0 else (0,1) if i==1 else (1,0)
                
                self.buttons[f"btn_{r}{c}"].config(
                    text=f"{m_name}\n({m_data['dmg']} dmg)", bg="#a00", fg="white", state="normal",
                    command=lambda m=m_data: self.start_qte_ui(m)
                )
        
        self.buttons["btn_21"].config(text="CANCEL", bg="#444", fg="white", state="normal", 
                                      command=self.set_neutral_state)

    def start_qte_ui(self, move_data):
        self.qte_sys.start(move_data)
        self.state_label.config(text="TIMING!", bg="#ffffff", fg="black")
        self.log(f"Setting up: {move_data['desc']}...")
        self.clear_buttons()
        self.buttons["btn_10"].config(text="!!! EXECUTE !!!", bg="#0f0", fg="black", state="normal", command=self.resolve_qte_ui)
        self.buttons["btn_11"].config(text="!!! EXECUTE !!!", bg="#0f0", fg="black", state="normal", command=self.resolve_qte_ui)

    def resolve_qte_ui(self):
        val = self.qte_sys.resolve()
        move = self.qte_sys.target_move
        
        if val > 95:
            # BOTCH
            self.log(f"BOTCHED! (Timing: {val}%)")
            self.log(move['botch']) # Using new flavor text
            self.player.hp -= 10
            self.update_ui()
            self.root.after(2000, self.set_neutral_state)
        elif val >= 70:
            # CRITICAL
            crit = int(move['dmg'] * 1.5)
            self.log(f"PERFECT! (Timing: {val}%)")
            self.log(move['crit']) # Using new flavor text
            self.cpu.hp -= crit
            self.update_ui()
            self.root.after(2000, self.set_neutral_state)
        elif val >= 40:
            # HIT
            self.log(f"GOOD HIT! (Timing: {val}%)")
            self.log(move['hit']) # Using new flavor text
            self.cpu.hp -= move['dmg']
            self.update_ui()
            self.root.after(2000, self.set_neutral_state)
        else:
            # WEAK
            self.log(f"WEAK... (Timing: {val}%)")
            self.log("They shrugged it off.")
            self.cpu.hp -= int(move['dmg'] / 2)
            self.update_ui()
            self.cpu_attacks_logic()

    # --- ACTIONS ---
    def attempt_strike(self):
        penalty = self.player.get_stale_penalty("Strike")
        self.player.record_move("Strike")
        
        # Pick a random strike text
        strike_name = random.choice(list(moves.STRIKES.keys()))
        strike_data = moves.STRIKES[strike_name]

        if random.random() > (0.2 + penalty):
            dmg = strike_data['dmg'] + self.player.heat_bonus
            self.log(strike_data['hit']) # Flavor!
            self.cpu.hp -= dmg
            self.player.heat_bonus = 0
            self.update_ui()
            if random.random() > 0.6: self.player_wins_control()
            else: self.set_neutral_state()
        else:
            if penalty > 0: self.log("Predictable! They know your pattern!")
            else: self.log(strike_data['blocked']) # Flavor!
            self.cpu_attacks_logic()

    def attempt_running_attack(self):
        # Let's randomly pick Clothesline or Spear for variety
        m_name = random.choice(list(moves.RUNNING_MOVES.keys()))
        move = moves.RUNNING_MOVES[m_name]
        
        self.log(f"You hit the ropes for a {m_name}...")
        
        if random.random() > move['risk']:
            total = move['dmg'] + self.player.heat_bonus
            self.log(move['hit']) # Flavor!
            self.cpu.hp -= total
            self.player.heat_bonus = 0
            self.update_ui()
            self.set_ground_state()
        else:
            self.log(move['miss']) # Flavor!
            self.player.hp -= 5
            self.cpu_attacks_logic()

    def attempt_taunt(self):
        if random.random() > 0.4:
            self.player.heat_bonus += 5
            self.log(f"You play to the crowd! (+{self.player.heat_bonus} Heat)")
            self.update_ui()
            self.cpu_attacks_logic()
        else:
            self.log("You turned your back! Cheap shot!")
            self.player.hp -= 5
            self.cpu_attacks_logic()

    def set_ground_state(self):
        self.player.state = "GROUND"
        self.state_label.config(text="ENEMY DOWN", bg="#880088", fg="white")
        self.clear_buttons()
        
        m_stomp = moves.GROUND_MOVES["Stomp"]
        m_elbow = moves.GROUND_MOVES["Elbow Drop"]

        self.buttons["btn_00"].config(text=f"STOMP\n({m_stomp['dmg']} dmg)", bg="#aa0", state="normal", 
                                      command=lambda: self.resolve_ground(m_stomp))
        self.buttons["btn_01"].config(text=f"ELBOW\n(Risk {m_elbow['risk']})", bg="#a44", state="normal", 
                                      command=lambda: self.resolve_ground(m_elbow))
        self.buttons["btn_10"].config(text="SUBMISSION", bg="#00a", fg="white", state="normal", 
                                      command=lambda: self.start_sub_ui(False))
        self.buttons["btn_11"].config(text="PICK UP", bg="#444", fg="white", state="normal", 
                                      command=self.set_neutral_state)

    def resolve_ground(self, move_data):
        if random.random() < move_data['risk']:
            self.log(move_data['miss']) # Flavor!
            self.player.hp -= 5 # Self damage on miss
            self.update_ui()
            self.set_neutral_state()
        else:
            final = move_data['dmg'] + self.player.heat_bonus
            self.log(move_data['hit']) # Flavor!
            self.cpu.hp -= final
            self.player.heat_bonus = 0
            self.update_ui()

    # --- SUBMISSION UI ---
    def start_sub_ui(self, is_defense):
        self.sub_sys.start(is_defense)
        self.state_label.config(text="SUBMISSION", bg="#00f" if not is_defense else "#f00")
        self.log(f"Applying hold... Pressure: {self.sub_sys.target}")
        self.update_sub_buttons(is_defense)

    def update_sub_buttons(self, is_defense):
        self.clear_buttons()
        self.buttons["btn_00"].config(text="LOWER", bg="#44f", state="normal", command=lambda: self.resolve_sub("LOWER", is_defense))
        self.buttons["btn_01"].config(text="HIGHER", bg="#f44", state="normal", command=lambda: self.resolve_sub("HIGHER", is_defense))

    def resolve_sub(self, guess, is_defense):
        next_val = self.sub_sys.generate_next()
        success = self.sub_sys.check_guess(guess, next_val)
        
        self.log(f"Next: {next_val} (Prev: {self.sub_sys.target})")
        self.sub_sys.target = next_val

        if is_defense:
            if success:
                self.sub_sys.attempts += 1
                self.log(f"Fight it! {self.sub_sys.attempts}/3")
                if self.sub_sys.attempts >= 3:
                    self.log("YOU BROKE THE HOLD!")
                    self.set_neutral_state()
                else: self.update_sub_buttons(True)
            else:
                self.log("They wrench it back! 8 dmg")
                self.player.hp -= 8
                self.update_ui()
                self.update_sub_buttons(True)
        else:
            if success:
                self.log("You tighten the hold! 10 dmg")
                self.cpu.hp -= 10
                self.update_ui()
                self.update_sub_buttons(False)
            else:
                self.log("They kicked you off!")
                self.set_neutral_state()

    # --- LOCK UP / AI ---
    def start_struggle(self, context):
        self.player.state = context
        self.mini_game_score = {"p": 0, "c": 0}
        self.state_label.config(text="LOCK UP", bg="#fa0", fg="black")
        self.log("Collar and Elbow tie up!")
        self.struggle_hit("p")
        self.clear_buttons()
        self.buttons["btn_00"].config(text="PUSH", bg="#0a0", state="normal", command=lambda: self.struggle_hit("p"))
        self.buttons["btn_01"].config(text="HOLD", bg="#a00", state="normal", command=self.struggle_stand)

    def struggle_hit(self, who):
        if self.game_over: return
        self.mini_game_score[who] += random.randint(1, 6)
        if who=="p": self.log(f"You push... {self.mini_game_score['p']}")
        
        if self.mini_game_score[who] > 15:
            if who=="p": self.log("You slipped! BUSTED!") or self.cpu_attacks_logic()
            else: self.log("CPU over-committed! BUSTED!") or self.player_wins_control()

    def struggle_stand(self):
        self.log(f"Holding at {self.mini_game_score['p']}...")
        while self.mini_game_score['c'] < 12: self.struggle_hit("c")
        if self.mini_game_score['c'] > 15: return
        if self.mini_game_score['p'] >= self.mini_game_score['c']: self.player_wins_control()
        else: self.cpu_attacks_logic()

    def cpu_attacks_logic(self):
        roll = random.random()
        if roll < 0.4:
            self.log("CPU lands a haymaker! 5 dmg")
            self.player.hp -= 5
            self.update_ui()
            self.root.after(1000, self.set_neutral_state)
        else:
            self.log("CPU locks in a Sleeper Hold!")
            self.start_sub_ui(True)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameEngine(root)
    root.mainloop()
