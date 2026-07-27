# Programme config stubs (P1)

PR1 does **not** seal a real prospective programme for cutover.

- Live pipeline continues to use fractional splits from `configs/default.yaml`.
- Tests use **synthetic fixtures** constructed in Python, not production manifests.

## Active research programme designs

| File | Status |
|------|--------|
| `funding_btc_usdt_m_daily_v1.yaml` | **Exploratory null** — PIT funding join + 10 hyps under `examples/batch/funding/`. See `docs/PROGRAMME_FUNDING_PIT_V1.md`. Do not re-mine daily thresholds. |
| `oi_btc_usdt_m_daily_v1.yaml` | **Designed + scaffolded** — PIT OI join + 10 pre-registered hyps under `examples/batch/oi/`. See `docs/PROGRAMME_OI_PIT_V1.md`. Live fetch **not** authorized. Mock OI is for tests only, never promotion. |
| `funding_btc_usdt_m_4h_power_v1.yaml` | **Null 0/6** — power study; ample trades still fail gates. |
