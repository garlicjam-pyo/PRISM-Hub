"""[E29] 보호 상태기계와 SALS의 연동: 400 V 부하 분리·감발 명령의 전달 지연·손실과 부하 계약 응답을 넣은 강등 순서 확인.

■ 목적
  R2 창 조정 모듈의 H-브리지 고장 강등(docs/24·25·26)은 "400 V 부하가 명령 20 ms 뒤 5 kW로 줄어든다"는 가정 위에 있다
  (E17·E20·E21). 실제로는 두 경로가 있다.
    (1) V_A가 부품 상한을 넘는 팩: 400 V급 부하를 접촉기로 분리한다(하드웨어 신호, 20 ms).
    (2) 상한 안 팩의 일시 감발: SALS 메시지로 부하에 전한다. 메시지는 1–5 ms 늦게 닿고 잃어버릴 수 있다. 부하는 계약
        변화율(0.5 kW/ms)로만 줄고, M0(Stage C·V2L)는 줄지 않는다. M1(컴프레서)에는 워치독이 없다.
  이 응답을 넣어도 강등 순서가 판정을 지키는지, 지키지 못하면 무엇을 바꿔야 하는지 확인한다. 이중 고장(상태 13)의 Stage A
  협조 정지도 모델에 넣는다(docs/24 남은 과제 4).

■ 왜 필요한가
  감발이 늦거나 덜 되면 (a) H-브리지 고장 유지(9)가 길어져 DAB 순환전류 노출과 제동 저항 에너지가 늘고, (b) 남은 부하가
  크면 링크 붕괴·소프트 투입이 실패해 이중 고장으로 간다. 또 감발이 D·M1만 끄면 48 V 회생(Stage C −3.2 kW)이 남아 버스
  순부하가 음이 될 수 있다. 다이오드 정류 유지는 경로전류가 양(버스 → 부하)일 때의 극성을 가정한다.

■ 연동 설계(이 시험에서 정함, 공용 모듈 sals_loads.py와 E17 r2_run의 sals 인자)
  - 고장 검출 → SALS 감발(D 허용치 0, M1 한도 0, 10 ms마다 재송신) + Stage C 회생 차단(허브 내부 명령, 0.1 ms 뒤 4 kW/ms).
    V_A 추정 > 상한 − 2 V면 접촉기 분리도 바로 명령한다(20 ms). 분리되면 Stage C만 남는다.
  - 감발 전용 팩(V_A ≤ 상한 − 2 V): 유지(9)를 시간이 아니라 측정으로 끝낸다. 부하전류 추정 i_load = i_p − (C_b + C_dmp)·dv_bus/dt
    (0.2 ms 필터)가 |i_load| ≤ I_COL로 T_CONF(0.2 ms) 이어지면 링크 붕괴(10)로. T_CUR_MAX 안에 안 되면 접촉기 분리로 넘어간다.
    (처음에는 경로전류 i_p만 봤다. seq 실행 전 점검에서, 고장 직후 다이오드가 막힌 동안(직렬 커패시터 충전, 25 kW에서 약 2.8 ms,
     부하가 작을수록 길다) 버스 커패시터가 부하를 대고 경로전류는 약 3 A라 감발 전에 확인이 성립했다. 그래서 추정으로 바꿨다.)
  - 강등 0.5 ms 뒤 SALS 되돌림(D·M1 증가 0.06 kW/ms). 접촉기를 연 경우 되돌리지 않는다(재연결은 부하 쪽 사전충전, 모델 밖).
  - 이중 고장(13): 접촉기 분리 + SALS 감발, Stage A 정지(상태 진입 + 5 µs, 모든 위상 자연 턴오프), 링크 제동 저항의
    과전압 보호(110 V 켬·105 V 끔) 유지.
  - 강등 순서 자체는 E21 P3t(전압비 정합 유지, EPS 첨두 상한 1.387배, 소프트 투입 시간 상한 → 이중 고장)를 그대로 쓴다.

■ 부분
  contract : 감발 완료 시간의 해석 상한과 몬테카를로(지연 1–5 ms 균일, 손실 0·5·20 %, 부하 구성 무작위)
  resid    : 감발 뒤 남는 부하별 H-브리지 고장 강등(감발 전용 팩 W460 930 V·W410 832 V, 25 kW, E21 P3t, 감발 20 ms 계단)
             → 문턱 I_COL(아래 규칙)
  seq      : 연동 강등 × 부하 구성 3 × 메시지 시나리오 6 × 팩 4, 분리 50 ms 감도
  regen    : 고장 순간 버스 순부하가 음(48 V 회생)이거나 감발로 음이 되는 경우, Stage C 회생 차단 유무
  failsafe : 이중 고장(DAB 고장 검출 0.5 ms 뒤 H-브리지 차단): 대책 없음(F0) / 제동 유지 + 부하 차단(F1) / + Stage A 정지(F2)
  regress  : 새 인자를 주지 않으면 E17·E21 저장 결과와 같은가
  figures

■ 설계값을 정하는 규칙(resid 실행 전에 고정)
  I_COL(모듈 설계별) = 0.8 × P_ok / (상한 − 2 V). P_ok는 resid에서 두 팩 모두 판정을 통과한 가장 큰 남는 부하다
  (분모는 감발 전용 팩의 가장 높은 V_A: |i_p| ≤ I_COL이면 남는 부하 ≤ 0.8 P_ok).
  T_CUR_MAX = 30 ms = 손실 없는 계약 상한 19 ms(지연 5 ms + 7 kW ÷ 0.5 kW/ms) + 재송신 한 번(10 ms)을 올림.

■ 판정(시험 전에 고정)
  resid·seq·regen(각 사례): E17 고장 판정(경로·필터 ≤ 100 A, 직렬 ≤ 120 V, 링크 ≤ 120 V, 바이패스 ≤ 329 A, 버스 ≥ 260 V,
      강등 상태 도달, 400 V 부하 연결 중 버스 ≤ 상한) + DAB 링크 쪽 첨두 ≤ 1.5 × 정격점(E20·E21) + 제동 저항 에너지 ≤ 64 J
      (docs/24 추가 하드웨어의 고장당 설계값).
      (정보) 유지 시간, 강등 완료 시각, 접촉기 개방 순간 경로전류, 소프트 투입 에너지, 서비스 중단(감발 시작 → 되돌림 완료).
  failsafe(각 사례): 경로·필터 ≤ 100 A, 직렬 ≤ 120 V, 링크 ≤ 120 V, 400 V 부하 연결 중 버스 ≤ 상한, 제동 에너지 ≤ 64 J,
      Stage A 정지(또는 이중 고장 진입) 뒤 5 ms 안에 |i_p| ≤ 1 A가 되어 끝까지 유지.
  contract: 손실 없는 몬테카를로 최대 ≤ 해석 상한(19 ms). 나머지는 정보(손실률별 T_CUR_MAX 초과 확률).
  regress : 저장된 E17 r2(DAB 고장·켬)·E21 compare(P3t) 행과 수치 키가 모두 같음(차 0).

■ 실행 경과와 결과(2026-10-28, 기준은 바꾸지 않았다)
  contract: 손실 없는 최대 18.98 ms ≤ 19 ms. 감발 완료가 T_CUR_MAX(30 ms)를 넘는 비율: 손실 5 % 0.34 %, 20 % 6.9 %.
  resid  : W460 930 V는 남는 부하 13 kW까지 통과(15.1 kW는 소프트 투입 시간 상한 → 이중 고장), W410 832 V는 15.1 kW까지 통과
           → I_COL 22.22·28.9 A. 소프트 투입 소자 에너지는 남는 부하에 따라 크게 늘었다(W460 5 kW 0.031 J → 9.1 kW 0.77 J → 13 kW 2.7 J).
  (seq 전 점검) 유지 끝을 경로전류로만 판단하자 고장 직후 다이오드 차단 구간(경로전류 약 3 A)에 감발 전에 확인이 성립했다
           → 부하전류 추정(위 연동 설계)으로 바꿨다.
  seq    : 74/74 통과. 손실 2번·컴프레서 손실·모두 손실의 M0 큰 구성은 접촉기 대체(유지 50 ms, 제동 ≤ 53.3 J).
  regen  : 차단 없음 R1 4/4 불통과(버스 480.6·527.0·432.7·483.4 V), 차단 있음 12/12 통과.
  regen_sens(정보): 통과하는 가장 긴 차단 지연 t_sc는 W460 1.0 ms, W410 0.5 ms.
  failsafe: 1차(설정 오류, 아래 T_EV2 주석)는 failsafe_run1_pre_detection.json. 2차(검출 0.5 ms 뒤 차단):
           F0·F1 모두 불통과(링크 138–252 V, 직렬 142–254 V). F2 1/4 통과: 링크 ≤ 110.1 V·직렬 ≤ 114.2 V·제동 ≤ 7.5 J는 모두 지켰지만
           |i_p| ≤ 1 A까지 4.73(W410 860 V)·5.07·6.83·7.29 ms로 세 사례가 5 ms 기준을 넘었다. Stage A가 멈춘 뒤에도 접촉기가 열리기
           전(20 ms) 부하가 C_A·버스 커패시터에서 전력을 빼고, 경로전류는 버스가 저전압 차단(250 V)에 닿을 때까지 흐른다.
  regress: E21·E20 행은 차 0, E17 행은 저장 결과(2026-10-24)와 6.4e-14·9.8e-15 차 → 엄밀 기준 불통과로 기록.
           변경 전 코드(git HEAD)로 같은 행을 계산하면 현재 코드와 차 0이었다(regress_head_check.json): 1e-14 차는 이 변경 전부터 있던 것.
           E20 행의 '판정 같음 False'는 E20 저장 판정에 DAB 1.5배 항목이 더 있어서다(수치는 같음).

■ 실행   python E29_sals_degradation.py contract resid seq regen regen_sens failsafe regress figures   (2코어 약 60분)
■ 결과   results/E29/*.json, results/E29/E29_sals_degradation.png
"""
import math
import sys
import time
from multiprocessing import Pool

import numpy as np

import E17_protection_integration as E17
import E21_dab_switching_margin as E21
from common import save_json, load_json, verdict, workers, outdir
from sals_loads import SalsLoads, DEV

EID = "E29"
P3T = E21.P3T                                     # 강등 순서(E21 P3t)
CUR_PACKS = {"W460_240s": 930., "W410_spec": 832.}          # 감발 전용 팩(V_A ≤ 상한 − 2 V, 창 조정 동작 중)
SEP_PACKS = {"W460_240s": 1008., "W410_spec": 920.}         # 분리 팩(V_A > 상한)
P0 = 25000.
BRK_MAX = 64.                                      # 제동 저항 에너지 상한 [J/고장] (docs/24)
PK_RATIO_MAX = 1.5                                 # DAB 링크 쪽 첨두 / 정격점 (E20·E21)
T_CONF = .2e-3
T_CUR_MAX = 30e-3
I_COL = {"W460_240s": 22.22, "W410_spec": 28.9}    # resid(2026-10-28) 뒤 규칙으로 정함: 0.8 × P_ok / (상한 − 2 V),
                                                   # P_ok = 13.0 kW(W460 930 V, 15.1 kW는 소프트 투입 시간 상한 → 이중 고장)·15.1 kW(W410 832 V, 시험 최대)
MIXES = {                                          # 고장 순간 부하 구성 [W] (합 25 kW: Tier-2 수준, E17·E21과 같은 전력)
    "MX": dict(sc=5300., v2l=3800., comp=6000., ptc=7000., bh=2900.),   # M0 최대(남는 부하 9.1 kW)
    "MD": dict(sc=5300., v2l=0., comp=5700., ptc=7000., bh=7000.),      # D 최대(감발이 가장 오래, 남는 부하 5.3 kW)
    "ML": dict(sc=2000., v2l=0., comp=3000., ptc=5000., bh=0.),         # 경부하 10 kW
}
SCEN = {                                           # 메시지 시나리오(감발·되돌림 메시지 모두)
    "S1": dict(delay=1e-3),                        # 최선 지연
    "S5": dict(delay=5e-3),                        # 최악 지연(손실 없음)
    "L1": dict(delay=5e-3, lost=dict(comp=1, ptc=1, bh=1), lost_r=dict(comp=1, ptc=1, bh=1)),   # 첫 송신 손실
    "L2": dict(delay=5e-3, lost=dict(comp=2, ptc=2, bh=2), lost_r=dict(comp=2, ptc=2, bh=2)),   # 두 번 손실
    "LC": dict(delay=5e-3, lost=dict(comp="all")),                  # 컴프레서만 모두 손실(워치독 없음)
    "LA": dict(delay=5e-3, lost=dict(comp="all", ptc="all", bh="all")),   # 모두 손실(D는 워치독 50 ms)
}


def i_col(case):
    if I_COL is not None:
        return I_COL[case]
    return load_json(EID, "resid")["i_col"][case]


def fault_checks(m):
    c = dict(m["checks"])
    c["dab_peak_1p5"] = bool(m["dab_peak_ratio"] <= PK_RATIO_MAX)
    c["brake_64J"] = bool(m["brk_energy_J"] <= BRK_MAX)
    return c


def ev_time(m, name):
    for e in m["events"]:
        if e[0] == name:
            return e[1]
    return None


def summarize(m, extra=None):
    """판정과 정보 지표(시각은 고장 시각 기준 ms)."""
    t0 = E17.T_EV * 1e3
    tr = m.pop("trace", None)
    ch = fault_checks(m)
    th, tc, tdg = ev_time(m, "HB_HOLD"), ev_time(m, "HB_COLLAPSE"), ev_time(m, "DEGRADED")
    out = dict(case=m["case"], V=m["V"], P=m["P"], event=m["event"], final_state=m["final_state"], checks=ch, pass_=bool(all(ch.values())),
               path_peak=m["path_peak"], bridge_peak=m["bridge_peak"], series_peak=m["series_peak"], vlink_max=m["vlink_max"],
               vbus_min=m["vbus_min"], vbus_max_loaded=m["vbus_max_loaded"], dab_sec_peak=m["dab_sec_peak"], dab_peak_ratio=m["dab_peak_ratio"],
               brk_energy_J=m["brk_energy_J"], soft_energy_J=m["soft_energy_J"], soft_entry=m["soft_entry"], soft_timeout=m["soft_timeout"],
               hold_ms=None if (th is None or tc is None) else round(tc - th, 4),
               deg_ms=None if tdg is None else round(tdg - t0, 4), events=m["events"], t_cont_ms=m.get("t_cont_ms"),
               restored=m.get("restored"), fallback=ev_time(m, "fallback_sep") is not None)
    if m.get("sals"):
        s = m["sals"]
        L = rebuild(s)
        out["curtail_done_ms"] = None if not math.isfinite(L.curtail_done()) else round((L.curtail_done() - E17.T_EV) * 1e3, 3)
        out["restore_done_ms"] = None if not math.isfinite(L.restore_done()) else round((L.restore_done() - E17.T_EV) * 1e3, 3)
        out["sals"] = s
    if tr is not None and m.get("t_cont_ms") is not None:     # 접촉기 개방 순간 경로전류(차단 전류, 정보)
        tt, lg = tr["t"], tr["log"]
        k = np.searchsorted(tt, E17.T_EV + (m["t_cont_ms"] + m["t_shed_ms"]) * 1e-3)
        out["i_break"] = float(lg[min(k, len(lg) - 1), 0])
    if extra:
        out.update(extra)
    return out


def rebuild(s):
    """r2_run 기록(sals)에서 같은 부하 응답을 다시 만든다(그림·해석값용). 시간 값은 이미 ks가 곱해진 값이다."""
    ks = s["ks"]
    L = SalsLoads(s["mix_W"], delay={k: v / ks for k, v in s["delay_s"].items()}, lost=s["lost"], lost_r=s["lost_r"],
                  period=s["period_s"] / ks, wd=s["wd_s"] / ks, up=s["up_W_per_s"] * ks, dn=s["dn_W_per_s"] * ks,
                  sc_block=s["sc_block"], t_sc=s["t_sc_s"], sc_slew=s["sc_slew_W_per_s"], ks=ks)
    if s["t_cut"] is not None:
        L.curtail(s["t_cut"])
    if s["t_rest"] is not None:
        L.restore(s["t_rest"])
    return L


def _run(job):
    tag = job.pop("_tag", None); extra = job.pop("_extra", None)
    t = time.time()
    m = E17.r2_run(job)
    r = summarize(m, extra)
    r["tag"] = tag; r["run_s"] = round(time.time() - t, 1)
    return r


def pool_map(jobs):
    with Pool(workers()) as pool:
        return pool.map(_run, jobs, chunksize=1)


# ---------------------------------------------------------------------------------------------------------------
# contract: 감발 완료 시간
# ---------------------------------------------------------------------------------------------------------------
def contract(n=20000, seed=20261028):
    """감발 대상(M1·D)이 모두 0이 되는 시간. 장치마다 송신 k번째(0부터)가 처음 성공하는 횟수 k ~ 기하분포(손실 p),
    지연 U(1, 5) ms. D는 워치독(명령 + 50 ms)으로 상한, M1은 상한 없음."""
    rng = np.random.default_rng(seed)
    dn, period, wd = 500e3, 10e-3, 50e-3
    bound = 5e-3 + 7000. / dn                                     # 손실 없는 해석 상한(지연 5 ms + 7 kW ÷ 0.5 kW/ms)
    out = {}
    for p in (0., .05, .2):
        pw = np.column_stack([rng.uniform(0, 6000, n), rng.uniform(0, 7000, n), rng.uniform(0, 7000, n)])
        done = np.zeros(n)
        for j, k in enumerate(DEV):
            kk = rng.geometric(1 - p, n) - 1 if p > 0 else np.zeros(n, int)
            arr = kk * period + rng.uniform(1e-3, 5e-3, n)
            if k != "comp":
                arr = np.minimum(arr, wd)
            done = np.maximum(done, arr + pw[:, j] / dn)
        q = np.percentile(done, [50, 99, 99.9]) * 1e3
        out["p%.2f" % p] = dict(p_loss=p, n=n, p50_ms=q[0], p99_ms=q[1], p999_ms=q[2], max_ms=float(done.max() * 1e3),
                                 frac_over_tcur=float(np.mean(done > T_CUR_MAX)))
        print("  손실 %.0f %%: 중앙 %.1f ms, 99 %% %.1f ms, 99.9 %% %.1f ms, 최대 %.1f ms, T_CUR_MAX 초과 %.4f"
              % (p * 100, q[0], q[1], q[2], done.max() * 1e3, out["p%.2f" % p]["frac_over_tcur"]))
    ok = verdict("손실 없는 최대 ≤ 해석 상한", out["p0.00"]["max_ms"] <= bound * 1e3 + 1e-9,
                 "%.2f ≤ %.1f ms" % (out["p0.00"]["max_ms"], bound * 1e3))
    save_json(EID, "contract", dict(bound_no_loss_ms=bound * 1e3, T_CUR_MAX_ms=T_CUR_MAX * 1e3, rows=out, pass_=ok,
                                    note="frac_over_tcur: 감발 대상이 모두 0이 되는 시각이 T_CUR_MAX를 넘는 비율(정보)"))


# ---------------------------------------------------------------------------------------------------------------
# resid: 남는 부하 문턱
# ---------------------------------------------------------------------------------------------------------------
P_RES = [0., 2500., 5000., 7500., 9100., 11000., 13000., 15100.]


def resid():
    jobs = []
    for case, V in CUR_PACKS.items():
        for pr in P_RES:
            jobs.append(dict(case=case, V=V, P=P0, event="hb_open", policy="clamp_brk", p_c=pr, keep=False,
                             _tag="%s_%.0fV_res%.0f" % (case, V, pr), _extra=dict(p_res=pr), **P3T))
    rows = pool_map(jobs)
    ok_p, icol = {}, {}
    for case, V in CUR_PACKS.items():
        rr = sorted([r for r in rows if r["case"] == case], key=lambda r: r["p_res"])
        good = [r["p_res"] for r in rr if r["pass_"]]
        # 가장 큰 통과값(그 아래도 모두 통과일 때만 인정)
        pk = None
        for r in rr:
            if r["pass_"]:
                pk = r["p_res"]
            else:
                break
        ok_p[case] = pk
        upper = E17.E19.CASES[case]["upper"]
        icol[case] = None if pk is None or pk <= 0 else round(.8 * pk / (upper - 2), 2)
        for r in rr:
            print("  %s %.0f V 남는 %5.0f W: %s 경로 %.1f A, DAB %.2f배, 제동 %.1f J, 소프트 %s(%.3f J), 강등 %s ms, 최종 %s"
                  % (case, V, r["p_res"], "통과" if r["pass_"] else "불통과", r["path_peak"], r["dab_peak_ratio"], r["brk_energy_J"],
                     (r["soft_entry"] or {}).get("why"), r["soft_energy_J"], r["deg_ms"], r["final_state"]))
        verdict("%s 남는 부하 문턱" % case, pk is not None, "P_ok = %s W, 모든 통과값 %s → I_COL = %s A" % (pk, good, icol[case]))
    save_json(EID, "resid", dict(p_res=P_RES, rows=rows, p_ok=ok_p, i_col=icol,
                                 rule="I_COL = 0.8 × P_ok / (상한 − 2 V), P_ok = 0부터 이어서 통과한 가장 큰 남는 부하"))


# ---------------------------------------------------------------------------------------------------------------
# seq: 연동 강등
# ---------------------------------------------------------------------------------------------------------------
def sals_cfg(case, mix, scen, ks=1., sc_block=True, t_cur_max=T_CUR_MAX):
    return dict(loads=dict(mix=mix, ks=ks, sc_block=sc_block, **scen), i_col=i_col(case), t_conf=T_CONF,
                t_cur_max=t_cur_max * ks)                  # 확인 지속(전기 측정)은 축소하지 않는다


def seq_jobs():
    js = []
    for packs, kind in ((CUR_PACKS, "cur"), (SEP_PACKS, "sep")):
        for case, V in packs.items():
            for mn, mix in MIXES.items():
                P = sum(mix.values())
                for sn, sc in SCEN.items():
                    dur = E17.T_EV + (T_CUR_MAX + E17.T_SHED + 18e-3)
                    js.append(dict(case=case, V=V, P=P, event="hb_open", policy="clamp_brk", sals=sals_cfg(case, mix, sc),
                                   duration=dur, keep=True, _tag="%s_%.0f_%s_%s" % (case, V, mn, sn),
                                   _extra=dict(kind=kind, mix=mn, scen=sn, t_shed_ms=20.), **P3T))
    for case, V in SEP_PACKS.items():                                          # 감도: 접촉기 50 ms
        js.append(dict(case=case, V=V, P=P0, event="hb_open", policy="clamp_brk", sals=sals_cfg(case, MIXES["MX"], SCEN["S5"]),
                       t_shed=50e-3, duration=E17.T_EV + 50e-3 + 18e-3, keep=True, _tag="%s_%.0f_MX_S5_shed50" % (case, V),
                       _extra=dict(kind="sep", mix="MX", scen="S5", t_shed_ms=50.), **P3T))
    return js


def seq():
    rows = pool_map(seq_jobs())
    n = sum(r["pass_"] for r in rows)
    for r in rows:
        bad = [k for k, v in r["checks"].items() if not v]
        print("  %-30s %s 유지 %6s ms 강등 %6s ms 경로 %5.1f A DAB %.2f배 제동 %5.1f J 소프트 %.3f J 분리 %s 되돌림 %s %s"
              % (r["tag"], "통과" if r["pass_"] else "불통과", r["hold_ms"], r["deg_ms"], r["path_peak"], r["dab_peak_ratio"],
                 r["brk_energy_J"], r["soft_energy_J"], r["t_cont_ms"], r.get("restore_done_ms"), bad))
    verdict("seq 전체", n == len(rows), "%d/%d" % (n, len(rows)))
    save_json(EID, "seq", dict(rows=rows, n_pass=n, n=len(rows), settings=dict(T_CONF=T_CONF, T_CUR_MAX=T_CUR_MAX,
                                                                                I_COL={c: i_col(c) for c in CUR_PACKS},
                                                                                mixes=MIXES, scen=SCEN, P3T=P3T)))


# ---------------------------------------------------------------------------------------------------------------
# regen: 버스 순부하가 음일 때
# ---------------------------------------------------------------------------------------------------------------
RMIX = {"R1": dict(sc=-3200.),                                       # 고장 순간부터 음(−3.2 kW)
        "R2": dict(sc=-3200., ptc=7000.),                            # +3.8 kW, 감발로 −3.2 kW
        "R3": dict(sc=-3200., v2l=3800., comp=6000., ptc=7000., bh=7000.)}   # +20.6 kW, 감발 뒤 +0.6 kW


def regen():
    js = []
    for case, V in (("W460_240s", 930.), ("W460_240s", 1008.), ("W410_spec", 832.), ("W410_spec", 920.)):
        for rn, mix in RMIX.items():
            for blk in (False, True):
                if rn == "R3" and not blk:
                    continue
                mx = {k: mix.get(k, 0.) for k in ("sc", "v2l", "comp", "ptc", "bh")}
                js.append(dict(case=case, V=V, P=sum(mx.values()), event="hb_open", policy="clamp_brk",
                               sals=sals_cfg(case, mx, SCEN["S5"], sc_block=blk), duration=E17.T_EV + T_CUR_MAX + E17.T_SHED + 18e-3,
                               keep=True, _tag="%s_%.0f_%s_%s" % (case, V, rn, "block" if blk else "noblock"),
                               _extra=dict(mix=rn, sc_block=blk), **P3T))
    rows = pool_map(js)
    for r in rows:
        bad = [k for k, v in r["checks"].items() if not v]
        print("  %-32s %s 버스(연결 중) 최대 %6.1f V, 최저 %6.1f V, 경로 %5.1f A, 강등 %s ms, 최종 %s %s"
              % (r["tag"], "통과" if r["pass_"] else "불통과", r["vbus_max_loaded"] or 0, r["vbus_min"], r["path_peak"],
                 r["deg_ms"], r["final_state"], bad))
    nb = [r for r in rows if r["sc_block"]]
    verdict("회생 차단 있음 전체", all(r["pass_"] for r in nb), "%d/%d" % (sum(r["pass_"] for r in nb), len(nb)))
    save_json(EID, "regen", dict(rows=rows, mixes=RMIX))


def regen_sens():
    """(정보) Stage C 회생 차단의 응답 지연 t_sc 감도: R1(고장 순간 −3.2 kW), 차단 있음. 통과하는 가장 긴 t_sc를 요구값으로 남긴다."""
    js = []
    mx = {k: RMIX["R1"].get(k, 0.) for k in ("sc", "v2l", "comp", "ptc", "bh")}
    for case, V in (("W460_240s", 930.), ("W460_240s", 1008.), ("W410_spec", 832.), ("W410_spec", 920.)):
        for tsc in (.1e-3, .3e-3, .5e-3, 1e-3, 2e-3):
            cfg = sals_cfg(case, mx, SCEN["S5"], sc_block=True); cfg["loads"]["t_sc"] = tsc
            js.append(dict(case=case, V=V, P=sum(mx.values()), event="hb_open", policy="clamp_brk", sals=cfg,
                           duration=E17.T_EV + T_CUR_MAX + E17.T_SHED + 18e-3, keep=True,
                           _tag="%s_%.0f_R1_tsc%.1fms" % (case, V, tsc * 1e3), _extra=dict(t_sc_ms=tsc * 1e3), **P3T))
    rows = pool_map(js)
    lim = {}
    for r in rows:
        print("  %-30s %s 버스(연결 중) 최대 %6.1f V" % (r["tag"], "통과" if r["pass_"] else "불통과", r["vbus_max_loaded"] or 0))
        key = "%s_%.0f" % (r["case"], r["V"])
        if r["pass_"]:
            lim[key] = max(lim.get(key, 0.), r["t_sc_ms"])
    print("  통과하는 가장 긴 t_sc [ms]:", lim)
    save_json(EID, "regen_sens", dict(rows=rows, t_sc_max_pass_ms=lim))


# ---------------------------------------------------------------------------------------------------------------
# failsafe: 이중 고장
# ---------------------------------------------------------------------------------------------------------------
T_EV2 = .5e-3                    # 두 번째 고장(H-브리지 차단): DAB 고장 검출 0.5 ms 뒤(분리 팩은 유지 7, 감발 팩은 램프 8 중)
ASTOP = dict(delay=5e-6, C_A=400e-6)
# (1차 실행, failsafe_run1_pre_detection.json) 두 번째 고장을 DAB 고장 0.6 ms 뒤로 두었다. DAB 고장의 링크 창 검출은 팩에 따라
# 0.62–7.4 ms 걸려(E17), 4사례 중 3사례에서 H-브리지 차단이 DAB 고장 검출보다 먼저였다. 또 주입한 차단을 검출로 기록하지 않아
# 상태기계가 1.2 ms 동안 반응하지 않았다. 의도한 시나리오(docs/24 상태 13: DAB 고장 강등 중 H-브리지 차단)가 아니었으므로
# 시점을 검출 기준으로 바꾸고, 주입한 차단을 비교기 검출로 기록하게 고쳐 다시 실행했다(판정 기준은 그대로).


def dab_det(case, V):
    """DAB 고장(링크 창)의 검출 시각 [s, 고장 기준] — 두 번째 고장 시점을 정하려고 먼저 계산한다."""
    m = E17.r2_run(dict(case=case, V=V, P=P0, event="dab", policy="brk_hold", duration=E17.T_EV + 10e-3, **P3T))
    return m["det_ms"] * 1e-3


def fs_judge(m, tr):
    t, lg = tr["t"], tr["log"]
    t_fs = ev_time(m, "FAILSAFE")
    ref = m.get("t_astop_ms") if m.get("t_astop_ms") is not None else (None if t_fs is None else t_fs - E17.T_EV * 1e3)
    zero_ms = None; held = False
    if ref is not None:
        t1 = E17.T_EV + ref * 1e-3
        w = t >= t1
        ip = np.abs(lg[w, 0]); tw = t[w]
        hi = np.flatnonzero(ip > 1.)
        if len(hi) == 0:
            zero_ms = 0.; held = True
        elif hi[-1] < len(ip) - 1:
            zero_ms = float((tw[hi[-1] + 1] - t1) * 1e3); held = True
    Lw = lg[lg[:, 7] > .5]
    ch = dict(current_100A=max(m["path_peak"], m["bridge_peak"]) <= 100., series_120V=m["series_peak"] <= 120.,
              link_120V=m["vlink_max"] <= 120., class_upper_while_400V_loads=(float(Lw[:, 2].max()) if len(Lw) else 0.) <= E17.E19.CASES[m["case"]]["upper"],
              brake_64J=m["brk_energy_J"] <= BRK_MAX, ip_zero_5ms=bool(held and zero_ms is not None and zero_ms <= 5.))
    return ch, zero_ms


def _run_fs(job):
    tag = job.pop("_tag"); extra = job.pop("_extra")
    m = E17.r2_run(job)
    tr = m.pop("trace")
    ch, zms = fs_judge(m, tr)
    t, lg = tr["t"], tr["log"]
    r = dict(tag=tag, case=m["case"], V=m["V"], P=m["P"], final_state=m["final_state"], events=m["events"], checks=ch,
             pass_=bool(all(ch.values())), path_peak=m["path_peak"], bridge_peak=m["bridge_peak"], series_peak=m["series_peak"],
             vlink_max=m["vlink_max"], brk_energy_J=m["brk_energy_J"], ip_zero_ms=zms, vA_end=m.get("vA_end"),
             vbus_end=float(lg[-1, 2]), vlink_end=float(lg[-1, 4]), t_astop_ms=m.get("t_astop_ms"), **extra)
    w = t >= E17.T_EV
    r["vbus_below_250_ms"] = None
    lo = np.flatnonzero(lg[w, 2] < E17.LOAD_MIN_V - 10)
    if len(lo):
        r["vbus_below_250_ms"] = float((t[w][lo[0]] - E17.T_EV) * 1e3)
    return r


FS_PACKS = (("W460_240s", 930.), ("W460_240s", 1008.), ("W410_spec", 860.), ("W410_spec", 920.))


def failsafe():
    with Pool(workers()) as pool:
        det = dict(zip(FS_PACKS, pool.starmap(dab_det, FS_PACKS)))
    js = []
    for case, V in FS_PACKS:
        t2 = E17.T_EV + det[(case, V)] + T_EV2
        for pn in ("F0", "F1", "F2"):
            j = dict(case=case, V=V, P=P0, event="dab", policy="brk_hold", event2=t2, duration=t2 + 10e-3,
                     keep=True, _tag="%s_%.0f_%s" % (case, V, pn), _extra=dict(pol=pn, dab_det_ms=det[(case, V)] * 1e3,
                                                                                 t2_ms=(t2 - E17.T_EV) * 1e3), **P3T)
            if pn in ("F1", "F2"):
                j.update(sals=sals_cfg(case, MIXES["MX"], SCEN["S5"]), fs_brake=True)
            if pn == "F2":
                j.update(astop=ASTOP)
            js.append(j)
    with Pool(workers()) as pool:
        rows = pool.map(_run_fs, js, chunksize=1)
    for r in rows:
        bad = [k for k, v in r["checks"].items() if not v]
        print("  %-24s %s 링크 최대 %7.1f V, 경로 %6.1f A, 직렬 %6.1f V, 제동 %6.1f J, |i_p| ≤ 1 A까지 %s ms, 버스 끝 %.0f V, V_A 끝 %s %s"
              % (r["tag"], "통과" if r["pass_"] else "불통과", r["vlink_max"], r["path_peak"], r["series_peak"], r["brk_energy_J"],
                 r["ip_zero_ms"], r["vbus_end"], r["vA_end"], bad))
    f2 = [r for r in rows if r["pol"] == "F2"]
    verdict("F2(Stage A 정지 + 부하 차단 + 제동 유지)", all(r["pass_"] for r in f2), "%d/%d" % (sum(r["pass_"] for r in f2), len(f2)))
    save_json(EID, "failsafe", dict(rows=rows, T_EV2_after_detection_ms=T_EV2 * 1e3, ASTOP=ASTOP,
                                    dab_det_ms={"%s_%.0f" % k: v * 1e3 for k, v in det.items()}))


# ---------------------------------------------------------------------------------------------------------------
# regress: 새 인자 없이 이전과 같은가
# ---------------------------------------------------------------------------------------------------------------
def _flat(d, pre=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_flat(v, pre + k + "."))
        elif isinstance(v, (int, float, bool)) or v is None or isinstance(v, str):
            out[pre + k] = v
    return out


def _rerun(job):
    return E17.r2_run(job)


def regress():
    """새 인자(p_c·sals·event2·astop·fs_brake)를 주지 않은 r2_run이 저장 결과와 같은가.
    E21 P3t(H-브리지 개방 930·1008 V), E20 P0(E17 추천 순서, 1008 V), E17 DAB 고장(제동 유지)·켬 각 1건."""
    r21 = load_json("E21", "compare")["rows"]; r20 = load_json("E20", "compare")["rows"]; r17 = load_json("E17", "r2")["rows"]
    pick = lambda rows, f: next(r for r in rows if f(r))
    sel = [("E21", pick(r21, lambda r: r.get("pol_name") == "P3t" and r["case"] == "W460_240s" and r["V"] == 930. and r["t_shed_ms"] == 20.), P3T),
           ("E21", pick(r21, lambda r: r.get("pol_name") == "P3t" and r["case"] == "W410_spec" and r["V"] == 920. and r["t_shed_ms"] == 20.), P3T),
           ("E20", pick(r20, lambda r: r.get("pol_name") == "P0" and r["case"] == "W460_240s" and r["V"] == 1008.), {}),
           ("E17", pick(r17, lambda r: r["event"] == "dab" and r["policy"] == "brk_hold" and r["V"] == 1008. and r["P"] == 25000.
                        and not r.get("tag")), {}),
           ("E17", pick(r17, lambda r: r["event"] == "enable" and r["prep"] == "zero" and not r["start_share"] and r["wait_ms"] == .2
                        and r["P"] == 25000. and r["case"] == "W460_240s"), {})]
    jobs = []
    for src, r, extra in sel:
        j = dict(case=r["case"], V=r["V"], P=r["P"], event=r["event"], damper=r["damper"], vd=r["vd"], **extra)
        if r["event"] == "enable":
            j.update(prep=r["prep"], wait=r["wait_ms"] * 1e-3, start_share=r["start_share"])
        else:
            j.update(policy=r["policy"], close=r["close"])
            if r["t_shed_ms"] != 20.:
                j["t_shed"] = r["t_shed_ms"] * 1e-3
        jobs.append(j)
    with Pool(workers()) as pool:
        new = pool.map(_rerun, jobs, chunksize=1)
    res = []
    for (src, r, _), m in zip(sel, new):
        a, b = _flat(r), _flat(m)
        keys = [k for k in a if k in b and isinstance(a[k], (int, float)) and not isinstance(a[k], bool)]
        diff = max((abs(float(a[k]) - float(b[k])) for k in keys if a[k] is not None and b[k] is not None), default=0.)
        same_ev = r["events"] == [list(e) for e in m["events"]]
        same_pass = r["pass_"] == m["pass_"]
        res.append(dict(src=src, case=r["case"], V=r["V"], event=r["event"], n_keys=len(keys), max_abs_diff=diff, same_events=same_ev,
                        same_pass=same_pass))
        print("  %s %s %.0f V %s: 수치 키 %d개, 최대 차 %.3g, 사건 같음 %s, 판정 같음 %s" % (src, r["case"], r["V"], r["event"], len(keys),
                                                                                diff, same_ev, same_pass))
    ok = verdict("regress", all(x["max_abs_diff"] == 0. and x["same_events"] and x["same_pass"] for x in res), "%d건" % len(res))
    save_json(EID, "regress", dict(rows=res, pass_=ok))


# ---------------------------------------------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------------------------------------------
def figures():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from plotstyle import korean, COLOR
    korean()
    C = dict(COLOR, grey=COLOR["gray"], purple="#7030a0")
    fig = plt.figure(figsize=(13, 11))
    gs = fig.add_gridspec(3, 3, hspace=.45, wspace=.5)
    # (a) 남는 부하 문턱
    ax = fig.add_subplot(gs[0, 0])
    rs = load_json(EID, "resid")
    for case, col in (("W460_240s", C["blue"]), ("W410_spec", C["orange"])):
        rr = sorted([r for r in rs["rows"] if r["case"] == case], key=lambda r: r["p_res"])
        x = [r["p_res"] / 1e3 for r in rr]
        ax.plot(x, [r["deg_ms"] if r["deg_ms"] is not None else np.nan for r in rr], "-o", color=col, ms=4,
                label="%s %.0f V 강등 완료" % (case.split("_")[0].replace("W", "R2-W"), CUR_PACKS[case]))
        for r in rr:
            if not r["pass_"]:
                ax.plot(r["p_res"] / 1e3, (r["deg_ms"] or 40), "x", color=C["red"], ms=8)
        ax.axvline(rs["p_ok"][case] / 1e3 if rs["p_ok"][case] is not None else 0, color=col, ls=":", lw=.8)
    ax.set_xlabel("감발 뒤 남는 부하 [kW]"); ax.set_ylabel("고장 → 강등 완료 [ms]")
    ax.set_title("(a) 남는 부하별 H-브리지 고장 강등(감발 20 ms 계단)\n×: 불통과, 점선: 문턱 P_ok", fontsize=9); ax.legend(fontsize=7)
    # (b)·(c) 대표 연동 사례 시간 궤적: 930 V MX S5(감발 전용), LA(모두 손실 → 접촉기)
    for col_i, (sn, title) in enumerate((("S5", "(b) 930 V·25 kW(M0 9.1 kW), 지연 5 ms"), ("LA", "(c) 같은 조건, 감발 메시지 모두 손실"))):
        case, V = "W460_240s", 930.
        mix = MIXES["MX"]
        m = E17.r2_run(dict(case=case, V=V, P=P0, event="hb_open", policy="clamp_brk", sals=sals_cfg(case, mix, SCEN[sn]),
                            duration=E17.T_EV + T_CUR_MAX + E17.T_SHED + 18e-3, keep=True, **P3T))
        tr = m["trace"]; t = (tr["t"] - E17.T_EV) * 1e3; lg = tr["log"]
        L = rebuild(m["sals"])
        ax = fig.add_subplot(gs[0, 1 + col_i])
        tl = tr["t"]
        conn = lg[:, 7] > .5
        for k, cc, lab in (("comp", C["orange"], "컴프레서(M1)"), ("ptc", C["red"], "PTC(D)"), ("bh", C["purple"], "배터리 히터(D)")):
            ax.plot(t, [L.p_dev(k, x) / 1e3 if c else 0 for x, c in zip(tl, conn)], color=cc, lw=1., label=lab)
        ax.plot(t, [L.power(x, c) / 1e3 for x, c in zip(tl, conn)], color="k", lw=1.4, label="버스 부하 합")
        ax.axhline(i_col(case) * (E17.E19.CASES[case]["upper"] - 2) / 1e3, color=C["grey"], ls=":", lw=.8)
        ax.set_ylabel("부하 전력 [kW]"); ax.set_xlabel("고장 뒤 시간 [ms]"); ax.set_xlim(-1, t[-1])
        ax2 = ax.twinx(); ax2.plot(t, lg[:, 0], color=C["blue"], lw=.8, alpha=.6); ax2.set_ylabel("경로전류 [A]", color=C["blue"])
        ax.set_ylim(-1, 28.5)
        ne = 0
        for e in m["events"]:
            if e[0] in ("HB_COLLAPSE", "SOFT_BYP", "DEGRADED", "fallback_sep", "shed_done", "restore"):
                ax.axvline(e[1] - E17.T_EV * 1e3, color=C["grey"], lw=.6, ls="--")
                ax.text(e[1] - E17.T_EV * 1e3 + .4, 28 - 2.2 * (ne % 4), {"HB_COLLAPSE": "붕괴", "SOFT_BYP": "소프트 투입", "DEGRADED": "강등",
                        "fallback_sep": "분리 명령", "shed_done": "분리 끝", "restore": "되돌림"}[e[0]], fontsize=6.5, va="top")
                ne += 1
        ax.set_title(title, fontsize=9)
        if col_i == 0:
            ax.legend(fontsize=6, loc="center right", framealpha=.9)
    # (d) seq 요약: 유지 시간·제동 에너지
    sq = load_json(EID, "seq")["rows"]
    ax = fig.add_subplot(gs[1, 0])
    sn = list(SCEN)
    for kind, mk in (("cur", "o"), ("sep", "s")):
        for mn, cc in zip(MIXES, (C["blue"], C["green"], C["orange"])):
            rr = [r for r in sq if r["kind"] == kind and r["mix"] == mn and r.get("t_shed_ms", 20.) == 20.]
            for case in CUR_PACKS:
                r2 = [r for r in rr if r["case"] == case]
                ax.plot([sn.index(r["scen"]) + (.1 if case == "W410_spec" else -.1) for r in r2], [r["hold_ms"] or np.nan for r in r2],
                        mk, color=cc, ms=4, mfc="none" if kind == "sep" else cc)
    ax.set_xticks(range(len(sn))); ax.set_xticklabels(sn); ax.set_ylabel("H-브리지 고장 유지(9) [ms]")
    ax.set_title("(d) 유지 시간: ● 감발 전용, □ 분리 팩\n색: MX(파랑)·MD(초록)·ML(주황)", fontsize=9)
    ax = fig.add_subplot(gs[1, 1])
    for kind, mk in (("cur", "o"), ("sep", "s")):
        for mn, cc in zip(MIXES, (C["blue"], C["green"], C["orange"])):
            r2 = [r for r in sq if r["kind"] == kind and r["mix"] == mn and r.get("t_shed_ms", 20.) == 20.]
            ax.plot([sn.index(r["scen"]) for r in r2], [r["brk_energy_J"] for r in r2], mk, color=cc, ms=4, mfc="none" if kind == "sep" else cc)
    ax.axhline(BRK_MAX, color=C["red"], ls="--", lw=.8); ax.text(0, BRK_MAX + 1, "64 J", fontsize=7, color=C["red"])
    ax.set_xticks(range(len(sn))); ax.set_xticklabels(sn); ax.set_ylabel("제동 저항 에너지 [J]")
    ax.set_title("(e) 고장당 제동 저항 에너지", fontsize=9)
    # (f) contract CDF
    ax = fig.add_subplot(gs[1, 2])
    ct = load_json(EID, "contract")
    labs = [("p0.00", "손실 0"), ("p0.05", "5 %"), ("p0.20", "20 %")]
    vals = [[ct["rows"][k][q] for q in ("p50_ms", "p99_ms", "p999_ms", "max_ms")] for k, _ in labs]
    xx = np.arange(4)
    for i, ((k, lab), v) in enumerate(zip(labs, vals)):
        ax.bar(xx + (i - 1) * .25, v, .25, label=lab)
    ax.axhline(T_CUR_MAX * 1e3, color=C["red"], ls="--", lw=.8); ax.axhline(ct["bound_no_loss_ms"], color=C["grey"], ls=":", lw=.8)
    ax.set_xticks(xx); ax.set_xticklabels(["중앙", "99 %", "99.9 %", "최대"]); ax.set_ylabel("감발 완료 [ms]")
    ax.set_title("(f) SALS 감발 완료 시간(M1·D, 몬테카를로)\n점선: 손실 없는 상한 19 ms, 빨강: T_CUR_MAX", fontsize=9); ax.legend(fontsize=7)
    # (g) regen
    ax = fig.add_subplot(gs[2, 0])
    for blk, cc in ((False, C["red"]), (True, C["blue"])):
        mx = {k: RMIX["R1"].get(k, 0.) for k in ("sc", "v2l", "comp", "ptc", "bh")}
        m = E17.r2_run(dict(case="W460_240s", V=930., P=sum(mx.values()), event="hb_open", policy="clamp_brk",
                            sals=sals_cfg("W460_240s", mx, SCEN["S5"], sc_block=blk), duration=E17.T_EV + 15e-3, keep=True, **P3T))
        tr = m["trace"]
        ax.plot((tr["t"] - E17.T_EV) * 1e3, tr["log"][:, 2], color=cc, lw=1., label="Stage C 회생 차단 %s" % ("있음" if blk else "없음"))
    ax.axhline(470, color=C["red"], ls="--", lw=.8); ax.text(.3, 470.6, "B_470 상한", fontsize=7, color=C["red"])
    ax.set_xlabel("고장 뒤 시간 [ms]"); ax.set_ylabel("버스전압 [V]"); ax.legend(fontsize=7, loc="lower right")
    ax.set_xlim(-1, 15)
    ax.set_title("(g) 930 V, 고장 순간 순부하 −3.2 kW(48 V 회생)", fontsize=9)
    # (h)·(i) failsafe
    fsr = load_json(EID, "failsafe")
    for j, (case, V) in enumerate((("W460_240s", 1008.),)):
        axl = fig.add_subplot(gs[2, 1]); axi = fig.add_subplot(gs[2, 2])
        for pn, cc in (("F0", C["red"]), ("F1", C["orange"]), ("F2", C["blue"])):
            t2 = E17.T_EV + dab_det(case, V) + T_EV2
            jj = dict(case=case, V=V, P=P0, event="dab", policy="brk_hold", event2=t2, duration=t2 + 10e-3, keep=True, **P3T)
            if pn in ("F1", "F2"):
                jj.update(sals=sals_cfg(case, MIXES["MX"], SCEN["S5"]), fs_brake=True)
            if pn == "F2":
                jj.update(astop=ASTOP)
            m = E17.r2_run(jj); tr = m["trace"]; t = (tr["t"] - E17.T_EV) * 1e3
            lab = {"F0": "F0 대책 없음", "F1": "F1 제동 유지 + 부하 차단", "F2": "F2 + Stage A 정지"}[pn]
            axl.plot(t, tr["log"][:, 4], color=cc, lw=1., label=lab)
            axi.plot(t, tr["log"][:, 0], color=cc, lw=1., label=lab)
        axl.axhline(120, color=C["grey"], ls="--", lw=.8); axl.set_ylim(0, 260)
        axl.set_xlabel("DAB 고장 뒤 시간 [ms]"); axl.set_ylabel("링크전압 [V]"); axl.legend(fontsize=7)
        axl.set_title("(h) 이중 고장(1008 V·25 kW, DAB 고장 검출 0.5 ms 뒤 H-브리지 차단)", fontsize=9)
        axi.set_xlabel("DAB 고장 뒤 시간 [ms]"); axi.set_ylabel("경로전류 [A]"); axi.legend(fontsize=7)
        axi.set_title("(i) 같은 사례의 경로전류", fontsize=9)
    p = outdir(EID) / "E29_sals_degradation.png"
    fig.savefig(p, dpi=130, bbox_inches="tight"); print("  → 그림:", p)


PARTS = dict(contract=contract, resid=resid, seq=seq, regen=regen, regen_sens=regen_sens, failsafe=failsafe, regress=regress,
             figures=figures)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E29 %s ====" % w)
        PARTS[w]()
