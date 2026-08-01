# Living research queue

**Updated:** 2026-08-01  
**Mode B+C:** **ON and started**

| Piece | Status |
|-------|--------|
| **B – 24h marathon** | **RUNNING** now (until ~24h from start) |
| **C – hourly watchdog** | **ON** (every 1 hour; restarts marathon if crashed) |
| Live trading | OFF |

## Check

```bash
cat research_kb/rd/MARATHON_STATE.json
cat research_kb/rd/WATCHDOG_STATUS.json
tail -20 logs/autonomous/marathon.log
```

## Pause

```bash
touch research_kb/rd/AUTONOMOUS_PAUSE
```

Docs: `docs/AUTONOMOUS_SCHEDULE.md`
