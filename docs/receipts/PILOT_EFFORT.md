# Step-4 pilot: Opus low vs high effort (paired, branch-selection)

- Command: `python scripts/pilot_effort.py --seeds 2` (10 specs, harder-first) → `PILOT_EFFORT.log`
- Agent: Claude Code Opus 4.8, `--effort low` vs `--effort high` (same weights, same
  contamination, only compute differs — Fable's clean A-vs-B instrument). User-sim: claude
  for both arms (same-family → symmetric, no differential confound). Mediated, `comparable=True`.
- This is a feasibility PILOT, not a powered result. n=20 paired instances.

## Numbers

| | pass (n=20) |
|---|---|
| Opus low effort | 0.500 |
| Opus high effort | 0.400 |
| gap (high − low) | −0.100 |

McNemar 2×2 (low,high): 11=6, 10=4, 01=2, 00=8 → discordant 6, **ψ = 0.30**.
Within-spec **ICC(diff) ≈ 0.48**. Per-spec: several are both-fail (29, 74, 79) or both-pass
(0), i.e. most variance is *between* specs.

## What the pilot actually establishes (and what it doesn't)

- **The harness is sound.** A high-effort *failure* (retail:60 seed 1, high=0 in the pilot)
  was re-run and *passed* — clean trajectory, correct modify, no parse error, no max-steps.
  So the failures are genuine agent behavior, NOT a verbose-output/parse/max-steps artifact.
- **The gap is not established.** That same-instance flip is the point: **CRN pairing fixes
  the instance but not agent/sim stochasticity** (trajectories diverge after the first
  message; the sim occasionally breaks character). Single-trial-per-instance at n=20 cannot
  resolve a ~10-pt effort gap against that noise. The "low ≥ high" direction (discordant 4:2
  for low — high effort perhaps overthinking agentic tasks) is *suggestive only*.
- **Two cost-inflators stack for any confirmatory:**
  1. within-spec ICC ≈ 0.48 → effective n ≪ raw n; need MANY specs, not many seeds/spec.
  2. un-CRN'd per-instance stochasticity → need MULTIPLE trials per (instance, effort) to
     estimate the per-instance rate before pairing buys anything.
  Together these push the confirmatory well past Fable's single-trial ballpark
  (≈100–230 paired for a 10-pt gap): realistically hundreds of specs-instances × several
  trials each × 2 arms.

## Decision this informs

The clean instrument works and the mechanism (paired generative eval) is sound, but the
Opus low-vs-high gap is (a) small/noisy and (b) expensive to pin. Options: run a multi-trial
mini-pilot to estimate per-instance rates and the true gap sign; OR defer the confirmatory to
a cross-model pair with a larger, cleaner gap once OpenAI/codex access returns (~3 days);
OR carry step 4 as pre-registered future work with these feasibility numbers. Not staked on
a rushed underpowered run.
