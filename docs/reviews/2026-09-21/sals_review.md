# PRISM-Hub SALS 독립 검토

검토일: 2026-09-21. 대상: `PRISM-Hub-review`의 HEAD `959efdf`. 저장소는 수정하지 않았다. 코드 검토와 독립 재현을 구분했다. 이 문서의 선행기술 평가는 기술적 중복과 연구 기여에 대한 검토이며 특허 청구항별 유효성·침해 판단은 하지 않는다.

**판정:** 포화가 예상될 때 비필수 부하를 먼저 제한하는 방향은 실용적이다. 다만 현재 구현은 시간적으로 분리된 우선순위 할당기이며, 15 ms 예측 최적화의 추가 효과가 입증되지 않았다. 강건성 주장에는 실제 허용 불확실성 범위 안의 반례가 있고, 300회 몬테카를로는 전압 안정성 시험이 아니다. 제어 기여의 신규성은 기존 CAN 기반 차량 부하 허용 제어, DC-DC 포화 관리 특허 및 reference/command governor와 비교해 대폭 좁혀야 한다.

## 1. 독립 재현 결과

재현 스크립트: [sals_checks.py](<./sals_checks.py>). 수치: [sals_checks_results.json](<./sals_checks_results.json>). Python venv의 numpy 2.3.5, scipy 1.18.1, matplotlib 3.11.2를 사용했다. 원본 모듈을 import하여 원본 함수를 호출했고, `__main__`의 결과 파일 생성 부분은 실행하지 않았다.

| 재현 항목 | 결과 | 의미 |
|---|---|---|
| H=1 대 H=15, perfect | 허용 전류 최대 차이 0.0 A | 지평선 추가 효과 없음 |
| H=1 대 H=15, −20%/+5 ms | 최대 차이 0.0 A | 동일 |
| H=1 대 H=15, robust −20%/+5 ms | 최대 차이 0.0 A | 동일 |
| H=1 대 H=15, robust early 5 ms | 최대 차이 0.0 A | 동일 |
| 허용 범위 내 CAN 지연 반례 | 피크 122.161 A, 100 A 초과 14 ms, 원본 판정 `collapse=True` | worst-case envelope가 실제 부하의 상한이 아님 |
| 같은 반례의 출력 `defer` | 세 부하 모두 0 ms | 이후 반복 제한·중단을 지연 지표가 누락 |
| 같은 반례의 99% 미만 공급 시간 | PTC 200 ms, BH 200 ms, V48 415 ms | 최초 허용 시점만으로 서비스 품질 평가 불가 |

고속 평균모델을 0–40 ms, 원본 K/Ts/C/L/Isat/Kaw, dt=0.2 µs로 재사용하면서 허용량 적용 방식만 비교했다.

| 예측 | 원본 선형 보간 vmin | 인과적인 이전 값 유지 vmin |
|---|---:|---:|
| perfect | 392.01394 V | 396.05066 V |
| robust −20%/+5 ms | 395.98226 V | 396.05066 V |

따라서 이 경우 보간을 고치면 perfect의 성능이 **좋아진다**. 비인과성이라는 구현 문제와 성능 과장 여부를 혼동해서는 안 된다. 문서의 perfect 약 8 V 대 robust 약 4 V 차이는 동일한 인과적 구현에서는 사라진다. 전체 원본 80 ms 시나리오를 재실행한 결과가 아니라 사건을 포함하는 최초 40 ms 비교다.

## 2. 중요 발견: LP는 시간마다 분리되어 지평선이 작동하지 않는다

근거: [tb_s6_sals.py:89](<https://github.com/garlicjam-pyo/PRISM-Hub/blob/959efdfb8fa504d407309eb9b1217041dd93f15d/python/tb_s6_sals.py#L89>)–99, [sals_montecarlo.py:46](<https://github.com/garlicjam-pyo/PRISM-Hub/blob/959efdfb8fa504d407309eb9b1217041dd93f15d/python/sals_montecarlo.py#L46>)–54, [wp45_predictor.py:93](<https://github.com/garlicjam-pyo/PRISM-Hub/blob/959efdfb8fa504d407309eb9b1217041dd93f15d/python/wp45_predictor.py#L93>)–100.

문제는 `max Σ_k a_k Σ_j w_j u_jk`, `0≤u_jk≤r_jk`, `Σ_j u_jk≤h_k`이다. 제약행마다 해당 시간의 변수만 존재하고, 에너지 잔량·마감시간·최소 동작시간·램프·스위칭 페널티·상태 천이가 없다. `a_k=1+0.02k>0`는 각 시간의 목적함수에 동일 양수를 곱할 뿐 우선순위나 최적해를 바꾸지 않는다. 실행하는 첫 행동은 현재 `h_0`와 `r_j0`만으로 정해진다.

세 우선순위가 1.0>0.7>0.5이므로 feasible한 경우 해는 다음과 같은 순차 할당으로 표현된다.

`u_1=min(r_1,max(h,0)); u_2=min(r_2,max(h-u_1,0)); u_3=min(r_3,max(h-u_1-u_2,0))`.

예외: 미래 시점 하나에서 비지연 부하만으로 `h_k<0`이면 전체 LP가 infeasible해지고, 코드는 현재 행동까지 전부 0으로 만든다. 이것은 미래 제약에 대응하는 동적 계획의 효과가 아니라 solver 실패에 따른 일괄 차단이다. 현재 시험들의 비지연 상한은 이 예외를 만들지 않는다.

문서 `02:400,404`의 “지평선 15 ms … 절충”, “먼 미래 지연 선호”는 현재 알고리즘으로 뒷받침되지 않는다. 1 ms LP 실행시간도 코드에 계측이 없으므로 `02:677`의 “LP 45변수 ≪1 ms, 달성”은 목표 MCU와 실제 WCET 측정 전에는 가정이다.

권고: 단순 우선순위 admission/curtailment로 정확히 명명하고 H=1·greedy를 필수 기준선에 넣는다. 예측 스케줄링의 기여를 주장하려면 부하 지연 상태, ramp/actuator delay, 최소 서비스·온도 제약, 누적 에너지 부채 및 마감시간을 연결한다. 그러면 지금 제한하거나 지금 공급하는 결정이 미래에 영향을 준다.

## 3. 중요 발견: CAN 지연을 더한 창은 강건 상한이 아니다

근거: [sals_montecarlo.py:22](<https://github.com/garlicjam-pyo/PRISM-Hub/blob/959efdfb8fa504d407309eb9b1217041dd93f15d/python/sals_montecarlo.py#L22>), [같은 파일:32](<https://github.com/garlicjam-pyo/PRISM-Hub/blob/959efdfb8fa504d407309eb9b1217041dd93f15d/python/sals_montecarlo.py#L32>)–40.

실제 onset은 `t_c+d_c`, 예측 창 시작은 `t_c+seen_delay+20 ms`다. 따라서 `d_c<seen_delay+20 ms`이면 서지가 창보다 앞선다. 늦게 받은 명령을 늦게 실행된 명령처럼 해석한 것이다.

재현 반례는 Vbat=800 V, 기본 14.9 A, 명령 t=50 ms, 실제 지연 21 ms, 서지계수 2.39, 압축기 정격 24.9 A(9.96 kW), 명령 관측 지연 15 ms, V2L 9 A, 기존 지연 가능 부하 합계 38.75 A, suspension=0 A다. 모두 선언된 범위 안이다. CAN 명령은 65 ms에 관측되지만 보수적 창은 85 ms에 시작한다. 실제 서지는 71 ms에 시작하여 제한 전 부하는 122.161 A다. 원본 스케줄러와 원본 판정 함수가 14 ms 초과와 실패를 출력했다.

수정에는 원 명령 timestamp, age/최대 전송 지연을 반영한 onset 집합이 필요하다. 수신시간 기준이면 창의 시작은 적어도 `최소 actuator delay−최대 통신 delay`만큼 앞당겨야 한다. 통신지연 30 ms가 최저 물리 지연 20 ms보다 크므로 명령을 받기 전에 서지가 발생할 수도 있다. 이 조건에서 상위 예측기만으로 보장은 불가능하다. 부하의 요청/승인 handshake, 사전 예약 또는 그 구간을 견디는 local fallback/에너지 여유가 필요하다.

문서의 신호 결측 시 창 확장(`02:560`)은 MC에서 구현되지 않았다. MC의 결측은 frame-level dropout이 아니라 episode마다 확률적으로 한 번 `seen_delay`를 부여한다. 선언된 CAN 모델과 평가 범위를 분리해야 한다.

## 4. 중요 발견: 300회 결과는 전압 붕괴 또는 버스 품질 검증이 아니다

근거: [sals_montecarlo.py:57](<https://github.com/garlicjam-pyo/PRISM-Hub/blob/959efdfb8fa504d407309eb9b1217041dd93f15d/python/sals_montecarlo.py#L57>)–73, 문서 `02:1154`–1167.

SALS와 무셰이핑의 `collapse`는 1 ms 샘플 중 `I>100 A`가 한 번이라도 있는지다. bus 상태, 전압, CPL 증가, 과부하 크기별 에너지 부족, PPRC 출력 한계는 적분하지 않는다. 100.01 A 초과와 140 A 초과는 같은 실패로 취급하고, 99.9 A에서의 동적 전압 이탈은 보지 않는다. 주석의 95 A 마진/80 A step은 `evaluate`의 합격 조건에 반영되지 않고 maxstep은 출력만 한다. 실제 저장된 최고 96.0666 A는 서두의 ≤95 A 전제부터 벗어난다.

반응형은 전혀 다른 축약식 `dip=12+2·deficit`를 사용하고 `dip>300 V`만 collapse라고 한다. 고속 모델은 `vmin<360 V`, 즉 40 V 딥을 collapse라고 한다(`tb_s6_sals.py:41`). 그래서 fast 결과의 reactive vmin≈349.97 V는 코드상 collapse=True인데 문서에서는 “생존”으로 표현된다. 서비스 규격 위반, 저전압 trip, 불안정 및 완전 전압 소실을 각각 정의해야 한다.

추가로 `Vbat∈[640,920]`이면 `|400−Vbat/2|≤80 V`이고, `min(95,7600/|ΔV|)=95 A`는 항상 일정하다(`sals_montecarlo.py:18`). 전압이 MC에서 실제 동특성이나 정격 제약을 바꾸지 않으므로 “배터리 전압 스윕까지 생존 검증”으로 해석할 수 없다.

300회 0실패 자체는 정확한 모델과 iid 분포를 전제해도 95% 단측 실패확률 상한 약 0.994%일 뿐 전 구간 보장이 아니다. 여기서는 실제 허용 범위 반례까지 있으므로 강건성 보장의 근거가 되지 않는다. `0/300 전류 초과`로 제한해서 보고하고, 동일 dynamic model/실패 기준으로 baseline을 재평가해야 한다.

## 5. 허용량 보간, 부하 서비스와 실제 동작 지연

원본 Python은 [tb_s6_sals.py:110](<https://github.com/garlicjam-pyo/PRISM-Hub/blob/959efdfb8fa504d407309eb9b1217041dd93f15d/python/tb_s6_sals.py#L110>) 및 [wp45_predictor.py:104](<https://github.com/garlicjam-pyo/PRISM-Hub/blob/959efdfb8fa504d407309eb9b1217041dd93f15d/python/wp45_predictor.py#L104>)에서 `np.interp`로 다음 tick 허용값을 미리 적용한다. 6 ms에 처음 요청한 부하가 5–6 ms에 이미 ramp한다. MATLAB은 [tb_s6_sals.m:17](<https://github.com/garlicjam-pyo/PRISM-Hub/blob/959efdfb8fa504d407309eb9b1217041dd93f15d/matlab/tb_s6_sals.m#L17>)에서 `'previous'`로 달라진다. 1절 수치처럼 이를 고치면 완전예측과 robust의 차이가 사라진다. 이는 성능이 반드시 과장되었다는 뜻이 아니라 서로 다른 입력 적용 방식으로 수치의 해석이 바뀐다는 뜻이다.

지연 지표는 `sals_montecarlo.py:63`의 최초 99% 허용 시각이다. 이후 200 ms 차단되거나 부분 공급된 경우는 지연 0 ms로 남는다. 세 부하의 요청 전력은 시간에 따라 무한히 계속되며, 미공급 에너지를 뒤에 보상하는 제약도 없다. 따라서 이 구현은 postponement뿐 아니라 curtailment이며 “200 ms 지연이라 체감 불가”를 입증하지 않는다. 총 미공급 에너지, 최초 시작지연, 최장 연속 중단, 재기동 횟수, 온도/서리제거/배터리 예열 목표 오차를 평가해야 한다.

SALS 명령 송신/조널 수신/실제 부하 응답도 현재 fast model에서는 즉시 반영된다. 문서의 PTC 5–50 ms ramp, CAN 10/20 ms, 신호 결측 모델(`02:567`–568)과 수 ms 내 부하 차단 효과를 동일시할 수 없다. anti-windup과 local dump도 실제 차단시간 및 복귀 재트립을 넣어야 한다. 현재 `Reactive`는 첫 trip 후 다시 trip하지 않는 one-shot 구현이다(`tb_s6_sals.py:148`–157).

## 6. 학습 실패 결과가 말하는 범위

합성 train/test를 episode 단위로 분리한 점, 실패도 숨기지 않은 점은 좋다. 그러나 문서 `02:1108`의 “5–15 ms 지평선 점추정에 정보가 없다”는 일반 결론은 현재 GBM 한 번의 결과보다 강하다.

이상적으로 원 명령 이후 시간이 알려지고 `D~U(20,200) ms`이며 아직 서지가 없으면 조건부 발생확률은 남은 구간에 따라 증가한다. 예를 들어 명령 후 185 ms까지 시작하지 않았다면 다음 15 ms 안의 시작확률은 1이다. 시간 이력·command age에는 정보가 있다. 기저 분포와 독립적인 지연을 정확히 점 예측하기 어렵다는 것과 미래 확률에 정보가 없다는 것은 다르다.

q0.9는 확률적 분위수이며 hard upper bound가 아니다. 희귀 순간까지 무조건 안전해야 하는 비교에서 90% 분위수 실패는 예상 가능하다. 엄밀한 비교에는 calibrated conditional upper bound, event-conditioned quantile, chance-constraint risk budget 또는 physics window와 learned refinement를 합친 safety filter가 필요하다. 이로써 학습의 보장 우열을 자동 결론 내릴 수는 없으며 실차 데이터가 먼저다.

코드상 첫 LP 시점은 `t0`지만 예측열은 `np.arange(15)+1`이고 최소 horizon5의 값을 h=1~4에 복사한다(`wp45_predictor.py:92`–100). 현재 applied move가 h=5 예측을 사실상 사용하며 시간 정렬이 명확하지 않다. 학습 데이터는 command가 50–350 ms에 들어오는데 단일 폐루프 예제는 5 ms로 초기 history/padding 분포도 다르다. `GradientBoostingRegressor(subsample=.5)`에 random_state를 주지 않아 학습 결과의 완전 재현성도 없다(`:62`).

압축기 부하는 서지 종료 시 2×정격에서 0으로 떨어진 후 정격으로 올라간다(`tb_s6_sals.py:69`, `sals_montecarlo.py:33`, `wp45_predictor.py:19`). 의도한 기동 waveform이면 근거를 제시하고, 일반적인 정격+서지 모델을 의도했다면 식을 수정해야 한다. 문서상 서지와 정상 전력 설명과 현재 식이 충분히 일치하지 않는다.

## 7. 정격·시나리오 범위와 재현성

- “8 kW = 5.3%”는 150 kW **충전 경로** 대비 정격 비율이다. PPRC가 실제 동작하는 주행 최대 25 kW 대비는 32%다. 25 kW에서의 처리전력 비율(약19%)과 설치정격 비율, 충전시 바이패스 비율을 분리한다. 100→150 A는 직렬 전류 정격 50% 증가이며, 788 V 한 점에서 8→12 kW 동등 하드웨어 비교를 실증한 것은 아니다.
- 냉시동은 피크110 A=44 kW, 정상상태가 85.25 A=34.1 kW다. 문서의 주행 max25 kW, >30 kW 모듈 추가 기동(`02:57,228`)과 달리 TB-S6는 1모듈로 고정돼 있다. 정격초과 스트레스 테스트 자체는 타당하나 실제 서비스 요구 및 module transition과 연계해야 한다.
- 확정 설계 표의 서지 envelope는 2.2×(`02:402,557`), MC는2.4×(`sals_montecarlo.py:40`)다. 범위와 적용 버전을 정합시킨다.
- 저장된 `python/results/wp45_window_rule.json`과 그림은 있으나 해당 결과를 생성하는 `wp45_window_rule.py` 또는 동등한 20/100/190 ms window fast test 코드가 저장소 Python 파일에서 검색되지 않았다. `wp45_predictor.py`는 learned q90 시험만 만들며, MC는 voltage states가 없다. 문서 `02:1110`의 핵심 window 396 V 재현 경로를 별도 스크립트로 공개해야 한다.

## 8. 선행기술 비교 — “유일하다”는 주장 불가

### 8.1 직접적으로 가까운 미인용 차량 특허

**Jaguar Land Rover, US20190023203A1, Electrical load management method and apparatus**: 2019-01-24 공개, 우선일2016-03-25, 등록판 US10829067B2. 명세서는 CAN 활성화 요청, HV/LV 네트워크의 실제/가용 전력, DC-DC 포화, 관리 가능/불가능 부하, 우선순위를 연결한다. 요청 전류와 가용 전류를 비교하여 허용·거절하거나 기존 저우선 부하를 끈다. 부분출력도 허용한다. 따라서 SALS의 CAN→headroom→priority allocation이라는 넓은 골격은 선행되어 있다. PPRC 직렬 출력의 전압 의존 한계와 지연 불확실성 창은 이 자료와의 추가 비교점이다. [공개 명세서](https://patents.google.com/patent/US20190023203A1/en), [등록판](https://patents.google.com/patent/US10829067B2/en).

**Robert Bosch, EP1053129A1, Method and device for controlling electric consumers in a motor vehicle**: 2000-11-22 공개, 우선일1998-12-15. 차량 전력공급 제약에 DC/DC 설계가 포함되고, 피크 요구를 사전 비교하며 전압 변화 허용 또는 online network model로 승인 여부를 평가한다. 우선순위 기반 전력 할당, 최소 유효전력, 다음 계산주기까지 소비자 활성화 지연을 기술한다. “부하를 먼저 협조시켜 버스를 보호”하는 원리가 새롭다는 주장을 제한한다. PRISM과 동일 회로나 동일 불확실성 알고리즘을 제시한다고 판정한 것은 아니다. [명세서](https://patents.google.com/patent/EP1053129A1/en).

### 8.2 논문과 제어 이론

**Kolmanovsky, Garone, Di Cairano (ACC2014), Reference and Command Governors: A Tutorial on Their Theory and Automotive Applications**, pp.226–241, DOI 10.1109/ACC.2014.6859176. 안정화된 내부 제어기에 명령 조정 계층을 추가하여 상태·입력 제약을 만족시키는 방법, 집합으로 제한된 불확실성 및 차량 적용을 다룬다. SALS의 상위명령 제약 계층은 이 계열과 비교해야 한다. 정격상한을 적용한 LP라는 사실만으로 새로운 제어 원리라고 보기 어렵다. [저자 소속기관 공개 원문](https://merl.com/publications/docs/TR2014-119.pdf).

**Berzi et al. (EEEIC2020), Smart Energy Management of Auxiliary Load for Electric Vehicles**, DOI10.1109/EEEIC/ICPSEurope49358.2020.9160762. 대학 저장소 초록은 보조부하와 차량동역학의 협조로 저장장치 전력 수요의 순간 중첩을 줄이는 목적을 확인해준다. 연구실 저장소에는 원문 첨부가 없다. 그러므로 문서의 “컨버터 정격제약·최악값창·LP 없음”을 이 초록만으로 확인했다고 쓰면 안 된다. 주목적이 battery demand smoothing이라는 점은 확인된다. [저자 소속 대학 저장소](https://flore.unifi.it/handle/2158/1206151).

**US9371005B2, Battery management apparatus for an electric vehicle, and method for managing same**: 컨버터 과부하 시 출력전압을 낮춰 보조배터리가 전류를 보충하거나 전부 공급하게 하여 컨버터를 피크 대신 평균 부하 수준으로 설계하는 선행기술이다. 문서가 이를 반응형 저장장치 보조와 구분한 것은 대체로 적절하다. 다만 위 JLR/Bosch 자료보다 SALS의 직접 비교대상으로 가깝지는 않다. [명세서](https://patents.google.com/patent/US9371005B2/en).

### 8.3 신규성의 가능한 범위

| 주장 | 판정 |
|---|---|
| 차량 부하를 선제적으로 제한하여 작은 컨버터를 보호 | 넓은 원리는 기존 차량 전력관리와 특허에 존재 |
| CAN 요청, manageable/nondeferrable 구분, 우선순위, 가용전류 할당 | JLR 선행과 직접 중복 |
| 상위 최적화로 내부 제어기 제약 보호 | reference/command governor 계열에 존재 |
| 15-step LP 고유 예측 성능 | 현재 구현은 H=1과 같아 기여 입증 안 됨 |
| PPRC의 동작점별 전압·전력·전류 제한과 실제 차량 지연을 함께 고려한 불확실성 모델 | 구체화하면 가능한 차별점, 현재 충분히 구현/검증되지 않음 |
| 별도 저장장치 추가 없이 정격/열/비용을 줄이고 서비스 품질을 유지하는 co-design | 하드웨어·차량시험으로 입증할 실용적 기여 후보 |

기존 문서 `02:156`의 “vehicle-to-converter 협조는 확인되지 않았다”와 `03:28`의 “가장 가까운 선행연구”는 수정이 필요하다. 정확히 동일한 PRISM-Hub 전체 조합을 이 제한된 조사에서 확인하지 못했다는 것과, 해당 아이디어가 유일하다는 것은 다른 명제다. 논문/특허 데이터베이스에서 발견하지 못했다는 사실로 유일성을 증명할 수 없다.

## 9. 다음 검증을 위한 최소 비교군과 합격 조건

1. 같은 물리 plant·샘플홀드·통신/actuator delay·서비스 요구에서 no shaping, fixed-priority greedy/current headroom, window+greedy, 실제 시간결합 LP/MPC 또는 governor, reactive local protection, 증대 하드웨어를 비교한다.
2. peak/thermal current, PPRC |Vser|·|P|·DAB phase/RMS current, Vbus 범위, state trajectory를 공통 판정식으로 평가한다. LP가 계산한 400 V 등가전류와 실제 CPL 전류도 구분한다.
3. CAN 지연/결측을 timestamp와 burst loss로 시험하고, 명령 수신 전 onset, 최악 부하 중첩, irreducible load>capacity를 결정론적 corner로 먼저 확인한다.
4. LP infeasibility·timeout·stale signal의 fallback과 부하 응답 지연을 실시간 HIL에서 측정한다. 계산시간은 MCU의 평균/99.9%/최악값과 통신 포함 전체 latency로 제시한다.
5. 총 미공급 Wh, 최장 연속 제한, 재기동, 온도/쾌적/예열시간 변화 및 150 A 대안의 비용/부피/열을 함께 제시한다. 과부하를 없애는 대신 제공 서비스를 줄인 효과를 하드웨어 우위로 오인하지 않도록 한다.

저장소가 학습의 실패를 공개하고 규칙 기반으로 목표를 좁힌 점은 긍정적이다. 다음 기여는 새로운 이름이나 LP 유무보다, 검증된 uncertainty contract와 물리적인 PPRC headroom을 사용하여 실제 서비스 제약하에서 줄일 수 있는 하드웨어 정격을 정량화하는 데 있다.
