"""Requirements matrix for one frozen controller, including known limitations."""
from dataclasses import replace, asdict
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pprc_fixed_control import NOMINAL, GAIN, run, assess
from pprc_two_stage import Parameters, design, simulate

OUT=Path(__file__).resolve().parents[1]/'validation'/'2026-09-22-fixed-control'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert np.max(np.abs(design(788,5000,NOMINAL)-GAIN))<1e-10
    # Check recovery semantics: never outside / recovered / not recovered.
    t=np.array([.001,.0015,.002,.003]); x=np.zeros((4,6)); x[:,2]=400
    assert assess(t,x,.001,True,True)['recovery_s']==0
    x[1,2]=391
    assert assess(t,x,.001,True,True)['recovery_s']==.001
    x[-1,2]=395
    assert assess(t,x,.001,True,True)['recovery_s'] is None
    specs=[]
    for v in sorted(set(range(640,921,10))|{648,788,907}):
        specs.append((f'rated60_{v}',v,1000,25000,NOMINAL,'nominal'))
    for v in [640,788,920]:
        specs += [(f'rated50_{v}',v,5000,25000,NOMINAL,'nominal'),
                  (f'unload60_{v}',v,25000,1000,NOMINAL,'nominal'),
                  (f'overload29_{v}',v,5000,29000,NOMINAL,'outside_continuous_rating')]
    specs += [('regen_640',640,5000,-5000,NOMINAL,'nominal'),
              ('regen_920',920,-5000,5000,NOMINAL,'nominal'),
              ('zero_crossing_800',800,5000,-5000,NOMINAL,'nominal')]
    # Diagnostic tolerance set: one factor at a time, not all combinations.
    for field in ['L','Cs','Cb','Lh','Clink','R','Rh']:
        for factor in [.9,1.1]:
            p=replace(NOMINAL,**{field:getattr(NOMINAL,field)*factor})
            for v in [640,920]:
                specs.append((f'tolerance_{field}_{factor}_{v}',v,1000,25000,p,'tolerance'))
    for field,value in [('delay',10e-6),('delay',15e-6),('tau',15e-6),('eta',.94)]:
        for v in [640,920]:
            specs.append((f'sensitivity_{field}_{value}_{v}',v,1000,25000,
                          replace(NOMINAL,**{field:value}),'sensitivity'))
    rows=[]; inputs=[]; traces={}
    for name,v,a,b,p,group in specs:
        r=run(v,a,b,p,keep_trace=True)
        traces[name]=(r.pop('t'),r.pop('x'))
        r.pop('u'); r.update(name=name,group=group)
        if group=='nominal': assert r['requirements_pass'],(name,r['checks'],r['violations'])
        rows.append(r)
        inputs.append(dict(name=name,vbat=v,power0=a,power1=b,dt=r['dt'],duration=r['duration'],
                           K=list(GAIN),parameters=asdict(p),control_parameters=asdict(NOMINAL),
                           expected_pass=r['requirements_pass'],group=group))
        print(name,'pass=',r['requirements_pass'],'droop=',round(r['droop'],3),
              'path=',round(r['path_peak'],3),'recovery_us=',None if r['recovery_s'] is None else round(r['recovery_s']*1e6,1),flush=True)
    # Regression guard: the original nominal 4 kHz candidate exceeded 100 A.
    legacy=Parameters(); baseline=simulate(640,1000,25000,p=legacy,
        K=design(788,5000,legacy),duration=.02,keep_trace=True)
    baseline.update(assess(baseline['t'],baseline['x'],.001,baseline['completed'],baseline['within_port_limits']))
    assert not baseline['requirements_pass'] and baseline['violations']['path_current']
    traces['baseline']=(baseline.pop('t'),baseline.pop('x')); baseline.pop('u')
    assert not next(r for r in rows if r['name']=='overload29_640')['requirements_pass']
    fine=run(640,dt=1e-7,keep_trace=True)
    convergence=float(np.max(np.abs(fine['x'][1::2,2]-traces['rated60_640'][1][:,2])))
    assert convergence<.05
    near_limit=run(640,plant=replace(NOMINAL,Lh=NOMINAL.Lh*.9),dt=1e-7)
    coarse=next(r for r in rows if r['name']=='tolerance_Lh_0.9_640')
    assert near_limit['requirements_pass']
    near_refinement=dict(coarse_path_peak_A=coarse['path_peak'],fine_path_peak_A=near_limit['path_peak'],
                         difference_A=abs(coarse['path_peak']-near_limit['path_peak']))
    summary={g:dict(total=sum(r['group']==g for r in rows),
                   passed=sum(r['group']==g and r['requirements_pass'] for r in rows))
             for g in ['nominal','outside_continuous_rating','tolerance','sensitivity']}
    data=dict(status='PASS: nominal requirements and expected failure regression checks',
              scope='One frozen gain; finite-link averaged plant; energized initial state; 20 ms',
              controller=dict(K=list(GAIN),parameters=asdict(NOMINAL),design_vbat=788,design_power=5000),
              summary=summary,timestep_halving_max_bus_difference_V=convergence,
              near_limit_refinement=near_refinement,baseline=baseline,cases=rows)
    (OUT/'python_results.json').write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')
    (OUT/'cases.json').write_text(json.dumps(inputs,indent=2,allow_nan=False),encoding='utf-8')
    fig,ax=plt.subplots(1,3,figsize=(13,3.8))
    for name,label in [('baseline','Previous common gain'),('rated60_640','New common gain, 640 V'),
                       ('rated60_920','New common gain, 920 V')]:
        t,x=traces[name]; sel=(t>=.0009)&(t<=.0025)
        for a,idx in zip(ax,[2,0,4],strict=True): a.plot(t[sel][::10]*1000,x[sel,idx][::10],label=label,lw=1)
    ax[0].axhline(392,color='red',ls='--'); ax[0].axhline(396,color='gray',ls=':',lw=.8)
    ax[1].axhline(100,color='red',ls='--')
    for a,label in zip(ax,['Bus voltage (V)','Path current (A)','Link voltage (V)'],strict=True):
        a.set_xlabel('Time (ms)'); a.set_ylabel(label); a.grid(alpha=.3)
    ax[0].legend(fontsize=7)
    fig.suptitle('Fixed controller: 1 to 25 kW CPL step (60 A equivalent at 400 V)')
    fig.tight_layout(); fig.savefig(OUT/'fixed_control.png',dpi=150); plt.close(fig)
    print(summary,flush=True)


if __name__=='__main__': main()
