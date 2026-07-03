# The cross-class boundary: a decision rule for bench builders

- Command: `uv run python scripts/boundary_experiment.py --seeds 500`
- Commit: `e3f69b6`
- Date: 2026-07-03 16:14:12 UTC
- Substrate: tau-bench retail DB in sqlite; one content resampler (prices x U(0.8,1.2), status flips for the target user); 500 seeds.

A **contaminated** adversary has perfectly memorized the shipped instance's answer artifact. We measure whether that memorization still PASSES after the exact same regeneration, under two scored targets:

- **Regime 2 (state-invariant target = the SQL query):** the leaked artifact is the gold query; the grader executes it against the regenerated rows.
- **Regime 3 (state-equivariant target = the answer value, replay oracle):** the leaked artifact is the shipped answer; the fresh oracle re-executes the reference on the regenerated rows.

| # | Question | shipped answer | R2 leaked-query pass | R3 leaked-answer pass | answer moved |
|---|---|---|---|---|---|
| 0 | What is the total price of the items in order #W2378156? | 1819.92 | **1.000** | **0.000** | 1.000 |
| 1 | How many delivered orders does Yusuf Rossi have? | 2 | **1.000** | **0.442** | 0.558 |
| 2 | What is the highest single-item price in order #W2378156? | 561.05 | **1.000** | **0.000** | 1.000 |

Means across 3 instances: leaked-query **1.000**, leaked-answer **0.147**.

## Reading

- **Regime 2 is the trap.** Leaked-query pass is **1.000**: regenerating the rows did nothing, because the correct SQL query is a fixed point of regeneration. Any benchmark whose scored artifact is a state-general program (text-to-SQL, competitive coding, a policy) inherits this — regeneration hardens the grader against wrong answers but buys ZERO contamination resistance. This is the common and costly mistake.
  - *Isn't R2 circular?* No — that is the vulnerability, stated precisely. A query that instead smuggled the memorized answer as a literal (`SELECT 1819.92`) would collapse to regime 3 and BE caught (a constant is state-equivariant-scored the moment it is compared to the fresh answer). What survives regeneration is exactly the state-GENERAL program. So the boundary runs inside text-to-SQL too: regeneration catches answer-smuggling leaks and misses the realistic query leak.
- **Regime 3 is the recommendation.** Leaked-answer pass collapses toward `1 - (answer moved)`: resistance is exactly the rate at which regeneration moves the scored target. The replay-derived (generative) oracle is what makes this regime free — the fresh answer is re-derived per seed with no re-annotation — which is the whole reason a generative oracle+golden *contributes* to contamination resistance rather than just costing more.
- **The boundary is scored-target equivariance, not the domain.** Same DB, same regenerator; the only difference between R2 and R3 is what gets scored. That is precondition 5, demonstrated.

## The decision rule

> Regenerating benchmark state defeats contamination **only if the scored target co-varies with the regenerated state** and the oracle is re-derived on that state (a replay/generative oracle makes this free). If the scored artifact is state-invariant (a program graded by execution), regeneration is cosmetic against a leak. Score the state, derive the golden by replay.

Cross-reference — the IN side, live: on tau-bench branch-selection the state-equivariant regime opens a **0.44-0.72** gap against the verbatim replayer A0 (`SOUNDNESS_AUDIT.md`, `DESIGN.md`), and a policy-following agent grounds on the regenerated world rather than its weights (`SHIPPED_ABLATION.md`). This receipt is the OUT side that makes it a boundary.
