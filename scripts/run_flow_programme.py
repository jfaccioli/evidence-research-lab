#!/usr/bin/env python3
"""Run locked flow programme with real CMD netflow (temp registry).

Not mock. Attribution: Ercin Dedeoglu crypto-market-data (CC BY 4.0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from crl.ops.autopsy import write_autopsy
    from crl.research.pipeline.batch import run_batch
    from crl.shared.config import project_root
    from crl.shared.data.sources.flow_cmd_github import (
        SERIES_ID,
        ingest_cmd_btc_netflow,
    )
    from crl.shared.data.sources.flow_ingest import resolve_flow_series
    from crl.shared.data.store import latest_manifest

    root = project_root()
    print("Ingesting CMD BTC exchange netflow...", flush=True)
    meta = ingest_cmd_btc_netflow()
    print(json.dumps(meta, indent=2), flush=True)

    events, h = resolve_flow_series(SERIES_ID)
    assert h == meta["content_hash"]

    m = latest_manifest(
        root / "data" / "manifests",
        symbol="BTCUSDT",
        interval="1d",
        source="binance_public",
    )
    if m is None:
        print("No BTC 1d dataset — run: crl fetch --interval 1d", file=sys.stderr)
        return 1

    reg = root / "data" / "processed" / "tmp_flow_cmd_v1.sqlite"
    if reg.exists():
        reg.unlink()

    hyp_dir = root / "examples" / "batch" / "flow"
    print(f"Running flow programme on {m.dataset_id} registry={reg}", flush=True)
    summary = run_batch(
        hyp_dir=hyp_dir,
        dataset_id=m.dataset_id,
        write_hyps=False,
        flow_events=events,
        flow_series_id=SERIES_ID,
        registry_path=reg,
    )
    print(json.dumps({k: summary.get(k) for k in (
        "n_run", "n_passed_val", "n_errors", "n_failed"
    ) if k in summary or True}, indent=2, default=str), flush=True)
    # richer
    print("RESULTS:", flush=True)
    for r in summary.get("results") or []:
        print(
            f"  {r.get('id')}: {r.get('status')} trades={r.get('val_trades')} "
            f"sh={r.get('val_sharpe')} {r.get('reasons')}",
            flush=True,
        )

    note = hyp_dir / "EXPLORATORY_NOTE.md"
    n_pass = sum(1 for r in (summary.get("results") or []) if r.get("status") == "passed_val")
    n_run = len(summary.get("results") or [])
    note.write_text(
        f"""# flow exploratory — CMD BTC exchange netflow v1

**Status:** exploratory batch complete on **real** free series (not mock).

| Field | Value |
|-------|-------|
| series_id | `{SERIES_ID}` |
| content_hash | `{meta['content_hash'][:16]}…` |
| n_events | {meta['n_events']} |
| publish_lag_days | {meta['publish_lag_days']} |
| dataset | `{m.dataset_id}` |
| registry | temp `{reg.name}` |
| result | **{n_pass}/{n_run}** passed_val |

## Attribution

{meta['attribution']}

## PIT caveat

Fixed publish lag (not vendor revision journal). See `src/crl/shared/data/sources/flow_cmd_github.py`.

## Outcome

See GATE_AUTOPSY_V1.md and per-hyp reports. Mock never used.
"""
    )
    try:
        ap = write_autopsy(hyp_dir)
        print(f"autopsy={ap}", flush=True)
    except Exception as e:
        print(f"autopsy_skip: {e}", flush=True)

    out_path = root / "data" / "processed" / "flow" / "batch_summary_cmd_v1.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"summary={out_path}", flush=True)
    return 0 if int(summary.get("n_errors") or 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
