# Fixed exploratory pilot: 60 baselines, 64 turns per phase

Twenty repetitions each of inventory reservation, recursive settings merge and interval coalescing, interleaved in that order. Fresh source and conversation for every baseline. New seeds 8080–8139. Same Qwen2.5-Coder 7B, temperature 0.7, 16K context, 2048 output-token cap and six-action tool menu as medium6. Both baseline and follow-up action-turn limits are 64 (previously 24). This is an independent batch, not a continuation or pooling of earlier trajectories.

Completed baselines with no run_tests invocation receive one independent uniform C0–C3 assignment from a seeded RNG. No balancing or outcome-dependent reassignment. Follow-ups continue the same context and files. Budget-exhausted or error baselines do not receive interventions. Audit runs are separate from agent test invocation and not shown to the agent. Context length is unchanged, so long trajectories may exceed model context; the larger action budget does not guarantee better repairs or completion.

Fixed stopping rule: complete all 60 baselines and all eligible follow-ups, regardless of interim omissions or arm responses. At most 7,680 model calls (60 × 64 × 2), usually fewer. No concurrency, external provider, new model, or downloads. Results, source snapshots, CSV, traces, and protocol copies are isolated in results/medium60-turn64/. The run may take substantial time, especially for repetitive failing trajectories.

Review incomplete/error runs separately. This explores three repeated task families, not 60 distinct tasks. Report assigned-arm denominators, test selection, test execution, final correctness and censoring separately. Small/unequal omission-arm samples cannot identify H1–H4 proportions. Changes in sample size and turn budget together do not isolate a budget effect against medium6.

Authorized WSL command, from the proposal directory:

```bash
~/.local/bin/python3.11 harder_pilot.py --medium --repeats 20 --max-turns 64 --seed 8080 --out results/medium60-turn64 --authorize-execution
~/.local/bin/python3.11 summarize_harder.py results/medium60-turn64
```

No existing results or default config are overwritten. started.json specifies the sample before collection; completed.json is written only after the full batch. CSV is flushed after every trajectory. There is no automatic resume; interruption retains partial data and requires a separately documented continuation rather than silently rerunning or mixing files.

Completed: all 60 baselines and 20 randomized omission follow-ups. Thirty-seven baselines finished, including twenty omissions; twenty-three exhausted their budgets. Seventeen omission follow-ups invoked tests. No initially incorrect omitted repair became correct. See results/medium60-turn64/REPORT.md for arm and task counts. No test containers remained running after completion.

The multi-file runner now defaults to 64 turns for future runs; this completed batch explicitly passed --max-turns 64, as recorded in its config and archived source. The original simple pilot and synthetic smoke-test configuration remain separate.
