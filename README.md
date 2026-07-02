# Generative τ-bench

A *method* for converting a database-shaped tool-agent benchmark into an evergreen,
contamination-resistant one, via seeded regeneration plus a **replay-derived oracle**.
τ-bench is the case study, not the product.

## The idea in one paragraph

τ-bench grades an agent by replaying a golden action program on a synthetic database
and hashing the final state. That oracle is *operational*: it is computed by running a
program, not by reading a stored answer, and anything computed by replay can be
recomputed under a transformation of its inputs. So publish a seeded generator that
emits the database, the golden program, and (by replay) the oracle, and you get fresh,
graded instances for free. Freshness by *generation*, not by mining new tasks
(LiveBench/SWE-rebench) or authoring per-variant answer keys (GSM-Symbolic). Games,
RL, vision, and software testing all found the same trick; the replay oracle is what
makes its strongest form ("generation *is* grading") reachable for stateful tool
agents. See [`DESIGN.md`](DESIGN.md) for the full argument and the oracle-strength ladder.

## Status

Schema-agnostic engine, validated on **two τ-bench domains through one code path**
plus per-domain descriptors:

| domain | descriptor | faithfulness (all test tasks × 5 seeds) |
|--------|-----------:|-----------------------------------------|
| retail | 5 field names | **575 / 575** |
| airline | 4 field names | **250 / 250** |

"Faithful" = re-keying preserves each golden's error pattern position-for-position,
the re-keyed golden reaches its own oracle (determinism), no original id leaks
(coverage), and the id map is injective. Full suite: 7 tests passing.

Honest scope (see [`docs/GENERALIZATION_ASSESSMENT.md`](docs/GENERALIZATION_ASSESSMENT.md)):
this proves the engine is *schema-general within the τ-bench family*. It does **not**
yet prove generalization across the precondition class — retail and airline share one
harness. The next step is one genuinely independent benchmark (candidate: AppWorld),
gated on whether it exposes a replay-able canonical solution.

## Domain of validity

The recipe applies iff a task is "database-shaped": (1) state is enumerable typed
entities with ids; (2) the solution is a program over those entities; (3) the oracle
is a deterministic function of the final state (replay-checkable); (4) a
constraint-preserving resampler exists. Real-world SWE/repo tasks fail these, which is
why coding benchmarks mine fresh tasks instead of regenerating them.

## Code layout

```
gtau/
  domains.py     Domain = the whole per-benchmark descriptor (id_collections + loaders)
  rekey.py       seeded, descriptor-driven re-key; schema-agnostic, names no domain
  replay.py      replay a golden through tau-bench's real tools; oracle_hash
  generate.py    (base task, seed, domain) -> fresh Instance with re-derived oracle
  hashing.py     to_hashable / consistent_hash, copied from tau-bench (attributed)
  world.py       minimal live world (no LLM user simulator, no API calls)
  eval.py        run_episode: drive an agent against a World, score vs oracle
  metrics.py     pass^k / pass@k (tau-bench estimator) + paired McNemar
  adapters/      pluggable agent interface + claude/codex CLI adapters
tests/           re-key faithfulness (both domains) + unit tests
scripts/run_eval.py   seeded trials -> pass^k (spawns a CLI agent; not run in CI)
```

Everything schema-specific lives in a `Domain`; the re-key, replay, and oracle code
name no benchmark. A `Domain`'s size is the portability metric.

## Setup and run

```bash
# clone tau-bench beside this repo (not vendored; MIT) and install into a venv
git clone https://github.com/sierra-research/tau-bench
uv venv && source .venv/bin/activate && uv pip install -e ./tau-bench pytest

# the faithfulness audit over both domains (pure, no API calls; ~4 min):
python -m pytest tests/ -q

# a CLI-agent episode (spawns claude/codex, which carry their own auth):
python scripts/run_eval.py --agent claude --domain retail --task 0 --trials 8
```

## Docs

- [`DESIGN.md`](DESIGN.md) — design and paper plan: contribution, domain-of-validity,
  contamination motivation, the cross-domain oracle-ladder spine, novelty, and the
  "what we must prove and the n it takes" evidentiary plan.
- [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md) and [`docs/PRIOR_ART_METHOD.md`](docs/PRIOR_ART_METHOD.md)
  — prior-art sweeps (component-level and method-level), citations verified.
- [`docs/GENERALIZATION_ASSESSMENT.md`](docs/GENERALIZATION_ASSESSMENT.md) — blunt
  reviewer-style assessment of what the generalization claim needs.
- [`docs/RELIABILITY-BENCHES.md`](docs/RELIABILITY-BENCHES.md) — background on how
  reliability benchmarks are built.

## Relationship to τ-bench

A derivative work of τ-bench (MIT, © 2024 Sierra), extended under the MIT license.
τ-bench is not vendored; clone it separately. See [`NOTICE`](NOTICE) and [`LICENSE`](LICENSE).
</content>
