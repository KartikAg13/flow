"""Live chokepoint risk (0-100) from GDELT events in flow.db.

Each article that names a chokepoint adds weight, negative tone adds more, and weight halves every
HALF_LIFE_H hours. The sum is divided by the number of 15-minute slices in the window (so pulling
more slices does not inflate the score) and squashed into 0-100.
"""

from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timedelta

HALF_LIFE_H = 24
WINDOW_H = 72
# Calibration knob: weighted mentions per slice that read as 63/100. Tuned on the Sep 2026 slices,
# where chokepoints drew 2-14 per slice.
K = 5.0


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def scores(con: sqlite3.Connection, as_of: str | None = None) -> dict[str, int]:
    """Risk per chokepoint id, using events observed in the WINDOW_H hours up to as_of."""
    return {k: round(100 * (1 - math.exp(-r / K))) for k, r in _rates(con, as_of).items()}


def _rates(con: sqlite3.Connection, as_of: str | None) -> dict[str, float]:
    ids = [r[0] for r in con.execute("SELECT id FROM chokepoints ORDER BY id")]
    as_of = as_of or con.execute("SELECT max(observed_at) FROM events").fetchone()[0]
    if as_of is None:
        return dict.fromkeys(ids, 0.0)
    end = _parse(as_of)
    start = (end - timedelta(hours=WINDOW_H)).strftime("%Y-%m-%dT%H:%M:%SZ")
    window = (start, as_of)
    slices = con.execute(
        "SELECT count(DISTINCT observed_at) FROM events WHERE observed_at > ? AND observed_at <= ?",
        window,
    ).fetchone()[0]
    weight = dict.fromkeys(ids, 0.0)
    rows = con.execute(
        """SELECT ee.entity_id, e.observed_at, e.tone FROM events e
           JOIN event_entities ee USING (event_id)
           WHERE e.observed_at > ? AND e.observed_at <= ?""",
        window,
    )
    for entity, at, tone in rows:
        if entity in weight:
            age_h = (end - _parse(at)).total_seconds() / 3600
            weight[entity] += 0.5 ** (age_h / HALF_LIFE_H) * (1 + max(0.0, -(tone or 0.0)) / 5)
    return {k: w / max(slices, 1) for k, w in weight.items()}


def history(con: sqlite3.Connection, points: int = 12) -> dict[str, list[int]]:
    """Scores at each of the last `points` ingest slices, oldest first (for sparklines)."""
    stamps = [
        r[0]
        for r in con.execute(
            "SELECT DISTINCT observed_at FROM events ORDER BY observed_at DESC LIMIT ?", (points,)
        )
    ][::-1]
    series = [scores(con, t) for t in stamps]
    ids = [r[0] for r in con.execute("SELECT id FROM chokepoints ORDER BY id")]
    return {k: [s[k] for s in series] for k in ids}


def store(con: sqlite3.Connection) -> dict[str, int]:
    """Recompute scores and replace the entity_risk table."""
    as_of = con.execute("SELECT max(observed_at) FROM events").fetchone()[0] or ""
    result = scores(con)
    con.execute("DELETE FROM entity_risk")
    con.executemany(
        "INSERT INTO entity_risk VALUES (?,?,?)", [(k, v, as_of) for k, v in result.items()]
    )
    con.commit()
    return result
