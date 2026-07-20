"""Ordered P1 schema migration steps.

Migrations are never run on import. Call ``crl.db.schema.migrate_database``
explicitly against a temporary database path.

Note: use ``Connection.execute`` (not ``executescript``) so DDL participates
in the caller's transaction — ``executescript`` issues an implicit COMMIT.
"""

from __future__ import annotations

from typing import Callable

import sqlite3

MigrationFn = Callable[[sqlite3.Connection], None]

_V1_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS crl_schema_meta (
        component TEXT PRIMARY KEY,
        version INTEGER NOT NULL,
        applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_lineages (
        research_lineage_id TEXT PRIMARY KEY,
        description TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS governance_epochs (
        governance_epoch_id TEXT PRIMARY KEY,
        research_lineage_id TEXT NOT NULL,
        status TEXT NOT NULL,
        opened_at TEXT,
        closed_at TEXT,
        notes TEXT NOT NULL DEFAULT '',
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS programme_versions (
        programme_version_id TEXT PRIMARY KEY,
        programme_lineage_id TEXT NOT NULL,
        research_lineage_id TEXT NOT NULL,
        governance_epoch_id TEXT,
        parent_programme_version_id TEXT,
        version_reason TEXT NOT NULL,
        prior_results_available_at_creation INTEGER NOT NULL,
        split_manifest_content_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id),
        FOREIGN KEY (governance_epoch_id)
            REFERENCES governance_epochs(governance_epoch_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS programme_split_manifests (
        content_hash TEXT PRIMARY KEY,
        programme_version_id TEXT NOT NULL,
        manifest_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (programme_version_id)
            REFERENCES programme_versions(programme_version_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_gov_epoch_lineage
        ON governance_epochs(research_lineage_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_prog_ver_lineage
        ON programme_versions(programme_lineage_id)
    """,
)


def _v1_p1_foundation(conn: sqlite3.Connection) -> None:
    """Create P1 programme / epoch tables and schema meta (version 1)."""
    for stmt in _V1_STATEMENTS:
        conn.execute(stmt)


# Forward-only chain: version N is applied when upgrading from N-1 → N.
MIGRATIONS: list[tuple[int, MigrationFn]] = [
    (1, _v1_p1_foundation),
]
