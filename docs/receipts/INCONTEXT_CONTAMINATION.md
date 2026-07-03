# In-context contamination: a real learner under two leak regimes

- Command: `python scripts/incontext_contamination.py --agent claude --regen-seeds 12`
- Commit: `e3f69b6`
- Date: 2026-07-03 16:39:47 UTC
- Agent: claude (one call per condition)
- Substrate: retail DB; 12 regenerated worlds; model sees NO rows.
- Method note: model calls run from an isolated empty cwd outside the repo, because the CLI agents have filesystem access and would otherwise read the real data. answer-ctrl=0.00 confirms the sandbox holds (an answer is unknowable without the rows). See `docs/WORKLOG.md` for the invalid first pass this guards against.

Pass rate = fraction correct against the replay-derived oracle. `ship` = shipped world, `regen` = mean over regenerated worlds. The model's output is fixed (it never observes a world), so `ship`->`regen` movement is regeneration acting on a *contaminated* learner.

| id | set | answer-leak ship/regen | query-leak ship/regen | answer-ctrl ship/regen | query-ctrl ship/regen |
|---|---|---|---|---|---|
| p0 | primed | 1.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| p1 | primed | 1.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| p2 | primed | 1.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| p3 | primed | 1.00 / 0.42 | 1.00 / 1.00 | 0.00 / 0.00 | 1.00 / 1.00 |
| p4 | primed | 1.00 / 0.58 | 1.00 / 1.00 | 0.00 / 0.00 | 1.00 / 1.00 |
| h0 | held-out | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| h1 | held-out | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| h2 | held-out | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 1.00 / 1.00 |

Means: answer-leak ship=0.62 regen=0.12; query-leak ship=1.00 regen=1.00; answer-ctrl ship=0.00 regen=0.00; query-ctrl ship=0.38 regen=0.38

## Reading

- **answer-leak: high on shipped, collapses on regen.** The in-context leak reproduces the shipped answer (contamination works on the static bench), and regeneration invalidates it — the memorized value is now stale. A real learner, not a scripted A0, and it still goes stale, because the fresh answer is a function of a world the model never saw.
- **query-leak: high on both, including held-out.** The leaked queries let the model emit correct SQL, which the grader executes on the fresh rows. Regeneration is cosmetic. On HELD-OUT questions it still scores high: the model **generalized the method** from the primed queries. This is precisely the critic's 'training learns the skill' scenario — and it confirms the boundary rather than breaking it: a learned state-general method is exactly what regeneration cannot dislodge.
- **controls localize the cause, and show the leak conveys real method.** query-ctrl is *mixed*: high on the count questions (the `COUNT ... WHERE status='delivered'` mapping is guessable from the schema) but **zero on the price-aggregation questions** — without the examples the model did not map 'total/highest price' to `SUM/MAX(price)` over `order_items`. So query-leak (1.00) beating query-ctrl (0.38) means the leak conveyed genuine, transferable method knowledge. The invariant that matters holds regardless of source: every query cell is FLAT ship→regen, because a state-general query is correct on any world. answer-ctrl is 0.00 (an answer is unknowable without observing the rows — this also confirms the sandbox: the model could not read the shipped file). Resistance lives exactly where observation is required to score, i.e. where the target co-varies with the regenerated state.

## Why this answers 'you didn't train two models'

The asymmetry is training-proof. No contamination — in-context here, or weight training in the full A2 — can supply the answer to a freshly regenerated instance, because that answer is determined by state the model has not observed. Training can only teach the state-general METHOD, which helps on the query target (where regeneration was already cosmetic) and cannot help on the answer target (where the value is unknowable a priori). So a weight-trained A2 moves the query cells to where they already are and leaves the answer cells where they already are. The remaining honest gap is empirical confirmation with an actual fine-tune (CoinRun-style held-out families; see DESIGN.md); this establishes the mechanism with a real, generalizing learner.
