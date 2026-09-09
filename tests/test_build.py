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
    conn.close()
