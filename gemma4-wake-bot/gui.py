# gui.py
# ─── Bujji AI Assistant — Tkinter Desktop GUI (Enhanced) ─────────────────────
#
# Drop this file into the root of your Bujji project (same folder as main.py).
# Launch with:  python gui.py
#
# It reuses all your existing modules unchanged.
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import threading
import time
import subprocess
import tkinter as tk
from tkinter import font as tkfont
import requests

# ── Path setup (same as main.py) ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import (
    WAKE_WORD,
    WAKE_CONFIRMATION,
    COMMAND_RECORD_SECONDS,
    RECOGNITION_MODE,
    API_URL,
)
from modules.wake_listener  import contains_wake_word, listen_for_wake_word_once
from modules.voice_input    import listen_once
from modules.voice_output   import speak
from modules.translator     import translate_to_telugu, translate_to_english, detect_language
from modules.intent_router  import route
from modules.system_control import (
    volume_up, volume_down, set_volume, mute, unmute,
    brightness_up, brightness_down, set_brightness,
    enable_dark_mode, disable_dark_mode, toggle_dark_mode,
    wifi_on, wifi_off, bluetooth_on, bluetooth_off,
    enable_do_not_disturb, disable_do_not_disturb,
    sleep_display, take_screenshot, get_battery, get_time,
    open_website, search_google, open_app, open_folder,
    get_clipboard, empty_trash, lock_screen,
    check_system_tools,
)


# ─────────────────────────────────────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────────────────────────────────────
BG           = "#0b0c10"
SIDEBAR_BG   = "#14151a"
PANEL_BG     = "#1c1d25"
CARD_BG      = "#242631"
CARD_HOVER   = "#2d303e"
BUBBLE_USER  = "#4f46e5"
BUBBLE_BOT   = "#242631"
TEXT_MAIN    = "#f1f1f4"
TEXT_DIM     = "#9499b3"
TEXT_MUTED   = "#4b4e6d"
ACCENT       = "#6366f1" # Indigo-Vibrant
ACCENT2      = "#8b5cf6" # Violet-Power
ACCENT_HOT   = "#f43f5e"
ACCENT_GREEN = "#10b981"
ACCENT_AMBER = "#f59e0b"
DIVIDER      = "#2d303e"
PILL_BG      = "#2d303e"
PILL_SEL     = "#6366f1"

FONT_BODY    = 11
FONT_SMALL   = 9
FONT_TITLE   = 14
FONT_CARD    = 10


# ─────────────────────────────────────────────────────────────────────────────
#  SYSTEM CONTROLS REGISTRY
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_CONTROLS = {
    "🔊  Audio": [
        ("Vol Up",      "🔊", lambda: volume_up()),
        ("Vol Down",    "🔉", lambda: volume_down()),
        ("Vol 50 %",    "🔈", lambda: set_volume(50)),
        ("Mute",        "🔇", lambda: mute()),
        ("Unmute",      "📢", lambda: unmute()),
    ],
    "☀️  Display": [
        ("Bright Up",   "☀️",  lambda: brightness_up()),
        ("Bright Down", "🌑", lambda: brightness_down()),
        ("Bright 60 %", "💡", lambda: set_brightness(60)),
        ("Dark Mode",   "🌙", lambda: enable_dark_mode()),
        ("Light Mode",  "🌤", lambda: disable_dark_mode()),
        ("Toggle Dark", "🔄", lambda: toggle_dark_mode()),
    ],
    "📶  Network": [
        ("Wi-Fi On",    "📶", lambda: wifi_on()),
        ("Wi-Fi Off",   "🚫", lambda: wifi_off()),
        ("BT On",       "🔵", lambda: bluetooth_on()),
        ("BT Off",      "⭕", lambda: bluetooth_off()),
    ],
    "🖥  System": [
        ("DND On",      "🔕", lambda: enable_do_not_disturb()),
        ("DND Off",     "🔔", lambda: disable_do_not_disturb()),
        ("Sleep",       "😴", lambda: sleep_display()),
        ("Screenshot",  "📸", lambda: take_screenshot()),
        ("Battery",     "🔋", lambda: get_battery()),
        ("Time",        "🕐", lambda: get_time()),
        ("Clipboard",   "📋", lambda: get_clipboard()),
        ("Empty Trash", "🗑", lambda: empty_trash()),
        ("Lock Screen", "🔒", lambda: lock_screen()),
    ],
    "📱  Apps": [
        ("YouTube",     "▶️",  lambda: open_website("youtube")),
        ("Google",      "🔍", lambda: search_google("Python tutorials")),
        ("Calculator",  "🔢", lambda: open_app("Calculator")),
        ("Downloads",   "📁", lambda: open_folder("downloads")),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER — rounded rectangle on Canvas
# ─────────────────────────────────────────────────────────────────────────────
def rounded_rect(canvas, x1, y1, x2, y2, r=18, **kwargs):
    points = [
        x1+r, y1, x2-r, y1,
        x2, y1, x2, y1+r,
        x2, y2-r, x2, y2,
        x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r,
        x1, y1+r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
#  CHAT BUBBLE
# ─────────────────────────────────────────────────────────────────────────────
class BubbleFrame(tk.Frame):
    PAD_H = 14
    PAD_V = 10
    MAX_W = 380

    def __init__(self, parent, text: str, sender: str, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        is_user  = sender == "user"
        bg_color = BUBBLE_USER if is_user else BUBBLE_BOT
        fg_color = TEXT_MAIN

        dummy = tk.Label(self, text=text, font=("Helvetica", FONT_BODY),
                         wraplength=self.MAX_W - self.PAD_H*2,
                         justify=tk.LEFT, bg=BG)
        dummy.pack()
        self.update_idletasks()
        tw = dummy.winfo_reqwidth()
        th = dummy.winfo_reqheight()
        dummy.destroy()

        cw = tw + self.PAD_H*2
        ch = th + self.PAD_V*2

        row = tk.Frame(self, bg=BG)
        row.pack(fill=tk.X, pady=(4, 0))

        av_text = "Y" if is_user else "B"
        av_bg   = ACCENT if is_user else "#2d2d42"
        av = tk.Label(row, text=av_text, bg=av_bg, fg=TEXT_MAIN,
                      font=("Helvetica", 9, "bold"),
                      width=2, height=1, relief=tk.FLAT)

        cvs = tk.Canvas(row, width=cw, height=ch, bg=BG, highlightthickness=0)
        rounded_rect(cvs, 0, 0, cw, ch, r=16, fill=bg_color, outline="")
        cvs.create_text(self.PAD_H, self.PAD_V, text=text,
                        anchor=tk.NW, fill=fg_color,
                        font=("Helvetica", FONT_BODY),
                        width=self.MAX_W - self.PAD_H*2)

        if is_user:
            cvs.pack(side=tk.RIGHT, padx=(4, 6))
            av.pack(side=tk.RIGHT, padx=(0, 2), pady=6, anchor=tk.N)
        else:
            av.pack(side=tk.LEFT, padx=(6, 2), pady=6, anchor=tk.N)
            cvs.pack(side=tk.LEFT, padx=(4, 6))


# ─────────────────────────────────────────────────────────────────────────────
#  ANIMATED MIC BUTTON
# ─────────────────────────────────────────────────────────────────────────────
class MicButton(tk.Canvas):
    SIZE = 56

    def __init__(self, parent, on_click, **kwargs):
        super().__init__(parent, width=self.SIZE, height=self.SIZE,
                         bg=SIDEBAR_BG, highlightthickness=0, **kwargs)
        self._on_click = on_click
        self._active   = False
        self._pulse_r  = 0
        self._draw_idle()
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda _: self._on_hover(True))
        self.bind("<Leave>", lambda _: self._on_hover(False))

    def _draw_idle(self, hover=False):
        self.delete("all")
        r = self.SIZE // 2
        col = "#3a7aff" if hover else ACCENT
        self.create_oval(4, 4, self.SIZE-4, self.SIZE-4, fill=col, outline="", tags="btn")
        self.create_text(r, r, text="🎙", font=("", 20), fill="white", tags="btn")

    def _draw_active(self):
        self.delete("all")
        r = self.SIZE // 2
        pr = self._pulse_r
        if pr > 0:
            alpha_col = ACCENT_HOT
            self.create_oval(r-pr, r-pr, r+pr, r+pr,
                             fill="", outline=alpha_col, width=2, tags="pulse")
        self.create_oval(4, 4, self.SIZE-4, self.SIZE-4,
                         fill=ACCENT_HOT, outline="", tags="btn")
        self.create_text(r, r, text="🎙", font=("", 20), fill="white", tags="btn")

    def _animate_pulse(self):
        if not self._active:
            return
        self._pulse_r = (self._pulse_r + 2) % (self.SIZE // 2 + 4)
        self._draw_active()
        self.after(40, self._animate_pulse)

    def set_active(self, state: bool):
        self._active = state
        if state:
            self._pulse_r = 0
            self._animate_pulse()
        else:
            self._draw_idle()

    def _on_hover(self, entering):
        if not self._active:
            self._draw_idle(hover=entering)

    def _click(self, _):
        self._on_click()


# ─────────────────────────────────────────────────────────────────────────────
#  STATUS BAR
# ─────────────────────────────────────────────────────────────────────────────
class StatusBar(tk.Frame):
    STATES = {
        "idle":      ("●  Idle",        TEXT_DIM),
        "listening": ("●  Listening…",  ACCENT_GREEN),
        "thinking":  ("●  Thinking…",   ACCENT_AMBER),
        "speaking":  ("●  Speaking…",   ACCENT),
        "error":     ("●  Error",       ACCENT_HOT),
        "startup":   ("●  Starting…",   TEXT_DIM),
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=SIDEBAR_BG, height=28, **kwargs)
        self._lbl = tk.Label(self, text="", bg=SIDEBAR_BG,
                             font=("Helvetica", FONT_SMALL), fg=TEXT_DIM)
        self._lbl.pack(side=tk.LEFT, padx=12, pady=4)
        self.set("idle")

    def set(self, state: str):
        text, color = self.STATES.get(state, ("", TEXT_DIM))
        self._lbl.config(text=text, fg=color)


# ─────────────────────────────────────────────────────────────────────────────
#  SYSTEM CONTROLS PANEL  (slides in/out from the right)
# ─────────────────────────────────────────────────────────────────────────────
class SystemPanel(tk.Frame):
    """A collapsible panel showing categorised system control buttons."""

    PANEL_W = 240

    def __init__(self, parent, on_action, **kwargs):
        super().__init__(parent, bg=PANEL_BG, width=self.PANEL_W, **kwargs)
        self._on_action   = on_action          # callback(label, fn)
        self._visible     = False
        self._cur_cat     = list(SYSTEM_CONTROLS.keys())[0]
        self._cat_btns    = {}
        self._cards_frame = None
        self._build()

    # ── Build the panel layout ────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=PANEL_BG)
        hdr.pack(fill=tk.X, padx=10, pady=(12, 6))

        tk.Label(hdr, text="System Controls", bg=PANEL_BG, fg=TEXT_MAIN,
                 font=("Helvetica", 11, "bold")).pack(side=tk.LEFT)

        close_btn = tk.Label(hdr, text="✕", bg=PANEL_BG, fg=TEXT_DIM,
                             font=("Helvetica", 11), cursor="hand2")
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda _: self._on_action(None, None))

        # Thin accent line
        tk.Frame(self, bg=ACCENT, height=1).pack(fill=tk.X, padx=10)

        # Category pill tabs (scrollable row)
        tab_outer = tk.Frame(self, bg=PANEL_BG)
        tab_outer.pack(fill=tk.X, padx=6, pady=8)

        self._tab_canvas = tk.Canvas(tab_outer, bg=PANEL_BG,
                                     height=30, highlightthickness=0)
        self._tab_canvas.pack(fill=tk.X)

        self._tab_inner = tk.Frame(self._tab_canvas, bg=PANEL_BG)
        self._tab_canvas.create_window((0, 0), window=self._tab_inner, anchor=tk.NW)

        for cat in SYSTEM_CONTROLS:
            self._make_pill(cat)

        # Cards area (scrollable)
        cards_outer = tk.Frame(self, bg=PANEL_BG)
        cards_outer.pack(fill=tk.BOTH, expand=True, padx=6)

        self._scroll_canvas = tk.Canvas(cards_outer, bg=PANEL_BG,
                                        highlightthickness=0)
        vsb = tk.Scrollbar(cards_outer, orient=tk.VERTICAL,
                           command=self._scroll_canvas.yview)
        self._scroll_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._cards_frame = tk.Frame(self._scroll_canvas, bg=PANEL_BG)
        self._scroll_canvas.create_window((0, 0), window=self._cards_frame,
                                          anchor=tk.NW)
        self._cards_frame.bind(
            "<Configure>",
            lambda _: self._scroll_canvas.configure(
                scrollregion=self._scroll_canvas.bbox("all"))
        )
        self._scroll_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._scroll_canvas.yview_scroll(
                -1 * (e.delta // 120), "units")
        )

        self._show_category(self._cur_cat)

    def _make_pill(self, cat: str):
        lbl = tk.Label(self._tab_inner, text=cat,
                       bg=PILL_BG, fg=TEXT_DIM,
                       font=("Helvetica", FONT_SMALL),
                       padx=8, pady=3,
                       cursor="hand2", relief=tk.FLAT)
        lbl.pack(side=tk.LEFT, padx=(0, 4))
        lbl.bind("<Button-1>", lambda _, c=cat: self._show_category(c))
        lbl.bind("<Enter>",    lambda _, l=lbl: l.config(fg=TEXT_MAIN) if l != self._cat_btns.get(self._cur_cat) else None)
        lbl.bind("<Leave>",    lambda _, l=lbl: l.config(fg=TEXT_DIM)   if l != self._cat_btns.get(self._cur_cat) else None)
        self._cat_btns[cat] = lbl

    def _show_category(self, cat: str):
        # Reset old pill
        old = self._cat_btns.get(self._cur_cat)
        if old:
            old.config(bg=PILL_BG, fg=TEXT_DIM)

        self._cur_cat = cat

        # Highlight new pill
        new = self._cat_btns.get(cat)
        if new:
            new.config(bg=PILL_SEL, fg="white")

        # Clear cards
        for w in self._cards_frame.winfo_children():
            w.destroy()

        # Build 2-column grid of cards
        controls = SYSTEM_CONTROLS.get(cat, [])
        for idx, (label, icon, fn) in enumerate(controls):
            row_f  = idx // 2
            col_f  = idx  % 2
            self._make_card(self._cards_frame, label, icon, fn, row_f, col_f)

    def _make_card(self, parent, label, icon, fn, row, col):
        card = tk.Frame(parent, bg=CARD_BG, cursor="hand2",
                        relief=tk.FLAT, bd=0)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        tk.Label(card, text=icon, bg=CARD_BG, font=("", 18)).pack(pady=(10, 2))
        tk.Label(card, text=label, bg=CARD_BG, fg=TEXT_MAIN,
                 font=("Helvetica", FONT_CARD), wraplength=90,
                 justify=tk.CENTER).pack(pady=(0, 10))

        def _on_enter(_, c=card):
            c.config(bg=CARD_HOVER)
            for child in c.winfo_children():
                child.config(bg=CARD_HOVER)

        def _on_leave(_, c=card):
            c.config(bg=CARD_BG)
            for child in c.winfo_children():
                child.config(bg=CARD_BG)

        def _on_click(_event, lbl=label, f=fn):
            self._on_action(lbl, f)

        for widget in [card] + list(card.winfo_children()):
            widget.bind("<Enter>",   _on_enter)
            widget.bind("<Leave>",   _on_leave)
            widget.bind("<Button-1>", _on_click)

    # ── Visibility ────────────────────────────────────────────────────────────

    def show(self):
        self._visible = True
        self.pack(side=tk.RIGHT, fill=tk.Y)

    def hide(self):
        self._visible = False
        self.pack_forget()

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    @property
    def visible(self):
        return self._visible


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION WINDOW
# ─────────────────────────────────────────────────────────────────────────────
class BujjiApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Bujji  ·  AI Assistant")
        self.geometry("620x700")
        self.minsize(460, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._is_recording        = False
        self._shutdown_event      = threading.Event()
        self._wake_listener_thread = None
        self._wake_enabled        = tk.BooleanVar(value=True)
        self._lang                = tk.StringVar(value="te")
        self._speech_visible      = False
        self._electron_process    = None
        self._api_process         = None

        # Start API server first
        self._start_api_server()
        
        # Automatically start the Electron desktop pet
        self._start_robot_pet()

        self._build_ui()
        self._startup()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ───────────────────────────────────────────────────────────
        top = tk.Frame(self, bg=SIDEBAR_BG, height=52)
        top.pack(fill=tk.X)
        top.pack_propagate(False)

        # Logo + title
        logo_frame = tk.Frame(top, bg=SIDEBAR_BG)
        logo_frame.pack(side=tk.LEFT, padx=14, pady=10)

        logo_dot = tk.Canvas(logo_frame, width=10, height=10,
                             bg=SIDEBAR_BG, highlightthickness=0)
        logo_dot.create_oval(0, 0, 10, 10, fill=ACCENT, outline="")
        logo_dot.pack(side=tk.LEFT, padx=(0, 6), pady=2)

        tk.Label(logo_frame, text="Bujji", bg=SIDEBAR_BG, fg=TEXT_MAIN,
                 font=("Helvetica", FONT_TITLE, "bold")).pack(side=tk.LEFT)

        tk.Label(logo_frame, text="AI Assistant", bg=SIDEBAR_BG, fg=TEXT_DIM,
                 font=("Helvetica", FONT_SMALL)).pack(side=tk.LEFT, padx=(6, 0), pady=1)

        # Right-side controls
        right = tk.Frame(top, bg=SIDEBAR_BG)
        right.pack(side=tk.RIGHT, padx=12, pady=10)

        self._lang_btn = tk.Label(
            right, text="Lang: TE", bg=CARD_BG, fg=TEXT_MAIN,
            font=("Helvetica", FONT_SMALL, "bold"),
            padx=10, pady=5, cursor="hand2", relief=tk.FLAT)
        self._lang_btn.pack(side=tk.RIGHT, padx=(6, 0))
        self._lang_btn.bind("<Button-1>", lambda _: self._toggle_language())
        self._lang_btn.bind("<Enter>",    lambda _: self._lang_btn.config(bg=ACCENT))
        self._lang_btn.bind("<Leave>",    lambda _: self._lang_btn.config(bg=CARD_BG))

        # System Controls toggle button
        self._ctrl_btn = tk.Label(
            right, text="⚙  Controls", bg=CARD_BG, fg=TEXT_MAIN,
            font=("Helvetica", FONT_SMALL, "bold"),
            padx=10, pady=5, cursor="hand2", relief=tk.FLAT)
        self._ctrl_btn.pack(side=tk.RIGHT, padx=(6, 0))
        self._ctrl_btn.bind("<Button-1>", lambda _: self._toggle_panel())
        self._ctrl_btn.bind("<Enter>",    lambda _: self._ctrl_btn.config(bg=ACCENT))
        self._ctrl_btn.bind("<Leave>",    lambda _: self._ctrl_btn.config(bg=CARD_BG if not self._panel.visible else ACCENT))

        wake_toggle = tk.Checkbutton(
            right, text="Wake", variable=self._wake_enabled,
            command=self._on_wake_toggle,
            bg=SIDEBAR_BG, fg=TEXT_DIM,
            activebackground=SIDEBAR_BG, activeforeground=TEXT_MAIN,
            selectcolor=SIDEBAR_BG, font=("Helvetica", FONT_SMALL),
        )
        wake_toggle.pack(side=tk.RIGHT, padx=(0, 6))

        reset_btn = tk.Label(right, text="↺", bg=SIDEBAR_BG, fg=TEXT_DIM,
                             font=("Helvetica", 13), cursor="hand2")
        reset_btn.pack(side=tk.RIGHT, padx=(0, 6))
        reset_btn.bind("<Button-1>", lambda _: self._reset_chat())
        reset_btn.bind("<Enter>",    lambda _: reset_btn.config(fg=TEXT_MAIN))
        reset_btn.bind("<Leave>",    lambda _: reset_btn.config(fg=TEXT_DIM))

        # ── Divider ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=DIVIDER, height=1).pack(fill=tk.X)

        # ── Main body (chat + optional panel) ─────────────────────────────────
        self._body = tk.Frame(self, bg=BG)
        self._body.pack(fill=tk.BOTH, expand=True)

        # System panel (hidden initially, packed into _body)
        self._panel = SystemPanel(self._body, on_action=self._panel_action)
        # Don't pack yet — shown on toggle

        # Chat column
        self._chat_col = tk.Frame(self._body, bg=BG)
        self._chat_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── Scrollable chat area ──────────────────────────────────────────────
        chat_outer = tk.Frame(self._chat_col, bg=BG)
        chat_outer.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(chat_outer, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_outer, orient=tk.VERTICAL,
                                 command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._chat_frame = tk.Frame(self._canvas, bg=BG)
        self._chat_window = self._canvas.create_window(
            (0, 0), window=self._chat_frame, anchor=tk.NW)

        self._chat_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units")
        )

        # ── Bottom bar ────────────────────────────────────────────────────────
        tk.Frame(self._chat_col, bg=DIVIDER, height=1).pack(fill=tk.X)

        bottom = tk.Frame(self._chat_col, bg=SIDEBAR_BG)
        bottom.pack(fill=tk.X)

        # Input row
        input_wrap = tk.Frame(bottom, bg="#1a1a26", relief=tk.FLAT)
        input_wrap.pack(fill=tk.X, padx=12, pady=(10, 6))

        self._text_var = tk.StringVar()
        self._entry = tk.Entry(
            input_wrap, textvariable=self._text_var,
            bg="#1a1a26", fg=TEXT_MAIN,
            insertbackground=ACCENT,
            relief=tk.FLAT,
            font=("Helvetica", FONT_BODY),
            bd=0, highlightthickness=0
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=9, ipadx=12)
        self._entry.bind("<Return>", lambda _: self._send_text())

        send_btn = tk.Label(input_wrap, text="↑", bg=ACCENT, fg="white",
                            font=("Helvetica", 13, "bold"),
                            cursor="hand2", width=3, pady=5)
        send_btn.pack(side=tk.RIGHT)
        send_btn.bind("<Button-1>", lambda _: self._send_text())
        send_btn.bind("<Enter>",    lambda _: send_btn.config(bg="#3a7aff"))
        send_btn.bind("<Leave>",    lambda _: send_btn.config(bg=ACCENT))

        # Mic row
        mic_row = tk.Frame(bottom, bg=SIDEBAR_BG)
        mic_row.pack(pady=(0, 8))

        self._mic_btn = MicButton(mic_row, on_click=self._toggle_mic)
        self._mic_btn.pack(side=tk.LEFT, padx=(0, 10))

        self._mic_label = tk.Label(
            mic_row, bg=SIDEBAR_BG, fg=TEXT_DIM,
            font=("Helvetica", FONT_SMALL), text="Tap to speak")
        self._mic_label.pack(side=tk.LEFT)

        # Speech output strip (visible while TTS plays)
        self._speech_frame = tk.Frame(self._chat_col, bg=SIDEBAR_BG)
        self._speech_label = tk.Label(
            self._speech_frame,
            text="",
            bg=SIDEBAR_BG,
            fg=TEXT_DIM,
            font=("Helvetica", FONT_SMALL),
            wraplength=560,
            justify=tk.LEFT,
        )
        self._speech_label.pack(fill=tk.X, padx=12, pady=6)

        # Status bar
        tk.Frame(self._chat_col, bg=DIVIDER, height=1).pack(fill=tk.X)
        self._status = StatusBar(self._chat_col)
        self._status.pack(fill=tk.X)

    # ── Start API server ──────────────────────────────────────────────────────

    def _start_api_server(self):
        """Start the FastAPI server in a background process."""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Start API server with uvicorn
            self._api_process = subprocess.Popen(
                ["python", "-m", "uvicorn", "api_server:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"✅ API server started (PID: {self._api_process.pid})")
            
            # Give API time to start
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️  Failed to start API server: {e}")

    # ── Start robot pet ───────────────────────────────────────────────────────

    def _start_robot_pet(self):
        """Start the Electron robot pet in a background process."""
        try:
            # Find robot-pet directory relative to this script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            robot_pet_dir = os.path.join(os.path.dirname(base_dir), "robot-pet")
            
            if not os.path.exists(robot_pet_dir):
                print(f"⚠️  Robot pet directory not found at {robot_pet_dir}")
                return
            
            # Start the Electron app
            self._electron_process = subprocess.Popen(
                ["npm", "start"],
                cwd=robot_pet_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"✅ Robot pet started (PID: {self._electron_process.pid})")
            
            # Optional: log any startup errors in a background thread
            def log_output():
                if self._electron_process.stderr:
                    for line in self._electron_process.stderr:
                        print(f"🤖 Robot: {line.strip()}")
            
            threading.Thread(target=log_output, daemon=True).start()
            
        except Exception as e:
            print(f"⚠️  Failed to start robot pet: {e}")

    # ── System Panel toggle ───────────────────────────────────────────────────

    def _toggle_panel(self):
        self._panel.toggle()
        if self._panel.visible:
            self._ctrl_btn.config(bg=ACCENT)
        else:
            self._ctrl_btn.config(bg=CARD_BG)

    def _panel_action(self, label, fn):
        """Called when a card is clicked or panel close (label=None)."""
        if label is None:
            # Close button
            self._panel.hide()
            self._ctrl_btn.config(bg=CARD_BG)
            return
        self._add_bubble(f"Running: {label}", "user")
        threading.Thread(target=self._run_control, args=(label, fn), daemon=True).start()

    def _run_control(self, label: str, fn):
        self._set_status("thinking")
        try:
            result = fn()
            msg = f"✅  {label}" + (f": {result}" if result else "")
            self._add_bubble(msg, "bot")
        except Exception as e:
            self._add_bubble(f"⚠️  {label} failed: {e}", "bot")
        self._set_status("idle")

    # ── Canvas helpers ────────────────────────────────────────────────────────

    def _on_frame_configure(self, _event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._chat_window, width=event.width)

    # ── Add bubble ────────────────────────────────────────────────────────────

    def _add_bubble(self, text: str, sender: str):
        self.after(0, self._add_bubble_main, text, sender)

    def _add_bubble_main(self, text: str, sender: str):
        bubble = BubbleFrame(self._chat_frame, text=text, sender=sender)
        bubble.pack(fill=tk.X, pady=2, padx=8)
        self.update_idletasks()
        self._canvas.yview_moveto(1.0)

    def _set_status(self, state: str):
        self.after(0, self._status.set, state)

    def _set_mic_label(self, text: str):
        self.after(0, self._mic_label.config, {"text": text})

    def _set_mic_active(self, state: bool):
        self.after(0, self._mic_btn.set_active, state)

    def _show_speech_text(self, text: str):
        def _do():
            self._speech_label.config(text=text)
            if not self._speech_visible:
                self._speech_frame.pack(fill=tk.X)
                self._speech_visible = True
        self.after(0, _do)

    def _hide_speech_text(self):
        def _do():
            self._speech_label.config(text="")
            if self._speech_visible:
                self._speech_frame.pack_forget()
                self._speech_visible = False
        self.after(0, _do)

    # ── Startup ───────────────────────────────────────────────────────────────

    def _startup(self):
        self._set_status("startup")
        self._add_bubble("Bujji is starting up… checking Ollama and system tools.", "bot")

        def _do():
            try:
                # Prefer the REST API health check when running GUI
                try:
                    resp = requests.get(f"{API_URL}/health", timeout=5)
                    if resp.ok:
                        data = resp.json()
                        if not data.get("ollama", False):
                            self._add_bubble("⚠️  Ollama not available via API.", "bot")
                    else:
                        self._add_bubble("⚠️  API health check failed.", "bot")
                except Exception as e:
                    self._add_bubble(f"⚠️  API health check failed: {e}", "bot")
                check_system_tools()
                self._speak("Bujji GUI is ready. Tap the mic button or type a message.")
                self._add_bubble(
                    f"✅  All systems ready!\n\nTap 🎙 to speak, or type below.\n"
                    f"Open ⚙ Controls to run system actions.\n"
                    f"Wake word: \"{WAKE_WORD}\"",
                    "bot"
                )
                self._set_status("idle")
                if self._wake_listener_thread is None:
                    self._wake_listener_thread = threading.Thread(
                        target=self._wake_listener_loop, daemon=True)
                    self._wake_listener_thread.start()
            except Exception as e:
                self._add_bubble(f"⚠️  Startup warning: {e}", "bot")
                self._set_status("error")

        threading.Thread(target=_do, daemon=True).start()

    # ── Text input ────────────────────────────────────────────────────────────

    def _send_text(self):
        text = self._text_var.get().strip()
        if not text:
            return
        self._text_var.set("")
        self._add_bubble(text, "user")
        threading.Thread(target=self._process_command, args=(text,), daemon=True).start()

    # ── Mic button ────────────────────────────────────────────────────────────

    def _toggle_mic(self, speak_confirm: bool = False):
        if self._is_recording:
            return
        self._is_recording = True
        self._set_mic_active(True)
        self._set_mic_label("Listening…")
        self._set_status("listening")
        threading.Thread(target=self._do_voice_capture, args=(speak_confirm,), daemon=True).start()

    def _do_voice_capture(self, speak_confirm: bool):
        if speak_confirm:
            self._speak(WAKE_CONFIRMATION)
        user_text = listen_once(max_seconds=COMMAND_RECORD_SECONDS)
        self._set_mic_active(False)
        self._set_mic_label("Tap to speak")
        self._is_recording = False

        if not user_text or len(user_text.strip()) < 2:
            self._add_bubble("I didn't catch that — please try again.", "bot")
            self._set_status("idle")
            return

        self._add_bubble(user_text, "user")
        self._process_command(user_text)

    def _wake_listener_loop(self):
        while not self._shutdown_event.is_set():
            if not self._wake_enabled.get():
                time.sleep(0.5)
                continue
            if self._is_recording:
                time.sleep(0.2)
                continue
            heard = listen_for_wake_word_once(timeout=5)
            if heard and not self._shutdown_event.is_set():
                self.after(0, self._on_wake_word)

    def _on_wake_word(self):
        if self._is_recording or not self._wake_enabled.get():
            return
        self._add_bubble(f"Wake word detected: \"{WAKE_WORD}\"", "bot")
        import urllib.request
        try:
            urllib.request.urlopen("http://127.0.0.1:8766/state?mode=awake", timeout=0.2)
        except Exception:
            pass
        self._toggle_mic(speak_confirm=True)

    def _on_wake_toggle(self):
        state = "enabled" if self._wake_enabled.get() else "disabled"
        self._add_bubble(f"Wake word {state}.", "bot")

    # ── Core pipeline ─────────────────────────────────────────────────────────

    def _process_command(self, user_text: str):
        self._set_status("thinking")
        try:
            # Use REST API /chat instead of local function call
            try:
                resp = requests.post(f"{API_URL}/chat", json={"message": user_text, "remember": True}, timeout=60)
                if resp.ok:
                    llm_response = resp.json().get("reply", "")
                else:
                    llm_response = f"I can't reach the API (status {resp.status_code})."
            except Exception as e:
                llm_response = f"I can't reach the API: {e}"
            if not llm_response.strip().startswith("SYSTEM_ACTION:"):
                lang = detect_language(llm_response)
                if self._lang.get() == "en" and lang == "telugu":
                    llm_response = translate_to_english(llm_response)
                elif self._lang.get() == "te" and lang == "english":
                    llm_response = translate_to_telugu(llm_response)

                # Notify the robot pet to stop moving and show this reply in its bubble.
                try:
                    self._notify_robot(llm_response)
                except Exception:
                    pass
            kind, result = route(llm_response, speak_fn=self._speak, silent=False)
            reply = f"✅  Done: {result}" if kind == "system" else llm_response
            self._add_bubble(reply, "bot")
            self._set_status("idle")
        except Exception as e:
            self._add_bubble(f"⚠️  Error: {e}", "bot")
            self._set_status("error")

    # ── Reset ─────────────────────────────────────────────────────────────────

    def _reset_chat(self):
        # Clear server-side history (if API available) and clear GUI chat
        try:
            try:
                requests.post(f"{API_URL}/reset", timeout=5)
            except Exception:
                pass
        finally:
            for w in self._chat_frame.winfo_children():
                w.destroy()
            self._add_bubble("Conversation reset. How can I help?", "bot")

    # ── Close ─────────────────────────────────────────────────────────────────

    def _on_close(self):
        """Clean shutdown: notify robot, stop processes, and close GUI."""
        self._shutdown_event.set()
        
        # Tell robot pet to go to sleep
        import urllib.request
        try:
            urllib.request.urlopen("http://127.0.0.1:8766/state?mode=sleeping", timeout=0.2)
        except Exception:
            pass
        
        # Terminate robot pet process
        if self._electron_process:
            try:
                print("Stopping robot pet...")
                self._electron_process.terminate()
                try:
                    self._electron_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print("Force killing robot pet...")
                    self._electron_process.kill()
            except Exception as e:
                print(f"Error stopping robot pet: {e}")
        
        # Terminate API server
        if self._api_process:
            try:
                print("Stopping API server...")
                self._api_process.terminate()
                try:
                    self._api_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print("Force killing API server...")
                    self._api_process.kill()
            except Exception as e:
                print(f"Error stopping API server: {e}")
        
        # Say goodbye
        self._speak("Goodbye!")
        self.destroy()

    # ── Language toggle ─────────────────────────────────────────────────────

    def _toggle_language(self):
        new_lang = "en" if self._lang.get() == "te" else "te"
        self._lang.set(new_lang)
        self._lang_btn.config(text=f"Lang: {new_lang.upper()}")
        label = "English" if new_lang == "en" else "Telugu"
        self._add_bubble(f"Language set to {label}.", "bot")
        self._speak(f"Language set to {label}.")

    def _speak(self, text: str, block: bool = True):
        def _do():
            self._show_speech_text(text)
            try:
                speak(text, block=True, lang=self._lang.get())
            finally:
                self._hide_speech_text()

        if block:
            _do()
        else:
            threading.Thread(target=_do, daemon=True).start()

    def _notify_robot(self, text: str, duration: float | None = None) -> None:
        """Notify the Electron robot pet to stop moving and show a bubble.

        This makes two best-effort HTTP calls to the local robot event server:
        - /state?mode=awake to transition the robot to the awake/idle state
        - /speech?text=... to show the speech/process bubble with the text
        Failures are ignored so the GUI keeps working if the robot isn't running.
        """
        try:
            import urllib.request, urllib.parse

            # Wake the robot (puts it into Idle/awake state and pauses walking briefly)
            try:
                urllib.request.urlopen("http://127.0.0.1:8766/state?mode=awake", timeout=0.2)
            except Exception:
                pass

            # Send the speech text so the robot shows the bubble
            try:
                encoded = urllib.parse.quote(text)
                url = f"http://127.0.0.1:8766/speech?text={encoded}"
                if duration is not None:
                    url += f"&duration={float(duration):.2f}"
                urllib.request.urlopen(url, timeout=0.5)
            except Exception:
                pass
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = BujjiApp()
    app.mainloop()
