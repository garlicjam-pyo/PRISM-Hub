import sys, json, pathlib, numpy as np
ROOT=pathlib.Path(__file__).parent
REPO=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'python'))
from tb_c1_cllc import simulate as simc
from tb_a_array import sim_array, analyze
rows=[]
for vin,ncyc,nstep in [(324,400,400),(400,300,400),(400,400,400),(400,800,400),(400,400,800),(460,400,400)]:
    r=simc(Vin=vin,ncyc=ncyc,Nstep=nstep)
    row=dict(Vin=vin,ncyc=ncyc,Nstep=nstep,Vo=float(r['Vo']),Po=float(r['Po']),Ipri_rms=float(r['Ipri_rms']),Isec_rms=float(r['Isec_rms']),Vo_pp=float(np.ptp(r['Vo_w'])))
    rows.append(row); print('CLLC',row,flush=True)
ar=sim_array(N=8,Iload=375,fratio=1,mode='zcp',tol=dict(C=.1,L=.1,R=.1),seed=3,ncyc=300)
a,b=analyze(ar)
out={'cllc':rows,'array_long':{'summary':{k:float(v) for k,v in b.items()},'fs':[float(x['fs']) for x in a], 'Iavg':[float(x['Iavg']) for x in a], 'zcs':[float(x['zcs']) for x in a]}}
print('ARRAY_LONG',out['array_long'],flush=True)
out['FHA_compare']=[]
for fn in [.9,.97,1,1.03,1.1]:
    v=1+1/6*(1-1/fn**2)
    llc=1/np.sqrt(v*v+(.4*(fn-1/fn))**2)
    cllc=1/np.sqrt(v*v+(.4*(fn-1/fn)*(2+1/6*(1-1/fn**2)))**2)
    out['FHA_compare'].append({'fn':fn,'repo_llc':llc,'symmetric_cllc':cllc})
print('FHA',out['FHA_compare'],flush=True)
(ROOT/'probe_stages_ac_results.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
