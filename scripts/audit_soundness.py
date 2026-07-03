#!/usr/bin/env python3
"""Scaled soundness audit: the generator's whole output, as a receipt.

DESIGN.md ("What we must prove") wants the soundness n *large and free*: the same
invariants that tests/test_rekey_invariance.py and tests/test_branch_selection.py
check at pytest scale, audited over thousands of generated instances, with an
explicit invalid-instance rate and provenance (command, commit, date, wall time)
written to docs/receipts/SOUNDNESS_AUDIT.md.

Per re-keyed instance (reusing gtau machinery, not reimplementing it):
  injectivity   the id map is one-to-one
  coverage      no original collected id leaks into the DB, golden args,
                instruction, or outputs
  determinism   generating twice at the same seed yields the same mapping and
                the same oracle hash
  faithfulness  the golden's tool-error pattern matches the base golden's,
                position for position
  solvability   no *new* tool error relative to the base golden (19 shipped
                retail goldens carry benign exploratory-read errors, so strict
                zero-error replay is reported separately, not required)

Per branch-selection spec (gtau/branch.py), over N seeds: solvability (zero tool
errors; construction-guaranteed), both-branches-fire, per-branch oracle
determinism (one end-state per branch), distinct end-states across branches, and
the empirical branch split.

Replays are pure and instances are checked-and-discarded, so the audit fans out
over a ProcessPoolExecutor and holds only counters. Worker-side memoization of
Domain.load_data/tasks/tools is sound because every gtau consumer deepcopies
before mutating (spec.resample, replay).

Run:  uv run python scripts/audit_soundness.py --domain all --seeds 25 --branch-seeds 1000 --workers 8
"""
from __future__ import annotations
import argparse
import copy
import datetime
import shlex
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gtau.action import Action
from gtau.branch import BRANCH_SPECS, generate_branch_instance
from gtau.domains import DOMAINS, Domain
from gtau.generate import generate_from_task
from gtau.rekey import _all_strings, _collect
from gtau.replay import apply_action

MAX_FAILURE_SAMPLES = 20  # per counter; enough to characterize, not to flood

# ---- counters ------------------------------------------------------------------


@dataclass
class RekeyCounts:
    """Pass counters over one domain's (task, seed) grid. `invalid` counts instances
    failing any required check; `solvable_strict` is informational (see module doc)."""
    instances: int = 0
    injective: int = 0
    coverage: int = 0
    determinism: int = 0
    faithful: int = 0
    solvable: int = 0            # no new tool error vs the base golden
    solvable_strict: int = 0     # zero tool errors outright
    invalid: int = 0
    failures: List[str] = field(default_factory=list)

    def merge(self, other: "RekeyCounts") -> None:
        for f in ("instances", "injective", "coverage", "determinism",
                  "faithful", "solvable", "solvable_strict", "invalid"):
            setattr(self, f, getattr(self, f) + getattr(other, f))
        self.failures = (self.failures + other.failures)[:MAX_FAILURE_SAMPLES]


@dataclass
class BranchCounts:
    """Counters over one branch spec's seed sweep. Aggregate properties (both fire,
    one oracle per branch, disjoint end-states) are judged after merging."""
    instances: int = 0
    solvable: int = 0
    invalid: int = 0
    branch_counts: Dict[str, int] = field(default_factory=dict)
    branch_oracles: Dict[str, Set[str]] = field(default_factory=dict)
    failures: List[str] = field(default_factory=list)

    def merge(self, other: "BranchCounts") -> None:
        self.instances += other.instances
        self.solvable += other.solvable
        self.invalid += other.invalid
        for b, n in other.branch_counts.items():
            self.branch_counts[b] = self.branch_counts.get(b, 0) + n
        for b, s in other.branch_oracles.items():
            self.branch_oracles.setdefault(b, set()).update(s)
        self.failures = (self.failures + other.failures)[:MAX_FAILURE_SAMPLES]


# ---- worker side -----------------------------------------------------------------

_CTX: Dict[str, Tuple[Domain, Dict[str, Any], Dict[str, Any], List[Any], Set[str]]] = {}


def _memo(fn):
    cell: list = []

    def wrapped():
        if not cell:
            cell.append(fn())
        return cell[0]

    return wrapped


def _domain_ctx(name: str):
    """Per-worker cache of (domain, base data, tools, tasks, original id set). Also
    memoizes the Domain's own loaders so generate_branch_instance (which reloads per
    call) does not pay the data-load cost 1000 times."""
    if name not in _CTX:
        dom = DOMAINS[name]
        dom.load_data = _memo(dom.load_data)
        dom.tasks = _memo(dom.tasks)
        dom.tools = _memo(dom.tools)
        base = dom.load_data()
        _CTX[name] = (dom, base, dom.tools(), dom.tasks(), _collect(base, dom.id_collections))
    return _CTX[name]


def _err_pattern(golden: List[Action], data: Dict[str, Any], tools: Dict[str, Any]) -> List[bool]:
    """Position-for-position tool-error mask; matches tests/test_rekey_invariance.py."""
    d = copy.deepcopy(data)
    return [str(apply_action(d, a, tools)).startswith("Error") for a in golden]


def _text_leaks(text: str, orig_ids: Set[str]) -> List[str]:
    """Original ids appearing verbatim in free text (the property rekey_text enforces)."""
    return [i for i in orig_ids if i in text]


def audit_rekey_task(job: Tuple[str, int, Tuple[int, ...]]) -> RekeyCounts:
    """All checks for one (domain, task) over its seed set. Instances are generated,
    checked, and dropped; only counters cross the process boundary."""
    domain_name, ti, seeds = job
    dom, base, tools, tasks, orig_ids = _domain_ctx(domain_name)
    task = tasks[ti]
    base_golden = [Action.from_tau(a) for a in task.actions]
    base_pattern = _err_pattern(base_golden, base, tools)
    c = RekeyCounts()

    def fail(check: str, seed: int, detail: str = "") -> None:
        if len(c.failures) < MAX_FAILURE_SAMPLES:
            c.failures.append(f"{domain_name} task {ti} seed {seed}: {check} {detail}".rstrip())

    for seed in seeds:
        inst = generate_from_task(task, seed, dom, base_data=base)
        c.instances += 1
        ok = True

        if len(set(inst.mapping.values())) == len(inst.mapping):
            c.injective += 1
        else:
            ok = False
            fail("non-injective map", seed)

        db_leak = _all_strings(inst.data, set()) & orig_ids
        golden_leak = _all_strings([a.kwargs for a in inst.golden], set()) & orig_ids
        text_leak = _text_leaks(inst.instruction, orig_ids)
        for out in inst.outputs:
            text_leak += _text_leaks(out, orig_ids)
        if not db_leak and not golden_leak and not text_leak:
            c.coverage += 1
        else:
            ok = False
            fail("id leak", seed,
                 f"db={sorted(db_leak)[:3]} golden={sorted(golden_leak)[:3]} text={text_leak[:3]}")

        inst2 = generate_from_task(task, seed, dom, base_data=base)
        if inst2.oracle == inst.oracle and inst2.mapping == inst.mapping:
            c.determinism += 1
        else:
            ok = False
            fail("non-deterministic regeneration", seed)

        pattern = _err_pattern(inst.golden, inst.data, tools)
        if pattern == base_pattern:
            c.faithful += 1
        else:
            ok = False
            fail("error-pattern drift", seed, f"base={base_pattern} got={pattern}")

        new_errors = [i for i, (p, bp) in enumerate(zip(pattern, base_pattern)) if p and not bp]
        if not new_errors:
            c.solvable += 1
        else:
            ok = False
            fail("new tool error", seed, f"at positions {new_errors}")
        if not any(pattern):
            c.solvable_strict += 1

        if not ok:
            c.invalid += 1
    return c


def audit_branch_chunk(job: Tuple[str, Tuple[int, ...]]) -> BranchCounts:
    """Solvability + branch/oracle bookkeeping for one seed chunk of one spec."""
    spec_key, seeds = job
    spec = BRANCH_SPECS[spec_key]
    _, _, tools, _, _ = _domain_ctx(spec.domain)
    c = BranchCounts()
    for seed in seeds:
        inst = generate_branch_instance(spec, seed)
        c.instances += 1
        errors = [i for i, e in enumerate(_err_pattern(inst.golden, inst.data, tools)) if e]
        if not errors:
            c.solvable += 1
        else:
            c.invalid += 1
            if len(c.failures) < MAX_FAILURE_SAMPLES:
                c.failures.append(f"{spec_key} seed {seed}: tool error at positions {errors}")
        c.branch_counts[inst.branch] = c.branch_counts.get(inst.branch, 0) + 1
        c.branch_oracles.setdefault(inst.branch, set()).add(inst.oracle)
    return c


# ---- orchestration ----------------------------------------------------------------


def _run(jobs: Sequence, fn, workers: int) -> Iterable:
    if workers <= 1:
        return map(fn, jobs)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, jobs))


def run_rekey_audit(domain_names: Sequence[str], n_seeds: int, workers: int,
                    max_tasks: Optional[int] = None) -> Dict[str, RekeyCounts]:
    """One job per (domain, task); each job sweeps all seeds. `max_tasks` exists for
    the CI smoke test only."""
    seeds = tuple(range(n_seeds))
    jobs = []
    for name in domain_names:
        n_tasks = len(DOMAINS[name].tasks())
        if max_tasks is not None:
            n_tasks = min(n_tasks, max_tasks)
        jobs += [(name, ti, seeds) for ti in range(n_tasks)]
    results: Dict[str, RekeyCounts] = {name: RekeyCounts() for name in domain_names}
    for job, counts in zip(jobs, _run(jobs, audit_rekey_task, workers)):
        results[job[0]].merge(counts)
    return results


def run_branch_audit(n_seeds: int, workers: int,
                     spec_keys: Optional[Sequence[str]] = None,
                     chunk: int = 32) -> Dict[str, BranchCounts]:
    keys = list(spec_keys if spec_keys is not None else BRANCH_SPECS)
    jobs = []
    for key in keys:
        seeds = list(range(n_seeds))
        jobs += [(key, tuple(seeds[i:i + chunk])) for i in range(0, len(seeds), chunk)]
    results: Dict[str, BranchCounts] = {key: BranchCounts() for key in keys}
    for job, counts in zip(jobs, _run(jobs, audit_branch_chunk, workers)):
        results[job[0]].merge(counts)
    return results


# ---- report ------------------------------------------------------------------------


def render_report(rekey: Dict[str, RekeyCounts], branch: Dict[str, BranchCounts],
                  meta: Dict[str, str]) -> str:
    lines = ["# Soundness Audit Receipt", ""]
    lines += [f"- Command: `{meta['command']}`",
              f"- Commit: `{meta['commit']}`",
              f"- Date: {meta['date']}",
              f"- Wall time: {meta['wall_time']}", ""]

    lines += ["## Re-key audit", "",
              "| Domain | Instances | Injective | Coverage | Deterministic | Faithful | Solvable (no new errors) | Clean replay (zero errors) | Invalid |",
              "|---|---|---|---|---|---|---|---|---|"]
    total = RekeyCounts()
    for name, c in rekey.items():
        total.merge(c)
        lines.append(f"| {name} | {c.instances} | {c.injective} | {c.coverage} | "
                     f"{c.determinism} | {c.faithful} | {c.solvable} | {c.solvable_strict} | {c.invalid} |")
    if len(rekey) > 1:
        lines.append(f"| **total** | {total.instances} | {total.injective} | {total.coverage} | "
                     f"{total.determinism} | {total.faithful} | {total.solvable} | {total.solvable_strict} | {total.invalid} |")
    lines += ["",
              "Coverage checks the DB, the golden's arguments, the instruction, and the outputs.",
              "Determinism regenerates each (task, seed) twice and compares mapping and oracle hash.",
              "Clean replay < Solvable is expected: some shipped base goldens carry benign",
              "exploratory-read tool errors, which faithfulness requires the re-keyed golden to",
              "reproduce position-for-position (see tests/test_rekey_invariance.py).", ""]

    lines += ["## Branch-selection audit", ""]
    branch_invalid = 0
    branch_instances = 0
    for key, b in branch.items():
        branch_invalid += b.invalid
        branch_instances += b.instances
        expected = set(BRANCH_SPECS[key].expected_branches)
        both_fire = set(b.branch_counts) == expected
        per_branch_det = all(len(s) == 1 for s in b.branch_oracles.values())
        oracle_sets = list(b.branch_oracles.values())
        # pairwise-disjoint across all k branches: union size == sum of sizes
        distinct = len(set().union(*oracle_sets)) == sum(len(s) for s in oracle_sets)
        split = " / ".join(
            f"{name} {n} ({100.0 * n / b.instances:.1f}%)"
            for name, n in sorted(b.branch_counts.items())) or "n/a"
        lines += [f"### Spec `{key}`", "",
                  "| Check | Result |",
                  "|---|---|",
                  f"| Instances | {b.instances} |",
                  f"| Solvable (zero tool errors) | {b.solvable}/{b.instances} |",
                  f"| All expected branches fire | {'pass' if both_fire else 'FAIL'} |",
                  f"| Per-branch oracle determinism | {'pass (one end-state per branch)' if per_branch_det else 'FAIL'} |",
                  f"| Distinct end-states across branches | {'pass' if distinct else 'FAIL'} |",
                  f"| Branch split | {split} |",
                  f"| Invalid | {b.invalid} |", ""]

    grand_total = total.instances + branch_instances
    grand_invalid = total.invalid + branch_invalid
    rate = 100.0 * grand_invalid / grand_total if grand_total else 0.0
    lines += ["## Overall", "",
              f"- Total instances audited: {grand_total} "
              f"({total.instances} re-keyed + {branch_instances} branch-selected)",
              f"- Invalid instances: {grand_invalid}",
              f"- Invalid-instance rate: {rate:.4f}% ({grand_invalid}/{grand_total})", ""]

    failures = total.failures + [f for b in branch.values() for f in b.failures]
    if failures:
        lines += ["## Failure samples (capped)", ""]
        lines += [f"- {f}" for f in failures[:2 * MAX_FAILURE_SAMPLES]]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--domain", choices=[*DOMAINS, "all"], default="all")
    ap.add_argument("--seeds", type=int, default=25, help="seeds per base task")
    ap.add_argument("--branch-seeds", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    domain_names = list(DOMAINS) if args.domain == "all" else [args.domain]
    spec_keys = [k for k, s in BRANCH_SPECS.items() if s.domain in domain_names]

    t0 = time.monotonic()
    rekey = run_rekey_audit(domain_names, args.seeds, args.workers)
    branch = run_branch_audit(args.branch_seeds, args.workers, spec_keys=spec_keys)
    wall = time.monotonic() - t0

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True,
                            cwd=Path(__file__).resolve().parent.parent).stdout.strip()
    meta = {
        "command": "uv run python " + shlex.join(sys.argv),
        "commit": commit or "unknown",
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "wall_time": f"{wall:.1f} s ({args.workers} workers)",
    }
    report = render_report(rekey, branch, meta)
    print(report)

    out = Path(__file__).resolve().parent.parent / "docs" / "receipts" / "SOUNDNESS_AUDIT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(f"[receipt written to {out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
