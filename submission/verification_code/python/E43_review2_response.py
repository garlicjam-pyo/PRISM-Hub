"""[E43] 외부 검토(2026-11-05) 대응: R2 창 조정 모듈의 측정 사양(S), 손실 민감도의 일관된 스위칭 배율(L),
V_A 클램프 저항 자기 가열 가정(H), Stage C 일시 정지 동안의 48 V 배터리(B).

■ 왜 필요한가(외부 검토 2026-11-05. 사용자 결정 2026-11-05: 재계산 + 문구 수정)
  (S) 요구사항 표의 센서·ADC(16비트, 버스 350–450 V 차동)는 처음 구조 ③(버스 400 V 정밀 조정, E12)의 값이다. 최종 구조의 창 조정
      모듈 R2-W460은 버스를 460 V로 조정하고, 강등 뒤 버스는 V_A(최대 504 V)다. 창 조정 검증(E19 평균모델, TB08 회로)은 이상 측정으로
      했고, 스위칭 모델의 센서 함수는 범위를 양자화 간격으로만 써서 포화가 없었다(검토 직접 호출: 460 V → 460.0006 V).
      R2의 측정 사양을 새로 정하고, 포화를 넣은 센서로 창 조정 전압 품질과 보호 오동작을 다시 판정한다.
  (L) E41·E42 민감도의 '스위칭 에너지 × 0.7·× 1.5'(K["esw"])는 다른 구조의 스위칭 손실(출력용량 항 포함, E15 hs_converter)에는
      곱해지지만, Stage A 손실표(위상당 손실 보간)에 들어 있는 출력용량 하드 스위칭 항 4·Q_oss(V/2)·(V/2)·f_s에는 곱해지지 않았다
      (검토 직접 확인: 800 V·10 A Stage A 손실이 배율 0–1.5에서 같음). 이 항에도 같은 배율을 주어 다시 계산한다.
  (H) R2-W460 클램프의 문턱 +1 %(요구 정확도의 끝)에서 가지 에너지 3,763.5 J가 저항 자기 가열 가정 3,750 J를 넘는다(E40 thr).
      자기 가열 가정이 문턱 정확도 범위 전체의 최대 에너지를 덮도록 갱신하고 다시 판정한다.
  (B) 최종 보호 순서는 H-브리지 고장 강등의 링크 붕괴·소프트 투입 동안 Stage C를 최대 12.4 ms 멈춘다(E38). 그동안 48 V는
      48 V 배터리가 맡는다고 두었으나 배터리는 그 계산과 회로(TB31)에 없다. 배터리 등가로 48 V 전압을 계산하고 요구를 도출한다.

■ 판정 기준(실행 전에 고정, 이 커밋. 결과를 본 뒤 바꾸지 않는다)
 (S) 측정 사양
  후보 S1: Stage B 측정 채널 6개(i_p, v_s, v_bus, i_h, v_link, i_link), 16비트, 포화 있음. 범위 ±150 A, ±100 V, 버스 0–600 V(단일 채널),
      ±150 A, 0–150 V, ±150 A. 잡음 표준편차 20 mA, 5 mV, 버스 10 mV, 20 mA, 5 mV, 20 mA. 이득 오차는 E12와 같다(1 %, 0.5 %, 0.25 %,
      1 %, 0.5 %, 1 %). 오프셋도 E12와 같되 버스만 1.2 V(E12 0.2 V/100 V 창과 같은 전 범위의 0.2 %).
  경우: E19 창 조정 사례 두 개(R2-W460: 930·960·1008 V, R2-W410: 830·860·920 V) × 매개변수 두 벌(공칭, 지연 +3.0 µs)
      × Tier-1 10계단 + Tier-2 2계단 = 144건. 센서 변형 네 가지: 이상(기준), S1 잡음·양자화, S1 + 오차(전류 낮게·전압 높게),
      S1 + 오차(전류 높게·전압 낮게). 모델: Stage B 스위칭 모델(E12 채택 설정, model_stage_b_switching), 플랜트·제어기 = E19.plant(사례).
  판정(각 건, 실제 값): E12 스위칭 판정을 V_W로 옮긴 것.
      Tier-1: 완료, 포트 한계(DAB 전력 ≤ P_r 포함), |v_bus − V_W| ≤ 8 V, 회복(±4 V 안) ≤ 1 ms, 최종 ±4 V, 마지막 1 ms 리플 ≤ 0.1 V,
              내부 꼬리 진동(i_h ≤ 1 A_pp, 변조율 ≤ 0.01), 순시 경로·브리지 ≤ 98 A.
      Tier-2: 완료, 포트 한계, 버스 [V_W − 16, min(V_W + 16, 상한)], 최종 ±4 V, 순시 ≤ 100 A, 내부 꼬리 진동.
      둘 다: 버스 최대(모든 시각) ≤ 부품 등급 상한(420·470 V).
  보호 오동작(각 건, 그 변형의 버스 오차 g·o·σ로 계산. 이상 변형은 0):
      (P1) 하드웨어 버스 과전압 비교기(정상 조정 상태, 문턱 = 상한, E17): max_t((1 + g)·v_bus + o) + 3σ + 0.1 V(제어 주기 안 리플
           여유) ≤ 상한.
      (P2) 버스 조정 상실(|v_meas − V_W| > 20 V가 0.5 ms 지속, E17): |(1 + g)·v_bus + o − V_W| + 3σ > 20 V인 연속 구간 < 0.5 ms.
  범위 (C): 측정 범위 상한 600 V ≥ 1.1 × max(이 시험 (H)의 요구 정확도 안 C1, 정상 최대 V_bat,max/2 = 504 V).
  채택 규칙: 이상 변형에서 통과한 건이 S1 세 변형에서 모두 통과하고, S1의 (P1)(P2)가 모든 건에서 통과하고, (C)가 통과하면 S1을
      R2 측정 사양으로 채택한다. 이상 변형의 불통과는 센서와 무관한 새 결과로 따로 보고한다.
      S1이 안 되면 후보 S2(조정용 버스 채널 = V_W ± 50 V 차동 창, 16비트, 잡음 5 mV, 이득 0.25 %, 오프셋 0.2 V, 포화. 보호용 넓은 채널
      = S1 버스 채널)로 같은 144건을 세 변형으로 다시 판정한다((P1)(P2)는 넓은 채널로). S2도 안 되면 미해결로 보고한다.
 (L) 손실 민감도
  Stage A 손실표(E41: A25R 사양 격자 E36._T_spec, E42: 확장 격자 E36._ext_model)의 위상당 손실 P(V, I)에
      (esw − 1)·4·Q_oss,위치(V/2)·(V/2)·f_r0를 더한다(E32 설계, model_stage_a.qoss_pos, 공칭 공진주파수). 1위상 운전은 drive가
      위상 수만큼 곱한다. 충전 경로 표는 바꾸지 않는다(민감도 대상 아님).
  다시 계산하는 경우: 스위칭 × 0.7·× 1.5(E41 run과 E42 run_cases의 해당 경우). 나머지 경우는 E41·E42 저장값을 쓴다.
  확인: (R1) E43 파이프라인으로 계산한 기존 방식(Stage A 배율 없음)의 스위칭 × 0.7·× 1.5가 E41 저장값(세 프로파일 ④⑤⑥)과
      E42 cases 저장값(모든 팩·구조)과 차 ≤ 1e-6 W. 통과하지 않으면 구현 오류로 보고 고친 뒤 다시 실행한다(1차 결과를 남긴다).
  결과 규칙: E41의 W1·W2를 같은 식으로 다시 계산한다(경우 목록 = E41 F2 전체, 스위칭 두 경우만 교체). E42 칸 판정(judge_cells,
      3 %)을 스위칭 두 경우만 교체해 다시 한다. 보고서의 범위·칸 판정은 E43 값으로 바꾸고, 이전 값은 '출력용량 항 배율 미적용'으로 남긴다.
 (H) 클램프 자기 가열 가정
  선정(E40 p5): 사양 팩 가지 3개 × 2.4 Ω, W460 가지 3개 × 2.7 Ω, 스위치 FF2MR12KM1P, 최대 연속 켜짐 0.5 ms.
  문턱 오차 ε(켬·끔 문턱에 같이 1 + ε): 사양 팩 −1.0, −0.5, 0, +0.05, +0.10 %, W460 −1.0, −0.5, 0, +0.5, +1.0 %(각 요구 정확도).
  절차: E40 선정 행의 마지막 자기 가열 가정(E_hi, E_lo)에서 시작해 모든 ε·조합·사건(E40과 같은 사건)을 계산하고, 관측 최대(모든 ε)가
      가정을 넘으면 50 J 단위로 올려 모서리 저항을 다시 계산하고 전체를 다시 실행한다(최대 2번, E39 R3과 같음).
  판정(각 ε): (C1) V_A·버스 ≤ 상한(470·530 V), (E) 가지 에너지 ≤ 15 kJ, 스위치 (I)(V)(T)(E39 judge39의 ok), 그리고 (S) 마지막 가정이
      모든 ε의 관측 최대를 덮음. 모두 통과하면 선정을 유지한다. 하나라도 불통과면 불통과로 보고한다(재선정은 이 시험에서 하지 않는다).
 (B) 48 V 배터리
  48 V 노드: 출력 커패시터 C_o 2.2 mF(E22) ∥ 배터리 등가(OCV, 내부저항 R_b) ∥ 48 V 쪽 정전력 부하 5.0 kW(Stage C 48 V 쪽 정격,
      E22 PO_MAX). Stage C 출력은 일시 정지 동안 0(램프 무시, 보수 쪽), 정지 시간 12.4 ms(E38 P6 최대). 시작 전압은 Stage C가 조정하던
      값 min(48 V, OCV + R_b·30 A)(충전 제한 30 A, E22).
  경우: OCV 44.0·47.0·47.9 V(E22 T5와 같음) × R_b 20·40·60 mΩ.
  판정: 48 V가 ISO 21780 무제한 운전 범위 36–52 V 안(E22와 같은 기준). 결과에서 요구를 도출한다: R_b ≤ (OCV_min − 36 V)·36 V / P,
      방전 전류 ≥ P / 36 V를 12.4 ms. 일시 정지 동안 Stage C의 ±2 % 조정은 적용되지 않음을 함께 적는다(48 V = 배터리 전압).
  한계: 배터리 인덕턴스·온도·SOC 변화, Stage C 재개 과도(E22 T5 배터리 연결 시험이 대표)는 넣지 않는다.

■ 실행   python E43_review2_response.py loss heat sens bat     (sens는 heat 결과를 (C)에 쓴다. 2코어에서 sens 약 1시간)
■ 결과   results/E43/loss.json, heat.json, sens.json, bat.json
"""
import math
import sys
import time
from dataclasses import replace
from common import Pool                     # fork 문맥 또는 같은 프로세스 차례 실행(common.py, 2026-11-06)

import numpy as np

import stage_b_tests as st
from controller_adopted import K_ADOPTED
from model_stage_b import current_limit
from common import save_json, load_json, verdict, workers, outdir

EID = "E43"
BAND = 0.03


# ======================================================================================================
# (S) 측정 사양
# ======================================================================================================
BITS = 16
SENS_LIM_S1 = np.array([[-150., 150.], [-100., 100.], [0., 600.], [-150., 150.], [0., 150.], [-150., 150.]])
SENS_NOISE_S1 = np.array([.02, .005, .010, .02, .005, .02])
SENS_OFF_S1 = np.array([.2, .1, 1.2, .2, .05, .2])
S2_WIN, S2_NOISE, S2_GAIN, S2_OFF = 50., .005, .0025, .2
P2_DEV, P2_T = 20., .5e-3
RIPPLE_ALLOW = .1
T1_INST_A, T2_INST_A = 98., 100.
SENS_CASES = ("W460_240s", "W410_spec")


def sens_arr(kind, case, sign=0):
    """kind 'S1'·'S2', sign 0(오차 없음)·+1(전류 낮게·전압 높게)·−1(반대). 6×6 [이득, 오프셋, 양자화, 잡음, 하한, 상한]."""
    import E12_switching_verification as E12
    import E19_r2_window_module as E19
    lim = SENS_LIM_S1.copy(); noise = SENS_NOISE_S1.copy(); off = SENS_OFF_S1.copy(); gain = E12.SENS_GAIN_ERR.copy()
    if kind == "S2":
        VW = E19.CASES[case]["VW"]
        lim[2] = (VW - S2_WIN, VW + S2_WIN); noise[2] = S2_NOISE; off[2] = S2_OFF; gain[2] = S2_GAIN
    sg = sign * E12.CUR_LOW_V_HIGH
    s = np.zeros((6, 6))
    s[:, 0] = 1. + sg * gain; s[:, 1] = sg * off
    s[:, 2] = (lim[:, 1] - lim[:, 0]) / 2 ** BITS; s[:, 3] = noise; s[:, 4] = lim[:, 0]; s[:, 5] = lim[:, 1]
    return s


def prot_err(kind, sign):
    """보호에 쓰는 버스 측정(넓은 채널 = S1 버스 채널)의 이득 오차 g, 오프셋 o, 잡음 σ. 이상 변형은 0."""
    import E12_switching_verification as E12
    if kind is None:
        return 0., 0., 0.
    sg = sign * E12.CUR_LOW_V_HIGH[2]
    return float(sg * E12.SENS_GAIN_ERR[2]), float(sg * SENS_OFF_S1[2]), float(SENS_NOISE_S1[2])


VARIANTS_S1 = [("이상", None, 0), ("S1 잡음·양자화", "S1", 0),
               ("S1 + 오차(전류 낮게·전압 높게)", "S1", 1), ("S1 + 오차(전류 높게·전압 낮게)", "S1", -1)]
VARIANTS_S2 = [("S2 잡음·양자화", "S2", 0), ("S2 + 오차(전류 낮게·전압 높게)", "S2", 1), ("S2 + 오차(전류 높게·전압 낮게)", "S2", -1)]


def judge_w_sw(tier, r, p, VW, upper):
    """E12 judge_sw를 창 기준 V_W로 옮긴 판정(Tier-2 띠 상한은 min(V_W + 16, 상한)) + 부품 등급 상한."""
    import E12_switching_verification as E12
    t, R = r["t"], r["rec"]
    pos = t > 1e-12; post = t >= 1e-3 - 1e-12
    vb, ip, ih, vl, il, pl, m = R[:, 0], R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5], R[:, 14]
    path_inst = float(R[pos, 8].max()); bridge_inst = float(max(R[pos, 6].max(), -R[pos, 7].min()))
    series_inst = float(R[pos, 17].max()); vl_min = float(R[pos, 11].min()); vl_max = float(R[pos, 12].max())
    lim = np.array([current_limit(a, b, p) for a, b in zip(vb[pos], vl[pos])])
    env = float(np.max(np.abs(il[pos]) - lim))
    out = np.flatnonzero(post & (np.abs(vb - VW) > 4))
    rec_s = 0.
    if len(out):
        rec_s = None if out[-1] == len(t) - 1 else float(t[out[-1] + 1] - 1e-3)
    if not r["completed"]:
        rec_s = None
    tail = t >= t[-1] - 1e-3
    ripple = float(np.ptp(vb[tail & post])); ih_pp = float(np.ptp(ih[tail])); m_pp = float(np.ptp(m[tail]))
    m_pwm = float(np.abs(R[pos, 18]).max())
    viol = dict(path_current=path_inst > p.path_max, bridge_current=bridge_inst > p.path_max,
                series_voltage=series_inst > p.series_max, link_current_rating=float(np.abs(il[pos]).max()) > p.link_max,
                dab_envelope=env > 0.5, dab_power=float(np.abs(pl[pos]).max()) > p.power_max,
                link_voltage_band=vl_min < 90 or vl_max > 110, modulation=float(np.abs(m[pos]).max()) > p.modulation_max + 1e-9,
                pwm_range=m_pwm > 1.)
    ports = not any(viol.values())
    excursion = float(np.max(np.abs(vb[post] - VW)))
    final_ok = abs(vb[-1] - VW) <= 4
    internal = ih_pp <= st.TAIL_IH_PP_A and m_pp <= st.TAIL_M_PP
    vmax_all = float(vb.max())
    if tier == 1:
        ok = (r["completed"] and ports and excursion <= 8 and final_ok and rec_s is not None and rec_s <= 1e-3
              and ripple <= .1 and internal and path_inst <= T1_INST_A and bridge_inst <= T1_INST_A)
    else:
        lo, hi = VW - 16, min(VW + 16, upper)
        ok = (r["completed"] and ports and vb[post].min() >= lo and vb[post].max() <= hi and final_ok
              and path_inst <= T2_INST_A and bridge_inst <= T2_INST_A and internal)
    ok = bool(ok and vmax_all <= upper)
    return dict(path_inst=path_inst, bridge_inst=bridge_inst, excursion=excursion, recovery_s=rec_s, tail_ripple_V=ripple,
                tail_ih_pp_A=ih_pp, tail_m_pp=m_pp, vbus_end=float(vb[-1]), vbus_max_all=vmax_all,
                vbus_min_post=float(vb[post].min()), vbus_max_post=float(vb[post].max()), link_power_avg=float(np.abs(pl[pos]).max()),
                vlink_min=vl_min, vlink_max=vl_max, completed=r["completed"], ports_violated=[k for k, v in viol.items() if v],
                pass_=ok, _vb=vb, _t=t)


def prot_checks(vb, t, VW, upper, g, o, sig):
    """(P1) 비교기 오동작 여유, (P2) 조정 상실 오판 최장 지속."""
    meas = (1. + g) * vb + o
    p1_max = float(meas.max() + 3 * sig + RIPPLE_ALLOW)
    bad = np.abs(meas - VW) + 3 * sig > P2_DEV
    longest, run = 0, 0
    for b in bad:
        run = run + 1 if b else 0
        longest = max(longest, run)
    dt = float(t[1] - t[0]) if len(t) > 1 else 0.
    p2_s = longest * dt
    return dict(P1_meas_max_V=p1_max, P1=bool(p1_max <= upper), P2_longest_s=p2_s, P2=bool(p2_s < P2_T))


def _sens_job(job):
    from model_stage_b_switching import simulate_switching
    import E19_r2_window_module as E19
    case, tier, sname, v, a, b, var, kind, sign, seed = job
    c = E19.CASES[case]; p, cp = E19.plant(case)
    if sname == "delay+3.0us":
        p = replace(p, delay=p.delay + st.DELAY_BUDGET)
    s = None if kind is None else sens_arr(kind, case, sign)
    r = simulate_switching(float(v), float(a), float(b), p, cp, K_ADOPTED, predict=True, sensors=s, seed=seed)
    row = dict(case=case, tier=tier, set=sname, vbat=v, p0=a, p1=b, variant=var)
    j = judge_w_sw(tier, r, p, c["VW"], c["upper"])
    vb, t = j.pop("_vb"), j.pop("_t")
    row.update(j)
    row.update(prot_checks(vb, t, c["VW"], c["upper"], *prot_err(kind, sign)))
    return row


def _sens_jobs(variants):
    import E19_r2_window_module as E19
    js = []
    i = 0
    for case in SENS_CASES:
        for v in E19.CASES[case]["V_win"]:
            for sname in ("nominal", "delay+3.0us"):
                for tier, steps in ((1, st.T1_STEPS), (2, st.T2_STEPS)):
                    for a, b in steps:
                        for var, kind, sign in variants:
                            js.append((case, tier, sname, float(v), float(a), float(b), var, kind, sign, 3000 + i))
                        i += 1
    return js


def _key(r):
    return (r["case"], r["tier"], r["set"], r["vbat"], r["p0"], r["p1"])


def _summ(rows, name):
    sel = [r for r in rows if r["variant"] == name]
    return dict(total=len(sel), passed=sum(r["pass_"] for r in sel), P1=sum(r["P1"] for r in sel), P2=sum(r["P2"] for r in sel),
                max_tail_ripple_V=max(r["tail_ripple_V"] for r in sel), max_tail_ih_pp_A=max(r["tail_ih_pp_A"] for r in sel),
                max_inst_A=max(max(r["path_inst"], r["bridge_inst"]) for r in sel),
                P1_meas_max_V={cs: max(r["P1_meas_max_V"] for r in sel if r["case"] == cs) for cs in SENS_CASES},
                P2_longest_ms=1e3 * max(r["P2_longest_s"] for r in sel),
                vbus_end_range={cs: [min(r["vbus_end"] for r in sel if r["case"] == cs), max(r["vbus_end"] for r in sel if r["case"] == cs)]
                                for cs in SENS_CASES},
                fails=[(r["case"], r["tier"], r["set"], r["vbat"], r["p0"], r["p1"], round(r["tail_ripple_V"], 3),
                        round(r["tail_ih_pp_A"], 3), round(r["excursion"], 2), r["ports_violated"]) for r in sel if not r["pass_"]])


def _adopt(rows, ref_pass, names):
    ok_cases = all(r["pass_"] for r in rows if r["variant"] in names and ref_pass.get(_key(r)))
    ok_prot = all(r["P1"] and r["P2"] for r in rows if r["variant"] in names)
    return bool(ok_cases), bool(ok_prot)


def sens():
    t0 = time.time()
    with Pool(workers()) as pool:
        rows = pool.map(_sens_job, _sens_jobs(VARIANTS_S1), chunksize=1)
    print("  sens S1: %d건, %.0f s" % (len(rows), time.time() - t0), flush=True)
    summ = {v[0]: _summ(rows, v[0]) for v in VARIANTS_S1}
    for k, s in summ.items():
        print("   %-28s %d/%d 통과, P1 %d, P2 %d, 리플 최대 %.3f V, i_h 꼬리 %.3f A, 순시 %.1f A, 비교기 측정 최대 %s V, 조정 상실 최장 %.3f ms%s"
              % (k, s["passed"], s["total"], s["P1"], s["P2"], s["max_tail_ripple_V"], s["max_tail_ih_pp_A"], s["max_inst_A"],
                 {a: round(b, 2) for a, b in s["P1_meas_max_V"].items()}, s["P2_longest_ms"],
                 (", 불통과 %s" % s["fails"][:6]) if s["fails"] else ""), flush=True)
    ref_pass = {_key(r): r["pass_"] for r in rows if r["variant"] == "이상"}
    s1_names = [v[0] for v in VARIANTS_S1 if v[1] == "S1"]
    ok_c, ok_p = _adopt(rows, ref_pass, s1_names)
    # (C) 범위
    vmax = 1008. / 2
    try:
        h = load_json(EID, "heat")
        vmax = max(vmax, max(e["C1_V"] for part in h["parts"].values() for e in part["eps_rows"]))
    except FileNotFoundError:
        print("  (C) heat 결과 없음: 정상 최대 504 V만 씀")
    C = dict(range_hi_V=float(SENS_LIM_S1[2, 1]), v_event_max_V=vmax, need_V=1.1 * vmax, ok=bool(SENS_LIM_S1[2, 1] >= 1.1 * vmax))
    adopted = "S1" if (ok_c and ok_p and C["ok"]) else None
    out = dict(rows=rows, summary=summ, ref_pass_count=sum(ref_pass.values()), S1=dict(cases=ok_c, protection=ok_p), C=C)
    if adopted is None:
        t0 = time.time()
        with Pool(workers()) as pool:
            rows2 = pool.map(_sens_job, _sens_jobs(VARIANTS_S2), chunksize=1)
        print("  sens S2: %d건, %.0f s" % (len(rows2), time.time() - t0), flush=True)
        summ2 = {v[0]: _summ(rows2, v[0]) for v in VARIANTS_S2}
        for k, s in summ2.items():
            print("   %-28s %d/%d 통과, P1 %d, P2 %d, 리플 최대 %.3f V%s" % (k, s["passed"], s["total"], s["P1"], s["P2"],
                                                                     s["max_tail_ripple_V"], (", 불통과 %s" % s["fails"][:6]) if s["fails"] else ""))
        ok_c2, ok_p2 = _adopt(rows2, ref_pass, [v[0] for v in VARIANTS_S2])
        out.update(rows_S2=rows2, summary_S2=summ2, S2=dict(cases=ok_c2, protection=ok_p2))
        adopted = "S2" if (ok_c2 and ok_p2 and C["ok"]) else None
    out["adopted"] = adopted
    save_json(EID, "sens", out)
    verdict("(S-ref) 이상 측정 기준에서 창 조정 144건 통과", summ["이상"]["passed"] == summ["이상"]["total"],
            "%d/%d" % (summ["이상"]["passed"], summ["이상"]["total"]))
    verdict("(S1) 이상 기준 통과 건이 S1 세 변형에서 모두 통과", ok_c, "")
    verdict("(S1) 보호 오동작 없음(P1 비교기, P2 조정 상실)", ok_p, "")
    verdict("(C) 측정 범위 600 V ≥ 1.1 × 사건 최대", C["ok"], "사건 최대 %.2f V → 필요 %.1f V" % (C["v_event_max_V"], C["need_V"]))
    verdict("(S) R2 측정 사양 채택", adopted is not None, "채택 %s" % adopted)


# ======================================================================================================
# (L) 손실 민감도: Stage A 출력용량 항에도 스위칭 배율
# ======================================================================================================
def _qterm(V):
    import model_stage_a as A
    import E32_stage_a_25k as E32
    A.set_design(E32.DESIGN)
    return 4 * A.qoss_pos(V / 2.) * (V / 2.) * A.FR0


def _scaled_P(P, VG, esw):
    add = np.array([(esw - 1.) * _qterm(float(v)) for v in VG])
    return np.asarray(P, float) + add[:, None]


def _loss_e41():
    import E41_fair_aux_comparison as E41
    import E36_a25r_impact as E36
    import E32_stage_a_25k as E32
    E15, SA = E41.setup()
    orig = E15.hs_converter; K0 = dict(E15.K)
    T = E36._T_spec()

    def case(k, SA4):
        E15.K.clear(); E15.K.update(K0); E15.K.update(k)
        E15.hs_converter = E41._hs_shed(E15, orig, None)
        try:
            return {pk: {s: v for s, v in E41._all(E15, SA4, pk).items() if s != "by_load"} for pk in E15.PROFILES}
        finally:
            E15.hs_converter = orig; E15.K.clear(); E15.K.update(K0)

    saved = load_json("E41", "fair")["cases"]
    res, r1 = {}, 0.
    for esw, tag in ((0.7, "스위칭 × 0.7"), (1.5, "스위칭 × 1.5")):
        old = case(dict(esw=esw), SA)
        T2 = dict(T); T2["P"] = _scaled_P(T["P"], E15.VGRID, esw)
        new = case(dict(esw=esw), E32.StageAs(T2, E36.I_OFF))
        d = max(abs(old[pk][s] - saved[tag][pk][s]) for pk in old for s in ("4", "5", "6"))
        r1 = max(r1, d)
        res[tag] = dict(old=old, new=new, R1_diff_W=d)
        c, n = old["drive_typ"], new["drive_typ"]
        print("  E41 %s: 이전 ④ %.2f ⑤ %.2f ⑥ %.2f W → Stage A 배율 ④ %.2f ⑤ %.2f ⑥ %.2f W (R1 차 %.2g W)"
              % (tag, c["4"], c["5"], c["6"], n["4"], n["5"], n["6"], d), flush=True)
    cases = {k: v for k, v in saved.items()}
    for tag in res:
        cases[tag] = res[tag]["new"]
    sens = [k for k in cases if k != "E38 기준(셰딩 없음)"]
    d = {k: (cases[k]["drive_typ"]["5"] - cases[k]["drive_typ"]["4"]) / cases[k]["drive_typ"]["5"] for k in sens}
    fair = d["공정 기준(F1)"]
    robust = fair > BAND and all(v > BAND for v in d.values())
    W1 = dict(rule="robust" if robust else "same_level", fair_pct=100 * fair, min_pct=100 * min(d.values()),
              max_pct=100 * max(d.values()), by_case_pct={k: 100 * v for k, v in d.items()})
    d6 = {k: cases[k]["drive_typ"]["4"] - cases[k]["drive_typ"]["6"] for k in sens}
    W2 = dict(fair_W=d6["공정 기준(F1)"], min_W=min(d6.values()), max_W=max(d6.values()), by_case_W=d6,
              always_positive=all(v > 0 for v in d6.values()))
    old = load_json("E41", "fair")
    print("  E41 W1: %s, 공정 %.2f %%, 범위 %.1f … %.1f %%(이전 %.1f … %.1f %%)" % (W1["rule"], W1["fair_pct"], W1["min_pct"], W1["max_pct"],
                                                                         old["W1"]["min_pct"], old["W1"]["max_pct"]))
    print("  E41 W2: ④ − ⑥ %.1f–%.1f W(이전 %.1f–%.1f W)" % (W2["min_W"], W2["max_W"], old["W2"]["min_W"], old["W2"]["max_W"]))
    other = {pk: {k: (cases[k][pk]["5"] - cases[k][pk]["4"]) / cases[k][pk]["5"] * 100 for k in sens} for pk in cases["공정 기준(F1)"]}
    return dict(cases=res, W1=W1, W2=W2, R1_max_W=r1, by_profile_pct={pk: dict(min=min(v.values()), max=max(v.values())) for pk, v in other.items()})


def _loss_e42():
    import E42_value_map_fair as E42
    import E41_fair_aux_comparison as E41
    E15, E18 = E42.setup()
    SAm = E18.stage_a_model()
    orig = E15.hs_converter; K0 = dict(E15.K)
    captured = {}
    E18.save_json = lambda eid, name, obj: captured.__setitem__("out", obj)
    E18.figure = lambda out, path: None

    def case(k, SAx):
        E15.K.clear(); E15.K.update(K0); E15.K.update(k)
        E15.hs_converter = E41._hs_shed(E15, orig, None)
        E18.stage_a_model = lambda: SAx
        try:
            E18.main()
        finally:
            E15.hs_converter = orig; E15.K.clear(); E15.K.update(K0)
        out = captured.pop("out")
        return {pk: dict(loss={s: v["loss"]["avg_W"] for s, v in r["structs"].items()},
                         same_as={s: v.get("same_as") for s, v in r["structs"].items()},
                         feas={c: sorted(r["best"][c]["feasible"]) for c in E42.CLASSES},
                         best={c: r["best"][c]["best"] for c in E42.CLASSES})
                for pk, r in out["packs"].items()}

    saved = load_json("E42", "cases")
    res, r1 = {}, 0.
    for esw, tag in ((0.7, "스위칭 × 0.7"), (1.5, "스위칭 × 1.5")):
        old = case(dict(esw=esw), SAm)
        SAn = type(SAm)(SAm.VG, _scaled_P(SAm.T["P"], SAm.VG, esw), SAm.T["D"], SAm.T["charge"])
        new = case(dict(esw=esw), SAn)
        d = max(abs(old[pk]["loss"][s] - saved[tag][pk]["loss"][s]) for pk in old for s in old[pk]["loss"]
                if old[pk]["loss"][s] is not None and saved[tag][pk]["loss"][s] is not None)
        same_feas = all(new[pk]["feas"] == saved[tag][pk]["feas"] for pk in new)
        r1 = max(r1, d)
        res[tag] = dict(old=old, new=new, R1_diff_W=d, feas_same=same_feas)
        print("  E42 %s: R1 차 %.2g W, 성립 집합 같음 %s" % (tag, d, same_feas), flush=True)
    cases = {k: v for k, v in saved.items()}
    for tag in res:
        cases[tag] = res[tag]["new"]
    cells = E42.judge_cells(cases)
    old_cells = load_json("E42", "cells")["cells"]
    changes = {k: dict(old=old_cells[k].get("cls"), new=v.get("cls"), old_min_margin=old_cells[k].get("min_margin_pct"),
                       new_min_margin=v.get("min_margin_pct"), new_ties=v.get("ties"))
               for k, v in cells.items()}
    for k, v in changes.items():
        if v["new"] in ("성립 없음",):
            continue
        print("  칸 %-12s %s → %s, 최소 여유 %s → %s %%, 같은 수준 후보 %s" % (
            k, v["old"], v["new"], None if v["old_min_margin"] is None else round(v["old_min_margin"], 1),
            None if v["new_min_margin"] is None else round(v["new_min_margin"], 1), v["new_ties"]))
    return dict(cases=res, cells=cells, changes=changes, R1_max_W=r1)


def loss():
    e41 = _loss_e41()
    e42 = _loss_e42()
    R1 = e41["R1_max_W"] <= 1e-6 and e42["R1_max_W"] <= 1e-6
    save_json(EID, "loss", dict(e41=e41, e42=e42, R1=dict(ok=R1, e41_W=e41["R1_max_W"], e42_W=e42["R1_max_W"]),
                                qterm_W={str(v): _qterm(v) for v in (640., 800., 920., 1008.)}))
    verdict("(R1) 기존 방식 재현(E41·E42 저장값과 차 ≤ 1e-6 W)", R1, "E41 %.2g W, E42 %.2g W" % (e41["R1_max_W"], e42["R1_max_W"]))
    verdict("(L) E41 W1: ④ 대 ⑤ 같은 수준 유지", e41["W1"]["rule"] == "same_level",
            "범위 %.1f … %.1f %%" % (e41["W1"]["min_pct"], e41["W1"]["max_pct"]))
    n_chg = sum(1 for v in e42["changes"].values() if v["old"] != v["new"])
    verdict("(L) E42 칸 판정 변화 없음", n_chg == 0, "변화 %d칸" % n_chg)


# ======================================================================================================
# (H) 클램프 자기 가열 가정
# ======================================================================================================
EPS_H = {"spec": (-0.01, -0.005, 0., 0.0005, 0.001), "W460": (-0.01, -0.005, 0., 0.005, 0.01)}
N_ITER_H = 2


def heat():
    import E39_clamp_switch_rejudge as E39
    import E40_typ_rule_rejudge as E40
    sws, _ = E40.switches40()            # (실행 경과) 1차 실행에서 반환값(튜플) 처리 누락으로 중단 → 고침
    vd = E40.vdrop40(sws)
    parts = {}
    for part, cfg, evf in (("spec", E40.SPEC, E40.spec_events), ("W460", E40.W460, E40.hv_events)):
        sel, row = E40._sel_row(part)
        n, Rb, swn = sel["n"], sel["R_b"], sel["switch"]
        sw = {swn: sws[swn]}
        last = row["iter"][-1]
        E_hi, E_lo = last["E_hi_assumed"], last["E_lo_assumed"]
        hist = []
        S = None
        for it in range(N_ITER_H + 1):
            c = E39.corners39(n, Rb, E_hi, E_lo)
            cbs = E40.combos40(n, c, vd)
            jobs = [("%g|%s" % (eps, cb), br, cfg["on"] * (1 + eps), cfg["off"] * (1 + eps), e, dict(t_on_max=E40.T_ON_MAX))
                    for eps in EPS_H[part] for cb, br in cbs.items() for e in evf()]
            t0 = time.time()
            recs = E40.run_jobs(jobs)
            eps_rows = []
            for eps in EPS_H[part]:
                re = {k.split("|", 1)[1]: v for k, v in recs.items() if k.split("|", 1)[0] == "%g" % eps}
                j = E40.judge40(re, sw, cfg["lim"])
                s = j["switches"][swn]
                eps_rows.append(dict(eps=eps, C1_V=j["C1_V"], C1=j["C1"], E_branch_max_J=j["E_branch_max_J"], E=j["E"],
                                     E_hi_obs=j["E_hi_obs"], E_lo_obs=j["E_lo_obs"], i_branch_max=j["i_branch_max"],
                                     sw_ok=s["ok"], I=s["I"], V=s["V"], T=s["T"], T_vj=s["T_vj"],
                                     t_on_cont_max_ms=j["t_on_cont_max_ms"]))
            Eh = max(r["E_hi_obs"] for r in eps_rows); El = max(r["E_lo_obs"] for r in eps_rows)
            need_hi, need_lo = Eh > E_hi + 1e-9, El > E_lo + 1e-9
            hist.append(dict(it=it, E_hi_assumed=E_hi, E_lo_assumed=E_lo, E_hi_obs=Eh, E_lo_obs=El, Rmax=c["Rmax"], Rmin=c["Rmin"],
                             sec=time.time() - t0))
            print("  %s it %d: 가정 E_hi %.0f·E_lo %.0f J, 관측 %.1f·%.1f J, R %.4f–%.4f Ω (%.0f s)"
                  % (part, it, E_hi, E_lo, Eh, El, c["Rmin"], c["Rmax"], time.time() - t0), flush=True)
            if not (need_hi or need_lo):
                S = True; break
            if it == N_ITER_H:
                S = False; break
            E_hi = math.ceil(Eh / E39.E_STEP) * E39.E_STEP if need_hi else E_hi
            E_lo = math.ceil(El / E39.E_STEP) * E39.E_STEP if need_lo else E_lo
        for r in eps_rows:
            print("    ε %+.2f %%: C1 %.3f V(%s), 가지 에너지 %.1f J, 가지 전류 %.1f A, %s %.2f °C(%s)"
                  % (100 * r["eps"], r["C1_V"], "통과" if r["C1"] else "불통과", r["E_branch_max_J"], r["i_branch_max"], swn, r["T_vj"],
                     "통과" if r["sw_ok"] else "불통과"))
        ok = bool(S and all(r["C1"] and r["E"] and r["sw_ok"] for r in eps_rows))
        parts[part] = dict(n=n, R_b=Rb, switch=swn, lim=cfg["lim"], eps_rows=eps_rows, iter=hist, S=S, ok=ok)
        verdict("(H) %s: 문턱 정확도 범위 전체에서 클램프 판정 통과(자기 가열 가정이 최대 에너지를 덮음)" % part, ok,
                "가정 E_hi %.0f·E_lo %.0f J" % (hist[-1]["E_hi_assumed"], hist[-1]["E_lo_assumed"]))
    save_json(EID, "heat", dict(parts=parts, eps=EPS_H))


# ======================================================================================================
# (B) 48 V 배터리
# ======================================================================================================
B_OCV = (44.0, 47.0, 47.9)
B_R = (0.02, 0.04, 0.06)
B_P = 5000.
B_T = 12.4e-3
B_CO = 2.2e-3
B_ICH = 30.
B_RANGE = (36., 52.)


def bat():
    rows = []
    for ocv in B_OCV:
        for R in B_R:
            v = min(48., ocv + R * B_ICH)
            dt = 1e-6; vmin = v; ibmax = 0.; E = 0.
            for _ in range(int(round(B_T / dt))):
                ib = (ocv - v) / R
                v += dt * (ib - B_P / v) / B_CO
                vmin = min(vmin, v); ibmax = max(ibmax, ib); E += ocv * ib * dt
            v_ss = (ocv + math.sqrt(ocv * ocv - 4 * R * B_P)) / 2 if ocv * ocv > 4 * R * B_P else float("nan")
            ok = bool(B_RANGE[0] <= vmin <= B_RANGE[1])
            rows.append(dict(OCV=ocv, R_b=R, v_start=min(48., ocv + R * B_ICH), v_min=vmin, v_steady=v_ss, i_bat_max=ibmax,
                             E_bat_J=E, ok=ok, within_2pct=bool(vmin >= 48. * 0.98)))
            print("  OCV %.1f V, R_b %.0f mΩ: 48 V 최저 %.2f V(정상 %.2f V), 배터리 전류 최대 %.0f A, 에너지 %.0f J → %s"
                  % (ocv, 1e3 * R, vmin, v_ss, ibmax, E, "36–52 V 안" if ok else "범위 밖"))
    ocv_min = min(B_OCV)
    Rmax = (ocv_min - B_RANGE[0]) * B_RANGE[0] / B_P
    req = dict(R_b_max_ohm_at_OCVmin=Rmax, OCV_min=ocv_min, I_pulse_A=B_P / B_RANGE[0], t_s=B_T)
    save_json(EID, "bat", dict(rows=rows, req=req, P_W=B_P, T_s=B_T, C_o=B_CO))
    verdict("(B) 배터리 등가(E22: OCV 44–47.9 V, 20 mΩ)에서 Stage C 일시 정지 동안 48 V가 36–52 V 안",
            all(r["ok"] for r in rows if r["R_b"] == 0.02), "")
    print("  요구: OCV %.0f V에서 R_b ≤ %.1f mΩ, 방전 전류 ≥ %.0f A(%.1f ms). 일시 정지 동안 ±2 %% 조정은 적용되지 않음(배터리 전압)."
          % (ocv_min, 1e3 * Rmax, B_P / B_RANGE[0], 1e3 * B_T))


if __name__ == "__main__":
    parts = sys.argv[1:] or ["loss", "heat", "sens", "bat"]
    for p in parts:
        print("\n==== E43 %s ====" % p, flush=True)
        {"loss": loss, "heat": heat, "sens": sens, "bat": bat}[p]()
