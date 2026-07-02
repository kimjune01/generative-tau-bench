"""Reliability and paired-comparison metrics.

pass^k mirrors tau-bench's unbiased estimator (run.py): per task with c successes
in n trials, the chance all k of a random k-subset succeed is C(c,k)/C(n,k),
averaged over tasks. pass@k is the at-least-one counterpart.

McNemar is the paired test for two agents on the SAME instances (common random
numbers): only discordant instances carry signal, which is why shared seeds tighten
model-vs-model comparison. See DESIGN.md.
"""
from __future__ import annotations
from math import comb
from typing import Dict, List, Sequence


def pass_hat_k(successes_per_task: Dict, n_trials: int, k: int) -> float:
    """successes_per_task: task_id -> count of successful trials (each out of n_trials)."""
    if k > n_trials:
        raise ValueError(f"pass^{k} needs at least {k} trials, got n={n_trials}")
    denom = comb(n_trials, k)
    total = sum(comb(c, k) / denom for c in successes_per_task.values())
    return total / len(successes_per_task) if successes_per_task else 0.0


def pass_at_k(successes_per_task: Dict, n_trials: int, k: int) -> float:
    if k > n_trials:
        raise ValueError(f"pass@{k} needs at least {k} trials, got n={n_trials}")
    denom = comb(n_trials, k)
    total = sum(1.0 - comb(n_trials - c, k) / denom for c in successes_per_task.values())
    return total / len(successes_per_task) if successes_per_task else 0.0


def mcnemar(a_success: Sequence[bool], b_success: Sequence[bool]) -> Dict[str, float]:
    """Paired comparison of two agents over the same instances. Returns discordant
    counts and McNemar's exact two-sided p-value (binomial at p=0.5 on the
    discordant pairs). Only discordant instances carry signal."""
    if len(a_success) != len(b_success):
        raise ValueError("paired inputs must be the same length")
    b_only = sum(1 for a, b in zip(a_success, b_success) if b and not a)  # b wins
    a_only = sum(1 for a, b in zip(a_success, b_success) if a and not b)  # a wins
    n = a_only + b_only
    p = _mcnemar_exact_p(min(a_only, b_only), n) if n else 1.0
    return {"a_only": a_only, "b_only": b_only, "discordant": n, "p_value": p}


def _mcnemar_exact_p(x: int, n: int) -> float:
    """Two-sided exact binomial test at p=0.5: 2 * P(X <= x), capped at 1."""
    lower = sum(comb(n, i) for i in range(0, x + 1)) / (2 ** n)
    return min(1.0, 2.0 * lower)
