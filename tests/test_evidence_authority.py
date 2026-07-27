"""PR6 authoritative mode gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from crl.db.schema import connect_p1, migrate_database
from crl.research.evidence.authority import (
    assess_authoritative_mode,
    decide_authoritative_mode,
    refuse_authoritative_if_blocked,
)
from crl.research.ledger.completeness import assess_completeness
from crl.research.ledger.events import append_event
from crl.research.programme.models import GovernanceCompleteness
from crl.research.planner.thesis_tree import ThesisTree, rebuild_thesis_tree

T0 = "2020-01-01T00:00:00.000000Z"


def test_authoritative_refused_on_default_p1_db(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    migrate_database(db)
    conn = connect_p1(db)
    try:
        conn.execute("BEGIN")
        conn.execute(
            """
            INSERT INTO research_lineages(research_lineage_id, created_at, description)
            VALUES ('rl1', ?, 't')
            """,
            (T0,),
        )
        append_event(conn, event_type="legacy_n_bound_proposed", payload={"n": 1})
        conn.execute("COMMIT")
        decision = assess_authoritative_mode(
            conn,
            research_lineage_id="rl1",
            force_non_authoritative=False,
        )
        assert decision.authoritative is False
        assert decision.promotion_blocked is True
        with pytest.raises(PermissionError, match="authoritative"):
            refuse_authoritative_if_blocked(decision)
    finally:
        conn.close()


def test_decide_authoritative_requires_complete():
    from crl.research.ledger.completeness import CompletenessAssessment

    a = CompletenessAssessment(
        completeness=GovernanceCompleteness.INCOMPLETE_KNOWN_GAPS,
        gaps=("x",),
        promotion_blocked=True,
        promotion_block_reasons=("y",),
        is_legacy_era=False,
        n_global=0,
        n_cohort=0,
    )
    d = decide_authoritative_mode(a)
    assert d.authoritative is False


def test_thesis_rebuild_default_non_authoritative(tmp_path: Path):
    # Empty/missing registry is ok for tree structure
    reg = tmp_path / "missing.sqlite"
    root = tmp_path / "proj"
    (root / "research_kb").mkdir(parents=True)
    tree = rebuild_thesis_tree(reg, root)
    assert tree.authoritative is False
    assert "NON-AUTHORITATIVE" in tree.summary
    assert tree.authority_reasons
