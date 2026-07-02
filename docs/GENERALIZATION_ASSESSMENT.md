# Generalization Assessment

Blunt verdict: the proposed triangulation is **plausible but not sufficient** for a
strong NeurIPS Datasets-and-Benchmarks-style generalization claim. It is enough to
argue that the method has a well-defined applicability class and that tau-bench is
not a toy. It is not enough to convince a skeptical reviewer that the method
generalizes across the class rather than across one benchmark codebase.

The central problem is independence. Retail and airline are different domains, but
they are still tau-bench: same authorship lineage, same benchmark philosophy, same
style of task authoring, same environment abstraction, same replay-oracle premise,
and likely similar assumptions about entities, tools, and graders. A theorem plus
two tau-bench schemas plus inspection of other benchmarks will read as "one
implementation, one family, many words about scope." For a methods paper, that is
a weak generalization story.

## Answers

### (a) Is the triangulation sufficient?

No, not as stated. I would expect reviewers to push back that this is a
single-benchmark-family result presented as a general transformation. The theorem
helps define the class, but it does not establish that real benchmarks in the
class can be transformed without hidden domain work. The hard part is not the
abstract alpha-renaming argument; it is discovering and enforcing the
constraint-preserving resampler, preserving semantic intent, handling
multiple-valid-final-states, and integrating with each benchmark's grader/user
simulation conventions.

The paper can claim:

- "For benchmarks satisfying these four preconditions, the transformation is sound
  by construction."
- "We instantiate it on tau-bench retail, and possibly airline if actually
  implemented."
- "Several existing benchmarks appear to satisfy the preconditions by inspection."

The paper should not strongly claim:

- "We demonstrate generalization across database-shaped stateful tool-agent
  benchmarks."
- "This converts the class of such benchmarks into evergreen benchmarks" unless at
  least one independent non-tau instantiation works end to end.

The likely reviewer objection is straightforward: the theorem proves conditional
soundness, but the empirical evidence only shows that one benchmark family happens
to satisfy the conditions in an implementation-friendly way.

### (b) Does retail + airline count as generalization evidence?

It counts, but weakly. It is within-family schema variation, not independent
generalization. It helps against the narrow criticism "you hard-coded retail table
names." It does not help much against the stronger criticism "your method only
works because tau-bench already has exactly the replay/action/oracle structure you
need."

Minimum independent second instantiation:

1. Run end-to-end on one non-tau benchmark with a different codebase and grader.
   AppWorld is the best candidate if the goal is to show database-shaped app state
   plus programmatic state-based evaluation. ToolSandbox is also reasonable, but
   its dynamic milestone evaluation may force more adaptation.
2. The second instantiation does not need the full suite. A serious subset is
   enough if it is principled: e.g. 25-50 tasks spanning several apps/scenarios,
   with a published adapter, generated seeds, replay/check determinism, failure
   accounting, and regenerated-oracle audit.
3. The paper should report engineering effort and failed cases. If AppWorld has
   750 tasks and only 40 cleanly satisfy the preconditions, that is still useful,
   but the denominator must be visible.

If the authors actually run full tau-bench retail and airline, that upgrades the
paper from "retail-only prototype" to "complete tau-bench-family conversion." It
does not make it a class-level empirical demonstration.

Local verification note: in this checkout, the implemented re-key invariance test
is retail-only over 115 retail test tasks and 5 seeds, explaining 575 checks. I did
not verify an airline implementation in the local `gtau` code. Treat "airline" as
proposed or external evidence unless there is another result outside this tree.

### (c) Is a precondition-membership survey convincing?

Not on its own. It is useful as a scope map, not as evidence that the
transformation ports. Inspection can establish that a benchmark probably has
enumerable state, programmatic tools, and deterministic graders. It cannot
establish that the resampler preserves task semantics, that all private intent is
remapped, that final-state equivalence is robust, or that the benchmark exposes
enough canonical solution structure to replay.

For tau2-bench, inspection is relatively credible because the paper explicitly
describes a compositional task generator with initialization, solution, and
assertion-style components. For AppWorld and ToolSandbox, inspection is weaker:
they clearly have stateful execution and programmatic evaluation, but that is not
the same as "canonical replay-derived oracle under seeded regeneration."

At least one non-tau benchmark should be executed. Without that, the survey should
be framed as "applicability analysis" or "candidate benchmarks," not as
generalization evidence.

### (d) How rigorous must the theorem be?

A stated proposition with a precise proof sketch is the minimum. An informal
paragraph will not carry weight because the theorem is doing too much rhetorical
work.

The formalism does not need to be mechanized, but it should define:

- A world state `S` as typed finite records with identifiers.
- A bijective seeded transformation `T_seed` over identifiers and resampled fields.
- An action program `P` whose arguments transform under `T_seed`.
- Tool transition semantics `step(S, a) -> S'` or `Error`.
- Oracle `O(S, P) = canonical_hash(replay(P, S))`.
- The exact equivariance/soundness condition: replaying the transformed canonical
  program on the transformed/resampled state produces a deterministic oracle for
  the transformed instance, and any agent final state is scored against that
  regenerated oracle.
- The role of constraint preservation: the theorem is conditional on transformed
  instances remaining well-typed, referentially valid, and semantically solvable.
- A canonicalization/equivalence relation for benign final-state variation; exact
  hash equality is too brittle to be the general theorem unless the benchmark
  already has unique final states.

The proof should be a real proposition, not a vibe: induction over the action
sequence is enough for pure re-keying if each tool transition is equivariant under
the id map. For structural resampling, the theorem is weaker: soundness follows
only after the generator certifies that the canonical program executes and the
oracle is recomputed. That distinction should be explicit.

A formal appendix is preferable. A mechanized proof is unnecessary.

### (e) Single minimal addition that flips this to sufficient

Run one independent non-tau benchmark end to end. My recommendation is AppWorld,
because its paper describes 9 apps, 457 APIs, 750 tasks, and state-based unit-test
evaluation with collateral-damage checks, making it close enough to the
precondition class but independent enough from tau-bench to matter.

The minimal sufficient addition:

- Implement a schema-agnostic adapter on AppWorld for a nontrivial subset.
- Generate multiple held-out seeds per task.
- Replay or execute a canonical solution/checker to derive the oracle or
  regenerated expected final-state assertions.
- Report pass/fail of the generator itself: referential integrity, deterministic
  replay, oracle derivation, task solvability, and any rejected/resampled cases.
- Run at least one agent/model on original vs regenerated or train-seed vs
  held-out-seed instances, mainly to show the benchmark still functions
  behaviorally.

This addition would not need to show a big performance result. The point is
portability of the transformation.

## Evidentiary Weight

Ranked strongest to weakest:

1. **Leg 2, empirical execution.** Actual transformed benchmark instances with
   regenerated oracles are the main evidence. Retail full-suite evidence matters;
   airline matters if implemented, but both are tau-family.
2. **Leg 1, theorem.** Strong for conditional soundness. Weak for empirical
   portability. It defines the valid class but does not prove membership is easy
   or non-domain-specific in real benchmarks.
3. **Leg 4, boundary/failure on SWE/repo tasks.** Useful for construct validity.
   It shows the class is not post-hoc "everything we tested." But it is mostly
   negative evidence and does not prove positive generalization.
4. **Leg 3, precondition survey.** Useful for positioning and future work. Weak as
   proof. Inspection without execution misses exactly the failure modes that matter
   for generators.

If airline is not actually implemented, Leg 2 is currently "retail only" and the
paper is much weaker. If airline is implemented but via tau-bench-specific code,
Leg 2 is still within-family.

## Stress Tests Reviewers Will Apply

- **Schema agnosticism:** Does the implementation discover typed entities,
  identifiers, foreign keys, tool arguments, and text references generically, or
  does it encode retail/airline namespaces by hand?
- **Semantic preservation:** Are regenerated tasks behaviorally the same task
  class, or merely syntactically fresh?
- **Constraint accounting:** How many candidate regenerations are rejected? What
  constraints were hand-authored? Does the paper report the failure denominator?
- **Oracle uniqueness:** Does exact final-state hashing unfairly reject valid
  alternate end states? If so, what equivalence relation is used?
- **User simulator leakage:** Are private intents and user-visible strings
  transformed consistently, or does the prompt reveal stale ids/answers?
- **Generator overfitting:** Seed rotation prevents memorizing concrete instances,
  not overfitting to generator templates. The paper needs held-out seeds and,
  ideally, held-out task classes.
- **Contamination claim:** Cosmetic re-keying only addresses verbatim leakage.
  Structural regeneration is needed for a strong contamination-resistance claim.

## Source-Grounded Facts

- Tau-bench evaluates dynamic conversations between an LLM-simulated user and a
  tool-using agent, and its abstract says evaluation compares final database state
  with annotated goal state; it also introduces `pass^k` and reports `pass^8 <25%`
  in retail for gpt-4o-like agents. Source: tau-bench arXiv abstract,
  https://arxiv.org/abs/2406.12045.
- Tau2-bench's abstract explicitly claims a compositional task generator that
  programmatically creates diverse, verifiable tasks from atomic components, with a
  dual-control telecom domain. Source: tau2-bench arXiv abstract,
  https://arxiv.org/abs/2506.07982.
- AppWorld's abstract describes an execution environment with 9 apps, 457 APIs,
  750 tasks, and robust programmatic evaluation with state-based unit tests plus
  collateral-damage checks. Source: AppWorld arXiv abstract,
  https://arxiv.org/abs/2407.18901.
- ToolSandbox's abstract describes stateful tool execution, implicit state
  dependencies, an on-policy user simulator, and dynamic evaluation over
  intermediate and final milestones. Source: ToolSandbox arXiv abstract,
  https://arxiv.org/abs/2408.04682.
- SWE-bench consists of 2,294 real GitHub issue/PR problems across 12 Python
  repositories where the model edits a codebase to resolve an issue; this supports
  treating repo-level SWE as a different regime from enumerable database-shaped
  tool worlds. Source: SWE-bench arXiv abstract,
  https://arxiv.org/abs/2310.06770.

## Claims I Cannot Verify Here

- I cannot verify from this workspace that tau-bench airline has been converted
  with the same generator/replay machinery. The local generator/re-key modules are
  retail-specific.
- I cannot verify that tau2-bench, AppWorld, or ToolSandbox fully satisfy all four
  preconditions without inspecting and executing their current repositories. The
  cited abstracts support candidacy, not proof.
- I cannot verify that "575/575 faithful" means more than 115 retail tasks times 5
  seeds in the local test. That is still useful, but it is not cross-schema
  evidence by itself.
