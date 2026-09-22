"""tb_b_pprc3.py -- PPRC series-path averaged model, v2 (review fix 2026-09-21).
Changes vs tb_b_pprc2.py (kept for history):
  (1) POWER BALANCE: the DAB primary is fed from the 400 V bus, so the bus equation includes the DAB input current
        i_in = (v_ser*i_dab)/(eta_dir * v_bus)  (eta = 0.96 when power flows bus->series port, 1/0.96 when it returns)
  (2) PPRC realised as DAB (400 V <-> 100 V unipolar link, 8 kW, i_link <= 80 A) + 4-quadrant H-bridge series port
      (v_ser in [-90,+90] V, i_path <= 100 A). The averaged actuator is the H-bridge current into C_ser; the DAB link
      supplies v_ser*i_path (<= 8 kW). Limits applied: |i_act| <= 100 A, |v_ser*i_act| <= 8 kW.
  (3) Steady-state PPRC power/current table from the true balance V_m*i_path = P_load + R*i_path^2 + P_dab_in ...
"""
import numpy as np, json, scipy.signal as sg
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"; R_A=10.2e-3; R_p=3e-3; tau=10e-6; d_dab=5e-6; Ts=5e-6; eta_dab=0.96; P_pprc=8e3
def design(L,Cs,Cb,f_bw=8e3,zeta=0.7):
    A=np.array([[-(R_A+R_p)/L,1/L,-1/L,0],[-1/Cs,0,0,1/Cs],[1/Cb,0,0,0],[0,0,0,-1/tau]]); B=np.array([[0],[0],[0],[1/tau]])
    Aa=np.zeros((5,5)); Aa[:4,:4]=A; Aa[4,2]=-1; Ba=np.zeros((5,1)); Ba[:4]=B; w=2*np.pi*f_bw
    return sg.place_poles(Aa,Ba,np.array([-zeta*w+1j*w*np.sqrt(1-zeta**2),-zeta*w-1j*w*np.sqrt(1-zeta**2),-w,-w/3,-2*np.pi*20e3])).gain_matrix[0]
def steady(Vbat,P,Vbus=400.):
    """solve V_m*i = P + R*i^2 + P_dab_in with P_dab_in = v_ser*i/eta (v_ser>0) or v_ser*i*eta (v_ser<0); v_ser = Vbus - V_m + R*i"""
    # path: V_m*i + v_ser*i - R*i^2 = V_bus*i ; bus: V_bus*i = P + P_dab_in ; P_dab_in = v_ser*i/eta (v_ser>0) or v_ser*i*eta (v_ser<0)
    # => V_m*i - R*i^2 = P + v_ser*i*(1/eta-1)  [v_ser>0]   or   P + v_ser*i*(eta-1)  [v_ser<0]
    Vm=Vbat/2; R=R_A+R_p; i=P/Vbus
    for _ in range(50):
        vs=Vbus-Vm+R*i; loss=vs*i*(1/eta_dab-1) if vs>0 else vs*i*(eta_dab-1)
        i=(P+R*i**2+loss)/Vm
    vs=Vbus-Vm+R*i; Pd=vs*i; Pin=Pd/eta_dab if Pd>0 else Pd*eta_dab
    return dict(i_path=i,v_ser=vs,P_pprc=Pd,i_dab_in=Pin/Vbus,ratio=abs(Pd)/P)
def simulate(K,L,Cs,Cb,Vbat=788.,dI=60.,t_step=1e-3,tend=2.5e-3,dt=0.1e-6,P0=5e3,Isat=100.,vref=400.):
    n=int(tend/dt); t=np.arange(n)*dt; ss=steady(Vbat,P0)
    ip=ss["i_path"]; vs=ss["v_ser"]; vb=vref; idab=ip
    q=-(ip+K[:4]@np.array([ip,vs,vb,idab]))/K[4]; dbuf=np.zeros(int(d_dab/dt)+1)+ip; cmd=ip; kc=int(Ts/dt); log=np.zeros((n,5))
    for k in range(n):
        tt=t[k]; Pload=P0+400.*dI*(tt>=t_step); il=Pload/vb
        if k%kc==0:
            u=-K[:4]@np.array([ip,vs,vb,idab])-K[4]*q
            u=np.clip(u,-Isat,Isat)
            if abs(vs)>1e-3: u=np.clip(u,-P_pprc/abs(vs),P_pprc/abs(vs))     # DAB link power limit
            cmd=u; q+=Ts*(vref-vb)+0.05*(cmd-(-K[:4]@np.array([ip,vs,vb,idab])-K[4]*q))/(-K[4])
        dbuf=np.roll(dbuf,1); dbuf[0]=cmd; u=dbuf[-1]
        Pd=vs*idab; iin=(Pd/eta_dab if Pd>0 else Pd*eta_dab)/vb          # DAB primary current drawn from bus (fix 1)
        dip=(Vbat/2-(R_A+R_p)*ip+vs-vb)/L; dvs=(idab-ip)/Cs; dvb=(ip-il-iin)/Cb; did=(u-idab)/tau
        ip+=dt*dip; vs+=dt*dvs; vb+=dt*dvb; idab+=dt*did; log[k]=(vb,ip,idab,vs,iin)
    m=t>=t_step; droop=400.-log[m,0].min(); ok=np.abs(log[:,0]-400.)<=4.0; rec=None
    for k in range(int(t_step/dt),n):
        if ok[k:].all(): rec=t[k]-t_step; break
    return dict(droop=droop,rec=rec,ipk=np.abs(log[:,2]).max(),Ppk=np.abs(log[:,3]*log[:,2]).max(),t=t,log=log)
if __name__=="__main__":
    out={}
    print("Steady-state PPRC balance at 25 kW (fix 1):")
    for V in [640.,648.,788.,907.,920.]:
        s=steady(V,25e3); out[f"ss_{int(V)}"]=s; print(f"  V_bat {V:.0f}: i_path {s['i_path']:.1f} A, v_ser {s['v_ser']:+.1f} V, P_pprc {s['P_pprc']/1e3:+.2f} kW ({s['ratio']*100:.1f} % of 25 kW), DAB bus current {s['i_dab_in']:+.1f} A")
    L=1.5e-6; Cs=100e-6; Cb=400e-6; K=design(L,Cs,Cb,8e3)
    print("TB-S1 (fix 1, 8 kHz, 60 A step, P0 5 kW):")
    for V in [648.,788.,907.]:
        r=simulate(K,L,Cs,Cb,Vbat=V); out[f"s1_{int(V)}"]=dict(droop=r["droop"],rec=r["rec"],ipk=r["ipk"],Ppk=r["Ppk"])
        print(f"  V_bat {V:.0f}: droop {r['droop']:.2f} V, recovery {r['rec']*1e6 if r['rec'] else float('nan'):.0f} us, i_act peak {r['ipk']:.1f} A, PPRC power peak {r['Ppk']/1e3:.2f} kW")
    # headroom cliff at 648 V with 25 kW base? (worst case): base 20 kW then step
    for dI in [20,30,40]:
        r=simulate(K,L,Cs,Cb,Vbat=648.,dI=dI,P0=20e3,tend=3e-3); print(f"  648 V, base 20 kW, +{dI} A: droop {r['droop']:.1f} V, i_act pk {r['ipk']:.0f} A, P pk {r['Ppk']/1e3:.1f} kW, rec {r['rec']}")
        out[f"cliff648_{dI}"]=dict(droop=r["droop"],ipk=r["ipk"],Ppk=r["Ppk"],rec=r["rec"])
    json.dump(out,open("results/tbb3_powerbalance.json","w"),indent=1,default=float)
