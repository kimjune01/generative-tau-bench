# Prior-Art Search: Seeded Regeneration + Replay-Derived Oracle

## Scope of the claim

The claim is a method for converting an existing stateful tool-agent benchmark into an evergreen, contamination-resistant benchmark by:

1. seeded procedural regeneration of each task instance; and
2. deriving the grading oracle by replaying a canonical solution program on the regenerated state.

The domain restriction matters. This recipe only applies to database-shaped tasks satisfying all four preconditions:

1. State is enumerable typed entities with IDs.
2. The solution is a program over those entities and transforms under a seeded re-key/resampling.
3. The oracle is a deterministic function of the final state and can be checked by replay.
4. A constraint-preserving resampler exists.

Real-world SWE/repo coding tasks usually fail these preconditions: the state is unstructured source trees, the answer is a free-form patch, correctness depends on hand-written tests or hidden tests, and there is no obvious semantics-preserving seeded resampler. That is why LiveCodeBench and SWE-rebench mine fresh tasks rather than regenerate old ones. tau-bench, tau2-bench, AppWorld, and ToolSandbox are much closer to the valid regime.

## Executive verdict

Blunt answer: the broad phrase "dynamic/evergreen/contamination-resistant benchmark transformation" is not new. DyVal, DyVal 2/Meta Probing Agents, Benchmark Self-Evolving, metamorphic testing, GSM-Symbolic/GSM-SEM, LiveBench, LiveCodeBench, SWE-rebench, AntiLeak-Bench, PaCoST, and ProcGen already cover large chunks of that territory.

The defensible delta is narrower:

> For database-shaped stateful tool-agent benchmarks, define an alpha-renaming/constraint-resampling transformation that regenerates both the initial world and canonical solution program from a seed, then computes the grader by replaying that canonical program on the regenerated world.

That is not subsumed by DyVal-style dynamic evaluation, because DyVal transforms text/reasoning problems and usually relies on known generated answers, judging agents, or task-specific symbolic generation. It does not solve the stateful tool-agent oracle problem where correctness is a final world state reached through mutating APIs.

But it is also not a clean-room invention. tau-bench already uses a replay-to-final-state oracle in code. tau2-bench already uses programmatic task generation from atomic initialization, solution, and assertion functions. ProcGen already supplies the seeded procedural generalization protocol. The contribution is the combination and formalization for an existing class of stateful/database-shaped tool-agent benchmarks, plus an implementation and evidence that it actually reduces oracle maintenance and contamination sensitivity.

## (a) Prior art comparison

| Work | General transformation or standalone benchmark? | Covers stateful/tool-agent/database-shaped tasks? | Relation to this claim |
|---|---:|---:|---|
| DyVal, Zhu et al., ICLR 2024 | General dynamic-evaluation protocol, instantiated as graph-informed generation for reasoning tasks. | No. It targets math, logic, and algorithmic reasoning samples, not mutating tool-world tasks. | Strong prior art for "dynamic evaluation" and controllable generated instances. Does not give replay-derived final-state oracles for stateful tool agents. |
| DyVal 2 / Meta Probing Agents, Zhu et al., ICML 2024 | General problem-transformation protocol using probing/judging agents. | No, not in the database-shaped tool-agent sense. | Stronger threat to the broad novelty claim because it explicitly transforms original evaluation problems. Still text/problem transformation, not seeded DB regeneration plus replay oracle. |
| Benchmark Self-Evolving, Wang et al. | General framework that manipulates/reframes existing benchmark instances with multi-agent operations. | No verified coverage of stateful tool-agent DB benchmarks. | Prior art for evolving existing benchmarks without fully new data. It does not solve deterministic state replay or regenerated DB graders. |
| Metamorphic testing for LLM evaluation | General testing methodology: transform inputs and check expected relations between outputs. | Usually no; can apply to systems, but LLM evaluation papers mostly target NLP/reasoning robustness. | Prior art for oracle-lite transformations and invariance checks. Different from deriving a concrete final-state oracle by executing a canonical solution program. |
| GSM-Symbolic | Standalone/template benchmark derived from GSM8K-style math templates. | No. | Prior art for symbolic/template regeneration and contamination/fragility probing. It is math-only and answer derivation is arithmetic, not stateful replay. |
| GSM-SEM | Reusable stochastic perturbation framework for GSM-style and some reasoning benchmarks. | No. | Close in spirit on "fresh variants without re-annotation"; not about stateful tools, DB worlds, or replayed tool programs. |
| LiveBench | Standalone continuously updated benchmark with fresh recent sources and objective ground truth. | No; broad LLM tasks, not stateful tool-agent DB worlds. | Mining/curation freshness, not transformation of an arbitrary existing stateful benchmark. |
| LiveCodeBench | Standalone/live coding benchmark built by continuously collecting new contest problems. | No for database-shaped tool agents; yes for code evaluation, but coding tasks fail the stated preconditions. | Demonstrates why SWE/code freshness is mined, not procedurally regenerated from old tasks. |
| SWE-rebench | Automated mining pipeline for fresh interactive SWE tasks from GitHub repos. | It is agentic SWE, but not database-shaped under these preconditions. | Direct support for the user's domain-boundary claim: repo tasks require mining because final correctness is patch/test based, not replay-checkable DB state. |
| ProcGen | Standalone RL benchmark/protocol using procedurally generated environments and train/test level splits. | Stateful environments, but not LLM tool-agent DB benchmarks. | Strong prior art for seeded procedural generation, held-out seeds, and measuring memorization/generalization. Does not address tool-call replay or benchmark transformation. |
| AntiLeak-Bench | Automated benchmark construction around updated real-world knowledge. | No. | Prior art for anti-contamination automation. It constructs new knowledge-based samples; it does not transform stateful benchmarks by seeded DB replay. |
| PaCoST | Contamination detection method using paired counterparts and confidence tests. | No. | Prior art for paired counterpart construction and contamination detection, not for making new evergreen benchmark instances or replay-derived graders. |
| tau-bench | Standalone stateful tool-agent benchmark. | Yes. | Very close on oracle: code computes ground-truth final DB hash by replaying expected actions. But tasks are fixed; no seeded regeneration of fresh instances. |
| tau2-bench | Standalone stateful conversational-agent benchmark with a compositional task generator. | Yes. | Closest prior art. It programmatically composes tasks from initialization, solution, and assertion functions. But the paper frames this as an internal task-generation/evaluation mechanism, not as a general method for transforming arbitrary existing benchmarks into evergreen ones via replay-derived oracles. |
| AppWorld | Standalone interactive coding/tool benchmark over simulated apps with state-based unit tests. | Mostly yes: app/database-shaped enough for this recipe in many tasks. | Close stateful-evaluation neighbor. Uses programmatic tests and collateral-damage checks, not a stated replay-derived canonical-solution oracle transformation. |
| ToolSandbox | Standalone stateful conversational tool-use benchmark with dynamic milestone/final evaluation. | Mostly yes. | Close stateful tool-use environment, but not a general transformation and not verified as using seeded regeneration plus replay-derived oracle. |

## (b) Specific replay-oracle + seeded-regeneration prior art

I did not find a paper that explicitly proposes the exact method:

> take an existing database-shaped stateful tool-agent benchmark, seeded-regenerate each instance and canonical solution program, and derive each fresh grader by replaying that solution program on the regenerated state.

What exists:

- tau-bench already implements the replay-derived oracle half. Its `calculate_reward()` computes the agent DB hash, resets the DB, replays the task's expected actions, computes the ground-truth DB hash, and compares. The task files contain expected action sequences. That means "replay a canonical solution to produce the final-state oracle" is prior art in this domain.
- tau2-bench already implements the programmatic-generation half. Its paper says the compositional task generator builds diverse verifiable tasks from atomic components defined by initialization, solution, and assertion functions. It verifies correctness by applying initialization and solution functions and checking assertions, and in telecom uses assertion functions for task success.
- AppWorld and ToolSandbox establish that stateful tool-agent benchmarks can use programmatic final-state checks. They are adjacent but not the exact replay-oracle/seeded-regeneration transformation.

What I could not verify:

- I did not verify tau2-bench's current repo internals line by line. The paper is enough to establish that it has init/solution/assertion generation, but not enough to prove whether some branch already has seeded per-instance regeneration with replay-derived graders.
- I did not find a tau2-bench statement framing its generator as an evergreen contamination-resistance transformation for arbitrary existing benchmarks. The framing I verified is "compositional task generator" for its telecom domain and task coverage/complexity.
- I did not verify every post-2025 follow-up in the tau3-bench/tau-Voice/tau-Knowledge family. tau3 release notes mention task fixes and new modalities/knowledge, not the exact method, but this is an active family and the closest group to doing it.

## (c) Blunt novelty verdict

As a paper claim, "we make benchmarks dynamic/evergreen/contamination-resistant" is too broad and would be rejected as subsumed by DyVal/DyVal2, Benchmark Self-Evolving, LiveBench-style updating, AntiLeak-Bench, GSM perturbation frameworks, and old procedural-generation practice.

As a domain-specific methods claim, it is real but narrow:

> A reusable transformation for database-shaped stateful tool-agent benchmarks that combines seeded constraint-preserving regeneration with replay-derived final-state oracles, allowing fresh instances and graders to be generated without re-annotation or mining new real tasks.

The precise defensible delta is:

1. DyVal-style methods transform problem statements; this transforms a relational world plus the canonical action program.
2. LiveBench/LiveCodeBench/SWE-rebench get freshness by mining/curating new tasks; this gets freshness by seed-driven regeneration within an existing benchmark domain.
3. tau-bench has replay-derived final-state grading but fixed tasks; this adds seeded regeneration of DB, instruction references, outputs, and canonical solution.
4. tau2-bench has compositional programmatic generation but still uses explicit assertion functions and is framed as internal benchmark construction; this makes regeneration a general conversion recipe for existing database-shaped benchmarks and tries to make the oracle derived from replay rather than separately asserted.
5. ProcGen has seed splits and procedural worlds; this ports that protocol to LLM tool-agent benchmarks with mutating APIs and final-state grading.

This is publishable only if it is more than a position paper. Minimum bar:

1. Implement it on at least one real existing benchmark, preferably tau-bench retail/airline or AppWorld, not only a toy.
2. Formalize the preconditions and prove or test the key invariants: ID re-keying, referential integrity, solvability, replay determinism, and preservation of task semantics under resampling.
3. Show oracle-maintenance reduction: fresh initial states and graders are generated without hand annotations, with audited failure rates.
4. Show contamination behavior empirically: train/few-shot/cache on original or train seeds, evaluate on held-out seeds, and show the gap.
5. Report paired statistics using the same seed set across models; otherwise procedural variance will swamp model comparisons.
6. Address multiple-valid-solution cases. Exact DB hashing is brittle unless the final-state equivalence relation is carefully canonicalized.
7. Address generator leakage. Public generators prevent memorizing individual instances, not overfitting to generator templates. A serious leaderboard needs hidden seed ranges, rotating generators, held-out task families, or private challenge rounds.
8. Compare explicitly against tau2-bench. That is the nearest miss and the main novelty threat.

Closest and most likely to have done it already:

- tau-bench/tau2/tau3 authors. They already have replay grading, stateful domains, and a compositional generator.
- AppWorld authors. Their app-world engine and state-based unit tests make seeded generation plausible.
- ToolSandbox authors. Their stateful tool execution and milestone/final evaluation are adjacent.
- DyVal/DyVal2 authors. They own the general dynamic-evaluation framing but would need to move into stateful tool worlds.
- LiveBench/LiveCodeBench/SWE-rebench maintainers. They own the contamination-free benchmark narrative, but their current mechanism is freshness by mining/curation, not replay-regeneration.

Bottom line: not novel as "dynamic evaluation"; not novel as "procedural generation"; not novel as "replay final-state oracle." Potentially novel as the specific conversion recipe for database-shaped stateful tool-agent benchmarks, if backed by a working implementation and hard comparison to tau2-bench.

## Sources

- DyVal: Dynamic Evaluation of Large Language Models for Reasoning Tasks. Zhu et al. ICLR 2024. https://arxiv.org/abs/2309.17167
- Dynamic Evaluation of Large Language Models by Meta Probing Agents / DyVal 2. Zhu et al. ICML 2024. https://arxiv.org/abs/2402.14865
- Benchmark Self-Evolving: A Multi-Agent Framework for Dynamic LLM Evaluation. Wang et al. https://arxiv.org/abs/2402.11443
- GSM-Symbolic: Understanding the Limitations of Mathematical Reasoning in Large Language Models. Mirzadeh et al. https://arxiv.org/abs/2410.05229
- GSM-SEM: Benchmark and Framework for Generating Semantically Variant Augmentations. Singh et al. https://arxiv.org/abs/2605.07053
- LLMORPH: Automated Metamorphic Testing of Large Language Models. Cho et al. https://arxiv.org/abs/2603.23611
- LGMT: Logic-Grounded Metamorphic Testing for Evaluating the Reasoning Reliability of LLMs. Zhou et al. https://arxiv.org/abs/2605.23965
- LiveBench: A Challenging, Contamination-Limited LLM Benchmark. White et al. https://arxiv.org/abs/2406.19314
- LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for Code. Jain et al. https://arxiv.org/abs/2403.07974
- SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of Software Engineering Agents. Badertdinov et al. https://arxiv.org/abs/2505.20411
- AntiLeakBench: Preventing Data Contamination by Automatically Constructing Benchmarks with Updated Real-World Knowledge. Wu et al. https://arxiv.org/abs/2412.13670
- PaCoST: Paired Confidence Significance Testing for Benchmark Contamination Detection in Large Language Models. Zhang et al. https://arxiv.org/abs/2406.18326
- Leveraging Procedural Generation to Benchmark Reinforcement Learning / ProcGen. Cobbe et al. https://arxiv.org/abs/1912.01588
- tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. Yao et al. https://arxiv.org/abs/2406.12045
- tau-bench GitHub. https://github.com/sierra-research/tau-bench
- tau-bench replay/hash code. https://raw.githubusercontent.com/sierra-research/tau-bench/main/tau_bench/envs/base.py
- tau-bench task action examples. https://raw.githubusercontent.com/sierra-research/tau-bench/main/tau_bench/envs/retail/tasks.py
- tau2-bench: Evaluating Conversational Agents in a Dual-Control Environment. Barres et al. https://arxiv.org/abs/2506.07982
- tau2-bench ar5iv HTML, used for generator/evaluation details. https://ar5iv.labs.arxiv.org/html/2506.07982
- tau2-bench GitHub. https://github.com/sierra-research/tau2-bench
- AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents. Trivedi et al. https://arxiv.org/abs/2407.18901
- ToolSandbox: A Stateful, Conversational, Interactive Evaluation Benchmark for LLM Tool Use Capabilities. Lu et al. https://arxiv.org/abs/2408.04682
