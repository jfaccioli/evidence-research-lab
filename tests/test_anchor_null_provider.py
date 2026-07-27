"""PR5 null providers and local backup verifier (no network)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from crl.research.anchor.local_backup import LocalPathBackupVerifier
from crl.research.anchor.null_provider import NullAnchorProvider, NullBackupVerifier
from crl.research.anchor.types import (
    AnchorStatus,
    AnchorTarget,
    BackupStatus,
    BackupVerificationError,
    BackupVerificationRequest,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def test_null_anchor_always_pending():
    p = NullAnchorProvider()
    r = p.anchor(
        AnchorTarget(
            research_lineage_id="rl1",
            final_event_seq=1,
            final_event_hash=HASH_A,
        )
    )
    assert r.status is AnchorStatus.UNANCHORED_PENDING
    assert r.external_ref is None
    assert r.provider_id == "null_anchor"


def test_null_backup_always_unverified(tmp_path: Path):
    v = NullBackupVerifier()
    r = v.verify(
        BackupVerificationRequest(
            research_lineage_id="rl1",
            snapshot_relative_path="snap.db",
            expected_snapshot_sha256=HASH_A,
            expected_size_bytes=1,
            final_event_seq=1,
            final_event_hash=HASH_A,
        ),
        backup_root=tmp_path,
    )
    assert r.status is BackupStatus.BACKUP_UNVERIFIED


def test_local_backup_verified_on_match(tmp_path: Path):
    data = b"snapshot-bytes"
    path = tmp_path / "snap.db"
    path.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    v = LocalPathBackupVerifier()
    r = v.verify(
        BackupVerificationRequest(
            research_lineage_id="rl1",
            snapshot_relative_path="snap.db",
            expected_snapshot_sha256=digest,
            expected_size_bytes=len(data),
            final_event_seq=3,
            final_event_hash=HASH_B,
        ),
        backup_root=tmp_path,
    )
    assert r.status is BackupStatus.BACKUP_VERIFIED


def test_local_backup_hash_mismatch_unverified(tmp_path: Path):
    path = tmp_path / "snap.db"
    path.write_bytes(b"x")
    v = LocalPathBackupVerifier()
    r = v.verify(
        BackupVerificationRequest(
            research_lineage_id="rl1",
            snapshot_relative_path="snap.db",
            expected_snapshot_sha256=HASH_A,
            expected_size_bytes=1,
            final_event_seq=1,
            final_event_hash=HASH_A,
        ),
        backup_root=tmp_path,
    )
    assert r.status is BackupStatus.BACKUP_UNVERIFIED


def test_local_backup_path_escape_fails(tmp_path: Path):
    v = LocalPathBackupVerifier()
    with pytest.raises(BackupVerificationError):
        v.verify(
            BackupVerificationRequest(
                research_lineage_id="rl1",
                snapshot_relative_path="../escape.db",
                expected_snapshot_sha256=HASH_A,
                expected_size_bytes=0,
                final_event_seq=1,
                final_event_hash=HASH_A,
            ),
            backup_root=tmp_path,
        )


def test_local_backup_symlink_unverified(tmp_path: Path):
    real = tmp_path / "real.db"
    real.write_bytes(b"data")
    link = tmp_path / "link.db"
    link.symlink_to(real)
    digest = hashlib.sha256(b"data").hexdigest()
    v = LocalPathBackupVerifier()
    r = v.verify(
        BackupVerificationRequest(
            research_lineage_id="rl1",
            snapshot_relative_path="link.db",
            expected_snapshot_sha256=digest,
            expected_size_bytes=4,
            final_event_seq=1,
            final_event_hash=HASH_A,
        ),
        backup_root=tmp_path,
    )
    assert r.status is BackupStatus.BACKUP_UNVERIFIED
