"""Batch exploratory evaluation of a hypothesis catalog."""

from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import Any

import yaml

from crl.research.hypotheses.catalog import write_catalog
from crl.research.meta.summary import taxonomy_survival_table
from crl.research.pipeline.run import run_hypothesis_pipeline
from crl.shared.config import load_config, project_root
from crl.shared.data.store import latest_manifest
from crl.shared.types import HypothesisSpec, ResearchMode, RuleSpec, Taxonomy


def load_hypothesis_yaml(path: Path) -> HypothesisSpec:
    raw = yaml.safe_load(path.read_text())
    entry = raw["entry"]
    exit_ = raw["exit"]
    return HypothesisSpec(
        id=raw["id"],
        version=int(raw.get("version", 1)),
        asset=raw.get("asset", "BTC/USDT"),
        timeframe=raw.get("timeframe", "1d"),
        taxonomy=Taxonomy(raw.get("taxonomy", "other")),
        family_id=raw.get("family_id", raw["id"]),
        entry=RuleSpec(
            expression=entry["expression"] if isinstance(entry, dict) else entry
        ),
        exit=RuleSpec(
            expression=exit_["expression"] if isinstance(exit_, dict) else exit_
        ),
        rationale=raw.get("rationale", ""),
        expected_outcome=raw.get("expected_outcome", ""),
        feature_tags=raw.get("feature_tags", []),
    )


def run_batch(
    *,
    hyp_dir: Path | None = None,
    dataset_id: str | None = None,
    limit: int | None = None,
    write_hyps: bool = True,
    config_path: str | None = None,
    funding_events: Any | None = None,
    funding_series_id: str | None = None,
    oi_events: Any | None = None,
    oi_series_id: str | None = None,
    flow_events: Any | None = None,
    flow_series_id: str | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    root = project_root()
    hyp_dir = hyp_dir or (root / "examples" / "batch")
    if write_hyps:
        write_catalog(hyp_dir)

    paths = sorted(hyp_dir.glob("hyp_*.yaml"))
    if limit is not None:
        paths = paths[:limit]
    if not paths:
        raise FileNotFoundError(f"No hyp_*.yaml in {hyp_dir}")

    # Infer interval from first hyp when dataset not specified (1d vs 4h programmes).
    if dataset_id is None:
        probe = load_hypothesis_yaml(paths[0])
        interval = probe.timeframe if probe.timeframe in ("1d", "4h") else "1d"
        m = latest_manifest(
            root / cfg["data"]["manifest_dir"],
            symbol=cfg.get("symbol_binance", "BTCUSDT"),
            interval=interval,
            source="binance_public",
        )
        if m is None:
            raise FileNotFoundError(
                f"No BTCUSDT {interval} dataset. Run: crl fetch --interval {interval}"
            )
        dataset_id = m.dataset_id
        print(f"dataset_id={dataset_id} (inferred interval={interval})", flush=True)

    results: list[dict[str, Any]] = []
    for i, path in enumerate(paths, 1):
        spec = load_hypothesis_yaml(path)
        print(f"[{i}/{len(paths)}] {spec.id} ...", flush=True)
        try:
            out = run_hypothesis_pipeline(
                spec,
                cfg,
                dataset_id=dataset_id,
                funding_events=funding_events,
                funding_series_id=funding_series_id,
                oi_events=oi_events,
                oi_series_id=oi_series_id,
                flow_events=flow_events,
                flow_series_id=flow_series_id,
                registry_path=registry_path,
                mode=ResearchMode.EXPLORATORY,
            )
            row = {
                "id": spec.id,
                "taxonomy": spec.taxonomy.value,
                "status": out["final_status"],
                "gate_passed": out["gates"]["passed"],
                "reasons": out["gates"]["reasons"][:5],
                "val_sharpe": out["metrics"]["val"].get("sharpe_after_cost"),
                "val_trades": out["metrics"]["val"].get("n_trades"),
                "val_excess_bh": out["metrics"]["val"].get("excess_return_vs_bh"),
                "reality_passed": out.get("reality", {}).get("passed"),
                "report": out.get("report_md"),
                "error": None,
            }
        except Exception as e:
            row = {
                "id": spec.id,
                "taxonomy": spec.taxonomy.value,
                "status": "error",
                "gate_passed": False,
                "reasons": [str(e)],
                "error": traceback.format_exc(limit=3),
            }
            print(f"  ERROR: {e}", flush=True)
        results.append(row)
        print(
            f"  -> {row.get('status')} gate={row.get('gate_passed')} "
            f"trades={row.get('val_trades')} sharpe={row.get('val_sharpe')}",
            flush=True,
        )

    summary = {
        "dataset_id": dataset_id,
        "n_run": len(results),
        "n_passed_val": sum(1 for r in results if r.get("status") == "passed_val"),
        "n_failed_val": sum(1 for r in results if r.get("status") == "failed_val"),
        "n_errors": sum(1 for r in results if r.get("status") == "error"),
        "taxonomy_survival": taxonomy_survival_table(
            root / cfg["registry"]["path"]
        ),
        "results": results,
    }

    out_path = root / "reports" / "batch_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, default=str))

    md = _summary_md(summary)
    md_path = root / "reports" / "batch_summary.md"
    md_path.write_text(md)
    summary["summary_md"] = str(md_path)
    summary["summary_json"] = str(out_path)

    # Research planner: update knowledge base (does not weaken gates)
    try:
        from crl.research.planner.plan import update_knowledge_after_batch

        kb = update_knowledge_after_batch(
            registry_path=root / cfg["registry"]["path"],
            root=root,
            batch_summary={
                "n_run": summary["n_run"],
                "n_passed_val": summary["n_passed_val"],
                "n_failed_val": summary["n_failed_val"],
                "n_errors": summary["n_errors"],
            },
            spend_units=float(len(results)),
            mode="exploratory",
            hyp_ids=[r["id"] for r in results if r.get("id")],
        )
        summary["knowledge_base"] = {
            "updated_at": kb.get("updated_at"),
            "budget_remaining": (kb.get("budget") or {}).get("units_remaining"),
        }
    except Exception as e:
        summary["knowledge_base_error"] = str(e)

    return summary


def _summary_md(summary: dict[str, Any]) -> str:
    lines = [
        "# Batch exploratory summary",
        "",
        f"- dataset_id: `{summary.get('dataset_id')}`",
        f"- n_run: {summary.get('n_run')}",
        f"- passed_val: {summary.get('n_passed_val')}",
        f"- failed_val: {summary.get('n_failed_val')}",
        f"- errors: {summary.get('n_errors')}",
        "",
        "## Taxonomy survival (registry-wide)",
        "",
        "| taxonomy | n | survived | rate |",
        "|----------|--:|---------:|-----:|",
    ]
    for r in summary.get("taxonomy_survival") or []:
        lines.append(
            f"| {r['taxonomy']} | {r['n_ideas']} | {r['n_survived']} | "
            f"{100 * r['survival_rate']:.1f}% |"
        )
    lines += ["", "## Per hypothesis", ""]
    lines.append("| id | tax | status | val_sharpe | trades | reality |")
    lines.append("|----|-----|--------|----------:|-------:|---------|")
    for r in summary.get("results") or []:
        lines.append(
            f"| {r.get('id')} | {r.get('taxonomy')} | {r.get('status')} | "
            f"{r.get('val_sharpe') if r.get('val_sharpe') is not None else ''} | "
            f"{r.get('val_trades') if r.get('val_trades') is not None else ''} | "
            f"{r.get('reality_passed')} |"
        )
    lines += [
        "",
        "## Philosophy",
        "",
        "Rejecting almost everything is success if the process is sound.",
        "Complexity is earned. Finding zero edges is still Phase 1 success.",
        "",
    ]
    return "\n".join(lines)
