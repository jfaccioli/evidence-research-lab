"""Factual analytical-trial registration (append-only identity facts).

``counts_for_multiplicity`` is **never** stored. Policy derives counts from
immutable factual fields and trial-state events.

Reproduction byte-identity is **never** caller-authoritative. Callers may name
a ``reproduction_of_trial_id``; registration derives equality by comparing the
new trial's ``immutable_input_hash`` to the referenced row's stored hash.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TrialKind(str, Enum):
    HYPOTHESIS_EVAL = "hypothesis_eval"
    SENSITIVITY_POINT = "sensitivity_point"
    PARAMETER_VARIANT = "parameter_variant"
    FEATURE_VARIANT = "feature_variant"
    THRESHOLD_VARIANT = "threshold_variant"
    HORIZON_VARIANT = "horizon_variant"
    INTERACTION_VARIANT = "interaction_variant"
    AGGREGATION_VARIANT = "aggregation_variant"
    REPRODUCTION = "reproduction"
    SYNTHETIC_FIXTURE = "synthetic_fixture"
    BENCHMARK_BH = "benchmark_bh"
    COST_STRESS_BASE = "cost_stress_base"
    COST_STRESS_2X = "cost_stress_2x"
    ABORTED_EVAL = "aborted_eval"
    CITATION = "citation"
    CHANGED_INPUT_RERUN = "changed_input_rerun"


class ExecutionState(str, Enum):
    REGISTERED = "registered"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"
    ERROR = "error"


# Kinds that can form selection-capable analytical variants.
_VARIANT_KINDS = frozenset(
    {
        TrialKind.HYPOTHESIS_EVAL,
        TrialKind.SENSITIVITY_POINT,
        TrialKind.PARAMETER_VARIANT,
        TrialKind.FEATURE_VARIANT,
        TrialKind.THRESHOLD_VARIANT,
        TrialKind.HORIZON_VARIANT,
        TrialKind.INTERACTION_VARIANT,
        TrialKind.AGGREGATION_VARIANT,
        TrialKind.COST_STRESS_BASE,
        TrialKind.COST_STRESS_2X,
        TrialKind.ABORTED_EVAL,
        TrialKind.CHANGED_INPUT_RERUN,
        TrialKind.REPRODUCTION,
    }
)


class TrialRegistrationError(ValueError):
    """Trial factual fields are invalid or incomplete."""


def _sha256(value: str, field: str) -> str:
    text = str(value).strip()
    if (
        len(text) != 64
        or text != text.lower()
        or any(ch not in "0123456789abcdef" for ch in text)
    ):
        raise TrialRegistrationError(f"{field} must be lowercase SHA-256 hex")
    return text


def _identifier(value: str, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise TrialRegistrationError(f"{field} must be non-empty")
    return text


def derive_selection_capable(
    *,
    trial_kind: TrialKind,
    synthetic: bool,
    is_citation: bool,
    reproduction_byte_identical: Optional[bool],
) -> bool:
    """System-derived selection capability (not a multiplicity count).

    ``reproduction_byte_identical`` must be system-derived (equal stored
    immutable input hashes), never a caller force-flag.
    """
    if synthetic or is_citation:
        return False
    if trial_kind in (
        TrialKind.SYNTHETIC_FIXTURE,
        TrialKind.BENCHMARK_BH,
        TrialKind.CITATION,
    ):
        return False
    if trial_kind is TrialKind.REPRODUCTION and reproduction_byte_identical is True:
        return False
    return trial_kind in _VARIANT_KINDS


@dataclass(frozen=True)
class TrialRegistrationFacts:
    """Immutable factual inputs for one analytical trial registration.

    Callers may supply ``reproduction_of_trial_id`` for reproduction trials.
    They must **not** supply byte-identity or the referenced input hash —
    those are system-derived at registration time from the referenced row.
    """

    trial_id: str
    research_lineage_id: str
    programme_version_id: str
    trial_kind: TrialKind
    immutable_input_hash: str
    selection_unit_id: str
    cohort_id: Optional[str] = None
    synthetic: bool = False
    result_exposed: bool = False
    preregistered: bool = True
    is_citation: bool = False
    reproduction_of_trial_id: Optional[str] = None
    billable: bool = True
    units_cost: int = 1

    def normalized(self) -> "TrialRegistrationFacts":
        kind = self.trial_kind
        if not isinstance(kind, TrialKind):
            kind = TrialKind(str(kind))
        trial_id = _identifier(self.trial_id, "trial_id")
        research_lineage_id = _identifier(
            self.research_lineage_id, "research_lineage_id"
        )
        programme_version_id = _identifier(
            self.programme_version_id, "programme_version_id"
        )
        selection_unit_id = _identifier(self.selection_unit_id, "selection_unit_id")
        immutable_input_hash = _sha256(
            self.immutable_input_hash, "immutable_input_hash"
        )
        cohort_id = (
            _identifier(self.cohort_id, "cohort_id") if self.cohort_id else None
        )
        units_cost = int(self.units_cost)
        if units_cost < 0:
            raise TrialRegistrationError("units_cost must be >= 0")
        if bool(self.billable) and units_cost < 1:
            raise TrialRegistrationError("billable trials require units_cost >= 1")

        repro_of = self.reproduction_of_trial_id
        if kind is TrialKind.REPRODUCTION:
            if not repro_of:
                raise TrialRegistrationError(
                    "reproduction trials require reproduction_of_trial_id"
                )
            repro_of = _identifier(repro_of, "reproduction_of_trial_id")
        else:
            if repro_of is not None:
                raise TrialRegistrationError(
                    "reproduction_of_trial_id only valid for reproduction trials"
                )

        # Citations / fixtures are never billable selection units.
        billable = bool(self.billable)
        synthetic = bool(self.synthetic) or kind is TrialKind.SYNTHETIC_FIXTURE
        is_citation = bool(self.is_citation) or kind is TrialKind.CITATION
        if synthetic or is_citation or kind is TrialKind.BENCHMARK_BH:
            billable = False
            units_cost = 0

        return TrialRegistrationFacts(
            trial_id=trial_id,
            research_lineage_id=research_lineage_id,
            programme_version_id=programme_version_id,
            trial_kind=kind,
            immutable_input_hash=immutable_input_hash,
            selection_unit_id=selection_unit_id,
            cohort_id=cohort_id,
            synthetic=synthetic,
            result_exposed=bool(self.result_exposed),
            preregistered=bool(self.preregistered),
            is_citation=is_citation,
            reproduction_of_trial_id=repro_of,
            billable=billable,
            units_cost=units_cost,
        )

    def selection_capable(
        self, *, reproduction_byte_identical: Optional[bool] = None
    ) -> bool:
        """Derive selection capability.

        For reproduction trials, pass the **system-derived** byte-identity
        flag. Callers cannot force exclusion via a registration Boolean.
        """
        kind = (
            self.trial_kind
            if isinstance(self.trial_kind, TrialKind)
            else TrialKind(str(self.trial_kind))
        )
        return derive_selection_capable(
            trial_kind=kind,
            synthetic=bool(self.synthetic),
            is_citation=bool(self.is_citation),
            reproduction_byte_identical=reproduction_byte_identical,
        )
