# 최종 중간보고서 추가 분석 (2026-09-25)

`docs/13_PRISM-Hub_중간보고서_최종본.docx`의 6.4·6.6·6.8·6.9절과 그림 2·5·7·8의 근거. 기준 코드는 태그 v1.0-interim(add4822)의 유한 링크 6상태 평균모델과 공통 고정이득 제어기이며, **Python 단독 계산(MATLAB 교차검증 예정)** 이다.

| 파일 | 내용 | 생성 |
|---|---|---|
| report_analysis.json | 25 kW 정상상태 스윕(640–920 V, 10 V), 640 V 코너 여유, 5 kW 기준 과도 허용 전력(12개 전압) | `python python/report_final_analysis.py` |
| capability_parts.json | 과도 허용 전력의 전압별 중간 결과(분할 실행용) | 같은 스크립트, 전압 인자로 분할 실행 가능 |
| sals_decomposition.json | SALS 관측 전 사건 반례(800 V)의 비지연·지연 가능 성분 분해 | 보고서 작성 시 계산(스케줄 함수는 python/sals_montecarlo.py) |
| delay_ripple_check_920V.json | 920 V에서 전달지연 6.4/6.5 µs의 마지막 1 ms 리플 재계산 | 보고서 작성 시 계산 |

과도 허용 전력은 20 ms 판정(400±8 V, 최종 ±4 V, 1 ms 회복, 리플 ≤ 0.1 V, 포트 한계)을 모두 만족하는 최대 최종전력을 0.25 kW 분해능 이분 탐색으로 구한 값이다. 25 kW를 넘는 값은 연속정격이 아니며, 공차·지연·연속 스텝 여유는 포함하지 않았다.
