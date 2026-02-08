from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
import random
import math
import os
import re
from datetime import datetime

# Import your existing logic
from wrestler import Wrestler, WrestlerState, GrappleRole, MAX_HEALTH
from moves_db import MOVES
from wrestler_roster import ROSTER, DEFAULT_CPU_PROFILE, DEFAULT_PLAYER_PROFILE

# Stable move IDs (slugs)
MOVE_DEFENSIVE = "def_defensive"
MOVE_REST = "util_rest"
MOVE_GROGGY_RECOVERY = "util_groggy_recovery"
MOVE_TAUNT = "util_taunt"
MOVE_SLOW_STAND_UP = "util_slow_stand_up"
MOVE_KIP_UP = "util_kip_up"
MOVE_LOCK_UP = "grap_lock_up"
MOVE_FIGHT_FOR_CONTROL = "grap_fight_for_control"
MOVE_SHOVE_OFF = "grap_shove_off"
MOVE_STOP_SHORT = "util_stop_short"
MOVE_CLIMB_DOWN = "air_climb_down"
MOVE_DESPERATION_PUNCH = "strike_desperation_punch"
MOVE_BITE = "strike_bite"
MOVE_FOREARM_CLUB = "strike_forearm_club"
MOVE_KNEE_TO_GUT = "strike_knee_to_gut"
MOVE_EAR_CLAP = "strike_ear_clap"
MOVE_GUT_PUNCH = "strike_gut_punch"
MOVE_CHARGE = "util_charge"
MOVE_RUNNING_CLOTHESLINE = "strike_running_clothesline"
MOVE_TRIP = "strike_trip"
MOVE_REGAIN_BALANCE = "util_regain_balance"

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

# Momentum (player advantage): -5..+5
COLOR_HEX_MOMENTUM_POS = "00c853"
COLOR_HEX_MOMENTUM_NEG = "ff5555"
COLOR_HEX_MOMENTUM_NEU = "bbbbbb"

# Control bar accents
COLOR_HEX_RETURN = "#6200ea"
COLOR_HEX_PLAY_ENABLED = "#00c853"
COLOR_HEX_PLAY_DISABLED = "#444444"

# Markup/log colors (hex)
COLOR_HEX_NAME_YOU = "55ff55"
COLOR_HEX_NAME_CPU = "55ffff"
COLOR_HEX_DAMAGE = "ff5555"
COLOR_HEX_STRIKE_LOG = "ff5555"
COLOR_HEX_GRAPPLE_LOG = "55aaff"
COLOR_HEX_SETUP_LOG = "cccccc"
COLOR_HEX_DEFENSIVE_LOG = "bbbbbb"

# HP status colors (Fog of War)
COLOR_HEX_HP_OPTIMAL = "55ff55"
COLOR_HEX_HP_STABLE = "b9ff3b"
COLOR_HEX_HP_STRAINED = "ffff55"
COLOR_HEX_HP_EXHAUSTED = "ffb055"
COLOR_HEX_HP_CRITICAL = "ff5555"

# TYPE COLORS (Used for button hints)
COLOR_STRIKE    = (0.40, 0.05, 0.05, 1)   # Dark Red
COLOR_GRAPPLE   = (0.05, 0.05, 0.40, 1)   # Dark Blue
COLOR_AERIAL    = (0.40, 0.40, 0.05, 1)   # Dark Yellow
COLOR_SUBMIT    = (0.05, 0.40, 0.05, 1)   # Dark Green

COLOR_DEFENSIVE = (0.10, 0.10, 0.10, 1)
COLOR_FINISHER = (0.83, 0.69, 0.22, 1)

COLOR_HYPE_SHOP = (0.28, 0.17, 0.0, 1)

# Combo-chain highlight (gold)
COLOR_CHAIN = (0.92, 0.74, 0.18, 1)

# Card selection highlight (avoid using green; it conflicts with HP/log accents)
COLOR_CARD_SELECTED = (1.00, 0.20, 0.75, 1)

# ==========================================
#  🎛️ TUNING KNOBS
# ==========================================
TUNING_ENABLE_PASSIVE_REGEN = True
TUNING_GRIT_PASSIVE_REGEN = 2  # Grit recovered if you spent 0 this turn

# Botch mechanic: injured wrestlers may fail Attack moves.
# Chance (%) = Missing_HP / TUNING_BOTCH_DIVISOR
TUNING_BOTCH_DIVISOR = 4

# True ties (score AND strength tied): chance of a classic double-down spot.
TUNING_DOUBLE_DOWN_ON_TRUE_TIE_CHANCE = 0.25

# True ties: if clash score and Strength are tied, sometimes both crash.
TUNING_DOUBLE_DOWN_ON_TRUE_TIE_CHANCE = 0.25

# Grapple-break strikes: if defender wins the clash by this margin while using a
# grapple-defense Strike, the grapple breaks and both reset to STANDING.
GRAPPLE_BREAK_STRIKE_VALUE = 3

# Log readability
LOG_EXCHANGE_SEPARATOR = "────────────────────────"

# Clash reveal tuning
REVEAL_LOSER_MOVE_NAME = True
REVEAL_LOSER_CARDS = False

# Optional debugging: show score math in the log
REVEAL_SCORE_BREAKDOWN = True

# Damage tuning
DOUBLES_DAMAGE_MODIFIER = 1.25
SUBMISSION_TICK_DAMAGE = 4

# AKI-style DAZED tuning (probabilistic, HP-based)
TUNING_DAZE_HP_THRESHOLD = 80       # HP% above this = immune to Daze
TUNING_DAZE_CHANCE_SCALAR = 1.5     # Lower HP => higher chance
TUNING_DAZE_MAX_TURNS = 3           # Max duration applied
TUNING_DAZE_WAKE_DAMAGE = 15        # If hit this hard while dazed, wake up instantly

# Strike knockdowns: for strike moves that *can* ground a standing/running opponent,
# chance = missing_hp_pct * 100 * scalar (clamped to 0..100).
TUNING_STRIKE_KNOCKDOWN_CHANCE_SCALAR = 1.0

# Momentum tuning
MOMENTUM_MAX_ABS = 5
MOMENTUM_WIN_DELTA = 1
MOMENTUM_GAIN_ON_ATTACKS_ONLY = True
MOMENTUM_REVERSAL_RESET_THRESHOLD = 4

# Momentum -> clash score modifier mapping
# 1-3 = +1, 4-5 = +2 (signed)
MOMENTUM_SCORE_TIER1_MAX = 3
MOMENTUM_SCORE_TIER1_BONUS = 1
MOMENTUM_SCORE_TIER2_MAX = 5
MOMENTUM_SCORE_TIER2_BONUS = 2

# CPU grounded behavior
CPU_GETUP_HEALTHY_PCT = 0.60
CPU_GETUP_BONUS_HEALTHY = 45
CPU_UPKICK_PENALTY_WHEN_HEALTHY = 22
CPU_REST_BONUS_WHEN_HURT = 28
CPU_REST_HURT_PCT = 0.45

# Auto-grit: prevent high-damage 0-cost moves from being "free".
TUNING_AUTO_GRIT_ON_DAMAGE = True
AUTO_GRIT_ONLY_WHEN_BASE_COST_ZERO = True
AUTO_GRIT_DAMAGE_THRESHOLD = 6
AUTO_GRIT_DAMAGE_STEP = 4
AUTO_GRIT_PER_STEP = 1

# ==========================================
#  ✨ VFX (Clash / Damage Overlay)
# ==========================================
# Overlay alpha at start (0..1)
VFX_OVERLAY_ALPHA = 0.22
# Base fade duration in seconds (no damage)
VFX_OVERLAY_FADE_BASE = 0.35
# Max fade duration in seconds (heavy damage)
VFX_OVERLAY_FADE_MAX = 1.10
# Damage threshold that maps to max fade
VFX_OVERLAY_DAMAGE_CAP = 20

# ==========================================
#  📏 DIMENSIONS & LAYOUT
# ==========================================
# Use dp() so the UI feels consistent across desktop and tall phones.

# Fixed bars (header/footer pattern)
# NOTE: HUD must be tall enough to fit HP + grit/hype meters without overlap.
HUD_HEIGHT = dp(165)
CONTROL_HEIGHT = dp(60)
HAND_HEIGHT = dp(80)

# Arena proportions (only applied within the flexible middle arena)
# More room for the match log; less dead space in the move grid.
ARENA_LOG_PCT = 0.45
ARENA_MOVES_PCT = 0.55

# Button sizing
BTN_HEIGHT_CATEGORY = dp(56)
BTN_HEIGHT_MOVE = dp(72)
BTN_HEIGHT_SHOP = dp(72)

# Spacing/padding (optional convenience)
PAD_SM = dp(6)
PAD_XS = dp(4)
GAP_SM = dp(8)
GAP_XS = dp(4)

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


class CenteredBar(Widget):
    """Meter bar that fills from center.

    Used for momentum: positive (player-favoring) fills LEFT, negative fills RIGHT.
    """

    value_signed = NumericProperty(0)  # -max_abs..+max_abs
    max_abs = NumericProperty(5)
    bar_color = ListProperty([1, 1, 1, 1])
    back_color = ListProperty([0.12, 0.12, 0.12, 1])
    center_color = ListProperty([0.25, 0.25, 0.25, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            from kivy.graphics import Color, Rectangle

            self._back_color_instr = Color(*self.back_color)
            self._back_rect = Rectangle(pos=self.pos, size=self.size)

            self._center_color_instr = Color(*self.center_color)
            self._center_rect = Rectangle(pos=self.pos, size=(dp(2), self.height))

            self._bar_color_instr = Color(*self.bar_color)
            self._bar_rect = Rectangle(pos=self.pos, size=(0, self.height))

        self.bind(pos=self._redraw, size=self._redraw)
        self.bind(value_signed=self._redraw, max_abs=self._redraw)
        self.bind(bar_color=self._redraw_colors, back_color=self._redraw_colors, center_color=self._redraw_colors)

    def _redraw_colors(self, *_args):
        self._back_color_instr.rgba = self.back_color
        self._bar_color_instr.rgba = self.bar_color
        self._center_color_instr.rgba = self.center_color
        self._redraw()

    def _redraw(self, *_args):
        self._back_rect.pos = self.pos
        self._back_rect.size = self.size

        cx = float(self.x) + (float(self.width) / 2.0)
        self._center_rect.pos = (cx - dp(1), self.y)
        self._center_rect.size = (dp(2), self.height)

        denom = float(self.max_abs) if float(self.max_abs) > 0 else 1.0
        pct = max(0.0, min(1.0, abs(float(self.value_signed)) / denom))
        half = float(self.width) / 2.0
        bar_w = half * pct

        if float(self.value_signed) >= 0:
            # Positive momentum: fill LEFT toward player.
            self._bar_rect.pos = (cx - bar_w, self.y)
        else:
            # Negative momentum: fill RIGHT toward CPU.
            self._bar_rect.pos = (cx, self.y)
        self._bar_rect.size = (bar_w, self.height)


class ScreenFlash(Widget):
    """Full-screen overlay flash that fades out."""

    alpha = NumericProperty(0.0)
    rgba = ListProperty([1, 1, 1, 0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._fade_ev = None
        self._t = 0.0
        self._dur = 0.5
        with self.canvas:
            from kivy.graphics import Color, Rectangle

            self._color = Color(1, 1, 1, 0)
            self._rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._redraw, size=self._redraw)
        self.bind(alpha=self._apply)
        self.bind(rgba=self._apply)

    def _redraw(self, *_args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _apply(self, *_args):
        r, g, b, _a = (list(self.rgba) + [0, 0, 0, 0])[:4]
        self._color.rgba = (float(r), float(g), float(b), float(self.alpha))

    def flash(self, *, rgb: tuple[float, float, float], duration: float) -> None:
        if self._fade_ev is not None:
            try:
                self._fade_ev.cancel()
            except Exception:
                pass
            self._fade_ev = None

        self.rgba = [float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0]
        self.alpha = float(VFX_OVERLAY_ALPHA)
        self._t = 0.0
        self._dur = max(0.05, float(duration))

        def step(dt: float) -> None:
            self._t += float(dt)
            p = min(1.0, self._t / max(0.001, self._dur))
            # Linear fade to 0
            self.alpha = float(VFX_OVERLAY_ALPHA) * (1.0 - p)
            if p >= 1.0:
                self.alpha = 0.0
                if self._fade_ev is not None:
                    try:
                        self._fade_ev.cancel()
                    except Exception:
                        pass
                    self._fade_ev = None

        self._fade_ev = Clock.schedule_interval(step, 1 / 60.0)


class BorderedButton(Button):
    """Button with an optional border highlight (used for selections)."""

    border_color = ListProperty([1, 1, 1, 1])
    border_width = NumericProperty(2.0)
    show_border = BooleanProperty(False)
    auto_wrap = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Mobile-friendly text behavior: wrap within bounds and center.
        # Individual callers can override these properties via kwargs.
        try:
            if not hasattr(self, "halign") or self.halign is None:
                self.halign = "center"
            if not hasattr(self, "valign") or self.valign is None:
                self.valign = "middle"
        except Exception:
            pass

        try:
            # Provide some padding so glyphs don't hit edges.
            if not getattr(self, "padding", None):
                self.padding = [dp(6), dp(6)]
        except Exception:
            pass

        def _fit_text(*_a) -> None:
            try:
                if not bool(getattr(self, "auto_wrap", True)):
                    self.text_size = (None, None)
                    return
                pad_x = dp(12)
                pad_y = dp(10)
                self.text_size = (max(0, self.width - pad_x), max(0, self.height - pad_y))
            except Exception:
                pass

        self.bind(size=_fit_text)
        self.bind(pos=_fit_text)
        self.bind(text=_fit_text)
        self.bind(auto_wrap=_fit_text)
        _fit_text()

        with self.canvas.after:
            from kivy.graphics import Color, Line

            self._border_color_instr = Color(1, 1, 1, 0)
            self._border_line = Line(rectangle=(self.x, self.y, self.width, self.height), width=float(self.border_width))

        self.bind(pos=self._redraw_border, size=self._redraw_border)
        self.bind(border_color=self._redraw_border, border_width=self._redraw_border, show_border=self._redraw_border)
        self._redraw_border()

    def _redraw_border(self, *_args) -> None:
        rgba = list(self.border_color) if self.border_color else [1, 1, 1, 1]
        rgba = (rgba + [1, 1, 1, 1])[:4]
        if not bool(self.show_border):
            rgba[3] = 0.0
        self._border_color_instr.rgba = [float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3])]
        self._border_line.rectangle = (float(self.x), float(self.y), float(self.width), float(self.height))
        self._border_line.width = float(self.border_width)

class WrestleApp(App):
    def build(self):
        Window.clearcolor = COLOR_BG_MAIN

        # --- Game Objects ---
        p_prof = dict(ROSTER.get(DEFAULT_PLAYER_PROFILE, {}))
        c_prof = dict(ROSTER.get(DEFAULT_CPU_PROFILE, {}))
        self.player = Wrestler("YOU", True, profile=p_prof)
        self.cpu = Wrestler("CPU", False, profile=c_prof)

        # Buffs (simple flags; stored on wrestler objects)
        self.player.lockup_edge_ready = False
        self.cpu.lockup_edge_ready = False
        
        # Game State
        self.game_over = False
        self._last_cpu_mode: str | None = None
        self.turn = "player"
        self._escape_mode: dict | None = None
        self.selected_cards: set[int] = set()
        self.selected_move: str | None = None
        self._menu_stage: str = "CATEGORIES"  # CATEGORIES | MOVES | HYPE_SHOP | ESCAPE
        self._selected_category: str | None = None

        # UX: avoid confusion when cards are tapped before a move is selected.
        self._card_tap_hint_shown: bool = False

        # Log capture (exportable)
        self._log_lines: list[str] = []
        self._match_started_at = datetime.now()

        # Momentum: -5..+5 (positive favors the player)
        self.momentum: int = 0
        
        # --- ROOT LAYOUT ---
        root = FloatLayout()
        self.root = root

        main = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self._main = main

        # 1. HUD (Top)
        hud = BoxLayout(orientation='vertical', size_hint_y=None, height=HUD_HEIGHT, padding=PAD_SM, spacing=dp(5))

        self.state_label = Label(
            text="[b]STATE:[/b] STANDING (NEUTRAL)  |  CPU: STANDING (NEUTRAL)",
            markup=True,
            color=COLOR_TEXT_MAIN,
            size_hint_y=None,
            height=dp(24),
            font_size="13sp",
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.state_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        hud.add_widget(self.state_label)
        
        hp_row = BoxLayout(orientation='horizontal', spacing=GAP_SM, size_hint_y=None, height=dp(54))
        left_hp = BoxLayout(orientation='vertical')
        right_hp = BoxLayout(orientation='vertical')
        self.player_hp_label = Label(
            text="YOU HP: 100",
            color=COLOR_HP_PLAYER,
            markup=True,
            size_hint_y=None,
            height=dp(16),
            halign="center",
            valign="middle",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.cpu_hp_label = Label(
            text="CPU HP: 100",
            color=COLOR_HP_CPU,
            markup=True,
            size_hint_y=None,
            height=dp(16),
            halign="center",
            valign="middle",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.player_hp_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))
        self.cpu_hp_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))

        self.player_state_small = Label(
            text="STATE: STANDING",
            color=COLOR_TEXT_SOFT,
            size_hint_y=None,
            height=dp(14),
            font_size="11sp",
            halign="center",
            valign="middle",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.cpu_state_small = Label(
            text="STATE: STANDING",
            color=COLOR_TEXT_SOFT,
            size_hint_y=None,
            height=dp(14),
            font_size="11sp",
            halign="center",
            valign="middle",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.player_state_small.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))
        self.cpu_state_small.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))
        self.player_hp_bar = ProgressBar(max=MAX_HEALTH, value=MAX_HEALTH, size_hint_y=None, height=dp(14))
        self.cpu_hp_bar = ProgressBar(max=MAX_HEALTH, value=MAX_HEALTH, size_hint_y=None, height=dp(14))
        left_hp.add_widget(self.player_hp_label)
        left_hp.add_widget(self.player_state_small)
        left_hp.add_widget(self.player_hp_bar)
        right_hp.add_widget(self.cpu_hp_label)
        right_hp.add_widget(self.cpu_state_small)
        right_hp.add_widget(self.cpu_hp_bar)
        hp_row.add_widget(left_hp)
        hp_row.add_widget(right_hp)

        # Momentum row
        mom_green = get_color_from_hex(COLOR_HEX_MOMENTUM_POS)
        self.momentum_label = Label(
            text=f"[color={COLOR_HEX_MOMENTUM_NEU}]MOM 0[/color]",
            markup=True,
            size_hint_y=None,
            height=dp(16),
            halign="center",
            valign="middle",
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.momentum_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))
        self.momentum_bar = CenteredBar(size_hint_y=None, height=dp(8), max_abs=int(MOMENTUM_MAX_ABS), value_signed=0, bar_color=mom_green)
        mom_box = BoxLayout(orientation='vertical', spacing=dp(2), size_hint_y=None, height=dp(28))
        mom_box.add_widget(self.momentum_label)
        mom_box.add_widget(self.momentum_bar)

        self.fire_up_btn = Button(
            text="FIRE UP!",
            size_hint_x=0.28,
            size_hint_y=None,
            height=dp(28),
            background_normal="",
            background_color=COLOR_BTN_BASE,
            disabled=True,
        )
        self.fire_up_btn.bind(on_release=self._on_fire_up_click)

        mom_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(28))
        mom_row.add_widget(mom_box)
        mom_row.add_widget(self.fire_up_btn)
        
        meters_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(82))

        purple = get_color_from_hex(COLOR_HEX_GRIT)
        orange = get_color_from_hex(COLOR_HEX_HYPE)

        # Player meters (left)
        p_box = BoxLayout(orientation='vertical', spacing=dp(2))
        self.p_grit_label = Label(
            text=f"[color={COLOR_HEX_GRIT}]GRIT 0/0[/color]",
            markup=True,
            size_hint_y=None,
            height=dp(16),
            halign="center",
            valign="middle",
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.p_grit_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))
        self.p_grit_bar = ColoredBar(size_hint_y=None, height=dp(8), max_value=self.player.max_grit, value=self.player.grit, bar_color=purple)
        self.p_hype_label = Label(
            text=f"[color={COLOR_HEX_HYPE}]HYPE 0/100[/color]",
            markup=True,
            size_hint_y=None,
            height=dp(16),
            halign="center",
            valign="middle",
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.p_hype_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))
        self.p_hype_bar = ColoredBar(size_hint_y=None, height=dp(8), max_value=100, value=self.player.hype, bar_color=orange)
        self.p_nums = Label(
            text="",
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=dp(12),
            halign="left",
            valign="middle",
            font_size="10sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.p_nums.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        self.p_limbs = Label(
            text="",
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=dp(12),
            halign="left",
            valign="middle",
            font_size="10sp",
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
        c_box = BoxLayout(orientation='vertical', spacing=dp(2))
        self.c_grit_label = Label(
            text=f"[color={COLOR_HEX_GRIT}]GRIT 0/0[/color]",
            markup=True,
            size_hint_y=None,
            height=dp(16),
            halign="center",
            valign="middle",
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.c_grit_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))
        self.c_grit_bar = ColoredBar(size_hint_y=None, height=dp(8), max_value=self.cpu.max_grit, value=self.cpu.grit, bar_color=purple)
        self.c_hype_label = Label(
            text=f"[color={COLOR_HEX_HYPE}]HYPE 0/100[/color]",
            markup=True,
            size_hint_y=None,
            height=dp(16),
            halign="center",
            valign="middle",
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.c_hype_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))
        self.c_hype_bar = ColoredBar(size_hint_y=None, height=dp(8), max_value=100, value=self.cpu.hype, bar_color=orange)
        self.c_nums = Label(
            text="",
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=dp(12),
            halign="left",
            valign="middle",
            font_size="10sp",
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.c_nums.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))
        self.c_limbs = Label(
            text="",
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=dp(12),
            halign="left",
            valign="middle",
            font_size="10sp",
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
        hud.add_widget(mom_row)
        hud.add_widget(meters_row)

        # 2. ARENA (Middle)
        arena_box = BoxLayout(orientation='vertical', size_hint_y=1)

        # A0. Log Controls
        log_controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), padding=[PAD_SM, 0, PAD_SM, 0])
        export_btn = Button(
            text="EXPORT LOG",
            background_color=COLOR_BTN_BASE,
            background_normal="",
            size_hint_x=None,
            width=dp(120),
        )
        export_btn.bind(on_release=self._export_match_log)
        log_controls.add_widget(export_btn)
        arena_box.add_widget(log_controls)
        
        # A. Game Log (Top of Arena)
        self.log_scroll = ScrollView(size_hint_y=ARENA_LOG_PCT)
        self.log_scroll.do_scroll_x = False
        self.log_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=PAD_SM, spacing=dp(2))
        self.log_layout.bind(minimum_height=self.log_layout.setter('height'))
        self.log_scroll.add_widget(self.log_layout)
        self.log_scroll.bind(width=self._sync_log_width)
        arena_box.add_widget(self.log_scroll)

        # B. Move List (Bottom of Arena) — 3-column grid for mobile density
        self.move_scroll = ScrollView(size_hint_y=ARENA_MOVES_PCT)
        self.move_list_layout = GridLayout(cols=3, spacing=PAD_SM, padding=[dp(10), dp(10), dp(10), dp(10)], size_hint_y=None)
        self.move_list_layout.bind(minimum_height=self.move_list_layout.setter('height'))
        self.move_scroll.add_widget(self.move_list_layout)
        arena_box.add_widget(self.move_scroll)
        
        main.add_widget(hud)
        main.add_widget(arena_box)

        # 3. CONTROL BAR
        controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=CONTROL_HEIGHT, spacing=GAP_SM, padding=[PAD_SM, PAD_XS, PAD_SM, PAD_XS])
        
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
            font_size="12sp",
            shorten=True,
            shorten_from="right",
            max_lines=2,
        )
        self.hint_label.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, inst.height)))

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
        main.add_widget(controls)

        # 4. HAND (Bottom)
        self.hand_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=HAND_HEIGHT, spacing=dp(4), padding=[PAD_SM, PAD_XS, PAD_SM, PAD_SM])
        main.add_widget(self.hand_layout)

        root.add_widget(main)

        # VFX overlay (must be last to draw above everything)
        self._flash = ScreenFlash(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        root.add_widget(self._flash)

        # Initial Start
        self._start_turn("player")
        return root

    def _flash_clash(self, *, outcome: str, damage: int = 0) -> None:
        """outcome: 'player' | 'cpu' | 'neutral'"""
        if not hasattr(self, "_flash"):
            return
        dmg = max(0, int(damage))
        cap = max(1, int(VFX_OVERLAY_DAMAGE_CAP))
        p = min(1.0, float(dmg) / float(cap))
        dur = float(VFX_OVERLAY_FADE_BASE) + (float(VFX_OVERLAY_FADE_MAX) - float(VFX_OVERLAY_FADE_BASE)) * p

        if outcome == "player":
            rgb = (0.0, 0.78, 0.30)
        elif outcome == "cpu":
            rgb = (0.95, 0.20, 0.20)
        else:
            rgb = (0.65, 0.65, 0.65)
        try:
            self._flash.flash(rgb=rgb, duration=dur)
        except Exception:
            pass

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

        # Reset per-beat UX hints.
        self._card_tap_hint_shown = False

        # Expire combo windows at the start of the next beat.
        for w in (self.player, self.cpu):
            if int(getattr(w, "chain_turns_remaining", 0)) > 0:
                w.chain_turns_remaining -= 1
                if int(w.chain_turns_remaining) <= 0:
                    w.chain_turns_remaining = 0
                    w.chain_window = None
                    w.chain_potency = 0

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
        self.selected_move = MOVE_REST
        self.selected_cards.clear()
        self._submit_cards()

    def _log(self, text: str):
        try:
            self._log_lines.append(str(text))
        except Exception:
            pass
        lbl = Label(
            text=f"> {text}",
            markup=True,
            size_hint_x=1,
            size_hint_y=None,
            halign="left",
            valign="top",
            color=COLOR_TEXT_MAIN,
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

    def _strip_kivy_markup(self, s: str) -> str:
        try:
            return re.sub(r"\[[^\]]+\]", "", str(s))
        except Exception:
            return str(s)

    def _export_match_log(self, _inst=None) -> None:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except Exception:
            base_dir = os.getcwd()

        out_dir = os.path.join(base_dir, "match_logs")
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            pass

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(out_dir, f"match_log_{ts}.txt")

        try:
            header = []
            header.append("WrestleText Match Log")
            try:
                started = getattr(self, "_match_started_at", None)
                if started:
                    header.append(f"Started: {started}")
            except Exception:
                pass
            header.append(f"YOU vs CPU")
            header.append("")

            lines = [self._strip_kivy_markup(x) for x in (self._log_lines or [])]
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(header + ["> " + ln for ln in lines]))
            self._log(f"Log exported to: {out_path}")
        except Exception:
            self._log("Log export failed.")

    def _log_separator(self) -> None:
        self._log(LOG_EXCHANGE_SEPARATOR)

    def _c(self, text: str, hex_color: str) -> str:
        return f"[color={hex_color}]{text}[/color]"

    def _fmt_name(self, w: Wrestler) -> str:
        if bool(getattr(w, "is_player", False)):
            return self._c(str(w.name), COLOR_HEX_NAME_YOU)
        return self._c(str(w.name), COLOR_HEX_NAME_CPU)

    def _calc_daze_application(self, target: Wrestler, move_data: dict) -> int:
        if not bool(move_data.get("can_daze", False)):
            return 0
        try:
            hp_pct = float(target.hp_pct()) * 100.0
        except Exception:
            return 0

        thr = float(TUNING_DAZE_HP_THRESHOLD)
        if hp_pct > thr:
            return 0

        diff = max(0.0, thr - hp_pct)
        chance = float(diff) * float(TUNING_DAZE_CHANCE_SCALAR)
        if float(random.uniform(0.0, 100.0)) >= float(chance):
            return 0

        max_turns = max(1, int(TUNING_DAZE_MAX_TURNS))
        severity = 0.0 if thr <= 0 else max(0.0, min(1.0, diff / thr))
        if max_turns == 1:
            return 1
        if max_turns == 2:
            return 2 if random.random() < (0.25 + 0.55 * severity) else 1

        p3 = max(0.0, min(0.60, 0.10 + 0.45 * severity))
        p2 = max(0.0, min(0.75, 0.30 + 0.40 * severity))
        r = random.random()
        if r < p3:
            return 3
        if r < (p3 + p2):
            return 2
        return 1

    def _fmt_damage(self, amount: int) -> str:
        return self._c(f"{int(amount)} dmg", COLOR_HEX_DAMAGE)

    def _fmt_move(self, move_name: str) -> str:
        mv = MOVES.get(move_name, {})
        disp = str(mv.get("name", move_name))
        t = str(mv.get("type", "Setup"))
        if move_name == MOVE_DEFENSIVE or t == "Defensive":
            return self._c(disp, COLOR_HEX_DEFENSIVE_LOG)
        if t == "Strike":
            return self._c(disp, COLOR_HEX_STRIKE_LOG)
        if t in {"Grapple", "Pin", "Submission"}:
            return self._c(disp, COLOR_HEX_GRAPPLE_LOG)
        return self._c(disp, COLOR_HEX_SETUP_LOG)

    def _fmt_cards(self, cards: list | None) -> str:
        if not cards:
            return "Cards: -"
        vals = ", ".join(str(int(c.value)) for c in cards)
        return f"Cards: {vals}"

    def _get_hp_status(self, current_hp: int) -> str:
        pct = 0.0
        try:
            pct = (float(current_hp) / float(MAX_HEALTH)) * 100.0
        except Exception:
            pct = 0.0

        if pct >= 80.0:
            return self._c("OPTIMAL", COLOR_HEX_HP_OPTIMAL)
        if pct >= 60.0:
            return self._c("STABLE", COLOR_HEX_HP_STABLE)
        if pct >= 40.0:
            return self._c("STRAINED", COLOR_HEX_HP_STRAINED)
        if pct >= 20.0:
            return self._c("EXHAUSTED", COLOR_HEX_HP_EXHAUSTED)
        return self._c("CRITICAL", COLOR_HEX_HP_CRITICAL)

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
        # Order matters: handle possessives before plain "You" to avoid corrupting "Your".
        out = out.replace("Your", attacker_poss.capitalize())
        out = out.replace("your", attacker_poss)
        out = out.replace("You", attacker_ref)
        out = out.replace("They", attacker_ref)
        out = out.replace("Their", attacker_poss.capitalize())
        out = out.replace(" them ", f" {defender_ref} ")
        out = out.replace(" Them ", f" {defender_ref_cap} ")
        out = out.replace(" their ", f" {defender_poss} ")
        out = out.replace(" Their ", f" {defender_poss.capitalize()} ")
        return out

    def _momentum_advantage_for(self, wrestler: Wrestler) -> int:
        """Return signed momentum advantage from the wrestler's perspective.

        Global momentum is stored as player-favoring (positive => player advantage).
        """
        m = int(getattr(self, "momentum", 0) or 0)
        if wrestler is self.player:
            return m
        return -m

    def _move_req_momentum_min(self, move_name: str) -> int:
        try:
            return max(0, int(MOVES.get(str(move_name), {}).get("req_momentum_min", 0) or 0))
        except Exception:
            return 0

    def _has_momentum_for_move(self, wrestler: Wrestler, move_name: str) -> bool:
        req = int(self._move_req_momentum_min(move_name))
        if req <= 0:
            return True
        return int(self._momentum_advantage_for(wrestler)) >= int(req)

    def _move_display_name(self, move_name: str) -> str:
        mv = MOVES.get(str(move_name), {})
        disp = str(mv.get("name", move_name))
        req = int(self._move_req_momentum_min(move_name))
        if req > 0:
            disp = f"{disp}{'*' * req}"
        return disp

    def _move_is_legal(self, move_name: str, user: Wrestler, target: Wrestler, *, ignore_momentum_gate: bool = False) -> bool:
        mv = MOVES[move_name]
        ru = str(mv.get("req_user_state", "ANY"))
        rt = str(mv.get("req_target_state", "ANY"))

        # --- 0) Groggy gating ---
        user_groggy = bool(getattr(user, "is_groggy", False))
        if user_groggy and move_name != MOVE_GROGGY_RECOVERY:
            return False
        if (not user_groggy) and move_name == MOVE_GROGGY_RECOVERY:
            return False

        # --- 0b) Limb gating (hobbled: no running/aerial) ---
        try:
            user_hobbled = bool(user.is_hobbled())
        except Exception:
            user_hobbled = False
        if user_hobbled and move_name not in {MOVE_STOP_SHORT, MOVE_CLIMB_DOWN, MOVE_GROGGY_RECOVERY, MOVE_DEFENSIVE, MOVE_REST}:
            mtype = str(mv.get("type", "Setup"))
            if mtype == "Aerial" or ru in {"RUNNING", "TOP_ROPE"}:
                return False

        # Taunt: allow while you have offensive control in a grapple.
        try:
            if move_name == MOVE_TAUNT and user.is_in_grapple() and user.grapple_role == GrappleRole.OFFENSE:
                return True
        except Exception:
            pass

        # --- 1) User requirement (state + grapple role) ---
        if ru == "GRAPPLE_DEFENSE":
            if not (user.is_in_grapple() and user.grapple_role == GrappleRole.DEFENSE):
                return False
        elif ru == "GRAPPLE_OFFENSE":
            if not (user.is_in_grapple() and user.grapple_role == GrappleRole.OFFENSE):
                return False
        elif ru != "ANY":
            if ru in {"GRAPPLED", "GRAPPLE_ANY"}:
                if not user.is_in_grapple():
                    return False
            elif ru == "GRAPPLE_WEAK":
                # Allow certain "weak" grapple moves in STRONG as well.
                if user.state not in {WrestlerState.GRAPPLE_WEAK, WrestlerState.GRAPPLE_STRONG}:
                    return False
            elif user.state.value != ru:
                return False

        # --- 2) Target requirement ---
        if rt != "ANY":
            if rt in {"GRAPPLED", "GRAPPLE_ANY"}:
                if not target.is_in_grapple():
                    return False
            elif target.state.value != rt:
                return False

        user_adv = user.is_in_grapple() and (user.grapple_role == GrappleRole.OFFENSE)
        user_dis = user.is_in_grapple() and (user.grapple_role == GrappleRole.DEFENSE)

        if user_dis:
            if move_name not in {
                MOVE_FIGHT_FOR_CONTROL,
                MOVE_DEFENSIVE,
                MOVE_REST,
                MOVE_SHOVE_OFF,
                MOVE_DESPERATION_PUNCH,
                MOVE_BITE,
                MOVE_EAR_CLAP,
                MOVE_GUT_PUNCH,
                MOVE_FOREARM_CLUB,
                MOVE_KNEE_TO_GUT,
            }:
                return False

        if move_name == MOVE_DEFENSIVE:
            if user_adv:
                return False
            neutral_ok = (user.state == WrestlerState.STANDING and target.state == WrestlerState.STANDING)
            tossed_ok = (user.state == WrestlerState.TOSSED)
            grounded_ok = (user.state == WrestlerState.GROUNDED)
            if not (neutral_ok or user_dis or tossed_ok or grounded_ok):
                return False

        # --- Momentum gating ---
        if not bool(ignore_momentum_gate):
            if not self._has_momentum_for_move(user, move_name):
                return False

        return True

    def _auto_move_cost(self, move_name: str) -> int:
        # Never add hidden costs to core system/utility actions.
        if str(move_name) in {MOVE_LOCK_UP, MOVE_REST, MOVE_TAUNT, MOVE_DEFENSIVE, MOVE_FIGHT_FOR_CONTROL}:
            return 0
        if not bool(TUNING_AUTO_GRIT_ON_DAMAGE):
            return 0
        mv = MOVES.get(str(move_name), {})
        base_cost = int(mv.get("cost", 0))
        if bool(AUTO_GRIT_ONLY_WHEN_BASE_COST_ZERO) and base_cost != 0:
            return 0
        dmg = int(mv.get("damage", 0))
        if dmg < int(AUTO_GRIT_DAMAGE_THRESHOLD):
            return 0
        step = max(1, int(AUTO_GRIT_DAMAGE_STEP))
        per = max(0, int(AUTO_GRIT_PER_STEP))
        # threshold..(threshold+step-1) => +per, then +per each additional step.
        tiers = int(math.ceil(float(dmg - int(AUTO_GRIT_DAMAGE_THRESHOLD) + 1) / float(step)))
        return max(0, int(tiers) * int(per))

    def _move_base_cost(self, move_name: str) -> int:
        mv = MOVES.get(str(move_name), {})
        return int(mv.get("cost", 0)) + int(self._auto_move_cost(move_name))

    def _passes_moveset(self, wrestler: Wrestler, move_name: str) -> bool:
        # Keep parity with Tk version: universal safety options always allowed.
        universal = {
            MOVE_DEFENSIVE,
            MOVE_REST,
            MOVE_GROGGY_RECOVERY,
            MOVE_TAUNT,
            MOVE_LOCK_UP,
            MOVE_SHOVE_OFF,
            MOVE_SLOW_STAND_UP,
            MOVE_KIP_UP,
            MOVE_CLIMB_DOWN,
            MOVE_STOP_SHORT,
            MOVE_REGAIN_BALANCE,
        }
        if move_name in universal:
            return True
        if wrestler.moveset is None:
            return True
        return move_name in set(wrestler.moveset)

    def _available_moves(self, user: Wrestler, target: Wrestler, *, ignore_momentum_gate: bool = False) -> list[str]:
        names = [
            n
            for n in MOVES.keys()
            if self._move_is_legal(n, user, target, ignore_momentum_gate=ignore_momentum_gate)
            and self._passes_moveset(user, n)
        ]

        if user.state == WrestlerState.STANDING and target.state == WrestlerState.STANDING:
            allowed_names = {MOVE_LOCK_UP, MOVE_TAUNT, MOVE_DEFENSIVE}

            def neutral_ok(n: str) -> bool:
                mv = MOVES.get(n, {})
                t = str(mv.get("type", "Setup"))
                su = str(mv.get("set_user_state", ""))
                return (t == "Strike") or (n in allowed_names) or (t == "Setup" and su in {"RUNNING", "TOP_ROPE"})

            names = [n for n in names if neutral_ok(n)]
            if (
                MOVE_REST not in names
                and self._move_is_legal(MOVE_REST, user, target, ignore_momentum_gate=ignore_momentum_gate)
                and self._passes_moveset(user, MOVE_REST)
            ):
                names.append(MOVE_REST)

        def key(n: str) -> tuple[int, int, str]:
            t = str(MOVES[n].get("type", "Setup"))
            type_order = {"Defensive": 0, "Setup": 1, "Strike": 2, "Grapple": 3, "Aerial": 4, "Submission": 5, "Pin": 6}
            return (type_order.get(t, 99), int(self._move_base_cost(n)), n)

        return sorted(names, key=key)

    def _calc_clash_score(self, move_name: str, cards: list, *, card_bonus: int = 0) -> int:
        if move_name == MOVE_DEFENSIVE:
            return -1
        if not cards:
            return 0

        # Groggy Recovery: card values are capped at 7 for scoring (but you may discard any card).
        clamp7 = (str(move_name) == MOVE_GROGGY_RECOVERY)

        def v(c) -> int:
            try:
                raw = int(c.value)
            except Exception:
                raw = 0
            return min(7, raw) if clamp7 else raw

        doubles = bool(len(cards) == 2 and int(cards[0].value) == int(cards[1].value))
        same_color = bool(len(cards) == 2 and (not doubles) and str(cards[0].color) == str(cards[1].color))

        if doubles:
            base = int(v(cards[0])) + 5
        elif same_color:
            hi = max(int(v(cards[0])), int(v(cards[1])))
            base = min(10, int(hi) + 2)
        else:
            base = sum(int(v(c)) for c in cards)

        move_type = str(MOVES.get(move_name, {}).get("type", "Setup"))
        if doubles or same_color:
            base += max(int(cards[0].color_bonus(move_type)), int(cards[1].color_bonus(move_type)))
        else:
            base += sum(int(c.color_bonus(move_type)) for c in cards)

        base += int(card_bonus)
        base += int(MOVES.get(move_name, {}).get("clash_mod", 0))
        return int(base)

    def _selected_player_cards(self) -> list:
        hand = list(self.player.hand or [])
        idxs = sorted(self.selected_cards)
        cards = [hand[i] for i in idxs if 0 <= i < len(hand)]

        if self.selected_move == MOVE_REST:
            return []

        if self.selected_move == MOVE_DEFENSIVE:
            if any(int(c.value) > 5 for c in cards):
                return []
            return cards

        if self.selected_move == MOVE_GROGGY_RECOVERY:
            # Value cap is applied in scoring/progress; do not hard-reject high cards.
            pass

        if len(cards) == 2:
            same_val = (int(cards[0].value) == int(cards[1].value))
            same_col = (str(cards[0].color) == str(cards[1].color))
            if not (same_val or same_col):
                return []
        return cards

    def _effective_cost(self, wrestler: Wrestler, move_name: str, cards: list) -> int:
        mv_cost = int(self._move_base_cost(move_name))
        # Momentum economy: when the player is "on fire", move costs flow more cheaply.
        try:
            if wrestler is self.player and int(getattr(self, "momentum", 0)) >= 2:
                mv_cost = max(0, int(mv_cost) - 2)
        except Exception:
            pass
        ignore_cards = (move_name == MOVE_REST)
        card_cost = 0 if ignore_cards else sum(int(c.grit_cost()) for c in (cards or []))
        return int(mv_cost) + int(card_cost)

    def _resolve_clash(self, p_move: str, p_cards: list, c_move: str, c_cards: list) -> None:
        if self.game_over:
            return

        self._log_separator()

        # Track pre-exchange TOSSED so a newly-created toss (e.g., Irish Whip)
        # persists into the next beat.
        p_was_tossed = (self.player.state == WrestlerState.TOSSED)
        c_was_tossed = (self.cpu.state == WrestlerState.TOSSED)

        p_move_cost = int(self._move_base_cost(p_move))
        c_move_cost = int(self._move_base_cost(c_move))

        # Safety: if a move is selected that can't be afforded, auto-convert it to Rest.
        if int(self.player.grit) < int(p_move_cost):
            self._log(f"{self._fmt_name(self.player)} can't afford {self._fmt_move(str(p_move))} — forced Rest.")
            p_move = MOVE_REST
            p_move_cost = int(self._move_base_cost(p_move))
            p_cards = []
        if int(self.cpu.grit) < int(c_move_cost):
            self._log(f"{self._fmt_name(self.cpu)} can't afford {self._fmt_move(str(c_move))} — forced Rest.")
            c_move = MOVE_REST
            c_move_cost = int(self._move_base_cost(c_move))
            c_cards = []

        p_ignore_cards = (p_move == MOVE_REST)
        c_ignore_cards = (c_move == MOVE_REST)

        # Rest is a "quiet" action: it should never use cards to outscore an attack.
        if p_ignore_cards:
            p_cards = []
        if c_ignore_cards:
            c_cards = []

        p_card_spent = 0 if p_ignore_cards else sum(int(c.grit_cost()) for c in (p_cards or []))
        c_card_spent = 0 if c_ignore_cards else sum(int(c.grit_cost()) for c in (c_cards or []))
        p_total_spent = int(p_move_cost) + int(p_card_spent)
        c_total_spent = int(c_move_cost) + int(c_card_spent)

        p_card_value_sum = 0 if p_ignore_cards else sum(int(c.value) for c in (p_cards or []))
        c_card_value_sum = 0 if c_ignore_cards else sum(int(c.value) for c in (c_cards or []))

        p_bonus = int(self.player.next_card_bonus)
        c_bonus = int(self.cpu.next_card_bonus)

        p_score = -1 if p_move == MOVE_DEFENSIVE else self._calc_clash_score(p_move, p_cards, card_bonus=p_bonus)
        c_score = -1 if c_move == MOVE_DEFENSIVE else self._calc_clash_score(c_move, c_cards, card_bonus=c_bonus)

        # Rest can never prevent pins/subs/attacks; make it always lose to them.
        def _is_attack_for_rest(move_name: str) -> bool:
            t = str(MOVES.get(str(move_name), {}).get("type", "Setup"))
            return t in {"Strike", "Grapple", "Aerial", "Pin", "Submission"}

        if str(p_move) == MOVE_REST and _is_attack_for_rest(c_move):
            p_score = -999
        if str(c_move) == MOVE_REST and _is_attack_for_rest(p_move):
            c_score = -999

        # Apply combo-chain bonuses (one-turn window).
        p_chain_add = 0
        c_chain_add = 0
        if p_move != MOVE_DEFENSIVE and getattr(self.player, "chain_window", None) == p_move and int(getattr(self.player, "chain_turns_remaining", 0)) > 0:
            p_chain_add = int(getattr(self.player, "chain_potency", 0))
            p_score += int(p_chain_add)
            self.player.chain_turns_remaining = 0
            self.player.chain_window = None
            self.player.chain_potency = 0
            self._log(f"{self._fmt_name(self.player)}: Combo bonus applied!")
        if c_move != MOVE_DEFENSIVE and getattr(self.cpu, "chain_window", None) == c_move and int(getattr(self.cpu, "chain_turns_remaining", 0)) > 0:
            c_chain_add = int(getattr(self.cpu, "chain_potency", 0))
            c_score += int(c_chain_add)
            self.cpu.chain_turns_remaining = 0
            self.cpu.chain_window = None
            self.cpu.chain_potency = 0
            self._log(f"{self._fmt_name(self.cpu)}: Combo bonus applied!")

        # Momentum modifier (scaled): 1-3 => ±1, 4-5 => ±2.
        mom = int(getattr(self, "momentum", 0))
        mom = max(-int(MOMENTUM_MAX_ABS), min(int(MOMENTUM_MAX_ABS), mom))
        mag = abs(int(mom))
        if mag == 0:
            mom_scaled = 0
        elif mag <= int(MOMENTUM_SCORE_TIER1_MAX):
            mom_scaled = int(MOMENTUM_SCORE_TIER1_BONUS)
        else:
            mom_scaled = int(MOMENTUM_SCORE_TIER2_BONUS)
        if mom < 0:
            mom_scaled = -int(mom_scaled)
        p_mom_add = int(mom_scaled) if int(mom_scaled) > 0 else 0
        c_mom_add = int(-mom_scaled) if int(mom_scaled) < 0 else 0
        if p_move != MOVE_DEFENSIVE:
            p_score += int(p_mom_add)
        if c_move != MOVE_DEFENSIVE:
            c_score += int(c_mom_add)

        if bool(REVEAL_SCORE_BREAKDOWN):
            def _breakdown(move_name: str, cards: list, card_bonus: int, chain_add: int, mom_add: int) -> str:
                if move_name == MOVE_DEFENSIVE:
                    return "DEF"
                if not cards:
                    return f"0+chain{int(chain_add)}+mom{int(mom_add)}"
                move_type = str(MOVES.get(move_name, {}).get("type", "Setup"))
                clash_mod = int(MOVES.get(move_name, {}).get("clash_mod", 0))
                doubles = bool(len(cards) == 2 and int(cards[0].value) == int(cards[1].value))
                val = int(cards[0].value) if doubles else sum(int(c.value) for c in cards)
                dbl = 5 if doubles else 0
                col = max(int(cards[0].color_bonus(move_type)), int(cards[1].color_bonus(move_type))) if doubles else sum(int(c.color_bonus(move_type)) for c in cards)
                base = int(val) + int(dbl) + int(col) + int(card_bonus) + int(clash_mod)
                return f"{val}+dbl{dbl}+col{col}+bon{int(card_bonus)}+mod{clash_mod}+chain{int(chain_add)}+mom{int(mom_add)}={int(base)+int(chain_add)+int(mom_add)}"

            self._log(
                f"Score: YOU {_breakdown(p_move, p_cards or [], p_bonus, p_chain_add, p_mom_add)} | "
                f"CPU {_breakdown(c_move, c_cards or [], c_bonus, c_chain_add, c_mom_add)}"
            )

        def is_simultaneous_nonconflicting(name: str) -> bool:
            mv = MOVES.get(name, {})
            t = str(mv.get("type", "Setup"))
            dmg = int(mv.get("damage", 0))
            if name in {MOVE_DEFENSIVE, MOVE_LOCK_UP, MOVE_FIGHT_FOR_CONTROL}:
                return False
            if t in {"Pin", "Submission"}:
                return False
            return (t == "Setup" and dmg == 0) or name in {MOVE_TAUNT, MOVE_REST, MOVE_SLOW_STAND_UP, MOVE_KIP_UP}

        simultaneous = bool(is_simultaneous_nonconflicting(p_move) and is_simultaneous_nonconflicting(c_move))
        defensive_vs_passive = bool(
            (p_move == MOVE_DEFENSIVE and is_simultaneous_nonconflicting(c_move))
            or (c_move == MOVE_DEFENSIVE and is_simultaneous_nonconflicting(p_move))
        )
        if defensive_vs_passive:
            simultaneous = True

        # Used by _execute_move to scale VFX by actual damage.
        self._last_clash_winner = None
        self._last_clash_flashed = False

        p_name = self._fmt_name(self.player)
        c_name = self._fmt_name(self.cpu)
        p_cards_txt = self._fmt_cards(p_cards)
        c_cards_txt = self._fmt_cards(c_cards)

        def cpu_mode_label() -> str:
            mode = str(getattr(self, "_last_cpu_mode", None) or "RND").upper()
            if mode == "GREED":
                return "Greed"
            if mode == "GOOD":
                return "GoodCard"
            if mode == "BAD":
                return "BadCard"
            return "Random"

        # Winner-focused reveal happens after the clash resolves.

        winner = loser = None
        w_move = None
        w_score = None
        skip_winner_botch_check = False
        force_winner_execute = False

        if simultaneous:
            if defensive_vs_passive:
                self._log("Quiet beat: Defense meets a non-attack — both actions resolve.")
            else:
                self._log("Simultaneous Action! Both wrestlers focus on their strategy.")
            self._flash_clash(outcome="neutral", damage=0)
        elif p_move == MOVE_DEFENSIVE and c_move == MOVE_DEFENSIVE:
            self._log("Both fighters play it safe—no clean opening this beat.")
            self._flash_clash(outcome="neutral", damage=0)
        elif (p_move != MOVE_DEFENSIVE) and (c_move != MOVE_DEFENSIVE) and (p_score == c_score):
            # Botch edge case: in a tie, a botch can break the stalemate.
            def is_attack(move_name: str) -> bool:
                t = str(MOVES.get(move_name, {}).get("type", "Setup"))
                return t not in {"Setup", "Defensive"}

            def botch_roll(w: Wrestler, move_name: str) -> bool:
                if not is_attack(move_name):
                    return False
                missing = max(0.0, float(MAX_HEALTH) - float(getattr(w, "hp", 0)))
                divisor = max(1.0, float(TUNING_BOTCH_DIVISOR))
                chance = max(0.0, min(100.0, missing / divisor))
                return float(random.uniform(0.0, 100.0)) < chance

            p_botch = botch_roll(self.player, p_move)
            c_botch = botch_roll(self.cpu, c_move)

            # If any botch is involved in breaking the tie, don't re-roll botch later.
            skip_winner_botch_check = bool(p_botch or c_botch)

            if p_botch and (not c_botch):
                self._log(f"BOTCH! {self._fmt_name(self.player)} stumbles due to injury!")
                winner, loser = self.cpu, self.player
                w_move, w_score = c_move, c_score
            elif c_botch and (not p_botch):
                self._log(f"BOTCH! {self._fmt_name(self.cpu)} stumbles due to injury!")
                winner, loser = self.player, self.cpu
                w_move, w_score = p_move, p_score
            elif p_botch and c_botch:
                # Double botch: healthier wrestler still lands their move.
                self._log("DOUBLE BOTCH! Both stumble — the healthier fighter capitalizes!")
                force_winner_execute = True
                if int(self.player.hp) > int(self.cpu.hp):
                    winner, loser = self.player, self.cpu
                    w_move, w_score = p_move, p_score
                elif int(self.cpu.hp) > int(self.player.hp):
                    winner, loser = self.cpu, self.player
                    w_move, w_score = c_move, c_score
                else:
                    if random.random() < 0.5:
                        winner, loser = self.player, self.cpu
                        w_move, w_score = p_move, p_score
                    else:
                        winner, loser = self.cpu, self.player
                        w_move, w_score = c_move, c_score
            else:
                # No botch: break ties by Strength (remaining deck + hand).
                try:
                    p_str = int(self.player.strength_current())
                except Exception:
                    p_str = 0
                try:
                    c_str = int(self.cpu.strength_current())
                except Exception:
                    c_str = 0

                if p_str > c_str:
                    winner, loser = self.player, self.cpu
                    w_move, w_score = p_move, p_score
                    force_winner_execute = True
                    self._log(f"TIE BREAK! {self._fmt_name(self.player)} muscles through on Strength.")
                elif c_str > p_str:
                    winner, loser = self.cpu, self.player
                    w_move, w_score = c_move, c_score
                    force_winner_execute = True
                    self._log(f"TIE BREAK! {self._fmt_name(self.cpu)} muscles through on Strength.")
                else:
                    # True tie: usually coin toss, occasionally double-down.
                    if random.random() < float(TUNING_DOUBLE_DOWN_ON_TRUE_TIE_CHANCE):
                        self._log("DOUBLE DOWN! Both crash into the mat — 5 damage each. Both are GROUNDED.")
                        self.player.take_damage(5)
                        self.cpu.take_damage(5)
                        self.player.clear_grapple()
                        self.cpu.clear_grapple()
                        self.player.set_state(WrestlerState.GROUNDED)
                        self.cpu.set_state(WrestlerState.GROUNDED)
                    else:
                        if random.random() < 0.5:
                            winner, loser = self.player, self.cpu
                            w_move, w_score = p_move, p_score
                        else:
                            winner, loser = self.cpu, self.player
                            w_move, w_score = c_move, c_score
                        force_winner_execute = True
                        self._log("TIE! A split-second edge decides it.")
        elif p_score > c_score:
            winner, loser = self.player, self.cpu
            w_move, w_score = p_move, p_score
        else:
            winner, loser = self.cpu, self.player
            w_move, w_score = c_move, c_score

        # Better feedback: make the clash winner obvious in the log.
        if (not simultaneous) and (winner is not None) and (loser is not None):
            winner_move = p_move if winner is self.player else c_move
            loser_move = c_move if winner is self.player else p_move
            winner_score = int(p_score) if winner is self.player else int(c_score)
            loser_score = int(c_score) if winner is self.player else int(p_score)
            winner_cards = p_cards if winner is self.player else c_cards
            loser_cards = c_cards if winner is self.player else p_cards

            def score_txt(move_name: str, score: int, cards: list) -> str:
                if move_name == MOVE_DEFENSIVE:
                    pool = sum(int(c.value) for c in (cards or []))
                    return f"DEF {pool}"
                return str(int(score))

            w_txt = score_txt(str(winner_move), winner_score, winner_cards)
            l_txt = score_txt(str(loser_move), loser_score, loser_cards)
            w_cards_txt = self._fmt_cards(winner_cards)
            l_cards_txt = self._fmt_cards(loser_cards)

            extra = ""
            if winner is self.cpu:
                extra = f" [{cpu_mode_label()}]"

            # Example style:
            # "CPU was going for Chokeslam (7), but YOU beat him to the punch with Lock Up (9) (Cards: 4, 5)!"
            if REVEAL_LOSER_MOVE_NAME:
                if REVEAL_LOSER_CARDS:
                    loser_bits = f"{self._fmt_move(str(loser_move))} ({l_txt}) ({l_cards_txt})"
                else:
                    loser_bits = f"{self._fmt_move(str(loser_move))} ({l_txt})"
                self._log(
                    f"[b]{self._fmt_name(winner)} wins the clash![/b] "
                    f"{self._fmt_name(loser)} was going for {loser_bits}, "
                    f"but {self._fmt_name(winner)} beats them to it with {self._fmt_move(str(winner_move))} ({w_txt}) ({w_cards_txt})!{extra}"
                )
            else:
                self._log(
                    f"[b]{self._fmt_name(winner)} wins the clash![/b] "
                    f"{self._fmt_move(str(winner_move))} ({w_txt}) ({w_cards_txt})!{extra}"
                )

            self._last_clash_winner = winner
            # Base flash on clash result; damage (if any) will override in _execute_move.
            self._flash_clash(outcome=("player" if winner is self.player else "cpu"), damage=0)

        # --- Botch check happens before criticals (so a botch can't "critical") ---
        caught_napping_player = False
        caught_napping_cpu = False
        critical_damage_override: int | None = None

        if (not simultaneous) and (winner is not None) and (w_move is not None):
            if (not skip_winner_botch_check) and (not force_winner_execute):
                w_type = str(MOVES.get(str(w_move), {}).get("type", "Setup"))
                is_attack = (w_type not in {"Setup", "Defensive"})
                if is_attack:
                    missing = max(0.0, float(MAX_HEALTH) - float(getattr(winner, "hp", 0)))
                    divisor = max(1.0, float(TUNING_BOTCH_DIVISOR))
                    botch_chance = max(0.0, min(100.0, missing / divisor))
                    if float(random.uniform(0.0, 100.0)) < botch_chance:
                        self._log(f"BOTCH! {self._fmt_name(winner)} stumbles due to injury!")
                        winner = None

        # --- "Caught Napping" criticals (Rest punish) ---
        if (not simultaneous) and (winner is not None) and (loser is not None) and (w_move is not None):
            loser_move = c_move if winner is self.player else p_move
            w_type = str(MOVES.get(str(w_move), {}).get("type", "Setup"))
            is_attack = w_type in {"Strike", "Grapple", "Aerial", "Pin", "Submission"}
            if (str(loser_move) == MOVE_REST) and is_attack:
                caught_napping_player = bool(loser is self.player)
                caught_napping_cpu = bool(loser is self.cpu)

                raw = int(MOVES.get(str(w_move), {}).get("damage", 0))
                if raw > 0:
                    critical_damage_override = int(round(float(raw) * 1.5))
                self._log(f"CRITICAL! {self._fmt_name(winner)} catches {self._fmt_name(loser)} resting!")

        # Passive regen text: show it early in the log stack.
        def _apply_passive_regen(w: Wrestler, total_spent: int, *, blocked: bool) -> None:
            if not TUNING_ENABLE_PASSIVE_REGEN:
                return
            if int(total_spent) != 0:
                return
            if bool(blocked):
                return
            before = int(w.grit)
            regen = int(TUNING_GRIT_PASSIVE_REGEN)
            try:
                if bool(w.is_winded()):
                    regen = max(0, int(regen // 2))
            except Exception:
                pass
            w.grit = min(w.max_grit, int(w.grit) + int(regen))
            gained = int(w.grit) - before
            if gained > 0:
                self._log(f"{self._fmt_name(w)}: Passive Regen (+{gained} Grit).")

        _apply_passive_regen(self.player, p_total_spent, blocked=bool(caught_napping_player and p_move == MOVE_REST))
        _apply_passive_regen(self.cpu, c_total_spent, blocked=bool(caught_napping_cpu and c_move == MOVE_REST))

        # Spend grit + apply card-driven economy + discard + redraw (both sides pay their attempt).
        self.player.spend_grit(p_move_cost)
        # If the player got caught resting, cancel all Rest regen (including card-regen).
        if not (caught_napping_player and p_move == MOVE_REST):
            self.player.apply_grit_from_cards(p_cards, ignore_cost=p_ignore_cards)
        self.player.discard_cards(p_cards)
        self.player.draw_to_full()

        self.cpu.spend_grit(c_move_cost)
        # If the CPU got caught resting, cancel all Rest regen (including card-regen).
        if not (caught_napping_cpu and c_move == MOVE_REST):
            self.cpu.apply_grit_from_cards(c_cards, ignore_cost=c_ignore_cards)
        self.cpu.discard_cards(c_cards)
        self.cpu.draw_to_full()

        self.player.next_card_bonus = 0
        self.cpu.next_card_bonus = 0

        # Grapple-break strikes: defender breaks free on a decisive win.
        if (not simultaneous) and (winner is not None) and (loser is not None) and (w_move is not None):
            try:
                mv = MOVES.get(str(w_move), {})
                if str(mv.get("type", "Setup")) == "Strike":
                    w_score_val = int(p_score) if winner is self.player else int(c_score)
                    l_score_val = int(c_score) if winner is self.player else int(p_score)
                    margin = int(w_score_val - l_score_val)
                    if (
                        margin >= int(GRAPPLE_BREAK_STRIKE_VALUE)
                        and bool(winner.is_in_grapple())
                        and bool(loser.is_in_grapple())
                        and getattr(winner, "grapple_role", None) == GrappleRole.DEFENSE
                        and getattr(loser, "grapple_role", None) == GrappleRole.OFFENSE
                    ):
                        winner.clear_grapple()
                        loser.clear_grapple()
                        winner.set_state(WrestlerState.STANDING)
                        loser.set_state(WrestlerState.STANDING)
                        self._log(f"BREAK! {self._fmt_name(winner)} cracks {self._fmt_name(loser)} and slips free of the hold!")
            except Exception:
                pass

        if simultaneous:
            self._execute_move(attacker=self.player, defender=self.cpu, move_name=p_move, clash_score=p_score, card_value_sum=p_card_value_sum, cards=p_cards)
            self._execute_move(attacker=self.cpu, defender=self.player, move_name=c_move, clash_score=c_score, card_value_sum=c_card_value_sum, cards=c_cards)
        elif (winner is not None) and (w_move is not None):
            loser_move = c_move if winner is self.player else p_move
            loser_type = str(MOVES.get(loser_move, {}).get("type", "Setup"))
            if str(w_move) in {MOVE_TAUNT, MOVE_REST} and loser_type not in {"Setup", "Defensive"}:
                self._log(f"{self._fmt_name(winner)} dodges effortlessly while {self._fmt_name(loser)} wastes the beat.")

            passive_winner = str(w_move) in {MOVE_TAUNT, MOVE_REST}
            positioning_loser = str(loser_move) in {MOVE_SLOW_STAND_UP, MOVE_KIP_UP, MOVE_CLIMB_DOWN, MOVE_STOP_SHORT, MOVE_SHOVE_OFF}
            run_loser_after = bool(passive_winner and positioning_loser)

            # Defensive cancel/soften
            if (p_move == MOVE_DEFENSIVE and winner is self.cpu) or (c_move == MOVE_DEFENSIVE and winner is self.player):
                defender_cards = p_cards if p_move == MOVE_DEFENSIVE else c_cards
                pool = sum(int(c.value) for c in (defender_cards or []))
                opp_score = int(w_score or 0)
                raw_dmg = int(MOVES.get(w_move, {}).get("damage", 0))

                # Active Defense: perfect-guard reversal if you barely lose (<=2).
                margin = int(opp_score) - int(pool)
                if 0 <= int(margin) <= 2:
                    defender = self.player if p_move == MOVE_DEFENSIVE else self.cpu
                    attacker = winner
                    self._log(f"PERFECT GUARD! {self._fmt_name(defender)} reverses the momentum at the last second!")
                    dealt = attacker.take_damage(5, target_part="BODY")
                    self._log(f"{self._fmt_name(attacker)} takes {self._fmt_damage(dealt)} on the counter!")
                    try:
                        delta = 2 if defender is self.player else -2
                        cur = int(getattr(self, "momentum", 0))
                        self.momentum = max(-int(MOMENTUM_MAX_ABS), min(int(MOMENTUM_MAX_ABS), int(cur + delta)))
                    except Exception:
                        pass
                    try:
                        self._flash_clash(outcome=("player" if defender is self.player else "cpu"), damage=int(dealt))
                    except Exception:
                        pass
                    # Do not execute the original attacker's move.
                else:
                    avoid_ok = (opp_score <= 10 and pool >= opp_score)
                    suppress_states = (opp_score <= 10 and pool >= max(1, opp_score - 2))
                    if avoid_ok:
                        self._log(f"Defensive ({pool}): slip away from the attack!")
                    else:
                        reduction = pool if opp_score <= 10 else (pool // 2)
                        boosted_raw = int(raw_dmg)
                        w_cards = p_cards if winner is self.player else c_cards
                        try:
                            if boosted_raw > 0 and w_cards and len(w_cards) == 2 and int(w_cards[0].value) == int(w_cards[1].value):
                                w_type = str(MOVES.get(w_move, {}).get("type", "Setup"))
                                if w_type in {"Strike", "Grapple", "Aerial"}:
                                    boosted_raw = int(math.ceil(float(boosted_raw) * float(DOUBLES_DAMAGE_MODIFIER)))
                        except Exception:
                            pass

                        dmg_override = max(0, int(boosted_raw) - max(0, reduction))
                        if int(raw_dmg) > 0 and int(dmg_override) < int(boosted_raw):
                            self._log(f"Defensive ({pool}): soften the blow ({int(boosted_raw)}->{int(dmg_override)}).")
                        w_val = p_card_value_sum if winner is self.player else c_card_value_sum
                        self._execute_move(attacker=winner, defender=loser, move_name=w_move, clash_score=w_score, damage_override=dmg_override, suppress_state_changes=bool(suppress_states), card_value_sum=w_val, cards=w_cards, apply_doubles_bonus=False)
            else:
                w_cards = p_cards if winner is self.player else c_cards
                w_val = p_card_value_sum if winner is self.player else c_card_value_sum
                self._execute_move(attacker=winner, defender=loser, move_name=w_move, clash_score=w_score, damage_override=critical_damage_override, card_value_sum=w_val, cards=w_cards)

            if run_loser_after:
                self._execute_move(attacker=loser, defender=winner, move_name=str(loser_move), damage_override=0)

        # Irish whip window: if a wrestler STARTED this exchange as TOSSED and the opponent
        # doesn't capitalize with a TOSSED-targeting attack, they recover.
        def _capitalized_on_tossed(attacker_move: str) -> bool:
            mv = MOVES.get(str(attacker_move), {})
            if str(mv.get("req_target_state", "ANY")) != "TOSSED":
                return False
            t = str(mv.get("type", "Setup"))
            dmg = int(mv.get("damage", 0))
            return (t not in {"Setup", "Defensive"}) or dmg > 0

        try:
            if bool(p_was_tossed) and self.player.state == WrestlerState.TOSSED and not _capitalized_on_tossed(str(c_move)):
                self.player.set_state(WrestlerState.STANDING)
            if bool(c_was_tossed) and self.cpu.state == WrestlerState.TOSSED and not _capitalized_on_tossed(str(p_move)):
                self.cpu.set_state(WrestlerState.STANDING)
        except Exception:
            pass

        # Groggy beat resolution: recovery clears groggy regardless of outcome.
        if str(p_move) == MOVE_GROGGY_RECOVERY:
            self.player.is_groggy = False
        if str(c_move) == MOVE_GROGGY_RECOVERY:
            self.cpu.is_groggy = False

        # Momentum update (after resolution): winning shifts MOM; big reversals reset toward center.
        if (not simultaneous) and (winner is not None) and (w_move is not None):
            delta = 0
            if str(w_move) != MOVE_DEFENSIVE:
                if bool(MOMENTUM_GAIN_ON_ATTACKS_ONLY):
                    w_type = str(MOVES.get(str(w_move), {}).get("type", "Setup"))
                    is_attack = w_type not in {"Setup", "Defensive"}
                    if is_attack:
                        delta = int(MOMENTUM_WIN_DELTA) if (winner is self.player) else -int(MOMENTUM_WIN_DELTA)
                else:
                    delta = int(MOMENTUM_WIN_DELTA) if (winner is self.player) else -int(MOMENTUM_WIN_DELTA)

            if delta != 0:
                cur = int(getattr(self, "momentum", 0))
                cur = max(-int(MOMENTUM_MAX_ABS), min(int(MOMENTUM_MAX_ABS), cur))
                if abs(cur) >= int(MOMENTUM_REVERSAL_RESET_THRESHOLD) and (cur * delta) < 0:
                    self._log("Momentum swing! The match flow resets.")
                    cur = 0
                self.momentum = max(-int(MOMENTUM_MAX_ABS), min(int(MOMENTUM_MAX_ABS), int(cur + delta)))

        self._update_hud()

        # No HP-based KO ending; clamp at 0 and keep going.
        self.player.hp = max(0, int(self.player.hp))
        self.cpu.hp = max(0, int(self.cpu.hp))

        if self._escape_mode:
            self._render_escape_ui()
            self._update_control_bar()
        else:
            self._start_turn("player")

    def _escape_threshold(self, victim_hp_pct: float) -> int:
        pct = max(0.0, min(1.0, float(victim_hp_pct)))
        v = 1 + int(25.0 * (1.0 - pct))
        return max(1, min(26, int(v)))

    def _begin_escape(self, *, attacker: Wrestler, defender: Wrestler, kind: str, move_name: str | None = None) -> None:
        threshold = self._escape_threshold(defender.hp_pct())
        self._escape_mode = {
            "kind": str(kind),
            "threshold": int(threshold),
            "total": 0,
            "plays_left": 3,
            "move_name": str(move_name) if move_name else None,
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

        # CPU defending: stepwise, greedy discards; user presses CONTINUE between beats.
        self._log(f"{self._fmt_name(attacker)} attempts a {str(kind).lower()}!")
        self._render_moves_ui()
        self._render_hand()
        self._update_control_bar()

    def _escape_continue_cpu(self, _inst=None) -> None:
        if self.game_over or not self._escape_mode:
            return
        if bool(self._escape_mode.get("defender_is_player")):
            return

        attacker = self._escape_mode.get("attacker")
        defender = self._escape_mode.get("defender")
        if not isinstance(attacker, Wrestler) or not isinstance(defender, Wrestler):
            return

        plays_before = int(self._escape_mode.get("plays_left", 0))
        if plays_before <= 0:
            return
        count_no = max(1, 4 - int(plays_before))

        hand = list(defender.hand or [])
        if not hand:
            self._escape_mode["plays_left"] = 0
        else:
            best = max(hand, key=lambda c: int(c.value))
            gained = int(best.value)
            defender.discard_cards([best])
            self._escape_mode["total"] = int(self._escape_mode.get("total", 0)) + gained
            self._escape_mode["plays_left"] = int(self._escape_mode.get("plays_left", 0)) - 1

            total = int(self._escape_mode.get("total", 0))
            threshold = int(self._escape_mode.get("threshold", 1))
            kind = str(self._escape_mode.get("kind", "ESCAPE"))

            if kind.upper() == "PINFALL":
                if count_no == 1:
                    self._log(f"ONE! {self._fmt_name(defender)} fights out using a {gained}. (total {total}/{threshold})")
                elif count_no == 2:
                    self._log(f"TWO! {self._fmt_name(defender)} kicks out using a {gained}. (total {total}/{threshold})")
                else:
                    self._log(f"THREE...?! {self._fmt_name(defender)} strains with a {gained}. (total {total}/{threshold})")
            else:
                self._log(f"Escape attempt: {self._fmt_name(defender)} discards {gained} (total {total}/{threshold})")

            if total >= threshold:
                if kind.upper() == "PINFALL":
                    if count_no == 1:
                        self._log(f"KICKOUT AT ONE! {self._fmt_name(defender)} escapes!")
                    elif count_no == 2:
                        self._log(f"KICKOUT AT TWO! {self._fmt_name(defender)} escapes!")
                    else:
                        self._log(f"JUST IN TIME! {self._fmt_name(defender)} escapes!")
                else:
                    self._log(f"{self._fmt_name(defender)} escapes the {str(kind).lower()} attempt!")
                self._end_escape(success=True)
                return

            if kind.upper() == "SUBMISSION":
                tick = int(SUBMISSION_TICK_DAMAGE)
                try:
                    move_name = str(self._escape_mode.get("move_name") or "")
                    mv = MOVES.get(move_name, {}) if move_name else {}
                    tick = int(mv.get("tick_damage", tick))
                except Exception:
                    tick = int(SUBMISSION_TICK_DAMAGE)
                dealt = defender.take_damage(int(tick), target_part="BODY")
                self._log(f"{self._fmt_name(attacker)} cranks it! {self._fmt_name(defender)} takes {self._fmt_damage(dealt)}.")

        if int(self._escape_mode.get("plays_left", 0)) <= 0:
            kind = str(self._escape_mode.get("kind", "ESCAPE"))
            winner = self._fmt_name(attacker)
            self.game_over = True
            if kind.upper() == "PINFALL":
                self._log(f"THREE! {kind}! Escape failed — {winner} wins.")
            else:
                self._log(f"{kind}! Escape failed — {winner} wins.")
            self._update_control_bar()
            return

        self._render_moves_ui()
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

        plays_before = int(self._escape_mode.get("plays_left", 0))
        count_no = max(1, 4 - int(plays_before))

        self._escape_mode["total"] = int(self._escape_mode.get("total", 0)) + gained
        self._escape_mode["plays_left"] = int(self._escape_mode.get("plays_left", 0)) - 1

        total = int(self._escape_mode.get("total", 0))
        threshold = int(self._escape_mode.get("threshold", 1))
        kind = str(self._escape_mode.get("kind", "ESCAPE"))

        if kind.upper() == "PINFALL":
            if count_no == 1:
                self._log(f"ONE! Escape attempt: discard {gained} (total {total}/{threshold})")
            elif count_no == 2:
                self._log(f"TWO! Escape attempt: discard {gained} (total {total}/{threshold})")
            else:
                self._log(f"THREE... Escape attempt: discard {gained} (total {total}/{threshold})")
        else:
            self._log(f"Escape discard: {gained} (total {total}/{threshold})")
        self._render_hand()
        self._render_moves_ui()
        self._update_control_bar()

        if total >= threshold:
            if kind.upper() == "PINFALL":
                if count_no == 1:
                    self._log("KICKOUT AT ONE!")
                elif count_no == 2:
                    self._log("KICKOUT AT TWO!")
                else:
                    self._log("JUST IN TIME! KICKOUT!")
            self._log(f"You escape the {kind.lower()} attempt!")
            self._end_escape(success=True)
            return

        if kind.upper() == "SUBMISSION":
            try:
                attacker = self._escape_mode.get("attacker")
                defender = self._escape_mode.get("defender")
                if isinstance(attacker, Wrestler) and isinstance(defender, Wrestler):
                    tick = int(SUBMISSION_TICK_DAMAGE)
                    try:
                        move_name = str(self._escape_mode.get("move_name") or "")
                        mv = MOVES.get(move_name, {}) if move_name else {}
                        tick = int(mv.get("tick_damage", tick))
                    except Exception:
                        tick = int(SUBMISSION_TICK_DAMAGE)
                    dealt = defender.take_damage(int(tick), target_part="BODY")
                    self._log(f"{self._fmt_name(attacker)} cranks it! {self._fmt_name(defender)} takes {self._fmt_damage(dealt)}.")
            except Exception:
                pass

        if int(self._escape_mode.get("plays_left", 0)) <= 0:
            winner = "YOU" if bool(self._escape_mode.get("attacker_is_player")) else "CPU"
            self.game_over = True
            if kind.upper() == "PINFALL":
                self._log(f"THREE! {kind}! Escape failed — {winner} wins.")
            else:
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

    def _execute_move(
        self,
        *,
        attacker: Wrestler,
        defender: Wrestler,
        move_name: str,
        clash_score: int | None = None,
        damage_override: int | None = None,
        suppress_state_changes: bool = False,
        card_value_sum: int = 0,
        cards: list | None = None,
        apply_doubles_bonus: bool = True,
    ) -> None:
        # card_value_sum/cards are optional extras used by Taunt + Stand Up systems.

        move = MOVES[move_name]
        mtype = str(move.get("type", "Setup"))

        was_dazed = False
        try:
            was_dazed = int(getattr(defender, "daze_turns", 0) or 0) > 0
        except Exception:
            was_dazed = False

        flavor = self._render_flavor_text(str(move.get("flavor_text", "")), attacker=attacker, defender=defender)
        self._log(f"{self._fmt_name(attacker)} uses {self._fmt_move(move_name)}! {flavor}")

        # AI memory: track what was just executed to avoid repetition.
        try:
            attacker.last_move_name = str(move_name)
        except Exception:
            pass

        if move_name == MOVE_REST:
            before = attacker.grit
            attacker.grit = min(attacker.max_grit, attacker.grit + 3)
            gained = attacker.grit - before
            self._log(f"{self._fmt_name(attacker)} recovers (+{gained} Grit).")
            return

        if move_name == MOVE_GROGGY_RECOVERY:
            # Clears groggy and leaves you vulnerable if hit next beat.
            attacker.is_groggy = False
            attacker.next_damage_taken_multiplier = max(float(getattr(attacker, "next_damage_taken_multiplier", 1.0)), 1.25)
            self._log(f"{self._fmt_name(attacker)} tries to steady themselves... (VULNERABLE)")
            return

        if move_name == MOVE_TAUNT:
            base = int(move.get("hype_gain", 0))
            bonus = int(card_value_sum) * 3
            gained = int(base) + int(bonus)
            attacker.add_hype(gained)
            self._log(f"{self._fmt_name(attacker)} gets fired up! (+{gained} Hype)")
            return

        if move_name in {MOVE_SLOW_STAND_UP, MOVE_KIP_UP}:
            # Cumulative stand-up: reduce stun_meter instead of instantly standing.
            if attacker.state != WrestlerState.GROUNDED:
                self._log(f"{self._fmt_name(attacker)} tries to stand, but isn't down.")
                return

            progress = int(card_value_sum)
            if cards and len(cards) == 2 and int(cards[0].value) == int(cards[1].value):
                progress += 5

            before = int(getattr(attacker, "stun_meter", 0))
            attacker.stun_meter = int(before) - int(progress)
            attacker.add_hype(int(move.get("hype_gain", 0)))

            if int(attacker.stun_meter) <= 0:
                attacker.stun_meter = 0
                attacker.set_state(WrestlerState.STANDING)
                self._log(f"{self._fmt_name(attacker)} fights to their feet!")
            else:
                self._log(f"Struggling to rise... (Stun: {attacker.stun_meter} left)")
            return

        if move_name == MOVE_SHOVE_OFF:
            if attacker.is_in_grapple() or defender.is_in_grapple():
                attacker.clear_grapple()
                defender.clear_grapple()
                attacker.set_state(WrestlerState.STANDING)
                defender.set_state(WrestlerState.STANDING)
                self._log(f"{self._fmt_name(attacker)} shoves free and resets to neutral!")
            else:
                self._log(f"{self._fmt_name(attacker)} pushes empty air — {self._fmt_name(defender)} was already gone!")
            return

        # Pin/Submission start escape
        if mtype in {"Pin", "Submission"}:
            kind = "PINFALL" if mtype == "Pin" else "SUBMISSION"
            self._begin_escape(attacker=attacker, defender=defender, kind=kind, move_name=move_name)
            return

        raw_damage = int(move.get("damage", 0)) if damage_override is None else int(damage_override)

        # Doubles bonus damage: if doubles were used for a successful attack, boost by 25%.
        try:
            if bool(apply_doubles_bonus) and raw_damage > 0 and cards and len(cards) == 2 and int(cards[0].value) == int(cards[1].value):
                if mtype in {"Strike", "Grapple", "Aerial"}:
                    raw_damage = int(math.ceil(float(raw_damage) * float(DOUBLES_DAMAGE_MODIFIER)))
                    self._log("Doubles hit! Damage boosted.")
        except Exception:
            pass
        if raw_damage > 0:
            target_part = move.get("target_part", None)
            dealt = defender.take_damage(raw_damage, target_part=str(target_part) if target_part else None)
            self._log(f"{self._fmt_name(defender)} takes {self._fmt_damage(dealt)}.")

            # Apply DAZED probabilistically (HP-based).
            try:
                if not bool(was_dazed):
                    turns = int(self._calc_daze_application(defender, move))
                    if turns > 0 and int(getattr(defender, "hp", 0)) > 0:
                        defender.daze_turns = max(int(getattr(defender, "daze_turns", 0) or 0), int(turns))
                        try:
                            defender.is_groggy = True
                        except Exception:
                            pass
                        self._log(f"{self._fmt_name(defender)} is DAZED! ({int(defender.daze_turns)})")
            except Exception:
                pass

            # Anti-infinite safety: hitting a dazed opponent wakes them up over time,
            # or instantly if you hit too hard.
            try:
                if bool(was_dazed) and mtype in {"Strike", "Grapple", "Aerial"}:
                    before = int(getattr(defender, "daze_turns", 0) or 0)
                    if int(dealt) >= int(TUNING_DAZE_WAKE_DAMAGE):
                        defender.daze_turns = 0
                        if before > 0:
                            self._log(f"{self._fmt_name(defender)} snaps back to reality from the shock!")
                    else:
                        defender.daze_turns = max(0, int(before) - 1)
                        if before > 0 and int(defender.daze_turns) == 0:
                            self._log(f"{self._fmt_name(defender)} is shaken awake by the impact!")
                            try:
                                defender.is_groggy = False
                            except Exception:
                                pass
            except Exception:
                pass

            # Clash overlay VFX: scale by actual dealt damage.
            try:
                if (not bool(getattr(self, "_last_clash_flashed", False))) and (getattr(self, "_last_clash_winner", None) is attacker):
                    outcome = "player" if attacker is self.player else "cpu"
                    self._flash_clash(outcome=outcome, damage=int(dealt))
                    self._last_clash_flashed = True
            except Exception:
                pass

            # (Groggy system remains available for special moves; heavy-hit stun is now handled by DAZED.)

        attacker.add_hype(int(move.get("hype_gain", 0)))

        if not suppress_state_changes:
            if "set_user_state" in move:
                attacker.set_state(WrestlerState(str(move["set_user_state"])))
            if "set_target_state" in move:
                tgt = str(move["set_target_state"])
                # Strike knockdowns should not be guaranteed early-match.
                if (
                    tgt == "GROUNDED"
                    and str(mtype) == "Strike"
                    and defender.state in {WrestlerState.STANDING, WrestlerState.RUNNING}
                    and (not bool(move.get("knockdown_always", False)))
                ):
                    try:
                        missing_pct = max(0.0, min(1.0, 1.0 - float(defender.hp_pct())))
                        chance = max(0.0, min(100.0, float(missing_pct) * 100.0 * float(TUNING_STRIKE_KNOCKDOWN_CHANCE_SCALAR)))
                        if float(random.uniform(0.0, 100.0)) < float(chance):
                            defender.set_state(WrestlerState.GROUNDED)
                        else:
                            self._log(f"{self._fmt_name(defender)} stays on their feet!")
                    except Exception:
                        defender.set_state(WrestlerState.GROUNDED)
                else:
                    defender.set_state(WrestlerState(tgt))

        if attacker.is_in_grapple() and defender.is_in_grapple():
            attacker.grapple_role = GrappleRole.OFFENSE
            defender.grapple_role = GrappleRole.DEFENSE

        # Combo chains: after a successful execution, open the follow-up window.
        chain_next = move.get("chain_next")
        if chain_next:
            attacker.chain_window = str(chain_next)
            attacker.chain_potency = int(move.get("chain_bonus", 0))
            # Stored as 2 because the next _start_turn() immediately decrements by 1.
            attacker.chain_turns_remaining = 2
            self._log(f"{self._fmt_name(attacker)} has a combo opening! (+{attacker.chain_potency} on {attacker.chain_window})")

    # -------------------------------------------------------------------------
    # HELPER LOGIC
    # -------------------------------------------------------------------------

    def _cpu_buy_buffs(self) -> None:
        """Spend CPU hype on buffs before selecting a move."""
        if self.game_over:
            return
        if int(self.cpu.hype) < 25:
            return

        # Simple parity behavior: occasionally buy a grit refill (if low), otherwise
        # choose between Pump (+1) and Adrenaline (+2).
        # Kept probabilistic so CPU doesn't always auto-buy.

        if int(self.cpu.hype) >= 30 and int(self.cpu.grit) <= 1 and random.random() < 0.35:
            self.cpu.hype -= 30
            before = int(self.cpu.grit)
            self.cpu.grit = min(self.cpu.max_grit, int(self.cpu.grit) + 4)
            gained = int(self.cpu.grit) - before
            self._log(f"{self._fmt_name(self.cpu)} rallies! (+{gained} Grit)")
            return

        # Lock Up Edge (non-stacking): only relevant if a lock up can happen soon.
        if (
            int(self.cpu.hype) >= 50
            and (not bool(getattr(self.cpu, "lockup_edge_ready", False)))
            and self.cpu.state == WrestlerState.STANDING
            and self.player.state == WrestlerState.STANDING
            and random.random() < 0.10
        ):
            self.cpu.hype -= 50
            self.cpu.lockup_edge_ready = True
            self._log(f"{self._fmt_name(self.cpu)} buys an edge for the next lock up!")
            return

        if int(self.cpu.hype) >= 50 and random.random() < 0.15:
            self.cpu.hype -= 50
            self.cpu.next_card_bonus = max(int(self.cpu.next_card_bonus), 2)
            self._log(f"{self._fmt_name(self.cpu)} uses the crowd energy! (Adrenaline +2 next card)")
            return

        if int(self.cpu.hype) >= 25 and random.random() < 0.20:
            self.cpu.hype -= 25
            self.cpu.next_card_bonus = max(int(self.cpu.next_card_bonus), 1)
            self._log(f"{self._fmt_name(self.cpu)} digs deep! (Pump Up +1 next card)")
            return

    def _cpu_ai_mode(self) -> str:
        traits = {}
        try:
            traits = dict(getattr(self.cpu, "profile", None) or {})
        except Exception:
            traits = {}
        weights = {}
        try:
            weights = dict(traits.get("ai_traits") or {})
        except Exception:
            weights = {}

        def w(key: str) -> int:
            try:
                return max(0, int(weights.get(key, 0)))
            except Exception:
                return 0

        opts = [("GREED", w("GREED")), ("GOOD", w("GOOD")), ("BAD", w("BAD")), ("RND", w("RND"))]
        total = sum(v for _k, v in opts)
        if total <= 0:
            return "RND"

        roll = random.randint(1, total)
        acc = 0
        for k, v in opts:
            acc += v
            if roll <= acc:
                return k
        return "RND"

    def _cpu_choose_move(self, *, mode: str | None = None):
        if bool(getattr(self.cpu, "is_groggy", False)):
            if self._move_is_legal(MOVE_GROGGY_RECOVERY, self.cpu, self.player) and self._passes_moveset(self.cpu, MOVE_GROGGY_RECOVERY):
                return MOVE_GROGGY_RECOVERY
        valid = self._available_moves(self.cpu, self.player)
        if not valid:
            return MOVE_REST

        # Parity with the player's UI: finishers require doubles.
        has_doubles = self.cpu.has_doubles_in_hand()
        filtered = [m for m in valid if not (bool(MOVES.get(m, {}).get("is_finisher")) and (not has_doubles))]
        if filtered:
            valid = filtered

        mode = str(mode or self._cpu_ai_mode())

        # Desperation override: low HP tries cheap options.
        try:
            if float(self.cpu.hp_pct()) < 0.30:
                panic = [m for m in valid if int(MOVES.get(m, {}).get("cost", 0)) == 0]
                if panic:
                    return random.choice(panic)
        except Exception:
            pass

        def type_bonus_for(name: str, mv: dict) -> int:
            # Smart defaults ONLY when ai_score is missing.
            if "ai_score" in mv:
                return 0

            raw_damage = int(mv.get("damage", 0))
            mtype = str(mv.get("type", "Setup"))

            if mtype == "Pin":
                return 20
            if mtype == "Submission":
                return 15
            if mtype == "Grapple" and raw_damage == 0:
                return 12
            if mtype == "Aerial" and raw_damage == 0:
                return 10
            if mtype == "Setup":
                return 5
            return 0

        def move_value(name: str) -> float:
            mv = MOVES.get(name, {})
            dmg = int(mv.get("damage", 0))
            manual = int(mv.get("ai_score", 0))
            bonus = int(type_bonus_for(name, mv))
            score = float(dmg + manual + bonus)

            # Grounded realism: prioritize standing up when healthy.
            try:
                cpu_state = getattr(self.cpu, "state", None)
                cpu_hp = float(self.cpu.hp_pct())
                is_grounded = (cpu_state == WrestlerState.GROUNDED)
                wants_up = bool(is_grounded and cpu_hp >= float(CPU_GETUP_HEALTHY_PCT))
                set_user = str(mv.get("set_user_state", ""))
                is_getup = bool(is_grounded and set_user == "STANDING")
                if wants_up and is_getup:
                    score += float(CPU_GETUP_BONUS_HEALTHY)
                # If healthy, discourage repeated ground strikes (e.g., Upkick) instead of standing.
                if wants_up and str(mv.get("type", "Setup")) == "Strike" and (not is_getup):
                    score -= float(CPU_UPKICK_PENALTY_WHEN_HEALTHY)
                # If hurt, resting from the mat becomes more appealing.
                if is_grounded and str(name) == MOVE_REST:
                    if cpu_hp <= float(CPU_REST_HURT_PCT) or int(self.cpu.grit) <= 1:
                        score += float(CPU_REST_BONUS_WHEN_HURT)
            except Exception:
                pass

            # Repetition penalty to prevent spamming
            if str(getattr(self.cpu, "last_move_name", None) or "") == str(name):
                score -= 15.0

            # Fuzzing noise to avoid deterministic "robot" behavior
            score += float(random.randint(0, 4))
            return score

        # Finisher priority: if a finisher is available, try to end it.
        finishers = [m for m in valid if bool(MOVES.get(m, {}).get("is_finisher"))]
        if finishers:
            if (mode != "RND") or (random.random() >= 0.25):
                finishers.sort(key=move_value, reverse=True)
                return finishers[0]

        scored = [(move_value(m), m) for m in valid]
        scored.sort(key=lambda t: float(t[0]), reverse=True)
        ordered = [m for _s, m in scored]

        if mode == "GREED":
            return ordered[0]
        if mode == "GOOD":
            return random.choice(ordered[: min(3, len(ordered))])
        if mode == "BAD":
            tail = ordered[max(0, len(ordered) - 3) :]
            return random.choice(tail or ordered)
        return random.choice(ordered)

    def _cpu_choose_cards(self, move_name, *, mode: str | None = None):
        hand = list(self.cpu.hand or [])
        if not hand:
            return []

        # Finishers require doubles.
        is_finisher = bool(MOVES.get(move_name, {}).get("is_finisher"))

        ignore_card_cost = (move_name == MOVE_REST)
        move_cost = int(MOVES.get(move_name, {}).get("cost", 0))

        defensive_only_small = (move_name == MOVE_DEFENSIVE)
        groggy_only_small = False

        candidates: list[dict] = []

        # Singles
        if not is_finisher:
            for c in hand:
                if defensive_only_small and int(c.value) > 5:
                    continue
                if groggy_only_small and int(c.value) > 7:
                    continue
                card_cost = 0 if ignore_card_cost else int(c.grit_cost())
                if int(self.cpu.grit) >= int(move_cost) + int(card_cost):
                    candidates.append({"cards": [c], "score": int(c.value)})

        # Doubles
        by_val: dict[int, list] = {}
        for c in hand:
            by_val.setdefault(int(c.value), []).append(c)
        for _v, cs in by_val.items():
            if len(cs) >= 2:
                if defensive_only_small and int(cs[0].value) > 5:
                    continue
                if groggy_only_small and int(cs[0].value) > 7:
                    continue
                pair = [cs[0], cs[1]]
                card_cost = 0 if ignore_card_cost else sum(int(x.grit_cost()) for x in pair)
                if int(self.cpu.grit) >= int(move_cost) + int(card_cost):
                    v = int(cs[0].value)
                    candidates.append({"cards": pair, "score": int(v + v + 5)})

        # Same-color pair: high card +2 (capped at 10). (Not allowed for finishers.)
        if not is_finisher:
            by_col: dict[str, list] = {}
            for c in hand:
                by_col.setdefault(str(c.color), []).append(c)
            for col, cs in by_col.items():
                if len(cs) < 2:
                    continue
                # If there is a doubles pair in this color, it's already covered above.
                cs_sorted = sorted(cs, key=lambda x: int(x.value), reverse=True)
                a = cs_sorted[0]
                b = next((x for x in cs_sorted[1:] if int(x.value) != int(a.value)), None)
                if b is None:
                    continue
                if defensive_only_small and (int(a.value) > 5 or int(b.value) > 5):
                    continue
                if groggy_only_small and (int(a.value) > 7 or int(b.value) > 7):
                    continue
                pair = [a, b]
                card_cost = 0 if ignore_card_cost else sum(int(x.grit_cost()) for x in pair)
                if int(self.cpu.grit) >= int(move_cost) + int(card_cost):
                    hi = max(int(a.value), int(b.value))
                    score = min(10, int(hi) + 2)
                    candidates.append({"cards": pair, "score": int(score)})

        if not candidates:
            return []

        candidates.sort(key=lambda d: int(d.get("score", 0)), reverse=True)
        mode = str(mode or self._cpu_ai_mode())
        if mode == "GREED":
            return list(candidates[0]["cards"])
        if mode == "GOOD":
            pool = candidates[: min(3, len(candidates))]
            return list(random.choice(pool)["cards"])
        if mode == "BAD":
            pool = candidates[max(0, len(candidates) - 3) :]
            return list(random.choice(pool or candidates)["cards"])
        return list(random.choice(candidates)["cards"])

    # -------------------------------------------------------------------------
    # UI EVENT HANDLERS
    # -------------------------------------------------------------------------

    def _on_fire_up_click(self, _inst=None) -> None:
        if self.game_over:
            return
        if self._escape_mode is not None:
            return
        mom = int(getattr(self, "momentum", 0))
        if mom <= 0:
            return
        bonus = int(mom) * 2
        self.momentum = 0
        self.player.next_card_bonus = int(self.player.next_card_bonus) + int(bonus)
        self._log(f"FIRE UP! You cash in momentum (+{bonus} to next card).")
        self._update_hud()
        self._render_moves_ui()
        self._update_control_bar()
    
    def _update_hud(self):
        def state_name(w: Wrestler) -> str:
            st = getattr(w, "state", None)
            return str(getattr(st, "name", st))

        def role_name(w: Wrestler) -> str:
            gr = getattr(w, "grapple_role", None)
            return str(getattr(gr, "name", "NEUTRAL")) if gr is not None else "NEUTRAL"

        def flow(w: Wrestler) -> str:
            if not w.is_flow():
                return ""
            return f" [FLOW {w.flow_turns_remaining}]"

        def grog(w: Wrestler) -> str:
            if bool(getattr(w, "is_groggy", False)):
                return " [GROGGY]"
            return ""

        def dazed(w: Wrestler) -> str:
            dt = int(getattr(w, "daze_turns", 0) or 0)
            return f" [DAZED {dt}]" if dt > 0 else ""

        p_state = state_name(self.player)
        c_state = state_name(self.cpu)
        p_role = role_name(self.player)
        c_role = role_name(self.cpu)
        self.state_label.text = (
            f"[b]STATE:[/b] {p_state} ({p_role}){flow(self.player)}{grog(self.player)}{dazed(self.player)}"
            f"  |  CPU: {c_state} ({c_role}){flow(self.cpu)}{grog(self.cpu)}{dazed(self.cpu)}"
        )

        # Always-visible per-wrestler state lines under names.
        try:
            if hasattr(self, "player_state_small"):
                self.player_state_small.text = f"STATE: {p_state}" if p_role == "NEUTRAL" else f"STATE: {p_state} ({p_role})"
            if hasattr(self, "cpu_state_small"):
                self.cpu_state_small.text = f"STATE: {c_state}" if c_role == "NEUTRAL" else f"STATE: {c_state} ({c_role})"
        except Exception:
            pass

        # Momentum
        mom = int(getattr(self, "momentum", 0))
        mom = max(-int(MOMENTUM_MAX_ABS), min(int(MOMENTUM_MAX_ABS), mom))
        if mom > 0:
            hexc = COLOR_HEX_MOMENTUM_POS
        elif mom < 0:
            hexc = COLOR_HEX_MOMENTUM_NEG
        else:
            hexc = COLOR_HEX_MOMENTUM_NEU
        self.momentum_label.text = f"[color={hexc}]MOMENTUM {mom:+d}[/color]"
        self.momentum_bar.max_abs = int(MOMENTUM_MAX_ABS)
        self.momentum_bar.value_signed = int(mom)
        self.momentum_bar.bar_color = get_color_from_hex(COLOR_HEX_MOMENTUM_POS if mom >= 0 else COLOR_HEX_MOMENTUM_NEG)

        try:
            if hasattr(self, "fire_up_btn"):
                self.fire_up_btn.disabled = int(mom) <= 0
        except Exception:
            pass

        # HP Fog-of-War: show only status bands, not exact numbers.
        self.player_hp_label.text = f"{self.player.name}: {self._get_hp_status(self.player.hp)}"
        self.cpu_hp_label.text = f"{self.cpu.name}: {self._get_hp_status(self.cpu.hp)}"
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

        def move_type_for_selected() -> str | None:
            if not self.selected_move:
                return None
            try:
                return str(MOVES.get(self.selected_move, {}).get("type", "Setup"))
            except Exception:
                return None

        def pending_mod_parts(card) -> list[str]:
            parts: list[str] = []

            # Move-type color bonus (+1) is conditional on selected move.
            mt = move_type_for_selected()
            if mt and mt not in {"Setup", "Defensive"}:
                try:
                    tb = int(card.color_bonus(mt))
                    if tb:
                        parts.append(f"+{tb} TYPE")
                except Exception:
                    pass

            # Hype Shop: next played card bonus.
            try:
                nb = int(getattr(self.player, "next_card_bonus", 0))
                if nb > 0:
                    parts.append(f"+{nb} HYPE")
            except Exception:
                pass

            # Momentum score modifier (only positive affects player).
            try:
                mom = int(getattr(self, "momentum", 0))
                mom = max(-int(MOMENTUM_MAX_ABS), min(int(MOMENTUM_MAX_ABS), mom))
                mag = abs(int(mom))
                if mag == 0:
                    mom_scaled = 0
                elif mag <= int(MOMENTUM_SCORE_TIER1_MAX):
                    mom_scaled = int(MOMENTUM_SCORE_TIER1_BONUS)
                else:
                    mom_scaled = int(MOMENTUM_SCORE_TIER2_BONUS)
                if mom < 0:
                    mom_scaled = -int(mom_scaled)
                if int(mom_scaled) > 0:
                    parts.append(f"+{int(mom_scaled)} MOM")
            except Exception:
                pass

            return parts

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

            selected = (i in self.selected_cards)

            parts = pending_mod_parts(card)
            if parts:
                mods_txt = "  " + "  ".join(parts)
                text = f"[b][size=22sp]{int(card.value)}[/size][/b]\n[size=12sp][color={COLOR_HEX_SETUP_LOG}]{mods_txt}[/color][/size]"
                markup = True
            else:
                text = str(card.value)
                markup = False

            btn = BorderedButton(
                text=text,
                markup=markup,
                background_color=bg, background_normal="",
                font_size='24sp', bold=True
            )
            # Hand cards should center cleanly and avoid awkward wrapping/clipping.
            try:
                btn.auto_wrap = False
                btn.halign = "center"
                btn.valign = "middle"
                btn.padding = [dp(4), dp(4)]
                btn.bind(size=lambda inst, _v: setattr(inst, 'text_size', inst.size))
                btn.text_size = btn.size
            except Exception:
                pass
            btn.border_color = list(COLOR_CARD_SELECTED)
            btn.border_width = float(dp(2))
            btn.show_border = bool(selected)
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
        # Include momentum-gated moves so categories remain visible (they'll render disabled inside).
        moves = self._available_moves(self.player, self.cpu, ignore_momentum_gate=True)
        if category == "STRIKES":
            return any(MOVES[m].get("type") == "Strike" for m in moves)
        if category == "GRAPPLES":
            return any(MOVES[m].get("type") in {"Grapple", "Submission", "Pin"} for m in moves)
        if category == "AERIAL_RUNNING":
            def is_aerial_running(m: str) -> bool:
                mv = MOVES.get(m, {})
                t = str(mv.get("type", "Setup"))
                ru = str(mv.get("req_user_state", "ANY"))
                rt = str(mv.get("req_target_state", "ANY"))
                su = str(mv.get("set_user_state", ""))
                return (
                    t == "Aerial"
                    or ru in {"RUNNING", "TOP_ROPE"}
                    or su in {"RUNNING", "TOP_ROPE"}
                    or rt == "TOSSED"
                )

            return any(is_aerial_running(m) for m in moves)
        if category == "UTILITY":
            def is_utility(m: str) -> bool:
                mv = MOVES.get(m, {})
                t = str(mv.get("type", "Setup"))
                su = str(mv.get("set_user_state", ""))
                # Keep Utility for true utility; exclude “charge up”/“climb” style state-setters.
                if t == "Defensive":
                    return True
                if t != "Setup":
                    return False
                if su in {"RUNNING", "TOP_ROPE"}:
                    return False
                return True

            return any(is_utility(m) for m in moves)
        return True

    def _render_moves_ui(self) -> None:
        self.move_list_layout.clear_widgets()
        # Default to 3 columns; certain stages (like ESCAPE) override.
        try:
            self.move_list_layout.cols = 3
        except Exception:
            pass

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
                return COLOR_SUBMIT
            if t == "Defensive":
                return COLOR_DEFENSIVE
            return COLOR_BTN_BASE

        # Escape stage UI
        if self._menu_stage == "ESCAPE" and self._escape_mode:
            try:
                self.move_list_layout.cols = 1
            except Exception:
                pass
            info = self._escape_mode
            defender_is_player = bool(info.get("defender_is_player"))
            if defender_is_player:
                instr = "Select a card, then press PLAY (no redraw)."
            else:
                instr = "CPU is escaping. Press CONTINUE between beats."
            lbl = Label(
                text=f"ESCAPE!  Total: {info.get('total', 0)}/{info.get('threshold', 1)}   Plays left: {info.get('plays_left', 0)}\n{instr}",
                color=COLOR_TEXT_SOFT,
                size_hint_y=None,
                height=84,
                halign="left",
                valign="middle",
            )
            lbl.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))
            self.move_list_layout.add_widget(lbl)

            if not defender_is_player:
                btn = Button(
                    text="CONTINUE",
                    background_color=get_color_from_hex(COLOR_HEX_PLAY_ENABLED),
                    background_normal="",
                    size_hint_y=None,
                    height=dp(54),
                )
                btn.disabled = self.game_over or int(info.get("plays_left", 0)) <= 0
                btn.bind(on_release=self._escape_continue_cpu)
                self.move_list_layout.add_widget(btn)
            return

        # Categories
        if self._menu_stage == "CATEGORIES":
            if bool(getattr(self.player, "is_groggy", False)):
                lbl = Label(
                    text="[b]STUNNED![/b]\nTry to recover — max card value 7.",
                    markup=True,
                    color=COLOR_TEXT_SOFT,
                    size_hint_y=None,
                    height=dp(64),
                    halign="left",
                    valign="middle",
                )
                lbl.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))
                self.move_list_layout.add_widget(lbl)

                def pick(_inst=None) -> None:
                    self.selected_move = MOVE_GROGGY_RECOVERY
                    self.selected_cards.clear()
                    self._render_hand()
                    self._update_play_button()

                btn = Button(
                    text="[b]GROGGY RECOVERY[/b]",
                    markup=True,
                    size_hint_x=1,
                    size_hint_y=None,
                    height=BTN_HEIGHT_CATEGORY,
                    background_normal="",
                    background_color=COLOR_BTN_BASE,
                )
                btn.bind(on_release=pick)
                self.move_list_layout.add_widget(btn)
                return

            if self.player.state == WrestlerState.STANDING:
                lock_ok = bool(
                    self._passes_moveset(self.player, MOVE_LOCK_UP)
                    and self.player.state == WrestlerState.STANDING
                    and self.cpu.state == WrestlerState.STANDING
                    and (not bool(getattr(self.player, "is_groggy", False)))
                )
                lock_btn = Button(
                    text=(
                        "[b]LOCK UP[/b]"
                        if lock_ok
                        else "[b]LOCK UP[/b]\n[size=13sp]Need both standing[/size]"
                        if self.cpu.state != WrestlerState.STANDING
                        else "[b]LOCK UP[/b]\n[size=13sp]You are groggy[/size]"
                        if bool(getattr(self.player, "is_groggy", False))
                        else "[b]LOCK UP[/b]\n[size=13sp]Not in moveset[/size]"
                    ),
                    markup=True,
                    size_hint_x=1,
                    size_hint_y=None,
                    height=BTN_HEIGHT_CATEGORY,
                    background_normal="",
                    background_color=COLOR_BTN_BASE,
                )
                lock_btn.disabled = not lock_ok
                lock_btn.bind(on_release=lambda _inst=None: self._do_lock_up())
                self.move_list_layout.add_widget(lock_btn)

                # Convenience: if opponent is grounded, surface Pick Up prominently.
                if self.cpu.state == WrestlerState.GROUNDED:
                    pick_ok = bool(self._move_is_legal("util_pick_up", self.player, self.cpu) and self._passes_moveset(self.player, "util_pick_up"))
                    pick_btn = Button(
                        text=("[b]PICK UP[/b]" if pick_ok else "[b]PICK UP[/b]\n[size=13sp]Not available[/size]"),
                        markup=True,
                        size_hint_x=1,
                        size_hint_y=None,
                        height=BTN_HEIGHT_CATEGORY,
                        background_normal="",
                        background_color=COLOR_BTN_BASE,
                    )
                    pick_btn.disabled = not pick_ok
                    pick_btn.bind(on_release=lambda _inst=None: self._on_category_click("GRAPPLES"))
                    self.move_list_layout.add_widget(pick_btn)

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
                    bg = COLOR_SUBMIT
                elif key == "HYPE_SHOP":
                    bg = COLOR_HYPE_SHOP
                else:
                    bg = COLOR_BTN_BASE

                btn = Button(
                    text=f"[b]{label}[/b]",
                    markup=True,
                    size_hint_x=1,
                    size_hint_y=None,
                    height=BTN_HEIGHT_CATEGORY,
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

            def buy_grit_refill(_inst=None) -> None:
                if self.player.hype < 30:
                    return
                if int(self.player.grit) >= int(self.player.max_grit):
                    return
                self.player.hype -= 30
                before = int(self.player.grit)
                self.player.grit = min(self.player.max_grit, int(self.player.grit) + 4)
                gained = int(self.player.grit) - before
                self._log(f"Hype Shop: Grit Refill! (+{gained} Grit)")
                self._update_hud()
                self._render_moves_ui()
                self._update_control_bar()

            def buy_lockup_edge(_inst=None) -> None:
                if self.player.hype < 50:
                    return
                if bool(getattr(self.player, "lockup_edge_ready", False)):
                    return
                self.player.hype -= 50
                self.player.lockup_edge_ready = True
                self._log("Hype Shop: Lock Up Edge purchased (next Lock Up you initiate auto-wins).")
                self._update_hud()
                self._render_moves_ui()
                self._update_control_bar()

            b1 = BorderedButton(text="Pump Up\n(25 Hype): Next card +1", size_hint_y=None, height=BTN_HEIGHT_SHOP, background_normal="", background_color=COLOR_BTN_BASE)
            b2 = BorderedButton(text="Adrenaline\n(50 Hype): Next card +2", size_hint_y=None, height=BTN_HEIGHT_SHOP, background_normal="", background_color=COLOR_BTN_BASE)
            b_edge = BorderedButton(text="Lock Up Edge\n(50 Hype): Auto-win next Lock Up", size_hint_y=None, height=BTN_HEIGHT_SHOP, background_normal="", background_color=COLOR_BTN_BASE)
            b_grit = BorderedButton(text="Grit Refill\n(30 Hype): +4 Grit", size_hint_y=None, height=BTN_HEIGHT_SHOP, background_normal="", background_color=COLOR_BTN_BASE)
            b3 = BorderedButton(text="Second Wind\n(80 Hype): Heal 15 HP", size_hint_y=None, height=BTN_HEIGHT_SHOP, background_normal="", background_color=COLOR_BTN_BASE)
            b1.disabled = self.player.hype < 25
            b2.disabled = self.player.hype < 50
            b_edge.disabled = (self.player.hype < 50) or bool(getattr(self.player, "lockup_edge_ready", False))
            b_grit.disabled = (self.player.hype < 30) or (int(self.player.grit) >= int(self.player.max_grit))
            b3.disabled = self.player.hype < 80
            b1.bind(on_release=buy_pump)
            b2.bind(on_release=buy_adrenaline)
            b_edge.bind(on_release=buy_lockup_edge)
            b_grit.bind(on_release=buy_grit_refill)
            b3.bind(on_release=buy_second_wind)
            self.move_list_layout.add_widget(b1)
            self.move_list_layout.add_widget(b2)
            self.move_list_layout.add_widget(b_edge)
            self.move_list_layout.add_widget(b_grit)
            self.move_list_layout.add_widget(b3)
            return

        # Moves within category
        if self._menu_stage == "MOVES":
            cat = str(self._selected_category or "UTILITY")
            # Show momentum-gated moves, but render them disabled until eligible.
            avail = self._available_moves(self.player, self.cpu, ignore_momentum_gate=True)

            def in_cat(name: str) -> bool:
                t = str(MOVES[name].get("type", "Setup"))
                ru = str(MOVES[name].get("req_user_state", "ANY"))
                rt = str(MOVES[name].get("req_target_state", "ANY"))
                if cat == "STRIKES":
                    return t == "Strike"
                if cat == "GRAPPLES":
                    return (t in {"Grapple", "Submission", "Pin"}) or (name == "util_pick_up")
                if cat == "AERIAL_RUNNING":
                    su = str(MOVES[name].get("set_user_state", ""))
                    return (
                        t == "Aerial"
                        or ru in {"RUNNING", "TOP_ROPE"}
                        or su in {"RUNNING", "TOP_ROPE"}
                        or rt == "TOSSED"
                    )
                if cat == "UTILITY":
                    # Exclude setup moves that exist primarily to set RUNNING/TOP_ROPE state.
                    if t == "Defensive":
                        return True
                    if t != "Setup":
                        return False
                    su = str(MOVES[name].get("set_user_state", ""))
                    if su in {"RUNNING", "TOP_ROPE"}:
                        return False
                    return True
                return True

            moves_to_show = [m for m in avail if in_cat(m)]
            if not moves_to_show:
                lbl = Label(
                    text="[b]NO MOVES AVAILABLE[/b]\n(Wrong State)",
                    markup=True,
                    color=COLOR_TEXT_SOFT,
                    size_hint_y=None,
                    height=dp(64),
                    halign="left",
                    valign="middle",
                )
                lbl.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))
                self.move_list_layout.add_widget(lbl)

                # Still show any always-useful safety moves that are currently legal.
                safety = [
                    MOVE_SHOVE_OFF,
                    MOVE_FIGHT_FOR_CONTROL,
                    MOVE_SLOW_STAND_UP,
                    MOVE_KIP_UP,
                    MOVE_CLIMB_DOWN,
                    MOVE_STOP_SHORT,
                    MOVE_DEFENSIVE,
                    MOVE_REST,
                    MOVE_TAUNT,
                ]
                moves_to_show = [m for m in avail if m in safety]
                if not moves_to_show:
                    return

            moves_to_show = moves_to_show[:18]

            has_doubles = self.player.has_doubles_in_hand()
            for slug in moves_to_show:
                mv = MOVES[slug]
                disp = self._move_display_name(slug)
                finisher = bool(mv.get("is_finisher"))
                mc = int(self._move_base_cost(slug))
                no_grit = int(self.player.grit) < int(mc)
                gate_req = int(self._move_req_momentum_min(slug))
                gate_locked = bool(gate_req > 0 and (not self._has_momentum_for_move(self.player, slug)))
                disabled = bool((finisher and (not has_doubles)) or no_grit or gate_locked)
                t = str(mv.get("type", "Setup"))

                if finisher and not disabled:
                    bg = COLOR_FINISHER
                else:
                    bg = COLOR_DEFENSIVE if disabled else type_color(t)

                selected = (self.selected_move == slug)
                if selected and (not disabled):
                    bg = brighten(bg)

                if (not disabled) and getattr(self.player, "chain_window", None) == slug and int(getattr(self.player, "chain_turns_remaining", 0)) > 0:
                    bg = brighten(COLOR_CHAIN, 1.05)

                star = "★ " if finisher else ""
                dmg = int(mv.get('damage', 0))
                if slug == MOVE_DEFENSIVE:
                    label = f"[b]{star}{disp}[/b]\n[size=13sp]Discard (≤5) to Block[/size]"
                elif slug == MOVE_FIGHT_FOR_CONTROL:
                    if self.player.is_in_grapple() and self.player.grapple_role == GrappleRole.OFFENSE:
                        sub = "Upgrade to Strong Grapple"
                    elif self.player.is_in_grapple() and self.player.grapple_role == GrappleRole.DEFENSE:
                        sub = "Break Hold / Reverse"
                    else:
                        sub = "Contest Control"
                    label = f"[b]{star}{disp}[/b]\n[size=13sp]{sub}[/size]"
                else:
                    label = f"[b]{star}{disp}[/b]\n[size=13sp]{dmg} DMG | [color={COLOR_HEX_GRIT}]{mc} GRIT[/color][/size]"
                if no_grit and slug not in {MOVE_DEFENSIVE, MOVE_FIGHT_FOR_CONTROL}:
                    label = label + f"\n[size=12sp][color={COLOR_HEX_HP_STRAINED}]NO GRIT[/color][/size]"
                if gate_locked:
                    label = label + f"\n[size=12sp][color={COLOR_HEX_HP_STRAINED}]NEED {gate_req} MOMENTUM[/color][/size]"
                btn = BorderedButton(
                    text=label,
                    markup=True,
                    size_hint_y=None,
                    height=BTN_HEIGHT_MOVE,
                    background_normal="",
                    background_color=bg,
                )
                btn.border_color = list(COLOR_CARD_SELECTED)
                btn.border_width = float(dp(2))
                btn.show_border = bool(selected and (not disabled))
                btn.disabled = disabled
                btn.move_name = slug
                btn.bind(on_release=self._on_move_click)
                self.move_list_layout.add_widget(btn)
            return

    def _on_move_click(self, instance):
        name = str(getattr(instance, "move_name", ""))
        if not name:
            return

        # Momentum-gated moves can be visible but disabled; guard here too.
        if not self._move_is_legal(name, self.player, self.cpu):
            req = int(self._move_req_momentum_min(name))
            if req > 0:
                have = int(self._momentum_advantage_for(self.player))
                self._log(f"Need momentum {req} (you have {have}).")
            else:
                self._log("That move isn't legal right now.")
            return

        # Lock Up resolves immediately (no card selection).
        if name == MOVE_LOCK_UP:
            self._do_lock_up()
            return

        self.selected_move = name
        self.selected_cards.clear()
        self._render_hand()
        self._render_moves_ui()
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
        if not self._move_is_legal(MOVE_LOCK_UP, self.player, self.cpu):
            # Better diagnostics to avoid confusion.
            reasons: list[str] = []
            try:
                cost = int(self._move_base_cost(MOVE_LOCK_UP))
                if int(self.player.grit) < cost:
                    reasons.append(f"need {cost} grit")
                if self.player.state != WrestlerState.STANDING:
                    reasons.append(f"you are {self.player.state.name}")
                if self.cpu.state != WrestlerState.STANDING:
                    reasons.append(f"CPU is {self.cpu.state.name}")
                if bool(getattr(self.player, "is_groggy", False)):
                    reasons.append("you are groggy")
            except Exception:
                pass
            tail = (" (" + ", ".join(reasons) + ")") if reasons else ""
            self._log("Lock Up is not legal right now." + tail)
            return

        # Hype Shop buff: next Lock Up you initiate is an auto-win.
        if bool(getattr(self.player, "lockup_edge_ready", False)):
            self.player.lockup_edge_ready = False
            self._log("Lock Up Edge! You seize control instantly!")
            self._apply_lockup_result(True)
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
        right = BoxLayout(orientation="vertical", spacing=8, size_hint_x=0.30)

        prompt = Label(
            text="LOCK UP\nGet closer to 15 without going over.",
            size_hint_y=None,
            height=dp(52),
            halign="left",
            valign="middle",
            color=COLOR_TEXT_PROMPT,
        )
        prompt.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))

        status = Label(
            text="YOU: 0   |   CPU: 0",
            size_hint_y=None,
            height=dp(24),
            color=COLOR_TEXT_SOFT,
            halign="left",
            valign="middle",
        )
        status.bind(size=lambda inst, _v: setattr(inst, 'text_size', (inst.width, None)))

        msg = Label(
            text="PUSH adds 1–6. HOLD lets CPU respond.",
            size_hint_y=None,
            height=dp(70),
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

        pop = Popup(title="Lock Up", content=root, size_hint=(0.92, 0.45), auto_dismiss=False)

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

        # Rest never uses cards.
        if self.selected_move == MOVE_REST:
            return

        # Escape mode: select 1 card, then press PLAY.
        if self._escape_mode is not None and bool(self._escape_mode.get("defender_is_player")):
            if idx in self.selected_cards:
                self.selected_cards.remove(idx)
            else:
                self.selected_cards.clear()
                self.selected_cards.add(idx)
            self._render_hand()
            self._update_play_button()
            return

        if not self.selected_move:
            # Cards are only selectable after choosing a move.
            if not bool(getattr(self, "_card_tap_hint_shown", False)):
                self._card_tap_hint_shown = True
                self._log("Pick a move first (category → move), then select your card(s).")
            return

        hand = list(self.player.hand or [])
        if idx >= len(hand):
            return

        if idx in self.selected_cards:
            self.selected_cards.remove(idx)
        else:
            if len(self.selected_cards) >= 2:
                self._log("Max 2 cards.")
                return

            # Defensive: only <=5
            if self.selected_move == MOVE_DEFENSIVE and int(hand[idx].value) > 5:
                self._log("Defensive can only discard cards value ≤ 5.")
                return

            # Groggy Recovery: value is capped at 7 for scoring; any card may be discarded.

            # Normal: if choosing second card, must be doubles
            if self.selected_move != MOVE_DEFENSIVE and len(self.selected_cards) == 1:
                first_idx = next(iter(self.selected_cards))
                same_val = (int(hand[first_idx].value) == int(hand[idx].value))
                same_col = (str(hand[first_idx].color) == str(hand[idx].color))
                if not (same_val or same_col):
                    self._log("Two-card play: must match value (doubles) OR match color (+2 to high card).")
                    return

            self.selected_cards.add(idx)

        self._render_hand()

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
            if bool(getattr(self.player, "is_groggy", False)):
                self.hint_label.text = "GROGGY! Pick Groggy Recovery."
            else:
                self.hint_label.text = "Pick a category."
        elif self._menu_stage == "HYPE_SHOP":
            self.hint_label.text = "Spend hype for a boost."
        elif self._menu_stage == "MOVES":
            if not self.selected_move:
                self.hint_label.text = "Pick a move."
            elif self.selected_move == MOVE_DEFENSIVE:
                self.hint_label.text = "Defensive: discard 0–2 cards (≤5)."
            elif self.selected_move == MOVE_GROGGY_RECOVERY:
                self.hint_label.text = "Groggy Recovery: play 1 card, doubles, or same-color (+2 to high). Max value 7."
            else:
                self.hint_label.text = "Select 1 card, doubles, or same-color (+2 to high), then PLAY."
        elif self._menu_stage == "ESCAPE":
            self.hint_label.text = "ESCAPE! Select 1 card, then PLAY."
        else:
            self.hint_label.text = ""

        # Play button enable + cost text
        enabled = False
        cost = 0
        move_name = self.selected_move

        if self.game_over:
            enabled = False
        elif self._menu_stage == "ESCAPE":
            enabled = bool(self._escape_mode is not None) and bool(self._escape_mode.get("defender_is_player")) and (len(self.selected_cards) == 1)
        elif self._menu_stage != "MOVES":
            enabled = False
        elif not move_name:
            enabled = False
        else:
            cards = self._selected_player_cards()
            selected_count = len(self.selected_cards)
            if move_name == MOVE_DEFENSIVE:
                enabled = (selected_count in {0, 1, 2}) and (selected_count == 0 or bool(cards))
            else:
                enabled = (selected_count in {1, 2}) and bool(cards)

            if enabled:
                # Final legality check (includes momentum gate).
                if not self._move_is_legal(move_name, self.player, self.cpu):
                    enabled = False

            if enabled:
                cost = self._effective_cost(self.player, move_name, cards)
                if int(self.player.grit) < int(cost):
                    enabled = False

        self.play_btn.disabled = not enabled
        if enabled:
            self.play_btn.background_color = get_color_from_hex(COLOR_HEX_PLAY_ENABLED)
            if self._menu_stage == "ESCAPE":
                self.play_btn.text = "PLAY\n(ESCAPE)"
            else:
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
        if self._escape_mode is not None and bool(self._escape_mode.get("defender_is_player")) and self._menu_stage == "ESCAPE":
            self._submit_escape_card()
        else:
            self._submit_cards()

    def _submit_escape_card(self) -> None:
        if self.game_over:
            return
        if self._escape_mode is None:
            return
        if not bool(self._escape_mode.get("defender_is_player")):
            return
        if self._menu_stage != "ESCAPE":
            return
        if len(self.selected_cards) != 1:
            return
        idx = next(iter(self.selected_cards))
        self.selected_cards.clear()
        self._escape_play_card(int(idx))

    def _submit_cards(self) -> None:
        if self.game_over:
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
        if self.selected_move == MOVE_DEFENSIVE:
            if len(p_cards) > 2:
                self._log("Defensive: discard up to 2 cards (value ≤ 5).")
                return
        else:
            if not p_cards:
                self._log("Select 1 card, doubles, or same-color (+2 to high).")
                return

        total_cost = self._effective_cost(self.player, self.selected_move, p_cards)
        if int(self.player.grit) < int(total_cost):
            self._log("Not enough grit (move + card cost).")
            return

        self._cpu_buy_buffs()
        cpu_mode = self._cpu_ai_mode()
        self._last_cpu_mode = str(cpu_mode)
        c_move = self._cpu_choose_move(mode=cpu_mode)
        c_cards = self._cpu_choose_cards(c_move, mode=cpu_mode)
        # Degrade AI card choice if it somehow can't afford.
        c_total = self._effective_cost(self.cpu, c_move, c_cards)
        if int(self.cpu.grit) < int(c_total):
            hand = list(self.cpu.hand or [])
            hand.sort(key=lambda c: int(c.value))
            c_cards = []
            for c in hand:
                if c_move == MOVE_DEFENSIVE and int(c.value) > 5:
                    continue
                test = self._effective_cost(self.cpu, c_move, [c])
                if int(self.cpu.grit) >= int(test):
                    c_cards = [c]
                    break

            # Defensive is allowed to play 0 cards.
            if c_move == MOVE_DEFENSIVE and not c_cards:
                c_cards = []

        self._resolve_clash(self.selected_move, p_cards, c_move, c_cards)

    def _on_return_click(self, instance):
        self.selected_move = None
        self.selected_cards.clear()
        self._render_hand()
        self._set_menu_stage("CATEGORIES")

    # -------------------------------------------------------------------------
    # ESCAPE MODE UI
    # -------------------------------------------------------------------------

    def _render_escape_ui(self):
        self._render_moves_ui()
        self._update_control_bar()

if __name__ == "__main__":
    WrestleApp().run()
