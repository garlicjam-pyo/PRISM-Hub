"""Stage A(2:1 공진 스위치드 커패시터, RSC) 어레이 스위칭 모델.

[모델 개요]
  Stage A는 800 V 배터리 전압을 1/2로 낮춰 400 V 보조버스(V_A 노드)를 만드는 2:1 RSC다.
  4개 모듈 × 2위상 = 8위상이며, 위상마다 플라잉 커패시터 C_fly와 공진 인덕턴스 L_r을 가진다.
  평균모델이 아니라 스위칭 순간을 그대로 적분하는 ODE 모델이므로 턴오프 순간의 잔류전류
  (영전류 스위칭, ZCS 품질)와 위상별 손실을 직접 볼 수 있다.

[위상 k의 상태와 방정식]  상태: i_C[k](공진전류), v_C[k](플라잉 커패시터 전압), 공용 V_bus
  구간 1(충전)  : L·di/dt = V_in − V_bus − v_C − R·i     (입력 → C_fly → 버스)
  구간 2(방전)  : L·di/dt = V_bus − v_C − R·i            (C_fly → 버스)
  데드타임(0)   : 전류가 남아 있으면 바디 다이오드(2·V_f)로 환류, 영을 지나면 차단
  공통          : C·dv_C/dt = i_C,  C_bus·dV_bus/dt = Σ i_out − I_load
  R은 스위치 2개의 R_ds(on) + 커패시터 ESR + 인덕터 저항 + 배선 저항의 합이다.

[타이밍 방식] (보고서 6.1절에서 비교하는 두 방식)
  'fixed' : 모든 위상이 고정 주기 T = 1/(f_ratio·f_r0)로 스위칭하고 위상 간 T/(2N) 오프셋을 둔다.
            부품 공차로 실제 공진주파수가 달라지면 턴오프 시점에 전류가 남는다.
  'zcp'   : 자기발진 영교차 추종. 위상마다 전류가 영으로 돌아온 것을 검출(검출 지연 td_det)하면
            그 구간을 끝내고 데드타임 뒤 다음 구간을 시작한다. 공칭 도통시간의 0.80–1.12배를
            블랭킹·보호 창으로 쓴다. 전류 부호(pulse_sign)를 기준으로 판정하므로 역방향 전력
            (버스 → 배터리)에서도 같은 논리가 동작한다.

[손실 추정] (위상당, 마지막 10주기 평균)
  도통손실 mean(i²)·R + 다이오드 손실 2·V_f·|i|(데드타임) + 출력용량 손실 4·E_oss·f_s + 게이트 손실 4·Q_g·E·f_s
  반도체·자성체 손실의 상세 모델이 아니라 회로 파라미터에 따른 추정값이다.

[적분] 고정 간격 RK4, 한 주기를 Nstep(기본 340) 단계로 나눈다. MATLAB 구현(matlab/prism_sim_array.m)과
       같은 알고리즘이며, 공차 난수도 MATLAB과 같은 순서로 뽑도록 matlab_rng()를 제공한다.
"""
import numpy as np

# 공칭 부품값 (보고서 3.2절 Stage A 설계값)
BASE = dict(
    Cfly=7.8125e-6,   # 플라잉 커패시터 [F]
    Lr=1.441e-7,      # 공진 인덕턴스 [H]  → f_r0 ≈ 150 kHz
    Rds=6e-3,         # 스위치 도통저항 [Ω] (전류 경로에 2개 직렬)
    ESR=1.5e-3,       # 커패시터 ESR [Ω]
    RL=1e-3,          # 인덕터 권선저항 [Ω]
    Rmisc=1.5e-3,     # 배선·접점 저항 [Ω]
    Vf=0.9,           # 바디 다이오드 순방향 전압 [V]
    Eoss=24e-6,       # 스위치당 출력용량 에너지 [J]
    Qg_E=2e-6,        # 스위치당 게이트 구동 에너지 [J]
    tdead=100e-9,     # 데드타임 [s]
)
FR0 = 1 / (2 * np.pi * np.sqrt(BASE["Lr"] * BASE["Cfly"]))   # 공칭 공진주파수 [Hz]

# (E32) 설계 묶음. 'R1_150k'는 위 BASE(E1–E31, 150 kHz)이고, 'A25'는 E31·docs/37의 수정안 (나)다.
#   A25: 위치당 C4MS008075U2 2병렬(R_ds 125 °C 10.53 mΩ/2), f_r 25 kHz(√(L/C) 유지: L_r·C_fly 6배),
#        출력용량 손실은 E_oss 대신 하드 스위칭 전이 손실 4·Q_oss,위치(V/2)·V/2·f_s(analyze, coss 키),
#        게이트 에너지 2 × 278 nC × 22 V, 바디 다이오드 V_SD 4.5 V(데이터시트 175 °C, V_GS −4 V),
#        적분 간격을 150 kHz와 같은 약 20 ns로(Nstep 2040: 25 kHz에서 340단계는 120 ns라 데드타임·영교차가 거칠다, TB25 진단).
#   set_design(name)이 BASE를 그 값으로 바꾸고 FR0를 다시 계산한다(모듈 전역 T = 1/FR0를 쓰는 스크립트는 다시 계산해야 한다).
DESIGNS = {
    "R1_150k": dict(BASE, Nstep=340, coss=None),
    "A25": dict(Cfly=7.8125e-6 * 6, Lr=1.441e-7 * 6, Rds=(8.0 + (11.8 - 8.0) * 100 / 150) * 1e-3 / 2, ESR=1.5e-3, RL=1e-3, Rmisc=1.5e-3, Vf=4.5,
                Eoss=0.0, Qg_E=2 * 278e-9 * 22., tdead=100e-9, Nstep=2040,
                coss=dict(Ctr=828e-12, Cer=510e-12, Vs=500., npar=2, device="C4MS008075U2")),
}
DESIGN = "R1_150k"


def set_design(name):
    """Stage A 설계 묶음을 바꾼다(BASE를 제자리에서 바꾸므로 BASE를 참조하는 다른 모듈에도 적용된다)."""
    global FR0, DESIGN
    BASE.clear(); BASE.update(DESIGNS[name])
    FR0 = 1 / (2 * np.pi * np.sqrt(BASE["Lr"] * BASE["Cfly"]))
    DESIGN = name
    return FR0


def qoss_pos(V):
    """(E32) 위치당 출력 전하 Q_oss(V) [C]: C_o(tr)·C_o(er) 거듭제곱 근사(E31과 같음). coss가 없으면 None."""
    c = BASE.get("coss")
    if not c:
        return None
    r = c["Cer"] / (2 * c["Ctr"]); m = r / (1 - r)
    return c["npar"] * c["Ctr"] * c["Vs"] * (V / c["Vs"]) ** m


def mround(x):
    """MATLAB round()와 같은 반올림(0.5는 0에서 먼 쪽). numpy·파이썬 round는 짝수 쪽으로 반올림하므로
    위상 오프셋(예: 42.5 단계)이 MATLAB과 1단계 달라지는 것을 막는다."""
    return np.sign(x) * np.floor(np.abs(x) + 0.5)


def matlab_rng(seed):
    """MATLAB의 rng(seed); rand(...)와 같은 난수열을 내는 생성기.

    MATLAB 기본 생성기(Mersenne Twister)는 seed 0을 5489로 바꿔 초기화한다. numpy RandomState는
    같은 MT19937이므로 seed만 맞추면 rand(1,N)과 random_sample(N)이 같은 값을 낸다.
    이렇게 해서 Python과 MATLAB이 같은 부품 공차 표본으로 시험한다. (GNU Octave의 rng는 초기화
    방식이 달라 다른 표본이 나온다.)
    """
    return np.random.RandomState(5489 if seed == 0 else seed)


def draw_tolerance(N, tol, rs):
    """위상별 C, L, R을 균일분포 공차로 뽑는다. MATLAB과 같은 순서(C 전체 → L 전체 → R 전체)."""
    C = np.full(N, BASE["Cfly"]); L = np.full(N, BASE["Lr"])
    R = np.full(N, 2 * BASE["Rds"] + BASE["ESR"] + BASE["RL"] + BASE["Rmisc"])
    if tol:
        C = C * (1 + tol["C"] * (2 * rs.random_sample(N) - 1))
        L = L * (1 + tol["L"] * (2 * rs.random_sample(N) - 1))
        R = R * (1 + tol["R"] * (2 * rs.random_sample(N) - 1))
    return C, L, R


def sim_array(N=8, Vbat=788., Iload=375., Cbus=400e-6, mode="zcp", fratio=1.0, tol=None, rs=None,
              R_in=0.0, C_in=100e-6, ncyc=60, Nstep=None, vC0=None, Vbus0=None, en=None,
              td_det=20e-9, i_thr=0.5, shed=None, bus=None, dead_fix=False, unarmed_stop="max", mgr=None, chg=None, fault=None,
              idle=0.0):
    """N위상 Stage A 어레이를 ncyc 주기 동안 적분한다.

    Iload     : 버스 부하전류 [A]. 음수면 역방향(버스 → 배터리) 전력.
                (E24) 구간 선형 프로파일 (tt, II)도 받는다(시각 [s], 전류 [A]).
    shed      : (E24) 경부하 위상 셰딩. None이면 쓰지 않는다(이전과 같음). dict 키:
                keep, sh(남는 위상·멈추는 위상 번호, 0부터), I_off·I_on(필터한 모듈 출력전류 크기 문턱 [A]),
                Ipk_on(남는 위상의 순시 전류 크기가 넘으면 바로 복귀 [A]), tau(출력전류 1차 필터 [s]),
                t_dwell(I_off 아래가 이어져야 하는 시간 [s]), off_frac(복귀 때 인터리빙 지연, 주기 비율, 기본 0.25).
                논리는 회로 게이트 ctrl/prism_gate_stageA_zcps.m과 같다(shed_step 참고).
    dead_fix  : (E24) 데드타임 전류 소멸 처리. 데드타임(구간 0)의 다이오드 환류 기울기는 ±V_bat/2/L(약 3.5 A/ns)라서
                적분 간격(약 20 ns) 안에 68 A까지 0이 된다. RK4는 이 부호 의존 기울기를 단계 안에서 평균해 전류가 0으로
                가지 않고 남거나(멈춘 위상에서는) 진동한다. True면 간격 시작에 그 간격 안에 0을 지나는 데드타임 전류를 0으로
                둔다(소멸). False(기본)는 E1–E23과 같다(이전 결과 재현용).
    bus       : (E24) V_A 노드 뒤의 400 V 버스. None이면 없음(이전과 같음). dict 키: Rw, Lw(배선), Cb(버스 커패시터),
                Rd, Cd(RC 감쇠기), P(정전력 부하 전력 프로파일 (tt, PP) [W]), vmin(정전력 부하 전압 하한), RA(초기값용
                Stage A 출력저항 추정). 이때 Iload는 V_A 노드에 바로 걸리는 전류(충전기 등, 음수 = 주입)다.
    unarmed_stop: (E27) 무장하지 못한 반주기(도통 중 |i|가 5·i_thr를 한 번도 넘지 않음)를 끝내는 시점.
                'max'(기본, E1–E26과 같음): 최대 도통시간(공칭의 1.12배)에서 끈다.
                'nom': 공칭 도통시간 t_on에서 끈다. 첨두가 무장 문턱보다 작은 반주기는 영교차를 검출할 수 없으므로,
                       전류가 거의 0인 공칭 시각에 끈다(최대 도통시간까지 두면 전류가 반대 방향으로 자란다, TB20 D).
                'mag'(E28): 무장하지 못한 반주기는 부호 없이 |i| < i_thr가 검출 지연만큼 이어지면 블랭킹(최소 도통시간) 뒤 끈다
                       (아니면 최대 도통시간). 공진주파수가 낮은 위상(공차)이나 모듈 재시작 직후의 비대칭 펄스는 공칭 도통시간에
                       아직 1 A 넘게 흐를 수 있어(E28 transient 1차), 실제 영교차 근처에서 끈다.
                무장한 반주기는 세 경우 모두 같다(영교차 검출 또는 최대 도통시간).
    mgr       : (E28) 모듈 관리기 + 모듈별 경부하 위상 셰딩. None이면 쓰지 않는다(이전과 같음). N은 짝수(모듈 = 위상 2개,
                모듈 m의 위상 2m·2m+1). dict 키: 위상 셰딩 I_off·I_on·Ipk_on·tau·t_dwell(shed와 같은 뜻, 모듈마다 따로),
                모듈 문턱 Im_up(모듈당 [A]: |필터한 전체 출력전류| > 동작 모듈 수 × Im_up이면 모듈 추가),
                Im_dn(모듈당 [A]: 필요 모듈 수 = ceil(|I|/Im_dn)가 동작 수보다 작은 상태가 t_dwell_m 이어지면 그 수로 줄임),
                Ipk_m(동작 위상 하나라도 순시 |i| > Ipk_m이면 모듈 추가), t_dwell_m, tau_m(모듈 수 판단용 전체 전류 필터 시정수,
                없으면 tau: 2 µs 필터는 위상 펄스 리플이 커서 60 A 평균에서 50–75 A로 흔들린다, E28 static 2차), t_lock(모듈을 더한 뒤 다음 추가를 막는 시간:
                새 모듈이 분담을 받기 전 같은 첨두로 연달아 더하지 않도록), t_hold(Stage A 시작 뒤 모듈 수를 바꾸지 않는 시간:
                시작 과도의 전류 넘침으로 모듈을 더하지 않도록, 없으면 0), n0(시작 동작 모듈 수, 없으면 부하로 정함).
                논리는 mgr_step과 회로 게이트 ctrl/prism_gate_stageA_zcpm.m이 같다.
    chg       : (E28) 충전 요청 구간 (t_start, t_end). 이 구간에서는 모든 모듈을 동작시킨다(충전기 전류 증가 전 사전 기동).
    fault     : (E30) 모듈 고장 [(t_f, m), ...]. 간격 k·dt ≥ t_f(간격 번호 round(t_f/dt))에서 모듈 m(0부터)의 위상을 바로
                멈추고(구간 0, 남은 전류는 다이오드로 소멸) 관리기 후보에서 영구히 뺀다(mgr_fault). mgr가 있어야 한다.
                None이면 이전과 같다.
    idle      : (E31) 휴지 시간 [s]. zcp에서 턴오프 뒤 데드타임에 이 시간을 더 기다린 다음 반주기를 시작한다(경부하 스위칭
                주파수 저감 참고 계산용). 0(기본)이면 이전과 같다.
    mode      : 'fixed'(고정 타이밍) 또는 'zcp'(자기발진 영교차 추종)
    fratio    : 스위칭 주파수 / 공칭 공진주파수 (zcp에서는 적분 간격을 정하는 기준 주기로만 쓴다)
    tol, rs   : 부품 공차 {'C','L','R'}와 난수 생성기(matlab_rng)
    R_in, C_in: 프리차지 저항과 입력 커패시터. R_in > 0이면 입력 커패시터 전압 0 V에서 시작한다.
    en        : 위상별 동작 여부(모듈 셰딩 시험에서 일부 위상을 끈다)
    반환값    : 파형 기록(dict). 요약 지표는 analyze()로 계산한다.
    """
    rs = rs if rs is not None else matlab_rng(0)
    C, L, R = draw_tolerance(N, tol, rs)
    en = np.ones(N, bool) if en is None else np.array(en, bool)
    Vf = BASE["Vf"]; td = BASE["tdead"]
    Nstep = int(Nstep or BASE.get("Nstep", 340))                   # (E32) 설계 묶음의 기본 단계 수(R1 340)
    fs = fratio * FR0; T = 1 / fs; dt = T / Nstep; n = ncyc * Nstep
    ndead = int(mround(td / dt)); half = Nstep // 2; ndet = int(mround(td_det / dt))
    nwait = ndead + int(mround(idle / dt))                         # (E31) 휴지 시간 포함 대기(idle = 0이면 ndead)
    off = mround(np.arange(N) * (Nstep / 2) / N).astype(int)       # 인터리빙 오프셋 T/(2N)

    # 초기조건: 정상상태 근처(v_C = V_bus = V_bat/2). 프리차지 시험은 0 V에서 시작.
    Vo0 = Vbat / 2
    iC = np.zeros(N)
    vC = np.full(N, Vo0) if vC0 is None else np.array(np.broadcast_to(np.asarray(vC0, float), (N,)), float)   # (E28) 위상별 초기값 허용
    Vb = Vo0 if Vbus0 is None else float(Vbus0)
    Vin = float(Vbat) if R_in == 0 else 0.0

    # 자기발진(zcp) 상태기계: 위상별 현재 구간, 다음 구간, 데드타임 타이머, 도통 카운터
    st = np.zeros(N, int); nxt = np.ones(N, int); tmr = -off.copy(); oncnt = np.zeros(N, int)
    armed = np.zeros(N, bool); det = np.zeros(N, int); pulse_sign = np.zeros(N)
    t_on = 0.5 / FR0 * (1 - 2 * td * FR0)                         # 공칭 도통시간
    min_on = int(mround(0.80 * t_on / dt)); max_on = int(mround(1.12 * t_on / dt))   # 블랭킹·보호 창
    nom_on = int(mround(t_on / dt)) if unarmed_stop == "nom" else max_on              # (E27) 무장 못 한 반주기의 끝

    log_i = np.zeros((n, N), np.float32); log_v = np.zeros((n, N), np.float32)
    log_vb = np.zeros(n, np.float32); log_st = np.zeros((n, N), np.int8); log_io = np.zeros((n, N), np.float32)
    log_arm = np.zeros((n, N), np.int8)                          # (E27) 무장 여부(zcp, 턴오프 분류용)
    busen = bus is not None                                      # (E24) 버스: 상태 [i_w, v_b, v_d]
    if busen:
        Rw, Lw, Cb, Rd, Cd = bus["Rw"], bus["Lw"], bus["Cb"], bus["Rd"], bus["Cd"]
        tt_p, PP_p = np.asarray(bus["P"][0], float), np.asarray(bus["P"][1], float)
        vmin_b = bus.get("vmin", 200.)
    prof = isinstance(Iload, (tuple, list))                      # (E24) 구간 선형 부하 프로파일
    if prof:
        tt_l, II_l = np.asarray(Iload[0], float), np.asarray(Iload[1], float)
    IL = float(np.interp(0., tt_l, II_l)) if prof else float(Iload)
    PL = float(np.interp(0., tt_p, PP_p)) if busen else 0.
    xb = np.zeros(3)
    if busen:                                                    # 버스 평형 근처에서 시작(V_A = V_bat/2 − R_A·I)
        iw = PL / (Vo0 - 0.0132 * PL / Vo0)
        for _ in range(5):
            vA = Vo0 - bus.get("RA", 10.2e-3) * (iw + IL); vbb = vA - Rw * iw; iw = PL / max(vbb, vmin_b)
        xb = np.array([iw, vbb, vbb]); Vb = vA if Vbus0 is None else Vb
        log_vbus = np.zeros(n, np.float32); log_iw = np.zeros(n, np.float32)
    if shed is not None:                                         # (E24) 셰딩 상태: 모드 2 둘 다, 3 멈추는 중, 1 하나, 4 복귀 대기
        sh = dict(shed); sh.setdefault("off_frac", 0.25)
        S = dict(mode=2, If=IL, tlow=0, blocked=False,
                 ndwell=int(mround(sh["t_dwell"] / dt)), noff=int(mround(sh["off_frac"] * Nstep)), a=dt / sh["tau"])
        log_sm = np.zeros(n, np.int8); log_if = np.zeros(n, np.float32); log_ig = np.zeros((n, N), np.float32)
    if mgr is not None:                                          # (E28) 모듈 관리기
        chg_on = (lambda tk: chg is not None and chg[0] <= tk < chg[1])
        M = mgr_init(mgr, N, IL, dt, chg_on(0.))
        align = bool(mgr.get("align_start"))                      # (E35) 새로 켜지는 위상을 동작 위상의 인터리빙 자리에 맞춰 시작
        fresh = M["blk"].copy(); lastk = np.full(N, -1); hp = np.full(N, half)
        flt_steps = [(int(mround(tf / dt)), int(fm)) for tf, fm in (fault or [])]
        log_na = np.zeros(n, np.int8); log_mm = np.zeros((n, N // 2), np.int8); log_if = np.zeros(n, np.float32)
        log_ig = np.zeros((n, N), np.float32); log_chg = np.zeros(n, np.int8)

    def deriv(iC, vC, Vb, s, Vin, xb):
        """구간 s(0 데드, 1 충전, 2 방전)에 따른 상태 미분과 출력·입력 전류. xb = 버스 상태(버스가 없으면 쓰지 않음)."""
        di = np.where(s == 1, (Vin - Vb - vC - iC * R) / L,
             np.where(s == 2, (Vb - vC - iC * R) / L,
             np.where(iC > 1e-3, (-vC - iC * R - 2 * Vf) / L,            # 데드타임 다이오드 환류(정방향 전류)
             np.where(iC < -1e-3, (Vin - vC - iC * R + 2 * Vf) / L, 0.0))))   # 데드타임 회생(역방향 전류)
        io = np.where(s == 1, iC, np.where(s == 2, -iC, 0.0))               # 버스로 나가는 전류
        iin = np.where(s == 1, iC, np.where((s == 0) & (iC < -1e-3), iC, 0.0))   # 입력에서 들어오는 전류
        if busen:                                                # V_A → 배선 → C_b ∥ 감쇠기 ∥ 정전력 부하
            idm = (xb[1] - xb[2]) / Rd
            dxb = np.array([(Vb - xb[1] - Rw * xb[0]) / Lw, (xb[0] - idm - PL / max(xb[1], vmin_b)) / Cb, idm / Cd])
            return di, iC / C, (io.sum() - IL - xb[0]) / Cbus, io, iin, dxb
        return di, iC / C, (io.sum() - IL) / Cbus, io, iin, xb

    for k in range(n):
        if prof:
            IL = float(np.interp(k * dt, tt_l, II_l))
        if busen:
            PL = float(np.interp(k * dt, tt_p, PP_p))
        if mode == "zcp" and shed is not None:
            log_ig[k] = iC                                       # 게이트가 본 전류(데드타임 소멸 처리 전, 회로 게이트 대조용)
            shed_step(S, sh, iC, st, tmr, ndead, en)
            log_sm[k] = S["mode"]; log_if[k] = S["If"]
        if mode == "zcp" and mgr is not None and fault:
            for nf, fm in flt_steps:                     # (E30) 모듈 고장: 위상을 바로 멈추고 관리기 후보에서 뺀다
                if k == nf:
                    mgr_fault(M, fm)
                    for kq in (2 * fm, 2 * fm + 1):
                        st[kq] = 0; tmr[kq] = 0; armed[kq] = False; det[kq] = 0; oncnt[kq] = 0
        if mode == "zcp" and mgr is not None:
            log_ig[k] = iC
            cg = chg_on(k * dt)
            mgr_step(M, iC, st, cg)
            log_na[k] = M["nact"]; log_mm[k] = M["mmode"]; log_if[k] = M["If"]; log_chg[k] = cg
        if mode == "zcp":
            # 데드타임이 끝난 위상은 다음 구간(1↔2 교대)을 시작한다.
            start = (st == 0) & (tmr >= nwait)
            if shed is not None and S["blocked"]:
                start[sh["sh"]] = False                              # 셰딩된 위상은 시작하지 않는다
            if mgr is not None:
                start &= ~M["blk"]                                   # (E28) 멈춘 모듈·셰딩된 위상은 시작하지 않는다
                if align:                                            # (E35) 막혔다 풀린 위상의 첫 시작: 기준 위상(가장 낮은 번호의
                    fresh |= M["blk"]                                #   동작 위상)의 마지막 시작 + 인터리빙 차(off) 자리에서만
                    run = np.flatnonzero((~fresh) & (~M["blk"]) & (lastk >= 0))
                    if len(run):
                        p0 = run[0]
                        for q in np.flatnonzero(start & fresh):
                            d = int((off[q] - off[p0]) % hp[p0])
                            if (k - lastk[p0] - d) % hp[p0] != 0:
                                start[q] = False
                if True:
                    for q in np.flatnonzero(start):
                        if lastk[q] >= 0 and k - lastk[q] < 1.5 * half:
                            hp[q] = k - lastk[q]
                        lastk[q] = k
                    fresh &= ~start
            st = np.where(start, nxt, st); nxt = np.where(start, 3 - nxt, nxt)
            armed = np.where(start, False, armed); det = np.where(start, 0, det)
            oncnt = np.where(start, 0, oncnt); tmr = np.where(start, 0, tmr)
            # 전류가 충분히 커지면(5·i_thr) 그 펄스의 부호를 기억하고 영교차 검출을 준비한다.
            new_arm = (st != 0) & (~armed) & (np.abs(iC) > i_thr * 5)
            pulse_sign[new_arm] = np.sign(iC[new_arm]); armed |= new_arm
            # 펄스 부호 기준으로 전류가 i_thr 아래로 돌아오면 영교차. 검출 지연(ndet 단계) 뒤 턴오프.
            if unarmed_stop == "mag":                    # (E28) 무장 전에는 부호 없는 영교차(|i| < i_thr)
                cross = (st != 0) & np.where(armed, pulse_sign * iC < i_thr, np.abs(iC) < i_thr)
            else:
                cross = (st != 0) & armed & (pulse_sign * iC < i_thr)
            det = np.where(cross, det + 1, 0); oncnt = np.where(st != 0, oncnt + 1, oncnt)
            stop = (st != 0) & (((oncnt >= min_on) & cross & (det > ndet)) | (oncnt >= max_on)
                                | ((~armed) & (oncnt >= nom_on)))
            st = np.where(stop, 0, st); tmr = np.where(stop, 0, tmr)
            tmr = np.where(st == 0, tmr + 1, tmr)
            s = st.copy()
        else:
            # 고정 타이밍: 반주기마다 구간 교대, 각 반주기 앞에 데드타임
            m = (k - off) % Nstep
            s = np.where(m < half, np.where(m >= ndead, 1, 0), np.where((m - half) >= ndead, 2, 0))
        s = np.where(en, s, 0)

        if dead_fix:                                     # (E24) 데드타임 전류가 이 간격 안에 0을 지나면 소멸
            vdrv = np.where(iC > 0, vC + 2 * Vf, Vin - vC + 2 * Vf)    # 환류 경로가 거스르는 전압
            ext = (s == 0) & (np.abs(iC) * L <= np.maximum(vdrv, 1e-9) * dt)
            iC = np.where(ext, 0.0, iC)
        # RK4 한 단계 (입력 커패시터 전압 V_in은 단계 안에서 고정)
        k1 = deriv(iC, vC, Vb, s, Vin, xb)
        k2 = deriv(iC + .5 * dt * k1[0], vC + .5 * dt * k1[1], Vb + .5 * dt * k1[2], s, Vin, xb + .5 * dt * k1[5])
        k3 = deriv(iC + .5 * dt * k2[0], vC + .5 * dt * k2[1], Vb + .5 * dt * k2[2], s, Vin, xb + .5 * dt * k2[5])
        k4 = deriv(iC + dt * k3[0], vC + dt * k3[1], Vb + dt * k3[2], s, Vin, xb + dt * k3[5])
        log_i[k] = iC; log_v[k] = vC; log_vb[k] = Vb; log_st[k] = s; log_io[k] = k1[3]
        if mode == "zcp":
            log_arm[k] = armed
        if busen:
            log_vbus[k] = xb[1]; log_iw[k] = xb[0]
            xb = xb + dt / 6 * (k1[5] + 2 * k2[5] + 2 * k3[5] + k4[5])
        iCn = iC + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        vC = vC + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        Vb = Vb + dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])
        iCn[(s == 0) & (iCn * iC <= 0)] = 0.0          # 데드타임에 다이오드 전류가 영을 지나면 차단
        iC = iCn
        if R_in > 0:                                     # 프리차지: R_in을 통한 입력 커패시터 충전
            Vin = Vin + dt * ((Vbat - Vin) / R_in - k1[4].sum()) / C_in

    t = np.arange(n) * dt
    out = dict(t=t, i=log_i, v=log_v, vb=log_vb, st=log_st, io=log_io, arm=log_arm,
               fs=fs, T=T, dt=dt, C=C, L=L, R=R, N=N)
    if shed is not None:
        out.update(sm=log_sm, If=log_if, ig=log_ig)
    if mgr is not None:
        out.update(nact=log_na, mm=log_mm, If=log_if, ig=log_ig, chg=log_chg, n_mcancel=M["mcancel"], n_pcancel=M["pcancel"],
                   flt=M["flt"].copy())
    if busen:
        out.update(vbus=log_vbus, iw=log_iw)
    return out


def shed_step(S, sh, iC, st, tmr, ndead, en):
    """(E24) 경부하 위상 셰딩 상태기계, 적분 간격마다 영교차 추종 갱신 직전에 한 번 부른다.
    회로 게이트 ctrl/prism_gate_stageA_zcps.m과 같은 순서·조건이다.
      입력 st·tmr는 직전 간격의 구간·데드타임 타이머(이 함수가 tmr[sh]를 고칠 수 있다).
      1) 모듈 출력전류 i_o = Σ(구간 1이면 +i, 구간 2이면 −i)를 1차 필터(시정수 tau)로 거른다(If).
      2) 모드 2(두 위상): |If| < I_off가 t_dwell 동안 이어지면 모드 3(멈추는 중).
      3) 모드 3: 복귀 조건이면 모드 2로 취소. 멈출 위상이 구간을 끝내 데드타임(구간 0)이면 막고(blocked) 모드 1.
         → 도통 중인 구간을 자르지 않으므로 끄는 순간도 영전류다.
      4) 모드 1(위상 하나): 복귀 조건(|If| > I_on 또는 남는 위상 |i| > I_pk,on)이면 모드 4.
      5) 모드 4: 남는 위상이 이번 간격에 구간을 시작하면(구간 0이고 타이머 ≥ n_dead) 멈춘 위상의 타이머를
         n_dead − n_off로 두고 막음을 푼다 → n_off 간격(T/4) 뒤에 시작해 인터리빙이 돌아온다. 모드 2.
         멈춘 위상은 멈추기 전 구간의 다음 구간(충전·방전 교대)부터 시작한다."""
    kp, ks = sh["keep"], sh["sh"]
    io = 0.
    for j in range(len(st)):
        if en[j]:
            io += iC[j] if st[j] == 1 else (-iC[j] if st[j] == 2 else 0.)
    S["If"] += (io - S["If"]) * S["a"]
    ret = abs(S["If"]) > sh["I_on"] or abs(iC[kp]) > sh["Ipk_on"]
    m = S["mode"]
    if m == 2:
        S["tlow"] = S["tlow"] + 1 if abs(S["If"]) < sh["I_off"] else 0
        if S["tlow"] >= S["ndwell"]:
            S["mode"] = 3
    elif m == 3:
        if ret:
            S["mode"] = 2; S["tlow"] = 0
        elif st[ks] == 0:
            S["blocked"] = True; S["mode"] = 1
    elif m == 1:
        if ret and S["noff"] < 0:                     # off_frac < 0: 기다리지 않고 바로 다시 시작(인터리빙은 맞추지 않음)
            S["blocked"] = False; S["mode"] = 2; S["tlow"] = 0
        elif ret:
            S["mode"] = 4
    elif m == 4:
        if st[kp] == 0 and tmr[kp] >= ndead:
            tmr[ks] = ndead - S["noff"]; S["blocked"] = False; S["mode"] = 2; S["tlow"] = 0


def mgr_init(cfg, N, IL, dt, chg0):
    """(E28) 모듈 관리기 상태. 모듈 모드: 0 정지, 2 두 위상, 3 위상 하나 멈추는 중, 1 위상 하나, 5 모듈 멈추는 중."""
    nm = N // 2
    if cfg.get("n0"):
        n0 = int(cfg["n0"])
    elif chg0:
        n0 = nm
    else:
        n0 = max(1, min(nm, int(np.ceil(abs(IL) / cfg["Im_up"]))))
    blk = np.zeros(N, bool)
    for m in range(n0, nm):
        blk[2 * m] = blk[2 * m + 1] = True
    return dict(cfg=cfg, nm=nm, nact=n0, If=float(IL), Ifm=np.array([IL / n0 if m < n0 else 0. for m in range(nm)]),
                tdn=0, mmode=np.array([2 if m < n0 else 0 for m in range(nm)], int), tlow=np.zeros(nm, int), blk=blk,
                a=dt / cfg["tau"], a_m=dt / cfg.get("tau_m", cfg["tau"]), ndwell=int(mround(cfg["t_dwell"] / dt)), ndwell_m=int(mround(cfg["t_dwell_m"] / dt)),
                nlock=int(mround(cfg["t_lock"] / dt)), tlock=0, nhold=int(mround(cfg.get("t_hold", 0.) / dt)), kstep=0,
                mcancel=0, pcancel=0,
                hl=list(range(nm)), rank=np.arange(nm), flt=np.zeros(nm, bool))   # (E30) 건전 모듈(번호 순), 모듈별 순위, 고장


def mgr_fault(M, m):
    """(E30) 모듈 m 고장: 관리기 후보(건전 모듈 목록 hl)에서 빼고 위상을 막는다. 동작 중이었으면 동작 수를 줄이고,
    동작 모듈이 하나도 남지 않으면 다음 건전 모듈을 바로 두 위상으로 시작한다(추가 막는 시간 n_lock을 건다).
    더 필요한 모듈은 mgr_step의 추가 규칙(충전 요청이면 건전 모듈 전부, 아니면 전류 문턱)이 정한다.
    회로 게이트 ctrl/prism_gate_stageA_zcpf.m과 같은 순서다."""
    if M["flt"][m]:
        return
    was = M["rank"][m] < M["nact"]
    M["flt"][m] = True
    M["hl"] = [x for x in M["hl"] if x != m]
    M["rank"] = np.full(M["nm"], 99)
    for j, x in enumerate(M["hl"]):
        M["rank"][x] = j
    if was:
        M["nact"] -= 1
    M["mmode"][m] = 0; M["tlow"][m] = 0
    M["blk"][2 * m] = True; M["blk"][2 * m + 1] = True
    if M["nact"] == 0 and len(M["hl"]) > 0:
        x = M["hl"][0]
        M["mmode"][x] = 2; M["tlow"][x] = 0; M["blk"][2 * x] = False; M["blk"][2 * x + 1] = False
        M["nact"] = 1; M["tdn"] = 0; M["tlock"] = M["nlock"]


def mgr_step(M, iC, st, chg):
    """(E28) 모듈 관리기와 모듈별 위상 셰딩, 적분 간격마다 영교차 추종 갱신 직전에 한 번 부른다(직전 간격의 구간 st로 판단).
    회로 게이트 ctrl/prism_gate_stageA_zcpm.m과 같은 순서·조건이다.
      1) 위상 출력전류(구간 1이면 +i, 2이면 −i)로 모듈 출력전류와 전체 출력전류를 만들고 1차 필터로 거른다
         (모듈 전류는 위상 셰딩용 계수 a, 전체 전류는 모듈 수 판단용 계수 a_m).
      2) 모듈 추가(바로): 충전 요청이거나, 추가 뒤 막는 시간(n_lock)이 지났고 |If| > 동작 수 × Im_up이거나 동작 위상의
         순시 |i| > Ipk_m이면, 충전 요청이면 모든 모듈, 아니면 max(동작 수 + 1, ceil(|If|/Im_up))개로 늘린다.
         멈추는 중이던 모듈은 취소(mcancel).
      (시작 유지) 시작 뒤 n_hold 간격 동안은 2)·3)을 하지 않는다.
      3) 모듈 줄임(지속 뒤): 충전 요청이 없고 ceil(|If|/Im_dn) < 동작 수인 상태가 n_dwell_m 이어지면 그 수로 줄인다.
         줄인 모듈은 모드 5(멈추는 중): 위상마다 지금 구간을 자연 턴오프로 끝낸 뒤(구간 0) 막는다 → 끄는 순간도 영전류.
         남는 모듈은 두 위상으로 되돌린다(위상 셰딩은 지속 조건이 다시 차면 다시 한다).
      4) 동작 모듈마다 E24와 같은 위상 셰딩(모듈 출력전류 Ifm, 남는 위상 2m, 멈추는 위상 2m+1, 복귀는 바로).
    반환하지 않고 M['blk'](위상별 시작 금지)를 고친다."""
    c = M["cfg"]; nm = M["nm"]; blk = M["blk"]; mm = M["mmode"]
    hl = M["hl"]; nh = len(hl); rk = M["rank"]          # (E30) 건전 모듈(번호 순)과 순위. 고장이 없으면 hl = 0..nm−1
    io = 0.; iom = np.zeros(nm)
    for k in range(2 * nm):
        x = iC[k] if st[k] == 1 else (-iC[k] if st[k] == 2 else 0.)
        io += x; iom[k // 2] += x
    M["If"] += (io - M["If"]) * M["a_m"]                # 모듈 수 판단용(느린 필터)
    M["Ifm"] += (iom - M["Ifm"]) * M["a"]
    nact = M["nact"]
    pk = 0.
    for k in range(2 * nm):
        if mm[k // 2] != 0 and abs(iC[k]) > pk:
            pk = abs(iC[k])
    If = abs(M["If"])
    hold = M["kstep"] < M["nhold"]                     # 시작 유지 구간: 모듈 수를 바꾸지 않는다
    if hold:
        M["kstep"] += 1
    if M["tlock"] > 0:
        M["tlock"] -= 1
    up = chg or (M["tlock"] == 0 and (If > nact * c["Im_up"] or pk > c["Ipk_m"]))
    if hold:
        M["tdn"] = 0
    elif nact < nh and up:
        new = nh if chg else min(nh, max(nact + 1, int(np.ceil(If / c["Im_up"]))))
        for m in hl[nact:new]:
            if mm[m] == 5:
                M["mcancel"] += 1
            mm[m] = 2; M["tlow"][m] = 0; blk[2 * m] = False; blk[2 * m + 1] = False
        M["nact"] = nact = new; M["tdn"] = 0; M["tlock"] = M["nlock"]
    elif (not chg) and nact > 1:
        ndn = max(1, int(np.ceil(If / c["Im_dn"])))
        M["tdn"] = M["tdn"] + 1 if ndn < nact else 0
        if M["tdn"] >= M["ndwell_m"]:
            for m in hl[ndn:nact]:
                mm[m] = 5
            for m in hl[:ndn]:                           # 남는 모듈은 두 위상으로(줄인 모듈의 전류를 위상 하나가 받지 않도록)
                if mm[m] in (1, 3):
                    mm[m] = 2; blk[2 * m + 1] = False
                M["tlow"][m] = 0
            M["nact"] = nact = ndn; M["tdn"] = 0
    else:
        M["tdn"] = 0
    noshed = bool(c.get("chg_noshed")) and chg               # (E35) 충전 요청 중에는 위상 셰딩을 하지 않는다(멈춘 위상은 바로 복귀)
    for m in range(nm):
        kp, ks = 2 * m, 2 * m + 1
        if rk[m] < nact:                                 # 동작 모듈: 위상 셰딩(E24 shed_step, 복귀는 바로)
            ret = noshed or abs(M["Ifm"][m]) > c["I_on"] or abs(iC[kp]) > c["Ipk_on"]
            if noshed and mm[m] == 2:
                M["tlow"][m] = 0
                continue
            if mm[m] == 2:
                M["tlow"][m] = M["tlow"][m] + 1 if abs(M["Ifm"][m]) < c["I_off"] else 0
                if M["tlow"][m] >= M["ndwell"]:
                    mm[m] = 3
            elif mm[m] == 3:
                if ret:
                    mm[m] = 2; M["tlow"][m] = 0; M["pcancel"] += 1
                elif st[ks] == 0:
                    blk[ks] = True; mm[m] = 1
            elif mm[m] == 1:
                if ret:
                    blk[ks] = False; mm[m] = 2; M["tlow"][m] = 0
        elif mm[m] == 5:                                 # 멈추는 모듈: 구간을 끝낸 위상부터 막는다
            if st[kp] == 0:
                blk[kp] = True
            if st[ks] == 0:
                blk[ks] = True
            if blk[kp] and blk[ks]:
                mm[m] = 0


def analyze(r, ncyc_last=10):
    """마지막 ncyc_last 주기에서 위상별 ZCS 품질과 손실, 버스 평균·리플을 계산한다.

    zcs = 턴오프 순간 전류의 최댓값 / 피크 전류.  판정 기준은 5 % 이하(보고서 표 6.1).
    """
    msk = r["t"] >= r["t"][-1] - ncyc_last * r["T"]
    Li = r["i"][msk]; Ls = r["st"][msk]; Lio = r["io"][msk]; Lb = r["vb"][msk]
    ph = []
    for k in range(r["N"]):
        ik = Li[:, k].astype(float); sk = Ls[:, k].astype(int)
        tr = np.where(np.diff(sk) != 0)[0]
        offk = tr[(sk[tr] != 0) & (sk[tr + 1] == 0)]         # 턴오프 순간
        onk = tr[(sk[tr] == 0) & (sk[tr + 1] == 1)]          # 충전 구간 시작 → 실제 스위칭 주파수
        Ipk = np.max(np.abs(ik)); ioff = np.max(np.abs(ik[offk])) if len(offk) else 0.0
        fsk = 1 / (np.mean(np.diff(onk)) * r["dt"]) if len(onk) > 2 else r["fs"]
        Pcond = np.mean(ik ** 2) * r["R"][k]
        Pdiode = np.mean((sk == 0) * 2 * BASE["Vf"] * np.abs(ik))
        if BASE.get("coss"):                                 # (E32) 하드 스위칭 출력용량 손실(노드 전압 = 버스 평균)
            Vh = float(np.mean(Lb)); Psw = 4 * qoss_pos(Vh) * Vh * fsk + 4 * BASE["Qg_E"] * fsk
        else:
            Psw = 4 * BASE["Eoss"] * fsk + 4 * BASE["Qg_E"] * fsk
        ph.append(dict(zcs=ioff / max(Ipk, 1e-6), Ipk=Ipk, Iavg=float(np.mean(Lio[:, k])),
                       fs=fsk, fr_ratio=fsk * 2 * np.pi * np.sqrt(r["L"][k] * r["C"][k]),
                       Ploss=Pcond + Pdiode + Psw))
    bus = dict(Vbus=float(np.mean(Lb)), ripple=float(np.ptp(Lb)))
    return ph, bus
