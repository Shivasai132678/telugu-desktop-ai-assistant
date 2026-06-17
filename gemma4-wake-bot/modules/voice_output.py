# modules/voice_output.py
# ─── Voice Output Module ──────────────────────────────────────────────────────
# Text-to-Speech (TTS) for Bujji using Piper TTS (Telugu voice).
# Translation is handled upstream by modules/translator.py — this module
# ONLY converts already-Telugu text to speech.
#
# STANDALONE TEST:
#   python -m modules.voice_output
#
# USED BY:
#   main.py & intent_router.py → call speak(text) to voice a reply
# ─────────────────────────────────────────────────────────────────────────────

import os
import re
import sys
import threading
import unicodedata

import numpy as np
import sounddevice as sd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

VOICE_MODEL_PATH_TE = os.getenv(
    "PIPER_VOICE_MODEL_TE",
    os.path.join(
        BASE_DIR,
        "piper_voices",
        "te",
        "te_IN",
        "padmavathi",
        "medium",
        "te_IN-padmavathi-medium.onnx",
    ),
)
VOICE_MODEL_PATH_EN = os.getenv(
    "PIPER_VOICE_MODEL_EN",
    os.path.join(
        BASE_DIR,
        "piper_voices",
        "en",
        "en_US",
        "lessac",
        "medium",
        "en_US-lessac-medium.onnx",
    ),
)

_voice_cache = {}
_voice_lock = threading.Lock()


def _get_voice(model_path: str):
    """Load a Piper voice model once and reuse it."""
    if model_path in _voice_cache:
        return _voice_cache[model_path]

    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Piper voice model not found at: {model_path}\n"
            "Set PIPER_VOICE_MODEL_TE or PIPER_VOICE_MODEL_EN, or download a model into ./piper_voices."
        )

    from piper import PiperVoice

    voice = PiperVoice.load(model_path)
    _voice_cache[model_path] = voice
    print(f"  [VoiceOutput] Piper voice loaded from {model_path} ✓")
    return voice


def _has_telugu(text: str) -> bool:
    return bool(re.search(r"[\u0C00-\u0C7F]", text))


def _select_voice_path(text: str, lang: str | None = None) -> str:
    if lang == "te":
        return VOICE_MODEL_PATH_TE
    if lang == "en":
        return VOICE_MODEL_PATH_EN or VOICE_MODEL_PATH_TE
    if _has_telugu(text):
        return VOICE_MODEL_PATH_TE
    return VOICE_MODEL_PATH_EN or VOICE_MODEL_PATH_TE


def _clean_text(text: str) -> str:
    """Remove markdown symbols and excess whitespace before synthesis."""
    return (
        text.replace("**", "")
            .replace("*", "")
            .replace("_", " ")
            .replace("#", "")
            .replace("`", "")
            .replace("\n", " ")
            .strip()
    )


def _sanitize_telugu(text: str) -> str:
    """Keep only Telugu Unicode range + basic punctuation/space."""
    text = unicodedata.normalize("NFC", text)
    keep = []
    for ch in text:
        if re.match(r"[\u0C00-\u0C7F]", ch):
            keep.append(ch)
        elif ch.isspace():
            keep.append(" ")
        elif ch in ".,!?;:'\"-()[]":
            keep.append(ch)
    return re.sub(r"\s+", " ", "".join(keep)).strip()


def _notify_speech(text: str, duration: float | None = None) -> None:
    """Notify the robot app to show a speech bubble for a duration."""
    import urllib.request
    import urllib.parse
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"http://127.0.0.1:8766/speech?text={encoded_text}"
        if duration is not None:
            url += f"&duration={duration:.2f}"
        urllib.request.urlopen(url, timeout=0.2)
    except Exception:
        pass


def speak(text: str, block: bool = True, lang: str | None = None) -> None:
    """
    Convert `text` to speech using Piper TTS (Telugu voice).

    Translation must happen BEFORE calling speak() — this function only
    handles text-to-speech synthesis.

    Args:
        text:  Telugu text to speak (or any text — Piper will attempt it).
        block: If True, block until playback finishes.
               If False, play in a background thread.
        lang:  Optional language hint (currently unused).
    """
    if not text or not text.strip():
        return

    clean = _clean_text(text)
    if not clean:
        return

    print(f"  [VoiceOutput] 🔊 Speaking: '{clean[:80]}{'…' if len(clean) > 80 else ''}'")

    voice_path = _select_voice_path(clean, lang=lang)
    if voice_path == VOICE_MODEL_PATH_TE:
        # Piper Telugu models can fail on non-Telugu glyphs; strip unsupported chars.
        sanitized = _sanitize_telugu(clean)
        if sanitized:
            clean = sanitized

    def _play() -> None:
        with _voice_lock:
            try:
                voice = _get_voice(voice_path)
                chunks = list(voice.synthesize(clean))
            except Exception as exc:
                if voice_path == VOICE_MODEL_PATH_TE and VOICE_MODEL_PATH_EN:
                    # Fallback to English voice if Telugu synthesis fails.
                    print(f"  [VoiceOutput] Telugu TTS failed: {exc}. Falling back to EN voice.")
                    voice = _get_voice(VOICE_MODEL_PATH_EN)
                    chunks = list(voice.synthesize(clean))
                else:
                    raise

        if not chunks:
            return

        audio = (
            np.concatenate([c.audio_int16_array for c in chunks])
            .astype(np.float32) / 32768.0
        )
        duration = float(audio.shape[0]) / float(chunks[0].sample_rate)
        _notify_speech(clean, duration=duration)
        try:
            sd.play(audio, samplerate=chunks[0].sample_rate)
            sd.wait()
        except Exception as e:
            print(f"  [VoiceOutput] Audio playback failed: {e}")
            # Try a safe fallback using the device's default sample rate
            try:
                device_info = sd.query_devices(kind="output")
                default_sr = int(device_info.get("default_samplerate", chunks[0].sample_rate))
                sd.play(audio, samplerate=default_sr)
                sd.wait()
            except Exception as e2:
                print(f"  [VoiceOutput] Fallback playback also failed: {e2}")
                # Last resort: write WAV to /tmp for debugging so audio can be inspected
                try:
                    import tempfile
                    from scipy.io.wavfile import write as wavwrite

                    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    wavwrite(tmp.name, int(chunks[0].sample_rate), (audio * 32767).astype(np.int16))
                    print(f"  [VoiceOutput] Wrote audio to {tmp.name} for debugging.")
                except Exception as e3:
                    print(f"  [VoiceOutput] Failed to write fallback WAV: {e3}")

    if block:
        _play()
    else:
        threading.Thread(target=_play, daemon=True).start()


# ─── STANDALONE TEST ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  🧪 voice_output.py — Standalone Test")
    print("=" * 55)
    print(f"  Model path (TE): {VOICE_MODEL_PATH_TE}")
    print(f"  Model exists (TE): {os.path.exists(VOICE_MODEL_PATH_TE)}")
    print(f"  Model path (EN): {VOICE_MODEL_PATH_EN}")
    print(f"  Model exists (EN): {os.path.exists(VOICE_MODEL_PATH_EN)}")
    print("=" * 55)
    print()

    test_phrases = [
        "నమస్కారం! నేను మీ సహాయకుడిని బుజ్జి.",
        "మీకు ఏమి సహాయం కావాలి?",
        "మీ వాల్యూమ్ పెంచబడింది.",
    ]

    for phrase in test_phrases:
        print(f"  Speaking: {phrase!r}")
        speak(phrase, block=True)
        print()

    print("✅ voice_output.py standalone test complete!")
