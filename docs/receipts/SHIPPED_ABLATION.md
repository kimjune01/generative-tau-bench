# Shipped-world ablation: the discriminating positive control

- Commands (below, per cell)
- Commit: `e3f69b6`
- Date: 2026-07-03 15:41 UTC
- Agent: claude (Claude Code CLI, default model), mediated by the CLI user-sim

The seeded ablation (`live_task0_claude_12seeds_ablated.log`) blocks observation on
*regenerated* worlds, where the memorized golden is **wrong** for the resampled
catalog. So a 0.000 there conflates two causes — the model can't observe, *and* its
memory doesn't fit the world — and cannot isolate reliance-on-weights.

This receipt runs the ablation on the **shipped** task 0 (`--shipped`: identity, no
regeneration), where the memorized golden is **exactly correct** — the ids claude
recites digit-perfect in `RECALL_PROBE.md` (`7706410293`, `credit_card_9513926`, …)
are the ground truth. The only manipulated variable is the observation channel.

## The 2×2 (task 0, 6 trials, mediated user-sim)

| claude, shipped task 0 | pass@1 | pass^6 |
|---|---|---|
| **observe** (catalog readable) | **0.667** (4/6) | 0.000 |
| **block** `get_product_details` | **0.000** (0/6) | 0.000 |

```
# observe
python scripts/run_eval.py --agent claude --user-sim claude --task 0 --trials 6 --shipped --max-steps 20
# block
python scripts/run_eval.py --agent claude --user-sim claude --task 0 --trials 6 --shipped --max-steps 20 --block get_product_details
```

Logs: `live_task0_claude_shipped_observe.log`, `live_task0_claude_shipped_ablated.log`.

## The finding: memory is inert even when it is correct

Claude passes the shipped world when it can read the catalog and fails **uniformly**
when it cannot — *on the same world, holding the answer in weights.* The verbose
transcript (`scratchpad`, one representative block trial) shows why: claude verifies
identity, pulls the order via `get_order_details` (unblocked), correctly names the
current keyboard variant, then calls `get_product_details` to find the **target**
variant's item id, hits the outage, **retries four times**, and finally tells the
user the catalog is unavailable and it cannot confirm the variant. It never plugs in
the `7706410293` it demonstrably knows. It treats the block as a real outage and
**grounds on the tool rather than substituting memory.**

This *refutes* the prediction logged in `RECALL_PROBE.md` ("under observation
ablation, claude can still pass shipped-branch worlds from weights"). The truth is
stronger for the thesis: contamination of the weights is proven present (RECALL_PROBE)
yet behaviorally **inert in both directions** —

- on regenerated worlds, memory is *wrong* → claude follows the world
  (`live_task0_claude_12seeds.log`, 0.917);
- on the shipped world under ablation, memory is *right but unobserved* → claude
  refuses to act on it (0.000, this receipt).

So for this model on this task, the memorization channel does not drive behavior in
the agentic loop. The behavioral meter's readings are meaningful: a flat branch
profile is "memory present but inert," not "nothing to remember."

## Scope and the honest limit

This is a disposition of *this* agent (grounding discipline), not a proof that no
agent can shortcut through memory. A less scrupulous policy, or the fine-tuned
**A2** adversary (train on the public generator's outputs; see DESIGN.md), could plug
memorized ids and would defeat this control. The shipped ablation therefore bounds
**A0/A1** behavioral reliance for a well-behaved agent; it does not discharge A2,
which the CLI-agent choice still forecloses.

## Weaker-model attempt: composer-2.5 (Cursor CLI) — a confound, not a test

To ask whether the refusal generalizes to a lighter model, we wired the Cursor CLI in
as an agent adapter (`gtau/adapters/cli_agent.py:cursor_adapter`,
`cursor-agent -p --trust --mode ask --model composer-2.5`) and ran the shipped+block
cell with the **same claude user-sim** (only the agent-under-test changes).

Composer-2.5 also failed (0.000) and also did **not** fabricate: it retried the
blocked lookup, then called `transfer_to_human_agents` rather than inventing item ids.
Grounding discipline in a lighter model — it won't hallucinate state it can't read.

But this is **not** the memory-refusal test, because a recall probe (RECALL_PROBE.md)
shows Composer *declines* task 0 from memory — it's uncontaminated, in codex's bucket.
Its shipped+block failure is "no memory + can't observe → escalate," not claude's
"has the correct memory but won't use it." The claude finding stands alone as the
genuine refusal; Composer is a clean second SUT (won't confabulate), not a second
instance of the refusal. **Weaker ≠ contaminated:** the leak tracks broad
benchmark-file scraping, which correlates with frontier scale, not with weakness.

To actually test the generalization we'd need a *lighter-and-contaminated* model —
one that recites task 0 yet is weaker than Opus 4.8. That candidate is not yet
identified.

## Codex cell: not re-run

The codex half of the 2×2 (the model that *lacks* the digits — RECALL_PROBE shows it
declines recall and fades to "unknown" exactly where `tasks_test.py` content begins)
was not re-run here (codex CLI drift; see `docs/WORKLOG.md`). The codex negative is
already on file — `live_task0_codex_12seeds_ablated.log` (0.000 across 12 seeded
worlds) plus the three RECALL_PROBE probes — so re-running it is confirmatory, not
load-bearing.
