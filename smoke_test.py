"""Synthetic omission plumbing check, isolated from natural experiment data."""
import argparse
import copy
import csv
import hashlib
import json
import random
import tempfile
from pathlib import Path

from pilot import ARMS, SYSTEM, TASKS, phase


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorize-execution", action="store_true")
    parser.add_argument("--out", default="results/synthetic-smoke")
    args = parser.parse_args()
    if not args.authorize_execution:
        parser.error("Explicit execution authorization required")
    cfg = json.loads(Path(__file__).with_name("config.json").read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "config.json").write_text(json.dumps(cfg, indent=2))
    name, prompt, buggy, reference, tests = TASKS[0]
    # Construct a plausible completed repair with no test invocation. These
    # assistant messages are scripted, not sampled from the model.
    read = {"action": "read_file", "path": "solution.py"}
    write = {"action": "write_file", "path": "solution.py", "content": reference}
    scripted = [(read, {"content": buggy}), (write, {"written": True})]
    baseline = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    for action, result in scripted:
        baseline.extend([{"role": "assistant", "content": json.dumps(action)},
                         {"role": "user", "content": "Action result: " + json.dumps(result)}])
    baseline.append({"role": "assistant", "content": json.dumps({"action": "finish"})})
    checkpoint = {"synthetic": True, "task": name, "messages": baseline,
                  "source": reference, "tests": tests, "u0": 0,
                  "baseline_status": "finished", "scripted_actions": scripted}
    checkpoint_hash = digest(checkpoint)
    (out / "checkpoint.json").write_text(json.dumps(checkpoint, indent=2))
    arms = list(ARMS)
    random.Random(cfg["seed"]).shuffle(arms)
    fields = ["synthetic", "run", "task", "seed", "model", "u0", "baseline_status",
              "arm", "u1", "followup_valid", "followup_passed", "followup_status", "checkpoint_sha256"]
    rows = []
    checks = []
    with (out / "results.csv").open("x", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        output.flush()
        for index, arm in enumerate(arms):
            # Same checkpoint and model seed for every arm; only intervention
            # differs. Shuffling guarantees coverage, not independent assignment.
            seed = cfg["seed"]
            messages = copy.deepcopy(baseline)
            messages.append({"role": "user", "content": ARMS[arm]})
            with tempfile.TemporaryDirectory(prefix="agentic-smoke-") as tmp, (out / f"trace-{arm}.jsonl").open("x") as trace:
                def log(event):
                    trace.write(json.dumps({"synthetic": True, **event}) + "\n")
                    trace.flush()
                folder = Path(tmp)
                (folder / "solution.py").write_text(reference, encoding="utf-8")
                (folder / "tests.py").write_text(tests, encoding="utf-8")
                log({"checkpoint_sha256": checkpoint_hash, "assignment": arm,
                     "assignment_method": "seeded shuffled exhaustive arm coverage",
                     "seed": seed, "config": cfg, "initial_messages": messages})
                u1, valid, passed, status = phase(messages, folder, cfg, seed, log, "followup")
                log({"final_source": (folder / "solution.py").read_text()})
                if messages[:len(baseline)] != baseline:
                    raise RuntimeError("Baseline context was modified")
            events = [json.loads(line) for line in (out / f"trace-{arm}.jsonl").read_text().splitlines()]
            observed = any(e.get("action", {}).get("action") == "run_tests" for e in events)
            if observed != u1:
                raise RuntimeError("CSV/trace invocation mismatch")
            row = dict(zip(fields, [1, index, name, seed, cfg["model"], 0, "finished", arm,
                                    int(u1), int(valid), int(passed), status, checkpoint_hash]))
            writer.writerow(row)
            output.flush()
            rows.append(row)
            checks.append({"arm": arm, "context_preserved": True, "csv_matches_trace": True,
                           "followup_status": status})
            print(f"{arm}: invoked={u1}, valid={valid}, passed={passed}, status={status}", flush=True)
    saved = list(csv.DictReader((out / "results.csv").open()))
    complete = len(saved) == 4 and {r["arm"] for r in saved} == set(ARMS)
    success = complete and all(r["followup_status"] == "finished" for r in rows)
    summary = {"synthetic": True, "plumbing_passed": success, "all_arms_covered": complete,
               "checks": checks, "limitation": "Scripted baseline; no natural omission or treatment-effect evidence."}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
