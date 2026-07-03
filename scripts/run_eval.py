#!/usr/bin/env python3
"""Run a CLI agent on seeded instances of a retail task and report reliability.

NOT run in the build session (it spawns the CLI agent). Usage:

    python scripts/run_eval.py --agent claude --task 0 --trials 8
    python scripts/run_eval.py --agent codex  --task 0 --trials 8 --seed-base 1000
    python scripts/run_eval.py --agent claude --task 0 --branch --user-sim claude --trials 4

Same seed set is used across agents in a round, so comparisons are paired
(common random numbers). Without --user-sim the instruction is handed to the agent
(intent leak): runs are marked comparable=False and are NOT tau-bench-comparable.
--branch draws instances from the branch-selection spec (gtau/branch.py) instead of
cosmetic re-keying. See DESIGN.md.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gtau.generate import generate
from gtau.branch import BRANCH_SPECS, generate_branch_instance
from gtau.eval import run_episode
from gtau.metrics import pass_hat_k, pass_at_k
from gtau.adapters.cli_agent import claude_adapter, codex_adapter
from gtau.domains import DOMAINS
from gtau.usersim import CLIUserSim

AGENTS = {"claude": claude_adapter, "codex": codex_adapter}
SIM_ARGV = {"claude": ["claude", "-p"], "codex": ["codex", "exec"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", choices=list(AGENTS), required=True)
    ap.add_argument("--domain", choices=list(DOMAINS), default="retail")
    ap.add_argument("--task", type=int, default=0, help="test task index")
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seed-base", type=int, default=0)
    ap.add_argument("--max-steps", type=int, default=30)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--branch", action="store_true",
                    help="branch-selection instances instead of cosmetic re-key")
    ap.add_argument("--user-sim", choices=list(SIM_ARGV), default=None,
                    help="mediate via a CLI user simulator (comparable=True)")
    ap.add_argument("--block", default=None, metavar="TOOL[,TOOL]",
                    help="observation ablation: these tools return an outage error "
                         "(positive control — forces reliance on weights; see "
                         "docs/receipts/RECALL_PROBE.md)")
    ap.add_argument("--verbose", action="store_true", help="print the transcript per trial")
    args = ap.parse_args()

    domain = DOMAINS[args.domain]
    tools = domain.tools()
    if args.block:
        class _Blocked:
            @staticmethod
            def invoke(data=None, **kwargs):
                return "Error: this service is temporarily unavailable"
        for name in args.block.split(","):
            if name not in tools:
                ap.error(f"--block: unknown tool {name!r}")
            tools = {**tools, name: _Blocked}
    agent = AGENTS[args.agent](timeout_s=args.timeout)
    successes = 0
    for t in range(args.trials):
        seed = args.seed_base + t
        if args.branch:
            spec = BRANCH_SPECS[f"{args.domain}:{args.task}"]
            inst = generate_branch_instance(spec, seed)
        else:
            inst = generate(domain, args.task, seed)
        sim = CLIUserSim(inst.instruction, SIM_ARGV[args.user_sim]) if args.user_sim else None
        res = run_episode(agent, inst, tools, max_steps=args.max_steps, user_sim=sim)
        successes += int(res.success)
        branch = f" branch={inst.branch}" if args.branch else ""
        err = f" error={res.error!r}" if res.error else ""
        print(f"  seed={seed} success={res.success} r_state={res.r_state} "
              f"r_outputs={res.r_outputs} comparable={res.comparable}{branch}{err}",
              flush=True)
        if args.verbose:
            for turn in res.transcript:
                print(f"    [{turn['role']}] {turn['content'][:160]}")

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
