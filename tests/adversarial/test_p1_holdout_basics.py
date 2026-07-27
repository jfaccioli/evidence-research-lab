"""Adversarial holdout scenarios (design §11 #1–3 subset)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest

from crl.db.schema import CURRENT_P1_SCHEMA_VERSION, connect_p1, migrate_database
from crl.research.holdout import (
    CohortMember,
    HoldoutState,
    HoldoutStateMachine,
    HoldoutTransitionError,
    ReservationCapabilityError,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _programme_database(path: Path) -> None:
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
                'pv1', 'pl1', 'rl1', NULL, NULL, 'adv fixture',
                1, ?, '2024-01-01T00:00:00.000000Z'
            )
            """,
            (HASH_A,),
        )
        conn.commit()
    finally:
        conn.close()


def _sealed_holdout(path: Path) -> HoldoutStateMachine:
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
    machine.seal_cohort(cohort_id="cohort1", sealed_at=T0)
    machine.register_holdout(
        holdout_id="holdout1",
        programme_version_id="pv1",
        created_at=T0,
    )
    return machine


def test_concurrent_reservation_one_winner(tmp_path: Path):
    path = tmp_path / "h.sqlite"
    _sealed_holdout(path)

    def attempt(_: int):
        local = HoldoutStateMachine(path)
        try:
            return local.reserve(
                holdout_id="holdout1",
                cohort_id="cohort1",
                reserved_at=T0,
            )
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(8)))
    wins = [r for r in results if not isinstance(r, Exception)]
    assert len(wins) == 1
    machine = HoldoutStateMachine(path)
    assert machine.state("holdout1") is HoldoutState.RESERVED


def test_burned_holdout_cannot_return_to_available(tmp_path: Path):
    path = tmp_path / "h.sqlite"
    machine = _sealed_holdout(path)
    res = machine.reserve(
        holdout_id="holdout1",
        cohort_id="cohort1",
        reserved_at=T0,
    )
    machine.abort_burned(res, reason="adversarial burn", terminal_at=T0)
    assert machine.state("holdout1") is HoldoutState.ABORTED_BURNED
    with pytest.raises(
        (HoldoutTransitionError, ReservationCapabilityError, Exception)
    ):
        machine.reserve(
            holdout_id="holdout1",
            cohort_id="cohort1",
            reserved_at=T0,
        )
