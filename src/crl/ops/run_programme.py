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
) -> dict[str, Any]:
    """Run a locked programme dir under a temp registry. Does not write catalog."""
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
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }

    if update_exploratory_note:
        note = hyp_dir / "EXPLORATORY_NOTE.md"
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        body = (
            f"# {hyp_dir.name} exploratory\n\n"
            f"**Date:** {stamp}\n\n"
            f"**Result:** {out['n_passed_val']}/{out['n_run']} passed_val; "
            f"failed_val={out['n_failed_val']}; errors={out['n_errors']}.\n\n"
            f"Temp registry: `{reg.name}`. Dataset: `{out.get('dataset_id')}`.\n\n"
            "Not promotion evidence. Frozen gates. No threshold mining on this lock.\n"
        )
        note.write_text(body)

    json_path = root / "data" / "processed" / f"tmp_batch_{hyp_dir.name}_summary.json"
    json_path.write_text(json.dumps(out, indent=2, default=str))
    out["summary_json"] = str(json_path)
    return out
