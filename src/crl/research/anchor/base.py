"""Provider protocols for external anchors and off-machine backup verify."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from crl.research.anchor.types import (
    AnchorReceipt,
    AnchorTarget,
    BackupVerificationReceipt,
    BackupVerificationRequest,
)


@runtime_checkable
class AnchorProvider(Protocol):
    """Pure provider: must not mutate the ledger (service records events)."""

    @property
    def provider_id(self) -> str: ...

    def anchor(self, target: AnchorTarget) -> AnchorReceipt:
        """Return UNANCHORED_PENDING when offline; never requires network."""
        ...


@runtime_checkable
class OffMachineBackupVerifier(Protocol):
    """Read-only verification under an explicit backup root (no network)."""

    @property
    def provider_id(self) -> str: ...

    def verify(
        self,
        request: BackupVerificationRequest,
        *,
        backup_root: Path,
    ) -> BackupVerificationReceipt: ...
