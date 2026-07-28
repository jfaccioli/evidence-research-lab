"""Scaffold a locked programme directory (capability for fast new evidence)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from crl.shared.config import project_root

TEMPLATE_HYP = """id: {hyp_id}
version: 1
asset: {asset}
timeframe: {timeframe}
taxonomy: other
family_id: family_{slug}
direction: long_only
entry:
  expression: {entry}
exit:
  expression: {exit}
rationale: >
  Pre-registered. Programme: {design}. Do not expand lock without new version.
expected_outcome: Exploratory; confirmatory only if earned under frozen gates.
feature_tags: {tags}
literature_refs: []
"""


def scaffold_programme(
    slug: str,
    *,
    design_rel: str,
    mechanism: str,
    external_kind: str | None = None,
    series_id: str | None = None,
    prefix: str = "xser",
    asset: str = "BTC/USDT",
    timeframe: str = "1d",
    placeholder_hyps: int = 3,
) -> dict[str, Any]:
    """Create examples/batch/<slug>/ + design stub if missing. Does not run science."""
    root = project_root()
    hyp_dir = root / "examples" / "batch" / slug
    if hyp_dir.exists() and any(hyp_dir.glob("hyp_*.yaml")):
        raise FileExistsError(f"programme already materialised: {hyp_dir}")
    hyp_dir.mkdir(parents=True, exist_ok=True)

    design_path = root / design_rel
    if not design_path.exists():
        design_path.parent.mkdir(parents=True, exist_ok=True)
        design_path.write_text(
            f"""# Programme: {slug}

**Status:** Scaffolded — lock hyps before seeing results.  
**Mechanism:** {mechanism}

## Scientific question

> TODO: falsifiable claim under frozen gates.

## Data / series

{f"- external kind `{external_kind}` series_id `{series_id}` prefix `{prefix}`" if series_id else "- OHLCV only or attach series in INDEX.yaml"}

## Hyps

See `examples/batch/{slug}/`. ≤8; do not expand without version bump.
"""
        )

    index: dict[str, Any] = {
        "programme": f"{slug}_v1",
        "design": design_rel,
        "live_data": bool(series_id),
        "hypotheses": [],
        "dataset": {"symbol": "BTCUSDT", "interval": timeframe},
    }
    if external_kind and series_id:
        index["external"] = {
            "kind": external_kind,
            "series_id": series_id,
            "prefix": prefix,
            "publish_lag_days": 1,
        }

    tags = f"[{slug}, external_pit]" if series_id else f"[{slug}]"
    # Placeholder rules use always-false-ish safe tokens so scaffold cannot
    # accidentally look like a tuned winner before human/agent edits.
    for i in range(1, max(1, placeholder_hyps) + 1):
        hid = f"hyp_{slug}_{i:02d}"
        fname = f"{hid}.yaml"
        # Require edit before science: expression uses missing feature until edited
        body = TEMPLATE_HYP.format(
            hyp_id=hid,
            asset=asset,
            timeframe=timeframe,
            slug=slug,
            design=design_rel,
            entry="close > sma_200",  # baseline placeholder — must re-lock for alt-data
            exit="close < sma_200",
            tags=tags,
        )
        (hyp_dir / fname).write_text(body)
        index["hypotheses"].append(fname)

    (hyp_dir / "INDEX.yaml").write_text(yaml.safe_dump(index, sort_keys=False))
    (hyp_dir / "EXPLORATORY_NOTE.md").write_text(
        f"# {slug} exploratory\n\n**Status:** scaffold only — edit hyps + attach real series before batch.\n"
    )
    return {
        "hyp_dir": str(hyp_dir.relative_to(root)),
        "design": design_rel,
        "n_hyps": len(index["hypotheses"]),
        "index": index,
    }
