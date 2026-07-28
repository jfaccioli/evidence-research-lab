"""Lab health check — strong tool reliability surface."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from crl.production.modes import LIVE_ENV_FLAG, live_explicitly_enabled
from crl.shared.config import load_config, project_root


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


@dataclass
class DoctorReport:
    ok: bool
    checks: list[Check] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": [asdict(c) for c in self.checks],
            "notes": self.notes,
        }


def run_doctor(config_path: str | None = None) -> DoctorReport:
    root = project_root()
    cfg = load_config(config_path)
    checks: list[Check] = []
    notes: list[str] = []

    # Config / gates present
    default_cfg = root / "configs" / "default.yaml"
    checks.append(
        Check(
            "default_config",
            default_cfg.exists(),
            str(default_cfg) if default_cfg.exists() else "missing configs/default.yaml",
        )
    )
    gates = cfg.get("gates") or {}
    checks.append(
        Check(
            "gates_loaded",
            bool(gates.get("min_trades")) and "sharpe_min" in gates,
            f"min_trades={gates.get('min_trades')} sharpe_min={gates.get('sharpe_min')}",
        )
    )

    # LIVE hard-disabled by default
    live_on = live_explicitly_enabled(config=cfg)
    checks.append(
        Check(
            "live_disabled_by_default",
            not live_on,
            f"{LIVE_ENV_FLAG} and phase5 flags must both be set for LIVE; currently live_on={live_on}",
        )
    )
    from crl.production.kill_switch import is_kill_switch_engaged

    ks = is_kill_switch_engaged()
    checks.append(
        Check(
            "kill_switch_readable",
            True,
            f"engaged={ks} (ops latch; paper refuses if engaged)",
        )
    )

    # Datasets
    mdir = root / cfg.get("data", {}).get("manifest_dir", "data/manifests")
    manifests = list(mdir.glob("binance_public_*.json")) if mdir.exists() else []
    has_1d = any("1d" in m.name for m in manifests)
    has_4h = any("4h" in m.name for m in manifests)
    checks.append(Check("ohlcv_1d_manifest", has_1d, f"manifests={len(manifests)} dir={mdir}"))
    checks.append(Check("ohlcv_4h_manifest", has_4h, "optional but recommended for power studies"))

    # Programme dirs
    from crl.ops.programmes import list_programmes

    progs = list_programmes()
    prog_dirs = [p.name for p in progs]
    missing_notes = [p.name for p in progs if not p.has_exploratory_note]
    checks.append(
        Check(
            "programme_dirs",
            len(prog_dirs) > 0,
            f"n={len(prog_dirs)} hyps_total={sum(p.n_hyps for p in progs)}",
        )
    )
    # Soft: missing notes do not fail doctor (run-programme will create notes).
    checks.append(
        Check(
            "programme_notes_coverage",
            True,
            "all have EXPLORATORY_NOTE"
            if not missing_notes
            else f"missing notes (warn): {missing_notes[:12]}",
        )
    )

    # Paper / shadow import surface
    try:
        from crl.production.paper.session import run_paper_session  # noqa: F401
        from crl.production.shadow.walk import shadow_walk  # noqa: F401
        from crl.production.risk_envelope import check_order  # noqa: F401

        checks.append(Check("production_imports", True, "paper/shadow/risk_envelope"))
    except Exception as e:
        checks.append(Check("production_imports", False, str(e)))

    # Docs
    for rel in (
        "docs/PROMOTION_LADDER.md",
        "docs/AUTONOMOUS_CHARTER.md",
        "docs/STATUS_LIVE_READINESS.md",
        "docs/OPERATOR_RUNBOOK.md",
        "AGENTS.md",
    ):
        p = root / rel
        checks.append(Check(f"doc:{rel}", p.exists(), str(p)))

    # Production surface
    try:
        from crl.production.execution import place_order

        try:
            place_order()
            bare_ok = False
            bare_detail = "place_order did not raise"
        except RuntimeError as e:
            bare_ok = "disabled" in str(e).lower() or "LIVE" in str(e) or "Phase" in str(e)
            bare_detail = str(e)[:120]
        checks.append(Check("bare_place_order_disabled", bare_ok, bare_detail))
    except Exception as e:
        checks.append(Check("bare_place_order_disabled", False, str(e)))

    # Thesis tree
    thesis = root / "research_kb" / "THESIS_TREE.md"
    checks.append(Check("thesis_tree_md", thesis.exists(), str(thesis)))

    notes.append(
        "Strong tool = fail-closed research + paper/shadow scaffolding; "
        "not forced alpha. See docs/META_NULL_SYNTHESIS_2026-07-27.md."
    )
    notes.append("Use temp registry for exploratory programme batches; do not soften gates.")

    ok = all(c.ok for c in checks if c.name != "ohlcv_4h_manifest")  # 4h optional soft
    # soft-fail 4h: still overall ok if only 4h missing
    hard = [c for c in checks if c.name != "ohlcv_4h_manifest"]
    ok = all(c.ok for c in hard)
    return DoctorReport(ok=ok, checks=checks, notes=notes)
