# -*- coding: utf-8 -*-
"""
[공통 모델] 비교 설계 제어기(지연 보상 없음)와 공통 판정 함수
========================================================================
용도
  - 보고서 6.3절의 "비교 설계": 채택 제어기와 같은 구조(상태궤환 + 적분 + 내부 전류 법칙 + 링크 PI)이나
    연산 지연 보상이 없고 주 극점 감쇠비가 0.7인 설계. 788 V·5 kW에서 한 번 계산한 이득(GAIN)을
    640–920 V 전 범위에 고정 적용한다(운전점별 이득 재계산 없음).
  - 모든 동특성 시험이 공통으로 쓰는 전압 품질 판정 함수 assess()를 정의한다.
  - E2(모델 구현 정합성)에서 Python·MATLAB 이중 구현을 비교할 때의 기준 제어기이기도 하다.

전압 품질 판정(보고서 표 2, Tier-1 전압 기준)
  1) 시뮬레이션 완료(발산·붕괴 없음)       2) 포트 물리 한계 위반 없음
  3) 스텝 후 버스전압 400 ± 8 V 이내       4) 20 ms 시점 400 ± 4 V 이내
  5) ±4 V 밖으로 나갔다면 1 ms 안에 재진입   6) 마지막 1 ms 버스 리플 ≤ 0.1 V
"""
import numpy as np
from model_stage_b import Parameters, simulate

# 제어기가 알고 있는 공칭 파라미터(극배치 기준 주파수 4.8 kHz)
NOMINAL=Parameters(bus_bw=4800.)
# 비교 설계 이득 K = [k_ip, k_vs, k_vbus, k_ih, k_q]  (788 V, 5 kW, 감쇠비 0.7에서 극배치)
GAIN=(-1.4476004429712448, -.49495671954233184, 2.935688138531015,
      .49113020413827174, -12686.999819984616)


def assess(t, x, step, completed, port_limits, vref=400.):
    """전압 품질 6개 항목 판정. 회복시간 = 마지막으로 ±4 V를 벗어났던 시점 다음 표본까지의 시간.
    시험 종료 시점까지 밖에 있으면 회복시간 없음(None)으로 실패 처리한다."""
    post=t>=step
    outside=np.flatnonzero(post & (np.abs(x[:,2]-vref)>4))
    recovery=0.
    if len(outside):
        last=outside[-1]
        recovery=None if last==len(t)-1 else float(t[last+1]-step)
    if not completed: recovery=None
    tail=x[t>=max(step,t[-1]-.001),2]          # 마지막 1 ms 버스전압
    checks=dict(completed=bool(completed),ports=bool(port_limits),
                voltage_excursion=bool(np.all(np.abs(x[post,2]-vref)<=8)),
                final_voltage=bool(abs(x[-1,2]-vref)<=4),
                recovery_1ms=bool(recovery is not None and recovery<=.001),
                final_1ms_ripple=bool(np.ptp(tail)<=.1))
    return dict(recovery_s=recovery,tail_ripple_V=float(np.ptp(tail)),
                checks=checks,requirements_pass=all(checks.values()))


def run(vbat=788., power0=1000., power1=25000., plant=NOMINAL,
        duration=.02, dt=2e-7, keep_trace=False):
    """비교 설계 제어기로 1개 스텝 시험을 실행하고 전압 품질 판정을 붙여 반환한다."""
    r=simulate(vbat,power0,power1,p=plant,K=GAIN,control_p=NOMINAL,
               duration=duration,dt=dt,keep_trace=True)
    r.update(assess(r['t'],r['x'],.001,r['completed'],r['within_port_limits']))
    r['delta_current_equivalent_A']=(power1-power0)/400.
    r['continuous_rating_exceeded']=max(abs(power0),abs(power1))>25000
    if not keep_trace:
        for key in ['t','x','u']: r.pop(key)
    return r
