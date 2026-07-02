# Reliability benchmarks, and what they teach about building good ones

A study note, sibling to the METR time-horizon audit in this repo. That audit
looked at one bench along the *construction* axis: what disclosures it makes, how
it handles unfinished tasks, whether it labels failures. This note looks at a
family of benchmarks along a second axis: what they *measure* when they measure
reliability rather than raw capability. The two axes meet, because most of the
METR audit's findings turn out to be named principles somewhere in this
literature.

Two claims organize the note:

1. Reliability is not capability, and the gap between them is *multiplicative*, so
   it has to be measured directly. A single headline number almost always reports
   capability and calls it reliability.
2. A benchmark is trustworthy on two independent counts: the metric measures the
   thing it claims (construct validity), and the data underneath is clean
   (solvable tasks, labeled failures, error bars). A bench can be strong on one
   and weak on the other. METR is.

---

## Part 1: reliability is not capability

Capability is a *maximum* over attempts. Reliability is a *lower tail*. Almost
every inflated eval number comes from reporting the first when readers assume the
second.

- **Capability** = does it work at all: best of k runs (`pass@k`), best phrasing,
  one lucky seed.
- **Reliability** = does it work every time, under repetition, rephrasing, and
  length.

The gap is not additive, it is exponential, and the same compounding math shows up
in three places:

- **Across repeated trials.** For per-task success `p` over `k` i.i.d. trials, the
  chance all `k` succeed is `p^k`. This is `pass^k` (§2.1).
- **Across sequential steps.** For per-step success `p` over a `T`-step task,
  completion probability is `p^T`. This is the long-horizon decay behind METR's
  time-horizon curve.
- **The optimistic mirror.** Because horizon length grows fast in per-step
  accuracy, small single-step gains compound into large horizon gains. "The
  Illusion of Diminishing Returns" (arXiv:2509.09677) argues both directions:
  marginal step-accuracy gains "compound into exponential improvements in the
  length of tasks a model can successfully complete," while real decay runs
  *faster* than the i.i.d. model because "models self-condition on their previous
  mistakes, leading to more mistakes in subsequent turns."

The reliability-specific reading of METR's own metric falls straight out of this:
a "time horizon" is just the task length at which the compounding curve crosses a
chosen probability threshold. That is why METR's 80% horizon is much shorter than
its 50% horizon (the exact multiplier is not confirmed here). Picking the
threshold *is* picking how much reliability you demand.

There is also a qualitative sense of reliability, distinct from any success rate.
Zhou et al., *Larger and more instructable language models become less reliable*
(Nature, 2024), define it as **predictability of error**: errors should sit where
humans expect them (hard items), and a model should abstain rather than
confabulate. Their finding is that scaling plus instruction tuning made models
*less* reliable in exactly these senses. Quotes below are from the open-access PMC
mirror, not diffed against the typeset PDF:

> "scaled-up, shaped-up models do not secure areas of low difficulty in which
> either the model does not err or human supervision can spot the errors."

> "scaling and shaping currently exchange avoidance for more incorrectness."

The lesson for a benchmark: a mean success rate cannot see any of this. Confident
wrong answers and lucky-run capability both average into the same number.

---

## Part 2: four case studies, each pairing a metric with a construction lesson

### 2.1 τ-bench / τ²-bench: the reliability metric done right

τ-bench (Sierra, arXiv:2406.12045) evaluates a tool-using agent across multi-turn
conversations with an LLM-simulated user, in retail and airline domains; τ²-bench
(arXiv:2506.07982) adds telecom.

**Metric: `pass^k`.** `pass@k` asks "will at least one of k attempts work" and
*rises* with k. `pass^k` asks "will all k attempts work" and *falls* with k. They
answer opposite questions: retry-friendly capability vs deployment reliability. The
canonical unbiased estimator, per task run `n` times with `c` successes, is
`E_task[ C(c,k) / C(n,k) ]` (reconstructed from secondary sources; the typeset
equation was not extractable from the PDF, so do not attribute the exact form
verbatim). The reported collapse is the whole point:

> "state-of-the-art function calling agents (like gpt-4o) succeed on <50% of the
> tasks, and are quite inconsistent (pass^8 <25% in retail)."

A ~60% relative drop from `pass^1` to `pass^8`: strong average capability, poor
reliability, invisible to a mean.

**Construction lesson: deterministic, outcome-based grading.** τ-bench compares the
*final database state* to an annotated goal state by hash, and checks required
outputs were communicated. LLMs *drive* the simulated user; they never *grade* the
outcome. This quarantines the one noisy component (user simulation) away from a
crisp verifier. τ²-bench hardens the construction further: a compositional task
generator built from individually verifiable atomic actions (controlled difficulty
and coverage instead of hand-authored one-offs), and a dual-control environment
where the user must also act (which costs top models up to ~25 points).

*Transferable principle:* verify the world-state, not the transcript, then stress
for consistency with `pass^k` instead of averaging.

### 2.2 SWE-bench → Verified → abandoned: the solvability lesson

This is the direct echo of the METR audit's `apron`/`beach` finding, and it played
out publicly over two years.

SWE-bench (arXiv:2310.06770) asks a model to resolve a real GitHub issue; a patch
is graded by held-out `FAIL_TO_PASS` and `PASS_TO_PASS` tests. The original set had
severe hygiene problems, quantified later by OpenAI's annotation campaign:

- **38.3%** of sampled issues were underspecified (multiple valid fixes, tests
  reward one).
- **61.1%** had tests that "may unfairly mark valid solutions as incorrect."
- Plus broken environments and solution leakage in issue threads.

**SWE-bench Verified** (OpenAI with the original authors, Aug 2024): 93 professional
developers screened instances for specification clarity and test validity, and
**68.3% of samples were filtered out**, leaving a clean 500. GPT-4o roughly doubled
(~16% → 33.2%), so much of the original "failure" was benchmark noise, not model
incapacity. (The often-repeated "3 annotators per sample" is not cleanly confirmed
in the primary text; the three Verified quotes below are from a faithful mirror
because the canonical page blocked automated fetch.)

> "Our annotation process resulted in 68.3% of SWE-bench samples being filtered out
> due to underspecification, unfair unit tests, or other issues."

The killer parallel is the 2026 sequel, *Why we no longer evaluate SWE-bench
Verified*: OpenAI audited 138 Verified problems that o3 failed across 64
independent runs, with ≥6 engineers each, and found **59.4%** had test/spec issues
"rendering them extremely difficult or impossible even for the most capable model
or human to solve" (35.5% narrow tests, 18.8% wide tests, plus contamination).
These figures come from secondary coverage of the post, not a direct fetch.

*Transferable principle, and the whole reason it matters here:* a task no strong
model solves across many runs is more likely **broken than hard**. The
persistently-failed tail is a signal to *audit*, not to trust. OpenAI found the bad
tasks precisely by flagging the never-solved runs and re-reviewing them, which is
exactly the reconciliation step the METR audit says is missing for `apron` and
`beach`.

### 2.3 Reliability as a measured property

Beyond any single bench, a small literature treats reliability as the object of
study:

- **Zhou et al. (Nature 2024)**, above: reliability as predictability of error,
  measured across five domains with difficulty concordance, prompt stability, and
  avoidance-vs-error.
- **Horizon decay**: the `p^T` compounding, with self-conditioning making it worse
  than i.i.d. (arXiv:2509.09677). A constructive counterpoint, *Solving a
  Million-Step LLM Task with Zero Errors* (arXiv:2511.09030), drives per-step error
  low enough (decomposition, voting) that the product stays near 1 over ~10^6 steps.
- **Self-consistency** (arXiv:2203.11171) is the adjacent decoding-time notion
  (sample many chains, majority vote). It is about *answer agreement*, not repeated
  end-to-end task success, so it is distinct from `pass^k` and often conflated with
  it.

*Transferable principle:* measure the whole distribution under repetition,
perturbation, and length, not a single best-case point. Pick a reliability
threshold and report the rate or horizon at which the system holds it.

### 2.4 HELM: standardize conditions, then measure more than one thing

HELM (Liang, Bommasani, Lee, et al., arXiv:2211.09110) is the reference for
breadth and comparability.

> "we adopt a multi-metric approach: We measure 7 metrics (accuracy, calibration,
> robustness, fairness, bias, toxicity, and efficiency) for each of 16 core
> scenarios when possible."

Two reliability-adjacent metrics are first-class: *robustness* (stability under
mild, semantics-preserving perturbations like typos and casing) and *calibration*
(HELM notes accuracy and calibration can move in opposite directions). But HELM's
most durable contribution is comparability through standardization:

> "Prior to HELM, models on average were evaluated on just 17.9% of the core HELM
> scenarios... We improve this to 96.0%: now all 30 models have been densely
> benchmarked on the same core scenarios and metrics under standardized
> conditions."

*Transferable principle:* hold the protocol fixed across models (same scenarios,
same prompts) so numbers are comparable, and report a *vector* of desiderata so a
headline accuracy can never hide a calibration or robustness failure.

---

## Part 3: what makes a benchmark trustworthy

Synthesized from the construction-methodology literature (BetterBench, Reuel et
al., arXiv:2411.12990, is the most on-point: 46 lifecycle best practices scored
against 24 benchmarks, finding "most benchmarks do not report statistical
significance of their results nor allow for their results to be easily
replicated").

| Property | What it means | Source |
|---|---|---|
| Construct validity | the task measures the ability claimed, not a narrow proxy sold as "general" | Raji et al. 2111.15366; BetterBench |
| Multi-metric | report accuracy *with* calibration, robustness, fairness; expose trade-offs | HELM 2211.09110 |
| Standardized conditions | all models on the same scenarios and prompts, head-to-head | HELM 2211.09110 |
| Statistical rigor | variance / significance / error bars, not one bolded SOTA number | BetterBench; Miller 2411.00640 |
| Contamination control | unique IDs or encrypted instances; detect test-set leakage | BetterBench; Golchin & Surdeanu 2308.08493 |
| Robustness to perturbation | stable under mild, meaning-preserving corruption | HELM 2211.09110 |
| Task solvability / quality | audit broken and unsolvable tasks; a noisy test set destabilizes rankings | SWE-bench Verified; Northcutt et al. 2103.14749 |
| Anti-saturation | design headroom in; consider dynamic or adversarial data | Kiela et al. 2104.14337 |
| Documentation | motivation, composition, collection, uses; working code and license | Gebru et al. 1803.09010; BetterBench |

Two supporting quotes worth keeping:

> "Fundamentally, evaluations are experiments; but the literature on evaluations
> has largely ignored the literature from other sciences on experiment analysis
> and planning." (Miller, *Adding Error Bars to Evals*, arXiv:2411.00640)

> "Construct validity refers to the degree to which a test or measurement tool
> accurately measures the construct it intends to measure." (BetterBench)

---

## Part 4: back to the METR audit

The audit's findings are not idiosyncratic. Each is a named principle from above,
which is the useful result: it tells us where METR is strong and where the gaps
are, on a shared scale rather than an ad-hoc one.

| METR audit finding | Principle it instances |
|---|---|
| `apron`/`beach`: 10m tasks nobody ever solved, fit as exact points | task solvability (SWE-bench Verified; the never-solved tail is broken, not hard) |
| `fatal_error_from` null on 95.7% of runs | task quality / failure diagnosis: you cannot tell a hard task from a broken one without labels |
| unfinished tasks fit as exact, censoring declined | reliability-threshold / horizon design: `p^T` demands you model the tail, not assert a coordinate |
| no CIs on the absolute level | statistical rigor (Miller, BetterBench: evals are experiments) |
| the estimated human-time axis | construct validity of the x-axis: is "hours of human work" measured or asserted |
| trend robust across the multiverse | standardized conditions and multi-arm sensitivity, done well |
| discloses `human_source`, publishes limitations | documentation, done well |

Read this way, METR scores high on standardization, disclosure, and trend
robustness, and has two real gaps: task-level solvability reconciliation and
level-CIs. That is the same generous verdict the audit reached, now stated in the
field's own vocabulary. The strongest benches in this note (τ-bench's hash-checked
verifier, SWE-bench Verified's human solvability filter) are precisely strong
where METR is thin, which is why they are the right comparison set.

The one metric-design idea METR could borrow outright: report a reliability
threshold explicitly and treat the 50% vs 80% horizon gap as a first-class result,
because that gap *is* the reliability the single headline horizon hides. That is
`pass^k` thinking applied to the time axis.

---

## Sources

Reliability metrics and property:
- τ-bench, [arXiv:2406.12045](https://arxiv.org/abs/2406.12045); τ²-bench, [arXiv:2506.07982](https://arxiv.org/abs/2506.07982); [Sierra blog](https://sierra.ai/blog/benchmarking-ai-agents)
- Zhou et al., *Larger and more instructable LMs become less reliable*, [Nature 2024](https://www.nature.com/articles/s41586-024-07930-y) ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446866/), [code](https://github.com/wschella/llm-reliability))
- *The Illusion of Diminishing Returns*, [arXiv:2509.09677](https://arxiv.org/abs/2509.09677)
- *Solving a Million-Step LLM Task with Zero Errors*, [arXiv:2511.09030](https://arxiv.org/abs/2511.09030)
- Self-consistency, [arXiv:2203.11171](https://arxiv.org/abs/2203.11171)
- METR, *Measuring AI Ability to Complete Long Tasks*, [arXiv:2503.14499](https://arxiv.org/abs/2503.14499)

Construction and hygiene:
- SWE-bench, [arXiv:2310.06770](https://arxiv.org/abs/2310.06770); [Introducing SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/); [Why we no longer evaluate SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
- HELM, [arXiv:2211.09110](https://arxiv.org/abs/2211.09110)
- BetterBench, [arXiv:2411.12990](https://arxiv.org/abs/2411.12990)
- *Adding Error Bars to Evals*, [arXiv:2411.00640](https://arxiv.org/abs/2411.00640)
- *Datasheets for Datasets*, [arXiv:1803.09010](https://arxiv.org/abs/1803.09010)
- *AI and the Everything in the Whole Wide World Benchmark*, [arXiv:2111.15366](https://arxiv.org/abs/2111.15366)
- *Time Travel in LLMs* (contamination), [arXiv:2308.08493](https://arxiv.org/abs/2308.08493)
- *Dynabench*, [arXiv:2104.14337](https://arxiv.org/abs/2104.14337)
- *Pervasive Label Errors in Test Sets*, [arXiv:2103.14749](https://arxiv.org/abs/2103.14749)

## Verification notes

Items below were flagged by the research pass as not confirmed against a primary
source, and should be checked before reuse in anything published:

- The `pass^k` estimator `C(c,k)/C(n,k)` is reconstructed from secondary sources,
  not extracted verbatim from the τ-bench PDF.
- Zhou et al. quotes are from the PMC open-access mirror, not the typeset Nature PDF.
- SWE-bench Verified "3 annotators per sample" is repeated in secondary sources but
  not clean in the primary post; the three Verified quotes are from a faithful
  mirror (canonical page returned 403 to automated fetch).
- The 2026 *Why we no longer evaluate SWE-bench Verified* figures (138 / 64 runs /
  59.4% / 35.5% / 18.8% / ≥6 reviewers) are from secondary coverage, not a direct
  fetch of the OpenAI post.
- METR's 80%-vs-50% horizon multiplier (~5x is sometimes cited) is not verified
  here; only the direction (80% horizon shorter) is.
- Two HELM sentences (standardized-conditions phrasing, 5-shot default) exist in
  substance but were not pinned verbatim; the quoted HELM lines above were.
- Some 2026 reliability preprints surfaced at abstract level only and are
  deliberately not cited.
</content>
