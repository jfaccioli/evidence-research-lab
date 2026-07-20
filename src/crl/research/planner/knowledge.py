"""Research knowledge base — durable learning across batches."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crl.research.planner.analyze import RegistryAnalysis, analyze_registry


def knowledge_paths(root: Path) -> dict[str, Path]:
    base = root / "research_kb"
    return {
        "dir": base,
        "state": base / "knowledge_state.json",
        "log": base / "LEARNINGS.md",
        "budget": base / "research_budget.json",
        "thesis_md": base / "THESIS_TREE.md",
        "thesis_json": base / "thesis_tree.json",
    }


def update_knowledge_base(
    registry_path: Path,
    root: Path,
    *,
    batch_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """After a batch (or on demand): refresh KB from registry + optional batch stats."""
    paths = knowledge_paths(root)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    analysis = analyze_registry(registry_path)

    prev: dict[str, Any] = {}
    if paths["state"].exists():
        prev = json.loads(paths["state"].read_text())

    state = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis.to_dict(),
        "last_batch": batch_summary,
        "family_recommendations": {
            f.family_id: {
                "recommendation": f.recommendation,
                "rationale": f.rationale,
                "n": f.n,
            }
            for f in analysis.families
        },
        "prior_update": prev.get("updated_at"),
    }
    paths["state"].write_text(json.dumps(state, indent=2, default=str))

    # Append human-readable learnings
    md = _render_learnings(analysis, batch_summary)
    if not paths["log"].exists():
        paths["log"].write_text(
            "# Research knowledge base — learnings log\n\n"
            "Updated after batches. Optimises *knowledge*, not win count.\n\n---\n"
        )
    with paths["log"].open("a") as f:
        f.write(md)

    # Research Thesis Tree (Chief Research Scientist map)
    try:
        from crl.research.planner.thesis_tree import rebuild_thesis_tree

        notes: list[dict] = []
        notes_path = paths["dir"] / "experiment_notes.jsonl"
        if notes_path.exists():
            for line in notes_path.read_text().splitlines():
                if line.strip():
                    notes.append(json.loads(line))
        tree = rebuild_thesis_tree(registry_path, root, experiment_notes=notes)
        state["thesis_summary"] = tree.summary
    except Exception as e:
        state["thesis_error"] = str(e)

    return state


def _render_learnings(
    analysis: RegistryAnalysis,
    batch_summary: dict[str, Any] | None,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"\n## {ts}\n",
        f"- Registry hypotheses: **{analysis.n_hypotheses}** (runs={analysis.n_runs})",
        f"- Unique rule fingerprints: **{len(analysis.explored_rule_fingerprints)}**",
        "",
        "### What we learned",
        "",
    ]
    for n in analysis.notes:
        lines.append(f"- {n}")
    if analysis.repeating_failures:
        lines.append("")
        lines.append("### Repeating failure modes")
        lines.append("")
        for rf in analysis.repeating_failures[:6]:
            lines.append(
                f"- **{rf['tag']}** (n={rf['count']}): {rf['interpretation']}"
            )
    lines.append("")
    lines.append("### Mechanism coverage")
    lines.append("")
    for mid, c in sorted(analysis.mechanism_coverage.items(), key=lambda x: x[1]):
        flag = " ← underrepresented" if mid in analysis.underrepresented_mechanisms else ""
        lines.append(f"- `{mid}`: {c}{flag}")

    lines.append("")
    lines.append("### Family recommendations")
    lines.append("")
    for f in analysis.families[:15]:
        lines.append(
            f"- `{f.family_id}` [{f.recommendation}] n={f.n} — {f.rationale}"
        )
    if analysis.exhausted_families:
        lines.append("")
        lines.append(
            "### Retire (exhausted) families\n\n"
            + ", ".join(f"`{x}`" for x in analysis.exhausted_families[:20])
        )

    if batch_summary:
        lines.append("")
        lines.append("### Latest batch snapshot")
        lines.append("")
        lines.append(
            f"- run={batch_summary.get('n_run')} passed_val={batch_summary.get('n_passed_val')} "
            f"failed={batch_summary.get('n_failed_val')} errors={batch_summary.get('n_errors')}"
        )

    lines.append("")
    lines.append("### Planner stance")
    lines.append("")
    lines.append(
        "- Prefer underrepresented mechanisms with high information gain.\n"
        "- Do not clone exhausted families.\n"
        "- Null results that cleanly retire a mechanism are valuable.\n"
    )
    lines.append("\n---\n")
    return "\n".join(lines)
