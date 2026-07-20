"""Research journal — human-readable evolution of understanding (not code)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HEADER = """# Crypto Research Lab — Research Journal

A history of how our understanding evolved. Not code. Not data. Lessons.

---
"""


def ensure_journal(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(HEADER)


def append_entry(
    path: Path,
    *,
    hypothesis_id: str,
    question: str,
    why: str,
    expected: str,
    result_summary: str,
    surprised: str,
    why_result: str,
    evolve: str,
    future_variants: str,
    extra: dict[str, Any] | None = None,
) -> None:
    ensure_journal(path)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = f"""
## {ts} — `{hypothesis_id}`

### Question
{question}

### Why are we testing this?
{why}

### Expected outcome
{expected}

### Result
{result_summary}

### Surprised?
{surprised}

### Why?
{why_result}

### Should this idea evolve?
{evolve}

### Future variants
{future_variants}
"""
    if extra:
        block += "\n### Notes\n"
        for k, v in extra.items():
            block += f"- **{k}:** {v}\n"
    block += "\n---\n"
    with path.open("a") as f:
        f.write(block)
