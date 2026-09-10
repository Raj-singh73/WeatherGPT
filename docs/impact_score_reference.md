# Weather Impact Index — Reference Values

**SIH 2026 · SIH26068**

Every value below is **computed by `backend/services/impact_score.py`**, not hand-written.
Regenerate at any time with `python scenarios.py`.

## Bands

| Score | Level | Meaning |
|---|---|---|
| 0–24 | LOW | Normal conditions; routine activity |
| 25–49 | MODERATE | Plan around the weather; minor disruption |
| 50–74 | HIGH | Significant disruption; postpone exposed activity |
| 75–100 | SEVERE | Check official IMD / SDMA bulletins and act |

## Method

The index takes **max() across hazards**, not a weighted average, so any single
severe hazard drives the score. Coincident hazards add a bounded +15, and rainfall
far above the local seasonal normal adds up to +10. Thresholds follow published IMD
categories for rainfall, wind, heatwave, cold wave and low-pressure systems.

Inputs that are unavailable are **omitted, never fabricated** — the response reports
how many of the six hazard inputs were backed by real data.

This is a deterministic index (`is_machine_learning: false`), not a forecast or an
official warning.

## Reference scores

```
Weather condition                      rain   gust   tmax   tmin     hPa |  SCORE LEVEL     driver      
--------------------------------------------------------------------------------------------------------------------

— CLEAR / NORMAL —
Clear winter day, Delhi                 0.0   12.0   22.0    9.0  1016.0 |    6.0 LOW       Cold        
Pleasant post-monsoon, Nagpur           0.0   15.0   31.0   21.0  1010.0 |    4.0 LOW       Wind        
Overcast, no rain, Kolkata              0.4   18.0   30.0   25.0  1006.0 |    5.1 LOW       Wind        

— LIGHT / MODERATE RAIN —
Light drizzle, Mumbai                   3.0   22.0   29.0   25.0  1005.0 |    8.2 LOW       Rainfall    
Moderate monsoon rain, Lucknow         22.0   28.0   31.0   26.0  1000.0 |   32.4 MODERATE  Rainfall    
Rather heavy rain, Guwahati            48.0   35.0   29.0   24.0   998.0 |   63.7 HIGH      Rainfall    

— HEAVY RAIN / FLOOD —
Heavy rain, Mumbai monsoon             95.0   45.0   28.0   25.0   996.0 |   94.5 SEVERE    Rainfall    
Very heavy rain, Kerala               150.0   50.0   27.0   24.0   994.0 |  100.0 SEVERE    Rainfall    
Cloudburst, Uttarakhand               260.0   55.0   22.0   16.0   992.0 |  100.0 SEVERE    Rainfall    
Urban flood, Chennai NE monsoon       120.0   60.0   27.0   24.0   995.0 |  100.0 SEVERE    Ground saturation

— WIND / STORM —
Pre-monsoon squall, Kolkata            18.0   75.0   34.0   26.0  1002.0 |   73.3 HIGH      Wind        
Dust storm, Rajasthan                   0.0   85.0   42.0   29.0  1000.0 |   79.9 SEVERE    Wind        
Thunderstorm with gusts, Bihar         35.0   70.0   32.0   25.0   999.0 |   73.4 HIGH      Wind        

— CYCLONE —
Depression, Bay of Bengal coast        45.0   55.0   29.0   25.0   994.0 |   65.2 HIGH      Rainfall    
Cyclonic storm approaching, Odisha     90.0   90.0   28.0   25.0   986.0 |   98.2 SEVERE    Wind        
Severe cyclone landfall, Puri         160.0  130.0   27.0   24.0   968.0 |  100.0 SEVERE    Pressure    

— HEAT —
Hot summer day, Nagpur                  0.0   20.0   39.0   27.0  1002.0 |   20.8 LOW       Heat        
Heatwave, Rajasthan                     0.0   25.0   44.0   30.0  1000.0 |   69.6 HIGH      Heat        
Severe heatwave, Vidarbha               0.0   22.0   47.5   33.0   999.0 |   93.1 SEVERE    Heat        

— COLD —
Cool winter night, Lucknow              0.0   10.0   20.0    8.0  1017.0 |    8.4 LOW       Cold        
Cold wave, Punjab                       0.0   14.0   14.0    3.0  1019.0 |   55.6 HIGH      Cold        
Severe cold wave, Kashmir valley        0.0   16.0    6.0   -3.0  1021.0 |  100.0 SEVERE    Cold        

— DRY-SEASON ANOMALY —
Unseasonal rain, Vidarbha (Feb)        28.0   40.0   30.0   17.0  1008.0 |   45.9 MODERATE  Rainfall
```

## Calibration notes

Thresholds are tuned for Indian conditions specifically:

- **Pressure** contributes ~nothing above 1000 hPa. Monsoon-season surface pressure
  across India routinely sits 1000–1008 hPa, so escalation begins at the IMD
  depression threshold and below.
- **Cold** starts below ~10 °C. An 8–10 °C winter night across north India is normal;
  the IMD plains cold-wave threshold is a minimum of 4 °C or lower.
- **Heat** starts around 38 °C. 36–39 °C is ordinary pre-monsoon heat in central India;
  the IMD plains heatwave threshold is a maximum of 40 °C or above.

_Generated 2026-09-10_
