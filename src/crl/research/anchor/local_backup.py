"""Local-path off-machine backup verifier (no network)."""

from __future__ import annotations

import hashlib
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from crl.research.anchor.types import (
    BackupStatus,
    BackupVerificationError,
    BackupVerificationReceipt,
    BackupVerificationRequest,
)
from crl.research.artifacts.paths import (
    ArtifactPathError,
    normalize_member_path,
    require_artifact_root,
    resolve_under_root,
)


def _utc_now() -> str:
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}Z"


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class LocalPathBackupVerifier:
    """Verify a snapshot file under an explicit backup_root (hash + size).

    Path traversal / symlink escapes fail closed. Missing or mismatched files
    return BACKUP_UNVERIFIED (or raise when path escapes).
    """

    def __init__(self, provider_id: str = "local_path_backup") -> None:
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
        try:
            root = require_artifact_root(backup_root)
        except ArtifactPathError as exc:
            raise BackupVerificationError(str(exc)) from exc
        try:
            rel = normalize_member_path(request.snapshot_relative_path)
        except ArtifactPathError as exc:
            raise BackupVerificationError(str(exc)) from exc
        # Inspect the unreolved join for symlink leaves before resolve() follows them.
        raw = root / rel
        try:
            st_raw = os.lstat(raw)
        except FileNotFoundError:
            return BackupVerificationReceipt(
                status=BackupStatus.BACKUP_UNVERIFIED,
                provider_id=self.provider_id,
                request=request,
                verified_at=_utc_now(),
                detail={"reason": "missing_or_not_regular_file", "path": rel},
            )
        except OSError as exc:
            raise BackupVerificationError(f"unreadable backup file: {exc}") from exc
        if stat.S_ISLNK(st_raw.st_mode):
            return BackupVerificationReceipt(
                status=BackupStatus.BACKUP_UNVERIFIED,
                provider_id=self.provider_id,
                request=request,
                verified_at=_utc_now(),
                detail={"reason": "symlink_forbidden", "path": rel},
            )
        try:
            path = resolve_under_root(root, rel)
        except ArtifactPathError as exc:
            raise BackupVerificationError(str(exc)) from exc
        if path.is_symlink():
            return BackupVerificationReceipt(
                status=BackupStatus.BACKUP_UNVERIFIED,
                provider_id=self.provider_id,
                request=request,
                verified_at=_utc_now(),
                detail={"reason": "symlink_forbidden", "path": rel},
            )
        if not path.is_file():
            return BackupVerificationReceipt(
                status=BackupStatus.BACKUP_UNVERIFIED,
                provider_id=self.provider_id,
                request=request,
                verified_at=_utc_now(),
                detail={"reason": "missing_or_not_regular_file", "path": rel},
            )
        try:
            st = path.lstat()
        except OSError as exc:
            raise BackupVerificationError(f"unreadable backup file: {exc}") from exc
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            return BackupVerificationReceipt(
                status=BackupStatus.BACKUP_UNVERIFIED,
                provider_id=self.provider_id,
                request=request,
                verified_at=_utc_now(),
                detail={"reason": "not_regular_file", "path": rel},
            )

        expected_hash = str(request.expected_snapshot_sha256).strip().lower()
        if len(expected_hash) != 64 or any(
            ch not in "0123456789abcdef" for ch in expected_hash
        ):
            raise BackupVerificationError("expected_snapshot_sha256 invalid")
        actual_hash = _file_sha256(path)
        actual_size = int(st.st_size)
        if actual_hash != expected_hash or actual_size != int(
            request.expected_size_bytes
        ):
            return BackupVerificationReceipt(
                status=BackupStatus.BACKUP_UNVERIFIED,
                provider_id=self.provider_id,
                request=request,
                verified_at=_utc_now(),
                detail={
                    "reason": "hash_or_size_mismatch",
                    "path": rel,
                    "actual_sha256": actual_hash,
                    "actual_size": actual_size,
                },
            )
        # Extra containment guard after open.
        root_s = str(root.resolve())
        path_s = str(path.resolve())
        if path_s != root_s and not path_s.startswith(root_s + os.sep):
            raise BackupVerificationError("path escapes backup root after resolve")
        return BackupVerificationReceipt(
            status=BackupStatus.BACKUP_VERIFIED,
            provider_id=self.provider_id,
            request=request,
            verified_at=_utc_now(),
            detail={"reason": "hash_and_size_match", "path": rel},
        )
