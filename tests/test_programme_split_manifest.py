"""PR1: programme split-manifest validation and deterministic content hash.

Direct construction raises pydantic ValidationError on contract failure.
validate_split_manifest() raises ManifestValidationError.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from crl.research.programme.models import (
    CandleSemantics,
    FeatureWarmUp,
    ProgrammeBoundaries,
)
from crl.research.programme.split_manifest import (
    ManifestValidationError,
    ProgrammeSplitManifest,
    TimingSemantics,
    canonical_serialization,
    content_hash,
    validate_and_hash,
    validate_split_manifest,
)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _valid_kwargs(**overrides: Any) -> dict[str, Any]:
    # raw_data_end is exclusive upper bound of raw series [start, end).
    # holdout_end <= raw_data_end; vintage freeze >= raw_data_end.
    base: dict[str, Any] = dict(
        programme_version_id="btc_usdt_spot_daily_fixture_pv0",
        programme_lineage_id="btc_usdt_spot_daily_fixture",
        research_lineage_id="crl_btc_research_v0",
        governance_epoch_id=None,
        parent_programme_version_id=None,
        version_reason="synthetic fixture for PR1 tests only",
        prior_results_available_at_creation=True,
        dataset_id="synthetic_BTCUSDT_1d_fixture_aaa",
        dataset_vintage_freeze_time=_dt("2020-01-01T00:00:00Z"),
        interval="1d",
        timezone="UTC",
        raw_data_start=_dt("2018-01-01T00:00:00Z"),
        raw_data_end=_dt("2020-01-01T00:00:00Z"),  # exclusive end
        feature_warm_up=FeatureWarmUp(
            min_bars=50,
            eligible_decision_start=_dt("2018-03-01T00:00:00Z"),
        ),
        candle_semantics=CandleSemantics(
            open_time_field="open_time_utc",
            close_time_field="close_time_utc",
            incomplete_open_candle="drop",
        ),
        signal_availability_rule="features use only data with close_time <= decision_time",
        decision_timestamp="bar close_time (signal time)",
        execution_timestamp="next bar open_time (fill model)",
        timing=TimingSemantics(
            signal_available_at=_dt("2018-06-01T00:00:00Z"),
            decision_at=_dt("2018-06-01T00:00:00Z"),
            execution_at=_dt("2018-06-02T00:00:00Z"),
        ),
        boundaries=ProgrammeBoundaries(
            train_start=_dt("2018-03-01T00:00:00Z"),
            train_end=_dt("2018-12-31T00:00:00Z"),
            val_end=_dt("2019-06-30T00:00:00Z"),
            holdout_start=_dt("2019-07-01T00:00:00Z"),
            holdout_end=_dt("2020-01-01T00:00:00Z"),
        ),
    )
    base.update(overrides)
    return base


def _manifest(**overrides: Any) -> ProgrammeSplitManifest:
    return ProgrammeSplitManifest(**_valid_kwargs(**overrides))


def test_valid_manifest_and_deterministic_hash():
    m1 = _manifest()
    m2 = _manifest()
    validate_split_manifest(m1)
    h1 = content_hash(m1)
    h2 = content_hash(m2)
    assert h1 == h2
    assert len(h1) == 64
    _, h3 = validate_and_hash(m1)
    assert h3 == h1
    s1 = canonical_serialization(m1)
    s2 = canonical_serialization(m2)
    assert s1 == s2
    assert s1.startswith("{")
    assert '"programme_version_id"' in s1
    assert ", " not in s1


def test_manifest_and_nested_models_are_immutable():
    m = _manifest()
    with pytest.raises(ValidationError):
        m.dataset_id = "mutated"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        m.boundaries.train_end = _dt("2019-01-01T00:00:00Z")  # type: ignore[misc]
    with pytest.raises(ValidationError):
        m.feature_warm_up.min_bars = 999  # type: ignore[misc]
    with pytest.raises(ValidationError):
        m.timing.decision_at = _dt("2019-01-01T00:00:00Z")  # type: ignore[misc]
    h = content_hash(m)
    assert content_hash(m) == h


def test_subsecond_vintage_difference_changes_hash():
    t0 = _dt("2020-01-01T00:00:00.000000Z")
    t1 = t0 + timedelta(microseconds=800_000)
    m0 = _manifest(dataset_vintage_freeze_time=t0)
    m1 = _manifest(dataset_vintage_freeze_time=t1)
    assert content_hash(m0) != content_hash(m1)
    assert "2020-01-01T00:00:00.000000Z" in canonical_serialization(m0)
    assert ".800000Z" in canonical_serialization(m1)


def test_empty_programme_version_id_rejected():
    with pytest.raises(ValidationError):
        _manifest(programme_version_id="   ")


def test_naive_datetime_rejected():
    with pytest.raises(ValidationError):
        _manifest(raw_data_start=datetime(2018, 1, 1))


def test_raw_start_not_before_end():
    with pytest.raises(ValidationError, match="raw_data_start"):
        _manifest(
            raw_data_start=_dt("2019-12-31T00:00:00Z"),
            raw_data_end=_dt("2018-01-01T00:00:00Z"),
        )


def test_raw_start_equal_end_rejected():
    with pytest.raises(ValidationError, match="raw_data_start"):
        _manifest(
            raw_data_start=_dt("2019-01-01T00:00:00Z"),
            raw_data_end=_dt("2019-01-01T00:00:00Z"),
        )


def test_eligible_decision_before_raw_start():
    with pytest.raises(ValidationError, match="eligible_decision_start"):
        _manifest(
            feature_warm_up=FeatureWarmUp(
                min_bars=10,
                eligible_decision_start=_dt("2017-01-01T00:00:00Z"),
            )
        )


def test_eligible_decision_after_train_end():
    with pytest.raises(ValidationError, match="eligible_decision_start"):
        _manifest(
            feature_warm_up=FeatureWarmUp(
                min_bars=10,
                eligible_decision_start=_dt("2019-01-15T00:00:00Z"),
            )
        )


def test_train_end_after_val_end():
    with pytest.raises(ValidationError, match="validation interval"):
        _manifest(
            boundaries=ProgrammeBoundaries(
                train_start=_dt("2018-03-01T00:00:00Z"),
                train_end=_dt("2019-08-01T00:00:00Z"),
                val_end=_dt("2019-06-30T00:00:00Z"),
                holdout_start=_dt("2019-09-01T00:00:00Z"),
                holdout_end=_dt("2020-01-01T00:00:00Z"),
            )
        )


def test_empty_validation_when_train_end_equals_val_end():
    with pytest.raises(ValidationError, match="validation interval"):
        _manifest(
            boundaries=ProgrammeBoundaries(
                train_start=_dt("2018-03-01T00:00:00Z"),
                train_end=_dt("2019-06-30T00:00:00Z"),
                val_end=_dt("2019-06-30T00:00:00Z"),
                holdout_start=_dt("2019-07-01T00:00:00Z"),
                holdout_end=_dt("2020-01-01T00:00:00Z"),
            )
        )


def test_holdout_overlap_validation_boundary():
    with pytest.raises(ValidationError, match="holdout overlaps"):
        _manifest(
            boundaries=ProgrammeBoundaries(
                train_start=_dt("2018-03-01T00:00:00Z"),
                train_end=_dt("2018-12-31T00:00:00Z"),
                val_end=_dt("2019-08-01T00:00:00Z"),
                holdout_start=_dt("2019-07-01T00:00:00Z"),
                holdout_end=_dt("2020-01-01T00:00:00Z"),
            )
        )


def test_contiguous_val_end_equals_holdout_start_allowed():
    m = _manifest(
        boundaries=ProgrammeBoundaries(
            train_start=_dt("2018-03-01T00:00:00Z"),
            train_end=_dt("2018-12-31T00:00:00Z"),
            val_end=_dt("2019-07-01T00:00:00Z"),
            holdout_start=_dt("2019-07-01T00:00:00Z"),
            holdout_end=_dt("2020-01-01T00:00:00Z"),
        )
    )
    assert content_hash(m)


def test_holdout_start_not_before_end():
    with pytest.raises(ValidationError, match="holdout interval"):
        _manifest(
            boundaries=ProgrammeBoundaries(
                train_start=_dt("2018-03-01T00:00:00Z"),
                train_end=_dt("2018-12-31T00:00:00Z"),
                val_end=_dt("2019-06-30T00:00:00Z"),
                holdout_start=_dt("2020-01-01T00:00:00Z"),
                holdout_end=_dt("2019-07-01T00:00:00Z"),
            )
        )


def test_train_start_before_raw_start():
    with pytest.raises(ValidationError, match="train_start"):
        _manifest(
            boundaries=ProgrammeBoundaries(
                train_start=_dt("2017-01-01T00:00:00Z"),
                train_end=_dt("2018-12-31T00:00:00Z"),
                val_end=_dt("2019-06-30T00:00:00Z"),
                holdout_start=_dt("2019-07-01T00:00:00Z"),
                holdout_end=_dt("2020-01-01T00:00:00Z"),
            )
        )


def test_holdout_end_after_raw_end():
    with pytest.raises(ValidationError, match="holdout_end"):
        _manifest(
            boundaries=ProgrammeBoundaries(
                train_start=_dt("2018-03-01T00:00:00Z"),
                train_end=_dt("2018-12-31T00:00:00Z"),
                val_end=_dt("2019-06-30T00:00:00Z"),
                holdout_start=_dt("2019-07-01T00:00:00Z"),
                holdout_end=_dt("2020-06-01T00:00:00Z"),
            )
        )


def test_partial_timing_execution_without_decision_rejected():
    with pytest.raises(ValidationError, match="all present|all absent|timing"):
        _manifest(
            timing=TimingSemantics(
                signal_available_at=None,
                decision_at=None,
                execution_at=_dt("2018-06-02T00:00:00Z"),
            )
        )


def test_partial_timing_signal_only_rejected():
    with pytest.raises(ValidationError, match="all present|all absent|timing"):
        TimingSemantics(
            signal_available_at=_dt("2018-06-01T00:00:00Z"),
            decision_at=None,
            execution_at=None,
        )


def test_signal_after_decision_rejected():
    with pytest.raises(ValidationError, match="signal_available_at"):
        _manifest(
            timing=TimingSemantics(
                signal_available_at=_dt("2018-06-02T00:00:00Z"),
                decision_at=_dt("2018-06-01T00:00:00Z"),
                execution_at=_dt("2018-06-03T00:00:00Z"),
            )
        )


def test_execution_not_strictly_after_decision():
    with pytest.raises(ValidationError, match="decision_at|execution"):
        _manifest(
            timing=TimingSemantics(
                signal_available_at=_dt("2018-06-01T00:00:00Z"),
                decision_at=_dt("2018-06-01T00:00:00Z"),
                execution_at=_dt("2018-06-01T00:00:00Z"),
            )
        )


def test_all_timing_absent_allowed():
    m = _manifest(timing=TimingSemantics())
    assert m.timing.signal_available_at is None
    assert content_hash(m)


def test_impossible_vintage_before_raw_end():
    with pytest.raises(ValidationError, match="dataset_vintage_freeze_time"):
        _manifest(dataset_vintage_freeze_time=_dt("2019-06-01T00:00:00Z"))


def test_empty_dataset_id_rejected():
    with pytest.raises(ValidationError):
        _manifest(dataset_id="")


def test_content_hash_changes_when_boundary_changes():
    m1 = _manifest()
    m2 = _manifest(
        boundaries=ProgrammeBoundaries(
            train_start=_dt("2018-03-01T00:00:00Z"),
            train_end=_dt("2018-11-30T00:00:00Z"),
            val_end=_dt("2019-06-30T00:00:00Z"),
            holdout_start=_dt("2019-07-01T00:00:00Z"),
            holdout_end=_dt("2020-01-01T00:00:00Z"),
        )
    )
    assert content_hash(m1) != content_hash(m2)


def test_content_hash_rejects_non_manifest_type():
    with pytest.raises(ManifestValidationError):
        content_hash({"not": "a manifest"})  # type: ignore[arg-type]


def test_validate_split_manifest_helper_raises_manifest_validation_error():
    """Helper wraps pydantic errors as ManifestValidationError."""
    with pytest.raises(ManifestValidationError):
        validate_split_manifest(
            _valid_kwargs(
                raw_data_start=_dt("2019-12-31T00:00:00Z"),
                raw_data_end=_dt("2018-01-01T00:00:00Z"),
            )
        )


@pytest.mark.parametrize(
    "field",
    [
        "interval",
        "signal_availability_rule",
        "decision_timestamp",
        "execution_timestamp",
    ],
)
def test_content_hash_rejects_model_copy_empty_required_strings(field: str):
    """model_copy(update=...) can skip validators; hash path must revalidate."""
    m = _manifest()
    bad = m.model_copy(update={field: ""})
    with pytest.raises(ManifestValidationError):
        content_hash(bad)
    with pytest.raises(ManifestValidationError):
        canonical_serialization(bad)
