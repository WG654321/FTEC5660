"""Build an eight-page evidence-based report and figures from completed runs."""
import json
from pathlib import Path
import statistics
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'; FIG=OUT/'figures'; FIG.mkdir(parents=True,exist_ok=True)
data=json.loads((OUT/'analysis/analysis.json').read_text())
if not data['complete']: raise SystemExit('Refusing to build final report before all nine runs finish')
rows=data['rows']; agg=data['aggregates']; arms=['base','ace_r3','ace_r1']
labels={'base':'Empty playbook','ace_r3':'ACE: max 3 rounds','ace_r1':'ACE: max 1 round'}
palette=['#687786','#126C7A','#D88335']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
fig,ax=plt.subplots(figsize=(8,3.5))
for i,arm in enumerate(arms):
    vals=[r['accuracy']*100 for r in rows if r['arm']==arm]
    ax.bar(i,statistics.mean(vals),color=palette[i],width=.55,alpha=.8)
    ax.errorbar(i,statistics.mean(vals),yerr=statistics.stdev(vals),fmt='none',ecolor='#192B38',capsize=5)
    ax.scatter([i-.12,i,i+.12],vals,c='#192B38',zorder=5,s=25)
ax.set_xticks(range(3),[labels[a] for a in arms]);ax.set_ylabel('Exact-match accuracy (%)');ax.set_ylim(0,100)
ax.set_title('Three sampling-seed runs; dots are runs, bars are means, error bars are sample SD')
fig.tight_layout();fig.savefig(FIG/'accuracy.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(9,3.3))
for i,a in enumerate(arms):
    axs[0].bar(i,agg[a]['mean_adaptation_cost_cny'],color=palette[i])
    axs[1].bar(i,agg[a]['mean_test_cost_cny'],color=palette[i])
for ax,title in zip(axs,['Mean adaptation cost','Mean frozen-test cost (100 questions)']):
    ax.set_xticks(range(3),['Empty','3 rounds','1 round']);ax.set_ylabel('CNY, conservative estimate');ax.set_title(title)
fig.tight_layout();fig.savefig(FIG/'cost.png');plt.close(fig)
fig,ax=plt.subplots(figsize=(8,3.4))
for arm,col in zip(arms[1:],palette[1:]):
    for seed in [42,43,44]:
        tr=data['trajectories'][f'{seed}_{arm}']
        ax.plot([t['step'] for t in tr],[t['playbook_tokens'] for t in tr],color=col,alpha=.55,label=labels[arm] if seed==42 else None)
ax.set_xlabel('Training example');ax.set_ylabel('Playbook tokens (upstream tokenizer)');ax.legend();fig.tight_layout();fig.savefig(FIG/'growth.png');plt.close(fig)

pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold','C:/Windows/Fonts/arialbd.ttf'))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyX',fontName='Arial',fontSize=10,leading=14,spaceAfter=9,textColor=colors.HexColor('#213440')))
styles.add(ParagraphStyle(name='TitleX',fontName='ArialBold',fontSize=24,leading=29,spaceAfter=18,textColor=colors.HexColor('#153C4C')))
styles.add(ParagraphStyle(name='HeadX',fontName='ArialBold',fontSize=16,leading=20,spaceAfter=12,textColor=colors.HexColor('#126C7A')))
styles.add(ParagraphStyle(name='SmallX',fontName='Arial',fontSize=8.2,leading=11,spaceAfter=7))
story=[]; sections=[]
def p(txt,style='BodyX'):
    story.append(Paragraph(txt,styles[style]));sections.append(txt)
def head(txt): p(txt,'HeadX')
def table(headers,body,widths=None):
    cells=[[Paragraph(escape(str(x)),styles['SmallX']) for x in row] for row in [headers]+body]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E4EEF0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#126C7A')),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#CCD6DB'))]))
    story.append(t);story.append(Spacer(1,12))
def page():story.append(PageBreak())
def pct(x):return f'{x*100:.1f}%'
def money(x):return f'{x:.3f}'
delta=(agg['ace_r3']['mean_accuracy']-agg['base']['mean_accuracy'])*100
depth=(agg['ace_r1']['mean_accuracy']-agg['ace_r3']['mean_accuracy'])*100

p('Reflection Budgets in Agentic Context Engineering','TitleX')
p('FTEC5660 reproducibility study<br/>Formula benchmark · DeepSeek Flash · November 2026','SmallX')
head('Abstract')
p(f'This study runs the official ACE implementation on a reduced Formula benchmark and changes one algorithmic parameter: the maximum number of correction-reflection rounds, from three to one. Across three sampling seeds, each with 50 training, 30 validation and 100 test questions, the empty-playbook control achieves {pct(agg["base"]["mean_accuracy"])}, three-round ACE {pct(agg["ace_r3"]["mean_accuracy"])}, and one-round ACE {pct(agg["ace_r1"]["mean_accuracy"])} mean exact-match accuracy. The three-round change against the control is {delta:+.1f} percentage points; changing three rounds to one changes mean accuracy by {depth:+.1f} points. These are measurements under a substituted model and reduced data, not an exact reproduction of the paper\'s absolute scores.')
head('Questions and contribution')
p('RQ1: Does the experience accumulated by ACE improve held-out financial numerical reasoning in this resource-constrained setting? RQ2: How does a one-round correction limit affect accuracy, realized reflection work and cost compared with three rounds? The contribution is a documented reproduction and a controlled parameter study, not a new algorithm.')
table(['Configuration','Mean accuracy','Sample SD','Runs'],[[labels[a],pct(agg[a]['mean_accuracy']),f'{100*agg[a]["sd_accuracy"]:.2f} pp','3'] for a in arms],[210,105,100,60])
p('All runs are retained. A negative or null effect is reported as such. The three seeds vary data subsets and order; provider stochasticity is not independently controlled. Overlapping test subsets across seeds preclude treating 300 predictions per arm as 300 independent questions.','SmallX')
page()

head('1. Reproduction target and system architecture')
p('The target is the direction of the supervised offline Formula result in ACE Table 2: the paper reports 67.5% for its DeepSeek-V3.1 base model and 85.5% for ACE. This study evaluates a smaller subset with a current hosted model. The paper\'s reflection-depth sensitivity experiment is on AppWorld (Appendix A.6, Table 19); our one-versus-three comparison transfers that question to Formula. [1]')
table(['Component','Role in the executed pipeline'],[
['Generator','Answers a question using the current playbook and optional reflection.'],
['Evaluator','Compares the extracted answer with the training label or held-out label.'],
['Reflector','Analyzes the answer, using training ground truth during adaptation.'],
['Curator','Proposes structured incremental updates to the playbook.'],
['Playbook','Persists reusable rules across training examples; frozen for held-out tests.']],[105,370])
p('A training step performs initial generation, conditional correction rounds, curation, and a post-curation generation. A correct initial answer still triggers a reflection to tag useful entries. Incorrect answers stop correction early when they become correct. Consequently, a maximum of three rounds does not imply three rounds on every example. [2]')
p('The small modification changes only max_num_rounds. The base arm uses the same Generator with an empty playbook. The underlying LLM weights are not trained. This is context-level self-improvement; the experiment does not establish recursively improving the improvement algorithm itself.')
p('Code map: ace/ace.py orchestrates learning; ace/core/{generator,reflector,curator}.py implement roles; eval/finance/data_processor.py implements the task metric. The local scripts/run_experiment.py supplies a compatible client and records usage without editing upstream algorithm files. [2]','SmallX')
page()

head('2. Experimental protocol and reproducibility')
table(['Setting','Executed value'],[
['Upstream','82709de050e1db6e6ef2f07bcb0393560b94992a'],['Model / provider','deepseek-flash / api.deepseek.com'],['Generation','Thinking disabled; temperature 0; max output 2048'],['Training','One epoch; 50 examples; empty initial playbook'],['Validation / test','30 / 100 examples per seed'],['Seeds','42, 43, 44; Python sampling, not provider RNG'],['Evaluation','Four workers; exact-match Formula processor'],['Memory controls','80,000-token playbook budget; embedding dedup disabled'],['Resource','Windows CPU orchestration; hosted API; no local LLM training']],[130,345])
p('The repository contains 500 train, 300 validation and 200 test records. Exact duplicate contexts were removed across split boundaries before deterministic sampling; none were found. Each seed uses identical subsets across all three arms. Source and subset hashes accompany the deliverable. Semantic near-duplicates and possible pretraining exposure were not ruled out.')
p('Only an end-of-epoch validation check is made. The selected playbook is therefore effectively the final trained checkpoint, except for the upstream empty-playbook fallback if validation accuracy is zero. No hyperparameters are selected from the final test results. The pilot was used for execution debugging, not prompt or algorithm tuning; pilot/main question overlap is disclosed.')
p('Important comparability limits: the model, dataset sizes, output cap, optional deduplication and adaptation schedule differ from the original study. Our control uses ACE\'s Generator prompt rather than the paper\'s dataset-default prompt. All test denominators are audited as exactly 100.','SmallX')
page()

head('3. Accuracy results')
story.append(Image(str(FIG/'accuracy.png'),width=475,height=208))
table(['Seed','Empty','ACE 3: initial / final','ACE 1: initial / final'],[[s,pct(next(r for r in rows if r['seed']==s and r['arm']=='base')['accuracy']), ' / '.join(pct(next(r for r in rows if r['seed']==s and r['arm']=='ace_r3')[k]) for k in ['initial_accuracy','accuracy']), ' / '.join(pct(next(r for r in rows if r['seed']==s and r['arm']=='ace_r1')[k]) for k in ['initial_accuracy','accuracy'])] for s in [42,43,44]],[55,90,165,165])
p(f'The mean three-round-minus-control difference is {delta:+.1f} pp; one-round-minus-three-round is {depth:+.1f} pp. The paper\'s 85.5% reference is not a directly comparable pass/fail threshold. Repeating initial empty-playbook evaluation inside the ACE arms makes model variability visible rather than treating a single baseline realization as deterministic.')
table(['Arm','Sample variance (accuracy fraction²)','Mean ± sample SD'],[[labels[a],f'{agg[a]["variance_accuracy"]:.6f}',f'{100*agg[a]["mean_accuracy"]:.1f} ± {100*agg[a]["sd_accuracy"]:.2f} pp'] for a in arms],[160,165,150])
p('Mean, SD and variance summarize three runs. These are descriptive statistics, not a confidence interval for general performance. Per-run Wilson intervals and exploratory paired discordance tests are in analysis.json. Overlap across seeds and the small number of runs limit inferential claims.','SmallX')
page()

head('4. Cost and realized reflection work')
story.append(Image(str(FIG/'cost.png'),width=475,height=174))
table(['Arm / seed','All calls','Correction rounds','Beyond first','All-run cost'],[[f'{r["arm"]} / {r["seed"]}',r['calls'],r['correction_rounds'],r['beyond_first_round'],money(r['cost_upper_cny'])] for r in rows],[130,65,95,80,105])
p('Costs use returned prompt/completion tokens at the verified peak cache-miss rates of CNY 2 / 8 per million, respectively. Cache hits and off-peak pricing can make the actual invoice lower. No claim is made to have reconciled the account invoice. [3]')
p('All-run cost includes initial tests and validation in addition to adaptation and final tests. The separate final-test figure excludes learning. Correction rounds count Reflector calls on wrong initial answers; correct-answer reflection remains present in both ACE arms. Differences in evolving trajectories can outweigh the nominal round cap.')
page()

head('5. Experience growth and paired error analysis')
story.append(Image(str(FIG/'growth.png'),width=475,height=202))
table(['Seed','3-round → 1-round gains','Losses','Net pp'],[[p['seed'],p['gained'],p['lost'],p['delta_pp']] for p in data['pairs'] if p['from']=='ace_r3' and p['to']=='ace_r1'],[65,160,100,150])
p('Gains are questions the three-round run misses and the one-round run answers correctly; losses reverse that relationship. These matched-question counts distinguish a small net change from extensive answer churn. They do not identify which learned rule caused a particular outcome.')
for arm in ['ace_r3','ace_r1']:
    err=data['errors'][f'42_{arm}']
    if err:
        e=sorted(err,key=lambda x:x['index'])[0]
        p(f'Deterministically selected error example (seed 42, {arm}, lowest wrong index {e["index"]}): predicted {escape(str(e["prediction"]))}; target {escape(str(e["ground_truth"]))}. This example is chosen by index rather than rhetorical appeal. The full question and output are preserved in the local data and raw logs.','SmallX')
p('Playbook token growth is measured by the upstream cl100k_base counter, not the provider billing tokenizer. Larger memory is not in itself evidence of useful learning. Exact-match failures include arithmetic, sign, units or answer formatting; this report does not silently introduce a tolerance to improve the score.','SmallX')
page()

head('6. Debug diary and validity checks')
table(['Issue','Resolution / consequence'],[
['GitHub clone and API access','Clone stalled; directory API was rate-limited. Used official codeload archive and verified its commit marker.'],
['Model-provider compatibility','Injected an OpenAI-compatible DeepSeek client; preserved original role prompts and learning logic.'],
['Unbounded retries','SDK retries disabled. Budget/transport failures stop execution, including through upstream exception handlers.'],
['Budget persistence','Reserve before requests; settle known usage at conservative rates; retain unknown-request reserves; prevent concurrent runner processes.'],
['Optional embedding dependencies','Disabled consistently; used CPU orchestration with minimal dependencies and a pinned environment.'],
['Scoring denominator','Require all 100 questions and consistency between correct counts and wrong-index sets.'],
['Randomness','Temperature zero did not make repeated outputs identical. Report all three seeds and initial-test repeats.']],[135,340])
p('Integrity tests cover budget persistence, settlement and refusal above the limit. Python compilation and end-to-end API runs provide separate checks. An immutable source commit, dependency lock, data hashes, raw responses and playbook snapshots support independent inspection.')
p('Limitations: only one task and one current hosted-model alias; three overlapping sampling seeds; no separation of sampling variance from API randomness; fixed execution order; possible response truncation under the 2048-token cap; supervised training feedback; no causal attribution of individual rules; no reproduction of AppWorld tool-use behavior. A small subset may not expose benefits requiring longer adaptation.')
page()

head('7. Conclusions and reproducibility package')
p(f'The implementation reproduces the operational behavior of experience accumulation and frozen-playbook evaluation. Under the stated conditions, three-round ACE changes mean accuracy by {delta:+.1f} pp relative to the empty-playbook control. Reducing the cap to one changes mean accuracy by {depth:+.1f} pp relative to three rounds. These results answer the selected task under a constrained configuration; they do not establish the original paper\'s absolute performance or broad superiority of either cap.')
p('The most useful follow-up is to replicate with an identical held-out set and repeated provider calls, then vary training volume while holding model and prompts fixed. Any future prompt or evaluator change should be a separate experiment. More reflection should be justified by measured correction gains and final-task performance, rather than assumed to help.')
head('What another student can reproduce')
p('Fetch the pinned upstream archive, install requirements-lock.txt, run prepare_data.py, configure DEEPSEEK_API_KEY locally, and execute run_suite.py. Analyze the nine completed runs with analyze.py. Rebuild this report with build_report.py. API output may vary; the released measurements remain auditable through the accompanying evidence files.')
head('References')
p('[1] Zhang et al. Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models. arXiv:2510.04618v3, 2026. Table 2; Appendix A.6. https://arxiv.org/html/2510.04618v3','SmallX')
p('[2] ACE official implementation, commit 82709de050e1db6e6ef2f07bcb0393560b94992a. https://github.com/ace-agent/ace','SmallX')
p('[3] DeepSeek official model/pricing documentation, checked 8 November 2026. https://api-docs.deepseek.com/zh-cn/quick_start/pricing/','SmallX')
head('Use of AI assistance')
p('AI assistance was used for code preparation, experiment orchestration, analysis and document drafting. All numerical results in this report come from saved API executions and deterministic analysis scripts. The submitting student should review the code, verify conclusions and follow course disclosure requirements.')

def footer(canvas,doc):
    canvas.setFont('Arial',8);canvas.setFillColor(colors.HexColor('#617482'))
    canvas.drawString(55,30,'FTEC5660 · ACE / Formula reproducibility')
    canvas.drawRightString(540,30,str(doc.page))
doc=SimpleDocTemplate(str(OUT/'ACE_Reproducibility_Report.pdf'),pagesize=(595.28,841.89),rightMargin=55,leftMargin=55,topMargin=48,bottomMargin=50)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'report_text.txt').write_text('\n\n'.join(sections),encoding='utf-8')
print('Report and figures generated')
