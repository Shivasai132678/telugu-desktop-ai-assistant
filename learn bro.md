# Bujji AI Assistant Project Notes

## Overview
Bujji is a local, modular voice assistant for macOS. It wakes on a wake word, records a voice command, transcribes speech to text, sends the text to a local LLM via Ollama, and then either executes a system action or speaks a reply.

## Models Used
- LLM: Gemma4:e2b via Ollama (local HTTP API at http://localhost:11434)
- Speech-to-text: OpenAI Whisper (default model size: base)
- Wake word recognition: SpeechRecognition (Google or Sphinx mode)

## Libraries and Tools
### Python Dependencies (requirements.txt)
- fastapi
- uvicorn
- requests
- speechrecognition
- sounddevice
- scipy
- numpy
- openai-whisper
- pyttsx3

### System Tools (macOS)
- brightness (for brightness control)
- blueutil (for Bluetooth control)
- ollama (LLM runtime and model hosting)

## How It Works
1. Wake word listener runs in a background thread and listens for the wake phrase (default: "hey bujji").
2. When the wake word is detected, the assistant acknowledges and starts listening for a command.
3. Voice input is captured from the microphone and transcribed using Whisper.
4. The transcribed text is sent to Gemma4:e2b via Ollama.
5. The LLM response is parsed:
   - If it matches a SYSTEM_ACTION tag, the action is executed (volume, brightness, apps, web, etc.).
   - Otherwise, it is spoken as a conversational reply.
6. The assistant returns to listening for more commands until a sleep/exit phrase is detected.

## Key Configuration
- OLLAMA_URL: http://localhost:11434/api/chat
- MODEL_NAME: gemma4:e2b
- WAKE_WORD: hey bujji
- RECOGNITION_MODE: google (or sphinx for offline)
- WHISPER_MODEL_SIZE: base
- COMMAND_RECORD_SECONDS: 7
- MAX_HISTORY_TURNS: 10

## REST API (FastAPI)
The REST API is implemented in api_server.py. It provides health checks, chat endpoints, system actions, TTS, and STT.

### Base
- Default host/port is typically 127.0.0.1:8000 (depends on how you launch uvicorn).

### Endpoints
#### GET /health
Checks whether the API is running and whether Ollama is reachable.

Response:
{
  "status": "ok",
  "ollama": true
}

#### GET /wake
Returns the wake confirmation message.

Response:
{
  "message": "Yes, I'm here!"
}

#### POST /chat
Sends a message to the LLM and returns the raw reply along with routing info.

Request:
{
  "message": "what time is it?",
  "remember": true
}

Response:
{
  "reply": "SYSTEM_ACTION:TIME",
  "kind": "system",
  "action": "TIME",
  "argument": ""
}

#### POST /command
Sends a message to the LLM, routes it, and returns the result.

Request:
{
  "message": "set volume to 30",
  "remember": true
}

Response:
{
  "reply": "SYSTEM_ACTION:VOLUME_SET:30",
  "kind": "system",
  "result": "Volume set to 30%."
}

#### POST /action
Executes a system action directly (bypasses the LLM).

Request:
{
  "action": "VOLUME_SET",
  "argument": "50"
}

Response:
{
  "result": "Volume set to 50%."
}

#### POST /tts
Speaks text using TTS.

Request:
{
  "text": "Hello from Bujji"
}

Response:
{
  "status": "spoken"
}

#### POST /stt
Speech-to-text API. Choose mode: listen_once or capture.

Request (listen_once):
{
  "mode": "listen_once",
  "max_seconds": 10
}

Request (capture):
{
  "mode": "capture",
  "seconds": 7
}

Response:
{
  "text": "transcribed text here"
}

## Example CURL
curl http://localhost:8000/health

curl http://localhost:8000/wake

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what time is it?","remember":true}'

curl -X POST http://localhost:8000/action \
  -H "Content-Type: application/json" \
  -d '{"action":"VOLUME_SET","argument":"60"}'

## Notes
- The LLM uses a strict SYSTEM_ACTION format to trigger system control actions.
- Whisper runs locally; larger models increase accuracy but require more memory.
- Some system actions need extra tools installed (brightness, blueutil).
