"""Inventory pre-registered research programmes under examples/batch."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from crl.shared.config import project_root


@dataclass
class ProgrammeInfo:
    name: str
    path: str
    n_hyps: int
    has_index: bool
    has_exploratory_note: bool
    has_gate_autopsy: bool
    design_doc: Optional[str]
    outcome_hint: Optional[str]


_OUTCOME_RE = re.compile(
    r"(0/\d+|1/\d+|\d+/\d+)\s*(passed_val|`passed_val`)|passed_val[^\n]{0,40}",
    re.I,
)


def _outcome_hint(note_path: Path) -> Optional[str]:
    if not note_path.exists():
        return None
    text = note_path.read_text()[:800]
    m = _OUTCOME_RE.search(text)
    if m:
        return m.group(0).replace("\n", " ")[:80]
    if "null" in text.lower():
        return "null (see note)"
    if "failed_test" in text.lower():
        return "confirmatory failed_test (see note)"
    return "see EXPLORATORY_NOTE"


def list_programmes(batch_root: Path | None = None) -> list[ProgrammeInfo]:
    root = project_root()
    batch = batch_root or (root / "examples" / "batch")
    if not batch.exists():
        return []
    out: list[ProgrammeInfo] = []
    for p in sorted(batch.iterdir()):
        if not p.is_dir():
            continue
        hyps = sorted(p.glob("hyp_*.yaml"))
        if not hyps and not (p / "INDEX.yaml").exists():
            continue
        design = None
        # common design paths
        candidates = [
            root / "docs" / f"PROGRAMME_{p.name.upper()}_V1.md",
            root / "docs" / f"PROGRAMME_{p.name.upper()}.md",
        ]
        # funding special names
        special = {
            "funding": "PROGRAMME_FUNDING_PIT_V1.md",
            "funding_4h": "PROGRAMME_FUNDING_4H_POWER_V1.md",
            "oi": "PROGRAMME_OI_PIT_V1.md",
            "capacity": "PROGRAMME_CAPACITY_TINY_FRICTION_V1.md",
            "asymmetric": "PROGRAMME_ASYMMETRIC_CAPTURE_V2.md",
            "hold_4h": "PROGRAMME_HOLD_4H_V1.md",
            "breakout_4h": "PROGRAMME_BREAKOUT_4H_POWER_V1.md",
            "vol_regime": "PROGRAMME_VOL_REGIME_V1.md",
            "slow_fast": "PROGRAMME_SLOW_FAST_V1.md",
            "atr_trail": "PROGRAMME_ATR_TRAIL_V1.md",
            "liquidity": "PROGRAMME_LIQUIDITY_PANIC_V1.md",
            "calendar": "PROGRAMME_CALENDAR_V1.md",
            "breakout": "PROGRAMME_BREAKOUT_V1.md",
            "volume": "PROGRAMME_VOLUME_V1.md",
            "fade": "PROGRAMME_FADE_V1.md",
            "herding": "PROGRAMME_HERDING_V1.md",
            "risk_off": "PROGRAMME_RISK_OFF_V1.md",
        }
        if p.name in special:
            candidates.insert(0, root / "docs" / special[p.name])
        for c in candidates:
            if c.exists():
                design = str(c.relative_to(root))
                break
        note = p / "EXPLORATORY_NOTE.md"
        out.append(
            ProgrammeInfo(
                name=p.name,
                path=str(p.relative_to(root)),
                n_hyps=len(hyps),
                has_index=(p / "INDEX.yaml").exists(),
                has_exploratory_note=note.exists(),
                has_gate_autopsy=(p / "GATE_AUTOPSY_V1.md").exists()
                or (p / "GATE_AUTOPSY.md").exists(),
                design_doc=design,
                outcome_hint=_outcome_hint(note) if note.exists() else None,
            )
        )
    return out


def programmes_to_dict(rows: list[ProgrammeInfo]) -> dict[str, Any]:
    return {
        "n_programmes": len(rows),
        "n_hyps_total": sum(r.n_hyps for r in rows),
        "programmes": [asdict(r) for r in rows],
    }
