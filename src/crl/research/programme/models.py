"""P1 programme / governance identity models (schema foundation only).

These models are **not** wired into the live pipeline in PR1. They exist so
later PRs can persist and validate lineage without inventing parallel types.

Scientific models are **frozen** (immutable) after construction so sealed
identity cannot drift after hashing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def require_utc(dt: datetime, field_name: str) -> datetime:
    """Normalize to timezone-aware UTC; reject naive datetimes."""
    if dt.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware UTC (got naive datetime)")
    return dt.astimezone(timezone.utc)


def utc_now() -> datetime:
    """Single-clock UTC timestamp for audit fields."""
    return datetime.now(timezone.utc)


class _FrozenModel(BaseModel):
    """Base for sealed scientific identity objects."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class GovernanceCompleteness(str, Enum):
    """Governed-epoch *completeness* labels (approved design).

    These are **labels**, not a public authority API. Authoritative COMPLETE
    may only be established by PR3 reconciliation (not by model construction
    or a caller-supplied flag). PR1 helpers never return COMPLETE.
    """

    COMPLETE = "COMPLETE"
    INCOMPLETE_KNOWN_GAPS = "INCOMPLETE_KNOWN_GAPS"
    INCOMPLETE_UNBOUNDED = "INCOMPLETE_UNBOUNDED"
    LEGACY_RECONSTRUCTED_CONSERVATIVELY = "LEGACY_RECONSTRUCTED_CONSERVATIVELY"


class EpochLifecycle(str, Enum):
    """Operational lifecycle of an epoch row (separate from completeness)."""

    OPEN = "open"
    CLOSED = "closed"


class ResearchLineage(_FrozenModel):
    """Lab-wide continuous research history identity."""

    research_lineage_id: str = Field(min_length=1)
    description: str = ""
    # Required for persistence (SQL NOT NULL). Defaults to construction time UTC.
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("research_lineage_id")
    @classmethod
    def _non_blank_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("research_lineage_id must be non-empty")
        return s

    @field_validator("created_at")
    @classmethod
    def _utc_created(cls, v: datetime) -> datetime:
        return require_utc(v, "created_at")


class GovernanceEpoch(_FrozenModel):
    """Span of research under full P1 controls.

    Default completeness is INCOMPLETE_UNBOUNDED. LEGACY_RECONSTRUCTED_CONSERVATIVELY
    is **not** a default: it requires the later conservative legacy census and
    human approval. COMPLETE is never established by this constructor.
    """

    governance_epoch_id: str = Field(min_length=1)
    research_lineage_id: str = Field(min_length=1)
    completeness: GovernanceCompleteness = GovernanceCompleteness.INCOMPLETE_UNBOUNDED
    lifecycle: EpochLifecycle = EpochLifecycle.OPEN
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    notes: str = ""

    @field_validator("governance_epoch_id", "research_lineage_id")
    @classmethod
    def _non_blank(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("identity fields must be non-empty")
        return s

    @field_validator("opened_at", "closed_at")
    @classmethod
    def _utc_optional(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return None
        return require_utc(v, "epoch timestamp")

    @field_validator("completeness")
    @classmethod
    def _no_authoritative_complete_via_constructor(
        cls, v: GovernanceCompleteness
    ) -> GovernanceCompleteness:
        # Public construction must not mint authoritative COMPLETE.
        if v is GovernanceCompleteness.COMPLETE:
            raise ValueError(
                "COMPLETE cannot be set via public GovernanceEpoch construction; "
                "authoritative completeness is established only by PR3 reconciliation"
            )
        return v


class FeatureWarmUp(_FrozenModel):
    """Feature warm-up bars and first eligible decision timestamp (UTC)."""

    min_bars: int = Field(ge=0)
    eligible_decision_start: datetime

    @field_validator("eligible_decision_start")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return require_utc(v, "eligible_decision_start")


class CandleSemantics(_FrozenModel):
    """Candle open/close field names and incomplete-bar policy."""

    open_time_field: str = Field(min_length=1)
    close_time_field: str = Field(min_length=1)
    incomplete_open_candle: Literal["drop", "forbid"] = "drop"


class ProgrammeBoundaries(_FrozenModel):
    """Immutable calendar endpoints for train / validation / holdout.

    Endpoint inclusion (explicit, half-open):
    - train:      [train_start, train_end)
    - validation: [train_end, val_end)
    - holdout:    [holdout_start, holdout_end)

    Intervals must be nonempty (start < end) and non-overlapping
    (holdout_start >= val_end). Contiguous programmes may set
    holdout_start == val_end.
    """

    train_start: datetime
    train_end: datetime
    val_end: datetime
    holdout_start: datetime
    holdout_end: datetime

    @field_validator(
        "train_start",
        "train_end",
        "val_end",
        "holdout_start",
        "holdout_end",
    )
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return require_utc(v, "boundary timestamp")


def _reject_whitespace_optional_id(v: Optional[str], field: str) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        raise ValueError(f"{field} must not be whitespace-only")
    return s


def _require_sha256_hex(v: str) -> str:
    s = v.strip()
    if len(s) != 64 or s != s.lower() or any(c not in "0123456789abcdef" for c in s):
        raise ValueError(
            "split_manifest_content_hash must be a 64-character lowercase SHA-256 hex digest"
        )
    return s


class ProgrammeVersion(_FrozenModel):
    """Sealed programme configuration identity (split + lineage metadata)."""

    programme_version_id: str = Field(min_length=1)
    programme_lineage_id: str = Field(min_length=1)
    research_lineage_id: str = Field(min_length=1)
    # None => not under a governed epoch (pre-P1 / ungoverned)
    governance_epoch_id: Optional[str] = None
    parent_programme_version_id: Optional[str] = None
    version_reason: str = Field(min_length=1)
    prior_results_available_at_creation: bool
    # Content hash of the sealed split manifest (64-char lowercase SHA-256).
    split_manifest_content_hash: str = Field(min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator(
        "programme_version_id",
        "programme_lineage_id",
        "research_lineage_id",
        "version_reason",
    )
    @classmethod
    def _non_blank(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("required identity/metadata fields must be non-empty")
        return s

    @field_validator("governance_epoch_id", "parent_programme_version_id")
    @classmethod
    def _optional_ids(cls, v: Optional[str], info) -> Optional[str]:
        return _reject_whitespace_optional_id(v, info.field_name)

    @field_validator("split_manifest_content_hash")
    @classmethod
    def _hash_format(cls, v: str) -> str:
        return _require_sha256_hex(v)

    @field_validator("created_at")
    @classmethod
    def _utc_created(cls, v: datetime) -> datetime:
        return require_utc(v, "created_at")
