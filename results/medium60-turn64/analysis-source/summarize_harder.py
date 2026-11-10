"""Describe a harder-pilot batch without pooling it with other experiments."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path


def main():
    folder=Path(sys.argv[1])
    rows=list(csv.DictReader((folder/'results.csv').open()))
    complete=[r for r in rows if r['baseline_status']=='finished']
    omissions=[r for r in complete if r['u0']=='0']
    arms={}
    for arm in ('C0','C1','C2','C3'):
        assigned=[r for r in omissions if r['arm']==arm]
        arms[arm]={'assigned':len(assigned),'invoked':sum(int(r['u1']) for r in assigned),
                   'finished':sum(r['followup_status']=='finished' for r in assigned),
                   'statuses':dict(Counter(r['followup_status'] for r in assigned)),
                   'valid_test_execution':sum(int(r['followup_valid']) for r in assigned),
                   'ever_passed_agent_tests':sum(int(r['followup_passed']) for r in assigned),
                   'incorrect_to_correct':sum(r['baseline_audit_passed']=='0' and r['final_audit_passed']=='1' for r in assigned),
                   'final_audit_passes':sum(int(r['final_audit_passed']) for r in assigned)}
    # Cross-check eligibility, assignment, and reported invocations against traces.
    for r in rows:
        events=[json.loads(line) for line in (folder/f"run-{int(r['run']):03}"/'trace.jsonl').read_text().splitlines()]
        for label,field in [('baseline','u0'),('followup','u1')]:
            selected=any(e.get('phase')==label and e.get('action',{}).get('action')=='run_tests' for e in events)
            if selected != bool(int(r[field])): raise RuntimeError('trace/CSV disagreement')
        eligible=r['baseline_status']=='finished' and r['u0']=='0'
        if bool(r['arm']) != eligible: raise RuntimeError('assignment eligibility mismatch')
    summary={'runs':len(rows),'baseline_statuses':dict(Counter(r['baseline_status'] for r in rows)),
             'baseline_test_invocations_all_runs':sum(int(r['u0']) for r in rows),
             'finished_baselines':len(complete),'natural_omissions':len(omissions),
             'omission_runs':[int(r['run']) for r in omissions],
             'baseline_audit_passes_all_runs':sum(int(r['baseline_audit_passed']) for r in rows),
             'omissions_with_passing_baseline_audit':sum(int(r['baseline_audit_passed']) for r in omissions),
             'arms':arms,'trace_csv_checks':'passed',
             'interpretation':'Exploratory batch. No forced omissions; errors and budget exhaustion excluded. No latent-class identification or causal comparison with the earlier simple pilot.'}
    (folder/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
