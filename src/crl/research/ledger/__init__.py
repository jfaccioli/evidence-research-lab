"""PR3/PR4 analytical-trial ledger foundation (unwired to live promotion).

Provides append-only events, factual trial registration, policy-derived
multiplicity, derived completeness (never promotable COMPLETE), and atomic
trial+budget(+holdout) registration. PR4 adds sealed artefact digests, exact completion-to-artefact links, and
bundle-linked COMPLETED finalization. The existing P0 fail-closed
multiple-testing path remains the default for promotable decisions.

PR3/PR4 do **not** expose a public path to mint verified legacy-N human
approval. ``propose_legacy_n_bound`` is diagnostic only. Reproduction
byte-identity is system-derived from stored immutable input hashes, never a
caller Boolean. Local checkpoints are non-authoritative.
"""

from crl.research.ledger.budget import (
    BudgetAvailability,
    BudgetError,
    allocation_availability,
)
from crl.research.ledger.completeness import (
    CompletenessAssessment,
    assess_completeness,
    derive_completeness_from_ledger,
)
from crl.research.ledger.events import append_event
from crl.research.ledger.hash_chain import (
    GENESIS_PREV_EVENT_HASH,
    ChainVerification,
    LedgerHashError,
    assert_hash_chain_intact,
    canonical_json,
    compute_event_hash,
    verify_hash_chain,
)
from crl.research.ledger.multiplicity import (
    GovernanceViolation,
    MultiplicityCensus,
    compute_multiplicity,
)
from crl.research.ledger.registration import (
    BundleRegistrationResult,
    RegistrationError,
    RegistrationResult,
    TrialCompletionWithBundleResult,
    TrialLedger,
)
from crl.research.ledger.trials import (
    ExecutionState,
    TrialKind,
    TrialRegistrationError,
    TrialRegistrationFacts,
    derive_selection_capable,
)

__all__ = [
    "BudgetAvailability",
    "BudgetError",
    "BundleRegistrationResult",
    "ChainVerification",
    "CompletenessAssessment",
    "ExecutionState",
    "GENESIS_PREV_EVENT_HASH",
    "GovernanceViolation",
    "LedgerHashError",
    "MultiplicityCensus",
    "RegistrationError",
    "RegistrationResult",
    "TrialCompletionWithBundleResult",
    "TrialKind",
    "TrialLedger",
    "TrialRegistrationError",
    "TrialRegistrationFacts",
    "allocation_availability",
    "append_event",
    "assert_hash_chain_intact",
    "assess_completeness",
    "canonical_json",
    "compute_event_hash",
    "compute_multiplicity",
    "derive_completeness_from_ledger",
    "derive_selection_capable",
    "verify_hash_chain",
]
