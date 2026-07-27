"""PR5 external anchor + off-machine backup (unwired to live pipeline)."""

from crl.research.anchor.local_backup import LocalPathBackupVerifier
from crl.research.anchor.null_provider import NullAnchorProvider, NullBackupVerifier
from crl.research.anchor.service import (
    latest_anchor_status,
    latest_backup_status,
    record_anchor,
    record_backup_verification,
)
from crl.research.anchor.types import (
    AnchorError,
    AnchorReceipt,
    AnchorStatus,
    AnchorTarget,
    BackupStatus,
    BackupVerificationError,
    BackupVerificationReceipt,
    BackupVerificationRequest,
)

__all__ = [
    "AnchorError",
    "AnchorReceipt",
    "AnchorStatus",
    "AnchorTarget",
    "BackupStatus",
    "BackupVerificationError",
    "BackupVerificationReceipt",
    "BackupVerificationRequest",
    "LocalPathBackupVerifier",
    "NullAnchorProvider",
    "NullBackupVerifier",
    "latest_anchor_status",
    "latest_backup_status",
    "record_anchor",
    "record_backup_verification",
]
