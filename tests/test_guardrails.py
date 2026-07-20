import pytest

from crl.research.hypotheses.guardrails import assert_hypothesis_admissible, validate_hypothesis_spec
from crl.research.hypotheses.propose import draft_from_templates
from crl.shared.types import HypothesisSpec, RuleSpec


def test_rejects_empty_rationale():
    spec = HypothesisSpec(
        id="x",
        entry=RuleSpec(expression="close > sma_50"),
        exit=RuleSpec(expression="close < sma_50"),
        rationale="",
        expected_outcome="fail",
    )
    r = validate_hypothesis_spec(spec)
    assert r.ok is False


def test_rejects_banned_story():
    spec = HypothesisSpec(
        id="x",
        entry=RuleSpec(expression="close > sma_50"),
        exit=RuleSpec(expression="close < sma_50"),
        rationale="We like this because it backtested well on our laptop yesterday run.",
        expected_outcome="Should make money if lucky forever hopefully yes.",
    )
    r = validate_hypothesis_spec(spec)
    assert r.ok is False
    assert any("banned" in e for e in r.errors)


def test_templates_pass_guardrails():
    specs = draft_from_templates()
    assert len(specs) >= 5
    for s in specs:
        assert_hypothesis_admissible(s)


def test_assert_raises():
    with pytest.raises(ValueError):
        assert_hypothesis_admissible(
            HypothesisSpec(
                id="bad",
                entry=RuleSpec(expression="close > 0"),
                exit=RuleSpec(expression="close < 0"),
            )
        )
