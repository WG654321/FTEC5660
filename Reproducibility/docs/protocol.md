# Frozen main experiment protocol

Frozen before main outcomes were analyzed (2026-11-08, Asia/Shanghai).

## Target and deviation
Target: ACE paper v3 Table 2, Formula offline adaptation with training labels (reported base 67.5%, ACE 85.5%). Test whether the direction of improvement holds in the current accessible model and reduced-data setting. Appendix A.6/Table 19 motivates reflection-depth sensitivity but uses AppWorld, not Formula: our Formula depth comparison is an extension, not a replication of that exact table.

Model: official DeepSeek `deepseek-flash` API, documented 2026-11-08 as V4.1-Flash-1017; the response alias is also recorded. Thinking disabled, temperature 0, output cap 2048. Upstream default provider/model differ. No assertion of identical original conditions. Three roles share one model. No extra prompt editing. Single training epoch; optional embedding dedup disabled in every arm; playbook budget 80000. Four evaluation workers, serial adaptation. Run-order and latency differences are limitations.

## Design
Seeds 42,43,44 govern Python random sampling (not provider RNG). Each run uses 50 train, 30 validation, 100 test items from the official split files, disjoint by exact context text within each seed. Each seed has paired identical subsets across arms. Subsets overlap across seeds; report mean, sample SD and sample variance across three runs, not 300 independent questions. The empty-playbook control uses ACE's Generator prompt and is not the paper's dataset-default-prompt Base LLM. Also retain the ACE runs' own initial empty-playbook tests.

Arms: `base`, `ace_r3` maximum three correction rounds, `ace_r1` maximum one. Start each learning run from an empty playbook. No shared skill memory or response cache across arms. Training labels may guide reflection; validation and final-test labels are used only for scoring. Only an end-of-epoch validation check is performed; this is effectively a final trained checkpoint, with upstream empty-playbook fallback if validation accuracy is zero. No hyperparameter search against validation or test.

The pilot exercised 5/5/10 items. Its questions can overlap the main subsets. No prompts or algorithmic choices were tuned on pilot answers; changes after pilot concern logging, budgeting and concurrency only. Disclose this rather than claim a fully untouched pilot-independent test set.

## Measurement
Primary: official Formula numeric exact-match accuracy, with upstream comma removal and float comparison. Do not introduce rounding tolerance into the primary metric. Denominator must remain all 100 requested test items. Recount wrong indices from saved error logs; any missing evaluated sample invalidates that run until resolved.

Secondary: actual API calls and usage tokens, peak cache-miss cost upper estimate, adaptation cost, fixed final-test cost, empirical reflection-round count, playbook growth and generator output truncations. Latency is descriptive because the API, network and evaluation concurrency differ from the paper.

Paired comparisons are descriptive across seeds. Per-seed discordant-pair counts and exact McNemar p-values may be included as exploratory diagnostics; do not pool overlapping seeds as independent evidence or claim equivalence from non-significance. Report negative and null findings.

## Budget and integrity
User budget CNY 100; cumulative stop ceiling 95. Initial pilot ledger retained. Before each request reserve a byte-based input bound plus output cap at verified peak prices (input 2 CNY/M, output 8 CNY/M). After successful usage return settle to the all-input-cache-miss upper cost; no refund for uncertain requests. No SDK automatic retries. Persist reservations before network calls. Concurrent evaluation threads share a locked ledger. A process lock prevents simultaneous experiment runners. Price changes require review.

Save raw API outputs, usage, configurations, subset hashes, errors and playbooks. Do not commit secrets. No reruns chosen for favorable accuracy. Any failure/restart must remain in the cost accounting and debug diary.

Sources: https://arxiv.org/html/2510.04618v3 ; https://github.com/ace-agent/ace/tree/82709de050e1db6e6ef2f07bcb0393560b94992a ; https://api-docs.deepseek.com/zh-cn/quick_start/pricing/
