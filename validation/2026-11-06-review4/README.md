# 제출 전 통합 수정안 대응(E45) 근거

판정 기준과 코드는 실행 전에 커밋했다(5918311). 정리 문서는 docs/50이다. 검토 기준 커밋은 74e9437이다.

| 파일 | 내용 |
|---|---|
| `E45/h2.json` | (h2) 저장 자료(validation의 E5–E7·E12·E36) 재집계. 입력 경로·SHA-256 기록. 640 V 복합 공차 Tier-2 평균모델 102/128, 스위칭 128/128 → H2 부분 충족 |
| `E45/vmap.json` | (vmap) 경우별 실제 최소와 비교하는 판정(V2)으로 14칸 재분류. 바뀐 칸은 B\_470 200s 하나(①·④ 같은 수준) |
| `E45/power.json` | (power) 충전기 명령·손실 비교 전력, 팩별 P\*·P\_ch와 위상 수 |
| `E45/s180.json` | (s180) 180·192s 정적 버스 범위와 Stage C 입력 하한 270 V |
| `E45/dstrict.json` | (dstrict) 엄격 비교기 자체 시험과 E44 D 저장 비교 7쌍 |
| `E45/delay.json` | (delay) 클램프 켬·끔 지연 1.0·0.5 µs × 폭 × 시간 간격, 지정 모서리의 최고 온도 세 사건 |
| `E45/p5.json` | (p5) 선정식 환산온도와 평균손실, 공칭·지정 모서리 |
| `E45/brake.json` | (brake) 제동 에너지 51.9 J 사건의 펄스 수·기간 |
| `E45/repro.json` | (repro, S1) 같은 프로세스 차례 실행(Windows와 같은 경로)의 대표 사례 대 저장 결과 |
| `E45/cfly_refactor.json`, `E45/fcheck.json` | (fcheck, S2) 코드 정리 뒤 E44 F 56행 재실행과 엄격 비교 |
| `E45/run_quick.log` | h2·vmap·power·s180·dstrict 실행 기록 |
| `E45/run_long1_repro_import_failed.log` | delay·p5·brake 실행 기록. 실행 중에 E16의 병렬 실행기를 바꾼 커밋 때문에 repro에서 ImportError로 멈춤(실행 경과) |
| `E45/run_long2.log` | repro·fcheck 재실행 기록 |
