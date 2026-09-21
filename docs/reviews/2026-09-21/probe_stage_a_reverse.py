import sys, pathlib, json, numpy as np
ROOT=pathlib.Path(__file__).parent
REPO=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'python'))
from tb_a_array import sim_array,analyze
results=[]
for direction in [1,-1]:
    r=sim_array(N=8,Iload=direction*375,fratio=1,mode='zcp',tol=dict(C=.1,L=.1,R=.1),seed=3,ncyc=60)
    a,b=analyze(r)
    d=dict(direction=direction,bus={k:float(v) for k,v in b.items()},zcs=[float(x['zcs']) for x in a],Iavg=[float(x['Iavg']) for x in a],Ipk=[float(x['Ipk']) for x in a],Ploss=sum(x['Ploss'] for x in a))
    results.append(d); print(json.dumps(d,indent=2),flush=True)
(ROOT/'probe_stage_a_reverse_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
