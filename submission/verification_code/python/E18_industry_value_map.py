"""[E18] 산업 적용 가치 지도: 배터리 팩 등급별 구조 성립성·손실·정격과 개선 구조 R2의 Stage B 크기.

■ 목적
  E15는 이 프로젝트의 사양(배터리 640–920 V)에서 Stage B의 400 V 조정이 손실·정격 이점을 주지 못함을 보였다(H5 기각).
  그러나 그 결론은 한 팩 등급에 대한 것이다. 산업 적용 범위를 정하려면 실제 차량의 팩 등급(셀 직렬수)과 400 V
  보조부품의 전압 등급(ISO 21498-1 B_420·B_470)에 따라 (1) 어떤 구조가 성립하고, (2) 성립하는 구조 가운데 무엇이
  손실·정격에서 나은지, (3) Stage A가 500 V급 충전기와 어디까지 호환되는지를 같은 규칙으로 계산해야 한다.
  이 스크립트는 그 '가치 지도'를 만들고, 개선 구조 R2의 창 조정 Stage B가 필요한 팩 등급과 그 크기를 정한다.

■ 왜 필요한가
  - 800 V급 팩(약 192–200s)은 V_bat/2가 420 V 이하라 조정 없이 400 V급 부품을 쓸 수 있다.
  - 900–1000 V급 팩(Lucid Gravity 926 V, BYD 1000 V 플랫폼)은 V_bat/2가 470 V를 넘어 비조정 구조(④)가 성립하지 않는다.
  - 500 V급 충전기(Tesla V3, 구형 CCS) 호환은 800 V 이상 차량의 공통 과제이며, 이 구조에서는 Stage A가 맡는다.
  Stage B가 가치를 갖는 조건과 Stage A의 충전 호환 범위를 수치로 보여야 아키텍처의 적용 범위를 정할 수 있다.

■ 비교 구조(E15와 같은 소자·손실 규칙, 48→12 V는 공통이라 제외)
  ①   전전력 승압기(충전) + 보조 강압기(V_bat → 400 V) + 고정이득 Stage C
  ②   Stage A + 전전력 조정기(4스위치 벅부스트, V_A → 400 V) + 고정이득 Stage C
  ③   PRISM-Hub 기준선: Stage A + Stage B(±90 V 직렬, 400 V 조정) + 고정이득 Stage C
  R2-W410 / R2-W460: Stage A + 창 조정 Stage B(V_A > V_W에서만 동작, 그 아래는 바이패스) + 조정형 Stage C.
       V_W 410 V는 B_420 부품용(E15의 ③′와 같은 구조), 460 V는 B_470 부품용. DAB 권선비는 V_W/100으로 맞추고
       누설 인덕턴스는 (V_W/400)²배로 두어 400 V 설계와 같은 위상·전류 비를 쓴다. DAB 정격은 정적 최대 링크전력의
       1.8배를 0.5 kW 단위로 올린 값. 1.8은 E19에서 Tier-2(1↔25 kW) 과도의 포화 없는 DAB 전력 첨두가 정적 최대의
       1.77배(R2-W460, 240s)·1.78배(R2-W410, 사양, E13 공차 포함)였던 데서 정했다. 처음 쓴 1.25배(③의 8/6.44)는
       E19에서 Tier-2 최대 배터리 전압 사례가 DAB 정격에 포화되어 포트 판정을 넘었으므로 버렸다
  ④ = R2 기본형: Stage A + 조정형 Stage C, 버스 = V_A(버스 RC 감쇠기)

■ 팩 등급과 운전 프로파일
  셀 직렬수 180·192·200·216·224·240s. 운전 범위 셀 3.0–4.2 V, 주행 프로파일은 셀 3.47–4.11 V 균등(E15 주행 대표
  760–900 V를 219s 등가 팩으로 환산). 400 V 부하 분포와 48 V 1.5 kW는 E15와 같다. 별도로 이 프로젝트의 사양
  (640–920 V)을 E15 프로파일 그대로 다시 계산해 E15 결과가 재현되는지 확인한다.

■ 성립 조건(계산 전에 고정)
  - 버스 창: 정적 운전점(배터리 운전 범위 25점 × 부하 −3.2·0·25 kW)의 버스가 [260 V, 부품 등급 상한] 안
  - 조정 구간의 정상점이 Stage B 포트 한계 안(model_stage_b.steady_feasible: 직렬 ±90 V, 변조율 0.95, 링크 80 A·DAB 정격)
  - 창 조정 기준 V_W ≤ 상한 − 10 V(Tier-2 상향 과도 여유)
  - 소자 직류 전압 사용률 ≤ 80 %(1200 V SiC ≤ 960 V, 750 V SiC ≤ 600 V, 650 V GaN ≤ 520 V)
■ 지표
  주행 프로파일 가중 보조 경로 평균 손실, 충전 375 A 경로 손실, 스위치 위치 수·스위치 VA, 인덕터 저장에너지
  (½·L·I_pk², 정격 전류의 30 % 리플 규칙, 공통인 Stage C CLLC 공진 L과 변압기 자화 에너지는 제외),
  창 조정 Stage B의 동작 구간·정격·주행 중 동작 비율
  500 V 충전기 호환: Stage A 375 A(8위상)에서 충전 가능한 최대 셀 전압, 셀 3.7 V에서의 충전전력,
  150·225 kW에 필요한 위상 수와 충전 경로 손실

■ 실행   python E18_industry_value_map.py              (Stage A 추가 격자 E1 계산 약 1분, 2코어)
         E18_REUSE_GRID=1 python E18_industry_value_map.py   (저장된 격자 재사용)
■ 결과   results/E18/stage_a_grid_ext.json, value_map.json, E18_value_map.png

■ 한계
  E15와 같은 설계 단계 추정이다(대표 소자, 자성체 비율 규칙, 열·기생 성분 제외). 성립성은 정적 운전점 기준이며
  과도 판정은 E19에서 따로 한다. ①의 1200 V SiC 사용률이 80 %를 넘는 팩에서는 상위 등급 소자의 손실 자료가 없어
  손실은 1200 V 소자 값으로 참고 표시만 하고 성립 구조에서 뺀다.
"""
import math
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np

import E15_baseline_loss_rating as B
from model_stage_b import steady_feasible
from controller_reference import NOMINAL
from common import outdir, save_json, load_json, workers

# ======================================================================================
# 1. 조건(계산 전에 고정)
# ======================================================================================
CELLS = [180, 192, 200, 216, 224, 240]           # 셀 직렬수
V_CELL = (3.0, 4.2)                              # 운전 범위 셀 전압 [V]
V_CELL_DRIVE = (3.47, 4.11)                      # 주행 프로파일(E15 760–900 V ÷ 219.05s)
CLASSES = {"B_420": 420., "B_470": 470.}         # ISO 21498-1 전압 하위등급 상한
LOAD_MIN_V = 260.                                # 조사한 400 V 부하 입력 하한의 최댓값(E4)
P_STATIC = [-3200., 0., 25000.]                  # 정적 성립성 부하점 [W]
UTIL_MAX = 0.8                                   # 소자 직류 전압 사용률 상한
WINDOW = {"W410": 410., "W460": 460.}            # 창 조정 기준
W_MARGIN = 10.                                   # V_W ≤ 상한 − 10 V
DAB_TRANSIENT = 1.8                              # DAB 정격 / 정적 최대 링크전력(E19 Tier-2 과도 첨두 비 1.77–1.78)
SPEC_V = (640., 920.)                            # 이 프로젝트의 사양(E15)
CHARGER_VMAX = 500.                              # 500 V급 충전기 최대 전압
I_CH = 375.                                      # Stage A 충전 정격(8위상)
R_CH = 0.00555                                   # 충전 경로 저항: Stage A 4모듈 2.55 mΩ + 배선 3 mΩ(E16)
I_PH_CH = I_CH / 8                               # 위상당 충전전류 46.9 A
STRUCTS = ["1", "2", "3", "W410", "W460", "4"]
LABEL = {"1": "① 승압기 + 보조 강압기", "2": "② Stage A + 전전력 조정기", "3": "③ PRISM-Hub 기준선(400 V 조정)",
         "W410": "R2-W410(창 조정, B_420용)", "W460": "R2-W460(창 조정, B_470용)", "4": "④ = R2 기본형(비조정)"}


def va_exact(vbat, power, R=NOMINAL.R):
    """비조정 정상점: V_A = V_bat/2 − R·P/V_A 의 큰 근(E13과 같은 식, 회생 P < 0 포함)."""
    e = vbat / 2
    return (e + math.sqrt(e * e - 4 * R * power)) / 2


def pack(ns):
    return dict(ns=ns, vmin=ns * V_CELL[0], vmax=ns * V_CELL[1],
                full=np.linspace(ns * V_CELL[0], ns * V_CELL[1], 25),
                drive=np.linspace(ns * V_CELL_DRIVE[0], ns * V_CELL_DRIVE[1], 15))


# ======================================================================================
# 2. Stage A 격자(E15 격자 + 사양 밖 배터리 전압)
# ======================================================================================
V_EXTRA = [540., 580., 960., 1010.]


class StageAX(B.StageA):
    """E15 StageA와 같은 보간 규칙에 배터리 전압 격자만 넓힌 것. 640–920 V 안에서는 E15와 같은 값을 낸다."""
    def __init__(self, VG, P, D, charge):
        super().__init__(dict(P=P, D=D, charge=charge))
        self.VG = np.asarray(VG)

    def _interp(self, Z, V, iph):
        iph = min(max(iph, B.IGRID[0]), B.IGRID[-1])
        row = np.array([np.interp(iph, B.IGRID, Z[k]) for k in range(len(self.VG))])
        return float(np.interp(V, self.VG, row))


def stage_a_model():
    reuse = os.environ.get("E18_REUSE_GRID") == "1" and (outdir("E18") / "stage_a_grid_ext.json").exists()
    if reuse:
        g = load_json("E18", "stage_a_grid_ext")
        print("E18 Stage A 격자: 저장된 결과 재사용")
    else:
        try:
            g15 = load_json("E15", "stage_a_grid")
        except FileNotFoundError:
            print("E15 격자가 없어 다시 계산 ...")
            T = B.stage_a_tables()
            g15 = dict(V=B.VGRID.tolist(), I=B.IGRID.tolist(), P_phase=T["P"].tolist(), dvA=T["D"].tolist(),
                       charge={str(k): v for k, v in T["charge"].items()})
        print(f"E18 Stage A 추가 격자(E1, 영교차 추종) 계산: V_bat {V_EXTRA} ...")
        jobs = [(V, i, 1.) for V in V_EXTRA for i in B.IGRID] + [(V, I_PH_CH, -1.) for V in V_EXTRA]
        with ProcessPoolExecutor(workers()) as ex:
            res = list(ex.map(B._e1_point, jobs))
        rows = {float(V): (P, D) for V, P, D in zip(g15["V"], g15["P_phase"], g15["dvA"])}
        for V in V_EXTRA:
            fw = [r for r in res if r["V"] == V and r["sign"] > 0]
            rows[V] = ([r["ploss_ph"] for r in fw], [r["dvA"] for r in fw])
        charge = {float(k): v for k, v in g15["charge"].items()}
        charge.update({r["V"]: r for r in res if r["sign"] < 0})
        VG = sorted(rows)
        g = dict(V=VG, I=B.IGRID, P_phase=[rows[v][0] for v in VG], dvA=[rows[v][1] for v in VG],
                 charge={str(k): charge[k] for k in sorted(charge)})
        save_json("E18", "stage_a_grid_ext", g)
    return StageAX(g["V"], np.array(g["P_phase"]), np.array(g["dvA"]), {float(k): v for k, v in g["charge"].items()})


# ======================================================================================
# 3. 창 조정 Stage B(R2-W): 권선비를 V_W에 맞춘 DAB + H-브리지 + 바이패스
# ======================================================================================
def dab_loss_v(Plink, Prated, V1=400.):
    """E15 dab_loss와 같은 규칙에 1차 전압 V1을 일반화. 권선비 V1/V_link, 누설 L = 11.1 µH·(V1/400)².
    V1 = 400이면 E15 dab_loss와 같은 값(회귀 검사 regression_check)."""
    s = V1 / 400.; L = B.LDAB * s ** 2; NT = V1 / B.VLINK; K = B.K; D650 = B.DEV["GaN650"]; D150 = B.DEV["GaN150"]
    wr = B.dab_wave(Prated, V1=V1, V2=V1, L=L)
    np_ = B.npar("GaN650", wr["Ipk"]); ns = B.npar("GaN150", NT * wr["Ipk"])
    w = B.dab_wave(Plink, V1=V1, V2=V1, L=L)
    Rw = K["mag_tr_cu"] * Prated / wr["Irms"] ** 2
    p_cond = (w["Irms"] ** 2 * 2 * D650["Ron"] / np_ + (NT * w["Irms"]) ** 2 * 2 * D150["Ron"] / ns + w["Irms"] ** 2 * Rw)
    p_nc = K["mag_tr_core"] * Prated
    I1min = 2 * np_ * D650["Ctr"] * V1 / 100e-9
    I2min = 2 * ns * D150["Ctr"] * B.VLINK / 100e-9 / NT
    if w["I1"] >= I1min:
        p_nc += 4 * B.FB * D650["Eoff"] * (w["I1"] / 20.) * s * K["esw"]
    else:
        p_nc += 4 * B.FB * np_ * D650["Eoss"] * s ** 1.5 * K["esw"]
    if w["I2"] >= I2min:
        p_nc += 4 * B.FB * 0.5 * B.VLINK * NT * w["I2"] * D150["toff"] * K["gan_t"] * K["esw"]
    else:
        p_nc += 4 * B.FB * ns * 0.5 * D150["Ctr"] * B.VLINK ** 2 * K["esw"]
    p_nc += 4 * B.FB * (np_ * D650["Qg"] * D650["Vg"] + ns * D150["Qg"] * D150["Vg"])
    p_nc += K["ctrl"]
    return p_cond + K["stageB_nc"] * p_nc


def path_window(SAm, V, P400, P48, VW, Pr, dab_v1=None):
    """R2-W 보조 경로 손실. V_A(무부하) > V_W + 0.5 V면 Stage B가 버스를 V_W로 조정, 아니면 바이패스(Stage B 정지)."""
    v1 = VW if dab_v1 is None else dab_v1
    if V / 2 > VW + 0.5:
        def solve(ip):
            pa, VA = SAm.drive(V, ip)
            pin_c, lc = B.stage_c(VW, P48, True)
            vs = VW - (VA - B.RW * ip)
            lhb = B.hbridge_loss(vs, ip)
            plink = vs * ip + lhb
            ldab = dab_loss_v(plink, Pr, v1)
            return VW * ip - (P400 + pin_c) - (plink + ldab), dict(pa=pa, lc=lc, lhb=lhb, ldab=ldab, plink=plink, vs=vs)
        ip = B.brentq(lambda x: solve(x)[0], 0., 250.)
        s = solve(ip)[1]
        return dict(loss=s["pa"] + B.RW * ip ** 2 + s["lhb"] + s["ldab"] + s["lc"], vbus=VW, ip=ip, plink=s["plink"],
                    vs=s["vs"], active=True)
    def bal(ip):
        pa, VA = SAm.drive(V, ip)
        vbus = VA - (B.RW + B.RBYP) * ip
        return vbus * ip - (P400 + B.stage_c(vbus, P48, True)[0])
    ip = B.brentq(bal, 0., 250.)
    pa, VA = SAm.drive(V, ip)
    vbus = VA - (B.RW + B.RBYP) * ip
    lc = B.stage_c(vbus, P48, True)[1]
    return dict(loss=pa + (B.RW + B.RBYP) * ip ** 2 + lc, vbus=vbus, ip=ip, plink=0., vs=0., active=False)


def window_rating_W(pk, VW):
    """창 조정 Stage B의 정적 최대 링크전력 [W]과 DAB 정격(×DAB_TRANSIENT, 0.5 kW 단위). 동작 구간이 없으면 None."""
    p = replace(NOMINAL, vref=VW)
    lw = [abs((p.vref - V / 2 + p.R * ip) * ip)
          for V in pk["full"] if V / 2 > VW + 0.5
          for P in P_STATIC for ip in [_eq_ip(V, P, p)]]
    if not lw:
        return None, None
    pmax = max(lw)
    return pmax, max(1000., math.ceil(DAB_TRANSIENT * pmax / 500.) * 500.)


def _eq_ip(vbat, power, p):
    from model_stage_b import equilibrium
    return float(equilibrium(vbat, power, p)[0][0])


# ======================================================================================
# 4. 성립성
# ======================================================================================
def feasibility(s, pk, cls, Pr=None):
    """구조 s가 팩 pk·부품 등급 cls에서 성립하는지(정적 운전점). 반환: dict(ok, reasons, bus_range, ...)."""
    upper = CLASSES[cls]; reasons = []; bus = []
    vA = [va_exact(V, P) for V in pk["full"] for P in P_STATIC]
    util = {}
    if s == "1":
        bus = [400.]
        util["SiC1200(승압기·보조 강압기)"] = pk["vmax"] / 1200.
    elif s == "2":
        bus = [400.]
        util["SiC750(Stage A)"] = pk["vmax"] / 2 / 750.; util["SiC750(조정기)"] = max(vA) / 750.
    elif s == "3":
        bus = [400.]
        p = replace(NOMINAL, vref=400.)
        bad = [V for V in pk["full"] for P in P_STATIC if not steady_feasible(V, P, p, control_reserve=False)]
        if bad:
            reasons.append("Stage B 포트 한계 밖: V_bat %.0f–%.0f V" % (min(bad), max(bad)))
        util["SiC750(Stage A)"] = pk["vmax"] / 2 / 750.; util["GaN650(DAB 1차)"] = 400. / 650.
    elif s in WINDOW:
        VW = WINDOW[s]
        if VW > upper - W_MARGIN:
            reasons.append("V_W %.0f V > 상한 − %.0f V" % (VW, W_MARGIN))
        p = replace(NOMINAL, vref=VW, turns=VW / NOMINAL.vlink, power_max=Pr or NOMINAL.power_max)
        bad = []
        for V in pk["full"]:
            for P in P_STATIC:
                if V / 2 > VW + 0.5:
                    bus.append(VW)
                    if not steady_feasible(V, P, p, control_reserve=False):
                        bad.append(V)
                else:
                    bus.append(va_exact(V, P) - B.RBYP * P / max(va_exact(V, P), 1.))
        if bad:
            reasons.append("Stage B 포트 한계 밖: V_bat %.0f–%.0f V" % (min(bad), max(bad)))
        util["SiC750(Stage A)"] = pk["vmax"] / 2 / 750.; util["GaN650(Stage C 전단·DAB 1차)"] = max(bus) / 650.
    elif s == "4":
        bus = vA
        util["SiC750(Stage A)"] = pk["vmax"] / 2 / 750.; util["GaN650(Stage C 전단)"] = max(vA) / 650.
    lo, hi = min(bus), max(bus)
    if hi > upper + 1e-9:
        reasons.append("버스 최대 %.1f V > %s 상한 %.0f V" % (hi, cls, upper))
    if lo < LOAD_MIN_V:
        reasons.append("버스 최소 %.1f V < 부하 하한 %.0f V" % (lo, LOAD_MIN_V))
    for k, u in util.items():
        if u > UTIL_MAX:
            reasons.append("%s 전압 사용률 %.0f %% > %.0f %%" % (k, 100 * u, 100 * UTIL_MAX))
    return dict(ok=not reasons, reasons=reasons, bus_V=[lo, hi], util={k: round(u, 3) for k, u in util.items()})


# ======================================================================================
# 5. 손실·정격·자성체
# ======================================================================================
def avg_loss(SAm, s, Vlist, Pr=None, dab_v1=None):
    L = np.zeros((len(Vlist), len(B.P400))); act = np.zeros(len(Vlist), bool)
    for i, V in enumerate(Vlist):
        for j, P in enumerate(B.P400):
            if s in WINDOW:
                r = path_window(SAm, V, P, B.P48, WINDOW[s], Pr, dab_v1)
                act[i] = r["active"]
            else:
                r = B.path_struct(s, SAm, V, P, B.P48)
            L[i, j] = r["loss"]
    return dict(avg_W=float(np.mean(L @ B.W400)), by_load_W=L.mean(0).tolist(), active_fraction=float(act.mean()))


def ind_energy(Iout, Vin_lo, Vin_hi, Vout, f, nph=1, ripple=0.3):
    """하드 스위칭 인덕터 저장에너지 [J] 합(½·L·I_pk²). 30 % 리플을 입력 범위 전체에서 지키는 최소 L(벅·부스트 중 큰 값).
    Iout: 위상당 인덕터 평균전류(벅: 출력전류, 부스트: 입력전류의 최댓값을 호출 측에서 넘김)."""
    dI = ripple * Iout
    Lb = (Vin_hi - Vout) * (Vout / Vin_hi) / (f * dI) if Vin_hi > Vout else 0.     # 벅 구간
    Lu = Vin_lo * (1 - Vin_lo / Vout) / (f * dI) if Vin_lo < Vout else 0.          # 부스트 구간
    L = max(Lb, Lu)
    return nph * 0.5 * L * (Iout + dI / 2) ** 2, L


def magnetics(s, pk, SAm, Pr=None):
    """구조별 인덕터 저장에너지 [mJ](공통인 Stage C CLLC 공진 L·변압기 자화 에너지는 제외)."""
    out = {}
    ipk_a = max(r["Ipk"] for r in SAm.T["charge"].values())
    stageA = 8 * 0.5 * 144e-9 * ipk_a ** 2
    vA_lo = min(va_exact(V, 25000.) for V in pk["full"]); vA_hi = max(va_exact(V, -3200.) for V in pk["full"])
    if s == "1":
        # 충전 승압기: 입력(충전기) V_bat/2 → 출력 V_bat, 듀티 0.5, 150 kW를 400 V 입력 기준 6위상으로 나눈 위상전류 62.5 A
        out["승압기(6위상, 150 kW)"] = ind_energy(150000. / 400. / 6, 400., 400., 800., 50e3, 6)[0]
        out["보조 강압기(2위상, 25 kW)"] = ind_energy(25000. / 400. / 2, pk["vmin"], pk["vmax"], 400., 50e3, 2)[0]
    else:
        out["Stage A 공진 L(8위상)"] = stageA
    if s == "2":
        out["전전력 조정기(25 kW)"] = ind_energy(25000. / vA_lo, vA_lo, vA_hi, 400., 50e3)[0]
    if s in ("3",) + tuple(WINDOW):
        out["Stage B 필터 L_h"] = 0.5 * 5e-6 * 100. ** 2
        VW = 400. if s == "3" else WINDOW[s]; Prr = 8000. if s == "3" else Pr
        if Prr:
            w = B.dab_wave(Prr, V1=VW, V2=VW, L=B.LDAB * (VW / 400.) ** 2)
            out["Stage B DAB 누설 L"] = 0.5 * B.LDAB * (VW / 400.) ** 2 * w["Ipk"] ** 2
    if s in tuple(WINDOW) + ("4",):
        hi = vA_hi if s == "4" else min(vA_hi, WINDOW[s])
        out["조정형 Stage C 전단(3.3 kW)"] = ind_energy(3300. / vA_lo, vA_lo, hi, 400., 100e3)[0]
    tot = sum(out.values())
    return dict(parts_mJ={k: round(1e3 * v, 2) for k, v in out.items()}, total_mJ=1e3 * tot)


def ratings_s(s, SAm, Pr=None):
    """E15 ratings와 같은 규칙. 창 조정은 DAB 정격 Pr과 1차 전압 V_W로 다시 계산."""
    base = B.ratings(SAm)
    if s in ("1", "2", "3", "4"):
        return base[s]["total"]
    VW = WINDOW[s]; NT = VW / B.VLINK; L = B.LDAB * (VW / 400.) ** 2
    if Pr is None:                                  # 동작 구간 없음: Stage B·바이패스를 설치하지 않음(= ④)
        return base["4"]["total"]
    wr = B.dab_wave(Pr, V1=VW, V2=VW, L=L)
    np_ = B.npar("GaN650", wr["Ipk"]); ns = B.npar("GaN150", NT * wr["Ipk"])
    stB = dict(positions=12, devices=4 * np_ + 4 * ns + 4 * B.npar("GaN150", 100.),
               switch_kVA=(4 * 650 * wr["Irms"] / math.sqrt(2) + 4 * 150 * NT * wr["Irms"] / math.sqrt(2)
                           + 4 * 150 * 100 / math.sqrt(2)) / 1e3, rated_kW=Pr / 1e3, magnetics=2)
    parts = [x[1] for x in B.ratings(SAm)["4"]["parts"].items()] + [stB, dict(positions=2, devices=4, switch_kVA=30., rated_kW=0., magnetics=0)]
    return {m: sum(p[m] for p in parts) for m in ("positions", "devices", "switch_kVA", "rated_kW", "magnetics")}


# ======================================================================================
# 6. 500 V급 충전기 호환(Stage A)
# ======================================================================================
def charging(pk, SAm):
    p_ph = float(np.mean([r["ploss_ph"] for r in SAm.T["charge"].values()]))     # 위상당 손실(46.9 A, 전압 무관)
    vmax_bat = 2 * (CHARGER_VMAX - R_CH * I_CH)
    cell_max = min(V_CELL[1], vmax_bat / pk["ns"])
    vA_mid = pk["ns"] * 3.7 / 2
    out = dict(vA_range_V=[pk["vmin"] / 2, pk["vmax"] / 2], vbat_max_500V=vmax_bat, cell_max_500V=cell_max,
               full_charge_ok=bool(pk["vmax"] <= vmax_bat), P_375A_cell3p7_kW=(vA_mid + R_CH * I_CH) * I_CH / 1e3)
    for Pt in (150e3, 225e3):
        nph = 2 * math.ceil(Pt / (vA_mid * I_PH_CH) / 2)                        # 모듈(2위상) 단위
        out[f"phases_for_{Pt/1e3:.0f}kW"] = nph
        out[f"loss_{Pt/1e3:.0f}kW_W"] = nph * p_ph * (Pt / (vA_mid * I_PH_CH * nph)) ** 2 + nph / 2 * B.K["ctrl"]
    return out


# ======================================================================================
# 7. 실행
# ======================================================================================
def regression_check(SAm):
    """(a) dab_loss_v(V1=400)가 E15 dab_loss와 같은지, (b) 사양(640–920 V) 손실이 E15 결과와 같은지."""
    d = max(abs(dab_loss_v(P, 5000.) - B.dab_loss(P, 5000.)) for P in (-3000., -100., 0., 50., 2000., 4500.))
    try:
        e15 = load_json("E15", "comparison")["results"]
    except FileNotFoundError:                         # E15를 먼저 실행하지 않았으면 DAB 회귀 검사만 한다
        print("회귀 검사: DAB 손실 최대 차 %.2e W (E15 결과 파일이 없어 사양 비교 생략)" % d)
        return dict(dab_max_diff_W=d, spec_avg_vs_E15_max_diff_W=None)
    Vd = B.PROFILES["drive_typ"]["V"]
    rep = {s: B.path_struct(s, SAm, 800., 5500., B.P48)["loss"] for s in ("1", "2", "3", "4")}
    rep_avg = {s: avg_loss(SAm, s, Vd)["avg_W"] for s in ("1", "2", "3", "4")}
    w = avg_loss(SAm, "W410", Vd, Pr=5000., dab_v1=400.)["avg_W"]
    ref = {s: e15[s]["drive_typ"]["avg_loss_W"] for s in ("1", "2", "3", "3w", "4")}
    diff = max([abs(rep_avg[s] - ref[s]) for s in rep_avg] + [abs(w - ref["3w"])])
    print("회귀 검사: DAB 손실 최대 차 %.2e W, 사양 프로파일 E15 대비 최대 차 %.2e W" % (d, diff))
    return dict(dab_max_diff_W=d, spec_avg_vs_E15_max_diff_W=diff, spec_avg=rep_avg | {"W410_E15form": w}, E15=ref,
                point_800V_5p5kW=rep)


def main():
    SAm = stage_a_model()
    reg = regression_check(SAm)
    out = dict(regression=reg, conditions=dict(cells=CELLS, v_cell=V_CELL, v_cell_drive=V_CELL_DRIVE, classes=CLASSES,
               load_min_V=LOAD_MIN_V, p_static_W=P_STATIC, util_max=UTIL_MAX, window_V=WINDOW, window_margin_V=W_MARGIN,
               charger_vmax_V=CHARGER_VMAX, charge_A=I_CH, charge_R_ohm=R_CH), packs={})
    # 사양(640–920 V): E15 프로파일과 같은 조건에서 R2-W460까지 계산
    spec = dict(ns=219.05, vmin=SPEC_V[0], vmax=SPEC_V[1], full=np.linspace(*SPEC_V, 25), drive=B.PROFILES["drive_typ"]["V"])
    for pk in [pack(n) for n in CELLS] + [spec]:
        key = "spec" if pk is spec else f"{pk['ns']}s"
        r = dict(vbat_V=[pk["vmin"], pk["vmax"]], drive_V=[float(pk["drive"][0]), float(pk["drive"][-1])], structs={})
        for s in STRUCTS:
            Pr = pmax = None
            if s in WINDOW:
                pmax, Pr = window_rating_W(pk, WINDOW[s])
            row = dict(loss=avg_loss(SAm, s, pk["drive"], Pr), feas={c: feasibility(s, pk, c, Pr) for c in CLASSES},
                       rating=ratings_s(s, SAm, Pr), magnetics=magnetics(s, pk, SAm, Pr))
            if s in WINDOW:
                row["stage_b"] = dict(needed=Pr is not None, link_W_static_max=pmax, dab_rated_W=Pr,
                                      active_vbat_from=2 * (WINDOW[s] + 0.5),
                                      series_max_V=(max(va_exact(V, -3200.) for V in pk["full"]) - WINDOW[s]) if Pr else 0.)
            r["structs"][s] = row
        for s in WINDOW:                       # 동작 구간이 없으면 Stage B·바이패스를 설치하지 않으므로 ④와 같다
            if not r["structs"][s]["stage_b"]["needed"]:
                sb = r["structs"][s]["stage_b"]
                r["structs"][s] = dict(r["structs"]["4"], stage_b=sb, same_as="4")
        r["charging"] = charging(pk, SAm)
        best = {}
        for c in CLASSES:
            ok = [s for s in STRUCTS if r["structs"][s]["feas"][c]["ok"] and "same_as" not in r["structs"][s]]
            best[c] = dict(feasible=ok, best=min(ok, key=lambda s: r["structs"][s]["loss"]["avg_W"]) if ok else None)
        r["best"] = best
        out["packs"][key] = r
        print(f"\n[{key}] 배터리 {pk['vmin']:.0f}–{pk['vmax']:.0f} V, V_A {pk['vmin']/2:.0f}–{pk['vmax']/2:.0f} V")
        for s in STRUCTS:
            x = r["structs"][s]
            extra = ""
            if s in WINDOW:
                sb = x["stage_b"]
                extra = (f" | Stage B {'불필요' if not sb['needed'] else '%.1f kW(정적 %.2f kW), 직렬 최대 %.1f V, 주행 동작 %.0f %%' % (sb['dab_rated_W']/1e3, sb['link_W_static_max']/1e3, sb['series_max_V'], 100*x['loss']['active_fraction'])}")
            print("  %-34s 손실 %6.1f W | B_420 %s | B_470 %s | 위치 %d VA %.0f kVA | L 에너지 %.1f mJ%s" % (
                LABEL[s], x["loss"]["avg_W"], "성립" if x["feas"]["B_420"]["ok"] else "불가",
                "성립" if x["feas"]["B_470"]["ok"] else "불가", x["rating"]["positions"], x["rating"]["switch_kVA"],
                x["magnetics"]["total_mJ"], extra))
            for c in CLASSES:
                if not x["feas"][c]["ok"]:
                    print("      %s: %s" % (c, "; ".join(x["feas"][c]["reasons"])))
        ch = r["charging"]
        print("  최선(성립 구조 중 최소 손실): B_420 %s, B_470 %s" % (best["B_420"]["best"], best["B_470"]["best"]))
        print("  500 V 충전기: 셀 %.3f V까지(%s), 375 A·셀 3.7 V에서 %.0f kW, 150 kW %d위상(%.0f W), 225 kW %d위상(%.0f W)" % (
            ch["cell_max_500V"], "만충 가능" if ch["full_charge_ok"] else "만충 불가", ch["P_375A_cell3p7_kW"],
            ch["phases_for_150kW"], ch["loss_150kW_W"], ch["phases_for_225kW"], ch["loss_225kW_W"]))
    save_json("E18", "value_map", out)
    figure(out, outdir("E18") / "E18_value_map.png")


def figure(out, path):
    from plotstyle import korean, COLOR as C
    plt = korean()
    keys = [f"{n}s" for n in CELLS]; ns = np.array(CELLS)
    col = {"1": C["gray"], "2": C["green"], "3": C["blue"], "W410": "#8faadc", "W460": C["red"], "4": C["orange"]}
    mk = {"1": "s", "2": "D", "3": "o", "W410": "^", "W460": "v", "4": "P"}
    short = {"1": "①", "2": "②", "3": "③", "W410": "R2-W410", "W460": "R2-W460", "4": "④(R2 기본)"}
    fig, ax = plt.subplots(1, 4, figsize=(16, 4.1))
    # (a) 비조정 V_A 범위와 부품 등급
    for k, n in zip(keys, ns):
        lo, hi = out["packs"][k]["structs"]["4"]["feas"]["B_470"]["bus_V"]
        ax[0].plot([n, n], [lo, hi], color=C["orange"], lw=6, solid_capstyle="butt")
    for y, t, c in [(420, "B_420 상한 420 V", C["blue"]), (470, "B_470 상한 470 V", C["red"]), (260, "부하 하한 260 V", C["gray"]),
                    (CHARGER_VMAX, "500 V급 충전기 최대", C["green"])]:
        ax[0].axhline(y, color=c, ls="--", lw=1); ax[0].text(203, y + 4, t, fontsize=7.5, color=c)
    ax[0].set_xlabel("셀 직렬수 [s]"); ax[0].set_ylabel("V_A = V_bat/2 (부하 −3.2–25 kW) [V]")
    ax[0].set_title("(a) 비조정 V_A 범위(셀 3.0–4.2 V)"); ax[0].set_ylim(240, 540); ax[0].set_xlim(175, 245)
    # (b)(c) 부품 등급별 평균 손실(성립: 채운 표시, 불가: 빈 표시)
    for a, c in zip(ax[1:3], CLASSES):
        for s in STRUCTS:
            # 창 조정 구조는 Stage B가 필요한 팩만 표시(필요 없으면 ④와 같으므로 생략)
            use = np.array(["same_as" not in out["packs"][k]["structs"][s] for k in keys])
            y = np.array([out["packs"][k]["structs"][s]["loss"]["avg_W"] for k in keys])
            ok = np.array([out["packs"][k]["structs"][s]["feas"][c]["ok"] for k in keys])
            a.plot(ns[use], y[use], "-", color=col[s], lw=1, alpha=.45)
            a.plot(ns[ok & use], y[ok & use], mk[s], color=col[s], ms=6, label=short[s])
            a.plot(ns[~ok & use], y[~ok & use], mk[s], color=col[s], ms=6, mfc="none", alpha=.6)
        a.set_xlabel("셀 직렬수 [s]"); a.set_ylabel("주행 프로파일 평균 보조 경로 손실 [W]")
        a.set_title(f"({'b' if c == 'B_420' else 'c'}) 400 V 부품 {c}: 채움 = 성립, 빈 표시 = 불가")
        a.set_ylim(60, 200); a.legend(ncol=3, fontsize=7, loc="upper left")
    # (d) 500 V 충전기 호환
    cm = [out["packs"][k]["charging"]["cell_max_500V"] for k in keys]
    pw = [out["packs"][k]["charging"]["P_375A_cell3p7_kW"] for k in keys]
    ax[3].bar(ns - 2, pw, 4, color=C["blue"], label="375 A·셀 3.7 V 충전전력 [kW]")
    ax[3].set_ylabel("충전전력 [kW]"); ax[3].set_ylim(0, 300); ax[3].set_xlabel("셀 직렬수 [s]")
    a2 = ax[3].twinx(); a2.grid(False)
    a2.plot(ns, cm, "o-", color=C["orange"], label="500 V 충전기로 충전 가능한 최대 셀 전압 [V]")
    a2.set_ylim(3.2, 4.25); a2.set_ylabel("최대 셀 전압 [V]")
    h1, l1 = ax[3].get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
    ax[3].legend(h1 + h2, l1 + l2, loc="center left", bbox_to_anchor=(0., .72), fontsize=7)
    ax[3].set_title("(d) Stage A 500 V급 충전기 호환(8위상 375 A)")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


if __name__ == "__main__":
    main()
