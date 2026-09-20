"""TB-C2: bidirectional CLLC with both bridges driven (phase shift phi), 400 V bus <-> 48 V battery (Rint model).
Forward: primary leads. Reverse: secondary leads. Step phi from +phi_f to -phi_f and measure direction-change time.
Model: same 6-state tank as TB-C1 but v_s2 = ±n*Vo square wave with phase phi (deg) w.r.t. primary; Vo = V48_ocv + R48*i_o (battery), i_o = filtered secondary current*sign convention.
"""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"
n=25/3; Vin=400.; fr=250e3; Lr1=11.0e-6; Cr1=36.8e-9; Lm=66e-6; Lr2p=Lr1; Cr2p=Cr1; Co=470e-6; td=50e-9
V48=48.; R48=20e-3

def simulate(phi_fn, ncyc=600, Nstep=400, v48_fn=lambda tt:48., fs=fr):
    T=1/fs; dt=T/Nstep; N=ncyc*Nstep; ginv=1/(1/Lr1+1/Lm+1/Lr2p)
    x=np.array([0.,0.,0.,0.,0.,48.]); log=np.zeros((N,4)); ndead=int(round(td/dt)); half=Nstep//2
    def sq(m,V):  # square wave value at step index m within period, with dead time
        if m<half: return V if m>=ndead else 0.0
        return -V if (m-half)>=ndead else 0.0
    for k in range(N):
        m=k%Nstep; phi=phi_fn(k*dt); ms=int(round(m - phi/360*Nstep))%Nstep   # secondary lags primary by phi (>0: forward)
        vp=sq(m,Vin)
        def f(x):
            ir1,vc1,im,ir2,vc2,Vo=x
            vs2=sq(ms,n*Vo)
            vm=((vp-vc1)/Lr1+(vc2+vs2)/Lr2p)*ginv
            # power delivered to 48 V side: i_o = i_r2' * sign(vs2)/... : the driven bridge rectifies: i_o = ir2 * n * sign_of_bridge_state
            s2=np.sign(sq(ms,1.0)); io=ir2*n*s2
            return np.array([(vp-vc1-vm)/Lr1, ir1/Cr1, vm/Lm, (vm-vc2-vs2)/Lr2p, ir2/Cr2p, (io-(Vo-v48_fn(k*dt))/R48)/Co])
        k1=f(x); k2=f(x+0.5*dt*k1); k3=f(x+0.5*dt*k2); k4=f(x+dt*k3); x=x+dt/6*(k1+2*k2+2*k3+k4)
        io=x[3]*n*np.sign(sq(ms,1.0)); log[k]=(x[0],x[3]*n,x[5],io)
    t=np.arange(N)*dt
    return t,log

if __name__=="__main__":
    out={}
    # synchronous operation (phi=0): power set by 48 V battery OCV vs bus (natural bidirectional flow)
    rows=[]
    for v in [46.,47.,48.,49.,50.,51.]:
        t,L=simulate(lambda tt:0.0, ncyc=300, v48_fn=lambda tt,v=v: v); m=t>t[-1]-20/fr
        P=np.mean(L[m,3]*L[m,2]); rows.append((v,P)); print(f"V48_ocv {v:.0f} V: P_48V side {P/1e3:+.2f} kW (Vo {L[m,2].mean():.2f})")
    out["P_vs_V48"]=rows
    # transition: OCV step 47.5 -> 49.5 V (regen surge) at t0, phi=0
    t0=300/fr
    t,L=simulate(lambda tt:0.0, ncyc=600, v48_fn=lambda tt: 47.5 if tt<t0 else 49.5)
    Pinst=L[:,3]*L[:,2]; w=400; Pf=np.convolve(Pinst,np.ones(w)/w,mode="same"); k0=np.argmax(t>=t0)
    Pb=Pf[k0-2000:k0-500].mean(); Pa=Pf[-2000:].mean(); kk=np.argmax(Pf[k0:]<=0.9*Pa) if Pa<0 else np.argmax(Pf[k0:]>=0.9*Pa); t_tr=t[k0+kk]-t0
    print(f"transition (OCV 47.5->49.5 V): P {Pb/1e3:+.2f} -> {Pa/1e3:+.2f} kW, 90 % in {t_tr*1e6:.1f} us, |i_sec| max {np.abs(L[:,1]).max():.0f} A")
    out["transition"]=dict(P_before=Pb,P_after=Pa,t_90=t_tr,isec_max=float(np.abs(L[:,1]).max()))
    # current limiting by frequency shift during reverse: fs = 1.1 fr and 1.2 fr with OCV 49.5
    for fsr in [1.0,1.1,1.2]:
        t2,L2=simulate(lambda tt:0.0, ncyc=300, v48_fn=lambda tt:49.5, fs=fsr*fr); m=t2>t2[-1]-20/(fsr*fr)
        print(f"reverse, fs={fsr} fr: P {np.mean(L2[m,3]*L2[m,2])/1e3:+.2f} kW, |i_sec| rms {np.sqrt(np.mean(L2[m,1]**2)):.0f} A"); out[f"rev_fs{fsr}"]=float(np.mean(L2[m,3]*L2[m,2]))
    fig,ax=plt.subplots(2,1,figsize=(8,5),sharex=True); tp=(t-t0)*1e6
    ax[0].plot(tp,Pf/1e3); ax[0].set_ylabel("48 V-side power (kW, 1-period avg)"); ax[0].grid(True); ax[0].set_xlim(-40,160)
    ax[1].plot(tp,L[:,2]); ax[1].set_ylabel("V_48 terminal (V)"); ax[1].set_xlabel("t - t_step (us)"); ax[1].grid(True)
    ax[0].set_title("TB-C2: CLLC synchronous (phi=0), 48 V OCV step 47.5 -> 49.5 V: forward -> reverse"); fig.tight_layout(); fig.savefig(f"{FIG}/tbc2_bidir.png",dpi=140); plt.close(fig)
    json.dump(out,open("results/tbc2_results.json","w"),indent=1,default=float)
