"""Reality Checker — economic and execution plausibility.

Statistical significance is necessary but not sufficient. This module asks
whether a human (or tiny-capital bot) could have executed the idea under
realistic market constraints — and whether the edge is economically
believable rather than pure noise / microstructure fiction.

Deterministic: no LLM, no agent override. Failures can hard-reject;
warnings are labeled for the report and journal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from crl.research.backtest.engine import BacktestResult
from crl.shared.types import CostConfig, HypothesisSpec, Metrics


@dataclass
class RealityIssue:
    code: str
    severity: str  # "reject" | "warn"
    question: str
    answer: str
    detail: str = ""


@dataclass
class RealityCheckResult:
    passed: bool
    issues: list[RealityIssue] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def reject_reasons(self) -> list[str]:
        return [f"[{i.code}] {i.answer}" for i in self.issues if i.severity == "reject"]

    @property
    def warnings(self) -> list[str]:
        return [f"[{i.code}] {i.answer}" for i in self.issues if i.severity == "warn"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "answers": self.answers,
            "scores": self.scores,
            "issues": [
                {
                    "code": i.code,
                    "severity": i.severity,
                    "question": i.question,
                    "answer": i.answer,
                    "detail": i.detail,
                }
                for i in self.issues
            ],
            "reject_reasons": self.reject_reasons,
            "warnings": self.warnings,
        }


def _bars_per_day(timeframe: str) -> float:
    tf = timeframe.lower()
    if tf in ("1d", "d", "1day"):
        return 1.0
    if tf in ("4h",):
        return 6.0
    if tf in ("1h",):
        return 24.0
    if tf in ("15m",):
        return 24.0 * 4
    return 1.0


def run_reality_checks(
    spec: HypothesisSpec,
    *,
    metrics: Metrics,
    result: BacktestResult,
    df: pd.DataFrame,
    costs: CostConfig,
    cfg: dict[str, Any] | None = None,
    capital_aud: float = 50.0,
) -> RealityCheckResult:
    """Evaluate economic/execution reality for a backtest slice (usually val).

    Config key: ``reality`` in default.yaml (optional; sensible defaults).
    """
    cfg = cfg or {}
    rcfg = cfg.get("reality", {})
    issues: list[RealityIssue] = []
    answers: dict[str, str] = {}
    scores: dict[str, float] = {}

    min_hold = int(rcfg.get("min_avg_hold_bars", 1))
    min_edge_bps = float(rcfg.get("min_edge_bps_vs_round_trip", 0.0))
    max_turnover_per_year = float(rcfg.get("max_turnover_per_year", 200.0))
    min_notional_usd = float(rcfg.get("min_trade_notional_usd", 5.0))
    require_human_executable = bool(rcfg.get("require_human_executable", True))
    high_freq_bar_hours = float(rcfg.get("high_freq_warn_bar_hours", 4.0))

    bpd = _bars_per_day(spec.timeframe)
    bar_hours = 24.0 / bpd if bpd else 24.0
    rt_cost_bps = costs.total_bps_round_trip(stress=False)
    rt_cost_stress = costs.total_bps_round_trip(stress=True)

    # --- 1. Human executable? ---
    q1 = "Could a human actually have executed this?"
    human_ok = True
    if bar_hours < 1.0:
        human_ok = False
        issues.append(
            RealityIssue(
                code="human_exec",
                severity="reject",
                question=q1,
                answer="No — sub-hourly decisions are not Phase-1 human/low-freq executable.",
                detail=f"bar_hours={bar_hours:.2f}",
            )
        )
    elif require_human_executable and bar_hours < high_freq_bar_hours:
        issues.append(
            RealityIssue(
                code="human_exec",
                severity="warn",
                question=q1,
                answer="Borderline — 4h bars need discipline; daily is safer for tiny capital.",
                detail=f"bar_hours={bar_hours:.2f}",
            )
        )
        answers[q1] = "Borderline (intraday low-freq)"
    else:
        answers[q1] = "Yes — low-frequency closed-bar rules suit a human or simple scheduler."
    scores["human_executable"] = 1.0 if human_ok and bar_hours >= high_freq_bar_hours else (0.6 if human_ok else 0.0)

    # --- 2. Latency matter? ---
    q2 = "Would Binance latency / microstructure matter?"
    # Next-bar fill on 1d/4h → latency negligible vs bar width
    if bar_hours >= 4.0:
        answers[q2] = (
            "Unlikely to dominate — signal on close, position from next bar; "
            "latency ms ≪ bar width."
        )
        scores["latency_ok"] = 1.0
    else:
        issues.append(
            RealityIssue(
                code="latency",
                severity="warn",
                question=q2,
                answer="Possibly — shorter bars make fill timing and API lag more material.",
                detail=f"bar_hours={bar_hours:.2f}",
            )
        )
        answers[q2] = "Possibly material at this timeframe"
        scores["latency_ok"] = 0.5

    # Intrabar stops forbidden in Phase 1 — note if someone later enables them
    if cfg.get("execution", {}).get("allow_intrabar_stops", False):
        issues.append(
            RealityIssue(
                code="intrabar_stops",
                severity="reject",
                question=q2,
                answer="Intrabar stops enabled — fill realism not guaranteed without adverse assumptions.",
            )
        )
        scores["latency_ok"] = 0.0

    # --- 3. Liquidity for tiny capital ---
    q3 = "Would liquidity matter at our size?"
    # BTCUSDT is deep; for 10-50 AUD essentially never
    capital_usd = capital_aud * float(rcfg.get("aud_usd", 0.65))  # rough
    # Typical daily quote volume if present
    liq_ok = True
    if "volume" in df.columns and "close" in df.columns:
        notionals = (df["volume"].astype(float) * df["close"].astype(float)).replace(0, np.nan)
        med_notional = float(notionals.median()) if notionals.notna().any() else float("inf")
        # Our size as fraction of median daily base*price volume
        frac = capital_usd / med_notional if med_notional > 0 else 0.0
        scores["size_vs_volume"] = float(min(1.0, 1.0 - min(frac * 1e6, 1.0)))  # tiny → ~1
        if frac > 0.001:  # >0.1% of median daily vol — absurd for retail BTC spot
            liq_ok = False
            issues.append(
                RealityIssue(
                    code="liquidity",
                    severity="reject",
                    question=q3,
                    answer="Size may impact market — not plausible for claimed fills.",
                    detail=f"capital_usd≈{capital_usd:.0f}, frac_of_median_daily_notional={frac:.2e}",
                )
            )
            answers[q3] = "No — size too large vs volume"
        else:
            answers[q3] = (
                f"Yes for tiny capital (~{capital_aud:.0f} AUD). "
                f"BTCUSDT median bar notional dwarfs size (frac≈{frac:.2e})."
            )
    else:
        answers[q3] = "Assumed OK for BTCUSDT spot tiny size (no volume column)."
        scores["size_vs_volume"] = 0.8

    if capital_usd < min_notional_usd:
        issues.append(
            RealityIssue(
                code="min_notional",
                severity="warn",
                question=q3,
                answer=(
                    f"Capital ≈${capital_usd:.2f} may hit exchange min notional dust issues "
                    f"in live Phase 5 — research uses continuous fractions."
                ),
            )
        )

    # --- 4. Fees / costs during volatility ---
    q4 = "Would fees/slippage change during volatility enough to kill the edge?"
    edge_bps = float(metrics.edge_bps_per_trade)
    scores["edge_vs_cost"] = edge_bps / rt_cost_bps if rt_cost_bps > 0 else 0.0
    if metrics.n_trades > 0 and edge_bps < min_edge_bps:
        # edge below configured floor (default 0 = only informational unless negative vs stress)
        pass
    if metrics.n_trades >= 5 and edge_bps < rt_cost_bps * 0.5 and metrics.avg_trade_return <= 0:
        issues.append(
            RealityIssue(
                code="fee_fragile",
                severity="reject",
                question=q4,
                answer="Average trade edge does not clear a meaningful fraction of round-trip costs.",
                detail=f"edge_bps={edge_bps:.1f}, rt_cost_bps={rt_cost_bps:.1f}",
            )
        )
        answers[q4] = "Yes — edge is fee-fragile / non-economic"
    elif metrics.n_trades >= 5 and edge_bps < rt_cost_stress:
        issues.append(
            RealityIssue(
                code="fee_fragile",
                severity="warn",
                question=q4,
                answer="Edge per trade is thinner than stressed round-trip costs — vol spikes could erase it.",
                detail=f"edge_bps={edge_bps:.1f}, stress_rt_bps={rt_cost_stress:.1f}",
            )
        )
        answers[q4] = "Possibly — thin vs stressed costs"
    else:
        answers[q4] = (
            f"Stress path uses {costs.stress_multiplier}× costs in gates. "
            f"edge_bps/trade≈{edge_bps:.1f}, base RT≈{rt_cost_bps:.1f} bps."
        )

    # Holding period: ultra-short holds amplify fee drag
    avg_hold = float(metrics.avg_hold_bars)
    if metrics.n_trades >= 3 and avg_hold < min_hold:
        issues.append(
            RealityIssue(
                code="hold_period",
                severity="reject",
                question=q4,
                answer=f"Avg hold {avg_hold:.1f} bars < min {min_hold} — churn vs costs unrealistic.",
            )
        )
    scores["avg_hold_bars"] = avg_hold

    # Turnover
    n_bars = max(metrics.n_bars, 1)
    years = n_bars / (bpd * 365.0) if bpd else n_bars / 365.0
    turnover_per_year = float(metrics.turnover) / years if years > 0 else float(metrics.turnover)
    scores["turnover_per_year"] = turnover_per_year
    if turnover_per_year > max_turnover_per_year:
        issues.append(
            RealityIssue(
                code="turnover",
                severity="warn",
                question=q4,
                answer=f"High turnover ≈{turnover_per_year:.0f}/yr — cost model errors dominate.",
                detail=f"max_configured={max_turnover_per_year}",
            )
        )

    # --- 5. Crowding / publication decay ---
    q5 = "Could this edge disappear after publication / crowding?"
    taxonomy = spec.taxonomy.value if hasattr(spec.taxonomy, "value") else str(spec.taxonomy)
    crowded = taxonomy in ("trend", "composite") and "sma_200" in (
        spec.entry.expression + " " + spec.exit.expression
    )
    if crowded:
        issues.append(
            RealityIssue(
                code="publication_decay",
                severity="warn",
                question=q5,
                answer=(
                    "Yes risk — SMA/trend filters are widely known; any edge may be beta timing "
                    "or already crowded, not a private inefficiency."
                ),
            )
        )
        answers[q5] = "High crowding / decay risk (classic technical rule)"
        scores["novelty"] = 0.3
    else:
        answers[q5] = (
            "Unknown — assume positive decay risk for any public crypto signal; "
            "prefer edges with economic story beyond chart folklore."
        )
        scores["novelty"] = 0.5

    # --- 6. Economically plausible vs noise ---
    q6 = "Is this economically plausible, or probably statistical noise?"
    noise_flags = []
    if metrics.n_trades < 30:
        noise_flags.append(f"few trades ({metrics.n_trades})")
    if metrics.beta_proxy > 0.85 and metrics.excess_return_vs_bh <= 0:
        noise_flags.append("high beta to BTC without excess vs buy-and-hold")
    if abs(metrics.sharpe_after_cost) > 3.0 and metrics.n_trades < 50:
        noise_flags.append("extreme Sharpe with small trade count (overfit smell)")
    if metrics.edge_bps_per_trade > 500 and metrics.n_trades < 20:
        noise_flags.append("implausibly large edge bps per trade with few samples")

    if noise_flags:
        # hard reject only for extreme sharpe+few trades; else warn
        extreme = any("extreme Sharpe" in f or "implausibly large" in f for f in noise_flags)
        issues.append(
            RealityIssue(
                code="economic_plausibility",
                severity="reject" if extreme else "warn",
                question=q6,
                answer="Weak economic story / noise risk: " + "; ".join(noise_flags),
            )
        )
        answers[q6] = "Probably noise or beta — see flags"
        scores["plausibility"] = 0.2 if extreme else 0.4
    else:
        answers[q6] = (
            "Plausible enough to keep studying if statistical gates pass: "
            f"edge≈{edge_bps:.0f} bps/trade, beta≈{metrics.beta_proxy:.2f}, "
            f"excess_vs_bh≈{metrics.excess_return_vs_bh:.3f}."
        )
        scores["plausibility"] = 0.7

    # --- 7. Fill model honesty ---
    q7 = "Does the fill model match something we could actually do?"
    fill = (result.meta or {}).get("fill_model", cfg.get("execution", {}).get("fill", "next_bar"))
    answers[q7] = (
        f"Model={fill}: closed-bar signal, next-bar position, bps costs. "
        "No mid-price fantasy; no L2. Acceptable for daily/4h research; "
        "not a guarantee of live fills."
    )
    scores["fill_realism"] = 0.85 if bar_hours >= 4 else 0.5

    # --- 8. Capacity (tiny capital research) ---
    q8 = "Is capacity consistent with the research goal (tiny capital)?"
    answers[q8] = (
        f"Yes for ~{capital_aud:.0f} AUD research mandate. "
        "Do not extrapolate to large AUM without liquidity/impact model."
    )
    scores["capacity_fit"] = 1.0

    rejects = [i for i in issues if i.severity == "reject"]
    return RealityCheckResult(
        passed=len(rejects) == 0,
        issues=issues,
        answers=answers,
        scores=scores,
    )
