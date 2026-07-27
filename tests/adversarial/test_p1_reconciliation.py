"""Adversarial reconciliation + promotion blocks (design §11 #10,12,16)."""

from __future__ import annotations

from pathlib import Path

from crl.db.schema import connect_p1, migrate_database
from crl.research.evidence.filters import (
    EvidenceRow,
    filter_promotable_evidence,
)
from crl.research.ledger.completeness import assess_completeness
from crl.research.ledger.events import append_event
from crl.research.ledger.trials import TrialKind
from crl.research.programme.models import GovernanceCompleteness

T0 = "2020-01-01T00:00:00.000000Z"


def test_synthetic_contamination_blocked_from_promotable_set():
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
        ),
    ]
    out = filter_promotable_evidence(rows)
    assert [r.trial_id for r in out] == ["real"]


def test_unanchored_and_legacy_cannot_promote(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    migrate_database(db)
    conn = connect_p1(db)
    try:
        conn.execute("BEGIN")
        conn.execute(
            """
            INSERT INTO research_lineages(research_lineage_id, created_at, description)
            VALUES ('rl1', ?, 't')
            """,
            (T0,),
        )
        append_event(conn, event_type="legacy_n_bound_proposed", payload={"n": 1})
        conn.execute("COMMIT")
        # Legacy era (no governance_epoch_id)
        a = assess_completeness(conn, research_lineage_id="rl1")
        assert a.promotion_blocked is True
        assert a.completeness is not GovernanceCompleteness.COMPLETE
        assert "missing_external_anchor_pr5" in a.gaps or any(
            "anchor" in g for g in a.gaps
        )
        assert "missing_verified_legacy_n_approval" in a.gaps or any(
            "legacy" in g for g in a.gaps
        )
    finally:
        conn.close()


def test_bundle_overwrite_rejected(tmp_path: Path):
    from crl.research.artifacts.bundle import BundleError, BundleLineage, seal_bundle

    art = tmp_path / "art"
    src = tmp_path / "a.bin"
    src.write_bytes(b"AAA")
    lineage = BundleLineage(
        research_lineage_id="rl1",
        programme_version_id="pv1",
        config_hash="a" * 64,
        candidate_spec_hash="b" * 64,
        split_manifest_hash="c" * 64,
        data_hash="d" * 64,
        feature_hash="e" * 64,
        dependency_lock_hash="f" * 64,
        trial_id="t1",
    )
    seal_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="run1",
        sources={"a.bin": src},
        lineage=lineage,
    )
    try:
        seal_bundle(
            artifact_root=art,
            bundle_kind="run",
            run_id="run1",
            sources={"a.bin": src},
            lineage=lineage,
        )
        raise AssertionError("second seal should fail")
    except BundleError as exc:
        assert "already exists" in str(exc).lower() or "no overwrite" in str(exc).lower()
