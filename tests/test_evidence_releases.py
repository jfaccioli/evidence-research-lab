"""PR6 legacy_pre_p1 release packaging."""

from __future__ import annotations

from pathlib import Path

import pytest

from crl.research.evidence.releases import (
    LEGACY_BANNER_MARKER,
    ReleaseError,
    package_legacy_pre_p1_release,
)
from crl.research.evidence.volatile import (
    is_volatile_research_path,
    refuse_stable_release_of_volatile,
)


def test_latest_plan_is_volatile():
    assert is_volatile_research_path("research_kb/latest_plan.json")
    assert is_volatile_research_path("latest_plan.md")
    assert is_volatile_research_path("research_kb/proposed/foo.yaml")
    with pytest.raises(ValueError, match="volatile"):
        refuse_stable_release_of_volatile("latest_plan.json")


def test_legacy_release_requires_banner_and_no_source_rewrite(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    narrative = src_dir / "META.md"
    narrative.write_text("# Old conclusions\nStill historical.\n", encoding="utf-8")
    original = narrative.read_text(encoding="utf-8")
    dest = tmp_path / "release_out"
    rel = package_legacy_pre_p1_release(
        source_files={"META.md": narrative},
        destination_root=dest,
        release_id="legacy_pack_1",
    )
    assert rel.manifest_sha256
    out = dest / "META.md"
    text = out.read_text(encoding="utf-8")
    assert LEGACY_BANNER_MARKER in text
    assert "Old conclusions" in text
    # Source not rewritten in place
    assert narrative.read_text(encoding="utf-8") == original
    assert (dest / "RELEASE_MANIFEST.json").is_file()


def test_volatile_path_rejected_in_stable_release(tmp_path: Path):
    src = tmp_path / "latest_plan.md"
    src.write_text("plan", encoding="utf-8")
    with pytest.raises((ReleaseError, ValueError)):
        package_legacy_pre_p1_release(
            source_files={"latest_plan.md": src},
            destination_root=tmp_path / "out",
            release_id="bad",
        )


def test_destination_no_overwrite(tmp_path: Path):
    src = tmp_path / "a.md"
    src.write_text("x", encoding="utf-8")
    dest = tmp_path / "out"
    package_legacy_pre_p1_release(
        source_files={"a.md": src},
        destination_root=dest,
        release_id="r1",
    )
    with pytest.raises(ReleaseError, match="already exists"):
        package_legacy_pre_p1_release(
            source_files={"a.md": src},
            destination_root=dest,
            release_id="r2",
        )
