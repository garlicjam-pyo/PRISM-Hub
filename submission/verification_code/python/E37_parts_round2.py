"""[E37] 부품 정격 표 2차(A25R 기준): E34 불통과 4건의 대책, 이중 고장 C_A 방전, 새 부품(C_A 2.4 mF, L_r), 남은 요구값 정리.

■ 목적
  E34(docs/39)는 9개 부품 가운데 4개가 불통과였다: P2 C_fly 전류 밀도, P5 V_A 클램프 스위치, P6 바이패스 소프트 투입, P9 W460 접촉기.
  E36(docs/41)에서는 C_A 2.4 mF 때문에 이중 고장 Stage A 정지(E29 F2)가 0/4가 되었다. 이 시험은 각 불통과에 대해 다른 후보 부품이나
  설계 변경을 같은 판정 규칙(E34 3절)으로 다시 판정하고, A25R에서 새로 생긴 부품(C_A 2.4 mF, L_r 864.6 nH)의 요구를 정한다.

■ 왜 필요한가
  최종 보고서의 부품 정격 표가 "불통과 4건 + 대책 미정"이면 설계가 실제 부품으로 성립하는지 말할 수 없다. 불통과가 후보 품목의
  한계인지(다른 품목으로 해결) 설계의 한계인지(설계 변경 필요)를 나눠야 한다.

■ 공통 가정: E34와 같다(냉각 T_C 100 °C·T_H 65 °C, 단발 사건 T_J ≤ T_J,max, 정상 T_J ≤ T_J,max − 25 °C, 전압 0.8·전류 0.5 여유,
  선형 영역 분담 보장 없음). 모델은 A25R(E35 configure, R_A 9.0 mΩ, C_A 2.4 mF). 데이터시트 값은 표·본문의 숫자만 쓴다(그림을
  읽지 않는다). 숫자가 없어 판정할 수 없는 항목은 '조건부'로 적는다.

■ 부분과 판정 기준(실행 전에 고정)
  Q1 C_fly(P2 2차). 후보: 공진·고주파 대전류용 필름(전도 냉각형 포함), 반강유전체 세라믹(CeraLink), C0G MLCC. 같은 품목 n개 병렬.
     기준: (C) 동작 바이어스(V_bat/2 = 320–504 V)에서 n·C가 46.875 µF ± 5 % 안(필름·C0G는 공칭값, 바이어스 의존 품목은 데이터시트
     숫자로 320·504 V 값을 계산, 숫자가 없으면 조건부), (I) n·I_rms ≥ 60.9 A(E34 공차 최악 위상 실효전류; 정격은 25 kHz에 가장 가까운
     주파수의 표 값. 그 주파수가 25 kHz보다 높으면 조건부), (V) V_R(DC) ≥ 518.1 V(E34 v_C 최대). 판정 = 세 조건을 만족하는 품목이
     하나라도 있으면 통과. 통과 품목 가운데 위상당 부피가 가장 작은 것을 고른다(부피는 정보).
  Q2 V_A 클램프(P5 2차). 설계 변형 R_clamp ∈ {1.0, 1.2} Ω × 끔 문턱 ∈ {463, 458} V(켬 468 V, 지연 1 µs 그대로) × 스위치 후보
     {FF450R12ME4P, 1200 V SiC 모듈 후보}. E26 클램프 사건 32개(C_A 2.4 mF, R_A 9.0 mΩ)를 변형마다 다시 계산한다.
     기준: (C1) V_A·버스 ≤ 470 V, (P4) 사건 최대 에너지 ≤ 891SP 15 kJ·R이 범위 안, (P5) 클램프 전류 ≤ 0.5 × I_CRM(펄스 정격),
     V_A ≤ 0.8 × 정격 전압, 사건 평균 손실 × 정상 열저항(접합–방열판) + 65 °C ≤ T_vj,op,max(E34와 같은 보수 계산; SiC는 데이터시트의
     켬·끔 에너지와 R_DS(on)을 E34와 같은 비례 규칙으로). 선택 순서: 기존 IGBT → R 1.0 Ω → 끔 463 V(바꾸는 것이 적은 순).
     R 1.2 Ω은 468 V에서 390 A로 충전기 375 A보다 커야 한다는 조건(R < 1.248 Ω)을 만족한다.
  Q3 이중 고장 C_A 방전(E29 F2 + E34 P7 2차). Stage A 정지(FAILSAFE) 뒤 V_A 노드 방전 저항 R_dis ∈ {1, 3, 10} Ω을 켠다.
     제어: V_A > V_bus − 60 V이면 켬, V_A < V_bus − 65 V이면 끔(허브가 재는 두 전압. 정방향 경로전류를 멈추고, 역방향 다이오드
     도통(V_bus − V_A > 링크 + 2V_D)은 일으키지 않도록). R_dis 1 Ω은 V_A 클램프 스위치·저항을 쓰는 경우다.
     기준: E29 failsafe와 같다(경로·필터 ≤ 100 A, 직렬 ≤ 120 V, 링크 ≤ 120 V, 400 V 부하 연결 중 버스 ≤ 상한, 제동 ≤ 64 J,
     Stage A 정지 뒤 5 ms 안에 |i_p| ≤ 1 A로 유지) 4/4, 그리고 E34 P7(H-브리지 역방향 도통 T_J ≤ 150 °C, 소자 첨두 ≤ 164.5 A).
     방전 저항 에너지·첨두 전력은 정보(1 Ω이면 891SP 15 kJ와 대조). 선택: 4/4 통과하는 가장 큰 R_dis.
  Q4 바이패스 소프트 투입(P6 2차). 후보: 선형 영역용 MOSFET(데이터시트에 선형·DC SOA를 숫자로 준 150 V 이상 품목)을 소프트 투입
     전용 소자로. 입력은 E34 P6 최악 전력 이력(W460 930 V, 0.75 J, 첨두 1,119 W, 약 1.8 ms). 기준: 소자 1개가 모두 받을 때
     T_C 100 °C + 첨두 전력 × Z_th(펄스 폭)(데이터시트 숫자; 없으면 R_thJC로 보수) ≤ T_J,max, 직렬 최대 ≤ 0.8 × V_DSS,
     전류 ≤ 정격. 판정 = 하나라도 통과하면 통과. 정보: 투입 전 남는 부하(M0) 감발로 줄어드는 에너지는 E29 다시 실행 없이 비례로 적지
     않는다(설계 변경으로 남김).
  Q5 W460 접촉기(P9 2차). 후보: 정격 전압 ≥ 500 V DC인 EV용 접촉기. 기준: E34 P9와 같다(버스 상한 470 V ≤ 정격 전압, 개방 순간
     전류 최대 52.7 A ≤ 그 전압에서의 전기적 수명 정격 전류). W410(420 V, 70.7 A)도 같은 품목으로 판정한다.
  Q6 C_A 2.4 mF(새 부품). 입력: A25R 모델의 C_A 전류 실효값(정격 충전 375 A + 버스 15 kW, 640·800·920 V × 공칭·표본 1,
     마지막 1 ms). 후보 TDK B3277x(E34의 표). 기준: n·C가 2.4 mF −0/+10 % 안, n·I_rms(70 °C, 10 kHz) ≥ 최악 실효전류,
     V_R ≥ 470 V(B_470 상한). 통과 조합 가운데 개수가 가장 적은 것.
  Q7 L_r 864.6 nH(요구·설계 추정, 판정 없음). 공심(포화 없음) 원통 코일 1점 설계: 실효 60.9 A·첨두 169.3 A·25 kHz에서 Litz 권선
     저항과 손실을 계산해 모델 가정(R_L 1 mΩ)과 비교해 적는다.
  Q8 남은 요구값 정리(판정 없음): DAB 누설 인덕터·변압기·H-브리지 필터 인덕터 포화 전류, 조정형 Stage C 데드타임(docs/24–27 값).

■ 실행   python E37_parts_round2.py ca fs clamp cfly bypass ctc lr table
■ 결과   results/E37/*.json
"""
import glob
import json
import math
import sys
from multiprocessing import Pool

import numpy as np

from common import load_json, save_json, verdict, workers
import E34_parts_rating as E34

EID = "E37"
RA_A25 = 9.0e-3
CA_R = 2.4e-3
I_CFLY = 60.9                 # E34 공차 최악 위상 실효전류 [A]
V_CFLY = 518.1                # E34 v_C 최대 [V]
C_FLY = 46.875                # [µF]
V_CA = 470.                   # C_A 정격 전압 하한(B_470 상한)
CLAMP_R = (1.0, 1.2)
CLAMP_OFF = (463., 458.)
RDIS = (10., 3., 1.)


def ds(name):
    return E34.ds(name)


def cands(prefix):
    return {p.split("/")[-1][:-5]: json.loads(open(p, encoding="utf-8").read()) for p in sorted(glob.glob(str(E34.DS_DIR / (prefix + "*.json"))))}


# ======================================================================================================
# Q6 C_A 2.4 mF: 실효전류와 TDK B3277x 조합
# ======================================================================================================
def _ca(args):
    V, seed = args
    import E28_stage_a_modules as E28
    import E35_a25r_verify as E35
    E35.configure()
    name = "CA_%.0f" % V
    E28.CASES[name] = dict(V=V, prof=([0, 1], [-375., -375.]), bus=([0, 1], [15e3, 15e3]), chg=(0., 1.), tend=4.0e-3, n_end=4,
                           add_max=0, rem_max=0)
    r = E28.run_case(name, seed)
    t = r["t"]; vb = r["vb"].astype(float)
    i = E28.CA * np.gradient(vb, t)
    w = t >= t[-1] - 1.0e-3
    return dict(V=V, seed=seed, I_rms=float(np.sqrt(np.mean(i[w] ** 2))), I_pk=float(np.abs(i[w]).max()),
                vA=[float(vb[w].min()), float(vb[w].max())])


def ca():
    import E33_stage_a_25k_dynamics as E33
    jobs = [(V, s) for V in (640., 800., 920.) for s in E33.SEEDS]
    with Pool(workers()) as p:
        rows = p.map(_ca, jobs, chunksize=1)
    irms = max(r["I_rms"] for r in rows)
    tdk = ds("TDK_B3277x"); F = tdk["row_fields"]
    combos = []
    for rw in tdk["rows"]:
        x = dict(zip(F, rw))
        if x["V_R_V"] < V_CA:
            continue
        n = int(math.ceil(CA_R * 1e6 / x["C_uF"]))
        C = n * x["C_uF"]
        if C > 1.1 * CA_R * 1e6:
            continue
        I = n * x["I_rms_70C_10kHz_A"]
        vol = n * x["w_mm"] * x["h_mm"] * x["l_mm"] / 1e3
        combos.append(dict(part=x["code_prefix"], V_R=x["V_R_V"], n=n, C_uF=C, I_rms=I, vol_cm3=vol, ok=bool(I >= irms)))
    ok = [c for c in combos if c["ok"]]
    best = min(ok, key=lambda c: (c["n"], c["vol_cm3"])) if ok else None
    for r in rows:
        print("  C_A %4.0f V 공차 %-4s: 실효 %.1f A, 첨두 %.1f A, V_A %.2f–%.2f V" % (r["V"], r["seed"], r["I_rms"], r["I_pk"], *r["vA"]))
    verdict("(Q6) C_A 2.4 mF 조합(TDK B3277x)", best is not None,
            "최악 실효 %.1f A → %s" % (irms, "%s × %d = %.0f µF, %.0f A, %.0f cm³" % (best["part"], best["n"], best["C_uF"], best["I_rms"],
                                                                               best["vol_cm3"]) if best else "없음"))
    save_json(EID, "ca", dict(rows=rows, I_rms_worst=irms, combos=combos, best=best))


# ======================================================================================================
# Q3 이중 고장 C_A 방전(E29 F2 + E34 P7)
# ======================================================================================================
def _fs(args):
    R, case, V = args
    import E17_protection_integration as E17
    import E29_sals_degradation as E29
    det = load_json("E29", "failsafe")["dab_det_ms"]["%s_%.0f" % (case, V)]
    t2 = E17.T_EV + det * 1e-3 + E29.T_EV2
    astop = dict(E29.ASTOP, C_A=CA_R, R_dis=R)
    job = dict(case=case, V=V, P=E29.P0, event="dab", policy="brk_hold", event2=t2, duration=t2 + 10e-3, keep=True,
               sals=E29.sals_cfg(case, E29.MIXES["MX"], E29.SCEN["S5"]), fs_brake=True, astop=astop, **E29.P3T)
    m = E17.r2_run(dict(job))
    tr = m.pop("trace")
    ch, zms = E29.fs_judge(m, tr)
    hb = E34._prot(("hb", "%s_%.0f_F2" % (case, V), dict(job)))
    hb.pop("trace", None)
    return dict(R_dis=R, tag="%s_%.0f" % (case, V), checks=ch, pass_=bool(all(ch.values())), ip_zero_ms=zms, path_peak=m["path_peak"],
                series_peak=m["series_peak"], vlink_max=m["vlink_max"], brk_energy_J=m["brk_energy_J"], vA_end=m.get("vA_end"),
                dis_E_J=m.get("dis_E_J"), dis_P_pk_W=m.get("dis_P_pk_W"), dis_I_pk_A=m.get("dis_I_pk_A"), dis_n_on=m.get("dis_n_on"),
                p7_dT=hb["dT"], p7_i_dev_max=hb["i_dev_max"], p7_span_ms=hb["p_span_ms"])


def fs():
    import E29_sals_degradation as E29
    jobs = [(R, c, V) for R in RDIS for c, V in E29.FS_PACKS]
    with Pool(workers()) as p:
        rows = p.map(_fs, jobs, chunksize=1)
    d = ds("EPC2305"); tj = d["ratings"]["T_J_max_C"]; ilim = E34.I_DER * d["ratings"]["I_DM_A"]
    res = {}
    for R in RDIS:
        rr = [r for r in rows if r["R_dis"] == R]
        for r in rr:
            r["p7_ok"] = bool(E34.T_C_SEMI + r["p7_dT"] <= tj and r["p7_i_dev_max"] <= ilim)
            bad = [k for k, v in r["checks"].items() if not v]
            print("  R_dis %4.1f Ω %-15s %s 경로 %.1f A, 직렬 %.1f V, 링크 %.1f V, 제동 %.1f J, |i_p| ≤ 1 A까지 %s ms, 방전 %.0f J·첨두 %.0f A·켬 %s번,"
                  " P7 T_J %.1f °C %s"
                  % (R, r["tag"], "통과" if r["pass_"] else "불통과", r["path_peak"], r["series_peak"], r["vlink_max"], r["brk_energy_J"],
                     None if r["ip_zero_ms"] is None else round(r["ip_zero_ms"], 2), r["dis_E_J"] or 0., r["dis_I_pk_A"] or 0., r["dis_n_on"],
                     E34.T_C_SEMI + r["p7_dT"], bad))
        ok = all(r["pass_"] and r["p7_ok"] for r in rr)
        res[str(R)] = dict(ok=ok, n_pass=sum(r["pass_"] and r["p7_ok"] for r in rr))
        verdict("(Q3) 이중 고장 C_A 방전 R_dis %.1f Ω" % R, ok, "%d/4" % res[str(R)]["n_pass"])
    sel = next((R for R in RDIS if res[str(R)]["ok"]), None)
    print("  선택(4/4 통과하는 가장 큰 R_dis):", sel)
    save_json(EID, "fs", dict(rows=rows, summary=res, selected_R_dis=sel, C_A=CA_R))


# ======================================================================================================
# Q2 V_A 클램프 변형(E26 사건 32개) × 스위치 후보
# ======================================================================================================
def _clamp_ev(args):
    R, voff, kw = args
    import E26_charging_stop as E26
    E26.BUS["CA"] = CA_R; E26.RA_MOD = RA_A25
    E26.CL = dict(E26.CL, R=R, off=voff)
    r = E26.run_event(**kw, rec_every=1, full_trace=True)
    tr = np.array(r.pop("trace"))
    t, vA, vb, icl = tr[:, 0], tr[:, 1], tr[:, 2], tr[:, 5]
    on = icl > 0
    k_on = np.flatnonzero(~on[:-1] & on[1:]) + 1
    k_off = np.flatnonzero(on[:-1] & ~on[1:]) + 1
    dt = float(t[1] - t[0])
    span = float(t[k_off[-1] - 1] - t[k_on[0]]) if len(k_on) and len(k_off) else float(on.sum() * dt)
    return dict(R=R, voff=voff, **{k: kw[k] for k in ("Vbat", "P400", "PC", "arch", "prof", "t_comm")},
                vA_max=float(r["vA_max"]), vb_max=float(r["vb_max"]), E_clamp_J=float(r["E_clamp_J"]), t_clamp_on_ms=float(r["t_clamp_on_ms"]),
                n_on=int(len(k_on)), span_s=span, i_max=float(icl.max()),
                S_on=float(np.sum(vA[k_on] * icl[k_on])), S_off=float(np.sum(vA[k_off - 1] * icl[k_off - 1])),
                S_i2=float(np.sum(icl[on] ** 2) * dt))


def switch_models():
    """스위치 후보: 켬·끔 에너지(기준 전압·전류), 도통(IGBT: V_CE = a·I, MOSFET: R_DS(on)), 열(IGBT: T_H 65 °C + R_thJH, SiC: T_C 100 °C +
    R_thJC, 둘 다 있으면 큰 쪽), 펄스 전류·전압 정격."""
    g = ds("FF450R12ME4P")["igbt"]
    out = {"FF450R12ME4P": dict(kind="igbt", E_on=g["E_on_mJ"]["125"] * 1e-3, E_off=g["E_off_mJ"]["125"] * 1e-3, V_ref=600., I_ref=450.,
                                k_cond=2.0 / 450., I_pulse=g["I_CRM_A"], V_rated=g["V_CES_V"], T_max=g["T_vj_op_max_C"],
                                therm=[(E34.T_H_IGBT, g["R_thJH_KperW"])])}
    for name, d in cands("E37_sic_").items():
        m = d.get("mosfet") or {}
        try:
            Tk = max(m["E_on_mJ"], key=lambda k: float(k))
            cond = m.get("E_cond_num") or {}
            th = []
            if m.get("R_thJC_KperW"):
                th.append((E34.T_C_SEMI, m["R_thJC_KperW"]))
            if m.get("R_thJH_KperW"):
                th.append((E34.T_H_IGBT, m["R_thJH_KperW"]))
            elif m.get("R_thJC_KperW") and m.get("R_thCH_KperW"):
                th.append((E34.T_H_IGBT, m["R_thJC_KperW"] + m["R_thCH_KperW"]))
            Rk = max(m["R_DSon_mohm"], key=lambda k: float(k) if k.replace(".", "").isdigit() else -1)
            out[d["part"]] = dict(kind="mosfet", E_on=m["E_on_mJ"][Tk] * 1e-3, E_off=m["E_off_mJ"][Tk] * 1e-3, V_ref=cond.get("V"),
                                  I_ref=cond.get("I"), R_on=m["R_DSon_mohm"][Rk] * 1e-3, I_pulse=m.get("I_DM_A"), V_rated=m["V_DSS_V"],
                                  T_max=m["T_vj_op_max_C"], therm=th, src=name)
        except (KeyError, TypeError, ValueError) as e:
            out[d.get("part", name)] = dict(kind="mosfet", error="데이터 부족: %s" % e, src=name)
    return out


def judge_switch(rows, sw):
    if sw.get("error") or not sw.get("V_ref") or not sw.get("I_ref") or not sw.get("therm"):
        return dict(ok=None, note=sw.get("error", "켬·끔 에너지 조건 또는 열저항 숫자 없음 → 조건부"))
    worst = None
    for r in rows:
        if r["n_on"] == 0:
            continue
        E_on = sw["E_on"] * r["S_on"] / (sw["V_ref"] * sw["I_ref"]); E_off = sw["E_off"] * r["S_off"] / (sw["V_ref"] * sw["I_ref"])
        E_c = (sw["k_cond"] if sw["kind"] == "igbt" else sw["R_on"]) * r["S_i2"]
        P = (E_on + E_off + E_c) / r["span_s"] if r["span_s"] > 0 else 0.
        T = max(Tb + P * Rth for Tb, Rth in sw["therm"])
        if worst is None or T > worst["T"]:
            worst = dict(T=T, P=P, E_on=E_on, E_off=E_off, E_cond=E_c, ev=dict(arch=r["arch"], Vbat=r["Vbat"], P400=r["P400"], prof=r["prof"],
                                                                                 t_comm=r["t_comm"]))
    imax = max(r["i_max"] for r in rows); vmax = max(r["vA_max"] for r in rows)
    ok_i = sw["I_pulse"] is not None and imax <= E34.I_DER * sw["I_pulse"]
    ok_v = vmax <= E34.V_DER * sw["V_rated"]
    Tw = worst["T"] if worst else E34.T_C_SEMI
    return dict(ok=bool(ok_i and ok_v and Tw <= sw["T_max"]), i_max=imax, I_lim=None if sw["I_pulse"] is None else E34.I_DER * sw["I_pulse"],
                v_max=vmax, T_vj=Tw, T_lim=sw["T_max"], worst=worst)


def clamp():
    import E26_charging_stop as E26
    evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
    jobs = [(R, vo, e) for R in CLAMP_R for vo in CLAMP_OFF for e in evs]
    with Pool(workers()) as p:
        rows = p.map(_clamp_ev, jobs, chunksize=2)
    save_json(EID, "clamp_rows", dict(rows=rows, C_A=CA_R, R_A=RA_A25))
    clamp_judge()


def clamp_judge():
    """저장한 사건 기록(clamp_rows)으로 변형 × 스위치 후보를 판정한다(후보 데이터가 늦게 오면 이것만 다시 실행)."""
    rows = load_json(EID, "clamp_rows")["rows"]
    o = ds("Ohmite_800_1000"); cand = next(r for r in o["rows"] if r[0] == "891SP")
    sws = switch_models()
    out = {}
    for R in CLAMP_R:
        for vo in CLAMP_OFF:
            rr = [r for r in rows if r["R"] == R and r["voff"] == vo]
            c1 = max(max(r["vA_max"], r["vb_max"]) for r in rr) <= 470.
            Emax = max(r["E_clamp_J"] for r in rr)
            p4 = Emax <= cand[6] and cand[3] <= R <= cand[4]
            fk = [r["n_on"] / r["span_s"] / 1e3 for r in rr if r["span_s"] > 0]
            key = "R%.1f_off%.0f" % (R, vo)
            out[key] = dict(R=R, voff=vo, C1=bool(c1), vA_max=max(r["vA_max"] for r in rr), P4=bool(p4), E_max_J=Emax,
                            n_on_max=max(r["n_on"] for r in rr), f_avg_kHz=[min(fk), max(fk)] if fk else [0, 0],
                            t_on_max_ms=max(r["t_clamp_on_ms"] for r in rr), switches={})
            print("  [%s] V_A 최고 %.2f V, 에너지 최대 %.0f J, 켬 최대 %d번(평균 %.1f–%.1f kHz), 켜진 시간 최대 %.1f ms"
                  % (key, out[key]["vA_max"], Emax, out[key]["n_on_max"], *out[key]["f_avg_kHz"], out[key]["t_on_max_ms"]))
            for sn, sw in sws.items():
                j = judge_switch(rr, sw)
                out[key]["switches"][sn] = j
                if j["ok"] is None:
                    print("      %-22s 조건부: %s" % (sn, j["note"]))
                else:
                    print("      %-22s %s 전류 %.0f A(한도 %s), T_vj %.0f °C(한도 %s)" % (sn, "통과" if j["ok"] else "불통과", j["i_max"],
                          "?" if j["I_lim"] is None else "%.0f" % j["I_lim"], j["T_vj"], j["T_lim"]))
            out[key]["ok_any"] = [sn for sn, j in out[key]["switches"].items() if j["ok"] and c1 and p4]
    order = [("FF450R12ME4P", "R1.0_off463"), ("FF450R12ME4P", "R1.0_off458"), ("FF450R12ME4P", "R1.2_off463"),
             ("FF450R12ME4P", "R1.2_off458")] + [(sn, k) for sn in sws if sn != "FF450R12ME4P"
                                                   for k in ("R1.0_off463", "R1.0_off458", "R1.2_off463", "R1.2_off458")]
    sel = next(((sn, k) for sn, k in order if sn in out[k]["ok_any"]), None)
    verdict("(Q2) V_A 클램프 2차", sel is not None, "선택 %s" % (sel,))
    save_json(EID, "clamp", dict(rows=rows, variants=out, selected=sel, switches={k: {kk: vv for kk, vv in v.items() if kk != "therm"} | {
        "therm": v.get("therm")} for k, v in sws.items()}))


if __name__ == "__main__":
    for part in sys.argv[1:]:
        print("E37", part, "...", flush=True)
        globals()[part]()
