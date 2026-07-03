"""Parametric branch-selection: the reachable rung above cosmetic re-keying.

Where re-keying preserves the resolution path (so a memorized golden still passes),
branch-selection resamples the content that decides which branch of an authored
conditional task fires, and derives the golden by the task's own stated predicate.
The oracle stays construction-derived (we select among catalog variants that already
exist; we never synthesize an action). See DESIGN.md, the regeneration ladder.

Five properties, checked over EVERY spec in gtau.branch.BRANCH_SPECS (the EASY
retail family, 12 specs), 64 seeds each:
  1. solvability: every derived golden replays with no tool error
  2. branch coverage: every realizable branch fires across seeds (and each world's
     canonical catalog pattern realizes exactly the branch it was authored for)
  3. distinctness: branches reach different end-states (the memorization signal)
  4. faithfulness: the branch matching the shipped DB reproduces the shipped task's
     golden byte-for-byte and its oracle exactly
  5. the memorization gap: a fixed memorized golden scores exactly the shipped-branch
     fraction, while a predicate-following policy scores 1.0 — the gap cosmetic
     re-keying can't produce. Run with -s to see the per-spec gap table.

Plus the sibling anchors: tasks 0/1 share their primary-branch golden; the lamp
permutation pairs (6/7, 8/9) share per-target templates; the twin pairs (41/42,
97/98) share worlds, goldens, and oracles; and task 44's outputs are co-derived
with the pivot (refund quote moves with the chosen lamp).

Run:  uv run pytest tests/test_branch_selection.py -q -s
"""
from __future__ import annotations
import copy
from collections import Counter
from typing import Dict, List, Tuple

import pytest

from gtau.action import Action
from gtau.branch import BRANCH_SPECS, generate_branch_instance
from gtau.domains import RETAIL
from gtau.replay import apply_action, oracle_hash
from tau_bench.envs.retail.tasks_test import TASKS_TEST

SEEDS = list(range(64))
SPEC_KEYS = sorted(BRANCH_SPECS, key=lambda k: int(k.split(":")[1]))
BASE_DATA = RETAIL.load_data()
TOOLS = RETAIL.tools()

_instance_cache: Dict[Tuple[str, int], object] = {}


def _inst(key: str, seed: int):
    if (key, seed) not in _instance_cache:
        _instance_cache[key, seed] = generate_branch_instance(
            BRANCH_SPECS[key], seed, base_data=BASE_DATA)
    return _instance_cache[key, seed]


def _instances(key: str):
    return [_inst(key, s) for s in SEEDS]


def _acts(actions: List[Action]) -> List[Tuple[str, dict]]:
    return [(a.name, a.kwargs) for a in actions]


def _shipped_golden(key: str) -> List[Action]:
    idx = int(key.split(":")[1])
    return [Action.from_tau(a) for a in TASKS_TEST[idx].actions]


def _replay_errors(golden, data, tools):
    d = copy.deepcopy(data)
    return [e for e in (apply_action(d, a, tools) for a in golden) if e.startswith("Error")]


# --- property 1: solvability ---------------------------------------------------------

@pytest.mark.parametrize("key", SPEC_KEYS)
def test_solvable_by_construction(key):
    for s in SEEDS:
        inst = _inst(key, s)
        assert not _replay_errors(inst.golden, inst.data, TOOLS), f"{key} seed {s} golden errored"


# --- property 2: branch coverage ------------------------------------------------------

@pytest.mark.parametrize("key", SPEC_KEYS)
def test_all_realizable_branches_fire(key):
    spec = BRANCH_SPECS[key]
    observed = {i.branch for i in _instances(key)}
    assert observed == set(spec.expected_branches), \
        f"{key}: 64 seeds fired {observed}, expected {set(spec.expected_branches)}"


@pytest.mark.parametrize("key", [k for k in SPEC_KEYS if k != "retail:0"])
def test_every_world_realizes_its_branch(key):
    """World/selector coherence: applying each world's canonical availability
    pattern makes the instruction predicate select exactly that world's branch.
    A stale spec (catalog drift) fails here instead of shipping a wrong oracle."""
    spec = BRANCH_SPECS[key]
    for world in spec.worlds:
        data = copy.deepcopy(BASE_DATA)
        for (pid, vid), flag in world.avail.items():
            data["products"][pid]["variants"][vid]["available"] = flag
        _, branch = spec.derive_golden(data)
        assert branch == world.label, f"{key}: world {world.label} selected {branch}"


# --- property 3: distinct end-states --------------------------------------------------

@pytest.mark.parametrize("key", SPEC_KEYS)
def test_branches_reach_distinct_end_states(key):
    spec = BRANCH_SPECS[key]
    by_branch: Dict[str, set] = {}
    for i in _instances(key):
        by_branch.setdefault(i.branch, set()).add(i.oracle)
    # each branch is internally deterministic (one canonical end-state) ...
    assert all(len(s) == 1 for s in by_branch.values()), f"{key}: nondeterministic branch"
    # ... and no two branches share an end-state
    oracles = [next(iter(s)) for s in by_branch.values()]
    assert len(set(oracles)) == len(oracles), f"{key}: branches collide on an end-state"


# --- property 4: faithfulness to the shipped task -------------------------------------

@pytest.mark.parametrize("key", SPEC_KEYS)
def test_shipped_branch_reproduces_shipped_task(key):
    """The branch matching the shipped DB reproduces the shipped tau-bench golden
    byte-for-byte and hashes to the shipped oracle (generalizes the original
    test_fallback_reproduces_shipped_golden; note tasks 79/107 ship on their
    primary/first branch — surprise #3, shipped != fallback)."""
    spec = BRANCH_SPECS[key]
    shipped = _shipped_golden(key)
    base_hash = oracle_hash(shipped, BASE_DATA, TOOLS)
    matches = [i for i in _instances(key) if i.branch == spec.shipped_branch]
    assert matches, f"{key}: shipped branch {spec.shipped_branch} never fired"
    inst = matches[0]
    assert _acts(inst.golden) == _acts(shipped), f"{key}: shipped-branch golden drifted"
    assert inst.oracle == base_hash, f"{key}: shipped-branch oracle drifted"


# --- property 5: the memorization gap -------------------------------------------------

@pytest.mark.parametrize("key", SPEC_KEYS)
def test_memorization_gap_fires(key):
    """The contamination meter. A fixed memorized golden (the shipped task) passes
    exactly on shipped-branch seeds; a predicate-following policy passes on all.
    Under cosmetic re-keying the memorizer would pass on all seeds and the gap
    would be ~0."""
    spec = BRANCH_SPECS[key]
    memorized = _shipped_golden(key)
    counts: Counter = Counter()
    mem = skill = 0
    for s in SEEDS:
        inst = _inst(key, s)
        counts[inst.branch] += 1
        mem += oracle_hash(memorized, inst.data, TOOLS) == inst.oracle
        skill += oracle_hash(inst.golden, inst.data, TOOLS) == inst.oracle
    n = len(SEEDS)
    assert skill == n                                # predicate-follower always passes
    assert mem == counts[spec.shipped_branch], \
        f"{key}: memorizer passed off the shipped branch (mem={mem})"
    gap = (skill - mem) / n
    split = " ".join(f"{b}:{counts[b]}" for b in spec.expected_branches)
    print(f"[gap] {key:>9s}  split[{split}]  mem={mem}/{n}  skill={skill}/{n}  gap={gap:.3f}")
    assert gap >= 0.25, f"{key}: memorization gap too small to be a meter: {gap:.3f}"


# --- sibling anchors -------------------------------------------------------------------

def test_task0_and_task1_share_the_primary_golden():
    """Tasks 0 and 1 state the same predicate with different fallbacks; their primary
    branches coincide (exchange keyboard AND thermostat), so the two specs must emit
    identical goldens — and identical oracles, since the primary world is the same
    one-flag flip of the shipped DB."""
    i0 = next(i for s in SEEDS if (i := _inst("retail:0", s)).branch == "primary")
    i1 = next(i for s in SEEDS if (i := _inst("retail:1", s)).branch == "primary")
    assert _acts(i0.golden) == _acts(i1.golden)
    assert i0.oracle == i1.oracle


@pytest.mark.parametrize("a,b", [("retail:6", "retail:7"), ("retail:8", "retail:9")])
def test_lamp_permutation_pairs_share_targets_and_templates(a, b):
    """6/7 (and 8/9) rank the same candidate pool in different preference orders:
    the reachable target sets are equal, and for a common target the goldens are
    identical action lists (the branch decides the target, not the template)."""
    ga = {i.branch: _acts(i.golden) for i in _instances(a)}
    gb = {i.branch: _acts(i.golden) for i in _instances(b)}
    assert set(ga) == set(gb)
    for branch in ga:
        assert ga[branch] == gb[branch], f"{a}/{b} disagree on target {branch}"


@pytest.mark.parametrize("a,b", [("retail:41", "retail:42"), ("retail:97", "retail:98")])
def test_twin_specs_share_worlds_goldens_and_oracles(a, b):
    """41/42 and 97/98 restate the same predicate over the same catalog; per branch
    the worlds, goldens, and end-states must all coincide."""
    ia = {i.branch: i for i in _instances(a)}
    ib = {i.branch: i for i in _instances(b)}
    assert set(ia) == set(ib)
    for branch in ia:
        assert _acts(ia[branch].golden) == _acts(ib[branch].golden)
        assert ia[branch].oracle == ib[branch].oracle


# --- outputs coupling (inventory surprise #5) ------------------------------------------

def test_task44_outputs_coderive_with_the_pivot():
    """Task 44's output quotes the refund (owned lamp price minus chosen price):
    '17.99' is only correct on the shipped branch; the instance outputs and the
    golden's `calculate` expression must both move with the resampled argmin."""
    seen = set()
    for s in SEEDS:
        i = _inst("retail:44", s)
        target = i.golden[-1].kwargs["new_item_ids"][0]
        price = i.data["products"]["6817146515"]["variants"][target]["price"]
        assert i.outputs == [f"{153.23 - price:.2f}"]
        calc = next(a for a in i.golden if a.name == "calculate")
        assert calc.kwargs["expression"] == f"{price} - 153.23"
        seen.add(i.outputs[0])
    assert seen == {"17.99", "10.21", "3.22"}
    shipped = next(i for s in SEEDS if (i := _inst("retail:44", s)).branch == "5320792178")
    assert shipped.outputs == list(TASKS_TEST[44].outputs)


def test_branch_invariant_outputs_pass_through():
    """Every other spec's base task ships with no pivot-derived outputs; instances
    must carry the base outputs unchanged (empty for the whole EASY set but 44)."""
    for key in SPEC_KEYS:
        if key == "retail:44":
            continue
        base = list(TASKS_TEST[int(key.split(":")[1])].outputs or [])
        assert _inst(key, 0).outputs == base
