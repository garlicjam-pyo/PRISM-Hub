# PRISM-Hub Simulink(Simscape Electrical) 스위칭 회로 모델

Stage A·B·C를 소자 수준 스위칭 회로로 구성하고, 검증 단계마다 **새 테스트벤치(TB) 모델 파일**을 만들어 남긴다.
각 TB는 기준값이 있는 검증 결과(Python 스위칭 ODE 모델, 해석식)와 대조해 판정한다. 전체 흐름은 docs/20 8절을 따른다.

## 폴더 구성

| 경로 | 내용 |
| --- | --- |
| `prism_hub_params.m` | 설계 파라미터·초기조건(검증 코드 E1–E14와 같은 설계값) |
| `prism_run.m` | 작업 실행기: 함수를 실행하고 `logs/<함수>.log`, `.done`에 결과를 남긴다 |
| `prism_watch.m` | 작업 대기열 감시기: `queue/*.job`(함수 이름 한 줄)을 차례로 실행. 패키지 함수만 허용 |
| `ctrl/` | MATLAB Function 블록에 들어가는 제어·게이트 코드(Stage A 게이트: 고정 타이밍·영교차 추종, Stage B 제어기·게이트, Stage C 게이트, DAB 손실 등가) |
| `lib/` | 모델 생성 도우미(스위치 셀, Stage A 위상, 결선, 주석, 계측부) |
| `tools/` | 설치 조사 스크립트(블록 포트·파라미터 이름) |
| `tb/TBxx_*/` | 테스트벤치: `TBxx_init.m`(조건), `build_TBxx.m`(모델 생성), `run_TBxx.m`(실행·판정), `ref/`(기준값), `results/`(결과), `TBxx_*.slx` |

## 사용법(MATLAB R2025a, Simscape Electrical)

```matlab
cd <이 폴더>
prism_run('build_TB01')   % 모델 생성: tb/TB01_StageA_RSC/TB01_StageA_RSC.slx
prism_run('run_TB01')     % 시뮬레이션·판정: tb/TB01_StageA_RSC/results/
```

모델 파일만 열어 실행해도 된다. 모델 InitFcn이 같은 폴더의 `TBxx_init.m`을 실행해 파라미터를 준비한다.

## 모델 작성 규칙

- 결선은 포트 이름으로 한다(`simscape.addConnection`, R2025a 이상). 포트·파라미터 이름은 설치에서 조사한 값(`logs/probe_*.log`)을 따른다.
- 전력 반도체는 스위치 셀 서브시스템(이상 스위치 + 역병렬 바디 다이오드 + 선택적 출력용량)으로 만들고, 이름은 역할을 드러내게 짓는다(예: `S1_VIN_A`). 게이트는 전역 Goto/From 태그로 전달하고 셀 아이콘에 태그를 표시한다.
- 계측 신호는 전역 태그로 모아 계측부(Scope, To Workspace)에서 받는다. 판정은 To Workspace 데이터로 계산한다.
- 해석기: Simulink 고정 간격 이산 5 ns, Simscape 지역 해석기 후진 오일러 5 ns. 스위치 셀이 많은 모델(TB04 이후)은 고정 비용(모드 반복 3회)으로 실행한다. 공진 변환기(TB05)는 후진 오일러의 수치 감쇠 때문에 2.5 ns로 판정한다. 적분 간격은 게이트 에지의 시간 격자이기도 하다. 그래서 Stage B 폐루프의 정상상태 리플은 격자에 따른 리밋 사이클을 포함하고, 판정은 0.625 ns 격자로 한다(TB04B).
- 시작 표본 보호: Simscape 첫 출력 표본(t = 0)은 초기화 중의 값이다. 디지털 제어기·게이트·부하 모델의 측정 입력은 `lib/sl_startup_guard.m`으로 처음 두 간격 동안 평형점 값을 쓴다.

## 테스트벤치 진행 상태

| TB | 내용 | 기준 | 상태 |
| --- | --- | --- | --- |
| [TB01](tb/TB01_StageA_RSC/README.md) | Stage A 1위상 RSC, 고정 타이밍 0.98 f_r0 | E1 공칭 사례(Python) | **통과**(2026-10-12): 전 지표 0.2 % 이내, 턴오프 전류 2.84 %(기준 2.66 %) |
| [TB02](tb/TB02_StageB_HBridge/README.md) | Stage B H-브리지 + L_h(개루프), 데드타임 전압오차 | 제어기 데드타임 교정표 | **통과**(2026-10-12): 15사례 최대 차이 0.135 V(전체 오차 2 V) |
| [TB03](tb/TB03_StageB_DAB/README.md) | Stage B DAB(개루프), 위상 계단·변압기 직류 편류·데드타임 영역 | E12 DAB 부분(Python) | **통과**(2026-10-12): SPS 영역 0.39 A 이내, 반전 편류 −6.52 A(기준 −7.07 A). 데드타임 영역·편류 감쇠는 C_oss에 민감(정보) |
| [TB04](tb/TB04_StageB_ClosedLoop/README.md) | Stage B 폐루프(이상 V_A + 채택 제어기), 640 V 15→25 kW · 788 V 0→10 kW | E12 스위칭 ODE(같은 사례 재계산) | **일치 통과**(2026-10-13): 최저 버스 0.03 V·최대 경로전류 0.4 A 차이. 정상상태 리플은 게이트 에지 양자화의 리밋 사이클 → TB04B에서 결론 |
| [TB04B](tb/TB04B_StageB_DAB_Coss/README.md) | TB04 + DAB 소자 출력용량을 후보 소자 값(1차 335 pF·2차 1371 pF)으로 | 같음 + E12 에지 양자화 계산 | **통과**(2026-10-15, 게이트 격자 0.625 ns): 리플 0.069·0.031 V. 2.5 ns에서는 0.207·0.102 V(리밋 사이클, 직류 편류 아님) → 설계 요구 **게이트 시간 분해능 ≤ 0.625 ns** |
| [TB05](tb/TB05_StageC_CLLC/README.md) | Stage C 대칭 CLLC(개루프), 3 · 1.5 · 0.3 kW, ZVS | E10과 같은 식, 2000주기 정상상태 | **통과**(2026-10-13): 이득 0.9965–1.0001, 전류 1.6 % 이내, 레그 전이 10 ns(데드타임 50 ns)·V_ds −0.08 V. 2.5 ns 판정(후진 오일러 수치 감쇠: 5 ns에서 3 kW 34 W 등가 손실) |
| [TB06](tb/TB06_Integrated_Drive/README.md) | 통합 모델(주행 모드): Stage A 모듈 1(2위상, 영교차 추종) + Stage B + Stage C 3 kW + 정전력 부하, 640 V 15→25 kW·788 V 5→15 kW·920 V 25→15 kW | E12(Stage A 등가 전원, Stage C 정전력 부하), E1(2위상 영교차 추종), TB05 | **통과**(2026-10-22, 5 ns): E12 대비 최저 버스 ≤ 0.38 V·최대 경로전류 ≤ 1.2 A, Stage A ZCS 0.06–2.9 %·V_A ±0.1 V, 48 V 47.24–48.06 V. 리플(정보) 0.06–0.18 V |
