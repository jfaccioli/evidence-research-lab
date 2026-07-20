"""PR1: explicit schema versioning on temporary databases only."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from crl.db.schema import (
    CURRENT_P1_SCHEMA_VERSION,
    SCHEMA_COMPONENT_P1,
    SchemaMigrationError,
    UnsupportedSchemaVersionError,
    get_schema_version,
    legacy_epoch_status_for_null,
    migrate_database,
    never_auto_complete,
    open_legacy_compatibility,
    read_schema_version_from_path,
)
from crl.research.hypotheses.registry import HypothesisRegistry, SCHEMA as LEGACY_SCHEMA
from crl.research.programme.models import GovernanceEpochStatus


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_legacy_db(path: Path) -> None:
    """Synthetic pre-P1 registry-shaped DB (no crl_schema_meta)."""
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
    """Importing crl.db must not create or touch databases."""
    db = tmp_path / "untouched.sqlite"
    assert not db.exists()
    import crl.db  # noqa: F401
    import crl.db.schema  # noqa: F401
    import crl.db.migrations  # noqa: F401

    assert not db.exists()
    assert list(tmp_path.iterdir()) == []


def test_hypothesis_registry_does_not_run_p1_migration(tmp_path: Path):
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
        assert "crl_schema_meta" not in tables
        assert "governance_epochs" not in tables
        assert "programme_versions" not in tables
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
        # Writes must fail in RO mode
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("CREATE TABLE should_fail (x INTEGER)")
    finally:
        conn.close()

    after = _file_sha256(path)
    assert after == before
    assert path.stat().st_size == size_before
    assert path.stat().st_mtime_ns == mtime_before
    assert read_schema_version_from_path(path) is None


def test_explicit_migration_success(tmp_path: Path):
    path = tmp_path / "p1.sqlite"
    ver = migrate_database(path)
    assert ver == CURRENT_P1_SCHEMA_VERSION
    assert read_schema_version_from_path(path) == CURRENT_P1_SCHEMA_VERSION

    conn = sqlite3.connect(str(path))
    try:
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
        v = get_schema_version(conn)
        assert v == 1
    finally:
        conn.close()


def test_migration_rollback_after_injected_failure(tmp_path: Path):
    path = tmp_path / "fail.sqlite"
    with pytest.raises(SchemaMigrationError, match="injected failure"):
        migrate_database(path, _inject_failure_before_version=1)

    # File may exist but must not have committed P1 schema version / tables
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
            assert "governance_epochs" not in tables
            assert get_schema_version(conn) is None
        finally:
            conn.close()


def test_migration_idempotent_repeat(tmp_path: Path):
    path = tmp_path / "idem.sqlite"
    assert migrate_database(path) == 1
    assert migrate_database(path) == 1
    assert migrate_database(path, target_version=1) == 1
    conn = sqlite3.connect(str(path))
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM crl_schema_meta WHERE component=?",
            (SCHEMA_COMPONENT_P1,),
        ).fetchone()[0]
        assert n == 1
    finally:
        conn.close()


def test_unknown_newer_version_rejected(tmp_path: Path):
    path = tmp_path / "newer.sqlite"
    migrate_database(path)
    # Manually stamp an unsupported future version
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


def test_legacy_records_never_auto_complete(tmp_path: Path):
    """Null/legacy epoch rows never become COMPLETE via migration or helpers."""
    path = tmp_path / "leg.sqlite"
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            """
            INSERT INTO research_lineages(research_lineage_id, description, created_at)
            VALUES ('lin1', 'test', '2020-01-01T00:00:00Z')
            """
        )
        # Legacy programme version: null governance_epoch_id
        conn.execute(
            """
            INSERT INTO programme_versions(
                programme_version_id, programme_lineage_id, research_lineage_id,
                governance_epoch_id, parent_programme_version_id, version_reason,
                prior_results_available_at_creation, split_manifest_content_hash,
                created_at
            ) VALUES (
                'pv_legacy', 'pl1', 'lin1', NULL, NULL, 'legacy fixture',
                1, 'abc', '2020-01-01T00:00:00Z'
            )
            """
        )
        conn.commit()
        row = conn.execute(
            "SELECT governance_epoch_id FROM programme_versions WHERE programme_version_id='pv_legacy'"
        ).fetchone()
        assert row[0] is None
        assert legacy_epoch_status_for_null(row[0]) == "legacy"
        assert never_auto_complete(row[0], None) == "legacy"
        assert never_auto_complete(None, "complete") == "legacy"
        assert GovernanceEpochStatus.LEGACY.value == "legacy"
        assert GovernanceEpochStatus.COMPLETE.value == "complete"
        # Migration did not insert any COMPLETE epoch
        n_complete = conn.execute(
            "SELECT COUNT(*) FROM governance_epochs WHERE status = 'complete'"
        ).fetchone()[0]
        assert n_complete == 0
    finally:
        conn.close()

    # Re-running migrate leaves legacy row null
    migrate_database(path)
    conn = sqlite3.connect(str(path))
    try:
        row = conn.execute(
            "SELECT governance_epoch_id FROM programme_versions WHERE programme_version_id='pv_legacy'"
        ).fetchone()
        assert row[0] is None
    finally:
        conn.close()
