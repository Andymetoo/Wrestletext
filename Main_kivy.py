from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
import random

# Import your existing logic
from wrestler import Wrestler, WrestlerState, GrappleRole
from cards import Deck
from moves_db import MOVES

class WrestleApp(App):
    def build(self):
        Window.clearcolor = (0.06, 0.06, 0.06, 1)

        # --- Game Objects ---
        self.player = Wrestler("Player", True)
        self.cpu = Wrestler("CPU", False)
        
        # Game State
        self.game_over = False
        self.turn = "player"
        self._escape_mode = None  # None or dict with pin info
        self.selected_cards = set()
        self.selected_move = None
        self.current_category = None
        
        # --- ROOT LAYOUT ---
        root = BoxLayout(orientation='vertical')

        # 1. HUD (Top 15%)
        hud = BoxLayout(orientation='vertical', size_hint_y=0.15, padding=5, spacing=2)
        
        hp_row = BoxLayout(orientation='horizontal')
        self.player_hp_label = Label(text="PLAYER HP: 100", color=(0.2, 1, 0.2, 1), bold=True)
        self.cpu_hp_label = Label(text="CPU HP: 100", color=(1, 0.2, 0.2, 1), bold=True)
        hp_row.add_widget(self.player_hp_label)
        hp_row.add_widget(self.cpu_hp_label)
        
        stats_row = BoxLayout(orientation='horizontal')
        self.grit_label = Label(text="[color=bb86fc]GRIT: 5[/color]", markup=True)
        self.hype_label = Label(text="[color=ff9800]HYPE: 0[/color]", markup=True)
        stats_row.add_widget(self.grit_label)
        stats_row.add_widget(self.hype_label)
        
        hud.add_widget(hp_row)
        hud.add_widget(stats_row)

        # 2. ARENA (Middle 65%)
        arena_box = BoxLayout(orientation='vertical', size_hint_y=0.65)
        
        # A. Game Log (Top of Arena)
        self.log_scroll = ScrollView(size_hint_y=0.3)
        self.log_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=6, spacing=2)
        self.log_layout.bind(minimum_height=self.log_layout.setter('height'))
        self.log_scroll.add_widget(self.log_layout)
        arena_box.add_widget(self.log_scroll)

        # B. Move List (Bottom of Arena)
        self.move_scroll = ScrollView(size_hint_y=0.7)
        self.move_list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5, padding=10)
        self.move_list_layout.bind(minimum_height=self.move_list_layout.setter('height'))
        self.move_scroll.add_widget(self.move_list_layout)
        arena_box.add_widget(self.move_scroll)
        
        root.add_widget(hud)
        root.add_widget(arena_box)

        # 3. CONTROL BAR (10%)
        controls = BoxLayout(orientation='horizontal', size_hint_y=0.10, spacing=10, padding=5)
        
        self.return_btn = Button(
            text="< RETURN",
            background_color=get_color_from_hex("#6200ea"),
            background_normal="",
            disabled=True,
            opacity=0 
        )
        self.return_btn.bind(on_release=self._on_return_click)

        self.play_btn = Button(
            text="PLAY\n(Cost: 0)",
            background_color=get_color_from_hex("#00c853"),
            background_normal="",
        )
        self.play_btn.bind(on_release=self._on_play_click)

        controls.add_widget(self.return_btn)
        controls.add_widget(self.play_btn)
        root.add_widget(controls)

        # 4. HAND (Bottom 10%)
        self.hand_layout = BoxLayout(orientation='horizontal', size_hint_y=0.10, spacing=2, padding=2)
        root.add_widget(self.hand_layout)

        # Initial Start
        self._start_turn("player")
        return root

    # -------------------------------------------------------------------------
    # CORE GAME LOOP & LOGIC
    # -------------------------------------------------------------------------

    def _start_turn(self, who):
        if self.game_over: return
        
        self.player.draw_to_full()
        self.cpu.draw_to_full()
        
        self.selected_cards.clear()
        self.selected_move = None
        self._escape_mode = None
        
        self._update_hud()
        self._render_hand()
        self._show_categories()
        
        # Soft lock check
        if self.player.grit == 0 and not self.player.has_low_card(max_value=5):
            self._log("GASSED OUT! Skipping turn to recover...")
            self.player.grit = 5
            self._update_hud()
            # Simple skip logic
            Clock.schedule_once(lambda dt: self._resolve_clash("Rest", [], "Jab", []), 1.5)

    def _log(self, text: str):
        lbl = Label(
            text=f"> {text}",
            size_hint_y=None, height=30,
            halign="left", valign="middle",
            text_size=(self.root.width * 0.9, None), # Wrap text
            color=(0.8, 1, 0.8, 1)
        )
        self.log_layout.add_widget(lbl)
        # Scroll to bottom
        Clock.schedule_once(lambda dt: self.log_scroll.scroll_to(lbl))

    def _resolve_clash(self, p_move, p_cards, c_move, c_cards):
        # 1. Calculate Costs
        p_move_cost = int(MOVES.get(p_move, {}).get("cost", 0))
        p_card_cost = sum(c.grit_cost() for c in p_cards)
        
        c_move_cost = int(MOVES.get(c_move, {}).get("cost", 0))
        c_card_cost = sum(c.grit_cost() for c in c_cards)

        # 2. Calculate Scores
        p_score = self._calc_clash_score(p_move, p_cards)
        c_score = self._calc_clash_score(c_move, c_cards)
        
        self._log(f"YOU: {p_move} ({p_score})")
        self._log(f"CPU: {c_move} ({c_score})")

        # 3. Determine Winner
        winner, loser = None, None
        w_move, w_score = None, None

        if p_score == c_score:
            self._log("DOUBLE DOWN! Both fighters hit the mat!")
            self.player.take_damage(5)
            self.cpu.take_damage(5)
            self.player.set_state(WrestlerState.GROUNDED)
            self.cpu.set_state(WrestlerState.GROUNDED)
        else:
            if p_score > c_score:
                winner, loser = self.player, self.cpu
                w_move, w_score = p_move, p_score
            else:
                winner, loser = self.cpu, self.player
                w_move, w_score = c_move, c_score
            
            # Execute Winner's Move
            self._execute_move(winner, loser, w_move, w_score)

        # 4. Pay Costs & Discard
        self.player.spend_grit(p_move_cost)
        self.player.discard_cards(p_cards)
        
        self.cpu.spend_grit(c_move_cost)
        self.cpu.discard_cards(c_cards)

        self._update_hud()
        
        # 5. Check Game Over
        if self.player.hp <= 0 or self.cpu.hp <= 0:
            self.game_over = True
            winner_name = "CPU" if self.player.hp <= 0 else "YOU"
            self._log(f"GAME OVER! {winner_name} WINS!")
            return

        # 6. Next Phase (Escape or New Turn)
        if self._escape_mode:
            self._render_escape_ui()
        else:
            self._start_turn("player")

    def _execute_move(self, attacker, defender, move_name, clash_score):
        move = MOVES[move_name]
        
        # Narrative
        flavor = move.get("flavor_text", "")
        # Pronoun fix
        target_name = "YOU" if defender == self.player else defender.name
        flavor = flavor.replace("them", target_name).replace("their", f"{target_name}'s")
        self._log(f"{attacker.name} hits {move_name}! {flavor}")

        # Pin/Sub Check
        mtype = move.get("type")
        if mtype in ["Pin", "Submission"]:
            threshold = 1 + int(25 * (1.0 - defender.hp_pct()))
            self._log(f"Survival Attempt! Threshold: {threshold}")
            self._escape_mode = {
                "active": True,
                "attacker": attacker,
                "defender": defender,
                "threshold": threshold,
                "current_score": 0,
                "turns_left": 3
            }
            return # Pause turn loop

        # Damage
        dmg = move.get("damage", 0)
        if dmg > 0:
            defender.take_damage(dmg)
        
        # Effects
        attacker.add_hype(move.get("hype_gain", 0))
        
        # State Changes
        if "set_user_state" in move:
            attacker.set_state(WrestlerState(move["set_user_state"]))
        if "set_target_state" in move:
            defender.set_state(WrestlerState(move["set_target_state"]))
            
        # Grapple Logic
        if move_name == "Shove Off":
            attacker.clear_grapple()
            defender.clear_grapple()

    # -------------------------------------------------------------------------
    # HELPER LOGIC
    # -------------------------------------------------------------------------

    def _calc_clash_score(self, move_name, cards):
        if not cards: return 0
        
        val = sum(c.value for c in cards)
        
        # Doubles Bonus
        if len(cards) == 2 and cards[0].value == cards[1].value:
            val += 5
            
        # Color Match Bonus
        mtype = MOVES[move_name].get("type", "").upper()
        # Map DB types to Card Colors
        type_map = {"STRIKE": "RED", "GRAPPLE": "BLUE", "SUBMISSION": "GREEN", "AERIAL": "YELLOW"}
        target_color = type_map.get(mtype, "")
        
        for c in cards:
            if c.color == target_color:
                val += 1
                
        return val

    def _cpu_choose_move(self):
        # 1. Get valid moves
        valid = []
        for name in MOVES:
            if self._move_is_legal(name, self.cpu, self.player):
                valid.append(name)
        
        if not valid: return "Rest"
        
        # 2. Hype Shop Check (20% chance)
        if self.cpu.hype > 25 and random.random() < 0.2:
            pass # (Implement buy logic later)
            
        # 3. Decision (Greedy vs Random)
        mistake_prob = 0.15
        if random.random() < mistake_prob:
            return random.choice(valid)
        else:
            # Greedy: Pick highest damage or best state
            valid.sort(key=lambda m: MOVES[m].get("damage", 0), reverse=True)
            return valid[0]

    def _cpu_choose_cards(self, move_name):
        # Simple Greedy: Use highest value card(s)
        # Sort hand descending
        sorted_hand = sorted(self.cpu.hand, key=lambda c: c.value, reverse=True)
        
        # Filter by what we can afford
        affordable = []
        move_cost = MOVES[move_name].get("cost", 0)
        current_grit = self.cpu.grit
        
        for c in sorted_hand:
            if (move_cost + c.grit_cost()) <= current_grit:
                affordable.append(c)
                
        if not affordable:
            return []
            
        return [affordable[0]] # Just play best single card for now

    def _move_is_legal(self, move_name, user, target):
        data = MOVES[move_name]
        req_u = data.get("req_user_state", "ANY")
        req_t = data.get("req_target_state", "ANY")
        
        # Check User State
        if req_u != "ANY" and user.state != req_u:
            # Special case: Grapple moves valid in both grapple states?
            if "GRAPPLE" in req_u and user.is_in_grapple():
                pass
            else:
                return False
                
        # Check Target State
        if req_t != "ANY" and target.state != req_t:
            return False
            
        # Check Cost
        if user.grit < data.get("cost", 0):
            return False
            
        return True

    # -------------------------------------------------------------------------
    # UI EVENT HANDLERS
    # -------------------------------------------------------------------------
    
    def _update_hud(self):
        self.player_hp_label.text = f"PLAYER HP: {self.player.hp}"
        self.cpu_hp_label.text = f"CPU HP: {self.cpu.hp}"
        self.grit_label.text = f"[color=bb86fc]GRIT: {self.player.grit}[/color]"
        self.hype_label.text = f"[color=ff9800]HYPE: {self.player.hype}[/color]"

    def _render_hand(self):
        self.hand_layout.clear_widgets()
        for i, card in enumerate(self.player.hand):
            # Color logic
            bg = (0.2, 0.2, 0.2, 1)
            if card.color == "RED": bg = (0.5, 0.1, 0.1, 1)
            elif card.color == "BLUE": bg = (0.1, 0.1, 0.5, 1)
            elif card.color == "GREEN": bg = (0.1, 0.5, 0.1, 1)
            elif card.color == "YELLOW": bg = (0.5, 0.5, 0.1, 1)

            btn = Button(
                text=str(card.value),
                background_color=bg, background_normal="",
                font_size='18sp', bold=True
            )
            btn.card_index = i 
            btn.bind(on_release=self._on_card_click)
            self.hand_layout.add_widget(btn)
        self._update_play_button()

    def _show_categories(self):
        self.move_list_layout.clear_widgets()
        self.current_category = None
        self.selected_move = None
        self.return_btn.disabled = True
        self.return_btn.opacity = 0
        
        categories = ["Strike", "Grapple", "Aerial", "Setup", "Hype"]
        for cat in categories:
            # Disable Grapple category if not in grapple
            if cat == "Grapple" and not self.player.is_in_grapple():
                continue 

            btn = Button(text=f"[b]{cat.upper()}[/b]", markup=True, size_hint_y=None, height=60, background_normal="", background_color=(0.15,0.15,0.15,1))
            btn.bind(on_release=lambda x, c=cat: self._on_category_click(c))
            self.move_list_layout.add_widget(btn)

    def _on_category_click(self, category):
        self.current_category = category
        self.move_list_layout.clear_widgets()
        self.return_btn.disabled = False
        self.return_btn.opacity = 1
        
        for name, data in MOVES.items():
            if data.get("type") == category or (category == "Setup" and data.get("type") == "Utility"):
                if self._move_is_legal(name, self.player, self.cpu):
                    
                    # Tint buttons
                    bg = (0.2,0.2,0.2,1)
                    if category == "Strike": bg = (0.4, 0, 0, 1)
                    if category == "Grapple": bg = (0, 0, 0.4, 1)

                    btn = Button(
                        text=f"{name}\n{data.get('damage',0)} Dmg | {data.get('cost',0)} Grit",
                        size_hint_y=None, height=60,
                        background_color=bg, background_normal="",
                        halign="center"
                    )
                    btn.move_name = name
                    btn.bind(on_release=self._on_move_click)
                    self.move_list_layout.add_widget(btn)

    def _on_move_click(self, instance):
        self.selected_move = instance.move_name
        self._update_play_button()

    def _on_card_click(self, instance):
        idx = instance.card_index
        if idx in self.selected_cards:
            self.selected_cards.remove(idx)
            instance.opacity = 1.0 
        else:
            if len(self.selected_cards) < 2:
                self.selected_cards.add(idx)
                instance.opacity = 0.5 
        self._update_play_button()

    def _update_play_button(self):
        cost = 0
        if self.selected_move:
            cost += MOVES[self.selected_move].get("cost", 0)
        for idx in self.selected_cards:
            if idx < len(self.player.hand):
                cost += self.player.hand[idx].grit_cost()
        
        btn_text = f"PLAY\n(Cost: {cost})"
        if self.player.grit < cost:
            btn_text = f"NEED {cost}\nGRIT"
            self.play_btn.background_color = (1, 0, 0, 1)
        else:
            self.play_btn.background_color = get_color_from_hex("#00c853")
            
        self.play_btn.text = btn_text

    def _on_play_click(self, instance):
        if self._escape_mode:
            self._handle_escape_play()
            return

        if not self.selected_move:
            self._log("Select a move first!")
            return
        
        p_cards = [self.player.hand[i] for i in self.selected_cards]
        # Basic Validation
        if not p_cards:
            self._log("You must play at least 1 card.")
            return

        # CPU Logic
        c_move = self._cpu_choose_move()
        c_cards = self._cpu_choose_cards(c_move)
        
        self._resolve_clash(self.selected_move, p_cards, c_move, c_cards)

    def _on_return_click(self, instance):
        self._show_categories()

    # -------------------------------------------------------------------------
    # ESCAPE MODE LOGIC
    # -------------------------------------------------------------------------
    
    def _render_escape_ui(self):
        self.move_list_layout.clear_widgets()
        # Hide standard controls
        self.return_btn.disabled = True
        self.return_btn.opacity = 0
        
        info = self._escape_mode
        lbl = Label(
            text=f"ESCAPE ATTEMPT!\nScore: {info['current_score']} / {info['threshold']}\nTurns Left: {info['turns_left']}",
            font_size='24sp', halign="center"
        )
        self.move_list_layout.add_widget(lbl)
        self.play_btn.text = "SUBMIT CARD"

    def _handle_escape_play(self):
        if not self.selected_cards: return
        
        # Play 1 card at a time logic
        idx = list(self.selected_cards)[0]
        card = self.player.hand.pop(idx) # Remove from hand
        
        val = card.value
        self._escape_mode["current_score"] += val
        self._escape_mode["turns_left"] -= 1
        
        self._log(f"You play {val}. Total: {self._escape_mode['current_score']}")
        
        if self._escape_mode["current_score"] >= self._escape_mode["threshold"]:
            self._log("ESCAPE SUCCESSFUL!")
            self._escape_mode = None
            self.player.set_state(WrestlerState.STANDING)
            self._start_turn("player")
        elif self._escape_mode["turns_left"] <= 0:
            self._log("ESCAPE FAILED! GAME OVER.")
            self.game_over = True
        else:
            self._render_hand()
            self._render_escape_ui()

if __name__ == "__main__":
    WrestleApp().run()
