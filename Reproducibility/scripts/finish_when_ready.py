"""Wait for the authorized suite, then build artifacts; never launch extra API runs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
deadline=time.monotonic()+3600
while time.monotonic()<deadline:
    if all(any((p/'completed.json').exists() for p in (ROOT/'results').glob(f'main_{arm}_{seed}_*')) for seed in [42,43,44] for arm in ['base','ace_r3','ace_r1']):break
    time.sleep(10)
else:raise SystemExit('Main suite did not complete within one hour; no final artifact generated')
for script in ['analyze.py','summarize.py','build_report.py']:
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts'/script)],cwd=ROOT,check=True)
node=Path('C:/Users/yugan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
subprocess.run([str(node),str(ROOT/'scripts/build_deck.mjs')],cwd=ROOT,check=True)
print('Artifacts generated; visual inspection and release packaging still required.',flush=True)
