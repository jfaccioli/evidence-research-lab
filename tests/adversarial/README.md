# P1 adversarial suite (PR7)

Design proposal §11 required scenarios live in:

`test_p1_design_section11_matrix.py` (`test_s01` … `test_s18`)

| # | Scenario | Test |
|---|----------|------|
| 1 | Concurrent reservation one winner | `test_s01_*` |
| 2 | Crash/stale RESERVED → ABORTED_BURNED | `test_s02_*` |
| 3 | Reopen burned holdout fails | `test_s03_*` |
| 4 | Cohort member append after seal fails | `test_s04_*` |
| 5 | Holdout data without capability fails | `test_s05_*` |
| 6 | Child programme version does not reset N_global | `test_s06_*` |
| 7 | Ledger UPDATE/DELETE rejected | `test_s07_*` |
| 8 | Hash-chain tamper/gap detected | `test_s08_*` |
| 9 | Bundle run_id overwrite rejected | `test_s09_*` |
| 10 | Synthetic contamination blocked | `test_s10_*` |
| 11 | Budget/ledger atomic rollback | `test_s11_*` |
| 12 | Unanchored/no backup cannot promote | `test_s12_*` |
| 13 | Split warm-up / eligible_decision rules | `test_s13_*` |
| 14 | Unregistered sensitivity blocks promotion | `test_s14_*` |
| 15 | Citation does not double-count | `test_s15_*` |
| 16 | Legacy never COMPLETE without approved bound | `test_s16_*` |
| 17 | Snapshot uses backup API, no overwrite | `test_s17_*` |
| 18 | Sealed cohort mutation rejected; loader error burns | `test_s18_*` |

Additional files: holdout basics, ledger immutability, reconciliation smoke tests.
