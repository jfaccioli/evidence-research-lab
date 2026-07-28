"""One-shot programme runner: doctor + series attach + temp registry + conf."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from crl.ops.doctor import run_doctor
from crl.ops.programme_index import load_programme_index
from crl.ops.research_queue_state import record_programme_result
from crl.ops.series_attach import (
    SeriesAttachError,
    maybe_window_dataset,
    resolve_attach,
    series_readiness,
)
from crl.research.pipeline.batch import run_batch
from crl.shared.config import project_root
from crl.shared.data.store import latest_manifest


def run_programme(
    hyp_dir: Path,
    *,
    dataset_id: str | None = None,
    config_path: str | None = None,
    limit: int | None = None,
    require_doctor: bool = True,
    update_exploratory_note: bool = True,
    confirmatory_on_pass: bool = True,
    require_series_ready: bool = False,
    record_queue: bool = True,
) -> dict[str, Any]:
    """Run a locked programme dir under a temp registry. Does not write catalog.

    Reads ``INDEX.yaml`` when present:
    - attaches flow/external series for explor + confirmatory
    - optional windowed OHLCV when ``window_from_series: true``

    If ``confirmatory_on_pass``, any exploratory ``passed_val`` is immediately
    run confirmatory on the same temp registry (same series kwargs).
    """
    from crl.research.pipeline.batch import load_hypothesis_yaml
    from crl.research.pipeline.run import run_hypothesis_pipeline
    from crl.shared.config import load_config
    from crl.shared.types import ResearchMode

    root = project_root()
    hyp_dir = Path(hyp_dir)
    if not hyp_dir.is_absolute():
        hyp_dir = root / hyp_dir
    if not hyp_dir.exists():
        raise FileNotFoundError(hyp_dir)

    idx = load_programme_index(hyp_dir)
    readiness = series_readiness(idx.external)
    if require_series_ready and not readiness.get("ready"):
        raise SeriesAttachError(readiness.get("message") or "series not ready")

    if require_doctor:
        doc = run_doctor(config_path)
        if not doc.ok:
            failed = [c.name for c in doc.checks if not c.ok]
            raise RuntimeError(f"crl doctor failed: {failed}")

    cfg = load_config(config_path)
    attach_kwargs: dict[str, Any] = {}
    series_meta: dict[str, Any] = {"readiness": readiness}
    if idx.external is not None:
        resolved = resolve_attach(idx.external)
        series_meta["content_hash"] = resolved.get("series_content_hash")
        series_meta["kind"] = resolved.get("attach_kind")
        series_meta["series_id"] = idx.external.series_id
        attach_kwargs = {
            k: v
            for k, v in resolved.items()
            if k
            in (
                "flow_events",
                "flow_series_id",
                "external_events",
                "external_series_id",
                "external_prefix",
            )
        }

    # Dataset resolution
    if dataset_id is None:
        m = latest_manifest(
            root / cfg["data"]["manifest_dir"],
            symbol=idx.dataset_symbol.replace("/", ""),
            interval=idx.dataset_interval if idx.dataset_interval in ("1d", "4h") else "1d",
            source="binance_public",
        )
        if m is None:
            raise FileNotFoundError(
                f"No dataset for {idx.dataset_symbol} {idx.dataset_interval}. "
                f"Run: crl fetch --interval {idx.dataset_interval} --symbol {idx.dataset_symbol.replace('/','')}"
            )
        dataset_id = m.dataset_id

    if idx.window_from_series and idx.external is not None:
        if idx.external.kind == "flow":
            ev = attach_kwargs["flow_events"]
            tcol = "flow_time"
        else:
            ev = attach_kwargs["external_events"]
            tcol = "event_time"
        dataset_id = maybe_window_dataset(
            idx, ev, tcol, base_dataset_id=str(dataset_id), config_path=config_path
        )
        series_meta["windowed_dataset_id"] = dataset_id

    reg = root / "data" / "processed" / f"tmp_batch_{hyp_dir.name}.sqlite"
    reg.parent.mkdir(parents=True, exist_ok=True)
    if reg.exists():
        reg.unlink()

    summary = run_batch(
        hyp_dir=hyp_dir,
        dataset_id=dataset_id,
        limit=limit,
        write_hyps=False,
        config_path=config_path,
        registry_path=reg,
        **attach_kwargs,
    )
    conf_results: list[dict[str, Any]] = []
    ds = summary.get("dataset_id") or dataset_id
    n_candidates = 0
    if confirmatory_on_pass and ds:
        for r in summary.get("results") or []:
            if r.get("status") != "passed_val":
                continue
            hid = r.get("id")
            yml = hyp_dir / f"{hid}.yaml"
            if not yml.exists():
                conf_results.append({"id": hid, "status": "error", "error": "yaml missing"})
                continue
            try:
                spec = load_hypothesis_yaml(yml)
                out_c = run_hypothesis_pipeline(
                    spec,
                    cfg,
                    dataset_id=str(ds),
                    registry_path=reg,
                    mode=ResearchMode.CONFIRMATORY,
                    **attach_kwargs,
                )
                st = out_c.get("final_status")
                if st == "candidate":
                    n_candidates += 1
                conf_results.append(
                    {
                        "id": hid,
                        "status": st,
                        "reasons": (out_c.get("gates") or {}).get("reasons", [])[:6],
                        "test_sharpe": (out_c.get("metrics") or {})
                        .get("test", {})
                        .get("sharpe_after_cost"),
                    }
                )
            except Exception as e:
                conf_results.append({"id": hid, "status": "error", "error": str(e)})

    out = {
        "programme": idx.name,
        "hyp_dir": str(hyp_dir),
        "registry_path": str(reg),
        "n_run": summary.get("n_run"),
        "n_passed_val": summary.get("n_passed_val"),
        "n_failed_val": summary.get("n_failed_val"),
        "n_errors": summary.get("n_errors"),
        "n_candidates": n_candidates,
        "dataset_id": summary.get("dataset_id") or dataset_id,
        "summary_md": summary.get("summary_md"),
        "results": summary.get("results"),
        "confirmatory": conf_results,
        "series": series_meta,
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }

    if update_exploratory_note:
        note = hyp_dir / "EXPLORATORY_NOTE.md"
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conf_line = ""
        if conf_results:
            conf_line = "\n**Confirmatory:** " + ", ".join(
                f"{c.get('id')}={c.get('status')}" for c in conf_results
            ) + "\n"
        series_line = ""
        if idx.external:
            series_line = (
                f"\n**Series:** `{idx.external.kind}:{idx.external.series_id}` "
                f"ready={readiness.get('ready')} hash=`{(series_meta.get('content_hash') or '')[:16]}…`\n"
            )
        body = (
            f"# {hyp_dir.name} exploratory\n\n"
            f"**Date:** {stamp}\n\n"
            f"**Result:** {out['n_passed_val']}/{out['n_run']} passed_val; "
            f"failed_val={out['n_failed_val']}; errors={out['n_errors']}; "
            f"candidates={n_candidates}.\n"
            f"{conf_line}{series_line}\n"
            f"Temp registry: `{reg.name}`. Dataset: `{out.get('dataset_id')}`.\n\n"
            "Not promotion evidence. Frozen gates. No threshold mining on this lock.\n"
        )
        note.write_text(body)

    json_path = root / "data" / "processed" / f"tmp_batch_{hyp_dir.name}_summary.json"
    json_path.write_text(json.dumps(out, indent=2, default=str))
    out["summary_json"] = str(json_path)

    try:
        from crl.ops.autopsy import write_autopsy

        out["autopsy_path"] = str(write_autopsy(hyp_dir))
    except Exception as e:
        out["autopsy_error"] = str(e)

    if record_queue:
        try:
            record_programme_result(
                idx.name,
                n_passed_val=int(out.get("n_passed_val") or 0),
                n_run=int(out.get("n_run") or 0),
                n_candidates=int(n_candidates),
                notes=f"dataset={out.get('dataset_id')}",
            )
        except Exception as e:
            out["queue_record_error"] = str(e)

    # Workstream F P3 — family trial ledger (informational multiplicity)
    try:
        from collections import Counter

        from crl.research.meta.family_trials import record_programme_trials
        from crl.research.pipeline.batch import load_hypothesis_yaml

        fam_counts: Counter[str] = Counter()
        for r in summary.get("results") or []:
            hid = r.get("id")
            if not hid:
                continue
            yml = hyp_dir / f"{hid}.yaml"
            if yml.exists():
                sp = load_hypothesis_yaml(yml)
                fam_counts[sp.family_id or sp.id] += 1
            else:
                fam_counts[str(hid)] += 1
        if fam_counts:
            out["family_trials"] = record_programme_trials(
                programme=idx.name,
                family_counts=dict(fam_counts),
                n_passed_val=int(out.get("n_passed_val") or 0),
                n_candidates=int(n_candidates),
                dataset_id=str(out.get("dataset_id") or ""),
            )
    except Exception as e:
        out["family_trials_error"] = str(e)

    return out
