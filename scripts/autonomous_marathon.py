#!/usr/bin/env python3
"""24h research marathon — keep running local science until budget expires.

Safety: no live trading, no secrets, pause file honored.
Heartbeat: research_kb/rd/MARATHON_STATE.json
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_kb" / "rd" / "MARATHON_STATE.json"
PAUSE = ROOT / "research_kb" / "rd" / "AUTONOMOUS_PAUSE"
LOG_DIR = ROOT / "logs" / "autonomous"
LOCK = LOG_DIR / "marathon.lock"
DEFAULT_HOURS = 24
HEARTBEAT_EVERY_S = 60
TICKET_GAP_S = 30  # pause between programmes
# After a full pass of all jobs, rest so 24h is time-bound not busy-spin
CYCLE_GAP_S = int(os.environ.get("CRL_MARATHON_CYCLE_GAP_S", "300"))


def discover_jobs() -> list[str]:
    """Allowlisted science scripts under scripts/ (new tickets auto-picked up)."""
    jobs: list[str] = []
    for pat in ("run_autonomous_ticket_*.py", "run_ms_*.py"):
        for p in sorted((ROOT / "scripts").glob(pat)):
            jobs.append(f"scripts/{p.name}")
    # stable fallback if folder empty
    if not jobs:
        jobs = [
            "scripts/run_autonomous_ticket_ms_vol_funding_v1.py",
            "scripts/run_autonomous_ticket_ms_oi_dir_v1.py",
            "scripts/run_autonomous_ticket_ms_basis_long_v1.py",
            "scripts/run_autonomous_ticket_ms_fund_neg_crowding_v1.py",
            "scripts/run_ms_funding_carry_v1.py",
        ]
    return jobs


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def write_state(**kwargs) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    cur = {}
    if STATE.exists():
        try:
            cur = json.loads(STATE.read_text())
        except Exception:
            cur = {}
    cur.update(kwargs)
    cur["heartbeat_at"] = utcnow().isoformat()
    cur["pid"] = os.getpid()
    STATE.write_text(json.dumps(cur, indent=2) + "\n")


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{utcnow().isoformat()}] MARATHON {msg}"
    print(line, flush=True)
    with open(LOG_DIR / "marathon.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    hours = float(os.environ.get("CRL_MARATHON_HOURS", DEFAULT_HOURS))
    # 0 or negative = no job cap; stop only when time budget expires
    max_jobs = int(os.environ.get("CRL_MARATHON_MAX_JOBS", "0"))
    ends = utcnow() + timedelta(hours=hours)
    jobs = discover_jobs()

    if PAUSE.exists():
        log("PAUSE present at start — exit")
        write_state(status="paused", message="pause file at start")
        return 0

    if LOCK.exists():
        try:
            old = int(LOCK.read_text().strip().split()[0])
            os.kill(old, 0)
            log(f"another marathon pid={old} alive — exit")
            return 0
        except Exception:
            LOCK.unlink(missing_ok=True)

    LOCK.write_text(f"{os.getpid()} {utcnow().isoformat()}\n")
    # Fresh window: clear prior completion fields
    write_state(
        status="running",
        started_at=utcnow().isoformat(),
        ends_at=ends.isoformat(),
        hours=hours,
        jobs_done=0,
        last_job=None,
        mode="B_continuous_time_only",
        max_jobs=max_jobs if max_jobs > 0 else None,
        job_catalog=jobs,
        finished_at=None,
        message=None,
        error=None,
    )
    log(
        f"START hours={hours} ends={ends.isoformat()} "
        f"max_jobs={'unlimited' if max_jobs <= 0 else max_jobs} n_scripts={len(jobs)}"
    )

    py = ROOT / ".venv" / "bin" / "python"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["CRL_AUTONOMOUS_TICK"] = "1"
    # strip secrets
    for k in list(env):
        ku = k.upper()
        if any(x in ku for x in ("API_KEY", "SECRET", "PASSWORD", "PRIVATE_KEY", "BINANCE_KEY")):
            env.pop(k, None)

    jobs_done = 0
    job_i = 0
    try:
        while utcnow() < ends:
            if max_jobs > 0 and jobs_done >= max_jobs:
                log(f"hit max_jobs={max_jobs}")
                break
            if PAUSE.exists():
                log("PAUSE detected — stopping marathon")
                write_state(status="paused", jobs_done=jobs_done, message="human pause")
                return 0

            # refresh catalog so new ticket scripts appear mid-run
            if job_i % max(len(jobs), 1) == 0:
                jobs = discover_jobs()

            write_state(status="running", jobs_done=jobs_done, ends_at=ends.isoformat())

            script = jobs[job_i % len(jobs)]
            job_i += 1
            cmd = [str(py), str(ROOT / script)]
            log(f"JOB start {script} (#{jobs_done + 1})")
            write_state(last_job=script, last_job_started=utcnow().isoformat())

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(ROOT),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=40 * 60,
                )
                tail = (proc.stdout or "")[-1500:]
                log(f"JOB end {script} code={proc.returncode}")
                if tail.strip():
                    log("stdout: " + tail.replace("\n", " | ")[:800])
                if proc.returncode != 0 and proc.stderr:
                    log("stderr: " + (proc.stderr or "")[-500:].replace("\n", " | "))
            except subprocess.TimeoutExpired:
                log(f"JOB timeout {script}")
            except Exception as e:
                log(f"JOB error {script}: {e}")

            jobs_done += 1
            write_state(jobs_done=jobs_done, last_job=script, last_job_finished=utcnow().isoformat())

            # longer rest after each full cycle of all scripts
            gap = CYCLE_GAP_S if (job_i % len(jobs) == 0) else TICKET_GAP_S
            gap_end = time.time() + gap
            while time.time() < gap_end:
                if PAUSE.exists() or utcnow() >= ends:
                    break
                write_state(status="running", jobs_done=jobs_done)
                time.sleep(min(HEARTBEAT_EVERY_S, max(1, gap_end - time.time())))

        write_state(
            status="completed",
            jobs_done=jobs_done,
            finished_at=utcnow().isoformat(),
            message="marathon time window finished (time-only stop)",
        )
        log(f"COMPLETE jobs_done={jobs_done} (time budget)")
        return 0
    except Exception:
        log("FATAL " + traceback.format_exc())
        write_state(status="crashed", error=traceback.format_exc()[-2000:])
        return 1
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
