# Generative τ-bench

A seeded, replay-oracle extension of τ-bench for contamination-resistant,
statistically honest tool-agent evaluation. Design note and paper plan.

## Thesis

τ-bench grades an agent by replaying a golden action sequence on a synthetic
database and hashing the final state. That oracle is *operational*: it is computed
by running a program, not by reading a stored answer. Anything computed by replay
can be recomputed under a transformation of its inputs. So the goldens do not have
to be static. Publish a seeded generator that emits the database, the golden
program, and (by replay) the oracle, and you get fresh instances on demand from an
open, auditable source. The contamination fix is regeneration, not secrecy.

That single move also fixes two unrelated τ-bench weaknesses: a test set too small
to carry error bars, and a hand-authored task set too narrow to control difficulty.
One change, three problems.

## Why now: what τ-bench gets right, and what ages badly

τ-bench's core is exemplary and we keep it. Grading is deterministic and
non-LLM-judged: `calculate_reward` in `tau_bench/envs/base.py` hashes the mutated
DB, reloads a clean DB, replays the task's `actions`, hashes that, and compares.
No judge model touches the outcome, which is why its reliability metric `pass^k`
(all k i.i.d. trials succeed, `run.py`) means anything.

Three things age badly, and all three are consequences of the instances being
*static*, not of the design being wrong:

1. **Contamination accrues with age.** The goldens ship in cleartext in
   `tasks_test.py`. At release (June 2024) the synthetic data was in no training
   corpus, so contamination was near zero by construction. It grows monotonically
   as the public repo ages into successive training cutoffs. The leak is a function
   of the repo's age, not its design. Compare the SWE-bench arc: SWE-bench Verified
   filtered out 68.3% of samples for quality, and OpenAI later retired it after
   finding 59.4% of a persistently-failed subset were broken or contaminated.
   Static open benchmarks decay.
2. **Too small for error bars.** 115 retail + 50 airline test tasks, with
   `pass^k` reported as a point and no CIs. `pass^8` at the frontier rides on a
   near-binary per-task estimator over ~50 tasks.
3. **Narrow and hand-authored.** Difficulty and coverage are not controlled; the
   suite contains near-duplicate tasks. τ²-bench's compositional generator is the
   authors' own acknowledgment of this gap.

## The design

A task is a *class* plus a *seed*. The class fixes the intent, the policy branch,
and the relational shape. The seed instantiates it into a concrete world.

```
(class, seed) --generator--> (DB instance, golden action program, derived oracle)
```

### 1. Regeneration by replay

The generator emits a synthetic DB and a golden action program over it. The oracle
is not stored: it is the hash of the DB state after replaying the golden program,
exactly as τ-bench already computes ground truth. To produce a fresh instance of a
class, re-key every entity id through a seeded bijection and resample values, then
apply the *same* map to the golden program's arguments and to the user-simulator
instruction. The oracle recomputes itself for free. Required output strings stop
being hand-annotated and become *derived* from the replayed final state.

Two levels, with a real cost boundary between them:

- **Cosmetic re-keying** (bijection over ids, resampled labels) is free and defeats
  *verbatim* memorization. Ship it first.
- **Structural regeneration** (resample the contents, not just relabel) defeats
  *pattern* memorization but can silently break tasks: randomize the catalog and a
  conditional preference may resolve down a different branch, or a required product
  variant may cease to exist; randomize order status and a "cancel pending order"
  task lands on a delivered order. So the generator must be *constraint-aware*: pin
  the predicates the task depends on, randomize everything else. That constraint
  set is the work, and it is what a class *is*.

### 2. Width in the number of classes, homogeneity within a class

Surface entropy (seed count) is nearly free and only defeats instance memorization.
Semantic width (distinct shapes, policy branches, compositional depths) is what
resists distribution overfit, and it is authored, not sampled. Put the width across
classes and keep each class internally homogeneous. Then per-class averages of a
handful of samples stay meaningful, and paired comparison stays clean. Target
*shortcut-foreclosing* width: wide enough that no non-skill shortcut survives, no
wider, since past that point width only adds variance and authoring cost.

### 3. Seed protocol: reveal at eval time, split train/test

Determinism alone does not decontaminate. If the generator and the evaluation seeds
are both public, the instances are regenerable and thus trainable-on. Freshness
comes from *when the seed is revealed*. Run it as a daily-challenge: publish the
generator (auditable), fix a seed per reported run (reproducible), and draw the
reported seeds so no training run could have front-run them (rotate per round, hold
a private range, or commit to a future public beacon). Report an in-distribution
(train-seed) versus held-out (test-seed) split; the gap is a built-in memorization
meter, the ProcGen protocol ported to tool agents.

### 4. Paired cross-model evaluation

Run every model in a round on the *same* seed set. Scores become positively
correlated across models (all face the same instances), so instance-difficulty
variance cancels in the difference and model-vs-model comparison tightens. This is
common random numbers; for the binary outcome the matching test is McNemar. Report
paired intervals, not just marginal ones. Note the pairing is at the instance level,
not the decoding level, which is where most of the variance-reduction gain sits.

### 5. Equivalence, not exact hash

Exact full-DB hashing is brittle when several valid end-states exist: a benign extra
write or a different-but-valid choice fails. Under regeneration this problem
multiplies across instances. Replace bare hash-equality with a canonicalization or
an explicit equivalence relation over states (ignore incidental fields, canonicalize
orderings) before hashing. This is the same task-quality risk τ-bench already has,
promoted to a first-class requirement because the generator must guarantee it across
its whole output distribution, not per hand-checked instance.

## Novelty: honest position

Every component exists. The contribution is the synthesis and the receipts, not a
new primitive, and the paper is only real if it is built and measured.

| Component | Prior art | Novelty |
|---|---|---|
| Replay-and-hash oracle | τ-bench | none, we keep it |
| Regenerate not hide | GSM-Symbolic, GSM-SEM, LiveBench, LiveCodeBench, AntiLeakBench | low; underdeveloped for relational tool worlds |
| Seeded procedural instances | ProcGen, ProcTHOR, Avalon | none in RL, derivative for agents |
| Train/test seed split | ProcGen | none, good to include |
| Shared-seed paired eval | common random numbers, McNemar, PaCoST | none statistically, underused in agent benchmarks |
| Replay oracle + seeded regeneration for stateful tool-agent DBs | τ²-bench is nearest | medium; no exact prior instance found |

The defensible claim, to our knowledge: *no published LLM agent benchmark uses a
public seeded generator to regenerate both a stateful tool-world instance and its
replay-derived oracle, enabling fresh contamination-resistant evaluation without
hidden goldens.* Keep "to our knowledge" until a deeper sweep is done.

### The delta versus τ²-bench, which is where novelty lives or dies

τ²-bench (`2506.07982`) already has a compositional generator built from atomic
init/solution/assert functions. Our differentiation is narrow and must be stated
precisely: (1) derive the oracle by *replaying the solution program* on the
generated DB rather than maintaining separate hand-written assertion functions, so
oracle maintenance drops toward zero; (2) make *seeded regeneration with
reveal-at-eval-time* the primary contamination protocol, not just a task-authoring
convenience; (3) make *paired CRN reporting* standard. Open task, blocking the
novelty claim: read τ²-bench's actual oracle and generation code and confirm it does
not already do (1). If it does, the delta collapses to (2) and (3), which are
protocol contributions, not mechanism.

Most likely to scoop this: the τ-bench / τ² authors, who own the franchise and have
the generator direction already.

## Evaluation plan (the bar the paper must clear)

1. **Invariance.** Show id re-keying preserves task semantics: for N classes, the
   re-keyed golden replays to the re-keyed expected state, and agent success is
   invariant to the seed under a fixed model, within sampling error.
2. **Solvability guarantee.** Show the generator emits only solvable,
   policy-consistent tasks across its whole output distribution (the generative
   analog of the SWE-bench Verified solvability filter). Report any invalid-instance
   rate and drive it to zero.
3. **Contamination sensitivity.** Fine-tune or few-shot a model on train-seed
   goldens, then show high train-seed accuracy and lower held-out-seed accuracy. If
   the gap is null, the memorization meter is only asserted.
4. **Paired statistics.** Same seeds across models; report paired CIs and McNemar,
   and quantify variance reduction versus independent-seed sampling.
5. **Generator audit.** Ablate suspected shortcuts (break a tell, watch for
   collapse) to separate seed memorization, generator-distribution overfit, and
   genuine competence.
6. **Reliability curves with bars.** Report `pass^k` with CIs, stratified by
   difficulty class, which the generator now controls by construction.

## Risks and honest limits

- **Authoring cost is the real labor.** Regeneration saves per-instance annotation,
  not per-class design. Width equals authored classes. LLM-authoring classes to
  scale reintroduces the solvability audit on machine-made templates.
- **User-simulator noise is orthogonal and unfixed here.** The reward's validity
  still depends on an LLM user simulator conveying intent faithfully. Regeneration
  cleans the grading-side leak, not the input-side noise. "No contamination" is
  earned; "all rigor" needs a tightened or verified user sim too.
- **Distribution overfit persists.** Regeneration kills instance memorization, not
  overfitting to a narrow generator. ProcGen shows this empirically. Mitigate with
  width, held-out task families, and seed rotation.
- **The novelty negative is a search result, not a proof.** Re-run the sweep before
  submission.

## Scope and milestones

- **MVP (proof of the load-bearing claim).** One retail class from `tasks_test.py`
  (e.g. an exchange-with-conditional-fallback). Implement seeded re-keying over the
  DB and golden, replay through the existing `calculate_reward`, and show the oracle
  validates against the re-keyed state. ~40 lines given the grader already replays.
- **Contamination receipt.** One model, train-seed vs held-out-seed gap on that
  class.
- **Scale-out.** Convert a family of retail classes to constraint-aware generators;
  add the equivalence-relation oracle; add paired reporting across 3+ models.
- **Paper.** Target a datasets-and-benchmarks track. Framing: the working generator
  plus the contamination and memorization receipts are the contribution; the
  primitives are borrowed and cited as such.

## Licensing (checked 2026-07-01)

τ-bench is MIT (Copyright 2024 Sierra), covering code and data under one license.
MIT explicitly permits modification, distribution, sublicensing, and derivative
works; the only obligation is to retain the copyright and permission notice in any
redistributed portions. The data readme adds an explicit "feel free to use some of
the data for other purposes." So this derivative is clear to build and publish. We
keep Sierra's MIT notice, relicense our additions as MIT with a NOTICE crediting
Sierra, and cite the paper as academic norm.

Note: that data readme also describes Sierra's own one-time procedural generation of
the base data (schema design, programmatic plus GPT-generated fields, code-based
composition). We cite it as prior art. Our delta is turning that one-time authoring
step into per-instance seeded regeneration bound to the replay oracle.

Open checks before reuse beyond the base repo: (a) τ²-bench's license separately, if
we read or reuse its generator code rather than only citing the paper; (b) fresh
provenance check if we ever swap in real-world-derived seed data.

## Prior art (verified on arXiv, 2026-07-01)

- τ-bench, `2406.12045`; τ²-bench, `2506.07982` (nearest prior art)
- AppWorld, `2407.18901`; ToolSandbox, `2408.04682`; Agent-Diff, `2602.11224`
  (state-diff success contracts, neighbors to the replay oracle)
- GSM-Symbolic, `2410.05229`; GSM-SEM, `2605.07053` (semantic-variant regeneration
  with preserved difficulty, direct support for width-in-classes)
- LiveBench, `2406.19314`; LiveCodeBench, `2403.07974`; AntiLeakBench, `2412.13670`
  (freshness-based contamination resistance)
- ProcGen, `1912.01588`; ProcGen competition, `2103.15332`; ProcTHOR, `2206.06994`;
  Avalon, `2210.13417` (seeded procedural generation, train/test seed split)
- Dynabench, `2104.14337`; BetterBench, `2411.12990`; CheckList, `2005.04118`;
  PaCoST, `2406.18326` (benchmark methodology, paired contamination testing)

Full assessment and source URLs: `PRIOR_ART_REGEN.md`.
</content>
