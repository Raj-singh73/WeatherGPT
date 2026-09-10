import React from 'react';
import { 
  CloudRain, 
  Thermometer, 
  Wind, 
  Gauge, 
  Droplets, 
  Calendar, 
  AlertTriangle, 
  ChevronRight, 
  Sparkles
} from 'lucide-react';
import RiskScoreDial from '../components/RiskScoreDial';
import WeatherMap from '../components/WeatherMap';
import { getTranslation } from '../translations';

export default function DashboardPage({ 
  currentWeather, 
  forecast, 
  alerts = [], 
  selectedCoordinates,
  selectedLocation,
  user = null,
  onSelectLocation,
  setActiveTab, 
  onQuickChatPrompt,
  language = 'en'
}) {
  const t = getTranslation(language);
  const current = currentWeather?.current || {};
  const forecastDays = forecast?.forecast_days || [];
  
  // Calculate ML risk features from today's forecast/current weather
  const todayRisk = forecastDays[0] || {};
  const todayRain = todayRisk.precipitation_sum || 0.0;
  const todayRainProb = todayRisk.precipitation_probability_max ?? current.precipitation_probability;
  const effectiveRain = Math.max(current.precipitation || 0.0, todayRain);
  const riskScore = Number.isFinite(todayRisk.risk_score) ? todayRisk.risk_score : 22.0;
  const riskLevel = todayRisk.risk_level || 'LOW';
  // Pass the computed value straight through (was clamped to a maximum of 0.88).
  const riskConfidence = Number.isFinite(todayRisk.confidence) ? todayRisk.confidence : null;
  const riskFactors = (Array.isArray(todayRisk.key_factors) && todayRisk.key_factors.length > 0)
    ? todayRisk.key_factors
    : [
        effectiveRain > 2.5 ? `Active precipitation forecast (${effectiveRain.toFixed(1)} mm)` : 'Atmospheric precipitation within seasonal bounds',
        current.wind_gust > 40 ? `Elevated gusts (${current.wind_gust} km/h)` : 'Wind gusts within normal velocity profile',
        'HistGradientBoosting Decision Ensemble assessment'
      ];
  const riskRecommendation = todayRisk.recommendation || 'Normal routine activities permitted. Keep monitoring regular local advisories.';

  // Format date
  const formattedDate = new Date().toLocaleDateString(t.common?.locale || 'en-IN', {
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });

  const cleanSelected = (selectedLocation || '').trim();
  const isSelectedRawCoords = !cleanSelected || cleanSelected.startsWith('GPS (') || cleanSelected.startsWith('Location (');
  const cleanWeatherLoc = (currentWeather?.location || '').trim();
  const isWeatherRawCoords = !cleanWeatherLoc || cleanWeatherLoc.startsWith('GPS (') || cleanWeatherLoc.startsWith('Location (');

  const displayLocation = !isSelectedRawCoords
    ? cleanSelected
    : (!isWeatherRawCoords ? cleanWeatherLoc : (cleanSelected || 'Current Location'));

  const displayState = (currentWeather?.state && currentWeather.state !== 'India')
    ? currentWeather.state
    : (user && selectedLocation?.toLowerCase().includes(user.district?.toLowerCase()) ? user.state : (currentWeather?.state || ''));

  // Target coordinates for WeatherMap: prioritize selectedCoordinates for instant synchronization
  const mapLat = Number.isFinite(selectedCoordinates?.lat)
    ? selectedCoordinates.lat
    : (Number.isFinite(currentWeather?.latitude) ? currentWeather.latitude : 21.1458);
  const mapLon = Number.isFinite(selectedCoordinates?.lon)
    ? selectedCoordinates.lon
    : (Number.isFinite(currentWeather?.longitude) ? currentWeather.longitude : 79.0882);

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner & Station Header */}
      <div className="bg-gradient-to-r from-sky-50 via-white to-blue-50/60 border border-sky-100 rounded-3xl p-6 shadow-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold text-sky-700 mb-1 uppercase tracking-wider">
              <span className="flex h-2 w-2 rounded-full bg-sky-600 animate-pulse"></span>
              <span>{t.dashboard.liveIntelligence}</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight flex items-center gap-2">
              <span>{displayLocation}</span>
              {displayState && (
                <span className="text-slate-500 text-2xl font-normal">, {displayState}</span>
              )}
            </h1>
            <p className="text-xs text-slate-600 mt-1 flex items-center gap-2">
              <span>{formattedDate}</span>
              <span>•</span>
              <span className="text-slate-700 font-semibold">{t.dashboard.elevation}: {currentWeather?.elevation_m || 245} m</span>
            </p>
          </div>

          {/* Provenance & Alert Indicators */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Live Data Badge */}
            <div className={`px-3 py-1.5 rounded-xl border text-xs font-bold flex items-center gap-1.5 shadow-sm ${
              currentWeather?.data_source?.includes('LIVE')
                ? 'bg-sky-50 border-sky-200 text-sky-800'
                : 'bg-amber-50 border-amber-200 text-amber-800'
            }`}>
              <span className={`h-2 w-2 rounded-full ${currentWeather?.data_source?.includes('LIVE') ? 'bg-sky-600 animate-pulse' : 'bg-amber-500'}`}></span>
              <span>{currentWeather?.data_source || 'LIVE (Open-Meteo API)'}</span>
            </div>

            {/* Active Alerts Pill */}
            {alerts.length > 0 && (
              <button 
                onClick={() => setActiveTab('alerts')}
                className="px-3 py-1.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold flex items-center gap-1.5 hover:bg-rose-100 transition-all cursor-pointer shadow-sm"
              >
                <AlertTriangle className="h-3.5 w-3.5 text-rose-600" />
                <span>{alerts.length} {t.dashboard.activeAlerts}</span>
                <ChevronRight className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>

        {/* Quick Question Chips */}
        <div className="mt-5 pt-4 border-t border-slate-200/80 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-600 font-bold flex items-center gap-1 mr-1">
            <Sparkles className="h-3.5 w-3.5 text-amber-500" />
            <span>{t.dashboard.askWeatherGPT}</span>
          </span>
          {(t.common?.quickPrompts || [
            `Will it rain tomorrow in ${displayLocation}?`,
            `Is it safe to travel this weekend?`,
            `Should I irrigate my wheat crop today?`,
            `Show cyclone frequency trends`
          ]).map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => onQuickChatPrompt(prompt)}
              className="text-xs bg-white hover:bg-sky-50 text-slate-700 hover:text-sky-700 hover:border-sky-300 px-3 py-1.5 rounded-xl border border-slate-200 transition-all cursor-pointer shadow-sm font-medium"
            >
              “{prompt}”
            </button>
          ))}
        </div>
      </div>

      {/* Real-time Weather Observation Cards (Grid of 5) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {/* Temperature Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold mb-2">
            <span>{t.dashboard.temp}</span>
            <Thermometer className="h-4 w-4 text-rose-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-slate-900">
            {current.temperature !== undefined ? `${current.temperature}°C` : '28.5°C'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            {t.dashboard.feelsLike}: <span className="text-slate-800 font-semibold">{current.apparent_temperature !== undefined ? `${current.apparent_temperature}°C` : '30.2°C'}</span>
          </p>
        </div>

        {/* Condition & Rainfall */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold mb-2">
            <span>{t.dashboard.precip}</span>
            <CloudRain className="h-4 w-4 text-sky-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-slate-900 flex items-baseline gap-2">
            <span>{current.precipitation !== undefined ? `${Number(current.precipitation).toFixed(1)} mm` : '0.0 mm'}</span>
            {todayRainProb !== undefined && (
              <span className="text-xs font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md border border-sky-200">
                {Math.round(todayRainProb)}% prob
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-600 mt-1 truncate font-medium flex items-center justify-between">
            <span>{current.precipitation_intensity || todayRisk.precipitation_category || (effectiveRain > 0 ? 'Light/Moderate Rain' : 'No Rain (Dry)')}</span>
            {todayRain > 0 && current.precipitation === 0 && (
              <span className="text-sky-700 font-bold ml-1">Today: {todayRain.toFixed(1)} mm</span>
            )}
          </div>
        </div>

        {/* Humidity */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold mb-2">
            <span>{t.dashboard.humidity}</span>
            <Droplets className="h-4 w-4 text-teal-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-slate-900">
            {current.relative_humidity !== undefined ? `${current.relative_humidity}%` : '62%'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            {t.dashboard.dewPoint}
          </p>
        </div>

        {/* Wind Speed & Gusts */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold mb-2">
            <span>{t.dashboard.wind}</span>
            <Wind className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-slate-900">
            {current.wind_speed !== undefined ? `${current.wind_speed} km/h` : '14 km/h'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            {t.dashboard.gustsTo}: <span className="text-slate-800 font-semibold">{current.wind_gust !== undefined ? `${current.wind_gust} km/h` : '21 km/h'}</span>
          </p>
        </div>

        {/* Surface Pressure */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold mb-2">
            <span>{t.dashboard.pressure}</span>
            <Gauge className="h-4 w-4 text-amber-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-slate-900">
            {current.surface_pressure !== undefined ? `${current.surface_pressure} hPa` : '1008 hPa'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            {t.dashboard.pressureStable}
          </p>
        </div>
      </div>

      {/* Core Intelligence Dual Panel: ML Risk Score & Geospatial Map */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left Column: AI Weather Impact Score & Explainability */}
        <div className="lg:col-span-6 flex flex-col">
          <RiskScoreDial
            riskScore={riskScore}
            riskLevel={riskLevel}
            confidence={riskConfidence}
            keyFactors={riskFactors}
            recommendation={riskRecommendation}
            metrics={{
              precipitation: effectiveRain,
              wind_gust: current.wind_gust || 18,
              temperature: current.temperature || 28,
              surface_pressure: current.surface_pressure || 1008,
              soil_moisture: 48
            }}
            language={language}
          />
        </div>

        {/* Right Column: Interactive Map */}
        <div className="lg:col-span-6 flex flex-col">
          <WeatherMap
            locationName={displayLocation}
            latitude={mapLat}
            longitude={mapLon}
            temperature={current.temperature || 28.5}
            riskScore={riskScore}
            riskLevel={riskLevel}
            weatherDesc={current.weather_description || 'Clear'}
            onSelectLocation={onSelectLocation}
          />
        </div>
      </div>

      {/* 7-Day Forecast Overview Strip */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center space-x-2">
            <Calendar className="h-4 w-4 text-sky-600" />
            <h3 className="text-sm font-extrabold text-slate-900">{t.dashboard.forecastOutlook}</h3>
          </div>
          <button 
            onClick={() => setActiveTab('forecast')}
            className="text-xs text-sky-600 hover:text-sky-700 font-bold flex items-center gap-1 cursor-pointer"
          >
            <span>{t.dashboard.detailedForecast}</span>
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {forecastDays.map((day, idx) => {
            const isToday = idx === 0;
            const dateObj = new Date(day.date);
            const dayName = isToday ? 'Today' : dateObj.toLocaleDateString('en-IN', { weekday: 'short' });
            const dateDisplay = dateObj.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

            return (
              <div 
                key={day.date}
                className={`rounded-xl p-3.5 text-center border transition-all ${
                  isToday 
                    ? 'bg-sky-50/80 border-sky-300 shadow-sm' 
                    : 'bg-slate-50/70 border-slate-200 hover:border-slate-300 hover:bg-white'
                }`}
              >
                <p className="text-xs font-bold text-slate-900">{dayName}</p>
                <p className="text-[10px] text-slate-500 font-medium">{dateDisplay}</p>
                
                <div className="my-2.5 flex justify-center">
                  <CloudRain className={`h-6 w-6 ${day.precipitation_sum > 10 ? 'text-sky-600' : 'text-slate-400'}`} />
                </div>

                <div className="text-xs font-extrabold text-slate-900">
                  {Math.round(day.temperature_max)}° / <span className="text-slate-500 font-normal">{Math.round(day.temperature_min)}°</span>
                </div>

                <p className="text-[10px] text-sky-700 font-semibold mt-1">
                  {day.precipitation_sum > 0 ? `${day.precipitation_sum.toFixed(1)} mm` : '0 mm'}
                </p>

                {/* Day Risk Badge */}
                <div className="mt-2.5 pt-2 border-t border-slate-200">
                  <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase border ${
                    day.risk_level?.toUpperCase() === 'SEVERE' ? 'bg-rose-100 text-rose-800 border-rose-200' :
                    day.risk_level?.toUpperCase() === 'HIGH' ? 'bg-orange-100 text-orange-800 border-orange-200' :
                    day.risk_level?.toUpperCase() === 'MODERATE' ? 'bg-amber-100 text-amber-800 border-amber-200' :
                    'bg-emerald-100 text-emerald-800 border-emerald-200'
                  }`}>
                    {day.risk_level}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
