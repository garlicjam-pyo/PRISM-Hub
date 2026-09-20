"""TB-S3 (800 V charging + 400 V aux step), TB-S4 (V2L + 48 V regen inflow, PPRC direction reversal), TB-S5 (battery sweep 600->920 V)
on the series-path average model with state feedback (App. C). V_bat is time-varying here.
"""
import numpy as np, json, scipy.signal as sg
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"; R_A=10.2e-3; R_p=3e-3; tau=10e-6; d_dab=5e-6; Ts=5e-6; L=1.5e-6; Cs=100e-6; Cb=400e-6
def design(f_bw=8e3,zeta=0.7):
    A=np.array([[-(R_A+R_p)/L,1/L,-1/L,0],[-1/Cs,0,0,1/Cs],[1/Cb,0,0,0],[0,0,0,-1/tau]]); B=np.array([[0],[0],[0],[1/tau]])
    Aa=np.zeros((5,5)); Aa[:4,:4]=A; Aa[4,2]=-1; Ba=np.zeros((5,1)); Ba[:4]=B; w=2*np.pi*f_bw
    return sg.place_poles(Aa,Ba,np.array([-zeta*w+1j*w*np.sqrt(1-zeta**2),-zeta*w-1j*w*np.sqrt(1-zeta**2),-w,-w/3,-2*np.pi*20e3])).gain_matrix[0]
def sim(K,vbat_fn,iload_fn,tend,dt=0.2e-6,Isat=100.,P0=5e3):
    n=int(tend/dt); t=np.arange(n)*dt; Vb0=vbat_fn(0.)
    ip=P0/400.; vs=400-(Vb0/2-R_A*ip); vb=400.; idab=ip; q=-(ip+K[:4]@np.array([ip,vs,vb,idab]))/K[4]
    dbuf=np.zeros(int(d_dab/dt)+1)+ip; cmd=ip; kc=int(Ts/dt); log=np.zeros((n,5))
    for k in range(n):
        tt=t[k]; Vbat=vbat_fn(tt); il=iload_fn(tt,vb)
        if k%kc==0:
            u=-K[:4]@np.array([ip,vs,vb,idab])-K[4]*q; cmd=np.clip(u,-Isat,Isat); q+=Ts*(400.-vb)+0.05*(cmd-u)/(-K[4])
        dbuf=np.roll(dbuf,1); dbuf[0]=cmd; u=dbuf[-1]
        ip+=dt*(Vbat/2-(R_A+R_p)*ip+vs-vb)/L; vs+=dt*(idab-ip)/Cs; vb+=dt*(ip-il)/Cb; idab+=dt*(u-idab)/tau
        log[k]=(vb,ip,idab,vs,Vbat)
    return t,log
if __name__=="__main__":
    K=design(); out={}
    # TB-S3: 800 V charger 200 A into battery -> V_bat = 788 + 0.06*200 = 800 V (Rint), aux 10 kW step at 0.3 ms (25 A)
    t,Lg=sim(K,lambda tt:800.,lambda tt,vb:(5e3+10e3*(tt>=0.3e-3))/vb,1.5e-3)
    m=t>=0.3e-3; print(f"TB-S3: V_bat 800 V (800 V charging), aux 10 kW step: droop {400-Lg[m,0].min():.2f} V, v_ser {Lg[-1,3]:.1f} V, PPRC power {abs(Lg[-1,3]*Lg[-1,1]):.0f} W; battery current unaffected (charger CC) by design")
    out["tbs3"]=dict(droop=float(400-Lg[m,0].min()),v_ser=float(Lg[-1,3]))
    # TB-S4: V2L 3.6 kW on (t=0.2 ms, +9 A), then 48 V regen inflow -3 kW at 0.8 ms (-7.5 A on bus) -> PPRC direction of power reverses if dV<0? at 788 V dV=+6.6 V so P_pprc = dV*i_p stays positive unless i_p<0; check i_dab sign and overshoot
    t,Lg=sim(K,lambda tt:788.,lambda tt,vb:(5e3+3.6e3*(tt>=0.2e-3)-3e3*(tt>=0.8e-3))/vb,1.6e-3)
    m=t>=0.8e-3; over=Lg[m,0].max()-400; print(f"TB-S4: V2L +9 A then regen -7.5 A: overshoot {over:.2f} V, i_dab min {Lg[m,2].min():.1f} A, PPRC power sign {'reverses' if (Lg[m,3]*Lg[m,2]).min()<0 else 'stays'}")
    out["tbs4"]=dict(overshoot=float(over),idab_min=float(Lg[m,2].min()))
    # TB-S4b at V_bat 907 V (dV negative: PPRC absorbs): same event
    t,Lg=sim(K,lambda tt:907.,lambda tt,vb:(5e3+3.6e3*(tt>=0.2e-3)-3e3*(tt>=0.8e-3))/vb,1.6e-3)
    print(f"TB-S4 @907 V: v_ser {Lg[-1,3]:.1f} V (absorbing), overshoot {Lg[t>=0.8e-3,0].max()-400:.2f} V")
    # TB-S5: battery sweep 600 -> 920 V over 20 ms (fast to keep sim short; slower ramps are easier), aux 25 kW
    t,Lg=sim(K,lambda tt:600.+320.*min(1.,tt/20e-3),lambda tt,vb:25e3/vb,22e-3,dt=0.5e-6)
    print(f"TB-S5: bus {Lg[:,0].min():.1f}–{Lg[:,0].max():.1f} V, v_ser {Lg[:,3].min():.1f}–{Lg[:,3].max():.1f} V, PPRC power max {np.abs(Lg[:,3]*Lg[:,1]).max()/1e3:.2f} kW (rating 8), i_path {Lg[:,1].max():.1f} A")
    out["tbs5"]=dict(vbus_min=float(Lg[:,0].min()),vbus_max=float(Lg[:,0].max()),vser_min=float(Lg[:,3].min()),vser_max=float(Lg[:,3].max()),Ppprc_max=float(np.abs(Lg[:,3]*Lg[:,1]).max()))
    fig,ax=plt.subplots(2,1,figsize=(8,5),sharex=True)
    ax[0].plot(t*1e3,Lg[:,4]/2,label="V_bat/2"); ax[0].plot(t*1e3,Lg[:,0],label="V_bus"); ax[0].legend(fontsize=8); ax[0].grid(True); ax[0].set_ylabel("V")
    ax[1].plot(t*1e3,Lg[:,3],label="v_ser"); ax[1].plot(t*1e3,Lg[:,3]*Lg[:,1]/1e3*10,label="PPRC power (x10 kW)"); ax[1].legend(fontsize=8); ax[1].grid(True); ax[1].set_xlabel("t (ms)")
    ax[0].set_title("TB-S5: battery 600 -> 920 V sweep at 25 kW aux (compressed to 20 ms)"); fig.tight_layout(); fig.savefig(f"{FIG}/tbs5_sweep.png",dpi=140); plt.close(fig)
    json.dump(out,open("results/tbs3_s5_results.json","w"),indent=1)
