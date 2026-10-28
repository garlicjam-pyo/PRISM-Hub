"""[E31] Stage A 출력용량(C_oss) 손실 재평가와 설계 수정안.

■ 발견 경위
  부품 정격 표를 만들려고 Stage A 스위치 후보의 데이터시트(출력용량)를 확인하다가, E1 손실 모델의 출력용량 항
  4·E_oss·f_s(E_oss = 24 µJ, 위상당 약 14 W)가 현상과 크기를 모두 작게 잡았음을 알았다.
  (1) 현상: Stage A는 영전류(ZCS)에서 끄고 데드타임 동안 전류가 0이라, 스위치 노드 전압(V_bat/2 = 320–460 V)을 옮길
      전류가 없다. 다음 반주기 스위치가 켜질 때 노드 용량을 하드 스위칭으로 충·방전한다. 노드 한 번의 전이에서 잃는
      에너지는 켜지는 스위치의 저장 에너지 E_oss(자기 방전) + 꺼진 쪽 충전 손실(Q_oss·V − E_oss) = Q_oss(V)·V 이다.
      위상당 한 주기에 노드 전이가 4번(스위치 4개가 한 번씩 켜짐) 있으므로 P_oss = 4·Q_oss,pos(V_bat/2)·(V_bat/2)·f_s.
      E_oss만 세면 SiC에서 3–4배 작다(Q·V / E_oss = 2·C_o(tr)/C_o(er)).
  (2) 크기: 위치당 6 mΩ(125 °C)를 750 V SiC로 만들면 위치당 Q_oss(400 V) ≈ 0.6–0.75 µC다. E_oss 24 µJ는 수십 mΩ급
      소자 하나의 값이다.
  → 원설계(150 kHz)의 출력용량 손실은 위상당 100 W를 넘는다(모델 14 W). E15·E25의 Stage A 손실, 특히 주행 보조 경로와
    400 V급 충전 손실 결론이 바뀔 수 있다. 이 실험은 그 영향을 정량하고, 이미 검증한 제어(영전류 턴오프, E24·E28 위상
    셰딩)만으로 성립하는 설계 수정안을 찾는다.

■ 계산 방법
  A. 물리 확인: 노드 용량을 넣은 RSC 한 위상의 정확한 구간선형 해(행렬 지수, 노드마다 2·C_pos)로 무부하 손실을 구해
     4·C·(V_bat/2)²·f_s와 비교한다. Q_oss가 비선형이어도 손실은 (전이 전하) × (전압)이므로 등가 C = Q_oss(V)/V로 같다.
  B. 소자 데이터(data/datasheets/*.json, 데이터시트 표 값만): C_o(tr)·C_o(er)로 Q_oss(V) = C_tr·V_s·(V/V_s)^m,
     m = r/(1 − r), r = C_er/(2·C_tr) (Q ∝ V^m이면 E = Q·V·m/(m+1); 두 등가 용량의 정의를 맞추는 거듭제곱 근사).
     R_ds(on)(125 °C)는 데이터시트 값(UG4SC075011K4S) 또는 25 °C와 175 °C(GaN은 150 °C) 값 사이 선형 보간(온도 곡선이
     아래로 볼록하므로 보간값이 실제보다 크다 = 도통 손실 쪽 보수적).
     게이트 에너지 = Q_g·ΔV_GS × 병렬 수(스위치 한 번 켜고 끄는 데 드는 구동 에너지). ΔV_GS: SiC MOSFET 22 V(−4/18 V),
     UG4SC 15 V(0/15 V, Q_g 측정 조건), GaN 9 V(−3/6 V, 가정).
  C. 도통·다이오드 손실과 V_A 강하는 E1 모델(sim_array zcp, 2위상, 60주기, E28·E30과 같은 데드타임 전류 소멸 처리
     dead_fix와 무장 전 영교차 'mag')을 R = 2·R_pos + 4 mΩ(ESR·인덕터·배선, E1과
     같음)으로 다시 돌려 위상당 평균 전류 격자(E15 IGRID)와 충전(375/8 A 역방향)에서 구한다(800 V). E15 격자에서 같은
     전류의 손실은 640–920 V에서 0.5 W 안으로 같으므로 800 V 값을 전 전압에 쓴다. f_r을 바꿀 때는 특성 임피던스
     √(L_r/C_fly)를 유지해 L_r·C_fly를 둘 다 f_r0/f_r배 한다(파형은 시간 축만 늘어나 도통 손실은 같다; 데드타임 100 ns의
     비중만 줄어 150 kHz 값이 약간 보수적). 선택안은 직접 모의로 확인한다(S4).
     출력용량·게이트 손실 = (4·Q_pos(V/2)·V/2 + 4·E_g)·f_s, f_s = 모의에서 잰 스위칭 주파수 × f_r/f_r0.
  D. 경로 손실: E15.path_struct('4')(R2 기본형 ④), E25.aux_avg(주행 대표 프로파일 760–900 V, 400 V 부하 분포),
     E15.charge_loss('4')(V_bat/2 충전기, 375 A, 8위상)를 그대로 쓴다. 경부하 운전 세 가지:
       none : 주행 중 모듈 1의 2위상(E15·E25가 쓴 가정)
       shed : E24 위상 셰딩(모듈 출력전류 < I_off = 15 A면 1위상). E24·E28에서 검증했고 R2 관리기에 들어 있는 기능
       idle : shed + 경부하 휴지 시간(스위칭 주파수 저감). 새 제어 기능이므로 참고로만 계산한다(선택 대상 아님).
              f_s = f_s0·x, x = min(1, max(0.1, √(P_cond/P_fix)))에서, 첨두 I_pk/x ≤ 36 A(E24 Ipk_on과 충돌하지 않게)와
              V_A 강하 dV/x ≤ 0.95 V(원설계 격자 최대)가 되도록 x를 올린다. 도통 손실은 1/x배(같은 전하를 짧은 펄스로).
     설계 격자: 소자 4종 × 위치당 병렬 수(SiC MOSFET 1–3·1–4, UG4SC 1–3, GaN 1–6) × f_r ∈ {150, 100, 75, 50, 35, 25} kHz.

■ 판정(실행 전에 고정)
  S1 원설계 보정: 출력용량·게이트 항만 실제 값으로 고친 원설계(위치당 6 mΩ, f_r 150 kHz)에서, 위상당 고정 손실 증가 ΔP
     (주행 대표 전압 평균)가 E25의 손익분기 14.8 W/위상(④ = ⑤) 이하인가. 소자 대응 두 가지: (a) C4MS008075U2 2병렬,
     (b) 6 mΩ를 FOM(R_125·Q_400)이 가장 좋은 후보로 만든 하한. 보정한 ④ 보조 손실·800 V 충전 손실도 보고한다(예상: 불합격).
  S2 수정안 조건(none·shed만, 판정은 shed): (A) ④ 보조 손실(주행 대표) ≤ ⑤ 114.6 W, (C) 800 V 충전 손실 ≤ 모터 승압
     기준점 1.165 kW(E25), (V) 1.1·V_bat,max/2 ≤ 0.8·V_DS 정격, (I) 충전 정격 위상 첨두 / 병렬 수 ≤ I_D(100 °C).
     강건성: Q_oss 1.2배(거듭제곱 근사 불확도)에서도 (A)(C) 합격(R), 수동소자 저항 2배(E25 Q5)에서도 합격(P).
  S3 선택 규칙(두 안): (가) 최소 변경안 = S2·R 합격 중 f_r 최대(수동소자 크기와 150 kHz로 한 동특성 검증과의 차이가 가장
     작다), 같으면 800 V 충전 손실 최소, 그다음 소자 수 최소. (나) 충전 우선안 = S2·R 합격이고 소자 수 ≤ 64(원설계와 같음)
     중 800 V 충전 손실 최소, 같으면 f_r 최대.
  S4 모델 일관성: 선택안을 L_r·C_fly·R을 직접 바꾼 E1 모델로 돌린 도통+다이오드 손실이 격자 값과 5 % 또는 1 W 안
     (위상 전류 3·10·30 A, 충전), 물리 확인(A)의 정확해 무부하 손실이 4·C·V²·f와 3 % 안(원설계·선택안).
  S5 결과 반영(합격 판정 없음): 선택안으로 E25 비교(①·④·⑤·⑥ 보조 손실, 충전 손실과 모터 승압 범위, 손실 에너지 예시)를
     다시 계산하고, 이전 결론 가운데 바뀌는 것을 그대로 적는다.

■ 실행   python E31_stage_a_coss.py      (E15·E25 결과 필요, 2코어 약 15분)
■ 결과   results/E31/coss.json, E31_stage_a_coss.png
"""
import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.linalg import expm

import E15_baseline_loss_rating as E15
import E25_motor_boost_comparison as E25
import model_stage_a as SA
from common import ROOT, load_json, outdir, save_json, verdict, workers

EID = "E31"
DS = ROOT / "data" / "datasheets"
DEVICES = ["C4MS008075U2", "C4MS025075K1", "UG4SC075011K4S", "GS66516T"]
NPAR = {"C4MS008075U2": (1, 2, 3), "C4MS025075K1": (1, 2, 3, 4), "UG4SC075011K4S": (1, 2, 3), "GS66516T": (1, 2, 3, 4, 6)}
DVGS = {"C4MS008075U2": 22., "C4MS025075K1": 22., "UG4SC075011K4S": 15., "GS66516T": 9.}
FR_SET = [150e3, 100e3, 75e3, 50e3, 35e3, 25e3]
LR0, CF0 = SA.BASE["Lr"], SA.BASE["Cfly"]
FRN = SA.FR0                                   # 원설계 공진주파수(149.98 kHz)
RDS0 = SA.BASE["Rds"]
RPASS = SA.BASE["ESR"] + SA.BASE["RL"] + SA.BASE["Rmisc"]   # 4 mΩ
FIX0_E = 4 * (SA.BASE["Eoss"] + SA.BASE["Qg_E"])           # 원모델의 위상당 고정 에너지 [J/주기]
V_SIM = 800.
IGRID = E15.IGRID
I_CHPH = 375. / 8
SHED_IOFF = 15.                                 # E24·E28 위상 셰딩 문턱(모듈 출력전류)
IDLE_IPK, IDLE_DV, IDLE_XMIN = 36., 0.95, 0.1
VBAT_MAX = 920.
Q_UNC, RP_UNC = 1.2, 2.0


# ======================================================================================
# 1. 소자 데이터
# ======================================================================================
def load_dev(name):
    d = json.loads((DS / f"{name}.json").read_text(encoding="utf-8"))
    e = d["electrical"]
    if e.get("R_DSon_125C_typ_mOhm"):
        r125, how = e["R_DSon_125C_typ_mOhm"], "데이터시트 125 °C 전형값"
    else:
        r25 = e["R_DSon_25C_typ_mOhm"]
        T1, r1 = (175, e["R_DSon_175C_typ_mOhm"]) if e.get("R_DSon_175C_typ_mOhm") else (150, e["R_DSon_150C_mOhm"])
        r125, how = r25 + (r1 - r25) * (125 - 25) / (T1 - 25), f"25 °C·{T1} °C 값 선형 보간"
    Ctr, Cer, Vs = e["C_o_tr_pF"] * 1e-12, e["C_o_er_pF"] * 1e-12, float(e["C_o_range_V"][1])
    r = Cer / (2 * Ctr)
    return dict(name=name, R125=r125 * 1e-3, R125_how=how, Ctr=Ctr, Cer=Cer, Vs=Vs, m=r / (1 - r),
                Qg=e["Q_G_nC"] * 1e-9, dVgs=DVGS[name], Eg=e["Q_G_nC"] * 1e-9 * DVGS[name],
                Vds=float(d["ratings"]["V_DS_V"]), Id100=float(d["ratings"]["I_D_100C_A"]), url=d["url"])


def qoss(dev, V):
    """소자 하나의 출력 전하 Q_oss(V) [C] (거듭제곱 근사)."""
    return dev["Ctr"] * dev["Vs"] * (V / dev["Vs"]) ** dev["m"]


# ======================================================================================
# 2. 물리 확인: 노드 용량을 넣은 RSC 한 위상의 정확해(행렬 지수)
# ======================================================================================
def rsc_nodecap(Vin, Vo, Cpos, Lr, Cf, Ron, Rrest, td=100e-9, fratio=0.98, ncyc=40):
    """2:1 RSC 한 위상(스위치 S1: V_in–A, S2: A–V_o, S3: B–V_o, S4: B–0, A–L_r–C_fly–B). 노드 A·B에 각각 2·C_pos.
    고정 타이밍(도통 T/2 − t_d, 데드타임 t_d, 전 스위치 off)으로 ncyc 주기 적분하고 마지막 주기 손실 [W]와 출력전류 [A]."""
    fr = 1 / (2 * np.pi * np.sqrt(Lr * Cf))
    T = 1 / (fratio * fr); ton = T / 2 - td

    def mats(on):
        G = [1 / Ron if s else 0. for s in on]
        C2 = 2 * Cpos
        A = np.zeros((7, 7))       # x = [v_A, v_B, i_L, v_C, q_in(채널), q_out(채널), 1]
        A[0, 0] = -(G[0] + G[1]) / C2; A[0, 2] = -1 / C2; A[0, 6] = (G[0] * Vin + G[1] * Vo) / C2
        A[1, 1] = -(G[2] + G[3]) / C2; A[1, 2] = 1 / C2; A[1, 6] = G[2] * Vo / C2
        A[2, 0] = 1 / Lr; A[2, 1] = -1 / Lr; A[2, 3] = -1 / Lr; A[2, 2] = -Rrest / Lr
        A[3, 2] = 1 / Cf
        A[4, 0] = -G[0]; A[4, 6] = G[0] * Vin
        A[5, 0] = G[1]; A[5, 1] = G[2]; A[5, 6] = -(G[1] + G[2]) * Vo
        return A
    seq = [((0, 0, 0, 0), td), ((1, 0, 1, 0), ton), ((0, 0, 0, 0), td), ((0, 1, 0, 1), ton)]
    Ms = [expm(mats(on) * dt) for on, dt in seq]
    x = np.array([Vin, Vo, 0., Vin / 2, 0., 0., 1.])
    for _ in range(ncyc):
        x0 = x.copy()
        for M in Ms:
            x = M @ x
    dvA, dvB = x[0] - x0[0], x[1] - x0[1]
    Qin = x[4] - x0[4] - Cpos * dvA                       # S1 용량의 변위 전류 포함
    Qout = x[5] - x0[5] + Cpos * dvA + Cpos * dvB         # S2·S3 용량의 변위 전류 포함
    Est = 0.5 * Lr * (x[2] ** 2 - x0[2] ** 2) + 0.5 * Cf * (x[3] ** 2 - x0[3] ** 2)
    return (Vin * Qin - Vo * Qout - Est) / T, Qout / T, 1 / T


def physics_check(cases):
    out = []
    for c in cases:
        V = 800.; Vh = V / 2
        Ceq = c["Qpos400"] / Vh
        Lr, Cf = LR0 * FRN / c["fr"], CF0 * FRN / c["fr"]
        p1, i1, f = rsc_nodecap(V, Vh, Ceq, Lr, Cf, c["Rpos"], RPASS)
        p0, i0, _ = rsc_nodecap(V, Vh, 1e-15, Lr, Cf, c["Rpos"], RPASS)
        ref = 4 * Ceq * Vh ** 2 * f
        out.append(dict(name=c["name"], fr=c["fr"], C_eq_nF=Ceq * 1e9, f_s=f, P_exact=p1 - p0, P_formula=ref,
                        err=(p1 - p0) / ref - 1, Iout=i1))
    return out


# ======================================================================================
# 3. E1 모델 도통·다이오드 손실(위상당)
# ======================================================================================
def ph_parts(r, ncyc_last=10):
    """마지막 ncyc_last 스위칭 주기(충전 구간 시작 사이) 위상 평균: 도통·다이오드 손실, 스위칭 주파수, 첨두, V_A 강하."""
    Vf = SA.BASE["Vf"]
    res = []
    for k in range(r["N"]):
        sk = r["st"][:, k].astype(int); ik = r["i"][:, k].astype(float)
        tr = np.where(np.diff(sk) != 0)[0]
        onk = tr[(sk[tr] == 0) & (sk[tr + 1] == 1)] + 1
        a, b = onk[-1 - ncyc_last], onk[-1]
        seg = slice(a, b)
        res.append(dict(Pc=float(np.mean(ik[seg] ** 2) * r["R"][k]),
                        Pd=float(np.mean((sk[seg] == 0) * 2 * Vf * np.abs(ik[seg]))),
                        fs=ncyc_last / ((b - a) * r["dt"]), Ipk=float(np.max(np.abs(ik[seg]))),
                        vb=float(np.mean(r["vb"][seg]))))
    return res


def _sim_point(args):
    """args = (Rds, fr, iph, sign, idle) → 위상 평균 도통·다이오드 손실 등(2위상, 800 V)."""
    Rds, fr, iph, sign, idle = args
    SA.BASE.update(Rds=Rds, Lr=LR0 * FRN / fr, Cfly=CF0 * FRN / fr)
    SA.FR0 = 1 / (2 * np.pi * np.sqrt(SA.BASE["Lr"] * SA.BASE["Cfly"]))
    ncyc = int(math.ceil(60 * (1 + 2 * idle * SA.FR0)))
    r = SA.sim_array(N=2, Vbat=V_SIM, Iload=sign * 2 * iph, Cbus=400e-6, mode="zcp", ncyc=ncyc, idle=idle, dead_fix=True,
                     unarmed_stop="mag")
    p = ph_parts(r)
    return dict(Rds=Rds, fr=fr, iph=iph, sign=sign, idle=idle, Pc=float(np.mean([x["Pc"] for x in p])),
                Pd=float(np.mean([x["Pd"] for x in p])), fs=float(np.mean([x["fs"] for x in p])),
                Ipk=float(np.mean([x["Ipk"] for x in p])), dvA=float(V_SIM / 2 - np.mean([x["vb"] for x in p])))


def run_points(jobs):
    with ProcessPoolExecutor(workers()) as ex:
        return list(ex.map(_sim_point, jobs))


def cond_jobs(Rds, fr=FRN):
    return [(Rds, fr, float(i), 1., 0.) for i in IGRID] + [(Rds, fr, I_CHPH, -1., 0.)]


def cond_table(res, Rds, fr=FRN):
    fw = sorted([r for r in res if r["Rds"] == Rds and r["fr"] == fr and r["sign"] > 0 and r["idle"] == 0], key=lambda r: r["iph"])
    ch = [r for r in res if r["Rds"] == Rds and r["fr"] == fr and r["sign"] < 0 and r["idle"] == 0][0]
    g = lambda k: np.array([r[k] for r in fw])
    return dict(Rds=Rds, Pc=g("Pc"), Pd=g("Pd"), fs=g("fs"), Ipk=g("Ipk"), dvA=g("dvA"), ch=ch)


# ======================================================================================
# 4. 설계안 → E15 Stage A 표 → 경로 손실
# ======================================================================================
class StageAx(E15.StageA):
    """E15.StageA + 위상 셰딩(모듈 출력전류 < I_off면 1위상)."""
    def __init__(self, T, shed=False):
        super().__init__(T); self.shed = shed

    def drive(self, V, I, nph=2):
        if self.shed and abs(I) < SHED_IOFF:
            nph = 1
        return super().drive(V, I, nph)


def fixed_energy(design, V, qmul=1.):
    """위상당 한 주기 고정 에너지 [J]: 출력용량 4·Q_pos(V/2)·V/2 + 게이트 4·E_g(위치당)."""
    Vh = V / 2
    return 4 * qmul * design["Qpos"](Vh) * Vh + 4 * design["Eg_pos"]


def make_table(design, ct, fr, mode, qmul=1., rpmul=1.):
    """design: Qpos(V)·Eg_pos·Rpos. ct: 같은 R의 도통 표(150 kHz). 반환: E15.StageA 표(P, D, charge)와 정보."""
    kr = (2 * design["Rpos"] + RPASS * rpmul) / (2 * design["Rpos"] + RPASS)   # 수동소자 저항 배율의 도통 손실 근사
    sc = fr / FRN
    VG = E15.VGRID
    P = np.zeros((len(VG), len(IGRID))); D = np.zeros_like(P); X = np.ones_like(P)
    for i, V in enumerate(VG):
        Ef = fixed_energy(design, V, qmul)
        for j in range(len(IGRID)):
            fs0 = ct["fs"][j] * sc
            pc, pd, pfix = ct["Pc"][j] * kr, ct["Pd"][j], Ef * fs0
            x = 1.
            if mode == "idle":
                x = min(1., max(IDLE_XMIN, math.sqrt(pc / pfix), ct["Ipk"][j] / IDLE_IPK, ct["dvA"][j] * kr / IDLE_DV))
            P[i, j] = pc / x + pd + pfix * x
            D[i, j] = ct["dvA"][j] * kr / x
            X[i, j] = x
    chg = {}
    c = ct["ch"]
    for V in VG:
        chg[float(V)] = dict(ploss_ph=c["Pc"] * kr + c["Pd"] + fixed_energy(design, V, qmul) * c["fs"] * sc,
                             Ipk=c["Ipk"], dvA=-c["dvA"])
    return dict(P=P, D=D, charge=chg, x=X)


def path_losses(T, shed):
    S = StageAx(T, shed)
    aux4, by = E25.aux_avg(lambda V, P: E15.path_struct("4", S, V, P, E15.P48)["loss"])
    ch = {f"{V:.0f}V": E15.charge_loss("4", S, V) for V in (640., 800., 920.)}
    return dict(aux4=aux4, by_load=by, charge=ch)


def hw_designs(devs):
    out = []
    for name in DEVICES:
        d = devs[name]
        for n in NPAR[name]:
            out.append(dict(key=f"{name}x{n}", dev=name, npar=n, Rpos=d["R125"] / n, Eg_pos=n * d["Eg"],
                            Qpos=(lambda Vh, d=d, n=n: n * qoss(d, Vh)), devices=32 * n,
                            Vok=1.1 * VBAT_MAX / 2 <= 0.8 * d["Vds"], Id100=d["Id100"]))
    return out


def original_designs(devs):
    """S1: 원설계(위치당 6 mΩ)의 출력용량·게이트를 실제 소자로 고친 두 경우."""
    c4 = devs["C4MS008075U2"]
    fom = {k: v["R125"] * qoss(v, 400.) for k, v in devs.items() if k != "GS66516T"}
    best = min(fom, key=fom.get); b = devs[best]; k = b["R125"] / RDS0         # 6 mΩ를 만드는 등가 병렬 배수
    return [dict(key="orig_a", label="(a) C4MS008075U2 2병렬", Rpos=RDS0, Eg_pos=2 * c4["Eg"],
                 Qpos=(lambda Vh: 2 * qoss(c4, Vh))),
            dict(key="orig_b", label=f"(b) FOM 최선({best}) 6 mΩ 등가", Rpos=RDS0, Eg_pos=k * b["Eg"],
                 Qpos=(lambda Vh: k * qoss(b, Vh)), fom_best=best, k=k)], fom


# ======================================================================================
# 5. 실행
# ======================================================================================
def main():
    devs = {n: load_dev(n) for n in DEVICES}
    print("E31 소자 데이터")
    for n, d in devs.items():
        print(f"  {n:15s} R125 {d['R125']*1e3:5.1f} mΩ ({d['R125_how']}), Q_oss(400 V) {qoss(d, 400.)*1e9:5.0f} nC, "
              f"m {d['m']:.3f}, FOM {d['R125']*1e3*qoss(d, 400.)*1e6:.2f} mΩ·µC, E_g {d['Eg']*1e6:.2f} µJ")
    c25 = load_json("E25", "comparison")
    AUX5, AUX6, AUX4_0 = c25["aux"]["5"]["avg_W"], c25["aux"]["6"]["avg_W"], c25["aux"]["4"]["avg_W"]
    MB = {k: v["motor_base"] for k, v in c25["charge"].items()}
    MR = {k: v["motor_range"] for k, v in c25["charge"].items()}
    DPEQ5 = c25["stageA_sensitivity"]["dP_eq5_W"]

    designs = hw_designs(devs)
    origs, fom = original_designs(devs)
    rds_set = sorted({RDS0} | {d["Rpos"] for d in designs})
    print(f"E31 도통 격자 모의: R_pos {len(rds_set)}종 × {len(IGRID) + 1}점 ...")
    res = run_points([j for R in rds_set for j in cond_jobs(R)])
    CT = {R: cond_table(res, R) for R in rds_set}

    # ---- S1 원설계 보정 --------------------------------------------------------------------------------------
    ct0 = CT[RDS0]
    # 원모델 재현(고정 = 4·(E_oss + Q_g·E)·f_s): E15 격자와 비교
    Pm = np.array([[ct0["Pc"][j] + ct0["Pd"][j] + FIX0_E * ct0["fs"][j] for j in range(len(IGRID))] for _ in E15.VGRID])
    g15 = load_json("E15", "stage_a_grid")
    rep_err = float(np.max(np.abs(Pm[3] - np.array(g15["P_phase"])[3])))      # 820 V 행 비교
    chm = ct0["ch"]
    Tm = dict(P=Pm, D=np.tile(ct0["dvA"], (len(E15.VGRID), 1)),
              charge={float(V): dict(ploss_ph=chm["Pc"] + chm["Pd"] + FIX0_E * chm["fs"], Ipk=chm["Ipk"], dvA=-chm["dvA"])
                      for V in E15.VGRID})
    S1 = dict(model=dict(none=path_losses(Tm, False), shed=path_losses(Tm, True)), reproduce_err_W=rep_err)
    Vd = E15.PROFILES["drive_typ"]["V"]
    fs_ref = float(np.interp(10., IGRID, ct0["fs"]))
    for o in origs:
        T_none = make_table(o, ct0, FRN, "none")
        dP = [(fixed_energy(o, V) - FIX0_E) * fs_ref for V in Vd]
        S1[o["key"]] = dict(label=o["label"], dP_avg_W=float(np.mean(dP)), dP_range_W=[float(min(dP)), float(max(dP))],
                            P_oss_800_W=4 * o["Qpos"](400.) * 400. * fs_ref, P_gate_W=4 * o["Eg_pos"] * fs_ref,
                            none=path_losses(T_none, False), shed=path_losses(T_none, True),
                            idle=path_losses(make_table(o, ct0, FRN, "idle"), True))
        S1[o["key"]]["pass"] = S1[o["key"]]["dP_avg_W"] <= DPEQ5
    S1["fom_mOhm_uC"] = {k: v * 1e12 for k, v in fom.items()}
    print("S1 원설계 보정")
    for k in ("orig_a", "orig_b"):
        s = S1[k]
        verdict(f"{s['label']}: 위상당 고정 손실 증가 {s['dP_avg_W']:.1f} W ≤ {DPEQ5:.1f} W", s["pass"],
                f"P_oss(800 V) {s['P_oss_800_W']:.0f} W, ④ 보조 {s['none']['aux4']:.0f} W(셰딩 {s['shed']['aux4']:.0f} W), "
                f"800 V 충전 {s['none']['charge']['800V']:.0f} W")
    print(f"  (원모델 재현: ④ 보조 {S1['model']['none']['aux4']:.1f} W(E25 {AUX4_0:.1f}), 충전 {S1['model']['none']['charge']['800V']:.0f} W, "
          f"격자 차 최대 {rep_err:.2f} W)")

    # ---- S2 설계 격자 -----------------------------------------------------------------------------------------
    print(f"E31 설계 격자 {len(designs)}종 × f_r {len(FR_SET)}개 ...")
    grid = []
    for d in designs:
        ct = CT[d["Rpos"]]
        Ipk_ch = ct["ch"]["Ipk"]
        for fr in FR_SET:
            row = dict(key=d["key"], dev=d["dev"], npar=d["npar"], devices=d["devices"], fr=fr, Rpos=d["Rpos"],
                       Rpath=2 * d["Rpos"] + RPASS, Ipk_ch=Ipk_ch, Ipk_per_dev=Ipk_ch / d["npar"], Id100=d["Id100"],
                       V_ok=bool(d["Vok"]), I_ok=bool(Ipk_ch / d["npar"] <= d["Id100"]),
                       Lr=LR0 * FRN / fr, Cfly=CF0 * FRN / fr,
                       P_fix_800=fixed_energy(d, 800.) * np.interp(10., IGRID, ct["fs"]) * fr / FRN)
            for mode in ("none", "shed", "idle"):
                T = make_table(d, ct, fr, mode)
                row[mode] = path_losses(T, mode != "none")
                if mode == "idle":
                    row["idle_x_min"] = float(T["x"].min())
            row["shed_Q12"] = path_losses(make_table(d, ct, fr, "shed", qmul=Q_UNC), True)
            row["shed_Rp2"] = path_losses(make_table(d, ct, fr, "shed", rpmul=RP_UNC), True)
            ok = lambda pl: bool(pl["aux4"] <= AUX5 and pl["charge"]["800V"] <= MB["800V"])
            row["A"] = bool(row["shed"]["aux4"] <= AUX5); row["C"] = bool(row["shed"]["charge"]["800V"] <= MB["800V"])
            row["S2"] = bool(row["A"] and row["C"] and row["V_ok"] and row["I_ok"])
            row["R"] = ok(row["shed_Q12"]); row["P"] = ok(row["shed_Rp2"])
            row["none_AC"] = ok(row["none"])
            grid.append(row)
    npass = sum(r["S2"] for r in grid)
    print(f"  S2 합격 {npass}/{len(grid)}, 그 가운데 Q_oss 1.2배도 합격 {sum(r['S2'] and r['R'] for r in grid)}, "
          f"수동소자 저항 2배도 합격 {sum(r['S2'] and r['P'] for r in grid)}")
    for fr in FR_SET:
        ok = [r for r in grid if r["fr"] == fr and r["S2"]]
        print(f"  f_r {fr/1e3:4.0f} kHz: S2 합격 {len(ok):2d}  " +
              ", ".join(f"{r['key']}({r['shed']['aux4']:.0f}/{r['shed']['charge']['800V']:.0f}{'' if r['R'] else ' R×'})" for r in ok))

    # ---- S3 선택 ----------------------------------------------------------------------------------------------
    cand = [r for r in grid if r["S2"] and r["R"]]
    selA = max(cand, key=lambda r: (r["fr"], -r["shed"]["charge"]["800V"], -r["devices"])) if cand else None
    candB = [r for r in cand if r["devices"] <= 64]
    selB = min(candB, key=lambda r: (r["shed"]["charge"]["800V"], -r["fr"])) if candB else None
    sel = {"가": selA, "나": selB}
    print("S3 선택")
    for k, r in sel.items():
        if r is None:
            verdict(f"({k}) 후보 없음", False); continue
        print(f"  ({k}) {r['key']} f_r {r['fr']/1e3:.0f} kHz: L_r {r['Lr']*1e9:.0f} nH, C_fly {r['Cfly']*1e6:.1f} µF, 소자 {r['devices']}개, "
              f"④ 보조 {r['shed']['aux4']:.1f} W, 충전 640/800/920 V {r['shed']['charge']['640V']:.0f}/{r['shed']['charge']['800V']:.0f}/"
              f"{r['shed']['charge']['920V']:.0f} W, 고정 손실(800 V) {r['P_fix_800']:.1f} W/위상")

    # ---- S4 모델 일관성 ---------------------------------------------------------------------------------------
    S4 = {}
    jobs = []
    for k, r in sel.items():
        if r is None:
            continue
        for i in (3., 10., 30.):
            jobs.append((r["Rpos"], r["fr"], i, 1., 0.))
        jobs.append((r["Rpos"], r["fr"], I_CHPH, -1., 0.))
    # idle 참고 계산의 도통 배율 확인(선택안 (가), 위상 전류 3 A, 표의 x로 휴지 시간 설정)
    idle_chk = None
    if selA is not None:
        ctA = CT[selA["Rpos"]]
        dA = [d for d in designs if d["key"] == selA["key"]][0]
        fs0 = float(np.interp(3., IGRID, ctA["fs"])) * selA["fr"] / FRN
        g3 = lambda k: float(np.interp(3., IGRID, ctA[k]))
        x3 = min(1., max(IDLE_XMIN, math.sqrt(g3("Pc") / (fixed_energy(dA, V_SIM) * fs0)), g3("Ipk") / IDLE_IPK, g3("dvA") / IDLE_DV))
        idle = (1 / (x3 * fs0) - 1 / fs0) / 2
        jobs.append((selA["Rpos"], selA["fr"], 3., 1., idle))
        idle_chk = dict(x=x3, idle_s=idle)
    dres = run_points(jobs) if jobs else []
    for k, r in sel.items():
        if r is None:
            continue
        ct = CT[r["Rpos"]]
        rows = []
        for q in dres:
            if q["Rds"] != r["Rpos"] or q["fr"] != r["fr"] or q["idle"] != 0:
                continue
            if q["sign"] > 0:
                tab = float(np.interp(q["iph"], IGRID, ct["Pc"] + ct["Pd"]))
            else:
                tab = ct["ch"]["Pc"] + ct["ch"]["Pd"]
            dirv = q["Pc"] + q["Pd"]
            ok = abs(dirv - tab) <= max(0.05 * tab, 1.0)
            rows.append(dict(iph=q["iph"], sign=q["sign"], direct_W=dirv, table_W=tab, ok=bool(ok), fs_direct=q["fs"],
                             fs_table=float(np.interp(q["iph"], IGRID, ct["fs"])) * r["fr"] / FRN if q["sign"] > 0 else ct["ch"]["fs"] * r["fr"] / FRN,
                             dvA_direct=q["dvA"], Ipk_direct=q["Ipk"]))
        S4[k] = dict(points=rows, pass_=bool(all(x["ok"] for x in rows)))
    if idle_chk is not None:
        q = [q for q in dres if q["idle"] > 0][0]
        base = float(np.interp(3., IGRID, CT[selA["Rpos"]]["Pc"]))
        fs0 = float(np.interp(3., IGRID, CT[selA["Rpos"]]["fs"])) * selA["fr"] / FRN
        idle_chk.update(fs_direct=q["fs"], x_direct=q["fs"] / fs0, Pc_direct=q["Pc"], Pc_pred=base / (q["fs"] / fs0),
                        Ipk_direct=q["Ipk"], dvA_direct=q["dvA"])
        S4["idle_check"] = idle_chk
    phys_cases = [dict(name="원설계 (a)", fr=FRN, Rpos=RDS0, Qpos400=origs[0]["Qpos"](400.))]
    for k, r in sel.items():
        if r is not None:
            d = [d for d in designs if d["key"] == r["key"]][0]
            phys_cases.append(dict(name=f"선택 ({k}) {r['key']}", fr=r["fr"], Rpos=r["Rpos"], Qpos400=d["Qpos"](400.)))
    PH = physics_check(phys_cases)
    S4["physics"] = PH
    S4["physics_pass"] = bool(all(abs(p["err"]) <= 0.03 for p in PH))
    print("S4 모델 일관성")
    for k in ("가", "나"):
        if k in S4:
            verdict(f"({k}) 직접 모의 도통+다이오드 손실이 격자 값과 5 % 또는 1 W 안", S4[k]["pass_"],
                    ", ".join(f"{p['iph']:.0f} A{'(충전)' if p['sign'] < 0 else ''} {p['direct_W']:.1f}/{p['table_W']:.1f} W" for p in S4[k]["points"]))
    verdict("정확해 무부하 출력용량 손실이 4·C·V²·f와 3 % 안", S4["physics_pass"],
            ", ".join(f"{p['name']} {p['P_exact']:.1f}/{p['P_formula']:.1f} W" for p in PH))
    if idle_chk:
        print(f"  (참고) idle 도통 배율: x 목표 {idle_chk['x']:.3f}, 모의 {idle_chk['x_direct']:.3f}, 도통 {idle_chk['Pc_direct']:.2f} W "
              f"(예측 {idle_chk['Pc_pred']:.2f} W), 첨두 {idle_chk['Ipk_direct']:.1f} A")

    # ---- S5 결과 반영 ----------------------------------------------------------------------------------------
    def e25_view(pl):
        ch = pl["charge"]
        out = dict(aux4=pl["aux4"], aux4_minus_aux5=pl["aux4"] - AUX5, aux4_minus_aux6=pl["aux4"] - AUX6, charge=ch,
                   charge_vs_motor={V: dict(stageA=ch[V], motor_base=MB[V], motor_min_Rph5=MR[V]["min_Rph5"], motor_min=MR[V]["min"],
                                            below_range_Rph5=bool(ch[V] < MR[V]["min_Rph5"]), below_base=bool(ch[V] < MB[V]))
                                    for V in ch})
        # E25 Q4 손실 에너지 예시(주행 1,000 h + 400–500 V급 충전 1,000 kWh)
        out["energy_kWh"] = dict(drive=pl["aux4"] * E25.DRIVE_H / 1e3, charge=ch["800V"] / (400. * E25.I_CH) * E25.CHARGE_KWH)
        out["energy_kWh"]["total"] = out["energy_kWh"]["drive"] + out["energy_kWh"]["charge"]
        # 모터 승압이 Stage A와 같은 충전 손실이 되는 상저항(E25 기준점 조합)
        from scipy.optimize import brentq
        pA = ch["800V"]
        f0 = E25.motor_boost_loss(800., Rph=0.)["total"]
        out["Rph_breakeven_base_mOhm"] = 1e3 * brentq(lambda x: E25.motor_boost_loss(800., Rph=x)["total"] - pA, 0., 0.05) if f0 < pA else 0.
        return out
    S5 = dict(ref=dict(aux1=c25["aux"]["1"]["avg_W"], aux5=AUX5, aux6=AUX6, aux4_E25=AUX4_0, motor_base=MB,
                       motor_range={k: dict(min=v["min"], min_Rph5=v["min_Rph5"], max=v["max"]) for k, v in MR.items()},
                       booster_800=c25["charge"]["800V"]["booster"],
                       energy_E25={k: c25["energy_example"][k] for k in ("1", "5", "4", "6")}),
              model_none=e25_view(S1["model"]["none"]), model_shed=e25_view(S1["model"]["shed"]),
              orig_a_none=e25_view(S1["orig_a"]["none"]), orig_a_shed=e25_view(S1["orig_a"]["shed"]),
              orig_b_shed=e25_view(S1["orig_b"]["shed"]))
    for k, r in sel.items():
        if r is not None:
            S5[f"sel_{k}"] = e25_view(r["shed"]); S5[f"sel_{k}_idle"] = e25_view(r["idle"])
    print("S5 E25 비교 다시 계산(④ 보조 / 800 V 충전, 기준 ⑤ %.1f W·⑥ %.1f W, 모터 승압 기준점 %.0f W·R_ph ≥ 5 mΩ 하한 %.0f W)"
          % (AUX5, AUX6, MB["800V"], MR["800V"]["min_Rph5"]))
    for k in [k for k in S5 if k != "ref"]:
        v = S5[k]
        print(f"  {k:14s} ④ {v['aux4']:6.1f} W (⑤ 대비 {v['aux4_minus_aux5']:+6.1f}, ⑥ 대비 {v['aux4_minus_aux6']:+6.1f}), "
              f"충전 {v['charge']['800V']:6.0f} W (모터 하한 아래 {v['charge_vs_motor']['800V']['below_range_Rph5']}), "
              f"손익분기 R_ph {v['Rph_breakeven_base_mOhm']:.1f} mΩ")

    out = dict(devices={k: {kk: vv for kk, vv in v.items()} for k, v in devs.items()},
               assumptions=dict(RPASS=RPASS, FR0=FRN, Lr0=LR0, Cfly0=CF0, DVGS=DVGS, SHED_IOFF=SHED_IOFF, IDLE=dict(Ipk=IDLE_IPK, dV=IDLE_DV, xmin=IDLE_XMIN),
                                Q_UNC=Q_UNC, RP_UNC=RP_UNC, V_SIM=V_SIM, FIX0_E=FIX0_E, dP_eq5=DPEQ5),
               cond_tables={f"{R*1e3:.3f}mOhm": dict(Pc=v["Pc"], Pd=v["Pd"], fs=v["fs"], Ipk=v["Ipk"], dvA=v["dvA"], ch=v["ch"]) for R, v in CT.items()},
               S1=S1, grid=grid, selection={k: (r["key"] + f"@{r['fr']/1e3:.0f}kHz" if r else None) for k, r in sel.items()},
               S4=S4, S5=S5)
    save_json(EID, "coss", out)
    figure(out, sel, CT, origs, designs)


def figure(out, sel, CT, origs, designs):
    import matplotlib
    matplotlib.use("Agg")
    from plotstyle import korean, COLOR
    plt = korean()
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    # (a) 위상당 손실 대 위상 전류(800 V)
    a = ax[0]
    ct0 = CT[RDS0]
    fs0 = ct0["fs"]
    a.plot(IGRID, ct0["Pc"] + ct0["Pd"] + FIX0_E * fs0, "o-", color=COLOR["gray"], label="원모델(E1, E_oss 24 µJ)")
    o = origs[0]
    a.plot(IGRID, ct0["Pc"] + ct0["Pd"] + fixed_energy(o, 800.) * fs0, "s-", color=COLOR["red"], label="원설계 보정 (a) 150 kHz")
    for (k, r), c in zip(sel.items(), (COLOR["blue"], COLOR["green"])):
        if r is None:
            continue
        d = [d for d in designs if d["key"] == r["key"]][0]; ct = CT[r["Rpos"]]
        a.plot(IGRID, ct["Pc"] + ct["Pd"] + fixed_energy(d, 800.) * ct["fs"] * r["fr"] / FRN, "^-", color=c,
               label=f"선택 ({k}) {r['key']} {r['fr']/1e3:.0f} kHz")
    a.set_xlabel("위상당 평균 출력전류 [A]"); a.set_ylabel("위상당 손실 [W] (800 V)"); a.set_yscale("log")
    a.set_title("(a) Stage A 위상당 손실"); a.legend(loc="lower right")
    # (b) 설계 격자: ④ 보조 손실 대 800 V 충전 손실(셰딩)
    b = ax[1]
    S5 = out["S5"]; ref = S5["ref"]
    mk = {"C4MS008075U2": "o", "C4MS025075K1": "s", "UG4SC075011K4S": "^", "GS66516T": "D"}
    frs = sorted(FR_SET)
    cmap = plt.get_cmap("viridis")
    for r in out["grid"]:
        c = cmap(frs.index(r["fr"]) / (len(frs) - 1))
        b.scatter(r["shed"]["aux4"], r["shed"]["charge"]["800V"] / 1e3, marker=mk[r["dev"]], s=22 if r["S2"] else 10,
                  facecolor=c if r["S2"] else "none", edgecolor=c, lw=0.8)
    b.axvline(ref["aux5"], color=COLOR["orange"], ls="--", lw=1); b.text(ref["aux5"], 0.32, " ⑤", color=COLOR["orange"])
    b.axvline(ref["aux6"], color=COLOR["green"], ls="--", lw=1); b.text(ref["aux6"], 0.32, " ⑥", color=COLOR["green"])
    b.axhline(ref["motor_base"]["800V"] / 1e3, color=COLOR["red"], ls="--", lw=1)
    b.axhline(ref["motor_range"]["800V"]["min_Rph5"] / 1e3, color=COLOR["red"], ls=":", lw=1)
    b.text(205, ref["motor_base"]["800V"] / 1e3, "모터 승압 기준점", color=COLOR["red"], va="bottom", ha="right", fontsize=7.5)
    b.text(205, ref["motor_range"]["800V"]["min_Rph5"] / 1e3, "모터 승압 하한(R_ph ≥ 5 mΩ)", color=COLOR["red"], va="bottom", ha="right", fontsize=7.5)
    m = S5["model_none"]; b.plot(m["aux4"], m["charge"]["800V"] / 1e3, "*", ms=12, color=COLOR["gray"], label="원모델(E25)")
    for k in ("가", "나"):
        if f"sel_{k}" in S5:
            v = S5[f"sel_{k}"]; b.plot(v["aux4"], v["charge"]["800V"] / 1e3, "o", ms=11, mfc="none", mec="k")
            b.annotate(f"({k})", (v["aux4"], v["charge"]["800V"] / 1e3), xytext=(6, 4), textcoords="offset points")
    for fr in frs:
        b.scatter([], [], color=cmap(frs.index(fr) / (len(frs) - 1)), label=f"{fr/1e3:.0f} kHz", s=14)
    b.set_xlim(60, 210); b.set_ylim(0.3, 2.0)
    b.set_xlabel("④ 보조 경로 손실, 주행 대표 [W]"); b.set_ylabel("800 V 충전 손실 [kW]")
    b.set_title("(b) 설계 격자(위상 셰딩, 채움 = S2 합격; ○ SiC MOSFET 8 mΩ, □ 25 mΩ, △ UG4SC, ◇ GaN)")
    b.legend(loc="upper right", ncol=2, fontsize=7)
    # (c) E25 비교 다시 계산
    c = ax[2]
    labels = ["원모델\n(E25)", "원설계\n보정 (a)"] + [f"선택\n({k})" for k in ("가", "나") if f"sel_{k}" in S5]
    keys = ["model_none", "orig_a_shed"] + [f"sel_{k}" for k in ("가", "나") if f"sel_{k}" in S5]
    xs = np.arange(len(keys))
    c.bar(xs - 0.2, [S5[k]["aux4"] for k in keys], 0.4, color=COLOR["blue"], label="④ 보조 손실 [W]")
    c2 = c.twinx()
    c2.bar(xs + 0.2, [S5[k]["charge"]["800V"] / 1e3 for k in keys], 0.4, color=COLOR["orange"], label="800 V 충전 손실 [kW]")
    c.axhline(ref["aux5"], color=COLOR["blue"], ls="--", lw=1); c.axhline(ref["aux6"], color=COLOR["blue"], ls=":", lw=1)
    c2.axhline(ref["motor_base"]["800V"] / 1e3, color=COLOR["orange"], ls="--", lw=1)
    c2.axhline(ref["motor_range"]["800V"]["min_Rph5"] / 1e3, color=COLOR["orange"], ls=":", lw=1)
    c.set_xticks(xs); c.set_xticklabels(labels); c.set_ylabel("④ 보조 손실 [W] (-- ⑤, ··· ⑥)"); c2.set_ylabel("800 V 충전 손실 [kW] (-- 모터 기준점, ··· 하한)")
    c.set_ylim(0, max(S5[k]["aux4"] for k in keys) * 1.15); c2.set_ylim(0, max(S5[k]["charge"]["800V"] for k in keys) / 1e3 * 1.15)
    c.set_title("(c) E25 비교 다시 계산(위상 셰딩 포함, 원모델은 E25 그대로)")
    h1, l1 = c.get_legend_handles_labels(); h2, l2 = c2.get_legend_handles_labels(); c.legend(h1 + h2, l1 + l2, loc="upper right")
    fig.tight_layout()
    p = outdir(EID) / "E31_stage_a_coss.png"
    fig.savefig(p, dpi=130); print("  → 저장:", p)


if __name__ == "__main__":
    main()
