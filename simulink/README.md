# PRISM-Hub Simulink(Simscape Electrical) 스위칭 회로 모델

Stage A·B·C를 소자 수준 스위칭 회로로 구성하고, 검증 단계마다 **새 테스트벤치(TB) 모델 파일**을 만들어 남긴다.
각 TB는 기준값이 있는 검증 결과(Python 스위칭 ODE 모델, 해석식)와 대조해 판정한다. 전체 흐름은 docs/20 8절을 따른다.

## 폴더 구성

| 경로 | 내용 |
| --- | --- |
| `prism_hub_params.m` | 설계 파라미터·초기조건(검증 코드 E1–E14와 같은 설계값) |
| `prism_run.m` | 작업 실행기: 함수를 실행하고 `logs/<함수>.log`, `.done`에 결과를 남긴다 |
| `prism_watch.m` | 작업 대기열 감시기: `queue/*.job`(함수 이름 한 줄)을 차례로 실행. 패키지 함수만 허용 |
| `ctrl/` | MATLAB Function 블록에 들어가는 제어·게이트 코드(Stage A 게이트, Stage B 제어기·게이트) |
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
- 해석기: Simulink 고정 간격 이산 5 ns, Simscape 지역 해석기 후진 오일러 5 ns.

## 테스트벤치 진행 상태

| TB | 내용 | 기준 | 상태 |
| --- | --- | --- | --- |
| [TB01](tb/TB01_StageA_RSC/README.md) | Stage A 1위상 RSC, 고정 타이밍 0.98 f_r0 | E1 공칭 사례(Python) | **통과**(2026-10-12): 전 지표 0.2 % 이내, 턴오프 전류 2.84 %(기준 2.66 %) |
| TB02 | Stage B H-브리지 + LC(개루프), 데드타임 전압오차 | 데드타임 교정표 | 계획 |
| TB03 | Stage B DAB(개루프), 위상 계단·직류 편류 | SPS 식 | 계획 |
| TB04 | Stage B 폐루프(이상 V_A + 채택 제어기) | E12 스위칭 ODE | 계획 |
| TB05 | Stage C CLLC 3 kW(개루프) | E10 | 계획 |
| TB06 | 통합 모델(A + B + C + 부하) | — | 계획 |
