"""TB-A1  rsc_phase switching simulation (piecewise-linear, RK4, 10 ns)
State x = [iC, vC, Vout] ; iC>0 = current entering C_fly top plate (charging)
Phase 1 (S1,S3 on):  L diC/dt = Vin - Vout - vC - iC*R
Phase 2 (S2,S4 on):  L diC/dt = Vout - vC - iC*R
Dead time (all off): body diodes:  iC>0 -> L diC/dt = -vC - iC*R - 2Vf  (freewheel around output node)
                                   iC<0 -> L diC/dt = Vin - vC - iC*R + 2Vf (energy returned to input)
                                   iC==0 -> stays 0 (diodes block)
Output node:  C_out dVout/dt = i_out - Vout/R_load ; i_out = iC (ph1), -iC (ph2), 0 (dead, iC>0), -iC->? (dead, iC<0 : current flows GND->B->A->Vin, not through output) = 0
"""
import numpy as np, json, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"; os.makedirs(FIG,exist_ok=True)

P = dict(Cfly=7.8125e-6, Lr=1.441e-7, Rds=6e-3, ESR=1.5e-3, RL=1e-3, Rmisc=1.5e-3, Vf=0.9,
         Eoss=24e-6, Qg_E=2e-6, Cout=400e-6, tdead=100e-9)
fr = 1/(2*np.pi*np.sqrt(P["Lr"]*P["Cfly"]))

def simulate(Vin=788., Iload=46.875, fratio=1.0, ncyc=300, Nstep=680, tdead=None):
    C,L=P["Cfly"],P["Lr"]; R=2*P["Rds"]+P["ESR"]+P["RL"]+P["Rmisc"]; Vf=P["Vf"]; Co=P["Cout"]
    td = P["tdead"] if tdead is None else tdead
    fs=fratio*fr; T=1/fs; Vo0=Vin/2; Rload=Vo0/Iload
    dt=T/Nstep; n=ncyc*Nstep; t=np.arange(n)*dt
    x=np.array([0.0, Vo0, Vo0])   # precharged
    iC=np.empty(n); vC=np.empty(n); Vo=np.empty(n); st=np.empty(n,dtype=np.int8); iout=np.empty(n)
    ndead=int(round(td/dt)); half=Nstep//2
    def state_of(k):
        m=k%Nstep
        if m<half: return 1 if m>=ndead else 0
        else:      return 2 if (m-half)>=ndead else 0
    def f(x,s):
        i,v,vo=x
        if s==1:   di=(Vin-vo-v-i*R)/L; io=i
        elif s==2: di=(vo-v-i*R)/L;     io=-i
        else:
            if i>1e-3:   di=(-v-i*R-2*Vf)/L; io=0.0
            elif i<-1e-3: di=(Vin-v-i*R+2*Vf)/L; io=0.0
            else: di=0.0; io=0.0
        return np.array([di, i/C, (io-vo/Rload)/Co]), io
    for k in range(n):
        s=state_of(k)
        iC[k],vC[k],Vo[k]=x; st[k]=s
        k1,io=f(x,s); k2,_=f(x+0.5*dt*k1,s); k3,_=f(x+0.5*dt*k2,s); k4,_=f(x+dt*k3,s)
        iout[k]=io
        xn=x+dt/6*(k1+2*k2+2*k3+k4)
        if s==0 and (xn[0]*x[0] <= 0.0): xn[0]=0.0   # diode blocking at zero crossing
        x=xn
    # analysis on last 20 cycles
    m = t >= (ncyc-20)*T
    tt=t[m]; i=iC[m]; v=vC[m]; vo=Vo[m]; s=st[m]; io=iout[m]
    Ipk=np.max(np.abs(i)); Irms=np.sqrt(np.mean(i**2))
    # switching-instant currents: at transitions of state
    trans=np.where(np.diff(s)!=0)[0]
    off=[k for k in trans if s[k]!=0 and s[k+1]==0]; on=[k for k in trans if s[k]==0 and s[k+1]!=0]
    i_sw_max=np.max(np.abs(i[off])) if len(off) else 0; i_on_max=np.max(np.abs(i[on])) if len(on) else 0
    swing=v.max()-v.min()
    Pcond=np.mean(i**2)*R                               # all series resistances
    Pdiode=np.mean(np.where(s==0,2*Vf*np.abs(i),0.0))
    Pcoss=4*P["Eoss"]*fs; Pgate=4*P["Qg_E"]*fs
    Pout=np.mean(vo**2/Rload); Ploss=Pcond+Pdiode+Pcoss+Pgate
    eta=Pout/(Pout+Ploss); Rout=(Vin/2-np.mean(vo))/np.mean(io)
    return dict(Vin=Vin,Iload=Iload,fratio=fratio,fs=fs,Ipk=Ipk,Irms=Irms,i_sw_max=i_sw_max,
                zcs_ratio=i_sw_max/Ipk,i_on_max=i_on_max,swing=swing,Pcond=Pcond,Pdiode=Pdiode,Pcoss=Pcoss,Pgate=Pgate,
                Ploss=Ploss,Pout=Pout,eta=eta,Rout=Rout,Vout=np.mean(vo)), (tt,i,v,vo,s)

res={}
# nominal
r,(tt,i,v,vo,s)=simulate()
res["nominal"]=r; print("nominal",{k:(round(float(x),4) if isinstance(x,(float,np.floating)) else x) for k,x in r.items()})
fig,ax=plt.subplots(3,1,figsize=(8,6),sharex=True)
tp=(tt-tt[0])*1e6
ax[0].plot(tp,i); ax[0].set_ylabel("i_C (A)"); ax[0].grid(True)
ax[1].plot(tp,v); ax[1].set_ylabel("v_Cfly (V)"); ax[1].grid(True)
ax[2].plot(tp,vo); ax[2].set_ylabel("V_out (V)"); ax[2].set_xlabel("t (us)"); ax[2].grid(True)
ax[0].set_title(f"TB-A1 nominal: Vin=788 V, I_ph=46.9 A, fs=fr={fr/1e3:.1f} kHz, tdead=100 ns")
fig.tight_layout(); fig.savefig(f"{FIG}/tba1_nominal_waveforms.png",dpi=140); plt.close(fig)
# zoom on a switching instant
fig,ax=plt.subplots(figsize=(7,3.2)); mm=tp<14
ax.plot(tp[mm],i[mm],label="i_C"); ax2=ax.twinx(); ax2.step(tp[mm],s[mm],where="post",color="C3",alpha=0.5,label="state")
ax.set_xlabel("t (us)"); ax.set_ylabel("i_C (A)"); ax2.set_ylabel("state (0 dead,1,2)"); ax.grid(True)
fig.tight_layout(); fig.savefig(f"{FIG}/tba1_zoom.png",dpi=140); plt.close(fig)

# sweep 1: fs/fr
sw1=[]
for fr_ in [0.90,0.95,0.97,1.00,1.03,1.05,1.10]:
    r,_=simulate(fratio=fr_); sw1.append(r); print("fratio",fr_, round(r["zcs_ratio"],3), round(r["Ploss"],1), round(r["eta"]*100,3), round(r["Ipk"],1), round(r["swing"],1))
res["sweep_fratio"]=sw1
# sweep 2: load
sw2=[]
for I in [5.,12.5,25.,46.875,60.]:
    r,_=simulate(Iload=I); sw2.append(r); print("load",I, round(r["zcs_ratio"],3), round(r["Ploss"],1), round(r["eta"]*100,3), round(r["Ipk"],1), round(r["Rout"]*1e3,2))
res["sweep_load"]=sw2
# sweep 3: Vin
sw3=[]
for V in [648.,788.,920.]:
    r,_=simulate(Vin=V); sw3.append(r); print("Vin",V, round(r["zcs_ratio"],3), round(r["Ploss"],1), round(r["eta"]*100,3), round(r["Vout"],1))
res["sweep_vin"]=sw3
# sweep 4: dead time
sw4=[]
for td in [50e-9,100e-9,200e-9,400e-9]:
    r,_=simulate(tdead=td); sw4.append(r); print("tdead",td, round(r["zcs_ratio"],3), round(r["Pdiode"],2), round(r["Ploss"],1))
res["sweep_tdead"]=sw4
# figure: fratio sweep
fig,ax=plt.subplots(1,2,figsize=(10,3.5))
fx=[r["fratio"] for r in sw1]
ax[0].plot(fx,[r["zcs_ratio"]*100 for r in sw1],"o-"); ax[0].axhline(5,color="r",ls="--",label="ZCS limit 5 %"); ax[0].set_xlabel("fs/fr"); ax[0].set_ylabel("|i| at switching / Ipk (%)"); ax[0].grid(True); ax[0].legend()
ax[1].plot(fx,[r["Ploss"] for r in sw1],"s-"); ax[1].axhline(59*1.3,color="r",ls="--",label="pass limit 76.7 W"); ax[1].set_xlabel("fs/fr"); ax[1].set_ylabel("loss per phase (W)"); ax[1].grid(True); ax[1].legend()
fig.tight_layout(); fig.savefig(f"{FIG}/tba1_fratio_sweep.png",dpi=140); plt.close(fig)
json.dump(res,open("results/tba1_results.json","w"),indent=1,default=float)
print("fr =",fr)
