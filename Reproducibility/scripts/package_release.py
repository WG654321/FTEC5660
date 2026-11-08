"""Package reproducible code and measured evidence after final visual review."""
import hashlib
import json
from pathlib import Path
import re
import zipfile
ROOT=Path(__file__).resolve().parents[1]
required=['output/ACE_Reproducibility_Report.pdf','output/ACE_Presentation.pptx','output/analysis/analysis.json']
if not all((ROOT/p).exists() for p in required):raise SystemExit('Final artifacts are missing')
if not json.loads((ROOT/required[-1]).read_text())['complete']:raise SystemExit('Incomplete experiments')
files=[]
for directory in ['scripts','tests','configs','docs','data','results','output/analysis','output/figures']:
    files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='.run.lock')
files.extend(ROOT/p for p in required[:2]+['README.md','requirements-lock.txt','.gitignore'])
for p in files:
    if p.suffix.lower() in {'.py','.json','.jsonl','.md','.txt','.mjs','.log'}:
        if re.search(rb'sk-[A-Za-z0-9]{20,}',p.read_bytes()):raise SystemExit('Possible credential found; packaging stopped')
manifest={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(ROOT/'output/release_manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(ROOT/'output/ACE_Submission_Package.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for p in files:archive.write(p,p.relative_to(ROOT))
    archive.write(ROOT/'output/release_manifest.json','release_manifest.json')
print('Packaged',len(files),'files; source fetched by pinned commit using scripts/fetch_upstream.py')
