"""Explicit, transactional schema versioning for temporary P1 databases.

Hard rules (PR1):
- No migration on import.
- No migration on ordinary HypothesisRegistry construction.
- Migrations only via ``migrate_database``.
- ``connect_p1`` never creates or migrates; requires an existing versioned DB.
- ``connect_p1`` runs the full schema verifier for the stored version and
  ``PRAGMA foreign_key_check`` before returning.
- Opening a legacy DB in compatibility mode must not change its bytes.
- Unknown / newer schema versions fail closed (including compatibility open).
- Malformed ``crl_schema_meta`` fails closed (distinct from meta-absent).
- Conflicting / incomplete post-migration schema fails before version stamp.
- COMPLETE is never established by public helpers (PR3 reconciliation only).
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from crl.db.migrations import (
    MIGRATION_STATEMENTS,
    MIGRATIONS,
    P1_V1_ALL_TABLES,
    P1_V1_COLUMNS,
    P1_V1_DATA_TABLES,
    P1_V1_FOREIGN_KEYS,
    P1_V1_INDEXES,
    P1_V1_TRIGGER_SQL,
    P1_V1_TRIGGERS,
    P1_V2_COLUMNS,
    P1_V2_DATA_TABLES,
    P1_V2_FOREIGN_KEYS,
    P1_V2_INDEXES,
    P1_V2_TRIGGER_SQL,
    P1_V2_TRIGGERS,
    P1_V3_COLUMNS,
    P1_V3_DATA_TABLES,
    P1_V3_FOREIGN_KEYS,
    P1_V3_INDEXES,
    P1_V3_TRIGGER_SQL,
    P1_V3_TRIGGERS,
    P1_V4_COLUMNS,
    P1_V4_DATA_TABLES,
    P1_V4_FOREIGN_KEYS,
    P1_V4_INDEXES,
    P1_V4_TRIGGER_SQL,
    P1_V4_TRIGGERS,
    P1_V5_COLUMNS,
    P1_V5_DATA_TABLES,
    P1_V5_FOREIGN_KEYS,
    P1_V5_INDEXES,
    P1_V5_TRIGGER_SQL,
    P1_V5_TRIGGERS,
    ColumnSpec,
    CompositeFK,
    IndexSpec,
    _normalize_sql,
)
from crl.research.programme.models import GovernanceCompleteness

SCHEMA_COMPONENT_P1 = "p1_programme"
CURRENT_P1_SCHEMA_VERSION = 5

_MAX_DEFINED_VERSION = max(v for v, _ in MIGRATIONS) if MIGRATIONS else 0
if CURRENT_P1_SCHEMA_VERSION != _MAX_DEFINED_VERSION:
    raise RuntimeError(
        f"CURRENT_P1_SCHEMA_VERSION={CURRENT_P1_SCHEMA_VERSION} "
        f"!= max migration version={_MAX_DEFINED_VERSION}"
    )


class SchemaError(Exception):
    """Base schema / version error (fail closed)."""


class SchemaMigrationError(SchemaError):
    """Migration failed; transaction should leave DB unchanged / unstamped."""


class UnsupportedSchemaVersionError(SchemaError):
    """Downgrade or unknown newer schema — fail closed."""


class MalformedSchemaMetaError(SchemaError):
    """``crl_schema_meta`` exists but is unreadable / malformed — fail closed."""


def _now() -> str:
    """Single UTC timestamp with full microsecond precision (Z suffix)."""
    ts = datetime.now(timezone.utc)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond:06d}Z"


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def get_schema_version(
    conn: sqlite3.Connection,
    *,
    component: str = SCHEMA_COMPONENT_P1,
) -> Optional[int]:
    """Return stored schema version.

    - ``None`` if the meta table is **absent** (true legacy / unversioned).
    - Raises ``MalformedSchemaMetaError`` if the meta table exists but is
      malformed or the version value is not a valid non-negative integer.
    """
    if not _table_exists(conn, "crl_schema_meta"):
        return None

    try:
        cols = {
            r[1]: (r[2] or "").upper()
            for r in conn.execute("PRAGMA table_info(crl_schema_meta)").fetchall()
        }
    except sqlite3.Error as exc:
        raise MalformedSchemaMetaError(
            "crl_schema_meta exists but PRAGMA table_info failed"
        ) from exc

    required = {"component", "version", "applied_at"}
    if not required <= set(cols):
        raise MalformedSchemaMetaError(
            f"crl_schema_meta missing columns {sorted(required - set(cols))}"
        )

    try:
        row = conn.execute(
            "SELECT version FROM crl_schema_meta WHERE component = ?",
            (component,),
        ).fetchone()
    except sqlite3.Error as exc:
        raise MalformedSchemaMetaError(
            "crl_schema_meta query failed (malformed table)"
        ) from exc

    if row is None:
        return None

    raw = row[0]
    if raw is None:
        raise MalformedSchemaMetaError("schema version is NULL")
    if isinstance(raw, bool):
        raise MalformedSchemaMetaError("schema version is not an integer")
    if isinstance(raw, int):
        version = raw
    elif isinstance(raw, str) and raw.strip().isdigit():
        version = int(raw.strip())
    else:
        try:
            if isinstance(raw, float) and raw != int(raw):
                raise MalformedSchemaMetaError(
                    f"schema version is not an integer: {raw!r}"
                )
            version = int(raw)
        except (TypeError, ValueError) as exc:
            raise MalformedSchemaMetaError(
                f"schema version is not an integer: {raw!r}"
            ) from exc

    if version < 0:
        raise MalformedSchemaMetaError(f"schema version is negative: {version}")
    return version


def _assert_supported_version(version: Optional[int]) -> None:
    if version is None:
        return
    if version > CURRENT_P1_SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(
            f"database has unknown newer schema version {version} "
            f"(max supported {CURRENT_P1_SCHEMA_VERSION}); fail closed"
        )
    if version < 0:
        raise UnsupportedSchemaVersionError(f"invalid schema version {version}")


def read_schema_version_from_path(
    path: str | Path,
    *,
    component: str = SCHEMA_COMPONENT_P1,
) -> Optional[int]:
    with open_legacy_compatibility(path) as conn:
        return get_schema_version(conn, component=component)


def _assert_no_fk_violations(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA foreign_key_check").fetchall()
    if rows:
        sample = [
            f"table={r[0]} rowid={r[1]} parent={r[2]} fkid={r[3]}" for r in rows[:5]
        ]
        raise SchemaError(
            f"foreign key violations present ({len(rows)}): " + "; ".join(sample)
        )


def _assert_integrity_ok(conn: sqlite3.Connection) -> None:
    """Require ``PRAGMA integrity_check`` to return exactly ``ok``."""
    rows = conn.execute("PRAGMA integrity_check").fetchall()
    if not rows or rows[0][0] != "ok" or len(rows) != 1:
        detail = ", ".join(str(r[0]) for r in rows[:5]) if rows else "(empty)"
        raise SchemaError(f"integrity_check failed: {detail}")


def _assert_trusted_open_checks(conn: sqlite3.Connection, version: int) -> None:
    """Full semantic verification + FK + integrity for a stamped DB."""
    try:
        verify_schema_for_version(conn, version)
    except SchemaMigrationError as exc:
        raise SchemaError(f"stored schema fails verification: {exc}") from exc
    _assert_no_fk_violations(conn)
    _assert_integrity_ok(conn)


def _p1_objects_exist(conn: sqlite3.Connection) -> bool:
    """True if any P1 data table, secondary index, or immutability trigger exists."""
    for name in (
        P1_V1_DATA_TABLES
        + P1_V2_DATA_TABLES
        + P1_V3_DATA_TABLES
        + P1_V4_DATA_TABLES
    ):
        if _table_exists(conn, name):
            return True
    for idx_name in (
        tuple(P1_V1_INDEXES)
        + tuple(P1_V2_INDEXES)
        + tuple(P1_V3_INDEXES)
        + tuple(P1_V4_INDEXES)
    ):
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
            (idx_name,),
        ).fetchone()
        if row is not None:
            return True
    for trg_name in (
        tuple(P1_V1_TRIGGERS)
        + tuple(P1_V2_TRIGGERS)
        + tuple(P1_V3_TRIGGERS)
        + tuple(P1_V4_TRIGGERS)
    ):
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?",
            (trg_name,),
        ).fetchone()
        if row is not None:
            return True
    # Meta table without a version row is also a partial-P1 smell when empty of
    # data tables, but only treat as P1 object if meta exists *and* something
    # else P1-ish — pure empty meta alone still handled via version path.
    return False


def open_legacy_compatibility(path: str | Path) -> sqlite3.Connection:
    """Open an existing database **without** migrating or writing.

    - Unstamped **and** no P1 objects: genuine legacy HypothesisRegistry path
      (read-only, no P1 semantic verification).
    - Unstamped **but** any P1 data table/index/trigger exists: fail closed as
      corrupted / partially migrated (must not open as legacy).
    - Supported/current schema version present: full trusted-open verification
      (semantic schema + FK check + integrity_check).
    - Fail-closed on unknown newer versions and malformed schema meta.
    """
    p = Path(path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"database not found for compatibility open: {p}")
    uri = p.as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        version = get_schema_version(conn)
        _assert_supported_version(version)
        if version is None:
            if _p1_objects_exist(conn):
                raise SchemaError(
                    "corrupted or partially migrated P1 database: "
                    "P1 data objects/indexes/triggers exist but p1_programme "
                    "version row is absent"
                )
            # genuine legacy
            return conn
        _assert_trusted_open_checks(conn, version)
    except Exception:
        conn.close()
        raise
    return conn


def verify_schema_for_version(conn: sqlite3.Connection, version: int) -> None:
    """Dispatch full schema verification for a stamped version."""
    if version == 1:
        verify_p1_v1_schema(conn)
        return
    if version == 2:
        verify_p1_v2_schema(conn)
        return
    if version == 3:
        verify_p1_v3_schema(conn)
        return
    if version == 4:
        verify_p1_v4_schema(conn)
        return
    if version == 5:
        verify_p1_v5_schema(conn)
        return
    raise SchemaError(f"no schema verifier registered for version {version}")


def connect_p1(path: str | Path, *, readonly: bool = False) -> sqlite3.Connection:
    """Open an **existing, versioned** P1 database with foreign keys enforced.

    - Does **not** create a missing file.
    - Does **not** migrate.
    - Rejects unversioned databases.
    - Runs the **full schema verifier** for the stored version.
    - Runs ``PRAGMA foreign_key_check`` and ``PRAGMA integrity_check`` (must be ok).
    """
    p = Path(path).resolve()
    if not p.is_file():
        raise FileNotFoundError(
            f"P1 database not found: {p} "
            "(connect_p1 does not create databases; use migrate_database)"
        )
    if readonly:
        uri = p.as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        version = get_schema_version(conn)
        if version is None:
            conn.close()
            raise SchemaError(
                "database is unversioned; connect_p1 requires an explicit "
                "migrate_database() stamp"
            )
        _assert_supported_version(version)
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        if int(fk) != 1:
            conn.close()
            raise SchemaError("failed to enable PRAGMA foreign_keys")
        _assert_trusted_open_checks(conn, version)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        raise
    return conn


def _set_schema_version(
    conn: sqlite3.Connection,
    version: int,
    *,
    component: str = SCHEMA_COMPONENT_P1,
) -> None:
    conn.execute(
        """
        INSERT INTO crl_schema_meta(component, version, applied_at)
        VALUES (?, ?, ?)
        ON CONFLICT(component) DO UPDATE SET
            version = excluded.version,
            applied_at = excluded.applied_at
        """,
        (component, int(version), _now()),
    )


def _type_matches(actual: str, expected: str) -> bool:
    actual = (actual or "").upper()
    expected = (expected or "").upper()
    if not expected:
        return True
    aliases = {
        "INTEGER": {"INT", "INTEGER", "BIGINT"},
        "TEXT": {"TEXT", "VARCHAR", "CHAR", "CLOB"},
    }
    return actual in aliases.get(expected, {expected})


def _verify_table_columns(
    conn: sqlite3.Connection,
    table: str,
    expected: dict[str, ColumnSpec],
) -> None:
    if not _table_exists(conn, table):
        raise SchemaMigrationError(f"missing required table {table!r}")
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    # cid, name, type, notnull, dflt_value, pk
    found: dict[str, tuple[str, int, int]] = {
        r[1]: ((r[2] or "").upper(), int(r[3]), int(r[5])) for r in rows
    }
    missing = set(expected) - set(found)
    if missing:
        raise SchemaMigrationError(
            f"table {table!r} missing columns {sorted(missing)}"
        )
    extra = set(found) - set(expected)
    if extra:
        raise SchemaMigrationError(
            f"table {table!r} has unexpected columns {sorted(extra)}"
        )
    for col, spec in expected.items():
        actual_type, actual_nn, actual_pk = found[col]
        if not _type_matches(actual_type, spec.type):
            raise SchemaMigrationError(
                f"table {table!r} column {col!r} type {actual_type!r} "
                f"!= expected {spec.type!r}"
            )
        if actual_pk != spec.pk:
            raise SchemaMigrationError(
                f"table {table!r} column {col!r} pk={actual_pk} "
                f"!= expected {spec.pk}"
            )
        # SQLite often reports notnull=0 for TEXT PRIMARY KEY columns even though
        # PK implies non-null; treat pk>0 as satisfying notnull when expected.
        effective_nn = bool(actual_nn) or actual_pk > 0
        if effective_nn != spec.notnull:
            raise SchemaMigrationError(
                f"table {table!r} column {col!r} notnull={int(effective_nn)} "
                f"(pragma_nn={actual_nn}, pk={actual_pk}) != expected {int(spec.notnull)}"
            )


def _verify_indexes(
    conn: sqlite3.Connection,
    expected_indexes: dict[str, tuple[str, IndexSpec]],
) -> None:
    for idx_name, (table, spec) in expected_indexes.items():
        # index must exist and belong to the table
        row = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='index' AND name=?",
            (idx_name,),
        ).fetchone()
        if row is None:
            raise SchemaMigrationError(f"missing required index {idx_name!r}")

        # PRAGMA index_list for uniqueness
        listed = {
            r[1]: bool(r[2])  # name -> unique
            for r in conn.execute(f"PRAGMA index_list({table})").fetchall()
        }
        if idx_name not in listed:
            raise SchemaMigrationError(
                f"index {idx_name!r} not listed on table {table!r}"
            )
        if listed[idx_name] != spec.unique:
            raise SchemaMigrationError(
                f"index {idx_name!r} unique={listed[idx_name]} "
                f"!= expected {spec.unique}"
            )
        cols = tuple(
            r[2]
            for r in conn.execute(f"PRAGMA index_info({idx_name})").fetchall()
            if r[2] is not None
        )
        if cols != spec.columns:
            raise SchemaMigrationError(
                f"index {idx_name!r} columns {cols} != expected {spec.columns}"
            )


def _composite_fks_from_pragma(
    conn: sqlite3.Connection, table: str
) -> set[CompositeFK]:
    """Group PRAGMA foreign_key_list rows into composite FK descriptors."""
    rows = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
    # id, seq, table, from, to, on_update, on_delete, match
    groups: dict[int, list[tuple[int, str, str, str]]] = defaultdict(list)
    for r in rows:
        groups[int(r[0])].append((int(r[1]), r[2], r[3], r[4]))
    result: set[CompositeFK] = set()
    for _fid, parts in groups.items():
        parts_sorted = sorted(parts, key=lambda x: x[0])
        ref_table = parts_sorted[0][1]
        pairs = tuple((p[2], p[3]) for p in parts_sorted)
        result.add((ref_table, pairs))
    return result


def _verify_composite_foreign_keys(
    conn: sqlite3.Connection,
    expected_foreign_keys: dict[str, tuple[CompositeFK, ...]],
) -> None:
    for table, expected in expected_foreign_keys.items():
        found = _composite_fks_from_pragma(conn, table)
        expected_set = set(expected)
        missing = expected_set - found
        if missing:
            raise SchemaMigrationError(
                f"table {table!r} missing composite foreign keys {sorted(missing)}"
            )
        # Extra FKs are not allowed (fail closed on unexpected constraints)
        extra = found - expected_set
        if extra:
            raise SchemaMigrationError(
                f"table {table!r} has unexpected composite foreign keys {sorted(extra)}"
            )


def _verify_sql_constraints(conn: sqlite3.Connection) -> None:
    """Spot-check CREATE SQL for CHECK clauses that PRAGMA does not expose fully."""
    for table in ("governance_epochs", "programme_versions", "programme_split_manifests"):
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if row is None or not row[0]:
            raise SchemaMigrationError(f"missing CREATE SQL for {table!r}")
        sql = row[0].upper()
        if table == "governance_epochs":
            if "INCOMPLETE_UNBOUNDED" not in sql:
                raise SchemaMigrationError(
                    f"table {table!r} missing completeness CHECK values"
                )
        if table == "programme_versions":
            if "GLOB" not in sql:
                raise SchemaMigrationError(
                    f"table {table!r} missing SHA-256 CHECK"
                )
            if "PARENT_PROGRAMME_VERSION_ID" not in sql or "PROGRAMME_LINEAGE_ID" not in sql:
                raise SchemaMigrationError(
                    f"table {table!r} missing parent/lineage columns in DDL"
                )
            # Triple parent candidate key must be present
            if "RESEARCH_LINEAGE_ID" not in sql:
                raise SchemaMigrationError(
                    f"table {table!r} missing research_lineage_id in DDL"
                )
        if table == "programme_split_manifests":
            if "GLOB" not in sql:
                raise SchemaMigrationError(
                    f"table {table!r} missing SHA-256 CHECK"
                )


def _verify_triggers(
    conn: sqlite3.Connection,
    *,
    expected_triggers: dict[str, str],
    expected_sql_by_name: dict[str, str],
    protected_tables: tuple[str, ...],
) -> None:
    """Require immutability triggers by **canonical SQL**, not token presence.

    Compares normalized stored CREATE TRIGGER SQL to the exact migration
    statements (event, timing, table, WHEN, RAISE body). Rejects unexpected
    triggers on P1 data tables.
    """
    rows = conn.execute(
        "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger'"
    ).fetchall()
    found = {r[0]: (r[1], r[2] or "") for r in rows}

    for name, expected_table in expected_triggers.items():
        if name not in found:
            raise SchemaMigrationError(f"missing required trigger {name!r}")
        tbl, sql = found[name]
        if tbl != expected_table:
            raise SchemaMigrationError(
                f"trigger {name!r} on table {tbl!r} != expected {expected_table!r}"
            )
        expected_sql = expected_sql_by_name[name]
        actual_sql = _normalize_sql(sql)
        if actual_sql != expected_sql:
            raise SchemaMigrationError(
                f"trigger {name!r} SQL does not match canonical semantics "
                f"(event/timing/WHEN/RAISE body)"
            )

    # No unexpected triggers on P1 data tables
    p1_tables = set(protected_tables)
    for name, (tbl, _sql) in found.items():
        if tbl in p1_tables and name not in expected_triggers:
            raise SchemaMigrationError(
                f"unexpected trigger {name!r} on P1 table {tbl!r}"
            )


def verify_p1_v1_schema(conn: sqlite3.Connection) -> None:
    """Verify complete post-migration v1 schema.

    Checks tables, exact column types/NOT NULL/PK, secondary indexes
    (uniqueness + column order), composite foreign-key grouping, and
    immutability triggers.
    """
    for table in P1_V1_ALL_TABLES:
        _verify_table_columns(conn, table, P1_V1_COLUMNS[table])
    _verify_indexes(conn, P1_V1_INDEXES)
    _verify_composite_foreign_keys(conn, P1_V1_FOREIGN_KEYS)
    _verify_sql_constraints(conn)
    _verify_triggers(
        conn,
        expected_triggers=P1_V1_TRIGGERS,
        expected_sql_by_name=P1_V1_TRIGGER_SQL,
        protected_tables=P1_V1_DATA_TABLES,
    )


def _verify_v2_sql_constraints(conn: sqlite3.Connection) -> None:
    required_tokens = {
        "cohorts": ("DRAFT", "SEALED", "GLOB", "JULIANDAY"),
        "cohort_members": ("ORDINAL >= 0", "GLOB", "JULIANDAY"),
        "holdouts": (
            "AVAILABLE",
            "RESERVED",
            "CONSUMED",
            "ABORTED_BURNED",
            "GLOB",
            "JULIANDAY",
        ),
    }
    for table, tokens in required_tokens.items():
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if row is None or not row[0]:
            raise SchemaMigrationError(f"missing CREATE SQL for {table!r}")
        sql = _normalize_sql(row[0])
        missing = [token for token in tokens if token not in sql]
        if missing:
            raise SchemaMigrationError(
                f"table {table!r} missing required CHECK semantics {missing}"
            )


def verify_p1_v2_schema(conn: sqlite3.Connection) -> None:
    """Verify v1 plus the PR2 cohort and irreversible-holdout foundation."""
    verify_p1_v1_schema(conn)
    for table in P1_V2_DATA_TABLES:
        _verify_table_columns(conn, table, P1_V2_COLUMNS[table])
    _verify_indexes(conn, P1_V2_INDEXES)
    _verify_composite_foreign_keys(conn, P1_V2_FOREIGN_KEYS)
    _verify_v2_sql_constraints(conn)
    _verify_triggers(
        conn,
        expected_triggers=P1_V2_TRIGGERS,
        expected_sql_by_name=P1_V2_TRIGGER_SQL,
        protected_tables=P1_V2_DATA_TABLES,
    )


def _verify_v3_sql_constraints(conn: sqlite3.Connection) -> None:
    required_tokens = {
        "ledger_events": (
            "EVENT_SEQ >= 1",
            "TRIAL_REGISTERED",
            "GLOB",
            "JULIANDAY",
        ),
        "trials": (
            "HYPOTHESIS_EVAL",
            "SENSITIVITY_POINT",
            "COST_STRESS_BASE",
            "COST_STRESS_2X",
            "SELECTION_CAPABLE IN (0, 1)",
            "GLOB",
            "JULIANDAY",
        ),
        "trial_state_events": (
            "REGISTERED",
            "COMPLETED",
            "ABORTED",
            "RESULT_EXPOSED IN (0, 1)",
            "JULIANDAY",
        ),
        "budget_allocations": ("UNITS_ALLOCATED > 0", "JULIANDAY"),
        "budget_debits": ("UNITS_SPENT > 0", "JULIANDAY"),
        "legacy_n_bound_proposals": (
            "UPPER_BOUND_N >= 0",
            "GLOB",
            "JULIANDAY",
        ),
    }
    for table, tokens in required_tokens.items():
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if row is None or not row[0]:
            raise SchemaMigrationError(f"missing CREATE SQL for {table!r}")
        sql = _normalize_sql(row[0])
        missing = [token for token in tokens if token not in sql]
        if missing:
            raise SchemaMigrationError(
                f"table {table!r} missing required CHECK semantics {missing}"
            )
    # Hard fail if agent-writable multiplicity Boolean ever appears.
    for table in P1_V3_DATA_TABLES:
        cols = {
            r[1]
            for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if "counts_for_multiplicity" in cols:
            raise SchemaMigrationError(
                f"table {table!r} must not store counts_for_multiplicity"
            )


def verify_p1_v3_schema(conn: sqlite3.Connection) -> None:
    """Verify v2 plus the PR3 analytical-trial ledger foundation."""
    verify_p1_v2_schema(conn)
    for table in P1_V3_DATA_TABLES:
        _verify_table_columns(conn, table, P1_V3_COLUMNS[table])
    _verify_indexes(conn, P1_V3_INDEXES)
    _verify_composite_foreign_keys(conn, P1_V3_FOREIGN_KEYS)
    _verify_v3_sql_constraints(conn)
    _verify_triggers(
        conn,
        expected_triggers=P1_V3_TRIGGERS,
        expected_sql_by_name=P1_V3_TRIGGER_SQL,
        protected_tables=P1_V3_DATA_TABLES,
    )


def _verify_v4_sql_constraints(conn: sqlite3.Connection) -> None:
    required_tokens = {
        "artifact_digests": (
            "BUNDLE_KIND IN ('RUN', 'COHORT')",
            "IS_CORRECTION IN (0, 1)",
            "SUPERSEDES_ARTIFACT_ID",
            "ARTIFACT_ID",
            "MERKLE_ROOT",
            "GLOB",
            "JULIANDAY",
        ),
        "trial_completion_links": (
            "TRIAL_ID",
            "COMPLETION_EVENT_SEQ",
            "ARTIFACT_ID",
            "RUN_ID",
            "REGISTRATION_EVENT_SEQ",
            "STATE_EVENT_ID",
        ),
        "checkpoints": (
            "CHECKPOINT_EVENT_SEQ = FINAL_EVENT_SEQ + 1",
            "IS_LOCAL_ONLY = 1",
            "IS_AUTHORITATIVE = 0",
            "GLOB",
            "JULIANDAY",
        ),
        "ledger_events": (
            "ARTIFACT_BUNDLE_SEALED",
            "ARTIFACT_BUNDLE_SUPERSESSION",
            "CHECKPOINT_RECORDED",
            "TRIAL_REGISTERED",
        ),
    }
    for table, tokens in required_tokens.items():
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if row is None or not row[0]:
            raise SchemaMigrationError(f"missing CREATE SQL for {table!r}")
        sql = _normalize_sql(row[0])
        missing = [token for token in tokens if token not in sql]
        if missing:
            raise SchemaMigrationError(
                f"table {table!r} missing required CHECK semantics {missing}"
            )


def verify_p1_v4_schema(conn: sqlite3.Connection) -> None:
    """Verify v3 plus PR4 immutable artefact digests and checkpoints.

    v4 may attach additional triggers to v3 tables (e.g. completed-state
    requires exact completion link). Verify v2 structure, then v3 objects,
    then v4 objects with a merged expected-trigger set so those extensions
    are required rather than rejected as unexpected.
    """
    verify_p1_v2_schema(conn)
    for table in P1_V3_DATA_TABLES:
        _verify_table_columns(conn, table, P1_V3_COLUMNS[table])
    _verify_indexes(conn, P1_V3_INDEXES)
    _verify_composite_foreign_keys(conn, P1_V3_FOREIGN_KEYS)
    _verify_v3_sql_constraints(conn)
    for table in P1_V4_DATA_TABLES:
        _verify_table_columns(conn, table, P1_V4_COLUMNS[table])
    _verify_indexes(conn, P1_V4_INDEXES)
    _verify_composite_foreign_keys(conn, P1_V4_FOREIGN_KEYS)
    _verify_v4_sql_constraints(conn)
    merged_triggers = {**P1_V3_TRIGGERS, **P1_V4_TRIGGERS}
    merged_sql = {**P1_V3_TRIGGER_SQL, **P1_V4_TRIGGER_SQL}
    _verify_triggers(
        conn,
        expected_triggers=merged_triggers,
        expected_sql_by_name=merged_sql,
        protected_tables=P1_V3_DATA_TABLES + P1_V4_DATA_TABLES,
    )


def _verify_v5_sql_constraints(conn: sqlite3.Connection) -> None:
    required_tokens = {
        "external_anchors": (
            "UNANCHORED_PENDING",
            "ANCHORED",
            "FINAL_EVENT_SEQ",
            "REGISTRATION_EVENT_SEQ",
            "GLOB",
            "JULIANDAY",
        ),
        "off_machine_backups": (
            "BACKUP_UNVERIFIED",
            "BACKUP_VERIFIED",
            "SNAPSHOT_SHA256",
            "FINAL_EVENT_SEQ",
            "REGISTRATION_EVENT_SEQ",
            "GLOB",
            "JULIANDAY",
        ),
        "ledger_events": (
            "EXTERNAL_ANCHOR_RECORDED",
            "OFF_MACHINE_BACKUP_RECORDED",
            "CHECKPOINT_RECORDED",
            "ARTIFACT_BUNDLE_SEALED",
        ),
    }
    for table, tokens in required_tokens.items():
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if row is None or not row[0]:
            raise SchemaMigrationError(f"missing CREATE SQL for {table!r}")
        sql = _normalize_sql(row[0])
        missing = [token for token in tokens if token not in sql]
        if missing:
            raise SchemaMigrationError(
                f"table {table!r} missing required CHECK semantics {missing}"
            )


def verify_p1_v5_schema(conn: sqlite3.Connection) -> None:
    """Verify v4 plus PR5 external anchor / off-machine backup tables."""
    verify_p1_v4_schema(conn)
    for table in P1_V5_DATA_TABLES:
        _verify_table_columns(conn, table, P1_V5_COLUMNS[table])
    _verify_indexes(conn, P1_V5_INDEXES)
    _verify_composite_foreign_keys(conn, P1_V5_FOREIGN_KEYS)
    _verify_v5_sql_constraints(conn)
    merged_triggers = {**P1_V3_TRIGGERS, **P1_V4_TRIGGERS, **P1_V5_TRIGGERS}
    merged_sql = {
        **P1_V3_TRIGGER_SQL,
        **P1_V4_TRIGGER_SQL,
        **P1_V5_TRIGGER_SQL,
    }
    _verify_triggers(
        conn,
        expected_triggers=merged_triggers,
        expected_sql_by_name=merged_sql,
        protected_tables=P1_V3_DATA_TABLES + P1_V4_DATA_TABLES + P1_V5_DATA_TABLES,
    )


def _detect_conflicting_preexisting_tables(conn: sqlite3.Connection) -> None:
    for name in P1_V1_ALL_TABLES:
        if not _table_exists(conn, name):
            continue
        try:
            _verify_table_columns(conn, name, P1_V1_COLUMNS[name])
        except SchemaMigrationError as exc:
            raise SchemaMigrationError(
                f"conflicting pre-existing table {name!r}: {exc}"
            ) from exc


def migrate_database(
    path: str | Path,
    *,
    target_version: Optional[int] = None,
    component: str = SCHEMA_COMPONENT_P1,
    _inject_failure_before_version: Optional[int] = None,
    _inject_failure_after_statements: Optional[int] = None,
) -> int:
    """Apply forward migrations up to ``target_version`` (default: current).

    Explicit API only. Stamps version only after full schema verification.
    """
    target = CURRENT_P1_SCHEMA_VERSION if target_version is None else int(target_version)
    if target < 0:
        raise UnsupportedSchemaVersionError(f"invalid target_version={target}")
    if target > CURRENT_P1_SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(
            f"unknown newer target schema version {target} "
            f"(max supported {CURRENT_P1_SCHEMA_VERSION})"
        )

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(p))
    conn.isolation_level = None
    conn.row_factory = sqlite3.Row
    try:
        # DDL-only migrations (including v4 ledger_events rebuild) run with
        # foreign_keys OFF so parent-table rebuilds remain transactional.
        # Integrity is enforced via PRAGMA foreign_key_check before stamp.
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("BEGIN IMMEDIATE")
        current = get_schema_version(conn, component=component)
        if current is None:
            current = 0
        if current > CURRENT_P1_SCHEMA_VERSION:
            raise UnsupportedSchemaVersionError(
                f"database has unknown newer schema version {current} "
                f"(max supported {CURRENT_P1_SCHEMA_VERSION}); fail closed"
            )
        if current > target:
            raise UnsupportedSchemaVersionError(
                f"unsupported downgrade from {current} to {target}; fail closed"
            )
        if current == target:
            if target >= 1:
                verify_schema_for_version(conn, target)
                _assert_no_fk_violations(conn)
                _assert_integrity_ok(conn)
            conn.execute("COMMIT")
            return current

        if current == 0 and target >= 1:
            _detect_conflicting_preexisting_tables(conn)
            any_p1 = any(_table_exists(conn, t) for t in P1_V1_DATA_TABLES)
            meta_exists = _table_exists(conn, "crl_schema_meta")
            if any_p1 or meta_exists:
                try:
                    verify_p1_v1_schema(conn)
                except SchemaMigrationError as exc:
                    raise SchemaMigrationError(
                        f"conflicting pre-existing P1 tables (unversioned): {exc}"
                    ) from exc
                _assert_no_fk_violations(conn)
                _assert_integrity_ok(conn)
                _set_schema_version(conn, 1, component=component)
                verify_p1_v1_schema(conn)
                _assert_no_fk_violations(conn)
                _assert_integrity_ok(conn)
                current = 1
                if target == 1:
                    conn.execute("COMMIT")
                    return 1

        by_version = {v: fn for v, fn in MIGRATIONS}
        for v in range(current + 1, target + 1):
            if v not in by_version:
                raise SchemaMigrationError(f"missing migration step for version {v}")
            if (
                _inject_failure_before_version is not None
                and v == _inject_failure_before_version
            ):
                raise SchemaMigrationError(
                    f"injected failure before applying schema version {v}"
                )
            if _inject_failure_after_statements is not None and v == current + 1:
                n = int(_inject_failure_after_statements)
                if n < 1:
                    raise SchemaMigrationError("inject_after_statements must be >= 1")
                statements = MIGRATION_STATEMENTS[v]
                for i, stmt in enumerate(statements):
                    if i >= n:
                        raise SchemaMigrationError(
                            f"injected failure after {n} DDL statement(s) "
                            f"during schema version {v}"
                        )
                    conn.execute(stmt)
                raise SchemaMigrationError(
                    f"injected failure after all statements without version stamp "
                    f"(version {v})"
                )
            by_version[v](conn)
            if v >= 1:
                # Pre-stamp: full verify + FK + integrity on temporary DB
                verify_schema_for_version(conn, v)
                _assert_no_fk_violations(conn)
                _assert_integrity_ok(conn)
                _set_schema_version(conn, v, component=component)
                verify_schema_for_version(conn, v)
                _assert_no_fk_violations(conn)
                _assert_integrity_ok(conn)

        conn.execute("COMMIT")
        return target
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        conn.close()


def derive_completeness(
    *,
    governance_epoch_id: Optional[str],
) -> GovernanceCompleteness:
    """Non-authoritative default completeness for PR1. Never returns COMPLETE."""
    _ = governance_epoch_id
    return GovernanceCompleteness.INCOMPLETE_UNBOUNDED


def legacy_epoch_status_for_null(governance_epoch_id: Optional[str]) -> str:
    return derive_completeness(governance_epoch_id=governance_epoch_id).value


def never_auto_complete(
    governance_epoch_id: Optional[str],
    stored_status: Optional[str] = None,
) -> str:
    _ = stored_status
    return derive_completeness(governance_epoch_id=governance_epoch_id).value
