"""Compact lab status for operators."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crl.ops.doctor import run_doctor
from crl.ops.programmes import list_programmes, programmes_to_dict
from crl.production.kill_switch import is_kill_switch_engaged
from crl.production.modes import live_explicitly_enabled
from crl.production.strategies import list_approved
from crl.shared.config import load_config, project_root


def _git_origin(root: Path | None = None) -> str | None:
    root = root or project_root()
    try:
        import subprocess

        rem = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if rem.returncode == 0 and rem.stdout.strip():
            return rem.stdout.strip()
    except Exception:
        return None
    return None


def lab_status(config_path: str | None = None) -> dict[str, Any]:
    cfg = load_config(config_path)
    doctor = run_doctor(config_path)
    progs = programmes_to_dict(list_programmes())
    origin = _git_origin()
    return {
        "doctor_ok": doctor.ok,
        "live_enabled": live_explicitly_enabled(config=cfg),
        "kill_switch": is_kill_switch_engaged(),
        "git_origin": origin,
        "approved_strategies": list_approved(),
        "confirmatory_candidates": len(list_approved()),
        "programmes": {
            "n": progs["n_programmes"],
            "n_hyps": progs["n_hyps_total"],
        },
        "failed_doctor_checks": [
            c.name for c in doctor.checks if not c.ok
        ],
        "notes": [
            "Strong tool = rejection engine + paper/shadow path.",
            "No APPROVED strategies until confirmatory survivors exist.",
            "Phase 2: pause daily technical clones (docs/PHASE2_STANCE.md).",
            *doctor.notes[:2],
        ],
    }


def write_status_md(path: Path | None = None, config_path: str | None = None) -> Path:
    st = lab_status(config_path)
    root = project_root()
    path = path or (root / "docs" / "LAB_STATUS.md")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Lab status",
        "",
        f"**Generated:** `{now}`  ",
        f"**doctor_ok:** {st['doctor_ok']}  ",
        f"**live_enabled:** {st['live_enabled']}  ",
        f"**kill_switch:** {st['kill_switch']}  ",
        f"**git_origin:** {st.get('git_origin') or '—'}  ",
        f"**approved_strategies:** {st['approved_strategies'] or '[]'}  ",
        f"**confirmatory_candidates:** {st['confirmatory_candidates']}  ",
        f"**programmes:** {st['programmes']['n']} dirs / {st['programmes']['n_hyps']} hyps  ",
        "",
        "## Notes",
        "",
    ]
    for n in st.get("notes") or []:
        lines.append(f"- {n}")
    lines.append("")
    if st.get("failed_doctor_checks"):
        lines.append("## Failed doctor checks")
        lines.append("")
        for c in st["failed_doctor_checks"]:
            lines.append(f"- {c}")
        lines.append("")
    path.write_text("\n".join(lines))
    return path

