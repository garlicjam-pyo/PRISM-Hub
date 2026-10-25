"""[E22] 조정형 Stage C 5 kW: 전단 벅 + CLLC 직류변압기(DCX)의 설계와 검증(R2 기본형의 48 V 공급).

■ 목적
  R2 기본형에서는 400 V 버스가 V_A를 그대로 따르므로(E15 ④, docs/23), 48 V를 만드는 Stage C가 넓은 입력에서
  스스로 조정해야 한다. 이 시험은 (1) 요구사항을 수치로 고정하고, (2) 전단 조정기 + 공진점 고정 CLLC(DCX)
  두 후보(벅 + 4.8:1, 4스위치 벅부스트 + 25/3:1)를 같은 손실 규칙으로 비교해 구조와 부품 값을 정하며,
  (3) 정한 DCX를 스위칭 ODE로, (4) 전단 제어를 평균모델로 확인한다. 회로 확인은 Simulink TB14가 한다.

■ 왜 필요한가
  기존 Stage C(E10·TB05)는 400±8 V 버스를 전제로 한 3 kW 고정이득 CLLC였다. R2에서는 입력이 270–504 V로
  넓어지고(1.87배), 48 V 배터리가 연결된 전원망에서 충전 전류까지 다뤄야 하며, 회생(48 V → 버스)도 받아야 한다.
  고정이득 CLLC에 V_A를 그대로 넣으면 48 V가 32.4–60.5 V가 되어 ISO 21780의 36–52 V를 벗어난다.
  공진형 하나로 주파수 조정을 하면 이득 범위 1.87배를 양방향으로 내야 해, 자화 인덕턴스를 작게 두는 대가로
  순환전류가 커진다. 그래서 전단 조정기 + 공진점 DCX의 2단 구성을 쓰고(Zanatta 등, IEEE TIA 2022),
  CLLC는 공진점에서 양방향 이득이 1인 성질(Jung 등, IEEE TPEL 2013)을 쓴다.

■ 요구사항(시험 전에 고정, docs/14·23)
  입력 V_bus 270–504 V: R2 팩 180–240s × 셀 3.0–4.2 V의 V_A, 강등 상태(버스 = V_A) 포함
  출력 48 V 전원망: 설정 48 V ±2 %(배터리 없는 최악 조건, 정상·계약 과도), CV 설정 범위 36–52 V(ISO 21780)
  전력 +5 kW(48 V 쪽 공급), −3 kW(48 V → 버스 회생), 출력전류 정격 105 A(과도 제어 제한 130 A, 2 ms), 부하 변화 ≤ 4 kW/ms(계약)
  견고성: 0 → 5 kW 계단, 버스 ±50 V 계단에서 36–52 V 유지

■ 방법
  design  : 후보 A(동기 벅 1상 100 kHz + CLLC 4.8:1, V_I 173–253 V)와 B(4스위치 벅부스트 + CLLC 25/3:1,
            V_I 300–433 V)의 손실(E15와 같은 소자·자성체·제어 손실 규칙), 스위치 위치·소자 수, 인덕터 에너지,
            동작 모드 경계. 선택한 구조의 부품 값(인덕터, 공진망, 커패시터).
  dcx     : 선택한 CLLC DCX의 공진점 스위칭 ODE(1차 환산 5상태, RK4 주기당 400단계). 보내는 쪽 브리지를 f_r 구형파로
            구동하고(데드타임 동안 브리지 전압은 전류 방향의 다이오드가 정함), 받는 쪽 브리지는 동기정류(다이오드처럼
            전류 방향으로 도통)로 둔다. 전력 방향(보내는 쪽)은 전력 지령의 부호로 고른다.
            V_I·V_o를 고정 전원으로 두고 V_I를 찾아 P_o −3–5 kW(V_o 36·48·52 V)를 맞춘 뒤 이득, 등가 저항,
            보내는 쪽 전환 순간 전류(ZVS), 실효·첨두 전류, 공진 커패시터 첨두를 본다.
            처음 안(두 브리지를 같은 위상으로 구동, 방향 자동)은 자화 전류가 두 브리지로 나뉘고 받는 쪽이 부하 전류를
            반대 방향으로 끊어 ZVS가 깨졌다(1차 여유 −0.70, 2차 −6.17). 그래서 받는 쪽을 동기정류로 바꿨다.
  control : 전단 벅 + DCX 평균모델(벅 인덕터, C_I, DCX 등가 L_x·R_x(dcx 계단 응답에서), C_o, 48 V 배터리·정전력 부하)과
            디지털 제어(100 kHz 표본, 계산 지연 1주기): 인덕터 전류 PI(교차 5 kHz, 입력전압 앞먹임) ← 출력전류 지령 =
            min(48 V 전압 PI(교차 1 kHz, 부하전류 앞먹임), 배터리 충전전류 PI(부하전류 + 충전 제한 앞먹임), 전류 제한).
            전류 제한은 과도 130 A, 지령이 정격 105 A를 넘은 시간이 2 ms를 넘으면 105 A(과부하 시간 제한).
            DCX 보내는 쪽은 전류 지령의 부호(히스테리시스 0.5 A).
            처음 안은 출력전류 제한 105 A(= 5 kW/47.6 V), 전압 기준을 낮추는 충전 제한, 포화 때 적분을 되돌리는 누적 방지였다.
            정전력 계단에서 전압이 47.6 V 아래로 내려가면 부하가 제한을 넘어 붕괴했고(T3), 배터리가 있으면 전압 루프 이득이
            R_b배로 작아져 충전 제한이 수 ms 걸렸다(T5). 되돌림 누적 방지는 포화가 풀린 뒤 적분이 비례 동작을 지워 전류가
            느리게 올랐다. 앞먹임에 배터리 전류까지 넣으면 방전이 지령을 더 낮추는 양의 되먹임이 되었다(부하 해제 뒤 배터리 −114 A).
            그래서 제어 제한을 130 A로, 충전 제한을 전류 지령의 최솟값 선택으로, 누적 방지를 조건부 적분으로, 앞먹임을 부하전류만으로
            바꿨다. 출력 커패시터 1 mF·제한 115 A에서는 배터리 없는 −3 → +5 kW 계단이 270 V 입력에서 벅 전류 기울기 한계
            (여유 32 V / 204 µH = 0.16 A/µs)로 붕괴했고, 5 → −3 kW 계단에서는 52.9 V가 되어 출력 커패시터를
            2.2 mF로 늘렸다. 배터리가 있으면 제한 130 A가 계속 걸려 정격 105 A를 넘었으므로 과부하 시간 제한을 넣었다.
            전류 PI는 계단 지령에서 약 15 % 넘쳐, 비례항에 지령 가중 0.7을 두었다.
            DCX는 커패시터 사이의 직류변압기라 계단 직후 출력전류가 벅 전류 제한을 순간적으로 넘는다(C_I·C_o 사이 교환).
            그래서 전류 제한 판정은 100 µs 이동평균으로 하고, 순간 첨두는 2차 소자 펄스 정격(EPC2305 329 A)과 비교한다
            (처음 기준은 순간값 ≤ 제한 × 1.05였고 지키지 못했다).
            시험 T1 정상 조정(입력 5점 × 전력 4점), T2 계약 부하 변화(4 kW/ms), T3 계단 부하(견고성), T4 버스 계단(±50 V/10 µs),
            T5 배터리 연결(충전 제한·부하 계단), T6 전력 방향 전환, T7 입력 임피던스와 버스 임피던스(Middlebrook).

■ 판정 기준(design)
  손실 지표는 E15(H5)와 같은 대표 부하를 쓴다: 48 V 1.5 kW에서 입력 270–504 V 다섯 점의 평균 손실(같은 병렬 2·2·2).
  이 평균 손실이 작은 후보를 고르고, 차가 5 % 이하면 모드 경계가 없고 스위치 위치가 적은 쪽을 고른다.
  제약: 선택 구조의 5 kW 효율 ≥ 96 %(입력 전 범위). 정격 5 kW의 최악 손실은 함께 기록한다(열 설계 근거).
  자화 전류는 ZVS 조건(최고 V_I에서 1차 레그 출력용량 충방전 전류의 1.2배, 최소 4 A)으로 정한다.

■ 판정 기준(dcx)
  이득 n·V_o/V_I = 1 ± 3 %(−3–5 kW, V_o 36·48·52 V, TB05와 같은 허용폭). 보내는 쪽 브리지가 모든 점에서 전환 순간 전류가
  ZVS 방향이고 크기 ≥ ZVS 전류(데드타임 100 ns 안에 레그 출력용량 충방전). 받는 쪽 전환 순간 전류(동기정류 꺼짐)와
  공진 커패시터 첨두는 기록.

■ 판정 기준(control)
  T1 정상 오차 ≤ 0.1 %. T2·T4·T6 48 V ±2 %(47.04–48.96 V). T3(배터리 없음, 0.1 ↔ 5 kW·−3 ↔ +5 kW 계단)·T5(배터리 연결,
  0.1 → 5 → 0.1 kW와 −3 ↔ +5 kW 계단) 36–52 V(ISO 21780) 안. 출력전류 100 µs 이동평균 ≤ 130 A × 1.05, 계단 2.5 ms 뒤
  ≤ 105 A × 1.05, 순간 2차 소자 전류 π/2·i_x/n_s ≤ 329 A(펄스 정격). T5 충전전류는 부하 계단 1 ms 뒤 ≤ 30 A × 1.05.
  모든 시험에서
  듀티 포화가 0.5 ms를 넘지 않음. T7 |Z_bus| ≤ |Z_in|/2(6 dB, 10 Hz–20 kHz, 5 kW·입력 270·504 V).

■ 실행   python E22_stage_c_regulated.py design dcx control figures   (약 6분)
■ 결과   results/E22/design.json, dcx.json, control.json, E22_stage_c_regulated.png
"""
import json
import math
import sys

import numpy as np

from common import save_json, verdict, outdir
from E15_baseline_loss_rating import DEV, K, esw_hard

try:
    from numba import njit
except ImportError:                                           # numba가 없으면 순수 Python(느림)
    def njit(*a, **k):
        def deco(f):
            return f
        return deco if not (len(a) == 1 and callable(a[0])) else a[0]

EID = "E22"

# ---------------------------------------------------------------------------------------------
# 요구사항
# ---------------------------------------------------------------------------------------------
VBUS = (270., 504.)                 # 입력 범위 [V]
VBUS_GRID = (270., 330., 400., 460., 504.)
VO_NOM = 48.                        # 48 V 설정
VO_TOL = 0.02                       # ±2 %
VO_CV = (36., 52.)                  # CV 설정 범위(ISO 21780 무제한 운전 범위)
PO_MAX = 5000.                      # 48 V 쪽 공급 [W]
PO_REV = -3000.                     # 48 V → 버스 회생 [W]
IO_MAX = 105.                       # 출력전류 정격(연속) [A]
I_LIM = 130.                        # 제어 전류 제한(과도, 최대 T_OL) [A]: 5 kW 정전력 부하가 38.5 V까지 내려가도 공급(계단 뒤 회복)
T_OL = 2e-3                         # 과도 전류 허용 시간 [s]: 지령이 정격(105 A)을 넘은 시간이 이보다 길면 제한을 105 A로
ID_PULSE_S = 329.                   # 2차 소자(EPC2305) 펄스 정격 [A](300 µs, 데이터시트)
SLEW = 4e6                          # 계약 부하 변화율 [W/s] = 4 kW/ms
TD = 100e-9                         # 1차 데드타임 [s]

# ---------------------------------------------------------------------------------------------
# 후보 구조
# ---------------------------------------------------------------------------------------------
# A: 동기 벅(V_bus → V_I, 항상 강압) + CLLC DCX n = 4.8. V_I = n·V_o + DCX 강하. V_o 52 V에서 V_I ≈ 253 V < 270 V
# B: 4스위치 벅부스트(V_bus ↔ V_I) + CLLC DCX n = 25/3(E10·TB05와 같은 권선비). V_I = 300–433 V
CAND = {
    "A": dict(label="동기 벅 + CLLC 4.8:1", front="buck", n=4.8, fb=100e3, fr=250e3),
    "B": dict(label="4스위치 벅부스트 + CLLC 25/3:1", front="fsbb", n=25 / 3, fb=100e3, fr=250e3),
}
RIPPLE = 0.3                        # 전단 인덕터 전류 리플(정격 전류 대비, 최악 입력)


def dcx_params(n, np_, Vo=VO_NOM, P=PO_MAX, fr=250e3, Q=0.4):
    """CLLC DCX 공진망: 정격 부하에서 품질계수 Q, 자화 전류 첨두 im_pk(ZVS용)로 L_r, C_r, L_m을 정한다(1차 환산, 대칭).
    Rac = 8n²/π²·R_L(기본파 등가 부하), Z0 = Q·Rac, L_r = Z0/(2πf_r), C_r = 1/(2πf_r·Z0), L_m = n·52 V/(4·f_r·im_pk).
    im_pk = max(4 A, 1.2 × ZVS 전류(V_I 최고 = n·52 V, 1차 병렬 np_))."""
    im_pk = max(4.0, 1.2 * zvs_current(n * VO_CV[1], np_))
    RL = Vo ** 2 / P
    Rac = 8 * n ** 2 / math.pi ** 2 * RL
    Z0 = Q * Rac
    Lr = Z0 / (2 * math.pi * fr); Cr = 1 / (2 * math.pi * fr * Z0)
    VI = n * Vo
    Lm = n * VO_CV[1] / (4 * fr * im_pk)
    return dict(n=n, fr=fr, Q=Q, Rac=Rac, Z0=Z0, Lr=Lr, Cr=Cr, Lm=Lm, m=Lm / Lr, im_pk=im_pk, VI=VI)


def zvs_current(Vi, npar, td=TD):
    """1차 레그 하나의 영전압 전이에 필요한 전류: 두 소자의 출력용량(C_o(tr))을 데드타임 안에 충방전."""
    return 2 * npar * DEV["GaN650"]["Ctr"] * Vi / td


def dcx_loss(c, Po, Vo, np_, ns_, Prated=PO_MAX):
    """CLLC DCX 손실 추정(공진점). 1차 전류 = 부하 정현파(첨두 πI_o/(2n)) + 자화 삼각파(첨두 im_pk).
    도통(1차 2소자·2차 2소자 경로 + 권선), 철손, 1차 꺼짐(자화 전류에서), 게이트, 제어. 2차는 공진점에서 영전류 전환."""
    n = c["n"]; Io = abs(Po) / Vo
    VI = n * Vo
    im = VI / (4 * c["fr"] * c["Lm"])
    Ip = math.sqrt((math.pi * Io / (2 * n)) ** 2 / 2 + im ** 2 / 3)
    Is = math.pi * Io / (2 * math.sqrt(2))
    Ip_r = math.sqrt((math.pi * (Prated / Vo) / (2 * n)) ** 2 / 2 + im ** 2 / 3)
    Rw = K["mag_tr_cu"] * Prated / Ip_r ** 2
    p = dict(cond_p=2 * DEV["GaN650"]["Ron"] / np_ * Ip ** 2, cond_s=2 * DEV["GaN150"]["Ron"] / ns_ * Is ** 2,
             winding=Rw * Ip ** 2, core=K["mag_tr_core"] * Prated,
             turnoff=4 * c["fr"] * DEV["GaN650"]["Eoff"] * (im / 20.) * K["esw"],
             gate=4 * c["fr"] * (np_ * DEV["GaN650"]["Qg"] * DEV["GaN650"]["Vg"] + ns_ * DEV["GaN150"]["Qg"] * DEV["GaN150"]["Vg"]),
             ctrl=K["ctrl"])
    p["total"] = sum(p.values())
    return p, dict(Ip=Ip, Is=Is, im=im, Ip_pk=math.pi * Io / (2 * n) + im, Is_pk=math.pi * Io / 2)


def front_mode(kind, Vbus, VI):
    if kind == "buck":
        return "buck"
    if Vbus > VI * 1.02:
        return "buck"
    if Vbus < VI * 0.98:
        return "boost"
    return "buckboost"


def front_design(c, Prated=PO_MAX * 1.03):
    """전단 인덕터: 최악 입력·출력에서 리플 RIPPLE × 정격 전류. 반환: L, 정격 전류, 최대 인덕터 전류."""
    n = c["n"]
    VIs = (n * VO_CV[0], n * VO_NOM, n * VO_CV[1])
    worst = []
    for Vb in VBUS_GRID:
        for VI in VIs:
            mode = front_mode(c["front"], Vb, VI)
            if mode == "buck":
                IL = Prated / VI; D = VI / Vb; L = VI * (1 - D) / (RIPPLE * IL * c["fb"])
            elif mode == "boost":
                IL = Prated / Vb; D = 1 - Vb / VI; L = Vb * D / (RIPPLE * IL * c["fb"])
            else:
                IL = Prated / min(Vb, VI); L = 0.
            worst.append((L, IL, Vb, VI))
    L = max(w[0] for w in worst)
    ILmax = max(w[1] for w in worst)
    return dict(L=L, IL_max=ILmax, E_L=0.5 * L * (ILmax * (1 + RIPPLE / 2)) ** 2)


def front_loss(c, fd, Vbus, VI, P, nsw):
    """전단 손실(E15 hs_converter와 같은 규칙, 소자 병렬 nsw를 직접 지정). P: 전단 출력(V_I 쪽) 전력의 크기."""
    d = DEV["GaN650"]
    mode = front_mode(c["front"], Vbus, VI)
    if mode == "buck":
        IL = P / VI; Vsw = Vbus; D = VI / Vbus; legs = 1
        dI = VI * (1 - D) / (fd["L"] * c["fb"])
        on_path = 1 if c["front"] == "buck" else 2
    elif mode == "boost":
        IL = P / Vbus; Vsw = VI; D = 1 - Vbus / VI; legs = 1
        dI = Vbus * D / (fd["L"] * c["fb"]); on_path = 2
    else:
        IL = P / min(Vbus, VI); Vsw = max(Vbus, VI); legs = 2; on_path = 2
        dI = RIPPLE * IL
    Irms2 = IL ** 2 + dI ** 2 / 12
    p = dict(cond=Irms2 * d["Ron"] / nsw * on_path,
             sw=legs * c["fb"] * esw_hard("GaN650", Vsw, IL, nsw),
             dead=legs * 2 * d["td"] * c["fb"] * IL * d["Vsd"],
             gate=legs * 2 * nsw * d["Qg"] * d["Vg"] * c["fb"])
    Irated = PO_MAX * 1.03 / (c["n"] * VO_NOM)
    Rdcr = K["mag_ind_cu"] * PO_MAX / Irated ** 2
    p["ind"] = Irms2 * Rdcr + K["mag_ind_core"] * PO_MAX
    p["ctrl"] = K["ctrl"]
    p["total"] = sum(p.values())
    return p, dict(mode=mode, IL=IL, dI=dI, D=D if mode != "buckboost" else None)


def evaluate(key, nsw, np_, ns_):
    c = CAND[key]
    c = dict(c, **dcx_params(c["n"], np_, fr=c["fr"]))
    fd = front_design(c)
    rows = []
    for Po in (PO_MAX, 1500., PO_REV):
        for Vb in VBUS_GRID:
            pd, xd = dcx_loss(c, Po, VO_NOM, np_, ns_)
            VI = c["n"] * VO_NOM
            Pfront = abs(Po) + pd["total"] if Po > 0 else abs(Po) - pd["total"]
            pf, xf = front_loss(c, fd, Vb, VI, Pfront, nsw)
            tot = pf["total"] + pd["total"]
            Pin = abs(Po) + tot
            rows.append(dict(Po=Po, Vbus=Vb, VI=VI, mode=xf["mode"], loss_front=pf["total"], loss_dcx=pd["total"], loss=tot,
                             eff=(abs(Po) / Pin) if Po > 0 else (abs(Po) - tot) / abs(Po),
                             front=pf, dcx=pd, IL=xf["IL"], dI=xf["dI"], D=xf["D"], Ip=xd["Ip"], Is=xd["Is"], im=xd["im"],
                             Ip_pk=xd["Ip_pk"], Is_pk=xd["Is_pk"]))
    pos = {"buck": 2, "fsbb": 4}[c["front"]] + 4 + 4
    dev = {"buck": 2, "fsbb": 4}[c["front"]] * nsw + 4 * np_ + 4 * ns_
    VIr = (c["n"] * VO_CV[0], c["n"] * VO_CV[1])
    nb = sum(1 for Vb in np.linspace(*VBUS, 200) for VI in np.linspace(*VIr, 50)
             if front_mode(c["front"], Vb, VI) == "buckboost")
    return dict(key=key, label=c["label"], params=c, front=fd, rows=rows, positions=pos, devices=dev,
                nsw=nsw, np=np_, ns=ns_, VI_range=VIr, buckboost_fraction=nb / (200 * 50),
                zvs_I=zvs_current(c["n"] * VO_CV[1], np_), im_pk=c["im_pk"])


def design():
    out = {}
    print("  후보별 손실(5 kW, 입력 270·330·400·460·504 V) [W]")
    for key in CAND:
        for nsw, np_, ns_ in ((1, 1, 2), (2, 2, 2)):
            r = evaluate(key, nsw, np_, ns_)
            tag = "%s_%d%d%d" % (key, nsw, np_, ns_)
            out[tag] = r
            L5 = [x["loss"] for x in r["rows"] if x["Po"] == PO_MAX]
            L15 = [x["loss"] for x in r["rows"] if x["Po"] == 1500.]
            print("  %-30s 병렬(전단·1차·2차) %d·%d·%d: 5 kW %s / 1.5 kW %s, 위치 %d·소자 %d, 벅부스트 경계 %.0f %%, L %.0f µH(%.0f mJ)"
                  % (r["label"], nsw, np_, ns_, " ".join("%.0f" % x for x in L5), " ".join("%.0f" % x for x in L15),
                     r["positions"], r["devices"], 100 * r["buckboost_fraction"], r["front"]["L"] * 1e6, r["front"]["E_L"] * 1e3))
    # 선택 규칙: 대표 부하(48 V 1.5 kW) 다섯 입력 평균 손실. 차 ≤ 5 %면 모드 경계 없고 위치가 적은 A
    typ = {k: float(np.mean([x["loss"] for x in out[k + "_222"]["rows"] if x["Po"] == 1500.])) for k in CAND}
    worst = {k: max(x["loss"] for x in out[k + "_222"]["rows"] if x["Po"] == PO_MAX) for k in CAND}
    lo, hi = sorted(CAND, key=lambda k: typ[k])
    if typ[hi] <= typ[lo] * 1.05:
        choice = "A"
        reason = "대표 부하 평균 손실 차 %.1f %%(≤ 5 %%) → 모드 경계 없음, 스위치 위치 10(B 12)" % (100 * abs(typ["A"] / typ["B"] - 1))
    else:
        choice = lo
        reason = "대표 부하 평균 손실이 %.0f %% 작음" % (100 * (1 - typ[lo] / typ[hi]))
    print("  대표 부하 1.5 kW 평균 손실 A %.1f W, B %.1f W / 5 kW 최악 A %.0f W, B %.0f W → 선택 %s(%s)"
          % (typ["A"], typ["B"], worst["A"], worst["B"], choice, reason))
    es = min(x["eff"] for x in out[choice + "_222"]["rows"] if x["Po"] == PO_MAX)
    verdict("선택 구조(%s)의 5 kW 효율 ≥ 96 %%(입력 전 범위)" % choice, es >= 0.96, "최저 %.2f %%" % (100 * es))
    sel = dict(choice=choice, nsw=2, np=2, ns=2, reason=reason, worst_5kW=worst, mean_1p5kW=typ)
    save_json(EID, "design", dict(requirements=dict(VBUS=VBUS, VO_NOM=VO_NOM, VO_TOL=VO_TOL, VO_CV=VO_CV, PO_MAX=PO_MAX,
                                                    PO_REV=PO_REV, IO_MAX=IO_MAX, SLEW=SLEW, TD=TD),
                                  candidates=out, selected=sel))


# ---------------------------------------------------------------------------------------------
# dcx: 공진점 CLLC DCX 스위칭 ODE
# ---------------------------------------------------------------------------------------------
def selected():
    """design.json의 선택 구조와 부품 값(없으면 design을 먼저 실행)."""
    f = outdir(EID) / "design.json"
    if not f.exists():
        design()
    D = json.loads(f.read_text(encoding="utf-8"))
    sel = D["selected"]
    r = D["candidates"]["%s_%d%d%d" % (sel["choice"], sel["nsw"], sel["np"], sel["ns"])]
    c = dict(r["params"]); c.update(nsw=sel["nsw"], np=sel["np"], ns=sel["ns"], L=r["front"]["L"], front=r["params"]["front"])
    # 직렬 저항(1차 환산): 1차 브리지 2소자 + 권선 절반, 2차 브리지 2소자 + 권선 절반
    Ip_r = math.sqrt((math.pi * (PO_MAX / VO_NOM) / (2 * c["n"])) ** 2 / 2 + c["im_pk"] ** 2 / 3)
    Rw = K["mag_tr_cu"] * PO_MAX / Ip_r ** 2
    c["R1"] = 2 * DEV["GaN650"]["Ron"] / c["np"] + Rw / 2
    c["R2"] = c["n"] ** 2 * 2 * DEV["GaN150"]["Ron"] / c["ns"] + Rw / 2
    return c


@njit(cache=True)
def _dcx(VI, Vo, n, L1, C1, Lm, L2, C2, R1, R2, fs, td, ncyc, nstep, nlast, mode, both):
    """CLLC DCX(1차 환산). 상태 [i1, vc1, im, i2, vc2], i1 = im + i2.
    보내는 쪽 브리지: [td, T/2) +V, [T/2 + td, T) −V, 데드타임 동안 다이오드(1차 −sign(i1)·V_I, 2차 +sign(i2)·n·V_o).
    받는 쪽 브리지: 동기정류(항상 다이오드처럼: 1차 −sign(i1)·V_I, 2차 +sign(i2)·n·V_o).
    mode = +1: 1차가 보냄(V_I → 48 V), −1: 2차가 보냄(48 V → V_I). both = 1이면 두 브리지를 같은 위상으로 구동(처음 안).
    전환 순간 전류는 보내는 쪽(both면 두 브리지 각각) 기준으로 ZVS 방향을 +로 기록한다.
    반환: [P_in(1차), P_out(2차), i1 실효, i2 실효(1차 환산), im 첨두, i1 첨두, i2 첨두,
           1차 꺼짐 전류(T/2⁻, T⁻ 평균, 부호는 ZVS 방향이 +), 2차 꺼짐 전류(같음), vc1 첨두, vc2 첨두(1차 환산), 주기 평균 im]"""
    T = 1. / fs; dt = T / nstep; nd = int(round(td / dt)); half = nstep // 2
    Vs = n * Vo
    ginv = 1. / (1. / L1 + 1. / Lm + 1. / L2)
    x = np.zeros(5)
    x[2] = -VI / (4. * Lm * fs)                     # 자화 전류는 반주기 대칭에서 시작(직류분 없이)
    acc = np.zeros(12); cnt = 0
    k_tot = ncyc * nstep
    for k in range(k_tot):
        m = k % nstep
        # 브리지 상태: +1, −1, 0(데드타임)
        if m < nd:
            sp = 0
        elif m < half:
            sp = 1
        elif m < half + nd:
            sp = 0
        else:
            sp = -1
        xs = x.copy()
        kk = np.zeros((4, 5))
        for st in range(4):
            if st == 0:
                y = xs
            elif st == 3:
                y = xs + dt * kk[2]
            else:
                y = xs + 0.5 * dt * kk[st - 1]
            i1 = y[2] + y[3]
            vp = -VI if i1 > 0. else VI                 # 다이오드(데드타임 또는 동기정류)
            vs = Vs if y[3] > 0. else -Vs
            if sp != 0:
                if mode > 0 or both == 1:
                    vp = sp * VI
                if mode < 0 or both == 1:
                    vs = sp * Vs
            vm = ((vp - y[1] - R1 * i1) / L1 + (y[4] + R2 * y[3] + vs) / L2) * ginv
            kk[st, 0] = 0.
            kk[st, 1] = i1 / C1
            kk[st, 2] = vm / Lm
            kk[st, 3] = (vm - y[4] - R2 * y[3] - vs) / L2
            kk[st, 4] = y[3] / C2
        x = xs + dt / 6. * (kk[0] + 2. * kk[1] + 2. * kk[2] + kk[3])
        if k >= k_tot - nlast * nstep:
            i1 = x[2] + x[3]
            vp = -VI if i1 > 0. else VI
            vs = Vs if x[3] > 0. else -Vs
            if sp != 0:
                if mode > 0 or both == 1:
                    vp = sp * VI
                if mode < 0 or both == 1:
                    vs = sp * Vs
            acc[0] += vp * i1
            acc[1] += vs * x[3]
            acc[2] += i1 * i1
            acc[3] += x[3] * x[3]
            acc[4] = max(acc[4], abs(x[2]))
            acc[5] = max(acc[5], abs(i1))
            acc[6] = max(acc[6], abs(x[3]))
            if m == half - 1:                    # 양의 상태 끝: 1차는 i1 > 0, 2차는 i2 < 0이어야 ZVS
                acc[7] += i1; acc[8] += -x[3]; cnt += 1
            elif m == nstep - 1:                 # 음의 상태 끝: 1차는 i1 < 0, 2차는 i2 > 0
                acc[7] += -i1; acc[8] += x[3]; cnt += 1
            acc[9] = max(acc[9], abs(x[1]))
            acc[10] = max(acc[10], abs(x[4]))
            acc[11] += x[2]
    N = nlast * nstep
    out = np.zeros(12)
    out[0] = acc[0] / N; out[1] = acc[1] / N
    out[2] = math.sqrt(acc[2] / N); out[3] = math.sqrt(acc[3] / N)
    out[4] = acc[4]; out[5] = acc[5]; out[6] = acc[6]
    out[7] = acc[7] / max(cnt, 1); out[8] = acc[8] / max(cnt, 1)
    out[9] = acc[9]; out[10] = acc[10]; out[11] = acc[11] / N
    return out


def dcx_point(c, VI, Vo, mode=1, both=0, ncyc=400, nstep=400, nlast=20):
    L1 = c["Lr"]; C1 = c["Cr"]; L2 = c["Lr"]; C2 = c["Cr"]           # 대칭 공진망(1차 환산)
    r = _dcx(VI, Vo, c["n"], L1, C1, c["Lm"], L2, C2, c["R1"], c["R2"], c["fr"], TD, ncyc, nstep, nlast, mode, both)
    return dict(VI=VI, Vo=Vo, Pin=r[0], Pout=r[1], I1=r[2], I2=r[3], Im_pk=r[4], I1_pk=r[5], I2_pk=r[6],
                isw1=r[7], isw2=r[8], vc1_pk=r[9], vc2_pk=r[10], im_mean=r[11])


def dcx_solve(c, Po, Vo, both=0):
    """P_out = Po가 되는 V_I(할선법). 보내는 쪽은 Po의 부호로 고른다(Po ≥ 0이면 1차)."""
    V0 = c["n"] * Vo
    mode = 1 if Po >= 0 else -1
    f = lambda VI: dcx_point(c, VI, Vo, mode, both)["Pout"] - Po
    a, b = V0 * (1 + 0.002 * np.sign(Po + 1e-9)), V0 * (1 + 0.02 * np.sign(Po + 1e-9))
    fa, fb = f(a), f(b)
    for _ in range(30):
        if abs(fb) < 2. or abs(b - a) < 1e-4:
            break
        a, b, fa = b, b - fb * (b - a) / (fb - fa), fb
        fb = f(b)
    r = dcx_point(c, b, Vo, mode, both)
    r["mode"] = mode
    return r


def dcx():
    c = selected()
    print("  DCX: n %.2f, L_r %.2f µH, C_r %.1f nF, L_m %.1f µH, f_r %.0f kHz, R1 %.1f mΩ, R2' %.1f mΩ(1차 환산)"
          % (c["n"], c["Lr"] * 1e6, c["Cr"] * 1e9, c["Lm"] * 1e6, c["fr"] / 1e3, c["R1"] * 1e3, c["R2"] * 1e3))
    izp = lambda VI: zvs_current(VI, c["np"])
    izs = lambda Vo: 2 * c["ns"] * DEV["GaN150"]["Ctr"] * Vo / TD / c["n"]          # 2차 ZVS 전류(1차 환산)
    # 처음 안(두 브리지 같은 위상 구동)의 대표 점: ZVS가 깨지는 근거로 남긴다
    first = []
    for Po in (PO_REV, 0., PO_MAX):
        r = dcx_solve(c, Po, VO_NOM, both=1)
        first.append(dict(Po=Po, VI=r["VI"], zvs1=r["isw1"] / izp(r["VI"]), zvs2=r["isw2"] / izs(VO_NOM)))
    print("  (처음 안: 두 브리지 같은 위상) ZVS 여유 1차·2차: " + ", ".join("%.0f W %.2f·%.2f" % (x["Po"], x["zvs1"], x["zvs2"]) for x in first))
    rows = []
    for Vo in (VO_CV[0], VO_NOM, VO_CV[1]):
        Pmax = min(PO_MAX, IO_MAX * Vo)
        for Po in (PO_REV, -1500., -200., 100., 500., 1500., 3000., Pmax):
            r = dcx_solve(c, Po, Vo)
            fwd = r["mode"] > 0
            zs = r["isw1"] / izp(r["VI"]) if fwd else r["isw2"] / izs(Vo)
            r.update(Po=Po, gain=c["n"] * Vo / r["VI"], zvs_send=zs,
                     i_recv_sw=(r["isw2"] if fwd else r["isw1"]),
                     eff=(r["Pout"] / r["Pin"]) if Po > 0 else (r["Pin"] / r["Pout"] if Po < 0 else float("nan")))
            rows.append(r)
            print("  V_o %4.1f V P %6.0f W(%s): V_I %6.2f V 이득 %.4f, 보내는 쪽 ZVS 여유 %5.2f, I1 %5.2f A, I2' %5.2f A(2차 %5.1f A),"
                  " im %.2f A, vc1 %4.0f V, vc2 %4.1f V(2차), 효율 %.4f"
                  % (Vo, Po, "1차→2차" if fwd else "2차→1차", r["VI"], r["gain"], zs, r["I1"], r["I2"], r["I2"] * c["n"], r["Im_pk"],
                     r["vc1_pk"], r["vc2_pk"] / c["n"], r["eff"]))
    g = [r["gain"] for r in rows]
    verdict("(dcx) 이득 1 ± 3 %(−3–5 kW, V_o 36·48·52 V)", all(abs(x - 1) <= 0.03 for x in g), "%.4f–%.4f" % (min(g), max(g)))
    z = min(r["zvs_send"] for r in rows)
    verdict("(dcx) 보내는 쪽 브리지 ZVS 여유 ≥ 1(모든 점)", z >= 1., "최소 %.2f" % z)
    save_json(EID, "dcx", dict(params=c, rows=rows, gain_range=[min(g), max(g)], zvs_min=z, first_try=first))


# ---------------------------------------------------------------------------------------------
# control: 전단 벅 + DCX 평균모델과 디지털 제어
# ---------------------------------------------------------------------------------------------
CI = 20e-6           # 중간 커패시터(필름) [F]
CO = 2.2e-3          # 48 V 출력 커패시터 [F](처음 1 mF: 계단 부하에서 52.9 V, 결과 참조)
FS_CTRL = 100e3      # 제어 표본(= 벅 스위칭 주파수) [Hz]
FCI = 5e3            # 전류 루프 교차 [Hz]
FCV = 1e3            # 전압 루프 교차 [Hz]
HYST = 0.5           # DCX 방향 전환 히스테리시스(인덕터 전류 지령) [A]
B_SP = 0.7           # 전류 PI 비례항의 지령 가중(1 = 보통 PI. 1이면 계단 지령에서 15 % 넘침, 0.5면 270 V 계단에서 붕괴)
DMAX = 0.97          # 벅 최대 듀티(부트스트랩 충전 시간)
IBAT_MAX = 30.       # 48 V 배터리 충전전류 제한 [A]
BAT = dict(OCV=47.0, R=0.02)   # 48 V 배터리 등가(13s 리튬이온 중간 SOC 부근, 내부저항 20 mΩ)


def dcx_equiv(c):
    """DCX 평균 등가(48 V 쪽 환산): R_x = 5 kW·48 V의 (V_I/n − V_o)/I_o(dcx 결과), L_x = 계단 응답 시정수 × R_x.
    계단 응답: V_I 고정 계단에서 주기 평균 출력전력이 63 %에 이르는 시간(13주기 ≈ 52 µs, dcx와 같은 ODE)."""
    D = json.loads((outdir(EID) / "dcx.json").read_text(encoding="utf-8"))
    r5 = [r for r in D["rows"] if r["Vo"] == VO_NOM and r["Po"] == PO_MAX][0]
    Rx = (r5["VI"] / c["n"] - VO_NOM) / (r5["Pout"] / VO_NOM)
    r3 = [r for r in D["rows"] if r["Vo"] == VO_NOM and r["Po"] == 3000.][0]
    P = [dcx_point(c, r3["VI"], VO_NOM, 1, 0, ncyc=k, nstep=400, nlast=1)["Pout"] for k in range(1, 61)]
    k63 = next(k for k, p in enumerate(P, 1) if p >= 0.632 * P[-1])
    tau = k63 / c["fr"]
    return dict(Rx=Rx, Lx=tau * Rx, tau=tau, P_step=P)


def gains(c, eq):
    """PI 이득: 전류 루프 K_p = 2πf_ci·L, T_i = 5/(2πf_ci). 전압 루프(출력 쪽 전류 지령) K_p = 2πf_cv·C_tot,
    C_tot = C_o + n²·C_I, T_i = 5/(2πf_cv)."""
    wci = 2 * math.pi * FCI; wcv = 2 * math.pi * FCV
    Kpi = wci * c["L"]; Kii = Kpi * wci / 5.
    Ctot = CO + c["n"] ** 2 * CI
    Kpv = wcv * Ctot; Kiv = Kpv * wcv / 5.
    return dict(Kpi=Kpi, Kii=Kii, Kpv=Kpv, Kiv=Kiv, Ctot=Ctot, Kpb=0.5, Kib=2 * math.pi * 300 * 0.5, b=B_SP)


@njit(cache=True)
def _interp(t, tt, yy):
    if t <= tt[0]:
        return yy[0]
    for k in range(1, tt.size):
        if t <= tt[k]:
            return yy[k - 1] + (yy[k] - yy[k - 1]) * (t - tt[k - 1]) / (tt[k] - tt[k - 1])
    return yy[-1]


@njit(cache=True)
def _avg(prm, ctl, tP, PP, tV, VV, bat, inj, T_end, dt, dec):
    """평균모델. prm = [L, R_L, C_I, n, L_x, R_x, C_o, V_ref], ctl = [T_s, K_pi, K_ii, K_pv, K_iv, I_fwd(과도), I_rev, 앞먹임, 히스, d_max,
    K_pb, K_ib, I_bat_max, I_정격, T_OL, 지령 가중 b], bat = [켬, OCV, R_b], inj = [진폭 V, 주파수 Hz](버스 정현 섭동).
    반환 행: [t, v_bus, i_L, v_I, i_x, v_o, d, 방향, i_bat, i_in, p_load, i_L 지령]"""
    L, RL, CIx, n, Lx, Rx, Co, Vref = prm[0], prm[1], prm[2], prm[3], prm[4], prm[5], prm[6], prm[7]
    Ts = ctl[0]
    N = int(T_end / dt); ns = int(round(Ts / dt))
    out = np.zeros((N // dec + 1, 12))
    # 초기 정상상태(시작 시각의 부하·버스)
    vb0 = _interp(0., tV, VV); p0 = _interp(0., tP, PP)
    vo = Vref
    ib = (vo - bat[1]) / bat[2] if bat[0] > 0 else 0.
    ix = p0 / vo + ib
    vI = n * (vo + Rx * ix)
    iL = ix / n
    d = (vI + RL * iL) / vb0
    mode = 1 if iL >= 0. else -1
    Iv = ix                                   # 전압 PI 적분(출력 쪽 전류 지령 단위)
    Ii = 0.                                   # 전류 PI 적분(전압 단위)
    Ib = 0.                                   # 충전전류 루프 적분(출력전류 단위)
    tol = 0.                                  # 정격 초과 누적 시간(과부하 시간 제한)
    d_next = d; iref = iL
    if ctl[7] > 0:
        Iv = ix - (p0 / vo + ib)              # 앞먹임이 있으면 적분은 0 근처
    j = 0
    for k in range(N):
        t = k * dt
        vb = _interp(t, tV, VV) + inj[0] * math.sin(2. * math.pi * inj[1] * t)
        pl = _interp(t, tP, PP)
        if k % ns == 0:                       # 디지털 제어 표본: 이번에 계산한 듀티는 다음 표본부터 적용(계산 지연 1주기)
            d = d_next
            ib = (vo - bat[1]) / bat[2] if bat[0] > 0 else 0.
            iload = pl / vo
            iout = iload + ib
            ev = Vref - vo
            ff = iload if ctl[7] > 0 else 0.                                  # 앞먹임은 부하전류만(배터리 전류를 넣으면 양의 되먹임)
            ixv = ctl[3] * ev + Iv + ctl[4] * ev * Ts + ff                     # 전압 루프 지령(적분 후보 포함)
            sel = 0                                                            # 0 전압, 1 충전 제한, 2 상한, 3 하한
            ixr = ixv
            if bat[0] > 0:                    # 충전전류 루프: 지령 = 부하전류 + 충전 제한 + PI(제한 − i_bat)
                eb = ctl[12] - ib
                ixb = iload + ctl[12] + ctl[10] * eb + Ib
                if ixb < ixr:
                    ixr = ixb; sel = 1
                    Ib += ctl[11] * eb * Ts
                else:
                    Ib = 0.
            dem = ixr                                       # 제한 전 수요
            lim = ctl[5] if tol < ctl[14] else ctl[13]      # 과부하 시간 제한: 과도 130 A, 2 ms 넘으면 정격
            if ixr > lim:
                ixr = lim; sel = 2
            elif ixr < -ctl[6]:
                ixr = -ctl[6]; sel = 3
            if dem > ctl[13]:                 # 과부하 시간: 제한 전 수요가 정격을 넘은 시간(제한 뒤 값으로 세면 제한이 들락날락한다)
                tol += Ts
            else:
                tol = max(0., tol - Ts)
            # 적분 누적 방지(조건부 적분): 전압 루프가 선택됐거나, 제한을 벗어나는 방향이 아닐 때만 적분
            if sel == 0 or (sel == 2 and ev < 0.) or (sel == 3 and ev > 0.):
                Iv += ctl[4] * ev * Ts
            elif sel == 1:                    # 충전 제한 중에는 전압 적분이 지령을 따라가게 둔다(전환 때 튀지 않게)
                Iv = min(Iv, ixr - ctl[3] * ev - ff)
            iref = ixr / n
            if iref > ctl[8]:
                mode = 1
            elif iref < -ctl[8]:
                mode = -1
            ei = iref - iL
            u = vI + ctl[1] * (ctl[15] * iref - iL) + Ii + ctl[2] * ei * Ts      # 비례항 지령 가중 b(계단 지령의 넘침 줄임)
            dn = u / vb
            if dn > ctl[9]:
                dn = ctl[9]
                if ei < 0.:
                    Ii += ctl[2] * ei * Ts            # 포화 방향이 아닐 때만 적분(조건부 적분)
            elif dn < 0.02:
                dn = 0.02
                if ei > 0.:
                    Ii += ctl[2] * ei * Ts
            else:
                Ii += ctl[2] * ei * Ts
            d_next = dn
        # 연속 상태(전진 오일러, dt = 0.05 µs)
        ib = (vo - bat[1]) / bat[2] if bat[0] > 0 else 0.
        il = pl / vo
        diL = (d * vb - vI - RL * iL) / L
        dvI = (iL - ix / n) / CIx
        dix = (vI / n - vo - Rx * ix) / Lx
        dvo = (ix - il - ib) / Co
        iL += diL * dt; vI += dvI * dt; ix += dix * dt; vo += dvo * dt
        if mode > 0 and ix < 0.:               # 받는 쪽 동기정류: 보내는 방향과 반대 전류는 흐르지 않는다
            ix = 0.
        elif mode < 0 and ix > 0.:
            ix = 0.
        if k % dec == 0:
            out[j, 0] = t; out[j, 1] = vb; out[j, 2] = iL; out[j, 3] = vI; out[j, 4] = ix; out[j, 5] = vo
            out[j, 6] = d; out[j, 7] = mode; out[j, 8] = ib; out[j, 9] = d * iL; out[j, 10] = pl; out[j, 11] = iref
            j += 1
    return out[:j]


def run_avg(c, eq, g, tP, PP, tV, VV, battery=False, T_end=8e-3, inj=(0., 0.), Vref=VO_NOM, dt=0.05e-6, dec=20, ff=True):
    prm = np.array([c["L"], K["mag_ind_cu"] * PO_MAX / (PO_MAX * 1.03 / (c["n"] * VO_NOM)) ** 2, CI, c["n"], eq["Lx"], eq["Rx"], CO, Vref])
    ctl = np.array([1 / FS_CTRL, g["Kpi"], g["Kii"], g["Kpv"], g["Kiv"], I_LIM, -PO_REV / VO_CV[0] * 1.1, 1. if ff else 0., HYST, DMAX,
                    g["Kpb"], g["Kib"], IBAT_MAX, IO_MAX, T_OL, g["b"]])
    bat = np.array([1. if battery else 0., BAT["OCV"], BAT["R"]])
    return _avg(prm, ctl, np.asarray(tP, float), np.asarray(PP, float), np.asarray(tV, float), np.asarray(VV, float),
                bat, np.asarray(inj, float), T_end, dt, dec)


def metrics(Z, t0, sat_ms=0.5, Ts=1 / FS_CTRL):
    q = Z[:, 0] >= t0
    vo = Z[q, 5]
    dsat = np.mean((Z[q, 6] >= DMAX - 1e-9) | (Z[q, 6] <= 0.02 + 1e-9)) * (Z[q, 0][-1] - Z[q, 0][0]) * 1e3
    flips = int(np.sum(np.abs(np.diff(Z[q, 7])) > 0))
    ixq = Z[q, 4]; dtz = Z[1, 0] - Z[0, 0]; w = max(1, int(round(100e-6 / dtz)))
    ixa = np.convolve(ixq, np.ones(w) / w, mode="valid")
    return dict(ix_avg100_max=float(np.abs(ixa).max()), ix_dev_peak=float(math.pi / 2 * np.abs(ixq).max() / 2),
                vo_min=float(vo.min()), vo_max=float(vo.max()), dev_pct=float(100 * max(abs(vo.min() - VO_NOM), abs(vo.max() - VO_NOM)) / VO_NOM),
                iL_max=float(np.abs(Z[q, 2]).max()), ix_max=float(Z[q, 4].max()), ix_min=float(Z[q, 4].min()),
                vI_max=float(Z[q, 3].max()), sat_ms=float(dsat), flips=flips, ibat_max=float(Z[q, 8].max()), ibat_min=float(Z[q, 8].min()),
                vo_end=float(Z[-1, 5]))


def ix_late(Z, t0, t1):
    """[t0, t1] 구간 출력전류 100 µs 이동평균의 최대 크기(과부하 시간 제한 뒤 정격 확인)."""
    q = (Z[:, 0] >= t0) & (Z[:, 0] <= t1)
    dtz = Z[1, 0] - Z[0, 0]; w = max(1, int(round(100e-6 / dtz)))
    return float(np.abs(np.convolve(Z[q, 4], np.ones(w) / w, mode="valid")).max())


def zbus(f):
    """R2 기본형 버스 임피던스(TB08–TB13과 같은 등가): V_A(이상) + R 13.2 mΩ + L 1.5 µH ∥ C_b 400 µF ∥ (1.6 mF + 48.6 mΩ)."""
    w = 2j * math.pi * f
    Zs = 0.0132 + w * 1.5e-6
    Y = 1 / Zs + w * 400e-6 + 1 / (0.0486 + 1 / (w * 1.6e-3))
    return 1 / Y


def control():
    c = selected(); eq = dcx_equiv(c); g = gains(c, eq)
    print("  평균 등가: R_x %.2f mΩ, L_x %.3f µH(τ %.1f µs), C_I %.0f µF, C_o %.1f mF, L %.0f µH / 이득 K_pi %.2f, K_pv %.2f(C_tot %.2f mF)"
          % (eq["Rx"] * 1e3, eq["Lx"] * 1e6, eq["tau"] * 1e6, CI * 1e6, CO * 1e3, c["L"] * 1e6, g["Kpi"], g["Kpv"], g["Ctot"] * 1e3))
    res = dict(equiv=dict(Rx=eq["Rx"], Lx=eq["Lx"], tau=eq["tau"]), gains=g, CI=CI, CO=CO, tests={})
    ok_all = {}
    T = res["tests"]
    # T1 정상 조정
    t1 = []
    for Vb in VBUS_GRID:
        for P in (PO_REV, 100., 1500., PO_MAX):
            Z = run_avg(c, eq, g, [0, 1], [P, P], [0, 1], [Vb, Vb], T_end=6e-3)
            q = Z[:, 0] > 5e-3
            err = float(100 * abs(Z[q, 5].mean() - VO_NOM) / VO_NOM)
            t1.append(dict(Vbus=Vb, P=P, err_pct=err, d=float(Z[q, 6].mean()), vI=float(Z[q, 3].mean()), iL=float(Z[q, 2].mean())))
    T["T1"] = t1
    ok_all["T1"] = max(x["err_pct"] for x in t1) <= 0.1
    verdict("(control T1) 정상 오차 ≤ 0.1 %(입력 5점 × 전력 4점)", ok_all["T1"], "최대 %.3f %%" % max(x["err_pct"] for x in t1))
    # T2 계약 부하 변화(4 kW/ms)
    t2 = []
    for Vb in VBUS_GRID:
        for P0, P1 in ((100., PO_MAX), (PO_MAX, 100.), (PO_REV, PO_MAX), (PO_MAX, PO_REV)):
            tr = abs(P1 - P0) / SLEW
            Z = run_avg(c, eq, g, [0, 2e-3, 2e-3 + tr, 1], [P0, P0, P1, P1], [0, 1], [Vb, Vb], T_end=2e-3 + tr + 4e-3)
            m = metrics(Z, 1.5e-3); m.update(Vbus=Vb, P0=P0, P1=P1)
            t2.append(m)
    T["T2"] = t2
    w2 = max(x["dev_pct"] for x in t2)
    ok_all["T2"] = w2 <= 2. and max(x["sat_ms"] for x in t2) <= 0.5
    verdict("(control T2) 계약 부하 변화 4 kW/ms에서 48 V ±2 %", ok_all["T2"], "최대 편차 %.2f %%" % w2)
    # T3 계단 부하(견고성)
    t3 = []
    for Vb in VBUS_GRID:
        for P0, P1 in ((100., PO_MAX), (PO_MAX, 100.), (PO_MAX, PO_REV), (PO_REV, PO_MAX)):
            Z = run_avg(c, eq, g, [0, 2e-3, 2e-3 + 1e-9, 1], [P0, P0, P1, P1], [0, 1], [Vb, Vb], T_end=7e-3)
            m = metrics(Z, 1.5e-3); m.update(Vbus=Vb, P0=P0, P1=P1, ix_late=ix_late(Z, 4.5e-3, 7e-3))
            t3.append(m)
    T["T3"] = t3
    def cur_ok(L):
        return (max(x["ix_avg100_max"] for x in L) <= I_LIM * 1.05 and max(x["ix_late"] for x in L) <= IO_MAX * 1.05
                and max(x["ix_dev_peak"] for x in L) <= ID_PULSE_S)

    def cur_txt(L):
        return "출력 100 µs 평균 최대 %.1f A, 2.5 ms 뒤 %.1f A, 2차 소자 순간 %.0f A(순간 i_x %.0f A)" % (
            max(x["ix_avg100_max"] for x in L), max(x["ix_late"] for x in L), max(x["ix_dev_peak"] for x in L), max(x["ix_max"] for x in L))
    ok_all["T3"] = (min(x["vo_min"] for x in t3) >= VO_CV[0] and max(x["vo_max"] for x in t3) <= VO_CV[1]
                    and max(x["sat_ms"] for x in t3) <= 0.5 and cur_ok(t3))
    verdict("(control T3) 계단 부하(배터리 없음)에서 36–52 V, 전류 제한", ok_all["T3"], "%.2f–%.2f V, 최대 편차 %.2f %%, %s" % (
        min(x["vo_min"] for x in t3), max(x["vo_max"] for x in t3), max(x["dev_pct"] for x in t3), cur_txt(t3)))
    # T4 버스 계단 ±50 V / 10 µs
    t4 = []
    for P in (PO_REV, 100., PO_MAX):
        for V0, V1 in ((320., 270.), (270., 320.), (454., 504.), (504., 454.)):
            Z = run_avg(c, eq, g, [0, 1], [P, P], [0, 2e-3, 2e-3 + 10e-6, 1], [V0, V0, V1, V1], T_end=6e-3)
            m = metrics(Z, 1.5e-3); m.update(P=P, V0=V0, V1=V1)
            t4.append(m)
    T["T4"] = t4
    w4 = max(x["dev_pct"] for x in t4)
    ok_all["T4"] = w4 <= 2. and max(x["sat_ms"] for x in t4) <= 0.5
    verdict("(control T4) 버스 계단 ±50 V/10 µs에서 48 V ±2 %", ok_all["T4"], "최대 편차 %.2f %%" % w4)
    # T5 배터리 연결: 충전 제한, 부하 계단 0.1 → 5 → 0.1 kW
    t5 = []
    for Vb in (270., 400., 504.):
        for ocv in (44.0, 47.0, 47.9):
            BAT["OCV"] = ocv
            Z = run_avg(c, eq, g, [0, 3e-3, 3e-3 + 1e-9, 8e-3, 8e-3 + 1e-9, 1], [100., 100., PO_MAX, PO_MAX, 100., 100.],
                        [0, 1], [Vb, Vb], battery=True, T_end=14e-3)
            m = metrics(Z, 2e-3); m.update(Vbus=Vb, OCV=ocv, ix_late=ix_late(Z, 5.5e-3, 8e-3))
            q = Z[:, 0] > 7e-3
            m["ibat_at_5kW"] = float(Z[q & (Z[:, 0] < 8e-3), 8].mean())
            m["ibat_after1ms"] = float(Z[Z[:, 0] >= 9e-3, 8].max())             # 부하 해제(8 ms) 1 ms 뒤 충전전류 최대
            m["ibat_end"] = float(Z[-200:, 8].mean())
            t5.append(m)
        for P0, P1 in ((PO_REV, PO_MAX), (PO_MAX, PO_REV)):
            BAT["OCV"] = 47.0
            Z = run_avg(c, eq, g, [0, 3e-3, 3e-3 + 1e-9, 1], [P0, P0, P1, P1], [0, 1], [Vb, Vb], battery=True, T_end=8e-3)
            m = metrics(Z, 2e-3); m.update(Vbus=Vb, OCV=47.0, P0=P0, P1=P1, ix_late=ix_late(Z, 5.5e-3, 8e-3))
            m["ibat_at_5kW"] = float("nan"); m["ibat_after1ms"] = float(Z[Z[:, 0] >= 4e-3, 8].max()); m["ibat_end"] = float(Z[-200:, 8].mean())
            t5.append(m)
    BAT["OCV"] = 47.0
    T["T5"] = t5
    ok_all["T5"] = (min(x["vo_min"] for x in t5) >= VO_CV[0] and max(x["vo_max"] for x in t5) <= VO_CV[1]
                    and max(x["ibat_after1ms"] for x in t5) <= IBAT_MAX * 1.05 and cur_ok(t5))
    verdict("(control T5) 배터리 연결: 36–52 V, 충전 ≤ %.0f A(1 ms 뒤), 전류 제한" % IBAT_MAX, ok_all["T5"],
            "%.2f–%.2f V, 1 ms 뒤 충전 최대 %.1f A, %s" % (min(x["vo_min"] for x in t5), max(x["vo_max"] for x in t5),
                                                 max(x["ibat_after1ms"] for x in t5), cur_txt(t5)))
    # T6 방향 전환(−3 → +3 → −3 kW, 1 kW/ms)
    t6 = []
    for Vb in VBUS_GRID:
        Z = run_avg(c, eq, g, [0, 2e-3, 8e-3, 14e-3, 1], [-3000., -3000., 3000., -3000., -3000.], [0, 1], [Vb, Vb], T_end=16e-3)
        m = metrics(Z, 1.5e-3); m.update(Vbus=Vb)
        t6.append(m)
    T["T6"] = t6
    w6 = max(x["dev_pct"] for x in t6)
    ok_all["T6"] = w6 <= 2.
    verdict("(control T6) 전력 방향 전환에서 48 V ±2 %", ok_all["T6"], "최대 편차 %.2f %%, 전환 %d회" % (w6, max(x["flips"] for x in t6)))
    # T7 입력 임피던스(버스 정현 섭동 1 V) 대 버스 임피던스
    t7 = []
    for Vb in (270., 504.):
        for f in (10., 30., 100., 300., 1e3, 3e3, 1e4, 2e4):
            Tsim = max(6e-3, 2e-3 + 10 / f)
            Z = run_avg(c, eq, g, [0, 1], [PO_MAX, PO_MAX], [0, 1], [Vb, Vb], T_end=Tsim, inj=(1.0, f), dec=4)
            q = Z[:, 0] >= Tsim - math.ceil(5 * f * 1e-3) / f if f >= 1e3 else Z[:, 0] >= Tsim - 5 / f
            tt = Z[q, 0]; e = np.exp(-2j * math.pi * f * tt)
            V = np.sum((Z[q, 1] - Z[q, 1].mean()) * e); I = np.sum((Z[q, 9] - Z[q, 9].mean()) * e)
            Zin = V / I
            zb = zbus(f)
            t7.append(dict(Vbus=Vb, f=f, Zin_abs=float(abs(Zin)), Zin_deg=float(np.degrees(np.angle(Zin))), Zbus_abs=float(abs(zb)),
                           margin_db=float(20 * np.log10(abs(Zin) / abs(zb)))))
    T["T7"] = t7
    mm = min(x["margin_db"] for x in t7)
    ok_all["T7"] = mm >= 6.
    verdict("(control T7) |Z_bus| ≤ |Z_in|/2(10 Hz–20 kHz, 5 kW)", ok_all["T7"], "최소 여유 %.1f dB" % mm)
    res["ok"] = ok_all
    save_json(EID, "control", res)


# ---------------------------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------------------------
def figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    D = json.loads((outdir(EID) / "design.json").read_text(encoding="utf-8"))
    X = json.loads((outdir(EID) / "dcx.json").read_text(encoding="utf-8"))
    Q = json.loads((outdir(EID) / "control.json").read_text(encoding="utf-8"))
    c = selected(); eq = dcx_equiv(c); g = gains(c, eq)
    fig, ax = plt.subplots(2, 3, figsize=(16, 8.4))
    # (a) 후보 손실
    a = ax[0, 0]
    for key, col in (("A_222", C["blue"]), ("B_222", C["orange"])):
        r = D["candidates"][key]
        for P, ls in ((PO_MAX, "-"), (1500., "--")):
            rows = [x for x in r["rows"] if x["Po"] == P]
            a.plot([x["Vbus"] for x in rows], [x["loss"] for x in rows], ls, color=col, marker="o", ms=3,
                   label="%s, %.1f kW" % (r["label"], P / 1e3))
    a.set_xlabel("입력(버스) 전압 [V]"); a.set_ylabel("Stage C 손실 [W]"); a.set_title("(a) 후보 구조 손실(같은 병렬 2·2·2)", fontsize=9)
    a.legend(fontsize=7)
    # (b) DCX 이득과 ZVS 여유
    a = ax[0, 1]; a2 = a.twinx()
    for Vo, col in ((VO_CV[0], C["gray"]), (VO_NOM, C["blue"]), (VO_CV[1], C["green"])):
        rows = sorted([r for r in X["rows"] if r["Vo"] == Vo], key=lambda r: r["Po"])
        a.plot([r["Po"] / 1e3 for r in rows], [r["gain"] for r in rows], "-o", ms=3, color=col, label="이득, V_o %.0f V" % Vo)
        a2.plot([r["Po"] / 1e3 for r in rows], [r["zvs_send"] for r in rows], ":s", ms=3, color=col)
    a.axhspan(0.97, 1.03, color=C["green"], alpha=0.08); a2.axhline(1, color=C["red"], ls=":", lw=.8)
    a.set_xlabel("48 V 쪽 전력 [kW](음수 = 회생)"); a.set_ylabel("이득 n·V_o/V_I"); a2.set_ylabel("보내는 쪽 ZVS 여유(점선)")
    a.set_title("(b) CLLC DCX(4.8:1): 이득과 ZVS 여유", fontsize=9); a.legend(fontsize=7, loc="lower left")
    # (c)(d)(e) 시간 응답
    cases = [("(c) 배터리 없음, 0.1 → 5 kW 계단", [100., PO_MAX], False), ("(d) 배터리 없음, −3 → +5 kW 계단", [PO_REV, PO_MAX], False),
             ("(e) 배터리 연결(OCV 47 V), 0.1 → 5 kW 계단", [100., PO_MAX], True)]
    for k, (title, (P0, P1), bat) in enumerate(cases):
        a = ax[1, k]
        for Vb, col in ((270., C["red"]), (400., C["blue"]), (504., C["green"])):
            BAT["OCV"] = 47.0
            Z = run_avg(c, eq, g, [0, 2e-3, 2e-3 + 1e-9, 1], [P0, P0, P1, P1], [0, 1], [Vb, Vb], battery=bat, T_end=5e-3, dec=10)
            a.plot((Z[:, 0] - 2e-3) * 1e3, Z[:, 5], color=col, lw=1.1, label="V_o, 입력 %.0f V" % Vb)
        a.axhspan(VO_NOM * 0.98, VO_NOM * 1.02, color=C["green"], alpha=0.08); a.axhline(VO_CV[0], color=C["red"], ls=":", lw=.8)
        a.set_xlim(-0.2, 2.5); a.set_xlabel("계단 뒤 시간 [ms]"); a.set_ylabel("48 V 출력 [V]"); a.set_ylim(35, 53)
        a.set_title(title, fontsize=9); a.legend(fontsize=7, loc="lower right")
    # (f) 입력 임피던스 대 버스 임피던스
    a = ax[0, 2]
    for Vb, col in ((270., C["red"]), (504., C["green"])):
        rows = [x for x in Q["tests"]["T7"] if x["Vbus"] == Vb]
        a.loglog([x["f"] for x in rows], [x["Zin_abs"] for x in rows], "-o", ms=3, color=col, label="|Z_in| Stage C 5 kW, 입력 %.0f V" % Vb)
    fz = np.logspace(1, np.log10(2e4), 100)
    a.loglog(fz, [abs(zbus(f)) for f in fz], color="k", lw=1.2, label="|Z_bus| R2 기본형 버스")
    a.set_xlabel("주파수 [Hz]"); a.set_ylabel("[Ω]"); a.set_title("(f) 입력 임피던스와 버스 임피던스(Middlebrook)", fontsize=9)
    a.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(outdir(EID) / "E22_stage_c_regulated.png", dpi=150); plt.close(fig)
    print("  figures saved")


PARTS = dict(design=design, dcx=dcx, control=control, figures=figures)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E22 %s ====" % w)
        PARTS[w]()
