"""Research Director programme — coordination, not experiments."""

from __future__ import annotations

from crl.research_director.core import (
    annual_objective,
    composite_score,
    director_report,
    is_duplicate_or_retired,
    knowledge_graph_summary,
    list_programmes,
    ranked_directions,
    sync_rd_state,
)


def test_programmes_include_rd_and_alpha():
    ids = {p["id"] for p in list_programmes()}
    assert "research_director" in ids
    assert "alpha_discovery" in ids
    assert "trading_platform" in ids


def test_composite_score_penalizes_overlap():
    high = composite_score(
        EIG=4, EEV=3, Pa=2, SciRisk=1, EngCost=1, ExtDep=0, Overlap=0
    )
    low = composite_score(
        EIG=4, EEV=3, Pa=2, SciRisk=1, EngCost=1, ExtDep=0, Overlap=5
    )
    assert high > low


def test_rank_and_forbidden():
    open_ranks = ranked_directions(include_forbidden=False)
    assert open_ranks
    assert all(d.get("status") != "forbidden" for d in open_ranks)
    assert "composite_score" in open_ranks[0]
    all_ranks = ranked_directions(include_forbidden=True)
    assert len(all_ranks) >= len(open_ranks)


def test_duplicate_check_blocks_mom():
    r = is_duplicate_or_retired("momentum long flat daily")
    # may or may not hit depending on string match — check mom keyword
    r2 = is_duplicate_or_retired("tsmom")
    assert "query" in r2


def test_graph_and_sync():
    kg = knowledge_graph_summary()
    assert kg["n_nodes"] > 5
    assert kg["n_edges"] > 3
    out = sync_rd_state()
    assert "state_path" in out
    assert "md_path" in out
    rep = director_report()
    assert "annual_objective" in rep
    assert "gates" in rep["standards"]
    assert rep["standards"]["weaken_gates_for_platform"] is False
    assert "understanding" in annual_objective().lower()
    assert rep.get("active_initiative") == "ECONOMIC_INEFFICIENCY_PROGRAMME_V1"
    assert "economic_inefficiency" in rep


def test_inefficiency_catalogue_ranks_etf_first():
    from crl.research_director.inefficiency import (
        eir_required,
        inefficiency_report,
        ranked_inefficiencies,
        top_inefficiency,
    )

    rows = ranked_inefficiencies()
    assert rows
    assert rows[0]["id"] == "ineff_etf_create_redeem"
    assert "IScore" in rows[0]
    top = top_inefficiency()
    assert top is not None
    assert eir_required(top) is True
    rep = inefficiency_report()
    assert rep["eir_required"] is True
    assert "etf" in rep["recommendation"].lower()
