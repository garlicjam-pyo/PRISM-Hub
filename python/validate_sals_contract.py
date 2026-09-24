"""Reproduce a pre-observation counterexample and test explicit admission bounds."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import linprog
import sals_montecarlo as legacy
from sals_admission import admit


def main():
    # All within the bundle's stated delay and surge ranges. No future event
    # is available to the controller before t_obs=80 ms; surge starts at 70 ms.
    e=dict(Vbat=800.,Imax=95.,base=14.9,t_c=.050,d_c=.020,seen_delay=.030,
           k_s=2.39,P_c=24.9,t_v=0.,v2l=True,sus=np.zeros(legacy.n),
           req={'PTC':(17.5,.030,1.),'BH':(17.5,.030,.7),'V48':(3.75,.030,.5)})
    names,al=legacy.schedule(e)
    total=legacy.nondef(e,legacy.tg)+al.sum(axis=1)
    blind=(legacy.tg>=.070)&(legacy.tg<.080)
    peak=float(np.max(total[blind])); exceed_ms=float(np.sum(blind&(total>100))*legacy.Tc*1000)
    assert peak>120 and exceed_ms>=9
    static_budget=admit(800,0.,{},coverage_valid=True)['load_budget_A']
    budget_excess=peak-static_budget
    budget_exceed_ms=float(np.sum(blind&(total>static_budget))*legacy.Tc*1000)
    assert budget_excess>60 and budget_exceed_ms>=9
    requests={'PTC':(17.5,1.),'BH':(17.5,.7),'V48':(3.75,.5)}
    safe=admit(648,25.,requests,coverage_valid=True)
    assert safe['static_admission_feasible'] and abs(safe['load_budget_A']-59.375)<1e-9
    assert sum(safe['allowance_A'].values())+25<=safe['load_budget_A']+1e-9
    # A first-step LP has exactly this priority solution. No horizon claim.
    lp=linprog([-1,-.7,-.5],A_ub=[[1,1,1]],b_ub=[safe['load_budget_A']-25],
               bounds=[(0,17.5),(0,17.5),(0,3.75)],method='highs')
    assert lp.success and np.max(np.abs(lp.x-list(safe['allowance_A'].values())))<1e-9
    blind_action=admit(800,25.,requests,coverage_valid=False)
    assert not blind_action['static_admission_feasible'] and sum(blind_action['allowance_A'].values())==0
    mandatory_bound=14.9+2.4*24.9+9+7.5
    infeasible=admit(648,mandatory_bound,requests,coverage_valid=True)
    assert not infeasible['static_admission_feasible'] and infeasible['mandatory_deficit_A']>30
    # Service energy is integrated on the actual time grid, not first admission.
    requested=np.column_stack([req*(legacy.tg>=tr) for req,tr,w in e['req'].values()])
    unmet_A_ms=np.maximum(0,requested-al).sum(axis=0)*legacy.Tc*1000
    out=dict(status='PASS: counterexample detected and static-contract checks passed',
             historical_window_counterexample=dict(surge_start_ms=70,observed_ms=80,
                 peak_load_A=peak,over_100A_before_observation_ms=exceed_ms,
                 static_load_budget_A=static_budget,
                 peak_above_static_budget_A=budget_excess,
                 surge_interval_above_static_budget_ms=budget_exceed_ms,
                 unmet_demand_A_ms=dict(zip(names,map(float,unmet_A_ms)))),
             normal_admission=safe,missing_coverage=blind_action,
             mandatory_upper_A=mandatory_bound,mandatory_infeasible=infeasible,
             conclusion='The 122.161 A peak is aggregate 400 V load demand. During the pre-observation surge interval, it exceeds the 59.375 A static load budget by 62.786 A; it is not a calculated Stage B path current. Window anchoring alone cannot cover events before observation. Static admission cannot rescue mandatory demand above converter capacity; no voltage guarantee claimed.')
    folder=Path(__file__).resolve().parents[1]/'validation'/'2026-09-22-integration'
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'sals_contract.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))


if __name__=='__main__': main()
