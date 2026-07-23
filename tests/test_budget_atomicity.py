"""PR3: atomic trial + budget registration and concurrent overspend protection."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pytest

from crl.db.schema import CURRENT_P1_SCHEMA_VERSION, connect_p1, migrate_database
from crl.research.holdout import (
    CohortMember,
    HoldoutState,
    HoldoutStateMachine,
)
from crl.research.ledger import (
    RegistrationError,
    TrialKind,
    TrialLedger,
    TrialRegistrationFacts,
    allocation_availability,
)
from crl.research.ledger.events import append_event


HASH_A = "a" * 64
HASH_B = "b" * 64
T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _programme_db(path: Path) -> None:
    assert migrate_database(path) == CURRENT_P1_SCHEMA_VERSION
    conn = connect_p1(path)
    try:
        conn.execute(
            """
            INSERT INTO research_lineages(
                research_lineage_id, description, created_at
            ) VALUES ('rl1', '', '2024-01-01T00:00:00.000000Z')
            """
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv1', 'pl1', 'rl1', NULL, NULL, 'budget fixture',
                1, ?, '2024-01-01T00:00:00.000000Z'
            )
            """,
            (HASH_A,),
        )
        conn.commit()
    finally:
        conn.close()


def test_trial_and_debit_rollback_on_injected_failure(tmp_path: Path):
    path = tmp_path / "rollback.sqlite"
    _programme_db(path)
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=5
    )
    with pytest.raises(RegistrationError, match="injected failure after trial"):
        ledger.register_trial(
            TrialRegistrationFacts(
                trial_id="t_fail",
                research_lineage_id="rl1",
                programme_version_id="pv1",
                trial_kind=TrialKind.HYPOTHESIS_EVAL,
                immutable_input_hash=HASH_A,
                selection_unit_id="su_fail",
            ),
            allocation_id="alloc1",
            _inject_failure="after_trial",
        )
    conn = connect_p1(path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM budget_debits").fetchone()[0] == 0
        # allocation event remains; failed trial registration event rolled back
        types = [
            r[0]
            for r in conn.execute(
                "SELECT event_type FROM ledger_events ORDER BY event_seq"
            )
        ]
        assert "trial_registered" not in types
        assert allocation_availability(conn, "alloc1").units_available == 5
    finally:
        conn.close()


def test_insufficient_budget_rolls_back_trial_and_debit(tmp_path: Path):
    path = tmp_path / "insufficient.sqlite"
    _programme_db(path)
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=1
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
    with pytest.raises(RegistrationError, match="insufficient budget"):
        ledger.register_trial(
            TrialRegistrationFacts(
                trial_id="t2",
                research_lineage_id="rl1",
                programme_version_id="pv1",
                trial_kind=TrialKind.HYPOTHESIS_EVAL,
                immutable_input_hash=HASH_B,
                selection_unit_id="su2",
                units_cost=1,
            ),
            allocation_id="alloc1",
        )
    conn = connect_p1(path)
    try:
        trials = [
            r[0]
            for r in conn.execute("SELECT trial_id FROM trials ORDER BY trial_id")
        ]
        assert trials == ["t1"]
        assert conn.execute("SELECT COUNT(*) FROM budget_debits").fetchone()[0] == 1
        assert allocation_availability(conn, "alloc1").units_available == 0
    finally:
        conn.close()


def test_concurrent_budget_registration_cannot_overspend(tmp_path: Path):
    path = tmp_path / "concurrent.sqlite"
    _programme_db(path)
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=3
    )

    def _register(i: int) -> str:
        try:
            ledger.register_trial(
                TrialRegistrationFacts(
                    trial_id=f"tc{i}",
                    research_lineage_id="rl1",
                    programme_version_id="pv1",
                    trial_kind=TrialKind.HYPOTHESIS_EVAL,
                    immutable_input_hash=HASH_A,
                    selection_unit_id=f"su_c{i}",
                    units_cost=1,
                ),
                allocation_id="alloc1",
            )
            return "ok"
        except RegistrationError:
            return "fail"

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_register, i) for i in range(10)]
        results = [f.result() for f in as_completed(futures)]

    assert results.count("ok") == 3
    assert results.count("fail") == 7
    conn = connect_p1(path)
    try:
        n_trials = conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0]
        n_debits = conn.execute("SELECT COUNT(*) FROM budget_debits").fetchone()[0]
        spent = conn.execute(
            "SELECT COALESCE(SUM(units_spent),0) FROM budget_debits"
        ).fetchone()[0]
        assert n_trials == 3
        assert n_debits == 3
        assert spent == 3
        assert allocation_availability(conn, "alloc1").units_available == 0
    finally:
        conn.close()


def test_trial_programme_and_budget_allocation_must_match_research_lineage(
    tmp_path: Path,
):
    path = tmp_path / "cross_lineage.sqlite"
    _programme_db(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            """
            INSERT INTO research_lineages(
                research_lineage_id, description, created_at
            ) VALUES ('rl2', '', '2024-01-01T00:00:00.000000Z')
            """
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv2', 'pl2', 'rl2', NULL, NULL, 'other lineage',
                1, ?, '2024-01-01T00:00:00.000000Z'
            )
            """,
            (HASH_B,),
        )
        conn.commit()
    finally:
        conn.close()

    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=2
    )
    ledger.allocate_budget(
        allocation_id="alloc2", research_lineage_id="rl2", units_allocated=2
    )

    with pytest.raises(RegistrationError, match="programme_version_id belongs"):
        ledger.register_trial(
            TrialRegistrationFacts(
                trial_id="wrong_programme",
                research_lineage_id="rl1",
                programme_version_id="pv2",
                trial_kind=TrialKind.HYPOTHESIS_EVAL,
                immutable_input_hash=HASH_A,
                selection_unit_id="su_wrong_programme",
            ),
            allocation_id="alloc1",
        )

    with pytest.raises(RegistrationError, match="allocation belongs"):
        ledger.register_trial(
            TrialRegistrationFacts(
                trial_id="wrong_allocation",
                research_lineage_id="rl1",
                programme_version_id="pv1",
                trial_kind=TrialKind.HYPOTHESIS_EVAL,
                immutable_input_hash=HASH_A,
                selection_unit_id="su_wrong_allocation",
            ),
            allocation_id="alloc2",
        )

    # Database triggers independently protect ordinary direct-SQL inserts.
    conn = connect_p1(path)
    conn.isolation_level = None
    try:
        conn.execute("BEGIN IMMEDIATE")
        event_seq, _ = append_event(
            conn,
            event_type="trial_registered",
            payload={"probe": "cross_programme"},
            recorded_at=T0,
        )
        with pytest.raises(sqlite3.IntegrityError, match="programme_version_id"):
            conn.execute(
                """
                INSERT INTO trials(
                    trial_id, registration_event_seq, research_lineage_id,
                    programme_version_id, cohort_id, trial_kind,
                    selection_capable, synthetic, immutable_input_hash,
                    result_exposed, preregistered, selection_unit_id,
                    is_citation, reproduction_of_trial_id,
                    reproduction_input_hash, reproduction_byte_identical,
                    billable, units_cost, registered_at
                ) VALUES (
                    'direct_wrong_programme', ?, 'rl1', 'pv2', NULL,
                    'hypothesis_eval', 1, 0, ?, 0, 1, 'su_direct_programme',
                    0, NULL, NULL, NULL, 1, 1,
                    '2024-01-01T00:00:00.000000Z'
                )
                """,
                (event_seq, HASH_A),
            )
        conn.execute("ROLLBACK")

        conn.execute("BEGIN IMMEDIATE")
        event_seq, _ = append_event(
            conn,
            event_type="trial_registered",
            payload={"probe": "cross_allocation"},
            recorded_at=T0,
        )
        conn.execute(
            """
            INSERT INTO trials(
                trial_id, registration_event_seq, research_lineage_id,
                programme_version_id, cohort_id, trial_kind,
                selection_capable, synthetic, immutable_input_hash,
                result_exposed, preregistered, selection_unit_id,
                is_citation, reproduction_of_trial_id,
                reproduction_input_hash, reproduction_byte_identical,
                billable, units_cost, registered_at
            ) VALUES (
                'direct_wrong_allocation', ?, 'rl1', 'pv1', NULL,
                'hypothesis_eval', 1, 0, ?, 0, 1, 'su_direct_allocation',
                0, NULL, NULL, NULL, 1, 1,
                '2024-01-01T00:00:00.000000Z'
            )
            """,
            (event_seq, HASH_A),
        )
        with pytest.raises(sqlite3.IntegrityError, match="allocation/trial"):
            conn.execute(
                """
                INSERT INTO budget_debits(
                    debit_id, allocation_id, trial_id, event_seq,
                    units_spent, debited_at
                ) VALUES (
                    'direct_bad_debit', 'alloc2', 'direct_wrong_allocation',
                    ?, 1, '2024-01-01T00:00:00.000000Z'
                )
                """,
                (event_seq,),
            )
        conn.execute("ROLLBACK")
    finally:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        conn.close()

    conn = connect_p1(path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM budget_debits").fetchone()[0] == 0
        assert [
            row[0]
            for row in conn.execute(
                "SELECT event_type FROM ledger_events ORDER BY event_seq"
            ).fetchall()
        ] == ["budget_allocated", "budget_allocated"]
    finally:
        conn.close()


def test_confirmatory_trial_debit_holdout_atomic_commit_and_rollback(tmp_path: Path):
    path = tmp_path / "conf.sqlite"
    _programme_db(path)
    machine = HoldoutStateMachine(path)
    machine.create_cohort(
        cohort_id="cohort1",
        programme_version_id="pv1",
        protocol_manifest_hash=HASH_B,
        created_at=T0,
    )
    machine.add_cohort_member(
        cohort_id="cohort1",
        member=CohortMember("cand_a", HASH_A),
        added_at=T0,
    )
    machine.seal_cohort(cohort_id="cohort1", sealed_at=T0)
    machine.register_holdout(
        holdout_id="holdout1",
        programme_version_id="pv1",
        created_at=T0,
    )
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=10
    )

    # Injected failure leaves trial/debit absent and holdout AVAILABLE
    with pytest.raises(RegistrationError, match="injected failure after holdout"):
        ledger.register_trial(
            TrialRegistrationFacts(
                trial_id="t_conf_fail",
                research_lineage_id="rl1",
                programme_version_id="pv1",
                cohort_id="cohort1",
                trial_kind=TrialKind.HYPOTHESIS_EVAL,
                immutable_input_hash=HASH_A,
                selection_unit_id="su_conf",
                units_cost=2,
            ),
            allocation_id="alloc1",
            holdout_id="holdout1",
            reserved_at=T0,
            _inject_failure="after_holdout",
        )
    assert machine.state("holdout1") is HoldoutState.AVAILABLE
    conn = connect_p1(path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM budget_debits").fetchone()[0] == 0
    finally:
        conn.close()

    # Successful atomic commit
    result = ledger.register_trial(
        TrialRegistrationFacts(
            trial_id="t_conf_ok",
            research_lineage_id="rl1",
            programme_version_id="pv1",
            cohort_id="cohort1",
            trial_kind=TrialKind.HYPOTHESIS_EVAL,
            immutable_input_hash=HASH_A,
            selection_unit_id="su_conf",
            units_cost=2,
        ),
        allocation_id="alloc1",
        holdout_id="holdout1",
        reserved_at=T0,
    )
    assert result.reservation is not None
    assert result.reservation.holdout_id == "holdout1"
    assert result.reservation.cohort_id == "cohort1"
    assert result.debit_id == "debit_t_conf_ok"
    assert result.units_spent == 2
    assert machine.state("holdout1") is HoldoutState.RESERVED
    conn = connect_p1(path)
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM trials WHERE trial_id='t_conf_ok'"
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT units_spent FROM budget_debits WHERE trial_id='t_conf_ok'"
        ).fetchone()[0] == 2
        # units_spent cannot be edited
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE budget_debits SET units_spent=1 WHERE trial_id='t_conf_ok'"
            )
    finally:
        conn.close()
