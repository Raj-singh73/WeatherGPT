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
  { code: 'hi-IN', key: 'hi', label: 'हिन्दी (Hindi)', flag: '🇮🇳' },
  { code: 'en-IN', key: 'en', label: 'English (India)', flag: '🇬🇧' },
  { code: 'mr-IN', key: 'mr', label: 'मराठी (Marathi)', flag: '🇮🇳' },
  { code: 'ta-IN', key: 'ta', label: 'தமிழ் (Tamil)', flag: '🇮🇳' },
  { code: 'bn-IN', key: 'bn', label: 'বাংলা (Bengali)', flag: '🇮🇳' },
  { code: 'te-IN', key: 'te', label: 'తెలుగు (Telugu)', flag: '🇮🇳' },
  { code: 'gu-IN', key: 'gu', label: 'ગુજરાતી (Gujarati)', flag: '🇮🇳' },
  { code: 'auto', key: 'auto', label: '🌐 Auto-Detect', flag: '🌐' }
];

const SAMPLE_CHIPS = {
  en: [
    { label: '🌧️ Will it rain tomorrow?', query: (loc) => `Will it rain today or tomorrow in ${loc}?` },
    { label: '🌱 Spray pesticide on crops?', query: (loc) => `Can I spray pesticide on crops tomorrow in ${loc}?` },
    { label: '👕 Can I dry clothes outside?', query: (loc) => `Can I dry clothes outdoors today in ${loc}?` },
    { label: '🚗 Safe to drive on highway?', query: (loc) => `Is it safe to drive on the highway today in ${loc}?` },
    { label: '💧 Should I irrigate my field?', query: (loc) => `Should I irrigate my crops today in ${loc}?` }
  ],
  hi: [
    { label: '🌧️ क्या कल बारिश होगी?', query: (loc) => `क्या आज या कल ${loc} में बारिश होगी?` },
    { label: '🌱 क्या कीटनाशक छिड़काव करूँ?', query: (loc) => `क्या मैं कल अपनी फसल पर कीटनाशक का छिड़काव कर सकता हूँ?` },
    { label: '👕 क्या कपड़े बाहर सुखा सकते हैं?', query: (loc) => `क्या आज ${loc} में कपड़े बाहर सुखा सकते हैं?` },
    { label: '🚗 क्या हाईवे यात्रा सुरक्षित है?', query: (loc) => `क्या आज ${loc} में हाईवे पर यात्रा करना सुरक्षित है?` },
    { label: '💧 क्या फसल में पानी लगाना चाहिए?', query: (loc) => `क्या मुझे आज अपनी फसल की सिंचाई करनी चाहिए?` }
  ],
  mr: [
    { label: '🌧️ उद्या पाऊस पडेल का?', query: (loc) => `उद्या ${loc} मध्ये पाऊस पडेल का?` },
    { label: '🌱 पिकावर औषध फवारणी करावी का?', query: (loc) => `उद्या पिकावर औषध फवारणी करावी का?` },
    { label: '👕 कपडे बाहेर वाळवावेत का?', query: (loc) => `आज ${loc} मध्ये कपडे बाहेर वाळवता येतील का?` },
    { label: '🚗 महामार्गावर प्रवास सुरक्षित आहे का?', query: (loc) => `आज महामार्गावर प्रवास करणे सुरक्षित आहे का?` },
    { label: '💧 पिकाला पाणी द्यावे का?', query: (loc) => `आज शेताला पाणी द्यावे का?` }
  ],
  ta: [
    { label: '🌧️ நாளை மழை பெய்யுமா?', query: (loc) => `நாளை ${loc}-ல் மழை பெய்யுமா?` },
    { label: '🌱 பூச்சிக்கொல்லி தெளிக்கலாமா?', query: (loc) => `நாளை பயிருக்கு பூச்சிக்கொல்லி தெளிக்கலாமா?` },
    { label: '👕 துணி காய வைக்கலாமா?', query: (loc) => `இன்று வெளியே துணி காய வைக்கலாமா?` },
    { label: '🚗 நெடுஞ்சாலை பயணம் பாதுகாப்பானதா?', query: (loc) => `இன்று நெடுஞ்சாலை பயணம் பாதுகாப்பானதா?` },
    { label: '💧 பாசனம் செய்யலாமா?', query: (loc) => `இன்று பயிருக்கு நீர் பாசனம் செய்யலாமா?` }
  ],
  te: [
    { label: '🌧️ రేపు వర్షం పడుతుందా?', query: (loc) => `రేపు ${loc}లో వర్షం పడుతుందా?` },
    { label: '🌱 మందు పిచికారీ చేయవచ్చా?', query: (loc) => `రేపు పంటపై మందు పిచికారీ చేయవచ్చా?` },
    { label: '👕 బట్టలు ఆరబెట్టవచ్చా?', query: (loc) => `ఈరోజు బయట బట్టలు ఆరబెట్టవచ్చా?` },
    { label: '🚗 ప్రయాణం సురక్షితమేనా?', query: (loc) => `ఈరోజు హైవే ప్రయాణం సురక్షితమేనా?` },
    { label: '💧 నీరు పెట్టవచ్చా?', query: (loc) => `ఈరోజు పంటకు నీరు పెట్టవచ్చా?` }
  ],
  bn: [
    { label: '🌧️ কাল কি বৃষ্টি হবে?', query: (loc) => `কাল ${loc}-এ কি বৃষ্টি হবে?` },
    { label: '🌱 কীটনাশক স্প্রে করব?', query: (loc) => `কাল ফসলে কীটনাশক স্প্রে করা যাবে কি?` },
    { label: '👕 জামাকাপড় শুকানো যাবে?', query: (loc) => `আজ কি বাইরে জামাকাপড় শুকানো যাবে?` },
    { label: '🚗 মহাসড়ক ভ্রমণ নিরাপদ?', query: (loc) => `আজ মহাসড়কে ভ্রমণ কি নিরাপদ?` },
    { label: '💧 সেচ দেওয়া উচিত?', query: (loc) => `আজ কি ফসলে সেচ দেওয়া উচিত?` }
  ],
  gu: [
    { label: '🌧️ કાલે વરસાદ પડશે?', query: (loc) => `કાલે ${loc}માં વરસાદ પડશે?` },
    { label: '🌱 દવાનો છંટકાવ કરવો?', query: (loc) => `કાલે પાક પર દવાનો છંટકાવ કરી શકાય?` },
    { label: '👕 કપડાં સૂકવી શકાય?', query: (loc) => `આજે બહાર કપડાં સૂકવવા યોગ્ય છે?` },
    { label: '🚗 હાઇવે મુસાફરી સલામત?', query: (loc) => `આજે હાઇવે પર મુસાફરી કરવી સલામત છે?` },
    { label: '💧 પાકને પાણી પાવું?', query: (loc) => `આજે પાકને પિયત આપવું જોઈએ?` }
  ]
};

export default function VoiceAssistantModal({ 
  isOpen, 
  onClose, 
  location = 'Nagpur', 
  language = 'en' 
}) {
  const t = getTranslation(language).voiceModal;

  // Selected Speech Language (defaults to current app language)
  const [selectedLang, setSelectedLang] = useState('hi-IN');
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
  const [isSoundDetected, setIsSoundDetected] = useState(false);
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
    setIsSoundDetected(false);
  };

  useEffect(() => {
    if (isOpen) {
      // Sync selectedLang with app language upon opening
      const langMap = {
        hi: 'hi-IN',
        mr: 'mr-IN',
        bn: 'bn-IN',
        ta: 'ta-IN',
        te: 'te-IN',
        gu: 'gu-IN',
        en: 'en-IN'
      };
      if (language && langMap[language]) {
        setSelectedLang(langMap[language]);
      }
    } else {
      cleanupAll();
    }
    return () => cleanupAll();
  }, [isOpen, language]);

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

    // 2. Audio Visualizer (Isolated AnalyserNode)
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
        const lvl = Math.min(100, Math.round(avg * 2.2));
        setAudioLevel(lvl);
        setIsSoundDetected(lvl > 10);
        animFrameRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();
    } catch (e) {
      console.warn('Visualizer notice:', e);
    }

    // 3. MediaRecorder
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

      mediaRecorder.start(200);
    } catch (mrErr) {
      console.warn('MediaRecorder notice:', mrErr);
    }

    // 4. Live Speech Recognition
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
        const appLangCode = langMap[language] || 'hi-IN';
        recog.lang = selectedLang === 'auto' ? appLangCode : selectedLang;

        recog.onresult = (event) => {
          let fullTranscript = '';
          let interimChunk = '';

          for (let i = 0; i < event.results.length; ++i) {
            const chunk = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              fullTranscript += chunk + ' ';
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
    setStatusMessage('Listening to your voice... Speak clearly in your chosen language!');

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

    const finalBlob = await stopMediaRecorderAsync();

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }

    setAudioLevel(0);
    await executeSubmission(finalBlob, queryOverride);
  };

  // Submit Query to Backend with 100% Respect for Chosen Language
  const executeSubmission = async (blobToUse, queryOverride) => {
    setIsLoading(true);
    setStatusMessage('Generating weather decision in chosen language...');

    const textToSubmit = queryOverride !== undefined ? queryOverride : (spokenText || interimText);
    const audioToUse = blobToUse; // ONLY use live recorded blob, NEVER fall back to stale audioBlobRef

    // Determine target language from selectedLang
    const targetLang = selectedLang === 'auto' ? (language || 'hi') : selectedLang.split('-')[0];

    try {
      let res;
      // If we have live recorded voice audio from recording button
      if (audioToUse && audioToUse.size > 300) {
        const formData = new FormData();
        formData.append('audio', audioToUse, 'voice_input.webm');
        formData.append('location', location);
        formData.append('language', selectedLang);
        if (textToSubmit) formData.append('typed_text', textToSubmit);

        res = await api.chatVoice(formData);
      } else {
        // Direct text submission (from typed text or tapped question chips)
        res = await api.chat({
          message: textToSubmit || `What is the weather forecast for ${location}?`,
          location: location,
          language: targetLang
        });
      }

      if (res.transcribed_text) {
        setSpokenText(res.transcribed_text);
      }

      const activeLangObj = SPOKEN_LANGUAGES.find(l => l.code === (res.detected_language || selectedLang)) ||
                            SPOKEN_LANGUAGES.find(l => l.key === targetLang);
      setDetectedLangName(activeLangObj ? activeLangObj.label : targetLang);

      setAiResponse(res.response);
      if (res.audio_url) {
        setAiAudioUrl(res.audio_url);
      }

      if (res.response) {
        setStatusMessage(`Decision synthesized! Playing voice in ${activeLangObj?.label || targetLang}...`);
        playVoiceResponse(res.audio_url, res.speech_text || res.response, targetLang);
      } else {
        setStatusMessage('Please choose a question or speak your query.');
      }
    } catch (err) {
      console.error('Submission error:', err);
      const fallback = `In ${location}, weather decision model is active.`;
      setAiResponse(fallback);
      playVoiceResponse(null, fallback, targetLang);
    } finally {
      setIsLoading(false);
    }
  };

  // High-Clarity indic gTTS stream playback with browser synthesis fallback
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

    const langCode = targetLangCode === 'auto' ? (language || 'hi') : (targetLangCode || 'hi');
    const shortCode = langCode.includes('-') ? langCode.split('-')[0] : langCode;

    // High-fidelity studio gTTS streaming from backend
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
        speakBrowserSynthesis(cleanText, shortCode);
      };

      audio.play().catch(err => {
        console.warn('Audio stream playback note:', err);
        speakBrowserSynthesis(cleanText, shortCode);
      });
    } catch (err) {
      speakBrowserSynthesis(cleanText, shortCode);
    }
  };

  const speakBrowserSynthesis = (cleanText, langCode) => {
    if (!('speechSynthesis' in window)) {
      setIsSpeaking(false);
      return;
    }
    window.speechSynthesis.cancel();

    const fullCodeMap = {
      hi: 'hi-IN', mr: 'mr-IN', bn: 'bn-IN',
      ta: 'ta-IN', te: 'te-IN', gu: 'gu-IN', en: 'en-IN'
    };
    const bcp47 = fullCodeMap[langCode] || `${langCode}-IN`;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = bcp47;
    utterance.rate = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const matchedVoice = voices.find(v => v.lang.startsWith(langCode));
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

  // Determine current active question chips based on chosen language
  const currentShortLang = selectedLang === 'auto' ? (language || 'hi') : selectedLang.split('-')[0];
  const activeChips = SAMPLE_CHIPS[currentShortLang] || SAMPLE_CHIPS['en'];

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
                Station: <strong className="text-slate-800">{location}</strong> • Speaks & Responds in Your Chosen Language
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
                <span>Select Response Language:</span>
              </span>
              <span className="text-[11px] font-extrabold text-sky-700 bg-sky-100 px-2.5 py-0.5 rounded-md border border-sky-200">
                Active: {SPOKEN_LANGUAGES.find(l => l.code === selectedLang)?.label || 'Auto-Detect'}
              </span>
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
                    audioBlobRef.current = null;
                    setAudioUrl(null);
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
                <div className="flex flex-wrap items-center justify-center gap-2">
                  <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-rose-600 bg-rose-50 px-3 py-1 rounded-full border border-rose-200">
                    <span className="h-2 w-2 rounded-full bg-rose-600 animate-ping"></span>
                    <span>00:{recordSeconds < 10 ? `0${recordSeconds}` : recordSeconds} / 00:45</span>
                  </div>

                  {isSoundDetected ? (
                    <div className="flex items-center gap-1.5 text-xs font-extrabold text-emerald-800 bg-emerald-100 px-3 py-1 rounded-full border border-emerald-300 animate-pulse shadow-xs">
                      <span className="h-2 w-2 rounded-full bg-emerald-600 animate-ping"></span>
                      <span>🎙️ Sound Detected ({audioLevel}%)</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800 bg-amber-50 px-3 py-1 rounded-full border border-amber-300">
                      <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse"></span>
                      <span>🎧 Speak near mic</span>
                    </div>
                  )}
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
                  {isSpeaking ? 'WeatherGPT is speaking...' : 'Tap mic or choose a question below'}
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  {statusMessage || `Output will be generated and spoken in ${SPOKEN_LANGUAGES.find(l => l.code === selectedLang)?.label || 'chosen language'}.`}
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
                  <span className="text-[11px] text-sky-700">Audio captured</span>
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

          {/* 3. Live Speech-to-Text / Question Input Box */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-sky-600" />
                <span>Question for WeatherGPT:</span>
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
                      audioBlobRef.current = null;
                      setAudioUrl(null);
                    }}
                    className="text-[10px] text-slate-400 hover:text-rose-600 p-1 rounded transition-colors cursor-pointer"
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
                onChange={(e) => {
                  setSpokenText(e.target.value);
                  audioBlobRef.current = null;
                }}
                placeholder="Ask any weather question... It will be answered in your chosen language."
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
                Tap questions below or type and press Process.
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

          {/* 4. Quick Sample Questions Tailored to Chosen Language */}
          <div className="pt-2 border-t border-slate-100 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-600 flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-amber-500" />
                <span>Tap any question to get instant solution & voice:</span>
              </span>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                {SPOKEN_LANGUAGES.find(l => l.code === selectedLang)?.label || 'Chosen Language'}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {activeChips.map((chip, idx) => {
                const queryText = typeof chip.query === 'function' ? chip.query(location) : chip.query;
                return (
                  <button
                    key={idx}
                    onClick={() => {
                      audioBlobRef.current = null;
                      setAudioUrl(null);
                      setSpokenText(queryText);
                      executeSubmission(null, queryText);
                    }}
                    className="text-[11px] bg-white hover:bg-sky-50 text-slate-700 hover:text-sky-800 font-semibold px-3 py-1.5 rounded-xl border border-slate-200 transition-all cursor-pointer shadow-2xs flex items-center gap-1"
                  >
                    {chip.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 5. AI Voice & Text Solution */}
          {isLoading && (
            <div className="flex items-center space-x-2 text-xs text-sky-700 bg-sky-50 p-4 rounded-2xl border border-sky-200 animate-pulse">
              <Loader2 className="h-4 w-4 animate-spin text-sky-600" />
              <span>Synthesizing actionable weather decision in {SPOKEN_LANGUAGES.find(l => l.code === selectedLang)?.label || 'chosen language'}...</span>
            </div>
          )}

          {aiResponse && !isLoading && (
            <div className="bg-slate-50 border border-slate-200 p-4 rounded-2xl space-y-2.5 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="text-xs uppercase font-extrabold text-emerald-800 flex items-center gap-1.5">
                  <Bot className="h-4 w-4 text-emerald-600" />
                  <span>WeatherGPT Solution ({SPOKEN_LANGUAGES.find(l => l.code === selectedLang)?.label || 'Chosen Language'}):</span>
                </span>
                <div className="flex items-center space-x-2">
                  {isSpeaking ? (
                    <button
                      onClick={stopSpeaking}
                      className="text-[11px] bg-rose-100 border border-rose-200 text-rose-800 px-2.5 py-1 rounded-full flex items-center gap-1 cursor-pointer font-bold animate-pulse"
                    >
                      <VolumeX className="h-3 w-3" /> Stop Voice
                    </button>
                  ) : (
                    <button
                      onClick={() => playVoiceResponse(aiAudioUrl, aiResponse, selectedLang)}
                      className="text-[11px] bg-sky-100 hover:bg-sky-200 border border-sky-300 text-sky-800 px-3 py-1 rounded-full flex items-center gap-1.5 cursor-pointer font-bold transition-all shadow-xs"
                    >
                      <Volume2 className="h-3.5 w-3.5" />
                      <span>🔊 Listen to Voice ({SPOKEN_LANGUAGES.find(l => l.code === selectedLang)?.label.split(' ')[0] || 'Play'})</span>
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
            Language: <strong className="text-slate-800">{SPOKEN_LANGUAGES.find(l => l.code === selectedLang)?.label}</strong>
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
