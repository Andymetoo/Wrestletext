from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty
import random

# Import your existing logic
from wrestler import Wrestler, WrestlerState, GrappleRole, MAX_HEALTH
from moves_db import MOVES

# ==========================================
#  🎨 THEME & TUNING (Tinker Here!)
# ==========================================

# COLORS (R, G, B, A) - 0.0 to 1.0
COLOR_BG_MAIN   = (0.06, 0.06, 0.06, 1)   # Almost Black
COLOR_BTN_BASE  = (0.15, 0.15, 0.15, 1)   # Dark Grey Buttons
COLOR_TEXT_MAIN = (1, 1, 1, 1)            # White Text

# Common text tones
COLOR_TEXT_SOFT = (0.90, 0.90, 0.90, 1)
COLOR_TEXT_HINT = (0.75, 0.75, 0.75, 1)
COLOR_TEXT_MUTED = (0.72, 0.72, 0.72, 1)
COLOR_TEXT_PROMPT = (0.95, 0.95, 0.95, 1)

# Accent + HUD
COLOR_LOG_TEXT = (0.8, 1, 0.8, 1)
COLOR_HP_PLAYER = (0.25, 1, 0.25, 1)
COLOR_HP_CPU = (1, 0.25, 0.25, 1)

# Kivy markup + bar colors
COLOR_HEX_GRIT = "bb86fc"
COLOR_HEX_HYPE = "ff9800"

# Control bar accents
COLOR_HEX_RETURN = "#6200ea"
COLOR_HEX_PLAY_ENABLED = "#00c853"
COLOR_HEX_PLAY_DISABLED = "#444444"

# TYPE COLORS (Used for button hints)
COLOR_STRIKE    = (0.40, 0.05, 0.05, 1)   # Dark Red
COLOR_GRAPPLE   = (0.05, 0.05, 0.40, 1)   # Dark Blue
COLOR_AERIAL    = (0.40, 0.40, 0.05, 1)   # Dark Yellow
COLOR_SUBMIT    = (0.05, 0.40, 0.05, 1)   # Dark Green

COLOR_DEFENSIVE = (0.10, 0.10, 0.10, 1)
COLOR_FINISHER = (0.83, 0.69, 0.22, 1)

COLOR_HYPE_SHOP = (0.28, 0.17, 0.0, 1)

# DIMENSIONS (Size Hints vs Fixed Pixels)
# (Set to current defaults so changing these is easy and predictable.)
HUD_HEIGHT_PCT = 0.22
ARENA_HEIGHT_PCT = 0.62
CONTROLS_HEIGHT_PCT = 0.10
HAND_HEIGHT_PCT = 0.10

ARENA_LOG_PCT = 0.30
ARENA_MOVES_PCT = 0.70

BTN_HEIGHT_CATEGORY_PX = 64
BTN_HEIGHT_MOVE_PX = 74
BTN_HEIGHT_SHOP_PX = 78

class ColoredBar(Widget):
    """Simple colored meter bar (avoids theme limitations of ProgressBar)."""

    value = NumericProperty(0)
    max_value = NumericProperty(100)
    bar_color = ListProperty([1, 1, 1, 1])
    back_color = ListProperty([0.12, 0.12, 0.12, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            from kivy.graphics import Color, Rectangle

            self._back_color_instr = Color(*self.back_color)
            self._back_rect = Rectangle(pos=self.pos, size=self.size)
            self._bar_color_instr = Color(*self.bar_color)
            self._bar_rect = Rectangle(pos=self.pos, size=(0, self.height))

        self.bind(pos=self._redraw, size=self._redraw)
        self.bind(value=self._redraw, max_value=self._redraw)
        self.bind(bar_color=self._redraw_colors, back_color=self._redraw_colors)

    def _redraw_colors(self, *_args):
        self._back_color_instr.rgba = self.back_color
        self._bar_color_instr.rgba = self.bar_color
        self._redraw()

    def _redraw(self, *_args):
        self._back_rect.pos = self.pos
        self._back_rect.size = self.size

        denom = float(self.max_value) if float(self.max_value) > 0 else 1.0
        pct = max(0.0, min(1.0, float(self.value) / denom))
        self._bar_rect.pos = self.pos
        self._bar_rect.size = (self.width * pct, self.height)

class WrestleApp(App):
    def build(self):
        Window.clearcolor = COLOR_BG_MAIN

        # --- Game Objects ---
        self.player = Wrestler("YOU", True)
        self.cpu = Wrestler("CPU", False)
        
        # Game State
        self.game_over = False
        self.turn = "player"
        self._escape_mode: dict | None = None
        self.selected_cards: set[int] = set()
        self.selected_move: str | None = None
        self._menu_stage: str = "CATEGORIES"  # CATEGORIES | MOVES | HYPE_SHOP | ESCAPE
        self._selected_category: str | None = None
        
        # --- ROOT LAYOUT ---
        root = BoxLayout(orientation='vertical')
        self.root = root

        # 1. HUD (Top)
        hud = BoxLayout(orientation='vertical', size_hint_y=HUD_HEIGHT_PCT, padding=6, spacing=4)

        self.state_label = Label(
            text="YOU: STANDING  |  CPU: STANDING",
            color=COLOR_TEXT_MAIN,
            size_hint_y=None,
            height=22,
            font_size="13sp",
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.state_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        hud.add_widget(self.state_label)
        
        hp_row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=42)
        left_hp = BoxLayout(orientation='vertical')
        right_hp = BoxLayout(orientation='vertical')
        self.player_hp_label = Label(text="YOU HP: 100", color=COLOR_HP_PLAYER, size_hint_y=None, height=18)
        self.cpu_hp_label = Label(text="CPU HP: 100", color=COLOR_HP_CPU, size_hint_y=None, height=18)
        self.player_hp_bar = ProgressBar(max=MAX_HEALTH, value=MAX_HEALTH)
        self.cpu_hp_bar = ProgressBar(max=MAX_HEALTH, value=MAX_HEALTH)
        left_hp.add_widget(self.player_hp_label)
        left_hp.add_widget(self.player_hp_bar)
        right_hp.add_widget(self.cpu_hp_label)
        right_hp.add_widget(self.cpu_hp_bar)
        hp_row.add_widget(left_hp)
        hp_row.add_widget(right_hp)
        
        meters_row = BoxLayout(orientation='horizontal', spacing=10)

        purple = get_color_from_hex(COLOR_HEX_GRIT)
        orange = get_color_from_hex(COLOR_HEX_HYPE)

        # Player meters (left)
        p_box = BoxLayout(orientation='vertical', spacing=2)
        self.p_grit_label = Label(
            text=f"[color={COLOR_HEX_GRIT}]GRIT 0/0[/color]",
            markup=True,
            size_hint_y=None,
            height=18,
            halign="left",
            valign="middle",
            font_size="12sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.p_grit_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        self.p_grit_bar = ColoredBar(size_hint_y=None, height=10, max_value=self.player.max_grit, value=self.player.grit, bar_color=purple)
        self.p_hype_label = Label(
            text=f"[color={COLOR_HEX_HYPE}]HYPE 0/100[/color]",
            markup=True,
            size_hint_y=None,
            height=18,
            halign="left",
            valign="middle",
            font_size="12sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.p_hype_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        self.p_hype_bar = ColoredBar(size_hint_y=None, height=10, max_value=100, value=self.player.hype, bar_color=orange)
        self.p_nums = Label(
            text="",
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=16,
            halign="left",
            valign="middle",
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.p_nums.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        self.p_limbs = Label(
            text="",
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=16,
            halign="left",
            valign="middle",
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.p_limbs.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))

        p_box.add_widget(self.p_grit_label)
        p_box.add_widget(self.p_grit_bar)
        p_box.add_widget(self.p_hype_label)
        p_box.add_widget(self.p_hype_bar)
        p_box.add_widget(self.p_nums)
        p_box.add_widget(self.p_limbs)

        # CPU meters (right)
        c_box = BoxLayout(orientation='vertical', spacing=2)
        self.c_grit_label = Label(
            text=f"[color={COLOR_HEX_GRIT}]GRIT 0/0[/color]",
            markup=True,
            size_hint_y=None,
            height=18,
            halign="left",
            valign="middle",
            font_size="12sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.c_grit_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        self.c_grit_bar = ColoredBar(size_hint_y=None, height=10, max_value=self.cpu.max_grit, value=self.cpu.grit, bar_color=purple)
        self.c_hype_label = Label(
            text=f"[color={COLOR_HEX_HYPE}]HYPE 0/100[/color]",
            markup=True,
            size_hint_y=None,
            height=18,
            halign="left",
            valign="middle",
            font_size="12sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.c_hype_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        self.c_hype_bar = ColoredBar(size_hint_y=None, height=10, max_value=100, value=self.cpu.hype, bar_color=orange)
        self.c_nums = Label(
            text="",
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=16,
            halign="left",
            valign="middle",
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.c_nums.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        self.c_limbs = Label(
            text="",
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=16,
            halign="left",
            valign="middle",
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.c_limbs.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))

        c_box.add_widget(self.c_grit_label)
        c_box.add_widget(self.c_grit_bar)
        c_box.add_widget(self.c_hype_label)
        c_box.add_widget(self.c_hype_bar)
        c_box.add_widget(self.c_nums)
        c_box.add_widget(self.c_limbs)

        meters_row.add_widget(p_box)
        meters_row.add_widget(c_box)

        hud.add_widget(hp_row)
        hud.add_widget(meters_row)

        # 2. ARENA (Middle)
        arena_box = BoxLayout(orientation='vertical', size_hint_y=ARENA_HEIGHT_PCT)
        
        # A. Game Log (Top of Arena)
        self.log_scroll = ScrollView(size_hint_y=ARENA_LOG_PCT)
        self.log_scroll.do_scroll_x = False
        self.log_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=6, spacing=2)
        self.log_layout.bind(minimum_height=self.log_layout.setter('height'))
        self.log_scroll.add_widget(self.log_layout)
        self.log_scroll.bind(width=self._sync_log_width)
        arena_box.add_widget(self.log_scroll)

        # B. Move List (Bottom of Arena) — 3-column grid for mobile density
        self.move_scroll = ScrollView(size_hint_y=ARENA_MOVES_PCT)
        self.move_list_layout = GridLayout(cols=3, spacing=6, padding=[10, 10, 10, 10], size_hint_y=None)
        self.move_list_layout.bind(minimum_height=self.move_list_layout.setter('height'))
        self.move_scroll.add_widget(self.move_list_layout)
        arena_box.add_widget(self.move_scroll)
        
        root.add_widget(hud)
        root.add_widget(arena_box)

        # 3. CONTROL BAR
        controls = BoxLayout(orientation='horizontal', size_hint_y=CONTROLS_HEIGHT_PCT, spacing=8, padding=[8, 6, 8, 6])
        
        self.return_btn = Button(
            text="< RETURN",
            background_color=get_color_from_hex(COLOR_HEX_RETURN),
            background_normal="",
            disabled=True,
            opacity=0,
            size_hint_x=0.30,
        )
        self.return_btn.bind(on_release=self._on_return_click)

        self.hint_label = Label(
            text="Pick a category.",
            color=COLOR_TEXT_HINT,
            halign="left",
            valign="middle",
        )
        self.hint_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))

        self.play_btn = Button(
            text="PLAY\n(0 Grit)",
            background_color=get_color_from_hex(COLOR_HEX_PLAY_ENABLED),
            background_normal="",
            disabled=True,
            size_hint_x=0.30,
        )
        self.play_btn.bind(on_release=self._on_play_click)

        controls.add_widget(self.return_btn)
        controls.add_widget(self.hint_label)
        controls.add_widget(self.play_btn)
        root.add_widget(controls)

        # 4. HAND (Bottom)
        self.hand_layout = BoxLayout(orientation='horizontal', size_hint_y=HAND_HEIGHT_PCT, spacing=4, padding=[6, 4, 6, 6])
        root.add_widget(self.hand_layout)

        # Initial Start
        self._start_turn("player")
        return root

    def _sync_log_width(self, *_args) -> None:
        # Keep log content aligned to the visible ScrollView width.
        try:
            self.log_layout.size_hint_x = 1
            self.log_layout.width = self.log_scroll.width
        except Exception:
            return

    # -------------------------------------------------------------------------
    # CORE GAME LOOP & LOGIC
    # -------------------------------------------------------------------------

    def _start_turn(self, who):
        if self.game_over: return

        # Phase 2: player always initiates the clash; CPU responds instantly.
        self.turn = "player"
        
        self.player.draw_to_full()
        self.cpu.draw_to_full()
        
        self.selected_cards.clear()
        self.selected_move = None
        self._escape_mode = None

        self._menu_stage = "CATEGORIES"
        self._selected_category = None
        
        self._update_hud()
        self._render_hand()
        self._render_moves_ui()
        self._update_control_bar()
        
        # Soft-lock protection: if you can't afford any play (no low cards and 0 grit), auto-rest.
        if self.player.grit == 0 and not self.player.has_low_card(max_value=5):
            self._log("GASSED OUT! You can’t afford any cards — auto Rest.")
            Clock.schedule_once(lambda _dt: self._submit_forced_rest(), 0.6)

    def _submit_forced_rest(self) -> None:
        if self.game_over:
            return
        if self._escape_mode is not None:
            return
        self.selected_move = "Rest"
        self.selected_cards.clear()
        self._submit_cards()

    def _log(self, text: str):
        lbl = Label(
            text=f"> {text}",
            size_hint_x=1,
            size_hint_y=None,
            halign="left",
            valign="top",
            color=COLOR_LOG_TEXT,
        )

        def refresh_wrap(*_a) -> None:
            pad = 16
            w = max(120, int(self.log_scroll.width) - pad)
            lbl.text_size = (w, None)
            lbl.texture_update()
            lbl.height = max(26, int(lbl.texture_size[1]) + 6)

        lbl.bind(width=refresh_wrap)
        self.log_scroll.bind(width=lambda *_a: refresh_wrap())
        refresh_wrap()

        self.log_layout.add_widget(lbl)
        Clock.schedule_once(lambda _dt: self.log_scroll.scroll_to(lbl), 0)

    # -------------------------------------------------------------------------
    # Shared mechanics (ported from main.py)
    # -------------------------------------------------------------------------

    def _render_flavor_text(self, text: str, *, attacker: Wrestler, defender: Wrestler) -> str:
        if not text:
            return ""
        attacker_ref = "You" if attacker.is_player else attacker.name
        attacker_poss = "your" if attacker.is_player else f"{attacker.name}'s"
        defender_ref = "you" if defender.is_player else defender.name
        defender_ref_cap = "You" if defender.is_player else defender.name
        defender_poss = "your" if defender.is_player else f"{defender.name}'s"

        out = str(text)
        out = out.replace("You're", f"{attacker_ref} are")
        out = out.replace("You", attacker_ref)
        out = out.replace("Your", attacker_poss.capitalize())
        out = out.replace("your", attacker_poss)
        out = out.replace("They", attacker_ref)
        out = out.replace("Their", attacker_poss.capitalize())
        out = out.replace(" them ", f" {defender_ref} ")
        out = out.replace(" Them ", f" {defender_ref_cap} ")
        out = out.replace(" their ", f" {defender_poss} ")
        out = out.replace(" Their ", f" {defender_poss.capitalize()} ")
        return out

    def _move_is_legal(self, move_name: str, user: Wrestler, target: Wrestler) -> bool:
        mv = MOVES[move_name]
        ru = str(mv.get("req_user_state", "ANY"))
        rt = str(mv.get("req_target_state", "ANY"))

        if ru != "ANY":
            if ru in {"GRAPPLED", "GRAPPLE_ANY"}:
                if not user.is_in_grapple():
                    return False
            elif user.state.value != ru:
                return False

        if rt != "ANY":
            if rt in {"GRAPPLED", "GRAPPLE_ANY"}:
                if not target.is_in_grapple():
                    return False
            elif target.state.value != rt:
                return False

        user_adv = user.is_in_grapple() and (user.grapple_role == GrappleRole.OFFENSE)
        user_dis = user.is_in_grapple() and (user.grapple_role == GrappleRole.DEFENSE)

        if user_dis:
            if move_name not in {"Fight For Control", "Defensive", "Rest", "Shove Off"}:
                return False

        if move_name == "Defensive":
            if user_adv:
                return False
            neutral_ok = (user.state == WrestlerState.STANDING and target.state == WrestlerState.STANDING)
            if not (neutral_ok or user_dis):
                return False

        return True

    def _passes_moveset(self, wrestler: Wrestler, move_name: str) -> bool:
        # Keep parity with Tk version: universal safety options always allowed.
        universal = {
            "Defensive",
            "Rest",
            "Taunt",
            "Lock Up",
            "Shove Off",
            "Slow Stand Up",
            "Kip-up",
            "Climb Down",
            "Stop Short",
        }
        if move_name in universal:
            return True
        if wrestler.moveset is None:
            return True
        return move_name in set(wrestler.moveset)

    def _available_moves(self, user: Wrestler, target: Wrestler) -> list[str]:
        names = [n for n in MOVES.keys() if self._move_is_legal(n, user, target) and self._passes_moveset(user, n)]

        if user.state == WrestlerState.STANDING and target.state == WrestlerState.STANDING:
            allowed_names = {"Lock Up", "Taunt", "Defensive"}
            names = [n for n in names if MOVES[n].get("type") == "Strike" or n in allowed_names]
            if self._move_is_legal("Rest", user, target) and self._passes_moveset(user, "Rest"):
                names.append("Rest")

        def key(n: str) -> tuple[int, int, str]:
            t = str(MOVES[n].get("type", "Setup"))
            type_order = {"Defensive": 0, "Setup": 1, "Strike": 2, "Grapple": 3, "Aerial": 4, "Submission": 5, "Pin": 6}
            return (type_order.get(t, 99), int(MOVES[n].get("cost", 0)), n)

        return sorted(names, key=key)

    def _calc_clash_score(self, move_name: str, cards: list, *, card_bonus: int = 0) -> int:
        if move_name == "Defensive":
            return -1
        if not cards:
            return 0

        if len(cards) == 2 and int(cards[0].value) == int(cards[1].value):
            base = int(cards[0].value) + 5
        else:
            base = sum(int(c.value) for c in cards)

        move_type = str(MOVES.get(move_name, {}).get("type", "Setup"))
        if len(cards) == 2 and int(cards[0].value) == int(cards[1].value):
            base += max(int(cards[0].color_bonus(move_type)), int(cards[1].color_bonus(move_type)))
        else:
            base += sum(int(c.color_bonus(move_type)) for c in cards)

        base += int(card_bonus)
        return int(base)

    def _selected_player_cards(self) -> list:
        hand = list(self.player.hand or [])
        idxs = sorted(self.selected_cards)
        cards = [hand[i] for i in idxs if 0 <= i < len(hand)]

        if self.selected_move == "Defensive":
            if any(int(c.value) > 5 for c in cards):
                return []
            return cards

        if len(cards) == 2 and int(cards[0].value) != int(cards[1].value):
            return []
        return cards

    def _effective_cost(self, wrestler: Wrestler, move_name: str, cards: list) -> int:
        mv_cost = int(MOVES.get(move_name, {}).get("cost", 0))
        ignore_cards = (move_name == "Rest")
        card_cost = 0 if ignore_cards else sum(int(c.grit_cost()) for c in (cards or []))
        return int(mv_cost) + int(card_cost)

    def _resolve_clash(self, p_move: str, p_cards: list, c_move: str, c_cards: list) -> None:
        if self.game_over:
            return

        p_move_cost = int(MOVES.get(p_move, {}).get("cost", 0))
        c_move_cost = int(MOVES.get(c_move, {}).get("cost", 0))

        p_ignore_cards = (p_move == "Rest")
        c_ignore_cards = (c_move == "Rest")

        p_bonus = int(self.player.next_card_bonus)
        c_bonus = int(self.cpu.next_card_bonus)

        p_score = -1 if p_move == "Defensive" else self._calc_clash_score(p_move, p_cards, card_bonus=p_bonus)
        c_score = -1 if c_move == "Defensive" else self._calc_clash_score(c_move, c_cards, card_bonus=c_bonus)

        if p_move == "Defensive":
            p_pool = sum(int(c.value) for c in (p_cards or []))
            self._log(f"YOU: Defensive [DEF {p_pool}]")
        else:
            self._log(f"YOU: {p_move} [{p_score}]")

        if c_move == "Defensive":
            c_pool = sum(int(c.value) for c in (c_cards or []))
            self._log(f"CPU: Defensive [DEF {c_pool}]")
        else:
            self._log(f"CPU: {c_move} [{c_score}]")

        winner = loser = None
        w_move = None
        w_score = None

        if p_move == "Defensive" and c_move == "Defensive":
            self._log("Both fighters play it safe—no clean opening this beat.")
        elif (p_move != "Defensive") and (c_move != "Defensive") and (p_score == c_score):
            self._log("DOUBLE DOWN! Both crash into the mat — 5 damage each. Both are GROUNDED.")
            self.player.take_damage(5)
            self.cpu.take_damage(5)
            self.player.clear_grapple()
            self.cpu.clear_grapple()
            self.player.set_state(WrestlerState.GROUNDED)
            self.cpu.set_state(WrestlerState.GROUNDED)
        elif p_score > c_score:
            winner, loser = self.player, self.cpu
            w_move, w_score = p_move, p_score
        else:
            winner, loser = self.cpu, self.player
            w_move, w_score = c_move, c_score

        # Spend grit + apply card-driven economy + discard + redraw (both sides pay their attempt).
        self.player.spend_grit(p_move_cost)
        self.player.apply_grit_from_cards(p_cards, ignore_cost=p_ignore_cards)
        self.player.discard_cards(p_cards)
        self.player.draw_to_full()

        self.cpu.spend_grit(c_move_cost)
        self.cpu.apply_grit_from_cards(c_cards, ignore_cost=c_ignore_cards)
        self.cpu.discard_cards(c_cards)
        self.cpu.draw_to_full()

        self.player.next_card_bonus = 0
        self.cpu.next_card_bonus = 0

        if winner is not None and w_move is not None:
            loser_move = c_move if winner is self.player else p_move
            loser_type = str(MOVES.get(loser_move, {}).get("type", "Setup"))
            if str(w_move) in {"Taunt", "Rest"} and loser_type not in {"Setup", "Defensive"}:
                self._log(f"{winner.name} dodges effortlessly while {loser.name} wastes the beat.")

            # Defensive cancel/soften
            if (p_move == "Defensive" and winner is self.cpu) or (c_move == "Defensive" and winner is self.player):
                defender_cards = p_cards if p_move == "Defensive" else c_cards
                pool = sum(int(c.value) for c in (defender_cards or []))
                opp_score = int(w_score or 0)
                raw_dmg = int(MOVES.get(w_move, {}).get("damage", 0))
                avoid_ok = (opp_score <= 10 and pool >= opp_score)
                suppress_states = (opp_score <= 10 and pool >= max(1, opp_score - 2))
                if avoid_ok:
                    self._log(f"Defensive ({pool}): slip away from the attack!")
                else:
                    reduction = pool if opp_score <= 10 else (pool // 2)
                    dmg_override = max(0, raw_dmg - max(0, reduction))
                    if raw_dmg > 0 and dmg_override < raw_dmg:
                        self._log(f"Defensive ({pool}): soften the blow ({raw_dmg}->{dmg_override}).")
                    self._execute_move(attacker=winner, defender=loser, move_name=w_move, clash_score=w_score, damage_override=dmg_override, suppress_state_changes=bool(suppress_states))
            else:
                self._execute_move(attacker=winner, defender=loser, move_name=w_move, clash_score=w_score)

        self._update_hud()

        if self.player.hp <= 0 or self.cpu.hp <= 0:
            self.game_over = True
            winner_name = "CPU" if self.player.hp <= 0 else "YOU"
            self._log(f"GAME OVER! {winner_name} WINS!")
            self._update_control_bar()
            return

        if self._escape_mode:
            self._render_escape_ui()
            self._update_control_bar()
        else:
            self._start_turn("player")

    def _escape_threshold(self, victim_hp_pct: float) -> int:
        pct = max(0.0, min(1.0, float(victim_hp_pct)))
        v = 1 + int(25.0 * (1.0 - pct))
        return max(1, min(26, int(v)))

    def _begin_escape(self, *, attacker: Wrestler, defender: Wrestler, kind: str) -> None:
        threshold = self._escape_threshold(defender.hp_pct())
        self._escape_mode = {
            "kind": str(kind),
            "threshold": int(threshold),
            "total": 0,
            "plays_left": 3,
            "attacker_is_player": bool(attacker.is_player),
            "defender_is_player": bool(defender.is_player),
            "attacker": attacker,
            "defender": defender,
        }
        self._menu_stage = "ESCAPE"
        self._selected_category = None
        self.selected_move = None
        self.selected_cards.clear()

        if defender.is_player:
            self._log(f"{kind}! Tap 3 cards to escape (no redraw).")
            self._render_moves_ui()
            self._render_hand()
            self._update_control_bar()
            return

        # CPU defending: simulate from its current hand.
        total = 0
        plays = 3
        while plays > 0:
            plays -= 1
            hand = list(defender.hand or [])
            if not hand:
                break
            best = max(hand, key=lambda c: int(c.value))
            total += int(best.value)
            defender.discard_cards([best])
            if total >= int(threshold):
                self._log(f"CPU escapes the {kind.lower()} attempt!")
                self._end_escape(success=True)
                return

        winner = "YOU" if attacker.is_player else "CPU"
        self.game_over = True
        self._log(f"{kind}! Escape failed — {winner} wins.")
        self._update_control_bar()

    def _escape_play_card(self, index: int) -> None:
        if self.game_over or not self._escape_mode:
            return
        if not bool(self._escape_mode.get("defender_is_player")):
            return
        hand = list(self.player.hand or [])
        if index < 0 or index >= len(hand):
            return
        card = hand[index]
        gained = int(card.value)
        self.player.discard_cards([card])

        self._escape_mode["total"] = int(self._escape_mode.get("total", 0)) + gained
        self._escape_mode["plays_left"] = int(self._escape_mode.get("plays_left", 0)) - 1

        total = int(self._escape_mode.get("total", 0))
        threshold = int(self._escape_mode.get("threshold", 1))
        kind = str(self._escape_mode.get("kind", "ESCAPE"))

        self._log(f"Escape discard: {gained} (total {total}/{threshold})")
        self._render_hand()
        self._render_moves_ui()
        self._update_control_bar()

        if total >= threshold:
            self._log(f"You escape the {kind.lower()} attempt!")
            self._end_escape(success=True)
            return

        if int(self._escape_mode.get("plays_left", 0)) <= 0:
            winner = "YOU" if bool(self._escape_mode.get("attacker_is_player")) else "CPU"
            self.game_over = True
            self._log(f"{kind}! Escape failed — {winner} wins.")
            self._update_control_bar()
            return

    def _end_escape(self, *, success: bool) -> None:
        if not self._escape_mode:
            return
        attacker = self._escape_mode.get("attacker")
        defender = self._escape_mode.get("defender")
        if success and isinstance(attacker, Wrestler) and isinstance(defender, Wrestler):
            attacker.clear_grapple()
            defender.clear_grapple()
            attacker.set_state(WrestlerState.STANDING)
            defender.set_state(WrestlerState.STANDING)
            attacker.draw_to_full()
            defender.draw_to_full()

        self._escape_mode = None
        self._menu_stage = "CATEGORIES"
        self._selected_category = None
        self.selected_move = None
        self.selected_cards.clear()
        self._render_hand()
        self._render_moves_ui()
        self._update_hud()
        self._update_control_bar()

    def _execute_move(self, *, attacker: Wrestler, defender: Wrestler, move_name: str, clash_score: int | None = None, damage_override: int | None = None, suppress_state_changes: bool = False) -> None:
        move = MOVES[move_name]
        mtype = str(move.get("type", "Setup"))

        flavor = self._render_flavor_text(str(move.get("flavor_text", "")), attacker=attacker, defender=defender)
        self._log(f"{attacker.name} uses {move_name}! {flavor}")

        if move_name == "Rest":
            before = attacker.grit
            attacker.grit = min(attacker.max_grit, attacker.grit + 3)
            gained = attacker.grit - before
            self._log(f"{attacker.name} recovers (+{gained} Grit).")
            return

        if move_name == "Taunt":
            attacker.add_hype(int(move.get("hype_gain", 0)))
            self._log(f"{attacker.name} gets fired up!")
            return

        if move_name == "Shove Off":
            if attacker.is_in_grapple() or defender.is_in_grapple():
                attacker.clear_grapple()
                defender.clear_grapple()
                attacker.set_state(WrestlerState.STANDING)
                defender.set_state(WrestlerState.STANDING)
                self._log(f"{attacker.name} shoves free and resets to neutral!")
            else:
                self._log(f"{attacker.name} tries to shove off, but they're not tied up.")
            return

        # Pin/Submission start escape
        if mtype in {"Pin", "Submission"}:
            kind = "PINFALL" if mtype == "Pin" else "SUBMISSION"
            self._begin_escape(attacker=attacker, defender=defender, kind=kind)
            return

        raw_damage = int(move.get("damage", 0)) if damage_override is None else int(damage_override)
        if raw_damage > 0:
            defender.take_damage(raw_damage)
            self._log(f"{defender.name} takes {raw_damage} damage.")

        attacker.add_hype(int(move.get("hype_gain", 0)))

        if not suppress_state_changes:
            if "set_user_state" in move:
                attacker.set_state(WrestlerState(str(move["set_user_state"])))
            if "set_target_state" in move:
                defender.set_state(WrestlerState(str(move["set_target_state"])))

        if attacker.is_in_grapple() and defender.is_in_grapple():
            attacker.grapple_role = GrappleRole.OFFENSE
            defender.grapple_role = GrappleRole.DEFENSE

    # -------------------------------------------------------------------------
    # HELPER LOGIC
    # -------------------------------------------------------------------------

    def _cpu_buy_buffs(self) -> None:
        """Spend CPU hype on buffs before selecting a move."""
        if self.game_over:
            return
        if int(self.cpu.hype) < 25:
            return

        # Simple parity behavior: choose between Pump (+1) and Adrenaline (+2).
        # Kept probabilistic so CPU doesn't always auto-buy.
        if int(self.cpu.hype) >= 50 and random.random() < 0.15:
            self.cpu.hype -= 50
            self.cpu.next_card_bonus = max(int(self.cpu.next_card_bonus), 2)
            self._log("CPU uses the crowd energy! (Adrenaline +2 next card)")
            return

        if int(self.cpu.hype) >= 25 and random.random() < 0.20:
            self.cpu.hype -= 25
            self.cpu.next_card_bonus = max(int(self.cpu.next_card_bonus), 1)
            self._log("CPU digs deep! (Pump Up +1 next card)")
            return

    def _cpu_choose_move(self):
        valid = self._available_moves(self.cpu, self.player)
        if not valid:
            return "Rest"

        if random.random() < float(self.cpu.mistake_prob):
            return random.choice(valid)

        # Greedy-ish: favor finishers when available, else damage.
        def score(name: str) -> float:
            mv = MOVES[name]
            base = float(mv.get("damage", 0))
            if bool(mv.get("is_finisher")):
                base += 8.0
            if name == "Lock Up" and self.cpu.state == WrestlerState.STANDING and self.player.state == WrestlerState.STANDING:
                base += 4.0
            if name == "Taunt" and self.cpu.hype < 80:
                base += 2.0
            return base + random.random() * 0.5

        valid.sort(key=score, reverse=True)
        return valid[0]

    def _cpu_choose_cards(self, move_name):
        hand = list(self.cpu.hand or [])
        if not hand:
            return []

        ignore_card_cost = (move_name == "Rest")
        move_cost = int(MOVES.get(move_name, {}).get("cost", 0))

        candidates: list[list] = []

        # Singles
        for c in hand:
            card_cost = 0 if ignore_card_cost else int(c.grit_cost())
            if int(self.cpu.grit) >= int(move_cost) + int(card_cost):
                candidates.append([c])

        # Doubles
        by_val: dict[int, list] = {}
        for c in hand:
            by_val.setdefault(int(c.value), []).append(c)
        for _v, cs in by_val.items():
            if len(cs) >= 2:
                pair = [cs[0], cs[1]]
                card_cost = 0 if ignore_card_cost else sum(int(x.grit_cost()) for x in pair)
                if int(self.cpu.grit) >= int(move_cost) + int(card_cost):
                    candidates.append(pair)

        if not candidates:
            return []

        if random.random() < float(self.cpu.mistake_prob):
            return random.choice(candidates)

        def value_key(cs: list) -> tuple[int, int]:
            raw = sum(int(c.value) for c in cs)
            score = self._calc_clash_score(move_name, cs, card_bonus=int(self.cpu.next_card_bonus)) if move_name != "Defensive" else -1
            return (raw, score)

        candidates.sort(key=value_key, reverse=True)
        return candidates[0]

    # -------------------------------------------------------------------------
    # UI EVENT HANDLERS
    # -------------------------------------------------------------------------
    
    def _update_hud(self):
        def role(w: Wrestler) -> str:
            if (not w.is_in_grapple()) or w.grapple_role is None:
                return ""
            return f" ({w.grapple_role.value})"

        def flow(w: Wrestler) -> str:
            if not w.is_flow():
                return ""
            return f" [FLOW {w.flow_turns_remaining}]"

        self.state_label.text = f"YOU: {self.player.state.value}{role(self.player)}{flow(self.player)}  |  CPU: {self.cpu.state.value}{role(self.cpu)}{flow(self.cpu)}"

        self.player_hp_label.text = f"YOU HP: {self.player.hp}"
        self.cpu_hp_label.text = f"CPU HP: {self.cpu.hp}"
        self.player_hp_bar.value = int(self.player.hp)
        self.cpu_hp_bar.value = int(self.cpu.hp)

        # Grit/Hype meters
        self.p_grit_label.text = f"[color={COLOR_HEX_GRIT}]GRIT {self.player.grit}/{self.player.max_grit}[/color]"
        self.c_grit_label.text = f"[color={COLOR_HEX_GRIT}]GRIT {self.cpu.grit}/{self.cpu.max_grit}[/color]"
        self.p_hype_label.text = f"[color={COLOR_HEX_HYPE}]HYPE {self.player.hype}/100[/color]"
        self.c_hype_label.text = f"[color={COLOR_HEX_HYPE}]HYPE {self.cpu.hype}/100[/color]"

        self.p_grit_bar.max_value = int(self.player.max_grit)
        self.c_grit_bar.max_value = int(self.cpu.max_grit)
        self.p_grit_bar.value = int(self.player.grit)
        self.c_grit_bar.value = int(self.cpu.grit)

        self.p_hype_bar.max_value = 100
        self.c_hype_bar.max_value = 100
        self.p_hype_bar.value = int(self.player.hype)
        self.c_hype_bar.value = int(self.cpu.hype)

        # Strength + limbs
        p_str = f"Str {self.player.strength_current()}/{self.player.strength_max()}"
        c_str = f"Str {self.cpu.strength_current()}/{self.cpu.strength_max()}"
        self.p_nums.text = p_str
        self.c_nums.text = c_str

        self.p_limbs.text = f"H:{self.player.body_parts['HEAD']}  B:{self.player.body_parts['BODY']}  L:{self.player.body_parts['LEGS']}"
        self.c_limbs.text = f"H:{self.cpu.body_parts['HEAD']}  B:{self.cpu.body_parts['BODY']}  L:{self.cpu.body_parts['LEGS']}"

    def _render_hand(self):
        self.hand_layout.clear_widgets()
        for i, card in enumerate(self.player.hand):
            # Color logic
            bg = COLOR_BTN_BASE
            if card.color == "RED":
                bg = COLOR_STRIKE
            elif card.color == "BLUE":
                bg = COLOR_GRAPPLE
            elif card.color == "GREEN":
                bg = COLOR_SUBMIT
            elif card.color == "YELLOW":
                bg = COLOR_AERIAL

            btn = Button(
                text=str(card.value),
                background_color=bg, background_normal="",
                font_size='18sp', bold=True
            )
            btn.card_index = i 
            btn.bind(on_release=self._on_card_click)
            self.hand_layout.add_widget(btn)
        self._update_play_button()

    def _set_menu_stage(self, stage: str, *, category: str | None = None) -> None:
        self._menu_stage = str(stage)
        self._selected_category = category
        self._render_moves_ui()
        self._update_control_bar()

    def _on_category_click(self, category: str) -> None:
        key = str(category)
        if key in {"HYPE", "HYPE_SHOP"}:
            self._set_menu_stage("HYPE_SHOP")
        else:
            self._set_menu_stage("MOVES", category=key)

    def _category_has_moves(self, category: str) -> bool:
        moves = self._available_moves(self.player, self.cpu)
        if category == "STRIKES":
            return any(MOVES[m].get("type") == "Strike" for m in moves)
        if category == "GRAPPLES":
            return any(MOVES[m].get("type") in {"Grapple", "Submission", "Pin"} for m in moves)
        if category == "AERIAL_RUNNING":
            return any(MOVES[m].get("type") == "Aerial" or self.player.state in {WrestlerState.RUNNING, WrestlerState.TOP_ROPE} for m in moves)
        if category == "UTILITY":
            return any(MOVES[m].get("type") in {"Setup", "Defensive"} for m in moves)
        return True

    def _render_moves_ui(self) -> None:
        self.move_list_layout.clear_widgets()

        def brighten(rgba: tuple[float, float, float, float], factor: float = 1.35) -> tuple[float, float, float, float]:
            r, g, b, a = rgba
            return (min(1.0, r * factor), min(1.0, g * factor), min(1.0, b * factor), a)

        def type_color(mtype: str) -> tuple[float, float, float, float]:
            t = str(mtype)
            if t == "Strike":
                return COLOR_STRIKE
            if t in {"Grapple", "Pin"}:
                return COLOR_GRAPPLE
            if t == "Submission":
                return COLOR_SUBMIT
            if t == "Aerial":
                return COLOR_AERIAL
            if t == "Defensive":
                return COLOR_DEFENSIVE
            return COLOR_BTN_BASE

        # Escape stage UI
        if self._menu_stage == "ESCAPE" and self._escape_mode:
            info = self._escape_mode
            # Single wide label (span by adding 3 cols worth)
            lbl = Label(
                text=f"ESCAPE!  Total: {info.get('total', 0)}/{info.get('threshold', 1)}   Plays left: {info.get('plays_left', 0)}\nTap a card to discard it (no redraw).",
                color=COLOR_TEXT_SOFT,
                size_hint_y=None,
                height=84,
                halign="left",
                valign="middle",
            )
            lbl.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))
            self.move_list_layout.add_widget(lbl)
            return

        # Categories
        if self._menu_stage == "CATEGORIES":
            buttons: list[tuple[str, str]] = [
                ("STRIKES", "STRIKES"),
                ("GRAPPLES", "GRAPPLES"),
                ("AERIAL/RUNNING", "AERIAL_RUNNING"),
                ("UTILITY", "UTILITY"),
                ("HYPE SHOP", "HYPE_SHOP"),
            ]

            for label, key in buttons:
                enabled = True
                if key == "GRAPPLES":
                    enabled = (self.player.state != WrestlerState.STANDING) or self._category_has_moves("GRAPPLES")
                elif key == "AERIAL_RUNNING":
                    enabled = self._category_has_moves("AERIAL_RUNNING")
                elif key == "UTILITY":
                    enabled = self._category_has_moves("UTILITY")

                def go(_inst=None, k=key) -> None:
                    self._on_category_click(k)

                if key == "STRIKES":
                    bg = COLOR_STRIKE
                elif key == "GRAPPLES":
                    bg = COLOR_GRAPPLE
                elif key == "AERIAL_RUNNING":
                    bg = COLOR_AERIAL
                elif key == "HYPE_SHOP":
                    bg = COLOR_HYPE_SHOP
                else:
                    bg = COLOR_BTN_BASE

                btn = Button(
                    text=f"[b]{label}[/b]",
                    markup=True,
                    size_hint_x=1,
                    size_hint_y=None,
                    height=BTN_HEIGHT_CATEGORY_PX,
                    background_normal="",
                    background_color=bg,
                )
                btn.disabled = not enabled
                btn.bind(on_release=go)
                self.move_list_layout.add_widget(btn)
            return

        # Hype shop
        if self._menu_stage == "HYPE_SHOP":
            def buy_pump(_inst=None) -> None:
                if self.player.hype < 25:
                    return
                self.player.hype -= 25
                self.player.next_card_bonus = max(int(self.player.next_card_bonus), 1)
                self._log("Hype Shop: Pump Up purchased (+1 to next played card).")
                self._update_hud()
                self._render_moves_ui()
                self._update_control_bar()

            def buy_adrenaline(_inst=None) -> None:
                if self.player.hype < 50:
                    return
                self.player.hype -= 50
                self.player.next_card_bonus = max(int(self.player.next_card_bonus), 2)
                self._log("Hype Shop: Adrenaline purchased (+2 to next played card).")
                self._update_hud()
                self._render_moves_ui()
                self._update_control_bar()

            def buy_second_wind(_inst=None) -> None:
                if self.player.hype < 80:
                    return
                self.player.hype -= 80
                self.player.hp = min(MAX_HEALTH, self.player.hp + 15)
                self._log("Hype Shop: Second Wind! (+15 HP)")
                self._update_hud()
                self._render_moves_ui()
                self._update_control_bar()

            b1 = Button(text="Pump Up\n(25 Hype): Next card +1", size_hint_y=None, height=BTN_HEIGHT_SHOP_PX, background_normal="", background_color=COLOR_BTN_BASE)
            b2 = Button(text="Adrenaline\n(50 Hype): Next card +2", size_hint_y=None, height=BTN_HEIGHT_SHOP_PX, background_normal="", background_color=COLOR_BTN_BASE)
            b3 = Button(text="Second Wind\n(80 Hype): Heal 15 HP", size_hint_y=None, height=BTN_HEIGHT_SHOP_PX, background_normal="", background_color=COLOR_BTN_BASE)
            b1.disabled = self.player.hype < 25
            b2.disabled = self.player.hype < 50
            b3.disabled = self.player.hype < 80
            b1.bind(on_release=buy_pump)
            b2.bind(on_release=buy_adrenaline)
            b3.bind(on_release=buy_second_wind)
            self.move_list_layout.add_widget(b1)
            self.move_list_layout.add_widget(b2)
            self.move_list_layout.add_widget(b3)
            return

        # Moves within category
        if self._menu_stage == "MOVES":
            cat = str(self._selected_category or "UTILITY")
            avail = self._available_moves(self.player, self.cpu)
            if not avail:
                avail = ["Rest"]

            def in_cat(name: str) -> bool:
                t = str(MOVES[name].get("type", "Setup"))
                if cat == "STRIKES":
                    return t == "Strike"
                if cat == "GRAPPLES":
                    return t in {"Grapple", "Submission", "Pin"}
                if cat == "AERIAL_RUNNING":
                    return t == "Aerial" or self.player.state in {WrestlerState.RUNNING, WrestlerState.TOP_ROPE}
                if cat == "UTILITY":
                    return t in {"Setup", "Defensive"}
                return True

            moves_to_show = [m for m in avail if in_cat(m)]
            if not moves_to_show:
                moves_to_show = ["Rest"]

            moves_to_show = moves_to_show[:18]

            has_doubles = self.player.has_doubles_in_hand()
            for name in moves_to_show:
                mv = MOVES[name]
                finisher = bool(mv.get("is_finisher"))
                disabled = bool(finisher and (not has_doubles))
                t = str(mv.get("type", "Setup"))

                if finisher and not disabled:
                    bg = COLOR_FINISHER
                else:
                    bg = COLOR_DEFENSIVE if disabled else type_color(t)

                selected = (self.selected_move == name)
                if selected and (not disabled):
                    bg = brighten(bg)

                star = "★ " if finisher else ""
                dmg = int(mv.get('damage', 0))
                mc = int(mv.get('cost', 0))
                if name == "Defensive":
                    label = f"{star}{name}\nDiscard (≤5) to Block"
                else:
                    label = f"{star}{name}\n{dmg} Dmg | {mc} Move"
                btn = Button(
                    text=label,
                    size_hint_y=None,
                    height=BTN_HEIGHT_MOVE_PX,
                    background_normal="",
                    background_color=bg,
                )
                btn.disabled = disabled
                btn.move_name = name
                btn.bind(on_release=self._on_move_click)
                self.move_list_layout.add_widget(btn)
            return

    def _on_move_click(self, instance):
        name = str(getattr(instance, "move_name", ""))
        if not name:
            return

        # Lock Up resolves immediately (no card selection).
        if name == "Lock Up":
            self._do_lock_up()
            return

        self.selected_move = name
        self.selected_cards.clear()
        self._update_play_button()

    def _do_lock_up(self) -> None:
        """Special-case Lock Up like the Tk build.

        It resolves immediately (no cards), sets grapple states/roles,
        and then returns the player to category selection.
        """
        if self.game_over:
            return
        if self._escape_mode is not None:
            return
        if not self._move_is_legal("Lock Up", self.player, self.cpu):
            self._log("Lock Up is not legal right now.")
            return

        self._lockup_minigame(on_done=self._apply_lockup_result)

    def _apply_lockup_result(self, player_won: bool) -> None:
        if self.game_over:
            return

        self.player.set_state(WrestlerState.GRAPPLE_WEAK)
        self.cpu.set_state(WrestlerState.GRAPPLE_WEAK)

        if bool(player_won):
            self._log("You win the lock up and take control!")
            self.player.grapple_role = GrappleRole.OFFENSE
            self.cpu.grapple_role = GrappleRole.DEFENSE
        else:
            self._log("CPU wins the lock up and takes control!")
            self.player.grapple_role = GrappleRole.DEFENSE
            self.cpu.grapple_role = GrappleRole.OFFENSE

        self.selected_move = None
        self.selected_cards.clear()
        self._set_menu_stage("CATEGORIES")
        self._update_hud()

    def _lockup_minigame(self, *, on_done) -> None:
        """Kivy port of mechanics.lockup_minigame (PUSH/HOLD)."""
        scores = {"p": 0, "c": 0}
        done = {"flag": False}
        timeout_ev = {"ev": None}

        root = BoxLayout(orientation="horizontal", spacing=10, padding=[12, 12, 12, 12])
        left = BoxLayout(orientation="vertical", spacing=8)
        right = BoxLayout(orientation="vertical", spacing=8, size_hint_x=0.35)

        prompt = Label(
            text="LOCK UP\nGet closer to 15 without going over.",
            halign="left",
            valign="middle",
            color=COLOR_TEXT_PROMPT,
        )
        prompt.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))

        status = Label(
            text="YOU: 0   |   CPU: 0",
            color=COLOR_TEXT_SOFT,
            halign="left",
            valign="middle",
        )
        status.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))

        msg = Label(
            text="PUSH adds 1–6. HOLD lets CPU respond.",
            color=COLOR_TEXT_HINT,
            halign="left",
            valign="top",
        )
        msg.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))

        left.add_widget(prompt)
        left.add_widget(status)
        left.add_widget(msg)
        root.add_widget(left)
        root.add_widget(right)

        pop = Popup(title="Lock Up", content=root, size_hint=(0.92, 0.38), auto_dismiss=False)

        def refresh() -> None:
            status.text = f"YOU: {scores['p']}   |   CPU: {scores['c']}"

        def finish(player_won: bool, message: str) -> None:
            if done["flag"]:
                return
            done["flag"] = True
            msg.text = message
            if timeout_ev["ev"] is not None:
                try:
                    timeout_ev["ev"].cancel()
                except Exception:
                    pass

            def close_and_apply(_dt=0):
                try:
                    pop.dismiss()
                except Exception:
                    pass
                try:
                    on_done(bool(player_won))
                except Exception:
                    return

            Clock.schedule_once(close_and_apply, 0.55)

        def timeout(_dt):
            finish(False, "Time's up—position lost!")

        def push(_inst=None) -> None:
            if done["flag"]:
                return
            scores["p"] += random.randint(1, 6)
            refresh()
            if scores["p"] > 15:
                finish(False, "You over-committed and slipped!")

        def cpu_push_once() -> None:
            scores["c"] += random.randint(1, 6)
            refresh()

        def hold(_inst=None) -> None:
            if done["flag"]:
                return
            msg.text = f"You hold at {scores['p']}... CPU responds."

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

        b_push = Button(text="PUSH", background_normal="", background_color=COLOR_BTN_BASE)
        b_hold = Button(text="HOLD", background_normal="", background_color=COLOR_BTN_BASE)
        b_push.bind(on_release=push)
        b_hold.bind(on_release=hold)
        right.add_widget(b_push)
        right.add_widget(b_hold)

        refresh()
        timeout_ev["ev"] = Clock.schedule_once(timeout, 12.0)
        pop.open()

    def _on_card_click(self, instance):
        idx = int(getattr(instance, "card_index", -1))
        if idx < 0:
            return

        # Escape mode: tap-to-discard.
        if self._escape_mode is not None and bool(self._escape_mode.get("defender_is_player")):
            self._escape_play_card(idx)
            return

        if not self.selected_move:
            return

        hand = list(self.player.hand or [])
        if idx >= len(hand):
            return

        if idx in self.selected_cards:
            self.selected_cards.remove(idx)
            instance.opacity = 1.0
        else:
            if len(self.selected_cards) >= 2:
                self._log("Max 2 cards.")
                return

            # Defensive: only <=5
            if self.selected_move == "Defensive" and int(hand[idx].value) > 5:
                self._log("Defensive can only discard cards value ≤ 5.")
                return

            # Normal: if choosing second card, must be doubles
            if self.selected_move != "Defensive" and len(self.selected_cards) == 1:
                first_idx = next(iter(self.selected_cards))
                if int(hand[first_idx].value) != int(hand[idx].value):
                    self._log("Two cards must be doubles (same value).")
                    return

            self.selected_cards.add(idx)
            instance.opacity = 0.55

        self._update_play_button()

    def _update_play_button(self):
        self._update_control_bar()

    def _update_control_bar(self) -> None:
        # Return visibility
        show_return = self._menu_stage in {"MOVES", "HYPE_SHOP"}
        self.return_btn.disabled = not show_return
        self.return_btn.opacity = 1.0 if show_return else 0.0

        # Hint
        if self._menu_stage == "CATEGORIES":
            self.hint_label.text = "Pick a category."
        elif self._menu_stage == "HYPE_SHOP":
            self.hint_label.text = "Spend hype for a boost."
        elif self._menu_stage == "MOVES":
            if not self.selected_move:
                self.hint_label.text = "Pick a move."
            elif self.selected_move == "Defensive":
                self.hint_label.text = "Defensive: discard 0–2 cards (≤5)."
            else:
                self.hint_label.text = "Select 1 card (or doubles), then PLAY."
        elif self._menu_stage == "ESCAPE":
            self.hint_label.text = "ESCAPE! Tap a card to discard."
        else:
            self.hint_label.text = ""

        # Play button enable + cost text
        enabled = False
        cost = 0
        move_name = self.selected_move

        if self.game_over:
            enabled = False
        elif self._menu_stage == "ESCAPE":
            enabled = False
        elif self._menu_stage != "MOVES":
            enabled = False
        elif not move_name:
            enabled = False
        else:
            cards = self._selected_player_cards()
            selected_count = len(self.selected_cards)
            if move_name == "Defensive":
                enabled = (selected_count in {0, 1, 2}) and (selected_count == 0 or bool(cards))
            else:
                enabled = (selected_count in {1, 2}) and bool(cards)

            if enabled:
                cost = self._effective_cost(self.player, move_name, cards)
                if int(self.player.grit) < int(cost):
                    enabled = False

        self.play_btn.disabled = not enabled
        if enabled:
            self.play_btn.background_color = get_color_from_hex(COLOR_HEX_PLAY_ENABLED)
            self.play_btn.text = f"PLAY\n({cost} Grit)"
        else:
            # Still show a cost estimate if we can.
            if move_name:
                cards = self._selected_player_cards()
                est = self._effective_cost(self.player, move_name, cards)
                self.play_btn.text = f"PLAY\n({est} Grit)"
            else:
                self.play_btn.text = "PLAY"
            self.play_btn.background_color = get_color_from_hex(COLOR_HEX_PLAY_DISABLED)

    def _on_play_click(self, instance):
        self._submit_cards()

    def _submit_cards(self) -> None:
        if self.game_over:
            return
        if self._escape_mode is not None:
            return
        if self._menu_stage != "MOVES":
            return
        if not self.selected_move:
            self._log("Pick a move first.")
            return

        if not self._move_is_legal(self.selected_move, self.player, self.cpu):
            self._log(f"{self.selected_move} is no longer legal.")
            self.selected_move = None
            self.selected_cards.clear()
            self._update_control_bar()
            return

        p_cards = self._selected_player_cards()
        if self.selected_move == "Defensive":
            if len(p_cards) > 2:
                self._log("Defensive: discard up to 2 cards (value ≤ 5).")
                return
        else:
            if not p_cards:
                self._log("Select 1 card (or doubles).")
                return

        total_cost = self._effective_cost(self.player, self.selected_move, p_cards)
        if int(self.player.grit) < int(total_cost):
            self._log("Not enough grit (move + card cost).")
            return

        self._cpu_buy_buffs()
        c_move = self._cpu_choose_move()
        c_cards = self._cpu_choose_cards(c_move)
        # Degrade AI card choice if it somehow can't afford.
        c_total = self._effective_cost(self.cpu, c_move, c_cards)
        if int(self.cpu.grit) < int(c_total):
            hand = list(self.cpu.hand or [])
            hand.sort(key=lambda c: int(c.value))
            c_cards = []
            for c in hand:
                test = self._effective_cost(self.cpu, c_move, [c])
                if int(self.cpu.grit) >= int(test):
                    c_cards = [c]
                    break

        self._resolve_clash(self.selected_move, p_cards, c_move, c_cards)

    def _on_return_click(self, instance):
        self.selected_move = None
        self.selected_cards.clear()
        self._set_menu_stage("CATEGORIES")

    # -------------------------------------------------------------------------
    # ESCAPE MODE UI
    # -------------------------------------------------------------------------

    def _render_escape_ui(self):
        self._render_moves_ui()
        self._update_control_bar()

if __name__ == "__main__":
    WrestleApp().run()
