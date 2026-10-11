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
  채택 제어기 이득·예측 구조는 평균모델과 같고, 변조기에 모델 기반 데드타임 보상(예측 전류·리플 극값에서의
  전이별 오차, 출력용량 1 nF 가정)을 두고, DAB 위상 한계는 누설 인덕턴스 −10 %에서도 링크 정격을 지키도록
  정한다. DAB 손실은 평균모델과 같은 효율 0.96(직전 주기 평균 전력 기준, 권선저항 손실 포함)이다.

■ 구성
  model_checks 모델 검산: 에너지 보존 잔차, SPS 전달식·평균모델 정상점과의 일치, 과도 중 변압기 직류 편류
  ripple      정상상태(−3.2·0·25 kW, 632–920 V)의 필터전류 리플, 변압기 전류, 링크·버스 리플, ZVS 조건
  linear      평균모델 선형화: 변조율 이득 오차(±10–30 %)의 영향(이득 오차가 있는 고정점에서 선형화)
  grid        Tier-1·Tier-2 격자(평균모델 E5와 같은 스텝·전압, 공차 17종 — DAB 시정수 대신 누설 인덕턴스 ±10 %)
  convergence 격자 전체를 적분간격 2.5 ns로 다시 계산해 판정·전류 최댓값의 수렴 확인
  dab_limit   DAB 위상 한계의 근거: 누설 인덕턴스 ±10 % × 위상 한계 기준(공칭 L / L −10 %)
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

■ 실행   python E12_switching_verification.py              (전체, 2코어 약 50분)
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
               modulation_pwm_peak=m_pwm, dc_bias_A=float(np.abs(R[pos, 19]).max()),
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
    r = simulate_switching(float(vbat), float(a), float(b), p, CP, K_ADOPTED, predict=True, profile=profile, sw=sw)
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


def part_dab_limit():
    """DAB 위상 한계 기준의 근거. 위상 앞먹임으로만 링크전류를 제한하므로 실제 누설 인덕턴스가 공칭보다 작으면
    같은 위상에서 더 큰 전류가 흐른다. 공칭 L 기준 한계와 L −10 % 기준 한계(채택)를 비교한다."""
    js = []
    for v in (632., 640.):
        for k in (.9, 1., 1.1):
            for lmin in (1., .9):
                p = replace(NOMINAL, Ldab=NOMINAL.Ldab * k)
                for t, a, b in [(2, 1000, 25000), (1, 15000, 25000)]:
                    js.append((t, v, a, b, p, 0, dict(dab_Lmin=lmin), dict(Ldab_scale=k, dab_Lmin=lmin)))
    rows = pmap(js)
    out = []
    for k in (.9, 1., 1.1):
        for lmin in (1., .9):
            sel = [r for r in rows if r["Ldab_scale"] == k and r["dab_Lmin"] == lmin]
            o = dict(Ldab_scale=k, dab_Lmin=lmin, link_avg_max_A=max(r["link_avg"] for r in sel),
                     link_power_avg_max_W=max(r["link_power_avg"] for r in sel), passed=sum(r["pass_"] for r in sel), total=len(sel),
                     max_inst_A=max(max(r["path_inst"], r["bridge_inst"]) for r in sel),
                     rating_violations=sorted({v for r in sel for v in r["ports_violated"]}))
            out.append(o)
            print(f"   L_dab ×{k}, 위상 한계 기준 L ×{lmin}: 링크전류 최대 {o['link_avg_max_A']:.2f} A, 링크전력 최대 {o['link_power_avg_max_W']:.0f} W, "
                  f"{o['passed']}/{o['total']} 통과, 순시 최대 {o['max_inst_A']:.2f} A" + (f", 위반 {o['rating_violations']}" if o["rating_violations"] else ""))
    adopted = [o for o in out if o["dab_Lmin"] == .9]
    verdict("채택 위상 한계(L −10 % 기준)에서 L_dab ±10 % 모두 링크 정격(80 A, 8 kW) 이내",
            all(o["link_avg_max_A"] <= 80 and o["link_power_avg_max_W"] <= 8000 for o in adopted))
    # 용량 쪽: 위상 앞먹임 한계는 실제 L이 크면 낼 수 있는 링크전류를 줄인다. 25 kW 정상 운전에 필요한 링크전류와 비교
    from model_stage_b import equilibrium
    cap = []
    for v in (632., 640.):
        need = float(equilibrium(v, 25000., NOMINAL)[0][5])
        for k in (.9, 1., 1.1):
            for lmin in (1., .9):
                sel = [r for r in rows if r["vbat"] == v and r["Ldab_scale"] == k and r["dab_Lmin"] == lmin]
                c = min(NOMINAL.link_max, NOMINAL.power_max / NOMINAL.vlink) * lmin / k   # 한계 위상에서 실제로 흐르는 링크전류(근사)
                cap.append(dict(vbat=v, Ldab_scale=k, dab_Lmin=lmin, need_A=need, capacity_A=c,
                                passed=all(r["pass_"] for r in sel), vlink_min=min(r["vlink_min"] for r in sel)))
    for x in cap:
        if x["Ldab_scale"] == 1.1:
            print(f"   {x['vbat']:.0f} V 25 kW 필요 링크전류 {x['need_A']:.2f} A, L_dab ×1.1·기준 L ×{x['dab_Lmin']}의 링크전류 상한(근사) "
                  f"{x['capacity_A']:.2f} A → {'통과' if x['passed'] else '실패'}(링크전압 최저 {x['vlink_min']:.1f} V)")
    bad = [(x["vbat"], x["Ldab_scale"]) for x in cap if x["dab_Lmin"] == .9 and not x["passed"]]
    verdict("채택 위상 한계에서 L_dab +10 %일 때도 632·640 V 25 kW 운전 유지(용량)", not bad, f"실패 {bad}" if bad else "")
    return dict(summary=out, capacity=cap, rows=rows)


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
SENS_VARIANTS = {"기준": {}, "DAB 위상 한계 공칭 L 기준": dict(dab_Lmin=1.), "데드타임 25 ns": dict(td_h=25e-9), "데드타임 100 ns": dict(td_h=100e-9),
                 "출력용량 0.5 nF(보상 모델 1 nF)": dict(coss_h=.5e-9), "출력용량 2 nF(보상 모델 1 nF)": dict(coss_h=2e-9),
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
             dab_limit=part_dab_limit, delay=part_delay, corners=part_corners, sequences=part_sequences,
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
