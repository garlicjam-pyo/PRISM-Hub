"""Candidate two-stage PPRC: finite DAB link + PWM H-bridge and LC filter.

State = [i_path, v_series, v_bus, i_bridge, v_link, i_dab_link].
The 100 A bridge/path rating is NOT the DAB's 80 A link-current rating.
This is an averaged research model, not switching/protection validation.
"""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import brentq
from scipy.signal import place_poles


@dataclass(frozen=True)
class Parameters:
    L: float = 1.5e-6
    Cs: float = 100e-6
    Cb: float = 400e-6
    R: float = .0132
    Lh: float = 5e-6       # provisional bridge filter, not a selected component
    Rh: float = .002
    Clink: float = .002   # provisional 2 mF, explicitly stored energy
    eta: float = .96      # directional DAB efficiency, fixed approximation
    tau: float = 10e-6
    Ts: float = 5e-6
    delay: float = 5e-6
    vref: float = 400.
    vlink: float = 100.
    modulation_max: float = .95
    path_max: float = 100.
    reference_max: float = 84.  # empirical control reserve; not a physical current clamp
    link_max: float = 80.
    power_max: float = 8000.
    series_max: float = 90.
    link_bw: float = 1000.
    inner_tau: float = 10e-6
    bus_bw: float = 4000.
    Ldab: float = 11.1e-6
    fs: float = 200e3
    turns: float = 4.
    phase_max: float = np.pi/3


def primary_power(power_link, p):
    """Positive: bus supplies link. Negative: link returns power to bus."""
    return power_link/p.eta if power_link >= 0 else power_link*p.eta


def current_limit(vbus, vlink, p):
    sps = max(vbus, 0)*p.turns*p.phase_max*(1-p.phase_max/np.pi)/(2*np.pi*p.fs*p.Ldab)
    return min(p.link_max, sps, p.power_max/max(vlink, 1e-9))


def equilibrium(vbat, power, p=Parameters()):
    def balance(ip):
        vs = p.vref-vbat/2+p.R*ip
        plink = (vs+p.Rh*ip)*ip
        return p.vref*ip-power-primary_power(plink, p)
    ip = brentq(balance, -500., 500., xtol=1e-12)
    vs = p.vref-vbat/2+p.R*ip
    m = (vs+p.Rh*ip)/p.vlink
    x = np.array([ip, vs, p.vref, ip, p.vlink, m*ip])
    return x, np.array([m, m*ip])


def steady_feasible(vbat, power, p=Parameters(), control_reserve=True):
    x,u=equilibrium(vbat,power,p)
    current=p.reference_max if control_reserve else p.path_max
    return bool(abs(x[0])<=current and abs(x[1])<=p.series_max
                and abs(u[0])<=p.modulation_max
                and abs(x[5])<=current_limit(x[2],x[4],p))


def continuous_power_limit(vbat, p=Parameters(), rated_power=25000.):
    """Positive-load static envelope only; no transient-safety guarantee."""
    if not steady_feasible(vbat,0,p): return 0.
    low,high=0.,rated_power
    for _ in range(50):
        mid=(low+high)/2
        if steady_feasible(vbat,mid,p): low=mid
        else: high=mid
    return low


def rhs(x, u, vbat, power, p=Parameters()):
    ip, vs, vb, ih, vl, idab = x
    m, icmd = u
    pin = primary_power(vl*idab, p)
    return np.array([(vbat/2-p.R*ip+vs-vb)/p.L,
                     (ih-ip)/p.Cs,
                     (ip-(power+pin)/vb)/p.Cb,
                     (m*vl-vs-p.Rh*ih)/p.Lh,
                     (idab-m*ih)/p.Clink,
                     (icmd-idab)/p.tau])


def energy_residual(x, dx, vbat, power, p=Parameters()):
    ip, vs, vb, ih, vl, idab = x
    derivative = np.dot(x[:5]*[p.L,p.Cs,p.Cb,p.Lh,p.Clink], dx[:5])
    dab_loss = primary_power(vl*idab,p)-vl*idab
    expected = vbat/2*ip-p.R*ip**2-p.Rh*ih**2-power-dab_loss
    return float(derivative-expected)


def design(vbat, power, p=Parameters()):
    """Reduced bus-loop design; finite-link dynamics are tested separately.

    Design assumes the bridge current follows a first-order reference and
    the link is regulated. The simulated plant retains both omitted dynamics.
    """
    xe, _ = equilibrium(vbat, power, p)
    def reduced(x):
        ip, vs, vb, ih = x
        pin = primary_power((vs+p.Rh*ih)*ih,p)
        return np.array([(vbat/2-p.R*ip+vs-vb)/p.L,(ih-ip)/p.Cs,
                         (ip-(power+pin)/vb)/p.Cb,-ih/p.inner_tau])
    h=1e-4
    J=np.column_stack([(reduced(xe[:4]+e)-reduced(xe[:4]-e))/(2*h) for e in np.eye(4)*h])
    A=np.zeros((5,5)); A[:4,:4]=J; A[4,2]=-1
    B=np.zeros((5,1)); B[3,0]=1/p.inner_tau
    w=2*np.pi*p.bus_bw; z=.7
    return place_poles(A,B,[-z*w+1j*w*np.sqrt(1-z*z),-z*w-1j*w*np.sqrt(1-z*z),-w,-w/3,-2.5*w]).gain_matrix[0]


def simulate(vbat=788., power0=5000., power1=25000., p=Parameters(),
             dt=2e-7, duration=.006, step=.001, K=None, keep_trace=False):
    if not (dt>0 and 0<=step<duration):
        raise ValueError('Require dt>0 and 0<=step<duration')
    sample=int(round(p.Ts/dt)); lag=int(round(p.delay/dt))
    if sample<1 or abs(sample*dt-p.Ts)>1e-12 or abs(lag*dt-p.delay)>1e-12:
        raise ValueError('dt must divide sample period and transport delay')
    if not steady_feasible(vbat,power0,p):
        raise ValueError('Initial steady state exceeds candidate operating envelope')
    K=design(vbat,power0,p) if K is None else np.asarray(K)
    x,u=equilibrium(vbat,power0,p); q=-(x[0]+K[:4]@x[:4])/K[4]; qlink=0.
    buffer=np.tile(u,(lag+1,1)); tick=0
    n=int(round(duration/dt)); log=np.empty((n,6)); controls=np.empty((n,2))
    residual=0.; stop=None; wlink=2*np.pi*p.link_bw
    for k in range(n):
        t=k*dt; power=power1 if t>=step else power0
        if k%sample==0:
            raw=-K[:4]@x[:4]-K[4]*q
            iref=np.clip(raw,-p.reference_max,p.reference_max)
            q+=p.Ts*(p.vref-x[2])+.1*(iref-raw)/(-K[4])
            mraw=(x[1]+p.Rh*x[3]+p.Lh/p.inner_tau*(iref-x[3]))/x[4]
            m=float(np.clip(mraw,-p.modulation_max,p.modulation_max))
            rawlink=m*x[3]+p.Clink*(2*.7*wlink*(p.vlink-x[4])+wlink*wlink*qlink)
            limit=current_limit(x[2],x[4],p)
            ilink=float(np.clip(rawlink,-limit,limit))
            qlink+=p.Ts*(p.vlink-x[4])+.1*(ilink-rawlink)/(p.Clink*wlink*wlink)
            u=np.array([m,ilink])
        buffer[tick]=u; applied=buffer[(tick+1)%len(buffer)].copy(); tick=(tick+1)%len(buffer)
        # Explicit midpoint; sample/delay input is held for the integration step.
        d1=rhs(x,applied,vbat,power,p)
        residual=max(residual,abs(energy_residual(x,d1,vbat,power,p)))
        mid=x+dt*.5*d1
        x=x+dt*rhs(mid,applied,vbat,power,p)
        log[k]=x; controls[k]=applied
        if not np.isfinite(x).all() or x[2]<50 or x[4]<10:
            stop=k; log=log[:k+1]; controls=controls[:k+1]; break
    t=(np.arange(len(log))+1)*dt
    post=log[t>=step,2]
    limit=np.array([current_limit(vb,vl,p) for vb,vl in log[:,[2,4]]])
    violations={
        'path_current':bool(np.max(np.abs(log[:,0]))>p.path_max+1e-6),
        'bridge_current':bool(np.max(np.abs(log[:,3]))>p.path_max+1e-6),
        'series_voltage':bool(np.max(np.abs(log[:,1]))>p.series_max+1e-6),
        'link_current_rating':bool(np.max(np.abs(log[:,5]))>p.link_max+1e-6),
        # A lagged current command can exceed a falling instantaneous envelope.
        'instantaneous_dab_envelope':bool(np.max(np.abs(log[:,5])-limit)>1e-3),
        'dab_power':bool(np.max(np.abs(log[:,4]*log[:,5]))>p.power_max+1e-3),
        'link_voltage_band':bool(np.min(log[:,4])<90 or np.max(log[:,4])>110),
        'modulation':bool(np.max(np.abs(controls[:,0]))>p.modulation_max+1e-9),
    }
    result=dict(vbat=vbat,power0=power0,power1=power1,dt=dt,duration=duration,
                droop=float(p.vref-np.min(post)),vbus_end=float(log[-1,2]),
                vbus_max=float(np.max(log[:,2])),vlink_min=float(np.min(log[:,4])),
                vlink_max=float(np.max(log[:,4])),path_peak=float(np.max(np.abs(log[:,0]))),
                bridge_peak=float(np.max(np.abs(log[:,3]))),link_peak=float(np.max(np.abs(log[:,5]))),
                series_peak=float(np.max(np.abs(log[:,1]))),dab_power_peak=float(np.max(np.abs(log[:,4]*log[:,5]))),
                modulation_peak=float(np.max(np.abs(controls[:,0]))),energy_residual_max=residual,
                completed=stop is None,end_time=float(t[-1]),violations=violations,
                within_port_limits=not any(violations.values()),
                voltage_quality_pass=bool(stop is None and np.min(post)>=392 and np.max(post)<=408 and abs(log[-1,2]-400)<=4),
                K=K.tolist(),parameters=asdict(p))
    if keep_trace: result.update(t=t,x=log,u=controls)
    return result
