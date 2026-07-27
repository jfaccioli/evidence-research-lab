"""PR3: policy-derived multiplicity and non-COMPLETE completeness."""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from crl.db.schema import (
    CURRENT_P1_SCHEMA_VERSION,
    connect_p1,
    derive_completeness,
    migrate_database,
    never_auto_complete,
)
from crl.research.programme.models import GovernanceCompleteness
from crl.research.ledger import (
    ExecutionState,
    RegistrationError,
    TrialKind,
    TrialLedger,
    TrialRegistrationFacts,
    TrialRegistrationError,
    assess_completeness,
    compute_multiplicity,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _setup(path: Path, *, second_lineage: bool = False) -> TrialLedger:
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
                'pv1', 'pl1', 'rl1', NULL, NULL, 'multiplicity fixture',
                1, ?, '2024-01-01T00:00:00.000000Z'
            )
            """,
            (HASH_A,),
        )
        conn.execute(
            """
            INSERT INTO cohorts(
                cohort_id, programme_version_id, state, protocol_manifest_hash,
                membership_hash, created_at, sealed_at
            ) VALUES (
                'cohort1', 'pv1', 'DRAFT', ?, NULL,
                '2024-01-01T00:00:00.000000Z', NULL
            )
            """,
            (HASH_B,),
        )
        # seal via direct state allowed only by trigger as DRAFT→SEALED with members
        conn.execute(
            """
            INSERT INTO cohort_members(
                cohort_id, ordinal, candidate_id, spec_hash, added_at
            ) VALUES ('cohort1', 0, 'cand', ?, '2024-01-01T00:00:00.000000Z')
            """,
            (HASH_A,),
        )
        conn.execute(
            """
            UPDATE cohorts
            SET state='SEALED', membership_hash=?, sealed_at='2024-01-01T00:00:00.000000Z'
            WHERE cohort_id='cohort1'
            """,
            (HASH_C,),
        )
        if second_lineage:
            conn.execute(
                """
                INSERT INTO research_lineages(
                    research_lineage_id, description, created_at
                ) VALUES ('rl2', 'other', '2024-01-01T00:00:00.000000Z')
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
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=100
    )
    if second_lineage:
        ledger.allocate_budget(
            allocation_id="alloc2", research_lineage_id="rl2", units_allocated=100
        )
    return ledger


def _reg(
    ledger: TrialLedger,
    *,
    trial_id: str,
    kind: TrialKind,
    selection_unit_id: str,
    input_hash: str = HASH_A,
    cohort_id: str | None = None,
    preregistered: bool = True,
    synthetic: bool = False,
    is_citation: bool = False,
    result_exposed: bool = False,
    billable: bool | None = None,
    reproduction_of: str | None = None,
    units_cost: int = 1,
    research_lineage_id: str = "rl1",
    programme_version_id: str = "pv1",
    allocation_id: str = "alloc1",
) -> None:
    if billable is None:
        billable = kind not in (
            TrialKind.SYNTHETIC_FIXTURE,
            TrialKind.BENCHMARK_BH,
            TrialKind.CITATION,
        ) and not synthetic and not is_citation
    facts = TrialRegistrationFacts(
        trial_id=trial_id,
        research_lineage_id=research_lineage_id,
        programme_version_id=programme_version_id,
        trial_kind=kind,
        immutable_input_hash=input_hash,
        selection_unit_id=selection_unit_id,
        cohort_id=cohort_id,
        preregistered=preregistered,
        synthetic=synthetic,
        is_citation=is_citation,
        result_exposed=result_exposed,
        billable=billable,
        units_cost=units_cost if billable else 0,
        reproduction_of_trial_id=reproduction_of,
    )
    ledger.register_trial(
        facts,
        allocation_id=allocation_id if facts.normalized().billable else None,
    )


def test_public_api_has_no_caller_byte_identity_boolean():
    """Finding 1: public registration facts expose no force-exclusion Boolean."""
    fields = {f.name for f in TrialRegistrationFacts.__dataclass_fields__.values()}
    assert "reproduction_byte_identical" not in fields
    assert "reproduction_input_hash" not in fields
    # Only linkage is caller-supplied for reproductions.
    assert "reproduction_of_trial_id" in fields
    sig = inspect.signature(TrialLedger.register_trial)
    assert "reproduction_byte_identical" not in sig.parameters
    assert "reproduction_input_hash" not in sig.parameters
    # No public approve/verify legacy path.
    assert not hasattr(TrialLedger, "approve_legacy_n_bound")
    assert not hasattr(TrialLedger, "verify_legacy_n_bound")
    assert not hasattr(TrialLedger, "approve_legacy_n")
    assert hasattr(TrialLedger, "propose_legacy_n_bound")


def test_sensitivity_neighbour_and_unregistered_violation(tmp_path: Path):
    path = tmp_path / "sens.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t_base",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_base",
    )
    _reg(
        ledger,
        trial_id="t_sens_reg",
        kind=TrialKind.SENSITIVITY_POINT,
        selection_unit_id="su_sens_reg",
        preregistered=True,
    )
    _reg(
        ledger,
        trial_id="t_sens_unreg",
        kind=TrialKind.SENSITIVITY_POINT,
        selection_unit_id="su_sens_unreg",
        preregistered=False,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert "su_base" in census.counting_selection_unit_ids
        assert "su_sens_reg" in census.counting_selection_unit_ids
        assert "su_sens_unreg" in census.counting_selection_unit_ids
        assert any(
            v.code == "unregistered_sensitivity_neighbour"
            for v in census.governance_violations
        )
        assert "open_governance_violations" in census.promotion_block_reasons
        assert "missing_verified_legacy_n_approval" in census.promotion_block_reasons
        assert census.promotion_blocked
        assert census.correlation_discount == 1.0
    finally:
        conn.close()


def test_citation_synthetic_bh_and_byte_identical_reproduction_non_count(
    tmp_path: Path,
):
    path = tmp_path / "exclude.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t_h",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_h",
        input_hash=HASH_A,
    )
    _reg(
        ledger,
        trial_id="t_cit",
        kind=TrialKind.CITATION,
        selection_unit_id="su_h",  # narrative reuse of same unit
        is_citation=True,
        billable=False,
        units_cost=0,
    )
    _reg(
        ledger,
        trial_id="t_syn",
        kind=TrialKind.SYNTHETIC_FIXTURE,
        selection_unit_id="su_syn",
        synthetic=True,
        billable=False,
        units_cost=0,
    )
    _reg(
        ledger,
        trial_id="t_bh",
        kind=TrialKind.BENCHMARK_BH,
        selection_unit_id="su_bh",
        billable=False,
        units_cost=0,
    )
    # Equal stored input hashes → system-derived byte-identical exclusion.
    _reg(
        ledger,
        trial_id="t_repro",
        kind=TrialKind.REPRODUCTION,
        selection_unit_id="su_repro",
        reproduction_of="t_h",
        input_hash=HASH_A,
        billable=False,
        units_cost=0,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert census.counting_selection_unit_ids == ("su_h",)
        assert census.n_global_ledger == 1
        row = conn.execute(
            """
            SELECT reproduction_input_hash, reproduction_byte_identical,
                   selection_capable
            FROM trials WHERE trial_id = 't_repro'
            """
        ).fetchone()
        assert row[0] == HASH_A  # system-derived from referenced trial
        assert int(row[1]) == 1
        assert int(row[2]) == 0
    finally:
        conn.close()


def test_changed_input_reproduction_counts(tmp_path: Path):
    """Different stored input hashes must count as selection-capable."""
    path = tmp_path / "repro_changed.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t_h",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_h",
        input_hash=HASH_A,
    )
    _reg(
        ledger,
        trial_id="t_repro_changed",
        kind=TrialKind.REPRODUCTION,
        selection_unit_id="su_repro_changed",
        reproduction_of="t_h",
        input_hash=HASH_B,  # different from referenced stored hash
        billable=False,
        units_cost=0,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert set(census.counting_selection_unit_ids) == {
            "su_h",
            "su_repro_changed",
        }
        row = conn.execute(
            """
            SELECT reproduction_input_hash, reproduction_byte_identical,
                   selection_capable
            FROM trials WHERE trial_id = 't_repro_changed'
            """
        ).fetchone()
        assert row[0] == HASH_A  # referenced hash, not the new trial hash
        assert int(row[1]) == 0
        assert int(row[2]) == 1
    finally:
        conn.close()


def test_missing_reproduction_reference_fails_atomically(tmp_path: Path):
    path = tmp_path / "repro_missing.sqlite"
    ledger = _setup(path)
    before_events = 0
    conn = connect_p1(path)
    try:
        before_events = conn.execute(
            "SELECT COUNT(*) FROM ledger_events"
        ).fetchone()[0]
        before_trials = conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0]
    finally:
        conn.close()

    with pytest.raises(RegistrationError, match="reproduction reference missing"):
        _reg(
            ledger,
            trial_id="t_repro_miss",
            kind=TrialKind.REPRODUCTION,
            selection_unit_id="su_miss",
            reproduction_of="does_not_exist",
            input_hash=HASH_A,
            billable=False,
            units_cost=0,
        )
    conn = connect_p1(path)
    try:
        assert (
            conn.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0]
            == before_events
        )
        assert (
            conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0] == before_trials
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM trials WHERE trial_id = 't_repro_miss'"
            ).fetchone()[0]
            == 0
        )
    finally:
        conn.close()


def test_cross_lineage_reproduction_reference_fails_atomically(tmp_path: Path):
    path = tmp_path / "repro_xlineage.sqlite"
    ledger = _setup(path, second_lineage=True)
    # Register a trial on rl2
    _reg(
        ledger,
        trial_id="t_other",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_other",
        research_lineage_id="rl2",
        programme_version_id="pv2",
        allocation_id="alloc2",
        input_hash=HASH_A,
    )
    conn = connect_p1(path)
    try:
        before_events = conn.execute(
            "SELECT COUNT(*) FROM ledger_events"
        ).fetchone()[0]
        before_trials = conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0]
    finally:
        conn.close()

    with pytest.raises(RegistrationError, match="another research_lineage_id"):
        _reg(
            ledger,
            trial_id="t_repro_x",
            kind=TrialKind.REPRODUCTION,
            selection_unit_id="su_x",
            reproduction_of="t_other",  # belongs to rl2
            research_lineage_id="rl1",
            programme_version_id="pv1",
            input_hash=HASH_A,
            billable=False,
            units_cost=0,
        )
    conn = connect_p1(path)
    try:
        assert (
            conn.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0]
            == before_events
        )
        assert (
            conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0] == before_trials
        )
    finally:
        conn.close()


def test_caller_cannot_force_byte_identical_via_facts_kwargs(tmp_path: Path):
    """Constructing facts with removed fields must TypeError (no force path)."""
    with pytest.raises(TypeError):
        TrialRegistrationFacts(  # type: ignore[call-arg]
            trial_id="t",
            research_lineage_id="rl1",
            programme_version_id="pv1",
            trial_kind=TrialKind.REPRODUCTION,
            immutable_input_hash=HASH_A,
            selection_unit_id="su",
            reproduction_of_trial_id="t_h",
            reproduction_byte_identical=True,
        )
    with pytest.raises(TypeError):
        TrialRegistrationFacts(  # type: ignore[call-arg]
            trial_id="t",
            research_lineage_id="rl1",
            programme_version_id="pv1",
            trial_kind=TrialKind.REPRODUCTION,
            immutable_input_hash=HASH_A,
            selection_unit_id="su",
            reproduction_of_trial_id="t_h",
            reproduction_input_hash=HASH_A,
        )


def test_changed_input_rerun_counts_and_base_2x_dedup(tmp_path: Path):
    path = tmp_path / "dedup.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t_cand",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_cand",
        input_hash=HASH_A,
    )
    _reg(
        ledger,
        trial_id="t_cost_base",
        kind=TrialKind.COST_STRESS_BASE,
        selection_unit_id="su_cand",
        input_hash=HASH_A,
    )
    _reg(
        ledger,
        trial_id="t_cost_2x",
        kind=TrialKind.COST_STRESS_2X,
        selection_unit_id="su_cand",
        input_hash=HASH_A,
    )
    _reg(
        ledger,
        trial_id="t_rerun",
        kind=TrialKind.CHANGED_INPUT_RERUN,
        selection_unit_id="su_rerun",
        input_hash=HASH_B,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert set(census.counting_selection_unit_ids) == {"su_cand", "su_rerun"}
        assert census.n_global_ledger == 2
    finally:
        conn.close()


def test_incompatible_selection_unit_collision_counts_each_trial_and_blocks(
    tmp_path: Path,
):
    """Caller ID reuse cannot collapse distinct analytical variants."""
    path = tmp_path / "selection_collision.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t_param",
        kind=TrialKind.PARAMETER_VARIANT,
        selection_unit_id="caller_shared",
        input_hash=HASH_A,
    )
    _reg(
        ledger,
        trial_id="t_feature",
        kind=TrialKind.FEATURE_VARIANT,
        selection_unit_id="caller_shared",
        input_hash=HASH_B,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert census.n_global_ledger == 2
        assert set(census.counting_selection_unit_ids) == {
            "trial:t_param",
            "trial:t_feature",
        }
        assert any(
            v.code == "invalid_selection_unit_collision"
            for v in census.governance_violations
        )
        assert "open_governance_violations" in census.promotion_block_reasons
        assert census.promotion_blocked
    finally:
        conn.close()


def test_cost_bundle_requires_same_sealed_input_context(tmp_path: Path):
    """Mismatched cost diagnostics fail closed instead of deduplicating."""
    path = tmp_path / "cost_collision.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t_anchor",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_cost",
        input_hash=HASH_A,
    )
    _reg(
        ledger,
        trial_id="t_cost_base",
        kind=TrialKind.COST_STRESS_BASE,
        selection_unit_id="su_cost",
        input_hash=HASH_A,
    )
    _reg(
        ledger,
        trial_id="t_cost_2x_wrong",
        kind=TrialKind.COST_STRESS_2X,
        selection_unit_id="su_cost",
        input_hash=HASH_B,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert census.n_global_ledger == 3
        assert any(
            v.code == "invalid_selection_unit_collision"
            for v in census.governance_violations
        )
    finally:
        conn.close()


def test_exposed_abort_counts(tmp_path: Path):
    path = tmp_path / "abort.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t_ok",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_ok",
    )
    _reg(
        ledger,
        trial_id="t_abort_exposed",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_ab_exp",
        result_exposed=False,
    )
    ledger.finalize_trial(
        trial_id="t_abort_exposed",
        execution_state=ExecutionState.ABORTED,
        result_exposed=True,
        notes="peek may have occurred",
    )
    _reg(
        ledger,
        trial_id="t_abort_clean",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_ab_clean",
        result_exposed=False,
    )
    ledger.finalize_trial(
        trial_id="t_abort_clean",
        execution_state=ExecutionState.ABORTED,
        result_exposed=False,
        notes="never exposed",
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert "su_ok" in census.counting_selection_unit_ids
        assert "su_ab_exp" in census.counting_selection_unit_ids
        assert "su_ab_clean" not in census.counting_selection_unit_ids
    finally:
        conn.close()


def test_n_global_n_cohort_no_correlation_discount(tmp_path: Path):
    path = tmp_path / "n.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t_g1",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_g1",
    )
    _reg(
        ledger,
        trial_id="t_c1",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su_c1",
        cohort_id="cohort1",
    )
    _reg(
        ledger,
        trial_id="t_c2",
        kind=TrialKind.FEATURE_VARIANT,
        selection_unit_id="su_c2",
        cohort_id="cohort1",
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(
            conn, research_lineage_id="rl1", cohort_id="cohort1"
        )
        assert census.n_global_ledger == 3
        assert census.n_cohort == 2
        assert census.correlation_discount == 1.0
        # No verified legacy approval → authoritative bound absent
        assert census.legacy_bound_n is None
        assert census.proposed_legacy_bound_n is None
        assert "missing_verified_legacy_n_approval" in census.promotion_block_reasons
        assert census.promotion_blocked
        # N_global is ledger-only (proposal not yet present)
        assert census.n_global == census.n_global_ledger

        ledger.propose_legacy_n_bound(
            proposal_id="prop1",
            research_lineage_id="rl1",
            upper_bound_n=40,
            supporting_artefact_hash=HASH_A,
            notes="diagnostic proposal fixture",
        )
        census2 = compute_multiplicity(
            conn, research_lineage_id="rl1", cohort_id="cohort1"
        )
        # Diagnostic only — does NOT enter authoritative N_global
        assert census2.proposed_legacy_bound_n == 40
        assert census2.legacy_bound_n is None
        assert census2.n_global == census2.n_global_ledger
        assert census2.n_global != census2.n_global_ledger + 40
        assert census2.n_cohort == 2
        assert "missing_verified_legacy_n_approval" in (
            census2.promotion_block_reasons
        )
        assert census2.promotion_blocked
    finally:
        conn.close()


def test_proposed_legacy_bound_does_not_unblock_completeness(tmp_path: Path):
    path = tmp_path / "prop_complete.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t1",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su1",
    )
    ledger.propose_legacy_n_bound(
        proposal_id="prop1",
        research_lineage_id="rl1",
        upper_bound_n=10,
        supporting_artefact_hash=HASH_B,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert census.proposed_legacy_bound_n == 10
        assert census.legacy_bound_n is None
        assert census.n_global == census.n_global_ledger

        assessment = assess_completeness(
            conn,
            research_lineage_id="rl1",
            governance_epoch_id=None,
            caller_claims_complete=True,
        )
        assert assessment.completeness is (
            GovernanceCompleteness.INCOMPLETE_UNBOUNDED
        )
        assert assessment.completeness is not GovernanceCompleteness.COMPLETE
        assert assessment.promotion_blocked
        assert "missing_verified_legacy_n_approval" in assessment.gaps
        assert "missing_verified_legacy_n_approval" in (
            assessment.promotion_block_reasons
        )
        assert assessment.proposed_legacy_bound_n == 10
    finally:
        conn.close()


def test_invalid_legacy_proposal_fails_atomically(tmp_path: Path):
    path = tmp_path / "prop_invalid.sqlite"
    ledger = _setup(path)
    conn = connect_p1(path)
    try:
        before = conn.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0]
    finally:
        conn.close()

    with pytest.raises(RegistrationError, match="upper_bound_n"):
        ledger.propose_legacy_n_bound(
            proposal_id="bad1",
            research_lineage_id="rl1",
            upper_bound_n=-1,
            supporting_artefact_hash=HASH_A,
        )
    with pytest.raises(RegistrationError, match="SHA-256"):
        ledger.propose_legacy_n_bound(
            proposal_id="bad2",
            research_lineage_id="rl1",
            upper_bound_n=5,
            supporting_artefact_hash="not-a-hash",
        )
    with pytest.raises(RegistrationError, match="unknown research_lineage_id"):
        ledger.propose_legacy_n_bound(
            proposal_id="bad3",
            research_lineage_id="missing_lineage",
            upper_bound_n=5,
            supporting_artefact_hash=HASH_A,
        )
    conn = connect_p1(path)
    try:
        assert (
            conn.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0] == before
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM legacy_n_bound_proposals"
            ).fetchone()[0]
            == 0
        )
    finally:
        conn.close()


def test_no_public_api_marks_legacy_bound_verified_or_approved():
    public_methods = [
        name
        for name in dir(TrialLedger)
        if not name.startswith("_") and callable(getattr(TrialLedger, name))
    ]
    forbidden_tokens = (
        "approve_legacy",
        "verify_legacy",
        "mint_legacy",
        "legacy_n_bound_approved",
        "mark_legacy_approved",
    )
    for name in public_methods:
        for token in forbidden_tokens:
            assert token not in name, f"forbidden public method {name}"
    # propose is allowed and is the only legacy-bound public path
    assert "propose_legacy_n_bound" in public_methods


def test_legacy_never_complete_and_caller_boolean_ignored(tmp_path: Path):
    path = tmp_path / "complete.sqlite"
    ledger = _setup(path)
    _reg(
        ledger,
        trial_id="t1",
        kind=TrialKind.HYPOTHESIS_EVAL,
        selection_unit_id="su1",
    )
    conn = connect_p1(path)
    try:
        # Null epoch / legacy path
        assert derive_completeness(governance_epoch_id=None) is (
            GovernanceCompleteness.INCOMPLETE_UNBOUNDED
        )
        assert never_auto_complete(None, "COMPLETE") == (
            GovernanceCompleteness.INCOMPLETE_UNBOUNDED.value
        )

        assessment = assess_completeness(
            conn,
            research_lineage_id="rl1",
            governance_epoch_id=None,
            caller_claims_complete=True,
        )
        assert assessment.completeness is not GovernanceCompleteness.COMPLETE
        assert assessment.is_legacy_era
        assert assessment.promotion_blocked
        assert "legacy_era_never_complete" in assessment.gaps
        # PR4 schema may be present; local checkpoints + PR5 anchors still block.
        assert (
            "missing_artifact_bundle_digests_pr4" in assessment.gaps
            or "local_checkpoints_non_authoritative" in assessment.gaps
        )
        assert "missing_verified_legacy_n_approval" in assessment.gaps
        assert "missing_external_anchor_pr5" in assessment.gaps

        # With proposal still not COMPLETE and still unbounded (no verified approval)
        ledger.propose_legacy_n_bound(
            proposal_id="prop1",
            research_lineage_id="rl1",
            upper_bound_n=10,
            supporting_artefact_hash=HASH_B,
        )
        assessment2 = assess_completeness(
            conn,
            research_lineage_id="rl1",
            governance_epoch_id=None,
            caller_claims_complete=True,
        )
        assert assessment2.completeness is (
            GovernanceCompleteness.INCOMPLETE_UNBOUNDED
        )
        assert assessment2.completeness is not GovernanceCompleteness.COMPLETE
        assert assessment2.completeness is not (
            GovernanceCompleteness.LEGACY_RECONSTRUCTED_CONSERVATIVELY
        )
        assert assessment2.promotion_blocked
        assert (
            "pr4_artifact_checkpoint_invariants_missing"
            in assessment2.promotion_block_reasons
            or "pr4_local_checkpoints_non_authoritative"
            in assessment2.promotion_block_reasons
            or "pr5_external_anchor_or_off_machine_backup_missing"
            in assessment2.promotion_block_reasons
        )
        assert "missing_verified_legacy_n_approval" in (
            assessment2.promotion_block_reasons
        )

        # Governed epoch also not COMPLETE at PR4
        assessment3 = assess_completeness(
            conn,
            research_lineage_id="rl1",
            governance_epoch_id="ge1",
            caller_claims_complete=True,
        )
        assert assessment3.completeness is (
            GovernanceCompleteness.INCOMPLETE_KNOWN_GAPS
        )
        assert assessment3.completeness is not GovernanceCompleteness.COMPLETE
    finally:
        conn.close()


def test_reproduction_requires_linkage_only(tmp_path: Path):
    """Reproduction facts require linkage; hash/Boolean are not caller inputs."""
    with pytest.raises(TrialRegistrationError, match="reproduction_of_trial_id"):
        TrialRegistrationFacts(
            trial_id="t",
            research_lineage_id="rl1",
            programme_version_id="pv1",
            trial_kind=TrialKind.REPRODUCTION,
            immutable_input_hash=HASH_A,
            selection_unit_id="su",
        ).normalized()
