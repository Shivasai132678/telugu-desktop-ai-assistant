<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# lets go with option a i want u to give me a markdown on this using gemma4 e2b i want to make. a seperate testing file

Here is your complete Copilot-ready markdown guide for the wake word system with Gemma4:e2b, built as separate individually runnable and testable files.

***

# 🎙️ Gemma4:e2b — Always-On Wake Word Bot

## Option A: SpeechRecognition + Whisper + Offline Wake Word

### Separate Runnable + Testable Files — Copilot Guide

> **How to use:** Give this entire file to GitHub Copilot and say: *"Follow this guide exactly. Build each file as a standalone testable module, then connect them all in background_bot.py"*

***

## 🎯 What We Are Building

```
😴 Bot sleeps silently in background
         ↓
👂 You say "Hey Gemma"
         ↓
🔊 Bot says "Yes?"
         ↓
🎙️ Whisper records + transcribes your command
         ↓
🧠 Gemma4:e2b processes command
         ↓
🔊 Bot speaks the reply out loud
         ↓
😴 Goes back to sleep — loop restarts
```


***

## 📁 Final Project Structure

```
gemma4-wake-bot/
│
├── config.py                     # Shared settings — imported by all
│
├── modules/
│   ├── __init__.py               # Makes modules/ a Python package
│   ├── voice_input.py            # Whisper transcription (existing)
│   ├── voice_output.py           # pyttsx3 TTS (existing)
│   ├── system_control.py         # System commands (existing)
│   ├── command_bot.py            # Gemma4:e2b Ollama API (existing)
│   └── wake_listener.py          # 🆕 Always-on wake word listener
│
├── tests/
│   ├── test_wake_listener.py     # 🆕 Test wake word alone
│   ├── test_voice_input.py       # 🆕 Test Whisper alone
│   ├── test_voice_output.py      # 🆕 Test TTS alone
│   ├── test_command_bot.py       # 🆕 Test Gemma4 alone
│   └── test_full_pipeline.py     # 🆕 Test all together before final run
│
├── background_bot.py             # 🆕 Final always-on bot — connects everything
└── requirements.txt              # Updated
```


***

## 📦 Step 1: Install Required Libraries

```bash
# Activate your existing venv first
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

# New libraries needed
pip install SpeechRecognition
pip install pocketsphinx        # offline wake word recognition (no internet)
pip install pyaudio             # mic access (may already be installed)
```

> ⚠️ **pocketsphinx install issues on Windows?**
> ```bash > pip install pipwin > pipwin install pyaudio > pip install pocketsphinx > ```

> ⚠️ **pocketsphinx install issues on Linux?**
> ```bash > sudo apt install swig libpulse-dev -y > pip install pocketsphinx > ```

### Updated `requirements.txt`

```
requests>=2.28.0
openai-whisper>=20231117
pyttsx3>=2.90
pyaudio>=0.2.13
sounddevice>=0.4.6
scipy>=1.11.0
numpy>=1.24.0
pyautogui>=0.9.54
pillow>=10.0.0
gradio>=4.0.0
SpeechRecognition>=3.10.0
pocketsphinx>=5.0.0
```


***

## ⚙️ Step 2: `config.py` — Shared Settings

> No standalone run needed. Imported by all modules.

```python
# config.py
# Shared configuration for all modules — Gemma4:e2b

# ─── Ollama Settings ──────────────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11434/api/chat"
MODEL_NAME  = "gemma4:e2b"

# ─── Wake Word Settings ───────────────────────────────────────────────────────
WAKE_WORD         = "hey gemma"    # The phrase that wakes the bot up
WAKE_CONFIRMATION = "Yes?"         # What the bot says when it wakes up
SLEEP_MESSAGE     = "Going back to sleep."  # Said after completing a command

# Recognition mode:
# "sphinx"  → 100% offline, no internet (recommended)
# "google"  → needs internet, more accurate
RECOGNITION_MODE = "sphinx"

# ─── Voice Input Settings ─────────────────────────────────────────────────────
COMMAND_RECORD_SECONDS = 6         # How long to listen for command after wake
WHISPER_MODEL_SIZE     = "base"    # tiny | base | small | medium

# ─── Voice Output Settings ────────────────────────────────────────────────────
SPEECH_RATE   = 155                # 100=slow 155=normal 200=fast
SPEECH_VOLUME = 0.95               # 0.0 to 1.0

# ─── Model Settings ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are Gemma, a smart and friendly voice assistant running locally on the user's computer.
You can answer questions AND control the user's computer.
Keep all responses SHORT and SPOKEN-FRIENDLY — no bullet points, no markdown,
no long lists. Respond in 1-3 sentences maximum unless asked for more.

─── CONVERSATIONAL COMMANDS ─────────────────────────────────────────
- summarize <text>       : Summarize in 1 sentence
- translate <text>       : Translate to English
- calculate <expression> : Solve math
- greet                  : Friendly greeting
- help                   : List commands briefly
- sentiment <text>       : Positive / Negative / Neutral
- define <word>          : One sentence definition

─── SYSTEM CONTROL COMMANDS ─────────────────────────────────────────
- open <website>         : e.g. "open youtube"
- search <query>         : Google search
- search youtube <query> : YouTube search
- open app <name>        : e.g. "open app notepad"
- open folder <name>     : e.g. "open folder downloads"
- volume up / down       : Adjust volume
- mute / unmute          : Toggle audio
- screenshot             : Take screenshot
- what time is it        : Current time
- lock screen            : Lock the screen

─── RULES ───────────────────────────────────────────────────────────
1. For SYSTEM CONTROL commands reply ONLY with:
   SYSTEM_ACTION:<action>:<argument>
   Examples:
     SYSTEM_ACTION:OPEN_WEB:youtube
     SYSTEM_ACTION:SEARCH:python tutorials
     SYSTEM_ACTION:SEARCH_YOUTUBE:lofi music
     SYSTEM_ACTION:OPEN_APP:notepad
     SYSTEM_ACTION:OPEN_FOLDER:downloads
     SYSTEM_ACTION:VOLUME_UP
     SYSTEM_ACTION:VOLUME_DOWN
     SYSTEM_ACTION:MUTE
     SYSTEM_ACTION:UNMUTE
     SYSTEM_ACTION:SCREENSHOT
     SYSTEM_ACTION:TIME
     SYSTEM_ACTION:LOCK
2. For conversational commands respond in plain spoken English only.
3. No markdown, no bullet points, no asterisks in responses.
4. Keep replies under 3 sentences unless the user specifically asks for more.
"""
```


***

## 👂 Step 3: Create `modules/wake_listener.py`

### ✅ Run standalone to test:

```bash
python modules/wake_listener.py
```


### Expected output:

```
😴 Wake listener ready. Say "hey gemma" to trigger...
[you say "hey gemma"]
👂 Wake word detected! Triggered at: 15:04:32
✅ wake_listener.py standalone test passed!
```

```python
# modules/wake_listener.py
# PURPOSE : Listen silently in background for wake word "hey gemma"
#           Uses pocketsphinx (offline) or google (online) recognition
# STANDALONE TEST : python modules/wake_listener.py
# NOTE : This uses lightweight SpeechRecognition — NOT Whisper
#        Whisper is only used AFTER wake word is detected

import sys
import os
import datetime
import speech_recognition as sr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import WAKE_WORD, RECOGNITION_MODE


def listen_for_wake_word(
    wake_word: str = WAKE_WORD,
    mode: str = RECOGNITION_MODE,
    energy_threshold: int = 300,
    pause_threshold: float = 0.6
) -> bool:
    """
    Block until the wake word is detected.
    Returns True when wake word is heard.

    Args:
        wake_word        : The phrase to listen for e.g. "hey gemma"
        mode             : "sphinx" (offline) or "google" (online)
        energy_threshold : Mic sensitivity. Lower = more sensitive.
        pause_threshold  : Seconds of silence before phrase ends.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold    = energy_threshold
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold     = pause_threshold

    print(f'😴 Wake listener ready. Say "{wake_word}" to trigger...')

    with sr.Microphone() as source:
        # Calibrate mic to ambient noise once at start
        print("   Calibrating mic to background noise (1 sec)...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("   Mic calibrated. Listening silently...")

        while True:
            try:
                # Listen with short phrase limit for wake word efficiency
                audio = recognizer.listen(
                    source,
                    timeout=None,           # wait forever
                    phrase_time_limit=3     # max 3 sec per listen attempt
                )

                # Transcribe using selected mode
                if mode == "sphinx":
                    # 100% offline — no internet needed
                    text = recognizer.recognize_sphinx(audio).lower()
                elif mode == "google":
                    # More accurate but needs internet
                    text = recognizer.recognize_google(audio).lower()
                else:
                    text = recognizer.recognize_sphinx(audio).lower()

                print(f"   Heard: '{text}'")

                if wake_word.lower() in text:
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"👂 Wake word detected! Triggered at: {timestamp}")
                    return True

            except sr.WaitTimeoutError:
                # No speech detected — keep looping silently
                continue
            except sr.UnknownValueError:
                # Audio detected but not understood — keep looping
                continue
            except sr.RequestError as e:
                # API error (only happens in google mode)
                print(f"⚠️  Recognition error: {e}. Retrying...")
                continue
            except KeyboardInterrupt:
                print("\n⛔ Wake listener stopped by user.")
                return False
            except Exception as e:
                print(f"⚠️  Unexpected error: {e}. Continuing...")
                continue


def listen_for_wake_word_once(
    wake_word: str = WAKE_WORD,
    mode: str = RECOGNITION_MODE,
    timeout: int = 10
) -> bool:
    """
    Listen for wake word with a timeout.
    Returns True if detected, False if timeout reached.
    Used for testing.

    Args:
        timeout : Seconds to wait before giving up
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print(f'👂 Listening for "{wake_word}" ({timeout}s window)...')
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=3)

            if mode == "sphinx":
                text = recognizer.recognize_sphinx(audio).lower()
            else:
                text = recognizer.recognize_google(audio).lower()

            print(f"   Heard: '{text}'")
            return wake_word.lower() in text

    except sr.WaitTimeoutError:
        print("⏰ Timeout — no wake word heard.")
        return False
    except sr.UnknownValueError:
        print("❓ Audio not understood.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# ─── STANDALONE TEST ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  🧪 Testing wake_listener.py standalone")
    print("=" * 50)
    print(f"  Wake word : '{WAKE_WORD}'")
    print(f"  Mode      : {RECOGNITION_MODE}")
    print("=" * 50 + "\n")

    detected = listen_for_wake_word()

    if detected:
        print("\n✅ wake_listener.py standalone test passed!")
        print("   Wake word detection is working correctly.")
    else:
        print("\n⛔ Test interrupted or failed.")
```


***

## 🧪 Step 4: Create All Test Files

### `tests/test_wake_listener.py`

```bash
# Run with:
python tests/test_wake_listener.py
```

```python
# tests/test_wake_listener.py
# Tests wake word detection with a fixed timeout window

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.wake_listener import listen_for_wake_word_once
from config import WAKE_WORD, RECOGNITION_MODE

print("=" * 50)
print("  TEST: Wake Word Detection")
print("=" * 50)
print(f"  Say '{WAKE_WORD}' within 10 seconds...\n")

result = listen_for_wake_word_once(
    wake_word=WAKE_WORD,
    mode=RECOGNITION_MODE,
    timeout=10
)

if result:
    print("\n✅ PASS — Wake word detected correctly!")
else:
    print("\n❌ FAIL — Wake word not detected in time.")
    print("   Tips:")
    print("   → Speak clearly and close to the mic")
    print("   → Try lowering energy_threshold in config.py")
    print("   → Switch RECOGNITION_MODE to 'google' in config.py")
```


***

### `tests/test_voice_input.py`

```bash
python tests/test_voice_input.py
```

```python
# tests/test_voice_input.py
# Tests Whisper mic recording and transcription

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.voice_input import listen_for_command

print("=" * 50)
print("  TEST: Whisper Voice Input")
print("=" * 50)
print("  Speak a sentence when prompted...\n")

result = listen_for_command(duration=5)

if result:
    print(f"\n✅ PASS — Transcribed: '{result}'")
else:
    print("\n❌ FAIL — Nothing transcribed.")
    print("   → Check your microphone is connected and working")
```


***

### `tests/test_voice_output.py`

```bash
python tests/test_voice_output.py
```

```python
# tests/test_voice_output.py
# Tests pyttsx3 text-to-speech output

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.voice_output import speak, list_available_voices

print("=" * 50)
print("  TEST: pyttsx3 Voice Output")
print("=" * 50)

print("  Speaking test sentence...\n")
speak("Hello! I am Gemma. Voice output is working correctly.", block=True)
print("✅ PASS — If you heard the sentence, TTS is working!")

print("\n  Available voices on your system:")
list_available_voices()
```


***

### `tests/test_command_bot.py`

```bash
# Make sure ollama serve is running first!
python tests/test_command_bot.py
```

```python
# tests/test_command_bot.py
# Tests Gemma4:e2b Ollama responses

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.command_bot import send_command, check_ollama_running
from config import MODEL_NAME

print("=" * 50)
print("  TEST: Gemma4:e2b Command Bot")
print("=" * 50)
print(f"  Model: {MODEL_NAME}\n")

if not check_ollama_running():
    print("❌ FAIL — Ollama is not running!")
    print("   → Open a new terminal and run: ollama serve")
    exit(1)

print("✅ Ollama is running!\n")

history = []
test_commands = [
    "greet",
    "calculate 25 multiplied by 4",
    "define machine learning",
    "open youtube",
]

all_passed = True
for cmd in test_commands:
    print(f"  Sending : '{cmd}'")
    response = send_command(cmd, history)
    if response:
        print(f"  Response: {response}\n")
    else:
        print(f"  ❌ No response received!\n")
        all_passed = False

if all_passed:
    print("✅ PASS — command_bot.py working correctly!")
else:
    print("❌ FAIL — Some commands did not respond.")
```


***

### `tests/test_full_pipeline.py`

```bash
# Run this LAST — tests the full wake → command → speak pipeline once
python tests/test_full_pipeline.py
```

```python
# tests/test_full_pipeline.py
# Full pipeline test: wake word → Whisper → Gemma4 → speak
# Run this after all individual tests pass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.wake_listener import listen_for_wake_word_once
from modules.voice_input import listen_for_command
from modules.voice_output import speak
from modules.command_bot import send_command, check_ollama_running
from config import WAKE_WORD, WAKE_CONFIRMATION, SLEEP_MESSAGE

print("=" * 50)
print("  TEST: Full Pipeline — One Cycle")
print("=" * 50)

# Step 1: Check Ollama
if not check_ollama_running():
    print("❌ Ollama not running. Start with: ollama serve")
    exit(1)
print("✅ Ollama running\n")

# Step 2: Wait for wake word
print(f"STEP 1 → Say '{WAKE_WORD}' to begin the test...\n")
detected = listen_for_wake_word_once(timeout=15)

if not detected:
    print("❌ Wake word not detected. Test failed.")
    exit(1)

print("✅ Wake word detected!\n")

# Step 3: Speak confirmation
print(f"STEP 2 → Speaking confirmation: '{WAKE_CONFIRMATION}'")
speak(WAKE_CONFIRMATION, block=True)

# Step 4: Listen for command
print("\nSTEP 3 → Speak your command now...")
command = listen_for_command(duration=6)

if not command:
    print("❌ No command heard. Test failed.")
    exit(1)

print(f"✅ Command transcribed: '{command}'\n")

# Step 5: Send to Gemma4
print("STEP 4 → Sending to Gemma4:e2b...")
history = []
response = send_command(command, history)
print(f"✅ Response: {response}\n")

# Step 6: Speak response
print("STEP 5 → Speaking response...")
speak(response, block=True)

# Step 7: Sleep message
speak(SLEEP_MESSAGE, block=True)

print("\n" + "=" * 50)
print("✅ FULL PIPELINE TEST PASSED!")
print("   All 5 steps completed successfully.")
print("=" * 50)
```


***

## 🔗 Step 5: Create `background_bot.py` — The Always-On Bot

```bash
# Terminal 1:
ollama serve

# Terminal 2:
python background_bot.py
```

```python
# background_bot.py
# PURPOSE : Always-on background bot — sleeps until wake word,
#           then listens, responds, and goes back to sleep. Loops forever.
# RUN     : python background_bot.py
# STOP    : Press Ctrl+C

import sys
import time
from modules.wake_listener import listen_for_wake_word
from modules.voice_input import listen_for_command
from modules.voice_output import speak
from modules.command_bot import send_command, check_ollama_running
from config import (
    MODEL_NAME, WAKE_WORD,
    WAKE_CONFIRMATION, SLEEP_MESSAGE,
    COMMAND_RECORD_SECONDS
)


def print_banner():
    print("\n" + "=" * 55)
    print("  🤖 Gemma4:e2b — Always-On Wake Word Bot")
    print(f"  Model      : {MODEL_NAME}")
    print(f"  Wake Word  : '{WAKE_WORD}'")
    print(f"  TTS        : pyttsx3 (offline)")
    print(f"  STT        : Whisper (offline)")
    print(f"  Wake Mode  : SpeechRecognition + pocketsphinx")
    print("=" * 55)
    print("  Press Ctrl+C at any time to stop the bot.")
    print("=" * 55 + "\n")


def run_bot():
    """Main always-on loop."""
    print_banner()

    # Pre-flight check
    if not check_ollama_running():
        print("❌ Ollama is not running!")
        print("   Open a new terminal and run: ollama serve")
        print("   Then restart this script.")
        return

    print("✅ Ollama is running!")
    speak("Gemma is online and ready. Say Hey Gemma to wake me up.")

    conversation_history = []
    session_count = 0

    while True:
        try:
            # ── STAGE 1: Sleep — wait for wake word ──────────────────────
            detected = listen_for_wake_word(wake_word=WAKE_WORD)

            if not detected:
                # User pressed Ctrl+C inside wake listener
                break

            # ── STAGE 2: Wake up — confirm activation ────────────────────
            session_count += 1
            print(f"\n{'─'*40}")
            print(f"  🟢 Session #{session_count} started")
            print(f"{'─'*40}")
            speak(WAKE_CONFIRMATION```

