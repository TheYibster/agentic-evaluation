# Agentic Evaluation

Local coding-agent experiments using Python, Ollama, and Docker in Ubuntu WSL2.

The agent can inspect/edit fixture repositories, run tests, and finish. A completed baseline without a `run_tests` request receives one randomized C0–C3 follow-up. Tool invocation and code correctness are measured separately. Controller audits are not shown to the agent.

Prerequisites: Python 3.11+, running Ollama with `qwen2.5-coder:7b`, and Docker with `python:3.11-slim` already pulled. Docker access is required. Model and image downloads are not automatic.

From Ubuntu WSL, in this directory:

```bash
python3.11 harder_pilot.py --medium --check-fixtures --authorize-execution
python3.11 harder_pilot.py --medium --repeats 20 --max-turns 64 --seed 8080 --out results/new-batch --authorize-execution
python3.11 summarize_harder.py results/new-batch
python3.11 report_large.py results/new-batch
```

Use an output directory that does not exist. The multi-file runner defaults to 64 turns per baseline and follow-up; the original single-file pilot uses its separate config.json. Fixed tests execute in restricted, network-disabled Docker containers. No paid APIs or cloud model fallback.

Latest completed batch: [60 baselines with 64-turn limits](results/medium60-turn64/REPORT.md). There were 20 natural omissions among 37 finished baselines; 23 baselines exhausted the budget. Seventeen omission follow-ups invoked tests, but no initially incorrect omission case became correct. These are exploratory observations from three repeated task families, not latent H1–H4 estimates.
