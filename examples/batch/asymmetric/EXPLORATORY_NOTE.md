# Asymmetric capture v2 — exploratory (non-authoritative)

**Date:** 2026-07-27  
**Programme:** `docs/PROGRAMME_ASYMMETRIC_CAPTURE_V2.md`  
**Result:** **0/5 `passed_val`** (temp registry)

Dominant failures: `min_trades` (sparse insurance filters) and bootstrap CI lo &lt; 0 (for the one adequate-trade rule `mom_flat_extension`).

**Interpretation:** Non-SMA “cut left tail / keep right tail” formulations in this lock do not survive frozen gates. Aligns with prior asymmetric refutation — mechanism remains open only under *distinct* future operationalisations, not parameter clones.
