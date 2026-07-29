"""Pre-registered experiment: OI-build incremental next-RV skill beyond rv_lag.

Family id: leverage_incremental_rv_skill_v1
Mechanism: leverage_cycle

Scientific question
-------------------
Does the leverage *build* state contain information about next-bar realized
volatility that is not already in lagged RV?

Hypothesis (H1)
---------------
The causal residual of rv_next after expanding regression on rv_lag remains
positively associated with a pre-defined build indicator.

Null (H0)
---------
|IC(build, residual)| < 0.05  OR  residual IC not positive at material level.

Design (locked)
---------------
1. rv_lag, rv_next as in synthesis panel (20-bar log-ret std, lag-1 / lead-1).
2. build_flag = 1 if oi_chg_pct_lag > expanding p75 AND abs_funding_lag
   (else abs_premium) >= expanding p50  (same as leverage_cycle v1).
3. Expanding OLS: rv_next ~ a + b * rv_lag using past only (min 120 bars);
   residual r_t = rv_next_t - (a_t + b_t * rv_lag_t).
4. Primary metric: Pearson IC(build_flag, residual) on finite residual sample.
5. Secondary: IC(build_flag, rv_next); IC(rv_lag, rv_next); mean residual | build=1
   vs build=0.
6. Decision: open risk-channel pre-reg discussion only if residual IC >= 0.05
   and mean residual | build=1 > mean residual | build=0.
   Else **retire** family leverage_incremental_rv_skill_v1 permanently.

Trial cost: 1 primary test (+ 2 secondaries, not free search).
Not a trading programme. Not LEDA promotion.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.research.market_properties.synthesis import build_property_panel
from crl.shared.data.oi import add_oi_features

FAMILY_ID = "leverage_incremental_rv_skill_v1"
STUDY_VERSION = 1
EXPAND_MIN = 120
RESIDUAL_IC_THRESHOLD = 0.05


def _expanding_q(s: pd.Series, q: float, min_periods: int = 60) -> pd.Series:
    vals = s.to_numpy(dtype=float)
    out = np.full(len(vals), np.nan)
    for i in range(len(vals)):
        if i + 1 < min_periods or not np.isfinite(vals[i]):
            continue
        w = vals[: i + 1]
        w = w[np.isfinite(w)]
        if len(w) < min_periods:
            continue
        out[i] = float(np.quantile(w, q))
    return pd.Series(out, index=s.index)


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float | None:
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 50:
        return None
    aa, bb = a[m], b[m]
    if np.std(aa) < 1e-15 or np.std(bb) < 1e-15:
        return None
    v = float(np.corrcoef(aa, bb)[0, 1])
    return None if v != v else round(v, 6)


def study_leverage_incremental_rv_skill(
    ohlcv: pd.DataFrame,
    *,
    oi_events: pd.DataFrame,
    premium_events: Optional[pd.DataFrame] = None,
    funding_events: Optional[pd.DataFrame] = None,
    expand_min: int = EXPAND_MIN,
) -> dict[str, Any]:
    """Run pre-registered incremental skill test. Returns retire/escalate decision."""
    if oi_events is None or len(oi_events) == 0:
        return {
            "ok": False,
            "family_id": FAMILY_ID,
            "reason": "oi_events required",
        }

    feat = add_oi_features(ohlcv, oi_events)
    panel = build_property_panel(
        ohlcv,
        premium_events=premium_events,
        funding_events=funding_events,
    )
    panel["oi_chg_pct_lag"] = feat["oi_chg_pct_1d"].shift(1)

    thr_oi_hi = _expanding_q(panel["oi_chg_pct_lag"], 0.75, 60)
    lev = None
    if "abs_funding_lag" in panel.columns:
        lev = panel["abs_funding_lag"]
    elif "abs_premium_lag" in panel.columns:
        lev = panel["abs_premium_lag"]
    thr_lev = _expanding_q(lev, 0.5, 60) if lev is not None else None

    build = (panel["oi_chg_pct_lag"] > thr_oi_hi) & thr_oi_hi.notna()
    if thr_lev is not None and lev is not None:
        build = build & (lev >= thr_lev) & thr_lev.notna()
    panel["build_flag"] = build.astype(float)

    df = panel.dropna(subset=["rv_lag", "rv_next", "oi_chg_pct_lag"]).copy()
    rv_l = df["rv_lag"].to_numpy(dtype=float)
    rv_n = df["rv_next"].to_numpy(dtype=float)
    bf = df["build_flag"].to_numpy(dtype=float)

    # Expanding residual of rv_next on rv_lag
    resid = np.full(len(df), np.nan)
    for i in range(len(df)):
        if i < expand_min:
            continue
        x = rv_l[:i]
        y = rv_n[:i]
        if np.std(x) < 1e-15:
            continue
        b = float(np.cov(x, y)[0, 1] / np.var(x))
        a = float(np.mean(y) - b * np.mean(x))
        resid[i] = rv_n[i] - (a + b * rv_l[i])

    m = np.isfinite(resid)
    n_res = int(m.sum())
    ic_resid_build = _safe_corr(bf[m], resid[m])
    ic_build_rvnext = _safe_corr(bf, rv_n)
    ic_rvlag_rvnext = _safe_corr(rv_l, rv_n)

    mean_resid_build = (
        round(float(np.mean(resid[m & (bf > 0.5)])), 8)
        if (m & (bf > 0.5)).sum() >= 20
        else None
    )
    mean_resid_not = (
        round(float(np.mean(resid[m & (bf < 0.5)])), 8)
        if (m & (bf < 0.5)).sum() >= 20
        else None
    )

    residual_ic_material = (
        ic_resid_build is not None and ic_resid_build >= RESIDUAL_IC_THRESHOLD
    )
    mean_diff_ok = (
        mean_resid_build is not None
        and mean_resid_not is not None
        and mean_resid_build > mean_resid_not
    )
    escalate = bool(residual_ic_material and mean_diff_ok)
    retire = not escalate

    return {
        "ok": True,
        "family_id": FAMILY_ID,
        "study_version": STUDY_VERSION,
        "mechanism_id": "leverage_cycle",
        "hypothesis": (
            "OI-build flag associates with positive residual next-RV after "
            "causal expanding control for rv_lag"
        ),
        "design": {
            "build_definition": "leverage_cycle v1 (oi_chg p75 + lev proxy p50)",
            "residual": f"expanding OLS rv_next~rv_lag min={expand_min}",
            "primary_metric": "Pearson IC(build_flag, residual)",
            "decision_threshold_residual_ic": RESIDUAL_IC_THRESHOLD,
            "trial_cost": 1,
        },
        "n_bars": len(df),
        "n_residual": n_res,
        "n_build": int((bf > 0.5).sum()),
        "ic_rv_lag_vs_rv_next": ic_rvlag_rvnext,
        "ic_build_vs_rv_next": ic_build_rvnext,
        "ic_build_vs_residual": ic_resid_build,
        "mean_residual_build": mean_resid_build,
        "mean_residual_not_build": mean_resid_not,
        "decision": {
            "residual_ic_material": residual_ic_material,
            "mean_residual_build_gt_not": mean_diff_ok,
            "escalate_to_risk_channel_prereg": escalate,
            "retire_family": retire,
            "family_if_retired": FAMILY_ID if retire else None,
        },
        "leda_candidate": False,
        "preregistered_candidate": escalate,  # only if incremental skill holds
        "promotion": "not_applicable — skill test only; confirmatory path still required if escalate",
        "interpretation": (
            "INCREMENTAL SKILL SUPPORTED — may pre-reg LEDA risk-state channel "
            "with family ledger"
            if escalate
            else (
                "INCREMENTAL SKILL NOT SUPPORTED — build state is largely collinear "
                "with RV level; retire leverage_incremental_rv_skill_v1; keep "
                "descriptive leverage_cycle knowledge only"
            )
        ),
    }
