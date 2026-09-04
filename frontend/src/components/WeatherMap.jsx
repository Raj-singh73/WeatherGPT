import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { 
  MapPin, 
  Layers, 
  Satellite, 
  Map as MapIcon, 
  Mountain, 
  Moon, 
  CloudRain, 
  Maximize2, 
  Minimize2, 
  Crosshair, 
  Radio, 
  Compass, 
  Globe, 
  Eye, 
  Sparkles,
  Box,
  Search,
  Loader2,
  X,
  Check
} from 'lucide-react';
import api from '../api';

// Custom SVG marker pin (Leaflet compatible, no external CDN needed)
const createPinIcon = (color, is3D = false) => L.divIcon({
  className: 'custom-weather-pin',
  html: `<div style="display:flex;align-items:center;justify-content:center;width:40px;height:40px;background:white;border:3px solid ${color};border-radius:50%;box-shadow:${is3D ? '0 12px 24px rgba(0,0,0,0.5)' : '0 4px 14px rgba(0,0,0,0.35)'};transform:${is3D ? 'translateY(-6px)' : 'none'};transition:all 0.3s ease;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>
      <circle cx="12" cy="10" r="3"></circle>
    </svg>
  </div>`,
  iconSize: [40, 40],
  iconAnchor: [20, 40],
  popupAnchor: [0, -40]
});

// Map Controller for Smooth Flying & Re-centering with Stable Primitive Dependencies
function MapFlyController({ center, zoom }) {
  const map = useMap();
  const lat = center?.[0];
  const lon = center?.[1];

  useEffect(() => {
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      try {
        map.flyTo([lat, lon], zoom, { duration: 1.5, easeLinearity: 0.25 });
      } catch (e) {
        map.setView([lat, lon], zoom);
      }
    }
  }, [lat, lon, zoom, map]);
  return null;
}

// Available High-Definition Map Perspectives & Formats (Google Satellite by Default)
const BASE_LAYERS = {
  google_hybrid: {
    id: 'google_hybrid',
    name: 'Google Satellite (Live Hybrid)',
    icon: Satellite,
    url: 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attribution: '&copy; Google Earth & Maps Satellite',
    maxZoom: 20
  },
  google_earth: {
    id: 'google_earth',
    name: 'Google Pure Earth Satellite',
    icon: Globe,
    url: 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attribution: '&copy; Google Earth Imagery',
    maxZoom: 20
  },
  google_terrain: {
    id: 'google_terrain',
    name: 'Google 3D Terrain & Contours',
    icon: Mountain,
    url: 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
    attribution: '&copy; Google Terrain Relief',
    maxZoom: 18
  },
  google_streets: {
    id: 'google_streets',
    name: 'Google Street Maps',
    icon: MapIcon,
    url: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attribution: '&copy; Google Maps',
    maxZoom: 20
  },
  esri_satellite: {
    id: 'esri_satellite',
    name: 'Esri World Imagery 3D',
    icon: Satellite,
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Earthstar Geographics',
    maxZoom: 19,
    labelsUrl: 'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'
  },
  dark_tactical: {
    id: 'dark_tactical',
    name: 'Tactical Night Radar',
    icon: Moon,
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; CARTO &copy; OpenStreetMap',
    maxZoom: 19
  }
};

export default function WeatherMap({ 
  locationName = 'Nagpur', 
  latitude = 21.1458, 
  longitude = 79.0882, 
  temperature = 28.5, 
  riskScore = 24, 
  riskLevel = 'LOW',
  weatherDesc = 'Clear',
  onSelectLocation
}) {
  const validLat = Number.isFinite(latitude) ? latitude : 21.1458;
  const validLon = Number.isFinite(longitude) ? longitude : 79.0882;

  // Local state for immediate responsiveness when user searches inside the map
  const [localCoords, setLocalCoords] = useState(null);
  const activeLat = localCoords?.lat ?? validLat;
  const activeLon = localCoords?.lon ?? validLon;
  const activeName = localCoords?.name ?? locationName;
  const center = [activeLat, activeLon];

  // In-map search states
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  // Active Map Layer format (Default to Google Satellite Live Aerial)
  const [activeLayer, setActiveLayer] = useState('google_hybrid');
  // Zoom Level (Default to high-resolution local village level 14)
  const [zoomLevel, setZoomLevel] = useState(14);
  // 3D Perspective Oblique View Mode Toggle
  const [is3DMode, setIs3DMode] = useState(false);
  // Doppler Rain Radar Overlay Toggle
  const [showRadarOverlay, setShowRadarOverlay] = useState(true);
  const [radarPath, setRadarPath] = useState(null);
  // Risk buffer circle toggle
  const [showRiskRadius, setShowRiskRadius] = useState(true);
  // Fullscreen container toggle
  const [isFullscreen, setIsFullscreen] = useState(false);
  // Layer switcher menu open/close
  const [isLayerMenuOpen, setIsLayerMenuOpen] = useState(false);

  // Reset localCoords when external props change
  useEffect(() => {
    setLocalCoords(null);
  }, [latitude, longitude, locationName]);

  // Auto zoom to high-resolution village view whenever location updates
  const prevCoordsRef = useRef({ lat: validLat, lon: validLon });
  useEffect(() => {
    if (
      Math.abs(prevCoordsRef.current.lat - validLat) > 0.001 ||
      Math.abs(prevCoordsRef.current.lon - validLon) > 0.001
    ) {
      prevCoordsRef.current = { lat: validLat, lon: validLon };
      setZoomLevel(14);
    }
  }, [validLat, validLon]);

  // Real-time suggestions as user types in the map search input
  useEffect(() => {
    const q = searchQuery.trim();
    if (q.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await api.suggestLocations(q);
        setSuggestions(res || []);
      } catch (err) {
        console.warn('In-map suggest notice:', err);
      } finally {
        setIsSearching(false);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSelectSuggestion = (item) => {
    setSearchQuery('');
    setSuggestions([]);
    const chosenLat = item.lat ?? item.latitude;
    const chosenLon = item.lon ?? item.longitude;
    if (Number.isFinite(chosenLat) && Number.isFinite(chosenLon)) {
      setLocalCoords({ lat: chosenLat, lon: chosenLon, name: item.name || item.village });
      setZoomLevel(14);
      const base = (item.village || item.name || '').trim();
      const cleanLocName = (item.district && !base.toLowerCase().includes(item.district.toLowerCase()))
        ? `${base} (${item.district})`
        : base;

      if (onSelectLocation) {
        onSelectLocation({
          name: cleanLocName,
          village: item.village || item.name,
          district: item.district,
          state: item.state,
          lat: chosenLat,
          lon: chosenLon,
          latitude: chosenLat,
          longitude: chosenLon,
          elevation: item.elevation || 240
        });
      }
    }
  };

  const handleSearchSubmit = async (e) => {
    e?.preventDefault?.();
    const q = searchQuery.trim();
    if (!q) return;
    setIsSearching(true);
    try {
      if (/^[1-9][0-9]{5}$/.test(q)) {
        const pinRes = await api.lookupPincode(q);
        if (pinRes && pinRes.lat && pinRes.lon) {
          const firstPo = pinRes.results?.[0] || {};
          handleSelectSuggestion({
            name: firstPo.name || `PIN ${q}`,
            village: firstPo.village || firstPo.name || `PIN ${q}`,
            district: firstPo.district,
            state: firstPo.state,
            lat: pinRes.lat,
            lon: pinRes.lon,
            pincode: q
          });
          return;
        }
      }
      const results = await api.suggestLocations(q);
      if (results && results.length > 0) {
        handleSelectSuggestion(results[0]);
      }
    } catch (err) {
      console.warn('In-map search submit notice:', err);
    } finally {
      setIsSearching(false);
    }
  };

  // Close fullscreen on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  // Fetch Live RainViewer Doppler Radar Time & Tile Path
  useEffect(() => {
    let isCancelled = false;
    fetch('https://api.rainviewer.com/public/weather-maps.json')
      .then(res => res.json())
      .then(data => {
        if (isCancelled) return;
        const past = data?.radar?.past || [];
        if (past.length > 0) {
          setRadarPath(past[past.length - 1].path);
        }
      })
      .catch(err => {
        console.warn('RainViewer live radar tile notice:', err);
      });
    return () => { isCancelled = true; };
  }, []);

  // Circle color based on risk level
  const getCircleColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'SEVERE': return '#e11d48';
      case 'HIGH': return '#ea580c';
      case 'MODERATE': return '#d97706';
      default: return '#059669';
    }
  };

  const circleColor = getCircleColor(riskLevel);
  const currentLayer = BASE_LAYERS[activeLayer] || BASE_LAYERS.satellite;

  // Render Fullscreen as a clean Modal Overlay
  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-[9998] bg-slate-900/80 backdrop-blur-sm p-3 sm:p-6 flex flex-col animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl p-4 sm:p-5 flex flex-col h-full w-full overflow-hidden">
          {/* Fullscreen Header */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
            <div className="flex items-center space-x-2.5">
              <div className="h-8 w-8 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center">
                <Radio className="h-4 w-4 animate-pulse" />
              </div>
              <div>
                <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
                  <span>Geospatial Risk & Weather Radar (Fullscreen 3D Studio)</span>
                  {is3DMode && (
                    <span className="text-[10px] bg-sky-100 text-sky-800 border border-sky-300 font-bold px-2 py-0.5 rounded-full">
                      3D Perspective On
                    </span>
                  )}
                </h3>
                <p className="text-[11px] text-slate-500">
                  Focus: <strong className="text-slate-800">{activeName}</strong> ({activeLat.toFixed(5)}°N, {activeLon.toFixed(5)}°E)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIs3DMode(!is3DMode)}
                className={`text-xs px-3 py-1.5 rounded-xl font-bold border transition-all cursor-pointer flex items-center gap-1.5 shadow-xs ${
                  is3DMode 
                    ? 'bg-sky-600 text-white border-sky-600' 
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
                }`}
              >
                <Globe className={`h-3.5 w-3.5 ${is3DMode ? 'animate-spin' : ''}`} />
                <span>{is3DMode ? '3D Active' : 'Enable 3D'}</span>
              </button>

              <button
                onClick={() => setIsFullscreen(false)}
                className="bg-slate-100 hover:bg-rose-50 text-slate-700 hover:text-rose-700 font-bold text-xs px-3.5 py-1.5 rounded-xl border border-slate-200 transition-colors flex items-center gap-1.5 cursor-pointer shadow-xs"
              >
                <Minimize2 className="h-3.5 w-3.5" />
                <span>Exit Fullscreen (Esc)</span>
              </button>
            </div>
          </div>

          {/* Fullscreen Map Canvas with 3D Tilt support */}
          <div 
            className="flex-1 w-full rounded-2xl overflow-hidden border border-slate-200 relative bg-slate-950 transition-all duration-500"
            style={is3DMode ? {
              perspective: '1200px',
              transform: 'rotateX(26deg) scale(1.03)',
              transformOrigin: '50% 85%'
            } : {}}
          >
            <MapContainer
              key={`fs_map_${activeLayer}`}
              center={center}
              zoom={zoomLevel}
              scrollWheelZoom={true}
              className="h-full w-full"
              style={{ height: '100%', minHeight: '400px' }}
            >
              <MapFlyController center={center} zoom={zoomLevel} />
              <TileLayer
                key={currentLayer.id}
                attribution={currentLayer.attribution}
                url={currentLayer.url}
                maxZoom={currentLayer.maxZoom || 19}
              />
              {currentLayer.labelsUrl && (
                <TileLayer
                  key={`${currentLayer.id}_labels`}
                  url={currentLayer.labelsUrl}
                  opacity={0.85}
                  maxZoom={19}
                />
              )}
              {showRadarOverlay && radarPath && (
                <TileLayer
                  key={`radar_${radarPath}`}
                  url={`https://tilecache.rainviewer.com/v2/radar/${radarPath}/256/{z}/{x}/{y}/2/1_1.png`}
                  opacity={0.7}
                  maxZoom={19}
                  attribution="Live Rain Radar &copy; RainViewer"
                />
              )}
              {showRiskRadius && (
                <Circle
                  center={center}
                  radius={zoomLevel >= 12 ? 8000 : 35000}
                  pathOptions={{
                    color: circleColor,
                    fillColor: circleColor,
                    fillOpacity: 0.18,
                    weight: 2
                  }}
                />
              )}
              <Marker position={center} icon={createPinIcon(circleColor, is3DMode)}>
                <Popup className="weather-popup">
                  <div className="p-1 space-y-1 min-w-[180px]">
                    <strong className="text-xs text-slate-900">{activeName}</strong>
                    <p className="text-[11px] text-slate-600">🌡️ {temperature}°C • {weatherDesc}</p>
                    <p className="text-[11px] text-slate-600">AI Risk: {riskScore}/100 ({riskLevel})</p>
                    <p className="text-[10px] text-slate-400 font-mono">{activeLat.toFixed(5)}°N, {activeLon.toFixed(5)}°E</p>
                  </div>
                </Popup>
              </Marker>
            </MapContainer>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm overflow-hidden flex flex-col transition-all duration-300 h-full min-h-[500px] relative z-0 isolate">
      
      {/* Header bar with Multiple Views and 3D Perspective controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3.5">
        <div className="flex items-center space-x-2.5">
          <div className="h-8 w-8 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center shadow-xs flex-shrink-0">
            <Radio className="h-4 w-4 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-1.5 flex-wrap">
              <h3 className="text-sm font-extrabold text-slate-900">
                Geospatial Risk & Weather Radar
              </h3>
              {is3DMode && (
                <span className="text-[9px] bg-sky-100 text-sky-800 border border-sky-300 font-black px-1.5 py-0.5 rounded-full uppercase">
                  3D Oblique
                </span>
              )}
              <span className="text-[9px] bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono font-bold px-1.5 py-0.5 rounded-full">
                {activeLat.toFixed(4)}°N, {activeLon.toFixed(4)}°E
              </span>
            </div>
            <p className="text-[11px] text-slate-500 truncate max-w-[200px] sm:max-w-xs">
              Focus: <strong className="text-slate-800">{activeName}</strong>
            </p>
          </div>
        </div>

        {/* Center: In-Radar Instant PIN & Village Precision Search */}
        <div className="relative flex-1 max-w-xs z-30">
          <form onSubmit={handleSearchSubmit} className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-sky-600" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search PIN (e.g. 273303) or Village..."
              className="w-full pl-8 pr-7 py-1.5 bg-slate-50 hover:bg-white focus:bg-white border border-slate-200 focus:border-sky-500 rounded-xl text-xs font-semibold text-slate-900 placeholder:text-slate-400 focus:outline-none transition-all shadow-xs"
            />
            {isSearching && (
              <Loader2 className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-sky-600 animate-spin" />
            )}
            {searchQuery && !isSearching && (
              <button
                type="button"
                onClick={() => { setSearchQuery(''); setSuggestions([]); }}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5 cursor-pointer"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </form>

          {/* Autocomplete Dropdown List */}
          {suggestions.length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-2xl shadow-xl z-50 max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs animate-fadeIn">
              {suggestions.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectSuggestion(item)}
                  className="w-full text-left px-3 py-2 hover:bg-sky-50 flex items-center justify-between group transition-colors cursor-pointer"
                >
                  <div className="truncate pr-2">
                    <span className="font-bold text-slate-900 group-hover:text-sky-700 block truncate">
                      {item.village || item.name}
                    </span>
                    <span className="text-[10px] text-slate-500 block truncate">
                      {item.district ? `${item.district}, ` : ''}{item.state} {item.pincode ? `(${item.pincode})` : ''}
                    </span>
                  </div>
                  <span className="text-[9px] font-mono font-bold text-sky-700 bg-sky-100 px-1.5 py-0.5 rounded flex-shrink-0">
                    {item.lat ? `${item.lat.toFixed(3)}°` : 'Exact'}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-1.5 ml-auto flex-wrap">
          
          {/* 3D SATELLITE OBLIQUE PERSPECTIVE TOGGLE */}
          <button
            onClick={() => setIs3DMode(!is3DMode)}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all cursor-pointer flex items-center gap-1.5 shadow-xs ${
              is3DMode
                ? 'bg-sky-600 text-white border-sky-600 ring-2 ring-sky-300 shadow-md scale-105'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
            }`}
            title="Toggle 3D Satellite Perspective (Google Earth Style Oblique Tilt)"
          >
            <Box className={`h-3.5 w-3.5 ${is3DMode ? 'animate-bounce' : ''}`} />
            <span>{is3DMode ? '3D Satellite View' : '3D View'}</span>
          </button>

          {/* Multiple Views Quick Scale Presets */}
          <div className="bg-slate-100 p-0.5 rounded-xl flex items-center border border-slate-200 text-[10px] font-bold">
            <button
              onClick={() => setZoomLevel(15)}
              className={`px-2 py-1 rounded-lg transition-all cursor-pointer ${
                zoomLevel >= 14 ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
              title="Hyperlocal Village View (Farms, houses & local lanes)"
            >
              Village
            </button>
            <button
              onClick={() => setZoomLevel(11)}
              className={`px-2 py-1 rounded-lg transition-all cursor-pointer ${
                zoomLevel >= 9 && zoomLevel < 14 ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
              title="District Basin View (Tehsils & rivers)"
            >
              District
            </button>
            <button
              onClick={() => setZoomLevel(6)}
              className={`px-2 py-1 rounded-lg transition-all cursor-pointer ${
                zoomLevel < 9 ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
              title="Cyclone Radar View (State & Bay of Bengal / Arabian Sea tracking)"
            >
              Cyclone
            </button>
          </div>

          {/* Recenter Button */}
          <button
            onClick={() => setZoomLevel(13)}
            className="p-1.5 rounded-xl bg-slate-100 hover:bg-sky-50 text-slate-600 hover:text-sky-700 border border-slate-200 transition-colors cursor-pointer shadow-xs"
            title="Recenter camera on exact location"
          >
            <Crosshair className="h-4 w-4" />
          </button>

          {/* Fullscreen Toggle */}
          <button
            onClick={() => setIsFullscreen(true)}
            className="p-1.5 rounded-xl bg-slate-100 hover:bg-sky-50 text-slate-600 hover:text-sky-700 border border-slate-200 transition-colors cursor-pointer shadow-xs"
            title="Expand Fullscreen Radar Studio"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Map Box with 3D Perspective Tilt Container */}
      <div 
        className={`flex-1 w-full rounded-2xl overflow-hidden border border-slate-200 relative min-h-[380px] bg-slate-900 transition-all duration-500 ${
          is3DMode ? 'shadow-2xl ring-2 ring-sky-400' : ''
        }`}
        style={is3DMode ? {
          perspective: '1200px',
          transform: 'rotateX(26deg) scale(1.04)',
          transformOrigin: '50% 85%',
          boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.45)'
        } : {}}
      >
        {/* Atmospheric horizon glow when 3D mode is active */}
        {is3DMode && (
          <div className="absolute top-0 left-0 right-0 h-12 bg-gradient-to-b from-sky-400/25 to-transparent pointer-events-none z-10"></div>
        )}

        <MapContainer
          key={`map_${activeLayer}`}
          center={center}
          zoom={zoomLevel}
          scrollWheelZoom={false}
          className="h-full w-full"
          style={{ height: '100%', minHeight: '380px' }}
        >
          <MapFlyController center={center} zoom={zoomLevel} />

          {/* Active Base Map Layer */}
          <TileLayer
            key={currentLayer.id}
            attribution={currentLayer.attribution}
            url={currentLayer.url}
            maxZoom={currentLayer.maxZoom || 19}
          />

          {/* Optional Boundaries & Labels overlay for Satellite Hybrid View */}
          {currentLayer.labelsUrl && (
            <TileLayer
              key={`${currentLayer.id}_labels`}
              url={currentLayer.labelsUrl}
              opacity={0.85}
              maxZoom={19}
            />
          )}

          {/* Live Doppler Rain Radar Clouds Overlay (RainViewer) */}
          {showRadarOverlay && radarPath && (
            <TileLayer
              key={`radar_${radarPath}`}
              url={`https://tilecache.rainviewer.com/v2/radar/${radarPath}/256/{z}/{x}/{y}/2/1_1.png`}
              opacity={0.7}
              maxZoom={19}
              attribution="Live Rain Radar &copy; RainViewer"
            />
          )}

          {/* Location Risk Radius Circle Buffer */}
          {showRiskRadius && (
            <Circle
              center={center}
              radius={zoomLevel >= 13 ? 5000 : zoomLevel >= 10 ? 18000 : 45000}
              pathOptions={{
                color: circleColor,
                fillColor: circleColor,
                fillOpacity: 0.18,
                weight: 2
              }}
            />
          )}

          {/* Primary Verified Station Marker */}
          <Marker position={center} icon={createPinIcon(circleColor, is3DMode)}>
            <Popup className="weather-popup">
              <div className="p-1 space-y-1.5 min-w-[180px]">
                <div className="flex items-center justify-between border-b border-slate-100 pb-1">
                  <strong className="text-xs text-slate-900 font-extrabold">{activeName}</strong>
                  <span className={`text-[9px] font-black px-1.5 py-0.5 rounded text-white ${
                    riskLevel === 'SEVERE' ? 'bg-rose-600' :
                    riskLevel === 'HIGH' ? 'bg-orange-600' :
                    riskLevel === 'MODERATE' ? 'bg-amber-600' : 'bg-emerald-600'
                  }`}>
                    {riskLevel}
                  </span>
                </div>
                <div className="text-[11px] text-slate-700 space-y-0.5 font-medium">
                  <p>🌡️ Temperature: <strong>{temperature}°C</strong></p>
                  <p>☁️ Condition: <strong>{weatherDesc}</strong></p>
                  <p>🛡️ AI Risk Index: <strong>{riskScore} / 100</strong></p>
                  <p className="text-[10px] text-slate-400 font-mono">
                    {activeLat.toFixed(5)}°N, {activeLon.toFixed(5)}°E
                  </p>
                </div>
              </div>
            </Popup>
          </Marker>
        </MapContainer>

        {/* Floating Multiple Views & Format Switcher Menu */}
        <div className="absolute bottom-3 left-3 z-20">
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsLayerMenuOpen(!isLayerMenuOpen)}
              className="bg-white/95 hover:bg-white text-slate-900 border border-slate-300 rounded-2xl px-3 py-2 shadow-lg backdrop-blur-md flex items-center space-x-2 text-xs font-bold transition-all cursor-pointer hover:scale-105"
            >
              {React.createElement(currentLayer.icon, { className: "h-4 w-4 text-sky-600" })}
              <span>Views: {currentLayer.name.split(' ')[0]}</span>
              <Layers className="h-3.5 w-3.5 text-slate-400" />
            </button>

            {/* Popup Menu of Multiple Location Views */}
            {isLayerMenuOpen && (
              <div className="absolute bottom-12 left-0 bg-white border border-slate-200 rounded-2xl p-3 shadow-2xl backdrop-blur-md w-72 space-y-3 animate-fadeIn">
                <div>
                  <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block mb-1.5">
                    Location Views & Formats (3D / Aerial / Street)
                  </span>
                  <div className="grid grid-cols-2 gap-1.5">
                    {Object.values(BASE_LAYERS).map((layer) => {
                      const IconComp = layer.icon;
                      const isSelected = activeLayer === layer.id;
                      return (
                        <button
                          key={layer.id}
                          type="button"
                          onClick={() => {
                            setActiveLayer(layer.id);
                            setIsLayerMenuOpen(false);
                          }}
                          className={`p-2 rounded-xl text-left text-xs font-bold transition-all cursor-pointer flex flex-col items-start border ${
                            isSelected
                              ? 'bg-sky-50 text-sky-700 border-sky-400 shadow-xs'
                              : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                          }`}
                        >
                          <IconComp className={`h-4 w-4 mb-1 ${isSelected ? 'text-sky-600' : 'text-slate-500'}`} />
                          <span className="text-[11px] truncate w-full">{layer.name}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Overlays (Radar Clouds & Risk Zone) */}
                <div className="pt-2 border-t border-slate-100 space-y-1.5">
                  <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block">
                    Live Atmospheric Overlays
                  </span>

                  <label className="flex items-center justify-between text-xs font-semibold text-slate-700 cursor-pointer p-1 rounded-lg hover:bg-slate-50">
                    <span className="flex items-center gap-1.5">
                      <CloudRain className="h-3.5 w-3.5 text-sky-600" />
                      <span>Live Rain Doppler Radar</span>
                    </span>
                    <input
                      type="checkbox"
                      checked={showRadarOverlay}
                      onChange={(e) => setShowRadarOverlay(e.target.checked)}
                      className="rounded text-sky-600 focus:ring-sky-500 cursor-pointer"
                    />
                  </label>

                  <label className="flex items-center justify-between text-xs font-semibold text-slate-700 cursor-pointer p-1 rounded-lg hover:bg-slate-50">
                    <span className="flex items-center gap-1.5">
                      <Radio className="h-3.5 w-3.5 text-amber-600" />
                      <span>Impact Risk Radius</span>
                    </span>
                    <input
                      type="checkbox"
                      checked={showRiskRadius}
                      onChange={(e) => setShowRiskRadius(e.target.checked)}
                      className="rounded text-amber-600 focus:ring-amber-500 cursor-pointer"
                    />
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Live Status Pill in Top-Right Corner of Map */}
        <div className="absolute top-3 right-3 z-20 flex items-center gap-2">
          {showRadarOverlay && radarPath && (
            <span className="bg-white/95 border border-slate-200 text-sky-800 text-[10px] font-extrabold px-2.5 py-1 rounded-xl shadow-md flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
              Live Doppler Active
            </span>
          )}
          {is3DMode && (
            <span className="bg-sky-600 text-white text-[10px] font-bold px-2.5 py-1 rounded-xl shadow-md">
              3D View
            </span>
          )}
          <span className="bg-slate-900/80 text-white text-[10px] font-mono px-2.5 py-1 rounded-xl shadow-md">
            Zoom: {zoomLevel}x
          </span>
        </div>

      </div>

      {/* Map Legend / Footer Indicators */}
      <div className="mt-3.5 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-[11px] text-slate-500 gap-2 font-medium">
        <div className="flex items-center space-x-3">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
            Low Risk (Safe)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500"></span>
            Moderate Watch
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-orange-500"></span>
            High Alert
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-600"></span>
            Severe Warning
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-400">
            Engine: Esri 3D Imagery & RainViewer Radar
          </span>
        </div>
      </div>

    </div>
  );
}
