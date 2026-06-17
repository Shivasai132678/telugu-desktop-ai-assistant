# modules/llm_engine.py
# ─── LLM Engine Module ────────────────────────────────────────────────────────
# Handles all communication with Gemma4:e2b via Ollama.
# Supports multi-turn conversation history and streaming responses.
#
# STANDALONE TEST:
#   python -m modules.llm_engine
#   (Opens an interactive CLI chat loop with Bujji via Gemma4:e2b)
#
# USED BY:
#   main.py → calls chat() with each user command, gets back LLM response
#   intent_router.py → receives the response string for routing
#
# REQUIRES:
#   Ollama running locally: `ollama serve`
#   Gemma4:e2b pulled:      `ollama pull gemma4:e2b`
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import json
import requests
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OLLAMA_URL, MODEL_NAME, SYSTEM_PROMPT, MAX_HISTORY_TURNS

# ─── Conversation history (list of {"role": ..., "content": ...} dicts) ───────
_conversation_history: List[Dict[str, str]] = []


def _build_messages(user_message: str) -> List[Dict[str, str]]:
    """Assemble the full message list with system prompt + history + new user msg."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(_conversation_history)
    messages.append({"role": "user", "content": user_message})
    return messages


def chat(user_message: str, remember: bool = True) -> str:
    """
    Send a message to Gemma4:e2b and return the assistant's reply.

    Args:
        user_message: The text to send to the model.
        remember:     If True, adds this exchange to conversation history.

    Returns:
        Assistant response string, or error message on failure.
    """
    global _conversation_history

    messages = _build_messages(user_message)

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 4096,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        reply = data["message"]["content"].strip()

        if remember:
            _conversation_history.append({"role": "user", "content": user_message})
            _conversation_history.append({"role": "assistant", "content": reply})
            # Trim history to stay within MAX_HISTORY_TURNS
            max_msgs = MAX_HISTORY_TURNS * 2  # each turn = 2 messages
            if len(_conversation_history) > max_msgs:
                _conversation_history = _conversation_history[-max_msgs:]

        return reply

    except requests.exceptions.ConnectionError:
        return (
            "I can't reach Ollama right now. Please make sure Ollama is running "
            "with `ollama serve` and that Gemma4:e2b is pulled."
        )
    except requests.exceptions.Timeout:
        return "The model took too long to respond. Please try again."
    except Exception as e:
        return f"LLM error: {e}"


def stream_chat(user_message: str, on_token=None) -> str:
    """
    Stream tokens from Gemma4:e2b, optionally calling on_token(token) for each.

    Args:
        user_message: The text to send to the model.
        on_token:     Optional callback(token: str) called for each streamed token.

    Returns:
        Full assembled response string.
    """
    global _conversation_history

    messages = _build_messages(user_message)

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 4096,
        },
    }

    full_reply = ""
    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line.decode("utf-8"))
                token = chunk.get("message", {}).get("content", "")
                full_reply += token
                if on_token:
                    on_token(token)
                if chunk.get("done", False):
                    break

        _conversation_history.append({"role": "user", "content": user_message})
        _conversation_history.append({"role": "assistant", "content": full_reply.strip()})

        max_msgs = MAX_HISTORY_TURNS * 2
        if len(_conversation_history) > max_msgs:
            _conversation_history = _conversation_history[-max_msgs:]

        return full_reply.strip()

    except Exception as e:
        return f"LLM streaming error: {e}"


def reset_history() -> None:
    """Clear the conversation history (fresh start)."""
    global _conversation_history
    _conversation_history = []
    print("  [LLMEngine] Conversation history cleared.")


def get_history() -> List[Dict[str, str]]:
    """Return a copy of the current conversation history."""
    return list(_conversation_history)


def check_ollama_health() -> bool:
    """Check if Ollama is reachable and Gemma4:e2b is available."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        if any("gemma4" in m for m in models):
            print(f"  [LLMEngine] ✅ Ollama healthy — {MODEL_NAME} found.")
            return True
        else:
            print(f"  [LLMEngine] ⚠️  Ollama running but {MODEL_NAME} not found.")
            print(f"              Run: ollama pull {MODEL_NAME}")
            return False
    except Exception as e:
        print(f"  [LLMEngine] ❌ Ollama not reachable: {e}")
        return False


# ─── STANDALONE TEST ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  🧪 llm_engine.py — Standalone Interactive Test")
    print("=" * 55)
    print(f"  Model   : {MODEL_NAME}")
    print(f"  Ollama  : {OLLAMA_URL}")
    print("=" * 55)
    print()

    # Health check first
    healthy = check_ollama_health()
    if not healthy:
        print("\n  ⚠️  Proceeding anyway — you may get errors.\n")

    print("  Type your message and press Enter.")
    print("  Commands: 'reset' to clear history, 'quit' or 'exit' to stop.\n")

    while True:
        try:
            user_input = input("  You → ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Bye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("  Goodbye!")
            break
        if user_input.lower() == "reset":
            reset_history()
            print("  History cleared.\n")
            continue

        print("  Bujji → ", end="", flush=True)
        reply = stream_chat(user_input, on_token=lambda t: print(t, end="", flush=True))
        print()  # newline after streamed output
        print()

    print("\n✅ llm_engine.py standalone test complete!")
