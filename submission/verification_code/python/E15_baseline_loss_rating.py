"""E15 기준 구조 손실·정격 비교(H5 1차 판정).

[목적]
  400±8 V 조정은 외부 요구가 아니라 파생 요구다(요구사항 D1). 그래서 Stage B(직렬 부분전력 조정기)의 가치는
  더 단순한 구조와 같은 조건에서 비교해야만 판정할 수 있다. 이 스크립트는 다섯 구조를 같은 소자 기술, 같은 부하,
  같은 손실 계산 규칙으로 놓고 H5 수락 기준의 세 지표(운전 프로파일 가중 손실, 정격 VA, 반도체 수)를 계산한다.

[비교 구조] (모두 같은 서비스: 400 V급 충전 150 kW·375 A, 400 V 보조부하, 48 V 출력. 48→12 V 강압은 공통이라 제외)
  ①  전전력 승압기(충전 전용, V_bat/2 → V_bat, 150 kW) + 800 → 400 V 보조 강압기(25 kW) + 고정이득 Stage C
  ②  Stage A(2:1 RSC) + 전전력 조정기(V_A → 400 V, 4스위치 벅부스트 25 kW) + 고정이득 Stage C
  ③  PRISM-Hub: Stage A + Stage B(DAB 8 kW + H-브리지, 직렬 보상) + 고정이득 Stage C
  ③′ 창 조정: Stage A + Stage B(V_A > 410 V에서만, 단극성, DAB 5 kW) + 바이패스 스위치 + 버스 RC 감쇠기
      + 조정형 Stage C(입력 319–410 V → 전단 벅부스트 + CLLC)
  ④  비조정: Stage A + 버스 RC 감쇠기 + 조정형 Stage C(입력 319–460 V). 400 V 부하는 B_470 부품

[손실 계산 규칙] (모든 구조에 같게 적용)
  - Stage A: 검증 모델 E1(model_stage_a, 영교차 추종)의 위상별 손실(도통·다이오드·출력용량·게이트)과 V_A 강하를 격자로 계산해 보간
  - 하드 스위칭 변환기: 도통 I_rms²·R_on(고온), 스위칭 에너지는 데이터시트 E_on + E_off를 출력용량 에너지(전류 무관,
    전압^1.5 근사)와 나머지(전압·전류 비례)로 나누어 환산, 데드타임 역도통, 게이트 구동 Q_g·V_g·f
  - 소프트 스위칭(DAB SPS, CLLC): 도통, 턴오프 에너지, 영전압 스위칭 실패 시 출력용량 에너지
  - 자성체: 인덕터 권선 저항은 정격전류에서 정격전력의 0.15 %, 철손 등은 동작 중 정격의 0.1 %로 일정.
    변압기 권선은 정격에서 0.3 %, 철손은 동작 중 정격의 0.2 %로 일정
  - 제어·보조전원: 동작 중인 변환기마다 5 W
  계수는 감도 분석 9종으로 결론의 견고성을 확인한다: 자성체 ×0.5·×2, 스위칭 에너지 ×0.7·×1.5, GaN 전이시간 ×2,
  제어 손실 0, Stage B 비도통 손실 ×0.5, Stage B 도통 손실만(이론 하한), 이전 평균모델의 Stage B 손실 가정(η 0.96·무부하 0)

[지표]
  - 손실: 배터리 → 400 V 부하·48 V 출력까지의 보조 경로 손실을 배터리 전압 분포 × 부하 분포로 가중한 평균[W].
    충전 경로 손실은 150 kW(375 A) 충전에서 따로 계산한다.
  - 정격 VA: 반도체 스위치 VA = Σ(소자 전압 등급 × 정격 운전의 스위치 실효전류) [kVA], 설치 변환기 정격 합[kW]
  - 반도체 수: 스위치 위치 수와 병렬을 포함한 소자 수

[H5 수락 기준] (요구사항 문서, 시험 전에 고정)
  ③이 손실·정격 VA·반도체 수 중 2개 이상에서 ④와 ③′보다 우수하고, 서비스(버스 창, 48 V 품질, 부품 전압 등급)가 동등 이상.

실행: python E15_baseline_loss_rating.py          (Stage A 격자 E1 계산 약 2분, 2코어)
      E15_REUSE_GRID=1 python E15_baseline_loss_rating.py   (저장된 Stage A 격자 재사용, 수 초)
결과: results/E15/stage_a_grid.json, comparison.json, E15_comparison.png

[보고서 수치] (주행 대표 프로파일, 2026-10-22 실행)
  보조 경로 평균 손실 ① 114.6 / ② 123.8 / ③ 133.8 / ③′ 114.1 / ④ 85.0 W
  충전 375 A(800 V) 경로 손실 ① 1.78 kW / ②–④ 0.50 kW
  스위치 위치 수 24 / 44 / 52 / 58 / 44, 스위치 VA 789 / 1,070 / 1,074 / 1,075 / 953 kVA
  H5 지표: ③ vs ④ 0/3, ③ vs ③′ 엄격 2/3(동등범위 3 %에서 1/3) → 불충족
  ③이 손실에서 ④와 같아지는 Stage B 비도통 손실 배율 0.23
"""
import math
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy.optimize import brentq

import model_stage_a as SA
from common import outdir, save_json, workers

# ======================================================================================
# 1. 소자(제조사 데이터시트 값, 접합온도 약 125 °C 기준 도통저항)
# ======================================================================================
DEV = {
    # 1200 V SiC MOSFET, Wolfspeed C3M0016120K: 16 mΩ(25 °C)·29 mΩ(175 °C) → 125 °C 선형 보간 24.7 mΩ.
    # E_on + E_off(바디 다이오드 환류) = 2552 + 788 µJ @ 800 V·80 A·175 °C. 90 A @ T_C 100 °C. Q_g 223 nC.
    # E_oss 127 µJ @ 800 V(스위치 1개의 출력용량 에너지, 켜짐 손실의 전류 무관 부분)
    "SiC1200": dict(V=1200, Ron=0.0247, I100=90., Eref=3340e-6, Vref=800., Iref=80., Eoss=127e-6, Voss=800.,
                    Qg=223e-9, Vg=19., Vsd=4.4, td=100e-9),
    # 750 V SiC FET, onsemi(UnitedSiC) UJ4SC075006K4S: 9.8 mΩ @125 °C. E_total 829 µJ @ 400 V·80 A·150 °C. 120 A. Q_g 164 nC.
    # E_oss 38 µJ @ 400 V
    "SiC750": dict(V=750, Ron=0.0098, I100=120., Eref=829e-6, Vref=400., Iref=80., Eoss=38e-6, Voss=400.,
                   Qg=164e-9, Vg=15., Vsd=1.06, td=100e-9),
    # 650 V GaN, GS66516T: 25 mΩ(25 °C)·65 mΩ(150 °C) → 125 °C 57 mΩ. E_on 134.1 µJ, E_off 17 µJ @ 400 V·20 A. 47 A @ T_C 100 °C.
    # E_oss 17 µJ @ 400 V, C_o(tr) 335 pF, Q_g 14.2 nC
    "GaN650": dict(V=650, Ron=0.057, I100=47., Eref=151.1e-6, Eoff=17e-6, Vref=400., Iref=20., Eoss=17e-6, Voss=400., Ctr=335e-12,
                   Qg=14.2e-9, Vg=6., Vsd=2.5, td=50e-9),
    # 150 V GaN, EPC2305: 2.2 mΩ(25 °C) × 1.5(125 °C, 가정) = 3.3 mΩ. 133 A(T_J ≤ 125 °C) → 열 설계 여유로 90 A 적용.
    # Q_oss 103 nC @ 75 V, C_oss(tr) 1371 pF, Q_g 22 nC. 하드 스위칭 전이시간 t_on 3 ns, t_off 2 ns(가정)
    "GaN150": dict(V=150, Ron=0.0033, I100=90., Qoss75=103e-9, Ctr=1371e-12, Qg=22e-9, Vg=5., Vsd=2.0, td=50e-9,
                   ton=3e-9, toff=2e-9),
}
K = dict(mag_ind_cu=0.0015, mag_ind_core=0.001, mag_tr_cu=0.003, mag_tr_core=0.002, ctrl=5.0, esw=1.0, gan_t=1.0,
         stageB_nc=1.0,   # stageB_nc: Stage B 비도통 손실 배율(감도 분석용, 기본 1)
         stageB_avg=0.0)  # 1이면 Stage B를 평균모델 가정(DAB 방향별 효율 0.96·무부하 손실 0, H-브리지 R_h 2 mΩ)으로 계산


def esw_hard(dev, V, I, n=1):
    """하드 스위칭 한 주기(켜짐 1회 + 꺼짐 1회) 에너지 [J]. n 병렬 소자가 전류를 나눈다."""
    d = DEV[dev]; I = abs(I)
    if dev.startswith("SiC") or dev == "GaN650":
        # 데이터시트 E_on + E_off를 두 부분으로 나눈다: 출력용량 에너지(전류 무관, 전압^1.5 근사)와
        # 나머지 전이 손실(전압·전류에 비례). 경부하에서도 출력용량 손실이 남는 것을 반영한다.
        eoss = d["Eoss"] * (V / d["Voss"]) ** 1.5
        eoss_ref = d["Eoss"] * (d["Vref"] / d["Voss"]) ** 1.5
        return K["esw"] * (n * eoss + (d["Eref"] - eoss_ref) * (V / d["Vref"]) * (I / d["Iref"]))
    # 150 V GaN: 켜짐 = Q_oss(V)·V(출력용량 방전) + ½·V·I·t_on, 꺼짐 = ½·V·I·t_off
    qoss = d["Qoss75"] * math.sqrt(V / 75.)
    return K["esw"] * (n * qoss * V + 0.5 * V * I * (d["ton"] + d["toff"]) * K["gan_t"])


def npar(dev, Ipk):
    return max(1, math.ceil(abs(Ipk) / DEV[dev]["I100"]))


# ======================================================================================
# 2. Stage A — 검증 모델 E1(영교차 추종)
# ======================================================================================
VGRID = np.array([640., 700., 760., 820., 880., 920.])
IGRID = np.array([1., 3., 6., 10., 15., 20., 30., 40., 50.])       # 위상당 평균 출력전류 [A]


def _e1_point(args):
    V, iph, sign = args
    r = SA.sim_array(N=2, Vbat=V, Iload=sign * 2 * iph, Cbus=400e-6, mode="zcp", ncyc=60)
    ph, bus = SA.analyze(r)
    return dict(V=V, iph=iph, sign=sign, ploss_ph=float(np.mean([p["Ploss"] for p in ph])),
                dvA=float(V / 2 - bus["Vbus"]), Ipk=float(np.mean([p["Ipk"] for p in ph])),
                zcs=float(np.max([p["zcs"] for p in ph])))


def stage_a_tables():
    jobs = [(V, i, 1.) for V in VGRID for i in IGRID] + [(V, 375. / 8, -1.) for V in VGRID]
    with ProcessPoolExecutor(workers()) as ex:
        res = list(ex.map(_e1_point, jobs))
    fw = [r for r in res if r["sign"] > 0]
    P = np.array([r["ploss_ph"] for r in fw]).reshape(len(VGRID), len(IGRID))
    D = np.array([r["dvA"] for r in fw]).reshape(len(VGRID), len(IGRID))
    ch = {r["V"]: r for r in res if r["sign"] < 0}
    return dict(P=P, D=D, charge=ch, raw=res)


class StageA:
    """Stage A 손실·V_A 강하(위상당 전류 기준 2차원 보간). 주행 모드는 모듈 1(2위상)."""
    def __init__(self, T):
        self.T = T

    def _interp(self, Z, V, iph):
        iph = min(max(iph, IGRID[0]), IGRID[-1])
        row = np.array([np.interp(iph, IGRID, Z[k]) for k in range(len(VGRID))])   # 1 A 아래는 1 A 값(고정 손실 지배)
        return float(np.interp(V, VGRID, row))

    def drive(self, V, I, nph=2):
        iph = abs(I) / nph
        p = nph * self._interp(self.T["P"], V, iph) + K["ctrl"]
        dv = self._interp(self.T["D"], V, iph) * (iph / max(iph, IGRID[0]))
        return p, V / 2 - math.copysign(dv, I)

    def charge(self, V):
        r = self.T["charge"]
        Vs = np.array(sorted(r)); P = np.array([8 * r[v]["ploss_ph"] for v in Vs])
        return float(np.interp(V, Vs, P)) + 4 * K["ctrl"]


# ======================================================================================
# 3. 하드 스위칭 비절연 변환기(벅, 부스트, 4스위치 벅부스트)
# ======================================================================================
def hs_converter(kind, Vin, Vout, P, dev, f, nph, Prated, Vnom, ripple=0.3):
    """kind: 'buck'(Vin > Vout), 'boost'(Vin < Vout), 'fsbb'(4스위치 벅부스트, 양방향 범위).
    P: 출력전력[W](양수). 반환: 손실[W], 정격 정보 dict(호출 측에서 따로 계산)"""
    if P <= 0:
        return 0.
    d = DEV[dev]
    if kind == "boost" or (kind == "fsbb" and Vin < Vout * 0.98):
        IL = P / Vin / nph; Vsw = Vout; D = 1 - Vin / Vout
        legs = 1; on_path = 1 if kind == "boost" else 2
    elif kind == "buck" or (kind == "fsbb" and Vin > Vout * 1.02):
        IL = P / Vout / nph; Vsw = Vin; D = Vout / Vin
        legs = 1; on_path = 1 if kind == "buck" else 2
    else:                                       # 벅부스트 경계(±2 %): 두 레그 모두 스위칭
        IL = P / Vout / nph; Vsw = max(Vin, Vout); D = 0.5; legs = 2; on_path = 2
    Irated = Prated / Vnom / nph
    dI = ripple * Irated
    n = npar(dev, Irated * (1 + ripple / 2))
    Irms2 = IL ** 2 + dI ** 2 / 12
    Ron = d["Ron"] / n
    p_cond = nph * Irms2 * Ron * on_path
    p_sw = nph * legs * f * esw_hard(dev, Vsw, IL, n)
    p_dead = nph * legs * 2 * d["td"] * f * IL * d["Vsd"]
    p_gate = nph * legs * 2 * n * d["Qg"] * d["Vg"] * f
    Rdcr = K["mag_ind_cu"] * (Prated / nph) / Irated ** 2
    p_ind = nph * Irms2 * Rdcr + K["mag_ind_core"] * Prated
    return p_cond + p_sw + p_dead + p_gate + p_ind + K["ctrl"]


def hs_rating(kind, dev, nph, Prated, Vnom, ripple=0.3, positions_per_phase=None):
    Irated = Prated / Vnom / nph
    n = npar(dev, Irated * (1 + ripple / 2))
    pos = nph * (positions_per_phase or (4 if kind == "fsbb" else 2))
    irms_pos = Irated * math.sqrt(0.5)                         # 한 스위치가 절반 시간 도통(대표값)
    return dict(positions=pos, devices=pos * n, switch_kVA=pos * DEV[dev]["V"] * irms_pos / 1e3, rated_kW=Prated / 1e3,
                magnetics=nph)


# ======================================================================================
# 4. Stage B(③·③′): DAB(SPS) + H-브리지 + L_h
# ======================================================================================
FB = 200e3; LDAB = 11.1e-6; NT = 4.; VLINK = 100.; LH = 5e-6


def dab_wave(Plink, V1=400., V2=400., L=LDAB, f=FB):
    """SPS DAB 1차 누설전류 파형(한 주기). 반환: I_rms, 1차·2차 스위칭 순간 전류(크기), 위상."""
    Pmax = V1 * V2 / (8 * f * L)
    a = min(abs(Plink) / Pmax, 1.)
    phi = math.pi / 2 * (1 - math.sqrt(1 - a)) * (1 if Plink >= 0 else -1)
    T = 1 / f; n = 4000; t = np.arange(n) * T / n
    v1 = np.where(t < T / 2, V1, -V1)
    sh = phi / (2 * math.pi) * T
    v2 = np.where(((t - sh) % T) < T / 2, V2, -V2)
    i = np.cumsum((v1 - v2) / L) * T / n
    i -= i.mean()
    k1 = 0; k2 = int(round((sh % T) / T * n)) % n
    return dict(Irms=float(np.sqrt(np.mean(i ** 2))), Ipk=float(np.max(np.abs(i))), I1=abs(float(i[k1])), I2=abs(float(i[k2])), phi=phi)


def dab_rating(Prated):
    w = dab_wave(Prated)
    np_ = npar("GaN650", w["Ipk"]); ns = npar("GaN150", NT * w["Ipk"])
    return dict(np=np_, ns=ns, Irms_rated=w["Irms"], Ipk=w["Ipk"])


def dab_loss(Plink, Prated):
    """DAB 손실(동작 중이면 링크 전력이 0이어도 철손·출력용량·제어 손실이 있다).
    도통 손실(스위치·권선)과 비도통 손실(철손·스위칭·게이트·제어)을 나누고, 비도통 부분에 K["stageB_nc"]를 곱한다
    (감도 분석에서 0으로 두면 'Stage B 도통 손실만'인 이론 하한이 된다)."""
    if K["stageB_avg"]:
        return (1 / 0.96 - 1) * max(Plink, 0.) + (1 - 0.96) * max(-Plink, 0.)
    R = dab_rating(Prated)
    w = dab_wave(Plink)
    Rw = K["mag_tr_cu"] * Prated / R["Irms_rated"] ** 2
    p_cond = (w["Irms"] ** 2 * 2 * DEV["GaN650"]["Ron"] / R["np"]
              + (NT * w["Irms"]) ** 2 * 2 * DEV["GaN150"]["Ron"] / R["ns"] + w["Irms"] ** 2 * Rw)
    p_nc = K["mag_tr_core"] * Prated
    # 스위칭: 영전압 스위칭이면 턴오프 손실, 전류가 출력용량을 데드타임 안에 충방전하지 못하면 출력용량 에너지 손실
    I1min = 2 * R["np"] * DEV["GaN650"]["Ctr"] * 400. / 100e-9
    I2min = 2 * R["ns"] * DEV["GaN150"]["Ctr"] * VLINK / 100e-9 / NT          # 1차 환산
    if w["I1"] >= I1min:
        p_nc += 4 * FB * DEV["GaN650"]["Eoff"] * (w["I1"] / 20.) * K["esw"]      # 턴오프 에너지(400 V·20 A 값의 전류 비례)
    else:
        p_nc += 4 * FB * R["np"] * DEV["GaN650"]["Eoss"] * K["esw"]
    if w["I2"] >= I2min:
        p_nc += 4 * FB * 0.5 * VLINK * NT * w["I2"] * DEV["GaN150"]["toff"] * K["gan_t"] * K["esw"]
    else:
        p_nc += 4 * FB * R["ns"] * 0.5 * DEV["GaN150"]["Ctr"] * VLINK ** 2 * K["esw"]
    p_nc += 4 * FB * (R["np"] * DEV["GaN650"]["Qg"] * DEV["GaN650"]["Vg"] + R["ns"] * DEV["GaN150"]["Qg"] * DEV["GaN150"]["Vg"])
    p_nc += K["ctrl"]
    return p_cond + K["stageB_nc"] * p_nc


def hbridge_loss(vhb, ih, Iprated=100.):
    """H-브리지(150 V GaN, 유니폴라 PWM 200 kHz) + L_h 손실. vhb: 브리지 평균 출력전압, ih: 필터 직류전류.
    H-브리지는 경로에 직렬이라 직렬전압이 0이어도 경로전류 전체가 흐른다(도통 손실)."""
    if K["stageB_avg"]:
        return 0.002 * ih ** 2
    d = DEV["GaN150"]; n = npar("GaN150", Iprated)
    m = min(abs(vhb) / VLINK, 0.95)
    dI = VLINK * m * (1 - m) / (2 * LH * FB)
    Irms2 = ih ** 2 + dI ** 2 / 12
    Rdcr = K["mag_ind_cu"] * 8000. / 80. ** 2                     # L_h: 정격 8 kW·80 A 기준(설계값 2 mΩ와 같은 크기)
    p_cond = Irms2 * (2 * d["Ron"] / n + Rdcr)
    ion = abs(ih) - dI / 2; ioff = abs(ih) + dI / 2
    if ion > 0:                                   # 전류가 한 방향: 레그마다 하드 켜짐 1회 + 하드 꺼짐 1회
        p_nc = 2 * FB * (n * d["Qoss75"] * math.sqrt(VLINK / 75.) * VLINK
                         + 0.5 * VLINK * (ion * d["ton"] + ioff * d["toff"]) * K["gan_t"]) * K["esw"]
    else:                                         # 리플이 영을 지남: 영전압 전이, 꺼짐 손실만
        p_nc = 2 * FB * 0.5 * VLINK * ioff * d["toff"] * K["gan_t"] * K["esw"]
    p_nc += 2 * 2 * d["td"] * FB * abs(ih) * d["Vsd"]
    p_nc += 4 * n * d["Qg"] * d["Vg"] * FB
    p_nc += K["mag_ind_core"] * 8000.
    return p_cond + K["stageB_nc"] * p_nc


# ======================================================================================
# 5. Stage C: 고정이득 CLLC(TB05 전류), 조정형 = 전단 벅부스트 + CLLC
# ======================================================================================
CP = np.array([0., 300., 1500., 3000.]); CIP = np.array([3.70, 3.894, 5.679, 9.165]); CIS = np.array([0., 7.65, 34.88, 69.33])
CRATED = 3000.


def cllc_loss(Po):
    Ip = float(np.interp(Po, CP, CIP)); Is = float(np.interp(Po, CP, CIS))
    ns = npar("GaN150", 100.)
    p = Ip ** 2 * 2 * DEV["GaN650"]["Ron"] + Is ** 2 * 2 * DEV["GaN150"]["Ron"] / ns
    Rw = K["mag_tr_cu"] * CRATED / CIP[-1] ** 2
    p += Ip ** 2 * Rw + K["mag_tr_core"] * CRATED
    p += 4 * 250e3 * DEV["GaN650"]["Eoff"] * (6.0 / 20.)          # 자화전류(약 6 A)에서 꺼짐, 영전압 켜짐
    p += 4 * 250e3 * (DEV["GaN650"]["Qg"] * 6 + ns * DEV["GaN150"]["Qg"] * 5)
    return p + K["ctrl"]


def stage_c(Vbus, Po, regulated):
    """Stage C 입력전력과 손실. regulated=False면 버스 400 V 고정이득, True면 버스 → 400 V 전단 벅부스트 + CLLC."""
    pc = cllc_loss(Po)
    if not regulated:
        return Po + pc, pc
    pin_cllc = Po + pc
    ppre = hs_converter("fsbb", Vbus, 400., pin_cllc, "GaN650", 100e3, 1, 3300., 400.)
    return pin_cllc + ppre, pc + ppre


# ======================================================================================
# 6. 구조별 보조 경로(배터리 → 400 V 부하 + 48 V 출력)
# ======================================================================================
RW = 0.003           # V_A → 직렬 포트(또는 버스) 배선 3 mΩ
RBYP = 0.0033        # ③′ 바이패스 스위치(150 V GaN 2병렬 역직렬)


def path_struct(name, SAm, V, P400, P48):
    """보조 경로 손실 [W]와 상태(버스전압, 경로전류, 링크전력)를 계산한다."""
    VA0 = V / 2
    if name == "1":
        pin_c, lc = stage_c(400., P48, False)
        P = P400 + pin_c
        lbuck = hs_converter("buck", V, 400., P, "SiC1200", 50e3, 2, 25000., 400.)
        return dict(loss=lbuck + lc, vbus=400., ip=P / 400., plink=0., parts=dict(aux_buck=lbuck, stageC=lc))
    if name == "2":
        pin_c, lc = stage_c(400., P48, False)
        P = P400 + pin_c
        def bal(ip):
            pa, VA = SAm.drive(V, ip)
            lf = hs_converter("fsbb", VA - RW * ip, 400., P, "SiC750", 50e3, 1, 25000., 400.)
            return (VA - RW * ip) * ip - (P + lf)
        ip = brentq(bal, 0., 200.)
        pa, VA = SAm.drive(V, ip)
        lf = hs_converter("fsbb", VA - RW * ip, 400., P, "SiC750", 50e3, 1, 25000., 400.)
        return dict(loss=pa + RW * ip ** 2 + lf + lc, vbus=400., ip=ip, plink=0.,
                    parts=dict(stageA=pa, wire=RW * ip ** 2, regulator=lf, stageC=lc))
    if name in ("3", "3w"):
        target = 400. if name == "3" else 410.
        active = name == "3" or VA0 > target + 0.5
        reg = name == "3w"
        if active:
            Pr = 8000. if name == "3" else 5000.
            def solve(ip):
                pa, VA = SAm.drive(V, ip)
                vbus = target
                pin_c, lc = stage_c(vbus, P48, reg)
                Pbus = P400 + pin_c
                vs = vbus - (VA - RW * ip)
                vhb = vs                                  # (L_h 권선 강하는 H-브리지 손실에 포함)
                lhb = hbridge_loss(vhb, ip)
                plink = vhb * ip + lhb
                ldab = dab_loss(plink, Pr)
                pdab_in = plink + ldab
                return vbus * ip - Pbus - pdab_in, dict(pa=pa, VA=VA, lc=lc, lhb=lhb, plink=plink, ldab=ldab, vs=vs)
            ip = brentq(lambda x: solve(x)[0], 0., 250.)
            s = solve(ip)[1]
            return dict(loss=s["pa"] + RW * ip ** 2 + s["lhb"] + s["ldab"] + s["lc"], vbus=target, ip=ip, plink=s["plink"],
                        vs=s["vs"], parts=dict(stageA=s["pa"], wire=RW * ip ** 2, hbridge=s["lhb"], dab=s["ldab"], stageC=s["lc"]))
        # ③′ 바이패스 구간: Stage B 정지, 경로전류는 바이패스 스위치로
        def bal(ip):
            pa, VA = SAm.drive(V, ip)
            vbus = VA - (RW + RBYP) * ip
            pin_c, lc = stage_c(vbus, P48, True)
            return vbus * ip - (P400 + pin_c)
        ip = brentq(bal, 0., 250.)
        pa, VA = SAm.drive(V, ip)
        vbus = VA - (RW + RBYP) * ip
        pin_c, lc = stage_c(vbus, P48, True)
        return dict(loss=pa + (RW + RBYP) * ip ** 2 + lc, vbus=vbus, ip=ip, plink=0.,
                    parts=dict(stageA=pa, wire=RW * ip ** 2, bypass=RBYP * ip ** 2, stageC=lc))
    if name == "4":
        def bal(ip):
            pa, VA = SAm.drive(V, ip)
            vbus = VA - RW * ip
            pin_c, lc = stage_c(vbus, P48, True)
            return vbus * ip - (P400 + pin_c)
        ip = brentq(bal, 0., 250.)
        pa, VA = SAm.drive(V, ip)
        vbus = VA - RW * ip
        pin_c, lc = stage_c(vbus, P48, True)
        return dict(loss=pa + RW * ip ** 2 + lc, vbus=vbus, ip=ip, plink=0., parts=dict(stageA=pa, wire=RW * ip ** 2, stageC=lc))
    raise ValueError(name)


def charge_loss(name, SAm, V, I=375.):
    """400 V급 충전(충전기 전압 V_bat/2, 375 A)의 충전 경로 손실 [W]."""
    if name == "1":
        P = V / 2 * I
        return hs_converter("boost", V / 2, V, P, "SiC1200", 50e3, 6, 150000., 400.)
    return SAm.charge(V) * (I / 375.) ** 2


# ======================================================================================
# 7. 정격(반도체 수, 스위치 VA, 설치 정격)
# ======================================================================================
def ratings(SAm):
    ipk = max(r["Ipk"] for r in SAm.T["charge"].values())          # 충전 정격(375 A)의 위상 피크 전류(배터리 전압 범위 최댓값)
    A = dict(positions=32, devices=64, switch_kVA=32 * 750 * (ipk / 2) / 1e3, rated_kW=150., magnetics=8)   # E1 설계: 위치당 2병렬
    dr8 = dab_rating(8000.); dr5 = dab_rating(5000.)
    def B(dr, Pr):
        return dict(positions=12, devices=4 * dr["np"] + 4 * dr["ns"] + 4 * npar("GaN150", 100.),
                    switch_kVA=(4 * 650 * dr["Irms_rated"] / math.sqrt(2) + 4 * 150 * NT * dr["Irms_rated"] / math.sqrt(2)
                                + 4 * 150 * 100 / math.sqrt(2)) / 1e3, rated_kW=Pr / 1e3, magnetics=2)
    C = dict(positions=8, devices=4 + 4 * npar("GaN150", 100.), switch_kVA=(4 * 650 * CIP[-1] / math.sqrt(2) + 4 * 150 * CIS[-1] / math.sqrt(2)) / 1e3,
             rated_kW=3., magnetics=1)
    Cpre = hs_rating("fsbb", "GaN650", 1, 3300., 400.)
    byp = dict(positions=2, devices=4, switch_kVA=2 * 150 * 100 / 1e3, rated_kW=0., magnetics=0)
    R = {
        "1": [("booster", hs_rating("boost", "SiC1200", 6, 150000., 400.)), ("aux_buck", hs_rating("buck", "SiC1200", 2, 25000., 400.)), ("stageC", C)],
        "2": [("stageA", A), ("regulator", hs_rating("fsbb", "SiC750", 1, 25000., 400.)), ("stageC", C)],
        "3": [("stageA", A), ("stageB", B(dr8, 8000.)), ("stageC", C)],
        "3w": [("stageA", A), ("stageB", B(dr5, 5000.)), ("bypass", byp), ("stageC", C), ("stageC_pre", Cpre)],
        "4": [("stageA", A), ("stageC", C), ("stageC_pre", Cpre)],
    }
    out = {}
    for k, lst in R.items():
        tot = {m: sum(x[1][m] for x in lst) for m in ("positions", "devices", "switch_kVA", "rated_kW", "magnetics")}
        out[k] = dict(parts={n: v for n, v in lst}, total=tot)
    out["extra"] = {"3w": "버스 RC 감쇠기 C_d 1.6 mF + R_d(바이패스 구간), 바이패스 투입 조건(직렬전압 ≈ 0)",
                    "4": "버스 RC 감쇠기 C_d 1.6 mF + R_d 48.6 mΩ, 400 V 부품 B_470"}
    return out


# ======================================================================================
# 8. 운전 프로파일과 실행
# ======================================================================================
PROFILES = {
    "drive_typ": dict(V=np.linspace(760., 900., 15), w=None, label="주행 대표(배터리 760–900 V 균등, SOC 약 15–90 %)"),
    "uniform":   dict(V=np.linspace(640., 920., 29), w=None, label="전 범위 균등(640–920 V)"),
    "low_soc":   dict(V=np.linspace(640., 780., 15), w=None, label="저 SOC 편중(640–780 V)"),
}
P400 = np.array([0.5, 2.5, 5.5, 10.5, 16.5, 23.0]) * 1e3        # 400 V 부하 [W]
W400 = np.array([0.30, 0.30, 0.20, 0.12, 0.06, 0.02])            # 시간 비율
P48 = 1500.                                                     # 48 V 출력(평균) [W]
STRUCTS = ["1", "2", "3", "3w", "4"]
LABEL = {"1": "① 전전력 승압기 + 보조 강압기", "2": "② Stage A + 전전력 조정기", "3": "③ PRISM-Hub",
         "3w": "③′ 창 조정(≤ 410 V)", "4": "④ 비조정"}


def evaluate(SAm):
    res = {}
    for s in STRUCTS:
        r = {}
        for pk, pr in PROFILES.items():
            L = np.zeros((len(pr["V"]), len(P400)))
            for i, V in enumerate(pr["V"]):
                for j, P in enumerate(P400):
                    L[i, j] = path_struct(s, SAm, V, P, P48)["loss"]
            r[pk] = dict(avg_loss_W=float(np.mean(L @ W400)), by_load_W=(L.mean(0)).tolist())
        r["points"] = {f"{V:.0f}V_{P/1e3:.1f}kW": path_struct(s, SAm, V, P, P48)
                       for V in (640., 800., 920.) for P in (2500., 23000.)}
        r["charge_W"] = {f"{V:.0f}V": charge_loss(s, SAm, V) for V in (640., 700., 800., 900.)}
        res[s] = r
    return res


def judge(res, rat, prof="drive_typ", band=0.0):
    """H5: ③이 ④와 ③′ 각각보다 세 지표 중 2개 이상에서 우수한가.
    band: 동등 범위(상대 차). band=0이면 차이가 조금이라도 있으면 우열을 매기는 엄격 판정,
    band=0.03이면 3 % 안의 차이는 '동등'으로 보아 우수로 세지 않는다(모델 불확도 고려)."""
    m = lambda s: dict(loss=res[s][prof]["avg_loss_W"], kVA=float(rat[s]["total"]["switch_kVA"]),
                       count=int(rat[s]["total"]["positions"]))
    out = {}
    for b in ("4", "3w"):
        a, c = m("3"), m(b)
        wins = {k: bool(a[k] < c[k] * (1 - band)) for k in a}
        loses = {k: bool(a[k] > c[k] * (1 + band)) for k in a}
        n = sum(wins.values())
        out[b] = dict(PRISM=a, baseline=c, wins=wins, loses=loses, n_wins=n, pass_=bool(n >= 2))
    out["H5_metric_pass"] = bool(all(out[b]["pass_"] for b in ("4", "3w")))
    out["band"] = band
    return out


def sensitivity(SAm, base_res):
    """계수 감도: 결론(③ 대 ④·③′ 손실 순위)이 손실 규칙 계수에 얼마나 의존하는가."""
    cases = {"mag_x0.5": dict(mag_ind_cu=0.00075, mag_ind_core=0.0005, mag_tr_cu=0.0015, mag_tr_core=0.001),
             "mag_x2": dict(mag_ind_cu=0.003, mag_ind_core=0.002, mag_tr_cu=0.006, mag_tr_core=0.004),
             "esw_x0.7": dict(esw=0.7), "esw_x1.5": dict(esw=1.5), "gan_t_x2": dict(gan_t=2.0), "ctrl_0W": dict(ctrl=0.0),
             "stageB_nc_x0.5": dict(stageB_nc=0.5),        # Stage B 비도통 손실 절반(경부하 버스트 운전 등 개선 가정)
             "stageB_cond_only": dict(stageB_nc=0.0),      # Stage B 도통 손실만(도달 불가능한 이론 하한)
             "stageB_avgmodel": dict(stageB_avg=1.0)}      # 이전 평균모델의 Stage B 손실 가정(η 0.96, 무부하 손실 0)
    base = dict(K)
    out = {}
    for name, ch in cases.items():
        K.update(ch)
        row = {}
        for s in STRUCTS:
            pr = PROFILES["drive_typ"]
            L = np.array([[path_struct(s, SAm, V, P, P48)["loss"] for P in P400] for V in pr["V"]])
            row[s] = float(np.mean(L @ W400))
        out[name] = row
        K.clear(); K.update(base)
    return out


def breakeven(SAm, prof="drive_typ"):
    """③의 평균 손실이 ④와 같아지는 Stage B 비도통 손실 배율(1 = 기본 모델). Stage B 개선 목표의 크기를 보여 준다."""
    pr = PROFILES[prof]
    def avg(s):
        L = np.array([[path_struct(s, SAm, V, P, P48)["loss"] for P in P400] for V in pr["V"]])
        return float(np.mean(L @ W400))
    L4 = avg("4")
    def f(x):
        K["stageB_nc"] = x
        return avg("3") - L4
    try:
        x0 = brentq(f, 0., 1.)
    finally:
        K["stageB_nc"] = 1.0
    return dict(stageB_nc_breakeven=x0, loss_4_W=L4)


def figure(res, rat, outpath):
    from plotstyle import korean, COLOR as C
    plt = korean()
    lab = ["①", "②", "③", "③′", "④"]
    col = [C["gray"], C["green"], C["blue"], "#8faadc", C["orange"]]
    x = np.arange(len(STRUCTS))
    fig, ax = plt.subplots(1, 4, figsize=(15, 3.9))
    # (a) 프로파일 가중 평균 손실
    wdt = 0.26
    for k, (pk, hatch) in enumerate(zip(["drive_typ", "uniform", "low_soc"], ["", "//", ".."])):
        ax[0].bar(x + (k - 1) * wdt, [res[s][pk]["avg_loss_W"] for s in STRUCTS], wdt, color=col, hatch=hatch,
                  edgecolor="white", label=PROFILES[pk]["label"].split("(")[0])
    ax[0].set_xticks(x, lab); ax[0].set_ylabel("보조 경로 평균 손실 [W]")
    ax[0].set_title("(a) 운전 프로파일 가중 손실"); ax[0].set_ylim(0, 175); ax[0].legend(loc="upper center", ncol=3, fontsize=7)
    # (b) 부하별 손실(주행 대표 전압 분포 평균)
    for s, c, l in zip(STRUCTS, col, lab):
        ax[1].plot(P400 / 1e3, res[s]["drive_typ"]["by_load_W"], "o-", color=c, label=l, ms=4)
    ax[1].set_xlabel("400 V 부하 [kW] (48 V 출력 1.5 kW 별도)"); ax[1].set_ylabel("손실 [W]")
    ax[1].set_title("(b) 부하별 손실(배터리 760–900 V 평균)"); ax[1].legend(ncol=2)
    # (c) 충전 경로 손실
    ax[2].bar(x, [res[s]["charge_W"]["800V"] / 1e3 for s in STRUCTS], 0.55, color=col)
    for xi, s in zip(x, STRUCTS):
        ax[2].text(xi, res[s]["charge_W"]["800V"] / 1e3 + 0.03, "%.2f" % (res[s]["charge_W"]["800V"] / 1e3), ha="center", fontsize=8)
    ax[2].set_xticks(x, lab); ax[2].set_ylabel("충전 경로 손실 [kW]")
    ax[2].set_title("(c) 충전 375 A(배터리 800 V, 150 kW)")
    # (d) 반도체 수와 스위치 VA
    a2b = ax[3].twinx()
    ax[3].bar(x - 0.18, [rat[s]["total"]["positions"] for s in STRUCTS], 0.36, color=C["blue"], label="스위치 위치 수")
    a2b.bar(x + 0.18, [rat[s]["total"]["switch_kVA"] for s in STRUCTS], 0.36, color=C["orange"], label="스위치 VA")
    a2b.grid(False)
    ax[3].set_xticks(x, lab); ax[3].set_ylabel("스위치 위치 수"); a2b.set_ylabel("스위치 VA [kVA]")
    ax[3].set_title("(d) 반도체 수와 스위치 VA")
    h1, l1 = ax[3].get_legend_handles_labels(); h2, l2 = a2b.get_legend_handles_labels()
    ax[3].set_ylim(0, 80); a2b.set_ylim(0, 1500)
    ax[3].legend(h1 + h2, l1 + l2, loc="upper center", ncol=2)
    fig.tight_layout(); fig.savefig(outpath); plt.close(fig)


def main():
    import os
    from common import load_json
    if os.environ.get("E15_REUSE_GRID") == "1" and (outdir("E15") / "stage_a_grid.json").exists():
        g = load_json("E15", "stage_a_grid")             # 같은 E1 격자를 다시 계산하지 않을 때(감도 분석 반복용)
        T = dict(P=np.array(g["P_phase"]), D=np.array(g["dvA"]), charge={float(k): v for k, v in g["charge"].items()})
        print("E15 Stage A 격자: 저장된 E1 결과 재사용")
    else:
        print("E15 Stage A 격자(E1, 영교차 추종) 계산 ...")
        T = stage_a_tables()
        save_json("E15", "stage_a_grid", dict(V=VGRID, I=IGRID, P_phase=T["P"], dvA=T["D"],
                                              charge={str(k): v for k, v in T["charge"].items()},
                                              zcs_max_drive=max(r["zcs"] for r in T["raw"] if r["sign"] > 0)))
    SAm = StageA(T)
    res = evaluate(SAm)
    rat = ratings(SAm)
    jd = judge(res, rat)
    jd_band = judge(res, rat, band=0.03)
    sens = sensitivity(SAm, res)
    jd_prof = {pk: judge(res, rat, pk) for pk in PROFILES}
    rank = {k: sorted(STRUCTS, key=lambda s: v[s]) for k, v in sens.items()}
    be = breakeven(SAm)
    save_json("E15", "comparison", dict(results=res, ratings=rat, judge=jd, judge_band3=jd_band, judge_by_profile=jd_prof,
                                         sensitivity=sens, sensitivity_rank=rank, breakeven=be,
                                         coefficients=K, devices=DEV, profiles={k: dict(V=v["V"], label=v["label"]) for k, v in PROFILES.items()},
                                         load_P400_W=P400, load_weights=W400, P48_W=P48))
    figure(res, rat, outdir("E15") / "E15_comparison.png")
    print("\n구조   주행 대표   균등   저SOC | 충전 800 V | 위치 | 소자 | 스위치 VA | 설치 정격")
    for s in STRUCTS:
        print("%-4s %9.1f %7.1f %7.1f | %8.0f W | %4d | %4d | %6.0f kVA | %6.1f kW" % (
            s, res[s]["drive_typ"]["avg_loss_W"], res[s]["uniform"]["avg_loss_W"], res[s]["low_soc"]["avg_loss_W"],
            res[s]["charge_W"]["800V"], rat[s]["total"]["positions"], rat[s]["total"]["devices"], rat[s]["total"]["switch_kVA"],
            rat[s]["total"]["rated_kW"]))
    for tag, j in (("엄격", jd), ("동등범위 3 %", jd_band)):
        for b in ("4", "3w"):
            print("[%s] ③ vs %s: 우수 %s, 열세 %s → %s" % (tag, b, j[b]["wins"], j[b]["loses"], "통과" if j[b]["pass_"] else "불통과"))
        print("[%s] H5 지표 기준(주행 대표 프로파일): %s" % (tag, "충족" if j["H5_metric_pass"] else "불충족"))
    print("프로파일별:", {pk: v["H5_metric_pass"] for pk, v in jd_prof.items()})
    print("③ = ④ 손익분기 Stage B 비도통 손실 배율: %.3f" % be["stageB_nc_breakeven"])
    print("감도(주행 대표 평균 손실 W, 손실 순위):")
    for k, v in sens.items():
        print("  %-17s " % k + "  ".join("%s %.1f" % (s, v[s]) for s in STRUCTS) + "   순위 " + " < ".join(rank[k]))


if __name__ == "__main__":
    main()
