import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'output/analysis/analysis.json').read_text())
if not d['complete']:raise SystemExit('Results incomplete')
summary=json.loads((ROOT/'results/summary.json').read_text())
lines=['# ACE Formula reproducibility','', 'Nine completed main runs; three sampling seeds per configuration. Raw evidence, report and presentation accompany the release.','',
'## Results','', '| Configuration | Mean accuracy | Sample SD |','|---|---:|---:|']
for arm,a in d['aggregates'].items():lines.append(f'| {arm} | {100*a["mean_accuracy"]:.1f}% | {100*a["sd_accuracy"]:.2f} pp |')
lines += ['',f'Total successful-call cost upper estimate, including pilot and interrupted attempts: CNY {summary["usage_cost_upper_cny"]:.3f}. This is not the provider invoice. The cumulative ledger retains uncertain-call reservations. User budget CNY 100; stop threshold 95.', '',
'## Scope and limitations','',
'Official ACE source commit `82709de050e1db6e6ef2f07bcb0393560b94992a`. Formula supervised offline adaptation with DeepSeek Flash. Three-round versus one-round maximum correction depth is the only algorithmic modification. Provider integration, logging, budgeting and concurrency are engineering adaptations. Upstream algorithm Python files are unchanged.', '',
'Each seed samples 50 train, 30 validation and 100 test questions. Same-seed arms share identical subsets. Seeds overlap and provider outputs vary even at temperature zero. Do not treat these as 300 independent test questions or as exact replication of the paper\'s model and full-data score. The control is ACE Generator with an empty playbook. See docs/protocol.md for the frozen design.', '',
'## Installation and execution','',
'```powershell','python -m venv .venv',r'.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt',r'.\.venv\Scripts\python.exe scripts/fetch_upstream.py',r'.\.venv\Scripts\python.exe scripts/prepare_data.py','```','',
'Configure DEEPSEEK_API_KEY locally. Do not commit it. Review current model/prices before executing paid runs. No local GPU is required. Optional embedding deduplication is disabled. The exact environment lock was produced on Windows / Python 3.14.', '',
'```powershell',r'.\.venv\Scripts\python.exe -X utf8 -u scripts/run_suite.py',r'.\.venv\Scripts\python.exe scripts/analyze.py',r'.\.venv\Scripts\python.exe scripts/summarize.py',r'.\.venv\Scripts\python.exe scripts/build_report.py','```','',
'The suite skips completed runs. It stops on API errors; inspect rather than deleting the budget ledger. The documented seed-44 interruption was restarted only after verifying the old process had stopped. All failed-attempt logs remain. Final accuracy summaries include exactly one completed run per arm/seed.', '',
'## Evidence and artifacts','',
'- output/analysis/analysis.json: audited metrics, paired errors and playbook trajectories','- output/analysis/run_metrics.csv: per-run measurements','- results/: raw responses, usage, playbooks, run settings and budget ledger','- data/manifest.json: deterministic subset hashes','- docs/recovery.md: interruption/recovery record','- output/ACE_Reproducibility_Report.pdf: report','- output/ACE_Presentation.pptx: slides with speaker notes','- docs/presentation_guide_zh.md: recording guide','',
'Rebuilding slides uses the Codex bundled Artifact Tool and the paths in scripts/build_deck.mjs; experiment and PDF reproduction do not require that proprietary library. The released PPTX is editable.', '',
'## Validation and submission','',
'Run `python -m unittest discover -s tests` for budget tests. Analysis requires all 100 test items and reconciles error indices with correct counts. Source hashing verifies no upstream algorithm edits. The eight-page PDF and ten-slide presentation were visually reviewed before release.', '',
'The student must review the work, add identifying information as required, record a Zoom presentation under 15 minutes. These external submission steps are not represented as already complete. AI assistance was used in implementation, orchestration, analysis and drafting.', '',
'Sources: https://arxiv.org/html/2510.04618v3 ; https://github.com/ace-agent/ace ; https://api-docs.deepseek.com/zh-cn/quick_start/pricing/','']
(ROOT/'README.md').write_text('\n'.join(lines),encoding='utf-8')
