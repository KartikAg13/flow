import pandas as pd

from flow.data.gdelt import commodities_in, entities_in, events_from_frame, gkg_stamps, parse_tone


def test_gkg_stamps_step_back_15_minutes() -> None:
    assert gkg_stamps("20260822121500", 2) == ["20260822121500", "20260822120000"]


def test_tone_takes_first_csv_field() -> None:
    assert parse_tone("1.25,2,3,4,5,6,7") == 1.25


def test_hormuz_oil_row_becomes_event() -> None:
    frame = pd.DataFrame(
        [
            {
                "GKGRECORDID": "20260822-1",
                "DATE": "20260822121500",
                "SourceCommonName": "reuters.com",
                "DocumentIdentifier": "https://example.com/hormuz-oil",
                "V2Themes": "ENV_OIL;",
                "V2Locations": "Strait of Hormuz",
                "V2Organizations": "",
                "V2Tone": "-3.1,0,0,0,0,0,10",
                "AllNames": "Qatar;Saudi Arabia",
            },
            {
                "GKGRECORDID": "20260822-2",
                "DATE": "20260822121500",
                "SourceCommonName": "example.com",
                "DocumentIdentifier": "https://example.com/sports",
                "V2Themes": "SPORT;",
                "V2Locations": "",
                "V2Organizations": "",
                "V2Tone": "0,0,0,0,0,0,1",
                "AllNames": "Football",
            },
        ]
    )
    events = events_from_frame(frame)
    assert len(events) == 1
    event = events[0]
    assert event["event_id"] == "20260822-1"
    assert "hormuz" in event["entities"]
    assert "QA" in event["entities"]
    assert "crude_oil" in event["commodities"]
    assert event["tone"] == -3.1


def test_alias_and_commodity_hints() -> None:
    text = "urea cargo delayed at mundra after potash talks"
    assert "mundra" in entities_in(text)
    assert "urea" in commodities_in(text)
    assert "mop" in commodities_in(text)
    # whole words only: "bureau" is not urea, "adapt" is not DAP, Chinatown is not China
    assert commodities_in("ukrainian bureau of investigation adapts to scam calls") == []
    assert entities_in("chinatown parade") == []


def test_country_only_and_broad_theme_rows_are_dropped() -> None:
    def row(i: int, themes: str, url: str, names: str = "") -> dict:
        return {
            "GKGRECORDID": f"r{i}",
            "DATE": "20261104160000",
            "SourceCommonName": "x.com",
            "DocumentIdentifier": url,
            "V2Themes": themes,
            "V2Locations": "Cleveland, Tennessee, United States",
            "V2Organizations": "",
            "V2Tone": "-13.9,0,0,0,0,0,1",
            "AllNames": names,
        }

    frame = pd.DataFrame(
        [
            row(1, "SANCTIONS;", "https://x.com/news/jail-dockets-11-4-26"),
            row(2, "UNGP_FORESTS_RIVERS_OCEANS;", "https://x.com/christa-pike-execution"),
            row(3, "ENERGY;", "https://x.com/top-officials-covered-up-for-scam-call-bureau"),
            row(4, "ENV_OIL;", "https://x.com/oil-tanker-attacked-strait-of-hormuz"),
            row(5, "ENV_OIL,120;", "https://x.com/epa-splurges-13-8m-on-training"),
        ]
    )
    assert [e["event_id"] for e in events_from_frame(frame)] == ["r4"]
