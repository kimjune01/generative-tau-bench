"""CI smoke over the soundness-audit script path (scripts/audit_soundness.py).

Tiny slice (2 tasks x 2 seeds, 16 branch seeds) through the same functions the
receipt run uses, including the ProcessPoolExecutor path (workers=2), so a break
in the audit machinery fails CI rather than the next receipt run. The full-scale
numbers live in docs/receipts/SOUNDNESS_AUDIT.md.
"""
from __future__ import annotations

from scripts.audit_soundness import render_report, run_branch_audit, run_rekey_audit


def test_rekey_audit_smoke():
    res = run_rekey_audit(["retail"], n_seeds=2, workers=2, max_tasks=2)
    c = res["retail"]
    assert c.instances == 4
    assert c.injective == c.coverage == c.determinism == c.faithful == c.solvable == 4
    assert c.invalid == 0, c.failures


def test_branch_audit_smoke():
    res = run_branch_audit(n_seeds=16, workers=2)
    b = res["retail:0"]
    assert b.instances == 16
    assert b.solvable == 16, b.failures
    assert set(b.branch_counts) == {"primary", "fallback"}  # seeds 0..15 cover both
    assert all(len(s) == 1 for s in b.branch_oracles.values())
    assert b.invalid == 0


def test_render_report_smoke():
    rekey = run_rekey_audit(["retail"], n_seeds=1, workers=1, max_tasks=1)
    branch = run_branch_audit(n_seeds=4, workers=1)
    meta = {"command": "smoke", "commit": "0000000", "date": "now", "wall_time": "0 s"}
    report = render_report(rekey, branch, meta)
    assert "Invalid-instance rate" in report
    assert "| retail | 1 |" in report
