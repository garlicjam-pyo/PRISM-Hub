"""Controller redesign helpers (2026-09-29).

Same structure as the frozen controller (state feedback on [i_p, v_s, v_bus, i_h] + bus-voltage integral,
inner bridge-current law through the modulation index, DAB link-voltage PI), with the pole set exposed:
    poles = {-z*w +/- j*w*sqrt(1-z^2), -a1*w, -a2*w, -a3*w},  w = 2*pi*bus_bw
The frozen controller is a1 = 1, a2 = 1/3, a3 = 2.5, z = 0.7, bus_bw = 4.8 kHz, inner_tau = 10 us.
"""
from dataclasses import replace
import numpy as np
from scipy.signal import place_poles
from pprc_two_stage import Parameters, equilibrium, primary_power


def design_poles(vbat, power, p, z=.7, a=(1., 1 / 3, 2.5)):
    """Pole placement on the reduced model used by pprc_two_stage.design(), with a configurable pole set."""
    xe, _ = equilibrium(vbat, power, p)
    def reduced(x):
        ip, vs, vb, ih = x
        pin = primary_power((vs + p.Rh * ih) * ih, p)
        return np.array([(vbat / 2 - p.R * ip + vs - vb) / p.L, (ih - ip) / p.Cs,
                         (ip - (power + pin) / vb) / p.Cb, -ih / p.inner_tau])
    h = 1e-4
    J = np.column_stack([(reduced(xe[:4] + e) - reduced(xe[:4] - e)) / (2 * h) for e in np.eye(4) * h])
    A = np.zeros((5, 5)); A[:4, :4] = J; A[4, 2] = -1
    B = np.zeros((5, 1)); B[3, 0] = 1 / p.inner_tau
    w = 2 * np.pi * p.bus_bw
    poles = [-z * w + 1j * w * np.sqrt(1 - z * z), -z * w - 1j * w * np.sqrt(1 - z * z)] + [-ai * w for ai in a]
    return place_poles(A, B, poles).gain_matrix[0]


class StageBController:
    """Sampled Stage B controller. With all options off it reproduces the frozen inline controller.

    predict     : one-sample state prediction of the fast states [i_p, v_s, i_h] with the nominal model
                  and the previous command (compensates the nominal transport delay of one period,
                  cf. Bibian & Jin, IEEE TPEL 15(5), 2000, doi:10.1109/63.867672). v_bus, v_link are held at their measured values,
                  so no load measurement is needed.
    vdev_limit  : bus-voltage deviation E (V) beyond which the proportional voltage term stops growing
                  (limits the recharge current after large, out-of-contract steps; the integral keeps acting).
    pcl         : (I_th, k_p) path-current limiter; the bridge-current reference is capped at
                  I_th - k_p*(i_p - I_th) when i_p exceeds I_th.
    """
    def __init__(self, K, cp, vbat, predict=False, vdev_limit=None, pcl=None, n_sub=5):
        self.K, self.cp, self.vbat = np.asarray(K, float), cp, float(vbat)
        self.predict, self.vdev_limit, self.pcl, self.n_sub = predict, vdev_limit, pcl, n_sub
        self.wlink = 2 * np.pi * cp.link_bw

    def reset(self, x, u):
        self.q = -(x[0] + self.K[:4] @ x[:4]) / self.K[4]
        self.qlink = 0.
        self.u_prev = np.array(u, float)

    def state(self):
        return np.concatenate([[self.q, self.qlink], self.u_prev])

    def set_state(self, s):
        self.q, self.qlink, self.u_prev = float(s[0]), float(s[1]), np.array(s[2:4], float)

    def _predict(self, x):
        cp = self.cp; ip, vs, vb, ih, vl = x[:5]; m = self.u_prev[0]
        h = cp.Ts / self.n_sub
        def f(s):
            ip, vs, ih = s
            return np.array([(self.vbat / 2 - cp.R * ip + vs - vb) / cp.L, (ih - ip) / cp.Cs,
                             (m * vl - vs - cp.Rh * ih) / cp.Lh])
        s = np.array([ip, vs, ih])
        for _ in range(self.n_sub):
            s = s + h * f(s + .5 * h * f(s))
        xp = np.array(x, float); xp[0], xp[1], xp[3] = s
        return xp

    def step(self, x):
        cp, K = self.cp, self.K
        xs = self._predict(x) if self.predict else x
        vb_term = xs[2]
        if self.vdev_limit is not None:
            vb_term = cp.vref - np.clip(cp.vref - xs[2], -self.vdev_limit, self.vdev_limit)
        raw = -(K[0] * xs[0] + K[1] * xs[1] + K[2] * vb_term + K[3] * xs[3]) - K[4] * self.q
        iref = np.clip(raw, -cp.reference_max, cp.reference_max)
        if self.pcl is not None and xs[0] > self.pcl[0]:
            iref = min(iref, self.pcl[0] - self.pcl[1] * (xs[0] - self.pcl[0]))
        self.q += cp.Ts * (cp.vref - x[2]) + .1 * (iref - raw) / (-K[4])
        mraw = (xs[1] + cp.Rh * xs[3] + cp.Lh / cp.inner_tau * (iref - xs[3])) / xs[4]
        m = float(np.clip(mraw, -cp.modulation_max, cp.modulation_max))
        w = self.wlink
        rawlink = m * xs[3] + cp.Clink * (2 * .7 * w * (cp.vlink - x[4]) + w * w * self.qlink)
        from pprc_two_stage import current_limit
        limit = current_limit(x[2], x[4], cp)
        ilink = float(np.clip(rawlink, -limit, limit))
        self.qlink += cp.Ts * (cp.vlink - x[4]) + .1 * (ilink - rawlink) / (cp.Clink * w * w)
        self.u_prev = np.array([m, ilink])
        return self.u_prev.copy()
