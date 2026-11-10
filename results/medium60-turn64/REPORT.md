# 60-baseline exploratory pilot: 64 turns per phase

Completed 60 fresh baselines. Limits: 64 action turns per baseline and per assigned follow-up. Model: qwen2.5-coder:7b; temperature 0.7; context 16384. Seeds 8080–8139.

## Baselines

- Finished: 37; natural omissions among finished baselines: 20.
- Status counts: {'budget_exhausted': 23, 'finished': 37}.
- Invoked tests, including incomplete runs: 40/60.
- Passing baseline correctness audits across all runs: 17/60.

| Task | Runs | Finished | Natural omissions | Budget exhausted | Baseline audit passes |
|---|---:|---:|---:|---:|---:|
| intervals | 20 | 19 | 4 | 1 | 16 |
| inventory | 20 | 6 | 5 | 14 | 0 |
| settings | 20 | 12 | 11 | 8 | 1 |

## Randomized omission follow-ups

| Arm | Assigned | Invoked tests | Finished | Budget exhausted | Errors | Final audit passes | Incorrect to correct |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 | 5 | 2 | 4 | 1 | 0 | 0 | 0 |
| C1 | 2 | 2 | 0 | 2 | 0 | 0 | 0 |
| C2 | 4 | 4 | 1 | 3 | 0 | 1 | 0 |
| C3 | 9 | 9 | 1 | 8 | 0 | 1 | 0 |

Invocation means the tool was selected at least once within the 64-turn window, even if the trajectory later exhausted its budget. Final correctness is measured by a controller audit, separately from invocation and any intermediate passing test result.

## Verification and interpretation

All planned rows are present. CSV invocations match traces; baseline contexts match reconstructed histories; assignments match the seeded uniform RNG and the correct C0–C3 messages; audits match CSV values; no phase exceeds the configured turn limit. The shared runner continues directly from its baseline message list and source folder.

Baseline model calls: 1719; follow-up model calls: 908. Reported prompt-evaluation tokens summed over calls: 11025062; generated tokens: 114198. These are local runtime counters, not API charges.

This is exploratory evidence from twenty repetitions of each of three task families, not sixty distinct tasks. Budget-exhausted/error baselines are censored rather than counted as omissions. Arm counts can be small and unequal; do not infer latent H1–H4 labels from responses. Context remains 16K despite the larger action budget, so long conversations may be truncated by the runtime. The prior smaller pilots use different seeds/budgets and were not pooled. No claim that raising the budget caused an improvement is justified by this batch alone.

Files: results.csv, summary.json, config.json, started.json, completed.json, run-*/trace.jsonl and saved baseline/final sources. protocol/ contains the source snapshot captured before execution.
