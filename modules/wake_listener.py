"""Wake-word listener for Bujji."""

import os
import sys
import re
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RECOGNITION_MODE, WAKE_WORD


def _normalize_phrase(text: str) -> str:
    """Lowercase text, remove punctuation, and collapse repeated whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


def contains_wake_word(text: Optional[str], wake_word: str = WAKE_WORD) -> bool:
    """Return True only when the spoken text exactly matches the wake phrase."""
    if not text:
        return False
    return _normalize_phrase(text) == _normalize_phrase(wake_word)


def _recognize(recognizer, audio) -> str:
    if RECOGNITION_MODE == "google":
        return recognizer.recognize_google(audio)
    return recognizer.recognize_sphinx(audio)


def listen_for_wake_word_once(timeout: int = 10) -> bool:
    """Listen for a single short utterance and return True if it matches the wake word."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 150
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.6

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
        except sr.WaitTimeoutError:
            return False

    try:
        text = _recognize(recognizer, audio).lower()
    except sr.UnknownValueError:
        return False
    except sr.RequestError:
        return False

    return contains_wake_word(text)


def listen_for_wake_word() -> bool:
    """Block until the wake word is heard."""
    while True:
        if listen_for_wake_word_once():
            return True


if __name__ == "__main__":
    print(f"Listening for wake word: {WAKE_WORD!r}")
    heard = listen_for_wake_word()
    print(f"Wake word detected: {heard}")