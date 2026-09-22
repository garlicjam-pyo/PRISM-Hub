"""Series PPRC path -- state feedback with integral action (pole placement), verified in time domain with DAB lag+delay+sampling.
Plant (continuous): x=[i_p, v_ser, v_bus, i_dab], u=cmd, w=i_load
  di_p/dt   = (-(R_A+R_p) i_p + v_ser - v_bus)/L
  dv_ser/dt = (i_dab - i_p)/C_ser
  dv_bus/dt = (i_p - w - v_ser*i_dab/v_bus)/C_bus
  di_dab/dt = (u - i_dab)/tau      (+ delay d, sampling Ts in simulation)
  integrator: dq/dt = v_ref - v_bus
Control: u = -K x + k_q q + i_ff  (+ feedforward of operating point)
"""
import numpy as np, json, scipy.signal as sg
from pprc_model import equilibrium, linearize, SPS_CURRENT_MAX
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"
Vbat=788.; R_A=10.2e-3; R_p=3e-3; tau=10e-6; d_dab=5e-6; Ts=5e-6

def plant(L,Cs,Cb):
    return linearize(L,Cs,Cb,Vbat,5e3,R_A+R_p,tau)

def design(L,Cs,Cb,f_bw,zeta=0.7):
    """pole placement: complex pair at f_bw (zeta), real at f_bw, integrator at f_bw/3, DAB at 2.5*f_bw (capped 30 kHz)"""
    w=2*np.pi*f_bw
    poles=[-zeta*w+1j*w*np.sqrt(1-zeta**2), -zeta*w-1j*w*np.sqrt(1-zeta**2), -w, -w/3, -min(2.5*w,2*np.pi*30e3)]
    Aa,Ba=plant(L,Cs,Cb)
    K=sg.place_poles(Aa,Ba,np.array(poles)).gain_matrix[0]
    return K

def simulate(K,L,Cs,Cb,dI=60.,t_step=1.0e-3,tend=2.5e-3,ff="none",pred_err=0.0,t_err=0.0,pre_boost=0.0,t_lead=1e-3,
             dt=0.1e-6,P0=5e3,Isat=SPS_CURRENT_MAX,v_ref=400.):
    n=int(tend/dt); t=np.arange(n)*dt
    ip,vs,vb,idab=equilibrium(Vbat,P0,R_A+R_p,v_ref)
    # steady-state: u = -K x + Kq q  -> choose q so that u = ip at steady state (x0)
    x0=np.array([ip,vs,vb,idab]); q=-(ip+K[:4]@x0)/K[4] if K[4]!=0 else 0.0
    dbuf=np.zeros(int(d_dab/dt)+1)+ip; cmd_hold=ip; k_ctrl=int(Ts/dt)
    log=np.zeros((n,4))
    for k in range(n):
        tt=t[k]; Pload=P0+400.*dI*(tt>=t_step); iload=Pload/vb
        if k%k_ctrl==0:
            if ff=="B1":   i_ff=(P0+400.*dI*(tt-20e-6>=t_step))/vb - P0/400.
            elif ff=="B2": i_ff=dI*(tt>=t_step-(tau+d_dab))
            elif ff=="ARL":i_ff=dI*(1-pred_err)*(tt>=t_step-(tau+d_dab)+t_err)
            else: i_ff=0.0
            vr=v_ref
            if pre_boost>0 and tt<t_step: vr=v_ref+pre_boost*min(1.0,max(0.0,(tt-(t_step-t_lead))/(t_lead*0.5)))
            x=np.array([ip,vs,vb,idab])
            cmd=-K[:4]@x - K[4]*q + i_ff
            limit=min(Isat,SPS_CURRENT_MAX*max(vb,0.)/400.,8e3/max(abs(vs),1e-9)); cmd=np.clip(cmd,-limit,limit); cmd_hold=cmd
            q+=Ts*(vr-vb)   # integrator (sampled)
        dbuf=np.roll(dbuf,1); dbuf[0]=cmd_hold; u=dbuf[-1]
        dip=(Vbat/2-(R_A+R_p)*ip+vs-vb)/L; dvs=(idab-ip)/Cs; dvb=(ip-iload-vs*idab/vb)/Cb; didab=(u-idab)/tau
        ip+=dt*dip; vs+=dt*dvs; vb+=dt*dvb; idab+=dt*didab
        log[k]=(vb,ip,idab,vs)
        if not np.isfinite(log[k]).all() or vb<50:
            log[k:]=log[k]; break
    m=t>=t_step; droop=400.-log[m,0].min(); over=log[:,0].max()-400.
    ok=np.abs(log[:,0]-400.)<=4.0; rec=None
    for k in range(int(t_step/dt),n):
        if ok[k:].all(): rec=t[k]-t_step; break
    # stability check: growing oscillation in last 0.5 ms
    tail=log[t>tend-0.5e-3,0]; unstable=(np.ptp(tail)>2.0) or not np.isfinite(tail).all() or np.min(tail)<50
    return dict(droop=droop,overshoot=over,rec=rec,ipeak=np.abs(log[:,2]).max(),unstable=unstable,t=t,log=log,within_port_limits=bool(np.max(np.abs(log[:,3]))<=90 and np.max(np.abs(log[:,3]*log[:,2]))<=8000 and np.max(np.abs(log[:,2]))<=Isat+1e-6))

def max_bw(L,Cs,Cb):
    """largest f_bw for which the sampled/delayed loop is stable with overshoot <= 4 V after a 60 A step and recovery <= 400 us"""
    best=None
    for fbw in [2e3,3e3,4e3,5e3,6e3,7e3,8e3]:   # capped at 8 kHz = the documented nominal design (README/App. C: 4.7 V)
        K=design(L,Cs,Cb,fbw); r=simulate(K,L,Cs,Cb)
        if r["within_port_limits"] and not r["unstable"] and r["overshoot"]<=4.0 and r["rec"] is not None and r["rec"]<=400e-6: best=(fbw,K,r)
    return best

if __name__=="__main__":
    out={}
    print("TB-B2 (state feedback + integral): max stable bandwidth vs L_path, Cs=100 uF, Cb=400 uF")
    for L in [0.5e-6,1.5e-6,3e-6]:
        b=max_bw(L,100e-6,400e-6); Ce=100e-6*400e-6/500e-6; fres=1/(2*np.pi*np.sqrt(L*Ce))
        if b is None:
            print(f"  L={L*1e6:.1f} uH: no feasible design in bandwidth grid")
            out[f"tbb2_L{L*1e6:.1f}"]={"status":"no_feasible_design"}
            continue
        print(f"  L={L*1e6:.1f} uH f_res={fres/1e3:.1f} kHz : max f_bw={b[0]/1e3:.1f} kHz  droop={b[2]['droop']:.1f} V rec={b[2]['rec']*1e6:.0f} us  K={np.round(b[1],3)}")
        out[f"tbb2_L{L*1e6:.1f}"]=dict(fres=fres,fbw=b[0],droop=b[2]["droop"],rec=b[2]["rec"],K=b[1].tolist())
    # PI-only reference (from tb_b_pprc): 1.78 kHz -> droop
    L=1.5e-6; Cs=100e-6; Cb=400e-6
    fbw=8e3; K=design(L,Cs,Cb,fbw)  # common nominal design with MATLAB; sweep is exploratory
    print(f"nominal design f_bw={fbw/1e3:.1f} kHz")
    logs={}
    for name,kw in [("B0",{}),("B1",dict(ff="B1")),("B2",dict(ff="B2")),("ARL(err20%,+50us)",dict(ff="ARL",pred_err=0.2,t_err=50e-6)),
                    ("ARL+preboost8V",dict(ff="ARL",pred_err=0.2,t_err=50e-6,pre_boost=8.0)),("preboost only",dict(pre_boost=8.0))]:
        rr=simulate(K,L,Cs,Cb,**kw); logs[name]=rr
        print(f"TB-S1 {name}: droop {rr['droop']:.2f} V, overshoot {rr['overshoot']:.2f} V, rec {rr['rec']*1e6 if rr['rec'] is not None else float('nan'):.0f} us, i_dab pk {rr['ipeak']:.0f} A")
        out[f"tbs1_{name}"]=dict(droop=rr["droop"],overshoot=rr["overshoot"],rec=rr["rec"],ipeak=rr["ipeak"])
    fig,ax=plt.subplots(figsize=(8,4))
    for name,rr in logs.items():
        m=(rr["t"]>=0.8e-3)&(rr["t"]<=1.6e-3); ax.plot((rr["t"][m]-1e-3)*1e6,rr["log"][m,0],label=name)
    ax.axhline(392,color="r",ls="--",lw=0.8); ax.set_xlabel("t - t_step (us)"); ax.set_ylabel("V_bus (V)"); ax.grid(True); ax.legend(fontsize=8)
    ax.set_title(f"TB-S1: 60 A CPL step, L 1.5 uH / C_ser 100 uF / C_bus 400 uF, state-feedback f_bw {fbw/1e3:.0f} kHz")
    fig.tight_layout(); fig.savefig(f"{FIG}/tbs1_step.png",dpi=140); plt.close(fig)
    # DAB current for B0 and ARL
    fig,ax=plt.subplots(figsize=(8,3.2))
    for name in ["B0","B2","ARL+preboost8V"]:
        rr=logs[name]; m=(rr["t"]>=0.8e-3)&(rr["t"]<=1.6e-3); ax.plot((rr["t"][m]-1e-3)*1e6,rr["log"][m,2],label=name)
    ax.set_xlabel("t - t_step (us)"); ax.set_ylabel("i_dab (A)"); ax.grid(True); ax.legend(fontsize=8); ax.set_title("PPRC (DAB) output current")
    fig.tight_layout(); fig.savefig(f"{FIG}/tbs1_idab.png",dpi=140); plt.close(fig)
    # cap scaling (controller re-designed per bank)
    print("Cap scaling (state feedback re-designed to max bandwidth per bank):")
    scal={}
    for s in [0.25,0.5,1.0,2.0]:
        Cs_,Cb_=100e-6*s,400e-6*s; bb=max_bw(L,Cs_,Cb_)
        if bb is None:
            print(f"  s={s}: no feasible design in bandwidth grid")
            scal[str(s)]={key:None for key in ["fbw","B0","B1","B2","ARL"]}
            continue
        r0=simulate(bb[1],L,Cs_,Cb_); r2=simulate(bb[1],L,Cs_,Cb_,ff="B2"); ra=simulate(bb[1],L,Cs_,Cb_,ff="ARL",pred_err=0.2,t_err=50e-6,pre_boost=8.0)
        rb1=simulate(bb[1],L,Cs_,Cb_,ff="B1")
        print(f"  s={s}: f_bw={bb[0]/1e3:.1f} kHz  B0 {r0['droop']:.1f} V  B1 {rb1['droop']:.1f} V  B2 {r2['droop']:.1f} V  ARL {ra['droop']:.1f} V")
        scal[str(s)]=dict(fbw=bb[0],B0=r0["droop"],B1=rb1["droop"],B2=r2["droop"],ARL=ra["droop"])
    out["cap_scaling"]=scal
    fig,ax=plt.subplots(figsize=(6,3.6)); ss=[s for s in [0.25,0.5,1.0,2.0] if scal[str(s)]["B0"] is not None]
    for key,lab,mk in [("B0","B0 state-feedback only","o-"),("B1","B1 measured-current ff","d-"),("B2","B2 ideal predictive ff","s-"),("ARL","ARL (20 % err, +50 us, pre-boost 8 V)","^-")]:
        ax.plot(ss,[scal[str(s)][key] if scal[str(s)][key] is not None else np.nan for s in ss],mk,label=lab)
    ax.axhline(8,color="r",ls=":",label="2 % (8 V)"); ax.set_xlabel("capacitor bank scale (1 = 100 uF + 400 uF)"); ax.set_ylabel("droop, 60 A step (V)"); ax.grid(True); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(f"{FIG}/tbs1_cap_scaling.png",dpi=140); plt.close(fig)
    # ARL sensitivity
    sens={}
    for pe in [0.0,0.2,0.4,0.6]:
        row=[]
        for te in [-100e-6,0.0,50e-6,100e-6,200e-6]:
            rr=simulate(K,L,Cs,Cb,ff="ARL",pred_err=pe,t_err=te); row.append(round(rr["droop"],1))
        sens[str(pe)]=row; print(f"ARL sensitivity err={pe}: droop(V) for t_err[-100,0,50,100,200 us] = {row}")
    out["arl_sens"]=sens
    # L_path robustness: controller designed for 1.5 uH applied to 0.75 / 3 uH
    for Lx in [0.75e-6,3e-6]:
        rr=simulate(K,Lx,Cs,Cb); print(f"robustness: K(1.5uH) on L={Lx*1e6} uH -> droop {rr['droop']:.1f} V, overshoot {rr['overshoot']:.1f} V, unstable={rr['unstable']}")
        out[f"robust_L{Lx*1e6}"]=dict(droop=rr["droop"],overshoot=rr["overshoot"],unstable=bool(rr["unstable"]))
    json.dump(out,open("results/tbb_results.json","w"),indent=1,default=float)
