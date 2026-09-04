import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import ForecastPage from './pages/ForecastPage';
import AlertsPage from './pages/AlertsPage';
import FarmerPage from './pages/FarmerPage';
import ClimatePage from './pages/ClimatePage';
import AboutPage from './pages/AboutPage';
import LocationHierarchyModal from './components/LocationHierarchyModal';
import VoiceAssistantModal from './components/VoiceAssistantModal';
import AuthModal from './components/AuthModal';
import UserProfileModal from './components/UserProfileModal';
import api from './api';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { getTranslation } from './translations';
import { getUserAccountAddress } from './utils/addressUtils';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  // User Authentication & Profile State
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('weathergpt_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  // Synchronous location resolution on app mount
  const getStartupLocation = () => {
    try {
      const manualLoc = localStorage.getItem('weathergpt_manual_location') || sessionStorage.getItem('weathergpt_manual_location');
      if (manualLoc) return manualLoc;
      const saved = localStorage.getItem('weathergpt_user');
      if (saved) {
        const u = JSON.parse(saved);
        const addr = getUserAccountAddress(u);
        if (addr) return addr;
      }
    } catch {
      // fallback
    }
    return 'Nagpur';
  };

  const initialLoc = getStartupLocation();
  const [selectedLocation, setSelectedLocation] = useState(initialLoc);

  // Instant 0ms cached weather for the active location:
  const [currentWeather, setCurrentWeather] = useState(() => {
    try {
      const cached = localStorage.getItem('weathergpt_cached_weather_' + (initialLoc || 'nagpur').toLowerCase());
      return cached ? JSON.parse(cached) : null;
    } catch {
      return null;
    }
  });

  const [forecast, setForecast] = useState(() => {
    try {
      const cached = localStorage.getItem('weathergpt_cached_forecast_' + (initialLoc || 'nagpur').toLowerCase());
      return cached ? JSON.parse(cached) : null;
    } catch {
      return null;
    }
  });

  const [selectedCoordinates, setSelectedCoordinates] = useState(() => {
    try {
      const cached = localStorage.getItem('weathergpt_cached_weather_' + (initialLoc || 'nagpur').toLowerCase());
      if (cached) {
        const parsed = JSON.parse(cached);
        if (parsed.latitude && parsed.longitude) {
          return { lat: parsed.latitude, lon: parsed.longitude };
        }
      }
    } catch {}
    return null;
  });

  const [language, setLanguage] = useState('en');
  const [alerts, setAlerts] = useState([]);
  const [initialChatPrompt, setInitialChatPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasConnectionError, setHasConnectionError] = useState(false);

  // Modals
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  // Restore authenticated session from token on startup
  useEffect(() => {
    const token = localStorage.getItem('weathergpt_token');
    if (token) {
      api.getMe()
        .then((userData) => {
          setCurrentUser(userData);
          localStorage.setItem('weathergpt_user', JSON.stringify(userData));

          // ONLY automatically switch to account address if user has not chosen a manual location
          const manualLoc = localStorage.getItem('weathergpt_manual_location') || sessionStorage.getItem('weathergpt_manual_location');
          if (!manualLoc) {
            const addr = getUserAccountAddress(userData);
            if (addr) {
              setSelectedLocation(addr);
            }
          }
          if (userData.preferred_language) {
            setLanguage(userData.preferred_language);
          }
        })
        .catch(() => {
          localStorage.removeItem('weathergpt_token');
          localStorage.removeItem('weathergpt_user');
          setCurrentUser(null);
        });
    }
  }, []);

  const handleAuthSuccess = (userData) => {
    setCurrentUser(userData);
    localStorage.setItem('weathergpt_user', JSON.stringify(userData));
    // Clear any previous manual location so newly logged-in account address takes effect immediately
    localStorage.removeItem('weathergpt_manual_location');
    sessionStorage.removeItem('weathergpt_manual_location');
    const userAddr = getUserAccountAddress(userData);
    if (userAddr) {
      setSelectedLocation(userAddr);
    }
    if (userData.preferred_language) {
      setLanguage(userData.preferred_language);
    }
  };

  const handleUserUpdated = (updatedUser) => {
    setCurrentUser(updatedUser);
    localStorage.setItem('weathergpt_user', JSON.stringify(updatedUser));
    const newAddr = getUserAccountAddress(updatedUser);
    if (newAddr) {
      localStorage.removeItem('weathergpt_manual_location');
      sessionStorage.removeItem('weathergpt_manual_location');
      setSelectedLocation(newAddr);
    }
    if (updatedUser.preferred_language) {
      setLanguage(updatedUser.preferred_language);
    }
  };

  const handleResetToAccountAddress = () => {
    const addr = getUserAccountAddress(currentUser);
    if (addr) {
      localStorage.removeItem('weathergpt_manual_location');
      sessionStorage.removeItem('weathergpt_manual_location');
      setSelectedLocation(addr);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (e) {
      console.warn('Logout API failed, clearing local state', e);
    }
    localStorage.removeItem('weathergpt_token');
    localStorage.removeItem('weathergpt_user');
    localStorage.removeItem('weathergpt_manual_location');
    sessionStorage.removeItem('weathergpt_manual_location');
    setCurrentUser(null);
    setSelectedLocation('Nagpur');
    setIsProfileModalOpen(false);
  };

  const t = getTranslation(language);

  const loadData = (locName = selectedLocation, lat = null, lon = null, explicitState = null) => {
    setLoading(true);
    setHasConnectionError(false);

    // Only pass lat/lon if they were explicitly provided for this specific location
    const targetLat = lat != null ? lat : null;
    const targetLon = lon != null ? lon : null;

    Promise.allSettled([
      api.getCurrentWeather(locName, targetLat, targetLon),
      api.getForecast(locName, 7, targetLat, targetLon),
      api.getAlerts(locName, targetLat, targetLon)
    ])
      .then(([currRes, foreRes, altRes]) => {
        let loadedAny = false;
        if (currRes.status === 'fulfilled' && currRes.value) {
          const resolvedState = (currRes.value.state && currRes.value.state !== 'India')
            ? currRes.value.state
            : (explicitState || currRes.value.state || '');
          const weatherPayload = {
            ...currRes.value,
            location: locName,
            state: resolvedState
          };
          setCurrentWeather(weatherPayload);
          localStorage.setItem('weathergpt_cached_weather_' + locName.toLowerCase(), JSON.stringify(weatherPayload));
          if (currRes.value.latitude && currRes.value.longitude) {
            setSelectedCoordinates({ lat: currRes.value.latitude, lon: currRes.value.longitude });
          }
          loadedAny = true;
        }
        if (foreRes.status === 'fulfilled' && foreRes.value) {
          setForecast(foreRes.value);
          localStorage.setItem('weathergpt_cached_forecast_' + locName.toLowerCase(), JSON.stringify(foreRes.value));
          loadedAny = true;
        }
        if (altRes.status === 'fulfilled' && altRes.value) {
          setAlerts(altRes.value.alerts || []);
        }

        if (!loadedAny) {
          setHasConnectionError(true);
        }
      })
      .catch(err => {
        console.error('Data loading error:', err);
        setHasConnectionError(true);
      })
      .finally(() => setLoading(false));
  };

  const skipNextLoadRef = useRef(false);

  useEffect(() => {
    if (skipNextLoadRef.current) {
      skipNextLoadRef.current = false;
      return;
    }
    loadData(selectedLocation, null, null);
  }, [selectedLocation]);

  // Handler when user confirms location from the State ➔ District ➔ Block ➔ Village modal or map
  const handleSelectHierarchyLocation = (loc) => {
    const chosenLat = loc.lat ?? loc.latitude;
    const chosenLon = loc.lon ?? loc.longitude;
    skipNextLoadRef.current = true;
    
    if (loc.isAccountReset) {
      localStorage.removeItem('weathergpt_manual_location');
      sessionStorage.removeItem('weathergpt_manual_location');
    } else {
      localStorage.setItem('weathergpt_manual_location', loc.name);
      sessionStorage.setItem('weathergpt_manual_location', loc.name);
    }

    setSelectedLocation(loc.name);
    if (chosenLat != null && chosenLon != null) {
      setSelectedCoordinates({ lat: chosenLat, lon: chosenLon });
    }

    // Instantly update current weather station coordinates so map instantly repositions
    setCurrentWeather(prev => ({
      ...(prev || {}),
      location: loc.name,
      state: loc.state,
      latitude: chosenLat,
      longitude: chosenLon,
      elevation_m: loc.elevation || 245,
      data_source: prev?.data_source || 'LIVE (Open-Meteo API)'
    }));

    loadData(loc.name, chosenLat, chosenLon, loc.state);
  };

  const handleManualLocationSelect = (locName) => {
    localStorage.setItem('weathergpt_manual_location', locName);
    sessionStorage.setItem('weathergpt_manual_location', locName);
    setSelectedLocation(locName);
  };

  const handleQuickChatPrompt = (promptText) => {
    setInitialChatPrompt(promptText);
    setActiveTab('chat');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedLocation={selectedLocation}
        setSelectedLocation={handleManualLocationSelect}
        language={language}
        setLanguage={setLanguage}
        onOpenLocationModal={() => setIsLocationModalOpen(true)}
        onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
        user={currentUser}
        onResetToAccountAddress={handleResetToAccountAddress}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onOpenProfileModal={() => setIsProfileModalOpen(true)}
      />

      {/* State ➔ District ➔ Block ➔ Village Hierarchy Modal */}
      <LocationHierarchyModal
        isOpen={isLocationModalOpen}
        onClose={() => setIsLocationModalOpen(false)}
        onSelectLocation={handleSelectHierarchyLocation}
        currentLocationName={selectedLocation}
        language={language}
        user={currentUser}
      />

      {/* Voice Assistant Modal (Talk & Listen) */}
      <VoiceAssistantModal
        isOpen={isVoiceModalOpen}
        onClose={() => setIsVoiceModalOpen(false)}
        location={selectedLocation}
        language={language}
      />

      {/* Authentication Modal (Sign In / Register) */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
        currentLocation={selectedLocation}
        language={language}
      />

      {/* User Profile & Database Inspector Modal */}
      <UserProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        user={currentUser}
        onUserUpdated={handleUserUpdated}
        onLogout={handleLogout}
      />

      {/* Connection Notice Banner if Backend Offline */}
      {hasConnectionError && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 text-xs text-amber-800 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0" />
            <span>
              Backend server is currently unreachable on port 8000. Running in offline baseline mode.
            </span>
          </div>
          <button
            onClick={() => loadData(selectedLocation)}
            className="flex items-center gap-1 bg-amber-100 hover:bg-amber-200 text-amber-900 px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer transition-all border border-amber-300"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {activeTab === 'dashboard' && (
          <DashboardPage
            currentWeather={currentWeather}
            forecast={forecast}
            alerts={alerts}
            selectedCoordinates={selectedCoordinates}
            selectedLocation={selectedLocation}
            user={currentUser}
            onSelectLocation={handleSelectHierarchyLocation}
            setActiveTab={setActiveTab}
            onQuickChatPrompt={handleQuickChatPrompt}
            language={language}
          />
        )}

        {activeTab === 'chat' && (
          <ChatPage
            location={selectedLocation}
            language={language}
            initialPrompt={initialChatPrompt}
            onClearInitialPrompt={() => setInitialChatPrompt('')}
          />
        )}

        {activeTab === 'forecast' && (
          <ForecastPage
            forecast={forecast}
            location={selectedLocation}
            language={language}
          />
        )}

        {activeTab === 'alerts' && (
          <AlertsPage
            alerts={alerts}
            location={selectedLocation}
            language={language}
          />
        )}

        {activeTab === 'farmer' && (
          <FarmerPage
            defaultLocation={selectedLocation}
            language={language}
          />
        )}

        {activeTab === 'climate' && (
          <ClimatePage
            language={language}
          />
        )}

        {activeTab === 'about' && (
          <AboutPage
            language={language}
          />
        )}
      </main>

      {/* Bottom Global Provenance & Hackathon Footer */}
      <footer className="border-t border-slate-200 bg-white py-5 text-center text-xs text-slate-500 mt-auto shadow-sm">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p className="font-medium text-slate-700">
            WeatherGPT — AI Weather Intelligence & Agro-Climatic Advisory Platform
          </p>
          <p className="text-[11px] text-slate-500">
            Powered by Open-Meteo API, ISRO NRSC VIC Hydrological Data & IMD Gridded Climatology
          </p>
        </div>
      </footer>
    </div>
  );
}
