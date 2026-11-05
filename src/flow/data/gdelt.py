"""Fetch GDELT 2.0 GKG slices and keep rows about our commodities and places."""

from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd

LASTUPDATE = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
GKG_BASE = "http://data.gdeltproject.org/gdeltv2"
HEADERS = {"User-Agent": "Mozilla/5.0"}

GKG_COLUMNS = [
    "GKGRECORDID",
    "DATE",
    "SourceCollectionIdentifier",
    "SourceCommonName",
    "DocumentIdentifier",
    "Counts",
    "V2Counts",
    "Themes",
    "V2Themes",
    "Locations",
    "V2Locations",
    "Persons",
    "V2Persons",
    "Organizations",
    "V2Organizations",
    "V2Tone",
    "Dates",
    "GCAM",
    "SharingImage",
    "RelatedImages",
    "SocialImageEmbeds",
    "SocialVideoEmbeds",
    "Quotations",
    "AllNames",
    "Amounts",
    "TranslationInfo",
    "Extras",
]

# Only commodity-specific themes. Broad ones (ENERGY, SANCTIONS, TAX_FNCACT_FARMER,
# UNGP_FORESTS_RIVERS_OCEANS) let in crime and celebrity stories by the hundred.
THEME_RE = r"\b(?:ENV_OIL|ENV_GAS|ECON_OILPRICE)\b"
# Word boundaries throughout: a bare substring finds "urea" in "bureau" and "dap" in "adapt".
KEYWORD_RE = (
    r"\b(?:crude|opec|petroleum|refiner|hormuz|lng|natural gas|brent crude|urea|"
    r"diammonium|potash|fertili[sz]er|iffco|malacca|bab[ -]el[ -]mandeb|suez|cape of good hope)"
)

# ponytail: hardcoded aliases until seeds exist; then read chokepoints.json / suppliers.json
ENTITY_ALIASES = {
    "strait of hormuz": "hormuz",
    "hormuz": "hormuz",
    "strait of malacca": "malacca",
    "malacca": "malacca",
    "bab el-mandeb": "bab_el_mandeb",
    "bab-el-mandeb": "bab_el_mandeb",
    "bab el mandeb": "bab_el_mandeb",
    "suez": "suez",
    "cape of good hope": "cape",
    "qatar": "QA",
    "saudi arabia": "SA",
    "united arab emirates": "AE",
    "russia": "RU",
    "iraq": "IQ",
    "kuwait": "KW",
    "united states": "US",
    "australia": "AU",
    "china": "CN",
    "canada": "CA",
    "dahej": "dahej",
    "hazira": "hazira",
    "jamnagar": "jamnagar",
    "paradip": "paradip",
    "mundra": "mundra",
}

# Matched against lowercased themes, names and URL. Bare "dap" and "mop" are left out on
# purpose: they are mostly Malaysia's DAP party and "mop up".
# GDELT's ENV_OIL / ENV_GAS themes alone are too loose (they tag EPA budgets and road works),
# so a theme counts only when the URL or names also say "oil" / "gas". The haystack puts
# themes first, and "\boil\b" never matches inside a theme token like "env_oil".
COMMODITY_HINTS = {
    "crude_oil": (
        r"\b(?:crude|petroleum|opec|brent crude|refiner)|\b(?:env_oil|econ_oilprice)\b.*\boil\b"
    ),
    "lng": r"\blng\b|\bnatural gas\b|\benv_gas\b.*\bgas\b",
    "urea": r"\burea\b",
    "dap": r"\bdiammonium\b|\bdap fertili[sz]er",
    "mop": r"\bpotash\b|\bpotassium chloride\b|\bmuriate of potash\b",
}
ALIAS_RE = {k: re.compile(rf"\b{re.escape(k)}\b") for k in ENTITY_ALIASES}
COMMODITY_RE = {k: re.compile(v, re.S) for k, v in COMMODITY_HINTS.items()}
# Chokepoint and port ids are lowercase; supplier countries are ISO codes. A country name
# alone (most of the news mentions the United States) does not make an article relevant.
PLACE_IDS = {v for v in ENTITY_ALIASES.values() if v.islower()}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def raw_dir() -> Path:
    path = repo_root() / "data" / "raw"
    path.mkdir(parents=True, exist_ok=True)
    return path


def latest_gkg_stamp(client: httpx.Client) -> str:
    text = client.get(LASTUPDATE, timeout=30).text
    line = next(item for item in text.splitlines() if item.strip().endswith("gkg.csv.zip"))
    filename = line.strip().split()[-1].rsplit("/", 1)[-1]
    return filename.removesuffix(".gkg.csv.zip")


def gkg_stamps(latest: str, slices: int) -> list[str]:
    start = datetime.strptime(latest, "%Y%m%d%H%M%S")
    return [(start - timedelta(minutes=15 * i)).strftime("%Y%m%d%H%M%S") for i in range(slices)]


def load_gkg(client: httpx.Client, stamp: str) -> pd.DataFrame:
    url = f"{GKG_BASE}/{stamp}.gkg.csv.zip"
    response = client.get(url, timeout=120)
    if response.status_code == 404:
        raise FileNotFoundError(url)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        name = archive.namelist()[0]
        return pd.read_csv(
            archive.open(name),
            sep="\t",
            header=None,
            names=GKG_COLUMNS,
            dtype=str,
            on_bad_lines="skip",
            encoding_errors="replace",
        )


def filter_rows(frame: pd.DataFrame) -> pd.DataFrame:
    themes = frame["V2Themes"].fillna("")
    urls = frame["DocumentIdentifier"].fillna("")
    names = frame["AllNames"].fillna("")
    blob = themes + " " + urls + " " + names
    mask = blob.str.contains(THEME_RE + "|" + KEYWORD_RE, case=False, regex=True)
    return frame.loc[mask]


def _haystack(row: pd.Series) -> str:
    parts = [
        str(row.get("V2Themes") or ""),
        str(row.get("V2Locations") or ""),
        str(row.get("V2Organizations") or ""),
        str(row.get("AllNames") or ""),
        str(row.get("DocumentIdentifier") or ""),
    ]
    return " ".join(parts).lower()


def entities_in(text: str) -> list[str]:
    found: list[str] = []
    for needle, entity_id in ENTITY_ALIASES.items():
        if entity_id not in found and ALIAS_RE[needle].search(text):
            found.append(entity_id)
    return found


def commodities_in(text: str) -> list[str]:
    return [c for c, pattern in COMMODITY_RE.items() if pattern.search(text)]


def parse_tone(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return float(raw.split(",")[0])
    except ValueError:
        return None


def parse_when(raw: str | None) -> str:
    if not raw or len(raw) < 14:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.strptime(raw[:14], "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%SZ")


def row_to_event(row: pd.Series) -> dict | None:
    text = _haystack(row)
    entities = entities_in(text)
    commodities = commodities_in(text)
    if not commodities and not PLACE_IDS.intersection(entities):
        return None
    event_id = str(row.get("GKGRECORDID") or row.get("DocumentIdentifier") or "")
    url = str(row.get("DocumentIdentifier") or "")
    if not event_id or not url:
        return None
    return {
        "event_id": event_id,
        "observed_at": parse_when(row.get("DATE")),
        "source_name": str(row.get("SourceCommonName") or ""),
        "url": url,
        "tone": parse_tone(row.get("V2Tone")),
        "entities": entities,
        "commodities": commodities,
    }


def events_from_frame(frame: pd.DataFrame) -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()
    for _, row in filter_rows(frame).iterrows():
        event = row_to_event(row)
        if event is None or event["event_id"] in seen:
            continue
        seen.add(event["event_id"])
        events.append(event)
    return events


def write_jsonl(events: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _events_for(client: httpx.Client, stamps: list[str]) -> list[dict]:
    frames = []
    for stamp in stamps:
        try:
            frames.append(load_gkg(client, stamp))
        except FileNotFoundError:
            continue
    if not frames:
        raise RuntimeError(f"no GKG slices downloaded for {stamps}")
    return events_from_frame(pd.concat(frames, ignore_index=True))


def fetch(slices: int = 1) -> Path:
    if slices < 1:
        raise ValueError("slices must be >= 1")
    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        stamps = gkg_stamps(latest_gkg_stamp(client), slices)
        events = _events_for(client, stamps)
    out = raw_dir() / f"events-{stamps[0]}.jsonl"
    write_jsonl(events, out)
    (raw_dir() / "events.jsonl").write_bytes(out.read_bytes())
    return out


def refilter() -> dict[str, tuple[int, int]]:
    """Re-download the GKG slices behind every data/raw/events-*.jsonl and filter them again.

    GDELT keeps old slices, so a stricter filter can be applied to news already pulled.
    Returns {file name: (events before, events after)}.
    """
    files = sorted(raw_dir().glob("events-*.jsonl"))
    counts = {}
    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for path in files:
            old = [
                json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()
            ]
            stamps = sorted({re.sub(r"\D", "", e["observed_at"]) for e in old}, reverse=True)
            if not stamps:
                continue
            events = _events_for(client, stamps)
            write_jsonl(events, path)
            counts[path.name] = (len(old), len(events))
    if files:
        (raw_dir() / "events.jsonl").write_bytes(files[-1].read_bytes())
    return counts
