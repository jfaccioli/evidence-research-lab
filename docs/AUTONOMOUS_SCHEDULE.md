# Autonomous schedule — modes B + C

**Updated:** 2026-08-01

## What you wanted

| Mode | Meaning |
|------|---------|
| **B** | Keep researching for up to **24 hours** (marathon) |
| **C** | Check **often** (every **1 hour**) that the marathon is still alive; restart if it crashed |

---

## How it works

```text
Hourly watchdog (launchd)
    │
    ├─ pause file? → stop
    ├─ marathon healthy? → OK
    ├─ marathon dead mid-window? → restart marathon
    └─ no marathon? → start 24h marathon

Marathon process
    │
    └─ runs research jobs in a loop until 24h ends (or pause)
```

---

## Install / reinstall

```bash
cd /Users/jimmyfaccioli/Desktop/crypto-research-lab
./scripts/install_macos_autonomous_schedule.sh
```

## Check status

```bash
cat research_kb/rd/MARATHON_STATE.json
cat research_kb/rd/WATCHDOG_STATUS.json
tail -20 logs/autonomous/marathon.log
tail -20 logs/autonomous/watchdog.log
```

## Pause everything

```bash
touch research_kb/rd/AUTONOMOUS_PAUSE
```

## Resume

```bash
rm -f research_kb/rd/AUTONOMOUS_PAUSE
./scripts/install_macos_autonomous_schedule.sh   # or wait for next hourly tick
```

## Safety

- No live trading  
- No paid APIs / secrets  
- Marathon max **24 hours** then stops (unless you set `CRL_MARATHON_AUTO_RESTART=1`)  
- Mac sleep: jobs resume when awake  

## Manual start marathon now

```bash
cd /Users/jimmyfaccioli/Desktop/crypto-research-lab
.venv/bin/python scripts/autonomous_watchdog.py
```
