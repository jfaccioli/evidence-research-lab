from pathlib import Path

from crl.production.paper.report import paper_rows_to_markdown, write_paper_report


def test_paper_report_md(tmp_path: Path):
    rows = [
        {
            "hypothesis_id": "h1",
            "n_bars": 100,
            "n_fills": 4,
            "total_return": 0.1,
            "max_drawdown": 0.05,
            "equity_end": 55.0,
        }
    ]
    md = paper_rows_to_markdown(rows)
    assert "h1" in md
    assert "not** a research" in md or "not" in md.lower()
    p = write_paper_report(rows, tmp_path / "r.md")
    assert p.exists()
