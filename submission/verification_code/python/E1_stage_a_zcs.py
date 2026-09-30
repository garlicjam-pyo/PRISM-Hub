"""[E1] Stage A 스위칭 ODE 시험: 영전류 스위칭(ZCS), 손실, 모듈 셰딩, 프리차지.

■ 목적
  Stage A(2:1 RSC)는 충전 전류 대부분(최대 375 A)을 직접 처리하므로, 공진 부품에 공차가 있어도
  턴오프 순간 전류가 거의 0이어야(ZCS) 효율과 소자 스트레스 목표를 지킬 수 있다. 이 시험은
  (1) 고정 타이밍으로는 공차에서 ZCS가 깨진다는 것과 (2) 영교차 추종(자기발진) 타이밍이 정·역방향
  모두에서 ZCS를 유지한다는 것을 보이고, 정격 손실·경부하 셰딩·기동 돌입을 추정한다.

■ 왜 필요한가
  공진 스위치드 커패시터의 장점(고효율·소형)은 ZCS에 의존한다. 부품 공차(C ±5 %, L ±10 %)만으로
  실제 공진주파수가 수 % 달라지므로, 타이밍 방식이 공차를 흡수할 수 있는지가 아키텍처 성립 조건이다.
  V2L·V2H처럼 버스에서 배터리로 전력이 흐르는 역방향도 같은 방식으로 동작해야 한다.

■ 방법 (모델: model_stage_a.py, MATLAB 동일 구현: matlab/prism_sim_array.m)
  1) 부품 공차 표본 시험(보고서 표 6.1 1·2행): 단상, 46.875 A(375 A / 8위상), C ±5 %, L ±10 %, R ±10 %
     균일분포 20개 표본. 같은 표본으로 ① 고정 타이밍 0.98·f_r0 ② 영교차 추종 정방향
     ③ 영교차 추종 역방향(−46.875 A)을 비교한다(짝지은 표본).
  2) 8위상 양방향 시험(보고서 표 6.1 3행): 788 V, ±375 A, 공칭 및 C·L·R ±10 % 공차, 60주기.
     정방향·공차 사례에서 총 손실과 모듈(2위상 묶음) 전류 편차를 구한다.
  3) 경부하 모듈 셰딩(표 6.1 4행): 3 kW(7.5 A)에서 1모듈(2위상)만 운전한 경우와 8위상 모두 운전한 경우의 손실.
  4) 프리차지(표 6.1 5행): 20 Ω 저항과 100 µF 입력 커패시터, 버스·플라잉 커패시터 0 V에서 무부하
     스위칭 기동. 위상 피크 전류와 버스가 95 %(0.95 × 394 V)에 도달하는 시간.

■ 판정 기준
  ZCS 품질 = 턴오프 순간 전류 / 피크 전류 ≤ 5 %  (마지막 10주기)
  고정 타이밍은 기준 초과가 나오는 것이 예상 결과(영교차 추종이 필요한 근거)이고,
  영교차 추종은 정·역방향 표본 전부와 8위상 4개 사례가 기준 이내여야 한다.

■ 실행   python E1_stage_a_zcs.py            (약 3–4분, 대부분 프리차지 시험)
■ 결과   results/E1/stage_a.json, results/E1/E1_tolerance_samples.png
■ 보고서 수치(MATLAB 실행값): 고정 16/20 초과·최대 40.1 %, 영교차 추종 0/20·최대 약 1.1 %,
         8위상 466 W·모듈 편차 −3.3 ~ +2.2 %, 셰딩 31.6 W 대 120.5 W, 프리차지 15.5 A·13.2 ms.
         공차 난수는 matlab_rng()로 MATLAB과 같은 표본을 쓰므로 Python 결과도 같은 값이 나와야 한다.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from model_stage_a import sim_array, analyze, matlab_rng
from common import save_json, verdict, outdir

ZCS_LIMIT = 0.05


def tolerance_samples(n=20):
    """1) 부품 공차 표본 20개로 고정 타이밍과 영교차 추종(정·역방향)을 짝지어 비교한다."""
    tol = dict(C=0.05, L=0.10, R=0.10)
    rs = matlab_rng(0)                       # MATLAB: rng(0)
    rows = []
    for k in range(n):
        state = rs.get_state()               # MATLAB: paired_rng = rng
        a, _ = analyze(sim_array(N=1, Iload=46.875, mode="fixed", fratio=0.98, tol=tol, rs=rs, ncyc=50))
        rs.set_state(state)                  # 같은 표본으로 다시
        b, _ = analyze(sim_array(N=1, Iload=46.875, mode="zcp", fratio=1.0, tol=tol, rs=rs, ncyc=50))
        rs.set_state(state)
        c, _ = analyze(sim_array(N=1, Iload=-46.875, mode="zcp", fratio=1.0, tol=tol, rs=rs, ncyc=50))
        rows.append(dict(fs_over_fr_fixed=a[0]["fr_ratio"],
                         zcs_fixed=a[0]["zcs"], zcs_zcp_fwd=b[0]["zcs"], zcs_zcp_rev=c[0]["zcs"],
                         loss_fixed=a[0]["Ploss"], loss_zcp_fwd=b[0]["Ploss"], loss_zcp_rev=c[0]["Ploss"]))
    return rows


def eight_phase():
    """2) 8위상 ±375 A, 공칭·공차(±10 %). MATLAB과 같이 각 사례 전에 rng(3)으로 초기화한다."""
    out = []
    for direction in (1, -1):
        for tolerance in (False, True):
            tol = dict(C=0.1, L=0.1, R=0.1) if tolerance else None
            r = sim_array(N=8, Iload=375. * direction, mode="zcp", fratio=1.0, tol=tol,
                          rs=matlab_rng(3), ncyc=60)
            ph, bus = analyze(r)
            Iav = np.array([p["Iavg"] for p in ph]); mod = Iav.reshape(4, 2).sum(1)   # 모듈 = 2위상
            out.append(dict(direction=direction, tolerance=tolerance,
                            zcs_max=max(p["zcs"] for p in ph), Vbus=bus["Vbus"], ripple=bus["ripple"],
                            Iout=float(Iav.sum()), loss_total=sum(p["Ploss"] for p in ph),
                            module_current=mod, module_dev_pct=(mod - mod.mean()) / mod.mean() * 100))
    return out


def shedding():
    """3) 3 kW 경부하: 1모듈(위상 1·2)만 운전 vs 8위상 운전."""
    out = {}
    for name, en in (("one_module", [1, 1, 0, 0, 0, 0, 0, 0]), ("all_phases", [1] * 8)):
        ph, bus = analyze(sim_array(N=8, Iload=7.5, mode="zcp", en=en, ncyc=40))
        loss = sum(p["Ploss"] for p, e in zip(ph, en) if e)
        out[name] = dict(loss=loss, eta_pct=3e3 / (3e3 + loss) * 100, Vbus=bus["Vbus"])
    return out


def precharge():
    """4) 20 Ω 프리차지 기동. 적분 간격을 절반 해상도(170단계/주기)로 두고 2,300주기(약 15 ms)."""
    r = sim_array(N=8, Iload=0.0, mode="zcp", fratio=1.0, R_in=20.0, C_in=100e-6,
                  vC0=0.0, Vbus0=0.0, ncyc=2300, Nstep=170)
    ipk = float(np.max(np.abs(r["i"])))
    hit = np.where(r["vb"] >= 0.95 * 394)[0]
    return dict(peak_phase_current=ipk, t95_ms=float(r["t"][hit[0]] * 1e3) if len(hit) else None,
                Vbus_end=float(r["vb"][-1]))


if __name__ == "__main__":
    print("[E1] Stage A 스위칭 ODE 시험")
    res = {}

    print("1) 부품 공차 표본 20개 (고정 타이밍 vs 영교차 추종 정·역방향)")
    rows = tolerance_samples()
    z = {k: np.array([r[k] for r in rows]) for k in ("zcs_fixed", "zcs_zcp_fwd", "zcs_zcp_rev")}
    for k, name in (("zcs_fixed", "고정 0.98 f_r"), ("zcs_zcp_fwd", "영교차 추종 정방향"), ("zcs_zcp_rev", "영교차 추종 역방향")):
        print(f"   {name:14s}: 기준 초과 {int((z[k] > ZCS_LIMIT).sum())}/20, 최대 {z[k].max()*100:.1f} %")
    res["tolerance_samples"] = dict(rows=rows, n_fail_fixed=int((z["zcs_fixed"] > ZCS_LIMIT).sum()),
                                    max_fixed=z["zcs_fixed"].max(),
                                    n_fail_zcp=int((z["zcs_zcp_fwd"] > ZCS_LIMIT).sum() + (z["zcs_zcp_rev"] > ZCS_LIMIT).sum()),
                                    max_zcp=max(z["zcs_zcp_fwd"].max(), z["zcs_zcp_rev"].max()))
    verdict("고정 타이밍은 공차에서 ZCS 기준을 넘는 표본이 생긴다(영교차 추종의 필요성)", (z["zcs_fixed"] > ZCS_LIMIT).any())
    verdict("영교차 추종은 정·역방향 40개 표본 모두 ZCS ≤ 5 %",
            (z["zcs_zcp_fwd"] <= ZCS_LIMIT).all() and (z["zcs_zcp_rev"] <= ZCS_LIMIT).all())

    print("2) 8위상 ±375 A, 공칭·공차 ±10 %")
    ep = eight_phase()
    for e in ep:
        print(f"   방향 {e['direction']:+d}, 공차 {'있음' if e['tolerance'] else '없음'}: ZCS 최대 {e['zcs_max']*100:.3f} %, "
              f"V_bus {e['Vbus']:.1f} V, 출력 {e['Iout']:.1f} A, 손실 {e['loss_total']:.0f} W")
    a2 = next(e for e in ep if e["direction"] == 1 and e["tolerance"])
    print(f"   정방향·공차: 모듈 전류 편차 {np.round(a2['module_dev_pct'], 1)} %")
    res["eight_phase"] = ep
    verdict("8위상 4개 사례 모두 ZCS ≤ 5 %", all(e["zcs_max"] <= ZCS_LIMIT for e in ep))

    print("3) 3 kW 모듈 셰딩")
    sh = shedding(); res["shedding"] = sh
    print(f"   1모듈 {sh['one_module']['loss']:.1f} W (효율 {sh['one_module']['eta_pct']:.2f} %), "
          f"8위상 {sh['all_phases']['loss']:.1f} W (효율 {sh['all_phases']['eta_pct']:.2f} %)")

    print("4) 프리차지 (20 Ω, 무부하 스위칭 기동)")
    pc = precharge(); res["precharge"] = pc
    print(f"   위상 피크 {pc['peak_phase_current']:.1f} A, 95 % 도달 {pc['t95_ms']:.1f} ms")

    save_json("E1", "stage_a", res)

    # 그림: 공차 표본별 ZCS 품질
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    x = np.array([r["fs_over_fr_fixed"] for r in rows])
    ax.scatter(x, z["zcs_fixed"] * 100, c="C3", label="Fixed timing 0.98 f_r0")
    ax.scatter(x, z["zcs_zcp_fwd"] * 100, c="C0", marker="o", label="ZC tracking, forward")
    ax.scatter(x, z["zcs_zcp_rev"] * 100, c="C2", marker="x", label="ZC tracking, reverse")
    ax.axhline(5, color="k", ls="--", lw=1)
    ax.set_xlabel("f_s / f_r,actual (fixed-timing sample)"); ax.set_ylabel("|i_off| / I_pk (%)")
    ax.set_title("E1: 20 tolerance samples (C±5 %, L±10 %, R±10 %)"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(outdir("E1") / "E1_tolerance_samples.png", dpi=150); plt.close(fig)
