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
