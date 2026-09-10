import React from 'react';
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
import { Calendar, CloudRain, Wind, Thermometer, ShieldAlert, Droplets, Clock, Umbrella, Sparkles, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';
import { getTranslation } from '../translations';

export default function ForecastPage({ forecast, location = 'Nagpur', language = 'en' }) {
  const t = getTranslation(language);
  const tf = t.forecast;
  const tc = t.common;
  const days = forecast?.forecast_days || [];

  // Format data for Recharts
  const chartData = days.map(d => {
    const dateObj = new Date(d.date);
    const dayLabel = dateObj.toLocaleDateString(tc?.locale || 'en-IN', { weekday: 'short', day: 'numeric' });
    const p = d.precipitation_sum || 0;
    const prob = (d.precipitation_probability_max !== undefined && d.precipitation_probability_max !== null) 
      ? d.precipitation_probability_max 
      : (p === 0 ? 3 : Math.min(95, Math.round(35 + Math.sqrt(p) * 20)));
    const hrs = d.precipitation_hours !== undefined ? d.precipitation_hours : (p > 0 ? Math.round(p * 0.4 * 10) / 10 : 0);
    
    return {
      name: dayLabel,
      date: d.date,
      maxTemp: d.temperature_max,
      minTemp: d.temperature_min,
      precip: p,
      rainSum: d.rain_sum || p,
      precipProb: Math.round(prob),
      precipHours: hrs,
      precipCategory: d.precipitation_category || (p > 0 ? (language === 'en' ? 'Light/Moderate Rain' : 'हल्की/मध्यम बारिश') : (language === 'en' ? 'No Rain (Dry)' : 'शुष्क मौसम')),
      windGust: d.wind_gust_max,
      riskScore: d.risk_score,
      riskLevel: d.risk_level,
      description: d.weather_description,
      keyFactors: d.key_factors || [],
      recommendation: d.recommendation || ''
    };
  });

  const totalAccumulatedRain = chartData.reduce((acc, d) => acc + d.precip, 0).toFixed(1);
  const rainyDaysCount = chartData.filter(d => d.precip > 0.5).length;
  const maxRainDay = chartData.reduce((max, d) => d.precip > (max?.precip || 0) ? d : max, chartData[0] || { precip: 0, name: 'None' });

  // 24h and 72h accumulated rain prediction
  const rain24h = chartData[0]?.precip || 0.0;
  const rain72h = chartData.slice(0, 3).reduce((acc, d) => acc + d.precip, 0);
  const todayForecast = chartData[0] || {};
  const todayRainProb = todayForecast.precipProb ?? 10;
  const todayRainHours = todayForecast.precipHours ?? 0;
  const todayPrecipCategory = todayForecast.precipCategory || (rain24h > 0 ? (language === 'en' ? 'Light Rain' : 'हल्की बारिश') : (language === 'en' ? 'No Rain (Dry)' : 'शुष्क मौसम'));

  if (!forecast && days.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] bg-white border border-slate-200 rounded-3xl p-12 text-center">
        <Loader2 className="h-10 w-10 text-sky-600 animate-spin mb-4" />
        <h3 className="text-lg font-bold text-slate-800">{tf.loadingTitle}</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-md">
          {tf.loadingDesc} ({location})
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Page Title Header */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold text-sky-700 mb-1 uppercase tracking-wider">
              <Calendar className="h-3.5 w-3.5" />
              <span>{tf.subtitle}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              {tf.title}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              {tf.station} <strong className="text-slate-800">{location}</strong> • {tf.modelInfo}
            </p>
          </div>

          <div className="px-3.5 py-1.5 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-700 font-semibold self-start sm:self-auto shadow-sm">
            {tf.source} {forecast?.data_source || 'LIVE (Open-Meteo API)'}
          </div>
        </div>
      </div>

      {/* Dedicated Precipitation Prediction Intelligence Dashboard */}
      <div className="bg-gradient-to-r from-sky-50 via-white to-blue-50 border border-sky-200 rounded-3xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-5">
          <div className="flex items-center space-x-2.5">
            <div className="h-9 w-9 rounded-xl bg-sky-600 text-white flex items-center justify-center shadow-md shadow-sky-600/20">
              <Umbrella className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-black text-slate-900">
                  {tf.precipModel}
                </h2>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 border border-sky-200 uppercase tracking-wider inline-flex items-center gap-1">
                  <Sparkles className="h-2.5 w-2.5" /> {tf.aiCalibrated}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {tf.precipModelDesc}
              </p>
            </div>
          </div>

          <span className="text-xs font-bold bg-sky-100 text-sky-800 border border-sky-200 px-3 py-1 rounded-xl self-start sm:self-auto">
            {rainyDaysCount > 0 ? tf.rainEvents.replace('{count}', rainyDaysCount) : tf.dryHorizon}
          </span>
        </div>

        {/* 4 Summary Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 mb-5">
          <div className="bg-white/90 border border-slate-200 rounded-2xl p-4 shadow-xs">
            <span className="text-[11px] font-bold text-slate-500 uppercase block">{tf.totalAccumulation}</span>
            <div className="text-2xl sm:text-3xl font-black text-sky-700 mt-1">
              {totalAccumulatedRain} <span className="text-sm font-normal text-slate-400">mm</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">{tf.totalAccumulationDesc}</p>
          </div>

          <div className="bg-white/90 border border-slate-200 rounded-2xl p-4 shadow-xs">
            <span className="text-[11px] font-bold text-slate-500 uppercase block">{tf.peakRainDay}</span>
            <div className="text-xl sm:text-2xl font-black text-indigo-700 mt-1 truncate">
              {maxRainDay?.name || 'N/A'}
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">
              {maxRainDay?.precip ? `${maxRainDay.precip.toFixed(1)} mm (${maxRainDay.precipProb}%)` : tf.dryHorizon}
            </p>
          </div>

          <div className="bg-white/90 border border-slate-200 rounded-2xl p-4 shadow-xs">
            <span className="text-[11px] font-bold text-slate-500 uppercase block">{tf.highProbDays}</span>
            <div className="text-2xl sm:text-3xl font-black text-teal-700 mt-1">
              {chartData.filter(d => d.precipProb >= 40).length}
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">{tf.highProbDaysDesc}</p>
          </div>

          <div className="bg-white/90 border border-slate-200 rounded-2xl p-4 shadow-xs">
            <span className="text-[11px] font-bold text-slate-500 uppercase block">{tf.forecast24h}</span>
            <div className="text-2xl sm:text-3xl font-black text-slate-800 mt-1 truncate">
              {rain24h.toFixed(1)} <span className="text-sm font-normal text-slate-400">mm</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">{tf.forecast24hDesc}</p>
          </div>
        </div>

        {/* AI Model Precipitation Prediction Card */}
        <div className="bg-white border border-sky-200 rounded-2xl p-4 shadow-xs mb-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-sky-800">{tf.modelAssessment}:</span>
              <span className={`text-xs font-black px-2.5 py-0.5 rounded-full border ${
                rain24h >= 30.0 ? 'bg-rose-100 text-rose-800 border-rose-200' :
                rain24h >= 7.6 ? 'bg-orange-100 text-orange-800 border-orange-200' :
                rain24h > 0 ? 'bg-sky-100 text-sky-800 border-sky-200' :
                'bg-emerald-100 text-emerald-800 border-emerald-200'
              }`}>
                {todayPrecipCategory}
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {tf.rain24hPred}: <strong className="text-slate-900">{rain24h.toFixed(1)} mm</strong> ({todayRainProb}% {tf.rainProb}, ~{todayRainHours} hrs) • {tf.rain72hCum}: <strong className="text-indigo-700">{rain72h.toFixed(1)} mm</strong>
            </p>
            {todayForecast.recommendation && (
              <p className="text-[11px] text-slate-500 italic mt-0.5">
                {tf.directive}: {todayForecast.recommendation}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 px-3 py-2 rounded-xl self-stretch md:self-auto justify-between md:justify-start">
            <span>24h / 72h:</span>
            <span className="text-sky-700 font-extrabold">{rain24h.toFixed(1)} mm / {rain72h.toFixed(1)} mm</span>
          </div>
        </div>

        {/* Precipitation Bar & Probability Chart */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-extrabold text-slate-800 flex items-center gap-1.5">
              <CloudRain className="h-4 w-4 text-sky-600" />
              {tf.precipChartTitle}
            </span>
            <div className="flex items-center gap-3 text-[11px] font-semibold">
              <span className="flex items-center gap-1 text-sky-700">
                <span className="h-2.5 w-2.5 rounded-sm bg-sky-600 inline-block"></span> {tf.rainfallMm}
              </span>
              <span className="flex items-center gap-1 text-teal-700">
                <span className="h-2.5 w-2.5 rounded-sm bg-teal-400 inline-block"></span> {tf.rainProb}
              </span>
            </div>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '0.75rem', fontSize: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                  labelStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                />
                <Bar dataKey="precip" fill="#0284c7" radius={[6, 6, 0, 0]} name={tf.rainfallMm} />
                <Bar dataKey="precipProb" fill="#2dd4bf" radius={[6, 6, 0, 0]} name={tf.rainProb} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Temperature Envelope (Min - Max) */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Thermometer className="h-4 w-4 text-rose-500" />
            <h3 className="text-sm font-extrabold text-slate-900">{tf.tempChartTitle}</h3>
          </div>
          <div className="flex items-center space-x-4 text-xs font-semibold">
            <span className="flex items-center gap-1.5 text-slate-600">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-500 inline-block"></span> {tf.maxTemp}
            </span>
            <span className="flex items-center gap-1.5 text-slate-600">
              <span className="h-2.5 w-2.5 rounded-full bg-sky-500 inline-block"></span> {tf.minTemp}
            </span>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="tempMaxGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0}/>
                </linearGradient>
                <linearGradient id="tempMinGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0284c7" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={['auto', 'auto']} unit="°" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '0.75rem', fontSize: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                labelStyle={{ color: '#0f172a', fontWeight: 'bold' }}
              />
              <Area type="monotone" dataKey="maxTemp" stroke="#e11d48" strokeWidth={2.5} fillOpacity={1} fill="url(#tempMaxGrad)" name={`${tf.maxTemp} (°C)`} />
              <Area type="monotone" dataKey="minTemp" stroke="#0284c7" strokeWidth={2} fillOpacity={1} fill="url(#tempMinGrad)" name={`${tf.minTemp} (°C)`} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Comprehensive 7-Day Day-by-Day Table with Precipitation Details */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm overflow-x-auto">
        <div className="flex items-center space-x-2 mb-4">
          <ShieldAlert className="h-4 w-4 text-amber-500" />
          <h3 className="text-sm font-extrabold text-slate-900">{tf.detailedDayTitle}</h3>
        </div>

        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-wider font-bold">
              <th className="pb-3 pl-2">{tf.date}</th>
              <th className="pb-3">{tf.rainPrecip}</th>
              <th className="pb-3">{tf.temp}</th>
              <th className="pb-3">{tf.rainfallMm}</th>
              <th className="pb-3">{tf.rainProb}</th>
              <th className="pb-3">{tf.intensityLevel}</th>
              <th className="pb-3">{tf.windGusts}</th>
              <th className="pb-3 pr-2">{tf.risk}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {chartData.map((d, i) => (
              <tr key={i} className="hover:bg-slate-50 transition-colors">
                <td className="py-3.5 pl-2 font-bold text-slate-900">{d.name} <span className="text-[10px] text-slate-500 font-normal">({d.date})</span></td>
                <td className="py-3.5 text-slate-700 font-medium">{d.description}</td>
                <td className="py-3.5 font-bold text-slate-900">{Math.round(d.maxTemp)}°C / <span className="text-slate-500 font-normal">{Math.round(d.minTemp)}°C</span></td>
                <td className="py-3.5 font-black text-sky-700">
                  {d.precip > 0 ? `${d.precip.toFixed(1)} mm` : '0.0 mm'}
                </td>
                <td className="py-3.5">
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-lg inline-flex items-center gap-1 ${
                    d.precipProb >= 70 ? 'bg-sky-100 text-sky-800 font-extrabold' :
                    d.precipProb >= 30 ? 'bg-slate-100 text-slate-700' :
                    'bg-slate-50 text-slate-400'
                  }`}>
                    <Droplets className="h-3 w-3 text-sky-600" />
                    {d.precipProb}%
                  </span>
                </td>
                <td className="py-3.5 text-slate-600 font-medium">{d.precipCategory}</td>
                <td className="py-3.5 text-indigo-700 font-semibold">{Math.round(d.windGust)} km/h</td>
                <td className="py-3.5 pr-2">
                  <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase border ${
                    d.riskLevel?.toUpperCase() === 'SEVERE' ? 'bg-rose-100 text-rose-800 border-rose-200' :
                    d.riskLevel?.toUpperCase() === 'HIGH' ? 'bg-orange-100 text-orange-800 border-orange-200' :
                    d.riskLevel?.toUpperCase() === 'MODERATE' ? 'bg-amber-100 text-amber-800 border-amber-200' :
                    'bg-emerald-100 text-emerald-800 border-emerald-200'
                  }`}>
                    {tc?.riskLevels?.[d.riskLevel?.toUpperCase()] || d.riskLevel}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
