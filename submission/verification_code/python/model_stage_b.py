# -*- coding: utf-8 -*-
"""
[공통 모델] Stage B 유한 링크 2단 부분전력 조정기(PPRC) 평균모델
========================================================================
용도
  보고서 4.3절의 Stage B(절연 DAB + 부유 100 V 링크 + 4상한 H-브리지 + LC 필터)를
  스위칭 주기 평균값으로 표현한 6상태 모델이다. E2–E9의 모든 Stage B 검증이 이 모델을 쓴다.

상태변수 x (6개)
  x[0] i_p   : 직렬 경로전류(Stage A 출력 V_A → 직렬 포트 → 400 V 보조버스)   [A]
  x[1] v_s   : 직렬 포트 커패시터 전압(양·음 보상전압)                      [V]
  x[2] v_bus : 400 V 보조버스 전압                                         [V]
  x[3] i_h   : H-브리지 LC 필터 인덕터 전류                                [A]
  x[4] v_link: DAB 2차측 부유 링크 전압(공칭 100 V)                          [V]
  x[5] i_dab : DAB가 링크에 공급하는 전류(지령에 1차 지연으로 추종)             [A]
입력 u = [m, i_link_cmd]  (m: H-브리지 평균 변조율, i_link_cmd: DAB 링크전류 지령)

모델 방정식(rhs 함수)
  L  di_p/dt    = V_bat/2 − R·i_p + v_s − v_bus            (Stage A 이상 2:1 출력 + 경로저항)
  C_s dv_s/dt   = i_h − i_p                                (직렬 커패시터: 과도 시 i_p ≠ i_h)
  C_b dv_bus/dt = i_p − (P_load + P_DAB,in)/v_bus           (정전력 부하 + DAB가 버스에서 가져가는 전력)
  L_h di_h/dt   = m·v_link − v_s − R_h·i_h                   (H-브리지 평균 출력전압)
  C_l dv_link/dt= i_dab − m·i_h                              (링크 전하 수지)
  τ  di_dab/dt  = i_link_cmd − i_dab                         (DAB 전류 응답 1차 지연)
  P_DAB,in = v_link·i_dab/η (버스→링크), v_link·i_dab·η (링크→버스), η = 0.96 고정 근사

한계(판정용)
  경로·필터 100 A, 링크 80 A, 링크 8 kW, 직렬 ±90 V, 링크 90–110 V, 변조율 ±0.95,
  DAB 단일 위상천이(SPS) 전달 한계. 전류지령 포화값 84 A는 제어기 내부 값이며 실제 전류 한계가 아니다.

검증 수준의 한계
  PWM 리플, 데드타임, 기생성분, 보호 동작은 포함하지 않는다(평균모델).
"""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import brentq
from scipy.signal import place_poles


@dataclass(frozen=True)
class Parameters:
    """Stage B 회로·제어 파라미터(공칭값). 공차 시험은 dataclasses.replace로 일부만 바꿔 만든다."""
    L: float = 1.5e-6          # 직렬 경로 인덕턴스 [H]
    Cs: float = 100e-6         # 직렬 포트 커패시터 [F]
    Cb: float = 400e-6         # 400 V 보조버스 커패시터 [F]
    R: float = .0132           # 경로 저항(Stage A 출력저항 포함) [Ω]
    Lh: float = 5e-6           # H-브리지 LC 필터 인덕턴스(잠정값) [H]
    Rh: float = .002           # H-브리지 경로 저항 [Ω]
    Clink: float = .002        # 부유 링크 커패시터 2 mF(잠정값) [F]
    eta: float = .96           # DAB 방향별 효율(고정 근사)
    tau: float = 10e-6         # DAB 링크전류 응답 시정수 [s]
    Ts: float = 5e-6           # 제어 주기(200 kHz) [s]
    delay: float = 5e-6        # 연산 후 적용까지의 전달지연(모델 내 지연) [s]
    vref: float = 400.         # 보조버스 기준전압 [V]
    vlink: float = 100.        # 링크 기준전압 [V]
    modulation_max: float = .95  # 변조율 한계
    path_max: float = 100.     # 경로·필터 전류 물리 정격 [A]
    reference_max: float = 84. # 제어기 전류지령 포화값(실제 전류 한계가 아님) [A]
    link_max: float = 80.      # DAB 링크전류 정격 [A]
    power_max: float = 8000.   # DAB 링크전력 정격 [W]
    series_max: float = 90.    # 직렬 포트 전압 한계 [V]
    link_bw: float = 1000.     # 링크전압 루프 대역 [Hz]
    inner_tau: float = 10e-6   # 내부 전류 법칙의 목표 응답 시정수 [s]
    bus_bw: float = 4000.      # 극배치 기준 주파수 [Hz] (제어기 설계에서 4.8 kHz로 지정)
    Ldab: float = 11.1e-6      # DAB 누설·직렬 인덕턴스 [H]
    fs: float = 200e3          # DAB 스위칭주파수 [Hz]
    turns: float = 4.          # DAB 권선비 4:1
    phase_max: float = np.pi/3 # SPS 최대 위상천이 [rad]


def primary_power(power_link, p):
    """링크 전력 → 버스 측 DAB 전력. 양수: 버스가 링크에 공급(손실만큼 더 가져감), 음수: 링크가 버스로 반환."""
    return power_link/p.eta if power_link >= 0 else power_link*p.eta


def current_limit(vbus, vlink, p):
    """DAB 링크전류의 순시 한계 = min(정격 80 A, SPS 전달 한계, 8 kW/v_link)."""
    sps = max(vbus, 0)*p.turns*p.phase_max*(1-p.phase_max/np.pi)/(2*np.pi*p.fs*p.Ldab)
    return min(p.link_max, sps, p.power_max/max(vlink, 1e-9))


def equilibrium(vbat, power, p=Parameters()):
    """정상상태(평형점) 계산. 버스 400 V를 유지하는 경로전류 i_p를 전력수지로 푼다.
    전력수지: v_ref·i_p = P_load + P_DAB,in(v_s·i_p),  v_s = v_ref − V_bat/2 + R·i_p"""
    def balance(ip):
        vs = p.vref-vbat/2+p.R*ip
        plink = (vs+p.Rh*ip)*ip
        return p.vref*ip-power-primary_power(plink, p)
    ip = brentq(balance, -500., 500., xtol=1e-12)
    vs = p.vref-vbat/2+p.R*ip
    m = (vs+p.Rh*ip)/p.vlink
    x = np.array([ip, vs, p.vref, ip, p.vlink, m*ip])
    return x, np.array([m, m*ip])


def steady_feasible(vbat, power, p=Parameters(), control_reserve=True):
    """정상점이 포트 한계 안에 있는지(전류는 지령 포화값 기준) 판정."""
    x,u=equilibrium(vbat,power,p)
    current=p.reference_max if control_reserve else p.path_max
    return bool(abs(x[0])<=current and abs(x[1])<=p.series_max
                and abs(u[0])<=p.modulation_max
                and abs(x[5])<=current_limit(x[2],x[4],p))


def continuous_power_limit(vbat, p=Parameters(), rated_power=25000.):
    """정적 연속 한계: 정상점이 성립하는 최대 부하전력(이분 탐색). 과도 안전성은 보장하지 않는다."""
    if not steady_feasible(vbat,0,p): return 0.
    low,high=0.,rated_power
    for _ in range(50):
        mid=(low+high)/2
        if steady_feasible(vbat,mid,p): low=mid
        else: high=mid
    return low


def rhs(x, u, vbat, power, p=Parameters()):
    """6상태 평균모델의 미분방정식(모듈 설명의 식과 같음)."""
    ip, vs, vb, ih, vl, idab = x
    m, icmd = u
    pin = primary_power(vl*idab, p)
    return np.array([(vbat/2-p.R*ip+vs-vb)/p.L,
                     (ih-ip)/p.Cs,
                     (ip-(power+pin)/vb)/p.Cb,
                     (m*vl-vs-p.Rh*ih)/p.Lh,
                     (idab-m*ih)/p.Clink,
                     (icmd-idab)/p.tau])


def energy_residual(x, dx, vbat, power, p=Parameters()):
    """에너지 보존 검산(E2): 저장에너지 변화율 − (입력전력 − 저항손실 − 부하 − DAB 손실).
    모델 방정식이 에너지를 만들거나 잃지 않으면 0이어야 한다."""
    ip, vs, vb, ih, vl, idab = x
    derivative = np.dot(x[:5]*[p.L,p.Cs,p.Cb,p.Lh,p.Clink], dx[:5])
    dab_loss = primary_power(vl*idab,p)-vl*idab
    expected = vbat/2*ip-p.R*ip**2-p.Rh*ih**2-power-dab_loss
    return float(derivative-expected)


def design(vbat, power, p=Parameters()):
    """비교 설계(감쇠비 0.7)의 극배치. 축약 4상태 모델 + 버스전압 적분으로 5개 극을 배치한다.
    극: −ζω ± jω√(1−ζ²), −ω, −ω/3, −2.5ω (ω = 2π·bus_bw, ζ = 0.7). 채택 설계는 controller_adopted.py 참고."""
    xe, _ = equilibrium(vbat, power, p)
    def reduced(x):
        ip, vs, vb, ih = x
        pin = primary_power((vs+p.Rh*ih)*ih,p)
        return np.array([(vbat/2-p.R*ip+vs-vb)/p.L,(ih-ip)/p.Cs,
                         (ip-(power+pin)/vb)/p.Cb,-ih/p.inner_tau])
    h=1e-4
    J=np.column_stack([(reduced(xe[:4]+e)-reduced(xe[:4]-e))/(2*h) for e in np.eye(4)*h])  # 수치 야코비안
    A=np.zeros((5,5)); A[:4,:4]=J; A[4,2]=-1       # 5번째 상태 = 버스전압 오차 적분
    B=np.zeros((5,1)); B[3,0]=1/p.inner_tau
    w=2*np.pi*p.bus_bw; z=.7
    return place_poles(A,B,[-z*w+1j*w*np.sqrt(1-z*z),-z*w-1j*w*np.sqrt(1-z*z),-w,-w/3,-2.5*w]).gain_matrix[0]


def simulate(vbat=788., power0=5000., power1=25000., p=Parameters(),
             dt=2e-7, duration=.006, step=.001, K=None, keep_trace=False,
             control_p=None, power_fn=None, controller=None):
    """폐루프 시간영역 시뮬레이션(모든 동특성 시험의 공통 엔진).

    - 평형점에서 시작해 t = step(1 ms)에 부하를 power0 → power1로 바꾼다(power_fn을 주면 임의 프로파일).
    - 플랜트는 실제 파라미터 p, 제어기는 공칭 파라미터 control_p를 쓴다(제어기는 공차를 모른다).
    - 제어기는 Ts(5 µs)마다 지령을 계산하고, 그 지령은 p.delay만큼 늦게 플랜트에 적용된다(버퍼로 구현).
    - controller 객체를 주면 그 제어기(채택 설계)를, 없으면 이득 K로 비교 설계 제어 법칙을 쓴다.
    - 적분: 명시적 중점법, 간격 dt. 매 스텝 에너지 보존 잔차를 기록한다.
    - 판정용으로 포트별 한계 위반(violations)을 계산한다. 제어기는 지령만 제한하고 실제 상태는
      제한하지 않으므로, 과부하·지연에 의한 정격 위반이 그대로 드러난다.
    """
    cp=p if control_p is None else control_p
    if not (dt>0 and 0<=step<duration):
        raise ValueError('Require dt>0 and 0<=step<duration')
    sample=int(round(cp.Ts/dt)); lag=int(round(p.delay/dt))
    if sample<1 or abs(sample*dt-cp.Ts)>1e-12 or abs(lag*dt-p.delay)>1e-12:
        raise ValueError('dt must divide sample period and transport delay')
    if not steady_feasible(vbat,power0,p):
        raise ValueError('Initial steady state exceeds candidate operating envelope')
    K=design(vbat,power0,p) if K is None else np.asarray(K)
    x,u=equilibrium(vbat,power0,p); q=-(x[0]+K[:4]@x[:4])/K[4]; qlink=0.   # 적분기 초기값: 평형점에서 지령 = i_p
    if controller is not None: controller.reset(x,u)
    buffer=np.tile(u,(lag+1,1)); tick=0          # 전달지연 버퍼(lag 스텝 전의 지령이 적용됨)
    n=int(round(duration/dt)); log=np.empty((n,6)); controls=np.empty((n,2))
    residual=0.; stop=None; wlink=2*np.pi*cp.link_bw
    for k in range(n):
        t=k*dt; power=(power1 if t>=step else power0) if power_fn is None else power_fn(t)
        if k%sample==0 and controller is not None:
            u=controller.step(x)                  # 채택 설계(예측 기반) 제어기
        elif k%sample==0:
            # ---- 비교 설계 제어 법칙(지연 보상 없음) ----
            raw=-K[:4]@x[:4]-K[4]*q                                   # 상태궤환 + 적분 → 브리지 전류지령
            iref=np.clip(raw,-cp.reference_max,cp.reference_max)       # 지령 포화 ±84 A
            q+=cp.Ts*(cp.vref-x[2])+.1*(iref-raw)/(-K[4])              # 버스전압 적분 + 역포화 보정
            mraw=(x[1]+cp.Rh*x[3]+cp.Lh/cp.inner_tau*(iref-x[3]))/x[4] # 내부 전류 법칙 → 변조율
            m=float(np.clip(mraw,-cp.modulation_max,cp.modulation_max))
            rawlink=m*x[3]+cp.Clink*(2*.7*wlink*(cp.vlink-x[4])+wlink*wlink*qlink)  # 링크전압 PI + 소비전류 앞먹임
            limit=current_limit(x[2],x[4],cp)
            ilink=float(np.clip(rawlink,-limit,limit))
            qlink+=cp.Ts*(cp.vlink-x[4])+.1*(ilink-rawlink)/(cp.Clink*wlink*wlink)
            u=np.array([m,ilink])
        buffer[tick]=u; applied=buffer[(tick+1)%len(buffer)].copy(); tick=(tick+1)%len(buffer)
        d1=rhs(x,applied,vbat,power,p)
        residual=max(residual,abs(energy_residual(x,d1,vbat,power,p)))
        mid=x+dt*.5*d1
        x=x+dt*rhs(mid,applied,vbat,power,p)      # 명시적 중점법
        log[k]=x; controls[k]=applied
        if not np.isfinite(x).all() or x[2]<50 or x[4]<10:   # 발산(붕괴) 시 조기 종료
            stop=k; log=log[:k+1]; controls=controls[:k+1]; break
    t=(np.arange(len(log))+1)*dt
    post=log[t>=step,2]
    limit=np.array([current_limit(vb,vl,p) for vb,vl in log[:,[2,4]]])
    # 포트별 물리 한계 위반 여부
    violations={
        'path_current':bool(np.max(np.abs(log[:,0]))>p.path_max+1e-6),
        'bridge_current':bool(np.max(np.abs(log[:,3]))>p.path_max+1e-6),
        'series_voltage':bool(np.max(np.abs(log[:,1]))>p.series_max+1e-6),
        'link_current_rating':bool(np.max(np.abs(log[:,5]))>p.link_max+1e-6),
        'instantaneous_dab_envelope':bool(np.max(np.abs(log[:,5])-limit)>1e-3),
        'dab_power':bool(np.max(np.abs(log[:,4]*log[:,5]))>p.power_max+1e-3),
        'link_voltage_band':bool(np.min(log[:,4])<90 or np.max(log[:,4])>110),
        'modulation':bool(np.max(np.abs(controls[:,0]))>p.modulation_max+1e-9),
    }
    result=dict(vbat=vbat,power0=power0,power1=power1,dt=dt,duration=duration,
                droop=float(p.vref-np.min(post)),vbus_end=float(log[-1,2]),
                vbus_max=float(np.max(log[:,2])),vlink_min=float(np.min(log[:,4])),
                vlink_max=float(np.max(log[:,4])),path_peak=float(np.max(np.abs(log[:,0]))),
                bridge_peak=float(np.max(np.abs(log[:,3]))),link_peak=float(np.max(np.abs(log[:,5]))),
                series_peak=float(np.max(np.abs(log[:,1]))),dab_power_peak=float(np.max(np.abs(log[:,4]*log[:,5]))),
                modulation_peak=float(np.max(np.abs(controls[:,0]))),energy_residual_max=residual,
                completed=stop is None,end_time=float(t[-1]),violations=violations,
                within_port_limits=not any(violations.values()),
                voltage_quality_pass=bool(stop is None and np.min(post)>=392 and np.max(post)<=408 and abs(log[-1,2]-400)<=4),
                K=K.tolist(),parameters=asdict(p))
    if keep_trace: result.update(t=t,x=log,u=controls)
    return result
