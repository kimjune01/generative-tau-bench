"""Parametric branch-selection: the reachable rung above cosmetic re-keying.

Where re-keying preserves the resolution path (so a memorized golden still passes),
branch-selection resamples the content that decides which branch of an authored
conditional task fires, and derives the golden by the task's own stated predicate.
The oracle stays construction-derived (we select among catalog variants that already
exist; we never synthesize an action). See DESIGN.md, the regeneration ladder.

Properties checked on the shipped retail spec (Yusuf Rossi keyboard/thermostat
exchange, base task 0):
  1. solvability: every derived golden replays with no tool error
  2. branch coverage: both branches fire across seeds (the seed actually varies it)
  3. distinctness: the two branches reach different end-states (the memorization signal)
  4. faithfulness: the fallback branch reproduces the shipped tau-bench task-0 oracle
  5. the memorization gap: a fixed memorized golden scores ~= the fallback fraction,
     while a predicate-following policy scores 1.0 — the gap cosmetic re-keying can't
     produce.

Run:  python -m pytest tests/test_branch_selection.py -q
"""
from __future__ import annotations
import copy

from gtau.action import Action
from gtau.branch import RETAIL_KEYBOARD_EXCHANGE as SPEC, generate_branch_instance
from gtau.domains import RETAIL
from gtau.replay import apply_action, oracle_hash
from tau_bench.envs.retail.tasks_test import TASKS_TEST

SEEDS = list(range(64))


def _tools():
    return RETAIL.tools()


def _replay_errors(golden, data, tools):
    d = copy.deepcopy(data)
    return [e for e in (apply_action(d, a, tools) for a in golden) if e.startswith("Error")]


def test_solvable_by_construction():
    tools = _tools()
    for s in SEEDS:
        inst = generate_branch_instance(SPEC, s)
        assert not _replay_errors(inst.golden, inst.data, tools), f"seed {s} golden errored"


def test_both_branches_fire():
    branches = {generate_branch_instance(SPEC, s).branch for s in SEEDS}
    assert branches == {"primary", "fallback"}, f"seed range didn't cover both branches: {branches}"


def test_branches_reach_distinct_end_states():
    prim = {i.oracle for i in (generate_branch_instance(SPEC, s) for s in SEEDS) if i.branch == "primary"}
    fall = {i.oracle for i in (generate_branch_instance(SPEC, s) for s in SEEDS) if i.branch == "fallback"}
    # each branch is internally deterministic (one canonical end-state) and the two differ
    assert len(prim) == 1 and len(fall) == 1
    assert prim.isdisjoint(fall)


def test_fallback_reproduces_shipped_golden():
    tools = _tools()
    base_golden = [Action.from_tau(a) for a in TASKS_TEST[0].actions]
    base_hash = oracle_hash(base_golden, RETAIL.load_data(), tools)
    fb = next(i for s in SEEDS if (i := generate_branch_instance(SPEC, s)).branch == "fallback")
    assert fb.oracle == base_hash


def test_memorization_gap_fires():
    """The contamination meter. A fixed memorized golden (shipped task 0) passes only on
    fallback seeds; a predicate-following policy passes on all. Under cosmetic re-keying
    the memorizer would pass on all seeds and the gap would be ~0."""
    tools = _tools()
    memorized = [Action.from_tau(a) for a in TASKS_TEST[0].actions]
    mem = skill = 0
    for s in SEEDS:
        inst = generate_branch_instance(SPEC, s)
        mem += oracle_hash(memorized, inst.data, tools) == inst.oracle
        skill += oracle_hash(inst.golden, inst.data, tools) == inst.oracle
    n = len(SEEDS)
    assert skill == n                        # skill policy always passes
    assert mem < n                           # memorizer strictly fails on primary seeds
    gap = (skill - mem) / n
    assert gap > 0.25, f"memorization gap too small to be a meter: {gap:.3f}"
