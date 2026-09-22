# MATLAB 실행 및 모델 수정 결과 — 2026-09-22

검토 기준 v0.7.0의 오류를 수정한 후 실제 MATLAB R2024b Update 8 및 Python에서 실행했다. [수정 내용·미완료 사항](../../docs/09_MATLAB_재검증_진행기록.md)을 함께 읽는다.

## MATLAB 재현

저장소 `matlab/` 폴더에서 다음 명령을 실행한다.

```matlab
validate_review_fixes       % 전력수지, Jacobian, 전류 한계, 양방향 ZCS 회귀시험
build_pprc_average_tb       % Simulink 평균 모델 생성, 컴파일, 실행, 파형 비교
tb_b_pprc                  % 수정한 PPRC 전체 시나리오
tb_a_array                 % Stage A MC·어레이·프리차지·셰딩 정상상태 시험
```

`validate_review_fixes`와 `build_pprc_average_tb`는 이 폴더의 JSON을 갱신한다. `prism_design_params`가 생성하는 `prism_params.mat`는 gitignore 대상이다. Simulink 모델은 base workspace 준비 없이 열어 실행할 수 있도록 상수를 포함하지만, 생성기와 다른 값으로 편집한 모델의 결과는 별도로 검증해야 한다.

## Python 재현

기존 numpy/scipy/matplotlib 환경에서 저장소 루트 기준:

```sh
python python/validate_review_fixes.py
python python/compare_matlab_results.py
```

환경은 검토 당시 Python3.12.14, NumPy2.3.5, SciPy1.18.1, Matplotlib3.11.2다. 동일 난수 seed라도 MATLAB과 NumPy의 난수열은 달라 공차 표본까지 동일하지는 않다.

## 산출물

- [MATLAB 회귀시험 결과](matlab_results.json)
- [Python 회귀시험 결과](python_results.json)
- [Simulink 생성·실행 결과](simulink_results.json)
- [MATLAB/Python 교차 비교](cross_language_results.json)
- [Stage A 전체 실행 로그](stage_a_execution.txt)
- [실행 가능한 PPRC 평균 모델](prism_pprc_average_tb.slx)

`within_port_limits`는 셀의 전압·전력·전류 한계를 뜻한다. `voltage_quality_pass`는 부하에 공급한 버스 전압 품질을 뜻하며 서로 다르다.648 V 배터리에서5→29 kW 시험은 전류 상한을 지키면서도 전압 요구를 만족하지 못하므로 `voltage_quality_pass=false`가 정상적인 회귀 결과다. 이 조건을 숨기거나 PASS로 바꾸지 않는다. 전류 지령은 버스 전압 하강에 따른 SPS 한계도 반영한다.

전체 회귀시험의 PASS는 구현의 검산과 명시한 성공/실패 시나리오가 재현됐다는 뜻이다. 모든 운전점, 실제 양극성 회로, EMI·절연·열 또는 전체 SALS의 합격을 의미하지 않는다. `.slx`는 이상 평균 모델이며 Simscape 전력 스위치 모델이 아니다.
