"""PR5 external-anchor and off-machine backup types (fail closed)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional


class AnchorStatus(str, Enum):
    UNANCHORED_PENDING = "UNANCHORED_PENDING"
    ANCHORED = "ANCHORED"


class BackupStatus(str, Enum):
    BACKUP_UNVERIFIED = "BACKUP_UNVERIFIED"
    BACKUP_VERIFIED = "BACKUP_VERIFIED"


class AnchorError(RuntimeError):
    """External anchor operation failed (fail closed)."""


class BackupVerificationError(RuntimeError):
    """Off-machine backup verification failed (fail closed)."""


@dataclass(frozen=True)
class AnchorTarget:
    """Content-addressed tip/checkpoint being attested."""

    research_lineage_id: str
    final_event_seq: int
    final_event_hash: str
    checkpoint_id: Optional[str] = None
    database_snapshot_hash: Optional[str] = None
    artifact_aggregate_root: Optional[str] = None


@dataclass(frozen=True)
class AnchorReceipt:
    status: AnchorStatus
    provider_id: str
    target: AnchorTarget
    external_ref: Optional[str]
    attested_at: str
    detail: Mapping[str, Any]


@dataclass(frozen=True)
class BackupVerificationRequest:
    research_lineage_id: str
    snapshot_relative_path: str
    expected_snapshot_sha256: str
    expected_size_bytes: int
    final_event_seq: int
    final_event_hash: str


@dataclass(frozen=True)
class BackupVerificationReceipt:
    status: BackupStatus
    provider_id: str
    request: BackupVerificationRequest
    verified_at: str
    detail: Mapping[str, Any]
