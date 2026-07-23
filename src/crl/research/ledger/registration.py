"""Atomic trial + budget (+ optional confirmatory holdout) registration.

One SQLite transaction appends the ledger event, trial registration, and
budget debit together. Confirmatory cohort registration also performs the
PR2 AVAILABLE→RESERVED transition in that same transaction and returns the
reservation capability. Any failure rolls everything back.

Reproduction byte-identity is derived inside the registration transaction by
comparing the new trial's ``immutable_input_hash`` to the referenced trial's
stored hash. Legacy N bounds are proposal-only; PR3 has no public path to mint
verified human approval.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from crl.db.schema import CURRENT_P1_SCHEMA_VERSION, connect_p1
from crl.research.holdout.state_machine import (
    HoldoutReservation,
    HoldoutStateMachine,
)
from crl.research.ledger.budget import BudgetError, insert_debit
from crl.research.ledger.events import append_event, _utc_text
from crl.research.ledger.hash_chain import LedgerHashError
from crl.research.ledger.trials import (
    ExecutionState,
    TrialKind,
    TrialRegistrationError,
    TrialRegistrationFacts,
    derive_selection_capable,
)


class RegistrationError(RuntimeError):
    """Atomic registration failed (transaction rolled back)."""


@dataclass(frozen=True)
class RegistrationResult:
    trial_id: str
    event_seq: int
    event_hash: str
    debit_id: Optional[str]
    units_spent: int
    selection_capable: bool
    reservation: Optional[HoldoutReservation]
    reproduction_input_hash: Optional[str] = None
    reproduction_byte_identical: Optional[bool] = None


def _sha256_digest(value: str, field: str) -> str:
    text = str(value).strip().lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise RegistrationError(f"{field} must be SHA-256 hex")
    return text


class TrialLedger:
    """Append-only analytical-trial ledger over an explicitly migrated v3 DB."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).resolve()
        conn = connect_p1(self.database_path, readonly=True)
        try:
            version = int(
                conn.execute(
                    "SELECT version FROM crl_schema_meta WHERE component='p1_programme'"
                ).fetchone()[0]
            )
            if version < 3 or CURRENT_P1_SCHEMA_VERSION < 3:
                raise RegistrationError("trial ledger requires schema v3")
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = connect_p1(self.database_path)
        conn.isolation_level = None
        return conn

    def allocate_budget(
        self,
        *,
        allocation_id: str,
        research_lineage_id: str,
        units_allocated: int,
        approval_note: str = "",
        allocated_at: Optional[datetime] = None,
    ) -> tuple[int, str]:
        from crl.research.ledger.budget import allocate_budget

        conn = self._connect()
        error: BaseException | None = None
        try:
            conn.execute("BEGIN IMMEDIATE")
            return allocate_budget(
                conn,
                allocation_id=allocation_id,
                research_lineage_id=research_lineage_id,
                units_allocated=units_allocated,
                approval_note=approval_note,
                allocated_at=allocated_at,
            )
        except BaseException as exc:
            error = exc
            raise
        finally:
            if error is None:
                conn.execute("COMMIT")
            else:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
            conn.close()

    def propose_legacy_n_bound(
        self,
        *,
        proposal_id: str,
        research_lineage_id: str,
        upper_bound_n: int,
        supporting_artefact_hash: str,
        notes: str = "",
        proposed_at: Optional[datetime] = None,
    ) -> tuple[int, str]:
        """Record an immutable **proposal** for a legacy N upper bound.

        A digest-shaped ``supporting_artefact_hash`` is stored for audit only.
        It is **not** independent human authority: the proposal never enters
        authoritative ``N_global``, never satisfies completeness, and never
        unblocks promotion inputs. PR3 has no verified-approval mint path.
        """
        proposal_id = str(proposal_id).strip()
        if not proposal_id:
            raise RegistrationError("proposal_id must be non-empty")
        research_lineage_id = str(research_lineage_id).strip()
        if not research_lineage_id:
            raise RegistrationError("research_lineage_id must be non-empty")
        upper = int(upper_bound_n)
        if upper < 0:
            raise RegistrationError("upper_bound_n must be >= 0")
        digest = _sha256_digest(
            supporting_artefact_hash, "supporting_artefact_hash"
        )

        conn = self._connect()
        error: BaseException | None = None
        try:
            conn.execute("BEGIN IMMEDIATE")
            lineage = conn.execute(
                """
                SELECT 1 FROM research_lineages
                WHERE research_lineage_id = ?
                """,
                (research_lineage_id,),
            ).fetchone()
            if lineage is None:
                raise RegistrationError(
                    f"unknown research_lineage_id {research_lineage_id!r}"
                )
            event_seq, event_hash = append_event(
                conn,
                event_type="legacy_n_bound_proposed",
                payload={
                    "proposal_id": proposal_id,
                    "research_lineage_id": research_lineage_id,
                    "upper_bound_n": upper,
                    "supporting_artefact_hash": digest,
                    "notes": notes or "",
                    "authoritative": False,
                },
                recorded_at=proposed_at,
            )
            conn.execute(
                """
                INSERT INTO legacy_n_bound_proposals(
                    proposal_id, research_lineage_id, upper_bound_n,
                    proposal_event_seq, proposed_at, supporting_artefact_hash,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id,
                    research_lineage_id,
                    upper,
                    event_seq,
                    _utc_text(proposed_at),
                    digest,
                    notes or "",
                ),
            )
            return event_seq, event_hash
        except BaseException as exc:
            error = exc
            raise
        finally:
            if error is None:
                conn.execute("COMMIT")
            else:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
            conn.close()

    def register_trial(
        self,
        facts: TrialRegistrationFacts,
        *,
        allocation_id: Optional[str] = None,
        registered_at: Optional[datetime] = None,
        holdout_id: Optional[str] = None,
        reserved_at: Optional[datetime] = None,
        _inject_failure: Optional[str] = None,
    ) -> RegistrationResult:
        """Atomically register trial + debit (+ optional holdout RESERVED)."""
        facts = facts.normalized()
        if facts.billable and not allocation_id:
            raise RegistrationError("billable trials require allocation_id")
        if holdout_id and not facts.cohort_id:
            raise RegistrationError(
                "confirmatory registration requires cohort_id with holdout_id"
            )

        registered_text = _utc_text(registered_at)
        debit_id: Optional[str] = None
        units_spent = 0
        reservation: Optional[HoldoutReservation] = None

        conn = self._connect()
        error: BaseException | None = None
        try:
            conn.execute("BEGIN IMMEDIATE")

            programme = conn.execute(
                """
                SELECT research_lineage_id
                FROM programme_versions
                WHERE programme_version_id = ?
                """,
                (facts.programme_version_id,),
            ).fetchone()
            if programme is None:
                raise RegistrationError(
                    f"unknown programme_version_id {facts.programme_version_id!r}"
                )
            if str(programme[0]) != facts.research_lineage_id:
                raise RegistrationError(
                    "programme_version_id belongs to another research_lineage_id"
                )

            # System-derived reproduction identity (never caller Boolean/hash).
            repro_input_hash: Optional[str] = None
            repro_byte_identical: Optional[bool] = None
            if facts.trial_kind is TrialKind.REPRODUCTION:
                assert facts.reproduction_of_trial_id is not None
                ref = conn.execute(
                    """
                    SELECT research_lineage_id, immutable_input_hash
                    FROM trials
                    WHERE trial_id = ?
                    """,
                    (facts.reproduction_of_trial_id,),
                ).fetchone()
                if ref is None:
                    raise RegistrationError(
                        f"reproduction reference missing: "
                        f"{facts.reproduction_of_trial_id!r}"
                    )
                ref_lineage = str(ref[0])
                ref_hash = str(ref[1])
                if ref_lineage != facts.research_lineage_id:
                    raise RegistrationError(
                        "reproduction reference belongs to another "
                        "research_lineage_id"
                    )
                repro_input_hash = ref_hash
                repro_byte_identical = facts.immutable_input_hash == ref_hash

            selection_capable = derive_selection_capable(
                trial_kind=facts.trial_kind,
                synthetic=facts.synthetic,
                is_citation=facts.is_citation,
                reproduction_byte_identical=repro_byte_identical,
            )

            payload = {
                "trial_id": facts.trial_id,
                "research_lineage_id": facts.research_lineage_id,
                "programme_version_id": facts.programme_version_id,
                "cohort_id": facts.cohort_id,
                "trial_kind": facts.trial_kind.value,
                "selection_capable": bool(selection_capable),
                "synthetic": bool(facts.synthetic),
                "immutable_input_hash": facts.immutable_input_hash,
                "result_exposed": bool(facts.result_exposed),
                "preregistered": bool(facts.preregistered),
                "selection_unit_id": facts.selection_unit_id,
                "is_citation": bool(facts.is_citation),
                "reproduction_of_trial_id": facts.reproduction_of_trial_id,
                "reproduction_input_hash": repro_input_hash,
                "reproduction_byte_identical": repro_byte_identical,
                "billable": bool(facts.billable),
                "units_cost": int(facts.units_cost),
            }
            event_seq, event_hash = append_event(
                conn,
                event_type="trial_registered",
                payload=payload,
                recorded_at=registered_at,
            )
            if _inject_failure == "after_event":
                raise RegistrationError("injected failure after ledger event")

            conn.execute(
                """
                INSERT INTO trials(
                    trial_id, registration_event_seq, research_lineage_id,
                    programme_version_id, cohort_id, trial_kind,
                    selection_capable, synthetic, immutable_input_hash,
                    result_exposed, preregistered, selection_unit_id,
                    is_citation, reproduction_of_trial_id,
                    reproduction_input_hash, reproduction_byte_identical,
                    billable, units_cost, registered_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    facts.trial_id,
                    event_seq,
                    facts.research_lineage_id,
                    facts.programme_version_id,
                    facts.cohort_id,
                    facts.trial_kind.value,
                    1 if selection_capable else 0,
                    1 if facts.synthetic else 0,
                    facts.immutable_input_hash,
                    1 if facts.result_exposed else 0,
                    1 if facts.preregistered else 0,
                    facts.selection_unit_id,
                    1 if facts.is_citation else 0,
                    facts.reproduction_of_trial_id,
                    repro_input_hash,
                    (
                        None
                        if repro_byte_identical is None
                        else (1 if repro_byte_identical else 0)
                    ),
                    1 if facts.billable else 0,
                    int(facts.units_cost),
                    registered_text,
                ),
            )
            if _inject_failure == "after_trial":
                raise RegistrationError("injected failure after trial insert")

            if facts.billable:
                assert allocation_id is not None
                debit_id = f"debit_{facts.trial_id}"
                units_spent = int(facts.units_cost)
                insert_debit(
                    conn,
                    debit_id=debit_id,
                    allocation_id=str(allocation_id).strip(),
                    trial_id=facts.trial_id,
                    event_seq=event_seq,
                    units_spent=units_spent,
                    debited_at=registered_at,
                )
                if _inject_failure == "after_debit":
                    raise RegistrationError("injected failure after budget debit")

            if holdout_id:
                machine = HoldoutStateMachine(self.database_path)
                reservation = machine.reserve_on_connection(
                    conn,
                    holdout_id=holdout_id,
                    cohort_id=facts.cohort_id or "",
                    reserved_at=reserved_at or registered_at,
                )
                if _inject_failure == "after_holdout":
                    raise RegistrationError(
                        "injected failure after holdout reservation"
                    )

            if _inject_failure == "before_commit":
                raise RegistrationError("injected failure before commit")

            return RegistrationResult(
                trial_id=facts.trial_id,
                event_seq=event_seq,
                event_hash=event_hash,
                debit_id=debit_id,
                units_spent=units_spent,
                selection_capable=selection_capable,
                reservation=reservation,
                reproduction_input_hash=repro_input_hash,
                reproduction_byte_identical=repro_byte_identical,
            )
        except (BudgetError, LedgerHashError, TrialRegistrationError) as exc:
            error = exc
            raise RegistrationError(str(exc)) from exc
        except BaseException as exc:
            error = exc
            raise
        finally:
            if error is None:
                conn.execute("COMMIT")
            else:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
            conn.close()

    def finalize_trial(
        self,
        *,
        trial_id: str,
        execution_state: ExecutionState | str,
        result_exposed: bool,
        notes: str = "",
        recorded_at: Optional[datetime] = None,
        state_event_id: Optional[str] = None,
    ) -> tuple[int, str]:
        """Append a trial-state/finalization event (identity remains immutable)."""
        trial_id = str(trial_id).strip()
        if isinstance(execution_state, ExecutionState):
            state = execution_state
        else:
            state = ExecutionState(str(execution_state))
        if state is ExecutionState.REGISTERED:
            raise RegistrationError("finalization must change state beyond registered")

        conn = self._connect()
        error: BaseException | None = None
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT 1 FROM trials WHERE trial_id = ?",
                (trial_id,),
            ).fetchone()
            if row is None:
                raise RegistrationError(f"unknown trial {trial_id!r}")
            sid = state_event_id or f"tse_{uuid.uuid4().hex}"
            event_seq, event_hash = append_event(
                conn,
                event_type="trial_state_transition",
                payload={
                    "state_event_id": sid,
                    "trial_id": trial_id,
                    "execution_state": state.value,
                    "result_exposed": bool(result_exposed),
                    "notes": notes or "",
                },
                recorded_at=recorded_at,
            )
            conn.execute(
                """
                INSERT INTO trial_state_events(
                    state_event_id, trial_id, event_seq, execution_state,
                    result_exposed, recorded_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid,
                    trial_id,
                    event_seq,
                    state.value,
                    1 if result_exposed else 0,
                    _utc_text(recorded_at),
                    notes or "",
                ),
            )
            return event_seq, event_hash
        except BaseException as exc:
            error = exc
            raise
        finally:
            if error is None:
                conn.execute("COMMIT")
            else:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
            conn.close()
