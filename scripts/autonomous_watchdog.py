#!/usr/bin/env python3
"""Hourly watchdog (mode C): ensure 24h marathon (mode B) is still running.

- If pause file: do nothing
- If marathon running and heartbeat fresh: log OK
- If marathon should be running but dead/stale: restart marathon in background
- If marathon completed its 24h window: leave completed (don't infinite restart unless CRL_MARATHON_AUTO_RESTART=1)
- Also runs one queue ticket if queue has pending and marathon not starving CPU
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_kb" / "rd" / "MARATHON_STATE.json"
PAUSE = ROOT / "research_kb" / "rd" / "AUTONOMOUS_PAUSE"
LOG_DIR = ROOT / "logs" / "autonomous"
STATUS = ROOT / "research_kb" / "rd" / "WATCHDOG_STATUS.json"
STALE_S = 10 * 60  # 10 min without heartbeat => dead
AUTO_RESTART = os.environ.get("CRL_MARATHON_AUTO_RESTART", "0") == "1"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{utcnow().isoformat()}] WATCHDOG {msg}"
    print(line, flush=True)
    with open(LOG_DIR / "watchdog.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state() -> dict:
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def start_marathon() -> int:
    py = ROOT / ".venv" / "bin" / "python"
    log_path = LOG_DIR / "marathon_daemon.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["CRL_MARATHON_HOURS"] = env.get("CRL_MARATHON_HOURS", "24")
    # detach
    proc = subprocess.Popen(
        [str(py), str(ROOT / "scripts" / "autonomous_marathon.py")],
        cwd=str(ROOT),
        env=env,
        stdout=open(log_path, "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log(f"started marathon pid={proc.pid}")
    return proc.pid


def main() -> int:
    if PAUSE.exists():
        log("paused")
        STATUS.write_text(json.dumps({"status": "paused", "at": utcnow().isoformat()}, indent=2) + "\n")
        return 0

    st = load_state()
    status = st.get("status")
    pid = st.get("pid")
    hb = st.get("heartbeat_at")
    ends = st.get("ends_at")

    alive = isinstance(pid, int) and pid_alive(pid)
    hb_age = None
    if hb:
        try:
            hb_age = (utcnow() - datetime.fromisoformat(hb)).total_seconds()
        except Exception:
            hb_age = None

    stale = hb_age is not None and hb_age > STALE_S
    window_open = True
    if ends:
        try:
            window_open = utcnow() < datetime.fromisoformat(ends)
        except Exception:
            window_open = True

    action = "none"
    if status == "running" and alive and not stale:
        action = "healthy"
        log(f"marathon healthy pid={pid} hb_age={hb_age:.0f}s jobs={st.get('jobs_done')}")
    elif status == "running" and (not alive or stale) and window_open:
        action = "restart"
        log(f"marathon dead/stale (alive={alive} stale={stale}) — restarting")
        start_marathon()
    elif status in (None, "", "idle", "crashed") or (status == "completed" and AUTO_RESTART):
        # no marathon — start one (user wants B+C)
        action = "start"
        log(f"no active marathon (status={status}) — starting 24h marathon")
        start_marathon()
    elif status == "completed" and not window_open:
        action = "completed_window"
        log("marathon window completed — not auto-restarting (set CRL_MARATHON_AUTO_RESTART=1 to loop)")
    elif status == "paused":
        action = "paused_state"
        log("state says paused")
    else:
        action = f"observe_{status}"
        log(f"observe status={status} alive={alive} window_open={window_open}")

    # Also drain one allowlisted queue ticket if any pending (light work)
    try:
        tick = ROOT / "scripts" / "autonomous_research_tick.py"
        py = ROOT / ".venv" / "bin" / "python"
        subprocess.run(
            [str(py), str(tick)],
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            timeout=45 * 60,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        log(f"queue tick skip: {e}")

    STATUS.write_text(
        json.dumps(
            {
                "status": action,
                "at": utcnow().isoformat(),
                "marathon": {
                    "status": load_state().get("status"),
                    "pid": load_state().get("pid"),
                    "jobs_done": load_state().get("jobs_done"),
                    "ends_at": load_state().get("ends_at"),
                    "last_job": load_state().get("last_job"),
                },
            },
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
