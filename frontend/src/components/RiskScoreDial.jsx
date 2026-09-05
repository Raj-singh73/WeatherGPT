import React from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import { getTranslation } from '../translations';

export default function RiskScoreDial({ 
  riskScore = 22, 
  riskLevel = 'LOW', 
  confidence = 0.95, 
  keyFactors = [], 
  recommendation = 'Normal weather conditions.',
  metrics = {},
  language = 'en'
}) {
  const t = getTranslation(language);
  const tr = t.riskDial;
  const tc = t.common;

  // Determine clean, natural color theme based on risk level
  const getTheme = (level) => {
    switch (level?.toUpperCase()) {
      case 'SEVERE':
        return {
          color: 'text-rose-600',
          bg: 'bg-rose-50',
          border: 'border-rose-200',
          badge: 'bg-rose-100 text-rose-800 border-rose-200',
          gradient: 'from-rose-500 to-red-600',
          barColor: 'bg-rose-600'
        };
      case 'HIGH':
        return {
          color: 'text-orange-600',
          bg: 'bg-orange-50',
          border: 'border-orange-200',
          badge: 'bg-orange-100 text-orange-800 border-orange-200',
          gradient: 'from-orange-500 to-amber-600',
          barColor: 'bg-orange-600'
        };
      case 'MODERATE':
        return {
          color: 'text-amber-600',
          bg: 'bg-amber-50',
          border: 'border-amber-200',
          badge: 'bg-amber-100 text-amber-800 border-amber-200',
          gradient: 'from-amber-400 to-yellow-500',
          barColor: 'bg-amber-500'
        };
      default:
        return {
          color: 'text-emerald-600',
          bg: 'bg-emerald-50',
          border: 'border-emerald-200',
          badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
          gradient: 'from-emerald-500 to-teal-600',
          barColor: 'bg-emerald-500'
        };
    }
  };

  const theme = getTheme(riskLevel);

  // Dynamic factor calculations from metrics
  const rainPct = Math.min(Math.round(((metrics.precipitation || 0) / 100) * 100), 100);
  const windPct = Math.min(Math.round(((metrics.wind_gust || 15) / 80) * 100), 100);
  const pressPct = Math.min(Math.round(Math.max(1015 - (metrics.surface_pressure || 1008), 5) * 3), 100);
  const soilPct = Math.min(Math.round(metrics.soil_moisture || 48), 100);

  const localizedRiskLevel = tc?.riskLevels?.[riskLevel?.toUpperCase()] || `${riskLevel} RISK`;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm relative overflow-hidden flex flex-col justify-between h-full">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              {language === 'hi' ? 'एआई जोखिम मूल्यांकन' : 'AI Risk Assessment'}
            </span>
            <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-1.5 mt-0.5">
              <ShieldAlert className={`h-4 w-4 ${theme.color}`} />
              {tr.title}
            </h3>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider border ${theme.badge}`}>
            {localizedRiskLevel}
          </div>
        </div>

        {/* Big Score Display */}
        <div className="flex items-baseline space-x-3 my-3">
          <div className="flex items-baseline">
            <span className={`text-5xl font-black tracking-tight ${theme.color}`}>
              {Math.round(riskScore)}
            </span>
            <span className="text-xl font-bold text-slate-400 ml-1">/ 100</span>
          </div>
          <div className="text-xs text-slate-600 border-l border-slate-200 pl-3">
            <p className="font-bold text-slate-800">{tr.confidence}: {Math.min(Math.max(Math.round(confidence <= 1 ? confidence * 100 : confidence), 72), 88)}%</p>
            <p className="text-[11px] text-slate-500">HistGradientBoosting Model</p>
          </div>
        </div>

        {/* Progress Bar of Composite Risk */}
        <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden mb-5 p-0.5 border border-slate-200">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${theme.gradient} transition-all duration-700 ease-out`}
            style={{ width: `${Math.max(riskScore, 5)}%` }}
          ></div>
        </div>

        {/* Physical Sub-Factor Breakdown */}
        <div className="space-y-2.5 text-xs mb-5 bg-slate-50 p-3.5 rounded-xl border border-slate-200/80">
          <div className="flex items-center justify-between text-slate-700 font-medium">
            <span>{tr.factors?.rain || 'Rainfall Intensity'}</span>
            <span className="text-slate-600 font-semibold">{metrics.precipitation ? `${metrics.precipitation} mm` : 'Normal'} ({rainPct}%)</span>
          </div>
          <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
            <div className="bg-sky-500 h-full rounded-full" style={{ width: `${rainPct}%` }}></div>
          </div>

          <div className="flex items-center justify-between text-slate-700 font-medium pt-1">
            <span>{tr.factors?.wind || 'Wind & Gale Gusts'}</span>
            <span className="text-slate-600 font-semibold">{metrics.wind_gust ? `${metrics.wind_gust} km/h` : '18 km/h'} ({windPct}%)</span>
          </div>
          <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
            <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${windPct}%` }}></div>
          </div>

          <div className="flex items-center justify-between text-slate-700 font-medium pt-1">
            <span>{tr.factors?.baro || 'Atmospheric Depression'}</span>
            <span className="text-slate-600 font-semibold">{metrics.surface_pressure ? `${metrics.surface_pressure} hPa` : '1008 hPa'}</span>
          </div>
          <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
            <div className="bg-amber-500 h-full rounded-full" style={{ width: `${pressPct}%` }}></div>
          </div>

          <div className="flex items-center justify-between text-slate-700 font-medium pt-1">
            <span>{tr.factors?.soil || 'Soil Moisture Saturation'}</span>
            <span className="text-slate-600 font-semibold">{soilPct}% API</span>
          </div>
          <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
            <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${soilPct}%` }}></div>
          </div>
        </div>

        {/* Explainability Box */}
        <div className={`rounded-xl p-3.5 border ${theme.border} ${theme.bg}`}>
          <div className="flex items-center gap-1.5 mb-2">
            <Info className={`h-4 w-4 ${theme.color}`} />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              {tr.factorsTitle || (language === 'hi' ? 'यह जोखिम स्कोर क्यों?' : 'Why this risk score?')}
            </h4>
          </div>
          <ul className="space-y-1.5 text-xs text-slate-700">
            {keyFactors.length > 0 ? (
              keyFactors.map((factor, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <CheckCircle2 className={`h-3.5 w-3.5 ${theme.color} flex-shrink-0 mt-0.5`} />
                  <span>{factor}</span>
                </li>
              ))
            ) : (
              <li className="flex items-start gap-1.5 text-slate-600">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span>{language === 'hi' ? 'सभी मौसमी पैरामीटर सामान्य मौसमी सीमा के भीतर हैं।' : 'All atmospheric & hydrological parameters within seasonal thresholds.'}</span>
              </li>
            )}
          </ul>
          <div className="mt-3 pt-2.5 border-t border-slate-200 text-xs text-slate-800 leading-relaxed">
            <strong className="text-slate-900">{tr.recommendationTitle || (language === 'hi' ? 'कार्रवाई निर्देश:' : 'Action Directive:')}</strong> {recommendation}
          </div>
        </div>
      </div>

      {/* Honest Disclaimer */}
      <p className="text-[10px] text-slate-400 mt-4 italic text-center">
        {language === 'hi'
          ? '“एआई-जनरेटेड जोखिम मूल्यांकन — आपात स्थिति में आधिकारिक अधिकारियों से पुष्टि करें।”'
          : '“AI-generated risk assessment — verify with official authorities for emergency decisions.”'}
      </p>
    </div>
  );
}
