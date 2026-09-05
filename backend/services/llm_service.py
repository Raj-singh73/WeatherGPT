"""
llm_service.py - Multi-provider Conversational Natural Language Synthesis & Decision Engine
SIH 2026 Problem Statement SIH26068: "From Weather Data to Actionable Decisions."

Features:
- Domain-Grounded Use Case Intent Classification (Laundry, Car Wash, Sports, Events, Farming, Painting, Fog, Floods)
- Direct Actionable Solutions (RECOMMENDED / CAUTION / NOT RECOMMENDED)
- Telemetry & ML Risk (HistGradientBoosting) Grounding
- Multilingual Natural Language Generation (English, Hindi, Marathi, Tamil, etc.)
- Structured Decision Metadata (Verdict, Suitability Score, Action Steps)
"""

import os
import re
import httpx
from typing import Dict, Any, List, Tuple, Optional
from config import settings
from rag.retriever import get_retriever
from services.weather_service import get_current_weather, get_forecast, resolve_location, compute_calibrated_rain_probability
from services.ml_service import assess_risk_from_daily_features
from services.farmer_service import get_current_agricultural_season, CROP_VALID_SEASONS

# Priority Intent Categories & Multi-Language Triggers
# NOTE: High-specificity intents must precede general ones to prevent false matches
INTENT_PATTERNS = {
    # 1. Laundry & Clothes Drying
    "DRYING_CLOTHES": [
        "dry clothes", "drying clothes", "dry laundry", "hang clothes", "dry my clothes",
        "wash and dry", "clothes dry", "kapde sukha", "kapde sukhana", "laundry",
        "कपड़े सुखाना", "कपड़े सुखाएं", "कपड़े सुखा", "सुखाना", "सुखा सकते", "कपडे वाळवणे", "துணி காயவைக்க"
    ],
    # 2. Car & Vehicle Washing
    "CAR_WASH": [
        "car wash", "wash car", "wash my car", "bike wash", "wash bike", "vehicle wash",
        "car dhona", "gaadi dhona", "gadi dhona", "car cleaning", "dhoni chahiye",
        "कार धोना", "कार धोनी", "कार धोएं", "कार धुलवा", "कार धुलवाना", "गाड़ी धोना", "गाड़ी धोनी", "गाड़ी धोएं", "वाहन धोणे", "गाड़ी धुलना", "வண்டி கழுவ"
    ],
    # 3. Outdoor Sports & Activities
    "OUTDOOR_SPORTS": [
        "play cricket", "cricket", "football", "match", "play outside", "outdoor game",
        "cricket match", "badminton", "running", "jogging", "morning walk", "sports",
        "क्रिकेट", "मैच", "खेल", "फुटबॉल", "दौड़", "क्रीडा", "விளையாட"
    ],
    # 4. Outdoor Functions, Weddings & Shamianas
    "OUTDOOR_EVENT": [
        "wedding", "marriage", "party", "outdoor event", "function", "picnic", "tent",
        "shamiana", "mandap", "outdoor gathering", "shaadi", "shadi", "utsaav", "celebration",
        "शादी", "समारोह", "पार्टी", "पिकनिक", "मंडप", "विवाह"
    ],
    # 5. Construction & Exterior Painting
    "CONSTRUCTION_PAINTING": [
        "exterior paint", "wall paint", "paint walls", "painting", "paint", "concrete",
        "cement", "linter", "plaster", "construction", "roofing", "rangai", "putai", "chhat",
        "रंगाई", "पुताई", "पेंट", "सीमेंट", "ल॔टर", "बांधकाम", "रंगकाम"
    ],
    # 6. Agriculture: Harvesting
    "HARVESTING": [
        "harvest", "harvesting", "reap", "cutting crop", "crop cut", "katai",
        "fasal katna", "fasal ki katai", "fasal katai", "sickle", "combine harvest",
        "कटाई", "काटना", "फसल काटना", "அறுவடை", "कापणी"
    ],
    # 7. Agriculture: Spraying
    "SPRAY_PESTICIDE": [
        "spray", "spraying", "pesticide", "insecticide", "fungicide", "herbicide",
        "dawa", "dawai", "chhidkav", "chidkaav", "kitnashak", "marunthu", "aushadh",
        "छिड़काव", "दवा", "दवाई", "कीटनाशक", "स्प्रे", "कीटनाशक छिड़कना", "மருந்து", "फवारणी", "ঔষধ"
    ],
    # 7b. Agriculture: Crop Recommendation & Seasonal Suitability
    "CROP_RECOMMENDATION": [
        "which crop", "what crop", "recommend crop", "crop recommendation", "crops to grow",
        "crop to grow", "suitable crop", "favorable crop", "crop for this season", "crops for this season",
        "crop in this season", "which farming", "what to grow", "which crop can i", "crop selection",
        "which crop is favorable", "crop favorable", "favoral", "konsi fasal", "kaun si fasal",
        "koun si fasal", "fasal ki buwai", "kaun sa crop", "kaun si kheti", "konsi kheti",
        "fasal lagaye", "fasal boye", "kaun sa anaj", "which crops grow", "which crop grow",
        "कौन सी फसल", "कौनसी फसल", "कौन सी खेती", "फसल सिफारिश", "मौसम की फसल", "उपयुक्त फसल", "फसल चयन"
    ],
    # 8. Agriculture: Sowing
    "SOWING": [
        "sow", "sowing", "seed", "seeding", "plant", "planting", "bona", "buwai",
        "lagana", "ropan", "vithai", "perani", "vapasa",
        "बुवाई", "बोना", "बीज", "रोपणी", "पेरणी", "விதைப்பு"
    ],
    # 9. Agriculture: Irrigation
    "IRRIGATION": [
        "irrigate", "irrigation", "water crop", "watering", "sinchai", "pani dena",
        "pani lagana", "neerpaasanam", "paani dyave",
        "सिंचाई", "पानी देना", "पानी लगाना", "பாசனம்", "पाणी"
    ],
    # 9b. Agriculture: Fertilizer & Urea Application
    "FERTILIZER": [
        "fertilizer", "fertiliser", "urea", "dap", "potash", "manure", "khad", "khad dalna",
        "urea dalna", "top dressing", "खाद", "यूरिया", "डीएपी", "खत", "உரம்"
    ],
    # 10. Fog, Smog & Road Visibility
    "FOG_VISIBILITY": [
        "fog", "foggy", "mist", "smog", "visibility", "kohra", "dhund", "driving visibility",
        "highway visibility", "low visibility",
        "कोहरा", "धुंध", "दृश्यता", "धुकं", "பனிமூட்டம்"
    ],
    # 11. Floods & Waterlogging
    "FLOOD_WATERLOGGING": [
        "flood", "flooding", "waterlog", "waterlogging", "inundation", "drainage",
        "jalbharaav", "jal jamav", "baadh", "overflow",
        "जलभराव", "बाढ़", "जल जमाव", "पूर", "வெள்ளம்"
    ],
    # 12. Health, Heatwave & Cold Safety
    "HEALTH_HEAT_COLD": [
        "heat stroke", "sunstroke", "heatwave", "loo", "cold wave", "safe for kids",
        "elderly", "sunburn", "uv index", "garmi se bachav", "sardi se bachav", "extreme heat",
        "लू", "हीटवेव", "शीतलहर", "लू लगना", "வெப்ப அலை"
    ],
    # 12b. Commute: Two-Wheeler & Bike Safety
    "BIKE_COMMUTE": [
        "bike", "motorcycle", "scooter", "two wheeler", "by bike", "bike se", "bike chala",
        "ride bike", "bike chalana", "scooty", "बाइक", "स्कूटर", "मोटरसाइकिल", "இருசக்கர வாகனம்"
    ],
    # 13. Travel & Highway Safety
    "TRAVEL_SAFETY": [
        "travel", "trip", "drive", "driving", "road", "safe to travel", "flight",
        "commute", "highway", "visit", "safar", "yatra", "payanam", "pravas",
        "यात्रा", "सफर", "गाड़ी", "सड़क", "रास्ता", "प्रवास"
    ],
    # 14. Cyclones & Severe Storms
    "CYCLONE_STORM": [
        "cyclone", "dana", "storm", "thunderstorm", "depression", "toofan",
        "chakravat", "puyal", "chanda marutham", "andhi", "bhavandar", "lightning", "thunder",
        "चक्रवात", "तूफान", "आंधी", "दाना", "पुயல்", "वादळ", "बिजली"
    ],
    # 15. Clothing & Daily Attire
    "CLOTHING": [
        "what to wear", "clothes to wear", "jacket", "coat", "sweater", "garam kapde",
        "dress warm", "kaise kapde pehne", "dress code",
        "कपड़े पहनें", "जैकेट", "रेनकोट", "गरम कपड़े"
    ],
    # 16. Direct Rain & Umbrella Check
    "RAIN": [
        "rain", "raining", "rainfall", "chance of rain", "will it rain", "umbrella", "chatha",
        "rain tomorrow", "rain today", "downpour", "shower", "baarish", "pani girega", "barsat",
        "malai", "paaus", "brishti", "varsham", "varsad",
        "बारिश", "बरसात", "वर्षा", "पानी गिरेगा", "पानी बरसेगा", "मूसलाधार",
        "மழை", "மழை வருமா", "पाऊस", "पाऊस पडेल", "বৃষ্টি", "వర్షం", "વરસાદ", "छाता"
    ],
    # 17. Current Temperature & Heat
    "TEMPERATURE_NOW": [
        "temperature", "how hot", "how cold", "taapmaan", "kulir", "veppam", "tapman",
        "तापमान", "गर्मी कितनी है", "ठंडी कितनी है"
    ],
    # 18. Wind & Humidity
    "HUMIDITY_WIND": [
        "wind", "windy", "breeze", "gust", "humidity", "moisture", "hawa",
        "nami", "katru", "vaara", "hava",
        "हवा", "आर्द्रता", "नमी", "हवा की गति"
    ],
    # 19. Climate History & Cyclone Records
    "CLIMATE_HISTORY": [
        "climate", "history", "trend", "annual", "1891", "archive", "century",
        "record", "purana", "itihas", "varalaru",
        "जलवायु", "इतिहास", "पुराना रिकॉर्ड"
    ],
    # 20. Multi-Day & Weekend Forecast
    "GENERAL_FORECAST": [
        "tomorrow", "forecast", "weekend", "next week", "upcoming", "kal",
        "aane wale", "adutha", "pudhil", "3 days", "this week",
        "पूर्वानुमान", "कल", "आने वाले दिन", "सप्ताहांत"
    ],
    # 21. Greetings
    "GREETING": [
        "hello", "hi", "hey", "namaste", "vanakkam", "kem cho", "namaskar",
        "who are you", "what can you do", "help me", "introduce", "kya kar sakte ho", "kaise ho",
        "नमस्ते", "नमस्कार", "வணக்கம்", "કેમ છો", "নমস্কার"
    ]
}

def detect_intent_and_location(user_msg: str, default_loc: str = "Nagpur") -> Tuple[str, str, Dict[str, str]]:
    """Detects primary user question intent with high precision, extracts location and optional crop context."""
    text_lower = user_msg.lower().strip()

    # 1. Location extraction
    extracted_loc = default_loc
    for key, loc in settings.LOCATIONS.items():
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, text_lower):
            extracted_loc = loc["name"]
            break

    # 2. Crop extraction
    crop_info = {}
    crops = ["wheat", "rice", "paddy", "maize", "cotton", "sugarcane", "pulses", "soybean", "mustard", "gehu", "dhan", "sarson", "chana"]
    for c in crops:
        if c in text_lower:
            c_std = "Wheat" if c in ["wheat", "gehu"] else ("Rice" if c in ["rice", "dhan"] else ("Mustard" if c == "sarson" else c.title()))
            crop_info["crop"] = c_std
            break

    # 3. Intent Detection: Iterate through ordered dictionary
    for intent, keywords in INTENT_PATTERNS.items():
        for kw in keywords:
            if len(kw) <= 3:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    return intent, extracted_loc, crop_info
            elif kw in text_lower:
                return intent, extracted_loc, crop_info

    return "GENERAL_WEATHER", extracted_loc, crop_info

def evaluate_use_case_decision(
    query: str,
    intent: str,
    location: str,
    lang: str,
    curr: Any,
    forecast: Any,
    risk: Dict[str, Any],
    crop_info: Dict[str, str],
    persona: str = "GENERAL"
) -> Tuple[str, Dict[str, Any]]:
    """
    Evaluates weather telemetry and ML impact risk to generate a direct, actionable solution
    tailored to the user's specific problem, persona, and question.
    """
    f0 = forecast.forecast_days[0] if forecast.forecast_days else None
    f1 = forecast.forecast_days[1] if len(forecast.forecast_days) > 1 else f0
    three_day_rain = sum(d.precipitation_sum for d in forecast.forecast_days[:3]) if forecast.forecast_days else 0.0
    rain_today = f0.precipitation_sum if f0 else 0.0
    rain_tomorrow = f1.precipitation_sum if f1 else 0.0
    rain_next_48h = rain_today + rain_tomorrow

    # Calculate calibrated probabilities from actual physics model
    if f0 and getattr(f0, 'precipitation_probability_max', None) is not None:
        rain_prob_today = float(f0.precipitation_probability_max)
    else:
        wc0 = getattr(f0, 'weather_code', 1) if f0 else 1
        rain_prob_today = compute_calibrated_rain_probability(rain_today, wc0)

    if f1 and getattr(f1, 'precipitation_probability_max', None) is not None:
        rain_prob = float(f1.precipitation_probability_max)
    else:
        wc1 = getattr(f1, 'weather_code', 1) if f1 else 1
        rain_prob = compute_calibrated_rain_probability(rain_tomorrow, wc1)

    wind_gust = f1.wind_gust_max if f1 else curr.wind_gust
    crop_name = crop_info.get("crop", "crops")
    humidity = curr.relative_humidity
    temp = curr.temperature
    apparent_temp = curr.apparent_temperature

    # Dew point estimation (Approximation: T - (100 - RH)/5)
    dew_point = temp - ((100.0 - humidity) / 5.0)
    dew_depression = max(0.0, temp - dew_point)

    meta = {
        "verdict": "INFO",
        "verdict_badge": "ℹ️ ADVISORY",
        "use_case": intent,
        "persona": persona,
        "suitability_score": 85.0,
        "action_steps": []
    }

    # ==================== 1. LAUNDRY & DRYING CLOTHES ====================
    if intent == "DRYING_CLOTHES":
        if rain_today > 1.0 or (rain_tomorrow > 2.0 and rain_prob > 60):
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 NOT RECOMMENDED (RAIN RISK)"
            score = 20.0
            steps = [
                "Hang wet clothes indoors under a ceiling fan or in a ventilated hallway.",
                f"Outdoor precipitation ({rain_today:.1f} mm today) will re-soak garments.",
                "Wait until clear sunny conditions return."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **नहीं, आज {location} में कपड़े बाहर सुखाना सही नहीं है।**\n\n"
                    f"• **कारण**: आज **{rain_today:.1f} मिमी वर्षा** ({rain_prob:.0f}% संभावना) का अनुमान है। कपड़े भीग जाएंगे और धूप न मिलने से सीलन की बदबू आएगी।\n"
                    f"• **हवा में नमी (Humidity)**: {humidity:.0f}% (उच्च स्तर)।\n\n"
                    f"💡 **समाधान**: कपड़े घर के अंदर पंखे की हवा में या हवादार बालकनी में सुखाएं।"
                )
            else:
                text = (
                    f"🔴 **No, do not dry clothes outdoors in {location} today.**\n\n"
                    f"• **Reason**: Active precipitation forecast ({rain_today:.1f} mm rain, {rain_prob:.0f}% likelihood). Outdoor laundry will get soaked and develop a damp mildew odor.\n"
                    f"• **Relative Humidity**: High at {humidity:.0f}%.\n\n"
                    f"💡 **Actionable Solution**: Dry clothes indoors under ceiling fans or in a sheltered, well-ventilated corridor."
                )
        elif humidity > 78.0:
            verdict = "CAUTION"
            badge = "🟡 CAUTION (SLOW DRYING)"
            score = 55.0
            steps = [
                "Place clothes outdoors only between 11:00 AM and 3:00 PM for maximum solar exposure.",
                "Bring laundry inside before evening dew sets in (by 4:30 PM).",
                "Ensure generous spacing between heavy fabric items."
            ]
            if lang == "hi":
                text = (
                    f"🟡 **सतर्कता के साथ: आज {location} में कपड़े धीरे-धीरे सूखेंगे।**\n\n"
                    f"• **मौसम स्थिति**: बारिश की संभावना कम है ({rain_today:.1f} मिमी), लेकिन हवा में अत्यधिक नमी (**{humidity:.0f}% आर्द्रता**) के कारण वाष्पीकरण धीमा रहेगा।\n"
                    f"• **सुखाने का सर्वश्रेष्ठ समय**: सुबह 11:00 बजे से दोपहर 3:30 बजे के बीच सीधी धूप में रखें।\n\n"
                    f"💡 **सलाह**: शाम 4:30 बजे से पहले कपड़े अंदर ले लें ताकि ओस से दोबारा गीले न हों।"
                )
            else:
                text = (
                    f"🟡 **Conditional: Laundry will dry slowly outdoors in {location} today.**\n\n"
                    f"• **Atmospheric Condition**: Rain risk is low ({rain_today:.1f} mm), but elevated relative humidity (**{humidity:.0f}% RH**) slows moisture evaporation significantly.\n"
                    f"• **Optimal Drying Window**: 11:00 AM to 3:30 PM under direct sunlight.\n\n"
                    f"💡 **Actionable Solution**: Space clothes widely on the clothesline and retrieve them before 4:30 PM to avoid evening dew absorption."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 RECOMMENDED (EXCELLENT DRYING)"
            score = 95.0
            steps = [
                "Hang laundry outdoors between 9:30 AM and 4:00 PM.",
                f"Ambient temperature ({temp:.1f}°C) and dry air will dry cottons in ~2 hours.",
                "Utilize light breeze for rapid natural freshening."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ! आज {location} में कपड़े बाहर सुखाने के लिए बहुत बढ़िया मौसम है।**\n\n"
                    f"• **मौसम अनुकूलता**: धूप खिली रहेगी, तापमान **{temp:.1f}°C** और हवा में नमी केवल **{humidity:.0f}%** है।\n"
                    f"• **सुखाने का समय**: सुबह 9:30 बजे से शाम 4:00 बजे तक। सामान्य सूती कपड़े 2 से 3 घंटे में पूरी तरह सूख जाएंगे।\n\n"
                    f"💡 **सलाह**: कपड़ों को खुले तार पर फैलाएं, प्राकृतिक धूप और हल्की हवा से कपड़े तरोताजा सूखेंगे।"
                )
            else:
                text = (
                    f"🟢 **Yes! Today is an optimal day to dry laundry outdoors in {location}.**\n\n"
                    f"• **Drying Profile**: Clear/partly cloudy sky, warm ambient temperature (**{temp:.1f}°C**), and low moisture (**{humidity:.0f}% RH**).\n"
                    f"• **Expected Drying Time**: Standard cottons will dry within 2 to 3 hours.\n\n"
                    f"💡 **Actionable Solution**: Hang garments between 9:30 AM and 4:00 PM for maximum solar exposure and natural UV sanitization."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 2. CAR & VEHICLE WASH ====================
    elif intent == "CAR_WASH":
        if rain_next_48h > 1.0:
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 POSTPONE CAR WASH"
            score = 25.0
            steps = [
                f"Hold off washing: {rain_next_48h:.1f} mm rain predicted within 48 hours.",
                "Road mud splashes and rainwater droplets will immediately spot clean paintwork.",
                "Use a dry microfiber duster for quick windshield cleaning instead."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **नहीं, आज {location} में कार या गाड़ी धोने की सलाह नहीं दी जाती।**\n\n"
                    f"• **कारण**: आगामी 48 घंटों में **{rain_next_48h:.1f} मिमी बारिश** ({rain_prob:.0f}% संभावना) का पूर्वानुमान है।\n"
                    f"• कार धोने के तुरंत बाद सड़क के कीचड़ और बारिश के छींटों से गाड़ी वापस गंदी हो जाएगी और आपका समय व पानी व्यर्थ होगा।\n\n"
                    f"💡 **समाधान**: धुलाई स्थगित रखें। केवल विंडशील्ड और शीशे सूखे माइक्रोफाइबर कपड़े से साफ कर लें।"
                )
            else:
                text = (
                    f"🔴 **No, postpone washing your car or vehicle in {location} today.**\n\n"
                    f"• **Reason**: Numerical forecast indicates **{rain_next_48h:.1f} mm precipitation** over the next 24–48 hours ({rain_prob:.0f}% likelihood).\n"
                    f"• Road spray, dirty puddle runoff, and rain droplet spotting will soil freshly detailed paintwork immediately.\n\n"
                    f"💡 **Actionable Solution**: Delay a full wash until dry conditions stabilize. Use a quick dry microfiber towel for windshield visibility."
                )
        elif wind_gust > 32.0:
            verdict = "CAUTION"
            badge = "🟡 CAUTION (GUSTY DUST)"
            score = 60.0
            steps = [
                f"Wash in a sheltered garage: wind gusts reach {wind_gust:.1f} km/h.",
                "Dry immediately with a chamois or microfiber cloth to avoid dust adhesion.",
                "Avoid applying liquid wax in open windy areas."
            ]
            if lang == "hi":
                text = (
                    f"🟡 **सतर्कता: कार धो सकते हैं, लेकिन ढके हुए स्थान पर धोएं।**\n\n"
                    f"• **मौसम स्थिति**: बारिश की संभावना नहीं है, परंतु तेज हवा के झोंके (**{wind_gust:.1f} किमी/घंटा**) धूल उड़ा सकते हैं।\n"
                    f"💡 **सलाह**: कार धोने के बाद तुरंत सूखे कपड़े से पोंछ लें ताकि गीली सतह पर उड़ती धूल न चिपके।"
                )
            else:
                text = (
                    f"🟡 **Conditional: You can wash, but do so in a sheltered or shaded area.**\n\n"
                    f"• **Atmospheric Condition**: Zero rain expected, but elevated wind gusts (**{wind_gust:.1f} km/h**) will kick up airborne road dust.\n"
                    f"💡 **Actionable Solution**: Towel-dry the vehicle immediately after rinsing to prevent dust particles adhering to wet panels."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 RECOMMENDED (GREAT WASH DAY)"
            score = 95.0
            steps = [
                "Proceed with full exterior wash and detailing.",
                "Zero precipitation expected over the next 3 days.",
                "Wash in the early morning or evening shade to prevent water spot rings."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ! आज {location} में कार या बाइक धोने के लिए उत्तम दिन है।**\n\n"
                    f"• **मौसम स्थिति**: आगामी 3 दिनों तक बारिश की कोई संभावना नहीं है ({three_day_rain:.1f} मिमी कुल वर्षा), आसमान साफ रहेगा।\n"
                    f"• आपकी गाड़ी कई दिनों तक साफ और चमकदार रहेगी।\n\n"
                    f"💡 **सलाह**: तेज धूप में पानी के निशान (water spots) से बचने के लिए सुबह या शाम के समय छाया में धुलाई करें।"
                )
            else:
                text = (
                    f"🟢 **Yes! Today is a great day to wash your car or vehicle in {location}.**\n\n"
                    f"• **Favorable Outlook**: Zero precipitation forecast over the next 3 days (total: {three_day_rain:.1f} mm). Roads will remain completely dry.\n"
                    f"• Your wash and wax will last cleanly for the week.\n\n"
                    f"💡 **Actionable Solution**: Wash during early morning or shaded late afternoon to prevent soap residue and mineral water spotting from harsh sun."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 3. OUTDOOR SPORTS & RECREATION ====================
    elif intent == "OUTDOOR_SPORTS":
        if rain_today > 2.0 or (rain_tomorrow > 3.0 and rain_prob > 65):
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 OUTDOOR PLAY NOT RECOMMENDED"
            score = 25.0
            steps = [
                "Avoid turf or dirt fields due to waterlogging and slippage injuries.",
                "Switch to an indoor gymnasium or badminton court.",
                "Monitor radar for sudden convective showers."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **आज {location} में क्रिकेट, फुटबॉल या आउटडोर खेल खेलना सुरक्षित नहीं है।**\n\n"
                    f"• **कारण**: बारिश (**{rain_today:.1f} मिमी**, {rain_prob:.0f}% संभावना) से मैदान गीला व फिसलन भरा रहेगा, जिससे चोट लगने का जोखिम है।\n"
                    f"💡 **समाधान**: आउटडोर मैच स्थगित करें या इनडोर खेलों (बैडमिंटन, जिम) का विकल्प चुनें।"
                )
            else:
                text = (
                    f"🔴 **Outdoor sports or running are not recommended in {location} today.**\n\n"
                    f"• **Hazards**: Precipitation ({rain_today:.1f} mm, {rain_prob:.0f}% probability) creates waterlogged turf, mud pitches, and severe traction slippage.\n"
                    f"💡 **Actionable Solution**: Move athletic sessions to an indoor sports complex or gym."
                )
        elif apparent_temp >= 38.0:
            verdict = "CAUTION"
            badge = "🟡 EARLY MORNING ONLY (HEAT CAUTION)"
            score = 60.0
            steps = [
                "Play strictly between 6:00 AM and 8:30 AM before temperatures surge.",
                f"Afternoon heat index reaches {apparent_temp:.1f}°C (risk of heat exhaustion).",
                "Carry electrolytes and take 5-minute hydration breaks every 20 minutes."
            ]
            if lang == "hi":
                text = (
                    f"🟡 **सतर्कता: केवल सुबह 6:00 से 8:30 बजे तक ही खेलें (गर्मी का जोखिम)।**\n\n"
                    f"• **मौसम स्थिति**: दोपहर में महसूस होने वाला तापमान (Heat Index) **{apparent_temp:.1f}°C** तक पहुंचेगा।\n"
                    f"• दोपहर 11:00 बजे से 4:00 बजे के बीच धूप में तेज दौड़ने या खेलने से लू (Heatstroke) और डिहाइड्रेशन हो सकता है।\n\n"
                    f"💡 **सलाह**: खेल सत्र सुबह जल्दी पूरा करें और पर्याप्त पानी व ओआरएस साथ रखें।"
                )
            else:
                text = (
                    f"🟡 **Caution: Play strictly during early morning hours (6:00 AM – 8:30 AM).**\n\n"
                    f"• **Thermal Stress**: The afternoon Heat Index spikes to **{apparent_temp:.1f}°C**, introducing high risk of dehydration and heat cramps.\n"
                    f"💡 **Actionable Solution**: Complete all intense cardiovascular running or cricket matches before 9:00 AM. Maintain regular electrolyte hydration."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 RECOMMENDED (OPTIMAL CONDITIONS)"
            score = 92.0
            steps = [
                "Ideal ground and atmospheric conditions for cricket, football, or jogging.",
                "Favorable time window: 6:30 AM – 9:30 AM or 4:30 PM – 6:30 PM.",
                f"Mild breeze ({wind_gust:.1f} km/h) and comfortable air."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ! आज {location} में क्रिकेट, दौड़ या आउटडोर खेल के लिए शानदार मौसम है।**\n\n"
                    f"• **मैदान व मौसम**: मैदान सूखा है, तापमान **{temp:.1f}°C** सामान्य है और बारिश का कोई खतरा नहीं है।\n"
                    f"• **सर्वश्रेष्ठ समय**: सुबह 6:30 से 9:30 बजे या शाम 4:30 से 6:30 बजे।\n\n"
                    f"💡 **सलाह**: खेल का आनंद लें और सामान्य मात्रा में पानी पीते रहें।"
                )
            else:
                text = (
                    f"🟢 **Yes! Weather conditions are ideal for outdoor sports and running in {location}.**\n\n"
                    f"• **Field Conditions**: Pitches and outfields are firm and dry, temperature is **{temp:.1f}°C**, and zero precipitation is expected.\n"
                    f"• **Recommended Window**: 6:30 AM to 9:30 AM or 4:30 PM to 6:30 PM.\n\n"
                    f"💡 **Actionable Solution**: Perfect day for team sports or long-distance cycling/jogging."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 3b. MORNING & EVENING WALK ====================
    elif intent == "MORNING_WALK":
        heat_warning = apparent_temp >= 36.0
        rain_warning = rain_today > 1.0 or rain_prob_today > 50.0
        if rain_warning:
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 AVOID OUTDOOR WALK (WET/RAIN)"
            score = 30.0
            steps = [
                f"Rain probability is {rain_prob_today:.0f}% with active precipitation ({rain_today:.1f} mm).",
                "Indoor walking or treadmill exercise is recommended.",
                "Slippery footpaths increase risk of fall injuries."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **आज {location} में बाहर टहलने (Morning Walk) की सलाह नहीं है।**\n\n"
                    f"• **कारण**: बारिश (**{rain_today:.1f} मिमी**, {rain_prob_today:.0f}% संभावना) से रास्ते गीले व फिसलन भरे रहेंगे।\n"
                    f"💡 **समाधान**: घर के अंदर या बालकनी में हल्की चहलकदमी करें।"
                )
            else:
                text = (
                    f"🔴 **Outdoor walk is not recommended in {location} today.**\n\n"
                    f"• **Hazards**: Active precipitation ({rain_today:.1f} mm, {rain_prob_today:.0f}% probability) makes pavements wet and slick.\n"
                    f"💡 **Actionable Solution**: Switch to indoor walking or light indoor exercise."
                )
        elif heat_warning:
            verdict = "CAUTION"
            badge = "🟡 WALK STRICTLY BEFORE 8:00 AM"
            score = 60.0
            steps = [
                "Walk strictly between 5:30 AM and 7:30 AM before heat builds up.",
                f"Afternoon feels-like temperature exceeds {apparent_temp:.1f}°C.",
                "Carry a water bottle for continuous hydration."
            ]
            if lang == "hi":
                text = (
                    f"🟡 **सतर्कता: केवल सुबह 5:30 से 7:30 बजे के बीच ही टहलें।**\n\n"
                    f"• **कारण**: दिन में तापमान **{temp:.1f}°C** (Heat Index: {apparent_temp:.1f}°C) तक पहुंचेगा।\n"
                    f"💡 **सलाह**: सुबह जल्दी टहलें और पर्याप्त पानी पिएं।"
                )
            else:
                text = (
                    f"🟡 **Caution: Complete walks strictly between 5:30 AM and 7:30 AM.**\n\n"
                    f"• **Thermal Stress**: Afternoon feels-like temperature reaches **{apparent_temp:.1f}°C**.\n"
                    f"💡 **Actionable Solution**: Walk in shaded parks during dawn hours and hydrate actively."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 IDEAL WEATHER FOR WALKING"
            score = 95.0
            steps = [
                "Ideal fresh air conditions for morning or evening walk.",
                "Best window: 6:00 AM – 8:30 AM or 5:30 PM – 7:30 PM.",
                f"Comfortable ambient temperature ({temp:.1f}°C) and calm breeze."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ! {location} में मॉर्निंग वॉक और टहलने के लिए बहुत ही सुखद मौसम है।**\n\n"
                    f"• **मौसम स्थिति**: तापमान **{temp:.1f}°C** सामान्य है, हवा शांत है और बारिश का कोई खतरा नहीं है ({rain_prob_today:.0f}% संभावना)।\n"
                    f"• **सर्वश्रेष्ठ समय**: सुबह 6:00 से 8:30 बजे या शाम 5:30 से 7:30 बजे।\n\n"
                    f"💡 **सलाह**: ताजी हवा का आनंद लें और सामान्य वॉक करें।"
                )
            else:
                text = (
                    f"🟢 **Yes! Weather conditions are ideal for morning/evening walks in {location}.**\n\n"
                    f"• **Comfort Profile**: Ambient temperature is **{temp:.1f}°C** with calm air and zero rain disruption ({rain_prob_today:.0f}% prob).\n"
                    f"• **Best Time Window**: 6:00 AM to 8:30 AM or 5:30 PM to 7:30 PM.\n\n"
                    f"💡 **Actionable Solution**: Excellent time for cardiovascular walking or jogging."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 4. OUTDOOR EVENTS & WEDDINGS ====================
    elif intent == "OUTDOOR_EVENT":
        if three_day_rain > 10.0 or wind_gust > 38.0:
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 HIGH WEATHER RISK FOR OPEN-AIR EVENT"
            score = 25.0
            steps = [
                f"Shift function to an enclosed banquet hall or waterproof pavilion.",
                f"Wind gusts up to {wind_gust:.1f} km/h endanger shamiana and tent pole stability.",
                f"Projected {three_day_rain:.1f} mm rainfall will saturate lawn and parking turf."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **सावधानी: {location} में खुले मैदान में शादी या कार्यक्रम आयोजित करने में बड़ा जोखिम है।**\n\n"
                    f"• **मौसम जोखिम**: आगामी दिनों में **{three_day_rain:.1f} मिमी कुल वर्षा** और **{wind_gust:.1f} किमी/घंटे की तेज हवा के झोंके** संभावित हैं।\n"
                    f"• खुले टेंट/शामियाना उखड़ने और लॉन में कीचड़/जलभराव होने का खतरा है।\n\n"
                    f"💡 **समाधान**: कार्यक्रम को पक्के वॉटरप्रूफ बैंक्वेट हॉल में स्थानांतरित करें या वाटरप्रूफ जर्मन हैंगर टेंट का उपयोग करें।"
                )
            else:
                text = (
                    f"🔴 **High Weather Risk: Open-air events or lawn weddings in {location} face significant hazards.**\n\n"
                    f"• **Hazards**: Cumulative rainfall of **{three_day_rain:.1f} mm** and peak wind gusts of **{wind_gust:.1f} km/h** threaten temporary marquee structures and generate sodden turf.\n"
                    f"💡 **Actionable Solution**: Transition the event to an indoor banquet venue or install reinforced German pagoda waterproof staging."
                )
        elif three_day_rain > 2.0 or wind_gust > 26.0:
            verdict = "CAUTION"
            badge = "🟡 CONDITIONAL (RAIN CONTINGENCY REQUIRED)"
            score = 65.0
            steps = [
                "Install waterproof overhead coverings and raised wooden flooring.",
                "Keep a covered backup area ready for dining and electrical consoles.",
                "Firmly anchor all canopy guy-ropes."
            ]
            if lang == "hi":
                text = (
                    f"🟡 **शर्तों के साथ: कार्यक्रम हो सकता है, लेकिन वॉटरप्रूफ बैकअप तैयार रखें।**\n\n"
                    f"• **मौसम स्थिति**: हल्की बूंदाबांदी ({three_day_rain:.1f} मिमी) और {wind_gust:.1f} किमी/घंटे की हवा संभावित है।\n"
                    f"💡 **सलाह**: स्टेज और भोजन क्षेत्र पर वाटरप्रूफ शामियाना लगाएं और बिजली के उपकरणों को जमीन से ऊपर रखें।"
                )
            else:
                text = (
                    f"🟡 **Conditional: Outdoor function feasible with active rain contingency.**\n\n"
                    f"• **Outlook**: Spotty light showers ({three_day_rain:.1f} mm) and moderate breezes ({wind_gust:.1f} km/h) possible.\n"
                    f"💡 **Actionable Solution**: Have a waterproof canopy shelter on standby and elevate sensitive sound/lighting equipment."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 RECOMMENDED (OPTIMAL EVENT WEATHER)"
            score = 95.0
            steps = [
                "Excellent open-air weather with dry ground and clear skies.",
                f"Pleasant evening temperature, wind gusts under {wind_gust:.1f} km/h.",
                "Standard outdoor setup permitted without weather disruptions."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ! {location} में खुले मैदान में कार्यक्रम या समारोह के लिए उत्तम मौसम है।**\n\n"
                    f"• **मौसम स्थिति**: बारिश की संभावना शून्य है, हवा शांत ({wind_gust:.1f} किमी/घंटा) और शाम का तापमान अत्यंत सुखद रहेगा।\n"
                    f"💡 **सलाह**: आप बिना किसी मौसम रुकावट के ओपन-एयर लॉन और शामियाना कार्यक्रम आयोजित कर सकते हैं।"
                )
            else:
                text = (
                    f"🟢 **Yes! Weather conditions in {location} are ideal for outdoor functions and weddings.**\n\n"
                    f"• **Atmospheric Profile**: Completely dry trajectory, calm wind gusts ({wind_gust:.1f} km/h), and clear skies ensure an uninterrupted outdoor gathering.\n"
                    f"💡 **Actionable Solution**: Open-air lawn arrangements, floral decor, and dining can proceed without weather disruption."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 5. AGRICULTURE: HARVESTING ====================
    elif intent == "HARVESTING":
        if three_day_rain > 2.0 or (f1 and f1.precipitation_sum > 1.5):
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 SUSPEND CROP HARVESTING"
            score = 20.0
            steps = [
                f"Hold harvesting of {crop_name}: rain predicted ({three_day_rain:.1f} mm in next 72h).",
                "Cut grain exposed to rain will develop mold, blackening, and premature germination.",
                "Ensure harvested heaps already in field are securely covered with tarpaulins."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **नहीं, {location} में {crop_name} की कटाई अभी तुरंत रोक दें!**\n\n"
                    f"• **कारण**: आगामी 72 घंटों में **{three_day_rain:.1f} मिमी वर्षा** का पूर्वानुमान है।\n"
                    f"• कटी हुई फसल भीगने से दाने काले पड़ जाएंगे, फफूंद (Mold) लगेगी और अंकुरण हो जाएगा, जिससे भारी आर्थिक नुकसान होगा।\n\n"
                    f"💡 **सलाह**: कटाई टालें और जो फसल पहले से खलिहान में कटी पड़ी है उसे तिरपाल से अच्छी तरह ढक दें।"
                )
            else:
                text = (
                    f"🔴 **No, immediately suspend harvesting {crop_name} in {location}.**\n\n"
                    f"• **Risk Analysis**: Numerical models forecast **{three_day_rain:.1f} mm cumulative rainfall** over the next 72 hours.\n"
                    f"• Wet harvesting triggers grain discoloration, fungal mold (Aspergillus), and premature in-ear germination.\n\n"
                    f"💡 **Actionable Solution**: Postpone sickle or combine harvesting. Secure previously reaped field bundles under heavy waterproof tarpaulins."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 PROCEED WITH HARVESTING"
            score = 92.0
            steps = [
                f"Favorable 3-day dry window for harvesting {crop_name}.",
                "Thresh and dry grain in field until moisture drops below 12-14%.",
                "Store dried produce in elevated, moisture-proof godowns."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ, {location} में {crop_name} की कटाई के लिए मौसम बिल्कुल अनुकूल है।**\n\n"
                    f"• **मौसम स्थिति**: आगामी 3 दिनों तक मौसम शुष्क रहेगा (बारिश: {three_day_rain:.1f} मिमी), खिली धूप से फसल अच्छी तरह सूखेगी।\n"
                    f"• दाने में सुरक्षित भंडारण के लिए नमी 12-14% तक आसानी से आ जाएगी।\n\n"
                    f"💡 **सलाह**: कटाई और गहाई (Threshing) का कार्य तेजी से पूरा करें और अनाज को सूखे सुरक्षित स्थान पर रखें।"
                )
            else:
                text = (
                    f"🟢 **Yes, conditions in {location} are favorable for harvesting {crop_name}.**\n\n"
                    f"• **Harvest Window**: Continuous dry weather across the next 3 days (precipitation: {three_day_rain:.1f} mm) facilitates smooth combine harvesting and sun-drying.\n"
                    f"• Ensures safe grain moisture below the 12–14% threshold for commercial storage.\n\n"
                    f"💡 **Actionable Solution**: Proceed with harvesting and threshing during peak daylight hours."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 6. AGRICULTURE: SPRAYING PESTICIDES ====================
    elif intent == "SPRAY_PESTICIDE":
        can_spray = rain_tomorrow < 1.5 and wind_gust < 20.0
        if can_spray:
            verdict = "RECOMMENDED"
            badge = "🟢 SAFE FOR CHEMICAL SPRAYING"
            score = 90.0
            steps = [
                "Conduct foliar spray between 7:30 AM and 11:00 AM after morning dew evaporates.",
                f"Calm wind ({wind_gust:.1f} km/h) prevents chemical drift to adjacent fields.",
                f"Negligible rain ({rain_tomorrow:.1f} mm) ensures 4-6 hours rainfast absorption."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ, {location} में कल कीटनाशक या दवा का छिड़काव करना सुरक्षित है।**\n\n"
                    f"• **मौसम स्थिति**: बारिश की संभावना केवल {rain_prob:.0f}% है (अनुमानित वर्षा: {rain_tomorrow:.1f} मिमी)।\n"
                    f"• **हवा की गति**: {wind_gust:.1f} किमी/घंटा (हवा शांत है, दवा उड़ने का खतरा नहीं है)।\n\n"
                    f"💡 **सलाह**: सुबह 7:30 से 11:00 बजे के बीच छिड़काव करें जब ओस सूख जाए।"
                )
            else:
                text = (
                    f"🟢 **Yes, it is safe to spray pesticide/fungicide in {location} tomorrow.**\n\n"
                    f"• **Rainfall Risk**: Negligible ({rain_tomorrow:.1f} mm, {rain_prob:.0f}% likelihood).\n"
                    f"• **Wind Drift**: Calm at {wind_gust:.1f} km/h (within safe < 20 km/h threshold).\n\n"
                    f"💡 **Actionable Solution**: Spray between 7:30 AM and 11:00 AM to allow 4–6 hours of rainfast chemical absorption."
                )
        else:
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 AVOID SPRAYING (WASHOFF RISK)"
            score = 25.0
            steps = [
                f"Postpone spraying: rain forecast ({rain_tomorrow:.1f} mm, {rain_prob:.0f}% chance).",
                f"Wind gusts ({wind_gust:.1f} km/h) will blow spray droplets away from target leaves.",
                "Chemical will be washed off, wasting inputs and polluting soil runoff."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **नहीं, {location} में अभी कीटनाशक का छिड़काव न करें।**\n\n"
                    f"• **कारण**: कल **{rain_tomorrow:.1f} मिमी वर्षा** ({rain_prob:.0f}% संभावना) और **{wind_gust:.1f} किमी/घंटा** हवा का अनुमान है।\n"
                    f"• दवा बारिश में धुल जाएगी और तेज हवा से उड़कर व्यर्थ हो जाएगी।\n\n"
                    f"💡 **सलाह**: मौसम साफ होने तक छिड़काव स्थगित रखें।"
                )
            else:
                text = (
                    f"🔴 **No, avoid chemical spraying in {location} over the next 24-48 hours.**\n\n"
                    f"• **Reason**: Forecast anticipates {rain_tomorrow:.1f} mm rainfall ({rain_prob:.0f}% likelihood) with gusts up to {wind_gust:.1f} km/h.\n"
                    f"• Rain will wash off active ingredients and wind will cause severe chemical drift.\n\n"
                    f"💡 **Actionable Solution**: Hold applications until clear, dry conditions return."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 7b. AGRICULTURE: CROP RECOMMENDATION & SEASONAL SUITABILITY ====================
    elif intent == "CROP_RECOMMENDATION":
        season_code, season_name_en, season_name_hi, in_season_crops, off_season_crops = get_current_agricultural_season()
        in_crops_str = ", ".join(in_season_crops)
        off_crops_str = ", ".join(off_season_crops)
        verdict = "RECOMMENDED"
        badge = f"🌾 {season_code} SEASON CROP ADVISORY"
        score = 92.0
        steps = [
            f"Active Agro-Season: {season_name_en}.",
            f"Favorable In-Season Crops: {in_crops_str}.",
            f"Off-Season Crops (Do NOT sow now): {off_crops_str}."
        ]
        if lang == "hi":
            text = (
                f"🌾 **{location} के लिए मौसमी फसल चयन परामर्श ({season_name_hi}):**\n\n"
                f"📌 **एक मौसम - एक फसल नियम (Seasonal Cropping Rule)**:\n"
                f"भारतीय कृषि विज्ञान (ICAR) के अनुसार एक निश्चित मौसम में केवल उसी ऋतु के अनुकूल फसलें ही उग सकती हैं। "
                f"वर्तमान में **{season_name_hi}** चल रहा है। इस समय रबी (जैसे गेहूं/सरसों) और खरीफ (जैसे धान) एक साथ कभी नहीं उग सकते।\n\n"
                f"✅ **इस मौसम के लिए अनुकूल फसलें (In-Season & Favorable):**\n"
                f"• **{in_crops_str}**\n"
                f"• तापमान ({f1.temperature_min:.1f}°C - {f1.temperature_max:.1f}°C) और मौसमी वर्षा इन फसलों के लिए उपयुक्त है।\n\n"
                f"⛔ **बेमौसम फसलें (Off-Season - अभी न बोएं):**\n"
                f"• **{off_crops_str}** — ये फसलें अभी अधिक तापमान व बारिश में सड़ जाएंगी। गेहूं/सरसों की बुवाई अक्टूबर अंत या नवंबर (रबी मौसम) में ही करें।\n\n"
                f"💡 **सलाह**: खेत में केवल **{in_season_crops[0]}** या **{in_season_crops[1] if len(in_season_crops) > 1 else 'मौसमी फसल'}** की ही बुवाई या तैयारी करें।"
            )
        else:
            text = (
                f"🌾 **Seasonal Crop Recommendation for {location} ({season_name_en}):**\n\n"
                f"📌 **Single-Season Cropping Principle**:\n"
                f"In Indian agriculture, crops strictly follow distinct photoperiod and thermal seasons. "
                f"In one season, only season-adapted crops will grow. You cannot grow a Rabi crop (like Wheat) and a Kharif crop (like Rice) simultaneously.\n\n"
                f"✅ **Favorable In-Season Crops (Active Now):**\n"
                f"• **{in_crops_str}**\n"
                f"• Current thermal window ({f1.temperature_min:.1f}°C - {f1.temperature_max:.1f}°C) and moisture regime match these crops.\n\n"
                f"⛔ **Off-Season Crops (Do NOT sow now):**\n"
                f"• **{off_crops_str}** — Out-of-season crops will suffer thermal shock, damping-off, and seed rot. Wheat and mustard must be sown in late October–November once winter sets in.\n\n"
                f"💡 **Actionable Solution**: Choose **{in_season_crops[0]}** or **{in_season_crops[1] if len(in_season_crops) > 1 else in_crops_str}** for current field operations."
            )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps, "current_season": season_name_en, "seasonal_crops_recommended": in_season_crops})
        return text, meta

    # ==================== 7. AGRICULTURE: SOWING ====================
    elif intent == "SOWING":
        season_code, season_name_en, season_name_hi, in_season_crops, off_season_crops = get_current_agricultural_season()
        crop_target = crop_info.get("crop", "").title()
        is_off_season = False
        if crop_target in CROP_VALID_SEASONS:
            allowed = CROP_VALID_SEASONS.get(crop_target, [])
            if season_code not in allowed and "PERENNIAL" not in allowed:
                is_off_season = True

        if is_off_season:
            in_crops_str = ", ".join(in_season_crops)
            verdict = "NOT_RECOMMENDED"
            badge = f"🔴 NOT RECOMMENDED (OFF-SEASON CROP)"
            score = 18.0
            steps = [
                f"{crop_target} is an off-season crop during {season_name_en}.",
                f"In one season, only season-appropriate crops will grow. Do NOT sow {crop_target} now.",
                f"Sow recommended in-season crops: {in_crops_str}."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **नहीं, अभी {location} में {crop_target} की बुवाई न करें (बेमौसम फसल)।**\n\n"
                    f"• **ऋतु असंगति**: वर्तमान में **{season_name_hi}** चल रहा है, जबकि **{crop_target}** एक शीतकालीन/विपरीत ऋतु की फसल है।\n"
                    f"• **जोखिम**: अभी {crop_target} बोने से अधिक तापमान ({f1.temperature_max:.1f}°C) और मौसमी वर्षा के कारण बीज अंकुरित नहीं होंगे और सड़ जाएंगे।\n"
                    f"• **वर्तमान मौसम की उपयुक्त फसलें**: {in_crops_str}।\n\n"
                    f"💡 **सलाह**: इस समय केवल {in_crops_str} की बुवाई करें। {crop_target} की बुवाई अक्टूबर अंत या नवंबर में ठंड आने पर करें।"
                )
            else:
                text = (
                    f"🔴 **No, do not sow {crop_target} in {location} right now (Off-Season Crop).**\n\n"
                    f"• **Season Mismatch**: Current period is **{season_name_en}**, while **{crop_target}** is adapted for a different season (e.g. Rabi winter).\n"
                    f"• **Biological Risk**: In one season, only season-adapted crops will grow. Sowing {crop_target} now will cause thermal shock ({f1.temperature_max:.1f}°C max) and fungal seed rotting.\n"
                    f"• **Favorable Crops for Current Season**: {in_crops_str}.\n\n"
                    f"💡 **Actionable Solution**: Grow in-season crops like {in_season_crops[0]} now. Hold off on {crop_target} until late October–November."
                )
            meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps, "current_season": season_name_en, "seasonal_crops_recommended": in_season_crops})
            return text, meta

        has_moisture = three_day_rain > 8.0 or humidity > 65.0
        verdict = "RECOMMENDED" if has_moisture else "CAUTION"
        badge = "🟢 SOWING CONDITIONS FAVORABLE" if has_moisture else "🟡 PRE-SOWING IRRIGATION NEEDED"
        score = 88.0 if has_moisture else 60.0
        steps = [
            f"Target crop: {crop_name}. In-Season ({season_name_en}).",
            "Test seed germination rate and apply bio-fungicide seed treatment before drilling.",
            "Apply pre-sowing irrigation if topsoil is dry."
        ]
        if lang == "hi":
            text = (
                f"🌱 **{location} में {crop_name} की बुवाई संबंधी सलाह ({season_name_hi}):**\n\n"
                f"• **ऋतु अनुकूलता**: {crop_name} वर्तमान मौसम के पूर्णतः अनुकूल है।\n"
                f"• **तापमान**: वर्तमान {temp:.1f}°C, आगामी न्यूनतम {f1.temperature_min:.1f}°C / अधिकतम {f1.temperature_max:.1f}°C।\n"
                f"• **3-दिवसीय वर्षा**: {three_day_rain:.1f} मिमी।\n\n"
                f"💡 **सलाह**: {'मिट्टी में पर्याप्त नमी है, बुवाई शुरू की जा सकती है।' if has_moisture else 'मिट्टी में नमी कम है, बुवाई से पहले हल्का पलेवा (Pre-sowing irrigation) अवश्य करें।'}"
            )
        else:
            text = (
                f"🌱 **Sowing Decision for {crop_name} in {location} ({season_name_en}):**\n\n"
                f"• **Seasonal Status**: In-Season & Climate Aligned.\n"
                f"• **Thermal Window**: Night Min {f1.temperature_min:.1f}°C / Day Max {f1.temperature_max:.1f}°C.\n"
                f"• **3-Day Rain Projection**: {three_day_rain:.1f} mm.\n\n"
                f"💡 **Actionable Solution**: {'Soil moisture is optimal for immediate seed drilling.' if has_moisture else 'Subsoil moisture is low; apply pre-sowing irrigation (palewa) before drilling seeds.'}"
            )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps, "current_season": season_name_en, "seasonal_crops_recommended": in_season_crops})
        return text, meta

    # ==================== 8. AGRICULTURE: IRRIGATION ====================
    elif intent == "IRRIGATION":
        needs_irrigation = three_day_rain < 8.0
        verdict = "RECOMMENDED" if needs_irrigation else "NOT_RECOMMENDED"
        badge = "🟢 LIGHT IRRIGATION RECOMMENDED" if needs_irrigation else "🔴 SUSPEND IRRIGATION (RAIN EXPECTED)"
        score = 85.0 if needs_irrigation else 25.0
        steps = [
            "Check root zone soil moisture depth before watering.",
            "Use furrow or drip irrigation during early morning or evening hours." if needs_irrigation else "Allow natural precipitation to saturate root zones without waterlogging."
        ]
        if lang == "hi":
            if needs_irrigation:
                text = (
                    f"💧 **{location} में फसलों की हल्की सिंचाई करें।**\n\n"
                    f"• **कारण**: आगामी 3 दिनों में केवल {three_day_rain:.1f} मिमी हल्की वर्षा संभावित है।\n"
                    f"• मिट्टी की नमी बनाए रखने के लिए शाम के समय हल्की सिंचाई या ड्रिप का प्रयोग करें।"
                )
            else:
                text = (
                    f"🛑 **{location} में आगामी सिंचाई तुरंत स्थगित रखें!**\n\n"
                    f"• **कारण**: आगामी 3 दिनों में कुल **{three_day_rain:.1f} मिमी वर्षा** का पूर्वानुमान है।\n"
                    f"• अतिरिक्त पानी लगाने से खेत में जलभराव होगा और जड़ें सड़ सकती हैं।"
                )
        else:
            if needs_irrigation:
                text = (
                    f"💧 **Light irrigation is recommended in {location}.**\n\n"
                    f"• **Reason**: 3-day projected rainfall is minimal ({three_day_rain:.1f} mm).\n"
                    f"• Apply light furrow or drip irrigation during early morning or late evening."
                )
            else:
                text = (
                    f"🛑 **Suspend scheduled irrigation cycles in {location}!**\n\n"
                    f"• **Reason**: Numerical forecast anticipates **{three_day_rain:.1f} mm cumulative rainfall** over the next 72 hours.\n"
                    f"• Natural rainfall will hydrate crops sufficiently without causing root suffocation."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 8b. AGRICULTURE: FERTILIZER & UREA ====================
    elif intent == "FERTILIZER":
        has_heavy_rain = rain_next_48h > 8.0 or rain_prob > 65.0
        if has_heavy_rain:
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 POSTPONE FERTILIZER / UREA"
            score = 25.0
            steps = [
                f"Rain forecast ({rain_next_48h:.1f} mm) will leach nitrogen beyond root zone.",
                "Surface fertilizer runoff into drains wastes expensive inputs.",
                "Wait until rain front passes and field soil stabilizes."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **नहीं, {location} में अभी {crop_name} में यूरिया या खाद न डालें!**\n\n"
                    f"• **कारण**: आगामी 48 घंटों में **{rain_next_48h:.1f} मिमी वर्षा** ({rain_prob:.0f}% संभावना) का अनुमान है।\n"
                    f"• भारी बारिश से यूरिया बहकर (Leaching/Runoff) नष्ट हो जाएगा और पौधों की जड़ों को लाभ नहीं मिलेगा।\n\n"
                    f"💡 **सलाह**: बारिश रुकने और खेत से अतिरिक्त पानी निकलने के बाद ही खाद का छिड़काव करें।"
                )
            else:
                text = (
                    f"🔴 **No, postpone fertilizer or urea top-dressing for {crop_name} in {location}.**\n\n"
                    f"• **Reason**: Predicted rainfall of **{rain_next_48h:.1f} mm** ({rain_prob:.0f}% probability) triggers severe nutrient leaching and surface runoff.\n"
                    f"• Soluble nitrogen will be washed away, wasting farm inputs.\n\n"
                    f"💡 **Actionable Solution**: Delay broadcasting fertilizer until the rain front passes and topsoil moisture stabilizes."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 FAVORABLE FOR FERTILIZER APPLICATION"
            score = 90.0
            steps = [
                f"Adequate soil moisture with zero heavy downpour risk ({rain_tomorrow:.1f} mm rain).",
                "Apply urea or NPK in the early morning or evening when wind is light.",
                "Incorporate lightly into topsoil for maximum root absorption."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ, {location} में {crop_name} में यूरिया या खाद डालने के लिए मौसम अनुकूल है।**\n\n"
                    f"• **मौसम स्थिति**: आगामी 48 घंटों में भारी बारिश का कोई खतरा नहीं है ({rain_next_48h:.1f} मिमी, केवल {rain_prob:.0f}% संभावना)।\n"
                    f"• हवा शांत है और मिट्टी की नमी खाद को घोलकर जड़ों तक पहुंचाने के लिए पर्याप्त है।\n\n"
                    f"💡 **सलाह**: सुबह या शाम के समय खाद डालें और यदि मिट्टी सूखी हो तो हल्का पानी अवश्य लगाएं।"
                )
            else:
                text = (
                    f"🟢 **Yes, conditions are favorable to apply fertilizer/urea for {crop_name} in {location}.**\n\n"
                    f"• **Favorable Weather**: Negligible runoff hazard ({rain_next_48h:.1f} mm rain, {rain_prob:.0f}% prob). Gentle winds ensure even distribution.\n"
                    f"• Soil conditions allow optimal root uptake.\n\n"
                    f"💡 **Actionable Solution**: Broadcast in early morning or late afternoon for maximum nutrient retention."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 9. CONSTRUCTION & EXTERIOR PAINTING ====================
    elif intent == "CONSTRUCTION_PAINTING":
        if rain_next_48h > 1.0 or humidity > 80.0:
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 POSTPONE PAINTING & SLAB POURING"
            score = 25.0
            steps = [
                f"Postpone exterior painting: humidity is {humidity:.0f}% (threshold: < 80%).",
                f"Rain in next 48h ({rain_next_48h:.1f} mm) will wash off wet latex/acrylic paint coats.",
                "Fresh concrete slab pouring risks surface slurry erosion from rain."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **नहीं, आज {location} में बाहरी दीवारों की पुताई या ल॔टर/कंक्रीट का काम टाल दें।**\n\n"
                    f"• **कारण**: हवा में नमी बहुत अधिक (**{humidity:.0f}% आर्द्रता**) है और आगामी 48 घंटों में बारिश ({rain_next_48h:.1f} मिमी) का खतरा है।\n"
                    f"• पेंट सूख नहीं पाएगा और पानी से बह जाएगा। ताजी कंक्रीट की ऊपरी सतह बारिश से कमजोर हो जाएगी।\n\n"
                    f"💡 **सलाह**: मौसम पूरी तरह शुष्क होने तक बाहरी निर्माण व रंगाई का काम रोक दें।"
                )
            else:
                text = (
                    f"🔴 **No, postpone exterior painting and concrete slab casting in {location} today.**\n\n"
                    f"• **Constraints**: Relative humidity ({humidity:.0f}% RH) exceeds the safe paint curing limit (< 80%), and rain is forecast within 48h ({rain_next_48h:.1f} mm).\n"
                    f"• Exterior coatings will bubble, peel, or wash off before film coalescence.\n\n"
                    f"💡 **Actionable Solution**: Postpone exterior painting and major roof slab concrete work until a guaranteed 48-hour dry window."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 EXCELLENT FOR PAINTING & CONSTRUCTION"
            score = 92.0
            steps = [
                f"Safe dry window: zero rain in next 48 hours, humidity {humidity:.0f}%.",
                "Exterior masonry paint coats will cure solidly within 4 to 6 hours.",
                "Ensure concrete curing water is applied properly under sunshine."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ! आज {location} में बाहरी पेंट, पुताई या कंक्रीट निर्माण के लिए बहुत अच्छा मौसम है।**\n\n"
                    f"• **मौसम स्थिति**: बारिश की कोई संभावना नहीं है, तापमान **{temp:.1f}°C** और आर्द्रता **{humidity:.0f}%** निर्माण कार्य के लिए आदर्श है।\n"
                    f"• पेंट की परतें 4 से 6 घंटे में अच्छी तरह सूखकर मजबूत पकड़ बना लेंगी।\n\n"
                    f"💡 **सलाह**: सुबह 9:00 बजे के बाद पुताई या प्लास्टर का काम शुरू करें।"
                )
            else:
                text = (
                    f"🟢 **Yes! Weather conditions in {location} are favorable for exterior painting and concrete work.**\n\n"
                    f"• **Curing Parameters**: Ambient humidity ({humidity:.0f}% RH) and temperature ({temp:.1f}°C) provide ideal curing dynamics without wash-off hazards.\n"
                    f"• Paint coats will set and cure within 4–6 hours.\n\n"
                    f"💡 **Actionable Solution**: Proceed with exterior masonry coating, plastering, or structural slab casting."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 10. FOG & ROAD VISIBILITY ====================
    elif intent == "FOG_VISIBILITY":
        is_foggy = humidity > 82.0 and curr.wind_speed < 10.0 and dew_depression < 2.5
        if is_foggy:
            verdict = "CAUTION"
            badge = "🟡 DENSE MORNING FOG / LOW VISIBILITY"
            score = 45.0
            steps = [
                "Expect dense radiation fog during early morning hours (4:30 AM – 8:30 AM).",
                "Use low-beam headlights and yellow fog lamps. Do NOT use high beams.",
                "Reduce highway driving speed by 30% and maintain 4x braking distance."
            ]
            if lang == "hi":
                text = (
                    f"🟡 **सावधानी: {location} में सुबह घना कोहरा (Fog) छाए रहने की संभावना है।**\n\n"
                    f"• **कारण**: शांत हवा और ओस बिंदु निकट होने (आर्द्रता {humidity:.0f}%) के कारण दृश्यता (Visibility) 150 मीटर से कम हो सकती है।\n"
                    f"💡 **सलाह**: हाईवे पर लो-बीम लाइट व फॉग लैंप का प्रयोग करें और गति धीमी रखें।"
                )
            else:
                text = (
                    f"🟡 **Caution: Dense morning radiation fog expected in {location}.**\n\n"
                    f"• **Meteorological Factors**: Calm wind with dew point convergence (relative humidity: {humidity:.0f}%) creates fog between 4:30 AM and 8:30 AM.\n"
                    f"• Highway visibility may drop below 150–200 meters.\n\n"
                    f"💡 **Actionable Solution**: Use low-beam headlights, reduce cruising speed, and avoid abrupt lane shifts on expressways."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 CLEAR VISIBILITY (SAFE TRANSIT)"
            score = 95.0
            steps = [
                "Unobstructed atmospheric visibility across roadways.",
                f"Dew point depression {dew_depression:.1f}°C keeps fog formation negligible.",
                "Standard highway travel speeds permitted."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **{location} में दृश्यता (Visibility) बिल्कुल साफ है।**\n\n"
                    f"• **स्थिति**: कोहरे या धुंध की कोई संभावना नहीं है। हवा सामान्य गति से चल रही है और सड़क यात्रा पूर्णतः सुगम है।\n"
                    f"💡 **सलाह**: सड़क व रेल यात्रा सामान्य गति से जारी रख सकते हैं।"
                )
            else:
                text = (
                    f"🟢 **Clear visibility prevails across {location}.**\n\n"
                    f"• **Optical Clarity**: Zero fog risk with dew point depression of {dew_depression:.1f}°C. Road and transit corridors are completely unobstructed.\n"
                    f"💡 **Actionable Solution**: Highway driving and flight schedules operate under normal clear conditions."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 11. FLOODS & WATERLOGGING ====================
    elif intent == "FLOOD_WATERLOGGING":
        if rain_today > 35.0 or three_day_rain > 70.0:
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 HIGH WATERLOGGING & LOCAL FLOOD RISK"
            score = 15.0
            steps = [
                f"Severe precipitation: {rain_today:.1f} mm rain today exceeds drainage capacity.",
                "Avoid low-lying underpasses and subterranean basements.",
                "State Disaster Management Emergency Helpline: 1077 / 112."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **चेतावनी: {location} के निचले इलाकों में जलभराव (Waterlogging) का गंभीर खतरा है!**\n\n"
                    f"• **वर्षा स्तर**: आज **{rain_today:.1f} मिमी भारी वर्षा** का अनुमान है, जिससे शहरी नालों पर भारी दबाव पड़ेगा।\n"
                    f"• अंडरपास और निचले रास्तों में पानी भर सकता है।\n\n"
                    f"💡 **सलाह**: जलभराव वाले रास्तों पर गाड़ी न ले जाएं। आवश्यक आपातकालीन संपर्क: 1077 / 112।"
                )
            else:
                text = (
                    f"🔴 **Warning: Elevated waterlogging and drainage inundation hazard in {location}.**\n\n"
                    f"• **Precipitation Stress**: Daily projected rainfall of **{rain_today:.1f} mm** exceeds municipal storm drainage capacity.\n"
                    f"• Low-lying underpasses and natural drainage corridors will experience localized inundation.\n\n"
                    f"💡 **Actionable Solution**: Avoid waterlogged transit underpasses. Emergency helpline: 1077 or 112."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 NO WATERLOGGING THREAT"
            score = 95.0
            steps = [
                "Urban storm runoff within normal baseline limits.",
                f"Projected rain ({rain_today:.1f} mm) is easily handled by municipal drainage.",
                "Roadways and basements are completely safe."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **{location} में जलभराव या बाढ़ का कोई खतरा नहीं है।**\n\n"
                    f"• **स्थिति**: वर्षा सामान्य या शून्य है ({rain_today:.1f} मिमी)। सभी शहरी जल निकासी मार्ग सामान्य रूप से कार्य कर रहे हैं।"
                )
            else:
                text = (
                    f"🟢 **No waterlogging or flood threat in {location}.**\n\n"
                    f"• **Status**: Minimal precipitation ({rain_today:.1f} mm) is well within standard drainage thresholds. Corridors are clear."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 12. HEALTH, HEATWAVE & COLD WAVE ====================
    elif intent == "HEALTH_HEAT_COLD":
        if apparent_temp >= 40.0 or temp >= 42.0:
            verdict = "NOT_RECOMMENDED"
            badge = "🔴 SEVERE HEAT STRESS / LOO RISK"
            score = 25.0
            steps = [
                f"Dangerous heat index: {apparent_temp:.1f}°C feels-like temperature.",
                "Children, pregnant women, and elderly must avoid direct sun between 11:00 AM and 4:30 PM.",
                "Drink 3-4 liters of fluids (ORS, lemon water, chaas)."
            ]
            if lang == "hi":
                text = (
                    f"🔴 **लू व भीषण गर्मी की चेतावनी — {location}:**\n\n"
                    f"• **महसूस होने वाला तापमान (Heat Index)**: **{apparent_temp:.1f}°C** (वास्तविक तापमान: {temp:.1f}°C)।\n"
                    f"• दोपहर 11:00 से 4:30 बजे के बीच लू (Heatstroke) का गंभीर खतरा है। बच्चों व बुजुर्गों को बाहर न जाने दें।\n\n"
                    f"💡 **सलाह**: ओआरएस, नींबू पानी, मट्ठा का सेवन करें और ढीले सूती कपड़े पहनें।"
                )
            else:
                text = (
                    f"🔴 **Extreme Heat Stress & Heatwave Alert — {location}:**\n\n"
                    f"• **Heat Index**: Feels-like temperature reaches **{apparent_temp:.1f}°C** (Ambient: {temp:.1f}°C).\n"
                    f"• High danger of heat exhaustion and sunstroke during midday exposure (11:00 AM – 4:30 PM).\n\n"
                    f"💡 **Actionable Solution**: Keep elderly individuals and young children indoors in cooled rooms. Consume minimum 3–4 liters of fluids with electrolytes."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 COMFORTABLE THERMAL CONDITIONS"
            score = 90.0
            steps = [
                f"Ambient temperature ({temp:.1f}°C) is within comfortable bodily limits.",
                "Standard hydration and outdoor activities permitted."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **{location} में तापमान सामान्य व आरामदायक है।**\n\n"
                    f"• **वर्तमान तापमान**: {temp:.1f}°C (महसूस होने वाला: {apparent_temp:.1f}°C)।\n"
                    f"• लू या शीतलहर का कोई खतरा नहीं है। सामान्य स्वास्थ्य सावधानियों के साथ दैनिक कार्य कर सकते हैं।"
                )
            else:
                text = (
                    f"🟢 **Comfortable thermal conditions in {location}.**\n\n"
                    f"• **Current Profile**: Ambient {temp:.1f}°C (Feels like: {apparent_temp:.1f}°C). Normal diurnal temperature cycle without extreme thermal stress."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 12b. TWO-WHEELER & BIKE COMMUTE ====================
    elif intent == "BIKE_COMMUTE":
        is_foggy = humidity > 82.0 and curr.wind_speed < 10.0 and dew_depression < 2.5
        is_wet = rain_today > 1.5 or rain_prob_today > 60.0 or rain_tomorrow > 2.0
        high_wind = wind_gust > 35.0
        if is_wet or is_foggy or high_wind:
            verdict = "CAUTION"
            badge = "🟡 TWO-WHEELER CAUTION (SLIPPERY/FOG)"
            score = 45.0
            hazard_reasons = []
            if is_wet: hazard_reasons.append(f"Wet road & rain ({rain_today:.1f} mm, {rain_prob_today:.0f}% prob)")
            if is_foggy: hazard_reasons.append("Dense morning fog (visibility < 200m)")
            if high_wind: hazard_reasons.append(f"Strong crosswinds ({wind_gust:.1f} km/h)")
            reasons_str = ", ".join(hazard_reasons)
            steps = [
                f"Transit hazards: {reasons_str}.",
                "Opt for metro, bus, or four-wheeler if available.",
                "If riding: keep speed below 40 km/h, maintain 2x stopping distance, wear clear visor."
            ]
            if lang == "hi":
                text = (
                    f"🟡 **सावधानी: आज/कल {location} में बाइक या स्कूटी से यात्रा करते समय विशेष सतर्कता रखें।**\n\n"
                    f"• **सड़क व मौसम**: {reasons_str}। सड़कों पर फिसलन और दृश्यता कम होने का खतरा है।\n"
                    f"• **सवारी सलाह**: यदि संभव हो तो कार, बस या मेट्रो का विकल्प चुनें।\n\n"
                    f"💡 **सुरक्षा उपाय**: हेलमेट का वाइज़र साफ रखें, अचानक ब्रेक लगाने से बचें और गति धीमी रखें।"
                )
            else:
                text = (
                    f"🟡 **Caution: Exercise extra care when riding a bike or scooter in {location}.**\n\n"
                    f"• **Hazard Profile**: {reasons_str}. Slippery tarmac and reduced visibility increase accident risks.\n"
                    f"• **Recommendation**: Consider public transit or car if distance is long.\n\n"
                    f"💡 **Rider Precautions**: Reduce cruising speed, avoid abrupt hard braking, and use high-visibility gear."
                )
        else:
            verdict = "RECOMMENDED"
            badge = "🟢 SAFE FOR BIKE / TWO-WHEELER"
            score = 95.0
            steps = [
                f"Roads are dry with clear visibility ({curr.weather_description}).",
                f"Mild breeze ({wind_gust:.1f} km/h) and comfortable riding temperature ({temp:.1f}°C).",
                "Wear standard helmet and ride within normal speed limits."
            ]
            if lang == "hi":
                text = (
                    f"🟢 **हाँ! {location} में बाइक या दो-पहिया वाहन से यात्रा के लिए मौसम बिल्कुल साफ व सुरक्षित है।**\n\n"
                    f"• **सड़क स्थिति**: बारिश का कोई खतरा नहीं है ({rain_prob_today:.0f}% संभावना), सड़कें सूखी हैं और दृश्यता स्पष्ट है।\n"
                    f"• तापमान **{temp:.1f}°C** आरामदायक है।\n\n"
                    f"💡 **सलाह**: हेलमेट पहनकर सुरक्षित गति से अपनी यात्रा पूरी करें।"
                )
            else:
                text = (
                    f"🟢 **Yes! Weather and roadway conditions in {location} are ideal for two-wheeler commutes.**\n\n"
                    f"• **Roadway Status**: Completely dry pavement with clear visibility ({curr.weather_description}) and zero rain risk ({rain_prob_today:.0f}% prob).\n"
                    f"• Ambient temperature ({temp:.1f}°C) is pleasant for riding.\n\n"
                    f"💡 **Actionable Solution**: Proceed with daily motorcycle/scooter travel normally."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 13. TRAVEL & HIGHWAY SAFETY ====================
    elif intent == "TRAVEL_SAFETY":
        is_safe = risk["risk_score"] < 50 and wind_gust < 35.0 and rain_today < 15.0
        verdict = "RECOMMENDED" if is_safe else "CAUTION"
        badge = "🟢 SAFE TO TRAVEL" if is_safe else "🟡 TRAVEL CAUTION ADVISED"
        score = 90.0 if is_safe else 45.0
        steps = [
            "Roadways, rail, and flights operating under normal schedules." if is_safe else "Allow 30 minutes extra transit buffer; watch for road ponding.",
            f"Wind gusts {wind_gust:.1f} km/h, AI Risk Score {risk['risk_score']:.0f}/100."
        ]
        if lang == "hi":
            text = (
                f"🚗 **{location} व आसपास यात्रा सुरक्षा रिपोर्ट:**\n\n"
                f"• **यात्रा स्थिति**: {'✅ यात्रा करना सुरक्षित है।' if is_safe else '⚠️ सावधानी बरतें — प्रतिकूल मौसम संभव है।'}\n"
                f"• **दृश्यता व हवा**: हवा के झोंके {wind_gust:.1f} किमी/घंटा, वर्तमान स्थिति: {curr.weather_description}।\n"
                f"• **जोखिम स्कोर**: {risk['risk_score']:.0f}/100 ({risk['risk_level']})।\n\n"
                f"💡 **सलाह**: {'सड़क व रेल यात्रा सामान्य गति से जारी रख सकते हैं।' if is_safe else 'जलभराव वाले अंडरपास से बचें और वाहन की गति नियंत्रित रखें।'}"
            )
        else:
            text = (
                f"🚗 **Travel & Transit Safety for {location}:**\n\n"
                f"• **Status**: {'✅ TRAVEL PERMITTED - Conditions Normal' if is_safe else '⚠️ TRAVEL CAUTION - Adverse Weather Active'}\n"
                f"• **Atmospheric Factors**: Wind gusts at {wind_gust:.1f} km/h, Sky: {curr.weather_description}.\n"
                f"• **AI Impact Index**: {risk['risk_score']:.0f}/100 ({risk['risk_level']}).\n\n"
                f"💡 **Direct Advice**: {'Roadways and rail transit are operating under clear conditions. Standard driving precautions apply.' if is_safe else 'Watch for slippery roads and reduced visibility. Delay non-critical journeys.'}"
            )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 14. RAIN CHECK & UMBRELLA ====================
    elif intent in ["RAIN", "RAIN_CHECK"]:
        q_lower = query.lower()
        asks_today = any(w in q_lower for w in ["today", "aaj", "आज", "tonight", "now", "abhi", "अभी", "आज रात"])
        asks_tomorrow = any(w in q_lower for w in ["tomorrow", "kal", "कल"])
        
        target_rain = rain_today if (asks_today and not asks_tomorrow) else rain_tomorrow
        target_prob = rain_prob_today if (asks_today and not asks_tomorrow) else rain_prob
        target_day_name = "today" if (asks_today and not asks_tomorrow) else ("tomorrow" if asks_tomorrow else "over the next 24-48 hours")
        target_day_name_hi = "आज" if (asks_today and not asks_tomorrow) else ("कल" if asks_tomorrow else "आगामी 24-48 घंटों में")
        target_desc = (f0.weather_description if f0 else curr.weather_description) if (asks_today and not asks_tomorrow) else (f1.weather_description if f1 else "Mainly clear")

        will_rain = target_rain >= 0.5 or target_prob >= 35.0
        verdict = "CAUTION" if will_rain else "RECOMMENDED"
        badge = f"🌧️ RAIN EXPECTED ({target_prob:.0f}%)" if will_rain else f"☀️ DRY CONDITIONS ({target_prob:.0f}%)"
        score = max(10.0, 100.0 - target_prob) if will_rain else min(98.0, 100.0 - target_prob)
        steps = [
            f"Precipitation: {target_rain:.1f} mm with {target_prob:.0f}% probability.",
            "Carry an umbrella or raincoat for outdoor transit." if will_rain else "No umbrella or rain gear required.",
            f"Sky condition: {target_desc}."
        ]
        if lang == "hi":
            if will_rain:
                text = (
                    f"🌧️ **हाँ, {target_day_name_hi} {location} में वर्षा होने की संभावना है।**\n\n"
                    f"• **वर्षा संभावना**: **{target_prob:.0f}%** (अनुमानित मात्रा: **{target_rain:.1f} मिमी**)\n"
                    f"• **मौसम स्थिति**: {target_desc}\n"
                    f"• **तापमान**: अधिकतम {f1.temperature_max:.1f}°C / न्यूनतम {f1.temperature_min:.1f}°C\n\n"
                    f"💡 **सलाह**: बाहर निकलते समय छाता या रेनकोट अवश्य साथ रखें और जलभराव वाले रास्तों से बचें।"
                )
            else:
                text = (
                    f"☀️ **नहीं, {target_day_name_hi} {location} में बारिश की संभावना नहीं है।**\n\n"
                    f"• **वर्षा संभावना**: केवल **{target_prob:.0f}%** (अनुमानित मात्रा: **{target_rain:.1f} मिमी**)\n"
                    f"• **मौसम स्थिति**: आसमान {target_desc} रहेगा, मौसम शुष्क रहेगा।\n"
                    f"• **तापमान**: अधिकतम {f1.temperature_max:.1f}°C / न्यूनतम {f1.temperature_min:.1f}°C\n\n"
                    f"💡 **सलाह**: छाते की आवश्यकता नहीं है, आपकी यात्रा या आउटडोर कार्य बिना रुकावट पूरे होंगे।"
                )
        else:
            if will_rain:
                text = (
                    f"🌧️ **Yes, rain is expected {target_day_name} in {location}.**\n\n"
                    f"• **Precipitation Probability**: **{target_prob:.0f}%** (Estimated volume: **{target_rain:.1f} mm**)\n"
                    f"• **Atmospheric Condition**: {target_desc}\n"
                    f"• **Temperature**: High {f1.temperature_max:.1f}°C / Low {f1.temperature_min:.1f}°C\n\n"
                    f"💡 **Actionable Solution**: Carry an umbrella or keep rain gear accessible; expect wet roadway conditions."
                )
            else:
                text = (
                    f"☀️ **No, rain is not expected {target_day_name} in {location}.**\n\n"
                    f"• **Precipitation Probability**: Minimal at **{target_prob:.0f}%** (Estimated volume: **{target_rain:.1f} mm**)\n"
                    f"• **Atmospheric Condition**: Predominantly dry ({target_desc}).\n"
                    f"• **Temperature**: High {f1.temperature_max:.1f}°C / Low {f1.temperature_min:.1f}°C\n\n"
                    f"💡 **Actionable Solution**: Safe to proceed without rain gear or umbrellas."
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 15. CLOTHING ====================
    elif intent == "CLOTHING":
        t_max = f0.temperature_max if f0 else temp
        t_min = f0.temperature_min if f0 else temp
        needs_umbrella = rain_today > 1.0 or rain_tomorrow > 1.0
        verdict = "INFO"
        badge = "ℹ️ CLOTHING ADVISORY"
        score = 85.0
        steps = [
            "Wear breathable cotton fabrics." if t_max > 28 else "Keep a light layer for evening.",
            "Carry an umbrella." if needs_umbrella else "No rain gear needed."
        ]
        if lang == "hi":
            clothes_tip = "हल्के सूती कपड़े पहनें।" if t_max > 28 else ("हल्की जैकेट की आवश्यकता होगी।" if t_min < 18 else "आरामदायक सामान्य कपड़े पहनें।")
            text = (
                f"👕 **{location} के लिए पहनावे संबंधी सलाह:**\n\n"
                f"• **तापमान**: वर्तमान {temp:.1f}°C (दिन का अधिकतम: {t_max:.1f}°C / रात का न्यूनतम: {t_min:.1f}°C)।\n"
                f"• **पहनावा**: {clothes_tip}\n"
                f"• **छाता / रेनकोट**: {'हाँ, छाता साथ रखें क्योंकि बारिश संभव है।' if needs_umbrella else 'छाते की आवश्यकता नहीं है, मौसम शुष्क रहेगा।'}"
            )
        else:
            clothes_tip = "Light, breathable cotton clothing is recommended." if t_max > 28 else ("A light jacket or sweater is advisable for morning/evening." if t_min < 18 else "Standard comfortable casuals.")
            text = (
                f"👕 **Clothing & Gear Recommendation for {location}:**\n\n"
                f"• **Thermal Profile**: Current {temp:.1f}°C (High: {t_max:.1f}°C, Low: {t_min:.1f}°C).\n"
                f"• **Recommended Attire**: {clothes_tip}\n"
                f"• **Umbrella Needed**: {'Yes, carry an umbrella as rain is forecast.' if needs_umbrella else 'No umbrella required; clear dry skies expected.'}"
            )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 16. MULTI-DAY / GENERAL FORECAST ====================
    elif intent == "GENERAL_FORECAST":
        verdict = "INFO"
        badge = "📅 MULTI-DAY TRAJECTORY"
        score = 88.0
        day_lines = []
        for i, d in enumerate(forecast.forecast_days[:4]):
            day_label = "Today" if i == 0 else ("Tomorrow" if i == 1 else f"+{i} Days")
            day_lines.append(f"• **{day_label} ({d.date})**: {d.temperature_min:.1f}°C – {d.temperature_max:.1f}°C | Rain: {d.precipitation_sum:.1f} mm ({d.weather_description})")
        days_formatted = "\n".join(day_lines)

        steps = [
            f"3-day cumulative rainfall: {three_day_rain:.1f} mm.",
            f"Overall ML Risk Level: {risk['risk_level']} ({risk['risk_score']:.0f}/100)."
        ]
        if lang == "hi":
            text = (
                f"📅 **{location} का 4-दिवसीय मौसम पूर्वानुमान:**\n\n"
                f"{days_formatted}\n\n"
                f"• **एआई मौसम जोखिम स्तर**: {risk['risk_level']} ({risk['risk_score']:.0f}/100)\n"
                f"💡 **सलाह**: {risk.get('recommendation', 'दैनिक गतिविधियों के लिए मौसम अनुकूल है।')}"
            )
        else:
            text = (
                f"📅 **4-Day Weather Outlook for {location}:**\n\n"
                f"{days_formatted}\n\n"
                f"• **AI Impact Score**: **{risk['risk_score']:.0f}/100** ({risk['risk_level']})\n"
                f"💡 **Actionable Advice**: {risk.get('recommendation', 'Weather conditions permit standard daily activities.')}"
            )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 17. GREETING ====================
    elif intent == "GREETING":
        verdict = "INFO"
        badge = "👋 WEATHRE-GPT ASSISTANT"
        score = 100.0
        steps = ["Ask practical weather questions like rain forecast, storm alerts, outdoor sports, or harvesting."]
        if lang == "hi":
            text = (
                f"नमस्ते! मैं WeatherGPT हूँ — आपका AI मौसम व व्यावहारिक निर्णय सहायक।\n\n"
                f"वर्तमान में **{location}** में तापमान **{temp:.1f}°C** है और आसमान **{curr.weather_description}** है।\n\n"
                f"मुझसे मौसम संबंधी निर्णय पूछें, जैसे:\n"
                f"• “क्या आज या कल बारिश होगी?”\n"
                f"• “क्या आंधी-तूफान या बिजली गिरने की चेतावनी है?”\n"
                f"• “क्या कल आउटडोर क्रिकेट खेल सकते हैं?”\n"
                f"• “क्या गेहूं/धान की फसल की कटाई शुरू करें?”"
            )
        else:
            text = (
                f"Hello! I am WeatherGPT — your AI assistant for real-time weather predictions and actionable decisions.\n\n"
                f"Currently in **{location}**, temperature is **{temp:.1f}°C** with **{curr.weather_description}**.\n\n"
                f"Ask me practical questions such as:\n"
                f"• “Will it rain today or tomorrow?”\n"
                f"• “Is there any thunderstorm or lightning alert?”\n"
                f"• “Can we play cricket or sports tomorrow?”\n"
                f"• “Should I harvest crops or spray pesticide?”"
            )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

    # ==================== 18. GENERAL & PERSONA-TAILORED INTELLIGENCE ====================
    else:
        if persona == "FARMER":
            can_spray = rain_tomorrow < 1.5 and wind_gust < 20.0
            needs_irrigation = three_day_rain < 8.0
            verdict = "RECOMMENDED" if can_spray else "CAUTION"
            badge = "🌾 FARMER ADVISORY: FAVORABLE" if can_spray else "🌾 FARMER ADVISORY: RAIN CAUTION"
            score = 88.0 if can_spray else 50.0
            steps = [
                f"3-day cumulative rain: {three_day_rain:.1f} mm, humidity {humidity:.0f}%.",
                f"Spraying safety: {'Safe (wind < 20 km/h, low rain)' if can_spray else 'Postpone (rain or high wind risk)'}.",
                f"Irrigation directive: {'Light irrigation recommended' if needs_irrigation else 'Hold irrigation (rain expected)'}."
            ]
            if lang == "hi":
                text = (
                    f"🌾 **{location} के लिए किसान परामर्श व फसल प्रबंधन रिपोर्ट:**\n\n"
                    f"• **मौसम अवलोकन**: वर्तमान तापमान **{temp:.1f}°C**, आर्द्रता **{humidity:.0f}%**, कल वर्षा: **{rain_tomorrow:.1f} मिमी** ({rain_prob:.0f}% संभावना)।\n"
                    f"• **सिंचाई (Irrigation)**: {'आगामी 3 दिनों में बारिश कम होने के कारण फसलों की हल्की सिंचाई कर सकते हैं।' if needs_irrigation else f'आगामी दिनों में {three_day_rain:.1f} मिमी बारिश का अनुमान है, इसलिए सिंचाई स्थगित रखें।'}\n"
                    f"• **कीटनाशक/दवा छिड़काव (Spraying)**: {'हवा शांत ({wind_gust:.1f} किमी/घंटा) है, सुबह ओस सूखने के बाद छिड़काव सुरक्षित है।' if can_spray else 'बारिश या तेज हवा के कारण छिड़काव टालें ताकि दवा न धुले।'}\n"
                    f"• **फसल कटाई (Harvesting)**: {'अगले 3 दिन शुष्क रहने से कटाई व गहाई का कार्य तेजी से निपटाएं।' if three_day_rain < 3.0 else 'कटी हुई फसल को तिरपाल से ढककर रखें।'}\n\n"
                    f"💡 **मुख्य सलाह**: मिट्टी में नमी की जांच के अनुसार ही पानी लगाएं। खाद का प्रयोग भारी बारिश से पहले न करें।"
                )
            else:
                text = (
                    f"🌾 **Agricultural Intelligence & Crop Advisory for {location}:**\n\n"
                    f"• **Weather Profile**: Current {temp:.1f}°C, Relative Humidity {humidity:.0f}%, Tomorrow Rain: {rain_tomorrow:.1f} mm ({rain_prob:.0f}% probability).\n"
                    f"• **Irrigation Directive**: {'Minimal 3-day rain expected; light irrigation or drip hydration is recommended.' if needs_irrigation else f'Postpone scheduled watering; {three_day_rain:.1f} mm natural rain will hydrate root zones.'}\n"
                    f"• **Foliar Spraying**: {'Winds ({wind_gust:.1f} km/h) and rain risk are low; safe to spray after morning dew.' if can_spray else 'Hold chemical sprays; wash-off and droplet drift hazards present.'}\n"
                    f"• **Harvesting**: {'Favorable 3-day dry window for combine harvesting and sun drying.' if three_day_rain < 3.0 else 'Protect open threshing yards with waterproof tarpaulins.'}\n\n"
                    f"💡 **Key Guidance**: Align nitrogen fertilizer top-dressing with dry ground conditions."
                )
        elif persona == "COMMUTER":
            is_foggy = humidity > 82.0 and curr.wind_speed < 10.0 and dew_depression < 2.5
            road_wet = rain_today > 1.0 or rain_tomorrow > 2.0
            verdict = "CAUTION" if (is_foggy or road_wet) else "RECOMMENDED"
            badge = "🚗 COMMUTE: ADVISORY ACTIVE" if (is_foggy or road_wet) else "🚗 COMMUTE: NORMAL TRANSIT"
            score = 55.0 if (is_foggy or road_wet) else 95.0
            steps = [
                f"Road conditions: {'Wet/Slippery with rain' if road_wet else 'Dry and clear'}.",
                f"Visibility: {'Dense morning fog expected (use low beams)' if is_foggy else 'Clear highway visibility'}.",
                f"Two-wheeler safety: {'Exercise caution or use public transport' if (is_foggy or road_wet) else 'Completely safe for bike commute'}."
            ]
            if lang == "hi":
                text = (
                    f"🚗 **{location} के लिए दैनिक यात्री व हाईवे सुरक्षा रिपोर्ट:**\n\n"
                    f"• **सड़क व दृश्यता**: {'सुबह 5:30 से 8:30 के बीच कोहरा संभव है, दृश्यता कम हो सकती है।' if is_foggy else 'सड़क पर दृश्यता पूर्णतः साफ है।'}\n"
                    f"• **वर्षा व फिसलन**: {'बारिश ({rain_today:.1f} मिमी) के कारण सड़कों पर फिसलन व पानी का जमाव हो सकता है।' if road_wet else 'बारिश का कोई खतरा नहीं है, सड़कें सूखी हैं।'}\n"
                    f"• **सवारी विकल्प**: {'दो-पहिया चालक हेलमेट वाइजर साफ रखें या संभव हो तो मेट्रो/कार का प्रयोग करें।' if (is_foggy or road_wet) else 'बाइक, कार व सार्वजनिक परिवहन सभी सामान्य व सुरक्षित हैं।'}\n"
                    f"• **छाता**: {'हाँ, छाता साथ लेकर निकलें।' if road_wet else 'छाते की आवश्यकता नहीं है।'}\n\n"
                    f"💡 **सलाह**: {'हाईवे पर 25% अतिरिक्त समय लेकर चलें और लो-बीम लाइट का प्रयोग करें।' if (is_foggy or road_wet) else 'यातायात सुगम रहेगा, मानक गति से यात्रा कर सकते हैं।'}"
                )
            else:
                text = (
                    f"🚗 **Commuter & Highway Transit Intelligence for {location}:**\n\n"
                    f"• **Roadway Condition**: {'Slick pavement and spray runoff expected.' if road_wet else 'Firm, completely dry tarmac with normal friction.'}\n"
                    f"• **Atmospheric Visibility**: {'Dense early morning radiation mist/fog possible.' if is_foggy else 'Clear optical clarity across arterial routes.'}\n"
                    f"• **Transit Recommendation**: {'Two-wheeler riders should exercise caution or consider metro/bus.' if (is_foggy or road_wet) else 'Optimal for two-wheeler, car, or cycling commutes.'}\n"
                    f"• **Rain Gear**: {'Carry an umbrella or raincoat.' if road_wet else 'No rain gear needed.'}\n\n"
                    f"💡 **Actionable Solution**: {'Allow 15-20 min buffer for rush hour transit.' if (is_foggy or road_wet) else 'Standard travel schedules apply smoothly.'}"
                )
        elif persona == "EVENT_OUTDOOR":
            outdoor_risk = three_day_rain > 3.0 or wind_gust > 30.0
            verdict = "NOT_RECOMMENDED" if outdoor_risk else "RECOMMENDED"
            badge = "🎪 OUTDOOR: CAUTION/CONTINGENCY" if outdoor_risk else "🎪 OUTDOOR: EXCELLENT CONDITIONS"
            score = 35.0 if outdoor_risk else 92.0
            steps = [
                f"Rain probability: {rain_prob:.0f}%, 3-day volume: {three_day_rain:.1f} mm.",
                f"Wind gusts: {wind_gust:.1f} km/h (tent threshold: 35 km/h).",
                f"Lawn/Ground state: {'Sodden / Soft ground' if three_day_rain > 2 else 'Firm, dry ground'}."
            ]
            if lang == "hi":
                text = (
                    f"🎪 **{location} के लिए आउटडोर कार्यक्रम, खेल व निर्माण परामर्श:**\n\n"
                    f"• **मौसम अनुकूलता**: {'⚠️ खुले में कार्यक्रम के लिए मौसम चुनौतीपूर्ण है।' if outdoor_risk else '🟢 खुले मैदान, लॉन या शादी समारोह के लिए शानदार मौसम है।'}\n"
                    f"• **हवा व टेंट सुरक्षा**: हवा के झोंके **{wind_gust:.1f} किमी/घंटा** {'(शामियाना के खूंटों को अतिरिक्त मजबूती दें)' if wind_gust > 25 else '(शांत हवा, शामियाना सुरक्षित)'}।\n"
                    f"• **वर्षा का खतरा**: 3 दिनों में कुल **{three_day_rain:.1f} मिमी वर्षा** ({rain_prob:.0f}% संभावना)।\n"
                    f"• **निर्माण / पुताई**: {'कंक्रीट ल॔टर व बाहरी पेंट का काम अभी टालें।' if three_day_rain > 2 else 'कंक्रीट ढलाई और दीवार पुताई के लिए मौसम अनुकूल है।'}\n\n"
                    f"💡 **सलाह**: {'कैटरिंग और साउंड सिस्टम के लिए वाटरप्रूफ शेड का बैकअप रखें।' if outdoor_risk else 'बिना किसी मौसम रुकावट के सभी आउटडोर गतिविधियाँ आयोजित कर सकते हैं।'}"
                )
            else:
                text = (
                    f"🎪 **Outdoor Event, Sports & Construction Advisory for {location}:**\n\n"
                    f"• **Feasibility**: {'⚠️ Elevated weather disruption risk for open-air functions.' if outdoor_risk else '🟢 Ideal atmospheric profile for open-air weddings, events & sports.'}\n"
                    f"• **Structural Wind Stability**: Gusts peak at **{wind_gust:.1f} km/h** {'(anchor marquee guy-ropes firmly)' if wind_gust > 25 else '(calm breeze, structures secure)'}.\n"
                    f"• **Precipitation**: 3-day volume {three_day_rain:.1f} mm ({rain_prob:.0f}% likelihood).\n"
                    f"• **Painting / Masonry**: {'Postpone external coating or roof slab casting.' if three_day_rain > 2 else 'Safe for concrete casting, plastering, and exterior painting.'}\n\n"
                    f"💡 **Actionable Solution**: {'Ensure backup waterproof banquet space is available.' if outdoor_risk else 'Standard outdoor lawns and stage equipment can proceed without disruption.'}"
                )
        elif persona == "HEALTH_DAILY":
            heat_alert = apparent_temp >= 38.0
            cold_alert = temp < 10.0
            verdict = "CAUTION" if (heat_alert or cold_alert) else "RECOMMENDED"
            badge = "🩺 HEALTH: THERMAL CAUTION" if (heat_alert or cold_alert) else "🩺 HEALTH: COMFORTABLE ENVIRONMENT"
            score = 50.0 if (heat_alert or cold_alert) else 95.0
            steps = [
                f"Ambient: {temp:.1f}°C, Feels like: {apparent_temp:.1f}°C.",
                f"Optimal outdoor hours: 6:00 AM – 8:30 AM and 5:00 PM – 7:00 PM.",
                f"Hydration: {'High fluid intake needed (ORS / lemon water)' if heat_alert else 'Normal fluid intake'}."
            ]
            if lang == "hi":
                text = (
                    f"🩺 **{location} के लिए स्वास्थ्य, वरिष्ठ नागरिक व दैनिक जीवन परामर्श:**\n\n"
                    f"• **तापमान व अहसास**: वर्तमान {temp:.1f}°C (महसूस होने वाला: **{apparent_temp:.1f}°C**), आर्द्रता **{humidity:.0f}%**।\n"
                    f"• **मॉर्निंग वॉक / व्यायाम**: सुबह 6:00 से 8:30 बजे का समय सबसे सुखद व सुरक्षित है।\n"
                    f"• **वरिष्ठ नागरिक व बच्चे**: {'दोपहर 11:30 से 4:00 के बीच सीधी धूप में न निकलें।' if heat_alert else 'मौसम पूरी तरह आरामदायक है।'}\n"
                    f"• **दैनिक दिनचर्या**: {'खुले वातावरण में सैर व दैनिक कार्यों के लिए मौसम अनुकूल है।' if rain_today < 0.5 and rain_tomorrow < 1.0 else 'बारिश का अनुमान; बाहर निकलते समय छाता साथ रखें।'}\n\n"
                    f"💡 **सलाह**: {'खूब पानी, मट्ठा व नारियल पानी पिएं।' if heat_alert else 'दिनचर्या सामान्य रूप से जारी रख सकते हैं।'}"
                )
            else:
                text = (
                    f"🩺 **Health, Lifestyle & Senior Citizen Advisory for {location}:**\n\n"
                    f"• **Thermal Feel**: Ambient {temp:.1f}°C (Feels like: **{apparent_temp:.1f}°C**), Humidity {humidity:.0f}%.\n"
                    f"• **Exercise & Walk Window**: Optimal between 6:00 AM – 8:30 AM and 5:00 PM – 7:00 PM.\n"
                    f"• **Senior Citizens & Children**: {'Avoid direct midday sun between 11:30 AM and 4:00 PM.' if heat_alert else 'Comfortable ambient profile without extreme thermal stress.'}\n"
                    f"• **Outdoor Routines**: {'Favorable conditions for daytime outdoor routines and travel.' if rain_today < 0.5 and rain_tomorrow < 1.0 else 'Precipitation expected; carry an umbrella and plan indoor alternatives.'}\n\n"
                    f"💡 **Actionable Solution**: {'Maintain active hydration with water and electrolytes.' if heat_alert else 'Standard health routines proceed smoothly.'}"
                )
        else: # GENERAL
            verdict = "INFO"
            badge = "🌤️ WEATHER OVERVIEW"
            score = 80.0
            steps = [
                f"Current temperature {temp:.1f}°C (Feels like: {apparent_temp:.1f}°C).",
                f"Tomorrow's rain: {rain_tomorrow:.1f} mm ({rain_prob:.0f}% prob), Wind: {wind_gust:.1f} km/h.",
                f"AI Risk Index: {risk['risk_score']:.0f}/100 ({risk['risk_level']})."
            ]
            if lang == "hi":
                text = (
                    f"🌤️ **{location} का मौसम विश्लेषण व निर्णय रिपोर्ट:**\n\n"
                    f"• **वर्तमान स्थिति**: तापमान {temp:.1f}°C, आर्द्रता {humidity:.0f}%, आसमान {curr.weather_description}।\n"
                    f"• **कल का पूर्वानुमान**: अधिकतम {f1.temperature_max:.1f}°C / न्यूनतम {f1.temperature_min:.1f}°C, वर्षा {rain_tomorrow:.1f} मिमी ({rain_prob:.0f}% संभावना)।\n"
                    f"• **मौसम जोखिम स्तर**: {risk['risk_level']} ({risk['risk_score']:.0f}/100)।\n\n"
                    f"💡 **सलाह**: {risk.get('recommendation', 'दैनिक गतिविधियों के लिए मौसम अनुकूल है।')}"
                )
            else:
                text = (
                    f"🌤️ **Weather Intelligence & Decision Summary for {location}:**\n\n"
                    f"• **Current Reality**: {temp:.1f}°C (Feels like: {apparent_temp:.1f}°C), {curr.weather_description}.\n"
                    f"• **Tomorrow's Trajectory**: High {f1.temperature_max:.1f}°C / Low {f1.temperature_min:.1f}°C, Rain: {rain_tomorrow:.1f} mm ({rain_prob:.0f}% prob).\n"
                    f"• **AI Impact Score**: **{risk['risk_score']:.0f}/100** ({risk['risk_level']}).\n\n"
                    f"💡 **Actionable Advice**: {risk.get('recommendation', 'Weather conditions permit standard daily operational activities.')}"
                )
        meta.update({"verdict": verdict, "verdict_badge": badge, "suitability_score": score, "action_steps": steps})
        return text, meta

def process_chat_message(user_msg: str, user_loc: str = "Nagpur", lang: str = "en", persona: str = "GENERAL") -> Dict[str, Any]:
    """End-to-end Chat Pipeline: Intent -> Entity Extraction -> Weather -> ML Risk -> Multilingual Localization -> Decision Synthesis."""
    import urllib.parse
    from services.multilingual_service import detect_language_from_text, translate_weather_response, clean_text_for_speech

    # 1. Detect language if auto or en
    effective_lang = (lang or "en").lower().split("-")[0]
    if effective_lang in ["auto", "en", ""]:
        detected = detect_language_from_text(user_msg)
        if detected != "en":
            effective_lang = detected

    # 2. Intent & Location
    intent, extracted_loc, crop_info = detect_intent_and_location(user_msg, default_loc=user_loc)
    
    # Check if a 6-digit Indian PIN code is in user message
    pin_match = re.search(r'\b([1-9][0-9]{5})\b', user_msg)
    if pin_match:
        extracted_loc = pin_match.group(1)

    # 3. Weather & Forecast Retrieval
    current_weather = get_current_weather(extracted_loc)
    forecast_data = get_forecast(extracted_loc, days=5)

    # 4. ML Risk Assessment
    f_day = forecast_data.forecast_days[1] if len(forecast_data.forecast_days) > 1 else forecast_data.forecast_days[0]
    risk = assess_risk_from_daily_features(
        location=extracted_loc,
        lat=forecast_data.latitude,
        lon=forecast_data.longitude,
        t_max=f_day.temperature_max,
        t_min=f_day.temperature_min,
        precipitation=f_day.precipitation_sum,
        wind_gust=f_day.wind_gust_max
    )

    # 5. Domain Decision Evaluation
    eval_lang = "hi" if effective_lang in ["hi", "mr"] else "en"
    response_text, decision_meta = evaluate_use_case_decision(
        query=user_msg,
        intent=intent,
        location=extracted_loc,
        lang=eval_lang,
        curr=current_weather.current,
        forecast=forecast_data,
        risk=risk,
        crop_info=crop_info,
        persona=persona
    )

    # 6. Multilingual Translation into target Indic Language
    if effective_lang not in ["en", "hi"]:
        response_text = translate_weather_response(response_text, target_lang=effective_lang)
    elif effective_lang == "hi" and eval_lang != "hi":
        response_text = translate_weather_response(response_text, target_lang="hi")

    # 7. RAG Retrieval for Supporting Provenance
    try:
        retriever = get_retriever()
        rag_matches = retriever.retrieve(user_msg, top_k=2)
    except Exception:
        rag_matches = []

    # 8. External LLM Synthesis (if API key is present)
    llm_provider = settings.LLM_PROVIDER.lower()
    if settings.GEMINI_API_KEY and llm_provider in ["auto", "gemini"]:
        try:
            prompt = (
                f"You are WeatherGPT, an AI weather intelligence platform. Answer the user accurately in {effective_lang}.\n"
                f"User Persona: {persona}\n"
                f"User Question: {user_msg}\n"
                f"Detected Use Case: {decision_meta['use_case']}, Verdict: {decision_meta['verdict']}\n"
                f"Location: {extracted_loc}\n"
                f"Current Temp: {current_weather.current.temperature}°C, Condition: {current_weather.current.weather_description}\n"
                f"Tomorrow Rain: {f_day.precipitation_sum}mm (Prob: {getattr(f_day, 'precipitation_probability_max', 10)}%), Wind Gusts: {f_day.wind_gust_max}km/h\n"
                f"AI Risk: {risk['risk_level']} (Score: {risk['risk_score']}/100)\n"
                f"Answer the user's specific practical question directly first with a clear verdict, give exact numbers, and conclude with actionable advice tailored to their role."
            )
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            with httpx.Client(timeout=4.0) as client:
                res = client.post(gemini_url, json=payload)
                if res.status_code == 200:
                    cand = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    if cand and len(cand.strip()) > 30:
                        response_text = cand
        except Exception as e:
            print(f"[WARN] Gemini synthesis notice: {e}")

    # 9. Clean Speech Text & Direct Audio Streaming URL
    speech_text = clean_text_for_speech(response_text)
    encoded_text = urllib.parse.quote(speech_text[:350])
    audio_url = f"/api/chat/tts?language={effective_lang}&text={encoded_text}"

    # 10. Citations & Provenance
    sources = [
        f"Live Weather Telemetry: {current_weather.data_source}",
        "Hydrological Baseline: ISRO NRSC VIC Dataset",
        "Climatology: IMD 0.25° Gridded Rainfall Archive",
        "Risk Engine: WeatherGPT ML Impact Model (HistGradientBoosting)"
    ]
    if rag_matches:
        for m in rag_matches:
            sources.append(m.get("source", "WeatherGPT Decision Guidelines"))

    weather_summary = {
        "temperature": round(current_weather.current.temperature, 1),
        "apparent_temperature": round(current_weather.current.apparent_temperature, 1),
        "humidity": round(current_weather.current.relative_humidity, 0),
        "wind_gust": round(f_day.wind_gust_max, 1),
        "rain_today": round(forecast_data.forecast_days[0].precipitation_sum, 1) if forecast_data.forecast_days else 0.0,
        "rain_tomorrow": round(f_day.precipitation_sum, 1),
        "condition": current_weather.current.weather_description,
        "rain_prob_today": round(current_weather.current.precipitation_probability or 0.0, 1),
        "rain_prob_tomorrow": round(f_day.precipitation_probability_max or 0.0, 1)
    }

    return {
        "response": response_text,
        "intent": intent,
        "extracted_location": extracted_loc,
        "language": effective_lang,
        "persona": persona,
        "risk_assessment": risk,
        "sources": sources,
        "confidence": 0.96,
        "verdict": decision_meta.get("verdict", "INFO"),
        "verdict_badge": decision_meta.get("verdict_badge", "ℹ️ ADVISORY"),
        "use_case": decision_meta.get("use_case", intent),
        "suitability_score": decision_meta.get("suitability_score", 85.0),
        "action_steps": decision_meta.get("action_steps", []),
        "weather_summary": weather_summary,
        "speech_text": speech_text,
        "audio_url": audio_url
    }

