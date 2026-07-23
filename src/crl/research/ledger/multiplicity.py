"""Policy-derived multiplicity (N_global / N_cohort). Never caller Booleans.

Rules (design §§3–4):
- visible selection-capable variants count;
- unregistered sensitivity counts and raises a promotion-blocking violation;
- synthetic fixtures, buy-and-hold, citations, verified byte-identical
  reproductions do not add a selection unit;
- base + 2x cost diagnostics share one selection-unit identity;
- changed-input reruns count;
- aborted evaluations count when exposure may have occurred;
- no correlation discount;
- proposed legacy bounds are diagnostic only and never enter N_global;
- absence of **verified** legacy approval always blocks promotion inputs
  (PR3 has no public verified-approval mint path).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

from crl.research.ledger.hash_chain import verify_hash_chain
from crl.research.ledger.trials import TrialKind


@dataclass(frozen=True)
class GovernanceViolation:
    code: str
    trial_id: str
    detail: str


@dataclass(frozen=True)
class MultiplicityCensus:
    """Multiple-testing inputs (unwired to the live P0 pipeline)."""

    research_lineage_id: str
    n_global: int
    n_cohort: int
    n_global_ledger: int
    # Authoritative verified legacy bound only. Always None in PR3 — no public
    # verified-approval path exists. Proposals never populate this field.
    legacy_bound_n: Optional[int]
    # Diagnostic proposed bound (never added into N_global).
    proposed_legacy_bound_n: Optional[int]
    correlation_discount: float
    counting_selection_unit_ids: tuple[str, ...]
    cohort_selection_unit_ids: tuple[str, ...]
    governance_violations: tuple[GovernanceViolation, ...]
    promotion_blocked: bool
    promotion_block_reasons: tuple[str, ...]
    hash_chain_ok: bool


@dataclass(frozen=True)
class _CountingTrial:
    trial_id: str
    cohort_id: Optional[str]
    programme_version_id: str
    trial_kind: str
    selection_unit_id: str
    immutable_input_hash: str


_COST_KINDS = frozenset(
    {TrialKind.COST_STRESS_BASE.value, TrialKind.COST_STRESS_2X.value}
)


def _effective_exposed(reg_exposed: int, state_exposed_flags: list[int]) -> bool:
    if int(reg_exposed) == 1:
        return True
    return any(int(x) == 1 for x in state_exposed_flags)


def _latest_execution_state(
    states: list[tuple[int, str, int]],
) -> Optional[str]:
    if not states:
        return None
    states_sorted = sorted(states, key=lambda s: s[0])
    return states_sorted[-1][1]


def _trial_adds_selection_unit(
    *,
    trial_kind: str,
    selection_capable: int,
    synthetic: int,
    is_citation: int,
    result_exposed: int,
    reproduction_byte_identical: Optional[int],
    state_rows: list[tuple[int, str, int]],
) -> bool:
    if int(synthetic) == 1 or trial_kind == TrialKind.SYNTHETIC_FIXTURE.value:
        return False
    if int(is_citation) == 1 or trial_kind == TrialKind.CITATION.value:
        return False
    if trial_kind == TrialKind.BENCHMARK_BH.value:
        return False
    if trial_kind == TrialKind.REPRODUCTION.value:
        # Only system-derived equal stored hashes exclude deterministic
        # reproductions. A changed hash is selection-capable.
        if reproduction_byte_identical is not None and int(reproduction_byte_identical) == 1:
            return False
        return True

    exposed = _effective_exposed(
        result_exposed, [s[2] for s in state_rows]
    )
    latest = _latest_execution_state(state_rows)

    if trial_kind == TrialKind.ABORTED_EVAL.value or latest == "aborted":
        # Aborted evaluations count only when exposure may have occurred.
        return exposed

    if trial_kind in _COST_KINDS:
        return True

    if trial_kind == TrialKind.CHANGED_INPUT_RERUN.value:
        return True

    # Visible selection-capable hypothesis / parameter / feature / threshold /
    # horizon / interaction / aggregation / sensitivity variants count.
    return int(selection_capable) == 1


def _selection_unit_keys(
    trials: list[_CountingTrial],
) -> tuple[
    dict[str, tuple[str, str]],
    list[GovernanceViolation],
]:
    """Derive conservative unit keys and expose unsafe caller collisions.

    A shared caller identity is accepted only for the intended base/2x cost
    bundle: at most one non-cost anchor, no duplicate cost kind, and the same
    programme, cohort, and sealed-input hash. Any other collision counts each
    trial separately and blocks promotion instead of silently understating N.
    """
    grouped: dict[str, list[_CountingTrial]] = {}
    for trial in trials:
        grouped.setdefault(trial.selection_unit_id, []).append(trial)

    keys: dict[str, tuple[str, str]] = {}
    violations: list[GovernanceViolation] = []
    for declared_id, group in grouped.items():
        if len(group) == 1:
            keys[group[0].trial_id] = ("declared", declared_id)
            continue

        cost_trials = [t for t in group if t.trial_kind in _COST_KINDS]
        non_cost_trials = [t for t in group if t.trial_kind not in _COST_KINDS]
        contexts = {
            (t.programme_version_id, t.cohort_id, t.immutable_input_hash)
            for t in group
        }
        cost_kinds = [t.trial_kind for t in cost_trials]
        valid_cost_bundle = (
            bool(cost_trials)
            and len(non_cost_trials) <= 1
            and len(cost_kinds) == len(set(cost_kinds))
            and len(contexts) == 1
        )
        if valid_cost_bundle:
            for trial in group:
                keys[trial.trial_id] = ("declared", declared_id)
            continue

        trial_ids = tuple(sorted(t.trial_id for t in group))
        violations.append(
            GovernanceViolation(
                code="invalid_selection_unit_collision",
                trial_id=trial_ids[0],
                detail=(
                    f"selection_unit_id {declared_id!r} was shared by "
                    f"incompatible trials {trial_ids}; each trial counts "
                    "separately and promotion is blocked"
                ),
            )
        )
        for trial in group:
            keys[trial.trial_id] = ("trial", trial.trial_id)
    return keys, violations


def _render_unit_key(key: tuple[str, str]) -> str:
    kind, value = key
    return value if kind == "declared" else f"trial:{value}"


def compute_multiplicity(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
    cohort_id: Optional[str] = None,
) -> MultiplicityCensus:
    """Derive N_global and N_cohort with no correlation discount."""
    lineage = str(research_lineage_id).strip()
    if not lineage:
        raise ValueError("research_lineage_id required")

    chain = verify_hash_chain(conn)
    trials = conn.execute(
        """
        SELECT trial_id, cohort_id, trial_kind, selection_capable, synthetic,
               result_exposed, preregistered, selection_unit_id, is_citation,
               reproduction_byte_identical, immutable_input_hash,
               programme_version_id
        FROM trials
        WHERE research_lineage_id = ?
        ORDER BY registration_event_seq ASC
        """,
        (lineage,),
    ).fetchall()

    state_by_trial: dict[str, list[tuple[int, str, int]]] = {}
    for row in conn.execute(
        """
        SELECT tse.trial_id, tse.event_seq, tse.execution_state, tse.result_exposed
        FROM trial_state_events tse
        JOIN trials t ON t.trial_id = tse.trial_id
        WHERE t.research_lineage_id = ?
        ORDER BY tse.event_seq ASC
        """,
        (lineage,),
    ).fetchall():
        state_by_trial.setdefault(str(row[0]), []).append(
            (int(row[1]), str(row[2]), int(row[3]))
        )

    counting_trials: list[_CountingTrial] = []
    violations: list[GovernanceViolation] = []

    for row in trials:
        trial_id = str(row[0])
        trial_cohort = row[1]
        trial_kind = str(row[2])
        selection_capable = int(row[3])
        synthetic = int(row[4])
        result_exposed = int(row[5])
        preregistered = int(row[6])
        selection_unit_id = str(row[7])
        is_citation = int(row[8])
        repro_ident = row[9]
        states = state_by_trial.get(trial_id, [])

        if (
            trial_kind == TrialKind.SENSITIVITY_POINT.value
            and preregistered == 0
            and synthetic == 0
            and is_citation == 0
        ):
            violations.append(
                GovernanceViolation(
                    code="unregistered_sensitivity_neighbour",
                    trial_id=trial_id,
                    detail=(
                        "ad-hoc unregistered sensitivity neighbour counts and "
                        "blocks promotion pending human review"
                    ),
                )
            )

        counts = _trial_adds_selection_unit(
            trial_kind=trial_kind,
            selection_capable=selection_capable,
            synthetic=synthetic,
            is_citation=is_citation,
            result_exposed=result_exposed,
            reproduction_byte_identical=(
                None if repro_ident is None else int(repro_ident)
            ),
            state_rows=states,
        )
        if not counts:
            continue
        counting_trials.append(
            _CountingTrial(
                trial_id=trial_id,
                cohort_id=None if trial_cohort is None else str(trial_cohort),
                programme_version_id=str(row[11]),
                trial_kind=trial_kind,
                selection_unit_id=selection_unit_id,
                immutable_input_hash=str(row[10]),
            )
        )

    unit_key_by_trial, collision_violations = _selection_unit_keys(counting_trials)
    violations.extend(collision_violations)
    counting_units = {
        unit_key_by_trial[trial.trial_id] for trial in counting_trials
    }
    if cohort_id is not None:
        cohort_units = {
            unit_key_by_trial[trial.trial_id]
            for trial in counting_trials
            if trial.cohort_id == cohort_id
        }
    else:
        cohort_units = {
            unit_key_by_trial[trial.trial_id]
            for trial in counting_trials
            if trial.cohort_id is not None
        }
    n_cohort = len(cohort_units)
    cohort_ids_out = tuple(sorted(_render_unit_key(k) for k in cohort_units))

    # Proposals are diagnostic only — never authoritative for N_global.
    proposal_row = conn.execute(
        """
        SELECT upper_bound_n
        FROM legacy_n_bound_proposals
        WHERE research_lineage_id = ?
        """,
        (lineage,),
    ).fetchone()
    proposed_legacy: Optional[int]
    if proposal_row is None:
        proposed_legacy = None
    else:
        proposed_legacy = int(proposal_row[0])

    # PR3 has no verified human-approval table/path. Authoritative bound is
    # always absent; proposals must never be added into N_global.
    legacy_bound: Optional[int] = None
    n_ledger = len(counting_units)
    n_global = n_ledger

    block_reasons: list[str] = []
    # Fail closed until a separately reviewed immutable human-approval path
    # exists (not implemented in PR3; no agent mint path).
    block_reasons.append("missing_verified_legacy_n_approval")
    if not chain.ok:
        block_reasons.append("hash_chain_integrity_failure")
    if violations:
        block_reasons.append("open_governance_violations")

    return MultiplicityCensus(
        research_lineage_id=lineage,
        n_global=n_global,
        n_cohort=n_cohort,
        n_global_ledger=n_ledger,
        legacy_bound_n=legacy_bound,
        proposed_legacy_bound_n=proposed_legacy,
        correlation_discount=1.0,  # no correlation discount
        counting_selection_unit_ids=tuple(
            sorted(_render_unit_key(k) for k in counting_units)
        ),
        cohort_selection_unit_ids=cohort_ids_out,
        governance_violations=tuple(violations),
        promotion_blocked=True,  # always blocked: no verified legacy approval
        promotion_block_reasons=tuple(block_reasons),
        hash_chain_ok=chain.ok,
    )
