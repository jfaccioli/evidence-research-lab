"""Deterministic immutable artefact bundles under a caller-supplied root.

Stages source bytes, hashes copies, builds a canonical manifest + Merkle root,
verifies the complete sealed directory, then publishes with exclusive
no-replace semantics. Never defaults to repository research_kb/reports/live
paths. ``SealedBundle`` is a return type only — registration must reopen and
verify under the explicit artefact root.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
import stat
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence

from crl.research.artifacts.merkle import merkle_root_from_members
from crl.research.artifacts.paths import (
    ArtifactPathError,
    cohort_bundle_relative_root,
    normalize_member_path,
    require_artifact_root,
    require_safe_path_component,
    resolve_under_root,
    run_bundle_relative_root,
    run_identity_relative_root,
)

MANIFEST_FILENAME = "MANIFEST.json"


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


class BundleError(RuntimeError):
    """Bundle stage/seal/publish failed (fail closed)."""


def _utc_text(value: Optional[datetime] = None) -> str:
    dt = value or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}Z"


def _sha256_hex(value: str, field: str) -> str:
    text = str(value).strip().lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise BundleError(f"{field} must be lowercase SHA-256 hex")
    return text


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def new_artifact_id() -> str:
    """Mint a fresh immutable artefact identity."""
    return f"art_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class BundleLineage:
    """Required immutable lineage hashes for a sealed bundle."""

    research_lineage_id: str
    programme_version_id: str
    config_hash: str
    candidate_spec_hash: str
    split_manifest_hash: str
    data_hash: str
    feature_hash: str
    dependency_lock_hash: str
    trial_id: Optional[str] = None

    def normalized(self) -> "BundleLineage":
        rl = str(self.research_lineage_id).strip()
        pv = str(self.programme_version_id).strip()
        if not rl or not pv:
            raise BundleError("research_lineage_id and programme_version_id required")
        trial = (
            str(self.trial_id).strip()
            if self.trial_id is not None and str(self.trial_id).strip()
            else None
        )
        return BundleLineage(
            research_lineage_id=rl,
            programme_version_id=pv,
            config_hash=_sha256_hex(self.config_hash, "config_hash"),
            candidate_spec_hash=_sha256_hex(
                self.candidate_spec_hash, "candidate_spec_hash"
            ),
            split_manifest_hash=_sha256_hex(
                self.split_manifest_hash, "split_manifest_hash"
            ),
            data_hash=_sha256_hex(self.data_hash, "data_hash"),
            feature_hash=_sha256_hex(self.feature_hash, "feature_hash"),
            dependency_lock_hash=_sha256_hex(
                self.dependency_lock_hash, "dependency_lock_hash"
            ),
            trial_id=trial,
        )


@dataclass(frozen=True)
class SealedBundle:
    """Result of a successful seal+publish under the artefact root.

    Not proof for registration: public DB methods must reopen and verify.
    """

    artifact_id: str
    bundle_kind: str
    run_id: Optional[str]
    cohort_id: Optional[str]
    relative_root: str
    absolute_root: Path
    merkle_root: str
    manifest_sha256: str
    byte_size: int
    lineage: BundleLineage
    member_count: int
    sealed_at: str
    is_correction: bool
    supersedes_artifact_id: Optional[str]


@dataclass(frozen=True)
class VerifiedBundleReceipt:
    """Facts derived solely from a reopened, fully verified sealed directory."""

    artifact_id: str
    bundle_kind: str
    run_id: Optional[str]
    cohort_id: Optional[str]
    relative_root: str
    absolute_root: Path
    merkle_root: str
    manifest_sha256: str
    byte_size: int
    lineage: BundleLineage
    member_count: int
    sealed_at: str
    is_correction: bool
    supersedes_artifact_id: Optional[str]


def _assert_regular_file(path: Path) -> None:
    if path.is_symlink():
        raise BundleError(f"symlink inputs are forbidden: {path}")
    if not path.exists():
        raise BundleError(f"source file missing: {path}")
    if not path.is_file():
        raise BundleError(f"non-regular source file forbidden: {path}")
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise BundleError(f"non-regular source file forbidden: {path}")


def _assert_no_symlink_path_components(path: Path) -> Path:
    """Walk every path component via lstat; reject any symlink component."""
    raw = path if path.is_absolute() else (Path.cwd() / path)
    # Normalize without resolving symlinks.
    parts = raw.parts
    if raw.is_absolute():
        accumulated = Path(parts[0])
        rest = parts[1:]
    else:
        accumulated = Path.cwd()
        rest = parts
    for i, part in enumerate(rest):
        accumulated = accumulated / part
        try:
            st = os.lstat(accumulated)
        except FileNotFoundError as exc:
            if i < len(rest) - 1:
                raise BundleError(
                    f"source path missing component: {accumulated}"
                ) from exc
            break
        if stat.S_ISLNK(st.st_mode):
            raise BundleError(
                f"symlink path component forbidden: {accumulated}"
            )
    return accumulated


def _validate_sources(
    sources: Mapping[str, str | Path],
) -> list[tuple[str, Path]]:
    if not sources:
        raise BundleError("bundle requires at least one source member")
    seen: set[str] = set()
    ordered: list[tuple[str, Path]] = []
    for raw_rel, raw_src in sources.items():
        rel = normalize_member_path(raw_rel)
        if rel == MANIFEST_FILENAME or rel.endswith("/" + MANIFEST_FILENAME):
            raise BundleError("MANIFEST.json is reserved for the sealed bundle")
        if rel in seen:
            raise BundleError(f"duplicate normalized member path: {rel!r}")
        seen.add(rel)
        src = Path(raw_src)
        src_abs = _assert_no_symlink_path_components(src)
        if src_abs.is_symlink():
            raise BundleError(f"symlink inputs are forbidden: {src_abs}")
        _assert_regular_file(src_abs)
        ordered.append((rel, src_abs))
    ordered.sort(key=lambda x: x[0])
    return ordered


def _best_effort_rmtree(path: Path, *, root: Path) -> None:
    """Remove only a path created beneath the supplied artefact root."""
    try:
        root_res = root.resolve()
        # Prefer lstat-aware containment: resolve only if not symlink escape.
        target = path.resolve()
        target.relative_to(root_res)
    except Exception:
        return
    if not str(target).startswith(str(root_res)):
        return
    if target == root_res:
        return
    try:
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists() or target.is_symlink():
            try:
                target.unlink()
            except OSError:
                pass
    except OSError:
        pass


def _assert_not_symlink_dir(path: Path, *, label: str) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink():
            raise BundleError(f"{label} must not be a symlink: {path}")
        try:
            st = os.lstat(path)
        except OSError as exc:
            raise BundleError(f"{label} unreadable: {path}") from exc
        if stat.S_ISLNK(st.st_mode):
            raise BundleError(f"{label} must not be a symlink: {path}")


def _exclusive_mkdir(path: Path, *, label: str) -> None:
    """Create a directory only if it does not already exist (fail closed)."""
    if path.exists() or path.is_symlink():
        raise BundleError(f"{label} already exists (no overwrite): {path}")
    try:
        os.mkdir(str(path))
    except FileExistsError as exc:
        raise BundleError(f"{label} already exists (no overwrite): {path}") from exc
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            raise BundleError(
                f"{label} already exists (no overwrite): {path}"
            ) from exc
        raise BundleError(f"{label} exclusive create failed: {exc}") from exc
    if path.is_symlink() or not path.is_dir():
        raise BundleError(f"{label} is not a regular directory after create: {path}")


def _publish_directory_noreplace(
    src: Path,
    dst: Path,
    *,
    _race_hook=None,
) -> None:
    """Publish a staged directory without replacing any pre-existing destination.

    Does **not** use ``os.rename(src, dst)`` onto a path that may already be an
    empty directory (on macOS that replace is allowed and would fail-open).
    Instead: exclusive ``mkdir(dst)`` claims the destination path, then each
    child is renamed into the owned empty directory. A race that creates
    ``dst`` before the exclusive mkdir fails closed and leaves the pre-existing
    destination untouched.
    """
    if not src.is_dir() or src.is_symlink():
        raise BundleError(f"publish source must be a regular directory: {src}")
    if dst.exists() or dst.is_symlink():
        raise BundleError(f"bundle target already exists (no overwrite): {dst}")
    claim = dst.parent / f".{dst.name}.publish-claim"
    try:
        fd = os.open(str(claim), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError as exc:
        raise BundleError(
            f"publication claim held (no overwrite): {dst}"
        ) from exc
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            raise BundleError(
                f"publication claim held (no overwrite): {dst}"
            ) from exc
        raise BundleError(f"publication claim failed: {exc}") from exc
    created_dst = False
    try:
        if dst.exists() or dst.is_symlink():
            raise BundleError(
                f"bundle target already exists (no overwrite): {dst}"
            )
        if _race_hook is not None:
            _race_hook(dst)
        if dst.exists() or dst.is_symlink():
            raise BundleError(
                f"bundle target already exists (no overwrite): {dst}"
            )
        _exclusive_mkdir(dst, label="bundle target")
        created_dst = True
        # Move staged children into the exclusively owned empty destination.
        try:
            with os.scandir(str(src)) as entries:
                children = list(entries)
        except OSError as exc:
            raise BundleError(f"publish source unreadable: {exc}") from exc
        if not children:
            raise BundleError("publish source directory is empty")
        for entry in children:
            dest_child = dst / entry.name
            if dest_child.exists() or dest_child.is_symlink():
                raise BundleError(
                    f"bundle target child already exists (no overwrite): {dest_child}"
                )
            try:
                os.rename(entry.path, str(dest_child))
            except OSError as exc:
                raise BundleError(
                    f"atomic child publish failed (no overwrite): {exc}"
                ) from exc
        try:
            os.rmdir(str(src))
        except OSError as exc:
            raise BundleError(f"failed to remove empty staging directory: {exc}") from exc
        if not dst.is_dir() or dst.is_symlink():
            raise BundleError("post-publish destination is not a regular directory")
    except Exception:
        if created_dst:
            _best_effort_rmtree(dst, root=dst.parent)
        raise
    finally:
        try:
            claim.unlink(missing_ok=True)
        except OSError:
            pass


def _write_manifest(
    staging_dir: Path,
    *,
    artifact_id: str,
    bundle_kind: str,
    run_id: Optional[str],
    cohort_id: Optional[str],
    relative_root: str,
    lineage: BundleLineage,
    members: Sequence[tuple[str, str, int]],
    merkle_root: str,
    sealed_at: str,
    is_correction: bool,
    supersedes_artifact_id: Optional[str],
) -> tuple[str, int]:
    payload = {
        "artifact_id": artifact_id,
        "bundle_kind": bundle_kind,
        "run_id": run_id,
        "cohort_id": cohort_id,
        "relative_root": relative_root,
        "research_lineage_id": lineage.research_lineage_id,
        "programme_version_id": lineage.programme_version_id,
        "trial_id": lineage.trial_id,
        "config_hash": lineage.config_hash,
        "candidate_spec_hash": lineage.candidate_spec_hash,
        "split_manifest_hash": lineage.split_manifest_hash,
        "data_hash": lineage.data_hash,
        "feature_hash": lineage.feature_hash,
        "dependency_lock_hash": lineage.dependency_lock_hash,
        "members": [
            {
                "relative_path": p,
                "sha256": d,
                "byte_size": s,
            }
            for p, d, s in members
        ],
        "merkle_root": merkle_root,
        "sealed_at": sealed_at,
        "is_correction": bool(is_correction),
        "supersedes_artifact_id": supersedes_artifact_id,
        "schema": "crl.artifact_bundle.v1",
    }
    text = _canonical_json(payload)
    data = text.encode("utf-8")
    manifest_path = staging_dir / MANIFEST_FILENAME
    manifest_path.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data)


def _enumerate_bundle_files(bundle_dir: Path) -> set[str]:
    """Return relative POSIX paths of every regular file; reject extras."""
    found: set[str] = set()
    if bundle_dir.is_symlink():
        raise BundleError("sealed bundle must not be a symlink")
    if not bundle_dir.is_dir():
        raise BundleError(f"sealed bundle directory missing: {bundle_dir}")
    for dirpath, dirnames, filenames in os.walk(
        bundle_dir, topdown=True, followlinks=False
    ):
        base = Path(dirpath)
        if base.is_symlink():
            raise BundleError(f"symlink directory inside sealed bundle: {base}")
        # Reject symlink children without following.
        for d in list(dirnames):
            child = base / d
            if child.is_symlink():
                raise BundleError(f"symlink directory inside sealed bundle: {d}")
        for name in filenames:
            child = base / name
            if child.is_symlink():
                raise BundleError(f"symlink inside sealed bundle: {name}")
            try:
                st = child.lstat()
            except OSError as exc:
                raise BundleError(f"unreadable sealed member: {name}") from exc
            if not stat.S_ISREG(st.st_mode):
                raise BundleError(f"non-regular file inside sealed bundle: {name}")
            rel = child.relative_to(bundle_dir).as_posix()
            found.add(rel)
        # Empty subdirectories are not allowed (only declared files + manifest).
        for d in dirnames:
            sub = base / d
            # If a directory has no files anywhere it will still appear; reject
            # empty dirs at verification by checking walk leaves files only.
            # Non-empty undeclared dirs fail because their files are undeclared.
            if sub.is_symlink():
                raise BundleError(f"symlink directory inside sealed bundle: {d}")
    return found


def verify_sealed_bundle_dir(
    bundle_dir: Path,
    *,
    expected_relative_root: Optional[str] = None,
) -> VerifiedBundleReceipt:
    """Verify a sealed directory completely; return derived receipt only."""
    if bundle_dir.is_symlink():
        raise BundleError("sealed bundle must not be a symlink")
    if not bundle_dir.is_dir():
        raise BundleError(f"sealed bundle directory missing: {bundle_dir}")
    manifest_path = bundle_dir / MANIFEST_FILENAME
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise BundleError("MANIFEST.json missing or not a regular file")
    raw = manifest_path.read_bytes()
    manifest_sha = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BundleError("MANIFEST.json is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise BundleError("MANIFEST.json must be an object")
    # Canonical encoding required (byte-identical to canonical re-encode).
    try:
        reencoded = _canonical_json(payload).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BundleError("MANIFEST.json is not canonically encodable") from exc
    if reencoded != raw:
        raise BundleError("non-canonical MANIFEST.json encoding")

    members_raw = payload.get("members")
    if not isinstance(members_raw, list) or not members_raw:
        raise BundleError("MANIFEST.json members must be a non-empty list")
    members: list[tuple[str, str, int]] = []
    declared_paths: list[str] = []
    total = len(raw)
    for item in members_raw:
        if not isinstance(item, dict):
            raise BundleError("invalid manifest member entry")
        try:
            rel = normalize_member_path(str(item["relative_path"]))
        except ArtifactPathError as exc:
            raise BundleError(str(exc)) from exc
        if rel in declared_paths:
            raise BundleError(f"duplicate manifest member path: {rel!r}")
        declared_paths.append(rel)
        digest = str(item["sha256"]).strip().lower()
        size = int(item["byte_size"])
        member_path = bundle_dir / rel
        if member_path.is_symlink():
            raise BundleError(f"symlink inside sealed bundle: {rel}")
        if not member_path.is_file():
            raise BundleError(f"missing sealed member: {rel}")
        actual = _file_sha256(member_path)
        actual_size = member_path.stat().st_size
        if actual != digest or actual_size != size:
            raise BundleError(f"sealed member digest/size mismatch: {rel}")
        members.append((rel, digest, size))
        total += actual_size
    recomputed = merkle_root_from_members(members)
    declared = str(payload.get("merkle_root", "")).strip().lower()
    if declared != recomputed:
        raise BundleError(
            f"manifest merkle_root mismatch: declared={declared} recomputed={recomputed}"
        )

    # Exact filesystem set: MANIFEST.json + declared members only.
    on_disk = _enumerate_bundle_files(bundle_dir)
    expected_files = {MANIFEST_FILENAME, *declared_paths}
    if on_disk != expected_files:
        extra = sorted(on_disk - expected_files)
        missing = sorted(expected_files - on_disk)
        raise BundleError(
            f"sealed directory set mismatch extra={extra} missing={missing}"
        )

    artifact_id = require_safe_path_component(
        str(payload.get("artifact_id", "")), field="artifact_id"
    )
    kind = str(payload.get("bundle_kind", "")).strip().lower()
    if kind not in ("run", "cohort"):
        raise BundleError("manifest bundle_kind must be run or cohort")
    run_id = payload.get("run_id")
    cohort_id = payload.get("cohort_id")
    run_id_s = str(run_id).strip() if run_id is not None else None
    cohort_id_s = str(cohort_id).strip() if cohort_id is not None else None
    if run_id_s == "":
        run_id_s = None
    if cohort_id_s == "":
        cohort_id_s = None
    rel_root = normalize_member_path(str(payload.get("relative_root", "")))
    if expected_relative_root is not None and rel_root != normalize_member_path(
        expected_relative_root
    ):
        raise BundleError("manifest relative_root does not match expected path")
    trial_raw = payload.get("trial_id")
    trial_id = (
        str(trial_raw).strip()
        if trial_raw is not None and str(trial_raw).strip()
        else None
    )
    if kind == "run":
        if not run_id_s or cohort_id_s is not None or not trial_id:
            raise BundleError("run manifest requires run_id+trial_id and forbids cohort_id")
    else:
        if not cohort_id_s or run_id_s is not None:
            raise BundleError("cohort manifest requires cohort_id and forbids run_id")

    is_correction = bool(payload.get("is_correction"))
    supersedes_raw = payload.get("supersedes_artifact_id")
    supersedes: Optional[str]
    if is_correction:
        if not supersedes_raw:
            raise BundleError("correction manifest requires supersedes_artifact_id")
        supersedes = str(supersedes_raw).strip()
        if not supersedes:
            raise BundleError("correction manifest requires supersedes_artifact_id")
    else:
        if supersedes_raw not in (None, ""):
            raise BundleError("ordinary manifest must not set supersedes_artifact_id")
        supersedes = None

    try:
        lineage = BundleLineage(
            research_lineage_id=str(payload.get("research_lineage_id", "")),
            programme_version_id=str(payload.get("programme_version_id", "")),
            config_hash=str(payload.get("config_hash", "")),
            candidate_spec_hash=str(payload.get("candidate_spec_hash", "")),
            split_manifest_hash=str(payload.get("split_manifest_hash", "")),
            data_hash=str(payload.get("data_hash", "")),
            feature_hash=str(payload.get("feature_hash", "")),
            dependency_lock_hash=str(payload.get("dependency_lock_hash", "")),
            trial_id=trial_id,
        ).normalized()
    except BundleError:
        raise
    except Exception as exc:
        raise BundleError(f"manifest lineage invalid: {exc}") from exc

    sealed_at = str(payload.get("sealed_at", ""))
    if len(sealed_at) != 27 or not sealed_at.endswith("Z"):
        raise BundleError("manifest sealed_at invalid")

    return VerifiedBundleReceipt(
        artifact_id=artifact_id,
        bundle_kind=kind,
        run_id=run_id_s,
        cohort_id=cohort_id_s,
        relative_root=rel_root,
        absolute_root=bundle_dir,
        merkle_root=recomputed,
        manifest_sha256=manifest_sha,
        byte_size=total,
        lineage=lineage,
        member_count=len(members),
        sealed_at=sealed_at,
        is_correction=is_correction,
        supersedes_artifact_id=supersedes,
    )


def seal_bundle(
    *,
    artifact_root: str | Path,
    bundle_kind: str,
    sources: Mapping[str, str | Path],
    lineage: BundleLineage,
    run_id: Optional[str] = None,
    cohort_id: Optional[str] = None,
    artifact_id: Optional[str] = None,
    is_correction: bool = False,
    supersedes_artifact_id: Optional[str] = None,
    sealed_at: Optional[datetime] = None,
    _race_hook=None,
) -> SealedBundle:
    """Stage, hash, verify, and atomically publish one immutable bundle."""
    root = require_artifact_root(artifact_root)
    root.mkdir(parents=True, exist_ok=True)
    _assert_not_symlink_dir(root, label="artifact_root")
    kind = str(bundle_kind).strip().lower()
    if kind not in ("run", "cohort"):
        raise BundleError("bundle_kind must be 'run' or 'cohort'")
    lineage_n = lineage.normalized()
    aid = require_safe_path_component(
        artifact_id or new_artifact_id(), field="artifact_id"
    )
    correction = bool(is_correction)
    supersedes: Optional[str] = None
    if correction:
        if not supersedes_artifact_id:
            raise BundleError("corrections require supersedes_artifact_id")
        supersedes = require_safe_path_component(
            str(supersedes_artifact_id), field="supersedes_artifact_id"
        )
        if supersedes == aid:
            raise BundleError("correction cannot supersede itself")
    else:
        if supersedes_artifact_id:
            raise BundleError(
                "ordinary seal must not set supersedes_artifact_id "
                "(corrections require is_correction=True)"
            )

    created_run_identity = False
    run_identity_dir: Optional[Path] = None
    if kind == "run":
        if not run_id or cohort_id is not None:
            raise BundleError("run bundles require run_id and forbid cohort_id")
        if lineage_n.trial_id is None:
            raise BundleError("run bundles require lineage.trial_id")
        rid = require_safe_path_component(str(run_id), field="run_id")
        cid: Optional[str] = None
        identity_rel = run_identity_relative_root(rid)
        rel_root = run_bundle_relative_root(rid, aid)
        run_identity_dir = resolve_under_root(root, identity_rel)
        final_dir = resolve_under_root(root, rel_root)
    else:
        if not cohort_id or run_id is not None:
            raise BundleError("cohort bundles require cohort_id and forbid run_id")
        rid = None
        cid = require_safe_path_component(str(cohort_id), field="cohort_id")
        rel_root = cohort_bundle_relative_root(cid, aid)
        final_dir = resolve_under_root(root, rel_root)

    if final_dir.exists() or final_dir.is_symlink():
        raise BundleError(
            f"bundle target already exists (no overwrite): {rel_root}"
        )

    members_src = _validate_sources(sources)
    token = uuid.uuid4().hex
    staging_parent = root / ".staging"
    if staging_parent.exists() or staging_parent.is_symlink():
        _assert_not_symlink_dir(staging_parent, label="staging parent")
    else:
        staging_parent.mkdir(parents=True, exist_ok=False)
        _assert_not_symlink_dir(staging_parent, label="staging parent")
    staging = staging_parent / f"{kind}-{token}"
    created_staging = False
    created_final = False
    try:
        staging.mkdir(parents=False, exist_ok=False)
        created_staging = True
        members: list[tuple[str, str, int]] = []
        for rel, src in members_src:
            dest = staging / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest, follow_symlinks=False)
            if dest.is_symlink():
                raise BundleError("refusing symlink created in staging")
            digest = _file_sha256(dest)
            size = dest.stat().st_size
            members.append((rel, digest, size))
        members.sort(key=lambda m: m[0])
        merkle = merkle_root_from_members(members)
        sealed_text = _utc_text(sealed_at)
        manifest_sha, _manifest_size = _write_manifest(
            staging,
            artifact_id=aid,
            bundle_kind=kind,
            run_id=rid,
            cohort_id=cid,
            relative_root=rel_root,
            lineage=lineage_n,
            members=members,
            merkle_root=merkle,
            sealed_at=sealed_text,
            is_correction=correction,
            supersedes_artifact_id=supersedes,
        )
        # Verify staged directory before publish (complete set).
        staged_receipt = verify_sealed_bundle_dir(
            staging, expected_relative_root=rel_root
        )
        if (
            staged_receipt.merkle_root != merkle
            or staged_receipt.manifest_sha256 != manifest_sha
            or staged_receipt.artifact_id != aid
        ):
            raise BundleError("pre-publish verification mismatch")

        # Claim run identity exclusively before any evidence lands under it.
        # Do not mkdir(exist_ok=True) the identity path — that would silently
        # create the exclusive claim and break no-replace semantics.
        if kind == "run":
            assert run_identity_dir is not None
            runs_parent = run_identity_dir.parent
            runs_parent.mkdir(parents=True, exist_ok=True)
            _assert_not_symlink_dir(runs_parent, label="runs parent")
            if run_identity_dir.exists() or run_identity_dir.is_symlink():
                raise BundleError(
                    f"run identity already exists (no overwrite): {identity_rel}"
                )
            _exclusive_mkdir(run_identity_dir, label="run identity")
            created_run_identity = True
            _assert_not_symlink_dir(run_identity_dir, label="run identity")
        else:
            final_dir.parent.mkdir(parents=True, exist_ok=True)
            _assert_not_symlink_dir(final_dir.parent, label="bundle parent")
        _publish_directory_noreplace(
            staging, final_dir, _race_hook=_race_hook
        )
        created_staging = False
        created_final = True
        created_run_identity = False  # owned by successful publish
        final_receipt = verify_sealed_bundle_dir(
            final_dir, expected_relative_root=rel_root
        )
        if (
            final_receipt.merkle_root != merkle
            or final_receipt.manifest_sha256 != manifest_sha
            or final_receipt.artifact_id != aid
        ):
            raise BundleError("post-publish verification mismatch")
        return SealedBundle(
            artifact_id=aid,
            bundle_kind=kind,
            run_id=rid,
            cohort_id=cid,
            relative_root=rel_root,
            absolute_root=final_dir,
            merkle_root=merkle,
            manifest_sha256=manifest_sha,
            byte_size=final_receipt.byte_size,
            lineage=lineage_n,
            member_count=final_receipt.member_count,
            sealed_at=sealed_text,
            is_correction=correction,
            supersedes_artifact_id=supersedes,
        )
    except (ArtifactPathError, OSError, ValueError) as exc:
        if isinstance(exc, BundleError):
            raise
        raise BundleError(str(exc)) from exc
    finally:
        if created_staging and staging.exists():
            _best_effort_rmtree(staging, root=root)
        if created_final and final_dir.exists() and sys.exc_info()[0] is not None:
            _best_effort_rmtree(final_dir, root=root)
        if (
            created_run_identity
            and run_identity_dir is not None
            and run_identity_dir.exists()
            and sys.exc_info()[0] is not None
        ):
            # Only remove an empty identity we created. Never delete foreign
            # content that may have raced under the identity path.
            try:
                if not any(run_identity_dir.iterdir()):
                    run_identity_dir.rmdir()
            except OSError:
                pass


def list_filesystem_bundle_roots(artifact_root: str | Path) -> list[str]:
    """List relative bundle roots present on disk (may include orphans)."""
    root = require_artifact_root(artifact_root)
    found: list[str] = []
    runs = root / "artifacts" / "runs"
    if runs.is_dir() and not runs.is_symlink():
        for run_dir in sorted(runs.iterdir()):
            if not run_dir.is_dir() or run_dir.is_symlink():
                continue
            # Exclusive identity layout: artifacts/runs/{run_id}/{artifact_id}
            for child in sorted(run_dir.iterdir()):
                if child.is_dir() and not child.is_symlink():
                    found.append(
                        f"artifacts/runs/{run_dir.name}/{child.name}"
                    )
    cohorts = root / "artifacts" / "cohorts"
    if cohorts.is_dir() and not cohorts.is_symlink():
        for cohort_dir in sorted(cohorts.iterdir()):
            if not cohort_dir.is_dir() or cohort_dir.is_symlink():
                continue
            for child in sorted(cohort_dir.iterdir()):
                if child.is_dir() and not child.is_symlink():
                    found.append(
                        f"artifacts/cohorts/{cohort_dir.name}/{child.name}"
                    )
    return found
