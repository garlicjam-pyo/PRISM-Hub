"""[E40] 전형값만 있는 손실 인자의 일관 규칙으로 부품 재판정, V_A 클램프 최대 켜짐 시간과 문턱 오차 예산(최종 검토 docs/45 대응).

■ 왜 필요한가
  최종 보고서 작성 전 최종 검토(docs/45, 2026-10-29)가 판정에 영향을 줄 수 있는 지적을 찾았다.
    A1  P5 클램프 스위치 CAB530M12BM3의 통과(146.5 °C)가 R_DS(on) 150 °C 전형값 3.96 mΩ에 기댄다. 데이터시트는 25 °C에서만 최대값을
        준다(전형 2.67·최대 3.55 mΩ). E39는 값이 하나뿐인 열저항에만 × 1.2를 썼다(진단: × 1.2면 152.5 °C, 판정 아님).
    A3  클램프 문턱 오차가 낮은 쪽이면 정상 충전 중 켜진 클램프가 꺼지지 않을 수 있다(배터리 경로가 살아 있으면 Stage A가 V_A를
        끔 문턱 아래에 붙잡는다). 저항에 약 350 kW가 들어가 수십 ms 안에 15 kJ를 넘는다. E26 사건은 모두 고장 사건이라 이 경우가 없다.
    A4  C_A 후보 표(E37 Q6)가 B32778 600 V를 60 µF까지만 담아 "가장 적은 개수" 선정이 바뀐다.
    B3  링크 제동 저항 LTO 150H의 75 J/0.1 s는 단발(accidental) 값이다. 반복 펄스는 52.8 J(k = 0.7).
    B13 같은 계열의 불일치: P1·P6·P7에는 값 하나뿐인 열저항 × 1.2를 쓰지 않았고 P1은 R_DS(on) 전형값, C_A 전압 기준은 470 V(W460은 511 V).
  사용자 결정(2026-10-29): 전형값만 있는 손실 인자에 하나의 규칙을 정해 P1·P5·P6·P7을 다시 판정하고, 클램프에는 최대 켜짐 시간을
  설계 변경으로 넣는다(검출 뒤 무장 방식은 쓰지 않는다). 문턱 오차 예산과 ±1 % 오차의 고장 없는 사건을 함께 본다.

■ 규칙 L: 전형값만 있는 손실 인자(실행 전에 고정)
  (L1) 저장 데이터시트 파일(data/datasheets)에 같은 양의 최대값이 어느 온도에서든 있으면, 손실 계산에 쓰는 전형값(E38·E39와 같이
       표의 가장 큰 온도 값)에 그 온도의 최대/전형 비를 곱한다.
  (L2) 최대값이 파일에 하나도 없으면 × 1.2(E39 열저항 규칙과 같은 값. 1.2는 최대·전형을 모두 주는 CAB450M12XM3 열저항 비 1.18을 올린 값).
  (L3) 열저항: 최대값이 있으면 최대값, 없으면 × 1.2(E39 R1과 같음). 과도 열임피던스(Foster 계수·Z_th 곡선)도 같은 배율.
  적용(손실 인자별):
    P5 클램프 스위치 후보 5종: R_DS(on)(SiC) 또는 V_CEsat(IGBT) — (L1)/(L2), E_on·E_off — (L2), 열저항 — (L3).
       CAB530M12BM3 R_DS(on) 3.96 × 3.55/2.67, CAB450M12XM3 4.6 × 3.7/2.6, SKM500MB120SC 6.3 × 4.7/3.8, FF2MR12KM1P 3.25 × 1.2,
       FF450R12ME4P V_CEsat 2.05 × 1.2(저장 파일에 최대값 없음). 스위칭 에너지는 다섯 품목 모두 전형값뿐이라 × 1.2.
    P1 Stage A C4MS008075U2: 도통(모델 R_ds, 125 °C 전형 보간) × 10.4/8.0 = 1.30, 바디 다이오드 V_f × 1.2(V_SD 전형만),
       출력용량 손실(C_o(er)·E_oss 전형만) × 1.2, R_thJC 0.16 × 1.2.
    P6 EPC2305 바이패스 소프트 투입: 손실은 회로의 직렬전압 × 전류(소자값 아님) → Z_thJC × 1.2만.
    P7 EPC2305 H-브리지 역방향 도통: V_SD 곡선(전형) × 1.2, Z_thJC × 1.2.
  클램프 큰 저항 모서리의 스위치 강하: E38은 2.05 V(FF450R12ME4P V_CEsat 150 °C)였다. 규칙 L에서 후보 다섯의 450 A 도통 강하
  (IGBT V_CEsat × 배율, SiC R_DS(on) × 배율 × 450 A) 가운데 가장 큰 값을 쓴다(코드가 계산해 출력한다).
  게이트 구동·배선 등 모델 밖 손실은 범위 밖이다(바꾸지 않는다).

■ 설계 변경 M: 클램프 최대 연속 켜짐 시간(실행 전에 고정)
  클램프 게이트가 t_on,max = 0.5 ms 동안 계속 켜져 있으면 끈다(스위치 지연 1 µs). 그 뒤는 보통 비교기 논리로 돌아간다
  (V_A ≥ 켬 문턱이면 다시 켠다). 근거: (i) 배터리 경로가 살아 있으면 끈 뒤 V_A가 정상값(켬 문턱 아래)으로 돌아가 다시 켜지지 않는다.
  (ii) 경로 상실이면 끈 뒤 V_A가 켬 문턱에 곧 다시 닿아 보호가 이어진다(강제 끔은 켬·끔 횟수만 늘린다). (iii) 오동작 한 번의 저항
  에너지가 수백 J로 15 kJ의 몇 % 안이다. 0.5 ms는 이 근거로 정한 값이며 결과를 보고 바꾸지 않는다.

■ 부분과 판정 기준(실행 전에 커밋. 바꾸면 그 이유와 함께 실행 경과에 적는다)
  reg  구현 확인(판정 아님): (a) E26의 새 선택 인자가 없을 때 E38 근거 파일(results/E38/clamp.json raw)의 두 사건을 차 0으로 재현,
       (b) 이 코드에 E39 규칙(배율 1, 강하 2.05 V, M 없음)을 주면 E39 사양 팩 선정 변형(가지 2개 × 1.6 Ω·끔 463 V)의 C1·가지 에너지·
       스위치별 T_vj를 상대 1e-9 안에서 재현(96사건 새로 실행).
  p5   (Q1″·Q2″) 클램프 재선정. 사건·저항 모서리·조합(max·min·mix)·자기 가열 갱신(R3)·기준 (C1)(I)(T)(E)(V)(S)는 E39와 같다.
       바뀌는 것: 규칙 L(열·손실), 강하(위), 설계 변경 M(모든 사건에 적용), 끔 458 V 변형 제외(E38 S1 규칙: 사양 팩 정상 V_A 최대
       460.84 V + 2 V > 458 V, docs/44 3.1절 주의).
       격자: 사양 팩(켬 468·끔 463 V, C1 ≤ 470 V) n = 2: {1.5, 1.6}, n = 3: {1.8, 2.0, 2.2, 2.4}, n = 4: {2.4, 2.7, 3.0, 3.3} Ω.
             W460(켬 511·끔 506 V, C1 ≤ 530 V) n = 2: {1.6, 1.8}, n = 3: {1.8, 2.0, 2.2, 2.7}, n = 4: {2.7, 3.0, 3.3} Ω.
       선정: E39 R4와 같다. 사양 팩 = 통과 변형 가운데 가지 수가 적은 것 → 큰 R_b, 스위치 = FF450R12ME4P가 통과하면 그것, 아니면
             온도 여유(T_vj,max − T_vj)가 가장 큰 SiC(같으면 전류 여유). W460 = 사양 팩 스위치가 통과하는 변형 가운데 가지 수가 적은 것
             → 큰 R_b(없으면 어떤 스위치든 같은 순서).
       정보: E39 선정(2 × 1.6 Ω·CAB530M12BM3, W460 2 × 1.8 Ω)의 E40 규칙 판정, 변형별 연속 켜짐 최장·강제 끔 횟수, 저항 하나의 크기는
             E38과 같다(891SP 15 kJ, 1–450 Ω 범위).
  thr  클램프 문턱 오차와 오동작(선정 변형, 선정 스위치, M 적용).
       오차 모형: 켬·끔 문턱에 같은 상대 오차 ε(분압기·절연 증폭기 이득 오차).
       (H) 높은 쪽: 경로 상실 사건(사양 32·W460 16), 세 조합, 문턱 × (1 + ε), ε ∈ {0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0} %.
           보고: (C1)과 선정 스위치 (T)·(E)가 모두 통과하는 가장 큰 ε = 높은 쪽 허용 오차(설계 요구로 적는다, 통과·불통과 대상 아님).
       (L) 낮은 쪽, 오동작 사건(고장 없음, 배터리 경로 정상, Stage A 4모듈 동작): t0 = 1 ms에 클램프 게이트가 비교기와 무관하게 켜진다
           (원인 — 문턱 오차와 과도, 잡음 — 을 가리지 않는 가장 나쁜 경우). 클램프가 켜지면 E26과 같이 비상 정지 신호가 나가 충전기가
           30 ms 유지 뒤 멈춘다. 사양 팩: R2, V_bat 920 V, 충전 375 A, 부하 {0, 20 + 5 kW}. W460: R2W, V_bat 1008 V(240s 최대) 주행
           (충전기 0)과 995.8 V 충전 375 A, 부하 {0, 20 + 5 kW}. 세 조합, ε ∈ {−1, −0.5, 0, +1} %. 사건 길이 t0 + 38 ms.
           기준(M 적용, 모든 사건):
             (M1) 클램프 연속 켜짐 ≤ t_on,max + 2 µs이고, 강제로 끈 뒤 사건 끝까지 다시 켜지지 않는다.
             (M2) 가지 저항 에너지 ≤ 891SP 15 kJ. 가지 전류 ≤ 0.5 × 선정 스위치 I_DM. V_A·버스 ≤ 상한(470·530 V).
             (M3) 선정 스위치 T_vj ≤ 한도: 켜짐 시간이 0.2 ms 이상인 사건은 E39 방법(사건 평균 손실 × 정상 열저항, 규칙 L).
                  0.2 ms 미만은 스위치 에너지만 보고한다(한 번의 짧은 펄스에 평균 손실 방법을 쓰면 스위칭 에너지를 µs로 나눠 뜻이 없다).
           보고: (M3)이 모든 사건에서 통과하는 가장 음의 ε = 낮은 쪽 허용 오차(설계 요구). 래치가 없는 낮은 쪽 오차(해석: 끔 문턱 × (1 + ε)
                 > 클램프가 켜진 채 Stage A가 붙잡는 V_A).
           정보: M 없이 ε = −1 %이면 클램프가 꺼지지 않는지(사건 길이 t0 + 100 ms), 가지 저항이 15 kJ에 닿는 시각. 평균모델에는 Stage A
                 동특성이 없어 정상 운전의 V_A 과도가 거의 없다(오동작을 강제로 넣는 이유). 회로 확인은 TB33.
  p1   P1 C4MS008075U2 열(규칙 L): E34 stagea와 같은 정격점(8위상, 375 A 충전, 640·800·920 V × 공칭·공차 표본 3개)을 A25R(C_A 2.4 mF)로
       다시 모의. 위치 손실 = 1.30 × 도통 + 1.2 × 다이오드 + 1.2 × 출력용량, 소자 = 위치 / 2 × 1.1, T_J = 100 °C + 소자 × 0.16 × 1.2 ≤ 150 °C
       (E34 정상 운전 기준 T_J,max − 25 °C). (V)(I)는 규칙과 무관해 E34 값을 그대로 적는다.
  p6p7 E38 근거(p6 74사례, f2 램프 3 ms 4사례)의 기록으로: P6 T_J = 100 + 1.2 × ΔT(소자 1개) ≤ 150 °C, P7 T_J = 100 + 1.2 × 1.2 × ΔT
       ≤ 150 °C. 전압·전류 기준은 E38 그대로. ΔT가 Z_th 배율과 V_SD 배율에 비례하므로 다시 모의하지 않는다.
  p8   P8 LTO 150H: E38 p6·f2(램프 3 ms) 사례의 제동 에너지 최대(사건이 0.1 s보다 짧아 사건 합 ≥ 0.1 s 창 최대) ≤ 반복 펄스 52.8 J
       (Vishay 응용 노트 51114: 100 ms 단발 75.5 J × k 0.7) → 조건부 통과(0.1 s보다 짧은 펄스의 곡선 대조는 남는다).
       반복 정격을 넘고 단발 이하이면 "단발 사건에만 성립"으로 불통과 처리한다.
  ca   (Q6′) C_A 2.4 mF: TDK B3277x 전체 표(B32774·B32776·B32778의 600 V 전부, 800 V 이상 저장 행). 기준은 E37 Q6과 같되 전압은
       V_R ≥ 530 V(W460 V_A 상한, E37은 470 V). 실효전류는 E37 ca 최댓값(공차 표본 1개, 50.6 A)이다. 선정: 개수 → 부피.
       (전류 여유가 크면 최악 탐색 없이 판정한다는 점을 보고에 적는다.)
  table 결과 요약.

■ 실행   python E40_typ_rule_rejudge.py reg p5 thr p1 p6p7 p8 ca table
■ 결과   results/E40/*.json
"""
import json
import math
import sys
from multiprocessing import Pool

import numpy as np

from common import load_json, save_json, verdict, workers
import E34_parts_rating as E34
import E38_review_response as E38
import E39_clamp_switch_rejudge as E39

EID = "E40"
F_TYP = 1.2                                   # 최대값이 없는 손실 인자의 배율(L2·L3)
T_ON_MAX = 0.5e-3                             # 설계 변경 M
I_DROP = 450.                                 # 강하 계산 전류
SPEC = dict(on=468., off=463., lim=E38.V_LIM,
            grid={2: (1.5, 1.6), 3: (1.8, 2.0, 2.2, 2.4), 4: (2.4, 2.7, 3.0, 3.3)})
W460 = dict(on=511., off=506., lim=E38.HV_LIM,
            grid={2: (1.6, 1.8), 3: (1.8, 2.0, 2.2, 2.7), 4: (2.7, 3.0, 3.3)})
EPS_HI = (0.0005, 0.001, 0.0015, 0.002, 0.003, 0.005, 0.01)
EPS_LO = (-0.01, -0.005, 0., 0.01)
T_SPUR = 1e-3
P1_K = dict(cond=10.4 / 8.0, diode=F_TYP, coss=F_TYP, rth=F_TYP)
V_CA = E38.HV_LIM


# ======================================================================================================
# 규칙 L: 스위치 손실 인자
# ======================================================================================================
def switches40(rule=True):
    """rule=False면 E39 그대로(열저항 R1만). 반환: (스위치 dict, 규칙 설명 dict)."""
    sw, rules = E39.switches39()
    if not rule:
        return sw, rules
    import glob
    ds = {}
    for p in glob.glob(str(E34.DS_DIR / "E37_sic_*.json")):
        d = json.loads(open(p, encoding="utf-8").read()); ds[d["part"]] = d["mosfet"]
    out = {}
    for name, s in sw.items():
        s = dict(s)
        txt = [rules[name]]
        s["E_on"] *= F_TYP; s["E_off"] *= F_TYP; txt.append("E_on·E_off × %.1f" % F_TYP)
        if s["kind"] == "igbt":
            g = E34.ds("FF450R12ME4P")["igbt"]
            if g.get("V_CEsat_450A_max_V"):
                k = max(g["V_CEsat_450A_max_V"].values()) / max(g["V_CEsat_450A_V"].values())
            else:
                k = F_TYP
            s["V_ce"] *= k; s["drop450"] = s["V_ce"]; txt.append("V_CEsat × %.3f" % k)
        else:
            m = ds[name]
            if m.get("R_DSon_25C_max_mohm") and m["R_DSon_mohm"].get("25"):
                k = m["R_DSon_25C_max_mohm"] / m["R_DSon_mohm"]["25"]; txt.append("R_DS(on) × %.3f(25 °C 최대/전형)" % k)
            else:
                k = F_TYP; txt.append("R_DS(on) × %.1f(최대값 없음)" % F_TYP)
            s["R_on"] *= k; s["drop450"] = s["R_on"] * I_DROP
        if s.get("foster"):
            s["foster"] = [(F_TYP * r, tau) for r, tau in s["foster"]]
        s["k_cond"] = k
        out[name] = s; rules[name] = ", ".join(txt)
    return out, rules


def vdrop40(sws):
    return max(s["drop450"] for s in sws.values())


# ======================================================================================================
# 사건 실행(E39 _ev39 + 최대 켜짐 시간·강제 켬)
# ======================================================================================================
def _ev40(args):
    br, on, off, kw, extra = args
    import E26_charging_stop as E26
    E26.BUS["CA"] = E38.CA_R; E26.RA_MOD = E38.RA_A25
    cl = dict(E26.CL, on=on, off=off, branches=[(R, vd, m) for _, R, vd, m in br])
    for k in ("t_on_max", "force_on_at"):
        cl.pop(k, None)
    cl.update(extra or {})
    E26.CL = cl
    r = E26.run_event(**kw, rec_every=1, full_trace=True)
    tr = np.array(r.pop("trace"))
    rows = E39._branch_rows(tr, kw, br, sum(m for *_, m in br))
    meta = dict(t_on_cont_max_ms=r["t_on_cont_max_ms"], n_forced_off=r["n_forced_off"], n_on_after_forced=r["n_on_after_forced"],
                clamp_on_end=r["clamp_on_end"], E_clamp_J=r["E_clamp_J"], t_clamp_on_ms=r["t_clamp_on_ms"],
                vA_min=float(tr[:, 1].min()), iA_min=float(tr[:, 4].min()), iA_max=float(tr[:, 4].max()))
    for v in rows.values():
        v.update(vA_max=float(r["vA_max"]), vb_max=float(r["vb_max"]), **meta)
    return rows


def run_jobs(jobs):
    """jobs: [(key, br, on, off, kw, extra)] → {key: [ {종류: row} per event ]}"""
    with Pool(workers()) as p:
        res = p.map(_ev40, [j[1:] for j in jobs], chunksize=2)
    out = {}
    for j, r in zip(jobs, res):
        out.setdefault(j[0], []).append(r)
    return out


def combos40(n, c, vdrop):
    out = dict(max=[("hi", c["Rmax"], vdrop, n)], min=[("lo", c["Rmin"], 0., n)])
    if n >= 2:
        out["mix"] = [("lo", c["Rmin"], 0., 1), ("hi", c["Rmax"], vdrop, n - 1)]
    return out


def judge40(recs, sws, vlim):
    j = E39.judge39(recs, sws, vlim)
    allrows = [r for evs in recs.values() for e in evs for r in e.values()]
    j["t_on_cont_max_ms"] = max(r["t_on_cont_max_ms"] for r in allrows)
    j["n_forced_off_max"] = max(r["n_forced_off"] for r in allrows)
    return j


def variant40(n, Rb, on, off, events, vlim, sws, vdrop, extra, tag=""):
    """E39 variant와 같은 (R3) 반복. extra: E26.CL에 더할 선택 인자(M)."""
    c = E39.corners39(n, Rb)
    hist = []
    for it in range(E39.N_ITER + 1):
        cbs = combos40(n, c, vdrop)
        jobs = [(cb, br, on, off, e, extra) for cb, br in cbs.items() for e in events]
        recs = run_jobs(jobs)
        j = judge40(recs, sws, vlim)
        need_hi = j["E_hi_obs"] > c["E_hi"] + 1e-9
        need_lo = j["E_lo_obs"] > c["E_lo"] + 1e-9
        passing = j["C1"] and j["E"] and any(v["ok"] for v in j["switches"].values())
        h = dict(it=it, E_hi_assumed=c["E_hi"], E_lo_assumed=c["E_lo"], E_hi_obs=j["E_hi_obs"], E_lo_obs=j["E_lo_obs"],
                 Rmax=c["Rmax"], Rmin=c["Rmin"], C1_V=j["C1_V"])
        if (need_hi or need_lo) and not passing:
            j["S"] = None; hist.append(dict(h, note="불통과 변형, 갱신 안 함")); break
        hist.append(h)
        if not (need_hi or need_lo):
            j["S"] = True; break
        if it == E39.N_ITER:
            j["S"] = False; break
        E_hi = math.ceil(j["E_hi_obs"] / E39.E_STEP) * E39.E_STEP if need_hi else c["E_hi"]
        E_lo = math.ceil(j["E_lo_obs"] / E39.E_STEP) * E39.E_STEP if need_lo else c["E_lo"]
        c = E39.corners39(n, Rb, E_hi, E_lo)
        print("    %s n %d R_b %.1f: 자기 가열 가정 갱신 E_hi %.0f J, E_lo %.0f J → R %.4f–%.4f Ω" % (tag, n, Rb, E_hi, E_lo, c["Rmin"], c["Rmax"]))
    j.update(n=n, R_b=Rb, on=on, off=off, R_max=c["Rmax"], R_min=c["Rmin"], kmax=c["kmax"], kmin=c["kmin"], iter=hist, vdrop=vdrop,
             ok_variant=bool(j["C1"] and j["E"] and j["S"] is True and any(v["ok"] for v in j["switches"].values())))
    return j, recs


def line40(j):
    return E39.line(j) + " | 연속 켜짐 최장 %.3f ms, 강제 끔 최대 %d번" % (j["t_on_cont_max_ms"], j["n_forced_off_max"])


def _slim(recs):
    """근거 파일용: 사건별·가지 종류별 집계값(열 판정을 다시 할 수 있는 양)만."""
    keep = ("Vbat", "P400", "PC", "arch", "prof", "t_comm", "kind", "R", "vdrop", "count", "vA_max", "vb_max", "E_branch_J", "n_on",
            "span_s", "i_max", "S_on", "S_off", "S_i", "S_i2", "t_on_cont_max_ms", "n_forced_off", "n_on_after_forced", "vA_min")
    return {cb: [{k: {f: r[f] for f in keep if f in r} for k, r in e.items()} for e in evs] for cb, evs in recs.items()}


def spec_events():
    import E26_charging_stop as E26
    return [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]


def hv_events():
    import E26_charging_stop as E26
    vchg = E38.CHG_VMAX - E38.R_CH * E38.I_CH
    return [dict(Vbat=vb, P400=P400, PC=PC, arch="R2W", clamp=True, prof=prof, t_comm=tc, tend=E26.T_STOP + tc + 8e-3)
            for vb in (940.8, 2 * vchg) for (P400, PC) in ((0., 0.), (20e3, 5e3)) for prof in ("hold", "ramp") for tc in (0., 10e-3)]


# ======================================================================================================
# 부분
# ======================================================================================================
def reg():
    import E26_charging_stop as E26
    raw = load_json("E38", "clamp")["raw"]
    evs = spec_events()
    keys = ("vA_max", "vb_max", "E_branch_J", "S_on", "S_off", "S_i", "S_i2", "i_max", "span_s")
    out = dict(e26=[], e39=None)
    for key, k_ev in (("2_1.6_463_max", 0), ("2_1.6_463_min", 5)):
        n, Rb, off, cn = key.split("_"); n = int(n); Rb = float(Rb); off = float(off)
        c = E38.corners(n, Rb)[cn]
        for k in ("branches", "t_on_max", "force_on_at"):
            E26.CL.pop(k, None)
        new = E38._ev((n, c["R"], c["vdrop"], 468., off, evs[k_ev]))
        d = max(abs(new[k] - raw[key][k_ev][k]) for k in keys)
        out["e26"].append(dict(key=key, ev=k_ev, diff=d))
        print("  (a) %s 사건 %d: E38 근거 재현 차 %.3g" % (key, k_ev, d))
    for k in ("branches", "t_on_max", "force_on_at"):
        E26.CL.pop(k, None)
    s39 = load_json("E39", "spec")
    row = next(r for r in s39["rows"] if r["n"] == 2 and r["R_b"] == 1.6 and r["off"] == 463.)
    sws, _ = switches40(rule=False)
    j, _ = variant40(2, 1.6, 468., 463., evs, E38.V_LIM, sws, E38.V_DROP_MAX, None, tag="reg")
    rel = lambda a, b: abs(a - b) / max(abs(b), 1e-12)
    cmp = dict(C1_V=rel(j["C1_V"], row["C1_V"]), E_branch=rel(j["E_branch_max_J"], row["E_branch_max_J"]),
               T={sn: rel(j["switches"][sn]["T_vj"], row["switches"][sn]["T_vj"]) for sn in row["switches"] if row["switches"][sn]["T_vj"]})
    out["e39"] = cmp
    print("  (b) E39 선정 변형 재현 상대 차: C1 %.2g, 에너지 %.2g, T %s" % (cmp["C1_V"], cmp["E_branch"],
                                                              {k: "%.2g" % v for k, v in cmp["T"].items()}))
    ok = all(x["diff"] == 0. for x in out["e26"]) and cmp["C1_V"] < 1e-9 and cmp["E_branch"] < 1e-9 and all(v < 1e-9 for v in cmp["T"].values())
    verdict("구현 확인(E26 기본값 재현 차 0, E39 규칙 재현 상대 ≤ 1e-9)", ok)
    out["ok"] = ok
    save_json(EID, "reg", out)


def _p5_part(cfg, events, tag, sw_first=None):
    sws, rules = switches40()
    vd = vdrop40(sws)
    extra = dict(t_on_max=T_ON_MAX)
    table = []; recs_all = {}
    for n, rs in cfg["grid"].items():
        for Rb in rs:
            j, recs = variant40(n, Rb, cfg["on"], cfg["off"], events, cfg["lim"], sws, vd, extra, tag=tag)
            table.append(j); recs_all["%d_%.1f" % (n, Rb)] = _slim(recs)
            print("  %s %s" % (tag, line40(j)), flush=True)
    return table, recs_all, sws, rules, vd


def p5():
    sws, rules = switches40()
    vd = vdrop40(sws)
    for sn, t in rules.items():
        print("  규칙 L %s: %s, 450 A 강하 %.2f V" % (sn, t, sws[sn]["drop450"]))
    print("  큰 저항 모서리 스위치 강하 %.2f V(E38 2.05 V), 최대 켜짐 시간 %.1f ms" % (vd, T_ON_MAX * 1e3))
    out = dict(rules=rules, vdrop=vd, t_on_max_ms=T_ON_MAX * 1e3, F_TYP=F_TYP,
               k_cond={sn: s["k_cond"] for sn, s in sws.items()})
    # 사양 팩
    tab, recs, *_ = _p5_part(SPEC, spec_events(), "spec")
    cands = [j for j in tab if j["ok_variant"]]
    sel = None
    if cands:
        v = min(cands, key=lambda j: (j["n"], -j["R_b"]))
        sel = dict(n=v["n"], R_b=v["R_b"], off=v["off"], on=v["on"], switch=E39.pick_switch(v, "FF450R12ME4P"))
    e39 = next((j for j in tab if j["n"] == 2 and j["R_b"] == 1.6), None)
    verdict("(Q1″) 사양 팩 V_A 클램프 재선정(규칙 L, 최대 켜짐 시간)", sel is not None, str(sel))
    if e39:
        s = e39["switches"]["CAB530M12BM3"]
        print("  정보: E39 선정(2 × 1.6 Ω·CAB530M12BM3)의 E40 판정: %s, %.2f °C" % ("통과" if s["ok"] else "불통과", s["T_vj"]))
    out["spec"] = dict(rows=tab, selected=sel, recs=recs,
                       e39_selection=None if not e39 else e39["switches"]["CAB530M12BM3"])
    # W460
    tabw, recsw, *_ = _p5_part(W460, hv_events(), "W460")
    sw1 = sel["switch"] if sel else None
    pool = [j for j in tabw if j["C1"] and j["E"] and j["S"] is True and sw1 and j["switches"][sw1]["ok"]]
    if not pool:
        pool = [j for j in tabw if j["ok_variant"]]
    selw = None
    if pool:
        v = min(pool, key=lambda j: (j["n"], -j["R_b"]))
        selw = dict(n=v["n"], R_b=v["R_b"], off=v["off"], on=v["on"], switch=E39.pick_switch(v, sw1))
    e39w = next((j for j in tabw if j["n"] == 2 and j["R_b"] == 1.8), None)
    verdict("(Q2″) 고전압 팩(R2-W460) 클램프 재선정", selw is not None, str(selw))
    if e39w:
        s = e39w["switches"]["CAB530M12BM3"]
        print("  정보: E39 W460 선정(2 × 1.8 Ω·CAB530M12BM3)의 E40 판정: %s, %.2f °C" % ("통과" if s["ok"] else "불통과", s["T_vj"]))
    out["W460"] = dict(rows=tabw, selected=selw, recs=recsw, same_hw_as_spec=bool(selw and sel and selw["switch"] == sel["switch"]),
                       e39_selection=None if not e39w else e39w["switches"]["CAB530M12BM3"])
    save_json(EID, "p5", out)


def _sel_row(part):
    d = load_json(EID, "p5")[part]; sel = d["selected"]
    if not sel:
        return None, None
    row = next(r for r in d["rows"] if r["n"] == sel["n"] and r["R_b"] == sel["R_b"])
    return sel, row


def _spur_events(part):
    if part == "spec":
        return [dict(Vbat=920., P400=P400, PC=PC, arch="R2", clamp=True, prof="hold", t_comm=0., nmod_after=4, I0=E38.I_CH)
                for (P400, PC) in ((0., 0.), (20e3, 5e3))]
    vchg = E38.CHG_VMAX - E38.R_CH * E38.I_CH
    ev = []
    for (vb, I0) in ((1008., 0.), (2 * vchg, E38.I_CH)):
        for (P400, PC) in ((0., 0.), (20e3, 5e3)):
            ev.append(dict(Vbat=vb, P400=P400, PC=PC, arch="R2W", clamp=True, prof="hold", t_comm=0., nmod_after=4, I0=I0))
    return ev


def thr():
    sws, _ = switches40()
    vd = vdrop40(sws)
    out = {}
    for part, cfg, evf in (("spec", SPEC, spec_events), ("W460", W460, hv_events)):
        sel, row = _sel_row(part)
        if not sel:
            out[part] = None; continue
        sw = {sel["switch"]: sws[sel["switch"]]}
        c = dict(Rmax=row["R_max"], Rmin=row["R_min"])
        cbs = combos40(sel["n"], c, vd)
        # (H) 높은 쪽
        hi = []
        for eps in EPS_HI:
            jobs = [(cb, br, cfg["on"] * (1 + eps), cfg["off"] * (1 + eps), e, dict(t_on_max=T_ON_MAX)) for cb, br in cbs.items() for e in evf()]
            recs = run_jobs(jobs)
            j = judge40(recs, sw, cfg["lim"])
            s = j["switches"][sel["switch"]]
            ok = bool(j["C1"] and j["E"] and s["T"])
            hi.append(dict(eps=eps, C1_V=j["C1_V"], E_branch_max_J=j["E_branch_max_J"], T_vj=s["T_vj"], ok=ok))
            print("  %s (H) ε +%.2f %%: C1 %.2f V, 가지 에너지 %.0f J, %s %.1f °C → %s" % (part, 100 * eps, j["C1_V"], j["E_branch_max_J"],
                                                                                 sel["switch"], s["T_vj"], "통과" if ok else "불통과"), flush=True)
        eps_hi = 0.
        for h in hi:
            if h["ok"]:
                eps_hi = h["eps"]
            else:
                break
        # (L) 낮은 쪽 오동작 사건
        lo = []
        I_lim = E34.I_DER * sw[sel["switch"]]["I_pulse"]
        for eps in EPS_LO:
            for withM in ((True, False) if eps == -0.01 else (True,)):
                extra = dict(force_on_at=T_SPUR)
                if withM:
                    extra["t_on_max"] = T_ON_MAX
                jobs = []
                for cb, br in cbs.items():
                    for e in _spur_events(part):
                        kw = dict(e, tend=T_SPUR + (38e-3 if withM else 100e-3))
                        jobs.append((cb, br, cfg["on"] * (1 + eps), cfg["off"] * (1 + eps), kw, extra))
                recs = run_jobs(jobs)
                for cb, evs in recs.items():
                    for e in evs:
                        for kind, r in e.items():
                            t_on = r["t_on_cont_max_ms"]
                            th = E38.thermal([r], sw[sel["switch"]]) if t_on >= 0.2 else None
                            E_sw = None
                            s_ = sw[sel["switch"]]
                            E_sw = (s_["E_on"] * r["S_on"] + s_["E_off"] * r["S_off"]) / (s_["V_ref"] * s_["I_ref"]) + \
                                   (s_["R_on"] * r["S_i2"] if s_["kind"] == "mosfet" else s_["V_ce"] * r["S_i"])
                            m1 = bool(t_on <= (T_ON_MAX * 1e3 + 2e-3) and r["n_on_after_forced"] == 0 and not r["clamp_on_end"]) if withM else None
                            m2 = bool(r["E_branch_J"] <= E38.E_RES and r["i_max"] <= I_lim and max(r["vA_max"], r["vb_max"]) <= cfg["lim"])
                            m3 = None if th is None else bool(th["T"] <= sw[sel["switch"]]["T_max"])
                            lo.append(dict(eps=eps, M=withM, combo=cb, kind=kind, Vbat=r["Vbat"], P400=r["P400"], arch=r["arch"],
                                           t_on_ms=t_on, n_forced=r["n_forced_off"], n_on_after_forced=r["n_on_after_forced"],
                                           on_end=r["clamp_on_end"], E_branch_J=r["E_branch_J"], i_max=r["i_max"], vA_min=r["vA_min"],
                                           vA_max=r["vA_max"], E_switch_J=E_sw, T_vj=None if th is None else th["T"], M1=m1, M2=m2, M3=m3))
        okM = [x for x in lo if x["M"]]
        M1 = all(x["M1"] for x in okM); M2 = all(x["M2"] for x in okM)
        eps_lo = None
        for eps in sorted(EPS_LO):
            rr = [x for x in okM if x["eps"] == eps]
            if all(x["M3"] is not False for x in rr):
                eps_lo = eps; break
        # 래치 없는 낮은 쪽 오차(해석): ε = −1 %에서 최대 켜짐 시간까지 켜져 있던 사건의 V_A 최저(켜진 채 붙잡힌 값)의 최고
        hl = [x["vA_min"] for x in okM if x["eps"] == -0.01 and x["t_on_ms"] >= 0.2]
        hold = max(hl) if hl else None
        for x in lo:
            print("  %s (L) ε %+.1f %% M %s %-3s %-2s %4.0f V 부하 %2.0f kW: 켜짐 %.3f ms(강제 %d, 재켬 %d, 끝 %s), 가지 %.0f J·%.0f A, V_A %.2f–%.2f V, "
                  "스위치 %.2f J%s" % (part, 100 * x["eps"], "있음" if x["M"] else "없음", x["combo"], x["kind"], x["Vbat"], x["P400"] / 1e3,
                                       x["t_on_ms"], x["n_forced"], x["n_on_after_forced"], "켜짐" if x["on_end"] else "꺼짐", x["E_branch_J"],
                                       x["i_max"], x["vA_min"], x["vA_max"], x["E_switch_J"],
                                       "" if x["T_vj"] is None else ", %.1f °C" % x["T_vj"]))
        latchM0 = [x for x in lo if not x["M"]]
        t15 = None
        if latchM0:
            w = max(latchM0, key=lambda x: x["E_branch_J"])
            t15 = dict(E_branch_J_100ms=w["E_branch_J"], on_end=w["on_end"], combo=w["combo"])
        verdict("(M1) %s 오동작 사건: 최대 켜짐 시간으로 클램프가 꺼지고 다시 켜지지 않음" % part, M1)
        verdict("(M2) %s 오동작 사건: 가지 에너지·전류·V_A 한도" % part, M2)
        print("  %s 허용 오차: 높은 쪽 +%.2f %%(C1·T·E), 낮은 쪽 %s(M3), 켜진 채 붙잡힌 V_A 최고 %.2f V(ε 0) → 래치 없는 낮은 쪽 %.2f %%"
              % (part, 100 * eps_hi, "없음" if eps_lo is None else "%+.1f %%" % (100 * eps_lo), hold or float("nan"),
                 100 * ((hold / cfg["off"]) - 1) if hold else float("nan")))
        out[part] = dict(selected=sel, hi=hi, eps_hi=eps_hi, lo=lo, M1=M1, M2=M2, eps_lo=eps_lo, v_hold_max=hold,
                         eps_nolatch=None if not hold else hold / cfg["off"] - 1, M0_latch=t15)
    save_json(EID, "thr", out)


def _rated40(args):
    import E32_stage_a_25k as E32
    E32.CA = E38.CA_R
    return E34._rated_r(args)


def p1():
    import E28_stage_a_modules as E28
    jobs = [(V, s) for s in E28.SEEDS for V in E28.RATED_V]
    with Pool(workers()) as p:
        rows = p.map(_rated40, jobs)
    dev = E34.ds("C4MS008075U2")
    allph = [dict(ph, V=x["V"], seed=x["seed"]) for x in rows for ph in x["phases"]]
    for q in allph:
        q["P_pos_L"] = P1_K["cond"] * q["P_pos_cond"] + P1_K["diode"] * q["P_pos_diode"] + P1_K["coss"] * q["P_pos_coss"]
    hot = max(allph, key=lambda q: q["P_pos_L"]); hot0 = max(allph, key=lambda q: q["P_pos"])
    rth = dev["thermal"]["R_thJC_CperW"]
    P_dev = hot["P_pos_L"] / 2 * E34.SHARE; Tj = E34.T_C_SEMI + P_dev * rth * P1_K["rth"]
    Tj0 = E34.T_C_SEMI + hot0["P_pos"] / 2 * E34.SHARE * rth
    T_lim = dev["ratings"]["T_J_max_C"] - 25
    e34 = load_json("E34", "stagea")["P1"]
    for x in rows:
        print("  %4.0f V 공차 %-4s: 위치 손실 최대 %.2f W(규칙 L %.2f W)" % (x["V"], x["seed"], max(q["P_pos"] for q in x["phases"]),
                                                               max(q["P_pos_L"] for q in allph if q["V"] == x["V"] and q["seed"] == x["seed"])))
    ok = bool(Tj <= T_lim and e34["V_max"] <= e34["V_lim"] and e34["I_dev_pk"] <= e34["I_lim"])
    verdict("P1 Stage A 스위치(규칙 L, A25R)", ok, "가장 뜨거운 위치 %.2f W → 소자 %.2f W → T_J %.1f °C(한도 %d; 규칙 없이 %.1f °C), V·I는 E34(%.0f V·%.1f A)"
            % (hot["P_pos_L"], P_dev, Tj, T_lim, Tj0, e34["V_max"], e34["I_dev_pk"]))
    save_json(EID, "p1", dict(rows=rows, K=P1_K, hot=dict(V=hot["V"], seed=hot["seed"], k=hot["k"], P_pos_L=hot["P_pos_L"],
                                                          parts=[hot["P_pos_cond"], hot["P_pos_diode"], hot["P_pos_coss"]]),
                              P_dev=P_dev, Tj=Tj, Tj_no_rule=Tj0, T_lim=T_lim, E34=dict(V_max=e34["V_max"], I_dev_pk=e34["I_dev_pk"]), ok=ok))


def p6p7():
    d = E34.ds("EPC2305")["ratings"]
    p6 = load_json("E38", "p6")["rows"]; f2 = load_json("E38", "f2")["rows"]
    T6 = [E34.T_C_SEMI + F_TYP * r["soft"]["dT_one"] for r in p6]
    T6_0 = [E34.T_C_SEMI + r["soft"]["dT_one"] for r in p6]
    lim = load_json("E38", "p6")["limits"]
    ok6 = all(t <= d["T_J_max_C"] for t in T6) and all(r["soft"]["vs_max_soft"] <= lim["V"] and r["soft"]["ib_max"] <= lim["I"] for r in p6)
    f3 = [r for r in f2 if abs(r["ramp_ms"] - 3.) < 1e-9]
    T7 = [E34.T_C_SEMI + F_TYP * F_TYP * r["p7_dT"] for r in f3]
    T7_0 = [r["p7_Tj"] for r in f3]
    ok7 = all(t <= d["T_J_max_C"] for t in T7) and all(r["p7_i_dev_max"] <= E34.I_DER * d["I_DM_A"] for r in f3)
    verdict("P6 바이패스 소프트 투입(규칙 L)", ok6, "최악 %.1f °C(규칙 없이 %.1f °C), 74사례" % (max(T6), max(T6_0)))
    verdict("P7 H-브리지 역방향 도통(규칙 L)", ok7, "최악 %.1f °C(규칙 없이 %.1f °C), 4사례" % (max(T7), max(T7_0)))
    save_json(EID, "p6p7", dict(P6=dict(T=max(T6), T_no_rule=max(T6_0), ok=ok6, n=len(p6)),
                                P7=dict(T=max(T7), T_no_rule=max(T7_0), ok=ok7, n=len(f3), i_dev_max=max(r["p7_i_dev_max"] for r in f3))))


def p8():
    an = E34.ds("E40_Vishay_AN51114")["LTO150H"]
    LTO_ACC_J = an["E_accidental_100ms_J"]; LTO_REP_J = an["E_repetitive_J"]
    p6 = load_json("E38", "p6")["rows"]; f2 = load_json("E38", "f2")["rows"]
    E = [(r["brk_energy_J"], r.get("tag")) for r in p6] + [(r["brk_energy_J"], r["tag"] + "_F2") for r in f2 if abs(r["ramp_ms"] - 3.) < 1e-9]
    Emax, tag = max(E)
    ok = Emax <= LTO_REP_J
    acc_only = (not ok) and Emax <= LTO_ACC_J
    verdict("P8 제동 저항 LTO 150H(반복 펄스 52.8 J)", ok, "최대 %.2f J(%s), 반복 정격의 %.0f %%%s" % (Emax, tag, 100 * Emax / LTO_REP_J,
                                                                                     ", 조건부: 0.1 s보다 짧은 펄스 곡선 대조" if ok else (", 단발 사건에만 성립" if acc_only else "")))
    save_json(EID, "p8", dict(E_max_J=Emax, tag=tag, rep_J=LTO_REP_J, acc_J=LTO_ACC_J, ok=ok, conditional=ok, accidental_only=acc_only,
                              k=an["k"], source=E34.ds("E40_Vishay_AN51114")["title"]))


def ca():
    a = load_json("E37", "ca")
    irms = a["I_rms_worst"]
    full = E34.ds("E40_TDK_B3277x_full")
    F = full["row_fields"]
    combos = []
    for rw in full["rows"]:
        x = dict(zip(F, rw))
        if x["V_R_V"] < V_CA:
            continue
        n = int(math.ceil(E38.CA_R * 1e6 / x["C_uF"]))
        C = n * x["C_uF"]
        if C > 1.1 * E38.CA_R * 1e6:
            continue
        I = n * x["I_rms_70C_10kHz_A"]
        vol = n * x["w_mm"] * x["h_mm"] * x["l_mm"] / 1e3
        combos.append(dict(part=x["code"], V_R=x["V_R_V"], n=n, C_uF=C, I_rms=I, vol_cm3=vol, ok=bool(I >= irms), I_margin=I / irms))
    ok = [c for c in combos if c["ok"]]
    best = min(ok, key=lambda c: (c["n"], c["vol_cm3"])) if ok else None
    e37 = load_json("E37", "ca")["best"]
    verdict("(Q6′) C_A 2.4 mF 조합(TDK B3277x 전체 표, V_R ≥ %.0f V)" % V_CA, best is not None,
            "실효 %.1f A → %s(E37: %s × %d)" % (irms, "%s × %d = %.0f µF, %.0f A(%.0f배), %.0f cm³" % (best["part"], best["n"], best["C_uF"], best["I_rms"],
                                                                                         best["I_margin"], best["vol_cm3"]) if best else "없음",
                                               e37["part"], e37["n"]))
    save_json(EID, "ca", dict(I_rms=irms, combos=combos, best=best, E37_best=e37, V_req=V_CA))


def table():
    out = {}
    for name in ("reg", "p5", "thr", "p1", "p6p7", "p8", "ca"):
        try:
            out[name] = load_json(EID, name)
        except FileNotFoundError:
            out[name] = None
    rows = []
    if out["p5"]:
        for part in ("spec", "W460"):
            d = out["p5"][part]; sel = d["selected"]
            if sel:
                v = next(r for r in d["rows"] if r["n"] == sel["n"] and r["R_b"] == sel["R_b"])
                rows.append(dict(item="P5 " + part, selected=sel, T_vj=v["switches"][sel["switch"]]["T_vj"], C1_V=v["C1_V"],
                                 i_branch_max=v["i_branch_max"], E_branch_max_J=v["E_branch_max_J"], t_on_cont_max_ms=v["t_on_cont_max_ms"]))
            else:
                rows.append(dict(item="P5 " + part, selected=None))
    if out["thr"]:
        for part in ("spec", "W460"):
            t = out["thr"].get(part)
            if t:
                rows.append(dict(item="문턱 " + part, eps_hi=t["eps_hi"], eps_lo=t["eps_lo"], eps_nolatch=t["eps_nolatch"], M1=t["M1"], M2=t["M2"]))
    for k in ("p1", "p8", "ca"):
        if out[k]:
            rows.append(dict(item=k, **{x: out[k][x] for x in out[k] if x in ("Tj", "ok", "E_max_J", "best")}))
    if out["p6p7"]:
        rows.append(dict(item="p6p7", P6=out["p6p7"]["P6"], P7=out["p6p7"]["P7"]))
    save_json(EID, "table", dict(rows=rows))
    for r in rows:
        print("  %s" % r)


if __name__ == "__main__":
    for part in sys.argv[1:]:
        print("E40", part, "...", flush=True)
        globals()[part]()
