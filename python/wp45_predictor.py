"""WP4.5  SALS predictor: interval (quantile) prediction of non-deferrable 400 V load current from vehicle anticipatory signals.
Data: synthetic episodes (1 ms). Signals: compressor rpm command (0/1 + target kW), PTC duty command (deferrable -> excluded from target),
V2L enable, suspension force command (48 V regen/consumption, ±), measured load current history.
Physics: compressor power follows command after random delay d_c ~ U(20,200) ms with 2x surge for 20 ms then ramp tau 50 ms;
V2L after 5 ms; suspension power = k*force with 2nd-order 5 ms response; CAN: signals sampled every 10 ms, delayed U(1,5) ms, 2 % loss (hold last).
Target: non-deferrable current at t+h for h in {5,10,15} ms.  Model: sklearn GradientBoostingRegressor with quantile loss (0.5, 0.9).
Closed loop: the 0.9-quantile profile feeds the LP scheduler (tb_s6_sals) in place of the hand-made robust bound.
"""
import numpy as np, json, time
from sklearn.ensemble import GradientBoostingRegressor
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"; rng=np.random.default_rng(1)

def episode(T=0.6, dt=1e-3):
    n=int(T/dt); t=np.arange(n)*dt
    base=12.5+rng.uniform(-2,4)
    # compressor
    t_c=rng.uniform(0.05,0.35); d_c=rng.uniform(0.02,0.20); P_c=rng.uniform(4,10)*1e3/400; surge=rng.uniform(1.6,2.2)
    comp=np.where(t>=t_c+d_c, np.where(t<t_c+d_c+0.020, surge*P_c, P_c*(1-np.exp(-(t-t_c-d_c-0.02)/0.05))),0.0)
    cmd_c=(t>=t_c).astype(float); tgt_c=cmd_c*P_c
    # V2L
    t_v=rng.uniform(0.0,0.5); on_v=rng.random()<0.5; v2l=np.where((t>=t_v+0.005)&on_v,9.0,0.0); cmd_v=((t>=t_v)&on_v).astype(float)
    # suspension (48 V, appears on 400 V bus via Stage C): force command random telegraph +-, power ±3 kW -> ±7.5 A, 2nd order 5 ms
    F=np.zeros(n); f=0.
    for k in range(n):
        if rng.random()<0.02: f=rng.uniform(-1,1)
        F[k]=f
    sus=np.zeros(n); x1=0.
    for k in range(n):
        x1+=(dt/0.005)*(F[k]-x1); sus[k]=7.5*x1     # 1st-order 5 ms actuator response
    nondef=base+comp+v2l+sus
    # CAN model: sample-hold 10 ms, delay 1-5 ms, 2 % loss
    def can(sig):
        out=np.zeros(n); last=0.; dly=int(rng.uniform(1,5))
        for k in range(n):
            if k%10==0 and rng.random()>0.02: last=sig[max(0,k-dly)]
            out[k]=last
        return out
    sig=np.stack([can(cmd_c),can(tgt_c),can(cmd_v),can(F)],1)
    # time since compressor command (as seen on CAN)
    seen=np.maximum.accumulate(sig[:,0]); tsc=np.zeros(n); c=0.
    for k in range(n):
        c = c+dt if seen[k]>0 else 0.; tsc[k]=c
    return t,nondef,sig,tsc

def build(n_ep, H=(5,10,15), W=20):
    X=[];Y=[]
    for _ in range(n_ep):
        t,nd,sig,tsc=episode(); n=len(t)
        for k in range(W,n-max(H)):
            feat=np.concatenate([nd[k-W:k], sig[k], [tsc[k]]])
            X.append(feat); Y.append([nd[k+h] for h in H])
    return np.array(X),np.array(Y)

if __name__=="__main__":
    out={}; t0=time.time()
    Xtr,Ytr=build(80); Xte,Yte=build(30)
    print(f"dataset: train {Xtr.shape}, test {Xte.shape}, gen {time.time()-t0:.0f} s")
    H=(5,10,15); models={}
    for j,h in enumerate(H):
        for q in [0.5,0.9]:
            m=GradientBoostingRegressor(loss="quantile",alpha=q,n_estimators=60,max_depth=3,learning_rate=0.12,subsample=0.5)
            m.fit(Xtr,Ytr[:,j]); models[(h,q)]=m
            p=m.predict(Xte); err=p-Yte[:,j]
            if q==0.5: print(f"h={h} ms median: MAE {np.abs(err).mean():.2f} A, RMSE {np.sqrt((err**2).mean()):.2f} A, under-prediction (>5 A) rate {(err<-5).mean()*100:.1f} %")
            else: print(f"h={h} ms q0.9: coverage {(p>=Yte[:,j]).mean()*100:.1f} %, mean margin {err.mean():.2f} A, max under-prediction {(-err).max():.1f} A")
            out[f"h{h}_q{q}"]=dict(mae=float(np.abs(err).mean()),coverage=float((p>=Yte[:,j]).mean()),mean_margin=float(err.mean()),max_under=float((-err).max()))
    # naive baseline (persistence): predict current value
    for j,h in enumerate(H):
        pers=Xte[:,19]; err=pers-Yte[:,j]; print(f"h={h} persistence MAE {np.abs(err).mean():.2f} A, under>5A rate {(err<-5).mean()*100:.1f} %")
        out[f"h{h}_persistence_mae"]=float(np.abs(err).mean())
    # example episode plot
    t,nd,sig,tsc=episode(); W=20; n=len(t)
    pred={h:np.full(n,np.nan) for h in H}; up={h:np.full(n,np.nan) for h in H}
    for k in range(W,n-15):
        feat=np.concatenate([nd[k-W:k],sig[k],[tsc[k]]])[None,:]
        for h in H: pred[h][k+h]=models[(h,0.5)].predict(feat)[0]; up[h][k+h]=models[(h,0.9)].predict(feat)[0]
    fig,ax=plt.subplots(figsize=(9,3.8))
    ax.plot(t*1e3,nd,"k",label="actual non-deferrable load (A)"); ax.plot(t*1e3,pred[10],"C0",label="median prediction, h=10 ms"); ax.plot(t*1e3,up[10],"C3--",label="90 % upper bound, h=10 ms")
    ax.plot(t*1e3,sig[:,0]*20,"gray",alpha=0.5,label="compressor command (CAN, scaled)"); ax.set_xlabel("t (ms)"); ax.set_ylabel("A"); ax.grid(True); ax.legend(fontsize=8); ax.set_title("WP4.5: quantile GBM predictor on a test episode")
    fig.tight_layout(); fig.savefig(f"{FIG}/wp45_predictor.png",dpi=140); plt.close(fig)
    # ---------- closed loop: use q0.9 profile (h=5/10/15 interpolated) in the SALS LP on the cold-start scenario of tb_s6
    exec(open("tb_s6_sals.py").read().split('if __name__=="__main__":')[0])
    ld=Loads()   # cold start: compressor command at 5 ms, actual surge at 5 ms (delay 0 -> harder than training which had 20-200 ms; use command issued 20 ms earlier to be consistent)
    ld.t_c=0.025   # compressor power at 25 ms; command seen at 5 ms (delay 20 ms = lower edge of training distribution)
    for nm in ld.deferrable: ld.deferrable[nm]["t"]=0.006
    tend=0.10; Tc=1e-3; tg=np.arange(0,tend,Tc); names=list(ld.deferrable); J=len(names); allowed={nm:np.zeros(len(tg)) for nm in names}
    hist=np.full(20,12.5)
    for i,t0_ in enumerate(tg):
        # features at t0: history of actual nondef (measured), CAN signals: compressor cmd since 5 ms with target 25 A, v2l cmd at 4 ms
        cmd_c=1.0 if t0_>=0.005 else 0.0; tsc=max(0.,t0_-0.005) if cmd_c else 0.; feat=np.concatenate([hist,[cmd_c,25.0*cmd_c,1.0 if t0_>=0.004 else 0.0,0.0],[tsc]])[None,:]
        q90=np.array([models[(h,0.9)].predict(feat)[0] for h in H]); nd_pred=np.interp(np.arange(15)+1,H,q90)*1.05   # +5 % margin
        c=np.zeros(15*J); bounds=[]
        for k in range(15):
            for j,nm in enumerate(names):
                dj=ld.deferrable[nm]; req=dj["req"] if t0_+k*Tc>=dj["t"] else 0.0; c[k*J+j]=-dj["w"]*(1+0.02*k); bounds.append((0.,req))
        A_ub=np.zeros((15,15*J)); b_ub=95.-nd_pred
        for k in range(15): A_ub[k,k*J:(k+1)*J]=1.0
        res=linprog(c,A_ub=A_ub,b_ub=b_ub,bounds=bounds,method="highs"); u=res.x if res.success else np.zeros(15*J)
        for j,nm in enumerate(names): allowed[nm][i]=u[j]
        hist=np.roll(hist,-1); hist[-1]=ld.nondef(np.array([t0_]))[0]
    def iload(tt,vb):
        i=ld.nondef(np.array([tt]))[0]
        for nm,dj in ld.deferrable.items(): i+=np.interp(tt,tg,allowed[nm],left=0.,right=allowed[nm][-1])
        return i*400./vb
    L=1.5e-6; Cs=100e-6; Cb=400e-6; K=design(L,Cs,Cb,8e3)
    t,log,_=sim_fast(K,L,Cs,Cb,iload,tend,Isat=100.,Kaw=0.05,dt=0.2e-6); m=metrics(t,log,0.0)
    print("closed loop with learned q0.9 predictor:",{k:round(float(v),1) if not isinstance(v,bool) else v for k,v in m.items()})
    out["closed_loop_q90"]=m
    # same event without shaping
    t,log2,_=sim_fast(K,L,Cs,Cb,lambda tt,vb:(ld.nondef(np.array([tt]))[0]+sum(dj["req"]*(tt>=dj["t"]) for dj in ld.deferrable.values()))*400./vb,tend,Isat=100.,Kaw=0.05,dt=0.2e-6); m2=metrics(t,log2,0.0)
    print("same event, no shaping:",{k:round(float(v),1) if not isinstance(v,bool) else v for k,v in m2.items()}); out["closed_loop_noshaping"]=m2
    fig,ax=plt.subplots(2,1,figsize=(9,5.5),sharex=True)
    ax[0].plot(t*1e3,log[:,3],label="load current, learned-predictor SALS"); ax[0].plot(t*1e3,log2[:,3],label="no shaping"); ax[0].axhline(100,color="r",ls="--"); ax[0].set_ylim(0,130); ax[0].set_ylabel("400 V load (A)"); ax[0].legend(fontsize=8); ax[0].grid(True)
    ax[1].plot(t*1e3,log[:,0],label="V_bus, learned-predictor SALS"); ax[1].plot(t*1e3,log2[:,0],label="V_bus, no shaping"); ax[1].axhspan(392,408,color="g",alpha=0.1); ax[1].set_ylim(300,420); ax[1].set_ylabel("V"); ax[1].set_xlabel("t (ms)"); ax[1].legend(fontsize=8); ax[1].grid(True)
    ax[0].set_title("WP4.5 closed loop: q0.9 GBM predictor -> LP scheduler, cold-start event (compressor cmd at 5 ms, surge at 25 ms)")
    fig.tight_layout(); fig.savefig(f"{FIG}/wp45_closed_loop.png",dpi=140); plt.close(fig)
    json.dump(out,open("results/wp45_predictor_results.json","w"),indent=1,default=float)
    print("total %.0f s"%(time.time()-t0))
