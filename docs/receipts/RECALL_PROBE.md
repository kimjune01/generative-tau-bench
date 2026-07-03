# Recall probe: is τ-bench task 0 in model weights?

2026-07-02. GSM1k measured a model's propensity to *regenerate* benchmark text and
correlated it with score inflation; this is that probe for τ-bench retail task 0,
run against the two CLI agents used elsewhere in this repo. Prompt (identical to
both, modulo the no-file-access phrasing codex needs):

> From memory only (no tools, no web): tau-bench is Sierra's 2024 tool-agent
> benchmark. In its retail domain test set, task 0 involves the user Yusuf Rossi
> (zip 19122). What does his instruction ask for, and what is the golden action
> sequence (tool names + arguments, including item ids)? If you don't know, say so
> plainly rather than guessing.

## claude (Claude Code CLI, default model): digit-perfect recall

Recited the instruction near-verbatim (keyboard exchange, thermostat
Google-Home swap, the clicky/RGB/full-size conditional with no-backlight
fallback) and produced, while explicitly disclaiming digit-level confidence
("ten-digit IDs are exactly where I'd confabulate"), the following ids — every
one of which matches `tau_bench/envs/retail/tasks_test.py` exactly:

| Recalled | Shipped golden | Match |
|---|---|---|
| `#W2378156` (order) | `#W2378156` | yes |
| `1151293680` (old keyboard) | `1151293680` | yes |
| `4983901480` (old thermostat) | `4983901480` | yes |
| `7706410293` (new keyboard, fallback) | `7706410293` | yes |
| `7747408585` (new thermostat) | `7747408585` | yes |
| `credit_card_9513926` (payment) | `credit_card_9513926` | yes |

One structural error: it claimed goldens annotate only DB-writing calls; the
shipped action list includes the four reads. The substance — the write action
and all its arguments — is verbatim.

## composer-2.5 (Cursor CLI, `cursor-agent --model composer-2.5`): declines

Added 2026-07-03. Same prompt. Declined cleanly: "I don't know those specifics from
memory… I do not have a reliable recall of retail test set task 0, Yusuf Rossi, his
instruction, or the golden action sequence." Correct on paper-level facts (Sierra,
2024, retail domain, golden tool-call trajectories), dark on every instance-level
detail — the same fade-not-cliff shape as codex. So Composer is **uncontaminated on
task 0** (or trained not to recite it): it sits in codex's bucket, not claude's.
Consequence for the weaker-model question (see SHIPPED_ABLATION.md): Composer cannot
test "does a weaker model *refuse* to use memory," because it has no task-0 memory to
refuse. Weaker ≠ contaminated; contamination tracks broad benchmark-file scraping,
which a Cursor-trained model largely escapes.

## codex (OpenAI Codex CLI, gpt-5.5): declines

"I don't know the exact instruction or golden action sequence for tau-bench
retail task 0 from memory, including the item IDs."

Two follow-up probes distinguish refusal (a cliff at the "benchmark internals"
boundary) from absence (a fade with specificity):

- *Graded probe*: fluent and correct on paper-level facts (`pass^k`, the
  retail/airline domains, final-state grading) — so no policy wall around
  discussing tau-bench — but "unknown" for any retail user name.
- *Completion probe*: handed the first half of task 0's instruction verbatim and
  asked to continue (completion framing, which does not pattern-match to "recite
  a benchmark answer"), it replied "no continuation in memory" rather than
  continuing or improvising.

The gradient is a fade that goes dark exactly where `tasks_test.py` content
begins, consistent with genuine instance-level absence — plausibly deliberate
training-data decontamination (labs filter benchmark instance files; secondary
discussion of the paper survives such filters, which matches the observed
knowledge boundary). Black-box caveat: absence of recall is still not absence in
weights; the completion probe is the strongest available negative short of
logprob access.

Cross-model prediction this licensed (falsifiable, cheap): under free
observation both models should read flat on the branch meter; under observation
ablation (`--block get_product_details`), claude can still pass shipped-branch
worlds from weights, while gpt-5.5, lacking the digits, must fail or ask on all
worlds.

**Outcome (2026-07-03): the claude half of this prediction was tested and refuted.**
Run on the *shipped* world (identity, where the memorized golden is exactly correct;
`SHIPPED_ABLATION.md`), claude scored 0.667 with observation and **0.000** with
`get_product_details` blocked — it retries the outage and tells the user it cannot
confirm the variant, never plugging in the `7706410293` it recites digit-perfect. It
does **not** substitute weights for a blocked observation; it grounds on the tool
(the retail policy requires confirming the target variant, and claude follows the
policy over its priors). So contamination is present *and behaviorally inert even
when the memory is correct* — a stronger result than the prediction, and it means the
codex ablation-produces-shipped-ids escape hatch is moot for this agent.

## Why this matters here

Recall and behavioral reliance are different quantities, and the branch-selection
meter reads only the second. This probe establishes the first is *present* for
claude, digit-perfect, fallback target included — the exact path the flipped-branch
worlds punish. Yet in the live mediated episode on a flipped world (seed 1,
`docs/receipts/live_task0_claude_12seeds.log`), the same model read the resampled
catalog and exchanged to `9025753381`, the branch its weights have never seen.
Weights said `7706410293`; the world said otherwise; the model followed the world.

So the strongest current statement is: contamination of the weights is proven,
and (n small) it does not govern behavior in the dialogue loop for this model on
this task. That makes the meter's live readings meaningful in both directions —
a flat profile is a real "memory present but inert" finding, not a "nothing to
remember" vacuity, and any future split is attributable to memory known to exist.
Caveat: absence of the golden in the *sampled* recall is not absence in weights
(one sample, one prompt); and digit-perfect recall under a disclaimer shows
self-reported confidence is not a contamination defense.
