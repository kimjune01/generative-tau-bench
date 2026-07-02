# Generative τ-bench

A seeded, replay-oracle extension of [τ-bench](https://github.com/sierra-research/tau-bench)
for contamination-resistant, statistically honest tool-agent evaluation.

## The idea in one paragraph

τ-bench grades an agent by replaying a golden action sequence on a synthetic
database and hashing the final state. That oracle is *operational*: it is computed
by running a program, not by reading a stored answer. Anything computed by replay
can be recomputed under a transformation of its inputs, so the goldens need not be
static. Publish a seeded generator that emits the database, the golden program, and
(by replay) the oracle, and you get fresh instances on demand from an open,
auditable source. The contamination fix is regeneration, not secrecy. The same move
also buys error bars (unbounded fresh instances) and difficulty control (generated,
not hand-authored).

## Status

MVP built and the re-key invariance is validated (9/9 tests pass): seeded re-keying
produces coherent, fresh, solvable instances with re-derived oracles. Two known
limits, surfaced by review and recorded in DESIGN.md Risks: cosmetic re-keying is
likely near-inert against the *semantic* contamination that exists in tau-bench (the
real signal needs structural regeneration, unbuilt), and the self-contained-instruction
eval leaks the user simulator's private intent, so its scores are marked
`comparable=False` and are not tau-bench-comparable until a `UserSim` mediates.

Decisive next experiment: run one strong model on the retail suite, original vs
re-keyed, and read the paired gap (`gtau/metrics.py` McNemar). It needs model runs,
so it is not executed here.

## Code layout

```
gtau/
  action.py      Action record (name + kwargs), dependency-free
  hashing.py     to_hashable / consistent_hash, copied from tau-bench (attributed)
  rekey.py       seeded bijection over retail id namespaces; deep_remap; pure
  replay.py      replay a golden through tau-bench's real tools; oracle_hash (lazy import)
  generate.py    (base task, seed) -> fresh Instance with re-derived oracle
  world.py       minimal live retail world (no LLM user simulator, no API calls)
  eval.py        run_episode: drive an agent against a World, score vs oracle
  metrics.py     pass^k / pass@k (tau-bench estimator) + paired McNemar
  adapters/
    base.py      AgentAdapter interface, tool catalog, JSON action parser
    cli_agent.py CLIAgentAdapter + claude_adapter() / codex_adapter()
tests/test_rekey_invariance.py   the load-bearing claim, as a runnable check
scripts/run_eval.py              CLI entry: seeded trials -> pass^k
```

The re-key and hashing layers import nothing from `tau_bench` (verified), so the
core stays free of the litellm/openai/anthropic stack. `tau_bench` is imported
lazily only where the real tool logic and data are needed.

## Usage (not exercised in-repo yet)

```bash
# one-time: clone tau-bench beside this repo and install it into a venv
git clone https://github.com/sierra-research/tau-bench
uv venv && source .venv/bin/activate && uv pip install -e ./tau-bench

# the load-bearing invariance check (pure, no API calls):
python -m pytest tests/ -q

# a CLI-agent episode (spawns claude/codex, which carry their own auth):
python scripts/run_eval.py --agent claude --task 0 --trials 8
python scripts/run_eval.py --agent codex  --task 0 --trials 8
```

## Contents

- [`DESIGN.md`](DESIGN.md) — the full design and paper plan.
- [`PRIOR_ART.md`](PRIOR_ART.md) — prior-art search and novelty assessment, citations
  verified 2026-07-01.
- [`RELIABILITY-BENCHES.md`](RELIABILITY-BENCHES.md) — background notes on how
  reliability benchmarks are built and the construction principles behind them.

## Relationship to τ-bench

This is a derivative work of τ-bench (MIT, Copyright 2024 Sierra), used and extended
under the MIT license. τ-bench itself is not vendored here; clone it separately. See
[`NOTICE`](NOTICE) for attribution and [`LICENSE`](LICENSE) for terms.
</content>
