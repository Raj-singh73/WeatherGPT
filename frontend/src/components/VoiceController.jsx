import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, AlertCircle } from 'lucide-react';

export default function VoiceController({ onSpeechRecognized, textToSpeak, language = 'en' }) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setSupported(true);
    } else {
      setSupported(false);
    }
  }, []);

  const toggleListening = async () => {
    if (!supported) {
      alert('Speech recognition is not supported in this browser.');
      return;
    }

    if (isListening) {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
        streamRef.current = null;
      }
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
      setIsListening(false);
      return;
    }

    // 1. Explicitly request microphone stream from userMedia to ensure hardware permission
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
    } catch (err) {
      console.warn('Microphone permission not granted:', err);
      alert('Microphone permission is required. Please check your browser address bar permissions.');
      return;
    }

    // 2. Start Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recog = new SpeechRecognition();
    recog.continuous = false;
    recog.interimResults = false;

    const langMap = {
      hi: 'hi-IN',
      mr: 'mr-IN',
      bn: 'bn-IN',
      ta: 'ta-IN',
      te: 'te-IN',
      gu: 'gu-IN',
      en: 'en-IN'
    };
    recog.lang = langMap[language] || 'en-IN';

    recog.onstart = () => {
      setIsListening(true);
    };

    recog.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (onSpeechRecognized) {
        onSpeechRecognized(transcript);
      }
      stopListening();
    };

    recog.onerror = (event) => {
      console.warn('Speech recognition notice:', event.error);
      stopListening();
    };

    recog.onend = () => {
      stopListening();
    };

    recognitionRef.current = recog;
    try {
      recog.start();
    } catch (e) {
      console.warn('Recog start error:', e);
      stopListening();
    }
  };

  const stopListening = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }
    setIsListening(false);
  };

  const audioElemRef = useRef(null);

  const speakViaBrowser = (clean) => {
    if (!('speechSynthesis' in window)) {
      setIsSpeaking(false);
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(clean);
    const langMap = {
      hi: 'hi-IN',
      mr: 'mr-IN',
      bn: 'bn-IN',
      ta: 'ta-IN',
      te: 'te-IN',
      gu: 'gu-IN',
      en: 'en-IN'
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

  const speakText = () => {
    if (!textToSpeak) return;
    if (isSpeaking) {
      if (audioElemRef.current) {
        audioElemRef.current.pause();
        audioElemRef.current = null;
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setIsSpeaking(false);
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

    // 1. Try High-Clarity gTTS Audio Stream First
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

      audio.play().catch(err => {
        console.warn('Audio stream playback note:', err);
        speakViaBrowser(clean);
      });
    } catch (err) {
      speakViaBrowser(clean);
    }
  };

  return (
    <div className="flex items-center space-x-1.5">
      {/* Speech-to-Text Microphone Button */}
      <button
        type="button"
        onClick={toggleListening}
        disabled={!supported}
        title={supported ? (isListening ? 'Listening... Tap to stop' : 'Tap to speak query') : 'Voice input not supported in this browser'}
        className={`p-2.5 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
          !supported
            ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
            : isListening
            ? 'bg-rose-600 text-white animate-pulse shadow-md shadow-rose-600/30 ring-2 ring-rose-300'
            : 'bg-slate-100 text-slate-700 hover:bg-sky-50 hover:text-sky-700 border border-slate-200'
        }`}
      >
        {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
      </button>

      {/* Text-to-Speech Button */}
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

      {isListening && (
        <span className="text-[10px] text-rose-600 font-bold animate-pulse hidden sm:inline-block">
          Listening...
        </span>
      )}
    </div>
  );
}
