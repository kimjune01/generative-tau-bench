# Generative τ-bench

A *method* for converting a database-shaped tool-agent benchmark into an evergreen,
contamination-resistant one, via seeded regeneration plus a replay-derived oracle.
τ-bench is the case study and existence proof, not the product. Design note and
paper plan.

## Contribution (crystallized)

> A reusable transformation for **database-shaped stateful tool-agent benchmarks**
> that combines seeded, constraint-preserving regeneration of each instance with a
> **replay-derived final-state oracle**, so fresh instances *and their graders*
> re-derive from a seed with no re-annotation and no mining of new real tasks.

The framing is a method, not a benchmark. That matters strategically (a recipe gets
cited even when a given instantiation is not adopted) and it sets the bar: the
transformation should be shown on more than one benchmark (τ-bench plus AppWorld or
ToolSandbox) so it reads as a method, not a single benchmark in method's clothing.

Lead with the words that are unconditionally true, **evergreen, reproducible,
difficulty-controlled, paired**; treat *contamination-resistant* as a corollary of
evergreen-with-seed-rotation, not as the headline (it carries an empirical burden a
null gap cannot discharge; see Risks).

## Domain of validity (the applicability theorem)

The recipe applies iff a task satisfies all four preconditions:

1. **State is enumerable typed entities with ids** (a relational DB, not free text).
2. **The solution is a program over those entities**, so it transforms under the
   same seeded re-key the state does.
3. **The oracle is a deterministic function of the final state** (replay-checkable),
   not a bespoke artifact.
4. **A constraint-preserving resampler exists** (vary contents without breaking
   solvability).

In scope: τ-bench, τ²-bench, AppWorld, ToolSandbox, and the broader transactional
tool-agent family (CRM, booking, inventory/ERP, SQL/data, form and workflow
automation). Out of scope: **unstructured-state, bespoke-oracle** tasks, canonically
real-world SWE (codebase state, free-form patch, hand-written tests, no
semantics-preserving resampler), which is exactly why coding benchmarks (SWE-rebench,
LiveCodeBench) get freshness by *mining* new tasks rather than regenerating old ones.
The boundary is not "code": parametric algorithmic coding with an executable
reference solution is regeneratable; repo-level SWE is not.

## Motivation: contamination is a recognized, cross-benchmark problem

The premise is not assumed; it is documented across position papers, audits, and the
benchmark builders themselves (citations verified from primary sources 2026-07-01
unless flagged).

*It is a field-wide validity threat.* Sainz et al. (2310.18018): "Contamination
causes an overestimation of the performance of a contaminated model ... The
consequences can be very harmful, with wrong scientific conclusions being published
while other correct ones are discarded." Balloccu et al. (EACL 2024, 2402.03927)
quantify the scale: across 255 papers, closed models "have been globally exposed to
~4.7M samples from 263 benchmarks."

*The inflation is measured, not hypothetical.* Zhang et al.'s GSM1k (2405.00332), a
freshly authored twin of GSM8k, found "accuracy drops of up to 8%, with several
families of models showing evidence of systematic overfitting," correlated (Spearman
r² = 0.36) with a model's propensity to regenerate GSM8k examples (they note frontier
models show minimal overfitting). Deng et al. (2311.09783) found GPT-4 could guess
masked MMLU answer options 57% of the time (ChatGPT 52%). Xu et al. (2404.18824)
found "substantial" test-set misuse across 31 LLMs on mathematical reasoning.

*Benchmark makers cite it as their reason to build.* LiveBench (2406.19314): "Test
set contamination ... is a well-documented obstacle for fair LLM evaluation and can
quickly render benchmarks obsolete," so it refreshes questions monthly.
LiveCodeBench (2403.07974) is "contamination-free" by "continuously collect[ing] new
problems over time." SWE-rebench (swe-rebench.com/about): "models released after this
date may have seen these exact issues or highly similar data during training." OpenAI
stopped reporting SWE-bench Verified partly because open, widely-discussed repos make
"avoiding contamination difficult for model developers" (the widely-cited audit
figures, ~59% flawed items, 80%→~23% drops, come from secondary reporting; the
official page 403s to automated fetch and is unverified here).

*Agent benchmarks are not exempt, and neither is a clean-at-release one.* Whether
scraped-but-timestamped (SWE-rebench) or fully synthetic (τ-bench, 2406.12045, users
"simulated by language models"), a static public benchmark decays as its gold data
ages past successive training cutoffs. (That τ-bench's public goldens age into cutoffs
is an inference from its being public and static, not a Sierra claim.)

This is the case for contamination-resistance that is *structural* rather than a
matter of timing, which is what regeneration provides.

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
   filtered out ~68% of samples for quality, and OpenAI later stopped reporting it,
   citing contamination among the reasons (the widely-cited audit percentages are
   from secondary reporting; the primary page is unverified here). Static open
   benchmarks decay.
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

## Design lineage: procedural content generation in games

This method is procedural content generation (PCG) applied to benchmarks. Games have
solved the same problems for decades and the mapping is exact enough to borrow both
framing and technique (sources: Togelius/Shaker/Nelson PCG book; Togelius et al. 2011
search-based taxonomy; Smith & Mateas ASP; Karth & Smith WFC; Smith & Whitehead
expressive range; Cobbe et al. ProcGen/CoinRun; Kazemi's Spelunky Generator Lessons).

- **Seed determinism = reproducible + fresh.** A seed fully determines the content, so
  the same seed reproduces an instance and a new seed yields a fresh one. Dwarf
  Fortress is the cautionary case: geography is seed-reproducible but history diverges
  when generation is not strictly seed-pure, the exact failure our determinism test
  guards against.
- **Daily-challenge seeds = decontamination + paired eval.** Spelunky and Slay the
  Spire issue one server-gated seed per day, identical for everyone, not available in
  advance. That is our protocol precisely: reveal the seed at eval time (un-rehearsable,
  so contamination-resistant) and run every system on the same seed (paired comparison).
- **Train/test seed split = memorization meter.** ProcGen and CoinRun train on a finite
  seed set and test on held-out seeds; "the gap between train and test performance
  determines the extent of overfitting" (CoinRun), tested zero-shot with no fine-tuning.
  This is our memorization measurement, and CoinRun's finding that overfitting persists
  until thousands of training levels is a quantitative anchor for required generator width.
- **Solvability guarantees = our solvability audit.** Games keep levels completable three
  ways: build-by-construction (Spelunky's solution path, Brogue's accretion tree),
  generate-and-test-and-reject (simulate a reference solver, regenerate on failure), and
  constraint-solver enumeration (ASP). **Our replay oracle is the reference-solver route:
  replaying the golden both certifies the instance is answerable and produces the grader,
  in one pass.** Warning inherited from Wave Function Collapse (Karth & Smith): local /
  per-field constraints do not imply global solvability, so a constraint-preserving
  resampler still needs a whole-task check (the golden replay), not just valid fields.
- **Expressive-range analysis = generator-width / anti-shortcut instrument.** Smith &
  Whitehead measure a generator's output distribution on emergent metrics kept
  *independent of the generation parameters*, then plot it to expose bias, thin coverage,
  or a clustered region a solver could exploit. This is the compute-free way to
  substantiate the "wide enough that no shortcut survives" claim: generate thousands of
  instances, score emergent difficulty/structure, inspect the distribution.
- **Constraint-based generation = structural regeneration.** ASP design spaces (Smith &
  Mateas) and mission/space grammars (Dormans) regenerate the scaffold under declared
  constraints rather than perturbing surface tokens, the model for structural (not
  cosmetic) task regeneration.

Two borrows to carry into the writeup: the replay oracle is the PCG reference-solver
solvability certificate doubling as the grader, and expressive-range analysis is a
ready-made, compute-free proof of generator coverage. (Flags from the sweep: Spelunky's
guarantee is constructive, not a digging solver; expressive-range quotes are from Smith's
dissertation, not the paywalled workshop paper; daily-mode exact wording came via search
summaries.)

## Cross-domain convergence and the oracle ladder (the spine)

Four fields independently beat memorization the same way, by generating fresh tests,
and they differ mainly in *how they label a generated instance*. That difference is
the whole argument.

| Oracle | Example | What you get | Cost / limit |
|---|---|---|---|
| **Constructive (generation = grading)** | domain randomization, class-conditional render (vision); **our replay oracle** | the graded answer, free, unlimited | only where the answer is a byproduct of generation |
| Human re-annotation | Recht ImageNet-v2, ObjectNet | ground truth | expensive, one-shot, not renewable |
| Metamorphic relation | DeepTest, ImageNet-C corruptions | a *consistency* constraint, not a label | needs a seed with a known label; bounds deviation, doesn't grade |
| Cross-reference vote | DeepXplore | a disagreement flag | can't say who is right; fails on shared blind spots |

The fresh-test trick is old and universal (games PCG, RL generalization ProcGen/
CoinRun, vision Recht/ObjectNet, software DeepTest/DeepXplore). The *top rung*
("generation is grading") is only available where the answer falls out of generation.
Vision reaches for metamorphic or vote oracles precisely when it cannot render the
label; LLM-QA refresh work (DyVal, Recht-style) pays for the label or derives it
symbolically; mining (LiveBench/SWE-rebench) sidesteps generation entirely. **Stateful
tool-agent tasks are the corner of LLM evaluation where the top rung is reachable,
because replaying the golden emits the (instance, grade) pair together.** That is the
port, and why it is new: not a new trick, the strongest-oracle trick applied where it
was newly available. Every "that is just DyVal / ProcGen / τ²" objection is answered by
one sentence: none of them had a constructive, replay-derived oracle over a mutating
tool world.

Honest hedge (Recht): a score drop on a fresh set is necessary but not sufficient
evidence of memorization. Recht found the ImageNet-v2 drop was harder-reconstruction,
not adaptivity (ranking preserved, gains transferred). A contamination claim needs a
rank-preservation / gap-decomposition analysis, not just a drop.

## Novelty: honest position

Every component exists. The contribution is the synthesis, formalization, and
receipts, not a new primitive, and the paper is only real if it is built and
measured. A dedicated method-level prior-art sweep is in [`PRIOR_ART_METHOD.md`](PRIOR_ART_METHOD.md)
(citations verified 2026-07-01); its verdict is folded in below.

**As a broad claim ("make benchmarks dynamic/evergreen/contamination-resistant"),
this is not novel** and would be rejected as subsumed. The dynamic-evaluation-as-a-
*method* ground is already held by DyVal (2309.17167), DyVal 2 / Meta Probing Agents
(2402.14865), Benchmark Self-Evolving (2402.11443), and metamorphic-testing work,
plus GSM-Symbolic/GSM-SEM (template regen), LiveBench/LiveCodeBench/SWE-rebench
(mining freshness), AntiLeakBench, and ProcGen (seeded procedural + seed splits).

| Component | Prior art | Novelty |
|---|---|---|
| Replay-and-hash oracle | τ-bench | none, we keep it |
| Regenerate not hide | GSM-Symbolic, GSM-SEM, LiveBench, LiveCodeBench, AntiLeakBench | low; underdeveloped for relational tool worlds |
| Dynamic-eval as a general transformation | DyVal, DyVal 2 / Meta Probing Agents, Benchmark Self-Evolving, metamorphic testing | none; but all transform *text/reasoning* problems, none the stateful tool-world |
| Seeded procedural instances + train/test seed split | ProcGen, ProcTHOR, Avalon | none in RL, derivative for agents |
| Shared-seed paired eval | common random numbers, McNemar, PaCoST | none statistically, underused in agent benchmarks |
| **Replay oracle + seeded regeneration for database-shaped tool-agent benchmarks** | τ²-bench is nearest | **medium; no exact prior instance found** |

**The defensible delta** (why DyVal-style dynamic evaluation does not subsume it):
DyVal and kin transform *problem statements* and rely on generated answers, judge
models, or symbolic derivation; they do not produce a **replay-derived final-state
oracle** for a *mutating tool world*. Stated for a paper, to our knowledge:

> For database-shaped stateful tool-agent benchmarks, a transformation that
> seeded-regenerates both the initial world and the canonical solution program, then
> derives each fresh grader by replaying that program on the regenerated world.

Keep "to our knowledge" until the sweep is re-run at submission.

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

## What we must prove, and the n it takes

This is a mechanism paper. The load-bearing usefulness claim is **not**
"we detect contamination" (cosmetic re-key is near-inert against semantic
contamination and a null gap is ambiguous; see Risks). It is: **the replay oracle
turns freshness from a per-instance cost into a fixed cost, which makes powered,
paired, evergreen measurement possible where mining and templating can't reach.**
Contamination-resistance follows *structurally* (evergreen by construction, seed
rotation), it is not the thing we stake on an experiment.

A mechanism proof is closer to correctness than to statistics, so "large n" is the
wrong axis. Disambiguate the n's:

| n | Want it | Cost | Why |
|---|---|---|---|
| generated instances (soundness audit) | **large** | **free** (no model calls) | correctness is shown over the generator's whole output; being able to get this for free is the point |
| benchmarks the recipe is applied to | **2+** | moderate | this is what makes it a *method* not a benchmark; τ-bench **and** AppWorld beats 20 models on τ-bench |
| models / harnesses evaluated | **small** | compute | the empirical section is an existence proof, not a population study |
| trials per instance | small–moderate | compute | enough for a `pass^k` illustration and one paired comparison |
| instances per class in the demo | argued, not run large | analytic | prove the static set is underpowered; supply, don't survey |

### The proof ladder (cheapest and most decisive first)

1. **Power argument (compute-free).** Show analytically that the static benchmark
   cannot resolve realistic effect sizes: at n=115 retail the binomial SE makes a
   5–8 point harness gap non-significant; state the n actually required. Proves
   *necessity* of more instances before any model runs.
2. **Cost accounting (compute-free).** Quantify the unique benefit: the generator
   emits M graded instances for *zero annotations* because the oracle re-derives by
   replay; mining needs a pipeline, templated QA needs per-variant answer keys,
   hand-authoring needs graders. Fixed-cost-high, marginal-cost-zero. Proves
   *uniqueness*, and is the direct answer to "why the extra complexity."
3. **Soundness (large-but-free).** Over thousands of generated instances: injective
   re-key, coverage (no original id leaks), clean solvability (golden replays with
   no tool errors), determinism (same seed → same oracle), and an audited
   invalid-instance rate driven to ~0. This is property/correctness evidence, not
   sampled estimates. (Core already passing in `tests/`.)
4. **Impact demo (small compute, the money shot).** Show the mechanism *changes a
   conclusion*: a harness A-vs-B comparison that is tied or misleading on static
   τ-bench resolves or flips under powered, same-seed-paired generative evaluation.
   Report `pass^k` with CIs stratified by difficulty class, and quantify the
   variance reduction from paired seeds vs independent sampling (McNemar). Small-n
   by design: flip *one* comparison, don't survey many.
5. **Contamination gap (compute, supporting only).** Original vs regenerated on one
   model; report whether it fires. Not load-bearing: if null, the benchmark is
   renewable regardless. A *non-null* drop is also not by itself memorization (Recht's
   ImageNet-v2 drop was harder-reconstruction, not adaptivity); isolate it with a
   rank-preservation / gap-decomposition analysis. Optionally ablate a suspected
   generator shortcut to separate instance-memorization, distribution-overfit, and
   genuine competence.

### The guardrail: more than a position paper, not a study

Minimum to clear codex's "position paper" bar without a large empirical study: a
working generator (have it), the soundness audit (step 3), **two** benchmark
instantiations (step, open: add AppWorld), and one illustrative eval (step 4). The
explicit τ²-bench oracle-code comparison remains the blocking novelty check.

## Risks and honest limits

- **Cosmetic re-keying may be near-inert against the contamination that exists here
  (the sharpest risk).** In tau-bench every id the golden needs is *discoverable
  in-context* via tool calls, so a contaminated model never had to memorize an id
  from weights. What it memorizes is the *resolution path*: the policy branch, the
  conditional fallback, the intended end-state. Re-keying preserves all of that
  byte-for-byte (same products, prices, structure, policy branch), so it defeats a
  threat model that barely exists. The real signal lives entirely in **structural
  regeneration** (resampling contents under class constraints), which is unbuilt.
  Corollary: a null memorization-gap could be *structural* (re-key blind to semantic
  contamination), not evidential. Treat cosmetic re-key as the substrate for
  structural regeneration, not as a contamination defense on its own.
- **The user simulator is central, not orthogonal, and the MVP has a construct-
  validity break.** A tau-bench `instruction` is the *user simulator's* script,
  carrying private conditional intent the agent must ELICIT over dialogue. Handing it
  straight to the agent (the current `user_sim=None` path) leaks the answer sheet, so
  those runs measure an easier task and are NOT tau-bench-comparable (`eval.py` now
  marks them `comparable=False`). A faithful number needs a `UserSim` (LLM, or a
  deterministic scripted user that reveals intent only when asked); the hook exists,
  no implementation ships.
- **CLI agents measure product, not model.** `claude -p` / `codex exec` wrap a model
  in a coding-agent scaffold with its own prompt and loop, and cannot be fine-tuned
  (which forecloses the memorization-meter experiment). Use them only for a labeled
  demo. Any published model-competence number should use an API tool-calling agent
  (tau-bench ships one). Whether the goal is *model* competence or *CLI-product*
  competence is an open decision that drives this.
- **Authoring cost is the real labor.** Regeneration saves per-instance annotation,
  not per-class design. Width equals authored classes. LLM-authoring classes to
  scale reintroduces the solvability audit on machine-made templates.
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
