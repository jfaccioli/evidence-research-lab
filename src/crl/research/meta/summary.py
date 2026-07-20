"""Meta-analysis of the hypothesis registry — research about research.

Not market alpha. Answers: which taxonomies survive gates more often?
Thin Phase-1 surface; meaningful once N is large (dozens–hundreds).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def taxonomy_survival_table(registry_path: str | Path) -> list[dict[str, Any]]:
    """Return per-taxonomy counts and survival rates from SQLite registry.

    Survival = status in (passed_val, candidate) / total rows for taxonomy.
    """
    path = Path(registry_path)
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT taxonomy,
                   COUNT(*) AS n_ideas,
                   SUM(CASE WHEN status IN ('passed_val', 'candidate') THEN 1 ELSE 0 END) AS n_survived,
                   SUM(CASE WHEN status LIKE 'failed%' OR status = 'rejected' THEN 1 ELSE 0 END) AS n_failed
            FROM hypotheses
            GROUP BY taxonomy
            ORDER BY n_ideas DESC
            """
        ).fetchall()
    finally:
        conn.close()

    out = []
    for r in rows:
        n = int(r["n_ideas"] or 0)
        survived = int(r["n_survived"] or 0)
        out.append(
            {
                "taxonomy": r["taxonomy"] or "unknown",
                "n_ideas": n,
                "n_survived": survived,
                "n_failed": int(r["n_failed"] or 0),
                "survival_rate": (survived / n) if n else 0.0,
            }
        )
    return out
