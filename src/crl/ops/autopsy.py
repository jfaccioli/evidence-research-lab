"""Build gate autopsy markdown from exploratory report JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from crl.shared.config import project_root


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def collect_reports_for_programme(
    hyp_dir: Path,
    *,
    reports_dir: Path | None = None,
    mode: str = "exploratory",
) -> list[dict[str, Any]]:
    root = project_root()
    reports_dir = reports_dir or (root / "reports")
    hyp_dir = Path(hyp_dir)
    rows: list[dict[str, Any]] = []
    for yml in sorted(hyp_dir.glob("hyp_*.yaml")):
        hid = yml.stem  # hyp_foo
        # reports named hyp_*_v1_exploratory.json
        candidates = list(reports_dir.glob(f"{hid}_*_v1_{mode}.json"))
        if not candidates:
            candidates = list(reports_dir.glob(f"{hid}_v1_{mode}.json"))
        if not candidates:
            # try version-less
            candidates = list(reports_dir.glob(f"{hid}*{mode}.json"))
        if not candidates:
            rows.append({"id": hid, "missing_report": True})
            continue
        path = max(candidates, key=lambda p: p.stat().st_mtime)
        d = _load_report(path)
        val = (d.get("metrics") or {}).get("val") or {}
        gates = d.get("gates") or {}
        stats = d.get("stats") or {}
        ci = stats.get("sharpe_ci") or [None, None]
        rows.append(
            {
                "id": d.get("hypothesis", {}).get("id") or hid,
                "status": d.get("final_status"),
                "n_trades": val.get("n_trades"),
                "sharpe": val.get("sharpe_after_cost"),
                "excess_bh": val.get("excess_return_vs_bh"),
                "ci_lo": ci[0] if ci else None,
                "reasons": gates.get("reasons") or [],
                "report": str(path),
            }
        )
    return rows


def autopsy_markdown(
    hyp_dir: Path,
    *,
    title: str | None = None,
    mode: str = "exploratory",
) -> str:
    hyp_dir = Path(hyp_dir)
    rows = collect_reports_for_programme(hyp_dir, mode=mode)
    name = title or hyp_dir.name
    n = len([r for r in rows if not r.get("missing_report")])
    n_pass = sum(1 for r in rows if r.get("status") == "passed_val")
    lines = [
        f"# Gate autopsy — {name}",
        "",
        f"**Mode:** {mode}  ",
        f"**Reports found:** {n}/{len(rows)}  ",
        f"**passed_val:** {n_pass}",
        "",
        "| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |",
        "|------------|--------|-----:|-------:|----------:|------:|---------|",
    ]
    for r in rows:
        if r.get("missing_report"):
            lines.append(f"| `{r['id']}` | missing | — | — | — | — | no report json |")
            continue
        sh = r.get("sharpe")
        sh_s = f"{sh:.3f}" if isinstance(sh, (int, float)) else "—"
        ex = r.get("excess_bh")
        ex_s = f"{ex:.3f}" if isinstance(ex, (int, float)) else "—"
        ci = r.get("ci_lo")
        ci_s = f"{ci:.3f}" if isinstance(ci, (int, float)) else "—"
        reasons = "; ".join(r.get("reasons") or [])[:80]
        lines.append(
            f"| `{r.get('id')}` | {r.get('status')} | {r.get('n_trades')} | "
            f"{sh_s} | {ex_s} | {ci_s} | {reasons} |"
        )
    lines.extend(
        [
            "",
            "## Process",
            "",
            "- Frozen gates; no threshold mining on this lock.",
            "- Autopsy is observational — not a promotion decision.",
            "",
        ]
    )
    return "\n".join(lines)


def write_autopsy(
    hyp_dir: Path,
    *,
    out_path: Path | None = None,
    mode: str = "exploratory",
) -> Path:
    hyp_dir = Path(hyp_dir)
    root = project_root()
    if not hyp_dir.is_absolute():
        hyp_dir = root / hyp_dir
    md = autopsy_markdown(hyp_dir, mode=mode)
    out_path = out_path or (hyp_dir / "GATE_AUTOPSY_V1.md")
    out_path.write_text(md)
    return out_path
