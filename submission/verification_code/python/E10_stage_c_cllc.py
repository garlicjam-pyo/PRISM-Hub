"""[E10] Stage C(CLLC 400 V → 48 V) 3 kW 스위칭 ODE 시험: 공진점 이득과 ZVS 여유.

■ 목적
  Stage C는 400 V 보조버스에서 48 V 전원망을 공급하는 대칭 CLLC 공진 변환기이며, 보조버스가 400±8 V로
  조정된다는 전제에서 공진점 부근의 고정이득(주파수 고정)으로 운전한다(보고서 4.4절). 이 시험은
  3 kW 후보 설계에서 (1) 공진점의 전압이득이 1에 가깝고 부하에 둔감한지, (2) 입력 ±2 %(±8 V)가 48 V
  출력에 그대로 비례해 나타나는지, (3) 1차측 영전압 스위칭(ZVS)에 필요한 전류가 확보되는지 확인한다.

■ 왜 필요한가
  Stage B가 보조버스를 400±8 V로 조정하는 가치(파생 요구, 보고서 3.2절)는 Stage C를 고정이득으로 둘 수
  있다는 데서 나온다. 고정이득 운전이 실제로 부하에 무관한 이득을 주는지 스위칭 수준에서 확인해야
  이 논리가 성립한다. 현재 요구전력은 약 5 kW이므로 이 3 kW 결과는 부분 검증이다.

■ 모델 (1차측 환산, 권선비 n = 25/3)
  상태: i_r1(1차 공진전류), v_c1, i_m(자화전류), i_r2'(2차 공진전류 환산), v_c2', V_o
  L_r1 di_r1/dt = v_p − v_c1 − v_m,  C_r1 dv_c1/dt = i_r1,  L_m di_m/dt = v_m
  L_r2' di_r2'/dt = v_m − v_c2' − v_s2',  C_r2' dv_c2'/dt = i_r2'
  자화 노드 KCL(i_r1 = i_m + i_r2')로 v_m을 대수적으로 구한다.
  1차: 50 % 구형파 ±V_in(데드타임 50 ns), 2차: 이상 동기정류(v_s2' = sign(i_r2')·n·V_o), 저항부하.
  적분: RK4, 한 주기 400단계.
  ZVS 여유 = (스위칭 순간 1차 전류 × 데드타임) / (2·C_oss·V_in)  — 1보다 크면 데드타임 안에 출력용량 충방전 가능.
  비교: 기본파 근사(FHA) 이득 1/√[(1 + (1/m)(1 − 1/f_n²))² + Q²(f_n − 1/f_n)²], m = L_m/L_r = 6

■ 판정 기준
  공진점(f_s = f_r) 이득이 0.3–3 kW에서 1 ± 3 % 이내, ZVS 여유 > 1

■ 실행   python E10_stage_c_cllc.py      (약 3–5분)
■ 결과   results/E10/stage_c.json, results/E10/E10_gain.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import save_json, verdict, outdir

n = 25 / 3                       # 권선비 400/48
fr = 250e3                       # 공진주파수 [Hz]
Lr1 = 11.0e-6; Cr1 = 36.8e-9     # 1차 공진 L, C
Lm = 66e-6                       # 자화 인덕턴스 (m = Lm/Lr = 6)
Lr2p = Lr1; Cr2p = Cr1           # 대칭 공진망(1차 환산)
Co = 470e-6                      # 48 V 출력 커패시터
Coss = 100e-12                   # 1차 스위치 출력용량
td = 50e-9                       # 데드타임


def simulate(Po=3000., fs=250e3, Vin=400., ncyc=400, Nstep=400, Vo0=48.):
    """ncyc 주기 적분 후 마지막 10주기로 평균 출력전압·이득·실효전류·ZVS 여유를 계산한다."""
    RL = 48. ** 2 / Po
    T = 1 / fs; dt = T / Nstep; N = ncyc * Nstep
    log = np.zeros((N, 6)); ndead = int(round(td / dt)); half = Nstep // 2
    ginv = 1 / (1 / Lr1 + 1 / Lm + 1 / Lr2p)

    def f(x, vp):
        ir1, vc1, im, ir2, vc2, Vo = x
        vs2 = np.sign(ir2) * n * Vo if abs(ir2) > 1e-6 else 0.0       # 이상 동기정류
        vm = ((vp - vc1) / Lr1 + (vc2 + vs2) / Lr2p) * ginv            # 자화 노드 전압
        return np.array([(vp - vc1 - vm) / Lr1, ir1 / Cr1, vm / Lm, (vm - vc2 - vs2) / Lr2p, ir2 / Cr2p,
                         (abs(ir2) * n - Vo / RL) / Co])

    x = np.array([0., 0., 0., 0., 0., Vo0])
    for k in range(N):
        m = k % Nstep
        vp = (Vin if m >= ndead else 0.0) if m < half else (-Vin if (m - half) >= ndead else 0.0)
        k1 = f(x, vp); k2 = f(x + .5 * dt * k1, vp); k3 = f(x + .5 * dt * k2, vp); k4 = f(x + dt * k3, vp)
        x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4); log[k] = x
    t = np.arange(N) * dt; msk = t >= (ncyc - 10) * T
    L = log[msk]; ir1 = L[:, 0]; im = L[:, 2]; ir2 = L[:, 3]; Vo = L[:, 5]
    # 스위칭 순간(각 반주기 끝, 데드타임 직전)의 1차 전류 = ZVS에 쓸 수 있는 전류
    idx = [i for i in range(len(ir1)) if (i % Nstep) == half - 1 or (i % Nstep) == Nstep - 1]
    i_sw = np.abs(ir1[idx]).mean()
    return dict(Vo=Vo.mean(), gain=Vo.mean() * n / Vin, Ipri_rms=np.sqrt(np.mean(ir1 ** 2)),
                Isec_rms=np.sqrt(np.mean(ir2 ** 2)) * n, Im_pk=np.abs(im).max(), i_sw=i_sw,
                zvs_margin=i_sw * td / (2 * Coss * Vin), Po=Vo.mean() ** 2 / RL)


def fha(fn, Q, m=6):
    """기본파 근사(FHA) 전압이득."""
    return 1 / np.sqrt((1 + (1 / m) * (1 - 1 / fn ** 2)) ** 2 + (Q * (fn - 1 / fn)) ** 2)


if __name__ == "__main__":
    print("[E10] Stage C CLLC 3 kW 스위칭 ODE")
    out = {}
    r = simulate()
    print(f"   공칭 3 kW, f_s = f_r: V_o {r['Vo']:.2f} V, 이득 {r['gain']:.4f}, 1차 실효 {r['Ipri_rms']:.2f} A, "
          f"2차 실효 {r['Isec_rms']:.1f} A, 자화 피크 {r['Im_pk']:.2f} A, ZVS 여유 {r['zvs_margin']:.1f}배")
    out["nominal"] = r
    rows = []
    for Po in [300., 1500., 3000.]:
        RL = 48 ** 2 / Po; Rac = 8 * n ** 2 * RL / np.pi ** 2; Q = 2 * np.pi * fr * Lr1 / Rac   # 교류 등가부하와 Q
        for fn in [0.9, 0.97, 1.0, 1.03, 1.1]:
            rr = simulate(Po=Po, fs=fn * fr, ncyc=300)
            rows.append(dict(Po=Po, fn=fn, gain_sim=rr["gain"], gain_fha=fha(fn, Q), Vo=rr["Vo"], zvs_margin=rr["zvs_margin"]))
            print(f"   {Po/1e3:.1f} kW, f_s/f_r {fn:.2f}: 이득 {rr['gain']:.3f} (FHA {fha(fn, Q):.3f}), V_o {rr['Vo']:.2f} V, ZVS 여유 {rr['zvs_margin']:.1f}배")
    out["gain_table"] = rows
    vin = {}
    for V in [392., 400., 408.]:
        vin[str(int(V))] = simulate(Vin=V, ncyc=300)["Vo"]
    print(f"   입력 392/400/408 V → V_o {vin['392']:.2f} / {vin['400']:.2f} / {vin['408']:.2f} V (고정이득이므로 입력 변동이 그대로 전달)")
    out["vin_sweep_Vo"] = vin
    g_res = [x["gain_sim"] for x in rows if x["fn"] == 1.0]
    verdict("공진점 이득이 0.3–3 kW에서 1 ± 3 % 이내", all(abs(g - 1) <= .03 for g in g_res), f"{min(g_res):.3f}–{max(g_res):.3f}")
    verdict("공진점 ZVS 여유 > 1", all(x["zvs_margin"] > 1 for x in rows if x["fn"] == 1.0),
            f"최소 {min(x['zvs_margin'] for x in rows if x['fn'] == 1.0):.1f}배")
    save_json("E10", "stage_c", out)

    fig, ax = plt.subplots(figsize=(6, 3.6))
    for Po in [300., 1500., 3000.]:
        rs = [x for x in rows if x["Po"] == Po]
        ax.plot([x["fn"] for x in rs], [x["gain_sim"] for x in rs], "o-", label=f"switching ODE {Po/1e3:.1f} kW")
        ax.plot([x["fn"] for x in rs], [x["gain_fha"] for x in rs], "--", color="gray")
    ax.axvspan(0.97, 1.03, color="y", alpha=.3); ax.set_xlabel("f_s / f_r"); ax.set_ylabel("gain n·V_o / V_in")
    ax.grid(alpha=.3); ax.legend(fontsize=8); ax.set_title("E10: CLLC gain, switching ODE (solid) vs FHA (dashed)")
    fig.tight_layout(); fig.savefig(outdir("E10") / "E10_gain.png", dpi=150); plt.close(fig)
