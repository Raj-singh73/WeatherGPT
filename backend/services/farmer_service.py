"""
farmer_service.py - Agronomic Decision Support & Crop Weather Advisory Engine
SIH 2026 Problem Statement SIH26068: "From Weather Data to Actionable Decisions."

Delivers genuine, crop-specific, stage-aware agro-meteorological advisories based on:
1. Multi-day NWP precipitation, temperature, wind gusts, and thunderstorm physics.
2. ICAR / IMD Agromet (Gramin Krishi Mausam Sewa - GKMS) scientific crop thresholds.
3. Growth-stage sensitivity (Sowing, Vegetative, Flowering, Maturity, Harvesting).
4. Physical field operations (machinery trafficability, post-harvest sucrose inversion, lodging risk).
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from models.schemas import FarmerAdvisoryRequest, FarmerAdvisoryResponse
from services.weather_service import get_current_weather, get_forecast, compute_calibrated_rain_probability

# Clean duplicate parenthesized district names like "Murad Nagar (Ghaziabad) (Ghaziabad)"
def sanitize_location_display(loc_raw: str) -> str:
    """Cleans up duplicate district tags, e.g. 'Murad Nagar (Ghaziabad) (Ghaziabad)' -> 'Murad Nagar, Ghaziabad'."""
    if not loc_raw:
        return "Unknown"
    clean = loc_raw.strip()
    # Replace repeated parenthesized tokens e.g. (Ghaziabad) (Ghaziabad)
    clean = re.sub(r'\(([^)]+)\)\s*\(\1\)', r'(\1)', clean)
    clean = re.sub(r'\(([^)]+)\)\s*\(\1\)', r'(\1)', clean)
    # If formatted like "Village (District)", make it "Village, District" for clean prose
    match = re.match(r'^([^(]+)\(([^)]+)\)$', clean)
    if match:
        v_name = match.group(1).strip()
        d_name = match.group(2).strip()
        if d_name.lower() in v_name.lower():
            return v_name
        return f"{v_name}, {d_name}"
    return clean

# Scientific Agronomic Thresholds & Crop Biology Knowledge Base
CROP_THRESHOLDS = {
    "Sugarcane": {
        "name_hi": "गन्ना",
        "optimal_temp_range": (20.0, 36.0),
        "critical_heat_threshold": 43.0,
        "frost_threshold": 6.0,
        "max_tolerated_rain_sowing": 30.0,
        "max_tolerated_rain_harvest": 5.0,
        "season": "Perennial / Annual (Rabi/Spring)",
        "pests_diseases": "Top borer, early shoot borer, red rot (Colletotrichum falcatum)",
        "description": "High biomass perennial cash crop sensitive to water stagnation at harvest and post-cut sucrose inversion."
    },
    "Wheat": {
        "name_hi": "गेहूं",
        "optimal_temp_range": (12.0, 25.0),
        "critical_heat_threshold": 32.0,
        "frost_threshold": 3.0,
        "max_tolerated_rain_sowing": 12.0,
        "max_tolerated_rain_harvest": 3.0,
        "season": "Rabi",
        "pests_diseases": "Yellow rust (Puccinia striiformis), Karnal bunt, aphids",
        "description": "Major Rabi cereal sensitive to terminal heat during grain filling and crusting during sowing."
    },
    "Rice": {
        "name_hi": "धान / चावल",
        "optimal_temp_range": (22.0, 35.0),
        "critical_heat_threshold": 39.0,
        "frost_threshold": 12.0,
        "max_tolerated_rain_sowing": 60.0,
        "max_tolerated_rain_harvest": 5.0,
        "season": "Kharif",
        "pests_diseases": "Bacterial leaf blight, blast (Magnaporthe oryzae), stem borer",
        "description": "Kharif staple thriving with standing water in vegetative stages but requiring dry soil for harvesting."
    },
    "Mustard": {
        "name_hi": "सरसों / राई",
        "optimal_temp_range": (10.0, 25.0),
        "critical_heat_threshold": 30.0,
        "frost_threshold": 4.0,
        "max_tolerated_rain_sowing": 10.0,
        "max_tolerated_rain_harvest": 2.0,
        "season": "Rabi",
        "pests_diseases": "Mustard aphid (Lipaphis erysimi), white rust, alternaria blight",
        "description": "Oilseed crop highly susceptible to aphids under cloudy/humid weather and pod shattering on hail/rain."
    },
    "Maize": {
        "name_hi": "मक्का",
        "optimal_temp_range": (18.0, 32.0),
        "critical_heat_threshold": 38.0,
        "frost_threshold": 6.0,
        "max_tolerated_rain_sowing": 25.0,
        "max_tolerated_rain_harvest": 5.0,
        "season": "Kharif / Rabi",
        "pests_diseases": "Fall armyworm (Spodoptera frugiperda), stem borer, banded leaf blight",
        "description": "Moderately drought-tolerant crop susceptible to waterlogging and asphyxiation in early root establishment."
    },
    "Cotton": {
        "name_hi": "कपास",
        "optimal_temp_range": (21.0, 35.0),
        "critical_heat_threshold": 42.0,
        "frost_threshold": 10.0,
        "max_tolerated_rain_sowing": 20.0,
        "max_tolerated_rain_harvest": 2.0,
        "season": "Kharif",
        "pests_diseases": "Pink bollworm, whitefly (cotton leaf curl virus), boll rot",
        "description": "Commercial fiber crop vulnerable to boll rot, square drop, and fiber staining under excessive rain."
    },
    "Pulses": {
        "name_hi": "दलहन / चना / अरहर",
        "optimal_temp_range": (15.0, 30.0),
        "critical_heat_threshold": 35.0,
        "frost_threshold": 5.0,
        "max_tolerated_rain_sowing": 10.0,
        "max_tolerated_rain_harvest": 3.0,
        "season": "Rabi / Kharif",
        "pests_diseases": "Fusarium wilt, pod borer (Helicoverpa armigera), Ascochyta blight",
        "description": "Leguminous crops with extreme intolerance to water stagnation; rain during bloom causes flower drop."
    },
    "Potato": {
        "name_hi": "आलू",
        "optimal_temp_range": (14.0, 24.0),
        "critical_heat_threshold": 30.0,
        "frost_threshold": 3.0,
        "max_tolerated_rain_sowing": 15.0,
        "max_tolerated_rain_harvest": 4.0,
        "season": "Rabi",
        "pests_diseases": "Late blight (Phytophthora infestans), early blight, tuber moth",
        "description": "Tuber vegetable crop with critical sensitivity to late blight under high humidity (>85%) and waterlogged ridges."
    }
}

# ICAR-IMD Standard Agricultural Cropping Seasons for India
CROP_VALID_SEASONS = {
    "Rice": ["KHARIF", "ZAID"],
    "Wheat": ["RABI"],
    "Mustard": ["RABI"],
    "Potato": ["RABI"],
    "Cotton": ["KHARIF"],
    "Maize": ["KHARIF", "RABI", "ZAID"],
    "Sugarcane": ["KHARIF", "RABI", "ZAID", "PERENNIAL"],
    "Pulses": ["KHARIF", "RABI", "ZAID"],
}

def get_current_agricultural_season(month: Optional[int] = None) -> Tuple[str, str, str, List[str], List[str]]:
    """
    Returns:
    (season_code, season_name_en, season_name_hi, in_season_crops, off_season_crops)
    - Kharif (Monsoon): June–October (Months 6-10) -> Rice, Maize, Cotton, Sugarcane, Pulses
    - Rabi (Winter): November–March/April (Months 11, 12, 1, 2, 3) -> Wheat, Mustard, Potato, Pulses, Sugarcane, Maize
    - Zaid (Summer): April–May (Months 4, 5) -> Pulses, Maize, Sugarcane
    """
    if month is None:
        month = datetime.now().month

    if 6 <= month <= 10:
        return (
            "KHARIF",
            "Kharif (Monsoon Season)",
            "खरीफ (मानसून ऋतु)",
            ["Rice", "Maize", "Cotton", "Sugarcane", "Pulses"],
            ["Wheat", "Mustard", "Potato"]
        )
    elif month in [11, 12, 1, 2, 3]:
        return (
            "RABI",
            "Rabi (Winter Season)",
            "रबी (शीतकालीन ऋतु)",
            ["Wheat", "Mustard", "Potato", "Pulses", "Sugarcane", "Maize"],
            ["Rice", "Cotton"]
        )
    else:  # Months 4, 5
        return (
            "ZAID",
            "Zaid (Summer Season)",
            "जायद (ग्रीष्मकालीन ऋतु)",
            ["Pulses", "Maize", "Sugarcane"],
            ["Wheat", "Mustard", "Rice", "Cotton"]
        )

def compute_continuous_crop_suitability(
    crop_name: str,
    stage: str,
    crop_profile: Dict[str, Any],
    max_temp_ahead: float,
    min_temp_ahead: float,
    three_day_rain: float,
    max_wind_ahead: float,
    has_thunderstorm: bool,
    curr_rh: float,
    soil_moisture: float = 45.0
) -> Tuple[float, str, List[Tuple[str, str]]]:
    """
    Computes a continuous multi-factor agronomic suitability score (0 to 100)
    combining thermal departure, stage-specific moisture, soil trafficability,
    wind lodging risk, and convective storm hazards.
    
    Returns:
    (suitability_score, status, factor_tuples)
    """
    opt_min, opt_max = crop_profile["optimal_temp_range"]
    t_crit = crop_profile.get("critical_heat_threshold", 40.0)
    t_frost = crop_profile.get("frost_threshold", 5.0)
    mean_temp = (max_temp_ahead + min_temp_ahead) / 2.0
    is_tall_crop = crop_name in ["Sugarcane", "Maize", "Wheat", "Mustard", "Cotton"]

    factor_explanations: List[Tuple[str, str]] = []

    # 1. Thermal Comfort Score (0 - 100)
    if opt_min <= mean_temp <= opt_max:
        center = (opt_min + opt_max) / 2.0
        span = max(1.0, (opt_max - opt_min) / 2.0)
        s_thermal = 95.0 + 5.0 * (1.0 - abs(mean_temp - center) / span)
        factor_explanations.append((
            f"Temperature regime ({min_temp_ahead:.1f}°C - {max_temp_ahead:.1f}°C) is favorable for {crop_name}.",
            f"तापमान सीमा ({min_temp_ahead:.1f}°C - {max_temp_ahead:.1f}°C) {crop_name} की वृद्धि के लिए अनुकूल है।"
        ))
    elif mean_temp > opt_max:
        if mean_temp >= t_crit:
            s_thermal = max(15.0, 50.0 - (mean_temp - t_crit) * 8.0)
            factor_explanations.append((
                f"Peak daytime temperature ({max_temp_ahead:.1f}°C) exceeds tolerance threshold ({t_crit:.1f}°C).",
                f"अधिकतम तापमान ({max_temp_ahead:.1f}°C) फसल की सुरक्षित सीमा ({t_crit:.1f}°C) से अधिक है।"
            ))
        else:
            fraction = (mean_temp - opt_max) / max(1.0, t_crit - opt_max)
            s_thermal = max(45.0, 95.0 - 45.0 * fraction)
            factor_explanations.append((
                f"Temperature ({max_temp_ahead:.1f}°C) is slightly above optimal but manageable.",
                f"तापमान ({max_temp_ahead:.1f}°C) सामान्य से थोड़ा अधिक है परंतु सहनीय है।"
            ))
    else:  # mean_temp < opt_min
        if mean_temp <= t_frost:
            s_thermal = max(15.0, 50.0 - (t_frost - mean_temp) * 8.0)
            factor_explanations.append((
                f"Low night temperature ({min_temp_ahead:.1f}°C) triggers chill/frost injury hazard.",
                f"न्यूनतम तापमान ({min_temp_ahead:.1f}°C) पाला / शीत लहर का जोखिम पैदा करता है।"
            ))
        else:
            fraction = (opt_min - mean_temp) / max(1.0, opt_min - t_frost)
            s_thermal = max(45.0, 95.0 - 45.0 * fraction)
            factor_explanations.append((
                f"Night temperatures ({min_temp_ahead:.1f}°C) are cooler than optimal.",
                f"रात्रि का तापमान ({min_temp_ahead:.1f}°C) फसल के लिए सामान्य से ठंडा है।"
            ))

    # 2. Stage-Specific Moisture / Rainfall Score (0 - 100)
    R = three_day_rain
    if stage == "Harvesting":
        if R <= 1.0:
            s_rain = 98.0 - R * 4.0
            factor_explanations.append((
                "Continuous dry weather and ample sunshine provide an optimal window for harvest and safe dispatch.",
                "शुष्क मौसम और खिली धूप कटाई और गहाई (Threshing) के लिए सर्वोत्तम अवसर प्रदान कर रहे हैं।"
            ))
        elif R <= 6.0:
            s_rain = max(45.0, 94.0 - (R - 1.0) * 8.5)
            factor_explanations.append((
                f"Moderate precipitation ({R:.1f} mm) delays grain sun-drying and machinery movement.",
                f"हल्की-मध्यम वर्षा ({R:.1f} मिमी) कटाई व धूप में सुखाने के कार्य को धीमा करेगी।"
            ))
        else:
            s_rain = max(12.0, 48.0 - (R - 6.0) * 1.5)
            if crop_name == "Sugarcane":
                factor_explanations.append((
                    f"Heavy imminent rain ({R:.1f} mm) causes severe tractor-trolley wheel rutting and rapid sucrose inversion in cut cane.",
                    f"आगामी 72 घंटों में भारी वर्षा ({R:.1f} मिमी) से खेत में कीचड़, ट्रैक्टर पहिये धंसने व कटे गन्ने में सुक्रोस ह्रास (Sucrose Inversion) का गंभीर खतरा है।"
                ))
            elif crop_name == "Rice":
                factor_explanations.append((
                    f"Precipitation ({R:.1f} mm) waterlogs paddy fields, bogs combines, and causes premature grain sprouting.",
                    f"बारिश ({R:.1f} मिमी) से धान के खेतों में पानी भरेगा, कंबाइन चलना असंभव होगा व कटी बालियों में अंकुरण का खतरा है।"
                ))
            else:
                factor_explanations.append((
                    f"Heavy imminent rainfall ({R:.1f} mm) threatens grain discolouration, fungal mold, and combine stoppages.",
                    f"आगामी वर्षा ({R:.1f} मिमी) से कटी फसल भीगने, दाने काले पड़ने व फफूंद लगने का खतरा है।"
                ))

    elif stage in ["Sowing", "Planting"]:
        if crop_name == "Rice":
            if 12.0 <= R <= 45.0:
                s_rain = 95.0
                factor_explanations.append((
                    f"Upcoming rainfall ({R:.1f} mm) is beneficial for field puddling (Leha/Machan) for transplanting.",
                    f"आगामी वर्षा ({R:.1f} मिमी) रोपाई हेतु खेत में लेवा/कीचड़ (Puddling) तैयारी के लिए अत्यधिक उपयोगी है।"
                ))
            elif R < 12.0:
                s_rain = 76.0 + R * 1.4
                factor_explanations.append((
                    "Warm temperature regime supports rapid paddy nursery seedling emergence.",
                    "गर्म तापमान और अनुकूल परिस्थितियां धान की नर्सरी तैयार करने के लिए उपयुक्त हैं।"
                ))
            else:
                s_rain = max(35.0, 95.0 - (R - 45.0) * 1.2)
                factor_explanations.append((
                    f"Excessive rainfall ({R:.1f} mm) requires drainage control in paddy nursery beds.",
                    f"अत्यधिक वर्षा ({R:.1f} मिमी) के कारण धान की नर्सरी क्यारियों में जल स्तर नियंत्रित रखना आवश्यक है।"
                ))
        else:
            max_tol = crop_profile.get("max_tolerated_rain_sowing", 20.0)
            if R <= 8.0:
                s_rain = 94.0 if R >= 1.0 else 82.0
                factor_explanations.append((
                    "Favorable seedbed moisture and clear skies ensure vigorous seedling emergence.",
                    "अनुकूल मृदा नमी और साफ मौसम बुवाई और अंकुरण के लिए उपयुक्त है।"
                ))
            elif R <= max_tol:
                s_rain = max(45.0, 92.0 - (R - 8.0) * 3.5)
                factor_explanations.append((
                    f"Moderate showers ({R:.1f} mm) require waiting for topsoil to reach workable moisture (Vapsa).",
                    f"मध्यम वर्षा ({R:.1f} मिमी) के कारण खेत सूखने (वतर आने) के बाद ही जुताई व बुवाई करें।"
                ))
            else:
                s_rain = max(15.0, 48.0 - (R - max_tol) * 1.8)
                factor_explanations.append((
                    f"Excessive rainfall ({R:.1f} mm) causes seedbed crusting (Papri) and seed rot; postpone drilling until workable field capacity (Vapsa) returns.",
                    f"अत्यधिक वर्षा ({R:.1f} मिमी) से मिट्टी की पपड़ी जमने (Crusting) और बीज सड़ने का खतरा है; बुवाई खेत में उचित नमी (वतर) आने तक स्थगित रखें।"
                ))

    elif stage == "Flowering":
        if R <= 3.0 and curr_rh <= 80.0:
            s_rain = 96.0
            factor_explanations.append((
                "Clear daylight promotes optimal insect pollination and healthy panicle emergence.",
                "अनुकूल खिली धूप सक्रिय कीट परागण (Bee activity) के लिए उत्तम है।"
            ))
        elif R <= 15.0 and curr_rh <= 85.0:
            s_rain = max(55.0, 94.0 - (R - 3.0) * 2.8)
            factor_explanations.append((
                "Beneficial soil moisture supports reproductive vigor and anthesis.",
                "मध्यम नमी से परागण और दाना बनने की प्रक्रिया को प्राकृतिक सहारा मिलता है।"
            ))
        else:
            s_rain = max(20.0, 55.0 - max(0.0, R - 15.0) * 1.5 - max(0.0, curr_rh - 85.0) * 1.0)
            factor_explanations.append((
                f"Rainfall ({R:.1f} mm) and high relative humidity ({curr_rh:.0f}%) threaten pollen wash and fungal flower blight.",
                f"बारिश ({R:.1f} मिमी) व उच्च आर्द्रता ({curr_rh:.0f}%) से परागकण धुलने व फफूंद जनित रोगों का जोखिम है।"
            ))

    elif stage == "Maturity":
        if R <= 4.0:
            s_rain = 96.0
            factor_explanations.append((
                "Dry atmospheric conditions accelerate starch hardening and sucrose accumulation.",
                "शुष्क वातावरण दानों के कड़े होने और शर्करा संचय (Brix) के लिए आदर्श है।"
            ))
        else:
            s_rain = max(22.0, 94.0 - (R - 4.0) * 3.2)
            factor_explanations.append((
                f"Rainfall ({R:.1f} mm) on mature crop risks grain discolouration, lodging, and pre-harvest sprouting.",
                f"पकती फसल पर वर्षा ({R:.1f} मिमी) दाना काला पड़ने और फसल गिरने का खतरा पैदा करती है।"
            ))

    else:  # Vegetative / Tillering
        if crop_name == "Rice":
            if 15.0 <= R <= 60.0:
                s_rain = 96.0
                factor_explanations.append((
                    f"Rainfall ({R:.1f} mm) provides ideal standing water to promote vigorous paddy tillering.",
                    f"वर्षा ({R:.1f} मिमी) धान के कल्ले फूटने (Tillering) के लिए आदर्श पानी उपलब्ध कराएगी।"
                ))
            elif R < 15.0:
                s_rain = 84.0
                factor_explanations.append((
                    "Favorable vegetative development; maintain shallow standing water layer.",
                    "वानस्पतिक बढ़वार के लिए सामान्य परिस्थितियां; खेत में 2-4 सेमी पानी बनाए रखें।"
                ))
            else:
                s_rain = max(45.0, 95.0 - (R - 60.0) * 0.8)
                factor_explanations.append((
                    f"High rain volume ({R:.1f} mm) requires open drainage to prevent submergence injury.",
                    f"अधिक वर्षा ({R:.1f} मिमी) से बचाव हेतु जल निकास नालियां खुली रखें।"
                ))
        else:
            if R > 60.0:
                s_rain = max(25.0, 58.0 - (R - 60.0) * 1.0)
                factor_explanations.append((
                    f"Severe rain accumulation ({R:.1f} mm) risks root zone saturation and nutrient leaching.",
                    f"भारी वर्षा ({R:.1f} मिमी) से खेत में जलभराव और जड़ों के दम घुटने का खतरा है।"
                ))
            elif R >= 12.0:
                s_rain = 95.0
                factor_explanations.append((
                    f"Rainfall ({R:.1f} mm) naturally recharges root zone moisture, saving scheduled irrigation costs.",
                    f"वर्षा ({R:.1f} मिमी) फसल की पानी की जरूरत पूरी करेगी और सिंचाई की लागत बचाएगी।"
                ))
            else:
                s_rain = 85.0
                factor_explanations.append((
                    "Vegetative canopy expansion proceeds normally under stable ambient conditions.",
                    "वानस्पतिक वृद्धि के लिए मौसम सामान्य है; आवश्यकतानुसार हल्की सिंचाई करें।"
                ))

    # 3. Wind Lodging / Mechanical Stress Score (0 - 100)
    if is_tall_crop:
        if max_wind_ahead <= 20.0:
            s_wind = 98.0
            factor_explanations.append((
                f"Wind speed ({max_wind_ahead:.1f} km/h) is calm and favorable for field operations.",
                f"हवा की गति ({max_wind_ahead:.1f} किमी/घंटा) शांत व कृषि कार्यों के लिए सुरक्षित है।"
            ))
        elif max_wind_ahead <= 35.0:
            s_wind = max(55.0, 98.0 - (max_wind_ahead - 20.0) * 2.5)
            factor_explanations.append((
                f"Brisk wind gusts ({max_wind_ahead:.1f} km/h) accelerate topsoil moisture evaporation.",
                f"तेज हवाएं ({max_wind_ahead:.1f} किमी/घंटा) ऊपरी मिट्टी से नमी का वाष्पीकरण तेज करती हैं।"
            ))
        else:
            s_wind = max(20.0, 55.0 - (max_wind_ahead - 35.0) * 2.2)
            factor_explanations.append((
                f"High wind gusts ({max_wind_ahead:.1f} km/h) risk mechanical lodging in tall standing {crop_name}.",
                f"तेज हवा के झोंके ({max_wind_ahead:.1f} किमी/घंटा) खड़ी फसल में गिरने (Lodging) का जोखिम पैदा करते हैं।"
            ))
    else:
        if max_wind_ahead <= 28.0:
            s_wind = 98.0
            factor_explanations.append((
                f"Wind speed ({max_wind_ahead:.1f} km/h) is calm and favorable for field operations.",
                f"हवा की गति ({max_wind_ahead:.1f} किमी/घंटा) शांत व कृषि कार्यों के लिए सुरक्षित है।"
            ))
        else:
            s_wind = max(40.0, 98.0 - (max_wind_ahead - 28.0) * 2.0)
            factor_explanations.append((
                f"Gusty winds ({max_wind_ahead:.1f} km/h) may impact spraying and field operations.",
                f"तेज हवाएं ({max_wind_ahead:.1f} किमी/घंटा) छिड़काव कार्य को प्रभावित कर सकती हैं।"
            ))

    # 4. Soil Moisture / Trafficability Score (0 - 100)
    if stage == "Harvesting":
        if soil_moisture <= 45.0:
            s_soil = 96.0
        elif soil_moisture <= 65.0:
            s_soil = max(50.0, 96.0 - (soil_moisture - 45.0) * 2.0)
        else:
            s_soil = max(15.0, 50.0 - (soil_moisture - 65.0) * 2.2)
    elif crop_name == "Rice":
        if soil_moisture >= 55.0:
            s_soil = 96.0
        else:
            s_soil = max(60.0, 70.0 + soil_moisture * 0.4)
    elif crop_name in ["Pulses", "Cotton", "Potato"]:
        if soil_moisture <= 65.0:
            s_soil = 94.0
        else:
            s_soil = max(20.0, 94.0 - (soil_moisture - 65.0) * 3.0)
    else:
        if soil_moisture <= 75.0:
            s_soil = 92.0
        else:
            s_soil = max(35.0, 92.0 - (soil_moisture - 75.0) * 2.5)

    # 5. Severe Weather / Storm Penalty
    storm_penalty = 0.0
    if has_thunderstorm:
        if stage in ["Maturity", "Harvesting"]:
            storm_penalty = 18.0
            factor_explanations.append((
                "Thunderstorm activity and wind gusts risk stalk lodging and grain shattering.",
                "गरज-चमक व आंधी से खड़ी फसल गिरने व दाना झड़ने का गंभीर खतरा है।"
            ))
        elif stage == "Flowering":
            storm_penalty = 14.0
            factor_explanations.append((
                "Thunderstorm activity risks pollen wash and floral abortion in active bloom.",
                "गरज-चमक की गतिविधियों से नाजुक फूलों के झड़ने व परागण बाधित होने की आशंका है।"
            ))
        elif stage in ["Sowing", "Planting"]:
            storm_penalty = 10.0
            factor_explanations.append((
                "Thunderstorm downpours risk soil crusting and seed displacement in newly prepared seedbeds.",
                "गरज-चमक व तेज बौछारों से नई बोई क्यारियों में मिट्टी की पपड़ी जमने (Crusting) का जोखिम है।"
            ))
        else:
            storm_penalty = 6.0
            factor_explanations.append((
                "Thunderstorm squalls require vigilance; maintain clear field runoff drains.",
                "गरज-चमक की गतिविधियों के दौरान खेत में जल निकास नालियां खुली रखें।"
            ))

    # Stage-Specific Weights
    if stage == "Harvesting":
        w_rain, w_soil, w_thermal, w_wind = 0.48, 0.24, 0.16, 0.12
    elif stage in ["Sowing", "Planting"]:
        w_rain, w_thermal, w_soil, w_wind = 0.38, 0.34, 0.16, 0.12
    elif stage == "Flowering":
        w_rain, w_thermal, w_wind, w_soil = 0.35, 0.38, 0.15, 0.12
    elif stage == "Maturity":
        w_rain, w_thermal, w_wind, w_soil = 0.42, 0.26, 0.18, 0.14
    else:  # Vegetative
        w_rain, w_thermal, w_soil, w_wind = 0.35, 0.40, 0.15, 0.10

    raw_score = (
        w_rain * s_rain +
        w_thermal * s_thermal +
        w_soil * s_soil +
        w_wind * s_wind -
        storm_penalty
    )

    final_score = float(np.clip(round(raw_score, 1), 15.0, 98.0))

    if final_score >= 80.0:
        status = "OPTIMAL"
    elif final_score >= 65.0:
        status = "FAVORABLE"
    elif final_score >= 45.0:
        status = "CAUTION"
    else:
        status = "UNFAVORABLE"

    return final_score, status, factor_explanations

def generate_farmer_advisory(req: FarmerAdvisoryRequest) -> FarmerAdvisoryResponse:
    """
    Combines live NWP physics, crop biology, stage sensitivity, and soil trafficability
    to generate an authentic, non-generic, actionable agro-meteorological advisory.
    """
    clean_location = sanitize_location_display(req.location)
    crop_name = req.crop.strip().title()
    crop_profile = CROP_THRESHOLDS.get(crop_name, CROP_THRESHOLDS["Wheat"])
    stage = req.crop_stage.strip().title()
    lang = (req.language or "en").lower()
    is_hi = lang == "hi"
    crop_hi = crop_profile.get("name_hi", crop_name)

    # 1. Fetch live forecast & current telemetry
    forecast = get_forecast(req.location, days=5)
    current = get_current_weather(req.location)

    # 2. Extract multi-day atmospheric metrics
    three_day_rain = sum(d.precipitation_sum for d in forecast.forecast_days[:3])
    max_rain_day = max((d.precipitation_sum for d in forecast.forecast_days[:3]), default=0.0)
    max_temp_ahead = max((d.temperature_max for d in forecast.forecast_days[:3]), default=30.0)
    min_temp_ahead = min((d.temperature_min for d in forecast.forecast_days[:3]), default=20.0)
    max_wind_ahead = max((d.wind_speed_max for d in forecast.forecast_days[:3]), default=12.0)
    
    # Check for thunderstorm / hail weather codes in forecast
    severe_weather_codes = {80, 81, 82, 85, 86, 95, 96, 99}
    has_thunderstorm = any(d.weather_code in severe_weather_codes for d in forecast.forecast_days[:3])
    curr_rh = getattr(current.current, 'relative_humidity', 65.0)

    # 0. Seasonality Check (Single-Season Agricultural Principle)
    # In Indian agriculture, crops belong to distinct thermal and daylength seasons.
    # In one season, only crops matching that season will grow; off-season crops will fail.
    season_code, season_name_en, season_name_hi, in_season_crops, off_season_crops = get_current_agricultural_season()
    allowed_seasons = CROP_VALID_SEASONS.get(crop_name, ["KHARIF", "RABI", "ZAID"])
    is_in_season = (season_code in allowed_seasons) or ("PERENNIAL" in allowed_seasons)

    if not is_in_season:
        # Dynamic Continuous Off-Season Suitability Modeling
        # Evaluates physical thermal departure and moisture excess rather than a static constant
        opt_min, opt_max = crop_profile["optimal_temp_range"]
        mean_temp_ahead = (max_temp_ahead + min_temp_ahead) / 2.0

        # Thermal departure from species biological comfort envelope
        if mean_temp_ahead > opt_max:
            temp_penalty = (mean_temp_ahead - opt_max) * 1.8
        elif mean_temp_ahead < opt_min:
            temp_penalty = (opt_min - mean_temp_ahead) * 1.8
        else:
            temp_penalty = 0.0

        # Off-season precipitation penalty (e.g. monsoon moisture rotting winter crops)
        rain_penalty = min(three_day_rain * 0.75, 14.0)
        storm_penalty = 6.0 if has_thunderstorm else 0.0

        raw_off_score = 38.0 - temp_penalty - rain_penalty - storm_penalty
        suitability_score = float(max(min(round(raw_off_score, 1), 42.0), 12.0))
        status = "UNFAVORABLE"
        in_season_list_str = ", ".join(in_season_crops)
        season_warning = (
            f"Off-Season Alert: {crop_name} is a {crop_profile.get('season', 'different season')} crop. "
            f"Current agricultural season is {season_name_en}. In one season, only season-appropriate crops will grow. "
            f"Favorable crops for this season are {in_season_list_str}."
            if not is_hi else
            f"ऋतु असंगति चेतावनी: {crop_hi} {crop_profile.get('season', 'अन्य ऋतु')} की फसल है। "
            f"वर्तमान कृषि मौसम {season_name_hi} है। एक मौसम में केवल उसी ऋतु की फसलें ही उग सकती हैं। "
            f"इस मौसम की अनुकूल फसलें {in_season_list_str} हैं।"
        )
        why_factors = [
            (
                f"Season Mismatch: Current month falls in {season_name_en}. {crop_name} is a {crop_profile.get('season')} crop "
                f"requiring cold/winter conditions (<20°C). Sowing or cultivating {crop_name} now will result in thermal shock, poor germination, and fungal rot."
                if not is_hi else
                f"ऋतु असंगति: वर्तमान समय {season_name_hi} का है। {crop_hi} एक {crop_profile.get('season')} फसल है जिसे ठंडी जलवायु की आवश्यकता होती है। खरीफ के गर्म व आर्द्र मौसम में {crop_hi} बोने से बीज सड़ जाएंगे।"
            ),
            (
                f"Single-Season Agronomic Rule: In one season, only season-appropriate crops will grow. "
                f"Recommended crops for this period: {in_season_list_str}."
                if not is_hi else
                f"एकल ऋतु कृषि नियम: एक मौसम में केवल उसी ऋतु के अनुकूल फसलें ही उग सकती हैं। वर्तमान मौसम के लिए उपयुक्त फसलें: {in_season_list_str}।"
            ),
            (
                f"Seasonal Transition Guidance: Await the arrival of {crop_profile.get('season')} (typically late October to November) before preparing fields for {crop_name}."
                if not is_hi else
                f"ऋतु आगमन प्रतीक्षा: {crop_hi} की बुवाई के लिए {crop_profile.get('season')} (अक्टूबर अंत या नवंबर) का इंतजार करें जब तापमान अनुकूल हो जाए।"
            )
        ]
        recommendation = (
            f"For {crop_name} in {clean_location}: Current weather suitability is UNFAVORABLE ({suitability_score:.0f}/100) due to seasonal mismatch. "
            f"You are currently in the {season_name_en}. In one season, one crop type matching the climate will grow. "
            f"Favorable crops for this season are {in_season_list_str}. Postpone {crop_name} operations until its proper season begins."
            if not is_hi else
            f"{clean_location} में {crop_hi} के लिए: मौसम उपयुक्तता अनुपयुक्त ({suitability_score:.0f}/100) है क्योंकि यह {crop_hi} का मौसम नहीं है। "
            f"वर्तमान में {season_name_hi} सक्रिय है। एक मौसम में उसी ऋतु की फसल ही सफल होती है। "
            f"इस मौसम के लिए उपयुक्त फसलें {in_season_list_str} हैं। {crop_hi} की बुवाई सही ऋतु आने पर ही करें।"
        )
        irrigation = (
            f"Withhold scheduled irrigation for off-season {crop_name}. Ensure field drainage channels are open for seasonal rains."
            if not is_hi else
            f"बेमौसम {crop_hi} के लिए सिंचाई रोकें। मौसमी बारिश के जल निकास की उचित व्यवस्था रखें।"
        )
        sow_harvest = (
            f"Do not sow {crop_name} out of season. Prepare field for in-season crops ({in_season_list_str}) or plan land preparation for {crop_name} in late October/November."
            if not is_hi else
            f"बेमौसम {crop_hi} की बुवाई कतई न करें। इस मौसम की फसलों ({in_season_list_str}) का चयन करें या अक्टूबर/नवंबर में {crop_hi} के लिए खेत तैयार करें।"
        )
        heat_warning = (
            f"Seasonal climate mismatch: Daytime temperatures ({min_temp_ahead:.1f}°C - {max_temp_ahead:.1f}°C) and photoperiod are unsuitable for {crop_name}."
            if not is_hi else
            f"ऋतु जलवायु असंगति: तापमान ({min_temp_ahead:.1f}°C - {max_temp_ahead:.1f}°C) और दिन की अवधि {crop_hi} के लिए अनुकूल नहीं हैं।"
        )
        weather_concern = f"Off-Season Crop ({season_name_en} Active)" if not is_hi else f"ऋतु असंगति ({season_name_hi} सक्रिय)"

        return FarmerAdvisoryResponse(
            crop=crop_name,
            crop_stage=stage,
            location=clean_location,
            suitability_score=suitability_score,
            suitability_status=status,
            weather_concern=weather_concern,
            irrigation_advice=irrigation,
            sowing_or_harvest_precaution=sow_harvest,
            heat_or_rain_stress_warning=heat_warning,
            recommendation=recommendation,
            why_factors=why_factors,
            data_sources=[
                "Open-Meteo NWP High-Resolution Atmospheric Forecast",
                "ICAR-IMD Gramin Krishi Mausam Sewa (GKMS) Standards",
                "ISRO NRSC VIC Hydrological Soil Moisture Dataset",
                "WeatherGPT Seasonal Crop Phenology Engine"
            ],
            disclaimer=(
                "AI-generated agricultural decision support based on ICAR agronomic thresholds — verify with local Krishi Vigyan Kendra (KVK) for certified field directives."
                if not is_hi else
                "भाकृअनुप (ICAR) मानकों पर आधारित AI कृषि मौसम परामर्श — आधिकारिक क्षेत्रीय निर्देशों के लिए अपने स्थानीय कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
            ),
            current_season=season_name_en,
            is_in_season=False,
            seasonal_crops_recommended=in_season_crops,
            season_warning=season_warning
        )

    # Compute max calibrated rain probability over 3 days
    rain_prob_3day = max(
        (compute_calibrated_rain_probability(d.precipitation_sum, d.weather_code, d.precipitation_probability_max, curr_rh)
         for d in forecast.forecast_days[:3]),
        default=5.0
    )

    soil_moisture = float(getattr(current.current, 'soil_moisture', 45.0))

    # Evaluate continuous multi-factor agronomic suitability engine
    suitability_score, status, factor_tuples = compute_continuous_crop_suitability(
        crop_name=crop_name,
        stage=stage,
        crop_profile=crop_profile,
        max_temp_ahead=max_temp_ahead,
        min_temp_ahead=min_temp_ahead,
        three_day_rain=three_day_rain,
        max_wind_ahead=max_wind_ahead,
        has_thunderstorm=has_thunderstorm,
        curr_rh=curr_rh,
        soil_moisture=soil_moisture
    )

    why_factors: List[str] = [
        (
            f"In-Season Crop: {crop_name} is actively aligned with the current {season_name_en}."
            if not is_hi else
            f"ऋतु अनुकूलता: {crop_hi} वर्तमान {season_name_hi} के पूर्णतः अनुकूल है।"
        )
    ]

    for en_factor, hi_factor in factor_tuples:
        why_factors.append(hi_factor if is_hi else en_factor)

    # 4. Generate STAGE-SPECIFIC and CROP-SPECIFIC Prescriptions
    if stage == "Harvesting":
        if three_day_rain >= 12.0 or (has_thunderstorm and three_day_rain >= 5.0):
            # HARVESTING UNDER HEAVY RAIN
            if crop_name == "Sugarcane":
                if is_hi:
                    irrigation = "कटाई पूर्व सिंचाई पहले से बंद रखी जाती है। मुख्य कार्य खेत की जल निकासी नालियों को तुरंत खोलना है ताकि जड़ों के पास पानी न ठहरे।"
                    sow_harvest = "कटे हुए गन्ने को सुक्रोस ह्रास (Sucrose Inversion) से बचाने के लिए 24 घंटे के भीतर चीनी मिल या क्रय केंद्र भेजें। जब तक खेत सूख न जाए, भारी ट्रैक्टर-ट्रॉली खेत में न ले जाएं।"
                    recommendation = (
                        f"{clean_location} में कटाई (Harvesting) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता अनुपयुक्त ({status} {suitability_score:.0f}/100) है। "
                        f"आगामी 72 घंटों में {three_day_rain:.1f} मिमी वर्षा व गरज-चमक का पूर्वानुमान है। खड़े गन्ने की कटाई तुरंत रोकें — गीली मिट्टी में भारी वाहनों से मिट्टी दबने व पेड़ी (Ratoon) की जड़ों को भारी नुकसान होगा। "
                        f"कटे हुए गन्ने को तुरंत मिल भेजें और जलभराव रोकने के लिए खेत की मेड़ों के निकास खोलें।"
                    )
                else:
                    irrigation = "Pre-harvest irrigation is withheld. Ensure field drainage outlets and furrows are completely clear to discharge rainwater."
                    sow_harvest = "Halt cutting standing cane immediately. Expedite already cut stalks to the sugar mill within 24 hours to prevent sucrose inversion (loss of recovery). Do not enter tractor-trailers into wet clayey fields to prevent deep wheel rutting."
                    recommendation = (
                        f"For {crop_name} at Harvesting stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100) due to {three_day_rain:.1f} mm rain and thunderstorm forecast over the next 72 hours. "
                        f"Immediately halt harvesting standing cane to prevent tractor wheel rutting and ratoon stool injury. "
                        f"Transport all already harvested cane to the sugar mill within 24 hours to prevent sucrose inversion, and clear drainage furrows to protect ratoon stubbles from red rot."
                    )
            elif crop_name == "Rice":
                if is_hi:
                    irrigation = "कटाई से 10-14 दिन पूर्व खेत का पानी पूरी तरह निकाल दिया जाता है। बारिश के पानी को तुरंत खेत से बाहर निकालें।"
                    sow_harvest = "कंबाइन हार्वेस्टिंग तुरंत रोकें। कटी हुई बालियों या धान की बोरियों को ऊंचे चबूतरों पर तिरपाल से सुरक्षित रखें ताकि दाने न जमने पाएं।"
                    recommendation = (
                        f"{clean_location} में कटाई (Harvesting) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता अनुपयुक्त ({status} {suitability_score:.0f}/100) है। "
                        f"आगामी {three_day_rain:.1f} मिमी बारिश से खेत में जलभराव होगा, कंबाइन मशीनें धंसेंगी व पके दानों में अंकुरण का खतरा है। कटाई रोकें और खेत से जल निकास करें।"
                    )
                else:
                    irrigation = "Paddy fields must be completely drained 10-14 days prior to harvest. Promptly open boundary dykes to expel stormwater."
                    sow_harvest = "Suspend combine harvesting immediately. Waterlogged mud will bog machinery down and wet panicles will sprout premature radicles. Shelter bagged paddy under tarpaulins."
                    recommendation = (
                        f"For {crop_name} at Harvesting stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100) due to {three_day_rain:.1f} mm rainfall forecast. "
                        f"Suspend combine harvesting immediately to prevent machinery bogging and grain sprouting in muddy water. Keep field bund outlets open to drain standing water."
                    )
            else:
                if is_hi:
                    irrigation = "कटाई अवस्था पर सिंचाई पूरी तरह बंद रखें। कटी हुई फसल को जलभराव से बचाने पर ध्यान दें।"
                    sow_harvest = "कंबाइन हार्वेस्टर तुरंत रोकें। खलिहान या खेत में कटी हुई पूलों/ढेरों को वाटरप्रूफ तिरपाल से ढकें ताकि दाने काले न पड़ें और बालियों में अंकुरण न हो।"
                    recommendation = (
                        f"{clean_location} में कटाई (Harvesting) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता अनुपयुक्त ({status} {suitability_score:.0f}/100) है। "
                        f"आगामी 72 घंटों में {three_day_rain:.1f} मिमी बारिश व तेज हवाओं ({max_wind_ahead:.1f} किमी/घंटा) की चेतावनी है। कटाई तुरंत स्थगित करें, कटी फसल को तिरपाल से सुरक्षित ढकें और खेत से पानी निकासी सुनिश्चित करें।"
                    )
                else:
                    irrigation = "No irrigation permitted at harvest stage. Ensure field perimeter ditches are opened for storm runoff drainage."
                    sow_harvest = "Cease combine harvesting immediately. Cover harvested bundles and thrashing heaps with waterproof tarpaulins to prevent grain discolouration, fungal mold, and pre-harvest earhead sprouting."
                    recommendation = (
                        f"For {crop_name} at Harvesting stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100) due to {three_day_rain:.1f} mm precipitation and wind gust warnings ({max_wind_ahead:.1f} km/h). "
                        f"Cease combine harvesting immediately, shelter harvested produce under waterproof tarpaulins, and open field drainage outlets."
                    )
        elif three_day_rain >= 3.0:
            # HARVESTING UNDER LIGHT SHOWER
            if is_hi:
                irrigation = "कटाई अवस्था पर सिंचाई निषिद्ध है। केवल जल निकासी का ध्यान रखें।"
                sow_harvest = "केवल उतना ही माल काटें जिसे उसी दिन सुरक्षित शेड या मंडी/मिल में पहुंचाया जा सके।"
                recommendation = (
                    f"{clean_location} में कटाई (Harvesting) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सतर्कतापूर्ण ({status} {suitability_score:.0f}/100) है। "
                    f"हल्की फुहारों ({three_day_rain:.1f} मिमी) की संभावना है। दैनिक आधार पर सीमित कटाई करें और उपज को खुले में न छोड़ें।"
                )
            else:
                irrigation = "Strictly withhold irrigation. Excess moisture softens field surface and degrades harvested produce quality."
                sow_harvest = "Harvest on a limited, daily-dispatch schedule. Haul produce directly to processing facilities on the same day."
                recommendation = (
                    f"For {crop_name} at Harvesting stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                    f"Intermittent precipitation ({three_day_rain:.1f} mm) may slow transport. Harvest only what can be moved to the mill/mandi within the same day."
                )
        else:
            # HARVESTING IN DRY OPTIMAL WEATHER
            if crop_name == "Sugarcane":
                if is_hi:
                    irrigation = "कटाई से 15-20 दिन पहले सिंचाई रोक दी जाती है ताकि तने में मिठास (Brix 18-20%) बढ़े और जमीन मजबूत रहे।"
                    sow_harvest = "गन्ने को जमीन की सतह से सटाकर तेज दरांती से काटें ताकि नीचे की शर्करा-युक्त पोरियां मिलें और पेड़ी (Ratoon) का फुटाव एकसमान हो। 24-36 घंटों में मिल भेजें।"
                    recommendation = (
                        f"{clean_location} में कटाई (Harvesting) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सर्वोत्तम ({status} {suitability_score:.0f}/100) है। "
                        f"शुष्क मौसम और खिली धूप कटाई के लिए आदर्श अवसर दे रहे हैं। गन्ने को जमीन की सतह से काटकर 24 घंटे के भीतर मिल गेट पर पहुंचाएं ताकि अधिकतम रिकवरी मिले।"
                    )
                else:
                    irrigation = "Pre-harvest irrigation remains strictly suspended to concentrate stalk sucrose Brix (18–20%) and firm the soil bed."
                    sow_harvest = "Cut stalks flush with the soil surface using sharp sickles to recover bottom internodes (richest in sucrose) and promote vigorous ratoon tillering. Dispatch cut cane to the sugar mill within 24–36 hours."
                    recommendation = (
                        f"For {crop_name} at Harvesting stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100) with dry weather and ample sunshine ahead. "
                        f"Full green light for cane harvesting operations. Cut stalks flush with the ground to maximize sucrose recovery and haul produce to the sugar mill within 24 hours."
                    )
            elif crop_name == "Rice":
                if is_hi:
                    irrigation = "कटाई के समय खेत पूरी तरह सूखा रखें ताकि कंबाइन हार्वेस्टर सुगमता से चल सके।"
                    sow_harvest = "दाना पकने पर धूप में (11:00 AM से 4:00 PM) कटाई करें जब नमी 14% से कम हो।"
                    recommendation = (
                        f"{clean_location} में कटाई (Harvesting) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सर्वोत्तम ({status} {suitability_score:.0f}/100) है। "
                        f"लगातार शुष्क मौसम और धूप धान की कंबाइन कटाई, गहाई व सुरक्षित भंडारण के लिए पूरी तरह अनुकूल हैं।"
                    )
                else:
                    irrigation = "Keep field drained and dry to allow solid ground bearing for combine harvesters."
                    sow_harvest = "Operate combine harvesters during dry midday hours (10:30 AM to 4:00 PM) when grain moisture is below 14%."
                    recommendation = (
                        f"For {crop_name} at Harvesting stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Continuous dry weather window allows uninhibited combine harvesting, sun-drying, and safe transport to market."
                    )
            else:
                if is_hi:
                    irrigation = "कटाई व गहाई के दौरान सिंचाई पूरी तरह बंद रखें।"
                    sow_harvest = "दोपहर के समय (11:00 AM से 4:00 PM) कंबाइन या थ्रेशर चलाएं जब नमी 12% से कम हो।"
                    recommendation = (
                        f"{clean_location} में कटाई (Harvesting) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सर्वोत्तम ({status} {suitability_score:.0f}/100) है। "
                        f"लगातार शुष्क मौसम कंबाइन हार्वेस्टिंग, गहाई और सुरक्षित भंडारण के लिए पूरी तरह अनुकूल है।"
                    )
                else:
                    irrigation = "Withhold irrigation completely to allow grain and soil dry-matter hardening."
                    sow_harvest = "Operate combine harvesters during peak midday hours (10:30 AM to 4:00 PM) when crop moisture is below 12-14%. Bag and store grain in elevated dry godowns."
                    recommendation = (
                        f"For {crop_name} at Harvesting stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Continuous dry weather window allows uninhibited combine harvesting, sun-drying, and safe transport to market."
                    )

    elif stage in ["Sowing", "Planting"]:
        if crop_name == "Rice":
            if three_day_rain >= 15.0:
                if is_hi:
                    irrigation = "वर्षा जल को मुख्य खेत की मेड़ों में संचित करें ताकि लेवा (Puddling) के काम आए। नर्सरी में 2-3 सेमी जलस्तर नियंत्रित रखें।"
                    sow_harvest = "अंकुरित बीजों को नर्सरी में समान रूप से बिखेरें। भारी वर्षा से पहले नर्सरी के निकास द्वार खोलें ताकि बीज बहने न पाएं।"
                    recommendation = (
                        f"{clean_location} में बुवाई/नर्सरी (Sowing/Nursery) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता अनुकूल ({status} {suitability_score:.0f}/100) है। "
                        f"आगामी {three_day_rain:.1f} मिमी बारिश मुख्य खेत में लेवा/कीचड़ (Puddling) तैयारी के लिए अत्यंत लाभकारी है, जिससे बिजली और डीजल की भारी बचत होगी। "
                        f"नर्सरी क्यारियों में जल निकासी खुली रखें ताकि पानी 2-3 सेमी से अधिक न भरे और अंकुरित बीज न बहें।"
                    )
                else:
                    irrigation = "Impound storm runoff in main field bunds for puddling (Leha). Maintain shallow standing water (2 cm) in nursery seedbeds."
                    sow_harvest = "Broadcast pre-germinated seed uniformly on raised nursery beds. Inspect drainage gates prior to showers to prevent seed displacement."
                    recommendation = (
                        f"For {crop_name} at Sowing/Nursery stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Upcoming {three_day_rain:.1f} mm rainfall offers an ideal opportunity to puddle and prepare main transplanting fields (Leha/Machan) with zero pumping electricity cost. "
                        f"In nursery beds, keep drainage outlets open to prevent standing water from exceeding 2–3 cm so unrooted sprouted seeds do not drift or drown."
                    )
            else:
                if is_hi:
                    irrigation = "नर्सरी क्यारियों में 1-2 सेमी पानी की पतली परत बनाए रखें ताकि अंकुरण तेजी से हो।"
                    sow_harvest = "बीजों को कार्बेन्डाजिम (2 ग्राम/किग्रा) या स्यूडोमोनास से उपचारित करके बोएं। सीधी बुवाई (DSR) के लिए सीड-ड्रिल तैयार रखें।"
                    recommendation = (
                        f"{clean_location} में बुवाई/नर्सरी अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सर्वोत्तम ({status} {suitability_score:.0f}/100) है। "
                        f"गर्म तापमान और खिली धूप धान की नर्सरी तैयार करने और अंकुरण के लिए पूरी तरह अनुकूल हैं। क्यारियों में पर्याप्त नमी बनाए रखें।"
                    )
                else:
                    irrigation = "Maintain saturated seedbed condition with 1–2 cm standing water in nursery beds."
                    sow_harvest = "Ensure certified seed treatment with Carbendazim (2g/kg) or Pseudomonas before sowing on raised beds or executing DSR drilling."
                    recommendation = (
                        f"For {crop_name} at Sowing/Nursery stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Warm temperature regime supports rapid nursery seedling emergence. Proceed with seedbed preparation and certified seed treatment."
                    )
        else:
            # Upland Crops (Wheat, Sugarcane, Maize, Pulses, Mustard, Cotton, Potato)
            if three_day_rain >= 15.0:
                if is_hi:
                    irrigation = "पलेवा / राउनी (Pre-sowing) सिंचाई रोक दें; आगामी वर्षा से खेत में पर्याप्त नमी संचित हो जाएगी।"
                    sow_harvest = "बुवाई स्थगित रखें। बारिश के बाद खेत में 'वतर' (Vapsa / कार्ययोग्य नमी) आने पर ही जुताई व बुवाई करें ताकि बीज सड़ें नहीं।"
                    recommendation = (
                        f"{clean_location} में बुवाई (Sowing) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता अनुपयुक्त ({status} {suitability_score:.0f}/100) है। "
                        f"आगामी {three_day_rain:.1f} मिमी बारिश से मिट्टी में जलभराव व पपड़ी जमने (Crusting) से बीज सड़ने का खतरा है। खेत सूखने और 'वतर' (Vapsa) आने तक बुवाई स्थगित रखें।"
                    )
                else:
                    irrigation = "Withhold pre-sowing (Rauni) irrigation as upcoming precipitation will sufficiently charge the soil profile."
                    sow_harvest = "Postpone sowing operations until topsoil dries to optimum workable field capacity (Vapsa). Treat seed with Trichoderma viride (4g/kg) or Thiram prior to planting."
                    recommendation = (
                        f"For {crop_name} at Sowing stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Postpone field preparation and sowing as {three_day_rain:.1f} mm expected rainfall will compact seedbeds and cause seed rotting. Resume sowing once the topsoil reaches workable condition (Vapsa)."
                    )
            else:
                if is_hi:
                    irrigation = "यदि खेत में नमी कम हो तो पलेवा (राउनी) करके उचित नमी पर बुवाई करें।"
                    sow_harvest = "प्रमाणित बीज उपचार (फफूंदनाशक + जैव उर्वरक) करके सीड-ड्रिल से उचित गहराई पर बुवाई करें।"
                    recommendation = (
                        f"{clean_location} में बुवाई (Sowing) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सर्वोत्तम ({status} {suitability_score:.0f}/100) है। "
                        f"मिट्टी की नमी और तापमान बीज अंकुरण के लिए अनुकूल हैं। समय पर बुवाई का कार्य संपन्न करें।"
                    )
                else:
                    irrigation = "If topsoil is dry, apply light pre-sowing irrigation (Rauni) 4–5 days prior to final seedbed harrowing."
                    sow_harvest = "Execute line sowing with seed-cum-fertilizer drills at recommended depth. Ensure fungicide seed treatment before dropping seed."
                    recommendation = (
                        f"For {crop_name} at Sowing stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Optimal soil moisture and temperature window for vigorous seed germination. Proceed with scheduled sowing and certified seed treatment."
                    )

    elif stage in ["Vegetative"]:
        if crop_name == "Rice":
            if three_day_rain >= 15.0:
                if is_hi:
                    irrigation = "बारिश का पानी खेत की मेड़ों में रोकें। 3-5 सेमी पानी कल्ले फूटने (Tillering) के लिए रखें और 7 सेमी से ऊपर का पानी निकाल दें।"
                    sow_harvest = "यूरिया की टॉप-ड्रेसिंग बारिश रुकने व खेत का पानी स्थिर होने के बाद करें ताकि खाद व्यर्थ न बहे।"
                    recommendation = (
                        f"{clean_location} में कल्ले फूटने (Vegetative/Tillering) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता अनुकूल ({status} {suitability_score:.0f}/100) है। "
                        f"आगामी वर्षा से कल्ले फूटने के लिए अनुकूल नमी मिलेगी। खेत में 3-5 सेमी पानी बनाए रखें और अधिक पानी की निकासी करें।"
                    )
                else:
                    irrigation = "Impound rainfall to maintain 3–5 cm water depth. Drain excess overflow beyond 7 cm to ensure solar radiation reaches lower tillers."
                    sow_harvest = "Withhold urea top-dressing until post-rain calm to prevent fertilizer wash-out."
                    recommendation = (
                        f"For {crop_name} at Vegetative (Tillering) stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Natural rainfall satisfies paddy moisture needs. Maintain standing water at 3–5 cm depth to stimulate tillering, and drain overflow above 7 cm."
                    )
            else:
                if is_hi:
                    irrigation = "खेत में लगातार 2-4 सेमी पानी की पतली परत बनाए रखें ताकि कल्ले स्वस्थ निकलें।"
                    sow_harvest = "नीले-हरे शैवाल (BGA) या यूरिया की अनुशंसित मात्रा डालें और खरपतवार की निगरानी करें।"
                    recommendation = (
                        f"{clean_location} में कल्ले फूटने (Vegetative) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सर्वोत्तम ({status} {suitability_score:.0f}/100) है। "
                        f"वानस्पतिक बढ़वार के लिए अनुकूल परिस्थितियां हैं। खेत में हल्का पानी बनाए रखें।"
                    )
                else:
                    irrigation = "Maintain shallow standing water (2-4 cm) in paddy fields by scheduled irrigation."
                    sow_harvest = "Apply recommended nitrogen top-dressing and scout for stem borer dead hearts."
                    recommendation = (
                        f"For {crop_name} at Vegetative stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Favorable conditions for active tillering. Maintain 2–4 cm standing water layer and monitor canopy health."
                    )
        else:
            if three_day_rain >= 15.0:
                if is_hi:
                    irrigation = f"सिंचाई स्थगित करें। आगामी 72 घंटों में {three_day_rain:.1f} मिमी बारिश से फसल की पानी की मांग पूरी हो जाएगी।"
                    sow_harvest = "यूरिया / खाद का छिड़काव बारिश के बाद करें ताकि पोषक तत्व बहकर या रिसकर व्यर्थ न जाएं।"
                    recommendation = (
                        f"{clean_location} में बढ़वार (Vegetative) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता अनुकूल ({status} {suitability_score:.0f}/100) है। "
                        f"आगामी {three_day_rain:.1f} मिमी वर्षा फसल के लिए लाभकारी रहेगी। निर्धारित सिंचाई और यूरिया की टॉप-ड्रेसिंग बारिश रुकने तक टालें।"
                    )
                else:
                    irrigation = f"Postpone scheduled irrigation. Upcoming {three_day_rain:.1f} mm precipitation fulfills root zone water requirements."
                    sow_harvest = "Withhold urea top-dressing and chemical spray until post-rain dry spell to prevent fertilizer runoff and leaching."
                    recommendation = (
                        f"For {crop_name} at Vegetative stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Upcoming {three_day_rain:.1f} mm rainfall will naturally replenish root zone moisture. Postpone irrigation and nitrogen top-dressing until showers clear."
                    )
            else:
                if is_hi:
                    irrigation = "मिट्टी की नमी जांचकर सुबह या शाम के समय हल्की क्यारी/ड्रिप सिंचाई करें।"
                    sow_harvest = "खेत में खुरपी/कल्टीवेटर से निराई-गुड़ाई करें ताकि जड़ों को हवा मिले और खरपतवार नष्ट हों।"
                    recommendation = (
                        f"{clean_location} में बढ़वार (Vegetative) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सर्वोत्तम ({status} {suitability_score:.0f}/100) है। "
                        f"सक्रिय वानस्पतिक वृद्धि के लिए परिस्थितियां उत्तम हैं। आवश्यकतानुसार हल्की सिंचाई और निराई-गुड़ाई करें।"
                    )
                else:
                    irrigation = "Apply scheduled light furrow or drip irrigation in morning or evening hours as topsoil moisture depletes."
                    sow_harvest = "Perform intercultural hoeing and weeding to aerate soil and eliminate competitive weeds."
                    recommendation = (
                        f"For {crop_name} at Vegetative stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                        f"Favorable conditions for active canopy growth and tillering. Schedule light irrigation and weed management as per routine."
                    )

    elif stage in ["Flowering"]:
        if three_day_rain >= 15.0 or curr_rh > 85.0:
            if is_hi:
                irrigation = "सिंचाई रोकें। फूल आते समय खेत में पानी जमा न होने दें।"
                sow_harvest = "फूल खिलने के समय किसी भी कीटनाशक का छिड़काव न करें ताकि परागण करने वाली मधुमक्खियों को नुकसान न पहुंचे।"
                recommendation = (
                    f"{clean_location} में फूल (Flowering) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सतर्कतापूर्ण ({status} {suitability_score:.0f}/100) है। "
                    f"वर्षा ({three_day_rain:.1f} मिमी) व उच्च आर्द्रता से पराग धुलने का खतरा है। किसी भी प्रकार के रसायनों का छिड़काव टालें और जल निकासी खुली रखें।"
                )
            else:
                irrigation = "Postpone irrigation. Avoid water stagnation around roots during the sensitive reproductive phase."
                sow_harvest = "Withhold all chemical insecticides and foliar sprays during active bloom to protect pollinator bees."
                recommendation = (
                    f"For {crop_name} at Flowering stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                    f"Rainfall ({three_day_rain:.1f} mm) and high relative humidity risk washing away pollen. Withhold chemical spraying and ensure field drainage."
                )
        else:
            if is_hi:
                irrigation = "फूल और दाना बनते समय नमी की कमी न होने दें; हल्की सिंचाई बनाए रखें।"
                sow_harvest = "फसल पर कीटों (माहू, सुंडी) के प्रकोप की नियमित निगरानी करें।"
                recommendation = (
                    f"{clean_location} में फूल (Flowering) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सर्वोत्तम ({status} {suitability_score:.0f}/100) है। "
                    f"खिली धूप सफल परागण और फली/बाली बनने के लिए आदर्श है। मृदा में मध्यम नमी बनाए रखें।"
                )
            else:
                irrigation = "Maintain adequate moisture without ponding; moisture stress during anthesis directly lowers grain set."
                sow_harvest = "Scout for sucking pests and fungal spots during calm morning hours."
                recommendation = (
                    f"For {crop_name} at Flowering stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                    f"Sunny weather supports high pollinator activity and sound grain set. Maintain uniform root zone moisture."
                )

    else:  # Maturity
        if three_day_rain >= 12.0:
            if is_hi:
                irrigation = "सिंचाई पूरी तरह बंद रखें। परिपक्वता पर पानी देने से दाना खराब होता है और फसल गिरती है।"
                sow_harvest = "तेज हवाओं से बचाव के लिए खेत की मेड़ों को मजबूत रखें और कटाई की तैयारी शुरू करें।"
                recommendation = (
                    f"{clean_location} में परिपक्वता (Maturity) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सतर्कतापूर्ण ({status} {suitability_score:.0f}/100) है। "
                    f"आगामी वर्षा ({three_day_rain:.1f} मिमी) से फसल गिरने (Lodging) का जोखिम है। सिंचाई बंद रखें और जल निकास सुगम बनाएं।"
                )
            else:
                irrigation = "Withhold irrigation strictly. Moisture at ripening softens stems, delays harvest, and induces lodging."
                sow_harvest = "Prepare threshing yard, check grain moisture, and prepare combine harvesting machinery."
                recommendation = (
                    f"For {crop_name} at Maturity stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                    f"Imminent rain ({three_day_rain:.1f} mm) threatens stalk lodging. Withhold all irrigation and ensure field furrows drain freely."
                )
        else:
            if is_hi:
                irrigation = "सिंचाई पूरी तरह बंद रखें ताकि फसल समान रूप से पके।"
                sow_harvest = "फसल की नमी 14% से कम आते ही कटाई की योजना बनाएं।"
                recommendation = (
                    f"{clean_location} में परिपक्वता (Maturity) अवस्था पर {crop_hi} के लिए: मौसम उपयुक्तता सर्वोत्तम ({status} {suitability_score:.0f}/100) है। "
                    f"खिली धूप दानों में चमक और शर्करा सांद्रता बढ़ाने के लिए अनुकूल है। कटाई यंत्र तैयार रखें।"
                )
            else:
                irrigation = "Withhold irrigation completely to promote natural field drying and maximum sucrose/grain test weight."
                sow_harvest = "Inspect crop maturity indices. Plan harvesting as soon as moisture falls below 14%."
                recommendation = (
                    f"For {crop_name} at Maturity stage in {clean_location}: Current weather suitability is {status} ({suitability_score:.0f}/100). "
                    f"Dry weather promotes uniform ripening and high starch/sucrose density. Prepare harvesting machinery."
                )

    # 5. Hydrometeorological & Thermal Warning formulation
    if has_thunderstorm or max_wind_ahead > 32.0:
        if is_hi:
            heat_warning = f"मौसम चेतावनी: तेज हवाएं ({max_wind_ahead:.1f} किमी/घंटा) व गरज-चमक का अलर्ट। लंबी फसलों ({crop_hi}) में गिरने (Lodging) का जोखिम है।"
        else:
            heat_warning = f"Severe weather alert: Thunderstorm activity and wind gusts up to {max_wind_ahead:.1f} km/h. High lodging risk for tall canopy {crop_name}."
    elif max_temp_ahead >= 38.0:
        if is_hi:
            heat_warning = f"तापमान अलर्ट: दोपहर का तापमान {max_temp_ahead:.1f}°C तक पहुंचेगा। वानस्पतिक अवस्था में शाम को हल्की सिंचाई देकर शीतलन प्रभाव बनाएं।"
        else:
            heat_warning = f"Thermal stress alert: Daytime high reaching {max_temp_ahead:.1f}°C. Provide light evening irrigation in vegetative phases to buffer microclimate."
    elif min_temp_ahead <= 5.0:
        if is_hi:
            heat_warning = f"शीत लहर चेतावनी: रात का तापमान {min_temp_ahead:.1f}°C तक गिर सकता है। पाले (Frost) से बचाव के लिए खेत के किनारों पर धुआं करें।"
        else:
            heat_warning = f"Cold wave warning: Night temperatures dropping to {min_temp_ahead:.1f}°C. Light irrigation buffers soil against frost injury."
    else:
        if is_hi:
            heat_warning = "तापमान और हवा की गति सामान्य कृषि सहनशीलता सीमा के भीतर हैं।"
        else:
            heat_warning = "Thermal stress index and wind conditions are within normal crop tolerance limits."

    # Weather concern summary
    if three_day_rain >= 15.0:
        weather_concern = f"Heavy rainfall expected ({three_day_rain:.1f} mm, {rain_prob_3day:.0f}% prob)" if not is_hi else f"भारी वर्षा का अलर्ट ({three_day_rain:.1f} मिमी, {rain_prob_3day:.0f}% संभावना)"
    elif max_wind_ahead > 32.0 or has_thunderstorm:
        weather_concern = f"Thunderstorm & high wind gusts ({max_wind_ahead:.1f} km/h)" if not is_hi else f"गरज-चमक व तेज आंधी ({max_wind_ahead:.1f} किमी/घंटा)"
    elif max_temp_ahead >= 38.0:
        weather_concern = f"High heat stress ({max_temp_ahead:.1f}°C)" if not is_hi else f"तीव्र गर्मी व लू ({max_temp_ahead:.1f}°C)"
    else:
        weather_concern = "Favorable weather conditions" if not is_hi else "अनुकूल सामान्य मौसम"

    return FarmerAdvisoryResponse(
        crop=crop_name,
        crop_stage=stage,
        location=clean_location,
        suitability_score=suitability_score,
        suitability_status=status,
        weather_concern=weather_concern,
        irrigation_advice=irrigation,
        sowing_or_harvest_precaution=sow_harvest,
        heat_or_rain_stress_warning=heat_warning,
        recommendation=recommendation,
        why_factors=why_factors,
        data_sources=[
            "Open-Meteo NWP High-Resolution Atmospheric Forecast",
            "ICAR-IMD Gramin Krishi Mausam Sewa (GKMS) Standards",
            "ISRO NRSC VIC Hydrological Soil Moisture Dataset",
            "WeatherGPT Crop Agro-meteorological Knowledge Base"
        ],
        disclaimer=(
            "AI-generated agricultural decision support based on ICAR agronomic thresholds — verify with local Krishi Vigyan Kendra (KVK) for certified field directives."
            if not is_hi else
            "भाकृअनुप (ICAR) मानकों पर आधारित AI कृषि मौसम परामर्श — आधिकारिक क्षेत्रीय निर्देशों के लिए अपने स्थानीय कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
        ),
        current_season=season_name_en,
        is_in_season=True,
        seasonal_crops_recommended=in_season_crops,
        season_warning=None
    )
