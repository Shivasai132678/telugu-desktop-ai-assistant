# modules/voice_input.py
# ─── Voice Input Module ───────────────────────────────────────────────────────
# Captures spoken audio and transcribes it using OpenAI Whisper.
#
# STANDALONE TEST:
#   python -m modules.voice_input
#   (Records 5 seconds of audio and prints the transcription)
#
# USED BY:
#   main.py → calls capture_command() after wake word is detected
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import tempfile
import time
import wave
import numpy as np
from typing import Callable, Optional

# Ensure package-level imports work when run standalone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COMMAND_RECORD_SECONDS, WHISPER_MODEL_SIZE

# ─── Lazy-load Whisper to avoid slow startup when testing other modules ────────
_whisper_model = None


def _get_whisper(status_cb: Optional[Callable[[str], None]] = None):
    """Load Whisper model once, reuse afterwards."""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print(f"  [VoiceInput] Loading Whisper '{WHISPER_MODEL_SIZE}' model…")
        if status_cb:
            status_cb(f"Loading Whisper {WHISPER_MODEL_SIZE} model. This may take a moment.")
        _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
        print("  [VoiceInput] Whisper ready ✓")
        if status_cb:
            status_cb("Speech transcription model is ready.")
    return _whisper_model


def capture_command(
    seconds: int = COMMAND_RECORD_SECONDS,
    status_cb: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Record `seconds` of audio from the microphone and return the transcription.

    Args:
        seconds: How many seconds to record.

    Returns:
        Transcribed text string (empty string on failure).
    """
    import sounddevice as sd
    from scipy.io.wavfile import write as wav_write

    sample_rate = 16_000  # Whisper expects 16 kHz

    print(f"  [VoiceInput] 🎙️  Recording for {seconds} seconds…")
    if status_cb:
        status_cb(f"Recording your command for up to {seconds} seconds.")
    audio_data = sd.rec(
        int(seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    print("  [VoiceInput] ✅ Recording complete.")
    if status_cb:
        status_cb("Recording complete. Transcribing now.")

    # Write to a temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        wav_write(tmp_path, sample_rate, audio_data)
        model = _get_whisper(status_cb=status_cb)
        # task='transcribe' preserves original language (Telugu or English)
        # language=None lets Whisper auto-detect — no language is forced
        result = model.transcribe(tmp_path, task="transcribe", language=None, fp16=False)
        text = result.get("text", "").strip()
        print(f"  [VoiceInput] Transcribed: '{text}'")
        return text
    except Exception as e:
        print(f"  [VoiceInput] ❌ Transcription error: {e}")
        return ""
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def listen_once(
    max_seconds: int = 10,
    status_cb: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Listen until the user stops speaking (up to max_seconds).
    Uses SpeechRecognition's listen() which auto-detects silence.

    Args:
        max_seconds: Maximum seconds to wait for speech.

    Returns:
        Transcribed text string (empty string on failure/timeout).
    """
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 200
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8  # Silence gap before stopping

    try:
        with sr.Microphone(sample_rate=16_000) as source:
            print("  [VoiceInput] 🎙️  Listening… (speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=max_seconds, phrase_time_limit=max_seconds)

        # Whisper transcription via audio data
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            with open(tmp_path, "wb") as f:
                f.write(audio.get_wav_data())

        model = _get_whisper(status_cb=status_cb)
        result = model.transcribe(tmp_path, task="transcribe", language=None, fp16=False)
        text = result.get("text", "").strip()
        print(f"  [VoiceInput] Transcribed: '{text}'")
        return text

    except sr.WaitTimeoutError:
        print("  [VoiceInput] ⏰ Timeout — nothing heard.")
        if status_cb:
            status_cb("I did not hear anything in time.")
        return ""
    except Exception as e:
        print(f"  [VoiceInput] ❌ Error: {e}")
        if status_cb:
            status_cb("I hit an audio processing error. Please try again.")
        return ""
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


# ─── STANDALONE TEST ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  🧪 voice_input.py — Standalone Test")
    print("=" * 55)
    print(f"  Whisper model : {WHISPER_MODEL_SIZE}")
    print(f"  Record time   : {COMMAND_RECORD_SECONDS}s")
    print("=" * 55)
    print()

    print("Mode 1: Fixed-duration capture")
    text = capture_command(seconds=5)
    print(f"\n  Result: '{text}'\n")

    print("-" * 55)
    print("Mode 2: Auto-stop when you stop speaking (max 10s)")
    text2 = listen_once(max_seconds=10)
    print(f"\n  Result: '{text2}'\n")

    print("✅ voice_input.py standalone test complete!")
