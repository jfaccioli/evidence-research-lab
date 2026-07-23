"""Immutable programme split manifest model, validator, and content hash.

Synthetic fixtures only in PR1 — no real prospective programme is sealed here.
Unused by the live fractional-split pipeline.

Sealing rules:
- All scientific models are frozen (immutable).
- Canonical JSON preserves full datetime precision (including microseconds).
- Construction and ``content_hash()`` always run complete scientific validation.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from crl.research.programme.models import (
    CandleSemantics,
    FeatureWarmUp,
    ProgrammeBoundaries,
    _reject_whitespace_optional_id,
    require_utc,
)


class ManifestValidationError(ValueError):
    """Raised by validate_split_manifest / content_hash for scientific violations.

    Direct ``ProgrammeSplitManifest(...)`` construction raises pydantic
    ``ValidationError`` (which may wrap the same messages). Callers should
    catch ``ValidationError`` for constructors and ``ManifestValidationError``
    for the explicit validate/hash helpers — or catch both.
    """


class TimingSemantics(BaseModel):
    """Signal / decision / execution ordering for validation.

    Absolute UTC instants must be **all present** or **all absent**.
    When present: ``signal_available_at <= decision_at < execution_at``.
    When absent, the default lab fill model is assumed valid by construction:
    features ready by decision (bar close) and execution at next bar open.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    signal_available_at: Optional[datetime] = None
    decision_at: Optional[datetime] = None
    execution_at: Optional[datetime] = None
    decision_kind: Literal["bar_close"] = "bar_close"
    execution_kind: Literal["next_bar_open"] = "next_bar_open"
    signal_kind: Literal["features_ready_by_decision"] = "features_ready_by_decision"

    @field_validator("signal_available_at", "decision_at", "execution_at")
    @classmethod
    def _utc_optional(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return None
        return require_utc(v, "timing timestamp")

    @model_validator(mode="after")
    def _all_or_none_ordering(self) -> TimingSemantics:
        present = [
            self.signal_available_at is not None,
            self.decision_at is not None,
            self.execution_at is not None,
        ]
        if any(present) and not all(present):
            raise ValueError(
                "timing instants must be all present or all absent "
                "(signal_available_at, decision_at, execution_at)"
            )
        if all(present):
            assert self.signal_available_at is not None
            assert self.decision_at is not None
            assert self.execution_at is not None
            if self.signal_available_at > self.decision_at:
                raise ValueError("signal_available_at must be <= decision_at")
            if not (self.decision_at < self.execution_at):
                raise ValueError("decision_at must be strictly before execution_at")
        return self


class ProgrammeSplitManifest(BaseModel):
    """Frozen calendar-based programme split (design §1.1 / §9).

    **raw_data_end semantics (exclusive upper bound of the raw series):**
    Raw bars occupy the half-open interval
    ``[raw_data_start, raw_data_end)`` in the same time domain as boundaries.
    The last included candle is the last bar whose close time is strictly less
    than ``raw_data_end``. Dataset vintage freeze must be at least the
    availability/close time of that last included candle, which under bar-close
    semantics is bounded by ``raw_data_end`` (freeze >= raw_data_end is the
    conservative requirement that the vintage is not frozen before the exclusive
    end of the declared raw window).

    Construction validates scientific calendar/timing contracts. Nested models
    are frozen; the root is frozen after successful validation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    programme_version_id: str = Field(min_length=1)
    programme_lineage_id: str = Field(min_length=1)
    research_lineage_id: str = Field(min_length=1)
    governance_epoch_id: Optional[str] = None
    parent_programme_version_id: Optional[str] = None
    version_reason: str = Field(min_length=1)
    prior_results_available_at_creation: bool

    dataset_id: str = Field(min_length=1)
    dataset_vintage_freeze_time: datetime
    interval: str = Field(min_length=1)
    timezone: Literal["UTC"] = "UTC"

    raw_data_start: datetime
    raw_data_end: datetime
    feature_warm_up: FeatureWarmUp
    candle_semantics: CandleSemantics
    signal_availability_rule: str = Field(min_length=1)
    decision_timestamp: str = Field(min_length=1)
    execution_timestamp: str = Field(min_length=1)
    timing: TimingSemantics = Field(default_factory=TimingSemantics)
    boundaries: ProgrammeBoundaries

    @field_validator(
        "programme_version_id",
        "programme_lineage_id",
        "research_lineage_id",
        "version_reason",
        "dataset_id",
        "interval",
        "signal_availability_rule",
        "decision_timestamp",
        "execution_timestamp",
    )
    @classmethod
    def _stable_non_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("stable ID / required string fields must be non-empty")
        return s

    @field_validator("governance_epoch_id", "parent_programme_version_id")
    @classmethod
    def _optional_ids(cls, v: Optional[str], info) -> Optional[str]:
        return _reject_whitespace_optional_id(v, info.field_name)

    @field_validator(
        "dataset_vintage_freeze_time",
        "raw_data_start",
        "raw_data_end",
    )
    @classmethod
    def _utc_required(cls, v: datetime) -> datetime:
        return require_utc(v, "manifest timestamp")

    @model_validator(mode="after")
    def _scientific_contracts(self) -> ProgrammeSplitManifest:
        _validate_manifest_invariants(self)
        return self


def _iso_full(dt: datetime) -> str:
    """UTC ISO-8601 with full precision (microseconds) and Z suffix."""
    dt = require_utc(dt, "timestamp")
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}Z"


def _revalidate_manifest(manifest: ProgrammeSplitManifest) -> ProgrammeSplitManifest:
    """Reconstruct and fully revalidate from dumped data.

    Defends against invalid instances produced by ``model_copy(update=...)``
    (which does not re-run field validators by default).
    """
    if not isinstance(manifest, ProgrammeSplitManifest):
        raise ManifestValidationError(
            "expected ProgrammeSplitManifest for revalidation"
        )
    try:
        # Round-trip through model_validate so Field(min_length=...) and
        # scientific contracts run again on the dumped payload.
        return ProgrammeSplitManifest.model_validate(
            manifest.model_dump(mode="python")
        )
    except ValidationError as exc:
        raise ManifestValidationError(str(exc)) from exc
    except ValueError as exc:
        raise ManifestValidationError(str(exc)) from exc


def canonical_manifest_dict(manifest: ProgrammeSplitManifest) -> dict[str, Any]:
    """JSON-ready dict with sorted keys and full-precision UTC timestamps.

    Always revalidates by reconstruction before dumping.
    """
    m = _revalidate_manifest(manifest)
    raw = m.model_dump(mode="python")

    def convert(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return _iso_full(obj)
        if isinstance(obj, dict):
            return {k: convert(obj[k]) for k in sorted(obj.keys())}
        if isinstance(obj, list):
            return [convert(x) for x in obj]
        return obj

    return convert(raw)  # type: ignore[return-value]


def canonical_serialization(manifest: ProgrammeSplitManifest) -> str:
    """Deterministic canonical JSON after full reconstruct/revalidate."""
    m = _revalidate_manifest(manifest)
    return json.dumps(
        canonical_manifest_dict(m),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def content_hash(manifest: ProgrammeSplitManifest) -> str:
    """SHA-256 hex of canonical serialization after reconstruct/revalidate."""
    if not isinstance(manifest, ProgrammeSplitManifest):
        raise ManifestValidationError("content_hash requires a ProgrammeSplitManifest")
    m = _revalidate_manifest(manifest)
    return hashlib.sha256(canonical_serialization(m).encode("utf-8")).hexdigest()


def _validate_manifest_invariants(m: ProgrammeSplitManifest) -> None:
    """Calendar / timing / vintage scientific contracts.

    Raises ManifestValidationError on violation when called from helpers.
    When invoked from pydantic model_validator, raises ValueError (wrapped as
    ValidationError by pydantic).
    """
    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(msg)

    for name in (
        "programme_version_id",
        "programme_lineage_id",
        "research_lineage_id",
        "dataset_id",
        "version_reason",
    ):
        val = getattr(m, name)
        if not str(val).strip():
            fail(f"{name} must be non-empty")

    if m.timezone != "UTC":
        fail("timezone must be UTC")

    # Raw window: half-open [raw_data_start, raw_data_end)
    if not (m.raw_data_start < m.raw_data_end):
        fail(
            "raw_data_start must be strictly before raw_data_end "
            "(raw series is half-open [raw_data_start, raw_data_end))"
        )

    elig = m.feature_warm_up.eligible_decision_start
    if elig < m.raw_data_start:
        fail("eligible_decision_start must be >= raw_data_start")
    # eligible start must lie inside the raw half-open window
    if not (elig < m.raw_data_end):
        fail("eligible_decision_start must be < raw_data_end (inside raw half-open window)")
    if m.feature_warm_up.min_bars < 0:
        fail("feature_warm_up.min_bars must be >= 0")

    b = m.boundaries
    # Half-open nonempty intervals
    if not (b.train_start < b.train_end):
        fail("train interval empty: require train_start < train_end (half-open)")
    if not (b.train_end < b.val_end):
        fail(
            "validation interval empty or overlapping train: "
            "require train_end < val_end (half-open; train_end == val_end rejected)"
        )
    if not (b.holdout_start < b.holdout_end):
        fail("holdout interval empty: require holdout_start < holdout_end (half-open)")
    if b.holdout_start < b.val_end:
        fail(
            "holdout overlaps validation: require holdout_start >= val_end "
            "(half-open; shared boundary candle not double-counted)"
        )

    # Boundaries inside raw half-open window
    if b.train_start < m.raw_data_start:
        fail("train_start must be >= raw_data_start")
    if not (b.holdout_end <= m.raw_data_end):
        fail(
            "holdout_end must be <= raw_data_end "
            "(holdout half-open end cannot exceed raw exclusive end)"
        )

    if not (elig < b.holdout_end):
        fail("eligible_decision_start must be < holdout_end")
    if not (elig < b.train_end):
        fail("eligible_decision_start must be < train_end")

    # Vintage: not earlier than availability of last included candle.
    # Last included candle close is strictly before raw_data_end (exclusive end);
    # conservative PR1 rule: freeze_time >= raw_data_end so the vintage cannot
    # predate the declared exclusive end of the raw window.
    if m.dataset_vintage_freeze_time < m.raw_data_end:
        fail(
            "dataset_vintage_freeze_time must be >= raw_data_end "
            "(raw_data_end is the exclusive upper bound of the raw series; "
            "vintage must not predate availability of the last included candle)"
        )

    if m.parent_programme_version_id is not None and not m.parent_programme_version_id.strip():
        fail("parent_programme_version_id if set must be non-empty")

    if not m.candle_semantics.open_time_field.strip():
        fail("candle_semantics.open_time_field must be non-empty")
    if not m.candle_semantics.close_time_field.strip():
        fail("candle_semantics.close_time_field must be non-empty")

    t = m.timing
    present = [
        t.signal_available_at is not None,
        t.decision_at is not None,
        t.execution_at is not None,
    ]
    if any(present) and not all(present):
        fail(
            "timing instants must be all present or all absent "
            "(signal_available_at, decision_at, execution_at)"
        )
    if all(present):
        assert t.signal_available_at is not None
        assert t.decision_at is not None
        assert t.execution_at is not None
        if t.signal_available_at > t.decision_at:
            fail("signal_available_at must be <= decision_at")
        if not (t.decision_at < t.execution_at):
            fail("decision_at must be strictly before execution_at (signal <= decision < execution)")

    if not (t.execution_kind == "next_bar_open" and t.decision_kind == "bar_close"):
        fail("unsupported decision/execution kind combination for PR1")
    if t.signal_kind != "features_ready_by_decision":
        fail("unsupported signal_kind for PR1")

    if errors:
        raise ValueError("; ".join(errors))


def validate_split_manifest(
    manifest: Union[ProgrammeSplitManifest, dict[str, Any]],
) -> ProgrammeSplitManifest:
    """Validate calendar/timing invariants. Returns a frozen validated instance.

    Raises ManifestValidationError (never bare ValidationError to callers).
    """
    try:
        if isinstance(manifest, ProgrammeSplitManifest):
            _validate_manifest_invariants(manifest)
            return manifest
        return ProgrammeSplitManifest.model_validate(manifest)
    except ManifestValidationError:
        raise
    except ValidationError as exc:
        raise ManifestValidationError(str(exc)) from exc
    except ValueError as exc:
        raise ManifestValidationError(str(exc)) from exc


def validate_and_hash(
    manifest: Union[ProgrammeSplitManifest, dict[str, Any]],
) -> tuple[ProgrammeSplitManifest, str]:
    """Validate then return (manifest, content_hash)."""
    m = validate_split_manifest(manifest)
    return m, content_hash(m)
