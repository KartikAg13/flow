from flow.data.build import build


def test_build_loads_seeds_and_hormuz_has_oil(tmp_path) -> None:
    db = build(tmp_path / "flow.db")
    import sqlite3

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM commodities").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM chokepoints").fetchone()[0] == 5
    oil = conn.execute(
        """
        SELECT SUM(r.volume) FROM routes r
        JOIN route_chokepoints rc ON rc.route_id = r.id
        WHERE rc.chokepoint_id = 'hormuz' AND r.commodity = 'crude_oil'
        """
    ).fetchone()[0]
    assert oil and oil > 100
    assert conn.execute("SELECT sum(capacity_mmt) FROM spr_sites").fetchone()[0] == 5.33
    conn.close()


def test_seed_models_reject_bad_rows() -> None:
    import pytest
    from pydantic import ValidationError

    from flow.models import Chokepoint

    row = {
        "id": "hormuz",
        "name": "Strait of Hormuz",
        "lat": 26.6,
        "lon": 56.3,
        "transit_volume": 20.9,
        "transit_unit": "mbpd",
        "year": 2025,
        "source": "EIA",
        "source_url": "https://www.eia.gov/",
    }
    Chokepoint.model_validate(row)
    for bad in ({"id": "Hormuz Strait"}, {"source_url": "eia.gov"}, {"volume": 1}):
        with pytest.raises(ValidationError):
            Chokepoint.model_validate(row | bad)


def test_append_events_incremental_and_deduplicated(tmp_path) -> None:
    import sqlite3

    from flow.data.build import append_events

    db = tmp_path / "test_flow.db"
    # Calling append_events on non-existent db builds it first
    events_batch_1 = [
        {
            "event_id": "test-event-1",
            "observed_at": "2026-09-16T10:00:00Z",
            "source_name": "testsource.com",
            "url": "https://testsource.com/1",
            "tone": -2.5,
            "entities": ["hormuz", "SA"],
            "commodities": ["crude_oil"],
        }
    ]
    inserted = append_events(events_batch_1, db)
    assert inserted == 1

    conn = sqlite3.connect(db)

    assert (
        conn.execute("""
        SELECT COUNT(*) FROM events WHERE event_id = 'test-event-1'
            """).fetchone()[0]
        == 1
    )

    assert (
        conn.execute("""
        SELECT COUNT(*) FROM event_entities WHERE event_id = 'test-event-1'
            """).fetchone()[0]
        == 2
    )

    assert (
        conn.execute("""
        SELECT COUNT(*) FROM event_commodities WHERE event_id = 'test-event-1'
            """).fetchone()[0]
        == 1
    )
    # Check static tables still intact
    assert conn.execute("SELECT COUNT(*) FROM commodities").fetchone()[0] == 5

    # Re-inserting the same event skips duplicate
    events_batch_2 = [
        events_batch_1[0],
        {
            "event_id": "test-event-2",
            "observed_at": "2026-09-16T10:15:00Z",
            "source_name": "testsource.com",
            "url": "https://testsource.com/2",
            "tone": 1.0,
            "entities": ["suez"],
            "commodities": ["lng"],
        },
    ]
    inserted_2 = append_events(events_batch_2, db)
    assert inserted_2 == 1  # only test-event-2 was newly added
    assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] >= 2
    conn.close()
