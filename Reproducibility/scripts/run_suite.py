"""Run the preregistered main suite serially; stop immediately on any failed arm."""
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONUNBUFFERED': '1'}
for seed in (42,43,44):
    for arm in ('base','ace_r3','ace_r1'):
        completed = [p for p in (ROOT/'results').glob(f'main_{arm}_{seed}_*') if (p/'completed.json').exists()]
        if completed:
            print(f'Skipping completed {arm} seed={seed}', flush=True)
            continue
        logfile = ROOT / 'results' / f'console_main_{arm}_{seed}.log'
        print(f'Starting {arm} seed={seed}', flush=True)
        with logfile.open('a', encoding='utf-8') as log:
            result = subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/run_experiment.py'),'--phase','main','--arm',arm,'--seed',str(seed),'--model','deepseek-flash','--input-cny-million','2','--output-cny-million','8','--workers','4'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            raise SystemExit(f'Suite stopped: {arm}, seed {seed}. See {logfile.name}.')
        print(f'Completed {arm} seed={seed}', flush=True)
print('ALL NINE MAIN RUNS COMPLETE', flush=True)
