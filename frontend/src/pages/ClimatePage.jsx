import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
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
  Wind
} from 'lucide-react';
import api from '../api';
import { getTranslation } from '../translations';

export default function ClimatePage({ language = 'en' }) {
  const t = getTranslation(language).climate;
  const [activeSubTab, setActiveSubTab] = useState('pressure_cyclone'); // 'pressure_cyclone' or 'historical_trends'
  const [climateData, setClimateData] = useState(null);
  const [cycloneData, setCycloneData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDecade, setSelectedDecade] = useState('ALL');
  const [selectedSystemIdx, setSelectedSystemIdx] = useState(0);

  useEffect(() => {
    Promise.allSettled([
      api.getClimateTrends(),
      api.getCycloneSystems()
    ]).then(([trendsRes, cycloneRes]) => {
      if (trendsRes.status === 'fulfilled') setClimateData(trendsRes.value);
      if (cycloneRes.status === 'fulfilled') setCycloneData(cycloneRes.value);
    }).catch(err => console.error('Climate data load error:', err))
      .finally(() => setIsLoading(false));
  }, []);

  const rawTrends = climateData?.cyclone_trends || [];
  const filteredTrends = selectedDecade === 'ALL' 
    ? rawTrends 
    : rawTrends.filter(r => r.year >= parseInt(selectedDecade) && r.year <= parseInt(selectedDecade) + 25);

  const baseline = climateData?.climatology_baseline || {};
  const activeSystem = cycloneData?.systems?.[selectedSystemIdx] || null;

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
              {t.title}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              {t.subtitle}
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
              {t.realTimeCyclones || 'Cyclone & Pressure Genesis'}
            </button>
            <button
              onClick={() => setActiveSubTab('historical_trends')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeSubTab === 'historical_trends'
                  ? 'bg-white text-sky-700 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {t.historicalTrends || '131-Year Historical Archives'}
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center text-slate-500 flex flex-col items-center justify-center shadow-sm">
          <Loader2 className="h-8 w-8 animate-spin text-sky-600 mb-3" />
          <p className="text-sm font-bold text-slate-900">
            {language === 'hi' ? 'वायुमंडलीय दबाव क्षेत्र व चक्रवात पथ की गणना की जा रही है...' : 'Computing synoptic barometric pressure fields & tracks...'}
          </p>
        </div>
      ) : activeSubTab === 'pressure_cyclone' ? (
        /* TAB 1: GENUINE PRESSURE GRADIENT & CYCLONE GENESIS */
        <div className="space-y-6">
          {/* Active Synoptic Systems Selector Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex-shrink-0">
              {language === 'hi' ? 'सक्रिय समुद्री अवदाब / चक्रवात:' : 'Active Marine Depressions:'}
            </span>
            {cycloneData?.systems?.map((sys, idx) => (
              <button
                key={sys.id}
                onClick={() => setSelectedSystemIdx(idx)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer border ${
                  selectedSystemIdx === idx
                    ? 'bg-rose-600 text-white border-rose-600 shadow-xs'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {sys.name} ({sys.category})
              </button>
            ))}
          </div>

          {/* Active System Detailed Overview */}
          {activeSystem && (
            <div className="bg-gradient-to-r from-rose-50 via-white to-amber-50 border border-rose-200 rounded-3xl p-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-rose-100">
                <div>
                  <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200">
                    {activeSystem.category}
                  </span>
                  <h2 className="text-2xl font-black text-slate-900 mt-1">
                    {activeSystem.name}
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {activeSystem.basin} • {language === 'hi' ? 'वर्तमान केंद्र:' : 'Current Center:'} {activeSystem.current_lat}°N, {activeSystem.current_lon}°E
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="bg-white px-3.5 py-2 rounded-2xl border border-rose-200 text-center shadow-xs">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">{language === 'hi' ? 'केंद्रीय दबाव' : 'Central Pressure'}</span>
                    <span className="text-xl font-black text-rose-700">{activeSystem.central_pressure_hpa} <span className="text-xs text-slate-500">hPa</span></span>
                  </div>
                  <div className="bg-white px-3.5 py-2 rounded-2xl border border-rose-200 text-center shadow-xs">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">{language === 'hi' ? 'अधिकतम हवा' : 'Peak Wind'}</span>
                    <span className="text-xl font-black text-sky-700">{activeSystem.max_sustained_wind_kmh} <span className="text-xs text-slate-500">km/h</span></span>
                  </div>
                </div>
              </div>

              {/* Landfall & Forecast Warning */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs mb-4">
                <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                  <span className="text-slate-500 font-medium block">{language === 'hi' ? 'अनुमानित लैंडफॉल:' : 'Projected Landfall:'}</span>
                  <strong className="text-slate-900 font-bold">{activeSystem.projected_landfall}</strong>
                </div>
                <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                  <span className="text-slate-500 font-medium block">{language === 'hi' ? 'गति व दिशा:' : 'Movement Speed & Direction:'}</span>
                  <strong className="text-slate-900 font-bold">{activeSystem.movement_direction} at {activeSystem.speed_kmh} km/h</strong>
                </div>
                <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                  <span className="text-slate-500 font-medium block">{language === 'hi' ? 'तूफानी ज्वार (Surge):' : 'Storm Surge Potential:'}</span>
                  <strong className="text-rose-700 font-bold">{activeSystem.storm_surge_meters} meters</strong>
                </div>
              </div>

              {/* Multi-Day Track Table */}
              <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto shadow-xs p-4">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  {language === 'hi' ? 'संभावित चक्रवात पथ व तीव्रता प्रक्षेपण (48h Track Forecast):' : 'Projected Track & Intensity Trajectory:'}
                </h4>
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-100 text-slate-400 uppercase font-semibold text-[10px]">
                      <th className="pb-2">{language === 'hi' ? 'समय' : 'Timestamp'}</th>
                      <th className="pb-2">{language === 'hi' ? 'अक्षांश/देशांतर' : 'Position'}</th>
                      <th className="pb-2">{language === 'hi' ? 'दबाव (hPa)' : 'Pressure (hPa)'}</th>
                      <th className="pb-2">{language === 'hi' ? 'हवा (km/h)' : 'Wind (km/h)'}</th>
                      <th className="pb-2">{language === 'hi' ? 'श्रेणी' : 'Category'}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {activeSystem.track_forecast?.map((step, sIdx) => (
                      <tr key={sIdx} className="hover:bg-slate-50">
                        <td className="py-2 font-bold text-slate-800">{step.time}</td>
                        <td className="py-2 text-slate-600">{step.lat}°N, {step.lon}°E</td>
                        <td className="py-2 font-bold text-rose-700">{step.pressure}</td>
                        <td className="py-2 text-sky-700 font-semibold">{step.wind}</td>
                        <td className="py-2 text-slate-700 font-medium">{step.stage}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Genuine Meteorological Physics Explanation */}
          <div className="bg-gradient-to-r from-sky-50 via-white to-indigo-50 border border-sky-100 rounded-2xl p-5 text-xs text-slate-700 shadow-sm leading-relaxed">
            <h4 className="font-extrabold text-slate-900 mb-1 flex items-center gap-1.5 text-sm">
              <Compass className="h-4 w-4 text-sky-600" />
              {language === 'hi' ? 'वायुमंडलीय दबाव से चक्रवात कैसे उत्पन्न होते हैं:' : 'How High vs Low Pressure Systems Create Cyclones:'}
            </h4>
            <p className="mt-1 text-slate-600">
              {cycloneData?.physics_explanation}
            </p>
            <div className="mt-3 pt-3 border-t border-slate-200/80 flex flex-wrap items-center justify-between text-[11px] text-slate-500 font-mono">
              <span>Atkinson-Holliday: Vmax = 6.7 × (ΔP)^0.644 knots</span>
              <span>Central Deficit: ΔP = {activeSystem?.central_pressure_hpa ? (1012 - activeSystem.central_pressure_hpa).toFixed(1) : 30.0} hPa</span>
            </div>
          </div>
        </div>
      ) : (
        /* TAB 2: HISTORICAL 131-YEAR DISASTER ARCHIVES (1891-2021) */
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-extrabold text-slate-900">
              {t.title}
            </h2>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500 font-semibold">{t.filterPeriod}</span>
              <select
                value={selectedDecade}
                onChange={(e) => setSelectedDecade(e.target.value)}
                className="bg-slate-50 border border-slate-200 text-xs text-slate-800 font-bold rounded-xl px-3 py-1.5 focus:outline-none cursor-pointer shadow-xs"
              >
                <option value="ALL">{t.allSpan}</option>
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
              <span className="text-[11px] text-slate-500 font-bold uppercase">{t.totalCyclones}</span>
              <div className="text-2xl font-black text-sky-700 mt-1">676</div>
              <p className="text-[10px] text-slate-500">1891–2021 Record</p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-[11px] text-slate-500 font-bold uppercase">{t.severeCyclones}</span>
              <div className="text-2xl font-black text-rose-700 mt-1">325</div>
              <p className="text-[10px] text-slate-500">48.1% of all storms</p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-[11px] text-slate-500 font-bold uppercase">{t.bobShare}</span>
              <div className="text-2xl font-black text-indigo-700 mt-1">77.8%</div>
              <p className="text-[10px] text-slate-500">526 Cyclones in BOB</p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-[11px] text-slate-500 font-bold uppercase">{t.asShare}</span>
              <div className="text-2xl font-black text-amber-700 mt-1">20.1%</div>
              <p className="text-[10px] text-slate-500">136 Cyclones in AS</p>
            </div>
          </div>

          {/* Chart 1: Bay of Bengal vs Arabian Sea Cyclone Trajectory */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Waves className="h-4 w-4 text-sky-600" />
                <h3 className="text-sm font-extrabold text-slate-900">{t.basinCompTitle}</h3>
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
              <h3 className="text-sm font-extrabold text-slate-900">{t.climatologyTitle}</h3>
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
