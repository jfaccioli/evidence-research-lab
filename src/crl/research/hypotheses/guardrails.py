"""Hypothesis design guardrails — quality of evidence, not feature theater.

Enforces standing orders: explicit rules, economic rationale, falsification
expectation. Blocks black-box / empty-story registrations.
"""

from __future__ import annotations

from dataclasses import dataclass

from crl.shared.types import HypothesisSpec


# Hard floor (blocks empty mining). Prefer longer economic stories (soft target).
MIN_RATIONALE_CHARS = 15
MIN_EXPECTED_CHARS = 10
SOFT_RATIONALE_CHARS = 40
SOFT_EXPECTED_CHARS = 20

# Phrases that look like story-free mining (warn/reject)
_BANNED_RATIONALE_FRAGMENTS = (
    "because it backtested well",
    "ai found this",
    "no idea why",
    "black box",
    "neural",
    "just optimize",
)


@dataclass
class GuardrailResult:
    ok: bool
    errors: list[str]
    warnings: list[str]


def validate_hypothesis_spec(spec: HypothesisSpec, *, strict: bool = True) -> GuardrailResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not spec.entry.expression.strip():
        errors.append("entry rule empty")
    if not spec.exit.expression.strip():
        errors.append("exit rule empty")

    rat = (spec.rationale or "").strip()
    exp = (spec.expected_outcome or "").strip()
    if len(rat) < MIN_RATIONALE_CHARS:
        errors.append(
            f"economic rationale too short ({len(rat)}<{MIN_RATIONALE_CHARS}): "
            "explain why this edge could exist in a market"
        )
    elif len(rat) < SOFT_RATIONALE_CHARS:
        warnings.append(
            f"rationale shorter than soft target {SOFT_RATIONALE_CHARS} chars — "
            "prefer a clear economic mechanism"
        )
    if len(exp) < MIN_EXPECTED_CHARS:
        errors.append(
            f"expected_outcome/falsification too short ({len(exp)}<{MIN_EXPECTED_CHARS})"
        )
    elif len(exp) < SOFT_EXPECTED_CHARS:
        warnings.append(
            f"expected_outcome shorter than soft target {SOFT_EXPECTED_CHARS} chars"
        )

    low = rat.lower()
    for frag in _BANNED_RATIONALE_FRAGMENTS:
        if frag in low:
            errors.append(f"rationale contains banned fragment: {frag!r}")

    if "sma" in (spec.entry.expression + spec.exit.expression).lower() and "trend" not in low and "crowd" not in low and "flow" not in low:
        warnings.append(
            "SMA-based rule without trend/flow language in rationale — "
            "prefer stating risk-on capital / herding mechanism"
        )

    if spec.direction not in ("long_only", "long"):
        errors.append("Phase 1/2 long_only only")

    if strict and errors:
        return GuardrailResult(ok=False, errors=errors, warnings=warnings)
    return GuardrailResult(ok=len(errors) == 0, errors=errors, warnings=warnings)


def assert_hypothesis_admissible(spec: HypothesisSpec) -> None:
    r = validate_hypothesis_spec(spec, strict=True)
    if not r.ok:
        raise ValueError("Hypothesis failed guardrails: " + "; ".join(r.errors))
