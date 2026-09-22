"""Lossless output-fed bipolar PPRC average plant; not a switching topology proof.

The DAB draws v_ser*i_dab/V_bus from the same bus that it regulates.
Its virtual signed series port still requires a physical polarity stage.
"""
import numpy as np

SPS_CURRENT_MAX = 400 * 4 * (np.pi/3) * (1-1/3) / (2*np.pi*200e3*11.1e-6)


def equilibrium(vbat, power, resistance=0.0132, vref=400.):
    vm = vbat/2
    disc = vm*vm-4*resistance*power
    if disc < 0 or vm <= 0 or vref <= 0:
        raise ValueError('No high-voltage equilibrium for these parameters')
    ip = 2*power/(vm+np.sqrt(disc))
    return np.array([ip, vref-vm+resistance*ip, vref, ip])


def linearize(L, Cs, Cb, vbat=788., power=5e3, resistance=.0132, tau=10e-6):
    ip, vs, vb, idab = equilibrium(vbat, power, resistance)
    A = np.array([[-resistance/L, 1/L, -1/L, 0],
                  [-1/Cs, 0, 0, 1/Cs],
                  [1/Cb, -idab/(vb*Cb), (power+vs*idab)/(vb*vb*Cb), -vs/(vb*Cb)],
                  [0, 0, 0, -1/tau]])
    Aa = np.zeros((5, 5)); Aa[:4, :4] = A; Aa[4, 2] = -1
    Ba = np.zeros((5, 1)); Ba[3, 0] = 1/tau
    return Aa, Ba


def rhs(x, command, vbat, power, L=1.5e-6, Cs=100e-6, Cb=400e-6,
        resistance=.0132, tau=10e-6):
    ip, vs, vb, idab = x
    return np.array([(vbat/2-resistance*ip+vs-vb)/L,
                     (idab-ip)/Cs,
                     (ip-(power+vs*idab)/vb)/Cb,
                     (command-idab)/tau])
