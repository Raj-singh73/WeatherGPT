import json
import os

# Script to build full pan-India administrative hierarchy across ALL 28 states & major UTs

STATES_DATA = {
    "Andhra Pradesh": {
        "lat": 15.9129, "lon": 79.7400,
        "districts": {
            "Visakhapatnam": {
                "lat": 17.6868, "lon": 83.2185, "climatology_mm": 8.5,
                "blocks": {
                    "Anakapalle": {"lat": 17.6913, "lon": 83.0039, "villages": [{"name": "Kasimkota", "lat": 17.65, "lon": 82.98, "elevation": 28}, {"name": "Munagapaka", "lat": 17.62, "lon": 83.02, "elevation": 25}]},
                    "Bheemunipatnam": {"lat": 17.8900, "lon": 83.4300, "villages": [{"name": "Tagarapuvalasa", "lat": 17.92, "lon": 83.42, "elevation": 35}, {"name": "Nidigattu", "lat": 17.88, "lon": 83.40, "elevation": 22}]},
                    "Gajuwaka": {"lat": 17.6900, "lon": 83.1800, "villages": [{"name": "Vadlapudi", "lat": 17.67, "lon": 83.19, "elevation": 18}, {"name": "Duvvada", "lat": 17.70, "lon": 83.15, "elevation": 26}]}
                }
            },
            "Krishna (Vijayawada)": {
                "lat": 16.5062, "lon": 80.6480, "climatology_mm": 6.2,
                "blocks": {
                    "Gannavaram": {"lat": 16.5400, "lon": 80.8000, "villages": [{"name": "Kesarapalle", "lat": 16.53, "lon": 80.78, "elevation": 24}, {"name": "Telaprolu", "lat": 16.58, "lon": 80.85, "elevation": 22}]},
                    "Machilipatnam": {"lat": 16.1800, "lon": 81.1300, "villages": [{"name": "Chilakalapudi", "lat": 16.20, "lon": 81.14, "elevation": 12}, {"name": "Pedana Rural", "lat": 16.26, "lon": 81.16, "elevation": 14}]}
                }
            },
            "Guntur": {
                "lat": 16.3067, "lon": 80.4365, "climatology_mm": 5.8,
                "blocks": {
                    "Tenali": {"lat": 16.2400, "lon": 80.6400, "villages": [{"name": "Angalakuduru", "lat": 16.23, "lon": 80.62, "elevation": 16}, {"name": "Kollipara", "lat": 16.28, "lon": 80.72, "elevation": 18}]},
                    "Mangalagiri": {"lat": 16.4300, "lon": 80.5600, "villages": [{"name": "Nowlur", "lat": 16.45, "lon": 80.54, "elevation": 20}, {"name": "Atmakur", "lat": 16.42, "lon": 80.57, "elevation": 22}]}
                }
            },
            "Chittoor (Tirupati)": {
                "lat": 13.6288, "lon": 79.4192, "climatology_mm": 9.4,
                "blocks": {
                    "Chandragiri": {"lat": 13.5800, "lon": 79.3100, "villages": [{"name": "A-Rangampeta", "lat": 13.60, "lon": 79.28, "elevation": 195}, {"name": "Panakam", "lat": 13.56, "lon": 79.33, "elevation": 188}]},
                    "Srikalahasti": {"lat": 13.7500, "lon": 79.7000, "villages": [{"name": "Thondamanadu", "lat": 13.72, "lon": 79.65, "elevation": 68}, {"name": "Subbanaidu Kandriga", "lat": 13.78, "lon": 79.72, "elevation": 62}]}
                }
            }
        }
    },
    "Arunachal Pradesh": {
        "lat": 28.2180, "lon": 94.7278,
        "districts": {
            "Papum Pare (Itanagar)": {
                "lat": 27.0844, "lon": 93.6053, "climatology_mm": 24.5,
                "blocks": {
                    "Doimukh": {"lat": 27.1400, "lon": 93.7500, "villages": [{"name": "Karsingsa", "lat": 27.12, "lon": 93.73, "elevation": 320}, {"name": "Rono Ground Village", "lat": 27.15, "lon": 93.76, "elevation": 335}]},
                    "Naharlagun": {"lat": 27.1000, "lon": 93.6900, "villages": [{"name": "Nirjuli", "lat": 27.13, "lon": 93.74, "elevation": 340}, {"name": "Banderdewa", "lat": 27.08, "lon": 93.81, "elevation": 210}]}
                }
            },
            "Tawang": {
                "lat": 27.5861, "lon": 91.8594, "climatology_mm": 18.2,
                "blocks": {
                    "Jang": {"lat": 27.5700, "lon": 91.9800, "villages": [{"name": "Lhou", "lat": 27.56, "lon": 91.95, "elevation": 2180}, {"name": "Mukto", "lat": 27.53, "lon": 91.93, "elevation": 2350}]}
                }
            }
        }
    },
    "Assam": {
        "lat": 26.2006, "lon": 92.9376,
        "districts": {
            "Kamrup Metropolitan (Guwahati)": {
                "lat": 26.1445, "lon": 91.7362, "climatology_mm": 12.4,
                "blocks": {
                    "Dispur": {"lat": 26.1400, "lon": 91.7900, "villages": [{"name": "Sonapur", "lat": 26.11, "lon": 91.97, "elevation": 62}, {"name": "Khetri", "lat": 26.10, "lon": 92.08, "elevation": 58}]},
                    "Azara": {"lat": 26.1100, "lon": 91.6000, "villages": [{"name": "Dharapur", "lat": 26.13, "lon": 91.62, "elevation": 54}, {"name": "Garal", "lat": 26.10, "lon": 91.59, "elevation": 52}]}
                }
            },
            "Dibrugarh": {
                "lat": 27.4728, "lon": 94.9120, "climatology_mm": 22.8,
                "blocks": {
                    "Tingkhong": {"lat": 27.2100, "lon": 95.1200, "villages": [{"name": "Rajgarh Tea Estate", "lat": 27.18, "lon": 95.15, "elevation": 115}, {"name": "Dillibari", "lat": 27.23, "lon": 95.09, "elevation": 112}]},
                    "Moran": {"lat": 27.1800, "lon": 94.9300, "villages": [{"name": "Khowang", "lat": 27.22, "lon": 94.90, "elevation": 105}, {"name": "Sepon", "lat": 27.15, "lon": 94.96, "elevation": 108}]}
                }
            },
            "Cachar (Silchar)": {
                "lat": 24.8333, "lon": 92.7789, "climatology_mm": 15.6,
                "blocks": {
                    "Lakhipur": {"lat": 24.8000, "lon": 93.0100, "villages": [{"name": "Binnakandi", "lat": 24.78, "lon": 93.04, "elevation": 32}, {"name": "Singerbond", "lat": 24.82, "lon": 92.99, "elevation": 29}]}
                }
            }
        }
    },
    "Bihar": {
        "lat": 25.0961, "lon": 85.3131,
        "districts": {
            "Patna": {
                "lat": 25.5941, "lon": 85.1376, "climatology_mm": 14.2,
                "blocks": {
                    "Danapur": {"lat": 25.6300, "lon": 85.0400, "villages": [{"name": "Khagual Rural", "lat": 25.58, "lon": 85.03, "elevation": 56}, {"name": "Usri", "lat": 25.65, "lon": 85.02, "elevation": 54}]},
                    "Phulwari Sharif": {"lat": 25.5700, "lon": 85.0800, "villages": [{"name": "Sampatchak", "lat": 25.54, "lon": 85.16, "elevation": 55}, {"name": "Janipur", "lat": 25.55, "lon": 85.04, "elevation": 56}]},
                    "Bakhtiarpur": {"lat": 25.4500, "lon": 85.5200, "villages": [{"name": "Salimpur", "lat": 25.47, "lon": 85.49, "elevation": 52}, {"name": "Ghoswari", "lat": 25.42, "lon": 85.56, "elevation": 50}]}
                }
            },
            "Gaya": {
                "lat": 24.7914, "lon": 85.0002, "climatology_mm": 16.5,
                "blocks": {
                    "Bodh Gaya": {"lat": 24.6961, "lon": 84.9869, "villages": [{"name": "Bakrour", "lat": 24.70, "lon": 84.99, "elevation": 115}, {"name": "Mora Pahar", "lat": 24.72, "lon": 85.02, "elevation": 120}]},
                    "Sherghati": {"lat": 24.5700, "lon": 84.7900, "villages": [{"name": "Dobhi", "lat": 24.52, "lon": 84.93, "elevation": 132}, {"name": "Amas", "lat": 24.58, "lon": 84.68, "elevation": 140}]}
                }
            },
            "Muzaffarpur": {
                "lat": 26.1209, "lon": 85.3647, "climatology_mm": 12.8,
                "blocks": {
                    "Kanti": {"lat": 26.2000, "lon": 85.2900, "villages": [{"name": "Damodarpur", "lat": 26.18, "lon": 85.31, "elevation": 58}, {"name": "Narma", "lat": 26.22, "lon": 85.27, "elevation": 60}]},
                    "Motipur": {"lat": 26.2800, "lon": 85.1800, "villages": [{"name": "Baruraj", "lat": 26.31, "lon": 85.15, "elevation": 62}, {"name": "Mahwal", "lat": 26.26, "lon": 85.20, "elevation": 59}]}
                }
            }
        }
    },
    "Chhattisgarh": {
        "lat": 21.2787, "lon": 81.8661,
        "districts": {
            "Raipur": {
                "lat": 21.2514, "lon": 81.6296, "climatology_mm": 11.2,
                "blocks": {
                    "Dharsiwa": {"lat": 21.3600, "lon": 81.6700, "villages": [{"name": "Tildanevada", "lat": 21.38, "lon": 81.69, "elevation": 298}, {"name": "Birgaon Rural", "lat": 21.31, "lon": 81.63, "elevation": 294}]},
                    "Abhanpur": {"lat": 21.0500, "lon": 81.7500, "villages": [{"name": "Nawapara", "lat": 20.97, "lon": 81.84, "elevation": 285}, {"name": "Kendri", "lat": 21.08, "lon": 81.71, "elevation": 290}]}
                }
            },
            "Bilaspur": {
                "lat": 22.0797, "lon": 82.1409, "climatology_mm": 14.5,
                "blocks": {
                    "Kota": {"lat": 22.2900, "lon": 82.0200, "villages": [{"name": "Ratanpur Rural", "lat": 22.30, "lon": 82.13, "elevation": 305}, {"name": "Belgahna", "lat": 22.38, "lon": 81.98, "elevation": 340}]},
                    "Takhatpur": {"lat": 22.1500, "lon": 81.8700, "villages": [{"name": "Sakri", "lat": 22.12, "lon": 82.05, "elevation": 288}, {"name": "Jarhagaon", "lat": 22.18, "lon": 81.79, "elevation": 292}]}
                }
            },
            "Bastar (Jagdalpur)": {
                "lat": 19.0740, "lon": 82.0080, "climatology_mm": 8.0,
                "blocks": {
                    "Tokapal": {"lat": 18.9800, "lon": 81.8700, "villages": [{"name": "Karanpur", "lat": 18.96, "lon": 81.89, "elevation": 558}, {"name": "Parpa", "lat": 19.01, "lon": 81.93, "elevation": 552}]}
                }
            }
        }
    },
    "Goa": {
        "lat": 15.2993, "lon": 74.1240,
        "districts": {
            "North Goa (Panaji)": {
                "lat": 15.4909, "lon": 73.8278, "climatology_mm": 0.5,
                "blocks": {
                    "Bardez (Mapusa)": {"lat": 15.5900, "lon": 73.8100, "villages": [{"name": "Calangute Rural", "lat": 15.54, "lon": 73.76, "elevation": 12}, {"name": "Aldona", "lat": 15.58, "lon": 73.87, "elevation": 24}]},
                    "Pernem": {"lat": 15.7200, "lon": 73.7900, "villages": [{"name": "Mandrem", "lat": 15.67, "lon": 73.73, "elevation": 8}, {"name": "Morjim", "lat": 15.62, "lon": 73.74, "elevation": 6}]}
                }
            },
            "South Goa (Margao)": {
                "lat": 15.2832, "lon": 73.9862, "climatology_mm": 0.4,
                "blocks": {
                    "Salcete": {"lat": 15.2700, "lon": 73.9600, "villages": [{"name": "Benaulim", "lat": 15.25, "lon": 73.93, "elevation": 5}, {"name": "Navelim", "lat": 15.26, "lon": 73.97, "elevation": 15}]},
                    "Canacona": {"lat": 15.0100, "lon": 74.0500, "villages": [{"name": "Agonda", "lat": 15.04, "lon": 73.98, "elevation": 10}, {"name": "Poinguinim", "lat": 14.97, "lon": 74.09, "elevation": 22}]}
                }
            }
        }
    },
    "Gujarat": {
        "lat": 22.2587, "lon": 71.1924,
        "districts": {
            "Ahmedabad": {
                "lat": 23.0225, "lon": 72.5714, "climatology_mm": 1.2,
                "blocks": {
                    "Daskroi": {"lat": 22.9500, "lon": 72.6000, "villages": [{"name": "Bavla Rural", "lat": 22.83, "lon": 72.36, "elevation": 42}, {"name": "Sanand Gam", "lat": 22.99, "lon": 72.38, "elevation": 48}]},
                    "Viramgam": {"lat": 23.1200, "lon": 72.0300, "villages": [{"name": "Mandal", "lat": 23.28, "lon": 71.92, "elevation": 40}, {"name": "Detroj", "lat": 23.33, "lon": 72.19, "elevation": 44}]}
                }
            },
            "Surat": {
                "lat": 21.1702, "lon": 72.8311, "climatology_mm": 0.8,
                "blocks": {
                    "Chorasi": {"lat": 21.1200, "lon": 72.7800, "villages": [{"name": "Dumas", "lat": 21.08, "lon": 72.71, "elevation": 6}, {"name": "Hajira Rural", "lat": 21.10, "lon": 72.65, "elevation": 8}]},
                    "Bardoli": {"lat": 21.1200, "lon": 73.1100, "villages": [{"name": "Kadod", "lat": 21.20, "lon": 73.16, "elevation": 32}, {"name": "Mahuva", "lat": 20.95, "lon": 73.15, "elevation": 38}]}
                }
            },
            "Rajkot (Saurashtra)": {
                "lat": 22.3039, "lon": 70.8022, "climatology_mm": 0.5,
                "blocks": {
                    "Gondal": {"lat": 21.9600, "lon": 70.7900, "villages": [{"name": "Kotda Sangani", "lat": 21.93, "lon": 70.92, "elevation": 142}, {"name": "Ribda", "lat": 22.09, "lon": 70.78, "elevation": 136}]},
                    "Morbi": {"lat": 22.8100, "lon": 70.8300, "villages": [{"name": "Tankara", "lat": 22.67, "lon": 70.75, "elevation": 85}, {"name": "Wankaner Rural", "lat": 22.61, "lon": 70.96, "elevation": 92}]}
                }
            },
            "Kutch (Bhuj)": {
                "lat": 23.2420, "lon": 69.6669, "climatology_mm": 1.0,
                "blocks": {
                    "Anjar": {"lat": 23.1100, "lon": 70.0200, "villages": [{"name": "Gandhidham Rural", "lat": 23.07, "lon": 70.13, "elevation": 27}, {"name": "Khedoi", "lat": 23.14, "lon": 69.96, "elevation": 54}]},
                    "Mandvi": {"lat": 22.8300, "lon": 69.3500, "villages": [{"name": "Gadhsisa", "lat": 22.95, "lon": 69.38, "elevation": 35}, {"name": "Mundra Rural", "lat": 22.84, "lon": 69.72, "elevation": 15}]}
                }
            }
        }
    },
    "Haryana": {
        "lat": 29.0588, "lon": 76.0856,
        "districts": {
            "Gurugram": {
                "lat": 28.4595, "lon": 77.0266, "climatology_mm": 16.5,
                "blocks": {
                    "Sohna": {"lat": 28.2500, "lon": 77.0600, "villages": [{"name": "Badshahpur Rural", "lat": 28.38, "lon": 77.05, "elevation": 224}, {"name": "Kasan", "lat": 28.34, "lon": 76.92, "elevation": 230}]},
                    "Pataudi": {"lat": 28.3200, "lon": 76.7800, "villages": [{"name": "Haileymandi", "lat": 28.34, "lon": 76.76, "elevation": 232}, {"name": "Farrukhnagar", "lat": 28.45, "lon": 76.82, "elevation": 226}]}
                }
            },
            "Karnal": {
                "lat": 29.6857, "lon": 76.9905, "climatology_mm": 24.8,
                "blocks": {
                    "Gharaunda": {"lat": 29.5400, "lon": 76.9700, "villages": [{"name": "Bastara", "lat": 29.58, "lon": 76.98, "elevation": 246}, {"name": "Kohand", "lat": 29.50, "lon": 76.96, "elevation": 244}]},
                    "Assandh": {"lat": 29.5200, "lon": 76.6000, "villages": [{"name": "Salwan", "lat": 29.47, "lon": 76.65, "elevation": 248}, {"name": "Jalmana", "lat": 29.55, "lon": 76.68, "elevation": 247}]}
                }
            },
            "Hisar": {
                "lat": 29.1492, "lon": 75.7217, "climatology_mm": 13.0,
                "blocks": {
                    "Hansi": {"lat": 29.1000, "lon": 75.9600, "villages": [{"name": "Dhana Kalan", "lat": 29.08, "lon": 75.93, "elevation": 218}, {"name": "Sisai", "lat": 29.18, "lon": 76.04, "elevation": 220}]}
                }
            }
        }
    },
    "Himachal Pradesh": {
        "lat": 31.1048, "lon": 77.1734,
        "districts": {
            "Shimla": {
                "lat": 31.1048, "lon": 77.1734, "climatology_mm": 65.0,
                "blocks": {
                    "Theog": {"lat": 31.1200, "lon": 77.3500, "villages": [{"name": "Kotkhai", "lat": 31.12, "lon": 77.53, "elevation": 1880}, {"name": "Fagu", "lat": 31.09, "lon": 77.29, "elevation": 2450}]},
                    "Rampur": {"lat": 31.4500, "lon": 77.6300, "villages": [{"name": "Sarahan", "lat": 31.51, "lon": 77.79, "elevation": 2165}, {"name": "Nankhari", "lat": 31.33, "lon": 77.58, "elevation": 2050}]}
                }
            },
            "Kangra (Dharamshala)": {
                "lat": 32.2190, "lon": 76.3234, "climatology_mm": 92.5,
                "blocks": {
                    "Palampur": {"lat": 32.1100, "lon": 76.5400, "villages": [{"name": "Baijnath Rural", "lat": 32.05, "lon": 76.65, "elevation": 1120}, {"name": "Maranda", "lat": 32.10, "lon": 76.51, "elevation": 1250}]},
                    "Nurpur": {"lat": 32.3000, "lon": 75.8900, "villages": [{"name": "Jawali", "lat": 32.15, "lon": 76.01, "elevation": 510}, {"name": "Fatehpur", "lat": 32.11, "lon": 75.92, "elevation": 460}]}
                }
            },
            "Kullu (Manali)": {
                "lat": 31.9579, "lon": 77.1095, "climatology_mm": 78.0,
                "blocks": {
                    "Manali": {"lat": 32.2396, "lon": 77.1887, "villages": [{"name": "Naggar", "lat": 32.14, "lon": 77.17, "elevation": 1850}, {"name": "Solang Village", "lat": 32.31, "lon": 77.15, "elevation": 2480}]}
                }
            }
        }
    },
    "Jharkhand": {
        "lat": 23.6102, "lon": 85.2799,
        "districts": {
            "Ranchi": {
                "lat": 23.3441, "lon": 85.3096, "climatology_mm": 18.0,
                "blocks": {
                    "Kanke": {"lat": 23.4300, "lon": 85.3200, "villages": [{"name": "Arsande", "lat": 23.41, "lon": 85.34, "elevation": 645}, {"name": "Pithoria", "lat": 23.51, "lon": 85.31, "elevation": 650}]},
                    "Namkum": {"lat": 23.3300, "lon": 85.3900, "villages": [{"name": "Tatisilwai", "lat": 23.36, "lon": 85.43, "elevation": 632}, {"name": "Rajaulatu", "lat": 23.31, "lon": 85.42, "elevation": 628}]}
                }
            },
            "East Singhbhum (Jamshedpur)": {
                "lat": 22.8046, "lon": 86.2029, "climatology_mm": 14.5,
                "blocks": {
                    "Ghatshila": {"lat": 22.5800, "lon": 86.4800, "villages": [{"name": "Galudih", "lat": 22.64, "lon": 86.40, "elevation": 115}, {"name": "Mouhanda", "lat": 22.55, "lon": 86.45, "elevation": 122}]},
                    "Potka": {"lat": 22.6200, "lon": 86.2300, "villages": [{"name": "Jaduguda Rural", "lat": 22.65, "lon": 86.35, "elevation": 145}, {"name": "Haldipokhar", "lat": 22.60, "lon": 86.21, "elevation": 152}]}
                }
            },
            "Dhanbad": {
                "lat": 23.7957, "lon": 86.4304, "climatology_mm": 15.0,
                "blocks": {
                    "Govindpur": {"lat": 23.8300, "lon": 86.5200, "villages": [{"name": "Barwadda", "lat": 23.85, "lon": 86.44, "elevation": 218}, {"name": "Tundi", "lat": 23.98, "lon": 86.45, "elevation": 235}]}
                }
            }
        }
    },
    "Karnataka": {
        "lat": 15.3173, "lon": 75.7139,
        "districts": {
            "Bengaluru Urban": {
                "lat": 12.9716, "lon": 77.5946, "climatology_mm": 2.5,
                "blocks": {
                    "Bengaluru North": {"lat": 13.0400, "lon": 77.5800, "villages": [{"name": "Yelahanka Rural", "lat": 13.045, "lon": 77.585, "elevation": 915}, {"name": "Hesaraghatta Kasba", "lat": 13.032, "lon": 77.572, "elevation": 912}]},
                    "Bengaluru South": {"lat": 12.9100, "lon": 77.5700, "villages": [{"name": "Anekal Rural", "lat": 12.71, "lon": 77.69, "elevation": 905}, {"name": "Sarjapura", "lat": 12.86, "lon": 77.78, "elevation": 890}]}
                }
            },
            "Mysuru": {
                "lat": 12.2958, "lon": 76.6394, "climatology_mm": 3.8,
                "blocks": {
                    "Nanjangud": {"lat": 12.1200, "lon": 76.6800, "villages": [{"name": "Hullahalli", "lat": 12.18, "lon": 76.54, "elevation": 678}, {"name": "Kowlande", "lat": 12.08, "lon": 76.78, "elevation": 692}]},
                    "Hunsur": {"lat": 12.3100, "lon": 76.2900, "villages": [{"name": "Bilikere", "lat": 12.33, "lon": 76.43, "elevation": 805}, {"name": "Periyapatna Rural", "lat": 12.34, "lon": 76.10, "elevation": 840}]}
                }
            },
            "Dharwad (Hubballi)": {
                "lat": 15.3647, "lon": 75.1240, "climatology_mm": 2.0,
                "blocks": {
                    "Navalgund": {"lat": 15.5600, "lon": 75.3600, "villages": [{"name": "Annigeri", "lat": 15.43, "lon": 75.43, "elevation": 624}, {"name": "Alagawadi", "lat": 15.61, "lon": 75.32, "elevation": 618}]}
                }
            },
            "Dakshina Kannada (Mangaluru)": {
                "lat": 12.9141, "lon": 74.8560, "climatology_mm": 1.2,
                "blocks": {
                    "Bantwal": {"lat": 12.8900, "lon": 75.0300, "villages": [{"name": "Panemangalore", "lat": 12.88, "lon": 75.01, "elevation": 32}, {"name": "Vittal", "lat": 12.76, "lon": 75.11, "elevation": 58}]}
                }
            }
        }
    },
    "Kerala": {
        "lat": 10.8505, "lon": 76.2711,
        "districts": {
            "Thiruvananthapuram": {
                "lat": 8.5241, "lon": 76.9366, "climatology_mm": 18.5,
                "blocks": {
                    "Neyyattinkara": {"lat": 8.4000, "lon": 77.0800, "villages": [{"name": "Balaramapuram", "lat": 8.43, "lon": 77.04, "elevation": 28}, {"name": "Parassala", "lat": 8.34, "lon": 77.15, "elevation": 42}]},
                    "Nedumangad": {"lat": 8.6000, "lon": 77.0000, "villages": [{"name": "Vithura", "lat": 8.67, "lon": 77.10, "elevation": 140}, {"name": "Palode", "lat": 8.70, "lon": 77.03, "elevation": 110}]}
                }
            },
            "Ernakulam (Kochi)": {
                "lat": 9.9312, "lon": 76.2673, "climatology_mm": 12.0,
                "blocks": {
                    "Aluva": {"lat": 10.1100, "lon": 76.3500, "villages": [{"name": "Angamaly Rural", "lat": 10.19, "lon": 76.38, "elevation": 18}, {"name": "Kalady", "lat": 10.17, "lon": 76.43, "elevation": 22}]},
                    "Muvattupuzha": {"lat": 9.9800, "lon": 76.5800, "villages": [{"name": "Piravom", "lat": 9.87, "lon": 76.49, "elevation": 28}, {"name": "Kothamangalam Rural", "lat": 10.06, "lon": 76.62, "elevation": 45}]}
                }
            },
            "Kozhikode": {
                "lat": 11.2588, "lon": 75.7804, "climatology_mm": 5.4,
                "blocks": {
                    "Vadakara": {"lat": 11.6000, "lon": 75.5900, "villages": [{"name": "Chorode", "lat": 11.63, "lon": 75.57, "elevation": 12}, {"name": "Nadapuram", "lat": 11.68, "lon": 75.65, "elevation": 35}]}
                }
            },
            "Wayanad": {
                "lat": 11.6854, "lon": 76.1320, "climatology_mm": 10.5,
                "blocks": {
                    "Sulthan Bathery": {"lat": 11.6600, "lon": 76.2600, "villages": [{"name": "Meenangadi", "lat": 11.66, "lon": 76.17, "elevation": 890}, {"name": "Ambalavayal", "lat": 11.61, "lon": 76.21, "elevation": 940}]}
                }
            }
        }
    },
    "Madhya Pradesh": {
        "lat": 22.9734, "lon": 78.6569,
        "districts": {
            "Bhopal": {
                "lat": 23.2599, "lon": 77.4126, "climatology_mm": 13.5,
                "blocks": {
                    "Berasia": {"lat": 23.6300, "lon": 77.4300, "villages": [{"name": "Nazirabad", "lat": 23.70, "lon": 77.48, "elevation": 490}, {"name": "Runaha", "lat": 23.58, "lon": 77.38, "elevation": 495}]},
                    "Phanda": {"lat": 23.2300, "lon": 77.2900, "villages": [{"name": "Bairagarh Kalan", "lat": 23.25, "lon": 77.31, "elevation": 515}, {"name": "Kolar Rural", "lat": 23.16, "lon": 77.41, "elevation": 520}]}
                }
            },
            "Indore": {
                "lat": 22.7196, "lon": 75.8577, "climatology_mm": 8.4,
                "blocks": {
                    "Mhow (Ambedkar Nagar)": {"lat": 22.5500, "lon": 75.7600, "villages": [{"name": "Hasalpur", "lat": 22.52, "lon": 75.78, "elevation": 575}, {"name": "Manpur", "lat": 22.43, "lon": 75.63, "elevation": 560}]},
                    "Sanwer": {"lat": 22.9800, "lon": 75.8300, "villages": [{"name": "Dharmat", "lat": 23.04, "lon": 75.75, "elevation": 535}, {"name": "Kshipra", "lat": 22.92, "lon": 75.99, "elevation": 542}]}
                }
            },
            "Jabalpur": {
                "lat": 23.1815, "lon": 79.9864, "climatology_mm": 21.0,
                "blocks": {
                    "Sihora": {"lat": 23.4800, "lon": 80.1100, "villages": [{"name": "Majholi", "lat": 23.51, "lon": 79.92, "elevation": 395}, {"name": "Gosawal", "lat": 23.45, "lon": 80.16, "elevation": 388}]},
                    "Patan": {"lat": 23.2800, "lon": 79.7000, "villages": [{"name": "Shahpura Bhitoni", "lat": 23.14, "lon": 79.66, "elevation": 382}, {"name": "Belkheda", "lat": 23.10, "lon": 79.52, "elevation": 378}]}
                }
            },
            "Gwalior": {
                "lat": 26.2183, "lon": 78.1828, "climatology_mm": 15.2,
                "blocks": {
                    "Dabra": {"lat": 25.8900, "lon": 78.3300, "villages": [{"name": "Bhitarwar", "lat": 25.80, "lon": 78.12, "elevation": 210}, {"name": "Antari", "lat": 26.04, "lon": 78.28, "elevation": 215}]}
                }
            }
        }
    },
    "Maharashtra": {
        "lat": 19.7515, "lon": 75.7139,
        "districts": {
            "Nagpur": {
                "lat": 21.1458, "lon": 79.0882, "climatology_mm": 12.2,
                "blocks": {
                    "Saoner": {"lat": 21.3800, "lon": 78.9100, "villages": [{"name": "Kelod", "lat": 21.46, "lon": 78.88, "elevation": 312}, {"name": "Khapa", "lat": 21.42, "lon": 79.01, "elevation": 305}]},
                    "Katol": {"lat": 21.2800, "lon": 78.5800, "villages": [{"name": "Kondhali", "lat": 21.18, "lon": 78.61, "elevation": 385}, {"name": "Narkhed", "lat": 21.36, "lon": 78.53, "elevation": 395}]},
                    "Hingna": {"lat": 21.0700, "lon": 78.9600, "villages": [{"name": "Wadi Rural", "lat": 21.14, "lon": 78.98, "elevation": 288}, {"name": "Takalghat", "lat": 20.95, "lon": 78.91, "elevation": 295}]},
                    "Kalmeshwar": {"lat": 21.2300, "lon": 78.9100, "villages": [{"name": "Dhapewada", "lat": 21.27, "lon": 78.89, "elevation": 320}, {"name": "Mohpa", "lat": 21.32, "lon": 78.82, "elevation": 332}]}
                }
            },
            "Wardha": {
                "lat": 20.7453, "lon": 78.6022, "climatology_mm": 11.5,
                "blocks": {
                    "Sevagram": {"lat": 20.7100, "lon": 78.6600, "villages": [{"name": "Paunar", "lat": 20.78, "lon": 78.67, "elevation": 242}, {"name": "Sindi", "lat": 20.81, "lon": 78.88, "elevation": 248}]},
                    "Hinganghat": {"lat": 20.5600, "lon": 78.8400, "villages": [{"name": "Samudrapur", "lat": 20.61, "lon": 79.04, "elevation": 228}, {"name": "Pohna", "lat": 20.51, "lon": 78.75, "elevation": 234}]}
                }
            },
            "Pune": {
                "lat": 18.5204, "lon": 73.8567, "climatology_mm": 1.8,
                "blocks": {
                    "Baramati": {"lat": 18.1500, "lon": 74.5800, "villages": [{"name": "Malegaon Khurd", "lat": 18.17, "lon": 74.52, "elevation": 548}, {"name": "Supe", "lat": 18.33, "lon": 74.38, "elevation": 612}]},
                    "Haveli": {"lat": 18.4800, "lon": 73.9100, "villages": [{"name": "Wagholi", "lat": 18.58, "lon": 73.98, "elevation": 575}, {"name": "Khadakwasla Rural", "lat": 18.43, "lon": 73.76, "elevation": 585}]}
                }
            },
            "Nashik": {
                "lat": 19.9975, "lon": 73.7898, "climatology_mm": 2.2,
                "blocks": {
                    "Niphad": {"lat": 20.0800, "lon": 74.1100, "villages": [{"name": "Pimpalgaon Baswant", "lat": 20.17, "lon": 73.98, "elevation": 560}, {"name": "Lasalgaon", "lat": 20.14, "lon": 74.23, "elevation": 572}]},
                    "Dindori": {"lat": 20.2000, "lon": 73.8300, "villages": [{"name": "Vani Kasba", "lat": 20.32, "lon": 73.89, "elevation": 630}, {"name": "Ojhar", "lat": 20.10, "lon": 73.92, "elevation": 570}]}
                }
            },
            "Chhatrapati Sambhajinagar (Aurangabad)": {
                "lat": 19.8762, "lon": 75.3433, "climatology_mm": 4.5,
                "blocks": {
                    "Paithan": {"lat": 19.4800, "lon": 75.3800, "villages": [{"name": "Bidkin", "lat": 19.68, "lon": 75.32, "elevation": 520}, {"name": "Pachod", "lat": 19.46, "lon": 75.56, "elevation": 505}]}
                }
            },
            "Mumbai Suburban": {
                "lat": 19.0760, "lon": 72.8777, "climatology_mm": 0.6,
                "blocks": {
                    "Borivali": {"lat": 19.2300, "lon": 72.8600, "villages": [{"name": "Gorai Village", "lat": 19.24, "lon": 72.78, "elevation": 8}, {"name": "Manori", "lat": 19.21, "lon": 72.79, "elevation": 6}]}
                }
            }
        }
    },
    "Manipur": {
        "lat": 24.6637, "lon": 93.9063,
        "districts": {
            "Imphal West": {
                "lat": 24.8170, "lon": 93.9368, "climatology_mm": 11.0,
                "blocks": {
                    "Lamphelpat": {"lat": 24.8200, "lon": 93.9100, "villages": [{"name": "Iroisemba", "lat": 24.83, "lon": 93.89, "elevation": 785}, {"name": "Langol", "lat": 24.85, "lon": 93.90, "elevation": 810}]}
                }
            },
            "Bishnupur": {
                "lat": 24.6324, "lon": 93.7637, "climatology_mm": 12.5,
                "blocks": {
                    "Moirang": {"lat": 24.5000, "lon": 93.7700, "villages": [{"name": "Sendra Loktak", "lat": 24.51, "lon": 93.80, "elevation": 772}, {"name": "Kumbi", "lat": 24.45, "lon": 93.81, "elevation": 770}]}
                }
            }
        }
    },
    "Meghalaya": {
        "lat": 25.4670, "lon": 91.3662,
        "districts": {
            "East Khasi Hills (Shillong)": {
                "lat": 25.5788, "lon": 91.8933, "climatology_mm": 14.8,
                "blocks": {
                    "Mylliem": {"lat": 25.5100, "lon": 91.8300, "villages": [{"name": "Mawkriah", "lat": 25.53, "lon": 91.81, "elevation": 1640}, {"name": "Pomlakrai", "lat": 25.50, "lon": 91.86, "elevation": 1720}]},
                    "Sohra (Cherrapunji)": {"lat": 25.2700, "lon": 91.7300, "villages": [{"name": "Nongriat", "lat": 25.25, "lon": 91.67, "elevation": 810}, {"name": "Mawsmai", "lat": 25.24, "lon": 91.72, "elevation": 1280}]}
                }
            },
            "West Garo Hills (Tura)": {
                "lat": 25.5141, "lon": 90.2033, "climatology_mm": 9.2,
                "blocks": {
                    "Rongram": {"lat": 25.5800, "lon": 90.2400, "villages": [{"name": "Asanang", "lat": 25.60, "lon": 90.27, "elevation": 410}, {"name": "Chibragre", "lat": 25.56, "lon": 90.22, "elevation": 360}]}
                }
            }
        }
    },
    "Mizoram": {
        "lat": 23.1645, "lon": 92.9376,
        "districts": {
            "Aizawl": {
                "lat": 23.7271, "lon": 92.7176, "climatology_mm": 10.5,
                "blocks": {
                    "Tlangnuam": {"lat": 23.7000, "lon": 92.7100, "villages": [{"name": "Tanhril", "lat": 23.73, "lon": 92.67, "elevation": 890}, {"name": "Muallungthu", "lat": 23.65, "lon": 92.74, "elevation": 940}]},
                    "Darlawn": {"lat": 23.9700, "lon": 92.9000, "villages": [{"name": "Sawleng", "lat": 23.94, "lon": 92.93, "elevation": 1080}, {"name": "Khawruhlian", "lat": 23.90, "lon": 92.86, "elevation": 1020}]}
                }
            },
            "Lunglei": {
                "lat": 22.8671, "lon": 92.7656, "climatology_mm": 11.2,
                "blocks": {
                    "Hnahthial": {"lat": 22.9600, "lon": 92.9300, "villages": [{"name": "Thingsai", "lat": 22.88, "lon": 93.04, "elevation": 950}, {"name": "Cherhlun", "lat": 22.81, "lon": 93.09, "elevation": 1120}]}
                }
            }
        }
    },
    "Nagaland": {
        "lat": 26.1584, "lon": 94.5624,
        "districts": {
            "Kohima": {
                "lat": 25.6751, "lon": 94.1086, "climatology_mm": 16.4,
                "blocks": {
                    "Jakhama": {"lat": 25.5900, "lon": 94.1300, "villages": [{"name": "Viswema", "lat": 25.55, "lon": 94.16, "elevation": 1650}, {"name": "Khonoma", "lat": 25.65, "lon": 94.02, "elevation": 1520}]},
                    "Chiephobozou": {"lat": 25.8000, "lon": 94.1800, "villages": [{"name": "Tseminyu Kasba", "lat": 25.91, "lon": 94.21, "elevation": 1420}, {"name": "Chiechama", "lat": 25.76, "lon": 94.14, "elevation": 1380}]}
                }
            },
            "Dimapur": {
                "lat": 25.9094, "lon": 93.7266, "climatology_mm": 14.0,
                "blocks": {
                    "Chumukedima": {"lat": 25.7900, "lon": 93.7700, "villages": [{"name": "Medziphema", "lat": 25.75, "lon": 93.86, "elevation": 320}, {"name": "Diphupar", "lat": 25.84, "lon": 93.75, "elevation": 210}]}
                }
            }
        }
    },
    "Odisha": {
        "lat": 20.9517, "lon": 85.0985,
        "districts": {
            "Khordha (Bhubaneswar)": {
                "lat": 20.2961, "lon": 85.8245, "climatology_mm": 12.8,
                "blocks": {
                    "Jatni": {"lat": 20.1600, "lon": 85.7000, "villages": [{"name": "Kudiary", "lat": 20.15, "lon": 85.69, "elevation": 42}, {"name": "Gohira", "lat": 20.18, "lon": 85.73, "elevation": 45}]},
                    "Balianta": {"lat": 20.2600, "lon": 85.9100, "villages": [{"name": "Hanspal", "lat": 20.31, "lon": 85.88, "elevation": 35}, {"name": "Pratapsasan", "lat": 20.22, "lon": 85.89, "elevation": 30}]}
                }
            },
            "Puri (Coastal Cyclone Belt)": {
                "lat": 19.8135, "lon": 85.8312, "climatology_mm": 9.5,
                "blocks": {
                    "Konark": {"lat": 19.8800, "lon": 86.1100, "villages": [{"name": "Chandrabhaga", "lat": 19.87, "lon": 86.12, "elevation": 6}, {"name": "Kuruma", "lat": 19.92, "lon": 86.08, "elevation": 12}]},
                    "Brahmagiri": {"lat": 19.8000, "lon": 85.6500, "villages": [{"name": "Alarnath", "lat": 19.78, "lon": 85.64, "elevation": 8}, {"name": "Satapada (Chilika)", "lat": 19.67, "lon": 85.43, "elevation": 4}]}
                }
            },
            "Ganjam (Berhampur)": {
                "lat": 19.3149, "lon": 84.7941, "climatology_mm": 8.0,
                "blocks": {
                    "Chhatrapur": {"lat": 19.3500, "lon": 84.9800, "villages": [{"name": "Aryapalli", "lat": 19.31, "lon": 85.01, "elevation": 8}, {"name": "Agasti Nuagaon", "lat": 19.38, "lon": 84.95, "elevation": 15}]},
                    "Gopalpur": {"lat": 19.2600, "lon": 84.9000, "villages": [{"name": "Haripur", "lat": 19.28, "lon": 84.87, "elevation": 12}, {"name": "Mansurkota", "lat": 19.24, "lon": 84.92, "elevation": 7}]}
                }
            },
            "Balasore (Bhadrak Coast)": {
                "lat": 21.4934, "lon": 86.9135, "climatology_mm": 14.5,
                "blocks": {
                    "Chandipur": {"lat": 21.4600, "lon": 87.0100, "villages": [{"name": "Balaramgadi", "lat": 21.47, "lon": 87.03, "elevation": 4}, {"name": "Kasafal", "lat": 21.55, "lon": 87.12, "elevation": 6}]}
                }
            }
        }
    },
    "Punjab": {
        "lat": 31.1471, "lon": 75.3412,
        "districts": {
            "Ludhiana": {
                "lat": 30.9010, "lon": 75.8573, "climatology_mm": 28.5,
                "blocks": {
                    "Jagraon": {"lat": 30.7800, "lon": 75.4800, "villages": [{"name": "Sidhwan Bet", "lat": 30.88, "lon": 75.44, "elevation": 234}, {"name": "Chowkiman", "lat": 30.82, "lon": 75.56, "elevation": 238}]},
                    "Khanna": {"lat": 30.7000, "lon": 76.2200, "villages": [{"name": "Samrala Rural", "lat": 30.83, "lon": 76.19, "elevation": 248}, {"name": "Payal", "lat": 30.72, "lon": 76.05, "elevation": 242}]}
                }
            },
            "Amritsar": {
                "lat": 31.6340, "lon": 74.8723, "climatology_mm": 32.0,
                "blocks": {
                    "Ajnala": {"lat": 31.8400, "lon": 74.7600, "villages": [{"name": "Ramdas", "lat": 31.97, "lon": 74.92, "elevation": 228}, {"name": "Chogawan", "lat": 31.78, "lon": 74.62, "elevation": 222}]},
                    "Attari": {"lat": 31.6000, "lon": 74.6000, "villages": [{"name": "Wagah Border Rural", "lat": 31.61, "lon": 74.57, "elevation": 225}, {"name": "Khasa", "lat": 31.62, "lon": 74.72, "elevation": 230}]}
                }
            },
            "Jalandhar": {
                "lat": 31.3260, "lon": 75.5762, "climatology_mm": 30.0,
                "blocks": {
                    "Nakodar": {"lat": 31.1300, "lon": 75.4700, "villages": [{"name": "Shahkot", "lat": 31.08, "lon": 75.34, "elevation": 226}, {"name": "Nurmahal", "lat": 31.09, "lon": 75.59, "elevation": 232}]}
                }
            }
        }
    },
    "Rajasthan": {
        "lat": 27.0238, "lon": 74.2179,
        "districts": {
            "Jaipur": {
                "lat": 26.9124, "lon": 75.7873, "climatology_mm": 8.5,
                "blocks": {
                    "Chomu": {"lat": 27.1700, "lon": 75.7200, "villages": [{"name": "Samode", "lat": 27.20, "lon": 75.81, "elevation": 435}, {"name": "Morija", "lat": 27.21, "lon": 75.69, "elevation": 428}]},
                    "Sanganer": {"lat": 26.8200, "lon": 75.7900, "villages": [{"name": "Watika", "lat": 26.74, "lon": 75.82, "elevation": 382}, {"name": "Mahapura", "lat": 26.85, "lon": 75.68, "elevation": 395}]},
                    "Kotputli": {"lat": 27.7000, "lon": 76.2000, "villages": [{"name": "Paota", "lat": 27.58, "lon": 76.12, "elevation": 348}, {"name": "Bansur Rural", "lat": 27.69, "lon": 76.35, "elevation": 355}]}
                }
            },
            "Jodhpur (Marwar)": {
                "lat": 26.2389, "lon": 73.0243, "climatology_mm": 3.2,
                "blocks": {
                    "Bilara": {"lat": 26.1800, "lon": 73.7100, "villages": [{"name": "Piparcity", "lat": 26.38, "lon": 73.54, "elevation": 248}, {"name": "Bhavis", "lat": 26.15, "lon": 73.65, "elevation": 262}]},
                    "Osian": {"lat": 26.7200, "lon": 72.9000, "villages": [{"name": "Tiwari", "lat": 26.54, "lon": 72.98, "elevation": 275}, {"name": "Balesar", "lat": 26.41, "lon": 72.48, "elevation": 285}]}
                }
            },
            "Udaipur (Mewar)": {
                "lat": 24.5854, "lon": 73.7125, "climatology_mm": 4.5,
                "blocks": {
                    "Mavli": {"lat": 24.7800, "lon": 73.9800, "villages": [{"name": "Fatehnagar", "lat": 24.87, "lon": 74.08, "elevation": 525}, {"name": "Sanwar", "lat": 24.79, "lon": 74.02, "elevation": 532}]},
                    "Girwa": {"lat": 24.5200, "lon": 73.7500, "villages": [{"name": "Nai Village", "lat": 24.55, "lon": 73.63, "elevation": 595}, {"name": "Kurabad", "lat": 24.46, "lon": 73.96, "elevation": 540}]}
                }
            },
            "Kota (Hadoti)": {
                "lat": 25.2138, "lon": 75.8648, "climatology_mm": 6.8,
                "blocks": {
                    "Sangod": {"lat": 24.9200, "lon": 76.2800, "villages": [{"name": "Kanwas", "lat": 24.89, "lon": 76.15, "elevation": 275}, {"name": "Bapawar Kalan", "lat": 24.96, "lon": 76.35, "elevation": 268}]}
                }
            }
        }
    },
    "Sikkim": {
        "lat": 27.5330, "lon": 88.5122,
        "districts": {
            "East Sikkim (Gangtok)": {
                "lat": 27.3389, "lon": 88.6065, "climatology_mm": 28.5,
                "blocks": {
                    "Ranka": {"lat": 27.3100, "lon": 88.5700, "villages": [{"name": "Rey Mindu", "lat": 27.32, "lon": 88.59, "elevation": 1450}, {"name": "Lingdum", "lat": 27.34, "lon": 88.56, "elevation": 1520}]},
                    "Pakyong": {"lat": 27.2400, "lon": 88.5900, "villages": [{"name": "Rorathang", "lat": 27.18, "lon": 88.62, "elevation": 850}, {"name": "Dugalakha", "lat": 27.22, "lon": 88.63, "elevation": 1100}]}
                }
            },
            "South Sikkim (Namchi)": {
                "lat": 27.1667, "lon": 88.3667, "climatology_mm": 22.0,
                "blocks": {
                    "Ravangla": {"lat": 27.3000, "lon": 88.3600, "villages": [{"name": "Borong", "lat": 27.32, "lon": 88.38, "elevation": 1780}, {"name": "Kewzing", "lat": 27.28, "lon": 88.34, "elevation": 1640}]}
                }
            }
        }
    },
    "Tamil Nadu": {
        "lat": 11.1271, "lon": 78.6569,
        "districts": {
            "Chennai": {
                "lat": 13.0827, "lon": 80.2707, "climatology_mm": 25.5,
                "blocks": {
                    "Tambaram (Chengalpattu)": {"lat": 12.9200, "lon": 80.1200, "villages": [{"name": "Medavakkam Rural", "lat": 12.91, "lon": 80.18, "elevation": 24}, {"name": "Mudichur", "lat": 12.90, "lon": 80.08, "elevation": 22}]},
                    "Ambattur": {"lat": 13.1100, "lon": 80.1500, "villages": [{"name": "Avadi Rural", "lat": 13.11, "lon": 80.09, "elevation": 30}, {"name": "Madhavaram Rural", "lat": 13.15, "lon": 80.23, "elevation": 18}]}
                }
            },
            "Coimbatore": {
                "lat": 11.0168, "lon": 76.9558, "climatology_mm": 5.4,
                "blocks": {
                    "Pollachi": {"lat": 10.6600, "lon": 77.0100, "villages": [{"name": "Anaimalai", "lat": 10.58, "lon": 76.93, "elevation": 285}, {"name": "Kottur", "lat": 10.54, "lon": 76.98, "elevation": 310}, {"name": "Negamam", "lat": 10.74, "lon": 77.10, "elevation": 340}]},
                    "Mettupalayam": {"lat": 11.3000, "lon": 76.9500, "villages": [{"name": "Karamadai", "lat": 11.24, "lon": 76.96, "elevation": 390}, {"name": "Sirumugai", "lat": 11.33, "lon": 77.02, "elevation": 345}]}
                }
            },
            "Madurai": {
                "lat": 9.9252, "lon": 78.1198, "climatology_mm": 11.8,
                "blocks": {
                    "Melur": {"lat": 10.0300, "lon": 78.3300, "villages": [{"name": "Alagarkoil", "lat": 10.08, "lon": 78.22, "elevation": 180}, {"name": "Kottampatti", "lat": 10.15, "lon": 78.43, "elevation": 152}]},
                    "Usilampatti": {"lat": 9.9700, "lon": 77.7900, "villages": [{"name": "Sedapatti", "lat": 9.81, "lon": 77.78, "elevation": 195}, {"name": "Chellampatti", "lat": 9.99, "lon": 77.92, "elevation": 175}]}
                }
            },
            "Thanjavur (Cauvery Delta)": {
                "lat": 10.7870, "lon": 79.1378, "climatology_mm": 18.0,
                "blocks": {
                    "Kumbakonam": {"lat": 10.9600, "lon": 79.3800, "villages": [{"name": "Thiruvidaimarudur", "lat": 10.99, "lon": 79.46, "elevation": 28}, {"name": "Swamimalai", "lat": 10.95, "lon": 79.32, "elevation": 32}]},
                    "Papanasam": {"lat": 10.9200, "lon": 79.2800, "villages": [{"name": "Ayyampet", "lat": 10.90, "lon": 79.20, "elevation": 35}, {"name": "Rajagiri", "lat": 10.94, "lon": 79.26, "elevation": 30}]}
                }
            },
            "Kanyakumari (Nagercoil)": {
                "lat": 8.0883, "lon": 77.5385, "climatology_mm": 16.2,
                "blocks": {
                    "Agastheeswaram": {"lat": 8.1200, "lon": 77.5200, "villages": [{"name": "Kovalam Rural", "lat": 8.09, "lon": 77.55, "elevation": 8}, {"name": "Suchindram", "lat": 8.15, "lon": 77.46, "elevation": 18}]}
                }
            }
        }
    },
    "Telangana": {
        "lat": 18.1124, "lon": 79.0193,
        "districts": {
            "Hyderabad": {
                "lat": 17.3850, "lon": 78.4867, "climatology_mm": 4.5,
                "blocks": {
                    "Secunderabad": {"lat": 17.4400, "lon": 78.5000, "villages": [{"name": "Alwal Rural", "lat": 17.50, "lon": 78.53, "elevation": 545}, {"name": "Malkajgiri Rural", "lat": 17.45, "lon": 78.53, "elevation": 535}]},
                    "Charminar": {"lat": 17.3600, "lon": 78.4700, "villages": [{"name": "Falaknuma", "lat": 17.33, "lon": 78.46, "elevation": 525}, {"name": "Chandrayangutta", "lat": 17.31, "lon": 78.48, "elevation": 515}]}
                }
            },
            "Warangal": {
                "lat": 17.9689, "lon": 79.5941, "climatology_mm": 6.8,
                "blocks": {
                    "Hanamkonda": {"lat": 18.0100, "lon": 79.5600, "villages": [{"name": "Kazipet Rural", "lat": 17.98, "lon": 79.51, "elevation": 288}, {"name": "Hasanparthy", "lat": 18.08, "lon": 79.54, "elevation": 295}]},
                    "Narsampet": {"lat": 17.9300, "lon": 79.8900, "villages": [{"name": "Pakhal Lake Rural", "lat": 17.96, "lon": 79.98, "elevation": 280}, {"name": "Chennaraopet", "lat": 17.88, "lon": 79.92, "elevation": 272}]}
                }
            },
            "Karimnagar": {
                "lat": 18.4386, "lon": 79.1288, "climatology_mm": 5.2,
                "blocks": {
                    "Huzurabad": {"lat": 18.1900, "lon": 79.4000, "villages": [{"name": "Jammikunta", "lat": 18.28, "lon": 79.47, "elevation": 242}, {"name": "Kamalapur", "lat": 18.15, "lon": 79.52, "elevation": 255}]}
                }
            }
        }
    },
    "Tripura": {
        "lat": 23.9408, "lon": 91.9882,
        "districts": {
            "West Tripura (Agartala)": {
                "lat": 23.8315, "lon": 91.2868, "climatology_mm": 12.0,
                "blocks": {
                    "Mohanpur": {"lat": 23.9700, "lon": 91.3700, "villages": [{"name": "Lembucherra", "lat": 23.91, "lon": 91.31, "elevation": 32}, {"name": "Sidhai", "lat": 23.99, "lon": 91.35, "elevation": 28}]},
                    "Dukli": {"lat": 23.7800, "lon": 91.2900, "villages": [{"name": "Surjamaninagar", "lat": 23.76, "lon": 91.26, "elevation": 24}, {"name": "Ranirbazar", "lat": 23.82, "lon": 91.36, "elevation": 26}]}
                }
            },
            "Gomati (Udaipur)": {
                "lat": 23.5333, "lon": 91.4833, "climatology_mm": 13.5,
                "blocks": {
                    "Matabari": {"lat": 23.5100, "lon": 91.5000, "villages": [{"name": "Kakraban", "lat": 23.48, "lon": 91.43, "elevation": 35}, {"name": "Killa", "lat": 23.58, "lon": 91.54, "elevation": 42}]}
                }
            }
        }
    },
    "Uttarakhand": {
        "lat": 30.0668, "lon": 79.0193,
        "districts": {
            "Dehradun": {
                "lat": 30.3165, "lon": 78.0322, "climatology_mm": 52.0,
                "blocks": {
                    "Rishikesh": {"lat": 30.1000, "lon": 78.3000, "villages": [{"name": "Rani Pokhari", "lat": 30.17, "lon": 78.22, "elevation": 480}, {"name": "Bhogpur", "lat": 30.13, "lon": 78.18, "elevation": 495}]},
                    "Vikasnagar": {"lat": 30.4500, "lon": 77.7700, "villages": [{"name": "Dakpathar", "lat": 30.50, "lon": 77.78, "elevation": 465}, {"name": "Herbertpur", "lat": 30.44, "lon": 77.74, "elevation": 450}]},
                    "Mussoorie Rural": {"lat": 30.4598, "lon": 78.0644, "villages": [{"name": "Barlowganj", "lat": 30.43, "lon": 78.08, "elevation": 1780}, {"name": "Kempty Fall Village", "lat": 30.48, "lon": 78.04, "elevation": 1420}]}
                }
            },
            "Haridwar": {
                "lat": 29.9457, "lon": 78.1642, "climatology_mm": 38.5,
                "blocks": {
                    "Roorkee": {"lat": 29.8700, "lon": 77.8900, "villages": [{"name": "Bhagwanpur", "lat": 29.94, "lon": 77.81, "elevation": 268}, {"name": "Manglaur", "lat": 29.79, "lon": 77.87, "elevation": 264}]},
                    "Laksar": {"lat": 29.7500, "lon": 78.0200, "villages": [{"name": "Sultanpur", "lat": 29.77, "lon": 78.07, "elevation": 255}, {"name": "Khanpur", "lat": 29.68, "lon": 78.08, "elevation": 252}]}
                }
            },
            "Nainital": {
                "lat": 29.3919, "lon": 79.4542, "climatology_mm": 68.0,
                "blocks": {
                    "Haldwani": {"lat": 29.2200, "lon": 79.5200, "villages": [{"name": "Kathgodam Rural", "lat": 29.27, "lon": 79.53, "elevation": 520}, {"name": "Lalkuan", "lat": 29.08, "lon": 79.51, "elevation": 375}]},
                    "Ramnagar": {"lat": 29.4000, "lon": 79.1300, "villages": [{"name": "Corbett Buffer Village", "lat": 29.44, "lon": 79.11, "elevation": 385}, {"name": "Pirumadara", "lat": 29.34, "lon": 79.08, "elevation": 340}]}
                }
            }
        }
    },
    "West Bengal": {
        "lat": 22.9868, "lon": 87.8550,
        "districts": {
            "Kolkata": {
                "lat": 22.5726, "lon": 88.3639, "climatology_mm": 13.5,
                "blocks": {
                    "South 24 Parganas (Alipore)": {"lat": 22.5300, "lon": 88.3300, "villages": [{"name": "Budge Budge Rural", "lat": 22.48, "lon": 88.18, "elevation": 9}, {"name": "Bishnupur (Diamond Harbour)", "lat": 22.38, "lon": 88.27, "elevation": 8}]},
                    "Sundarbans Coastal": {"lat": 21.9500, "lon": 88.8500, "villages": [{"name": "Gosaba", "lat": 22.16, "lon": 88.81, "elevation": 4}, {"name": "Canning Rural", "lat": 22.31, "lon": 88.66, "elevation": 6}, {"name": "Kakdwip", "lat": 21.87, "lon": 88.19, "elevation": 5}]}
                }
            },
            "North 24 Parganas (Barasat)": {
                "lat": 22.7200, "lon": 88.4800, "climatology_mm": 14.0,
                "blocks": {
                    "Habra": {"lat": 22.8400, "lon": 88.6300, "villages": [{"name": "Ashoknagar", "lat": 22.83, "lon": 88.61, "elevation": 12}, {"name": "Maslandapur", "lat": 22.88, "lon": 88.67, "elevation": 11}]},
                    "Basirhat (Border / Delta)": {"lat": 22.6600, "lon": 88.8900, "villages": [{"name": "Hingalganj", "lat": 22.47, "lon": 88.98, "elevation": 5}, {"name": "Hasnabad", "lat": 22.57, "lon": 88.92, "elevation": 6}]}
                }
            },
            "Darjeeling (North Bengal)": {
                "lat": 27.0410, "lon": 88.2663, "climatology_mm": 24.5,
                "blocks": {
                    "Kurseong": {"lat": 26.8800, "lon": 88.2800, "villages": [{"name": "Makaibari Tea Estate", "lat": 26.86, "lon": 88.27, "elevation": 1450}, {"name": "Tindharia", "lat": 26.85, "lon": 88.33, "elevation": 860}]},
                    "Siliguri": {"lat": 26.7200, "lon": 88.4200, "villages": [{"name": "Matigara", "lat": 26.71, "lon": 88.38, "elevation": 125}, {"name": "Naxalbari", "lat": 26.68, "lon": 88.22, "elevation": 150}]}
                }
            },
            "Purba Medinipur (Digha Coast)": {
                "lat": 21.6266, "lon": 87.5074, "climatology_mm": 12.0,
                "blocks": {
                    "Contai (Kanthi)": {"lat": 21.7800, "lon": 87.7500, "villages": [{"name": "Digha Coastal Gram", "lat": 21.63, "lon": 87.52, "elevation": 6}, {"name": "Mandarmoni", "lat": 21.66, "lon": 87.60, "elevation": 5}]}
                }
            }
        }
    },
    "Delhi NCR": {
        "lat": 28.6139, "lon": 77.2090,
        "districts": {
            "New Delhi": {
                "lat": 28.6139, "lon": 77.2090, "climatology_mm": 19.5,
                "blocks": {
                    "Alipur (North)": {"lat": 28.8000, "lon": 77.1300, "villages": [{"name": "Bakoli Village", "lat": 28.805, "lon": 77.135, "elevation": 215}, {"name": "Khamnpur", "lat": 28.792, "lon": 77.122, "elevation": 214}]},
                    "Najafgarh (South West)": {"lat": 28.6100, "lon": 76.9800, "villages": [{"name": "Dichaon Kalan", "lat": 28.615, "lon": 76.985, "elevation": 218}, {"name": "Chhawla Village", "lat": 28.602, "lon": 76.972, "elevation": 216}]}
                }
            }
        }
    },
    "Jammu & Kashmir": {
        "lat": 33.7782, "lon": 76.5762,
        "districts": {
            "Srinagar (Kashmir Valley)": {
                "lat": 34.0837, "lon": 74.7973, "climatology_mm": 72.0,
                "blocks": {
                    "Ganderbal Rural": {"lat": 34.2200, "lon": 74.7800, "villages": [{"name": "Kangan", "lat": 34.26, "lon": 74.90, "elevation": 1810}, {"name": "Manasbal", "lat": 34.24, "lon": 74.68, "elevation": 1585}]},
                    "Pampore (Saffron Belt)": {"lat": 34.0200, "lon": 74.9300, "villages": [{"name": "Khrew", "lat": 34.02, "lon": 74.98, "elevation": 1620}, {"name": "Lethpora", "lat": 33.99, "lon": 74.97, "elevation": 1605}]}
                }
            },
            "Jammu": {
                "lat": 32.7266, "lon": 74.8570, "climatology_mm": 54.0,
                "blocks": {
                    "R.S. Pura (Basmati Belt)": {"lat": 32.6000, "lon": 74.7300, "villages": [{"name": "Suchetgarh Border", "lat": 32.57, "lon": 74.68, "elevation": 278}, {"name": "Miran Sahib", "lat": 32.63, "lon": 74.79, "elevation": 285}]},
                    "Akhnoor": {"lat": 32.9000, "lon": 74.7400, "villages": [{"name": "Khour", "lat": 32.92, "lon": 74.65, "elevation": 310}, {"name": "Jourian", "lat": 32.84, "lon": 74.58, "elevation": 298}]}
                }
            }
        }
    },
    "Ladakh": {
        "lat": 34.1526, "lon": 77.5771,
        "districts": {
            "Leh": {
                "lat": 34.1526, "lon": 77.5771, "climatology_mm": 12.0,
                "blocks": {
                    "Nubra": {"lat": 34.6900, "lon": 77.5600, "villages": [{"name": "Diskit", "lat": 34.54, "lon": 77.56, "elevation": 3140}, {"name": "Hunder", "lat": 34.58, "lon": 77.47, "elevation": 3160}]},
                    "Kharu": {"lat": 33.9200, "lon": 77.7200, "villages": [{"name": "Hemis Village", "lat": 33.91, "lon": 77.70, "elevation": 3520}, {"name": "Thiksey", "lat": 34.05, "lon": 77.66, "elevation": 3320}]}
                }
            }
        }
    }
}

print(f"Loaded {len(STATES_DATA)} complete states & territories.")
