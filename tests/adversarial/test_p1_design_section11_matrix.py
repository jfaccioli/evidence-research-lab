"""PR7: design proposal §11 required scenarios (1–18) in one matrix.

Each test is tagged with its scenario number. Implementations use temp DBs only.
"""

from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

import pytest

from crl.db.schema import connect_p1, migrate_database
from crl.db.snapshot import SnapshotError, create_consistent_snapshot
from crl.research.artifacts.bundle import BundleError, BundleLineage, seal_bundle
from crl.research.evidence.filters import EvidenceRow, filter_promotable_evidence
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
from crl.research.ledger import (
    RegistrationError,
    TrialKind,
    TrialLedger,
    TrialRegistrationFacts,
    assess_completeness,
    compute_multiplicity,
)
from crl.research.ledger.events import append_event
from crl.research.ledger.hash_chain import verify_hash_chain
from crl.research.programme.models import GovernanceCompleteness
from crl.research.programme.split_manifest import (
    ManifestValidationError,
    ProgrammeSplitManifest,
    validate_split_manifest,
)
from tests.adversarial.conftest import (
    HASH_A,
    HASH_B,
    HASH_C,
    HASH_D,
    HASH_E,
    HASH_F,
    T0,
    T0_TEXT,
    programme_db,
    reg_trial,
    sealed_holdout_machine,
    trial_ledger,
)


# ---------------------------------------------------------------------------
# §11.1 Concurrent cohort reservation (one wins)
# ---------------------------------------------------------------------------
def test_s01_concurrent_reservation_one_winner(tmp_path: Path):
    path = tmp_path / "s01.sqlite"
    sealed_holdout_machine(path)

    def attempt(_: int):
        local = HoldoutStateMachine(path)
        try:
            return local.reserve(
                holdout_id="holdout1", cohort_id="cohort1", reserved_at=T0
            )
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(8)))
    wins = [r for r in results if not isinstance(r, Exception)]
    assert len(wins) == 1
    assert HoldoutStateMachine(path).state("holdout1") is HoldoutState.RESERVED


# ---------------------------------------------------------------------------
# §11.2 Crash after RESERVED → ABORTED_BURNED; never AVAILABLE
# ---------------------------------------------------------------------------
def test_s02_stale_reserved_recovery_burns_never_available(tmp_path: Path):
    path = tmp_path / "s02.sqlite"
    machine = sealed_holdout_machine(path)
    reservation = machine.reserve(
        holdout_id="holdout1", cohort_id="cohort1", reserved_at=T0
    )
    burned = machine.recover_stale_reservations(
        stale_before=T0 + timedelta(minutes=1),
        recovered_at=T0 + timedelta(minutes=2),
    )
    assert burned == ("holdout1",)
    assert machine.state("holdout1") is HoldoutState.ABORTED_BURNED
    with pytest.raises(ReservationCapabilityError):
        machine.consume(reservation)
    with pytest.raises(HoldoutTransitionError, match="not AVAILABLE"):
        machine.reserve(holdout_id="holdout1", cohort_id="cohort1", reserved_at=T0)


# ---------------------------------------------------------------------------
# §11.3 Attempted reopening of burned holdout
# ---------------------------------------------------------------------------
def test_s03_burned_holdout_cannot_reopen(tmp_path: Path):
    path = tmp_path / "s03.sqlite"
    machine = sealed_holdout_machine(path)
    res = machine.reserve(
        holdout_id="holdout1", cohort_id="cohort1", reserved_at=T0
    )
    machine.abort_burned(
        res, reason="aborted", terminal_at=T0 + timedelta(hours=1)
    )
    assert machine.state("holdout1") is HoldoutState.ABORTED_BURNED
    with pytest.raises(HoldoutTransitionError, match="not AVAILABLE"):
        machine.reserve(holdout_id="holdout1", cohort_id="cohort1", reserved_at=T0)


# ---------------------------------------------------------------------------
# §11.4 Attempted cohort-member append after reservation / seal
# ---------------------------------------------------------------------------
def test_s04_cohort_member_append_after_seal_rejected(tmp_path: Path):
    path = tmp_path / "s04.sqlite"
    machine = sealed_holdout_machine(path)
    machine.reserve(holdout_id="holdout1", cohort_id="cohort1", reserved_at=T0)
    with pytest.raises(CohortStateError, match="sealed"):
        machine.add_cohort_member(
            cohort_id="cohort1",
            member=CohortMember("post_reservation", HASH_D),
            added_at=T0 + timedelta(hours=1),
        )


# ---------------------------------------------------------------------------
# §11.5 Direct test-data access without reservation
# ---------------------------------------------------------------------------
def test_s05_direct_holdout_data_without_reservation_rejected(tmp_path: Path):
    path = tmp_path / "s05.sqlite"
    machine = sealed_holdout_machine(path)
    with pytest.raises(HoldoutAccessError, match="HoldoutDataHandle"):
        load_holdout_data(None, lambda *_: "leaked")  # type: ignore[arg-type]
    with pytest.raises(HoldoutAccessError, match="only be issued"):
        HoldoutDataHandle(machine, object(), object())  # type: ignore[arg-type]
    # After consume, handle is dead
    res = machine.reserve(
        holdout_id="holdout1", cohort_id="cohort1", reserved_at=T0
    )
    handle = machine.issue_data_handle(res)
    machine.consume(res, terminal_at=T0 + timedelta(hours=1))
    with pytest.raises(ReservationCapabilityError):
        load_holdout_data(handle, lambda *_: "too late")


# ---------------------------------------------------------------------------
# §11.6 Programme-version change does not reset N_global with parent/prior
# ---------------------------------------------------------------------------
def test_s06_child_programme_version_does_not_reset_n_global(tmp_path: Path):
    path = tmp_path / "s06.sqlite"
    ledger = trial_ledger(path)
    reg_trial(ledger, trial_id="t_pv1", selection_unit_id="su_pv1")
    conn = connect_p1(path)
    try:
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv2', 'pl1', 'rl1', NULL, 'pv1', 'child with prior results',
                1, ?, ?
            )
            """,
            (HASH_B, T0_TEXT),
        )
        conn.commit()
    finally:
        conn.close()
    reg_trial(
        ledger,
        trial_id="t_pv2",
        selection_unit_id="su_pv2",
        programme_version_id="pv2",
        input_hash=HASH_B,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        # Both selection units under the same research lineage count in N_global
        assert set(census.counting_selection_unit_ids) == {"su_pv1", "su_pv2"}
        assert census.n_global_ledger == 2
        assert census.n_global == 2
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# §11.7 Ledger UPDATE/DELETE rejected
# ---------------------------------------------------------------------------
def test_s07_ledger_update_delete_rejected(tmp_path: Path):
    path = tmp_path / "s07.sqlite"
    programme_db(path)
    conn = connect_p1(path)
    try:
        conn.execute("BEGIN")
        seq, _ = append_event(
            conn, event_type="legacy_n_bound_proposed", payload={"n": 1}
        )
        conn.execute("COMMIT")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE ledger_events SET payload_json='{}' WHERE event_seq=?",
                (seq,),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM ledger_events WHERE event_seq=?", (seq,))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# §11.8 Hash-chain gap / corruption detection
# ---------------------------------------------------------------------------
def test_s08_hash_chain_gap_and_payload_tamper_detected(tmp_path: Path):
    path = tmp_path / "s08.sqlite"
    programme_db(path)
    conn = connect_p1(path)
    try:
        conn.execute("BEGIN")
        append_event(conn, event_type="legacy_n_bound_proposed", payload={"n": 1})
        append_event(conn, event_type="legacy_n_bound_proposed", payload={"n": 2})
        conn.execute("COMMIT")
        assert verify_hash_chain(conn).ok
    finally:
        conn.close()

    # Tamper via raw sqlite without going through connect_p1 triggers:
    # drop no-update trigger is blocked if we use connect_p1. Use sqlite3 +
    # disable triggers by recreating — use UPDATE with PRAGMA is not enough.
    # Corrupt by rewriting event_hash via a connection that drops triggers.
    # Adversarial offline tamper (simulates media corruption / attacker with
    # raw file access). Verify on a plain connection — trusted open would fail
    # closed after trigger removal, which is also correct fail-closed behaviour.
    raw = sqlite3.connect(str(path))
    try:
        raw.execute("PRAGMA foreign_keys=OFF")
        raw.execute("DROP TRIGGER IF EXISTS trg_ledger_events_no_update")
        raw.execute(
            "UPDATE ledger_events SET event_hash=? WHERE event_seq=2",
            ("f" * 64,),
        )
        raw.commit()
        chain = verify_hash_chain(raw)
        assert not chain.ok
        assert any("mismatch" in e or "hash" in e for e in chain.errors)
    finally:
        raw.close()


# ---------------------------------------------------------------------------
# §11.9 Bundle overwrite / run_id collision rejected
# ---------------------------------------------------------------------------
def test_s09_bundle_run_id_collision_rejected(tmp_path: Path):
    art = tmp_path / "art"
    src = tmp_path / "a.bin"
    src.write_bytes(b"AAA")
    lineage = BundleLineage(
        research_lineage_id="rl1",
        programme_version_id="pv1",
        config_hash=HASH_A,
        candidate_spec_hash=HASH_B,
        split_manifest_hash=HASH_C,
        data_hash=HASH_D,
        feature_hash=HASH_E,
        dependency_lock_hash=HASH_F,
        trial_id="t1",
    )
    sealed = seal_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="run1",
        sources={"a.bin": src},
        lineage=lineage,
    )
    old = (sealed.absolute_root / "a.bin").read_bytes()
    with pytest.raises(BundleError, match="already exists|no overwrite"):
        seal_bundle(
            artifact_root=art,
            bundle_kind="run",
            run_id="run1",
            sources={"a.bin": src},
            lineage=lineage,
        )
    assert (sealed.absolute_root / "a.bin").read_bytes() == old


# ---------------------------------------------------------------------------
# §11.10 Synthetic evidence contamination blocked
# ---------------------------------------------------------------------------
def test_s10_synthetic_contamination_blocked_from_promotable_set():
    rows = [
        EvidenceRow(
            trial_id="real",
            trial_kind=TrialKind.HYPOTHESIS_EVAL.value,
            synthetic=False,
            selection_capable=True,
            is_citation=False,
            programme_version_id="pv1",
            research_lineage_id="rl1",
            selection_unit_id="su_real",
        ),
        EvidenceRow(
            trial_id="syn",
            trial_kind=TrialKind.SYNTHETIC_FIXTURE.value,
            synthetic=True,
            selection_capable=True,
            is_citation=False,
            programme_version_id="pv1",
            research_lineage_id="rl1",
            selection_unit_id="su_syn",
            dataset_id="mock_BTCUSDT",
        ),
    ]
    out = filter_promotable_evidence(rows)
    assert [r.trial_id for r in out] == ["real"]
    conn_path_ids = filter_promotable_evidence(
        [
            EvidenceRow(
                trial_id="mock_src",
                trial_kind=TrialKind.HYPOTHESIS_EVAL.value,
                synthetic=False,
                selection_capable=True,
                is_citation=False,
                programme_version_id="pv1",
                research_lineage_id="rl1",
                selection_unit_id="su_m",
                source_class="mock",
            )
        ]
    )
    assert conn_path_ids == ()


# ---------------------------------------------------------------------------
# §11.11 Budget/ledger atomic rollback
# ---------------------------------------------------------------------------
def test_s11_budget_ledger_atomic_rollback(tmp_path: Path):
    path = tmp_path / "s11.sqlite"
    ledger = trial_ledger(path)
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
        types = [
            r[0]
            for r in conn.execute(
                "SELECT event_type FROM ledger_events ORDER BY event_seq"
            )
        ]
        assert "trial_registered" not in types
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# §11.12 UNANCHORED / no backup cannot promote
# ---------------------------------------------------------------------------
def test_s12_unanchored_without_backup_cannot_promote(tmp_path: Path):
    path = tmp_path / "s12.sqlite"
    programme_db(path)
    conn = connect_p1(path)
    try:
        conn.execute("BEGIN")
        append_event(conn, event_type="legacy_n_bound_proposed", payload={"n": 1})
        conn.execute("COMMIT")
        a = assess_completeness(conn, research_lineage_id="rl1")
        assert a.promotion_blocked is True
        assert a.completeness is not GovernanceCompleteness.COMPLETE
        assert "missing_external_anchor_pr5" in a.gaps
        assert "missing_verified_off_machine_backup_pr5" in a.gaps
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# §11.13 Prospective split warm-up / eligible_decision_start correctness
# ---------------------------------------------------------------------------
def test_s13_split_manifest_eligible_decision_and_warm_up_rules():
    from datetime import datetime, timezone

    from pydantic import ValidationError

    from crl.research.programme.models import (
        CandleSemantics,
        FeatureWarmUp,
        ProgrammeBoundaries,
    )
    from crl.research.programme.split_manifest import (
        ProgrammeSplitManifest,
        TimingSemantics,
        validate_split_manifest,
    )

    def _dt(s: str) -> datetime:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    def _kwargs(**overrides):
        base = dict(
            programme_version_id="btc_usdt_spot_daily_fixture_pv0",
            programme_lineage_id="btc_usdt_spot_daily_fixture",
            research_lineage_id="crl_btc_research_v0",
            governance_epoch_id=None,
            parent_programme_version_id=None,
            version_reason="adv s13",
            prior_results_available_at_creation=True,
            dataset_id="synthetic_BTCUSDT_1d_fixture_aaa",
            dataset_vintage_freeze_time=_dt("2020-01-01T00:00:00Z"),
            interval="1d",
            timezone="UTC",
            raw_data_start=_dt("2018-01-01T00:00:00Z"),
            raw_data_end=_dt("2020-01-01T00:00:00Z"),
            feature_warm_up=FeatureWarmUp(
                min_bars=50,
                eligible_decision_start=_dt("2018-03-01T00:00:00Z"),
            ),
            candle_semantics=CandleSemantics(
                open_time_field="open_time_utc",
                close_time_field="close_time_utc",
                incomplete_open_candle="drop",
            ),
            signal_availability_rule=(
                "features use only data with close_time <= decision_time"
            ),
            decision_timestamp="bar close_time (signal time)",
            execution_timestamp="next bar open_time (fill model)",
            timing=TimingSemantics(
                signal_available_at=_dt("2018-06-01T00:00:00Z"),
                decision_at=_dt("2018-06-01T00:00:00Z"),
                execution_at=_dt("2018-06-02T00:00:00Z"),
            ),
            boundaries=ProgrammeBoundaries(
                train_start=_dt("2018-03-01T00:00:00Z"),
                train_end=_dt("2018-12-31T00:00:00Z"),
                val_end=_dt("2019-06-30T00:00:00Z"),
                holdout_start=_dt("2019-07-01T00:00:00Z"),
                holdout_end=_dt("2020-01-01T00:00:00Z"),
            ),
        )
        base.update(overrides)
        return base

    m = ProgrammeSplitManifest(**_kwargs())
    validate_split_manifest(m)
    with pytest.raises(ValidationError, match="eligible_decision_start"):
        ProgrammeSplitManifest(
            **_kwargs(
                feature_warm_up=FeatureWarmUp(
                    min_bars=10,
                    eligible_decision_start=_dt("2017-01-01T00:00:00Z"),
                )
            )
        )


# ---------------------------------------------------------------------------
# §11.14 Unregistered sensitivity neighbour counts and blocks promotion
# ---------------------------------------------------------------------------
def test_s14_unregistered_sensitivity_neighbour_blocks(tmp_path: Path):
    path = tmp_path / "s14.sqlite"
    ledger = trial_ledger(path)
    reg_trial(ledger, trial_id="t_base", selection_unit_id="su_base")
    reg_trial(
        ledger,
        trial_id="t_sens_reg",
        selection_unit_id="su_sens_reg",
        kind=TrialKind.SENSITIVITY_POINT,
        preregistered=True,
        input_hash=HASH_B,
    )
    reg_trial(
        ledger,
        trial_id="t_sens_unreg",
        selection_unit_id="su_sens_unreg",
        kind=TrialKind.SENSITIVITY_POINT,
        preregistered=False,
        input_hash=HASH_C,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert "su_sens_unreg" in census.counting_selection_unit_ids
        assert any(
            v.code == "unregistered_sensitivity_neighbour"
            for v in census.governance_violations
        )
        assert census.promotion_blocked
        assert "open_governance_violations" in census.promotion_block_reasons
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# §11.15 Citation reuse does not double-count trials
# ---------------------------------------------------------------------------
def test_s15_citation_does_not_double_count(tmp_path: Path):
    path = tmp_path / "s15.sqlite"
    ledger = trial_ledger(path)
    reg_trial(ledger, trial_id="t_h", selection_unit_id="su_h", input_hash=HASH_A)
    reg_trial(
        ledger,
        trial_id="t_cit",
        selection_unit_id="su_h",
        kind=TrialKind.CITATION,
        is_citation=True,
        billable=False,
        units_cost=0,
        input_hash=HASH_A,
    )
    conn = connect_p1(path)
    try:
        census = compute_multiplicity(conn, research_lineage_id="rl1")
        assert census.counting_selection_unit_ids == ("su_h",)
        assert census.n_global_ledger == 1
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# §11.16 Legacy cannot be COMPLETE; blocked without approved legacy bound
# ---------------------------------------------------------------------------
def test_s16_legacy_never_complete_without_approved_bound(tmp_path: Path):
    path = tmp_path / "s16.sqlite"
    programme_db(path)
    conn = connect_p1(path)
    try:
        conn.execute("BEGIN")
        append_event(conn, event_type="legacy_n_bound_proposed", payload={"n": 99})
        conn.execute("COMMIT")
        a = assess_completeness(conn, research_lineage_id="rl1")  # no epoch → legacy
        assert a.is_legacy_era is True
        assert a.completeness is not GovernanceCompleteness.COMPLETE
        assert a.promotion_blocked is True
        assert "missing_verified_legacy_n_approval" in a.gaps or any(
            "legacy" in g for g in a.gaps
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# §11.17 Checkpoint DB hash rejects live-file hash path (backup API only)
# ---------------------------------------------------------------------------
def test_s17_snapshot_uses_backup_api_not_naive_live_file_copy(tmp_path: Path):
    path = tmp_path / "s17.sqlite"
    ledger = trial_ledger(path)
    reg_trial(ledger, trial_id="t1", selection_unit_id="su1")
    dest = tmp_path / "snap.sqlite"
    meta = create_consistent_snapshot(
        path, dest, expected_contents={"trials": {"trial_id": "t1"}}
    )
    assert meta.method == "sqlite_backup"
    # Naive live-file hash is not what create_consistent_snapshot claims as method
    live_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    # Snapshot may coincidentally match size but method must be backup API
    assert meta.method != "live_file_copy"
    assert meta.method != "naive_copy"
    assert dest.is_file()
    # Overwrite destination refused
    with pytest.raises(SnapshotError, match="already exists"):
        create_consistent_snapshot(path, dest)
    _ = live_hash  # not used as authority


# ---------------------------------------------------------------------------
# §11.18 Accrual isolation: sealed cohort mutation rejected; loader error burns
# ---------------------------------------------------------------------------
def test_s18_sealed_cohort_mutation_rejected_and_loader_error_burns(tmp_path: Path):
    path = tmp_path / "s18.sqlite"
    machine = sealed_holdout_machine(path)
    # Mutation of sealed membership rejected
    with pytest.raises(CohortStateError, match="sealed"):
        machine.add_cohort_member(
            cohort_id="cohort1",
            member=CohortMember("exploratory_leak", HASH_D),
            added_at=T0 + timedelta(days=1),
        )
    # Early/broken evaluation path burns holdout (no silent recovery to AVAILABLE)
    res = machine.reserve(
        holdout_id="holdout1", cohort_id="cohort1", reserved_at=T0
    )
    handle = machine.issue_data_handle(res)

    def broken_loader(*_args):
        raise RuntimeError("partial exploratory peek failed")

    with pytest.raises(RuntimeError, match="partial exploratory"):
        load_holdout_data(handle, broken_loader)
    assert machine.state("holdout1") is HoldoutState.ABORTED_BURNED
    with pytest.raises(HoldoutTransitionError, match="not AVAILABLE"):
        machine.reserve(holdout_id="holdout1", cohort_id="cohort1", reserved_at=T0)


def test_section11_matrix_has_eighteen_scenario_tests():
    """Meta-check: this module defines s01–s18 scenario entry points."""
    import tests.adversarial.test_p1_design_section11_matrix as m

    names = [n for n in dir(m) if n.startswith("test_s") and n[6:8].isdigit()]
    nums = sorted({n[6:8] for n in names})
    assert nums == [f"{i:02d}" for i in range(1, 19)]
