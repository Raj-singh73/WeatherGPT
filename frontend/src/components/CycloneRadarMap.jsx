import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { ShieldAlert, Compass, Wind, AlertTriangle } from 'lucide-react';

// Custom Map Markers
const createPressureIcon = (letter, color, bgColor = 'white') => L.divIcon({
  className: 'custom-pressure-pin',
  html: `<div style="display:flex;align-items:center;justify-content:center;width:38px;height:38px;background:${bgColor};border:3px solid ${color};border-radius:50%;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-weight:900;font-size:16px;color:${color};font-family:sans-serif;">
    ${letter}
  </div>`,
  iconSize: [38, 38],
  iconAnchor: [19, 19],
  popupAnchor: [0, -20]
});

const createLandfallIcon = () => L.divIcon({
  className: 'custom-landfall-pin',
  html: `<div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;background:#e11d48;border:3px solid white;border-radius:50%;box-shadow:0 4px 12px rgba(225,29,72,0.5);color:white;">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="22" y1="12" x2="18" y2="12"></line>
      <line x1="6" y1="12" x2="2" y2="12"></line>
      <line x1="12" y1="6" x2="12" y2="2"></line>
      <line x1="12" y1="22" x2="12" y2="18"></line>
    </svg>
  </div>`,
  iconSize: [36, 36],
  iconAnchor: [18, 18],
  popupAnchor: [0, -20]
});

export default function CycloneRadarMap({ activeSystem }) {
  if (!activeSystem) return null;

  const currentPos = activeSystem.current_position || { lat: 17.8, lon: 86.4 };
  // The detector reports a steering ridge only when one is actually resolved in
  // the pressure field. Previously this fell back to fixed coordinates, drawing
  // an "H" marker for a ridge that had not been measured.
  const ridgePos = activeSystem.high_pressure_ridge || null;
  const landfall = activeSystem.landfall_prediction || {};
  const forecastTrack = activeSystem.forecast_track || [];

  const trackPoints = forecastTrack.map(pt => [pt.lat, pt.lon]);

  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-rose-600 uppercase tracking-wider mb-1">
            <span className="flex h-2 w-2 rounded-full bg-rose-600 animate-ping"></span>
            <span>Synoptic Pressure & Cyclone Genesis Radar</span>
          </div>
          <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
            <span>{activeSystem.name}</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 font-extrabold border border-rose-200 uppercase">
              {typeof activeSystem.category === 'object' ? (activeSystem.category?.title || activeSystem.category?.code) : (activeSystem.category || 'Cyclone')}
            </span>
          </h3>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-600 font-semibold bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-rose-600 inline-flex items-center justify-center text-[9px] text-white font-black">L</span>
            Low Pressure: <strong>{activeSystem.central_pressure_hpa} hPa</strong>
          </span>
          <span className="text-slate-300">|</span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-sky-600 inline-flex items-center justify-center text-[9px] text-white font-black">H</span>
            Ambient Ridge: <strong>{activeSystem.ambient_pressure_hpa} hPa</strong>
          </span>
        </div>
      </div>

      {/* Leaflet Map Canvas */}
      <div className="flex-1 w-full rounded-2xl overflow-hidden border border-slate-200 relative min-h-[380px] bg-slate-100">
        <MapContainer
          key={`cyclone_map_${currentPos.lat}_${currentPos.lon}`}
          center={[currentPos.lat || 19.5, currentPos.lon || 84.5]}
          zoom={6}
          scrollWheelZoom={false}
          className="h-full w-full"
          style={{ height: '100%', minHeight: '380px' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Isobar Concentric Pressure Circles around the Low Pressure Center */}
          {activeSystem.isobar_rings?.map((ring, idx) => (
            <Circle
              key={idx}
              center={[currentPos.lat, currentPos.lon]}
              radius={ring.radius_km * 1000}
              pathOptions={{
                color: ring.color,
                fillColor: ring.color,
                fillOpacity: idx === 0 ? 0.22 : 0.04,
                weight: 1.5,
                dashArray: idx > 1 ? '4, 4' : undefined
              }}
            >
              <Popup>
                <div className="p-1 text-xs">
                  <strong className="text-slate-900">{ring.label}</strong>
                  <p className="text-slate-600 text-[11px]">Radius: ~{ring.radius_km} km</p>
                </div>
              </Popup>
            </Circle>
          ))}

          {/* Forecast Landfall Track Line */}
          {trackPoints.length > 1 && (
            <Polyline
              positions={trackPoints}
              pathOptions={{
                color: '#e11d48',
                weight: 3,
                dashArray: '6, 6'
              }}
            />
          )}

          {/* Low Pressure Vortex Center Marker (L) */}
          <Marker position={[currentPos.lat, currentPos.lon]} icon={createPressureIcon('L', '#e11d48')}>
            <Popup>
              <div className="p-1.5 text-xs text-slate-800">
                <h4 className="font-extrabold text-rose-600 text-sm mb-1">LOW PRESSURE CORE (L)</h4>
                <p><strong>System:</strong> {activeSystem.name}</p>
                <p><strong>Central Pressure:</strong> <span className="font-black text-rose-600">{activeSystem.central_pressure_hpa} hPa</span></p>
                <p><strong>Pressure Drop Rate:</strong> {activeSystem.pressure_drop_rate_hpa_3h} hPa / 3h</p>
                <p><strong>Max Sustained Winds:</strong> {activeSystem.vmax_kmh} km/h (Gusts: {activeSystem.gust_kmh} km/h)</p>
                <p><strong>Sea Surface Temp:</strong> {currentPos.sea_surface_temp_c}°C</p>
              </div>
            </Popup>
          </Marker>

          {/* High Pressure Blocking Ridge Marker (H) */}
          {ridgePos && (
          <Marker position={[ridgePos.lat, ridgePos.lon]} icon={createPressureIcon('H', '#2563eb')}>
            <Popup>
              <div className="p-1.5 text-xs text-slate-800">
                <h4 className="font-extrabold text-sky-600 text-sm mb-1">HIGH PRESSURE RIDGE (H)</h4>
                <p><strong>Ridge Pressure:</strong> {ridgePos.pressure_hpa} hPa</p>
                <p><strong>Influence:</strong> {ridgePos.steering_influence}</p>
              </div>
            </Popup>
          </Marker>
          )}

          {/* Predicted Landfall Target Marker */}
          {landfall.landfall_lat && (
            <Marker position={[landfall.landfall_lat, landfall.landfall_lon]} icon={createLandfallIcon()}>
              <Popup>
                <div className="p-1.5 text-xs text-slate-800">
                  <h4 className="font-extrabold text-rose-700 text-sm mb-1">TARGET LANDFALL ZONE</h4>
                  <p><strong>Location:</strong> {landfall.predicted_point}</p>
                  <p><strong>ETA:</strong> ~{landfall.eta_hours} Hours</p>
                  <p><strong>Wind at Landfall:</strong> {landfall.expected_intensity_at_landfall}</p>
                  <p><strong>Storm Surge:</strong> {activeSystem.estimated_surge_m} m</p>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Track Waypoint Markers */}
          {forecastTrack.map((pt, i) => (
            <Marker
              key={i}
              position={[pt.lat, pt.lon]}
              icon={L.divIcon({
                className: 'custom-waypoint',
                html: `<div style="width:10px;height:10px;background:#e11d48;border:2px solid white;border-radius:50%;box-shadow:0 1px 4px rgba(0,0,0,0.4);"></div>`,
                iconSize: [10, 10],
                iconAnchor: [5, 5]
              })}
            >
              <Popup>
                <div className="p-1 text-xs">
                  <p className="font-bold text-slate-900">{pt.hour}</p>
                  <p>Pressure: {pt.pressure_hpa} hPa</p>
                  <p>Intensity: {pt.intensity}</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Map Legend & Physics Annotations */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-600 gap-2">
        <div className="flex items-center flex-wrap gap-4">
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-rose-600 inline-block"></span>
            <strong>L</strong>: Low Pressure Core ({activeSystem.central_pressure_hpa} hPa)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-sky-600 inline-block"></span>
            <strong>H</strong>: High Pressure Ridge ({activeSystem.ambient_pressure_hpa} hPa)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 bg-rose-600 inline-block border-t border-dashed border-rose-600"></span>
            Landfall Track Vector (dP/dx)
          </span>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">
          Gradient: {activeSystem.pressure_gradient}
        </span>
      </div>
    </div>
  );
}
