"""PR4: consistent SQLite snapshot via backup API."""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from pathlib import Path

import pytest

from crl.db.schema import CURRENT_P1_SCHEMA_VERSION, connect_p1, migrate_database
from crl.db.snapshot import SnapshotError, create_consistent_snapshot
from crl.research.ledger import TrialKind, TrialLedger, TrialRegistrationFacts

HASH_A = "a" * 64
T0 = "2024-01-01T00:00:00.000000Z"


def _seed(path: Path) -> TrialLedger:
    assert migrate_database(path) == CURRENT_P1_SCHEMA_VERSION
    conn = connect_p1(path)
    try:
        conn.execute(
            """
            INSERT INTO research_lineages(research_lineage_id, description, created_at)
            VALUES ('rl1', '', ?)
            """,
            (T0,),
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv1', 'pl1', 'rl1', NULL, NULL, 'snap fixture',
                1, ?, ?
            )
            """,
            (HASH_A, T0),
        )
        conn.commit()
    finally:
        conn.close()
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=50
    )
    return ledger


def test_snapshot_consistent_reopenable_expected_contents(tmp_path: Path):
    db = tmp_path / "live.sqlite"
    ledger = _seed(db)
    ledger.register_trial(
        TrialRegistrationFacts(
            trial_id="t1",
            research_lineage_id="rl1",
            programme_version_id="pv1",
            trial_kind=TrialKind.HYPOTHESIS_EVAL,
            immutable_input_hash=HASH_A,
            selection_unit_id="su1",
        ),
        allocation_id="alloc1",
    )
    dest = tmp_path / "snap.sqlite"
    meta = create_consistent_snapshot(
        db,
        dest,
        expected_contents={"trials": {"trial_id": "t1"}},
    )
    assert meta.method == "sqlite_backup"
    assert len(meta.sha256) == 64
    assert meta.byte_size > 0
    assert meta.ledger_tip_seq >= 1
    assert dest.is_file()

    snap = connect_p1(dest)
    try:
        row = snap.execute(
            "SELECT trial_id FROM trials WHERE trial_id='t1'"
        ).fetchone()
        assert row is not None
        tip = snap.execute(
            "SELECT event_seq, event_hash FROM ledger_events ORDER BY event_seq DESC LIMIT 1"
        ).fetchone()
        assert int(tip[0]) == meta.ledger_tip_seq
        assert str(tip[1]) == meta.ledger_tip_hash
    finally:
        snap.close()

    with pytest.raises(SnapshotError, match="already exists"):
        create_consistent_snapshot(db, dest)


def test_snapshot_publish_race_destination_unchanged(tmp_path: Path):
    db = tmp_path / "live.sqlite"
    _seed(db)
    dest = tmp_path / "race.sqlite"
    marker = b"preexisting-snapshot-bytes-must-remain"

    def race(path: Path) -> None:
        path.write_bytes(marker)

    with pytest.raises(SnapshotError, match="already exists"):
        create_consistent_snapshot(db, dest, _race_hook=race)
    assert dest.read_bytes() == marker


def test_snapshot_rejects_unsafe_sql_identifiers(tmp_path: Path):
    db = tmp_path / "live.sqlite"
    _seed(db)
    dest = tmp_path / "bad.sqlite"
    with pytest.raises(SnapshotError, match="unsafe SQL identifier"):
        create_consistent_snapshot(
            db,
            dest,
            expected_contents={"trials; DROP TABLE trials;--": {"trial_id": "t1"}},
        )


def test_snapshot_under_wal_concurrent_writer(tmp_path: Path):
    db = tmp_path / "wal.sqlite"
    ledger = _seed(db)
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()

    stop = threading.Event()
    errors: list[BaseException] = []

    def writer():
        try:
            local = TrialLedger(db)
            i = 0
            while not stop.is_set() and i < 40:
                local.register_trial(
                    TrialRegistrationFacts(
                        trial_id=f"tw_{i}",
                        research_lineage_id="rl1",
                        programme_version_id="pv1",
                        trial_kind=TrialKind.HYPOTHESIS_EVAL,
                        immutable_input_hash=HASH_A,
                        selection_unit_id=f"su_w_{i}",
                    ),
                    allocation_id="alloc1",
                )
                i += 1
                time.sleep(0.01)
        except BaseException as exc:
            errors.append(exc)

    t = threading.Thread(target=writer)
    t.start()
    time.sleep(0.05)
    dest = tmp_path / "wal_snap.sqlite"
    meta = create_consistent_snapshot(db, dest)
    stop.set()
    t.join(timeout=10)
    assert not errors, errors

    snap = connect_p1(dest)
    try:
        integrity = snap.execute("PRAGMA integrity_check").fetchone()[0]
        assert integrity == "ok"
        tip = snap.execute(
            "SELECT event_seq FROM ledger_events ORDER BY event_seq DESC LIMIT 1"
        ).fetchone()
        assert tip is not None
        assert int(tip[0]) == meta.ledger_tip_seq
        seqs = [
            int(r[0])
            for r in snap.execute(
                "SELECT event_seq FROM ledger_events ORDER BY event_seq"
            )
        ]
        assert seqs == list(range(1, len(seqs) + 1))
    finally:
        snap.close()

    live_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    assert len(meta.sha256) == 64
    assert isinstance(live_hash, str)
