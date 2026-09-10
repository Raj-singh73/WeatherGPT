"""Reference scores: run the index across realistic Indian weather conditions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))
from services.impact_score import compute_impact_score   # noqa: E402

# (label, rain mm/24h, gust km/h, tmax C, tmin C, pressure hPa, rain7d mm, anomaly ratio)
SCENARIOS = [
    ("— CLEAR / NORMAL —", None, None, None, None, None, None, None),
    ("Clear winter day, Delhi",            0.0,  12.0, 22.0, 9.0,  1016.0,   0.0, None),
    ("Pleasant post-monsoon, Nagpur",      0.0,  15.0, 31.0, 21.0, 1010.0,   8.0, None),
    ("Overcast, no rain, Kolkata",         0.4,  18.0, 30.0, 25.0, 1006.0,  12.0, None),

    ("— LIGHT / MODERATE RAIN —", None, None, None, None, None, None, None),
    ("Light drizzle, Mumbai",              3.0,  22.0, 29.0, 25.0, 1005.0,  20.0, 0.2),
    ("Moderate monsoon rain, Lucknow",    22.0,  28.0, 31.0, 26.0, 1000.0,  70.0, 0.6),
    ("Rather heavy rain, Guwahati",       48.0,  35.0, 29.0, 24.0,  998.0, 140.0, 1.1),

    ("— HEAVY RAIN / FLOOD —", None, None, None, None, None, None, None),
    ("Heavy rain, Mumbai monsoon",        95.0,  45.0, 28.0, 25.0,  996.0, 220.0, 2.4),
    ("Very heavy rain, Kerala",          150.0,  50.0, 27.0, 24.0,  994.0, 320.0, 3.5),
    ("Cloudburst, Uttarakhand",          260.0,  55.0, 22.0, 16.0,  992.0, 380.0, 8.0),
    ("Urban flood, Chennai NE monsoon",  120.0,  60.0, 27.0, 24.0,  995.0, 400.0, 4.2),

    ("— WIND / STORM —", None, None, None, None, None, None, None),
    ("Pre-monsoon squall, Kolkata",       18.0,  75.0, 34.0, 26.0, 1002.0,  25.0, 1.5),
    ("Dust storm, Rajasthan",              0.0,  85.0, 42.0, 29.0, 1000.0,   0.0, None),
    ("Thunderstorm with gusts, Bihar",    35.0,  70.0, 32.0, 25.0,  999.0,  60.0, 1.3),

    ("— CYCLONE —", None, None, None, None, None, None, None),
    ("Depression, Bay of Bengal coast",   45.0,  55.0, 29.0, 25.0,  994.0, 110.0, 1.4),
    ("Cyclonic storm approaching, Odisha", 90.0,  90.0, 28.0, 25.0,  986.0, 180.0, 2.8),
    ("Severe cyclone landfall, Puri",    160.0, 130.0, 27.0, 24.0,  968.0, 300.0, 6.0),

    ("— HEAT —", None, None, None, None, None, None, None),
    ("Hot summer day, Nagpur",             0.0,  20.0, 39.0, 27.0, 1002.0,   0.0, None),
    ("Heatwave, Rajasthan",                0.0,  25.0, 44.0, 30.0, 1000.0,   0.0, None),
    ("Severe heatwave, Vidarbha",          0.0,  22.0, 47.5, 33.0,  999.0,   0.0, None),

    ("— COLD —", None, None, None, None, None, None, None),
    ("Cool winter night, Lucknow",         0.0,  10.0, 20.0, 8.0,  1017.0,   0.0, None),
    ("Cold wave, Punjab",                  0.0,  14.0, 14.0, 3.0,  1019.0,   0.0, None),
    ("Severe cold wave, Kashmir valley",   0.0,  16.0,  6.0, -3.0, 1021.0,   0.0, None),

    ("— DRY-SEASON ANOMALY —", None, None, None, None, None, None, None),
    ("Unseasonal rain, Vidarbha (Feb)",   28.0,  40.0, 30.0, 17.0, 1008.0,  35.0, 9.0),
]

print(f"{'Weather condition':<36} {'rain':>6} {'gust':>6} {'tmax':>6} {'tmin':>6} "
      f"{'hPa':>7} | {'SCORE':>6} {'LEVEL':<9} {'driver':<12}")
print("-" * 116)
for row in SCENARIOS:
    label = row[0]
    if row[1] is None and label.startswith("—"):
        print(f"\n{label}")
        continue
    _, rain, gust, tmax, tmin, pres, r7, anom = row
    r = compute_impact_score(
        precipitation_mm=rain, wind_gust_kmh=gust,
        temperature_max_c=tmax, temperature_min_c=tmin,
        surface_pressure_hpa=pres, rainfall_7d_mm=r7,
        rainfall_anomaly_ratio=anom)
    print(f"{label:<36} {rain:>6} {gust:>6} {tmax:>6} {tmin:>6} {pres:>7} | "
          f"{r['score']:>6} {r['level']:<9} {r['dominant_hazard']:<12}")
