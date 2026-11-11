# Repair check followed by balanced replay

Fixed sequence, using the 20 natural omissions saved in results/medium60-turn64. First run an explicit repair-capability check on all 18 initially incorrect omission checkpoints. Restore their code but use fresh context containing the original task/system and an explicit instruction to invoke tests, inspect failures, repair and retest. This removes the prior decision history and is a capability diagnostic, not an intervention-effect estimate. Do not add stronger models, hints, reference solutions or altered tests.

Then run all 20 checkpoints under each of C0–C3, for 80 follow-ups. Each branch independently restores the original saved conversation and source; only its intervention differs. Keep the same model seed across the four arms within a checkpoint (10000 + source run ID). Shuffle arm order with schedule seed 10080. Repair seeds are 9000 + source run ID. Original model, temperature 0.7, 16K context, 2048 output-token cap, immutable tests and Docker isolation are unchanged. Each trajectory allows 64 model action turns.

Verify saved omission histories, files and initial audit outcomes before making model calls. Capture both schedules before outcomes and finish the fixed sample regardless of results. At most 6272 model calls across 98 trajectories; sequential execution may take substantial time. No new baselines, installations, downloads or paid APIs. Explicit repair context and paired replay are kept separate from each other and previous datasets. The replay schedule is balanced within checkpoints rather than independent uniform assignment as in the original pilot.

Record invocation, valid execution, test passes, final independent audit, source edits, distinct source states, completion/censoring and errors. Compare paired invocation differences against C0; do not treat all 80 branches as independent or infer latent causes from responses. These selected checkpoints cover only three repeated task families. The repair check conditions differ from replay and should not be interpreted as a randomized fifth arm. Context limits may still affect long conversations.

```bash
~/.local/bin/python3.11 repair_replay.py --authorize-execution
~/.local/bin/python3.11 summarize_repair_replay.py results/repair-check18 results/balanced-replay80
```

Both output directories must be new. Source results are read-only inputs. CSV is flushed after every case; no automatic resume or overwrite. The replay output manifest is created before repair collection, but its model calls start only after repair collection completes. A completed.json file confirms completion of each stage.
