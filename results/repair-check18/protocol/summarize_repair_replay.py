"""Verify and summarize checkpoint repair/replay experiments."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from repair_replay import ARMS, REPAIR, sha


def main():
    for location in sys.argv[1:]:
        folder=Path(location)
        plan=json.loads((folder/'manifest.json').read_text())
        rows=list(csv.DictReader((folder/'results.csv').open()))
        if not (folder/'completed.json').exists() or len(rows)!=plan['planned_cases']:
            raise RuntimeError('Experiment incomplete')
        cases={(str(c['run']),c['arm']):c for c in plan['cases']}
        for row in rows:
            case=cases[(row['source_run'],row['arm'])]
            if row['checkpoint_sha256']!=case['checkpoint_sha256'] or int(row['seed'])!=case['seed']:
                raise RuntimeError('Checkpoint/seed mismatch')
            run=folder/f"run-{int(row['source_run']):03}-{row['arm']}"
            original=Path(plan['source'])/f"run-{int(row['source_run']):03}"
            original_files=json.loads((original/'baseline-files.json').read_text())
            original_context=json.loads((original/'baseline-context.json').read_text())
            if sha({'files':original_files,'context':original_context})!=row['checkpoint_sha256']:
                raise RuntimeError('Source checkpoint changed')
            if json.loads((run/'initial-files.json').read_text())!=original_files:
                raise RuntimeError('Restored files differ from checkpoint')
            expected=(original_context+[{'role':'user','content':ARMS[row['arm']]}]
                      if plan['kind']=='balanced_replay' else original_context[:2]+[{'role':'user','content':REPAIR}])
            initial_context=json.loads((run/'initial-context.json').read_text())
            final_context=json.loads((run/'final-context.json').read_text())
            if initial_context!=expected or final_context[:len(expected)]!=expected:
                raise RuntimeError('Context continuity mismatch')
            events=[json.loads(line) for line in (run/'trace.jsonl').read_text().splitlines()]
            invoked=any(e.get('action',{}).get('action')=='run_tests' for e in events)
            if invoked!=bool(int(row['invoked_tests'])): raise RuntimeError('Invocation mismatch')
            if int(row['model_calls'])>64: raise RuntimeError('Turn limit exceeded')
            audit=events[-1]['controller_final_audit']
            if bool(int(row['final_audit_passed']))!=audit['passed']: raise RuntimeError('Audit mismatch')
        groups={}
        for arm in sorted({r['arm'] for r in rows}):
            group=[r for r in rows if r['arm']==arm]
            groups[arm]={'cases':len(group),'invoked_tests':sum(int(r['invoked_tests']) for r in group),
                'statuses':dict(Counter(r['status'] for r in group)),
                'initially_correct':sum(int(r['initial_audit_passed']) for r in group),
                'finally_correct':sum(int(r['final_audit_passed']) for r in group),
                'incorrect_to_correct':sum(int(r['incorrect_to_correct']) for r in group),
                'mean_distinct_source_states':sum(int(r['distinct_source_states']) for r in group)/len(group)}
        pairs={}
        if plan['kind']=='balanced_replay':
            by_checkpoint={r['source_run']:{} for r in rows}
            for row in rows: by_checkpoint[row['source_run']][row['arm']]=row
            if len(by_checkpoint)!=20 or any(set(g)!=set(('C0','C1','C2','C3')) for g in by_checkpoint.values()):
                raise RuntimeError('Unbalanced checkpoint coverage')
            for arm in ('C1','C2','C3'):
                pairs[arm+'_vs_C0']={
                    'invoked_only_with_guidance':sum(g[arm]['invoked_tests']=='1' and g['C0']['invoked_tests']=='0' for g in by_checkpoint.values()),
                    'invoked_only_with_C0':sum(g[arm]['invoked_tests']=='0' and g['C0']['invoked_tests']=='1' for g in by_checkpoint.values())}
        summary={'kind':plan['kind'],'cases':len(rows),'groups':groups,'paired_counts':pairs,'checks':'passed'}
        (folder/'summary.json').write_text(json.dumps(summary,indent=2))
        lines=[f"# {plan['kind']} results",'',f"Completed {len(rows)} planned cases with 64-turn limits.",'',
            '| Arm | Cases | Invoked tests | Finished | Budget exhausted | Errors | Initially correct | Finally correct | Incorrect to correct |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for arm,g in groups.items():
            lines.append(f"| {arm} | {g['cases']} | {g['invoked_tests']} | {g['statuses'].get('finished',0)} | {g['statuses'].get('budget_exhausted',0)} | {g['statuses'].get('error',0)} | {g['initially_correct']} | {g['finally_correct']} | {g['incorrect_to_correct']} |")
        lines+=['','Invocation and final correctness are separate outcomes. Final correctness is a controller audit, never shown to the model. Initial correctness was checked before collection. All source checkpoints came from the selected natural-omission sample, not a new random task sample.','']
        if pairs: lines+=['Paired invocation differences against C0:', '', '```json', json.dumps(pairs,indent=2),'```','',
            'These are 20 paired checkpoints, not 80 independent task samples. Every arm restores the same saved baseline conversation and files, with the same seed within a checkpoint; arm order is seeded and shuffled. No formal significance or latent-state identification claims.']
        else: lines+=['Fresh context contains the original task and explicit instructions to test and repair. The files are the saved incorrect baseline repairs. This checks repair capability under explicit guidance and is not a randomized comparison with the original omission interventions.']
        lines+=['','CSV/trace invocation checks, manifest seeds, checkpoint identifiers, audit outcomes and turn budgets verified. Original data remain unchanged.']
        (folder/'REPORT.md').write_text('\n'.join(lines)+'\n')
        print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
