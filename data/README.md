# Data we need

We need two kinds of data.

The static pile is who sells India crude, LNG, urea, DAP, and MOP; which Indian ports and plants take it; which sea lanes it crosses. Type those from official tables. Store them as JSON or CSV with a year and a source on every number.

The live pile is news. We pull that from GDELT and add fertilizer keywords so a urea story is not dropped because it never said "oil".

If a number has no year and no source, it does not go in a seed file.

---

## News (GDELT)

[GDELT](https://www.gdeltproject.org/) watches a large set of news sites and turns articles into tables. No API key. Free. Ugly.

We use **GDELT 2.0 Global Knowledge Graph (GKG)** files, not the older daily dump. GKG 2.0 updates about every 15 minutes. Each slice is a zip of a tab-separated file with themes, locations, organisations, tone, and the article URL.

Useful links:

- Project home: [https://www.gdeltproject.org/](https://www.gdeltproject.org/)
- How to get the files: [https://www.gdeltproject.org/data.html](https://www.gdeltproject.org/data.html)
- Latest 15-minute files: [http://data.gdeltproject.org/gdeltv2/lastupdate.txt](http://data.gdeltproject.org/gdeltv2/lastupdate.txt)
- Full file list: [http://data.gdeltproject.org/gdeltv2/masterfilelist.txt](http://data.gdeltproject.org/gdeltv2/masterfilelist.txt)
- GKG column meanings: [GKG codebook v2.1 (PDF)](http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf)
- Search API if you do not want to download the zip (DOC 2.0): [https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)

`lastupdate.txt` looks like this (size, hash, url):

```
249221071  2F3A...  http://data.gdeltproject.org/gdeltv2/20260822121500.export.CSV.zip
21984931   ...      http://data.gdeltproject.org/gdeltv2/20260822121500.mentions.CSV.zip
157394024  ...      http://data.gdeltproject.org/gdeltv2/20260822121500.gkg.csv.zip
```

We want the line that ends in `gkg.csv.zip`.

Keep rows whose `V2Themes` hit energy tags (`ENV_OIL`, `ENV_GAS`, `ENERGY`, `ECON_OILPRICE`, ...) or whose URL/names mention oil, Hormuz, LNG, sanctions, and so on. Also keep urea, DAP, potash, fertilizer, IFFCO, and the same chokepoint names.

The files are large. Filter before you save.

```python
import io, zipfile, requests, pandas as pd

HEADERS = {"User-Agent": "Mozilla/5.0"}  # some CDNs 403 a bare Python UA

def latest_gkg_url() -> str:
    text = requests.get(
        "http://data.gdeltproject.org/gdeltv2/lastupdate.txt",
        timeout=30,
        headers=HEADERS,
    ).text
    line = next(l for l in text.splitlines() if l.strip().endswith("gkg.csv.zip"))
    return line.strip().split()[-1]

def load_gkg(url: str) -> pd.DataFrame:
    raw = requests.get(url, timeout=60, headers=HEADERS).content
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = z.namelist()[0]
        return pd.read_csv(z.open(name), sep="\t", header=None, dtype=str, on_bad_lines="skip")
```

If you only need a handful of articles, skip the zip and hit DOC 2.0:

```python
# docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
r = requests.get(
    "https://api.gdeltproject.org/api/v2/doc/doc",
    params={
        "query": '"strait of hormuz" sourcelang:english',
        "mode": "ArtList",
        "maxrecords": 10,
        "format": "json",
    },
    timeout=30,
)
print(r.json().get("articles", [])[:2])
```

Keep from each article: a stable id (`GKGRECORDID` or URL), timestamp, source name, URL, tone if present, and which of our graph nodes it mentioned (Hormuz, Qatar, Dahej, ...). Dedup on that id so a rerun does not double-count.

Raw dumps go under `data/raw/` (gitignored). Do not commit the zip.

---

## Crude oil

We need three tables: **import mix by country**, **Indian refineries**, **likely discharge ports**. Then we join them with chokepoints (below).

### Import mix

Best official series is PPAC (Petroleum Planning and Analysis Cell, under MoPNG).

- Site: [https://ppac.gov.in/](https://ppac.gov.in/)
- Import / export: [https://ppac.gov.in/import-export](https://ppac.gov.in/import-export)
- Monthly snapshot ("Ready Reckoner"): linked from the PPAC home page as "Snapshot of India's Oil and Gas Data"

Country-wise crude import shares are usually in that snapshot PDF, not as a clean JSON API. Download the PDF for a stated month, type the top suppliers into `data/seeds/oil/imports.json`, and write the PDF name + month in a `source` field.

DGCIS / DGFT trade data can back that up: [https://www.dgft.gov.in/](https://www.dgft.gov.in/)

UN Comtrade is useful when you want a country pair in one HTTP call ([Comtrade Plus](https://comtradeplus.un.org/)):

```python
# HS 2709 = petroleum oils, crude. reporter=India (699), yearly.
# docs: https://comtradedeveloper.un.org/
import requests
r = requests.get(
    "https://comtradeplus.un.org/api/get",
    params={
        "typeCode": "C",
        "freqCode": "A",
        "clCode": "HS",
        "period": "2024",
        "reporterCode": "699",
        "cmdCode": "2709",
        "flowCode": "M",
        "partnerCode": "all",
    },
    timeout=60,
)
```

Use Comtrade as a check, not as a replacement for PPAC when the two disagree. Prefer PPAC for India.

### Refineries

PPAC publishes installed refining capacity (see [What's new](https://ppac.gov.in/all-whats-new); there is an "Installed Refinery Capacity" note). Also company sites: IOCL, BPCL, HPCL, RIL, Nayara.

Each refinery row needs: name, operator, lat/lon, capacity (bbl/day or MMTPA, pick one unit and stick to it), crude grade notes if you have them, nearest crude port.

Start with the large plants (Jamnagar, Vadinar, Kochi, Mangalore, Panipat, Vizag, Paradip, and the rest of the PPAC capacity table). Rebuild the list from PPAC so the year is current.

### Crude ports

The plant is inland or on the coast. The tanker stops at a port.

West coast: Sikka / Vadinar (Jamnagar), Mundra, Mumbai, New Mangalore, Kochi.
East coast: Paradip, Visakhapatnam, Haldia, Chennai.

For each port: name, lat/lon, which refineries it feeds, draft/size class if you can find it. IPA has port pages: [https://www.ipa.nic.in/](https://www.ipa.nic.in/). Ministry of Ports: [https://shipmin.gov.in/](https://shipmin.gov.in/). World Port Index (NGA) if you need lat/lon in one place: [https://msi.nga.mil/Publications/WPI](https://msi.nga.mil/Publications/WPI).

---

## LNG

PPAC again (natural gas section of the same Ready Reckoner). Note that PPAC crude import tables often say **LNG is not included** in the crude import line. Do not mix the two.

Country mix is dominated by Qatar, plus the US, UAE, Australia depending on the year. Write the year.

Indian LNG terminals (name, operator, nameplate capacity in MMTPA, lat/lon, port):

- Dahej (Petronet)
- Hazira (Shell)
- Dabhol
- Kochi (Petronet)
- Ennore
- Mundra
- Dhamra
- Jaigarh

Confirm the live list and capacities from PPAC / PNGRB / the operator. GIIGNL's annual report is a decent secondary source: [https://giignl.org/](https://giignl.org/).

Qatar cargoes to west-coast terminals pass Hormuz. US cargoes usually do not. That difference has to be in the route table or the cascade math will be wrong.

---

## Fertilizers (urea, DAP, MOP)

Treat them as three commodities, not one blob called "fertilizer".

- Department of Fertilizers: [https://www.fert.nic.in/](https://www.fert.nic.in/)
- Fertilizer Association of India: [https://www.faidelhi.org/](https://www.faidelhi.org/)
- DGFT / DGCIS for import by partner country
- UN Comtrade HS codes (check the year of the HS edition you use): urea ~3102.10, DAP ~3105.30, MOP (potassium chloride) ~3104.20

For each product: India import volume, top partner countries, typical load ports, Indian discharge ports (Kandla, Mundra, Paradip, Kakinada, Krishnapatnam come up a lot), and a few domestic plants (IFFCO, NFL, RCF, ...) so the graph has an Indian sink.

Gulf urea/DAP to India is a Hormuz problem. Canadian MOP is not. Russian / Belarusian MOP is a sanctions problem. Put that on the route, not in a comment.

---

## Chokepoints

Do not invent daily volumes. Copy EIA.

[World oil transit chokepoints](https://www.eia.gov/international/analysis/special-topics/World_Oil_Transit_Chokepoints) (EIA also keeps a table under International > World Oil Transit Chokepoints, last updated March 2026 at the time of writing).

For us, the ones that actually sit on Indian cargoes:

- Strait of Hormuz (Gulf crude, Qatari LNG, Gulf urea/DAP)
- Bab el-Mandeb / Red Sea (if the cargo came via Suez)
- Strait of Malacca (eastbound leftovers; most India-bound Gulf cargo does not need it)
- Cape of Good Hope (US LNG and Atlantic crude that skip Suez)

Each chokepoint row: name, lat/lon, EIA transit volume with year, which of our routes list it.

IEA has a short Hormuz note as well: [Strait of Hormuz factsheet (Feb 2026, PDF)](https://iea.blob.core.windows.net/assets/c8248eba-8689-46d9-ae4b-b858b59c0f1c/StraitofHormuz2026-Factsheet.pdf).

---

## What a seed row looks like

Same shape in oil, LNG, and fertilizer files:

```json
{
  "commodity": "crude_oil",
  "supplier_iso": "SA",
  "supplier_name": "Saudi Arabia",
  "volume": 40.2,
  "unit": "mmt",
  "year": 2024,
  "share_of_india_imports": 0.18,
  "chokepoints": ["hormuz"],
  "indian_port": "sikka",
  "source": "PPAC Ready Reckoner, July 2025, table X",
  "source_url": "https://ppac.gov.in/"
}
```

Units: pick one per commodity and convert in the loader. Do not mix bbl/day and MMT in the same file.

---

## Where this sits in the repo

| Path | What goes there |
| --- | --- |
| `data/README.md` | This note |
| `data/seeds/oil/` | Import mix, refineries, crude ports, oil routes |
| `data/seeds/lng/` | Import mix, terminals, LNG routes |
| `data/seeds/fertilizer/` | Urea / DAP / MOP separately |
| `data/raw/` | GDELT zips and filtered extracts. Gitignored. Rebuild with a script. |
| `src/flow/data/` | Loaders: read seeds, fetch GDELT, write into whatever store we pick |
| `src/flow/intel/` | Filter news, map text to node names, scores |
| `src/flow/models/` | Pydantic types for the JSON above |
| `src/flow/graph/` | Build the NetworkX graph from seeds (does not download news) |
| `notebooks/` | One-off PPAC PDF scraping, GDELT filter tuning |
| `scripts/` | `fetch_gdelt.py` and similar |
| `tests/` | Tiny frozen fixtures, not a full GKG zip |
| `tests/fixtures/` | 10 to 50 sample GDELT rows + one seed file for tests |

News loaders belong in `src/flow/data/` and `src/flow/intel/`. Pattern: read `lastupdate.txt`, download the GKG zip, filter by theme and keyword. Do not dump fetch logic into `src/flow/graph/`.
