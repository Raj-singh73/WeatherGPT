import React, { useState, useMemo, useEffect } from 'react';
import { 
  X, 
  MapPin, 
  Search, 
  Check, 
  Layers, 
  Building2, 
  Home, 
  Compass, 
  Navigation, 
  Loader2, 
  Sparkles, 
  Hash, 
  CheckCircle2, 
  Radar
} from 'lucide-react';
import { 
  ALL_INDIA_DISTRICTS_CATALOG
} from '../data/indiaAdminData';
import api from '../api';
import { getTranslation } from '../translations';
import { getUserAccountAddress } from '../utils/addressUtils';

const PROMINENT_HUBS = {
  'Maharajganj': [
    { name: 'Nautanwa', subDistrict: 'Nautanwa', lat: 27.4280, lon: 83.4210, elevation: 102, desc: 'Major Border Transit & Trade Hub' },
    { name: 'Sonauli', subDistrict: 'Nautanwa', lat: 27.4780, lon: 83.4680, elevation: 105, desc: 'Indo-Nepal International Border' },
    { name: 'Nichlaul', subDistrict: 'Nichlaul', lat: 27.3170, lon: 83.7290, elevation: 98, desc: 'Sohagi Barwa Ecological Tehsil' },
    { name: 'Pharenda', subDistrict: 'Pharenda', lat: 27.1320, lon: 83.2840, elevation: 92, desc: 'Anandnagar Rail Junction' },
    { name: 'Siswa Bazar', subDistrict: 'Nichlaul', lat: 27.1550, lon: 83.7620, elevation: 94, desc: 'Commercial Agricultural Mandi' },
    { name: 'Brijmanganj', subDistrict: 'Pharenda', lat: 27.2180, lon: 83.1890, elevation: 95, desc: 'Western Agro-Meteorological Hub' },
    { name: 'Ghughli', subDistrict: 'Maharajganj', lat: 27.0580, lon: 83.6930, elevation: 93, desc: 'Sugar Mill & Cane Belt' },
    { name: 'Kolhui', subDistrict: 'Pharenda', lat: 27.3450, lon: 83.3320, elevation: 96, desc: 'North-West Transit Hub' },
    { name: 'Maharajganj Sadar', subDistrict: 'Maharajganj', lat: 27.1450, lon: 83.5600, elevation: 95, desc: 'District Administrative Center' },
  ],
  'Lucknow': [
    { name: 'Malihabad', subDistrict: 'Malihabad', lat: 26.9200, lon: 80.7100, elevation: 128, desc: 'World-Renowned Dasheri Mango Belt' },
    { name: 'Mohanlalganj', subDistrict: 'Mohanlalganj', lat: 26.6710, lon: 80.9850, elevation: 122, desc: 'Southern Agronomic Mandi & Tehsil' },
    { name: 'Bakshi Ka Talab', subDistrict: 'Bakshi Ka Talab', lat: 26.9780, lon: 80.8980, elevation: 125, desc: 'Northern Agricultural Research Zone' },
    { name: 'Sarojini Nagar', subDistrict: 'Lucknow', lat: 26.7580, lon: 80.8650, elevation: 124, desc: 'Amausi Weather Radar & Airport' },
    { name: 'Kakori', subDistrict: 'Malihabad', lat: 26.8800, lon: 80.7900, elevation: 126, desc: 'Historical Zari & Horticulture Cluster' },
    { name: 'Gosainganj', subDistrict: 'Mohanlalganj', lat: 26.7720, lon: 81.1210, elevation: 122, desc: 'Eastern Rural Market & Transit' },
    { name: 'Chinhat', subDistrict: 'Lucknow', lat: 26.8780, lon: 81.0250, elevation: 124, desc: 'Peri-Urban Agri-Industrial Zone' },
    { name: 'Lucknow Sadar', subDistrict: 'Lucknow', lat: 26.8467, lon: 80.9462, elevation: 123, desc: 'State Meteorological Headquarters' },
  ]
};

export default function LocationHierarchyModal({ 
  isOpen, 
  onClose, 
  onSelectLocation, 
  currentLocationName = 'Nagpur', 
  language = 'en',
  user = null
}) {
  const t = getTranslation(language).locationModal;
  const accountAddress = getUserAccountAddress(user);

  const [activeTab, setActiveTab] = useState('cascade'); // 'cascade', 'pincode', 'gps'

  // Hierarchy Selection States: DIRECT State ➔ District ➔ Village (No intermediate block step!)
  const [selectedState, setSelectedState] = useState('Uttar Pradesh');
  const [selectedDistrict, setSelectedDistrict] = useState('Gorakhpur');
  const [selectedSubDistrict, setSelectedSubDistrict] = useState('ALL');
  const [selectedVillage, setSelectedVillage] = useState('Gorakhpur Sadar');
  const [customCoordinates, setCustomCoordinates] = useState(null);

  // Dynamic District Villages loaded directly from backend API
  const [districtVillages, setDistrictVillages] = useState([]);
  const [isLoadingVillages, setIsLoadingVillages] = useState(false);
  const [villageFilterQuery, setVillageFilterQuery] = useState('');

  // Top Global Suggestion Search Bar States
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestResults, setSuggestResults] = useState([]);
  const [isSuggesting, setIsSuggesting] = useState(false);

  // Pan-India Live Village Detector States (for detecting ANY of India's 650,000+ villages)
  const [detectVillageQuery, setDetectVillageQuery] = useState('');
  const [detectedVillageData, setDetectedVillageData] = useState(null);
  const [isDetectingVillage, setIsDetectingVillage] = useState(false);
  const [detectVillageError, setDetectVillageError] = useState('');
  const [villageAutoSuggestions, setVillageAutoSuggestions] = useState([]);

  // PIN Code Lookup States
  const [pincodeInput, setPincodeInput] = useState('');
  const [pincodeResults, setPincodeResults] = useState([]);
  const [isLookingUpPin, setIsLookingUpPin] = useState(false);

  // GPS Geolocation States
  const [isDetectingGps, setIsDetectingGps] = useState(false);
  const [detectedGpsLocation, setDetectedGpsLocation] = useState(null);
  const [gpsStatus, setGpsStatus] = useState('');
  const [gpsError, setGpsError] = useState('');

  // 1. All 36 States & Union Territories
  const stateOptions = useMemo(() => Object.keys(ALL_INDIA_DISTRICTS_CATALOG), []);

  // 2. All Official Districts of Selected State (All 784 Districts of India)
  const districtOptions = useMemo(() => {
    return ALL_INDIA_DISTRICTS_CATALOG[selectedState] || [];
  }, [selectedState]);

  // Load Real Villages Directly whenever Selected District Changes (Bypassing Block)
  useEffect(() => {
    let isCancelled = false;
    setIsLoadingVillages(true);
    setDetectedVillageData(null);
    setDetectVillageQuery('');
    setVillageFilterQuery('');
    setSelectedSubDistrict('ALL');

    api.getDistrictHierarchy(selectedDistrict, selectedState)
      .then(res => {
        if (isCancelled) return;
        const vList = res.villages && res.villages.length > 0 ? res.villages : [
          { name: `${selectedDistrict} Sadar`, elevation: 240, type: 'District Center' },
          { name: `${selectedDistrict} Rural`, elevation: 245, type: 'Village' }
        ];
        setDistrictVillages(vList);
        setSelectedVillage(vList[0]?.name || `${selectedDistrict} Sadar`);
        if (vList[0]?.lat && vList[0]?.lon) {
          setCustomCoordinates({
            lat: vList[0].lat,
            lon: vList[0].lon,
            elevation: vList[0].elevation || 240
          });
        }
        setIsLoadingVillages(false);
      })
      .catch((err) => {
        console.warn('Backend district hierarchy notice:', err);
        if (!isCancelled) setIsLoadingVillages(false);
      });

    return () => { isCancelled = true; };
  }, [selectedState, selectedDistrict]);

  // Compute unique subDistricts (Tehsils) in this district
  const availableSubDistricts = useMemo(() => {
    const subs = new Set();
    districtVillages.forEach(v => {
      if (v.subDistrict) subs.add(v.subDistrict);
    });
    return Array.from(subs).sort();
  }, [districtVillages]);

  // Count of villages per subDistrict
  const subDistrictCounts = useMemo(() => {
    const counts = {};
    districtVillages.forEach(v => {
      const s = v.subDistrict || 'Other';
      counts[s] = (counts[s] || 0) + 1;
    });
    return counts;
  }, [districtVillages]);

  // Instant filter over all villages in the selected district with Tehsil isolation
  const filteredVillages = useMemo(() => {
    let list = districtVillages;
    if (selectedSubDistrict !== 'ALL') {
      list = list.filter(v => (v.subDistrict || '').toLowerCase() === selectedSubDistrict.toLowerCase());
    }
    if (villageFilterQuery.trim()) {
      const q = villageFilterQuery.toLowerCase().trim();
      list = list.filter(v => 
        (v.name || v.village || '').toLowerCase().includes(q) ||
        (v.subDistrict || '').toLowerCase().includes(q)
      );
    }
    return list;
  }, [districtVillages, selectedSubDistrict, villageFilterQuery]);

  // Active village item for preview
  const activeVillageObject = useMemo(() => {
    const match = districtVillages.find(v => (v.name || v.village) === selectedVillage);
    if (match) return match;
    return {
      name: selectedVillage,
      village: selectedVillage,
      district: selectedDistrict,
      state: selectedState,
      subDistrict: selectedSubDistrict !== 'ALL' ? selectedSubDistrict : `${selectedDistrict} Tehsil`,
      lat: customCoordinates?.lat || 21.1458,
      lon: customCoordinates?.lon || 79.0882,
      elevation: customCoordinates?.elevation || 240
    };
  }, [districtVillages, selectedVillage, selectedDistrict, selectedState, selectedSubDistrict, customCoordinates]);

  // Top Global Autocomplete Search via Backend /api/location/suggest
  useEffect(() => {
    if (!searchQuery || searchQuery.trim().length < 2) {
      setSuggestResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSuggesting(true);
      try {
        const results = await api.suggestLocations(searchQuery.trim());
        setSuggestResults(results || []);
      } catch (e) {
        console.warn('Suggest API error:', e);
      } finally {
        setIsSuggesting(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Live Auto-Suggest as user types in the Village Detector
  useEffect(() => {
    if (!detectVillageQuery || detectVillageQuery.trim().length < 2) {
      setVillageAutoSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const results = await api.suggestLocations(detectVillageQuery.trim(), selectedState, selectedDistrict);
        setVillageAutoSuggestions(results || []);
      } catch (e) {
        console.warn('Village suggestions error:', e);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [detectVillageQuery, selectedState, selectedDistrict]);

  // Trigger Pan-India Village Detection via Live Geocoding API
  const handleDetectVillage = async (vName) => {
    const q = (vName || detectVillageQuery).trim();
    if (!q || q.length < 2) return;

    setIsDetectingVillage(true);
    setDetectVillageError('');
    setDetectedVillageData(null);

    try {
      const res = await api.detectVillage(q, null, selectedDistrict, selectedState);
      if (res && res.found) {
        setDetectedVillageData(res);
        setSelectedVillage(res.village || res.name);
        if (res.district && districtOptions.includes(res.district)) {
          setSelectedDistrict(res.district);
        }
        if (res.lat && res.lon) {
          setCustomCoordinates({ lat: res.lat, lon: res.lon, elevation: res.elevation || 240 });
        }
      } else {
        setDetectVillageError(`Could not pinpoint "${q}". Please verify the spelling or check neighboring tehsils.`);
      }
    } catch (e) {
      console.warn('Village detection error:', e);
      setDetectVillageError('Network timeout while reaching village geocoding service.');
    } finally {
      setIsDetectingVillage(false);
    }
  };

  // Handle PIN code lookup
  const handlePincodeSearch = async (pin) => {
    setPincodeInput(pin);
    if (/^[1-9][0-9]{5}$/.test(pin.trim())) {
      setIsLookingUpPin(true);
      try {
        const res = await api.lookupPincode(pin.trim());
        setPincodeResults(res.results || []);
      } catch (e) {
        console.warn('PIN lookup notice:', e);
        setPincodeResults([]);
      } finally {
        setIsLookingUpPin(false);
      }
    } else {
      setPincodeResults([]);
    }
  };

  // High-Accuracy GPS Auto-Detection
  const handleGpsDetect = () => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your browser.');
      return;
    }

    setIsDetectingGps(true);
    setGpsError('');
    setGpsStatus('Acquiring high-accuracy satellite/device coordinates...');
    setDetectedGpsLocation(null);

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude, accuracy } = pos.coords;
        setGpsStatus(`GPS Satellite Lock: ${latitude.toFixed(4)}°N, ${longitude.toFixed(4)}°E (Accuracy: ±${Math.round(accuracy || 15)}m). Reverse-geocoding exact village...`);
        try {
          const exactAddr = await api.reverseGeocode(latitude, longitude);
          setDetectedGpsLocation(exactAddr);
          setGpsStatus('✅ Precise Location Verified!');
        } catch (err) {
          console.warn('Reverse geocode error:', err);
          setGpsError('Coordinate captured, but reverse-geocoding service was unreachable.');
        } finally {
          setIsDetectingGps(false);
        }
      },
      (err) => {
        setIsDetectingGps(false);
        setGpsError('GPS Access Denied: ' + err.message + '. Please allow location access in your browser address bar.');
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  };

  // Direct selection of an item from Suggestions, Detected Village, or PIN lookup
  const handleSelectExactLocation = (item) => {
    if (item.state && stateOptions.includes(item.state)) {
      setSelectedState(item.state);
    }
    if (item.district) setSelectedDistrict(item.district);
    if (item.village) setSelectedVillage(item.village);

    const chosenLat = item.lat ?? item.latitude;
    const chosenLon = item.lon ?? item.longitude;

    if (chosenLat != null && chosenLon != null) {
      setCustomCoordinates({ lat: chosenLat, lon: chosenLon, elevation: item.elevation || 240 });
    }

    const formatCleanName = (vName, dName, fallback) => {
      const base = (vName || fallback || '').trim();
      if (!dName) return base;
      if (base.toLowerCase().includes(dName.toLowerCase())) return base;
      return `${base} (${dName})`;
    };

    if (onSelectLocation) {
      onSelectLocation({
        name: formatCleanName(item.village, item.district, item.name || item.district),
        village: item.village || item.name,
        district: item.district,
        state: item.state,
        lat: chosenLat != null ? chosenLat : 21.1458,
        lon: chosenLon != null ? chosenLon : 79.0882,
        latitude: chosenLat != null ? chosenLat : 21.1458,
        longitude: chosenLon != null ? chosenLon : 79.0882,
        elevation: item.elevation || 240,
        climatology_mm: 12.0
      });
      onClose();
    }
  };

  // Confirm cascade selection
  const handleConfirm = () => {
    const vObj = activeVillageObject;
    const villageName = vObj?.name || selectedVillage || `${selectedDistrict} Sadar`;
    const chosenLat = vObj?.lat ?? customCoordinates?.lat ?? 21.1458;
    const chosenLon = vObj?.lon ?? customCoordinates?.lon ?? 79.0882;
    const cleanDisplayName = villageName.toLowerCase().includes((selectedDistrict || '').toLowerCase())
      ? villageName
      : `${villageName} (${selectedDistrict})`;

    const locPayload = {
      name: cleanDisplayName,
      village: villageName,
      district: selectedDistrict,
      state: selectedState,
      lat: chosenLat,
      lon: chosenLon,
      latitude: chosenLat,
      longitude: chosenLon,
      elevation: vObj?.elevation || customCoordinates?.elevation || 240,
      climatology_mm: 12.0
    };

    if (onSelectLocation) {
      onSelectLocation(locPayload);
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] relative z-10">
        
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-2.5">
            <div className="h-9 w-9 rounded-xl bg-sky-100 border border-sky-200 flex items-center justify-center text-sky-700">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-slate-900">
                Pan-India Location Directory (Direct State ➔ District ➔ Village)
              </h3>
              <p className="text-[11px] text-slate-500">
                Select State ➔ District ➔ Village directly, or detect ANY of India's 650,000+ villages
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Global Instant Search Bar with Live Suggestions */}
        <div className="p-4 border-b border-slate-200 bg-white relative">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search ANY Indian Village, Gram Panchayat, District, or PIN..."
              className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 font-semibold focus:outline-none focus:border-sky-500 focus:bg-white transition-all shadow-xs"
            />
            {isSuggesting && (
              <Loader2 className="absolute right-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-sky-600 animate-spin" />
            )}
            {searchQuery && !isSuggesting && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Autocomplete Suggestion Dropdown */}
          {suggestResults.length > 0 && (
            <div className="absolute left-4 right-4 top-full mt-1.5 bg-white border border-slate-200 rounded-2xl shadow-2xl z-30 max-h-64 overflow-y-auto divide-y divide-slate-100 animate-fadeIn">
              <div className="p-2 bg-slate-50 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Instant Pan-India Suggestions ({suggestResults.length} matches):
              </div>
              {suggestResults.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    handleSelectExactLocation(item);
                    setSearchQuery('');
                  }}
                  className="w-full px-4 py-2.5 text-left hover:bg-sky-50 flex items-center justify-between text-xs cursor-pointer group transition-colors"
                >
                  <div className="flex items-center space-x-2.5 truncate">
                    <MapPin className="h-4 w-4 text-sky-600 flex-shrink-0" />
                    <div className="truncate">
                      <strong className="text-slate-900 group-hover:text-sky-700 block truncate">
                        {item.name}
                      </strong>
                      <span className="text-[10px] text-slate-400 block truncate">
                        {[item.village, item.subDistrict, item.district, item.state].filter(Boolean).join(' • ')}
                      </span>
                    </div>
                  </div>
                  <span className="text-[10px] bg-slate-100 group-hover:bg-sky-100 text-slate-600 group-hover:text-sky-800 px-2 py-0.5 rounded-md font-semibold">
                    Select
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Quick Select Default Account Address if logged in */}
        {accountAddress && (
          <div className="mx-4 my-2 p-3 bg-gradient-to-r from-sky-50 via-indigo-50/40 to-blue-50 border border-sky-200 rounded-2xl flex items-center justify-between shadow-xs">
            <div className="flex items-center space-x-2.5 truncate">
              <div className="h-8 w-8 rounded-xl bg-sky-600 text-white flex items-center justify-center flex-shrink-0 shadow-xs">
                <Home className="h-4 w-4" />
              </div>
              <div className="truncate">
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-black uppercase tracking-wider bg-sky-100 text-sky-800 border border-sky-200 px-1.5 py-0.5 rounded-md">
                    Account Default
                  </span>
                  <span className="text-xs font-black text-slate-900 truncate">{accountAddress}</span>
                </div>
                <p className="text-[11px] text-slate-500 truncate">
                  Registered address for {user?.name || 'User'} ({user?.role || 'Farmer'})
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                onSelectLocation({
                  name: accountAddress,
                  village: user?.village,
                  district: user?.district,
                  state: user?.state,
                  lat: null,
                  lon: null,
                  isAccountReset: true
                });
                onClose();
              }}
              className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer flex items-center gap-1 flex-shrink-0 ml-2"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Use Account Address</span>
            </button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-5 pt-2 gap-2 text-xs font-bold">
          <button
            onClick={() => setActiveTab('cascade')}
            className={`pb-2.5 px-3 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'cascade'
                ? 'border-sky-600 text-sky-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Layers className="h-4 w-4" />
            <span>Direct Hierarchy (State ➔ District ➔ Village)</span>
          </button>

          <button
            onClick={() => setActiveTab('pincode')}
            className={`pb-2.5 px-3 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'pincode'
                ? 'border-sky-600 text-sky-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Hash className="h-4 w-4" />
            <span>PIN Code Lookup</span>
          </button>

          <button
            onClick={() => setActiveTab('gps')}
            className={`pb-2.5 px-3 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'gps'
                ? 'border-sky-600 text-sky-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Navigation className="h-4 w-4" />
            <span>GPS Satellite Lock</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1">
          
          {/* TAB 1: DIRECT CASCADING HIERARCHY (STATE ➔ DISTRICT ➔ VILLAGE DIRECTLY) */}
          {activeTab === 'cascade' && (
            <div className="space-y-4">
              
              {/* Row 1: State & District Direct Selection */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {/* 1. State Selector (All 36 States & UTs) */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center gap-1.5">
                    <Building2 className="h-3.5 w-3.5 text-sky-600" />
                    <span>1. State / Union Territory ({stateOptions.length})</span>
                  </label>
                  <select
                    value={selectedState}
                    onChange={(e) => {
                      const newState = e.target.value;
                      setSelectedState(newState);
                      const dists = ALL_INDIA_DISTRICTS_CATALOG[newState] || [];
                      if (dists.length > 0) setSelectedDistrict(dists[0]);
                    }}
                    className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-900 font-semibold rounded-xl px-3 py-2.5 focus:outline-none focus:border-sky-500 cursor-pointer shadow-xs"
                  >
                    {stateOptions.map(state => (
                      <option key={state} value={state}>{state}</option>
                    ))}
                  </select>
                </div>

                {/* 2. District Selector (All 784 Districts) */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Compass className="h-3.5 w-3.5 text-indigo-600" />
                      <span>2. District ({districtOptions.length} in {selectedState})</span>
                    </span>
                    {isLoadingVillages && (
                      <span className="text-[10px] text-sky-600 font-medium flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" /> Loading villages...
                      </span>
                    )}
                  </label>
                  <select
                    value={selectedDistrict}
                    onChange={(e) => setSelectedDistrict(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-900 font-semibold rounded-xl px-3 py-2.5 focus:outline-none focus:border-sky-500 cursor-pointer shadow-xs"
                  >
                    {districtOptions.map(dist => (
                      <option key={dist} value={dist}>{dist}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Row 2: DIRECT VILLAGE SELECTION OVER ALL DISTRICT VILLAGES */}
              <div className="pt-2 space-y-3">
                {/* Header with counts and Tehsil summary */}
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <Home className="h-4 w-4 text-emerald-600" />
                    <span>3. Villages in {selectedDistrict} ({districtVillages.length} Official Villages)</span>
                  </label>
                  <span className="text-[10px] text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full font-bold shadow-xs">
                    {availableSubDistricts.length > 0 ? `${availableSubDistricts.length} Tehsils • ` : ''}{districtVillages.length} Verified
                  </span>
                </div>

                {/* Sub-District / Tehsil Filter Tabs */}
                {availableSubDistricts.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] font-bold text-slate-500">
                      <span>Filter by Administrative Tehsil / Block:</span>
                      <span className="text-sky-700 font-semibold">{selectedSubDistrict === 'ALL' ? 'All Tehsils' : `Tehsil: ${selectedSubDistrict}`}</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5 pb-0.5">
                      <button
                        type="button"
                        onClick={() => setSelectedSubDistrict('ALL')}
                        className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer shadow-xs ${
                          selectedSubDistrict === 'ALL'
                            ? 'bg-sky-600 text-white shadow-sky-600/30'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        All ({districtVillages.length})
                      </button>
                      {availableSubDistricts.map(sub => {
                        const count = subDistrictCounts[sub] || 0;
                        const isSelected = selectedSubDistrict === sub;
                        return (
                          <button
                            key={sub}
                            type="button"
                            onClick={() => setSelectedSubDistrict(sub)}
                            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer shadow-xs flex items-center gap-1 ${
                              isSelected
                                ? 'bg-sky-600 text-white font-bold shadow-sky-600/30'
                                : 'bg-slate-100 text-slate-700 hover:bg-sky-50 hover:text-sky-700'
                            }`}
                          >
                            <span>{sub}</span>
                            <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isSelected ? 'bg-sky-700 text-sky-100' : 'bg-slate-200 text-slate-600'}`}>
                              {count}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Prominent Regional Hubs Quick-Pick Shortcuts */}
                {PROMINENT_HUBS[selectedDistrict] && PROMINENT_HUBS[selectedDistrict].length > 0 && (
                  <div className="bg-amber-50/70 border border-amber-200/90 rounded-xl p-2.5 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-[11px] font-bold text-amber-900">
                      <Sparkles className="h-3.5 w-3.5 text-amber-600" />
                      <span>Prominent Hubs & Agricultural Centers ({selectedDistrict}):</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {PROMINENT_HUBS[selectedDistrict].map((hub, idx) => {
                        const isChosen = selectedVillage === hub.name;
                        return (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => {
                              setSelectedVillage(hub.name);
                              setCustomCoordinates({ lat: hub.lat, lon: hub.lon, elevation: hub.elevation });
                            }}
                            title={hub.desc}
                            className={`px-2.5 py-1 rounded-lg text-xs transition-all cursor-pointer flex items-center gap-1 shadow-2xs ${
                              isChosen
                                ? 'bg-amber-600 text-white font-bold'
                                : 'bg-white text-slate-800 hover:bg-amber-100 hover:text-amber-900 border border-amber-200 font-medium'
                            }`}
                          >
                            <span>{hub.name}</span>
                            <span className="text-[10px] opacity-75">({hub.subDistrict})</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Instant Search Bar with Live Match Counter */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                  <input
                    type="text"
                    value={villageFilterQuery}
                    onChange={(e) => setVillageFilterQuery(e.target.value)}
                    placeholder={`Type to search ANY village in ${selectedDistrict}... (e.g. ${selectedDistrict === 'Maharajganj' ? 'Sonauli, Siswa, Bargadwa' : selectedDistrict === 'Lucknow' ? 'Malihabad, Mohanlalganj, Kakori' : 'Kasba, Rampur'})`}
                    className="w-full pl-9 pr-24 py-2 bg-slate-50 border border-slate-200 text-xs font-semibold rounded-xl text-slate-900 focus:bg-white focus:outline-none focus:border-sky-500 shadow-xs"
                  />
                  <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
                    {villageFilterQuery && (
                      <button
                        type="button"
                        onClick={() => setVillageFilterQuery('')}
                        className="text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                    <span className="text-[10px] font-bold text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">
                      {filteredVillages.length} found
                    </span>
                  </div>
                </div>

                {/* Interactive Visual Village Card Browser */}
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-2 max-h-56 overflow-y-auto space-y-1 shadow-inner">
                  {filteredVillages.length === 0 ? (
                    <div className="py-6 text-center text-xs text-slate-400">
                      No villages found matching "{villageFilterQuery}". Try typing another name or select "All ({districtVillages.length})".
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                      {filteredVillages.slice(0, 150).map((v, i) => {
                        const vName = v.name || v.village || v;
                        const isSelected = selectedVillage === vName;
                        return (
                          <button
                            key={i}
                            type="button"
                            onClick={() => {
                              setSelectedVillage(vName);
                              if (v.lat && v.lon) {
                                setCustomCoordinates({ lat: v.lat, lon: v.lon, elevation: v.elevation || 240 });
                              }
                            }}
                            className={`text-left p-2 rounded-lg border transition-all cursor-pointer flex items-center justify-between text-xs group ${
                              isSelected
                                ? 'bg-sky-50 border-sky-500 text-sky-900 shadow-xs ring-1 ring-sky-500'
                                : 'bg-white border-slate-200 text-slate-800 hover:bg-slate-100 hover:border-slate-300'
                            }`}
                          >
                            <div className="truncate pr-2">
                              <span className={`block truncate ${isSelected ? 'font-black text-sky-950' : 'font-semibold text-slate-800 group-hover:text-sky-700'}`}>
                                {vName}
                              </span>
                              {v.subDistrict && (
                                <span className="text-[10px] text-slate-400 block truncate">
                                  Tehsil: <strong className="text-slate-600">{v.subDistrict}</strong>
                                </span>
                              )}
                            </div>
                            {isSelected ? (
                              <CheckCircle2 className="h-4 w-4 text-sky-600 flex-shrink-0" />
                            ) : (
                              <span className="text-[10px] text-slate-300 group-hover:text-slate-500 flex-shrink-0">
                                Select
                              </span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  )}
                  {filteredVillages.length > 150 && (
                    <div className="pt-2 text-center text-[10px] font-bold text-slate-400 border-t border-slate-200">
                      Showing first 150 of {filteredVillages.length} villages. Type above in the search box to pinpoint instantly.
                    </div>
                  )}
                </div>

                {/* Quick Selection Status & Direct "Apply Location" Card */}
                <div className="bg-white border border-sky-200 rounded-xl p-3 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-lg bg-sky-100 border border-sky-200 flex items-center justify-center text-sky-700 flex-shrink-0">
                      <MapPin className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Active Pick:</span>
                        <strong className="text-xs font-black text-slate-900">{activeVillageObject.name}</strong>
                        {activeVillageObject.subDistrict && (
                          <span className="text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200 px-1.5 py-0.2 rounded">
                            {activeVillageObject.subDistrict}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500 block">
                        {selectedDistrict}, {selectedState} • {activeVillageObject.lat ? `${activeVillageObject.lat.toFixed(4)}°N, ${activeVillageObject.lon.toFixed(4)}°E` : 'Calibrated coordinates'} (Elevation: {activeVillageObject.elevation || 240}m)
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleConfirm()}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all cursor-pointer shadow-sm hover:shadow flex items-center justify-center gap-1.5 flex-shrink-0"
                  >
                    <Check className="h-3.5 w-3.5" />
                    <span>Apply This Location</span>
                  </button>
                </div>
              </div>

              {/* 🌟 PAN-INDIA VILLAGE DETECTOR (DETECT ANY VILLAGE IN INDIA VIA LIVE API) 🌟 */}
              <div className="bg-gradient-to-r from-sky-50 to-indigo-50 border border-sky-200 rounded-2xl p-4 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-sky-600 text-white shadow-xs">
                      <Radar className="h-4 w-4" />
                    </div>
                    <div>
                      <strong className="text-xs font-extrabold text-slate-900 block">
                        Search or Detect ANY Village in India (Live Satellite API):
                      </strong>
                      <span className="text-[11px] text-slate-500">
                        Type any village name in {selectedDistrict} or across India (e.g. Bakhira, Pipraich, Kelod, Khandala...)
                      </span>
                    </div>
                  </div>
                  {isDetectingVillage && (
                    <span className="text-[11px] font-bold text-sky-700 flex items-center gap-1">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" /> Detecting...
                    </span>
                  )}
                </div>

                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={detectVillageQuery}
                      onChange={(e) => setDetectVillageQuery(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleDetectVillage();
                        }
                      }}
                      placeholder={`Type any village name in ${selectedDistrict} or all India...`}
                      className="w-full bg-white border border-sky-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 font-semibold focus:outline-none focus:border-sky-500 shadow-xs"
                    />
                    {detectVillageQuery && (
                      <button
                        onClick={() => {
                          setDetectVillageQuery('');
                          setDetectedVillageData(null);
                          setVillageAutoSuggestions([]);
                        }}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => handleDetectVillage()}
                    disabled={isDetectingVillage || !detectVillageQuery.trim()}
                    className="bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white font-bold text-xs px-4 py-2 rounded-xl transition-all cursor-pointer shadow-sm flex items-center gap-1.5 flex-shrink-0"
                  >
                    <Search className="h-3.5 w-3.5" />
                    <span>Detect Village</span>
                  </button>
                </div>

                {/* Auto-Suggestion Pills while typing */}
                {villageAutoSuggestions.length > 0 && !detectedVillageData && (
                  <div className="space-y-1 pt-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Quick Matches (Click to Select):
                    </span>
                    <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                      {villageAutoSuggestions.map((item, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            handleDetectVillage(item.village || item.name);
                            setVillageAutoSuggestions([]);
                          }}
                          className="text-xs bg-white hover:bg-sky-600 text-slate-800 hover:text-white border border-sky-200 font-semibold px-2.5 py-1 rounded-lg transition-all cursor-pointer shadow-xs flex items-center gap-1"
                        >
                          <Home className="h-3 w-3 text-sky-600" />
                          <span>{item.village || item.name}</span>
                          <span className="text-[10px] opacity-70">({item.district})</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Detected Village Card with Instant Confirmation */}
                {detectedVillageData && (
                  <div className="bg-white border border-emerald-300 rounded-xl p-3.5 shadow-sm animate-fadeIn space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
                          <CheckCircle2 className="h-4 w-4" />
                        </div>
                        <div>
                          <strong className="text-xs font-black text-slate-900 block">
                            Village Verified: {detectedVillageData.name}
                          </strong>
                          <span className="text-[11px] text-slate-500 block">
                            District: <span className="font-bold text-slate-700">{detectedVillageData.district}</span>, {detectedVillageData.state}
                          </span>
                        </div>
                      </div>

                      <span className="text-[10px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded">
                        {detectedVillageData.lat.toFixed(4)}°N, {detectedVillageData.lon.toFixed(4)}°E
                      </span>
                    </div>

                    <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                      <span className="text-[10px] text-slate-500 font-medium">
                        Elevation: {detectedVillageData.elevation}m • Source: {detectedVillageData.source}
                      </span>
                      <button
                        onClick={() => handleSelectExactLocation(detectedVillageData)}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-3.5 py-1.5 rounded-lg transition-all cursor-pointer shadow-sm flex items-center gap-1"
                      >
                        <Check className="h-3 w-3" />
                        <span>Apply This Village</span>
                      </button>
                    </div>
                  </div>
                )}

                {detectVillageError && (
                  <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 font-semibold">
                    {detectVillageError}
                  </div>
                )}
              </div>

              {/* Selection Summary Pill */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs text-slate-600">
                <span>Selected: <strong className="text-slate-900">{selectedVillage}</strong>, District: <strong>{selectedDistrict}</strong>, {selectedState}</span>
                <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-md border border-emerald-200">
                  Ready to Apply
                </span>
              </div>
            </div>
          )}

          {/* TAB 2: PIN CODE LOOKUP */}
          {activeTab === 'pincode' && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
                <label className="block text-xs font-bold text-slate-800">
                  Enter 6-Digit Postal PIN Code:
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    maxLength={6}
                    value={pincodeInput}
                    onChange={(e) => handlePincodeSearch(e.target.value)}
                    placeholder="e.g. 201206, 273001, 752001, 440001"
                    className="flex-1 bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 font-bold focus:outline-none focus:border-sky-500 shadow-xs"
                  />
                  {isLookingUpPin && (
                    <div className="px-3 py-2 text-xs font-bold text-sky-700 flex items-center gap-1">
                      <Loader2 className="h-4 w-4 animate-spin" /> Resolving...
                    </div>
                  )}
                </div>
              </div>

              {/* PIN Code Post Offices / Villages List */}
              {pincodeResults.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-700 block">
                    Found {pincodeResults.length} Gram Panchayats / Post Offices under PIN {pincodeInput}:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto">
                    {pincodeResults.map((item, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSelectExactLocation(item)}
                        className="p-3 text-left bg-white hover:bg-sky-50 border border-slate-200 hover:border-sky-300 rounded-xl transition-all cursor-pointer shadow-xs group flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between gap-1 mb-1">
                            <strong className="text-xs text-slate-900 group-hover:text-sky-700 block truncate">
                              {item.village || item.name}
                            </strong>
                            <span className="text-[10px] font-mono font-bold bg-sky-50 text-sky-700 border border-sky-200 px-1.5 py-0.2 rounded flex-shrink-0">
                              {item.lat ? `${item.lat.toFixed(4)}°N, ${item.lon.toFixed(4)}°E` : 'Exact PIN'}
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-500 block truncate">
                            {item.block ? `Tehsil: ${item.block} • ` : ''}{item.district}, {item.state}
                          </span>
                        </div>
                        <div className="mt-2 pt-1 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                          <span>PIN: {item.pincode}</span>
                          <span className="text-sky-600 font-bold group-hover:underline">Lock Location ➔</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: HIGH-ACCURACY GPS */}
          {activeTab === 'gps' && (
            <div className="p-6 bg-slate-50 border border-slate-200 rounded-2xl text-center space-y-4">
              <div className="h-14 w-14 rounded-full bg-sky-100 border border-sky-200 text-sky-700 flex items-center justify-center mx-auto shadow-sm">
                <Navigation className={`h-7 w-7 ${isDetectingGps ? 'animate-spin text-sky-600' : ''}`} />
              </div>
              
              <div>
                <h4 className="text-base font-extrabold text-slate-900">
                  Instant Satellite GPS Geolocation
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  Acquires your device coordinates and resolves your exact Village and District.
                </p>
              </div>

              {gpsStatus && (
                <div className="p-3 bg-sky-50 border border-sky-200 rounded-xl text-xs text-sky-900 font-semibold">
                  {gpsStatus}
                </div>
              )}

              {gpsError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 font-semibold">
                  {gpsError}
                </div>
              )}

              {detectedGpsLocation && (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-left space-y-1.5 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-emerald-950 uppercase tracking-wider">
                      Verified Location:
                    </span>
                    <span className="text-[10px] font-bold bg-emerald-200 text-emerald-900 px-2 py-0.5 rounded">
                      GPS Lock
                    </span>
                  </div>
                  <p className="text-sm font-bold text-slate-900">
                    {detectedGpsLocation.name}
                  </p>
                  <p className="text-xs text-slate-600">
                    District: {detectedGpsLocation.district}, {detectedGpsLocation.state}
                  </p>
                  <button
                    onClick={() => handleSelectExactLocation(detectedGpsLocation)}
                    className="mt-2 w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs py-2 rounded-xl transition-all cursor-pointer shadow-sm"
                  >
                    Apply Detected Village & Coordinates
                  </button>
                </div>
              )}

              <button
                onClick={handleGpsDetect}
                disabled={isDetectingGps}
                className="bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white font-bold text-xs px-6 py-2.5 rounded-xl transition-all cursor-pointer shadow-md inline-flex items-center gap-2"
              >
                <Navigation className="h-4 w-4" />
                <span>{isDetectingGps ? 'Acquiring Satellite Lock...' : 'Detect My Exact Location'}</span>
              </button>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Current: <strong className="text-slate-800">{currentLocationName}</strong>
          </span>

          <div className="flex items-center space-x-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="px-5 py-2 rounded-xl text-xs font-bold bg-sky-600 hover:bg-sky-700 text-white transition-all cursor-pointer shadow-md flex items-center gap-1.5"
            >
              <Check className="h-3.5 w-3.5" />
              <span>Apply Location</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
