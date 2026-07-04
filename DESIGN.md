# Generative τ-bench

**Thesis.** If a benchmark's tasks are the kind where regenerating the state changes the
correct answer *through the skill being measured* (skill-bearing state equivariance), and
the generator stays representative of the target task (construct validity), then seeded
procedural generation *re-prices* the benchmark's decay rather than halting it. It converts
the failure clock from time-until-instances-leak (the ~1–2 year saturation of a fixed test
set) into time-until-the-orbit's-skill-quotient-is-learned, a slower clock whose rate is set
by how much *structural* variation you author, not by the calendar. The asset becomes
renewable at the margin but bounded: per-instance freshness entropy cannot exceed the class's
authored structural entropy. Seeds recycle that entropy, they do not manufacture it. (This is
the honest form after an adversarial fable pass; "indefinite" freshness was the overclaim a
single fine-tune-on-the-generator experiment would end.)

A *method*, not a benchmark: a reusable transformation that regenerates an interactive
environment's state from a seed and re-derives the grader by replaying a canonical reference
against it, so fresh instances *and their oracles* come for free. τ-bench is the validated
case study and existence proof, not the product. Design note and paper plan.

## Contribution (crystallized)

> A reusable transformation for **interactive, state-mutating benchmarks whose scored
> output co-varies with the regenerated state**: combine seeded, constraint-preserving
> regeneration of the environment state with a **replay-derived oracle** (re-execute a
> canonical reference against that state), so fresh instances *and their graders*
> re-derive from a seed with no re-annotation and no mining. The empirical core is
> mapping the boundary of *when* regeneration re-prices contamination, and against which
> declared adversary class the re-pricing holds.

Reframed after an adversarial fan-out (log: `_drafts/executable-oracle-class.md`; codex
convergence folded in). Three things changed the claim:

- **The load-bearing precondition is equivariance, not "database-shaped"** (see Domain of
  validity, precondition 5). This is what killed the tempting text-to-SQL and competitive-
  coding demonstrations.
- **Two regeneration axes.** *State*-regeneration (ours) keeps the oracle a pure computation
  and holds difficulty fixed (re-keying is a nuisance-parameter swap). *Problem*-regeneration
  (DyVal, GSM-Symbolic: synthesize a fresh problem) also raises the contamination bar but reintroduces
  variable difficulty and well-posedness risk through an LLM in the instance path. We claim the
  state-regeneration axis for interactive environments; we cite problem-regeneration as the
  neighboring alternative (e.g. text-to-SQL is only evergreen-able on *that* axis).
- **Position vs DyVal.** Extend contamination-resistant dynamic evaluation from generated
  *static reasoning* instances (DyVal, ICLR 2024; GSM-Symbolic) to *stateful interactive
  environments* where the instance is a mutable world state and correctness is computed by
  replaying a reference against it. DyVal is the single-turn degenerate case — cited, not
  claimed as the genus (property-based testing, MiniWoB/WebArena also live in that genus).

The framing is a method, not a benchmark (a recipe gets cited even when an instantiation is
not adopted). It sets the bar: show the transformation on a second, *independent* benchmark
(**WorkArena**, not just a second τ-bench domain), and — the real empirical contribution —
demonstrate the equivariance boundary *across classes*.

Lead with the words that are unconditionally true: **evergreen, reproducible,
difficulty-controlled, paired**. Treat *contamination-resistant* as earned by the boundary
experiment, not asserted (a null gap alone cannot discharge it; and per Recht a non-null gap
is not automatically memorization; see Risks).

## Domain of validity (the applicability theorem)

The recipe applies iff:

1. **State is enumerable typed entities with ids** (a relational/world DB, not free text).
2. **The interaction is a program over those entities** that replays/transforms under the
   seeded re-key.
3. **The oracle is a deterministic function of the final state** (replay-checkable) — not a
   stored key (a *lookup*), nor an LLM/human *judgment*.
4. **A constraint-preserving resampler exists** (vary contents without breaking solvability).
5. **(the crux) The scored output co-varies with the regenerated state, and recovering that
   co-variation requires the measured skill** — *skill-bearing state equivariance*. Two
   failure modes it rules out (independently re-derived by a blind fable pass, which also
   confirmed the SQL/coding calls and the Zhong-et-al. prior art):
   - *Invariance (mode B):* if the scored artifact is *invariant* under regeneration —
     because correctness is defined by *executing* it against the seed's data (a SQL query, a
     program, a policy that quantifies over the state) — then the correct answer is a fixed
     point of the whole grader family, and memorizing it survives. Regeneration here hardens
     the grader against *wrong* answers (grader integrity) but does nothing for contamination;
     conflating the two is the common error.
   - *Cheap transport (mode A):* if the answer co-varies but can be produced by a skill-free
     transport of a memorized canonical answer (rename variables, plug fresh numbers into a
     memorized closed form), regeneration only *degrades* memorization, it does not defeat it,
     and the measured construct quietly shrinks (GSM-Symbolic: "comprehend and solve" →
     "plug in and compute"). τ-bench passes because the transport *is* the skill: executing a
     policy against freshly-bound state via tool calls is what is being measured.
   The crisp form (fable): regeneration measures exactly the computation that transports the
   seed's fresh entropy into the graded output; whatever the randomization leaves invariant
   remains memorizable and silently drops out of what is measured. This is a formalization of
   a known equivariance / label-changing principle, not a new phenomenon.

Precondition 5 is what a "database-shaped" reading misses, and it redraws the boundary:

- **IN** (all five; interactive, state-equivariant): **τ-bench, AppWorld, WorkArena** — the
  agent emits a *state-specific action trajectory* graded by re-executing a reference against
  the regenerated state.
- **Single-turn degenerate** (cite, do not claim): DyVal, GSM-Symbolic — scored answer
  co-varies, but static reasoning, not interactive state.
- **OUT on precondition 5** (pass 1–4, fail 5): **text-to-SQL** (scored artifact is the SQL
  query, a state-*general* program, invariant to row regeneration) and **competitive coding**
  (scored artifact is code, input-invariant; and there the input distribution *is* the
  difficulty). These are only evergreen-able via *problem*-regeneration, not ours.
- **OUT earlier**: repo-level SWE (fail 1–4: unstructured state, bespoke tests); MMLU (fail 3:
  stored key = lookup); Chatbot Arena (fail 3: judgment oracle).

The clean test is MMLU vs GSM-Symbolic: both are single-answer QA, but GSM-Symbolic carries a
*re-runnable solution procedure* while MMLU carries only a *key*. Presence of a re-runnable
reference is the boundary between computation and lookup; precondition 5 is the boundary
between computation-that-co-varies and computation-that-doesn't.

## What "evergreen" buys: two axes, an adversary ladder, and a bounded budget

The applicability preconditions above say *where* the recipe fits. They do not say *what it
buys against a determined adversary*, and stating that honestly is the difference between a
proposition and a vibe. Structure forced open by an adversarial fable pass:

**It is two axes, not a list of preconditions.** Everything collapses into two independent
quantities:

- **Oracle axis (trust, not cost).** Does a golden-producing procedure exist whose correctness
  is *independent of the capability under test* — no learned component anywhere in the oracle
  path? This is the right statement, not "construction is cheaper than solving." Our own
  flagship refutes the cost framing: branch-selection derives the golden by running the same
  predicate the winning policy runs, so construction is *not* cheaper than solving; it is
  *trusted* where an LLM golden would not be. Factoring is the special case where the trusted
  computation happens to be forward planting (construction genuinely cheaper). Full structural
  regen fails this axis: its only golden-producer is an LLM as fallible as the testee.
- **Entropy axis (one quantity, not two conditions).** The min-entropy of the golden given the
  adversary's *total* view: public generator code, orbit history, and the instance. "Non-leaking"
  (entropy given the instance) and "equivariance" (entropy given memorized orbit representatives)
  are two conditioning slices of this one quantity, so they are not independent conditions. It is
  also a *continuum, not a boolean*: cosmetic re-key transports 0 fresh bits, GSM-Symbolic
  transports operand-bits-only, branch-selection transports 1 bit (which branch), full structural
  would transport many. A boolean iff over a continuum is false at every interior point; the
  contribution is the *measure*, not a partition.

Two seams the preconditions do not cover, both real: **grader completeness** (plantedness
certifies *one* witness; a sound oracle must accept the whole equivalence class of valid
behaviors — see "Equivalence, not exact hash," promoted here to a first-class requirement that must hold across the
orbit, not per hand-checked instance); and **orbit min-entropy vs. the adversary's training
budget** (if the seed range is guessable or the orbit is small enough to enumerate and train
on, all axes pass and the benchmark is still contaminated — the seed protocol (reveal at eval time) is doing
load-bearing work *outside* any generator-intrinsic condition).

**Index every claim by a declared adversary class.** There is no hardness assumption available
("evaluate one predicate" is hard for no interesting circuit class), so evergreen-ness is only
ever *relative to a declared adversary*:

- **A0 — verbatim replayer.** Emits the memorized shipped golden. Defeated by any equivariant
  regeneration (this is what the 0.44–0.72 branch-selection gaps measure).
- **A1 — memorize-plus-cheap-transport.** Memorizes re-key maps, closed-form plug-ins, and
  *the finite authored branch pool plus a dispatch selector*. This adversary closes the
  branch-selection gap, because the branch template pool is finite, authored, and public.
- **A2 — fine-tune on the public generator's outputs.** The strongest, and the one our
  memorization meter most needs; the CLI-agent choice (see Risks) forecloses running it, which is a
  real hole, not a footnote.

**The honest headline, and its bound.** Regeneration does not *defeat* memorization; it
*re-prices* it, from per-instance (leaks on a training-cutoff clock) to per-class (learned on a
train-on-the-quotient clock), at a per-class cost bounded by the authoring budget already paid.
The mode-A critique we level at GSM-Symbolic applies to branch-selection one rung up: against
A1 the measured construct shrinks from "follow a natural-language policy over dialogue" to
"dispatch among authored templates." So the flagship's honest claim is narrow and bold: *it
opens a measurable gap against A0 where cosmetic re-keying opens none* — not "defeats
memorization." The iff is demoted to a **prediction**: the boundary experiment (the proof ladder) should
show the gap firing on equivariant classes and staying null on invariant ones, and the
distinctive, falsifiable version is CoinRun-style — fine-tune on N public seeds, and the gap
persists for held-out *families* (thesis) rather than decaying to zero (null: regeneration
merely re-prices with no skill transfer).

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
   `pass^k` reported as a point and no CIs. At k = trials = 8 the per-task
   `pass^8` estimator is exactly binary (all 8 pass or not), so the reported
   number is a plain proportion over ~50 Bernoulli tasks
   (receipt: `docs/receipts/POWER_AND_COST.md`).
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

Three rungs, and what separates them is not cost but whether the oracle stays
*derivable by construction*:

- **Cosmetic re-keying** (bijection over ids, resampled labels) is free and defeats
  *verbatim* memorization. The oracle is a proven alpha-renaming invariant. Ship it
  first, but see Risks: against tau-bench's actual threat model it is near-inert,
  because it preserves the resolution path byte-for-byte.
- **Parametric branch-selection** (resample the contents that decide *which* golden
  fires; hold the golden's shape fixed) defeats *path* memorization. Resample the
  catalog so a conditional preference resolves down the other branch and the correct
  action program changes, so a memorized resolution path stops transferring. The
  oracle stays construction-derived because the branches are *already hand-authored*:
  in retail's `tasks_test.py` the two branches of one instruction ship as two
  separate Sierra-verified tasks. The generator's only job is to pin, by seed, which
  predicate outcome the resampled DB satisfies. It *selects* among authored goldens,
  it does not synthesize one. This is the reachable rung above cosmetic. **Built and
  validated on a 13-task family** (`gtau/branch.py`, `tests/test_branch_selection.py`;
  inventory: `docs/BRANCHABLE_TASKS.md` — 76 of 165 tasks are state-testable, 14 graded
  EASY, 12 of 12 attempted specs validated, task 83 deferred as a different resampler
  shape). The engine is a three-part algebra: a seeded resampler over each spec's
  realizable availability-worlds, a selector that re-evaluates the instruction's stated
  predicate (preference cascade or argmin/argmax) on the resampled catalog, and a golden
  builder that substitutes the branch-decided slot into the shipped action list —
  identity substitution on the shipped branch, so every spec reproduces its shipped
  oracle byte-for-byte (and the sibling task pairs 0/1, 6/7, 8/9, 41/42, 97/98 anchor
  both sides). Every derived golden replays with zero tool errors (solvable by
  construction); branches reach distinct end-states; branch-coupled `outputs` co-derive
  with the pivot (task 44's refund amount). The payoff is a memorization meter *against
  adversary A0* (the verbatim replayer): across the 13 specs the shipped-golden replayer
  scores exactly the shipped-branch seed fraction (asserted, not approximated) while the
  predicate-following policy scores **1.00** on all, for gaps of **0.44–0.72**
  (binary specs ~0.5, k-way argmin specs up to 0.72 — more realizable branches, bigger
  gap), where cosmetic re-keying leaves the same gap at ~0 because it preserves the
  very path the replayer emits. State it narrow and bold: this opens a gap against A0 where
  re-keying opens none. It does *not* survive A1 (memorize the k authored branches plus the
  one-bit dispatch predicate closes it), because the branch pool is finite, authored, and
  public. Widening the class past A0 is authoring more branches, which is the bounded budget
  the thesis names, not free freshness (see "What evergreen buys").
- **Full structural regeneration** (a genuinely new golden path, a policy branch no
  human enumerated) would defeat *pattern* memorization outright, but is not
  tractable here. It needs a `solve(db, intent) -> action_program` that reads the
  policy and emits a correct program; no such solver exists in tau-bench or gtau, and
  the policy is 81 lines of `wiki.md` prose with content-dependent branches, not a
  machine-checkable spec. The only artifact that can pick a branch under genuinely
  new state is an LLM reading that prose, i.e. the system under test, which makes the
  oracle as fallible as the agent and collapses precondition 3. This rung is
  foreclosed unless a class's policy is first re-authored as an executable constraint
  program, which is the per-class authoring cost made total, and what a class *is*.

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
was newly available. The "that is just DyVal / ProcGen / τ²" objection is answered by the
*assembly*, not the oracle alone: τ² does have a constructive replay-derived oracle
(retail/airline) and does have a compositional generator (telecom), but never in the same
domain and never wired to seeded regeneration as a freshness protocol (see "The delta versus
τ²-bench"). DyVal/ProcGen never had the replay oracle over a mutating tool world. What is new
is the fusion, in one domain, of the top-rung oracle with seeded, reveal-at-eval regeneration.

Honest hedge (Recht): a score drop on a fresh set is necessary but not sufficient
evidence of memorization. Recht found the ImageNet-v2 drop was harder-reconstruction,
not adaptivity (ranking preserved, gains transferred). A contamination claim needs a
rank-preservation / gap-decomposition analysis, not just a drop.

## Novelty: honest position

Every component exists. The contribution is the synthesis, formalization, and
receipts, not a new primitive, and the paper is only real if it is built and
measured. A dedicated method-level prior-art sweep is in [`docs/PRIOR_ART_METHOD.md`](docs/PRIOR_ART_METHOD.md)
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

τ²-bench (`2506.07982`) has both halves of an evergreen benchmark, but they never
meet, and neither is a freshness protocol. Verified against the actual source
(`src/tau2/evaluator/`, `src/tau2/domains/telecom/tasks/`), not the paper:

- Replay-derived grading is real but *not* our invention. Retail and airline grade by
  building a gold env, replaying `evaluation_criteria.actions`, and comparing
  `get_db_hash()` (`evaluator_env.py:81-125`). That is τ-bench's existing mechanism.
  Claim (1) below, "we derive the oracle by replay," must therefore be *cited, not
  claimed as novel* — gtau's own `replay.py` docstring already concedes this.
- The compositional generator is real but *deterministic enumeration dumped to static
  public JSON*, run once at authoring time, over hardcoded entity literals
  (`"John Smith"`, `customer_id="C1001"`). No `random.Random(seed)` touches DB content
  anywhere. Every `seed` in the repo drives the user-sim LLM or subsamples the fixed
  pool. So τ² is not evergreen in any operational sense: the emitted set is frozen and
  shipped, and re-running the generator yields new *combinations*, not new *content*.
- The two halves live in *different domains and never co-occur*. The domain with the
  generator (telecom) grades 100% by hand-written `env_assertions`, 0% by replay; the
  domains with replay-derived grading (retail, airline) have no generator at all. τ²
  never fuses "generated instance" with "oracle re-derived by replay."

So the defensible delta is exactly the assembly τ² leaves unbuilt: (1) *use* the
replay-derived oracle to make seeded regeneration free (no fresh assertions), in the
same domain; (2) make *seeded regeneration with reveal-at-eval-time* the primary
contamination protocol, not a one-time authoring convenience; (3) make *paired CRN
reporting* standard. This is validated only on DB-hash-graded (retail/airline-style)
domains; extending it to an assertion-graded compositional domain like τ²'s telecom
is unbuilt and non-trivial. Scope the claim there and say so.

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
| benchmarks the recipe is applied to | **2+, one independent** | moderate | makes it a *method*; τ-bench (retail+airline) is one family, so the second must be independent (WorkArena) — two τ-bench domains don't count |
| models / harnesses evaluated | **small** | compute | the empirical section is an existence proof, not a population study |
| trials per instance | small–moderate | compute | enough for a `pass^k` illustration and one paired comparison |
| instances per class in the demo | argued, not run large | analytic | prove the static set is underpowered; supply, don't survey |

### The proof ladder (cheapest and most decisive first)

1. **Power argument (compute-free). DONE** (`docs/receipts/POWER_AND_COST.md`): the
   static benchmark cannot resolve realistic effect sizes — the minimum detectable
   effect for an unpaired harness comparison is **15–18 points at n=115** (retail)
   and **22–28 points at n=50** (airline), α=.05, power=.80; a 5-point gap needs
   ~1,565 instances/arm unpaired, ~1,256 shared paired. Pairing on the *static* set
   does not rescue it (power 0.107 at n=115): the generator's contribution is
   unbounded n *while retaining* pairing via shared seeds. Bonus: τ-bench's
   `pass^8` per-task estimator is exactly binary (k = trials = 8), and p→p⁸
   attenuates a 5-point per-trial gap to ~0.45 points. Proves *necessity* of more
   instances before any model runs.
2. **Cost accounting (compute-free). DONE** (same receipt): the generator emits M
   graded instances for *zero annotations* because the oracle re-derives by replay;
   mining needs per-instance collection + filtering, hand-authoring needs a
   verified golden per task. Honest scoping from the receipt: templated QA
   (GSM-Symbolic) *also* reaches ~zero marginal annotation by deriving each
   variant's answer — per-*template*, not per-variant, cost — so the delta we own
   is zero marginal cost *for stateful interactive tasks*, where templating does
   not reach. Fixed-cost-high, marginal-cost-zero. Proves *uniqueness*, and is the
   direct answer to "why the extra complexity."
3. **Soundness (large-but-free). DONE** (`docs/receipts/SOUNDNESS_AUDIT.md`,
   `scripts/audit_soundness.py`): injective re-key, coverage (no original id leaks,
   checked at substring level), clean solvability, determinism, faithfulness, over
   4,125 re-keyed + branch-selected instances at scale — invalid rate driven to
   **0** after the audit caught a real id-leak bug the 5-seed test suite had
   certified clean (`_mint`'s suffix fallback embedded the original id in every
   digit-less airline reservation code; fixed by same-length letter-run
   regeneration). The audit paying for itself is the receipt's own argument.
4. **Impact demo (the money shot). PILOTED; confirmatory is pre-registered future work**
   (`docs/receipts/PILOT_EFFORT.md`). The claim: a harness A-vs-B comparison *tied on
   static τ-bench* (n=115, MDE 15–18) *resolves* under paired generative evaluation. Piloted
   with the clean instrument — Opus 4.8 at low vs high reasoning effort (same weights, same
   contamination, only compute differs). Findings that scope the confirmatory: (a) the
   harness is sound (a high-effort failure re-ran and passed cleanly — genuine agent
   behavior, not a parse/max-steps artifact); (b) the per-instance outcome is **stochastic
   across runs**, so CRN pairing fixes the *instance* but not agent/sim noise — a
   single-trial gap is not identifiable; (c) two cost-inflators stack — within-spec
   ICC ≈ 0.48 and that un-CRN'd stochasticity — so a powered confirmatory needs *many specs
   AND multiple trials per instance*, beyond the current budget. Reframe kept from the
   pilot: **the generator's gift is unbounded n, not pairing** (pairing/McNemar is free on
   the static 115 too — our own power receipt shows paired power 0.107 there; the generator
   lifts the n-cap *while keeping* pairing). Deferred to a cross-model pair (larger, cleaner
   gap) once OpenAI/codex access returns; the Opus-effort-tier gap is small and noisy and is
   a weak instrument. Report `pass^k` at small k as a stratified illustration only (pass^1 is
   the powered metric; p→p⁸ crushes the gap). Small-n by design: flip *one* comparison.
5. **The cross-class boundary experiment (THE empirical contribution). Construction-level
   DONE** (`docs/receipts/BOUNDARY.md`, `scripts/boundary_experiment.py`). This is
   what the fan-out surfaced and what codex says the paper survives on: don't just show a
   contamination gap on τ-bench, *map the boundary*. Memorize a static baseline, then show
   the gap **fires on the equivariant classes** (τ-bench, WorkArena: scored trajectory
   co-varies) and **stays null on the invariant ones** (text-to-SQL, competitive coding:
   scored artifact is a state-general program). That double result is precondition 5
   validated empirically, and no one has drawn this boundary for benchmark regeneration.
   The construction-level receipt does it on ONE substrate (retail DB, one resampler),
   varying only the scored target: a perfectly-leaked SQL *query* passes **1.00** of
   regenerated instances (regeneration wasted) while a leaked *answer* graded by a
   replay-derived oracle collapses to `1 - (answer-moved-rate)` (~0.15). Framed as a
   bench-builder's decision rule: score the state, derive the golden by replay. The
   remaining live version (a *contaminated model* read flat on regenerated Spider,
   non-null on τ-bench) is the natural extension.
   Caveats: a null gap on the OUT side is the *predicted* result (not a failure); on the IN
   side, a non-null gap is not automatically memorization (Recht's ImageNet-v2 drop was
   harder-reconstruction) — isolate with rank-preservation / gap-decomposition.

6. **Independent second demonstration. DONE on AppWorld** (`docs/receipts/APPWORLD_INDEPENDENT.md`),
   not WorkArena (deferred on infra cost: ServiceNow + browser). AppWorld (Stony Brook, ACL
   2024) is a local DB-backed tool-agent benchmark with deterministic state-diff grading and
   a runnable seeded generator. Using its *own* generator (so this corroborates the
   regenerate+replay pattern in an independently built domain, not a port of our code), we
   regenerated 12 train scenarios at a **held-out seed** — state beyond the shipped configs,
   new users and answers — and the pipeline ran end-to-end on fresh state (12/12; a
   self-consistency check, not a soundness proof). On the 15 answer-type instances (of 36; the
   other 21 are state-mutation, needing the trajectory-replay adversary), an A0 that memorized
   the shipped answers survives **2/15 = 0.13** on held-out state — both are answer collisions
   (0/13 on distinct-answer instances, n small); the control (own fresh answer) passes 15/15,
   showing the harness accepts the correct answer. So the gap is exactly where regeneration
   moves the scored value off the memorized one — precondition 5 on independent ground. Honest
   scope: A0 is the floor (scalar memorization); state-mutation trajectory-replay is the
   stronger adversary (future work); "independent" is independent-*within-genus* (both DB-backed
   tool-agent) — a modality-distant domain (WorkArena) remains the stretch. The lazy "call
   their hooks on shipped seeds" version is explicitly avoided.

### The guardrail: more than a position paper, not a study

Minimum to clear codex's "position paper" bar without a large empirical study — **all four
now met**: the working schema-agnostic generator (τ-bench retail+airline, 25 branch specs),
the soundness audit (step 3, DONE), one **independent** second instantiation (step 6, DONE
on **AppWorld** — not WorkArena, deferred on infra; a held-out-seed method run, both
boundary sides), and the cross-class boundary experiment (step 5, DONE — construction +
in-context learner). That set is what makes it a method, not "known machinery applied to
τ-bench." The impact demo (step 4) is an *enhancement above* this bar, not part of it: it is
piloted and pre-registered as future work (the Opus-effort-tier gap is small/noisy and the
confirmatory is over budget; a cross-model pair awaits access). The explicit τ²-bench
oracle-code comparison is done (see "The delta versus τ²-bench"): the delta survives but
narrows to the freshness-protocol assembly, and "generation is grading" must be cited to
τ-bench, not claimed.

## Risks and honest limits

- **Cosmetic re-keying may be near-inert against the contamination that exists here
  (the sharpest risk).** In tau-bench every id the golden needs is *discoverable
  in-context* via tool calls, so a contaminated model never had to memorize an id
  from weights. What it memorizes is the *resolution path*: the policy branch, the
  conditional fallback, the intended end-state. Re-keying preserves all of that
  byte-for-byte (same products, prices, structure, policy branch), so it defeats a
  threat model that barely exists. The real signal lives one rung up, in **parametric
  branch-selection** (resample the contents that decide which authored golden fires),
  now built on a 13-task family and shown to open 0.44–0.72 gaps *against A0* where cosmetic
  re-keying opens ~0 (see the regeneration ladder above) — but that gap is closed by A1
  (memorize the authored branch pool plus the dispatch predicate), so branch-selection
  buys a slower depreciation, not immunity; the rung above that, **full structural
  regeneration**, the only one that would break the authoring-budget bound, is foreclosed
  on tau-bench because its only implementation path is an LLM-as-golden, which
  disqualifies the oracle.
  Corollary: a null memorization-gap could be *structural* (re-key blind to semantic
  contamination), not evidential. Treat cosmetic re-key as the substrate for
  branch-selection, not as a contamination defense on its own.
- **The user simulator is central, not orthogonal, and the MVP has a construct-
  validity break.** A tau-bench `instruction` is the *user simulator's* script,
  carrying private conditional intent the agent must ELICIT over dialogue. Handing it
  straight to the agent (the current `user_sim=None` path) leaks the answer sheet, so
  those runs measure an easier task and are NOT tau-bench-comparable (`eval.py` now
  marks them `comparable=False`). A faithful number needs a `UserSim` that reveals
  intent only when asked; `gtau/usersim.py` now ships one (a CLI-driven simulator
  carrying tau-bench's own simulator prompt verbatim), and the first mediated
  episodes pass on both branches of the task-0 spec with `comparable=True`. The
  remaining honest caveat: the simulator is itself an LLM, so simulator fidelity is
  a shared limitation with tau-bench, not a new one.
- **CLI agents foreclose the A2 experiment the theory most needs.** `claude -p` /
  `codex exec` wrap a model in a coding-agent scaffold with its own prompt and loop, and
  cannot be fine-tuned. That is not a minor infra limit: the A2 adversary (fine-tune on the
  public generator, then measure the held-out-*family* gap) is the *only* experiment that
  discharges the central thesis — that the gap persists for held-out families rather than
  decaying to zero as the generator's distribution is learned. Foreclosing it means the
  built 0.44–0.72 gaps can only speak to A0, the weakest adversary. Any published
  model-competence *or contamination-resistance* number needs an API tool-calling agent
  that can be fine-tuned (tau-bench ships the tool-calling agent; the fine-tune arm is
  unbuilt). Whether the goal is *model* competence or *CLI-product* competence is an open
  decision that drives this.
- **Authoring cost is the real labor.** Regeneration saves per-instance annotation,
  not per-class design. Width equals authored classes. LLM-authoring classes to
  scale reintroduces the solvability audit on machine-made templates.
- **"Trained on the distribution" (the Chollet objection) reduces to construct validity.**
  The strongest attack (fable, via Chollet's *On the Measure of Intelligence*, 2019):
  regeneration relocates memorization one level up — the generator is a finite public
  artifact, so a model can train on its whole distribution, and within a fixed procedural
  family "trained on the distribution" is behaviorally indistinguishable from the skill. But
  this is **not a new failure introduced by regeneration**; it is the standard construct-
  validity requirement every benchmark already bears (a static suite that isn't a
  representative sample of its target task measures the wrong thing too), relocated from the
  fixed sample to the generator. It dissolves *if the generator's distribution faithfully
  covers the target task*: then distribution-mastery *is* skill, which is the goal. The
  residue is concrete and dischargeable: (i) a mechanical generator is more prone to narrow
  coverage and non-task *tells* than a curated sample, so representativeness must be *shown*,
  not assumed — via expressive-range / coverage analysis (Smith & Whitehead) and held-out
  task *families* (not just held-out seeds); (ii) the legitimate/illegitimate line is sharp —
  learning task-relevant structure is skill, learning generator artifacts is the failure, and
  the artifact bucket is exactly what expressive-range analysis bounds; (iii) scope the claim
  to the generator's demonstrated coverage — "skill on this distribution" — as any curated
  benchmark's "we sampled 500 issues" claim also is, just made explicit.
- **The novelty negative is a search result, not a proof.** Re-run the sweep before
  submission.

## Discussion material (live receipts, 2026-07-02)

Staging for the paper's discussion section. Every claim here traces to a receipt in
`docs/receipts/`; numbers are small-n and say so.

- **Weights-contamination without behavior-contamination is a real state, and only a
  behavioral instrument can see it.** The recall probe (`RECALL_PROBE.md`) shows a
  frontier model reproducing task 0's golden digit-perfect from weights: order id,
  all four item ids, payment method, fallback target included. The same model, live
  on flipped worlds with the catalog one tool call away, followed the catalog
  (5/6 flipped, 6/6 shipped; `live_task0_claude_12seeds.log`). A static score cannot
  distinguish clean weights from contaminated-but-inert weights; the pair of probes
  separates presence (recall) from deployment (branch split). The static benchmark's
  shadow is the converse statement: every post-2024 static τ-bench number carries an
  unmeasurable memorization component, and this instrument is how it becomes
  measurable.

- **Self-report is not a contamination defense, in either direction.** The recalling
  model flagged ten-digit ids as exactly where it would confabulate, then produced
  all six exactly. Its confidence report was anti-correlated with its memory. The
  declining model (gpt-5.5, same probe) is the other direction: "I don't know" is
  threefold ambiguous between absent memory, failed retrieval, and trained
  reluctance to recite benchmark internals. Recall probes are asymmetric evidence.
  They establish presence when they fire and nothing when silent.

- **Regurgitation auditing will go dark; behavioral metering survives.** GSM1k
  correlates score inflation with a model's propensity to regenerate benchmark text.
  That propensity is trainable away, and refusal is cheap to teach, so
  confession-based auditing stops working the moment labs patch it (the declining
  model above may be that future arriving early). The branch split cannot be
  suppressed by policy. Removing it requires the model to read the resampled world
  instead of its weights, which is decontamination of the behavior itself. A meter
  the subject can only game by becoming honest is the right kind of meter.

- **The static benchmark nests inside the generative one, which retires the Recht
  confound by construction.** Shipped-world seeds reproduce the original instance
  byte for byte (the faithfulness anchors), so original-versus-regenerated is a
  within-instrument, difficulty-controlled comparison: the shipped stratum gives the
  regular reading, the flipped strata give the reading only the seeded instrument
  can take. A drop confined to flipped strata cannot be reconstruction-hardness,
  because the control stratum IS the original world, re-run with fresh dialogue.

- **Lab-side hold-out is real, partial, unauditable — and the meter reads through
  it.** The cross-model recall asymmetry is plausibly supply-side decontamination
  observed in the wild: labs that eval on a benchmark filter it from training, and
  gpt-5.5's fade (paper-level facts intact, instance-level dark, "no continuation
  in memory" under completion framing) is what a working filter looks like. Claude's
  digit-perfect recall is what a failing one looks like — filtering the canonical
  repo misses the diaspora of forks, harnesses, and quoted logs that replicate the
  exact strings (GSM1k's replication finding, one level up). Jointly they show
  hold-out is heterogeneous across labs, and filter lists are secret, so static
  cross-lab numbers rest on unverifiable, unequal supplier promises. The behavioral
  meter converts the promise into a measurement (twelve blind episodes read one
  lab's filter as effective — 0/12 including shipped-branch worlds where memorized
  digits would have sufficed — and the recall probe read the other's as leaky), and
  regeneration removes the need for the promise: no filter has to work against
  worlds that do not exist until the seed draws them.

- **The clean positive control: memory that is provably present and provably correct
  is still behaviorally inert.** The seeded ablation is confounded (on a regenerated
  world the memorized golden is *wrong*, so failure could be ignorance). The
  discriminating control runs the ablation on the *shipped* world, where claude's
  memorized ids are exactly the ground truth (`SHIPPED_ABLATION.md`): 0.667 with the
  catalog readable, **0.000** with it blocked. Claude retries the outage and refuses
  to confirm the variant rather than plugging in the `7706410293` it recites
  digit-perfect. The mechanism is policy-grounding: the retail wiki requires
  confirming the target variant, and the agent follows the task over its priors, so
  the refusal is contingent on the policy demanding observation, and bounds A0/A1
  behavioral reliance for a policy-following agent, not A2. This refuted the naive
  prediction (logged in `RECALL_PROBE.md`) that correct memory would substitute for a
  blocked observation; the truth is stronger for the meter.

- **What was proven is a property of the meter, not of any agent.** Sensitivity: the
  scripted A0 ceiling, 0.44–0.72 across 13 specs. Specificity: the predicate-follower
  at 1.00 everywhere (regeneration leaves the task solvable) and the re-key null on
  the same memorizer (the reading comes from the branch flip alone). Live-model
  statements ride on the live strata comparisons and are n-limited until the sweep
  across spec shapes lands.

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
