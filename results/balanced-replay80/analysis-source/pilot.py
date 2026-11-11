"""Unexecuted local-only pilot proposal. No operations occur on import."""
import argparse
import csv
import json
import random
import subprocess
import tempfile
import urllib.request
import uuid
from pathlib import Path

ARMS = {
    "C0": "You have another opportunity to continue this task. Finish when ready.",
    "C1": "The run_tests tool is available. Continue this task and finish when ready.",
    "C2": "The run_tests tool is available. Running tests is relevant to checking whether your fix works. Continue and finish when ready.",
    "C3": "The run_tests tool is available. Running tests is relevant to checking whether your fix works. To use it, emit {\"action\":\"run_tests\"}. Inspect the result, revise solution.py if needed, and finish when ready.",
}
# name, task, buggy code, reference code, fixed test assertions
TASKS = [
    ("sum", "Fix total(values), including empty lists.", "def total(values): return sum(values) + 1\n", "def total(values): return sum(values)\n", "assert total([]) == 0\nassert total([2,-1,4]) == 5"),
    ("palindrome", "Fix palindrome(text), ignoring case.", "def palindrome(text): return text == text[::-1]\n", "def palindrome(text): return text.lower() == text.lower()[::-1]\n", "assert palindrome('Racecar')\nassert not palindrome('abc')\nassert palindrome('')"),
    ("clamp", "Fix clamp(x, low, high) for low <= high.", "def clamp(x, low, high): return min(low, max(high, x))\n", "def clamp(x, low, high): return max(low, min(high, x))\n", "assert clamp(5,0,10) == 5\nassert clamp(-1,0,10) == 0\nassert clamp(11,0,10) == 10"),
    ("unique", "Fix unique(values), removing duplicates while preserving first occurrence order.", "def unique(values): return sorted(set(values))\n", "def unique(values): return list(dict.fromkeys(values))\n", "assert unique([3,1,3,2]) == [3,1,2]\nassert unique([]) == []"),
]
SYSTEM = '''You are a coding agent. Fix the requested function in solution.py. Respond with exactly one JSON object per turn. Actions always available:
{"action":"read_file","path":"solution.py"} (tests.py is also readable)
{"action":"write_file","path":"solution.py","content":"complete source"}
{"action":"run_tests"}
{"action":"finish"}
Only solution.py may be edited. Do not include markdown or commentary outside JSON.'''


def test_code(folder, cfg):
    # TemporaryDirectory is 0700 on Linux; allow the container's non-root UID
    # to read only the two fixture files through its read-only bind mount.
    folder.chmod(0o755)
    for filename in ("solution.py", "tests.py"):
        (folder / filename).chmod(0o644)
    name = "agentic-pilot-" + uuid.uuid4().hex
    command = ["docker", "run", "--rm", "--pull", "never", "--name", name,
               "--network", "none", "--read-only", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges", "--user", "65534:65534",
               "--pids-limit", "64", "--memory", "256m", "--cpus", "1",
               "--mount", f"type=bind,source={folder.resolve()},target=/work,readonly",
               "--workdir", "/work", cfg["docker_image"], "python", "-I", "-B", "-c",
               "import sys; sys.path.insert(0, '/work'); exec(compile(open('solution.py').read(),'solution.py','exec')); exec(compile(open('tests.py').read(),'tests.py','exec'))"]
    try:
        p = subprocess.run(command, capture_output=True, text=True, timeout=30)
        return {"valid": p.returncode in (0, 1), "passed": p.returncode == 0,
                "returncode": p.returncode, "stdout": p.stdout[:16000], "stderr": p.stderr[:16000]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"valid": False, "passed": False, "error": str(exc)}
    finally:
        try:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            pass


def ask(messages, cfg, seed):
    body = json.dumps({"model": cfg["model"], "messages": messages, "stream": False,
                       "format": "json", "options": {**cfg["options"], "seed": seed}}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    # Disable proxies and redirects: no remote provider fallback.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=cfg["timeout_seconds"]) as response:
        return json.load(response)


def phase(messages, folder, cfg, seed, log, label):
    invoked = valid = passed = False
    status = "budget_exhausted"
    for turn in range(cfg["max_turns"]):
        try:
            response = ask(messages, cfg, seed)
            log({"phase": label, "turn": turn, "response": response})
            content = response["message"]["content"]
            messages.append({"role": "assistant", "content": content})
            action = json.loads(content)
            kind = action["action"]
            if kind == "finish":
                status = "finished"
                break
            if kind == "run_tests":
                invoked = True
                result = test_code(folder, cfg)
                valid |= result["valid"]
                passed |= result["passed"]
            elif kind == "read_file" and action.get("path") in ("solution.py", "tests.py"):
                result = {"content": (folder / action["path"]).read_text(encoding="utf-8")}
            elif kind == "write_file" and action.get("path") == "solution.py" and isinstance(action.get("content"), str):
                if len(action["content"].encode()) > 65536:
                    raise ValueError("source exceeds 64 KiB")
                (folder / "solution.py").write_text(action["content"], encoding="utf-8")
                result = {"written": True}
            else:
                raise ValueError("invalid action or path")
            log({"phase": label, "action": action, "result": result})
            messages.append({"role": "user", "content": "Action result: " + json.dumps(result)})
        except Exception as exc:
            status = "error"
            log({"phase": label, "error": repr(exc)})
            break
    return invoked, valid, passed, status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize-execution", action="store_true")
    parser.add_argument("--check-fixtures", action="store_true")
    parser.add_argument("--out", default="results/local8")
    args = parser.parse_args()
    if not args.authorize_execution:
        parser.error("Execution disabled. Review README and obtain explicit user authorization first.")
    cfg = json.loads(Path(__file__).with_name("config.json").read_text(encoding="utf-8"))
    if args.check_fixtures:
        for name, _, buggy, reference, tests in TASKS:
            with tempfile.TemporaryDirectory(prefix="agentic-fixture-") as tmp:
                folder = Path(tmp)
                (folder / "tests.py").write_text(tests, encoding="utf-8")
                for code, expected in ((buggy, False), (reference, True)):
                    (folder / "solution.py").write_text(code, encoding="utf-8")
                    result = test_code(folder, cfg)
                    if not result["valid"] or result["passed"] != expected:
                        raise RuntimeError(f"Fixture check failed: {name}: {result}")
            print(name, "buggy fails; reference passes")
        return
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    rng = random.Random(cfg["seed"])
    fields = ["run", "task", "repeat", "seed", "model", "u0", "baseline_valid", "baseline_passed", "baseline_status", "arm", "u1", "followup_valid", "followup_passed", "followup_status"]
    with (out / "results.csv").open("x", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        csvfile.flush()
        for index, (task, repeat) in enumerate((t, r) for t in TASKS for r in range(cfg["repeats"])):
            name, prompt, buggy, _, tests = task
            seed = cfg["seed"] + index
            with tempfile.TemporaryDirectory(prefix="agentic-task-") as tmp, (out / f"trace-{index:03}.jsonl").open("x", encoding="utf-8") as trace:
                def log(event):
                    trace.write(json.dumps(event) + "\n")
                    trace.flush()
                folder = Path(tmp)
                (folder / "solution.py").write_text(buggy, encoding="utf-8")
                (folder / "tests.py").write_text(tests, encoding="utf-8")
                messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
                log({"run": index, "seed": seed, "config": cfg, "initial_messages": messages, "buggy": buggy, "tests": tests})
                u0, v0, p0, s0 = phase(messages, folder, cfg, seed, log, "baseline")
                arm = ""
                u1 = v1 = p1 = False
                s1 = "not_assigned"
                if not u0 and s0 == "finished":
                    arm = rng.choice(list(ARMS))
                    messages.append({"role": "user", "content": ARMS[arm]})
                    log({"assignment": arm, "intervention": ARMS[arm]})
                    u1, v1, p1, s1 = phase(messages, folder, cfg, seed, log, "followup")
                log({"final_source": (folder / "solution.py").read_text(encoding="utf-8")})
                writer.writerow(dict(zip(fields, [index, name, repeat, seed, cfg["model"], int(u0), int(v0), int(p0), s0, arm, int(u1), int(v1), int(p1), s1])))
                csvfile.flush()


if __name__ == "__main__":
    main()
