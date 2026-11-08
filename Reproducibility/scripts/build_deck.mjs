import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const runtime='C:/Users/yugan/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const skill='D:/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'));
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs'));
const d=JSON.parse(await fs.readFile(root+'/output/analysis/analysis.json','utf8'));
if(!d.complete)throw new Error('Nine completed runs required');
const p=Presentation.create({slideSize:{width:1280,height:720}});
const dir=root+'/build/deck';await fs.mkdir(dir,{recursive:true});
const arms=['base','ace_r3','ace_r1'],labels=['Empty playbook','ACE 3 rounds','ACE 1 round'];
const pct=v=>(100*v).toFixed(1)+'%';
const round=v=>Number(v.toFixed(4));
function text(s,t,y,size=30){const b=s.shapes.add({geometry:'textbox',position:{left:75,top:y,width:1120,height:size>40?130:110},fill:'none',line:{fill:'none',width:0}});b.text=t;b.text.style={typeface:'Arial',fontSize:size,color:'#173E50',insets:0,wrap:'square'};}
function slide(title,lines,notes){const s=p.slides.add();s.background.fill='#FFFFFF';text(s,title,55,44);lines.forEach((x,i)=>text(s,x,200+i*115));s.speakerNotes.text=notes+' Sources: https://arxiv.org/html/2510.04618v3 ; local output/analysis/analysis.json.';return s;}
slide('Reflection budgets in ACE',['Formula benchmark reproduction','DeepSeek Flash · 3 sampling seeds · 9 runs','FTEC5660 · November 2026'],'介绍目标：验证经验积累是否改善未见问题，比较一轮与三轮反思。约一分钟。');
slide('Reproduction target',['Paper Formula result: base 67.5%, ACE 85.5%','Our model and dataset sizes differ','Target: direction of improvement under stated constraints'],'说明原论文与当前实验不能直接比较绝对数值。原论文反思轮数实验在 AppWorld，我们把问题迁移到 Formula。');
slide('Experience accumulation',['Generator answers with the current playbook','Reflector analyzes feedback; Curator updates rules','Frozen playbook answers held-out test questions'],'模型权重不变，改进对象是经验手册。正确答案仍会反思，错误答案纠正后提前停止。');
slide('Experimental controls',['50 training / 30 validation / 100 test per seed','Same subsets across three arms; seeds 42, 43, 44','Temperature 0, thinking off, output cap 2048'],'种子控制数据抽样，不保证 API 确定性。三个种子有重叠，不能视为三百道独立问题。');
let s=slide('Held-out accuracy',[], '展示三个运行平均准确率，标准差见报告。所有结果均保留，包括负结果。');
let c=s.charts.add('bar',{position:{left:90,top:190,width:1100,height:400},categories:labels,series:[{name:'Accuracy (%)',values:arms.map(a=>round(100*d.aggregates[a].mean_accuracy)),fill:'#126C7A'}],hasLegend:false,barOptions:{direction:'column'},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0'},yAxis:{min:0,max:100}});applyPresentationChartFont(c,{fontFamily:'Arial'});
slide('Results by sampling seed',[42,43,44].map(seed=>`Seed ${seed}: `+arms.map((a,i)=>labels[i]+' '+pct(d.rows.find(r=>r.seed===seed&&r.arm===a).accuracy)).join(' / ')),'逐个种子比较，而不是只展示最好的一次。');
s=slide('Adaptation and test costs',[],'分开计算学习成本和最终测试成本。按高峰未缓存价格保守估算，实际发票可能更低。');
c=s.charts.add('bar',{position:{left:90,top:190,width:1100,height:400},categories:labels,series:[{name:'Adaptation CNY',values:arms.map(a=>round(d.aggregates[a].mean_adaptation_cost_cny)),fill:'#126C7A'},{name:'Final test CNY',values:arms.map(a=>round(d.aggregates[a].mean_test_cost_cny)),fill:'#D88335'}],hasLegend:true,barOptions:{direction:'column',grouping:'clustered'},dataLabels:{showValue:true,numberFormatCode:'0.00'},yAxis:{numberFormatCode:'0.00'}});applyPresentationChartFont(c,{fontFamily:'Arial'});
slide('Allowed rounds versus actual work',[42,43,44].map(seed=>{let a=d.rows.find(r=>r.seed===seed&&r.arm==='ace_r3'),b=d.rows.find(r=>r.seed===seed&&r.arm==='ace_r1');return `Seed ${seed}: correction rounds ${a.correction_rounds} vs ${b.correction_rounds}; extra rounds ${a.beyond_first_round}`;}),'最大轮数不等于真实调用次数。两组手册发展路径不同，不能假设一轮一定显著便宜。');
slide('Limitations',['One task and a substituted hosted model','Three overlapping samples and provider variability','Strict scoring, finite output cap, fixed run order'],'说明没有对模型权重进行训练，也没有证明递归自我改进。');
slide('Reproducibility and conclusions',[`ACE 3 mean: ${pct(d.aggregates.ace_r3.mean_accuracy)}; empty: ${pct(d.aggregates.base.mean_accuracy)}`,`ACE 1 mean: ${pct(d.aggregates.ace_r1.mean_accuracy)}`,'Pinned code, data hashes, raw logs and cost ledger'],'最后展示 README 和经验手册。本人审阅材料并按课程规则披露 AI 辅助。');
for(const [i,s]of p.slides.items.entries()){let b=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(dir+`/slide-${i+1}.png`,new Uint8Array(await b.arrayBuffer()));}
const candidate=dir+'/candidate.pptx';await(await PresentationFile.exportPptx(p)).save(candidate);
console.log(await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:root+'/output/ACE_Presentation.pptx',pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000'],requiredNativeChartOwnerSlides:[5,7],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:dir+'/validation.json'}));
