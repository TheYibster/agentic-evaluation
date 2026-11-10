"""Exploratory natural-omission pilot. No forced omissions or synthetic history."""
import argparse
import csv
import json
import random
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from pilot import ARMS, ask, test_code
from harder_tasks import TASKS

SYSTEM = '''Repair the repository for the user's request. Respond with one JSON action per turn, without markdown.
Available actions:
{"action":"list_files"}
{"action":"read_file","path":"filename"}
{"action":"search","query":"literal text"}
{"action":"write_file","path":"filename","content":"complete source"}
{"action":"run_tests"}
{"action":"finish"}
The public API is in solution.py. Use list_files to discover repository filenames. Only existing .py source files other than tests.py can be edited. Do not invent actions.'''


def setup(folder, task, reference=False):
    for name, content in task['files'].items():
        (folder/name).write_text(content, encoding='utf-8')
    if reference:
        (folder/'solution.py').write_text(task['reference'], encoding='utf-8')
    # The original sandbox uses isolated Python; explicitly add the mounted
    # repository for imports, without exposing host files or credentials.
    (folder/'tests.py').write_text("import sys\nsys.path.insert(0, '/work')\n"+task['tests'], encoding='utf-8')


def snapshot(folder):
    return {p.name:p.read_text(encoding='utf-8') for p in folder.iterdir() if p.is_file()}


def phase(messages, folder, cfg, seed, log, label):
    invoked=valid=passed=False
    status='budget_exhausted'
    for turn in range(cfg['max_turns']):
        try:
            response=ask(messages,cfg,seed)
            log({'phase':label,'turn':turn,'response':response})
            content=response['message']['content']
            messages.append({'role':'assistant','content':content})
            action=json.loads(content)
            kind=action['action']
            if kind=='finish':
                status='finished'
                break
            files=snapshot(folder)
            if kind=='list_files': result={'files':sorted(files)}
            elif kind=='search' and isinstance(action.get('query'),str):
                result={'matches':[(name,i,line) for name,text in files.items() for i,line in enumerate(text.splitlines(),1) if action['query'] in line][:100]}
            elif kind=='read_file' and action.get('path') in files:
                result={'content':files[action['path']]}
            elif kind=='write_file' and action.get('path') in files and action['path'].endswith('.py') and action['path']!='tests.py':
                source=action['content']
                if not isinstance(source,str) or len(source.encode())>65536: raise ValueError('invalid source')
                (folder/action['path']).write_text(source,encoding='utf-8')
                result={'written':True}
            elif kind=='run_tests':
                invoked=True
                result=test_code(folder,cfg)
                valid|=result['valid']; passed|=result['passed']
            else: result={'error':'Invalid action or path. Use list_files to discover existing files.'}
            log({'phase':label,'action':action,'result':result})
            messages.append({'role':'user','content':'Action result: '+json.dumps(result)})
        except Exception as exc:
            log({'phase':label,'error':repr(exc)})
            status='error'
            break
    return int(invoked),int(valid),int(passed),status


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--authorize-execution',action='store_true')
    ap.add_argument('--check-fixtures',action='store_true')
    ap.add_argument('--out',default='results/harder12')
    ap.add_argument('--medium',action='store_true')
    ap.add_argument('--repeats',type=int)
    ap.add_argument('--max-turns',type=int)
    ap.add_argument('--seed',type=int)
    args=ap.parse_args()
    if not args.authorize_execution: ap.error('Explicit execution authorization required')
    cfg=json.loads(Path(__file__).with_name('config.json').read_text())
    cfg.update(seed=6080,repeats=4,max_turns=24)
    cfg['options'].update(temperature=0.4,num_ctx=16384,num_predict=2048)
    tasks=TASKS
    if args.medium:
        from medium_tasks import TASKS as tasks
        cfg.update(seed=7080,repeats=2)
        cfg['options']['temperature']=0.7
    cfg['suite']='medium' if args.medium else 'harder'
    for key in ('repeats','max_turns','seed'):
        value=getattr(args,key)
        if value is not None:
            if value<1: ap.error(f'--{key.replace("_","-")} must be positive')
            cfg[key]=value
    if args.check_fixtures:
        for task in tasks:
            for ref in (False,True):
                with tempfile.TemporaryDirectory(prefix='agentic-hard-fixture-') as tmp:
                    folder=Path(tmp); setup(folder,task,ref)
                    result=test_code(folder,cfg)
                    if not result['valid'] or result['passed']!=ref: raise RuntimeError((task['id'],ref,result))
            print(task['id'],'buggy fails; reference passes',flush=True)
        return
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    (out/'config.json').write_text(json.dumps(cfg,indent=2))
    protocol=out/'protocol'; protocol.mkdir()
    for source in ('harder_pilot.py','pilot.py','medium_tasks.py','harder_tasks.py','summarize_harder.py'):
        shutil.copyfile(Path(__file__).with_name(source),protocol/source)
    (out/'started.json').write_text(json.dumps({'started_utc':datetime.now(timezone.utc).isoformat(),
        'planned_baselines':len(tasks)*cfg['repeats'],'baseline_turn_limit':cfg['max_turns'],
        'followup_turn_limit':cfg['max_turns'],'stop_rule':'Complete the fixed sample; do not stop based on omission or response outcomes.'},indent=2))
    (out/'design.txt').write_text('Exploratory natural baseline; suite, repeats and temperature recorded in config.json; no forced omissions. Uniform seeded C0-C3 assignment only for finished U0=0 baselines. Controller audits occur after follow-up and are never shown to the model. This batch changes task complexity, tools, temperature and budgets together; it cannot isolate their effects.\n')
    rng=random.Random(cfg['seed'])
    fields=['run','task','repeat','seed','model','u0','baseline_valid','baseline_passed','baseline_status','arm','u1','followup_valid','followup_passed','followup_status','baseline_audit_valid','baseline_audit_passed','final_audit_valid','final_audit_passed']
    with (out/'results.csv').open('x',newline='') as output:
        writer=csv.DictWriter(output,fieldnames=fields); writer.writeheader(); output.flush()
        for index,(task,repeat) in enumerate((t,r) for r in range(cfg['repeats']) for t in tasks):
            seed=cfg['seed']+index
            run_dir=out/f'run-{index:03}'; run_dir.mkdir()
            with tempfile.TemporaryDirectory(prefix='agentic-hard-') as tmp,(run_dir/'trace.jsonl').open('x') as trace:
                def log(event): trace.write(json.dumps(event)+'\n'); trace.flush()
                folder=Path(tmp); setup(folder,task)
                initial=snapshot(folder)
                messages=[{'role':'system','content':SYSTEM},{'role':'user','content':task['prompt']}]
                log({'seed':seed,'config':cfg,'initial_messages':messages,'initial_files':initial})
                b=phase(messages,folder,cfg,seed,log,'baseline')
                baseline=snapshot(folder)
                (run_dir/'baseline-files.json').write_text(json.dumps(baseline,indent=2))
                (run_dir/'baseline-context.json').write_text(json.dumps(messages,indent=2))
                arm=''; f=(0,0,0,'not_assigned')
                if b[0]==0 and b[3]=='finished':
                    arm=rng.choice(list(ARMS))
                    messages.append({'role':'user','content':ARMS[arm]})
                    log({'assignment':arm,'intervention':ARMS[arm]})
                    f=phase(messages,folder,cfg,seed,log,'followup')
                final=snapshot(folder)
                (run_dir/'final-files.json').write_text(json.dumps(final,indent=2))
                # Separate outcome audits: never counted as model tool calls.
                fa=test_code(folder,cfg)
                for name,source in baseline.items(): (folder/name).write_text(source,encoding='utf-8')
                ba=test_code(folder,cfg)
                log({'controller_audits':{'baseline':ba,'final':fa}})
                row=dict(zip(fields,[index,task['id'],repeat,seed,cfg['model'],*b,arm,*f,int(ba['valid']),int(ba['passed']),int(fa['valid']),int(fa['passed'])]))
                writer.writerow(row); output.flush()
                print(json.dumps(row),flush=True)
    (out/'completed.json').write_text(json.dumps({'completed_utc':datetime.now(timezone.utc).isoformat(),
        'completed_baselines':len(tasks)*cfg['repeats']},indent=2))


if __name__=='__main__': main()
