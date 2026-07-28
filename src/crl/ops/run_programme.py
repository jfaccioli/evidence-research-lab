"""One-shot programme runner: doctor gate + temp registry batch + summary note."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from crl.ops.doctor import run_doctor
from crl.research.pipeline.batch import run_batch
from crl.shared.config import project_root


def run_programme(
    hyp_dir: Path,
    *,
    dataset_id: str | None = None,
    config_path: str | None = None,
    limit: int | None = None,
    require_doctor: bool = True,
    update_exploratory_note: bool = True,
    confirmatory_on_pass: bool = True,
) -> dict[str, Any]:
    """Run a locked programme dir under a temp registry. Does not write catalog.

    If ``confirmatory_on_pass``, any exploratory ``passed_val`` is immediately
    run confirmatory on the same temp registry (budget-aware path).
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

    if require_doctor:
        doc = run_doctor(config_path)
        if not doc.ok:
            failed = [c.name for c in doc.checks if not c.ok]
            raise RuntimeError(f"crl doctor failed: {failed}")

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
    )
    conf_results: list[dict[str, Any]] = []
    ds = summary.get("dataset_id") or dataset_id
    if confirmatory_on_pass and ds:
        cfg = load_config(config_path)
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
                )
                conf_results.append(
                    {
                        "id": hid,
                        "status": out_c.get("final_status"),
                        "reasons": (out_c.get("gates") or {}).get("reasons", [])[:6],
                    }
                )
            except Exception as e:
                conf_results.append({"id": hid, "status": "error", "error": str(e)})

    out = {
        "programme": hyp_dir.name,
        "hyp_dir": str(hyp_dir),
        "registry_path": str(reg),
        "n_run": summary.get("n_run"),
        "n_passed_val": summary.get("n_passed_val"),
        "n_failed_val": summary.get("n_failed_val"),
        "n_errors": summary.get("n_errors"),
        "dataset_id": summary.get("dataset_id"),
        "summary_md": summary.get("summary_md"),
        "results": summary.get("results"),
        "confirmatory": conf_results,
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
        body = (
            f"# {hyp_dir.name} exploratory\n\n"
            f"**Date:** {stamp}\n\n"
            f"**Result:** {out['n_passed_val']}/{out['n_run']} passed_val; "
            f"failed_val={out['n_failed_val']}; errors={out['n_errors']}.\n"
            f"{conf_line}\n"
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

    return out
