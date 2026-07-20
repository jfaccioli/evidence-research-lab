"""P1 programme / governance identity models (schema foundation only).

These models are **not** wired into the live pipeline in PR1. They exist so
later PRs can persist and validate lineage without inventing parallel types.
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


class GovernanceEpochStatus(str, Enum):
    """Epoch completeness labels.

    LEGACY rows never transition to COMPLETE under P1 rules.
    COMPLETE is only meaningful for a governed epoch after full reconciliation
    (later PRs); PR1 storage must not auto-assign COMPLETE.
    """

    LEGACY = "legacy"
    OPEN = "open"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


class ResearchLineage(BaseModel):
    """Lab-wide continuous research history identity."""

    model_config = ConfigDict(extra="forbid")

    research_lineage_id: str = Field(min_length=1)
    description: str = ""
    created_at: Optional[datetime] = None

    @field_validator("research_lineage_id")
    @classmethod
    def _non_blank_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("research_lineage_id must be non-empty")
        return s


class GovernanceEpoch(BaseModel):
    """Span of research under full P1 controls (or LEGACY pre-epoch)."""

    model_config = ConfigDict(extra="forbid")

    governance_epoch_id: str = Field(min_length=1)
    research_lineage_id: str = Field(min_length=1)
    status: GovernanceEpochStatus = GovernanceEpochStatus.OPEN
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


class FeatureWarmUp(BaseModel):
    """Feature warm-up bars and first eligible decision timestamp (UTC)."""

    model_config = ConfigDict(extra="forbid")

    min_bars: int = Field(ge=0)
    eligible_decision_start: datetime

    @field_validator("eligible_decision_start")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return require_utc(v, "eligible_decision_start")


class CandleSemantics(BaseModel):
    """Candle open/close field names and incomplete-bar policy."""

    model_config = ConfigDict(extra="forbid")

    open_time_field: str = Field(min_length=1)
    close_time_field: str = Field(min_length=1)
    incomplete_open_candle: Literal["drop", "forbid"] = "drop"


class ProgrammeBoundaries(BaseModel):
    """Immutable calendar endpoints for train / validation / holdout."""

    model_config = ConfigDict(extra="forbid")

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


class ProgrammeVersion(BaseModel):
    """Sealed programme configuration identity (split + lineage metadata)."""

    model_config = ConfigDict(extra="forbid")

    programme_version_id: str = Field(min_length=1)
    programme_lineage_id: str = Field(min_length=1)
    research_lineage_id: str = Field(min_length=1)
    # None => legacy / not under a governed epoch
    governance_epoch_id: Optional[str] = None
    parent_programme_version_id: Optional[str] = None
    version_reason: str = Field(min_length=1)
    prior_results_available_at_creation: bool
    split_manifest_content_hash: str = ""
    created_at: Optional[datetime] = None

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
