# Natural omission observations

Six model-generated baseline runs; no scripted history, suppressed test calls, or forced omissions. Four baselines finished, two exhausted the 24-turn budget. Of the four finished baselines, two invoked tests and passed the fixture checks, and two finished without invoking tests. This is a tiny exploratory sample of three repeated task families, not an omission-rate estimate for coding agents generally.

The natural omissions were runs 1 and 4, both recursive settings merge repairs (seeds 7081 and 7084). Their saved baseline contexts end in the model's own finish action. CSV invocation flags were independently cross-checked against the JSONL action traces. The testing tool was available throughout.

Each eligible omission received one independent seeded uniform C0–C3 assignment. Both happened to receive C2 (awareness plus relevance). Neither was reassigned to obtain arm balance. In both cases the continuation invoked run_tests, exposing failures in the submitted implementation; both follow-ups subsequently exhausted the turn budget without passing the fixture checks. Baseline and final controller audits also failed. Controller audits ran after the conversation and were not shown to the model or counted as agent invocation.

This demonstrates two actual omission → randomized intervention → test invocation trajectories. It does not establish C2 effectiveness, compare C0–C3, identify latent failure causes, or demonstrate successful repairs. No observations were collected in C0, C1 or C3 in this batch.

The preceding twelve harder runs in ../harder12-v2 all invoked tests and exhausted their budgets, and are not pooled here. The earlier failed filename-handling batch in ../harder12 is also separate. The synthetic smoke test remains separate.

Evidence: results.csv, summary.json, config.json, and run-001/ and run-004/ (baseline-context.json, baseline-files.json, final-files.json, trace.jsonl).
