"""Frozen common controller candidate, designed once at 788 V / 5 kW.

No gain scheduling or knowledge of actual plant tolerances. Reference limit
remains 84 A; pass/fail includes physical currents and a 1 ms recovery limit.
The coefficient set is for the finite-link average model, not firmware release.
"""
import numpy as np
from pprc_two_stage import Parameters, simulate

NOMINAL=Parameters(bus_bw=4800.)
GAIN=(-1.4476004429712448, -.49495671954233184, 2.935688138531015,
      .49113020413827174, -12686.999819984616)


def assess(t, x, step, completed, port_limits, vref=400.):
    """Recovery: first sample after the last exit from +/-4 V until run end.

    A trajectory still outside the band at run end has no measured recovery.
    This definition is finite-horizon, not a long-term stability guarantee.
    """
    post=t>=step
    outside=np.flatnonzero(post & (np.abs(x[:,2]-vref)>4))
    recovery=0.
    if len(outside):
        last=outside[-1]
        recovery=None if last==len(t)-1 else float(t[last+1]-step)
    if not completed: recovery=None
    tail=x[t>=max(step,t[-1]-.001),2]
    checks=dict(completed=bool(completed),ports=bool(port_limits),
                voltage_excursion=bool(np.all(np.abs(x[post,2]-vref)<=8)),
                final_voltage=bool(abs(x[-1,2]-vref)<=4),
                recovery_1ms=bool(recovery is not None and recovery<=.001),
                final_1ms_ripple=bool(np.ptp(tail)<=.1))
    return dict(recovery_s=recovery,tail_ripple_V=float(np.ptp(tail)),
                checks=checks,requirements_pass=all(checks.values()))


def run(vbat=788., power0=1000., power1=25000., plant=NOMINAL,
        duration=.02, dt=2e-7, keep_trace=False):
    r=simulate(vbat,power0,power1,p=plant,K=GAIN,control_p=NOMINAL,
               duration=duration,dt=dt,keep_trace=True)
    r.update(assess(r['t'],r['x'],.001,r['completed'],r['within_port_limits']))
    r['delta_current_equivalent_A']=(power1-power0)/400.
    r['continuous_rating_exceeded']=max(abs(power0),abs(power1))>25000
    if not keep_trace:
        for key in ['t','x','u']: r.pop(key)
    return r
