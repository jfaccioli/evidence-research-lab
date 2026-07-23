"""Immutable budget allocations and append-only one-to-one trial debits.

Available budget is always derived: sum(allocations) − sum(debits).
Callers cannot edit ``units_spent``.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from crl.research.ledger.events import append_event, _utc_text


class BudgetError(RuntimeError):
    """Budget allocation or debit failed (fail closed)."""


@dataclass(frozen=True)
class BudgetAvailability:
    allocation_id: str
    units_allocated: int
    units_spent: int

    @property
    def units_available(self) -> int:
        return max(0, self.units_allocated - self.units_spent)


def allocation_availability(
    conn: sqlite3.Connection, allocation_id: str
) -> BudgetAvailability:
    row = conn.execute(
        """
        SELECT units_allocated
        FROM budget_allocations
        WHERE allocation_id = ?
        """,
        (allocation_id,),
    ).fetchone()
    if row is None:
        raise BudgetError(f"unknown allocation {allocation_id!r}")
    spent_row = conn.execute(
        """
        SELECT COALESCE(SUM(units_spent), 0)
        FROM budget_debits
        WHERE allocation_id = ?
        """,
        (allocation_id,),
    ).fetchone()
    return BudgetAvailability(
        allocation_id=allocation_id,
        units_allocated=int(row[0]),
        units_spent=int(spent_row[0]),
    )


def allocate_budget(
    conn: sqlite3.Connection,
    *,
    allocation_id: str,
    research_lineage_id: str,
    units_allocated: int,
    approval_note: str = "",
    allocated_at: Optional[datetime] = None,
) -> tuple[int, str]:
    """Insert an immutable allocation linked to a ledger event.

    Must run inside the caller's transaction.
    """
    allocation_id = str(allocation_id).strip()
    research_lineage_id = str(research_lineage_id).strip()
    if not allocation_id or not research_lineage_id:
        raise BudgetError("allocation_id and research_lineage_id required")
    units = int(units_allocated)
    if units < 1:
        raise BudgetError("units_allocated must be > 0")
    at = _utc_text(allocated_at)
    event_seq, event_hash = append_event(
        conn,
        event_type="budget_allocated",
        payload={
            "allocation_id": allocation_id,
            "research_lineage_id": research_lineage_id,
            "units_allocated": units,
            "approval_note": approval_note or "",
        },
        recorded_at=allocated_at,
    )
    conn.execute(
        """
        INSERT INTO budget_allocations(
            allocation_id, research_lineage_id, units_allocated,
            allocation_event_seq, allocated_at, approval_note
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            allocation_id,
            research_lineage_id,
            units,
            event_seq,
            at,
            approval_note or "",
        ),
    )
    return event_seq, event_hash


def insert_debit(
    conn: sqlite3.Connection,
    *,
    debit_id: str,
    allocation_id: str,
    trial_id: str,
    event_seq: int,
    units_spent: int,
    debited_at: Optional[datetime] = None,
) -> None:
    """Append one debit linked 1:1 to a billable trial (caller transaction)."""
    units = int(units_spent)
    if units < 1:
        raise BudgetError("units_spent must be > 0")
    lineage_row = conn.execute(
        """
        SELECT a.research_lineage_id, t.research_lineage_id
        FROM budget_allocations a
        JOIN trials t ON t.trial_id = ?
        WHERE a.allocation_id = ?
        """,
        (trial_id, allocation_id),
    ).fetchone()
    if lineage_row is None:
        raise BudgetError("allocation and registered trial must both exist")
    if str(lineage_row[0]) != str(lineage_row[1]):
        raise BudgetError(
            "budget allocation belongs to another research_lineage_id"
        )
    avail = allocation_availability(conn, allocation_id)
    if avail.units_available < units:
        raise BudgetError(
            f"insufficient budget on {allocation_id!r}: "
            f"need {units}, available {avail.units_available}"
        )
    conn.execute(
        """
        INSERT INTO budget_debits(
            debit_id, allocation_id, trial_id, event_seq,
            units_spent, debited_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            str(debit_id).strip(),
            allocation_id,
            trial_id,
            int(event_seq),
            units,
            _utc_text(debited_at),
        ),
    )
