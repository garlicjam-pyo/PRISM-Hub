"""Series PPRC path average model (drive mode, 1 Stage-A module active)
States: i_p (path current through L_path), v_ser (C_ser), v_bus (C_bus), i_dab (DAB output current, lag), PI integrator
  V_A   = Vbat/2 - R_A*i_p
  L dip/dt = V_A + v_ser - v_bus - R_p*i_p
  C_ser dv_ser/dt = i_dab - i_p
  C_bus dv_bus/dt = i_p - i_load(t)          (CPL: i_load = P/v_bus)
  DAB: i_dab -> 1st-order lag tau_dab, plus transport delay d_dab (phase-shift update)
Controller (Ts=5us): i_cmd = Kp*(v_ref - v_bus) + Ki*int(v_ref - v_bus) + i_ff ; saturate +-100 A
"""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"
Vbat=788.; R_A=10.2e-3; R_p=3e-3; tau_dab=10e-6; d_dab=5e-6; Ts=5e-6

def loop_gain(f, Kp, Ki, L, Cs, Cb, RA=R_A, Rp=R_p):
    """analytic loop gain from i_dab command to v_bus with PI, incl. DAB lag+delay. Small-signal, CPL neglected (adds damping-negative small term)."""
    s=2j*np.pi*f
    Zc_s=1/(s*Cs); Zc_b=1/(s*Cb); ZL=s*L+Rp+RA
    # i_dab splits: into C_ser or through path: v_ser node: i_dab = i_Cs + i_p ; i_p = (v_ser - v_bus)/ZL ; v_bus = i_p*Zc_b
    # v_ser = i_Cs*Zc_s ; solve: i_p = (v_ser - i_p Zc_b)/ZL -> v_ser = i_p (ZL+Zc_b) ; i_dab = v_ser/Zc_s + i_p = i_p((ZL+Zc_b)/Zc_s + 1)
    G = Zc_b/((ZL+Zc_b)/Zc_s + 1)             # v_bus / i_dab
    Gdab = np.exp(-s*d_dab)/(1+s*tau_dab)
    C = Kp + Ki/s
    return C*Gdab*G, G

def margins(Kp,Ki,L,Cs,Cb):
    f=np.logspace(2,5.5,4000); T,_=loop_gain(f,Kp,Ki,L,Cs,Cb)
    mag=np.abs(T); ph=np.unwrap(np.angle(T))*180/np.pi
    ic=np.where(np.diff(np.sign(mag-1))!=0)[0]
    fc=f[ic[0]] if len(ic) else np.nan; pm=180+ph[ic[0]] if len(ic) else np.nan
    ipc=np.where(np.diff(np.sign(ph+180))!=0)[0]
    gm=-20*np.log10(mag[ipc[0]]) if len(ipc) else np.inf
    return fc,pm,gm

def design_pi(L,Cs,Cb,target_pm=45,target_gm=6):
    """largest crossover fc with PM>=45 deg and GM>=6 dB; PI zero at fc/4"""
    best=None
    for fc in np.logspace(3,4.3,120):
        wc=2*np.pi*fc; Kp=wc*(Cs+Cb); Ki=Kp*wc/4
        # refine Kp so |T(fc)|=1
        T,_=loop_gain(fc,Kp,Ki,L,Cs,Cb); Kp/=abs(T); Ki=Kp*wc/4
        fcm,pm,gm=margins(Kp,Ki,L,Cs,Cb)
        if pm>=target_pm and gm>=target_gm: best=(fc,Kp,Ki,pm,gm)
    return best

def simulate(Kp,Ki,L,Cs,Cb,dI=60.,t_step=1.0e-3,tend=2.5e-3,ff="none",pred_err=0.0,t_err=0.0,pre_boost=0.0,t_lead=1e-3,
             dt=0.1e-6,P0=5e3,Isat=100.):
    n=int(tend/dt); t=np.arange(n)*dt
    ip=P0/400.; vs=400-(Vbat/2-R_A*ip); vb=400.; idab=ip; integ=ip/Ki if Ki>0 else 0.0   # steady state init (i_dab = i_p)
    v_ref=400.
    dbuf=np.zeros(int(d_dab/dt)+1)+idab; cmd_hold=idab
    log=np.zeros((n,4)); k_ctrl=int(Ts/dt)
    for k in range(n):
        tt=t[k]
        Pload=P0+400.*dI*(tt>=t_step)          # CPL step of dI at 400 V
        iload=Pload/vb
        if k%k_ctrl==0:
            # feedforward variants
            if ff=="B1":   i_ff = (Pload_meas:=P0+400.*dI*(tt-20e-6>=t_step))/vb - P0/400.     # measured, 20 us delay
            elif ff=="B2": i_ff = dI*(tt>=t_step-(tau_dab+d_dab))                               # ideal predictive, timed to actuator delay
            elif ff=="ARL":i_ff = dI*(1-pred_err)*(tt>=t_step-(tau_dab+d_dab)+t_err)           # magnitude & timing error
            else: i_ff=0.0
            vr = v_ref + (pre_boost*min(1.0,max(0.0,(tt-(t_step-t_lead))/(t_lead*0.5))) if (pre_boost>0 and tt<t_step) else 0.0)  # ramp pre-boost, released at step
            if pre_boost>0 and tt>=t_step: vr=v_ref
            e=vr-vb; integ+=e*Ts
            cmd=Kp*e+Ki*integ+i_ff
            cmd=np.clip(cmd,-Isat,Isat); cmd_hold=cmd
        # delay buffer
        dbuf=np.roll(dbuf,1); dbuf[0]=cmd_hold; cmd_d=dbuf[-1]
        # derivatives
        VA=Vbat/2-R_A*ip
        dip=(VA+vs-vb-R_p*ip)/L; dvs=(idab-ip)/Cs; dvb=(ip-iload)/Cb; didab=(cmd_d-idab)/tau_dab
        ip+=dt*dip; vs+=dt*dvs; vb+=dt*dvb; idab+=dt*didab
        log[k]=(vb,ip,idab,vs)
    m=t>=t_step
    droop=400.-log[m,0].min(); over=log[:,0].max()-400.
    # recovery: first time after step where |vb-400|<=4 V and stays
    ok=np.abs(log[:,0]-400.)<=4.0
    rec=None
    for k in range(int(t_step/dt),n):
        if ok[k:].all(): rec=t[k]-t_step; break
    return dict(droop=droop,overshoot=over,rec=rec,ipeak=np.abs(log[:,2]).max(),t=t,log=log)


