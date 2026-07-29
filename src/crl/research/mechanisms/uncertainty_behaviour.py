"""Mechanism study: participant behaviour under uncertainty.

Mechanism id: uncertainty_behaviour
Question: How do market participants change behaviour during uncertainty?

Hypothesis (locked for study v1):
  When lagged RV is high, the next-bar (or same decision-time lag-1) regime shows
  lower trade intensity, changed taker aggression, and wider absolute cross-venue
  basis than when RV is low — i.e. behaviour shifts under uncertainty.

Design (pre-registered, causal):
  - High uncertainty: rv_lag >= expanding p75
  - Low uncertainty: rv_lag <= expanding p25
  - Compare contemporaneous lagged properties (already lag-1 in panel):
      log_intensity_lag, taker_buy_ratio_lag, abs_basis_lag
  - Report mean differences (high − low). No trading rules.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.research.market_properties.synthesis import build_property_panel

MECHANISM_ID = "uncertainty_behaviour"
STUDY_VERSION = 1


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


def _mean_on(mask: np.ndarray, x: np.ndarray) -> float | None:
    m = mask & np.isfinite(x)
    if m.sum() < 30:
        return None
    return round(float(np.mean(x[m])), 8)


def study_uncertainty_behaviour(
    ohlcv: pd.DataFrame,
    *,
    basis_events: Optional[pd.DataFrame] = None,
    premium_events: Optional[pd.DataFrame] = None,
    funding_events: Optional[pd.DataFrame] = None,
    min_periods: int = 60,
) -> dict[str, Any]:
    panel = build_property_panel(
        ohlcv,
        basis_events=basis_events,
        premium_events=premium_events,
        funding_events=funding_events,
    )
    if "rv_lag" not in panel.columns:
        return {"ok": False, "mechanism_id": MECHANISM_ID, "reason": "need rv_lag"}

    thr_hi = _expanding_q(panel["rv_lag"], 0.75, min_periods)
    thr_lo = _expanding_q(panel["rv_lag"], 0.25, min_periods)
    high = (panel["rv_lag"] >= thr_hi) & thr_hi.notna()
    low = (panel["rv_lag"] <= thr_lo) & thr_lo.notna()

    behaviours = []
    for col, claim in (
        ("log_intensity_lag", "intensity_lower_in_high_rv"),
        ("taker_buy_ratio_lag", "tbr_differs_in_high_rv"),
        ("abs_basis_lag", "abs_basis_wider_in_high_rv"),
        ("abs_premium_lag", "abs_premium_higher_in_high_rv"),
        ("abs_funding_lag", "abs_funding_higher_in_high_rv"),
    ):
        if col not in panel.columns:
            behaviours.append({"property": col, "available": False})
            continue
        x = panel[col].to_numpy(dtype=float)
        mh = high.to_numpy()
        ml = low.to_numpy()
        mean_h = _mean_on(mh, x)
        mean_l = _mean_on(ml, x)
        diff = (
            round(mean_h - mean_l, 8)
            if mean_h is not None and mean_l is not None
            else None
        )
        # Directional support flags (descriptive)
        supported = None
        if diff is not None:
            if col == "log_intensity_lag":
                supported = diff < -0.05  # log scale: meaningfully lower
            elif col == "abs_basis_lag":
                supported = diff > 0  # wider dislocation
            elif col in ("abs_premium_lag", "abs_funding_lag"):
                supported = diff > 0
            elif col == "taker_buy_ratio_lag":
                supported = abs(diff) > 0.005  # any shift
        behaviours.append(
            {
                "property": col,
                "available": True,
                "mean_high_rv": mean_h,
                "mean_low_rv": mean_l,
                "diff_high_minus_low": diff,
                "claim": claim,
                "claim_supported": supported,
                "n_high": int((mh & np.isfinite(x)).sum()),
                "n_low": int((ml & np.isfinite(x)).sum()),
            }
        )

    supported_claims = [
        b["claim"] for b in behaviours if b.get("claim_supported") is True
    ]
    rejected_claims = [
        b["claim"] for b in behaviours if b.get("claim_supported") is False
    ]

    return {
        "ok": True,
        "mechanism_id": MECHANISM_ID,
        "study_version": STUDY_VERSION,
        "hypothesis": (
            "Under high lagged RV, intensity falls, aggression shifts, and "
            "absolute cross-venue basis widens relative to low-RV regimes"
        ),
        "design": {
            "high_rv": "rv_lag >= expanding p75",
            "low_rv": "rv_lag <= expanding p25",
            "compare": "mean of lag-1 behaviour properties",
        },
        "n_bars": int(panel["rv_lag"].notna().sum()),
        "behaviours": behaviours,
        "interpretation": {
            "supported_claims": supported_claims,
            "rejected_claims": rejected_claims,
            "note": (
                "Descriptive conditioning only. Not a forecast model. "
                "Supported claims may later motivate risk-state channels after pre-reg."
            ),
        },
        "leda_candidate": False,
        "promotion": "not_applicable — mechanism study only",
        "preregistered_candidate": False,
    }
