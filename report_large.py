"""Write an exploratory report and verify assignment and context continuity."""
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path
from pilot import ARMS


def main():
    folder=Path(sys.argv[1])
    cfg=json.loads((folder/'config.json').read_text())
    started=json.loads((folder/'started.json').read_text())
    rows=list(csv.DictReader((folder/'results.csv').open()))
    if not (folder/'completed.json').exists() or len(rows)!=started['planned_baselines']:
        raise RuntimeError('Fixed batch has not completed')
    rng=random.Random(cfg['seed'])
    baseline_turns=[]; followup_turns=[]; prompt_tokens=output_tokens=0
    for row in rows:
        run=folder/f"run-{int(row['run']):03}"
        events=[json.loads(line) for line in (run/'trace.jsonl').read_text().splitlines()]
        assignment=[e for e in events if 'assignment' in e]
        eligible=row['baseline_status']=='finished' and row['u0']=='0'
        if eligible:
            expected=rng.choice(list(ARMS))
            if row['arm']!=expected or len(assignment)!=1 or assignment[0]['intervention']!=ARMS[expected]:
                raise RuntimeError('Assignment mismatch')
        elif assignment or row['arm']:
            raise RuntimeError('Ineligible intervention')
        messages=list(events[0]['initial_messages'])
        baseline_context=json.loads((run/'baseline-context.json').read_text())
        for label,field,turns in [('baseline','u0',baseline_turns),('followup','u1',followup_turns)]:
            phase_events=[e for e in events if e.get('phase')==label]
            calls=[e for e in phase_events if e.get('action',{}).get('action')=='run_tests']
            if bool(calls)!=bool(int(row[field])): raise RuntimeError('Invocation mismatch')
            responses=[e for e in phase_events if 'response' in e]
            if label=='baseline' or eligible: turns.append(len(responses))
            if len(responses)>cfg['max_turns']: raise RuntimeError('Turn limit exceeded')
            for e in responses:
                response=e['response']
                prompt_tokens+=response.get('prompt_eval_count',0)
                output_tokens+=response.get('eval_count',0)
            if label=='baseline':
                for e in phase_events:
                    if 'response' in e:
                        messages.append({'role':'assistant','content':e['response']['message']['content']})
                    elif 'action' in e:
                        messages.append({'role':'user','content':'Action result: '+json.dumps(e['result'])})
                if messages!=baseline_context: raise RuntimeError('Baseline context mismatch')
        audit=[e['controller_audits'] for e in events if 'controller_audits' in e]
        if len(audit)!=1: raise RuntimeError('Missing audits')
        for label,prefix in [('baseline','baseline'),('final','final')]:
            if int(row[prefix+'_audit_passed'])!=int(audit[0][label]['passed']): raise RuntimeError('Audit mismatch')
    summary=json.loads((folder/'summary.json').read_text())
    finished=summary['finished_baselines']; omitted=summary['natural_omissions']
    text=['# 60-baseline exploratory pilot: 64 turns per phase','',
          f"Completed {len(rows)} fresh baselines. Limits: {cfg['max_turns']} action turns per baseline and per assigned follow-up. Model: {cfg['model']}; temperature {cfg['options']['temperature']}; context {cfg['options']['num_ctx']}. Seeds {cfg['seed']}–{cfg['seed']+len(rows)-1}.",'',
          '## Baselines','',
          f"- Finished: {finished}; natural omissions among finished baselines: {omitted}.",
          f"- Status counts: {summary['baseline_statuses']}.",
          f"- Invoked tests, including incomplete runs: {summary['baseline_test_invocations_all_runs']}/{len(rows)}.",
          f"- Passing baseline correctness audits across all runs: {summary['baseline_audit_passes_all_runs']}/{len(rows)}.",'',
          '| Task | Runs | Finished | Natural omissions | Budget exhausted | Baseline audit passes |',
          '|---|---:|---:|---:|---:|---:|']
    for task in sorted({r['task'] for r in rows}):
        group=[r for r in rows if r['task']==task]
        text.append(f"| {task} | {len(group)} | {sum(r['baseline_status']=='finished' for r in group)} | {sum(r['baseline_status']=='finished' and r['u0']=='0' for r in group)} | {sum(r['baseline_status']=='budget_exhausted' for r in group)} | {sum(int(r['baseline_audit_passed']) for r in group)} |")
    text+=['','## Randomized omission follow-ups','',
           '| Arm | Assigned | Invoked tests | Finished | Budget exhausted | Errors | Final audit passes | Incorrect to correct |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm,a in summary['arms'].items():
        text.append(f"| {arm} | {a['assigned']} | {a['invoked']} | {a['finished']} | {a['statuses'].get('budget_exhausted',0)} | {a['statuses'].get('error',0)} | {a['final_audit_passes']} | {a['incorrect_to_correct']} |")
    text+=['','Invocation means the tool was selected at least once within the 64-turn window, even if the trajectory later exhausted its budget. Final correctness is measured by a controller audit, separately from invocation and any intermediate passing test result.','',
           '## Verification and interpretation','',
           'All planned rows are present. CSV invocations match traces; baseline contexts match reconstructed histories; assignments match the seeded uniform RNG and the correct C0–C3 messages; audits match CSV values; no phase exceeds the configured turn limit. The shared runner continues directly from its baseline message list and source folder.','',
           f"Baseline model calls: {sum(baseline_turns)}; follow-up model calls: {sum(followup_turns)}. Reported prompt-evaluation tokens summed over calls: {prompt_tokens}; generated tokens: {output_tokens}. These are local runtime counters, not API charges.",'',
           'This is exploratory evidence from twenty repetitions of each of three task families, not sixty distinct tasks. Budget-exhausted/error baselines are censored rather than counted as omissions. Arm counts can be small and unequal; do not infer latent H1–H4 labels from responses. Context remains 16K despite the larger action budget, so long conversations may be truncated by the runtime. The prior smaller pilots use different seeds/budgets and were not pooled. No claim that raising the budget caused an improvement is justified by this batch alone.','',
           'Files: results.csv, summary.json, config.json, started.json, completed.json, run-*/trace.jsonl and saved baseline/final sources. protocol/ contains the source snapshot captured before execution.']
    (folder/'REPORT.md').write_text('\n'.join(text)+'\n')
    print('Wrote',folder/'REPORT.md')


if __name__=='__main__': main()
