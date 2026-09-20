"""SALS Monte Carlo (reduced-order): survival statistics of the worst-case-window LP scheduler vs no shaping vs reactive load dump.
Reduced-order survival criterion (from verified fast-scale results, App. C/D): the bus stays within spec if the shaped 400 V load current
never exceeds I_rated(100 A) - 5 A margin AND no single step exceeds 80 A (droop <= 6.3 V). Collapse if load > 100 A for > 0.4 ms.
Reactive load dump: when load > 100 A the bus dips (20 V/ms per 10 A deficit) to the trip level (388 V) in t_trip = 12 V/(2*(deficit)) ms,
then all deferrable loads shed after 1 ms: survives with a dip of ~ (deficit*(t_trip+1 ms)*2 V/ms/A) - recorded as dip depth.
Randomised per episode: V_bat U(640,920) V (headroom rule), compressor command time, delay U(20,200) ms, surge factor U(1.6,2.4),
steady compressor power U(6,10) kW, requests for PTC/battery heater/48 V lowprio at random times, V2L on/off, CAN loss up to 20 %
(signal seen late by U(0,30) ms with prob p_loss), base load U(10,15) A, suspension ±7.5 A random telegraph.
"""
import numpy as np, json
from scipy.optimize import linprog
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"; rng=np.random.default_rng(7)
Tc=1e-3; H=15; T=0.5; n=int(T/Tc); tg=np.arange(n)*Tc

def episode():
    e={}
    e["Vbat"]=rng.uniform(640,920); dV=abs(400-e["Vbat"]/2); e["Imax"]=min(95.,0.95*8e3/max(dV,1.0))
    e["base"]=rng.uniform(10,15); e["t_c"]=rng.uniform(0.05,0.25); e["d_c"]=rng.uniform(0.02,0.20); e["k_s"]=rng.uniform(1.6,2.4); e["P_c"]=rng.uniform(6,10)*1e3/400
    e["t_v"]=rng.uniform(0.0,0.4); e["v2l"]=rng.random()<0.5
    e["req"]={"PTC":(17.5,rng.uniform(0.0,0.3),1.0),"BH":(17.5,rng.uniform(0.0,0.3),0.7),"V48":(3.75,rng.uniform(0.0,0.3),0.5)}
    e["p_loss"]=rng.uniform(0,0.2); e["seen_delay"]=rng.uniform(0,0.03) if rng.random()<e["p_loss"] else 0.0
    F=np.zeros(n); f=0.
    for k in range(n):
        if rng.random()<0.02: f=rng.uniform(-1,1)
        F[k]=f
    sus=np.zeros(n); x=0.
    for k in range(n): x+=(Tc/0.005)*(F[k]-x); sus[k]=7.5*x
    e["sus"]=sus
    return e
def nondef(e,t):
    t=np.asarray(t,float); ts=e["t_c"]+e["d_c"]
    comp=np.where(t>=ts, np.where(t<ts+0.020, e["k_s"]*e["P_c"], e["P_c"]*(1-np.exp(-(t-ts-0.02)/0.05))),0.0)
    v2l=np.where((t>=e["t_v"]+0.005)&e["v2l"],9.0,0.0)
    return e["base"]+comp+v2l+np.interp(t,tg,e["sus"])
def envelope(e,t):
    """worst-case window as seen by SALS: compressor command observed at t_c+seen_delay; window [+20,+220] ms with 2.4x P_c (upper bound of surge factor);
       V2L request observed at t_v; suspension margin 7.5 A; base measured."""
    t=np.asarray(t,float); tc=e["t_c"]+e["seen_delay"]
    comp=np.where((t>=tc+0.02)&(t<tc+0.22),2.4*e["P_c"],np.where(t>=tc+0.22,e["P_c"],0.0))
    v2l=np.where((t>=e["t_v"])&e["v2l"],9.0,0.0)
    return e["base"]+comp+v2l+7.5
def schedule(e):
    names=list(e["req"]); J=len(names); al=np.zeros((n,J))
    for i,t0 in enumerate(tg):
        th=t0+np.arange(H)*Tc; nd=envelope(e,th)
        c=np.zeros(H*J); bounds=[]
        for k in range(H):
            for j,nm in enumerate(names):
                req,tr,w=e["req"][nm]; r=req if th[k]>=tr else 0.0; c[k*J+j]=-w*(1+0.02*k); bounds.append((0.,r))
        A=np.zeros((H,H*J)); b=e["Imax"]-nd
        for k in range(H): A[k,k*J:(k+1)*J]=1.0
        res=linprog(c,A_ub=A,b_ub=b,bounds=bounds,method="highs"); u=res.x if res.success else np.zeros(H*J)
        al[i]=u[:J]
    return names,al
def evaluate(e,names,al):
    nd=nondef(e,tg); tot=nd+al.sum(1); Irate=100.
    over=tot>Irate; collapse=bool(np.any(np.convolve(over.astype(float),np.ones(1),mode="same")>0))   # any ms above rating -> deficit persists >=1 ms > 0.4 ms
    steps=np.diff(tot,prepend=tot[0]); maxstep=float(steps.max())
    # deferral: time from request to full allowance
    defer={}
    for j,nm in enumerate(names):
        req,tr,w=e["req"][nm]; idx=np.where((tg>=tr)&(al[:,j]>=0.99*req))[0]
        defer[nm]=float((tg[idx[0]]-tr)*1e3) if len(idx) else float((T-tr)*1e3)
    return dict(collapse=collapse,peak=float(tot.max()),maxstep=maxstep,defer=defer)
def evaluate_noshape(e):
    nd=nondef(e,tg); tot=nd+sum(req*(tg>=tr) for req,tr,w in e["req"].values()); return dict(collapse=bool(np.any(tot>100.)),peak=float(tot.max()))
def evaluate_reactive(e):
    nd=nondef(e,tg); tot=nd+sum(req*(tg>=tr) for req,tr,w in e["req"].values()); over=np.where(tot>100.)[0]
    if not len(over): return dict(collapse=False,dip=0.0)
    k=over[0]; deficit=tot[k]-100.; rate=2.0*deficit          # V/ms  (500 uF: 10 A -> 20 V/ms)
    t_trip=12.0/rate; dip=rate*(t_trip+1.0)                      # dip at shed time (trip 388 V + 1 ms actuation)
    return dict(collapse=bool(dip>300),dip=float(dip))
if __name__=="__main__":
    N=300; R={"sals":[],"none":[],"react":[]}
    for i in range(N):
        e=episode(); names,al=schedule(e); R["sals"].append(evaluate(e,names,al)); R["none"].append(evaluate_noshape(e)); R["react"].append(evaluate_reactive(e))
    s=R["sals"]; nn=R["none"]; rr=R["react"]
    print(f"episodes {N}: events exceeding 100 A without shaping: {sum(x['collapse'] for x in nn)} ({sum(x['collapse'] for x in nn)/N*100:.0f} %)")
    print(f"SALS: collapse {sum(x['collapse'] for x in s)} / {N}, peak max {max(x['peak'] for x in s):.1f} A, max single step {max(x['maxstep'] for x in s):.1f} A")
    for nm in ["PTC","BH","V48"]:
        d=[x["defer"][nm] for x in s]; print(f"  deferral {nm}: median {np.median(d):.0f} ms, 95th {np.percentile(d,95):.0f} ms, max {max(d):.0f} ms")
    dips=[x["dip"] for x in rr if x["dip"]>0]; print(f"reactive: dips in {len(dips)} events, median dip {np.median(dips):.0f} V, max {max(dips):.0f} V, collapses {sum(x['collapse'] for x in rr)}")
    out=dict(N=N,none_exceed=sum(x['collapse'] for x in nn),sals_collapse=sum(x['collapse'] for x in s),sals_peak_max=max(x['peak'] for x in s),
             defer={nm:dict(median=float(np.median([x['defer'][nm] for x in s])),p95=float(np.percentile([x['defer'][nm] for x in s],95)),max=float(max(x['defer'][nm] for x in s))) for nm in ["PTC","BH","V48"]},
             reactive=dict(n_dip=len(dips),median_dip=float(np.median(dips)) if dips else 0,max_dip=float(max(dips)) if dips else 0,collapse=sum(x['collapse'] for x in rr)))
    json.dump(out,open("results/sals_montecarlo.json","w"),indent=1)
    fig,ax=plt.subplots(1,2,figsize=(10,3.6))
    ax[0].hist([x["peak"] for x in nn],bins=30,alpha=0.6,label="no shaping"); ax[0].hist([x["peak"] for x in s],bins=30,alpha=0.6,label="SALS window rule"); ax[0].axvline(100,color="r",ls="--"); ax[0].set_xlabel("peak 400 V load current (A)"); ax[0].legend(fontsize=8); ax[0].grid(True)
    ax[1].hist([x["defer"]["BH"] for x in s],bins=30,alpha=0.7,label="battery heater deferral"); ax[1].hist([x["defer"]["PTC"] for x in s],bins=30,alpha=0.7,label="cabin PTC deferral"); ax[1].set_xlabel("deferral (ms)"); ax[1].legend(fontsize=8); ax[1].grid(True)
    fig.suptitle(f"SALS Monte Carlo, {N} episodes (V_bat 640–920 V, delay 20–200 ms, surge 1.6–2.4x, CAN loss ≤ 20 %)"); fig.tight_layout(); fig.savefig(f"{FIG}/sals_montecarlo.png",dpi=140); plt.close(fig)
