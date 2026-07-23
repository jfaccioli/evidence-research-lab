"""Append-only ledger hash chain (canonical payload + recomputable hashes).

The first event uses an explicit fixed genesis ``prev_event_hash``. Chain
integrity is verified by recomputation; gaps, payload edits, and hash edits
fail closed.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

# Explicit fixed genesis previous-hash for event_seq == 1.
GENESIS_PREV_EVENT_HASH = "0" * 64


class LedgerHashError(RuntimeError):
    """Hash-chain verification or construction failed (fail closed)."""


def canonical_json(payload: Mapping[str, Any] | Sequence[Any] | Any) -> str:
    """RFC-style compact canonical JSON (sorted keys, no extra whitespace)."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def compute_event_hash(
    *,
    event_seq: int,
    event_type: str,
    payload_json: str,
    prev_event_hash: str,
) -> str:
    """Recomputable SHA-256 over contiguous sequence fields + payload bytes."""
    if int(event_seq) < 1:
        raise LedgerHashError("event_seq must be >= 1")
    if not event_type or not str(event_type).strip():
        raise LedgerHashError("event_type must be non-empty")
    if not payload_json or not str(payload_json).strip():
        raise LedgerHashError("payload_json must be non-empty")
    prev = str(prev_event_hash).strip().lower()
    if len(prev) != 64 or any(ch not in "0123456789abcdef" for ch in prev):
        raise LedgerHashError("prev_event_hash must be lowercase SHA-256 hex")
    material = {
        "event_seq": int(event_seq),
        "event_type": str(event_type),
        "payload_json": str(payload_json),
        "prev_event_hash": prev,
    }
    digest = hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()
    return digest


def expected_prev_hash(conn: sqlite3.Connection) -> tuple[int, str]:
    """Return ``(next_event_seq, prev_event_hash)`` for the next append."""
    row = conn.execute(
        """
        SELECT event_seq, event_hash
        FROM ledger_events
        ORDER BY event_seq DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return 1, GENESIS_PREV_EVENT_HASH
    return int(row[0]) + 1, str(row[1])


@dataclass(frozen=True)
class ChainVerification:
    """Result of full-chain recomputation."""

    ok: bool
    event_count: int
    tip_seq: int
    tip_hash: Optional[str]
    errors: tuple[str, ...]


def verify_hash_chain(conn: sqlite3.Connection) -> ChainVerification:
    """Recompute every event hash and enforce contiguous sequence from 1."""
    rows = conn.execute(
        """
        SELECT event_seq, event_type, payload_json, prev_event_hash, event_hash
        FROM ledger_events
        ORDER BY event_seq ASC
        """
    ).fetchall()
    errors: list[str] = []
    prev_hash = GENESIS_PREV_EVENT_HASH
    expected_seq = 1
    tip_hash: Optional[str] = None
    tip_seq = 0
    for row in rows:
        seq = int(row[0])
        event_type = str(row[1])
        payload_json = str(row[2])
        stored_prev = str(row[3])
        stored_hash = str(row[4])
        if seq != expected_seq:
            errors.append(
                f"sequence gap/mismatch at event_seq={seq} expected={expected_seq}"
            )
            # resync expected to continue reporting further damage
            expected_seq = seq
        if stored_prev != prev_hash:
            errors.append(
                f"prev_event_hash mismatch at event_seq={seq}: "
                f"stored={stored_prev} expected={prev_hash}"
            )
        try:
            recomputed = compute_event_hash(
                event_seq=seq,
                event_type=event_type,
                payload_json=payload_json,
                prev_event_hash=stored_prev,
            )
        except LedgerHashError as exc:
            errors.append(f"hash construction failed at event_seq={seq}: {exc}")
            recomputed = None
        if recomputed is not None and recomputed != stored_hash:
            errors.append(
                f"event_hash mismatch at event_seq={seq}: "
                f"stored={stored_hash} recomputed={recomputed}"
            )
        prev_hash = stored_hash
        tip_hash = stored_hash
        tip_seq = seq
        expected_seq = seq + 1
    return ChainVerification(
        ok=not errors,
        event_count=len(rows),
        tip_seq=tip_seq,
        tip_hash=tip_hash,
        errors=tuple(errors),
    )


def assert_hash_chain_intact(conn: sqlite3.Connection) -> ChainVerification:
    result = verify_hash_chain(conn)
    if not result.ok:
        raise LedgerHashError(
            "ledger hash chain verification failed: " + "; ".join(result.errors[:5])
        )
    return result
