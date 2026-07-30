# Living research queue (Research Director)

**Updated:** 2026-07-30  
**Active initiative:** **Economic Inefficiency Programme V1**  
**Suspended:** Immediate deployable-strategy search from free shelf  

## Objective

Identify **economically plausible reasons** BTC might be temporarily predictable,  
and the **smallest additional information** needed to test them.

## Top inefficiency

| Rank | ID | Status |
|------|-----|--------|
| **1** | Spot BTC **ETF create/redeem** | **EIR issued** — free delayed flow data required |
| 2 | Options dealer hedging | Deferred (data cost) after ETF |
| 3 | Forced liquidations | Low priority (overlap with conf-null free series) |
| 4 | Stablecoin mint/burn transmission | Data gap (stock have; creation missing) |

## Human / next action

See **`docs/EVIDENCE_INVESTMENT_REVIEW_INEFFICIENCY_2026-07-30.md`**:

- Prefer **free delayed** aggregate US spot BTC ETF net flows + PIT lag  
- **Do not pay** for vendor API until free path fails  
- Open Alpha Discovery programme only after series is pinned  

## Commands

```bash
python -m crl rd inefficiencies
python -m crl rd eir
python -m crl rd status
python -m crl rd sync
```

## Gates

Unchanged. Platform ≠ alpha. No LIVE without confirmatory + dual flags.
