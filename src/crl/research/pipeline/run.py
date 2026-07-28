"""End-to-end research pipeline for one hypothesis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from crl.research.backtest.engine import (
    always_cash,
    buy_and_hold,
    run_backtest,
    sma_crossover_baseline,
)
from crl.research.backtest.splitter import chronological_split, walk_forward_folds
from crl.research.hypotheses.registry import HypothesisRegistry
from crl.research.journal.journal import append_entry
from crl.research.reality.checker import run_reality_checks
from crl.research.regimes.labels import add_regime_labels, regime_concentration
from crl.research.reporting.report import write_report
from crl.research.stats.metrics import compute_metrics, trade_returns
from crl.research.stats.monte_carlo import trade_sequence_mc
from crl.research.stats.multiple_testing import evaluate_multiple_testing
from crl.research.stats.sensitivity import sma_neighborhood_sensitivity
from crl.research.stats.significance import bootstrap_bar_sharpe
from crl.research.hypotheses.guardrails import assert_hypothesis_admissible
from crl.risk.constraints import assert_phase1_universe
from crl.risk.promotion import evaluate_gates
from crl.shared.config import (
    cost_from_config,
    gates_from_config,
    project_root,
    splits_from_config,
)
from crl.shared.data.feature_store import load_or_build_features
from crl.shared.data.features import add_features
from crl.shared.data.store import load_dataset
from crl.shared.reproducibility import make_repro_stamp
from crl.shared.types import (
    HypothesisSpec,
    HypothesisStatus,
    Metrics,
    ResearchMode,
)


def prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Uncached path (tests / ad-hoc). Batch uses feature_store."""
    feat = add_features(df)
    return add_regime_labels(feat)


def _ann_factor(timeframe: str, stats_cfg: dict) -> float:
    if timeframe in ("1d", "1D", "d"):
        v = stats_cfg.get("annualization_1d", 365)
    elif timeframe in ("4h", "4H"):
        v = stats_cfg.get("annualization_4h", 2190)
    else:
        v = 365
    if isinstance(v, str) and "*" in v:
        # allow "365 * 6" style configs safely
        parts = [p.strip() for p in v.split("*")]
        out = 1.0
        for p in parts:
            out *= float(p)
        return out
    return float(v)


def run_hypothesis_pipeline(
    spec: HypothesisSpec,
    cfg: dict[str, Any],
    *,
    dataset_id: str | None = None,
    mode: ResearchMode = ResearchMode.EXPLORATORY,
    df: pd.DataFrame | None = None,
    manifest: Any | None = None,
    funding_events: pd.DataFrame | None = None,
    funding_series_id: str | None = None,
    oi_events: pd.DataFrame | None = None,
    oi_series_id: str | None = None,
    flow_events: pd.DataFrame | None = None,
    flow_series_id: str | None = None,
    external_events: pd.DataFrame | None = None,
    external_series_id: str | None = None,
    external_prefix: str = "xser",
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run full research path. Exploratory never promotes off test metrics.

    Optional ``funding_events`` / ``oi_events`` / ``flow_events`` / ``external_events``
    join PIT features. Optional ``registry_path`` overrides live registry for isolated runs.
    """
    root = project_root()
    assert_phase1_universe(spec.model_dump(), cfg=cfg)
    assert_hypothesis_admissible(spec)

    costs = cost_from_config(cfg)
    gates = gates_from_config(cfg)
    splits = splits_from_config(cfg)
    stats_cfg = cfg.get("stats", {})
    seed = int(stats_cfg.get("seed", 42))

    reg_path = Path(registry_path) if registry_path is not None else (
        root / cfg.get("registry", {}).get("path", "registry/crl.sqlite")
    )
    registry = HypothesisRegistry(reg_path)
    try:
        registry.upsert_hypothesis(spec, status=HypothesisStatus.DRAFT)
    except RuntimeError as e:
        # Frozen hyp: still allow re-run without rewriting ledger
        if "frozen" not in str(e).lower():
            raise

    if mode == ResearchMode.CONFIRMATORY:
        registry.assert_confirmatory_allowed(
            spec.id,
            spec.version,
            spec,
            monthly_budget=int(gates.research_budget_confirmatory_per_month),
        )

    # Data
    if df is None:
        mdir = root / cfg.get("data", {}).get("manifest_dir", "data/manifests")
        if dataset_id is None:
            raise ValueError("dataset_id or df required")
        df, manifest = load_dataset(dataset_id, manifest_dir=mdir, verify_hash=True)
    trust = float(getattr(manifest, "trust_score", 0.97) if manifest else 0.97)
    dataset_id = getattr(manifest, "dataset_id", dataset_id or "inline")
    data_sha = getattr(manifest, "sha256", "")

    if manifest is not None:
        registry.register_data_asset(manifest.model_dump() if hasattr(manifest, "model_dump") else dict(manifest))

    cache_dir = root / cfg.get("data", {}).get("cache_dir", "data/processed") / "features"
    frame = load_or_build_features(
        df,
        dataset_id=str(dataset_id),
        cache_dir=cache_dir,
        funding_events=funding_events,
        funding_series_id=funding_series_id,
        oi_events=oi_events,
        oi_series_id=oi_series_id,
        flow_events=flow_events,
        flow_series_id=flow_series_id,
        external_events=external_events,
        external_series_id=external_series_id,
        external_prefix=external_prefix,
    )
    # Drop burn-in where core features unknown
    need = [
        c
        for c in (
            "sma_200",
            "rvol_20",
            "ret_60",
            "ret_90",
            "price_z_20",
            "donch_high_55",
        )
        if c in frame.columns
    ]
    frame = frame.dropna(subset=need).copy()
    ann = _ann_factor(spec.timeframe, stats_cfg)

    holdout = chronological_split(frame, splits)
    # WF only on train+val
    tv = pd.concat([holdout.train, holdout.val])
    folds = walk_forward_folds(tv, splits)

    # Status: only transition to running if not already terminal
    existing = registry.get_hypothesis(spec.id, spec.version)
    if existing is None or existing["status"] in ("draft", "running"):
        try:
            registry.transition(spec.id, spec.version, HypothesisStatus.RUNNING, "pipeline start")
        except Exception:
            pass
    repro = make_repro_stamp(
        cfg,
        dataset_id=str(dataset_id),
        data_sha256=data_sha,
        hypothesis_id=spec.id,
        hypothesis_version=spec.version,
        mode=mode.value,
        seed=seed,
        cwd=root,
    )
    run_id = registry.start_run(
        spec.id,
        spec.version,
        mode,
        dataset_id=str(dataset_id),
        data_sha256=data_sha,
        git_sha=repro.git_sha,
        config_hash=repro.config_hash,
    )

    def eval_split(sub: pd.DataFrame, name: str) -> tuple[dict, Any]:
        res = run_backtest(sub, spec, costs)
        bh = buy_and_hold(sub, costs)
        m = compute_metrics(res, timeframe=spec.timeframe, bh_result=bh, ann=stats_cfg)
        registry.add_metrics(run_id, name, m.model_dump())
        return m.model_dump(), res

    train_m, train_res = eval_split(holdout.train, "train")
    val_m, val_res = eval_split(holdout.val, "val")

    # Baselines on val
    bh_val = buy_and_hold(holdout.val, costs)
    cash_val = always_cash(holdout.val)
    try:
        sma_val = sma_crossover_baseline(holdout.val, costs)
        sma_m = compute_metrics(sma_val, timeframe=spec.timeframe, bh_result=bh_val, ann=stats_cfg)
    except Exception:
        sma_m = None
    baselines = {
        "buy_and_hold": compute_metrics(bh_val, timeframe=spec.timeframe, ann=stats_cfg).model_dump(),
        "cash": compute_metrics(cash_val, timeframe=spec.timeframe, ann=stats_cfg).model_dump(),
    }
    if sma_m:
        baselines["sma_50_200"] = sma_m.model_dump()

    # Walk-forward
    fold_rows = []
    pos = 0
    for fold in folds:
        fres = run_backtest(fold.val, spec, costs)
        fm = compute_metrics(fres, timeframe=spec.timeframe, ann=stats_cfg)
        fold_rows.append(
            {
                "fold_id": fold.fold_id,
                "sharpe": fm.sharpe_after_cost,
                "n_trades": fm.n_trades,
                "total_return": fm.total_return,
            }
        )
        if fm.total_return >= 0:
            pos += 1
    wf_pos_frac = pos / len(fold_rows) if fold_rows else 0.0

    # Stats on validation: primary metric bootstrap (bar Sharpe) + trade MC
    tr = trade_returns(val_res.trades)
    boot = bootstrap_bar_sharpe(
        val_res.bar_returns.values,
        ann_factor=ann,
        n_boot=int(stats_cfg.get("bootstrap_n", 500)),
        block=int(stats_cfg.get("bootstrap_block_size", 5)),
        seed=seed,
    )
    bh_w0 = float(getattr(bh_val, "initial_equity", 1.0) or 1.0)
    bh_term = (
        float(bh_val.equity.iloc[-1] / bh_w0) if len(bh_val.equity) else 1.0
    )
    mc = trade_sequence_mc(
        tr,
        n_sims=int(stats_cfg.get("mc_n", 500)),
        seed=seed,
        dd_limit=gates.max_drawdown,
        bh_terminal=bh_term,
    )
    sens = sma_neighborhood_sensitivity(
        holdout.val, spec, costs, gates, timeframe=spec.timeframe
    )
    family_id = spec.family_id or spec.id
    n_family = max(registry.count_family(family_id), 1)
    n_global = max(registry.count_all_hypotheses(), 1)
    # Legacy programme: trial history not proven complete → fail closed (no fake N)
    mt = evaluate_multiple_testing(
        sharpe_point=float(val_m["sharpe_after_cost"]),
        n_obs=int(val_m["n_bars"]),
        n_family=n_family,
        n_global=n_global,
        ann_factor=ann,
        n_analytical_trials=None,
        trial_history_complete=False,
        bar_returns=val_res.bar_returns.values,
    )

    # Stress costs on val (pre-test requirement)
    stress_res = run_backtest(holdout.val, spec, costs, stress=True)
    stress_m = compute_metrics(stress_res, timeframe=spec.timeframe, ann=stats_cfg)
    stress_sharpe_for_gate = stress_m.sharpe_after_cost

    # Regime concentration from val trades
    reg = regime_concentration(
        [t.regime_at_entry or "unknown" for t in val_res.trades],
        [t.return_net for t in val_res.trades],
    )

    # Reality Checker — economic/execution plausibility (val slice)
    reality = run_reality_checks(
        spec,
        metrics=Metrics(**val_m),
        result=val_res,
        df=holdout.val,
        costs=costs,
        cfg=cfg,
        capital_aud=float(cfg.get("reality", {}).get("capital_aud", 50.0)),
    )

    gate_val = evaluate_gates(
        Metrics(**val_m),
        gates,
        train_sharpe=train_m["sharpe_after_cost"],
        wf_positive_frac=wf_pos_frac,
        bootstrap_sharpe_lo=boot.sharpe_ci[0],
        skeptical_p=boot.p_mean_gt_0_skeptical,
        mc_dd_breach_frac=mc.frac_dd_breach,
        fragility_pass_frac=sens.pass_frac if sens.pass_frac is not None else None,
        stress_sharpe=stress_sharpe_for_gate,
        trust_score=trust,
        min_trust=float(cfg.get("data", {}).get("min_trust_score", 0.7)),
        regime_max_share=reg.get("max_pos_share"),
        confirmatory=False,
        reality_reject_reasons=reality.reject_reasons,
        reality_warnings=reality.warnings,
        multiple_testing_ok=mt.passes_bonferroni_hint,
        multiple_testing_note=mt.note,
        fragility_inconclusive=sens.pass_frac is None,
    )

    test_m = None
    gate_final = gate_val
    if mode == ResearchMode.CONFIRMATORY:
        # Only touch test if val gates pass
        if gate_val.passed:
            test_m, test_res = eval_split(holdout.test, "test")
            registry.mark_saw_test(spec.id, spec.version)
            tr_t = trade_returns(test_res.trades)
            boot_t = bootstrap_bar_sharpe(
                test_res.bar_returns.values,
                ann_factor=ann,
                n_boot=int(stats_cfg.get("bootstrap_n", 500)),
                block=int(stats_cfg.get("bootstrap_block_size", 5)),
                seed=seed,
            )
            mc_t = trade_sequence_mc(
                tr_t,
                n_sims=int(stats_cfg.get("mc_n", 500)),
                seed=seed,
                dd_limit=gates.max_drawdown,
            )
            mt_t = evaluate_multiple_testing(
                sharpe_point=float(test_m["sharpe_after_cost"]),
                n_obs=int(test_m["n_bars"]),
                n_family=n_family,
                n_global=n_global,
                ann_factor=ann,
                n_analytical_trials=None,
                trial_history_complete=False,  # legacy: fail closed
                bar_returns=test_res.bar_returns.values,
            )
            reality_test = run_reality_checks(
                spec,
                metrics=Metrics(**test_m),
                result=test_res,
                df=holdout.test,
                costs=costs,
                cfg=cfg,
                capital_aud=float(cfg.get("reality", {}).get("capital_aud", 50.0)),
            )
            # B3: separate 2×-cost stress on the confirmatory test slice
            stress_test_res = run_backtest(holdout.test, spec, costs, stress=True)
            stress_test_m = compute_metrics(
                stress_test_res, timeframe=spec.timeframe, ann=stats_cfg
            )
            gate_final = evaluate_gates(
                Metrics(**test_m),
                gates,
                train_sharpe=train_m["sharpe_after_cost"],
                wf_positive_frac=wf_pos_frac,
                bootstrap_sharpe_lo=boot_t.sharpe_ci[0],
                skeptical_p=boot_t.p_mean_gt_0_skeptical,
                mc_dd_breach_frac=mc_t.frac_dd_breach,
                fragility_pass_frac=sens.pass_frac if sens.pass_frac is not None else None,
                stress_sharpe=stress_test_m.sharpe_after_cost,
                trust_score=trust,
                min_trust=float(cfg.get("data", {}).get("min_trust_score", 0.7)),
                regime_max_share=reg.get("max_pos_share"),
                confirmatory=True,
                reality_reject_reasons=reality_test.reject_reasons,
                reality_warnings=reality_test.warnings,
                multiple_testing_ok=mt_t.passes_bonferroni_hint,
                multiple_testing_note=mt_t.note,
                fragility_inconclusive=sens.pass_frac is None,
            )
            reality = reality_test
            boot = boot_t
            mc = mc_t
            mt = mt_t
            stress_sharpe_for_gate = stress_test_m.sharpe_after_cost
        else:
            gate_final = gate_val

    # Status transitions
    if mode == ResearchMode.EXPLORATORY:
        if gate_val.passed:
            registry.transition(
                spec.id, spec.version, HypothesisStatus.PASSED_VAL, "; ".join(gate_val.reasons) or "val ok"
            )
            final_status = HypothesisStatus.PASSED_VAL
        else:
            registry.transition(
                spec.id, spec.version, HypothesisStatus.FAILED_VAL, "; ".join(gate_val.reasons)
            )
            final_status = HypothesisStatus.FAILED_VAL
    else:
        if not gate_val.passed:
            registry.transition(
                spec.id, spec.version, HypothesisStatus.FAILED_VAL, "; ".join(gate_val.reasons)
            )
            final_status = HypothesisStatus.FAILED_VAL
        elif gate_final.passed:
            registry.transition(
                spec.id, spec.version, HypothesisStatus.CANDIDATE, "confirmatory pass"
            )
            final_status = HypothesisStatus.CANDIDATE
        else:
            registry.transition(
                spec.id, spec.version, HypothesisStatus.FAILED_TEST, "; ".join(gate_final.reasons)
            )
            final_status = HypothesisStatus.FAILED_TEST

    failure_modes = [
        "Look-ahead controlled via next-bar position + causal features",
        "Multiple-testing: family N + Deflated Sharpe / Bonferroni hygiene",
        "Beta cosplay checked via excess vs B&H and beta_proxy",
        "Cost blindness checked via 2× stress",
        "Regime concentration warned if > threshold",
        "Dependent trades: block bootstrap / MC used",
        "Reality Checker: economic/execution plausibility (not stats-only)",
    ]
    if not reality.passed:
        failure_modes.append("Reality Checker hard reject: " + "; ".join(reality.reject_reasons))
    if not gate_final.passed:
        failure_modes.append("Rejected under primary after-cost Sharpe + constraints")

    metrics_out = {"train": train_m, "val": val_m}
    if test_m:
        metrics_out["test"] = test_m

    payload = {
        "hypothesis": {
            "id": spec.id,
            "version": spec.version,
            "asset": spec.asset,
            "timeframe": spec.timeframe,
            "taxonomy": spec.taxonomy.value if hasattr(spec.taxonomy, "value") else str(spec.taxonomy),
            "entry": spec.entry.expression,
            "exit": spec.exit.expression,
            "rationale": spec.rationale,
            "expected_outcome": spec.expected_outcome,
            "family_id": spec.family_id or spec.id,
        },
        "mode": mode.value,
        "final_status": final_status.value,
        "trust_score": trust,
        "repro": repro.model_dump(),
        "metrics": metrics_out,
        "baselines": baselines,
        "walk_forward": {"positive_frac": wf_pos_frac, "folds": fold_rows},
        "regimes": reg,
        "stats": {
            "sharpe_point_boot": boot.sharpe_point,
            "sharpe_ci": boot.sharpe_ci,
            "mean_bar_ci": boot.mean_bar_ci,
            "skeptical_p": boot.p_mean_gt_0_skeptical,
            "n_effective_hint": boot.n_effective_hint,
            "ann_factor": boot.ann_factor,
            "monte_carlo": {
                "max_dd_p95": mc.max_dd_p95,
                "frac_dd_breach": mc.frac_dd_breach,
                "frac_underperform_bh": mc.frac_underperform_bh,
                "terminal_p5": mc.terminal_p5,
            },
            "sensitivity": {
                "pass_frac": sens.pass_frac,
                "n_tested": sens.n_tested,
                "neighbors": sens.neighbors,
                "mode": sens.mode,
            },
            "multiple_testing": {
                "n_family": mt.n_family,
                "n_global": mt.n_global,
                "n_trials_display": getattr(mt, "n_trials_display", None),
                "sharpe_period": getattr(mt, "sharpe_period", None),
                "sharpe_annualized": getattr(mt, "sharpe_annualized", None),
                "se_period": getattr(mt, "se_period", None),
                "se_annualized": getattr(mt, "se_annualized", None),
                "bonferroni_alpha": mt.bonferroni_alpha,
                "approx_null_selection_proxy": getattr(
                    mt, "approx_null_selection_proxy", None
                ),
                "passes_hint": mt.passes_bonferroni_hint,
                "trials_ambiguous": getattr(mt, "trials_ambiguous", True),
                "trial_history_complete": getattr(mt, "trial_history_complete", False),
                "definition": getattr(mt, "definition", ""),
                "note": mt.note,
            },
            "stress_sharpe_val": stress_m.sharpe_after_cost,
            "stress_sharpe": stress_sharpe_for_gate,
        },
        "gates": {
            "passed": gate_final.passed,
            "reasons": gate_final.reasons,
            "warnings": gate_final.warnings,
        },
        "reality": reality.to_dict(),
        "failure_modes": failure_modes,
    }

    report_dir = root / cfg.get("reporting", {}).get("dir", "reports")
    stem = f"{spec.id}_v{spec.version}_{mode.value}"
    md_path, json_path = write_report(payload, report_dir, stem)
    registry.finish_run(run_id, report_path=str(md_path))

    # Research journal
    jpath = root / cfg.get("journal", {}).get("path", "journal/RESEARCH_JOURNAL.md")
    append_entry(
        jpath,
        hypothesis_id=f"{spec.id}_v{spec.version}",
        question=f"Does rule [{spec.entry.expression}] / exit [{spec.exit.expression}] have after-cost edge on {spec.asset} {spec.timeframe}?",
        why=spec.rationale or "Pipeline validation / research",
        expected=spec.expected_outcome or "Unknown — falsify if gates fail",
        result_summary=(
            f"status={final_status.value}; val_sharpe={val_m['sharpe_after_cost']:.3f}; "
            f"val_trades={val_m['n_trades']}; gate_passed={gate_final.passed}; "
            f"reasons={gate_final.reasons}"
        ),
        surprised="n/a — fill in after human review",
        why_result="See report metrics, WF folds, regimes, MC, Reality Checker",
        evolve="Only if new version with pre-registration; do not edit frozen confirmatory specs",
        future_variants="Param neighborhood listed in sensitivity section",
        extra={
            "report": str(md_path),
            "reality_passed": reality.passed,
            "reality_summary": "; ".join(
                f"{q} → {a}" for q, a in list(reality.answers.items())[:3]
            ),
        },
    )

    payload["report_md"] = str(md_path)
    payload["report_json"] = str(json_path)
    return payload
