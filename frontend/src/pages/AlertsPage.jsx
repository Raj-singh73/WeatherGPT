import React, { useState } from 'react';
import { 
  ShieldAlert, 
  AlertTriangle, 
  Clock, 
  MapPin, 
  CheckCircle2, 
  Info, 
  AlertOctagon,
  Wind,
  CloudRain,
  Zap,
  Sun,
  Waves,
  PhoneCall,
  Flame,
  Check,
  LifeBuoy,
  Compass
} from 'lucide-react';
import { getTranslation } from '../translations';

export default function AlertsPage({ alerts = [], location = 'Nagpur', language = 'en' }) {
  const t = getTranslation(language).alerts;
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  // Filter alerts by category
  const filteredAlerts = alerts.filter(a => {
    if (selectedCategory === 'ALL') return true;
    if (selectedCategory === 'CYCLONE' && (a.alert_type === 'CYCLONE_ALERT' || a.alert_type === 'STORM_SURGE_INUNDATION')) return true;
    if (selectedCategory === 'RAIN' && (a.alert_type === 'HEAVY_RAIN' || a.alert_type === 'FLOOD_RISK')) return true;
    if (selectedCategory === 'LIGHTNING' && a.alert_type === 'THUNDERSTORM_LIGHTNING') return true;
    if (selectedCategory === 'HEAT' && a.alert_type === 'HEATWAVE') return true;
    return true;
  });

  // Color & badge styling according to IMD 4-Stage Severity Framework
  const getSeverityStyle = (severity, imdColor) => {
    const code = imdColor?.toUpperCase() || (
      severity?.toUpperCase() === 'SEVERE' ? 'RED' :
      severity?.toUpperCase() === 'WARNING' ? 'ORANGE' :
      severity?.toUpperCase() === 'WATCH' ? 'YELLOW' : 'GREEN'
    );

    switch (code) {
      case 'RED':
        return {
          card: 'bg-rose-50/90 border-rose-300 ring-1 ring-rose-200',
          badge: 'bg-rose-600 text-white border-rose-700 shadow-sm',
          icon: AlertOctagon,
          iconColor: 'text-rose-600',
          colorName: 'IMD RED WARNING (Take Immediate Action)',
          headerBg: 'bg-rose-100/80 text-rose-900 border-rose-200'
        };
      case 'ORANGE':
        return {
          card: 'bg-orange-50/90 border-orange-300 ring-1 ring-orange-200',
          badge: 'bg-orange-600 text-white border-orange-700 shadow-sm',
          icon: AlertTriangle,
          iconColor: 'text-orange-600',
          colorName: 'IMD ORANGE ALERT (Be Prepared)',
          headerBg: 'bg-orange-100/80 text-orange-900 border-orange-200'
        };
      case 'YELLOW':
        return {
          card: 'bg-amber-50/80 border-amber-300 ring-1 ring-amber-200',
          badge: 'bg-amber-500 text-white border-amber-600 shadow-sm',
          icon: Info,
          iconColor: 'text-amber-600',
          colorName: 'IMD YELLOW WATCH (Be Updated)',
          headerBg: 'bg-amber-100/80 text-amber-900 border-amber-200'
        };
      default:
        return {
          card: 'bg-emerald-50/80 border-emerald-300 ring-1 ring-emerald-200',
          badge: 'bg-emerald-600 text-white border-emerald-700 shadow-sm',
          icon: CheckCircle2,
          iconColor: 'text-emerald-600',
          colorName: 'IMD GREEN (No Emergency Warning)',
          headerBg: 'bg-emerald-100/80 text-emerald-900 border-emerald-200'
        };
    }
  };

  // Primary vulnerability basin detected
  const primaryBasin = alerts[0]?.vulnerability_zone || 'Inland Continental Plain / River Basin';
  const isCoastalBasin = primaryBasin.toLowerCase().includes('coastal') || primaryBasin.toLowerCase().includes('maritime');

  return (
    <div className="space-y-6 pb-12">
      
      {/* Top Header & Vulnerability Scope Banner */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-extrabold text-rose-600 mb-1.5 uppercase tracking-wider">
              <ShieldAlert className="h-4 w-4" />
              <span>Multi-Hazard Early Warning & Impact Engine</span>
            </div>
            
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              {t.title}
            </h1>
            
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span className="text-xs text-slate-600">
                Location Focus: <strong className="text-slate-900">{location}</strong>
              </span>
              <span className="text-slate-300">•</span>
              <span className={`text-[11px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                isCoastalBasin 
                  ? 'bg-sky-100 text-sky-800 border-sky-300' 
                  : 'bg-amber-100 text-amber-800 border-amber-300'
              }`}>
                {isCoastalBasin ? '🌊 Maritime Coastal Basin' : '🌾 Inland Continental Basin'}
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 self-start md:self-auto">
            <div className="px-3.5 py-2 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold flex items-center gap-2 shadow-xs">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-600 animate-ping"></span>
              <span>{alerts.length} Active Hazard Advisories</span>
            </div>
          </div>
        </div>

        {/* Basin Classification Context Banner */}
        <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-700">
          <div className="flex items-center gap-2.5">
            <Compass className="h-5 w-5 text-sky-600 flex-shrink-0" />
            <div>
              <strong className="block text-slate-900 font-bold">
                Geographical Basin: {primaryBasin}
              </strong>
              <p className="text-[11px] text-slate-500">
                {isCoastalBasin 
                  ? 'High vulnerability to Tropical Cyclones, High Wind Gales, Severe Sea Swells, and Tidal Surges.' 
                  : 'Vulnerability centered on Heavy Precipitation, Flash Inundation, Damini Lightning, and Temperature Extremes.'}
              </p>
            </div>
          </div>

          <span className="text-[10px] font-mono text-slate-500 bg-white px-2.5 py-1 rounded-lg border border-slate-200 self-start sm:self-auto flex-shrink-0">
            Protocols: NDMA & IMD
          </span>
        </div>

        {/* Hazard Category Filter Chips */}
        <div className="flex flex-wrap items-center gap-2 mt-4 pt-3 border-t border-slate-100">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mr-1">
            Filter Hazard:
          </span>
          {[
            { id: 'ALL', label: 'All Hazards' },
            { id: 'CYCLONE', label: '🌪️ Cyclones & Marine' },
            { id: 'RAIN', label: '🌧️ Heavy Rain & Floods' },
            { id: 'LIGHTNING', label: '⚡ Damini Lightning' },
            { id: 'HEAT', label: '☀️ Thermal Extremes' }
          ].map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer border ${
                selectedCategory === cat.id
                  ? 'bg-sky-600 text-white border-sky-600 shadow-sm scale-105'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Dynamic Alerts List */}
      <div className="space-y-6">
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map((alert) => {
            const style = getSeverityStyle(alert.severity, alert.imd_color_code);
            const Icon = style.icon;

            return (
              <div 
                key={alert.id}
                className={`rounded-3xl p-6 border shadow-sm transition-all overflow-hidden ${style.card}`}
              >
                {/* Alert Top Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-3 border-b border-slate-200/80 mb-3.5">
                  <div className="flex items-center space-x-2.5">
                    <div className={`p-2 rounded-xl bg-white shadow-xs border border-slate-200 ${style.iconColor}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="text-base sm:text-lg font-black text-slate-900 leading-snug">
                        {alert.title}
                      </h3>
                      <span className="text-[10px] font-mono text-slate-500">
                        Identifier: {alert.id} • {alert.hazard_category || 'METEOROLOGICAL'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs font-black px-3 py-1 rounded-full uppercase border shadow-xs ${style.badge}`}>
                      {alert.severity} ({alert.imd_color_code || 'WATCH'})
                    </span>
                    <span className="text-[10px] font-extrabold px-2.5 py-1 rounded-full bg-white text-slate-700 border border-slate-200">
                      {alert.is_demo ? 'SIMULATED EARLY WARNING' : 'OFFICIAL'}
                    </span>
                  </div>
                </div>

                {/* Scope & Timing Metadata */}
                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 mb-3.5 font-medium">
                  <span className="flex items-center gap-1.5 text-slate-900 font-bold bg-white px-2.5 py-1 rounded-lg border border-slate-200">
                    <MapPin className="h-3.5 w-3.5 text-sky-600" />
                    {alert.location}, {alert.state}
                  </span>
                  <span className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-slate-200">
                    <Clock className="h-3.5 w-3.5 text-slate-500" />
                    Valid Through: <strong className="text-slate-900">{alert.valid_until}</strong>
                  </span>
                  <span className="text-slate-500 text-[11px]">
                    Issued: {alert.issued_time}
                  </span>
                </div>

                {/* Key Atmospheric Thresholds Strip */}
                {alert.key_thresholds && alert.key_thresholds.length > 0 && (
                  <div className="mb-4 flex flex-wrap items-center gap-2">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Trigger Thresholds:</span>
                    {alert.key_thresholds.map((th, idx) => (
                      <span 
                        key={idx}
                        className="text-[11px] font-bold bg-white px-2.5 py-1 rounded-lg text-slate-800 border border-slate-200 shadow-xs"
                      >
                        {th}
                      </span>
                    ))}
                  </div>
                )}

                {/* Technical Atmospheric Summary */}
                <div className="bg-white/90 p-4 rounded-2xl border border-slate-200 mb-4 text-xs text-slate-800 leading-relaxed font-medium shadow-xs">
                  <strong className="block text-slate-900 font-extrabold text-[11px] uppercase tracking-wider mb-1 text-sky-900">
                    Synoptic Assessment & Meteorological Drivers:
                  </strong>
                  <p>{alert.summary}</p>
                </div>

                {/* 🚨 LIFE SURVIVAL PROTOCOLS */}
                {alert.life_survival_protocols && alert.life_survival_protocols.length > 0 && (
                  <div className="bg-rose-50/90 border border-rose-200 rounded-2xl p-4 mb-4 shadow-xs">
                    <h4 className="font-black text-rose-950 text-xs uppercase tracking-wider mb-2.5 flex items-center gap-2">
                      <LifeBuoy className="h-4 w-4 text-rose-600" />
                      <span>Life Survival Actionable Protocols (जीवन रक्षा दिशानिर्देश):</span>
                    </h4>
                    <ul className="space-y-2 text-xs text-rose-900">
                      {alert.life_survival_protocols.map((protocol, pIdx) => (
                        <li key={pIdx} className="flex items-start gap-2 bg-white/80 p-2.5 rounded-xl border border-rose-100">
                          <Check className="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                          <span className="font-semibold leading-relaxed">{protocol}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Sectoral Livelihood Instructions (Farmers, Commuters, Fishermen) */}
                <div className="bg-white rounded-2xl p-4 border border-slate-200 text-xs shadow-xs mb-4">
                  <h4 className="font-extrabold text-sky-900 uppercase tracking-wider text-[11px] mb-1.5 flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-sky-600" />
                    <span>Livelihood, Commuter & Agricultural Protection:</span>
                  </h4>
                  <p className="text-slate-700 leading-relaxed font-medium">
                    {alert.action_instructions}
                  </p>
                </div>

                {/* Emergency Hotlines Quick Dials */}
                {alert.emergency_contacts && Object.keys(alert.emergency_contacts).length > 0 && (
                  <div className="pt-3 border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-2">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                      <PhoneCall className="h-3.5 w-3.5 text-rose-600" />
                      Emergency Helplines:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(alert.emergency_contacts).map(([agency, number]) => (
                        <a
                          key={agency}
                          href={`tel:${number}`}
                          className="bg-white hover:bg-slate-50 text-slate-800 text-[11px] font-extrabold px-2.5 py-1 rounded-xl border border-slate-200 shadow-xs flex items-center gap-1 transition-all"
                        >
                          <span className="text-slate-500 font-normal">{agency}:</span>
                          <span className="text-rose-700 underline">{number}</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            );
          })
        ) : (
          <div className="bg-white border border-slate-200 rounded-3xl p-12 text-center text-slate-500 shadow-sm">
            <CheckCircle2 className="h-10 w-10 text-emerald-600 mx-auto mb-3" />
            <h3 className="text-base font-bold text-slate-900 mb-1">No Active Warnings in this Category</h3>
            <p className="text-xs">Conditions in {location} remain within seasonal safety thresholds.</p>
          </div>
        )}
      </div>

    </div>
  );
}
