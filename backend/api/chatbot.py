"""
chatbot.py - Conversational WeatherGPT Chatbot API Router with Audio Voice Transcription
SIH 2026 Problem Statement SIH26068
"""

import io
import os
import wave
import concurrent.futures
import io
import os
import wave
import urllib.parse
import concurrent.futures
from typing import Optional, Dict, Any, Tuple
from fastapi import APIRouter, UploadFile, File, Form, Query, Response
from models.schemas import ChatRequest, ChatResponse
from services.llm_service import process_chat_message
from services.multilingual_service import (
    generate_tts_audio_stream,
    clean_text_for_speech,
    detect_language_from_text,
    SUPPORTED_LANGUAGES
)

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])

def convert_audio_to_16k_wav(audio_bytes: bytes) -> bytes:
    """Converts browser audio (WebM, Opus, OGG, WAV, MP4) to 16kHz mono 16-bit PCM WAV bytes using PyAV."""
    try:
        import av
        input_file = io.BytesIO(audio_bytes)
        container = av.open(input_file)
        audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
        if not audio_stream:
            return audio_bytes

        resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
        out_io = io.BytesIO()
        with wave.open(out_io, 'wb') as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)
            wav_out.setframerate(16000)
            for frame in container.decode(audio_stream):
                for resampled_frame in resampler.resample(frame):
                    wav_out.writeframes(resampled_frame.to_ndarray().tobytes())
        return out_io.getvalue()
    except Exception as e:
        print(f"[VOICE] PyAV conversion notice: {e}. Using raw audio bytes.")
        return audio_bytes

def transcribe_multi_lingual_audio(wav_pcm_bytes: bytes, requested_lang: str = "auto") -> Tuple[str, str]:
    """
    Transcribes audio and automatically detects spoken Indian or English language.
    Returns (transcribed_text, detected_language_code).
    """
    import speech_recognition as sr

    r = sr.Recognizer()
    r.energy_threshold = 120 # High sensitivity to soft speech
    r.dynamic_energy_threshold = True

    # Priority candidate languages
    req_clean = (requested_lang or "").strip().lower()
    if req_clean and req_clean not in ["auto", ""]:
        # Map short codes e.g. 'hi' -> 'hi-IN'
        full_code = requested_lang if "-" in requested_lang else f"{requested_lang}-IN"
        candidates = [full_code]
    else:
        # Check Hindi and English first, followed by major Indian languages
        candidates = ["hi-IN", "en-IN", "mr-IN", "bn-IN", "ta-IN", "te-IN", "gu-IN"]

    best_text = ""
    best_lang = "hi-IN"
    best_score = -1.0

    def try_candidate(lang_code):
        try:
            with io.BytesIO(wav_pcm_bytes) as wav_file:
                with sr.AudioFile(wav_file) as source:
                    audio_data = r.record(source)
                    txt = r.recognize_google(audio_data, language=lang_code)
                    if txt and isinstance(txt, str) and txt.strip():
                        clean_txt = txt.strip()
                        num_words = len(clean_txt.split())
                        # Base score from word count
                        score = num_words * 10
                        
                        # Script bonus
                        if lang_code == "hi-IN" and any('\u0900' <= c <= '\u097F' for c in clean_txt):
                            score += 35
                        elif lang_code == "mr-IN" and any('\u0900' <= c <= '\u097F' for c in clean_txt):
                            score += 30
                        elif lang_code == "bn-IN" and any('\u0980' <= c <= '\u09FF' for c in clean_txt):
                            score += 35
                        elif lang_code == "ta-IN" and any('\u0B80' <= c <= '\u0BFF' for c in clean_txt):
                            score += 35
                        elif lang_code == "te-IN" and any('\u0C00' <= c <= '\u0C7F' for c in clean_txt):
                            score += 35
                        elif lang_code == "gu-IN" and any('\u0A80' <= c <= '\u0AFF' for c in clean_txt):
                            score += 35
                        elif lang_code == "en-IN" and clean_txt.isascii():
                            score += 25
                        return lang_code, clean_txt, score
        except Exception:
            pass
        return None

    # Run candidates concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(candidates))) as executor:
        futures = [executor.submit(try_candidate, lc) for lc in candidates]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                lc, txt, score = res
                if score > best_score:
                    best_score = score
                    best_text = txt
                    best_lang = lc

    return best_text, best_lang

@router.get("/tts")
def get_tts_audio_stream(
    text: str = Query(..., description="Text to speak"),
    language: str = Query("hi", description="Language code e.g. hi, en, ta, mr, bn, te, gu")
):
    """Synthesizes high-clarity native Indic voice audio stream via gTTS."""
    audio_bytes, mime = generate_tts_audio_stream(text, language)
    return Response(
        content=audio_bytes,
        media_type=mime,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": "inline; filename=speech.mp3"
        }
    )

@router.post("/tts")
def post_tts_audio_stream(req: Dict[str, str]):
    """Synthesizes high-clarity native Indic voice audio stream for JSON requests."""
    text = req.get("text", "")
    lang = req.get("language", "hi")
    audio_bytes, mime = generate_tts_audio_stream(text, lang)
    return Response(
        content=audio_bytes,
        media_type=mime,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": "inline; filename=speech.mp3"
        }
    )

@router.post("", response_model=ChatResponse)
def chat_with_weathergpt(req: ChatRequest):
    """
    Conversational AI Weather Assistant:
    Intent Routing -> Weather/Forecast -> ML Risk -> RAG Retrieval -> Actionable Multilingual Synthesis.
    """
    loc = req.location or "Nagpur"
    lang = req.language or "en"
    persona = req.persona or "GENERAL"
    result = process_chat_message(user_msg=req.message, user_loc=loc, lang=lang, persona=persona)
    return ChatResponse(**result)

@router.post("/voice")
async def chat_with_voice(
    audio: Optional[UploadFile] = File(None),
    location: str = Form("Nagpur"),
    language: str = Form("auto"),
    persona: str = Form("GENERAL"),
    typed_text: Optional[str] = Form(None)
):
    """
    Accepts real recorded voice audio (WebM, OGG, or WAV), converts it in memory,
    automatically detects the language spoken, and generates a tailored weather decision in that language.
    """
    user_query = ""
    detected_lang_code = language if language != "auto" else "hi-IN"

    # 1. Prioritize Hardware Recorded Audio Transcription
    if audio:
        try:
            content = await audio.read()
            print(f"[VOICE] Received audio payload: {len(content)} bytes, requested lang: {language}")
            if len(content) > 300:
                wav_pcm_bytes = convert_audio_to_16k_wav(content)
                text, detected = transcribe_multi_lingual_audio(wav_pcm_bytes, requested_lang=language)
                if text:
                    user_query = text
                    detected_lang_code = detected
                    print(f"[VOICE] Audio Transcribed ({detected_lang_code}) -> '{user_query}'")
        except Exception as e:
            print(f"[WARN] Audio transcription error: {e}")

    # 2. Fallback to typed text or browser interim transcript if audio transcription had silence
    if not user_query and typed_text and typed_text.strip():
        user_query = typed_text.strip()
        print(f"[VOICE] Using text input fallback -> '{user_query}'")

    # 3. Detect Language from transcribed/typed text
    detected_short = detect_language_from_text(user_query) if user_query else "hi"
    short_to_full = {
        "hi": "hi-IN", "en": "en-IN", "ta": "ta-IN", "mr": "mr-IN",
        "bn": "bn-IN", "te": "te-IN", "gu": "gu-IN"
    }
    if language == "auto":
        detected_lang_code = short_to_full.get(detected_short, "hi-IN")
        short_lang = detected_short
    else:
        short_lang = language.split("-")[0] if "-" in language else language
        detected_lang_code = short_to_full.get(short_lang, language)

    # 4. Handle Empty Audio / Speech
    if not user_query:
        msg_map = {
            "hi": "माइक से आपकी आवाज़ सुनाई नहीं दी। कृपया माइक के पास बोलें या अपना प्रश्न लिखें।",
            "ta": "உங்கள் குரல் கேட்கவில்லை. தயவுசெய்து மைக்கில் தெளிவாக பேசவும்.",
            "mr": "तुमचा आवाज स्पष्ट आला नाही. कृपया माइक जवळ येऊन बोला किंवा प्रश्न लिहा.",
            "bn": "আপনার কথা শোনা যায়নি। দয়া করে মাইকের কাছে এসে কথা বলুন বা প্রশ্ন লিখুন।",
            "te": "మీ వాయిస్ స్పష్టంగా వినబడలేదు. దయచేసి మైక్ దగ్గర మాట్లాడండి.",
            "gu": "તમારો અવાજ સ્પષ્ટ સંભળાયો નથી. કૃપા કરીને માઇક પાસે બોલો."
        }
        msg = msg_map.get(short_lang, "Could not detect clear speech from your microphone. Please speak closer to your microphone or type your question.")

        speech_txt = clean_text_for_speech(msg)
        enc_speech = urllib.parse.quote(speech_txt)
        return {
            "transcribed_text": "",
            "detected_language": detected_lang_code,
            "response": f"⚠️ {msg}",
            "intent": "INCOMPLETE_AUDIO",
            "extracted_location": location,
            "language": short_lang,
            "speech_text": speech_txt,
            "audio_url": f"/api/chat/tts?language={short_lang}&text={enc_speech}",
            "risk_assessment": {
                "risk_score": 0,
                "risk_level": "UNKNOWN",
                "key_factors": ["No audio recognized"],
                "recommendation": msg
            },
            "sources": ["Voice Input Subsystem"],
            "confidence": 0.0
        }

    # 5. Process Decision in the exact detected language
    result = process_chat_message(user_msg=user_query, user_loc=location, lang=short_lang, persona=persona)
    result["transcribed_text"] = user_query
    result["detected_language"] = detected_lang_code

    # 6. Ensure Clean Speech Text & Audio Stream URL are attached
    speech_text = clean_text_for_speech(result.get("response", ""))
    result["speech_text"] = speech_text
    enc_text = urllib.parse.quote(speech_text[:350])
    result["audio_url"] = f"/api/chat/tts?language={short_lang}&text={enc_text}"

    return result

