"""Correctness of seeded re-keying (pure, no API calls).

Re-keying is a faithful alpha-rename of the initial DB and the golden program. It
does NOT commute with replay (some tools sort lists by id value, so re-keying can
reorder them), and it need not: the oracle is `replay(rekey(golden), rekey(db))`,
which is self-consistent. The properties that actually matter:

  1. injective mapping (no two ids collapse)
  2. coverage: no original collected id leaks into the re-keyed instance
  3. clean solvability: the re-keyed golden replays with no tool errors
  4. freshness: the golden's id arguments all change
  5. determinism: same seed => same oracle

Run:  PYTHONPATH=. python tests/test_rekey_invariance.py    (or: python -m pytest tests/ -q)
"""
from __future__ import annotations

from gtau.action import Action
from gtau.rekey import build_mapping, _collect
from gtau.replay import replay, apply_action, oracle_hash
from gtau.generate import generate_from_task, _base_retail_data, _base_retail_tasks

SEEDS = [0, 1, 7, 42, 12345]
TASK_INDICES = [0, 5, 10, 20, 50, 100]


def _all_strings(obj):
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k) if isinstance(k, str) else None
            out |= _all_strings(v)
    elif isinstance(obj, list):
        for e in obj:
            out |= _all_strings(e)
    elif isinstance(obj, str):
        out.add(obj)
    return out


def test_mapping_injective():
    base = _base_retail_data()
    for seed in SEEDS:
        m = build_mapping(base, seed)
        assert len(set(m.values())) == len(m), f"non-injective mapping at seed {seed}"


def test_no_original_ids_leak():
    base = _base_retail_data()
    tasks = _base_retail_tasks()
    original_ids = set().union(*_collect(base).values())
    for ti in TASK_INDICES:
        for seed in SEEDS:
            inst = generate_from_task(tasks[ti], seed, base_data=base)
            leaked = _all_strings(inst.data) & original_ids
            assert not leaked, f"task {ti} seed {seed}: original ids leaked: {list(leaked)[:5]}"
            gleaked = _all_strings([a.kwargs for a in inst.golden]) & original_ids
            assert not gleaked, f"task {ti} seed {seed}: golden references stale ids: {gleaked}"


def test_golden_solves_cleanly():
    """The re-keyed golden must replay on the re-keyed DB with no tool errors, and
    reach exactly its own oracle (determinism)."""
    tasks = _base_retail_tasks()
    for ti in TASK_INDICES:
        for seed in SEEDS:
            inst = generate_from_task(tasks[ti], seed)
            import copy
            data = copy.deepcopy(inst.data)
            for a in inst.golden:
                obs = apply_action(data, a)
                assert not str(obs).startswith("Error"), (
                    f"task {ti} seed {seed}: golden action {a.name} errored: {obs}"
                )
            assert oracle_hash(inst.golden, inst.data) == inst.oracle


def test_fresh_ids():
    tasks = _base_retail_tasks()
    for ti in TASK_INDICES:
        base_golden = [Action.from_tau(a) for a in tasks[ti].actions]
        base_ids = _all_strings([a.kwargs for a in base_golden]) & \
            set().union(*_collect(_base_retail_data()).values())
        if not base_ids:
            continue
        inst = generate_from_task(tasks[ti], 999)
        new_ids = _all_strings([a.kwargs for a in inst.golden])
        assert not (base_ids & new_ids), f"task {ti}: some golden ids unchanged"


def test_deterministic():
    tasks = _base_retail_tasks()
    a = generate_from_task(tasks[0], 42)
    b = generate_from_task(tasks[0], 42)
    assert a.oracle == b.oracle and a.mapping == b.mapping


if __name__ == "__main__":
    test_mapping_injective()
    test_no_original_ids_leak()
    test_golden_solves_cleanly()
    test_fresh_ids()
    test_deterministic()
    print("all re-key invariants OK")
