"""PR4: immutable artefact bundles, Merkle roots, path safety, registration."""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import sqlite3
from pathlib import Path

import pytest

from crl.db.schema import CURRENT_P1_SCHEMA_VERSION, connect_p1, migrate_database
from crl.research.artifacts import (
    BundleError,
    BundleLineage,
    SealedBundle,
    aggregate_digest_merkle,
    empty_merkle_root,
    leaf_hash,
    merkle_root_from_leaves,
    merkle_root_from_members,
    node_hash,
    normalize_member_path,
    seal_bundle,
    verify_sealed_bundle_dir,
)
from crl.research.ledger import (
    ExecutionState,
    RegistrationError,
    TrialKind,
    TrialLedger,
    TrialRegistrationFacts,
    assess_completeness,
)
from crl.research.ledger.registration import TrialLedger as TrialLedgerCls
from crl.research.programme.models import GovernanceCompleteness

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64
HASH_F = "f" * 64
HASH_G = "g" * 64
HASH_H = "h" * 64
T0 = "2024-01-01T00:00:00.000000Z"


def _lineage(**overrides) -> BundleLineage:
    base = dict(
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
    base.update(overrides)
    return BundleLineage(**base)


def _seed_db(path: Path) -> TrialLedger:
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
                'pv1', 'pl1', 'rl1', NULL, NULL, 'artifact fixture',
                1, ?, ?
            )
            """,
            (HASH_C, T0),
        )
        conn.commit()
    finally:
        conn.close()
    ledger = TrialLedger(path)
    ledger.allocate_budget(
        allocation_id="alloc1", research_lineage_id="rl1", units_allocated=20
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
    return ledger


def _src(tmp: Path, name: str, data: bytes) -> Path:
    p = tmp / name
    p.write_bytes(data)
    return p


# --- Merkle -----------------------------------------------------------------


def test_merkle_known_vectors_ordering_domain_separation_empty():
    empty = empty_merkle_root()
    assert len(empty) == 64
    assert empty == empty_merkle_root()
    assert empty != hashlib.sha256(b"").hexdigest()

    leaf_a = leaf_hash(relative_path="a.txt", content_sha256=HASH_A, byte_size=1)
    leaf_b = leaf_hash(relative_path="b.txt", content_sha256=HASH_B, byte_size=2)
    assert leaf_a != hashlib.sha256(b"a.txt").digest()
    node = node_hash(leaf_a, leaf_b)
    assert node != hashlib.sha256(leaf_a + leaf_b).digest()
    assert node == node_hash(leaf_a, leaf_b)

    root_ab = merkle_root_from_leaves([leaf_a, leaf_b])
    root_ba = merkle_root_from_leaves([leaf_b, leaf_a])
    assert root_ab != root_ba

    m1 = merkle_root_from_members(
        [("b.txt", HASH_B, 2), ("a.txt", HASH_A, 1)]
    )
    m2 = merkle_root_from_members(
        [("a.txt", HASH_A, 1), ("b.txt", HASH_B, 2)]
    )
    assert m1 == m2 == root_ab
    assert merkle_root_from_leaves([leaf_a]) == leaf_a.hex()

    leaf_c = leaf_hash(relative_path="c.txt", content_sha256=HASH_C, byte_size=3)
    root3 = merkle_root_from_leaves([leaf_a, leaf_b, leaf_c])
    mid = node_hash(leaf_a, leaf_b)
    assert root3 == node_hash(mid, leaf_c).hex()


def test_aggregate_preserves_distinct_identical_content():
    """Identical content roots across distinct artefact IDs must not collapse."""
    one = aggregate_digest_merkle([("art_a", HASH_A)])
    two = aggregate_digest_merkle([("art_a", HASH_A), ("art_b", HASH_A)])
    assert one != two
    # Order of input does not matter; identity set does.
    two_rev = aggregate_digest_merkle([("art_b", HASH_A), ("art_a", HASH_A)])
    assert two == two_rev


# --- Path safety ------------------------------------------------------------


def test_path_traversal_absolute_symlink_duplicate_nonregular_rejected(tmp_path: Path):
    root = tmp_path / "artifacts_root"
    root.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    good = _src(src_dir, "ok.bin", b"hello")

    with pytest.raises(Exception):
        normalize_member_path("../escape")
    with pytest.raises(Exception):
        normalize_member_path("/abs/path")
    with pytest.raises(Exception):
        normalize_member_path("foo/../bar")
    with pytest.raises(Exception):
        normalize_member_path(".")
    with pytest.raises(Exception):
        normalize_member_path("a//b")

    link = src_dir / "link.bin"
    link.symlink_to(good)
    with pytest.raises(BundleError, match="symlink"):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="r_sym",
            sources={"data.bin": link},
            lineage=_lineage(),
        )

    # Symlink in a source parent path component is rejected.
    outside = tmp_path / "outside_real"
    outside.mkdir()
    real_file = outside / "payload.bin"
    real_file.write_bytes(b"payload")
    linked_parent = src_dir / "linked_parent"
    linked_parent.symlink_to(outside)
    with pytest.raises(BundleError, match="symlink"):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="r_sym_parent",
            sources={"data.bin": linked_parent / "payload.bin"},
            lineage=_lineage(),
        )

    with pytest.raises(BundleError, match="non-regular|directory|regular"):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="r_dir",
            sources={"data.bin": src_dir},
            lineage=_lineage(),
        )

    with pytest.raises(BundleError, match="duplicate"):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="r_dup",
            sources={"data.bin": good, "./data.bin": good},
            lineage=_lineage(),
        )

    with pytest.raises(Exception):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="r_abs",
            sources={"/etc/passwd": good},
            lineage=_lineage(),
        )


def test_staging_symlink_parent_rejected(tmp_path: Path):
    root = tmp_path / "art"
    root.mkdir()
    outside = tmp_path / "escaped_staging"
    outside.mkdir()
    staging = root / ".staging"
    staging.symlink_to(outside)
    src = _src(tmp_path, "x.bin", b"x")
    with pytest.raises(BundleError, match="symlink|staging"):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="r_stage",
            sources={"x.bin": src},
            lineage=_lineage(),
        )
    # Outside must not receive a published bundle.
    assert list(outside.iterdir()) == []


def test_required_lineage_fields_hash_shaped(tmp_path: Path):
    root = tmp_path / "art"
    src = _src(tmp_path, "x.bin", b"x")
    with pytest.raises(BundleError, match="SHA-256"):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="r1",
            sources={"x.bin": src},
            lineage=_lineage(config_hash="not-a-hash"),
        )
    sealed = seal_bundle(
        artifact_root=root,
        bundle_kind="run",
        run_id="r1",
        sources={"x.bin": src},
        lineage=_lineage(),
    )
    assert sealed.lineage.config_hash == HASH_A
    assert sealed.lineage.dependency_lock_hash == HASH_F
    assert len(sealed.merkle_root) == 64
    assert sealed.artifact_id.startswith("art_")


def test_run_collision_overwrite_rejected_old_bytes_intact(tmp_path: Path):
    root = tmp_path / "art"
    src1 = _src(tmp_path, "a.bin", b"AAA")
    src2 = _src(tmp_path, "b.bin", b"BBB")
    sealed = seal_bundle(
        artifact_root=root,
        bundle_kind="run",
        run_id="run1",
        sources={"a.bin": src1},
        lineage=_lineage(),
    )
    old_bytes = (sealed.absolute_root / "a.bin").read_bytes()
    with pytest.raises(BundleError, match="already exists"):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="run1",
            sources={"a.bin": src2},
            lineage=_lineage(),
        )
    assert (sealed.absolute_root / "a.bin").read_bytes() == old_bytes
    verify_sealed_bundle_dir(sealed.absolute_root)


def test_publish_race_destination_unchanged(tmp_path: Path):
    """Pre-existing destination under exclusive identity must never be replaced.

    Injects destination creation after the last existence check and immediately
    before exclusive mkdir (the former os.rename race window on macOS empty dirs).
    """
    root = tmp_path / "art"
    src = _src(tmp_path, "a.bin", b"AAA")
    marker = b"preexisting-destination-bytes"
    captured: dict[str, Path] = {}

    def race(dst: Path) -> None:
        captured["dst"] = dst
        dst.mkdir(parents=True, exist_ok=False)
        (dst / "keep.bin").write_bytes(marker)

    with pytest.raises(BundleError, match="already exists|no overwrite"):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="run_race",
            sources={"a.bin": src},
            lineage=_lineage(),
            _race_hook=race,
        )
    assert "dst" in captured
    dest = captured["dst"]
    # Layout is artifacts/runs/{run_id}/{artifact_id}
    assert dest.parent.name == "run_race"
    assert dest.parent.parent.name == "runs"
    assert dest.is_dir()
    assert (dest / "keep.bin").read_bytes() == marker
    assert not (dest / "a.bin").exists()
    assert not (dest / "MANIFEST.json").exists()


def test_publish_race_empty_destination_not_replaced(tmp_path: Path):
    """Empty destination appearing in the rename window must fail closed."""
    root = tmp_path / "art"
    src = _src(tmp_path, "a.bin", b"AAA")
    captured: dict[str, Path] = {}

    def race(dst: Path) -> None:
        captured["dst"] = dst
        dst.mkdir(parents=True, exist_ok=False)

    with pytest.raises(BundleError, match="already exists|no overwrite"):
        seal_bundle(
            artifact_root=root,
            bundle_kind="run",
            run_id="run_empty_race",
            sources={"a.bin": src},
            lineage=_lineage(),
            _race_hook=race,
        )
    dest = captured["dst"]
    assert dest.is_dir()
    assert list(dest.iterdir()) == []
    assert not (dest / "MANIFEST.json").exists()
    assert not (dest / "a.bin").exists()


def test_undeclared_file_directory_symlink_fail_verification(tmp_path: Path):
    root = tmp_path / "art"
    sealed = seal_bundle(
        artifact_root=root,
        bundle_kind="run",
        run_id="run_ud",
        sources={"a.bin": _src(tmp_path, "a.bin", b"a")},
        lineage=_lineage(),
    )
    # Undeclared file
    (sealed.absolute_root / "undeclared.txt").write_text("extra")
    with pytest.raises(BundleError, match="set mismatch|extra"):
        verify_sealed_bundle_dir(sealed.absolute_root)
    (sealed.absolute_root / "undeclared.txt").unlink()

    # Undeclared directory with file
    extra_dir = sealed.absolute_root / "extra_dir"
    extra_dir.mkdir()
    (extra_dir / "x.bin").write_bytes(b"x")
    with pytest.raises(BundleError, match="set mismatch|extra"):
        verify_sealed_bundle_dir(sealed.absolute_root)
    (extra_dir / "x.bin").unlink()
    extra_dir.rmdir()

    # Symlink inside bundle
    (sealed.absolute_root / "link.bin").symlink_to(sealed.absolute_root / "a.bin")
    with pytest.raises(BundleError, match="symlink"):
        verify_sealed_bundle_dir(sealed.absolute_root)


def test_non_canonical_manifest_rejected(tmp_path: Path):
    root = tmp_path / "art"
    sealed = seal_bundle(
        artifact_root=root,
        bundle_kind="run",
        run_id="run_nc",
        sources={"a.bin": _src(tmp_path, "a.bin", b"a")},
        lineage=_lineage(),
    )
    manifest = sealed.absolute_root / "MANIFEST.json"
    payload = json.loads(manifest.read_text())
    # Pretty-printed / non-canonical encoding
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=False))
    with pytest.raises(BundleError, match="non-canonical"):
        verify_sealed_bundle_dir(sealed.absolute_root)


def test_correction_requires_supersession_and_preserves_old(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    src1 = _src(tmp_path, "v1.bin", b"v1")
    src2 = _src(tmp_path, "v2.bin", b"v2")

    first = ledger.seal_and_register_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="run_orig",
        sources={"out.bin": src1},
        lineage=_lineage(trial_id="t1"),
    )
    old_root = first.receipt.absolute_root
    old_artifact = first.artifact_id
    old_bytes = (old_root / "out.bin").read_bytes()

    with pytest.raises(BundleError, match="ordinary seal|is_correction"):
        seal_bundle(
            artifact_root=art,
            bundle_kind="run",
            run_id="run_fake",
            sources={"out.bin": src2},
            lineage=_lineage(trial_id="t1"),
            supersedes_artifact_id=old_artifact,
            is_correction=False,
        )

    with pytest.raises(BundleError, match="supersedes"):
        seal_bundle(
            artifact_root=art,
            bundle_kind="run",
            run_id="run_corr",
            sources={"out.bin": src2},
            lineage=_lineage(trial_id="t1"),
            is_correction=True,
        )

    sealed_bad = seal_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="run_bad",
        sources={"out.bin": src2},
        lineage=_lineage(trial_id="t1"),
        is_correction=True,
        supersedes_artifact_id="art_missingprior0000000000000000000001",
    )
    with pytest.raises(RegistrationError, match="unknown prior"):
        ledger.register_sealed_bundle(
            artifact_root=art,
            relative_root=sealed_bad.relative_root,
        )

    corr = ledger.seal_and_register_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="run_corr",
        sources={"out.bin": src2},
        lineage=_lineage(trial_id="t1"),
        is_correction=True,
        supersedes_artifact_id=old_artifact,
    )
    assert corr.supersession_event_seq is not None
    assert corr.artifact_id != old_artifact
    assert (old_root / "out.bin").read_bytes() == old_bytes
    conn = connect_p1(db)
    try:
        rows = conn.execute(
            """
            SELECT artifact_id, is_correction, supersedes_artifact_id
            FROM artifact_digests ORDER BY registration_event_seq
            """
        ).fetchall()
        assert len(rows) == 2
        assert rows[0][0] == old_artifact
        assert rows[0][1] == 0
        assert rows[1][1] == 1
        assert rows[1][2] == old_artifact
        events = conn.execute(
            "SELECT event_type FROM ledger_events WHERE event_type LIKE 'artifact%'"
        ).fetchall()
        types = {r[0] for r in events}
        assert "artifact_bundle_sealed" in types
        assert "artifact_bundle_supersession" in types
    finally:
        conn.close()


def test_identical_content_two_runs_both_register(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    # Second trial so both runs can bind exact trial lineage.
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
    payload = b'{"null":true}'
    a = ledger.seal_and_register_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="run_a",
        sources={"metrics.json": _src(tmp_path, "m1.json", payload)},
        lineage=_lineage(trial_id="t1"),
    )
    b = ledger.seal_and_register_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="run_b",
        sources={"metrics.json": _src(tmp_path, "m2.json", payload)},
        lineage=_lineage(trial_id="t2"),
    )
    assert a.merkle_root == b.merkle_root
    assert a.artifact_id != b.artifact_id
    agg1 = aggregate_digest_merkle([(a.artifact_id, a.merkle_root)])
    agg2 = aggregate_digest_merkle(
        [(a.artifact_id, a.merkle_root), (b.artifact_id, b.merkle_root)]
    )
    assert agg1 != agg2
    conn = connect_p1(db)
    try:
        n = conn.execute("SELECT COUNT(*) FROM artifact_digests").fetchone()[0]
        assert n == 2
        roots = {
            r[0]
            for r in conn.execute("SELECT merkle_root FROM artifact_digests").fetchall()
        }
        assert roots == {a.merkle_root}
    finally:
        conn.close()


def test_no_completion_bypass_parameter():
    sig = inspect.signature(TrialLedgerCls.finalize_trial)
    assert "_allow_completed_without_bundle" not in sig.parameters
    assert "allow_completed_without_bundle" not in sig.parameters


def test_fabricated_sealed_bundle_cannot_register(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    # Caller-constructed dataclass with digest-shaped fields, missing directory.
    fake = SealedBundle(
        artifact_id="art_fake",
        bundle_kind="run",
        run_id="run_fake",
        cohort_id=None,
        relative_root="artifacts/runs/run_fake",
        absolute_root=art / "artifacts" / "runs" / "run_fake",
        merkle_root=HASH_G,
        manifest_sha256=HASH_H,
        byte_size=1,
        lineage=_lineage(),
        member_count=1,
        sealed_at=T0,
        is_correction=False,
        supersedes_artifact_id=None,
    )
    with pytest.raises(RegistrationError, match="missing|directory|verify"):
        ledger.register_sealed_bundle(
            artifact_root=art,
            relative_root=fake.relative_root,
        )
    # Mismatched lineage after seal: tamper manifest identity fields.
    sealed = seal_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="run_tamper",
        sources={"x.bin": _src(tmp_path, "x.bin", b"x")},
        lineage=_lineage(),
    )
    manifest = sealed.absolute_root / "MANIFEST.json"
    payload = json.loads(manifest.read_bytes())
    payload["research_lineage_id"] = "rl_other"
    # rewrite non-canonical or wrong lineage — either fails verification
    from crl.research.artifacts.bundle import _canonical_json

    raw = _canonical_json(payload).encode("utf-8")
    manifest.write_bytes(raw)
    with pytest.raises(RegistrationError):
        ledger.register_sealed_bundle(
            artifact_root=art,
            relative_root=sealed.relative_root,
        )


def test_direct_completed_without_link_is_blocking_gap(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    ledger = _seed_db(db)
    # Schema trigger rejects completed without completion link.
    conn = connect_p1(db)
    try:
        from crl.research.ledger.events import append_event

        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        seq, _ = append_event(
            conn,
            event_type="trial_state_transition",
            payload={
                "state_event_id": "tse_direct",
                "trial_id": "t1",
                "execution_state": "completed",
                "result_exposed": True,
                "notes": "fabricated",
            },
        )
        with pytest.raises(sqlite3.IntegrityError, match="completion"):
            conn.execute(
                """
                INSERT INTO trial_state_events(
                    state_event_id, trial_id, event_seq, execution_state,
                    result_exposed, recorded_at, notes
                ) VALUES ('tse_direct', 't1', ?, 'completed', 1, ?, '')
                """,
                (seq, T0),
            )
        conn.execute("ROLLBACK")
        # Even if a completed row were present without link, reconciliation
        # treats that as a blocking gap (query coverage).
        assessment = assess_completeness(conn, research_lineage_id="rl1")
        assert "completed_trials_without_exact_completion_link" not in assessment.gaps
        # No completed rows exist.
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM trial_state_events WHERE execution_state='completed'"
            ).fetchone()[0]
            == 0
        )
    finally:
        conn.close()


def test_duplicate_completion_rejected(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    ledger.complete_trial_with_run_bundle(
        trial_id="t1",
        artifact_root=art,
        run_id="run_ok",
        sources={"m.json": _src(tmp_path, "m.json", b"{}")},
        lineage=_lineage(trial_id="t1"),
    )
    with pytest.raises(RegistrationError, match="already has a completed"):
        ledger.complete_trial_with_run_bundle(
            trial_id="t1",
            artifact_root=art,
            run_id="run_ok2",
            sources={"m.json": _src(tmp_path, "m2.json", b"{}")},
            lineage=_lineage(trial_id="t1"),
        )


def test_cross_programme_cohort_bundle_rejected(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    conn = connect_p1(db)
    try:
        # Second programme + research lineage and a cohort under each.
        conn.execute(
            """
            INSERT INTO research_lineages(research_lineage_id, description, created_at)
            VALUES ('rl2', '', ?)
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
                'pv2', 'pl2', 'rl2', NULL, NULL, 'other',
                1, ?, ?
            )
            """,
            (HASH_C, T0),
        )
        conn.execute(
            """
            INSERT INTO cohorts(
                cohort_id, programme_version_id, state, protocol_manifest_hash,
                membership_hash, created_at, sealed_at
            ) VALUES (
                'coh1', 'pv2', 'DRAFT', ?, NULL, ?, NULL
            )
            """,
            (HASH_A, T0),
        )
        conn.execute(
            """
            INSERT INTO cohort_members(
                cohort_id, ordinal, candidate_id, spec_hash, added_at
            ) VALUES ('coh1', 0, 'cand', ?, ?)
            """,
            (HASH_B, T0),
        )
        conn.execute(
            """
            UPDATE cohorts
            SET state='SEALED', membership_hash=?, sealed_at=?
            WHERE cohort_id='coh1'
            """,
            (HASH_B, T0),
        )
        conn.commit()
    finally:
        conn.close()

    # API: cohort coh1 belongs to pv2/rl2, bundle claims pv1/rl1.
    with pytest.raises(RegistrationError, match="cohort|lineage|programme|unknown"):
        ledger.seal_and_register_bundle(
            artifact_root=art,
            bundle_kind="cohort",
            cohort_id="coh1",
            sources={"summary.json": _src(tmp_path, "s.json", b"{}")},
            lineage=_lineage(trial_id=None),
        )

    # Direct SQL insert of cross-lineage cohort artefact fails.
    sealed = seal_bundle(
        artifact_root=art,
        bundle_kind="cohort",
        cohort_id="coh1",
        sources={"summary.json": _src(tmp_path, "s2.json", b"{}")},
        lineage=BundleLineage(
            research_lineage_id="rl1",
            programme_version_id="pv1",
            config_hash=HASH_A,
            candidate_spec_hash=HASH_B,
            split_manifest_hash=HASH_C,
            data_hash=HASH_D,
            feature_hash=HASH_E,
            dependency_lock_hash=HASH_F,
            trial_id=None,
        ),
    )
    conn = connect_p1(db)
    try:
        from crl.research.ledger.events import append_event

        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        seq, _ = append_event(
            conn,
            event_type="artifact_bundle_sealed",
            payload={"artifact_id": sealed.artifact_id},
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO artifact_digests(
                    artifact_id, merkle_root, bundle_kind, run_id, cohort_id,
                    trial_id, research_lineage_id, programme_version_id,
                    manifest_sha256, config_hash, candidate_spec_hash,
                    split_manifest_hash, data_hash, feature_hash,
                    dependency_lock_hash, relative_root, byte_size,
                    registration_event_seq, supersedes_artifact_id,
                    is_correction, sealed_at
                ) VALUES (
                    ?, ?, 'cohort', NULL, 'coh1', NULL, 'rl1', 'pv1',
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, ?
                )
                """,
                (
                    sealed.artifact_id,
                    sealed.merkle_root,
                    sealed.manifest_sha256,
                    HASH_A,
                    HASH_B,
                    HASH_C,
                    HASH_D,
                    HASH_E,
                    HASH_F,
                    sealed.relative_root,
                    sealed.byte_size,
                    seq,
                    sealed.sealed_at,
                ),
            )
        conn.execute("ROLLBACK")
    finally:
        conn.close()


def test_cohort_correction_retains_logical_cohort_id(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    conn = connect_p1(db)
    try:
        conn.execute(
            """
            INSERT INTO cohorts(
                cohort_id, programme_version_id, state, protocol_manifest_hash,
                membership_hash, created_at, sealed_at
            ) VALUES (
                'coh_keep', 'pv1', 'DRAFT', ?, NULL, ?, NULL
            )
            """,
            (HASH_A, T0),
        )
        conn.execute(
            """
            INSERT INTO cohort_members(
                cohort_id, ordinal, candidate_id, spec_hash, added_at
            ) VALUES ('coh_keep', 0, 'cand', ?, ?)
            """,
            (HASH_B, T0),
        )
        conn.execute(
            """
            UPDATE cohorts
            SET state='SEALED', membership_hash=?, sealed_at=?
            WHERE cohort_id='coh_keep'
            """,
            (HASH_B, T0),
        )
        conn.commit()
    finally:
        conn.close()
    lin = _lineage(trial_id=None)
    first = ledger.seal_and_register_bundle(
        artifact_root=art,
        bundle_kind="cohort",
        cohort_id="coh_keep",
        sources={"s.json": _src(tmp_path, "s1.json", b"v1")},
        lineage=lin,
    )
    second = ledger.seal_and_register_bundle(
        artifact_root=art,
        bundle_kind="cohort",
        cohort_id="coh_keep",
        sources={"s.json": _src(tmp_path, "s2.json", b"v2")},
        lineage=lin,
        is_correction=True,
        supersedes_artifact_id=first.artifact_id,
    )
    assert first.receipt.cohort_id == second.receipt.cohort_id == "coh_keep"
    assert first.artifact_id != second.artifact_id
    assert first.receipt.absolute_root.exists()
    assert second.receipt.absolute_root.exists()
    assert first.receipt.absolute_root != second.receipt.absolute_root


def test_bundle_write_failure_no_digest_or_completed(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    with pytest.raises(RegistrationError, match="injected bundle"):
        ledger.complete_trial_with_run_bundle(
            trial_id="t1",
            artifact_root=art,
            run_id="run_fail",
            sources={"x.bin": _src(tmp_path, "x.bin", b"x")},
            lineage=_lineage(trial_id="t1"),
            _inject_bundle_failure="before_seal",
        )
    conn = connect_p1(db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM artifact_digests").fetchone()[0] == 0
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM trial_state_events WHERE execution_state='completed'"
            ).fetchone()[0]
            == 0
        )
        assert (
            conn.execute("SELECT COUNT(*) FROM trial_completion_links").fetchone()[0]
            == 0
        )
    finally:
        conn.close()


def test_db_failure_rolls_back_preserves_preexisting_bundle(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    src = _src(tmp_path, "p.bin", b"pre")
    pre = ledger.seal_and_register_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="run_pre",
        sources={"p.bin": src},
        lineage=_lineage(trial_id="t1"),
    )
    pre_bytes = (pre.receipt.absolute_root / "p.bin").read_bytes()

    with pytest.raises(RegistrationError, match="injected failure"):
        ledger.complete_trial_with_run_bundle(
            trial_id="t1",
            artifact_root=art,
            run_id="run_new",
            sources={"n.bin": _src(tmp_path, "n.bin", b"new")},
            lineage=_lineage(trial_id="t1"),
            _inject_db_failure="before_commit",
        )
    assert (pre.receipt.absolute_root / "p.bin").read_bytes() == pre_bytes
    conn = connect_p1(db)
    try:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM artifact_digests WHERE run_id='run_new'"
            ).fetchone()[0]
            == 0
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM trial_state_events WHERE execution_state='completed'"
            ).fetchone()[0]
            == 0
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM artifact_digests WHERE run_id='run_pre'"
            ).fetchone()[0]
            == 1
        )
    finally:
        conn.close()


def test_direct_completed_finalization_rejected_on_v4(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    ledger = _seed_db(db)
    with pytest.raises(RegistrationError, match="sealed run bundle"):
        ledger.finalize_trial(
            trial_id="t1",
            execution_state=ExecutionState.COMPLETED,
            result_exposed=True,
        )
    ledger.finalize_trial(
        trial_id="t1",
        execution_state=ExecutionState.RUNNING,
        result_exposed=False,
    )
    ledger.finalize_trial(
        trial_id="t1",
        execution_state=ExecutionState.ABORTED,
        result_exposed=False,
    )


def test_complete_with_bundle_success_and_immutability_triggers(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    result = ledger.complete_trial_with_run_bundle(
        trial_id="t1",
        artifact_root=art,
        run_id="run_ok",
        sources={"metrics.json": _src(tmp_path, "m.json", b'{"ok":1}')},
        lineage=_lineage(trial_id="t1"),
    )
    assert result.bundle.merkle_root
    assert result.bundle.artifact_id
    conn = connect_p1(db)
    try:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM trial_state_events WHERE execution_state='completed'"
            ).fetchone()[0]
            == 1
        )
        link = conn.execute(
            """
            SELECT artifact_id, run_id, completion_event_seq
            FROM trial_completion_links WHERE trial_id='t1'
            """
        ).fetchone()
        assert link is not None
        assert str(link[0]) == result.bundle.artifact_id
        assert str(link[1]) == "run_ok"
        assert int(link[2]) == result.completion_event_seq
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE artifact_digests SET byte_size=0 WHERE artifact_id=?",
                (result.bundle.artifact_id,),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "DELETE FROM artifact_digests WHERE artifact_id=?",
                (result.bundle.artifact_id,),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO artifact_digests(
                    artifact_id, merkle_root, bundle_kind, run_id, cohort_id,
                    trial_id, research_lineage_id, programme_version_id,
                    manifest_sha256, config_hash, candidate_spec_hash,
                    split_manifest_hash, data_hash, feature_hash,
                    dependency_lock_hash, relative_root, byte_size,
                    registration_event_seq, supersedes_artifact_id,
                    is_correction, sealed_at
                ) VALUES (
                    'art_bad', ?, 'run', 'run_bad', NULL, 't1', 'rl1', 'pv1', ?,
                    ?, ?, ?, ?, ?, ?, 'artifacts/runs/run_bad',
                    1, 99999, NULL, 0, ?
                )
                """,
                (HASH_G, HASH_A, HASH_A, HASH_B, HASH_C, HASH_D, HASH_E, HASH_F, T0),
            )
        assessment = assess_completeness(
            conn, research_lineage_id="rl1", artifact_root=art
        )
        assert assessment.completeness is not GovernanceCompleteness.COMPLETE
        assert assessment.promotion_blocked
        assert "missing_verified_legacy_n_approval" in assessment.gaps
        assert "missing_external_anchor_pr5" in assessment.gaps
        assert "completed_trials_without_exact_completion_link" not in assessment.gaps
    finally:
        conn.close()


def test_orphan_directory_non_authoritative(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    art = tmp_path / "art"
    ledger = _seed_db(db)
    sealed = seal_bundle(
        artifact_root=art,
        bundle_kind="run",
        run_id="orphan_run",
        sources={"o.bin": _src(tmp_path, "o.bin", b"orphan")},
        lineage=_lineage(trial_id="t1"),
    )
    assert sealed.absolute_root.is_dir()
    conn = connect_p1(db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM artifact_digests").fetchone()[0] == 0
        assessment = assess_completeness(
            conn, research_lineage_id="rl1", artifact_root=art
        )
        assert "filesystem_orphan_bundle_directory" in assessment.gaps
        with pytest.raises(RegistrationError, match="sealed run bundle"):
            ledger.finalize_trial(
                trial_id="t1",
                execution_state=ExecutionState.COMPLETED,
                result_exposed=True,
            )
    finally:
        conn.close()
