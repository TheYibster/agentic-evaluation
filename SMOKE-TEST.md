# Synthetic omission smoke test

This is a separate plumbing check, not natural experimental evidence. `smoke_test.py` constructs a scripted assistant history that reads and fixes the sum function, then finishes without invoking run_tests. The target tool remains available throughout; no model-generated baseline action is suppressed or relabeled.

Four independent copies of that checkpoint receive C0, C1, C2, and C3 once each, in seeded shuffled order. All use the same model seed, messages and source before the intervention. This deliberately guarantees arm coverage; it is not the production pilot's independent uniform assignment among naturally occurring omissions. The actual model generates each continuation with the existing agent loop and isolated Docker tests.

Artifacts are exclusively under `results/synthetic-smoke/`: scripted checkpoint, configuration, per-arm JSONL traces, CSV marked synthetic, and a machine-readable summary. The natural pilot and `results/local8/` are unchanged. Never pool these rows with natural data or use them to estimate omission rates, treatment effects, or latent states.

Checks cover all four intervention messages, preserved baseline context, completed model continuations, CSV/trace agreement for invocation, and arm coverage. Invocation is a measured outcome, not a pass requirement: C0 may legitimately finish without testing. This checks continuation plumbing, not the production omission-eligibility/randomization branch, which still needs naturally occurring omissions. No harder tasks are launched by this script.

Authorized WSL execution from this directory:

```bash
~/.local/bin/python3.11 smoke_test.py --authorize-execution
```

Output directory must not already exist. At most 32 model calls (four arms, eight turns per arm). No installs or downloads.
