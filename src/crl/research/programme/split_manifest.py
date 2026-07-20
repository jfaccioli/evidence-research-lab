"""Immutable programme split manifest model, validator, and content hash.

Synthetic fixtures only in PR1 — no real prospective programme is sealed here.
Unused by the live fractional-split pipeline.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from crl.research.programme.models import (
    CandleSemantics,
    FeatureWarmUp,
    ProgrammeBoundaries,
    require_utc,
)


class ManifestValidationError(ValueError):
    """Raised when a programme split manifest violates calendar/timing rules."""


class TimingSemantics(BaseModel):
    """Signal / decision / execution ordering for validation.

    Absolute UTC instants may be supplied (tests and explicit programmes).
    When omitted, the default lab fill model is assumed valid by construction:
    features ready by decision (bar close) and execution at next bar open
    (strictly after decision).
    """

    model_config = ConfigDict(extra="forbid")

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


class ProgrammeSplitManifest(BaseModel):
    """Frozen calendar-based programme split (design §1.1 / §9)."""

    model_config = ConfigDict(extra="forbid")

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

    @field_validator(
        "dataset_vintage_freeze_time",
        "raw_data_start",
        "raw_data_end",
    )
    @classmethod
    def _utc_required(cls, v: datetime) -> datetime:
        return require_utc(v, "manifest timestamp")


def _iso_z(dt: datetime) -> str:
    dt = require_utc(dt, "timestamp")
    # Canonical: seconds precision with Z suffix
    s = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return s


def canonical_manifest_dict(manifest: ProgrammeSplitManifest) -> dict[str, Any]:
    """JSON-ready dict with sorted structure and Z-normalized UTC timestamps."""
    raw = manifest.model_dump(mode="python")

    def convert(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return _iso_z(obj)
        if isinstance(obj, dict):
            return {k: convert(obj[k]) for k in sorted(obj.keys())}
        if isinstance(obj, list):
            return [convert(x) for x in obj]
        return obj

    return convert(raw)  # type: ignore[return-value]


def canonical_serialization(manifest: ProgrammeSplitManifest) -> str:
    """Deterministic canonical JSON (sorted keys, compact separators)."""
    return json.dumps(
        canonical_manifest_dict(manifest),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def content_hash(manifest: ProgrammeSplitManifest) -> str:
    """SHA-256 hex digest of the canonical serialization."""
    return hashlib.sha256(canonical_serialization(manifest).encode("utf-8")).hexdigest()


def validate_split_manifest(manifest: ProgrammeSplitManifest) -> ProgrammeSplitManifest:
    """Validate calendar/timing invariants. Returns the same instance on success.

    Raises ManifestValidationError (or pydantic ValidationError for type issues).
    """
    try:
        # Re-validate field constraints if constructed loosely
        m = (
            manifest
            if isinstance(manifest, ProgrammeSplitManifest)
            else ProgrammeSplitManifest.model_validate(manifest)
        )
    except Exception as exc:  # pydantic ValidationError
        raise ManifestValidationError(str(exc)) from exc

    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(msg)

    # Non-empty stable IDs (also enforced by model; re-check parent optional)
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

    # Raw start/end ordering
    if not (m.raw_data_start < m.raw_data_end):
        fail("raw_data_start must be strictly before raw_data_end")

    # Warm-up / eligible decision start
    elig = m.feature_warm_up.eligible_decision_start
    if elig < m.raw_data_start:
        fail("eligible_decision_start must be >= raw_data_start")
    if elig > m.raw_data_end:
        fail("eligible_decision_start must be <= raw_data_end")
    if m.feature_warm_up.min_bars < 0:
        fail("feature_warm_up.min_bars must be >= 0")

    b = m.boundaries
    # Train / validation / holdout ordering
    if not (b.train_start <= b.train_end):
        fail("train_start must be <= train_end")
    if not (b.train_end <= b.val_end):
        fail("train_end must be <= val_end")
    if not (b.val_end <= b.holdout_start):
        fail("val_end must be <= holdout_start")
    if not (b.holdout_start < b.holdout_end):
        fail("holdout_start must be strictly before holdout_end")

    # Boundaries inside raw window
    if b.train_start < m.raw_data_start:
        fail("train_start must be >= raw_data_start")
    if b.holdout_end > m.raw_data_end:
        fail("holdout_end must be <= raw_data_end")

    # Eligible decision should not start after first train decision window ends absurdly;
    # require eligible_decision_start <= train_end (can trade during train after warm-up)
    if elig > b.holdout_end:
        fail("eligible_decision_start must be <= holdout_end")
    if elig > b.train_end:
        # Warm-up may extend into train; eligible start after train_end would leave no train
        fail("eligible_decision_start must be <= train_end")

    # Dataset vintage required (non-null UTC already)
    if m.dataset_vintage_freeze_time.tzinfo is None:
        fail("dataset_vintage_freeze_time must be UTC-aware")

    # Parent / version metadata: genesis may omit parent; non-empty reason already checked
    if m.parent_programme_version_id is not None and not m.parent_programme_version_id.strip():
        fail("parent_programme_version_id if set must be non-empty")

    # Candle fields non-empty
    if not m.candle_semantics.open_time_field.strip():
        fail("candle_semantics.open_time_field must be non-empty")
    if not m.candle_semantics.close_time_field.strip():
        fail("candle_semantics.close_time_field must be non-empty")

    # Signal / decision / execution ordering
    t = m.timing
    if t.signal_available_at is not None and t.decision_at is not None:
        if t.signal_available_at > t.decision_at:
            fail("signal_available_at must be no later than decision_at")
    if t.decision_at is not None and t.execution_at is not None:
        if not (t.execution_at > t.decision_at):
            fail("execution_at must be strictly after decision_at")
    # If absolute times partially provided, require consistent sets for the pair checks above.
    # Rule-based default (bar_close → next_bar_open) is always execution-after-decision.
    if t.execution_kind == "next_bar_open" and t.decision_kind == "bar_close":
        pass  # valid by construction
    else:
        fail("unsupported decision/execution kind combination for PR1")

    if t.signal_kind != "features_ready_by_decision":
        fail("unsupported signal_kind for PR1")

    if errors:
        raise ManifestValidationError("; ".join(errors))
    return m


def validate_and_hash(manifest: ProgrammeSplitManifest) -> tuple[ProgrammeSplitManifest, str]:
    """Validate then return (manifest, content_hash)."""
    m = validate_split_manifest(manifest)
    return m, content_hash(m)
