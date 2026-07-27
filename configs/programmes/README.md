# Programme config stubs (P1)

PR1 does **not** seal a real prospective programme for cutover.

- Live pipeline continues to use fractional splits from `configs/default.yaml`.
- Tests use **synthetic fixtures** constructed in Python, not production manifests.

## Active research programme designs

| File | Status |
|------|--------|
| `funding_btc_usdt_m_daily_v1.yaml` | **Designed + scaffolded** — PIT funding join + 10 pre-registered hyps under `examples/batch/funding/`. See `docs/PROGRAMME_FUNDING_PIT_V1.md`. Live fetch **not** authorized. Mock funding is for tests only, never promotion. |
