# -*- coding: utf-8 -*-
"""
Test script for verifying WeatherGPT conversational decision engine across real-world use cases.
"""
import os
import sys
import io

# Set UTF-8 for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))
from services.llm_service import process_chat_message

test_queries = [
    ("Can I wash my car today in Nagpur?", "CAR_WASH"),
    ("Can I dry clothes outside today in Nagpur?", "DRYING_CLOTHES"),
    ("Can we play cricket tomorrow in Delhi?", "OUTDOOR_SPORTS"),
    ("Can we organize an outdoor wedding this weekend in Mumbai?", "OUTDOOR_EVENT"),
    ("Should I harvest wheat tomorrow in Lucknow?", "HARVESTING"),
    ("Can I paint my exterior walls tomorrow in Nagpur?", "CONSTRUCTION_PAINTING"),
    ("Is there fog tomorrow morning in Lucknow for driving?", "FOG_VISIBILITY"),
    ("Will heavy rain cause waterlogging in Lucknow?", "FLOOD_WATERLOGGING"),
    ("Is it safe for kids to go out in the heat in Delhi?", "HEALTH_HEAT_COLD"),
    ("Will it rain tomorrow in Wardha?", "RAIN_CHECK"),
    ("क्या आज नागपुर में कपड़े बाहर सुखा सकते हैं?", "DRYING_CLOTHES"),
    ("क्या मुझे आज कार धोनी चाहिए?", "CAR_WASH"),
]

print("=" * 80)
print("TESTING WEATHERGPT REAL-WORLD USE CASE DECISION ENGINE")
print("=" * 80)

passed = 0
for query, expected_use_case in test_queries:
    res = process_chat_message(query)
    actual_use_case = res.get("use_case")
    verdict = res.get("verdict")
    badge = res.get("verdict_badge")
    score = res.get("suitability_score")
    steps = res.get("action_steps", [])
    
    is_match = (actual_use_case == expected_use_case)
    status_str = "PASS" if is_match else "FAIL"
    if is_match:
        passed += 1
        
    print(f"\n[{status_str}] Query: \"{query}\"")
    print(f"  Detected Use Case : {actual_use_case} (Expected: {expected_use_case})")
    print(f"  Action Verdict    : {verdict} ({badge})")
    print(f"  Suitability Score : {score}/100")
    print(f"  Action Directives : {len(steps)} steps")
    print(f"  Response Preview  : {res['response'][:110].strip()}...")

print("\n" + "=" * 80)
print(f"RESULTS: {passed}/{len(test_queries)} queries passed accurately!")
print("=" * 80)
