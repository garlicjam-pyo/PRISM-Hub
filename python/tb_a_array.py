"""Stage A array-level switching model (vectorized over N phases).
Each phase k: states iC[k], vC[k]; shared bus: Vbus.  Optional input resistor R_in (precharge) and
per-phase parameter tolerance.  Timing: fixed period T (common), phase offsets; conduction ends either
at scheduled time (fixed mode) or at zero-crossing detection (zc mode, detection delay td_det).
Phase1 (charge): L diC/dt = Vin_eff - Vbus - vC - iC*R ; input current = iC
Phase2 (discharge): L diC/dt = Vbus - vC - iC*R ; input current 0
Dead: diode freewheel/regen as before; blocked when crossing zero.
Bus: Cbus dVbus/dt = sum(iout_k) - Iload  ; Vin_eff = Vbat - R_in*sum(iin_k)
"""
import numpy as np, json, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"

BASE=dict(Cfly=7.8125e-6, Lr=1.441e-7, Rds=6e-3, ESR=1.5e-3, RL=1e-3, Rmisc=1.5e-3, Vf=0.9,
          Eoss=24e-6, Qg_E=2e-6, tdead=100e-9)
fr0=1/(2*np.pi*np.sqrt(BASE["Lr"]*BASE["Cfly"]))

def sim_array(N=8, Vbat=788., Iload=375., Cbus=400e-6, fratio=0.98, mode="fixed", tol=None, seed=0,
              R_in=0.0, C_in=100e-6, ncyc=60, Nstep=340, vC0=None, Vbus0=None, td_det=20e-9, en=None, i_thr=0.5):
    rng=np.random.default_rng(seed)
    C=np.full(N,BASE["Cfly"]); L=np.full(N,BASE["Lr"]); R=np.full(N,2*BASE["Rds"]+BASE["ESR"]+BASE["RL"]+BASE["Rmisc"])
    if tol:
        C*=1+rng.uniform(-tol["C"],tol["C"],N); L*=1+rng.uniform(-tol["L"],tol["L"],N); R*=1+rng.uniform(-tol["R"],tol["R"],N)
    en=np.ones(N,bool) if en is None else np.array(en,bool)
    Vf=BASE["Vf"]; td=BASE["tdead"]
    fs=fratio*fr0; T=1/fs; dt=T/Nstep; n=ncyc*Nstep; ndead=int(round(td/dt)); half=Nstep//2
    ndet=int(round(td_det/dt))
    off=(np.arange(N)*Nstep/(N)/1.0)   # interleave: 180deg/N spacing in half-period units -> T/(2N)? use T/N *0.5
    off=np.round(np.arange(N)*(Nstep/2)/N).astype(int)  # 22.5 deg for N=8 (of 360) == T/(2N)
    Vo0=Vbat/2
    iC=np.zeros(N); vC=np.full(N,Vo0) if vC0 is None else np.full(N,float(vC0)); Vb=Vo0 if Vbus0 is None else float(Vbus0)
    Vin=float(Vbat) if R_in==0 else 0.0   # input cap voltage (precharge starts at 0)
    # per-phase adaptive state
    forced_off=np.zeros(N,bool); det_cnt=np.zeros(N,int); armed=np.zeros(N,bool)
    # self-oscillating (zcp): per-phase state machine: ph_state 1/2 conducting, 0 dead; timer counts steps in dead; max on-time guard
    ph_state=np.zeros(N,int); ph_next=np.ones(N,int); ph_timer=np.zeros(N,int); on_cnt=np.zeros(N,int)
    ph_timer=-off.copy()              # stagger start by interleave offsets
    t_on_nom=0.5/fr0*(1-2*td*fr0)
    min_on=int(round(0.80*t_on_nom/dt)); max_on=int(round(1.12*t_on_nom/dt))   # ZC window [0.80,1.12] x nominal (blanking + guard)
    log_i=np.zeros((n,N),np.float32); log_v=np.zeros((n,N),np.float32); log_vb=np.zeros(n,np.float32); log_st=np.zeros((n,N),np.int8); log_io=np.zeros((n,N),np.float32); log_iin=np.zeros(n,np.float32)
    def sched(k):
        m=(k-off)%Nstep
        s=np.where(m<half, np.where(m>=ndead,1,0), np.where((m-half)>=ndead,2,0))
        newhalf=(m==0)|(m==half)
        return s,newhalf
    def deriv(iC,vC,Vb,s,Vin_eff):
        di=np.where(s==1,(Vin_eff-Vb-vC-iC*R)/L, np.where(s==2,(Vb-vC-iC*R)/L,
             np.where(iC>1e-3,(-vC-iC*R-2*Vf)/L, np.where(iC<-1e-3,(Vin_eff-vC-iC*R+2*Vf)/L,0.0))))
        io=np.where(s==1,iC,np.where(s==2,-iC,0.0))
        iin=np.where(s==1,iC,np.where((s==0)&(iC<-1e-3),-iC,0.0))
        return di, iC/C, io, iin
    for k in range(n):
        s,newhalf=sched(k)
        if mode=="zc":
            forced_off[newhalf]=False; armed[newhalf]=False; det_cnt[newhalf]=0
            armed|= (s!=0)&(np.abs(iC)>i_thr*5)          # current has built up
            # detect crossing: current sign opposite to conduction direction
            cross=(s!=0)&armed&(((s==1)&(iC<i_thr))|((s==2)&(iC>-i_thr)))
            det_cnt=np.where(cross,det_cnt+1,det_cnt)
            forced_off|= cross&(det_cnt>ndet)
            s=np.where(forced_off,0,s)
        if mode=="zcp":
            # dead timer / start
            start=(ph_state==0)&(ph_timer>=ndead)
            ph_state=np.where(start,ph_next,ph_state); ph_next=np.where(start,3-ph_next,ph_next)
            armed=np.where(start,False,armed); det_cnt=np.where(start,0,det_cnt); on_cnt=np.where(start,0,on_cnt)
            ph_timer=np.where(start,0,ph_timer)
            armed|=(ph_state!=0)&(np.abs(iC)>i_thr*5)
            cross=(ph_state!=0)&armed&(((ph_state==1)&(iC<i_thr))|((ph_state==2)&(iC>-i_thr)))
            det_cnt=np.where(cross,det_cnt+1,det_cnt); on_cnt=np.where(ph_state!=0,on_cnt+1,on_cnt)
            stop=(ph_state!=0)&(((on_cnt>=min_on)&cross&(det_cnt>ndet))|(on_cnt>=max_on))
            ph_state=np.where(stop,0,ph_state); ph_timer=np.where(stop,0,ph_timer)
            ph_timer=np.where(ph_state==0,ph_timer+1,ph_timer)
            s=ph_state.copy()
        s=np.where(en,s,0)
        Vin_eff=Vin
        # RK4 (Vin held over step; input cap updated after)
        def f(iC,vC,Vb):
            di,dv,io,iin=deriv(iC,vC,Vb,s,Vin_eff); return di,dv,(io.sum()-Iload)/Cbus,io,iin
        k1=f(iC,vC,Vb); k2=f(iC+0.5*dt*k1[0],vC+0.5*dt*k1[1],Vb+0.5*dt*k1[2])
        k3=f(iC+0.5*dt*k2[0],vC+0.5*dt*k2[1],Vb+0.5*dt*k2[2]); k4=f(iC+dt*k3[0],vC+dt*k3[1],Vb+dt*k3[2])
        log_i[k]=iC; log_v[k]=vC; log_vb[k]=Vb; log_st[k]=s; log_io[k]=k1[3]; log_iin[k]=k1[4].sum()
        iCn=iC+dt/6*(k1[0]+2*k2[0]+2*k3[0]+k4[0]); vC=vC+dt/6*(k1[1]+2*k2[1]+2*k3[1]+k4[1]); Vb=Vb+dt/6*(k1[2]+2*k2[2]+2*k3[2]+k4[2])
        blk=(s==0)&(iCn*iC<=0); iCn[blk]=0.0
        iC=iCn
        if R_in>0: Vin=Vin+dt*((Vbat-Vin)/R_in-k1[4].sum())/C_in
    t=np.arange(n)*dt
    return dict(t=t,i=log_i,v=log_v,vb=log_vb,st=log_st,io=log_io,iin=log_iin,fs=fs,T=T,C=C,L=L,R=R,dt=dt,N=N,Iload=Iload,Vbat=Vbat,Vin_end=Vin)

def analyze(r, ncyc_last=10):
    T=r["T"]; m=r["t"]>=r["t"][-1]-ncyc_last*T
    i=r["i"][m]; st=r["st"][m]; vb=r["vb"][m]; io=r["io"][m]
    N=r["N"]; out=[]
    for k in range(N):
        s=st[:,k]; ik=i[:,k]
        tr=np.where(np.diff(s)!=0)[0]
        offk=[j for j in tr if s[j]!=0 and s[j+1]==0]
        Ipk=np.max(np.abs(ik)); ioff=np.max(np.abs(ik[offk])) if offk else 0.0
        fr_k=1/(2*np.pi*np.sqrt(r["L"][k]*r["C"][k]))
        Rk=r["R"][k]
        onk=[j for j in tr if s[j]==0 and s[j+1]==1]
        fs_k=1/(np.mean(np.diff(np.array(onk)))*r["dt"]) if len(onk)>2 else r["fs"]
        Pcond=np.mean(ik**2)*Rk; Pdiode=np.mean(np.where(s==0,2*BASE["Vf"]*np.abs(ik),0.0)); Pcoss=4*BASE["Eoss"]*fs_k; Pg=4*BASE["Qg_E"]*fs_k
        out.append(dict(Ipk=Ipk,ioff=ioff,zcs=ioff/Ipk if Ipk>0 else 0,Iavg=np.mean(io[:,k]),fr_ratio=fs_k/fr_k,fs=fs_k,Ploss=Pcond+Pdiode+Pcoss+Pg,swing=np.ptp(r["v"][m][:,k])))
    return out, dict(Vbus=np.mean(vb), Vbus_ripple=np.ptp(vb), Iout=np.mean(io.sum(1)))

import sys
if __name__=="__main__":
    stage=sys.argv[1] if len(sys.argv)>1 else "all"
    rp="results/stageA_array_results.json"
    res=json.load(open(rp)) if os.path.exists(rp) else {}
    if stage in ("all","mc"):
        mc={"fixed":[],"zc":[],"zcp":[]}
        for seed in range(20):
            for mode,fr_ in [("fixed",0.98),("zc",0.90),("zcp",1.0)]:
                r=sim_array(N=1,Iload=46.875,fratio=fr_,mode=mode,tol=dict(C=0.05,L=0.10,R=0.10),seed=seed,ncyc=50); a,_=analyze(r)
                mc[mode].append((float(a[0]["fr_ratio"]),float(a[0]["zcs"]),float(a[0]["Ploss"]),float(a[0]["Ipk"])))
        for mode in mc:
            arr=np.array(mc[mode]); print(mode,"fs/fr_actual range",arr[:,0].min().round(3),arr[:,0].max().round(3),"ZCS max %.1f%% mean %.1f%%"%(arr[:,1].max()*100,arr[:,1].mean()*100),"Ploss max %.1f mean %.1f"%(arr[:,2].max(),arr[:,2].mean()), "n_fail(>5%)",int((arr[:,1]>0.05).sum()))
        res["mc"]=mc
        fig,ax=plt.subplots(figsize=(6,3.6))
        lab={"fixed":"fixed fs=0.98 fr0","zc":"ZC turn-off, fixed T (fs=0.90 fr0)","zcp":"self-oscillating (per-phase ZC period)"}
        for mode,c in [("fixed","C3"),("zc","C1"),("zcp","C0")]:
            arr=np.array(mc[mode]); ax.scatter(arr[:,0],arr[:,1]*100,label=lab[mode],color=c)
        ax.axhline(5,color="k",ls="--"); ax.set_xlabel("fs / fr,actual (tolerance draw)"); ax.set_ylabel("|i_off|/Ipk (%)"); ax.grid(True); ax.legend(fontsize=8); ax.set_title("WP3-1: Monte Carlo C±5%, L±10%, R±10% (20 draws)")
        fig.tight_layout(); fig.savefig(f"{FIG}/wp31_montecarlo.png",dpi=140); plt.close(fig)
    if stage in ("all","a2"):
        r=sim_array(N=8,Iload=375.,fratio=1.0,mode="zcp",tol=dict(C=0.10,L=0.10,R=0.10),seed=3,ncyc=60)
        a,b=analyze(r)
        Iav=np.array([x["Iavg"] for x in a]); mod=Iav.reshape(4,2).sum(1)
        print("TB-A2 array: bus",b, "phase Iavg",Iav.round(1),"module",mod.round(1),"dev % (module)",((mod-mod.mean())/mod.mean()*100).round(1),"zcs max %.1f%%"%(max(x["zcs"] for x in a)*100),"Ploss total %.0f W"%sum(x["Ploss"] for x in a))
        print("   R draw (mOhm):",(r["R"]*1e3).round(2),"phase dev %:",((Iav-Iav.mean())/Iav.mean()*100).round(1))
        res["tba2"]=dict(Vbus=float(b["Vbus"]),ripple=float(b["Vbus_ripple"]),Iavg=Iav.tolist(),mod=mod.tolist(),zcs=[float(x["zcs"]) for x in a],Ploss=[float(x["Ploss"]) for x in a],R=r["R"].tolist(),C=r["C"].tolist(),L=r["L"].tolist())
        m=r["t"]>=r["t"][-1]-2*r["T"]
        fig,ax=plt.subplots(2,1,figsize=(8,5),sharex=True)
        ax[0].plot((r["t"][m]-r["t"][m][0])*1e6,r["io"][m]); ax[0].set_ylabel("phase i_out (A)"); ax[0].grid(True)
        ax[1].plot((r["t"][m]-r["t"][m][0])*1e6,r["vb"][m]); ax[1].set_ylabel("V_bus (V)"); ax[1].set_xlabel("t (us)"); ax[1].grid(True)
        ax[0].set_title("TB-A2: 8-phase array, 375 A, tolerance ±10 %, self-oscillating ZC timing")
        fig.tight_layout(); fig.savefig(f"{FIG}/tba2_array.png",dpi=140); plt.close(fig)
    if stage in ("all","a3"):
        r=sim_array(N=8,Iload=0.0,fratio=1.0,mode="zcp",R_in=20.0,vC0=0.0,Vbus0=0.0,ncyc=2300,Nstep=170)
        ipk=np.max(np.abs(r["i"])); hit=np.where(r["vb"]>=0.95*394)[0]; t95=r["t"][hit[0]] if len(hit) else None
        print("TB-A3 precharge: peak phase current %.1f A, t95 = %s ms, final Vbus %.1f, vC %.1f"%(ipk, None if t95 is None else round(t95*1e3,2), r["vb"][-1], r["v"][-1].mean()))
        res["tba3"]=dict(ipk=float(ipk),t95=None if t95 is None else float(t95),Vbus_end=float(r["vb"][-1]))
        fig,ax=plt.subplots(2,1,figsize=(8,5),sharex=True)
        ax[0].plot(r["t"]*1e3,r["vb"],label="V_bus"); ax[0].plot(r["t"]*1e3,r["v"][:,0],label="v_Cfly (phase 1)"); ax[0].legend(); ax[0].grid(True); ax[0].set_ylabel("V")
        ax[1].plot(r["t"]*1e3,np.abs(r["i"]).max(1)); ax[1].set_ylabel("max |i_C| (A)"); ax[1].set_xlabel("t (ms)"); ax[1].grid(True)
        ax[0].set_title("TB-A3: precharge through 20 Ω, converter switching, no load")
        fig.tight_layout(); fig.savefig(f"{FIG}/tba3_precharge.png",dpi=140); plt.close(fig)
        r=sim_array(N=8,Iload=0.0,fratio=0.95,mode="fixed",R_in=0.0,vC0=0.0,Vbus0=0.0,ncyc=3,Nstep=340)
        print("TB-A3 no precharge peak current %.0f A"%np.max(np.abs(r["i"])))
        res["tba3_nopre_peak"]=float(np.max(np.abs(r["i"])))
    if stage in ("all","a4"):
        for en,name in [([1,1,0,0,0,0,0,0],"1module"),([1]*8,"all")]:
            r=sim_array(N=8,Iload=7.5,fratio=1.0,mode="zcp",en=en,ncyc=40); a,b=analyze(r)
            Pl=sum(x["Ploss"] for x,e in zip(a,en) if e); print(f"TB-A4 3 kW {name}: loss {Pl:.1f} W, eta {3e3/(3e3+Pl)*100:.2f} %, Vbus {b['Vbus']:.1f}")
            res[f"tba4_{name}"]=float(Pl)
    json.dump(res,open(rp,"w"),indent=1,default=float)
