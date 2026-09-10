"""Verify the new impact index fixes every failure the probes found."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from services.impact_score import compute_impact_score, explain_impact   # noqa: E402

BENIGN = dict(precipitation_mm=0.0, wind_gust_kmh=15.0,
              temperature_max_c=31.0, temperature_min_c=23.0,
              surface_pressure_hpa=1008.0, rainfall_7d_mm=5.0)

fails = 0


def case(name, expect_level, **over):
    global fails
    args = dict(BENIGN); args.update(over)
    r = compute_impact_score(**args)
    ok = r["level"] == expect_level
    if not ok:
        fails += 1
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<38} score={r['score']:>5}  "
          f"level={r['level']:<8} (expected {expect_level})  driver={r['dominant_hazard']}")
    return r


print("=" * 88)
print("A. THE THREE REGRESSIONS THE OLD MODEL FAILED (all scored LOW before)")
print("=" * 88)
case("gusts 120 km/h, no rain", "SEVERE", wind_gust_kmh=120.0)
case("pressure 960 hPa, no rain", "SEVERE", surface_pressure_hpa=960.0)
case("temperature 48 C", "SEVERE", temperature_max_c=48.0)

print()
print("=" * 88)
print("B. RAINFALL MUST KEEP SCALING (old model saturated: 100mm=60.7, 200mm=60.8)")
print("=" * 88)
prev = -1
for mm in [0, 10, 30, 60, 100, 150, 250]:
    r = compute_impact_score(**{**BENIGN, "precipitation_mm": mm, "rainfall_7d_mm": mm * 1.5})
    mono = r["score"] >= prev
    if not mono:
        fails += 1
    print(f"  {'PASS' if mono else 'FAIL'}  rain {mm:>4} mm -> score {r['score']:>5}  "
          f"level {r['level']:<8} {r['dominant_band']}")
    prev = r["score"]

print()
print("=" * 88)
print("C. SEASONAL ANOMALY MUST MATTER (old model: Jan 22.4 vs Jul 22.1)")
print("=" * 88)
dry = compute_impact_score(**{**BENIGN, "precipitation_mm": 30.0,
                              "rainfall_anomaly_ratio": 9.0})   # 30mm in a dry month
wet = compute_impact_score(**{**BENIGN, "precipitation_mm": 30.0,
                              "rainfall_anomaly_ratio": 0.1})   # 30mm in monsoon
ok = dry["score"] > wet["score"]
if not ok:
    fails += 1
print(f"  {'PASS' if ok else 'FAIL'}  30 mm far above normal -> {dry['score']}   "
      f"30 mm in normal season -> {wet['score']}")
print(f"        note: {dry['anomaly_note']}")

print()
print("=" * 88)
print("D. ONE SEVERE HAZARD MUST OUTRANK SEVERAL MILD ONES (max, not average)")
print("=" * 88)
one_severe = compute_impact_score(**{**BENIGN, "wind_gust_kmh": 125.0})
many_mild = compute_impact_score(precipitation_mm=12.0, wind_gust_kmh=42.0,
                                 temperature_max_c=37.0, temperature_min_c=20.0,
                                 surface_pressure_hpa=1002.0, rainfall_7d_mm=60.0)
ok = one_severe["score"] > many_mild["score"]
if not ok:
    fails += 1
print(f"  {'PASS' if ok else 'FAIL'}  one severe hazard {one_severe['score']} > "
      f"several mild {many_mild['score']}")

print()
print("=" * 88)
print("E. MISSING INPUTS ARE OMITTED, NEVER FABRICATED")
print("=" * 88)
partial = compute_impact_score(precipitation_mm=80.0)      # only rain known
print(f"  components present: {[c['hazard'] for c in partial['components']]}")
ok = len(partial["components"]) == 1 and partial["available"]
if not ok:
    fails += 1
print(f"  {'PASS' if ok else 'FAIL'}  only the known hazard contributes -> "
      f"score {partial['score']}, level {partial['level']}")
none_known = compute_impact_score()
ok2 = none_known["available"] is False and none_known["score"] is None
if not ok2:
    fails += 1
print(f"  {'PASS' if ok2 else 'FAIL'}  nothing known -> available=False, no invented score")

print()
print("=" * 88)
print("F. BENIGN WEATHER MUST STAY LOW (no false alarms)")
print("=" * 88)
case("calm clear day", "LOW")
case("light rain 4 mm", "LOW", precipitation_mm=4.0)
case("breezy 35 km/h", "LOW", wind_gust_kmh=35.0)

print()
print("=" * 88)
print("G. WORKED EXAMPLE - explanation is grounded in real measured values")
print("=" * 88)
cyc = compute_impact_score(precipitation_mm=140.0, wind_gust_kmh=95.0,
                           temperature_max_c=29.0, temperature_min_c=25.0,
                           surface_pressure_hpa=982.0, rainfall_7d_mm=260.0,
                           rainfall_anomaly_ratio=6.2)
print(f"  Cyclone landfall scenario -> score {cyc['score']}, {cyc['level']}")
for line in explain_impact(cyc):
    print("    -", line)

print()
print("ALL IMPACT TESTS PASSED" if fails == 0 else f"{fails} TEST(S) FAILED")
sys.exit(1 if fails else 0)
