<div align="center">
  <br>
  <h1>🤖 Bujji — Telugu Desktop AI Assistant</h1>
  <p>
    <strong>Your offline, bilingual, voice-activated personal AI assistant for macOS</strong>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/LLM-Gemma4:e2b-FF6F00?logo=google" alt="Gemma4:e2b">
    <img src="https://img.shields.io/badge/TTS-Piper%20%7C%20XTTS--v2-brightgreen" alt="TTS">
    <img src="https://img.shields.io/badge/STT-Whisper%20(offline)-yellow" alt="Whisper STT">
    <img src="https://img.shields.io/badge/platform-macOS-lightgrey?logo=apple" alt="macOS">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
    <img src="https://img.shields.io/github/last-commit/Shivasai132678/telugu-desktop-ai-assistant" alt="Last Commit">
  </p>
  <br>
  <p>
    <a href="#-overview">Overview</a> •
    <a href="#-features">Features</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-usage-modes">Usage</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-api-reference">API</a> •
    <a href="#-faq">FAQ</a>
  </p>
  <br>
</div>

---

https://github.com/user-attachments/assets/b6b22d6d-89f0-4fdb-99e5-0b7fa38f6d21

---

## 📖 Overview

**Bujji** is a personal AI assistant that runs entirely on your local machine — **no internet, no API keys, no cloud**. Inspired by the AI companion from *Kalki 2898 AD*, Bujji understands natural language voice and text commands in **Telugu and English**, executes system actions, and speaks back — all fully offline.

> 🎯 **Why Bujji?** Most voice assistants (Alexa, Siri, Google Assistant) require cloud connectivity and don't support Telugu natively. Bujji is built for **privacy, offline reliability, and bilingual (Telugu/English) support** — making it ideal for Indian users who prefer native language interaction.

### 🌟 Key Differentiators

| vs. | Siri / Alexa | Google Assistant | Bujji |
|-----|-------------|-----------------|-------|
| **Offline** | ❌ Requires cloud | ❌ Requires cloud | ✅ Fully local |
| **Telugu Support** | ❌ None | ❌ Limited | ✅ Full bilingual |
| **System Control** | ❌ Limited | ❌ Limited | ✅ Full macOS |
| **Privacy** | ❌ Data sent to cloud | ❌ Data sent to cloud | ✅ 100% offline |
| **Customizable** | ❌ Closed | ❌ Closed | ✅ Open source |
| **Cost** | 💰 Free (with data) | 💰 Free (with data) | 🆓 Completely free |

---

## ✨ Features

### 🎙️ Voice & Speech
| Feature | Technology | Details |
|---------|-----------|---------|
| Speech-to-Text | OpenAI Whisper | Offline STT with `tiny`/`base`/`small`/`medium` models |
| Text-to-Speech | Piper TTS | Fast, natural-sounding local TTS |
| Voice Cloning | XTTS-v2 | Clone any voice for a personalized Bujji |
| Wake Word | Custom detector | "Hey Bujji" — stays silent until triggered |
| Bilingual | Telugu + English | Auto-detects input language, speaks both |

### 🧠 AI & Intelligence
| Feature | Technology | Details |
|---------|-----------|---------|
| Language Model | Gemma4:e2b / Qwen | Via Ollama — no API key, no cloud |
| Intent Routing | Custom parser | Regex + dispatch engine for system actions |
| Conversation Memory | 10-turn history | Maintains context across exchanges |
| English→Telugu | indic-transliteration | Translates LLM output to Telugu |

### 💻 System Control (macOS)
| Category | Actions |
|----------|--------|
| **Audio** | Volume up/down, set level, mute/unmute |
| **Display** | Brightness up/down, set level |
| **Appearance** | Dark mode on/off/toggle |
| **Network** | Wi-Fi on/off/status, Bluetooth on/off |
| **Focus** | Do Not Disturb on/off |
| **Power** | Sleep, sleep display, restart, shutdown, lock |
| **Applications** | Open/quit any app by name |
| **Files** | Open folder (Downloads, Desktop, etc.), empty trash |
| **Web** | Open websites, Google search, YouTube search |
| **Info** | Current time, battery status, take screenshot |
| **Clipboard** | Get/set clipboard contents |

### 🖥️ Interface Options
- **Desktop GUI** — Flask + PyWebView clean browser-based chat
- **CLI Mode** — Text-only interaction (no mic needed)
- **API Mode** — OpenAI-compatible REST API
- **Robot Pet** — Electron-based animated companion

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     BUJJI AI ASSISTANT                           │
│                                                                  │
│  ┌─────────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │  Wake Listener   │────►│   Whisper    │────►│   Ollama     │  │
│  │  (background     │     │   (STT)      │     │  Gemma4:e2b  │  │
│  │   thread)        │     │   offline    │     │  (local LLM) │  │
│  └─────────────────┘     └──────────────┘     └──────┬───────┘  │
│                                                       │          │
│                                                       ▼          │
│  ┌─────────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │  System Control  │◄────│   Intent     │◄────│  LLM Response│  │
│  │  (macOS actions) │     │   Router     │     │  (Telugu/En) │  │
│  └─────────────────┘     └──────┬───────┘     └──────────────┘  │
│                                  │                               │
│  ┌─────────────────┐            ▼                               │
│  │  Piper TTS /     │    ┌──────────────┐                       │
│  │  XTTS-v2         │    │  Translator  │                       │
│  │  (Voice Output)  │    │  EN→Telugu  │                       │
│  └─────────────────┘    └──────────────┘                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Interface Layer: Flask GUI · PyWebView · CLI · API     │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow (Voice Mode)
```
1. [Background] Wake listener hears "Hey Bujji"
       │
2.     ▼  Bujji speaks: "Yes, I'm here!"
       │
3.     ▼  Records audio (up to 7s, auto-stop on silence)
       │
4.     ▼  Whisper transcribes speech → text
       │
5.     ▼  Sends text to Gemma4:e2b via Ollama
       │
6.     ▼  LLM responds (Telugu or SYSTEM_ACTION tag)
       │
7.     ▼  Intent Router parses response:
       │
       ├── SYSTEM_ACTION → dispatch to system_control.py
       │     (volume, brightness, apps, web, etc.)
       │
       └── Conversation → translate to Telugu → speak via TTS
       │
8.     ▼  Returns to listening state
```

---

## 🧱 Tech Stack

| Layer | Technology | Version | Why this? |
|-------|-----------|---------|-----------|
| **Language** | Python | 3.10+ | Best ML ecosystem, fast prototyping |
| **Speech-to-Text** | [OpenAI Whisper](https://github.com/openai/whisper) | `base` | Best offline STT; Telugu support |
| **Text-to-Speech** | [Piper TTS](https://github.com/rhasspy/piper) | Latest | Fast, local, no GPU needed |
| **Voice Cloning** | [XTTS-v2](https://github.com/coqui-ai/TTS) | v2 | High-quality voice cloning |
| **LLM Runtime** | [Ollama](https://ollama.com) | Latest | Easiest local LLM runner |
| **Language Model** | [Gemma4:e2b](https://ollama.com/library/gemma4) | 4 | Lightweight, runs on M1 8GB |
| **Web Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Latest | Async, auto-docs, OpenAI compat |
| **Desktop UI** | [PyWebView](https://pywebview.flowrl.com/) | Latest | Native webview, no Electron |
| **Translation** | [indic-transliteration](https://github.com/indic-transliteration/indic_transliteration) | Latest | Telugu script conversion |
| **Audio** | sounddevice / pyaudio | Latest | Cross-platform mic access |
| **System Control** | macOS `osascript` | Native | AppleScript for macOS automation |

---

## 🚀 Quick Start

### 📋 Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|--------------|
| macOS | Monterey+ (M1/Intel) | `sw_vers` |
| Homebrew | Latest | `brew --version` |
| Python | 3.10+ | `python3 --version` |
| Ollama | Latest | `ollama --version` |
| Git | Latest | `git --version` |

### Step 1: Install System Dependencies

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required system packages
brew install portaudio brightness
```

### Step 2: Install & Setup Ollama

```bash
# Install Ollama
brew install ollama

# Start Ollama server (keep this terminal open!)
ollama serve
```

> ⚠️ **Important:** `ollama serve` must be running in a terminal tab **before** starting Bujji.

### Step 3: Download the LLM Model

```bash
# In a new terminal tab, pull the model
ollama pull gemma4:e2b

# Verify it's downloaded
ollama list
```

> ⏱️ **First-time download:** ~3-5 GB. Takes 5-15 minutes depending on your internet.

### Step 4: Clone & Setup Bujji

```bash
git clone https://github.com/Shivasai132678/telugu-desktop-ai-assistant.git
cd telugu-desktop-ai-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (~2-5 minutes)
pip install -r requirements.txt
```

### Step 5: Grant Microphone Permission

Go to **System Settings → Privacy & Security → Microphone** and enable:
- ✅ Terminal (or your IDE)
- ✅ Your browser (for GUI mode)

### Step 6: Run Bujji 🎉

```bash
# 🎙️ Voice mode (needs microphone)
python main.py

# OR ⌨️ Text-only mode (no mic)
python main.py --cli

# OR 🌐 API server mode
python main.py --api --port 8000
```

### ✅ First-Run Checklist

- [ ] Ollama is running (`ollama serve`)
- [ ] Model downloaded (`ollama list` shows `gemma4:e2b`)
- [ ] Virtual env activated (`source venv/bin/activate`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Microphone permissions granted
- [ ] `brew install portaudio brightness` completed

---

## 📖 Usage Modes

### 🎙️ Voice Mode (Default)

```bash
python main.py
```

**Interaction Flow:**
1. Bujji calibrates microphone and starts background listening
2. Say **"Hey Bujji"** — wakes up and says "Yes, I'm here!"
3. Speak your command in **Telugu or English**
4. Bujji processes and responds (action or conversation)
5. Say *"goodbye"*, *"sleep"*, or *"bye"* to put Bujji back to sleep

**Example Commands:**
```
"Hey Bujji"
→ "Yes, I'm here!"

"turn up the volume"
→ 🔉 Volume increased

"What's the time?"
→ 🕐 "It's 3:45 PM"

"open Spotify"
→ 🎵 Spotify launched

"take a screenshot"
→ 📸 Screenshot saved to Desktop

"search for Python tutorials"
→ 🌐 Opens Google search

"set brightness to 50"
→ 💡 Brightness adjusted

"what's my battery status"
→ 🔋 Battery at 85%
```

### ⌨️ CLI Mode (No Microphone)

```bash
python main.py --cli
```

Great for testing without audio hardware or for quick interactions:

```
╔══════════════════════════════════════════════╗
║     🤖 Bujji — CLI Text Mode                ║
║     Type 'quit' to exit, 'reset' for fresh   ║
╚══════════════════════════════════════════════╝

You → what time is it?
🧠 Thinking…
📝 Telugu: ప్రస్తుతం సమయం 3:45 PM

You → open chrome
🧠 Thinking…
✅ [SYSTEM] Chrome opened

You → quit
Goodbye!
```

Available CLI commands:
| Command | Action |
|---------|--------|
| `quit`, `exit`, `q` | Exit CLI mode |
| `reset` | Clear conversation history |

### 🌐 API Mode (For Developers)

```bash
python main.py --api --host 0.0.0.0 --port 8000
```

OpenAI-compatible `/v1/chat/completions` endpoint — use with any OpenAI client:

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # Bujji doesn't need an API key
)

response = client.chat.completions.create(
    model="gemma4:e2b",
    messages=[{"role": "user", "content": "what time is it?"}]
)

print(response.choices[0].message.content)
```

---

## 📁 Project Structure

```
telugu-desktop-ai-assistant/
│
├── main.py                 ← Entry point (voice / CLI / API modes)
├── config.py               ← Central config (wake word, model, TTS...)
├── api_server.py           ← FastAPI /v1/chat/completions server
├── gui.py                  ← PyWebView desktop GUI
├── requirements.txt        ← Python dependencies
├── check_permissions.py    ← Mic & system permissions checker
│
├── GUIDE.md                ← Detailed module reference & troubleshooting
├── telugu.md               ← Telugu language support docs
├── xtts_v2_voice_cloning_bujji.md  ← Voice cloning setup guide
├── wake\ up.md             ← Wake word configuration notes
│
├── modules/
│   ├── __init__.py
│   ├── wake_listener.py    ← "Hey Bujji" detection (background thread)
│   ├── voice_input.py      ← Audio capture → Whisper transcription
│   ├── voice_output.py     ← Text-to-Speech engine (Piper/pyttsx3)
│   ├── llm_engine.py       ← Ollama client + conversation memory
│   ├── intent_router.py    ← Parses LLM → system action or speech
│   ├── system_control.py   ← macOS automation (volume, apps, web...)
│   └── translator.py       ← English → Telugu transliteration
│
├── assets/                 ← Static files (icons, sounds, images)
├── robot-pet/              ← Electron animated robot companion
└── tests/                  ← Test suite
```

---

## ⚙️ Configuration

All settings live in [`config.py`](config.py). Edit this file to customize Bujji.

### Core Settings

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `MODEL_NAME` | `gemma4:e2b` | Ollama model | Any Ollama model |
| `OLLAMA_URL` | `http://localhost:11434/api/chat` | Ollama endpoint | — |
| `WAKE_WORD` | `hey bujji` | Wake phrase | Any phrase |
| `WAKE_CONFIRMATION` | `Yes, I'm here!` | Wake response | Any text |

### Speech & Audio

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `RECOGNITION_MODE` | `google` | STT backend | `google`, `sphinx` |
| `WHISPER_MODEL_SIZE` | `base` | Whisper model size | `tiny`, `base`, `small`, `medium` |
| `COMMAND_RECORD_SECONDS` | `7` | Max recording time | 3–15 |
| `SPEECH_RATE` | `165` | TTS speed (wpm) | 100–250 |
| `SPEECH_VOLUME` | `0.95` | TTS volume | 0.0–1.0 |

### System Control

| Variable | Default | Description |
|----------|---------|-------------|
| `VOLUME_STEP` | `10` | % per volume up/down |
| `BRIGHTNESS_STEP` | `10` | % per brightness up/down |
| `SCREENSHOT_DIR` | `~/Desktop` | Screenshot save location |
| `MAX_HISTORY_TURNS` | `10` | Conversation memory depth |

### 🔧 Performance Tuning

| If Bujji feels... | Change this | Effect |
|------------------|-------------|--------|
| 🐢 Slow transcription | `WHISPER_MODEL_SIZE = "tiny"` | Faster STT, slightly less accurate |
| 🐢 Slow responses | Use `qwen:0.5b` instead of `gemma4:e2b` | Faster but dumber |
| 🐢 Too chatty | `MAX_HISTORY_TURNS = 3` | Less context, faster responses |
| 🔊 Too loud/quiet | `SPEECH_VOLUME = 0.8` | Adjust TTS output level |

---

## 🔌 API Reference

When running in API mode, Bujji exposes these endpoints:

### Health Check
```bash
GET /health
```
```json
{ "status": "ok", "model": "gemma4:e2b" }
```

### Chat Completion (OpenAI Compatible)
```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "gemma4:e2b",
  "messages": [
    {"role": "user", "content": "what time is it?"}
  ]
}
```
```json
{
  "id": "chatcmpl-bujji-123",
  "object": "chat.completion",
  "created": 1712345678,
  "model": "gemma4:e2b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "సమయం 3:45 PM"
      }
    }
  ]
}
```

### Wake Endpoint
```bash
GET /wake
```
Triggers wake confirmation — useful for testing.

---

## 🧪 Testing

### Per-Module Testing

Each module is independently testable — perfect for debugging:

```bash
# Test wake word detection
python -m modules.wake_listener
# → Say "Hey Bujji" to test detection

# Test voice recording & transcription
python -m modules.voice_input
# → Records 7s and transcribes with Whisper

# Test text-to-speech
python -m modules.voice_output
# → Bujji speaks three test phrases

# Test LLM interaction
python -m modules.llm_engine
# → Opens interactive chat with Gemma4:e2b

# Test all system controls
python -m modules.system_control
# → Interactive menu: volume, brightness, apps, etc.

# Test intent routing logic
python -m modules.intent_router
# → Runs 19 test cases through the router
```

### Quick API Test
```bash
# With API mode running
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what time is it?"}'
```

---

## 🗣️ Voice Cloning with XTTS-v2

Bujji supports **voice cloning** via Coqui XTTS-v2 — make Bujji sound like you, a friend, or any voice you have a recording of.

### Quick Overview
1. Install XTTS-v2 dependencies
2. Provide a 10-30 second audio sample
3. Run the voice cloning script
4. Bujji now speaks in the cloned voice!

📄 See **[`xtts_v2_voice_cloning_bujji.md`](xtts_v2_voice_cloning_bujji.md)** for the complete setup guide.

---

## 🔧 Extending Bujji

### ➕ Add a New System Action

Want to add a "play music" command? Here's all you need:

**Step 1:** Add handler in `modules/system_control.py`:
```python
def play_music(query: str) -> str:
    """Open Apple Music and play a track."""
    _run_shell("open -a Music")
    return "Opening Music. పాట ప్రారంభించాను."
```

**Step 2:** Register in `dispatch()`:
```python
"PLAY_MUSIC": lambda a: play_music(a),
```

**Step 3:** Update `SYSTEM_PROMPT` in `config.py`:
```
SYSTEM_ACTION:PLAY_MUSIC:<song or genre>
```

**That's it!** The intent router automatically picks up new actions — no changes needed in `intent_router.py` or `main.py`.

### 🧠 Use a Different LLM

```python
# In config.py, change:
MODEL_NAME = "qwen:0.5b"    # Faster, less capable
MODEL_NAME = "llama3.2:3b"  # Balanced
MODEL_NAME = "gemma4:e2b"   # Default, best quality
```

Just make sure the model is pulled: `ollama pull <model-name>`

### 🔤 Change the Wake Word

```python
# In config.py:
WAKE_WORD = "hey computer"
```

### 💾 Add Persistent Memory

In `modules/llm_engine.py`, add:
```python
import json

def _save_history():
    with open("history.json", "w") as f:
        json.dump(_conversation_history, f)

def _load_history():
    try:
        with open("history.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
```

---

## 🩺 Troubleshooting

### Common Issues

| 🚫 Problem | ✅ Solution |
|-----------|-----------|
| `ConnectionError` / Ollama not reachable | Run `ollama serve` in a separate terminal **before** starting Bujji |
| `gemma4:e2b not found` | Run `ollama pull gemma4:e2b` (first-time download ~3-5 GB) |
| Microphone not working | Grant mic access: **System Settings → Privacy → Microphone → enable Terminal** |
| Whisper too slow | Set `WHISPER_MODEL_SIZE = "tiny"` in config.py — much faster, still usable |
| Brightness not changing | Run `brew install brightness` — Bujji still works for other commands |
| Wake word never triggers | Switch `RECOGNITION_MODE = "google"` in config.py (requires internet but more accurate) |
| TTS no sound | Check macOS audio output; run `python -m modules.voice_output` to test |
| `ModuleNotFoundError: pyaudio` | Run `brew install portaudio && pip install pyaudio` |
| Bujji speaks English instead of Telugu | The translator translates after LLM responds — if LLM replies in English, it gets translated |

### 🔍 Diagnostic Commands

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check if model is downloaded
ollama list

# Test system control module
python -m modules.system_control

# Check microphone permissions
python check_permissions.py
```

### 📊 System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **RAM** | 8 GB | 16 GB |
| **Storage** | 5 GB free | 10 GB free |
| **CPU** | Intel Core i5 | Apple Silicon (M1+) |
| **OS** | macOS Monterey | macOS Sonoma+ |
| **Microphone** | Built-in | Any USB/Bluetooth mic |

---

## 📸 Screenshots

<!-- TODO: Add screenshots of Bujji in action -->
<!--
![Voice Mode Demo](assets/screenshots/voice-mode.png)
![CLI Mode](assets/screenshots/cli-mode.png)
![GUI Interface](assets/screenshots/gui.png)
![Robot Pet Companion](assets/screenshots/robot-pet.png)
-->

> 💡 **Contributors welcome!** If you've set up Bujji, consider taking a screenshot and submitting it via PR.

---

## 🗺️ Roadmap

### 📋 Planned Features

- [ ] **🐧 Windows/Linux support** — Cross-platform TTS + system control
- [ ] **🎯 Custom wake word training** — Train on your own trigger phrase
- [ ] **🧩 Plugin system** — Community-contributed action modules
- [ ] **🧠 RAG memory** — Long-term recall across sessions (vector DB)
- [ ] **🌐 WebSocket GUI** — Real-time browser UI with streaming responses
- [ ] **🔄 Multi-model routing** — Switch between Gemma, Qwen, Llama based on task
- [ ] **📊 Analytics dashboard** — Usage stats, token counts, command history
- [ ] **📱 Mobile companion** — Simple iOS/Android remote control

### ✅ Completed

- [x] Voice mode with wake word
- [x] Telugu + English bilingual support
- [x] macOS system control (volume, brightness, apps, web)
- [x] OpenAI-compatible API mode
- [x] Voice cloning via XTTS-v2
- [x] Desktop GUI with PyWebView
- [x] CLI text-only mode
- [x] Robot pet companion

---

## 🤝 Contributing

Contributions are **welcome and appreciated!** Here's how you can help:

### 🐛 Report a Bug
Open an [issue](https://github.com/Shivasai132678/telugu-desktop-ai-assistant/issues) with:
- Bujji version / commit hash
- macOS version
- Steps to reproduce
- Expected vs actual behavior

### 💡 Suggest a Feature
Open an [issue](https://github.com/Shivasai132678/telugu-desktop-ai-assistant/issues) with:
- Clear description of the feature
- Why it would be useful
- Any implementation ideas

### 🛠️ Submit a PR
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a [Pull Request](https://github.com/Shivasai132678/telugu-desktop-ai-assistant/pulls)

**Guidelines:**
- Keep code clean and documented
- Add type hints to Python code
- Test your changes
- Update docs if needed

---

## 📄 License

This project is licensed under the **MIT License** — you're free to use, modify, and distribute it. See the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 Shivasai132678

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 🙏 Acknowledgments

- 🎬 **[Kalki 2898 AD](https://en.wikipedia.org/wiki/Kalki_2898_AD)** — For the Bujji character inspiration
- 🦙 **[Ollama](https://ollama.com)** — Making local LLMs accessible to everyone
- 🧠 **[Google Gemma](https://ollama.com/library/gemma4)** — The Gemma4:e2b model powering Bujji's brain
- 🎙️ **[OpenAI Whisper](https://github.com/openai/whisper)** — State-of-the-art offline STT
- 🔊 **[Piper TTS](https://github.com/rhasspy/piper)** — Fast, local text-to-speech
- 🗣️ **[Coqui XTTS](https://github.com/coqui-ai/TTS)** — Voice cloning capabilities
- ⚡ **[FastAPI](https://fastapi.tiangolo.com)** — Async web framework for the API
- 🖥️ **[PyWebView](https://pywebview.flowrl.com)** — Lightweight desktop GUI

### ⭐ Support

If you find Bujji useful, consider:
- ⭐ **Starring** the repo on GitHub
- 🐛 **Reporting** issues you find
- 🔀 **Contributing** via pull requests
- 📢 **Sharing** with friends who might find it useful

---

<div align="center">
  <br>
  <p>
    <strong>Built with ❤️ for Telugu speakers everywhere</strong>
    <br>
    <sub>Shivasai132678 · 2026</sub>
  </p>
  <br>
  <p>
    <a href="https://github.com/Shivasai132678/telugu-desktop-ai-assistant/issues">Report Bug</a>
    •
    <a href="https://github.com/Shivasai132678/telugu-desktop-ai-assistant/issues">Request Feature</a>
    •
    <a href="https://github.com/Shivasai132678/telugu-desktop-ai-assistant/discussions">Discussion</a>
  </p>
  <br>
  <p>
    <sub>Made in India 🇮🇳</sub>
  </p>
  <br>
</div>
