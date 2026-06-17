# modules/intent_router.py
# ─── Intent Router Module ─────────────────────────────────────────────────────
# Parses the LLM's raw response and routes it to the correct handler:
#   • SYSTEM_ACTION tag  → system_control.dispatch()
#   • Plain text reply   → voice_output.speak()
#
# The router is the "glue" between the LLM brain and the action layer.
#
# STANDALONE TEST:
#   python -m modules.intent_router
#   (Runs a set of mock LLM responses through the router and shows results)
#
# USED BY:
#   main.py → calls route(llm_response, speak_fn) after every LLM reply
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import re
from typing import Callable, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Regex: matches SYSTEM_ACTION:<ACTION> or SYSTEM_ACTION:<ACTION>:<ARG> ────
# Examples:
#   SYSTEM_ACTION:VOLUME_UP
#   SYSTEM_ACTION:BRIGHTNESS_SET:70
#   SYSTEM_ACTION:SEARCH:python tutorials
#   SYSTEM_ACTION:OPEN_WEB:youtube.com
_SYSTEM_ACTION_RE = re.compile(
    r"SYSTEM_ACTION:([A-Z_\-\s]+)(?::(.+))?",
    re.IGNORECASE
)


def _normalize_action(action: str) -> str:
    """Normalize action tokens to match system_control.dispatch keys."""
    raw = re.sub(r"[\s\-]+", "_", action.strip().upper())

    alias_map = {
        # Volume
        "INCREASE_BRIGHTNESS": "BRIGHTNESS_UP",
        "DECREASE_BRIGHTNESS": "BRIGHTNESS_DOWN",
        "RAISE_BRIGHTNESS":    "BRIGHTNESS_UP",
        "LOWER_BRIGHTNESS":    "BRIGHTNESS_DOWN",
        "BRIGHTNESS_UP":       "BRIGHTNESS_UP",
        "BRIGHTNESS_DOWN":     "BRIGHTNESS_DOWN",
        "INCREASE_VOLUME":     "VOLUME_UP",
        "DECREASE_VOLUME":     "VOLUME_DOWN",
        "RAISE_VOLUME":        "VOLUME_UP",
        "LOWER_VOLUME":        "VOLUME_DOWN",
        "VOLUME_UP":           "VOLUME_UP",
        "VOLUME_DOWN":         "VOLUME_DOWN",
        # Dark Mode
        "DARK_MODE":           "DARK_MODE_TOGGLE",
        "DARKMODE":            "DARK_MODE_TOGGLE",
        "NIGHT_MODE":          "DARK_MODE_ON",
        "LIGHT_MODE":          "DARK_MODE_OFF",
        # Wi-Fi
        "WIFI":                "WIFI_STATUS",
        "TURN_ON_WIFI":        "WIFI_ON",
        "TURN_OFF_WIFI":       "WIFI_OFF",
        "ENABLE_WIFI":         "WIFI_ON",
        "DISABLE_WIFI":        "WIFI_OFF",
        # Bluetooth
        "TURN_ON_BLUETOOTH":   "BLUETOOTH_ON",
        "TURN_OFF_BLUETOOTH":  "BLUETOOTH_OFF",
        "ENABLE_BLUETOOTH":    "BLUETOOTH_ON",
        "DISABLE_BLUETOOTH":   "BLUETOOTH_OFF",
        # Do Not Disturb
        "DO_NOT_DISTURB":      "DND_ON",
        "DND":                 "DND_ON",
        "FOCUS_MODE":          "DND_ON",
        # Power
        "SLEEP_SYSTEM":        "SLEEP",
        "SLEEP_SCREEN":        "SLEEP_DISPLAY",
        # Misc
        "TRASH":               "EMPTY_TRASH",
        "CLOSE_APP":           "QUIT_APP",
    }

    return alias_map.get(raw, raw)


def parse_response(llm_response: str) -> Tuple[str, str, str]:
    """
    Parse the LLM's raw response string.

    Returns a tuple of:
        (kind, action, argument)

    Where:
        kind     → "system"  if a SYSTEM_ACTION tag was detected
                   "speech"  if the response is plain conversational text
        action   → action keyword (e.g. "VOLUME_UP") if kind=="system", else ""
        argument → action argument (e.g. "50")        if kind=="system", else ""
    """
    if not llm_response:
        return ("speech", "", "")

    text = llm_response.strip()

    match = _SYSTEM_ACTION_RE.search(text)
    if match:
        action   = _normalize_action(match.group(1))
        argument = (match.group(2) or "").strip()
        return ("system", action, argument)

    return ("speech", "", text)


def route(
    llm_response: str,
    speak_fn: Optional[Callable[[str], None]] = None,
    silent: bool = False,
) -> Tuple[str, str]:
    """
    Route the LLM response to the appropriate handler.

    Args:
        llm_response: Raw string returned by llm_engine.chat() or stream_chat().
        speak_fn:     Function to call for speech output. If None, imports
                      voice_output.speak automatically.
        silent:       If True, skip speaking (useful for pure CLI / testing mode).

    Returns:
        (kind, result_message)
        kind           → "system" or "speech"
        result_message → human-readable result string
    """
    from modules import system_control

    if speak_fn is None and not silent:
        from modules import voice_output
        speak_fn = voice_output.speak

    kind, action, argument = parse_response(llm_response)

    if kind == "system":
        print(f"  [IntentRouter] 🔧 System action → {action}({argument!r})")

        # Speak progress before executing the action for real-time feedback.
        if not silent and speak_fn:
            progress = _progress_message(action, argument)
            if progress:
                speak_fn(progress)

        result = system_control.dispatch(action, argument)
        if not silent and speak_fn:
            speak_fn(result)
        return ("system", result)

    else:
        # Plain conversational text
        text = argument  # parse_response puts text in `argument` for speech kind
        if not text:
            text = llm_response.strip()

        print(f"  [IntentRouter] 💬 Speech reply → '{text[:60]}{'…' if len(text) > 60 else ''}'")
        if not silent and speak_fn:
            speak_fn(text)
        return ("speech", text)


def _progress_message(action: str, argument: str) -> str:
    """Return a short spoken message that announces the action in progress."""
    action = action.strip().upper()
    messages = {
        "VOLUME_UP":        "Increasing the volume.",
        "VOLUME_DOWN":      "Decreasing the volume.",
        "MUTE":             "Muting the volume.",
        "UNMUTE":           "Unmuting.",
        "BRIGHTNESS_UP":    "Increasing the brightness.",
        "BRIGHTNESS_DOWN":  "Decreasing the brightness.",
        "DARK_MODE_ON":     "Enabling dark mode.",
        "DARK_MODE_OFF":    "Switching to light mode.",
        "DARK_MODE_TOGGLE": "Toggling dark mode.",
        "WIFI_ON":          "Turning Wi-Fi on.",
        "WIFI_OFF":         "Turning Wi-Fi off.",
        "BLUETOOTH_ON":     "Turning Bluetooth on.",
        "BLUETOOTH_OFF":    "Turning Bluetooth off.",
        "DND_ON":           "Enabling Do Not Disturb.",
        "DND_OFF":          "Disabling Do Not Disturb.",
        "SLEEP":            "Putting the system to sleep.",
        "SLEEP_DISPLAY":    "Turning off the display.",
        "RESTART":          "Restarting the system.",
        "SHUTDOWN":         "Shutting down.",
        "SCREENSHOT":       "Taking a screenshot.",
        "LOCK":             "Locking the screen.",
        "EMPTY_TRASH":      "Emptying the trash.",
        "BATTERY":          "Checking battery status.",
    }
    if action == "VOLUME_SET":
        return f"Setting volume to {argument.strip()} percent." if argument else "Setting volume."
    if action == "BRIGHTNESS_SET":
        return f"Setting brightness to {argument.strip()} percent." if argument else "Setting brightness."
    if action == "OPEN_APP":
        return f"Opening {argument}." if argument else "Opening app."
    if action == "QUIT_APP":
        return f"Quitting {argument}." if argument else "Quitting app."
    if action == "OPEN_WEB":
        return f"Opening {argument} in your browser." if argument else "Opening website."
    if action == "SEARCH":
        return f"Searching Google for {argument}." if argument else "Searching Google."
    if action == "SEARCH_YOUTUBE":
        return f"Searching YouTube for {argument}." if argument else "Searching YouTube."
    if action == "OPEN_FOLDER":
        return f"Opening your {argument} folder." if argument else "Opening folder."
    if action == "CLIPBOARD_SET":
        snippet = argument[:30] + "…" if argument and len(argument) > 30 else argument
        return f"Copying to clipboard: {snippet}." if argument else "Copying to clipboard."
    static_extras = {
        "WIFI_STATUS":    "Checking Wi-Fi status.",
        "TIME":           "Let me check the time.",
        "BATTERY":        "Checking battery status.",
        "CLIPBOARD_GET":  "Reading your clipboard.",
    }
    return messages.get(action, static_extras.get(action, ""))


# ─── STANDALONE TEST ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  🧪 intent_router.py — Standalone Test")
    print("=" * 60)
    print()

    # Mock speak function (prints instead of speaking)
    def mock_speak(text: str):
        print(f"  🔊 [MOCK SPEAK] '{text}'")

    test_cases = [
        # (description, mock_llm_response, expected_kind)
        ("Volume Up",          "SYSTEM_ACTION:VOLUME_UP",                         "system"),
        ("Volume Down",        "SYSTEM_ACTION:VOLUME_DOWN",                       "system"),
        ("Set Volume to 60",   "SYSTEM_ACTION:VOLUME_SET:60",                     "system"),
        ("Mute",               "SYSTEM_ACTION:MUTE",                              "system"),
        ("Unmute",             "SYSTEM_ACTION:UNMUTE",                            "system"),
        ("Brightness Up",      "SYSTEM_ACTION:BRIGHTNESS_UP",                     "system"),
        ("Brightness Down",    "SYSTEM_ACTION:BRIGHTNESS_DOWN",                   "system"),
        ("Set Brightness 50",  "SYSTEM_ACTION:BRIGHTNESS_SET:50",                 "system"),
        ("Screenshot",         "SYSTEM_ACTION:SCREENSHOT",                        "system"),
        ("Open YouTube",       "SYSTEM_ACTION:OPEN_WEB:youtube.com",              "system"),
        ("Google Search",      "SYSTEM_ACTION:SEARCH:python tutorials",           "system"),
        ("YouTube Search",     "SYSTEM_ACTION:SEARCH_YOUTUBE:lofi music",        "system"),
        ("Open App",           "SYSTEM_ACTION:OPEN_APP:Calculator",               "system"),
        ("Open Folder",        "SYSTEM_ACTION:OPEN_FOLDER:downloads",             "system"),
        ("Get Time",           "SYSTEM_ACTION:TIME",                              "system"),
        ("Lock Screen",        "SYSTEM_ACTION:LOCK",                              "system"),
        ("Plain Chat Reply",   "The sky is blue because of Rayleigh scattering.", "speech"),
        ("Mixed (chat wins)",  "Sure! SYSTEM_ACTION:VOLUME_UP done for you.",    "system"),
        ("Empty Response",     "",                                                 "speech"),
    ]

    passed = 0
    failed = 0

    for description, mock_response, expected_kind in test_cases:
        print(f"  ─── {description}")
        print(f"      Input  : {mock_response!r}")
        kind, result = route(mock_response, speak_fn=mock_speak, silent=False)
        status = "✅" if kind == expected_kind else "❌"
        if kind == expected_kind:
            passed += 1
        else:
            failed += 1
        print(f"      Kind   : {kind}  {status}")
        print(f"      Result : {result}")
        print()

    print("=" * 60)
    print(f"  Tests passed: {passed} / {passed + failed}")
    print("=" * 60)
    print("\n✅ intent_router.py standalone test complete!")
