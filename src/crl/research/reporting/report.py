"""Markdown + JSON research reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_report(
    payload: dict[str, Any],
    out_dir: Path,
    stem: str,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str))
    md_path.write_text(render_markdown(payload))
    return md_path, json_path


def render_markdown(p: dict[str, Any]) -> str:
    hyp = p.get("hypothesis", {})
    gates = p.get("gates", {})
    repro = p.get("repro", {})
    lines = [
        f"# Research Report: {hyp.get('id', '?')} v{hyp.get('version', 1)}",
        "",
        f"**Mode:** {p.get('mode', '?')}  ",
        f"**Status decision:** {'PASS' if gates.get('passed') else 'REJECT'}  ",
        f"**Primary metric:** after-cost Sharpe  ",
        "",
        "## Hypothesis",
        "",
        f"- **Asset / TF:** {hyp.get('asset')} / {hyp.get('timeframe')}",
        f"- **Taxonomy:** {hyp.get('taxonomy')}",
        f"- **Entry:** `{hyp.get('entry')}`",
        f"- **Exit:** `{hyp.get('exit')}`",
        f"- **Rationale:** {hyp.get('rationale', '')}",
        f"- **Expected:** {hyp.get('expected_outcome', '')}",
        "",
        "## Reproducibility",
        "",
        f"- dataset_id: `{repro.get('dataset_id')}`",
        f"- data_sha256: `{repro.get('data_sha256')}`",
        f"- config_hash: `{repro.get('config_hash')}`",
        f"- git_sha: `{repro.get('git_sha')}` dirty={repro.get('git_dirty')}",
        f"- seed: {repro.get('seed')}",
        f"- trust_score: {p.get('trust_score')}",
        "",
        "## Metrics by split",
        "",
    ]
    for split, m in (p.get("metrics") or {}).items():
        lines.append(f"### {split}")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        for k in (
            "sharpe_after_cost",
            "total_return",
            "cagr",
            "max_drawdown",
            "n_trades",
            "avg_trade_return",
            "excess_return_vs_bh",
            "ir_vs_bh",
            "beta_proxy",
        ):
            if k in m:
                val = m[k]
                if isinstance(val, float):
                    lines.append(f"| {k} | {val:.4f} |")
                else:
                    lines.append(f"| {k} | {val} |")
        lines.append("")

    lines += ["## Baselines", ""]
    for name, m in (p.get("baselines") or {}).items():
        lines.append(
            f"- **{name}:** Sharpe={m.get('sharpe_after_cost', 0):.3f}, "
            f"ret={m.get('total_return', 0):.3f}, DD={m.get('max_drawdown', 0):.3f}"
        )
    lines.append("")

    lines += ["## Walk-forward", ""]
    wf = p.get("walk_forward", {})
    lines.append(f"- positive fold frac: {wf.get('positive_frac')}")
    for fold in wf.get("folds", []):
        lines.append(
            f"  - fold {fold.get('fold_id')}: sharpe={fold.get('sharpe'):.3f}, trades={fold.get('n_trades')}"
        )
    lines.append("")

    lines += ["## Regimes", ""]
    reg = p.get("regimes", {})
    lines.append(f"- max positive share: {reg.get('max_pos_share')}")
    for k, v in (reg.get("pos_shares") or {}).items():
        lines.append(f"  - {k}: {v:.3f}")
    lines.append("")

    lines += ["## Uncertainty & sequence risk", ""]
    st = p.get("stats", {})
    lines.append(f"- bootstrap primary Sharpe CI: {st.get('sharpe_ci')}")
    lines.append(f"- mean bar return CI: {st.get('mean_bar_ci')}")
    lines.append(f"- skeptical P(mean bar > 0): {st.get('skeptical_p')}")
    lines.append(f"- n_effective_hint: {st.get('n_effective_hint')}")
    mt = st.get("multiple_testing") or {}
    if mt:
        lines.append(
            f"- multiple-testing: family={mt.get('n_family')} global={mt.get('n_global')} "
            f"proxy={mt.get('approx_null_selection_proxy')} "
            f"(NOT BLP DSR; ambiguous={mt.get('trials_ambiguous')})"
        )
        lines.append(f"  - {mt.get('note')}")
    mc = st.get("monte_carlo") or {}
    if mc:
        lines.append(f"- MC max DD p95: {mc.get('max_dd_p95')}")
        lines.append(f"- MC frac DD breach: {mc.get('frac_dd_breach')}")
        lines.append(f"- MC frac underperform B&H: {mc.get('frac_underperform_bh')}")
    sens = st.get("sensitivity") or {}
    if sens:
        lines.append(f"- fragility pass_frac: {sens.get('pass_frac')}")
    lines.append("")

    lines += ["## Reality Checker (economic / execution)", ""]
    reality = p.get("reality") or {}
    lines.append(
        f"**Passed:** {reality.get('passed')} — statistics without tradeability is not an edge."
    )
    lines.append("")
    for q, a in (reality.get("answers") or {}).items():
        lines.append(f"- **{q}**")
        lines.append(f"  - {a}")
    if reality.get("issues"):
        lines.append("")
        lines.append("Issues:")
        for iss in reality["issues"]:
            lines.append(
                f"- `{iss.get('severity')}` **{iss.get('code')}**: {iss.get('answer')}"
            )
    lines.append("")

    lines += ["## Gate decision", ""]
    if gates.get("passed"):
        lines.append("**PASSED** constraints for this mode.")
    else:
        lines.append("**REJECTED.** Reasons:")
        for r in gates.get("reasons") or []:
            lines.append(f"- {r}")
    for w in gates.get("warnings") or []:
        lines.append(f"- WARNING: {w}")
    lines.append("")

    lines += ["## Failure-mode checklist", ""]
    for item in p.get("failure_modes") or []:
        lines.append(f"- {item}")
    lines.append("")

    lines += [
        "## Philosophy",
        "",
        "Finding zero edges is still Phase 1 success. This report optimizes for truth, not demo theater.",
        "",
    ]
    return "\n".join(lines)
