# repair_check results

Completed 18 planned cases with 64-turn limits.

| Arm | Cases | Invoked tests | Finished | Budget exhausted | Errors | Initially correct | Finally correct | Incorrect to correct |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| explicit_repair | 18 | 17 | 3 | 15 | 0 | 0 | 1 | 1 |

Invocation and final correctness are separate outcomes. Final correctness is a controller audit, never shown to the model. Initial correctness was checked before collection. All source checkpoints came from the selected natural-omission sample, not a new random task sample.

Correctness labels in these tables mean passing the frozen fixture suite, not proof of full specification compliance.

Manual review identified an audit coverage gap; see [AUDIT-REVIEW.md](AUDIT-REVIEW.md) before interpreting the fixture-passing count.

Fresh context contains the original task and explicit instructions to test and repair. The files are the saved incorrect baseline repairs. This checks repair capability under explicit guidance and is not a randomized comparison with the original omission interventions.

CSV/trace invocation checks, manifest seeds, checkpoint identifiers, audit outcomes and turn budgets verified. Original data remain unchanged.
