"""SQLite hypothesis registry with append-only event audit trail."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from crl.shared.types import HypothesisSpec, HypothesisStatus, ResearchMode


SCHEMA = """
CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL,
    taxonomy TEXT,
    family_id TEXT,
    asset TEXT,
    timeframe TEXT,
    spec_json TEXT NOT NULL,
    spec_hash TEXT NOT NULL,
    rationale TEXT,
    saw_test INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (id, version)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    mode TEXT NOT NULL,
    dataset_id TEXT,
    data_sha256 TEXT,
    git_sha TEXT,
    config_hash TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    report_path TEXT,
    FOREIGN KEY (hypothesis_id, version) REFERENCES hypotheses(id, version)
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    split TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    ts TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    reason TEXT,
    payload_json TEXT
);

CREATE TABLE IF NOT EXISTS data_assets (
    dataset_id TEXT PRIMARY KEY,
    source TEXT,
    symbol TEXT,
    interval TEXT,
    sha256 TEXT,
    trust_score REAL,
    path TEXT,
    meta_json TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HypothesisRegistry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def upsert_hypothesis(self, spec: HypothesisSpec, status: HypothesisStatus = HypothesisStatus.DRAFT) -> None:
        """Register hypothesis. Existing non-draft rows are immutable (spec_hash locked).

        Re-runs of the same (id, version) do not rewrite frozen specs or force status
        back to draft — transitions own status changes.
        """
        now = _now()
        payload = spec.model_dump_json()
        import hashlib

        spec_hash = hashlib.sha256(spec.frozen_hash_payload().encode()).hexdigest()[:16]
        with self._conn() as conn:
            row = conn.execute(
                "SELECT status, spec_hash, saw_test FROM hypotheses WHERE id=? AND version=?",
                (spec.id, spec.version),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO hypotheses
                    (id, version, status, taxonomy, family_id, asset, timeframe,
                     spec_json, spec_hash, rationale, saw_test, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?)
                    """,
                    (
                        spec.id,
                        spec.version,
                        status.value,
                        spec.taxonomy.value if hasattr(spec.taxonomy, "value") else str(spec.taxonomy),
                        spec.family_id or spec.id,
                        spec.asset,
                        spec.timeframe,
                        payload,
                        spec_hash,
                        spec.rationale,
                        now,
                        now,
                    ),
                )
                self._event(conn, spec.id, spec.version, None, status.value, "created")
                return

            # Immutable once left pure draft or saw_test consumed
            frozen = row["status"] not in ("draft",) or bool(row["saw_test"])
            if frozen:
                if row["spec_hash"] != spec_hash:
                    raise RuntimeError(
                        f"Hypothesis {spec.id} v{spec.version} is frozen "
                        f"(status={row['status']}); create a new version to change the rule."
                    )
                # no-op: keep status; new runs attach via start_run
                return

            # Still draft and not saw_test: allow content edit while draft
            conn.execute(
                """
                UPDATE hypotheses SET spec_json=?, spec_hash=?, rationale=?,
                taxonomy=?, family_id=?, updated_at=?
                WHERE id=? AND version=?
                """,
                (
                    payload,
                    spec_hash,
                    spec.rationale,
                    spec.taxonomy.value if hasattr(spec.taxonomy, "value") else str(spec.taxonomy),
                    spec.family_id or spec.id,
                    now,
                    spec.id,
                    spec.version,
                ),
            )

    def get_hypothesis(self, hyp_id: str, version: int = 1) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM hypotheses WHERE id=? AND version=?",
                (hyp_id, version),
            ).fetchone()
            return dict(row) if row else None

    def transition(
        self,
        hyp_id: str,
        version: int,
        to_status: HypothesisStatus,
        reason: str = "",
        payload: dict | None = None,
    ) -> None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT status, saw_test, spec_hash FROM hypotheses WHERE id=? AND version=?",
                (hyp_id, version),
            ).fetchone()
            if row is None:
                raise KeyError(f"Unknown hypothesis {hyp_id} v{version}")
            from_status = row["status"]
            conn.execute(
                "UPDATE hypotheses SET status=?, updated_at=? WHERE id=? AND version=?",
                (to_status.value, _now(), hyp_id, version),
            )
            self._event(conn, hyp_id, version, from_status, to_status.value, reason, payload)

    def mark_saw_test(self, hyp_id: str, version: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE hypotheses SET saw_test=1, updated_at=? WHERE id=? AND version=?",
                (_now(), hyp_id, version),
            )
            self._event(conn, hyp_id, version, None, None, "test_unlocked_consumed")

    def assert_confirmatory_allowed(
        self,
        hyp_id: str,
        version: int,
        spec: HypothesisSpec,
        *,
        monthly_budget: int = 10,
    ) -> None:
        row = self.get_hypothesis(hyp_id, version)
        if row is None:
            raise KeyError(hyp_id)
        if row["saw_test"]:
            raise RuntimeError(
                f"Hypothesis {hyp_id} v{version} already consumed confirmatory test; "
                "create a new version for further tests."
            )
        import hashlib

        h = hashlib.sha256(spec.frozen_hash_payload().encode()).hexdigest()[:16]
        if h != row["spec_hash"]:
            raise RuntimeError("Spec hash mismatch — confirmatory requires frozen registered spec")
        n_month = self.count_confirmatory_runs_this_month()
        if n_month >= monthly_budget:
            raise RuntimeError(
                f"Confirmatory research budget exhausted for this month "
                f"({n_month}/{monthly_budget}). Wait or raise budget deliberately in config."
            )

    def count_family(self, family_id: str) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM hypotheses WHERE family_id=?",
                (family_id,),
            ).fetchone()
            return int(row["n"] if row else 0)

    def count_all_hypotheses(self) -> int:
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM hypotheses").fetchone()
            return int(row["n"] if row else 0)

    def count_runs_for_family(self, family_id: str) -> int:
        """Count all pipeline runs for hypotheses in a family (includes reruns)."""
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS n FROM runs r
                JOIN hypotheses h ON h.id = r.hypothesis_id AND h.version = r.version
                WHERE h.family_id = ?
                """,
                (family_id,),
            ).fetchone()
            return int(row["n"] if row else 0)

    def count_all_runs(self) -> int:
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM runs").fetchone()
            return int(row["n"] if row else 0)

    def count_confirmatory_runs_this_month(self) -> int:
        prefix = _now()[:7]  # YYYY-MM
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS n FROM runs
                WHERE mode='confirmatory' AND started_at LIKE ?
                """,
                (f"{prefix}%",),
            ).fetchone()
            return int(row["n"] if row else 0)

    def start_run(
        self,
        hyp_id: str,
        version: int,
        mode: ResearchMode,
        *,
        dataset_id: str = "",
        data_sha256: str = "",
        git_sha: str = "",
        config_hash: str = "",
    ) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO runs
                (hypothesis_id, version, mode, dataset_id, data_sha256, git_sha, config_hash, started_at)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    hyp_id,
                    version,
                    mode.value,
                    dataset_id,
                    data_sha256,
                    git_sha,
                    config_hash,
                    _now(),
                ),
            )
            return int(cur.lastrowid)

    def finish_run(self, run_id: int, report_path: str = "") -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE runs SET finished_at=?, report_path=? WHERE run_id=?",
                (_now(), report_path, run_id),
            )

    def add_metrics(self, run_id: int, split: str, metrics: dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO metrics (run_id, split, metrics_json) VALUES (?,?,?)",
                (run_id, split, json.dumps(metrics, default=str)),
            )

    def register_data_asset(self, manifest: dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_assets
                (dataset_id, source, symbol, interval, sha256, trust_score, path, meta_json)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    manifest.get("dataset_id"),
                    manifest.get("source"),
                    manifest.get("symbol"),
                    manifest.get("interval"),
                    manifest.get("sha256"),
                    manifest.get("trust_score"),
                    manifest.get("path"),
                    json.dumps(manifest, default=str),
                ),
            )

    def list_hypotheses(self, status: str | None = None) -> list[dict[str, Any]]:
        with self._conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM hypotheses WHERE status=? ORDER BY updated_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM hypotheses ORDER BY updated_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def _event(
        self,
        conn: sqlite3.Connection,
        hyp_id: str,
        version: int,
        from_status: str | None,
        to_status: str | None,
        reason: str,
        payload: dict | None = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO events (hypothesis_id, version, ts, from_status, to_status, reason, payload_json)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                hyp_id,
                version,
                _now(),
                from_status,
                to_status,
                reason,
                json.dumps(payload or {}, default=str),
            ),
        )
