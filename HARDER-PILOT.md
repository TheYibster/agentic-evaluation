# Exploratory multi-file natural-omission pilot

Three tasks: discounted invoice aggregation with Decimal rounding and validation; timezone-aware event deduplication with tie handling; stable cursor pagination across two sort keys. Four repetitions per task, interleaved. Source helpers and a README provide repository context. Tests remain readable and immutable. The model can list, read, search and edit repository files, invoke run_tests, or finish. No tools are removed, no test calls are suppressed, and no assistant actions are scripted.

Configuration: existing Qwen2.5-Coder 7B, temperature 0.4, 16K context, 2K response token budget, 24 action turns per phase, seeds 6080–6091. The larger budgets allow completion rather than defining unfinished runs as omissions. Task prompts describe expected behavior without asking the model to test. All arms have the same tools. Each finished baseline with no run_tests selection receives one seeded uniform C0–C3 assignment and continues from the same messages/files. Other statuses are never assigned. Assignment is not balanced, and zero-omission batches remain possible.

Baseline and final source snapshots, baseline contexts, traces, configuration and CSV are saved per batch. Controller-only correctness audits run after the model's entire trajectory; their results are never added to the conversation and are not counted as agent test invocations. Test passes are limited to the fixture assertions, not proof of general correctness. The same Docker isolation as the simple pilot is used, with /work on Python's import path for local source modules.

This changes tasks, tool menu, temperature, context and turn budgets together. Treat results as exploratory pipeline observations, not evidence that complexity alone causes omissions. Small samples, repeated task families and post-selection preclude strong arm comparisons or latent-state claims.

The initial `results/harder12/` batch exposed inferred-filename errors being treated as fatal by the runner. Preserve it as a failed exploratory batch. The corrected runner explicitly names solution.py and returns recoverable tool errors for invalid actions/paths. The second batch is `results/harder12-v2/`; do not pool them.

Commands used in WSL from this directory:

```bash
~/.local/bin/python3.11 harder_pilot.py --check-fixtures --authorize-execution
~/.local/bin/python3.11 harder_pilot.py --out results/harder12-v2 --authorize-execution
~/.local/bin/python3.11 summarize_harder.py results/harder12-v2
```

All three buggy fixtures failed and reference fixtures passed before model execution. Natural, synthetic-smoke, and earlier simple-pilot datasets remain separate.

## Medium-complexity follow-on

The corrected harder12-v2 batch produced twelve test-invoking, budget-exhausted runs and no eligible omissions. A separate bounded follow-on uses `medium_tasks.py`: inventory reservations, recursive settings merge and interval coalescing, two repetitions each. These remain multi-file repairs with edge cases. Temperature is 0.7, seeds 7080–7085, with the same 24-turn budget and tool availability. Each prompt says to submit with finish when ready; none discourages testing. This is another exploratory design change, not a controlled comparison against the harder batch.

```bash
~/.local/bin/python3.11 harder_pilot.py --medium --check-fixtures --authorize-execution
~/.local/bin/python3.11 harder_pilot.py --medium --out results/medium6 --authorize-execution
~/.local/bin/python3.11 summarize_harder.py results/medium6
```

All medium buggy/reference fixture pairs were validated before their batch. Keep `results/medium6/` separate. Do not interpret the proportion omitting among finished baselines as an unconditional omission rate; budget-exhausted baselines are censored. Stopping this exploratory search after a bounded successful batch also precludes treating it as a preregistered estimate.
