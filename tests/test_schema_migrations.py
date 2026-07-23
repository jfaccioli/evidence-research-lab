"""PR1: explicit schema versioning on temporary databases only.

Uses the actual ``HypothesisRegistry`` and its live ``SCHEMA`` for the
registry-isolation integration test (via live_src_for_overlay_tests when the
Desktop tree is unavailable). Synthetic legacy DBs for RO-compat are additive.
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from crl.db.schema import (
    CURRENT_P1_SCHEMA_VERSION,
    SCHEMA_COMPONENT_P1,
    MalformedSchemaMetaError,
    SchemaError,
    SchemaMigrationError,
    UnsupportedSchemaVersionError,
    connect_p1,
    derive_completeness,
    get_schema_version,
    legacy_epoch_status_for_null,
    migrate_database,
    never_auto_complete,
    open_legacy_compatibility,
    read_schema_version_from_path,
    verify_p1_v1_schema,
)
from crl.research.hypotheses.registry import (
    SCHEMA as LEGACY_SCHEMA,
    HypothesisRegistry,
)
from crl.research.programme.models import (
    GovernanceCompleteness,
    GovernanceEpoch,
    ProgrammeVersion,
    ResearchLineage,
)

VALID_HASH_A = "a" * 64
VALID_HASH_B = "b" * 64


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_legacy_db(path: Path) -> None:
    """Legacy DB using the **actual** HypothesisRegistry SCHEMA."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(LEGACY_SCHEMA)
        conn.execute(
            """
            INSERT INTO hypotheses
            (id, version, status, taxonomy, family_id, asset, timeframe,
             spec_json, spec_hash, rationale, saw_test, created_at, updated_at)
            VALUES ('legacy_h', 1, 'rejected', 'trend', 'legacy_h', 'BTC/USDT', '1d',
                    '{}', 'deadbeef', 'legacy', 0, '2020-01-01T00:00:00Z',
                    '2020-01-01T00:00:00Z')
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_import_does_not_migrate(tmp_path: Path):
    db = tmp_path / "untouched.sqlite"
    assert not db.exists()
    import crl.db  # noqa: F401
    import crl.db.schema  # noqa: F401
    import crl.db.migrations  # noqa: F401

    assert not db.exists()
    assert list(tmp_path.iterdir()) == []


def test_hypothesis_registry_does_not_run_p1_migration(tmp_path: Path):
    """Integration: actual HypothesisRegistry construction must not create P1 schema."""
    reg_path = tmp_path / "reg.sqlite"
    HypothesisRegistry(reg_path)
    conn = sqlite3.connect(str(reg_path))
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "hypotheses" in tables
        assert "runs" in tables
        assert "metrics" in tables
        assert "events" in tables
        assert "data_assets" in tables
        # Actual live SCHEMA must be what was applied
        assert "CREATE TABLE IF NOT EXISTS hypotheses" in LEGACY_SCHEMA
        assert "crl_schema_meta" not in tables
        assert "governance_epochs" not in tables
        assert "programme_versions" not in tables
        assert "programme_split_manifests" not in tables
        assert "research_lineages" not in tables
    finally:
        conn.close()


def test_legacy_compat_open_does_not_change_bytes(tmp_path: Path):
    path = tmp_path / "legacy.sqlite"
    _make_legacy_db(path)
    before = _file_sha256(path)
    size_before = path.stat().st_size
    mtime_before = path.stat().st_mtime_ns

    conn = open_legacy_compatibility(path)
    try:
        assert get_schema_version(conn) is None
        row = conn.execute("SELECT id FROM hypotheses").fetchone()
        assert row["id"] == "legacy_h"
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("CREATE TABLE should_fail (x INTEGER)")
    finally:
        conn.close()

    after = _file_sha256(path)
    assert after == before
    assert path.stat().st_size == size_before
    assert path.stat().st_mtime_ns == mtime_before
    assert read_schema_version_from_path(path) is None


def test_compat_open_rejects_unsupported_newer_version(tmp_path: Path):
    path = tmp_path / "newer.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "UPDATE crl_schema_meta SET version = 99 WHERE component = ?",
            (SCHEMA_COMPONENT_P1,),
        )
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(UnsupportedSchemaVersionError, match="unknown newer"):
        open_legacy_compatibility(path)

    with pytest.raises(UnsupportedSchemaVersionError, match="unknown newer"):
        connect_p1(path)


def test_explicit_migration_success(tmp_path: Path):
    path = tmp_path / "p1.sqlite"
    ver = migrate_database(path)
    assert ver == CURRENT_P1_SCHEMA_VERSION
    assert read_schema_version_from_path(path) == CURRENT_P1_SCHEMA_VERSION

    conn = connect_p1(path)
    try:
        assert int(conn.execute("PRAGMA foreign_keys").fetchone()[0]) == 1
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for t in (
            "crl_schema_meta",
            "research_lineages",
            "governance_epochs",
            "programme_versions",
            "programme_split_manifests",
        ):
            assert t in tables
        assert get_schema_version(conn) == CURRENT_P1_SCHEMA_VERSION
    finally:
        conn.close()


def test_migration_rollback_before_any_ddl(tmp_path: Path):
    path = tmp_path / "fail_before.sqlite"
    with pytest.raises(SchemaMigrationError, match="injected failure before"):
        migrate_database(path, _inject_failure_before_version=1)

    if path.exists():
        conn = sqlite3.connect(str(path))
        try:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            assert "crl_schema_meta" not in tables
            assert get_schema_version(conn) is None
        finally:
            conn.close()


def test_migration_rollback_after_partial_ddl(tmp_path: Path):
    path = tmp_path / "fail_partial.sqlite"
    with pytest.raises(SchemaMigrationError, match="after 1 DDL"):
        migrate_database(path, _inject_failure_after_statements=1)

    conn = sqlite3.connect(str(path))
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "crl_schema_meta" not in tables
        assert "governance_epochs" not in tables
        assert get_schema_version(conn) is None
    finally:
        conn.close()


def test_migration_idempotent_repeat(tmp_path: Path):
    path = tmp_path / "idem.sqlite"
    assert migrate_database(path) == CURRENT_P1_SCHEMA_VERSION
    assert migrate_database(path) == CURRENT_P1_SCHEMA_VERSION
    conn = sqlite3.connect(str(path))
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM crl_schema_meta WHERE component=?",
            (SCHEMA_COMPONENT_P1,),
        ).fetchone()[0]
        assert n == 1
    finally:
        conn.close()

    v1_path = tmp_path / "idem_v1.sqlite"
    assert migrate_database(v1_path, target_version=1) == 1
    assert migrate_database(v1_path, target_version=1) == 1


def test_unknown_newer_version_rejected_on_migrate(tmp_path: Path):
    path = tmp_path / "newer.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "UPDATE crl_schema_meta SET version = 99 WHERE component = ?",
            (SCHEMA_COMPONENT_P1,),
        )
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(UnsupportedSchemaVersionError, match="unknown newer"):
        migrate_database(path)


def test_unsupported_downgrade_rejected(tmp_path: Path):
    path = tmp_path / "down.sqlite"
    migrate_database(path, target_version=1)
    with pytest.raises(UnsupportedSchemaVersionError, match="downgrade"):
        migrate_database(path, target_version=0)


def test_unknown_target_above_current_rejected(tmp_path: Path):
    path = tmp_path / "tgt.sqlite"
    with pytest.raises(UnsupportedSchemaVersionError, match="unknown newer target"):
        migrate_database(path, target_version=CURRENT_P1_SCHEMA_VERSION + 5)


def test_malformed_existing_table_fails_unstamped(tmp_path: Path):
    """Conflicting pre-existing table → SchemaMigrationError, no version stamp."""
    path = tmp_path / "bad.sqlite"
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "CREATE TABLE governance_epochs (wrong_col INTEGER PRIMARY KEY)"
        )
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(SchemaMigrationError, match="conflicting|missing columns"):
        migrate_database(path)

    conn = sqlite3.connect(str(path))
    try:
        assert get_schema_version(conn) is None
        # Malformed table still present (rollback of failed migrate does not
        # remove pre-existing user tables created outside the txn start...
        # actually our BEGIN rolls back only changes in the transaction;
        # pre-existing table remains. Critical: no stamp.
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='crl_schema_meta'"
        ).fetchone()
        # meta may have been created then rolled back
        assert row is None or get_schema_version(conn) is None
        assert get_schema_version(conn) is None
    finally:
        conn.close()


def test_connect_p1_does_not_create_missing_database(tmp_path: Path):
    missing = tmp_path / "nope.sqlite"
    assert not missing.exists()
    with pytest.raises(FileNotFoundError, match="does not create"):
        connect_p1(missing)
    assert not missing.exists()


def test_connect_p1_rejects_unversioned_database(tmp_path: Path):
    path = tmp_path / "empty.sqlite"
    sqlite3.connect(str(path)).close()
    assert path.is_file()
    with pytest.raises(SchemaError, match="unversioned"):
        connect_p1(path)


def test_connect_p1_rejects_legacy_registry_db(tmp_path: Path):
    path = tmp_path / "legacy_reg.sqlite"
    HypothesisRegistry(path)
    with pytest.raises(SchemaError, match="unversioned"):
        connect_p1(path)


def test_get_schema_version_absent_vs_malformed(tmp_path: Path):
    path = tmp_path / "meta.sqlite"
    conn = sqlite3.connect(str(path))
    try:
        assert get_schema_version(conn) is None  # absent
        conn.execute("CREATE TABLE crl_schema_meta (only_wrong TEXT)")
        conn.commit()
        with pytest.raises(MalformedSchemaMetaError, match="missing columns"):
            get_schema_version(conn)
    finally:
        conn.close()

    with pytest.raises(MalformedSchemaMetaError):
        open_legacy_compatibility(path)


def test_get_schema_version_non_integer_fails_closed(tmp_path: Path):
    path = tmp_path / "badver.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "UPDATE crl_schema_meta SET version = 'not-a-number' WHERE component=?",
            (SCHEMA_COMPONENT_P1,),
        )
        conn.commit()
        with pytest.raises(MalformedSchemaMetaError):
            get_schema_version(conn)
    finally:
        conn.close()

    with pytest.raises(MalformedSchemaMetaError):
        open_legacy_compatibility(path)


def test_foreign_keys_reject_orphan_epoch(tmp_path: Path):
    path = tmp_path / "fk.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        assert int(conn.execute("PRAGMA foreign_keys").fetchone()[0]) == 1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO governance_epochs(
                    governance_epoch_id, research_lineage_id, completeness, lifecycle
                ) VALUES ('ep1', 'missing_lineage', 'INCOMPLETE_UNBOUNDED', 'open')
                """
            )
            conn.commit()
    finally:
        conn.close()


def test_cross_table_lineage_epoch_must_match_programme_lineage(tmp_path: Path):
    """Programme governance_epoch must belong to the same research_lineage_id."""
    path = tmp_path / "lineage.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('linA', '', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('linB', '', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            """
            INSERT INTO governance_epochs(
                governance_epoch_id, research_lineage_id, completeness, lifecycle
            ) VALUES ('epA', 'linA', 'INCOMPLETE_UNBOUNDED', 'open')
            """
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            # same epoch id but programme claims linB
            conn.execute(
                """
                INSERT INTO programme_versions(
                    programme_version_id, programme_lineage_id, research_lineage_id,
                    governance_epoch_id, parent_programme_version_id, version_reason,
                    prior_results_available_at_creation, split_manifest_content_hash,
                    created_at
                ) VALUES (
                    'pv1', 'pl1', 'linB', 'epA', NULL, 'fixture',
                    1, ?, '2020-01-01T00:00:00.000000Z'
                )
                """,
                (VALID_HASH_A,),
            )
            conn.commit()
    finally:
        conn.close()


def test_manifest_hash_must_match_programme_version_hash(tmp_path: Path):
    path = tmp_path / "hash.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', '', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv1', 'pl1', 'lin1', NULL, NULL, 'fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_A,),
        )
        conn.commit()
        # Mismatched content_hash vs split_manifest_content_hash
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO programme_split_manifests(
                    content_hash, programme_version_id, manifest_json, created_at
                ) VALUES (?, 'pv1', '{}', '2020-01-01T00:00:00.000000Z')
                """,
                (VALID_HASH_B,),
            )
            conn.commit()
        # Matching hash succeeds
        conn.execute(
            """
            INSERT INTO programme_split_manifests(
                content_hash, programme_version_id, manifest_json, created_at
            ) VALUES (?, 'pv1', '{}', '2020-01-01T00:00:00.000000Z')
            """,
            (VALID_HASH_A,),
        )
        conn.commit()
    finally:
        conn.close()


def test_sha256_check_rejects_short_or_uppercase_hash(tmp_path: Path):
    path = tmp_path / "sha.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', '', '2020-01-01T00:00:00.000000Z')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO programme_versions(
                    programme_version_id, programme_lineage_id, research_lineage_id,
                    governance_epoch_id, parent_programme_version_id, version_reason,
                    prior_results_available_at_creation, split_manifest_content_hash,
                    created_at
                ) VALUES (
                    'pv1', 'pl1', 'lin1', NULL, NULL, 'fixture',
                    1, 'abc', '2020-01-01T00:00:00.000000Z'
                )
                """
            )
            conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO programme_versions(
                    programme_version_id, programme_lineage_id, research_lineage_id,
                    governance_epoch_id, parent_programme_version_id, version_reason,
                    prior_results_available_at_creation, split_manifest_content_hash,
                    created_at
                ) VALUES (
                    'pv2', 'pl1', 'lin1', NULL, NULL, 'fixture',
                    1, ?, '2020-01-01T00:00:00.000000Z'
                )
                """,
                ("A" * 64,),
            )
            conn.commit()
    finally:
        conn.close()


def test_parent_programme_fk(tmp_path: Path):
    path = tmp_path / "parent.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', '', '2020-01-01T00:00:00.000000Z')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO programme_versions(
                    programme_version_id, programme_lineage_id, research_lineage_id,
                    governance_epoch_id, parent_programme_version_id, version_reason,
                    prior_results_available_at_creation, split_manifest_content_hash,
                    created_at
                ) VALUES (
                    'pv_child', 'pl1', 'lin1', NULL, 'missing_parent', 'fixture',
                    1, ?, '2020-01-01T00:00:00.000000Z'
                )
                """,
                (VALID_HASH_A,),
            )
            conn.commit()
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv_parent', 'pl1', 'lin1', NULL, NULL, 'fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_A,),
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv_child', 'pl1', 'lin1', NULL, 'pv_parent', 'fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_B,),
        )
        conn.commit()
        # Same parent id but different programme_lineage_id is rejected
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO programme_versions(
                    programme_version_id, programme_lineage_id, research_lineage_id,
                    governance_epoch_id, parent_programme_version_id, version_reason,
                    prior_results_available_at_creation, split_manifest_content_hash,
                    created_at
                ) VALUES (
                    'pv_other_lineage', 'pl_OTHER', 'lin1', NULL, 'pv_parent', 'fixture',
                    1, ?, '2020-01-01T00:00:00.000000Z'
                )
                """,
                ("c" * 64,),
            )
            conn.commit()
    finally:
        conn.close()


def test_parent_same_programme_lineage_different_research_lineage_rejected(
    tmp_path: Path,
):
    """Ordinary parent must match research_lineage_id as well as programme_lineage_id."""
    path = tmp_path / "parent_rline.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('linA', '', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('linB', '', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv_parent', 'pl1', 'linA', NULL, NULL, 'fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_A,),
        )
        conn.commit()
        # Same programme lineage, different research lineage → rejected
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO programme_versions(
                    programme_version_id, programme_lineage_id, research_lineage_id,
                    governance_epoch_id, parent_programme_version_id, version_reason,
                    prior_results_available_at_creation, split_manifest_content_hash,
                    created_at
                ) VALUES (
                    'pv_child', 'pl1', 'linB', NULL, 'pv_parent', 'fixture',
                    1, ?, '2020-01-01T00:00:00.000000Z'
                )
                """,
                (VALID_HASH_B,),
            )
            conn.commit()
    finally:
        conn.close()


def test_connect_p1_rejects_stamped_damaged_schema(tmp_path: Path):
    """Stamped v1 missing programme_split_manifests must not open."""
    path = tmp_path / "damaged.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("DROP TABLE programme_split_manifests")
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="verification|missing"):
        connect_p1(path)


def test_connect_p1_rejects_existing_fk_violations(tmp_path: Path):
    path = tmp_path / "fkviol.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', '', '2020-01-01T00:00:00.000000Z')"
        )
        # Orphan governance_epoch_id (no such epoch)
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv1', 'pl1', 'lin1', 'missing_epoch', NULL, 'fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_A,),
        )
        conn.commit()
        assert conn.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="foreign key violations"):
        connect_p1(path)


def test_verify_rejects_incorrect_composite_fk_grouping(tmp_path: Path):
    """Single-column FKs are not a substitute for the composite hash FK."""
    path = tmp_path / "bad_composite.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("DROP TABLE programme_split_manifests")
        # Wrong: only version FK, not (version, content_hash) composite
        conn.execute(
            """
            CREATE TABLE programme_split_manifests (
                content_hash TEXT NOT NULL,
                programme_version_id TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (content_hash),
                UNIQUE (programme_version_id),
                FOREIGN KEY (programme_version_id)
                    REFERENCES programme_versions(programme_version_id)
            )
            """
        )
        conn.commit()
        with pytest.raises(SchemaMigrationError, match="composite foreign keys"):
            verify_p1_v1_schema(conn)
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="verification|composite|missing"):
        connect_p1(path)


def test_one_manifest_per_programme_version(tmp_path: Path):
    path = tmp_path / "uniq.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', 'test', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv1', 'pl1', 'lin1', NULL, NULL, 'fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_A,),
        )
        conn.execute(
            """
            INSERT INTO programme_split_manifests(
                content_hash, programme_version_id, manifest_json, created_at
            ) VALUES (?, 'pv1', '{}', '2020-01-01T00:00:00.000000Z')
            """,
            (VALID_HASH_A,),
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO programme_split_manifests(
                    content_hash, programme_version_id, manifest_json, created_at
                ) VALUES (?, 'pv1', '{}', '2020-01-01T00:00:00.000000Z')
                """,
                (VALID_HASH_B,),
            )
            conn.commit()
    finally:
        conn.close()


def test_check_rejects_invalid_completeness_status(tmp_path: Path):
    path = tmp_path / "chk.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', 'test', '2020-01-01T00:00:00.000000Z')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO governance_epochs(
                    governance_epoch_id, research_lineage_id, completeness, lifecycle
                ) VALUES ('ep1', 'lin1', 'nonsense', 'open')
                """
            )
            conn.commit()
    finally:
        conn.close()


def test_whitespace_only_optional_ids_rejected():
    with pytest.raises(ValidationError):
        ProgrammeVersion(
            programme_version_id="pv",
            programme_lineage_id="pl",
            research_lineage_id="rl",
            governance_epoch_id="   ",
            version_reason="x",
            prior_results_available_at_creation=True,
            split_manifest_content_hash=VALID_HASH_A,
        )
    with pytest.raises(ValidationError):
        ProgrammeVersion(
            programme_version_id="pv",
            programme_lineage_id="pl",
            research_lineage_id="rl",
            parent_programme_version_id="  ",
            version_reason="x",
            prior_results_available_at_creation=True,
            split_manifest_content_hash=VALID_HASH_A,
        )


def test_model_requires_sha256_hex_hash():
    with pytest.raises(ValidationError):
        ProgrammeVersion(
            programme_version_id="pv",
            programme_lineage_id="pl",
            research_lineage_id="rl",
            version_reason="x",
            prior_results_available_at_creation=True,
            split_manifest_content_hash="abc",
        )


def test_null_epoch_defaults_to_incomplete_unbounded_not_legacy_reconstructed():
    assert (
        derive_completeness(governance_epoch_id=None)
        == GovernanceCompleteness.INCOMPLETE_UNBOUNDED
    )
    assert (
        legacy_epoch_status_for_null(None)
        == GovernanceCompleteness.INCOMPLETE_UNBOUNDED.value
    )
    assert (
        never_auto_complete(None, "COMPLETE")
        == GovernanceCompleteness.INCOMPLETE_UNBOUNDED.value
    )
    assert derive_completeness(governance_epoch_id="any") != GovernanceCompleteness.COMPLETE


def test_public_constructor_cannot_establish_complete():
    with pytest.raises(ValidationError, match="COMPLETE"):
        GovernanceEpoch(
            governance_epoch_id="e1",
            research_lineage_id="r1",
            completeness=GovernanceCompleteness.COMPLETE,
        )


def test_research_lineage_created_at_required_utc():
    rl = ResearchLineage(research_lineage_id="r1")
    assert rl.created_at.tzinfo is not None
    with pytest.raises(ValidationError):
        ResearchLineage(
            research_lineage_id="r2",
            created_at=datetime(2020, 1, 1),
        )


def test_allowed_completeness_enum_values():
    values = {c.value for c in GovernanceCompleteness}
    assert values == {
        "COMPLETE",
        "INCOMPLETE_KNOWN_GAPS",
        "INCOMPLETE_UNBOUNDED",
        "LEGACY_RECONSTRUCTED_CONSERVATIVELY",
    }


def test_legacy_rows_remain_null_epoch_after_migrate(tmp_path: Path):
    path = tmp_path / "leg.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', 'test', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv_legacy', 'pl1', 'lin1', NULL, NULL, 'legacy fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_A,),
        )
        conn.commit()
        row = conn.execute(
            "SELECT governance_epoch_id FROM programme_versions WHERE programme_version_id='pv_legacy'"
        ).fetchone()
        assert row[0] is None
        n_complete = conn.execute(
            "SELECT COUNT(*) FROM governance_epochs WHERE completeness = 'COMPLETE'"
        ).fetchone()[0]
        assert n_complete == 0
    finally:
        conn.close()
    migrate_database(path)
    conn = connect_p1(path)
    try:
        row = conn.execute(
            "SELECT governance_epoch_id FROM programme_versions WHERE programme_version_id='pv_legacy'"
        ).fetchone()
        assert row[0] is None
    finally:
        conn.close()


def test_now_uses_single_timestamp(monkeypatch: pytest.MonkeyPatch):
    """``_now`` must read the clock exactly once (not combine two instants)."""
    from datetime import timezone as tz

    from crl.db import schema as sch

    fixed = datetime(2020, 1, 2, 3, 4, 5, 123456, tzinfo=tz.utc)
    calls: list[int] = []

    class _FakeDateTime:
        timezone = tz

        @staticmethod
        def now(tzinfo=None):
            calls.append(1)
            return fixed

    monkeypatch.setattr(sch, "datetime", _FakeDateTime)
    out = sch._now()
    assert len(calls) == 1
    assert out == "2020-01-02T03:04:05.123456Z"


def test_immutability_triggers_programme_versions(tmp_path: Path):
    path = tmp_path / "imm_pv.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', '', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv1', 'pl1', 'lin1', NULL, NULL, 'fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_A,),
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute(
                "UPDATE programme_versions SET version_reason='x' WHERE programme_version_id='pv1'"
            )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute("DELETE FROM programme_versions WHERE programme_version_id='pv1'")
    finally:
        conn.close()


def test_immutability_triggers_manifests(tmp_path: Path):
    path = tmp_path / "imm_mf.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', '', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv1', 'pl1', 'lin1', NULL, NULL, 'fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_A,),
        )
        conn.execute(
            """
            INSERT INTO programme_split_manifests(
                content_hash, programme_version_id, manifest_json, created_at
            ) VALUES (?, 'pv1', '{}', '2020-01-01T00:00:00.000000Z')
            """,
            (VALID_HASH_A,),
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute(
                "UPDATE programme_split_manifests SET manifest_json='x' WHERE content_hash=?",
                (VALID_HASH_A,),
            )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute(
                "DELETE FROM programme_split_manifests WHERE content_hash=?",
                (VALID_HASH_A,),
            )
    finally:
        conn.close()


def test_immutability_triggers_research_lineages(tmp_path: Path):
    path = tmp_path / "imm_rl.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', 'd0', '2020-01-01T00:00:00.000000Z')"
        )
        conn.commit()
        # description may change
        conn.execute(
            "UPDATE research_lineages SET description='d1' WHERE research_lineage_id='lin1'"
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="identity|creation|immutable"):
            conn.execute(
                "UPDATE research_lineages SET created_at='2099-01-01T00:00:00.000000Z' "
                "WHERE research_lineage_id='lin1'"
            )
        with pytest.raises(sqlite3.IntegrityError, match="DELETE|forbidden"):
            conn.execute("DELETE FROM research_lineages WHERE research_lineage_id='lin1'")
    finally:
        conn.close()


def test_immutability_triggers_governance_epochs(tmp_path: Path):
    path = tmp_path / "imm_ge.sqlite"
    migrate_database(path)
    conn = connect_p1(path)
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', '', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            """
            INSERT INTO governance_epochs(
                governance_epoch_id, research_lineage_id, completeness, lifecycle,
                opened_at, notes
            ) VALUES (
                'ep1', 'lin1', 'INCOMPLETE_UNBOUNDED', 'open',
                '2020-01-01T00:00:00.000000Z', ''
            )
            """
        )
        conn.commit()
        # Allowed lifecycle path
        conn.execute(
            "UPDATE governance_epochs SET lifecycle='closed', closed_at='2021-01-01T00:00:00.000000Z', "
            "notes='closed by human' WHERE governance_epoch_id='ep1'"
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="immutable|identity"):
            conn.execute(
                "UPDATE governance_epochs SET completeness='COMPLETE' WHERE governance_epoch_id='ep1'"
            )
        with pytest.raises(sqlite3.IntegrityError, match="DELETE|forbidden"):
            conn.execute("DELETE FROM governance_epochs WHERE governance_epoch_id='ep1'")
    finally:
        conn.close()


def test_compat_open_rejects_damaged_stamped_database(tmp_path: Path):
    """Stamped DB must not bypass verification via open_legacy_compatibility."""
    path = tmp_path / "compat_damaged.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("DROP TABLE programme_split_manifests")
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="verification|missing"):
        open_legacy_compatibility(path)


def test_compat_open_still_allows_true_legacy_registry(tmp_path: Path):
    path = tmp_path / "true_legacy.sqlite"
    HypothesisRegistry(path)
    conn = open_legacy_compatibility(path)
    try:
        assert get_schema_version(conn) is None
        assert conn.execute("SELECT COUNT(*) FROM hypotheses").fetchone()[0] == 0
    finally:
        conn.close()


def test_integrity_check_failure_blocks_connect(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    path = tmp_path / "intfail.sqlite"
    migrate_database(path)
    from crl.db import schema as sch

    def boom(conn):
        raise SchemaError("integrity_check failed: not ok")

    monkeypatch.setattr(sch, "_assert_integrity_ok", boom)
    with pytest.raises(SchemaError, match="integrity_check failed"):
        connect_p1(path)


def test_integrity_check_failure_blocks_compat_stamped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    path = tmp_path / "intfail2.sqlite"
    migrate_database(path)
    from crl.db import schema as sch

    def boom(conn):
        raise SchemaError("integrity_check failed: not ok")

    monkeypatch.setattr(sch, "_assert_integrity_ok", boom)
    with pytest.raises(SchemaError, match="integrity_check failed"):
        open_legacy_compatibility(path)


def test_assert_integrity_ok_requires_exactly_ok(tmp_path: Path):
    from crl.db.schema import _assert_integrity_ok

    path = tmp_path / "ok.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        _assert_integrity_ok(conn)  # real ok
    finally:
        conn.close()

    class FakeConn:
        def execute(self, sql):
            class R:
                def fetchall(self_inner):
                    return [("*** in database main ***",), ("Page 1 is never used",)]

            return R()

    with pytest.raises(SchemaError, match="integrity_check failed"):
        _assert_integrity_ok(FakeConn())  # type: ignore[arg-type]


def _stamp_version(conn: sqlite3.Connection, version: int = 1) -> None:
    conn.execute(
        """
        INSERT INTO crl_schema_meta(component, version, applied_at)
        VALUES (?, ?, '2020-01-01T00:00:00.000000Z')
        ON CONFLICT(component) DO UPDATE SET version=excluded.version
        """,
        (SCHEMA_COMPONENT_P1, version),
    )
    conn.commit()


def test_verify_rejects_inert_when0_trigger(tmp_path: Path):
    """WHEN 0 inert body must not pass canonical trigger verification.

    Also proves the inert trigger is scientifically fail-open: UPDATE would
    succeed if verification were skipped.
    """
    path = tmp_path / "when0.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "INSERT INTO research_lineages(research_lineage_id, description, created_at) "
            "VALUES ('lin1', '', '2020-01-01T00:00:00.000000Z')"
        )
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv1', 'pl1', 'lin1', NULL, NULL, 'fixture',
                1, ?, '2020-01-01T00:00:00.000000Z'
            )
            """,
            (VALID_HASH_A,),
        )
        conn.execute("DROP TRIGGER trg_programme_versions_no_update")
        conn.execute(
            """
            CREATE TRIGGER trg_programme_versions_no_update
            BEFORE UPDATE ON programme_versions
            WHEN 0
            BEGIN
                SELECT RAISE(ABORT, 'programme_versions is immutable: UPDATE forbidden');
            END
            """
        )
        conn.commit()
        # Fail-open proof: inert WHEN 0 allows UPDATE
        conn.execute(
            "UPDATE programme_versions SET version_reason='tampered' "
            "WHERE programme_version_id='pv1'"
        )
        conn.commit()
        row = conn.execute(
            "SELECT version_reason FROM programme_versions WHERE programme_version_id='pv1'"
        ).fetchone()
        assert row[0] == "tampered"
        with pytest.raises(SchemaMigrationError, match="canonical|SQL|semantics"):
            verify_p1_v1_schema(conn)
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="verification|canonical|SQL|semantics"):
        connect_p1(path)
    with pytest.raises(SchemaError, match="verification|canonical|SQL|semantics"):
        open_legacy_compatibility(path)


def test_verify_rejects_unexpected_p1_trigger(tmp_path: Path):
    path = tmp_path / "extra_trg.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            """
            CREATE TRIGGER trg_unexpected_extra
            BEFORE INSERT ON programme_versions
            BEGIN
                SELECT RAISE(ABORT, 'unexpected');
            END
            """
        )
        conn.commit()
        with pytest.raises(SchemaMigrationError, match="unexpected trigger"):
            verify_p1_v1_schema(conn)
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="verification|unexpected"):
        connect_p1(path)


def test_verify_rejects_wrong_operation_trigger(tmp_path: Path):
    path = tmp_path / "wrong_op.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("DROP TRIGGER trg_programme_versions_no_update")
        # Wrong operation: DELETE instead of UPDATE
        conn.execute(
            """
            CREATE TRIGGER trg_programme_versions_no_update
            BEFORE DELETE ON programme_versions
            BEGIN
                SELECT RAISE(ABORT, 'programme_versions is immutable: UPDATE forbidden');
            END
            """
        )
        conn.commit()
        with pytest.raises(SchemaMigrationError, match="canonical|SQL|semantics"):
            verify_p1_v1_schema(conn)
    finally:
        conn.close()
    with pytest.raises(SchemaError):
        connect_p1(path)


def test_verify_rejects_incomplete_protected_column_when(tmp_path: Path):
    path = tmp_path / "partial_when.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("DROP TRIGGER trg_governance_epochs_identity_guard")
        # Incomplete WHEN: omits completeness and opened_at protections
        conn.execute(
            """
            CREATE TRIGGER trg_governance_epochs_identity_guard
            BEFORE UPDATE ON governance_epochs
            WHEN OLD.governance_epoch_id IS NOT NEW.governance_epoch_id
              OR OLD.research_lineage_id IS NOT NEW.research_lineage_id
            BEGIN
                SELECT RAISE(ABORT,
                    'governance_epochs identity/completeness/opened_at immutable');
            END
            """
        )
        conn.commit()
        with pytest.raises(SchemaMigrationError, match="canonical|SQL|semantics"):
            verify_p1_v1_schema(conn)
    finally:
        conn.close()
    with pytest.raises(SchemaError):
        open_legacy_compatibility(path)


def test_compat_open_fails_when_version_row_deleted_but_p1_tables_remain(
    tmp_path: Path,
):
    path = tmp_path / "ver_deleted.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "DELETE FROM crl_schema_meta WHERE component=?",
            (SCHEMA_COMPONENT_P1,),
        )
        conn.execute("DROP TABLE programme_split_manifests")
        conn.commit()
        assert get_schema_version(conn) is None
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="partially migrated|corrupted"):
        open_legacy_compatibility(path)


def test_compat_open_fails_partial_p1_objects_without_version_row(tmp_path: Path):
    path = tmp_path / "partial_p1.sqlite"
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            """
            CREATE TABLE research_lineages (
                research_lineage_id TEXT PRIMARY KEY,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="partially migrated|corrupted"):
        open_legacy_compatibility(path)


def test_compat_open_genuine_legacy_registry_still_ok(tmp_path: Path):
    path = tmp_path / "genuine_legacy.sqlite"
    HypothesisRegistry(path)
    # No P1 objects; RO open succeeds
    c = open_legacy_compatibility(path)
    try:
        assert get_schema_version(c) is None
        tables = {
            r[0]
            for r in c.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "hypotheses" in tables
        assert "research_lineages" not in tables
    finally:
        c.close()
