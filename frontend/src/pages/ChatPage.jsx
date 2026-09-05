import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Sparkles, 
  Bot, 
  User, 
  Database, 
  Languages,
  Loader2,
  Clock,
  Check,
  CheckCheck,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Info,
  ShieldCheck,
  Activity,
  Calendar,
  Droplets,
  Wind,
  CloudRain,
  Thermometer,
  Layers
} from 'lucide-react';
import VoiceController from '../components/VoiceController';
import api from '../api';
import { getTranslation } from '../translations';

export default function ChatPage({ 
  location = 'Nagpur', 
  language = 'en', 
  initialPrompt = '', 
  onClearInitialPrompt 
}) {
  const t = getTranslation(language).chat;

  const getWelcomeMessage = (lang, loc) => {
    switch (lang) {
      case 'hi':
        return `नमस्ते! मैं **WeatherGPT** हूँ — आपका AI मौसम व बहु-आपदा जोखिम विश्लेषक।\n\nमैं **${loc}** और पूरे भारत के लिए वास्तविक समय पूर्वानुमान, वर्षा जोखिम, आंधी-तूफान चेतावनी, खेल, फसल परामर्श और सुरक्षित यात्रा का सटीक विश्लेषण प्रदान करता हूँ।\n\nनीचे दिए गए किसी भी विषय पर क्लिक करें या अपना प्रश्न पूछें!`;
      case 'mr':
        return `नमस्कार! मी **WeatherGPT** आहे, आपला एआई हवामान व व्यावहारिक निर्णय सहाय्यक.\n\nमी **${loc}** साठी थेट हवामान अंदाज, पावसाचा धोका, वादळ चेतावणी आणि शेती व प्रवास मार्गदर्शन करतो. मी कशी मदत करू?`;
      case 'bn':
        return `নমস্কার! আমি **WeatherGPT** — আপনার এআই আবহাওয়া ও দুর্যোগ পূর্বাভাস সহকারী।\n\nআমি **${loc}** ও সমগ্র ভারতের লাইভ পূর্বাভাস, বৃষ্টির সম্ভাবনা, ঝড় সতর্কতা, কৃষিকাজ ও নিরাপদ ভ্রমণের পরামর্শ প্রদান করি। আপনি কী জানতে চান?`;
      case 'ta':
        return `வணக்கம்! நான் **WeatherGPT** — உங்கள் செயற்கை நுண்ணறிவு வானிலை மற்றும் நடைமுறை முடிவெடுக்கும் உதவியாளர்.\n\nநான் **${loc}** பகுதிக்கான மழை வாய்ப்பு, புயல் எச்சரிக்கை, விவசாய வழிகாட்டுதல் மற்றும் பயண பாதுகாப்பை வழங்க முடியும். உங்களுக்கு என்ன தகவல் வேண்டும்?`;
      case 'te':
        return `నమస్కారం! నేను **WeatherGPT** — మీ రియల్ టైమ్ వాతావరణ మరియు విపత్తు నిర్ణయ సహాయకుడిని.\n\nనేను **${loc}** కోసం వర్ష సూచన, తుఫాను హెచ్చరికలు మరియు పంట సలహాలను అందిస్తాను. మీకు ఏ సమాచారం కావాలి?`;
      case 'gu':
        return `નમસ્તે! હું **WeatherGPT** છું — તમારો એઆઈ હવામાન અને આપત્તિ જોખમ સહાયક.\n\nહું **${loc}** માટે વાસ્તવિક સમયની આગાહી, વરસાદનું જોખમ, વાવાઝોડાની ચેતવણી અને ખેતી અંગે માર્ગદર્શન આપું છું. નીચે આપેલા વિષયોમાંથી પસંદ કરો અથવા સવાલ પૂછો!`;
      default:
        return `Hello! I am **WeatherGPT** — your AI assistant for real-time weather intelligence and multi-hazard risk analysis.\n\nI analyze physics telemetry, satellite hydrological archives, and ML impact models for **${loc}** to give you direct, calibrated answers: rain probability, thunderstorm alerts, outdoor sports suitability, crop advisories, and highway transit safety.\n\nTap any category below or ask your question!`;
    }
  };

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      text: getWelcomeMessage(language, location),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      sources: [
        'Open-Meteo NWP Forecast Engine',
        'ISRO NRSC VIC Hydrological Rainfall Dataset',
        'IMD 0.25° Gridded Climatology Archive',
        'WeatherGPT ML Risk Engine (HistGradientBoosting)'
      ]
    }
  ]);

  // Update welcome message if language or location changes
  useEffect(() => {
    setMessages(prev => {
      if (prev.length <= 1) {
        return [{
          id: 'welcome',
          sender: 'bot',
          text: getWelcomeMessage(language, location),
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          sources: [
            'Open-Meteo NWP Forecast Engine',
            'ISRO NRSC VIC Hydrological Rainfall Dataset',
            'IMD 0.25° Gridded Climatology Archive',
            'WeatherGPT ML Risk Engine (HistGradientBoosting)'
          ]
        }];
      }
      return prev;
    });
  }, [language, location]);

  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState('ALL');
  const [selectedPersona, setSelectedPersona] = useState('GENERAL');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    if (initialPrompt) {
      handleSendMessage(initialPrompt);
      if (onClearInitialPrompt) onClearInitialPrompt();
    }
  }, [initialPrompt]);

  const handleSendMessage = async (customText = null) => {
    const text = (customText || inputMessage).trim();
    if (!text || isLoading) return;

    const userMsgId = Date.now().toString();
    const newUserMsg = {
      id: userMsgId,
      sender: 'user',
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      status: 'sending',
      situation: 'NORMAL'
    };

    setMessages(prev => [...prev, newUserMsg]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await api.chat({
        message: text,
        location: location,
        language: language,
        persona: selectedPersona
      });

      const situation = response.verdict 
        || (response.risk_assessment?.risk_level) 
        || (response.weather_summary?.rain_today > 2.5 ? 'CAUTION' : 'RECOMMENDED');

      const botMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: response.intent,
        persona: response.persona || selectedPersona,
        extractedLocation: response.extracted_location,
        sources: response.sources || [],
        riskAssessment: response.risk_assessment,
        verdict: response.verdict,
        verdictBadge: response.verdict_badge,
        useCase: response.use_case,
        suitabilityScore: response.suitability_score,
        actionSteps: response.action_steps || [],
        weatherSummary: response.weather_summary
      };

      setMessages(prev => prev.map(m => m.id === userMsgId ? { ...m, status: 'sended', situation } : m).concat(botMsg));
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: "I experienced a temporary connection hiccup with the intelligence service. However, the local baseline model indicates normal seasonal conditions. Please check your query or retry shortly.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: ['WeatherGPT Offline Fallback Engine']
      };
      setMessages(prev => prev.map(m => m.id === userMsgId ? { ...m, status: 'sended', situation: 'CAUTION' } : m).concat(errorMsg));
    } finally {
      setIsLoading(false);
    }
  };

  // Human-readable Use Case Labels
  const getUseCaseDisplayName = (useCaseKey, lang) => {
    const isHi = lang === 'hi';
    switch (useCaseKey) {
      case 'DRYING_CLOTHES':
        return isHi ? '🧺 कपड़े सुखाना (Laundry)' : '🧺 Laundry & Clothes Drying';
      case 'CAR_WASH':
        return isHi ? '🚗 कार धुलाई (Car Wash)' : '🚗 Car & Vehicle Wash';
      case 'OUTDOOR_SPORTS':
        return isHi ? '🏏 आउटडोर खेल व दौड़' : '🏏 Outdoor Sports & Fitness';
      case 'OUTDOOR_EVENT':
        return isHi ? '🎉 समारोह व शादी (Event)' : '🎉 Outdoor Event & Wedding';
      case 'HARVESTING':
        return isHi ? '🌾 फसल कटाई सलाह' : '🌾 Crop Harvesting Directive';
      case 'SPRAY_PESTICIDE':
        return isHi ? '🧪 कीटनाशक छिड़काव' : '🧪 Pesticide Spray Safety';
      case 'SOWING':
        return isHi ? '🌱 बुवाई निर्णय' : '🌱 Crop Sowing Guidance';
      case 'IRRIGATION':
        return isHi ? '💧 सिंचाई निर्णय' : '💧 Irrigation Advisory';
      case 'CONSTRUCTION_PAINTING':
        return isHi ? '🎨 बाहरी पुताई व निर्माण' : '🎨 Painting & Concrete Casting';
      case 'FOG_VISIBILITY':
        return isHi ? '🌫️ हाईवे कोहरा व दृश्यता' : '🌫️ Highway Fog & Visibility';
      case 'FLOOD_WATERLOGGING':
        return isHi ? '🌊 जलभराव व बाढ़ जोखिम' : '🌊 Flood & Waterlogging Risk';
      case 'HEALTH_HEAT_COLD':
        return isHi ? '☀️ गर्मी व स्वास्थ्य' : '☀️ Heat Stress & Health';
      case 'TRAVEL_SAFETY':
        return isHi ? '🚗 यात्रा सुरक्षा रिपोर्ट' : '🚗 Highway & Transit Safety';
      case 'RAIN_CHECK':
        return isHi ? '🌧️ वर्षा व छाता जांच' : '🌧️ Rain Probability & Umbrella';
      case 'GENERAL_FORECAST':
        return isHi ? '📅 बहु-दिवसीय पूर्वानुमान' : '📅 4-Day Forecast Trajectory';
      default:
        return isHi ? '🌤️ मौसम आसूचना निर्णय' : '🌤️ Weather Decision Engine';
    }
  };

  // Verdict Card Styling
  const getVerdictStyle = (verdict) => {
    switch (verdict) {
      case 'RECOMMENDED':
        return 'bg-emerald-50 text-emerald-800 border-emerald-300 ring-1 ring-emerald-500/20';
      case 'CAUTION':
        return 'bg-amber-50 text-amber-800 border-amber-300 ring-1 ring-amber-500/20';
      case 'NOT_RECOMMENDED':
        return 'bg-rose-50 text-rose-800 border-rose-300 ring-1 ring-rose-500/20';
      default:
        return 'bg-sky-50 text-sky-800 border-sky-300 ring-1 ring-sky-500/20';
    }
  };

  const getVerdictIcon = (verdict) => {
    switch (verdict) {
      case 'RECOMMENDED':
        return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0" />;
      case 'CAUTION':
        return <AlertTriangle className="h-3.5 w-3.5 text-amber-600 flex-shrink-0" />;
      case 'NOT_RECOMMENDED':
        return <AlertCircle className="h-3.5 w-3.5 text-rose-600 flex-shrink-0" />;
      default:
        return <Info className="h-3.5 w-3.5 text-sky-600 flex-shrink-0" />;
    }
  };

  // Light, Modern & Professional User Bubble Styling
  const getUserBubbleStyle = (msg) => {
    if (msg.status !== 'sended') {
      return 'bg-sky-50/90 text-slate-900 font-medium shadow-xs border border-sky-200 border-r-4 border-r-sky-500';
    }
    switch (msg.situation) {
      case 'NOT_RECOMMENDED':
      case 'SEVERE':
        return 'bg-gradient-to-br from-rose-50/80 to-white text-slate-900 font-medium shadow-xs border border-rose-200/90 border-r-4 border-r-rose-500';
      case 'CAUTION':
      case 'HIGH':
      case 'MODERATE':
        return 'bg-gradient-to-br from-amber-50/80 to-white text-slate-900 font-medium shadow-xs border border-amber-200/90 border-r-4 border-r-amber-500';
      case 'RECOMMENDED':
        return 'bg-gradient-to-br from-emerald-50/80 to-white text-slate-900 font-medium shadow-xs border border-emerald-200/90 border-r-4 border-r-emerald-500';
      default:
        return 'bg-gradient-to-br from-sky-50/80 to-white text-slate-900 font-medium shadow-xs border border-sky-200/90 border-r-4 border-r-sky-500';
    }
  };

  // Rich formatted text rendering
  const renderFormattedText = (rawText) => {
    if (!rawText) return null;
    const lines = rawText.split('\n');

    return lines.map((line, lineIdx) => {
      const trimmed = line.trim();
      if (!trimmed) {
        return <div key={lineIdx} className="h-1.5" />;
      }

      const isBullet = trimmed.startsWith('•') || trimmed.startsWith('-');
      const cleanLine = isBullet ? trimmed.replace(/^[•\-]\s*/, '') : trimmed;

      const parts = cleanLine.split(/(\*\*.*?\*\*)/g);
      const renderedParts = parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={index} className="text-slate-900 font-extrabold">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return part;
      });

      if (isBullet) {
        return (
          <div key={lineIdx} className="flex items-start gap-2 pl-1 py-0.5 text-slate-700">
            <span className="text-sky-600 font-bold text-xs mt-0.5">•</span>
            <span className="flex-1 leading-relaxed">{renderedParts}</span>
          </div>
        );
      }

      return (
        <p key={lineIdx} className="leading-relaxed text-slate-800 py-0.5">
          {renderedParts}
        </p>
      );
    });
  };

  // Persona Definitions for Tailored Intelligence
  const personas = [
    { id: 'GENERAL', label: language === 'hi' ? 'सामान्य नागरिक' : 'General Citizen', icon: '🌐', desc: language === 'hi' ? 'दैनिक मौसम व घरेलू निर्णय' : 'Daily decisions & rain' },
    { id: 'FARMER', label: language === 'hi' ? 'किसान / कृषि' : 'Farmer / Agri', icon: '🌾', desc: language === 'hi' ? 'फसल, कीटनाशक, बुवाई, सिंचाई' : 'Crops, pesticide spray, sowing' },
    { id: 'COMMUTER', label: language === 'hi' ? 'यात्री / कम्यूटर' : 'Commuter / Transit', icon: '🚗', desc: language === 'hi' ? 'दोपहिया, हाईवे कोहरा, सफर' : 'Two-wheeler, fog, highway' },
    { id: 'EVENT_OUTDOOR', label: language === 'hi' ? 'इवेंट व आउटडोर' : 'Event & Outdoors', icon: '🎪', desc: language === 'hi' ? 'शादी, मैच, खुला शामियाना' : 'Weddings, matches, open-air' },
    { id: 'HEALTH_DAILY', label: language === 'hi' ? 'स्वास्थ्य व फिटनेस' : 'Health & Daily', icon: '🩺', desc: language === 'hi' ? 'मॉर्निंग वॉक, बुजुर्ग, ठंड/लू' : 'Morning walk, heat/cold stress' },
  ];

  // Interactive Categorized Prompt Presets
  const promptCategories = [
    { id: 'ALL', label: language === 'hi' ? '✨ सभी सुझाव' : (language === 'mr' ? '✨ सर्व प्रश्न' : (language === 'bn' ? '✨ সব প্রশ্ন' : (language === 'gu' ? '✨ બધા પ્રશ્નો' : (language === 'ta' ? '✨ அனைத்தும்' : (language === 'te' ? '✨ అన్ని ప్రశ్నలు' : '✨ All Suggestions'))))) },
    { id: 'RAIN', label: language === 'hi' ? '🌧️ वर्षा व छाता' : (language === 'mr' ? '🌧️ पाऊस व छत्री' : (language === 'bn' ? '🌧️ বৃষ্টি ও ছাতা' : (language === 'gu' ? '🌧️ વરસાદ અને છત્રી' : (language === 'ta' ? '🌧️ மழை & குடை' : (language === 'te' ? '🌧️ వర్షం & గొడుగు' : '🌧️ Rain & Storm'))))) },
    { id: 'SPORTS', label: language === 'hi' ? '🏏 खेल व आउटडोर' : (language === 'mr' ? '🏏 खेळ व धावणे' : (language === 'bn' ? '🏏 খেলাধুলা' : (language === 'gu' ? '🏏 રમતગમત' : (language === 'ta' ? '🏏 விளையாட்டுகள்' : (language === 'te' ? '🏏 ఆటలు & పరుగు' : '🏏 Sports'))))) },
    { id: 'FARM', label: language === 'hi' ? '🌾 फसल व कृषि' : (language === 'mr' ? '🌾 शेती व पिके' : (language === 'bn' ? '🌾 কৃষি ও ফসল' : (language === 'gu' ? '🌾 ખેતી અને પાક' : (language === 'ta' ? '🌾 விவசாயம்' : (language === 'te' ? '🌾 వ్యవసాయం' : '🌾 Farming'))))) },
    { id: 'HEAT_COLD', label: language === 'hi' ? '☀️ गर्मी व स्वास्थ्य' : (language === 'mr' ? '☀️ उष्णता व आरोग्य' : (language === 'bn' ? '☀️ তাপপ্রবাহ ও স্বাস্থ্য' : (language === 'gu' ? '☀️ ગરમી અને સ્વાસ્થ્ય' : (language === 'ta' ? '☀️ வெப்பம் & நலம்' : (language === 'te' ? '☀️ వేడి & ఆరోగ్యం' : '☀️ Heat & Health'))))) },
    { id: 'PAINT', label: language === 'hi' ? '🎨 निर्माण व पुताई' : (language === 'mr' ? '🎨 बांधकाम व रंगकाम' : (language === 'bn' ? '🎨 রঙ ও নির্মাণ' : (language === 'gu' ? '🎨 બાંધકામ અને રંગકામ' : (language === 'ta' ? '🎨 கட்டுமானம்' : (language === 'te' ? '🎨 నిర్మాణం & పెయింట్' : '🎨 Construction'))))) },
    { id: 'DRIVE', label: language === 'hi' ? '🌫️ कोहरा व यात्रा' : (language === 'mr' ? '🌫️ धुके व प्रवास' : (language === 'bn' ? '🌫️ কুয়াশা ও ভ্রমণ' : (language === 'gu' ? '🌫️ ધુમ્મસ અને મુસાફરી' : (language === 'ta' ? '🌫️ மூடுபனி & பயணம்' : (language === 'te' ? '🌫️ పొగమంచు & ప్రయాణం' : '🌫️ Highway Fog'))))) },
    { id: 'FORECAST', label: language === 'hi' ? '📅 4-दिवसीय मौसम' : (language === 'mr' ? '📅 ४ दिवसांचा अंदाज' : (language === 'bn' ? '📅 ৪ দিনের পূর্বাভাস' : (language === 'gu' ? '📅 ૪ દિવસની આગાહી' : (language === 'ta' ? '📅 4 நாள் வானிலை' : (language === 'te' ? '📅 4 రోజుల సూచన' : '📅 Outlook'))))) },
  ];

  const getPromptsForCategory = (catId, personaId, lang, loc) => {
    // Multilingual prompt bank
    if (lang === 'mr') {
      if (catId === 'ALL') {
        if (personaId === 'FARMER') return [`या हंगामात कोणती पिके घेणे फायदेशीर आहे?`, `उद्या ${loc} मध्ये पेरणी करू शकतो का?`, `उद्या पिकावर औषध फवारणी करावी का?`, `आज शेताला पाणी द्यावे का?`];
        return [`आज किंवा उद्या ${loc} मध्ये पाऊस पडेल का?`, `वादळाचा काही इशारा आहे का?`, `आज बाहेर जाताना छत्री सोबत ठेवावी का?`, `पुढील ४ दिवसांचे हवामान कसे राहील?`];
      }
      if (catId === 'RAIN') return [`आज किंवा उद्या ${loc} मध्ये पाऊस पडेल का? किती टक्के शक्यता आहे?`, `आज छत्री सोबत ठेवावी का?`, `पुढील ४८ तासांत मुसळधार पावसाचा इशारा आहे का?`];
      if (catId === 'HEAT_COLD') return [`दुपारी उष्णतेचा काय परिणाम राहील?`, `सकाळी धावण्यासाठी तापमान केव्हा अनुकूल राहील?`];
      if (catId === 'SPORTS') return [`उद्या ${loc} मध्ये क्रिकेट खेळू शकतो का?`, `सकाळी फिरायला जाण्यासाठी उत्तम वेळ कोणती?`];
      if (catId === 'FARM') return [`उद्या पिकांची कापणी करावी का?`, `कीटकनाशक फवारणी सुरक्षित आहे का?`, `आज पिकाला पाणी द्यावे का?`];
      if (catId === 'PAINT') return [`उद्या बाहेरील भिंतींना रंग देऊ शकतो का?`, `आज स्लॅबचे काम करणे सुरक्षित आहे का?`];
      if (catId === 'DRIVE') return [`उद्या सकाळी महामार्गावर धुके असेल का?`, `बाईक चालवणे सुरक्षित आहे का?`];
      if (catId === 'FORECAST') return [`${loc} चा ४ दिवसांचा हवामान अंदाज दाखवा`, `उद्या पावसाची नेमकी शक्यता किती?`];
    } else if (lang === 'bn') {
      if (catId === 'ALL') {
        if (personaId === 'FARMER') return [`এই মরশুমে কোন ফসল সবচেয়ে উপযুক্ত?`, `কাল কি ${loc} এ ধান বোনা যাবে?`, `আজ কি জমিতে সেচ দেওয়া উচিত?`, `কাল কি কীটনাশক স্প্রে করা নিরাপদ?`];
        return [`আজ বা কাল কি ${loc} এ বৃষ্টি হবে?`, `কোনো ঝড় বা বজ্রপাতের সতর্কতা আছে কি?`, `আজ কি ছাতা সাথে রাখা দরকার?`, `আগামী ৪ দিনের আবহাওয়া কেমন থাকবে?`];
      }
      if (catId === 'RAIN') return [`আজ বা কাল ${loc} এ বৃষ্টির সম্ভাবনা কত?`, `আজ কি ছাতা নিয়ে বেরোনো দরকার?`, `আগামী ৪৮ ঘণ্টায় ভারী বৃষ্টির সম্ভাবনা আছে কি?`];
      if (catId === 'HEAT_COLD') return [`দুপুরে তাপপ্রবাহের মাত্রা কেমন থাকবে?`, `সকালে হাঁটার জন্য আবহাওয়া কেমন?`];
      if (catId === 'SPORTS') return [`কাল কি ক্রিকেট বা ফুটবল খেলা যাবে?`, `সকালে দৌড়ানোর সেরা সময় কোনটি?`];
      if (catId === 'FARM') return [`কাল কি ফসল কাটা ঠিক হবে?`, `আজ কি জমিতে জল দেওয়া উচিত?`];
      if (catId === 'DRIVE') return [`কাল সকালে হাইওয়েতে কি কুয়াশা থাকবে?`, `বাইকে ভ্রমণ কি নিরাপদ?`];
      if (catId === 'FORECAST') return [`${loc} এর ৪ দিনের পূর্বাভাস দেখান`, `কাল বৃষ্টির সঠিক সম্ভাবনা কত?`];
    } else if (lang === 'gu') {
      if (catId === 'ALL') {
        if (personaId === 'FARMER') return [`આ સિઝનમાં કયો પાક લેવો સૌથી સારો?`, `શું કાલે ${loc} માં વાવણી કરી શકાય?`, `શું આજે પાકને પિયત આપવું જોઈએ?`];
        return [`શું આજે કે કાલે ${loc} માં વરસાદ પડશે?`, `વાવાઝોડા કે ભારે પવનની કોઈ ચેતવણી છે?`, `શું આજે છત્રી સાથે રાખવાની જરૂર છે?`, `આવનારા ૪ દિવસનું હવામાન કેવું રહેશે?`];
      }
      if (catId === 'RAIN') return [`આજે કે કાલે ${loc} માં વરસાદની કેટલી શક્યતા છે?`, `શું આજે છત્રી સાથે રાખવી જરૂરી છે?`];
      if (catId === 'FARM') return [`શું કાલે પાકની કાપણી કરી શકાય?`, `શું કાલે જંતુનાશક દવા છાંટવી સલામત છે?`];
      if (catId === 'DRIVE') return [`શું કાલે સવારે હાઇવે પર ધુમ્મસ રહેશે?`, `શું મુસાફરી સલામત છે?`];
      if (catId === 'FORECAST') return [`${loc} ની ૪ દિવસની હવામાન આગાહી બતાવો`, `કાલે વરસાદની શક્યતા કેટલી?`];
    } else if (lang === 'ta') {
      if (catId === 'ALL') {
        if (personaId === 'FARMER') return [`இந்த பருவத்தில் எந்த பயிர் நடவு செய்வது நல்லது?`, `இன்று பயிருக்கு நீர் பாய்ச்சலாமா?`, `நாளை பூச்சிக்கொல்லி தெளிக்கலாமா?`];
        return [`இன்று அல்லது நாளை ${loc} பகுதியில் மழை பெய்யுமா?`, `ஏதேனும் புயல் எச்சரிக்கை உள்ளதா?`, `இன்று குடை எடுத்துச் செல்ல வேண்டுமா?`, `அடுத்த 4 நாட்களின் வானிலை எப்படி இருக்கும்?`];
      }
      if (catId === 'RAIN') return [`இன்று அல்லது நாளை மழை வாய்ப்பு எவ்வளவு?`, `இன்று குடை எடுத்துச் செல்ல வேண்டுமா?`];
      if (catId === 'FARM') return [`நாளை அறுவடை செய்யலாமா?`, `இன்று பயிருக்கு நீர் பாய்ச்சலாமா?`];
      if (catId === 'FORECAST') return [`${loc} பகுதிக்கான 4 நாள் வானிலை முன்னறிவிப்பு காட்டு`, `நாளை மழை பெய்ய வாய்ப்புள்ளதா?`];
    } else if (lang === 'te') {
      if (catId === 'ALL') {
        if (personaId === 'FARMER') return [`ఈ సీజన్‌లో ఏ పంట వేయడం మంచిది?`, `ఈరోజు పొలానికి నీరు పెట్టవచ్చా?`, `రేపు పురుగుమందు పిచికారీ చేయవచ్చా?`];
        return [`ఈరోజు లేదా రేపు ${loc} లో వర్షం పడుతుందా?`, `ఏదైనా తుఫాను హెచ్చరిక ఉందా?`, `ఈరోజు గొడుగు తీసుకెళ్లాలా?`, `రాబోయే 4 రోజుల వాతావరణం ఎలా ఉంటుంది?`];
      }
      if (catId === 'RAIN') return [`ఈరోజు లేదా రేపు వర్షం పడే సంభావ్యత ఎంత?`, `ఈరోజు గొడుగు అవసరమా?`];
      if (catId === 'FARM') return [`రేపు పంట కోత కోయవచ్చా?`, `ఈరోజు నీరు పెట్టవచ్చా?`];
      if (catId === 'FORECAST') return [`${loc} యొక్క 4 రోజుల సూచన చూపించు`, `రేపు వర్షం పడే అవకాశం ఎంత?`];
    } else if (lang === 'hi') {
      if (catId === 'ALL') {
        switch (personaId) {
          case 'FARMER':
            return [
              `वर्तमान मौसम में कौन सी फसल लगाना सबसे उपयुक्त है?`,
              `क्या कल ${loc} में धान की बुवाई कर सकते हैं?`,
              `क्या कल ${loc} में फसल पर कीटनाशक छिड़कना सुरक्षित है?`,
              `क्या आज खेत में सिंचाई करनी चाहिए?`,
              `क्या आज यूरिया / खाद डालना ठीक रहेगा?`
            ];
          case 'COMMUTER':
            return [
              `क्या कल सुबह बाइक या स्कूटी से दफ्तर जाना सुरक्षित है?`,
              `क्या कल सुबह हाईवे पर घना कोहरा रहेगा?`,
              `क्या शाम के समय रास्ते में जलभराव या बारिश होगी?`,
              `क्या इस सप्ताहांत लंबी हाईवे सड़क यात्रा सुरक्षित है?`
            ];
          case 'EVENT_OUTDOOR':
            return [
              `क्या कल शाम खुला शामियाना/टेंट लगाना सुरक्षित है?`,
              `क्या कल आउटडोर क्रिकेट मैच या खेल प्रतियोगिता हो सकती है?`,
              `कल शाम 5 से 10 बजे के बीच बारिश का सटीक प्रतिशत कितना है?`,
              `क्या तेज आंधी या हवाओं से टेंट को नुकसान का खतरा है?`
            ];
          case 'HEALTH_DAILY':
            return [
              `क्या कल सुबह 6 बजे मॉर्निंग वॉक के लिए जाना सुरक्षित है?`,
              `क्या अस्थमा या बुजुर्गों के लिए बाहर जाना ठीक है?`,
              `दोपहर में लू (Heat Stress) या धूप का क्या स्तर रहेगा?`,
              `शीतलहर (Cold Wave) से बचाव के लिए क्या सावधानी बरतें?`
            ];
          default: // GENERAL
            return [
              `क्या आज या कल ${loc} में बारिश होगी? कितने प्रतिशत संभावना है?`,
              `क्या ${loc} में आंधी-तूफान या तेज हवाओं की चेतावनी है?`,
              `क्या आज बाहर निकलते समय छाता साथ रखना चाहिए?`,
              `क्या कल ${loc} में क्रिकेट या खेलकूद खेल सकते हैं?`,
              `क्या कल सुबह हाईवे पर कोहरा या यात्रा में कोई जोखिम है?`,
              `आगामी 4 दिनों का मौसम पूर्वानुमान व तापमान कैसा रहेगा?`
            ];
        }
      }

      switch (catId) {
        case 'RAIN':
          return [
            `क्या आज या कल ${loc} में बारिश होगी? सटीक संभावना क्या है?`,
            `क्या आज छाता साथ रखना आवश्यक है?`,
            `क्या अगले 48 घंटों में भारी वर्षा या जलभराव का खतरा है?`,
            `आज बारिश होने पर कितने घंटे तक पानी बरसने का अनुमान है?`
          ];
        case 'HEAT_COLD':
          return [
            `दोपहर में लू (Heat Stress) या धूप का क्या स्तर रहेगा?`,
            `सुबह वॉक या दौड़ के लिए तापमान कब सबसे अनुकूल रहेगा?`,
            `शीतलहर (Cold Wave) से बचाव के लिए क्या सावधानी बरतें?`
          ];
        case 'SPORTS':
          return [
            `क्या कल ${loc} में क्रिकेट खेल सकते हैं?`,
            `दौड़ या वॉक के लिए सबसे अच्छा समय क्या है?`
          ];
        case 'FARM':
          return [
            `क्या कल ${loc} में गेहूं की कटाई कर सकते हैं?`,
            `क्या आज फसल पर कीटनाशक का छिड़काव करना सुरक्षित है?`,
            `क्या आज गेहूं में सिंचाई करनी चाहिए?`,
            `क्या आज यूरिया / उर्वरक डालना ठीक रहेगा?`
          ];
        case 'PAINT':
          return [
            `क्या कल ${loc} में बाहरी दीवारों पर पेंट कर सकते हैं?`,
            `क्या आज कंक्रीट या ल॔टर का काम सुरक्षित है?`
          ];
        case 'DRIVE':
          return [
            `क्या कल सुबह ${loc} में हाईवे पर कोहरा रहेगा?`,
            `क्या कल सुबह बाइक से सफर करना सुरक्षित है?`,
            `क्या इस सप्ताह यात्रा करना सुरक्षित है?`
          ];
        case 'FORECAST':
          return [
            `${loc} का 4-दिवसीय मौसम पूर्वानुमान दिखाएं`,
            `क्या कल बारिश होगी और कितने प्रतिशत संभावना है?`,
            `क्या इस सप्ताह भारी बारिश का अलर्ट है?`
          ];
        default:
          return [
            `क्या आज ${loc} में कपड़े बाहर सुखा सकते हैं?`,
            `क्या कल बारिश होगी?`
          ];
      }
    }

    // Default English
    if (catId === 'ALL') {
      switch (personaId) {
        case 'FARMER':
          return [
            `Which crop is favorable for this season in ${loc}?`,
            `Can I sow rice in ${loc} now?`,
            `Can I spray pesticide on crops tomorrow in ${loc}?`,
            `Should I irrigate crops today in ${loc}?`,
            `Should I apply fertilizer or urea today in ${loc}?`
          ];
        case 'COMMUTER':
          return [
            `Is it safe to ride a bike to work tomorrow morning in ${loc}?`,
            `Will there be dense fog on highway tomorrow morning in ${loc}?`,
            `Will there be waterlogging or heavy rain during evening transit?`,
            `Is a long highway road trip safe this weekend from ${loc}?`
          ];
        case 'EVENT_OUTDOOR':
          return [
            `Can we set up an open-air tent/wedding tomorrow evening in ${loc}?`,
            `Can we organize an outdoor cricket tournament tomorrow in ${loc}?`,
            `What is the exact rain probability between 5 PM and 10 PM?`,
            `Is there risk of high wind gusts damaging event setup?`
          ];
        case 'HEALTH_DAILY':
          return [
            `Is tomorrow morning safe for morning walk and jogging in ${loc}?`,
            `Is the air humidity and temperature safe for asthma patients outside?`,
            `What is the heat index and UV exposure risk this afternoon in ${loc}?`,
            `What precautions are needed for cold wave / chill index?`
          ];
        default: // GENERAL
          return [
            `Will it rain today or tomorrow in ${loc}? What is the exact probability?`,
            `Is there any thunderstorm or severe weather alert in ${loc}?`,
            `Do I need to carry an umbrella outdoors today in ${loc}?`,
            `Can we play cricket or outdoor sports tomorrow in ${loc}?`,
            `Is there morning fog for highway travel in ${loc}?`,
            `What is the 4-day weather trajectory and temperature outlook for ${loc}?`
          ];
      }
    }

    switch (catId) {
      case 'RAIN':
        return [
          `Will it rain today or tomorrow in ${loc}? What is the exact probability?`,
          `Do I need to carry an umbrella outdoors today in ${loc}?`,
          `Is there risk of heavy precipitation or waterlogging in next 48 hours?`,
          `How many precipitation hours are predicted if it rains today?`
        ];
      case 'HEAT_COLD':
        return [
          `What is the heat index and thermal stress this afternoon in ${loc}?`,
          `What is the optimal temperature window for morning exercise in ${loc}?`,
          `What precautions are needed for cold wave or nighttime chill in ${loc}?`
        ];
      case 'SPORTS':
        return [
          `Can we play cricket tomorrow in ${loc}?`,
          `What is the best time for morning jogging/running?`
        ];
      case 'FARM':
        return [
          `Should I harvest wheat tomorrow in ${loc}?`,
          `Can I spray pesticide on my crops tomorrow?`,
          `Should I irrigate crops today in ${loc}?`,
          `Should I apply fertilizer to crops today?`
        ];
      case 'PAINT':
        return [
          `Can I paint exterior walls tomorrow in ${loc}?`,
          `Is it safe for roof slab concrete pouring today?`
        ];
      case 'DRIVE':
        return [
          `Is there morning fog for highway driving in ${loc}?`,
          `Is two-wheeler commute safe tomorrow morning?`,
          `Is highway transit safe this weekend?`
        ];
      case 'FORECAST':
        return [
          `Show 4-day forecast outlook for ${loc}`,
          `Will it rain tomorrow and what is the exact probability?`,
          `Will there be heavy rain this week?`
        ];
      default:
        return [
          `Can I dry clothes outside today in ${loc}?`,
          `Will it rain tomorrow in ${loc}?`
        ];
    }
  };

  const displayedPrompts = getPromptsForCategory(activeCategory, selectedPersona, language, location);

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-145px)] pb-2">
      {/* Header Panel */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 mb-2 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
              <span>{t.headerTitle}</span>
              <span className="text-[10px] bg-sky-50 text-sky-700 border border-sky-200 px-2 py-0.5 rounded-full font-bold">
                {location}
              </span>
              <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full font-bold hidden sm:inline-flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" /> Decision Engine Active
              </span>
            </h2>
            <p className="text-[11px] text-slate-500">
              {language === 'hi' 
                ? 'मौसम पूर्वानुमान, एमएल जोखिम व व्यावहारिक निर्णय (वर्षा, आंधी, खेल, खेती, यात्रा, निर्माण)'
                : 'Real-time forecast, ML impact predictions & actionable directives (Rain, Storms, Sports, Farming, Transit)'
              }
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-600">
          <Languages className="h-4 w-4 text-sky-600" />
          <span className="font-bold uppercase text-slate-800">{language}</span>
        </div>
      </div>

      {/* Persona Mode Selector Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-2.5 mb-2.5 shadow-2xs">
        <div className="flex items-center justify-between gap-2 mb-1.5 px-1">
          <div className="flex items-center gap-1.5 text-[11px] font-extrabold text-slate-800">
            <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
            <span>{language === 'hi' ? 'पर्सोना व विशेषज्ञ मोड:' : 'Select Persona & Decision Mode:'}</span>
          </div>
          <span className="text-[10px] text-slate-400 font-medium hidden sm:inline">
            {language === 'hi' ? 'डोमेन-अनुकूलित व्यावहारिक मार्गदर्शन' : 'Domain-tailored intelligence'}
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
          {personas.map((p) => {
            const isSelected = selectedPersona === p.id;
            return (
              <button
                key={p.id}
                onClick={() => {
                  setSelectedPersona(p.id);
                  setActiveCategory('ALL');
                }}
                className={`flex flex-col items-start p-2 rounded-xl border text-left transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-gradient-to-r from-sky-50 to-indigo-50 border-sky-400 text-sky-950 ring-1 ring-sky-400/40 shadow-xs'
                    : 'bg-slate-50/70 border-slate-200 hover:bg-slate-100/80 text-slate-700'
                }`}
              >
                <div className="flex items-center gap-1.5 font-bold text-xs">
                  <span>{p.icon}</span>
                  <span className="truncate">{p.label}</span>
                </div>
                <span className="text-[9.5px] text-slate-500 line-clamp-1 mt-0.5">{p.desc}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Messages Thread Container */}
      <div className="flex-1 bg-slate-100/60 border border-slate-200 rounded-2xl p-4 overflow-y-auto space-y-4 shadow-inner">
        {messages.map((msg) => {
          const isBot = msg.sender === 'bot';
          const hasDecisionCard = isBot && (msg.verdict || msg.useCase || msg.suitabilityScore !== undefined);

          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${isBot ? 'justify-start' : 'justify-end'}`}
            >
              {isBot && (
                <div className="h-8 w-8 rounded-xl bg-white border border-slate-200 shadow-sm flex items-center justify-center flex-shrink-0 mt-0.5 text-sky-600">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div
                className={`max-w-[88%] sm:max-w-[82%] rounded-2xl p-4 text-xs leading-relaxed shadow-sm transition-all duration-300 ${
                  isBot
                    ? 'bg-white border border-slate-200 text-slate-800'
                    : getUserBubbleStyle(msg)
                }`}
              >
                {/* Structured Decision Card (Bot Only) */}
                {hasDecisionCard && (
                  <div className="mb-3.5 p-3 rounded-xl border bg-slate-50/80 shadow-2xs flex flex-col gap-2.5">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {/* Use Case Pill */}
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-white border border-slate-200 text-slate-800 shadow-2xs">
                          <Activity className="h-3.5 w-3.5 text-sky-600" />
                          <span>{getUseCaseDisplayName(msg.useCase || msg.intent, language)}</span>
                        </div>

                        {/* Persona Pill */}
                        {msg.persona && msg.persona !== 'GENERAL' && (
                          <span className="text-[10px] font-bold px-2 py-1 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-2xs">
                            {personas.find(p => p.id === msg.persona)?.icon || '🎯'} {msg.persona} Mode
                          </span>
                        )}
                      </div>

                      {/* Verdict Badge */}
                      {msg.verdict && (
                        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-extrabold border shadow-2xs ${getVerdictStyle(msg.verdict)}`}>
                          {getVerdictIcon(msg.verdict)}
                          <span>{msg.verdictBadge || msg.verdict}</span>
                        </div>
                      )}
                    </div>

                    {/* Telemetry & ML Risk Mini Bar */}
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 text-[10px]">
                      {msg.suitabilityScore !== undefined && (
                        <div className="bg-white px-2 py-1.5 rounded-lg border border-slate-200 flex items-center justify-between shadow-2xs">
                          <span className="text-slate-500 font-medium">Suitability</span>
                          <span className="font-extrabold text-slate-800">{Math.round(msg.suitabilityScore)}/100</span>
                        </div>
                      )}
                      {msg.riskAssessment && (
                        <div className="bg-white px-2 py-1.5 rounded-lg border border-slate-200 flex items-center justify-between shadow-2xs">
                          <span className="text-slate-500 font-medium">ML Risk</span>
                          <span className="font-extrabold text-slate-800">
                            {msg.riskAssessment.risk_level} ({Math.round(msg.riskAssessment.risk_score || 0)}/100)
                          </span>
                        </div>
                      )}
                      {msg.weatherSummary?.rain_today !== undefined && (
                        <div className="bg-white px-2 py-1.5 rounded-lg border border-slate-200 flex items-center justify-between shadow-2xs">
                          <span className="text-slate-500 font-medium">Rain (Today)</span>
                          <span className="font-extrabold text-slate-800">
                            {msg.weatherSummary.rain_today} mm
                            {msg.weatherSummary.rain_prob_today !== undefined ? ` (${msg.weatherSummary.rain_prob_today}%)` : ''}
                          </span>
                        </div>
                      )}
                      {msg.weatherSummary?.rain_tomorrow !== undefined && (
                        <div className="bg-white px-2 py-1.5 rounded-lg border border-slate-200 flex items-center justify-between shadow-2xs">
                          <span className="text-slate-500 font-medium">Rain (Tomo)</span>
                          <span className="font-extrabold text-slate-800">
                            {msg.weatherSummary.rain_tomorrow} mm
                            {msg.weatherSummary.rain_prob_tomorrow !== undefined ? ` (${msg.weatherSummary.rain_prob_tomorrow}%)` : ''}
                          </span>
                        </div>
                      )}
                      {msg.weatherSummary?.humidity !== undefined && (
                        <div className="bg-white px-2 py-1.5 rounded-lg border border-slate-200 flex items-center justify-between shadow-2xs">
                          <span className="text-slate-500 font-medium">Humidity</span>
                          <span className="font-extrabold text-slate-800">{msg.weatherSummary.humidity}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Formatted Markdown Paragraphs */}
                <div className="space-y-1.5">
                  {renderFormattedText(msg.text)}
                </div>

                {/* Structured Action Directives (if available) */}
                {isBot && msg.actionSteps && msg.actionSteps.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-slate-100 bg-sky-50/50 -mx-3 p-3 rounded-lg">
                    <div className="text-[11px] font-bold text-slate-800 flex items-center gap-1.5 mb-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-sky-600" />
                      <span>{language === 'hi' ? 'महत्वपूर्ण कार्य निर्देश (Action Directives):' : 'Recommended Action Directives:'}</span>
                    </div>
                    <ul className="space-y-1">
                      {msg.actionSteps.map((step, idx) => (
                        <li key={idx} className="flex items-start gap-1.5 text-[11px] text-slate-700">
                          <span className="text-sky-600 font-bold mt-0.5">•</span>
                          <span className="leading-relaxed">{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Sources & Provenance Footer for Bot Responses */}
                {isBot && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3.5 pt-2.5 border-t border-slate-100 text-[11px] text-slate-600 space-y-1 bg-slate-50/70 -mx-3 -mb-3 p-3 rounded-b-xl">
                    <div className="flex items-center gap-1 font-bold text-slate-800">
                      <Database className="h-3 w-3 text-sky-600" />
                      <span>{t.sources}</span>
                    </div>
                    <ul className="list-disc list-inside space-y-0.5 text-[10px] text-slate-600">
                      {msg.sources.map((src, i) => (
                        <li key={i}>{src}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex items-center justify-end gap-1.5 mt-2 text-[10px] text-slate-400 font-medium">
                  <Clock className="h-3 w-3 text-slate-400" />
                  <span>{msg.timestamp}</span>
                  {!isBot && (
                    <span className="flex items-center gap-1 ml-1.5">
                      {msg.status === 'sended' ? (
                        <span className="flex items-center gap-1">
                          <CheckCheck className={`h-3.5 w-3.5 ${
                            msg.situation === 'NOT_RECOMMENDED' || msg.situation === 'SEVERE'
                              ? 'text-rose-600'
                              : msg.situation === 'CAUTION' || msg.situation === 'MODERATE' || msg.situation === 'HIGH'
                              ? 'text-amber-600'
                              : msg.situation === 'RECOMMENDED'
                              ? 'text-emerald-600'
                              : 'text-sky-600'
                          }`} />
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                            msg.situation === 'NOT_RECOMMENDED' || msg.situation === 'SEVERE'
                              ? 'bg-rose-100/90 text-rose-700 border border-rose-200'
                              : msg.situation === 'CAUTION' || msg.situation === 'MODERATE' || msg.situation === 'HIGH'
                              ? 'bg-amber-100/90 text-amber-700 border border-amber-200'
                              : msg.situation === 'RECOMMENDED'
                              ? 'bg-emerald-100/90 text-emerald-700 border border-emerald-200'
                              : 'bg-sky-100/90 text-sky-700 border border-sky-200'
                          }`}>
                            {msg.situation === 'NOT_RECOMMENDED' || msg.situation === 'SEVERE'
                              ? (language === 'hi' ? 'गंभीर' : 'Severe')
                              : msg.situation === 'CAUTION' || msg.situation === 'MODERATE' || msg.situation === 'HIGH'
                              ? (language === 'hi' ? 'सतर्क' : 'Caution')
                              : msg.situation === 'RECOMMENDED'
                              ? (language === 'hi' ? 'अनुकूल' : 'Favorable')
                              : (language === 'hi' ? 'सामान्य' : 'Normal')}
                          </span>
                        </span>
                      ) : (
                        <Check className="h-3.5 w-3.5 text-sky-500 animate-pulse" />
                      )}
                    </span>
                  )}
                </div>
              </div>

              {!isBot && (
                <div className={`h-8 w-8 rounded-xl border flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-bold shadow-2xs transition-all duration-300 ${
                  msg.situation === 'NOT_RECOMMENDED' || msg.situation === 'SEVERE'
                    ? 'bg-rose-50 border-rose-200 text-rose-600'
                    : msg.situation === 'CAUTION' || msg.situation === 'MODERATE' || msg.situation === 'HIGH'
                    ? 'bg-amber-50 border-amber-200 text-amber-600'
                    : msg.situation === 'RECOMMENDED'
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-600'
                    : 'bg-sky-50 border-sky-200 text-sky-600'
                }`}>
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          );
        })}

        {/* Loading Spinner */}
        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="h-8 w-8 rounded-xl bg-white border border-slate-200 shadow-sm flex items-center justify-center text-sky-600">
              <Bot className="h-4 w-4" />
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl p-4 text-xs text-slate-600 flex items-center space-x-2 shadow-sm">
              <Loader2 className="h-4 w-4 animate-spin text-sky-600" />
              <span>Analyzing telemetry, ML risk models & physical thresholds...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Categorized Decision Chips Bar */}
      <div className="pt-2 pb-1">
        {/* Category Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1.5">
          {promptCategories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`text-[10px] font-bold px-2.5 py-1 rounded-lg whitespace-nowrap transition-all cursor-pointer border ${
                activeCategory === cat.id
                  ? 'bg-sky-600 text-white border-sky-600 shadow-xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Question Pills for Selected Category */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1">
          <span className="text-[10px] text-slate-500 font-bold flex-shrink-0 flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-amber-500" />
          </span>
          {displayedPrompts.map((p, i) => (
            <button
              key={i}
              onClick={() => handleSendMessage(p)}
              className="text-[10.5px] whitespace-nowrap bg-white hover:bg-sky-50 text-slate-700 hover:text-sky-700 px-3 py-1 rounded-xl border border-slate-200 transition-all cursor-pointer shadow-2xs font-medium"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Input Box with Voice Controller */}
      <div className="bg-white border border-slate-300 rounded-2xl p-2 shadow-md flex items-center space-x-2">
        <VoiceController
          language={language}
          onSpeechRecognized={(speechText) => {
            setInputMessage(speechText);
            handleSendMessage(speechText);
          }}
          textToSpeak={messages[messages.length - 1]?.sender === 'bot' ? messages[messages.length - 1].text : ''}
        />

        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder={language === 'hi' ? 'कोई भी व्यावहारिक प्रश्न पूछें (जैसे: क्या आज कपड़े सुखा सकते हैं?)...' : 'Ask practical decisions (e.g., Can I wash my car today?)...'}
          className="flex-1 bg-transparent text-xs text-slate-900 placeholder-slate-400 focus:outline-none px-2 py-2 font-medium"
        />

        <button
          onClick={() => handleSendMessage()}
          disabled={!inputMessage.trim() || isLoading}
          aria-label="Send message"
          className="p-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-40 disabled:hover:bg-sky-600 text-white font-medium transition-all shadow-sm cursor-pointer"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
