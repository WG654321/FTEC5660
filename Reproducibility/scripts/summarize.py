"""Summarize completed runs and conservative usage cost, without reading secrets."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
rows = []
for folder in sorted((ROOT / 'results').glob('*')):
    if not folder.is_dir() or not (folder / 'settings.json').exists():
        continue
    settings = json.loads((folder / 'settings.json').read_text())
    usage_path = folder / 'usage.jsonl'
    usage = [json.loads(x) for x in usage_path.read_text().splitlines()] if usage_path.exists() else []
    inputs = sum((x.get('usage') or {}).get('prompt_tokens',0) for x in usage)
    outputs = sum((x.get('usage') or {}).get('completion_tokens',0) for x in usage)
    row = dict(run=folder.name, arm=settings['arm'], calls=len(usage), input_tokens=inputs, output_tokens=outputs,
               cost_upper_cny=(inputs*settings['input_cny_million']+outputs*settings['output_cny_million'])/1e6)
    final = list(folder.glob('*/final_results.json'))
    row['completed'] = bool(final)
    if final:
        results = json.loads(final[0].read_text())
        metrics = results.get('final_test_results', results.get('test_results', {}))
        row['accuracy'] = metrics.get('accuracy')
    rows.append(row)
report = {'runs': rows, 'usage_cost_upper_cny': sum(r['cost_upper_cny'] for r in rows),
          'note': 'Cache-miss peak rates; provider bill may be lower. Pilot results are not final evidence.'}
(ROOT / 'results/summary.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
