from pathlib import Path

from crl.ops.autopsy import autopsy_markdown, write_autopsy


def test_autopsy_handles_missing_reports(tmp_path: Path):
    d = tmp_path / "prog"
    d.mkdir()
    (d / "hyp_x.yaml").write_text(
        "id: hyp_x\nentry: {expression: above_sma_50 == 1}\nexit: {expression: above_sma_50 == 0}\n"
    )
    md = autopsy_markdown(d)
    assert "hyp_x" in md
    assert "missing" in md or "Reports found" in md
    p = write_autopsy(d)
    assert p.exists()
