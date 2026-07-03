# Worklog

Process notes, dead ends, and mistakes. Standing results live in `docs/receipts/` and
`DESIGN.md`; this file is where the wrong turns are recorded so the receipts stay clean.

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
