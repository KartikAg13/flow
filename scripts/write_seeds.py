"""One-shot writer for data/seeds/*.json. Numbers are cited in each row."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"

WITS_OIL = "https://wits.worldbank.org/trade/comtrade/en/country/IND/year/2024/tradeflow/Imports/partner/ALL/product/270900"
WITS_LNG = "https://wits.worldbank.org/trade/comtrade/en/country/IND/year/2024/tradeflow/Imports/partner/ALL/product/271111"
PPAC_REF = "https://ppac.gov.in/infrastructure/installed-refinery-capacity"
FERT_REPORTS = "https://www.fert.gov.in/en/documents/reports"
FERT_PLANTS = "https://www.fert.gov.in/en/department/our-organizations"
IPA_URL = "https://www.ipa.org.in/"
EIA = "https://www.eia.gov/international/analysis/special-topics/World_Oil_Transit_Chokepoints"
PIB_SPR = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2113233"
PPAC_ICR = "https://ppac.gov.in/uploads/rep_studies/1711109718_Industry-Consumption-Report-February-2024.pdf"
RS_UREA = "https://rsdebate.nic.in/bitstream/123456789/749969/1/PQ_265_30072024_U827_p230_p230.pdf"
EI_CONV = "https://www.energyintel.com/0000017b-a7ba-de4c-a17b-e7fac9fa0000"
# PPAC's own link to this edition was unavailable; this is a copy of the PPAC PDF
PPAC_RR = "https://forum.valuepickr.com/uploads/short-url/dxhgtaVB1GYtnMa6VOaP7cew7jr.pdf"
PPAC_SECTORAL = "https://ppac.gov.in/uploads/rep_studies/1666932000_ExecutiveSummarySectoralConsumptionStudy.pdf"
PIB_FERT = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2244621"
LS_UREA = "https://sansad.in/getFile/lsapps/loksabhaquestions/annex/188/AS94_oSh6Go.pdf"
AGCENSUS = "https://agcensus.da.gov.in/statesummarytype.aspx"
EIA_HORMUZ = "https://www.eia.gov/todayinenergy/detail.php?id=65504"
EIA_CHOKEPOINTS = "https://www.eia.gov/international/content/analysis/special_topics/World_Oil_Transit_Chokepoints/"
EI_REVIEW = "https://www.energyinst.org/statistical-review"
SEAROUTE = "https://github.com/genthalili/searoute-py"

# Export terminal of each route (name, lat, lon), approximate; "Other" suppliers have none
ORIGIN = {
    "oil-RU-sikka": ("Primorsk", 60.35, 28.68),
    "oil-IQ-sikka": ("Basrah Oil Terminal", 29.68, 48.82),
    "oil-SA-sikka": ("Ras Tanura", 26.64, 50.16),
    "oil-AE-mundra": ("Jebel Dhanna", 24.19, 52.60),
    "oil-NG-mumbai": ("Bonny", 4.42, 7.15),
    "oil-US-sikka": ("Corpus Christi", 27.81, -97.39),
    "oil-AO-sikka": ("Luanda", -8.80, 13.20),
    "oil-KW-sikka": ("Mina al Ahmadi", 29.07, 48.16),
    "oil-VE-sikka": ("Jose", 10.10, -64.83),
    "oil-CO-sikka": ("Covenas", 9.41, -75.69),
    "oil-MX-sikka": ("Dos Bocas", 18.43, -93.20),
    "lng-QA-dahej": ("Ras Laffan", 25.92, 51.61),
    "lng-US-dahej": ("Sabine Pass", 29.73, -93.87),
    "lng-AE-hazira": ("Das Island", 25.15, 52.87),
    "lng-AO-dahej": ("Soyo", -6.13, 12.35),
    "lng-OM-dahej": ("Qalhat", 22.70, 59.37),
    "lng-NG-dahej": ("Bonny", 4.42, 7.15),
    "lng-GQ-dahej": ("Punta Europa", 3.78, 8.71),
    "lng-CM-dahej": ("Kribi", 2.87, 9.83),
    "lng-MZ-dhamra": ("Coral South FLNG", -10.40, 40.60),
    "lng-TT-dahej": ("Point Fortin", 10.18, -61.69),
    "urea-OM-kandla": ("Sur", 22.57, 59.53),
    "urea-RU-kandla": ("Ust-Luga", 59.68, 28.40),
    "urea-SA-kandla": ("Jubail", 27.00, 49.66),
    "urea-QA-kandla": ("Mesaieed", 24.99, 51.56),
    "urea-NG-kandla": ("Onne", 4.70, 7.15),
    "dap-SA-kandla": ("Ras Al Khair", 27.48, 49.27),
    "dap-MA-kandla": ("Jorf Lasfar", 33.12, -8.63),
    "dap-CN-paradip": ("Fangcheng", 21.60, 108.35),
    "mop-RU-kandla": ("St Petersburg", 59.90, 30.20),
    "mop-CA-kandla": ("Vancouver", 49.30, -123.10),
    "mop-JO-kandla": ("Aqaba", 29.52, 35.00),
    "mop-IL-kandla": ("Eilat", 29.55, 34.96),
    "mop-TM-kandla": ("Bandar Abbas", 27.18, 56.28),
}
# Our chokepoint ids -> searoute passage names. The Cape is open ocean, not a passage, so a path
# counts as "cape" when its geometry rounds southern Africa.
PASSAGES = {"hormuz": "ormuz", "bab_el_mandeb": "babalmandab", "suez": "suez", "malacca": "malacca"}
PORT_SAID = (31.26, 32.31)  # north end of the Suez Canal


def sea_paths(leg: str, start: tuple[float, float], end: tuple[float, float]) -> list[dict]:
    """Every distinct way by sea between two (lat, lon) points, shortest per chokepoint set."""
    import warnings

    import searoute as sr

    def leg_path(a: tuple[float, float], b: tuple[float, float], shut=()) -> tuple[float, set]:
        with warnings.catch_warnings():  # "no path found" when the passages shut leave none
            warnings.simplefilter("ignore")
            f = sr.searoute(
                [a[1], a[0]],
                [b[1], b[0]],
                units="naut",
                restrictions=["northwest", *(PASSAGES[c] for c in shut)],
                return_passages=True,
            )
        crossed = set(f.properties.get("traversed_passages") or [])
        used = {c for c, name in PASSAGES.items() if name in crossed}
        if any(lat < -30 and 0 < lon < 45 for lon, lat in f.geometry.coordinates):
            used.add("cape")
        return f.properties["length"], used

    best: dict[tuple[str, ...], float] = {}
    for k in range(len(PASSAGES) + 1):
        for shut in itertools.combinations(PASSAGES, k):
            nm, used = leg_path(start, end, shut)
            if nm and not used & set(shut):
                best[tuple(sorted(used))] = min(best.get(tuple(sorted(used)), nm), nm)
    # The Cape cannot be shut in searoute, so give Atlantic origins a path forced through Suez
    if start[1] < PORT_SAID[1] and not any("suez" in k for k in best):
        (nm1, used1), (nm2, used2) = leg_path(start, PORT_SAID), leg_path(PORT_SAID, end)
        if nm1 and nm2:
            best[tuple(sorted(used1 | used2 | {"suez"}))] = nm1 + nm2
    return [
        {
            "id": f"{leg}~{i}",
            "leg": leg,
            "passes": list(passes),
            "nm": round(nm),
            "source": "searoute 1.6 on the Eurostat SeaRoute marine network: shortest path "
            "with the other passages shut",
            "source_url": SEAROUTE,
        }
        for i, (passes, nm) in enumerate(sorted(best.items(), key=lambda kv: kv[1]))
    ]


# State of every Indian site (ports, refineries, LNG terminals, fertilizer plants, SPR)
STATE = {
    **dict.fromkeys(
        [
            "sikka",
            "vadinar",
            "mundra",
            "kandla",
            "dahej",
            "hazira",
            "koyali",
            "jamnagar_dta",
            "jamnagar_sez",
            "vadinar_ref",
            "hazira_lng",
            "mundra_lng",
            "iffco_kalol",
            "kribhco_hazira",
        ],
        "Gujarat",
    ),
    **dict.fromkeys(
        [
            "mumbai",
            "dabhol",
            "jaigarh",
            "hpcl_mumbai",
            "bpcl_mumbai",
            "dabhol_lng",
            "jaigarh_lng",
            "rcf_thal",
            "rcf_trombay",
        ],
        "Maharashtra",
    ),
    **dict.fromkeys(["mangalore", "mangalore_ref", "spr_mangaluru", "spr_padur"], "Karnataka"),
    **dict.fromkeys(["kochi", "kochi_ref", "kochi_lng"], "Kerala"),
    **dict.fromkeys(["paradip", "dhamra", "paradip_ref", "dhamra_lng", "iffco_paradeep"], "Odisha"),
    **dict.fromkeys(
        ["visakhapatnam", "kakinada", "krishnapatnam", "vizag_ref", "tatipaka", "spr_vizag"],
        "Andhra Pradesh",
    ),
    **dict.fromkeys(["haldia", "haldia_ref"], "West Bengal"),
    **dict.fromkeys(["chennai", "ennore", "manali", "ennore_lng"], "Tamil Nadu"),
    **dict.fromkeys(["digboi", "guwahati", "bongaigaon", "numaligarh"], "Assam"),
    **dict.fromkeys(["bathinda", "nfl_nangal"], "Punjab"),
    **dict.fromkeys(["pachpadra", "chambal_kota"], "Rajasthan"),
    "barauni": "Bihar",
    "mathura": "Uttar Pradesh",
    "panipat": "Haryana",
    "bina": "Madhya Pradesh",
}

FUEL_TMT = {  # state: (diesel/HSD, petrol/MS), FY2023-24 (P)
    "Andaman & Nicobar": (160.8, 20.2),
    "Andhra Pradesh": (3639.5, 1571.4),
    "Arunachal Pradesh": (244.5, 78.0),
    "Assam": (1312.2, 668.1),
    "Bihar": (2366.9, 1081.7),
    "Chandigarh": (244.6, 119.8),
    "Chhattisgarh": (2125.6, 798.1),
    "Dadra & Nagar Haveli and Daman & Diu": (182.6, 46.3),
    "Delhi": (614.2, 960.3),
    "Goa": (274.0, 216.6),
    "Gujarat": (7178.7, 2546.1),
    "Haryana": (4274.5, 1289.9),
    "Himachal Pradesh": (795.2, 320.8),
    "Jammu & Kashmir": (916.2, 380.2),
    "Jharkhand": (1888.5, 693.0),
    "Karnataka": (8350.6, 2899.4),
    "Kerala": (2413.3, 1791.5),
    "Ladakh": (97.3, 21.7),
    "Lakshadweep": (19.1, 1.3),
    "Madhya Pradesh": (4163.7, 1825.1),
    "Maharashtra": (9926.7, 4068.0),
    "Manipur": (103.6, 75.5),
    "Meghalaya": (438.4, 135.5),
    "Mizoram": (111.2, 42.7),
    "Nagaland": (121.9, 58.5),
    "Odisha": (3286.8, 1058.6),
    "Puducherry": (572.7, 181.1),
    "Punjab": (3467.0, 1182.9),
    "Rajasthan": (5495.0, 1896.4),
    "Sikkim": (89.9, 28.9),
    "Tamil Nadu": (6287.2, 3352.0),
    "Telangana": (3668.3, 1675.1),
    "Tripura": (108.9, 68.1),
    "Uttar Pradesh": (10307.6, 4368.6),
    "Uttarakhand": (815.3, 438.7),
    "West Bengal": (3522.3, 1259.1),
}
HOLDINGS = {  # Agriculture Census 2015-16, number of operational holdings, all size classes
    "Andaman & Nicobar": 11954,
    "Andhra Pradesh": 8523910,
    "Arunachal Pradesh": 113253,
    "Assam": 2741711,
    "Bihar": 16412893,
    "Chandigarh": 748,
    "Chhattisgarh": 4010772,
    "Dadra & Nagar Haveli and Daman & Diu": 23088,
    "Delhi": 20842,
    "Goa": 74563,
    "Gujarat": 5320626,
    "Haryana": 1628015,
    "Himachal Pradesh": 996809,
    "Jammu & Kashmir": 1416509,
    "Jharkhand": 2802946,
    "Karnataka": 8680739,
    "Kerala": 7583496,
    "Lakshadweep": 10017,
    "Madhya Pradesh": 10003135,
    "Maharashtra": 15285439,
    "Manipur": 150484,
    "Meghalaya": 232397,
    "Mizoram": 89774,
    "Nagaland": 196532,
    "Odisha": 4865850,
    "Puducherry": 33840,
    "Punjab": 1092713,
    "Rajasthan": 7654616,
    "Sikkim": 71532,
    "Tamil Nadu": 7937947,
    "Telangana": 5947735,
    "Tripura": 573194,
    "Uttar Pradesh": 23821625,
    "Uttarakhand": 881305,
    "West Bengal": 7242732,
}

# Lok Sabha Starred Q.94 (24.07.2026) Annexure-II: DBT sales, Kharif 2026 to 19.07.26, LMT
FERT_SALES = {  # state: (urea, DAP, MOP); used only for each state's share of national sales
    "Andhra Pradesh": (2.44, 0.72, 0.29),
    "Arunachal Pradesh": (0.01, 0, 0),
    "Assam": (1.57, 0.23, 0.19),
    "Bihar": (2.90, 0.80, 0.11),
    "Chhattisgarh": (4.83, 1.32, 0.50),
    "Delhi": (0.08, 0.02, 0),
    "Goa": (0.01, 0, 0),
    "Gujarat": (5.17, 1.53, 0.19),
    "Haryana": (7.17, 1.15, 0.13),
    "Himachal Pradesh": (0.24, 0, 0),
    "Jammu & Kashmir": (0.75, 0.19, 0.10),
    "Jharkhand": (0.91, 0.21, 0.01),
    "Karnataka": (4.35, 2.23, 0.74),
    "Kerala": (0.38, 0.08, 0.28),
    "Madhya Pradesh": (8.65, 2.07, 0.27),
    "Maharashtra": (8.42, 2.50, 0.81),
    "Manipur": (0.10, 0.01, 0),
    "Meghalaya": (0.01, 0, 0),
    "Nagaland": (0.01, 0, 0),
    "Odisha": (1.56, 0.75, 0.20),
    "Puducherry": (0.04, 0, 0),
    "Punjab": (11.53, 1.28, 0.21),
    "Rajasthan": (6.44, 1.78, 0.04),
    "Tamil Nadu": (2.84, 0.55, 0.39),
    "Telangana": (3.78, 1.36, 0.12),
    "Tripura": (0.05, 0.01, 0.01),
    "Uttarakhand": (0.68, 0.14, 0.01),
    "Uttar Pradesh": (16.69, 3.33, 0.22),
    "West Bengal": (3.18, 0.53, 0.38),
}
# Same answer, Annexure-I: urea production by state, 2024-25, LMT
UREA_OUTPUT = {
    "Andhra Pradesh": 2.17,
    "Assam": 1.87,
    "Bihar": 8.55,
    "Goa": 4.17,
    "Gujarat": 40.09,
    "Haryana": 5.15,
    "Jharkhand": 12.47,
    "Karnataka": 4.43,
    "Madhya Pradesh": 21.35,
    "Maharashtra": 20.90,
    "Punjab": 10.64,
    "Rajasthan": 38.69,
    "Tamil Nadu": 12.50,
    "Telangana": 11.95,
    "Uttar Pradesh": 97.02,
    "West Bengal": 14.71,
}
# PPAC all-India study on sectoral demand for petrol and diesel (Oct 2020 - Sep 2021), percent
SEGMENTS = {
    "diesel": [  # Figure 17: retail and direct sales, full year
        ("Trucks (HCV/LCV)", 55.4),
        ("Private cars", 12.4),
        ("Industry", 6.3),
        ("Others", 6.3),
        ("Buses", 5.9),
        ("Agriculture (tractors, pumps)", 4.8),
        ("Taxis", 2.9),
        ("Railways", 2.1),
        ("Power gensets", 1.6),
        ("Three-wheelers", 1.2),
        ("Aviation and shipping", 0.8),
        ("Mobile towers", 0.3),
    ],
    "petrol": [  # Figure 10: retail outlets
        ("Two-wheelers", 59.0),
        ("Private cars", 28.0),
        ("Private SUVs", 8.62),
        ("Taxis", 1.91),
        ("Taxi SUVs", 1.38),
        ("Three-wheelers (goods)", 0.69),
        ("Three-wheelers (passenger)", 0.55),
    ],
}


def dump(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"{len(rows):3d}  {path.relative_to(ROOT)}")


def main() -> None:
    dump(
        SEEDS / "suppliers.json",
        [
            {"iso": iso, "name": name, "lat": lat, "lon": lon}
            for iso, name, lat, lon in [
                ("IN", "India", 20.5937, 78.9629),
                ("RU", "Russia", 61.5240, 105.3188),
                ("IQ", "Iraq", 33.2232, 43.6793),
                ("SA", "Saudi Arabia", 23.8859, 45.0792),
                ("AE", "United Arab Emirates", 23.4241, 53.8478),
                ("US", "United States", 37.0902, -95.7129),
                ("NG", "Nigeria", 9.0820, 8.6753),
                ("AO", "Angola", -11.2027, 17.8739),
                ("KW", "Kuwait", 29.3117, 47.4818),
                ("VE", "Venezuela", 6.4238, -66.5897),
                ("CO", "Colombia", 4.5709, -74.2973),
                ("MX", "Mexico", 23.6345, -102.5528),
                ("QA", "Qatar", 25.3548, 51.1839),
                ("OM", "Oman", 21.4735, 55.9754),
                ("GQ", "Equatorial Guinea", 1.6508, 10.2679),
                ("CM", "Cameroon", 7.3697, 12.3547),
                ("MZ", "Mozambique", -18.6657, 35.5296),
                ("TT", "Trinidad and Tobago", 10.6918, -61.2225),
                ("AU", "Australia", -25.2744, 133.7751),
                ("MA", "Morocco", 31.7917, -7.0926),
                ("CN", "China", 35.8617, 104.1954),
                ("CA", "Canada", 56.1304, -106.3468),
                ("JO", "Jordan", 30.5852, 36.2384),
                ("IL", "Israel", 31.0461, 34.8516),
                ("TM", "Turkmenistan", 38.9697, 59.5563),
                ("XX", "Other", None, None),
            ]
        ],
    )

    ports = [
        ("sikka", "Sikka", "IN", "west", 22.43, 69.83, ["crude_oil"]),
        ("vadinar", "Vadinar", "IN", "west", 22.37, 69.72, ["crude_oil"]),
        (
            "mundra",
            "Mundra",
            "IN",
            "west",
            22.74,
            69.71,
            ["crude_oil", "lng", "urea", "dap", "mop"],
        ),
        ("mumbai", "Mumbai", "IN", "west", 18.95, 72.85, ["crude_oil"]),
        ("mangalore", "New Mangalore", "IN", "west", 12.87, 74.84, ["crude_oil"]),
        ("kochi", "Kochi", "IN", "west", 9.97, 76.24, ["crude_oil", "lng"]),
        ("kandla", "Kandla", "IN", "west", 23.03, 70.22, ["urea", "dap", "mop"]),
        ("dahej", "Dahej", "IN", "west", 21.71, 72.57, ["lng"]),
        ("hazira", "Hazira", "IN", "west", 21.12, 72.65, ["lng"]),
        ("dabhol", "Dabhol", "IN", "west", 17.54, 73.16, ["lng"]),
        ("jaigarh", "Jaigarh", "IN", "west", 17.30, 73.19, ["lng"]),
        ("paradip", "Paradip", "IN", "east", 20.26, 86.67, ["crude_oil", "urea", "dap"]),
        ("visakhapatnam", "Visakhapatnam", "IN", "east", 17.69, 83.30, ["crude_oil"]),
        ("haldia", "Haldia", "IN", "east", 22.04, 88.06, ["crude_oil"]),
        ("chennai", "Chennai", "IN", "east", 13.08, 80.29, ["crude_oil"]),
        ("ennore", "Ennore", "IN", "east", 13.26, 80.34, ["lng"]),
        ("dhamra", "Dhamra", "IN", "east", 20.82, 87.00, ["lng"]),
        ("kakinada", "Kakinada", "IN", "east", 16.98, 82.28, ["urea", "dap", "mop"]),
        ("krishnapatnam", "Krishnapatnam", "IN", "east", 14.25, 80.13, ["urea", "dap", "mop"]),
    ]
    dump(
        SEEDS / "ports.json",
        [
            {
                "id": i,
                "name": n,
                "country_iso": c,
                "coast": coast,
                "state": STATE[i],
                "lat": lat,
                "lon": lon,
                "commodities": comm,
                "source": "IPA / World Port Index coordinates (approx port location)",
                "source_url": IPA_URL,
            }
            for i, n, c, coast, lat, lon, comm in ports
        ],
    )

    # PPAC installed capacity as of 1 Apr 2026, '000 MT -> mmtpa
    refs = [
        ("digboi", "IOC Digboi", "IOCL", 27.38, 95.62, 0.65, "paradip"),
        ("guwahati", "IOC Guwahati", "IOCL", 26.18, 91.75, 1.20, "paradip"),
        ("koyali", "IOC Koyali", "IOCL", 22.37, 73.12, 13.70, "sikka"),
        ("barauni", "IOC Barauni", "IOCL", 25.47, 86.02, 6.00, "paradip"),
        ("haldia_ref", "IOC Haldia", "IOCL", 22.03, 88.06, 8.00, "haldia"),
        ("mathura", "IOC Mathura", "IOCL", 27.49, 77.67, 8.00, "mumbai"),
        ("panipat", "IOC Panipat", "IOCL", 29.39, 76.97, 15.00, "mumbai"),
        ("bongaigaon", "IOC Bongaigaon", "IOCL", 26.47, 90.56, 2.70, "paradip"),
        ("paradip_ref", "IOC Paradip", "IOCL", 20.26, 86.61, 15.00, "paradip"),
        ("hpcl_mumbai", "HPCL Mumbai", "HPCL", 19.07, 72.88, 9.50, "mumbai"),
        ("vizag_ref", "HPCL Vizag", "HPCL", 17.69, 83.22, 15.00, "visakhapatnam"),
        ("bpcl_mumbai", "BPCL Mumbai", "BPCL", 19.07, 72.88, 12.00, "mumbai"),
        ("kochi_ref", "BPCL Kochi", "BPCL", 9.97, 76.27, 15.50, "kochi"),
        ("bina", "BPCL Bina", "BPCL", 24.18, 78.20, 7.80, "mumbai"),
        ("manali", "CPCL Manali", "CPCL", 13.17, 80.27, 10.50, "chennai"),
        ("numaligarh", "NRL Numaligarh", "NRL", 26.59, 93.74, 3.00, "paradip"),
        ("tatipaka", "ONGC Tatipaka", "ONGC", 16.55, 82.15, 0.066, "visakhapatnam"),
        ("mangalore_ref", "MRPL Mangalore", "MRPL", 12.91, 74.86, 15.00, "mangalore"),
        ("bathinda", "HMEL Bathinda", "HMEL", 30.21, 74.95, 11.30, "mumbai"),
        ("pachpadra", "HRRL Pachpadra", "HRRL", 25.80, 72.00, 9.00, "mundra"),
        ("jamnagar_dta", "RIL Jamnagar DTA", "RIL", 22.47, 69.89, 33.00, "sikka"),
        ("jamnagar_sez", "RIL Jamnagar SEZ", "RIL", 22.47, 69.89, 35.20, "sikka"),
        ("vadinar_ref", "Nayara Vadinar", "Nayara", 22.37, 69.72, 20.00, "vadinar"),
    ]
    dump(
        SEEDS / "oil" / "refineries.json",
        [
            {
                "id": i,
                "name": n,
                "operator": op,
                "state": STATE[i],
                "lat": lat,
                "lon": lon,
                "capacity": cap,
                "capacity_unit": "mmtpa",
                "year": 2026,
                "nearest_port": port,
                "source": "PPAC Installed Refining Capacity as on 1.04.2026",
                "source_url": PPAC_REF,
            }
            for i, n, op, lat, lon, cap, port in refs
        ],
    )

    terminals = [
        ("dahej", "Dahej LNG", "Petronet LNG", 21.71, 72.57, 22.5, "dahej"),
        ("hazira_lng", "Hazira LNG", "Shell", 21.12, 72.65, 5.0, "hazira"),
        ("dabhol_lng", "Dabhol LNG", "Konkan LNG / GAIL", 17.54, 73.16, 5.0, "dabhol"),
        ("kochi_lng", "Kochi LNG", "Petronet LNG", 9.97, 76.24, 5.0, "kochi"),
        ("ennore_lng", "Ennore LNG", "IOCL", 13.26, 80.34, 5.0, "ennore"),
        ("mundra_lng", "Mundra LNG", "GSPC LNG", 22.74, 69.71, 5.0, "mundra"),
        ("dhamra_lng", "Dhamra LNG", "Adani", 20.82, 87.00, 5.0, "dhamra"),
        ("jaigarh_lng", "Jaigarh LNG", "H-Energy", 17.30, 73.19, 4.0, "jaigarh"),
    ]
    dump(
        SEEDS / "lng" / "terminals.json",
        [
            {
                "id": i,
                "name": n,
                "operator": op,
                "state": STATE[i],
                "lat": lat,
                "lon": lon,
                "capacity_mtpa": cap,
                "year": 2026,
                "port": port,
                "source": "Operator nameplate; cross-check PPAC / GIIGNL 2026",
                "source_url": "https://giignl.org/",
            }
            for i, n, op, lat, lon, cap, port in terminals
        ],
    )

    plants = [
        ("iffco_kalol", "IFFCO Kalol", "IFFCO", ["urea"], 23.25, 72.49, "kandla"),
        ("iffco_paradeep", "IFFCO Paradeep", "IFFCO", ["dap", "urea"], 20.26, 86.61, "paradip"),
        ("nfl_nangal", "NFL Nangal", "NFL", ["urea"], 31.37, 76.38, "mumbai"),
        ("rcf_thal", "RCF Thal", "RCF", ["urea"], 18.73, 72.87, "mumbai"),
        ("rcf_trombay", "RCF Trombay", "RCF", ["urea"], 19.00, 72.90, "mumbai"),
        ("chambal_kota", "Chambal Fertilizers Kota", "CFCL", ["urea"], 25.18, 75.83, "kandla"),
        ("kribhco_hazira", "KRIBHCO Hazira", "KRIBHCO", ["urea"], 21.12, 72.65, "hazira"),
    ]
    dump(
        SEEDS / "fertilizer" / "plants.json",
        [
            {
                "id": i,
                "name": n,
                "operator": op,
                "state": STATE[i],
                "products": prod,
                "lat": lat,
                "lon": lon,
                "nearest_port": port,
                "source": "Company sites; DoF plant list",
                "source_url": FERT_PLANTS,
            }
            for i, n, op, prod, lat, lon, port in plants
        ],
    )

    # ISPRL Phase-I caverns; coordinates are approximate site locations
    dump(
        SEEDS / "oil" / "spr.json",
        [
            {
                "id": i,
                "name": n,
                "lat": lat,
                "lon": lon,
                "state": STATE[i],
                "capacity_mmt": cap,
                "year": 2025,
                "source": "PIB: ISPRL Phase-I SPR, 5.33 MMT at Visakhapatnam, Mangaluru, Padur",
                "source_url": PIB_SPR,
            }
            for i, n, lat, lon, cap in [
                ("spr_vizag", "ISPRL Visakhapatnam", 17.69, 83.26, 1.33),
                ("spr_mangaluru", "ISPRL Mangaluru", 12.97, 74.88, 1.50),
                ("spr_padur", "ISPRL Padur", 13.21, 74.75, 2.50),
            ]
        ],
    )

    # Constants for the LNG -> urea cascade in flow.sim
    dump(
        SEEDS / "factors.json",
        [
            {
                "id": "fertilizer_gas_share",
                "value": 0.31,
                "unit": "fraction",
                "year": 2024,
                "source": "PPAC Industry Consumption Report Feb 2024: fertilizer 31% of "
                "natural gas consumption, Apr-Feb FY2023-24 (provisional)",
                "source_url": PPAC_ICR,
            },
            {
                "id": "urea_gcal_per_t",
                "value": 6.2,
                "unit": "gcal/t",
                "year": 2024,
                "source": "NUP-2015 target energy norm for the middle group of gas-based urea "
                "units (groups: 5.5 / 6.2 / 6.5 Gcal per t); Rajya Sabha answer, 30 Jul 2024",
                "source_url": RS_UREA,
            },
            {
                "id": "lng_gcal_per_t",
                "value": 12.3,
                "unit": "gcal/t",
                "year": 2024,
                "source": "1 Mt LNG = 1.23 Mtoe and 1 toe = 10 Gcal (Energy Intelligence "
                "conversion factors)",
                "source_url": EI_CONV,
            },
            *[
                {
                    "id": f"{sector}_gas_share",
                    "value": share,
                    "unit": "fraction",
                    "year": 2024,
                    "source": f"PPAC Industry Consumption Report Feb 2024: {label} {share:.0%} of "
                    "natural gas consumption, Apr-Feb FY2023-24 (provisional)",
                    "source_url": PPAC_ICR,
                }
                for sector, label, share in [("cgd", "city gas", 0.19), ("power", "power", 0.14)]
            ],
            *[
                {
                    "id": f"{fuel}_yield",
                    "value": round(made / 261.5, 3),
                    "unit": "fraction of crude processed",
                    "year": 2024,
                    "source": f"PPAC Ready Reckoner H1 FY2024-25, Tables 4.1 and 4.4: {made} MMT "
                    f"{code} from 261.5 MMT crude processed, FY2023-24 (P)",
                    "source_url": PPAC_RR,
                }
                for fuel, code, made in [("diesel", "HSD", 115.9), ("petrol", "MS", 45.1)]
            ],
            *[
                {
                    "id": f"{fuel}_exports_mmt",
                    "value": mmt,
                    "unit": "mmt/yr",
                    "year": 2024,
                    "source": "PPAC Ready Reckoner H1 FY2024-25, Table 4.11: "
                    f"{fuel} exports FY2023-24 (P)",
                    "source_url": PPAC_RR,
                }
                for fuel, mmt in [("diesel", 28.2), ("petrol", 13.5)]
            ],
            {
                "id": "hormuz_bypass_spare_mbpd",
                "value": 2.6,
                "unit": "mb/d",
                "year": 2025,
                "source": "EIA: about 2.6 million b/d of Saudi and UAE pipeline capacity could "
                "bypass the Strait of Hormuz in a supply disruption",
                "source_url": EIA_HORMUZ,
            },
            {
                "id": "hormuz_crude_mbpd",
                "value": round(5.5 / 0.38, 1),
                "unit": "mb/d",
                "year": 2024,
                "source": "EIA: Saudi crude and condensate exports, 5.5 million b/d, were 38% of "
                "Hormuz crude flows in 2024 (5.5 / 0.38)",
                "source_url": EIA_HORMUZ,
            },
            {
                "id": "crude_bbl_per_t",
                "value": 7.33,
                "unit": "bbl/t",
                "year": 2024,
                "source": "Energy Institute Statistical Review of World Energy, approximate "
                "conversion factors: 1 tonne of crude oil = 7.33 barrels",
                "source_url": EI_REVIEW,
            },
            *[
                {
                    "id": f"{c}_consumption_mmt",
                    "value": round(lmt / 10, 3),
                    "unit": "mmt/yr",
                    "year": 2025,
                    "source": f"Rajya Sabha Unstarred Q.3550 (24.03.2026) annexure via PIB: {lmt} "
                    f"LMT {c.upper()} DBT sales in FY2024-25",
                    "source_url": PIB_FERT,
                }
                for c, lmt in [("urea", 387.92), ("dap", 96.29), ("mop", 22.02)]
            ],
        ],
    )

    # Guard the hand-copied tables against their published totals
    assert abs(sum(d for d, _ in FUEL_TMT.values()) - 89584.8) < 0.5  # sum of PPAC region rows
    assert abs(sum(m for _, m in FUEL_TMT.values()) - 37219.3) < 0.5
    assert sum(HOLDINGS.values()) == 146453741
    for i, total in enumerate([94.78, 22.82, 5.20]):
        assert abs(sum(v[i] for v in FERT_SALES.values()) - total) < 0.1, total
    assert abs(sum(UREA_OUTPUT.values()) - 306.67) < 0.05
    for fuel, rows in SEGMENTS.items():
        assert abs(sum(pct for _, pct in rows) - 100) < 0.2, fuel

    rr = "PPAC Ready Reckoner H1 FY2024-25, Table 6.4({}): {} industry sales FY2023-24 (P)"
    ls = "Lok Sabha Starred Q.94 (24.07.2026), Annexure-{}"
    stats = [
        *(
            (st, metric, v, "tmt", 2024, rr.format(t, code), PPAC_RR)
            for st, pair in FUEL_TMT.items()
            for (metric, t, code), v in zip([("diesel", "C", "HSD"), ("petrol", "B", "MS")], pair)
        ),
        *(
            (
                st,
                "farm_holdings",
                n,
                "count",
                2016,
                "Agriculture Census 2015-16, State Tables: "
                "operational holdings, all size classes and social groups",
                AGCENSUS,
            )
            for st, n in HOLDINGS.items()
        ),
        *(
            (
                st,
                f"{c}_sales",
                v,
                "lmt",
                2026,
                ls.format("II") + ": DBT sales, Kharif 2026 "
                "(01.04-19.07.26); used as state shares only",
                LS_UREA,
            )
            for st, trio in FERT_SALES.items()
            for c, v in zip(("urea", "dap", "mop"), trio)
            if v
        ),
        *(
            (
                st,
                "urea_production",
                v,
                "lmt",
                2025,
                ls.format("I") + ": urea production 2024-25",
                LS_UREA,
            )
            for st, v in UREA_OUTPUT.items()
        ),
    ]
    dump(
        SEEDS / "states.json",
        [
            dict(zip(("state", "metric", "value", "unit", "year", "source", "source_url"), row))
            for row in stats
        ],
    )
    dump(
        SEEDS / "segments.json",
        [
            {
                "fuel": fuel,
                "segment": name,
                "share": round(pct / sum(p for _, p in rows), 4),
                "year": 2021,
                "source": "PPAC all-India study on sectoral demand for petrol and diesel "
                "(Oct 2020 - Sep 2021), "
                + ("Fig. 17, retail and direct" if fuel == "diesel" else "Fig. 10, retail"),
                "source_url": PPAC_SECTORAL,
            }
            for fuel, rows in SEGMENTS.items()
            for name, pct in rows
        ],
    )

    def imports(commodity: str, year: int, source: str, url: str, rows: list[tuple]) -> list[dict]:
        return [
            {
                "commodity": commodity,
                "supplier_iso": iso,
                "supplier_name": name,
                "volume": vol,
                "unit": "mmt",
                "year": year,
                "share_of_india_imports": share,
                "source": source,
                "source_url": url,
            }
            for iso, name, vol, share in rows
        ]

    # WITS/Comtrade HS 2709, calendar 2024, kg -> mmt
    dump(
        SEEDS / "oil" / "imports.json",
        imports(
            "crude_oil",
            2024,
            "WITS/UN Comtrade HS 2709 quantity, calendar 2024",
            WITS_OIL,
            [
                ("RU", "Russia", 92.009, 0.3806),
                ("IQ", "Iraq", 50.091, 0.2072),
                ("SA", "Saudi Arabia", 31.723, 0.1312),
                ("AE", "United Arab Emirates", 21.251, 0.0879),
                ("NG", "Nigeria", 6.396, 0.0265),
                ("US", "United States", 5.959, 0.0247),
                ("AO", "Angola", 5.782, 0.0239),
                ("KW", "Kuwait", 5.252, 0.0217),
                ("VE", "Venezuela", 3.729, 0.0154),
                ("CO", "Colombia", 3.442, 0.0142),
                ("MX", "Mexico", 3.250, 0.0134),
                ("XX", "Other", 12.866, 0.0532),
            ],
        ),
    )

    # WITS/Comtrade HS 271111, calendar 2024, kg -> mmt
    dump(
        SEEDS / "lng" / "imports.json",
        imports(
            "lng",
            2024,
            "WITS/UN Comtrade HS 271111 quantity, calendar 2024",
            WITS_LNG,
            [
                ("QA", "Qatar", 11.304, 0.4067),
                ("US", "United States", 5.420, 0.1950),
                ("AE", "United Arab Emirates", 3.164, 0.1138),
                ("AO", "Angola", 1.968, 0.0708),
                ("OM", "Oman", 1.459, 0.0525),
                ("NG", "Nigeria", 1.424, 0.0512),
                ("GQ", "Equatorial Guinea", 0.967, 0.0348),
                ("CM", "Cameroon", 0.795, 0.0286),
                ("MZ", "Mozambique", 0.588, 0.0212),
                ("TT", "Trinidad and Tobago", 0.380, 0.0137),
                ("XX", "Other", 0.325, 0.0117),
            ],
        ),
    )

    # Parliament annex FY 2024-25, LMT / 10 = MMT
    dump(
        SEEDS / "fertilizer" / "imports.json",
        imports(
            "urea",
            2024,
            "Rajya Sabha annex AS41, FY 2024-25, LMT converted to MMT",
            FERT_REPORTS,
            [
                ("OM", "Oman", 2.613, 0.4627),
                ("RU", "Russia", 0.923, 0.1634),
                ("SA", "Saudi Arabia", 0.538, 0.0953),
                ("QA", "Qatar", 0.370, 0.0655),
                ("NG", "Nigeria", 0.283, 0.0501),
                ("XX", "Other", 0.920, 0.1629),
            ],
        )
        + imports(
            "dap",
            2024,
            "Rajya Sabha annex AS41, FY 2024-25, LMT converted to MMT",
            FERT_REPORTS,
            [
                ("SA", "Saudi Arabia", 1.905, 0.4170),
                ("MA", "Morocco", 1.074, 0.2351),
                ("CN", "China", 0.847, 0.1854),
                ("XX", "Other", 0.743, 0.1626),
            ],
        )
        + imports(
            "mop",
            2024,
            "Rajya Sabha annex AS41, FY 2024-25, LMT converted to MMT",
            FERT_REPORTS,
            [
                ("RU", "Russia", 1.800, 0.5083),
                ("CA", "Canada", 0.883, 0.2494),
                ("JO", "Jordan", 0.301, 0.0850),
                ("IL", "Israel", 0.280, 0.0791),
                ("TM", "Turkmenistan", 0.277, 0.0782),
            ],
        ),
    )

    def route(
        rid: str,
        commodity: str,
        iso: str,
        chokepoints: list[str],
        port: str,
        volume: float,
        facility: str | None = None,
    ) -> dict:
        return {
            "id": rid,
            "commodity": commodity,
            "supplier_iso": iso,
            **dict(zip(("origin", "origin_lat", "origin_lon"), ORIGIN.get(rid, (None,) * 3))),
            "chokepoints": chokepoints,
            "indian_port": port,
            "indian_facility": facility,
            "volume": volume,
            "unit": "mmt",
            "year": 2024,
            "source": "Assigned from import mix and typical seaborne path to west-coast India",
            "source_url": EIA,
        }

    gulf = ["hormuz"]
    cape = ["cape"]
    malacca = ["malacca"]
    mandeb = ["bab_el_mandeb"]

    oil_routes = [
        route("oil-RU-sikka", "crude_oil", "RU", cape, "sikka", 92.009, "jamnagar_sez"),
        route("oil-IQ-sikka", "crude_oil", "IQ", gulf, "sikka", 50.091, "jamnagar_dta"),
        route("oil-SA-sikka", "crude_oil", "SA", gulf, "sikka", 31.723, "vadinar_ref"),
        route("oil-AE-mundra", "crude_oil", "AE", gulf, "mundra", 21.251, "koyali"),
        route("oil-NG-mumbai", "crude_oil", "NG", cape, "mumbai", 6.396, "bpcl_mumbai"),
        route("oil-US-sikka", "crude_oil", "US", cape, "sikka", 5.959, "jamnagar_sez"),
        route("oil-AO-sikka", "crude_oil", "AO", cape, "sikka", 5.782, "jamnagar_dta"),
        route("oil-KW-sikka", "crude_oil", "KW", gulf, "sikka", 5.252, "vadinar_ref"),
        route("oil-VE-sikka", "crude_oil", "VE", cape, "sikka", 3.729, "jamnagar_sez"),
        route("oil-CO-sikka", "crude_oil", "CO", cape, "sikka", 3.442, "jamnagar_dta"),
        route("oil-MX-sikka", "crude_oil", "MX", cape, "sikka", 3.250, "jamnagar_sez"),
        route("oil-XX-paradip", "crude_oil", "XX", malacca, "paradip", 12.866, "paradip_ref"),
    ]
    dump(SEEDS / "oil" / "routes.json", oil_routes)

    lng_routes = [
        route("lng-QA-dahej", "lng", "QA", gulf, "dahej", 11.304, "dahej"),
        route("lng-US-dahej", "lng", "US", cape, "dahej", 5.420, "dahej"),
        route("lng-AE-hazira", "lng", "AE", gulf, "hazira", 3.164, "hazira_lng"),
        route("lng-AO-dahej", "lng", "AO", cape, "dahej", 1.968, "dahej"),
        route("lng-OM-dahej", "lng", "OM", [], "dahej", 1.459, "dahej"),
        route("lng-NG-dahej", "lng", "NG", cape, "dahej", 1.424, "dahej"),
        route("lng-GQ-dahej", "lng", "GQ", cape, "dahej", 0.967, "dahej"),
        route("lng-CM-dahej", "lng", "CM", cape, "dahej", 0.795, "dahej"),
        # Mozambique is on the Indian Ocean: no Cape rounding to reach India
        route("lng-MZ-dhamra", "lng", "MZ", [], "dhamra", 0.588, "dhamra_lng"),
        route("lng-TT-dahej", "lng", "TT", cape, "dahej", 0.380, "dahej"),
        route("lng-XX-kochi", "lng", "XX", [], "kochi", 0.325, "kochi_lng"),
    ]
    dump(SEEDS / "lng" / "routes.json", lng_routes)

    fert_routes = [
        route("urea-OM-kandla", "urea", "OM", [], "kandla", 2.613),
        route("urea-RU-kandla", "urea", "RU", cape, "kandla", 0.923),
        route("urea-SA-kandla", "urea", "SA", gulf, "kandla", 0.538),
        route("urea-QA-kandla", "urea", "QA", gulf, "kandla", 0.370),
        route("urea-NG-kandla", "urea", "NG", cape, "kandla", 0.283),
        route("urea-XX-paradip", "urea", "XX", malacca, "paradip", 0.920),
        route("dap-SA-kandla", "dap", "SA", gulf, "kandla", 1.905),
        route("dap-MA-kandla", "dap", "MA", cape, "kandla", 1.074),
        route("dap-CN-paradip", "dap", "CN", malacca, "paradip", 0.847),
        route("dap-XX-kakinada", "dap", "XX", malacca, "kakinada", 0.743),
        route("mop-RU-kandla", "mop", "RU", cape, "kandla", 1.800),
        route(
            "mop-CA-kandla", "mop", "CA", malacca, "kandla", 0.883
        ),  # Vancouver, across the Pacific
        route("mop-JO-kandla", "mop", "JO", mandeb, "kandla", 0.301),
        route("mop-IL-kandla", "mop", "IL", mandeb, "kandla", 0.280),
        route("mop-TM-kandla", "mop", "TM", gulf, "kandla", 0.277),
    ]
    dump(SEEDS / "fertilizer" / "routes.json", fert_routes)

    rr_gas = "PPAC Ready Reckoner H1 FY2024-25, Table 5.1: natural gas pipelines, as on 01.10.2024"
    rr_crude = "PPAC Ready Reckoner H1 FY2024-25, Table 5.2: crude oil pipelines, as on 01.10.2024"
    # id, name, fluid, operator, sites in flow order, capacity, unit, km, status, source
    domestic = [
        (
            "smpl",
            "Salaya-Mathura pipeline",
            "crude",
            "IOCL",
            ["port:vadinar", "refinery:koyali", "refinery:mathura", "refinery:panipat"],
            25.0,
            "mmtpa",
            2646,
            "operational",
            rr_crude,
        ),
        (
            "phbpl",
            "Paradip-Haldia-Barauni pipeline",
            "crude",
            "IOCL",
            ["port:paradip", "refinery:haldia_ref", "refinery:barauni"],
            20.4,
            "mmtpa",
            1873,
            "operational",
            rr_crude,
        ),
        (
            "mundra_panipat",
            "Mundra-Panipat pipeline",
            "crude",
            "IOCL",
            ["port:mundra", "refinery:panipat"],
            8.4,
            "mmtpa",
            1194,
            "operational",
            rr_crude,
        ),
        (
            "mundra_bathinda",
            "Mundra-Bathinda pipeline",
            "crude",
            "HMPL",
            ["port:mundra", "refinery:bathinda"],
            11.3,
            "mmtpa",
            1017,
            "operational",
            rr_crude,
        ),
        (
            "vadinar_bina",
            "Vadinar-Bina pipeline",
            "crude",
            "BPCL",
            ["port:vadinar", "refinery:bina"],
            7.8,
            "mmtpa",
            937,
            "operational",
            rr_crude,
        ),
        (
            "ddbb",
            "Duliajan-Digboi-Bongaigaon-Barauni pipeline (Assam crude)",
            "crude",
            "OIL",
            ["refinery:digboi", "refinery:guwahati", "refinery:bongaigaon", "refinery:barauni"],
            9.0,
            "mmtpa",
            1195,
            "operational",
            rr_crude,
        ),
        (
            "hvj",
            "Hazira-Vijaipur-Jagdishpur / Dahej-Vijaipur (HVJ-GREP-DVPL), with the "
            "Dadri-Bawana-Nangal spur",
            "gas",
            "GAIL",
            [
                "lng_terminal:dahej",
                "lng_terminal:hazira_lng",
                "fertilizer_plant:kribhco_hazira",
                "fertilizer_plant:chambal_kota",
                "fertilizer_plant:nfl_nangal",
            ],
            107.0,
            "mmscmd",
            6725,
            "operational",
            rr_gas,
        ),
        (
            "dupl",
            "Dahej-Uran-Panvel-Dabhol pipeline",
            "gas",
            "GAIL",
            [
                "lng_terminal:dahej",
                "fertilizer_plant:rcf_trombay",
                "fertilizer_plant:rcf_thal",
                "lng_terminal:dabhol_lng",
            ],
            19.9,
            "mmscmd",
            943,
            "operational",
            rr_gas,
        ),
        (
            "gujarat_grid",
            "Gujarat high-pressure gas grid",
            "gas",
            "GSPL",
            [
                "lng_terminal:mundra_lng",
                "fertilizer_plant:iffco_kalol",
                "lng_terminal:dahej",
                "lng_terminal:hazira_lng",
            ],
            31.0,
            "mmscmd",
            2657,
            "operational",
            rr_gas,
        ),
        (
            "kkbmpl",
            "Kochi-Koottanad-Bengaluru-Mangalore pipeline",
            "gas",
            "GAIL",
            ["lng_terminal:kochi_lng", "refinery:mangalore_ref"],
            12.0,
            "mmscmd",
            642,
            "part operational",
            rr_gas,
        ),
        (
            "jhbdpl",
            "Jagdishpur-Haldia-Bokaro-Dhamra-Paradip-Barauni-Guwahati (Urja Ganga)",
            "gas",
            "GAIL",
            [
                "lng_terminal:dhamra_lng",
                "fertilizer_plant:iffco_paradeep",
                "refinery:haldia_ref",
                "refinery:barauni",
                "refinery:guwahati",
            ],
            7.44,
            "mmscmd",
            2383,
            "part operational",
            rr_gas,
        ),
        (
            "etbpnmt",
            "Ennore-Thiruvallur-Bengaluru-Puducherry-Nagapattinam-Madurai-Tuticorin",
            "gas",
            "IOCL",
            ["lng_terminal:ennore_lng", "refinery:manali"],
            84.67,
            "mmscmd",
            1421,
            "part operational",
            rr_gas,
        ),
    ]
    bypass = [  # id, name, operator, supplier, bypasses, start, end, mb/d, source, url
        (
            "east_west",
            "East-West crude pipeline (Abqaiq-Yanbu)",
            "Saudi Aramco",
            "SA",
            ["hormuz"],
            ("Abqaiq", 25.93, 49.67),
            ("Yanbu", 24.09, 38.06),
            5.0,
            "EIA: 5 million b/d East-West pipeline from Abqaiq to Yanbu on the Red Sea",
            EIA_HORMUZ,
        ),
        (
            "adcop",
            "Abu Dhabi Crude Oil Pipeline (Habshan-Fujairah)",
            "ADNOC",
            "AE",
            ["hormuz"],
            ("Habshan", 23.83, 53.62),
            ("Fujairah", 25.17, 56.36),
            1.8,
            "EIA: 1.8 million b/d pipeline to the Fujairah terminal on the Gulf of Oman",
            EIA_HORMUZ,
        ),
        (
            "sumed",
            "SUMED pipeline (Ain Sukhna-Sidi Kerir)",
            "Mubadala Energy",
            None,
            ["suez"],
            ("Ain Sukhna", 29.60, 32.35),
            ("Sidi Kerir", 31.10, 29.65),
            2.5,
            "EIA: SUMED carries crude north through Egypt, 2.5 million b/d",
            EIA_CHOKEPOINTS,
        ),
    ]
    dump(
        SEEDS / "pipelines.json",
        [
            {
                "id": i,
                "name": n,
                "fluid": fluid,
                "scope": "domestic",
                "operator": op,
                "sites": sites,
                "capacity": cap,
                "capacity_unit": unit,
                "length_km": km,
                "status": status,
                "year": 2024,
                "source": src,
                "source_url": PPAC_RR,
            }
            for i, n, fluid, op, sites, cap, unit, km, status, src in domestic
        ]
        + [
            {
                "id": i,
                "name": n,
                "fluid": "crude",
                "scope": "bypass",
                "operator": op,
                "supplier_iso": iso,
                "bypasses": around,
                **dict(zip(("start_name", "start_lat", "start_lon"), start)),
                **dict(zip(("end_name", "end_lat", "end_lon"), end)),
                "capacity": mbpd,
                "capacity_unit": "mbpd",
                "status": "operational",
                "year": 2025,
                "source": src,
                "source_url": url,
            }
            for i, n, op, iso, around, start, end, mbpd, src, url in bypass
        ],
    )

    # Sea paths: every route from its export terminal, and every bypass outlet to the Indian port
    # that supplier's crude lands at. Each seeded chokepoint list must be one of the real paths.
    ports_at = {p[0]: (p[4], p[5]) for p in ports}
    paths = []
    for r in oil_routes + lng_routes + fert_routes:
        if r["origin"]:
            found = sea_paths(
                r["id"], (r["origin_lat"], r["origin_lon"]), ports_at[r["indian_port"]]
            )
            assert sorted(r["chokepoints"]) in [p["passes"] for p in found], (r["id"], found)
            paths += found
    for i, _, _, iso, _, _, end, *_ in bypass:
        for r in oil_routes:
            if r["supplier_iso"] == iso:
                paths += sea_paths(f"{i}>{r['indian_port']}", end[1:], ports_at[r["indian_port"]])
    dump(SEEDS / "sea_paths.json", paths)


if __name__ == "__main__":
    main()
