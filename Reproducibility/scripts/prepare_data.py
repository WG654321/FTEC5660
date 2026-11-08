"""Prepare deterministic disjoint subsets without API calls."""
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def prepare():
    cfg = json.loads((ROOT / 'configs/experiment.json').read_text())
    source = ROOT / 'upstream/ace-main/eval/finance/data'
    files = {'train': 'formula_train_subset_500.jsonl', 'val': 'formula_val_subset_300.jsonl', 'test': 'formula_test.jsonl'}
    raw = {k: [json.loads(x) for x in (source / v).read_text(encoding='utf-8').splitlines() if x.strip()] for k, v in files.items()}
    # Remove exact question overlap in priority order test > validation > train.
    seen = set()
    clean = {}
    removed = {}
    for split in ('test', 'val', 'train'):
        clean[split] = []
        for item in raw[split]:
            identity = item['context'].strip()
            if identity not in seen:
                clean[split].append(item)
                seen.add(identity)
        removed[split] = len(raw[split]) - len(clean[split])
    manifest = {'source_commit': cfg['upstream_commit'], 'removed_exact_duplicates': removed, 'files': {}}
    for phase in ('pilot', 'main'):
        for seed in cfg['seeds']:
            folder = ROOT / 'data' / phase / str(seed)
            folder.mkdir(parents=True, exist_ok=True)
            for split in files:
                items = random.Random(seed).sample(clean[split], cfg[phase + '_sizes'][split])
                blob = ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in items).encode('utf-8')
                path = folder / (split + '.jsonl')
                path.write_bytes(blob)
                manifest['files'][str(path.relative_to(ROOT))] = {'n': len(items), 'sha256': hashlib.sha256(blob).hexdigest()}
    (ROOT / 'data/manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'source_sizes': {k: len(v) for k, v in raw.items()}, 'removed': removed, 'prepared_files': len(manifest['files'])}))

if __name__ == '__main__':
    prepare()
