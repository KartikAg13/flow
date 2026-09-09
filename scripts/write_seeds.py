"""One-shot writer for data/seeds/*.json. Numbers are cited in each row."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"

WITS_OIL = "https://wits.worldbank.org/trade/comtrade/en/country/IND/year/2024/tradeflow/Imports/partner/ALL/product/270900"
WITS_LNG = "https://wits.worldbank.org/trade/comtrade/en/country/IND/year/2024/tradeflow/Imports/partner/ALL/product/271111"
PPAC_REF = "https://ppac.gov.in/infrastructure/installed-refinery-capacity"
SANSAD = "https://sansad.in/getFile/annex/270/AS41_r2YfWE.pdf"
EIA = "https://www.eia.gov/international/analysis/special-topics/World_Oil_Transit_Chokepoints"


def dump(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"{len(rows):3d}  {path.relative_to(ROOT)}")


def main() -> None:
    dump(
        SEEDS / "suppliers.json",
        [
            {"iso": iso, "name": name}
            for iso, name in [
                ("IN", "India"),
                ("RU", "Russia"),
                ("IQ", "Iraq"),
                ("SA", "Saudi Arabia"),
                ("AE", "United Arab Emirates"),
                ("US", "United States"),
                ("NG", "Nigeria"),
                ("AO", "Angola"),
                ("KW", "Kuwait"),
                ("VE", "Venezuela"),
                ("CO", "Colombia"),
                ("MX", "Mexico"),
                ("QA", "Qatar"),
                ("OM", "Oman"),
                ("GQ", "Equatorial Guinea"),
                ("CM", "Cameroon"),
                ("MZ", "Mozambique"),
                ("TT", "Trinidad and Tobago"),
                ("AU", "Australia"),
                ("MA", "Morocco"),
                ("CN", "China"),
                ("CA", "Canada"),
                ("JO", "Jordan"),
                ("IL", "Israel"),
                ("TM", "Turkmenistan"),
                ("XX", "Other"),
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
                "lat": lat,
                "lon": lon,
                "commodities": comm,
                "source": "IPA / World Port Index coordinates (approx port location)",
                "source_url": "https://www.ipa.nic.in/",
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
        ("dahej", "Dahej LNG", "Petronet LNG", 21.71, 72.57, 17.5, "dahej"),
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
                "lat": lat,
                "lon": lon,
                "capacity_mtpa": cap,
                "year": 2025,
                "port": port,
                "source": "Operator nameplate; cross-check PPAC / GIIGNL 2025",
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
                "products": prod,
                "lat": lat,
                "lon": lon,
                "nearest_port": port,
                "source": "Company sites; DoF plant list",
                "source_url": "https://www.fert.nic.in/",
            }
            for i, n, op, prod, lat, lon, port in plants
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
            SANSAD,
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
            SANSAD,
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
            SANSAD,
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
    red = ["suez", "bab_el_mandeb"]

    oil_routes = [
        route("oil-RU-sikka", "crude_oil", "RU", cape, "sikka", 92.009, "jamnagar_sez"),
        route("oil-IQ-sikka", "crude_oil", "IQ", gulf, "sikka", 50.091, "jamnagar_dta"),
        route("oil-SA-sikka", "crude_oil", "SA", gulf, "sikka", 31.723, "vadinar_ref"),
        route("oil-AE-sikka", "crude_oil", "AE", gulf, "mundra", 21.251, "koyali"),
        route("oil-NG-sikka", "crude_oil", "NG", cape, "mumbai", 6.396, "bpcl_mumbai"),
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
        route("lng-OM-dahej", "lng", "OM", gulf, "dahej", 1.459, "dahej"),
        route("lng-NG-dahej", "lng", "NG", cape, "dahej", 1.424, "dahej"),
        route("lng-GQ-dahej", "lng", "GQ", cape, "dahej", 0.967, "dahej"),
        route("lng-CM-dahej", "lng", "CM", cape, "dahej", 0.795, "dahej"),
        route("lng-MZ-dhamra", "lng", "MZ", cape, "dhamra", 0.588, "dhamra_lng"),
        route("lng-TT-dahej", "lng", "TT", cape, "dahej", 0.380, "dahej"),
        route("lng-XX-kochi", "lng", "XX", [], "kochi", 0.325, "kochi_lng"),
    ]
    dump(SEEDS / "lng" / "routes.json", lng_routes)

    fert_routes = [
        route("urea-OM-kandla", "urea", "OM", gulf, "kandla", 2.613),
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
        route("mop-CA-kandla", "mop", "CA", cape, "kandla", 0.883),
        route("mop-JO-kandla", "mop", "JO", red, "kandla", 0.301),
        route("mop-IL-kandla", "mop", "IL", red, "kandla", 0.280),
        route("mop-TM-kandla", "mop", "TM", gulf, "kandla", 0.277),
    ]
    dump(SEEDS / "fertilizer" / "routes.json", fert_routes)


if __name__ == "__main__":
    main()
