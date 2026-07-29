"""Mechanism study: what processes co-occur with volatility clustering?

Mechanism id: vol_clustering
Hypothesis (locked for this study version):
  High-vol states persist partly because leverage stress and liquidity
  withdrawal co-occur with high RV and prolong uncertainty — not only because
  of pure statistical inertia of RV.

Design (pre-registered, causal, NOT a trading programme):
  - High-RV state at t: rv_lag >= expanding median of past rv_lag (causal).
  - Persistence: P(rv_next high | rv_lag high) vs P(rv_next high).
  - Co-factor stress (each evaluated separately, no free combination search):
      leverage: abs(funding_lag) or abs(premium_lag) >= own expanding p75
      liquidity: supply_dlog30_lag <= expanding p25 (contraction / low growth)
      participation: log_intensity_lag <= expanding p25 (quiet activity)
  - Report persistence of high-RV conditional on each co-factor.
  - No LEDA mapping. No position rules.

Success: uncertainty reduction about *why* RV clusters.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.research.market_properties.synthesis import build_property_panel

MECHANISM_ID = "vol_clustering"
STUDY_VERSION = 1


def _expanding_quantile(s: pd.Series, q: float, min_periods: int = 60) -> pd.Series:
    """Causal expanding quantile (past including t)."""
    vals = s.to_numpy(dtype=float)
    out = np.full(len(vals), np.nan)
    for i in range(len(vals)):
        if i + 1 < min_periods or not np.isfinite(vals[i]):
            continue
        window = vals[: i + 1]
        window = window[np.isfinite(window)]
        if len(window) < min_periods:
            continue
        out[i] = float(np.quantile(window, q))
    return pd.Series(out, index=s.index)


def _rate(mask: np.ndarray, event: np.ndarray) -> float | None:
    m = mask & np.isfinite(event.astype(float))
    if m.sum() < 30:
        return None
    return round(float(np.mean(event[m])), 6)


def study_vol_clustering(
    ohlcv: pd.DataFrame,
    *,
    premium_events: Optional[pd.DataFrame] = None,
    funding_events: Optional[pd.DataFrame] = None,
    supply_events: Optional[pd.DataFrame] = None,
    min_periods: int = 60,
) -> dict[str, Any]:
    """Run pre-registered vol-clustering co-factor study (science only)."""
    panel = build_property_panel(
        ohlcv,
        premium_events=premium_events,
        funding_events=funding_events,
        supply_events=supply_events,
    )
    if "rv_lag" not in panel.columns or "rv_next" not in panel.columns:
        return {"ok": False, "mechanism_id": MECHANISM_ID, "reason": "need rv_lag/rv_next"}

    rv_lag = panel["rv_lag"].astype(float)
    rv_next = panel["rv_next"].astype(float)
    # High-RV thresholds (causal expanding medians)
    thr_lag = _expanding_quantile(rv_lag, 0.5, min_periods=min_periods)
    thr_next = thr_lag  # same scale family; next high vs same expanding median level
    # Use expanding median of rv_lag as high threshold for both lag and next
    high_lag = (rv_lag >= thr_lag) & thr_lag.notna() & rv_lag.notna()
    high_next = (rv_next >= thr_lag) & thr_lag.notna() & rv_next.notna()

    base = panel.dropna(subset=["rv_lag", "rv_next"]).copy()
    hl = high_lag.reindex(base.index).fillna(False).to_numpy()
    hn = high_next.reindex(base.index).fillna(False).to_numpy()

    p_high_uncond = round(float(np.mean(hn)), 6) if len(hn) else None
    p_persist = _rate(hl, hn.astype(float))
    # Lift
    lift = (
        round(p_persist / p_high_uncond, 4)
        if p_persist is not None and p_high_uncond and p_high_uncond > 0
        else None
    )

    def cofactor_persistence(
        name: str, stress_mask: pd.Series
    ) -> dict[str, Any]:
        sm = stress_mask.reindex(base.index).fillna(False).to_numpy()
        both = hl & sm
        only_rv = hl & ~sm
        return {
            "cofactor": name,
            "n_high_rv_and_stress": int(both.sum()),
            "n_high_rv_without_stress": int(only_rv.sum()),
            "p_high_next_given_high_rv_and_stress": _rate(both, hn.astype(float)),
            "p_high_next_given_high_rv_without_stress": _rate(only_rv, hn.astype(float)),
        }

    cofactors = []
    # Leverage: abs funding high
    if "abs_funding_lag" in panel.columns:
        q75 = _expanding_quantile(panel["abs_funding_lag"], 0.75, min_periods=min_periods)
        stress = panel["abs_funding_lag"] >= q75
        cofactors.append(cofactor_persistence("abs_funding_ge_expanding_p75", stress))
    if "abs_premium_lag" in panel.columns:
        q75 = _expanding_quantile(panel["abs_premium_lag"], 0.75, min_periods=min_periods)
        stress = panel["abs_premium_lag"] >= q75
        cofactors.append(cofactor_persistence("abs_premium_ge_expanding_p75", stress))
    # Liquidity: low supply growth
    if "supply_dlog30_lag" in panel.columns:
        q25 = _expanding_quantile(panel["supply_dlog30_lag"], 0.25, min_periods=min_periods)
        stress = panel["supply_dlog30_lag"] <= q25
        cofactors.append(cofactor_persistence("supply_dlog30_le_expanding_p25", stress))
    # Participation: low intensity
    if "log_intensity_lag" in panel.columns:
        q25 = _expanding_quantile(panel["log_intensity_lag"], 0.25, min_periods=min_periods)
        stress = panel["log_intensity_lag"] <= q25
        cofactors.append(cofactor_persistence("log_intensity_le_expanding_p25", stress))

    # Interpretation (descriptive, not promotion)
    supported = []
    weak = []
    for c in cofactors:
        a = c["p_high_next_given_high_rv_and_stress"]
        b = c["p_high_next_given_high_rv_without_stress"]
        if a is None or b is None:
            weak.append(c["cofactor"])
            continue
        if a >= b + 0.03:
            supported.append(c["cofactor"])
        else:
            weak.append(c["cofactor"])

    return {
        "ok": True,
        "mechanism_id": MECHANISM_ID,
        "study_version": STUDY_VERSION,
        "hypothesis": (
            "High-vol states persist partly because leverage stress and liquidity "
            "withdrawal co-occur with high RV and prolong uncertainty"
        ),
        "design": {
            "high_rv_definition": "rv_lag >= causal expanding median of rv_lag",
            "persistence": "P(rv_next high | rv_lag high)",
            "cofactors": "separate tests; no free multi-cofactor search",
            "min_periods_expanding": min_periods,
        },
        "n_bars": len(base),
        "p_high_rv_next_unconditional": p_high_uncond,
        "p_high_rv_next_given_high_rv_lag": p_persist,
        "persistence_lift_vs_unconditional": lift,
        "cofactor_results": cofactors,
        "interpretation": {
            "cofactors_increasing_persistence": supported,
            "cofactors_not_increasing_persistence": weak,
            "note": (
                "Descriptive mechanism evidence only. Does not open LEDA channels. "
                "If no cofactor lifts persistence, pure statistical RV inertia remains "
                "the working description of clustering under this operationalisation."
            ),
        },
        "leda_candidate": False,
        "promotion": "not_applicable — mechanism study only",
        "next_science": (
            "If leverage cofactors lift persistence, deepen leverage_cycle study; "
            "if not, do not invent multi-factor stress scores — mechanism claim weak."
        ),
    }
