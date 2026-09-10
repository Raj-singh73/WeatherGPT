import React from 'react';
import { ShieldCheck, ShieldAlert, WifiOff, MapPin, Navigation, Info } from 'lucide-react';

/**
 * CycloneStatusPanel
 *
 * Renders the three states the cyclone detector can genuinely be in:
 *
 *   1. Detection unavailable  - the live pressure field could not be fetched.
 *                               Says so plainly instead of showing stale or
 *                               invented cyclone data.
 *   2. No active system       - the scan ran and found nothing. This is the
 *                               normal state for most of the year and must be
 *                               stated positively, not left as an empty page.
 *   3. System(s) detected     - a per-location risk summary sits alongside the
 *                               radar map that ClimatePage already renders.
 *
 * Nothing here fabricates a value. Every figure comes from the API payload, and
 * anything absent is simply not shown.
 */
export default function CycloneStatusPanel({ scan, risk, locationName = '', language = 'en' }) {
  const hi = language === 'hi';
  if (!scan) return null;

  const systems = scan.systems || [];
  const scanInfo = scan.scan || {};

  // ---------------------------------------------------- 1. detection is down
  if (scan.available === false) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-3xl p-6 shadow-sm">
        <div className="flex items-start gap-3">
          <WifiOff className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-base font-black text-amber-900">
              {hi ? 'चक्रवात पहचान अभी उपलब्ध नहीं' : 'Cyclone detection unavailable'}
            </h3>
            <p className="text-sm text-amber-800 mt-1 max-w-2xl">
              {scan.message || (hi
                ? 'लाइव दबाव डेटा नहीं मिल सका, इसलिए कोई चक्रवात जानकारी नहीं दिखाई जा रही।'
                : 'The live pressure field could not be retrieved, so no cyclone information is being shown.')}
            </p>
            <p className="text-xs text-amber-700 mt-2">
              {hi
                ? 'अनुमान दिखाने के बजाय कुछ न दिखाना अधिक सुरक्षित है। कृपया बाद में पुनः प्रयास करें।'
                : 'Showing nothing is safer than showing a guess. Please try again shortly.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ------------------------------------------------- 2. scan ran, nothing found
  if (systems.length === 0) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded-3xl p-6 shadow-sm">
        <div className="flex items-start gap-3">
          <ShieldCheck className="h-6 w-6 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-lg font-black text-emerald-900">
              {hi ? 'कोई सक्रिय चक्रवात नहीं' : 'No active cyclone detected'}
            </h3>
            <p className="text-sm text-emerald-800 mt-1 max-w-2xl">
              {scan.message || (hi
                ? 'उत्तरी हिंद महासागर में कोई निम्न दबाव प्रणाली नहीं मिली।'
                : 'No low-pressure system was found in the North Indian Ocean.')}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
              <Stat label={hi ? 'स्कैन बिंदु' : 'Grid points scanned'} value={scanInfo.grid_points ?? '—'} />
              <Stat label={hi ? 'बेसिन' : 'Basins'} value={(scanInfo.basins || []).length || '—'} />
              <Stat
                label={hi ? 'सीमा' : 'LPA threshold'}
                value={scanInfo.lpa_threshold_hpa ? `${scanInfo.lpa_threshold_hpa} hPa` : '—'}
              />
              <Stat
                label={hi ? 'रिज़ॉल्यूशन' : 'Resolution'}
                value={scanInfo.resolution_deg ? `${scanInfo.resolution_deg}°` : '—'}
              />
            </div>

            {(scanInfo.basins || []).length > 0 && (
              <p className="text-xs text-emerald-700 mt-3">
                {hi ? 'जाँचे गए क्षेत्र: ' : 'Areas checked: '}
                {scanInfo.basins.join(' · ')}
              </p>
            )}
            <Provenance scan={scan} hi={hi} />
          </div>
        </div>
      </div>
    );
  }

  // ------------------------------------------- 3. system found: location risk
  if (!risk || risk.available === false) return null;

  const ns = risk.nearest_system;
  const theme = {
    SEVERE: { bg: 'bg-rose-50', border: 'border-rose-200', text: 'text-rose-900', pill: 'bg-rose-600' },
    HIGH: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-900', pill: 'bg-orange-600' },
    MODERATE: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-900', pill: 'bg-amber-500' },
    LOW: { bg: 'bg-sky-50', border: 'border-sky-200', text: 'text-sky-900', pill: 'bg-sky-600' },
    NONE: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-900', pill: 'bg-emerald-600' },
  }[risk.risk_level] || { bg: 'bg-slate-50', border: 'border-slate-200', text: 'text-slate-900', pill: 'bg-slate-500' };

  return (
    <div className={`${theme.bg} border ${theme.border} rounded-3xl p-6 shadow-sm`}>
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <ShieldAlert className={`h-6 w-6 flex-shrink-0 mt-0.5 ${theme.text}`} />
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className={`text-lg font-black ${theme.text}`}>
                {hi ? 'आपके स्थान पर चक्रवात जोखिम' : 'Cyclone risk at your location'}
              </h3>
              <span className={`text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full text-white ${theme.pill}`}>
                {risk.risk_level}
              </span>
            </div>
            <p className="text-sm text-slate-700 mt-1 flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5" />
              {risk.location || locationName}
              {risk.is_coastal ? (hi ? ' · तटीय' : ' · coastal') : (hi ? ' · अंतर्देशीय' : ' · inland')}
            </p>
          </div>
        </div>
        <div className="flex items-baseline gap-1">
          <span className={`text-4xl font-black ${theme.text}`}>{Math.round(risk.risk_score ?? 0)}</span>
          <span className="text-sm font-bold text-slate-400">/ 100</span>
        </div>
      </div>

      {ns && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
          <Stat label={hi ? 'दूरी' : 'Distance'} value={`${ns.distance_km} km`} />
          <Stat label={hi ? 'दिशा' : 'Bearing'} value={ns.bearing_from_location || '—'} />
          <Stat label={hi ? 'श्रेणी' : 'Category'} value={ns.category || '—'} />
          <Stat label={hi ? 'केंद्र दबाव' : 'Central pressure'} value={`${ns.central_pressure_hpa} hPa`} />
        </div>
      )}

      {ns?.movement && (
        <p className="text-xs text-slate-600 mt-3 flex items-center gap-1.5">
          <Navigation className="h-3.5 w-3.5" />
          {hi ? 'गति: ' : 'Moving '}
          {ns.movement.direction} {ns.movement.speed_kmh ? `at ${ns.movement.speed_kmh} km/h` : ''}
          {ns.position_uncertainty_km
            ? ` · ${hi ? 'स्थिति अनिश्चितता' : 'position uncertainty'} ±${ns.position_uncertainty_km} km`
            : ''}
        </p>
      )}

      {(risk.notes || []).length > 0 && (
        <ul className="mt-4 space-y-1.5">
          {risk.notes.map((n, i) => (
            <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
              <Info className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-slate-400" />
              <span>{n}</span>
            </li>
          ))}
        </ul>
      )}

      <Provenance scan={scan} risk={risk} hi={hi} />
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-white/70 border border-white rounded-xl px-3 py-2">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="text-sm font-black text-slate-800 mt-0.5">{value}</p>
    </div>
  );
}

function Provenance({ scan, risk, hi }) {
  const src = risk?.data_source || scan?.data_source;
  const at = risk?.checked_at || scan?.timestamp;
  return (
    <div className="mt-4 pt-3 border-t border-white/80">
      <p className="text-[11px] text-slate-500 leading-relaxed">
        <strong className="text-slate-600">
          {hi ? 'मॉडल अनुमान — आधिकारिक चेतावनी नहीं।' : 'Model estimate — not an official warning.'}
        </strong>{' '}
        {src && <>{hi ? 'स्रोत: ' : 'Source: '}{src}. </>}
        {at && <>{hi ? 'जाँचा गया: ' : 'Checked: '}{new Date(at).toLocaleString()}. </>}
        {hi ? 'आधिकारिक जानकारी के लिए IMD देखें।' : 'IMD remains the authoritative source.'}
      </p>
    </div>
  );
}
