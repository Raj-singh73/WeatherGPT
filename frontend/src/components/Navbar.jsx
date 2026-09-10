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
  Radio,
  User,
  Home,
  Moon,
  SunMedium
} from 'lucide-react';
import { getTranslation } from '../translations';
import { getUserAccountAddress } from '../utils/addressUtils';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  selectedLocation, 
  setSelectedLocation, 
  language, 
  setLanguage,
  theme = 'light',
  onToggleTheme,
  onOpenLocationModal,
  onOpenVoiceModal,
  user = null,
  onResetToAccountAddress,
  onOpenAuthModal,
  onOpenProfileModal
}) {
  const t = getTranslation(language);
  const accountAddress = getUserAccountAddress(user);
  const isDifferentFromAccount = Boolean(
    user && accountAddress && selectedLocation?.toLowerCase() !== accountAddress?.toLowerCase()
  );

  const navItems = [
    { id: 'dashboard', label: t.nav.dashboard, icon: CloudSun },
    { id: 'chat', label: t.nav.chat, icon: MessageSquare },
    { id: 'forecast', label: t.nav.forecast, icon: Calendar },
    { id: 'alerts', label: t.nav.alerts, icon: ShieldAlert },
    { id: 'farmer', label: t.nav.farmer, icon: Sprout },
    { id: 'climate', label: t.nav.climate, icon: LineChart },
    { id: 'about', label: t.nav.about, icon: Info },
  ];

  const isDark = theme === 'dark';

  return (
    <header className={`sticky top-0 z-40 w-full backdrop-blur-md border-b shadow-sm ${isDark ? 'bg-slate-950/95 border-slate-800' : 'bg-white/95 border-slate-200'}`}>
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
                <span className={`text-base sm:text-lg font-black tracking-tight ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                  Weather<span className="text-sky-600">GPT</span>
                </span>
              </div>
              <p className={`text-[10px] hidden xl:block leading-tight ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{t.tagline}</p>
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
            
            {/* 1. Theme Switcher */}
            <button
              type="button"
              onClick={onToggleTheme}
              aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
              className={`flex items-center justify-center rounded-xl border px-2.5 py-1.5 text-xs font-bold transition-all cursor-pointer flex-shrink-0 shadow-sm ${isDark ? 'bg-slate-900 border-slate-700 text-slate-100 hover:bg-slate-800' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'}`}
            >
              {isDark ? <SunMedium className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-sky-600" />}
            </button>

            {/* 2. Language Switcher (Always visible, cannot be pushed off) */}
            <div className={`flex items-center rounded-xl px-2.5 py-1.5 text-xs flex-shrink-0 shadow-sm ring-1 ${isDark ? 'bg-slate-900 border border-slate-700 ring-slate-800 text-slate-100 hover:bg-slate-800' : 'bg-white border border-slate-200 ring-slate-100 text-slate-800 hover:bg-slate-50'}`}>
              <Globe className="h-4 w-4 text-sky-600 mr-1.5 flex-shrink-0" />
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                aria-label="Select interface language"
                className={`bg-transparent border-none text-xs font-bold focus:outline-none cursor-pointer pr-1 min-w-[95px] sm:min-w-[115px] ${isDark ? 'text-slate-100' : 'text-slate-800'}`}
              >
                <option value="en" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>English</option>
                <option value="hi" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>हिन्दी (Hindi)</option>
                <option value="mr" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>मराठी (Marathi)</option>
                <option value="bn" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>বাংলा (Bengali)</option>
                <option value="ta" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>தமிழ் (Tamil)</option>
                <option value="te" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>తెలుగు (Telugu)</option>
                <option value="gu" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>ગુજરાતી (Gujarati)</option>
                <option value="kn" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>ಕನ್ನಡ (Kannada)</option>
                <option value="ml" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>മലയാളം (Malayalam)</option>
                <option value="pa" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>ਪੰਜਾਬੀ (Punjabi)</option>
                <option value="or" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>ଓଡ଼ିଆ (Odia)</option>
                <option value="as" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>অসমীয়া (Assamese)</option>
                <option value="ur" className={isDark ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'}>اردو (Urdu)</option>
              </select>
            </div>

            {/* 3. Hierarchical Location Selector Trigger */}
            <div className="flex items-center space-x-1 flex-shrink-0">
              <button
                onClick={onOpenLocationModal}
                title="Select State ➔ District ➔ Block ➔ Village (Click to change manually)"
                className={`flex items-center space-x-1.5 rounded-xl px-2.5 py-1.5 text-xs transition-all cursor-pointer flex-shrink-0 shadow-sm ${isDark ? 'bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-100' : 'bg-white hover:bg-slate-50 border border-slate-200 text-slate-800'}`}
              >
                <MapPin className="h-3.5 w-3.5 text-sky-600 flex-shrink-0" />
                <span className={`font-bold max-w-[85px] sm:max-w-[130px] truncate ${isDark ? 'text-slate-100' : 'text-slate-800'}`}>
                  {selectedLocation}
                </span>
                <Layers className={`h-3 w-3 ml-0.5 hidden sm:inline ${isDark ? 'text-slate-400' : 'text-slate-400'}`} />
              </button>

              {isDifferentFromAccount && (
                <button
                  onClick={onResetToAccountAddress}
                  title={`Switch back to your account default address: ${accountAddress}`}
                  className="flex items-center space-x-1 bg-sky-50 hover:bg-sky-100 border border-sky-200 text-sky-700 rounded-xl px-2 py-1.5 text-xs font-bold transition-all cursor-pointer shadow-xs"
                >
                  <Home className="h-3.5 w-3.5 text-sky-600" />
                  <span className="hidden xl:inline text-[10px] uppercase tracking-wider font-extrabold">Default</span>
                </button>
              )}
            </div>

            {/* 4. Interactive Voice Assistant Button */}
            <button
              onClick={onOpenVoiceModal}
              title="Talk & Listen with WeatherGPT"
              className="flex items-center space-x-1 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white px-2.5 sm:px-3 py-1.5 rounded-xl text-xs font-bold shadow-sm transition-all cursor-pointer flex-shrink-0"
            >
              <Radio className="h-3.5 w-3.5 animate-pulse" />
              <span className="hidden md:inline">{t.nav.voiceAssistant}</span>
            </button>

            {/* 5. User Profile / Sign In Button */}
            {user ? (
              <button
                onClick={onOpenProfileModal}
                title={`Signed in as ${user.name} (${user.role || 'Farmer'})`}
                className={`flex items-center space-x-1.5 rounded-xl px-2.5 py-1 text-xs transition-all cursor-pointer flex-shrink-0 shadow-xs ring-1 ${isDark ? 'bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-100 ring-slate-700/50' : 'bg-gradient-to-r from-sky-50 to-indigo-50 hover:from-sky-100 hover:to-indigo-100 border border-sky-200/80 text-slate-800 ring-sky-200/50'}`}
              >
                <div className="h-6 w-6 rounded-full bg-gradient-to-tr from-sky-500 to-indigo-600 text-white font-black text-[10px] flex items-center justify-center flex-shrink-0 shadow-xs">
                  {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className={`font-bold max-w-[85px] sm:max-w-[110px] truncate text-[11px] ${isDark ? 'text-slate-100' : 'text-slate-800'}`}>
                  {user.name}
                </span>
                <span className={`hidden sm:inline text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded ${isDark ? 'bg-sky-900 text-sky-200' : 'bg-sky-200/70 text-sky-800'}`}>
                  {user.role === 'Farmer' ? '🌾 Kisan' : user.role || 'User'}
                </span>
              </button>
            ) : (
              <button
                onClick={onOpenAuthModal}
                title="Sign In or Create Account"
                className={`flex items-center space-x-1.5 rounded-xl px-2.5 sm:px-3 py-1.5 text-xs font-bold transition-all cursor-pointer flex-shrink-0 shadow-sm ${isDark ? 'bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-100 hover:text-white' : 'bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 hover:text-slate-900'}`}
              >
                <User className="h-3.5 w-3.5 text-sky-600" />
                <span>Sign In</span>
              </button>
            )}

          </div>

        </div>
      </div>

      {/* Sub-Header Navigation Bar (Under 2xl) */}
      <div className={`2xl:hidden flex items-center overflow-x-auto no-scrollbar border-t px-2.5 py-1.5 gap-1 ${isDark ? 'border-slate-800 bg-slate-900/90' : 'border-slate-200 bg-slate-50'}`}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs whitespace-nowrap font-medium transition-all cursor-pointer ${
                isActive
                  ? isDark
                    ? 'bg-slate-800 text-sky-300 border border-slate-700 shadow-sm font-bold'
                    : 'bg-white text-sky-700 border border-slate-200 shadow-sm font-bold'
                  : isDark
                    ? 'text-slate-300 hover:text-slate-100 hover:bg-slate-800'
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
