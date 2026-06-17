<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# give me a complete markdown on all the steps requried

Here is the **complete markdown guide** for adding Telugu voice support to your Gemma4 voice assistant:[^1]

***

```markdown
# 🇮🇳 Telugu Voice Assistant — Complete Setup Guide

> Stack: Gemma4:e2b (brain) + Whisper (voice input) + Piper TTS (Telugu voice output)

---

## 📋 Overview

| Component         | Telugu Support? | Action Required             |
|:------------------|:----------------|:----------------------------|
| Gemma4:e2b        | ✅ YES           | Add Telugu instruction to system prompt |
| Whisper           | ✅ YES           | No change needed            |
| Piper TTS         | ✅ YES           | Install + download voice model |
| Kokoro TTS        | ❌ NO            | Remove / replace             |
| Coqui XTTS v2     | ❌ NO            | Remove / replace             |

---

## 🔧 Step 1 — Install Dependencies

```bash
pip install piper-tts sounddevice numpy huggingface_hub
```


---

## 📥 Step 2 — Download Telugu Voice Model

```bash
# Create voice models folder
mkdir piper_voices

# Download via Python
python -c "
from huggingface_hub import hf_hub_download

hf_hub_download(
    repo_id='rhasspy/piper-voices',
    filename='te/te_IN/padmavathi/medium/te_IN-padmavathi-medium.onnx',
    local_dir='./piper_voices'
)
hf_hub_download(
    repo_id='rhasspy/piper-voices',
    filename='te/te_IN/padmavathi/medium/te_IN-padmavathi-medium.onnx.json',
    local_dir='./piper_voices'
)
"
```

> **Manual alternative:** Download directly from
> `https://huggingface.co/rhasspy/piper-voices/tree/main/te/te_IN/padmavathi/medium`

---

## ✏️ Step 3 — Update `config.py`

Add a **single line** to your `SYSTEM_PROMPT` to instruct Gemma4 to respond in Telugu:

```python
# config.py

SYSTEM_PROMPT = """
You are a smart voice assistant. Always respond in Telugu (తెలుగు) language only.
Use simple, natural Telugu — not overly formal.

─── SYSTEM CONTROL COMMANDS ───
(rest of your existing prompt stays here, unchanged)
"""
```

> Gemma4:e2b is trained on 140+ languages including Telugu — no fine-tuning needed.

---

## 🔊 Step 4 — Replace `modules/voice_output.py`

Completely replace your existing `voice_output.py` with this Piper TTS version:

```python
# modules/voice_output.py — Telugu Piper TTS version

import sounddevice as sd
import numpy as np
import threading
from piper import PiperVoice

VOICE_MODEL = "./piper_voices/te/te_IN/padmavathi/medium/te_IN-padmavathi-medium.onnx"
_voice      = PiperVoice.load(VOICE_MODEL)
SAMPLE_RATE = 22050


def speak(text: str, block: bool = True):
    """Convert Telugu text to speech and play it."""
    if not text or not text.strip():
        return

    # Strip markdown/special symbols before speaking
    clean = (
        text.replace("**", "").replace("*", "").replace("#", "")
            .replace("```", "").replace("`", "")
            .replace("❌", "").replace("✅", "")
    )

    def _play():
        chunks = []
        for chunk in _voice.synthesize_stream_raw(clean):
            chunks.append(np.frombuffer(chunk, dtype=np.int16))
        if chunks:
            audio = np.concatenate(chunks).astype(np.float32) / 32768.0
            sd.play(audio, samplerate=SAMPLE_RATE)
            sd.wait()

    if block:
        _play()
    else:
        threading.Thread(target=_play, daemon=True).start()


if __name__ == "__main__":
    print("🔊 Testing Telugu Piper TTS...")
    speak("నమస్కారం! నేను మీ సహాయకుడిని. మీకు ఎలా సహాయం చేయాలి?", block=True)
    print("✅ Telugu TTS works!")
```


---

## 🧪 Step 5 — Test the TTS Independently

Run the voice output module directly to confirm it works before integrating:

```bash
python modules/voice_output.py
```

Expected output:

```
🔊 Testing Telugu Piper TTS...
✅ Telugu TTS works!
```

You should hear: *"నమస్కారం! నేను మీ సహాయకుడిని. మీకు ఎలా సహాయం చేయాలి?"*

---

## 🚀 Step 6 — Run Your Full Assistant

No other files need to change. Launch your assistant as usual:

```bash
python main.py
```

Whisper will capture your Telugu speech → Gemma4 processes it in Telugu → Piper speaks back in Telugu. ✅

---

## 📁 Final Project File Status

| File | Status | Change |
| :-- | :-- | :-- |
| `config.py` | 🔄 Modified | Added Telugu instruction to SYSTEM_PROMPT |
| `modules/voice_output.py` | 🔄 Replaced | Full Piper TTS Telugu version |
| `modules/voice_input.py` | ✅ Unchanged | Whisper supports Telugu natively |
| `main.py` | ✅ Unchanged | No changes needed |
| `piper_voices/` (new) | ➕ New folder | Holds the `te_IN-padmavathi-medium.onnx` model |


---

## 🌐 Optional — Bilingual Toggle (Telugu + English)

To support both languages with a toggle button in your UI:

```python
# In your UI handler

def set_language(lang: str):
    if lang == "telugu":
        config.SYSTEM_PROMPT = "You are a smart assistant. Always reply in Telugu (తెలుగు).\n" + BASE_PROMPT
    else:
        config.SYSTEM_PROMPT = "You are a smart assistant. Always reply in English.\n" + BASE_PROMPT
```

Add two buttons in your UI: **`🇮🇳 Telugu Mode`** and **`🇬🇧 English Mode`**, calling `set_language("telugu")` or `set_language("english")` on click.

---

> **Voice model size:** ~60MB (one-time download)
> **Offline:** Yes — Piper TTS runs 100% locally, no internet needed after download
> **Model source:** [rhasspy/piper-voices on Hugging Face](https://huggingface.co/rhasspy/piper-voices)

```

***

This complete guide covers all 6 steps end-to-end [file:1]: installing Piper TTS, downloading the `te_IN-padmavathi-medium` voice model (~60MB), updating your `config.py` system prompt, replacing `voice_output.py`, testing TTS independently, and running the full assistant. Only **2 files** need to change in your entire project — everything else including Whisper and `main.py` stays the same [file:1].


<div align="center">⁂</div>

[^1]: what-about-i-need-it-to-speak-and-give-answers-in.md```

