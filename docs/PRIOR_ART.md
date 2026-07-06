# Prior-art search: replay-oracle + seeded regeneration for LLM agent benchmarks

Date searched: 2026-07-01.

## Blunt verdict

The full proposal is a useful benchmark-engineering pattern, not a cleanly new benchmark idea. Four of the five pieces are well-trodden:

- procedural/seeded generation and train/test seed splits are ProcGen-era RL practice;
- regenerating contamination-resistant variants is already central to GSM-Symbolic-style and live/dynamic benchmark work;
- tau-bench already uses expected action sequences and a replay-to-final-state hash in code;
- paired/common-instance comparisons are basic experimental design and are already normal in NLP significance testing, even if people rarely call them "common random numbers".

The potentially publishable nugget is narrower: **for stateful tool-agent benchmarks, publish a deterministic generator that emits both the initial relational world and a canonical solution program, then derive the oracle by replaying that solution program rather than hand-writing assertions or hiding instances.** I did not find a prior LLM-agent benchmark that states exactly that combination as the contamination defense. tau2-bench gets close with programmatic task generation from init/solution/assert functions, but it still keeps explicit assertion functions and sampled task suites rather than framing seeded regeneration as the anti-leakage mechanism.

So: real contribution if implemented and evaluated well; easy to dismiss as repackaging if presented only as a concept paper.

## The five pieces

### 1. Operational oracle: replay golden actions and hash final DB state

Closest prior art:

- **tau-bench**. The paper says evaluation compares the final database state to an annotated goal state. The code is more specific: `calculate_reward()` hashes the agent-mutated DB, resets the DB, replays the task's expected actions, hashes the resulting ground-truth DB, and compares the hashes. The task files store `"actions"` as the expected sequence.
  - Paper: https://arxiv.org/abs/2406.12045
  - Code: https://github.com/sierra-research/tau-bench
  - Relevant raw files:
    - `tau_bench/envs/base.py`: https://raw.githubusercontent.com/sierra-research/tau-bench/main/tau_bench/envs/base.py
    - `tau_bench/envs/retail/tasks.py`: https://raw.githubusercontent.com/sierra-research/tau-bench/main/tau_bench/envs/retail/tasks.py
- **AppWorld** uses programmatic state-based unit tests over a simulated app world, including checking collateral damage. This is close in spirit but not "replay golden actions, hash state".
  - https://arxiv.org/abs/2407.18901
- **ToolSandbox** uses stateful tool execution and dynamic milestone/final evaluation. Close for stateful evaluation, less close for replay-derived oracle.
  - https://arxiv.org/abs/2408.04682
- **Agent-Diff** defines success by expected state changes rather than trace matching. This is directly adjacent, but again uses a state-diff contract, not a replayed canonical solution as oracle.
  - https://arxiv.org/abs/2602.11224

Assessment: **not novel** as an oracle. tau-bench already does it in the relevant setting.

### 2. Regeneration instead of secrecy

Closest prior art:

- **GSM-Symbolic** generates symbolic-template variants of GSM8K to test whether models solve variants rather than memorize fixed instances.
  - https://arxiv.org/abs/2410.05229
- **GSM-SEM** goes further with stochastic semantic variants and explicitly argues for fresh variants without re-annotation.
  - https://arxiv.org/abs/2605.07053
- **LiveBench** and **LiveCodeBench** combat contamination by continuously adding recent, objective-ground-truth questions rather than relying on a fixed secret set.
  - LiveBench: https://arxiv.org/abs/2406.19314
  - LiveCodeBench: https://arxiv.org/abs/2403.07974
- **Dynabench** is the classic dynamic benchmark platform: human/model-in-the-loop data collection to keep benchmarks from saturating.
  - https://arxiv.org/abs/2104.14337
- **BetterBench** (Reuel et al.; 46 best-practice criteria assessed over 24 benchmarks) treats contamination/gaming mitigation as a benchmark best practice. Our proposal is a different *kind* of mitigation: regenerate rather than hide. (The specific "unique identifiers / encrypt evaluation instances" mechanisms are in the checklist body, not the abstract — not re-verified against source in the last pass; keep the contrast general until confirmed.)
  - https://arxiv.org/abs/2411.12990

Assessment: **mostly reinvention** at the benchmark-strategy level. The specific application to tau-bench-style relational tool worlds is more interesting.

### 3. Seeded procedural generation, roguelike style

Closest prior art:

- **ProcGen Benchmark** is the obvious ancestor: procedurally generated game-like environments, designed specifically to test RL sample efficiency and generalization.
  - https://arxiv.org/abs/1912.01588
- **Quantifying Generalization in RL (CoinRun; Cobbe et al.)** is the load-bearing citation for the orbit-min-entropy threshold. Verified from the paper (§3.2): "substantial overfitting occurs when there are less than 4,000 training levels. Even with 16,000 training levels, overfitting is still noticeable. Agents perform best when trained on an unbounded set of levels." This sets the *scale* at which method-memorization stops being contamination and becomes skill — sobering for our hand-authored ~25-template orbit (orders of magnitude below even the 16,000 mark), and the empirical basis for making structural class generation the load-bearing future work (see DESIGN, "orbit min-entropy").
  - https://arxiv.org/abs/1812.02341
- **Procedural Knowledge in Pretraining Drives Reasoning (Ruis et al.)** grounds the claim that the *method*, not the answer, is the unit models absorb: for reasoning tasks, influential pretraining documents demonstrate how-to-solve (formulae/code) rather than containing the answer, and the same document is influential across many questions in a task. Supports "method is memorizable/learnable from data" — hence regeneration re-prices contamination rather than defeating it.
  - https://arxiv.org/abs/2411.12580
- **NeurIPS 2020 ProcGen competition** standardized sample-efficiency/generalization evaluation over ProcGen.
  - https://arxiv.org/abs/2103.15332
- **ProcTHOR** uses procedural generation for embodied AI environments.
  - https://arxiv.org/abs/2206.06994
- **Avalon** uses procedurally generated 3D worlds for RL generalization.
  - https://arxiv.org/abs/2210.13417

Assessment: **not novel**. The LLM-agent benchmark adaptation is useful but derivative.

### 4. Train/test seed split as memorization/generalization meter

Closest prior art:

- **ProcGen** is again the cleanest prior art: train on a finite distribution of levels/seeds and evaluate on held-out procedural levels/seeds to measure generalization.
  - https://arxiv.org/abs/1912.01588
- **GSM-Symbolic** and **GSM-SEM** provide a language-benchmark analogue: evaluate families of generated variants, exposing brittleness to instantiation changes.
  - https://arxiv.org/abs/2410.05229
  - https://arxiv.org/abs/2605.07053
- **PaCoST** is adjacent for contamination measurement: it constructs paired counterparts and tests confidence differences between original benchmark items and distribution-matched variants.
  - https://arxiv.org/abs/2406.18326

Assessment: **not novel**, but good to include. For agents, it can make overfitting visible if you actually publish train-seed and held-out-seed protocols.

### 5. Shared seed set across models for paired/common-random-numbers comparison

Closest prior art:

- **Common random numbers** are a standard simulation variance-reduction technique: compare systems on matched random draws so instance difficulty cancels in the difference.
  - Overview: https://en.wikipedia.org/wiki/Variance_reduction#Common_random_numbers
- **McNemar's test** is the standard paired binary-outcome test for two classifiers/systems evaluated on the same items.
  - https://en.wikipedia.org/wiki/McNemar%27s_test
- NLP has long used paired significance tests such as paired bootstrap/randomization tests over the same examples. This is not usually branded as CRN, but statistically it is the same reason leaderboards evaluate all models on the same test set.
- **PaCoST** uses paired counterpart examples for contamination detection, not cross-model leaderboard comparison.
  - https://arxiv.org/abs/2406.18326

Assessment: **not novel statistically**. It may be underused/understated in LLM-agent benchmark papers. Calling it out and reporting paired intervals/McNemar/exact tests would be a quality improvement.

## Combination prior art

The closest combinations I found:

- **tau-bench**: stateful relational/API environment + expected action sequence + replay-derived final DB hash.
  - https://arxiv.org/abs/2406.12045
  - https://github.com/sierra-research/tau-bench
- **tau2-bench / tau3-bench**: extends the tau-bench family with a compositional task generator. The paper describes atomic subtasks with initialization, solution, and assertion functions, and verifies task correctness by applying initialization and solution and checking assertions.
  - Paper: https://arxiv.org/abs/2506.07982
  - Repo: https://github.com/sierra-research/tau2-bench
- **AppWorld**: synthetic app world + stateful APIs + programmatic state-based unit tests.
  - https://arxiv.org/abs/2407.18901
- **ToolSandbox**: stateful tool-use benchmark with dynamic evaluation over arbitrary trajectories.
  - https://arxiv.org/abs/2408.04682
- **LiveBench/LiveCodeBench**: contamination resistance via continual fresh objective-ground-truth instances.
  - https://arxiv.org/abs/2406.19314
  - https://arxiv.org/abs/2403.07974
- **ProcGen**: seeded procedural worlds + train/test generalization protocol.
  - https://arxiv.org/abs/1912.01588

What I did **not** find: a benchmark paper that explicitly combines **tau-bench-style replay oracle** with **public seeded regeneration of fresh relational/API task instances** as the main answer to benchmark leakage. tau2-bench is the one that should worry you most because it already has solution functions in a compositional generator. Your delta is to remove/derivatize hand assertions where possible, re-key/resample worlds by seed, and make leakage resistance a first-class protocol.

## Answers to the specific questions

### (a) Closest prior art for each piece and the combination

See the sections above. In short:

- Operational oracle: tau-bench code; AppWorld/ToolSandbox/Agent-Diff as neighboring state-based evaluators.
- Regeneration: GSM-Symbolic, GSM-SEM, LiveBench, LiveCodeBench, Dynabench, AntiLeak-Bench.
- Seeded procedural generation: ProcGen, ProcTHOR, Avalon.
- Train/test seed split: ProcGen; GSM-Symbolic/GSM-SEM variants as language analogues.
- Shared seeds/paired comparison: common random numbers, McNemar, paired NLP significance tests.
- Combination: tau2-bench is closest, followed by tau-bench + ProcGen + LiveBench as the conceptual merge.

### (b) Has anyone combined replay-based oracle with seeded regeneration so goldens and graders re-derive for free?

I could not verify an exact prior instance in LLM tool/agent benchmarking.

The nearest miss is **tau2-bench**. It has programmatic generation from atomic initialization, solution, and assertion functions, and verifies generated tasks by applying solutions and assertions. But the paper still describes assertion functions as part of the task definition, and the repo/paper do not appear to position seeded regeneration as a contamination-resistance mechanism where goldens and graders are re-derived for arbitrary fresh seeds.

The other near miss is **tau-bench** itself: it already replays expected actions to derive a state hash, but the tasks are fixed and stored. It does not, in the original form I checked, regenerate new DB/task/action triples from seeds.

So the claim should be narrow: **"To our knowledge, no published LLM agent benchmark uses a public seeded generator to regenerate both a stateful tool-world instance and its replay-derived oracle, allowing fresh contamination-resistant evaluation without hidden goldens."** Add "to our knowledge" unless you complete a deeper systematic review.

### (c) Has anyone used shared-seed paired evaluation / common random numbers for cross-model LLM benchmarking?

I did not find a clear LLM benchmark paper saying "we use common random numbers/shared seeds" for cross-model comparison. But the method is not new:

- Every fixed-test-set benchmark already evaluates models on common items.
- Paired bootstrap/randomization tests and McNemar-style tests are standard for comparing systems on common examples.
- The CRN framing is standard in simulation, not an LLM novelty.

The possible publishable point is practical: **procedural LLM-agent benchmarks should sample one seed set per evaluation round and run every model on exactly that seed set, then report paired uncertainty**, instead of letting each model see independently sampled instances. That is a good protocol recommendation, not a research invention.

### (d) Real contribution or repackaging?

Bluntly: **as written, it is 70% repackaging and 30% real contribution.** The real part is the engineering synthesis for stateful tool-agent benchmarks, especially if you actually eliminate manual oracle maintenance and quantify contamination/memorization.

What to add to make it publishable:

1. **Build the generator, not just the argument.** A paper without a working tau-bench-like domain generator will read like a benchmark-design note.
2. **Prove/validate invariants.** Show that ID re-keying preserves task semantics; show resampling constraints preserve solvability; show replayed golden actions produce canonical expected state.
3. **Separate equivalence from exactness.** Final DB hashing is brittle when multiple valid states exist. You need canonicalization or an equivalence relation for benign differences, or you will recreate tau-bench task-quality problems.
4. **Show contamination sensitivity.** Fine-tune or prompt-cache on train seeds/goldens, then demonstrate high train-seed performance and lower held-out-seed performance. Otherwise the "memorization meter" is just asserted.
5. **Report paired statistics.** Same seeds for every model; give paired confidence intervals, McNemar/exact tests for binary success, and variance reduction compared with independent seed sampling.
6. **Adversarially audit the generator.** A public generator can be learned. You need to distinguish memorizing seeds, learning the generator distribution, and genuine tool-use competence.
7. **Address leakage of the generator itself.** Regeneration prevents memorizing instances, not overfitting to generator templates. You need rotating generators, held-out task families, or private seed ranges if leaderboard gaming matters.
8. **Compare against tau2-bench explicitly.** Your novelty claim lives or dies against tau2-bench's compositional generator.

Who could scoop this:

- **tau-bench/tau2/tau3 authors**: they already own the benchmark family, have the generator direction, and can add seeded regeneration faster than outsiders.
- **AppWorld / ToolSandbox-style teams**: they already have stateful API worlds and programmatic evaluation.
- **LiveBench/LiveCodeBench-style maintainers**: they own the contamination-free benchmark narrative and could add procedural/stateful agent tasks.
- **Agent-Diff / enterprise API benchmark authors**: state-diff-based evaluation plus generated enterprise tasks is a short step from this.
- **RL generalization people**: they already understand seed splits and CRN; they could port the ProcGen protocol to agents.

## Novelty map

| Component | Novelty verdict | Why |
|---|---:|---|
| Replay final-state oracle | Low | tau-bench code already does this. |
| Regenerate instead of hide | Low-medium | Known from GSM-Symbolic/GSM-SEM/live benchmarks; less developed for relational tool-agent worlds. |
| Seeded procedural instances | Low | ProcGen and many simulation benchmarks. |
| Train/test seed split | Low | ProcGen standard. |
| Shared seed paired eval | Low | CRN/McNemar/paired tests are old; useful but not new. |
| Replay oracle + seeded regeneration for stateful tool-agent DBs | Medium | I did not find exact prior art; tau2-bench is close. |
| Public auditable generator as anti-contamination mechanism | Medium | Strong if paired with empirical leakage/memorization evidence. |

## Caveats / things I could not fully verify

- I verified tau-bench's replay/hash behavior from the GitHub raw source, but did not clone and run the repository.
- I did not do a full Semantic Scholar citation-graph sweep. The "no exact prior art found" claim is therefore a search-based assessment, not a proof.
- tau2-bench/tau3-bench repository internals are evolving. I relied mainly on the paper and README-level docs plus the public repo state visible during search.
- Some 2026 search results may be very recent. If submitting, rerun the search immediately before writing related work.

## Sources

- tau-bench paper: https://arxiv.org/abs/2406.12045
- tau-bench GitHub: https://github.com/sierra-research/tau-bench
- tau-bench replay/hash code: https://raw.githubusercontent.com/sierra-research/tau-bench/main/tau_bench/envs/base.py
- tau-bench task action examples: https://raw.githubusercontent.com/sierra-research/tau-bench/main/tau_bench/envs/retail/tasks.py
- tau2-bench paper: https://arxiv.org/abs/2506.07982
- tau2/tau3-bench GitHub: https://github.com/sierra-research/tau2-bench
- GSM-Symbolic: https://arxiv.org/abs/2410.05229
- GSM-SEM: https://arxiv.org/abs/2605.07053
- LiveBench: https://arxiv.org/abs/2406.19314
- LiveCodeBench: https://arxiv.org/abs/2403.07974
- Dynabench: https://arxiv.org/abs/2104.14337
- BetterBench: https://arxiv.org/abs/2411.12990
- ProcGen Benchmark: https://arxiv.org/abs/1912.01588
- NeurIPS 2020 ProcGen competition: https://arxiv.org/abs/2103.15332
- ProcTHOR: https://arxiv.org/abs/2206.06994
- Avalon: https://arxiv.org/abs/2210.13417
- AppWorld: https://arxiv.org/abs/2407.18901
- ToolSandbox: https://arxiv.org/abs/2408.04682
- Agent-Diff: https://arxiv.org/abs/2602.11224
- PaCoST: https://arxiv.org/abs/2406.18326
- CheckList: https://arxiv.org/abs/2005.04118
- AntiLeak-Bench: https://arxiv.org/abs/2412.13670
- Common random numbers overview: https://en.wikipedia.org/wiki/Variance_reduction#Common_random_numbers
- McNemar's test overview: https://en.wikipedia.org/wiki/McNemar%27s_test
