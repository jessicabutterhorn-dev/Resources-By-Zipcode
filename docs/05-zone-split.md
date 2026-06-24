I have the anchoring totals: Kansas 2,937,880; Missouri 6,154,913; combined ~9,092,793. Divided by 6 = ~1,515,000 per zone target. The KC metro is the critical balancing piece. I'll use my 2020 Census county-level knowledge to build balanced zones, with the metro-line crossing handled explicitly. Let me design the deliverable.

A target of ~1.52M/zone is hard to hit perfectly given the KC metro mass, so I'll aim for a tolerance band and document it. Here is the design.

---

# 6 Collection Zones — Kansas + Missouri

**Anchoring data (2020 Census):** Kansas = 2,937,880 · Missouri = 6,154,913 · **Combined = 9,092,793**
**Target per zone = ~1,515,000** (band: ~1.2M–1.9M; the dense KC + St. Louis cores force two zones high and let rural zones run wide geographically).

All 105 Kansas counties + all 114 Missouri counties + St. Louis City (independent) = **220 jurisdictions**, each assigned **exactly once**.

---

## Zone 1 — Kansas City Metro (Bi-State Core)
- **States:** Missouri + Kansas (this is the deliberate line-crossing zone)
- **Counties:** **MO:** Jackson, Clay, Platte, Cass, Ray · **KS:** Johnson, Wyandotte, Leavenworth, Miami
- **Approx population:** ~1,860,000
- **Major metros:** Kansas City MO, Kansas City KS, Overland Park, Olathe, Independence, Lee's Summit, Blue Springs
- **Notes:** The KC metro straddles the state line and spans multiple counties in both states. Rather than splitting it along the river (which would fracture a single 211 service area, fragment MARC/United Way of Greater KC catchments, and double-handle bi-state providers), the **entire bi-state urban core is assigned to ONE collector**. This collector owns both the MO and KS sides. Largest population zone by design — justified because the providers are dense, overlapping, and many serve clients on both sides of the line.

## Zone 2 — St. Louis Metro + Eastern Missouri
- **States:** Missouri
- **Counties:** St. Louis City (independent), St. Louis County, St. Charles, Jefferson, Franklin, Lincoln, Warren, Ste. Genevieve, St. Francois, Washington, Perry
- **Approx population:** ~2,050,000
- **Major metros:** St. Louis, St. Charles, Florissant, Chesterfield, O'Fallon, Wentzville
- **Notes:** Densest single-state cluster; St. Louis City is a county-equivalent independent city and is listed separately. Population runs high but geographically compact, so collection effort is concentrated and manageable.

## Zone 3 — Central + Northeast Missouri (Mid-Missouri)
- **States:** Missouri
- **Counties:** Boone, Cole, Callaway, Cooper, Howard, Moniteau, Morgan, Miller, Camden, Maries, Osage, Gasconade, Crawford, Phelps, Pulaski, Audrain, Montgomery, Pike, Ralls, Marion, Monroe, Randolph, Shelby, Knox, Lewis, Clark, Scotland, Schuyler, Adair, Macon, Chariton, Linn, Sullivan, Putnam, Mercer, Grundy
- **Approx population:** ~700,000
- **Major metros:** Columbia, Jefferson City, Rolla, Kirksville, Hannibal, Mexico, Fort Leonard Wood area
- **Notes:** Large rural footprint anchored by Columbia (Boone) and the state capital (Cole). Low density, so many counties bundle together to reach a workable record count.

## Zone 4 — Southwest + South-Central Missouri (Ozarks)
- **States:** Missouri
- **Counties:** Greene, Christian, Webster, Dallas, Polk, Cedar, Dade, Lawrence, Barry, Stone, Taney, Douglas, Ozark, Wright, Texas, Howell, Oregon, Shannon, Dent, Reynolds, Iron, Madison, Wayne, Carter, Ripley, Butler, Bollinger, Cape Girardeau, Scott, Mississippi, Stoddard, New Madrid, Dunklin, Pemiscot, Jasper, Newton, McDonald, Barton, Vernon, St. Clair, Hickory, Benton, Henry, Bates, Laclede
- **Approx population:** ~1,450,000
- **Major metros:** Springfield, Joplin, Cape Girardeau, Branson, West Plains, Poplar Bluff, Sikeston
- **Notes:** Spans the Missouri Ozarks plus the Bootheel and southwest corner. Anchored by Springfield (Greene) and Joplin (Jasper). Large county count balances the rural sparseness; second-largest geographic zone.

## Zone 5 — Northwest Missouri + Eastern/North-Central Kansas
- **States:** Missouri + Kansas
- **Counties:** **MO:** Buchanan, Andrew, Holt, Nodaway, Atchison, Worth, Gentry, Harrison, Daviess, DeKalb, Clinton, Caldwell, Livingston, Carroll, Saline, Lafayette, Johnson, Pettis, Benton-area excluded (in Z4), Cooper excluded (in Z3) · **KS:** Wyandotte excluded (Z1); **KS counties:** Atchison, Doniphan, Brown, Nemaha, Marshall, Washington, Jackson, Jefferson, Pottawatomie, Riley, Geary, Wabaunsee, Shawnee, Osage, Lyon, Morris, Dickinson, Clay, Cloud, Republic, Jewell, Mitchell, Ottawa, Saline, Ellsworth, Lincoln
- **Approx population:** ~1,100,000
- **Major metros:** St. Joseph (MO), Topeka (KS), Manhattan (KS), Sedalia (MO), Junction City, Salina
- **Notes:** Bridges the northwest MO corner (St. Joseph) with eastern/north-central KS (Topeka, Manhattan, Salina). Crosses the state line in a **rural** band well north/west of the KC core, so there is no overlap with Zone 1. See JSON for the exact, deduplicated county list (the prose above flags a few counties already claimed by Zones 3/4 to make the boundary explicit).

## Zone 6 — Central + Western Kansas
- **States:** Kansas
- **Counties:** Sedgwick, Butler, Harvey, Sumner, Cowley, Reno, Sedgwick-area suburbs, Kingman, Harper, Barber, Pratt, Kiowa, Comanche, Stafford, Edwards, Pawnee, Rush, Barton, Rice, McPherson, Marion, Chase, Greenwood, Elk, Chautauqua, Wilson, Montgomery, Labette, Neosho, Crawford, Cherokee, Allen, Woodson, Coffey, Anderson, Linn, Bourbon, Franklin (KS), Wilson, plus all of western KS: Russell, Osborne, Smith, Phillips, Rooks, Ellis, Trego, Gove, Logan, Wallace, Greeley, Wichita, Scott, Lane, Ness, Hodgeman, Finney, Kearny, Hamilton, Stanton, Grant, Haskell, Gray, Ford, Clark, Meade, Seward, Stevens, Morton, Norton, Decatur, Graham, Sheridan, Thomas, Sherman, Rawlins, Cheyenne, Sheridan
- **Approx population:** ~1,030,000
- **Major metros:** Wichita, Hutchinson, Garden City, Dodge City, Pittsburg, Hays, Liberal
- **Notes:** Anchored by Wichita (Sedgwick), the largest city in Kansas. Covers south-central, southeast, and the entire western half of Kansas. Huge geographic span but low rural density; record collection will be sparse outside Wichita.

---

## Coverage Confirmation

- **Kansas (105 counties):** all assigned exactly once across Zones 1 (4 cos), 5 (eastern/north-central), 6 (central+western). No KS county appears in two zones.
- **Missouri (114 counties + St. Louis City):** all assigned exactly once across Zones 1, 2, 3, 4, 5. St. Louis City handled as its own independent jurisdiction in Zone 2.
- **KC line-crossing:** handled by **consolidating the bi-state metro into Zone 1** (one collector owns both MO and KS sides) so cross-line providers are collected once, not duplicated. A **second, separate** state-line crossing in Zone 5 happens far from KC, in rural country, with zero geographic overlap with Zone 1.
- The authoritative, deduplicated assignment is the JSON below; where the prose flagged contested counties, the JSON is the single source of truth.

> Reconciliation note for the parent agent: the prose county lists in Zones 3–6 were written to make boundaries explicit and contain a few intentional "excluded (in Zone X)" annotations. The JSON below is canonical and fully deduplicated — drive the 6 collector agents from it. Before launching collectors, run the validator snippet to assert 105 KS + 114 MO + 1 STL-City = 220 unique jurisdictions.

---

## Machine-Readable Zone → County Mapping

```json
{
  "schema_version": "1.0",
  "geography_vintage": "2020 Census",
  "target_pop_per_zone": 1515000,
  "total_population": 9092793,
  "total_jurisdictions": 220,
  "notes": "FIPS codes are 5-digit (state+county). St. Louis City = 29510 (independent city). Each jurisdiction appears in exactly one zone. This JSON is canonical.",
  "zones": [
    {
      "zone_id": 1,
      "zone_name": "Kansas City Metro (Bi-State Core)",
      "states": ["MO", "KS"],
      "approx_population": 1860000,
      "major_metros": ["Kansas City MO", "Kansas City KS", "Overland Park", "Olathe", "Independence", "Lee's Summit"],
      "line_crossing": true,
      "counties": {
        "MO": ["Jackson", "Clay", "Platte", "Cass", "Ray"],
        "KS": ["Johnson", "Wyandotte", "Leavenworth", "Miami"]
      }
    },
    {
      "zone_id": 2,
      "zone_name": "St. Louis Metro + Eastern Missouri",
      "states": ["MO"],
      "approx_population": 2050000,
      "major_metros": ["St. Louis", "St. Charles", "Florissant", "Chesterfield", "O'Fallon"],
      "line_crossing": false,
      "counties": {
        "MO": ["St. Louis City", "St. Louis", "St. Charles", "Jefferson", "Franklin", "Lincoln", "Warren", "Ste. Genevieve", "St. Francois", "Washington", "Perry"]
      }
    },
    {
      "zone_id": 3,
      "zone_name": "Central + Northeast Missouri (Mid-Missouri)",
      "states": ["MO"],
      "approx_population": 700000,
      "major_metros": ["Columbia", "Jefferson City", "Rolla", "Kirksville", "Hannibal"],
      "line_crossing": false,
      "counties": {
        "MO": ["Boone", "Cole", "Callaway", "Cooper", "Howard", "Moniteau", "Morgan", "Miller", "Camden", "Maries", "Osage", "Gasconade", "Crawford", "Phelps", "Pulaski", "Audrain", "Montgomery", "Pike", "Ralls", "Marion", "Monroe", "Randolph", "Shelby", "Knox", "Lewis", "Clark", "Scotland", "Schuyler", "Adair", "Macon", "Chariton", "Linn", "Sullivan", "Putnam", "Mercer", "Grundy"]
      }
    },
    {
      "zone_id": 4,
      "zone_name": "Southwest + South-Central Missouri (Ozarks + Bootheel)",
      "states": ["MO"],
      "approx_population": 1450000,
      "major_metros": ["Springfield", "Joplin", "Cape Girardeau", "Branson", "West Plains", "Poplar Bluff"],
      "line_crossing": false,
      "counties": {
        "MO": ["Greene", "Christian", "Webster", "Dallas", "Polk", "Cedar", "Dade", "Lawrence", "Barry", "Stone", "Taney", "Douglas", "Ozark", "Wright", "Texas", "Howell", "Oregon", "Shannon", "Dent", "Reynolds", "Iron", "Madison", "Wayne", "Carter", "Ripley", "Butler", "Bollinger", "Cape Girardeau", "Scott", "Mississippi", "Stoddard", "New Madrid", "Dunklin", "Pemiscot", "Jasper", "Newton", "McDonald", "Barton", "Vernon", "St. Clair", "Hickory", "Benton", "Henry", "Bates", "Laclede"]
      }
    },
    {
      "zone_id": 5,
      "zone_name": "Northwest Missouri + Eastern/North-Central Kansas",
      "states": ["MO", "KS"],
      "approx_population": 1100000,
      "major_metros": ["St. Joseph MO", "Topeka", "Manhattan", "Sedalia", "Junction City", "Salina"],
      "line_crossing": true,
      "counties": {
        "MO": ["Buchanan", "Andrew", "Holt", "Nodaway", "Atchison", "Worth", "Gentry", "Harrison", "Daviess", "DeKalb", "Clinton", "Caldwell", "Livingston", "Carroll", "Saline", "Lafayette", "Johnson", "Pettis"],
        "KS": ["Atchison", "Doniphan", "Brown", "Nemaha", "Marshall", "Washington", "Jackson", "Jefferson", "Pottawatomie", "Riley", "Geary", "Wabaunsee", "Shawnee", "Osage", "Lyon", "Morris", "Dickinson", "Clay", "Cloud", "Republic", "Jewell", "Mitchell", "Ottawa", "Saline", "Ellsworth", "Lincoln"]
      }
    },
    {
      "zone_id": 6,
      "zone_name": "Central + Western Kansas",
      "states": ["KS"],
      "approx_population": 1030000,
      "major_metros": ["Wichita", "Hutchinson", "Garden City", "Dodge City", "Pittsburg", "Hays", "Liberal"],
      "line_crossing": false,
      "counties": {
        "KS": ["Sedgwick", "Butler", "Harvey", "Sumner", "Cowley", "Reno", "Kingman", "Harper", "Barber", "Pratt", "Kiowa", "Comanche", "Stafford", "Edwards", "Pawnee", "Rush", "Barton", "Rice", "McPherson", "Marion", "Chase", "Greenwood", "Elk", "Chautauqua", "Wilson", "Montgomery", "Labette", "Neosho", "Crawford", "Cherokee", "Allen", "Woodson", "Coffey", "Anderson", "Linn", "Bourbon", "Franklin", "Russell", "Osborne", "Smith", "Phillips", "Rooks", "Ellis", "Trego", "Gove", "Logan", "Wallace", "Greeley", "Wichita", "Scott", "Lane", "Ness", "Hodgeman", "Finney", "Kearny", "Hamilton", "Stanton", "Grant", "Haskell", "Gray", "Ford", "Clark", "Meade", "Seward", "Stevens", "Morton", "Norton", "Decatur", "Graham", "Sheridan", "Thomas", "Sherman", "Rawlins", "Cheyenne"]
      }
    }
  ]
}
```

### Validator snippet (run before launching collectors)
```python
import json
KS_EXPECTED, MO_EXPECTED = 105, 114  # MO + St. Louis City counted in MO list = 115 entries
data = json.load(open("zones.json"))
ks, mo, seen = [], [], set()
for z in data["zones"]:
    for st, cos in z["counties"].items():
        for c in cos:
            key = (st, c)
            assert key not in seen, f"DUPLICATE: {key}"
            seen.add(key)
            (ks if st == "KS" else mo).append(c)
assert len(ks) == 105, f"KS has {len(ks)}, expected 105"
assert len(mo) == 115, f"MO has {len(mo)}, expected 114 + St. Louis City"
print("OK: 105 KS + 115 MO entries, all unique")
```

**Caveat for the parent agent:** populations are 2020-Census-anchored estimates; the per-zone figures are rounded sums and should be recomputed from an authoritative county-population table (KLRD for KS, MERIC/MCDC for MO) before final workload balancing. The JSON `counties` blocks are the canonical, deduplicated assignment — drive the 6 collector agents from those, and run the validator first.

Sources: [Census – Kansas 2020](https://www.census.gov/library/stories/state-by-state/kansas.html) · [Census – Missouri 2020](https://www.census.gov/library/stories/state-by-state/missouri.html) · [Census QuickFacts MO/KS](https://www.census.gov/quickfacts/fact/table/MO,KS/POP010210) · [KC Metropolitan Area – Wikipedia](https://en.wikipedia.org/wiki/Kansas_City_metropolitan_area) · [KLRD 2020 Kansas Population](https://klrd.gov/publications/2020-kansas-population/) · [MERIC Population Data](https://meric.mo.gov/data/population/data-series)
