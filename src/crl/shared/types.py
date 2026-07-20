"""Shared types and hypothesis schemas for the research lab."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ResearchMode(str, Enum):
    EXPLORATORY = "exploratory"
    CONFIRMATORY = "confirmatory"


class HypothesisStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PASSED_TRAIN = "passed_train"
    FAILED_VAL = "failed_val"
    PASSED_VAL = "passed_val"
    FAILED_TEST = "failed_test"
    CANDIDATE = "candidate"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class Taxonomy(str, Enum):
    TREND = "trend"
    VOL_FILTER = "vol_filter"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    CALENDAR = "calendar"
    VOLUME = "volume"
    COMPOSITE = "composite"
    # Proxies only in Phase 1 (no live social / limited alt-data)
    SENTIMENT_PROXY = "sentiment_proxy"
    ONCHAIN_PROXY = "onchain_proxy"
    FUNDING_PROXY = "funding_proxy"
    OTHER = "other"


class RuleSpec(BaseModel):
    """Simple rule expressions over feature column names.

    Supported forms (evaluated on closed bars):
      - "close > sma_200"
      - "vol_z_20 < 0"
      - combined with 'and' / 'or' (lowercase)
    """

    expression: str


class HypothesisSpec(BaseModel):
    id: str
    version: int = 1
    asset: str = "BTC/USDT"
    timeframe: str = "1d"
    direction: str = "long_only"
    taxonomy: Taxonomy = Taxonomy.TREND
    family_id: str = ""
    entry: RuleSpec
    exit: RuleSpec
    position_sizing: str = "full_or_flat"
    rationale: str = ""
    expected_outcome: str = ""
    literature_refs: list[dict[str, str]] = Field(default_factory=list)
    feature_tags: list[str] = Field(default_factory=list)
    falsification: dict[str, Any] = Field(default_factory=dict)
    primary_metric: str = "sharpe_after_cost"
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def frozen_hash_payload(self) -> str:
        """Canonical JSON for confirmatory immutability checks."""
        return self.model_dump_json(exclude={"created_at"})


class CostConfig(BaseModel):
    fee_bps_per_side: float = 10.0
    half_spread_bps: float = 1.5
    slippage_bps_per_side: float = 5.0
    stress_multiplier: float = 2.0

    def total_bps_one_way(self, stress: bool = False) -> float:
        bps = (
            self.fee_bps_per_side
            + self.half_spread_bps
            + self.slippage_bps_per_side
        )
        if stress:
            bps *= self.stress_multiplier
        return bps

    def total_bps_round_trip(self, stress: bool = False) -> float:
        return 2.0 * self.total_bps_one_way(stress=stress)


class SplitConfig(BaseModel):
    train_frac: float = 0.50
    val_frac: float = 0.25
    test_frac: float = 0.25
    wf_train_bars: int = 730
    wf_val_bars: int = 180
    wf_step_bars: int = 90


class GateConfig(BaseModel):
    primary_metric: str = "sharpe_after_cost"
    min_trades: int = 30
    sharpe_min: float = 0.20
    max_drawdown: float = 0.55
    overfit_gap_max: float = 1.0
    wf_min_positive_fold_frac: float = 0.60
    bootstrap_ci_lower_sharpe_min: float = -0.10
    skeptical_p_mean_trade_gt0_min: float = 0.55
    mc_max_dd_breach_frac: float = 0.50
    fragility_min_pass_frac: float = 0.40
    regime_concentration_warn: float = 0.80
    research_budget_confirmatory_per_month: int = 10


class DataManifest(BaseModel):
    dataset_id: str
    source: str
    symbol: str
    interval: str
    start: str
    end: str
    row_count: int
    sha256: str
    trust_score: float
    fetched_at: str
    path: str


class Trade(BaseModel):
    entry_time: Any
    exit_time: Any
    entry_price: float
    exit_price: float
    return_net: float
    bars_held: int
    regime_at_entry: Optional[str] = None
    is_open: bool = False  # True if no exit cost applied (terminal open or B&H hold)


class Metrics(BaseModel):
    n_bars: int = 0
    n_trades: int = 0
    total_return: float = 0.0
    cagr: float = 0.0
    volatility: float = 0.0
    sharpe_after_cost: float = 0.0
    sortino: float = 0.0
    calmar: float = 0.0
    max_drawdown: float = 0.0
    time_underwater_frac: float = 0.0
    turnover: float = 0.0
    avg_trade_return: float = 0.0
    avg_hold_bars: float = 0.0
    edge_bps_per_trade: float = 0.0
    excess_return_vs_bh: float = 0.0
    ir_vs_bh: float = 0.0
    beta_proxy: float = 0.0


class ReproStamp(BaseModel):
    git_sha: str = "unknown"
    git_dirty: bool = False
    config_hash: str = ""
    dataset_id: str = ""
    data_sha256: str = ""
    code_version: str = "0.1.0"
    python_version: str = ""
    seed: int = 42
    run_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    hypothesis_id: str = ""
    hypothesis_version: int = 1
    mode: str = ResearchMode.EXPLORATORY.value
