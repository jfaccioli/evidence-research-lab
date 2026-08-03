# Living research queue

**Updated:** 2026-08-03  
**Goal:** Autotrading that works **and** is scientifically supported (gates + shadow before live)

| System | Status |
|--------|--------|
| Marathon | **RUNNING** — **48 hours**, no job cap |
| Ends about | **2026-08-05 ~08:31 UTC** |
| Watchdog | Hourly health check / restart if crash |
| Ticket scripts | **14** (expanded) |
| Live trading | **OFF** until survivor + you |

## New jobs added this session

- mom + structure, breakout+vol/funding, mean-rev in trend, carry only when residual low  

## Check

```bash
cat research_kb/rd/MARATHON_STATE.json
tail -20 logs/autonomous/marathon.log
```
