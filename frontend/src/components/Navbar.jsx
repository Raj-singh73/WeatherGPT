import React from 'react';
import { 
  CloudSun, 
  MessageSquare, 
  Calendar, 
  ShieldAlert, 
  Sprout, 
  LineChart, 
  Info, 
  MapPin, 
  Globe, 
  Layers,
  Radio
} from 'lucide-react';
import { getTranslation } from '../translations';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  selectedLocation, 
  setSelectedLocation, 
  language, 
  setLanguage,
  onOpenLocationModal,
  onOpenVoiceModal
}) {
  const t = getTranslation(language);

  const navItems = [
    { id: 'dashboard', label: t.nav.dashboard, icon: CloudSun },
    { id: 'chat', label: t.nav.chat, icon: MessageSquare },
    { id: 'forecast', label: t.nav.forecast, icon: Calendar },
    { id: 'alerts', label: t.nav.alerts, icon: ShieldAlert },
    { id: 'farmer', label: t.nav.farmer, icon: Sprout },
    { id: 'climate', label: t.nav.climate, icon: LineChart },
    { id: 'about', label: t.nav.about, icon: Info },
  ];

  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-md bg-white/95 border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-2 sm:gap-4">
          
          {/* Logo & Product Title */}
          <div 
            className="flex items-center space-x-2.5 cursor-pointer flex-shrink-0" 
            onClick={() => setActiveTab('dashboard')}
          >
            <div className="h-9 w-9 sm:h-10 sm:w-10 rounded-2xl bg-gradient-to-tr from-sky-500 via-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-sky-500/20 flex-shrink-0">
              <CloudSun className="h-5 w-5 sm:h-6 sm:w-6" />
            </div>
            <div className="flex-shrink-0">
              <div className="flex items-center space-x-1.5">
                <span className="text-base sm:text-lg font-black tracking-tight text-slate-900">
                  Weather<span className="text-sky-600">GPT</span>
                </span>
                <span className="text-[9px] uppercase font-bold tracking-widest bg-sky-100 text-sky-700 border border-sky-200 px-1.5 py-0.5 rounded-full">
                  SIH
                </span>
              </div>
              <p className="text-[10px] text-slate-500 hidden xl:block leading-tight">{t.tagline}</p>
            </div>
          </div>

          {/* Center Navigation Links (Visible on 2xl) */}
          <nav className="hidden 2xl:flex items-center space-x-1 flex-shrink">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-1 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                    isActive
                      ? 'bg-sky-50 text-sky-700 border border-sky-200 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-sky-600' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Controls: Priority Layout with flex-shrink-0 */}
          <div className="flex items-center space-x-2 sm:space-x-2.5 flex-shrink-0 ml-auto z-20">
            
            {/* 1. Language Switcher (Always visible, cannot be pushed off) */}
            <div className="flex items-center bg-white hover:bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 text-xs text-slate-800 flex-shrink-0 shadow-sm ring-1 ring-slate-100">
              <Globe className="h-4 w-4 text-sky-600 mr-1.5 flex-shrink-0" />
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                aria-label="Select interface language"
                className="bg-transparent border-none text-xs text-slate-800 font-bold focus:outline-none cursor-pointer pr-1 min-w-[95px] sm:min-w-[115px]"
              >
                <option value="en" className="bg-white text-slate-800">English</option>
                <option value="hi" className="bg-white text-slate-800">हिन्दी (Hindi)</option>
                <option value="mr" className="bg-white text-slate-800">मराठी (Marathi)</option>
                <option value="bn" className="bg-white text-slate-800">বাংলা (Bengali)</option>
                <option value="ta" className="bg-white text-slate-800">தமிழ் (Tamil)</option>
                <option value="te" className="bg-white text-slate-800">తెలుగు (Telugu)</option>
                <option value="gu" className="bg-white text-slate-800">ગુજરાતી (Gujarati)</option>
              </select>
            </div>

            {/* 2. Hierarchical Location Selector Trigger */}
            <button
              onClick={onOpenLocationModal}
              title="Select State ➔ District ➔ Block ➔ Village"
              className="flex items-center space-x-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 text-xs text-slate-800 transition-all cursor-pointer flex-shrink-0 shadow-sm"
            >
              <MapPin className="h-3.5 w-3.5 text-sky-600 flex-shrink-0" />
              <span className="font-bold max-w-[85px] sm:max-w-[130px] truncate text-slate-800">
                {selectedLocation}
              </span>
              <Layers className="h-3 w-3 text-slate-400 ml-0.5 hidden sm:inline" />
            </button>

            {/* 3. Interactive Voice Assistant Button */}
            <button
              onClick={onOpenVoiceModal}
              title="Talk & Listen with WeatherGPT"
              className="flex items-center space-x-1 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white px-2.5 sm:px-3 py-1.5 rounded-xl text-xs font-bold shadow-sm transition-all cursor-pointer flex-shrink-0"
            >
              <Radio className="h-3.5 w-3.5 animate-pulse" />
              <span className="hidden md:inline">{t.nav.voiceAssistant}</span>
            </button>

          </div>

        </div>
      </div>

      {/* Sub-Header Navigation Bar (Under 2xl) */}
      <div className="2xl:hidden flex items-center overflow-x-auto no-scrollbar border-t border-slate-200 px-2.5 py-1.5 bg-slate-50 gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs whitespace-nowrap font-medium transition-all cursor-pointer ${
                isActive
                  ? 'bg-white text-sky-700 border border-slate-200 shadow-sm font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-sky-600' : 'text-slate-500'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
}
