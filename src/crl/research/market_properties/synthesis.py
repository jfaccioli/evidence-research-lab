"""Property Synthesis Review — causal shelf analysis + pre-registered composites.

Not free combination search. Targets and combination rules are declared here
before evaluation. Failure retires the combination family.

Pre-registered family (locked):
  TARGET: next-bar realized vol (rv_next = rolling-20 log-ret std shifted -1)
  BASELINE: rv_lag alone
  COMPOSITE: equal-weight mean of causal rolling percentile ranks of stress inputs
  STRESS_INPUTS (higher rank = more stress / higher expected next RV):
    1. rv_lag
    2. abs(premium_lag)
    3. abs(funding_lag)
    4. abs(supply_dlog30_lag)
  Optional fifth if available: abs(basis_lag)
  RANK_WINDOW: 60 (causal rolling percentile)
  ABLATIONS: drop-one each input (family cost counted)
  FORBIDDEN: free weight optimization, threshold grids on test
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.leda.util import roll_percentile_rank

# --- Pre-registration (do not edit after first evaluation without version bump) ---
SYNTHESIS_VERSION = 1
TARGET = "rv_next"
BASELINE = "rv_lag"
RANK_WINDOW = 60
STRESS_CORE = ("rv_lag", "abs_premium_lag", "abs_funding_lag", "abs_supply_dlog30_lag")
STRESS_OPTIONAL = ("abs_basis_lag",)
FAMILY_ID = "leda_synth_stress_equal_rank_v1"

ROLE_MAP: dict[str, dict[str, str]] = {
    "rv_lag": {
        "role": "volatility / uncertainty",
        "mechanism": "RV persistence",
        "stress_sign": "high = stress",
    },
    "trade_intensity_lag": {
        "role": "participation",
        "mechanism": "activity / liquidity intensity",
        "stress_sign": "low intensity may stress (not in core composite)",
    },
    "taker_buy_ratio_lag": {
        "role": "participation / aggression",
        "mechanism": "aggressive buyer share",
        "stress_sign": "not used as stress (co-moves with returns)",
    },
    "premium_lag": {
        "role": "leverage stress",
        "mechanism": "perp mark–index premium",
        "stress_sign": "high |premium| = stress",
    },
    "funding_lag": {
        "role": "leverage stress",
        "mechanism": "discrete funding print",
        "stress_sign": "high |funding| = stress",
    },
    "supply_dlog30_lag": {
        "role": "liquidity",
        "mechanism": "stablecoin supply growth",
        "stress_sign": "high |growth| = liquidity regime change / stress proxy",
    },
    "tvl_dlog30_lag": {
        "role": "capital allocation",
        "mechanism": "DeFi TVL growth",
        "stress_sign": "not in core (prior null linear skill)",
    },
    "basis_lag": {
        "role": "market dislocation",
        "mechanism": "cross-venue log price ratio",
        "stress_sign": "high |basis| = fragmentation stress",
    },
}


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float | None:
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 30:
        return None
    aa, bb = a[m], b[m]
    if np.std(aa) < 1e-15 or np.std(bb) < 1e-15:
        return None
    v = float(np.corrcoef(aa, bb)[0, 1])
    return None if v != v else round(v, 6)


def build_property_panel(
    ohlcv: pd.DataFrame,
    *,
    premium_events: Optional[pd.DataFrame] = None,
    funding_events: Optional[pd.DataFrame] = None,
    supply_events: Optional[pd.DataFrame] = None,
    tvl_events: Optional[pd.DataFrame] = None,
    basis_events: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Causal lagged property panel on BTC OHLCV index."""
    close = ohlcv["close"].astype(float)
    log_ret = np.log(close / close.shift(1))
    rv = log_ret.rolling(20, min_periods=20).std()
    panel = pd.DataFrame(index=ohlcv.index)
    panel["ret_lag"] = log_ret.shift(1)
    panel["fwd_ret"] = log_ret.shift(-1)
    panel["rv_lag"] = rv.shift(1)
    panel["rv_next"] = rv.shift(-1)

    if "taker_buy_base" in ohlcv.columns and "n_trades" in ohlcv.columns:
        from crl.research.market_properties.kline_aggression import build_aggression_frame

        ag = build_aggression_frame(ohlcv)
        panel["taker_buy_ratio_lag"] = ag["taker_buy_ratio_lag"]
        panel["trade_intensity_lag"] = ag["trade_intensity_lag"]
        panel["log_intensity_lag"] = np.log(
            ag["trade_intensity_lag"].astype(float).replace(0, np.nan)
        )

    if premium_events is not None and len(premium_events):
        from crl.research.market_properties.perp_premium import align_premium_to_ohlcv

        p = align_premium_to_ohlcv(ohlcv, premium_events)
        panel["premium_lag"] = p["premium_lag"]
        panel["abs_premium_lag"] = p["premium_lag"].abs()

    if funding_events is not None and len(funding_events):
        from crl.research.market_properties.perp_premium import _align_funding_daily

        fl = _align_funding_daily(ohlcv, funding_events).shift(1)
        panel["funding_lag"] = fl
        panel["abs_funding_lag"] = fl.abs()

    if supply_events is not None and len(supply_events):
        from crl.research.market_properties.stablecoin_supply import align_supply_to_ohlcv

        s = align_supply_to_ohlcv(ohlcv, supply_events)
        panel["supply_dlog30_lag"] = s["supply_dlog_30_lag"]
        panel["abs_supply_dlog30_lag"] = s["supply_dlog_30_lag"].abs()

    if tvl_events is not None and len(tvl_events):
        from crl.research.market_properties.defi_tvl import align_tvl_to_ohlcv

        t = align_tvl_to_ohlcv(ohlcv, tvl_events)
        panel["tvl_dlog30_lag"] = t["tvl_dlog_30_lag"]

    if basis_events is not None and len(basis_events):
        from crl.research.market_properties.cross_venue_basis import align_basis_to_ohlcv

        b = align_basis_to_ohlcv(ohlcv, basis_events)
        panel["basis_lag"] = b["basis_lag"]
        panel["abs_basis_lag"] = b["abs_basis_lag"]

    return panel


def correlation_matrix(panel: pd.DataFrame, cols: list[str]) -> dict[str, dict[str, float | None]]:
    out: dict[str, dict[str, float | None]] = {}
    for a in cols:
        out[a] = {}
        if a not in panel.columns:
            continue
        for b in cols:
            if b not in panel.columns:
                out[a][b] = None
            else:
                out[a][b] = _safe_corr(
                    panel[a].to_numpy(dtype=float), panel[b].to_numpy(dtype=float)
                )
    return out


def equal_rank_stress(
    panel: pd.DataFrame,
    inputs: tuple[str, ...] | list[str],
    *,
    rank_window: int = RANK_WINDOW,
) -> pd.Series:
    """Equal-weight mean of causal percentile ranks (NaN-safe mean)."""
    ranks = []
    for c in inputs:
        if c not in panel.columns:
            continue
        ranks.append(roll_percentile_rank(panel[c].astype(float), rank_window))
    if not ranks:
        return pd.Series(np.nan, index=panel.index)
    mat = pd.concat(ranks, axis=1)
    return mat.mean(axis=1, skipna=True)


def evaluate_stress_family(
    panel: pd.DataFrame,
    *,
    include_basis: bool = False,
) -> dict[str, Any]:
    """Evaluate pre-registered equal-rank stress composite vs rv_lag baseline."""
    inputs = list(STRESS_CORE)
    if include_basis and "abs_basis_lag" in panel.columns:
        inputs = inputs + list(STRESS_OPTIONAL)

    present = [c for c in inputs if c in panel.columns]
    missing = [c for c in inputs if c not in panel.columns]

    stress = equal_rank_stress(panel, present, rank_window=RANK_WINDOW)
    work = panel.copy()
    work["stress_equal_rank"] = stress

    need = ["rv_lag", "rv_next", "stress_equal_rank"]
    df = work.dropna(subset=need)
    n = len(df)
    baseline_ic = _safe_corr(
        df["rv_lag"].to_numpy(dtype=float), df["rv_next"].to_numpy(dtype=float)
    )
    composite_ic = _safe_corr(
        df["stress_equal_rank"].to_numpy(dtype=float),
        df["rv_next"].to_numpy(dtype=float),
    )

    # Incremental: partial correlation composite vs rv_next controlling rv_lag (simple residual)
    # residual of stress on rv_lag (expanding would be heavier; use full-sample residual only for descriptive?
    # User asked strictly causal. Use expanding residual of stress ~ rv_lag.
    resid = np.full(len(df), np.nan)
    s = df["stress_equal_rank"].to_numpy(dtype=float)
    r = df["rv_lag"].to_numpy(dtype=float)
    y = df["rv_next"].to_numpy(dtype=float)
    expand_min = 120
    for i in range(len(s)):
        if i < expand_min:
            continue
        x = r[:i]
        yy = s[:i]
        if np.std(x) < 1e-15:
            continue
        b = float(np.cov(x, yy)[0, 1] / np.var(x))
        a = float(np.mean(yy) - b * np.mean(x))
        resid[i] = s[i] - (a + b * r[i])
    m = np.isfinite(resid)
    incr_ic = _safe_corr(resid[m], y[m]) if m.sum() > 50 else None

    ablations = []
    for drop in present:
        sub = [c for c in present if c != drop]
        st = equal_rank_stress(panel, sub, rank_window=RANK_WINDOW)
        tmp = panel[["rv_next"]].copy()
        tmp["st"] = st
        tmp = tmp.dropna()
        ic = _safe_corr(tmp["st"].to_numpy(dtype=float), tmp["rv_next"].to_numpy(dtype=float))
        ablations.append({"drop": drop, "ic_vs_rv_next": ic, "n_inputs": len(sub)})

    # Single-input ICs for context
    singles = {}
    for c in present:
        tmp = panel[[c, "rv_next"]].dropna()
        singles[c] = _safe_corr(
            tmp[c].to_numpy(dtype=float), tmp["rv_next"].to_numpy(dtype=float)
        )

    # Decision rule (pre-declared): composite must beat baseline IC by >= 0.02
    # AND incremental residual IC >= 0.05 to open composite programme discussion
    beats = (
        composite_ic is not None
        and baseline_ic is not None
        and composite_ic >= baseline_ic + 0.02
    )
    incr_ok = incr_ic is not None and abs(incr_ic) >= 0.05
    open_programme = bool(beats and incr_ok)

    return {
        "family_id": FAMILY_ID,
        "synthesis_version": SYNTHESIS_VERSION,
        "target": TARGET,
        "baseline": BASELINE,
        "combination_rule": "equal_weight_mean_of_causal_percentile_ranks",
        "rank_window": RANK_WINDOW,
        "inputs_declared": list(inputs),
        "inputs_present": present,
        "inputs_missing": missing,
        "n_eval": n,
        "baseline_ic_rv_lag_vs_rv_next": baseline_ic,
        "composite_ic_stress_vs_rv_next": composite_ic,
        "incremental_ic_stress_resid_vs_rv_next": incr_ic,
        "single_input_ic_vs_rv_next": singles,
        "ablations_drop_one": ablations,
        "decision_thresholds": {
            "composite_beats_baseline_by": 0.02,
            "min_abs_incremental_ic": 0.05,
        },
        "beats_baseline": beats,
        "incremental_material": incr_ok,
        "open_composite_leda_programme": open_programme,
        "family_trial_cost": 1 + len(ablations),  # composite + drop-one ablations
        "promotion": "not_applicable — synthesis diagnostic only",
        "note": (
            "If open_composite_leda_programme is false, retire free weight/threshold "
            "fishing on this family. Null is success."
        ),
    }


def run_property_synthesis_review(
    ohlcv: pd.DataFrame,
    *,
    premium_events: Optional[pd.DataFrame] = None,
    funding_events: Optional[pd.DataFrame] = None,
    supply_events: Optional[pd.DataFrame] = None,
    tvl_events: Optional[pd.DataFrame] = None,
    basis_events: Optional[pd.DataFrame] = None,
) -> dict[str, Any]:
    """Full synthesis review payload for documentation / CLI."""
    panel = build_property_panel(
        ohlcv,
        premium_events=premium_events,
        funding_events=funding_events,
        supply_events=supply_events,
        tvl_events=tvl_events,
        basis_events=basis_events,
    )

    corr_cols = [
        c
        for c in (
            "rv_lag",
            "log_intensity_lag",
            "taker_buy_ratio_lag",
            "premium_lag",
            "funding_lag",
            "supply_dlog30_lag",
            "tvl_dlog30_lag",
            "basis_lag",
            "fwd_ret",
            "rv_next",
        )
        if c in panel.columns
    ]
    corr = correlation_matrix(panel, corr_cols)

    # Role map filtered to present
    roles = {k: v for k, v in ROLE_MAP.items() if k in panel.columns or k.replace("_lag", "") in str(panel.columns)}
    # Always include static map for documented shelf
    roles = ROLE_MAP

    family = evaluate_stress_family(
        panel, include_basis="abs_basis_lag" in panel.columns
    )

    # High redundancy pairs (|corr| > 0.6 among predictors)
    redundant = []
    preds = [c for c in corr_cols if c not in ("fwd_ret", "rv_next")]
    for i, a in enumerate(preds):
        for b in preds[i + 1 :]:
            v = corr.get(a, {}).get(b)
            if v is not None and abs(v) >= 0.6:
                redundant.append({"a": a, "b": b, "corr": v})

    return {
        "review": "Property Synthesis Review",
        "synthesis_version": SYNTHESIS_VERSION,
        "role_map": roles,
        "panel_columns": list(panel.columns),
        "n_bars": len(panel),
        "correlation_lagged_properties": corr,
        "high_redundancy_pairs_abs_corr_ge_0_6": redundant,
        "stress_family_evaluation": family,
        "scientific_conclusion": (
            "Open composite LEDA programme"
            if family["open_composite_leda_programme"]
            else (
                "Do NOT open composite LEDA programme: equal-rank stress does not "
                "materially beat rv_lag baseline with incremental residual skill. "
                "Retire free combination search for family "
                f"{FAMILY_ID}."
            )
        ),
        "improves_understanding_without_edge": True,
    }
