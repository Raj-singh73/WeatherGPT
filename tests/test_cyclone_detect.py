"""
Offline test of cyclone detection.

The Open-Meteo pressure field is replaced with a SYNTHETIC one containing a
cyclone at a known position. That tests the DETECTION ALGORITHM against a known
answer. No synthetic data ever reaches the application - this stub lives only
in the test.
"""
import sys
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import services.cyclone_detect as cd   # noqa: E402

fails = 0


def check(name, cond, detail=""):
    global fails
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")
    if not cond:
        fails += 1


# A cyclone centred at 17.0 N, 87.0 E with a 980 hPa core, drifting NW.
TRUE_LAT, TRUE_LON, CORE = 17.0, 87.0, 980.0
AMBIENT = 1010.0
HOURS = 96


def synthetic_field(points, forecast_hours=48):
    base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0, tzinfo=None)
    times = [(base + timedelta(hours=h)).isoformat(timespec="minutes") for h in range(HOURS)]
    cells = []
    for (la, lo) in points:
        pressures, gusts = [], []
        for h in range(HOURS):
            # centre drifts north-west at ~15 km/h
            clat = TRUE_LAT + 0.10 * h      # ~11 km/h north
            clon = TRUE_LON - 0.10 * h      # ~11 km/h west  (=> ~15 km/h NW)
            d = cd.haversine_km(la, lo, clat, clon)
            depth = (AMBIENT - CORE) * math.exp(-(d / 350.0) ** 2)
            pressures.append(round(AMBIENT - depth, 1))
            gusts.append(round(max(8.0, 150.0 * math.exp(-(d / 300.0) ** 2)), 1))
        cells.append({"lat": la, "lon": lo, "time": times,
                      "pressure": pressures, "wind": [g * 0.7 for g in gusts], "gust": gusts})
    return cells


def calm_field(points, forecast_hours=48):
    base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0, tzinfo=None)
    times = [(base + timedelta(hours=h)).isoformat(timespec="minutes") for h in range(HOURS)]
    return [{"lat": la, "lon": lo, "time": times,
             "pressure": [1010.0] * HOURS, "wind": [12.0] * HOURS, "gust": [18.0] * HOURS}
            for (la, lo) in points]


print("=" * 76)
print("A. A REAL SYSTEM IN THE FIELD MUST BE FOUND, AT ROUGHLY THE RIGHT PLACE")
print("=" * 76)
cd.fetch_field = synthetic_field
cd._CACHE.clear()
scan = cd.detect_active_systems(force=True)
check("scan reports available", scan["available"])
check("exactly one system detected", scan["active_systems_count"] == 1,
      f"got {scan['active_systems_count']}")
if scan["systems"]:
    s = scan["systems"][0]
    pos = s["current_position"]
    err = cd.haversine_km(pos["lat"], pos["lon"], TRUE_LAT, TRUE_LON)
    print(f"    true centre 17.0N 87.0E | detected {pos['lat']}N {pos['lon']}E "
          f"| error {err:.0f} km")
    check("centre within one grid cell (~250 km)", err <= 250, f"error {err:.0f} km")
    check("basin identified as Bay of Bengal", s["basin"] == "Bay of Bengal", s["basin"])
    print(f"    pressure {s['central_pressure_hpa']} hPa (true {CORE})  "
          f"vmax {s['vmax_kmh']} km/h  category {s['category']['title']}")
    check("central pressure close to truth", abs(s["central_pressure_hpa"] - CORE) < 12)
    check("classified at least a Cyclonic Storm",
          s["category"]["code"] in ("CS", "SCS", "VSCS", "ESCS", "SuCS"), s["category"]["code"])
    check("never flagged as official", s["provenance"]["is_official_warning"] is False)

print()
print("=" * 76)
print("B. THE TRACK MUST COME FROM FORECAST HOURS, NOT BE TYPED IN")
print("=" * 76)
if scan["systems"]:
    track = scan["systems"][0]["forecast_track"]
    print(f"    {len(track)} track points")
    for p in track:
        print(f"      {p['hour']:>6}  {p['lat']:.1f}N {p['lon']:.1f}E  "
              f"{p['pressure_hpa']} hPa  {p['intensity']}")
    check("more than one track point", len(track) > 1)
    moved = cd.haversine_km(track[0]["lat"], track[0]["lon"], track[-1]["lat"], track[-1]["lon"])
    check("centre actually moves along the track", moved > 50, f"{moved:.0f} km")
    mv = scan["systems"][0].get("movement")
    check("movement direction is north-westerly", mv and "N" in mv["direction"] and "W" in mv["direction"],
          str(mv))

print()
print("=" * 76)
print("C. A CALM FIELD MUST PRODUCE NO SYSTEM (no invented cyclone)")
print("=" * 76)
cd.fetch_field = calm_field
cd._CACHE.clear()
calm = cd.detect_active_systems(force=True)
check("no systems detected", calm["active_systems_count"] == 0)
check("message says so", "No active" in calm["message"], calm["message"])

print()
print("=" * 76)
print("D. PER-LOCATION RISK MUST FALL OFF WITH DISTANCE")
print("=" * 76)
cd.fetch_field = synthetic_field
cd._CACHE.clear()
places = [("Puri (Odisha coast)", 19.81, 85.83, True),
          ("Kolkata", 22.57, 88.36, True),
          ("Visakhapatnam", 17.69, 83.22, True),
          ("Nagpur (inland)", 21.15, 79.09, False),
          ("Delhi (far inland)", 28.61, 77.21, False),
          ("Mumbai (other coast)", 19.08, 72.88, True)]
prev = None
for nm, la, lo, coastal in places:
    r = cd.cyclone_risk_for_location(nm, la, lo, is_coastal=coastal)
    ns = r.get("nearest_system") or {}
    print(f"    {nm:<24} dist={ns.get('distance_km', 0):>7} km  "
          f"score={r['risk_score']:>5}  {r['risk_level']:<9} bearing={ns.get('bearing_from_location','-')}")
check("Puri outranks Delhi",
      cd.cyclone_risk_for_location("P", 19.81, 85.83, True)["risk_score"] >
      cd.cyclone_risk_for_location("D", 28.61, 77.21, False)["risk_score"])

print()
print("=" * 76)
print("E. FIELD UNAVAILABLE MUST DEGRADE HONESTLY")
print("=" * 76)
cd.fetch_field = lambda points, forecast_hours=48: None
cd._CACHE.clear()
down = cd.detect_active_systems(force=True)
check("available is False", down["available"] is False)
check("no systems invented", down["systems"] == [])
r = cd.cyclone_risk_for_location("Puri", 19.81, 85.83, True)
check("per-location risk reports UNKNOWN", r["risk_level"] == "UNKNOWN", r["risk_level"])
print(f"    message: {down['message'][:88]}...")

print()
print("ALL CYCLONE TESTS PASSED" if fails == 0 else f"{fails} TEST(S) FAILED")
sys.exit(1 if fails else 0)
