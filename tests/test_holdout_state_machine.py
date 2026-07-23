"""PR2 cohort and irreversible programme-holdout behavior."""

from __future__ import annotations

import inspect
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from crl.db.schema import (
    CURRENT_P1_SCHEMA_VERSION,
    SchemaError,
    connect_p1,
    get_schema_version,
    migrate_database,
)
from crl.research.holdout import (
    CohortMember,
    CohortStateError,
    HoldoutAccessError,
    HoldoutDataHandle,
    HoldoutState,
    HoldoutStateMachine,
    HoldoutTransitionError,
    ReservationCapabilityError,
    load_holdout_data,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _programme_database(path: Path, *, programme_version_id: str = "pv1") -> None:
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
                ?, 'pl1', 'rl1', NULL, NULL, 'PR2 fixture',
                1, ?, '2024-01-01T00:00:00.000000Z'
            )
            """,
            (programme_version_id, HASH_A),
        )
        conn.commit()
    finally:
        conn.close()


def _sealed_setup(path: Path) -> tuple[HoldoutStateMachine, str]:
    _programme_database(path)
    machine = HoldoutStateMachine(path)
    machine.create_cohort(
        cohort_id="cohort1",
        programme_version_id="pv1",
        protocol_manifest_hash=HASH_B,
        created_at=T0,
    )
    machine.add_cohort_member(
        cohort_id="cohort1",
        member=CohortMember("candidate_a", HASH_A),
        added_at=T0,
    )
    machine.add_cohort_member(
        cohort_id="cohort1",
        member=CohortMember("candidate_b", HASH_B),
        added_at=T0,
    )
    digest = machine.seal_cohort(cohort_id="cohort1", sealed_at=T0)
    machine.register_holdout(
        holdout_id="holdout1",
        programme_version_id="pv1",
        created_at=T0,
    )
    return machine, digest


def test_v2_schema_is_explicit_and_v1_can_upgrade(tmp_path: Path):
    path = tmp_path / "upgrade.sqlite"
    assert migrate_database(path, target_version=1) == 1
    conn = connect_p1(path)
    try:
        assert get_schema_version(conn) == 1
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "holdouts" not in tables
    finally:
        conn.close()

    assert migrate_database(path) == 2
    conn = connect_p1(path)
    try:
        assert get_schema_version(conn) == 2
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"cohorts", "cohort_members", "holdouts"} <= tables
    finally:
        conn.close()


def test_v2_partial_migration_rolls_back_to_valid_v1(tmp_path: Path):
    path = tmp_path / "rollback_v2.sqlite"
    migrate_database(path, target_version=1)
    with pytest.raises(Exception, match="injected failure after"):
        migrate_database(path, _inject_failure_after_statements=2)

    conn = connect_p1(path)
    try:
        assert get_schema_version(conn) == 1
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "cohorts" not in tables
        assert "holdouts" not in tables
    finally:
        conn.close()


def test_cohort_membership_seals_deterministically_and_cannot_append(tmp_path: Path):
    machine, digest = _sealed_setup(tmp_path / "cohort.sqlite")
    assert len(digest) == 64
    assert [m.candidate_id for m in machine.cohort_members("cohort1")] == [
        "candidate_a",
        "candidate_b",
    ]
    with pytest.raises(CohortStateError, match="sealed"):
        machine.add_cohort_member(
            cohort_id="cohort1",
            member=CohortMember("candidate_c", "c" * 64),
        )
    with pytest.raises(CohortStateError, match="not DRAFT"):
        machine.seal_cohort(cohort_id="cohort1")


def test_reservation_requires_sealed_same_programme_cohort(tmp_path: Path):
    path = tmp_path / "preconditions.sqlite"
    _programme_database(path)
    machine = HoldoutStateMachine(path)
    machine.create_cohort(
        cohort_id="draft",
        programme_version_id="pv1",
        protocol_manifest_hash=HASH_B,
    )
    machine.add_cohort_member(
        cohort_id="draft",
        member=CohortMember("candidate", HASH_A),
    )
    machine.register_holdout(holdout_id="h1", programme_version_id="pv1")
    with pytest.raises(CohortStateError, match="SEALED"):
        machine.reserve(holdout_id="h1", cohort_id="draft")
    assert machine.state("h1") is HoldoutState.AVAILABLE


def test_database_boundary_rejects_empty_seal_and_draft_reservation(tmp_path: Path):
    path = tmp_path / "db_preconditions.sqlite"
    _programme_database(path)
    machine = HoldoutStateMachine(path)
    machine.create_cohort(
        cohort_id="empty",
        programme_version_id="pv1",
        protocol_manifest_hash=HASH_B,
        created_at=T0,
    )
    machine.register_holdout(
        holdout_id="h1",
        programme_version_id="pv1",
        created_at=T0,
    )
    conn = connect_p1(path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="DRAFT to SEALED"):
            conn.execute(
                """
                UPDATE cohorts
                SET state='SEALED', membership_hash=?, sealed_at=?
                WHERE cohort_id='empty'
                """,
                (HASH_A, "2024-01-01T00:01:00.000000Z"),
            )
        conn.rollback()

        with pytest.raises(sqlite3.IntegrityError, match="invalid or reversible"):
            conn.execute(
                """
                UPDATE holdouts
                SET state='RESERVED',
                    reserved_cohort_id='empty',
                    reservation_token_hash=?,
                    reserved_at=?
                WHERE holdout_id='h1'
                """,
                (HASH_B, "2024-01-01T00:01:00.000000Z"),
            )
        conn.rollback()
    finally:
        conn.close()


def test_concurrent_reservation_has_exactly_one_winner(tmp_path: Path):
    path = tmp_path / "concurrent.sqlite"
    machine, _ = _sealed_setup(path)

    def reserve_once():
        local = HoldoutStateMachine(path)
        try:
            return local.reserve(
                holdout_id="holdout1",
                cohort_id="cohort1",
                reserved_at=T0,
            )
        except HoldoutTransitionError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _i: reserve_once(), range(2)))

    winners = [result for result in results if not isinstance(result, Exception)]
    failures = [result for result in results if isinstance(result, Exception)]
    assert len(winners) == 1
    assert len(failures) == 1
    assert machine.state("holdout1") is HoldoutState.RESERVED


def test_consumed_and_burned_holdouts_cannot_reopen(tmp_path: Path):
    consumed_path = tmp_path / "consumed.sqlite"
    consumed, _ = _sealed_setup(consumed_path)
    reservation = consumed.reserve(
        holdout_id="holdout1",
        cohort_id="cohort1",
        reserved_at=T0,
    )
    with pytest.raises(CohortStateError, match="sealed"):
        consumed.add_cohort_member(
            cohort_id="cohort1",
            member=CohortMember("post_reservation", "d" * 64),
        )
    consumed.consume(reservation, terminal_at=T0 + timedelta(hours=1))
    assert consumed.state("holdout1") is HoldoutState.CONSUMED
    with pytest.raises(HoldoutTransitionError, match="not AVAILABLE"):
        consumed.reserve(holdout_id="holdout1", cohort_id="cohort1")
    with pytest.raises(ReservationCapabilityError):
        consumed.abort_burned(reservation, reason="late retry")

    burned_path = tmp_path / "burned.sqlite"
    burned, _ = _sealed_setup(burned_path)
    burned_reservation = burned.reserve(
        holdout_id="holdout1",
        cohort_id="cohort1",
        reserved_at=T0,
    )
    burned.abort_burned(
        burned_reservation,
        reason="evaluation aborted",
        terminal_at=T0 + timedelta(hours=1),
    )
    assert burned.state("holdout1") is HoldoutState.ABORTED_BURNED
    with pytest.raises(HoldoutTransitionError, match="not AVAILABLE"):
        burned.reserve(holdout_id="holdout1", cohort_id="cohort1")


def test_one_programme_version_has_one_holdout_opening_identity(tmp_path: Path):
    path = tmp_path / "one_opening.sqlite"
    machine, _ = _sealed_setup(path)
    with pytest.raises(sqlite3.IntegrityError):
        machine.register_holdout(
            holdout_id="second_holdout",
            programme_version_id="pv1",
        )


def test_stale_reserved_recovery_burns_and_never_restores_available(tmp_path: Path):
    path = tmp_path / "stale.sqlite"
    machine, _ = _sealed_setup(path)
    reservation = machine.reserve(
        holdout_id="holdout1",
        cohort_id="cohort1",
        reserved_at=T0,
    )
    assert machine.recover_stale_reservations(
        stale_before=T0 + timedelta(minutes=1),
        recovered_at=T0 + timedelta(minutes=2),
    ) == ("holdout1",)
    assert machine.state("holdout1") is HoldoutState.ABORTED_BURNED
    with pytest.raises(ReservationCapabilityError):
        machine.consume(reservation)
    assert machine.recover_stale_reservations(
        stale_before=T0 + timedelta(days=1),
        recovered_at=T0 + timedelta(days=1),
    ) == ()


def test_transition_timestamps_are_monotonic(tmp_path: Path):
    path = tmp_path / "time.sqlite"
    machine, _ = _sealed_setup(path)
    with pytest.raises(HoldoutTransitionError, match="precede holdout creation"):
        machine.reserve(
            holdout_id="holdout1",
            cohort_id="cohort1",
            reserved_at=T0 - timedelta(seconds=1),
        )
    reservation = machine.reserve(
        holdout_id="holdout1",
        cohort_id="cohort1",
        reserved_at=T0,
    )
    with pytest.raises(HoldoutTransitionError, match="precede reservation"):
        machine.consume(
            reservation,
            terminal_at=T0 - timedelta(seconds=1),
        )
    assert machine.state("holdout1") is HoldoutState.RESERVED
    with pytest.raises(HoldoutTransitionError, match="stale cutoff"):
        machine.recover_stale_reservations(
            stale_before=T0 + timedelta(minutes=2),
            recovered_at=T0 + timedelta(minutes=1),
        )
    machine.abort_burned(
        reservation,
        reason="test cleanup",
        terminal_at=T0 + timedelta(minutes=3),
    )


def test_holdout_data_requires_active_capability(tmp_path: Path):
    path = tmp_path / "handle.sqlite"
    machine, _ = _sealed_setup(path)
    with pytest.raises(HoldoutAccessError, match="HoldoutDataHandle"):
        load_holdout_data(None, lambda *_: "leaked")  # type: ignore[arg-type]
    with pytest.raises(HoldoutAccessError, match="only be issued"):
        HoldoutDataHandle(machine, object(), object())  # type: ignore[arg-type]

    reservation = machine.reserve(
        holdout_id="holdout1",
        cohort_id="cohort1",
        reserved_at=T0,
    )
    handle = machine.issue_data_handle(reservation)
    observed = load_holdout_data(
        handle,
        lambda holdout_id, programme_id: (holdout_id, programme_id),
    )
    assert observed == ("holdout1", "pv1")
    machine.consume(reservation)
    with pytest.raises(ReservationCapabilityError, match="active"):
        load_holdout_data(handle, lambda *_: "too late")


def test_loader_error_burns_holdout(tmp_path: Path):
    path = tmp_path / "loader_error.sqlite"
    machine, _ = _sealed_setup(path)
    reservation = machine.reserve(
        holdout_id="holdout1",
        cohort_id="cohort1",
        reserved_at=T0,
    )
    handle = machine.issue_data_handle(reservation)

    def broken_loader(*_args):
        raise RuntimeError("partial read failed")

    with pytest.raises(RuntimeError, match="partial read"):
        load_holdout_data(handle, broken_loader)
    assert machine.state("holdout1") is HoldoutState.ABORTED_BURNED


def test_database_triggers_reject_inserted_terminal_and_reverse_transition(
    tmp_path: Path,
):
    path = tmp_path / "trigger.sqlite"
    machine, _ = _sealed_setup(path)
    conn = connect_p1(path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="inserted as AVAILABLE"):
            conn.execute(
                """
                INSERT INTO holdouts(
                    holdout_id, programme_version_id, state,
                    reserved_cohort_id, reservation_token_hash,
                    created_at, reserved_at, terminal_at, terminal_reason
                ) VALUES (
                    'forged', 'pv1', 'ABORTED_BURNED',
                    'cohort1', ?, '2024-01-01T00:00:00.000000Z',
                    '2024-01-01T00:00:00.000000Z',
                    '2024-01-01T00:00:01.000000Z', 'forged'
                )
                """,
                ("f" * 64,),
            )
        conn.rollback()
    finally:
        conn.close()

    reservation = machine.reserve(
        holdout_id="holdout1",
        cohort_id="cohort1",
        reserved_at=T0,
    )
    conn = connect_p1(path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="invalid or reversible"):
            conn.execute(
                """
                UPDATE holdouts
                SET state='AVAILABLE',
                    reserved_cohort_id=NULL,
                    reservation_token_hash=NULL,
                    reserved_at=NULL
                WHERE holdout_id='holdout1'
                """
            )
        conn.rollback()
    finally:
        conn.close()
    assert machine.state("holdout1") is HoldoutState.RESERVED
    machine.abort_burned(reservation, reason="test cleanup")


def test_damaged_v2_trigger_fails_trusted_open(tmp_path: Path):
    path = tmp_path / "damaged.sqlite"
    _programme_database(path)
    conn = sqlite3.connect(path)
    try:
        conn.execute("DROP TRIGGER trg_holdouts_irreversible_transition")
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="verification|trigger"):
        connect_p1(path)


def test_no_per_hypothesis_fresh_lease_api():
    reserve_params = set(inspect.signature(HoldoutStateMachine.reserve).parameters)
    assert "hypothesis_id" not in reserve_params
    assert "candidate_id" not in reserve_params
    assert reserve_params == {"self", "holdout_id", "cohort_id", "reserved_at"}
