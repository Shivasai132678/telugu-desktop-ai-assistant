from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import WAKE_CONFIRMATION
from modules.intent_router import parse_response, route
from modules.llm_engine import chat, stream_chat, check_ollama_health
import uuid
import json
import threading
import queue
from fastapi import Request
from fastapi.responses import StreamingResponse
from modules.system_control import dispatch
from modules.voice_input import capture_command, listen_once
from modules.voice_output import speak

app = FastAPI(title="Bujji API", version="1.0")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    remember: bool = True


class ChatResponse(BaseModel):
    reply: str
    kind: str
    action: str
    argument: str


class CommandResponse(BaseModel):
    reply: str
    kind: str
    result: str


class ActionRequest(BaseModel):
    action: str = Field(..., min_length=1)
    argument: Optional[str] = ""


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1)


class SttRequest(BaseModel):
    mode: str = Field("listen_once", pattern="^(listen_once|capture)$")
    max_seconds: int = 10
    seconds: int = 7


@app.get("/health")
def health():
    ollama_ok = check_ollama_health()
    return {"status": "ok", "ollama": ollama_ok}


@app.get("/wake")
def wake():
    return {"message": WAKE_CONFIRMATION}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    reply = chat(payload.message, remember=payload.remember)
    kind, action, argument = parse_response(reply)
    return ChatResponse(reply=reply, kind=kind, action=action, argument=argument)


@app.post("/command", response_model=CommandResponse)
def command_endpoint(payload: ChatRequest):
    reply = chat(payload.message, remember=payload.remember)
    kind, result = route(reply, silent=True)
    return CommandResponse(reply=reply, kind=kind, result=result)


@app.post("/action")
def action_endpoint(payload: ActionRequest):
    try:
        result = dispatch(payload.action, payload.argument or "")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"result": result}


@app.post("/tts")
def tts_endpoint(payload: TtsRequest):
    speak(payload.text)
    return {"status": "spoken"}


@app.post("/reset")
def reset_endpoint():
    """Clear the server-side conversation history for the LLM engine."""
    try:
        from modules.llm_engine import reset_history

        reset_history()
        return {"status": "ok", "message": "history cleared"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/stt")
def stt_endpoint(payload: SttRequest):
    if payload.mode == "listen_once":
        text = listen_once(max_seconds=payload.max_seconds)
    else:
        text = capture_command(seconds=payload.seconds)
    return {"text": text}


@app.post("/v1/chat/completions")
async def openai_chat_completions(request: Request):
    """Minimal OpenAI-compatible `/v1/chat/completions` endpoint.

    Supports both non-streaming and streaming (SSE `text/event-stream`) modes.
    Translates incoming OpenAI-style `messages` payload into a single user
    prompt (last user message preferred) and proxies to the existing
    `chat` / `stream_chat` functions.
    """
    body = await request.json()
    stream = bool(body.get("stream", False))

    # Extract user message from OpenAI-style `messages` if present
    messages = body.get("messages")
    if messages and isinstance(messages, list):
        user_msgs = [m for m in messages if m.get("role") == "user"]
        if user_msgs:
            user_message = user_msgs[-1].get("content", "")
        else:
            user_message = messages[-1].get("content", "")
    else:
        # fallback to older `prompt`/`input` fields
        user_message = body.get("prompt") or body.get("input") or ""

    if not user_message or not user_message.strip():
        raise HTTPException(status_code=400, detail="No user message provided")

    model = body.get("model") or "gemma4:e2b"

    if not stream:
        # Non-streaming: call existing chat() and return OpenAI-style response
        reply = chat(user_message, remember=body.get("remember", True))
        resp = {
            "id": str(uuid.uuid4()),
            "object": "chat.completion",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": reply},
                    "finish_reason": "stop",
                }
            ],
            "usage": {},
        }
        return resp

    # Streaming path: return SSE stream with token deltas
    def event_stream():
        q = queue.Queue()
        stop_marker = object()

        def on_token(tok: str):
            q.put(tok)

        def run_stream():
            try:
                stream_chat(user_message, on_token=on_token)
            except Exception as e:
                q.put(f"[LLM error] {e}")
            finally:
                q.put(stop_marker)

        threading.Thread(target=run_stream, daemon=True).start()

        while True:
            token = q.get()
            if token is stop_marker:
                break
            chunk = {"choices": [{"delta": {"content": token}, "index": 0}]}
            yield f"data: {json.dumps(chunk)}\n\n"

        # finalization events
        final = {"choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}]}
        yield f"data: {json.dumps(final)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/chat_stream_openai")
async def chat_stream_openai(payload: ChatRequest):
    """Compatibility alias for older tooling: stream tokens for a single `message` field."""
    user_message = payload.message
    remember = bool(payload.remember)

    def event_stream():
        q = queue.Queue()
        stop_marker = object()

        def on_token(tok: str):
            q.put(tok)

        def run_stream():
            try:
                stream_chat(user_message, on_token=on_token)
            except Exception as e:
                q.put(f"[LLM error] {e}")
            finally:
                q.put(stop_marker)

        threading.Thread(target=run_stream, daemon=True).start()

        while True:
            token = q.get()
            if token is stop_marker:
                break
            chunk = {"choices": [{"delta": {"content": token}, "index": 0}]}
            yield f"data: {json.dumps(chunk)}\n\n"

        final = {"choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}]}
        yield f"data: {json.dumps(final)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
