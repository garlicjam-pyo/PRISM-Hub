"""TB08 기준값 생성: R2 창 조정 Stage B 모듈(1000 V급 240s 팩, B_470 부품, V_W 460 V)의 검증 모델 결과.

창 조정 설계값(E19 R2-W460): 기준전압 V_W 460 V, DAB 권선비 4.6:1(= V_W/100), 누설 인덕턴스 11.1 µH·(460/400)²
= 14.68 µH, DAB 정격 4.0 kW(정적 최대 링크전력 2.16 kW × 1.8). 채택 제어기의 이득·예측 구조는 그대로다.

사례
  A  1008 V, 1 → 25 kW(Tier-2, 최대 배터리 전압)         기준: E12 스위칭 ODE(model_stage_b_switching)
  B   930 V, 15 → 25 kW(Tier-1, 창 하단 근처, DAB 저전류) 기준: E12 스위칭 ODE
  C   910 V, 25 kW, 끔: 1 ms에 기준 460 V → V_A 램프 1 ms, 1 ms 유지, 영벡터 0.2 ms, 바이패스(3.2 ms)
                                                           기준: E19 모드 평균모델(다이오드 상태 고정, diode_fix)
  D  1008 V, 25 kW, DAB 고장: 1 ms에 DAB 정지 + 기준 → V_A 램프 1 ms, 0.2 ms 뒤 영벡터 0.2 ms, 바이패스(2.4 ms)
                                                           기준: E19 모드 평균모델
  E   930 V, 25 kW, 켬: 0–0.5 ms 바이패스 + H-브리지 영벡터(전류 분담), 0.5 ms에 바이패스 열림(영벡터만),
      0.7 ms에 제어 시작(무충격 초기화) + 기준 V_A → 460 V 램프 1 ms
                                                           기준: E19 켬 평균모델(영벡터 상태에서 시작, 0.7 ms만큼 시간 이동)
결과(사례마다): TB08_<사례>_init.json(초기조건·제어기 초기상태·모드 시퀀스)
      A·B: TB08_<사례>_rec.csv(5 µs 주기 기록, TB04와 같은 열), TB08_<사례>_wave.csv(계단 전후 순시 파형)
      C·D·E: TB08_<사례>_avg.csv(평균모델 궤적 1 µs 간격: t, i_p, v_s, v_bus, i_h, v_link, i_dab, 모드 번호)
실행: python make_ref_TB08.py <검증 코드 python 폴더>
"""
import json
import sys
from dataclasses import replace

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
from controller_reference import NOMINAL                                   # noqa: E402
from controller_adopted import K_ADOPTED, CP                               # noqa: E402
from model_stage_b import equilibrium                                      # noqa: E402
from model_stage_b_switching import simulate_switching, _phase_ff, _cp_vec, _loss   # noqa: E402
import E19_r2_window_module as E19                                         # noqa: E402
from E14_protection_startup import run_modes, run_modes_cont, va_est, zero_vector_state   # noqa: E402

VW, PR = 460., 4000.
p, cp = E19.plant("W460_240s", PR)            # 플랜트·제어기 파라미터(기준전압·권선비·누설 L·DAB 정격만 400 V 설계와 다름)
K = np.asarray(K_ADOPTED, float)
R_BYP = 3.3e-3                                # 바이패스 스위치(150 V GaN 역직렬 2개) 도통저항
R_HZ = p.Rh + 2 * 1e-4                        # H-브리지 영벡터 경로: L_h 저항 + 하측 스위치 2개(회로 R_on 0.1 mΩ)
REC_COLS = ["vbus", "ip", "ih", "vlink", "ilink", "plink", "ih_max", "ih_min", "ip_absmax", "vbus_min", "vbus_max",
            "vlink_min", "vlink_max", "iL_absmax", "m_cmd", "ilink_cmd", "phase", "vs_absmax", "m_pwm", "iL_mean",
            "ploss", "rho", "eps", "r_f", "fault"]
MODE_ID = {"ctrl": 0, "ctrl_nodab": 1, "zero": 2, "bypass": 3}
NEVER = 1e30


def seq(t_ramp0=NEVER, t_ramp1=NEVER, v_from=VW, v_to=VW, t_nodab=NEVER, t_zero=NEVER, t_byp=NEVER,
        t_open=NEVER, t_ctrl=0., mode_init=0):
    """회로 모델의 모드 시퀀서(ctrl/prism_r2_sequence.m) 상수. 순서가 그 함수 머리말과 같다."""
    return [t_ramp0, t_ramp1, v_from, v_to, t_nodab, t_zero, t_byp, t_open, t_ctrl, float(mode_init)]


def init_common(vbat, P0, P1, t_step, t_end):
    x0, u0 = equilibrium(vbat, P0, p)
    q0 = -(x0[0] + K[0] * x0[0] + K[1] * x0[1] + K[2] * x0[2] + K[3] * x0[3]) / K[4]
    ph0 = _phase_ff(u0[1], x0[2], _cp_vec(cp), 0.9)
    return dict(vbat=vbat, P0=P0, P1=P1, t_step=t_step, t_end=t_end, x0=[float(z) for z in x0[:5]],
                u0=[float(z) for z in u0], q0=float(q0), ph0=float(ph0), ploss0=float(_loss(x0[4] * u0[1], p.eta)),
                eta=p.eta, VW=VW, dab_rated_W=PR, turns=p.turns, Ldab=p.Ldab, K=[float(z) for z in K])


def save_avg(name, t, log, modes_fn, t_shift=0.):
    """평균모델 궤적을 1 µs 간격으로 저장(적분 간격 0.2 µs의 5번째마다)."""
    k = np.arange(4, len(t), 5)
    md = np.array([MODE_ID[modes_fn(tt)] for tt in t[k]])
    np.savetxt(f"TB08_{name}_avg.csv", np.c_[t[k] + t_shift, log[k, :6], md], delimiter=",",
               header="t_s,ip,vs,vbus,ih,vlink,idab,mode", comments="", fmt="%.9g")


out = {}
# ---------------- A·B: 창 조정 Tier 사례(스위칭 ODE) ----------------------------------------------------
for name, (v, a, b) in {"A_1008V_1to25kW": (1008., 1000., 25000.), "B_930V_15to25kW": (930., 15000., 25000.)}.items():
    r = simulate_switching(v, a, b, p, cp, K_ADOPTED, predict=True, profile=0, duration=4e-3, step=1e-3,
                           sw=dict(t_pre=0.), capture=[0.95e-3, 1.25e-3, 10])
    init = init_common(v, a, b, 1e-3, 4e-3)
    init.update(kind="switching", seq=seq(), completed=r["completed"], energy_residual_W=r["energy_residual_W"])
    json.dump(init, open(f"TB08_{name}_init.json", "w"), indent=1)
    rec = r["rec"]
    np.savetxt(f"TB08_{name}_rec.csv", np.c_[r["t"], rec], delimiter=",", header="t_end_s," + ",".join(REC_COLS),
               comments="", fmt="%.9g")
    np.savetxt(f"TB08_{name}_wave.csv", r["wave"], delimiter=",", header="t_s,ip,vs,vbus,ih,vlink,iL,sA_minus_sB,s1",
               comments="", fmt="%.7g")
    post = r["t"] > 1e-3
    out[name] = dict(vbus_min=float(rec[post, 9].min()), vbus_max=float(rec[post, 10].max()),
                     ip_absmax=float(rec[post, 8].max()), ih_max=float(rec[post, 6].max()),
                     plink_absmax=float(np.abs(rec[:, 5]).max()), vbus_final=float(rec[-1, 0]))
    print(name, "completed", r["completed"], {k: round(x, 3) for k, x in out[name].items()})

# ---------------- C: 끔(창 조정 → 바이패스), 평균모델 -------------------------------------------------
vbat, P = 910., 25000.
va = float(va_est(vbat, P, p.R))
t_ev, tr, hold, zoff = 1e-3, 1e-3, 1e-3, .2e-3
t_zero = t_ev + tr + hold; t_byp = t_zero + zoff
x0, u0 = equilibrium(vbat, P, p)
ctrl = E19.RampW(cp, vbat, lambda t: VW if t < t_ev else VW + (va - VW) * min((t - t_ev) / tr, 1.))
sch = lambda t: "ctrl" if t < t_zero else ("zero" if t < t_byp else "bypass")
_, t, log = run_modes(vbat, P, sch, x0, ctrl=ctrl, p=p, duration=4.5e-3, diode_fix=True)
init = init_common(vbat, P, P, NEVER, 4.5e-3)
init.update(kind="averaged", VA=va, seq=seq(t_ramp0=t_ev, t_ramp1=t_ev + tr, v_from=VW, v_to=va, t_zero=t_zero, t_byp=t_byp))
json.dump(init, open("TB08_C_910V_disable_25kW_init.json", "w"), indent=1)
save_avg("C_910V_disable_25kW", t, log, sch)
k = int(np.searchsorted(t, t_byp)) - 1
out["C"] = dict(VA=va, ip_max=float(log[:, 0].max()), ih_absmax=float(np.abs(log[:, 3]).max()),
                vbus=[float(log[:, 2].min()), float(log[:, 2].max())], vs_at_bypass=float(log[k, 1]),
                vlink_max=float(log[:, 4].max()))
print("C", {kk: (np.round(x, 3) if not isinstance(x, list) else [round(y, 3) for y in x]) for kk, x in out["C"].items()})

# ---------------- D: DAB 고장 → 바이패스 강등, 평균모델 ----------------------------------------------
vbat = 1008.
va = float(va_est(vbat, P, p.R))
t_zero = t_ev + tr + .2e-3; t_byp = t_zero + zoff
x0, u0 = equilibrium(vbat, P, p)
ctrl = E19.RampW(cp, vbat, lambda t: VW if t < t_ev else VW + (va - VW) * min((t - t_ev) / tr, 1.))
sch = lambda t: "ctrl" if t < t_ev else ("ctrl_nodab" if t < t_zero else ("zero" if t < t_byp else "bypass"))
_, t, log = run_modes(vbat, P, sch, x0, ctrl=ctrl, p=p, duration=4e-3, diode_fix=True)
init = init_common(vbat, P, P, NEVER, 4e-3)
init.update(kind="averaged", VA=va, seq=seq(t_ramp0=t_ev, t_ramp1=t_ev + tr, v_from=VW, v_to=va, t_nodab=t_ev,
                                             t_zero=t_zero, t_byp=t_byp))
json.dump(init, open("TB08_D_1008V_dabfault_25kW_init.json", "w"), indent=1)
save_avg("D_1008V_dabfault_25kW", t, log, sch)
k = int(np.searchsorted(t, t_byp)) - 1
out["D"] = dict(VA=va, ip_max=float(log[:, 0].max()), ih_absmax=float(np.abs(log[:, 3]).max()),
                vbus=[float(log[:, 2].min()), float(log[:, 2].max())], vs_at_bypass=float(log[k, 1]),
                vlink_max=float(log[:, 4].max()))
print("D", out["D"])

# ---------------- E: 켬(바이패스 + 영벡터 → 영벡터 → 창 조정), 평균모델 --------------------------------
vbat = 930.
t_open, t_ctrl = .5e-3, .7e-3
# 회로 초기상태(바이패스와 H-브리지 영벡터가 경로전류를 저항비로 나눔)
Rpar = R_BYP * R_HZ / (R_BYP + R_HZ)
vb0 = float(va_est(vbat, P, p.R + Rpar)); ip0 = P / vb0
ih0 = ip0 * R_BYP / (R_BYP + R_HZ); vs0 = -R_HZ * ih0
# 기준: 바이패스가 열린 뒤의 영벡터 정상상태에서 제어 시작(E19 enable_case와 같은 계산, 시간 0 = 회로 0.7 ms)
xz, vaz = zero_vector_state(vbat, P, p)
vfn = lambda t: vaz + (VW - vaz) * min(t / tr, 1.)
ctrl = E19.RampW(cp, vbat, vfn); ctrl.reset(xz, np.array([0., 0.]))
_, t, log = run_modes_cont(vbat, P, xz, ctrl, p=p, duration=4e-3 - t_ctrl)
init = dict(vbat=vbat, P0=P, P1=P, t_step=NEVER, t_end=4e-3, x0=[ip0, vs0, vb0, ih0, 100.], u0=[0., 0.],
            q0=float(-(xz[0] + K[0] * xz[0] + K[1] * xz[1] + K[2] * xz[2] + K[3] * xz[3]) / K[4]), ph0=0., ploss0=0.,
            eta=p.eta, VW=VW, dab_rated_W=PR, turns=p.turns, Ldab=p.Ldab, K=[float(z) for z in K], kind="averaged",
            VA=vaz, R_bypass=R_BYP, ih_share=ih0 / ip0,
            seq=seq(t_ramp0=t_ctrl, t_ramp1=t_ctrl + tr, v_from=vaz, v_to=VW, t_open=t_open, t_ctrl=t_ctrl, mode_init=4))
json.dump(init, open("TB08_E_930V_enable_25kW_init.json", "w"), indent=1)
save_avg("E_930V_enable_25kW", t, log, lambda tt: "ctrl", t_shift=t_ctrl)
out["E"] = dict(VA_zero_vector=vaz, vb0_bypass_share=vb0, ih_share=ih0 / ip0, ip_max=float(log[:, 0].max()),
                ih_absmax=float(np.abs(log[:, 3]).max()), vbus=[float(log[:, 2].min()), float(log[:, 2].max())],
                vbus_final=float(log[-1, 2]))
print("E", out["E"])
json.dump(out, open("TB08_ref_summary.json", "w"), indent=1)
