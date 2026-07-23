"""Backtest determinism + isolated pipeline E2E (tmp_path project root only).

Replacement for the live-repo test that previously wrote into Desktop
``project_root()`` / live registry. When applied to the repository, this file
supersedes ``tests/test_engine_reproducibility.py``.

Isolation rules:
- Monkeypatch ``crl.research.pipeline.run.project_root`` **before** any data,
  registry, report, journal or reproducibility operation.
- Never use the Desktop project root for paths.
- Skipped when the full research pipeline package is not on PYTHONPATH.
"""

from __future__ import annotations

from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("yaml")
pytest.importorskip("crl.research.pipeline.run")
pytest.importorskip("crl.shared.data.sources.mock")

import yaml  # noqa: E402

from crl.research.backtest.engine import run_backtest  # noqa: E402
from crl.research.pipeline import run as run_mod  # noqa: E402
from crl.research.pipeline.run import prepare_frame, run_hypothesis_pipeline  # noqa: E402
from crl.shared.data.sources.mock import MockOHLCVSource  # noqa: E402
from crl.shared.data.store import save_dataset  # noqa: E402
from crl.shared.types import (  # noqa: E402
    CostConfig,
    HypothesisSpec,
    ResearchMode,
    RuleSpec,
    Taxonomy,
)


def test_backtest_deterministic():
    """Pure in-memory backtest — no project root / registry I/O."""
    df = MockOHLCVSource(n=500, seed=9).fetch_ohlcv("BTCUSDT", "1d")
    feat = prepare_frame(df).dropna(subset=["sma_200"])
    spec = HypothesisSpec(
        id="det",
        entry=RuleSpec(expression="close > sma_200"),
        exit=RuleSpec(expression="close < sma_200"),
    )
    c = CostConfig()
    a = run_backtest(feat, spec, c)
    b = run_backtest(feat, spec, c)
    assert np.allclose(a.equity.values, b.equity.values)


def test_pipeline_mock_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Full pipeline under an isolated tmp project root — never live Desktop paths."""
    root = tmp_path / "proj"
    for sub in (
        "configs",
        "data/processed",
        "data/manifests",
        "registry",
        "reports",
        "journal",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)

    # BEFORE any data/registry/report/journal/repro work: pin project_root.
    monkeypatch.setattr(run_mod, "project_root", lambda: root)
    try:
        from crl.shared import config as cfg_mod

        monkeypatch.setattr(cfg_mod, "project_root", lambda: root)
    except Exception:
        pass

    # Minimal config under tmp_path only (not loaded from live root).
    # config_path / project_root are not kwargs to run_hypothesis_pipeline;
    # isolation is via project_root monkeypatch + relative paths in cfg.
    cfg = {
        "registry": {"path": "registry/crl.sqlite"},
        "reporting": {"dir": "reports"},
        "journal": {"path": "journal/RESEARCH_JOURNAL.md"},
        "data": {
            "cache_dir": "data/processed",
            "manifest_dir": "data/manifests",
            "min_trust_score": 0.0,
        },
        "splits": {
            "train_frac": 0.5,
            "val_frac": 0.25,
            "test_frac": 0.25,
            "wf_train_bars": 100,
            "wf_val_bars": 30,
            "wf_step_bars": 20,
        },
        "gates": {
            "primary_metric": "sharpe_after_cost",
            "min_trades": 1,
            "sharpe_min": 0.0,
            "max_drawdown": 0.99,
            "overfit_gap_max": 99.0,
            "wf_min_positive_fold_frac": 0.0,
            "bootstrap_ci_lower_sharpe_min": -99.0,
            "skeptical_p_mean_trade_gt0_min": 0.0,
            "mc_max_dd_breach_frac": 1.0,
            "fragility_min_pass_frac": 0.0,
            "regime_concentration_warn": 1.0,
            "research_budget_confirmatory_per_month": 100,
        },
        "stats": {
            "bootstrap_n": 20,
            "bootstrap_block_size": 3,
            "mc_n": 20,
            "seed": 0,
            "annualization_1d": 365,
        },
        "risk": {
            "max_position": 1.0,
            "min_position": 0.0,
            "max_leverage": 1.0,
            "allow_short": False,
            "allow_derivatives": False,
        },
        "reality": {"capital_aud": 50.0},
        "costs": {},
    }
    cfg_path = root / "configs" / "default.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))

    # Relative paths in cfg resolve under isolated root
    monkeypatch.chdir(root)

    df = MockOHLCVSource(n=1200, seed=11).fetch_ohlcv("BTCUSDT", "1d")
    manifest = save_dataset(
        df,
        source="mock",
        symbol="BTCUSDT",
        interval="1d",
        processed_dir=root / "data" / "processed",
        manifest_dir=root / "data" / "manifests",
        source_class="mock",
    )
    spec = HypothesisSpec(
        id="hyp_e2e_mock",
        version=1,
        taxonomy=Taxonomy.COMPOSITE,
        entry=RuleSpec(expression="close > sma_200 and rvol_below_median > 0.5"),
        exit=RuleSpec(expression="close < sma_200"),
        rationale="E2E pipeline test of trend plus vol filter under synthetic data.",
        expected_outcome="Likely reject; validates plumbing not alpha.",
    )

    # Real signature: (spec, cfg, *, dataset_id=None, mode=..., df=None, manifest=None)
    # Do not catch TypeError — real pipeline defects must surface.
    result = run_hypothesis_pipeline(
        spec,
        cfg,
        dataset_id=manifest.dataset_id,
        mode=ResearchMode.EXPLORATORY,
    )

    # Artifacts only under tmp_path
    assert any((root / "registry").glob("*.sqlite")) or (
        root / "registry" / "crl.sqlite"
    ).exists()
    root_resolved = root.resolve()
    for p in root.rglob("*"):
        if p.is_file():
            assert root_resolved in p.resolve().parents or p.resolve() == root_resolved
            assert tmp_path.resolve() in p.resolve().parents or p.resolve().is_relative_to(
                tmp_path.resolve()
            )
    assert result is not None
