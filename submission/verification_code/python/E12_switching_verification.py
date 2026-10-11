"""[E12] Stage B 스위칭 모델 검증: 리플 포함 전류 판정, 데드타임, 지연 여유, 복합 공차.

■ 목적
  평균모델(E5–E7)에서 확인한 채택 제어기의 전류·전압·지연 여유가 PWM 리플, 데드타임, DAB 위상천이
  동작을 포함한 스위칭 수준에서도 성립하는지 확인한다(보고서 8.2절의 1단계). 판정은 docs/14 D5의 스위칭
  모델 기준(리플 포함 순시 경로·필터 전류 Tier-1 ≤ 98 A, Tier-2 ≤ 100 A)이다.

■ 왜 필요한가
  평균모델의 전류 기준 90 A·93.75 A는 "스위칭 리플 반진폭 최대 6.25 A"라는 가정에서 나왔다. 이 가정과
  평균모델 결과가 실제 스위칭 동작에서 맞는지, 그리고 평균모델이 다루지 않는 데드타임 전압오차·DAB 위상
  양자화·표본 시점의 리플이 제어 성능을 바꾸지 않는지 확인해야 제어기를 하드웨어로 옮길 수 있다.

■ 모델 (model_stage_b_switching.py)
  H-브리지 유니폴라 PWM 200 kHz(데드타임 50 ns, 출력용량 1 nF/스위치), DAB SPS 200 kHz(데드타임 100 ns,
  영전류 클램프, 반송파에 고정한 대칭 에지와 직류 편류를 막는 위상 갱신), 표본 시점은 반송파 최댓값, 지령은
  전달지연 뒤 반영. 에지는 적분 간격 안의 정확한 위치로 처리한다(5 ns 격자에 따른 듀티·위상 양자화 없음).
  채택 제어기 이득·예측 구조는 평균모델과 같고, 변조기에 교정표 기반 부분 데드타임 보상(예측 전류·리플 극값에서의
  전이별 오차를 전류별 오차표에서 읽어 비율 κ만 보상, κ는 20 A 이하 0.6 → 80 A 1.0, 기본 플랜트는 선형 출력용량 1 nF)을 둔다. DAB 링크전류는 누설 인덕턴스 −10 % 기준 앞먹임 위상에 측정 링크전류로
  추정한 전류비 보정을 더해 정한다(정격 보호와 용량을 함께 만족). DAB 손실은 평균모델과 같은 효율 0.96(직전 주기
  평균 전력 기준, 권선저항 손실 포함)이다. 센서는 기본 이상이며, sensors 파트에서 ADC·잡음·이득·오프셋 오차를 넣는다.

■ 구성
  model_checks 모델 검산: 에너지 보존 잔차, SPS 전달식·평균모델 정상점과의 일치, 과도 중 변압기 직류 편류
  ripple      정상상태(−3.2·0·25 kW, 632–920 V)의 필터전류 리플, 변압기 전류, 링크·버스 리플, ZVS 조건
  linear      평균모델 선형화: 변조율 이득 오차(±10–30 %)의 영향(이득 오차가 있는 고정점에서 선형화)
  grid        Tier-1·Tier-2 격자(평균모델 E5와 같은 스텝·전압, 공차 17종 — DAB 시정수 대신 누설 인덕턴스 ±10 %)
  convergence 격자 전체를 적분간격 2.5 ns로 다시 계산해 판정·전류 최댓값의 수렴 확인
  dab_limit   DAB 링크전류 제한 방식 비교: 누설 인덕턴스 ±10 % × (공칭 L 앞먹임 / L −10 % 앞먹임 / 채택 전류비 보정)
  sensors     센서·ADC: 채널별 잡음 이득, 양자화 비트 수, 기본 집합 168건을 12비트와 요구 사양(16비트·창 측정·잡음·오차)으로 판정
  sensor_diag sensors에서 보장 범위 사례가 실패하면 원인 분리(채널 묶음별 오차, DAB·H-브리지 데드타임 제거)
  comp_schedule 데드타임 보상 비율의 전류 스케줄 비교(고정 1.0·고정 0.6·급한 증가·채택)
  deadtime_robust 데드타임 보상 강건성: 불확도 10종(L_h ±10 %, 선형·비선형 출력용량·교정 오차) × 경부하 보상 비율 κ 5종 × 9개 사례
  delay       비선형 추가 지연 경계(640·920 V, Tier-1 대표 3 스텝)
  corners     복합 ±10 % 공차 128개 코너(640 V): Tier-1(+3.0 µs), Tier-2
  sequences   부하 계약 최악 시퀀스 48건
  sensitivity 대표 8개 사례 × 데드타임·출력용량(보상 모델 불일치)·보상 방식·DAB 데드타임·적분간격 변형
  figures     그림(640 V Tier-2 과도, 700 V 정상상태 파형)

■ 판정 (주기 평균 = 5 µs 제어주기 평균)
  전압 품질 6항목은 주기 평균 버스전압으로, 포트 한계는 순시값(경로·필터 100 A, 직렬 90 V, 링크전압
  90–110 V)과 주기 평균(링크전류 80 A, 링크전력 8 kW)으로, 내부 진동은 주기 평균 i_h와 변조율 지령으로 본다.
  DAB 포락선 검사(주기 평균 링크전류 ≤ 주기 평균 전압으로 계산한 SPS 한계)는 주기 평균끼리의 비교라 0.5 A를
  허용한다(평균모델은 1e-3 A). 변조율 한계 0.95는 제어기 출력(보상 전 지령)에 적용하고, 데드타임 보상 후 PWM
  비교값은 ±1(반송파 범위) 안에 있는지 따로 확인한다.
  Tier-1: 위 항목 + 순시 경로·필터 ≤ 98 A,  Tier-2: 완료·포트·버스 384–416 V·최종 ±4 V·순시 ≤ 100 A·내부 진동

■ 실행   python E12_switching_verification.py              (전체, 2코어 약 2.5시간)
         python E12_switching_verification.py grid sensitivity
■ 결과   results/E12/*.json, results/E12/E12_*.png
"""
import itertools
import sys
import time
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

import stage_b_tests as st
from controller_reference import NOMINAL
from controller_adopted import K_ADOPTED, CP
from model_stage_b import current_limit
from model_stage_b_switching import simulate_switching, SW_DEFAULT
from common import save_json, load_json, verdict, workers, outdir

T1_INST_A, T2_INST_A = 98., 100.


# ------------------------------------------------------------------ 판정
def judge_sw(tier, r, p):
    t, R = r["t"], r["rec"]
    pos = t > 1e-12; post = t >= 1e-3 - 1e-12
    vb, ip, ih, vl, il, pl, m = R[:, 0], R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5], R[:, 14]
    path_inst = float(R[pos, 8].max()); bridge_inst = float(max(R[pos, 6].max(), -R[pos, 7].min()))
    series_inst = float(R[pos, 17].max()); vl_min = float(R[pos, 11].min()); vl_max = float(R[pos, 12].max())
    lim = np.array([current_limit(a, b, p) for a, b in zip(vb[pos], vl[pos])])
    env = float(np.max(np.abs(il[pos]) - lim))
    out = np.flatnonzero(post & (np.abs(vb - 400) > 4))
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
    excursion = float(np.max(np.abs(vb[post] - 400)))
    final_ok = abs(vb[-1] - 400) <= 4
    internal = ih_pp <= st.TAIL_IH_PP_A and m_pp <= st.TAIL_M_PP
    row = dict(path_inst=path_inst, bridge_inst=bridge_inst, path_avg=float(np.abs(ip[pos]).max()),
               bridge_avg=float(np.abs(ih[pos]).max()), link_avg=float(np.abs(il[pos]).max()),
               link_power_avg=float(np.abs(pl[pos]).max()), iL_peak=float(R[pos, 13].max()), series_inst=series_inst,
               vlink_min=vl_min, vlink_max=vl_max, droop=float(400 - vb[post].min()), vbus_max_post=float(vb[post].max()),
               vbus_min_post=float(vb[post].min()), recovery_s=rec_s, tail_ripple_V=ripple, tail_ih_pp_A=ih_pp,
               tail_m_pp=m_pp, modulation_peak=float(np.abs(m[pos]).max()), dab_envelope_excess_A=env,
               modulation_pwm_peak=m_pwm, dc_bias_A=float(np.abs(R[pos, 19]).max()), dab_rho_end=float(R[-1, 21]),
               vbus_end=float(vb[-1]),
               tail_ih_freq_hz=tail_freq(t, ih) if ih_pp > .05 else None,
               completed=r["completed"], ports_violated=[k for k, v in viol.items() if v],
               zvs_primary=float(r["zvs"][0] / max(r["zvs"][1], 1)), zvs_secondary=float(r["zvs"][2] / max(r["zvs"][3], 1)))
    if tier == 1:
        ok = (r["completed"] and ports and excursion <= 8 and final_ok and rec_s is not None and rec_s <= 1e-3
              and ripple <= .1 and internal and path_inst <= T1_INST_A and bridge_inst <= T1_INST_A)
    else:
        ok = (r["completed"] and ports and vb[post].min() >= st.T2_BAND[0] and vb[post].max() <= st.T2_BAND[1]
              and final_ok and path_inst <= T2_INST_A and bridge_inst <= T2_INST_A and internal)
    row["pass_"] = bool(ok)
    return row


def tail_freq(t, ih, win=5e-3):
    """마지막 win 구간 주기 평균 i_h의 지배 주파수 [Hz](내부 진동이 있을 때 기록용, 8배 영채움 FFT)."""
    s = t >= t[-1] - win
    y = ih[s] - ih[s].mean(); n = len(y)
    if n < 16:
        return None
    sp = np.abs(np.fft.rfft(y * np.hanning(n), 8 * n)); f = np.fft.rfftfreq(8 * n, t[1] - t[0])
    return float(f[np.argmax(sp[1:]) + 1])


def run_case(args):
    tier, vbat, a, b, p, profile, sw, meta = args
    meta = dict(meta); sens = meta.pop("_sensors", None); seed = meta.pop("_seed", 1)
    r = simulate_switching(float(vbat), float(a), float(b), p, CP, K_ADOPTED, predict=True, profile=profile, sw=sw,
                           sensors=None if sens is None else np.array(sens), seed=seed)
    row = dict(tier=tier, vbat=vbat, p0=a, p1=b, profile=profile, **meta)
    row.update(judge_sw(tier, r, p))
    return row


def pmap(js):
    with Pool(workers()) as pool:
        return pool.map(run_case, js, chunksize=2)


# ------------------------------------------------------------------ 파트
def part_ripple():
    """정상상태 리플·변압기 전류·ZVS 조건."""
    rows = []
    js = [(v, P) for v in (632., 640., 660., 700., 750., 788., 860., 920.) for P in (-3200., 0., 25000.)]
    for v, P in js:
        r = simulate_switching(v, P, P, NOMINAL, CP, K_ADOPTED, duration=.002, capture=[1.98e-3, 2e-3, 1])
        R = r["rec"]; tail = r["t"] >= r["t"][-1] - .5e-3; w = r["wave"]
        rows.append(dict(vbat=v, power=P, ih_avg=float(R[tail, 2].mean()), m=float(R[tail, 14].mean()),
                         vlink_avg=float(R[tail, 3].mean()),
                         ih_ripple_pp=float((R[tail, 6] - R[tail, 7]).mean()), iL_peak=float(R[tail, 13].max()),
                         iL_rms=float(np.sqrt(np.mean(w[:, 6] ** 2))), ih_rms=float(np.sqrt(np.mean(w[:, 4] ** 2))),
                         vlink_pp=float(np.ptp(w[:, 5])), vbus_pp=float(np.ptp(w[:, 3])), vs_pp=float(np.ptp(w[:, 2])),
                         phase_deg=float(np.degrees(R[tail, 16].mean())),
                         zvs_primary=float(r["zvs"][0] / max(r["zvs"][1], 1)), zvs_secondary=float(r["zvs"][2] / max(r["zvs"][3], 1))))
    mx = max(rows, key=lambda x: x["ih_ripple_pp"])
    print(f"   필터전류 리플 최대 {mx['ih_ripple_pp']:.2f} A pp(반진폭 {mx['ih_ripple_pp']/2:.2f} A) @ {mx['vbat']:.0f} V, "
          f"{mx['power']/1e3:g} kW, m = {mx['m']:.2f}  (가정 6.25 A)")
    for x in rows:
        if x["power"] == 25000.:
            print(f"   {x['vbat']:.0f} V 25 kW: m {x['m']:.3f}, 리플 {x['ih_ripple_pp']:.2f} A pp, 변압기 피크 {x['iL_peak']:.1f} A·실효 {x['iL_rms']:.1f} A, "
                  f"링크 리플 {x['vlink_pp']*1e3:.0f} mV, 버스 리플 {x['vbus_pp']*1e3:.1f} mV, ZVS 1차 {x['zvs_primary']*100:.0f} %·2차 {x['zvs_secondary']*100:.0f} %")
    # 해석식(유니폴라): Δi_pp = v_link·|m|(1−|m|)/(2·L_h·f_sw)
    for x in rows:
        mm = abs(x["m"]); x["ih_ripple_pp_formula"] = x["vlink_avg"] * mm * (1 - mm) / (2 * NOMINAL.Lh * 200e3)
    err = max(abs(x["ih_ripple_pp"] - x["ih_ripple_pp_formula"]) / max(x["ih_ripple_pp_formula"], 1.) for x in rows)
    err_hi = max(abs(x["ih_ripple_pp"] - x["ih_ripple_pp_formula"]) / x["ih_ripple_pp_formula"] for x in rows if abs(x["m"]) >= .2)
    vmax = mx["vlink_avg"] / (8 * NOMINAL.Lh * 200e3)
    verdict("리플 최댓값이 해석식 최댓값 v_link/(8·L_h·f)과 1 % 이내", abs(mx["ih_ripple_pp"] - vmax) / vmax < .01,
            f"{mx['ih_ripple_pp']:.2f} / {vmax:.2f} A")
    worst = max(rows, key=lambda x: abs(x["ih_ripple_pp"] - x["ih_ripple_pp_formula"]) / max(x["ih_ripple_pp_formula"], 1.))
    print(f"   해석식 v_link·|m|(1−|m|)/(2·L_h·f) 대비 오차: |m| ≥ 0.2에서 최대 {err_hi*100:.2f} %, 전체 최대 {err*100:.2f} % "
          f"(최대 위치 {worst['vbat']:.0f} V, {worst['power']/1e3:g} kW, m = {worst['m']:.3f})")
    print(f"   리플 반진폭 최대 {mx['ih_ripple_pp']/2:.2f} A: 평균모델 기준의 가정 6.25 A(링크 100 V)보다 "
          f"{mx['ih_ripple_pp']/2 - 6.25:+.2f} A(이 운전점 링크 {mx['vlink_avg']:.2f} V). Tier-1 90 A 기준의 여유 1.75 A 안이다.")
    zp = min(x["zvs_primary"] for x in rows); zs = min(x["zvs_secondary"] for x in rows)
    print(f"   DAB 전류 방향 기준 ZVS 조건: 1차 최소 {zp*100:.0f} %, 2차 최소 {zs*100:.0f} % (−3.2·0·25 kW 전체)")
    lost = [(x["vbat"], x["power"], round(x["zvs_primary"], 2), round(x["zvs_secondary"], 2)) for x in rows
            if min(x["zvs_primary"], x["zvs_secondary"]) < .99]
    print(f"   ZVS 조건을 일부 잃는 운전점(경부하): {lost}")
    return dict(rows=rows, max_ripple_half_A=mx["ih_ripple_pp"] / 2, formula_max_rel_err=err, formula_rel_err_m_ge_0p2=err_hi,
                formula_worst_point=dict(vbat=worst["vbat"], power=worst["power"], m=worst["m"]),
                zvs_min=(zp, zs), zvs_lost_points=lost)


def sets_sw():
    base = {"nominal": NOMINAL, "delay+3.0us": replace(NOMINAL, delay=NOMINAL.delay + st.DELAY_BUDGET)}
    tol = {}
    for f in st.FIELDS:
        for k in (.9, 1.1):
            tol[f"{f}x{k}"] = replace(NOMINAL, **{f: getattr(NOMINAL, f) * k})
    tol["eta0.94"] = replace(NOMINAL, eta=.94)
    for k in (.9, 1.1):
        tol[f"Ldabx{k}"] = replace(NOMINAL, Ldab=NOMINAL.Ldab * k)
    return base, tol


def part_grid():
    base, tol = sets_sw()
    js = []
    for v in st.V_ALL:
        for n, p in base.items():
            js += [(1, v, a, b, p, 0, None, dict(set=n)) for a, b in st.T1_STEPS]
            js += [(2, v, a, b, p, 0, None, dict(set=n)) for a, b in st.T2_STEPS]
    for v in st.V_TOL:
        for n, p in tol.items():
            js += [(1, v, a, b, p, 0, None, dict(set=n)) for a, b in st.T1_STEPS]
            js += [(2, v, a, b, p, 0, None, dict(set=n)) for a, b in st.T2_STEPS]
    rows = pmap(js)
    # 평균모델 결과와 비교(같은 조건이 있는 경우)
    avg = {(r["tier"], r["set"], float(r["vbat"]), r["p0"], r["p1"]): r for r in load_json("E5", "grid_adopted")["rows"]}
    for r in rows:
        a = avg.get((r["tier"], r["set"], float(r["vbat"]), r["p0"], r["p1"]))
        if a:
            r["avg_model"] = dict(path_peak=a["path_peak"], bridge_peak=a["bridge_peak"], droop=a["droop"], pass_=a["pass_"])

    def agg(tier, delay):
        sel = [r for r in rows if r["tier"] == tier and (r["set"] == "delay+3.0us") == delay]
        return dict(total=len(sel), passed=sum(r["pass_"] for r in sel),
                    max_inst_A=max(max(r["path_inst"], r["bridge_inst"]) for r in sel),
                    max_avg_A=max(max(r["path_avg"], r["bridge_avg"]) for r in sel),
                    vbus_post_range_V=(min(r["vbus_min_post"] for r in sel), max(r["vbus_max_post"] for r in sel)),
                    max_droop_V=max(r["droop"] for r in sel), max_tail_ih_pp_A=max(r["tail_ih_pp_A"] for r in sel),
                    max_dc_bias_A=max(r["dc_bias_A"] for r in sel), max_iL_peak_A=max(r["iL_peak"] for r in sel),
                    max_modulation_cmd=max(r["modulation_peak"] for r in sel),
                    max_modulation_pwm=max(r["modulation_pwm_peak"] for r in sel),
                    fails=[(r["set"], r["vbat"], r["p0"], r["p1"], r["ports_violated"]) for r in sel if not r["pass_"]])
    summ = {"T1": agg(1, False), "T1_delay": agg(1, True), "T2": agg(2, False), "T2_delay": agg(2, True)}
    cmp = [r for r in rows if "avg_model" in r]
    d_path = [r["path_avg"] - r["avg_model"]["path_peak"] for r in cmp]
    d_droop = [r["droop"] - r["avg_model"]["droop"] for r in cmp]
    summ["vs_average_model"] = dict(cases=len(cmp), path_avg_minus_avg_model_A=(min(d_path), max(d_path)),
                                    droop_minus_avg_model_V=(min(d_droop), max(d_droop)),
                                    verdict_changes=[(r["tier"], r["set"], r["vbat"], r["p0"], r["p1"], r["avg_model"]["pass_"], r["pass_"])
                                                     for r in cmp if r["avg_model"]["pass_"] != r["pass_"]])
    summ["max_link_power_avg_W"] = max(r["link_power_avg"] for r in rows)
    summ["max_link_avg_A"] = max(r["link_avg"] for r in rows)
    summ["max_iL_peak_A"] = max(r["iL_peak"] for r in rows)
    summ["max_dc_bias_A"] = max(r["dc_bias_A"] for r in rows)
    summ["max_dab_envelope_excess_A"] = max(r["dab_envelope_excess_A"] for r in rows)
    summ["max_modulation_pwm"] = max(r["modulation_pwm_peak"] for r in rows)
    summ["tail_ih_pp_over_0p1A"] = [(r["tier"], r["set"], r["vbat"], r["p0"], r["p1"], round(r["tail_ih_pp_A"], 3), r["tail_ih_freq_hz"])
                                    for r in rows if r["tail_ih_pp_A"] > .1]
    for k in ("T1", "T1_delay", "T2", "T2_delay"):
        s = summ[k]
        print(f"   {k:9s}: {s['passed']}/{s['total']} 통과, 순시 최대 {s['max_inst_A']:.2f} A (주기 평균 최대 {s['max_avg_A']:.2f} A)"
              + (f", 실패 {s['fails'][:4]}" if s["fails"] else ""))
    v = summ["vs_average_model"]
    print(f"   평균모델 대비: 주기 평균 경로전류 차 {v['path_avg_minus_avg_model_A'][0]:+.2f} ~ {v['path_avg_minus_avg_model_A'][1]:+.2f} A, "
          f"강하 차 {v['droop_minus_avg_model_V'][0]:+.2f} ~ {v['droop_minus_avg_model_V'][1]:+.2f} V, 판정 변화 {len(v['verdict_changes'])}건")
    verdict("Tier-1(지연 제외) 전부 통과(순시 ≤ 98 A)", summ["T1"]["passed"] == summ["T1"]["total"])
    verdict("Tier-1 추가 지연 +3.0 µs 전부 통과", summ["T1_delay"]["passed"] == summ["T1_delay"]["total"])
    verdict("Tier-2(지연 제외) 전부 통과(순시 ≤ 100 A)", summ["T2"]["passed"] == summ["T2"]["total"])
    return dict(summary=summ, rows=rows)


def part_convergence():
    """격자 전체(576건)를 적분간격 2.5 ns로 다시 계산해 5 ns 결과와 비교한다."""
    base, tol = sets_sw()
    allsets = dict(base, **tol)
    prev = load_json("E12", "grid")["rows"]
    js = [(r["tier"], r["vbat"], r["p0"], r["p1"], allsets[r["set"]], 0, dict(dt=2.5e-9), dict(set=r["set"])) for r in prev]
    rows = pmap(js)
    d_inst = [abs(max(a["path_inst"], a["bridge_inst"]) - max(b["path_inst"], b["bridge_inst"])) for a, b in zip(prev, rows)]
    d_droop = [abs(a["droop"] - b["droop"]) for a, b in zip(prev, rows)]
    changes = [(a["tier"], a["set"], a["vbat"], a["p0"], a["p1"], a["pass_"], b["pass_"]) for a, b in zip(prev, rows) if a["pass_"] != b["pass_"]]
    i = int(np.argmax(d_inst))
    out = dict(cases=len(rows), max_inst_current_diff_A=float(max(d_inst)), worst=dict(tier=prev[i]["tier"], set=prev[i]["set"],
               vbat=prev[i]["vbat"], p0=prev[i]["p0"], p1=prev[i]["p1"]), max_droop_diff_V=float(max(d_droop)),
               verdict_changes=changes, max_tail_ih_pp_A=max(r["tail_ih_pp_A"] for r in rows),
               rows=[dict(tier=r["tier"], set=r["set"], vbat=r["vbat"], p0=r["p0"], p1=r["p1"], pass_=r["pass_"],
                          path_inst=r["path_inst"], bridge_inst=r["bridge_inst"], droop=r["droop"], tail_ih_pp_A=r["tail_ih_pp_A"]) for r in rows])
    print(f"   {len(rows)}건: 순시 전류 최댓값 차 최대 {out['max_inst_current_diff_A']:.3f} A, 강하 차 최대 {out['max_droop_diff_V']:.3f} V, "
          f"판정 변화 {len(changes)}건")
    verdict("적분간격 5 → 2.5 ns(격자 전체)에서 판정 변화 없음, 순시 전류 차 < 0.1 A", not changes and out["max_inst_current_diff_A"] < .1,
            f"{out['max_inst_current_diff_A']:.3f} A")
    return out


DAB_DESIGNS = {"앞먹임·공칭 L 기준": dict(dab_estimator=False, dab_Lmin=1.),
               "앞먹임·L −10 % 기준": dict(dab_estimator=False, dab_Lmin=.9),
               "측정 전류비 보정(채택)": {}}


def part_dab_limit():
    """DAB 링크전류 제한 방식의 비교. 위상 앞먹임만으로 전류를 정하면 실제 누설 인덕턴스가 공칭과 다를 때
    같은 위상에서 흐르는 전류가 달라진다. (1) 공칭 L 기준 앞먹임, (2) L −10 % 기준 앞먹임, (3) 채택: L −10 % 기준
    앞먹임 + 측정 링크전류로 추정한 전류비 ρ̂로 지령을 보정(미학습 시 ρ̂ = 1)을 L_dab ±10 %, 632·640 V에서 비교한다."""
    from model_stage_b import equilibrium
    js = []
    for v in (632., 640.):
        for k in (.9, 1., 1.1):
            for name, sw in DAB_DESIGNS.items():
                p = replace(NOMINAL, Ldab=NOMINAL.Ldab * k)
                for t, a, b in [(2, 1000, 25000), (1, 15000, 25000)]:
                    js.append((t, v, a, b, p, 0, sw, dict(Ldab_scale=k, design=name)))
    rows = pmap(js)
    out = []
    for name in DAB_DESIGNS:
        for k in (.9, 1., 1.1):
            sel = [r for r in rows if r["Ldab_scale"] == k and r["design"] == name]
            o = dict(design=name, Ldab_scale=k, link_avg_max_A=max(r["link_avg"] for r in sel),
                     link_power_avg_max_W=max(r["link_power_avg"] for r in sel), passed=sum(r["pass_"] for r in sel), total=len(sel),
                     max_inst_A=max(max(r["path_inst"], r["bridge_inst"]) for r in sel), vlink_min=min(r["vlink_min"] for r in sel),
                     rho_end=[round(r["dab_rho_end"], 4) for r in sel], rating_violations=sorted({v for r in sel for v in r["ports_violated"]}))
            out.append(o)
            print(f"   {name:16s} L_dab ×{k}: 링크전류 최대 {o['link_avg_max_A']:.2f} A, 링크전력 최대 {o['link_power_avg_max_W']:.0f} W, "
                  f"링크전압 최저 {o['vlink_min']:.1f} V, {o['passed']}/{o['total']} 통과" + (f", 위반 {o['rating_violations']}" if o["rating_violations"] else ""))
    need = {v: float(equilibrium(v, 25000., NOMINAL)[0][5]) for v in (632., 640.)}
    print(f"   25 kW 정상 운전에 필요한 링크전류: 632 V {need[632.]:.2f} A, 640 V {need[640.]:.2f} A")
    est = [r for r in rows if r["design"] == "측정 전류비 보정(채택)" and r["p0"] == 15000]   # 스텝 전 15 kW에서 학습된 상태
    rho_err = max(abs(r["dab_rho_end"] - .9 / r["Ldab_scale"]) for r in est)
    print(f"   전류비 추정값(이론 0.9/k): " + ", ".join(f"{r['vbat']:.0f} V ×{r['Ldab_scale']}: {r['dab_rho_end']:.4f}" for r in est)
          + f" → 최대 차 {rho_err:.4f}")
    adopted = [o for o in out if o["design"] == "측정 전류비 보정(채택)"]
    verdict("채택 방식에서 L_dab ±10 %·632·640 V 모두 통과하고 링크 정격(80 A, 8 kW) 이내",
            all(o["passed"] == o["total"] and o["link_avg_max_A"] <= 80 and o["link_power_avg_max_W"] <= 8000 for o in adopted))
    verdict("앞먹임만으로는 L ±10 %를 함께 만족하지 못함(공칭 L 기준은 정격 초과, L −10 % 기준은 용량 부족)",
            any(o["rating_violations"] for o in out if o["design"] == "앞먹임·공칭 L 기준")
            and any(o["passed"] < o["total"] for o in out if o["design"] == "앞먹임·L −10 % 기준"))
    return dict(summary=out, need_link_A=need, rho_max_err=rho_err, rows=rows)


# ------------------------------------------------------------------ 센서·ADC
# 채널: i_p, v_s, v_bus, i_h, v_link, 링크전류(주기 평균). 측정 범위(ADC 전 범위)와 요구 사양 후보.
SENS_NAMES = ["i_p", "v_s", "v_bus", "i_h", "v_link", "i_link"]
SENS_RANGE_FULL = np.array([300., 300., 600., 300., 150., 300.])  # 전 범위 측정: ±150 A, ±150 V, 0–600 V, ±150 A, 0–150 V, ±150 A
SENS_RANGE = np.array([300., 200., 100., 300., 150., 300.])      # 요구 사양: v_s ±100 V, v_bus 350–450 V 창(차동), 나머지 같음
SENS_NOISE_REQ = np.array([.02, .005, .005, .02, .005, .02])     # 요구 사양: 표본 잡음 표준편차 [A 또는 V]
SENS_GAIN_ERR = np.array([.01, .005, .0025, .01, .005, .01])     # 이득 오차
SENS_OFFSET_ERR = np.array([.2, .1, .2, .2, .05, .2])            # 오프셋 [A 또는 V]
CUR_LOW_V_HIGH = np.array([-1., 1., 1., -1., 1., -1.])           # 전류는 낮게, 전압은 높게 읽는 조합


def sensor_set(bits=None, noise=None, sign=None, ranges=None):
    s = np.zeros((6, 4)); s[:, 0] = 1.
    if bits:
        s[:, 2] = (SENS_RANGE if ranges is None else ranges) / 2 ** bits
    if noise is not None:
        s[:, 3] = noise
    if sign is not None:
        s[:, 0] += sign * SENS_GAIN_ERR; s[:, 1] = sign * SENS_OFFSET_ERR
    return s


def _noise_job(a):
    v, P, name, s, seed = a
    r = simulate_switching(v, P, P, NOMINAL, CP, K_ADOPTED, duration=.006, sensors=s, seed=seed)
    R = r["rec"]; tl = R[-200:]
    return dict(vbat=v, power=P, case=name, ih_std=float(np.std(R[-400:, 2])), ih_pp=float(np.ptp(tl[:, 2])),
                vbus_pp=float(np.ptp(tl[:, 0])), m_pp=float(np.ptp(tl[:, 14])), vbus_mean_err=float(R[-400:, 0].mean() - 400))


def part_sensors():
    """센서·ADC가 판정에 주는 영향과 요구 사양. 판정 기준은 그대로(전압·전류는 실제 값으로 판정)이며,
    (1) 채널별 잡음 이득(잡음 표준편차 0.1 A 또는 0.1 V를 한 채널에만 넣은 정상상태), (2) 전 범위 측정의 양자화 비트 수,
    (3) 시험 격자의 기본 집합(공칭·+3.0 µs, 168건)을 12비트 전 범위 측정과 요구 사양(16비트, 버스전압 350–450 V 창·직렬전압
    ±100 V 측정, 전압 5 mV·전류 20 mA 잡음, 이득·오프셋 오차)으로 판정한다. 이득·오프셋 오차 조합은 보장 범위(640 V 이상)로도 따로 집계한다."""
    pts = [(640., 25000.), (700., 25000.), (920., 25000.), (788., 5000.)]
    js = []
    for v, P in pts:
        for c in range(5):
            s = sensor_set(); s[c, 3] = .1
            js.append((v, P, f"잡음 {SENS_NAMES[c]} 0.1", s, 11 + c))
        for bits in (12, 14, 16):
            js.append((v, P, f"양자화 {bits}비트", sensor_set(bits=bits, ranges=SENS_RANGE_FULL), 1))
    with Pool(workers()) as pool:
        nrows = pool.map(_noise_job, js, chunksize=2)
    gains = {}
    for c in range(5):
        sel = [x for x in nrows if x["case"] == f"잡음 {SENS_NAMES[c]} 0.1"]
        gains[SENS_NAMES[c]] = dict(ih_pp_per_unit=max(x["ih_pp"] for x in sel) / .1, vbus_pp_per_unit=max(x["vbus_pp"] for x in sel) / .1,
                                    m_pp_per_unit=max(x["m_pp"] for x in sel) / .1)
        g = gains[SENS_NAMES[c]]
        print(f"   잡음 이득 {SENS_NAMES[c]:6s}: i_h 주기 평균 변동 {g['ih_pp_per_unit']:.1f} A pp/단위, 버스 {g['vbus_pp_per_unit']:.2f} V pp/단위, "
              f"변조율 {g['m_pp_per_unit']:.4f}/단위 (단위 = 1 A 또는 1 V 표준편차, 4개 운전점 최대)")
    quant = {}
    for bits in (12, 14, 16):
        sel = [x for x in nrows if x["case"] == f"양자화 {bits}비트"]
        quant[bits] = dict(ih_pp=max(x["ih_pp"] for x in sel), vbus_pp=max(x["vbus_pp"] for x in sel), m_pp=max(x["m_pp"] for x in sel))
        print(f"   양자화 {bits}비트(전 범위 측정, 잡음 없음): i_h 변동 {quant[bits]['ih_pp']:.3f} A pp, 버스 {quant[bits]['vbus_pp']:.3f} V pp, 변조율 {quant[bits]['m_pp']:.4f}")
    # 시험 격자 기본 집합
    base, _ = sets_sw()
    cases = [(t, v, a, b, n, p) for v in st.V_ALL for n, p in base.items()
             for t, steps in ((1, st.T1_STEPS), (2, st.T2_STEPS)) for a, b in steps]
    variants = {"12비트 양자화(전 범위)": sensor_set(bits=12, ranges=SENS_RANGE_FULL),
                "요구 사양(16비트·잡음)": sensor_set(bits=16, noise=SENS_NOISE_REQ),
                "요구 사양 + 오차(전류 낮게·전압 높게)": sensor_set(bits=16, noise=SENS_NOISE_REQ, sign=CUR_LOW_V_HIGH),
                "요구 사양 + 오차(전류 높게·전압 낮게)": sensor_set(bits=16, noise=SENS_NOISE_REQ, sign=-CUR_LOW_V_HIGH)}
    js = [(t, v, a, b, p, 0, None, dict(set=n, variant=name, _sensors=s.tolist(), _seed=1000 + i))
          for name, s in variants.items() for i, (t, v, a, b, n, p) in enumerate(cases)]
    rows = pmap(js)
    summ = {}
    for name in variants:
        sel = [r for r in rows if r["variant"] == name]
        fails = [r for r in sel if not r["pass_"]]
        reasons = {}
        for r in fails:
            for k, bad in [("tail_ripple>0.1V", r["tail_ripple_V"] > .1), ("internal_osc", r["tail_ih_pp_A"] > st.TAIL_IH_PP_A or r["tail_m_pp"] > st.TAIL_M_PP),
                           ("current", max(r["path_inst"], r["bridge_inst"]) > (T1_INST_A if r["tier"] == 1 else T2_INST_A)),
                           ("ports", bool(r["ports_violated"])), ("final_or_recovery", abs(r["vbus_end"] - 400) > 4 or (r["tier"] == 1 and (r["recovery_s"] is None or r["recovery_s"] > 1e-3)))]:
                if bad:
                    reasons[k] = reasons.get(k, 0) + 1
        g640 = [r for r in sel if r["vbat"] >= 640]
        summ[name] = dict(total=len(sel), passed=len(sel) - len(fails), fail_reasons=reasons,
                          total_640plus=len(g640), passed_640plus=sum(r["pass_"] for r in g640),
                          fails=[(r["tier"], r["set"], r["vbat"], r["p0"], r["p1"], round(r["tail_ih_pp_A"], 3), round(r["tail_m_pp"], 4),
                                  round(r["vbus_end"], 2)) for r in fails],
                          max_inst_A=max(max(r["path_inst"], r["bridge_inst"]) for r in sel),
                          max_tail_ripple_V=max(r["tail_ripple_V"] for r in sel), max_tail_ih_pp_A=max(r["tail_ih_pp_A"] for r in sel),
                          max_tail_m_pp=max(r["tail_m_pp"] for r in sel), vbus_end_range=(min(r["vbus_end"] for r in sel), max(r["vbus_end"] for r in sel)),
                          max_droop_V=max(r["droop"] for r in sel), max_link_avg_A=max(r["link_avg"] for r in sel))
        x = summ[name]
        print(f"   {name:24s}: {x['passed']}/{x['total']} 통과, 순시 최대 {x['max_inst_A']:.2f} A, 마지막 1 ms 리플 최대 {x['max_tail_ripple_V']:.3f} V, "
              f"i_h 변동 최대 {x['max_tail_ih_pp_A']:.3f} A, 변조율 변동 최대 {x['max_tail_m_pp']:.4f}, 최종 버스 {x['vbus_end_range'][0]:.2f}–{x['vbus_end_range'][1]:.2f} V"
              + (f", 실패 사유 {reasons}" if fails else ""))
    noise_only = summ["요구 사양(16비트·잡음)"]
    verdict("요구 사양 센서(16비트, 전압 5 mV·전류 20 mA 잡음)에서 기본 집합 168건 전부 통과",
            noise_only["passed"] == noise_only["total"])
    err = [summ[n] for n in variants if n.startswith("요구 사양 +")]
    verdict("이득·오프셋 오차를 더해도 보장 범위(640–920 V) 144건 전부 통과",
            all(x["passed_640plus"] == x["total_640plus"] for x in err))
    return dict(noise_gain=gains, quantization=quant, requirement=dict(bits=16, range=SENS_RANGE.tolist(), noise=SENS_NOISE_REQ.tolist(),
                gain_err=SENS_GAIN_ERR.tolist(), offset_err=SENS_OFFSET_ERR.tolist(), channels=SENS_NAMES),
                summary=summ, noise_rows=nrows, rows=[{k: v for k, v in r.items()} for r in rows])


def _err_parts(cur=None, volt=None, link=None):
    """채널 묶음별 이득·오프셋 오차(잡음·양자화 없음)."""
    s = sensor_set()
    for chans, sg in (((0, 3), cur), ((1, 2, 4), volt), ((5,), link)):
        if sg is not None:
            for c in chans:
                s[c, 0] += sg * SENS_GAIN_ERR[c]; s[c, 1] = sg * SENS_OFFSET_ERR[c]
    return s


def part_sensor_diag():
    """sensors 파트에서 보장 범위(640 V 이상) 사례가 실패한 경우의 원인 분리. 잡음을 빼고 오차를 채널 묶음별로
    나누어 넣고, DAB 데드타임 또는 H-브리지 데드타임을 없앤 경우와 비교한다."""
    prev = load_json("E12", "sensors")
    bad = [r for r in prev["rows"] if r["variant"].startswith("요구 사양 +") and r["vbat"] >= 640 and not r["pass_"]]
    keys = sorted({(r["tier"], r["set"], r["vbat"], r["p0"], r["p1"], r["variant"]) for r in bad})
    if not keys:
        print("   보장 범위 실패 사례 없음"); return dict(cases=[])
    base, _ = sets_sw()
    js = []
    for t, n, v, a, b, var in keys:
        sg = CUR_LOW_V_HIGH if "전류 낮게" in var else -CUR_LOW_V_HIGH
        full = _err_parts(cur=sg[0], volt=sg[1], link=sg[5])
        for tag, s, sw in [("오차 전체(잡음 없음)", full, None), ("전류 센서 오차만", _err_parts(cur=sg[0]), None),
                           ("전압 센서 오차만", _err_parts(volt=sg[1]), None), ("링크전류 센서 오차만", _err_parts(link=sg[5]), None),
                           ("오차 전체 + DAB 데드타임 0", full, dict(td_dab=0.)),
                           ("오차 전체 + H-브리지 데드타임 0·보상 없음", full, dict(td_h=0., deadtime_comp="none"))]:
            js.append((t, v, a, b, base[n], 0, sw, dict(set=n, variant=var, diag=tag, _sensors=s.tolist(), _seed=1)))
    rows = pmap(js)
    for r in rows:
        print(f"   {r['vbat']:.0f} V {r['p0']/1e3:g}→{r['p1']/1e3:g} kW({r['set']}) {r['diag']:24s}: i_h 변동 {r['tail_ih_pp_A']:.3f} A"
              + (f" ({r['tail_ih_freq_hz']/1e3:.2f} kHz)" if r["tail_ih_freq_hz"] else "") + f", {'통과' if r['pass_'] else '실패'}")
    return dict(cases=[list(k) for k in keys], rows=rows)


DT_SCALES = (1., .8, .7, .6, .5)
DT_UNCERTAINTY = {"공칭": {}, "L_h ×0.9": "Lh0.9", "L_h ×1.1": "Lh1.1",
                  "선형 C_oss 0.5 nF(표 1 nF)": dict(coss_h=.5e-9, table_cq=1e-9), "선형 C_oss 2 nF(표 1 nF)": dict(coss_h=2e-9, table_cq=1e-9),
                  "비선형 C_Q 1 nF, 실제 곡선 표": dict(coss_nonlinear=True), "비선형 C_Q 1 nF, 표 ×0.8": dict(coss_nonlinear=True, table_cq=.8e-9),
                  "비선형 C_Q 1 nF, 선형 모양 표": dict(coss_nonlinear=True, table_nonlinear=False),
                  "비선형 C_Q 0.5 nF, 실제 곡선 표": dict(coss_nonlinear=True, coss_h=.5e-9), "비선형 C_Q 2 nF, 실제 곡선 표": dict(coss_nonlinear=True, coss_h=2e-9)}
DT_CASES = [(2, 632., 25000., 1000.), (2, 640., 25000., 1000.), (2, 660., 25000., 1000.), (2, 920., 25000., 1000.),
            (2, 640., 25000., 5000.), (2, 920., 25000., 5000.), (1, 640., 25000., 15000.),
            (2, 632., 1000., 25000.), (2, 640., 1000., 25000.)]


def part_deadtime_robust():
    """데드타임 보상의 강건성과 경부하 보상 비율 κ 선정. 교정표(전류별 전이 오차) × κ(i)를 보상한다
    (κ(i): 예측 전류 20 A 이하에서 κ, 80 A에서 1로 선형 증가).
    경부하(25→1 kW 뒤 1 kW, 리플 극값 전류가 0 부근)에서는 보상이 실제 오차보다 큰 전류 구간이 생기면 데드타임의
    수동적(저항성) 성질이 뒤집혀 지속 진동이 생길 수 있다. 불확도 10종(필터 L_h ±10 %, 선형·비선형 출력용량과 교정 오차)
    × κ 5종 × 9개 사례(경부하 4, 중부하 3, 정격 2)로 진동과 판정을 확인한다. 비선형 출력용량은 C(v) = C0·(1 + v/5 V)^(−0.5)."""
    js = []
    for k in DT_SCALES:
        for uname, u in DT_UNCERTAINTY.items():
            p = NOMINAL; sw = dict(comp_scale=k)
            if u == "Lh0.9":
                p = replace(NOMINAL, Lh=NOMINAL.Lh * .9)
            elif u == "Lh1.1":
                p = replace(NOMINAL, Lh=NOMINAL.Lh * 1.1)
            else:
                sw.update(u)
            for t, v, a, b in DT_CASES:
                js.append((t, v, a, b, p, 0, sw, dict(scale=k, uncertainty=uname)))
    rows = pmap(js)
    summ = {}
    for k in DT_SCALES:
        sel = [r for r in rows if r["scale"] == k]
        osc = [r for r in sel if r["tail_ih_pp_A"] > .1]
        full = [r for r in sel if r["p0"] == 1000. and r["p1"] == 25000.]
        summ[str(k)] = dict(scale=k, total=len(sel), passed=sum(r["pass_"] for r in sel), oscillating=len(osc),
                            max_tail_ih_pp_A=max(r["tail_ih_pp_A"] for r in sel),
                            fails=[(r["uncertainty"], r["vbat"], r["p0"], r["p1"], round(r["tail_ih_pp_A"], 2), r["tail_ih_freq_hz"]) for r in sel if not r["pass_"]],
                            full_load_max_inst_A=max(max(r["path_inst"], r["bridge_inst"]) for r in full),
                            full_load_max_droop_V=max(r["droop"] for r in full))
        x = summ[str(k)]
        print(f"   κ = {k}: {x['passed']}/{x['total']} 통과, 진동(> 0.1 A pp) {x['oscillating']}건, 최대 {x['max_tail_ih_pp_A']:.2f} A pp, "
              f"정격 사례 순시 최대 {x['full_load_max_inst_A']:.2f} A·강하 최대 {x['full_load_max_droop_V']:.2f} V"
              + (f", 실패 {x['fails'][:6]}" if x["fails"] else ""))
    clean = [k for k in DT_SCALES if summ[str(k)]["passed"] == summ[str(k)]["total"] and summ[str(k)]["oscillating"] == 0]
    print(f"   전 불확도에서 진동 없이 통과한 κ: {clean}")
    verdict(f"채택 κ = {SW_DEFAULT['comp_scale']}에서 불확도 10종 × 9개 사례 전부 통과, 지속 진동 없음",
            str(SW_DEFAULT["comp_scale"]) in summ and summ[str(SW_DEFAULT["comp_scale"])]["passed"] == summ[str(SW_DEFAULT["comp_scale"])]["total"]
            and summ[str(SW_DEFAULT["comp_scale"])]["oscillating"] == 0)
    return dict(summary=summ, clean_scales=clean, rows=rows)


COMP_SCHEDULES = {"고정 κ = 1.0": dict(comp_scale=1.), "고정 κ = 0.6": dict(comp_full_from_A=1e9, comp_full_at_A=2e9),
                  "0.6 → 1.0, 15→25 A": dict(comp_full_from_A=15., comp_full_at_A=25.), "0.6 → 1.0, 20→80 A(채택)": {}}


def part_comp_schedule():
    """데드타임 보상 비율의 전류 스케줄 비교. 경부하 진동(L_h +10 %, 25→1 kW), 중부하(25→5 kW), 데드타임 100 ns의
    640 V 정격 부하(전류 여유), 632 V 정격 부하에서 네 가지 스케줄을 비교한다."""
    N = NOMINAL
    cases = [("경부하 L_h ×1.1", 2, 640., 25000., 1000., replace(N, Lh=N.Lh * 1.1), {}),
             ("중부하 25→5 kW", 2, 640., 25000., 5000., N, {}),
             ("중부하 25→5 kW, L_h ×1.1", 2, 640., 25000., 5000., replace(N, Lh=N.Lh * 1.1), {}),
             ("데드타임 100 ns, Tier-2", 2, 640., 1000., 25000., N, dict(td_h=100e-9)),
             ("데드타임 100 ns, Tier-1 +3 µs", 1, 640., 15000., 25000., replace(N, delay=N.delay + 3e-6), dict(td_h=100e-9)),
             ("632 V Tier-2 +3 µs", 2, 632., 1000., 25000., replace(N, delay=N.delay + 3e-6), {})]
    js = [(t, v, a, b, p, 0, dict(sw, **sch), dict(schedule=name, case=cname))
          for name, sch in COMP_SCHEDULES.items() for cname, t, v, a, b, p, sw in cases]
    rows = pmap(js)
    for name in COMP_SCHEDULES:
        sel = [r for r in rows if r["schedule"] == name]
        print(f"   {name:20s}: " + ", ".join(f"{r['case']} {'통과' if r['pass_'] else '실패'}(진동 {r['tail_ih_pp_A']:.2f} A, 강하 {r['droop']:.1f} V)" for r in sel))
    adopted = [r for r in rows if r["schedule"] == "0.6 → 1.0, 20→80 A(채택)"]
    verdict("채택 스케줄은 6개 비교 사례 전부 통과", all(r["pass_"] for r in adopted))
    return dict(rows=rows)


def part_delay():
    extras = [3.0, 3.5, 3.8, 4.0, 4.1, 4.2, 4.5]
    js = [(1, v, a, b, replace(NOMINAL, delay=round((NOMINAL.delay + e * 1e-6) / 1e-7) * 1e-7), 0, None, dict(added_us=e))
          for v in (640, 920) for e in extras for a, b in [(15000, 25000), (25000, 15000), (0, 10000)]]
    rows = pmap(js)
    bound = {}
    for v in (640, 920):
        ok = [e for e in extras if all(r["pass_"] for r in rows if r["vbat"] == v and r["added_us"] == e)]
        bad = [e for e in extras if e not in ok]
        bound[str(v)] = dict(last_pass_added_us=max([e for e in ok if not bad or e < min(bad)], default=None),
                             first_fail_added_us=min(bad, default=None))
        print(f"   {v} V: +{bound[str(v)]['last_pass_added_us']} µs 통과, +{bound[str(v)]['first_fail_added_us']} µs 실패")
    verdict("스위칭 모델에서도 추가 지연 +3.0 µs 통과(640·920 V)", all(b["last_pass_added_us"] is not None and b["last_pass_added_us"] >= 3.0
                                                                  for b in bound.values()))
    return dict(boundary=bound, rows=rows)


def part_corners():
    js = []
    for s in itertools.product([-1, 1], repeat=7):
        for t in (1, 2):
            p = replace(NOMINAL, **{f: getattr(NOMINAL, f) * (1 + .1 * k) for f, k in zip(st.FIELDS, s)})
            if t == 1:
                p = replace(p, delay=NOMINAL.delay + 3e-6)
            a, b = (15000, 25000) if t == 1 else (1000, 25000)
            js.append((t, 640, a, b, p, 0, None, dict(signs=list(s))))
    rows = pmap(js)
    out = {}
    for t in (1, 2):
        sel = [r for r in rows if r["tier"] == t]
        w = max(sel, key=lambda r: max(r["path_inst"], r["bridge_inst"]))
        out[f"T{t}"] = dict(total=len(sel), passed=sum(r["pass_"] for r in sel), worst=w,
                            over_rating_100A=sum(max(r["path_inst"], r["bridge_inst"]) > 100 for r in sel))
        print(f"   복합 코너 Tier-{t}: {out[f'T{t}']['passed']}/{len(sel)} 통과, 순시 최대 {max(w['path_inst'], w['bridge_inst']):.2f} A, "
              f"100 A 초과 {out[f'T{t}']['over_rating_100A']}건")
    return dict(summary=out, rows=rows)


def part_sequences():
    sets = {"nominal": NOMINAL, "Lhx0.9": replace(NOMINAL, Lh=NOMINAL.Lh * .9), "Lx1.1": replace(NOMINAL, L=NOMINAL.L * 1.1),
            "delay+3.0us": replace(NOMINAL, delay=NOMINAL.delay + 3e-6)}
    prof = {"up_ramp": 1, "up_stair": 2, "down_ramp": 3, "down_stair": 4}
    js = []
    for v in (632., 640., 920.):
        for n, p in sets.items():
            for fn, k in prof.items():
                p0 = st.SEQUENCES[fn](0.)
                js.append((1, v, p0, p0, p, k, None, dict(set=n, sequence=fn)))
    rows = pmap(js)
    w = max(rows, key=lambda r: max(r["path_inst"], r["bridge_inst"]))
    print(f"   계약 시퀀스: {sum(r['pass_'] for r in rows)}/{len(rows)} 통과, 순시 최대 {max(w['path_inst'], w['bridge_inst']):.2f} A")
    return dict(passed=sum(r["pass_"] for r in rows), total=len(rows), worst=w, rows=rows)


SENS_CASES = [(2, 640, 1000, 25000, 0.), (1, 640, 15000, 25000, 3e-6), (2, 700, 1000, 25000, 0.), (2, 920, 1000, 25000, 0.),
              (2, 640, 25000, 1000, 0.), (2, 920, 25000, 1000, 0.), (1, 800, 5000, -5000, 0.), (1, 788, 0, 10000, 0.)]
SENS_VARIANTS = {"기준": {}, "DAB 전류비 보정 없음(L −10 % 기준 앞먹임)": dict(dab_estimator=False),
                 "DAB 공칭 L 기준 앞먹임": dict(dab_estimator=False, dab_Lmin=1.), "데드타임 25 ns": dict(td_h=25e-9), "데드타임 100 ns": dict(td_h=100e-9),
                 "출력용량 0.5 nF(보상표 1 nF 기준)": dict(coss_h=.5e-9, table_cq=1e-9), "출력용량 2 nF(보상표 1 nF 기준)": dict(coss_h=2e-9, table_cq=1e-9),
                 "데드타임 보상 없음": dict(deadtime_comp="none"), "전류지령 비례 보상(±20 A)": dict(deadtime_comp="linear"),
                 "DAB 데드타임 200 ns": dict(td_dab=200e-9), "적분간격 2.5 ns": dict(dt=2.5e-9), "적분간격 1.25 ns": dict(dt=1.25e-9)}


def part_sensitivity():
    js = [(t, v, a, b, replace(NOMINAL, delay=NOMINAL.delay + d), 0, sw, dict(variant=name))
          for name, sw in SENS_VARIANTS.items() for t, v, a, b, d in SENS_CASES]
    rows = pmap(js)
    summ = {}
    for name in SENS_VARIANTS:
        sel = [r for r in rows if r["variant"] == name]
        summ[name] = dict(passed=sum(r["pass_"] for r in sel), total=len(sel),
                          max_inst_A=max(max(r["path_inst"], r["bridge_inst"]) for r in sel),
                          max_droop_V=max(r["droop"] for r in sel),
                          fails=[(r["vbat"], r["p0"], r["p1"], r["ports_violated"], round(r["droop"], 2)) for r in sel if not r["pass_"]])
        print(f"   {name:24s}: {summ[name]['passed']}/{summ[name]['total']} 통과, 순시 최대 {summ[name]['max_inst_A']:.2f} A, "
              f"최대 강하 {summ[name]['max_droop_V']:.2f} V" + (f", 실패 {summ[name]['fails']}" if summ[name]["fails"] else ""))
    base = {(r["vbat"], r["p0"], r["p1"]): r for r in rows if r["variant"] == "기준"}
    conv = {}
    for name in ("적분간격 2.5 ns", "적분간격 1.25 ns"):
        fine = {(r["vbat"], r["p0"], r["p1"]): r for r in rows if r["variant"] == name}
        conv[name] = dict(path_inst_A=max(abs(base[k]["path_inst"] - fine[k]["path_inst"]) for k in base),
                          bridge_inst_A=max(abs(base[k]["bridge_inst"] - fine[k]["bridge_inst"]) for k in base),
                          droop_V=max(abs(base[k]["droop"] - fine[k]["droop"]) for k in base),
                          verdict_changes=sum(base[k]["pass_"] != fine[k]["pass_"] for k in base))
    c = max(max(v["path_inst_A"], v["bridge_inst_A"]) for v in conv.values())
    verdict("적분간격 5 → 2.5·1.25 ns에서 순시 경로·필터 전류 차 < 0.1 A, 판정 변화 없음",
            c < .1 and all(v["verdict_changes"] == 0 for v in conv.values()), f"최대 {c:.3f} A")
    return dict(summary=summ, timestep_convergence=conv, rows=rows)


def part_linear():
    """평균모델 선형화로 본 변조율 이득 오차의 영향(링크전압 감지·PWM 이득 오차, 데드타임 보상 오차의 선형 근사).
    제어기 출력 m에 g를 곱해 플랜트에 넣는다(예측기는 g를 모른다). 이득 오차가 있으면 정상상태의 제어기 내부
    상태가 달라지므로 그 고정점(아래 fixed_rho)에서 야코비안을 계산한다. 내부 변조율 m_eq/g가 한계 0.95를
    넘거나 전류지령이 포화하는 운전점은 포화 없는 고정점이 없어 제외하고 따로 기록한다."""
    from controller_adopted import StageBController
    from linearize import period_map_ctrl, NHIST
    from model_stage_b import equilibrium

    class Mod(StageBController):
        def __init__(self, *a, g=1., **k):
            super().__init__(*a, **k); self.g = g
        def step(self, x):
            u = super().step(x)                       # u_prev = [m, i_link] (예측기는 이득 오차를 모른다)
            return np.array([u[0] * self.g, u[1]])

    def jac(z, v, P, ctrl):
        sc = np.maximum(np.abs(z), 1e-3) * 1e-6
        J = np.empty((len(z), len(z)))
        for i in range(len(z)):
            e_ = np.zeros(len(z)); e_[i] = sc[i]
            J[:, i] = (period_map_ctrl(z + e_, v, P, NOMINAL, ctrl) - period_map_ctrl(z - e_, v, P, NOMINAL, ctrl)) / (2 * sc[i])
        return J

    def fixed_rho(v, P, g):
        """고정점을 직접 구성한다: 플랜트는 평형점 x_eq(플랜트가 받는 지령이 u_eq이므로), 제어기 내부 변조율은
        m_eq/g, 적분기 q·q_link는 그 지령을 내도록 정한다. 구성한 점이 한 주기 사상의 고정점인지 잔차로 확인한다."""
        x, u = equilibrium(v, P, NOMINAL)
        mi = u[0] / g
        if abs(mi) >= CP.modulation_max:
            return None
        ctrl = Mod(K_ADOPTED, CP, v, predict=True, g=g); ctrl.reset(x, u); ctrl.u_prev = np.array([mi, u[1]])
        xs = ctrl._predict(x); K = K_ADOPTED
        iref = xs[3] + CP.inner_tau / CP.Lh * (mi * xs[4] - xs[1] - CP.Rh * xs[3])
        if abs(iref) >= CP.reference_max:
            return None
        ctrl.q = -(iref + K[0] * xs[0] + K[1] * xs[1] + K[2] * xs[2] + K[3] * xs[3]) / K[4]
        ctrl.qlink = (u[1] - mi * xs[3]) / (CP.Clink * ctrl.wlink ** 2)
        z = np.concatenate([x, ctrl.state(), np.tile(u, NHIST)])
        res = float(np.max(np.abs(period_map_ctrl(z, v, P, NOMINAL, ctrl) - z) / np.maximum(np.abs(z), 1.)))
        lam = np.linalg.eigvals(jac(z, v, P, ctrl)); i = int(np.argmax(np.abs(lam)))
        return float(np.abs(lam[i])), float(abs(np.angle(lam[i])) / (2 * np.pi * CP.Ts)), res

    gain = []
    for g in (.7, .8, .9, 1., 1.1, 1.2, 1.3):
        pts = []; skipped = []
        for v in (632., 640., 700., 788., 860., 920.):
            for P in (-3200., 0., 5000., 15000., 25000.):
                o = fixed_rho(v, P, g)
                if o is None:
                    skipped.append((v, P))
                else:
                    pts.append(dict(vbat=v, power=P, rho=o[0], mode_hz=o[1], fixed_point_residual=o[2]))
        w = max(pts, key=lambda d: d["rho"])
        gain.append(dict(g=g, rho=w["rho"], mode_hz=w["mode_hz"], vbat=w["vbat"], power=w["power"], points=len(pts),
                         skipped_saturated=skipped, max_fixed_point_residual=max(d["fixed_point_residual"] for d in pts)))
        assert gain[-1]["max_fixed_point_residual"] < 1e-9, gain[-1]["max_fixed_point_residual"]
        print(f"   변조율 이득 ×{g}: 최대 스펙트럼 반경 {w['rho']:.4f} ({w['mode_hz']/1e3:.2f} kHz, {w['vbat']:.0f} V, {w['power']/1e3:g} kW), "
              f"운전점 {len(pts)}개" + (f", 포화로 제외 {skipped}" if skipped else ""))
    verdict("채택 설계는 변조율 이득 ±30 %의 고정점에서 국소 안정", all(x["rho"] < 1 for x in gain))
    return dict(modulation_gain=gain)


def part_model_checks():
    """스위칭 모델 자체의 검산: 에너지 보존(미분방정식 구현), SPS 전달식, 평균모델 정상점."""
    from model_stage_b import equilibrium
    rows = []
    for v, a, b in [(640., 1000., 25000.), (920., 25000., 1000.), (800., 5000., -5000.), (700., 25000., 25000.)]:
        r = simulate_switching(v, a, b, NOMINAL, CP, K_ADOPTED, duration=.004)
        rows.append(dict(vbat=v, p0=a, p1=b, energy_residual_W=r["energy_residual_W"]))
    eres = max(x["energy_residual_W"] for x in rows)
    verdict("에너지 보존 잔차(스위칭 함수 포함 미분방정식) < 1e-4 W", eres < 1e-4, f"{eres:.1e} W")
    sps = []
    for v, P in [(640., 25000.), (700., 25000.), (788., 25000.), (920., 25000.), (640., -3200.), (920., -3200.)]:
        r = simulate_switching(v, P, P, NOMINAL, CP, K_ADOPTED, duration=.002)
        R = r["rec"]; tail = r["t"] >= r["t"][-1] - .5e-3
        ph = R[tail, 16].mean(); vb = R[tail, 0].mean(); il = R[tail, 4].mean()
        k = NOMINAL.turns * vb / (2 * np.pi * NOMINAL.fs * NOMINAL.Ldab)
        il_f = k * ph * (1 - abs(ph) / np.pi)
        x0, u0 = equilibrium(v, P, NOMINAL)
        sps.append(dict(vbat=v, power=P, phase_deg=float(np.degrees(ph)), ilink_sim=float(il), ilink_sps_formula=float(il_f),
                        ilink_avg_model=float(x0[5]), ip_sim=float(R[tail, 1].mean()), ip_avg_model=float(x0[0]),
                        vs_sim_minus_avg=float(R[tail, 0].mean() - 400)))
        print(f"   {v:.0f} V {P/1e3:g} kW: 위상 {np.degrees(ph):+.2f}°, 링크전류 {il:+.2f} A (SPS 식 {il_f:+.2f}, 평균모델 정상점 {x0[5]:+.2f}), "
              f"경로전류 {R[tail, 1].mean():.2f} A (평균모델 {x0[0]:.2f})")
    dev = max(abs(x["ilink_sim"] - x["ilink_avg_model"]) for x in sps)
    verdict("정상상태 링크전류가 평균모델 정상점과 0.5 A 이내", dev < .5, f"최대 차 {dev:.2f} A")
    devp = max(abs(x["ip_sim"] - x["ip_avg_model"]) for x in sps)
    verdict("정상상태 경로전류가 평균모델 정상점과 0.5 A 이내", devp < .5, f"최대 차 {devp:.2f} A")
    # 과도 중 변압기 전류의 직류 편류(주기 평균 i_L): 위상 갱신 방식 확인(양·음 위상, 부호 반전 포함)
    bias = []
    for v, a, b in [(640., 1000., 25000.), (640., 25000., 1000.), (920., 1000., 25000.), (920., 25000., 1000.),
                    (800., 5000., -5000.), (632., -3200., 25000.)]:
        r = simulate_switching(v, a, b, NOMINAL, CP, K_ADOPTED, duration=.004)
        R = r["rec"]; t = r["t"]; pre = (t < 1e-3) & (t >= 0); post = t >= 1e-3
        late = (t >= 1.3e-3) & (t < 1.6e-3)
        ph = np.degrees(R[post, 16])
        bias.append(dict(vbat=v, p0=a, p1=b, dc_bias_pre_A=float(np.abs(R[pre, 19]).max()),
                         dc_bias_post_A=float(np.abs(R[post, 19]).max()), iL_peak_A=float(R[post, 13].max()),
                         dc_bias_late_A=float(abs(R[late, 19].mean())), phase_range_deg=(float(ph.min()), float(ph.max()))))
        x = bias[-1]; x["ratio_to_peak"] = x["dc_bias_post_A"] / x["iL_peak_A"]
        print(f"   {v:.0f} V {a/1e3:g}→{b/1e3:g} kW: 위상 {ph.min():+.1f}~{ph.max():+.1f}°, 변압기 전류 주기 평균 최대 "
              f"{x['dc_bias_post_A']:.3f} A(피크 {x['iL_peak_A']:.2f} A의 {x['ratio_to_peak']*100:.1f} %), 스텝 후 0.3–0.6 ms 평균 "
              f"{x['dc_bias_late_A']:.3f} A, 스텝 전 {x['dc_bias_pre_A']:.4f} A")
    bmax = max(x["dc_bias_post_A"] for x in bias); rmax = max(x["ratio_to_peak"] for x in bias)
    verdict("과도 중 변압기 전류 주기 평균(직류 편류)이 피크의 10 % 미만(양·음 위상, 부호 반전 포함)", rmax < .1,
            f"최대 {bmax:.3f} A, 피크 대비 최대 {rmax*100:.1f} %")
    return dict(energy=rows, max_energy_residual_W=eres, sps=sps, dc_bias=bias, max_dc_bias_A=bmax, max_dc_bias_ratio=rmax)


def part_figures():
    from plotstyle import korean, COLOR as C
    from model_stage_b import simulate
    from controller_adopted import make
    plt = korean()
    # (a) 640 V Tier-2 1→25 kW: 스위칭 vs 평균모델
    r = simulate_switching(640., 1000., 25000., NOMINAL, CP, K_ADOPTED, capture=[0.9e-3, 2.5e-3, 4])
    w = r["wave"]
    ra = simulate(640., 1000., 25000., p=NOMINAL, K=K_ADOPTED, control_p=CP, duration=.003, dt=2e-7, keep_trace=True,
                  controller=make(640., "adopted"))
    fig, ax = plt.subplots(1, 3, figsize=(7.6, 2.6))
    tt = (w[:, 0] - 1e-3) * 1e3; ta = (ra["t"] - 1e-3) * 1e3
    ax[0].plot(tt, w[:, 1], color=C["blue"], lw=.8, label="스위칭 모델")
    ax[0].plot(ta, ra["x"][:, 0], color=C["orange"], lw=1, ls="--", label="평균모델")
    ax[0].axhline(100, color=C["red"], ls=":", lw=.9)
    ax[0].set_title("(a) 경로전류 i_p"); ax[0].set_ylabel("A")
    ax[1].plot(tt, w[:, 4], color=C["blue"], lw=.4, label="스위칭 모델(리플 포함)")
    ax[1].plot(ta, ra["x"][:, 3], color=C["orange"], lw=1, ls="--", label="평균모델")
    ax[1].axhline(100, color=C["red"], ls=":", lw=.9); ax[1].set_title("(b) 브리지 필터전류 i_h")
    ax[2].plot((r["t"] - 1e-3) * 1e3, r["rec"][:, 0], color=C["blue"], lw=1, label="스위칭(주기 평균)")
    ax[2].plot(ta, ra["x"][:, 2], color=C["orange"], lw=1, ls="--", label="평균모델")
    ax[2].axhline(392, color=C["red"], ls=":", lw=.9); ax[2].set_ylim(390, 404); ax[2].set_title("(c) 버스전압")
    for a_ in ax:
        a_.set_xlim(-.1, 1.5); a_.set_xlabel("스텝 후 시간 (ms)")
    ax[0].legend(loc="lower right", fontsize=7); ax[1].legend(loc="lower right", fontsize=7)
    fig.suptitle("640 V, 1→25 kW(Tier-2): 스위칭 모델과 평균모델", fontsize=9)
    fig.tight_layout(); fig.savefig(outdir("E12") / "E12_transient_640V.png"); plt.close(fig)
    # (b) 700 V 25 kW 정상상태 파형(2주기)
    r = simulate_switching(700., 25000., 25000., NOMINAL, CP, K_ADOPTED, duration=.002, capture=[1.99e-3, 2e-3, 1])
    w = r["wave"]; tt = (w[:, 0] - w[0, 0]) * 1e6
    fig, ax = plt.subplots(3, 1, figsize=(6.4, 4.6), sharex=True)
    ax[0].plot(tt, w[:, 7] * w[:, 5], color=C["gray"], lw=.8); ax[0].set_ylabel("v_hb (V)")
    ax2 = ax[0].twinx(); ax2.plot(tt, w[:, 4], color=C["blue"], lw=1); ax2.set_ylabel("i_h (A)"); ax2.grid(False)
    ax[1].plot(tt, w[:, 8] * w[:, 3], color=C["gray"], lw=.8); ax[1].set_ylabel("v_p (V)")
    ax3 = ax[1].twinx(); ax3.plot(tt, w[:, 6], color=C["orange"], lw=1); ax3.set_ylabel("i_L (A)"); ax3.grid(False)
    ax[2].plot(tt, (w[:, 5] - w[:, 5].mean()) * 1e3, color=C["green"], lw=1)
    ax[2].set_ylabel("v_link 편차 (mV)"); ax[2].set_xlabel("시간 (µs)")
    ax[0].set_title("700 V, 25 kW 정상상태(2주기)", fontsize=9)
    fig.tight_layout(); fig.savefig(outdir("E12") / "E12_steady_700V.png"); plt.close(fig)
    print("   → 그림: results/E12/E12_transient_640V.png, E12_steady_700V.png")


PARTS = dict(model_checks=part_model_checks, ripple=part_ripple, linear=part_linear, grid=part_grid, convergence=part_convergence,
             dab_limit=part_dab_limit, sensors=part_sensors, sensor_diag=part_sensor_diag, deadtime_robust=part_deadtime_robust, comp_schedule=part_comp_schedule, delay=part_delay, corners=part_corners, sequences=part_sequences,
             sensitivity=part_sensitivity, figures=part_figures)

if __name__ == "__main__":
    todo = sys.argv[1:] or list(PARTS)
    print("[E12] Stage B 스위칭 모델 검증")
    print(f"   스위칭 파라미터: {SW_DEFAULT}")
    for name in todo:
        t0 = time.time(); print(f"-- {name}", flush=True)
        res = PARTS[name]()
        if res is not None:
            res["switching_parameters"] = SW_DEFAULT
            save_json("E12", name, res)
        print(f"   ({time.time() - t0:.0f} s)", flush=True)
