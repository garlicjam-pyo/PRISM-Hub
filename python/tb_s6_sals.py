"""TB-S6  Saturation-aware control on the series PPRC path (drive mode, 1 module).
Part A: fast-scale — state feedback + integral with anti-windup (back-calculation) at s = 0.25, 0.5, 1.
Part B: slow-scale — SALS load shaping: receding-horizon LP (1 ms) schedules deferrable loads so that the
        predicted 400 V load current stays below the PPRC series-current headroom; the shaped load then
        drives the fast average model.  Compared with: no shaping (B0), and hardware alternative (PPRC 150 A).
"""
import numpy as np, json, scipy.signal as sg
from scipy.optimize import linprog
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"
Vbat=788.; R_A=10.2e-3; R_p=3e-3; tau=10e-6; d_dab=5e-6; Ts=5e-6; Vbus=400.

def design(L,Cs,Cb,f_bw,zeta=0.7):
    A=np.array([[-(R_A+R_p)/L,1/L,-1/L,0],[-1/Cs,0,0,1/Cs],[1/Cb,0,0,0],[0,0,0,-1/tau]]); B=np.array([[0],[0],[0],[1/tau]])
    Aa=np.zeros((5,5)); Aa[:4,:4]=A; Aa[4,2]=-1.0; Ba=np.zeros((5,1)); Ba[:4]=B
    w=2*np.pi*f_bw; poles=[-zeta*w+1j*w*np.sqrt(1-zeta**2),-zeta*w-1j*w*np.sqrt(1-zeta**2),-w,-w/3,-min(2.5*w,2*np.pi*30e3)]
    return sg.place_poles(Aa,Ba,np.array(poles)).gain_matrix[0]

def sim_fast(K,L,Cs,Cb,iload_fn,tend,Isat=100.,Kaw=0.0,dt=0.1e-6,P0=5e3,vref=400.):
    """iload_fn(t, vb) -> load current (A). Returns log [vb, ip, idab, iload]."""
    n=int(tend/dt); t=np.arange(n)*dt
    ip=P0/Vbus; vs=vref-(Vbat/2-R_A*ip); vb=vref; idab=ip
    x0=np.array([ip,vs,vb,idab]); q=-(ip+K[:4]@x0)/K[4]
    dbuf=np.zeros(int(d_dab/dt)+1)+ip; cmd_hold=ip; kc=int(Ts/dt)
    log=np.zeros((n,4)); sat_flag=False
    for k in range(n):
        tt=t[k]; il=iload_fn(tt,vb)
        if k%kc==0:
            x=np.array([ip,vs,vb,idab]); u_un=-K[:4]@x-K[4]*q
            u=np.clip(u_un,-Isat,Isat); cmd_hold=u
            q+=Ts*(vref-vb)+Kaw*(u-u_un)/(-K[4])   # back-calculation anti-windup (du/dq = -K[4])
            if abs(u_un)>Isat: sat_flag=True
        dbuf=np.roll(dbuf,1); dbuf[0]=cmd_hold; u=dbuf[-1]
        dip=(Vbat/2-(R_A+R_p)*ip+vs-vb)/L; dvs=(idab-ip)/Cs; dvb=(ip-il)/Cb; did=(u-idab)/tau
        ip+=dt*dip; vs+=dt*dvs; vb+=dt*dvb; idab+=dt*did
        if vb<50: vb=50.   # collapse floor (model validity)
        log[k]=(vb,ip,idab,il)
    return t,log,sat_flag

def metrics(t,log,t0=0.0):
    m=t>=t0; vb=log[m,0]; return dict(vmin=vb.min(),vmax=vb.max(),droop=Vbus-vb.min(),collapse=bool(vb.min()<360),
        outside2pct_us=float(np.sum(np.abs(vb-Vbus)>8)*(t[1]-t[0])*1e6))

# ------------------------------------------------------------------ Part A: anti-windup at small banks
def partA():
    out={}
    L=1.5e-6; step=lambda dI: (lambda tt,vb: (5e3+Vbus*dI*(tt>=0.3e-3))/vb)
    for s in [0.25,0.5,1.0]:
        Cs,Cb=100e-6*s,400e-6*s
        best=None
        for fbw in [4e3,6e3,8e3,10e3,12e3]:
            K=design(L,Cs,Cb,fbw)
            for Kaw in [0.0,0.1,0.3,0.6,1.0]:
                t,log,satf=sim_fast(K,L,Cs,Cb,step(60.),1.5e-3,Kaw=Kaw)
                mt=metrics(t,log,0.3e-3); tail=log[t>1.0e-3,0]; unstable=np.ptp(tail)>2.0
                if not unstable and (best is None or mt["droop"]<best[2]["droop"]): best=(fbw,Kaw,mt)
        print(f"Part A s={s}: best f_bw={best[0]/1e3:.0f} kHz Kaw={best[1]} droop={best[2]['droop']:.1f} V vmax={best[2]['vmax']:.1f}" if best else f"Part A s={s}: no stable design")
        out[str(s)]=dict(fbw=best[0],Kaw=best[1],**best[2]) if best else None
    return out

# ------------------------------------------------------------------ Part B: SALS load shaping
class Loads:
    """Cold-start worst case (A at 400 V): base 12.5 A (Stage C etc.); heat-pump compressor: command at t_c -> ramp tau 50 ms to 25 A (10 kW)
       with 2x surge (+25 A) for 20 ms; V2L 9 A (3.6 kW) at t_v (non-deferrable); deferrable: cabin PTC 17.5 A (7 kW), battery heater 17.5 A (7 kW),
       48 V low-priority 3.75 A (1.5 kW). Peak without shaping = 12.5+50+9+17.5+17.5+3.75 = 110 A > 100 A rating."""
    def __init__(self,t_c=0.005,t_p=0.006,t_v=0.004,base=12.5):
        self.t_c,self.t_p,self.t_v,self.base=t_c,t_p,t_v,base
    def nondef(self,t):
        comp=np.where(t>=self.t_c, np.where(t<self.t_c+0.020, 50.0, 25*(1-np.exp(-(t-self.t_c-0.020)/0.05))+0.0), 0.0)
        v2l=np.where(t>=self.t_v,9.0,0.0)
        return self.base+comp+v2l
    deferrable={"PTC":dict(req=17.5,t=0.006,w=1.0,ramp=None),"BatHeater":dict(req=17.5,t=0.006,w=0.7,ramp=None),"48V_lowprio":dict(req=3.75,t=0.006,w=0.5,ramp=None)}

def sals_schedule(loads,Imax=95.,H=15,Tc=1e-3,tend=0.08,pred_err=0.0,t_err=0.0,robust=None):
    """robust=(dt_unc, mag_unc): use worst case over timing shifts +-dt_unc and magnitude (1+mag_unc)"""
    """Receding-horizon LP every Tc: allow u_j,k in [0,req_j] for deferrable loads; minimize sum_k sum_j w_j (req_j - u_j,k) * (1+0.02 k)
       s.t. nondef_pred_k + sum_j u_j,k <= Imax. Returns allowed power time series (first move applied)."""
    tgrid=np.arange(0,tend,Tc); names=list(loads.deferrable); J=len(names)
    allowed={nm:np.zeros(len(tgrid)) for nm in names}
    for i,t0 in enumerate(tgrid):
        th=t0+np.arange(H)*Tc
        # predicted non-deferrable profile with error: magnitude (1+pred_err), timing shift t_err
        nd=loads.nondef(th - t_err)*(1+pred_err)
        if robust is not None:
            dtu,magu=robust; shifts=np.linspace(-dtu,dtu,11)
            nd=np.max([loads.nondef(th - t_err - sh) for sh in shifts],axis=0)*(1+pred_err)*(1+magu)
        # decision vector u (H*J)
        c=np.zeros(H*J); bounds=[]
        for k in range(H):
            for j,nm in enumerate(names):
                dj=loads.deferrable[nm]; req=dj["req"] if th[k]>=dj["t"] else 0.0
                c[k*J+j]=-dj["w"]*(1+0.02*k)          # maximize served -> minimize negative
                bounds.append((0.0,req))
        A_ub=np.zeros((H,H*J)); b_ub=np.zeros(H)
        for k in range(H):
            A_ub[k,k*J:(k+1)*J]=1.0; b_ub[k]=Imax-nd[k]
        res=linprog(c,A_ub=A_ub,b_ub=b_ub,bounds=bounds,method="highs")
        u=res.x if res.success else np.zeros(H*J)
        for j,nm in enumerate(names): allowed[nm][i]=u[j]     # first move
    return tgrid,allowed

def partB():
    out={}; L=1.5e-6; Cs=100e-6; Cb=400e-6; K=design(L,Cs,Cb,8e3)
    ld=Loads()
    def make_iload(allowed=None,tgrid=None):
        def f(tt,vb):
            i=ld.nondef(np.array([tt]))[0]
            for nm,dj in ld.deferrable.items():
                if allowed is None: i+= dj["req"] if tt>=dj["t"] else 0.0
                else: i+= np.interp(tt,tgrid,allowed[nm],left=0.0,right=allowed[nm][-1])
            return i*Vbus/vb
        return f
    tend=0.08
    # (1) no shaping, PPRC 100 A
    t,log,_=sim_fast(K,L,Cs,Cb,make_iload(),tend,Isat=100.,Kaw=0.05,dt=0.2e-6)
    m0=metrics(t,log,0.0); print("B0 no shaping, PPRC 100 A:",{k:round(float(v),1) if not isinstance(v,bool) else v for k,v in m0.items()}); out["B0_100A"]=m0
    # (2) hardware alternative: PPRC 150 A (12 kW)
    t2,log2,_=sim_fast(K,L,Cs,Cb,make_iload(),tend,Isat=150.,Kaw=0.05,dt=0.2e-6)
    m2=metrics(t2,log2,0.0); print("HW alt PPRC 150 A:",{k:round(float(v),1) if not isinstance(v,bool) else v for k,v in m2.items()}); out["HW_150A"]=m2
    # (3) SALS with perfect prediction
    tg,al=sals_schedule(ld,Imax=95.,tend=tend)
    t3,log3,_=sim_fast(K,L,Cs,Cb,make_iload(al,tg),tend,Isat=100.,Kaw=0.05,dt=0.2e-6)
    m3=metrics(t3,log3,0.0); print("SALS perfect prediction:",{k:round(float(v),1) if not isinstance(v,bool) else v for k,v in m3.items()}); out["SALS_perfect"]=m3
    ptc_delay=float(tg[np.argmax(al["PTC"]>=17.4)]-ld.deferrable["PTC"]["t"]) if np.any(al["PTC"]>=17.4) else None
    bh_delay=float(tg[np.argmax(al["BatHeater"]>=17.4)]-0.006) if np.any(al["BatHeater"]>=17.4) else None
    print("   delays: PTC %s ms, BatHeater %s ms, 48V %s ms"%(None if ptc_delay is None else round(ptc_delay*1e3), None if bh_delay is None else round(bh_delay*1e3), round((tg[np.argmax(al['48V_lowprio']>=3.7)]-0.006)*1e3)))
    out["SALS_perfect"]["batheater_delay_ms"]=None if bh_delay is None else bh_delay*1e3
    out["SALS_perfect"]["ptc_delay_ms"]=ptc_delay*1e3 if ptc_delay else None
    # (4) SALS with prediction errors: magnitude -20 % (under-predict), timing +5 ms (surge later than predicted)
    for pe,te,tag in [(-0.2,0.0,"under20"),(0.0,5e-3,"late5ms"),(-0.2,5e-3,"under20_late5ms"),(0.0,-5e-3,"early5ms")]:
        tg4,al4=sals_schedule(ld,Imax=95.,tend=tend,pred_err=pe,t_err=te)
        t4,log4,_=sim_fast(K,L,Cs,Cb,make_iload(al4,tg4),tend,Isat=100.,Kaw=0.05,dt=0.2e-6)
        m4=metrics(t4,log4,0.0); print(f"SALS pred err {tag}:",{k:round(float(v),1) if not isinstance(v,bool) else v for k,v in m4.items()}); out[f"SALS_{tag}"]=m4
    # (5) SALS margin sweep: Imax 90/95/98 with under20_late5ms
    for Imax in [85.,90.,95.,98.]:
        tg5,al5=sals_schedule(ld,Imax=Imax,tend=tend,pred_err=-0.2,t_err=5e-3)
        t5,log5,_=sim_fast(K,L,Cs,Cb,make_iload(al5,tg5),tend,Isat=100.,Kaw=0.05,dt=0.2e-6)
        m5=metrics(t5,log5,0.0); print(f"SALS Imax={Imax} (err under20+late5ms): collapse={m5['collapse']} droop={m5['droop']:.1f}"); out[f"SALS_margin_{int(Imax)}"]=m5
    # (6) robust SALS (timing +-5 ms, magnitude +25 %) under the same errors
    for pe,te,tag in [(-0.2,5e-3,"under20_late5ms"),(0.0,-5e-3,"early5ms"),(-0.2,0.0,"under20")]:
        tg6,al6=sals_schedule(ld,Imax=95.,tend=tend,pred_err=pe,t_err=te,robust=(5e-3,0.25))
        t6,log6,_=sim_fast(K,L,Cs,Cb,make_iload(al6,tg6),tend,Isat=100.,Kaw=0.05,dt=0.2e-6)
        m6=metrics(t6,log6,0.0); print(f"SALS-robust err {tag}:",{k:round(float(v),1) if not isinstance(v,bool) else v for k,v in m6.items()}); out[f"SALSrobust_{tag}"]=m6
        if tag=="under20_late5ms": t6r,log6r=t6,log6
    # (7) reactive under-voltage shedding (no prediction): trip at 384 V, 1 ms actuation, restore after 40 ms, priority order
    class Reactive:
        """reactive UV load-dump: trip at 388 V -> shed ALL deferrable loads after 1 ms actuation; restore one by one (priority) every 20 ms if v>396"""
        def __init__(s_): s_.trip=None; s_.restored={nm:False for nm in ld.deferrable}; s_.order=["PTC","BatHeater","48V_lowprio"]; s_.lastr=None
        def __call__(s_,tt,vb):
            i=ld.nondef(np.array([tt]))[0]
            if s_.trip is None and vb<388.0: s_.trip=tt+1e-3; s_.lastr=tt+1e-3
            if s_.trip is not None and tt>=s_.trip+20e-3 and vb>396.0 and tt-s_.lastr>=20e-3:
                for nm in s_.order:
                    if not s_.restored[nm]: s_.restored[nm]=True; s_.lastr=tt; break
            for nm,dj in ld.deferrable.items():
                shed = s_.trip is not None and tt>=s_.trip and not s_.restored[nm]
                i+= dj["req"] if (tt>=dj["t"] and not shed) else 0.0
            return i*Vbus/vb
    rf=Reactive(); t7,log7,_=sim_fast(K,L,Cs,Cb,rf,tend,Isat=100.,Kaw=0.05,dt=0.2e-6)
    m7=metrics(t7,log7,0.0); print("Reactive UV load-dump (388 V trip, shed all):",{k:round(float(v),1) if not isinstance(v,bool) else v for k,v in m7.items()}); out["Reactive"]=m7
    # figure
    fig,ax=plt.subplots(2,1,figsize=(9,6),sharex=True)
    ax[0].plot(t*1e3,log[:,3],label="load current, no shaping"); ax[0].plot(t3*1e3,log3[:,3],label="load current, SALS-shaped (perfect)"); ax[0].plot(t7*1e3,log7[:,3],label="load current, reactive shedding"); ax[0].axhline(100,color="r",ls="--",label="PPRC series rating 100 A"); ax[0].set_ylabel("400 V load current (A)"); ax[0].set_ylim(0,130); ax[0].legend(fontsize=8); ax[0].grid(True)
    ax[1].plot(t*1e3,log[:,0],label="B0 no shaping (PPRC 100 A) -> collapse"); ax[1].plot(t7*1e3,log7[:,0],label="reactive UV load-dump (388 V trip)"); ax[1].plot(t2*1e3,log2[:,0],label="HW alternative: PPRC 150 A"); ax[1].plot(t3*1e3,log3[:,0],label="SALS perfect prediction"); ax[1].plot(t6r*1e3,log6r[:,0],label="SALS robust, -20 % / +5 ms error"); ax[1].axhspan(392,408,color="g",alpha=0.1); ax[1].set_ylim(300,420); ax[1].set_ylabel("V_bus (V)"); ax[1].set_xlabel("t (ms)"); ax[1].legend(fontsize=8); ax[1].grid(True)
    ax[0].set_title("TB-S6: cold-start event (compressor surge + cabin PTC + battery heater + V2L + 48 V low-prio), V_bat 788 V")
    fig.tight_layout(); fig.savefig(f"{FIG}/tbs6_sals.png",dpi=140); plt.close(fig)
    return out

if __name__=="__main__":
    import sys, os
    res={}
    if len(sys.argv)<2 or sys.argv[1]=="A": res["A"]=partA()
    if len(sys.argv)<2 or sys.argv[1]=="B": res["B"]=partB()
    prev={}
    if os.path.exists("results/tbs6_results.json"): prev=json.load(open("results/tbs6_results.json"))
    prev.update(res); json.dump(prev,open("results/tbs6_results.json","w"),indent=1,default=float)
