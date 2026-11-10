"""Offline analysis; never invokes models or Docker."""
import csv
import math
import sys


def interval(k, n):
    if not n:
        return "NA"
    z = 1.96
    p = k / n
    d = 1 + z*z/n
    mid = (p + z*z/(2*n))/d
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return f"{p:.3f} [{mid-half:.3f}, {mid+half:.3f}]"


if __name__ == "__main__":
    with open(sys.argv[1], newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    eligible = [r for r in rows if r["baseline_status"] == "finished"]
    print(f"Rows: {len(rows)}; completed baselines: {len(eligible)}")
    print("Baseline invocation:", interval(sum(int(r["u0"]) for r in eligible), len(eligible)))
    for arm in ("C0", "C1", "C2", "C3"):
        group = [r for r in rows if r["arm"] == arm]
        print(arm, "assigned", len(group), "post invocation", interval(sum(int(r["u1"]) for r in group), len(group)),
              "post errors/censored", sum(r["followup_status"] != "finished" for r in group))
    print("Wilson 95% intervals; tiny pilot, descriptive only. No latent-state identification.")
