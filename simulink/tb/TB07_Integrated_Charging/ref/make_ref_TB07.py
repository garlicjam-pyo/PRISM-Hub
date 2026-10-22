"""TB07 기준값 생성: 통합 회로 모델(충전 모드: Stage A 4모듈 + 충전기 + Stage B + Stage C)과 비교할 검증 모델 계산.

(1) Stage B 폐루프 — 검증 모델 E16 스위칭 모드(E12 엔진 model_stage_b_switching.simulate_switching).
    Stage A는 충전 모드 등가 전원으로 둔다: 경로 전원 v_src = V_bat/2 + R_A·i_ch, 경로저항 R = R_A + 3 mΩ,
    R_A = 10.2 mΩ/4(4모듈). 제어기는 주행과 같다(공칭 경로저항 13.2 mΩ, V_bat 측정값 = 실제 배터리 전압).
    충전전류 변화는 경로 전원의 10 µs 선형 변화로 넣는다(src_t0 → src_t1). Stage C는 버스 정전력 부하.
    부하는 버스 총부하(Stage C 입력 포함). 평형점에서 시작, 2 ms에 계단 또는 충전전류 전환, 5 ms까지.
    결과: TB07_<사례>_init.json, _rec.csv(5 µs 주기 기록), _wave.csv(전환 전후 1.95–2.25 ms 상태 파형)
(2) Stage A — 검증 모델 E1(model_stage_a.sim_array, 영교차 추종 'zcp', 8위상 = 4모듈).
    V_A 노드 400 µF에서 일정 전류 i_out = i_p − i_ch(충전 중 음수)를 끄는 조건으로, (1)의 전환 전·끝 평균 경로전류와
    그 구간의 충전전류로 정상상태를 계산한다.
    결과: TB07_<사례>_stageA.json
실행: python make_ref_TB07.py <검증 코드 python 폴더> [사례1,사례2,...]
"""
import json, sys
from dataclasses import replace
import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
from controller_reference import NOMINAL                      # noqa: E402
from controller_adopted import K_ADOPTED, CP                  # noqa: E402
from model_stage_b import equilibrium                         # noqa: E402
from model_stage_b_switching import simulate_switching, _phase_ff, _cp_vec, _loss   # noqa: E402
import model_stage_a as A                                     # noqa: E402

T_STEP, T_END, T_RAMP = 2e-3, 5e-3, 10e-6
RA = 10.2e-3 / 4; RW = 3.0e-3
PLANT = replace(NOMINAL, R=RA + RW)


def ich_max(V):
    return min(375., 150e3 / (V / 2))


# 사례: (V_bat, 버스 총부하 계단 전, 후, 충전전류 전, 후, 판정 등급, 충전전류 변화 시간)
CASES = {"A_640V_chg_15to25kW": (640., 15000., 25000., 375., 375., 1, T_RAMP),          # 충전 중 동시 운전, 가장 큰 경로전류
         "B_920V_chgstop_25kW": (920., 25000., 25000., ich_max(920.), 0., 2, T_RAMP),  # 충전 비상 정지(음의 직렬전압, 최고 전압)
         "C_788V_chgon_5kW":    (788., 5000., 5000., 0., 375., 2, T_RAMP),             # 충전기 접속(직렬전압 ≈ 0, DAB 저전류)
         # 추가 실행(2026-10-22): 충전전류 변화 속도 의존(사례 C를 100 µs·1 ms로)과 최대 경로전류 코너(640 V, 25 kW)
         "C2_788V_chgon_5kW_100us": (788., 5000., 5000., 0., 375., 2, 100e-6),
         "C3_788V_chgon_5kW_1ms":   (788., 5000., 5000., 0., 375., 2, 1e-3),
         "D_640V_chgon_25kW":       (640., 25000., 25000., 0., 375., 2, T_RAMP),
         "E_640V_chgstop_25kW":     (640., 25000., 25000., 375., 0., 2, T_RAMP)}
ONLY = sys.argv[2].split(",") if len(sys.argv) > 2 else None   # 일부 사례만 다시 계산
REC_COLS = ["vbus", "ip", "ih", "vlink", "ilink", "plink", "ih_max", "ih_min", "ip_absmax", "vbus_min", "vbus_max",
            "vlink_min", "vlink_max", "iL_absmax", "m_cmd", "ilink_cmd", "phase", "vs_absmax", "m_pwm", "iL_mean",
            "ploss", "rho", "eps", "r_f", "fault"]


def stage_a_ref(vbat, iout):
    """E1 영교차 추종 8위상: V_A 노드 400 µF에 일정 전류 iout(Stage A → V_A 양수)을 끄는 정상상태(마지막 10주기)."""
    r = A.sim_array(N=8, Vbat=vbat, Iload=iout, Cbus=400e-6, mode="zcp", ncyc=80)
    ph, bus = A.analyze(r, ncyc_last=10)
    return dict(iout=float(iout), vA_mean=bus["Vbus"], vA_ripple=bus["ripple"],
                zcs=[p["zcs"] for p in ph], Ipk=[p["Ipk"] for p in ph], Iavg=[p["Iavg"] for p in ph],
                fs=[p["fs"] for p in ph], vA_ideal=vbat / 2)


for name, (v, a, b, i0, i1, tier, tr) in CASES.items():
    if ONLY and name not in ONLY:
        continue
    vb0 = v + 2 * RA * i0; vb1 = v + 2 * RA * i1                  # 플랜트 경로 전원 2·v_src(전환 전·후)
    sw = dict(t_pre=0., ctrl_vbat=v)
    if i0 != i1:
        sw.update(src_t0=T_STEP, src_t1=T_STEP + tr, src_vbat1=vb1)
    r = simulate_switching(vb0, a, b, PLANT, CP, K_ADOPTED, predict=True, profile=0, duration=T_END, step=T_STEP,
                           sw=sw, capture=[T_STEP - 0.05e-3, T_STEP + 0.25e-3, 10])
    x0, u0 = equilibrium(vb0, a, PLANT)
    K = np.asarray(K_ADOPTED, float)
    q0 = -(x0[0] + K[0] * x0[0] + K[1] * x0[1] + K[2] * x0[2] + K[3] * x0[3]) / K[4]
    ph0 = _phase_ff(u0[1], x0[2], _cp_vec(CP), 0.9)
    init = dict(vbat=v, P0=a, P1=b, t_step=T_STEP, t_end=T_END, tier=tier, chg_prm=[i0, i1, T_STEP, tr],
                RA=RA, Rpath=RW, x0=[float(z) for z in x0], u0=[float(z) for z in u0],
                q0=float(q0), ph0=float(ph0), ploss0=float(_loss(x0[4] * u0[1], NOMINAL.eta)), eta=NOMINAL.eta,
                completed=r["completed"], energy_residual_W=r["energy_residual_W"],
                state_order="ip vs vbus ih vlink iL", K=[float(z) for z in K],
                note="P0, P1 are total bus loads (Stage C input included); plant source V_bat/2 + RA*i_ch, R = RA + Rpath; "
                     "controller uses nominal R 13.2 mOhm and the true V_bat")
    json.dump(init, open(f"TB07_{name}_init.json", "w"), indent=1)
    rec = r["rec"]
    np.savetxt(f"TB07_{name}_rec.csv", np.c_[r["t"], rec], delimiter=",", header="t_end_s," + ",".join(REC_COLS),
               comments="", fmt="%.9g")
    np.savetxt(f"TB07_{name}_wave.csv", r["wave"], delimiter=",", header="t_s,ip,vs,vbus,ih,vlink,iL,sA_minus_sB,s1",
               comments="", fmt="%.7g")
    t = r["t"]
    pre = (t > T_STEP - 0.2e-3) & (t <= T_STEP); fin = t > T_END - 0.2e-3; post = t > T_STEP
    ip_pre, ip_fin = rec[pre, 1].mean(), rec[fin, 1].mean()
    sa = dict(pre=stage_a_ref(v, ip_pre - i0), final=stage_a_ref(v, ip_fin - i1), ich_pre=i0, ich_final=i1,
              note="E1 zcp, N=8 phases (4 modules), C_out 400 uF, constant output current = mean path current - charger current")
    json.dump(sa, open(f"TB07_{name}_stageA.json", "w"), indent=1)
    print(name, "completed", r["completed"], "x0", np.round(x0, 3), "ph0 %.4f" % ph0)
    print("  pre: vbus %.3f ip %.2f ilink %.2f | post: vbus min %.2f max %.2f |ip|max %.2f ilink max %.2f final vbus %.3f ip %.2f"
          % (rec[pre, 0].mean(), ip_pre, rec[pre, 4].mean(), rec[post, 9].min(), rec[post, 10].max(),
             rec[post, 8].max(), np.abs(rec[post, 4]).max(), rec[fin, 0].mean(), ip_fin))
    for k in ("pre", "final"):
        s = sa[k]
        print("  Stage A %-5s iout %.2f A: V_A %.3f V (ideal %.1f), ripple %.3f V, zcs max %.4f, Ipk %.2f-%.2f"
              % (k, s["iout"], s["vA_mean"], s["vA_ideal"], s["vA_ripple"], max(s["zcs"]), min(s["Ipk"]), max(s["Ipk"])))
