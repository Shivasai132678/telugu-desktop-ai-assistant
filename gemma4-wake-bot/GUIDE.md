# 🤖 Bujji AI Assistant — Complete Guide

> **Bujji** is a fully modular, locally-running AI voice assistant powered by **Gemma4:e2b** via Ollama.
> She wakes up when you say **"Hey Bujji"**, understands your commands, controls your Mac, and chats back — all offline.

---

## 📁 Project Structure

```
gemma4-wake-bot/
│
├── config.py                  ← Central configuration (wake word, model, TTS, etc.)
├── main.py                    ← Orchestrator — runs the full assistant
├── requirements.txt           ← All Python dependencies
│
├── modules/
│   ├── __init__.py
│   ├── wake_listener.py       ← Detects "Hey Bujji" in the background
│   ├── voice_input.py         ← Records audio + transcribes with Whisper
│   ├── voice_output.py        ← Text-to-Speech (Bujji's voice)
│   ├── llm_engine.py          ← Talks to Gemma4:e2b via Ollama
│   ├── system_control.py      ← Controls volume, brightness, apps, browser, etc.
│   └── intent_router.py       ← Parses LLM response and routes to correct handler
│
└── GUIDE.md                   ← This file
```

---

## ⚙️ One-Time Setup

### 1. Install System Tools

```bash
# macOS: install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Brightness control CLI (used by system_control.py)
brew install brightness

# PortAudio — required by pyaudio for microphone access
brew install portaudio
```

### 2. Install Ollama + Pull Gemma4:e2b

```bash
# Install Ollama
brew install ollama

# Start the Ollama server (keep this running in a terminal tab)
ollama serve

# Pull the Gemma4 e2b model (first-time only, ~3-5 GB download)
ollama pull gemma4:e2b

# Verify model is available
ollama list
```

### 3. Create & Activate Virtual Environment

```bash
cd "/Users/kmsreenidhi/wake up"

python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
cd gemma4-wake-bot
pip install -r requirements.txt
```

> **macOS microphone permissions**: Go to  
> `System Preferences → Security & Privacy → Privacy → Microphone`  
> and allow Terminal (or your IDE) to access the microphone.

---

## 📄 Module Reference

Each module is independently runnable with `python -m modules.<module_name>` or `python modules/<module_name>.py`.

---

### `config.py` — Central Configuration

> **Purpose**: Single source of truth for all settings. Every module imports from here.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434/api/chat` | Ollama API endpoint |
| `MODEL_NAME` | `gemma4:e2b` | LLM model to use |
| `WAKE_WORD` | `hey bujji` | Phrase that wakes the assistant |
| `WAKE_CONFIRMATION` | `Yes, I'm here!` | Spoken when woken |
| `RECOGNITION_MODE` | `google` | `google` (internet) or `sphinx` (offline) |
| `COMMAND_RECORD_SECONDS` | `7` | Max seconds to capture a command |
| `WHISPER_MODEL_SIZE` | `base` | Whisper model: `tiny`, `base`, `small`, `medium` |
| `SPEECH_RATE` | `165` | TTS speed (words/min) |
| `SPEECH_VOLUME` | `0.95` | TTS volume (0.0–1.0) |
| `VOLUME_STEP` | `10` | % change per volume up/down command |
| `BRIGHTNESS_STEP` | `10` | % change per brightness up/down command |
| `SCREENSHOT_DIR` | `~/Desktop` | Where screenshots are saved |
| `MAX_HISTORY_TURNS` | `10` | Max conversation turns to remember |

**Edit this file to customise Bujji's persona, wake word, or model settings.**

---

### `modules/wake_listener.py` — Wake Word Detection

> **Purpose**: Continuously listens to the microphone in the background and fires when it hears "Hey Bujji".

**Standalone test:**
```bash
python -m modules.wake_listener
# or
python modules/wake_listener.py
```

**Key functions:**

| Function | Description |
|---|---|
| `listen_for_wake_word()` | Blocks indefinitely until wake word is heard. Returns `True`. |
| `listen_for_wake_word_once(timeout=10)` | Listens for up to `timeout` seconds. Returns `True`/`False`. |

**How it works:**
1. Opens microphone with `SpeechRecognition`
2. Calibrates to background noise (1 second)
3. Loops: captures short audio snippets → recognises text → checks for wake word
4. When the recognised text exactly matches `WAKE_WORD` after normalisation → returns `True`

**Switch recognition mode in `config.py`:**
- `"google"` — internet required, more accurate
- `"sphinx"` — fully offline, needs `pocketsphinx` installed

---

### `modules/voice_input.py` — Voice Command Capture

> **Purpose**: Records the user's command after the wake word is detected, then transcribes it using OpenAI Whisper.

**Standalone test:**
```bash
python -m modules.voice_input
```
(Tests both fixed-duration capture and auto-stop-on-silence capture)

**Key functions:**

| Function | Description |
|---|---|
| `capture_command(seconds=7)` | Records exactly N seconds of audio, returns transcribed text. |
| `listen_once(max_seconds=10)` | Listens until silence detected (SpeechRecognition + Whisper), returns text. |

**How it works:**
1. Records audio via `sounddevice` (or `SpeechRecognition` for `listen_once`)
2. Writes audio to a temporary WAV file
3. Passes WAV to `whisper.transcribe()`
4. Returns the transcription string, cleans up temp file

**Change Whisper model size in `config.py`** (`WHISPER_MODEL_SIZE`):
- `tiny` — fastest, lowest accuracy (~75 MB)
- `base` — good balance (default, ~150 MB)
- `small` — better accuracy (~450 MB)
- `medium` — near-human accuracy (~1.5 GB)

---

### `modules/voice_output.py` — Text-to-Speech (Bujji's Voice)

> **Purpose**: Converts text into speech using `pyttsx3` — Bujji talks back to you.

**Standalone test:**
```bash
python -m modules.voice_output
```
(Lists available voices, then speaks three intro phrases as Bujji)

**Key functions:**

| Function | Description |
|---|---|
| `speak(text)` | Speaks the given text. Blocks until finished. Strips markdown automatically. |
| `set_voice_properties(rate, volume)` | Change TTS speed/volume at runtime. |
| `list_available_voices()` | Returns list of `(id, name)` tuples for installed voices. |

**macOS voice tip:** Bujji prefers `Samantha` → `Alex` → `Victoria` → `Karen`.  
To add better voices: `System Preferences → Accessibility → Spoken Content → System Voice → Manage Voices`.

---

### `modules/llm_engine.py` — Gemma4:e2b Brain

> **Purpose**: All communication with Gemma4:e2b via Ollama. Manages multi-turn conversation memory.

**Standalone test — interactive CLI chat:**
```bash
python -m modules.llm_engine
```
(Opens a terminal chat loop with Bujji. Type `reset` to clear history, `quit` to exit.)

**Key functions:**

| Function | Description |
|---|---|
| `check_ollama_health()` | Checks if Ollama is running and `gemma4:e2b` is available. Returns `bool`. |
| `chat(message, remember=True)` | Sends message to LLM, returns full response string. |
| `stream_chat(message, on_token=None)` | Streams tokens; calls `on_token(token)` for each chunk. |
| `reset_history()` | Clears conversation memory (fresh start). |
| `get_history()` | Returns a copy of the current conversation history list. |

**How conversation memory works:**
- Each `chat()` / `stream_chat()` call appends `{role: user}` + `{role: assistant}` to `_conversation_history`
- History is trimmed to `MAX_HISTORY_TURNS * 2` messages
- The `SYSTEM_PROMPT` from `config.py` is always prepended
- Call `reset_history()` to start a new conversation

**Ollama API format used:**
```json
{
  "model": "gemma4:e2b",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user",   "content": "..."}
  ],
  "stream": false
}
```

---

### `modules/system_control.py` — macOS System Controller

> **Purpose**: Executes system-level actions: volume, brightness, apps, browser, screenshots, time, and screen lock.

**Standalone test — interactive menu:**
```bash
python -m modules.system_control
```
(Presents a numbered menu to test every control individually)

**Available controls:**

| Function | What it does |
|---|---|
| `volume_up()` | Increases volume by `VOLUME_STEP`% |
| `volume_down()` | Decreases volume by `VOLUME_STEP`% |
| `set_volume(level)` | Sets volume to exact level 0–100 |
| `mute()` | Mutes audio |
| `unmute()` | Unmutes audio |
| `brightness_up()` | Increases brightness by `BRIGHTNESS_STEP`% |
| `brightness_down()` | Decreases brightness by `BRIGHTNESS_STEP`% |
| `set_brightness(level)` | Sets brightness 0–100 (requires `brew install brightness`) |
| `take_screenshot()` | Saves PNG to Desktop with timestamp |
| `open_website(name_or_url)` | Opens URL in default browser (has shortcuts for YouTube, Gmail, etc.) |
| `search_google(query)` | Opens Google search in browser |
| `search_youtube(query)` | Opens YouTube search in browser |
| `open_app(name)` | Opens macOS app by name (uses `open -a`) |
| `open_folder(name)` | Opens folder in Finder (Downloads, Desktop, Documents, etc.) |
| `get_time()` | Returns current time + date as a string |
| `lock_screen()` | Locks the macOS screen |
| `dispatch(action, argument)` | **Central dispatcher** — called by `intent_router.py` |

**`dispatch()` examples:**

```python
from modules.system_control import dispatch

dispatch("VOLUME_UP")
dispatch("VOLUME_SET", "75")
dispatch("BRIGHTNESS_DOWN")
dispatch("SEARCH", "best python tips")
dispatch("OPEN_WEB", "youtube")
dispatch("SCREENSHOT")
dispatch("TIME")
```

---

### `modules/intent_router.py` — Smart Response Router

> **Purpose**: Parses the LLM's raw response and decides whether to execute a system action or speak a conversational reply.

**Standalone test:**
```bash
python -m modules.intent_router
```
(Runs 19 test cases through the router with mock responses and shows results)

**Key functions:**

| Function | Description |
|---|---|
| `parse_response(llm_response)` | Returns `(kind, action, argument)` tuple. |
| `route(llm_response, speak_fn, silent)` | Parses + dispatches. Returns `(kind, result)`. |

**How routing works:**

1. LLM returns a string like `SYSTEM_ACTION:VOLUME_UP` or `"The sky is blue…"`
2. `parse_response()` uses regex to detect `SYSTEM_ACTION:<ACTION>:<ARGUMENT>` pattern
3. If matched → calls `system_control.dispatch(action, argument)` → speaks result
4. If not matched → passes the text directly to `voice_output.speak()`

**SYSTEM_ACTION tag format:**
```
SYSTEM_ACTION:<ACTION>
SYSTEM_ACTION:<ACTION>:<ARGUMENT>

Examples:
  SYSTEM_ACTION:VOLUME_UP
  SYSTEM_ACTION:VOLUME_SET:60
  SYSTEM_ACTION:BRIGHTNESS_SET:80
  SYSTEM_ACTION:SEARCH:python tutorials
  SYSTEM_ACTION:OPEN_WEB:youtube.com
  SYSTEM_ACTION:SCREENSHOT
  SYSTEM_ACTION:TIME
  SYSTEM_ACTION:LOCK
```

---

### `main.py` — Full Orchestrator

> **Purpose**: Wires everything together. The single entry point to run the complete Bujji assistant.

**Run the full assistant (voice mode):**
```bash
python main.py
```

**Run in text-only CLI mode (no microphone):**
```bash
python main.py --cli
```

**Run with debug logging:**
```bash
python main.py --debug
```

**Run REST API server:**
```bash
python main.py --api --host 0.0.0.0 --port 8000
```

**Quick API checks:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/wake
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"what time is it?"}'
```

**Full voice mode flow:**
```
[Background Thread]                    [Main Thread]
wake_listener ──────── "Hey Bujji" ──► _wake_event.set()
                                            │
                                            ▼
                                       speak("Yes, I'm here!")
                                            │
                                            ▼
                                       voice_input.listen_once()
                                            │ user speaks
                                            ▼
                                       llm_engine.chat(text)
                                            │ Gemma4:e2b replies
                                            ▼
                                       intent_router.route(reply)
                                            │
                             ┌─────────────┴─────────────┐
                             ▼                             ▼
                    system_control.dispatch()        voice_output.speak()
                    (volume, brightness, apps…)      (conversational reply)
                             │                             │
                             └─────────────┬─────────────┘
                                           ▼
                                    Return to listening
```

---

## 🔗 How to Connect Modules Individually

### Use just the LLM (no voice)

```python
from modules.llm_engine import chat, stream_chat

response = chat("What is the capital of France?")
print(response)

# With streaming
stream_chat("Tell me a joke", on_token=lambda t: print(t, end="", flush=True))
```

### Use just TTS

```python
from modules.voice_output import speak
speak("Hello, I am Bujji!")
```

### Use just voice input

```python
from modules.voice_input import listen_once, capture_command
text = listen_once(max_seconds=8)
print(f"You said: {text}")
```

### Use just system control

```python
from modules.system_control import dispatch, volume_up, get_time
volume_up()
print(get_time())
dispatch("BRIGHTNESS_SET", "70")
```

### Use just the intent router (with custom speak function)

```python
from modules.intent_router import route

def my_speak(text):
    print(f"[SPEAK] {text}")

kind, result = route("SYSTEM_ACTION:SCREENSHOT", speak_fn=my_speak)
```

### Wire LLM + Router + TTS (no wake word)

```python
from modules.llm_engine   import chat
from modules.intent_router import route

user_input = "Turn up the volume"
response   = chat(user_input)
kind, result = route(response)
# Bujji speaks the result automatically
```

### Wire everything except the wake word

```python
from modules.voice_input   import listen_once
from modules.llm_engine    import chat
from modules.intent_router import route

text     = listen_once()
response = chat(text)
route(response)
```

---

## 🚀 Quick Start Commands

```bash
# 1. Start Ollama
ollama serve

# 2. (New terminal) Activate venv
cd "/Users/kmsreenidhi/wake up"
source venv/bin/activate
cd gemma4-wake-bot

# 3. Run tests for each module individually
python -m modules.wake_listener     # Say "Hey Bujji" to test detection
python -m modules.voice_input       # Record & transcribe your voice
python -m modules.voice_output      # Hear Bujji speak
python -m modules.llm_engine        # Chat with Gemma4:e2b in terminal
python -m modules.system_control    # Test all system controls via menu
python -m modules.intent_router     # Test routing logic

# 4. Run the full assistant
python main.py                      # Full voice mode
python main.py --cli                # Text-only mode (no mic)
python main.py --debug              # Verbose logging
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `ConnectionError` / `Ollama not reachable` | Run `ollama serve` in a separate terminal |
| `gemma4:e2b not found` | Run `ollama pull gemma4:e2b` |
| `No module named 'pyaudio'` | `brew install portaudio && pip install pyaudio` |
| `No module named 'pocketsphinx'` | `pip install pocketsphinx` or switch to `RECOGNITION_MODE = "google"` in `config.py` |
| Brightness not changing | `brew install brightness` — or adjust manually; Bujji will still respond |
| TTS no sound | Check macOS audio output device; try `python -m modules.voice_output` |
| Wake word never triggers | Switch `RECOGNITION_MODE = "google"` in `config.py`; Google is more accurate |
| Whisper is slow | Change `WHISPER_MODEL_SIZE = "tiny"` in `config.py` |
| `PermissionError` on microphone | Grant mic access: `System Preferences → Privacy → Microphone` |

---

## 🧩 Module Dependency Map

```
config.py
    └── imported by ALL modules

wake_listener.py        ← independent (only needs SpeechRecognition + config)
voice_input.py          ← independent (needs Whisper + sounddevice + config)
voice_output.py         ← independent (needs pyttsx3 + config)
llm_engine.py           ← independent (needs requests + config)
system_control.py       ← independent (needs os/subprocess + config)

intent_router.py        ← depends on: system_control, voice_output
main.py                 ← depends on: ALL modules
```

---

## 🔮 Extending Bujji

### Add a new system action (e.g. "play music")

1. **Add handler in `system_control.py`:**
   ```python
   def play_music(query: str) -> str:
       _run_shell(f'open -a Music')
       return f"Opening Music app."
   ```

2. **Register in `dispatch()` in `system_control.py`:**
   ```python
   "PLAY_MUSIC": lambda a: play_music(a),
   ```

3. **Update `SYSTEM_PROMPT` in `config.py`:**
   ```
   SYSTEM_ACTION:PLAY_MUSIC:<song or genre>
   ```

No changes needed in `intent_router.py` or `main.py` — the router picks it up automatically via `dispatch()`.

### Change the wake word

Edit `config.py`:
```python
WAKE_WORD = "hey bujji"   # change to anything you like
```

### Make Bujji remember across sessions

In `llm_engine.py`, add persistence to `_conversation_history` using `json.dump()`/`json.load()` to a file. Load on startup, save after each exchange.

---

*Built with ❤️ — Bujji AI Assistant · Gemma4:e2b · macOS*
