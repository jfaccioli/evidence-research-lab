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


def _utc_timestamp_check(col: str) -> str:
    return (
        f"length({col}) = 27 "
        f"AND substr({col}, 5, 1) = '-' "
        f"AND substr({col}, 8, 1) = '-' "
        f"AND substr({col}, 11, 1) = 'T' "
        f"AND substr({col}, 14, 1) = ':' "
        f"AND substr({col}, 17, 1) = ':' "
        f"AND substr({col}, 20, 1) = '.' "
        f"AND substr({col}, 27, 1) = 'Z' "
        f"AND julianday({col}) IS NOT NULL"
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


P1_V2_DATA_TABLES: tuple[str, ...] = (
    "cohorts",
    "cohort_members",
    "holdouts",
)

P1_V2_COLUMNS: dict[str, dict[str, ColumnSpec]] = {
    "cohorts": {
        "cohort_id": ColumnSpec("TEXT", True, 1),
        "programme_version_id": ColumnSpec("TEXT", True, 0),
        "state": ColumnSpec("TEXT", True, 0),
        "protocol_manifest_hash": ColumnSpec("TEXT", True, 0),
        "membership_hash": ColumnSpec("TEXT", False, 0),
        "created_at": ColumnSpec("TEXT", True, 0),
        "sealed_at": ColumnSpec("TEXT", False, 0),
    },
    "cohort_members": {
        "cohort_id": ColumnSpec("TEXT", True, 1),
        "ordinal": ColumnSpec("INTEGER", True, 0),
        "candidate_id": ColumnSpec("TEXT", True, 2),
        "spec_hash": ColumnSpec("TEXT", True, 0),
        "added_at": ColumnSpec("TEXT", True, 0),
    },
    "holdouts": {
        "holdout_id": ColumnSpec("TEXT", True, 1),
        "programme_version_id": ColumnSpec("TEXT", True, 0),
        "state": ColumnSpec("TEXT", True, 0),
        "reserved_cohort_id": ColumnSpec("TEXT", False, 0),
        "reservation_token_hash": ColumnSpec("TEXT", False, 0),
        "created_at": ColumnSpec("TEXT", True, 0),
        "reserved_at": ColumnSpec("TEXT", False, 0),
        "terminal_at": ColumnSpec("TEXT", False, 0),
        "terminal_reason": ColumnSpec("TEXT", False, 0),
    },
}

P1_V2_INDEXES: dict[str, tuple[str, IndexSpec]] = {
    "idx_cohorts_programme": (
        "cohorts",
        IndexSpec(unique=False, columns=("programme_version_id",)),
    ),
    "idx_holdouts_state_reserved": (
        "holdouts",
        IndexSpec(unique=False, columns=("state", "reserved_at")),
    ),
}

P1_V2_FOREIGN_KEYS: dict[str, tuple[CompositeFK, ...]] = {
    "cohorts": (
        (
            "programme_versions",
            (("programme_version_id", "programme_version_id"),),
        ),
    ),
    "cohort_members": (
        ("cohorts", (("cohort_id", "cohort_id"),)),
    ),
    "holdouts": (
        (
            "programme_versions",
            (("programme_version_id", "programme_version_id"),),
        ),
        (
            "cohorts",
            (
                ("reserved_cohort_id", "cohort_id"),
                ("programme_version_id", "programme_version_id"),
            ),
        ),
    ),
}

_V2_TABLE_STATEMENTS: tuple[str, ...] = (
    f"""
    CREATE TABLE cohorts (
        cohort_id TEXT PRIMARY KEY,
        programme_version_id TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'DRAFT',
        protocol_manifest_hash TEXT NOT NULL,
        membership_hash TEXT,
        created_at TEXT NOT NULL,
        sealed_at TEXT,
        CHECK (state IN ('DRAFT', 'SEALED')),
        CHECK (length(trim(cohort_id)) > 0),
        CHECK (length(trim(programme_version_id)) > 0),
        CHECK ({_sha256_check("protocol_manifest_hash")}),
        CHECK ({_utc_timestamp_check("created_at")}),
        CHECK (sealed_at IS NULL OR ({_utc_timestamp_check("sealed_at")})),
        CHECK (sealed_at IS NULL OR sealed_at >= created_at),
        CHECK (
            (
                state = 'DRAFT'
                AND membership_hash IS NULL
                AND sealed_at IS NULL
            )
            OR
            (
                state = 'SEALED'
                AND membership_hash IS NOT NULL
                AND sealed_at IS NOT NULL
            )
        ),
        CHECK (membership_hash IS NULL OR ({_sha256_check("membership_hash")})),
        UNIQUE (cohort_id, programme_version_id),
        FOREIGN KEY (programme_version_id)
            REFERENCES programme_versions(programme_version_id)
    )
    """,
    f"""
    CREATE TABLE cohort_members (
        cohort_id TEXT NOT NULL,
        ordinal INTEGER NOT NULL,
        candidate_id TEXT NOT NULL,
        spec_hash TEXT NOT NULL,
        added_at TEXT NOT NULL,
        PRIMARY KEY (cohort_id, candidate_id),
        UNIQUE (cohort_id, ordinal),
        CHECK (length(trim(cohort_id)) > 0),
        CHECK (length(trim(candidate_id)) > 0),
        CHECK (ordinal >= 0),
        CHECK ({_sha256_check("spec_hash")}),
        CHECK ({_utc_timestamp_check("added_at")}),
        FOREIGN KEY (cohort_id)
            REFERENCES cohorts(cohort_id)
    )
    """,
    f"""
    CREATE TABLE holdouts (
        holdout_id TEXT PRIMARY KEY,
        programme_version_id TEXT NOT NULL,
        state TEXT NOT NULL,
        reserved_cohort_id TEXT,
        reservation_token_hash TEXT,
        created_at TEXT NOT NULL,
        reserved_at TEXT,
        terminal_at TEXT,
        terminal_reason TEXT,
        CHECK (
            state IN (
                'AVAILABLE',
                'RESERVED',
                'CONSUMED',
                'ABORTED_BURNED'
            )
        ),
        CHECK (length(trim(holdout_id)) > 0),
        CHECK (length(trim(programme_version_id)) > 0),
        CHECK ({_utc_timestamp_check("created_at")}),
        CHECK (reserved_at IS NULL OR ({_utc_timestamp_check("reserved_at")})),
        CHECK (terminal_at IS NULL OR ({_utc_timestamp_check("terminal_at")})),
        CHECK (reserved_at IS NULL OR reserved_at >= created_at),
        CHECK (terminal_at IS NULL OR terminal_at >= reserved_at),
        CHECK (
            reservation_token_hash IS NULL
            OR ({_sha256_check("reservation_token_hash")})
        ),
        CHECK (
            (
                state = 'AVAILABLE'
                AND reserved_cohort_id IS NULL
                AND reservation_token_hash IS NULL
                AND reserved_at IS NULL
                AND terminal_at IS NULL
                AND terminal_reason IS NULL
            )
            OR
            (
                state = 'RESERVED'
                AND reserved_cohort_id IS NOT NULL
                AND reservation_token_hash IS NOT NULL
                AND reserved_at IS NOT NULL
                AND terminal_at IS NULL
                AND terminal_reason IS NULL
            )
            OR
            (
                state IN ('CONSUMED', 'ABORTED_BURNED')
                AND reserved_cohort_id IS NOT NULL
                AND reservation_token_hash IS NOT NULL
                AND reserved_at IS NOT NULL
                AND terminal_at IS NOT NULL
                AND terminal_reason IS NOT NULL
                AND length(terminal_reason) > 0
            )
        ),
        UNIQUE (programme_version_id),
        UNIQUE (holdout_id, programme_version_id),
        FOREIGN KEY (programme_version_id)
            REFERENCES programme_versions(programme_version_id),
        FOREIGN KEY (reserved_cohort_id, programme_version_id)
            REFERENCES cohorts(cohort_id, programme_version_id)
    )
    """,
    """
    CREATE INDEX idx_cohorts_programme
        ON cohorts(programme_version_id)
    """,
    """
    CREATE INDEX idx_holdouts_state_reserved
        ON holdouts(state, reserved_at)
    """,
)

_V2_TRIGGER_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TRIGGER trg_cohorts_insert_draft_only
    BEFORE INSERT ON cohorts
    WHEN NEW.state <> 'DRAFT'
      OR NEW.membership_hash IS NOT NULL
      OR NEW.sealed_at IS NOT NULL
    BEGIN
        SELECT RAISE(ABORT, 'cohorts must be inserted as DRAFT');
    END
    """,
    """
    CREATE TRIGGER trg_cohorts_seal_only
    BEFORE UPDATE ON cohorts
    WHEN NOT (
        OLD.state = 'DRAFT'
        AND NEW.state = 'SEALED'
        AND OLD.cohort_id IS NEW.cohort_id
        AND OLD.programme_version_id IS NEW.programme_version_id
        AND OLD.protocol_manifest_hash IS NEW.protocol_manifest_hash
        AND OLD.created_at IS NEW.created_at
        AND OLD.membership_hash IS NULL
        AND NEW.membership_hash IS NOT NULL
        AND OLD.sealed_at IS NULL
        AND NEW.sealed_at IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM cohort_members
            WHERE cohort_id = OLD.cohort_id
        )
    )
    BEGIN
        SELECT RAISE(ABORT, 'cohorts permit only DRAFT to SEALED transition');
    END
    """,
    """
    CREATE TRIGGER trg_cohorts_no_delete
    BEFORE DELETE ON cohorts
    BEGIN
        SELECT RAISE(ABORT, 'cohorts DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_cohort_members_draft_insert_only
    BEFORE INSERT ON cohort_members
    WHEN COALESCE(
        (SELECT state FROM cohorts WHERE cohort_id = NEW.cohort_id),
        ''
    ) <> 'DRAFT'
      OR NEW.added_at < COALESCE(
          (SELECT created_at FROM cohorts WHERE cohort_id = NEW.cohort_id),
          '9999-12-31T23:59:59.999999Z'
      )
    BEGIN
        SELECT RAISE(ABORT, 'cohort members may be appended only while DRAFT');
    END
    """,
    """
    CREATE TRIGGER trg_cohort_members_no_update
    BEFORE UPDATE ON cohort_members
    BEGIN
        SELECT RAISE(ABORT, 'cohort_members UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_cohort_members_no_delete
    BEFORE DELETE ON cohort_members
    BEGIN
        SELECT RAISE(ABORT, 'cohort_members DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_holdouts_insert_available_only
    BEFORE INSERT ON holdouts
    WHEN NEW.state <> 'AVAILABLE'
      OR NEW.reserved_cohort_id IS NOT NULL
      OR NEW.reservation_token_hash IS NOT NULL
      OR NEW.reserved_at IS NOT NULL
      OR NEW.terminal_at IS NOT NULL
      OR NEW.terminal_reason IS NOT NULL
    BEGIN
        SELECT RAISE(ABORT, 'holdouts must be inserted as AVAILABLE');
    END
    """,
    """
    CREATE TRIGGER trg_holdouts_irreversible_transition
    BEFORE UPDATE ON holdouts
    WHEN NOT (
        (
            OLD.state = 'AVAILABLE'
            AND NEW.state = 'RESERVED'
            AND OLD.holdout_id IS NEW.holdout_id
            AND OLD.programme_version_id IS NEW.programme_version_id
            AND OLD.created_at IS NEW.created_at
            AND OLD.reserved_cohort_id IS NULL
            AND NEW.reserved_cohort_id IS NOT NULL
            AND OLD.reservation_token_hash IS NULL
            AND NEW.reservation_token_hash IS NOT NULL
            AND OLD.reserved_at IS NULL
            AND NEW.reserved_at IS NOT NULL
            AND OLD.terminal_at IS NULL
            AND NEW.terminal_at IS NULL
            AND OLD.terminal_reason IS NULL
            AND NEW.terminal_reason IS NULL
            AND COALESCE(
                (
                    SELECT state
                    FROM cohorts
                    WHERE cohort_id = NEW.reserved_cohort_id
                ),
                ''
            ) = 'SEALED'
        )
        OR
        (
            OLD.state = 'RESERVED'
            AND NEW.state IN ('CONSUMED', 'ABORTED_BURNED')
            AND OLD.holdout_id IS NEW.holdout_id
            AND OLD.programme_version_id IS NEW.programme_version_id
            AND OLD.created_at IS NEW.created_at
            AND OLD.reserved_cohort_id IS NEW.reserved_cohort_id
            AND OLD.reservation_token_hash IS NEW.reservation_token_hash
            AND OLD.reserved_at IS NEW.reserved_at
            AND OLD.terminal_at IS NULL
            AND NEW.terminal_at IS NOT NULL
            AND OLD.terminal_reason IS NULL
            AND NEW.terminal_reason IS NOT NULL
            AND length(NEW.terminal_reason) > 0
        )
    )
    BEGIN
        SELECT RAISE(ABORT, 'invalid or reversible holdout transition');
    END
    """,
    """
    CREATE TRIGGER trg_holdouts_no_delete
    BEFORE DELETE ON holdouts
    BEGIN
        SELECT RAISE(ABORT, 'holdouts DELETE forbidden');
    END
    """,
)

_V2_STATEMENTS: tuple[str, ...] = _V2_TABLE_STATEMENTS + _V2_TRIGGER_STATEMENTS

P1_V2_TRIGGER_SQL: dict[str, str] = {
    _trigger_name_from_create(stmt): _normalize_sql(stmt)
    for stmt in _V2_TRIGGER_STATEMENTS
}

P1_V2_TRIGGERS: dict[str, str] = {}
for _name, _norm in P1_V2_TRIGGER_SQL.items():
    import re as _re

    _match = _re.search(r"\bON\s+([A-Z_][A-Z0-9_]*)\b", _norm)
    if not _match:
        raise RuntimeError(f"cannot parse table for trigger {_name}")
    P1_V2_TRIGGERS[_name] = _match.group(1).lower()


def _v2_holdout_foundation(conn: sqlite3.Connection) -> None:
    """Create cohort and irreversible holdout state-machine schema."""
    for stmt in _V2_STATEMENTS:
        conn.execute(stmt)


# =============================================================================
# v3 — analytical-trial ledger, budget atomicity, proposed (non-approved) legacy N
# =============================================================================
# Append-only factual store. Multiplicity counts are policy-derived in code and
# are never stored as an agent-writable ``counts_for_multiplicity`` Boolean.
# Completeness remains reconciliation-derived (PR3 never mints promotable
# COMPLETE: PR4 artifact/checkpoint invariants are explicit gaps).
# Legacy N bounds are proposal-only; a caller digest is never verified human
# approval and never authorises N_global / completeness unblocking.

P1_V3_DATA_TABLES: tuple[str, ...] = (
    "ledger_events",
    "trials",
    "trial_state_events",
    "budget_allocations",
    "budget_debits",
    "legacy_n_bound_proposals",
)

_TRIAL_KIND_CHECK = (
    "trial_kind IN ("
    "'hypothesis_eval',"
    "'sensitivity_point',"
    "'parameter_variant',"
    "'feature_variant',"
    "'threshold_variant',"
    "'horizon_variant',"
    "'interaction_variant',"
    "'aggregation_variant',"
    "'reproduction',"
    "'synthetic_fixture',"
    "'benchmark_bh',"
    "'cost_stress_base',"
    "'cost_stress_2x',"
    "'aborted_eval',"
    "'citation',"
    "'changed_input_rerun'"
    ")"
)

_EXECUTION_STATE_CHECK = (
    "execution_state IN ("
    "'registered',"
    "'running',"
    "'completed',"
    "'aborted',"
    "'error'"
    ")"
)

_EVENT_TYPE_CHECK = (
    "event_type IN ("
    "'trial_registered',"
    "'trial_state_transition',"
    "'budget_allocated',"
    "'legacy_n_bound_proposed'"
    ")"
)

P1_V3_COLUMNS: dict[str, dict[str, ColumnSpec]] = {
    "ledger_events": {
        "event_seq": ColumnSpec("INTEGER", True, 1),
        "event_type": ColumnSpec("TEXT", True, 0),
        "payload_json": ColumnSpec("TEXT", True, 0),
        "prev_event_hash": ColumnSpec("TEXT", True, 0),
        "event_hash": ColumnSpec("TEXT", True, 0),
        "recorded_at": ColumnSpec("TEXT", True, 0),
    },
    "trials": {
        "trial_id": ColumnSpec("TEXT", True, 1),
        "registration_event_seq": ColumnSpec("INTEGER", True, 0),
        "research_lineage_id": ColumnSpec("TEXT", True, 0),
        "programme_version_id": ColumnSpec("TEXT", True, 0),
        "cohort_id": ColumnSpec("TEXT", False, 0),
        "trial_kind": ColumnSpec("TEXT", True, 0),
        "selection_capable": ColumnSpec("INTEGER", True, 0),
        "synthetic": ColumnSpec("INTEGER", True, 0),
        "immutable_input_hash": ColumnSpec("TEXT", True, 0),
        "result_exposed": ColumnSpec("INTEGER", True, 0),
        "preregistered": ColumnSpec("INTEGER", True, 0),
        "selection_unit_id": ColumnSpec("TEXT", True, 0),
        "is_citation": ColumnSpec("INTEGER", True, 0),
        "reproduction_of_trial_id": ColumnSpec("TEXT", False, 0),
        # System-derived from the referenced trial's stored immutable_input_hash.
        "reproduction_input_hash": ColumnSpec("TEXT", False, 0),
        # System-derived: equal stored hashes only (never caller-authoritative).
        "reproduction_byte_identical": ColumnSpec("INTEGER", False, 0),
        "billable": ColumnSpec("INTEGER", True, 0),
        "units_cost": ColumnSpec("INTEGER", True, 0),
        "registered_at": ColumnSpec("TEXT", True, 0),
    },
    "trial_state_events": {
        "state_event_id": ColumnSpec("TEXT", True, 1),
        "trial_id": ColumnSpec("TEXT", True, 0),
        "event_seq": ColumnSpec("INTEGER", True, 0),
        "execution_state": ColumnSpec("TEXT", True, 0),
        "result_exposed": ColumnSpec("INTEGER", True, 0),
        "recorded_at": ColumnSpec("TEXT", True, 0),
        "notes": ColumnSpec("TEXT", True, 0),
    },
    "budget_allocations": {
        "allocation_id": ColumnSpec("TEXT", True, 1),
        "research_lineage_id": ColumnSpec("TEXT", True, 0),
        "units_allocated": ColumnSpec("INTEGER", True, 0),
        "allocation_event_seq": ColumnSpec("INTEGER", True, 0),
        "allocated_at": ColumnSpec("TEXT", True, 0),
        "approval_note": ColumnSpec("TEXT", True, 0),
    },
    "budget_debits": {
        "debit_id": ColumnSpec("TEXT", True, 1),
        "allocation_id": ColumnSpec("TEXT", True, 0),
        "trial_id": ColumnSpec("TEXT", True, 0),
        "event_seq": ColumnSpec("INTEGER", True, 0),
        "units_spent": ColumnSpec("INTEGER", True, 0),
        "debited_at": ColumnSpec("TEXT", True, 0),
    },
    "legacy_n_bound_proposals": {
        "proposal_id": ColumnSpec("TEXT", True, 1),
        "research_lineage_id": ColumnSpec("TEXT", True, 0),
        "upper_bound_n": ColumnSpec("INTEGER", True, 0),
        "proposal_event_seq": ColumnSpec("INTEGER", True, 0),
        "proposed_at": ColumnSpec("TEXT", True, 0),
        "supporting_artefact_hash": ColumnSpec("TEXT", True, 0),
        "notes": ColumnSpec("TEXT", True, 0),
    },
}

P1_V3_INDEXES: dict[str, tuple[str, IndexSpec]] = {
    "idx_ledger_events_hash": (
        "ledger_events",
        IndexSpec(unique=True, columns=("event_hash",)),
    ),
    "idx_trials_lineage": (
        "trials",
        IndexSpec(unique=False, columns=("research_lineage_id",)),
    ),
    "idx_trials_cohort": (
        "trials",
        IndexSpec(unique=False, columns=("cohort_id",)),
    ),
    "idx_trials_selection_unit": (
        "trials",
        IndexSpec(unique=False, columns=("selection_unit_id",)),
    ),
    "idx_trial_state_trial": (
        "trial_state_events",
        IndexSpec(unique=False, columns=("trial_id", "event_seq")),
    ),
    "idx_budget_debits_allocation": (
        "budget_debits",
        IndexSpec(unique=False, columns=("allocation_id",)),
    ),
    "idx_legacy_n_bound_proposals_lineage": (
        "legacy_n_bound_proposals",
        IndexSpec(unique=True, columns=("research_lineage_id",)),
    ),
}

P1_V3_FOREIGN_KEYS: dict[str, tuple[CompositeFK, ...]] = {
    "trials": (
        ("ledger_events", (("registration_event_seq", "event_seq"),)),
        ("research_lineages", (("research_lineage_id", "research_lineage_id"),)),
        (
            "programme_versions",
            (("programme_version_id", "programme_version_id"),),
        ),
        (
            "cohorts",
            (
                ("cohort_id", "cohort_id"),
                ("programme_version_id", "programme_version_id"),
            ),
        ),
        ("trials", (("reproduction_of_trial_id", "trial_id"),)),
    ),
    "trial_state_events": (
        ("trials", (("trial_id", "trial_id"),)),
        ("ledger_events", (("event_seq", "event_seq"),)),
    ),
    "budget_allocations": (
        ("research_lineages", (("research_lineage_id", "research_lineage_id"),)),
        ("ledger_events", (("allocation_event_seq", "event_seq"),)),
    ),
    "budget_debits": (
        ("budget_allocations", (("allocation_id", "allocation_id"),)),
        ("trials", (("trial_id", "trial_id"),)),
        ("ledger_events", (("event_seq", "event_seq"),)),
    ),
    "legacy_n_bound_proposals": (
        ("research_lineages", (("research_lineage_id", "research_lineage_id"),)),
        ("ledger_events", (("proposal_event_seq", "event_seq"),)),
    ),
}

_V3_TABLE_STATEMENTS: tuple[str, ...] = (
    f"""
    CREATE TABLE ledger_events (
        event_seq INTEGER PRIMARY KEY,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        prev_event_hash TEXT NOT NULL,
        event_hash TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        CHECK (event_seq >= 1),
        CHECK ({_EVENT_TYPE_CHECK}),
        CHECK (length(trim(payload_json)) > 0),
        CHECK ({_sha256_check("prev_event_hash")}),
        CHECK ({_sha256_check("event_hash")}),
        CHECK ({_utc_timestamp_check("recorded_at")})
    )
    """,
    f"""
    CREATE TABLE trials (
        trial_id TEXT PRIMARY KEY,
        registration_event_seq INTEGER NOT NULL,
        research_lineage_id TEXT NOT NULL,
        programme_version_id TEXT NOT NULL,
        cohort_id TEXT,
        trial_kind TEXT NOT NULL,
        selection_capable INTEGER NOT NULL,
        synthetic INTEGER NOT NULL,
        immutable_input_hash TEXT NOT NULL,
        result_exposed INTEGER NOT NULL,
        preregistered INTEGER NOT NULL,
        selection_unit_id TEXT NOT NULL,
        is_citation INTEGER NOT NULL,
        reproduction_of_trial_id TEXT,
        reproduction_input_hash TEXT,
        reproduction_byte_identical INTEGER,
        billable INTEGER NOT NULL,
        units_cost INTEGER NOT NULL,
        registered_at TEXT NOT NULL,
        CHECK (length(trim(trial_id)) > 0),
        CHECK (length(trim(research_lineage_id)) > 0),
        CHECK (length(trim(programme_version_id)) > 0),
        CHECK (length(trim(selection_unit_id)) > 0),
        CHECK ({_TRIAL_KIND_CHECK}),
        CHECK (selection_capable IN (0, 1)),
        CHECK (synthetic IN (0, 1)),
        CHECK (result_exposed IN (0, 1)),
        CHECK (preregistered IN (0, 1)),
        CHECK (is_citation IN (0, 1)),
        CHECK (billable IN (0, 1)),
        CHECK (units_cost >= 0),
        CHECK (
            reproduction_byte_identical IS NULL
            OR reproduction_byte_identical IN (0, 1)
        ),
        CHECK ({_sha256_check("immutable_input_hash")}),
        CHECK (
            reproduction_input_hash IS NULL
            OR ({_sha256_check("reproduction_input_hash")})
        ),
        CHECK ({_utc_timestamp_check("registered_at")}),
        CHECK (
            (
                trial_kind <> 'reproduction'
                AND reproduction_of_trial_id IS NULL
                AND reproduction_input_hash IS NULL
                AND reproduction_byte_identical IS NULL
            )
            OR
            (
                trial_kind = 'reproduction'
                AND reproduction_of_trial_id IS NOT NULL
                AND reproduction_input_hash IS NOT NULL
                AND reproduction_byte_identical IS NOT NULL
            )
        ),
        UNIQUE (registration_event_seq),
        FOREIGN KEY (registration_event_seq)
            REFERENCES ledger_events(event_seq),
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id),
        FOREIGN KEY (programme_version_id)
            REFERENCES programme_versions(programme_version_id),
        FOREIGN KEY (cohort_id, programme_version_id)
            REFERENCES cohorts(cohort_id, programme_version_id),
        FOREIGN KEY (reproduction_of_trial_id)
            REFERENCES trials(trial_id)
    )
    """,
    f"""
    CREATE TABLE trial_state_events (
        state_event_id TEXT PRIMARY KEY,
        trial_id TEXT NOT NULL,
        event_seq INTEGER NOT NULL,
        execution_state TEXT NOT NULL,
        result_exposed INTEGER NOT NULL,
        recorded_at TEXT NOT NULL,
        notes TEXT NOT NULL DEFAULT '',
        CHECK (length(trim(state_event_id)) > 0),
        CHECK (length(trim(trial_id)) > 0),
        CHECK ({_EXECUTION_STATE_CHECK}),
        CHECK (result_exposed IN (0, 1)),
        CHECK ({_utc_timestamp_check("recorded_at")}),
        UNIQUE (event_seq),
        FOREIGN KEY (trial_id)
            REFERENCES trials(trial_id),
        FOREIGN KEY (event_seq)
            REFERENCES ledger_events(event_seq)
    )
    """,
    f"""
    CREATE TABLE budget_allocations (
        allocation_id TEXT PRIMARY KEY,
        research_lineage_id TEXT NOT NULL,
        units_allocated INTEGER NOT NULL,
        allocation_event_seq INTEGER NOT NULL,
        allocated_at TEXT NOT NULL,
        approval_note TEXT NOT NULL DEFAULT '',
        CHECK (length(trim(allocation_id)) > 0),
        CHECK (length(trim(research_lineage_id)) > 0),
        CHECK (units_allocated > 0),
        CHECK ({_utc_timestamp_check("allocated_at")}),
        UNIQUE (allocation_event_seq),
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id),
        FOREIGN KEY (allocation_event_seq)
            REFERENCES ledger_events(event_seq)
    )
    """,
    f"""
    CREATE TABLE budget_debits (
        debit_id TEXT PRIMARY KEY,
        allocation_id TEXT NOT NULL,
        trial_id TEXT NOT NULL,
        event_seq INTEGER NOT NULL,
        units_spent INTEGER NOT NULL,
        debited_at TEXT NOT NULL,
        CHECK (length(trim(debit_id)) > 0),
        CHECK (length(trim(allocation_id)) > 0),
        CHECK (length(trim(trial_id)) > 0),
        CHECK (units_spent > 0),
        CHECK ({_utc_timestamp_check("debited_at")}),
        UNIQUE (trial_id),
        UNIQUE (event_seq),
        FOREIGN KEY (allocation_id)
            REFERENCES budget_allocations(allocation_id),
        FOREIGN KEY (trial_id)
            REFERENCES trials(trial_id),
        FOREIGN KEY (event_seq)
            REFERENCES ledger_events(event_seq)
    )
    """,
    f"""
    CREATE TABLE legacy_n_bound_proposals (
        proposal_id TEXT PRIMARY KEY,
        research_lineage_id TEXT NOT NULL,
        upper_bound_n INTEGER NOT NULL,
        proposal_event_seq INTEGER NOT NULL,
        proposed_at TEXT NOT NULL,
        supporting_artefact_hash TEXT NOT NULL,
        notes TEXT NOT NULL DEFAULT '',
        CHECK (length(trim(proposal_id)) > 0),
        CHECK (length(trim(research_lineage_id)) > 0),
        CHECK (upper_bound_n >= 0),
        CHECK ({_sha256_check("supporting_artefact_hash")}),
        CHECK ({_utc_timestamp_check("proposed_at")}),
        UNIQUE (proposal_event_seq),
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id),
        FOREIGN KEY (proposal_event_seq)
            REFERENCES ledger_events(event_seq)
    )
    """,
    """
    CREATE UNIQUE INDEX idx_ledger_events_hash
        ON ledger_events(event_hash)
    """,
    """
    CREATE INDEX idx_trials_lineage
        ON trials(research_lineage_id)
    """,
    """
    CREATE INDEX idx_trials_cohort
        ON trials(cohort_id)
    """,
    """
    CREATE INDEX idx_trials_selection_unit
        ON trials(selection_unit_id)
    """,
    """
    CREATE INDEX idx_trial_state_trial
        ON trial_state_events(trial_id, event_seq)
    """,
    """
    CREATE INDEX idx_budget_debits_allocation
        ON budget_debits(allocation_id)
    """,
    """
    CREATE UNIQUE INDEX idx_legacy_n_bound_proposals_lineage
        ON legacy_n_bound_proposals(research_lineage_id)
    """,
)

_V3_TRIGGER_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TRIGGER trg_ledger_events_no_update
    BEFORE UPDATE ON ledger_events
    BEGIN
        SELECT RAISE(ABORT, 'ledger_events is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_ledger_events_no_delete
    BEFORE DELETE ON ledger_events
    BEGIN
        SELECT RAISE(ABORT, 'ledger_events is append-only: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_ledger_events_contiguous_insert
    BEFORE INSERT ON ledger_events
    WHEN NEW.event_seq <> (
        SELECT COALESCE(MAX(event_seq), 0) + 1 FROM ledger_events
    )
    BEGIN
        SELECT RAISE(ABORT, 'ledger_events.event_seq must be contiguous');
    END
    """,
    """
    CREATE TRIGGER trg_trials_no_update
    BEFORE UPDATE ON trials
    BEGIN
        SELECT RAISE(ABORT, 'trials is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_trials_no_delete
    BEFORE DELETE ON trials
    BEGIN
        SELECT RAISE(ABORT, 'trials is append-only: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_trials_programme_research_lineage_match
    BEFORE INSERT ON trials
    WHEN NOT EXISTS (
        SELECT 1
        FROM programme_versions p
        WHERE p.programme_version_id = NEW.programme_version_id
          AND p.research_lineage_id = NEW.research_lineage_id
    )
    BEGIN
        SELECT RAISE(
            ABORT,
            'trial programme_version_id/research_lineage_id mismatch'
        );
    END
    """,
    """
    CREATE TRIGGER trg_trial_state_events_no_update
    BEFORE UPDATE ON trial_state_events
    BEGIN
        SELECT RAISE(ABORT, 'trial_state_events is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_trial_state_events_no_delete
    BEFORE DELETE ON trial_state_events
    BEGIN
        SELECT RAISE(ABORT, 'trial_state_events is append-only: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_budget_allocations_no_update
    BEFORE UPDATE ON budget_allocations
    BEGIN
        SELECT RAISE(ABORT, 'budget_allocations is immutable: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_budget_allocations_no_delete
    BEFORE DELETE ON budget_allocations
    BEGIN
        SELECT RAISE(ABORT, 'budget_allocations is immutable: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_budget_debits_no_update
    BEFORE UPDATE ON budget_debits
    BEGIN
        SELECT RAISE(ABORT, 'budget_debits is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_budget_debits_no_delete
    BEFORE DELETE ON budget_debits
    BEGIN
        SELECT RAISE(ABORT, 'budget_debits is append-only: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_budget_debits_research_lineage_match
    BEFORE INSERT ON budget_debits
    WHEN (
        SELECT research_lineage_id
        FROM budget_allocations
        WHERE allocation_id = NEW.allocation_id
    ) IS NOT (
        SELECT research_lineage_id
        FROM trials
        WHERE trial_id = NEW.trial_id
    )
    BEGIN
        SELECT RAISE(
            ABORT,
            'budget allocation/trial research_lineage_id mismatch'
        );
    END
    """,
    """
    CREATE TRIGGER trg_legacy_n_bound_proposals_no_update
    BEFORE UPDATE ON legacy_n_bound_proposals
    BEGIN
        SELECT RAISE(ABORT, 'legacy_n_bound_proposals is immutable: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_legacy_n_bound_proposals_no_delete
    BEFORE DELETE ON legacy_n_bound_proposals
    BEGIN
        SELECT RAISE(ABORT, 'legacy_n_bound_proposals is immutable: DELETE forbidden');
    END
    """,
)

_V3_STATEMENTS: tuple[str, ...] = _V3_TABLE_STATEMENTS + _V3_TRIGGER_STATEMENTS

P1_V3_TRIGGER_SQL: dict[str, str] = {
    _trigger_name_from_create(stmt): _normalize_sql(stmt)
    for stmt in _V3_TRIGGER_STATEMENTS
}

P1_V3_TRIGGERS: dict[str, str] = {}
for _name, _norm in P1_V3_TRIGGER_SQL.items():
    import re as _re

    _match = _re.search(r"\bON\s+([A-Z_][A-Z0-9_]*)\b", _norm)
    if not _match:
        raise RuntimeError(f"cannot parse table for trigger {_name}")
    P1_V3_TRIGGERS[_name] = _match.group(1).lower()


def _v3_trial_ledger_foundation(conn: sqlite3.Connection) -> None:
    """Create append-only analytical-trial ledger and budget schema."""
    for stmt in _V3_STATEMENTS:
        conn.execute(stmt)


# =============================================================================
# v4 — immutable artefact bundles, consistent snapshots, post-event checkpoints
# =============================================================================
# Clean PR4 v4 (uncommitted redesign): distinct artifact_id identity, non-unique
# content merkle_root, exact completion-to-artefact links, composite cohort
# lineage binding, append-only digests/checkpoints. Local checkpoints remain
# non-authoritative (is_authoritative=0). No PR5 authority.

_EVENT_TYPE_CHECK_V4 = (
    "event_type IN ("
    "'trial_registered',"
    "'trial_state_transition',"
    "'budget_allocated',"
    "'legacy_n_bound_proposed',"
    "'artifact_bundle_sealed',"
    "'artifact_bundle_supersession',"
    "'checkpoint_recorded'"
    ")"
)

_BUNDLE_KIND_CHECK = "bundle_kind IN ('run', 'cohort')"

P1_V4_DATA_TABLES: tuple[str, ...] = (
    "artifact_digests",
    "trial_completion_links",
    "checkpoints",
)

P1_V4_COLUMNS: dict[str, dict[str, ColumnSpec]] = {
    "artifact_digests": {
        "artifact_id": ColumnSpec("TEXT", True, 1),
        "merkle_root": ColumnSpec("TEXT", True, 0),
        "bundle_kind": ColumnSpec("TEXT", True, 0),
        "run_id": ColumnSpec("TEXT", False, 0),
        "cohort_id": ColumnSpec("TEXT", False, 0),
        "trial_id": ColumnSpec("TEXT", False, 0),
        "research_lineage_id": ColumnSpec("TEXT", True, 0),
        "programme_version_id": ColumnSpec("TEXT", True, 0),
        "manifest_sha256": ColumnSpec("TEXT", True, 0),
        "config_hash": ColumnSpec("TEXT", True, 0),
        "candidate_spec_hash": ColumnSpec("TEXT", True, 0),
        "split_manifest_hash": ColumnSpec("TEXT", True, 0),
        "data_hash": ColumnSpec("TEXT", True, 0),
        "feature_hash": ColumnSpec("TEXT", True, 0),
        "dependency_lock_hash": ColumnSpec("TEXT", True, 0),
        "relative_root": ColumnSpec("TEXT", True, 0),
        "byte_size": ColumnSpec("INTEGER", True, 0),
        "registration_event_seq": ColumnSpec("INTEGER", True, 0),
        "supersedes_artifact_id": ColumnSpec("TEXT", False, 0),
        "is_correction": ColumnSpec("INTEGER", True, 0),
        "sealed_at": ColumnSpec("TEXT", True, 0),
    },
    "trial_completion_links": {
        "trial_id": ColumnSpec("TEXT", True, 1),
        "completion_event_seq": ColumnSpec("INTEGER", True, 0),
        "artifact_id": ColumnSpec("TEXT", True, 0),
        "run_id": ColumnSpec("TEXT", True, 0),
        "registration_event_seq": ColumnSpec("INTEGER", True, 0),
        "state_event_id": ColumnSpec("TEXT", True, 0),
    },
    "checkpoints": {
        "checkpoint_id": ColumnSpec("TEXT", True, 1),
        "checkpoint_event_seq": ColumnSpec("INTEGER", True, 0),
        "final_event_seq": ColumnSpec("INTEGER", True, 0),
        "final_event_hash": ColumnSpec("TEXT", True, 0),
        "database_snapshot_hash": ColumnSpec("TEXT", True, 0),
        "artifact_aggregate_merkle_root": ColumnSpec("TEXT", True, 0),
        "snapshot_byte_size": ColumnSpec("INTEGER", True, 0),
        "snapshot_relative_path": ColumnSpec("TEXT", True, 0),
        "recorded_at": ColumnSpec("TEXT", True, 0),
        "code_git_sha": ColumnSpec("TEXT", False, 0),
        "code_package_version": ColumnSpec("TEXT", True, 0),
        "code_dirty": ColumnSpec("INTEGER", True, 0),
        "is_local_only": ColumnSpec("INTEGER", True, 0),
        "is_authoritative": ColumnSpec("INTEGER", True, 0),
    },
}

P1_V4_INDEXES: dict[str, tuple[str, IndexSpec]] = {
    "idx_artifact_digests_merkle": (
        "artifact_digests",
        IndexSpec(unique=False, columns=("merkle_root",)),
    ),
    "idx_artifact_digests_run": (
        "artifact_digests",
        IndexSpec(unique=True, columns=("run_id",)),
    ),
    "idx_artifact_digests_cohort": (
        "artifact_digests",
        IndexSpec(unique=False, columns=("cohort_id",)),
    ),
    "idx_artifact_digests_lineage": (
        "artifact_digests",
        IndexSpec(unique=False, columns=("research_lineage_id",)),
    ),
    "idx_artifact_digests_event": (
        "artifact_digests",
        IndexSpec(unique=True, columns=("registration_event_seq",)),
    ),
    "idx_artifact_digests_relative_root": (
        "artifact_digests",
        IndexSpec(unique=True, columns=("relative_root",)),
    ),
    "idx_trial_completion_links_event": (
        "trial_completion_links",
        IndexSpec(unique=True, columns=("completion_event_seq",)),
    ),
    "idx_trial_completion_links_artifact": (
        "trial_completion_links",
        IndexSpec(unique=True, columns=("artifact_id",)),
    ),
    "idx_checkpoints_final_seq": (
        "checkpoints",
        IndexSpec(unique=True, columns=("final_event_seq",)),
    ),
    "idx_checkpoints_event": (
        "checkpoints",
        IndexSpec(unique=True, columns=("checkpoint_event_seq",)),
    ),
}

P1_V4_FOREIGN_KEYS: dict[str, tuple[CompositeFK, ...]] = {
    "artifact_digests": (
        ("ledger_events", (("registration_event_seq", "event_seq"),)),
        ("research_lineages", (("research_lineage_id", "research_lineage_id"),)),
        (
            "programme_versions",
            (("programme_version_id", "programme_version_id"),),
        ),
        ("trials", (("trial_id", "trial_id"),)),
        (
            "cohorts",
            (
                ("cohort_id", "cohort_id"),
                ("programme_version_id", "programme_version_id"),
            ),
        ),
        (
            "artifact_digests",
            (("supersedes_artifact_id", "artifact_id"),),
        ),
    ),
    "trial_completion_links": (
        ("trials", (("trial_id", "trial_id"),)),
        ("ledger_events", (("completion_event_seq", "event_seq"),)),
        ("artifact_digests", (("artifact_id", "artifact_id"),)),
        ("ledger_events", (("registration_event_seq", "event_seq"),)),
    ),
    "checkpoints": (
        ("ledger_events", (("checkpoint_event_seq", "event_seq"),)),
    ),
}

# Rebuild ledger_events with expanded event_type CHECK (pure SQL; FKs off).
_V4_LEDGER_EVENTS_REBUILD: tuple[str, ...] = (
    f"""
    CREATE TABLE ledger_events__p1v4 (
        event_seq INTEGER PRIMARY KEY,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        prev_event_hash TEXT NOT NULL,
        event_hash TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        CHECK (event_seq >= 1),
        CHECK ({_EVENT_TYPE_CHECK_V4}),
        CHECK (length(trim(payload_json)) > 0),
        CHECK ({_sha256_check("prev_event_hash")}),
        CHECK ({_sha256_check("event_hash")}),
        CHECK ({_utc_timestamp_check("recorded_at")})
    )
    """,
    """
    INSERT INTO ledger_events__p1v4(
        event_seq, event_type, payload_json,
        prev_event_hash, event_hash, recorded_at
    )
    SELECT
        event_seq, event_type, payload_json,
        prev_event_hash, event_hash, recorded_at
    FROM ledger_events
    """,
    "DROP TRIGGER IF EXISTS trg_ledger_events_no_update",
    "DROP TRIGGER IF EXISTS trg_ledger_events_no_delete",
    "DROP TRIGGER IF EXISTS trg_ledger_events_contiguous_insert",
    "DROP INDEX IF EXISTS idx_ledger_events_hash",
    "DROP TABLE ledger_events",
    "ALTER TABLE ledger_events__p1v4 RENAME TO ledger_events",
    """
    CREATE UNIQUE INDEX idx_ledger_events_hash
        ON ledger_events(event_hash)
    """,
    """
    CREATE TRIGGER trg_ledger_events_no_update
    BEFORE UPDATE ON ledger_events
    BEGIN
        SELECT RAISE(ABORT, 'ledger_events is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_ledger_events_no_delete
    BEFORE DELETE ON ledger_events
    BEGIN
        SELECT RAISE(ABORT, 'ledger_events is append-only: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_ledger_events_contiguous_insert
    BEFORE INSERT ON ledger_events
    WHEN NEW.event_seq <> (
        SELECT COALESCE(MAX(event_seq), 0) + 1 FROM ledger_events
    )
    BEGIN
        SELECT RAISE(ABORT, 'ledger_events.event_seq must be contiguous');
    END
    """,
)

_V4_TABLE_STATEMENTS: tuple[str, ...] = (
    f"""
    CREATE TABLE artifact_digests (
        artifact_id TEXT PRIMARY KEY,
        merkle_root TEXT NOT NULL,
        bundle_kind TEXT NOT NULL,
        run_id TEXT,
        cohort_id TEXT,
        trial_id TEXT,
        research_lineage_id TEXT NOT NULL,
        programme_version_id TEXT NOT NULL,
        manifest_sha256 TEXT NOT NULL,
        config_hash TEXT NOT NULL,
        candidate_spec_hash TEXT NOT NULL,
        split_manifest_hash TEXT NOT NULL,
        data_hash TEXT NOT NULL,
        feature_hash TEXT NOT NULL,
        dependency_lock_hash TEXT NOT NULL,
        relative_root TEXT NOT NULL,
        byte_size INTEGER NOT NULL,
        registration_event_seq INTEGER NOT NULL,
        supersedes_artifact_id TEXT,
        is_correction INTEGER NOT NULL,
        sealed_at TEXT NOT NULL,
        CHECK ({_BUNDLE_KIND_CHECK}),
        CHECK (length(trim(artifact_id)) > 0),
        CHECK (length(trim(merkle_root)) = 64),
        CHECK ({_sha256_check("merkle_root")}),
        CHECK ({_sha256_check("manifest_sha256")}),
        CHECK ({_sha256_check("config_hash")}),
        CHECK ({_sha256_check("candidate_spec_hash")}),
        CHECK ({_sha256_check("split_manifest_hash")}),
        CHECK ({_sha256_check("data_hash")}),
        CHECK ({_sha256_check("feature_hash")}),
        CHECK ({_sha256_check("dependency_lock_hash")}),
        CHECK (byte_size >= 0),
        CHECK (length(trim(relative_root)) > 0),
        CHECK (length(trim(research_lineage_id)) > 0),
        CHECK (length(trim(programme_version_id)) > 0),
        CHECK (is_correction IN (0, 1)),
        CHECK (
            (
                bundle_kind = 'run'
                AND run_id IS NOT NULL
                AND length(trim(run_id)) > 0
                AND cohort_id IS NULL
                AND trial_id IS NOT NULL
                AND length(trim(trial_id)) > 0
            )
            OR
            (
                bundle_kind = 'cohort'
                AND cohort_id IS NOT NULL
                AND length(trim(cohort_id)) > 0
                AND run_id IS NULL
            )
        ),
        CHECK (
            (
                is_correction = 0
                AND supersedes_artifact_id IS NULL
            )
            OR
            (
                is_correction = 1
                AND supersedes_artifact_id IS NOT NULL
                AND length(trim(supersedes_artifact_id)) > 0
                AND supersedes_artifact_id <> artifact_id
            )
        ),
        CHECK ({_utc_timestamp_check("sealed_at")}),
        UNIQUE (registration_event_seq),
        UNIQUE (run_id),
        UNIQUE (relative_root),
        FOREIGN KEY (registration_event_seq)
            REFERENCES ledger_events(event_seq),
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id),
        FOREIGN KEY (programme_version_id)
            REFERENCES programme_versions(programme_version_id),
        FOREIGN KEY (trial_id)
            REFERENCES trials(trial_id),
        FOREIGN KEY (cohort_id, programme_version_id)
            REFERENCES cohorts(cohort_id, programme_version_id),
        FOREIGN KEY (supersedes_artifact_id)
            REFERENCES artifact_digests(artifact_id)
    )
    """,
    f"""
    CREATE TABLE trial_completion_links (
        trial_id TEXT PRIMARY KEY,
        completion_event_seq INTEGER NOT NULL,
        artifact_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        registration_event_seq INTEGER NOT NULL,
        state_event_id TEXT NOT NULL,
        CHECK (length(trim(trial_id)) > 0),
        CHECK (length(trim(artifact_id)) > 0),
        CHECK (length(trim(run_id)) > 0),
        CHECK (length(trim(state_event_id)) > 0),
        CHECK (completion_event_seq >= 1),
        CHECK (registration_event_seq >= 1),
        UNIQUE (completion_event_seq),
        UNIQUE (artifact_id),
        UNIQUE (state_event_id),
        FOREIGN KEY (trial_id)
            REFERENCES trials(trial_id),
        FOREIGN KEY (completion_event_seq)
            REFERENCES ledger_events(event_seq),
        FOREIGN KEY (artifact_id)
            REFERENCES artifact_digests(artifact_id),
        FOREIGN KEY (registration_event_seq)
            REFERENCES ledger_events(event_seq)
    )
    """,
    f"""
    CREATE TABLE checkpoints (
        checkpoint_id TEXT PRIMARY KEY,
        checkpoint_event_seq INTEGER NOT NULL,
        final_event_seq INTEGER NOT NULL,
        final_event_hash TEXT NOT NULL,
        database_snapshot_hash TEXT NOT NULL,
        artifact_aggregate_merkle_root TEXT NOT NULL,
        snapshot_byte_size INTEGER NOT NULL,
        snapshot_relative_path TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        code_git_sha TEXT,
        code_package_version TEXT NOT NULL,
        code_dirty INTEGER NOT NULL,
        is_local_only INTEGER NOT NULL,
        is_authoritative INTEGER NOT NULL,
        CHECK (length(trim(checkpoint_id)) > 0),
        CHECK (checkpoint_event_seq >= 1),
        CHECK (final_event_seq >= 0),
        CHECK (checkpoint_event_seq = final_event_seq + 1),
        CHECK ({_sha256_check("final_event_hash")}),
        CHECK ({_sha256_check("database_snapshot_hash")}),
        CHECK ({_sha256_check("artifact_aggregate_merkle_root")}),
        CHECK (snapshot_byte_size >= 0),
        CHECK (length(trim(snapshot_relative_path)) > 0),
        CHECK (length(trim(code_package_version)) > 0),
        CHECK (code_dirty IN (0, 1)),
        CHECK (is_local_only = 1),
        CHECK (is_authoritative = 0),
        CHECK (
            code_git_sha IS NULL
            OR (
                length(code_git_sha) >= 7
                AND length(code_git_sha) <= 64
                AND code_git_sha GLOB '[0-9a-f]*'
            )
        ),
        CHECK ({_utc_timestamp_check("recorded_at")}),
        UNIQUE (checkpoint_event_seq),
        UNIQUE (final_event_seq),
        FOREIGN KEY (checkpoint_event_seq)
            REFERENCES ledger_events(event_seq)
    )
    """,
    """
    CREATE INDEX idx_artifact_digests_merkle
        ON artifact_digests(merkle_root)
    """,
    """
    CREATE UNIQUE INDEX idx_artifact_digests_run
        ON artifact_digests(run_id)
    """,
    """
    CREATE INDEX idx_artifact_digests_cohort
        ON artifact_digests(cohort_id)
    """,
    """
    CREATE INDEX idx_artifact_digests_lineage
        ON artifact_digests(research_lineage_id)
    """,
    """
    CREATE UNIQUE INDEX idx_artifact_digests_event
        ON artifact_digests(registration_event_seq)
    """,
    """
    CREATE UNIQUE INDEX idx_artifact_digests_relative_root
        ON artifact_digests(relative_root)
    """,
    """
    CREATE UNIQUE INDEX idx_trial_completion_links_event
        ON trial_completion_links(completion_event_seq)
    """,
    """
    CREATE UNIQUE INDEX idx_trial_completion_links_artifact
        ON trial_completion_links(artifact_id)
    """,
    """
    CREATE UNIQUE INDEX idx_checkpoints_final_seq
        ON checkpoints(final_event_seq)
    """,
    """
    CREATE UNIQUE INDEX idx_checkpoints_event
        ON checkpoints(checkpoint_event_seq)
    """,
)

_V4_TRIGGER_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TRIGGER trg_artifact_digests_no_update
    BEFORE UPDATE ON artifact_digests
    BEGIN
        SELECT RAISE(ABORT, 'artifact_digests is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_artifact_digests_no_delete
    BEFORE DELETE ON artifact_digests
    BEGIN
        SELECT RAISE(ABORT, 'artifact_digests is append-only: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_trial_completion_links_no_update
    BEFORE UPDATE ON trial_completion_links
    BEGIN
        SELECT RAISE(ABORT, 'trial_completion_links is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_trial_completion_links_no_delete
    BEFORE DELETE ON trial_completion_links
    BEGIN
        SELECT RAISE(ABORT, 'trial_completion_links is append-only: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_artifact_digests_programme_research_lineage_match
    BEFORE INSERT ON artifact_digests
    WHEN NOT EXISTS (
        SELECT 1
        FROM programme_versions p
        WHERE p.programme_version_id = NEW.programme_version_id
          AND p.research_lineage_id = NEW.research_lineage_id
    )
    BEGIN
        SELECT RAISE(
            ABORT,
            'artifact programme_version_id/research_lineage_id mismatch'
        );
    END
    """,
    """
    CREATE TRIGGER trg_artifact_digests_trial_lineage_match
    BEFORE INSERT ON artifact_digests
    WHEN NEW.trial_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1
        FROM trials t
        WHERE t.trial_id = NEW.trial_id
          AND t.research_lineage_id = NEW.research_lineage_id
          AND t.programme_version_id = NEW.programme_version_id
    )
    BEGIN
        SELECT RAISE(
            ABORT,
            'artifact trial_id lineage/programme mismatch'
        );
    END
    """,
    """
    CREATE TRIGGER trg_artifact_digests_cohort_programme_match
    BEFORE INSERT ON artifact_digests
    WHEN NEW.cohort_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1
        FROM cohorts c
        JOIN programme_versions p
          ON p.programme_version_id = c.programme_version_id
        WHERE c.cohort_id = NEW.cohort_id
          AND c.programme_version_id = NEW.programme_version_id
          AND p.research_lineage_id = NEW.research_lineage_id
    )
    BEGIN
        SELECT RAISE(
            ABORT,
            'artifact cohort programme/research lineage mismatch'
        );
    END
    """,
    """
    CREATE TRIGGER trg_artifact_digests_correction_same_lineage
    BEFORE INSERT ON artifact_digests
    WHEN NEW.is_correction = 1
      AND NOT EXISTS (
        SELECT 1
        FROM artifact_digests old
        WHERE old.artifact_id = NEW.supersedes_artifact_id
          AND old.research_lineage_id = NEW.research_lineage_id
          AND old.bundle_kind = NEW.bundle_kind
    )
    BEGIN
        SELECT RAISE(
            ABORT,
            'correction must supersede same-lineage same-kind artefact'
        );
    END
    """,
    """
    CREATE TRIGGER trg_trial_completion_links_run_artifact
    BEFORE INSERT ON trial_completion_links
    WHEN NOT EXISTS (
        SELECT 1
        FROM artifact_digests ad
        WHERE ad.artifact_id = NEW.artifact_id
          AND ad.bundle_kind = 'run'
          AND ad.run_id = NEW.run_id
          AND ad.trial_id = NEW.trial_id
          AND ad.registration_event_seq = NEW.registration_event_seq
    )
    BEGIN
        SELECT RAISE(
            ABORT,
            'completion link must bind exact run artefact for trial'
        );
    END
    """,
    """
    CREATE TRIGGER trg_trial_state_completed_requires_link
    BEFORE INSERT ON trial_state_events
    WHEN NEW.execution_state = 'completed'
      AND NOT EXISTS (
        SELECT 1
        FROM trial_completion_links l
        WHERE l.trial_id = NEW.trial_id
          AND l.completion_event_seq = NEW.event_seq
          AND l.state_event_id = NEW.state_event_id
    )
    BEGIN
        SELECT RAISE(
            ABORT,
            'completed state requires exact trial_completion_links row'
        );
    END
    """,
    """
    CREATE TRIGGER trg_trial_state_single_completed
    BEFORE INSERT ON trial_state_events
    WHEN NEW.execution_state = 'completed'
      AND EXISTS (
        SELECT 1
        FROM trial_state_events e
        WHERE e.trial_id = NEW.trial_id
          AND e.execution_state = 'completed'
    )
    BEGIN
        SELECT RAISE(
            ABORT,
            'trial already has a completed transition'
        );
    END
    """,
    """
    CREATE TRIGGER trg_checkpoints_no_update
    BEFORE UPDATE ON checkpoints
    BEGIN
        SELECT RAISE(ABORT, 'checkpoints is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_checkpoints_no_delete
    BEFORE DELETE ON checkpoints
    BEGIN
        SELECT RAISE(ABORT, 'checkpoints is append-only: DELETE forbidden');
    END
    """,
)

_V4_STATEMENTS: tuple[str, ...] = (
    _V4_LEDGER_EVENTS_REBUILD + _V4_TABLE_STATEMENTS + _V4_TRIGGER_STATEMENTS
)

P1_V4_TRIGGER_SQL: dict[str, str] = {
    _trigger_name_from_create(stmt): _normalize_sql(stmt)
    for stmt in _V4_TRIGGER_STATEMENTS
}

P1_V4_TRIGGERS: dict[str, str] = {}
for _name, _norm in P1_V4_TRIGGER_SQL.items():
    import re as _re

    _match = _re.search(r"\bON\s+([A-Z_][A-Z0-9_]*)\b", _norm)
    if not _match:
        raise RuntimeError(f"cannot parse table for trigger {_name}")
    P1_V4_TRIGGERS[_name] = _match.group(1).lower()


def _v4_artifact_checkpoint_foundation(conn: sqlite3.Connection) -> None:
    """Expand ledger event types; create artefact digest + checkpoint schema."""
    for stmt in _V4_STATEMENTS:
        conn.execute(stmt)


# =============================================================================
# v5 — external anchors + off-machine backup verification (PR5)
# =============================================================================
# Append-only external_anchors / off_machine_backups. Expand ledger event types.
# Never mutates prior events; UNANCHORED_PENDING / BACKUP_UNVERIFIED default path.

_EVENT_TYPE_CHECK_V5 = (
    "event_type IN ("
    "'trial_registered',"
    "'trial_state_transition',"
    "'budget_allocated',"
    "'legacy_n_bound_proposed',"
    "'artifact_bundle_sealed',"
    "'artifact_bundle_supersession',"
    "'checkpoint_recorded',"
    "'external_anchor_recorded',"
    "'off_machine_backup_recorded'"
    ")"
)

_ANCHOR_STATUS_CHECK = (
    "status IN ('UNANCHORED_PENDING', 'ANCHORED')"
)
_BACKUP_STATUS_CHECK = (
    "status IN ('BACKUP_UNVERIFIED', 'BACKUP_VERIFIED')"
)

P1_V5_DATA_TABLES: tuple[str, ...] = (
    "external_anchors",
    "off_machine_backups",
)

P1_V5_COLUMNS: dict[str, dict[str, ColumnSpec]] = {
    "external_anchors": {
        "anchor_id": ColumnSpec("TEXT", True, 1),
        "provider_id": ColumnSpec("TEXT", True, 0),
        "status": ColumnSpec("TEXT", True, 0),
        "research_lineage_id": ColumnSpec("TEXT", True, 0),
        "final_event_seq": ColumnSpec("INTEGER", True, 0),
        "final_event_hash": ColumnSpec("TEXT", True, 0),
        "checkpoint_id": ColumnSpec("TEXT", False, 0),
        "database_snapshot_hash": ColumnSpec("TEXT", False, 0),
        "artifact_aggregate_root": ColumnSpec("TEXT", False, 0),
        "external_ref": ColumnSpec("TEXT", False, 0),
        "registration_event_seq": ColumnSpec("INTEGER", True, 0),
        "attested_at": ColumnSpec("TEXT", True, 0),
        "detail_json": ColumnSpec("TEXT", True, 0),
    },
    "off_machine_backups": {
        "backup_id": ColumnSpec("TEXT", True, 1),
        "provider_id": ColumnSpec("TEXT", True, 0),
        "status": ColumnSpec("TEXT", True, 0),
        "research_lineage_id": ColumnSpec("TEXT", True, 0),
        "snapshot_relative_path": ColumnSpec("TEXT", True, 0),
        "snapshot_sha256": ColumnSpec("TEXT", True, 0),
        "snapshot_size_bytes": ColumnSpec("INTEGER", True, 0),
        "final_event_seq": ColumnSpec("INTEGER", True, 0),
        "final_event_hash": ColumnSpec("TEXT", True, 0),
        "registration_event_seq": ColumnSpec("INTEGER", True, 0),
        "verified_at": ColumnSpec("TEXT", True, 0),
        "detail_json": ColumnSpec("TEXT", True, 0),
    },
}

P1_V5_INDEXES: dict[str, tuple[str, IndexSpec]] = {
    "idx_external_anchors_tip": (
        "external_anchors",
        IndexSpec(
            unique=False,
            columns=("research_lineage_id", "final_event_seq"),
        ),
    ),
    "idx_external_anchors_event": (
        "external_anchors",
        IndexSpec(unique=True, columns=("registration_event_seq",)),
    ),
    "idx_off_machine_backups_tip": (
        "off_machine_backups",
        IndexSpec(
            unique=False,
            columns=("research_lineage_id", "final_event_seq"),
        ),
    ),
    "idx_off_machine_backups_event": (
        "off_machine_backups",
        IndexSpec(unique=True, columns=("registration_event_seq",)),
    ),
}

P1_V5_FOREIGN_KEYS: dict[str, tuple[CompositeFK, ...]] = {
    "external_anchors": (
        ("ledger_events", (("registration_event_seq", "event_seq"),)),
        ("research_lineages", (("research_lineage_id", "research_lineage_id"),)),
    ),
    "off_machine_backups": (
        ("ledger_events", (("registration_event_seq", "event_seq"),)),
        ("research_lineages", (("research_lineage_id", "research_lineage_id"),)),
    ),
}

_V5_LEDGER_EVENTS_REBUILD: tuple[str, ...] = (
    f"""
    CREATE TABLE ledger_events__p1v5 (
        event_seq INTEGER PRIMARY KEY,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        prev_event_hash TEXT NOT NULL,
        event_hash TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        CHECK (event_seq >= 1),
        CHECK ({_EVENT_TYPE_CHECK_V5}),
        CHECK (length(trim(payload_json)) > 0),
        CHECK ({_sha256_check("prev_event_hash")}),
        CHECK ({_sha256_check("event_hash")}),
        CHECK ({_utc_timestamp_check("recorded_at")})
    )
    """,
    """
    INSERT INTO ledger_events__p1v5(
        event_seq, event_type, payload_json,
        prev_event_hash, event_hash, recorded_at
    )
    SELECT
        event_seq, event_type, payload_json,
        prev_event_hash, event_hash, recorded_at
    FROM ledger_events
    """,
    "DROP TRIGGER IF EXISTS trg_ledger_events_no_update",
    "DROP TRIGGER IF EXISTS trg_ledger_events_no_delete",
    "DROP TRIGGER IF EXISTS trg_ledger_events_contiguous_insert",
    "DROP INDEX IF EXISTS idx_ledger_events_hash",
    "DROP TABLE ledger_events",
    "ALTER TABLE ledger_events__p1v5 RENAME TO ledger_events",
    """
    CREATE UNIQUE INDEX idx_ledger_events_hash
        ON ledger_events(event_hash)
    """,
    """
    CREATE TRIGGER trg_ledger_events_no_update
    BEFORE UPDATE ON ledger_events
    BEGIN
        SELECT RAISE(ABORT, 'ledger_events is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_ledger_events_no_delete
    BEFORE DELETE ON ledger_events
    BEGIN
        SELECT RAISE(ABORT, 'ledger_events is append-only: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_ledger_events_contiguous_insert
    BEFORE INSERT ON ledger_events
    WHEN NEW.event_seq <> (
        SELECT COALESCE(MAX(event_seq), 0) + 1 FROM ledger_events
    )
    BEGIN
        SELECT RAISE(ABORT, 'ledger_events.event_seq must be contiguous');
    END
    """,
)

_V5_TABLE_STATEMENTS: tuple[str, ...] = (
    f"""
    CREATE TABLE external_anchors (
        anchor_id TEXT PRIMARY KEY,
        provider_id TEXT NOT NULL,
        status TEXT NOT NULL,
        research_lineage_id TEXT NOT NULL,
        final_event_seq INTEGER NOT NULL,
        final_event_hash TEXT NOT NULL,
        checkpoint_id TEXT,
        database_snapshot_hash TEXT,
        artifact_aggregate_root TEXT,
        external_ref TEXT,
        registration_event_seq INTEGER NOT NULL,
        attested_at TEXT NOT NULL,
        detail_json TEXT NOT NULL,
        CHECK (length(trim(anchor_id)) > 0),
        CHECK (length(trim(provider_id)) > 0),
        CHECK ({_ANCHOR_STATUS_CHECK}),
        CHECK (final_event_seq >= 1),
        CHECK ({_sha256_check("final_event_hash")}),
        CHECK (
            database_snapshot_hash IS NULL
            OR ({_sha256_check("database_snapshot_hash")})
        ),
        CHECK (
            artifact_aggregate_root IS NULL
            OR ({_sha256_check("artifact_aggregate_root")})
        ),
        CHECK (length(trim(detail_json)) > 0),
        CHECK ({_utc_timestamp_check("attested_at")}),
        UNIQUE (registration_event_seq),
        FOREIGN KEY (registration_event_seq)
            REFERENCES ledger_events(event_seq),
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id)
    )
    """,
    f"""
    CREATE TABLE off_machine_backups (
        backup_id TEXT PRIMARY KEY,
        provider_id TEXT NOT NULL,
        status TEXT NOT NULL,
        research_lineage_id TEXT NOT NULL,
        snapshot_relative_path TEXT NOT NULL,
        snapshot_sha256 TEXT NOT NULL,
        snapshot_size_bytes INTEGER NOT NULL,
        final_event_seq INTEGER NOT NULL,
        final_event_hash TEXT NOT NULL,
        registration_event_seq INTEGER NOT NULL,
        verified_at TEXT NOT NULL,
        detail_json TEXT NOT NULL,
        CHECK (length(trim(backup_id)) > 0),
        CHECK (length(trim(provider_id)) > 0),
        CHECK ({_BACKUP_STATUS_CHECK}),
        CHECK (length(trim(snapshot_relative_path)) > 0),
        CHECK (snapshot_size_bytes >= 0),
        CHECK (final_event_seq >= 1),
        CHECK ({_sha256_check("snapshot_sha256")}),
        CHECK ({_sha256_check("final_event_hash")}),
        CHECK (length(trim(detail_json)) > 0),
        CHECK ({_utc_timestamp_check("verified_at")}),
        UNIQUE (registration_event_seq),
        FOREIGN KEY (registration_event_seq)
            REFERENCES ledger_events(event_seq),
        FOREIGN KEY (research_lineage_id)
            REFERENCES research_lineages(research_lineage_id)
    )
    """,
    """
    CREATE INDEX idx_external_anchors_tip
        ON external_anchors(research_lineage_id, final_event_seq)
    """,
    """
    CREATE UNIQUE INDEX idx_external_anchors_event
        ON external_anchors(registration_event_seq)
    """,
    """
    CREATE INDEX idx_off_machine_backups_tip
        ON off_machine_backups(research_lineage_id, final_event_seq)
    """,
    """
    CREATE UNIQUE INDEX idx_off_machine_backups_event
        ON off_machine_backups(registration_event_seq)
    """,
)

_V5_TRIGGER_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TRIGGER trg_external_anchors_no_update
    BEFORE UPDATE ON external_anchors
    BEGIN
        SELECT RAISE(ABORT, 'external_anchors is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_external_anchors_no_delete
    BEFORE DELETE ON external_anchors
    BEGIN
        SELECT RAISE(ABORT, 'external_anchors is append-only: DELETE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_off_machine_backups_no_update
    BEFORE UPDATE ON off_machine_backups
    BEGIN
        SELECT RAISE(ABORT, 'off_machine_backups is append-only: UPDATE forbidden');
    END
    """,
    """
    CREATE TRIGGER trg_off_machine_backups_no_delete
    BEFORE DELETE ON off_machine_backups
    BEGIN
        SELECT RAISE(ABORT, 'off_machine_backups is append-only: DELETE forbidden');
    END
    """,
)

_V5_STATEMENTS: tuple[str, ...] = (
    _V5_LEDGER_EVENTS_REBUILD + _V5_TABLE_STATEMENTS + _V5_TRIGGER_STATEMENTS
)

P1_V5_TRIGGER_SQL: dict[str, str] = {
    _trigger_name_from_create(stmt): _normalize_sql(stmt)
    for stmt in _V5_TRIGGER_STATEMENTS
}

P1_V5_TRIGGERS: dict[str, str] = {}
for _name, _norm in P1_V5_TRIGGER_SQL.items():
    import re as _re

    _match = _re.search(r"\bON\s+([A-Z_][A-Z0-9_]*)\b", _norm)
    if not _match:
        raise RuntimeError(f"cannot parse table for trigger {_name}")
    P1_V5_TRIGGERS[_name] = _match.group(1).lower()


def _v5_external_anchor_foundation(conn: sqlite3.Connection) -> None:
    """Expand ledger event types; create external anchor + backup tables."""
    for stmt in _V5_STATEMENTS:
        conn.execute(stmt)


MIGRATIONS: list[tuple[int, MigrationFn]] = [
    (1, _v1_p1_foundation),
    (2, _v2_holdout_foundation),
    (3, _v3_trial_ledger_foundation),
    (4, _v4_artifact_checkpoint_foundation),
    (5, _v5_external_anchor_foundation),
]

MIGRATION_STATEMENTS: dict[int, tuple[str, ...]] = {
    1: _V1_STATEMENTS,
    2: _V2_STATEMENTS,
    3: _V3_STATEMENTS,
    4: _V4_STATEMENTS,
    5: _V5_STATEMENTS,
}
