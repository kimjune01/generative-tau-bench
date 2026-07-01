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

Design stage. No generator code yet. Next step is the MVP: seeded re-keying of one
retail task class, replayed through τ-bench's existing grader, showing the oracle
still validates against the re-keyed state.

## Contents

- [`DESIGN.md`](DESIGN.md) — the full design and paper plan: regeneration by replay,
  width-in-classes, the seed protocol, paired evaluation, the equivalence oracle,
  an honest novelty map, the evaluation bar, risks, and milestones.
- [`PRIOR_ART.md`](PRIOR_ART.md) — prior-art search and blunt novelty assessment,
  with arXiv citations verified 2026-07-01.
- [`RELIABILITY-BENCHES.md`](RELIABILITY-BENCHES.md) — background study notes on how
  reliability benchmarks are built (τ-bench, SWE-bench Verified, HELM, ProcGen, the
  reliability-as-property literature) and the construction principles behind them.

## Relationship to τ-bench

This is a derivative work of τ-bench (MIT, Copyright 2024 Sierra), used and extended
under the MIT license. τ-bench itself is not vendored here; clone it separately. See
[`NOTICE`](NOTICE) for attribution and [`LICENSE`](LICENSE) for terms.
</content>
