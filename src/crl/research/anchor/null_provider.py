"""Default null providers: never network; never silent promotion authority."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from crl.research.anchor.types import (
    AnchorReceipt,
    AnchorStatus,
    AnchorTarget,
    BackupStatus,
    BackupVerificationReceipt,
    BackupVerificationRequest,
)


def _utc_now() -> str:
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}Z"


class NullAnchorProvider:
    """Always UNANCHORED_PENDING. Safe default; no network; no secrets."""

    def __init__(self, provider_id: str = "null_anchor") -> None:
        self._provider_id = str(provider_id)

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def anchor(self, target: AnchorTarget) -> AnchorReceipt:
        detail: Mapping[str, Any] = {
            "reason": "null_provider_never_anchors",
            "research_lineage_id": target.research_lineage_id,
            "final_event_seq": target.final_event_seq,
        }
        return AnchorReceipt(
            status=AnchorStatus.UNANCHORED_PENDING,
            provider_id=self.provider_id,
            target=target,
            external_ref=None,
            attested_at=_utc_now(),
            detail=dict(detail),
        )


class NullBackupVerifier:
    """Always BACKUP_UNVERIFIED (does not inspect filesystem)."""

    def __init__(self, provider_id: str = "null_backup") -> None:
        self._provider_id = str(provider_id)

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def verify(
        self,
        request: BackupVerificationRequest,
        *,
        backup_root: Path,
    ) -> BackupVerificationReceipt:
        _ = backup_root  # explicit root required by protocol; unused
        return BackupVerificationReceipt(
            status=BackupStatus.BACKUP_UNVERIFIED,
            provider_id=self.provider_id,
            request=request,
            verified_at=_utc_now(),
            detail={"reason": "null_provider_never_verifies"},
        )
