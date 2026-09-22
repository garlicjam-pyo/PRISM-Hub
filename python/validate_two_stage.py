"""Finite-link PPRC validation, including deliberately failing requirements.
Run from any working directory. Results never replace historical review data.
"""
from dataclasses import replace
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pprc_two_stage import (Parameters, equilibrium, rhs, energy_residual,
                            simulate, primary_power, steady_feasible, continuous_power_limit)

OUT=Path(__file__).resolve().parents[1]/'validation'/'2026-09-22-integration'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    p=Parameters(); steady=[]; max_balance=0.; max_rhs=0.
    for v in [640,648,788,800,907,920]:
        for power in [-5000,0,5000,25000]:
            x,u=equilibrium(v,power,p); dx=rhs(x,u,v,power,p)
            max_rhs=max(max_rhs,float(np.max(np.abs(dx))))
            link_power=x[4]*x[5]
            steady.append(dict(vbat=v,power=power,x=x.tolist(),u=u.tolist(),
                               dab_primary_power=primary_power(link_power,p),
                               feasible=steady_feasible(v,power,p)))
    rng=np.random.default_rng(71)
    for _ in range(1000):
        x=np.array([rng.uniform(-100,100),rng.uniform(-90,90),rng.uniform(360,420),
                    rng.uniform(-100,100),rng.uniform(90,110),rng.uniform(-80,80)])
        u=np.array([rng.uniform(-.95,.95),rng.uniform(-80,80)])
        v=rng.uniform(640,920); power=rng.uniform(-5000,30000)
        max_balance=max(max_balance,abs(energy_residual(x,rhs(x,u,v,power,p),v,power,p)))
    assert max_rhs<1e-5 and max_balance<1e-7
    cases=[]; traces={}
    specs=[(f'rated_{v}',v,5000,25000,p) for v in [640,648,788,907,920]]
    specs += [('unload_640',640,25000,5000,p),('unload_920',920,25000,5000,p),
              ('regeneration_640',640,5000,-5000,p),('regeneration_920',920,-5000,5000,p),
              ('zero_crossing_800',800,5000,-5000,p),
              ('overload_648',648,20000,36000,p),
              ('no_control_reserve_640',640,5000,25000,replace(p,reference_max=100))]
    for name,v,a,b,params in specs:
        r=simulate(v,a,b,params,keep_trace=True)
        traces[name]=(r.pop('t'),r.pop('x'),r.pop('u'))
        r['name']=name; cases.append(r)
        if name.startswith(('rated','unload','regeneration','zero_crossing')):
            assert r['completed'] and r['within_port_limits'] and r['voltage_quality_pass'],name
        print(name,round(r['droop'],3),round(r['path_peak'],3),r['within_port_limits'],r['voltage_quality_pass'],flush=True)
    assert not cases[-1]['within_port_limits'] and cases[-1]['voltage_quality_pass']
    assert not cases[-2]['within_port_limits'] and not cases[-2]['voltage_quality_pass']
    assert not steady_feasible(600,0,p) and continuous_power_limit(600,p)==0
    refined=simulate(640,dt=1e-7,keep_trace=True)
    # Midpoint integration convergence with identical sampled controls and delay.
    voltage_error=float(np.max(np.abs(refined['x'][1::2,2]-traces['rated_640'][1][:,2])))
    assert voltage_error<.05
    result=dict(scope='Finite-link averaged candidate; sampled grid, no hardware or switching proof',
                max_energy_residual_W=max_balance,max_equilibrium_derivative=max_rhs,
                timestep_halving_max_bus_difference_V=voltage_error,steady=steady,cases=cases,
                static_power_limit_W={str(v):continuous_power_limit(v,p) for v in [600,620,625,640,648,788,920]},
                status='PASS: regression checks, including expected engineering failures')
    (OUT/'two_stage_python.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    # MATLAB independently recomputes equilibrium and integrates the plant with these exact gains.
    inputs=[dict(name=r['name'],vbat=r['vbat'],power0=r['power0'],power1=r['power1'],
                 dt=r['dt'],duration=r['duration'],K=r['K'],parameters=r['parameters']) for r in cases]
    (OUT/'two_stage_cases.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(2,2,figsize=(11,7),sharex=True)
    for name,label in [('rated_640','640 V, 84 A reference'),('rated_920','920 V, 84 A reference'),
                       ('no_control_reserve_640','640 V, 100 A reference')]:
        t,x,u=traces[name]; keep=slice(None,None,25); ms=t[keep]*1000
        for ax,data in zip(axes.flat,[x[:,2],x[:,0],x[:,4],x[:,5]],strict=True):
            ax.plot(ms,data[keep],label=label,lw=1)
    axes[0,0].axhline(392,color='r',ls='--',lw=.8); axes[0,1].axhline(100,color='r',ls='--',lw=.8)
    axes[1,1].axhline(80,color='r',ls='--',lw=.8); axes[1,1].axhline(-80,color='r',ls='--',lw=.8)
    for ax,label in zip(axes.flat,['Bus voltage (V)','Path current (A)','Link voltage (V)','DAB link current (A)'],strict=True):
        ax.set_ylabel(label); ax.grid(alpha=.3); ax.set_xlim(.8,2.5)
    axes[0,0].legend(fontsize=7); axes[1,0].set_xlabel('Time (ms)'); axes[1,1].set_xlabel('Time (ms)')
    fig.suptitle('Two-stage averaged PPRC: 5 to 25 kW at 1 ms')
    fig.tight_layout(); fig.savefig(OUT/'two_stage.png',dpi=150); plt.close(fig)
    print(result['status'])


if __name__=='__main__': main()
