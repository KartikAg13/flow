from flow import intel
from flow.data.build import append_events, build, connect


def event(i: int, at: str, tone: float, *entities: str) -> dict:
    return {
        "event_id": f"t{i}",
        "observed_at": at,
        "source_name": "test",
        "url": f"https://test/{i}",
        "tone": tone,
        "entities": list(entities),
        "commodities": [],
    }


def test_recent_negative_news_scores_highest(tmp_path) -> None:
    db = build(tmp_path / "flow.db")
    con = connect(db)
    con.executescript(
        "DELETE FROM event_entities; DELETE FROM event_commodities; DELETE FROM events;"
    )
    append_events(
        [
            event(1, "2026-09-16T12:00:00Z", -6.0, "hormuz"),
            event(2, "2026-09-16T12:00:00Z", -6.0, "hormuz"),
            event(3, "2026-09-16T12:00:00Z", 2.0, "suez"),
            event(4, "2026-09-10T12:00:00Z", -6.0, "malacca"),  # outside the 72 h window
        ],
        db,
    )
    s = intel.store(con)
    assert s["hormuz"] > s["suez"] > 0
    assert s["malacca"] == s["cape"] == 0
    stored = con.execute("SELECT live_risk FROM entity_risk WHERE entity_id = 'hormuz'").fetchone()
    assert stored[0] == s["hormuz"]
    assert intel.history(con)["malacca"][0] > 0  # it was live back on 10 Sep
    con.close()
