"""Validate and summarize finished main runs. No network or model calls."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/analysis'
OUT.mkdir(parents=True, exist_ok=True)

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def cost(records):
    return sum(((x.get('usage') or {}).get('prompt_tokens',0)*2 + (x.get('usage') or {}).get('completion_tokens',0)*8)/1e6 for x in records)

def wilson(k,n):
    z=1.96
    center=(k/n+z*z/(2*n))/(1+z*z/n)
    half=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/(1+z*z/n)
    return [center-half,center+half]

def load_run(folder):
    settings=read(folder/'settings.json')
    run=next(folder.glob('ace_run*'))
    final=read(run/'final_results.json')
    metric=final.get('final_test_results',final.get('test_results'))
    errors=read(run/('test_test_results.json' if settings['arm']=='base' else 'final_test_results.json'))['error_log']['errors']
    n=len((ROOT/'data/main'/str(settings['seed'])/'test.jsonl').read_text(encoding='utf-8').splitlines())
    assert metric['total']==n==100, f'Incomplete evaluation: {folder}'
    wrong={e['index'] for e in errors}
    assert len(wrong)==len(errors)==n-metric['correct']
    assert abs(metric['accuracy']-(n-len(wrong))/n)<1e-10
    usage=[json.loads(x) for x in (folder/'usage.jsonl').read_text().splitlines()]
    # Upstream eval calls are in worker threads and have no parent stage stack.
    # Their serial block order is unambiguous: initial 100, validation 30, final 100.
    eval_usage=[u for u in usage if (u.get('call_id') or '').startswith('test_eval_')]
    assert len(eval_usage)==(100 if settings['arm']=='base' else 230)
    adaptation=[u for u in usage if (u.get('call_id') or '').startswith('train_')]
    final_usage=eval_usage[-100:]
    row={'arm':settings['arm'],'seed':settings['seed'],'run':folder.name,'accuracy':metric['accuracy'], 'correct':metric['correct'],'total':n,
         'initial_accuracy':final.get('initial_test_results',metric)['accuracy'],'calls':len(usage),'cost_upper_cny':cost(usage),
         'adaptation_cost_cny':cost(adaptation),'final_test_cost_cny':cost(final_usage),
         'input_tokens':sum(u['usage']['prompt_tokens'] for u in usage),'output_tokens':sum(u['usage']['completion_tokens'] for u in usage),
         'reflection_calls':sum(u.get('role')=='reflector' for u in adaptation),
         'correction_rounds':sum(u.get('role')=='reflector' and re.search(r'_round_\d+$',u.get('call_id','')) is not None for u in adaptation),
         'beyond_first_round':sum(u.get('role')=='reflector' and re.search(r'_round_[1-9]\d*$',u.get('call_id','')) is not None for u in adaptation),
         'truncated_calls':sum(u.get('finish_reason')=='length' for u in usage),
         'wall_seconds':read(folder/'completed.json')['completed_at']-settings['started_at'],
         'wilson95':wilson(metric['correct'],n)}
    trajectory=[]
    if settings['arm']!='base':
        train=read(run/'pre_train_post_train_results.json')
        for step in train:
            trajectory.append({'step':step['step'], 'pre_correct':step['pre_train_result']['is_correct'], 'post_correct':step['post_train_result']['is_correct'], 'playbook_tokens':step['post_train_result']['playbook_num_tokens']})
        row['playbook_tokens']=trajectory[-1]['playbook_tokens']
        row['train_pre_accuracy']=statistics.mean(int(t['pre_correct']) for t in trajectory)
        row['train_post_accuracy']=statistics.mean(int(t['post_correct']) for t in trajectory)
    else:
        row['playbook_tokens']=0
    return row,wrong,errors,trajectory

def main():
    rows=[]; wrongs={}; errors={}; trajectories={}
    for seed in [42,43,44]:
        for arm in ['base','ace_r3','ace_r1']:
            paths=[p for p in (ROOT/'results').glob(f'main_{arm}_{seed}_*') if (p/'completed.json').exists()]
            if not paths:
                continue
            if len(paths)!=1:
                raise RuntimeError('Multiple completed runs need explicit inclusion audit')
            row,wrong,err,traj=load_run(paths[0]); rows.append(row)
            wrongs[(seed,arm)]=wrong; errors[f'{seed}_{arm}']=err; trajectories[f'{seed}_{arm}']=traj
    aggregates={}
    for arm in ['base','ace_r3','ace_r1']:
        items=[r for r in rows if r['arm']==arm]
        if items:
            vals=[r['accuracy'] for r in items]
            aggregates[arm]={'n_runs':len(items),'mean_accuracy':statistics.mean(vals),'sd_accuracy':statistics.stdev(vals) if len(vals)>1 else None,'variance_accuracy':statistics.variance(vals) if len(vals)>1 else None,
                             'mean_cost_cny':statistics.mean(r['cost_upper_cny'] for r in items),'mean_adaptation_cost_cny':statistics.mean(r['adaptation_cost_cny'] for r in items),'mean_test_cost_cny':statistics.mean(r['final_test_cost_cny'] for r in items)}
    pairs=[]
    for seed in [42,43,44]:
        for a,b in [('base','ace_r3'),('base','ace_r1'),('ace_r3','ace_r1')]:
            if (seed,a) not in wrongs or (seed,b) not in wrongs: continue
            gained=len(wrongs[(seed,a)]-wrongs[(seed,b)])
            lost=len(wrongs[(seed,b)]-wrongs[(seed,a)])
            n=gained+lost
            p=min(1,2*sum(math.comb(n,k) for k in range(min(gained,lost)+1))/2**n) if n else 1
            pairs.append({'seed':seed,'from':a,'to':b,'gained':gained,'lost':lost,'delta_pp':gained-lost,'mcnemar_exact_p_exploratory':p})
    report={'rows':rows,'aggregates':aggregates,'pairs':pairs,'trajectories':trajectories,'errors':errors,'complete':len(rows)==9,
            'main_cost_upper_cny':sum(r['cost_upper_cny'] for r in rows)}
    (OUT/'analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if rows:
        fields=sorted(set().union(*(r.keys() for r in rows)))
        with (OUT/'run_metrics.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    print(json.dumps({'completed':len(rows),'aggregates':aggregates,'main_cost_upper_cny':report['main_cost_upper_cny']},indent=2))

if __name__=='__main__': main()
