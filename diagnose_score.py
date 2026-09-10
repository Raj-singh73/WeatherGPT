"""
diagnose_score.py - Find out why the Weather Impact Score is wrong.

Run from the project root:
    python diagnose_score.py

It checks each layer in order and prints the FIRST thing that actually fails,
with the real exception, instead of leaving you to guess from the UI.
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

FAIL = []


def step(name):
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)


# ---------------------------------------------------------------- 1. imports
step("1. Can the new modules be imported?")
for mod in ["services.impact_score", "services.climatology_service", "services.ml_service"]:
    try:
        __import__(mod)
        print(f"  OK    {mod}")
    except Exception:
        FAIL.append(mod)
        print(f"  FAIL  {mod}")
        traceback.print_exc()

if FAIL:
    print("\nSTOP: an import failed above. That alone makes every score fall back "
          "to 0 / UNAVAILABLE. Fix the traceback and re-run.")
    sys.exit(1)

# --------------------------------------------------------- 2. pure index maths
step("2. Does the index compute WITHOUT any network?")
from services.impact_score import compute_impact_score        # noqa: E402
try:
    r = compute_impact_score(precipitation_mm=40.0, wind_gust_kmh=60.0,
                             temperature_max_c=33.0, temperature_min_c=25.0)
    print(f"  score={r['score']}  level={r['level']}  driver={r['dominant_hazard']}")
    print("  OK    the index itself is fine (this needs no internet)")
    if r["score"] == 0:
        print("  WARNING: score is 0 with real inputs - that should not happen.")
except Exception:
    print("  FAIL  the index raised:")
    traceback.print_exc()
    sys.exit(1)

# ------------------------------------------------------- 3. network enrichers
step("3. Are the optional network lookups reachable? (failures are survivable)")
from services.climatology_service import compute_rainfall_anomaly   # noqa: E402
from services.ml_service import fetch_antecedent_rainfall           # noqa: E402

try:
    a = compute_rainfall_anomaly(30.0, 26.8467, 80.9462, "2026-07-19", blocking=True)
    print(f"  climatology available={a.get('available')}  "
          f"baseline={a.get('climatology_mm')}  reason={a.get('reason', '-')}")
except Exception:
    print("  climatology raised (survivable):")
    traceback.print_exc()

try:
    b = fetch_antecedent_rainfall(26.8467, 80.9462)
    print(f"  antecedent rainfall available={b.get('available')}  "
          f"days={len(b.get('series', {}))}")
except Exception:
    print("  antecedent raised (survivable):")
    traceback.print_exc()

# --------------------------------------------------------- 4. the service call
step("4. What does the service return for one forecast day?")
from services.ml_service import assess_risk_from_daily_features     # noqa: E402
try:
    d = assess_risk_from_daily_features(
        location="Lucknow", lat=26.8467, lon=80.9462,
        t_max=33.0, t_min=26.0, precipitation=40.0, wind_gust=60.0,
        climatology=9.4, weather_code=63, date_str="2026-07-19")
    print(f"  risk_score      : {d['risk_score']}")
    print(f"  risk_level      : {d['risk_level']}")
    print(f"  dominant_hazard : {d.get('dominant_hazard')}")
    print(f"  inputs_available: {d.get('inputs_available')}")
    print(f"  confidence      : {d['confidence']}")
    if d["risk_score"] == 0:
        print("\n  >>> THIS IS THE PROBLEM. The service returned 0.")
        print("  >>> reason:", d.get("unavailable_reason") or d.get("recommendation"))
except Exception:
    print("  FAIL  the service raised - this is why the UI shows 0:")
    traceback.print_exc()
    sys.exit(1)

# ------------------------------------------------------------- 5. the real API
step("5. What do the HTTP endpoints return?")
try:
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)

    r = c.post("/api/predict/risk", json={
        "location": "Lucknow", "latitude": 26.8467, "longitude": 80.9462,
        "precipitation": 40.0, "wind_gust": 60.0,
        "temperature_max": 33.0, "temperature_min": 26.0})
    print(f"  POST /api/predict/risk -> {r.status_code}")
    if r.status_code == 200:
        j = r.json()
        print(f"    risk_score={j['risk_score']}  risk_level={j['risk_level']}  "
              f"driver={j.get('dominant_hazard')}")
    else:
        print("    body:", str(r.text)[:400])

    r2 = c.get("/api/weather/forecast?location=Lucknow&days=3")
    print(f"  GET  /api/weather/forecast -> {r2.status_code}")
    if r2.status_code == 200:
        j2 = r2.json()
        print(f"    data_source: {j2.get('data_source')}")
        for day in j2["forecast_days"]:
            print(f"    {day['date']}  score={day['risk_score']:<6} "
                  f"level={day['risk_level']:<12} rain={day['precipitation_sum']} mm  "
                  f"gust={day['wind_gust_max']} km/h")
        if all(d["risk_score"] == 0 for d in j2["forecast_days"]):
            print("\n    >>> Every day is 0. If step 4 above was NOT 0, the failure is")
            print("    >>> inside weather_service.get_forecast - check the [WARN] lines")
            print("    >>> printed by your running backend.")
    else:
        print("    body:", str(r2.text)[:400])
except Exception:
    print("  FAIL  could not start the app:")
    traceback.print_exc()

print("\n" + "=" * 70)
print("Done. Paste this whole output if the score is still wrong.")
print("=" * 70)
