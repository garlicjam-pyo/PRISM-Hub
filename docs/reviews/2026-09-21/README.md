# 2026-09-21 독립 엔지니어링·선행기술 검토

검토 기준은 `v0.7.0`, commit [`959efdfb8fa504d407309eb9b1217041dd93f15d`](https://github.com/garlicjam-pyo/PRISM-Hub/tree/959efdfb8fa504d407309eb9b1217041dd93f15d)입니다. 이 폴더는 해당 버전에 대한 검토 기록입니다. 이후 설계가 수정되더라도 당시 결과와 수정 후 결과를 구분해서 읽어야 합니다.

## 보고서

- [종합 검토](PRISM_Hub_종합검토.md): 결론, 우선 수정 사항, 독립 계산·재현, 선행기술 비교 및 검증 순서.
- [하드웨어 선행기술·참고문헌](hardware_prior_art.md): 논문·제품·공개특허 비교, 서지 교정과 원문 확인 범위.
- [SALS 검토](sals_review.md): 통신 지연 반례, LP 지평선, 평가 지표, 가까운 차량 부하 관리 선행기술.
- [Stage A·C 검토](stages_ac_review.md): 역방향 ZCS, 충전 공유 버스, 정격·손실·모델 및 MATLAB 정적 검토.

핵심 판정은 **설계 방향의 가치는 있으나 전력수지·양방향 동작·모드별 포트 사양·강건성을 재검증해야 하며, 현재 자료로 성능 우위나 유일성을 확정할 수 없다**는 것입니다. 이 커밋은 검토 자료를 추가하며 기존 컨버터 구현을 수정하지 않습니다.

## 독립 재현

Python 3.12.14에서 실행한 결과입니다. MATLAB은 라이선스 만료로 실행하지 못했고 관련 지적은 정적 코드 검토입니다. 하드웨어 측정 결과는 포함하지 않습니다.

저장소 루트에서 필요한 패키지를 설치하고 각 스크립트를 실행합니다. 별도 가상환경 사용을 권장합니다.

```sh
python -m pip install -r docs/reviews/2026-09-21/requirements.txt
python docs/reviews/2026-09-21/audit_pprc.py
python docs/reviews/2026-09-21/sals_checks.py
python docs/reviews/2026-09-21/probe_stage_a_reverse.py
python docs/reviews/2026-09-21/probe_stages_ac.py
```

스크립트는 위치를 기준으로 저장소의 `python/` 모듈을 읽고, 같은 검토 폴더의 결과 JSON을 갱신합니다. 따라서 재실행하면 저장된 결과 파일에 변경이 생길 수 있습니다. 원본 컨버터 모듈의 `__main__`을 실행하거나 설계 소스를 변경하지 않습니다. PPRC 스크립트에 포함한 전력수지 보완 모델은 별도 민감도 분석이며 검증 완료된 대체 설계가 아닙니다.

이후 컨버터 코드가 바뀐 상태에서 실행하면 원래 검토의 재현이 아니라 수정 후 시험이 됩니다. 원래 수치를 비교하려면 기준 커밋의 `python/` 소스와 이 폴더의 검토 스크립트를 함께 사용해야 합니다.

| 스크립트 | 결과 | 내용 |
|---|---|---|
| [audit_pprc.py](audit_pprc.py) | [JSON](audit_pprc_results.json) | 전력수지·정격 계산, 원본 과도/충전 함수, 보완 평균 모델 민감도 |
| [sals_checks.py](sals_checks.py) | [JSON](sals_checks_results.json) | H=1/15 비교, 허용 범위의 CAN 지연 반례, 샘플홀드 비교 |
| [probe_stage_a_reverse.py](probe_stage_a_reverse.py) | [JSON](probe_stage_a_reverse_results.json) | 동일 공차에서 Stage A 정·역방향 ZCS 비교 |
| [probe_stages_ac.py](probe_stages_ac.py) | [JSON](probe_stages_ac_results.json) | CLLC 입력 범위·수치 수렴, 장시간 어레이, FHA 식 비교 |

[원본 entrypoint 실행 로그](reproduce_tbb_stdout.txt)는 당시 별도 복사본에서 `tb_b_pprc2.py`를 실행한 기록입니다. 개인 로컬 경로만 저장소 상대 경로로 정리했습니다. [실행 환경](runtime_versions.txt)에는 관련 패키지만 남겼습니다. 보고서의 로컬 파일 링크와 스크립트의 경로 탐색도 GitHub 및 저장소 배치에 맞게 변경했으며, 보관한 수치 결과 자체는 변경하지 않았습니다.
