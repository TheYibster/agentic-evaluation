# Installation status — November 9, 2026

Installed inside Ubuntu 26.04.1 on WSL2, using the user's installation authorization:

- Existing Python 3.11.16: `/home/yiboliang02/.local/bin/python3.11` (not reinstalled).
- Ubuntu-packaged Docker Engine 29.1.3 (`docker.io`), containerd and dependencies.
- Ollama 0.40.15 via its reviewed official Linux installer.
- `qwen2.5-coder:7b`, Q4_K_M, 4,683,087,561 bytes. Digest: `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- `python:3.11-slim` image digest: `sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535`.

Docker and Ollama services are active and enabled by their installers. Ollama listens on 127.0.0.1:11434. Startup logs detect RTX 5080 via CUDA. Inference has not been tested. No Linux NVIDIA driver was installed.

Measured storage: Ollama libraries 2.4 GiB, model files 4.4 GiB, containerd storage 181 MiB, plus Docker packages and dependencies (apt estimated 288 MB). Roughly 7–8 GB added, excluding filesystem and cache overhead.

No model inference, fixture tests, or pilot runs were performed during installation. After the user approved Docker access, continued the previously authorized run: all four fixture checks passed, then all eight baselines completed with successful test invocations. No baseline omissions occurred, so no C0–C3 follow-ups were assigned. CSV and traces are in `results/local8/`. Fixed Linux temporary-directory permissions so the non-root test container can read the fixture files. The proposal was executed via WSL from its Windows-mounted directory; it has not been copied into the Linux filesystem.

User subsequently explicitly approved Docker group membership. Added `yiboliang02` to `docker` and verified regular-user access to Docker Engine 29.1.3 from a fresh WSL session. Existing terminal sessions may need reopening.

The model pull reported success and the local model inventory independently confirmed its digest. The command wrapper returned a nonzero exit afterward due to an empty shell exit-status variable; this was a wrapper error, not a failed model download.

The original README describes preparation-time status and PowerShell commands. Those statements are historical; use this record for current installation status. Do not execute that Windows checklist for the WSL installation.
