# Receipt: power argument and cost accounting (proof-ladder steps 1 and 2)

Date: 2026-07-02. Git commit: `218e1ba` (script and this receipt added in the working
tree at that commit). Reproduce every number below with:

```bash
cd /path/to/generative-tau-bench
uv run scripts/power_analysis.py          # seed 20260702, 100,000 MC reps per cell
```

The script is self-provisioning (PEP 723 inline metadata; numpy + scipy). Runtime
~25 s. All Monte Carlo draws flow from `--seed` (default 20260702); rerunning with
the default seed reproduces the tables byte-for-byte. Analytic tables (A.1 to A.4,
B.2, and the analytic columns of B.3) involve no randomness at all.

**Headline.** The static τ-bench test set cannot resolve realistic harness gaps: the
minimum detectable effect for an unpaired A-vs-B comparison at 80% power is 15 to 18
points at n=115 (retail) and 22 to 28 points at n=50 (airline), while real harness
gaps run 3 to 8 points. Resolving a 5-point gap at a 50% baseline takes 1,565
instances per arm unpaired, or 1,256 shared instances paired (McNemar on common
seeds); a 3-point gap takes 4,355 per arm unpaired, 3,489 paired. The static set is
13.6x (retail) to 31.3x (airline) too small for the 5-point case, and pairing alone
does not rescue it (paired power at n=115, 5-point gap: 0.107). The generator
supplies that n at zero marginal annotation cost, because the oracle for every fresh
instance is re-derived by replaying the golden program (section 3).

## 1. The static set is underpowered (analytic)

Setup: alpha = 0.05 two-sided (z = 1.959964), power = 0.80 (z = 0.841621).

### 1.1 Standard error of a single pass-rate

SE(p, n) = sqrt(p(1-p)/n).

| n | p | SE | 95% CI half-width |
|---|---|----|-------------------|
| 115 | 0.3 | 0.0427 | ±0.0838 (8.4 pts) |
| 115 | 0.5 | 0.0466 | ±0.0914 (9.1 pts) |
| 115 | 0.7 | 0.0427 | ±0.0838 (8.4 pts) |
| 50 | 0.3 | 0.0648 | ±0.1270 (12.7 pts) |
| 50 | 0.5 | 0.0707 | ±0.1386 (13.9 pts) |
| 50 | 0.7 | 0.0648 | ±0.1270 (12.7 pts) |

A single reported pass rate on airline carries a ±14-point confidence interval at
p = 0.5. That is before any comparison is attempted.

### 1.2 Minimum detectable effect, unpaired A-vs-B

Two-proportion z-test sample size per arm:

n = (z_{α/2} sqrt(2 p̄ q̄) + z_β sqrt(p₁q₁ + p₂q₂))² / δ²,  p̄ = (p₁+p₂)/2.

The MDE is the δ at which this n equals the available n (solved by bisection).

| n per arm | baseline p | MDE (points) |
|-----------|------------|--------------|
| 115 | 0.3 | 17.9 |
| 115 | 0.5 | 18.1 |
| 115 | 0.7 | 15.3 |
| 50 | 0.3 | 27.5 |
| 50 | 0.5 | 26.7 |
| 50 | 0.7 | 21.8 |

DESIGN.md claims "at n=115 retail the binomial SE makes a 5–8 point harness gap
non-significant." Substantiated with margin: the smallest detectable gap at n=115 is
15 to 18 points, roughly double the top of that range.

### 1.3 Required n for realistic gaps

| baseline p | gap (pts) | n per arm | vs retail 115 | vs airline 50 |
|------------|-----------|-----------|---------------|---------------|
| 0.3 | 3 | 3,762 | 32.7x | 75.2x |
| 0.3 | 5 | 1,376 | 12.0x | 27.5x |
| 0.3 | 8 | 549 | 4.8x | 11.0x |
| 0.5 | 3 | 4,355 | 37.9x | 87.1x |
| 0.5 | 5 | 1,565 | 13.6x | 31.3x |
| 0.5 | 8 | 608 | 5.3x | 12.2x |
| 0.7 | 3 | 3,553 | 30.9x | 71.1x |
| 0.7 | 5 | 1,251 | 10.9x | 25.0x |
| 0.7 | 8 | 471 | 4.1x | 9.4x |

### 1.4 pass^8: the estimator arithmetic

τ-bench's unbiased estimator (`run.py`, mirrored in `gtau/metrics.py:pass_hat_k`)
scores each task C(c,k)/C(n,k) for c successes in n trials. τ-bench runs n = k = 8
trials, so the per-task estimator is C(c,8)/C(8,8), which over c = 0..8 evaluates to

[0, 0, 0, 0, 0, 0, 0, 0, 1]

i.e. the indicator that all 8 trials passed. DESIGN.md line ~244 says pass^8 "rides
on a near-binary per-task estimator over ~50 tasks." Corrected upward: at k =
n_trials the per-task estimator is *exactly* binary, and pass^8 over airline is a
plain proportion over 50 Bernoulli tasks, SE = sqrt(π(1-π)/50) ≤ 0.0707. The
"near-binary" hedge is only needed when n_trials > k; even then, the underlying map
p → p⁸ traverses 0.1 → 0.9 only over per-trial p in (0.750, 0.987), so any task
outside that band has a near-binary pass^8 probability regardless of trial count.

The map also collapses effect sizes. Gap transmission is d(p⁸)/dp = 8p⁷:

| per-trial p | p^8 | gap transmission 8p^7 |
|-------------|-----|------------------------|
| 0.3 | 0.0001 | 0.002 |
| 0.5 | 0.0039 | 0.062 |
| 0.7 | 0.0576 | 0.659 |
| 0.75 | 0.1001 | 1.068 |
| 0.9 | 0.4305 | 3.826 |
| 0.95 | 0.6634 | 5.587 |
| 0.987 | 0.9006 | 7.300 |
| 0.99 | 0.9227 | 7.457 |

On the pass^8 scale (π = p⁸, same two-proportion formulas, per-trial gap of 5 points
induces a π-gap of (p+0.05)⁸ − p⁸):

| per-trial p | pi=p^8 | SE @T=115 | SE @T=50 | MDE(pi) @T=50 (pts) | per-trial gap 5pts -> pi-gap (pts) | T req. for that pi-gap |
|---|---|---|---|---|---|---|
| 0.3 | 0.0001 | 0.0008 | 0.0011 | 14.3 | 0.02 | 89,616 |
| 0.5 | 0.0039 | 0.0058 | 0.0088 | 14.9 | 0.45 | 4,799 |
| 0.7 | 0.0576 | 0.0217 | 0.0330 | 20.2 | 4.25 | 631 |

At a 50% per-trial rate, a 5-point per-trial gap shrinks to a 0.45-point pass^8 gap
and would need 4,799 tasks per arm to detect. That is the effective-n collapse:
below p ≈ 0.75 the eighth power crushes both the level and the gap; only near p → 1
(8p⁷ > 1) does pass^8 amplify differences.

## 2. Paired seeds vs independent instances (simulation)

Model: instance difficulty q_i ~ Beta(2,2) (mean 0.5, Var 0.05). Harness A succeeds
with probability q_i; harness B with sigmoid(logit(q_i) + d), d solved so the
marginal gap E[p_B] − E[p_A] equals the target δ. Outcomes are conditionally
independent given q_i, so all correlation between harnesses flows through shared
instance difficulty (the common-random-numbers channel).

Budget matching: paired runs both harnesses on the same n instances (2n episodes);
unpaired runs each harness on its own n fresh instances (2n episodes). Equal episode
budget; the generator makes instances free either way.

Tests: exact McNemar on discordant pairs (identical statistic to
`gtau/metrics.py:mcnemar`) vs the pooled two-proportion z-test. 100,000 Monte Carlo
reps per cell, seed 20260702. Under this model the per-instance joint outcome
distribution is exact (Beta-averaged 2x2 cells), so the simulation draws
Multinomial/Binomial counts directly; a brute-force per-instance simulation
cross-checks one cell (2.4 below).

### 2.1 Empirical power (δ = 0 rows are size/calibration checks)

| delta (pts) | design | n=50 | n=115 | n=500 | n=2000 | n=10000 |
|---|---|---|---|---|---|---|
| 0 | paired (McNemar) | 0.029 | 0.037 | 0.042 | 0.045 | 0.049 |
| 0 | unpaired (2-prop z) | 0.057 | 0.054 | 0.055 | 0.051 | 0.051 |
| 2 | paired (McNemar) | 0.033 | 0.048 | 0.096 | 0.283 | 0.883 |
| 2 | unpaired (2-prop z) | 0.061 | 0.068 | 0.103 | 0.248 | 0.808 |
| 3 | paired (McNemar) | 0.039 | 0.060 | 0.168 | 0.552 | 0.998 |
| 3 | unpaired (2-prop z) | 0.068 | 0.082 | 0.163 | 0.481 | 0.989 |
| 5 | paired (McNemar) | 0.055 | 0.107 | 0.395 | 0.939 | 1.000 |
| 5 | unpaired (2-prop z) | 0.088 | 0.128 | 0.367 | 0.889 | 1.000 |
| 8 | paired (McNemar) | 0.100 | 0.230 | 0.791 | 1.000 | 1.000 |
| 8 | unpaired (2-prop z) | 0.139 | 0.242 | 0.724 | 0.999 | 1.000 |

Calibration caveat, stated plainly: exact McNemar is conservative at small n (size
0.029 at n=50 vs nominal 0.05) while the z-test runs slightly hot (0.057). The
z-test's apparent power edge at n ≤ 115 is size inflation; at matched size (n ≥ 500)
the paired design wins every cell, and the analytic required-n comparison (2.2) is
the size-free statement.

At the static budgets, neither design resolves anything real: 5-point-gap power is
0.055 to 0.128 at n = 50 and 115. Pairing does not rescue the cap on n; it only
multiplies what a larger n buys.

### 2.2 Required n for 80% power (analytic)

Paired uses Connor's (1987) McNemar sample size, n = (z_{α/2}√ψ + z_β√(ψ−δ²))²/δ²
with ψ = p₁₀ + p₀₁ the discordance rate computed exactly from the Beta model;
unpaired uses the section-1.2 formula on the marginal rates.

| delta (pts) | paired n (instances) | unpaired n per arm | paired episodes | unpaired episodes |
|---|---|---|---|---|
| 2 | 7,849 | 9,806 | 15,699 | 19,612 |
| 3 | 3,489 | 4,355 | 6,978 | 8,711 |
| 5 | 1,256 | 1,565 | 2,513 | 3,129 |
| 8 | 491 | 608 | 982 | 1,216 |

### 2.3 What pairing buys, as a function of difficulty heterogeneity

Variance-reduction factor VRF = [p_A q_A + p_B q_B] / [p_A q_A + p_B q_B − 2 cov],
cov = p₁₁ − p_A p_B. δ = 5 points throughout; empirical column from the simulated
variance of the gap estimate at n=500.

| Beta(a,b) | Var(q_i) | outcome corr rho | VRF (analytic) | VRF (empirical) | paired n for 80% | unpaired n per arm |
|---|---|---|---|---|---|---|
| Beta(20,20) | 0.0061 | 0.024 | 1.02 | 1.02 | 1,530 | 1,565 |
| Beta(5,5) | 0.0227 | 0.091 | 1.10 | 1.11 | 1,426 | 1,565 |
| Beta(2,2) | 0.0500 | 0.199 | 1.25 | 1.25 | 1,256 | 1,565 |
| Beta(1,1) | 0.0833 | 0.332 | 1.50 | 1.51 | 1,049 | 1,565 |
| Beta(0.5,0.5) | 0.1250 | 0.497 | 1.99 | 1.99 | 790 | 1,565 |
| Beta(0.3,0.3) | 0.1562 | 0.621 | 2.64 | 2.65 | 598 | 1,565 |

The gain tracks Var(q_i) (VRF ≈ 1/(1−ρ), ρ = cov/outcome-variance). Homogeneous
difficulty (Beta(20,20)) makes pairing nearly worthless; strongly bimodal difficulty
(Beta(0.3,0.3), mass near 0 and 1) makes it worth 2.6x, cutting the 5-point
requirement from 1,565 per arm to 598 shared instances. Section 1.4's arithmetic
argues τ-bench-like task difficulty is exactly the bimodal case (per-task pass
probability near-binary outside a narrow band), so the high end of this table is the
operative one.

### 2.4 Internal checks

- Brute-force per-instance simulation (fresh q_i, per-outcome coin flips) vs the
  collapsed Multinomial/Binomial sampler, Beta(2,2), δ=5 pts, n=115, 20,000 reps:
  paired 0.106 vs 0.107, unpaired 0.128 vs 0.128; both within Monte Carlo error
  (~0.005).
- Size rows (δ=0) in 2.1 sit at or below nominal alpha for McNemar and within
  discreteness of nominal for the z-test.
- Empirical VRF matches analytic VRF to two decimals in every row of 2.3.

## 3. Cost accounting: annotations per fresh graded instance

Entries with no sourced figure say "unquantified"; no numbers are invented.

| Regime | Fixed cost | Marginal cost per fresh graded instance | Source |
|---|---|---|---|
| gtau seeded regeneration (this repo) | author the class: generator + re-key map + solvability/determinism audit (bounded, per class; gtau/rekey.py, gtau/branch.py, tests/) | 0 annotations. The oracle is re-derived by replaying the re-keyed golden program against the regenerated DB (gtau/replay.py); the same replay certifies solvability. Marginal cost of a fresh graded instance is CPU only. | this repo; DESIGN.md 'Regeneration by replay' |
| mining (LiveBench-, SWE-rebench-style) | build and maintain a collection + decontamination pipeline | per-instance collection AND per-instance quality filtering; unquantified (no public per-instance figure). Anchor for the filtering burden: SWE-bench Verified discarded ~68% of samples on quality screening (as cited in DESIGN.md; primary page unverified there). Freshness rate is capped by the arrival of new real-world tasks. | LiveBench arXiv:2406.19314; SWE-rebench arXiv:2505.20411 |
| templated QA (GSM-Symbolic-style) | per-template authoring, including the symbolic answer-derivation program | ~0 within an authored template (the answer key is derived symbolically per variant, not hand-written). But the derivation must exist in closed form, which confines the trick to single-turn, symbolically-answerable tasks; freshness is bounded by the authored template pool. Template count/effort: unquantified. | GSM-Symbolic arXiv:2410.05229 |
| hand-authoring (tau-bench itself) | domain, tools, policy wiki | 1 golden action sequence + required outputs + human verification per task ('Sierra-verified' in tasks_test.py). 115 retail + 50 airline tasks shipped, i.e. every graded instance that exists was hand-paid-for. Per-task hours: unquantified. | tau-bench arXiv:2406.12045 |

Honest note: templated QA also reaches ~zero marginal annotation within a template.
The delta claimed for gtau is zero marginal cost *for stateful interactive tasks*,
where no closed-form answer function exists and the only label source is replaying a
golden program against the regenerated state. This also corrects DESIGN.md's
phrasing "templated QA needs per-variant answer keys" (line ~529): the per-variant
key is derived automatically; the authored cost is per-template.

## 4. What this buys the paper

Putting sections 1 to 3 together: detecting a 5-point harness gap at a 50% baseline
needs 1,256 paired instances (2,513 episodes) or 1,565 per arm unpaired (3,129
episodes). Under hand-authoring that is 1,256+ new goldens with human verification;
under mining it is 1,256+ collected-and-filtered tasks; under the generator it is
compute only, and the paired variant is free because every harness replays the same
seed set. The static benchmark is an order of magnitude short of this resolution
(1.3), and its headline reliability metric pass^8 is shorter still (1.4). Necessity
(step 1) and uniqueness (step 2) of the mechanism, on arithmetic alone.
