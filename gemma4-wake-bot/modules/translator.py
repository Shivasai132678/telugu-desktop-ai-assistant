# modules/translator.py
# ─── English → Telugu Translation Module ─────────────────────────────────────
# Uses facebook/nllb-200-distilled-600M — Meta's multilingual translation model
# with official Telugu support.  Downloaded once (~2.4 GB), cached forever.
#
# STANDALONE TEST:
#   python -m modules.translator
#
# USED BY:
#   main.py → translate_to_telugu(llm_response) before passing to speak()
# ─────────────────────────────────────────────────────────────────────────────

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Model config ─────────────────────────────────────────────────────────────
# NLLB-200 distilled 600M — best quality/size tradeoff for EN↔TE
MODEL_NAME   = "facebook/nllb-200-distilled-600M"
SRC_LANG     = "eng_Latn"   # English
TGT_LANG     = "tel_Telu"   # Telugu
SRC_LANG_TE  = "tel_Telu"   # Telugu
TGT_LANG_EN  = "eng_Latn"   # English

_tokenizer   = None
_model       = None

# Telugu Unicode block: U+0C00–U+0C7F
_TELUGU_RE   = re.compile(r"[\u0C00-\u0C7F]")


def _is_telugu(text: str) -> bool:
    """Return True if the text already contains significant Telugu characters."""
    telugu_chars = len(_TELUGU_RE.findall(text))
    total_alpha  = sum(1 for c in text if c.isalpha())
    if total_alpha == 0:
        return False
    return (telugu_chars / total_alpha) > 0.3   # >30% Telugu → already Telugu


def _load_model(verbose: bool = True) -> None:
    """Lazy-load NLLB-200 once. Downloads ~2.4 GB on first run, cached forever."""
    global _tokenizer, _model
    if _tokenizer is not None:
        return

    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    if verbose:
        print(f"  [Translator] Loading {MODEL_NAME} …")
        print("  [Translator] (First run downloads ~2.4 GB — subsequent runs are instant)")

    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    _model     = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    _model.eval()

    if verbose:
        print("  [Translator] ✅ NLLB-200 translation model ready.")


def _translate(text: str, src_lang: str, tgt_lang: str, force: bool = False) -> str:
    """Translate text between languages using NLLB-200."""
    if not text or not text.strip():
        return text

    # Pass through unchanged if already Telugu and target is Telugu
    if tgt_lang == TGT_LANG and not force and _is_telugu(text):
        return text

    # Pass through SYSTEM_ACTION tags unchanged
    if text.strip().startswith("SYSTEM_ACTION:"):
        return text

    try:
        _load_model()

        import torch

        # Split into sentence chunks to stay within 200-token limit
        chunks = _split_sentences(text)
        translated_parts = []

        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            if chunk.startswith("SYSTEM_ACTION:"):
                translated_parts.append(chunk)
                continue

            _tokenizer.src_lang = src_lang
            encoded = _tokenizer(
                chunk,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=200,
            )

            forced_bos = _tokenizer.convert_tokens_to_ids(tgt_lang)

            with torch.no_grad():
                generated = _model.generate(
                    **encoded,
                    forced_bos_token_id=forced_bos,
                    num_beams=4,
                    max_length=200,
                    early_stopping=True,
                )

            result = _tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
            translated_parts.append(result)

        return " ".join(translated_parts)

    except Exception as e:
        print(f"  [Translator] ⚠️  Translation failed ({e}), returning original text.")
        return text


def translate_to_telugu(text: str, force: bool = False) -> str:
    """
    Translate `text` from English to Telugu using NLLB-200.

    • If the text is already mostly Telugu, returns it unchanged (unless force=True).
    • SYSTEM_ACTION: tags are passed through untouched.
    • Returns the original text on any error — pipeline never breaks.

    Args:
        text:  Input string (English or mixed).
        force: Translate even if text looks like Telugu already.

    Returns:
        Telugu string.
    """
    return _translate(text, SRC_LANG, TGT_LANG, force=force)


def translate_to_english(text: str, force: bool = False) -> str:
    """Translate `text` from Telugu to English using NLLB-200."""
    return _translate(text, SRC_LANG_TE, TGT_LANG_EN, force=force)


def _split_sentences(text: str) -> list:
    """Split text into small chunks for translation (max ~200 tokens each)."""
    parts = re.split(r"(?<=[.!?\n])\s+", text.strip())
    chunks, current = [], ""
    for part in parts:
        if len(current) + len(part) < 300:
            current = (current + " " + part).strip()
        else:
            if current:
                chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks if chunks else [text]


def detect_language(text: str) -> str:
    """Return 'telugu' if text is mostly Telugu script, else 'english'."""
    return "telugu" if _is_telugu(text) else "english"


# ─── STANDALONE TEST ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  🧪 translator.py — Standalone Test (NLLB-200)")
    print("=" * 60)
    print()

    test_cases = [
        ("Hello, how are you?",                          "en"),
        ("What time is it now?",                         "en"),
        ("I am your smart assistant Bujji.",             "en"),
        ("The volume has been increased.",               "en"),
        ("Good morning! Have a great day.",              "en"),
        ("I can help you control your computer.",       "en"),
        ("నమస్కారం! ఇది ఇప్పటికే తెలుగు.",            "te"),  # Already Telugu
        ("SYSTEM_ACTION:VOLUME_UP",                      "--"),  # Should pass through
    ]

    for sentence, lang_hint in test_cases:
        lang   = detect_language(sentence)
        result = translate_to_telugu(sentence)
        status = "✅ PASS-THRU" if lang == "telugu" or sentence.startswith("SYSTEM_ACTION") else "🔄 TRANSLATED"
        print(f"  [{lang.upper():7}] {sentence!r}")
        print(f"  {status} → {result!r}")
        print()

    print("✅ translator.py standalone test complete!")
