# Fan-out: the executable-oracle class + best independent second demonstration

**Question.** The method = seeded regeneration of a benchmark instance + a *replay/
execution-derived oracle* (re-run a canonical reference procedure on the regenerated
input). Validated on tau-bench retail+airline (same family). To earn generalization we
need one *independent* second demonstration, and the right applicability-class framing.

**Four preconditions.** (1) state = enumerable typed entities with ids; (2) solution =
declarative program over them (not arbitrary code); (3) oracle = deterministic function
of final state / execution result (ideally native); (4) constraint-preserving resampler.

**Funnel.** Cycle 1: k=3 broad+concrete. Codex converge. Prune. Cycle 2: extend survivors.

---

## Cycle 1

### H1: text-to-SQL (Spider/BIRD) (opus, DEAD)

**Verdict:** No-go. The scored output is the SQL query, which is INVARIANT to row
regeneration, so memorizing question→SQL survives. Regeneration yields a new database,
not a new instance.

**Dead:** (killed by the generator itself, pre-codex) two independent fatal blows:
- **Target-invariance / precondition-5 failure.** In tau-bench the golden *action
  trajectory* co-varies with state (ids/balances), so resampling changes the correct
  output. SQL is a schema-level program, row-invariant by construction. So state
  regeneration cannot defeat the contamination that matters (the question→program map).
- **Mechanism is incumbent prior art.** "Regenerate DB, re-execute gold, compare result
  sets" = test-suite accuracy [Zhong et al., EMNLP 2020, aclanthology.org/2020.emnlp-main.29],
  coverage-guided DB gen included (solves the empty-result failure mode). Evergreen NL2SQL
  = LiveSQLBench; perturbation/contamination = Dr.Spider (2301.08881), SPENCE (2604.17771).

**Profound lesson (the real crux): PRECONDITION 5 — the canonical solution must co-vary
with the regenerated state (scored artifact is state-SPECIFIC, not a general program).**
This is what the survey and the earlier codex/generalization work all missed. It prunes
text-to-SQL AND likely algorithmic-coding (H3: code is input-invariant like SQL).

**Salvage (weak):** reframe SQL task as execution-QA (agent emits the answer SET, not the
SQL); target then co-varies. But that's closed-book table-QA, off-family, weak.

### H2: the "executable-oracle" reframe (opus, SURVIVES — narrowed)

**Verdict:** Directionally right, strictly broader than "database-shaped," but the maximal
genus over-reaches into DyVal. Claim the *interactive-state species*, cite DyVal as the
single-turn degenerate case.
**Claims:**
- Genus ("regenerate problem, programmatically obtain answer") is NOT novel: DyVal (ICLR
  2024, 2309.17167, contamination-motivated, DAG-generated reasoning), GSM-Symbolic,
  property-based testing already own it. [generator]
- Defensible delta = interactive-state species DyVal doesn't touch: (i) G regenerates the
  STATE of a pre-existing benchmark; (ii) R = separate canonical reference re-executed vs
  that state; (iii) agent graded on stateful multi-turn interaction, not a scalar answer.
- Discriminating property is THREE poles: computation (IN) vs lookup/stored-key (MMLU, OUT)
  vs judgment (Arena, OUT). MMLU-vs-GSM-Symbolic is the clean test.
- vs metamorphic testing: clean win (MT is oracle-FREE; we produce a concrete oracle).
**One-sentence class:** "benchmarks whose instance is a regeneratable environment state
x=G(seed) and whose ground truth is recomputed by re-executing a canonical reference on
that state o=R(x), scored by decidable comparison — DyVal/GSM-Symbolic the single-turn
degenerate case, our contribution the interactive state-mutating members (tau-bench,
AppWorld, WorkArena)."
**Flag (unverified):** DyVal's exact label-computation mechanism not re-read this session.

### H3: algorithmic-coding-with-generated-IO (opus, DEAD)

**Verdict:** No-go. Regenerates the wrong thing: coding contamination = memorized
solution/algorithm (keyed to the unchanged problem statement); regenerating test IO leaves
statement+solution intact, so ~0 contamination resistance. And "input-is-difficulty":
adversarial input selection is the difficulty, so a generic resampler collapses
discriminative power (CodeContests+ 2506.05817 documents this — mutation-tests too weak;
needed per-problem G-V + Checker agents). APPS/CodeContests ship reference solutions + IO
but NO generators/checkers. Same root failure as H1: scored artifact (code) is
state-invariant → precondition 5 fails.

---

## Cycle-1 synthesis (pre-codex)

**Convergent finding across H1+H2+H3 — the real precondition:**
> **(5) the agent's scored output must CO-VARY with the regenerated state** (state-specific
> action trajectory / answer, NOT a state-general program).

**Contradiction resolved:** H2 classed Spider IN (executable oracle); H1 classed Spider OUT
(state-invariant target). Both right on different axes. The method needs BOTH: executable
oracle AND state-covarying scored artifact. Intersection ∩ interactive = the true class.

**True domain of validity:** interactive, state-mutating benchmarks where the agent emits a
state-specific action trajectory graded by re-executing a canonical reference against the
regenerated state. Members: tau-bench, AppWorld, **WorkArena**. Degenerate single-turn case
(cite, don't claim): DyVal, GSM-Symbolic. OUT: text-to-SQL, competitive-coding (state-
invariant scored artifact); MMLU (lookup); Arena (judgment).

**Second-demonstration pivot:** text-to-SQL is DEAD. **WorkArena** is now the best
independent candidate — interactive agentic, ships cheat() executable solver + state-based
validate() + seeded setup(), scored output (action trajectory) co-varies with seeded state
(passes precondition 5), independent (ServiceNow/Mila). AppWorld also IN but heavier
(code solutions, assertion oracle).

---

## Cycle 0: broad landscape survey (external, verified)

**Strongest single class: text-to-SQL (BIRD/Spider).** Unique max on all 4 preconditions
with a NATIVE oracle: DBMS execution = the grader (result-set equality, no imposed
assertions), gold SQL = declarative program that re-executes on a resampled DB,
relational schema = canonical re-keyable state, resampler = regenerate rows respecting
schema/type/FK/uniqueness then re-run gold SQL. Independent (Yale, HKU/Alibaba).
Contamination documented (Spider: Ranaldi 2024 "GPT exhibit clear knowledge about
Spider"; BIRD→LiveSQLBench successor). EX def: "the proportion of examples for which the
executed results of both the predicted and ground-truth SQLs are identical" (BIRD,
2305.03111). Caveat: single-turn semantic parsing, NOT a multi-turn tool-agent.

**Best AGENTIC independent analog: WorkArena (ServiceNow/Mila, 2403.07718).** Already
ships both halves: `cheat()` Playwright solver (executable canonical solution) + state-
based `validate()` querying the DB (oracle) + procedural seeded `setup()` (resampler,
10 seeds/task). "cheat functions use Playwright to automatically solve the task";
validation "querying the database to retrieve entries created by the agent and verifying
their values." Replaying cheat() on a regenerated instance ~ our exact move. Smallest
delta to a full agentic demonstration in tau-bench's genre.

**Third: ScienceWorld (AI2, 2203.07540)** — 30 gold trajectories replay natively in the
sim, 7,200 parametric variations (real resampler), already probes memorization. Looser
precondition 1 (predicates not relational DB).

**Disqualified with reasons:** KGQA/SPARQL (frozen shared KB, no resampler); CRMArena
(grades returned answer not DB state, no solution program); WebArena (solution program
deliberately omitted); Spider 2.0 (gold = answer table not SQL; cloud-scale breaks
resampler); StableToolBench/ToolEmu (LLM-simulated state + LLM-judge oracle, opposite of
requirements); WikiSQL (no FK, saturated).

**=> Emerging plan: a PAIR of independent demonstrations.** text-to-SQL (purest form of
the core transformation, cross-community, but single-turn) + WorkArena (agentic,
independent, already has replay machinery). Together they answer both "cleanest form"
and "in tau-bench's agentic genre, independently" — a much stronger generalization story
than either alone. [survey, verified]

## Codex convergence (adversarial) — verdict

- **Precondition 5: correct, but FOLKLORE.** Crux sharpened to **target equivariance w.r.t.
  regenerated latent state**: if the scored target is invariant under regenerated variables,
  regeneration can't defeat memorization. Confirmed tau-bench passes / SQL / coding fail.
  BUT it's folklore under other names (invariance/equivariance, metamorphic, label-preserving
  vs label-changing). Present as a FORMALIZATION of a known principle, not a discovery.
  Codex's crisp form: "scored-target state equivariance: the scored target Y must have high
  conditional entropy under regenerated state; the oracle recomputes Y from S."
- **DyVal-as-genus: TOO STRONG.** DyVal is one LLM-era species of procedural dynamic eval,
  not the genus (property-based testing, MiniWoB/WebArena, unit-test code eval also there).
  Don't say "DyVal doesn't touch agents." Correct delta: "extend contamination-resistant
  dynamic evaluation from generated STATIC REASONING instances to STATEFUL INTERACTIVE
  ENVIRONMENTS — instance = mutable world state, agent policy must adapt to regenerated
  concrete entities, correctness computed by replaying/validating against environment state
  rather than a static key." DyVal targets static math/logic/algo QA; it does NOT regenerate
  the state of an existing mutable environment + re-execute a reference policy in it.
- **WorkArena: valid but circularity is a real attack.** If "method" = "use WorkArena's
  setup/cheat/validate," the demo is circular. Non-circular demo MUST: regenerate state
  BEYOND the shipped fixed instances/configs, rerun the independent cheat()/solver to produce
  the oracle on the NEW state, and show memorization baselines COLLAPSE while capable agents
  still solve. Only-shipped-seeds = weak.
- **Biggest risk:** "not a new method, just applying existing procedural machinery (DyVal,
  WorkArena, BrowserGym, code benchmarks) to tau-bench." Survives ONLY IF: (a) the
  theorem-like equivariance condition is explicit, AND (b) an empirical **contamination
  failure/success BOUNDARY across classes** is shown.

## Cycle-1 result: the refined thesis (paper spine)

**Contribution =** (1) formalize scored-target state-equivariance as the precondition for
regeneration to defeat contamination; (2) EMPIRICALLY MAP THE BOUNDARY across classes —
regeneration defeats memorization where the target co-varies (tau-bench, WorkArena) and
FAILS where it doesn't (text-to-SQL, competitive-coding); (3) ship the working transformation
for the interactive-state members. Position as extending dynamic-eval (DyVal/metamorphic/
property-based lineage) from static reasoning to interactive state-mutating environments.
The cross-class boundary experiment is the novel empirical core; it converts the "folklore
precondition" concern into "nobody has empirically drawn this boundary for benchmark
regeneration." WorkArena = second demo (must regenerate beyond shipped configs + show the
memorization collapse).
</content>
