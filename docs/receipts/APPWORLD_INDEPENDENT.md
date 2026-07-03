# Independent second domain: AppWorld (proof-ladder step 6)

- Domain: AppWorld (Stony Brook, ACL 2024), `appworld==0.2.0.dev0`, repo `a072b7a`.
- Setup + exact commands: `scripts/appworld/SETUP.md`; process notes in `docs/WORKLOG.md`.
- Commit (this repo): `ac5c956`. Date: 2026-07-03 20:51 UTC.
- Substrate: 9-app local tool-agent world (FastAPI + SQLite), graded by a deterministic
  state-diff over the app databases. No browser, no external service, no LLM in this receipt.

This is the independent, non-τ-bench instantiation the guardrail (DESIGN.md) requires.
Rather than only observe that AppWorld ships instance variants, we ran its regenerate +
replay-derive-oracle pipeline on genuinely fresh state and measured whether a model
contaminated on the shipped benchmark still passes. Note what this does and does not
establish: AppWorld's generator is the *authors'* own, so this **corroborates that the
regenerate+replay pattern already exists in an independently built domain and operates on
fresh state** — it is not a port of our τ-bench code. For a genus-level claim that is
arguably stronger evidence.

## Regenerating at a held-out seed

We ran AppWorld's own generator (`generate_and_validate_tasks.py`) at seed 12345 across
**12 train scenarios**, 3 tasks each → **36 fresh instances**. Held-out means the seed and
the drawn state differ from the shipped release: e.g. scenario 82e2fac drew users
clmiller/joseharr/kathrynmaldonado (shipped: joyce/glenn/paul) and answer "Lost in the
Twilight of Hope" (shipped: "A Love That Never Was"). Answer-disjointness from shipped was
checked exhaustively (that is how the collisions below were found); user/state disjointness
was spot-checked, not verified for all 36.

| Held-out generation | Result |
|---|---|
| Scenarios regenerated | 12 / 12 |
| Fresh instances | 36 |
| Pipeline runs end-to-end + reference solution reaches its re-derived oracle | 12 / 12 |

What 12/12 establishes and what it does not: the pipeline **executes end-to-end,
deterministically, on fresh state**, and the generated solution reaches its
replay-derived oracle. That last check is *self-consistent by construction* — the oracle
is defined as the replay endpoint of that solution — so it certifies executability, not
soundness, and says nothing about whether the regenerated task *text* still matches the
regenerated state (the classic template-regeneration failure mode). Rejection-side
validity comes from the A0 arm below (the oracle does reject wrong answers).

Train only: solutions and generators ship for train/dev, not the held-out test splits, so
the method run is on train scenarios.

## The memorization gap on held-out state

Answer-swap applies only to the **15 of 36** held-out instances that are answer-type (QA);
the other **21 are state-mutation tasks** (null scalar answer, graded by DB diff) — exactly
where the stronger trajectory-replay adversary below would operate, and not scored here. An
A0 adversary memorizes the shipped answers; we complete each held-out QA task with (a) its
own fresh answer and (b) the shipped answer, grading against the held-out replay-derived
evaluator (`scripts/appworld/heldout_a0.py`).

| Held-out QA (n=15) | pass |
|---|---|
| memorized SHIPPED answer, **unconditional** (A0 survival) | **2 / 15 = 0.133** |
| — of which distinct-answer instances (A0 gap) | 0 / 13 |
| — of which answer collisions (shipped == held) | 2 / 2 |
| control: own fresh answer through the same harness | 15 / 15 |

Reading. Memorization survives on **2/15** held-out instances; both are answer *collisions*
(`d0b1f43_1`, `_3`: money sums 1068.0, 1213.0 that happened to equal shipped). The
collision is coincidental, not a regeneration-invariant quantity — the same scenario's `_2`
instance moved (786.0 → 3208.0) — though two exact hits on money sums is worth confirming
the underlying transaction sets actually differ. On the 13 distinct-answer instances the
memorized answer passes 0 times; with n=13 the rule-of-three 95% upper bound on that rate
is ~0.23, so read it as "small and consistent with zero," not a hard 0. The control arm
(15/15) is not independent soundness evidence — it is the same self-consistency fact as
12/12, re-measured through the completion harness — but it is necessary: it shows the
grading path used for the memorized answer *accepts* the correct answer, so the 2/15 is a
real gap and not a broken harness.

The collisions are the reason this is a precondition-5 measurement and not a tautology: the
evaluator grades by value, so when the regenerated value coincides with the memorized one,
memorization passes. The gap is exactly the rate at which regeneration moves the scored
target off the memorized value.

Breadth (shipped `_1/_2/_3` orbit, cross-instance answer-swap,
`scripts/appworld/appworld_a0_qa.py`): own 1.000, cross 0.000 — same shape, weaker because
it is orbit analysis of public instances rather than a run on fresh state.

## The other side of the boundary: a state-general procedure survives (all 36 held-out)

The QA gap is the IN side (a concrete answer co-varies with state → memorizing it dies). The
OUT side is the invariance mode: AppWorld's shipped `compiled_solution.py` is a *state-general
procedure* — it reads the current world's supervisor/contacts/notes dynamically and acts, so
it is not tied to any instance's concrete values. Running each **shipped** procedure against
its **held-out** world (`scripts/appworld/procedure_survival.py`) measures whether
procedure-level memorization survives regeneration, and doubles as the specificity control
(are the held-out tasks solvable on fresh state at all?):

| Shipped procedure on held-out world (n=36) | result |
|---|---|
| survives (reaches held-out oracle) | **32 / 36 = 0.889** |
| — QA instances | 15 / 15 |
| — state-mutation instances | 17 / 21 |
| completed-but-wrong / crashed | 1 / 3 |

So on the same held-out state where a memorized *answer* dies (0/13), a memorized *procedure*
survives (0.889). That is precondition 5 with both sides measured on independent ground, and
it parallels the SQL boundary (`BOUNDARY.md`: leaked query survives, leaked answer dies).
Read as re-pricing: regeneration defeats value/trajectory-level contamination and leaves
procedure-level contamination (A1) intact — it does not, by itself, distinguish a memorized
procedure from genuine skill (that needs the held-out-family / CoinRun test, future work).
The 4 non-survivors are compiled solutions with residual instance-specificity (3 crash, 1
completes wrong) — not every shipped "procedure" is perfectly state-general; disclosed, not
hidden. The specificity control also holds: the held-out mutation tasks are solvable on fresh
state (17/21), so the QA null gap is "memorization stale," not "task broken."

## Honest scope

- **A0 is the floor, not a realistic adversary.** A QA answer is a scalar, so "memorized
  answer goes stale" is the minimal contamination model. The licensed claim is narrow:
  regeneration defeats *value-level* memorization, where the scored target co-varies with
  the regenerated state. A model that memorized the *procedure* is not defeated by this —
  see the boundary corollary (`BOUNDARY.md`): a state-general method survives by design.
- **State-mutation is covered on the OUT side (procedure survival, above); the IN-side
  verbatim-trajectory replay is not run.** Replaying instance i's concrete `api_calls.json`
  against instance j would fail mostly via stale access-tokens/ids (crash), i.e. brittleness
  rather than a clean "memorization stale" signal — so it is deferred; the procedure-survival
  measurement is the informative half.
- **Validation is a self-consistency check**, not a task-text-validity check (see above).
- **"Independent" means independent-within-genus.** AppWorld and τ-bench are both DB-backed
  tool-agent benchmarks with deterministic state checks — a second benchmark within the
  method's declared scope (preconditions 1–5), different authors, different apps, not a
  modality-distant domain (WorkArena, deferred on infra cost).
- The shipped orbit is public and entirely in any model's contamination surface; it shows
  *equivariance*. The held-out generation is what speaks to *resistance* — memorization of
  the public benchmark does not transfer to freshly drawn state (outside collisions).
