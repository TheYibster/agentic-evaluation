# balanced_replay results

Completed 80 planned cases with 64-turn limits.

| Arm | Cases | Invoked tests | Finished | Budget exhausted | Errors | Initially correct | Finally correct | Incorrect to correct |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 | 20 | 2 | 18 | 2 | 0 | 2 | 2 | 0 |
| C1 | 20 | 20 | 4 | 16 | 0 | 2 | 3 | 1 |
| C2 | 20 | 20 | 2 | 18 | 0 | 2 | 2 | 0 |
| C3 | 20 | 20 | 4 | 16 | 0 | 2 | 4 | 2 |

Invocation and final correctness are separate outcomes. Final correctness is a controller audit, never shown to the model. Initial correctness was checked before collection. All source checkpoints came from the selected natural-omission sample, not a new random task sample.

Correctness labels in these tables mean passing the frozen fixture suite, not proof of full specification compliance.

Paired invocation differences against C0:

```json
{
  "C1_vs_C0": {
    "invoked_only_with_guidance": 18,
    "invoked_only_with_C0": 0
  },
  "C2_vs_C0": {
    "invoked_only_with_guidance": 18,
    "invoked_only_with_C0": 0
  },
  "C3_vs_C0": {
    "invoked_only_with_guidance": 18,
    "invoked_only_with_C0": 0
  }
}
```

These are 20 paired checkpoints, not 80 independent task samples. Every arm restores the same saved baseline conversation and files, with the same seed within a checkpoint; arm order is seeded and shuffled. No formal significance or latent-state identification claims.

CSV/trace invocation checks, manifest seeds, checkpoint identifiers, audit outcomes and turn budgets verified. Original data remain unchanged.
