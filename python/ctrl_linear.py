"""Sampled-data linearization of the Stage B closed loop, exactly as coded in pprc_two_stage.simulate().

One controller period T is mapped z_k -> z_{k+1}, with
    z = [plant x (6), q, q_link, u_{k-1}, ..., u_{k-N}]   (u = [m, i_link_cmd])
The plant is integrated with the same explicit midpoint rule and step as simulate(); the input applied at
time t is the control computed at the latest sample <= t - delay (any delay, not a multiple of T).
The Jacobian at the closed-loop equilibrium gives the discrete eigenvalues; |lambda| < 1 means locally
stable. Used to locate the mode that limits the delay margin and to screen redesign candidates before
nonlinear simulation. Saturations are inactive at the equilibrium and therefore absent from the Jacobian.
"""
from dataclasses import replace
import numpy as np
from pprc_two_stage import Parameters, equilibrium, rhs, current_limit

NHIST = 4                     # command history: supports total delay < (NHIST-1)*Ts = 15 us


def controller_step(x, q, qlink, K, cp, law=None):
    """Identical arithmetic to simulate(); `law` may override the modulation law (redesign hook)."""
    raw = -K[:4] @ x[:4] - K[4] * q
    iref = np.clip(raw, -cp.reference_max, cp.reference_max)
    q = q + cp.Ts * (cp.vref - x[2]) + .1 * (iref - raw) / (-K[4])
    if law is None:
        mraw = (x[1] + cp.Rh * x[3] + cp.Lh / cp.inner_tau * (iref - x[3])) / x[4]
    else:
        mraw = law(x, iref, cp)
    m = float(np.clip(mraw, -cp.modulation_max, cp.modulation_max))
    wlink = 2 * np.pi * cp.link_bw
    rawlink = m * x[3] + cp.Clink * (2 * .7 * wlink * (cp.vlink - x[4]) + wlink * wlink * qlink)
    limit = current_limit(x[2], x[4], cp)
    ilink = float(np.clip(rawlink, -limit, limit))
    qlink = qlink + cp.Ts * (cp.vlink - x[4]) + .1 * (ilink - rawlink) / (cp.Clink * wlink * wlink)
    return np.array([m, ilink]), q, qlink


def unpack(z):
    return z[:6], z[6], z[7], z[8:].reshape(NHIST, 2)


def period_map(z, vbat, power, p, cp, K, dt=1e-7, law=None):
    x, q, qlink, hist = unpack(z)
    u, q, qlink = controller_step(x, q, qlink, K, cp, law)
    hist = np.vstack([u, hist[:-1]])                       # hist[0] = u_k, hist[1] = u_{k-1}, ...
    n = int(round(cp.Ts / dt))
    for j in range(n):
        t_rel = j * dt - p.delay                           # time since sample k, minus delay
        idx = int(np.ceil(-t_rel / cp.Ts - 1e-9))          # samples back: 0 -> u_k
        applied = hist[min(max(idx, 0), NHIST - 1)]
        d1 = rhs(x, applied, vbat, power, p)
        mid = x + dt * .5 * d1
        x = x + dt * rhs(mid, applied, vbat, power, p)
    return np.concatenate([x, [q, qlink], hist[:NHIST].ravel()])


def equilibrium_state(vbat, power, p, K):
    x, u = equilibrium(vbat, power, p)
    q = -(x[0] + K[:4] @ x[:4]) / K[4]
    return np.concatenate([x, [q, 0.], np.tile(u, NHIST)])


def jacobian(vbat, power, p, cp, K, dt=1e-7, law=None):
    z0 = equilibrium_state(vbat, power, p, K)
    f0 = period_map(z0, vbat, power, p, cp, K, dt, law)
    scale = np.maximum(np.abs(z0), 1e-3) * 1e-6
    J = np.empty((len(z0), len(z0)))
    for i in range(len(z0)):
        e = np.zeros(len(z0)); e[i] = scale[i]
        J[:, i] = (period_map(z0 + e, vbat, power, p, cp, K, dt, law) - period_map(z0 - e, vbat, power, p, cp, K, dt, law)) / (2 * scale[i])
    return J, float(np.max(np.abs(f0 - z0)[:6] / np.maximum(np.abs(z0[:6]), 1)))


def modes(vbat, power, p, cp, K, dt=1e-7, law=None):
    J, fixed_err = jacobian(vbat, power, p, cp, K, dt, law)
    lam = np.linalg.eigvals(J)
    order = np.argsort(-np.abs(lam))
    lam = lam[order]
    f = np.abs(np.angle(lam)) / (2 * np.pi * cp.Ts)
    return lam, f, fixed_err


def rho(vbat, power, p, cp, K, dt=1e-7, law=None):
    return float(np.max(np.abs(modes(vbat, power, p, cp, K, dt, law)[0])))


def delay_margin(vbat, power, p, cp, K, lo=0., hi=5e-6, tol=1e-7, dt=1e-7, law=None):
    """Smallest added delay (beyond p.delay) at which rho >= 1, minus one step: upward scan in `tol` steps.
    An upward scan is used because stability is not monotonic in the delay (it can re-appear at larger delays)."""
    base = p.delay
    unstable = lambda extra: rho(vbat, power, replace(p, delay=base + extra), cp, K, dt, law) >= 1
    if unstable(lo): return -1.
    n = int(round((hi - lo) / tol))
    for i in range(1, n + 1):
        if unstable(lo + i * tol): return lo + (i - 1) * tol
    return hi


# ---------------------------------------------------------------- controller-object variant
def period_map_ctrl(z, vbat, power, p, ctrl, dt=1e-7):
    nx, nc = 6, len(ctrl.state())
    x = z[:nx]; ctrl.set_state(z[nx:nx + nc]); hist = z[nx + nc:].reshape(NHIST, 2)
    u = ctrl.step(x)
    hist = np.vstack([u, hist[:-1]])
    n = int(round(ctrl.cp.Ts / dt))
    for j in range(n):
        idx = int(np.ceil((p.delay - j * dt) / ctrl.cp.Ts - 1e-9))
        applied = hist[min(max(idx, 0), NHIST - 1)]
        d1 = rhs(x, applied, vbat, power, p)
        x = x + dt * rhs(x + dt * .5 * d1, applied, vbat, power, p)
    return np.concatenate([x, ctrl.state(), hist.ravel()])


def rho_ctrl(vbat, power, p, make_ctrl, dt=1e-7):
    """make_ctrl(vbat) -> controller; returns spectral radius and the dominant-mode frequency (Hz)."""
    x, u = equilibrium(vbat, power, p)
    ctrl = make_ctrl(vbat); ctrl.reset(x, u)
    z0 = np.concatenate([x, ctrl.state(), np.tile(u, NHIST)])
    scale = np.maximum(np.abs(z0), 1e-3) * 1e-6
    J = np.empty((len(z0), len(z0)))
    for i in range(len(z0)):
        e = np.zeros(len(z0)); e[i] = scale[i]
        J[:, i] = (period_map_ctrl(z0 + e, vbat, power, p, ctrl, dt) - period_map_ctrl(z0 - e, vbat, power, p, ctrl, dt)) / (2 * scale[i])
    lam = np.linalg.eigvals(J); i = int(np.argmax(np.abs(lam)))
    return float(np.abs(lam[i])), float(abs(np.angle(lam[i])) / (2 * np.pi * ctrl.cp.Ts))


def delay_margin_ctrl(vbat, power, p, make_ctrl, hi=8e-6, dt=1e-7, step=1e-7):
    """Largest added delay before the first instability, by an upward scan (stability is not monotonic in delay)."""
    base = p.delay
    unstable = lambda extra: rho_ctrl(vbat, power, replace(p, delay=base + extra), make_ctrl, dt)[0] >= 1
    if unstable(0.): return -1.
    n = int(round(hi / step))
    for i in range(1, n + 1):
        if unstable(i * step): return (i - 1) * step
    return hi
