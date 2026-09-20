"""TB-C1  CLLC 400 V -> 48 V, 3 kW, symmetric tank, switching-level ODE.
Primary full bridge: v_p = ±Vin square (50 %, dead time td). Secondary: synchronous rectifier modelled as ideal
bidirectional switches driven by secondary current sign (diode-like) with Vf=0 -> v_s2 = sign(i_s)*Vo (referred).
States: i_r1 (primary resonant current), v_c1, i_m (magnetizing), i_r2' (secondary current referred to primary), v_c2', Vo
Equations (all referred to primary, n = 25/3):
  L_r1 di_r1/dt = v_p - v_c1 - v_m
  C_r1 dv_c1/dt = i_r1
  L_m  di_m/dt  = v_m
  L_r2' di_r2'/dt = v_m - v_c2' - v_s2'         (i_r2' flows out of the magnetizing node into secondary)
  C_r2' dv_c2'/dt = i_r2'
  i_r1 = i_m + i_r2'  (KCL at magnetizing node) -> v_m determined algebraically:
     from the three inductor equations: di_r1/dt = di_m/dt + di_r2'/dt
     (v_p - v_c1 - v_m)/L_r1 = v_m/L_m + (v_m - v_c2' - v_s2')/L_r2'
     -> v_m = [ (v_p - v_c1)/L_r1 + (v_c2' + v_s2')/L_r2' ] / (1/L_r1 + 1/L_m + 1/L_r2')
  C_o dVo/dt = |i_r2'|*n - Vo/R_L  (ideal SR: secondary current magnitude delivered to output), v_s2' = sign(i_r2')*n*Vo
Dead time: v_p = 0 with body diodes ignored -> ZVS check done analytically from i_r1 at switching instant vs required Coss charge.
"""
import numpy as np, json, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"
n=25/3; Vin=400.; fr=250e3; Lr1=11.0e-6; Cr1=36.8e-9; Lm=66e-6; Lr2p=Lr1; Cr2p=Cr1   # symmetric (referred)
Co=470e-6; Coss=100e-12; td=50e-9

def simulate(Po=3000., fs=250e3, Vin=400., ncyc=400, Nstep=400, Vo0=48., reverse=False):
    RL=48.**2/Po if Po>0 else 1e9
    T=1/fs; dt=T/Nstep; N=ncyc*Nstep
    ir1=0.; vc1=0.; im=0.; ir2=0.; vc2=0.; Vo=Vo0
    log=np.zeros((N,6)); ndead=int(round(td/dt)); half=Nstep//2
    ginv=1/(1/Lr1+1/Lm+1/Lr2p)
    def f(x,vp):
        ir1,vc1,im,ir2,vc2,Vo=x
        vs2=np.sign(ir2)*n*Vo if abs(ir2)>1e-6 else 0.0
        vm=((vp-vc1)/Lr1+(vc2+vs2)/Lr2p)*ginv
        return np.array([(vp-vc1-vm)/Lr1, ir1/Cr1, vm/Lm, (vm-vc2-vs2)/Lr2p, ir2/Cr2p, (abs(ir2)*n - Vo/RL)/Co])
    x=np.array([ir1,vc1,im,ir2,vc2,Vo])
    for k in range(N):
        m=k%Nstep
        if m<half: vp=Vin if m>=ndead else 0.0
        else:      vp=-Vin if (m-half)>=ndead else 0.0
        k1=f(x,vp); k2=f(x+0.5*dt*k1,vp); k3=f(x+0.5*dt*k2,vp); k4=f(x+dt*k3,vp)
        x=x+dt/6*(k1+2*k2+2*k3+k4); log[k]=x
    t=np.arange(N)*dt; msk=t>=(ncyc-10)*T
    L=log[msk]; ir1=L[:,0]; im=L[:,2]; ir2=L[:,3]; Vo=L[:,5]
    # switching instants: end of each half (index just before dead time start): current available for ZVS = i_r1 at that instant
    idx=[i for i in range(len(ir1)) if (i%Nstep)==half-1 or (i%Nstep)==Nstep-1]
    i_sw=np.abs(ir1[idx]).mean()
    # ZVS requirement: charge 2*Coss*Vin within td with i_sw: need i_sw*td >= 2*Coss*Vin  (approx, constant current)
    q_req=2*Coss*Vin; q_avail=i_sw*td
    return dict(Vo=Vo.mean(), gain=Vo.mean()*n/Vin, Ipri_rms=np.sqrt(np.mean(ir1**2)), Isec_rms=np.sqrt(np.mean(ir2**2))*n,
                Im_pk=np.abs(im).max(), i_sw=i_sw, zvs_margin=q_avail/q_req, Po=Vo.mean()**2/RL, t=t[msk], ir1=ir1, ir2=ir2*n, im=im, Vo_w=Vo)

if __name__=="__main__":
    out={}
    r=simulate(); print(f"nominal 3 kW fs=fr: Vo {r['Vo']:.2f} V gain {r['gain']:.4f} Ipri_rms {r['Ipri_rms']:.2f} A Isec_rms {r['Isec_rms']:.1f} A Im_pk {r['Im_pk']:.2f} A i_sw {r['i_sw']:.2f} A ZVS margin {r['zvs_margin']:.1f}x")
    out["nominal"]={k:float(v) for k,v in r.items() if isinstance(v,(float,np.floating))}
    fig,ax=plt.subplots(3,1,figsize=(8,6),sharex=True); tp=(r["t"]-r["t"][0])*1e6
    ax[0].plot(tp,r["ir1"],label="i_r1 (primary)"); ax[0].plot(tp,r["im"],label="i_m"); ax[0].legend(fontsize=8); ax[0].grid(True); ax[0].set_ylabel("A")
    ax[1].plot(tp,r["ir2"]); ax[1].set_ylabel("i_sec (A)"); ax[1].grid(True)
    ax[2].plot(tp,r["Vo_w"]); ax[2].set_ylabel("V_o (V)"); ax[2].set_xlabel("t (us)"); ax[2].grid(True)
    ax[0].set_title("TB-C1 CLLC 400 -> 48 V, 3 kW, fs = fr = 250 kHz"); fig.tight_layout(); fig.savefig(f"{FIG}/tbc1_waveforms.png",dpi=140); plt.close(fig)
    # gain vs fs/fr and load  (compare to FHA)
    def fha(fn,Q,m=6): return 1/np.sqrt((1+(1/m)*(1-1/fn**2))**2+(Q*(fn-1/fn))**2)
    rows=[]
    for Po in [300.,1500.,3000.]:
        RL=48**2/Po; Rac=8*n**2*RL/np.pi**2; Q=2*np.pi*fr*Lr1/Rac
        for fn in [0.9,0.97,1.0,1.03,1.1]:
            rr=simulate(Po=Po,fs=fn*fr,ncyc=300); rows.append((Po,fn,rr["gain"],fha(fn,Q),rr["Vo"],rr["zvs_margin"])); print(f"Po {Po:.0f} fn {fn}: gain sim {rr['gain']:.3f} FHA {fha(fn,Q):.3f} Vo {rr['Vo']:.2f} ZVS {rr['zvs_margin']:.1f}x")
    out["gain_table"]=rows
    fig,ax=plt.subplots(figsize=(6,3.6))
    for Po in [300.,1500.,3000.]:
        rs=[x for x in rows if x[0]==Po]; ax.plot([x[1] for x in rs],[x[2] for x in rs],"o-",label=f"sim {Po/1e3:.1f} kW"); ax.plot([x[1] for x in rs],[x[3] for x in rs],"--",color="gray")
    ax.axvspan(0.97,1.03,color="y",alpha=0.3); ax.set_xlabel("fs/fr"); ax.set_ylabel("gain (n·Vo/Vin)"); ax.grid(True); ax.legend(fontsize=8); ax.set_title("TB-C1 gain: switching sim (solid) vs FHA (dashed)")
    fig.tight_layout(); fig.savefig(f"{FIG}/tbc1_gain.png",dpi=140); plt.close(fig)
    # input voltage ±2 %
    for V in [392.,400.,408.]:
        rr=simulate(Vin=V,ncyc=300); print(f"Vin {V}: Vo {rr['Vo']:.2f} V"); out[f"Vin{int(V)}"]=float(rr["Vo"])
    # losses from rms currents (same device assumptions as 3.4.4)
    r=simulate(ncyc=300); Ipri=r["Ipri_rms"]; Isec=r["Isec_rms"]
    Ppri=2*(Ipri/np.sqrt(2))**2*50e-3*2; Psr=2*(Isec/np.sqrt(2))**2*1e-3; Pxf=0.012*3000+10; Pg=4; Pcr=3
    Pl=Ppri+Psr+Pxf+Pg+Pcr; print(f"loss estimate from sim rms: pri {Ppri:.1f} W, SR {Psr:.1f} W, xfmr {Pxf:.0f} W -> total {Pl:.0f} W, eta {3000/(3000+Pl)*100:.2f} %")
    out["loss"]=dict(Ppri=Ppri,Psr=Psr,Pxf=Pxf,total=Pl,eta=3000/(3000+Pl))
    os.makedirs("results",exist_ok=True); json.dump(out,open("results/tbc1_results.json","w"),indent=1,default=float)
