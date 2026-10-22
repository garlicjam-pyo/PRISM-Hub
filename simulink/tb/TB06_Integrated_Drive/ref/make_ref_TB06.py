"""TB06 기준값 생성: 통합 회로 모델(Stage A 1모듈 + Stage B + Stage C + 정전력 부하)과 비교할 검증 모델 계산.

(1) Stage B 폐루프 — 검증 모델 E12(스위칭 ODE, model_stage_b_switching.simulate_switching).
    Stage A는 등가 전원(V_bat/2, 경로 13.2 mΩ·1.5 µH, Stage A 출력저항 포함)으로, Stage C는 버스 정전력 부하로 둔다.
    부하는 버스 총부하(Stage C 입력 포함)다. 평형점에서 시작, 2 ms에 부하 계단, 5 ms까지(TB04는 1 ms 계단·4 ms).
    결과: TB06_<사례>_init.json, _rec.csv(5 µs 주기 기록), _wave.csv(계단 전후 1.95–2.25 ms 상태 파형)
(2) Stage A — 검증 모델 E1(model_stage_a.sim_array, 영교차 추종 'zcp', 2위상 = 1모듈).
    출력 커패시터 400 µF(V_A 노드)에 일정 전류를 끄는 조건에서, (1)의 계단 전·끝 평균 경로전류로 정상상태를 계산한다.
    결과: TB06_<사례>_stageA.json(위상별 ZCS 비율·피크 전류·평균 출력전류, V_A 평균·리플)
실행: python make_ref_TB06.py <검증 코드 python 폴더>
"""
import json, sys
import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
from controller_reference import NOMINAL                      # noqa: E402
from controller_adopted import K_ADOPTED, CP                  # noqa: E402
from model_stage_b import equilibrium                         # noqa: E402
from model_stage_b_switching import simulate_switching, _phase_ff, _cp_vec, _loss   # noqa: E402
import model_stage_a as A                                     # noqa: E402

T_STEP, T_END = 2e-3, 5e-3
CASES = {"A_640V_15to25kW": (640., 15000., 25000.),     # Tier-1 대표, 가장 큰 경로전류(설계 코너)
         "B_788V_5to15kW":  (788., 5000., 15000.),      # 직렬전압 ≈ 0 부근, DAB 저전류 구간
         "C_920V_25to15kW": (920., 25000., 15000.)}     # 음의 직렬전압, 링크 → 버스 방향, Stage A 최고 전압
REC_COLS = ["vbus", "ip", "ih", "vlink", "ilink", "plink", "ih_max", "ih_min", "ip_absmax", "vbus_min", "vbus_max",
            "vlink_min", "vlink_max", "iL_absmax", "m_cmd", "ilink_cmd", "phase", "vs_absmax", "m_pwm", "iL_mean",
            "ploss", "rho", "eps", "r_f", "fault"]


def stage_a_ref(vbat, iout):
    """E1 영교차 추종 2위상: V_A 노드 400 µF에 일정 전류 iout을 끄는 정상상태(마지막 10주기)."""
    r = A.sim_array(N=2, Vbat=vbat, Iload=iout, Cbus=400e-6, mode="zcp", ncyc=80)
    ph, bus = A.analyze(r, ncyc_last=10)
    return dict(iout=float(iout), vA_mean=bus["Vbus"], vA_ripple=bus["ripple"],
                zcs=[p["zcs"] for p in ph], Ipk=[p["Ipk"] for p in ph], Iavg=[p["Iavg"] for p in ph],
                fs=[p["fs"] for p in ph], vA_ideal=vbat / 2)


for name, (v, a, b) in CASES.items():
    r = simulate_switching(v, a, b, NOMINAL, CP, K_ADOPTED, predict=True, profile=0, duration=T_END, step=T_STEP,
                           sw=dict(t_pre=0.), capture=[T_STEP - 0.05e-3, T_STEP + 0.25e-3, 10])
    x0, u0 = equilibrium(v, a, NOMINAL)
    K = np.asarray(K_ADOPTED, float)
    q0 = -(x0[0] + K[0] * x0[0] + K[1] * x0[1] + K[2] * x0[2] + K[3] * x0[3]) / K[4]
    ph0 = _phase_ff(u0[1], x0[2], _cp_vec(CP), 0.9)
    init = dict(vbat=v, P0=a, P1=b, t_step=T_STEP, t_end=T_END, x0=[float(z) for z in x0], u0=[float(z) for z in u0],
                q0=float(q0), ph0=float(ph0), ploss0=float(_loss(x0[4] * u0[1], NOMINAL.eta)), eta=NOMINAL.eta,
                completed=r["completed"], energy_residual_W=r["energy_residual_W"],
                state_order="ip vs vbus ih vlink iL", K=[float(z) for z in K],
                note="P0, P1 are total bus loads (Stage C input included)")
    json.dump(init, open(f"TB06_{name}_init.json", "w"), indent=1)
    rec = r["rec"]
    np.savetxt(f"TB06_{name}_rec.csv", np.c_[r["t"], rec], delimiter=",", header="t_end_s," + ",".join(REC_COLS),
               comments="", fmt="%.9g")
    np.savetxt(f"TB06_{name}_wave.csv", r["wave"], delimiter=",", header="t_s,ip,vs,vbus,ih,vlink,iL,sA_minus_sB,s1",
               comments="", fmt="%.7g")
    t = r["t"]
    pre = (t > T_STEP - 0.2e-3) & (t <= T_STEP); fin = t > T_END - 0.2e-3; post = t > T_STEP
    ip_pre, ip_fin = rec[pre, 1].mean(), rec[fin, 1].mean()
    sa = dict(pre=stage_a_ref(v, ip_pre), final=stage_a_ref(v, ip_fin),
              note="E1 zcp, N=2 phases (module 1), C_out 400 uF, constant output current = mean path current of the E12 reference")
    json.dump(sa, open(f"TB06_{name}_stageA.json", "w"), indent=1)
    print(name, "completed", r["completed"], "x0", np.round(x0, 3), "ph0 %.4f" % ph0)
    print("  pre: vbus %.3f ip %.2f ilink %.2f rho %.3f | post: vbus min %.2f max %.2f |ip|max %.2f ilink max %.2f final vbus %.3f ip %.2f"
          % (rec[pre, 0].mean(), ip_pre, rec[pre, 4].mean(), rec[pre, 21].mean(), rec[post, 9].min(), rec[post, 10].max(),
             rec[post, 8].max(), np.abs(rec[post, 4]).max(), rec[fin, 0].mean(), ip_fin))
    for k in ("pre", "final"):
        s = sa[k]
        print("  Stage A %-5s iout %.2f A: V_A %.3f V (ideal %.1f), ripple %.3f V, zcs %s, Ipk %s" % (
            k, s["iout"], s["vA_mean"], s["vA_ideal"], s["vA_ripple"], np.round(s["zcs"], 4), np.round(s["Ipk"], 2)))
