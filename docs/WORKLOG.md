# Worklog

Process notes, dead ends, and mistakes. Standing results live in `docs/receipts/` and
`DESIGN.md`; this file is where the wrong turns are recorded so the receipts stay clean.

## 2026-07-03 (cont.) — widening the spec pool (for effective-n; chose this before step-4 pilot)

Goal: ~40 specs so a cluster-robust analysis can carry "powered" (13 specs → n_eff dies).
Reality check from authoring: the easy variant-availability well is nearly dry.
- Of the 14 inventoried EASY tasks, 13 are already specs; the last (retail 83) pivots on an
  ORDER FIELD (payment method), not variant availability → needs a new resampler axis.
- Added 4 clean specs from the MEDIUM tier that fit the existing CatalogBranchSpec machinery:
  retail 29 (argmax price, 28-inch bamboo), 74 (i9 laptop cascade 256GB→silver), 110 & 111
  (cheapest tablet, argmin). All validated: branches fire, per-branch oracle determinism,
  distinct end-states, zero tool errors, over 240 seeds each. Now 17 specs.
- Candidates that DON'T cheaply fit (surfaced while authoring): 52 (camera max-zoom) and 77
  (perfume max-size) are DEGENERATE — toggling the target off leaves a tie / self-exchange,
  so only one realizable branch (BestAvailable raises on ties by design). 35 (multi-attribute
  laptop cascade) is a construct-validity judgment the audit can't check. Many remaining
  MEDIUM/HARD pivot on order status / payment / price / quantity (new resampler axes) or are
  airline (new schema).
- Highest-leverage next addition: a CARDINALITY selector ("X if *multiple* colors/options")
  unlocks ~7 (retail 45, 60, 70, 71, 72, 102, 103) + the 2-way existence pairs 99/100 — one
  new selector → ~9 specs, getting ~17→~26. Reaching 40 then still needs order-field/price
  pivots (new machinery) and/or airline. So "widen to 40" is a real multi-step grind, not an
  afternoon; flagged for the user.
- **Target reset to n=30** (user: "good enough by most standards"). And the cardinality tasks
  turned out NOT to need a new selector — "X if multiple, else the available one" REDUCES to a
  `FirstAvailable` cascade (exactly as task 107 already does), so they use existing machinery.
  Added 7 more (→ 24): retail 70 (helmet color), 102/103 (metal-watch color), 45 (vacuum
  bagless-if-several), 60 (blue earbuds), 99/100 (jigsaw animal/art). For 45 and 60 the
  fallback worlds expose exactly ONE option so "the single available one" stays well-posed.
  71/72 dropped (degenerate: only one medium-polyester backpack variant exists). All validated
  over 240 seeds. Remaining 6 to hit 30 = action-flip tasks (modify-vs-cancel / exchange-vs-
  return: retail 76, 88, 91, 30, 57, 89), which pivot on variant availability (already
  supported) but need `patch` functions to reshape the golden per branch — the CatalogBranchSpec
  `patch` hook (used by task 1) covers this; no new resampler axis needed for 30.
- **+1 more (→ 25) and the availability-only boundary.** Added retail 91 (e-reader
  self-exchange vs return, action-flip via `patch`; non-shipped return branch reconstructed
  from unambiguous intent; validated clean). ATTEMPTED retail 88 (bookshelf modify-vs-cancel)
  but DROPPED it: the primary (modify to the 4ft glass-white bookshelf, $531.22) is not
  solvable-by-construction — the owned 5ft is $504.65 and the order's gift card holds only
  $19, so the +$26.57 price step fails ("insufficient gift card balance"). Forcing the variant
  *available* is not enough; the branch also needs *price/payment* control the `World`
  mechanism (availability flags only) doesn't have. Ships infeasible → refused.
  This is the real edge: the remaining candidates to 30 all hit the same wall —
  payment/price constraints (88, 20, 40), price resamples (89, 64), order-field pivots
  (57, 82, 83), degenerate branches (52, 77, 71, 72), or reconstruction ambiguity (76, 30).
  So availability-only faithfully tops out around 25. Reaching 30 cleanly needs a modest
  extension: **price overrides in `World`** (a `prices` map alongside `avail`), which unlocks
  the payment/price-constrained tasks (88 with an affordable resampled price, 20, 40, 89, 64).
  Defined next step, not a grind — flagged for the user rather than shipping faithless specs.

## 2026-07-06 — citation integrity pass (Sonnet subagent)

Verified all ~28 arXiv ids in DESIGN/PRIOR_ART against source (3 already read this session
skipped). Result: **25 VERIFIED, 0 MISMATCH, 0 UNRESOLVABLE, 3 PARTIAL.** The suspicious
recent-2026 ids (2505.20411 SWE-rebench, 2602.11224 Agent-Diff, 2603.23611 LLMORPH,
2605.07053 GSM-SEM, 2605.23965 LGMT) all resolve to real papers matching our claims — no
fabrications. Load-bearing novelty citations (τ² 2506.07982, τ-bench 2406.12045, DyVal
2309.17167, DyVal2 2402.14865, Benchmark Self-Evolving 2402.11443) all verified.
Three PARTIALs fixed (framing over-attributions, not integrity failures):
- Avalon (2210.13417): the train/test seed-split *protocol* is ProcGen's, not Avalon's —
  relabeled so seed-split attaches to ProcGen; Avalon/ProcTHOR are seeded procedural gen.
- CheckList (2005.04118): it's behavioral testing, not a contamination claim — relabeled as
  our grouping; "paired contamination test" now attached specifically to PaCoST (2406.18326).
- BetterBench (2411.12990): the specific "unique IDs / encrypt instances" mechanisms aren't
  in the abstract (checklist body); softened to the confirmed best-practices framing, kept
  the regenerate-vs-hide contrast general (WebFetch was 529-throttled; flagged for a body
  check before quoting the mechanisms).

## 2026-07-03 (cont.) — step-4 impact demo: Fable design review before spending compute

Asked Fable to validate the plan (Composer-2.5 vs Opus-4.8; Opus low vs high, paired-CRN
McNemar on branch-selection). Verdict: the plan as stated is the WRONG instrument. Kept
corrections:
- **Pair 1 (Composer vs Opus) is wrong for step 4.** A big capability gap is resolved by
  static n=115 too (MDE 15-18), so it fails the "tied on static" premise → zero evidence for
  the generator's value. Plus capability×contamination confound (and "Composer uncontaminated"
  is refuted by our own RECALL_PROBE: declining is threefold ambiguous). Park Pair 1 in the
  rung-5/discussion contamination material, not step 4.
- **Drop "flips," aim for "resolves a tie."** Our own SHIPPED_ABLATION (recall behaviorally
  inert) predicts no sign-reversal.
- **Goldilocks gap ≈ [8,15] pts.** Static blind below ~15; paired generative at feasible n
  (~400-600 paired) sees ~8. Pair 2 (Opus low vs high) is the clean instrument (same weights,
  same contamination, controls all but compute) and PLAUSIBLY in-window — but could be <5
  (infeasible). A PILOT gates everything: ~60-100 paired episodes to estimate gap, discordance
  ψ, and within-spec ICC; plug Connor's formula; check required n is affordable.
- **Run the static arm empirically** (115 tasks, same harness/sim, paired McNemar p>.05, CI
  spanning zero) — don't just cite the MDE table as the "tied" leg.
- **The generator's gift is n, not pairing.** Pairing is free on static too (McNemar on 115;
  our own receipt: paired power 0.107). The generator lifts the n-cap while keeping pairing.
  Reframe the headline accordingly.
- **BIGGEST hole — effective n / clustering.** 13 specs × N seeds: within-spec seeds are
  near-replicates (branch flip ≈ 1 bit), correlated, so McNemar's independent-pairs assumption
  inflates n. n_eff = n/(1+(m-1)ICC); 13×40 at ICC 0.3 → n_eff ~40. Kills the "powered" headline.
  Fix: cluster-robust analysis (cluster bootstrap / spec-level) AND widen the spec pool to
  ~40 (we have 76 state-testable tasks inventoried; 40×10 beats 13×31 by ~3× effective n).
- User-sim family confound: pin a third-family sim, same version both arms (hard right now —
  codex/OpenAI out ~3 days).
- Honest two-stage design: declared pilot → pre-registered confirmatory on committed seeds,
  cluster-robust McNemar + empirical static arm. "Small-n, flip one" is honest only if ONE is
  chosen before the data.

## 2026-07-03 (cont.) — step-4 pilot ran (Opus low vs high effort)

Model-access detour: Cursor free plan blocks named models (`ActionRequiredError: Named
models unavailable`), so opus-4-8-low/high via cursor-agent is out (composer-2.5/auto only);
codex/OpenAI out ~3 days. BUT Claude Code exposes `--effort low|medium|high|xhigh|max` on
Opus directly → the clean same-weights A-vs-B instrument, unblocked. Wired `--claude-effort`
into run_eval and `effort` into claude_adapter.

Pilot (`scripts/pilot_effort.py`, receipt `PILOT_EFFORT.{md,log}`), 10 specs × 2 seeds:
- low pass 0.500, high pass 0.400 (gap −0.10), ψ=0.30, within-spec ICC(diff) ≈ 0.48.
- **Harness sound, gap NOT established.** A high-effort pilot failure (60:s1) re-ran and
  PASSED (clean trajectory, no parse/max-steps error) → failures are genuine agent behavior,
  and the per-instance outcome is STOCHASTIC across runs. CRN fixes the instance, not agent/
  sim noise (Fable's caveat, confirmed). Single-trial n=20 can't resolve a 10-pt gap.
- Suggestive only: low ≥ high (discordant 4:2 for low — high effort maybe overthinking
  agentic tasks). Two cost-inflators stack (ICC 0.48 + un-CRN'd stochasticity) → confirmatory
  is much more expensive than Fable's ballpark (need many specs AND multi-trial per instance).
- Decision pending (user): multi-trial mini-pilot to pin the gap; OR defer to a cross-model
  pair when codex returns; OR carry step 4 as pre-registered future work with these numbers.

## 2026-07-03 (cont.) — AppWorld as the independent second domain (proof-ladder step 6)

Chose AppWorld over WorkArena (local Python, no ServiceNow/browser; same replay-oracle
shape). Journey and judgments:

- **Feasibility confirmed.** `pip install appworld` + `appworld install` + `download data`
  (~183M, fully local FastAPI/SQLite). Tasks ship as `{scenario}_1/_2/_3` orbits (same
  template, varied instance), train/dev carry a runnable reference `solution.py`
  (adaptive, branches on `public_data`), a specialized `compiled_solution.py`, concrete
  `api_calls.json`, and a state-diff `evaluation.py`. `AppWorld(task_id)` + `execute()` +
  `evaluate()` runs end-to-end on this machine.
- **QA answer-swap A0 (breadth, gathered):** over 13 QA scenarios with distinct-answer
  orbits, own-answer 39/39=1.000 (soundness), cross-answer 0/39=0.000 (memorized answer
  stale). Real, but weak — see Fable.
- **Fable adversarial review (checkpoint).** Verdicts kept: (1) QA cross-fail alone is
  near-tautological; the informative object is the *conjunction* own-pass ∧ cross-fail =
  a precondition-5 measurement — report at SCENARIO granularity, not pooled pairs (pooling
  inflates n), and treat answer collisions (booleans/counts) as the signal the instrument
  reads more than FAIL. (2) The shipped orbit shows *equivariance*, NOT "our method ports"
  — we ran nothing, and all 3 siblings are public (in the contamination surface). (3) The
  single objection-killer: run the generator at a HELD-OUT seed on fresh state. (4)
  Load-bearing adversary is state-mutation trajectory-replay (scalars are where tautology
  bites), with a completed-but-wrong vs crashed-on-missing-id failure taxonomy. (5)
  Residual, unfixable: AppWorld and τ-bench are the same genus → "independent benchmark
  within declared scope"; state it, take it.
- **Honesty finding (mixed regeneration).** Per-task `dbs/` are empty except
  `supervisor.jsonl`; app data lives in a shared base catalog. Across an orbit the
  main_user (joyce-weav → glenn.burton → paul_mill) and query parameters
  (most/least, metric, library) vary over that fixed catalog. So the shipped orbit is
  *mixed state/problem regeneration*, not clean state-resampling — must disclose, and it
  motivates running the generator for genuinely fresh state.
- **Decision:** run the generator at a held-out seed (objection-killer). Cloned the repo
  for the `generate/` package; reusing the already-downloaded base catalog to skip the
  ~45-60 min base-DB regen.
- **Repo setup gotchas (resolved):** generator code + base-gen code live in git-LFS
  `.source/*.bundle` (skip-smudge clone leaves pointers → `git lfs pull`, then
  `appworld install --repo` unpacks). `generate/` is not a package on PYTHONPATH (run with
  `PYTHONPATH=<repo>`). Generation refuses to run unless `PYTHONHASHSEED` is set (repro
  guard) — `PYTHONHASHSEED=<n>`.
- **Generator WORKS on fresh state (key win).** At `--random_seed 12345` scenario 82e2fac
  drew a NEW main_user "Claudia Miller" (none of the shipped joyce/glenn/paul) and a NEW
  replay-derived answer "Lost in the Twilight of Hope" (shipped _1 was "A Love That Never
  Was") — genuinely fresh state with the oracle re-derived, not the shipped orbit.
- **Version blocker (resolved):** pip-downloaded base data is db-version 0.1.0; repo code is
  0.2.0.dev0, which rejects 0.1.0 tasks. Re-downloaded v0.2.0 data to `v2root` (733 tasks).
  Also: generated-task save runs `ruff` as a subprocess — must have the venv `bin` on PATH
  (`PATH=<venv>/bin:$PATH`) or it exits 127.
- **METHOD RUN SUCCEEDS on genuinely fresh state (objection-killer, n=1 scenario).** At
  held-out `--random_seed 12345`, scenario 82e2fac regenerated a full orbit with NEW users
  (clmiller/joseharr/kathrynmaldonado, none shipped) and NEW answers ("Lost in the Twilight
  of Hope" / "Beyond the Horizon's Reach" / "Shadows of the Past" vs shipped "A Love That
  Never Was"/"Distant Love"/"Wandering the Streets Alone"), and validation PASSED 2/2 — the
  regenerated reference solution reaches the regenerated replay-derived oracle on state that
  did not exist before. This is the actual regenerate+replay method ported to an independent
  domain, not orbit analysis. Next: scale to a batch of scenarios and quantify (soundness on
  fresh state ~1.0; memorized-shipped-answer A0 ~0).
- **Batch method run (quantified, objection-killer).** Regenerated 12 train scenarios at
  held-out seed 12345: 12/12 validated (36 fresh instances, each reference solution reaches
  its regenerated replay-derived oracle). Held-out A0 over the QA subset: own-fresh-answer
  **15/15 = 1.000** (replay oracle sound on never-shipped state), memorized-shipped-answer
  **0/13 = 0.000** (gap fires). Fable's predicted signal present: 2/15 numeric-answer
  collisions (1068.0, 1213.0) where shipped==held, so memorization WOULD survive — the
  instrument reads the boundary, not a tautological always-FAIL. Result → receipt
  `APPWORLD_INDEPENDENT.md`. Honest scope kept: independent-within-genus; A0 is the floor;
  state-mutation trajectory-replay (the stronger adversary) is the follow-up.
- **Fable receipt review caught overclaims (fixed).** The first receipt draft said the oracle
  was "sound," the method "ports," and it "produces valid graded instances." Fable: 12/12
  validation is CIRCULAR (solution reaches an oracle defined as its own replay endpoint) →
  certifies executability/determinism, not soundness; we ran AppWorld's OWN generator so it's
  corroboration, not a port; 15/15 is the control arm (same fact as 12/12), not independent
  soundness; and only 15 of 36 instances were scored (silent subsetting). Rewrote: dropped
  sound/ports/valid, led the gap with the UNCONDITIONAL 2/15 (not the post-hoc 0/13), stated
  the 15-of-36 selection rule (21 are state-mutation), added the rule-of-three n-caveat, and
  characterized the 2 collisions as coincidental (sibling _2 moved 786→3208). Data survived;
  only the adjectives were wrong.
- **State-mutation follow-up reframed (procedure survives, not trajectory crashes).** Planned
  A0 = replay a memorized concrete trajectory on a held-out mutation task. On inspection the
  shipped `compiled_solution.py` is NOT hardcoded to shipped creds — it reads the supervisor
  profile/passwords/contacts DYNAMICALLY and logs in as whatever the current world's user is.
  So it is a state-general PROCEDURE, and running shipped 22cc237_1's procedure on the
  held-out 22cc237_1 world PASSED 4/4 — it adapts. That is the boundary OUT side on a
  state-mutation task (a memorized procedure survives regeneration) AND the specificity
  control (the mutation task is solvable on fresh state, so a null gap is not "unsolvable").
  A verbatim `api_calls.json` replay would instead fail via stale tokens/ids = brittleness
  (the crash asterisk), so the clean measurement is procedure-survival across the 36 held-out
  instances, paired with the QA concrete-answer IN side. Precondition 5, both sides, on fresh
  independent state.
- **Boundary on AppWorld held-out state (both sides, quantified).** Shipped procedure on the
  held-out world survives 32/36 = 0.889 (QA 15/15, mutation 17/21; 3 crashed, 1 wrong — a few
  compiled solutions carry residual instance-specificity, honest). Paired with the IN side
  (memorized concrete answer 0/13): regeneration kills value-level memorization and leaves
  state-general procedures intact — precondition 5 replicated on the independent domain, the
  A0→A1 re-pricing made concrete. Not "regeneration passes only skill": procedure-knowledge
  can itself be contamination (A2); separating skill from procedure-memorization needs the
  held-out-family/CoinRun test, still future work.

## 2026-07-03 — shipped ablation, cross-class boundary, in-context contamination

Standing results (valid): `SHIPPED_ABLATION.md`, `BOUNDARY.md`,
`INCONTEXT_CONTAMINATION.md`. Mistakes and dead ends from getting there:

- **RECALL_PROBE prediction refuted (walk-back, not a bug).** RECALL_PROBE.md had
  predicted claude would pass shipped-branch worlds *from weights* under observation
  ablation. The shipped ablation tested it and it was false: claude scored 0.000
  blocked / 0.667 observing, refusing to substitute its (correct, digit-perfect)
  memory for a blocked lookup. Kept as the stronger finding; prediction language in
  RECALL_PROBE updated to record the outcome.

- **codex CLI drift broke the codex shipped cells.** `codex exec` (v0.141.0) changed
  how it takes a prompt — it now blocks reading stdin under the user-sim's
  `[*argv, prompt]` invocation ("Reading additional input from stdin…"). The codex
  half of the shipped 2×2 could not be produced. Not re-run; the codex negative is
  already covered by `live_task0_codex_12seeds_ablated.log` + the RECALL_PROBE probes.
  Fix TODO: a codex-exec shim that passes the prompt the way v0.141 expects.

- **Composer-2.5 was the wrong subject for "does a weaker model refuse to use
  memory."** Wired the Cursor CLI in as an agent (`cursor_adapter`) and ran it on the
  shipped+block cell — it also refused to fabricate (escalated to a human). But a
  recall probe showed Composer *declines* task 0 from memory: it is uncontaminated, in
  codex's bucket, so it has no memory to refuse. Lesson: **weaker ≠ contaminated** —
  contamination tracks broad benchmark-file scraping, not capability. The cursor
  adapter is kept (useful, many models via one CLI); the "weaker model" question still
  needs a lighter-AND-contaminated model, not yet identified.

- **CLI agents have filesystem access; the first in-context run was invalid.**
  `claude -p` is an agentic CLI, not a pure model. Run inside the repo, it read the
  real `tau-bench/.../orders.json` and computed shipped answers — the first
  `incontext_contamination.py` run showed answer-ctrl (no leak, no rows in prompt) =
  1.00 on shipped, which is impossible without observation. Caught via that impossible
  cell. Fix: make all model calls from an isolated empty cwd outside the repo;
  answer-ctrl = 0.00 on the re-run confirms the sandbox. Only the isolated run is kept.
  Lesson: when using a coding-agent CLI as a "model," it can observe the working tree —
  sandbox the cwd or the no-observation premise is silently violated.
