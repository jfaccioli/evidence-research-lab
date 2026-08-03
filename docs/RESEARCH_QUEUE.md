# Living research queue

**Updated:** 2026-08-03  
**Marathon:** restarted with **expanded job catalog** (time-only 24h)

## New exploration scripts (better options)

| Script | Angle |
|--------|--------|
| `ms_funding_chg_v1` | Funding **change** (easing crowding), not level |
| `ms_btc_eth_rs_v1` | BTC vs ETH relative strength |
| `ms_vol_compress_break_v1` | Quiet vol → expansion breakout |
| `ms_dd_reentry_v1` | Re-enter after controlled drawdown |
| `ms_prem_fund_disagree_v1` | Premium vs funding disagreement |
| `ms_trend_quality_v2` | Trend stack not overextended |

First smoke run: all **REJECT** (some val teases → conf fail). Marathon will keep cycling them + older scripts.

## Check

```bash
cat research_kb/rd/MARATHON_STATE.json
tail -20 logs/autonomous/marathon.log
```
