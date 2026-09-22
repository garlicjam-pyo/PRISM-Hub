"""Scoped regression checks; historical review results remain unchanged."""
from pathlib import Path
import json
import numpy as np
from pprc_model import equilibrium, linearize, rhs, SPS_CURRENT_MAX
from tb_a_array import sim_array, analyze
from tb_s2_b3 import tb_s2
import tb_b_pprc2 as pprc


def main():
    out={'scope':'Ideal average model and Stage A ODE regressions; not hardware certification',
         'SPS_current_max':SPS_CURRENT_MAX}
    rows=[]
    for vbat in [648,788,907]:
        x=equilibrium(vbat,25000)
        assert np.max(np.abs(rhs(x,x[3],vbat,25000)))<1e-5
        y=x+np.array([3,-2,4,-1]); dy=rhs(y,10,vbat,27000)
        residual=abs(np.dot(y[:3]*[1.5e-6,100e-6,400e-6],dy[:3])-(vbat/2*y[0]-.0132*y[0]**2-27000))
        assert residual<1e-7
        rows.append(dict(Vbat=vbat,x=x.tolist(),energy_residual=residual))
    out['equilibrium']=rows
    x=equilibrium(788,5000); A,_=linearize(1.5e-6,100e-6,400e-6)
    J=np.column_stack([(rhs(x+e,x[3],788,5000)-rhs(x-e,x[3],788,5000))/(2e-4) for e in np.eye(4)*1e-4])
    assert np.max(np.abs(J-A[:4,:4]))<.01
    K=pprc.design(1.5e-6,100e-6,400e-6,8e3)
    r=pprc.simulate(K,1.5e-6,100e-6,400e-6,dI=0)
    assert np.max(np.abs(r['log'][:,0]-400))<1e-6
    out['step']=[]
    for vbat in [648.,788.,907.]:
        pprc.Vbat=vbat
        K=pprc.design(1.5e-6,100e-6,400e-6,8e3)
        r=pprc.simulate(K,1.5e-6,100e-6,400e-6)
        assert np.isfinite(r['log']).all()
        assert r['ipeak']<=SPS_CURRENT_MAX+1e-6
        quality=bool(r['droop']<=8 and abs(r['log'][-1,0]-400)<=4)
        out['step'].append(dict(Vbat=vbat,droop=float(r['droop']),vbus_end=float(r['log'][-1,0]),current_peak=float(r['ipeak']),within_port_limits=r['within_port_limits'],voltage_quality_pass=quality))
    pprc.Vbat=648.
    K=pprc.design(1.5e-6,100e-6,400e-6,8e3)
    r=pprc.simulate(K,1.5e-6,100e-6,400e-6,dI=50,tend=.008)
    assert r['within_port_limits'] and r['droop']<=8 and abs(r['log'][-1,0]-400)<=4
    out['rated_low_battery']=dict(droop=float(r['droop']),vbus_end=float(r['log'][-1,0]))
    assert not out['step'][0]['voltage_quality_pass']
    assert all(row['voltage_quality_pass'] for row in out['step'][1:])
    assert all(row['within_port_limits'] for row in out['step'])
    pprc.Vbat=788.
    out['stage_a']=[]
    for tol in [None,dict(C=.1,L=.1,R=.1)]:
        for direction in [1,-1]:
            r=sim_array(N=8,Iload=direction*375,fratio=1,mode='zcp',tol=tol,seed=3,ncyc=60)
            a,b=analyze(r); zcs=max(float(x['zcs']) for x in a)
            assert zcs<.05, zcs
            out['stage_a'].append(dict(direction=direction,tolerance=tol is not None,zcs_max=zcs,**{k:float(v) for k,v in b.items()}))
            print('Stage A',out['stage_a'][-1],flush=True)
    out['charger']=[]
    for soc in [.0,.5,.955]:
        r=tb_s2(SoC0=soc,tend=.15)
        peak=float(np.max(r['log'][:,1]*r['log'][:,2]))
        assert peak<=150000+1e-6
        assert np.max(r['log'][:,2])<=375+1e-6
        out['charger'].append(dict(SoC0=soc,peak_power_W=peak))
    full=tb_s2()
    peak=float(np.max(full['log'][:,1]*full['log'][:,2]))
    assert full['t_cv'] is not None and peak<=150000+1e-6
    out['charger_cc_cv']=dict(t_cv=float(full['t_cv']),peak_power_W=peak,voltage_max=float(np.max(full['log'][:,0])))
    out['status']='PASS: scoped regression assertions'
    folder=Path(__file__).resolve().parents[1]/'validation'/'2026-09-22'
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'python_results.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(out['status'])


if __name__=='__main__':
    main()
