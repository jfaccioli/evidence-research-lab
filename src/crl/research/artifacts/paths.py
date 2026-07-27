"""Bounded artefact-root path validation (fail closed).

Never infers repository ``research_kb``, ``reports``, or live paths.
"""

from __future__ import annotations

import os
import re
from pathlib import Path, PurePosixPath

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ArtifactPathError(ValueError):
    """Member path rejected by bounded artefact-root rules."""


def require_artifact_root(root: str | Path) -> Path:
    """Resolve and require an explicit caller-supplied artefact root directory."""
    if root is None:
        raise ArtifactPathError("artifact_root is required (no default)")
    text = str(root).strip()
    if not text:
        raise ArtifactPathError("artifact_root must be non-empty")
    path = Path(text).expanduser().resolve()
    return path


def require_safe_path_component(value: str, *, field: str) -> str:
    """Require a single non-empty, non-traversal path component."""
    if value is None:
        raise ArtifactPathError(f"{field} is required")
    text = str(value).strip()
    if not text:
        raise ArtifactPathError(f"{field} must be non-empty")
    if text in (".", "..") or "/" in text or "\\" in text or "\0" in text:
        raise ArtifactPathError(
            f"{field} must be a single safe path component (no traversal)"
        )
    if not _SAFE_ID_RE.fullmatch(text):
        raise ArtifactPathError(
            f"{field} must be a single safe path component (no traversal)"
        )
    return text


def normalize_member_path(member: str) -> str:
    """Normalize a relative member path; reject absolute/traversal/empty/dot."""
    if member is None:
        raise ArtifactPathError("member path is required")
    raw = str(member)
    if raw == "" or raw.strip() == "":
        raise ArtifactPathError("member path must be non-empty")
    if "\\" in raw:
        raise ArtifactPathError("member path must use POSIX separators only")
    if "//" in raw:
        raise ArtifactPathError("member path rejects empty path components")
    if raw.startswith("/") or raw.startswith("~"):
        raise ArtifactPathError("absolute member paths are forbidden")
    # Windows drive letters
    if len(raw) >= 2 and raw[1] == ":":
        raise ArtifactPathError("absolute member paths are forbidden")
    pure = PurePosixPath(raw)
    parts = pure.parts
    if not parts:
        raise ArtifactPathError("member path must be non-empty")
    if pure.is_absolute():
        raise ArtifactPathError("absolute member paths are forbidden")
    normalized_parts: list[str] = []
    for part in parts:
        if part in ("", ".", ".."):
            raise ArtifactPathError(
                f"member path rejects empty/dot/parent components: {raw!r}"
            )
        if part.startswith("/") or "\\" in part:
            raise ArtifactPathError(f"invalid member path component: {part!r}")
        normalized_parts.append(part)
    return "/".join(normalized_parts)


def resolve_under_root(root: Path, relative: str) -> Path:
    """Resolve ``relative`` strictly beneath ``root`` (no escape)."""
    rel = normalize_member_path(relative)
    root_res = root.resolve()
    # Join without resolving intermediate symlinks first, then resolve and check.
    candidate = (root_res / rel).resolve()
    try:
        candidate.relative_to(root_res)
    except ValueError as exc:
        raise ArtifactPathError(
            f"path escapes artefact root: {relative!r}"
        ) from exc
    # Extra string guard for symlink races before materialization.
    root_s = str(root_res)
    cand_s = str(candidate)
    if cand_s != root_s and not cand_s.startswith(root_s + os.sep):
        raise ArtifactPathError(f"path escapes artefact root: {relative!r}")
    return candidate


def run_identity_relative_root(run_id: str) -> str:
    """Exclusive run identity directory (owned via mkdir exist_ok=False)."""
    rid = require_safe_path_component(run_id, field="run_id")
    return f"artifacts/runs/{rid}"


def run_bundle_relative_root(run_id: str, artifact_id: str) -> str:
    """Sealed run bundle path: exclusive run identity + fixed artefact child.

    Layout: ``artifacts/runs/{run_id}/{artifact_id}/``. The identity directory
    is claimed with exclusive mkdir before any evidence is published; the
    sealed tree lives in the artefact child so pre-existing run identities
    cannot be replaced by directory rename.
    """
    rid = require_safe_path_component(run_id, field="run_id")
    aid = require_safe_path_component(artifact_id, field="artifact_id")
    return f"artifacts/runs/{rid}/{aid}"


def cohort_bundle_relative_root(cohort_id: str, artifact_id: str) -> str:
    """Cohort path binds logical cohort_id plus distinct artefact identity.

    Corrections may retain the same logical cohort_id while publishing a new
    artefact_id/path; old directories never mutate.
    """
    cid = require_safe_path_component(cohort_id, field="cohort_id")
    aid = require_safe_path_component(artifact_id, field="artifact_id")
    return f"artifacts/cohorts/{cid}/{aid}"
