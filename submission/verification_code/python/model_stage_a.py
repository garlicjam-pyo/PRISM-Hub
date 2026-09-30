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
              R_in=0.0, C_in=100e-6, ncyc=60, Nstep=340, vC0=None, Vbus0=None, en=None,
              td_det=20e-9, i_thr=0.5):
    """N위상 Stage A 어레이를 ncyc 주기 동안 적분한다.

    Iload     : 버스 부하전류 [A]. 음수면 역방향(버스 → 배터리) 전력.
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
    fs = fratio * FR0; T = 1 / fs; dt = T / Nstep; n = ncyc * Nstep
    ndead = int(mround(td / dt)); half = Nstep // 2; ndet = int(mround(td_det / dt))
    off = mround(np.arange(N) * (Nstep / 2) / N).astype(int)       # 인터리빙 오프셋 T/(2N)

    # 초기조건: 정상상태 근처(v_C = V_bus = V_bat/2). 프리차지 시험은 0 V에서 시작.
    Vo0 = Vbat / 2
    iC = np.zeros(N)
    vC = np.full(N, Vo0 if vC0 is None else float(vC0))
    Vb = Vo0 if Vbus0 is None else float(Vbus0)
    Vin = float(Vbat) if R_in == 0 else 0.0

    # 자기발진(zcp) 상태기계: 위상별 현재 구간, 다음 구간, 데드타임 타이머, 도통 카운터
    st = np.zeros(N, int); nxt = np.ones(N, int); tmr = -off.copy(); oncnt = np.zeros(N, int)
    armed = np.zeros(N, bool); det = np.zeros(N, int); pulse_sign = np.zeros(N)
    t_on = 0.5 / FR0 * (1 - 2 * td * FR0)                         # 공칭 도통시간
    min_on = int(mround(0.80 * t_on / dt)); max_on = int(mround(1.12 * t_on / dt))   # 블랭킹·보호 창

    log_i = np.zeros((n, N), np.float32); log_v = np.zeros((n, N), np.float32)
    log_vb = np.zeros(n, np.float32); log_st = np.zeros((n, N), np.int8); log_io = np.zeros((n, N), np.float32)

    def deriv(iC, vC, Vb, s, Vin):
        """구간 s(0 데드, 1 충전, 2 방전)에 따른 상태 미분과 출력·입력 전류."""
        di = np.where(s == 1, (Vin - Vb - vC - iC * R) / L,
             np.where(s == 2, (Vb - vC - iC * R) / L,
             np.where(iC > 1e-3, (-vC - iC * R - 2 * Vf) / L,            # 데드타임 다이오드 환류(정방향 전류)
             np.where(iC < -1e-3, (Vin - vC - iC * R + 2 * Vf) / L, 0.0))))   # 데드타임 회생(역방향 전류)
        io = np.where(s == 1, iC, np.where(s == 2, -iC, 0.0))               # 버스로 나가는 전류
        iin = np.where(s == 1, iC, np.where((s == 0) & (iC < -1e-3), iC, 0.0))   # 입력에서 들어오는 전류
        return di, iC / C, (io.sum() - Iload) / Cbus, io, iin

    for k in range(n):
        if mode == "zcp":
            # 데드타임이 끝난 위상은 다음 구간(1↔2 교대)을 시작한다.
            start = (st == 0) & (tmr >= ndead)
            st = np.where(start, nxt, st); nxt = np.where(start, 3 - nxt, nxt)
            armed = np.where(start, False, armed); det = np.where(start, 0, det)
            oncnt = np.where(start, 0, oncnt); tmr = np.where(start, 0, tmr)
            # 전류가 충분히 커지면(5·i_thr) 그 펄스의 부호를 기억하고 영교차 검출을 준비한다.
            new_arm = (st != 0) & (~armed) & (np.abs(iC) > i_thr * 5)
            pulse_sign[new_arm] = np.sign(iC[new_arm]); armed |= new_arm
            # 펄스 부호 기준으로 전류가 i_thr 아래로 돌아오면 영교차. 검출 지연(ndet 단계) 뒤 턴오프.
            cross = (st != 0) & armed & (pulse_sign * iC < i_thr)
            det = np.where(cross, det + 1, 0); oncnt = np.where(st != 0, oncnt + 1, oncnt)
            stop = (st != 0) & (((oncnt >= min_on) & cross & (det > ndet)) | (oncnt >= max_on))
            st = np.where(stop, 0, st); tmr = np.where(stop, 0, tmr)
            tmr = np.where(st == 0, tmr + 1, tmr)
            s = st.copy()
        else:
            # 고정 타이밍: 반주기마다 구간 교대, 각 반주기 앞에 데드타임
            m = (k - off) % Nstep
            s = np.where(m < half, np.where(m >= ndead, 1, 0), np.where((m - half) >= ndead, 2, 0))
        s = np.where(en, s, 0)

        # RK4 한 단계 (입력 커패시터 전압 V_in은 단계 안에서 고정)
        k1 = deriv(iC, vC, Vb, s, Vin)
        k2 = deriv(iC + .5 * dt * k1[0], vC + .5 * dt * k1[1], Vb + .5 * dt * k1[2], s, Vin)
        k3 = deriv(iC + .5 * dt * k2[0], vC + .5 * dt * k2[1], Vb + .5 * dt * k2[2], s, Vin)
        k4 = deriv(iC + dt * k3[0], vC + dt * k3[1], Vb + dt * k3[2], s, Vin)
        log_i[k] = iC; log_v[k] = vC; log_vb[k] = Vb; log_st[k] = s; log_io[k] = k1[3]
        iCn = iC + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        vC = vC + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        Vb = Vb + dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])
        iCn[(s == 0) & (iCn * iC <= 0)] = 0.0          # 데드타임에 다이오드 전류가 영을 지나면 차단
        iC = iCn
        if R_in > 0:                                     # 프리차지: R_in을 통한 입력 커패시터 충전
            Vin = Vin + dt * ((Vbat - Vin) / R_in - k1[4].sum()) / C_in

    t = np.arange(n) * dt
    return dict(t=t, i=log_i, v=log_v, vb=log_vb, st=log_st, io=log_io,
                fs=fs, T=T, dt=dt, C=C, L=L, R=R, N=N)


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
        Psw = 4 * BASE["Eoss"] * fsk + 4 * BASE["Qg_E"] * fsk
        ph.append(dict(zcs=ioff / max(Ipk, 1e-6), Ipk=Ipk, Iavg=float(np.mean(Lio[:, k])),
                       fs=fsk, fr_ratio=fsk * 2 * np.pi * np.sqrt(r["L"][k] * r["C"][k]),
                       Ploss=Pcond + Pdiode + Psw))
    bus = dict(Vbus=float(np.mean(Lb)), ripple=float(np.ptp(Lb)))
    return ph, bus
