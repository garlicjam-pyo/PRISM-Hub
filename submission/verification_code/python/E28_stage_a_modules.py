"""[E28] Stage A 4모듈(8위상) 경부하 운전: 모듈 관리기 + 모듈별 위상 셰딩 + 부품 공차.

■ 목적
  E24(docs/29)는 Stage A 모듈 하나(위상 2개)만 계산했다. 실제 Stage A는 모듈 4개다. 주행 중 보조부하(수–100 A)는 모듈
  하나나 둘이면 되고, 400–500 V급 충전(375 A)에는 넷이 모두 필요하다. 이 시험은
  (1) 동작 모듈 수를 정하는 문턱을 손실과 위상 정격으로 정하고(design),
  (2) 모듈 관리기와 모듈별 위상 셰딩을 함께 켠 정상 운전점 격자를 공차 표본과 함께 판정하며(static),
  (3) 부하 계단·램프, 충전 시작·종료(사전 기동 있음·없음), 역방향 경부하를 지나는 과도를 판정하고(transient),
  (4) 멈춰 있던 모듈이 다시 시작할 때 플라잉 커패시터 전압 오차가 얼마까지 괜찮은지 정하며(restart),
  (4′) 공차 표본마다 정격 충전점(375 A, 4모듈)의 위상 첨두를 계산해 첨두 기준값으로 쓰고 부품 정격 표의 입력으로 남기며(rated),
  (5) 기존 모델 경로가 바뀌지 않았는지 확인한다(regress).
  회로 확인은 TB22다.
  게이트(최종): 무장하지 못한 반주기는 부호 없이 |i| < i_thr가 검출 지연만큼 이어지면 블랭킹 뒤 끈다(unarmed_stop='mag').
  1차 실행은 E27의 방식('nom': 공칭 도통시간에 끔)이었다(아래 ■ 실행 경과).

■ 왜 필요한가
  - 모듈 넷을 경부하에서 모두 돌리면 모듈당 전류가 작아 영전류 스위칭 비율이 나빠지고(E24: 2위상 10 A에서 5.5 %),
    위상당 고정 손실(약 15.6 W)이 여덟 번 든다. 모듈을 줄이면 남은 모듈이 부하 증가를 받는다.
  - 충전기 전류는 3.75 A/µs로 375 A까지 오른다(모듈당 0.94 A/µs). 모듈 하나가 이 램프를 받으면 정격(위상 첨두 76.4 A)을
    넘는다(E24 사례 E). 그래서 충전 전 모듈을 미리 켜야 하는지, 켜지 못했을 때 관리기가 따라가는지 확인해야 한다.
  - 공진 L·C가 위상마다 다르면 모듈 사이 분담과 위상 하나 운전의 첨두가 바뀐다. 문턱은 공칭값으로 정했다.
  - 멈춘 모듈의 플라잉 커패시터는 오래 쉬는 동안 균형 회로가 정한 전압에 머문다. 이 전압이 운전 중 평균(V_bat/2)과
    다르면 재시작 첫 펄스 전류는 오차/특성 임피던스(√(L/C) = 0.136 Ω)만큼 커진다(1 V당 약 7.4 A).

■ 모듈 관리기(model_stage_a.mgr_step, 회로 ctrl/prism_gate_stageA_zcpm.m과 같은 논리)
  전체 출력전류 I(위상 출력전류의 합, 1차 필터 τ_m = 20 µs, 변경 (4))로 모듈 수를 정한다. 모듈 m은 위상 2m·2m+1이다.
  - 추가(바로): 충전 요청 → 모든 모듈. |I| > 동작 수 × Im_up 또는 동작 위상 순시 |i| > Ipk_m → max(동작 수 + 1, ⌈|I|/Im_up⌉).
    더한 뒤 t_lock 동안은 다음 추가를 하지 않는다(새 모듈이 분담을 받기 전에 연달아 더하지 않도록).
  - 시작 유지: Stage A 시작 뒤 t_hold(100 µs) 동안은 모듈 수를 바꾸지 않는다. static 1차 실행(유지 없음)에서 공진전류 0에서
    시작하는 과도의 전체 전류 넘침(60 A 부하에서 필터 전류 80 A)으로 모듈을 더해 S3가 불통과했다. 기준은 그대로 두고
    설계에 시작 유지를 넣어 다시 실행했다(1차 결과 static_run1_nohold.json).
  - 줄임(지속 뒤): 충전 요청이 없고 ⌈|I|/Im_dn⌉ < 동작 수가 t_dwell_m 이어지면 그 수로 줄인다. 줄인 모듈의 위상은
    지금 구간을 자연 턴오프로 끝낸 뒤 멈춘다(영전류). 번호가 큰 모듈부터 줄이고 모듈 1은 늘 동작한다.
  - 동작 모듈마다 E24와 같은 위상 셰딩(I_off 15 A·100 µs, I_on 22 A, I_pk,on 36 A, 복귀는 바로).

■ 실행 경과(기준은 바꾸지 않았다. 1·2차 결과는 *_run1*.json, static_run2_hold.json으로 남김)
  1차(시작 유지 없음, 줄일 때 남는 모듈 그대로, 게이트 'nom'):
    static: S3 불통과 48/96(60·90·130·160 A, 시작 과도의 전체 전류 넘침으로 모듈을 하나 더함)
    transient: 공칭 4/7, 공차 12/21. (T4) 시작 과도로 모듈 추가(MD·MG), 640 V 충전 종료 뒤 4 → 1로 줄이자마자 남은 모듈
      (위상 하나 운전 중)이 전류를 받으며 넘쳐 다시 추가(MD). (T1) 무장하지 못한 반주기(첨두 1.0–2.45 A)를 공칭 도통시간에
      끈 턴오프 1.01–1.24 A(공진주파수 −3.3 % 위상, 모듈 재시작·충전기 램프 직후의 비대칭 펄스). (T2) MF(사전 기동 없음) 80.3 A
  설계 변경 3가지: (1) 시작 유지 t_hold 100 µs, (2) 모듈을 줄일 때 남는 모듈을 두 위상으로, (3) 무장 전 부호 없는 영교차 검출
  ('mag'). (3)은 E24·E27 결과를 바꿀 수 있어 regress에 (G2)·(G3)을 더했다.
  2차(위 세 변경): static S3 불통과 24/96(60·130 A). 시작 유지가 끝난 뒤에도 모듈 수 판단 필터(τ 2 µs)가 위상 펄스 리플을
    거르지 못해 60 A 평균에서 50–75 A로 흔들렸다(130 A는 101–160 A). 또 S4가 −375 A(정격 충전점)에서 불통과였는데, 1차부터
    같았다: S4의 첨두를 0.1 ms 이후 전체에서 재어 공진전류 0에서 시작하는 시작 과도(82.1 A)가 들어간다(P_rated는 정상 20주기
    첨두 76.5 A). 판정 창은 바꾸지 않고 불통과로 둔다. 정상 창(마지막 10주기) 첨두는 정보로 함께 남긴다(pk_steady).
  설계 변경 1가지: (4) 모듈 수 판단용 전체 전류 필터를 따로 두고 τ_m = 20 µs(위상 셰딩용 모듈 전류 필터는 2 µs 그대로).
  3차: 네 변경을 모두 넣은 최종 설계(이 파일의 MGR, GATE).

■ 판정 기준(시험 전에 고정. design으로 문턱을 정한 뒤, rated·static·transient·restart 실행 전에 정함)
  첨두 기준 P_rated(표본) = 같은 공차 표본의 정격 충전점(V_A 노드 375 A 주입, 4모듈 8위상 전부 켬, 640·800·920 V) 위상 첨두
  최댓값. design에서 공칭 모듈 93.75 A(위상 46.875 A)의 첨두가 76.6 A로, E24의 76.4 A(위상 하나 단독 46.875 A)보다 0.2 A
  컸다. 공차 표본은 분담이 달라 정격점 첨두 자체가 커진다. 그래서 "모듈 관리·셰딩이 같은 하드웨어의 정격점보다 큰 첨두를
  만들지 않는다"를 기준으로 하고, 정격점 첨두의 공차 영향은 부품 정격 표(검증 과제 5)로 넘긴다.
  static  (S1) 동작 모듈 출력 |I_m| ≥ 7.5 A: 그 모듈 위상의 턴오프 전류/피크 ≤ 5 %(마지막 10주기, E24와 같은 정의)
          (S2) |I_m| < 7.5 A: 턴오프 순간 전류 ≤ 1.0 A
          (S3) 동작 모듈 수가 규칙의 기대값(주행 ⌈|I|/Im_up⌉, 충전 4)이고 운전 중 바뀌지 않음,
               모듈별 위상 수가 기대값(공칭 모듈 전류 |I/N| < 15 A면 하나, 아니면 둘)
          (S4) 위상 첨두 ≤ P_rated(표본)
          (정보) 모듈 분담: 동작 모듈 평균전류의 최대/평균
  transient(0.3 ms 이후)
          (T1) 모든 턴오프: |i_off| ≤ max(5 % × 그 반주기 첨두, 1.0 A)
          (T2) 위상 첨두 ≤ P_rated(표본)
          (T3) V_A 최저·최고가 같은 프로파일·공차의 전부 켬(8위상, 셰딩 없음)과 1.0 V 안
               (모듈 하나의 출력저항이 넷의 네 배라 정상 차만 70 A에서 0.54 V다. E24의 0.5 V보다 넓게 잡는다)
          (T4) 모듈 수: 끝 동작 수가 기대값, 추가·줄임 횟수가 사례별 상한 이하, 멈추던 모듈의 취소 0
  restart  판정이 아니라 설계값을 정한다: 재시작 모듈의 (T1)·(T2)를 모든 배터리 전압에서 지키는 플라잉 커패시터
           전압 오차의 범위 → 정지 모듈 균형 회로의 요구 정확도
  regress  (G) 관리기를 쓰지 않는 경로(mgr=None, 이전 게이트)는 이전과 같다: E24 과도 사례 F·H와 E27 repro('nom', 시작 +0)의
           지표가 저장된 결과와 같음(차 ≤ 1e-9)
           (G2) 새 게이트('mag')로 E27 repro(시작 6가지 + 공차)·stress(48사례): 모든 턴오프 ≤ max(5 %·첨두, 1 A)
           (G3) 새 게이트로 E24 static 26점·transient 10사례(모듈 하나, 셰딩): 판정이 저장된 결과와 같음

■ 실행   python E28_stage_a_modules.py design rated static transient restart regress figures   (2코어 약 70분)
■ 결과   results/E28/design.json, rated.json, static.json, transient.json, restart.json, regress.json, E28_stage_a_modules.png
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import model_stage_a as A
import E24_stage_a_shedding as E24
from common import save_json, verdict, outdir, workers

EID = "E28"
T = 1 / A.FR0
CA = 400e-6
DF = True
GATE = "mag"                               # 무장 전 부호 없는 영교차 검출(1차 실행은 E27의 'nom')
RATED_PK = E24.RATED_PK                    # 76.4 A
I_ABS = 1.0
I_LOW = 7.5
TOL = dict(C=0.05, L=0.10, R=0.10)         # E1·E27과 같은 공차
SEEDS = (None, 1, 2, 3)                    # 공칭 + 공차 표본 3개(matlab_rng 시드)
BUS = dict(E24.BUS)                        # R2 버스(배선 3 mΩ·1.5 µH, C_b 400 µF, 감쇠기 48.6 mΩ + 1.6 mF)
RA1 = 10.2e-3                              # 모듈 하나의 출력저항(버스 초기값 계산용)

# 모듈 관리기 설계값(design에서 정함, 근거는 design() 출력과 docs/34)
MGR = dict(I_off=15., I_on=22., Ipk_on=36., tau=2e-6, t_dwell=100e-6,            # 위상 셰딩(E24와 같음)
           Im_up=70., Im_dn=60., Ipk_m=66., t_dwell_m=1e-3, t_lock=20e-6,         # 모듈 관리
           t_hold=100e-6,    # 시작 유지: static 1차 실행(유지 없음)에서 시작 과도로 모듈을 더해 S3 불통과 → 추가(docs/34)
           tau_m=20e-6)      # 모듈 수 판단용 필터: static 2차 실행(τ 2 µs)에서 위상 펄스 리플로 60 A 평균이 75 A까지 흔들려 추가

DES_V = (540., 800., 1008.)
DES_I = (5., 7.5, 10., 15., 20., 25., 30., 40., 50., 60., 70., 80., 93.75)       # 모듈 출력전류 [A]


def _tol(seed):
    return (TOL, A.matlab_rng(seed)) if seed else (None, None)


# ---------------------------------------------------------------- rated: 공차 표본별 정격점 위상 첨두(첨두 기준)
RATED_V = (640., 800., 920.)


def _rated(args):
    V, seed = args
    tol, rs = _tol(seed)
    r = A.sim_array(N=8, Vbat=V, Iload=-375., Cbus=CA, mode="zcp", ncyc=80, tol=tol, rs=rs, dead_fix=DF, unarmed_stop=GATE)
    ph, bus = A.analyze(r, ncyc_last=20)
    return dict(V=V, seed=seed, Ipk=max(p["Ipk"] for p in ph), Iavg=[p["Iavg"] for p in ph], zcs=max(p["zcs"] for p in ph))


def rated():
    jobs = [(V, s) for s in SEEDS for V in RATED_V]
    with Pool(workers()) as p:
        rows = p.map(_rated, jobs)
    pr = {}
    for s in SEEDS:
        rr = [x for x in rows if x["seed"] == s]
        pr[str(s)] = max(x["Ipk"] for x in rr)
        ia = np.abs(np.array(rr[1]["Iavg"]))
        print("  공차 %-4s: 정격점 위상 첨두 %s → P_rated %.1f A, 위상 평균전류 최대/평균 %.3f(800 V)"
              % (s, ["%.1f" % x["Ipk"] for x in rr], pr[str(s)], ia.max() / ia.mean()))
    save_json(EID, "rated", dict(rows=rows, P_rated=pr))


def p_rated(seed):
    return json.loads((outdir(EID) / "rated.json").read_text(encoding="utf-8"))["P_rated"][str(seed)]


# ---------------------------------------------------------------- design: 모듈 수 문턱
def _des(args):
    V, I = args
    r = A.sim_array(N=2, Vbat=V, Iload=I, Cbus=CA, mode="zcp", ncyc=60, dead_fix=DF, unarmed_stop=GATE)
    ph, bus = A.analyze(r, ncyc_last=10)
    return dict(V=V, I=I, loss=sum(p["Ploss"] for p in ph), Ipk=max(p["Ipk"] for p in ph), zcs=max(p["zcs"] for p in ph))


def design():
    """모듈 하나(2위상)의 손실·위상 첨두를 모듈 전류의 함수로 계산하고, N개 모듈이 같은 전류를 나눌 때의 배열 손실
    N·P(I/N)로 모듈 수 사이의 손실 교차점을 구한다(위상 셰딩은 넣지 않은 2위상 값, 경부하 쪽은 E24가 따로 다룸)."""
    jobs = [(V, I) for V in DES_V for I in DES_I]
    with Pool(workers()) as p:
        rows = p.map(_des, jobs)
    out = dict(rows=rows, mgr=MGR, cross={}, pk_at_up={})
    for V in DES_V:
        rr = sorted([r for r in rows if r["V"] == V], key=lambda r: r["I"])
        Ig = np.array([r["I"] for r in rr]); Pg = np.array([r["loss"] for r in rr]); Kg = np.array([r["Ipk"] for r in rr])
        P = lambda I: float(np.interp(I, Ig, Pg))
        cr = []
        for N in (1, 2, 3):                               # N ↔ N+1 교차: N·P(I/N) = (N+1)·P(I/(N+1))
            II = np.linspace(N * 20., min(N * 93.75, 375.), 2000)
            d = np.array([N * P(I / N) - (N + 1) * P(I / (N + 1)) for I in II])
            j = np.where(np.diff(np.sign(d)) > 0)[0]
            cr.append(float(II[j[0]]) if len(j) else None)
        out["cross"][V] = cr
        out["pk_at_up"][V] = float(np.interp(MGR["Im_up"], Ig, Kg))
        print("  %4.0f V: 모듈 전류 [A] / 손실 [W] / 위상 첨두 [A] / 턴오프 비율" % V)
        for r in rr:
            print("     %6.2f  %6.1f  %5.1f  %5.2f %%" % (r["I"], r["loss"], r["Ipk"], 100 * r["zcs"]))
        print("    손실 교차(전체 전류): 1↔2 %s, 2↔3 %s, 3↔4 %s A / Im_up(%.0f A)에서 위상 첨두 %.1f A"
              % (*["%.0f" % c if c else "–" for c in cr], MGR["Im_up"], out["pk_at_up"][V]))
    pk_up = max(out["pk_at_up"].values())
    cr_min = [min(out["cross"][V][N] for V in DES_V) for N in range(3)]
    up = [MGR["Im_up"] * N for N in (1, 2, 3)]; dn = [MGR["Im_dn"] * N for N in (1, 2, 3)]
    # (D1) 추가 문턱의 위상 첨두가 순시 추가 문턱보다 작다(정상 운전에서 순시 추가가 걸리지 않음), 순시 문턱 < 정격 첨두
    d1 = pk_up < MGR["Ipk_m"] < RATED_PK
    # (D2) 줄임 문턱(N+1 → N)이 손실 교차보다 작다(줄인 쪽이 손실이 작거나 같은 곳에서만 줄임)
    d2 = all(dn[N] <= cr_min[N] for N in range(3))
    print("  선택: Im_up %.0f A(추가 1→2·2→3·3→4 = %s A), Im_dn %.0f A(줄임 2→1·3→2·4→3 = %s A), Ipk_m %.0f A, 지속 %.1f ms, "
          "추가 뒤 막음 %.0f µs" % (MGR["Im_up"], up, MGR["Im_dn"], dn, MGR["Ipk_m"], MGR["t_dwell_m"] * 1e3, MGR["t_lock"] * 1e6))
    verdict("(D1) Im_up의 정상 위상 첨두 < Ipk_m < 위상 정격 첨두", d1, "%.1f < %.0f < %.1f A" % (pk_up, MGR["Ipk_m"], RATED_PK))
    verdict("(D2) 줄임 문턱 ≤ 손실 교차(모든 배터리 전압)", d2, "줄임 %s, 교차 최소 %s A" % (dn, ["%.0f" % c for c in cr_min]))
    out.update(D1=d1, D2=d2, up=up, dn=dn, cross_min=cr_min, pk_up=pk_up)
    save_json(EID, "design", out)


# ---------------------------------------------------------------- static: 정상 운전점 × 공차
ST_DRIVE_V = (540., 800., 1008.)
ST_DRIVE_I = (3., 10., 30., 60., 90., 130., 160., 220.)      # V_A 노드 부하(주행 방향)
ST_CHG_V = (640., 800., 920.)
ST_CHG_I = (-30., -120., -250., -375.)                      # V_A 노드 주입(충전 방향), 충전 요청 켬


def expect_static(I, chg):
    n = 4 if chg else max(1, int(np.ceil(abs(I) / MGR["Im_up"])))
    nph = 1 if abs(I / n) < MGR["I_off"] else 2
    return n, nph


def _static(args):
    V, I, chg, seed = args
    tol, rs = _tol(seed)
    r = A.sim_array(N=8, Vbat=V, Iload=I, Cbus=CA, mode="zcp", ncyc=int(0.6e-3 / T), tol=tol, rs=rs, dead_fix=DF,
                    unarmed_stop=GATE, mgr=MGR, chg=(0., 1.) if chg else None)
    tl = r["t"][-1] - 10 * T
    w = r["t"] > tl
    n_exp, nph_exp = expect_static(I, chg)
    to = E24.turnoffs(r, tl)
    mods = []
    ok = True
    for m in range(4):
        act = [k for k in (2 * m, 2 * m + 1) if np.any(r["st"][w, k] != 0)]
        if not act:
            continue
        Im = float(r["io"][w][:, 2 * m:2 * m + 2].sum(axis=1).mean())
        tm = [x for x in to if x[0] in act]
        zr = max(abs(x[2]) / x[3] for x in tm); za = max(abs(x[2]) for x in tm)
        okm = (zr <= 0.05) if abs(Im) >= I_LOW else (za <= I_ABS)
        mods.append(dict(m=m, phases=len(act), I=Im, zcs=zr, ioff_max=za, ok=okm))
        ok &= okm
    na = r["nact"]
    s3 = (int(na[-1]) == n_exp and np.all(na == na[0]) and len(mods) == n_exp and all(x["phases"] == nph_exp for x in mods))
    pk = float(np.abs(r["i"][r["t"] > 0.1e-3]).max())
    Im = [x["I"] for x in mods]
    share = max(np.abs(Im)) / np.mean(np.abs(Im)) if len(Im) > 1 else 1.0
    pk_st = float(np.abs(r["i"][w]).max())                      # (정보) 정상 창(마지막 10주기) 첨두
    L = dict(S12=bool(ok), S3=bool(s3), S4=pk <= p_rated(seed))
    return dict(V=V, I=I, chg=chg, seed=seed, n_exp=n_exp, nph_exp=nph_exp, nact=int(na[-1]), mods=mods, phase_peak=pk, pk_steady=pk_st,
                share=share, limits=L, passed=all(L.values()))


def static():
    jobs = [(V, I, False, s) for V in ST_DRIVE_V for I in ST_DRIVE_I for s in SEEDS] + \
           [(V, I, True, s) for V in ST_CHG_V for I in ST_CHG_I for s in SEEDS]
    with Pool(workers()) as p:
        rows = p.map(_static, jobs)
    for x in rows:
        if x["seed"] is None or not x["passed"]:
            print("  %4.0f V %7.1f A %s 공차 %s: 모듈 %d(기대 %d), 위상/모듈 %s, 비율 최대 %.2f %%, 턴오프 최대 %.2f A, 첨두 %.1f A, "
                  "분담 %.3f, %s" % (x["V"], x["I"], "충전" if x["chg"] else "주행", x["seed"], x["nact"], x["n_exp"],
                                    [m["phases"] for m in x["mods"]], 100 * max(m["zcs"] for m in x["mods"]),
                                    max(m["ioff_max"] for m in x["mods"]), x["phase_peak"], x["share"],
                                    "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v])))
    tolr = [x for x in rows if x["seed"]]
    print("  공차 표본: 분담 최대 %.3f, 첨두 최대 %.1f A, 비율 최대 %.2f %%"
          % (max(x["share"] for x in tolr), max(x["phase_peak"] for x in tolr),
             100 * max(m["zcs"] for x in tolr for m in x["mods"] if abs(m["I"]) >= I_LOW)))
    verdict("(static) 공칭: S1·S2 턴오프, S3 모듈·위상 수, S4 위상 첨두", all(x["passed"] for x in rows if x["seed"] is None),
            "%d/%d" % (sum(x["passed"] for x in rows if x["seed"] is None), sum(1 for x in rows if x["seed"] is None)))
    verdict("(static) 공차 표본 3개: 같은 기준", all(x["passed"] for x in tolr),
            "%d/%d" % (sum(x["passed"] for x in tolr), len(tolr)))
    save_json(EID, "static", dict(rows=rows, mgr=MGR))


# ---------------------------------------------------------------- transient: 사례(시험 전에 고정)
#   prof: V_A 노드 전류원(양수 = 부하, 음수 = 충전기 주입), bus: R2 버스 뒤 정전력 부하 [W], chg: 충전 요청 구간
#   n_end: 끝 동작 모듈 수, add_max·rem_max: 모듈 추가·줄임 횟수 상한
STEP = lambda a, b, t1, t2, tr=1e-9: ([0, t1, t1 + tr, t2, t2 + tr, 1], [a, a, b, b, a, a])
CHG_PROF = ([0, 0.5e-3, 0.6e-3, 1.3e-3, 1.4e-3, 1], [0, 0, -375., -375., 0, 0])     # 3.75 A/µs, 100 µs 램프
CASES = {
    "MA_540V_bus_5_25_5kW": dict(V=540., prof=0., bus=STEP(5e3, 25e3, 0.5e-3, 1.5e-3), tend=2.9e-3, n_end=1, add_max=1, rem_max=1),
    "MB_800V_bus_ramp_2_36_2kW": dict(V=800., prof=0., bus=([0, .3e-3, 1.3e-3, 1.8e-3, 2.8e-3, 1], [2e3, 2e3, 36e3, 36e3, 2e3, 2e3]),
                                      tend=3.6e-3, n_end=1, add_max=1, rem_max=1),
    "MC_800V_charge_prestart": dict(V=800., prof=CHG_PROF, bus=([0, 1], [15e3, 15e3]), chg=(0.4e-3, 1.45e-3), tend=2.8e-3,
                                    n_end=1, add_max=1, rem_max=1),
    "MD_640V_charge_prestart": dict(V=640., prof=CHG_PROF, bus=([0, 1], [15e3, 15e3]), chg=(0.4e-3, 1.45e-3), tend=2.8e-3,
                                    n_end=1, add_max=1, rem_max=1),
    "ME_920V_charge_prestart": dict(V=920., prof=CHG_PROF, bus=([0, 1], [15e3, 15e3]), chg=(0.4e-3, 1.45e-3), tend=2.8e-3,
                                    n_end=1, add_max=1, rem_max=1),
    "MF_800V_charge_no_prestart": dict(V=800., prof=CHG_PROF, bus=([0, 1], [15e3, 15e3]), tend=2.8e-3, n_end=1, add_max=3, rem_max=1),
    "MG_1008V_bus_25_5_25kW": dict(V=1008., prof=0., bus=STEP(25e3, 5e3, 0.5e-3, 1.5e-3), tend=2.0e-3, n_end=1, add_max=0, rem_max=0),
}


def run_case(name, seed=None, ref=False):
    """ref=True: 같은 프로파일·공차로 8위상 전부 켬(관리기·셰딩 없음)."""
    c = CASES[name]
    tol, rs = _tol(seed)
    P0 = c["bus"][1][0]
    n0 = 4 if ref else max(1, int(np.ceil((P0 / (c["V"] / 2) + (c["prof"] if np.isscalar(c["prof"]) else c["prof"][1][0]))
                                           / MGR["Im_up"])))
    bus = dict(BUS, RA=RA1 / n0, P=c["bus"])
    return A.sim_array(N=8, Vbat=c["V"], Iload=c["prof"], Cbus=CA, mode="zcp", ncyc=int(c["tend"] / T), tol=tol, rs=rs,
                       bus=bus, dead_fix=DF, unarmed_stop=GATE, mgr=None if ref else MGR, chg=None if ref else c.get("chg"))


def case_metrics(name, r, b, seed=None):
    """과도 사례 판정(T1–T4). r = 관리기 켬, b = 전부 켬(같은 프로파일·공차). TB22 기준값도 이 함수로 만든다."""
    c = CASES[name]
    t = r["t"]; w = t > 0.3e-3
    to = E24.turnoffs(r, 0.3e-3)
    bad = [x for x in to if abs(x[2]) > max(0.05 * x[3], I_ABS)]
    pk = float(np.abs(r["i"][w]).max()); pkb = float(np.abs(b["i"][w]).max())
    vmin, vmax = float(r["vb"][w].min()), float(r["vb"][w].max())
    bmin, bmax = float(b["vb"][w].min()), float(b["vb"][w].max())
    na = r["nact"].astype(int); ch = np.where(np.diff(na) != 0)[0]
    ev = [(round(float(t[k + 1]) * 1e3, 4), int(na[k + 1])) for k in ch]
    n_add = sum(1 for k in ch if na[k + 1] > na[k]); n_rem = sum(1 for k in ch if na[k + 1] < na[k])
    pev = {}
    for m in range(4):
        mm = r["mm"][:, m].astype(int); cm = np.where(np.diff(mm) != 0)[0]
        pev[m] = [(round(float(t[k + 1]) * 1e3, 4), int(mm[k + 1])) for k in cm]
    L = dict(T1=len(bad) == 0, T2=pk <= p_rated(seed), T3=abs(vmin - bmin) <= 1.0 and abs(vmax - bmax) <= 1.0,
             T4=int(na[-1]) == c["n_end"] and n_add <= c["add_max"] and n_rem <= c["rem_max"] and r["n_mcancel"] == 0)
    tob = E24.turnoffs(b, 0.3e-3)
    badb = [x for x in tob if abs(x[2]) > max(0.05 * x[3], I_ABS)]
    worst = max(to, key=lambda x: abs(x[2]) - max(0.05 * x[3], I_ABS))
    return dict(case=name, V=c["V"], limits=L, passed=all(L.values()), P_rated=p_rated(seed), events=ev, n_add=n_add, n_rem=n_rem,
                n_mcancel=int(r["n_mcancel"]), n_pcancel=int(r["n_pcancel"]), phase_events=pev,
                n_turnoff=len(to), n_bad=len(bad), worst=dict(phase=worst[0], t_ms=worst[1] * 1e3, i_off=worst[2], pk=worst[3]),
                ioff_max=max(abs(x[2]) for x in to), phase_peak=pk, phase_peak_ref=pkb, vA=[vmin, vmax], vA_ref=[bmin, bmax],
                n_bad_ref=len(badb), ioff_max_ref=max(abs(x[2]) for x in tob))


def _transient(args):
    name, seed = args
    m = case_metrics(name, run_case(name, seed), run_case(name, seed, ref=True), seed)
    m["seed"] = seed
    return m


def transient():
    jobs = [(n, s) for n in CASES for s in SEEDS]
    with Pool(workers()) as p:
        res = p.map(_transient, jobs)
    for x in res:
        print("  %-28s 공차 %-4s %s  모듈 수 %s(추가 %d, 줄임 %d, 취소 %d)"
              % (x["case"], x["seed"], "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v]),
                 x["events"], x["n_add"], x["n_rem"], x["n_mcancel"]))
        print("      턴오프 %d번 중 위반 %d(전부 켬 %d), 최대 %.2f A, 위상 첨두 %.1f A(전부 켬 %.1f A), V_A %.2f–%.2f V(전부 켬 %.2f–%.2f V)"
              % (x["n_turnoff"], x["n_bad"], x["n_bad_ref"], x["ioff_max"], x["phase_peak"], x["phase_peak_ref"],
                 x["vA"][0], x["vA"][1], x["vA_ref"][0], x["vA_ref"][1]))
    nom = [x for x in res if x["seed"] is None]; tl = [x for x in res if x["seed"]]
    verdict("(transient) 공칭 7사례: T1 턴오프, T2 위상 첨두, T3 V_A, T4 모듈 수", all(x["passed"] for x in nom),
            "%d/%d" % (sum(x["passed"] for x in nom), len(nom)))
    verdict("(transient) 공차 표본 3개 × 7사례: 같은 기준", all(x["passed"] for x in tl), "%d/%d" % (sum(x["passed"] for x in tl), len(tl)))
    save_json(EID, "transient", dict(cases=res, mgr=MGR, rated_pk=RATED_PK))


# ---------------------------------------------------------------- restart: 멈춘 모듈의 플라잉 커패시터 전압 오차
RS_V = (540., 800., 1008.)
RS_DV = (-15., -10., -5., -2., 0., 2., 5., 10., 15.)


def _restart(args):
    V, dv = args
    prof = ([0, 0.25e-3, 0.26e-3, 1], [60., 60., 85., 85.])     # 모듈 하나 60 A → 85 A(> Im_up): 모듈 2 재시작
    vc0 = np.array([V / 2] * 2 + [V / 2 + dv] * 2 + [V / 2] * 4)
    r = A.sim_array(N=8, Vbat=V, Iload=prof, Cbus=CA, mode="zcp", ncyc=int(0.45e-3 / T), vC0=vc0, dead_fix=DF,
                    unarmed_stop=GATE, mgr=dict(MGR, n0=1))
    na = r["nact"]; k2 = int(np.argmax(na >= 2))
    t2 = float(r["t"][k2])
    to = E24.turnoffs(r, 0.2e-3)
    bad = [x for x in to if abs(x[2]) > max(0.05 * x[3], I_ABS)]
    w = r["t"] > t2
    pk2 = float(np.abs(r["i"][w][:, 2:4]).max()); pk = float(np.abs(r["i"][r["t"] > 0.2e-3]).max())
    first = []
    for k in (2, 3):                                            # 재시작 위상의 첫 반주기 첨두
        s = r["st"][:, k].astype(int); i = r["i"][:, k]
        on = np.where((s[:-1] == 0) & (s[1:] != 0))[0] + 1; on = on[on > k2]
        if len(on) >= 2:
            first.append(float(np.abs(i[on[0]:on[1]]).max()))
    return dict(V=V, dv=dv, t_restart_ms=t2 * 1e3, n_bad=len(bad), ioff_max=max(abs(x[2]) for x in to), phase_peak=pk,
                peak_restart=pk2, first_pulse=max(first) if first else None, ok=len(bad) == 0 and pk <= p_rated(None))


def restart():
    jobs = [(V, dv) for V in RS_V for dv in RS_DV]
    with Pool(workers()) as p:
        rows = p.map(_restart, jobs)
    for x in rows:
        print("  %4.0f V ΔvC %+5.1f V: 재시작 %.4f ms, 첫 반주기 첨두 %.1f A, 재시작 위상 첨두 %.1f A, 전체 첨두 %.1f A, 턴오프 최대 %.2f A, "
              "위반 %d → %s" % (x["V"], x["dv"], x["t_restart_ms"], x["first_pulse"] or 0, x["peak_restart"], x["phase_peak"],
                               x["ioff_max"], x["n_bad"], "통과" if x["ok"] else "불통과"))
    okdv = [dv for dv in RS_DV if all(x["ok"] for x in rows if x["dv"] == dv)]
    lim = None
    for a in sorted(set(abs(d) for d in RS_DV)):
        if all(d in okdv for d in RS_DV if abs(d) <= a):
            lim = a
    slope = np.polyfit([x["dv"] for x in rows if x["V"] == 800. and x["dv"] > 0],
                       [x["first_pulse"] for x in rows if x["V"] == 800. and x["dv"] > 0], 1)[0]
    win = [min(okdv), max(okdv)] if okdv else None
    print("  T1·T2를 모든 전압에서 지키는 |ΔvC| 범위: ≤ %s V(격자), 통과한 ΔvC: %s V(구간 %s V)" % (lim, okdv, win))
    save_json(EID, "restart", dict(rows=rows, dv_ok=lim, dv_pass=okdv, dv_window=win, slope_800=slope, mgr=MGR))


# ---------------------------------------------------------------- regress: 관리기를 쓰지 않는 경로
def _reg(job):
    kind, name = job
    if kind == "E24":
        c = E24.CASES[name]
        return kind, name, E24.case_metrics(name, E24.run_case(name, True), E24.run_case(name, False))
    import E27_zcp_reversal as E27
    return kind, name, E27._repro(("nom", 0., False))


def regress():
    root = Path(__file__).resolve().parents[3] / "validation"
    old24 = json.loads((root / "2026-10-26-stage-a-shedding" / "E24" / "transient.json").read_text(encoding="utf-8"))
    old27 = json.loads((root / "2026-10-27-zcp-reversal" / "E27" / "repro.json").read_text(encoding="utf-8"))
    jobs = [("E24", "F_1008V_bus_25_5_25kW"), ("E24", "H_1008V_bus5kW_charger_74A"), ("E27", "nom0")]
    with Pool(workers()) as p:
        res = p.map(_reg, jobs)
    rows = []
    for kind, name, m in res:
        if kind == "E24":
            o = next(x for x in old24["cases"] if x["case"] == name)
            keys = ("phase_peak", "phase_peak_noshed", "ioff_max", "n_turnoff")
            d = max(abs(float(m[k]) - float(o[k])) for k in keys)
            d = max(d, max(abs(a - b) for a, b in zip(m["vA"], o["vA"])))
        else:
            o = next(x for x in old27["rows"] if x["gate"] == "nom" and x["off"] == 0. and not x["tol"])
            keys = ("n", "n_bad", "n_unarmed", "ioff_max", "ioff_unarmed_max")
            d = max(abs(float(m[k]) - float(o[k])) for k in keys)
        rows.append(dict(kind=kind, case=name, max_diff=d))
        print("  %s %s: 저장된 결과와 최대 차 %.3g" % (kind, name, d))
    g = all(x["max_diff"] <= 1e-9 for x in rows)
    verdict("(G) 관리기를 쓰지 않는 경로가 E24·E27 저장 결과와 같다", g, "최대 차 %.3g" % max(x["max_diff"] for x in rows))
    # (G2) 새 게이트로 E27 방향 반전
    import E27_zcp_reversal as E27
    j27 = [("rep", (GATE, off, False)) for off in E27.D_OFFS] + [("rep", (GATE, 0., True))] + \
          [("st", (GATE, V, sl, d, sd)) for V in E27.ST_V for sl in E27.ST_SLOPE for d in E27.ST_DIR for sd in E27.ST_TOL]
    with Pool(workers()) as p:
        r27 = p.map(_g2, j27)
    n_bad = sum(x["n_bad"] for x in r27)
    print("  (G2) E27 %d사례: 위반 %d, 턴오프 최대 %.2f A, 무장 못 한 반주기 턴오프 최대 %.2f A"
          % (len(r27), n_bad, max(x["ioff_max"] for x in r27), max(x["ioff_unarmed_max"] for x in r27)))
    g2 = n_bad == 0
    verdict("(G2) 새 게이트: E27 repro·stress 모든 턴오프 ≤ max(5 %·첨두, 1 A)", g2, "위반 %d" % n_bad)
    # (G3) 새 게이트로 E24 정상·과도 판정
    old24s = json.loads((root / "2026-10-26-stage-a-shedding" / "E24" / "static.json").read_text(encoding="utf-8"))
    with Pool(workers()) as p:
        s24 = p.map(_g3s, list(E24.STATIC_I))
        t24 = p.map(_g3t, list(E24.CASES))
    rows3 = []
    for d in s24:
        for V, x in d.items():
            o = next(y for y in old24s["rows"] if y["V"] == V and y["I"] == x["I"])
            rows3.append(dict(kind="static", key="%.0fV %.2fA" % (V, x["I"]), ok_new=x["ok"], ok_old=o["ok"], zcs_new=x["zcs"],
                              zcs_old=o["zcs"], ioff_new=x["ioff_max"], ioff_old=o["ioff_max"]))
    for m in t24:
        o = next(y for y in old24["cases"] if y["case"] == m["case"])
        rows3.append(dict(kind="transient", key=m["case"], ok_new=m["passed"], ok_old=o["passed"], pk_new=m["phase_peak"],
                          pk_old=o["phase_peak"], ioff_new=m["ioff_max"], ioff_old=o["ioff_max"]))
    for x in rows3:
        if x["ok_new"] != x["ok_old"] or x["kind"] == "transient":
            print("  (G3) %-9s %-28s 판정 %s → %s, 턴오프 최대 %.2f → %.2f A"
                  % (x["kind"], x["key"], x["ok_old"], x["ok_new"], x["ioff_old"], x["ioff_new"]))
    g3 = all(x["ok_new"] == x["ok_old"] for x in rows3)
    verdict("(G3) 새 게이트: E24 static 26점·transient 10사례 판정이 저장된 결과와 같다", g3,
            "%d/%d 같음" % (sum(x["ok_new"] == x["ok_old"] for x in rows3), len(rows3)))
    save_json(EID, "regress", dict(rows=rows, G=g, G2=g2, e27=r27, G3=g3, e24=rows3, gate=GATE))


def _g2(job):
    import E27_zcp_reversal as E27
    kind, a = job
    return E27._repro(a) if kind == "rep" else E27._stress(a)


def _g3s(I):
    """E24._static과 같은 계산(새 게이트)."""
    out = {}
    for V in E24.DESIGN_V:
        r = A.sim_array(N=2, Vbat=V, Iload=I, Cbus=E24.CA, mode="zcp", ncyc=int(0.6e-3 / T), shed=E24.SHED, dead_fix=DF,
                        unarmed_stop=GATE)
        tl = r["t"][-1] - 10 * T
        to = E24.turnoffs(r, tl)
        zr = max(abs(x[2]) / x[3] for x in to); za = max(abs(x[2]) for x in to)
        out[V] = dict(I=I, zcs=zr, ioff_max=za, ok=(zr <= 0.05) if abs(I) >= E24.I_LOW else (za <= E24.I_ABS))
    return out


def _g3t(name):
    """E24 과도 사례(새 게이트, 셰딩 켬·없음)."""
    c = E24.CASES[name]
    bus = dict(E24.BUS, P=c["bus"]) if "bus" in c else None
    run = lambda sh: A.sim_array(N=2, Vbat=c["V"], Iload=c["prof"], Cbus=E24.CA, mode="zcp", ncyc=int(c["tend"] / T),
                                 shed=E24.SHED if sh else None, bus=bus, dead_fix=DF, unarmed_stop=GATE)
    return E24.case_metrics(name, run(True), run(False))


# ---------------------------------------------------------------- figures
def figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    D = json.loads((outdir(EID) / "design.json").read_text(encoding="utf-8"))
    R = json.loads((outdir(EID) / "restart.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(2, 2, figsize=(13, 8.5))
    rr = sorted([r for r in D["rows"] if r["V"] == 800.], key=lambda r: r["I"])
    Ig = np.array([r["I"] for r in rr]); Pg = np.array([r["loss"] for r in rr])
    II = np.linspace(5, 375, 400)
    cols = [C["blue"], C["red"], C["green"], "0.3"]
    for N in (1, 2, 3, 4):
        m = II <= N * 93.75
        ax[0, 0].plot(II[m], [N * np.interp(I / N, Ig, Pg) for I in II[m]], color=cols[N - 1], label="모듈 %d개" % N)
    for x in D["up"]:
        ax[0, 0].axvline(x, color="k", ls=":", lw=0.8)
    for x in D["dn"]:
        ax[0, 0].axvline(x, color="0.5", ls="--", lw=0.8)
    ax[0, 0].set_xlabel("Stage A 전체 출력전류 [A]"); ax[0, 0].set_ylabel("Stage A 손실 추정 [W]")
    ax[0, 0].set_title("(a) 모듈 수별 손실(800 V, 2위상). 점선 추가 문턱, 파선 줄임 문턱", fontsize=9); ax[0, 0].legend(fontsize=7)
    for V, ls in ((540., "--"), (800., "-"), (1008., ":")):
        rv = sorted([r for r in D["rows"] if r["V"] == V], key=lambda r: r["I"])
        ax[0, 1].plot([r["I"] for r in rv], [r["Ipk"] for r in rv], ls, color=C["blue"], marker="o", ms=3, label="%.0f V" % V)
    ax[0, 1].axhline(RATED_PK, color="k", ls=":"); ax[0, 1].axhline(MGR["Ipk_m"], color=C["red"], ls="--")
    ax[0, 1].axvline(MGR["Im_up"], color="0.5", ls="--")
    ax[0, 1].set_xlabel("모듈 출력전류 [A]"); ax[0, 1].set_ylabel("위상 첨두 [A]")
    ax[0, 1].set_title("(b) 위상 첨두(점선 정격 76.4 A, 붉은 파선 순시 추가 문턱)", fontsize=9); ax[0, 1].legend(fontsize=7)
    r = run_case("MC_800V_charge_prestart")
    t = r["t"] * 1e3
    for k in range(8):
        ax[1, 0].plot(t, r["i"][:, k], lw=0.3, color=cols[k // 2])
    a2 = ax[1, 0].twinx(); a2.plot(t, r["nact"], color="k", lw=1.2); a2.set_ylabel("동작 모듈 수"); a2.set_ylim(0, 4.5)
    ax[1, 0].axhline(RATED_PK, color="k", ls=":"); ax[1, 0].axhline(-RATED_PK, color="k", ls=":")
    ax[1, 0].set_xlabel("시간 [ms]"); ax[1, 0].set_ylabel("위상 공진전류 [A]")
    ax[1, 0].set_title("(c) 800 V 충전 시작·종료(사전 기동), 색 = 모듈", fontsize=9)
    rv = sorted([x for x in R["rows"] if x["V"] == 800.], key=lambda x: x["dv"])     # 540·1008 V도 같은 값
    ax[1, 1].plot([x["dv"] for x in rv], [x["peak_restart"] for x in rv], marker="o", color=C["blue"], label="재시작 모듈 위상 첨두")
    ax[1, 1].plot([x["dv"] for x in rv], [x["phase_peak"] for x in rv], marker="s", ls="--", color=C["red"], label="전체 위상 첨두")
    for x in rv:
        if x["n_bad"]:
            ax[1, 1].annotate("턴오프 위반 %d" % x["n_bad"], (x["dv"], x["phase_peak"]), fontsize=7, xytext=(4, 4),
                              textcoords="offset points")
    ax[1, 1].axhline(p_rated(None), color="k", ls=":")
    ax[1, 1].axvspan(-10, 0, color=C["green"], alpha=0.08)
    ax[1, 1].set_xlabel("재시작 모듈의 플라잉 커패시터 전압 오차 ΔvC [V]"); ax[1, 1].set_ylabel("위상 첨두 [A]")
    ax[1, 1].set_title("(d) 모듈 재시작(모듈 하나 60 → 85 A, 800 V). 점선 P_rated, 녹색 띠 T1·T2 통과", fontsize=9)
    ax[1, 1].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(outdir(EID) / "E28_stage_a_modules.png", dpi=150); plt.close(fig)
    print("  figures saved")


PARTS = dict(design=design, rated=rated, static=static, transient=transient, restart=restart, regress=regress, figures=figures)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E28 %s ====" % w)
        PARTS[w]()
