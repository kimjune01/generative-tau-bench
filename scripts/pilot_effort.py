"""Step-4 pilot: Opus low vs high effort, paired (common-random-number) over
branch-selection instances. Estimates the gap, the McNemar discordance rate psi, and
the within-spec ICC of the paired difference — the inputs that decide whether a powered
confirmatory run is feasible (Connor's n) and how many specs it needs (n_eff).

Same weights, same contamination, only compute differs — Fable's clean instrument. The
user-sim is claude for BOTH arms, so its same-family status biases them symmetrically
(no differential confound). Paired: both arms see the SAME (spec, seed) instance.

NOT powered itself; a pilot. Logs each paired instance so a clearly-zero gap can stop it
early. Run:  python scripts/pilot_effort.py --seeds 3 2>&1 | tee docs/receipts/PILOT_EFFORT.log
"""
from __future__ import annotations
import argparse, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gtau.branch import BRANCH_SPECS, generate_branch_instance
from gtau.eval import run_episode
from gtau.adapters.cli_agent import claude_adapter
from gtau.domains import DOMAINS
from gtau.usersim import CLIUserSim

# harder specs first (multi-leg / argmin-over-many / multi-rung cascade), then a couple
# easy ones for calibration — the gap, if any, lives in the harder tasks.
PILOT_SPECS = ["retail:44", "retail:41", "retail:29", "retail:110", "retail:6",
               "retail:74", "retail:8", "retail:60", "retail:0", "retail:79"]
SIM_ARGV = ["claude", "-p"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--specs", default=None, help="comma-separated override")
    ap.add_argument("--max-steps", type=int, default=25)
    ap.add_argument("--timeout", type=int, default=500)
    args = ap.parse_args()
    specs = args.specs.split(",") if args.specs else PILOT_SPECS

    dom = DOMAINS["retail"]; tools = dom.tools()
    low = claude_adapter(timeout_s=args.timeout, effort="low")
    high = claude_adapter(timeout_s=args.timeout, effort="high")

    # 2x2 McNemar cells across all instances, and per-spec paired outcomes for ICC
    cells = {"11": 0, "10": 0, "01": 0, "00": 0}   # (low,high)
    per_spec = defaultdict(list)                    # spec -> list of (low_pass, high_pass)
    n_low = n_high = n = 0
    print(f"# pilot: low-vs-high, {len(specs)} specs x {args.seeds} seeds", flush=True)
    for key in specs:
        spec = BRANCH_SPECS[key]
        for seed in range(args.seeds):
            inst = generate_branch_instance(spec, seed)
            sim_l = CLIUserSim(inst.instruction, SIM_ARGV)
            r_low = run_episode(low, inst, tools, max_steps=args.max_steps, user_sim=sim_l)
            sim_h = CLIUserSim(inst.instruction, SIM_ARGV)
            r_high = run_episode(high, inst, tools, max_steps=args.max_steps, user_sim=sim_h)
            a, b = int(r_low.success), int(r_high.success)
            cells[f"{a}{b}"] += 1
            per_spec[key].append((a, b))
            n_low += a; n_high += b; n += 1
            print(f"  {key} seed={seed} low={a} high={b} branch={inst.branch}", flush=True)

    disc = cells["10"] + cells["01"]
    print(f"\n# n={n}  low pass={n_low/n:.3f}  high pass={n_high/n:.3f}  "
          f"gap={ (n_high-n_low)/n:+.3f}")
    print(f"# McNemar cells (low,high): 11={cells['11']} 10={cells['10']} "
          f"01={cells['01']} 00={cells['00']}  discordant={disc}  psi={disc/n:.3f}")
    # crude within-spec ICC of the paired difference d = high-low
    import statistics
    diffs_all = [h - l for v in per_spec.values() for (l, h) in v]
    if len(diffs_all) > 1 and statistics.pstdev(diffs_all) > 0:
        grand = statistics.mean(diffs_all)
        ss_total = sum((x - grand) ** 2 for x in diffs_all)
        ss_between = sum(len(v) * (statistics.mean([h - l for (l, h) in v]) - grand) ** 2
                         for v in per_spec.values())
        icc = ss_between / ss_total if ss_total else 0.0
        print(f"# within-spec ICC(diff) ~= {icc:.3f}  (0 = seeds independent within spec)")
    print("# per-spec (low,high) pass counts:")
    for k, v in per_spec.items():
        print(f"#   {k}: low={sum(l for l,_ in v)}/{len(v)} high={sum(h for _,h in v)}/{len(v)}")


if __name__ == "__main__":
    main()
