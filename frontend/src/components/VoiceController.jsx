import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Square, Globe, Loader2, Sparkles, Check, X } from 'lucide-react';
import api from '../api';

const VOICE_LANGUAGES = [
  { code: 'auto', key: 'auto', label: '🌐 Auto-Detect', short: 'Auto' },
  { code: 'hi-IN', key: 'hi', label: '🇮🇳 हिन्दी (Hindi)', short: 'हिन्दी' },
  { code: 'en-IN', key: 'en', label: '🇬🇧 English', short: 'English' },
  { code: 'mr-IN', key: 'mr', label: '🇮🇳 मराठी (Marathi)', short: 'मराठी' },
  { code: 'bn-IN', key: 'bn', label: '🇮🇳 বাংলা (Bengali)', short: 'বাংলা' },
  { code: 'ta-IN', key: 'ta', label: '🇮🇳 தமிழ் (Tamil)', short: 'தமிழ்' },
  { code: 'te-IN', key: 'te', label: '🇮🇳 తెలుగు (Telugu)', short: 'తెలుగు' },
  { code: 'gu-IN', key: 'gu', label: '🇮🇳 ગુજરાતી (Gujarati)', short: 'ગુજરાતી' },
  { code: 'kn-IN', key: 'kn', label: '🇮🇳 ಕನ್ನಡ (Kannada)', short: 'ಕನ್ನಡ' },
  { code: 'ml-IN', key: 'ml', label: '🇮🇳 മലയാളം (Malayalam)', short: 'മലയാളം' },
  { code: 'pa-IN', key: 'pa', label: '🇮🇳 ਪੰਜਾਬੀ (Punjabi)', short: 'ਪੰਜਾਬੀ' },
  { code: 'or-IN', key: 'or', label: '🇮🇳 ଓଡ଼ିଆ (Odia)', short: 'ଓଡ଼ିଆ' },
  { code: 'as-IN', key: 'as', label: '🇮🇳 অসমীয়া (Assamese)', short: 'অসমীয়া' },
  { code: 'ur-IN', key: 'ur', label: '🇮🇳 اردو (Urdu)', short: 'اردو' },
];

export default function VoiceController({ 
  onSpeechRecognized, 
  onTranscriptUpdate, 
  textToSpeak, 
  language = 'en',
  location = 'Nagpur'
}) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isSoundDetected, setIsSoundDetected] = useState(false);
  const [selectedVoiceLang, setSelectedVoiceLang] = useState('auto');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [detectedLangBadge, setDetectedLangBadge] = useState('');

  const isListeningRef = useRef(false);
  const recognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const animFrameRef = useRef(null);
  const audioElemRef = useRef(null);
  const interimTranscriptRef = useRef('');
  const finalTranscriptRef = useRef('');

  // Sync default language with current app language on mount or change
  useEffect(() => {
    const langMap = {
      hi: 'hi-IN',
      mr: 'mr-IN',
      bn: 'bn-IN',
      ta: 'ta-IN',
      te: 'te-IN',
      gu: 'gu-IN',
      kn: 'kn-IN',
      ml: 'ml-IN',
      pa: 'pa-IN',
      or: 'or-IN',
      as: 'as-IN',
      ur: 'ur-IN',
      kn: 'kn-IN',
      ml: 'ml-IN',
      pa: 'pa-IN',
      or: 'or-IN',
      as: 'as-IN',
      ur: 'ur-IN',
      kn: 'kn-IN',
      ml: 'ml-IN',
      pa: 'pa-IN',
      or: 'or-IN',
      as: 'as-IN',
      ur: 'ur-IN',
      en: 'en-IN'
    };
    if (selectedVoiceLang === 'auto' && language && langMap[language]) {
      setSelectedVoiceLang(langMap[language]);
    }
  }, [language]);

  const cleanupAudio = () => {
    isListeningRef.current = false;
    setIsListening(false);
    setIsSoundDetected(false);
    setAudioLevel(0);

    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try { audioContextRef.current.close(); } catch (e) {}
      audioContextRef.current = null;
    }

    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
      recognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch (e) {}
    }
  };

  useEffect(() => {
    return () => cleanupAudio();
  }, []);

  const toggleListening = async () => {
    if (isListening) {
      await stopListeningAndProcess();
      return;
    }

    if (isSpeaking) {
      stopSpeaking();
    }

    interimTranscriptRef.current = '';
    finalTranscriptRef.current = '';
    setDetectedLangBadge('');
    audioChunksRef.current = [];

    // 1. Hardware Microphone Stream
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true, 
          noiseSuppression: true, 
          autoGainControl: true 
        } 
      });
      streamRef.current = stream;
    } catch (err) {
      console.warn('Microphone permission error:', err);
      alert('Microphone permission is needed. Please allow microphone access in your browser.');
      return;
    }

    // 2. Web Audio API Sound Level & Voice Activity Detection (VAD)
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser); // No destination to speakers (zero feedback)

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!isListeningRef.current) return;
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        const avg = sum / dataArray.length;
        const lvl = Math.min(100, Math.round(avg * 2.2));
        setAudioLevel(lvl);
        setIsSoundDetected(lvl > 10);
        animFrameRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();
    } catch (e) {
      console.warn('AudioContext notice:', e);
    }

    // 3. Hardware MediaRecorder for Reliable Backup Audio Transcription
    try {
      const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4', ''];
      const supportedType = mimeTypes.find(type => !type || MediaRecorder.isTypeSupported(type)) || '';
      const mediaRecorder = supportedType ? new MediaRecorder(stream, { mimeType: supportedType }) : new MediaRecorder(stream);
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(200); // 200ms chunks
    } catch (mrErr) {
      console.warn('MediaRecorder notice:', mrErr);
    }

    // 4. Live Browser SpeechRecognition (Interim & Continuous Multi-Lingual STT)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recog = new SpeechRecognition();
        recog.continuous = true;
        recog.interimResults = true;

        const langMap = {
          hi: 'hi-IN',
          mr: 'mr-IN',
          bn: 'bn-IN',
          ta: 'ta-IN',
          te: 'te-IN',
          gu: 'gu-IN',
          en: 'en-IN'
        };
        const activeLangCode = selectedVoiceLang === 'auto' ? (langMap[language] || 'hi-IN') : selectedVoiceLang;
        recog.lang = activeLangCode;

        recog.onresult = (event) => {
          let full = '';
          let interim = '';

          for (let i = 0; i < event.results.length; ++i) {
            const chunk = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              full += chunk + ' ';
            } else {
              interim += chunk;
            }
          }

          const combined = (full + interim).trim();
          finalTranscriptRef.current = full.trim();
          interimTranscriptRef.current = interim.trim();

          if (combined && onTranscriptUpdate) {
            onTranscriptUpdate(combined);
          }
        };

        recog.onerror = (event) => {
          console.warn('SpeechRecognition event:', event.error);
        };

        recognitionRef.current = recog;
        recog.start();
      } catch (e) {
        console.warn('SpeechRecognition start error:', e);
      }
    }

    isListeningRef.current = true;
    setIsListening(true);
  };

  const stopMediaRecorderAsync = () => {
    return new Promise((resolve) => {
      const mr = mediaRecorderRef.current;
      if (!mr || mr.state === 'inactive') {
        resolve(null);
        return;
      }
      mr.onstop = () => {
        if (audioChunksRef.current.length > 0) {
          const blobType = mr.mimeType || 'audio/webm';
          const blob = new Blob(audioChunksRef.current, { type: blobType });
          resolve(blob);
        } else {
          resolve(null);
        }
      };
      try { mr.stop(); } catch (e) { resolve(null); }
    });
  };

  const stopListeningAndProcess = async () => {
    isListeningRef.current = false;
    setIsListening(false);
    setIsTranscribing(true);

    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }

    const recordedBlob = await stopMediaRecorderAsync();
    cleanupAudio();

    const capturedBrowserText = (finalTranscriptRef.current || interimTranscriptRef.current).trim();

    // If browser captured speech cleanly, use it directly
    if (capturedBrowserText) {
      setIsTranscribing(false);
      if (onSpeechRecognized) {
        onSpeechRecognized(capturedBrowserText);
      }
      return;
    }

    // Otherwise, upload recorded hardware audio to backend for server-side multi-lingual transcription
    if (recordedBlob && recordedBlob.size > 400) {
      try {
        const formData = new FormData();
        formData.append('audio', recordedBlob, 'query.webm');
        formData.append('location', location);
        formData.append('language', selectedVoiceLang);
        if (capturedBrowserText) formData.append('typed_text', capturedBrowserText);

        const res = await api.chatVoice(formData);
        if (res.transcribed_text) {
          if (res.detected_language) {
            const langObj = VOICE_LANGUAGES.find(l => l.code === res.detected_language);
            setDetectedLangBadge(langObj ? langObj.short : res.detected_language);
          }
          if (onTranscriptUpdate) onTranscriptUpdate(res.transcribed_text);
          if (onSpeechRecognized) onSpeechRecognized(res.transcribed_text);
        } else {
          alert('Could not detect clear speech. Please try speaking closer to your microphone.');
        }
      } catch (err) {
        console.warn('Backend audio transcription error:', err);
      }
    }

    setIsTranscribing(false);
  };

  // Text-to-Speech Playback for AI answers
  const speakText = () => {
    if (!textToSpeak) return;
    if (isSpeaking) {
      stopSpeaking();
      return;
    }

    const clean = textToSpeak
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/•|\-|\*/g, ' ')
      .replace(/#{1,6}\s*/g, '')
      .replace(/\[.*?\]\(.*?\)/g, '')
      .replace(/[\u{1F1E0}-\u{1F1FF}\u{1F300}-\u{1F5FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 350);

    if (!clean) return;

    // High-Clarity indic gTTS stream with browser fallback
    try {
      const audioUrl = `/api/chat/tts?language=${language || 'hi'}&text=${encodeURIComponent(clean)}`;
      const audio = new Audio(audioUrl);
      audioElemRef.current = audio;
      setIsSpeaking(true);

      audio.onplay = () => setIsSpeaking(true);
      audio.onended = () => {
        setIsSpeaking(false);
        audioElemRef.current = null;
      };
      audio.onerror = () => {
        setIsSpeaking(false);
        audioElemRef.current = null;
        speakViaBrowser(clean);
      };

      audio.play().catch(() => speakViaBrowser(clean));
    } catch (err) {
      speakViaBrowser(clean);
    }
  };

  const speakViaBrowser = (clean) => {
    if (!('speechSynthesis' in window)) {
      setIsSpeaking(false);
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(clean);
    const langMap = {
      hi: 'hi-IN', mr: 'mr-IN', bn: 'bn-IN',
      ta: 'ta-IN', te: 'te-IN', gu: 'gu-IN', en: 'en-IN'
    };
    utterance.lang = langMap[language] || 'hi-IN';
    utterance.rate = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const matchedVoice = voices.find(v => v.lang.startsWith(language));
    if (matchedVoice) utterance.voice = matchedVoice;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (audioElemRef.current) {
      audioElemRef.current.pause();
      audioElemRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  return (
    <div className="relative flex items-center space-x-1.5">
      {/* Speech-to-Text Microphone Button */}
      <button
        type="button"
        onClick={toggleListening}
        disabled={isTranscribing}
        title={isListening ? 'Listening to voice... Click to finish speaking' : 'Speak in any language'}
        className={`p-2.5 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
          isTranscribing
            ? 'bg-amber-500 text-white animate-pulse'
            : isListening
            ? 'bg-rose-600 text-white animate-pulse shadow-md shadow-rose-600/30 ring-2 ring-rose-300'
            : 'bg-slate-100 text-slate-700 hover:bg-sky-50 hover:text-sky-700 border border-slate-200'
        }`}
      >
        {isTranscribing ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : isListening ? (
          <Square className="h-4 w-4 fill-white" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </button>

      {/* Text-to-Speech Output Button */}
      {textToSpeak && (
        <button
          type="button"
          onClick={speakText}
          title={isSpeaking ? 'Mute speech' : 'Listen to answer'}
          className={`p-2.5 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
            isSpeaking
              ? 'bg-sky-600 text-white shadow-md shadow-sky-600/30'
              : 'bg-slate-100 text-slate-700 hover:bg-sky-50 hover:text-sky-700 border border-slate-200'
          }`}
        >
          {isSpeaking ? <VolumeX className="h-4 w-4 animate-pulse" /> : <Volume2 className="h-4 w-4" />}
        </button>
      )}

      {/* Language Selector Trigger Pill */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setShowLangMenu(!showLangMenu)}
          className="text-[10.5px] font-bold px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 flex items-center gap-1 transition-all cursor-pointer"
          title="Change voice recognition language"
        >
          <Globe className="h-3 w-3 text-sky-600" />
          <span>{VOICE_LANGUAGES.find(l => l.code === selectedVoiceLang)?.short || 'Auto'}</span>
        </button>

        {showLangMenu && (
          <div className="absolute bottom-full mb-1 left-0 bg-white border border-slate-200 shadow-xl rounded-2xl p-1.5 z-50 w-44 space-y-0.5 animate-fadeIn">
            <span className="text-[10px] font-extrabold text-slate-400 px-2 py-1 block uppercase tracking-wider">
              Speech Language:
            </span>
            {VOICE_LANGUAGES.map(lang => (
              <button
                key={lang.code}
                type="button"
                onClick={() => {
                  setSelectedVoiceLang(lang.code);
                  setShowLangMenu(false);
                  if (isListening) stopListeningAndProcess();
                }}
                className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-between transition-all cursor-pointer ${
                  selectedVoiceLang === lang.code
                    ? 'bg-sky-50 text-sky-700 font-bold'
                    : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                <span>{lang.label}</span>
                {selectedVoiceLang === lang.code && <Check className="h-3.5 w-3.5 text-sky-600" />}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Active Sound Detection & Equalizer HUD */}
      {isListening && (
        <div className="flex items-center gap-2 bg-slate-900/90 text-white px-3 py-1 rounded-xl shadow-lg animate-fadeIn border border-slate-700">
          {/* Real-time decibel waveform equalizer */}
          <div className="flex items-center gap-1 h-4">
            {[...Array(6)].map((_, i) => {
              const height = Math.max(3, Math.min(16, Math.sin((audioLevel + i * 20) * 0.1) * 14 + 4));
              return (
                <div
                  key={i}
                  className={`w-1 rounded-full transition-all duration-75 ${
                    isSoundDetected ? 'bg-emerald-400' : 'bg-rose-400'
                  }`}
                  style={{ height: `${height}px` }}
                ></div>
              );
            })}
          </div>

          {/* Sound detection badge */}
          {isSoundDetected ? (
            <span className="text-[11px] text-emerald-300 font-extrabold animate-pulse flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
              Hearing Voice ({audioLevel}%)
            </span>
          ) : (
            <span className="text-[11px] text-amber-300 font-medium flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping"></span>
              Speak now...
            </span>
          )}

          <button
            type="button"
            onClick={stopListeningAndProcess}
            className="text-[10px] bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold px-2 py-0.5 rounded-md transition-colors"
          >
            Done
          </button>
        </div>
      )}

      {/* Detected Language notification badge if populated */}
      {detectedLangBadge && !isListening && (
        <span className="text-[10px] font-extrabold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-md border border-emerald-300">
          Detected: {detectedLangBadge}
        </span>
      )}
    </div>
  );
}
