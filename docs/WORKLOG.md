# Worklog

Process notes, dead ends, and mistakes. Standing results live in `docs/receipts/` and
`DESIGN.md`; this file is where the wrong turns are recorded so the receipts stay clean.

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
