"""Sequential repair-capability check and paired C0-C3 checkpoint replay."""
import argparse
import copy
import csv
import hashlib
import json
import random
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from harder_pilot import phase, snapshot
from pilot import ARMS, test_code

REPAIR = ('The current repository contains an attempted repair that may still be incorrect. '
          'Explicitly invoke run_tests, inspect the failures, and repair the implementation. '
          'Rerun tests after your changes. Preserve the task requirements and immutable tests. '
          'Use finish when ready.')


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


def restore(folder, files):
    for name, content in files.items():
        if Path(name).name != name or name in ('.', '..'):
            raise ValueError('Unsafe checkpoint filename')
        (folder/name).write_text(content, encoding='utf-8')
        (folder/name).chmod(0o644)


def checkpoints(source):
    cfg=json.loads((source/'config.json').read_text())
    rows=list(csv.DictReader((source/'results.csv').open()))
    selected=[]
    for row in rows:
        if row['baseline_status']!='finished' or row['u0']!='0':
            continue
        run=source/f"run-{int(row['run']):03}"
        files=json.loads((run/'baseline-files.json').read_text())
        context=json.loads((run/'baseline-context.json').read_text())
        events=[json.loads(line) for line in (run/'trace.jsonl').read_text().splitlines()]
        reconstructed=copy.deepcopy(events[0]['initial_messages'])
        for event in events:
            if event.get('phase')!='baseline': continue
            if 'response' in event:
                reconstructed.append({'role':'assistant','content':event['response']['message']['content']})
            elif 'action' in event:
                if event['action']['action']=='run_tests': raise RuntimeError('Not an omission')
                reconstructed.append({'role':'user','content':'Action result: '+json.dumps(event['result'])})
        if reconstructed!=context or json.loads(context[-1]['content']).get('action')!='finish':
            raise RuntimeError('Saved context does not match baseline trace')
        # Reconstruct the baseline files directly from logged source writes.
        reconstructed_files=copy.deepcopy(events[0]['initial_files'])
        for event in events:
            if event.get('phase')=='baseline' and event.get('action',{}).get('action')=='write_file' and event.get('result',{}).get('written'):
                reconstructed_files[event['action']['path']]=event['action']['content']
        if reconstructed_files!=files: raise RuntimeError('Saved files do not match baseline writes')
        selected.append({'run':int(row['run']),'task':row['task'],
                         'baseline_passed':int(row['baseline_audit_passed']),
                         'files':files,'context':context,
                         'checkpoint_sha256':sha({'files':files,'context':context})})
    if len(selected)!=20 or sum(not c['baseline_passed'] for c in selected)!=18:
        raise RuntimeError('Expected the 20 saved omissions, including 18 incorrect checkpoints')
    return cfg,selected


def prepare(out, kind, cfg, cases, source):
    out.mkdir(parents=True,exist_ok=False)
    save(out/'config.json',cfg)
    manifest={'kind':kind,'source':source.as_posix(),'started_utc':now(),
              'planned_cases':len(cases),'max_turns':64,
              'stop_rule':'Complete all planned cases, without stopping or changing settings based on outcomes.',
              'cases':[{k:v for k,v in case.items() if k not in ('files','context')} for case in cases]}
    save(out/'manifest.json',manifest)
    protocol=out/'protocol'; protocol.mkdir()
    for name in ('repair_replay.py','harder_pilot.py','pilot.py','summarize_repair_replay.py'):
        shutil.copyfile(Path(__file__).with_name(name),protocol/name)


def collect(out, kind, cfg, cases):
    fields=['kind','source_run','task','arm','seed','initial_audit_passed','invoked_tests',
            'valid_test_execution','ever_passed_agent_tests','status','final_audit_valid',
            'final_audit_passed','incorrect_to_correct','model_calls','write_calls',
            'distinct_source_states','checkpoint_sha256']
    with (out/'results.csv').open('x',newline='',encoding='utf-8') as output:
        writer=csv.DictWriter(output,fieldnames=fields); writer.writeheader(); output.flush()
        for index,case in enumerate(cases):
            label=f"run-{case['run']:03}-{case['arm']}"
            run=out/label; run.mkdir()
            if kind=='repair_check':
                # Fresh task context removes the agent's earlier decisions; code
                # remains the same saved incorrect attempted repair.
                messages=copy.deepcopy(case['context'][:2])
                messages.append({'role':'user','content':REPAIR})
            else:
                messages=copy.deepcopy(case['context'])
                messages.append({'role':'user','content':ARMS[case['arm']]})
            initial_messages=copy.deepcopy(messages)
            save(run/'initial-files.json',case['files'])
            save(run/'initial-context.json',messages)
            events=[]
            with tempfile.TemporaryDirectory(prefix='agentic-replay-') as tmp,(run/'trace.jsonl').open('x',encoding='utf-8') as trace:
                folder=Path(tmp); restore(folder,case['files'])
                def log(event):
                    events.append(event)
                    trace.write(json.dumps(event)+'\n'); trace.flush()
                log({'kind':kind,'source_run':case['run'],'arm':case['arm'],'seed':case['seed'],
                     'checkpoint_sha256':case['checkpoint_sha256'],'initial_files_sha256':sha(case['files']),
                     'initial_messages':messages,'config':cfg})
                result=phase(messages,folder,cfg,case['seed'],log,kind)
                if messages[:len(initial_messages)]!=initial_messages:
                    raise RuntimeError('Starting conversation changed')
                final=snapshot(folder)
                save(run/'final-files.json',final); save(run/'final-context.json',messages)
                audit=test_code(folder,cfg)
                log({'controller_final_audit':audit})
            observed=any(e.get('action',{}).get('action')=='run_tests' for e in events)
            if observed!=bool(result[0]): raise RuntimeError('Invocation/trace mismatch')
            writes=[e['action'] for e in events if e.get('action',{}).get('action')=='write_file' and e.get('result',{}).get('written')]
            states={sha(case['files'])}; state=copy.deepcopy(case['files'])
            for action in writes:
                state[action['path']]=action['content']; states.add(sha(state))
            row=dict(zip(fields,[kind,case['run'],case['task'],case['arm'],case['seed'],case['baseline_passed'],
                *result,int(audit['valid']),int(audit['passed']),int(not case['baseline_passed'] and audit['passed']),
                sum('response' in e for e in events),len(writes),len(states),case['checkpoint_sha256']]))
            writer.writerow(row); output.flush()
            print(f"{kind} {index+1}/{len(cases)}: source={case['run']} {case['arm']} tests={result[0]} status={result[3]} correct={audit['passed']}",flush=True)
    save(out/'completed.json',{'completed_utc':now(),'cases':len(cases)})


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--authorize-execution',action='store_true')
    ap.add_argument('--source',default='results/medium60-turn64')
    ap.add_argument('--repair-out',default='results/repair-check18')
    ap.add_argument('--replay-out',default='results/balanced-replay80')
    args=ap.parse_args()
    if not args.authorize_execution: ap.error('Explicit execution authorization required')
    source=Path(args.source); repair_out=Path(args.repair_out); replay_out=Path(args.replay_out)
    if repair_out.exists() or replay_out.exists(): raise RuntimeError('Use new output directories')
    cfg,selected=checkpoints(source); cfg['max_turns']=64
    # Verify correctness on the restored snapshots before making model calls.
    for case in selected:
        with tempfile.TemporaryDirectory(prefix='agentic-replay-preflight-') as tmp:
            folder=Path(tmp); restore(folder,case['files']); audit=test_code(folder,cfg)
            if not audit['valid'] or int(audit['passed'])!=case['baseline_passed']:
                raise RuntimeError(f"Preflight audit mismatch: {case['run']}")
    print('Preflight passed: 20 verified omission checkpoints, 18 incorrect and 2 correct.',flush=True)
    repair=[{**case,'arm':'explicit_repair','seed':9000+case['run']} for case in selected if not case['baseline_passed']]
    replay=[]; rng=random.Random(10080)
    for case in selected:
        arms=list(ARMS); rng.shuffle(arms)
        replay.extend({**case,'arm':arm,'seed':10000+case['run']} for arm in arms)
    # Record both schedules before observing any new outcomes.
    prepare(repair_out,'repair_check',cfg,repair,source)
    prepare(replay_out,'balanced_replay',cfg,replay,source)
    save(repair_out/'paired_replay_plan.json',{'replay_out':replay_out.as_posix(),'cases':80,'after':'repair check completes'})
    collect(repair_out,'repair_check',cfg,repair)
    print('Repair check complete; starting balanced replay with settings unchanged.',flush=True)
    collect(replay_out,'balanced_replay',cfg,replay)


if __name__=='__main__': main()
