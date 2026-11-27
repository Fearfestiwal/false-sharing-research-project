from pathlib import Path
import sys,csv,json,statistics,html,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/python'))
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,Flowable
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

for name,file in [('Body','arial.ttf'),('BodyBold','arialbd.ttf'),('BodyItalic','ariali.ttf')]:
 pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')
navy=colors.HexColor('#163144');teal=colors.HexColor('#127c87');orange=colors.HexColor('#db7556')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Text',fontName='Body',fontSize=10.1,leading=14.2,spaceAfter=8,textColor=navy))
styles.add(ParagraphStyle(name='SmallText',fontName='Body',fontSize=8.3,leading=11,spaceAfter=6,textColor=navy))
styles.add(ParagraphStyle(name='SectionTitle',fontName='BodyBold',fontSize=17,leading=21,spaceAfter=12,textColor=navy))
styles.add(ParagraphStyle(name='PaperTitle',fontName='BodyBold',fontSize=26,leading=30,spaceAfter=12,textColor=navy))
styles.add(ParagraphStyle(name='SubTitle',fontName='BodyBold',fontSize=11.5,leading=15,spaceBefore=8,spaceAfter=7,textColor=teal))
story=[];md=[]
def p(text,small=False):
 story.append(Paragraph(text,styles['SmallText' if small else 'Text']));md.append(text.replace('<b>','**').replace('</b>','**'))
def h(text):story.append(Paragraph(text,styles['SubTitle']));md.append('### '+text)
def page(title):
 if story:story.append(PageBreak())
 story.append(Paragraph(title,styles['SectionTitle']));md.append('\n## '+title)
def fig(name,caption,width=480):
 from PIL import Image as PI
 path=ROOT/'figures'/name;w,hh=PI.open(path).size
 story.append(Image(str(path),width=width,height=width*hh/w));p(caption,True);md.append(f'![{caption}](figures/{name})')
def table(rows,widths):
 cells=[[Paragraph(str(c),styles['SmallText'])for c in row]for row in rows]
 t=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2eff0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.8,teal),('LINEBELOW',(0,-1),(-1,-1),.5,teal)]));story.append(t);story.append(Spacer(1,9));md.extend([' | '.join(map(str,row))for row in rows])
class LayoutDiagram(Flowable):
 def __init__(self):Flowable.__init__(self);self.width=480;self.height=111
 def draw(self):
  c=self.canv;c.setFont('BodyBold',10)
  for y,label,col in [(82,'Adjacent: 8-byte stride',orange),(27,'Separated: 64-byte stride',teal)]:
   c.setFillColor(navy);c.drawString(0,y+15,label)
   for i in range(4):
    x=175+i*72;c.setFillColor(col if y==27 else colors.HexColor('#f3d4c9'));c.roundRect(x,y-4,65,24,3,fill=1,stroke=0)
    c.setFillColor(colors.white if y==27 else navy);c.setFont('Body',9);c.drawCentredString(x+32,y+4,'T'+str(i)+( ' + pad' if y==27 else ''))
   c.setStrokeColor(navy)
   if y==82:c.rect(172,y-7,284,30,fill=0,stroke=1)
   c.setFont('Body',8);c.setFillColor(navy);c.drawString(175,y-19,'One shared line (4 workers)' if y==82 else 'Each box begins on a different cache line')
rows=list(csv.DictReader(open(ROOT/'data/summary.csv')))
lookup={(r['placement'],int(r['threads']),int(r['batch']),int(r['stride'])):float(r['median_ms'])for r in rows}
analysis=json.load(open(ROOT/'data/analysis.json'))
effects={(e['placement'],e['threads'],e['batch']):e['ratio']for e in analysis['effects']}
atomic_analysis=json.load(open(ROOT/'runs/atomic/data/analysis.json'))
store_analysis=json.load(open(ROOT/'runs/matched_store/data/analysis.json'))
ae={(e['placement'],e['threads'],e['batch']):e['ratio']for e in atomic_analysis['effects']}
se={(e['placement'],e['threads'],e['batch']):e['ratio']for e in store_analysis['effects']}
ar={(r['placement'],int(r['threads']),int(r['batch']),int(r['stride'])):float(r['median_ms'])for r in csv.DictReader(open(ROOT/'runs/atomic/data/summary.csv'))}
shutil.copyfile(ROOT/'runs/atomic/figures/scaling.png',ROOT/'figures/atomic_scaling.png')
def interval(x):return f'{x[0]:.2f} [{x[1]:.2f}, {x[2]:.2f}]'
N=16000000
def ms(p,t,b,s):return lookup[(p,t,b,s)]
def eff(p,t,b):return effects[(p,t,b)][0]
def ci(p,t,b):
 x=effects[(p,t,b)];return f'{x[0]:.2f} [{x[1]:.2f}, {x[2]:.2f}]'
def pct(a,b):return 100*(1-b/a)
best=max([e for e in analysis['effects'] if e['threads']>1 and e['batch']<N],key=lambda e:e['ratio'][0])
main=eff('P_physical',6,1);batchratio=ms('P_physical',6,1,64)/ms('P_physical',6,N,64)
story.append(Paragraph('When More Threads Become Slower',styles['PaperTitle']))
p('Separating memory layout and publication frequency in a hybrid-CPU microbenchmark')
p('<b>Zeynep Uyan (75616) and Muhammed Enes Aksoy (75569)</b><br/>Architecture of Computers | Group-4 | Vistula University',True)
p('Experimental report - measurements collected 12 November 2026.<br/>AI-assisted manuscript; student verification and reviewer-accessible evidence upload remain required before submission.',True)
h('Abstract')
p(f'False sharing and frequent publication are distinct sources of multithreaded overhead. This study investigates their interaction using a state-publication microbenchmark on an Intel Core i7-13620H running Windows 11. Aligned 8-byte and 64-byte layouts are compared across worker counts, publication intervals and hybrid-core placements. An initial ordinary-store experiment collected 792 measurements. A subsequent workload-matched extension compared ordinary stores and relaxed atomic exchanges, collecting another 1,232 measurements. All correctness, affinity and alignment checks passed. For six physical performance-core workers publishing every iteration, the matched ordinary-store layout ratio was {se[("P_physical",6,1)][0]:.2f}, with a descriptive bootstrap interval spanning one. The atomic-exchange ratio was {ae[("P_physical",6,1)][0]:.2f}; at 256 iterations per publication it fell to {ae[("P_physical",6,256)][0]:.2f}, with an interval spanning one. The extension was motivated by the initial findings and is explicitly exploratory. These results show why publication primitive, placement and update interval must be reported alongside a padding benchmark. Batching also changes loop overhead, so its benefit cannot be attributed solely to fewer memory instructions. No coherence-event counters were collected, and all experiments used one active laptop session. The findings establish conditional timing contrasts rather than a universal speedup or direct measurement of coherence traffic. Code, raw measurements and analysis instructions accompany the report.')
h('1  Motivation and question')
p('Padding changes where workers publish; local accumulation changes how often they publish. Comparing these strategies without holding publication frequency constant confounds two interventions. We ask: <b>How do placement, worker count and publication interval change the benefit of cache-line separation, and what additional timing change remains when publication is batched in an already separated layout?</b>')
story.append(LayoutDiagram());p('Figure 1. Four-worker layout schematic. Measurements use verified addresses; twelve adjacent states occupy two lines, not one.',True)

page('2  Background and experimental design')
p('Bolosky and Scott describe false sharing as accesses to distinct objects within a coherence block that induce unnecessary coherence activity, while emphasizing the difficulty of quantifying it [1]. Intel demonstrates a profiling-led workflow for identifying contended data and evaluating alignment changes [2]. These sources establish the phenomenon; this study does not claim to discover it. Its contribution is a documented comparison of layout and publication interventions on one hybrid laptop CPU. Sections 2-4 report the initial ordinary-store experiment; Section 5 describes the subsequent matched extension without pooling their timings.')
p('Hybrid-core topology must be enumerated rather than inferred from a single logical-processor count [3]. Windows exposes physical-core relationships through GetLogicalProcessorInformationEx [4]. We combine those relationships with per-logical-CPU CPUID leaf 0x1A to distinguish P cores (type 0x40) and E cores (type 0x20). The measured mapping contains six P cores with two SMT siblings each and four E cores.')
table([['Factor','Levels and control'],['Layout','8-byte stride (adjacent); 64-byte stride (separated). Allocation base aligned to 64 bytes.'],['Publication interval B','1, 16, 256, N=16,000,000 iterations; last level publishes only the final state.'],['P physical','1, 2, 4, 6 workers; CPUs selected from [0,2,4,6,8,10].'],['P SMT','2, 4, 8, 12 workers; prefixes of CPUs [0,1,...,11], filling sibling pairs first.'],['E physical','1, 2, 4 workers; prefixes of CPUs [12,13,14,15].'],['Replication','One warm-up and nine measured executions per condition; 88 conditions total.']],[115,365])
h('2.1  Workload and equal-work control')
p('Each worker owns a separate uint64_t state seeded with its worker index plus one. Each logical iteration computes x = 6364136223846793005*x + 1442695040888963407 modulo 2^64. The dependent recurrence prevents trivial constant-counter substitution and provides a deterministic final state. Every B iterations, the worker writes its current state to its assigned slot. All configurations use the same recurrence and N iterations per worker; the arithmetic result is checked independently after completion.')
p('This is a synthetic state-publication workload, not an atomic fetch-add counter. It operationalizes the proposal using reproducible checkpoint stores. The final-only case represents local accumulation; joining and any final reduction are outside the timed interval. No claim about a complete application reduction follows from these measurements.')
h('2.2  What the interventions isolate')
p('At a fixed B and placement, changing stride modifies the address calculation before the worker loop but leaves publication count and arithmetic work unchanged. This is the primary layout contrast. Changing B in the separated layout evaluates batching when inter-worker line sharing has been removed. That contrast changes both publication count and outer-loop overhead; it cannot identify the cost of stores alone.')

page('3  Measurement and primary results')
h('3.1  Execution protocol')
p('The compiler is Zig 0.13.0 with its bundled Clang toolchain, C++17 and -O2. Loop unrolling and loop/SLP vectorization are disabled to retain a comparable dependent arithmetic loop. Volatile stores preserve publications; volatile is not used for synchronization, consistent with LLVM guidance [5]. Atomics implement the start and completion gate, and a Win32 event wakes the controller. Each worker sets a single-CPU affinity mask before the start gate; failure aborts the run.')
p('Timing uses std::chrono::steady_clock from immediately before start release until the completion event wakes the controller. It excludes thread construction, joins and correctness checks, but includes start-release and completion/event overhead. Configurations are shuffled with seed 20261112, then partitioned so all warm-ups precede measurements. No outliers are removed. Each condition is summarized by its median and interquartile range (IQR). Ratios use independent bootstrap resampling of the nine observations per cell (5,000 resamples; fixed seed). Intervals are descriptive, assume exchangeability and do not account for session-level dependence or multiple comparisons.')
fig('scaling.png','Figure 2. Per-iteration publication (B=1). Error bars show IQR, not confidence intervals. Work is fixed per worker; increasing thread count increases total work.')
h('3.2  Layout effects at equal publication frequency')
p(f'For six physical P-core workers at B=1, adjacent and separated medians were {ms("P_physical",6,1,8):.2f} and {ms("P_physical",6,1,64):.2f} ms, respectively. Their ratio was {ci("P_physical",6,1)} (descriptive 95% bootstrap interval). For four E-core workers, the corresponding ratio was {ci("E_physical",4,1)}. Both intervals span one: these cells do not establish a clear padding benefit. Two SMT workers occupy siblings on one P core, giving a ratio of {ci("P_SMT",2,1)}; this placement must not be treated as two independent physical cores.')
p(f'The largest observed layout ratio among multiworker, non-final-only cells was {best["ratio"][0]:.2f} for {best["placement"]}, {best["threads"]} workers and B={best["batch"]}. This is an exploratory maximum across many conditions, not an unbiased estimate of an optimal configuration. Single-worker cells provide a control where inter-worker false sharing is absent; remaining layout differences there reflect noise or other effects.')

page('4  Publication frequency and interaction')
fig('batching.png','Figure 3. Publication interval at the largest worker count in each placement family. Final-only publication is the local-accumulation analogue; medians of nine executions.')
table([['Six physical P workers','Adjacent (ms)','Separated (ms)','Layout ratio [95% interval]']]+[[('Final only' if b==N else 'B = '+str(b)),f'{ms("P_physical",6,b,8):.2f}',f'{ms("P_physical",6,b,64):.2f}',ci('P_physical',6,b)]for b in [1,16,256,N]],[125,90,90,175])
p(f'Within the separated six-P-core layout, B=1 versus final-only publication gave a median-time ratio of {batchratio:.2f}. This timing change occurs without changing line separation and therefore cannot be credited to padding. It combines reduced stores with fewer publication-loop boundaries. Intermediate intervals show whether most of the benefit appears before final-only publication; no monotonic benefit is assumed.')
fig('effects.png','Figure 4. Layout ratios across the full grid. Values above 1 favor separation; values below 1 favor adjacency. Color is capped for legibility; annotations show actual ratios.')
p('The grid is a conditional map, not a universal ranking. Layout and publication interval may interact, and SMT placement changes what is shared within a physical core. At final-only publication, the main body performs no repeated output stores, so sustained ownership bouncing on those output lines is not a sufficient explanation for a large residual timing difference. Such differences require caution about noise, frequency, scheduling or common overhead.',True)

page('5  Exploratory extension: publication primitive')
p('The initial ordinary-store results did not show a clear six-P-core padding benefit. Rather than relabeling this as success, we added an exploratory control: relaxed atomic exchange of the same state. This tests sensitivity to the publication primitive; it is not a correction that erases the initial negative result. Atomic exchange is deliberately used as a stress variant, not recommended as necessary synchronization for worker-owned outputs.')
p('Both extension blocks use the same updated binary, 1,000,000 recurrence iterations per worker, B in {1,16,256,N}, the same layouts and placement groups, and seven measured repetitions after one warm-up per cell. The atomic block was executed first and the matched ordinary-store block second; modes were not interleaved. Each block has 88 conditions and 616 measured runs. Within each block, condition order is randomized. Absolute times across blocks are not a clean causal estimate of the primitive cost because order and power state remain confounded.')
fig('atomic_scaling.png','Figure 5. Atomic-exchange extension at B=1. Medians and IQR from seven executions per cell. Its N differs from Figures 2-4; compare layout ratios, not absolute times across those figures.')
table([['Placement / interval','Ordinary-store ratio','Atomic-exchange ratio']]+[[label,interval(se[(pl,t,b)]),interval(ae[(pl,t,b)])]for label,pl,t,b in [('P physical / 6 / B=1','P_physical',6,1),('P physical / 6 / B=16','P_physical',6,16),('P physical / 6 / B=256','P_physical',6,256),('P physical / 6 / final','P_physical',6,1000000),('P SMT / 2 / B=1','P_SMT',2,1),('P SMT / 12 / B=1','P_SMT',12,1),('E physical / 4 / B=1','E_physical',4,1)]],[150,165,165])
p(f'For six physical P workers, atomic B=1 medians were {ar[("P_physical",6,1,8)]:.2f} ms adjacent and {ar[("P_physical",6,1,64)]:.2f} ms separated. Their {ae[("P_physical",6,1)][0]:.2f}-fold ratio contracts to {ae[("P_physical",6,256)][0]:.2f} at B=256, whose interval spans one. The generated assembly contains a memory xchg for the atomic variant. The same-cell store result does not reproduce this large separation benefit. These observations are consistent with sensitivity to atomic publication and topology; they still do not count coherence events. Small final-only timings and residual layout ratios caution against reading every ratio as false sharing.',True)

page('6  Interpretation, costs and limitations')
h('6.1  Answer to the research question')
p(f'The equal-frequency layout contrast and the separated-layout batching contrast produce different quantities. On six physical P workers the measured layout ratio changes from {eff("P_physical",6,1):.2f} at B=1 to {eff("P_physical",6,N):.2f} with final-only publication. The observed benefit therefore depends on publication regime rather than on padding alone. The practical interpretation is to measure the intended update pattern and placement before expanding every per-thread object.')
p('The adjacent allocation uses 8 bytes per worker, while the separated allocation reserves 64 bytes per worker: an eightfold storage increase. For six workers this is 48 versus 384 allocated bytes; for twelve workers, 96 versus 768 bytes. These are allocation sizes, not measured resident-set or whole-program memory costs. Larger footprints may matter in real data structures, but this tiny experiment cannot quantify cache-capacity or TLB penalties.')
h('6.2  Mechanism and evidence boundary')
p('Addresses confirm when output states share a 64-byte line. The same worker loop and publication count are used in each fixed-B stride contrast. These controls make false sharing a plausible interpretation of suitable timing differences. They do not measure coherence messages. No HITM, cache-to-cache, invalidation or other PMU events were collected. Intel recommends profiling contended structures [2]; a follow-up should correlate timing with appropriate hardware events before claiming a quantified coherence mechanism.')
h('6.3  Threats to validity')
p('<b>Environment.</b> This is one session on an active Windows 11 desktop (build 26200), with Balanced power policy. A pre-run power snapshot reported battery operation and 85% charge. Power, temperature and frequency were not continuously logged. Background processes were not eliminated; assembly-generation work overlapped the early execution period. Random ordering and robust summaries reduce some sensitivity but cannot remove these confounders.')
p('<b>Timing and synchronization.</b> Common completion atomics and event wake-up add overhead, and the controller is not explicitly pinned. Physical P workers leave their SMT siblings available to other processes. Short runs and scheduling noise can influence ratios. Warm-ups occur in a separate phase; this does not guarantee a stationary thermal state throughout measurements.')
p('<b>Workload and scaling.</b> A serial multiply-add recurrence is intentionally simple. The added exchange variant does not implement a full concurrent application or consumer protocol. Publication batching changes loop overhead as well as stores. Scaling is weak: total work grows with worker count. Rising elapsed time is not proof that fixed-work parallel speedup is negative. Initial and extension workloads use different N and source versions; their times are not pooled.')
p('<b>Statistics and generalization.</b> Nine initial and seven extension executions per cell are insufficient for strong tail-latency conclusions. Bootstrap intervals are descriptive, not confirmatory tests. The extension followed inspection of the initial results; mode blocks were sequential. There is no second machine, independent session or alternate compiler. P/E differences include shared-resource and placement differences, not a single isolated cause.')
h('6.4  Conclusion')
p('Separation, publication reduction and publication primitive should be reported distinctly. A large atomic-exchange layout contrast coexists with an inconclusive ordinary-store contrast on the same machine. Batching substantially changes the atomic result. This supports conditional decisions for the tested microbenchmark, while stronger causal and application-level claims require hardware-event profiling and independent replication.')

page('7  Reproducibility, declarations and references')
h('7.1  Evidence package')
p('The accompanying research_package.zip contains source, build/run scripts, raw measurements, addresses, topology, environment metadata, compiler-produced assembly, statistics, analysis code and this manuscript. README.md gives flags and run instructions. The initial dataset is in data/; the matched blocks are in runs/atomic/data/ and runs/matched_store/data/. The initial source and executable are preserved separately. Across all three blocks there are 2,288 executions: 264 warm-ups and 2,024 measured runs. All recorded correctness, affinity and base-alignment flags are true. No synthetic result values were substituted.')
p('For each record, addresses.csv supplies the assigned CPU, address, address divided by 64, and line offset. Independent validation checks that separated outputs have distinct line indices and zero offsets, whereas adjacent outputs occupy consecutive 8-byte offsets from an aligned base. This confirms allocation layout, not runtime cache residency. The compiler-generated worker loop contains the recurrence multiply/add and an output store after each batch.')
p('The source and binary hashes are retained in data/hashes.txt. New runs go into timestamped directories so the original evidence is preserved. Before submission, the student authors must publish or privately share the evidence package through a reviewer-accessible repository and place its actual URL in the submitted PDF. The accompanying archive is currently the evidence delivery route; no public repository has been created.')
h('7.2  Declaration of Generative AI and AI-Assisted Technologies')
p('OpenAI Codex was used to design and implement the benchmark, execute local experiments, assist with source discovery, analyze saved measurements, generate figures, and draft this manuscript. Automated checks verified final numerical states, recorded affinity success and memory layout. These checks do not replace independent student review of methods, sources and interpretation. The named students must understand and verify the work before submission and accurately declare their own contributions; no unverified individual contribution is asserted here.')
h('7.3  References')
refs=[
('[1] W. J. Bolosky and M. L. Scott, "False Sharing and its Effect on Shared Memory Performance," USENIX SEDMS IV, 1993.','https://www.usenix.org/legacy/publications/library/proceedings/sedms4/bolosky.html'),
('[2] Intel, "False Sharing," Intel VTune Profiler Cookbook, version 2024.2, 2024.','https://www.intel.com/content/www/us/en/docs/vtune-profiler/cookbook/2024-2/false-sharing.html'),
('[3] Intel, "Game Dev Guide for 12th Gen Intel Core Processor," updated June 13, 2022. Used for topology principles, not as a specification of the tested 13th Gen CPU.','https://www.intel.com/content/www/us/en/developer/articles/guide/12th-gen-intel-core-processor-gamedev-guide.html'),
('[4] Microsoft, "GetLogicalProcessorInformationEx function (sysinfoapi.h)," Microsoft Learn.','https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getlogicalprocessorinformationex'),
('[5] LLVM Project, "LLVM Atomic Instructions and Concurrency Guide," section on atomic and volatile operations.','https://llvm.org/docs/Atomics.html')]
for label,url in refs:p(html.escape(label)+f' <link href="{url}" color="#127c87">Source</link>. Accessed November 12, 2026.',True);md.append(url)
p('Keywords: false sharing; memory layout; publication batching; hybrid processors; multithreading; reproducibility.',True)
def footer(c,doc):
 c.setStrokeColor(teal);c.setLineWidth(.7);c.line(42,42,553,42)
 c.setFont('Body',8);c.setFillColor(navy);c.drawString(42,28,'UYAN / AKSOY  |  ARCHITECTURE OF COMPUTERS  |  EXPERIMENTAL REPORT');c.drawRightString(553,28,str(doc.page))
doc=SimpleDocTemplate(str(ROOT/'output/pdf/research_paper.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=38,bottomMargin=55,title='When More Threads Become Slower: Investigating False Sharing and Its Mitigation',author='Zeynep Uyan; Muhammed Enes Aksoy')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(ROOT/'paper.md').write_text('\n\n'.join(md),encoding='utf-8')
print('Wrote paper.md and output/pdf/research_paper.pdf')
