"""[E34] 부품 정격 표(Stage A 25 kHz 설계 A25 기준): 모의에서 나온 소자 스트레스를 데이터시트 정격과 대조.

■ 목적
  지금까지의 검증(E15–E33, TB01–TB26)은 회로·제어가 판정 한계 안에서 동작하는지를 보았다. 그 한계가 실제 부품으로 성립하는지는
  따로 확인해야 한다. 이 시험은 설계의 핵심 부품마다 (1) 모의에서 나온 최대 전압·전류·에너지·손실을 모으고, (2) 후보 부품의
  데이터시트 표 값과 미리 정한 여유 규칙으로 대조한다. 후보가 없거나 데이터시트가 그림으로만 정격을 주는 항목은 요구 정격만
  적고 판정하지 않는다(또는 조건부).

■ 왜 필요한가
  E31에서 Stage A 손실 모델의 출력용량 항이 한 자릿수 작았던 것은 부품 데이터를 대조하면서 찾았다. 같은 종류의 빈틈(모델에는
  없지만 부품이 받아야 하는 스트레스)이 보호 부품(클램프, 바이패스 선형 영역, 제동 저항, 접촉기)과 수동소자에 남아 있는지 본다.
  A25는 공진 주파수를 1/6로 낮춰 C_fly가 6배(46.9 µF)가 되었으므로 커패시터 전류 밀도를 따로 확인해야 한다.

■ 대상, 입력, 후보(실행 전에 정함)
  P1 Stage A 스위치 C4MS008075U2(위치당 2병렬): A25 정격점 모의(E32 rated와 같은 설정: 8위상, 375 A 충전, 640·800·920 V × 공칭·
     공차 표본 1–3)의 위상별 전류·손실 + E32·E33 결과의 최대 위상 첨두(정상점·과도·모듈 고장)
  P2 플라잉 커패시터 46.875 µF: 위 정격점 모의의 위상 실효전류·전압. 후보 TDK B3277x(600·800 V, 표에서 가져온 20행)
  P3 공진 인덕터 864.6 nH: 요구 정격만(맞춤 자성체, 후보 없음)
  P4 V_A 클램프 저항 1 Ω: E26 클램프 사건 32개를 다시 계산(전체 기록). 후보 Ohmite 891SP(1 Ω, 15 kJ, < 10 ms 펄스 기준)
  P5 V_A 클램프 스위치: 같은 기록에서 켬·끔 횟수와 전류. 후보 Infineon FF450R12ME4P(1200 V, 450 A IGBT)
  P6 바이패스 소프트 투입(EPC2305 2병렬 × 역직렬): E29 seq에서 소프트 투입 에너지가 가장 큰 사례(팩별 1개)를 기록과 함께 재실행
  P7 H-브리지 역방향 도통(EPC2305, 위치당 2병렬): E29 failsafe F2(채택 대책) 4사례를 기록과 함께 재실행
  P8 링크 제동 저항 3 Ω: E29 seq에서 제동 에너지가 가장 큰 사례를 재실행. 후보 Vishay LTO 150H(75 J/0.1 s)
  P9 400 V 부하 접촉기: E29 seq 저장값(접촉기 개방 순간 경로전류)과 팩 등급 버스 전압. 후보 Panasonic AEV18012(450 V)

■ 공통 가정(실행 전에 고정)
  - 냉각 기준 온도: SiC·GaN 소자 케이스 T_C = 100 °C, IGBT 모듈 방열판 T_H = 65 °C.
  - 정상 운전(연속): T_J ≤ T_J,max − 25 °C. 고장 사건(단발): T_J ≤ T_J,max(데이터시트 SOA가 쓰는 한계).
  - 스위칭 병렬 분담: 같은 몫 × 1.1. 선형 영역(바이패스 소프트 투입)은 분담을 보장할 수 없으므로 판정은 소자 1개가 모두 받는 경우,
    같은 몫은 정보로 적는다.
  - 열: Stage A·IGBT는 정상 열저항(R_thJC·R_thJH). 사건이 열저항의 시정수보다 짧으면 정상 열저항은 보수적이다. EPC2305는 데이터시트
    그림 12의 단일 펄스 Z_thJC(벡터 경로에서 읽은 100점, data/datasheets/EPC2305.json)를 Foster 회로망(고정 τ 25개(10^-6.5–10^0.5 s), 비음 최소제곱)으로
    맞춰 전력 이력을 겹쳐 계산한다(맞춤 오차를 보고).
  - IGBT 스위칭 에너지: 데이터시트 E_on·E_off(125 °C, 600 V, 450 A, 유도성 부하)를 전압·전류에 비례로 줄인다. 저항 부하라 보수적이다.
    도통 전압 V_CE = 2.0 V × I/450 A(125 °C 표 값을 지나는 직선).

■ 판정 기준(실행 전에 고정)
  반도체 공통: (V) 모델 최대 차단 전압 ≤ 0.8 × 정격(기생 인덕턴스 과전압은 모델에 없음), (I) 소자당 첨두 ≤ 0.5 × 펄스 정격,
               (T) 위 온도 규칙
  P1: V = max(v_C, V_bat − v_C) 최대(1008 V 팩은 V_bat/2 + 정격점 모의의 v_C 상승분으로 올림), I = 최대 위상 첨두/2 × 1.1,
      T = 정격점 중 가장 뜨거운 위상: 위치 손실 = 도통 mean(i²)·R_위치/2 + 다이오드/4 + Q_oss,위치(V)·V·f, 소자 = 위치/2 × 1.1
  P2: 조합(같은 품목 또는 두 품목, 1–6개)의 총 C가 46.875 µF ± 5 % 안이고, Σ I_rms(70 °C, 10 kHz 표 값) ≥ 위상 실효전류
      (공칭 정격점과 공차 표본 최악 위상 둘 다), V_R ≥ v_C 최대(85 °C 이하 정격). 만족하는 조합이 하나라도 있으면 통과.
      없으면 불통과와 함께 (a) ± 5 % 안에서 전류가 가장 큰 조합, (b) 전류만 맞추는 데 필요한 개수와 그때의 C를 보고한다.
  P3: 판정 없음. 요구: I_sat ≥ 1.2 × 최대 위상 첨두, 실효전류, 저장 에너지.
  P4: 사건 최대 에너지 ≤ 후보 정격 에너지(< 10 ms 기준; 사건은 더 길므로 보수적), 사건 최대 V_A ≤ 정격 첨두 전압, 1 Ω가 저항 범위 안.
      (데이터시트 단서: 저항값별 허용치는 제조사 확인 → 조건부로 적음)
  P5: (I) 클램프 전류 최대 ≤ 0.5 × I_CRM, (V) V_A 최대 ≤ 0.8 × V_CES, (T) 사건 평균 손실 × R_thJH + T_H ≤ 150 °C(사건 중 평균은
      켬 첫 시각–끔 마지막 시각 사이). 보수 계산으로 불통과면 불통과로 적고, Z_th 그림 대조로 바뀔 수 있음을 함께 적는다.
  P6: 소자 1개 기준 T_C + ΔT_J ≤ 150 °C(EPC2305 T_J,max), (V) 직렬전압 최대 ≤ 0.8 × 150 V
  P7: 소자당 전류 = 1.1 × |i_h|/2, V_SD = 데이터시트 그림 8의 125 °C 역방향 곡선(V_GS = 0 V), T_C + ΔT_J ≤ 150 °C,
      (I) 소자당 첨두 ≤ 0.5 × 329 A
  P8: 고장당 에너지 ≤ 75 J 이고 저항값이 범위 안이면 '조건부 통과'(데이터시트는 0.1 s 펄스 한 점만 숫자로 준다. 펄스 폭이 0.1 s보다
      짧으면 그림의 펄스 에너지 곡선과 대조해야 한다), 넘으면 불통과.
  P9: 팩 등급별 (V) 버스 상한 ≤ 정격 전압 450 V, (I) 개방 순간 전류 최대 ≤ 80 A(450 V 전기적 수명 정격 전류) → 둘 다면 통과

■ 실행 경과와 결과(2026-10-28, 기준은 바꾸지 않았다)
  실행 경과: stagea 1차는 E33 transient·fault 결과 파일의 열쇠 이름(rows가 아니라 cases)을 잘못 읽어 두 결과가 첨두 출처에서
            빠졌다(stagea_run1_E33key.json). 읽기 코드만 고쳐 다시 실행했다. 판정은 같았고 소자 첨두·L_r 요구가 커졌다.
  P1 통과: 차단 518 V(한도 600), 소자 첨두 93.1 A(위상 169.3 A, E33 MF 사전 기동 없는 충전 — 금지 조건; 고장 최대는 119.6 A),
           가장 뜨거운 위치 19.2 W → 소자 10.6 W → T_J 101.7 °C
  P2 불통과: 위상 실효 공칭 52.5·최악 60.9 A → 1.30 A/µF 필요. ± 5 % 안 최대 46 µF·44.1 A(10 µF × 3 + 16 µF, 600 V).
           전류만 맞추면 10 µF × 6 = 60 µF.
  P3 요구: I_sat ≥ 203 A(금지 조건 MF 제외 시 144 A), 실효 60.9 A, 865 nH
  P4 조건부 통과: 최대 6987 J ≤ 891SP 15 kJ(< 10 ms 기준, 1 Ω 허용치 제조사 확인)
  P5 불통과: 클램프가 29–40 kHz로 켜고 꺼진다(사건당 최대 1599번). 보수 계산 T_vj 334–405 °C, 전류 469 A > 450 A
  P6 불통과: 소프트 투입(W460 930 V, 0.75 J, 약 1.8 ms) 소자 1개 176 °C(같은 몫 138 °C)
  P7 통과: 소자 32.7 A, T_J 103 °C.  P8 조건부 통과: 53.3 J/60 ms ≤ 75 J/0.1 s(짧은 펄스 곡선 대조 필요)
  P9: W460 불통과(버스 470 V > 450 V), W410 통과(420 V, 70.7 A)

■ 실행   python E34_parts_rating.py clamp prot stagea table figures   (clamp·prot 약 15분, stagea 약 20분, 2코어)
■ 결과   results/E34/clamp.json, prot.json, stagea.json, table.json, table.csv, E34_parts_rating.png
"""
import itertools
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from common import ROOT, load_json, outdir, save_json, verdict, workers

EID = "E34"
DS_DIR = ROOT / "data" / "datasheets"
T_C_SEMI = 100.0           # SiC·GaN 케이스 [°C]
T_H_IGBT = 65.0            # IGBT 방열판 [°C]
SHARE = 1.1                # 스위칭 병렬 분담 여유
V_DER = 0.8                # 전압 여유
I_DER = 0.5                # 펄스 전류 여유
C_TOL = 0.05               # C_fly 조합 허용 범위
SAT_MARGIN = 1.2           # 인덕터 포화 여유


def ds(name):
    return json.loads((DS_DIR / f"{name}.json").read_text(encoding="utf-8"))


# ======================================================================================================
# 열: EPC2305 단일 펄스 Z_thJC → Foster 회로망
# ======================================================================================================
def foster_fit(curve, rth, taus=None):
    """단일 펄스 정규화 Z_th 곡선([t, z], z = Z/R_th) → Foster 항 (R_i, τ_i). 비음 최소제곱, τ 고정."""
    from scipy.optimize import nnls
    t = np.array([p[0] for p in curve]); z = np.array([p[1] for p in curve]) * rth
    taus = np.logspace(-6.5, 0.5, 25) if taus is None else np.asarray(taus)
    Amat = 1 - np.exp(-t[:, None] / taus[None, :])
    w = 1 / z                                         # 상대 오차 최소화
    R, _ = nnls(Amat * w[:, None], z * w)
    zf = Amat @ R
    return dict(R=R.tolist(), tau=taus.tolist(), max_rel_err=float(np.max(np.abs(zf / z - 1))), R_sum=float(R.sum()), rth=rth)


def foster_dT(F, t, p):
    """전력 이력 p(t)(구간 일정, t 균일 간격) → 접합 온도 상승 ΔT(t)."""
    dt = float(t[1] - t[0]); R = np.array(F["R"]); tau = np.array(F["tau"])
    a = np.exp(-dt / tau); b = R * (1 - a)
    x = np.zeros_like(R); out = np.empty(len(p))
    for k, pk in enumerate(p):
        x = a * x + b * pk
        out[k] = x.sum()
    return out


def epc_foster():
    d = ds("EPC2305")
    return foster_fit(d["zth_jc_single_pulse_norm"], d["thermal"]["R_thJC_top_CperW"])


# ======================================================================================================
# P4·P5: V_A 클램프(E26 사건 재계산)
# ======================================================================================================
def _clamp(kw):
    import E26_charging_stop as E26
    r = E26.run_event(**kw, rec_every=1, full_trace=True)
    tr = np.array(r.pop("trace"))
    t, vA, icl = tr[:, 0], tr[:, 1], tr[:, 5]
    on = icl > 0
    k_on = np.flatnonzero(~on[:-1] & on[1:]) + 1
    k_off = np.flatnonzero(on[:-1] & ~on[1:]) + 1
    g = ds("FF450R12ME4P")["igbt"]
    eon, eoff = g["E_on_mJ"]["125"] * 1e-3, g["E_off_mJ"]["125"] * 1e-3
    E_on = float(np.sum(eon * (vA[k_on] / 600.) * (icl[k_on] / 450.)))
    E_off = float(np.sum(eoff * (vA[k_off - 1] / 600.) * (icl[k_off - 1] / 450.)))
    dt = float(t[1] - t[0])
    E_cond = float(np.sum(2.0 * icl[on] / 450. * icl[on]) * dt)
    span = float(t[k_off[-1] - 1] - t[k_on[0]]) if len(k_on) and len(k_off) else float(on.sum() * dt)
    out = dict({k: r[k] for k in ("Vbat", "P400", "PC", "arch", "prof", "t_comm", "E_clamp_J", "P_clamp_pk_W", "t_clamp_on_ms", "vA_max")},
               n_on=int(len(k_on)), n_off=int(len(k_off)), span_ms=span * 1e3, f_avg_kHz=len(k_on) / span / 1e3 if span > 0 else 0.,
               i_max=float(icl.max()), vA_on_max=float(vA[on].max()) if on.any() else None,
               E_on_J=E_on, E_off_J=E_off, E_cond_J=E_cond, E_igbt_J=E_on + E_off + E_cond,
               P_igbt_avg_W=(E_on + E_off + E_cond) / span if span > 0 else 0.)
    out["Tvj_C"] = T_H_IGBT + out["P_igbt_avg_W"] * g["R_thJH_KperW"]
    if kw["Vbat"] == 920. and kw["arch"] == "R2W" and kw["P400"] == 0. and kw["prof"] == "hold" and kw["t_comm"] > 0:
        w = (t >= t[k_on[0]] - 50e-6) & (t <= t[k_on[0]] + 300e-6)
        out["zoom"] = dict(t=t[w].tolist(), vA=vA[w].tolist(), icl=icl[w].tolist())
    return out


def clamp():
    import E26_charging_stop as E26
    evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
    with Pool(workers()) as p:
        rows = p.map(_clamp, evs)
    o = ds("Ohmite_800_1000"); g = ds("FF450R12ME4P")["igbt"]
    cand = next(r for r in o["rows"] if r[0] == "891SP")
    w = max(rows, key=lambda r: r["E_clamp_J"]); wt = max(rows, key=lambda r: r["Tvj_C"])
    for r in rows:
        print("  %-3s %4.0f V %2.0f+%1.0f kW %-4s t_comm %2.0f ms: 저항 %6.0f J·%5.1f kW·%5.1f ms, 켬 %5d번(평균 %4.1f kHz, 구간 %5.1f ms), "
              "IGBT 켬 %.1f·끔 %.1f·도통 %.1f J → 평균 %.0f W → T_vj %.0f °C"
              % (r["arch"], r["Vbat"], r["P400"] / 1e3, r["PC"] / 1e3, r["prof"], r["t_comm"] * 1e3, r["E_clamp_J"], r["P_clamp_pk_W"] / 1e3,
                 r["t_clamp_on_ms"], r["n_on"], r["f_avg_kHz"], r["span_ms"], r["E_on_J"], r["E_off_J"], r["E_cond_J"], r["P_igbt_avg_W"], r["Tvj_C"]))
    vmax = max(r["vA_max"] for r in rows); imax = max(r["i_max"] for r in rows)
    p4 = dict(E_max_J=w["E_clamp_J"], E_rating_J=cand[6], V_max=vmax, V_rating=cand[7], R_in_range=cand[3] <= 1.0 <= cand[4],
              ok=bool(w["E_clamp_J"] <= cand[6] and vmax <= cand[7] and cand[3] <= 1.0 <= cand[4]), conditional="저항값별 허용치 제조사 확인")
    p5 = dict(i_max=imax, I_lim=I_DER * g["I_CRM_A"], V_max=vmax, V_lim=V_DER * g["V_CES_V"], Tvj_max=wt["Tvj_C"], T_lim=g["T_vj_op_max_C"],
              worst=dict(arch=wt["arch"], Vbat=wt["Vbat"], P400=wt["P400"], prof=wt["prof"], t_comm=wt["t_comm"]),
              n_on_max=max(r["n_on"] for r in rows), f_avg_kHz=[min(r["f_avg_kHz"] for r in rows), max(r["f_avg_kHz"] for r in rows)])
    p5["ok"] = bool(p5["i_max"] <= p5["I_lim"] and p5["V_max"] <= p5["V_lim"] and p5["Tvj_max"] <= p5["T_lim"])
    verdict("P4 클램프 저항(891SP)", p4["ok"], "최대 %.0f J ≤ %d J, V_A %.1f V, 조건: %s" % (p4["E_max_J"], p4["E_rating_J"], vmax, p4["conditional"]))
    verdict("P5 클램프 스위치(FF450R12ME4P)", p5["ok"], "전류 %.0f A(한도 %.0f), T_vj %.0f °C(한도 %d), 켬 최대 %d번, 평균 %.0f–%.0f kHz"
            % (imax, p5["I_lim"], wt["Tvj_C"], p5["T_lim"], p5["n_on_max"], *p5["f_avg_kHz"]))
    save_json(EID, "clamp", dict(rows=rows, P4=p4, P5=p5, assumptions=dict(T_H=T_H_IGBT, E_scale="E(125 °C)·V/600·I/450", V_CE="2.0 V·I/450")))


# ======================================================================================================
# P6–P9: 보호 부품(E29 재실행)
# ======================================================================================================
def _job_seq(tag):
    import E29_sals_degradation as E29
    j = next(j for j in E29.seq_jobs() if j["_tag"] == tag)
    j = dict(j); j.pop("_tag"); j.pop("_extra"); j["keep"] = True
    return j


def _job_fs(case, V):
    import E17_protection_integration as E17
    import E29_sals_degradation as E29
    det = load_json("E29", "failsafe")["dab_det_ms"]["%s_%.0f" % (case, V)] * 1e-3
    t2 = E17.T_EV + det + E29.T_EV2
    return dict(case=case, V=V, P=E29.P0, event="dab", policy="brk_hold", event2=t2, duration=t2 + 10e-3, keep=True,
                sals=E29.sals_cfg(case, E29.MIXES["MX"], E29.SCEN["S5"]), fs_brake=True, astop=E29.ASTOP, **E29.P3T)


def _prot(args):
    kind, tag, job = args
    import E17_protection_integration as E17
    m = E17.r2_run(job)
    tr = m.pop("trace"); t, lg = tr["t"], tr["log"]
    F = epc_foster(); d = ds("EPC2305")
    dt = float(t[1] - t[0])
    out = dict(kind=kind, tag=tag, dt_us=dt * 1e6, final_state=m["final_state"], series_peak=m["series_peak"], bridge_peak=m["bridge_peak"],
               soft_energy_J=m["soft_energy_J"], brk_energy_J=m["brk_energy_J"])
    if kind == "soft":
        p = np.abs(lg[:, 1] * lg[:, 6])                       # 바이패스 전체 손실(직렬전압 × 바이패스 전류)
        dT1 = foster_dT(F, t, p); dT2 = foster_dT(F, t, p / 2)
        k = int(np.argmax(dT1)); act = np.flatnonzero(p > 1.)
        out.update(E_byp_J=float(p.sum() * dt), P_byp_pk_W=float(p.max()), dT_one=float(dT1.max()), dT_share=float(dT2.max()),
                   t_peak_ms=float((t[k] - E17.T_EV) * 1e3), vs_max_soft=float(np.abs(lg[act, 1]).max()) if len(act) else 0.,
                   ib_max=float(np.abs(lg[:, 6]).max()),
                   p_span_ms=float((t[act[-1]] - t[act[0]]) * 1e3) if len(act) else 0.)
        w = slice(max(act[0] - 200, 0), min(act[-1] + 2000, len(t))) if len(act) else slice(0, 1)
        out["trace"] = dict(t=((t[w] - E17.T_EV) * 1e3)[::5].tolist(), p=p[w][::5].tolist(), dT=dT1[w][::5].tolist())
    elif kind == "hb":
        rev = np.array(d["reverse_vgs0_125C_V_A"])           # [V, A]
        ih = np.abs(lg[:, 3]); off = lg[:, 8] > 1.5
        idev = SHARE * ih / 2 * off
        vsd = np.interp(idev, rev[:, 1], rev[:, 0])
        p = vsd * idev
        dT = foster_dT(F, t, p); k = int(np.argmax(dT)); act = np.flatnonzero(p > .5)
        out.update(i_dev_max=float(idev.max()), vsd_at_max=float(vsd[np.argmax(idev)]), E_dev_J=float(p.sum() * dt), P_dev_pk_W=float(p.max()),
                   dT=float(dT.max()), t_peak_ms=float((t[k] - E17.T_EV) * 1e3),
                   p_span_ms=float((t[act[-1]] - t[act[0]]) * 1e3) if len(act) else 0., rev_curve_max_A=float(rev[:, 1].max()))
        w = slice(max(act[0] - 200, 0), min(act[-1] + 2000, len(t))) if len(act) else slice(0, 1)
        out["trace"] = dict(t=((t[w] - E17.T_EV) * 1e3)[::5].tolist(), p=p[w][::5].tolist(), dT=dT[w][::5].tolist())
    elif kind == "brake":
        p = lg[:, 9]; act = np.flatnonzero(p > 1.)
        E = float(p.sum() * dt)
        n01 = int(round(0.1 / dt)); cs = np.concatenate([[0.], np.cumsum(p) * dt])
        e01 = float(np.max(cs[n01:] - cs[:-n01])) if len(cs) > n01 else E
        vl = lg[:, 4]
        out.update(E_J=E, E_max_100ms_J=e01, P_pk_W=float(p.max()), span_ms=float((t[act[-1]] - t[act[0]]) * 1e3) if len(act) else 0.,
                   on_ms=float(len(act) * dt * 1e3), vlink_max=float(vl.max()))
        out["trace"] = dict(t=((t - E17.T_EV) * 1e3)[::20].tolist(), p=p[::20].tolist())
    return out


def prot():
    import E29_sals_degradation as E29
    seq = load_json("E29", "seq")["rows"]
    soft_tags = [max([r for r in seq if r["case"] == c], key=lambda r: r["soft_energy_J"])["tag"] for c in ("W460_240s", "W410_spec")]
    brk_tag = max(seq, key=lambda r: r["brk_energy_J"])["tag"]
    jobs = [("soft", tg, _job_seq(tg)) for tg in soft_tags] + [("brake", brk_tag, _job_seq(brk_tag))] + \
           [("hb", "%s_%.0f_F2" % cv, _job_fs(*cv)) for cv in E29.FS_PACKS]
    with Pool(workers()) as p:
        rows = p.map(_prot, jobs, chunksize=1)
    F = epc_foster(); d = ds("EPC2305")
    tj = d["ratings"]["T_J_max_C"]
    print("  EPC2305 Z_thJC Foster 맞춤: R 합 %.3f K/W(R_thJC %.2f), 최대 상대 오차 %.1f %%" % (F["R_sum"], F["rth"], 100 * F["max_rel_err"]))
    soft = [r for r in rows if r["kind"] == "soft"]; hb = [r for r in rows if r["kind"] == "hb"]; br = [r for r in rows if r["kind"] == "brake"][0]
    for r in soft:
        print("  P6 %-24s 소프트 에너지 %.3f J(재계산 %.3f), 첨두 %.0f W, 구간 %.2f ms → ΔT_J 1개 %.1f K / 같은 몫 %.1f K, 직렬 최대 %.1f V"
              % (r["tag"], r["soft_energy_J"], r["E_byp_J"], r["P_byp_pk_W"], r["p_span_ms"], r["dT_one"], r["dT_share"], r["series_peak"]))
    for r in hb:
        print("  P7 %-24s 소자 전류 최대 %.1f A(V_SD %.2f V), 소자 에너지 %.3f J, 첨두 %.0f W, 구간 %.2f ms → ΔT_J %.1f K"
              % (r["tag"], r["i_dev_max"], r["vsd_at_max"], r["E_dev_J"], r["P_dev_pk_W"], r["p_span_ms"], r["dT"]))
    print("  P8 %s: 제동 %.1f J(0.1 s 창 최대 %.1f J), 첨두 %.0f W, 펄스 구간 %.1f ms(켜진 시간 %.1f ms), 링크 최대 %.1f V"
          % (br["tag"], br["E_J"], br["E_max_100ms_J"], br["P_pk_W"], br["span_ms"], br["on_ms"], br["vlink_max"]))
    p6 = dict(dT_one=max(r["dT_one"] for r in soft), dT_share=max(r["dT_share"] for r in soft), T_lim=tj,
              V_max=max(r["vs_max_soft"] for r in soft), V_lim=V_DER * d["ratings"]["V_DS_V"],
              i_max=max(r["ib_max"] for r in soft), I_lim=I_DER * d["ratings"]["I_DM_A"] * 2)
    p6["Tj_one"] = T_C_SEMI + p6["dT_one"]; p6["Tj_share"] = T_C_SEMI + p6["dT_share"]
    p6["ok"] = bool(p6["Tj_one"] <= tj and p6["V_max"] <= p6["V_lim"])
    p6["ok_share"] = bool(p6["Tj_share"] <= tj and p6["V_max"] <= p6["V_lim"])
    p7 = dict(dT=max(r["dT"] for r in hb), i_dev_max=max(r["i_dev_max"] for r in hb), I_lim=I_DER * d["ratings"]["I_DM_A"], T_lim=tj,
              V_max=max(r["series_peak"] for r in hb), V_lim=V_DER * d["ratings"]["V_DS_V"])
    p7["Tj"] = T_C_SEMI + p7["dT"]
    p7["ok"] = bool(p7["Tj"] <= tj and p7["i_dev_max"] <= p7["I_lim"] and p7["V_max"] <= p7["V_lim"])
    lto = ds("Vishay_LTO150H")["ratings"]
    p8 = dict(E_J=br["E_J"], E_100ms_J=br["E_max_100ms_J"], E_rating_J=lto["E_pulse_J"], span_ms=br["span_ms"], R_ohm=3.0,
              R_in_range=lto["R_range_ohm"][0] <= 3.0 <= lto["R_range_ohm"][1], vlink_max=br["vlink_max"])
    p8["ok"] = bool(p8["E_100ms_J"] <= p8["E_rating_J"] and p8["R_in_range"])
    p8["conditional"] = p8["ok"] and p8["span_ms"] < 100.
    # P9 접촉기
    ctc = ds("Panasonic_AEV18012")["ratings"]
    import E17_protection_integration as E17
    p9 = {}
    for case in ("W460_240s", "W410_spec"):
        rr = [r for r in seq if r["case"] == case and r.get("i_break") is not None]
        imax = max(abs(r["i_break"]) for r in rr)
        up = E17.E19.CASES[case]["upper"]
        p9[case] = dict(i_break_max=imax, n=len(rr), V_bus_upper=up, V_rating=ctc["V_rated_V"], I_rating=ctc["I_carry_A"],
                        ok=bool(up <= ctc["V_rated_V"] and imax <= ctc["I_carry_A"]))
    verdict("P6 바이패스 소프트 투입(소자 1개)", p6["ok"], "T_J %.1f °C(같은 몫 %.1f °C), 한도 %d °C, 직렬 %.1f V" % (p6["Tj_one"], p6["Tj_share"], tj, p6["V_max"]))
    verdict("P7 H-브리지 역방향 도통", p7["ok"], "T_J %.1f °C, 소자 전류 %.1f A, 직렬 %.1f V" % (p7["Tj"], p7["i_dev_max"], p7["V_max"]))
    verdict("P8 제동 저항(LTO 150H)", p8["ok"], "%.1f J ≤ %d J%s" % (p8["E_100ms_J"], p8["E_rating_J"],
                                                                     ", 조건부(펄스 %.0f ms < 0.1 s: 곡선 대조 필요)" % p8["span_ms"] if p8["conditional"] else ""))
    for case, v in p9.items():
        verdict("P9 접촉기(AEV18012) %s" % case, v["ok"], "버스 상한 %.0f V(정격 %d V), 개방 전류 최대 %.1f A(%d A)"
                % (v["V_bus_upper"], v["V_rating"], v["i_break_max"], v["I_rating"]))
    save_json(EID, "prot", dict(rows=rows, foster=F, P6=p6, P7=p7, P8=p8, P9=p9, T_C=T_C_SEMI))


# ======================================================================================================
# P1–P3: Stage A
# ======================================================================================================
def _rated_r(args):
    V, seed = args
    import model_stage_a as A
    import E28_stage_a_modules as E28
    import E32_stage_a_25k as E32
    A.set_design(E32.DESIGN)
    tol, rs = (E28.TOL, A.matlab_rng(seed)) if seed else (None, None)
    r = A.sim_array(N=8, Vbat=V, Iload=-375., Cbus=E32.CA, mode="zcp", ncyc=80, tol=tol, rs=rs, dead_fix=True, unarmed_stop=E32.GATE)
    ph, bus = A.analyze(r, ncyc_last=20)
    msk = r["t"] >= r["t"][-1] - 20 * r["T"]
    B = A.BASE; Rpos = B["Rds"]
    out = []
    for k, p in enumerate(ph):
        i = r["i"][msk, k].astype(float); v = r["v"][msk, k].astype(float); st = r["st"][msk, k].astype(int)
        Vh = float(np.mean(r["vb"][msk]))
        pc = float(np.mean(i ** 2)) * Rpos / 2
        pd = float(np.mean((st == 0) * 2 * B["Vf"] * np.abs(i))) / 4
        po = float(A.qoss_pos(Vh) * Vh * p["fs"])
        out.append(dict(k=k, Irms=float(np.sqrt(np.mean(i ** 2))), Ipk=p["Ipk"], fs=p["fs"], vC_max=float(v.max()), vC_min=float(v.min()),
                        vblock_max=float(max(v.max(), (V - v).max())), Vh=Vh, P_pos_cond=pc, P_pos_diode=pd, P_pos_coss=po,
                        P_pos=pc + pd + po, C=float(r["C"][k]), L=float(r["L"][k])))
    return dict(V=V, seed=seed, phases=out)


def stagea():
    import model_stage_a as A
    import E28_stage_a_modules as E28
    import E32_stage_a_25k as E32
    A.set_design(E32.DESIGN)
    jobs = [(V, s) for s in E28.SEEDS for V in E28.RATED_V]
    with Pool(workers()) as p:
        rows = p.map(_rated_r, jobs)
    B = A.BASE; dev = ds("C4MS008075U2")
    # 첨두: E32 rated, E33 static·transient·fault
    pk = dict(E32_rated=max(x["Ipk"] for x in load_json("E32", "rated")["rows"]))
    for nm in ("static", "transient", "fault"):
        try:
            dd = load_json("E33", nm)
            rr = dd["rows"] if "rows" in dd else dd["cases"]          # static은 rows, transient·fault는 cases
            pk["E33_" + nm] = max(x["phase_peak"] for x in rr)
        except Exception as e:                                       # noqa: BLE001
            pk["E33_" + nm] = None; print("  (E33 %s 없음: %s)" % (nm, e))
    ipk = max(v for v in pk.values() if v is not None)
    allph = [dict(ph, V=x["V"], seed=x["seed"]) for x in rows for ph in x["phases"]]
    hot = max(allph, key=lambda q: q["P_pos"])
    nom = [q for q in allph if q["seed"] is None]
    irms_nom = max(q["Irms"] for q in nom); irms_w = max(q["Irms"] for q in allph)
    dv_up = max(q["vC_max"] - q["V"] / 2 for q in allph)
    vmax = max(1008. / 2 + dv_up, max(q["vblock_max"] for q in allph))
    # P1
    P_dev = hot["P_pos"] / 2 * SHARE
    Tj = T_C_SEMI + P_dev * dev["thermal"]["R_thJC_CperW"]
    p1 = dict(V_max=vmax, V_lim=V_DER * dev["ratings"]["V_DS_V"], I_dev_pk=ipk / 2 * SHARE, I_lim=I_DER * dev["ratings"]["I_DM_A"],
              hot=dict(V=hot["V"], seed=hot["seed"], k=hot["k"], P_pos=hot["P_pos"], parts=[hot["P_pos_cond"], hot["P_pos_diode"], hot["P_pos_coss"]],
                       Irms=hot["Irms"]), P_dev=P_dev, Tj=Tj, T_lim=dev["ratings"]["T_J_max_C"] - 25, peaks=pk, I_phase_pk_max=ipk,
              I_dev_rms=hot["Irms"] / 2 / math.sqrt(2) * SHARE, I_D100=dev["ratings"]["I_D_100C_A"])
    p1["ok"] = bool(p1["V_max"] <= p1["V_lim"] and p1["I_dev_pk"] <= p1["I_lim"] and Tj <= p1["T_lim"])
    # P2
    tdk = ds("TDK_B3277x"); Cd = B["Cfly"] * 1e6
    cand = []
    rows_c = [dict(zip(tdk["row_fields"], rw)) for rw in tdk["rows"] if rw[1] >= vmax]
    for n in range(1, 7):
        for a in rows_c:
            cand.append(([a["code_prefix"]] * n, n * a["C_uF"], n * a["I_rms_70C_10kHz_A"], a["V_R_V"]))
        for a, b in itertools.combinations(rows_c, 2):
            if a["V_R_V"] != b["V_R_V"]:
                continue
            for na in range(1, n):
                cand.append(([a["code_prefix"]] * na + [b["code_prefix"]] * (n - na), na * a["C_uF"] + (n - na) * b["C_uF"],
                             na * a["I_rms_70C_10kHz_A"] + (n - na) * b["I_rms_70C_10kHz_A"], a["V_R_V"]))
    inC = [c for c in cand if abs(c[1] / Cd - 1) <= C_TOL]
    ok_c = [c for c in inC if c[2] >= irms_w]
    best = max(inC, key=lambda c: c[2]) if inC else None
    dens = max(rows_c, key=lambda a: a["I_rms_70C_10kHz_A"] / a["C_uF"])
    n_need = math.ceil(irms_w / dens["I_rms_70C_10kHz_A"])
    p2 = dict(C_design_uF=Cd, V_max=vmax, Irms_nominal=irms_nom, Irms_worst=irms_w, A_per_uF_needed=irms_w / Cd,
              n_comb=len(cand), n_inC=len(inC), ok=bool(ok_c),
              best_inC=None if best is None else dict(parts=best[0], C_uF=best[1], I_rms=best[2], V_R=best[3]),
              best_density=dict(part=dens["code_prefix"], V_R=dens["V_R_V"], A_per_uF=dens["I_rms_70C_10kHz_A"] / dens["C_uF"],
                                n_for_current=n_need, C_uF=n_need * dens["C_uF"], f_r_kHz_if_L_kept=1e-3 / (2 * math.pi * math.sqrt(B["Lr"] * n_need * dens["C_uF"] * 1e-6)),
                                f_r_kHz_if_Z0_kept=1e-3 / (2 * math.pi * math.sqrt(B["Lr"] / B["Cfly"]) * n_need * dens["C_uF"] * 1e-6)),
              passing=[dict(parts=c[0], C_uF=c[1], I_rms=c[2]) for c in ok_c[:5]])
    # P3
    p3 = dict(L_nH=B["Lr"] * 1e9, I_sat_req=SAT_MARGIN * ipk, I_pk_max=ipk, Irms_nominal=irms_nom, Irms_worst=irms_w,
              E_uJ=0.5 * B["Lr"] * ipk ** 2 * 1e6, f_kHz=hot["fs"] / 1e3)
    for x in rows:
        print("  %4.0f V 공차 %-4s: 위상 실효 %s A, 첨두 최대 %.1f A, v_C 최대 − V/2 %.1f V, 위치 손실 최대 %.1f W"
              % (x["V"], x["seed"], ["%.1f" % q["Irms"] for q in x["phases"]], max(q["Ipk"] for q in x["phases"]),
                 max(q["vC_max"] - x["V"] / 2 for q in x["phases"]), max(q["P_pos"] for q in x["phases"])))
    print("  첨두 출처 %s → %.1f A" % ({k: (None if v is None else round(v, 1)) for k, v in pk.items()}, ipk))
    verdict("P1 Stage A 스위치(C4MS008075U2 2병렬)", p1["ok"], "V %.0f V(한도 %.0f), 소자 첨두 %.1f A(한도 %.0f), 가장 뜨거운 위치 %.1f W → 소자 %.1f W → T_J %.1f °C(한도 %d)"
            % (vmax, p1["V_lim"], p1["I_dev_pk"], p1["I_lim"], hot["P_pos"], P_dev, Tj, p1["T_lim"]))
    verdict("P2 C_fly(TDK B3277x 조합)", p2["ok"], "실효 공칭 %.1f·최악 %.1f A, 필요 %.2f A/µF; ±5 %% 안 최대 %s; 전류만 맞추면 %s × %d = %.0f µF"
            % (irms_nom, irms_w, p2["A_per_uF_needed"], p2["best_inC"], dens["code_prefix"], n_need, n_need * dens["C_uF"]))
    print("  P3 L_r 요구: %.0f nH, I_sat ≥ %.0f A, 실효 %.1f(최악 %.1f) A, 저장 %.0f µJ" % (p3["L_nH"], p3["I_sat_req"], irms_nom, irms_w, p3["E_uJ"]))
    save_json(EID, "stagea", dict(rows=rows, P1=p1, P2=p2, P3=p3))


# ======================================================================================================
# 표·그림
# ======================================================================================================
def table():
    c = load_json(EID, "clamp"); p = load_json(EID, "prot"); s = load_json(EID, "stagea")
    P1, P2, P3, P4, P5 = s["P1"], s["P2"], s["P3"], c["P4"], c["P5"]
    P6, P7, P8, P9 = p["P6"], p["P7"], p["P8"], p["P9"]
    V = lambda ok, cond=False: ("조건부 통과" if cond else "통과") if ok else "불통과"
    T = [
        ("P1", "Stage A 스위치", "C4MS008075U2 × 2(위치당)", "차단 전압", "%.0f V" % P1["V_max"], "≤ 0.8 × 750 = %.0f V" % P1["V_lim"], V(P1["V_max"] <= P1["V_lim"])),
        ("P1", "", "", "소자 첨두", "%.1f A(위상 %.1f A)" % (P1["I_dev_pk"], P1["I_phase_pk_max"]), "≤ 0.5 × I_DM = %.0f A" % P1["I_lim"], V(P1["I_dev_pk"] <= P1["I_lim"])),
        ("P1", "", "", "접합 온도(정격 충전, 가장 뜨거운 위치)", "%.1f W → %.1f °C" % (P1["P_dev"], P1["Tj"]), "T_C 100 °C, ≤ %d °C" % P1["T_lim"], V(P1["Tj"] <= P1["T_lim"])),
        ("P2", "플라잉 커패시터 46.9 µF", "TDK B3277x 조합", "실효전류·용량",
         "%.1f(최악 %.1f) A, %.2f A/µF" % (P2["Irms_nominal"], P2["Irms_worst"], P2["A_per_uF_needed"]),
         "C ± 5 % 안 조합의 Σ I_rms ≥ 최악", V(P2["ok"])),
        ("P3", "공진 인덕터 864.6 nH", "맞춤(후보 없음)", "포화 전류 요구", "I_sat ≥ %.0f A, 실효 %.1f A" % (P3["I_sat_req"], P3["Irms_worst"]), "요구만", "판정 없음"),
        ("P4", "V_A 클램프 저항 1 Ω", "Ohmite 891SP", "사건 에너지", "%.0f J, V_A %.1f V" % (P4["E_max_J"], P4["V_max"]), "≤ %d J(< 10 ms 기준)" % P4["E_rating_J"], V(P4["ok"], P4["ok"])),
        ("P5", "V_A 클램프 스위치", "FF450R12ME4P", "접합 온도(보수)", "켬 %d번, 평균 %.0f–%.0f kHz → %.0f °C" % (P5["n_on_max"], *P5["f_avg_kHz"], P5["Tvj_max"]),
         "T_H 65 °C, R_thJH, ≤ 150 °C", V(P5["Tvj_max"] <= P5["T_lim"])),
        ("P5", "", "", "전류·전압", "%.0f A, %.1f V" % (P5["i_max"], P5["V_max"]), "≤ %.0f A, ≤ %.0f V" % (P5["I_lim"], P5["V_lim"]),
         V(P5["i_max"] <= P5["I_lim"] and P5["V_max"] <= P5["V_lim"])),
        ("P6", "바이패스(소프트 투입)", "EPC2305 2병렬 × 역직렬", "접합 온도", "1개 %.1f °C(같은 몫 %.1f °C)" % (P6["Tj_one"], P6["Tj_share"]),
         "T_C 100 °C, Z_thJC, ≤ 150 °C", V(P6["ok"])),
        ("P7", "H-브리지(이중 고장 역방향 도통)", "EPC2305 × 2(위치당)", "접합 온도", "%.1f A → %.1f °C" % (P7["i_dev_max"], P7["Tj"]), "≤ 150 °C", V(P7["ok"])),
        ("P8", "링크 제동 저항 3 Ω", "Vishay LTO 150H", "고장당 에너지", "%.1f J(펄스 %.0f ms)" % (P8["E_100ms_J"], P8["span_ms"]), "≤ 75 J/0.1 s", V(P8["ok"], P8["conditional"])),
    ]
    for case, v in P9.items():
        T.append(("P9", "400 V 부하 접촉기(%s)" % case.split("_")[0], "Panasonic AEV18012", "차단 전압·전류",
                  "%.0f V, %.1f A" % (v["V_bus_upper"], v["i_break_max"]), "≤ 450 V, ≤ 80 A", V(v["ok"])))
    rows = [dict(zip(("id", "part", "candidate", "item", "stress", "rule", "verdict"), x)) for x in T]
    save_json(EID, "table", dict(rows=rows))
    with open(outdir(EID) / "table.csv", "w", encoding="utf-8") as f:
        f.write("id,part,candidate,item,stress,rule,verdict\n")
        for x in T:
            f.write(",".join('"%s"' % s.replace('"', "'") for s in x) + "\n")
    for x in T:
        print("  %-3s %-28s %-24s %-22s %-34s %-30s %s" % x)


def figures():
    from plotstyle import korean
    plt = korean()
    c = load_json(EID, "clamp"); p = load_json(EID, "prot"); s = load_json(EID, "stagea")
    fig, ax = plt.subplots(2, 3, figsize=(15, 8.4))
    # (a) 클램프 확대
    z = next(r for r in c["rows"] if "zoom" in r)["zoom"]
    t0 = z["t"][0]
    a = ax[0, 0]; a.plot((np.array(z["t"]) - t0) * 1e6, z["vA"], lw=.8, color="C0"); a.set_ylabel("V_A [V]", color="C0")
    a2 = a.twinx(); a2.plot((np.array(z["t"]) - t0) * 1e6, z["icl"], lw=.8, color="C3"); a2.set_ylabel("클램프 전류 [A]", color="C3")
    a.set_xlabel("시간 [µs]"); a.set_title("(a) V_A 클램프 히스테리시스 스위칭(920 V R2-W)")
    # (b) 클램프 사건별 IGBT T_vj
    a = ax[0, 1]
    rr = c["rows"]
    for arch, col in (("R2", "C0"), ("R2W", "C1")):
        q = [r for r in rr if r["arch"] == arch]
        a.scatter([r["E_clamp_J"] for r in q], [r["Tvj_C"] for r in q], color=col, s=18, label=arch)
    a.axhline(150, color="k", ls="--", lw=.8); a.legend(fontsize=7); a.set_xlabel("저항 에너지 [J]"); a.set_ylabel("IGBT T_vj(보수) [°C]")
    a.set_title("(b) 클램프 사건 32개: 저항 에너지와 스위치 온도")
    # (c) 바이패스·H-브리지 Z_th
    a = ax[0, 2]
    for r in p["rows"]:
        if r["kind"] in ("soft", "hb"):
            a.plot(r["trace"]["t"], np.array(r["trace"]["dT"]) + p["T_C"], lw=.9, label="%s %s" % ("바이패스" if r["kind"] == "soft" else "H-브리지", r["tag"].replace("_240s", "").replace("_spec", "")))
    a.axhline(150, color="k", ls="--", lw=.8); a.set_xlabel("고장 뒤 시간 [ms]"); a.set_ylabel("T_J [°C](T_C 100 °C)")
    a.set_title("(c) EPC2305 접합 온도(Z_thJC 겹침)"); a.legend(fontsize=7)
    # (d) C_fly 전류 밀도
    a = ax[1, 0]
    tdk = ds("TDK_B3277x")
    for rw in tdk["rows"]:
        a.scatter(rw[2], rw[3] / rw[2], color="C0" if rw[1] == 600 else "C1", s=14)
    a.axhline(s["P2"]["A_per_uF_needed"], color="C3", lw=1, label="A25 필요(최악 위상)")
    a.axhline(s["P2"]["Irms_nominal"] / s["P2"]["C_design_uF"], color="C3", lw=1, ls="--", label="A25 필요(공칭)")
    a.set_xlabel("단위 C [µF]"); a.set_ylabel("I_rms / C [A/µF](70 °C, 10 kHz)"); a.legend(fontsize=7)
    a.set_title("(d) C_fly 전류 밀도: TDK B3277x(파랑 600 V, 주황 800 V)")
    # (e) 제동 저항
    a = ax[1, 1]
    br = next(r for r in p["rows"] if r["kind"] == "brake")
    a.plot(br["trace"]["t"], np.array(br["trace"]["p"]) / 1e3, lw=.6)
    a.set_xlabel("고장 뒤 시간 [ms]"); a.set_ylabel("제동 전력 [kW]"); a.set_title("(e) 링크 제동 저항: %s, %.1f J" % (br["tag"], br["E_J"]))
    # (f) Stage A 위치 손실
    a = ax[1, 2]
    allph = [(x["V"], x["seed"], q) for x in s["rows"] for q in x["phases"]]
    for i, (Vb, sd, q) in enumerate(allph):
        a.bar(i, q["P_pos_cond"], color="C0"); a.bar(i, q["P_pos_diode"], bottom=q["P_pos_cond"], color="C1")
        a.bar(i, q["P_pos_coss"], bottom=q["P_pos_cond"] + q["P_pos_diode"], color="C2")
    a.set_xlabel("정격점 위상(640·800·920 V × 공칭·표본 1–3 × 8위상)"); a.set_ylabel("위치 손실 [W]")
    a.set_title("(f) Stage A 위치 손실(도통·다이오드·출력용량)")
    fig.tight_layout()
    path = outdir(EID) / "E34_parts_rating.png"
    fig.savefig(path, dpi=130); print("  → 저장:", path)


if __name__ == "__main__":
    parts = sys.argv[1:] or ["clamp", "prot", "stagea", "table", "figures"]
    for nm in parts:
        print("E34", nm, "...")
        globals()[nm]()
