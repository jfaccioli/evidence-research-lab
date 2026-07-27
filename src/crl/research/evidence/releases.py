"""Legacy pre-P1 release packaging (copy-forward + mandatory banner).

Never rewrites source narratives in place as a truth upgrade. Writes only
under an explicit destination root (temp dirs in tests).
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from crl.research.evidence.volatile import (
    is_volatile_research_path,
    refuse_stable_release_of_volatile,
)

LEGACY_PRE_P1_BANNER = """\
<!-- legacy_pre_p1: NOT post-P1 validated scientific truth -->
> **LEGACY PRE-P1 RELEASE**
>
> This package is a **copy-forward** of historical research artefacts for
> audit/context only. It is **not** upgraded to post-P1 COMPLETE authority.
> Do not treat conclusions herein as promotable evidence under the governed
> epoch without a separate human-approved legacy census and P1 gates.
>
> Packaging does not rewrite source files in place.
"""

LEGACY_BANNER_MARKER = "legacy_pre_p1"


class ReleaseError(RuntimeError):
    """Release packaging failed (fail closed)."""


def _utc_now() -> str:
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}Z"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class ReleaseMember:
    relative_path: str
    sha256: str
    byte_size: int
    banner_applied: bool


@dataclass(frozen=True)
class LegacyPreP1Release:
    release_id: str
    created_at: str
    destination_root: str
    members: tuple[ReleaseMember, ...]
    banner_text_sha256: str
    manifest_sha256: str


def package_legacy_pre_p1_release(
    *,
    source_files: Mapping[str, str | Path],
    destination_root: str | Path,
    release_id: str,
    allow_volatile: bool = False,
) -> LegacyPreP1Release:
    """Copy sources into destination with mandatory legacy banner for markdown.

    - ``source_files`` maps release-relative path → absolute/local source path.
    - Destination must not already exist.
    - Volatile paths (latest_plan, proposed/, …) rejected unless allow_volatile
      (still never labeled authoritative).
    - Markdown/text narrative files receive the legacy banner prefix.
    - Binary/json machine files are copied bytes-identical; manifest records them
      as legacy_pre_p1 members without banner injection when not text narrative.
    """
    dest = Path(destination_root).expanduser().resolve()
    if dest.exists() or dest.is_symlink():
        raise ReleaseError(f"destination already exists (no overwrite): {dest}")
    if not source_files:
        raise ReleaseError("release requires at least one source file")
    rid = str(release_id).strip()
    if not rid or "/" in rid or "\\" in rid or rid in (".", ".."):
        raise ReleaseError("release_id must be a single safe path component")

    members: list[ReleaseMember] = []
    dest.mkdir(parents=False, exist_ok=False)
    try:
        for rel_raw, src_raw in sorted(source_files.items(), key=lambda x: x[0]):
            rel = str(rel_raw).replace("\\", "/").strip().lstrip("/")
            parts = tuple(p for p in rel.split("/") if p != "")
            if not rel or any(p in (".", "..") for p in parts):
                raise ReleaseError(f"invalid relative path: {rel_raw!r}")
            if not allow_volatile:
                refuse_stable_release_of_volatile(rel)
            elif is_volatile_research_path(rel):
                # Even if allowed into a dry-run package, never omit banner duty.
                pass
            src = Path(src_raw)
            if src.is_symlink() or not src.is_file():
                raise ReleaseError(f"source must be a regular file: {src}")
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            banner_applied = False
            if _is_narrative_text(src):
                text = src.read_text(encoding="utf-8")
                if LEGACY_BANNER_MARKER not in text[:500]:
                    text = LEGACY_PRE_P1_BANNER + "\n" + text
                    banner_applied = True
                else:
                    banner_applied = True
                out.write_text(text, encoding="utf-8", newline="\n")
            else:
                shutil.copyfile(src, out, follow_symlinks=False)
            digest = _sha256_file(out)
            size = out.stat().st_size
            members.append(
                ReleaseMember(
                    relative_path=rel,
                    sha256=digest,
                    byte_size=size,
                    banner_applied=banner_applied,
                )
            )
        # Require at least one banner-applied narrative or explicit non-narrative
        # package still carries release manifest declaring legacy_pre_p1.
        banner_hash = hashlib.sha256(
            LEGACY_PRE_P1_BANNER.encode("utf-8")
        ).hexdigest()
        created = _utc_now()
        manifest = {
            "release_type": "legacy_pre_p1",
            "release_id": rid,
            "created_at": created,
            "banner_required": True,
            "banner_sha256": banner_hash,
            "authoritative": False,
            "truth_upgrade": False,
            "members": [
                {
                    "relative_path": m.relative_path,
                    "sha256": m.sha256,
                    "byte_size": m.byte_size,
                    "banner_applied": m.banner_applied,
                }
                for m in members
            ],
        }
        man_text = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        man_path = dest / "RELEASE_MANIFEST.json"
        man_path.write_text(man_text + "\n", encoding="utf-8")
        man_sha = hashlib.sha256(man_path.read_bytes()).hexdigest()
        # Fail closed: every markdown narrative must have banner.
        for m in members:
            if m.relative_path.endswith((".md", ".markdown")) and not m.banner_applied:
                raise ReleaseError(
                    f"legacy banner missing on narrative: {m.relative_path}"
                )
        return LegacyPreP1Release(
            release_id=rid,
            created_at=created,
            destination_root=str(dest),
            members=tuple(members),
            banner_text_sha256=banner_hash,
            manifest_sha256=man_sha,
        )
    except Exception:
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        raise


def _is_narrative_text(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix in {".md", ".markdown", ".txt", ".rst"}


def default_banner_template_path() -> Path:
    """Repo docs template path (may be missing in stripped installs)."""
    return (
        Path(__file__).resolve().parents[4]
        / "docs"
        / "templates"
        / "legacy_pre_p1_banner.md"
    )
