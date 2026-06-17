# XTTS-v2 Voice Cloning Integration for Bujji Bot

## Context

This document provides a full implementation guide to replace the existing Piper TTS in `modules/voice_output.py` with XTTS-v2 (Coqui TTS) for zero-shot voice cloning using a personal voice recording.

**Project:** `gemma4-wake-bot` (Bujji)  
**File to modify:** `modules/voice_output.py`  
**Config file:** `config.py`  
**Languages supported:** Telugu (`te`) and English (`en`)

---

## Prerequisites

### 1. Install Dependencies

```bash
pip install TTS soundfile numpy sounddevice
```

> Note: `TTS` is the Coqui TTS package. On first run it will auto-download the `xtts_v2` model (~1.8 GB).

### 2. Record Your Voice Sample

Record a clean **10–30 second WAV file** of your voice:
- Format: **WAV, 22050 Hz, mono**
- Content: Speak naturally — a few sentences in Telugu and/or English
- No background noise, no music, no echo
- Save as: `assets/my_voice.wav` inside the project root

**Recommended tool:** Audacity (free) — File → Export → WAV → 22050 Hz mono

---

## Config Changes (`config.py`)

Add the following constant:

```python
# Voice cloning — path to your personal voice sample WAV
SPEAKER_WAV = "./assets/my_voice.wav"
```

---

## Full Replacement: `modules/voice_output.py`

Replace the entire file with the following:

```python
# modules/voice_output.py
# ─── Voice Output Module (XTTS-v2 Voice Cloning) ─────────────────────────────
# Text-to-Speech using Coqui XTTS-v2 with personal voice cloning.
# Supports Telugu ("te") and English ("en") — language auto-detected by script.
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
import tempfile

import numpy as np
import sounddevice as sd
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SPEAKER_WAV

# ─── XTTS-v2 Model (loaded once, reused) ─────────────────────────────────────
_xtts_model = None
_xtts_lock = threading.Lock()

def _get_xtts():
    """Load XTTS-v2 model once and cache it."""
    global _xtts_model
    if _xtts_model is not None:
        return _xtts_model
    from TTS.api import TTS
    print("[VoiceOutput] Loading XTTS-v2 model (first run downloads ~1.8 GB)…")
    _xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    print("[VoiceOutput] XTTS-v2 loaded ✓")
    return _xtts_model

# ─── Language & Text Utilities ────────────────────────────────────────────────

def _has_telugu(text: str) -> bool:
    """Return True if text contains Telugu Unicode characters."""
    return bool(re.search(r"[\u0C00-\u0C7F]", text))

def _detect_language(text: str) -> str:
    """Return XTTS-v2 language code: 'te' for Telugu, 'en' for English."""
    return "te" if _has_telugu(text) else "en"

def _clean_text(text: str) -> str:
    """Strip markdown symbols before synthesis."""
    return (
        text.replace("**", "")
            .replace("*", "")
            .replace("_", " ")
            .replace("#", "")
            .replace("`", "")
            .replace("\n", " ")
            .strip()
    )

# ─── Core speak() Function ────────────────────────────────────────────────────

def speak(text: str, block: bool = True, lang: str | None = None) -> None:
    """
    Convert `text` to speech using XTTS-v2 with your cloned voice.

    Translation must happen BEFORE calling speak() — this function only
    handles text-to-speech synthesis.

    Args:
        text:  Text to speak (Telugu or English — auto-detected).
        block: If True, block until playback finishes.
               If False, play in a background thread.
        lang:  Optional language override ('te' or 'en').
               If None, auto-detected from script.
    """
    if not text or not text.strip():
        return

    clean = _clean_text(text)
    if not clean:
        return

    language = lang if lang else _detect_language(clean)
    print(f"[VoiceOutput] 🔊 Speaking [{language}]: '{clean[:80]}{'…' if len(clean) > 80 else ''}'")

    def _play() -> None:
        with _xtts_lock:
            tts = _get_xtts()

            # Validate speaker WAV exists
            if not os.path.exists(SPEAKER_WAV):
                print(f"[VoiceOutput] ⚠️  Speaker WAV not found: {SPEAKER_WAV}")
                print("[VoiceOutput] Record your voice and save it to that path.")
                return

            # Synthesise to a temp WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                tts.tts_to_file(
                    text=clean,
                    speaker_wav=SPEAKER_WAV,
                    language=language,
                    file_path=tmp_path,
                )

                # Load and play via sounddevice
                data, sample_rate = sf.read(tmp_path, dtype="float32")
                sd.play(data, samplerate=sample_rate)
                sd.wait()

            finally:
                os.unlink(tmp_path)  # clean up temp file

    if block:
        _play()
    else:
        threading.Thread(target=_play, daemon=True).start()


# ─── STANDALONE TEST ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print(" 🧪 voice_output.py — XTTS-v2 Standalone Test")
    print("=" * 55)
    print(f" Speaker WAV : {SPEAKER_WAV}")
    print(f" WAV exists  : {os.path.exists(SPEAKER_WAV)}")
    print("=" * 55)
    print()

    test_phrases = [
        ("నమస్కారం! నేను మీ సహాయకుడిని బుజ్జి.", "te"),
        ("Hello! I am Bujji, your assistant.", "en"),
    ]

    for phrase, detected_lang in test_phrases:
        print(f" Speaking [{detected_lang}]: {phrase!r}")
        speak(phrase, block=True)
        print()

    print("✅ XTTS-v2 standalone test complete!")
```

---

## What Changed vs. Original Piper Version

| Area | Original (Piper) | New (XTTS-v2) |
|------|-----------------|---------------|
| Model loading | `PiperVoice.load(model_path)` | `TTS("tts_models/multilingual/multi-dataset/xtts_v2")` |
| Voice selection | Two `.onnx` files (one per language) | Single `SPEAKER_WAV` recording for both languages |
| Synthesis call | `voice.synthesize(clean)` | `tts.tts_to_file(text, speaker_wav, language, file_path)` |
| Audio playback | `np.concatenate(chunks)` → `sd.play()` | `sf.read(tmp.wav)` → `sd.play()` |
| Language detection | `_has_telugu()` → picks `.onnx` path | `_has_telugu()` → passes `"te"` or `"en"` to XTTS-v2 |
| `speak()` signature | Unchanged | Unchanged ✅ |
| `_clean_text()` | Unchanged | Unchanged ✅ |
| `block` param | Unchanged | Unchanged ✅ |

> All callers of `speak()` in `main.py`, `intent_router.py`, and `gui.py` require **zero changes**.

---

## Switching Back to Piper (Rollback)

If you want to revert, restore the original `voice_output.py` and remove `SPEAKER_WAV` from `config.py`. No other files need to change.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `FileNotFoundError` on model | Run once with internet — XTTS-v2 auto-downloads |
| `Speaker WAV not found` | Record your voice and save to `./assets/my_voice.wav` |
| Telugu sounds robotic | Use a longer recording (20–30 sec) with Telugu sentences |
| High latency | XTTS-v2 is slower than Piper; use `block=False` for non-critical speech |
| `soundfile` not installed | `pip install soundfile` |
| Audio distorted | Ensure WAV is 22050 Hz mono; re-export from Audacity if needed |

---

## Quick Checklist

- [ ] `pip install TTS soundfile` done
- [ ] Voice sample recorded → saved as `./assets/my_voice.wav` (WAV, 22050 Hz, mono, 10–30 sec)
- [ ] `SPEAKER_WAV = "./assets/my_voice.wav"` added to `config.py`
- [ ] `modules/voice_output.py` replaced with the code above
- [ ] Standalone test run: `python -m modules.voice_output`
- [ ] Bujji bot launched and voice verified in GUI
