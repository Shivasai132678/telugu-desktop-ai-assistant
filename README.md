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
  </p>
  <br>
</div>

---

## 📖 Overview

**Bujji** is a personal AI assistant that runs entirely on your local machine — no internet, no API keys, no cloud. Inspired by the AI companion from *Kalki 2898 AD*, Bujji understands natural language voice and text commands in **Telugu and English**, executes system actions, and speaks back — all fully offline.

> 🎯 **Why Bujji?** Most voice assistants require cloud connectivity. Bujji is built for privacy, offline reliability, and bilingual (Telugu/English) support — making it ideal for Indian users who prefer native language interaction.

---

## ✨ Features

| Category | Feature | Details |
|----------|---------|---------|
| 🎙️ **Voice Input** | Speech-to-Text | OpenAI Whisper (offline) — `tiny` to `medium` model sizes |
| 🔊 **Voice Output** | Text-to-Speech | Piper TTS / XTTS-v2 with voice cloning support |
| 🧠 **AI Brain** | Local LLM | Gemma4:e2b or Qwen via Ollama — no API key needed |
| 🌐 **Bilingual** | Telugu + English | Auto-detects script, translates English→Telugu |
| 💻 **System Control** | macOS Actions | Volume, brightness, dark mode, Wi-Fi, Bluetooth, DND, apps, files, web search, screenshots, clipboard, power controls |
| 😴 **Wake Word** | "Hey Bujji" | Background listening, activates on trigger |
| 🖥️ **Desktop GUI** | Flask + PyWebView | Clean browser-based chat with voice button |
| 🔌 **API Mode** | OpenAI-compatible | `/v1/chat/completions` endpoint for ecosystem tools |
| 🗣️ **Voice Cloning** | XTTS-v2 | Clone your voice for a personalized Bujji |
| 🔒 **Privacy** | Fully Offline | Zero data leaves your machine |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    BUJJI AI ASSISTANT                         │
│                                                              │
│  ┌──────────────┐   ┌──────────┐   ┌──────────────────────┐  │
│  │ Wake Listener│──►│  Whisper │──►│  Gemma4:e2b (Ollama) │  │
│  │ (background) │   │  (STT)   │   │  (Local LLM)         │  │
│  └──────────────┘   └──────────┘   └──────────┬───────────┘  │
│                                                │              │
│                                                ▼              │
│  ┌────────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ System Control │◄──│ Intent       │◄──│ LLM Response  │    │
│  │ (macOS actions)│   │ Router       │   │ (Telugu/Eng)  │    │
│  └────────────────┘   └──────┬───────┘   └──────────────┘    │
│                              │                                │
│                              ▼                                │
│  ┌───────────────────────────────────────────────┐           │
│  │  Voice Output (Piper TTS / XTTS-v2)           │           │
│  │  OR                                            │           │
│  │  Flask GUI + PyWebView Desktop App             │           │
│  └───────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
```

---

## 🧱 Tech Stack

| Layer | Technology | Why? |
|-------|-----------|------|
| **Speech Recognition** | [OpenAI Whisper](https://github.com/openai/whisper) | Best offline STT; multilingual support |
| **Text-to-Speech** | [Piper TTS](https://github.com/rhasspy/piper) / [XTTS-v2](https://github.com/coqui-ai/TTS) | Fast local TTS + voice cloning |
| **Language Model** | [Gemma4:e2b](https://ollama.com/library/gemma4) via [Ollama](https://ollama.com) | Lightweight, runs on M1 8GB RAM |
| **Intent Routing** | Custom Python (regex + dispatch) | Simple, fast, extensible |
| **System Control** | macOS `osascript` + shell | Native AppleScript integration |
| **Desktop GUI** | [Flask](https://flask.palletsprojects.com/) + [PyWebView](https://pywebview.flowrl.com/) | Lightweight, no Electron bloat |
| **API Server** | FastAPI + Uvicorn | Async, OpenAI-compatible |
| **Translation** | `indic-transliteration` | English → Telugu transliteration |

---

## 🚀 Quick Start

### Prerequisites

- macOS (M1/Intel)
- [Homebrew](https://brew.sh)
- [Ollama](https://ollama.com)
- Python 3.10+

### 1. Install System Dependencies

```bash
brew install portaudio brightness
```

### 2. Setup Ollama

```bash
brew install ollama
ollama serve           # Start server (keep this terminal open)
ollama pull gemma4:e2b # Download model (~3-5 GB)
```

### 3. Setup Bujji

```bash
git clone https://github.com/Shivasai132678/telugu-desktop-ai-assistant.git
cd telugu-desktop-ai-assistant

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run Bujji

```bash
# Voice mode (needs microphone)
python main.py

# Text-only mode (no mic needed)
python main.py --cli

# API server mode
python main.py --api --port 8000
```

---

## 📖 Usage Modes

### 🎙️ Voice Mode (Default)
```bash
python main.py
```
1. Bujji starts listening for **"Hey Bujji"** in the background
2. Say the wake word → Bujji wakes up "Yes, I'm here!"
3. Speak your command in Telugu or English
4. Bujji executes the action or replies conversationally
5. Say *"goodbye"*, *"sleep"*, or *"bye"* to put Bujji back to sleep

### ⌨️ CLI Mode
```bash
python main.py --cli
```
Text-based interaction — no microphone required. Great for testing.

### 🌐 API Mode
```bash
python main.py --api --host 0.0.0.0 --port 8000
```
OpenAI-compatible API for integration with other tools:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what time is it?"}'
```

---

## 📁 Project Structure

```
telugu-desktop-ai-assistant/
├── main.py                 ← Entry point (voice, CLI, or API mode)
├── config.py               ← Central configuration (wake word, model, TTS, etc.)
├── api_server.py           ← FastAPI server with /v1/chat/completions endpoint
├── gui.py                  ← PyWebView desktop GUI
├── requirements.txt        ← Python dependencies
├── check_permissions.py   ← Mic and system permissions checker
├── GUIDE.md                ← Detailed module reference & troubleshooting
├── telugu.md               ← Telugu language support documentation
├── xtts_v2_voice_cloning_bujji.md ← Voice cloning setup guide
├── wake up.md              ← Wake word configuration notes
│
├── modules/
│   ├── wake_listener.py    ← Background wake word detection ("Hey Bujji")
│   ├── voice_input.py      ← Audio capture + Whisper transcription
│   ├── voice_output.py     ← Text-to-speech engine
│   ├── llm_engine.py       ← Ollama/Gemma4:e2b interface with conversation memory
│   ├── intent_router.py    ← Parses LLM output → system action or speech
│   ├── system_control.py   ← macOS volume, brightness, apps, web, etc.
│   └── translator.py       ← English → Telugu transliteration
│
├── assets/                 ← Static files (icons, sounds, etc.)
├── robot-pet/              ← Electron-based animated robot pet companion
└── tests/                  ← Test suite
```

---

## ⚙️ Configuration

All settings live in `config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `gemma4:e2b` | Ollama model |
| `WAKE_WORD` | `hey bujji` | Wake phrase |
| `RECOGNITION_MODE` | `google` | `google` or `sphinx` |
| `WHISPER_MODEL_SIZE` | `base` | `tiny`/`base`/`small`/`medium` |
| `COMMAND_RECORD_SECONDS` | `7` | Max listen duration |
| `SPEECH_RATE` | `165` | TTS words per minute |
| `MAX_HISTORY_TURNS` | `10` | Conversation memory depth |

---

## 🧪 Testing

Each module is independently testable:

```bash
python -m modules.wake_listener     # Test wake word detection
python -m modules.voice_input       # Record + transcribe your voice
python -m modules.voice_output      # Hear Bujji speak
python -m modules.llm_engine        # Chat with Gemma4:e2b
python -m modules.system_control    # Test all system controls
python -m modules.intent_router     # Test routing logic
```

---

## 🗣️ Voice Cloning with XTTS-v2

Bujji supports voice cloning via XTTS-v2 — make Bujji sound like you (or anyone).

See [`xtts_v2_voice_cloning_bujji.md`](xtts_v2_voice_cloning_bujji.md) for full setup guide.

---

## 🔧 Extending Bujji

### Add a new system action (e.g., "play music")

1. **Add handler in `modules/system_control.py`:**
   ```python
   def play_music(query: str) -> str:
       _run_shell("open -a Music")
       return "Opening Music."
   ```
2. **Register in `dispatch()`:**
   ```python
   "PLAY_MUSIC": lambda a: play_music(a),
   ```
3. **Update `SYSTEM_PROMPT` in `config.py`:**
   ```
   SYSTEM_ACTION:PLAY_MUSIC:<song>
   ```

No changes needed in `intent_router.py` or `main.py` — the router picks it up automatically.

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| ❌ `ConnectionError` | Run `ollama serve` in a separate terminal |
| ❌ `gemma4:e2b not found` | Run `ollama pull gemma4:e2b` |
| ❌ Mic not working | Grant mic access: System Preferences → Privacy → Microphone |
| ❌ Whisper is slow | Set `WHISPER_MODEL_SIZE = "tiny"` in `config.py` |
| ❌ Brightness not changing | `brew install brightness` |
| ❌ Wake word never triggers | Switch `RECOGNITION_MODE = "google"` in `config.py` |

> For **detailed troubleshooting**, module references, and code examples, see [`GUIDE.md`](GUIDE.md).

---

## 🗺️ Roadmap

- [ ] **Windows/Linux support** — cross-platform TTS + system control
- [ ] **Custom wake word training** — train on your own trigger phrase
- [ ] **Plugin system** — community-contributed actions
- [ ] **RAG memory** — long-term recall across sessions
- [ ] **WebSocket GUI** — real-time browser UI
- [ ] **Multi-model routing** — switch between Gemma, Qwen, Llama

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve Bujji:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- [Kalki 2898 AD](https://en.wikipedia.org/wiki/Kalki_2898_AD) for the Bujji inspiration
- [Ollama](https://ollama.com) for making local LLMs easy
- [OpenAI Whisper](https://github.com/openai/whisper) for offline speech recognition
- [Piper TTS](https://github.com/rhasspy/piper) for fast local TTS

---

<div align="center">
  <p>
    <strong>Built with ❤️ for Telugu speakers everywhere</strong>
    <br>
    <sub>Shivasai132678 · 2026</sub>
  </p>
</div>
