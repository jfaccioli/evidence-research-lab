"""Ordered P1 schema migration steps.

Migrations are never run on import. Call ``crl.db.schema.migrate_database``
explicitly against a temporary database path.

Note: use ``Connection.execute`` (not ``executescript``) so DDL participates
in the caller's transaction — ``executescript`` issues an implicit COMMIT.

v1 uses CREATE TABLE **without** IF NOT EXISTS so a conflicting pre-existing
table fails the migration transaction rather than being silently retained.

=============================================================================
Parent programme constraint (ChatGPT-resolved policy)
=============================================================================
An ordinary parent programme version must belong to **both**:
  - the same ``programme_lineage_id``; and
  - the same ``research_lineage_id``.

Implemented as::

    UNIQUE (programme_version_id, programme_lineage_id, research_lineage_id)

    FOREIGN KEY (
        parent_programme_version_id,
        programme_lineage_id,
        research_lineage_id
    ) REFERENCES programme_versions (
        programme_version_id,
        programme_lineage_id,
        research_lineage_id
    )

=============================================================================
No cross-research-lineage fork machinery in schema v1
=============================================================================
Cross-research-lineage forks are **not representable** in v1.

This migration does **not** introduce:
  - ``forked_from_programme_version_id``
  - approval / authority records for forks
  - multiplicity-root infrastructure for forked lineages

A future fork requires an **independently reviewed** migration with explicit
provenance, human approval, and inherited multiplicity accounting. Prior
influence must **never** be severed silently.

=============================================================================
Database-level immutability (triggers)
=============================================================================
- ``programme_versions``: reject every UPDATE and DELETE.
- ``programme_split_manifests``: reject every UPDATE and DELETE.
- ``research_lineages``: reject DELETE; reject changes to identity/creation
  fields (``research_lineage_id``, ``created_at``); ``description`` may update.
- ``governance_epochs``: reject DELETE; reject changes to identity-bearing and
  completeness fields (``governance_epoch_id``, ``research_lineage_id``,
  ``completeness``, ``opened_at``). Allowed future lifecycle path only:
  ``lifecycle``, ``closed_at``, ``notes`` (operational close / annotation).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import sqlite3

MigrationFn = Callable[[sqlite3.Connection], None]

_COMPLETENESS_CHECK = (
    "completeness IN ("
    "'COMPLETE',"
    "'INCOMPLETE_KNOWN_GAPS',"
    "'INCOMPLETE_UNBOUNDED',"
    "'LEGACY_RECONSTRUCTED_CONSERVATIVELY'"
    ")"
)

_LIFECYCLE_CHECK = "lifecycle IN ('open', 'closed')"


def _sha256_check(col: str) -> str:
    return (
        f"length({col}) = 64 AND {col} = lower({col}) "
        f"AND {col} GLOB '[0-9a-f]*' "
        f"AND {col} NOT GLOB '*[^0-9a-f]*'"
    )


@dataclass(frozen=True)
class ColumnSpec:
    """Expected column attributes from PRAGMA table_info."""

    type: str  # upper-case affinity token
    notnull: bool
    pk: int  # 0 = not PK; 1+ = PK ordinal


@dataclass(frozen=True)
class IndexSpec:
    unique: bool
    columns: tuple[str, ...]  # left-to-right key order


# Composite FK: (referenced_table, ordered (from_col, to_col) pairs)
CompositeFK = tuple[str, tuple[tuple[str, str], ...]]

P1_V1_DATA_TABLES: tuple[str, ...] = (
    "research_lineages",
    "governance_epochs",
    "programme_versions",
    "programme_split_manifests",
)

P1_V1_ALL_TABLES: tuple[str, ...] = ("crl_schema_meta",) + P1_V1_DATA_TABLES

P1_V1_COLUMNS: dict[str, dict[str, ColumnSpec]] = {
    "crl_schema_meta": {
        "component": ColumnSpec("TEXT", True, 1),
        "version": ColumnSpec("INTEGER", True, 0),
        "applied_at": ColumnSpec("TEXT", True, 0),
    },
    "research_lineages": {
        "research_lineage_id": ColumnSpec("TEXT", True, 1),
        "description": ColumnSpec("TEXT", True, 0),
        "created_at": ColumnSpec("TEXT", True, 0),
    },
    "governance_epochs": {
        "governance_epoch_id": ColumnSpec("TEXT", True, 1),
        "research_lineage_id": ColumnSpec("TEXT", True, 0),
        "completeness": ColumnSpec("TEXT", True, 0),
        "lifecycle": ColumnSpec("TEXT", True, 0),
        "opened_at": ColumnSpec("TEXT", False, 0),
        "closed_at": ColumnSpec("TEXT", False, 0),
        "notes": ColumnSpec("TEXT", True, 0),
    },
    "programme_versions": {
        "programme_version_id": ColumnSpec("TEXT", True, 1),
        "programme_lineage_id": ColumnSpec("TEXT", True, 0),
        "research_lineage_id": ColumnSpec("TEXT", True, 0),
        "governance_epoch_id": ColumnSpec("TEXT", False, 0),
        "parent_programme_version_id": ColumnSpec("TEXT", False, 0),
        "version_reason": ColumnSpec("TEXT", True, 0),
        "prior_results_available_at_creation": ColumnSpec("INTEGER", True, 0),
        "split_manifest_content_hash": ColumnSpec("TEXT", True, 0),
        "created_at": ColumnSpec("TEXT", True, 0),
    },
    "programme_split_manifests": {
        "content_hash": ColumnSpec("TEXT", True, 1),
        "programme_version_id": ColumnSpec("TEXT", True, 0),
        "manifest_json": ColumnSpec("TEXT", True, 0),
        "created_at": ColumnSpec("TEXT", True, 0),
    },
}

P1_V1_INDEXES: dict[str, tuple[str, IndexSpec]] = {
    "idx_gov_epoch_lineage": (
        "governance_epochs",
        IndexSpec(unique=False, columns=("research_lineage_id",)),
    ),
    "idx_prog_ver_lineage": (
        "programme_versions",
        IndexSpec(unique=False, columns=("programme_lineage_id",)),
    ),
}

P1_V1_FOREIGN_KEYS: dict[str, tuple[CompositeFK, ...]] = {
    "governance_epochs": (
        ("research_lineages", (("research_lineage_id", "research_lineage_id"),)),
    ),
    "programme_versions": (
        ("research_lineages", (("research_lineage_id", "research_lineage_id"),)),
        (
            "governance_epochs",
            (
                ("governance_epoch_id", "governance_epoch_id"),
                ("research_lineage_id", "research_lineage_id"),
            ),
        ),
        # Ordinary parent: same programme_lineage_id AND same research_lineage_id.
        (
            "programme_versions",
            (
                ("parent_programme_version_id", "programme_version_id"),
                ("programme_lineage_id", "programme_lineage_id"),
                ("research_lineage_id", "research_lineage_id"),
            ),
        ),
    ),
    "programme_split_manifests": (
        (
            "programme_versions",
            (
                ("programme_version_id", "programme_version_id"),
                ("content_hash", "split_manifest_content_hash"),
            ),
        ),
    ),
}

P1_V1_INDEX_NAMES: tuple[str, ...] = tuple(P1_V1_INDEXES.keys())

_V1_TABLE_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE crl_schema_meta (
        component TEXT PRIMARY KEY,
        version INTEGER NOT NULL,
        applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE research_lineages (
        research_lineage_id TEXT PRIMARY KEY,
        description TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL
    )
    """,
    f"""
    CREATE TABLE governance_epochs (
        governance_epoch_id TEXT PRIMARY KEY,
        research_lineage_id TEXT NOT NULL,
        completeness TEXT NOT NULL,
        lifecycle TEXT NOT NULL DEFAULT 'open',
        opened_at TEXT,
        closed_at TEXT,
        notes TEXT NOT NULL DEFAULT '',
        CHECK ({_COMPLETENESS_CHECK}),
        CHECK ({_LIFECYCLE_CHECK}),
        UNIQUE (governance_epoch_id, research_lineage_id),
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id)
    )
    """,
    f"""
    CREATE TABLE programme_versions (
        programme_version_id TEXT PRIMARY KEY,
        programme_lineage_id TEXT NOT NULL,
        research_lineage_id TEXT NOT NULL,
        governance_epoch_id TEXT,
        parent_programme_version_id TEXT,
        version_reason TEXT NOT NULL,
        prior_results_available_at_creation INTEGER NOT NULL,
        split_manifest_content_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        CHECK (prior_results_available_at_creation IN (0, 1)),
        CHECK ({_sha256_check("split_manifest_content_hash")}),
        UNIQUE (programme_version_id, split_manifest_content_hash),
        UNIQUE (programme_version_id, programme_lineage_id, research_lineage_id),
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id),
        FOREIGN KEY (governance_epoch_id, research_lineage_id)
            REFERENCES governance_epochs(governance_epoch_id, research_lineage_id),
        FOREIGN KEY (
            parent_programme_version_id,
            programme_lineage_id,
            research_lineage_id
        )
            REFERENCES programme_versions (
                programme_version_id,
                programme_lineage_id,
                research_lineage_id
            )
    )
    """,
    f"""
    CREATE TABLE programme_split_manifests (
        content_hash TEXT NOT NULL,
        programme_version_id TEXT NOT NULL,
        manifest_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (content_hash),
        UNIQUE (programme_version_id),
        UNIQUE (programme_version_id, content_hash),
        CHECK ({_sha256_check("content_hash")}),
        FOREIGN KEY (programme_version_id, content_hash)
            REFERENCES programme_versions(programme_version_id, split_manifest_content_hash)
    )
    """,
    """
    CREATE INDEX idx_gov_epoch_lineage
        ON governance_epochs(research_lineage_id)
    """,
    """
    CREATE INDEX idx_prog_ver_lineage
        ON programme_versions(programme_lineage_id)
    """,
)

_V1_TRIGGER_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TRIGGER trg_programme_versions_no_update
    BEFORE UPDATE ON programme_versions
    BEGIN
        SELECT RAISE(ABORT, 'programme_versions is immutable: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_programme_versions_no_delete
    BEFORE DELETE ON programme_versions
    BEGIN
        SELECT RAISE(ABORT, 'programme_versions is immutable: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_programme_split_manifests_no_update
    BEFORE UPDATE ON programme_split_manifests
    BEGIN
        SELECT RAISE(ABORT, 'programme_split_manifests is immutable: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_programme_split_manifests_no_delete
    BEFORE DELETE ON programme_split_manifests
    BEGIN
        SELECT RAISE(ABORT, 'programme_split_manifests is immutable: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_research_lineages_no_delete
    BEFORE DELETE ON research_lineages
    BEGIN
        SELECT RAISE(ABORT, 'research_lineages DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_research_lineages_identity_guard
    BEFORE UPDATE ON research_lineages
    WHEN OLD.research_lineage_id IS NOT NEW.research_lineage_id
      OR OLD.created_at IS NOT NEW.created_at
    BEGIN
        SELECT RAISE(ABORT,
            'research_lineages identity/creation fields are immutable');
    END
    """,
    """
    CREATE TRIGGER trg_governance_epochs_no_delete
    BEFORE DELETE ON governance_epochs
    BEGIN
        SELECT RAISE(ABORT, 'governance_epochs DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_governance_epochs_identity_guard
    BEFORE UPDATE ON governance_epochs
    WHEN OLD.governance_epoch_id IS NOT NEW.governance_epoch_id
      OR OLD.research_lineage_id IS NOT NEW.research_lineage_id
      OR OLD.completeness IS NOT NEW.completeness
      OR OLD.opened_at IS NOT NEW.opened_at
    BEGIN
        SELECT RAISE(ABORT,
            'governance_epochs identity/completeness/opened_at immutable');
    END
    """,
)

# Full ordered DDL for migration step v1 (tables/indexes then triggers).
_V1_STATEMENTS: tuple[str, ...] = _V1_TABLE_STATEMENTS + _V1_TRIGGER_STATEMENTS


def _normalize_sql(sql: str) -> str:
    """Collapse whitespace for exact canonical SQL comparison."""
    import re

    return re.sub(r"\s+", " ", (sql or "").strip()).upper()


def _trigger_name_from_create(sql: str) -> str:
    """Extract trigger name from a CREATE TRIGGER statement."""
    import re

    m = re.search(
        r"CREATE\s+TRIGGER\s+(IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)",
        sql,
        flags=re.IGNORECASE,
    )
    if not m:
        raise ValueError(f"cannot parse trigger name from: {sql[:80]!r}")
    return m.group(2)


# Canonical expected trigger SQL (normalized) keyed by trigger name.
P1_V1_TRIGGER_SQL: dict[str, str] = {
    _trigger_name_from_create(stmt): _normalize_sql(stmt)
    for stmt in _V1_TRIGGER_STATEMENTS
}

# Expected immutability triggers (name -> table) derived from canonical SQL.
P1_V1_TRIGGERS: dict[str, str] = {}
for _name, _norm in P1_V1_TRIGGER_SQL.items():
    # ... ON <table> ...
    import re as _re

    m = _re.search(r"\bON\s+([A-Z_][A-Z0-9_]*)\b", _norm)
    if not m:
        raise RuntimeError(f"cannot parse table for trigger {_name}")
    P1_V1_TRIGGERS[_name] = m.group(1).lower()


def _v1_p1_foundation(conn: sqlite3.Connection) -> None:
    """Create P1 programme / epoch tables and immutability triggers (version 1)."""
    for stmt in _V1_STATEMENTS:
        conn.execute(stmt)


MIGRATIONS: list[tuple[int, MigrationFn]] = [
    (1, _v1_p1_foundation),
]
