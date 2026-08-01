#!/usr/bin/env python3
"""One autonomous research tick for launchd/cron.

Safety:
  - No live/paper/shadow
  - No reading .env secrets
  - Command allowlist only
  - Single-flight lock
  - Optional pause file
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "research_kb" / "rd" / "autonomous_queue.json"
PAUSE = ROOT / "research_kb" / "rd" / "AUTONOMOUS_PAUSE"
LOCK = ROOT / "logs" / "autonomous" / "tick.lock"
LOG_DIR = ROOT / "logs" / "autonomous"
STATUS = ROOT / "research_kb" / "rd" / "AUTONOMOUS_TICK_STATUS.json"
DEFAULT_MAX_MIN = 45

# Only these prefixes may run
ALLOW_PREFIXES = (
    "python scripts/run_autonomous_ticket_",
    "python scripts/run_ms_",
    ".venv/bin/python scripts/run_autonomous_ticket_",
    ".venv/bin/python scripts/run_ms_",
    "python -m crl run-programme examples/batch/",
    ".venv/bin/python -m crl run-programme examples/batch/",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(msg: str, fp) -> None:
    line = f"[{utc_now()}] {msg}"
    print(line, flush=True)
    fp.write(line + "\n")
    fp.flush()


def allowed(cmd: str) -> bool:
    c = " ".join(cmd.split())
    return any(c.startswith(p) or c.startswith(p.replace("python ", str(ROOT / ".venv/bin/python") + " ")) for p in ALLOW_PREFIXES) or any(
        c.startswith(p) for p in ALLOW_PREFIXES
    )


def load_queue() -> dict:
    if not QUEUE.exists():
        return {"version": 1, "tickets": []}
    return json.loads(QUEUE.read_text())


def save_queue(q: dict) -> None:
    q["updated_at"] = utc_now()[:10]
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps(q, indent=2) + "\n")


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "latest.log"
    stamp_log = LOG_DIR / f"tick_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log"

    with open(log_path, "a", encoding="utf-8") as fp, open(stamp_log, "a", encoding="utf-8") as fp2:

        def both(msg: str) -> None:
            log(msg, fp)
            fp2.write(f"[{utc_now()}] {msg}\n")
            fp2.flush()

        if PAUSE.exists():
            both("PAUSE file present — exiting")
            STATUS.write_text(
                json.dumps({"status": "paused", "at": utc_now()}, indent=2) + "\n"
            )
            return 0

        # lock
        if LOCK.exists():
            try:
                age = time.time() - LOCK.stat().st_mtime
                if age < DEFAULT_MAX_MIN * 60 + 120:
                    both(f"Lock held (age {age:.0f}s) — skip")
                    return 0
                both("Stale lock — removing")
                LOCK.unlink(missing_ok=True)
            except OSError:
                pass
        LOCK.write_text(utc_now() + "\n")

        try:
            q = load_queue()
            pending = [t for t in q.get("tickets") or [] if t.get("status") == "pending"]
            if not pending:
                both("No pending tickets")
                STATUS.write_text(
                    json.dumps(
                        {"status": "idle", "at": utc_now(), "message": "queue empty"},
                        indent=2,
                    )
                    + "\n"
                )
                return 0

            ticket = pending[0]
            tid = ticket["id"]
            cmd = ticket["cmd"].strip()
            # Prefer venv python
            if cmd.startswith("python "):
                vpy = ROOT / ".venv" / "bin" / "python"
                if vpy.exists():
                    cmd = str(vpy) + " " + cmd[len("python ") :]

            if not allowed(ticket["cmd"].strip()) and not allowed(cmd):
                both(f"REFUSED non-allowlisted cmd: {ticket['cmd']}")
                ticket["status"] = "blocked"
                ticket["error"] = "command not on allowlist"
                save_queue(q)
                return 2

            max_min = int(ticket.get("max_minutes") or DEFAULT_MAX_MIN)
            both(f"START ticket={tid} max_min={max_min} cmd={cmd}")
            ticket["status"] = "running"
            ticket["started_at"] = utc_now()
            save_queue(q)

            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT / "src") + (
                os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
            )
            env["CRL_AUTONOMOUS_TICK"] = "1"
            # Do not pass secrets; strip common ones if present
            for k in list(env):
                if any(s in k.upper() for s in ("KEY", "SECRET", "TOKEN", "PASSWORD", "API")):
                    if k in ("PYTHONPATH", "PATH", "HOME", "USER", "LANG"):
                        continue
                    # keep PATH etc; drop credential-like
                    if k not in ("PATH", "HOME", "USER", "SHELL", "TMPDIR"):
                        if any(
                            x in k.upper()
                            for x in (
                                "API_KEY",
                                "SECRET",
                                "PASSWORD",
                                "PRIVATE",
                                "BINANCE",
                                "EXCHANGE",
                            )
                        ):
                            env.pop(k, None)

            try:
                proc = subprocess.run(
                    shlex.split(cmd),
                    cwd=str(ROOT),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=max_min * 60,
                )
                out = (proc.stdout or "")[-8000:]
                err = (proc.stderr or "")[-4000:]
                both(f"EXIT code={proc.returncode}")
                if out:
                    both("stdout_tail:\n" + out[-2000:])
                if err:
                    both("stderr_tail:\n" + err[-1500:])
                ticket["status"] = "done" if proc.returncode == 0 else "failed"
                ticket["exit_code"] = proc.returncode
                ticket["finished_at"] = utc_now()
                ticket["log"] = str(stamp_log.relative_to(ROOT))
            except subprocess.TimeoutExpired:
                both("TIMEOUT")
                ticket["status"] = "timeout"
                ticket["finished_at"] = utc_now()
            except Exception as e:
                both(f"ERROR {e}")
                ticket["status"] = "failed"
                ticket["error"] = str(e)
                ticket["finished_at"] = utc_now()

            save_queue(q)
            STATUS.write_text(
                json.dumps(
                    {
                        "status": ticket["status"],
                        "ticket_id": tid,
                        "at": utc_now(),
                        "log": str(stamp_log),
                    },
                    indent=2,
                )
                + "\n"
            )
            both(f"DONE ticket={tid} status={ticket['status']}")
            return 0 if ticket["status"] == "done" else 1
        finally:
            LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
