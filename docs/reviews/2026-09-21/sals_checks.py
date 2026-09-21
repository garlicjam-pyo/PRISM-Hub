"""Independent SALS checks; writes audit results beside this script; leaves converter source unchanged."""
import importlib.util
import json
import pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(__file__).resolve().parents[3]

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / 'python' / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

tb = load('tb_s6_sals', 'tb_s6_sals.py')
mc = load('sals_montecarlo', 'sals_montecarlo.py')
out = {}

# All scenarios used by the repository Part B have time-separable objectives.
configs = [(0., 0., None), (-.2, .005, None), (-.2, .005, (.005, .25)), (0., -.005, (.005, .25))]
out['horizon_equivalence'] = []
for pe, te, robust in configs:
    _, a1 = tb.sals_schedule(tb.Loads(), H=1, pred_err=pe, t_err=te, robust=robust)
    _, a15 = tb.sals_schedule(tb.Loads(), H=15, pred_err=pe, t_err=te, robust=robust)
    out['horizon_equivalence'].append(dict(pe=pe, te=te, robust=robust,
        max_abs_difference_A=max(float(np.max(np.abs(a1[k]-a15[k]))) for k in a1)))
print('horizon', out['horizon_equivalence'], flush=True)

# A deterministic corner inside the advertised uncertainty bounds.
e = dict(Vbat=800., Imax=95., base=14.9, t_c=.05, d_c=.021,
         k_s=2.39, P_c=24.9, t_v=0., v2l=True,
         req={'PTC':(17.5,0.,1.), 'BH':(17.5,0.,.7), 'V48':(3.75,0.,.5)},
         p_loss=.19, seen_delay=.015, sus=np.zeros(mc.n))
names, allowed = mc.schedule(e)
result = mc.evaluate(e, names, allowed)
nd, env = mc.nondef(e, mc.tg), mc.envelope(e, mc.tg)
result.update(envelope_underbound_max_A=float(np.max(nd-env)),
              first_over_ms=float(mc.tg[np.flatnonzero(nd+allowed.sum(1)>100)[0]]*1000),
              time_over_ms=int(np.sum(nd+allowed.sum(1)>100)),
              interruption_ms={name:float(np.sum(allowed[:,j] < .99*e['req'][name][0])) for j,name in enumerate(names)})
out['admissible_late_CAN_counterexample'] = result
print('CAN corner', result, flush=True)

# Linear interpolation executes part of the next tick's action before it exists.
ld=tb.Loads()
L,Cs,Cb=1.5e-6,100e-6,400e-6
K=tb.design(L,Cs,Cb,8e3)
out['hold_comparison']={}
for tag, kwargs in [('perfect',{}),('robust',dict(pred_err=-.2,t_err=.005,robust=(.005,.25)))]:
    tg,al=tb.sals_schedule(ld,tend=.04,**kwargs)
    matrix=np.stack([al[k] for k in al],axis=1)
    for kind in ['linear','previous']:
        def iload(tt,vb):
            val=float(ld.nondef(np.array([tt]))[0])
            if kind=='linear':
                val+=sum(np.interp(tt,tg,al[k],left=0.,right=al[k][-1]) for k in al)
            else:
                i=np.clip(np.searchsorted(tg,tt,side='right')-1,0,len(tg)-1)
                val+=matrix[i].sum()
            return val*400/vb
        t,log,_=tb.sim_fast(K,L,Cs,Cb,iload,.04,Isat=100.,Kaw=.05,dt=.2e-6)
        metric=tb.metrics(t,log)
        metric={k:float(v) if isinstance(v,np.generic) else v for k,v in metric.items()}
        out['hold_comparison'][tag+'_'+kind]=metric
        print(tag,kind,metric,flush=True)

(HERE/'sals_checks_results.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
