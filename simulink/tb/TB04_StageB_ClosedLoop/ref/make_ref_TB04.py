"""TB04 기준값 생성: 검증 모델(E12 스위칭 ODE, model_stage_b_switching.simulate_switching)로 같은 폐루프 사례를 계산한다.

사례: A) 640 V, 15 → 25 kW(Tier-1 대표, 가장 큰 전류)   B) 788 V, 0 → 10 kW(경부하, DAB 저전류 구간)
조건: 평형점에서 시작(사전 계산 없음, t_pre = 0), 1 ms에 부하 계단, 4 ms까지. 이상 센서, 전달지연 5 µs,
      채택 제어기(1주기 예측, ρ̂·ε̂ 보정, 교정표 데드타임 보상) — E12 기본 설정과 같다.
결과(사례마다): TB04_<사례>_init.json(초기조건·제어기 초기상태), TB04_<사례>_rec.csv(5 µs 주기 기록),
      TB04_<사례>_wave.csv(계단 전후 0.95–1.25 ms, 50 ns 간격 상태 파형)
실행: python make_ref_TB04.py <검증 코드 python 폴더>
"""
import json, sys
import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
from controller_reference import NOMINAL                      # noqa: E402
from controller_adopted import K_ADOPTED, CP                  # noqa: E402
from model_stage_b import equilibrium                         # noqa: E402
from model_stage_b_switching import simulate_switching, _phase_ff, _cp_vec, _loss   # noqa: E402

CASES = {"A_640V_15to25kW": (640., 15000., 25000.), "B_788V_0to10kW": (788., 0., 10000.)}
REC_COLS = ["vbus", "ip", "ih", "vlink", "ilink", "plink", "ih_max", "ih_min", "ip_absmax", "vbus_min", "vbus_max",
            "vlink_min", "vlink_max", "iL_absmax", "m_cmd", "ilink_cmd", "phase", "vs_absmax", "m_pwm", "iL_mean",
            "ploss", "rho", "eps", "r_f", "fault"]
for name, (v, a, b) in CASES.items():
    r = simulate_switching(v, a, b, NOMINAL, CP, K_ADOPTED, predict=True, profile=0, duration=4e-3, step=1e-3,
                           sw=dict(t_pre=0.), capture=[0.95e-3, 1.25e-3, 10])
    x0, u0 = equilibrium(v, a, NOMINAL)
    K = np.asarray(K_ADOPTED, float)
    q0 = -(x0[0] + K[0] * x0[0] + K[1] * x0[1] + K[2] * x0[2] + K[3] * x0[3]) / K[4]
    ph0 = _phase_ff(u0[1], x0[2], _cp_vec(CP), 0.9)
    init = dict(vbat=v, P0=a, P1=b, t_step=1e-3, t_end=4e-3, x0=[float(z) for z in x0], u0=[float(z) for z in u0],
                q0=float(q0), ph0=float(ph0), ploss0=float(_loss(x0[4] * u0[1], NOMINAL.eta)), eta=NOMINAL.eta,
                completed=r["completed"], energy_residual_W=r["energy_residual_W"],
                state_order="ip vs vbus ih vlink iL", K=[float(z) for z in K])
    json.dump(init, open(f"TB04_{name}_init.json", "w"), indent=1)
    rec = r["rec"]
    np.savetxt(f"TB04_{name}_rec.csv", np.c_[r["t"], rec], delimiter=",", header="t_end_s," + ",".join(REC_COLS),
               comments="", fmt="%.9g")
    w = r["wave"]
    np.savetxt(f"TB04_{name}_wave.csv", w, delimiter=",", header="t_s,ip,vs,vbus,ih,vlink,iL,sA_minus_sB,s1",
               comments="", fmt="%.7g")
    pre = (r["t"] > 0.8e-3) & (r["t"] <= 1e-3); post = r["t"] > 1e-3
    print(name, "completed", r["completed"], "x0", np.round(x0, 3), "u0", np.round(u0, 4), "ph0 %.4f" % ph0)
    print("  pre-step mean vbus %.3f ip %.2f ih %.2f vlink %.2f ilink %.2f rho %.3f" % tuple(rec[pre][:, [0, 1, 2, 3, 4, 21]].mean(0)))
    print("  post: vbus min %.2f max %.2f, |ip| max %.2f, ih max %.2f min %.2f, ilink max %.2f, final vbus %.3f eps %.2f" % (
        rec[post, 9].min(), rec[post, 10].max(), rec[post, 8].max(), rec[post, 6].max(), rec[post, 7].min(),
        rec[post, 4].max(), rec[-1, 0], rec[-1, 22]))
