import numpy as np, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "DejaVu Sans"
out = {}
FIG = "../docs/fig"
import os; os.makedirs(FIG, exist_ok=True)

# ---------------------------------------------------------------- 1. System
Ns = 216; Vcell_min, Vcell_nom, Vcell_max = 3.0, 3.65, 4.2
Vbat_min, Vbat_nom, Vbat_max = Ns*Vcell_min, Ns*Vcell_nom, Ns*Vcell_max
Vbat_abs = 920.0   # design-abs max incl. balancing/OCV overshoot margin
out["bat"] = dict(Ns=Ns, Vmin=Vbat_min, Vnom=Vbat_nom, Vmax=Vbat_max)
Vbus = 400.0
P_chg = 150e3; I_chg_bus = P_chg/Vbus; I_chg_bat = P_chg/(2*Vbus)
P_aux_max = 25e3; I_aux = P_aux_max/Vbus
out["sys"] = dict(I_chg_bus=I_chg_bus, I_chg_bat=I_chg_bat, I_aux=I_aux)

# ---------------------------------------------------------------- 2. Stage A (2:1 resonant SC)
# module: 37.5 kW, 2 interleaved phases
Nmod = 4; Pmod = P_chg/Nmod; Iout_mod = Pmod/Vbus
Nph = 2; Iout_ph = Iout_mod/Nph          # avg output current per phase (A)
# For the 2:1 ladder cell each phase's flying cap carries half-sine current in BOTH half periods,
# and the OUTPUT current of one phase = 2 x flying-cap average? No: in phase-1 (charge) the input current
# = i_fly and flows to output; in phase-2 (discharge) i_fly flows to output. Output current per cell = i_fly(avg over both halves) = Iout_ph
# So the flying-cap current is a full-wave rectified sine of average Iout_ph -> peak = pi/2 * Iout_ph
Ipk_ph = np.pi/2*Iout_ph
Irms_sw = Ipk_ph/2            # each switch conducts one half-sine per period -> rms over T = Ipk/2
Irms_cap = Ipk_ph/np.sqrt(2)  # continuous full-wave rectified sine
Vsw = Vbat_abs/2              # switch blocking = Vin/2 in 2:1 ladder
# device: SiC 750 V, Rds_on 12 mOhm @Tj=125C, two in parallel per switch
Rds_die = 12e-3; Npar = 2; Rds = Rds_die/Npar
Eoss_400 = 12e-6              # J per device @ 400 V (typ 650-750V SiC, Coss_er ~150 pF -> 0.5*150p*400^2=12uJ)
Eoss_sw = Eoss_400*Npar
ESR_cap = 1.5e-3; R_L = 1.0e-3
def stageA_loss(fs, Iout_ph, dVc_ratio=0.05):
    Q = Iout_ph/(2*fs)            # charge per half period
    Cfly = Q/(dVc_ratio*Vbus)     # cap swing = 5% of 400 V
    Lr = 1/((2*np.pi*fs)**2*Cfly)
    Ipk = np.pi/2*Iout_ph
    Pcond = 4*(Ipk/2)**2*Rds      # 4 switches per phase
    Pcap  = (Ipk/np.sqrt(2))**2*ESR_cap
    Pind  = (Ipk/np.sqrt(2))**2*R_L
    Psw   = 4*Eoss_sw*fs          # ZCS: Coss energy dissipated at turn-on (conservative, 100%)
    Pgate = 4*Npar*1.0e-6*fs      # Qg~60 nC x 15 V ~ 1 uJ per device per cycle
    Pmisc = (Ipk/np.sqrt(2))**2*1.5e-3   # busbar/PCB/contacts 1.5 mOhm per phase path
    return dict(Cfly=Cfly, Lr=Lr, Ipk=Ipk, Pcond=Pcond, Pcap=Pcap, Pind=Pind, Psw=Psw, Pgate=Pgate, Pmisc=Pmisc,
                Pfixed=Psw+Pgate, Ptot=Pcond+Pcap+Pind+Psw+Pgate+Pmisc)
fs_list = np.array([50e3,100e3,150e3,200e3,300e3,400e3])
sweepA = []
for fs in fs_list:
    r = stageA_loss(fs, Iout_ph)
    Pph = Pmod/Nph
    eta = 1 - r["Ptot"]/Pph
    Ecap = 0.5*r["Cfly"]*Vbus**2   # stored energy proxy for cap volume
    EL   = 0.5*r["Lr"]*r["Ipk"]**2
    sweepA.append(dict(fs=fs, Cfly=r["Cfly"], Lr=r["Lr"], Ptot=r["Ptot"], eta=eta, Ecap=Ecap, EL=EL,
                       Pcond=r["Pcond"], Psw=r["Psw"], Pcap=r["Pcap"], Pind=r["Pind"]))
out["stageA_sweep"] = sweepA
fsA = 150e3
rA = stageA_loss(fsA, Iout_ph)
Ploss_mod = rA["Ptot"]*Nph
Rout_mod = Ploss_mod/Iout_mod**2
Rout_sys = Rout_mod/Nmod
eta_A_full = 1 - Ploss_mod/Pmod
# efficiency vs load (per module)
loads = np.linspace(0.05,1,20)
etaA_load=[]
for L in loads:
    r = stageA_loss(fsA, Iout_ph*L)
    etaA_load.append(1 - r["Ptot"]*Nph/(Pmod*L))
out["stageA"] = dict(Nmod=Nmod, Pmod=Pmod, Nph=Nph, Iout_ph=Iout_ph, Ipk=rA["Ipk"], Irms_sw=Irms_sw,
                     Vsw=Vsw, util_750=Vsw/750, util_650=Vsw/650, fs=fsA, Cfly=rA["Cfly"], Lr=rA["Lr"],
                     Ploss_mod=Ploss_mod, eta_full=eta_A_full, Rout_mod=Rout_mod, Rout_sys=Rout_sys,
                     Pcond=rA["Pcond"], Psw=rA["Psw"], Pcap=rA["Pcap"], Pind=rA["Pind"], Pgate=rA["Pgate"],
                     loads=loads.tolist(), eta_load=etaA_load,
                     Vdrop_chg=Rout_sys*I_chg_bus, Vdrop_aux=Rout_sys*I_aux)
# inrush: if Cfly precharged to 0 and connected at Vbat/2 through Lr: peak = V*sqrt(C/L)
Zr = np.sqrt(rA["Lr"]/rA["Cfly"])
out["stageA"]["Zr"]=Zr; out["stageA"]["I_inrush_nopre"]=Vsw/Zr
# ---------------------------------------------------------------- 3. Stage B PPRC
VA_mid = np.array([Vbat_min, Vbat_nom, Vbat_max])/2
dV = Vbus - VA_mid   # series voltage required (drive mode, no load droop)
# include Stage A droop at aux current: V_A = Vbat/2 - I*Rout
dV_aux = Vbus - (np.array([Vbat_min, Vbat_nom, Vbat_max])/2 - I_aux*Rout_sys)
kpr = np.abs(dV_aux)/Vbus
P_pprc_drive = np.abs(dV_aux)*I_aux
out["stageB"] = dict(VA_mid=VA_mid.tolist(), dV=dV.tolist(), dV_aux=dV_aux.tolist(), kpr=kpr.tolist(),
                     P_pprc_drive=P_pprc_drive.tolist())
# sweep Vbat 650..920
Vb = np.linspace(Vbat_min, Vbat_abs, 50)
dV_sw = Vbus - (Vb/2 - I_aux*Rout_sys)
out["stageB"]["sweep_Vb"]=Vb.tolist(); out["stageB"]["sweep_dV"]=dV_sw.tolist()
out["stageB"]["sweep_P"]=(np.abs(dV_sw)*I_aux).tolist()
# PPRC rating decision: 8 kW, series voltage +/-90 V design, current 100 A (drive), DAB 400V->~100V
P_pprc = 8e3; Vser_max = 90.0; Iser_max = 100.0
n_dab = 4.0   # 400 : 100
fs_dab = 200e3
# DAB Ls sizing: P = V1*V2/(n*2*pi*fs*Ls) * phi*(1-phi/pi) ; max at phi=pi/2 -> V1*V2/(8 fs Ls n)
V1=400.; V2=100.
Ls = V1*V2/(8*fs_dab*P_pprc)/n_dab* n_dab  # referred to primary with n: P = n*V1*V2'... use P=V1*(n*V2)/(8 fs L)
Ls = V1*(n_dab*V2)/(8*fs_dab*P_pprc)  # primary-referred, at phi=pi/2
# choose operating phi_max = pi/3 (0.33 of pi) for margin -> Ls smaller
phi_op = np.pi/3
Ls_op = V1*(n_dab*V2)*phi_op*(1-phi_op/np.pi)/(2*np.pi*fs_dab*P_pprc)
# series cell conduction (low-voltage GaN 200 V, 4 mOhm die, x4 parallel)
R200 = 4e-3/4
Pser_cond_drive = I_aux**2*(2*R200)      # two switches in path at any time
Pser_cond_chg   = I_chg_bus**2*(2*R200)
# transformer secondary winding 0.3 mOhm
Rsec = 0.3e-3
out["stageB"].update(dict(P_pprc=P_pprc, Vser_max=Vser_max, Iser_max=Iser_max, n_dab=n_dab, fs_dab=fs_dab,
      Ls_phi90=Ls, Ls_phi60=Ls_op, Pser_cond_drive=Pser_cond_drive, Pser_cond_chg=Pser_cond_chg,
      Pser_cond_chg_pct=Pser_cond_chg/P_chg, Psec_chg=I_chg_bus**2*Rsec))
# PPRC efficiency model: DAB eta 96%, processed power = |dV|*I -> system loss at drive mode
eta_dab=0.96
def stageA_drive_loss(P):
    # phase shedding: 1 module (2 phases) active in drive mode
    Iph = P/Vbus/Nph
    r = stageA_loss(fsA, Iph)
    return r["Ptot"]*Nph
def drive_eff(Vbat, P):
    I=P/Vbus
    VA = Vbat/2 - I*Rout_mod
    dv = Vbus - VA
    Ppp = abs(dv)*I
    PA = stageA_drive_loss(P)
    Pdab_fixed = 15.0   # DAB idle/gate/core loss floor
    Ploss = PA + Ppp*(1-eta_dab) + Pdab_fixed + I**2*(2*R200+Rsec)
    return 1 - Ploss/P, Ppp/P
eff_drive = {str(int(v)):[drive_eff(v,P) for P in [3e3,5e3,10e3,25e3]] for v in [Vbat_min,Vbat_nom,Vbat_max]}
out["stageA_drive_loss"]={str(P):stageA_drive_loss(P) for P in [3e3,5e3,10e3,25e3]}
out["stageA_allmod_loss_light"]={str(P):stageA_loss(fsA,P/Vbus/(Nmod*Nph))["Ptot"]*Nmod*Nph for P in [3e3,5e3]}
out["stageB"]["eff_drive"]=eff_drive
# ---------------------------------------------------------------- 4. C_ser / droop  (series PPRC transient)
# droop dV = dI * t_resp / C_ser (bus cap contributes but C_ser << C_bus and path R small)
dI_list = np.array([12.5, 25., 60.])
Cser_list = np.array([50e-6, 100e-6, 200e-6, 470e-6, 1000e-6])
t_resp_list = np.array([30e-6, 60e-6, 100e-6, 200e-6])
droop = {}
for dI in dI_list:
    for tr in t_resp_list:
        droop[f"dI{dI:.1f}_tr{tr*1e6:.0f}"] = (dI*tr/Cser_list).tolist()
out["droop"]=dict(dI=dI_list.tolist(), Cser=Cser_list.tolist(), t_resp=t_resp_list.tolist(), table=droop)
# combined with C_bus: effective: the bus node also has C_bus; transient current splits per impedance;
# rigorous: C_ser in series with source (stiff), C_bus shunt. dV_bus(t)= dI*t/(C_bus + C_ser)?? No:
# charge conservation: dI flows partly from C_bus (shunt) and partly through path (which discharges C_ser).
# Path current i_p: V_A + v_ser - i_p*R = v_bus.  d(v_ser)/dt = -i_p/C_ser ; C_bus dv_bus/dt = i_p - dI
# For R->0: v_bus = V_A + v_ser => dv_bus/dt = dv_ser/dt = -i_p/C_ser ; C_bus*(-i_p/C_ser) = i_p - dI
# -> i_p = dI*C_ser/(C_ser+C_bus) ... => dv_bus/dt = -dI/(C_ser+C_bus).  So caps add (series path stiff)
# Good: with C_bus=400uF, C_ser=100uF -> dv/dt = dI/500uF.
C_bus = 400e-6
def droop_bus(dI, tr, Cser, Cb=C_bus):
    return dI*tr/(Cser+Cb)
out["droop"]["with_Cbus"] = {f"dI{dI:.1f}": [droop_bus(dI, tr, 100e-6) for tr in t_resp_list] for dI in dI_list}
out["droop"]["C_bus"]=C_bus
# ARL effect: prediction lead t_lead >= t_resp -> residual droop = |err|*dI*tr/(C)
err_list = np.array([0.1,0.2,0.3,0.5])
out["droop"]["arl_residual_60A_100us"] = {str(e): droop_bus(60*e, 100e-6, 100e-6) for e in err_list}
# pre-boost energy
for pb in [0.01,0.02]:
    Vpb = Vbus*(1+pb)
    E = 0.5*(C_bus+100e-6)*(Vpb**2 - Vbus**2)
    out["droop"][f"preboost_{int(pb*100)}pct_J"]=E
    out["droop"][f"preboost_{int(pb*100)}pct_t_at_60A_us"]=E/(Vbus*60)*1e6
    out["droop"][f"preboost_{int(pb*100)}pct_t_at_25A_us"]=E/(Vbus*25)*1e6
# saturation: PPRC rating vs step
out["droop"]["I_at_Vbat_min_rating"] = P_pprc/abs(Vbus - Vbat_min/2)
# ---------------------------------------------------------------- 5. Stage C CLLC 400 -> 48 V, 3 kW
Vo=48.; Po=3e3; n_c = Vbus/Vo
n_turns = (25,3)
fr=250e3; m=6; Qd=0.4
RL = Vo**2/Po
Rac = 8*n_c**2*RL/np.pi**2
Lr_c = Qd*Rac/(2*np.pi*fr)
Cr_c = 1/((2*np.pi*fr)**2*Lr_c)
Lm_c = m*Lr_c
Im_pk = Vbus/(4*Lm_c*fr)     # magnetizing peak (approx n*Vo/(4 Lm fr) with n*Vo=Vin at gain 1)
Coss_c = 100e-12
t_dead_min = 2*Coss_c*Vbus/Im_pk  # need t_dead >= 2*Coss*Vin/Im (approx)
# FHA gain
def gain(fn, Q, m):
    k = m  # Lm/Lr ratio
    num = 1
    den = np.sqrt((1 + (1/k)*(1-1/fn**2))**2 + (Q*(fn-1/fn))**2)
    return 1/den
fn = np.linspace(0.6,1.6,200)
gains = {f"Q{q}":gain(fn,q,m).tolist() for q in [0.1,0.2,0.4,0.6]}
# with fs tolerance +/-3% around fr : gain deviation
g_tol = {f"Q{q}":[gain(0.97,q,m), gain(1.0,q,m), gain(1.03,q,m)] for q in [0.1,0.2,0.4,0.6]}
# secondary current 3kW/48V=62.5 A avg; rms ~ (pi/(2*sqrt2))*Iavg for half-sine SR ~1.11*Iavg (full-wave)
Io = Po/Vo; Isec_rms = Io*np.pi/(2*np.sqrt(2))
R100 = 2e-3/2   # 100 V GaN 2 mOhm x2
Psr = 2*(Isec_rms/np.sqrt(2))**2*R100   # two SR conduct alternately: each rms = Isec_rms/sqrt2
Ipri_rms = Isec_rms/n_c*1.05
R650 = 50e-3
Ppri = 2*(Ipri_rms/np.sqrt(2))**2*R650*2   # 4 switches, 2 conduct
Pxfmr = 0.012*Po; Pcore=10.; Pgate_c=4.; Pcr=3.
Pc_tot = Psr+Ppri+Pxfmr+Pcore+Pgate_c+Pcr
Rout_c = 8e-3  # referred output resistance estimate (Rds + winding), V
out_reg = Io*Rout_c
out["stageC"]=dict(n=n_c, turns=n_turns, fr=fr, m=m, Q=Qd, RL=RL, Rac=Rac, Lr=Lr_c, Cr=Cr_c, Lm=Lm_c,
                   Im_pk=Im_pk, t_dead_min=t_dead_min, gain_tol=g_tol, Io=Io, Isec_rms=Isec_rms,
                   Psr=Psr, Ppri=Ppri, Pxfmr=Pxfmr, Pcore=Pcore, Ploss=Pc_tot, eta=1-Pc_tot/Po, load_reg_V=out_reg,
                   fn=fn.tolist(), gains=gains)
# 12 V: 48->12 buck 1.5 kW, 4-phase, 100 V GaN
out["stage12"]=dict(P=1.5e3, Io=125., phases=4, Iph=31.25, eta_est=0.965)
# ---------------------------------------------------------------- 6. Bus capacitor
# ripple: Stage A 2 phase x 4 modules interleaved at 150 kHz -> effective 8*150k=1.2 MHz ripple, small.
# hold-up for mode transition: allow 400->380 V (5%) for 2 ms at 25 kW
L_path=1.5e-6
R_cpl = -Vbus**2/P_aux_max
C_cpl_min = L_path/R_cpl**2      # Middlebrook-type damping: C > L/R^2 (sufficient condition)
C_eff = 100e-6*C_bus/(100e-6+C_bus)
f_res = 1/(2*np.pi*np.sqrt(L_path*C_eff))
BW_max = f_res/3
t_resp_phys = 0.35/BW_max
out["bus"]=dict(C_bus=C_bus, R_cpl=R_cpl, C_cpl_min=C_cpl_min, E_bus=0.5*C_bus*Vbus**2, L_path=L_path,
                C_eff=C_eff, f_res=f_res, BW_max=BW_max, t_resp_phys=t_resp_phys,
                droop60_full=droop_bus(60,t_resp_phys,100e-6,C_bus), droop60_half=droop_bus(60,t_resp_phys,50e-6,200e-6),
                droop60_quarter=droop_bus(60,t_resp_phys,25e-6,100e-6),
                film_vol_cm3_400uF=0.5*C_bus*Vbus**2/0.08)
# ---------------------------------------------------------------- 7. Baseline comparison
eta_dab_full = 0.97   # 150 kW full-power DAB booster (SiC), typical peak 97-98
eta_llc_wide = 0.94   # wide-range 800->48 V LLC APM
eta_hv_aux_conv = 0.965 # 800->400 V regulated (baseline)
comp = {}
# charge mode 150 kW at 400 V
P_loss_base_chg = P_chg*(1-eta_dab_full)
P_loss_prism_chg = P_chg*(1-eta_A_full) + 0.0  # PPRC bypassed; contactor 0.2 mOhm
P_loss_prism_chg += I_chg_bus**2*0.2e-3
comp["chg150kW"]=dict(base=P_loss_base_chg, prism=P_loss_prism_chg,
                      eta_base=1-P_loss_base_chg/P_chg, eta_prism=1-P_loss_prism_chg/P_chg)
# drive mode aux 5 kW at Vbat nom
e5, kp5 = drive_eff(Vbat_nom, 5e3)
e3, kp3 = drive_eff(Vbat_nom, 3e3)
comp["aux5kW"]=dict(eta_base=eta_hv_aux_conv, eta_prism=e5, loss_base=5e3*(1-eta_hv_aux_conv), loss_prism=5e3*(1-e5))
e25, kp25 = drive_eff(Vbat_min, 25e3)
comp["aux25kW_Vmin"]=dict(eta_base=eta_hv_aux_conv, eta_prism=e25, kpr=kp25)
# 48 V 3 kW
eta48_prism = e5*(1-Pc_tot/Po)
comp["v48_3kW"]=dict(eta_base=eta_llc_wide, eta_prism=eta48_prism, loss_base=3e3*(1-eta_llc_wide), loss_prism=3e3*(1-eta48_prism))
# magnetics VA
VA_base = 150e3 + 5e3 + 25e3   # DAB xfmr 150 kVA + APM 5 kVA + 800->400 converter inductor ~25 kVA
VA_prism = P_pprc + 3.5e3 + 8*0.5*rA["Lr"]*rA["Ipk"]**2*fsA*2  # PPRC xfmr + CLLC + Lr energy*f proxy
comp["magnetics_VA"]=dict(base=VA_base, prism=VA_prism, reduction=1-VA_prism/VA_base)
# drive-cycle energy: aux avg 3 kW for 1 h/100 km => 3 kWh; saving
sav = 3e3*((1-eta_hv_aux_conv)-(1-e3))*1  # W over 1 h at 3 kW avg aux
comp["energy_100km_Wh"]=sav
comp["aux3kW"]=dict(eta_base=eta_hv_aux_conv,eta_prism=e3)
out["comp"]=comp

# ---------------------------------------------------------------- figures
# Fig1: Stage A sweep
fig,ax=plt.subplots(1,2,figsize=(10,3.6))
ax[0].plot(fs_list/1e3,[s["eta"]*100 for s in sweepA],"o-"); ax[0].set_xlabel("fs (kHz)"); ax[0].set_ylabel("Stage A efficiency (%)"); ax[0].grid(True)
ax[1].plot(fs_list/1e3,[s["Cfly"]*1e6 for s in sweepA],"s-",label="Cfly (uF)")
ax2=ax[1].twinx(); ax2.plot(fs_list/1e3,[s["Lr"]*1e9 for s in sweepA],"^-",color="C1",label="Lr (nH)")
ax[1].set_xlabel("fs (kHz)"); ax[1].set_ylabel("Cfly (uF)"); ax2.set_ylabel("Lr (nH)"); ax[1].grid(True)
fig.tight_layout(); fig.savefig(f"{FIG}/fig1_stageA_sweep.png",dpi=140); plt.close(fig)
# Fig2: PPRC required voltage & power vs Vbat
fig,ax=plt.subplots(figsize=(6,3.6))
ax.plot(Vb,dV_sw,label="required series voltage (V)"); ax.set_xlabel("Vbat (V)"); ax.set_ylabel("ΔV (V)"); ax.grid(True)
ax2=ax.twinx(); ax2.plot(Vb,np.abs(dV_sw)*I_aux/1e3,"C1--",label="PPRC power @25 kW aux (kW)"); ax2.set_ylabel("P_PPRC (kW)")
ax.axhline(0,color="k",lw=0.5); fig.legend(loc="upper center",ncol=2,fontsize=8); fig.tight_layout(); fig.savefig(f"{FIG}/fig2_pprc_range.png",dpi=140); plt.close(fig)
# Fig3: droop vs Cser
fig,ax=plt.subplots(figsize=(6,3.6))
for tr in t_resp_list:
    ax.plot(Cser_list*1e6,[droop_bus(60,tr,c) for c in Cser_list],"o-",label=f"t_resp={tr*1e6:.0f} us")
ax.axhline(8,color="r",ls="--",label="2% limit (8 V)"); ax.set_xscale("log"); ax.set_xlabel("C_ser (uF), C_bus=400 uF"); ax.set_ylabel("bus droop for 60 A step (V)"); ax.grid(True,which="both"); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(f"{FIG}/fig3_droop.png",dpi=140); plt.close(fig)
# Fig4: CLLC gain
fig,ax=plt.subplots(figsize=(6,3.6))
for q in [0.1,0.2,0.4,0.6]: ax.plot(fn,gain(fn,q,m),label=f"Q={q}")
ax.axvspan(0.97,1.03,color="y",alpha=0.3,label="±3% fs window"); ax.set_xlabel("fn = fs/fr"); ax.set_ylabel("gain"); ax.grid(True); ax.legend(fontsize=8); ax.set_ylim(0.5,1.6)
fig.tight_layout(); fig.savefig(f"{FIG}/fig4_cllc_gain.png",dpi=140); plt.close(fig)
# Fig5: Stage A eta vs load
fig,ax=plt.subplots(figsize=(6,3.4))
ax.plot(loads*100,np.array(etaA_load)*100,"o-"); ax.set_xlabel("load (%)"); ax.set_ylabel("Stage A efficiency (%)"); ax.grid(True)
fig.tight_layout(); fig.savefig(f"{FIG}/fig5_stageA_eta_load.png",dpi=140); plt.close(fig)
json.dump(out, open("results/design_calc_results.json","w"), indent=1, default=float)
print(json.dumps({k:v for k,v in out.items() if k not in ("stageA_sweep",)}, indent=1, default=lambda o: round(float(o),6) if isinstance(o,(np.floating,float)) else str(o))[:12000])
