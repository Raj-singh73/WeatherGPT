import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Bot, 
  User, 
  Loader2, 
  Radio, 
  AlertCircle,
  Send,
  Play,
  Pause,
  Languages,
  Square,
  Trash2,
  Sparkles,
  Globe
} from 'lucide-react';
import api from '../api';
import { getTranslation } from '../translations';

const SPOKEN_LANGUAGES = [
  { code: 'auto', key: 'auto', label: '🌐 Auto-Detect Language (Any Language)', flag: '🌐' },
  { code: 'hi-IN', key: 'hi', label: 'हिन्दी (Hindi)', flag: '🇮🇳' },
  { code: 'en-IN', key: 'en', label: 'English (India)', flag: '🇬🇧' },
  { code: 'ta-IN', key: 'ta', label: 'தமிழ் (Tamil)', flag: '🇮🇳' },
  { code: 'mr-IN', key: 'mr', label: 'मराठी (Marathi)', flag: '🇮🇳' },
  { code: 'bn-IN', key: 'bn', label: 'বাংলা (Bengali)', flag: '🇮🇳' },
  { code: 'te-IN', key: 'te', label: 'తెలుగు (Telugu)', flag: '🇮🇳' },
  { code: 'gu-IN', key: 'gu', label: 'ગુજરાતી (Gujarati)', flag: '🇮🇳' },
];

export default function VoiceAssistantModal({ 
  isOpen, 
  onClose, 
  location = 'Nagpur', 
  language = 'en' 
}) {
  const t = getTranslation(language).voiceModal;

  // Selected Speech Language (defaults to auto-detect any language)
  const [selectedLang, setSelectedLang] = useState('auto');
  const [detectedLangName, setDetectedLangName] = useState('');

  // Recording & Audio States
  const [isRecording, setIsRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Live Speech-to-Text Typing States
  const [spokenText, setSpokenText] = useState('');
  const [interimText, setInterimText] = useState('');
  
  // AI Response States
  const [isLoading, setIsLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState('');
  const [aiAudioUrl, setAiAudioUrl] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [permissionError, setPermissionError] = useState('');
  const [statusMessage, setStatusMessage] = useState('');

  const isRecordingRef = useRef(false);
  const recognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioBlobRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const animFrameRef = useRef(null);
  const timerRef = useRef(null);
  const recordedAudioElemRef = useRef(null);
  const aiAudioElemRef = useRef(null);

  useEffect(() => {
    isRecordingRef.current = isRecording;
  }, [isRecording]);

  const cleanupAll = () => {
    isRecordingRef.current = false;
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch (e) {}
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try { audioContextRef.current.close(); } catch (e) {}
      audioContextRef.current = null;
    }
    
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (e) {}
      recognitionRef.current = null;
    }
    
    if (aiAudioElemRef.current) {
      aiAudioElemRef.current.pause();
      aiAudioElemRef.current = null;
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    
    if (recordedAudioElemRef.current) {
      recordedAudioElemRef.current.pause();
    }
    
    setIsRecording(false);
    setIsSpeaking(false);
    setIsPlayingAudio(false);
    setAudioLevel(0);
  };

  useEffect(() => {
    if (!isOpen) {
      cleanupAll();
    }
    return () => cleanupAll();
  }, [isOpen]);

  // Start Hardware Audio Recording + Speech Recognition
  const startRecording = async () => {
    setPermissionError('');
    setStatusMessage('Connecting microphone...');
    if (isSpeaking) stopSpeaking();

    // Reset session states
    setSpokenText('');
    setInterimText('');
    setAiResponse('');
    setAudioUrl(null);
    setDetectedLangName('');
    audioChunksRef.current = [];
    audioBlobRef.current = null;

    // 1. Get Hardware Microphone Stream
    let stream = null;
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
      console.error('Microphone access denied:', err);
      setPermissionError('Microphone access was denied. Please allow microphone permissions in your browser URL bar.');
      setIsRecording(false);
      return;
    }

    // 2. Audio Visualizer (Isolated AnalyserNode - zero speaker destination to prevent feedback muting)
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
      source.connect(analyser); // NOT connected to speakers, zero feedback!

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!isRecordingRef.current) return;
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        const avg = sum / dataArray.length;
        setAudioLevel(Math.min(100, Math.round(avg * 2.2)));
        animFrameRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();
    } catch (e) {
      console.warn('Visualizer notice:', e);
    }

    // 3. Reliable Native MediaRecorder
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

      mediaRecorder.start(200); // Emit chunk every 200ms
    } catch (mrErr) {
      console.warn('MediaRecorder notice:', mrErr);
    }

    // 4. Concurrent Live Speech Recognition (if available in browser)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recog = new SpeechRecognition();
        recog.continuous = true;
        recog.interimResults = true;
        recog.lang = selectedLang === 'auto' ? (navigator.language || 'hi-IN') : selectedLang;

        recog.onresult = (event) => {
          let fullTranscript = '';
          let interimChunk = '';

          for (let i = 0; i < event.results.length; ++i) {
            const chunk = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              fullTranscript += chunk;
            } else {
              interimChunk += chunk;
            }
          }

          if (fullTranscript) {
            setSpokenText(fullTranscript.trim());
            setInterimText('');
          } else if (interimChunk) {
            setInterimText(interimChunk.trim());
          }
        };

        recog.onerror = (event) => {
          console.warn('Speech recognition event:', event.error);
        };

        recognitionRef.current = recog;
        recog.start();
      } catch (err) {
        console.warn('Speech recognition init notice:', err);
      }
    }

    isRecordingRef.current = true;
    setIsRecording(true);
    setRecordSeconds(0);
    setStatusMessage('Listening to your voice... Speak clearly in any language!');

    timerRef.current = setInterval(() => {
      setRecordSeconds(prev => {
        if (prev >= 45) {
          stopRecordingAndProcess();
          return prev;
        }
        return prev + 1;
      });
    }, 1000);
  };

  // Asynchronous Stop Promise that GUARANTEES the final audio Blob is created
  const stopMediaRecorderAsync = () => {
    return new Promise((resolve) => {
      const mr = mediaRecorderRef.current;
      if (!mr || mr.state === 'inactive') {
        resolve(audioBlobRef.current);
        return;
      }

      mr.onstop = () => {
        if (audioChunksRef.current.length > 0) {
          const blobType = mr.mimeType || 'audio/webm';
          const blob = new Blob(audioChunksRef.current, { type: blobType });
          audioBlobRef.current = blob;
          const url = URL.createObjectURL(blob);
          setAudioUrl(url);
          resolve(blob);
        } else {
          resolve(null);
        }
      };

      try { mr.stop(); } catch (e) { resolve(audioBlobRef.current); }
    });
  };

  // Stop Recording and Process Audio
  const stopRecordingAndProcess = async (queryOverride) => {
    isRecordingRef.current = false;
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);

    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }

    setIsLoading(true);
    setStatusMessage('Capturing voice and analyzing question...');

    // Await the MediaRecorder to finish bundling the audio chunks
    const finalBlob = await stopMediaRecorderAsync();

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }

    setAudioLevel(0);

    // Now submit query
    await executeSubmission(finalBlob, queryOverride);
  };

  // Submit Query to Backend
  const executeSubmission = async (blobToUse, queryOverride) => {
    setIsLoading(true);
    setStatusMessage('Detecting language and generating intelligent weather decision...');

    const textToSubmit = queryOverride !== undefined ? queryOverride : (spokenText || interimText);
    const audioToUse = blobToUse || audioBlobRef.current;

    try {
      let res;
      // If we have recorded voice audio and user didn't tap an explicit sample chip
      if (!queryOverride && audioToUse && audioToUse.size > 300) {
        const formData = new FormData();
        formData.append('audio', audioToUse, 'voice_input.webm');
        formData.append('location', location);
        formData.append('language', selectedLang);
        if (textToSubmit) formData.append('typed_text', textToSubmit);

        res = await api.chatVoice(formData);
      } else {
        // Fallback text endpoint
        const targetLang = selectedLang === 'auto' ? 'hi' : selectedLang.split('-')[0];
        res = await api.chat({
          message: textToSubmit || `What is the weather forecast for ${location}?`,
          location: location,
          language: targetLang
        });
      }

      // Display transcribed text from backend
      if (res.transcribed_text) {
        setSpokenText(res.transcribed_text);
      }

      // Display detected language badge
      if (res.detected_language) {
        const langObj = SPOKEN_LANGUAGES.find(l => l.code === res.detected_language);
        setDetectedLangName(langObj ? langObj.label : res.detected_language);
      }

      setAiResponse(res.response);
      if (res.audio_url) {
        setAiAudioUrl(res.audio_url);
      }

      if (res.confidence > 0 && res.response) {
        setStatusMessage('Decision synthesized! Playing voice response...');
        playVoiceResponse(res.audio_url, res.speech_text || res.response, res.detected_language || selectedLang);
      } else {
        setStatusMessage(res.response || 'Please speak again or type your question.');
      }
    } catch (err) {
      console.error('Submission error:', err);
      const fallback = `In ${location}, weather decision model is active. Please try speaking again.`;
      setAiResponse(fallback);
      playVoiceResponse(null, fallback, selectedLang);
    } finally {
      setIsLoading(false);
    }
  };

  // Dual-Mode Text-To-Speech Playback (Backend High-Clarity gTTS Stream + Browser Speech Synthesis Fallback)
  const playVoiceResponse = (audioStreamUrl, text, targetLangCode) => {
    stopSpeaking();

    const cleanText = (text || '')
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/•|\-|\*/g, ' ')
      .replace(/#{1,6}\s*/g, '')
      .replace(/\[.*?\]\(.*?\)/g, '')
      .replace(/[\u{1F1E0}-\u{1F1FF}\u{1F300}-\u{1F5FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 350);

    const langCode = targetLangCode === 'auto' ? 'hi-IN' : (targetLangCode || 'hi-IN');
    const shortCode = langCode.split('-')[0];

    // Priority 1: High-fidelity studio gTTS streaming from backend (Guaranteed native pronunciation for any Indian language)
    const streamUrl = audioStreamUrl || `/api/chat/tts?language=${shortCode}&text=${encodeURIComponent(cleanText)}`;
    try {
      const audio = new Audio(streamUrl);
      aiAudioElemRef.current = audio;
      setIsSpeaking(true);

      audio.onplay = () => setIsSpeaking(true);
      audio.onended = () => {
        setIsSpeaking(false);
        aiAudioElemRef.current = null;
      };
      audio.onerror = () => {
        setIsSpeaking(false);
        aiAudioElemRef.current = null;
        speakBrowserSynthesis(cleanText, langCode);
      };

      audio.play().catch(err => {
        console.warn('Audio stream playback note:', err);
        speakBrowserSynthesis(cleanText, langCode);
      });
    } catch (err) {
      speakBrowserSynthesis(cleanText, langCode);
    }
  };

  const speakBrowserSynthesis = (cleanText, langCode) => {
    if (!('speechSynthesis' in window)) {
      setIsSpeaking(false);
      return;
    }
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = langCode;
    utterance.rate = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const matchedVoice = voices.find(v => v.lang.startsWith(langCode.slice(0, 2)));
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (aiAudioElemRef.current) {
      aiAudioElemRef.current.pause();
      aiAudioElemRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  const togglePlayRecordedAudio = () => {
    if (!recordedAudioElemRef.current) return;
    if (isPlayingAudio) {
      recordedAudioElemRef.current.pause();
      setIsPlayingAudio(false);
    } else {
      recordedAudioElemRef.current.play();
      setIsPlayingAudio(true);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] relative z-10">
        
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-2.5">
            <div className="h-9 w-9 rounded-xl bg-sky-100 border border-sky-200 flex items-center justify-center text-sky-700">
              <Radio className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-slate-900">
                WeatherGPT Multi-Lingual Voice Decision Assistant
              </h3>
              <p className="text-[11px] text-slate-500">
                Station: <strong className="text-slate-800">{location}</strong> • Speak in Any Indian Language
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              cleanupAll();
              onClose();
            }}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-4 flex-1">
          
          {/* 1. Language Mode Selector */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3.5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <Globe className="h-4 w-4 text-sky-600" />
                <span>Language Detection:</span>
              </span>
              {detectedLangName ? (
                <span className="text-[11px] font-extrabold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-md border border-emerald-300 animate-pulse">
                  Detected: {detectedLangName}
                </span>
              ) : (
                <span className="text-[11px] font-extrabold text-sky-700 bg-sky-100 px-2 py-0.5 rounded-md">
                  Active: {SPOKEN_LANGUAGES.find(l => l.code === selectedLang)?.label || 'Auto-Detect'}
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-1.5">
              {SPOKEN_LANGUAGES.map(lang => (
                <button
                  key={lang.code}
                  onClick={() => {
                    setSelectedLang(lang.code);
                    setSpokenText('');
                    setInterimText('');
                    setDetectedLangName('');
                    if (isRecording) {
                      stopRecordingAndProcess();
                    }
                  }}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 border ${
                    selectedLang === lang.code
                      ? 'bg-sky-600 text-white border-sky-600 shadow-sm scale-105'
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-sky-50 hover:text-sky-700'
                  }`}
                >
                  <span>{lang.flag}</span>
                  <span>{lang.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Microphone Permission Warning */}
          {permissionError && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-800 flex items-start gap-2.5">
              <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="block">Microphone Permission Notice:</strong>
                <span>{permissionError}</span>
              </div>
            </div>
          )}

          {/* Central Recording Orb & Action Buttons */}
          <div className="flex flex-col items-center justify-center text-center space-y-3 pt-1">
            <div className="relative">
              {isRecording && (
                <>
                  <div 
                    className="absolute -inset-4 rounded-full bg-rose-500/20 animate-ping"
                    style={{ transform: `scale(${1 + audioLevel / 50})` }}
                  ></div>
                  <div 
                    className="absolute -inset-8 rounded-full bg-sky-500/15 animate-pulse"
                    style={{ transform: `scale(${1 + audioLevel / 70})` }}
                  ></div>
                </>
              )}
              {isSpeaking && (
                <div className="absolute -inset-4 rounded-full bg-sky-500/25 animate-ping"></div>
              )}

              <button
                onClick={isRecording ? () => stopRecordingAndProcess() : startRecording}
                className={`relative z-10 h-20 w-20 rounded-full flex items-center justify-center transition-all shadow-xl cursor-pointer ${
                  isRecording
                    ? 'bg-rose-600 text-white shadow-rose-600/30 scale-110 ring-4 ring-rose-200 animate-pulse'
                    : isSpeaking
                    ? 'bg-sky-600 text-white shadow-sky-600/30'
                    : 'bg-sky-600 hover:bg-sky-700 text-white shadow-sky-600/25 hover:scale-105'
                }`}
              >
                {isRecording ? (
                  <Square className="h-8 w-8 text-white fill-white" />
                ) : isSpeaking ? (
                  <Volume2 className="h-9 w-9 animate-bounce text-white" />
                ) : (
                  <Mic className="h-9 w-9 text-white" />
                )}
              </button>
            </div>

            {/* Recording Timer & Audio Decibel Bars */}
            {isRecording ? (
              <div className="flex flex-col items-center space-y-2">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-rose-600 bg-rose-50 px-3 py-1 rounded-full border border-rose-200">
                  <span className="h-2 w-2 rounded-full bg-rose-600 animate-ping"></span>
                  <span>RECORDING: 00:{recordSeconds < 10 ? `0${recordSeconds}` : recordSeconds} / 00:45</span>
                </div>

                <div className="flex items-center gap-1.5 h-6">
                  {[...Array(11)].map((_, i) => {
                    const height = Math.max(4, Math.min(24, Math.sin((audioLevel + i * 15) * 0.1) * 20 + 8));
                    return (
                      <div
                        key={i}
                        className="w-1.5 bg-rose-500 rounded-full transition-all duration-75"
                        style={{ height: `${height}px` }}
                      ></div>
                    );
                  })}
                </div>

                {/* Stop & Analyze Button */}
                <button
                  onClick={() => stopRecordingAndProcess()}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-extrabold px-6 py-2.5 rounded-xl transition-all shadow-md cursor-pointer flex items-center gap-2"
                >
                  <Square className="h-3.5 w-3.5 fill-white" />
                  <span>Done Speaking — Analyze Now</span>
                </button>
              </div>
            ) : (
              <div>
                <h4 className="text-base font-black text-slate-900">
                  {isSpeaking ? 'WeatherGPT is speaking...' : 'Tap the microphone to speak'}
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  {statusMessage || 'Speak in Hindi, English, Tamil, Marathi, or any language. We auto-detect and answer.'}
                </p>
              </div>
            )}
          </div>

          {/* 2. Recorded Voice Playback Player */}
          {audioUrl && (
            <div className="p-3 bg-sky-50 border border-sky-200 rounded-2xl flex items-center justify-between animate-fadeIn">
              <div className="flex items-center space-x-2.5">
                <button
                  type="button"
                  onClick={togglePlayRecordedAudio}
                  className="h-8 w-8 rounded-full bg-sky-600 text-white flex items-center justify-center hover:bg-sky-700 transition-all cursor-pointer shadow-sm"
                >
                  {isPlayingAudio ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
                </button>
                <div>
                  <strong className="text-xs text-slate-900 block">Your Recorded Voice ({recordSeconds}s)</strong>
                  <span className="text-[11px] text-sky-700">Audio captured cleanly</span>
                </div>
              </div>

              <audio
                ref={recordedAudioElemRef}
                src={audioUrl}
                onEnded={() => setIsPlayingAudio(false)}
                className="hidden"
              />

              <button
                onClick={() => executeSubmission()}
                disabled={isLoading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3.5 py-1.5 rounded-xl transition-all shadow-sm cursor-pointer flex items-center gap-1.5"
              >
                <Send className="h-3 w-3" />
                <span>Re-Analyze Audio</span>
              </button>
            </div>
          )}

          {/* 3. Live Speech-to-Text Typing Container */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-sky-600" />
                <span>What You Spoke (Auto-Transcribed):</span>
              </label>
              {(spokenText || interimText) && (
                <div className="flex items-center space-x-1.5">
                  <span className="text-[10px] text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                    {(spokenText || interimText).trim().split(/\s+/).filter(Boolean).length} words
                  </span>
                  <button
                    onClick={() => {
                      setSpokenText('');
                      setInterimText('');
                    }}
                    className="text-[10px] text-slate-400 hover:text-rose-600 p-1 rounded transition-colors"
                    title="Clear text"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              )}
            </div>

            <div className="relative">
              <textarea
                rows={3}
                value={spokenText ? (interimText ? `${spokenText} ${interimText}` : spokenText) : interimText}
                onChange={(e) => setSpokenText(e.target.value)}
                placeholder="Speak in any language... The words you speak will be transcribed here."
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-3 text-xs text-slate-900 font-semibold focus:outline-none focus:border-sky-500 focus:bg-white resize-none shadow-xs"
              />
              {isRecording && (
                <span className="absolute right-3 bottom-3 text-[10px] font-bold text-rose-600 animate-pulse bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200">
                  Listening...
                </span>
              )}
            </div>

            {/* Send & Process Button */}
            <div className="flex items-center justify-between pt-1">
              <span className="text-[11px] text-slate-400">
                You can edit what you spoke above or tap Send directly.
              </span>
              <button
                onClick={() => executeSubmission()}
                disabled={isLoading}
                className="bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white text-xs font-bold px-5 py-2 rounded-xl transition-all cursor-pointer shadow-md flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-3.5 w-3.5" />
                    <span>Process & Get Solution</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Quick Sample Questions */}
          <div className="pt-2 border-t border-slate-100 space-y-1">
            <span className="text-[11px] font-bold text-slate-500 block">
              Or tap any specific question to test:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {[
                { label: '🌧️ Will it rain tomorrow?', query: `Will it rain today or tomorrow in ${location}?` },
                { label: '🌱 क्या मैं कीटनाशक का छिड़काव करूँ?', query: `क्या मैं कल अपनी फसल पर कीटनाशक का छिड़काव कर सकता हूँ?` },
                { label: '👕 What should I wear?', query: `Should I carry an umbrella or wear a jacket today in ${location}?` },
                { label: '🚗 Highway travel safe?', query: `Is it safe to drive on the highway today in ${location}?` },
                { label: '💧 फसल में पानी लगाना चाहिए?', query: `क्या मुझे आज अपनी फसल की सिंचाई करनी चाहिए?` }
              ].map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setSpokenText(chip.query);
                    executeSubmission(null, chip.query);
                  }}
                  className="text-[11px] bg-slate-100 hover:bg-sky-100 text-slate-700 hover:text-sky-800 font-semibold px-2.5 py-1 rounded-lg transition-all cursor-pointer"
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </div>

          {/* 4. AI Voice Response */}
          {isLoading && (
            <div className="flex items-center space-x-2 text-xs text-sky-700 bg-sky-50 p-4 rounded-2xl border border-sky-200 animate-pulse">
              <Loader2 className="h-4 w-4 animate-spin text-sky-600" />
              <span>Analyzing your speech and generating direct weather decision...</span>
            </div>
          )}

          {aiResponse && !isLoading && (
            <div className="bg-slate-50 border border-slate-200 p-4 rounded-2xl space-y-2.5 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="text-xs uppercase font-extrabold text-emerald-800 flex items-center gap-1.5">
                  <Bot className="h-4 w-4 text-emerald-600" />
                  <span>WeatherGPT Solution:</span>
                </span>
                <div className="flex items-center space-x-2">
                  {isSpeaking ? (
                    <button
                      onClick={stopSpeaking}
                      className="text-[11px] bg-rose-100 border border-rose-200 text-rose-800 px-2.5 py-1 rounded-full flex items-center gap-1 cursor-pointer font-bold"
                    >
                      <VolumeX className="h-3 w-3" /> Stop Voice
                    </button>
                  ) : (
                    <button
                      onClick={() => playVoiceResponse(aiAudioUrl, aiResponse, selectedLang)}
                      className="text-[11px] bg-sky-100 hover:bg-sky-200 border border-sky-200 text-sky-800 px-3 py-1 rounded-full flex items-center gap-1.5 cursor-pointer font-bold transition-all shadow-xs"
                    >
                      <Volume2 className="h-3.5 w-3.5" />
                      <span>Listen to Voice (आवाज़ सुनें)</span>
                    </button>
                  )}
                </div>
              </div>

              <p className="text-xs text-slate-800 leading-relaxed font-medium whitespace-pre-wrap max-h-48 overflow-y-auto">
                {aiResponse}
              </p>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">
            Microphone: <strong>{isRecording ? 'Active Recording' : 'Standby'}</strong>
          </span>

          <button
            onClick={() => {
              cleanupAll();
              onClose();
            }}
            className="px-5 py-2 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
