"""[E38] 외부 검토(2026-10-29) 대응과 남은 설계 과제 두 가지(P6 바이패스 소프트 투입, F2 이중 고장 경로전류)의 설계 변경 판정.

■ 왜 필요한가
  외부 검토가 최종 수치·부품 선정의 근거 6곳을 지적했다(검토 결과는 직접 재현해 모두 확인했다, docs/43 1절).
    (1) 손실·정격 비교의 Stage C가 이전 3 kW 고정이득 CLLC(TB05 전류, CRATED 3000) + 4스위치 벅부스트 모델이다.
    (2) V_A 클램프 1.2 Ω은 공칭값만 시험했다. 468 V에서 375 A를 흡수하려면 저항 전체가 470/375 = 1.253 Ω 이하여야 하는데
        저항 공차·온도계수·노화·배선·스위치 강하를 넣지 않았다(1.26 Ω에서 32사건 중 12건이 470 V 초과).
    (3) 클램프 IGBT 149 °C는 125 °C 스위칭 에너지로 계산했다. 150 °C 값이면 151.3–152.8 °C다.
    (4) 468/463 V 클램프는 V_bat/2가 이 문턱을 넘는 팩(224s·240s, R2-W460)에서 정상 운전 중에 켜진다.
    (5) 640·800·920 V 충전 손실은 '150 kW'가 아니라 375 A 정전류(120·150·172.5 kW)의 값이다.
    (6) 충전 손실을 전류 제곱으로 환산하면 출력용량·게이트의 고정 손실까지 줄어든다.
  그리고 남은 설계 과제 두 가지의 검토(2026-10-29, 진단은 판정 아님)에서 원인과 대책을 찾았다.
    P6: 남는 부하(Stage C 5.3 + V2L 3.8 kW)가 크면 링크 붕괴가 시간 상한에 걸려 직렬 −25.7 V에서 소프트 투입한다.
        에너지 0.75 J의 대부분은 버스 커패시터 2 mF를 25.7 V 충전하는 손실이다. → 붕괴·투입 동안 Stage C 일시 정지(허브 내부).
    F2: 이중 고장 뒤 400 V 부하가 붙어 있는 동안 버스가 저전압 차단(250 V)까지 떨어지며 경로전류가 남는다. → 전용 배선 부하 정지.
  사용자 결정(2026-10-29): 위 대책을 설계 변경으로 채택하고 검증한다(Stage C 일시 정지는 docs/14 M0 계약의 보호 예외,
  부하 정지는 400 V 부하의 새 인터페이스 요구).

■ 부분과 판정 기준(실행 전에 커밋. 기준을 바꾸면 그 이유와 함께 실행 경과에 적는다)
  공통: 데이터시트 값은 표·본문 숫자만 쓴다. 온도별 값이 여럿이면 표에 있는 온도 가운데 가장 큰 값(E_on·E_off·R_DS(on)·V_CEsat)을
        쓴다(검토 지적 3의 일관된 보수 규칙). 열은 E34·E37과 같다(IGBT 방열판 65 °C + 사건 평균 손실 × R_thJH, SiC는
        케이스 100 °C + R_thJC 또는 방열판 65 °C + R_thJH 중 큰 쪽, 정상 열저항).

  clamp (Q1, 검토 지적 2·3) V_A 클램프 재선정. 사건: E26 클램프 사건 32개(A25R: C_A 2.4 mF, R_A 9.0 mΩ, 켬 468 V, 지연 1 µs).
     저항: Ohmite 800/1000 시리즈 SP(데이터시트 rev 7/25-1): 공차 K ±10 %(가장 좁은 코드), 온도계수 +0.2 … −0.08 %/°C,
           부하 수명·단시간 과부하 변화 ±5 %. 저항체 온도: 주위 −40 … 85 °C(가정) + 사건 자기 가열 ΔT = E_가지 / C_th,
           C_th = 891SP 정격 에너지 15 kJ ÷ (최고 사용 온도 350 °C − 40 °C) = 48.4 J/K(가정: 정격 펄스가 최고 온도를 넘지 않음),
           E_가지 = 7.0 kJ(E37 최대 6,981 J) ÷ 가지 수.
           k_max = 1.10 × 1.05 × (1 + 0.002 × (85 + ΔT − 25)), k_min = 0.90 × 0.95 × min(1 − 0.002 × 65, 1 − 0.0008 × (85 + ΔT − 25)).
     변형: 가지 수 n(가지마다 저항 + 스위치 하나, 같은 게이트) × 가지 저항 공칭 R_b × 끔 문턱 {463, 458} V.
           n = 1: R_b ∈ {1.0, 1.1, 1.2} Ω, n = 2: {1.5, 1.6, 1.8, 2.0, 2.2} Ω, n = 3: {1.8, 2.2, 2.7, 3.0} Ω.
     모서리: 큰 저항 R_b·k_max + 배선 3 mΩ(가정, E15 RW), 스위치 강하 2.05 V(후보 가운데 450 A에서 가장 큰 강하: FF450R12ME4P
             V_CEsat 150 °C). 작은 저항 R_b·k_min, 강하 0(전류 최대).
     기준: (C1) 큰 저항 모서리에서 32사건 모두 V_A·버스 ≤ 470 V. (I) 작은 저항 모서리에서 가지 전류 첨두 ≤ 0.5 × 펄스 정격.
           (T) 두 모서리 모두 스위치 T_vj ≤ T_vj,op,max: 켬·끔 에너지 = 데이터시트 값 × (켬·끔 순간 V·I)/(V_ref·I_ref),
               도통 IGBT = V_CEsat(450 A) × ∫i dt(450 A 이하에서 보수), SiC = R_DS(on) × ∫i² dt, 사건 평균 손실 = 합 ÷ 동작 구간.
           (E) 가지 저항 에너지 ≤ 891SP 15 kJ, R_b가 891SP 범위(1–450 Ω) 안. (V) V_A ≤ 0.8 × 스위치 정격 전압.
     후보 스위치: FF450R12ME4P(IGBT), E37의 SiC 모듈 4종(가지마다 하나).
     선정: 통과 변형 가운데 가지 수가 적은 것 → FF450R12ME4P → 끔 463 V → 큰 R_b 순으로 첫 번째.

  hv (Q2, 검토 지적 4) 고전압 팩의 V_A 보호 범위.
     (S1) 팩별 정상 V_A 최대 = max(주행 V_bat,max/2, 충전 min(V_bat,max/2 + R_A·375 A, 500 V 충전기 한계 500 − R_CH·375 A))
          (R_A = 9.0 mΩ/4 = 2.25 mΩ, R_CH = 5.55 mΩ, E18). 기준: 정상 V_A 최대 ≤ 끔 문턱 − 2 V. 사양 설정(468/463 V)은 이를 넘는
          팩에 쓸 수 없다(범위로 명시).
     (S2) 넘는 팩(R2-W460)의 설정: 끔 = 올림(그 팩들의 정상 V_A 최대 + 2 V), 켬 = 끔 + 5 V. 한도: V_A ≤ 530 V(V_W 460 V + Stage B
          직렬 포트 ±90 V − 여유 20 V. C_A 600 V·Stage A 0.8 × 750 V보다 낮음). 사건: E26 'R2W' 구조, V_bat ∈ {940.8 V(224s 최대),
          995.8 V(500 V 충전기로 375 A 충전이 되는 최대)} × 부하 {0, 20 + 5 kW} × {유지, 감소} × 통신 지연 {0, 10 ms} = 16개.
          저항·스위치 규칙과 기준(C1은 530 V)은 clamp와 같다. 선정: clamp에서 고른 하드웨어 → 그 밖의 변형(같은 순서).
     (S3) 정보: 사건 중 Stage B 직렬 전압(V_A 최고 − 460 V). 사건 중 Stage B의 버스 유지는 모델 밖(남은 과제로 적음).

  l1 (검토 지적 1) Stage C 모델 교체 재계산. 조정형 Stage C = E22 선택안(동기 벅 + CLLC 4.8:1, L_m 33 µH, 병렬 2·2·2) 손실,
     고정이득 Stage C(①②③) = 같은 규칙의 5 kW 공진점 DCX(권선비 400/48, E22 dcx_loss). 정격: 스위치 위치·소자 수는 E22,
     스위치 VA = Σ 위치 정격 전압 × (가지 실효전류 / √2)(E15 규칙), 5 kW·최악 입력. ⑥(E25)은 조정형 2개(입력 직렬).
     E15(H5)·E25·E18(A25R)을 E36과 같은 흐름으로 다시 계산한다. 판정 규칙은 E15·E18·E25 그대로이고, H5 판정·가치 지도의
     성립·최선 칸·E25 결론 문장이 E36과 같은지 보고한다(새 합격 기준 없음).

  l2 (검토 지적 5·6) 충전 손실. E18 팩별 150·225 kW 충전 손실을 위상 전류 제곱 환산 대신 E32 스위칭 모의(그 팩의 V_bat =
     셀 3.7 V × 직렬수, 위상 전류 = P / (V_A·위상 수), 충전 방향)로 직접 계산한다. 640·800·920 V 값은 375 A 정전류(입력
     120·150·172.5 kW)로 표기한다. 판정 없음(정보 갱신).

  p6 Stage C 일시 정지(E17 sc_pause): E29 연동 강등 74사례. 기준: E29 seq와 같은 판정 74/74, 그리고 E34 P6(바이패스 소프트
     투입, EPC2305 1개가 모두 받음: 100 °C + Foster ΔT ≤ 150 °C, 직렬 ≤ 0.8 × 150 V, 바이패스 전류 ≤ 329 A)를 74사례 모두에.
     정보: Stage C 일시 정지 시간(재개 램프 포함)과 48 V 배터리가 맡는 에너지.

  f2 이중 고장 400 V 부하 정지(E17 load_stop): E29 F2 4사례(C_A 2.4 mF, 방전 저항 없음) × 정지 램프 {1, 2, 3, 5} ms.
     기준: E29 failsafe 판정(경로전류 5 ms 포함) 4/4 + E34 P7(H-브리지 역방향 도통 T_J ≤ 150 °C, 소자 첨두 ≤ 164.5 A).
     선정(요구값): 4/4 통과하고 직렬 전압 첨두 ≤ 100 V(직렬 전압 비교기 문턱 VS_HW)인 가장 긴 램프.

■ 실행 경과(검토 진단과의 관계)
  p6·f2의 대책은 기준 커밋 전 검토 진단(저장소 밖, 판정 아님)에서 찾았다: Stage C 일시 정지 74/74·최악 0.036 J, 부하 정지 1–3 ms
  4/4(직렬 ≤ 95 V), 5 ms 4/4(직렬 114 V). 이 실행은 같은 로직을 공용 모듈의 선택 인자로 옮겨 기준대로 판정한다.

  l1 1차 실행(2026-10-29): E15는 끝났지만 E25가 R2 정격의 'stageC_pre'(전단) 항목을 찾지 못해 멈췄다. 조정형 Stage C 정격을 한 항목으로
  합쳐 넣었기 때문이다(구현 오류). 조정형을 DCX(stageC)와 전단 동기 벅(stageC_pre)으로 나눠 넣게 고쳐 l1부터 다시 실행했다(기준 그대로).

■ 실행   python E38_review_response.py clamp hv l1 l2 p6 f2 table
■ 결과   results/E38/*.json
"""
import json
import math
import sys
from multiprocessing import Pool

import numpy as np

from common import load_json, outdir, save_json, verdict, workers
import E34_parts_rating as E34

EID = "E38"
CA_R, RA_A25 = 2.4e-3, 9.0e-3
V_LIM = 470.
# ---- SP 저항(데이터시트 rev 7/25-1) ----------------------------------------------------------------------------
TOL, DRIFT = 0.10, 0.05
TCR_POS, TCR_NEG = 0.002, -0.0008            # [1/°C]
T_REF, T_AMB = 25., (-40., 85.)
E_RES, T_RES_MAX, T_RES_PWR = 15000., 350., 40.
C_TH = E_RES / (T_RES_MAX - T_RES_PWR)       # 48.4 J/K(가정)
E_EVT = 7000.
R_WIRE = 3e-3
V_DROP_MAX = 2.05
GRID = {1: (1.0, 1.1, 1.2), 2: (1.5, 1.6, 1.8, 2.0, 2.2), 3: (1.8, 2.2, 2.7, 3.0)}
OFFS = (463., 458.)
# ---- 고전압 팩 ----------------------------------------------------------------------------------------------
R_A4 = RA_A25 / 4; R_CH = 5.55e-3; I_CH = 375.; CHG_VMAX = 500.
HV_LIM = 530.; V_W = 460.
VS_HW = 100.


def kfac(n):
    dT = E_EVT / n / C_TH
    Th = T_AMB[1] + dT
    kmax = (1 + TOL) * (1 + DRIFT) * (1 + TCR_POS * (Th - T_REF))
    kmin = (1 - TOL) * (1 - DRIFT) * min(1 + TCR_POS * (T_AMB[0] - T_REF), 1 + TCR_NEG * (Th - T_REF))
    return dict(dT=dT, T_hot=Th, kmax=kmax, kmin=kmin)


def corners(n, Rb):
    k = kfac(n)
    return dict(max=dict(R=Rb * k["kmax"] + R_WIRE, vdrop=V_DROP_MAX), min=dict(R=Rb * k["kmin"], vdrop=0.))


# ======================================================================================================
# 스위치 후보(가장 큰 온도 값 규칙)
# ======================================================================================================
def switches():
    out = {}
    g = E34.ds("FF450R12ME4P")["igbt"]
    out["FF450R12ME4P"] = dict(kind="igbt", E_on=max(g["E_on_mJ"].values()) * 1e-3, E_off=max(g["E_off_mJ"].values()) * 1e-3,
                               V_ref=600., I_ref=450., V_ce=max(g["V_CEsat_450A_V"].values()), I_pulse=g["I_CRM_A"],
                               V_rated=g["V_CES_V"], T_max=g["T_vj_op_max_C"], therm=[(E34.T_H_IGBT, g["R_thJH_KperW"])])
    import glob
    for p in sorted(glob.glob(str(E34.DS_DIR / "E37_sic_*.json"))):
        d = json.loads(open(p, encoding="utf-8").read()); m = d["mosfet"]
        th = []
        if m.get("R_thJC_KperW"):
            th.append((E34.T_C_SEMI, m["R_thJC_KperW"]))
        if m.get("R_thJH_KperW"):
            th.append((E34.T_H_IGBT, m["R_thJH_KperW"]))
        elif m.get("R_thJC_KperW") and m.get("R_thCH_KperW"):
            th.append((E34.T_H_IGBT, m["R_thJC_KperW"] + m["R_thCH_KperW"]))
        cond = m.get("E_cond_num") or {}
        out[d["part"]] = dict(kind="mosfet", E_on=max(m["E_on_mJ"].values()) * 1e-3, E_off=max(m["E_off_mJ"].values()) * 1e-3,
                              V_ref=cond.get("V"), I_ref=cond.get("I"), R_on=max(m["R_DSon_mohm"].values()) * 1e-3,
                              I_pulse=m.get("I_DM_A"), V_rated=m["V_DSS_V"], T_max=m["T_vj_op_max_C"], therm=th)
    return out


# ======================================================================================================
# clamp·hv 공용: 사건 실행(가지 기록)
# ======================================================================================================
def _ev(args):
    n, Rc, vdrop, on, off, kw = args
    import E26_charging_stop as E26
    E26.BUS["CA"] = CA_R; E26.RA_MOD = RA_A25
    E26.CL = dict(E26.CL, on=on, off=off, R=Rc, n=n, vdrop=vdrop)
    r = E26.run_event(**kw, rec_every=1, full_trace=True)
    tr = np.array(r.pop("trace"))
    t, vA, icl = tr[:, 0], tr[:, 1], tr[:, 5] / n                 # 가지 전류
    on_ = icl > 0
    k_on = np.flatnonzero(~on_[:-1] & on_[1:]) + 1
    k_off = np.flatnonzero(on_[:-1] & ~on_[1:]) + 1
    dt = float(t[1] - t[0])
    span = float(t[k_off[-1] - 1] - t[k_on[0]]) if len(k_on) and len(k_off) else float(on_.sum() * dt)
    return dict(n=n, R=Rc, vdrop=vdrop, on=on, off=off, **{k: kw[k] for k in ("Vbat", "P400", "PC", "arch", "prof", "t_comm")},
                vA_max=float(r["vA_max"]), vb_max=float(r["vb_max"]), E_branch_J=float(r["E_clamp_J"]) / n,
                t_on_ms=float(r["t_clamp_on_ms"]), n_on=int(len(k_on)), span_s=span, i_max=float(icl.max()),
                S_on=float(np.sum(vA[k_on] * icl[k_on])), S_off=float(np.sum(vA[k_off - 1] * icl[k_off - 1])),
                S_i=float(np.sum(icl[on_]) * dt), S_i2=float(np.sum(icl[on_] ** 2) * dt))


def thermal(rows, sw):
    if not sw.get("V_ref") or not sw.get("I_ref") or not sw.get("therm"):
        return dict(T=None, note="켬·끔 에너지 조건 또는 열저항 숫자 없음")
    worst = None
    for r in rows:
        if r["n_on"] == 0 or r["span_s"] <= 0:
            continue
        E_on = sw["E_on"] * r["S_on"] / (sw["V_ref"] * sw["I_ref"]); E_off = sw["E_off"] * r["S_off"] / (sw["V_ref"] * sw["I_ref"])
        E_c = sw["V_ce"] * r["S_i"] if sw["kind"] == "igbt" else sw["R_on"] * r["S_i2"]
        P = (E_on + E_off + E_c) / r["span_s"]
        T = max(Tb + P * Rth for Tb, Rth in sw["therm"])
        if worst is None or T > worst["T"]:
            worst = dict(T=T, P=P, E_on=E_on, E_off=E_off, E_cond=E_c, ev=dict(arch=r["arch"], Vbat=r["Vbat"], P400=r["P400"],
                                                                               prof=r["prof"], t_comm=r["t_comm"]))
    return worst or dict(T=E34.T_H_IGBT, note="켜지지 않음")


def judge_variant(rmax, rmin, sws, vlim):
    """rmax·rmin: 같은 변형의 두 모서리 사건 기록."""
    c1 = max(max(r["vA_max"], r["vb_max"]) for r in rmax)
    E_b = max(r["E_branch_J"] for r in rmax + rmin)
    imax = max(r["i_max"] for r in rmin)
    vmax = max(r["vA_max"] for r in rmax + rmin)
    out = dict(C1_V=c1, C1=bool(c1 <= vlim), E_branch_max_J=E_b, E=bool(E_b <= E_RES), i_branch_max=imax, vA_max=vmax,
               n_on_max=max(r["n_on"] for r in rmax + rmin), t_on_max_ms=max(r["t_on_ms"] for r in rmax + rmin), switches={})
    for sn, sw in sws.items():
        tmax = thermal(rmax, sw); tmin = thermal(rmin, sw)
        Ts = [x["T"] for x in (tmax, tmin) if x.get("T") is not None]
        ok_i = sw.get("I_pulse") is not None and imax <= E34.I_DER * sw["I_pulse"]
        ok_v = vmax <= E34.V_DER * sw["V_rated"]
        ok_t = len(Ts) == 2 and max(Ts) <= sw["T_max"]
        out["switches"][sn] = dict(ok=bool(ok_i and ok_v and ok_t and out["C1"] and out["E"]), I=bool(ok_i), I_lim=None if sw.get("I_pulse") is None else E34.I_DER * sw["I_pulse"],
                                   V=bool(ok_v), T=bool(ok_t), T_vj=max(Ts) if Ts else None, T_lim=sw["T_max"], at_Rmax=tmax, at_Rmin=tmin)
    return out


def _run_variants(variants, events, on_off):
    """variants: [(n, Rb, off)], on_off(off) → on. 반환: {(n, Rb, off, corner): rows}"""
    jobs = []
    for n, Rb, off in variants:
        for cn, c in corners(n, Rb).items():
            for e in events:
                jobs.append((n, c["R"], c["vdrop"], on_off(off), off, e, (n, Rb, off, cn)))
    with Pool(workers()) as p:
        res = p.map(_ev, [j[:6] for j in jobs], chunksize=4)
    out = {}
    for j, r in zip(jobs, res):
        out.setdefault(j[6], []).append(r)
    return out


def _select(table, order_sw, prefer=None):
    """table: [(n, Rb, off, judged)] → 선정 규칙(가지 수 → 스위치 순서 → 끔 463 → 큰 R_b)."""
    cands = []
    for n, Rb, off, j in table:
        for k, sn in enumerate(order_sw):
            if j["switches"][sn]["ok"]:
                cands.append(((0 if prefer and (n, Rb, sn) == prefer else 1), n, k, -off, -Rb, dict(n=n, R_b=Rb, off=off, switch=sn)))
    if not cands:
        return None
    return min(cands, key=lambda x: x[:5])[5]


def clamp():
    import E26_charging_stop as E26
    evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
    variants = [(n, Rb, off) for n, rs in GRID.items() for Rb in rs for off in OFFS]
    raw = _run_variants(variants, evs, lambda off: 468.)
    sws = switches(); order = ["FF450R12ME4P"] + [k for k in sws if k != "FF450R12ME4P"]
    table = []; rows = []
    for n, Rb, off in variants:
        j = judge_variant(raw[(n, Rb, off, "max")], raw[(n, Rb, off, "min")], sws, V_LIM)
        k = kfac(n); c = corners(n, Rb)
        j.update(n=n, R_b=Rb, off=off, R_max=c["max"]["R"], R_min=c["min"]["R"], kmax=k["kmax"], kmin=k["kmin"], dT_self=k["dT"])
        table.append((n, Rb, off, j)); rows.append(j)
        print("  n %d R_b %.1f Ω 끔 %.0f V: R %.3f–%.3f Ω, C1 %.2f V %s, 가지 전류 %.0f A, 가지 에너지 %.0f J, 켬 %d번 | %s"
              % (n, Rb, off, c["min"]["R"], c["max"]["R"], j["C1_V"], "통과" if j["C1"] else "불통과", j["i_branch_max"], j["E_branch_max_J"],
                 j["n_on_max"], ", ".join("%s %s(%s)" % (sn, "✓" if v["ok"] else "✗", "%.0f °C" % v["T_vj"] if v["T_vj"] else "-")
                                        for sn, v in j["switches"].items())))
    sel = _select(table, order)
    verdict("(Q1) V_A 클램프 재선정(공차·온도계수·노화·배선·스위치 강하, 150 °C 손실)", sel is not None, str(sel))
    save_json(EID, "clamp", dict(rows=rows, selected=sel, resistor=dict(TOL=TOL, DRIFT=DRIFT, TCR=[TCR_POS, TCR_NEG], T_amb=T_AMB, C_th=C_TH,
                                                                          E_evt=E_EVT, R_wire=R_WIRE, V_drop=V_DROP_MAX),
                                 kfac={n: kfac(n) for n in GRID}, raw={"%d_%.1f_%.0f_%s" % k: v for k, v in raw.items()}))


# ======================================================================================================
# hv
# ======================================================================================================
def _packs():
    import E18_industry_value_map as E18
    out = {}
    for ns in E18.CELLS:
        out["%ds" % ns] = dict(ns=ns, vmax=ns * E18.V_CELL[1])
    out["spec"] = dict(ns=None, vmax=920.)
    return out


def hv():
    import E26_charging_stop as E26
    P = _packs(); rows = {}
    vchg = CHG_VMAX - R_CH * I_CH
    for k, p in P.items():
        drive = p["vmax"] / 2; chg = min(p["vmax"] / 2 + R_A4 * I_CH, vchg)
        vmx = max(drive, chg)
        rows[k] = dict(vbat_max=p["vmax"], vA_drive=drive, vA_charge=chg, vA_normal_max=vmx, spec_ok=bool(vmx <= 463. - 2.))
        print("  %-5s V_bat 최대 %.1f V: 정상 V_A 최대 %.2f V(주행 %.2f, 충전 %.2f) → 사양 설정(끔 463 V) %s"
              % (k, p["vmax"], vmx, drive, chg, "가능" if rows[k]["spec_ok"] else "불가"))
    hi = [k for k, r in rows.items() if not r["spec_ok"]]
    out = dict(packs=rows, spec_limit_V=461., hv_packs=hi)
    if not hi:
        verdict("(Q2) 사양 설정이 모든 팩에서 정상 운전 중 켜지지 않음", True, "")
        save_json(EID, "hv", out); return
    off_w = math.ceil(max(rows[k]["vA_normal_max"] for k in hi) + 2.); on_w = off_w + 5.
    print("  고전압 팩 %s → W460 설정: 켬 %.0f V·끔 %.0f V, 한도 V_A ≤ %.0f V" % (hi, on_w, off_w, HV_LIM))
    vb_ev = (940.8, 2 * vchg)
    evs = [dict(Vbat=vb, P400=P400, PC=PC, arch="R2W", clamp=True, prof=prof, t_comm=tc, tend=E26.T_STOP + tc + 8e-3)
           for vb in vb_ev for (P400, PC) in ((0., 0.), (20e3, 5e3)) for prof in ("hold", "ramp") for tc in (0., 10e-3)]
    sel1 = load_json(EID, "clamp")["selected"]
    variants = [(n, Rb, off_w) for n in (2, 3) for Rb in (1.5, 1.6, 1.8, 2.0, 2.2, 2.7, 3.0)]
    if sel1 and (sel1["n"], sel1["R_b"], off_w) not in variants:
        variants.insert(0, (sel1["n"], sel1["R_b"], off_w))
    raw = _run_variants(variants, evs, lambda off: on_w)
    sws = switches(); order = ["FF450R12ME4P"] + [k for k in sws if k != "FF450R12ME4P"]
    table = []; vr = []
    for n, Rb, off in variants:
        j = judge_variant(raw[(n, Rb, off, "max")], raw[(n, Rb, off, "min")], sws, HV_LIM)
        c = corners(n, Rb)
        j.update(n=n, R_b=Rb, off=off, on=on_w, R_max=c["max"]["R"], R_min=c["min"]["R"], series_max_V=j["vA_max"] - V_W)
        table.append((n, Rb, off, j)); vr.append(j)
        print("  W460 n %d R_b %.1f Ω: V_A 최고 %.2f V %s, 가지 전류 %.0f A, 직렬 %.1f V | %s"
              % (n, Rb, j["C1_V"], "통과" if j["C1"] else "불통과", j["i_branch_max"], j["series_max_V"],
                 ", ".join("%s %s(%s)" % (sn, "✓" if v["ok"] else "✗", "%.0f °C" % v["T_vj"] if v["T_vj"] else "-") for sn, v in j["switches"].items())))
    prefer = (sel1["n"], sel1["R_b"], sel1["switch"]) if sel1 else None
    sel = _select(table, order, prefer)
    out.update(W460=dict(on=on_w, off=off_w, limit=HV_LIM, events=evs, rows=vr, selected=sel,
                         same_hw_as_spec=bool(sel and prefer and (sel["n"], sel["R_b"], sel["switch"]) == prefer)))
    verdict("(Q2) 고전압 팩(R2-W460) V_A 보호 설정 %.0f/%.0f V" % (on_w, off_w), sel is not None, str(sel))
    save_json(EID, "hv", out)


# ======================================================================================================
# l1: Stage C 모델 교체
# ======================================================================================================
def stage_c_models():
    import E15_baseline_loss_rating as E15
    import E22_stage_c_regulated as E22
    c = E22.selected(True); fd = E22.front_design(c)
    cf = dict(c, **E22.dcx_params(400. / 48., c["np"], fr=c["fr"]))
    orig = E15.stage_c

    def stage_c(Vbus, Po, regulated):
        if regulated:
            pd, _ = E22.dcx_loss(c, Po, E22.VO_NOM, c["np"], c["ns"])
            pf, _ = E22.front_loss(c, fd, Vbus, c["n"] * E22.VO_NOM, Po + pd["total"], c["nsw"])
            l = pd["total"] + pf["total"]
        else:
            pd, _ = E22.dcx_loss(cf, Po, E22.VO_NOM, c["np"], c["ns"])
            l = pd["total"]
        return Po + l, l

    # 정격: 5 kW, 최악 입력(E22 VBUS_GRID)
    _, xA = E22.dcx_loss(c, E22.PO_MAX, E22.VO_NOM, c["np"], c["ns"])
    _, xF = E22.dcx_loss(cf, E22.PO_MAX, E22.VO_NOM, c["np"], c["ns"])
    IL = fd["IL_max"] * math.sqrt(1 + E22.RIPPLE ** 2 / 12)
    regA = dict(positions=8, devices=4 * c["np"] + 4 * c["ns"],                                  # DCX(1차·2차 브리지)
                switch_kVA=(4 * 650 * xA["Ip"] / math.sqrt(2) + 4 * 150 * xA["Is"] / math.sqrt(2)) / 1e3,
                rated_kW=E22.PO_MAX / 1e3, magnetics=1)
    regF = dict(positions=2, devices=2 * c["nsw"], switch_kVA=2 * 650 * IL / math.sqrt(2) / 1e3,       # 전단 동기 벅
                rated_kW=E22.PO_MAX / 1e3, magnetics=1)
    fixF = dict(positions=8, devices=4 * c["np"] + 4 * c["ns"],
                switch_kVA=(4 * 650 * xF["Ip"] / math.sqrt(2) + 4 * 150 * xF["Is"] / math.sqrt(2)) / 1e3, rated_kW=E22.PO_MAX / 1e3,
                magnetics=1)
    return stage_c, orig, (regA, regF), fixF, dict(reg=dict(Lm=c["Lm"], n=c["n"], front=c["front"]), fix=dict(Lm=cf["Lm"], n=cf["n"]))


def l1():
    import os
    import E15_baseline_loss_rating as E15
    import E25_motor_boost_comparison as E25
    import E36_a25r_impact as E36
    from common import outdir as od
    sc, orig, (regA, regF), fixF, info = stage_c_models()
    E15.stage_c = sc
    r0 = E15.ratings

    def ratings(SAm):
        r = r0(SAm)
        for k, v in r.items():
            if k == "extra":
                continue
            parts = dict(v["parts"])
            if "stageC_pre" in parts:                                       # 조정형: DCX(stageC) + 전단 벅(stageC_pre)
                parts["stageC"] = regA; parts["stageC_pre"] = regF
            else:
                parts["stageC"] = fixF
            tot = {m: sum(x[m] for x in parts.values()) for m in ("positions", "devices", "switch_kVA", "rated_kW", "magnetics")}
            r[k] = dict(parts=parts, total=tot)
        return r
    E15.ratings = ratings
    E25.stage_c_rating_x2 = lambda: dict(positions=2 * (regA["positions"] + regF["positions"]), devices=2 * (regA["devices"] + regF["devices"]))
    made = set()

    def sj(eid, name, obj):
        made.add(name); return save_json(EID, "l1_" + name, obj)

    def lj(eid, name):
        if eid == "E36" and name in made:
            return load_json(EID, "l1_" + name)
        return load_json(eid, name)
    E36.save_json = sj; E36.load_json = lj; E36.outdir = lambda eid: od(EID)
    E25.outdir = lambda eid: od(EID)                                    # E25 그림도 E38 폴더로(E36 결과를 덮어쓰지 않게)
    print("== l1 E15(H5) ==", flush=True); E36.e15()
    print("== l1 E25 ==", flush=True); E36.e25()
    print("== l1 E18 ==", flush=True); E36.e18()
    for f in ("e25_motor_boost.png", "e18_R1_value_map.png", "e18_A25R_value_map.png"):
        if (od(EID) / f).exists():
            os.replace(od(EID) / f, od(EID) / ("l1_" + f))
    # E36과 대조
    a, b = load_json("E36", "e15_comparison"), load_json(EID, "l1_e15_comparison")
    cmp = dict(stage_c=info, ratings_stageC=dict(regulated_dcx=regA, regulated_front=regF, fixed=fixF),
               aux_W={s: [a["results"][s]["drive_typ"]["avg_loss_W"], b["results"][s]["drive_typ"]["avg_loss_W"]] for s in a["results"]},
               ratings={s: [a["ratings"][s]["total"], b["ratings"][s]["total"]] for s in a["ratings"] if s != "extra"},
               H5=[a["judge"]["H5_metric_pass"], b["judge"]["H5_metric_pass"]], H5_band3=[a["judge_band3"]["H5_metric_pass"], b["judge_band3"]["H5_metric_pass"]],
               e25_statements=[load_json("E36", "e25_statements")["A25R"], load_json(EID, "l1_e25_statements")["A25R"]])
    m0, m1 = load_json("E36", "e18_A25R_value_map"), load_json(EID, "l1_e18_A25R_value_map")
    diff = []
    for pk in m0["packs"]:
        for cl in m0["packs"][pk]["best"]:
            x, y = m0["packs"][pk]["best"][cl], m1["packs"][pk]["best"][cl]
            if x["best"] != y["best"] or sorted(x["feasible"]) != sorted(y["feasible"]):
                diff.append(dict(pack=pk, cls=cl, E36=x, E38=y))
    cmp["e18_changed"] = diff
    save_json(EID, "l1_compare", cmp)
    print("  보조 평균 E36 → E38:", {s: "%.1f → %.1f" % tuple(v) for s, v in cmp["aux_W"].items()})
    print("  정격(위치·VA) E36 → E38:", {s: "%d/%.0f → %d/%.0f" % (v[0]["positions"], v[0]["switch_kVA"], v[1]["positions"], v[1]["switch_kVA"])
                                    for s, v in cmp["ratings"].items()})
    verdict("(l1) H5 판정이 E36과 같음(엄격·3 %)", cmp["H5"][0] == cmp["H5"][1] and cmp["H5_band3"][0] == cmp["H5_band3"][1],
            "E36 %s / E38 %s" % (cmp["H5"][0], cmp["H5"][1]))
    verdict("(l1) E18 성립·최선 칸이 E36과 같음", not diff, "바뀐 칸 %d" % len(diff))
    verdict("(l1) E25 결론 문장이 E36과 같음", cmp["e25_statements"][0] == cmp["e25_statements"][1], "")


# ======================================================================================================
# l2: 충전 손실 직접 계산
# ======================================================================================================
def _chg_point(args):
    import E32_stage_a_25k as E32
    return E32._e15_point(args)


def l2():
    import E18_industry_value_map as E18
    import E15_baseline_loss_rating as B
    m = load_json("E36", "e18_A25R_value_map")
    P = {"%ds" % ns: dict(ns=ns) for ns in E18.CELLS}; P["spec"] = dict(ns=219.05)
    jobs = []; meta = []
    for pk, p in P.items():
        vA = p["ns"] * 3.7 / 2
        for Pt in (150e3, 225e3):
            nph = 2 * math.ceil(Pt / (vA * E18.I_PH_CH) / 2)
            iph = Pt / (vA * nph)
            jobs.append((2 * vA, iph, -1.)); meta.append((pk, Pt, nph, iph, vA))
    jobs += [(V, I_CH / 8, -1.) for V in (640., 800., 920.)]
    with Pool(workers()) as pool:
        res = pool.map(_chg_point, jobs, chunksize=1)
    out = dict(rows=[], spec_points={})
    for (pk, Pt, nph, iph, vA), r in zip(meta, res[:len(meta)]):
        loss = nph * r["ploss_ph"] + nph / 2 * B.K["ctrl"]
        old = m["packs"][pk]["charging"]["loss_%.0fkW_W" % (Pt / 1e3)]
        out["rows"].append(dict(pack=pk, P_kW=Pt / 1e3, nph=nph, iph=iph, vbat=2 * vA, ploss_ph=r["ploss_ph"], loss_W=loss, e18_W=old,
                                diff_pct=100 * (loss / old - 1)))
        print("  %-5s %3.0f kW: %2d위상 × %.1f A(V_bat %.0f V) → %.0f W(E18 제곱 환산 %.0f W, %+.0f %%)" % (pk, Pt / 1e3, nph, iph, 2 * vA, loss, old, 100 * (loss / old - 1)))
    for V, r in zip((640., 800., 920.), res[len(meta):]):
        out["spec_points"]["%.0fV" % V] = dict(I_A=I_CH, P_in_kW=V / 2 * I_CH / 1e3, loss_W=8 * r["ploss_ph"] + 4 * B.K["ctrl"])
        print("  %.0f V·375 A(입력 %.1f kW): %.0f W" % (V, V / 2 * I_CH / 1e3, out["spec_points"]["%.0fV" % V]["loss_W"]))
    save_json(EID, "l2", out)


# ======================================================================================================
# p6·f2
# ======================================================================================================
def _soft(m, tr):
    t, lg = tr["t"], tr["log"]
    F = E34.epc_foster()
    p = np.abs(lg[:, 1] * lg[:, 6]); dt = float(t[1] - t[0])
    dT = E34.foster_dT(F, t, p)
    act = np.flatnonzero(p > .1 * p.max()) if p.max() > 0 else np.array([0])
    return dict(soft_energy_J=m["soft_energy_J"], E_byp_J=float(p.sum() * dt), P_pk_W=float(p.max()), span10_ms=float((t[act[-1]] - t[act[0]]) * 1e3),
                dT_one=float(dT.max()), vs_max_soft=float(np.abs(lg[p > 1., 1]).max()) if (p > 1.).any() else 0., ib_max=float(np.abs(lg[:, 6]).max()))


def _p6_job(job):
    import E17_protection_integration as E17
    import E29_sals_degradation as E29
    tag = job.pop("_tag"); extra = job.pop("_extra")
    job["sc_pause"] = True
    m = E17.r2_run(job)
    tr = m["trace"]
    s = _soft(m, tr)
    info = dict(sc_pause_ms=m.get("sc_pause_ms"), sc_resume_ms=m.get("sc_resume_ms"))
    r = E29.summarize(m, extra); r.pop("sals", None)
    r.update(tag=tag, soft=s, **info)
    return r


def p6():
    import E29_sals_degradation as E29
    d = E34.ds("EPC2305")["ratings"]
    jobs = E29.seq_jobs()
    with Pool(workers()) as p:
        rows = p.map(_p6_job, jobs, chunksize=1)
    T_lim, V_lim, I_lim = d["T_J_max_C"], E34.V_DER * d["V_DS_V"], E34.I_DER * d["I_DM_A"] * 2
    sc_kW = max(E29.MIXES[m]["sc"] for m in E29.MIXES) / 1e3
    for r in rows:
        s = r["soft"]
        r["P6"] = dict(Tj=E34.T_C_SEMI + s["dT_one"], ok=bool(E34.T_C_SEMI + s["dT_one"] <= T_lim and s["vs_max_soft"] <= V_lim and s["ib_max"] <= I_lim))
        if r["sc_pause_ms"] is not None and r["sc_resume_ms"] is not None:
            r["pause_ms"] = r["sc_resume_ms"] - r["sc_pause_ms"] + sc_kW / 4.
            r["batt48_J"] = sc_kW * 1e3 * r["pause_ms"] * 1e-3
    n_seq = sum(r["pass_"] for r in rows); n_p6 = sum(r["P6"]["ok"] for r in rows)
    w = max(rows, key=lambda r: r["P6"]["Tj"])
    pm = [r["pause_ms"] for r in rows if r.get("pause_ms") is not None]
    print("  E29 판정 %d/%d, P6 %d/%d. 최악 %s: %.3f J, 첨두 %.0f W, T_J %.1f °C, 직렬 %.1f V. Stage C 일시 정지 %.1f–%.1f ms"
          % (n_seq, len(rows), n_p6, len(rows), w["tag"], w["soft"]["soft_energy_J"], w["soft"]["P_pk_W"], w["P6"]["Tj"], w["soft"]["vs_max_soft"], min(pm), max(pm)))
    bad = [(r["tag"], [k for k, v in r["checks"].items() if not v]) for r in rows if not r["pass_"]]
    if bad:
        print("  불통과:", bad)
    verdict("(p6) Stage C 일시 정지: E29 연동 강등 판정", n_seq == len(rows), "%d/%d" % (n_seq, len(rows)))
    verdict("(p6) 바이패스 소프트 투입 EPC2305 1개(E34 P6)", n_p6 == len(rows), "%d/%d, 최악 %.1f °C" % (n_p6, len(rows), w["P6"]["Tj"]))
    save_json(EID, "p6", dict(rows=rows, limits=dict(T=T_lim, V=V_lim, I=I_lim), pause_ms=[min(pm), max(pm)],
                              batt48_J_max=max(r.get("batt48_J", 0.) for r in rows)))


def _f2_job(args):
    case, V, ramp = args
    import E17_protection_integration as E17
    import E29_sals_degradation as E29
    det = load_json("E29", "failsafe")["dab_det_ms"]["%s_%.0f" % (case, V)]
    t2 = E17.T_EV + det * 1e-3 + E29.T_EV2
    job = dict(case=case, V=V, P=E29.P0, event="dab", policy="brk_hold", event2=t2, duration=t2 + 10e-3, keep=True,
               sals=E29.sals_cfg(case, E29.MIXES["MX"], E29.SCEN["S5"]), fs_brake=True, astop=dict(E29.ASTOP, C_A=CA_R),
               load_stop=ramp, **E29.P3T)
    m = E17.r2_run(dict(job))
    tr = m.pop("trace")
    ch, zms = E29.fs_judge(m, tr)
    hb = E34._prot(("hb", "%s_%.0f_F2" % (case, V), dict(job))); hb.pop("trace", None)
    t, lg = tr["t"], tr["log"]
    return dict(tag="%s_%.0f" % (case, V), ramp_ms=ramp * 1e3, checks=ch, pass_=bool(all(ch.values())), ip_zero_ms=zms, path_peak=m["path_peak"],
                bridge_peak=m["bridge_peak"], series_peak=m["series_peak"], vlink_max=m["vlink_max"], brk_energy_J=m["brk_energy_J"],
                vbus_end=float(lg[-1, 2]), vA_end=m.get("vA_end"), load_stop_ms=m.get("load_stop_ms"),
                p7_dT=hb["dT"], p7_i_dev_max=hb["i_dev_max"], p7_Tj=E34.T_C_SEMI + hb["dT"])


def f2():
    import E29_sals_degradation as E29
    d = E34.ds("EPC2305")["ratings"]
    ramps = (1e-3, 2e-3, 3e-3, 5e-3)
    jobs = [(c, V, r) for r in ramps for c, V in E29.FS_PACKS]
    with Pool(workers()) as p:
        rows = p.map(_f2_job, jobs, chunksize=1)
    summ = {}
    for r in rows:
        r["P7"] = bool(r["p7_Tj"] <= d["T_J_max_C"] and r["p7_i_dev_max"] <= E34.I_DER * d["I_DM_A"])
        r["ok"] = bool(r["pass_"] and r["P7"])
    for ramp in ramps:
        rr = [r for r in rows if abs(r["ramp_ms"] - ramp * 1e3) < 1e-9]
        summ["%.0f" % (ramp * 1e3)] = dict(n_pass=sum(r["ok"] for r in rr), series_max=max(r["series_peak"] for r in rr),
                                          ip_zero_ms=[min(r["ip_zero_ms"] for r in rr if r["ip_zero_ms"] is not None),
                                                      max(r["ip_zero_ms"] if r["ip_zero_ms"] is not None else 99. for r in rr)],
                                          vbus_min_end=min(r["vbus_end"] for r in rr), p7_Tj=max(r["p7_Tj"] for r in rr))
        s = summ["%.0f" % (ramp * 1e3)]
        print("  정지 램프 %.0f ms: %d/4, |i_p| ≤ 1 A까지 %.2f–%.2f ms, 직렬 최대 %.1f V, 버스 끝 ≥ %.0f V, P7 %.0f °C"
              % (ramp * 1e3, s["n_pass"], *s["ip_zero_ms"], s["series_max"], s["vbus_min_end"], s["p7_Tj"]))
        for r in rr:
            if not r["ok"]:
                print("    불통과 %s: %s" % (r["tag"], [k for k, v in r["checks"].items() if not v] + ([] if r["P7"] else ["P7"])))
    ok = [r for r in ramps if summ["%.0f" % (r * 1e3)]["n_pass"] == 4 and summ["%.0f" % (r * 1e3)]["series_max"] <= VS_HW]
    sel = max(ok) if ok else None
    verdict("(f2) 이중 고장 400 V 부하 정지(방전 저항 없음): 4/4 + 직렬 ≤ 100 V인 가장 긴 램프", sel is not None,
            "선정 %s ms" % (None if sel is None else sel * 1e3))
    save_json(EID, "f2", dict(rows=rows, summary=summ, selected_ramp_ms=None if sel is None else sel * 1e3))


# ======================================================================================================
# table
# ======================================================================================================
def table():
    out = {}
    for name in ("clamp", "hv", "l1_compare", "l2", "p6", "f2"):
        try:
            out[name] = load_json(EID, name)
        except FileNotFoundError:
            out[name] = None
    c, h = out["clamp"], out["hv"]
    rows = []
    if c:
        rows.append(dict(item="Q1 V_A 클램프(사양 팩)", result=c["selected"]))
    if h:
        rows.append(dict(item="Q2 고전압 팩 범위", result=dict(hv_packs=h["hv_packs"], W460=None if "W460" not in h else
                                                             dict(on=h["W460"]["on"], off=h["W460"]["off"], selected=h["W460"]["selected"]))))
    if out["p6"]:
        rows.append(dict(item="P6 Stage C 일시 정지", result=dict(pause_ms=out["p6"]["pause_ms"], batt48_J_max=out["p6"]["batt48_J_max"])))
    if out["f2"]:
        rows.append(dict(item="F2 부하 정지 램프", result=out["f2"]["selected_ramp_ms"]))
    save_json(EID, "table", dict(rows=rows))
    for r in rows:
        print("  %s: %s" % (r["item"], r["result"]))


if __name__ == "__main__":
    for part in sys.argv[1:]:
        print("E38", part, "...", flush=True)
        globals()[part]()
