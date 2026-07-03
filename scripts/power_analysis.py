#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "scipy>=1.11"]
# ///
"""Proof-ladder steps 1 (power argument) and 2 (cost accounting) from DESIGN.md.

Everything printed here feeds docs/receipts/POWER_AND_COST.md. Run:

    uv run scripts/power_analysis.py            # default seed 20260702
    uv run scripts/power_analysis.py --seed 7   # different Monte Carlo seed

Sections:
  A. Analytic binomial power of the static test set (n=115 retail, n=50 airline):
     SE of a single pass-rate, minimum detectable effect (MDE) for an unpaired
     two-proportion z-test (alpha=.05 two-sided, power=.80), required n for
     3/5/8-point gaps, and the same on the pass^8 scale.
  B. Paired-vs-unpaired Monte Carlo under instance-difficulty heterogeneity
     (q_i ~ Beta, harness gap = shift on the log-odds scale, outcomes of the two
     harnesses conditionally independent given q_i). Under that model the joint
     per-instance outcome distribution collapses exactly:
       - unpaired arm: each outcome is compound-Bernoulli, i.e. marginally
         Bernoulli(E[p(q)]), so the arm count is Binomial(n, p_bar);
       - paired: the per-instance (a,b) cell probabilities are the Beta-averaged
         joint, so the 2x2 table is Multinomial(n, (p11,p10,p01,p00)).
     Monte Carlo is over instance sampling only; a brute-force per-instance
     simulation cross-checks one cell. Tests: pooled two-proportion z (unpaired)
     vs exact McNemar (paired; same statistic as gtau/metrics.py:mcnemar).
     Budget matching: paired uses n instances x 2 harnesses = 2n episodes;
     unpaired uses n fresh instances per arm = 2n episodes. Equal episode budget.
  C. Cost accounting: annotations per fresh graded instance across generation
     regimes. Qualitative where no sourced number exists ("unquantified"), never
     invented.

Analytic formulas (printed with their outputs):
  SE(p, n)            = sqrt(p(1-p)/n)
  unpaired n per arm  = (z_{a/2} sqrt(2 pbar qbar) + z_b sqrt(p1 q1 + p2 q2))^2 / d^2
  MDE(p, n)           = the d at which that n equals the available n (bisection)
  McNemar n (Connor 1987) = (z_{a/2} sqrt(psi) + z_b sqrt(psi - d^2))^2 / d^2,
                        psi = p10 + p01 (discordance rate), d = p01 - p10
  variance reduction  = [pA qA + pB qB] / [pA qA + pB qB - 2 cov],
                        cov = p11 - pA pB  (per-instance outcome covariance)
"""
from __future__ import annotations

import argparse
from math import comb, sqrt

import numpy as np
from scipy.optimize import brentq
from scipy.stats import beta as beta_dist
from scipy.stats import binom, norm

ALPHA = 0.05
POWER = 0.80
Z_A = norm.ppf(1 - ALPHA / 2)  # 1.959964
Z_B = norm.ppf(POWER)          # 0.841621
K = 8                          # tau-bench's pass^8
QUAD_M = 400_000               # Beta quadrature midpoints (inverse-CDF grid)


# ----------------------------------------------------------------------------
# Section A: analytic binomial power of the static set
# ----------------------------------------------------------------------------

def se(p: float, n: int) -> float:
    return sqrt(p * (1 - p) / n)


def unpaired_n_per_arm(p1: float, p2: float) -> float:
    """Two-proportion z-test sample size per arm, alpha two-sided, power POWER."""
    d = abs(p2 - p1)
    pbar = (p1 + p2) / 2
    a = Z_A * sqrt(2 * pbar * (1 - pbar))
    b = Z_B * sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return (a + b) ** 2 / d ** 2


def mde_unpaired(p1: float, n: int) -> float | None:
    """Smallest upward gap detectable with the given n per arm; None if even the
    maximum possible gap (to p2=1) is underpowered."""
    hi = 1 - p1 - 1e-9
    f = lambda d: unpaired_n_per_arm(p1, p1 + d) - n
    if f(hi) > 0:
        return None
    return brentq(f, 1e-6, hi, xtol=1e-9)


def section_a() -> None:
    print("=" * 78)
    print("A. STATIC TEST SET: BINOMIAL SE, MDE, REQUIRED n")
    print(f"   alpha={ALPHA} two-sided (z={Z_A:.6f}), power={POWER} (z={Z_B:.6f})")
    print("=" * 78)

    ns = [115, 50]
    ps = [0.3, 0.5, 0.7]
    gaps = [0.03, 0.05, 0.08]

    print("\nA.1  SE of a single pass-rate estimate, SE = sqrt(p(1-p)/n)")
    print("\n| n | p | SE | 95% CI half-width |")
    print("|---|---|----|-------------------|")
    for n in ns:
        for p in ps:
            s = se(p, n)
            print(f"| {n} | {p:.1f} | {s:.4f} | ±{Z_A * s:.4f} ({Z_A * s * 100:.1f} pts) |")

    print("\nA.2  MDE for an unpaired A-vs-B comparison at the static n (per arm)")
    print("\n| n per arm | baseline p | MDE (points) |")
    print("|-----------|------------|--------------|")
    for n in ns:
        for p in ps:
            d = mde_unpaired(p, n)
            cell = f"{d * 100:.1f}" if d is not None else ">100-p (unreachable)"
            print(f"| {n} | {p:.1f} | {cell} |")

    print("\nA.3  Required n per arm to detect a gap of 3 / 5 / 8 points (unpaired)")
    print("\n| baseline p | gap (pts) | n per arm | vs retail 115 | vs airline 50 |")
    print("|------------|-----------|-----------|---------------|---------------|")
    for p in ps:
        for g in gaps:
            n_req = unpaired_n_per_arm(p, p + g)
            print(f"| {p:.1f} | {g * 100:.0f} | {n_req:,.0f} | {n_req / 115:.1f}x | {n_req / 50:.1f}x |")

    # --- pass^8 ---
    print(f"\nA.4  pass^{K}: the per-task estimator and the effective-n collapse")
    est = [comb(c, K) / comb(K, K) if c >= K else 0.0 for c in range(K + 1)]
    print(f"\nWith tau-bench's protocol (k = n_trials = {K}) the per-task estimator")
    print(f"C(c,{K})/C({K},{K}) over c=0..{K} successes is: {est}")
    print("i.e. EXACTLY binary per task: the indicator that all 8 trials passed.")
    print("(DESIGN.md line ~244 says 'near-binary'; at k = n_trials it is exact.)")

    print("\nHomogeneous-p map p -> p^8 (per-trial rate -> per-task pass^8 rate):")
    print("\n| per-trial p | p^8 | gap transmission 8p^7 |")
    print("|-------------|-----|------------------------|")
    for p in [0.3, 0.5, 0.7, 0.75, 0.9, 0.95, 0.987, 0.99]:
        print(f"| {p} | {p ** K:.4f} | {8 * p ** 7:.3f} |")
    lo = brentq(lambda p: p ** K - 0.1, 0.01, 0.999999)
    hi = brentq(lambda p: p ** K - 0.9, 0.01, 0.999999)
    print(f"\np^8 traverses 0.1 -> 0.9 over per-trial p in ({lo:.3f}, {hi:.3f}):")
    print("outside that band a task's pass^8 probability is <0.1 or >0.9, so even")
    print("with many trials the per-task quantity is near-binary in p.")

    print(f"\npass^{K} scale at the static n (pi = p^{K}, SE = sqrt(pi(1-pi)/T) over T tasks;")
    print("MDE/required-T from the same two-proportion formulas on the pi scale, where")
    print("the per-trial gap d induces a pi-gap (p+d)^8 - p^8):")
    print("\n| per-trial p | pi=p^8 | SE @T=115 | SE @T=50 | MDE(pi) @T=50 (pts) | per-trial gap 5pts -> pi-gap (pts) | T req. for that pi-gap |")
    print("|---|---|---|---|---|---|---|")
    for p in ps:
        pi = p ** K
        d_tr = 0.05
        pi2 = (p + d_tr) ** K
        gap = pi2 - pi
        t_req = unpaired_n_per_arm(pi, pi2)
        m50 = mde_unpaired(pi, 50)
        m50s = f"{m50 * 100:.1f}" if m50 is not None else "unreachable"
        print(f"| {p:.1f} | {pi:.4f} | {se(pi, 115):.4f} | {se(pi, 50):.4f} | {m50s} | "
              f"{gap * 100:.2f} | {t_req:,.0f} |")
    print("\nEffective-n collapse, stated: at mid-range per-trial rates the map p->p^8")
    print("multiplies a harness gap by 8p^7 (0.0625 at p=0.5, 0.66 at p=0.7), so the")
    print("required task count on the pass^8 scale grows by orders of magnitude over")
    print("the already-unaffordable pass^1 requirement. Only near p->1 (8p^7>1) does")
    print("pass^8 amplify gaps.")


# ----------------------------------------------------------------------------
# Section B: paired vs unpaired Monte Carlo
# ----------------------------------------------------------------------------

def beta_quad(a: float, b: float, m: int = QUAD_M) -> np.ndarray:
    """Equal-probability-mass quadrature grid for Beta(a,b) via inverse CDF."""
    u = (np.arange(m) + 0.5) / m
    q = beta_dist.ppf(u, a, b)
    return np.clip(q, 1e-12, 1 - 1e-12)


def shifted(q: np.ndarray, d: float) -> np.ndarray:
    """sigmoid(logit(q) + d)."""
    lo = np.log(q) - np.log1p(-q)
    return 1.0 / (1.0 + np.exp(-(lo + d)))


def solve_shift(q: np.ndarray, delta: float) -> float:
    """Log-odds shift d such that E[sigmoid(logit(q)+d)] - E[q] = delta."""
    if delta == 0:
        return 0.0
    return brentq(lambda d: shifted(q, d).mean() - q.mean() - delta, 0.0, 30.0)


def joint_cells(q: np.ndarray, d: float) -> tuple[float, float, float, float]:
    """Beta-averaged joint outcome cells (p11, p10, p01, p00) for harnesses
    A ~ Bern(q) and B ~ Bern(sigmoid(logit(q)+d)), conditionally independent
    given q. p10 = A-only, p01 = B-only."""
    pa, pb = q, shifted(q, d)
    p11 = float((pa * pb).mean())
    p10 = float((pa * (1 - pb)).mean())
    p01 = float(((1 - pa) * pb).mean())
    return p11, p10, p01, 1.0 - p11 - p10 - p01


def power_paired(cells, n: int, reps: int, rng) -> float:
    """Exact McNemar (two-sided binomial at 0.5 on discordant pairs; identical
    statistic to gtau/metrics.py:mcnemar), rejection at p <= alpha."""
    counts = rng.multinomial(n, cells, size=reps)
    a_only, b_only = counts[:, 1], counts[:, 2]
    nd = a_only + b_only
    pval = np.minimum(1.0, 2.0 * binom.cdf(np.minimum(a_only, b_only), nd, 0.5))
    return float((pval <= ALPHA).mean())


def power_unpaired(pa: float, pb: float, n: int, reps: int, rng) -> float:
    """Pooled two-proportion z-test on independent arms of n instances each."""
    xa = rng.binomial(n, pa, size=reps)
    xb = rng.binomial(n, pb, size=reps)
    pool = (xa + xb) / (2 * n)
    s = np.sqrt(pool * (1 - pool) * (2 / n))
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(s > 0, (xb - xa) / n / s, 0.0)
    return float((np.abs(z) >= Z_A).mean())


def mcnemar_n(cells, delta: float) -> float:
    """Connor (1987) paired sample size: n = (z_a sqrt(psi) + z_b sqrt(psi-d^2))^2/d^2."""
    psi = cells[1] + cells[2]
    return (Z_A * sqrt(psi) + Z_B * sqrt(psi - delta ** 2)) ** 2 / delta ** 2


def brute_force_check(a: float, b: float, delta: float, n: int, reps: int, rng) -> tuple[float, float]:
    """Per-instance simulation (fresh q_i per instance) of both designs, to verify
    the multinomial/binomial collapse used everywhere else."""
    q_quad = beta_quad(a, b)
    d = solve_shift(q_quad, delta)
    rej_p = 0
    rej_u = 0
    chunk = 2000
    done = 0
    while done < reps:
        c = min(chunk, reps - done)
        # paired: same instances, shared q
        q = rng.beta(a, b, size=(c, n)).clip(1e-12, 1 - 1e-12)
        pa, pb = q, shifted(q, d)
        oa = rng.random((c, n)) < pa
        ob = rng.random((c, n)) < pb
        a_only = (oa & ~ob).sum(axis=1)
        b_only = (ob & ~oa).sum(axis=1)
        nd = a_only + b_only
        pval = np.minimum(1.0, 2.0 * binom.cdf(np.minimum(a_only, b_only), nd, 0.5))
        rej_p += int((pval <= ALPHA).sum())
        # unpaired: two independent instance sets
        q1 = rng.beta(a, b, size=(c, n)).clip(1e-12, 1 - 1e-12)
        q2 = rng.beta(a, b, size=(c, n)).clip(1e-12, 1 - 1e-12)
        xa = (rng.random((c, n)) < q1).sum(axis=1)
        xb = (rng.random((c, n)) < shifted(q2, d)).sum(axis=1)
        pool = (xa + xb) / (2 * n)
        s = np.sqrt(pool * (1 - pool) * (2 / n))
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(s > 0, (xb - xa) / n / s, 0.0)
        rej_u += int((np.abs(z) >= Z_A).sum())
        done += c
    return rej_p / reps, rej_u / reps


def section_b(seed: int, reps: int) -> None:
    print("\n" + "=" * 78)
    print("B. PAIRED vs UNPAIRED: MONTE CARLO UNDER DIFFICULTY HETEROGENEITY")
    print(f"   model: q_i ~ Beta(2,2) (mean 0.5, Var 0.05); harness A ~ Bern(q_i),")
    print(f"   B ~ Bern(sigmoid(logit(q_i)+d)), d solved so E[pB]-E[pA] = delta;")
    print(f"   outcomes conditionally independent given q_i.")
    print(f"   {reps:,} Monte Carlo reps per cell, seed={seed}.")
    print("   Budget: paired = n instances x 2 harnesses; unpaired = n fresh")
    print("   instances per arm. Both = 2n episodes.")
    print("=" * 78)

    rng = np.random.default_rng(seed)
    a_par, b_par = 2.0, 2.0
    q = beta_quad(a_par, b_par)
    deltas = [0.0, 0.02, 0.03, 0.05, 0.08]
    ns = [50, 115, 500, 2000, 10000]

    print("\nB.1  Empirical power (rejection rate at alpha=.05); delta=0 row = size/calibration")
    print("\n| delta (pts) | design | " + " | ".join(f"n={n}" for n in ns) + " |")
    print("|---|---|" + "---|" * len(ns))
    results: dict[tuple[float, str], list[float]] = {}
    for delta in deltas:
        d = solve_shift(q, delta)
        cells = joint_cells(q, d)
        pa_bar, pb_bar = float(q.mean()), float(shifted(q, d).mean())
        row_p = [power_paired(cells, n, reps, rng) for n in ns]
        row_u = [power_unpaired(pa_bar, pb_bar, n, reps, rng) for n in ns]
        results[(delta, "paired")] = row_p
        results[(delta, "unpaired")] = row_u
        lbl = f"{delta * 100:.0f}"
        print(f"| {lbl} | paired (McNemar) | " + " | ".join(f"{x:.3f}" for x in row_p) + " |")
        print(f"| {lbl} | unpaired (2-prop z) | " + " | ".join(f"{x:.3f}" for x in row_u) + " |")

    print("\nB.2  Required n for 80% power (analytic; paired = Connor 1987 McNemar n,")
    print("     unpaired = two-proportion formula on the marginal rates)")
    print("\n| delta (pts) | paired n (instances) | unpaired n per arm | paired episodes | unpaired episodes |")
    print("|---|---|---|---|---|")
    for delta in [0.02, 0.03, 0.05, 0.08]:
        d = solve_shift(q, delta)
        cells = joint_cells(q, d)
        n_p = mcnemar_n(cells, cells[2] - cells[1])
        pa_bar, pb_bar = float(q.mean()), float(shifted(q, d).mean())
        n_u = unpaired_n_per_arm(pa_bar, pb_bar)
        print(f"| {delta * 100:.0f} | {n_p:,.0f} | {n_u:,.0f} | {2 * n_p:,.0f} | {2 * n_u:,.0f} |")

    print("\nB.3  Variance reduction from pairing as a function of difficulty variance")
    print("     (delta = 5 pts; VRF = [pAqA + pBqB] / [pAqA + pBqB - 2cov], cov = p11 - pA pB;")
    print("     empirical column: Var ratio of the estimated gap over "
          f"{reps:,} reps at n=500)")
    print("\n| Beta(a,b) | Var(q_i) | outcome corr rho | VRF (analytic) | VRF (empirical) | paired n for 80% | unpaired n per arm |")
    print("|---|---|---|---|---|---|---|")
    for ab in [(20, 20), (5, 5), (2, 2), (1, 1), (0.5, 0.5), (0.3, 0.3)]:
        a, b = ab
        var_q = a * b / ((a + b) ** 2 * (a + b + 1))
        qg = beta_quad(a, b)
        d = solve_shift(qg, 0.05)
        cells = joint_cells(qg, d)
        pa_bar = float(qg.mean())
        pb_bar = float(shifted(qg, d).mean())
        va = pa_bar * (1 - pa_bar)
        vb = pb_bar * (1 - pb_bar)
        cov = cells[0] - pa_bar * pb_bar
        vrf = (va + vb) / (va + vb - 2 * cov)
        rho = cov / sqrt(va * vb)
        # empirical VRF at n=500
        n0 = 500
        counts = rng.multinomial(n0, cells, size=reps)
        diff_p = (counts[:, 2] - counts[:, 1]) / n0  # (b_only - a_only)/n
        xa = rng.binomial(n0, pa_bar, size=reps)
        xb = rng.binomial(n0, pb_bar, size=reps)
        diff_u = (xb - xa) / n0
        vrf_emp = float(diff_u.var() / diff_p.var())
        n_p = mcnemar_n(cells, cells[2] - cells[1])
        n_u = unpaired_n_per_arm(pa_bar, pb_bar)
        print(f"| Beta({a},{b}) | {var_q:.4f} | {rho:.3f} | {vrf:.2f} | {vrf_emp:.2f} | "
              f"{n_p:,.0f} | {n_u:,.0f} |")

    print("\nB.4  Collapse cross-check: brute-force per-instance simulation vs the")
    print("     multinomial/binomial collapse (Beta(2,2), delta=5 pts, n=115, 20,000 reps)")
    bp, bu = brute_force_check(2.0, 2.0, 0.05, 115, 20_000, rng)
    cp = results[(0.05, "paired")][ns.index(115)]
    cu = results[(0.05, "unpaired")][ns.index(115)]
    mc_se = sqrt(0.25 / 20_000) + sqrt(0.25 / reps)
    print(f"     paired:   brute {bp:.3f} vs collapsed {cp:.3f} "
          f"(|diff| {abs(bp - cp):.4f}, ~MC SE {mc_se:.4f})")
    print(f"     unpaired: brute {bu:.3f} vs collapsed {cu:.3f} "
          f"(|diff| {abs(bu - cu):.4f})")
    print("\nB.5  The static set, even paired: at n=115, delta=5 pts, paired power is")
    print(f"     {results[(0.05, 'paired')][ns.index(115)]:.3f}; at n=50 it is "
          f"{results[(0.05, 'paired')][ns.index(50)]:.3f}. Pairing does not rescue the cap on n.")


# ----------------------------------------------------------------------------
# Section C: cost accounting
# ----------------------------------------------------------------------------

COST_ROWS = [
    (
        "gtau seeded regeneration (this repo)",
        "author the class: generator + re-key map + solvability/determinism audit "
        "(bounded, per class; gtau/rekey.py, gtau/branch.py, tests/)",
        "0 annotations. The oracle is re-derived by replaying the re-keyed golden "
        "program against the regenerated DB (gtau/replay.py); the same replay "
        "certifies solvability. Marginal cost of a fresh graded instance is CPU "
        "only.",
        "this repo; DESIGN.md 'Regeneration by replay'",
    ),
    (
        "mining (LiveBench-, SWE-rebench-style)",
        "build and maintain a collection + decontamination pipeline",
        "per-instance collection AND per-instance quality filtering; unquantified "
        "(no public per-instance figure). Anchor for the filtering burden: "
        "SWE-bench Verified discarded ~68% of samples on quality screening (as "
        "cited in DESIGN.md; primary page unverified there). Freshness rate is "
        "capped by the arrival of new real-world tasks.",
        "LiveBench arXiv:2406.19314; SWE-rebench arXiv:2505.20411",
    ),
    (
        "templated QA (GSM-Symbolic-style)",
        "per-template authoring, including the symbolic answer-derivation program",
        "~0 within an authored template (the answer key is derived symbolically "
        "per variant, not hand-written). But the derivation must exist in closed "
        "form, which confines the trick to single-turn, symbolically-answerable "
        "tasks; freshness is bounded by the authored template pool. Template "
        "count/effort: unquantified.",
        "GSM-Symbolic arXiv:2410.05229",
    ),
    (
        "hand-authoring (tau-bench itself)",
        "domain, tools, policy wiki",
        "1 golden action sequence + required outputs + human verification per "
        "task ('Sierra-verified' in tasks_test.py). 115 retail + 50 airline tasks "
        "shipped, i.e. every graded instance that exists was hand-paid-for. "
        "Per-task hours: unquantified.",
        "tau-bench arXiv:2406.12045",
    ),
]


def section_c() -> None:
    print("\n" + "=" * 78)
    print("C. COST ACCOUNTING: ANNOTATIONS PER FRESH GRADED INSTANCE")
    print("=" * 78)
    print("\n| Regime | Fixed cost | Marginal cost per fresh graded instance | Source |")
    print("|---|---|---|---|")
    for name, fixed, marginal, src in COST_ROWS:
        print(f"| {name} | {fixed} | {marginal} | {src} |")
    print("\nHonest note: templated QA also reaches ~zero marginal annotation within a")
    print("template. The delta claimed for gtau is not 'zero marginal cost' alone but")
    print("zero marginal cost FOR STATEFUL INTERACTIVE TASKS, where no closed-form")
    print("answer function exists and the only label source is replaying a golden")
    print("program against the regenerated state. (This also corrects DESIGN.md's")
    print("'templated QA needs per-variant answer keys': the per-variant key is")
    print("derived automatically; the authored cost is per-template.)")


# ----------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=20260702)
    ap.add_argument("--reps", type=int, default=100_000,
                    help="Monte Carlo reps per cell (default 100,000)")
    args = ap.parse_args()
    print(f"power_analysis.py  seed={args.seed}  reps={args.reps:,}  "
          f"alpha={ALPHA}  power={POWER}  quad_points={QUAD_M:,}")
    section_a()
    section_b(args.seed, args.reps)
    section_c()


if __name__ == "__main__":
    main()
