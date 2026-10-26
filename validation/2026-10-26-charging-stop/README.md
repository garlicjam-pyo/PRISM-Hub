# 충전 중 Stage A 정지 협조(E26·TB20) 근거 (2026-10-26)

R2에서 충전 중 Stage A가 멈출 때의 정지 순서와 V_A 클램프를 정하고 회로로 확인한 근거 파일이다. 문서는 [docs/31](../../docs/31_충전중_정지협조_E26_TB20.md)이다.

- **검증 코드**: `submission/verification_code`의 `E26_charging_stop.py`다. 아래 E26 파일은 그 실행 결과(`results/E26`)를 옮긴 것이다(event는 시간 이력을 뺀 요약).
- **회로 모델**: [TB20](../../simulink/tb/TB20_R2_Charging_Stop/README.md)(Stage A 4모듈 + 충전기 + 400 V 버스 + 조정형 Stage C + V\_A 클램프)다.

| 파일 | 내용 |
|---|---|
| E26/overload.json | 충전 375 A를 모듈 4·3·2개가 받을 때 모듈 하나의 위상 첨두·턴오프 전류/피크·손실(640·800·920 V) |
| E26/event_summary.json | 배터리 경로 상실·모듈 고장 사건 42건: V\_A·버스 최고, 클램프 흡수 에너지·첨두 전력·동작 시간, 클램프가 없을 때 470·600·650 V 도달 시간 |
| E26/E26_charging_stop.png | 클램프 없음·있음 V\_A, 남은 모듈 수별 위상 첨두 |
| TB20/ | TB20 요약 4사례(txt·json), 기준값 요약 |
