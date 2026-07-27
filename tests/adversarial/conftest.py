"""Shared fixtures for P1 design §11 adversarial suite."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from crl.db.schema import CURRENT_P1_SCHEMA_VERSION, connect_p1, migrate_database
from crl.research.holdout import CohortMember, HoldoutStateMachine
from crl.research.ledger import TrialKind, TrialLedger, TrialRegistrationFacts

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64
HASH_F = "f" * 64
T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
T0_TEXT = "2024-01-01T00:00:00.000000Z"


def programme_db(path: Path, *, with_cohort: bool = False) -> None:
    assert migrate_database(path) == CURRENT_P1_SCHEMA_VERSION
    conn = connect_p1(path)
    try:
        conn.execute(
            """
            INSERT INTO research_lineages(
                research_lineage_id, description, created_at
            ) VALUES ('rl1', '', ?)
            """,
            (T0_TEXT,),
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
                1, ?, ?
            )
            """,
            (HASH_A, T0_TEXT),
        )
        if with_cohort:
            conn.execute(
                """
                INSERT INTO cohorts(
                    cohort_id, programme_version_id, state, protocol_manifest_hash,
                    membership_hash, created_at, sealed_at
                ) VALUES (
                    'cohort1', 'pv1', 'DRAFT', ?, NULL, ?, NULL
                )
                """,
                (HASH_B, T0_TEXT),
            )
            conn.execute(
                """
                INSERT INTO cohort_members(
                    cohort_id, ordinal, candidate_id, spec_hash, added_at
                ) VALUES ('cohort1', 0, 'cand', ?, ?)
                """,
                (HASH_A, T0_TEXT),
            )
            conn.execute(
                """
                UPDATE cohorts
                SET state='SEALED', membership_hash=?, sealed_at=?
                WHERE cohort_id='cohort1'
                """,
                (HASH_C, T0_TEXT),
            )
        conn.commit()
    finally:
        conn.close()


def sealed_holdout_machine(path: Path) -> HoldoutStateMachine:
    programme_db(path)
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


def trial_ledger(path: Path) -> TrialLedger:
    programme_db(path)
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=50
    )
    return ledger


def reg_trial(
    ledger: TrialLedger,
    *,
    trial_id: str,
    selection_unit_id: str,
    kind: TrialKind = TrialKind.HYPOTHESIS_EVAL,
    input_hash: str = HASH_A,
    synthetic: bool = False,
    is_citation: bool = False,
    preregistered: bool = True,
    programme_version_id: str = "pv1",
    units_cost: int = 1,
    billable: bool = True,
    reproduction_of: str | None = None,
) -> None:
    ledger.register_trial(
        TrialRegistrationFacts(
            trial_id=trial_id,
            research_lineage_id="rl1",
            programme_version_id=programme_version_id,
            trial_kind=kind,
            immutable_input_hash=input_hash,
            selection_unit_id=selection_unit_id,
            synthetic=synthetic,
            is_citation=is_citation,
            preregistered=preregistered,
            units_cost=units_cost,
            billable=billable,
            reproduction_of_trial_id=reproduction_of,
        ),
        allocation_id="alloc1",
    )
