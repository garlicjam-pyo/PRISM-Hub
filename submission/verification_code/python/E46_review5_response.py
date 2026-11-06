"""[E46] 두 번째 통합 검토(2026-11-06 밤, 검토 커밋 36a7833) 대응: 충전기 직결 단자 정의, H1·H2·H4 분모, 충전 기동 경부하,
TB25·E31 분모, Stage C 최종 손실과 CV 경계, 보호 분기·부품 한도, 가치 지도 창 경로, 손실 교점, 버스 리플 정의, 검증기·재개 키.

■ 왜 필요한가(사용자 지시 2026-11-06 22:17: 검토서와 별첨을 바탕으로 다시 검토하고 수정)
  검토서는 결론을 바꾸는 조건(H2 추가 지연, 충전 시작 부하, 48 V 조정 범위, 고장 부품 정격)과 원고·코드·측정량의 불일치를
  지적했다. 계산이 필요한 항목을 저장소 코드로 다시 계산해 확인한다. 기존 E1–E45의 등록 판정과 원시 결과는 바꾸지 않는다.

■ 판정 기준(실행 전에 고정, 이 커밋. 결과를 본 뒤 바꾸지 않는다)
 (power) 정의 계산: 충전기 직결 단자는 V_A다. E16의 V_A = V_bat/2 + R_A(I_ch − i_path), R_A = 9.0 mΩ/4모듈 = 2.25 mΩ.
      보조부하 0에서 216s·3.7 V/셀의 375 A 단자 출력, 150 kW 전류와 위상 수(위상당 ≤ 46.875 A, 2위상 단위), P* = (V_bat/2)I
      기준과 비교, 180–240s 단자 출력, 400·500 V 충전기가 무보조 375 A로 도달하는 팩 전압, 500 V 충전기·4.2 V/셀의 최대 직렬수.
      이전 정의(E45 5.25 mΩ, E18 5.55 mΩ: V_A 앞 별도 3 mΩ 충전 경로)의 값도 함께 적는다. TB28 C28·A28·B28 사건 전 1.001–1.401 ms
      1 µs 평균 파형에서 충전기·보조 경로·Stage A 전류와 전력 분기를 적산한다(진단).
      판정 N1(재현): 216s 직결 375 A 출력 = 150.166 kW(±0.01 kW), 150 kW 전류 374.585 A(±0.01 A)·8위상, P* 기준 10위상.
 (h1) 저장 자료 재집계: 링크 처리전력 최대(E4 주행 정상, E5 640–920 V 정식 격자에서 Tier-2 추가 지연 정보 시험을 뺀 516건,
      E7 복합 공차 256건, E36 충전 정적·정식 과도 516건). 판정 H1-1: 모두 ≤ 8 kW.
 (h2d) 새 계산(후속 진단, H2 판정은 이미 부분 충족이며 바꾸지 않음): E12 스위칭 모델, 640 V, Tier-2 1→25 kW, 7변수 ±10 % 128개
      끝값 조합에 추가 지연 +3 µs(적분 간격 E12 기본 5 ns). 기준은 E12 judge_sw(순시 100 A 등) 그대로. 통과 수·초과 범위·
      링크전력 최대를 적는다. 재현 G0: 단일점 ++−−−−−가 101.21 A(±0.01 A)로 다시 나와야 한다(gate).
      (h2s) 저장 자료: E5 단일 공차 격자의 정식 640–920 V만의 분모(Tier-1, Tier-2 추가 지연 제외), 632 V 진단 분리.
 (h4) E8 시나리오 생성기(시드 20260928, 200개)를 다시 돌려 무손실·손실 시나리오의 압축기 요청 수와 손실 확률 범위를 센다.
      판정 H4-0(gate): 요청 합계가 저장 결과의 압축기 기동 488과 같다. 미공급률의 분모(지연 가능 히터 PTC·BH 요청 에너지)를 적는다.
 (ramp) 새 계산: E35 MD_640V_charge_slow(A25R, C_A 2.4 mF, 사전 기동·램프 600 µs, 375 A)에서 보조부하만 0·1·15·25 kW(공칭 표본),
      1 kW는 적분 단계 2배와 C_fly 45.0·42.75 µF(제어 타이밍 45.0 µF)도. 기준: 턴오프 위반 0, 위상 첨두 ≤ E32 공칭 P_rated
      74.53 A(E35 T2). 재현 R0(gate): 15 kW 첨두 = 저장 68.71858 A(상대 1e-6). 15·25 kW 외의 결과는 기동 조건의 적용 범위로 보고한다.
 (tb25) 저장 판정 재집계: TB25 세 설계 × T1(무부하)·T2(부하·용량 있음)·T3(부하·용량 없음)의 통과 수.
 (e31) 저장 자료 재집계: E31 격자 90안의 주파수별 S2, 100·150 kHz 후보의 기준별(전압·전류 정격, 충전 손실 C, 보조 손실 A) 통과 수.
 (c22) 새 계산: (a) E22 최종 설계(L_m 33 µH, apply_zvs)와 초기 후보의 손실·효율(입력 270–504 V × 1.5·5 kW, 48 V).
      (b) 270·268.772 V, 52 V, −650 W, 출력용량 1.0·1.2배: 단측 송신 정상점의 V_I·필요 듀티와 한도 0.97, 같은 점의 양측 구동.
      (c) 268.772·270·504 V, 48 V 설정의 평균모델 램프(4 kW/ms)·계단 5개 전이(E22 run_avg). 결과를 그대로 적는다(판정 없음).
 (tb15) 저장 결과: TB15 H 사례의 회로 최저·최고·끝 전압과 E22의 차.
 (prot) 저장 자료 재집계: E38 p6 74건의 경로(직접 분리·감발 후 복원·감발 후 분리), P6 바이패스 전류의 단독 선형 한도
      0.5 × 329 A = 164.5 A 재판정(판정 P6-I: 74건 모두 이하), DAB 2차 첨두의 1차 환산(W410 n 4.1, W460 n 4.6)과 모의 한도,
      Stage C 정지 에너지(E38 사각 상계 5.3 kW × 12.4101 ms와 같은 4 kW/ms 램프 적분), E43 48 V 배터리 9점.
 (vmap2) (a) E45 판정 함수의 min_rel 기록 정정 뒤 14칸 분류·후보가 E45 vmap과 같아야 한다(gate). 23개 최소값 기록 확인.
      (b) 창 진입·이탈 ±5 V(상승: V/2 ≥ V_W + 5 V일 때만 조정, 하강: V/2 ≥ V_W − 5 V이면 조정)로 E18 path_window를 다시 계산해
      14칸을 재분류(판정 없음, 바뀐 칸을 그대로 보고). (c) E18 정적 포트 성립성에서 누설 L을 (V_W/400)²로 바꾸기 전후 활성
      운전점의 성립 변화 수(변화가 있으면 가치 지도 성립 판정을 다시 해야 한다).
 (loss) 저장 자료 계산: ④−⑤ 부하별 차, 0.5 kW 운전시간을 23 kW로 옮길 때 순위가 바뀌는 비율, 총손실 교점(보조 손실 차 /
      충전 에너지당 손실 차; 모터 기준점·상저항 ≥ 5 mΩ 격자 최소; 640·800·920 V, 375 A 고정).
 (nc) [추가 등록, 실행 전] E15 dab_loss·hbridge_loss의 stageB_nc 배율 대상(비도통 손실 항 전체)을 배율 1과 0의 차로 계산:
      8 kW DAB의 링크 0·1·3 kW, H-브리지 직렬전압 20 V에서 경로전류 0·25·60 A. 저장 E44 breakeven 배율(0.31977)도 적는다(판정 없음).
 (vmap2 c 정정) [실행 경과, 1차 실행 뒤] 1차 실행은 창 정격을 W410 5 kW·W460 4 kW로 고정하고 사양 팩을 빠뜨렸다(141점). E18
      window_rating_W의 팩별 정격과 사양 팩(640–920 V 25점)을 넣어 다시 센다(판정 기준은 같음: 변화 수를 보고).
 (ripple) 새 계산: E43 S1 최대 리플 사례를 같은 작업 번호·시드로 다시 계산해 주기평균 열의 마지막 1 ms 폭(원 정의), 같은 구간
      순시 최대−최소, 단일 PWM 주기 최대 폭을 적는다. 재현(gate): 원 정의 값이 저장값과 상대 1e-6.
 (gate) 검증기 오류 주입(E45 fcheck_judge, 복사본에만 적용): 정상 → 통과, 같은 행을 두 파일에서 삭제 → 실패, F-b 제어 주파수만
      20 kHz → 실패, 한 행 첨두 +10 A → 실패. 넷 다 기대대로여야 한다(gate). 실패 판정이 종료 코드 1을 내는지 자식 프로세스로 확인.
 (cache) 클램프 재개 키: 선택 소자의 열저항만 +5 %로 바꾸면 E44 _clamp_config_hash가 달라져야 한다(gate).

■ 실행   python E46_review5_response.py power h1 h2d h2s h4 ramp tb25 e31 c22 tb15 prot vmap2 loss ripple gate cache
■ 결과   results/E46/*.json. 필수 판정(gate)이 실패하면 종료 코드 1.
"""
import itertools
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

import common
from common import save_json, load_json, verdict, workers, Pool, strict_diff, input_record

EID = "E46"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VAL = ROOT / "validation"


def _vj(*parts):
    return json.loads((VAL.joinpath(*parts)).read_text(encoding="utf-8"))


# ======================================================================================================
# (power)
# ======================================================================================================
RA_MOD = 9.0e-3
NMOD = 4
RA = RA_MOD / NMOD
I_PH = 46.875


def _phases(I):
    n = math.ceil(I / I_PH - 1e-9)
    return n + (n % 2)


def _i_for(P, half, R):
    return (-half + math.sqrt(half * half + 4 * R * P)) / (2 * R) if R > 0 else P / half


def power():
    rows = {}
    for s in (180, 192, 200, 216, 224, 240):
        Vb = 3.7 * s; h = Vb / 2
        I_dir = _i_for(150e3, h, RA)
        rows["%ds" % s] = dict(Vbat=Vb, half=h, P_direct_375A_kW=(h + RA * 375) * 375 / 1e3, P_star_375A_kW=h * 375 / 1e3,
                               I_direct_150kW=I_dir, phases_direct=_phases(I_dir), I_star_150kW=150e3 / h, phases_star=_phases(150e3 / h),
                               P_525_375A_kW=(h + 5.25e-3 * 375) * 375 / 1e3, I_525_150kW=_i_for(150e3, h, 5.25e-3),
                               P_555_375A_kW=(h + 5.55e-3 * 375) * 375 / 1e3)
    reach = {str(v): 2 * (v - RA * 375) for v in (400., 500.)}
    cell_240 = reach["500.0"] / 240
    smax = int(math.floor(reach["500.0"] / 4.2))
    r216 = rows["216s"]
    n1 = (abs(r216["P_direct_375A_kW"] - 150.166) <= 0.01 and abs(r216["I_direct_150kW"] - 374.585) <= 0.01
          and r216["phases_direct"] == 8 and r216["phases_star"] == 10)
    # TB28 사건 전 분기
    tb = {}
    d = ROOT / "simulink" / "tb" / "TB28_A25R_Charging_Stop" / "results"
    for cn in ("A28_920V_pathloss", "B28_640V_pathloss_ramp", "C28_800V_module_fault"):
        A = np.loadtxt(d / ("TB28_%s_avg1us.csv" % cn), delimiter=",")
        t = A[:, 0]; m = (t > 1.0e-3) & (t <= 1.401e-3 + 1e-12)
        vA, vbus, iAo, icl, ich, ipath = (A[m, k] for k in (1, 2, 3, 4, 5, 6))
        tb[cn] = dict(n=int(m.sum()), V_A=float(vA.mean()), V_bus=float(vbus.mean()), I_charger=float(ich.mean()), I_path=float(ipath.mean()),
                      I_stageA_out=float(iAo.mean()), I_clamp=float(icl.mean()),
                      P_VA_from_charger_kW=float(np.mean(vA * ich)) / 1e3, P_to_path_kW=float(np.mean(vA * ipath)) / 1e3,
                      P_to_stageA_kW=float(np.mean(vA * -iAo)) / 1e3, input=input_record(d / ("TB28_%s_avg1us.csv" % cn), "archived(Simulink)"))
    out = dict(R_A_ohm=RA, packs=rows, charger_reach_pack_V=reach, cell_V_240s_500V=cell_240, max_series_500V_4p2=smax,
               direct_range_kW=[min(r["P_direct_375A_kW"] for r in rows.values()), max(r["P_direct_375A_kW"] for r in rows.values())],
               tb28_before_event=tb, N1=n1)
    save_json(EID, "power", out)
    print("  216s 직결 375 A %.3f kW, 150 kW %.3f A(%d위상) / P* %.3f kW·%.3f A(%d위상) / 이전 5.25 mΩ %.3f kW·%.3f A"
          % (r216["P_direct_375A_kW"], r216["I_direct_150kW"], r216["phases_direct"], r216["P_star_375A_kW"], r216["I_star_150kW"],
             r216["phases_star"], r216["P_525_375A_kW"], r216["I_525_150kW"]))
    print("  180–240s 직결 단자 %.2f–%.2f kW, 400·500 V 충전기 도달 %.2f·%.2f V, 240s 500 V 상한 %.4f V/셀, 최대 직렬 %ds"
          % (out["direct_range_kW"][0], out["direct_range_kW"][1], reach["400.0"], reach["500.0"], cell_240, smax))
    for k, v in tb.items():
        print("  %s: V_A %.2f V, 충전기 %.1f A, 보조 경로 %.2f A, Stage A %.2f A → V_A 받음 %.2f kW, 보조 %.2f kW, Stage A %.2f kW"
              % (k, v["V_A"], v["I_charger"], v["I_path"], -v["I_stageA_out"], v["P_VA_from_charger_kW"], v["P_to_path_kW"], v["P_to_stageA_kW"]))
    verdict("(power N1) 216s 직결 단자 150.166 kW·374.585 A·8위상, P* 10위상", n1, gate=True)


# ======================================================================================================
# (h1)
# ======================================================================================================
def h1():
    g = _vj("2026-09-29-controller", "grid.json")["rows"]
    formal = [r for r in g if r["vbat"] >= 640 and not (r["tier"] == 2 and r["set"] == "delay+3.0us")]
    w5 = max(formal, key=lambda r: r["dab_power_peak"])
    c7 = _vj("2026-09-29-controller", "corners.json")
    rows7 = c7["rows"] if isinstance(c7, dict) and "rows" in c7 else c7
    k7 = "dab_power_peak" if "dab_power_peak" in rows7[0] else "link_power_peak"
    w7 = max(rows7, key=lambda r: r[k7])
    co = _vj("2026-10-28-a25r-impact", "E36", "e16_concurrent.json")["rows"]
    cof = [r for r in co if r["V"] >= 640 and not (r["tier"] == 2 and r["name"] == "delay+3.0us")]
    wco = max(cof, key=lambda r: r["dab_power_peak"])
    sc = _vj("2026-11-06-review3", "E44", "scope.json")
    out = dict(E5_formal_n=len(formal), E5_transient_max_W=w5["dab_power_peak"], E5_worst=dict(V=w5["vbat"], set=w5["set"], p0=w5["p0"], p1=w5["p1"]),
               E7_n=len(rows7), E7_max_W=w7[k7], E36_formal_n=len(cof), E36_transient_max_W=wco["dab_power_peak"], E44_scope_H1=sc.get("H1"))
    ok = max(out["E5_transient_max_W"], out["E7_max_W"], out["E36_transient_max_W"]) <= 8000
    save_json(EID, "h1", out)
    print("  E5 정식 %d건 과도 최대 %.2f W(%s), E7 %d건 %.2f W, E36 충전 정식 %d건 %.2f W"
          % (len(formal), out["E5_transient_max_W"], out["E5_worst"], len(rows7), out["E7_max_W"], len(cof), out["E36_transient_max_W"]))
    verdict("(h1 H1-1) 링크 처리전력 ≤ 8 kW", ok)


# ======================================================================================================
# (h2d, h2s)
# ======================================================================================================
def _h2d_job(s):
    import E12_switching_verification as E12
    import stage_b_tests as st
    p = replace(E12.NOMINAL, **{f: getattr(E12.NOMINAL, f) * (1 + .1 * k) for f, k in zip(st.FIELDS, s)})
    p = replace(p, delay=E12.NOMINAL.delay + 3e-6)
    r = E12.run_case((2, 640, 1000, 25000, p, 0, None, dict(signs=list(s))))
    return {k: (v if not isinstance(v, np.generic) else v.item()) for k, v in r.items()}


def h2d():
    import E12_switching_verification as E12
    t0 = time.time()
    g0 = _h2d_job((1, 1, -1, -1, -1, -1, -1))
    ok0 = abs(max(g0["path_inst"], g0["bridge_inst"]) - 101.21) <= 0.01
    verdict("(h2d G0) 단일점 ++−−−−− 재현 %.4f A" % max(g0["path_inst"], g0["bridge_inst"]), ok0, gate=True)
    signs = list(itertools.product([-1, 1], repeat=7))
    with Pool(workers()) as p:
        rows = p.map(_h2d_job, signs, chunksize=2)
    fails = [r for r in rows if not r["pass_"]]
    inst = [max(r["path_inst"], r["bridge_inst"]) for r in rows]
    finst = [max(r["path_inst"], r["bridge_inst"]) for r in fails]
    out = dict(n=len(rows), passed=sum(r["pass_"] for r in rows), fail_inst_range=[min(finst, default=None), max(finst, default=None)],
               inst_max=max(inst), link_power_max_W=max(r["link_power_avg"] for r in rows),
               fail_reasons=sorted(set(json.dumps(r.get("ports_violated", [])) for r in fails)),
               over_100A=sum(i > 100 for i in inst), worst_signs=max(rows, key=lambda r: max(r["path_inst"], r["bridge_inst"]))["signs"],
               dt_ns=None, sec=time.time() - t0, rows=rows)
    save_json(EID, "h2d", out)
    print("  Tier-2 +3 µs 복합 128: 통과 %d/128, 실패 순시 %s A, 순시 최대 %.4f A, 링크 최대 %.1f W"
          % (out["passed"], out["fail_inst_range"], out["inst_max"], out["link_power_max_W"]))


def h2s():
    g = _vj("2026-09-29-controller", "grid.json")["rows"]
    out = {}
    for name, f in (("all_632_920", lambda r: True), ("formal_640_920", lambda r: r["vbat"] >= 640)):
        t1 = [r for r in g if f(r) and r["tier"] == 1]
        t2 = [r for r in g if f(r) and r["tier"] == 2 and r["set"] != "delay+3.0us"]
        t2d = [r for r in g if f(r) and r["tier"] == 2 and r["set"] == "delay+3.0us"]
        out[name] = dict(T1=[sum(r["pass_"] for r in t1), len(t1)], T2=[sum(r["pass_"] for r in t2), len(t2)],
                         T2_delay_info=[sum(r["pass_"] for r in t2d), len(t2d)])
    save_json(EID, "h2s", out)
    print("  단일 공차 격자:", json.dumps(out, ensure_ascii=False))


# ======================================================================================================
# (h4)
# ======================================================================================================
def h4():
    import E8_load_admission as E8
    rng = np.random.default_rng(20260928)
    n0 = n1 = 0; pl = []
    for i in range(200):
        p_loss = 0. if i % 2 == 0 else float(rng.uniform(0, .2))
        scn = E8.scenario(rng, p_loss)
        if i % 2 == 0:
            n0 += len(scn["comp"])
        else:
            n1 += len(scn["comp"]); pl.append(p_loss)
    ss = _vj("2026-09-28-requirements", "sals_contract.json")["summary"]
    ok = (n0 + n1) == ss["sals"]["compressor_starts"]
    out = dict(compressor_requests_noloss=n0, compressor_requests_loss=n1, p_loss_range_pct=[100 * min(pl), 100 * max(pl)],
               stored_starts=ss["sals"]["compressor_starts"], never_started=ss["sals"]["compressor_requests_never_started"],
               unmet_sals_pct=100 * ss["sals"]["d_unmet_fraction"]["total"], unmet_static_pct=100 * ss["static"]["d_unmet_fraction"]["total"],
               unmet_basis="지연 가능 히터 2종(PTC·BH)의 요청 에너지 대비", budget_exceed_ms=ss["sals"]["budget_exceed_ms_total"],
               peak_kW=ss["sals"]["peak_kW"])
    save_json(EID, "h4", out)
    print("  압축기 요청: 무손실 %d, 손실 %d(손실 확률 %.4f–%.4f %%), 미공급 %.4f %% 대 정적 %.4f %%"
          % (n0, n1, out["p_loss_range_pct"][0], out["p_loss_range_pct"][1], out["unmet_sals_pct"], out["unmet_static_pct"]))
    verdict("(h4 H4-0) 요청 합계 = 저장 압축기 기동 %d" % ss["sals"]["compressor_starts"], ok, gate=True)


# ======================================================================================================
# (ramp)
# ======================================================================================================
def _ramp_job(args):
    load_kW, mult, cfly = args
    import E35_a25r_verify as E35
    import E28_stage_a_modules as E28
    import E24_stage_a_shedding as E24
    A = E28.A
    base_cfly = A.DESIGNS["A25"]["Cfly"]
    try:
        if cfly is not None:
            A.DESIGNS["A25"]["Cfly"] = 45.0e-6
            A.PLANT.clear(); A.PLANT["Cfly"] = cfly
        E35.configure()
        nstep0 = A.BASE["Nstep"]
        A.BASE["Nstep"] = nstep0 * mult
        name = "MD_640V_charge_slow"
        case = dict(E28.CASES[name]); case["bus"] = ([0, 1], [load_kW * 1e3, load_kW * 1e3]); E28.CASES[name] = case
        r = E28.run_case(name, None)
        t = r["t"]
        turn = E24.turnoffs(r, E28.T_JUDGE)
        bad = [x for x in turn if abs(x[2]) > max(.05 * x[3], E28.I_ABS)]
        pk = float(np.max(np.abs(r["i"][t > E28.T_JUDGE])))
        series = np.max(np.abs(r["i"]), axis=1)
        tpk = float(t[np.argmax(np.where(t > E28.T_JUDGE, series, -np.inf))] * 1e3)
        Pr = float(E28.p_rated(None))
        res = dict(load_kW=load_kW, step_mult=mult, cfly_uF=None if cfly is None else cfly * 1e6, dt_ns=float(r["dt"] * 1e9),
                   phase_peak=pk, peak_ms=tpk, n_turnoff=len(turn), n_bad=len(bad), P_rated=Pr, T1=not bad, T2=pk <= Pr)
        A.BASE["Nstep"] = nstep0
        return res
    finally:
        A.PLANT.clear(); A.DESIGNS["A25"]["Cfly"] = base_cfly


def ramp():
    jobs = [(0., 1, None), (1., 1, None), (15., 1, None), (25., 1, None), (1., 2, None), (1., 1, 45.0e-6), (1., 1, 42.75e-6)]
    with Pool(workers()) as p:
        rows = p.map(_ramp_job, jobs, chunksize=1)
    try:
        tr = _vj("2026-10-28-stage-a-25k", "E35", "transient.json")["cases"]
        ref = next(x for x in tr if x["case"] == "MD_640V_charge_slow" and x["seed"] is None)
    except Exception as e:
        ref = dict(phase_peak=None, err=str(e))
    r15 = next(r for r in rows if r["load_kW"] == 15. and r["step_mult"] == 1 and r["cfly_uF"] is None)
    ok0 = ref.get("phase_peak") is not None and abs(r15["phase_peak"] - ref["phase_peak"]) <= 1e-6 * max(1., ref["phase_peak"])
    save_json(EID, "ramp", dict(rows=rows, stored_15kW=ref.get("phase_peak"), R0=ok0))
    for r in rows:
        print("  보조 %4.1f kW 단계×%d C_fly %s: 첨두 %.5f A(%.3f ms), 턴오프 %d·위반 %d, 기준 %.5f A → %s"
              % (r["load_kW"], r["step_mult"], r["cfly_uF"], r["phase_peak"], r["peak_ms"], r["n_turnoff"], r["n_bad"], r["P_rated"],
                 "통과" if (r["T1"] and r["T2"]) else "초과"))
    verdict("(ramp R0) 15 kW 공칭 첨두가 저장 E35 값과 같음", ok0, "%.6f / %s" % (r15["phase_peak"], ref.get("phase_peak")), gate=True)


# ======================================================================================================
# (tb25, e31, tb15)
# ======================================================================================================
def tb25():
    j = json.loads((ROOT / "simulink" / "tb" / "TB25_StageA_Coss" / "results" / "TB25_summary.json").read_text(encoding="utf-8"))["judge"]
    cnt = {t: [sum(j[d][t]["pass"] for d in "OAB"), 3] for t in ("T1", "T2", "T3")}
    out = dict(by_test=cnt, no_load=cnt["T1"], load=[cnt["T2"][0] + cnt["T3"][0], 6], total=[sum(v[0] for v in cnt.values()), 9],
               errors_pct={d: {t: 100 * j[d][t]["err"] for t in ("T1", "T2", "T3")} for d in "OAB"})
    save_json(EID, "tb25", out)
    print("  TB25:", json.dumps(out["by_test"]), "무부하", out["no_load"], "부하", out["load"], "전체", out["total"])


def e31():
    g = json.loads((HERE.parent / "results" / "E31" / "coss.json").read_text(encoding="utf-8"))["grid"] \
        if (HERE.parent / "results" / "E31" / "coss.json").exists() else _vj("2026-10-28-stage-a-coss", "E31", "coss.json")["grid"]
    by_f = {}
    for f in sorted(set(r["fr"] for r in g), reverse=True):
        rr = [r for r in g if r["fr"] == f]
        vi = [r for r in rr if r["V_ok"] and r["I_ok"]]
        by_f["%.0f" % f] = dict(n=len(rr), S2=sum(r["S2"] for r in rr), VI=len(vi), VI_C=sum(r["C"] for r in vi), VI_A=sum(r["A"] for r in vi))
    save_json(EID, "e31", dict(n=len(g), by_f=by_f))
    for f, v in by_f.items():
        print("  %6s Hz: %s" % (f, v))


def tb15():
    s = json.loads((ROOT / "simulink" / "tb" / "TB15_StageC_LightLoad" / "results" / "TB15_H_400V_cross_summary.json").read_text(encoding="utf-8"))
    out = dict(vo_min=s["vo_min"], vo_max=s["vo_max"], ref=s["ref"], d_min=s["vo_min"] - s["ref"]["vo_min"], d_max=s["vo_max"] - s["ref"]["vo_max"],
               vo_end_diff=s["vo_end_diff"], verdict=s["verdict"])
    save_json(EID, "tb15", out)
    print("  TB15 H: 최저 %.5f(E22 %.5f, 차 %.5f), 최고 차 %.5f, 끝 차 %.5f V" % (out["vo_min"], out["ref"]["vo_min"], out["d_min"], out["d_max"], out["vo_end_diff"]))


# ======================================================================================================
# (c22)
# ======================================================================================================
def c22():
    import E22_stage_c_regulated as C
    c = C.selected(); orig = C.selected(apply_zvs=False)

    def loss(calc, v, p):
        pd, _ = C.dcx_loss(calc, p, 48., calc["np"], calc["ns"])
        front_abs = abs(p) + (1 if p > 0 else -1) * pd["total"]
        pf, _ = C.front_loss(calc, {"L": calc["L"]}, v, calc["n"] * 48., front_abs, calc["nsw"])
        L = pd["total"] + pf["total"]
        return dict(loss_W=L, eff=p / (p + L))
    losses = [dict(V=v, P=p, initial=loss(orig, v, p), final=loss(c, v, p)) for v in C.VBUS_GRID for p in (1500., 5000.)]
    Rl = C.K["mag_ind_cu"] * C.PO_MAX / (C.PO_MAX * 1.03 / (c["n"] * C.VO_NOM)) ** 2
    cv = []
    for vb in (270., 268.772):
        for cs in (1.0, 1.2):
            VI, r, ok = C.legs_solve(c, c["Lm"], c["td_s"], -650., 52., cscale=cs)
            duty = (VI + Rl * r[0] / VI) / vb
            row = dict(Vbus=vb, Vo=52., P=-650., cscale=cs, single=dict(VI=VI, P_out=float(r[1]), reached=bool(ok), duty=duty,
                                                                          duty_ok=bool(duty <= C.DMAX)))
            VIb, rb, okb = C.legs_solve_both(c, c.get("td_sb", c["td_s"]), -650., 52., cscale=cs)
            row["both"] = dict(VI=VIb, P_out=float(rb[1]), reached=bool(okb), duty=(VIb + Rl * rb[0] / VIb) / vb)
            cv.append(row)
    eq = load_json("E22", "control")["equiv"]; gg = load_json("E22", "control")["gains"]
    tr = []
    for v in (268.772, 270., 504.):
        for p0, p1 in ((100, 5000), (-3000, 5000), (5000, -3000), (5000, 100), (-3000, -300)):
            for slope in (4e6, 1e12):
                tt = abs((p1 - p0) / slope)
                z = C.run_avg(c, eq, gg, [0, .002, .002 + tt, 1], [p0, p0, p1, p1], [0, 1], [v, v], T_end=.006 + tt)
                m = C.metrics(z, .0015)
                tr.append(dict(vbus=v, p0=p0, p1=p1, ramp=slope < 1e9, vo_min=m["vo_min"], vo_max=m["vo_max"], dev_pct=m["dev_pct"],
                               ix_avg100_max=m["ix_avg100_max"], sat_ms=m["sat_ms"]))
    out = dict(losses=losses, cv=cv, dmax=C.DMAX, transitions=tr, Lm_final=c["Lm"], Lm_initial=orig["Lm"])
    save_json(EID, "c22", out)
    for x in losses:
        if x["P"] == 5000.:
            print("  %5.0f V 5 kW: 초기 %.3f W(%.4f %%), 최종 %.3f W(%.4f %%)" % (x["V"], x["initial"]["loss_W"], 100 * x["initial"]["eff"],
                                                                         x["final"]["loss_W"], 100 * x["final"]["eff"]))
    for r in cv:
        print("  CV %.3f V·52 V·−650 W·C×%.1f: 단측 V_I %.3f, P %.1f, 듀티 %.5f(한도 %.2f) / 양측 V_I %.3f, P %.1f, 듀티 %.5f"
              % (r["Vbus"], r["cscale"], r["single"]["VI"], r["single"]["P_out"], r["single"]["duty"], C.DMAX, r["both"]["VI"], r["both"]["P_out"], r["both"]["duty"]))
    for v in (268.772, 270., 504.):
        for rp in (True, False):
            a = [x for x in tr if x["vbus"] == v and x["ramp"] == rp]
            print("  %.3f V %s: 48 V %.3f–%.3f V, 편차 최대 %.3f %%, 100 µs 평균 최대 %.2f A, 포화 %.3f ms"
                  % (v, "램프" if rp else "계단", min(x["vo_min"] for x in a), max(x["vo_max"] for x in a), max(x["dev_pct"] for x in a),
                     max(x["ix_avg100_max"] for x in a), max(x["sat_ms"] for x in a)))


# ======================================================================================================
# (prot)
# ======================================================================================================
def prot():
    d = _vj("2026-10-29-review-response", "E38", "p6.json")
    rows = d["rows"]
    br = {}
    for r in rows:
        key = "직접 분리" if r["kind"] == "sep" else ("감발 후 복원" if r["restored"] else "감발 후 분리")
        br.setdefault(key, []).append(r["tag"])
    lim1 = 0.5 * 329.0
    ib = {str(V): max(r["soft"]["ib_max"] for r in rows if r["V"] == V) for V in sorted(set(r["V"] for r in rows))}
    ok6 = all(r["soft"]["ib_max"] <= lim1 for r in rows)
    turns = {832.: 4.1, 920.: 4.1, 930.: 4.6, 1008.: 4.6}
    dab = {}
    for V in sorted(turns):
        rr = [r for r in rows if r["V"] == V]
        w = max(rr, key=lambda r: r["dab_sec_peak"])
        dab[str(V)] = dict(window="W410" if turns[V] == 4.1 else "W460", sec_peak_A=w["dab_sec_peak"], prim_peak_A=w["dab_sec_peak"] / turns[V], tag=w["tag"])
    acc = {"W410": 90.0, "W460": 68.7}
    dab_lim = {k: dict(sec_limit_A=v, prim_equiv_A=v / (4.1 if k == "W410" else 4.6)) for k, v in acc.items()}
    pr = [r for r in rows if r.get("pause_ms")]
    wp = max(pr, key=lambda r: r["pause_ms"])
    P_sc = 5300.; slope = 4.0e6
    t_ramp = P_sc / slope
    span = wp["pause_ms"] * 1e-3
    hold = span - t_ramp                       # 정지 지령 → 재개 지령
    E_rect = P_sc * span
    E_int = P_sc * hold                        # 대칭 4 kW/ms 램프의 공급 결손 = P_sc × (정지 지령 → 재개 지령)
    bat = _vj("2026-11-05-external-review", "E43", "bat.json")
    out = dict(branches={k: len(v) for k, v in br.items()}, branch_tags=br, P6_single_limit_A=lim1, P6_ib_max_by_V=ib, P6_ok=ok6,
               dab=dab, dab_limits=dab_lim, pause=dict(tag=wp["tag"], span_ms=wp["pause_ms"], hold_ms=hold * 1e3, ramp_ms=t_ramp * 1e3,
                                                       E_rect_J=E_rect, E_ramp_integral_J=E_int, port="고압 버스 쪽 Stage C 입력(E29 MX sc 5.3 kW)"),
               e43_bat=dict(rows=bat["rows"], P_W=bat["P_W"], T_s=bat["T_s"], load_J=bat["P_W"] * bat["T_s"], req=bat["req"],
                            port="48 V 출력 +5 kW 부하, 12.4 ms 완전 정지"))
    save_json(EID, "prot", out)
    print("  분기:", {k: len(v) for k, v in br.items()})
    print("  P6 단독 한도 %.1f A, 전압별 최대 %s" % (lim1, {k: round(v, 5) for k, v in ib.items()}))
    print("  DAB:", {k: (v["window"], round(v["sec_peak_A"], 5), round(v["prim_peak_A"], 5)) for k, v in dab.items()}, dab_lim)
    print("  정지 에너지: %s %.4f ms(정지→재개 %.4f ms), 사각 %.5f J, 램프 적분 %.5f J; E43 48 V 부하 %.1f J"
          % (wp["tag"], wp["pause_ms"], hold * 1e3, E_rect, E_int, out["e43_bat"]["load_J"]))
    verdict("(prot P6-I) 바이패스 전류 ≤ 단독 선형 한도 164.5 A(74건)", ok6)


# ======================================================================================================
# (vmap2)
# ======================================================================================================
def vmap2():
    import E45_review4_response as E45
    cs = load_json("E44", "fix_e42_cases")
    e43 = load_json("E44", "fix_e43_loss")
    for t in ("스위칭 × 0.7", "스위칭 × 1.5"):
        cs[t] = e43["e42"]["cases"][t]["new"]
    v2 = E45.judge_cells_v2(cs)
    old = json.loads((VAL / "2026-11-06-review4" / "E45" / "vmap.json").read_text(encoding="utf-8"))["cells"]
    same = all(v2[k].get("cls") == old[k].get("cls") and v2[k].get("ties", []) == old[k].get("ties", []) and v2[k].get("best_fair") == old[k].get("best_fair")
               for k in v2)
    zeros = sum(1 for z in v2.values() for v in z.get("min_rel_to_case_best_pct", {}).values() if v == 0.)
    verdict("(vmap2 a) min_rel 기록 정정 뒤 14칸 분류·후보가 E45와 같음", same, "0 기록 %d개" % zeros, gate=True)
    # (b) ±5 V 경로
    import inspect
    import E15_baseline_loss_rating as base
    import E18_industry_value_map as window
    import E36_a25r_impact as revised
    import E41_fair_aux_comparison as fair
    import E43_review2_response as corr
    base.DEV["SiC1200"]["Voss"] = 1000.                               # E44 소자 조건 정정과 같게
    import E38_review_response as final
    base.stage_c = final.stage_c_models()[0]
    nom = load_json("E44", "fix_e42_value_map_fair")
    src = inspect.getsource(window.path_window)
    assert src.count("if V / 2 > VW + 0.5:") == 1
    setting = {}
    ns = dict(window.__dict__); ns["_SET"] = setting
    exec(src.replace("if V / 2 > VW + 0.5:", "if V / 2 >= VW + _SET['th']:"), ns)
    pw = ns["path_window"]
    sa0 = revised._ext_model("A25R")
    ks = dict(base.K); hs = base.hs_converter
    others = [t for t in cs if t != "E38 기준(셰딩 없음)"]
    res = {}
    try:
        for direction, th in (("registered", 0.5), ("ascending", 5.), ("descending", -5.)):
            setting["th"] = th
            diag = json.loads(json.dumps(cs))
            win = {}
            for tag in others:
                base.K.clear(); base.K.update(ks)
                sa = sa0
                if tag.startswith("자성체"):
                    mult = .5 if "0.5" in tag else 2.
                    for k in ("mag_ind_cu", "mag_ind_core", "mag_tr_cu", "mag_tr_core"):
                        base.K[k] *= mult
                elif tag.startswith("스위칭"):
                    mult = .7 if "0.7" in tag else 1.5
                    base.K["esw"] = mult
                    sa = type(sa0)(sa0.VG, corr._scaled_P(sa0.T["P"], sa0.VG, mult), sa0.T["D"], sa0.T["charge"])
                elif tag.startswith("제어"):
                    base.K["ctrl"] = 0
                elif tag.startswith("GaN"):
                    base.K["gan_t"] = 2
                base.hs_converter = fair._hs_shed(base, hs, 25e3 if "25 kHz" in tag else None)
                for pk, x in nom["packs"].items():
                    vb = window.pack(int(pk[:-1]))["drive"] if pk != "spec" else base.PROFILES["drive_typ"]["V"]
                    for mode, VW in window.WINDOW.items():
                        z = x["structs"][mode]; Pr = z["stage_b"]["dab_rated_W"]
                        if Pr is None or not any(mode in cs[tag][pk]["feas"][cc] for cc in window.CLASSES):
                            continue
                        L = np.array([[pw(sa, V, P, base.P48, VW, Pr)["loss"] for P in base.P400] for V in vb])
                        val = float(np.mean(L @ base.W400))
                        diag[tag][pk]["loss"][mode] = val
                        if tag == "공정 기준(F1)":
                            win["%s/%s" % (pk, mode)] = dict(active=int(sum(float(v / 2) >= VW + th for v in vb)), n=len(vb), W=val,
                                                             stored_W=cs[tag][pk]["loss"][mode])
            v = E45.judge_cells_v2(diag)
            res[direction] = dict(window=win, cells={k: dict(best=z.get("best_fair"), ties=z.get("ties", []), cls=z["cls"]) for k, z in v.items()})
    finally:
        base.hs_converter = hs; base.K.clear(); base.K.update(ks)
    reg_ok = all(abs(z["W"] - z["stored_W"]) < 1e-6 for z in res["registered"]["window"].values())
    verdict("(vmap2 b0) 등록 경계(+0.5 V)로 다시 계산한 창 손실이 저장값과 같음", reg_ok, gate=True)
    changed = {d: {k: v for k, v in res[d]["cells"].items() if v != res["registered"]["cells"][k]} for d in ("ascending", "descending")}
    # (c) 누설 L 정정 전후 정적 포트 성립
    cnt = _ldab_points()
    out = dict(cells_v2=v2, same_as_E45=same, zero_records=zeros, path=res, changed_cells=changed, ldab=cnt,
               Ldab_uH={k: 11.1 * (v / 400.) ** 2 for k, v in window.WINDOW.items()})
    save_json(EID, "vmap2", out)
    for d in ("registered", "ascending", "descending"):
        print("  %s: %s" % (d, {k: (v["active"], v["n"], round(v["W"], 2)) for k, v in res[d]["window"].items()}))
    print("  바뀐 칸:", json.dumps(changed, ensure_ascii=False))
    print("  누설 L 정정: 활성 정적점 %d개 중 성립 변화 %d개" % (cnt["points"], cnt["changed"]))


def _ldab_points():
    """E18 정적 포트 성립성: 누설 L 11.1 µH(이전) 대 11.1·(V_W/400)² µH. 팩별 창 정격은 E18 window_rating_W, 사양 팩 포함."""
    import E18_industry_value_map as window
    import E15_baseline_loss_rating as base
    from controller_reference import NOMINAL
    from model_stage_b import steady_feasible
    cnt = dict(points=0, changed=0, examples=[], by=[])
    packs = {str(n): window.pack(n) for n in window.CELLS}
    packs["spec"] = dict(full=np.linspace(640., 920., 25))
    for k, pk in packs.items():
        for mode, VW in window.WINDOW.items():
            _, Pr = window.window_rating_W(pk, VW)
            if not Pr:
                continue
            p_old = replace(NOMINAL, vref=VW, turns=VW / NOMINAL.vlink, power_max=Pr)
            p_new = replace(p_old, Ldab=NOMINAL.Ldab * (VW / 400.) ** 2)
            n0 = cnt["points"]
            for V in pk["full"]:
                if not V / 2 > VW + 0.5:
                    continue
                for P in window.P_STATIC:
                    a = steady_feasible(V, P, p_old, control_reserve=False); b = steady_feasible(V, P, p_new, control_reserve=False)
                    cnt["points"] += 1
                    if bool(a) != bool(b):
                        cnt["changed"] += 1; cnt["examples"].append([k, mode, float(V), P, bool(a), bool(b)])
            cnt["by"].append([k, mode, Pr, cnt["points"] - n0])
    return cnt


def ldab():
    """vmap2 (c)만 다시(실행 경과: 1차 실행의 점 집합 정정)."""
    cnt = _ldab_points()
    v = load_json(EID, "vmap2")
    v["ldab_run1"] = v.get("ldab"); v["ldab"] = cnt
    save_json(EID, "vmap2", v)
    print("  누설 L 정정: 활성 정적점 %d개 중 성립 변화 %d개, %s" % (cnt["points"], cnt["changed"], cnt["by"]))


def nc():
    import E15_baseline_loss_rating as base
    k0 = base.K["stageB_nc"]
    out = dict(dab={}, hbridge={})
    try:
        for Pl in (0., 1000., 3000.):
            base.K["stageB_nc"] = 1.; a = base.dab_loss(Pl, 8000.)
            base.K["stageB_nc"] = 0.; b = base.dab_loss(Pl, 8000.)
            out["dab"][str(Pl)] = dict(total=a, cond=b, nc=a - b)
        for ih in (0., 25., 60.):
            base.K["stageB_nc"] = 1.; a = base.hbridge_loss(20., ih)
            base.K["stageB_nc"] = 0.; b = base.hbridge_loss(20., ih)
            out["hbridge"][str(ih)] = dict(total=a, cond=b, nc=a - b)
    finally:
        base.K["stageB_nc"] = k0
    out["breakeven"] = load_json("E44", "fix_l1_e15_comparison").get("breakeven")
    save_json(EID, "nc", out)
    print("  DAB 8 kW 비도통 항:", {k: round(v["nc"], 4) for k, v in out["dab"].items()}, " H-브리지 20 V:", {k: round(v["nc"], 4) for k, v in out["hbridge"].items()})
    print("  저장 배율:", out["breakeven"])


# ======================================================================================================
# (loss)
# ======================================================================================================
def loss():
    import E15_baseline_loss_rating as base
    J = load_json("E44", "fix_e41_fair")["cases"]["공정 기준(F1)"]
    ld = {}
    for pk, z in J.items():
        dl = np.array(z["by_load"]["4"]) - np.array(z["by_load"]["5"])
        d = float(base.W400 @ dl)
        ld[pk] = dict(diff_4_5_by_load_W=list(map(float, dl)), weighted_W=d, shift_frac_0p5_to_23=float(d / (dl[0] - dl[-1])))
    e25 = load_json("E44", "fix_l1_e25_comparison")
    aux = e25["breakeven"]["aux_diff_4_minus_6_W"]
    st = load_json("E44", "fix_l1_e25_statements") if (common.RESULTS / "E44" / "fix_l1_e25_statements.json").exists() else None
    ch = e25["charge"]
    out = dict(load_shift=ld, aux_diff_4_minus_6_W=aux, crossover=_crossover(ch, aux), stored_breakeven=e25["breakeven"], statements=st)
    save_json(EID, "loss", out)
    print("  ④−⑤ 대표:", {k: (round(v["diff_4_5_by_load_W"][0], 2), round(v["diff_4_5_by_load_W"][-1], 2), round(v["weighted_W"], 3),
                                round(100 * v["shift_frac_0p5_to_23"], 3)) for k, v in ld.items()})
    print("  총손실 교점(kWh/주행 h):", json.dumps(out["crossover"], ensure_ascii=False))


def _crossover(ch, aux):
    """ch: fix_l1_e25_comparison['charge']. 전압별 Stage A·모터 기준점·격자 최소 손실(W)을 찾아 교점 = aux / ((P_motor − P_A)/P_ch)."""
    out = {}
    P = {"640V": 120e3, "800V": 150e3, "920V": 172.5e3}
    for V, Pch in P.items():
        z = ch.get(V) if isinstance(ch, dict) else None
        if not isinstance(z, dict):
            continue
        a = float(z["stageA"]); mb = float(z["motor_base"]); mm = float(z["motor_range"]["min_Rph5"])
        row = dict(stageA_W=a, motor_base_W=mb, motor_min_W=mm, booster_W=float(z["booster"]))
        for nm, m in (("base", mb), ("min", mm)):
            if a is not None and m is not None:
                f = (m - a) / Pch
                row["kWh_per_h_" + nm] = aux / f / 1e3 if f > 0 else None
        out[V] = row
    return out


# ======================================================================================================
# (ripple)
# ======================================================================================================
def ripple():
    import E43_review2_response as E43
    s1 = json.loads((VAL / "2026-11-05-external-review" / "E43" / "sens.json").read_text(encoding="utf-8"))
    rows = s1["rows"]
    w = max(rows, key=lambda r: r["tail_ripple_V"])
    js = E43._sens_jobs(E43.VARIANTS_S1)
    job = next(j for j in js if (j[0], j[1], j[2], j[3], j[4], j[5], j[6]) == (w["case"], w["tier"], w["set"], w["vbat"], w["p0"], w["p1"], w["variant"]))
    from model_stage_b_switching import simulate_switching
    import E19_r2_window_module as E19
    import stage_b_tests as st
    from controller_adopted import K_ADOPTED
    case, tier, sname, v, a, b, var, kind, sign, seed = job
    p, cp = E19.plant(case)
    if sname == "delay+3.0us":
        p = replace(p, delay=p.delay + st.DELAY_BUDGET)
    sen = None if kind is None else E43.sens_arr(kind, case, sign)
    r = simulate_switching(float(v), float(a), float(b), p, cp, K_ADOPTED, predict=True, sensors=sen, seed=seed)
    t, R = r["t"], r["rec"]
    post = t >= 1e-3 - 1e-12; tail = (t >= t[-1] - 1e-3) & post
    rip_avg = float(np.ptp(R[tail, 0])); rip_inst = float(R[tail, 10].max() - R[tail, 9].min()); per = float(np.max(R[tail, 10] - R[tail, 9]))
    ok = abs(rip_avg - w["tail_ripple_V"]) <= 1e-6 * max(1., w["tail_ripple_V"])
    out = dict(case=dict(case=case, tier=tier, set=sname, vbat=v, p0=a, p1=b, variant=var), stored=w["tail_ripple_V"], ripple_period_avg_V=rip_avg,
               ripple_instant_V=rip_inst, single_period_max_V=per, vmax_period_avg=float(R[post, 0].max()), vmax_instant=float(R[post, 10].max()))
    save_json(EID, "ripple", out)
    print("  %s: 주기평균 폭 %.8f V(저장 %.8f), 순시 최대−최소 %.8f V, 단일 주기 최대 %.8f V, 최고 평균 %.4f·순시 %.4f V"
          % (out["case"], rip_avg, w["tail_ripple_V"], rip_inst, per, out["vmax_period_avg"], out["vmax_instant"]))
    verdict("(ripple) 원 정의 리플이 저장값과 같음", ok, gate=True)


# ======================================================================================================
# (gate, cache)
# ======================================================================================================
def gate():
    import copy
    import E45_review4_response as E45
    old = json.loads((VAL / "2026-11-06-review3" / "E44" / "cfly.json").read_text(encoding="utf-8"))
    new = json.loads((VAL / "2026-11-06-review4" / "E45" / "cfly_refactor.json").read_text(encoding="utf-8"))
    cases = []
    ok, det = E45.fcheck_judge(old, new); cases.append(("정상", ok, True, det["problems"]))
    o2, n2 = copy.deepcopy(old), copy.deepcopy(new)
    del o2["F-a_45.00uF"]["transient"][0]; del n2["F-a_45.00uF"]["transient"][0]
    ok, det = E45.fcheck_judge(o2, n2); cases.append(("같은 행 삭제", ok, False, det["problems"]))
    n3 = copy.deepcopy(new); n3["F-b_42.75uF"]["f_control_Hz"] = 20000.0
    ok, det = E45.fcheck_judge(old, n3); cases.append(("제어 주파수 20 kHz", ok, False, det["problems"]))
    n4 = copy.deepcopy(new); n4["F-b_42.75uF"]["fault"][0]["phase_peak"] += 10.0
    ok, det = E45.fcheck_judge(old, n4); cases.append(("첨두 +10 A", ok, False, [list(map(str, x)) for x in strict_diff(old["F-b_42.75uF"]["fault"], n4["F-b_42.75uF"]["fault"])[:2]]))
    good = all(c[1] == c[2] for c in cases)
    # 종료 코드: 실패하는 gate 판정 하나를 자식 프로세스에서 내고 종료 코드를 본다
    code = subprocess.run([sys.executable, "-c", "import common,sys; common.verdict('주입',False,gate=True); sys.exit(common.exit_status())"],
                          cwd=str(HERE), capture_output=True, text=True).returncode
    code0 = subprocess.run([sys.executable, "-c", "import common,sys; common.verdict('주입',True,gate=True); sys.exit(common.exit_status())"],
                           cwd=str(HERE), capture_output=True, text=True).returncode
    save_json(EID, "gate", dict(cases=[dict(case=c[0], S2=c[1], expected=c[2], problems=c[3]) for c in cases], exit_fail=code, exit_pass=code0))
    for c in cases:
        print("  %-16s S2=%s(기대 %s) %s" % (c[0], c[1], c[2], c[3][:2]))
    verdict("(gate) 오류 주입 네 경우가 기대대로, 필수 실패는 종료 코드 1", good and code == 1 and code0 == 0, "종료 %d·%d" % (code, code0), gate=True)


def cache():
    import copy
    import E44_review3_response as E44
    P = E44._setup_part("spec")
    h0 = E44._clamp_config_hash("spec", P)
    P2 = copy.deepcopy(P)
    sw = P2["sw"][P2["swn"]]
    sw["therm"] = [(Tb, Rth * 1.05) for Tb, Rth in sw["therm"]]
    h1 = E44._clamp_config_hash("spec", P2)
    save_json(EID, "cache", dict(switch=P["swn"], therm0=P["sw"][P["swn"]]["therm"], therm1=sw["therm"], hash0=h0, hash1=h1, changed=h0 != h1))
    verdict("(cache) 열저항 +5 %이면 재개 키가 바뀜", h0 != h1, gate=True)


PARTS = dict(power=power, h1=h1, h2d=h2d, h2s=h2s, h4=h4, ramp=ramp, tb25=tb25, e31=e31, c22=c22, tb15=tb15, prot=prot, vmap2=vmap2,
             loss=loss, ripple=ripple, gate=gate, cache=cache, nc=nc, ldab=ldab)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        if w not in PARTS:
            raise SystemExit("알 수 없는 부분: %s (가능: %s)" % (w, ", ".join(PARTS)))
    for w in want:
        print("\n==== E46 %s ====" % w, flush=True)
        PARTS[w]()
    sys.exit(common.exit_status())
