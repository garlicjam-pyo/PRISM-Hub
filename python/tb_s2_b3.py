"""TB-S2: 400 V fast charge 150 kW CC-CV through Stage A array (4 modules, R_out 2.6 mOhm), PPRC bypassed.
Charger: current-controlled source, CC ramp 20 A/s? (too slow for sim) -> use 20 A/ms ramp to 375 A (worst case for transient),
current loop BW 100 Hz (1st order), CV when battery reaches 907 V. Battery: 216s pack, OCV(SoC) linear 648->907 V from 0->100 %,
R_int 60 mOhm, capacity 80 kWh -> C = 80e3/788 = 101 Ah. Default 20 s at SoC 95.5% to show power-limited CC->CV.
TB-B3: Drive->Chg400 transition sequence on the series-path model: PPRC phi->0 ramp (v_ser -> 0 over 2 ms), bypass close, PPRC off;
       and reverse. Metrics: bus deviation, series current surge.
"""
import numpy as np, json, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"

def tb_s2(SoC0=0.955, tend=20.0, dt=1e-4, I_cc=375., ramp=20e3, Vmax=907., R_int=0.06, R_out_arr=2.6e-3, C_bus=400e-6, Rbyp=0.2e-3, Ah=101., P_max=150e3):
    """Ideal charger with current/power envelope; C_bus dynamics are not modeled."""
    n=int(tend/dt); t=np.arange(n)*dt
    soc=SoC0; ocv=lambda s: 648+(907-648)*s
    i_chg=0.; i_ref_cc=0.; tau_loop=1/(2*np.pi*100.)
    log=np.zeros((n,6)); cv=False
    for k in range(n):
        vb_ocv=ocv(soc); i_bat=i_chg/2                        # 2:1 fixed ratio: battery current = half of charger current
        v_bat=vb_ocv+R_int*i_bat
        v_A=v_bat/2 + i_chg*(R_out_arr+Rbyp)                 # charger terminal (bus) voltage = battery/2 + drops (charging: bus above V_bat/2)
        # charger: CC with ramp, switch to CV when v_bat >= Vmax (charger regulates its terminal to hold v_bat = Vmax)
        if v_bat>=Vmax: cv=True
        if not cv: i_ref=min(I_cc, i_ref_cc+ramp*dt); i_ref_cc=i_ref
        else:      # CV: reduce current to hold v_bat = Vmax: i_bat_ref = (Vmax - ocv)/R_int
            i_ref=max(0., 2*(Vmax-vb_ocv)/R_int); i_ref=min(i_ref,I_cc)
        # Terminal voltage is a+b*I, so impose the power limit consistently
        # rather than Pmax divided by a stale terminal-voltage sample.
        a=vb_ocv/2; b=R_int/4+R_out_arr+Rbyp
        i_power=2*P_max/(a+np.sqrt(a*a+4*b*P_max))
        i_ref=min(i_ref,i_power)
        i_chg+=dt*(i_ref-i_chg)/tau_loop
        i_chg=np.clip(i_chg,0.,min(I_cc,i_power))  # ideal instantaneous EVSE protection envelope
        v_bat=vb_ocv+R_int*i_chg/2
        v_A=v_bat/2+i_chg*(R_out_arr+Rbyp)
        soc+=dt*(i_chg/2)/(Ah*3600)
        P_loss=i_chg**2*(R_out_arr+Rbyp)+ (i_chg/2)**2*0.0 ; P_in=v_A*i_chg
        log[k]=(v_bat,v_A,i_chg,i_chg/2,soc,P_loss)
    m=log[:,2]>1
    return dict(t=t,log=log,eta_cc=1-np.mean(log[m,5]/(log[m,1]*log[m,2])),v_A_range=(log[:,1].min(),log[:,1].max()),t_cv=t[np.argmax(log[:,0]>=Vmax)] if np.any(log[:,0]>=Vmax) else None)

def tb_b3(Vbat=788., P_aux=5e3, L=1.5e-6, Cs=100e-6, Cb=400e-6, R_A=10.2e-3, R_p=3e-3, Rbyp=0.2e-3, tau=10e-6, dt=0.1e-6):
    """Series path with bypass switch across C_ser (ser_in-ser_out). Sequence (Drive->Chg): t=0.5 ms start ramping v_ser reference to 0 over 2 ms
       (PPRC keeps regulating bus? No: during ramp the bus follows V_A + v_ser -> bus drifts to V_A = 394 V (allowed: charger will regulate later));
       at t=3 ms close bypass (ideal switch with Rbyp), PPRC off (i_dab=0). Reverse (Chg->Drive) at t=6 ms: PPRC on, pre-charge v_ser to (400-V_A) with bypass closed
       (no current flows in C_ser while bypassed... v_ser cannot build) -> instead: open bypass first with v_ser=0 then regulate: bus dips V_A then recovers.
       We quantify both orders."""
    import scipy.signal as sg
    A=np.array([[-(R_A+R_p)/L,1/L,-1/L,0],[-1/Cs,0,0,1/Cs],[1/Cb,0,0,0],[0,0,0,-1/tau]]); B=np.array([[0],[0],[0],[1/tau]])
    Aa=np.zeros((5,5)); Aa[:4,:4]=A; Aa[4,2]=-1; Ba=np.zeros((5,1)); Ba[:4]=B; w=2*np.pi*8e3; z=0.7
    K=sg.place_poles(Aa,Ba,np.array([-z*w+1j*w*np.sqrt(1-z**2),-z*w-1j*w*np.sqrt(1-z**2),-w,-w/3,-2*np.pi*20e3])).gain_matrix[0]
    tend=10e-3; n=int(tend/dt); t=np.arange(n)*dt; Ts=5e-6; kc=int(Ts/dt)
    ip=P_aux/400.; vs=400-(Vbat/2-R_A*ip); vb=400.; idab=ip; q=-(ip+K[:4]@np.array([ip,vs,vb,idab]))/K[4]; cmd=ip
    log=np.zeros((n,5)); byp=False; pprc_on=True; vref=400.
    for k in range(n):
        tt=t[k]
        # sequence
        if 0.5e-3<=tt<3.0e-3: vref=400.-(400.-(Vbat/2-R_A*ip))*min(1.,(tt-0.5e-3)/2.0e-3)   # ramp bus ref toward V_A (v_ser -> 0)
        if tt>=3.0e-3 and tt<6.0e-3: byp=True; pprc_on=False
        if tt>=6.0e-3: byp=False; pprc_on=True; vref=400.-(400.-(Vbat/2-R_A*ip))*max(0.,1-(tt-6.0e-3)/2.0e-3)  # reopen and ramp back to 400
        il=P_aux/vb
        if k%kc==0 and pprc_on:
            u=-K[:4]@np.array([ip,vs,vb,idab])-K[4]*q; cmd=np.clip(u,-100,100); q+=Ts*(vref-vb)
        if not pprc_on: cmd=0.0
        # bypass: ideal switch across C_ser: when closed, v_ser forced ~0 via Rbyp path: model as large conductance discharging C_ser
        i_byp=(vs)/Rbyp if byp else 0.0
        dip=(Vbat/2-(R_A+R_p)*ip+vs-vb)/L; dvs=(idab-ip-i_byp)/Cs; dvb=(ip-il)/Cb; did=(cmd-idab)/tau
        # stiff bypass: clamp vs decay analytically when closed
        if byp: vs*=np.exp(-dt/(Rbyp*Cs)); dvs=(idab-ip)/Cs
        ip+=dt*dip; vs+=dt*dvs; vb+=dt*dvb; idab+=dt*did
        log[k]=(vb,ip,idab,vs,float(byp))
    return dict(t=t,log=log,K=K)

if __name__=="__main__":
    out={}
    r=tb_s2(); L=r["log"]
    cv_label=f"{r['t_cv']:.2f} s" if r['t_cv'] is not None else "not reached"
    print(f"TB-S2: charger terminal (bus) voltage range {r['v_A_range'][0]:.1f}–{r['v_A_range'][1]:.1f} V, CC->CV at t={cv_label}, path efficiency (Stage A + bypass) {r['eta_cc']*100:.2f} %")
    out["tbs2"]=dict(vA_min=r["v_A_range"][0],vA_max=r["v_A_range"][1],t_cv=r["t_cv"],eta=r["eta_cc"])
    fig,ax=plt.subplots(2,1,figsize=(8,5),sharex=True)
    ax[0].plot(r["t"],L[:,0],label="V_bat"); ax[0].plot(r["t"],2*L[:,1],label="2 x V_charger (bus)"); ax[0].axhline(907,color="r",ls="--",label="V_max 907"); ax[0].legend(fontsize=8); ax[0].grid(True); ax[0].set_ylabel("V")
    ax[1].plot(r["t"],L[:,2],label="charger current (400 V side)"); ax[1].plot(r["t"],L[:,3],label="battery current"); ax[1].legend(fontsize=8); ax[1].grid(True); ax[1].set_ylabel("A"); ax[1].set_xlabel("t (s)")
    ax[0].set_title("TB-S2: 150 kW CC-CV through 2:1 array, PPRC bypassed, SoC 95.5 % -> CV"); fig.tight_layout(); fig.savefig(f"{FIG}/tbs2_ccv.png",dpi=140); plt.close(fig)
    # 400 V charger window check across SoC (static)
    for soc in [0.0,0.5,1.0]:
        vb=648+259*soc; vA=vb/2+375*(2.6e-3+0.2e-3)+0.06*187.5/2; print(f"  SoC {soc:.0%}: V_bat_ocv {vb:.0f} V -> charger terminal at 375 A ≈ {vA:.1f} V")
    # TB-B3
    b=tb_b3(); Lb=b["log"]; t=b["t"]
    seg=lambda a,c: (t>=a)&(t<c)
    dev_open=400-Lb[seg(0.5e-3,3e-3),0].min(); vb_at_close=Lb[np.argmax(t>=3e-3),0]; dev_close=np.abs(Lb[seg(3e-3,3.5e-3),0]-Lb[np.argmax(t>=2.99e-3),0]).max()
    surge=np.abs(Lb[seg(2.99e-3,3.5e-3),1]).max(); dev_reopen=np.abs(Lb[seg(6e-3,6.5e-3),0]-Lb[np.argmax(t>=5.99e-3),0]).max(); rec=Lb[seg(8e-3,10e-3),0]
    print(f"TB-B3: ramp-down phase bus goes 400 -> {Lb[np.argmax(t>=2.99e-3),0]:.1f} V (= V_A, by design); at bypass close: bus jump {dev_close:.2f} V, path current peak {surge:.1f} A (aux {5e3/400:.1f} A); at reopen: bus jump {dev_reopen:.2f} V; back to 400 V: {rec[-1]:.1f} V (±{np.ptp(rec):.2f} V)")
    out["tbb3"]=dict(vb_at_close=float(vb_at_close),jump_close=float(dev_close),surge=float(surge),jump_reopen=float(dev_reopen),vb_end=float(rec[-1]))
    fig,ax=plt.subplots(2,1,figsize=(8,5),sharex=True)
    ax[0].plot(t*1e3,Lb[:,0],label="V_bus"); ax[0].plot(t*1e3,Lb[:,3]+394,label="V_A + v_ser (path EMF)",alpha=0.6); ax[0].plot(t*1e3,380+Lb[:,4]*10,label="bypass state (offset)",color="gray"); ax[0].legend(fontsize=8); ax[0].grid(True); ax[0].set_ylabel("V")
    ax[1].plot(t*1e3,Lb[:,1],label="path current"); ax[1].plot(t*1e3,Lb[:,2],label="i_dab"); ax[1].legend(fontsize=8); ax[1].grid(True); ax[1].set_ylabel("A"); ax[1].set_xlabel("t (ms)")
    ax[0].set_title("TB-B3: Drive -> Chg400 (bypass close at 3 ms) -> Drive (reopen at 6 ms), aux 5 kW"); fig.tight_layout(); fig.savefig(f"{FIG}/tbb3_bypass.png",dpi=140); plt.close(fig)
    os.makedirs("results",exist_ok=True); json.dump(out,open("results/tbs2_tbb3_results.json","w"),indent=1,default=float)
