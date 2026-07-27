"""Markdown summary for paper sessions (ops artifact, not science gate)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence


def paper_rows_to_markdown(rows: Sequence[dict[str, Any]], *, title: str = "Paper replay") -> str:
    lines = [
        f"# {title}",
        "",
        "> Full-sample paper equity is **not** a research promotion gate.",
        "",
        "| hypothesis | n_bars | n_fills | return | max_dd | equity_end |",
        "|------------|-------:|--------:|-------:|-------:|-----------:|",
    ]
    for r in rows:
        ret = r.get("total_return")
        ret_s = f"{ret:.2%}" if isinstance(ret, (int, float)) else "—"
        dd = r.get("max_drawdown")
        dd_s = f"{dd:.2%}" if isinstance(dd, (int, float)) else "—"
        eq = r.get("equity_end")
        eq_s = f"{eq:.2f}" if isinstance(eq, (int, float)) else "—"
        lines.append(
            f"| {r.get('hypothesis_id')} | {r.get('n_bars')} | {r.get('n_fills')} | "
            f"{ret_s} | {dd_s} | {eq_s} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_paper_report(rows: Sequence[dict[str, Any]], path: Path, **kwargs: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(paper_rows_to_markdown(rows, **kwargs))
    return path
