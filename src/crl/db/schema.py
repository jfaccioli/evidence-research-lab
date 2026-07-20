"""Explicit, transactional schema versioning for temporary P1 databases.

Hard rules (PR1):
- No migration on import.
- No migration on ordinary HypothesisRegistry construction.
- Migrations only via ``migrate_database`` (or test helpers that call it).
- Opening a legacy DB in compatibility mode must not change its bytes.
- Unknown / newer schema versions fail closed.
- Unsupported downgrade fails closed.
- Repeated migration to the same target is idempotent.
- Legacy rows remain null/legacy and never auto-COMPLETE.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from crl.db.migrations import MIGRATIONS

SCHEMA_COMPONENT_P1 = "p1_programme"
CURRENT_P1_SCHEMA_VERSION = 1  # max version defined in MIGRATIONS

_MAX_DEFINED_VERSION = max(v for v, _ in MIGRATIONS) if MIGRATIONS else 0
if CURRENT_P1_SCHEMA_VERSION != _MAX_DEFINED_VERSION:
    # Developer guard: keep constant in sync with migration chain
    raise RuntimeError(
        f"CURRENT_P1_SCHEMA_VERSION={CURRENT_P1_SCHEMA_VERSION} "
        f"!= max migration version={_MAX_DEFINED_VERSION}"
    )


class SchemaError(Exception):
    """Base schema / version error (fail closed)."""


class SchemaMigrationError(SchemaError):
    """Migration failed; transaction should leave DB unchanged."""


class UnsupportedSchemaVersionError(SchemaError):
    """Downgrade or unknown newer schema — fail closed."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_schema_version(
    conn: sqlite3.Connection,
    *,
    component: str = SCHEMA_COMPONENT_P1,
) -> Optional[int]:
    """Return stored schema version, or None if meta table/row absent (legacy)."""
    try:
        row = conn.execute(
            "SELECT version FROM crl_schema_meta WHERE component = ?",
            (component,),
        ).fetchone()
    except sqlite3.OperationalError:
        # Table does not exist → legacy / unversioned
        return None
    if row is None:
        return None
    return int(row[0])


def read_schema_version_from_path(
    path: str | Path,
    *,
    component: str = SCHEMA_COMPONENT_P1,
) -> Optional[int]:
    """Read version via compatibility open (no writes)."""
    with open_legacy_compatibility(path) as conn:
        return get_schema_version(conn, component=component)


def open_legacy_compatibility(path: str | Path) -> sqlite3.Connection:
    """Open an existing database **without** migrating or writing.

    Uses SQLite immutable/read-only URI so accidental writes fail.
    Does not create the file if missing.
    """
    p = Path(path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"database not found for compatibility open: {p}")
    # mode=ro prevents writes; immutable=1 avoids even journal side-effects on some FS
    uri = p.as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
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


def migrate_database(
    path: str | Path,
    *,
    target_version: Optional[int] = None,
    component: str = SCHEMA_COMPONENT_P1,
    _inject_failure_before_version: Optional[int] = None,
) -> int:
    """Apply forward migrations up to ``target_version`` (default: current).

    Explicit API only — never called from HypothesisRegistry or import side effects.

    - Idempotent when already at target.
    - Transactional: failure rolls back schema and version.
    - Fails closed on unknown newer version or unsupported downgrade.
    - Creates the SQLite file if missing (temp DBs in tests).
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
    # Manual transactions only — isolation_level None disables implicit commits.
    conn.isolation_level = None
    conn.row_factory = sqlite3.Row
    try:
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
            conn.execute("COMMIT")
            return current

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
            by_version[v](conn)
            # Meta table exists after v1 foundation
            if v >= 1:
                _set_schema_version(conn, v, component=component)

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


def legacy_epoch_status_for_null(governance_epoch_id: str | None) -> str:
    """Map null / empty epoch id to explicit legacy label — never COMPLETE."""
    if governance_epoch_id is None or str(governance_epoch_id).strip() == "":
        return "legacy"
    # Non-null id without a COMPLETE reconciliation event is not COMPLETE.
    return "open"


def never_auto_complete(
    governance_epoch_id: str | None,
    stored_status: str | None,
) -> str:
    """Derive display status for rows; null epoch never becomes COMPLETE."""
    if governance_epoch_id is None or str(governance_epoch_id).strip() == "":
        return "legacy"
    if stored_status is None or str(stored_status).strip() == "":
        return "incomplete"
    s = str(stored_status).lower()
    if s == "complete":
        return "complete"
    if s == "legacy":
        return "legacy"
    if s == "open":
        return "open"
    return "incomplete"
