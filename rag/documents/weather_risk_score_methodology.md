# WeatherGPT AI Impact Scoring & Multi-hazard Methodology

## Weather Impact Score Definition
The Weather Impact Score is a continuous value between 0 and 100 derived using physically constrained multi-hazard analysis combined with trained Machine Learning ensemble classifiers (Random Forest and HistGradientBoosting).

## Risk Tier Classification
- **LOW (0 - 29)**: Green alert tier. Atmospheric variables are within historical seasonal standard deviations. No special precautions necessary.
- **MODERATE (30 - 54)**: Yellow alert tier. Mild weather disturbances (scattered showers, moderate gusts up to 45 km/h). Keep monitoring daily forecast.
- **HIGH (55 - 74)**: Orange alert tier. Substantial weather hazard (heavy downpours > 65 mm, strong wind squalls, above-normal rainfall anomalies). Postpone non-critical travel and agricultural spraying.
- **SEVERE (75 - 100)**: Red alert tier. Extreme life/property danger (cyclones, gale winds > 75 km/h, catastrophic deluge > 115 mm, deep barometric drops). Immediate shelter and emergency precautions mandatory.

## Physical Contributors to Composite Risk
1. 24h & Multi-day rainfall accumulation (40% weight)
2. Peak surface wind gusts (25% weight)
3. Atmospheric barometric depression (15% weight)
4. Extreme temperature deviations (10% weight)
5. Hydrological soil saturation indices (10% weight)
