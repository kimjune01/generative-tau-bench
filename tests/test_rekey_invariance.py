"""Correctness of seeded, descriptor-driven re-keying (pure, no API calls).

Now runs over BOTH tau-bench domains (retail and airline) through the *same* engine,
parameterized only by each domain's `id_collections` descriptor. This is Leg 2 of the
generalization argument: two schemas, one engine, no schema-specific re-key code.

Invariants, checked over each full test suite:
  1. faithfulness: re-keying preserves each golden's error pattern position-for-position
     (some goldens have benign exploratory reads that error in the original too)
  2. determinism: the re-keyed golden reaches its own oracle
  3. coverage: no original collected id leaks into the regenerated instance
  4. injectivity: the id map is one-to-one

Run:  python -m pytest tests/ -q
"""
from __future__ import annotations
import copy

from gtau.action import Action
from gtau.rekey import build_mapping, _collect, _all_strings
from gtau.replay import apply_action, oracle_hash
from gtau.generate import generate_from_task
from gtau.domains import RETAIL, AIRLINE

SEEDS = [0, 1, 7, 42, 12345]


def _err_pattern(golden, data, tools):
    d = copy.deepcopy(data)
    return [str(apply_action(d, a, tools)).startswith("Error") for a in golden]


def _audit(domain) -> int:
    base = domain.load_data()
    tools = domain.tools()
    tasks = domain.tasks()
    orig_ids = _collect(base, domain.id_collections)
    checked = 0
    for ti, task in enumerate(tasks):
        golden = [Action.from_tau(a) for a in task.actions]
        op = _err_pattern(golden, base, tools)
        for seed in SEEDS:
            inst = generate_from_task(task, seed, domain, base_data=base)
            assert _err_pattern(inst.golden, inst.data, tools) == op, (
                f"{domain.name} task {ti} seed {seed}: re-key changed the error pattern"
            )
            assert oracle_hash(inst.golden, inst.data, tools) == inst.oracle
            leak = _all_strings(inst.data, set()) & orig_ids
            assert not leak, (
                f"{domain.name} task {ti} seed {seed}: leaked ids {list(leak)[:3]}"
            )
            checked += 1
    return checked


def test_retail_faithful():
    assert _audit(RETAIL) > 0


def test_airline_faithful():
    assert _audit(AIRLINE) > 0


def test_injective():
    for domain in (RETAIL, AIRLINE):
        base = domain.load_data()
        for seed in SEEDS:
            m = build_mapping(base, seed, domain.id_collections)
            assert len(set(m.values())) == len(m), f"{domain.name} seed {seed} non-injective"


if __name__ == "__main__":
    for d in (RETAIL, AIRLINE):
        print(f"{d.name}: {_audit(d)} checks faithful")
    print("injectivity OK")
