# RTX 5080 local pilot — unexecuted proposal

Prepared as an additive fallback. The existing project, its instructions, and the prior sandbox ZIP could not be inspected without commands/scripts. This is not evidence of a local installation. No installation, validation, model call, download, Docker operation, or experiment was performed. Review applicable workspace instructions before adopting these files.

Python 3.11 standard library only. Uses Ollama's local `/api/chat` endpoint and an explicit JSON action protocol, not native model tool-calling support. Qwen2.5-Coder 7B is a proposed model inherited from the prior discussion; availability, protocol reliability, GPU compatibility and memory use are unverified. No OpenAI SDK, API key, tracing, remote endpoint, or automatic download is used.

## Design

Four deliberately buggy functions, two repetitions each. Every baseline has fresh files/context and the same four available actions: read_file, write_file, run_tests, finish. Baseline context contains the task and action definitions, with no diagnostic intervention. U0 records selection of run_tests even if execution fails. Only completed baseline omissions enter seeded uniform random assignment to C0–C3. Follow-up continues the same messages and files. U1 records subsequent selection separately from valid Docker execution and test success. Budget exhaustion and protocol/model errors are explicit statuses and excluded from the omission randomization; this avoids treating infrastructure errors as behavioral omissions.

C0: neutral second chance. C1: tool awareness. C2: awareness and relevance. C3: awareness, relevance and procedure. Each omitted baseline receives one arm, never all four. Uniform randomization does not guarantee balance with eight runs. Traces contain prompts, responses, calls, outputs, errors, model settings and seeds. Results are saved incrementally; interrupted runs may have a trace without a final CSV row. Output directories must be new. There is no resume mechanism.

Tests execute agent-written code only inside disposable Docker containers: no network, no credentials, read-only mount/root filesystem, dropped capabilities, non-root user, PID/memory/CPU/time limits. Only solution.py can be edited; tests are fixed. This isolation is unverified and requires review. Docker uses `--pull never`. No host execution of model-generated code. A timed-out Docker client could leave a container behind; the named-container cleanup is attempted in finally, but cleanup cannot be guaranteed on process termination. Inspect Docker manually after interruptions.

## Exact planned PowerShell checklist — DO NOT EXECUTE YET

Every command below requires your explicit authorization of execution first. Run from this proposal directory. Stop on any failed step. No installers or system changes are included; if prerequisites are missing, stop and review installation separately. Starting Docker Desktop or Ollama is also a separately authorized manual action.

- [ ] Review all source files and applicable parent AGENTS.md instructions using your editor.
- [ ] Authorize inventory only, then run individually:
  ```powershell
  py -3.11 --version
  nvidia-smi
  ollama --version
  ollama list
  docker version
  docker image inspect python:3.11-slim
  ```
- [ ] If separately approved and the model/image are missing, download individually (network and disk use):
  ```powershell
  ollama pull qwen2.5-coder:7b
  docker pull python:3.11-slim
  ```
- [ ] Review config.json. Record actual model digest and image ID from the inventory in study notes; tags can change. No GPU assumptions have been verified.
- [ ] Authorize fixture validation (Docker operations, no model calls):
  ```powershell
  py -3.11 pilot.py --check-fixtures --authorize-execution
  ```
- [ ] Authorize experiment separately (up to 128 model requests: eight baselines and at most eight follow-ups, each eight turns; actual number may be smaller):
  ```powershell
  py -3.11 pilot.py --out results/local8 --authorize-execution
  ```
- [ ] Authorize local CSV analysis:
  ```powershell
  py -3.11 analyze.py results/local8/results.csv
  ```

The flags are an accidental-execution guard, not authorization by themselves. No requirements installation or virtual environment is needed by this standalone proposal. Do not replace existing project files until a source comparison is authorized. Fixture checks should show buggy versions failing and reference versions passing. The analysis reports observable response rates and Wilson intervals, not H1–H4 latent class proportions. Eight baselines validate the pipeline, not inferential identification. Selection, valid execution and success are different outcomes; preserve all three.
