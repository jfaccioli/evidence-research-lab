"""Append-only ledger event writer (no UPDATE/DELETE path)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from crl.research.ledger.hash_chain import (
    LedgerHashError,
    canonical_json,
    compute_event_hash,
    expected_prev_hash,
)

ALLOWED_EVENT_TYPES = frozenset(
    {
        "trial_registered",
        "trial_state_transition",
        "budget_allocated",
        "legacy_n_bound_proposed",
    }
)


def _utc_text(value: Optional[datetime] = None) -> str:
    dt = value or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}Z"


def append_event(
    conn: sqlite3.Connection,
    *,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: Optional[datetime] = None,
) -> tuple[int, str]:
    """Append one ledger event inside the caller's transaction.

    Returns ``(event_seq, event_hash)``.
    """
    event_type = str(event_type).strip()
    if event_type not in ALLOWED_EVENT_TYPES:
        raise LedgerHashError(f"unsupported event_type {event_type!r}")
    payload_json = canonical_json(dict(payload))
    event_seq, prev_hash = expected_prev_hash(conn)
    event_hash = compute_event_hash(
        event_seq=event_seq,
        event_type=event_type,
        payload_json=payload_json,
        prev_event_hash=prev_hash,
    )
    conn.execute(
        """
        INSERT INTO ledger_events(
            event_seq, event_type, payload_json,
            prev_event_hash, event_hash, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            event_seq,
            event_type,
            payload_json,
            prev_hash,
            event_hash,
            _utc_text(recorded_at),
        ),
    )
    return event_seq, event_hash
