import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { 
  LineChart as LineChartIcon, 
  CloudRain, 
  ShieldAlert, 
  Waves, 
  Database, 
  Loader2,
  Compass,
  AlertTriangle,
  ArrowRight,
  Gauge,
  ThermometerSnowflake,
  Wind,
  RefreshCw,
  MapPin
} from 'lucide-react';
import api from '../api';
import { getTranslation } from '../translations';
import CycloneRadarMap from '../components/CycloneRadarMap';
import CycloneStatusPanel from '../components/CycloneStatusPanel';

export default function ClimatePage({ language = 'en', location = 'Nagpur', latitude = null, longitude = null }) {
  const t = getTranslation(language)?.climate || {};
  const [activeSubTab, setActiveSubTab] = useState('pressure_cyclone'); // 'pressure_cyclone' or 'historical_trends'
  const [climateData, setClimateData] = useState(null);
  const [cycloneData, setCycloneData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [selectedDecade, setSelectedDecade] = useState('ALL');
  const [selectedSystemIdx, setSelectedSystemIdx] = useState(0);
  const [cycloneRisk, setCycloneRisk] = useState(null);

  const fetchData = () => {
    setIsLoading(true);
    setHasError(false);
    Promise.allSettled([
      api.getClimateTrends(),
      api.getCycloneSystems(),
      api.getCycloneRisk(location, latitude, longitude)
    ]).then(([trendsRes, cycloneRes, riskRes]) => {
      if (riskRes.status === 'fulfilled' && riskRes.value) {
        setCycloneRisk(riskRes.value);
      } else {
        setCycloneRisk(null);
      }
      let loadedAny = false;
      if (trendsRes.status === 'fulfilled' && trendsRes.value) {
        setClimateData(trendsRes.value);
        loadedAny = true;
      }
      if (cycloneRes.status === 'fulfilled' && cycloneRes.value) {
        setCycloneData(cycloneRes.value);
        loadedAny = true;
      }
      if (!loadedAny) {
        setHasError(true);
      }
    }).catch(err => {
      console.error('Climate data load error:', err);
      setHasError(true);
    }).finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchData();
    // Re-run when the user switches location so the per-location cyclone risk
    // follows the rest of the app.
  }, [location, latitude, longitude]);

  const rawTrends = climateData?.cyclone_trends || [];
  const filteredTrends = selectedDecade === 'ALL' 
    ? rawTrends 
    : rawTrends.filter(r => r.year >= parseInt(selectedDecade) && r.year <= parseInt(selectedDecade) + 25);

  const baseline = climateData?.climatology_baseline || {};
  const systems = cycloneData?.systems || [];
  const activeSystem = systems[selectedSystemIdx] || systems[0] || null;

  // Safe helper to extract category text whether it is an object or string
  const getCategoryTitle = (cat) => {
    if (!cat) return 'Cyclonic System';
    if (typeof cat === 'object') return cat.title || cat.code || 'Cyclonic System';
    return String(cat);
  };

  const getCategorySeverity = (cat) => {
    if (typeof cat === 'object') return cat.severity || 'WATCH';
    return 'HIGH';
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner & Module Selector */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold text-sky-700 mb-1 uppercase tracking-wider">
              <LineChartIcon className="h-3.5 w-3.5" />
              <span>{t.badge || 'Synoptic Meteorology & Climatology Engine'}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              {t.title || 'Climate & Cyclonic Intelligence'}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              {t.subtitle || 'Real-time synoptic barometric tracking, cyclone radar & 131-year IMD archives'}
            </p>
          </div>

          {/* Sub-Tab Navigation Toggle */}
          <div className="flex items-center bg-slate-100 p-1 rounded-2xl border border-slate-200 self-start md:self-auto shadow-xs">
            <button
              onClick={() => setActiveSubTab('pressure_cyclone')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeSubTab === 'pressure_cyclone'
                  ? 'bg-white text-rose-700 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {t.realTimeCyclones || '🌪️ Cyclone & Pressure Genesis'}
            </button>
            <button
              onClick={() => setActiveSubTab('historical_trends')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeSubTab === 'historical_trends'
                  ? 'bg-white text-sky-700 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {t.historicalTrends || '📊 131-Year Historical Archives'}
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="bg-white border border-slate-200 rounded-3xl p-16 text-center text-slate-500 flex flex-col items-center justify-center shadow-sm">
          <Loader2 className="h-9 w-9 animate-spin text-rose-600 mb-3" />
          <p className="text-sm font-bold text-slate-900">
            {language === 'hi' 
              ? 'वायुमंडलीय दबाव क्षेत्र व चक्रवात पथ लोड हो रहा है...' 
              : 'Computing synoptic barometric pressure fields & cyclone trajectory...'}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Analyzing Atkinson-Holliday wind relationships & IMD radar data
          </p>
        </div>
      ) : hasError ? (
        <div className="bg-white border border-rose-200 rounded-3xl p-12 text-center shadow-sm">
          <AlertTriangle className="h-10 w-10 text-rose-500 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-900">Unable to load Synoptic Data</h3>
          <p className="text-xs text-slate-500 mt-1 mb-4">
            Could not connect to the meteorological analytics service. Please verify the backend is running.
          </p>
          <button
            onClick={fetchData}
            className="inline-flex items-center gap-2 px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 transition-colors cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Retry Connection
          </button>
        </div>
      ) : activeSubTab === 'pressure_cyclone' ? (
        /* TAB 1: GENUINE PRESSURE GRADIENT & CYCLONE GENESIS */
        <div className="space-y-6">
          {/* Detection status: unavailable / nothing found / per-location risk */}
          <CycloneStatusPanel
            scan={cycloneData}
            risk={cycloneRisk}
            locationName={location}
            language={language}
          />

          {/* Active Synoptic Systems Selector Pills */}
          {systems.length > 0 && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex-shrink-0">
                {language === 'en' ? 'Active Marine Systems:' : 'सक्रिय समुद्री अवदाब / चक्रवात:'}
              </span>
              {systems.map((sys, idx) => (
                <button
                  key={sys.id || idx}
                  onClick={() => setSelectedSystemIdx(idx)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer border ${
                    selectedSystemIdx === idx
                      ? 'bg-rose-600 text-white border-rose-600 shadow-xs'
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  🌪️ {sys.name} ({getCategoryTitle(sys.category)})
                </button>
              ))}
            </div>
          )}

          {/* Interactive Synoptic Radar Map */}
          {activeSystem && (
            <div className="w-full">
              <CycloneRadarMap activeSystem={activeSystem} />
            </div>
          )}

          {/* Active System Detailed Overview */}
          {activeSystem && (
            <div className="bg-gradient-to-r from-rose-50 via-white to-amber-50 border border-rose-200 rounded-3xl p-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-rose-100">
                <div>
                  <span className={`text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                    getCategorySeverity(activeSystem.category) === 'HIGH' 
                      ? 'bg-rose-100 text-rose-800 border-rose-200' 
                      : 'bg-amber-100 text-amber-800 border-amber-200'
                  }`}>
                    {getCategoryTitle(activeSystem.category)}
                  </span>
                  <h2 className="text-2xl font-black text-slate-900 mt-1">
                    {activeSystem.name}
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5">
                    <MapPin className="h-3 w-3 text-rose-500" />
                    <span>{activeSystem.basin}</span>
                    <span>•</span>
                    <span>
                      {language === 'en' ? 'Current Center:' : 'वर्तमान स्थान:'}{' '}
                      {activeSystem.current_position?.location_name
                        || (activeSystem.current_position?.lat != null
                            ? `${activeSystem.current_position.lat}°N, ${activeSystem.current_position.lon}°E`
                            : '—')}
                    </span>
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="bg-white px-3.5 py-2 rounded-2xl border border-rose-200 text-center shadow-xs">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">{language === 'en' ? 'Central Pressure' : 'केंद्रीय दबाव'}</span>
                    <span className="text-xl font-black text-rose-700">{activeSystem.central_pressure_hpa} <span className="text-xs text-slate-500">hPa</span></span>
                  </div>
                  <div className="bg-white px-3.5 py-2 rounded-2xl border border-rose-200 text-center shadow-xs">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">{language === 'en' ? 'Peak Wind' : 'अधिकतम हवा'}</span>
                    <span className="text-xl font-black text-sky-700">{activeSystem.vmax_kmh ?? activeSystem.max_sustained_wind_kmh ?? '—'} <span className="text-xs text-slate-500">km/h</span></span>
                  </div>
                  {activeSystem.gust_kmh && (
                    <div className="bg-white px-3.5 py-2 rounded-2xl border border-amber-200 text-center shadow-xs">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">{language === 'en' ? 'Gusts' : 'झोंके'}</span>
                      <span className="text-xl font-black text-amber-700">{activeSystem.gust_kmh} <span className="text-xs text-slate-500">km/h</span></span>
                    </div>
                  )}
                </div>
              </div>

              {/* Landfall & Forecast Warning */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs mb-4">
                <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                  <span className="text-slate-500 font-medium block">{language === 'en' ? 'Projected Landfall Zone:' : 'अनुमानित लैंडफॉल:'}</span>
                  <strong className="text-slate-900 font-bold">
                    {activeSystem.landfall_prediction?.predicted_point
                      || activeSystem.landfall_prediction?.target_coast
                      || activeSystem.projected_landfall
                      || 'Not forecast — track projection only'}
                  </strong>
                </div>
                <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                  <span className="text-slate-500 font-medium block">{language === 'en' ? 'High Pressure Steering:' : 'स्टीयरिंग रिड्ज प्रभाव:'}</span>
                  <strong className="text-slate-900 font-bold">
                    {activeSystem.high_pressure_ridge?.steering_influence
                      || (activeSystem.movement
                          ? `${activeSystem.movement.direction} at ${activeSystem.movement.speed_kmh} km/h`
                          : (activeSystem.movement_direction
                              ? `${activeSystem.movement_direction} at ${activeSystem.speed_kmh} km/h`
                              : 'Not resolved'))}
                  </strong>
                </div>
                <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                  <span className="text-slate-500 font-medium block">{language === 'en' ? 'Storm Surge Potential:' : 'तूफानी ज्वार (Surge):'}</span>
                  <strong className="text-rose-700 font-bold">
                    {activeSystem.estimated_surge_m ?? activeSystem.storm_surge_meters ?? '—'} meters
                  </strong>
                </div>
              </div>

              {/* High-Alert Coastal Districts */}
              {activeSystem.landfall_prediction?.impact_districts?.length > 0 && (
                <div className="mb-4 bg-white p-3.5 rounded-2xl border border-rose-100">
                  <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-2">
                    {language === 'en' ? '🚨 High-Alert Coastal Impact Districts:' : '🚨 प्रभावित होने वाले उच्च जोखिम तटीय जिले:'}
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {activeSystem.landfall_prediction.impact_districts.map((d, dIdx) => (
                      <span key={dIdx} className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-xl shadow-2xs">
                        <strong className="text-slate-800">{d.name}</strong>
                        <span className="text-slate-400 text-[10px]">({d.state})</span>
                        <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-md ${
                          d.risk === 'EXTREME' 
                            ? 'bg-rose-600 text-white' 
                            : d.risk === 'HIGH' 
                              ? 'bg-rose-100 text-rose-800' 
                              : 'bg-amber-100 text-amber-800'
                        }`}>
                          {d.risk}
                        </span>
                        {d.wind && <span className="text-slate-500 text-[10px]">💨 {d.wind}</span>}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Multi-Day Track Table */}
              {(activeSystem.forecast_track || activeSystem.track_forecast) && (
                <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto shadow-xs p-4">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                    {language === 'en' ? 'Projected Track & Intensity Trajectory:' : 'संभावित चक्रवात पथ व तीव्रता प्रक्षेपण (Track Forecast):'}
                  </h4>
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-100 text-slate-400 uppercase font-semibold text-[10px]">
                        <th className="pb-2">{language === 'en' ? 'Timestamp' : 'समय'}</th>
                        <th className="pb-2">{language === 'en' ? 'Position' : 'अक्षांश/देशांतर'}</th>
                        <th className="pb-2">{language === 'en' ? 'Pressure (hPa)' : 'दबाव (hPa)'}</th>
                        <th className="pb-2">{language === 'en' ? 'Intensity' : 'हवा / तीव्रता'}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {(activeSystem.forecast_track || activeSystem.track_forecast).map((step, sIdx) => (
                        <tr key={sIdx} className="hover:bg-slate-50">
                          <td className="py-2 font-bold text-slate-800">{step.hour || step.time}</td>
                          <td className="py-2 text-slate-600">{step.lat}°N, {step.lon}°E</td>
                          <td className="py-2 font-bold text-rose-700">{step.pressure_hpa || step.pressure}</td>
                          <td className="py-2 text-sky-700 font-semibold">{step.intensity || step.wind || step.stage}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Genuine Meteorological Physics Explanation */}
          <div className="bg-gradient-to-r from-sky-50 via-white to-indigo-50 border border-sky-100 rounded-2xl p-5 text-xs text-slate-700 shadow-sm leading-relaxed">
            <h4 className="font-extrabold text-slate-900 mb-1 flex items-center gap-1.5 text-sm">
              <Compass className="h-4 w-4 text-sky-600" />
              {language === 'en' ? 'How High vs Low Pressure Systems Create Cyclones:' : 'वायुमंडलीय दबाव से चक्रवात कैसे उत्पन्न होते हैं:'}
            </h4>
            <p className="mt-1 text-slate-600">
              {cycloneData?.physics_explanation || 'Cyclogenesis is driven by intense marine surface heating causing deep convective updrafts and low pressure formation.'}
            </p>
            <div className="mt-3 pt-3 border-t border-slate-200/80 flex flex-wrap items-center justify-between text-[11px] text-slate-500 font-mono">
              <span>Atkinson-Holliday: Vmax = 6.7 × (ΔP)^0.644 knots</span>
              <span>Central Deficit: ΔP = {activeSystem?.central_pressure_hpa ? (1012 - activeSystem.central_pressure_hpa).toFixed(1) : '30.0'} hPa</span>
            </div>
          </div>
        </div>
      ) : (
        /* TAB 2: HISTORICAL 131-YEAR DISASTER ARCHIVES (1891-2021) */
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-extrabold text-slate-900">
              {t.title || '131-Year Cyclone Frequency Trends (1891–2021)'}
            </h2>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500 font-semibold">{t.filterPeriod || 'Filter Period:'}</span>
              <select
                value={selectedDecade}
                onChange={(e) => setSelectedDecade(e.target.value)}
                className="bg-slate-50 border border-slate-200 text-xs text-slate-800 font-bold rounded-xl px-3 py-1.5 focus:outline-none cursor-pointer shadow-xs"
              >
                <option value="ALL">{t.allSpan || 'Full Span (1891–2021)'}</option>
                <option value="2000">Modern Era (2000–2021)</option>
                <option value="1980">Late 20th Cent (1980–1999)</option>
                <option value="1960">Mid 20th Cent (1960–1979)</option>
                <option value="1920">Early 20th Cent (1920–1939)</option>
              </select>
            </div>
          </div>

          {/* Macro Summary Stats (4 Metrics) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-[11px] text-slate-500 font-bold uppercase">{t.totalCyclones || 'Total Cyclones'}</span>
              <div className="text-2xl font-black text-sky-700 mt-1">676</div>
              <p className="text-[10px] text-slate-500">1891–2021 Record</p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-[11px] text-slate-500 font-bold uppercase">{t.severeCyclones || 'Severe Cyclones'}</span>
              <div className="text-2xl font-black text-rose-700 mt-1">325</div>
              <p className="text-[10px] text-slate-500">48.1% of all storms</p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-[11px] text-slate-500 font-bold uppercase">{t.bobShare || 'Bay of Bengal Share'}</span>
              <div className="text-2xl font-black text-indigo-700 mt-1">77.8%</div>
              <p className="text-[10px] text-slate-500">526 Cyclones in BOB</p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-[11px] text-slate-500 font-bold uppercase">{t.asShare || 'Arabian Sea Share'}</span>
              <div className="text-2xl font-black text-amber-700 mt-1">20.1%</div>
              <p className="text-[10px] text-slate-500">136 Cyclones in AS</p>
            </div>
          </div>

          {/* Chart 1: Bay of Bengal vs Arabian Sea Cyclone Trajectory */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Waves className="h-4 w-4 text-sky-600" />
                <h3 className="text-sm font-extrabold text-slate-900">{t.basinCompTitle || 'Ocean Basin Comparison: Bay of Bengal vs Arabian Sea'}</h3>
              </div>
              <div className="flex items-center space-x-4 text-xs font-semibold">
                <span className="flex items-center gap-1.5 text-slate-600">
                  <span className="h-2.5 w-2.5 rounded-full bg-indigo-600 inline-block"></span> Bay of Bengal (BOB)
                </span>
                <span className="flex items-center gap-1.5 text-slate-600">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500 inline-block"></span> Arabian Sea (AS)
                </span>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart key={`area_${selectedDecade}`} data={filteredTrends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="bobGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.25}/>
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0}/>
                    </linearGradient>
                    <linearGradient id="asGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#d97706" stopOpacity={0.25}/>
                      <stop offset="95%" stopColor="#d97706" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '0.75rem', fontSize: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                    labelStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                  />
                  <Area type="monotone" dataKey="cyclones_bob" stroke="#4f46e5" strokeWidth={2} fillOpacity={1} fill="url(#bobGrad)" name="Bay of Bengal" />
                  <Area type="monotone" dataKey="cyclones_as" stroke="#d97706" strokeWidth={2} fillOpacity={1} fill="url(#asGrad)" name="Arabian Sea" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Gridded Rainfall Climatology Insights Panel */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center space-x-2 mb-3">
              <CloudRain className="h-4 w-4 text-sky-600" />
              <h3 className="text-sm font-extrabold text-slate-900">{t.climatologyTitle || 'IMD Gridded Rainfall Climatology Baseline'}</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              Extracted from NetCDF gridded analysis (<strong>rf_p25_jan_clm.nc</strong>), providing high-resolution January 
              rainfall climatological baselines across 17,415 grid cells (0.25° × 0.25° resolution).
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
              {baseline.sample_regional_baselines_mm && Object.entries(baseline.sample_regional_baselines_mm).map(([city, val]) => (
                <div key={city} className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-center shadow-xs">
                  <p className="text-slate-500 font-bold text-[11px] truncate">{city}</p>
                  <p className="text-lg font-black text-sky-700 mt-1">{val} mm</p>
                  <p className="text-[10px] text-slate-400">Jan Baseline</p>
                </div>
              ))}
            </div>

            <div className="mt-5 pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-400 gap-1">
              <span className="flex items-center gap-1 font-medium">
                <Database className="h-3 w-3 text-sky-600" />
                Data Provenance: India Meteorological Department, Pune (National Climate Centre)
              </span>
              <span>Grid Bounds: 6.5°N–38.5°N, 66.5°E–100.0°E</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
