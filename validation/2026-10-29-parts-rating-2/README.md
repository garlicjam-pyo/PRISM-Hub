# 부품 정격 표 2차(E37) 근거 (2026-10-29)

E34(docs/39)의 불통과 4건(C\_fly, V\_A 클램프 스위치, 바이패스 소프트 투입, W460 접촉기)과 E36(docs/41)의 이중 고장 C\_A 방전을 다른 후보 부품·설계 변경으로 다시 판정하고, A25R의 새 부품(C\_A 2.4 mF, L\_r 864.6 nH)의 요구를 정한 근거 파일이다. 문서는 [docs/42](../../docs/42_부품정격표_2차_E37.md)이다.

- **검증 코드**: `submission/verification_code/python/E37_parts_round2.py`(판정 기준은 실행 전에 커밋), 실행 뒤 진단 `E37_diag_fs.py`. `E17_protection_integration.r2_run`에 V\_A 노드 방전 저항 선택 인자를 더했다(기본 꺼짐).
- **회로 모델**: [TB29](../../simulink/tb/TB29_A25R_Clamp12/README.md)(TB28 회로 + 클램프 저항 1.2 Ω).
- **후보 데이터**: `submission/verification_code/data/datasheets/E37_*.json`(데이터시트 표·본문의 숫자만, 그림 값 없음, 출처 URL·접근일 포함).

| 파일 | 내용 |
|---|---|
| E37/ca.json | Q6 C\_A 실효전류(640·800·920 V × 공칭·표본 1)와 TDK B3277x 조합 |
| E37/fs.json | Q3 이중 고장 F2 × 방전 저항 10·3·1 Ω, E34 P7(H-브리지 역방향 도통) |
| E37/clamp\_rows.json, clamp.json | Q2 E26 클램프 사건 32개 × 변형 4개(R 1.0·1.2 Ω × 끔 463·458 V)의 기록 요약과 스위치 후보 5종 판정 |
| E37/cfly.json, cfly\_run1\_interp.json | Q1 C\_fly 후보 157품목 판정. 두 번째 파일은 바이어스 용량을 직선 보간한 1차 실행(보관) |
| E37/bypass.json, bypass\_run1\_span.json | Q4 선형 MOSFET 5종. 두 번째는 펄스 폭 보고를 고치기 전 실행 |
| E37/ctc.json, ctc\_run1\_breakmax.json | Q5 접촉기 4종. 두 번째는 단발 최대 차단 행을 넣은 1차 실행(보관) |
| E37/lr.json, req.json, table.json | Q7 L\_r 공심 추정, Q8 요구값 정리, 결과 표 |
| E37/E37\_run1.log, E37\_run2.log, E37\_diag\_fs.log | 실행 기록(ca·fs·clamp / clamp\_judge·cfly·bypass·ctc·lr·req·table), 진단 기록 |
| TB29/ | 클램프 1.2 Ω 회로 2사례 요약과 실행 기록(빌드·짧은 실행·본 실행) |

| 항목 | 결과 |
|---|---|
| Q1 C\_fly | 통과: CastorCap CC7.5u1300 × 6(45.0 µF, 180 A @ 10 kHz·30 °C, 1300 V). 100 kHz 정격 필름·CeraLink는 조건부 |
| Q2 V\_A 클램프 | 통과(설계 변경): FF450R12ME4P + 1.2 Ω·끔 463 V, 390 A·149 °C. 458 V면 135 °C. SiC FF2MR12KM1P는 원설계에서 145 °C |
| Q3 이중 고장 C\_A 방전 | **불통과**: 1 Ω 2/4(W410 통과), 3·10 Ω 0/4. 직렬 전압은 해결(≤ 67 V), W460 경로전류 소멸 6.1–6.2 ms |
| Q4 소프트 투입 선형 소자 | **불통과**(Z\_th 숫자 없음 → R\_thJC 대체 246 °C 이상) |
| Q5 W460 접촉기 | 통과: TE ECK100B, Omron G9EK-1 |
| Q6 C\_A 2.4 mF | 통과: TDK B32778Z5606 × 40(최악 실효 50.6 A, 3.1 L) |
| Q7 L\_r | 공심 3.6회·지름 60 mm, 3.1–4.2 W(모델 3.7 W) |
| TB29 | 2/2 통과: 클램프 1.2 Ω에서 V\_A ≤ 468.12 V, 흡수 441.7·144.0 J(모델 441.4·144.2 J) |
