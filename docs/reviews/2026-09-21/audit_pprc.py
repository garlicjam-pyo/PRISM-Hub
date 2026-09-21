"""Independent audit of PRISM-Hub 959efdf. Writes audit results beside this script; does not modify the reviewed converter source.
Analytical checks plus selected original Python functions and an explicitly modified,
ideal power-conserving averaged model for sensitivity (not a validated replacement).
"""
from pathlib import Path
import sys, json, math
import numpy as np
ROOT = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO/'python'))
import tb_b_pprc2 as b
import tb_s2_b3 as ch

result = {'commit':'959efdfb8fa504d407309eb9b1217041dd93f15d',
          'environment':{'python':sys.version,'numpy':np.__version__}}

R = .0102 + .003
def equilibrium(vbat, power):
    vm = vbat/2
    # Pload = Vm I - R I^2 for ideal output-fed series compensator.
    current = 2*power/(vm+math.sqrt(vm*vm-4*R*power))
    vs = 400-vm+R*current
    return {'Vbat':vbat,'Pload_W':power,'path_A':current,'vser_V':vs,
            'PPRC_output_W':vs*current,'PPRC_bus_input_A':vs*current/400,
            'ratio_abs':abs(vs*current)/power,
            'battery_input_W':vm*current,'R_loss_W':R*current*current}
result['ideal_power_conserving_equilibria']=[equilibrium(v,p) for v,p in [(648,25000),(788,25000),(907,25000),(600,20000),(640,25000)]]
result['original_model_energy_residual'] = []
for vbat in [648,788,907]:
    il=25000/400; vs=400-vbat/2+R*il
    # Model steady state: ip=idab=il. Missing bus supply = vs*idab.
    result['original_model_energy_residual'].append({'Vbat':vbat,'Pload_W':25000,
        'battery_input_W':vbat/2*il,'R_loss_W':R*il*il,
        'unaccounted_DAB_input_W':vs*il})
phi=math.pi/3
imax=400*4*phi*(1-phi/math.pi)/(2*math.pi*200e3*11.1e-6)
result['SPS_DAB']={'current_max_at_60deg_A':imax,'power_at_V2_90_W':90*imax,
    'power_at_V2_77_W':77*imax,'L_required_100A_at_60deg_uH':400*4*phi*(1-phi/math.pi)/(2*math.pi*200e3*100)*1e6}
result['bypass_bus']=[{'Vbat':v,'Vbus_ideal':v/2,'V48_fixed_gain':v/2*3/25,
    'power_at_375A_W':v/2*375,'input_current_for_150kW_A':150000/(v/2)} for v in [648,788,907,920]]

for fbw in [8000,10000]:
    K=b.design(1.5e-6,100e-6,400e-6,fbw)
    r=b.simulate(K,1.5e-6,100e-6,400e-6)
    result[f'original_B0_{fbw}Hz']={key:float(r[key]) if r[key] is not None else None for key in ['droop','overshoot','rec','ipeak']}

cr=ch.tb_s2()
log=cr['log']; pi=log[:,1]*log[:,2]
result['original_TBS2']={'eta':float(cr['eta_cc']),'t_cv_s':float(cr['t_cv']) if cr['t_cv'] is not None else None,
    'charger_power_max_W':float(pi.max()),'charger_voltage_min_V':float(log[:,1].min()),'charger_voltage_max_V':float(log[:,1].max()),
    'charger_current_max_A':float(log[:,2].max())}
br=ch.tb_b3()
t=br['t']; lg=br['log']
result['original_TBB3']={'vb_min':float(lg[:,0].min()),'vb_end':float(lg[-1,0]),'path_peak_A':float(np.abs(lg[:,1]).max())}

def modified_power_conserving(vbat,p0,dp,with_limits=True):
    """Same nominal state-feedback gains, corrected ideal bus KCL; no DAB switching model."""
    L,Cs,Cb=1.5e-6,100e-6,400e-6; K=b.design(L,Cs,Cb,8000)
    e=equilibrium(vbat,p0); ip=e['path_A']; vs=e['vser_V']; vb=400.; idab=ip
    q=-(ip+K[:4]@np.array([ip,vs,vb,idab]))/K[4]
    dt=.1e-6; n=int(.0025/dt); delay=np.full(int(b.d_dab/dt)+1,ip); cmd=ip; lo=[]; energy=[]
    for k in range(n):
        tt=k*dt; pl=p0+dp*(tt>=.001)
        if k%int(b.Ts/dt)==0:
            raw=-K[:4]@np.array([ip,vs,vb,idab])-K[4]*q
            lim=min(100,8000/max(abs(vs),1)) if with_limits else 100
            cmd=np.clip(raw,-lim,lim); q+=b.Ts*(400-vb)+.05*(cmd-raw)/(-K[4])
        delay=np.roll(delay,1);delay[0]=cmd
        iin_dab=vs*idab/vb
        di=(vbat/2-R*ip+vs-vb)/L; dsv=(idab-ip)/Cs; dbv=(ip-pl/vb-iin_dab)/Cb
        residual=vbat/2*ip-R*ip*ip-pl-(L*ip*di+Cs*vs*dsv+Cb*vb*dbv)
        ip+=dt*di;vs+=dt*dsv;vb+=dt*dbv;idab+=dt*(delay[-1]-idab)/b.tau
        lo.append((vb,ip,vs,idab));energy.append(residual)
        if vb<100 or not np.isfinite(vb):break
    ar=np.array(lo); after=ar[min(int(.001/dt),len(ar)-1):]
    return {'Vbat':vbat,'droop_V':float(400-after[:,0].min()),'vbus_end_V':float(ar[-1,0]),
      'path_end_A':float(ar[-1,1]),'vser_end_V':float(ar[-1,2]),'energy_residual_max_W':float(np.max(np.abs(energy))),
      'note':'Sensitivity only: original gains, ideal bipolar actuator, corrected bus input, not a replacement hardware validation.'}
result['modified_average_sensitivity']=[modified_power_conserving(v,5000,24000) for v in [648,788,907]]
(ROOT/'audit_pprc_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
