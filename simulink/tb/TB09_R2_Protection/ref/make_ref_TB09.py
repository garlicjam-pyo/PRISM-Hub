"""TB09 기준값 생성: R2 창 조정 모듈(R2-W460)의 보호 상태기계, 검증 코드 E17(r2_run)의 같은 사례 계산.

사례(모두 R2-W460: V_W 460 V, DAB 4.6:1·4 kW, 바이패스 3.3 mΩ, 버스 RC 감쇠기 1.6 mF·48.6 mΩ, 링크 제동 저항 3 Ω)
  A  1008 V, 25 kW, H-브리지 개방 고장 → 다이오드 클램프 유지(DAB 보조 루프 + 제동 저항) → 400 V 부하 분리(3 ms)
     → 링크 붕괴(20 V/ms) → 소프트 바이패스(경로전류 조절, 제한 없으면 1 ms)
  B   930 V, 25 kW, H-브리지 개방 고장(V_A 465 V ≤ 상한이라 분리 없음) → 바로 링크 붕괴 → 소프트 바이패스
  C   930 V, 25 kW, 켬: 바이패스 → 전류 조향(바이패스 전류 → 0, 0.5 ms) → 열림 → 바로 제어(기준 V_A → 460 V 1 ms)
  D  1008 V, 25 kW, DAB 고장(링크전압 창 검출) → 제동 저항으로 링크 ≤ 110 V 유지 → 400 V 부하 분리(3 ms)
     → 기준 V_A로 1 ms 램프 → |v_s| ≤ 2 V 확인 → 직렬전압 조향 0.2 ms → 바이패스
  부하 분리 시간은 회로 계산 시간을 줄이려고 3 ms로 둔다(E17 기본 20 ms·감도 50 ms는 검증 모델에서만).
  (2차, 2026-10-24) 붕괴 정체 감지·경로전류 조절 소프트 투입을 넣고(상태기계 파라미터 56개), 회로에서 정체 뒤 소프트 투입까지
  보이도록 A·B 계산 시간을 늘렸다(A 13 ms, B 16 ms). H-브리지 강등 유지 중 제동 저항은 링크 과전압 보호(110 V)만 한다.
결과(사례마다): TB09_<사례>_init.json(초기조건·제어기 초기상태·상태기계 파라미터·보호 파라미터),
                TB09_<사례>_avg.csv(1 µs 간격: t, i_p, v_s, v_bus, i_h, v_link, i_dab, i_byp, 400 V 부하 연결, 브리지 모드, 제동 전력),
                TB09_<사례>_metrics.json(E17 판정 지표), TB09_ref_summary.json
실행: python make_ref_TB09.py <검증 코드 python 폴더>
"""
import json
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E17_protection_integration as E17          # noqa: E402
import E19_r2_window_module as E19                # noqa: E402
from controller_adopted import K_ADOPTED          # noqa: E402
from model_stage_b import equilibrium             # noqa: E402

CASE = "W460_240s"
T_SHED_TB = 3e-3
CASES = {
    "A_1008V_hbopen_25kW": dict(V=1008., P=25000., event="hb_open", policy="clamp_brk", t_shed=T_SHED_TB, duration=E17.T_EV + 12.5e-3),
    "B_930V_hbopen_25kW": dict(V=930., P=25000., event="hb_open", policy="clamp_brk", t_shed=T_SHED_TB, duration=E17.T_EV + 15.5e-3),
    "C_930V_enable_steer_25kW": dict(V=930., P=25000., event="enable", prep="steer", wait=0., duration=E17.T_EV + 3.5e-3),
    "D_1008V_dabfault_25kW": dict(V=1008., P=25000., event="dab", policy="brk_hold", close="steer", t_shed=T_SHED_TB, duration=E17.T_EV + 6.5e-3),
}
EV = {"enable": 1, "disable": 2, "dab": 3, "hb_open": 4, "m_pos": 5, "m_neg": 6}
POL = {"now": 1, "collapse_now": 2, "clamp": 3, "clamp_brk": 4, "clamp_brk_hard": 5, "ramp": 1, "brk_hold": 2}
FTYPE = {"hb_open": 1, "dab": 2}

c = E19.CASES[CASE]; p, cp = E19.plant(CASE)
K = np.asarray(K_ADOPTED, float)
out = {}
for name, job in CASES.items():
    j = dict(case=CASE, keep=True, **job)
    m = E17.r2_run(j)
    tr = m.pop("trace")
    V, P = job["V"], job["P"]
    # 초기 상태(감쇠기 커패시터 = 버스전압)
    if job["event"] == "enable":
        x0 = E17.bypass_state(V, P, p); st0 = 0
    else:
        xe, ue = equilibrium(V, P, p); x0 = np.array(xe, float); st0 = 3
    u0 = np.array([x0[1] / x0[4], 0.])
    q0 = float(-(x0[0] + K[:4] @ x0[:4]) / K[4])
    sup = [c["VW"], c["upper"], E17.H, p.R, p.Rh, p.Cs, p.Lh, p.inner_tau, p.Clink, j.get("vd", E17.VD),
           E17.T_EV, EV[job["event"]], POL.get(job.get("policy", "clamp_brk"), 4), 1. if job.get("prep") == "steer" else 0.,
           1. if job.get("close") == "steer" else 0., j.get("t_prep", E17.T_PREP), j.get("wait", E17.T_WAIT),
           E17.RAMP, E17.HOLD, E17.ZERO, j.get("t_shed", E17.T_SHED), E17.RATE_COL, E17.VL_SOFT, j.get("t_soft", E17.T_SOFT),
           E17.R_SOFT0, E17.R_BYP, E17.T_COL_MAX, E17.VL_SW[0], E17.VL_SW[1], E17.T_SW, E17.VB_SW, E17.T_VB,
           E17.KP_B, E17.KI_B, E17.QB_MAX, E17.W_L, E17.TAU_ST, 1e6, p.power_max, p.link_max, p.turns, p.phase_max,
           p.fs, p.Ldab, V, st0, p.Ts, E17.VS_GATE, E17.T_GATE, E17.T_GATE_MAX,
           E17.VL_STALL, E17.T_STALL, E17.DV_STALL, E17.DI_SOFT, E17.K_UP, E17.T_SOFT_MAX]
    prot = [E17.T_HW, E17.I_HW, E17.VL_HW, E17.VS_HW, c["upper"], FTYPE.get(job["event"], 0), E17.T_EV, E17.T_GDF]
    init = dict(case=name, vbat=V, P0=P, Pc=min(P, E17.P_C), t_end=job["duration"], x0=x0[:6].tolist(), vcd0=float(x0[2]),
                u0=u0.tolist(), q0=q0, st0=st0, VW=c["VW"], upper=c["upper"], dab_rated_W=p.power_max, turns=p.turns, Ldab=p.Ldab,
                eta=p.eta, R_bypass=E17.R_BYP, Vd=j.get("vd", E17.VD), Rbrk=E17.R_BRK, Rdmp=E17.R_DMP, Cdmp=E17.C_DMP,
                sup_prm=sup, prot_prm=prot, event=job["event"], policy=job.get("policy", "-"))
    json.dump(init, open(f"TB09_{name}_init.json", "w"), indent=1)
    L = tr["log"]; t = tr["t"]
    np.savetxt(f"TB09_{name}_avg.csv", np.column_stack([t, L[:, :6], L[:, 6], L[:, 7], L[:, 8], L[:, 9]]), delimiter=",",
               header="t_s,ip,vs,vbus,ih,vlink,idab,ibyp,loads400,bridge,Pbrk", comments="", fmt="%.9g")
    keep = {k: v for k, v in m.items() if k not in ("trace",)}
    json.dump(keep, open(f"TB09_{name}_metrics.json", "w"), indent=1, default=float)
    out[name] = dict(pass_=m["pass_"], failed=[k for k, v in m["checks"].items() if not v], events=m["events"],
                     path_peak=m["path_peak"], bridge_peak=m["bridge_peak"], vbus_min=m["vbus_min"], vbus_max=m["vbus_max"],
                     vbus_max_loaded=m["vbus_max_loaded"], vlink_max=m["vlink_max"], vlink_min=m["vlink_min"],
                     byp_peak=m["byp_peak"], vs_at_close=m.get("vs_at_close"), byp_pulse_A=m.get("byp_pulse_A"),
                     brk_energy_J=m["brk_energy_J"], fault_bus_min=m.get("fault_bus_min"), soft_entry=m.get("soft_entry"),
                     soft_ms=m.get("soft_ms"), soft_energy_J=m.get("soft_energy_J"), dab_sec_peak=m.get("dab_sec_peak"),
                     dab_peak_state=m.get("dab_peak_state"), dab_rated_sec_peak=m.get("dab_rated_sec_peak"))
    print(name, "PASS" if m["pass_"] else "FAIL", out[name])
json.dump(out, open("TB09_ref_summary.json", "w"), indent=1, default=float)
