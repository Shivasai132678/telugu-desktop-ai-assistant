# main.py
# ─── Bujji AI Assistant — Main Orchestrator ───────────────────────────────────
#
# This is the entry point that wires ALL modules together into a running
# voice assistant:
#
#   1. Starts the wake-word listener in a background thread
#   2. When "Hey Bujji" is detected, speaks the confirmation
#   3. Captures the user's voice command via Whisper
#   4. Sends the command to Gemma4:e2b via Ollama
#   5. Routes the LLM response through intent_router
#      → System actions are executed (volume, brightness, apps, etc.)
#      → Conversational replies are spoken back via TTS
#   6. Returns to listening state — loop forever
#
# USAGE:
#   python main.py
#   python main.py --cli           ← text-only mode (no microphone needed)
#   python main.py --debug         ← verbose logging
#
# REQUIREMENTS:
#   • Ollama running:         `ollama serve`
#   • Gemma4:e2b pulled:      `ollama pull gemma4:e2b`
#   • Virtual env active:     `source venv/bin/activate`
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import time
import threading
import argparse
import signal

# ─── Path setup ───────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import (
    WAKE_WORD,
    WAKE_CONFIRMATION,
    SLEEP_MESSAGE,
    RECOGNITION_MODE,
    COMMAND_RECORD_SECONDS,
)

# ─── Module imports ───────────────────────────────────────────────────────────
from modules.wake_listener  import contains_wake_word
from modules.voice_input    import listen_once
from modules.voice_output   import speak
from modules.llm_engine     import chat, stream_chat, check_ollama_health, reset_history
from modules.intent_router  import route
from modules.system_control import check_system_tools
from modules.translator     import translate_to_telugu, detect_language


# ──────────────────────────────────────────────────────────────────────────────
#  GLOBALS
# ──────────────────────────────────────────────────────────────────────────────

_shutdown_event = threading.Event()     # Set to True to gracefully stop all threads
_wake_event     = threading.Event()     # Set to True when wake word is detected
_interaction_active = threading.Event()  # Set while command capture/response is in progress
_debug          = False


def dlog(msg: str) -> None:
    """Print debug messages only when --debug flag is active."""
    if _debug:
        print(f"  [DEBUG] {msg}")


# ──────────────────────────────────────────────────────────────────────────────
#  WAKE WORD LISTENER THREAD
# ──────────────────────────────────────────────────────────────────────────────

def _wake_word_thread_fn():
    """
    Runs continuously in a background thread.
    Sets _wake_event when the wake word "Hey Bujji" is heard.
    Stops when _shutdown_event is set.
    """
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 150
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.6

    print(f'\n  👂 Wake listener started. Say "{WAKE_WORD}" to activate Bujji…\n')

    with sr.Microphone() as source:
        speak("Calibrating microphone, please stay quiet for a moment.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        dlog("Mic calibrated for wake listener.")
        speak("Microphone ready. I'm now listening for the wake word.")

        while not _shutdown_event.is_set():
            if _interaction_active.is_set():
                time.sleep(0.1)
                continue

            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=3)

                if _shutdown_event.is_set():
                    break

                try:
                    if RECOGNITION_MODE == "google":
                        text = recognizer.recognize_google(audio).lower()
                    else:
                        text = recognizer.recognize_sphinx(audio).lower()

                    dlog(f"Wake listener heard: '{text}'")

                    if contains_wake_word(text):
                        print(f"\n  👂 Wake word detected! Activating Bujji…")
                        import urllib.request
                        try:
                            urllib.request.urlopen("http://127.0.0.1:8766/state?mode=awake", timeout=0.2)
                        except Exception:
                            pass
                        _wake_event.set()

                except sr.UnknownValueError:
                    pass  # silence — expected most of the time
                except sr.RequestError as e:
                    print(f"  ⚠️  Recognition error: {e}")
                    if not _interaction_active.is_set():
                        speak(f"Warning: speech recognition error. {e}")

            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                if not _shutdown_event.is_set():
                    print(f"  ⚠️  Wake listener error: {e}")
                continue

    print("  [WakeListener] Thread stopped.")


# ──────────────────────────────────────────────────────────────────────────────
#  VOICE CONVERSATION LOOP
# ──────────────────────────────────────────────────────────────────────────────

def handle_voice_interaction() -> None:
    """
    Called when the wake word is detected.
    Stays in continuous listening mode for multiple commands.
    Say "hey bujji" anytime to confirm it's listening.
    Say "goodbye" or "sleep" to exit.
    """
    _interaction_active.set()
    import urllib.request
    import urllib.parse

    try:
        def _speak_status(message: str) -> None:
            """Speak short real-time process updates."""
            if message and message.strip():
                speak(message)

        # 1. Acknowledge wake
        speak(WAKE_CONFIRMATION)
        print(f'  🤖 Bujji: "{WAKE_CONFIRMATION}"')

        while True:
            # 2. Capture command (auto-stop on silence, up to N seconds)
            print(f"  🎙️  Listening for your command (up to {COMMAND_RECORD_SECONDS}s)…")
            try:
                urllib.request.urlopen("http://127.0.0.1:8766/speech?text=" + urllib.parse.quote("🎙️ Listening..."), timeout=0.2)
            except Exception:
                pass

            user_text = listen_once(
                max_seconds=COMMAND_RECORD_SECONDS,
                status_cb=_speak_status,
            )

            if not user_text or len(user_text.strip()) < 2:
                msg = "I didn't catch that. Please try again."
                speak(msg)
                print(f"  🤖 Bujji: '{msg}'")
                continue

            print(f"  🗣️  You said: '{user_text}'")

            # If the user says the wake phrase again, acknowledge it and stay awake.
            if contains_wake_word(user_text):
                print(f'  🤖 Bujji: "{WAKE_CONFIRMATION}"')
                speak(WAKE_CONFIRMATION)
                continue

            # Check for exit commands
            exit_words = ["goodbye", "sleep", "bye", "stop listening", "that's all"]
            if any(word in user_text.lower() for word in exit_words):
                sleep_msg = "Goodbye! I'll be here when you need me."
                speak(sleep_msg)
                print(f'  🤖 Bujji: "{sleep_msg}"')
                try:
                    urllib.request.urlopen("http://127.0.0.1:8766/state?mode=sleeping", timeout=0.2)
                except Exception:
                    pass
                break

            # 3. Send to LLM
            print(f"  🧠 Sending to Gemma4:e2b…")
            try:
                urllib.request.urlopen("http://127.0.0.1:8766/speech?text=" + urllib.parse.quote("🧠 Thinking..."), timeout=0.2)
            except Exception:
                pass
            llm_response = chat(user_text)
            print(f"  🤖 Raw LLM response: '{llm_response}'")

            # 4. Translate to Telugu if Gemma4 replied in English
            lang = detect_language(llm_response)
            if lang == "english" and not llm_response.strip().startswith("SYSTEM_ACTION:"):
                print(f"  🔄 Translating English → Telugu…")
                llm_response = translate_to_telugu(llm_response)
                print(f"  🤖 Telugu response: '{llm_response}'")

            # 5. Route response (system action OR speak reply)
            kind, result = route(llm_response, speak_fn=speak, silent=False)
            if kind == "system":
                speak("పని పూర్తయింది. తదుపరి ఆదేశం చెప్పండి.")   # Task done. Tell me next command.
            else:
                speak("తదుపరి ఆదేశం చెప్పండి.")   # Tell me next command.

            # Continue listening for next command (don't break)

        print()  # visual spacer
    finally:
        try:
            urllib.request.urlopen("http://127.0.0.1:8766/state?mode=walking", timeout=0.2)
        except Exception:
            pass
        _interaction_active.clear()


# ──────────────────────────────────────────────────────────────────────────────
#  CLI TEXT MODE
# ──────────────────────────────────────────────────────────────────────────────

def run_cli_mode() -> None:
    """
    Text-only mode — no microphone needed.
    Useful for testing the LLM + routing pipeline without audio hardware.
    """
    print("\n" + "=" * 60)
    print("  🤖 Bujji — CLI Text Mode")
    print("=" * 60)
    print("  Type your message and press Enter.")
    print("  Commands: 'reset' to clear history, 'quit' to exit.")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("  You → ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("  Goodbye!")
            break
        if user_input.lower() == "reset":
            reset_history()
            print("  🔄 Conversation history cleared.\n")
            continue

        print("  🧠 Thinking…")
        llm_response = chat(user_input)
        print(f"  📝 Raw LLM: {llm_response!r}")

        # Translate to Telugu if Gemma4 replied in English
        lang = detect_language(llm_response)
        if lang == "english" and not llm_response.strip().startswith("SYSTEM_ACTION:"):
            print("  🔄 Translating to Telugu…")
            llm_response = translate_to_telugu(llm_response)
            print(f"  📝 Telugu: {llm_response!r}")

        kind, result = route(llm_response)
        print(f"  ✅ [{kind.upper()}] {result}")
        print()


# ──────────────────────────────────────────────────────────────────────────────
#  MAIN — VOICE MODE
# ──────────────────────────────────────────────────────────────────────────────

def run_voice_mode() -> None:
    """
    Full voice mode:
      - Wake word listener runs in background thread
      - Main thread handles interactions when wake word fires
    """
    print("\n" + "=" * 60)
    print("  🤖 Bujji AI Assistant — Voice Mode")
    print("=" * 60)
    print(f"  Wake word  : '{WAKE_WORD}'")
    print(f"  Model      : gemma4:e2b via Ollama")
    print(f"  Mode       : {RECOGNITION_MODE}")
    print("=" * 60)
    speak("Bujji AI Assistant is starting up.")

    # Spawn Electron robot pet in background
    import subprocess
    electron_process = None
    try:
        electron_process = subprocess.Popen(
            ["npm", "start"],
            cwd="/Users/kmsreenidhi/wake up/robot-pet",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"  ⚠️  Failed to start Electron robot pet: {e}")

    # Graceful shutdown on Ctrl+C
    def _signal_handler(sig, frame):
        print("\n\n  ⛔ Shutting down Bujji…")
        speak("Shutting down. Goodbye!")
        _shutdown_event.set()
        if electron_process:
            try:
                electron_process.terminate()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)

    # Health check
    print("\n  🔍 Checking Ollama…")
    speak("Checking if Ollama is running.")
    check_ollama_health()

    print("\n  🔧 Checking system tools…")
    speak("Checking system tools.")
    check_system_tools()

    speak("All systems ready. Say Hey Bujji to wake me up.")

    # Start wake-word listener after the startup prompt finishes so calibration
    # happens against room noise instead of Bujji's own voice output.
    wake_thread = threading.Thread(
        target=_wake_word_thread_fn,
        name="WakeWordListener",
        daemon=True,
    )
    wake_thread.start()

    # ─── Main event loop ──────────────────────────────────────────────────────
    while not _shutdown_event.is_set():
        # Block until wake word is detected (or shutdown)
        woken = _wake_event.wait(timeout=1.0)

        if _shutdown_event.is_set():
            break

        if woken:
            _wake_event.clear()          # Reset for next interaction
            try:
                handle_voice_interaction()
                speak("Back to listening. Say Hey Bujji whenever you need me.")
            except Exception as e:
                print(f"  ❌ Interaction error: {e}")
                speak("Sorry, something went wrong. I'm back to listening.")

    print("  👋 Bujji has shut down. Goodbye!")


def run_api_mode(host: str, port: int) -> None:
    """
    Start the REST API server.
    """
    import uvicorn
    from api_server import app

    print("\n" + "=" * 60)
    print("  🤖 Bujji AI Assistant — REST API Mode")
    print("=" * 60)
    print(f"  Host      : {host}")
    print(f"  Port      : {port}")
    print("=" * 60)

    uvicorn.run(app, host=host, port=port, log_level="info")


# ──────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    global _debug

    parser = argparse.ArgumentParser(
        description="Bujji AI Assistant powered by Gemma4:e2b"
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--cli",
        action="store_true",
        help="Run in text-only CLI mode (no microphone required)",
    )
    modes.add_argument(
        "--api",
        action="store_true",
        help="Run REST API server mode",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for REST API server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for REST API server (default: 8000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging",
    )
    args = parser.parse_args()
    _debug = args.debug

    if args.cli:
        run_cli_mode()
    elif args.api:
        run_api_mode(args.host, args.port)
    else:
        run_voice_mode()


if __name__ == "__main__":
    main()
