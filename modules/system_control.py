# modules/system_control.py
# ─── System Control Module ────────────────────────────────────────────────────
# Controls macOS system: volume, brightness, Wi-Fi, Bluetooth, Dark Mode,
# Do Not Disturb, sleep, apps, browser, screenshots, etc.
# All functions use osascript / shell commands — no third-party libs required.
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import subprocess
import webbrowser
import datetime
import urllib.parse
from typing import Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VOLUME_STEP, BRIGHTNESS_STEP, SCREENSHOT_DIR


# ══════════════════════════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _run_osascript(script: str) -> str:
    """Run an AppleScript snippet and return its stdout."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def _run_shell(cmd: str) -> Tuple[int, str, str]:
    """Run a shell command; returns (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _command_exists(name: str) -> bool:
    rc, _, _ = _run_shell(f"command -v {name} >/dev/null 2>&1")
    return rc == 0


def check_system_tools() -> None:
    missing = []
    if not _command_exists("brightness"):
        missing.append("brightness (brew install brightness)")
    if not _command_exists("blueutil"):
        missing.append("blueutil (brew install blueutil)")

    if missing:
        print("  [SystemControl] ⚠️  Missing tools for full control:")
        for item in missing:
            print(f"    - {item}")
        print("  [SystemControl] ℹ️  Brightness/Bluetooth commands may be limited.")
    else:
        print("  [SystemControl] ✅ System tools OK (brightness, blueutil).")


def _get_current_volume() -> int:
    out = _run_osascript("output volume of (get volume settings)")
    try:
        return int(out)
    except ValueError:
        return 50


def _set_volume_raw(level: int) -> None:
    level = max(0, min(100, level))
    _run_osascript(f"set volume output volume {level}")


# ══════════════════════════════════════════════════════════════════════════════
#  VOLUME CONTROLS
# ══════════════════════════════════════════════════════════════════════════════

def volume_up(step: int = VOLUME_STEP) -> str:
    current = _get_current_volume()
    new_vol = min(100, current + step)
    _set_volume_raw(new_vol)
    msg = f"Volume increased to {new_vol}%."
    print(f"  [SystemControl] 🔊 {msg}")
    return msg


def volume_down(step: int = VOLUME_STEP) -> str:
    current = _get_current_volume()
    new_vol = max(0, current - step)
    _set_volume_raw(new_vol)
    msg = f"Volume decreased to {new_vol}%."
    print(f"  [SystemControl] 🔉 {msg}")
    return msg


def set_volume(level: int) -> str:
    level = max(0, min(100, int(level)))
    _set_volume_raw(level)
    msg = f"Volume set to {level}%."
    print(f"  [SystemControl] 🔊 {msg}")
    return msg


def mute() -> str:
    _run_osascript("set volume with output muted")
    msg = "System audio muted."
    print(f"  [SystemControl] 🔇 {msg}")
    return msg


def unmute() -> str:
    _run_osascript("set volume without output muted")
    msg = "System audio unmuted."
    print(f"  [SystemControl] 🔊 {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  BRIGHTNESS CONTROLS
# ══════════════════════════════════════════════════════════════════════════════

def _get_current_brightness() -> int:
    if not _command_exists("brightness"):
        return 50
    rc, out, _ = _run_shell("brightness -l 2>/dev/null | grep -oE '[0-9]+\\.[0-9]+'")
    if rc == 0 and out:
        try:
            return int(float(out.split()[0]) * 100)
        except (ValueError, IndexError):
            pass
    return 50


def _set_brightness_raw(level_pct: int) -> bool:
    level_pct = max(1, min(100, level_pct))  # macOS won't go fully dark
    level_float = round(level_pct / 100, 2)
    if not _command_exists("brightness"):
        return False
    rc, _, _ = _run_shell(f"brightness {level_float} 2>/dev/null")
    if rc == 0:
        return True
    return False


def brightness_up(step: int = BRIGHTNESS_STEP) -> str:
    current = _get_current_brightness()
    new_level = min(100, current + step)
    ok = _set_brightness_raw(new_level)
    if not ok:
        msg = "Brightness control needs: brew install brightness"
        print(f"  [SystemControl] ❌ {msg}")
        return msg
    msg = f"Brightness increased to {new_level}%."
    print(f"  [SystemControl] ☀️  {msg}")
    return msg


def brightness_down(step: int = BRIGHTNESS_STEP) -> str:
    current = _get_current_brightness()
    new_level = max(10, current - step)
    ok = _set_brightness_raw(new_level)
    if not ok:
        msg = "Brightness control needs: brew install brightness"
        print(f"  [SystemControl] ❌ {msg}")
        return msg
    msg = f"Brightness decreased to {new_level}%."
    print(f"  [SystemControl] 🌑 {msg}")
    return msg


def set_brightness(level: int) -> str:
    level = max(10, min(100, int(level)))
    ok = _set_brightness_raw(level)
    if not ok:
        msg = "Brightness control needs: brew install brightness"
        print(f"  [SystemControl] ❌ {msg}")
        return msg
    msg = f"Brightness set to {level}%."
    print(f"  [SystemControl] ☀️  {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  DARK MODE
# ══════════════════════════════════════════════════════════════════════════════

def enable_dark_mode() -> str:
    _run_osascript(
        'tell application "System Events" to tell appearance preferences to set dark mode to true'
    )
    msg = "Dark mode enabled."
    print(f"  [SystemControl] 🌙 {msg}")
    return msg


def disable_dark_mode() -> str:
    _run_osascript(
        'tell application "System Events" to tell appearance preferences to set dark mode to false'
    )
    msg = "Light mode enabled."
    print(f"  [SystemControl] ☀️  {msg}")
    return msg


def toggle_dark_mode() -> str:
    current = _run_osascript(
        'tell application "System Events" to tell appearance preferences to return dark mode'
    )
    if current.strip().lower() == "true":
        return disable_dark_mode()
    return enable_dark_mode()


# ══════════════════════════════════════════════════════════════════════════════
#  DO NOT DISTURB  (macOS 12+ uses Focus)
# ══════════════════════════════════════════════════════════════════════════════

def enable_do_not_disturb() -> str:
    # macOS 12+ shortcut: Control+Option+Cmd+F1 is not standard; use shortcuts db
    # Most reliable cross-version method via shortcuts or defaults write
    rc, _, _ = _run_shell(
        "shortcuts run 'Turn On Do Not Disturb' 2>/dev/null || "
        "osascript -e 'tell application \"System Events\" to keystroke \"d\" "
        "using {command down, option down}'"
    )
    msg = "Do Not Disturb enabled."
    print(f"  [SystemControl] 🔕 {msg}")
    return msg


def disable_do_not_disturb() -> str:
    rc, _, _ = _run_shell(
        "shortcuts run 'Turn Off Do Not Disturb' 2>/dev/null || "
        "osascript -e 'tell application \"System Events\" to keystroke \"d\" "
        "using {command down, option down}'"
    )
    msg = "Do Not Disturb disabled."
    print(f"  [SystemControl] 🔔 {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  WI-FI
# ══════════════════════════════════════════════════════════════════════════════

def wifi_on() -> str:
    rc, _, err = _run_shell("networksetup -setairportpower en0 on")
    if rc != 0:
        # Try en1 as fallback
        _run_shell("networksetup -setairportpower en1 on")
    msg = "Wi-Fi turned on."
    print(f"  [SystemControl] 📶 {msg}")
    return msg


def wifi_off() -> str:
    rc, _, err = _run_shell("networksetup -setairportpower en0 off")
    if rc != 0:
        _run_shell("networksetup -setairportpower en1 off")
    msg = "Wi-Fi turned off."
    print(f"  [SystemControl] 📵 {msg}")
    return msg


def wifi_status() -> str:
    _, out, _ = _run_shell("networksetup -getairportpower en0")
    msg = f"Wi-Fi status: {out}"
    print(f"  [SystemControl] 📶 {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  BLUETOOTH
# ══════════════════════════════════════════════════════════════════════════════

def bluetooth_on() -> str:
    # blueutil is the most reliable (brew install blueutil)
    if not _command_exists("blueutil"):
        _run_shell("open 'x-apple.systempreferences:com.apple.Bluetooth'")
        msg = "Bluetooth: install blueutil for direct control: brew install blueutil"
        print(f"  [SystemControl] 🔵 {msg}")
        return msg
    rc, _, _ = _run_shell("blueutil -p 1 2>/dev/null")
    if rc != 0:
        _run_shell("open 'x-apple.systempreferences:com.apple.Bluetooth'")
        msg = "Bluetooth: opened settings (install blueutil for direct control: brew install blueutil)"
        print(f"  [SystemControl] 🔵 {msg}")
        return msg
    msg = "Bluetooth turned on."
    print(f"  [SystemControl] 🔵 {msg}")
    return msg


def bluetooth_off() -> str:
    if not _command_exists("blueutil"):
        msg = "Bluetooth: install blueutil for direct control: brew install blueutil"
        print(f"  [SystemControl] ❌ {msg}")
        return msg
    rc, _, _ = _run_shell("blueutil -p 0 2>/dev/null")
    if rc != 0:
        msg = "Bluetooth: install blueutil for direct control: brew install blueutil"
        print(f"  [SystemControl] ❌ {msg}")
        return msg
    msg = "Bluetooth turned off."
    print(f"  [SystemControl] 📵 {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  POWER / SLEEP
# ══════════════════════════════════════════════════════════════════════════════

def sleep_system() -> str:
    msg = "Putting the system to sleep."
    print(f"  [SystemControl] 💤 {msg}")
    _run_osascript('tell application "System Events" to sleep')
    return msg


def sleep_display() -> str:
    _run_shell("pmset displaysleepnow")
    msg = "Display is now sleeping."
    print(f"  [SystemControl] 🖥️  {msg}")
    return msg


def restart_system() -> str:
    msg = "Restarting the system."
    print(f"  [SystemControl] 🔄 {msg}")
    _run_osascript('tell application "System Events" to restart')
    return msg


def shutdown_system() -> str:
    msg = "Shutting down the system."
    print(f"  [SystemControl] ⏻ {msg}")
    _run_osascript('tell application "System Events" to shut down')
    return msg


def empty_trash() -> str:
    _run_osascript('tell application "Finder" to empty trash')
    msg = "Trash emptied."
    print(f"  [SystemControl] 🗑️  {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  WEB & SEARCH
# ══════════════════════════════════════════════════════════════════════════════

def open_website(url_or_name: str) -> str:
    name = url_or_name.strip().lower()
    shortcuts = {
        "youtube":   "https://www.youtube.com",
        "google":    "https://www.google.com",
        "github":    "https://www.github.com",
        "gmail":     "https://mail.google.com",
        "maps":      "https://maps.google.com",
        "reddit":    "https://www.reddit.com",
        "twitter":   "https://www.twitter.com",
        "x":         "https://www.x.com",
        "netflix":   "https://www.netflix.com",
        "spotify":   "https://open.spotify.com",
        "wikipedia": "https://www.wikipedia.org",
        "amazon":    "https://www.amazon.com",
        "linkedin":  "https://www.linkedin.com",
    }
    url = shortcuts.get(name, None)
    if url is None:
        url = url_or_name if "." in url_or_name else f"https://www.{url_or_name}.com"
    webbrowser.open(url)
    msg = f"Opening {url_or_name} in your browser."
    print(f"  [SystemControl] 🌐 {msg}")
    return msg


def search_google(query: str) -> str:
    encoded = urllib.parse.quote_plus(query.strip())
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    msg = f"Searching Google for: {query}"
    print(f"  [SystemControl] 🔍 {msg}")
    return msg


def search_youtube(query: str) -> str:
    encoded = urllib.parse.quote_plus(query.strip())
    url = f"https://www.youtube.com/results?search_query={encoded}"
    webbrowser.open(url)
    msg = f"Searching YouTube for: {query}"
    print(f"  [SystemControl] 📺 {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  APP & FOLDER CONTROL
# ══════════════════════════════════════════════════════════════════════════════

def open_app(app_name: str) -> str:
    rc, _, err = _run_shell(f'open -a "{app_name}"')
    if rc == 0:
        msg = f"Opening {app_name}."
        print(f"  [SystemControl] 🖥️  {msg}")
        return msg
    else:
        msg = f"Could not open {app_name}. Make sure the app is installed."
        print(f"  [SystemControl] ❌ {msg} ({err})")
        return msg


def quit_app(app_name: str) -> str:
    result = _run_osascript(f'tell application "{app_name}" to quit')
    msg = f"Quit {app_name}."
    print(f"  [SystemControl] ✖️  {msg}")
    return msg


def open_folder(folder_name: str) -> str:
    folder_map = {
        "downloads":    os.path.expanduser("~/Downloads"),
        "desktop":      os.path.expanduser("~/Desktop"),
        "documents":    os.path.expanduser("~/Documents"),
        "pictures":     os.path.expanduser("~/Pictures"),
        "music":        os.path.expanduser("~/Music"),
        "movies":       os.path.expanduser("~/Movies"),
        "home":         os.path.expanduser("~"),
        "applications": "/Applications",
    }
    path = folder_map.get(folder_name.strip().lower(), os.path.expanduser("~/Desktop"))
    _run_shell(f'open "{path}"')
    msg = f"Opening {folder_name} folder."
    print(f"  [SystemControl] 📁 {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  SCREENSHOT
# ══════════════════════════════════════════════════════════════════════════════

def take_screenshot() -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_dir = os.path.expanduser(SCREENSHOT_DIR)
    filepath = os.path.join(save_dir, f"Bujji_screenshot_{ts}.png")
    rc, _, err = _run_shell(f'screencapture -x "{filepath}"')
    if rc == 0:
        msg = f"Screenshot saved to Desktop as Bujji_screenshot_{ts}.png"
        print(f"  [SystemControl] 📸 {msg}")
        return msg
    else:
        msg = "Could not take a screenshot."
        print(f"  [SystemControl] ❌ {msg} ({err})")
        return msg


# ══════════════════════════════════════════════════════════════════════════════
#  TIME & BATTERY
# ══════════════════════════════════════════════════════════════════════════════

def get_time() -> str:
    now = datetime.datetime.now()
    msg = f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."
    print(f"  [SystemControl] 🕐 {msg}")
    return msg


def get_battery() -> str:
    rc, out, _ = _run_shell("pmset -g batt | grep -oE '[0-9]+%'")
    if rc == 0 and out:
        charging_rc, charging_out, _ = _run_shell("pmset -g batt | grep -i charging")
        status = "charging" if "charging" in charging_out.lower() else "not charging"
        msg = f"Battery is at {out.strip()} and {status}."
    else:
        msg = "Could not read battery status."
    print(f"  [SystemControl] 🔋 {msg}")
    return msg


def lock_screen() -> str:
    _run_osascript(
        'tell application "System Events" to keystroke "q" using {command down, control down}'
    )
    msg = "Screen locked."
    print(f"  [SystemControl] 🔒 {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  CLIPBOARD
# ══════════════════════════════════════════════════════════════════════════════

def get_clipboard() -> str:
    rc, out, _ = _run_shell("pbpaste")
    if out:
        msg = f"Clipboard contains: {out[:200]}"
    else:
        msg = "Clipboard is empty."
    print(f"  [SystemControl] 📋 {msg}")
    return msg


def set_clipboard(text: str) -> str:
    subprocess.run("pbcopy", input=text.encode(), check=True)
    msg = f"Copied to clipboard: {text[:60]}"
    print(f"  [SystemControl] 📋 {msg}")
    return msg


# ══════════════════════════════════════════════════════════════════════════════
#  DISPATCHER — called by intent_router.py
# ══════════════════════════════════════════════════════════════════════════════

def dispatch(action: str, argument: str = "") -> str:
    action = action.strip().upper()
    argument = argument.strip()

    def _safe_int(val, default=50):
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    handlers = {
        # Volume
        "VOLUME_UP":          lambda a: volume_up(),
        "VOLUME_DOWN":        lambda a: volume_down(),
        "VOLUME_SET":         lambda a: set_volume(_safe_int(a)),
        "MUTE":               lambda a: mute(),
        "UNMUTE":             lambda a: unmute(),
        # Brightness
        "BRIGHTNESS_UP":      lambda a: brightness_up(),
        "BRIGHTNESS_DOWN":    lambda a: brightness_down(),
        "BRIGHTNESS_SET":     lambda a: set_brightness(_safe_int(a)),
        # Dark Mode
        "DARK_MODE_ON":       lambda a: enable_dark_mode(),
        "DARK_MODE_OFF":      lambda a: disable_dark_mode(),
        "DARK_MODE_TOGGLE":   lambda a: toggle_dark_mode(),
        # Wi-Fi
        "WIFI_ON":            lambda a: wifi_on(),
        "WIFI_OFF":           lambda a: wifi_off(),
        "WIFI_STATUS":        lambda a: wifi_status(),
        # Bluetooth
        "BLUETOOTH_ON":       lambda a: bluetooth_on(),
        "BLUETOOTH_OFF":      lambda a: bluetooth_off(),
        # Do Not Disturb
        "DND_ON":             lambda a: enable_do_not_disturb(),
        "DND_OFF":            lambda a: disable_do_not_disturb(),
        # Power
        "SLEEP":              lambda a: sleep_system(),
        "SLEEP_DISPLAY":      lambda a: sleep_display(),
        "RESTART":            lambda a: restart_system(),
        "SHUTDOWN":           lambda a: shutdown_system(),
        # Apps & Files
        "OPEN_APP":           lambda a: open_app(a),
        "QUIT_APP":           lambda a: quit_app(a),
        "OPEN_FOLDER":        lambda a: open_folder(a),
        "EMPTY_TRASH":        lambda a: empty_trash(),
        # Web
        "OPEN_WEB":           lambda a: open_website(a),
        "SEARCH":             lambda a: search_google(a),
        "SEARCH_YOUTUBE":     lambda a: search_youtube(a),
        # Utilities
        "SCREENSHOT":         lambda a: take_screenshot(),
        "TIME":               lambda a: get_time(),
        "BATTERY":            lambda a: get_battery(),
        "LOCK":               lambda a: lock_screen(),
        "CLIPBOARD_GET":      lambda a: get_clipboard(),
        "CLIPBOARD_SET":      lambda a: set_clipboard(a),
    }

    handler = handlers.get(action)
    if handler:
        return handler(argument)
    else:
        msg = f"Unknown system action: {action}"
        print(f"  [SystemControl] ⚠️  {msg}")
        return msg


# ─── STANDALONE TEST ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  🧪 system_control.py — Standalone Test Menu")
    print("=" * 60)

    menu = {
        "1":  ("Volume Up",             lambda: volume_up()),
        "2":  ("Volume Down",           lambda: volume_down()),
        "3":  ("Set Volume to 50%",     lambda: set_volume(50)),
        "4":  ("Mute",                  lambda: mute()),
        "5":  ("Unmute",                lambda: unmute()),
        "6":  ("Brightness Up",         lambda: brightness_up()),
        "7":  ("Brightness Down",       lambda: brightness_down()),
        "8":  ("Set Brightness to 60%", lambda: set_brightness(60)),
        "9":  ("Enable Dark Mode",      lambda: enable_dark_mode()),
        "10": ("Disable Dark Mode",     lambda: disable_dark_mode()),
        "11": ("Toggle Dark Mode",      lambda: toggle_dark_mode()),
        "12": ("Wi-Fi On",              lambda: wifi_on()),
        "13": ("Wi-Fi Off",             lambda: wifi_off()),
        "14": ("Bluetooth On",          lambda: bluetooth_on()),
        "15": ("Bluetooth Off",         lambda: bluetooth_off()),
        "16": ("DND On",                lambda: enable_do_not_disturb()),
        "17": ("DND Off",               lambda: disable_do_not_disturb()),
        "18": ("Sleep Display",         lambda: sleep_display()),
        "19": ("Take Screenshot",       lambda: take_screenshot()),
        "20": ("Get Battery",           lambda: get_battery()),
        "21": ("What time is it?",      lambda: get_time()),
        "22": ("Open YouTube",          lambda: open_website("youtube")),
        "23": ("Search Google: Python", lambda: search_google("Python tutorials")),
        "24": ("Open Calculator",       lambda: open_app("Calculator")),
        "25": ("Open Downloads Folder", lambda: open_folder("downloads")),
        "26": ("Get Clipboard",         lambda: get_clipboard()),
        "27": ("Empty Trash",           lambda: empty_trash()),
        "28": ("Lock Screen",           lambda: lock_screen()),
        "q":  ("Quit",                  None),
    }

    for key, (label, _) in menu.items():
        print(f"  [{key}] {label}")
    print()

    while True:
        choice = input("  Choose an action (number / q): ").strip().lower()
        if choice == "q":
            print("  Goodbye!")
            break
        entry = menu.get(choice)
        if entry:
            label, fn = entry
            if fn:
                print(f"\n  → Running: {label}")
                result = fn()
                print(f"  → Result : {result}\n")
        else:
            print("  Invalid choice, try again.")

    print("\n✅ system_control.py standalone test complete!")
