#!/usr/bin/env python3
"""Run a CLI agent on seeded instances of a retail task and report reliability.

NOT run in the build session (it spawns the CLI agent). Usage:

    python scripts/run_eval.py --agent claude --task 0 --trials 8
    python scripts/run_eval.py --agent codex  --task 0 --trials 8 --seed-base 1000

Same seed set is used across agents in a round, so comparisons are paired
(common random numbers). See DESIGN.md.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gtau.generate import generate
from gtau.eval import run_episode
from gtau.metrics import pass_hat_k, pass_at_k
from gtau.adapters.cli_agent import claude_adapter, codex_adapter
from gtau.domains import DOMAINS

AGENTS = {"claude": claude_adapter, "codex": codex_adapter}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", choices=list(AGENTS), required=True)
    ap.add_argument("--domain", choices=list(DOMAINS), default="retail")
    ap.add_argument("--task", type=int, default=0, help="test task index")
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seed-base", type=int, default=0)
    ap.add_argument("--max-steps", type=int, default=30)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    domain = DOMAINS[args.domain]
    tools = domain.tools()
    agent = AGENTS[args.agent](timeout_s=args.timeout)
    successes = 0
    for t in range(args.trials):
        seed = args.seed_base + t
        inst = generate(domain, args.task, seed)
        res = run_episode(agent, inst, tools, max_steps=args.max_steps)
        successes += int(res.success)
        print(f"  seed={seed} success={res.success} r_state={res.r_state} "
              f"r_outputs={res.r_outputs}")

    spt = {args.task: successes}
    n = args.trials
    print(f"\nagent={args.agent} task={args.task} trials={n}")
    print(f"  pass@1  = {successes / n:.3f}")
    for k in (2, 4, min(8, n)):
        if k <= n:
            print(f"  pass^{k} = {pass_hat_k(spt, n, k):.3f}   "
                  f"pass@{k} = {pass_at_k(spt, n, k):.3f}")


if __name__ == "__main__":
    main()
