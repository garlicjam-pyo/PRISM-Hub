"""[E17] 보호 상태기계 결합: 링크전류 센서 감시(P6) 회귀와 R2 창 조정 모듈의 측정 기반 상태기계·고장 강등.

■ 목적
  E14는 보호·기동 요구(P1–P6)를, E19는 R2 창 조정 모듈의 모드 전환과 DAB 고장 강등을 "언제 어떤 모드로 바꿀지"를
  시험 조건으로 정해 둔 계산으로 확인했다. 실제 장치는 측정값으로 고장을 판단하고, 판단·차단에 지연이 있으며,
  운전 상태(배터리 전압, 부품 등급 상한 초과 여부)에 따라 다른 절차를 골라야 한다. E17은 이 결정 논리를 검증한다.
  (1) monitor: 링크전류 센서 타당성 감시(P6)를 켠 채 E12 시험 격자와 센서 요구 사양 집합을 다시 계산해도
      판정이 같고 오경보가 없는가(400 V 설계, 채택 제어기).
  (2) r2: R2 창 조정 모듈(R2-W460·R2-W410)의 보호 상태기계. 켬·끔은 V_bat/2와 히스테리시스로, 고장은 하드웨어 비교기·
      게이트 구동기 고장 신호·링크전압 창·버스 조정 상실 감시로 판단한다. 고장 종류별 강등 순서를 정하고 판정한다.
      - DAB 고장: E19 순서(DAB 정지 상태로 기준을 V_A로 1 ms 램프 → 영벡터 → 바이패스)를 링크전압 창 검출로 시작
      - H-브리지 차단(구동기 고장, 또는 변조율 고착을 보호가 차단한 경우): E19에서 즉시 바이패스는 740–838 A로 불통과였다.
        H-브리지가 꺼지면 소자의 역방향 도통이 다이오드 정류기를 이루어 직렬전압이 −(v_link + 2V_D)로 묶인다.
        창 조정 모듈은 음의 직렬전압(전력을 흡수하는 쪽)만 쓰므로, DAB가 링크전압을 정하면 H-브리지 없이도 버스를 잡을 수
        있다. 이 성질로 (a) 400 V 부하 분리가 끝날 때까지 버스를 창 안에 붙잡고(clamp hold), (b) 링크를 0 V로 20 V/ms로 내려
        직렬전압을 다이오드 전압까지 줄인 뒤(collapse, 링크 ≤ 0.5 V 또는 정체 감지), (c) 바이패스를 게이트 전압을 올려 닫되
        경로전류가 투입 시작값 + 25 A를 넘지 않게 조절한다(soft bypass).
        비교 정책: 즉시 바이패스(now), 붙잡지 않고 바로 붕괴(collapse_now), 붕괴 뒤 바로 닫기(clamp_hard).
      - (2026-10-24, 회로 TB09 1차 결과 반영) 회로에서는 링크가 0.5 V까지 내려가지 않고 3.5–22 V에서 멈췄고, 남은 직렬전압을
        로그 램프(1 ms)로 닫자 버스 RC 감쇠기 충전전류로 경로전류가 177 A까지 올랐다. 그래서 정체 감지와 경로전류 조절을 넣었고,
        감도 'DAB 저링크 저하'(링크 10 V 아래 DAB 전달 저하)로 이 동작을 평균모델에서도 확인한다.

■ 왜 필요한가
  R2의 목표는 Stage B 고장이 48 V 공급을 끊지 않는 것이다(Stage A는 계속 동작, 버스 = V_A로 강등). 그런데 H-브리지
  고장의 강등 방식이 정해지지 않았고(E19), 강등 후 버스 = V_A가 부품 상한을 넘는 팩에서는 400 V 부하를 분리해야 하므로
  분리에 걸리는 시간 동안 버스를 상한 아래로 붙잡을 수 있는지가 강등 순서를 정한다. TB08에서 회로로 본 바이패스 투입·
  열림 과도도 같은 상태기계 안에서 다시 본다(바이패스를 3.3 mΩ 저항으로 모델링).

■ 모델(r2)
  E19의 6상태 평균모델을 일반화했다. 바이패스는 직렬 포트(N1–N2) 사이의 컨덕턴스(닫힘 3.3 mΩ, 소프트 투입은 10 Ω에서 5 µs마다
  로그 단계로 낮추고 경로전류 제한에 걸리면 되올림), H-브리지는 PWM·영벡터·전 소자 차단(역방향 도통 V_D = 2 V/소자, 감도 1.4·3.0 V), DAB는 1차 지연 전류원
  (강등 중에는 주 제어기와 독립인 보조 루프가 지령). 400 V 부하 분리는 명령 후 20 ms(접촉기, 감도 50 ms)에 정전력 부하가
  조정형 Stage C 몫(5 kW)으로 줄어드는 것으로 둔다. 적분 간격 0.1 µs(중점법), 제어·감시 표본 5 µs, 전달지연 5 µs.

■ 판정(시험 전에 고정)
  켬: 전류 ≤ 90 A, 직렬 ≤ 90 V, 링크 90–110 V, 버스 ≤ 상한, 바이패스 전류 ≤ 329 A(2병렬 → 소자당 펄스 정격의 50 %),
      램프 끝 뒤 ±4 V 정착 ≤ 10 ms, 최종 ±4 V
  끔: 전류 ≤ 90 A, 직렬 ≤ 90 V, 링크 90–110 V, 바이패스 전류 ≤ 329 A, 버스 ≥ 260 V, 바이패스 상태 도달, 버스 ≤ 상한
  고장: 경로·필터 ≤ 100 A, 직렬 ≤ 120 V, 링크 ≤ 120 V, 바이패스 전류 ≤ 329 A, 버스 ≥ 260 V, 강등 상태(바이패스) 도달.
      H-브리지 차단 대응은 여기에 "400 V 부하가 연결된 동안 버스 ≤ 부품 등급 상한"을 더한다.
      DAB 고장은 버스가 상한을 넘는 시각을 기록한다(부하 분리 시간 요구).

■ 부품 스트레스(정보, 판정에 넣지 않음)
  DAB 링크 쪽 순시 첨두: 평균모델에는 순시 전류가 없으므로 평균 링크전류와 버스·링크전압에서 SPS 식으로 계산한다(dab_sps_peak).
  강등 중에는 n·v_link ≪ v_bus라 순환전류가 정격점의 4배 이상이 된다(회로 TB09에서 n·|i_L|로 확인). 소프트 투입 소자 에너지
  ∫ G·v_s² dt도 기록한다.

■ 실행   python E17_protection_integration.py monitor r2 figures
■ 결과   results/E17/*.json, results/E17/E17_*.png
"""
import sys
import time
from multiprocessing import Pool

import numpy as np

import stage_b_tests as st
from controller_adopted import K_ADOPTED, CP
from model_stage_b_switching import simulate_switching
from common import save_json, verdict, workers, outdir
import E12_switching_verification as E12

EID = "E17"
VAL_E12 = "../../../validation/2026-10-11-matlab-switching/E12"


# ----------------------------------------------------------------------------------------------
# (1) 감시를 켠 E12 재계산
# ----------------------------------------------------------------------------------------------
def _mon_case(args):
    tier, vbat, a, b, p, sw, meta = args
    meta = dict(meta); sens = meta.pop("_sensors", None); seed = meta.pop("_seed", 1)
    r = simulate_switching(float(vbat), float(a), float(b), p, CP, K_ADOPTED, predict=True, profile=0, sw=sw,
                           sensors=None if sens is None else np.array(sens), seed=seed)
    row = dict(tier=tier, vbat=vbat, p0=a, p1=b, **meta)
    row.update(E12.judge_sw(tier, r, p))
    rec = r["rec"]
    row["monitor_fault"] = bool(rec[:, 24].max() > .5)          # 감시가 고장으로 판정했는가(오경보)
    row["monitor_resid_max_A"] = float(np.abs(rec[:, 23]).max())  # 느린 필터 잔차 최대
    return row


def _key(r):
    return (r["tier"], r["set"], float(r["vbat"]), float(r["p0"]), float(r["p1"]), r.get("variant", ""))


def monitor():
    import json, os
    base, tol = E12.sets_sw()
    mon = dict(link_monitor=True)
    js = []
    for v in st.V_ALL:
        for n, p in base.items():
            js += [(1, v, a, b, p, mon, dict(set=n)) for a, b in st.T1_STEPS]
            js += [(2, v, a, b, p, mon, dict(set=n)) for a, b in st.T2_STEPS]
    for v in st.V_TOL:
        for n, p in tol.items():
            js += [(1, v, a, b, p, mon, dict(set=n)) for a, b in st.T1_STEPS]
            js += [(2, v, a, b, p, mon, dict(set=n)) for a, b in st.T2_STEPS]
    ngrid = len(js)
    cases = [(t, v, a, b, n, p) for v in st.V_ALL for n, p in base.items()
             for t, steps in ((1, st.T1_STEPS), (2, st.T2_STEPS)) for a, b in steps]
    variants = {"요구 사양(16비트·잡음)": E12.sensor_set(bits=16, noise=E12.SENS_NOISE_REQ),
                "요구 사양 + 오차(전류 낮게·전압 높게)": E12.sensor_set(bits=16, noise=E12.SENS_NOISE_REQ, sign=E12.CUR_LOW_V_HIGH),
                "요구 사양 + 오차(전류 높게·전압 낮게)": E12.sensor_set(bits=16, noise=E12.SENS_NOISE_REQ, sign=-E12.CUR_LOW_V_HIGH)}
    js += [(t, v, a, b, p, mon, dict(set=n, variant=name, _sensors=s.tolist(), _seed=1000 + i))
           for name, s in variants.items() for i, (t, v, a, b, n, p) in enumerate(cases)]
    t0 = time.time()
    with Pool(workers()) as pool:
        rows = pool.map(_mon_case, js, chunksize=2)
    print("  monitor: %d건, %.0f s" % (len(rows), time.time() - t0))
    grid, sens = rows[:ngrid], rows[ngrid:]
    # E12 저장 결과(감시 없음)와 비교
    ref_grid = {_key(r): r for r in json.load(open(os.path.join(VAL_E12, "grid.json")))["rows"]}
    ref_sens = {_key(r): r for r in json.load(open(os.path.join(VAL_E12, "sensors.json")))["rows"]}
    def compare(rows, ref):
        ch, dp, dd, miss = [], [], [], 0
        for r in rows:
            q = ref.get(_key(r))
            if q is None:
                miss += 1; continue
            if q["pass_"] != r["pass_"]:
                ch.append((r["tier"], r["set"], r["vbat"], r["p0"], r["p1"], r.get("variant", ""), q["pass_"], r["pass_"]))
            dp.append(max(r["path_inst"], r["bridge_inst"]) - max(q["path_inst"], q["bridge_inst"]))
            dd.append(r["droop"] - q["droop"])
        return dict(compared=len(dp), missing=miss, verdict_changes=ch,
                    inst_current_diff_A=[float(min(dp)), float(max(dp))] if dp else None,
                    droop_diff_V=[float(min(dd)), float(max(dd))] if dd else None)
    out = dict(grid=dict(total=len(grid), passed=sum(r["pass_"] for r in grid),
                         monitor_faults=sum(r["monitor_fault"] for r in grid),
                         resid_max_A=max(r["monitor_resid_max_A"] for r in grid),
                         vs_E12=compare(grid, ref_grid)),
               sensors={})
    for name in variants:
        sel = [r for r in sens if r["variant"] == name]
        out["sensors"][name] = dict(total=len(sel), passed=sum(r["pass_"] for r in sel),
                                    passed_640plus=sum(r["pass_"] for r in sel if r["vbat"] >= 640),
                                    total_640plus=sum(1 for r in sel if r["vbat"] >= 640),
                                    monitor_faults=sum(r["monitor_fault"] for r in sel),
                                    resid_max_A=max(r["monitor_resid_max_A"] for r in sel),
                                    vs_E12=compare(sel, ref_sens))
    g = out["grid"]
    print("  격자(감시 켬): %d/%d 통과, 오경보 %d건, 잔차 최대 %.2f A, E12 대비 판정 변화 %d건, 순시 전류 차 %s A"
          % (g["passed"], g["total"], g["monitor_faults"], g["resid_max_A"], len(g["vs_E12"]["verdict_changes"]), g["vs_E12"]["inst_current_diff_A"]))
    for name, s in out["sensors"].items():
        print("  %s: %d/%d 통과(640 V 이상 %d/%d), 오경보 %d건, 잔차 최대 %.2f A, 판정 변화 %d건"
              % (name, s["passed"], s["total"], s["passed_640plus"], s["total_640plus"], s["monitor_faults"], s["resid_max_A"],
                 len(s["vs_E12"]["verdict_changes"])))
    ok = (g["monitor_faults"] == 0 and not g["vs_E12"]["verdict_changes"]
          and all(s["monitor_faults"] == 0 and not s["vs_E12"]["verdict_changes"] for s in out["sensors"].values()))
    verdict("E17 감시를 켜도 E12 격자·센서 요구 사양 판정이 같고 오경보가 없다", ok)
    out["pass_"] = bool(ok)
    save_json(EID, "monitor", dict(summary=out, rows=rows))
    return out


# ----------------------------------------------------------------------------------------------
# (2) R2 창 조정 모듈 보호 상태기계
# ----------------------------------------------------------------------------------------------
from dataclasses import replace                                     # noqa: E402
from model_stage_b import primary_power, current_limit, equilibrium  # noqa: E402
from E14_protection_startup import va_est                            # noqa: E402
import E19_r2_window_module as E19                                   # noqa: E402
import dab_modulation as DM                                          # noqa: E402

DT = 1e-7                    # 적분 간격(바이패스 3.3 mΩ·C_s 100 µF 시정수 0.33 µs를 중점법으로 안정하게)
T_EV = .5e-3                 # 사건(켬 허가, 정지 요청, 고장) 시각
H = 5.                       # 모드 히스테리시스 [V]
LOAD_MIN_V = 260.
# 바이패스(150 V GaN EPC2305 2병렬 × 역직렬)와 H-브리지 다이오드
R_BYP = 3.3e-3               # 바이패스 도통저항(E15·E19·TB08과 같음)
VD = 2.0                     # H-브리지 소자의 역방향 도통 전압(꺼진 GaN, 소자 1개, 수십 A) [V]. 데이터시트 V_SD 1.4 V(0.5 A)
I_BYP_LIM = 329.             # 바이패스 전류 판정 한계: 2병렬이므로 소자당 164.5 A = 펄스 정격 329 A의 50 %
R_SOFT0, T_SOFT = 10., 1e-3    # 소프트 투입: 저항을 10 Ω → 3.3 mΩ로 1 ms 동안 로그 스케일 램프(게이트 전압 완만 상승).
                               # 경로 L–버스 C 공진 주기(약 0.15 ms)보다 길게 해 투입 때 버스 계단(직렬전압 수 V)이 진동을 일으키지 않게 한다
# 400 V 부하 분리와 강등 순서
P_C = 5000.                  # 분리 뒤 남는 부하 = 조정형 Stage C(48 V 공급, 입력 V_A 범위)
T_SHED = 20e-3               # 400 V 부하 분리 완료 시간(접촉기, 명령 후)
RATE_COL = 20e3             # 링크 붕괴: 링크 기준을 20 V/ms로 0 V까지 낮춘다(DAB 전류 한계 안)
T_COL_MAX = 10e-3            # 붕괴가 이 시간 안에 VL_SOFT에 이르지 못하면 그대로 소프트 투입(실패로 기록)
VL_SOFT = .5                 # 이 링크전압 아래에서 소프트 투입 시작(직렬전압 = 링크 + 다이오드 2개 + R_h 강하)
# (TB09 회로 결과로 추가, 2026-10-24) 회로에서는 링크가 0.5 V까지 내려가지 않고 3.5–22 V에서 멈췄다(전압비가 극단인 DAB의
# 실제 전달전류 부족). 그래서 (1) 붕괴 정체를 감지해 소프트 투입으로 넘어가고, (2) 소프트 투입을 경로전류로 조절한다
# (남은 직렬전압 수–십 V가 버스 RC 감쇠기 1.6 mF를 거의 직접 충전하면 로그 램프만으로는 경로전류가 177 A까지 올랐다).
VL_STALL, T_STALL, DV_STALL = 15., .5e-3, .5   # 링크 기준이 0에 닿은 뒤 0.5 ms 동안 0.5 V도 안 내려가고 링크 ≤ 15 V면 정체
DI_SOFT, K_UP = 25., 1.2     # 소프트 투입 중 경로전류 > 투입 시작값 + 25 A면 저항을 표본(5 µs)마다 1.2배로 되올린다
T_SOFT_MAX = 5e-3            # 소프트 투입 시간 상한: 넘으면 주 스위치를 닫고 기록(soft_timeout)
PK_FAULT = 1.5               # (E20) 강등 상태(9–11)의 DAB 링크 쪽 순시 첨두 상한 = 정격점 첨두의 1.5배(dmod 'eps'에서 지령 전류 제한)
T_RESTORE = .5e-3            # (E20) 일시 감발 해제: 강등(바이패스 닫힘) 0.5 ms 뒤 400 V 부하 출력을 되돌린다
T_PREP, T_WAIT = .5e-3, .2e-3  # 켬: 바이패스 + 영벡터 분담 시간, 바이패스 열림 뒤 제어 시작까지(TB08과 같음)
R_DMP, C_DMP = 48.6e-3, 1.6e-3  # 버스 RC 감쇠기(E13 설계값, R2 기본형 구성). E19·TB08에는 없었으므로 '없음'을 감도로 본다
R_BRK = 3.                   # 링크 제동 저항(선택): 110 V에서 4 kW. 창 조정 최대 흡수전력(W410 920 V·25 kW에서 약 3 kW)보다 크게
TAU_ST = 50e-6               # 전류 조향(steer): 바이패스 전류를 0으로(켬) 또는 직렬전압을 0으로(끔) 모는 시정수
RAMP, HOLD, ZERO = 1e-3, .2e-3, .2e-3  # 끔·DAB 고장: 기준 램프, 최소 유지, 영벡터
VS_GATE, T_GATE, T_GATE_MAX = 2., 50e-6, 5e-3   # 영벡터 진입 조건: 램프 뒤 기준을 V_A 추정으로 따라가다가 |v_s| ≤ 2 V가 50 µs 이어지면
                                               # (E19의 '바이패스 직전 직렬 ≤ 2 V'를 진입 조건으로). 5 ms 안에 안 되면 그대로 진입(기록)
# 보호 문턱(시험 전에 고정). 하드웨어 비교기는 연속 감시(검출 + 게이트 전파 1.2 µs), 소프트웨어는 5 µs 표본
I_HW, VL_HW, VS_HW = 110., 115., 100.    # 경로·필터 전류, 링크전압, 직렬전압. 버스 과전압 = 부품 등급 상한
T_HW = 1.2e-6
VL_SW, T_SW = (92., 108.), 50e-6         # 링크전압 창: 벗어난 채 50 µs면 DAB 고장으로 판단
VB_SW, T_VB = 20., .5e-3                 # 버스 조정 상실: |v_bus − V_ref| > 20 V가 0.5 ms 지속
T_GDF = 1e-6                             # 게이트 구동기 고장 신호(H-브리지 개방) 전달
# 강등 중 DAB 링크 제어(주 제어기와 독립인 보조 루프, 5 µs 표본)
KP_B, KI_B, QB_MAX = .3, 100., 10.       # 버스 → 링크 기준 PI [V/V, 1/s], 적분 몫 제한 ±10 V(앞먹임이 주, 적분은 V_D 오차 보정)
W_L = 2 * np.pi * 300.                   # 링크전압 루프 [rad/s]


def diode(x, vd):
    """꺼진 H-브리지의 다이오드 상태 (me, blocked). |v_s| ≤ v_link + 2V_D이고 필터전류 0이면 차단."""
    ih, vs, vl = x[3], x[1], x[4]
    if ih == 0. and abs(vs) <= vl + 2 * vd:
        return 0., True
    return (-np.sign(ih) if ih != 0. else np.sign(vs)), False


def deriv_r2(x, m, bridge, icmd, G, vsrc, P, p, dz, vd, Gb=0.):
    if len(x) == 7:                                               # 버스 RC 감쇠기(선택): 7번째 상태 = 감쇠기 커패시터 전압
        d = deriv_r2(x[:6], m, bridge, icmd, G, vsrc, P, p, dz, vd, Gb)
        idmp = (x[2] - x[6]) / R_DMP
        d[2] -= idmp / p.Cb
        return np.append(d, idmp / C_DMP)
    """일반화 모드 모델. bridge: 'pwm'(변조율 m) | 'zero'(영벡터) | 'off'(전 소자 차단, 다이오드 dz)
    G: 바이패스 컨덕턴스(직렬 포트 N1–N2 사이), icmd: DAB 링크전류 지령(0이면 DAB 정지와 같음),
    Gb: 링크 제동 저항 컨덕턴스(켜졌을 때 1/R_BRK)."""
    ip, vs, vb, ih, vl, idab = x
    dip = (vsrc - p.R * ip + vs - vb) / p.L
    dvs = (ih - ip - G * vs) / p.Cs
    dvb = (ip - (P + primary_power(vl * idab, p)) / vb) / p.Cb
    didab = (icmd - idab) / p.tau
    if bridge == "pwm":
        vbr, ilk = m * vl, m * ih
    elif bridge == "zero":
        vbr, ilk = 0., 0.
    else:
        me, blocked = dz
        if blocked:
            return np.array([dip, dvs, dvb, 0., (idab - Gb * vl) / p.Clink, didab])
        vbr, ilk = me * (vl + 2 * vd), me * ih
    return np.array([dip, dvs, dvb, (vbr - vs - p.Rh * ih) / p.Lh, (idab - ilk - Gb * vl) / p.Clink, didab])


def bypass_state(vbat, P, p):
    """바이패스 정상상태: 직렬 포트를 바이패스(3.3 mΩ)가 단락, H-브리지·DAB 정지, 링크 100 V."""
    va = float(va_est(vbat, P, p.R + R_BYP)); ip = P / va
    return np.array([ip, -R_BYP * ip, va, 0., 100., 0.])


def share_state(vbat, P, p):
    """바이패스 + 영벡터 분담 정상상태(TB08 사례 E의 시작 상태): 바이패스(3.3 mΩ)와 영벡터 경로(R_h)가 저항비로 나눈다."""
    rpar = R_BYP * p.Rh / (R_BYP + p.Rh)
    va = float(va_est(vbat, P, p.R + rpar)); ip = P / va
    return np.array([ip, -rpar * ip, va, ip * R_BYP / (R_BYP + p.Rh), 100., 0.])


class LinkAux:
    """강등 중 DAB 보조 루프: H-브리지가 꺼져 다이오드 정류기가 되면 직렬전압 = −(v_link + 2V_D)이므로,
    DAB로 링크전압을 정해 버스를 잡는다(hold), 이어 링크를 0으로 내린다(collapse).
    hold 'vw'  : 버스를 V_W에 붙잡는 링크 기준(버스 PI + 앞먹임). 링크가 40–67 V로 내려가 DAB 전압비가 어긋난다.
    hold 'match': (E20) DAB 전압비를 1로 두는 링크 기준 n·v_link = v_bus, 즉 v_link = (V_A − (R + R_h)i_p − 2V_D)/(n + 1).
                  버스는 V_A − (n + 1)/n·…로 V_W보다 낮지만(1008 V에서 약 410 V) 부품 상한·하한 안이고, DAB는 정격 전압비로
                  동작한다. DAB 정격을 넘는 링크전력은 제동 저항이 받는다."""
    def __init__(self, p, VW, hold="vw"):
        self.p, self.VW, self.qb, self.mode, self.t0, self.vl0, self.hold = p, VW, 0., "hold", 0., 100., hold

    def collapse(self, t, vl):
        self.mode, self.t0, self.vl0 = "collapse", t, vl

    def step(self, x, t, vbat):
        p = self.p; ip, vs, vb, ih, vl, idab = x[:6]
        if self.mode == "hold" and self.hold == "match":
            vref = float(np.clip((vbat / 2 - (p.R + p.Rh) * ip - 2 * VD) / (p.turns + 1), 0., 100.))
        elif self.mode == "hold":
            e = vb - self.VW
            self.qb = float(np.clip(self.qb + p.Ts * KI_B * e, -QB_MAX, QB_MAX))
            ff = vbat / 2 - (p.R + p.Rh) * ip - 2 * VD - self.VW
            vref = float(np.clip(ff + KP_B * e + self.qb, 0., 110.))
        else:
            vref = max(self.vl0 - RATE_COL * (t - self.t0), 0.)
        icmd = -abs(ih) + p.Clink * W_L * (vref - vl)
        lim = current_limit(vb, max(vl, 1e-3), p)
        return float(np.clip(icmd, -lim, lim)), vref


def dab_sps_peak(vb, vl, idab, p):
    """SPS DAB의 링크 쪽(2차) 전류 첨두 [A]: 평균 링크전류 idab를 내는 위상 φ를 SPS 식에서 구하고, 반주기 시작(θ = 0)과
    2차 전환(θ = φ) 전류 중 큰 것. 평균모델에는 없는 순시 전류로, 1차 전압(vb/n)과 링크전압이 어긋날수록 커진다
    (링크 → 0이면 φ와 무관하게 vb/(4 n f_s L′), L′ = L_dab/n²)."""
    n, w = p.turns, 2 * np.pi * p.fs
    k = n * max(vb, 1.) / (w * p.Ldab)
    a = min(abs(idab) / (np.pi * k / 4), 1.)
    phi = np.pi / 2 * (1 - np.sqrt(1 - a))
    v1, wl = vb / n, w * p.Ldab / n ** 2
    i0 = -(v1 * np.pi + vl * (2 * phi - np.pi)) / (2 * wl)
    iph = (v1 * (2 * phi - np.pi) + vl * np.pi) / (2 * wl)
    return max(abs(i0), abs(iph))


def r2_run(job):
    """R2-W 모듈 1건: 측정 기반 상태기계 + 일반화 모드 모델.
    job: case, V, P, event('enable' | 'disable' | 'dab' | 'hb_open' | 'm_pos' | 'm_neg'),
         policy  H-브리지 차단: 'now' | 'collapse_now' | 'clamp' | 'clamp_brk' | 'clamp_brk_hard'
                 DAB 고장: 'ramp'(E19, 검출 즉시 V_A로 램프) | 'brk_hold'(링크 제동 저항으로 붙잡고 분리 뒤 램프)
         prep('zero' | 'steer'), t_prep, wait(켬), close('zero' | 'steer', 끔·DAB 고장의 바이패스 직전),
         vd, t_soft(제한 없는 소프트 램프 시간), t_shed, start_share, duration, keep,
         dab_lowv(감도: 링크전압이 이 값 아래면 DAB 전달전류를 v_link/dab_lowv배로 줄인다 — 회로에서 본 붕괴 정체 모사),
         hold('vw' | 'match', H-브리지 강등 유지의 링크 기준, E20), curtail(H-브리지 고장이면 V_A와 무관하게 400 V 부하 출력을
         줄이고 강등 뒤 V_A ≤ 상한이면 되돌림, E20), dmod('sps' | 'eps', 강등 상태 9–11의 DAB 변조. 'eps'면 첨두 ≤ PK_FAULT × 정격점 첨두가 되도록
         지령 전류를 제한, E20. pk_fault로 배수를 바꿈), pk_table('ideal' | 'sw', E21: 'sw'면 첨두 상한 탐색·첨두 지표·실제 링크전류를
         데드타임·출력용량·역방향 도통을 넣은 스위칭 정상상태 표로), soft_fail(소프트 투입 시간 상한이면 주 스위치를 닫지 않고 FAILSAFE로, E20).
    (E29, 모두 선택이고 없으면 이전과 같다)
         p_c   : 분리·감발 뒤 남는 부하 [W](기본 P_C 5 kW, 잔여부하 문턱 탐색용)
         sals  : dict(loads=sals_loads.SalsLoads 인자, i_col, t_conf, t_cur_max). 주면 400 V 부하를 등급별 계약 응답으로 바꾼다.
                 고장 검출 때 SALS 감발(+ Stage C 회생 차단)을 보내고, V_A가 상한을 넘는 팩만 접촉기 분리를 바로 명령한다.
                 감발 전용(V_A ≤ 상한)이면 H-브리지 고장 유지(9)를 시간이 아니라 부하전류 추정(i_p − (C_b + C_dmp)dv_bus/dt,
                 tau_il 0.2 ms 필터) |i_load| ≤ i_col이 t_conf 이어질 때
                 끝내고, t_cur_max 안에 안 되면 접촉기 분리로 넘어간다. 강등 T_RESTORE 뒤 SALS 되돌림(접촉기를 연 경우는 없음).
         event2: 두 번째 고장(H-브리지 비교기 차단) 시각 [s]. DAB 고장 강등 중이면 이중 고장(FAILSAFE)
         astop : dict(delay, C_A). 이중 고장이면 delay 뒤 Stage A를 멈춘다(V_A 노드 = C_A가 경로전류로 방전)
                 (E37, 선택) R_dis·dv_on·dv_off: Stage A 정지 뒤 V_A 노드 방전 저항. V_A > v_bus − dv_on(기본 60 V)이면 켬,
                 V_A < v_bus − dv_off(기본 65 V)이면 끔. 없으면 이전과 같다
         fs_brake: 이중 고장에서도 링크 제동 저항의 과전압 보호(110 V 켬·105 V 끔)를 유지
    (E38, 모두 선택이고 없으면 이전과 같다. sals가 있을 때만 쓴다)
         sc_pause : True면 링크 붕괴 시작 때 Stage C를 일시 정지(양의 입력전력을 4 kW/ms로 0까지, 허브 내부 명령)하고,
                    강등(바이패스 닫힘) T_RESTORE 뒤 같은 변화율로 재개한다(감발 전용 팩은 SALS 되돌림과 같은 시각)
         load_stop: 이중 고장(FAILSAFE) 진입 때 400 V 부하 전체(Stage C 포함)를 이 시간[s] 동안 선형으로 0까지(전용 배선 정지 신호)"""
    case, V, P, event = job["case"], job["V"], job["P"], job["event"]
    pol = job.get("policy", {"dab": "brk_hold"}.get(event, "clamp_brk")); vd = job.get("vd", VD)
    t_soft = job.get("t_soft", T_SOFT); t_shed = job.get("t_shed", T_SHED)
    p_c = job.get("p_c", P_C)
    sals = job.get("sals"); SL = None; Pl_s = None
    if sals is not None:
        from sals_loads import SalsLoads
        SL = SalsLoads(**sals["loads"])
        i_col, t_conf, t_cur_max = sals["i_col"], sals["t_conf"], sals["t_cur_max"]
        assert abs(SL.power(0.) - P) < 1e-6, "부하 구성의 합이 P와 다르다"
    t_cont = None; low_since = None; restored = False; ev2 = job.get("event2"); astop = job.get("astop"); t_as = None
    dis_on = False; E_dis = 0.; P_dis_pk = 0.; I_dis_pk = 0.; n_dis = 0                     # (E37) V_A 노드 방전 저항
    fs_brake = bool(job.get("fs_brake", False))
    sc_pause = bool(job.get("sc_pause", False)); ls_ramp = job.get("load_stop")              # (E38)
    t_wait = job.get("wait", T_WAIT); t_prep = job.get("t_prep", T_PREP)
    prep, close = job.get("prep", "zero"), job.get("close", "zero")
    brk = pol in ("clamp_brk", "clamp_brk_hard", "brk_hold")
    c = E19.CASES[case]; p, cp = E19.plant(case); VW, upper = c["VW"], c["upper"]
    VA = V / 2
    sample = int(round(p.Ts / DT)); lag = int(round(p.delay / DT))
    # ---- 초기 상태 -------------------------------------------------------------------------------
    if event == "enable" and job.get("start_share"):                    # TB08 사례 E와 같은 시작(분담 정상상태, 곧바로 PREP)
        x = share_state(V, P, p); st, G = "PREP", 1. / R_BYP
    elif event == "enable":
        x = bypass_state(V, P, p); st, G = "BYPASS", 1. / R_BYP
    else:
        x0, u0 = equilibrium(V, P, p); x = np.array(x0, float); st, G = "WINDOW", 0.
    damper = job.get("damper", True)                                    # R2 기본형의 버스 RC 감쇠기(기본 포함)
    if damper:
        x = np.append(x, x[2])
    ctrl = E19.RampW(cp, V, lambda t: VW); u = np.array([x[1] / x[4], 0.]); ctrl.reset(x, u)
    vref_fn = lambda t: VW
    vt = [VW]                                                          # 추종 기준(V_A 추정)을 담는 칸
    track = lambda tt: vt[0]
    gate_since = None; gate_timeout = False
    hold, curtail, dmod = job.get("hold", "vw"), bool(job.get("curtail", False)), job.get("dmod", "sps")
    soft_fail = bool(job.get("soft_fail", False))
    aux = LinkAux(p, VW, hold)
    curtail_only = False; dab_pk_hold = 0.; dab_pk_col = 0.
    pk_rated = dab_sps_peak(VW, 100., p.power_max / 100., p)          # 정격점(링크 100 V, 정격 전력) 첨두
    pkf = job.get("pk_fault", PK_FAULT)                               # 첨두 상한 배수(E20 감도: 회로 여유)
    sw = job.get("pk_table", "ideal") == "sw" and job.get("dmod", "sps") == "eps"   # (E21) 스위칭 반영 첨두·전류표
    buf = np.tile(u, (lag + 1, 1)); tick = 0
    if SL is not None:                                                # (E29) 부하전류 추정 = 경로전류 − 버스 커패시터 전류(필터)
        c_tot = p.Cb + (C_DMP if damper else 0.); tau_il = sals.get("tau_il", .2e-3); il_f = P / x[2]; vb_prev = x[2]
    t_st = 0.; hw_since = sw_since = vb_since = None; t_det = None; det_src = None; t_gdf = None
    shed_cmd = None; loads400 = True; bridge_dead = False; dab_dead = False; Gb = 0.; steer = False
    t_over = None; t_soft0 = None; t_close = None; events = []; icmd_aux = 0.; vl_aux_ref = 100.
    r_soft = R_SOFT0; ip_soft0 = 0.; k_dn = (R_SOFT0 / R_BYP) ** (p.Ts / t_soft)   # 소프트 투입(경로전류 조절)
    stall_ref = None; stalled = False; soft_entry = None; soft_timeout = False; e_soft = 0.; t_deg = None
    dab_pk = 0.; dab_pk_t = None; dab_pk_st = None; dab_lowv = job.get("dab_lowv")
    DAB_ON = ("WINDOW", "OFF_RAMP", "OFF_HOLD", "HB_HOLD", "HB_COLLAPSE", "SOFT_BYP")
    # 계산 시간: H-브리지 강등은 분리 + 붕괴 상한(10 ms) + 소프트 상한(5 ms) + 여유, DAB 고장은 저부하에서 링크가 창을 벗어나기까지
    # (V_A ≈ V_W·5 kW에서 약 31 ms) 보도록 분리 + 25 ms
    dur = job.get("duration") or (T_EV + (t_shed + 16e-3 if event in ("hb_open", "m_pos", "m_neg") else
                                          (t_shed + 25e-3 if event == "dab" else 8e-3)))
    n = int(round(dur / DT)); log = np.empty((n, 10))
    SWITCHING = ("PREP", "OPEN_WAIT", "WINDOW", "OFF_RAMP", "OFF_HOLD", "ZERO", "DAB_HOLD", "DAB_RAMP")
    NORMAL = ("PREP", "OPEN_WAIT", "WINDOW", "OFF_RAMP", "OFF_HOLD")

    def go(s, t):
        nonlocal st, t_st
        st, t_st = s, t; events.append((s, round(t * 1e3, 4)))

    def gate_ok(t):
        """|v_s| ≤ VS_GATE가 T_GATE 동안 이어졌는가(표본마다 호출)."""
        nonlocal gate_since
        if abs(x[1]) <= VS_GATE:
            gate_since = t if gate_since is None else gate_since
            return t - gate_since >= T_GATE
        gate_since = None
        return False

    def hb_path(t, x):
        """H-브리지 차단(구동기 고장 또는 보호 래치) 뒤의 강등 경로."""
        nonlocal G, t_close
        if dab_dead:
            go("FAILSAFE", t); return                               # 이중 고장: Stage A 협조 정지가 필요(모델 밖)
        if pol == "now":
            G = 1. / R_BYP; t_close = t; go("DEGRADED", t)
        elif pol == "collapse_now":
            aux.collapse(t, x[4]); go("HB_COLLAPSE", t)
        else:
            go("HB_HOLD", t)

    for k in range(n):
        t = k * DT
        # ---- 사건 주입 --------------------------------------------------------------------------
        if t >= T_EV:
            if event == "dab":
                dab_dead = True
            if event == "hb_open" and not bridge_dead:
                bridge_dead = True; t_gdf = t + T_GDF
        if ev2 is not None and t >= ev2 and not bridge_dead:     # (E29) 두 번째 고장: H-브리지 비교기 차단으로 기록
            bridge_dead = True; events.append(("hw_trip", round(t * 1e3, 4)))
            if t_det is None:                                      # 비교기 차단은 검출이다(하드웨어 비교기와 같게)
                t_det, det_src = t, "hw"
        # ---- 하드웨어 비교기(연속, 브리지가 동작하는 동안): 차단 래치 -----------------------------------------
        if st in SWITCHING and not bridge_dead:
            cond = (abs(x[0]) > I_HW or abs(x[3]) > I_HW or x[4] > VL_HW or abs(x[1]) > VS_HW
                    or (st in NORMAL and x[2] > upper))            # 버스 과전압은 정상 조정 상태에서만(강등 램프 중에는 가림)
            if cond:
                hw_since = t if hw_since is None else hw_since
                if t - hw_since >= T_HW:
                    bridge_dead = True; events.append(("hw_trip", round(t * 1e3, 4)))
                    if t_det is None:
                        t_det, det_src = t, "hw"
            else:
                hw_since = None
        # ---- 상태기계(5 µs 표본) --------------------------------------------------------------------
        if k % sample == 0:
            va_m = V / 2 - p.R * x[0]                              # V_A 추정(배터리 전압 센서 − 경로 강하)
            vt[0] = va_m
            if event == "hb_open" and t_det is None and t_gdf is not None and t >= t_gdf:
                t_det, det_src = t, "gate_driver_fault"
            if st in ("WINDOW", "OFF_RAMP", "OFF_HOLD") and t_det is None:
                if not (VL_SW[0] <= x[4] <= VL_SW[1]):              # DAB 고장 판단(링크전압 창)
                    sw_since = t if sw_since is None else sw_since
                    if t - sw_since >= T_SW:
                        t_det, det_src = t, "link_window"; dab_dead = True
                else:
                    sw_since = None
                if abs(x[2] - vref_fn(t)) > VB_SW:                  # 버스 조정 상실 → 브리지 차단
                    vb_since = t if vb_since is None else vb_since
                    if t - vb_since >= T_VB:
                        t_det, det_src = t, "bus_window"; bridge_dead = True
                else:
                    vb_since = None
            # 고장 → 강등 경로
            if t_det is not None and shed_cmd is None and st not in ("BYPASS",) and (
                    va_m > upper - 2 or (curtail and bridge_dead and det_src != "link_window")):
                shed_cmd = t; events.append(("shed_cmd", round(t * 1e3, 4)))
                curtail_only = va_m <= upper - 2                  # 상한 안이면 일시 감발(강등 뒤 되돌림)
                if SL is not None:                                 # (E29) SALS 감발은 항상, 접촉기 분리는 상한을 넘는 팩만 바로
                    SL.curtail(t)
                    if not curtail_only:
                        t_cont = t
            if SL is not None and t_det is not None:
                SL.block_regen(t)                                   # (E29) Stage C 회생 차단(허브 내부 명령)
            if st == "FAILSAFE" and SL is not None and t_cont is None:
                SL.curtail(t); t_cont = t                           # (E29) 이중 고장: 접촉기 분리 + SALS 감발
            if st == "FAILSAFE" and SL is not None and ls_ramp and SL.t_stop is None:
                SL.load_stop(t, ls_ramp); events.append(("load_stop", round(t * 1e3, 4)))   # (E38) 400 V 부하 정지 신호
            if st == "FAILSAFE" and astop is not None and t_as is None:
                t_as = t + astop["delay"]; vA = V / 2; events.append(("stageA_stop", round(t_as * 1e3, 4)))
            # (E29) 감발 전용: 부하전류 추정으로 유지(9) 끝을 정하고, 시간 상한이면 접촉기 분리로.
            # 고장 직후 다이오드가 막힌 동안(직렬 커패시터 충전, 수 ms)은 경로전류가 작아도 부하를 버스 커패시터가 대고 있으므로
            # 경로전류만으로는 판단할 수 없다(시험 전 점검에서 확인) → i_load ≈ i_p − (C_b + C_dmp)·dv_bus/dt를 0.2 ms로 거른다.
            if SL is not None:
                il_f += ((x[0] - c_tot * (x[2] - vb_prev) / p.Ts) - il_f) * p.Ts / tau_il; vb_prev = x[2]
            cur_ok = False
            if SL is not None and st == "HB_HOLD" and curtail_only and t_cont is None:
                if abs(il_f) <= i_col:
                    low_since = t if low_since is None else low_since
                    cur_ok = t - low_since >= t_conf
                else:
                    low_since = None
                if not cur_ok and t - shed_cmd >= t_cur_max:
                    t_cont = t; events.append(("fallback_sep", round(t * 1e3, 4)))
            if bridge_dead and t_det is not None and det_src != "link_window" and st in SWITCHING:
                hb_path(t, x)                                      # 검출된 뒤에만 반응(물리적 차단 ≠ 검출)
            elif bridge_dead and det_src == "link_window" and st in SWITCHING and any(e[0] == "hw_trip" for e in events):
                hb_path(t, x)                                      # DAB 고장 강등 중 하드웨어 차단 → 이중 고장
            elif det_src == "link_window" and st in ("WINDOW", "OFF_RAMP", "OFF_HOLD"):
                if pol == "brk_hold" and shed_cmd is not None:
                    go("DAB_HOLD", t)
                else:
                    vref_fn = (lambda tt, v0=vref_fn(t), v1=va_m, t1=t: v0 + (v1 - v0) * min((tt - t1) / RAMP, 1.))
                    ctrl.vref_fn = vref_fn; go("DAB_RAMP", t)
            # 링크 붕괴 정체: 링크 기준이 0에 닿은 뒤 T_STALL 동안 DV_STALL도 안 내려가면(링크 ≤ VL_STALL)
            if st == "HB_COLLAPSE" and t - t_st >= aux.vl0 / RATE_COL:
                if stall_ref is None or stall_ref[1] - x[4] >= DV_STALL:
                    stall_ref = (t, x[4])
                stalled = t - stall_ref[0] >= T_STALL and x[4] <= VL_STALL
            # 정상 순서
            if st == "BYPASS" and event == "enable" and t >= T_EV and V / 2 >= VW + H:   # 판단은 V_bat/2(히스테리시스 ±5 V)
                go("PREP", t)
            elif st == "PREP" and t - t_st >= t_prep:
                G = 0.; go("OPEN_WAIT", t)
            elif st == "OPEN_WAIT" and t - t_st >= t_wait:
                vref_fn = lambda tt, va0=va_m, t1=t: va0 + (VW - va0) * min((tt - t1) / RAMP, 1.)
                ctrl.vref_fn = vref_fn; ctrl.reset(x, np.array([0., 0.])); go("WINDOW", t)
            elif st == "WINDOW" and event == "disable" and t >= T_EV and t_det is None and V / 2 <= VW - H:
                vref_fn = lambda tt, v0=vref_fn(t), v1=va_m, t1=t: v0 + (v1 - v0) * min((tt - t1) / RAMP, 1.)
                ctrl.vref_fn = vref_fn; go("OFF_RAMP", t)
            elif st == "OFF_RAMP" and t - t_st >= RAMP:
                vref_fn = track; ctrl.vref_fn = vref_fn; gate_since = None; go("OFF_HOLD", t)
            elif st == "OFF_HOLD" and t - t_st >= HOLD and (gate_ok(t) or t - t_st >= T_GATE_MAX):
                gate_timeout = gate_timeout or not gate_ok(t); go("ZERO", t)
            elif st == "DAB_HOLD" and not loads400:
                vref_fn = (lambda tt, v0=vref_fn(t), v1=va_m, t1=t: v0 + (v1 - v0) * min((tt - t1) / RAMP, 1.))
                ctrl.vref_fn = vref_fn; go("DAB_RAMP", t)
            elif st == "DAB_RAMP" and t - t_st >= RAMP and vref_fn is not track:
                vref_fn = track; ctrl.vref_fn = vref_fn; gate_since = None
            elif st == "DAB_RAMP" and t - t_st >= RAMP + HOLD and (gate_ok(t) or t - t_st >= RAMP + T_GATE_MAX):
                gate_timeout = gate_timeout or not gate_ok(t); go("ZERO", t)
            elif st == "ZERO" and t - t_st >= ZERO:
                G = 1. / R_BYP; t_close = t; go("DEGRADED" if t_det is not None else "BYPASS", t)
            elif st == "HB_HOLD" and (shed_cmd is None or not loads400 or cur_ok):   # 분리가 끝났거나 필요 없으면 링크 붕괴
                if sc_pause and SL is not None:                     # (E38) Stage C 일시 정지(붕괴·소프트 투입 동안)
                    SL.sc_pause(t); events.append(("sc_pause", round(t * 1e3, 4)))
                aux.collapse(t, x[4]); go("HB_COLLAPSE", t)
            elif st == "HB_COLLAPSE" and (x[4] <= VL_SOFT or stalled or t - t_st >= T_COL_MAX):
                t_close = t
                soft_entry = dict(why="vl" if x[4] <= VL_SOFT else ("stall" if stalled else "timeout"), ms=round((t - T_EV) * 1e3, 4),
                                  vl=float(x[4]), vs=float(x[1]), ip=float(x[0]))
                if pol == "clamp_brk_hard":
                    G = 1. / R_BYP; t_deg = t; go("DEGRADED", t)
                else:
                    t_soft0 = t; r_soft = R_SOFT0; ip_soft0 = x[0]; G = 1. / r_soft; go("SOFT_BYP", t)
            elif st == "SOFT_BYP" and (r_soft <= R_BYP * (1 + 1e-9) or t - t_st >= T_SOFT_MAX):
                soft_timeout = r_soft > R_BYP * (1 + 1e-9)
                if soft_timeout and soft_fail:                     # (E20) 시간 상한이면 닫지 않고 이중 고장 처리(Stage A 협조 정지)
                    go("FAILSAFE", t)
                else:
                    G = 1. / R_BYP; t_deg = t; go("DEGRADED", t)
            # 소프트 투입(경로전류 조절): 제한 안이면 로그 램프(10 Ω → 3.3 mΩ, t_soft), 넘으면 저항을 되올린다
            if st == "SOFT_BYP" and t > t_soft0:
                r_soft = min(r_soft * K_UP, R_SOFT0) if x[0] > ip_soft0 + DI_SOFT else max(r_soft / k_dn, R_BYP)
                G = 1. / r_soft
            # SPS DAB 링크 쪽 전류 첨두(정보): DAB가 스위칭하는 상태에서
            if st in DAB_ON and not dab_dead:
                fault_st = st in ("HB_HOLD", "HB_COLLAPSE", "SOFT_BYP")
                if fault_st and sw:
                    pk = DM.sw_peak_A(x[2], x[4], icmd_aux, p)       # 지령 칸의 스위칭 반영 첨두(E21)
                else:
                    pk = DM.peak_A(x[2], x[4], x[5], p, "eps" if (fault_st and dmod == "eps") else "sps")
                if pk > dab_pk:
                    dab_pk, dab_pk_t, dab_pk_st = pk, t, st
                if st == "HB_HOLD":
                    dab_pk_hold = max(dab_pk_hold, pk)
                elif fault_st:
                    dab_pk_col = max(dab_pk_col, pk)
            # 지령
            steer = (st in ("PREP", "OPEN_WAIT") and prep == "steer") or (st == "ZERO" and close == "steer")
            if st in ("WINDOW", "OFF_RAMP", "OFF_HOLD", "DAB_HOLD", "DAB_RAMP"):
                ctrl.t = t; u = ctrl.step(x)
            elif steer:                                            # 전류 조향: 켬은 바이패스 전류 → 0, 끔은 직렬전압 → 0
                ihs = x[0] if st != "ZERO" else x[0] - p.Cs * x[1] / TAU_ST
                u = np.array([float(np.clip((x[1] + p.Rh * x[3] + p.Lh / p.inner_tau * (ihs - x[3])) / x[4], -.95, .95)), 0.])
            if st in ("HB_HOLD", "HB_COLLAPSE", "SOFT_BYP"):
                icmd_aux, vl_aux_ref = aux.step(x, t, V)
                if dmod == "eps":                                  # 첨두 상한을 지키는 전류만 지령(나머지는 제동 저항이 받음)
                    if sw:                                         # (E21) 회로 블록과 같이 링크 → 1차 쪽만, 스위칭 반영 첨두로 탐색
                        icmd_aux = float(np.clip(icmd_aux, -DM.sw_ilim(x[2], x[4], p, pkf * pk_rated), 0.))
                    else:
                        lim_e = DM.eps_ilim(x[2], x[4], p, pkf * pk_rated)
                        icmd_aux = float(np.clip(icmd_aux, -lim_e, lim_e))
            # 링크 제동 저항(선택): H-브리지 강등의 유지 중에는 링크 과전압 보호만(110 V 위에서 켬), 붕괴·소프트 투입 중에는
            # 링크 기준 + 5 V 위에서 켠다. DAB 고장에서는 110 V 위에서 켠다.
            # (2026-10-24 수정: 유지 중에도 기준 추종으로 켜면 링크가 너무 빨리 내려가 버스가 급히 올라 경로전류 첨두가 커졌다 —
            #  W410 920 V·25 kW 103 A. 유지 중 링크는 DAB 보조 루프만으로 내린다.)
            if brk and st == "HB_HOLD" and hold == "vw":
                Gb = 1. / R_BRK if x[4] > 110. else (0. if x[4] < 105. else Gb)
            elif brk and st == "HB_HOLD":                          # 전압비 정합 유지: DAB 정격 밖 전력을 제동 저항이 받음
                Gb = 1. / R_BRK if x[4] > vl_aux_ref + 5. else (0. if x[4] < vl_aux_ref + 2. else Gb)
            elif brk and st in ("HB_COLLAPSE", "SOFT_BYP"):
                Gb = 1. / R_BRK if x[4] > vl_aux_ref + 5. else (0. if x[4] < vl_aux_ref + 2. else Gb)
            elif brk and st in ("DAB_HOLD", "DAB_RAMP", "ZERO") and dab_dead:
                Gb = 1. / R_BRK if x[4] > 110. else (0. if x[4] < 105. else Gb)
            elif st == "FAILSAFE" and fs_brake:                     # (E29) 이중 고장에서도 링크 과전압 보호 유지
                Gb = 1. / R_BRK if x[4] > 110. else (0. if x[4] < 105. else Gb)
            else:
                Gb = 0.
        if st == "SOFT_BYP":
            e_soft += G * x[1] * x[1] * DT                        # 소프트 투입 소자(선형 영역)의 소비 에너지
        if SL is not None:                                         # (E29) 접촉기 = 400 V 부하 연결 상태, 되돌림은 SALS 메시지
            if t_cont is not None and loads400 and t - t_cont >= t_shed:
                loads400 = False; events.append(("shed_done", round(t * 1e3, 4)))
            if curtail_only and t_cont is None and t_deg is not None and not restored and t - t_deg >= T_RESTORE:
                SL.restore(t); restored = True; events.append(("restore", round(t * 1e3, 4)))
            if sc_pause and SL.t_pause is not None and SL.t_resume is None and t_deg is not None and t - t_deg >= T_RESTORE:
                SL.sc_resume(t); events.append(("sc_resume", round(t * 1e3, 4)))   # (E38) Stage C 재개
        else:
            if shed_cmd is not None and loads400 and t - shed_cmd >= t_shed and not (curtail_only and t_deg is not None):
                loads400 = False; events.append(("shed_done", round(t * 1e3, 4)))
            if curtail_only and t_deg is not None and not loads400 and t - t_deg >= T_RESTORE:
                loads400 = True; events.append(("restore", round(t * 1e3, 4)))   # 일시 감발 해제(버스 = V_A ≤ 상한)
        # ---- 적용(전달지연 버퍼) --------------------------------------------------------------------
        buf[tick] = u; applied = buf[(tick + 1) % len(buf)].copy(); tick = (tick + 1) % len(buf)
        if event in ("m_pos", "m_neg") and t >= T_EV:
            applied[0] = .95 if event == "m_pos" else -.95
        if bridge_dead or st not in SWITCHING:
            bridge = "off"
        elif st in ("PREP", "OPEN_WAIT", "ZERO"):
            bridge = "pwm" if steer else "zero"
        else:
            bridge = "pwm"
        if dab_dead:
            icmd = 0.
        elif st in ("HB_HOLD", "HB_COLLAPSE", "SOFT_BYP"):
            icmd = DM.sw_current(x[2], x[4], icmd_aux, p) if sw else icmd_aux   # (E21) 데드타임으로 바뀐 실제 링크전류
            if dab_lowv:
                icmd *= min(1., max(x[4], 0.) / dab_lowv)
        elif st in ("WINDOW", "OFF_RAMP", "OFF_HOLD") and not bridge_dead:
            icmd = applied[1]
        else:
            icmd = 0.
        if SL is not None:                                         # (E29) 등급별 계약 응답(5 µs 표본마다 갱신)
            if k % sample == 0 or Pl_s is None:
                Pl_s = SL.power(t, loads400)
            Pl = Pl_s
        else:
            Pl = (P if loads400 else min(P, p_c))
        if x[2] < LOAD_MIN_V - 10:
            Pl = 0.                                                # 저전압 차단
        dz = diode(x, vd) if bridge == "off" else None
        ih0 = x[3]
        vsrc = VA
        if t_as is not None and t >= t_as:                         # (E29) Stage A 정지: V_A 노드 = C_A, 경로전류로 방전
            i_dis = 0.
            if astop.get("R_dis"):                                 # (E37) 방전 저항(V_A와 버스를 재서 켜고 끔)
                if not dis_on and vA > x[2] - astop.get("dv_on", 60.):
                    dis_on = True; n_dis += 1
                elif dis_on and vA < x[2] - astop.get("dv_off", 65.):
                    dis_on = False
                if dis_on:
                    i_dis = vA / astop["R_dis"]
                    E_dis += vA * i_dis * DT; P_dis_pk = max(P_dis_pk, vA * i_dis); I_dis_pk = max(I_dis_pk, i_dis)
            vA = max(vA - (x[0] + i_dis) * DT / astop["C_A"], 0.); vsrc = vA
        d1 = deriv_r2(x, applied[0], bridge, icmd, G, vsrc, Pl, p, dz, vd, Gb)
        x = x + DT * deriv_r2(x + .5 * DT * d1, applied[0], bridge, icmd, G, vsrc, Pl, p, dz, vd, Gb)
        if bridge == "off" and (ih0 == 0. or ih0 * x[3] < 0.) and not abs(x[1]) > x[4] + 2 * vd:
            x[3] = 0.
        if loads400 and x[2] > upper and t_over is None and t >= T_EV:
            t_over = t
        log[k] = [*x[:6], -G * x[1], float(loads400), {"pwm": 0, "zero": 1, "off": 2}[bridge], Gb * x[4] * x[4]]
        if not np.isfinite(x).all():
            log = log[:k + 1]; break
    tt = (np.arange(len(log)) + 1) * DT
    post = tt >= (T_EV if event != "enable" else 0.)
    L = log[post]; Lw = log[post & (log[:, 7] > .5)]
    ib = log[:, 6]
    m = dict(case=case, V=V, P=P, event=event, policy=pol if event in ("hb_open", "m_pos", "m_neg", "dab") else "-",
             prep=prep if event == "enable" else "-", t_prep_ms=t_prep * 1e3, close=close if event in ("disable", "dab") else "-",
             start_share=bool(job.get("start_share")), tag=job.get("tag"), damper=bool(damper), vd=vd, t_soft_us=t_soft * 1e6, t_shed_ms=t_shed * 1e3, wait_ms=t_wait * 1e3,
             events=events, det_src=det_src, det_ms=None if t_det is None else round((t_det - T_EV) * 1e3, 4),
             final_state=st, path_peak=float(np.abs(L[:, 0]).max()), bridge_peak=float(np.abs(L[:, 3]).max()),
             series_peak=float(np.abs(L[:, 1]).max()), vlink_max=float(L[:, 4].max()), vlink_min=float(L[:, 4].min()),
             vbus_min=float(L[:, 2].min()), vbus_max=float(L[:, 2].max()),
             vbus_max_loaded=float(Lw[:, 2].max()) if len(Lw) else None, vbus_end=float(log[-1, 2]),
             byp_peak=float(np.abs(ib[post]).max()), t_over_ms=None if t_over is None else round((t_over - T_EV) * 1e3, 3),
             shed_needed=shed_cmd is not None, gate_timeout=gate_timeout,
             fault_path_peak=float(np.abs(log[(tt >= T_EV) & (tt <= T_EV + 3e-3), 0]).max()) if event != "enable" else None,
             fault_bridge_peak=float(np.abs(log[(tt >= T_EV) & (tt <= T_EV + 3e-3), 3]).max()) if event != "enable" else None,
             fault_bus_min=float(log[(tt >= T_EV) & (tt <= T_EV + 3e-3), 2].min()) if event != "enable" else None, brk_energy_J=float(log[:, 9].sum() * DT), brk_peak_kW=float(log[:, 9].max() / 1e3))
    rated_pk = dab_sps_peak(VW, 100., p.power_max / 100., p)      # 정격(4·5 kW, 링크 100 V)에서의 첨두
    m.update(dab_sec_peak=dab_pk, dab_prim_peak=dab_pk / p.turns, dab_peak_ms=None if dab_pk_t is None else round((dab_pk_t - T_EV) * 1e3, 4),
             dab_peak_state=dab_pk_st, dab_rated_sec_peak=rated_pk, dab_peak_ratio=dab_pk / rated_pk,
             soft_entry=soft_entry, soft_timeout=soft_timeout, soft_energy_J=e_soft,
             soft_ms=None if (t_soft0 is None or t_deg is None) else round((t_deg - t_soft0) * 1e3, 4),
             hold=hold, curtail=curtail, dmod=dmod, soft_fail=soft_fail, dab_peak_hold=dab_pk_hold, dab_peak_collapse=dab_pk_col,
             dab_peak_limit=pkf * pk_rated)
    if "p_c" in job:
        m["p_c"] = p_c
    if SL is not None or ev2 is not None or astop is not None:      # (E29) 연동 기록
        m.update(sals=None if SL is None else SL.describe(), t_cont_ms=None if t_cont is None else round((t_cont - T_EV) * 1e3, 4),
                 restored=restored, t_astop_ms=None if t_as is None else round((t_as - T_EV) * 1e3, 4),
                 vA_end=None if t_as is None else float(vA), fs_brake=fs_brake)
        if astop is not None and astop.get("R_dis"):
            m.update(dis_E_J=E_dis, dis_P_pk_W=P_dis_pk, dis_I_pk_A=I_dis_pk, dis_n_on=n_dis)
        if sc_pause or ls_ramp:                                    # (E38)
            ms = lambda v: None if v is None else round((v - T_EV) * 1e3, 4)
            m.update(sc_pause=sc_pause, load_stop=ls_ramp, sc_pause_ms=ms(SL.t_pause), sc_resume_ms=ms(SL.t_resume),
                     load_stop_ms=ms(SL.t_stop))
    if t_close is not None:                                        # 바이패스 투입 순간(소프트 투입 포함) + 50 µs
        w = (tt >= t_close) & (tt <= (t_deg if t_deg is not None else t_close) + 50e-6)
        m.update(close_ms=round((t_close - T_EV) * 1e3, 4), vs_at_close=float(log[np.searchsorted(tt, t_close), 1]),
                 byp_pulse_A=float(np.abs(ib[w]).max()), byp_pulse_mJ=float(np.sum(np.abs(log[w, 1] * ib[w])) * DT * 1e3),
                 path_close_peak=float(np.abs(log[w, 0]).max()))
    if event == "enable":
        t_open = [e[1] for e in events if e[0] == "OPEN_WAIT"]
        t_win = [e[1] for e in events if e[0] == "WINDOW"]
        if t_open:
            w = (tt >= t_open[0] * 1e-3) & (tt <= (t_win[0] if t_win else t_open[0] + .2) * 1e-3 + 1e-12)
            m.update(open_ip_range=[float(log[w, 0].min()), float(log[w, 0].max())],
                     open_vs_range=[float(log[w, 1].min()), float(log[w, 1].max())], open_vbus_max=float(log[w, 2].max()))
            x0w = log[w, 0] - log[w, 0].mean(); tw = tt[w]
            zc = tw[np.flatnonzero(x0w[:-1] * x0w[1:] < 0) + 1]
            m["open_ring_kHz"] = float(1e-3 / (2 * np.mean(np.diff(zc)))) if len(zc) >= 3 else None
            wa = (tt >= t_open[0] * 1e-3) & (tt <= t_open[0] * 1e-3 + .5e-3)       # 열림 뒤 0.5 ms(제어 시작 포함)
            m["open_path_peak_0p5ms"] = float(np.abs(log[wa, 0]).max())
        tr_end = (t_win[0] * 1e-3 + RAMP) if t_win else tt[-1]
        out = np.flatnonzero((tt >= tr_end) & (np.abs(log[:, 2] - VW) > 4.))
        m["settle_after_ramp_ms"] = float((tt[out[-1]] - tr_end) * 1e3) if len(out) else 0.
        m["checks"] = dict(current_90A=max(m["path_peak"], m["bridge_peak"]) <= 90., series_90V=m["series_peak"] <= 90.,
                           link_band=m["vlink_min"] >= 90. and m["vlink_max"] <= 110., class_upper=m["vbus_max"] <= upper,
                           bypass_current=m["byp_peak"] <= I_BYP_LIM, settle_10ms=m["settle_after_ramp_ms"] <= 10.,
                           final=abs(m["vbus_end"] - VW) <= 4.)
    elif event == "disable":
        m["checks"] = dict(current_90A=max(m["path_peak"], m["bridge_peak"]) <= 90., series_90V=m["series_peak"] <= 90.,
                           link_band=m["vlink_min"] >= 90. and m["vlink_max"] <= 110., bypass_current=m["byp_peak"] <= I_BYP_LIM,
                           bus_ge_260=m["vbus_min"] >= LOAD_MIN_V, reached_bypass=st == "BYPASS", class_upper=m["vbus_max"] <= upper)
    else:
        m["checks"] = dict(current_100A=max(m["path_peak"], m["bridge_peak"]) <= 100., series_120V=m["series_peak"] <= 120.,
                           link_120V=m["vlink_max"] <= 120., bypass_current=m["byp_peak"] <= I_BYP_LIM,
                           bus_ge_260=m["vbus_min"] >= LOAD_MIN_V, degraded_reached=st == "DEGRADED",
                           class_upper_while_400V_loads=(m["vbus_max_loaded"] or 0.) <= upper)
    m["pass_"] = bool(all(m["checks"].values()))
    if job.get("keep"):
        m["trace"] = dict(t=tt[::10], log=log[::10])
    return m


R2_V = {"W460_240s": [930., 1008.], "W410_spec": [860., 920.]}


def r2_jobs():
    js = [dict(case="W460_240s", V=930., P=25000., event="enable", start_share=True, damper=False, tag="TB08 대조")]
    for case, c in E19.CASES.items():
        for P in (5000., 25000.):
            for prep, w in (("zero", T_WAIT), ("zero", 0.), ("steer", 0.)):
                js.append(dict(case=case, V=2 * (c["VW"] + H), P=P, event="enable", prep=prep, wait=w))
            for cl in ("zero", "steer"):
                js.append(dict(case=case, V=2 * (c["VW"] - H), P=P, event="disable", close=cl))
            for V in R2_V[case]:
                for pol, cl in (("ramp", "zero"), ("brk_hold", "zero"), ("brk_hold", "steer")):
                    js.append(dict(case=case, V=V, P=P, event="dab", policy=pol, close=cl))
                for pol in ("now", "collapse_now", "clamp", "clamp_brk", "clamp_brk_hard"):
                    js.append(dict(case=case, V=V, P=P, event="hb_open", policy=pol))
                for ev in ("m_pos", "m_neg"):
                    js.append(dict(case=case, V=V, P=P, event=ev, policy="clamp_brk"))
    # 감도(최대 전압·25 kW): 감쇠기 없음(E19·TB08과 같은 플랜트), 다이오드 전압, 소프트 투입 시간, 부하 분리 시간
    for case in E19.CASES:
        V = R2_V[case][-1]
        js.append(dict(case=case, V=V, P=25000., event="hb_open", policy="clamp_brk", damper=False, tag="감쇠기 없음"))
        js.append(dict(case=case, V=V, P=25000., event="dab", policy="brk_hold", damper=False, tag="감쇠기 없음"))
        for vd in (1.4, 3.0):
            js.append(dict(case=case, V=V, P=25000., event="hb_open", policy="clamp_brk", vd=vd, tag="V_D %.1f V" % vd))
        js.append(dict(case=case, V=V, P=25000., event="hb_open", policy="clamp_brk", t_soft=.1e-3, tag="소프트 0.1 ms"))
        js.append(dict(case=case, V=V, P=25000., event="hb_open", policy="clamp_brk", t_shed=50e-3, tag="분리 50 ms"))
        for V2 in R2_V[case]:                                         # 회로(TB09)에서 본 붕괴 정체를 모사: 링크 10 V 아래 DAB 전달 저하
            js.append(dict(case=case, V=V2, P=25000., event="hb_open", policy="clamp_brk", dab_lowv=10., tag="DAB 저링크 저하 10 V"))
    return js


def r2():
    js = r2_jobs()
    t0 = time.time()
    with Pool(workers()) as pool:
        rows = pool.map(r2_run, js, chunksize=1)
    print("  r2: %d건, %.0f s" % (len(rows), time.time() - t0))
    groups = {}
    for r in rows:
        k = "%s|%s|%s" % (r["case"], r["event"], r["policy"])
        if r["event"] == "enable":
            k += "|%s|대기 %.1f ms" % (r["prep"], r["wait_ms"])
        if r["event"] in ("disable", "dab"):
            k += "|%s" % r["close"]
        if r.get("tag"):
            k += "|" + r["tag"]
        g = groups.setdefault(k, dict(n=0, passed=0, path=0., bridge=0., series=0., link=0., bus_max=0., bus_max_loaded=0.,
                                      byp=0., byp_mJ=0., dab_pk=0., soft_J=0., det_ms=[], t_over_ms=[], fails={}))
        g["n"] += 1; g["passed"] += int(r["pass_"])
        for a, b in (("path", "path_peak"), ("bridge", "bridge_peak"), ("series", "series_peak"), ("link", "vlink_max"),
                     ("bus_max", "vbus_max"), ("byp", "byp_peak"), ("byp_mJ", "byp_pulse_mJ"),
                     ("dab_pk", "dab_sec_peak"), ("soft_J", "soft_energy_J")):
            g[a] = max(g[a], r.get(b) or 0.)
        g["bus_max_loaded"] = max(g["bus_max_loaded"], r["vbus_max_loaded"] or 0.)
        if r["det_ms"] is not None:
            g["det_ms"].append(r["det_ms"])
        if r["t_over_ms"] is not None:
            g["t_over_ms"].append(r["t_over_ms"])
        for cname, ok in r["checks"].items():
            if not ok:
                g["fails"].setdefault(cname, []).append((r["V"], r["P"]))
    for k, g in groups.items():
        print("  %-52s %2d/%2d, 경로 %.0f·필터 %.0f A, 바이패스 %.0f A(%.2f mJ, 소프트 %.3f J), DAB 2차 첨두 %.0f A, 직렬 %.0f V, 링크 %.0f V, 버스 최대 %.0f V(부하 연결 중 %.0f V)%s%s%s"
              % (k, g["passed"], g["n"], g["path"], g["bridge"], g["byp"], g["byp_mJ"], g["soft_J"], g["dab_pk"], g["series"], g["link"], g["bus_max"],
                 g["bus_max_loaded"], (", 검출 %.3f–%.3f ms" % (min(g["det_ms"]), max(g["det_ms"]))) if g["det_ms"] else "",
                 (", 상한 초과 %.2f ms" % min(g["t_over_ms"])) if g["t_over_ms"] else "",
                 ("  실패 " + str({c: len(v) for c, v in g["fails"].items()})) if g["fails"] else ""))
    save_json(EID, "r2", dict(groups=groups, rows=rows, settings=dict(
        R_BYP=R_BYP, VD=VD, I_BYP_LIM=I_BYP_LIM, R_SOFT0=R_SOFT0, T_SOFT=T_SOFT, P_C=P_C, T_SHED=T_SHED, RATE_COL=RATE_COL, T_COL_MAX=T_COL_MAX, TAU_ST=TAU_ST,
        VL_SOFT=VL_SOFT, T_PREP=T_PREP, T_WAIT=T_WAIT, RAMP=RAMP, HOLD=HOLD, ZERO=ZERO, VS_GATE=VS_GATE, T_GATE=T_GATE, T_GATE_MAX=T_GATE_MAX, I_HW=I_HW, VL_HW=VL_HW, VS_HW=VS_HW,
        T_HW=T_HW, VL_SW=VL_SW, T_SW=T_SW, VB_SW=VB_SW, T_VB=T_VB, T_GDF=T_GDF, KP_B=KP_B, KI_B=KI_B, QB_MAX=QB_MAX, W_L=W_L, R_BRK=R_BRK, R_DMP=R_DMP, C_DMP=C_DMP,
        VL_STALL=VL_STALL, T_STALL=T_STALL, DV_STALL=DV_STALL, DI_SOFT=DI_SOFT, K_UP=K_UP, T_SOFT_MAX=T_SOFT_MAX)))
    return groups


def figures():
    """E17 그림: (1) H-브리지 차단 강등(클램프 유지 + 제동 저항 → 링크 붕괴 → 소프트 바이패스), (2) 켬 전환·DAB 고장."""
    import os
    from plotstyle import korean, COLOR as C
    plt = korean()
    case = "W460_240s"; c = E19.CASES[case]
    # ---- (1) H-브리지 차단, 1008 V·25 kW -----------------------------------------------------------------
    m = r2_run(dict(case=case, V=1008., P=25000., event="hb_open", policy="clamp_brk", keep=True))
    t = m["trace"]["t"] * 1e3; L = m["trace"]["log"]
    ev = dict((e[0], e[1]) for e in m["events"])
    fig, ax = plt.subplots(2, 2, figsize=(13, 6.6), sharex="col")
    for col, (a, b) in enumerate(((0.3, 3.0), (ev["HB_COLLAPSE"] - .3, ev["DEGRADED"] + .8))):
        w = (t >= a) & (t <= b)
        A = ax[0, col]
        A.plot(t[w], L[w, 2], color=C["blue"], label="버스 v_bus")
        A.axhline(c["upper"], color=C["red"], ls="--", lw=.8); A.text(a + .02 * (b - a), c["upper"] + 3, "B_470 상한(400 V 부하 연결 중)", fontsize=7, color=C["red"])
        A.axhline(1008. / 2, color=C["gray"], ls=":", lw=.8); A.text(a + .02 * (b - a), 504 + 3, "V_A", fontsize=7, color=C["gray"])
        A2 = A.twinx(); A2.grid(False)
        A2.plot(t[w], -L[w, 1], color=C["orange"], lw=1., label="−직렬전압 −v_s")
        A2.plot(t[w], L[w, 4], color=C["green"], lw=1., label="링크 v_link")
        A.set_ylim(360, 530); A2.set_ylim(0, 140)
        A.set_ylabel("버스 [V]"); A2.set_ylabel("[V]")
        h1, l1 = A.get_legend_handles_labels(); h2, l2 = A2.get_legend_handles_labels()
        A.legend(h1 + h2, l1 + l2, fontsize=7, loc="lower right")
        B = ax[1, col]
        B.plot(t[w], L[w, 0], color=C["blue"], lw=1., label="경로전류 i_p")
        B.plot(t[w], L[w, 3], color=C["orange"], lw=1., label="필터전류 i_h(다이오드 정류)")
        B.plot(t[w], L[w, 6], color="#7030a0", lw=1.2, label="바이패스 전류")
        B.plot(t[w], L[w, 9] / 100., color=C["green"], lw=.8, label="제동 저항 전력/100 [W]")
        B.axhline(100, color=C["red"], ls="--", lw=.8)
        B.set_xlabel("시간 [ms]"); B.set_ylabel("[A]"); B.set_ylim(-30, 120); B.legend(fontsize=7, loc="upper right", ncol=2)
    ax[0, 0].set_title("(a) H-브리지 차단 직후: 다이오드 클램프 유지(DAB가 링크를 낮춰 버스를 상한 아래로, 제동은 과전압 보호만)", fontsize=9)
    ax[0, 1].set_title("(b) 400 V 부하 분리(20 ms) 뒤: 링크 붕괴 20 V/ms → 소프트 바이패스(경로전류 조절)", fontsize=9)
    fig.suptitle("E17 R2-W460, V_bat 1008 V, 25 kW: H-브리지 개방 고장의 강등(버스 RC 감쇠기 포함)", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(outdir(EID), "E17_r2_hbridge_fault.png"), dpi=150); plt.close(fig)
    # ---- (2) 켬 전환(TB08 대조, 전류 조향)과 DAB 고장 ----------------------------------------------------------
    fig, ax = plt.subplots(1, 3, figsize=(15, 3.9))
    tb = os.path.join(os.path.dirname(__file__), "..", "..", "..", "simulink", "tb", "TB08_R2_WindowModule", "results",
                      "TB08_zoom_E_930V_enable_25kW.csv")
    m = r2_run(dict(case=case, V=930., P=25000., event="enable", start_share=True, damper=False, keep=True))
    t = m["trace"]["t"] * 1e3; L = m["trace"]["log"]; w = (t >= .45) & (t <= 1.2)
    if os.path.exists(tb):
        Z = np.loadtxt(tb, delimiter=","); zt = Z[:, 0] * 1e3 + .5
        ax[0].plot(zt[::20], Z[::20, 2], color=C["gray"], lw=1.6, label="회로(TB08, 순시)")
    ax[0].plot(t[w], L[w, 0], color=C["blue"], lw=1., ls="--", label="E17 모델(바이패스 3.3 mΩ)")
    ax[0].axvline(.5, color=C["gray"], lw=.8, ls=":"); ax[0].axvline(.7, color=C["gray"], lw=.8, ls=":")
    ax[0].text(.51, 22, "바이패스 열림", fontsize=7); ax[0].text(.71, 22, "제어 시작", fontsize=7)
    ax[0].set_xlim(.45, .72); ax[0].set_ylim(20, 80)
    ax[0].set_xlabel("시간 [ms]"); ax[0].set_ylabel("경로전류 [A]"); ax[0].legend(fontsize=7, loc="upper left")
    ax[0].set_title("(a) 켬, 930 V·25 kW: 바이패스 열림 과도, 회로와 모델 대조")
    for prep, wt, col, lab in (("zero", T_WAIT, C["orange"], "영벡터 분담 → 열림 → 0.2 ms 뒤 제어(TB08 순서)"),
                               ("steer", 0., C["blue"], "전류 조향(바이패스 전류 → 0) → 열림 → 바로 제어")):
        m = r2_run(dict(case=case, V=930., P=25000., event="enable", prep=prep, wait=wt, keep=True))
        t = m["trace"]["t"] * 1e3; L = m["trace"]["log"]
        ax[1].plot(t, L[:, 0], color=col, lw=1., label=lab)
    ax[1].axhline(90, color=C["red"], ls="--", lw=.8)
    ax[1].set_xlim(.8, 2.5); ax[1].set_ylim(0, 100); ax[1].set_xlabel("시간 [ms]"); ax[1].set_ylabel("경로전류 [A]")
    ax[1].legend(fontsize=7, loc="lower right"); ax[1].set_title("(b) 켬 순서 비교(감쇠기 포함): 열림 전 바이패스 전류를 0으로")
    for pol, col, lab in (("ramp", C["orange"], "검출 즉시 V_A로 램프(E19 순서)"), ("brk_hold", C["blue"], "제동 저항으로 유지 → 분리 뒤 램프")):
        m = r2_run(dict(case=case, V=1008., P=25000., event="dab", policy=pol, keep=True, t_shed=3e-3, duration=T_EV + 8e-3))
        t = m["trace"]["t"] * 1e3; L = m["trace"]["log"]
        ax[2].plot(t, L[:, 4], color=col, lw=1., label=lab + ": 링크")
    ax[2].axhline(VL_HW, color=C["red"], ls="--", lw=.8); ax[2].text(.2, VL_HW + 1, "링크 과전압 비교기 115 V", fontsize=7, color=C["red"])
    ax[2].set_xlim(0, 8); ax[2].set_ylim(95, 125); ax[2].set_xlabel("시간 [ms]"); ax[2].set_ylabel("링크 [V]")
    ax[2].legend(fontsize=7, loc="lower right"); ax[2].set_title("(c) DAB 고장, 1008 V·25 kW(그림은 분리 3 ms)")
    fig.tight_layout(); fig.savefig(os.path.join(outdir(EID), "E17_r2_transitions.png"), dpi=150); plt.close(fig)
    # ---- (3) DAB 전압비 불일치의 순시 전류(SPS 해석)와 회로(TB09) 측정 ---------------------------------------------
    p, _ = E19.plant(case)
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.2))
    vls = np.linspace(0., 110., 221)
    for vb, idab, col, ls in ((460., 0., C["blue"], "-"), (460., -40., C["blue"], "--"), (504., 0., C["orange"], "-"), (504., -40., C["orange"], "--")):
        ax[0].plot(vls, [dab_sps_peak(vb, v, idab, p) for v in vls], color=col, ls=ls, lw=1.2,
                   label="버스 %.0f V, 링크전류 %.0f A" % (vb, idab))
    rated = dab_sps_peak(c["VW"], 100., p.power_max / 100., p)
    for y, txt, col in ((rated, "정격점(4 kW, 링크 100 V) %.0f A" % rated, C["green"]), (164.5, "EPC2305 펄스 정격 329 A의 50 %", C["red"]),
                        (329., "EPC2305 펄스 정격(25 °C, 300 µs)", C["gray"])):
        ax[0].axhline(y, color=col, ls=":", lw=.9); ax[0].text(2, y + 4, txt, fontsize=7, color=col)
    ax[0].set_xlabel("링크전압 v_link [V]"); ax[0].set_ylabel("DAB 링크 쪽 순시 첨두 [A]"); ax[0].set_ylim(0, 350)
    ax[0].set_title("(a) SPS DAB(4.6:1, 14.68 µH, 200 kHz): 링크전압이 n·v_link < v_bus로 내려갈수록 순환전류가 커진다", fontsize=8.5)
    ax[0].legend(fontsize=7, loc="upper right")
    m = r2_run(dict(case=case, V=1008., P=25000., event="hb_open", policy="clamp_brk", t_shed=3e-3, keep=True))
    t = m["trace"]["t"]; L = m["trace"]["log"]; ev = dict((e[0], e[1]) for e in m["events"])
    on = t * 1e3 < ev["DEGRADED"] + T_EV * 1e3
    pk = np.array([dab_sps_peak(L[i, 2], L[i, 4], L[i, 5], p) if on[i] else np.nan for i in range(len(t))])
    ax[1].plot(t * 1e3, pk, color=C["blue"], lw=1.2, label="E17 평균 궤적의 SPS 해석 첨두")
    tbp = os.path.join(os.path.dirname(__file__), "..", "..", "..", "simulink", "tb", "TB09_R2_Protection", "results",
                       "TB09_A_1008V_hbopen_25kW_periods.csv")
    if os.path.exists(tbp):
        Z = np.loadtxt(tbp, delimiter=","); zs = Z[:, 15]
        zpk = p.turns * Z[:, 13]; zpk[~np.isin(np.round(zs), [3, 4, 5, 9, 10, 11])] = np.nan
        ax[1].plot(Z[:, 0] * 1e3, zpk, color=C["gray"], lw=1., label="회로 TB09: n·max|i_L| (5 µs마다)")
    A2 = ax[1].twinx(); A2.grid(False); A2.plot(t * 1e3, L[:, 4], color=C["green"], lw=.9, label="링크 v_link(E17)"); A2.set_ylabel("v_link [V]")
    ax[1].axhline(rated, color=C["green"], ls=":", lw=.9); ax[1].axhline(164.5, color=C["red"], ls=":", lw=.9)
    ax[1].set_xlabel("시간 [ms]"); ax[1].set_ylabel("DAB 링크 쪽 순시 첨두 [A]"); ax[1].set_ylim(0, 230); A2.set_ylim(0, 115)
    ax[1].set_xlim(0, ev["DEGRADED"] + T_EV * 1e3 + 2.)
    ax[1].set_title("(b) 1008 V·25 kW H-브리지 개방(분리 3 ms): 클램프 유지 → 붕괴 → 소프트 투입", fontsize=8.5)
    h1, l1 = ax[1].get_legend_handles_labels(); h2, l2 = A2.get_legend_handles_labels(); ax[1].legend(h1 + h2, l1 + l2, fontsize=7, loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(outdir(EID), "E17_r2_dab_stress.png"), dpi=150); plt.close(fig)
    print("  figures saved")


PARTS = dict(monitor=monitor, r2=r2, figures=figures)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E17 %s ====" % w, flush=True)
        PARTS[w]()
