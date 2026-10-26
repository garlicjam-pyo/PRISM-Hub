"""[E25] 모터·인버터 승압 충전과 800 V 보조부품 구조를 더한 기준 구조 비교.

■ 목적
  E15·E18은 Stage A(2:1 공진 스위치드 커패시터) 기반 구조를 ① 전용 승압기(하드 스위칭 6상 부스트)와 비교했다.
  그러나 800 V급 차량이 400–500 V급 충전기를 쓰는 가장 흔한 산업 방식은 구동 모터 권선과 구동 인버터를 승압기로
  다시 쓰는 방식이다(현대차그룹 E-GMP, 루시드 Gravity, docs/23 3.1절). 이 방식은 충전용 반도체를 더하지 않는다.
  또 800 V급 보조부품(컴프레서·히터)이 양산되면서 400 V 보조버스 자체를 두지 않는 설계도 주류가 되고 있다.
  이 두 구조와 비교하지 않으면 PRISM-Hub(R2)의 이점이 어느 조건에서 성립하는지 말할 수 없다.

■ 비교 구조(E15와 같은 소자·손실 규칙, 같은 부하·배터리 분포, 사양 팩 640–920 V)
  ①  전용 승압기(충전) + 800 → 400 V 보조 강압기 + 고정이득 Stage C          (E15 그대로)
  ⑤  모터·인버터 승압(충전) + 800 → 400 V 보조 강압기 + 고정이득 Stage C       (보조 경로 = ①, 충전 경로만 다름)
  ④  R2 기본형: Stage A + 버스 RC 감쇠기 + 조정형 Stage C                    (E15 그대로, 400 V 부품 B_470)
  ⑥  모터·인버터 승압(충전) + 800 V급 보조부품(배터리 직결) + 48 V: 입력 직렬·출력 병렬 조정형 Stage C 2개
      (각 V_bat/2 입력, ④의 Stage C와 같은 모델). 400 V 보조부품을 쓰지 않으므로 서비스(부품 등급)가 다르다.

■ 모터·인버터 승압 충전 모델(이 스크립트에서 새로 계산)
  - 충전기(V_bat/2, 375 A, Stage A와 같은 조건)를 모터 중성점에 연결하고, 구동 인버터 세 레그를 120° 엇갈린
    동기 부스트로 운전해 V_bat로 승압한다. 상전류 = 375/3 A, 듀티 D = 1 − V_in/V_bat.
  - 세 상 전류가 같아 회전 자계가 생기지 않으므로, 상마다 보이는 인덕턴스는 영상(누설) 인덕턴스 L_0다.
    상전류 리플 ΔI = V_in·D/(L_0·f).
  - 인버터: 1200 V SiC(E15와 같은 C3M0016120K 규칙), 스위치 위치마다 n개 병렬(구동 정격이 정한다).
    도통 I_rms²·R_on/n, 하드 스위칭 E_on + E_off(esw_hard), 데드타임 역도통, 게이트.
  - 모터 권선: 직류 I²·R_ph + 리플 성분 (ΔI²/12)·R_ph·k_ac. 리플에 의한 철손·자석 와전류 손실은 넣지 않는다
    (→ 이 모델의 모터 승압 손실은 하한 쪽이다. Stage A와의 비교는 모터 승압 쪽에 유리하게 잡은 것이다).
  - 계수 범위(가정): R_ph 0(권선 손실 없는 하한)·5·10·15 mΩ, L_0 50·100·200·400 µH, f 10·20 kHz, n 4·5·6, k_ac 3.
    공개된 양산 차량의 모터 영상 인덕턴스·상저항 값은 찾지 못했다. 그래서 범위 전체를 보고하고, 결론은 그 범위에서
    바뀌지 않는 것만 쓴다.

■ 판정(시험 전에 정한 질문)
  Q1 충전 손실: Stage A(0.50 kW)가 모터 승압 손실 범위의 하한보다 작은가, 범위 안인가.
  Q2 보조 경로 손실: ④ 대 ⑤(같은 400 V 부품), ④ 대 ⑥(800 V 부품).
  Q3 추가 반도체: 충전 기능을 위해 더하는 스위치 위치 수(⑤·⑥은 0).
  Q4 연간 손실 에너지 예시: 주행 1,000시간 + 400–500 V급 충전 1,000 kWh당(가정한 사용 비율, 결론 대신 크기 감각용).
  Q5 Stage A 손실 모델 감도: E15는 Stage A 손실을 E1 모델(스위치·ESR·인덕터 권선·배선 도통, 다이오드, 출력용량, 게이트)로
     계산했고, 다른 변환기처럼 자성체 철손 항(정격의 0.1 %)은 두지 않았다(공진 인덕터 144 nH를 공심으로 가정).
     (a) 수동소자 저항(ESR·인덕터·배선)을 2배(150 kHz 교류저항)로 두고 E1 격자를 다시 계산,
     (b) 동작 위상마다 고정 손실 ΔP를 더해(철심 인덕터·기판 손실 등) ④가 ⑤·⑥과 같아지는 ΔP를 구한다.

■ 실행   python E25_motor_boost_comparison.py   (E15 결과 results/E15/stage_a_grid.json·comparison.json 필요, 수 초)
■ 결과   results/E25/comparison.json, E25_motor_boost.png
"""
import itertools
import math

import numpy as np

import E15_baseline_loss_rating as E15
from common import load_json, outdir, save_json

EID = "E25"
I_CH = 375.                       # 충전전류 [A](Stage A 8위상 정격과 같음)
V_EVAL = (640., 800., 920.)       # 충전 손실을 볼 배터리 전압
GRID = dict(Rph=[0.0, 0.005, 0.010, 0.015], L0=[50e-6, 100e-6, 200e-6, 400e-6], f=[10e3, 20e3], n=[4, 5, 6])
BASE = dict(Rph=0.010, L0=100e-6, f=10e3, n=5)   # 대표값(그림·표의 기준점)
K_AC = 3.0                        # 리플 주파수 권선 교류저항 배율(가정)
DRIVE_H = 1000.                   # Q4: 주행 시간 [h]
CHARGE_KWH = 1000.                # Q4: 400–500 V급 충전기로 충전한 에너지 [kWh]


def motor_boost_loss(Vbat, I=I_CH, Rph=BASE["Rph"], L0=BASE["L0"], f=BASE["f"], n=BASE["n"]):
    """모터·인버터 승압 충전 손실 [W]과 내역. 충전기 전압 = V_bat/2(Stage A와 같은 400 V급 충전기 조건)."""
    d = E15.DEV["SiC1200"]
    Vin = Vbat / 2
    D = 1 - Vin / Vbat
    Iph = I / 3
    dI = Vin * D / (L0 * f)                               # 상전류 리플(첨두-첨두)
    Irms2 = Iph ** 2 + dI ** 2 / 12
    p_cond = 3 * Irms2 * d["Ron"] / n                     # 동기 정류: 한 주기 내내 위·아래 스위치 중 하나가 도통
    ion = Iph - dI / 2                                    # 아래 스위치 켜짐 순간 전류
    ioff = Iph + dI / 2                                   # 아래 스위치 꺼짐 순간 전류
    # 스위칭 에너지: E15 esw_hard와 같은 분해(출력용량분 + 전압·전류 비례분)를 켜짐·꺼짐으로 나눈다.
    # 데이터시트 비 E_on : E_off = 2552 : 788 µJ(800 V·80 A). 켜짐 순간 전류가 음이면(리플이 0을 지남) 영전압 켜짐이라
    # 출력용량분과 켜짐 손실이 없다(모터 승압 쪽에 유리한 근사).
    eoss = d["Eoss"] * (Vbat / d["Voss"]) ** 1.5
    eoss_ref = d["Eoss"] * (d["Vref"] / d["Voss"]) ** 1.5
    kvi = (d["Eref"] - eoss_ref) * (Vbat / d["Vref"]) / d["Iref"]
    fon, foff = 2552. / 3340., 788. / 3340.
    if ion >= 0:
        e = E15.K["esw"] * (n * eoss + kvi * (fon * ion + foff * ioff))
    else:
        e = E15.K["esw"] * kvi * foff * ioff
    p_sw = 3 * f * e
    p_dead = 3 * 2 * d["td"] * f * Iph * d["Vsd"]
    p_gate = 3 * 2 * n * d["Qg"] * d["Vg"] * f
    p_wind = 3 * (Iph ** 2 * Rph + dI ** 2 / 12 * Rph * K_AC)
    tot = p_cond + p_sw + p_dead + p_gate + p_wind + E15.K["ctrl"]
    return dict(total=tot, inverter=p_cond + p_sw + p_dead + p_gate, winding=p_wind, ripple_pp=dI, Iph=Iph,
                parts=dict(cond=p_cond, sw=p_sw, dead=p_dead, gate=p_gate, winding=p_wind, ctrl=E15.K["ctrl"]))


def motor_boost_range(Vbat):
    vals = []
    for Rph, L0, f, n in itertools.product(GRID["Rph"], GRID["L0"], GRID["f"], GRID["n"]):
        r = motor_boost_loss(Vbat, Rph=Rph, L0=L0, f=f, n=n)
        vals.append(dict(Rph=Rph, L0=L0, f=f, n=n, total=r["total"], inverter=r["inverter"], winding=r["winding"],
                         ripple_pp=r["ripple_pp"]))
    t = np.array([v["total"] for v in vals])
    lo = vals[int(np.argmin(t))]; hi = vals[int(np.argmax(t))]
    # 권선 손실 0을 뺀 범위(현실적인 하한: R_ph ≥ 5 mΩ)
    t5 = np.array([v["total"] for v in vals if v["Rph"] >= 0.005])
    return dict(min=float(t.min()), max=float(t.max()), min_Rph5=float(t5.min()), median=float(np.median(t)),
                argmin=lo, argmax=hi, n_cases=len(vals))


def path6(SAm, V, P400, P48):
    """⑥: 400 V 보조부하는 800 V급 부품으로 배터리에 직결(변환 손실 0). 48 V는 입력 직렬·출력 병렬 조정형 Stage C 2개."""
    pin, lc = E15.stage_c(V / 2, P48 / 2, True)
    return dict(loss=2 * lc, parts=dict(stageC_x2=2 * lc))


def aux_avg(fn, prof="drive_typ"):
    pr = E15.PROFILES[prof]
    L = np.array([[fn(V, P) for P in E15.P400] for V in pr["V"]])
    return float(np.mean(L @ E15.W400)), (L.mean(0)).tolist()


def stage_a_sensitivity(SAm, aux, ch800):
    """Q5: Stage A 손실 모델의 두 가지 불확도가 ④의 보조·충전 손실에 주는 영향."""
    import os
    import model_stage_a as SA
    from common import RESULTS
    cache = RESULTS / EID / "stage_a_grid_Rpass_x2.json"
    if cache.exists() and os.environ.get("E25_RECOMPUTE") != "1":
        g = load_json(EID, "stage_a_grid_Rpass_x2")
        T2 = dict(P=np.array(g["P_phase"]), D=np.array(g["dvA"]), charge={float(k): v for k, v in g["charge"].items()})
    else:
        print("E25 Stage A 격자(수동소자 저항 2배) 계산 ...")
        keep = {k: SA.BASE[k] for k in ("ESR", "RL", "Rmisc")}
        try:
            for k in keep:
                SA.BASE[k] = 2 * keep[k]
            T2 = E15.stage_a_tables()
        finally:
            SA.BASE.update(keep)
        save_json(EID, "stage_a_grid_Rpass_x2", dict(V=E15.VGRID, I=E15.IGRID, P_phase=T2["P"], dvA=T2["D"],
                                                    charge={str(k): v for k, v in T2["charge"].items()}))
    SA2 = E15.StageA(T2)
    aux4_2, _ = aux_avg(lambda V, P: E15.path_struct("4", SA2, V, P, E15.P48)["loss"])
    ch2 = E15.charge_loss("4", SA2, 800.)
    d5 = aux["5"]["avg_W"] - aux["4"]["avg_W"]
    d6 = aux["6"]["avg_W"] - aux["4"]["avg_W"]
    fs = 1 / (2 * np.pi * np.sqrt(SA.BASE["Lr"] * SA.BASE["Cfly"]))
    fixed = 4 * SA.BASE["Eoss"] * fs + 4 * SA.BASE["Qg_E"] * fs
    return dict(Rpass_x2=dict(aux4_W=aux4_2, charge800_W=ch2),
                dP_eq5_W=d5 / 2, dP_eq6_W=d6 / 2,            # 주행 중 Stage A는 모듈 1(위상 2개)
                fixed_per_phase_W=fixed, core_rule_W=0.001 * 150e3 / 8,
                dP_charge_W_per_W=8.)                        # ΔP 1 W마다 충전 손실 8 W(8위상)


def stage_c_rating_x2():
    C = dict(positions=8, devices=4 + 4 * E15.npar("GaN150", 100.))
    Cpre = E15.hs_rating("fsbb", "GaN650", 1, 3300., 400.)
    return dict(positions=2 * (C["positions"] + Cpre["positions"]), devices=2 * (C["devices"] + Cpre["devices"]))


def main():
    g = load_json("E15", "stage_a_grid")
    T = dict(P=np.array(g["P_phase"]), D=np.array(g["dvA"]), charge={float(k): v for k, v in g["charge"].items()})
    SAm = E15.StageA(T)
    c15 = load_json("E15", "comparison")

    # ---- 충전 경로 손실 ---------------------------------------------------------------------------------------
    charge = {}
    for V in V_EVAL:
        mb = motor_boost_loss(V)
        charge[f"{V:.0f}V"] = dict(stageA=E15.charge_loss("4", SAm, V), booster=E15.charge_loss("1", SAm, V),
                                   motor_base=mb["total"], motor_base_parts=mb["parts"], motor_ripple_pp=mb["ripple_pp"],
                                   motor_range=motor_boost_range(V))
    # 감도: 기준점에서 한 변수씩
    sens = {}
    for key, vals in GRID.items():
        sens[key] = {str(v): motor_boost_loss(800., **{key: v})["total"] for v in vals}

    # ---- 보조 경로 손실(주행 대표 프로파일) --------------------------------------------------------------------
    aux = {}
    for s, fn in (("1", lambda V, P: E15.path_struct("1", SAm, V, P, E15.P48)["loss"]),
                  ("4", lambda V, P: E15.path_struct("4", SAm, V, P, E15.P48)["loss"]),
                  ("6", lambda V, P: path6(SAm, V, P, E15.P48)["loss"])):
        aux[s] = dict(zip(("avg_W", "by_load_W"), aux_avg(fn)))
    aux["5"] = dict(aux["1"])                                    # ⑤의 보조 경로는 ①과 같다
    reg = dict(aux_1=aux["1"]["avg_W"], E15_1=c15["results"]["1"]["drive_typ"]["avg_loss_W"],
               aux_4=aux["4"]["avg_W"], E15_4=c15["results"]["4"]["drive_typ"]["avg_loss_W"])

    # ---- 반도체(스위치 위치 수): 충전 기능과 보조 기능 ----------------------------------------------------------
    rat15 = c15["ratings"]
    sc2 = stage_c_rating_x2()
    semis = {
        "1": dict(charge=rat15["1"]["parts"]["booster"]["positions"],
                  aux=rat15["1"]["parts"]["aux_buck"]["positions"] + rat15["1"]["parts"]["stageC"]["positions"]),
        "5": dict(charge=0, aux=rat15["1"]["parts"]["aux_buck"]["positions"] + rat15["1"]["parts"]["stageC"]["positions"]),
        "4": dict(charge=rat15["4"]["parts"]["stageA"]["positions"],
                  aux=rat15["4"]["parts"]["stageC"]["positions"] + rat15["4"]["parts"]["stageC_pre"]["positions"]),
        "6": dict(charge=0, aux=sc2["positions"]),
    }
    for k in semis:
        semis[k]["total"] = semis[k]["charge"] + semis[k]["aux"]

    # ---- Q4 손실 에너지 예시 ---------------------------------------------------------------------------------
    ch800 = charge["800V"]
    E = {}
    for s, pch in (("1", ch800["booster"]), ("5", ch800["motor_base"]), ("4", ch800["stageA"]), ("6", ch800["motor_base"])):
        e_drive = aux[s]["avg_W"] * DRIVE_H / 1e3                     # kWh
        e_ch = pch / (800. / 2 * I_CH) * CHARGE_KWH                  # 충전 손실 비율 × 충전 에너지
        E[s] = dict(drive_kWh=e_drive, charge_kWh=e_ch, total_kWh=e_drive + e_ch)
    mr = ch800["motor_range"]
    E["5_range_charge_kWh"] = [mr["min_Rph5"] / (400. * I_CH) * CHARGE_KWH, mr["max"] / (400. * I_CH) * CHARGE_KWH]

    # ---- 손익분기 ----------------------------------------------------------------------------------------------
    # (1) 모터 승압이 Stage A와 같은 충전 손실이 되는 상저항: 권선 외 손실이 가장 작은 조합(L_0·f·n 격자 최소)에서
    from scipy.optimize import brentq
    best = min((dict(L0=L0, f=f, n=n) for L0, f, n in itertools.product(GRID["L0"], GRID["f"], GRID["n"])),
               key=lambda c: motor_boost_loss(800., Rph=0., **c)["total"])
    pA = ch800["stageA"]
    f0 = motor_boost_loss(800., Rph=0., **best)["total"]
    rph_be = brentq(lambda r: motor_boost_loss(800., Rph=r, **best)["total"] - pA, 0., 0.05) if f0 < pA else 0.
    rph_be_base = brentq(lambda r: motor_boost_loss(800., Rph=r)["total"] - pA, 0., 0.05) \
        if motor_boost_loss(800., Rph=0.)["total"] < pA else 0.
    # (2) ④(R2) 대 ⑥: 보조 손실 차(⑥이 작음)를 충전 손실 차(④가 작음)가 메우는 400–500 V급 충전 에너지 / 주행 시간
    d_aux = aux["4"]["avg_W"] - aux["6"]["avg_W"]                          # W
    d_ch_frac = (ch800["motor_base"] - pA) / (400. * I_CH)                   # 충전 에너지당 손실 비율 차(기준점)
    d_ch_frac_lo = (ch800["motor_range"]["min_Rph5"] - pA) / (400. * I_CH)   # R_ph ≥ 5 mΩ 하한
    be = dict(Rph_breakeven_best_mOhm=1e3 * rph_be, Rph_breakeven_base_mOhm=1e3 * rph_be_base, best_combo=best,
              aux_diff_4_minus_6_W=d_aux, charge_loss_frac_diff_base=d_ch_frac, charge_loss_frac_diff_lo=d_ch_frac_lo,
              kWh_per_drive_h_base=d_aux / 1e3 / d_ch_frac, kWh_per_drive_h_lo=d_aux / 1e3 / d_ch_frac_lo)

    # ---- Q5 Stage A 손실 모델 감도 ------------------------------------------------------------------------------
    sa = stage_a_sensitivity(SAm, aux, ch800)

    out = dict(charge=charge, sensitivity_800V=sens, aux=aux, regression=reg, semis=semis, energy_example=E, breakeven=be,
               stageA_sensitivity=sa,
               assumptions=dict(GRID=GRID, BASE=BASE, K_AC=K_AC, DRIVE_H=DRIVE_H, CHARGE_KWH=CHARGE_KWH,
                                note="모터 리플 철손·자석 와전류 손실 미포함(모터 승압 손실 하한 쪽)"))
    save_json(EID, "comparison", out)
    figure(out)

    # ---- 출력 ------------------------------------------------------------------------------------------------
    print("회귀: ① 보조 %.1f W(E15 %.1f), ④ %.1f W(E15 %.1f)" % (reg["aux_1"], reg["E15_1"], reg["aux_4"], reg["E15_4"]))
    for k, v in charge.items():
        r = v["motor_range"]
        print("충전 %s: Stage A %.0f W, 전용 승압기 %.0f W, 모터 승압 기준점 %.0f W(리플 %.0f A pp), 범위 %.0f–%.0f W "
              "(R_ph ≥ 5 mΩ 하한 %.0f W)" % (k, v["stageA"], v["booster"], v["motor_base"], v["motor_ripple_pp"],
                                             r["min"], r["max"], r["min_Rph5"]))
    print("모터 승압 800 V 내역(기준점):", {k: round(x) for k, x in charge["800V"]["motor_base_parts"].items()})
    print("감도(800 V):", {k: {kk: round(vv) for kk, vv in v.items()} for k, v in sens.items()})
    for s in ("1", "5", "4", "6"):
        print("구조 %s: 보조 평균 %.1f W, 스위치 위치 충전 %d + 보조 %d = %d, 예시 손실 %.1f kWh(주행 %.1f + 충전 %.1f)" % (
            s, aux[s]["avg_W"], semis[s]["charge"], semis[s]["aux"], semis[s]["total"], E[s]["total_kWh"], E[s]["drive_kWh"],
            E[s]["charge_kWh"]))
    print("⑤ 충전 손실 에너지 범위(R_ph ≥ 5 mΩ): %.2f–%.2f kWh / %d kWh" % (*E["5_range_charge_kWh"], CHARGE_KWH))
    print("손익분기: 모터 승압 = Stage A 충전 손실이 되는 상저항 %.2f mΩ(가장 유리한 L_0·f·n), %.2f mΩ(기준점)" % (
        be["Rph_breakeven_best_mOhm"], be["Rph_breakeven_base_mOhm"]))
    print("Stage A 감도: 수동소자 저항 2배 → ④ 보조 %.1f W(+%.1f), 충전 %.0f W(+%.0f)" % (
        sa["Rpass_x2"]["aux4_W"], sa["Rpass_x2"]["aux4_W"] - aux["4"]["avg_W"], sa["Rpass_x2"]["charge800_W"],
        sa["Rpass_x2"]["charge800_W"] - ch800["stageA"]))
    print("Stage A 감도: 위상당 고정 손실 ΔP가 %.1f W면 ④ = ⑤(보조), %.1f W면 ④ = ⑥(보조). 현재 모델의 위상당 고정 손실 %.1f W, "
          "철심 인덕터 규칙(정격 0.1 %%) %.1f W" % (sa["dP_eq5_W"], sa["dP_eq6_W"], sa["fixed_per_phase_W"], sa["core_rule_W"]))
    print("손익분기: ④가 ⑥과 같은 총손실이 되는 400–500 V급 충전 에너지 = 주행 1시간당 %.2f kWh(모터 승압 기준점), "
          "%.2f kWh(R_ph ≥ 5 mΩ 하한)" % (be["kWh_per_drive_h_base"], be["kWh_per_drive_h_lo"]))


def figure(out):
    from plotstyle import korean, COLOR as C
    plt = korean()
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.8))
    # (a) 충전 손실
    Vs = [640., 800., 920.]
    xs = np.arange(len(Vs))
    ch = out["charge"]
    ax[0].bar(xs - 0.27, [ch[f"{V:.0f}V"]["booster"] / 1e3 for V in Vs], 0.27, color=C["gray"], label="① 전용 승압기")
    mb = [ch[f"{V:.0f}V"]["motor_base"] / 1e3 for V in Vs]
    lo = [ch[f"{V:.0f}V"]["motor_range"]["min_Rph5"] / 1e3 for V in Vs]
    hi = [ch[f"{V:.0f}V"]["motor_range"]["max"] / 1e3 for V in Vs]
    ax[0].bar(xs, mb, 0.27, color=C["green"], label="⑤·⑥ 모터 승압(기준점)",
              yerr=[np.subtract(mb, lo), np.subtract(hi, mb)], capsize=3, ecolor="k")
    ax[0].bar(xs + 0.27, [ch[f"{V:.0f}V"]["stageA"] / 1e3 for V in Vs], 0.27, color=C["orange"], label="④ Stage A")
    ax[0].set_xticks(xs, ["%.0f V" % V for V in Vs]); ax[0].set_ylabel("충전 경로 손실 [kW]")
    ax[0].set_title("(a) 충전 375 A(충전기 V_bat/2)\n오차막대: 모터 승압 범위(R_ph ≥ 5 mΩ)"); ax[0].legend(fontsize=7)
    # (b) 감도
    s = out["sensitivity_800V"]
    names = {"Rph": "R_ph [mΩ]", "L0": "L_0 [µH]", "f": "f [kHz]", "n": "병렬 n"}
    scale = {"Rph": 1e3, "L0": 1e6, "f": 1e-3, "n": 1}
    for k, mk in zip(s, "osd^"):
        xv = [float(x) * scale[k] for x in s[k]]
        ax[1].plot(range(len(xv)), [v / 1e3 for v in s[k].values()], marker=mk, label=names[k])
        for i, xx in enumerate(xv):
            ax[1].annotate("%g" % xx, (i, list(s[k].values())[i] / 1e3), fontsize=6, xytext=(2, 2), textcoords="offset points")
    ax[1].axhline(ch["800V"]["stageA"] / 1e3, color=C["orange"], ls="--", lw=1, label="Stage A")
    ax[1].set_xlabel("변수 값의 순서(점 옆 숫자)"); ax[1].set_ylabel("모터 승압 충전 손실 [kW]")
    ax[1].set_title("(b) 800 V 충전, 기준점에서 한 변수씩"); ax[1].legend(fontsize=7)
    # (c) 보조 손실 대 추가 반도체
    lab = {"1": "①", "5": "⑤", "4": "④ R2", "6": "⑥ 800 V 부품"}
    col = {"1": C["gray"], "5": C["green"], "4": C["orange"], "6": C["blue"]}
    for k in ("1", "5", "4", "6"):
        ax[2].scatter(out["semis"][k]["total"], out["aux"][k]["avg_W"], s=60, color=col[k])
        ax[2].annotate(lab[k], (out["semis"][k]["total"], out["aux"][k]["avg_W"]), xytext=(5, 3), textcoords="offset points")
    ax[2].set_xlabel("충전·보조 기능의 스위치 위치 수(구동 인버터 제외)"); ax[2].set_ylabel("보조 경로 평균 손실 [W]")
    ax[2].set_title("(c) 보조 경로 손실과 반도체 수(주행 대표 프로파일)")
    fig.tight_layout(); fig.savefig(outdir(EID) / "E25_motor_boost.png"); plt.close(fig)


if __name__ == "__main__":
    main()
