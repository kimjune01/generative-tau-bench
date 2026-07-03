# Soundness Audit Receipt

- Command: `uv run python scripts/audit_soundness.py --domain all --seeds 25 --branch-seeds 300 --workers 6`
- Commit: `669e97b`
- Date: 2026-07-03 05:07:27 UTC
- Wall time: 672.4 s (6 workers)

## Re-key audit

| Domain | Instances | Injective | Coverage | Deterministic | Faithful | Solvable (no new errors) | Clean replay (zero errors) | Invalid |
|---|---|---|---|---|---|---|---|---|
| retail | 2875 | 2875 | 2875 | 2875 | 2875 | 2875 | 2400 | 0 |
| airline | 1250 | 1250 | 1250 | 1250 | 1250 | 1250 | 1250 | 0 |
| **total** | 4125 | 4125 | 4125 | 4125 | 4125 | 4125 | 3650 | 0 |

Coverage checks the DB, the golden's arguments, the instruction, and the outputs.
Determinism regenerates each (task, seed) twice and compares mapping and oracle hash.
Clean replay < Solvable is expected: some shipped base goldens carry benign
exploratory-read tool errors, which faithfulness requires the re-keyed golden to
reproduce position-for-position (see tests/test_rekey_invariance.py).

## Branch-selection audit

### Spec `retail:0`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | fallback 138 (46.0%) / primary 162 (54.0%) |
| Invalid | 0 |

### Spec `retail:1`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | fallback 144 (48.0%) / primary 156 (52.0%) |
| Invalid | 0 |

### Spec `retail:6`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 1569765161 97 (32.3%) / 7453605304 109 (36.3%) / 9190635437 94 (31.3%) |
| Invalid | 0 |

### Spec `retail:7`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 1569765161 115 (38.3%) / 7453605304 97 (32.3%) / 9190635437 88 (29.3%) |
| Invalid | 0 |

### Spec `retail:8`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 1270145486 104 (34.7%) / 7624783998 100 (33.3%) / 9083642334 96 (32.0%) |
| Invalid | 0 |

### Spec `retail:9`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 1270145486 98 (32.7%) / 7624783998 107 (35.7%) / 9083642334 95 (31.7%) |
| Invalid | 0 |

### Spec `retail:41`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 1096508426 78 (26.0%) / 4068787148 81 (27.0%) / 4772738468 70 (23.3%) / 9665100170 71 (23.7%) |
| Invalid | 0 |

### Spec `retail:42`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 1096508426 79 (26.3%) / 4068787148 70 (23.3%) / 4772738468 66 (22.0%) / 9665100170 85 (28.3%) |
| Invalid | 0 |

### Spec `retail:44`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 1569765161 103 (34.3%) / 5320792178 106 (35.3%) / 7453605304 91 (30.3%) |
| Invalid | 0 |

### Spec `retail:79`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | fallback 151 (50.3%) / primary 149 (49.7%) |
| Invalid | 0 |

### Spec `retail:97`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 2652637226 97 (32.3%) / 5967152432 104 (34.7%) / 9440686670 99 (33.0%) |
| Invalid | 0 |

### Spec `retail:98`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 2652637226 102 (34.0%) / 5967152432 92 (30.7%) / 9440686670 106 (35.3%) |
| Invalid | 0 |

### Spec `retail:107`

| Check | Result |
|---|---|
| Instances | 300 |
| Solvable (zero tool errors) | 300/300 |
| All expected branches fire | pass |
| Per-branch oracle determinism | pass (one end-state per branch) |
| Distinct end-states across branches | pass |
| Branch split | 2060066974 157 (52.3%) / 8124970213 143 (47.7%) |
| Invalid | 0 |

## Overall

- Total instances audited: 8025 (4125 re-keyed + 3900 branch-selected)
- Invalid instances: 0
- Invalid-instance rate: 0.0000% (0/8025)
