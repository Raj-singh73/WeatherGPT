"""
multilingual_service.py - Multi-Lingual Decision Translation & Voice Speech Engine
SIH 2026 Problem Statement SIH26068: "From Weather Data to Actionable Decisions."

Delivers:
1. Multi-lingual Indic language detection (Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, English).
2. Direct translation & localization of weather directives, verdicts, and telemetry.
3. Natural-sounding Text-to-Speech (TTS) audio synthesis using gTTS.
"""

import io
import re
import concurrent.futures
from typing import Tuple, Dict, Any, Optional

SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "hi": {"bcp47": "hi-IN", "name": "हिन्दी", "english_name": "Hindi", "gtts": "hi"},
    "en": {"bcp47": "en-IN", "name": "English", "english_name": "English", "gtts": "en"},
    "ta": {"bcp47": "ta-IN", "name": "தமிழ்", "english_name": "Tamil", "gtts": "ta"},
    "mr": {"bcp47": "mr-IN", "name": "मराठी", "english_name": "Marathi", "gtts": "mr"},
    "bn": {"bcp47": "bn-IN", "name": "বাংলা", "english_name": "Bengali", "gtts": "bn"},
    "te": {"bcp47": "te-IN", "name": "తెలుగు", "english_name": "Telugu", "gtts": "te"},
    "gu": {"bcp47": "gu-IN", "name": "ગુજરાતી", "english_name": "Gujarati", "gtts": "gu"}
}

# Key Marathi distinction words to separate Marathi from Hindi in Devanagari script
MARATHI_MARKER_WORDS = {
    "आहे", "नाही", "होईल", "पाऊस", "शेतकरी", "करावा", "उद्या", "कधी", "करावे", "शक्य",
    "पिकावर", "फवारणी", "पावसाची", "हवामान", "शेत", "करणे", "येईल", "असल्यास"
}

def detect_language_from_text(text: str) -> str:
    """
    Detects the primary Indic or English language code from textual characters and vocabulary.
    Returns: 'hi', 'ta', 'bn', 'te', 'mr', 'gu', or 'en'.
    """
    if not text or not text.strip():
        return "hi"

    clean = text.strip()

    # 1. Tamil Script (\u0B80 - \u0BFF)
    if any('\u0B80' <= c <= '\u0BFF' for c in clean):
        return "ta"

    # 2. Bengali Script (\u0980 - \u09FF)
    if any('\u0980' <= c <= '\u09FF' for c in clean):
        return "bn"

    # 3. Telugu Script (\u0C00 - \u0C7F)
    if any('\u0C00' <= c <= '\u0C7F' for c in clean):
        return "te"

    # 4. Gujarati Script (\u0A80 - \u0AFF)
    if any('\u0A80' <= c <= '\u0AFF' for c in clean):
        return "gu"

    # 5. Devanagari Script (\u0900 - \u097F) -> Check Marathi vs Hindi
    if any('\u0900' <= c <= '\u097F' for c in clean):
        words = set(re.findall(r'[\u0900-\u097F]+', clean))
        if words.intersection(MARATHI_MARKER_WORDS):
            return "mr"
        return "hi"

    # 6. Latin / ASCII -> Check for Hinglish / Marathi / Tamil transliterations
    lower = clean.lower()
    if any(k in lower for k in ["kya", "aaj", "barish", "hogi", "fasal", "khet", "pani", "mausam", "sichai", "chhidkaw"]):
        return "hi"
    if any(k in lower for k in ["paus", "ahe", "hoil", "sheti", "fawarani", "pikavar"]):
        return "mr"
    if any(k in lower for k in ["mazhai", "varuma", "inru", "nalla", "payir"]):
        return "ta"
    if any(k in lower for k in ["brishti", "hobe", "aajke", "chash"]):
        return "bn"

    return "en"

def clean_text_for_speech(text: str, max_chars: int = 350) -> str:
    """
    Removes Markdown symbols, emojis, URLs, and formatting so Text-To-Speech engines
    speak fluently without pronouncing symbol names or stuttering.
    """
    if not text:
        return ""

    # Remove markdown headers, bold, bullet points
    clean = re.sub(r'#{1,6}\s*', '', text)
    clean = re.sub(r'\*\*(.*?)\*\*', r'\1', clean)
    clean = re.sub(r'\*(.*?)\*', r'\1', clean)
    clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', clean)
    clean = re.sub(r'•|\-|\*', ' ', clean)

    # Remove common emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F700-\U0001F77F"  # alchemical
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\u2600-\u26FF"          # Weather symbols (sun, umbrella, cloud)
        "\u2700-\u27BF"          # Dingbats
        "]+",
        flags=re.UNICODE
    )
    clean = emoji_pattern.sub(' ', clean)

    # Clean whitespace and limit to max length at sentence boundary
    clean = re.sub(r'\s+', ' ', clean).strip()
    if len(clean) > max_chars:
        truncated = clean[:max_chars]
        last_period = max(truncated.rfind('.'), truncated.rfind('।'), truncated.rfind('?'), truncated.rfind('!'))
        if last_period > 100:
            clean = truncated[:last_period + 1]
        else:
            clean = truncated + "..."

    return clean

def translate_weather_response(text: str, target_lang: str) -> str:
    """
    Translates or localizes weather decision text into the specified Indic language.
    Falls back gracefully to original text if translation times out or is unnecessary.
    """
    t_lang = (target_lang or "en").lower().split("-")[0]
    if t_lang in ["en", "auto"]:
        return text

    # If text is already in the target language script, return directly
    current_script = detect_language_from_text(text)
    if current_script == t_lang:
        return text

    # Attempt GoogleTranslator via deep_translator with 3.5s timeout
    try:
        from deep_translator import GoogleTranslator

        def _do_translate():
            translator = GoogleTranslator(source="auto", target=t_lang)
            # Translate up to 1500 characters
            to_trans = text[:1500]
            return translator.translate(to_trans)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_translate)
            translated = future.result(timeout=3.5)
            if translated and len(translated.strip()) > 10 and not translated.startswith("Error"):
                return translated
    except Exception as e:
        print(f"[WARN] deep_translator note ({t_lang}): {e}")

    return text

def generate_tts_audio_stream(text: str, language_code: str) -> Tuple[bytes, str]:
    """
    Generates high-fidelity MP3 voice audio using gTTS in the requested Indian or English language.
    Returns (mp3_bytes, mime_type).
    """
    from gtts import gTTS

    lang_short = (language_code or "hi").lower().split("-")[0]
    supported_info = SUPPORTED_LANGUAGES.get(lang_short, SUPPORTED_LANGUAGES["hi"])
    gtts_lang = supported_info["gtts"]

    clean = clean_text_for_speech(text)
    if not clean:
        clean = "मौसम की जानकारी उपलब्ध है।" if lang_short == "hi" else "Weather decision available."

    try:
        tts = gTTS(text=clean, lang=gtts_lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.getvalue(), "audio/mpeg"
    except Exception as e:
        print(f"[WARN] gTTS voice generation note for {gtts_lang}: {e}. Trying English fallback.")
        tts = gTTS(text=clean, lang="en", slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.getvalue(), "audio/mpeg"

