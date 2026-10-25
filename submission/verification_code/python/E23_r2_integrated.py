"""[E23] R2 기본형 통합: Stage A(정적 등가) + 400 V 버스(C_A·배선·C_b·RC 감쇠기) + 400 V 부하 + 조정형 Stage C의 평균모델.

■ 목적
  R2 기본형에서는 Stage B 없이 400 V 버스가 V_A(Stage A 출력)를 그대로 따른다. 조정형 Stage C(E22)는 지금까지 이상 버스
  전원(지령 전압)으로 확인했다. 이 시험은 (1) Stage A 출력 임피던스·V_A 노드 커패시터·배선·버스 감쇠기와 400 V 정전력 부하가
  있는 버스에서 Stage C의 48 V 조정과 버스 전압을 함께 계산하고, (2) Stage A 출력 커패시터 C_A를 넣은 버스 임피던스로
  Stage C 입력 임피던스와의 Middlebrook 여유를 다시 보며, (3) 회로 모델 TB16(Stage A 스위칭 회로 + 조정형 Stage C)의
  기준값과 Stage A 기준값(E1 영교차 추종)을 만든다. (4) R2-W460 창 조정 모듈의 H-브리지 개방 강등(E17) 동안 움직이는 버스에서
  48 V를 계산하고 회로 모델 TB17(Stage A + 창 조정 Stage B + 조정형 Stage C)의 기준값을 만든다.

■ 왜 필요한가
  E22 T7은 Stage A를 이상 전원 + 13.2 mΩ + 1.5 µH로 두고 C_A를 뺐다. 실제 V_A 노드에는 C_A 400 µF와 공진 스위치드
  커패시터가 있고, Stage C는 정전력 부하(음의 증분 저항)이며 입력전류를 100 kHz로 끊는다. 400 V 부하 계단은 Stage A 출력
  저항을 지나 Stage C 입력 전압을 흔들고, Stage C 부하 계단은 V_A를 흔든다. 두 단을 한 버스에서 같이 풀어야 한다.

■ 방법
  base   : E22 평균모델(run_avg)에 버스 회로를 같이 푼다(bus 인자). Stage A는 V_bat/2와 출력저항 R_A 10.2 mΩ(1모듈,
           TB06에서 회로 10.6 mΩ 확인)의 정적 등가 → C_A 400 µF → 배선 3 mΩ·1.5 µH → C_b 400 µF ∥ 감쇠기
           48.6 mΩ + 1.6 mF ∥ 400 V 정전력 부하 ∥ Stage C 입력(d·i_L). 사례 3개(TB16과 같음)를 2 ms 사건, 5 ms까지 계산한다.
           Stage A 기준값은 E1(model_stage_a, 영교차 추종 2위상)로 사건 전·끝 평균 출력전류에서 계산한다.
  zbus   : C_A와 Stage A 출력저항을 넣은 버스 임피던스와 E22 T7의 Stage C 입력 임피던스(5 kW, 270·504 V)를 비교한다.
  degrade: R2-W460 창 조정 모듈의 H-브리지 개방 강등(E17 보호 상태기계, 강등 방식은 E21 P3t = TB13과 같음, 고장 시각만
           1.5 ms) 동안 버스는 V_W 460 V → 다이오드 클램프 → 부하 분리·링크 붕괴 → 소프트 바이패스 → V_A로 움직인다. 그 버스
           궤적(5 µs 평균)을 E22 평균모델의 이상 버스 전원으로 넣어 48 V를 계산한다. Stage C 부하는 입력 5 kW(= E17 P_C)가
           되는 4.9 kW. Stage A 기준값은 E1(사건 전·끝 평균 전류, 끝은 위상 하나만 운전한 경우도). 회로 TB17의 기준값이다.
  figures: 사례 응답, 임피던스.

■ 사례(시험 전에 고정, TB16과 같음)
  A_540V_Cstep   배터리 540 V(180s × 3.0 V, V_A ≈ 270 V = Stage C 입력 최저), 400 V 부하 10 kW, Stage C 0.1 → 5 kW 계단
  B_806V_Qstep   배터리 806 V(192s × 4.2 V, V_A ≈ 403 V, B_420 부품 상한 근처), Stage C 3 kW, 400 V 부하 15 → 25 kW(10 µs)
  C_907V_Cregen  배터리 907 V(216s × 4.2 V, V_A ≈ 453 V, B_470), 400 V 부하 10 kW, Stage C 5 → −3 kW 계단(회생을 400 V 부하가 받음)

■ 판정 기준(base, 평균모델. TB16 회로에도 같은 기준)
  (a) 48 V: 사례 B ±2 %(47.04–48.96 V, 400 V 부하 계단은 Tier-2 계약 과도), 사례 A·C 36–52 V(Stage C 계단 견고성, E22·TB14와 같음)
  (b) 버스: 사건 0.2 ms 전부터 끝까지 5 µs 평균 버스가 각 정상 평형점(사건 전·뒤)의 낮은 값 − 3 % 이상, 높은 값 + 3 % 이하
  (c) 버스 안정: 끝 0.5 ms 동안 버스 진동(5 µs 평균의 최대 − 최소) ≤ 0.5 V
  (d) Stage C 전류: 출력 100 µs 평균 ≤ 136.5 A, 2차 소자 순간(π/2·|i_x|/2) ≤ 329 A
■ 판정 기준(zbus)
  |Z_bus| ≤ |Z_in|/2(6 dB, 10 Hz–20 kHz, 5 kW, 입력 270·504 V). E22 T7과 같은 기준, 버스 등가에 C_A와 R_A를 넣었다.
■ 판정 기준(degrade)
  48 V ±2 %(고장 0.2 ms 전부터 끝까지), Stage C 전류(base (d)와 같음), E17 고장 판정 통과. 정보: E1 Stage A ZCS ≤ 5 %(2위상)

■ 실행   python E23_r2_integrated.py base zbus degrade figures   (약 2분, E22 design zvs both dcx와 E21 table 결과가 있어야 함)
■ 결과   results/E23/base.json, zbus.json, degrade.json, E23_r2_integrated.png, E23_degrade.png
"""
import json
import math
import sys

import numpy as np

from common import save_json, verdict, outdir
import E22_stage_c_regulated as S

EID = "E23"

# ---------------------------------------------------------------------------------------------
# R2 기본형 버스(TB06·TB08–TB13·E22 zbus와 같은 값)
# ---------------------------------------------------------------------------------------------
RA = 10.2e-3       # Stage A 1모듈 출력저항(설계 추정, TB06 회로 10.6 mΩ)
CA = 400e-6        # V_A 노드 출력 커패시터
RW = 3e-3          # 배선
LW = 1.5e-6
CB = 400e-6        # 버스 커패시터
RD = 48.6e-3       # RC 감쇠기
CD = 1.6e-3
VMIN_Q = 200.      # 400 V 정전력 부하 전압 하한(부하 전류 = P/max(v, 200 V))
T0 = 2e-3          # 사건 시각(Stage A 회로가 정착하도록 2 ms 뒤)
T_END = 5e-3

CASES = {
    "A_540V_Cstep": dict(vbat=540., tQ=[0, 1], QQ=[10000., 10000.], tP=[0, T0, T0 + 1e-9, 1], PP=[100., 100., 5000., 5000.],
                         band=(S.VO_CV[0], S.VO_CV[1])),
    "B_806V_Qstep": dict(vbat=806., tQ=[0, T0, T0 + 10e-6, 1], QQ=[15000., 15000., 25000., 25000.], tP=[0, 1], PP=[3000., 3000.],
                         band=(S.VO_NOM * (1 - S.VO_TOL), S.VO_NOM * (1 + S.VO_TOL))),
    "C_907V_Cregen": dict(vbat=907., tQ=[0, 1], QQ=[10000., 10000.], tP=[0, T0, T0 + 1e-9, 1], PP=[5000., 5000., -3000., -3000.],
                          band=(S.VO_CV[0], S.VO_CV[1])),
}


def bus_args(vbat):
    """run_avg의 bus 인자: [V_s, R_A, C_A, R_w, L_w, C_b, R_d, C_d, v_min]."""
    return [vbat / 2., RA, CA, RW, LW, CB, RD, CD, VMIN_Q]


def design():
    """E22의 선택 설계(zvs·both 반영)와 평균 등가·게인."""
    c = S.selected(); eq = S.dcx_equiv(c); g = S.gains(c, eq)
    return c, eq, g


def run_case(name, c=None, eq=None, g=None, dec=20):
    if c is None:
        c, eq, g = design()
    cs = CASES[name]
    return S.run_avg(c, eq, g, cs["tP"], cs["PP"], [0, 1], [400., 400.], T_end=T_END, dec=dec,
                     bus=bus_args(cs["vbat"]), tQ=cs["tQ"], QQ=cs["QQ"])


def avg5(Z, col, Ts=5e-6):
    """열 col의 Ts 주기 평균(회로 판정과 같은 5 µs)."""
    dtz = Z[1, 0] - Z[0, 0]; w = max(1, int(round(Ts / dtz)))
    m = Z.shape[0] // w
    return Z[:m * w, 0].reshape(m, w)[:, -1], Z[:m * w, col].reshape(m, w).mean(axis=1)


def stage_a_ref(vbat, iout, N=2):
    """E1 영교차 추종 2위상(1모듈): V_A 노드 400 µF에 일정 전류 iout을 끄는 정상상태(마지막 10주기). TB06과 같은 계산.
    N = 1이면 위상 하나만 운전(경부하 위상 셰딩, degrade의 비교용)."""
    import model_stage_a as A
    r = A.sim_array(N=N, Vbat=vbat, Iload=iout, Cbus=CA, mode="zcp", ncyc=80)
    ph, bus = A.analyze(r, ncyc_last=10)
    return dict(iout=float(iout), vA_mean=bus["Vbus"], vA_ripple=bus["ripple"],
                zcs=[float(p["zcs"]) for p in ph], Ipk=[float(p["Ipk"]) for p in ph], Iavg=[float(p["Iavg"]) for p in ph],
                fs=[float(p["fs"]) for p in ph], vA_ideal=vbat / 2)


def evaluate(name, Z):
    """판정 (a)–(d)와 TB16 대조용 지표."""
    cs = CASES[name]
    m = S.metrics(Z, T0 - 0.2e-3)
    tb, vb = avg5(Z, 1)
    q = tb >= T0 - 0.2e-3
    pre = (Z[:, 0] > T0 - 0.2e-3) & (Z[:, 0] <= T0); fin = Z[:, 0] > T_END - 0.2e-3
    vb_pre, vb_fin = float(Z[pre, 1].mean()), float(Z[fin, 1].mean())
    lo, hi = min(vb_pre, vb_fin) * 0.97, max(vb_pre, vb_fin) * 1.03
    osc = float(vb[tb > T_END - 0.5e-3].max() - vb[tb > T_END - 0.5e-3].min())
    iA_pre, iA_fin = float(Z[pre, 13].mean()), float(Z[fin, 13].mean())
    L = dict(voltage=bool(m["vo_min"] >= cs["band"][0] and m["vo_max"] <= cs["band"][1]),
             bus_band=bool(vb[q].min() >= lo and vb[q].max() <= hi),
             bus_settle=bool(osc <= 0.5),
             current_avg100=bool(m["ix_avg100_max"] <= S.I_LIM * 1.05),
             device_pulse=bool(m["ix_dev_peak"] <= S.ID_PULSE_S))
    return dict(case=name, vbat=cs["vbat"], limits=L, passed=all(L.values()), vo_min=m["vo_min"], vo_max=m["vo_max"],
                vo_end=float(Z[fin, 5].mean()), band=list(cs["band"]), bus_min=float(vb[q].min()), bus_max=float(vb[q].max()),
                bus_pre=vb_pre, bus_end=vb_fin, bus_band=[lo, hi], bus_osc_end=osc, vA_pre=float(Z[pre, 12].mean()),
                vA_end=float(Z[fin, 12].mean()), iA_pre=iA_pre, iA_end=iA_fin, iL_end=float(Z[fin, 2].mean()),
                ix_avg100_max=m["ix_avg100_max"], ix_dev_peak=m["ix_dev_peak"], flips=m["flips"], sat_ms=m["sat_ms"],
                both_frac_end=float(np.mean(Z[fin, 7] == 2)))


def base():
    c, eq, g = design()
    print("  Stage C 설계: L_m %.1f µH, 두 브리지 구동 < %.0f W(나감 %.0f W) / 버스: R_A %.1f mΩ, C_A %.0f µF, 배선 %.0f mΩ·%.1f µH, "
          "C_b %.0f µF, 감쇠기 %.1f mΩ + %.1f mF" % (c["Lm"] * 1e6, c["P_in"], c["P_out"], RA * 1e3, CA * 1e6, RW * 1e3, LW * 1e6,
                                                    CB * 1e6, RD * 1e3, CD * 1e3))
    out = {}
    for name in CASES:
        Z = run_case(name, c, eq, g)
        e = evaluate(name, Z)
        e["stageA"] = dict(pre=stage_a_ref(e["vbat"], e["iA_pre"]), final=stage_a_ref(e["vbat"], e["iA_end"]))
        out[name] = e
        sa = e["stageA"]
        print("  %-14s v_o %.2f–%.2f V(끝 %.3f), 버스 %.2f–%.2f V(사건 전 %.2f, 끝 %.2f, 끝 진동 %.3f V), Stage A %.1f → %.1f A"
              % (name, e["vo_min"], e["vo_max"], e["vo_end"], e["bus_min"], e["bus_max"], e["bus_pre"], e["bus_end"], e["bus_osc_end"],
                 e["iA_pre"], e["iA_end"]))
        print("      E1 Stage A: V_A %.3f / %.3f V, ZCS %.2f·%.2f %% / %.2f·%.2f %%, 판정 %s"
              % (sa["pre"]["vA_mean"], sa["final"]["vA_mean"], 100 * sa["pre"]["zcs"][0], 100 * sa["pre"]["zcs"][1],
                 100 * sa["final"]["zcs"][0], 100 * sa["final"]["zcs"][1], "통과" if e["passed"] else "불통과 " + str(
                     [k for k, v in e["limits"].items() if not v])))
    verdict("(base) 3사례 평균모델: 48 V·버스 범위·버스 정착·Stage C 전류", all(e["passed"] for e in out.values()),
            ", ".join("%s %.2f–%.2f V" % (k[:1], e["vo_min"], e["vo_max"]) for k, e in out.items()))
    zmax = max(max(e["stageA"]["pre"]["zcs"] + e["stageA"]["final"]["zcs"]) for e in out.values())
    verdict("(base) E1 Stage A ZCS ≤ 5 %(사건 전·끝 평균 전류)", zmax <= 0.05, "최대 %.2f %%" % (100 * zmax))
    save_json(EID, "base", dict(cases=out, bus=dict(RA=RA, CA=CA, RW=RW, LW=LW, CB=CB, RD=RD, CD=CD, VMIN_Q=VMIN_Q),
                                T0=T0, T_END=T_END))


def zbus_ca(f, RA_=RA):
    """C_A·R_A를 넣은 버스 임피던스: [V_s(이상) + R_A] ∥ C_A → 배선 R_w + L_w → C_b ∥ 감쇠기."""
    w = 2j * math.pi * f
    ZA = 1 / (1 / RA_ + w * CA)
    Zs = ZA + RW + w * LW
    return 1 / (1 / Zs + w * CB + 1 / (RD + 1 / (w * CD)))


def zbus():
    Q = json.loads((S.outdir(S.EID) / "control.json").read_text(encoding="utf-8"))
    rows = []
    for r in Q["tests"]["T7"]:
        zin = r["Zin_abs"] * np.exp(1j * math.radians(r["Zin_deg"]))
        zb = zbus_ca(r["f"]); zb0 = S.zbus(r["f"])
        rows.append(dict(Vbus=r["Vbus"], f=r["f"], Zin_abs=r["Zin_abs"], Zbus_ca=abs(zb), Zbus_E22=abs(zb0),
                         margin_db=20 * math.log10(abs(zin) / abs(zb)), margin_E22_db=r["margin_db"]))
    mm = min(x["margin_db"] for x in rows)
    for x in rows:
        if x["f"] in (10., 1000., 3000., 10000., 20000.):
            print("  %3.0f V %6.0f Hz: |Z_in| %.3f Ω, |Z_bus| C_A 포함 %.4f Ω(E22 %.4f Ω), 여유 %.1f dB(E22 %.1f dB)"
                  % (x["Vbus"], x["f"], x["Zin_abs"], x["Zbus_ca"], x["Zbus_E22"], x["margin_db"], x["margin_E22_db"]))
    verdict("(zbus) |Z_bus| ≤ |Z_in|/2(C_A·R_A 포함, 10 Hz–20 kHz, 5 kW)", mm >= 6., "최소 여유 %.1f dB" % mm)
    save_json(EID, "zbus", dict(rows=rows, min_margin_db=mm))


def figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    B = json.loads((outdir(EID) / "base.json").read_text(encoding="utf-8"))
    Zb = json.loads((outdir(EID) / "zbus.json").read_text(encoding="utf-8"))
    c, eq, g = design()
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    cols = {"A_540V_Cstep": C["red"], "B_806V_Qstep": C["blue"], "C_907V_Cregen": C["green"]}
    for name, col in cols.items():
        Z = run_case(name, c, eq, g)
        t = (Z[:, 0] - T0) * 1e3
        ax[0, 0].plot(t, Z[:, 5], color=col, lw=1, label=name)
        tb, vb = avg5(Z, 1)
        e = B["cases"][name]
        ax[0, 1].plot((tb - T0) * 1e3, vb - e["bus_pre"], color=col, lw=1, label="%s(사건 전 %.1f V)" % (name, e["bus_pre"]))
        ax[1, 0].plot(t, Z[:, 13], color=col, lw=1, label=name)
    ax[0, 0].axhspan(S.VO_NOM * 0.98, S.VO_NOM * 1.02, color=C["green"], alpha=0.08)
    ax[0, 0].set_xlim(-0.2, 3); ax[0, 0].set_xlabel("사건 뒤 시간 [ms]"); ax[0, 0].set_ylabel("48 V 출력 [V]")
    ax[0, 0].set_title("(a) 48 V(평균모델, 버스 회로 포함)", fontsize=9); ax[0, 0].legend(fontsize=7)
    ax[0, 1].set_xlim(-0.2, 3); ax[0, 1].set_xlabel("사건 뒤 시간 [ms]"); ax[0, 1].set_ylabel("버스 − 사건 전 [V](5 µs 평균)")
    ax[0, 1].set_title("(b) 400 V 버스(= V_A − 배선 강하)", fontsize=9); ax[0, 1].legend(fontsize=7)
    ax[1, 0].set_xlim(-0.2, 3); ax[1, 0].set_xlabel("사건 뒤 시간 [ms]"); ax[1, 0].set_ylabel("Stage A 출력전류 [A](정적 등가)")
    ax[1, 0].set_title("(c) Stage A 출력전류", fontsize=9); ax[1, 0].legend(fontsize=7)
    a = ax[1, 1]
    for V, col in ((270., C["red"]), (504., C["green"])):
        rr = [r for r in Zb["rows"] if r["Vbus"] == V]
        a.loglog([r["f"] for r in rr], [r["Zin_abs"] for r in rr], "-o", ms=3, color=col, label="|Z_in| Stage C 5 kW, %.0f V" % V)
    rr = [r for r in Zb["rows"] if r["Vbus"] == 270.]
    a.loglog([r["f"] for r in rr], [r["Zbus_ca"] for r in rr], "k-", label="|Z_bus| C_A·R_A 포함")
    a.loglog([r["f"] for r in rr], [r["Zbus_E22"] for r in rr], "k:", label="|Z_bus| E22(C_A 없음)")
    a.set_xlabel("주파수 [Hz]"); a.set_ylabel("[Ω]"); a.set_title("(d) Middlebrook: 최소 여유 %.1f dB" % Zb["min_margin_db"], fontsize=9)
    a.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(outdir(EID) / "E23_r2_integrated.png", dpi=150); plt.close(fig)
    if (outdir(EID) / "degrade.json").exists():         # R2-W460 강등 중 48 V
        fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
        for (name, cs), col in zip(DEG_CASES.items(), (C["red"], C["blue"])):
            job, m, tr, Z, p48 = degrade_case(name, c, eq, g)
            ax[0].plot(tr["t"] * 1e3, tr["log"][:, 2], color=col, lw=1, label="%s 버스(E17)" % name)
            ax[1].plot(Z[:, 0] * 1e3, Z[:, 5], color=col, lw=1, label="%s 48 V(E22, 부하 %.0f W)" % (name, p48))
        ax[0].axhline(470, color="k", ls=":", lw=0.8)
        ax[0].set_ylabel("400 V 버스 [V]"); ax[0].legend(fontsize=7)
        ax[0].set_title("(a) H-브리지 개방 강등(고장 %.1f ms): 창 460 V → 클램프 → 부하 분리·링크 붕괴 → 소프트 바이패스 → V_A" % (T_EV_DEG * 1e3),
                        fontsize=9)
        ax[1].axhspan(S.VO_NOM * 0.98, S.VO_NOM * 1.02, color=C["green"], alpha=0.08)
        ax[1].set_ylabel("48 V 출력 [V]"); ax[1].set_xlabel("시간 [ms]"); ax[1].legend(fontsize=7)
        ax[1].set_title("(b) 조정형 Stage C 48 V(입력 5 kW, 녹색 띠 ±2 %)", fontsize=9)
        fig.tight_layout(); fig.savefig(outdir(EID) / "E23_degrade.png", dpi=150); plt.close(fig)
    print("  figures saved")


# ---------------------------------------------------------------------------------------------
# degrade: R2-W460 창 조정 모듈의 H-브리지 개방 강등 중 48 V(회로 TB17의 기준값)
# ---------------------------------------------------------------------------------------------
T_EV_DEG = 1.5e-3      # 고장 시각. Stage A 회로가 정착(TB16에서 약 0.3 ms)하고 사건 전 구간(1.3–1.5 ms)을 두도록 E17 기본 0.5 ms보다 1 ms 늦춤
PC_IN = 5000.          # Stage C 입력 전력 = E17 P_C(400 V 부하 분리 뒤 남는 부하)
PKD = round(1.5 / (1.03 * 1.05), 3)   # 설계 상한 1.387 × 정격점(E21 P3t, TB13과 같음)
DEG_CASES = {           # TB13과 같은 고장·강등 방식(E21 P3t), 고장 시각만 T_EV_DEG
    "A_1008V_hbopen": dict(V=1008., P=25000.),
    "B_930V_hbopen": dict(V=930., P=25000.),
}


def p48_for_input(c, eq, pin=PC_IN):
    """평균모델 정상상태에서 Stage C 입력 전력이 pin이 되는 48 V 부하 전력.
    입력 = (v_I + R_L·i_L)·i_L, v_I = n(V_o + R_x·i_x), i_L = i_x/n → pin = V_o·i_x + (R_x + R_L/n²)·i_x²."""
    n = c["n"]
    RL = S.K["mag_ind_cu"] * S.PO_MAX / (S.PO_MAX * 1.03 / (n * S.VO_NOM)) ** 2
    a = eq["Rx"] + RL / n ** 2
    ix = (-S.VO_NOM + math.sqrt(S.VO_NOM ** 2 + 4 * a * pin)) / (2 * a)
    return S.VO_NOM * ix


def degrade_job(V, P):
    import E17_protection_integration as E17
    return dict(case="W460_240s", keep=True, V=V, P=P, event="hb_open", policy="clamp_brk", t_shed=3e-3,
                duration=T_EV_DEG + 16.5e-3, hold="match", dmod="eps", soft_fail=True, curtail=True, pk_table="sw", pk_fault=PKD)


def degrade_case(name, c=None, eq=None, g=None):
    """E17 보호 상태기계(고장 시각 T_EV_DEG)로 버스 궤적을 구하고, 그 버스를 E22 평균모델(이상 버스 전원 = E17 버스)에 넣는다.
    반환: (job, E17 지표, E17 궤적, Stage C 평균모델 Z, P48)"""
    import E17_protection_integration as E17
    if c is None:
        c, eq, g = design()
    cs = DEG_CASES[name]
    job = degrade_job(cs["V"], cs["P"])
    t_ev0 = E17.T_EV
    E17.T_EV = T_EV_DEG                         # r2_run은 모듈 전역 T_EV를 실행 중에 읽는다(파이썬 루프)
    try:
        m = E17.r2_run(dict(job))
    finally:
        E17.T_EV = t_ev0
    tr = m.pop("trace")
    t, L = tr["t"], tr["log"]                   # 1 µs, [ip vs vbus ih vlink idab ibyp loads400 bridge Pbrk]
    w = 5                                       # 5 µs 평균 버스(회로 판정 주기)
    nn = (t.size // w) * w
    tV = np.concatenate(([0.], t[:nn].reshape(-1, w)[:, -1]))
    VV = np.concatenate(([L[0, 2]], L[:nn, 2].reshape(-1, w).mean(axis=1)))
    p48 = p48_for_input(c, eq)
    Z = S.run_avg(c, eq, g, [0., 1.], [p48, p48], tV, VV, T_end=job["duration"], dec=20, start_eq=True)
    return job, m, tr, Z, p48


def degrade():
    c, eq, g = design()
    out = {}
    for name, cs in DEG_CASES.items():
        job, m, tr, Z, p48 = degrade_case(name, c, eq, g)
        t, L = tr["t"], tr["log"]
        mm = S.metrics(Z, T_EV_DEG - 0.2e-3)
        q = Z[:, 0] >= T_EV_DEG - 0.2e-3
        pin = Z[q, 9] * Z[q, 1]
        band = (S.VO_NOM * (1 - S.VO_TOL), S.VO_NOM * (1 + S.VO_TOL))
        pre = (t > T_EV_DEG - 0.2e-3) & (t <= T_EV_DEG); fin = t > t[-1] - 0.2e-3
        ip_pre, ip_end = float(L[pre, 0].mean()), float(L[fin, 0].mean())
        Lm = dict(voltage=bool(mm["vo_min"] >= band[0] and mm["vo_max"] <= band[1]),
                  current_avg100=bool(mm["ix_avg100_max"] <= S.I_LIM * 1.05),
                  device_pulse=bool(mm["ix_dev_peak"] <= S.ID_PULSE_S),
                  e17_pass=bool(m["pass_"]))
        e = dict(case=name, vbat=cs["V"], P0=cs["P"], p48=p48, limits=Lm, passed=all(Lm.values()), band=list(band),
                 vo_min=mm["vo_min"], vo_max=mm["vo_max"], vo_end=float(Z[-1, 5]), dev_pct=mm["dev_pct"],
                 ix_avg100_max=mm["ix_avg100_max"], ix_dev_peak=mm["ix_dev_peak"], d_max=float(Z[q, 6].max()),
                 d_min=float(Z[q, 6].min()), pin_min=float(pin.min()), pin_max=float(pin.max()),
                 bus_min=float(L[t >= T_EV_DEG, 2].min()), bus_max=float(L[t >= T_EV_DEG, 2].max()), bus_end=float(L[fin, 2].mean()),
                 dvdt_max_V_per_ms=float(np.abs(np.diff(L[:, 2]) / np.diff(t)).max() * 1e-3),
                 ip_pre=ip_pre, ip_end=ip_end, events=m["events"], final_state=m["final_state"],
                 e17=dict(checks=m["checks"], path_peak=m["path_peak"], vbus_min=m["vbus_min"], vbus_max=m["vbus_max"],
                          dab_sec_peak=m.get("dab_sec_peak"), soft_energy_J=m.get("soft_energy_J"), brk_energy_J=m["brk_energy_J"]),
                 stageA=dict(pre=stage_a_ref(cs["V"], ip_pre), final=stage_a_ref(cs["V"], ip_end),
                             final_1ph=stage_a_ref(cs["V"], ip_end, N=1)))
        out[name] = e
        sa = e["stageA"]
        print("  %-15s P48 %.0f W(입력 %.0f–%.0f W), 버스 %.1f–%.1f V(끝 %.1f, 최대 %.0f V/ms), v_o %.3f–%.3f V(%.2f %%), 최종 %s"
              % (name, p48, e["pin_min"], e["pin_max"], e["bus_min"], e["bus_max"], e["bus_end"], e["dvdt_max_V_per_ms"],
                 e["vo_min"], e["vo_max"], e["dev_pct"], e["final_state"]))
        print("      E1 Stage A: 사건 전 %.1f A ZCS %.2f·%.2f %%, 끝 %.1f A ZCS %.2f·%.2f %%(위상 하나만 운전하면 %.2f %%), V_A %.2f / %.2f V"
              % (ip_pre, 100 * sa["pre"]["zcs"][0], 100 * sa["pre"]["zcs"][1], ip_end, 100 * sa["final"]["zcs"][0],
                 100 * sa["final"]["zcs"][1], 100 * sa["final_1ph"]["zcs"][0], sa["pre"]["vA_mean"], sa["final"]["vA_mean"]))
    verdict("(degrade) R2-W460 H-브리지 개방 강등 중 48 V ±2 %·Stage C 전류(E17 버스 궤적, 2사례)",
            all(e["passed"] for e in out.values()),
            ", ".join("%s %.2f–%.2f V" % (k[:1], e["vo_min"], e["vo_max"]) for k, e in out.items()))
    za = {k: max(e["stageA"]["pre"]["zcs"] + e["stageA"]["final"]["zcs"]) for k, e in out.items()}
    verdict("(degrade) E1 Stage A ZCS ≤ 5 %(2위상, 사건 전·끝 평균 전류)", max(za.values()) <= 0.05,
            ", ".join("%s 최대 %.2f %%" % (k[:1], 100 * v) for k, v in za.items())
            + " — 강등 뒤 Stage C만 남는 경부하(1008 V, 약 10 A)에서는 검출 문턱·지연에 비해 공진전류 첨두가 작다. 위상 하나만 운전하면 "
            + ", ".join("%s %.2f %%" % (k[:1], 100 * e["stageA"]["final_1ph"]["zcs"][0]) for k, e in out.items()))
    save_json(EID, "degrade", dict(cases=out, T_EV=T_EV_DEG, PC_IN=PC_IN, PKD=PKD))


PARTS = dict(base=base, zbus=zbus, degrade=degrade, figures=figures)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E23 %s ====" % w)
        PARTS[w]()
