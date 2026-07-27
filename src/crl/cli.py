"""CLI entrypoints for Crypto Research Lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crl.shared.config import load_config, project_root
from crl.shared.data.sources.binance_public import BinancePublicSource
from crl.shared.data.sources.mock import MockOHLCVSource
from crl.shared.data.store import latest_manifest, save_dataset
from crl.shared.types import HypothesisSpec, ResearchMode, RuleSpec, Taxonomy


def cmd_fetch(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    root = project_root()
    symbol = cfg.get("symbol_binance", "BTCUSDT")
    interval = args.interval
    processed = root / cfg["data"]["cache_dir"]
    manifests = root / cfg["data"]["manifest_dir"]

    if args.mock:
        src = MockOHLCVSource(n=args.mock_bars, seed=0)
        df = src.fetch_ohlcv(symbol, interval)
        source_name = "mock"
    else:
        src = BinancePublicSource(base_url=cfg["data"].get("base_url", "https://api.binance.com"))
        print(f"Fetching {symbol} {interval} from Binance public API...")
        df = src.fetch_ohlcv(symbol, interval)
        source_name = "binance_public"

    if df.empty:
        print("No data returned", file=sys.stderr)
        return 1
    manifest = save_dataset(
        df,
        source=source_name,
        symbol=symbol,
        interval=interval,
        processed_dir=processed,
        manifest_dir=manifests,
        source_class=source_name,
    )
    print(json.dumps(manifest.model_dump(), indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from crl.research.pipeline.run import run_hypothesis_pipeline

    cfg = load_config(args.config)
    root = project_root()
    spec_path = Path(args.hypothesis)
    raw = json.loads(spec_path.read_text()) if spec_path.suffix == ".json" else None
    if spec_path.suffix in (".yaml", ".yml"):
        import yaml

        raw = yaml.safe_load(spec_path.read_text())
    if raw is None:
        print("Hypothesis must be .json or .yaml", file=sys.stderr)
        return 1

    spec = HypothesisSpec(
        id=raw["id"],
        version=int(raw.get("version", 1)),
        asset=raw.get("asset", "BTC/USDT"),
        timeframe=raw.get("timeframe", "1d"),
        taxonomy=Taxonomy(raw.get("taxonomy", "trend")),
        family_id=raw.get("family_id", raw["id"]),
        entry=RuleSpec(expression=raw["entry"]["expression"] if isinstance(raw["entry"], dict) else raw["entry"]),
        exit=RuleSpec(expression=raw["exit"]["expression"] if isinstance(raw["exit"], dict) else raw["exit"]),
        rationale=raw.get("rationale", ""),
        expected_outcome=raw.get("expected_outcome", ""),
        feature_tags=raw.get("feature_tags", []),
    )
    mode = ResearchMode.CONFIRMATORY if args.confirmatory else ResearchMode.EXPLORATORY

    dataset_id = args.dataset_id
    df = None
    manifest = None
    if args.mock:
        src = MockOHLCVSource(n=args.mock_bars, seed=1)
        df = src.fetch_ohlcv("BTCUSDT", spec.timeframe)
        manifest = save_dataset(
            df,
            source="mock",
            symbol="BTCUSDT",
            interval=spec.timeframe,
            processed_dir=root / cfg["data"]["cache_dir"],
            manifest_dir=root / cfg["data"]["manifest_dir"],
            source_class="mock",
        )
        dataset_id = manifest.dataset_id
        df = None  # reload via id for realism
    elif not dataset_id:
        m = latest_manifest(
            root / cfg["data"]["manifest_dir"],
            symbol=cfg.get("symbol_binance", "BTCUSDT"),
            interval=spec.timeframe,
            source="binance_public",
        )
        if m is None:
            print("No dataset found. Run: crl fetch --interval 1d", file=sys.stderr)
            return 1
        dataset_id = m.dataset_id

    result = run_hypothesis_pipeline(
        spec,
        cfg,
        dataset_id=dataset_id,
        mode=mode,
    )
    print(f"Status: {result['final_status']}")
    print(f"Gate passed: {result['gates']['passed']}")
    if result["gates"]["reasons"]:
        print("Reasons:", "; ".join(result["gates"]["reasons"]))
    print(f"Report: {result['report_md']}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    from crl.research.hypotheses.registry import HypothesisRegistry

    cfg = load_config(args.config)
    root = project_root()
    reg = HypothesisRegistry(root / cfg["registry"]["path"])
    rows = reg.list_hypotheses(status=args.status)
    for r in rows:
        print(f"{r['id']} v{r['version']}  {r['status']:12}  {r['taxonomy']}  {r['timeframe']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="crl", description="Crypto Research Lab CLI")
    parser.add_argument("--config", default=None, help="Path to config YAML")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="Fetch and pin OHLCV dataset")
    p_fetch.add_argument("--interval", default="1d", choices=["1d", "4h"])
    p_fetch.add_argument("--mock", action="store_true")
    p_fetch.add_argument("--mock-bars", type=int, default=1500)
    p_fetch.set_defaults(func=cmd_fetch)

    p_run = sub.add_parser("run", help="Run hypothesis pipeline")
    p_run.add_argument("--hypothesis", "-H", required=True)
    p_run.add_argument("--dataset-id", default=None)
    p_run.add_argument("--confirmatory", action="store_true")
    p_run.add_argument("--mock", action="store_true", help="Use synthetic data")
    p_run.add_argument("--mock-bars", type=int, default=1500)
    p_run.set_defaults(func=cmd_run)

    p_list = sub.add_parser("list", help="List registry hypotheses")
    p_list.add_argument("--status", default=None)
    p_list.set_defaults(func=cmd_list)

    p_meta = sub.add_parser("meta", help="Meta-research: taxonomy survival from registry")
    p_meta.set_defaults(func=cmd_meta)

    p_batch = sub.add_parser("batch", help="Write catalog + run exploratory batch")
    p_batch.add_argument("--limit", type=int, default=None, help="Max hypotheses to run")
    p_batch.add_argument("--dataset-id", default=None)
    p_batch.add_argument("--no-write", action="store_true", help="Do not rewrite YAML catalog")
    p_batch.set_defaults(func=cmd_batch)

    p_catalog = sub.add_parser("catalog", help="Write hypothesis YAMLs from catalog")
    p_catalog.set_defaults(func=cmd_catalog)

    p_draft = sub.add_parser(
        "draft",
        help="Print guarded economic-template drafts (does not backtest)",
    )
    p_draft.set_defaults(func=cmd_draft)

    p_plan = sub.add_parser(
        "plan",
        help="Evidence-driven research plan (analyse registry → IG proposals)",
    )
    p_plan.set_defaults(func=cmd_plan)

    p_learn = sub.add_parser(
        "learn",
        help="Update research knowledge base from registry (post-batch learning)",
    )
    p_learn.set_defaults(func=cmd_learn)

    p_thesis = sub.add_parser(
        "thesis",
        help="Rebuild/print Research Thesis Tree (mechanism evidence map)",
    )
    p_thesis.set_defaults(func=cmd_thesis)

    p_paper = sub.add_parser(
        "paper",
        help="Historical paper session for one hyp (no exchange; LIVE disabled)",
    )
    p_paper.add_argument("--hypothesis", "-H", default=None)
    p_paper.add_argument(
        "--hyp-dir",
        default=None,
        help="Replay all hyp_*.yaml in directory (paper batch)",
    )
    p_paper.add_argument("--dataset-id", default=None)
    p_paper.add_argument("--cash", type=float, default=50.0)
    p_paper.add_argument("--limit", type=int, default=None)
    p_paper.add_argument(
        "--journal-dir",
        default=None,
        help="Default: data/paper_journal/",
    )
    p_paper.set_defaults(func=cmd_paper)

    p_shadow = sub.add_parser(
        "shadow",
        help="Historical shadow walk (signals only; no orders)",
    )
    p_shadow.add_argument("--hypothesis", "-H", required=True)
    p_shadow.add_argument("--dataset-id", default=None)
    p_shadow.add_argument("--log-dir", default=None, help="Default: data/shadow/")
    p_shadow.set_defaults(func=cmd_shadow)

    p_batch.add_argument(
        "--hyp-dir",
        default=None,
        help="Hypothesis directory (default examples/batch)",
    )

    args = parser.parse_args(argv)
    return int(args.func(args))


def cmd_catalog(args: argparse.Namespace) -> int:
    from crl.research.hypotheses.catalog import catalog_count, write_catalog

    root = project_root()
    paths = write_catalog(root / "examples" / "batch")
    print(f"Wrote {len(paths)} hypotheses (catalog size {catalog_count()}) to examples/batch/")
    return 0


def cmd_draft(args: argparse.Namespace) -> int:
    """List guarded templates — expand search space without auto-mining winners."""
    from crl.research.hypotheses.propose import draft_from_templates

    for spec in draft_from_templates():
        print(f"--- {spec.id} [{spec.taxonomy.value}] ---")
        print(f"entry: {spec.entry.expression}")
        print(f"exit:  {spec.exit.expression}")
        print(f"why:   {spec.rationale[:120]}...")
        print(f"expect:{spec.expected_outcome[:80]}...")
        print()
    print("Not registered/run. Add to catalog and crl batch when pre-registered.")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    """Build next-research plan from registry evidence (no trading)."""
    from crl.research.planner.plan import build_research_plan

    cfg = load_config(args.config)
    root = project_root()
    plan = build_research_plan(
        registry_path=root / cfg["registry"]["path"],
        root=root,
        cfg=cfg,
        write_artifacts=True,
    )
    print(f"Proposals: {len(plan.proposals)}")
    for p in plan.proposals:
        print(
            f"  [{p.priority_rank}] IG={p.information_gain.total:.3f}  {p.id}  "
            f"mechs={','.join(p.mechanism_ids)}"
        )
    for r in plan.recommendations:
        print(f"* {r}")
    print(f"Plan: {plan.paths.get('plan_md')}")
    return 0


def cmd_learn(args: argparse.Namespace) -> int:
    from crl.research.planner.plan import update_knowledge_after_batch

    cfg = load_config(args.config)
    root = project_root()
    state = update_knowledge_after_batch(
        registry_path=root / cfg["registry"]["path"],
        root=root,
        batch_summary=None,
    )
    print(f"KB updated_at={state.get('updated_at')}")
    print(f"Learnings: {knowledge_paths_print(root)}")
    if state.get("thesis_summary"):
        print(f"Thesis: {state['thesis_summary']}")
    return 0


def cmd_thesis(args: argparse.Namespace) -> int:
    from crl.research.planner.knowledge import knowledge_paths
    from crl.research.planner.thesis_tree import rebuild_thesis_tree

    cfg = load_config(args.config)
    root = project_root()
    notes = []
    np = root / "research_kb" / "experiment_notes.jsonl"
    if np.exists():
        import json

        for line in np.read_text().splitlines():
            if line.strip():
                notes.append(json.loads(line))
    tree = rebuild_thesis_tree(
        root / cfg["registry"]["path"], root, experiment_notes=notes
    )
    paths = knowledge_paths(root)
    print(tree.summary)
    print(f"Tree: {paths['thesis_md']}")
    # compact table
    print(f"{'mechanism':36} {'stance':22} {'conf':>5} {'n':>4} {'rec'}")
    for n in tree.nodes:
        print(
            f"{n.mechanism_id:36} {n.stance:22} {n.confidence:5.2f} {n.n_tests:4d} {n.recommendation}"
        )
    return 0


def knowledge_paths_print(root) -> str:
    from crl.research.planner.knowledge import knowledge_paths

    return str(knowledge_paths(root)["log"])


def cmd_batch(args: argparse.Namespace) -> int:
    from crl.research.pipeline.batch import run_batch

    hyp_dir = Path(args.hyp_dir) if getattr(args, "hyp_dir", None) else None
    summary = run_batch(
        hyp_dir=hyp_dir,
        dataset_id=args.dataset_id,
        limit=args.limit,
        write_hyps=not args.no_write,
        config_path=args.config,
    )
    print(
        f"Done. passed_val={summary['n_passed_val']} "
        f"failed_val={summary['n_failed_val']} errors={summary['n_errors']}"
    )
    print(f"Summary: {summary['summary_md']}")
    return 0 if summary["n_errors"] == 0 else 1


def _load_feat_for_cli(args: argparse.Namespace, timeframe: str = "1d"):
    from crl.shared.data.feature_store import load_or_build_features
    from crl.shared.data.store import load_dataset, latest_manifest

    cfg = load_config(args.config)
    root = project_root()
    mdir = root / cfg.get("data", {}).get("manifest_dir", "data/manifests")
    dataset_id = args.dataset_id
    if dataset_id is None:
        m = latest_manifest(
            mdir,
            symbol=cfg.get("symbol_binance", "BTCUSDT"),
            interval=timeframe if timeframe in ("1d", "4h") else "1d",
            source="binance_public",
        )
        if m is None:
            return None, None, "No dataset. Run: crl fetch --interval 1d"
        dataset_id = m.dataset_id
    df, _ = load_dataset(dataset_id, manifest_dir=mdir, verify_hash=True)
    cache = root / cfg.get("data", {}).get("cache_dir", "data/processed") / "features"
    feat = load_or_build_features(df, dataset_id=str(dataset_id), cache_dir=cache)
    return cfg, feat, None


def _fee_rt(cfg: dict) -> float:
    costs = cfg.get("costs", {})
    return (
        float(costs.get("fee_bps_per_side", 10)) * 2
        + float(costs.get("slippage_bps_per_side", 5)) * 2
        + float(costs.get("half_spread_bps", 1.5)) * 2
    )


def cmd_paper(args: argparse.Namespace) -> int:
    """Run a historical paper session (sim fills only)."""
    from crl.production.paper.replay import replay_hyp_dir, write_replay_summary
    from crl.production.paper.session import run_paper_session
    from crl.research.pipeline.batch import load_hypothesis_yaml

    root = project_root()
    if not args.hypothesis and not args.hyp_dir:
        print("Need --hypothesis or --hyp-dir", file=sys.stderr)
        return 2
    tf = "1d"
    if args.hypothesis:
        spec0 = load_hypothesis_yaml(Path(args.hypothesis))
        tf = spec0.timeframe if spec0.timeframe in ("1d", "4h") else "1d"
    cfg, feat, err = _load_feat_for_cli(args, tf)
    if err:
        print(err, file=sys.stderr)
        return 1
    assert cfg is not None and feat is not None
    jdir = Path(args.journal_dir) if args.journal_dir else (root / "data" / "paper_journal")
    fee_rt = _fee_rt(cfg)
    if args.hyp_dir:
        rows = replay_hyp_dir(
            Path(args.hyp_dir),
            feat,
            starting_cash=float(args.cash),
            fee_bps_rt=fee_rt,
            journal_dir=jdir,
            limit=args.limit,
        )
        out = root / "data" / "paper_journal" / "replay_summary.json"
        write_replay_summary(rows, out)
        print(json.dumps({"n": len(rows), "summary": str(out), "results": rows}, indent=2, default=str))
        return 0
    spec = load_hypothesis_yaml(Path(args.hypothesis))
    res = run_paper_session(
        spec,
        feat,
        starting_cash=float(args.cash),
        fee_bps_rt=fee_rt,
        journal_dir=jdir,
    )
    print(json.dumps({
        "hypothesis_id": res.hypothesis_id,
        "n_bars": res.n_bars,
        "n_fills": res.n_fills,
        "starting_cash": res.starting_cash,
        "equity_end": res.equity_end,
        "max_drawdown": res.max_drawdown,
        "final_position": res.final_position,
        "journal_path": res.journal_path,
        "notes": res.notes,
    }, indent=2))
    return 0


def cmd_shadow(args: argparse.Namespace) -> int:
    """Historical shadow walk — intents only."""
    from crl.production.shadow.walk import shadow_walk
    from crl.research.pipeline.batch import load_hypothesis_yaml

    root = project_root()
    spec = load_hypothesis_yaml(Path(args.hypothesis))
    tf = spec.timeframe if spec.timeframe in ("1d", "4h") else "1d"
    cfg, feat, err = _load_feat_for_cli(args, tf)
    if err:
        print(err, file=sys.stderr)
        return 1
    assert feat is not None
    log_dir = Path(args.log_dir) if args.log_dir else (root / "data" / "shadow")
    out = shadow_walk(spec, feat, log_dir=log_dir)
    print(json.dumps(out, indent=2))
    return 0


def cmd_meta(args: argparse.Namespace) -> int:
    from crl.research.meta.summary import taxonomy_survival_table

    cfg = load_config(args.config)
    root = project_root()
    table = taxonomy_survival_table(root / cfg["registry"]["path"])
    if not table:
        print("No hypotheses in registry yet.")
        return 0
    print(f"{'taxonomy':16} {'n':>5} {'survived':>8} {'rate':>8}")
    for r in table:
        print(
            f"{r['taxonomy']:16} {r['n_ideas']:5d} {r['n_survived']:8d} "
            f"{100 * r['survival_rate']:7.1f}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
