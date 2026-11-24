from pathlib import Path
import sys,csv,json,collections,statistics
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/Path(sys.argv[1]) if len(sys.argv)>1 else ROOT
BASE.mkdir(parents=True,exist_ok=True)
(BASE/'figures').mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/python'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150,'savefig.bbox':'tight'})
rows=list(csv.DictReader(open(BASE/'data/raw.csv')))
assert all(r['correct']==r['affinity_ok']==r['aligned_ok']=='1' for r in rows)
groups=collections.defaultdict(list)
for r in rows:
 if int(r['rep'])>=0:groups[(r['placement'],int(r['threads']),int(r['batch']),int(r['stride']))].append(float(r['seconds']))
summary=[]
for k,v in sorted(groups.items()):
 q=np.percentile(v,[25,75]);summary.append(dict(placement=k[0],threads=k[1],batch=k[2],stride=k[3],n=len(v),median_ms=1000*statistics.median(v),q25_ms=1000*q[0],q75_ms=1000*q[1],min_ms=1000*min(v),max_ms=1000*max(v)))
with open(BASE/'data/summary.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=summary[0]);w.writeheader();w.writerows(summary)
rng=np.random.default_rng(20261112)
def ratio(a,b):
 a=np.array(groups[a]);b=np.array(groups[b]);boot=np.median(rng.choice(a,(5000,len(a))),axis=1)/np.median(rng.choice(b,(5000,len(b))),axis=1)
 return [float(np.median(a)/np.median(b)),*map(float,np.percentile(boot,[2.5,97.5]))]
effects=[]
for p,t,b,s in sorted(groups):
 if s==8:effects.append(dict(placement=p,threads=t,batch=b,ratio=ratio((p,t,b,8),(p,t,b,64))))
json.dump({'rows':len(rows),'measured':sum(len(v) for v in groups.values()),'conditions':len(groups),'effects':effects},open(BASE/'data/analysis.json','w'),indent=2)
colors={8:'#db7556',64:'#127c87'}
fig,axs=plt.subplots(1,3,figsize=(11,3.5))
for ax,p in zip(axs,['P_physical','P_SMT','E_physical']):
 for s in [8,64]:
  rr=sorted([r for r in summary if r['placement']==p and r['batch']==1 and r['stride']==s],key=lambda r:r['threads'])
  ax.errorbar([r['threads'] for r in rr],[r['median_ms'] for r in rr],yerr=[[r['median_ms']-r['q25_ms'] for r in rr],[r['q75_ms']-r['median_ms'] for r in rr]],fmt='o-',color=colors[s],capsize=3,label='Adjacent' if s==8 else 'Separated')
 ax.set_title(p.replace('_',' '));ax.set_xlabel('Worker threads');ax.set_xticks([r['threads'] for r in rr]);ax.grid(alpha=.2)
axs[0].set_ylabel('Elapsed time (ms; median and IQR)');axs[0].legend(frameon=False)
fig.tight_layout();fig.savefig(BASE/'figures/scaling.png');plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(11,3.5))
for ax,(p,t) in zip(axs,[('P_physical',6),('P_SMT',12),('E_physical',4)]):
 for s in [8,64]:
  rr=sorted([r for r in summary if r['placement']==p and r['threads']==t and r['stride']==s],key=lambda r:r['batch'])
  ax.plot(range(len(rr)),[r['median_ms'] for r in rr],'o-',color=colors[s],label='Adjacent' if s==8 else 'Separated')
 ax.set_xticks(range(len(rr)),['1','16','256','Final only']);ax.set_xlabel('Iterations per publication');ax.set_title(f'{p.replace("_"," ")} / {t} workers');ax.grid(alpha=.2)
axs[0].set_ylabel('Elapsed time (ms; median)');axs[0].legend(frameon=False)
fig.tight_layout();fig.savefig(BASE/'figures/batching.png');plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(11,3.4))
for ax,p in zip(axs,['P_physical','P_SMT','E_physical']):
 ts=sorted({k[1] for k in groups if k[0]==p});bs=sorted({k[2] for k in groups if k[0]==p})
 z=np.array([[statistics.median(groups[(p,t,b,8)])/statistics.median(groups[(p,t,b,64)]) for b in bs]for t in ts])
 ax.imshow(z,cmap='RdBu_r',norm=TwoSlopeNorm(vmin=.7,vcenter=1,vmax=2),aspect='auto')
 for i in range(len(ts)):
  for j in range(len(bs)):ax.text(j,i,f'{z[i,j]:.2f}',ha='center',va='center',fontsize=9)
 ax.set_xticks(range(len(bs)),['1','16','256','Final']);ax.set_yticks(range(len(ts)),ts);ax.set_title(p.replace('_',' '));ax.set_xlabel('Iterations per publication')
axs[0].set_ylabel('Worker threads');fig.suptitle('Adjacent / separated median time (>1 favors separation)',fontsize=11)
fig.tight_layout();fig.savefig(BASE/'figures/effects.png');plt.close(fig)
print(json.dumps({'measurements':sum(len(v) for v in groups.values()),'conditions':len(groups),'selected_effects':[e for e in effects if (e['placement'],e['threads'])in [('P_physical',6),('P_SMT',2),('P_SMT',12),('E_physical',4)]]},indent=2))
