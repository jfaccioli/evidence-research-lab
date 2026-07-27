"""Atomic trial + budget (+ optional confirmatory holdout) registration.

One SQLite transaction appends the ledger event, trial registration, and
budget debit together. Confirmatory cohort registration also performs the
PR2 AVAILABLE→RESERVED transition in that same transaction and returns the
reservation capability. Any failure rolls everything back.

Reproduction byte-identity is derived inside the registration transaction by
comparing the new trial's ``immutable_input_hash`` to the referenced trial's
stored hash. Legacy N bounds are proposal-only; PR3 has no public path to mint
verified human approval.

PR4: direct COMPLETED finalization is fail-closed without an exact immutable
completion-to-artefact link. Use ``complete_trial_with_run_bundle`` to stage/
seal and record digest + COMPLETED + link together. Caller-constructed
``SealedBundle`` instances are never treated as proof — registration reopens
the path under the explicit artefact root and derives a verified receipt.
Not wired into the P0 research pipeline.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional

from crl.db.schema import CURRENT_P1_SCHEMA_VERSION, connect_p1, get_schema_version
from crl.research.artifacts.bundle import (
    BundleError,
    BundleLineage,
    SealedBundle,
    VerifiedBundleReceipt,
    seal_bundle,
    verify_sealed_bundle_dir,
)
from crl.research.artifacts.paths import (
    ArtifactPathError,
    require_artifact_root,
    resolve_under_root,
)
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


@dataclass(frozen=True)
class BundleRegistrationResult:
    """Result of registering a verified artefact digest (+ optional supersession)."""

    artifact_id: str
    merkle_root: str
    seal_event_seq: int
    seal_event_hash: str
    supersession_event_seq: Optional[int]
    supersession_event_hash: Optional[str]
    receipt: VerifiedBundleReceipt


@dataclass(frozen=True)
class TrialCompletionWithBundleResult:
    """Atomic COMPLETED finalization linked to a sealed run bundle."""

    trial_id: str
    completion_event_seq: int
    completion_event_hash: str
    bundle: BundleRegistrationResult


def _sha256_digest(value: str, field: str) -> str:
    text = str(value).strip().lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise RegistrationError(f"{field} must be SHA-256 hex")
    return text


def _reopen_verified_receipt(
    *,
    artifact_root: str | Path,
    relative_root: str,
) -> VerifiedBundleReceipt:
    """Reopen under explicit root and derive all registration facts from disk."""
    try:
        root = require_artifact_root(artifact_root)
        path = resolve_under_root(root, relative_root)
    except ArtifactPathError as exc:
        raise RegistrationError(str(exc)) from exc
    if path.is_symlink() or not path.is_dir():
        raise RegistrationError(
            f"sealed bundle directory missing or not a directory: {relative_root}"
        )
    try:
        return verify_sealed_bundle_dir(
            path, expected_relative_root=relative_root
        )
    except BundleError as exc:
        raise RegistrationError(str(exc)) from exc


class TrialLedger:
    """Append-only analytical-trial ledger over an explicitly migrated v3+ DB."""

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
                raise RegistrationError("trial ledger requires schema v3+")
            self._schema_version = version
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
        """Append a trial-state/finalization event (identity remains immutable).

        On schema v4+, public COMPLETED finalization is always fail-closed.
        Use ``complete_trial_with_run_bundle`` which records the exact
        completion-to-artefact link in the same transaction.
        """
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
            version = get_schema_version(conn) or 0
            if state is ExecutionState.COMPLETED and int(version) >= 4:
                raise RegistrationError(
                    "COMPLETED finalization on schema v4+ requires a sealed "
                    "run bundle via complete_trial_with_run_bundle"
                )
            row = conn.execute(
                "SELECT 1 FROM trials WHERE trial_id = ?",
                (trial_id,),
            ).fetchone()
            if row is None:
                raise RegistrationError(f"unknown trial {trial_id!r}")
            if state is ExecutionState.COMPLETED:
                prior = conn.execute(
                    """
                    SELECT 1 FROM trial_state_events
                    WHERE trial_id = ? AND execution_state = 'completed'
                    """,
                    (trial_id,),
                ).fetchone()
                if prior is not None:
                    raise RegistrationError(
                        f"trial already has a completed transition: {trial_id!r}"
                    )
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

    def _insert_verified_artifact_on_conn(
        self,
        conn: sqlite3.Connection,
        *,
        receipt: VerifiedBundleReceipt,
        recorded_at: Optional[datetime] = None,
    ) -> BundleRegistrationResult:
        """Register verified receipt (+ supersession) inside caller's txn."""
        version = get_schema_version(conn) or 0
        if int(version) < 4:
            raise RegistrationError("artifact digests require schema v4")

        lineage = receipt.lineage
        programme = conn.execute(
            """
            SELECT research_lineage_id
            FROM programme_versions
            WHERE programme_version_id = ?
            """,
            (lineage.programme_version_id,),
        ).fetchone()
        if programme is None:
            raise RegistrationError(
                f"unknown programme_version_id {lineage.programme_version_id!r}"
            )
        if str(programme[0]) != lineage.research_lineage_id:
            raise RegistrationError(
                "programme_version_id belongs to another research_lineage_id"
            )

        if receipt.bundle_kind == "run":
            if lineage.trial_id is None or receipt.run_id is None:
                raise RegistrationError("run bundles require trial_id and run_id")
            trial = conn.execute(
                """
                SELECT research_lineage_id, programme_version_id
                FROM trials WHERE trial_id = ?
                """,
                (lineage.trial_id,),
            ).fetchone()
            if trial is None:
                raise RegistrationError(f"unknown trial_id {lineage.trial_id!r}")
            if str(trial[0]) != lineage.research_lineage_id:
                raise RegistrationError("trial research_lineage_id mismatch")
            if str(trial[1]) != lineage.programme_version_id:
                raise RegistrationError("trial programme_version_id mismatch")
        elif lineage.trial_id is not None:
            trial = conn.execute(
                """
                SELECT research_lineage_id, programme_version_id
                FROM trials WHERE trial_id = ?
                """,
                (lineage.trial_id,),
            ).fetchone()
            if trial is None:
                raise RegistrationError(f"unknown trial_id {lineage.trial_id!r}")
            if str(trial[0]) != lineage.research_lineage_id:
                raise RegistrationError("trial research_lineage_id mismatch")
            if str(trial[1]) != lineage.programme_version_id:
                raise RegistrationError("trial programme_version_id mismatch")

        if receipt.cohort_id is not None:
            cohort = conn.execute(
                """
                SELECT c.programme_version_id, p.research_lineage_id
                FROM cohorts c
                JOIN programme_versions p
                  ON p.programme_version_id = c.programme_version_id
                WHERE c.cohort_id = ?
                  AND c.programme_version_id = ?
                """,
                (receipt.cohort_id, lineage.programme_version_id),
            ).fetchone()
            if cohort is None:
                raise RegistrationError(
                    f"unknown cohort_id {receipt.cohort_id!r} for "
                    f"programme_version_id {lineage.programme_version_id!r}"
                )
            if str(cohort[1]) != lineage.research_lineage_id:
                raise RegistrationError(
                    "cohort programme/research lineage mismatch"
                )

        if receipt.is_correction:
            if not receipt.supersedes_artifact_id:
                raise RegistrationError(
                    "correction requires supersedes_artifact_id"
                )
            prior = conn.execute(
                """
                SELECT research_lineage_id, bundle_kind, run_id, cohort_id
                FROM artifact_digests
                WHERE artifact_id = ?
                """,
                (receipt.supersedes_artifact_id,),
            ).fetchone()
            if prior is None:
                raise RegistrationError(
                    "correction references unknown prior artifact_id"
                )
            if str(prior[0]) != lineage.research_lineage_id:
                raise RegistrationError(
                    "correction must remain in the same research lineage"
                )
            if str(prior[1]) != receipt.bundle_kind:
                raise RegistrationError(
                    "correction must supersede same bundle_kind"
                )
            # Run corrections require a new run_id artefact path identity.
            if receipt.bundle_kind == "run" and receipt.run_id == prior[2]:
                raise RegistrationError(
                    "correction must use a new run_id artefact identity"
                )
            # Cohort corrections may retain logical cohort_id with new artifact_id.

        existing_id = conn.execute(
            "SELECT 1 FROM artifact_digests WHERE artifact_id = ?",
            (receipt.artifact_id,),
        ).fetchone()
        if existing_id is not None:
            raise RegistrationError(
                f"artifact_id already registered: {receipt.artifact_id}"
            )
        if receipt.run_id is not None:
            run_hit = conn.execute(
                "SELECT 1 FROM artifact_digests WHERE run_id = ?",
                (receipt.run_id,),
            ).fetchone()
            if run_hit is not None:
                raise RegistrationError(
                    f"run_id already has a sealed bundle: {receipt.run_id!r}"
                )
        rel_hit = conn.execute(
            "SELECT 1 FROM artifact_digests WHERE relative_root = ?",
            (receipt.relative_root,),
        ).fetchone()
        if rel_hit is not None:
            raise RegistrationError(
                f"relative_root already registered: {receipt.relative_root!r}"
            )

        seal_payload = {
            "artifact_id": receipt.artifact_id,
            "merkle_root": receipt.merkle_root,
            "bundle_kind": receipt.bundle_kind,
            "run_id": receipt.run_id,
            "cohort_id": receipt.cohort_id,
            "trial_id": lineage.trial_id,
            "research_lineage_id": lineage.research_lineage_id,
            "programme_version_id": lineage.programme_version_id,
            "manifest_sha256": receipt.manifest_sha256,
            "config_hash": lineage.config_hash,
            "candidate_spec_hash": lineage.candidate_spec_hash,
            "split_manifest_hash": lineage.split_manifest_hash,
            "data_hash": lineage.data_hash,
            "feature_hash": lineage.feature_hash,
            "dependency_lock_hash": lineage.dependency_lock_hash,
            "relative_root": receipt.relative_root,
            "byte_size": receipt.byte_size,
            "is_correction": bool(receipt.is_correction),
            "supersedes_artifact_id": receipt.supersedes_artifact_id,
        }
        seal_seq, seal_hash = append_event(
            conn,
            event_type="artifact_bundle_sealed",
            payload=seal_payload,
            recorded_at=recorded_at,
        )
        conn.execute(
            """
            INSERT INTO artifact_digests(
                artifact_id, merkle_root, bundle_kind, run_id, cohort_id,
                trial_id, research_lineage_id, programme_version_id,
                manifest_sha256, config_hash, candidate_spec_hash,
                split_manifest_hash, data_hash, feature_hash,
                dependency_lock_hash, relative_root, byte_size,
                registration_event_seq, supersedes_artifact_id,
                is_correction, sealed_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                receipt.artifact_id,
                receipt.merkle_root,
                receipt.bundle_kind,
                receipt.run_id,
                receipt.cohort_id,
                lineage.trial_id,
                lineage.research_lineage_id,
                lineage.programme_version_id,
                receipt.manifest_sha256,
                lineage.config_hash,
                lineage.candidate_spec_hash,
                lineage.split_manifest_hash,
                lineage.data_hash,
                lineage.feature_hash,
                lineage.dependency_lock_hash,
                receipt.relative_root,
                int(receipt.byte_size),
                seal_seq,
                receipt.supersedes_artifact_id,
                1 if receipt.is_correction else 0,
                receipt.sealed_at,
            ),
        )

        super_seq: Optional[int] = None
        super_hash: Optional[str] = None
        if receipt.is_correction:
            assert receipt.supersedes_artifact_id is not None
            super_seq, super_hash = append_event(
                conn,
                event_type="artifact_bundle_supersession",
                payload={
                    "new_artifact_id": receipt.artifact_id,
                    "supersedes_artifact_id": receipt.supersedes_artifact_id,
                    "new_merkle_root": receipt.merkle_root,
                    "research_lineage_id": lineage.research_lineage_id,
                    "bundle_kind": receipt.bundle_kind,
                    "run_id": receipt.run_id,
                    "cohort_id": receipt.cohort_id,
                },
                recorded_at=recorded_at,
            )

        return BundleRegistrationResult(
            artifact_id=receipt.artifact_id,
            merkle_root=receipt.merkle_root,
            seal_event_seq=seal_seq,
            seal_event_hash=seal_hash,
            supersession_event_seq=super_seq,
            supersession_event_hash=super_hash,
            receipt=receipt,
        )

    def register_sealed_bundle(
        self,
        *,
        artifact_root: str | Path,
        relative_root: str,
        recorded_at: Optional[datetime] = None,
        _inject_failure: Optional[str] = None,
    ) -> BundleRegistrationResult:
        """Reopen+verify a sealed directory, then register derived facts only.

        Never trusts a caller-constructed ``SealedBundle`` as proof.
        """
        receipt = _reopen_verified_receipt(
            artifact_root=artifact_root,
            relative_root=relative_root,
        )
        conn = self._connect()
        error: BaseException | None = None
        try:
            conn.execute("BEGIN IMMEDIATE")
            result = self._insert_verified_artifact_on_conn(
                conn, receipt=receipt, recorded_at=recorded_at
            )
            if _inject_failure == "before_commit":
                raise RegistrationError("injected failure before bundle commit")
            return result
        except (BundleError, LedgerHashError) as exc:
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

    def seal_and_register_bundle(
        self,
        *,
        artifact_root: str | Path,
        bundle_kind: str,
        sources: Mapping[str, str | Path],
        lineage: BundleLineage,
        run_id: Optional[str] = None,
        cohort_id: Optional[str] = None,
        is_correction: bool = False,
        supersedes_artifact_id: Optional[str] = None,
        sealed_at: Optional[datetime] = None,
        recorded_at: Optional[datetime] = None,
        _inject_db_failure: Optional[str] = None,
    ) -> BundleRegistrationResult:
        """Seal on disk then reopen/verify/register; DB failure cleans this seal only."""
        sealed = seal_bundle(
            artifact_root=artifact_root,
            bundle_kind=bundle_kind,
            sources=sources,
            lineage=lineage,
            run_id=run_id,
            cohort_id=cohort_id,
            is_correction=is_correction,
            supersedes_artifact_id=supersedes_artifact_id,
            sealed_at=sealed_at,
        )
        try:
            return self.register_sealed_bundle(
                artifact_root=artifact_root,
                relative_root=sealed.relative_root,
                recorded_at=recorded_at,
                _inject_failure=_inject_db_failure,
            )
        except Exception:
            from crl.research.artifacts.bundle import _best_effort_rmtree

            root = require_artifact_root(artifact_root)
            if sealed.absolute_root.exists():
                _best_effort_rmtree(sealed.absolute_root, root=root)
            raise

    def complete_trial_with_run_bundle(
        self,
        *,
        trial_id: str,
        artifact_root: str | Path,
        run_id: str,
        sources: Mapping[str, str | Path],
        lineage: BundleLineage,
        result_exposed: bool = True,
        notes: str = "",
        recorded_at: Optional[datetime] = None,
        state_event_id: Optional[str] = None,
        is_correction: bool = False,
        supersedes_artifact_id: Optional[str] = None,
        _inject_db_failure: Optional[str] = None,
        _inject_bundle_failure: Optional[str] = None,
    ) -> TrialCompletionWithBundleResult:
        """Stage/seal a run bundle and record digest + COMPLETED + link atomically.

        Bundle failure → no COMPLETED event and no digest row.
        DB failure → rollback digest + COMPLETED + link; may cleanup only the
        bundle created by this call (never a pre-existing target).
        """
        trial_id = str(trial_id).strip()
        run_id = str(run_id).strip()
        if not trial_id or not run_id:
            raise RegistrationError("trial_id and run_id are required")

        # Ensure lineage.trial_id matches.
        lineage_n = lineage.normalized()
        if lineage_n.trial_id is None:
            lineage_n = BundleLineage(
                research_lineage_id=lineage_n.research_lineage_id,
                programme_version_id=lineage_n.programme_version_id,
                config_hash=lineage_n.config_hash,
                candidate_spec_hash=lineage_n.candidate_spec_hash,
                split_manifest_hash=lineage_n.split_manifest_hash,
                data_hash=lineage_n.data_hash,
                feature_hash=lineage_n.feature_hash,
                dependency_lock_hash=lineage_n.dependency_lock_hash,
                trial_id=trial_id,
            )
        elif lineage_n.trial_id != trial_id:
            raise RegistrationError("lineage.trial_id must match trial_id")

        if _inject_bundle_failure == "before_seal":
            raise RegistrationError("injected bundle failure before seal")

        sealed = seal_bundle(
            artifact_root=artifact_root,
            bundle_kind="run",
            sources=sources,
            lineage=lineage_n,
            run_id=run_id,
            is_correction=is_correction,
            supersedes_artifact_id=supersedes_artifact_id,
            sealed_at=recorded_at,
        )
        if _inject_bundle_failure == "after_seal":
            from crl.research.artifacts.bundle import _best_effort_rmtree

            root = require_artifact_root(artifact_root)
            _best_effort_rmtree(sealed.absolute_root, root=root)
            raise RegistrationError("injected bundle failure after seal")

        # Always re-derive facts from disk under the explicit root.
        try:
            receipt = _reopen_verified_receipt(
                artifact_root=artifact_root,
                relative_root=sealed.relative_root,
            )
        except RegistrationError:
            from crl.research.artifacts.bundle import _best_effort_rmtree

            root = require_artifact_root(artifact_root)
            if sealed.absolute_root.exists():
                _best_effort_rmtree(sealed.absolute_root, root=root)
            raise

        conn = self._connect()
        error: BaseException | None = None
        try:
            conn.execute("BEGIN IMMEDIATE")
            version = get_schema_version(conn) or 0
            if int(version) < 4:
                raise RegistrationError(
                    "complete_trial_with_run_bundle requires schema v4"
                )
            row = conn.execute(
                """
                SELECT research_lineage_id, programme_version_id
                FROM trials WHERE trial_id = ?
                """,
                (trial_id,),
            ).fetchone()
            if row is None:
                raise RegistrationError(f"unknown trial {trial_id!r}")
            if str(row[0]) != lineage_n.research_lineage_id:
                raise RegistrationError("trial research_lineage_id mismatch")
            if str(row[1]) != lineage_n.programme_version_id:
                raise RegistrationError("trial programme_version_id mismatch")

            # Reject second completed transition before writes.
            prior_completed = conn.execute(
                """
                SELECT 1 FROM trial_state_events
                WHERE trial_id = ? AND execution_state = 'completed'
                """,
                (trial_id,),
            ).fetchone()
            if prior_completed is not None:
                raise RegistrationError(
                    f"trial already has a completed transition: {trial_id!r}"
                )
            prior_link = conn.execute(
                "SELECT 1 FROM trial_completion_links WHERE trial_id = ?",
                (trial_id,),
            ).fetchone()
            if prior_link is not None:
                raise RegistrationError(
                    f"trial already has a completion link: {trial_id!r}"
                )

            if receipt.lineage.trial_id != trial_id:
                raise RegistrationError("verified receipt trial_id mismatch")
            if receipt.run_id != run_id:
                raise RegistrationError("verified receipt run_id mismatch")
            if receipt.lineage.research_lineage_id != lineage_n.research_lineage_id:
                raise RegistrationError("verified receipt research_lineage_id mismatch")
            if receipt.lineage.programme_version_id != lineage_n.programme_version_id:
                raise RegistrationError("verified receipt programme_version_id mismatch")

            bundle_result = self._insert_verified_artifact_on_conn(
                conn, receipt=receipt, recorded_at=recorded_at
            )
            if _inject_db_failure == "after_digest":
                raise RegistrationError("injected failure after digest insert")

            sid = state_event_id or f"tse_{uuid.uuid4().hex}"
            event_seq, event_hash = append_event(
                conn,
                event_type="trial_state_transition",
                payload={
                    "state_event_id": sid,
                    "trial_id": trial_id,
                    "execution_state": ExecutionState.COMPLETED.value,
                    "result_exposed": bool(result_exposed),
                    "notes": notes or "",
                    "artifact_id": receipt.artifact_id,
                    "artifact_merkle_root": receipt.merkle_root,
                    "run_id": run_id,
                },
                recorded_at=recorded_at,
            )
            # Exact immutable completion link BEFORE state row (trigger requires it).
            conn.execute(
                """
                INSERT INTO trial_completion_links(
                    trial_id, completion_event_seq, artifact_id, run_id,
                    registration_event_seq, state_event_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    trial_id,
                    event_seq,
                    receipt.artifact_id,
                    run_id,
                    bundle_result.seal_event_seq,
                    sid,
                ),
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
                    ExecutionState.COMPLETED.value,
                    1 if result_exposed else 0,
                    _utc_text(recorded_at),
                    notes or "",
                ),
            )
            if _inject_db_failure == "before_commit":
                raise RegistrationError(
                    "injected failure before completion commit"
                )
            return TrialCompletionWithBundleResult(
                trial_id=trial_id,
                completion_event_seq=event_seq,
                completion_event_hash=event_hash,
                bundle=bundle_result,
            )
        except (BundleError, LedgerHashError) as exc:
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
                from crl.research.artifacts.bundle import _best_effort_rmtree

                root = require_artifact_root(artifact_root)
                if sealed.absolute_root.exists():
                    _best_effort_rmtree(sealed.absolute_root, root=root)
            conn.close()
