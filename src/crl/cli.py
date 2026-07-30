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
    from crl.shared.universe import assert_symbol_allowed, default_binance_symbol

    cfg = load_config(args.config)
    root = project_root()
    symbol = assert_symbol_allowed(
        getattr(args, "symbol", None) or default_binance_symbol(cfg),
        cfg,
        context="fetch",
    )
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

    from crl.shared.universe import asset_to_binance_symbol, assert_symbol_allowed

    run_symbol = assert_symbol_allowed(
        asset_to_binance_symbol(spec.asset), cfg, context="run"
    )

    dataset_id = args.dataset_id
    df = None
    manifest = None
    if args.mock:
        src = MockOHLCVSource(n=args.mock_bars, seed=1)
        df = src.fetch_ohlcv(run_symbol, spec.timeframe)
        manifest = save_dataset(
            df,
            source="mock",
            symbol=run_symbol,
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
            symbol=run_symbol,
            interval=spec.timeframe,
            source="binance_public",
        )
        if m is None:
            print(
                f"No dataset for {run_symbol}. Run: crl fetch --interval 1d --symbol {run_symbol}",
                file=sys.stderr,
            )
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
    p_fetch.add_argument(
        "--symbol",
        default=None,
        help="Binance symbol in universe (default: config symbol_binance; e.g. ETHUSDT)",
    )
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
    p_batch.add_argument(
        "--write-catalog",
        action="store_true",
        help="Force catalog write even when --hyp-dir is set (default: no write for programme dirs)",
    )
    p_batch.add_argument(
        "--registry-path",
        default=None,
        help="Override registry sqlite (use temp path for programme batches)",
    )
    p_batch.set_defaults(func=cmd_batch)

    p_doctor = sub.add_parser(
        "doctor",
        help="Lab health check (configs, LIVE disabled, data, programmes)",
    )
    p_doctor.set_defaults(func=cmd_doctor)

    p_progs = sub.add_parser(
        "programmes",
        help="List pre-registered programme dirs under examples/batch",
    )
    p_progs.add_argument(
        "--write-md",
        action="store_true",
        help="Write docs/PROGRAMME_INVENTORY.md from live inventory",
    )
    p_progs.set_defaults(func=cmd_programmes)

    p_batch.add_argument(
        "--temp-registry",
        action="store_true",
        help="Use data/processed/tmp_batch_<hypdir>.sqlite (implies no catalog write)",
    )

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
    p_paper.add_argument(
        "--mandate-limits",
        action="store_true",
        help="Apply tiny-live envelope (1 trade/day, notional cap)",
    )
    p_paper.add_argument(
        "--require-approved",
        action="store_true",
        help="Refuse unless hyp id is in production.strategies.APPROVED (empty until survivors)",
    )
    p_paper.add_argument(
        "--record-clock",
        action="store_true",
        help="Append paper-clock session under data/paper_clock/ (mandate path; not a science gate)",
    )
    p_paper.set_defaults(func=cmd_paper)

    p_status = sub.add_parser(
        "status",
        help="Compact lab status (doctor + programmes + LIVE/kill)",
    )
    p_status.add_argument(
        "--write-md",
        action="store_true",
        help="Write docs/LAB_STATUS.md",
    )
    p_status.add_argument(
        "--readiness",
        action="store_true",
        help="Include lab-ops vs autotrading readiness scores",
    )
    p_status.set_defaults(func=cmd_status)

    p_runp = sub.add_parser(
        "run-programme",
        help="Doctor + series attach (INDEX.yaml) + temp-registry explor/conf",
    )
    p_runp.add_argument("hyp_dir", help="Path e.g. examples/batch/fade")
    p_runp.add_argument("--dataset-id", default=None)
    p_runp.add_argument("--limit", type=int, default=None)
    p_runp.add_argument(
        "--skip-doctor",
        action="store_true",
        help="Do not require doctor ok (not recommended)",
    )
    p_runp.add_argument(
        "--require-series",
        action="store_true",
        help="Fail if INDEX external series missing/short (<180 events)",
    )
    p_runp.set_defaults(func=cmd_run_programme)

    p_series = sub.add_parser(
        "series",
        help="List/validate pinned PIT series under data/processed/{flow,external}",
    )
    p_series.add_argument(
        "action",
        choices=["list", "ready"],
        help="list local series, or ready (check programme INDEX attach)",
    )
    p_series.add_argument(
        "--hyp-dir",
        default=None,
        help="For ready: programme dir with INDEX.yaml external block",
    )
    p_series.set_defaults(func=cmd_series)

    p_queue = sub.add_parser(
        "queue",
        help="Show machine research queue state (research_kb/research_queue_state.json)",
    )
    p_queue.set_defaults(func=cmd_queue)

    p_newp = sub.add_parser(
        "new-programme",
        help="Scaffold locked programme dir + design stub (does not run science)",
    )
    p_newp.add_argument("slug", help="Directory name under examples/batch/")
    p_newp.add_argument("--mechanism", default="TODO mechanism")
    p_newp.add_argument(
        "--design",
        default=None,
        help="Design doc path (default docs/PROGRAMME_<SLUG>_V1.md)",
    )
    p_newp.add_argument("--kind", default=None, choices=["flow", "external"])
    p_newp.add_argument("--series-id", default=None)
    p_newp.add_argument("--prefix", default="xser")
    p_newp.add_argument("--n-hyps", type=int, default=3)
    p_newp.set_defaults(func=cmd_new_programme)

    p_metaf = sub.add_parser(
        "meta-research",
        help="Workstream F: principles ledger + family trial multiplicity snapshot",
    )
    p_metaf.add_argument(
        "--sync",
        action="store_true",
        help="Rewrite research_kb/meta_research_principles.json from code",
    )
    p_metaf.set_defaults(func=cmd_meta_research)

    p_eacq = sub.add_parser(
        "evidence-acq",
        help="Living evidence-acquisition roadmap (rank novel data; cost/EV advice)",
    )
    p_eacq.add_argument(
        "--sync",
        action="store_true",
        help="Rewrite research_kb/evidence_acquisition_catalog.json",
    )
    p_eacq.add_argument(
        "--recommend",
        default=None,
        metavar="ITEM_ID",
        help="Cost/EV recommendation for catalog id (e.g. vendor_exchange_flow)",
    )
    p_eacq.add_argument(
        "--annual-usd",
        type=float,
        default=None,
        help="Optional annual cost for --recommend",
    )
    p_eacq.add_argument(
        "--programme-locked",
        action="store_true",
        help="With --recommend: hyps pre-registered",
    )
    p_eacq.add_argument(
        "--free-exhausted",
        action="store_true",
        help="With --recommend: free alternatives considered exhausted",
    )
    p_eacq.set_defaults(func=cmd_evidence_acq)

    p_leda = sub.add_parser(
        "leda",
        help="LEDA protocol, evidence channels, and thin stack decide",
    )
    p_leda.add_argument(
        "action",
        choices=[
            "protocol",
            "eval-vol-risk",
            "eval-trend",
            "eval-xasset",
            "decide",
            "eval-stack",
            "eval-vol-veto",
            "eval-vol-veto-grid",
            "paper",
        ],
        help=(
            "protocol | channel skill evals | decide | economic evals | "
            "paper (LEDA-7 audit wire)"
        ),
    )
    p_leda.add_argument(
        "--mock",
        action="store_true",
        help="For eval-*: use mock OHLCV instead of pinned BTC",
    )
    p_leda.add_argument(
        "--e-forecast",
        type=float,
        default=None,
        help="For decide: forecast score in [0,1]",
    )
    p_leda.add_argument(
        "--e-risk",
        type=float,
        default=None,
        help="For decide: risk score in [0,1]",
    )
    p_leda.add_argument(
        "--mode",
        default="paper",
        help="For decide: execution mode label (default paper)",
    )
    p_leda.set_defaults(func=cmd_leda)

    p_alpha = sub.add_parser(
        "alpha-discovery",
        help="Rank information advantages (not vendors); Alpha Discovery Directive",
    )
    p_alpha.add_argument("--sync", action="store_true", help="Rewrite alpha_discovery_catalog.json")
    p_alpha.set_defaults(func=cmd_alpha_discovery)

    p_obs = sub.add_parser(
        "observe",
        help="Discover/characterize market properties (not trade signals)",
    )
    p_obs.add_argument(
        "action",
        choices=[
            "inventory",
            "characterize-aggression",
            "fetch-premium",
            "characterize-premium",
            "characterize-premium-residual",
            "fetch-stable-supply",
            "characterize-stable-supply",
            "fetch-defi-tvl",
            "characterize-defi-tvl",
            "fetch-cross-basis",
            "characterize-cross-basis",
            "synthesis-review",
            "mechanisms",
            "study-vol-clustering",
            "study-leverage-cycle",
            "study-uncertainty-behaviour",
            "study-leverage-incremental-rv",
        ],
        help="Properties + mechanism studies (mechanism-first mission)",
    )
    p_obs.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data where applicable",
    )
    p_obs.add_argument(
        "--symbol",
        default="BTCUSDT",
        help="Symbol for premium fetch (default BTCUSDT)",
    )
    p_obs.set_defaults(func=cmd_observe)

    p_opsr = sub.add_parser(
        "ops-readiness",
        help="Operational readiness track (paper/safety/audit; NOT scientific promotion)",
    )
    p_opsr.add_argument(
        "action",
        choices=["check", "checklist"],
        nargs="?",
        default="check",
        help="Run ops readiness checklist (zero capital, non-alpha policies)",
    )
    p_opsr.set_defaults(func=cmd_ops_readiness)

    p_plat = sub.add_parser(
        "platform",
        help="Trading Platform (engineering; benchmarks only — not alpha discovery)",
    )
    p_plat.add_argument(
        "action",
        choices=["list", "run", "walkforward", "attribute", "deploy-gate"],
        help="list|run|walkforward|attribute|deploy-gate",
    )
    p_plat.add_argument(
        "--strategy",
        default="bench_buy_and_hold",
        help="Strategy id (default bench_buy_and_hold)",
    )
    p_plat.add_argument(
        "--mock",
        action="store_true",
        help="Use mock OHLCV instead of pinned BTC",
    )
    p_plat.set_defaults(func=cmd_platform)

    p_rd = sub.add_parser(
        "rd",
        help="Research Director — prioritise science; knowledge graph; anti-duplication",
    )
    p_rd.add_argument(
        "action",
        choices=[
            "status",
            "programmes",
            "areas",
            "rank",
            "graph",
            "check",
            "sync",
            "report",
            "inefficiencies",
            "eir",
            "phase1",
        ],
        help="status|programmes|areas|rank|graph|check|sync|report|inefficiencies|eir|phase1",
    )
    p_rd.add_argument(
        "--query",
        default="",
        help="For check: keyword to test against retired/duplicate work",
    )
    p_rd.add_argument(
        "--include-forbidden",
        action="store_true",
        help="For rank: include forbidden directions",
    )
    p_rd.set_defaults(func=cmd_rd)

    p_pcs = sub.add_parser(
        "pcs",
        help="Production Candidate Sprint (deployability-ranked science)",
    )
    p_pcs.add_argument(
        "action",
        choices=["status", "eval-vol-scale", "eval-basis-riskoff"],
        help="status | eval-vol-scale | eval-basis-riskoff",
    )
    p_pcs.add_argument("--mock", action="store_true", help="Mock OHLCV (not for promotion)")
    p_pcs.set_defaults(func=cmd_pcs)

    p_autopsy = sub.add_parser(
        "autopsy",
        help="Write GATE_AUTOPSY_V1.md from reports for a programme dir",
    )
    p_autopsy.add_argument("hyp_dir", help="Path e.g. examples/batch/fade")
    p_autopsy.add_argument(
        "--mode",
        default="exploratory",
        choices=["exploratory", "confirmatory"],
    )
    p_autopsy.set_defaults(func=cmd_autopsy)

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

    root = project_root()
    hyp_dir = Path(args.hyp_dir) if getattr(args, "hyp_dir", None) else None
    # Programme dirs: never rewrite catalog by default (avoids clobbering locked hyps).
    if hyp_dir is not None:
        write_hyps = bool(getattr(args, "write_catalog", False))
    else:
        write_hyps = not args.no_write
    if args.no_write or getattr(args, "temp_registry", False):
        write_hyps = False

    registry_path = getattr(args, "registry_path", None)
    if getattr(args, "temp_registry", False) and not registry_path:
        name = hyp_dir.name if hyp_dir else "catalog"
        reg_dir = root / "data" / "processed"
        reg_dir.mkdir(parents=True, exist_ok=True)
        registry_path = str(reg_dir / f"tmp_batch_{name}.sqlite")
        print(f"temp_registry={registry_path}", flush=True)

    summary = run_batch(
        hyp_dir=hyp_dir,
        dataset_id=args.dataset_id,
        limit=args.limit,
        write_hyps=write_hyps,
        config_path=args.config,
        registry_path=registry_path,
    )
    print(
        f"Done. passed_val={summary['n_passed_val']} "
        f"failed_val={summary['n_failed_val']} errors={summary['n_errors']}"
    )
    print(f"Summary: {summary['summary_md']}")
    return 0 if summary["n_errors"] == 0 else 1


def cmd_doctor(args: argparse.Namespace) -> int:
    from crl.ops.doctor import run_doctor

    rep = run_doctor(args.config)
    print(json.dumps(rep.to_dict(), indent=2))
    return 0 if rep.ok else 1


def cmd_programmes(args: argparse.Namespace) -> int:
    from crl.ops.programmes import list_programmes, programmes_to_dict, write_inventory_md

    rows = list_programmes()
    print(json.dumps(programmes_to_dict(rows), indent=2))
    if getattr(args, "write_md", False):
        path = write_inventory_md()
        print(f"wrote {path}", flush=True)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    from crl.ops.status import lab_status, write_status_md

    st = lab_status(args.config)
    if getattr(args, "readiness", False):
        from crl.ops.readiness import readiness_report

        st = {**st, "readiness": readiness_report(args.config)}
    print(json.dumps(st, indent=2))
    if getattr(args, "write_md", False):
        path = write_status_md(config_path=args.config)
        print(f"wrote {path}", flush=True)
    return 0 if st.get("doctor_ok") and not st.get("live_enabled") else 1


def cmd_series(args: argparse.Namespace) -> int:
    from crl.ops.programme_index import load_programme_index
    from crl.ops.series_attach import list_local_series, series_readiness

    if args.action == "list":
        print(json.dumps({"series": list_local_series()}, indent=2))
        return 0
    if not args.hyp_dir:
        print("--hyp-dir required for ready", file=sys.stderr)
        return 2
    idx = load_programme_index(Path(args.hyp_dir))
    print(json.dumps(series_readiness(idx.external), indent=2, default=str))
    return 0 if series_readiness(idx.external).get("ready") else 1


def cmd_queue(args: argparse.Namespace) -> int:
    from crl.ops.research_queue_state import load_queue_state

    print(json.dumps(load_queue_state(), indent=2))
    return 0


def cmd_new_programme(args: argparse.Namespace) -> int:
    from crl.ops.new_programme import scaffold_programme

    design = args.design or f"docs/PROGRAMME_{args.slug.upper()}_V1.md"
    try:
        out = scaffold_programme(
            args.slug,
            design_rel=design,
            mechanism=args.mechanism,
            external_kind=args.kind,
            series_id=args.series_id,
            prefix=args.prefix,
            placeholder_hyps=int(args.n_hyps),
        )
    except Exception as e:
        print(f"new-programme failed: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2))
    return 0


def cmd_meta_research(args: argparse.Namespace) -> int:
    """Workstream F — improve how the lab thinks (not invent signals)."""
    from crl.research.meta.family_trials import multiplicity_snapshot
    from crl.research.meta.workstream_f import principles_report, sync_principles_file

    if getattr(args, "sync", False):
        path = sync_principles_file()
        print(f"wrote {path}", flush=True)
    else:
        # keep file fresh on every read
        sync_principles_file()
    print(
        json.dumps(
            {
                "workstream": "F_scientific_meta_research",
                "principles": principles_report(),
                "multiplicity": multiplicity_snapshot(),
            },
            indent=2,
            default=str,
        )
    )
    return 0


def cmd_evidence_acq(args: argparse.Namespace) -> int:
    """Rank novel predictive-information sources; advise cost vs EV."""
    from crl.research.meta.evidence_acquisition import (
        acquisition_summary,
        recommend_spend,
        ranked_items,
        sync_catalog,
    )

    if getattr(args, "sync", False) or True:
        path = sync_catalog()
        if getattr(args, "sync", False):
            print(f"wrote {path}", flush=True)
    if getattr(args, "recommend", None):
        out = recommend_spend(
            args.recommend,
            annual_usd_cost=getattr(args, "annual_usd", None),
            programme_locked=bool(getattr(args, "programme_locked", False)),
            free_alternatives_exhausted=bool(getattr(args, "free_exhausted", False)),
        )
        print(json.dumps(out, indent=2))
        return 0 if out.get("should_spend_money_now") or out.get("recommendation_base") in (
            "acquire_free",
            "wait",
            "reject",
            "buy_if_programme_ready",
        ) else 1
    print(
        json.dumps(
            {
                "summary": acquisition_summary(),
                "ranked": [
                    {
                        "rank": i.get("rank"),
                        "id": i["id"],
                        "name": i["name"],
                        "ev": i["ev"],
                        "recommendation": i["recommendation"],
                        "cost_class": i["cost_class"],
                        "cost_note": i.get("cost_note"),
                        "human_required": i.get("human_required"),
                    }
                    for i in ranked_items()
                ],
            },
            indent=2,
        )
    )
    return 0


def _leda_load_ohlcv(args: argparse.Namespace, *, symbol: str = "BTCUSDT"):
    """Shared 1d (or mock) loader for LEDA channel evals."""
    if getattr(args, "mock", False):
        from crl.shared.data.sources.mock import MockOHLCVSource

        seed = 11 if symbol.startswith("BTC") else 13
        ohlcv = MockOHLCVSource(n=800, seed=seed).fetch_ohlcv(symbol, "1d")
        if ohlcv.index.tz is None:
            ohlcv.index = ohlcv.index.tz_localize("UTC")
        return ohlcv, "mock", f"mock_{symbol}"

    from crl.shared.config import load_config, project_root
    from crl.shared.data.store import latest_manifest, load_dataset

    cfg = load_config(args.config)
    root = project_root()
    m = latest_manifest(
        root / cfg["data"]["manifest_dir"],
        symbol=symbol,
        interval="1d",
        source="binance_public",
    )
    if m is None:
        return None, None, None
    ohlcv, _ = load_dataset(
        m.dataset_id,
        manifest_dir=root / cfg["data"]["manifest_dir"],
        verify_hash=True,
    )
    return ohlcv, "binance_public", m.dataset_id


def cmd_leda(args: argparse.Namespace) -> int:
    """LEDA-0 protocol, LEDA-1/2 channel evals, LEDA-3 decide."""
    if args.action == "protocol":
        from crl.leda.protocol import protocol_summary

        print(json.dumps(protocol_summary(), indent=2))
        return 0

    if args.action == "decide":
        from crl.leda.stack import decide_bar

        out = decide_bar(
            asof_time="cli",
            e_forecast=getattr(args, "e_forecast", None),
            e_risk=getattr(args, "e_risk", None),
            mode=getattr(args, "mode", "paper") or "paper",
        )
        print(json.dumps(out, indent=2))
        return 0

    ohlcv, source, dataset_id = _leda_load_ohlcv(args)
    if ohlcv is None:
        print("No BTC 1d dataset; use --mock or crl fetch --interval 1d", file=sys.stderr)
        return 1

    if args.action in ("eval-stack", "eval-vol-veto", "eval-vol-veto-grid", "paper"):
        if args.action == "paper":
            from crl.leda.paper import run_leda_paper_session
            from crl.shared.config import project_root

            jdir = project_root() / "data" / "paper_journal" / "leda"
            report = run_leda_paper_session(
                ohlcv,
                journal_dir=jdir,
                max_bars=800 if getattr(args, "mock", False) else None,
            )
        else:
            from crl.leda.economic import (
                evaluate_stack_economic,
                evaluate_vol_veto_policy,
                evaluate_vol_veto_threshold_grid,
            )

            if args.action == "eval-stack":
                report = evaluate_stack_economic(ohlcv)
            elif args.action == "eval-vol-veto":
                report = evaluate_vol_veto_policy(ohlcv)
            else:
                report = evaluate_vol_veto_threshold_grid(ohlcv)
        report["dataset_id"] = dataset_id
        report["source"] = source
        print(json.dumps(report, indent=2))
        # Exit 0 always for diagnostic run; promotion is never implied
        return 0

    if args.action == "eval-xasset":
        from crl.leda.channels.xasset import (
            CHANNEL_ID,
            CHANNEL_VERSION,
            build_xasset_evidence,
            evaluate_xasset_forecast_skill,
        )

        eth, eth_source, eth_id = _leda_load_ohlcv(args, symbol="ETHUSDT")
        if eth is None:
            print("No ETH 1d dataset; use --mock or crl fetch ETH", file=sys.stderr)
            return 1
        # Align calendars (inner join on index)
        common = ohlcv.index.intersection(eth.index)
        if len(common) < 200:
            print(f"Insufficient BTC∩ETH overlap: {len(common)}", file=sys.stderr)
            return 1
        btc_a = ohlcv.loc[common]
        eth_a = eth.loc[common]
        ev = build_xasset_evidence(btc_a, eth_a)
        skill = evaluate_xasset_forecast_skill(ev)
        print(
            json.dumps(
                {
                    "leda": "5a",
                    "channel_id": CHANNEL_ID,
                    "version": CHANNEL_VERSION,
                    "dataset_id_btc": dataset_id,
                    "dataset_id_eth": eth_id,
                    "source": source,
                    "eth_source": eth_source,
                    "n_bars": len(common),
                    "n_scored": int(ev["score"].notna().sum()),
                    "skill": skill,
                    "promotion": "not_applicable — forecast evidence only",
                },
                indent=2,
            )
        )
        return 0 if skill.get("ok") else 1

    if args.action == "eval-vol-risk":
        from crl.leda.channels.vol_risk import (
            CHANNEL_ID,
            CHANNEL_VERSION,
            build_vol_risk_evidence,
            evaluate_vol_forecast_skill,
        )

        ev = build_vol_risk_evidence(ohlcv)
        skill = evaluate_vol_forecast_skill(ev)
        payload = {
            "leda": "1",
            "channel_id": CHANNEL_ID,
            "version": CHANNEL_VERSION,
            "dataset_id": dataset_id,
            "source": source,
            "n_bars": len(ohlcv),
            "n_scored": int(ev["score"].notna().sum()),
            "skill": skill,
            "promotion": "not_applicable — risk evidence only",
        }
    else:
        # eval-trend
        from crl.leda.channels.trend import (
            CHANNEL_ID,
            CHANNEL_VERSION,
            build_trend_evidence,
            evaluate_trend_forecast_skill,
        )

        ev = build_trend_evidence(ohlcv)
        skill = evaluate_trend_forecast_skill(ev)
        payload = {
            "leda": "2",
            "channel_id": CHANNEL_ID,
            "version": CHANNEL_VERSION,
            "dataset_id": dataset_id,
            "source": source,
            "n_bars": len(ohlcv),
            "n_scored": int(ev["score"].notna().sum()),
            "skill": skill,
            "promotion": "not_applicable — forecast evidence only",
        }

    print(json.dumps(payload, indent=2))
    return 0 if skill.get("ok") else 1


def cmd_observe(args: argparse.Namespace) -> int:
    """Market property discovery — characterize measurable market behaviour."""
    from crl.shared.config import load_config, project_root

    if args.action == "inventory":
        inv = project_root() / "docs" / "OBSERVATION_INVENTORY.md"
        directive = project_root() / "docs" / "MARKET_PROPERTIES_DIRECTIVE.md"
        print(
            json.dumps(
                {
                    "directive": str(directive),
                    "inventory": str(inv),
                    "properties": ["kline_aggression", "perp_premium"],
                    "philosophy": (
                        "Characterize market properties; do not mine indicators"
                    ),
                },
                indent=2,
            )
        )
        if inv.exists():
            print(inv.read_text()[:4000])
        return 0

    if args.action == "fetch-premium":
        from crl.shared.data.premium import save_premium_series
        from crl.shared.data.sources.binance_premium import BinancePremiumSource

        symbol = str(getattr(args, "symbol", None) or "BTCUSDT").upper()
        print(f"Fetching {symbol} 1d premiumIndexKlines from Binance futures...", flush=True)
        src = BinancePremiumSource()
        df = src.fetch_premium_klines(symbol, "1d")
        root = project_root()
        meta = save_premium_series(
            df,
            symbol=symbol,
            interval="1d",
            processed_dir=root / "data" / "processed" / "premium",
        )
        print(json.dumps(meta, indent=2))
        return 0

    if args.action == "fetch-stable-supply":
        from crl.shared.data.sources.defillama_stablecoins import DefiLlamaStablecoinSource
        from crl.shared.data.stablecoin_supply import save_supply_series

        print("Fetching aggregate stablecoin supply from DefiLlama...", flush=True)
        src = DefiLlamaStablecoinSource(publish_lag_days=1)
        df = src.fetch_supply_events()
        root = project_root()
        meta = save_supply_series(
            df,
            processed_dir=root / "data" / "processed" / "stablecoin",
            publish_lag_days=1,
        )
        print(json.dumps(meta, indent=2))
        return 0

    if args.action == "fetch-defi-tvl":
        from crl.shared.data.defi_tvl import save_tvl_series
        from crl.shared.data.sources.defillama_tvl import DefiLlamaTvlSource

        print("Fetching aggregate DeFi TVL from DefiLlama...", flush=True)
        df = DefiLlamaTvlSource(publish_lag_days=1).fetch_tvl_events()
        meta = save_tvl_series(
            df,
            processed_dir=project_root() / "data" / "processed" / "defi_tvl",
            publish_lag_days=1,
        )
        print(json.dumps(meta, indent=2))
        return 0

    if args.action == "fetch-cross-basis":
        import numpy as np
        import pandas as pd

        from crl.shared.data.cross_venue import save_basis_series
        from crl.shared.data.sources.coinbase_public import CoinbasePublicSource

        print("Fetching Coinbase BTC-USD daily closes...", flush=True)
        cb = CoinbasePublicSource().fetch_daily_closes("BTC-USD")
        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("Need BTC Binance OHLCV for basis numerator", file=sys.stderr)
            return 1
        # Same UTC calendar day on both venues (not asof lag — that induced return contamination)
        bars = (
            ohlcv.index.tz_convert("UTC")
            if ohlcv.index.tz is not None
            else ohlcv.index.tz_localize("UTC")
        )
        bn = pd.DataFrame(
            {
                "event_time": pd.DatetimeIndex(pd.to_datetime(bars, utc=True)).floor("D"),
                "bn_close": ohlcv["close"].astype(float).to_numpy(),
            }
        )
        right = cb.copy()
        right["event_time"] = pd.to_datetime(right["event_time"], utc=True).dt.floor("D")
        merged = bn.merge(right, on="event_time", how="inner")
        merged = merged.dropna(subset=["bn_close", "cb_close"])
        # Drop incomplete current UTC day
        today = pd.Timestamp.now(tz="UTC").floor("D")
        merged = merged.loc[merged["event_time"] < today]
        merged["basis"] = np.log(
            merged["bn_close"].astype(float) / merged["cb_close"].astype(float)
        )
        basis_df = merged[["event_time", "basis", "bn_close", "cb_close"]]
        meta = save_basis_series(
            basis_df,
            processed_dir=project_root() / "data" / "processed" / "cross_venue",
        )
        meta["binance_dataset_id"] = dataset_id
        meta["binance_source"] = source
        meta["n_coinbase"] = len(cb)
        meta["alignment"] = "same_utc_calendar_day_inner_join"
        meta["pit_note"] = (
            "Same-day closes known after UTC day completes; use lag-1 for "
            "predictive association (USD vs USDT not FX-adjusted)"
        )
        print(json.dumps(meta, indent=2, default=str))
        return 0

    if args.action == "characterize-cross-basis":
        from crl.research.market_properties.cross_venue_basis import (
            characterize_cross_venue_basis,
        )
        from crl.shared.data.cross_venue import load_latest_basis

        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC OHLCV", file=sys.stderr)
            return 1
        if getattr(args, "mock", False):
            import numpy as np
            import pandas as pd

            rng = np.random.default_rng(0)
            basis = pd.DataFrame(
                {
                    "event_time": ohlcv.index,
                    "basis": rng.normal(0, 0.001, size=len(ohlcv)),
                }
            )
            meta = {"series_id": "mock_basis"}
        else:
            basis, meta = load_latest_basis(
                project_root() / "data" / "processed" / "cross_venue"
            )
        report = characterize_cross_venue_basis(ohlcv, basis)
        report["dataset_id"] = dataset_id
        report["basis_series_id"] = meta.get("series_id")
        print(json.dumps(report, indent=2))
        return 0 if report.get("ok") else 1

    def _load_mechanism_series():
        root = project_root()
        premium = funding = supply = tvl = basis = None
        try:
            from crl.shared.data.premium import load_latest_premium

            premium, _ = load_latest_premium(root / "data" / "processed" / "premium")
        except Exception:
            pass
        fund_dir = root / "data" / "processed" / "funding"
        if fund_dir.exists():
            import pandas as pd

            parts = sorted(fund_dir.glob("binance_funding_BTCUSDT_*.parquet"))
            if parts:
                funding = pd.read_parquet(parts[-1])
        try:
            from crl.shared.data.stablecoin_supply import load_latest_supply

            supply, _ = load_latest_supply(root / "data" / "processed" / "stablecoin")
        except Exception:
            pass
        try:
            from crl.shared.data.defi_tvl import load_latest_tvl

            tvl, _ = load_latest_tvl(root / "data" / "processed" / "defi_tvl")
        except Exception:
            pass
        try:
            from crl.shared.data.cross_venue import load_latest_basis

            basis, _ = load_latest_basis(root / "data" / "processed" / "cross_venue")
        except Exception:
            pass
        return premium, funding, supply, tvl, basis

    def _prefer_micro_ohlcv(ohlcv, dataset_id):
        if "taker_buy_base" in ohlcv.columns or getattr(args, "mock", False):
            return ohlcv, dataset_id
        from crl.shared.config import load_config
        from crl.shared.data.store import load_dataset

        root = project_root()
        cfg = load_config(args.config)
        mdir = root / cfg["data"]["manifest_dir"]
        for mp in sorted(mdir.glob("binance_public_BTCUSDT_1d_*.json"), reverse=True):
            try:
                mid = json.loads(mp.read_text())["dataset_id"]
                df, _ = load_dataset(mid, manifest_dir=mdir, verify_hash=True)
                if "taker_buy_base" in df.columns:
                    return df, mid
            except Exception:
                continue
        return ohlcv, dataset_id

    if args.action == "mechanisms":
        from crl.research.mechanisms.registry import load_registry, ranked_mechanisms

        reg = load_registry()
        print(
            json.dumps(
                {
                    "directive": "docs/MECHANISM_DISCOVERY_DIRECTIVE.md",
                    "registry_doc": "docs/MECHANISM_REGISTRY.md",
                    "workflow": reg.get("workflow"),
                    "mechanisms": ranked_mechanisms(),
                    "retired_combination_families": reg.get("retired_combination_families"),
                },
                indent=2,
            )
        )
        return 0

    if args.action == "study-vol-clustering":
        from crl.research.mechanisms.vol_clustering import study_vol_clustering

        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC OHLCV", file=sys.stderr)
            return 1
        ohlcv, dataset_id = _prefer_micro_ohlcv(ohlcv, dataset_id)
        premium, funding, supply, _, _ = _load_mechanism_series()
        report = study_vol_clustering(
            ohlcv,
            premium_events=premium,
            funding_events=funding,
            supply_events=supply,
        )
        report["dataset_id"] = dataset_id
        report["ohlcv_source"] = source
        print(json.dumps(report, indent=2, default=str))
        return 0 if report.get("ok") else 1

    def _load_oi_events(ohlcv):
        import pandas as pd

        oi_events = None
        oi_dir = project_root() / "data" / "processed" / "oi"
        if oi_dir.exists():
            parts = sorted(oi_dir.glob("bybit_oi_*.parquet"))
            if parts:
                oi_events = pd.read_parquet(parts[-1])
        if oi_events is None and getattr(args, "mock", False):
            import numpy as np

            rng = np.random.default_rng(0)
            oi_events = pd.DataFrame(
                {
                    "oi_time": ohlcv.index,
                    "open_interest": 1000
                    * np.exp(np.cumsum(rng.normal(0, 0.02, len(ohlcv)))),
                }
            )
        return oi_events

    if args.action == "study-leverage-cycle":
        from crl.research.mechanisms.leverage_cycle import study_leverage_cycle

        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC OHLCV", file=sys.stderr)
            return 1
        ohlcv, dataset_id = _prefer_micro_ohlcv(ohlcv, dataset_id)
        premium, funding, _, _, _ = _load_mechanism_series()
        oi_events = _load_oi_events(ohlcv)
        report = study_leverage_cycle(
            ohlcv,
            oi_events=oi_events,
            premium_events=premium,
            funding_events=funding,
        )
        report["dataset_id"] = dataset_id
        report["ohlcv_source"] = source
        print(json.dumps(report, indent=2, default=str))
        return 0 if report.get("ok") else 1

    if args.action == "study-leverage-incremental-rv":
        from crl.research.mechanisms.leverage_incremental_rv import (
            study_leverage_incremental_rv_skill,
        )

        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC OHLCV", file=sys.stderr)
            return 1
        ohlcv, dataset_id = _prefer_micro_ohlcv(ohlcv, dataset_id)
        premium, funding, _, _, _ = _load_mechanism_series()
        oi_events = _load_oi_events(ohlcv)
        if oi_events is None:
            print("OI events required", file=sys.stderr)
            return 1
        report = study_leverage_incremental_rv_skill(
            ohlcv,
            oi_events=oi_events,
            premium_events=premium,
            funding_events=funding,
        )
        report["dataset_id"] = dataset_id
        report["ohlcv_source"] = source
        print(json.dumps(report, indent=2, default=str))
        return 0 if report.get("ok") else 1

    if args.action == "study-uncertainty-behaviour":
        from crl.research.mechanisms.uncertainty_behaviour import (
            study_uncertainty_behaviour,
        )

        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC OHLCV", file=sys.stderr)
            return 1
        ohlcv, dataset_id = _prefer_micro_ohlcv(ohlcv, dataset_id)
        premium, funding, _, _, basis = _load_mechanism_series()
        report = study_uncertainty_behaviour(
            ohlcv,
            basis_events=basis,
            premium_events=premium,
            funding_events=funding,
        )
        report["dataset_id"] = dataset_id
        report["ohlcv_source"] = source
        print(json.dumps(report, indent=2, default=str))
        return 0 if report.get("ok") else 1

    if args.action == "synthesis-review":
        from crl.research.market_properties.synthesis import run_property_synthesis_review

        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC OHLCV", file=sys.stderr)
            return 1
        ohlcv, dataset_id = _prefer_micro_ohlcv(ohlcv, dataset_id)
        premium, funding, supply, tvl, basis = _load_mechanism_series()
        report = run_property_synthesis_review(
            ohlcv,
            premium_events=premium,
            funding_events=funding,
            supply_events=supply,
            tvl_events=tvl,
            basis_events=basis,
        )
        report["dataset_id"] = dataset_id
        report["ohlcv_source"] = source
        print(json.dumps(report, indent=2, default=str))
        return 0

    if args.action in ("characterize-stable-supply", "characterize-defi-tvl"):
        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC 1d; fetch or --mock", file=sys.stderr)
            return 1

        def _load_funding_premium():
            import pandas as pd

            funding = prem = None
            fund_dir = project_root() / "data" / "processed" / "funding"
            if fund_dir.exists():
                parts = sorted(fund_dir.glob("binance_funding_BTCUSDT_*.parquet"))
                if parts:
                    funding = pd.read_parquet(parts[-1])
            try:
                from crl.shared.data.premium import load_latest_premium

                prem, _ = load_latest_premium(
                    project_root() / "data" / "processed" / "premium"
                )
            except Exception:
                prem = None
            return funding, prem

        if args.action == "characterize-stable-supply":
            from crl.research.market_properties.stablecoin_supply import (
                characterize_stablecoin_supply,
            )
            from crl.shared.data.stablecoin_supply import load_latest_supply

            if getattr(args, "mock", False):
                import numpy as np
                import pandas as pd

                rng = np.random.default_rng(1)
                n = len(ohlcv)
                level = 1e10 * np.exp(np.cumsum(rng.normal(0.0002, 0.002, size=n)))
                supply = pd.DataFrame({"event_time": ohlcv.index, "supply_usd": level})
                meta = {"series_id": "mock_stable_supply"}
                funding = prem = None
            else:
                supply, meta = load_latest_supply(
                    project_root() / "data" / "processed" / "stablecoin"
                )
                funding, prem = _load_funding_premium()
            report = characterize_stablecoin_supply(
                ohlcv, supply, funding_events=funding, premium_events=prem
            )
            report["supply_series_id"] = meta.get("series_id")
        else:
            from crl.research.market_properties.defi_tvl import characterize_defi_tvl
            from crl.shared.data.defi_tvl import load_latest_tvl

            if getattr(args, "mock", False):
                import numpy as np
                import pandas as pd

                rng = np.random.default_rng(2)
                n = len(ohlcv)
                level = 1e9 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, size=n)))
                tvl = pd.DataFrame({"event_time": ohlcv.index, "tvl_usd": level})
                meta = {"series_id": "mock_tvl"}
                supply = funding = prem = None
            else:
                tvl, meta = load_latest_tvl(
                    project_root() / "data" / "processed" / "defi_tvl"
                )
                funding, prem = _load_funding_premium()
                supply = None
                try:
                    from crl.shared.data.stablecoin_supply import load_latest_supply

                    supply, _ = load_latest_supply(
                        project_root() / "data" / "processed" / "stablecoin"
                    )
                except Exception:
                    supply = None
            report = characterize_defi_tvl(
                ohlcv,
                tvl,
                supply_events=supply,
                funding_events=funding,
                premium_events=prem,
            )
            report["tvl_series_id"] = meta.get("series_id")

        report["dataset_id"] = dataset_id
        report["ohlcv_source"] = source
        print(json.dumps(report, indent=2))
        return 0 if report.get("ok") else 1

    if args.action in ("characterize-premium", "characterize-premium-residual"):
        from crl.research.market_properties.kline_aggression import build_aggression_frame
        from crl.research.market_properties.perp_premium import (
            characterize_perp_premium,
            characterize_premium_residual,
        )
        from crl.shared.data.premium import load_latest_premium

        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC 1d; fetch or --mock", file=sys.stderr)
            return 1
        if getattr(args, "mock", False):
            import numpy as np
            import pandas as pd

            rng = np.random.default_rng(0)
            n = len(ohlcv)
            prem = pd.DataFrame(
                {
                    "event_time": ohlcv.index,
                    "premium_close": rng.normal(0, 0.0003, size=n),
                }
            )
            meta = {"series_id": "mock_premium", "source": "mock"}
            funding = pd.DataFrame(
                {
                    "funding_time": ohlcv.index,
                    "funding_rate": rng.normal(0, 1e-4, size=n),
                }
            )
        else:
            prem, meta = load_latest_premium(
                project_root() / "data" / "processed" / "premium",
                symbol=str(getattr(args, "symbol", None) or "BTCUSDT"),
            )
            funding = None
            fund_dir = project_root() / "data" / "processed" / "funding"
            if fund_dir.exists():
                import pandas as pd

                parts = sorted(fund_dir.glob("binance_funding_BTCUSDT_*.parquet"))
                if parts:
                    funding = pd.read_parquet(parts[-1])

        if args.action == "characterize-premium-residual":
            if funding is None:
                print("Funding series required for residual characterization", file=sys.stderr)
                return 1
            report = characterize_premium_residual(ohlcv, prem, funding)
        else:
            aggr = None
            if "taker_buy_base" in ohlcv.columns:
                try:
                    aggr = build_aggression_frame(ohlcv)
                except ValueError:
                    aggr = None
            report = characterize_perp_premium(
                ohlcv, prem, funding_events=funding, aggression=aggr
            )
        report["dataset_id"] = dataset_id
        report["ohlcv_source"] = source
        report["premium_series_id"] = meta.get("series_id")
        print(json.dumps(report, indent=2))
        return 0 if report.get("ok") else 1

    # characterize-aggression
    from crl.research.market_properties.kline_aggression import characterize_kline_aggression

    ohlcv, source, dataset_id = _leda_load_ohlcv(args)
    if ohlcv is None:
        print("No BTC 1d dataset; use --mock or crl fetch --interval 1d", file=sys.stderr)
        return 1
    if "taker_buy_base" not in ohlcv.columns and not getattr(args, "mock", False):
        from crl.shared.data.store import load_dataset

        root = project_root()
        cfg = load_config(args.config)
        mdir = root / cfg["data"]["manifest_dir"]
        found = None
        for mp in sorted(mdir.glob("binance_public_BTCUSDT_1d_*.json"), reverse=True):
            try:
                mid = json.loads(mp.read_text())["dataset_id"]
                df, _ = load_dataset(mid, manifest_dir=mdir, verify_hash=True)
                if "taker_buy_base" in df.columns:
                    found = (df, mid)
                    break
            except Exception:
                continue
        if found is None:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "reason": (
                            "Pinned BTC OHLCV lacks kline micro columns. "
                            "Run: python -m crl fetch --interval 1d"
                        ),
                        "dataset_id": dataset_id,
                    },
                    indent=2,
                )
            )
            return 1
        ohlcv, dataset_id = found
        source = "binance_public"

    report = characterize_kline_aggression(ohlcv)
    report["dataset_id"] = dataset_id
    report["source"] = source
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


def cmd_ops_readiness(args: argparse.Namespace) -> int:
    """Operational readiness track — zero capital; not scientific promotion."""
    from crl.production.ops_readiness import run_ops_readiness_checklist
    from crl.shared.config import project_root

    root = project_root()
    jdir = root / "data" / "ops" / "readiness_journals"
    report = run_ops_readiness_checklist(root=root, journal_dir=jdir)
    out = report.to_dict()
    # Persist latest summary
    out_path = root / "data" / "ops" / "OPS_READINESS_LATEST.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    out["summary_path"] = str(out_path)
    print(json.dumps(out, indent=2))
    return 0 if report.all_ok() else 1


def cmd_pcs(args: argparse.Namespace) -> int:
    """Production Candidate Sprint."""
    if args.action == "status":
        from pathlib import Path

        from crl.shared.config import project_root

        root = project_root()
        res = root / "research_kb" / "pcs" / "PCS_V1_RESULT.json"
        print(
            json.dumps(
                {
                    "sprint": "PRODUCTION_CANDIDATE_SPRINT_V1",
                    "doc": "docs/PRODUCTION_CANDIDATE_SPRINT_V1.md",
                    "primary": "PCS_VOL_SCALE_V1",
                    "reserve": "PCS_BASIS_RISKOFF (not opened until primary decisive)",
                    "result_path": str(res) if res.exists() else None,
                    "result": json.loads(res.read_text()) if res.exists() else None,
                },
                indent=2,
            )
        )
        return 0

    if args.action == "eval-vol-scale":
        from crl.research.pcs.vol_scale import evaluate_pcs_vol_scale
        from crl.shared.config import project_root

        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC 1d; fetch or --mock", file=sys.stderr)
            return 1
        if getattr(args, "mock", False):
            print("WARNING: mock data — not valid for confirmatory pass", file=sys.stderr)
        report = evaluate_pcs_vol_scale(ohlcv)
        report["dataset_id"] = dataset_id
        report["source"] = source
        out_dir = project_root() / "research_kb" / "pcs"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "PCS_V1_RESULT.json"
        path.write_text(json.dumps(report, indent=2))
        report["wrote"] = str(path)
        print(json.dumps(report, indent=2))
        return 0 if report.get("confirmatory_pass") else 1

    if args.action == "eval-basis-riskoff":
        from crl.research.pcs.basis_riskoff import evaluate_pcs_basis_riskoff
        from crl.shared.config import project_root
        from crl.shared.data.cross_venue import load_latest_basis

        ohlcv, source, dataset_id = _leda_load_ohlcv(args)
        if ohlcv is None:
            print("No BTC 1d", file=sys.stderr)
            return 1
        try:
            basis, bmeta = load_latest_basis(
                project_root() / "data" / "processed" / "cross_venue"
            )
        except Exception as e:
            print(f"basis series required: {e}", file=sys.stderr)
            return 1
        report = evaluate_pcs_basis_riskoff(ohlcv, basis)
        report["dataset_id"] = dataset_id
        report["basis_series_id"] = bmeta.get("series_id")
        out_dir = project_root() / "research_kb" / "pcs"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "PCS_V1_BASIS_RESULT.json"
        path.write_text(json.dumps(report, indent=2))
        report["wrote"] = str(path)
        print(json.dumps(report, indent=2))
        return 0 if report.get("confirmatory_pass") else 1

    return 2


def cmd_rd(args: argparse.Namespace) -> int:
    """Research Director — laboratory principal investigator interface."""
    from crl.research_director.core import (
        director_report,
        is_duplicate_or_retired,
        knowledge_graph_summary,
        list_areas,
        list_programmes,
        ranked_directions,
        sync_rd_state,
    )

    action = args.action
    if action in ("status", "report", "sync"):
        out = sync_rd_state() if action == "sync" else {"report": director_report()}
        if action == "sync":
            print(json.dumps({"synced": True, "state_path": out["state_path"], "md_path": out["md_path"]}, indent=2))
            print(json.dumps(out["report"], indent=2, default=str))
        else:
            print(json.dumps(out["report"] if "report" in out else out, indent=2, default=str))
        return 0
    if action == "programmes":
        print(json.dumps({"programmes": list_programmes()}, indent=2))
        return 0
    if action == "areas":
        print(json.dumps({"areas": list_areas()}, indent=2))
        return 0
    if action == "rank":
        rows = ranked_directions(include_forbidden=bool(args.include_forbidden))
        print(
            json.dumps(
                {
                    "n": len(rows),
                    "directions": rows,
                    "note": "Higher composite_score = higher joint priority",
                },
                indent=2,
            )
        )
        return 0
    if action == "graph":
        from crl.research_director.core import _load_json

        g = _load_json("knowledge_graph.json")
        print(
            json.dumps(
                {
                    "summary": knowledge_graph_summary(),
                    "n_nodes": len(g.get("nodes") or []),
                    "n_edges": len(g.get("edges") or []),
                    "nodes": g.get("nodes"),
                    "edges": g.get("edges"),
                },
                indent=2,
            )
        )
        return 0
    if action == "check":
        q = (args.query or "").strip()
        if not q:
            print("rd check requires --query", file=sys.stderr)
            return 2
        print(json.dumps(is_duplicate_or_retired(q), indent=2))
        return 0
    if action == "inefficiencies":
        from crl.research_director.inefficiency import inefficiency_report

        print(json.dumps(inefficiency_report(), indent=2))
        return 0
    if action == "eir":
        from pathlib import Path

        from crl.research_director.inefficiency import eir_required, top_inefficiency
        from crl.shared.config import project_root

        top = top_inefficiency()
        eir_path = (
            project_root()
            / "docs"
            / "EVIDENCE_INVESTMENT_REVIEW_INEFFICIENCY_2026-07-30.md"
        )
        print(
            json.dumps(
                {
                    "eir_required": eir_required(top),
                    "top_inefficiency": top.get("id") if top else None,
                    "eir_path": str(eir_path) if eir_path.exists() else None,
                    "recommendation": (
                        "Free delayed US spot BTC ETF net flows with PIT lag; "
                        "no paid API until free path fails"
                    ),
                },
                indent=2,
            )
        )
        if eir_path.exists():
            # print first ~80 lines of EIR for operator visibility
            lines = eir_path.read_text().splitlines()
            print("\n".join(lines[:80]))
        return 0
    if action == "phase1":
        from crl.research_director.phase1 import phase1_status

        print(json.dumps(phase1_status(), indent=2))
        return 0
    return 2


def cmd_platform(args: argparse.Namespace) -> int:
    """Trading Platform CLI — benchmark validation only (not science)."""
    # Ensure benchmark registration
    import crl.platform  # noqa: F401
    from crl.platform.strategy import get_strategy, list_strategies
    from crl.shared.config import project_root

    if args.action == "list":
        rows = [
            {
                "id": m.id,
                "name": m.name,
                "is_benchmark": m.is_benchmark,
                "is_scientific_candidate": m.is_scientific_candidate,
                "params": m.params,
                "description": m.description,
            }
            for m in list_strategies()
        ]
        print(
            json.dumps(
                {
                    "programme": "trading_platform",
                    "n": len(rows),
                    "strategies": rows,
                    "note": "Benchmarks are engineering artefacts, not alpha claims",
                },
                indent=2,
            )
        )
        return 0

    if args.action == "deploy-gate":
        from crl.platform.deployment import deployment_gate

        meta = get_strategy(args.strategy).meta
        print(json.dumps(deployment_gate(meta), indent=2))
        return 0

    # Need OHLCV for run / walkforward / attribute
    ohlcv, source, dataset_id = _leda_load_ohlcv(args)
    if ohlcv is None:
        print("No BTC 1d data; use --mock or crl fetch", file=sys.stderr)
        return 1

    if args.action == "attribute":
        from crl.platform.attribution import attribute_all_benchmarks

        report = attribute_all_benchmarks(ohlcv)
        report["dataset_id"] = dataset_id
        report["source"] = source
        print(json.dumps(report, indent=2))
        return 0

    strat = get_strategy(args.strategy)
    if args.action == "run":
        from crl.platform.engine import run_platform_backtest

        audit_dir = project_root() / "data" / "platform" / "audit"
        res = run_platform_backtest(strat, ohlcv, audit_dir=audit_dir)
        out = res.to_summary()
        out["dataset_id"] = dataset_id
        out["source"] = source
        print(json.dumps(out, indent=2, default=str))
        return 0

    if args.action == "walkforward":
        from crl.platform.walkforward import walkforward_strategy

        report = walkforward_strategy(strat, ohlcv)
        report["dataset_id"] = dataset_id
        report["source"] = source
        print(json.dumps(report, indent=2))
        return 0

    print(f"unknown action {args.action}", file=sys.stderr)
    return 2


def cmd_alpha_discovery(args: argparse.Namespace) -> int:
    """Information advantages first — Alpha Discovery Directive."""
    from crl.research.meta.alpha_discovery import (
        discovery_summary,
        ranked_advantages,
        self_critique_prompt,
        sync_catalog,
    )

    path = sync_catalog()
    if getattr(args, "sync", False):
        print(f"wrote {path}", flush=True)
    print(
        json.dumps(
            {
                "directive": "docs/ALPHA_DISCOVERY_DIRECTIVE.md",
                "question": (
                    "What information advantage might exist that this laboratory "
                    "cannot currently observe?"
                ),
                "summary": discovery_summary(),
                "self_critique": self_critique_prompt(),
                "advantages": [
                    {
                        "rank": a["rank"],
                        "id": a["id"],
                        "name": a["name"],
                        "mechanism": a["mechanism"],
                        "ev": a["ev"],
                        "action": a["action"],
                        "currently_observable": a["currently_observable"],
                        "cost_class": a["cost_class"],
                    }
                    for a in ranked_advantages()
                ],
            },
            indent=2,
        )
    )
    return 0


def cmd_run_programme(args: argparse.Namespace) -> int:
    from crl.ops.run_programme import run_programme

    try:
        out = run_programme(
            Path(args.hyp_dir),
            dataset_id=args.dataset_id,
            config_path=args.config,
            limit=args.limit,
            require_doctor=not args.skip_doctor,
            require_series_ready=bool(getattr(args, "require_series", False)),
        )
    except Exception as e:
        print(f"run-programme failed: {e}", file=sys.stderr)
        return 1
    print(json.dumps({
        k: out[k]
        for k in (
            "programme",
            "n_run",
            "n_passed_val",
            "n_failed_val",
            "n_errors",
            "dataset_id",
            "registry_path",
            "summary_json",
            "confirmatory",
            "ran_at",
        )
        if k in out
    }, indent=2, default=str))
    for r in out.get("results") or []:
        print(
            f"  {r.get('id')}: {r.get('status')} n={r.get('val_trades')} "
            f"sh={r.get('val_sharpe')} {r.get('reasons')}"
        )
    for c in out.get("confirmatory") or []:
        print(f"  CONF {c.get('id')}: {c.get('status')} {c.get('reasons') or c.get('error')}")
    # Auto autopsy when reports exist
    try:
        from crl.ops.autopsy import write_autopsy

        ap = write_autopsy(Path(args.hyp_dir))
        print(f"autopsy={ap}", flush=True)
    except Exception as e:
        print(f"autopsy_skip: {e}", flush=True)
    return 0 if int(out.get("n_errors") or 0) == 0 else 1


def cmd_autopsy(args: argparse.Namespace) -> int:
    from crl.ops.autopsy import write_autopsy

    try:
        path = write_autopsy(Path(args.hyp_dir), mode=args.mode)
    except Exception as e:
        print(f"autopsy failed: {e}", file=sys.stderr)
        return 1
    print(path)
    return 0


def _load_feat_for_cli(
    args: argparse.Namespace,
    timeframe: str = "1d",
    *,
    symbol: str | None = None,
):
    from crl.shared.data.feature_store import load_or_build_features
    from crl.shared.data.store import load_dataset, latest_manifest
    from crl.shared.universe import assert_symbol_allowed, default_binance_symbol

    cfg = load_config(args.config)
    root = project_root()
    mdir = root / cfg.get("data", {}).get("manifest_dir", "data/manifests")
    dataset_id = args.dataset_id
    if dataset_id is None:
        sym = assert_symbol_allowed(
            symbol or default_binance_symbol(cfg), cfg, context="paper/shadow"
        )
        m = latest_manifest(
            mdir,
            symbol=sym,
            interval=timeframe if timeframe in ("1d", "4h") else "1d",
            source="binance_public",
        )
        if m is None:
            return (
                None,
                None,
                f"No dataset for {sym}. Run: crl fetch --interval 1d --symbol {sym}",
            )
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
    try:
        return _cmd_paper_body(args, root, load_hypothesis_yaml, replay_hyp_dir, run_paper_session)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1


def _cmd_paper_body(args, root, load_hypothesis_yaml, replay_hyp_dir, run_paper_session) -> int:
    from crl.shared.universe import asset_to_binance_symbol

    tf = "1d"
    sym = None
    if args.hypothesis:
        spec0 = load_hypothesis_yaml(Path(args.hypothesis))
        tf = spec0.timeframe if spec0.timeframe in ("1d", "4h") else "1d"
        sym = asset_to_binance_symbol(spec0.asset)
    cfg, feat, err = _load_feat_for_cli(args, tf, symbol=sym)
    if err:
        print(err, file=sys.stderr)
        return 1
    assert cfg is not None and feat is not None
    jdir = Path(args.journal_dir) if args.journal_dir else (root / "data" / "paper_journal")
    fee_rt = _fee_rt(cfg)
    if getattr(args, "require_approved", False):
        from crl.production.strategies import assert_approved

        if args.hypothesis:
            assert_approved(load_hypothesis_yaml(Path(args.hypothesis)).id)

    if args.hyp_dir:
        if getattr(args, "require_approved", False):
            from crl.production.strategies import assert_approved

            for yp in sorted(Path(args.hyp_dir).glob("hyp_*.yaml")):
                assert_approved(load_hypothesis_yaml(yp).id)
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
        from crl.production.paper.report import write_paper_report

        md = root / "data" / "paper_journal" / "replay_summary.md"
        write_paper_report(rows, md, title=f"Paper replay: {Path(args.hyp_dir).name}")
        print(json.dumps({
            "n": len(rows),
            "summary_json": str(out),
            "summary_md": str(md),
            "results": rows,
        }, indent=2, default=str))
        return 0
    spec = load_hypothesis_yaml(Path(args.hypothesis))
    if getattr(args, "require_approved", False):
        from crl.production.strategies import assert_approved

        assert_approved(spec.id)
    res = run_paper_session(
        spec,
        feat,
        starting_cash=float(args.cash),
        fee_bps_rt=fee_rt,
        journal_dir=jdir,
        mandate_limits=bool(getattr(args, "mandate_limits", False)),
    )
    out: dict = {
        "hypothesis_id": res.hypothesis_id,
        "n_bars": res.n_bars,
        "n_fills": res.n_fills,
        "starting_cash": res.starting_cash,
        "equity_end": res.equity_end,
        "max_drawdown": res.max_drawdown,
        "final_position": res.final_position,
        "journal_path": res.journal_path,
        "notes": res.notes,
    }
    if getattr(args, "record_clock", False):
        from crl.production.paper.clock import default_clock_dir, record_session

        clock = record_session(
            default_clock_dir(root),
            res.hypothesis_id,
            n_bars=res.n_bars,
            n_fills=res.n_fills,
            equity_end=res.equity_end,
            max_drawdown=res.max_drawdown,
            journal_path=res.journal_path,
            mandate_limits=bool(getattr(args, "mandate_limits", False)),
        )
        out["paper_clock"] = {
            "strategy_id": clock.strategy_id,
            "status": clock.status,
            "n_sessions": len(clock.sessions),
            "min_calendar_days": clock.min_calendar_days,
        }
    print(json.dumps(out, indent=2))
    return 0


def cmd_shadow(args: argparse.Namespace) -> int:
    """Historical shadow walk — intents only."""
    from crl.production.shadow.walk import shadow_walk
    from crl.research.pipeline.batch import load_hypothesis_yaml
    from crl.shared.universe import asset_to_binance_symbol

    root = project_root()
    spec = load_hypothesis_yaml(Path(args.hypothesis))
    tf = spec.timeframe if spec.timeframe in ("1d", "4h") else "1d"
    cfg, feat, err = _load_feat_for_cli(
        args, tf, symbol=asset_to_binance_symbol(spec.asset)
    )
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
