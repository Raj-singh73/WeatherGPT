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

_TRANSLATION_CACHE: Dict[Tuple[str, str], str] = {}

BCP47_MAP = {
    "hi": "hi-IN",
    "mr": "mr-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "en": "en-IN"
}

# Domain-specific localized keyword dictionary for guaranteed fallback
INDIC_WEATHER_TERMS: Dict[str, Dict[str, str]] = {
    "mr": {
        "Reason": "कारण",
        "Precipitation Probability": "पावसाची शक्यता",
        "Relative Humidity": "हवेतील आर्द्रता",
        "Optimal Drying Window": "वाळवण्याची उत्तम वेळ",
        "Actionable Solution": "सल्ला व उपाय",
        "Recommendation": "शिफारस",
        "Atmospheric Condition": "हवामान स्थिती",
        "Expected Drying Time": "अपेक्षित वेळ",
        "Wind Gusts": "वाऱ्याचा वेग",
        "Rain Risk": "पावसाचा धोका"
    },
    "ta": {
        "Reason": "காரணம்",
        "Precipitation Probability": "மழைப்பொழிவு நிகழ்தகவு",
        "Relative Humidity": "ஈரப்பதம்",
        "Optimal Drying Window": "சிறந்த நேரம்",
        "Actionable Solution": "செயல் திட்டம் & தீர்வு",
        "Recommendation": "பரிந்துரை",
        "Atmospheric Condition": "வானிலை நிலை",
        "Expected Drying Time": "எதிர்பார்க்கப்படும் நேரம்",
        "Wind Gusts": "காற்றின் வேகம்",
        "Rain Risk": "மழை ஆபத்து"
    },
    "te": {
        "Reason": "కారణం",
        "Precipitation Probability": "వర్ష సూచన సంభావ్యత",
        "Relative Humidity": "తేమ శాతం",
        "Optimal Drying Window": "ఉత్తమ సమయం",
        "Actionable Solution": "సూచన & పరిష్కారం",
        "Recommendation": "సిఫార్సు",
        "Atmospheric Condition": "వాతావరణ స్థితి",
        "Expected Drying Time": "పట్టే సమయం",
        "Wind Gusts": "గాలి వేగం",
        "Rain Risk": "వర్ష ప్రమాదం"
    },
    "bn": {
        "Reason": "কারণ",
        "Precipitation Probability": "বৃষ্টির সম্ভাবনা",
        "Relative Humidity": "বাতাসের আর্দ্রতা",
        "Optimal Drying Window": "সেরা সময়",
        "Actionable Solution": "পরামর্শ ও পদক্ষেপ",
        "Recommendation": "সুপারিশ",
        "Atmospheric Condition": "আবহাওয়া পরিস্থিতি",
        "Expected Drying Time": "প্রয়োজনীয় সময়",
        "Wind Gusts": "বাতাসের গতিবেগ",
        "Rain Risk": "বৃষ্টির ঝুঁকি"
    },
    "gu": {
        "Reason": "કારણ",
        "Precipitation Probability": "વરસાદની સંભાવના",
        "Relative Humidity": "ભેજનું પ્રમાણ",
        "Optimal Drying Window": "શ્રેષ્ઠ સમય",
        "Actionable Solution": "સલાહ અને ઉપાય",
        "Recommendation": "ભલામણ",
        "Atmospheric Condition": "હવામાન સ્થિતિ",
        "Expected Drying Time": "અંદાજિત સમય",
        "Wind Gusts": "પવનની ગતિ",
        "Rain Risk": "વરસાદનું જોખમ"
    },
    "hi": {
        "Reason": "कारण",
        "Precipitation Probability": "वर्षा संभावना",
        "Relative Humidity": "हवा में नमी",
        "Optimal Drying Window": "सुखाने का समय",
        "Actionable Solution": "समाधान व सलाह",
        "Recommendation": "सलाह",
        "Atmospheric Condition": "मौसम स्थिति",
        "Expected Drying Time": "समय",
        "Wind Gusts": "हवा के झोंके",
        "Rain Risk": "बारिश का जोखिम"
    }
}

def translate_weather_response(text: str, target_lang: str) -> str:
    """
    Translates or localizes weather decision text into the specified Indic language.
    Employs an in-memory cache, GoogleTranslator, MyMemoryTranslator fallback,
    and an Indic Lexicon replacer to guarantee output is in the user's chosen language.
    """
    if not text or not text.strip():
        return text

    t_lang = (target_lang or "en").lower().split("-")[0]
    if t_lang in ["auto"]:
        return text

    # Check cache first
    cache_key = (text[:350], t_lang)
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    # If text is already in the target language script, return directly
    current_script = detect_language_from_text(text)
    if current_script == t_lang and t_lang != "en":
        return text

    # 1. Attempt GoogleTranslator via deep_translator
    try:
        from deep_translator import GoogleTranslator

        def _do_google():
            translator = GoogleTranslator(source="auto", target=t_lang)
            return translator.translate(text[:1400])

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_google)
            translated = future.result(timeout=5.0)
            if translated and len(translated.strip()) > 10 and not translated.lower().startswith("error"):
                _TRANSLATION_CACHE[cache_key] = translated
                return translated
    except Exception:
        pass

    # 2. Attempt MyMemoryTranslator fallback (100% free with BCP-47 codes)
    try:
        from deep_translator import MyMemoryTranslator
        bcp_target = BCP47_MAP.get(t_lang, f"{t_lang}-IN")

        def _do_mymemory():
            translator = MyMemoryTranslator(source="en-IN", target=bcp_target)
            return translator.translate(text[:500])

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_mymemory)
            translated = future.result(timeout=4.0)
            if translated and len(translated.strip()) > 10 and not translated.lower().startswith("error"):
                _TRANSLATION_CACHE[cache_key] = translated
                return translated
    except Exception:
        pass

    # 3. Built-in Lexicon Replacement Fallback
    terms = INDIC_WEATHER_TERMS.get(t_lang, {})
    if terms:
        localized_text = text
        for eng_term, indic_term in terms.items():
            localized_text = localized_text.replace(eng_term, indic_term)
        _TRANSLATION_CACHE[cache_key] = localized_text
        return localized_text

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

