import os
import sys

# Import the base states data
sys.path.insert(0, r"C:\Users\rajs6\.gemini\antigravity\scratch\weathergpt\scratch")
from generate_full_india_hierarchy import STATES_DATA

# Read existing UP districts and Maharashtra from original file
orig_file = r"C:\Users\rajs6\.gemini\antigravity\scratch\weathergpt\frontend\src\data\indiaAdminData.js"

with open(orig_file, "r", encoding="utf-8") as f:
    orig_content = f.read()

# Let's extract Uttar Pradesh from original file
up_start = orig_content.find('"Uttar Pradesh": {')
up_end = orig_content.find('"Maharashtra": {')
up_chunk = orig_content[up_start:up_end].strip()
if up_chunk.endswith(','):
    up_chunk = up_chunk[:-1]

# Now let's assemble the full JS file
out_file = r"C:\Users\rajs6\.gemini\antigravity\scratch\weathergpt\frontend\src\data\indiaAdminData.js"

import json

js_header = """// Pan-India Comprehensive Administrative Geo-Hierarchy Database
// Covers ALL 28 States and Major Union Territories
// Level 1: State / Union Territory
// Level 2: District
// Level 3: Block / Tehsil / Mandal (Sub-District)
// Level 4: Village / Gram Panchayat with micro-coordinates and climatological rainfall

export const INDIA_ADMIN_HIERARCHY = {
"""

with open(out_file, "w", encoding="utf-8") as out:
    out.write(js_header)
    
    # 1. Write Uttar Pradesh (with all 75 districts from ISRO NRSC VIC data)
    out.write("  " + up_chunk + ",\n\n")
    
    # 2. Write all other 27 states + UTs
    state_names = sorted(STATES_DATA.keys())
    for idx, sname in enumerate(state_names):
        sdata = STATES_DATA[sname]
        json_str = json.dumps({sname: sdata}, indent=2, ensure_ascii=False)
        # strip outer { and }
        inner = json_str.strip()[1:-1].strip()
        out.write("  " + inner)
        if idx < len(state_names) - 1:
            out.write(",\n\n")
        else:
            out.write("\n")
            
    out.write("};\n\n")
    
    # Write search index function
    footer = """// Flat search index for instant autocomplete across all levels
export const getAdminSearchIndex = () => {
  const list = [];
  Object.entries(INDIA_ADMIN_HIERARCHY).forEach(([stateName, stateData]) => {
    Object.entries(stateData.districts).forEach(([districtName, distData]) => {
      // Add district
      list.push({
        label: `${districtName}, ${stateName}`,
        level: 'district',
        name: districtName,
        district: districtName,
        state: stateName,
        lat: distData.lat,
        lon: distData.lon,
        elevation: 245,
        climatology_mm: distData.climatology_mm
      });

      if (distData.blocks) {
        Object.entries(distData.blocks).forEach(([blockName, blockData]) => {
          // Add block
          list.push({
            label: `${blockName} Block, ${districtName}, ${stateName}`,
            level: 'block',
            name: blockName,
            block: blockName,
            district: districtName,
            state: stateName,
            lat: blockData.lat,
            lon: blockData.lon,
            elevation: 240,
            climatology_mm: distData.climatology_mm
          });

          if (blockData.villages) {
            blockData.villages.forEach((village) => {
              // Add village
              list.push({
                label: `${village.name}, ${blockName} Block, ${districtName} (${stateName})`,
                level: 'village',
                name: village.name,
                village: village.name,
                block: blockName,
                district: districtName,
                state: stateName,
                lat: village.lat,
                lon: village.lon,
                elevation: village.elevation || 240,
                climatology_mm: distData.climatology_mm
              });
            });
          }
        });
      }
    });
  });
  return list;
};

export default INDIA_ADMIN_HIERARCHY;
"""
    out.write(footer)

print("Wrote complete 28-state hierarchy to:", out_file)
