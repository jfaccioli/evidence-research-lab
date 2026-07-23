"""PR3: append-only ledger hash chain integrity."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from crl.db.schema import CURRENT_P1_SCHEMA_VERSION, connect_p1, migrate_database
from crl.research.ledger import (
    GENESIS_PREV_EVENT_HASH,
    TrialKind,
    TrialLedger,
    TrialRegistrationFacts,
    assert_hash_chain_intact,
    compute_event_hash,
    verify_hash_chain,
)


HASH_A = "a" * 64
T0 = "2024-01-01T00:00:00.000000Z"


def _seed_lineage(path: Path) -> None:
    assert migrate_database(path) == CURRENT_P1_SCHEMA_VERSION
    conn = connect_p1(path)
    try:
        conn.execute(
            """
            INSERT INTO research_lineages(
                research_lineage_id, description, created_at
            ) VALUES ('rl1', '', ?)
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
                'pv1', 'pl1', 'rl1', NULL, NULL, 'ledger fixture',
                1, ?, ?
            )
            """,
            (HASH_A, T0),
        )
        conn.commit()
    finally:
        conn.close()


def test_hash_chain_recomputes_contiguous_and_uses_genesis(tmp_path: Path):
    path = tmp_path / "chain.sqlite"
    _seed_lineage(path)
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1",
        research_lineage_id="rl1",
        units_allocated=10,
    )
    ledger.register_trial(
        TrialRegistrationFacts(
            trial_id="t1",
            research_lineage_id="rl1",
            programme_version_id="pv1",
            trial_kind=TrialKind.HYPOTHESIS_EVAL,
            immutable_input_hash=HASH_A,
            selection_unit_id="su1",
            units_cost=1,
        ),
        allocation_id="alloc1",
    )
    conn = connect_p1(path)
    try:
        rows = conn.execute(
            """
            SELECT event_seq, event_type, payload_json, prev_event_hash, event_hash
            FROM ledger_events ORDER BY event_seq
            """
        ).fetchall()
        assert len(rows) >= 2
        assert rows[0]["event_seq"] == 1
        assert rows[0]["prev_event_hash"] == GENESIS_PREV_EVENT_HASH
        for i, row in enumerate(rows):
            assert row["event_seq"] == i + 1
            recomputed = compute_event_hash(
                event_seq=row["event_seq"],
                event_type=row["event_type"],
                payload_json=row["payload_json"],
                prev_event_hash=row["prev_event_hash"],
            )
            assert recomputed == row["event_hash"]
            if i > 0:
                assert row["prev_event_hash"] == rows[i - 1]["event_hash"]
        result = assert_hash_chain_intact(conn)
        assert result.ok
        assert result.event_count == len(rows)
    finally:
        conn.close()


def test_hash_chain_detects_payload_hash_and_gap_damage(tmp_path: Path):
    path = tmp_path / "damage.sqlite"
    _seed_lineage(path)
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1",
        research_lineage_id="rl1",
        units_allocated=5,
    )
    # Drop immutability triggers only in this adversarial harness to inject damage.
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("DROP TRIGGER trg_ledger_events_no_update")
        conn.execute(
            "UPDATE ledger_events SET payload_json = '{\"tampered\":true}' WHERE event_seq = 1"
        )
        conn.commit()
        damaged = verify_hash_chain(conn)
        assert not damaged.ok
        assert any("event_hash mismatch" in e for e in damaged.errors)
    finally:
        conn.close()

    # Hash damage
    path2 = tmp_path / "hash_damage.sqlite"
    _seed_lineage(path2)
    TrialLedger(path2).allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=3
    )
    raw = sqlite3.connect(str(path2))
    try:
        raw.execute("DROP TRIGGER trg_ledger_events_no_update")
        raw.execute(
            "UPDATE ledger_events SET event_hash = ? WHERE event_seq = 1",
            ("f" * 64,),
        )
        raw.commit()
        damaged = verify_hash_chain(raw)
        assert not damaged.ok
        assert any(
            "event_hash mismatch" in e or "prev_event_hash mismatch" in e
            for e in damaged.errors
        )
    finally:
        raw.close()

    # Gap damage: non-contiguous sequence after dropping contiguity guards
    path3 = tmp_path / "gap.sqlite"
    _seed_lineage(path3)
    TrialLedger(path3).allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=3
    )
    raw = sqlite3.connect(str(path3))
    try:
        raw.execute("DROP TRIGGER IF EXISTS trg_ledger_events_no_delete")
        raw.execute("DROP TRIGGER IF EXISTS trg_ledger_events_no_update")
        raw.execute("DROP TRIGGER IF EXISTS trg_ledger_events_contiguous_insert")
        raw.execute("DROP TRIGGER IF EXISTS trg_budget_allocations_no_delete")
        raw.execute("DELETE FROM budget_allocations")
        raw.execute("DELETE FROM ledger_events")
        raw.execute(
            """
            INSERT INTO ledger_events(
                event_seq, event_type, payload_json, prev_event_hash, event_hash, recorded_at
            ) VALUES (2, 'budget_allocated', '{}', ?, ?, ?)
            """,
            (GENESIS_PREV_EVENT_HASH, "b" * 64, T0),
        )
        raw.commit()
        damaged = verify_hash_chain(raw)
        assert not damaged.ok
        assert any("gap" in e or "mismatch" in e for e in damaged.errors)
    finally:
        raw.close()


def test_update_delete_on_ledger_facts_fails(tmp_path: Path):
    path = tmp_path / "immutable.sqlite"
    _seed_lineage(path)
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1",
        research_lineage_id="rl1",
        units_allocated=10,
    )
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
    conn = connect_p1(path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="append-only|UPDATE forbidden|immutable"):
            conn.execute(
                "UPDATE ledger_events SET payload_json='x' WHERE event_seq=1"
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only|DELETE forbidden"):
            conn.execute("DELETE FROM ledger_events WHERE event_seq=1")
        with pytest.raises(sqlite3.IntegrityError, match="append-only|UPDATE forbidden"):
            conn.execute("UPDATE trials SET synthetic=1 WHERE trial_id='t1'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only|DELETE forbidden"):
            conn.execute("DELETE FROM trials WHERE trial_id='t1'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only|UPDATE forbidden"):
            conn.execute(
                "UPDATE budget_debits SET units_spent=99 WHERE trial_id='t1'"
            )
        with pytest.raises(sqlite3.IntegrityError, match="immutable|UPDATE forbidden"):
            conn.execute(
                "UPDATE budget_allocations SET units_allocated=1 WHERE allocation_id='alloc1'"
            )
    finally:
        conn.close()
