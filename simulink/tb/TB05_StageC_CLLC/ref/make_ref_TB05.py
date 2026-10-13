"""TB05 기준값 생성: 검증 모델 E10(Stage C 대칭 CLLC 스위칭 ODE)과 같은 계산을 하고 파형도 저장한다.

E10_stage_c_cllc.simulate와 같은 식·같은 적분(RK4, 한 주기 400단계, 1차 환산 6상태, 이상 동기정류, 데드타임 동안 v_p = 0)이다.
사례: 공진점(f_s = f_r = 250 kHz) 3 kW(400주기)·1.5 kW·0.3 kW(300주기), 입력 400 V, 출력 초기 48 V.
결과: TB05_ref_python.json(사례별 지표), TB05_ref_python_wave_3kW.csv(3 kW 마지막 3주기 파형)
실행: python make_ref_TB05.py
"""
import json
import numpy as np

n = 25 / 3; fr = 250e3; Lr1 = 11.0e-6; Cr1 = 36.8e-9; Lm = 66e-6; Lr2p = Lr1; Cr2p = Cr1
Co = 470e-6; Coss = 100e-12; td = 50e-9


def simulate(Po=3000., fs=250e3, Vin=400., ncyc=400, Nstep=400, Vo0=48.):
    RL = 48. ** 2 / Po
    T = 1 / fs; dt = T / Nstep; N = ncyc * Nstep
    log = np.zeros((N, 6)); vpl = np.zeros(N); ndead = int(round(td / dt)); half = Nstep // 2
    ginv = 1 / (1 / Lr1 + 1 / Lm + 1 / Lr2p)

    def f(x, vp):
        ir1, vc1, im, ir2, vc2, Vo = x
        vs2 = np.sign(ir2) * n * Vo if abs(ir2) > 1e-6 else 0.0
        vm = ((vp - vc1) / Lr1 + (vc2 + vs2) / Lr2p) * ginv
        return np.array([(vp - vc1 - vm) / Lr1, ir1 / Cr1, vm / Lm, (vm - vc2 - vs2) / Lr2p, ir2 / Cr2p,
                         (abs(ir2) * n - Vo / RL) / Co])

    x = np.array([0., 0., 0., 0., 0., Vo0])
    for k in range(N):
        m = k % Nstep
        vp = (Vin if m >= ndead else 0.0) if m < half else (-Vin if (m - half) >= ndead else 0.0)
        k1 = f(x, vp); k2 = f(x + .5 * dt * k1, vp); k3 = f(x + .5 * dt * k2, vp); k4 = f(x + dt * k3, vp)
        x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4); log[k] = x; vpl[k] = vp
    t = (np.arange(N) + 1) * dt; msk = t > (ncyc - 10) * T + 1e-12
    L = log[msk]; ir1 = L[:, 0]; im = L[:, 2]; ir2 = L[:, 3]; Vo = L[:, 5]
    idx = [i for i in range(len(ir1)) if (i % Nstep) == half - 1 or (i % Nstep) == Nstep - 1]
    i_sw = np.abs(ir1[idx]).mean()
    r = dict(Po=Po, Vo=float(Vo.mean()), gain=float(Vo.mean() * n / Vin), Ipri_rms=float(np.sqrt(np.mean(ir1 ** 2))),
             Isec_rms=float(np.sqrt(np.mean(ir2 ** 2)) * n), Im_pk=float(np.abs(im).max()), i_sw=float(i_sw),
             zvs_margin=float(i_sw * td / (2 * Coss * Vin)), Vo_ripple=float(Vo.max() - Vo.min()))
    return r, t, log, vpl


out = {"source": "make_ref_TB05.py (E10_stage_c_cllc.simulate와 같은 계산)", "cases": []}
for Po, nc in [(3000., 400), (1500., 300), (300., 300)]:
    r, t, log, vpl = simulate(Po=Po, ncyc=nc)
    out["cases"].append(r)
    print(r)
    if Po == 3000.:
        T = 4e-6; m = t > t[-1] - 3 * T + 1e-12
        np.savetxt("TB05_ref_python_wave_3kW.csv", np.c_[t[m], log[m][:, 0], log[m][:, 1], log[m][:, 2], log[m][:, 3] * n,
                   log[m][:, 5], vpl[m]], delimiter=",", header="t_s,ir1_A,vcr1_V,im_A,ir2_secondary_A,Vo_V,vp_V",
                   comments="", fmt="%.8g")
json.dump(out, open("TB05_ref_python.json", "w"), indent=1)
