import React, { useState, useEffect } from 'react';
import { 
  Sprout, 
  Droplets, 
  SunMedium, 
  CheckCircle2, 
  Calendar, 
  MapPin, 
  Sparkles, 
  Loader2,
  Database,
  ArrowRight
} from 'lucide-react';
import api from '../api';
import { getTranslation } from '../translations';

export default function FarmerPage({ defaultLocation = 'Lucknow', language = 'en' }) {
  const t = getTranslation(language).farmer;
  const tc = getTranslation(language).common;
  const isHi = language === 'hi';

  // Current Agricultural Season Determination
  const currentMonth = new Date().getMonth() + 1; // 1-12
  const isKharif = currentMonth >= 6 && currentMonth <= 10;
  const isRabi = currentMonth >= 11 || currentMonth <= 3;
  const currentSeasonCode = isKharif ? 'KHARIF' : (isRabi ? 'RABI' : 'ZAID');
  const currentSeasonLabel = tc?.seasons?.[currentSeasonCode] || (isKharif 
    ? (isHi ? 'खरीफ (मानसून ऋतु - सक्रिय)' : 'Kharif (Monsoon Season - Active)') 
    : (isRabi 
        ? (isHi ? 'रबी (शीतकालीन ऋतु - सक्रिय)' : 'Rabi (Winter Season - Active)') 
        : (isHi ? 'जायद (ग्रीष्म ऋतु - सक्रिय)' : 'Zaid (Summer Season - Active)')));

  // Default to an in-season crop so farmers see favorable crops immediately
  const defaultCrop = isKharif ? 'Rice' : 'Wheat';

  const [location, setLocation] = useState(defaultLocation);
  const [crop, setCrop] = useState(defaultCrop);
  const [cropStage, setCropStage] = useState('Sowing');
  const [advisory, setAdvisory] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Sync with navbar location changes
  useEffect(() => {
    if (defaultLocation) {
      setLocation(defaultLocation);
    }
  }, [defaultLocation]);

  const availableCrops = [
    { id: 'Rice', label: tc?.crops?.Rice || 'Rice / Paddy (धान)', season: 'Kharif', seasonCodes: ['KHARIF', 'ZAID'] },
    { id: 'Maize', label: tc?.crops?.Maize || 'Maize (मक्का)', season: 'Kharif / Rabi', seasonCodes: ['KHARIF', 'RABI', 'ZAID'] },
    { id: 'Cotton', label: tc?.crops?.Cotton || 'Cotton (कपास)', season: 'Kharif', seasonCodes: ['KHARIF'] },
    { id: 'Sugarcane', label: tc?.crops?.Sugarcane || 'Sugarcane (गन्ना)', season: 'Perennial', seasonCodes: ['KHARIF', 'RABI', 'ZAID', 'PERENNIAL'] },
    { id: 'Pulses', label: tc?.crops?.Pulses || 'Pulses / Gram (दलहन)', season: 'Kharif / Rabi', seasonCodes: ['KHARIF', 'RABI', 'ZAID'] },
    { id: 'Wheat', label: tc?.crops?.Wheat || 'Wheat (गेहूं)', season: 'Rabi', seasonCodes: ['RABI'] },
    { id: 'Mustard', label: tc?.crops?.Mustard || 'Mustard (सरसों)', season: 'Rabi', seasonCodes: ['RABI'] },
    { id: 'Potato', label: tc?.crops?.Potato || 'Potato (आलू)', season: 'Rabi', seasonCodes: ['RABI'] }
  ];

  const inSeasonCrops = availableCrops.filter(c => c.seasonCodes.includes(currentSeasonCode) || c.seasonCodes.includes('PERENNIAL'));
  const offSeasonCrops = availableCrops.filter(c => !c.seasonCodes.includes(currentSeasonCode) && !c.seasonCodes.includes('PERENNIAL'));

  const cropStages = [
    'Sowing',
    'Vegetative',
    'Flowering',
    'Maturity',
    'Harvesting'
  ];

  const getStageDisplay = (s) => {
    return tc?.stages?.[s] || `${s} Phase`;
  };

  const getCropDisplay = (cropId) => {
    return tc?.crops?.[cropId] || cropId;
  };

  const fetchAdvisory = async () => {
    const cleanLoc = location.replace(/\(([^)]+)\)\s*\(\1\)/g, '($1)').trim();
    if (!cleanLoc) return;
    setIsLoading(true);
    try {
      const res = await api.getFarmerAdvisory({
        location: cleanLoc,
        crop: crop,
        crop_stage: cropStage,
        language: language
      });
      setAdvisory(res);
    } catch (e) {
      console.error('Farmer advisory error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAdvisory();
  }, [crop, cropStage, defaultLocation, language]);

  const getStatusTheme = (status) => {
    switch (status?.toUpperCase()) {
      case 'OPTIMAL':
        return {
          color: 'text-emerald-700',
          bg: 'bg-emerald-50',
          badge: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          border: 'border-emerald-200'
        };
      case 'MODERATE':
        return {
          color: 'text-amber-700',
          bg: 'bg-amber-50',
          badge: 'bg-amber-100 text-amber-800 border-amber-300',
          border: 'border-amber-200'
        };
      case 'OFF_SEASON':
      case 'RISK':
        return {
          color: 'text-rose-700',
          bg: 'bg-rose-50',
          badge: 'bg-rose-100 text-rose-800 border-rose-300',
          border: 'border-rose-200'
        };
      default:
        return {
          color: 'text-sky-700',
          bg: 'bg-sky-50',
          badge: 'bg-sky-100 text-sky-800 border-sky-300',
          border: 'border-sky-200'
        };
    }
  };

  const theme = getStatusTheme(advisory?.suitability_status);

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-50 via-white to-teal-50 border border-emerald-100 rounded-3xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold text-emerald-700 mb-1 uppercase tracking-wider">
              <Sprout className="h-3.5 w-3.5" />
              <span>{t.badge}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              {t.title}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              {t.subtitle}
            </p>
            {/* Active Season Pill */}
            <div className="flex flex-wrap items-center gap-2 mt-3 pt-2.5 border-t border-emerald-100/60">
              <span className="px-3 py-1 rounded-full bg-emerald-100/90 border border-emerald-300 text-emerald-800 text-[11px] font-extrabold flex items-center gap-1.5 shadow-xs">
                <span>🌾 {isHi ? 'सक्रिय कृषि ऋतु:' : 'Active Agro-Season:'}</span>
                <span className="text-emerald-950">{currentSeasonLabel}</span>
              </span>
              <span className="text-[11px] text-slate-500 font-medium">
                {isHi 
                  ? '• एक मौसम में केवल उसी ऋतु के अनुकूल फसल ही उगती है' 
                  : '• Single-Season Rule: In one season, only season-appropriate crops will grow'}
              </span>
            </div>
          </div>

          <div className="px-3.5 py-1.5 rounded-xl bg-emerald-100 border border-emerald-200 text-emerald-800 text-xs font-bold self-start sm:self-auto flex items-center gap-1.5 shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
            <span>{t.kisanModel}</span>
          </div>
        </div>

        {/* Input Selectors (Crop, Stage, Location) */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-slate-200/80">
          {/* Location input */}
          <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
            <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
              {t.locationLabel}
            </label>
            <div className="flex items-center space-x-2 text-xs text-slate-900">
              <MapPin className="h-4 w-4 text-sky-600 flex-shrink-0" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchAdvisory()}
                placeholder="Enter district"
                className="bg-transparent text-xs text-slate-900 font-bold focus:outline-none w-full"
              />
            </div>
          </div>

          {/* Crop Selector with In-Season vs Off-Season Grouping */}
          <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-1">
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                {t.cropLabel}
              </label>
              <span className={`text-[10px] font-extrabold px-1.5 py-0.2 rounded ${inSeasonCrops.some(c => c.id === crop) ? 'text-emerald-700 bg-emerald-50' : 'text-amber-700 bg-amber-50'}`}>
                {inSeasonCrops.some(c => c.id === crop) ? (tc?.inSeason || 'In-Season') : (tc?.offSeason || 'Off-Season')}
              </span>
            </div>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="bg-transparent text-xs text-slate-900 font-bold focus:outline-none w-full cursor-pointer"
            >
              <optgroup label={`✅ ${tc?.inSeason || 'In-Season'} (${currentSeasonCode})`}>
                {inSeasonCrops.map((c) => (
                  <option key={c.id} value={c.id} className="bg-white text-slate-900 font-semibold">
                    {c.label} • {c.season}
                  </option>
                ))}
              </optgroup>
              <optgroup label={`⏳ ${tc?.offSeason || 'Off-Season'}`}>
                {offSeasonCrops.map((c) => (
                  <option key={c.id} value={c.id} className="bg-slate-50 text-slate-600">
                    {c.label} • {c.season} ({tc?.offSeason || 'Off-Season'})
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          {/* Crop Stage */}
          <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
            <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
              {t.stageLabel}
            </label>
            <select
              value={cropStage}
              onChange={(e) => setCropStage(e.target.value)}
              className="bg-transparent text-xs text-slate-900 font-bold focus:outline-none w-full cursor-pointer"
            >
              {cropStages.map((s) => (
                <option key={s} value={s} className="bg-white text-slate-900">
                  {getStageDisplay(s)}
                </option>
              ))}
            </select>
          </div>

          {/* Analyze Action Button */}
          <div className="flex items-end">
            <button
              onClick={fetchAdvisory}
              disabled={isLoading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs py-3 px-4 rounded-xl flex items-center justify-center gap-1.5 transition-all shadow-sm cursor-pointer"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <span>{t.analyzeBtn}</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Off-Season Selection Alert Banner */}
      {advisory?.is_in_season === false && (
        <div className="bg-gradient-to-r from-amber-50 via-amber-50/70 to-orange-50 border-2 border-amber-300 rounded-3xl p-5 shadow-sm animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="p-2.5 rounded-2xl bg-amber-200 text-amber-900 mt-0.5 flex-shrink-0 shadow-xs">
                <Calendar className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-200 text-amber-900 border border-amber-300">
                    {tc?.offSeason || 'Off-Season Selection'}
                  </span>
                  <span className="text-xs font-bold text-amber-900">
                    {getCropDisplay(advisory.crop)} ≠ {currentSeasonLabel}
                  </span>
                </div>
                <p className="text-xs text-amber-900 font-semibold mt-1 leading-relaxed">
                  {advisory.season_warning || (isHi 
                    ? `एक मौसम में केवल उसी ऋतु की फसल ही सफल होती है। ${getCropDisplay(advisory.crop)} को इस मौसम में बोने से नुकसान होगा।` 
                    : `In a single season, only crops matching the active season will grow. Sowing ${getCropDisplay(advisory.crop)} out of season leads to failure.`)}
                </p>
                <p className="text-[11px] text-amber-800 font-medium mt-1">
                  {isHi ? 'वर्तमान मौसम की अनुशंसित फसलें:' : 'Recommended Favorable Crops for this Season:'}{' '}
                  <strong className="text-emerald-800 font-bold">
                    {advisory.seasonal_crops_recommended?.map(c => getCropDisplay(c)).join(', ') || inSeasonCrops.map(c => c.label).join(', ')}
                  </strong>
                </p>
              </div>
            </div>
            <button
              onClick={() => setCrop(inSeasonCrops[0]?.id || 'Rice')}
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-extrabold transition-all shadow-sm flex-shrink-0 cursor-pointer self-start sm:self-center flex items-center gap-1.5"
            >
              <span>{isHi ? `अनुकूल फसल चुनें (${inSeasonCrops[0]?.label || 'धान'})` : `Switch to In-Season (${inSeasonCrops[0]?.label || 'Rice'})`}</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Advisory Output Cards */}
      {isLoading ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center text-slate-500 flex flex-col items-center justify-center shadow-sm">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600 mb-3" />
          <p className="text-sm font-bold text-slate-900">Synthesizing crop weather suitability & field directives...</p>
        </div>
      ) : advisory ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Suitability Dial Panel */}
          <div className="lg:col-span-4 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{t.weatherMatch}</span>
              <h3 className="text-sm font-extrabold text-slate-900 mt-1">
                {getCropDisplay(advisory.crop)?.toUpperCase()} {t.suitabilityTitle}
              </h3>

              <div className="my-5 flex items-baseline space-x-2">
                <span className={`text-5xl font-black ${theme.color}`}>
                  {Math.round(advisory.suitability_score || 75)}
                </span>
                <span className="text-xl font-bold text-slate-400">/ 100</span>
              </div>

              <div className="mb-4">
                <span className={`text-xs font-extrabold px-3 py-1 rounded-full uppercase border ${theme.badge}`}>
                  STATUS: {advisory.suitability_status}
                </span>
              </div>

              <div className="space-y-2 text-xs text-slate-700 mt-4 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                <p><strong>{t.primaryConcern}</strong> <span className="text-slate-900 font-semibold">{advisory.weather_concern}</span></p>
                <p><strong>{t.targetStage}</strong> <span className="text-slate-900 font-semibold">{getStageDisplay(advisory.crop_stage)}</span></p>
                <p><strong>{t.location}</strong> <span className="text-slate-900 font-semibold">{advisory.location}</span></p>
              </div>
            </div>

            {/* Why this recommendation */}
            <div className="mt-5 pt-4 border-t border-slate-200">
              <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                {t.contributingFactors}
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-700">
                {advisory.why_factors?.map((f, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <CheckCircle2 className={`h-3.5 w-3.5 ${theme.color} flex-shrink-0 mt-0.5`} />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Actionable Directives Panel (Right Column) */}
          <div className="lg:col-span-8 space-y-4">
            {/* Master Directive Box */}
            <div className={`p-6 rounded-2xl border ${theme.border} ${theme.bg} shadow-sm`}>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className={`h-4 w-4 ${theme.color}`} />
                <h3 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider">
                  {t.directiveTitle}
                </h3>
              </div>
              <p className="text-sm text-slate-800 leading-relaxed font-semibold">
                {advisory.recommendation}
              </p>
            </div>

            {/* Sub-directives Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Irrigation Advice */}
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <div className="flex items-center space-x-2 text-sky-700 text-xs font-bold uppercase tracking-wider mb-2">
                  <Droplets className="h-4 w-4 text-sky-600" />
                  <span>{t.irrigationTitle}</span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {advisory.irrigation_advice}
                </p>
              </div>

              {/* Thermal & Heat Stress Warning */}
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <div className="flex items-center space-x-2 text-amber-700 text-xs font-bold uppercase tracking-wider mb-2">
                  <SunMedium className="h-4 w-4 text-amber-600" />
                  <span>{t.thermalTitle}</span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {advisory.heat_or_rain_stress_warning}
                </p>
              </div>

              {/* Sowing / Harvest Operations */}
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm sm:col-span-2">
                <div className="flex items-center space-x-2 text-emerald-700 text-xs font-bold uppercase tracking-wider mb-2">
                  <Calendar className="h-4 w-4 text-emerald-600" />
                  <span>{t.fieldTitle}</span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {advisory.sowing_or_harvest_precaution}
                </p>
              </div>
            </div>

            {/* Source Citations & Disclaimer */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 text-[11px] text-slate-600 space-y-1.5 shadow-xs">
              <div className="flex items-center gap-1 font-bold text-slate-800">
                <Database className="h-3.5 w-3.5 text-sky-600" />
                <span>{t.knowledgeProvenance}</span>
              </div>
              <p>{advisory.data_sources?.join(' • ')}</p>
              <p className="text-[10px] text-slate-500 italic pt-1 border-t border-slate-100">
                “{advisory.disclaimer}”
              </p>
            </div>
          </div>
        </div>
      ) : null}

      {/* Seasonal Crop Calendar & Single-Season Agronomic Guide Card */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
              <span>🌾 {isHi ? 'भारतीय कृषि मौसमी चक्र (Single-Season Cropping Guide)' : 'Indian Agricultural Seasonal Cropping Guide (ICAR)'}</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {isHi 
                ? 'एक निश्चित मौसम में केवल उसी ऋतु के अनुकूल फसल ही उगती है। विपरीत मौसम में फसल लगाने से शत-प्रतिशत विफलता होती है।'
                : 'In Indian agro-meteorology, a single season sustains only one adapted crop type. You cannot grow Kharif and Rabi crops simultaneously.'}
            </p>
          </div>
          <span className="px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 text-[11px] font-bold self-start sm:self-auto">
            {isHi ? 'भाकृअनुप मानक' : 'ICAR / GKMS Standards'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          {/* Kharif Card */}
          <div className={`p-4 rounded-2xl border transition-all ${currentSeasonCode === 'KHARIF' ? 'bg-emerald-50/80 border-emerald-300 ring-2 ring-emerald-500/20 shadow-xs' : 'bg-slate-50/70 border-slate-200'}`}>
            <div className="flex items-center justify-between mb-1">
              <span className="font-extrabold text-slate-900 text-sm">🌧️ {tc?.seasons?.KHARIF || (isHi ? 'खरीफ (मानसून)' : 'Kharif (Monsoon)')}</span>
              {currentSeasonCode === 'KHARIF' && (
                <span className="text-[9px] bg-emerald-600 text-white px-2 py-0.5 rounded-full font-black uppercase tracking-wider">
                  {isHi ? 'सक्रिय ऋतु' : 'Active Now'}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 font-semibold">{isHi ? 'जून से अक्टूबर (दक्षिण-पश्चिम मानसून)' : 'June – October (Southwest Monsoon)'}</p>
            <div className="mt-3 space-y-1 text-slate-700">
              <p><strong>{isHi ? 'प्रमुख अनुकूल फसलें:' : 'Favorable Crops:'}</strong></p>
              <p className="text-emerald-800 font-bold bg-white/80 p-2 rounded-xl border border-emerald-200">
                Rice / Paddy (धान), Maize (मक्का), Cotton (कपास), Sugarcane (गन्ना), Kharif Pulses (अरहर)
              </p>
              <p className="text-[11px] text-rose-700 pt-1">
                ⛔ <strong>{tc?.offSeason || 'Off-Season:'}</strong> {isHi ? 'गेहूं, सरसों, आलू (अभी न बोएं)' : 'Wheat, Mustard, Potato (Do NOT sow now)'}
              </p>
            </div>
          </div>

          {/* Rabi Card */}
          <div className={`p-4 rounded-2xl border transition-all ${currentSeasonCode === 'RABI' ? 'bg-emerald-50/80 border-emerald-300 ring-2 ring-emerald-500/20 shadow-xs' : 'bg-slate-50/70 border-slate-200'}`}>
            <div className="flex items-center justify-between mb-1">
              <span className="font-extrabold text-slate-900 text-sm">❄️ {tc?.seasons?.RABI || (isHi ? 'रबी (शीतकाल)' : 'Rabi (Winter)')}</span>
              {currentSeasonCode === 'RABI' && (
                <span className="text-[9px] bg-emerald-600 text-white px-2 py-0.5 rounded-full font-black uppercase tracking-wider">
                  {isHi ? 'सक्रिय ऋतु' : 'Active Now'}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 font-semibold">{isHi ? 'नवंबर से अप्रैल (शीतकालीन ठंड)' : 'November – April (Winter Cool Window)'}</p>
            <div className="mt-3 space-y-1 text-slate-700">
              <p><strong>{isHi ? 'प्रमुख अनुकूल फसलें:' : 'Favorable Crops:'}</strong></p>
              <p className="text-slate-800 font-bold bg-white/80 p-2 rounded-xl border border-slate-200">
                Wheat (गेहूं), Mustard (सरसों), Potato (आलू), Gram / Chana (चना), Peas (मटर)
              </p>
              <p className="text-[11px] text-rose-700 pt-1">
                ⛔ <strong>{tc?.offSeason || 'Off-Season:'}</strong> {isHi ? 'धान (चावल), कपास' : 'Rice / Paddy, Cotton'}
              </p>
            </div>
          </div>

          {/* Zaid Card */}
          <div className={`p-4 rounded-2xl border transition-all ${currentSeasonCode === 'ZAID' ? 'bg-emerald-50/80 border-emerald-300 ring-2 ring-emerald-500/20 shadow-xs' : 'bg-slate-50/70 border-slate-200'}`}>
            <div className="flex items-center justify-between mb-1">
              <span className="font-extrabold text-slate-900 text-sm">☀️ {tc?.seasons?.ZAID || (isHi ? 'जायद (ग्रीष्म)' : 'Zaid (Summer)')}</span>
              {currentSeasonCode === 'ZAID' && (
                <span className="text-[9px] bg-emerald-600 text-white px-2 py-0.5 rounded-full font-black uppercase tracking-wider">
                  {isHi ? 'सक्रिय ऋतु' : 'Active Now'}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 font-semibold">{isHi ? 'अप्रैल से जून (गर्मी / शुष्क काल)' : 'April – June (Pre-Monsoon Summer)'}</p>
            <div className="mt-3 space-y-1 text-slate-700">
              <p><strong>{isHi ? 'प्रमुख अनुकूल फसलें:' : 'Favorable Crops:'}</strong></p>
              <p className="text-slate-800 font-bold bg-white/80 p-2 rounded-xl border border-slate-200">
                Moong (मूंग), Urad (उड़द), Watermelon (तरबूज), Cucumber (खीरा), Fodder Maize
              </p>
              <p className="text-[11px] text-rose-700 pt-1">
                ⛔ <strong>{tc?.offSeason || 'Off-Season:'}</strong> {isHi ? 'गेहूं (कटाई पूर्ण), मुख्य धान' : 'Wheat (Harvested), Main Rice'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
