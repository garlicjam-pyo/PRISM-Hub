# 중간보고서(2026-10-26) 본문(5): 14–17장, 부록
from content_d import B, H1, H2, P, BL, TB, FG, PB
from tb11 import T11, T12, T13       # TB11–TB13 판정 문자열(results 요약에서 채움)

# ---------------------------------------------------------------- 14
H1("14. 소자 수준 회로 모델(Simulink) 현황")
H2("14.1 테스트벤치 시리즈")
P("소자 수준 회로 모델은 하나의 파일을 계속 고치지 않고 검증 단계마다 새 테스트벤치를 만들어 남겼다. 모든 모델은 빌드 스크립트로 처음부터 생성되며, 단별 서브시스템(전력단·게이트·제어·계측), 역할이 드러나는 소자 이름, 결선·파라미터를 설명하는 주석 블록, 한글 주석이 달린 제어 코드를 갖춘다. 각 테스트벤치는 같은 조건의 검증 모델 결과를 기준값으로 두어 시험 전에 고정한 기준으로 판정한다(표 {t:tb}). 10월 25일 보고 이후 TB14–TB20의 일곱 개를 더했다.")
TB("표 {t:tb}. 테스트벤치 시리즈와 판정", [1.1, 4.4, 2.0, 3.9],
   ["TB", "대상", "기준", "판정"],
   [["TB01", "Stage A 1위상 RSC, 고정 타이밍", "E1", "통과(전 지표 0.2 % 이내)"],
    ["TB02", "Stage B H-브리지(개루프), 데드타임 전압오차", "교정표", "통과(최대 차 0.135 V)"],
    ["TB03", "Stage B DAB(개루프), 위상 계단·직류 편류", "E12", "통과(0.39 A 이내)"],
    ["TB04", "Stage B 폐루프", "E12", "일치 통과(리플은 TB04B에서 결론)"],
    ["TB04B", "TB04 + 후보 소자 출력용량, 게이트 격자", "E12", "통과(0.625 ns, 리플 0.069·0.031 V)"],
    ["TB05", "Stage C CLLC 3 kW(고정이득)", "E10", "통과(이득 0.9965–1.0001)"],
    ["TB06", "통합(주행): Stage A 모듈 1 + B + C", "E12, E1, TB05", "통과 3/3"],
    ["TB07", "통합(충전): Stage A 8위상 + 충전기 + B + C", "E16, E1", "회로 한계 7/7, 일치는 조건부(충전전류 램프 ≥ 100 µs)"],
    ["TB08", "창 조정 모듈 R2-W460 + 바이패스·모드 시퀀서", "E12, E19", "통과 5/5"],
    ["TB09", "R2 보호 상태기계, 제동 저항, 소프트 투입, 감쇠기", "E17", "최종 실행 4/4(첫 실행 2사례 불통과 → 상태기계 보완)"],
    ["TB10", "DAB 고장 모드 변조(EPS 게이트, 정합 유지, 감발)", "E20", "통과 3/3(회로 기준 2배), 1.5배 목표는 붕괴 구간 초과"],
    ["TB11", "TB10 + 데드타임 반영 첨두 표", "E21", T11["verdict"] + " — 지령표 칸 전환 과도"],
    ["TB12", "TB11 + EPS 지령 전이의 직류 편류 방지·변화율 상한", "E21", T12["verdict"] + " — 전이 끝 1.3 A 초과"],
    ["TB13", "TB12 + 지령 전이 여유(설계 상한 1.387배)", "E21", T13["verdict"]],
    ["TB14", "조정형 Stage C 5 kW(동기 벅 + CLLC 직류변압기 4.8:1)", "E22", "1차 0/5(영전압 스위칭) → 재설계 뒤 2차 6/7(270 V 역방향 경부하 불통과)"],
    ["TB15", "TB14 + 경부하 두 브리지 구동", "E22", "통과 5/5"],
    ["TB16", "R2 기본형 통합: Stage A 모듈 1 + 버스 감쇠기 + 조정형 Stage C", "E23, E1", "통과 3/3"],
    ["TB17", "R2-W460 통합 강등: TB13 + Stage A·조정형 Stage C 회로", "E23, E17", "통과 2/2(강등 중 48 V ±0.03 %)"],
    ["TB18", "Stage A 경부하 위상 셰딩: 모듈 1 + R2 버스 + 충전기 전류원", "E24", "통과 5/5"],
    ["TB19", "TB17 + 위상 셰딩 게이트", "E24, E17", "통과 2/2"],
    ["TB20", "충전 중 정지: Stage A 4모듈 + 충전기 + V_A 클램프 + 버스 + 조정형 Stage C", "E26", "3/4(충전기 램프 사례 턴오프 1.01 A > 1.0 A)"]],
   "", fs=15)
H2("14.2 모델 간 차이와 해석상 유의점")
for x in ["**게이트 에지 양자화.** 게이트 에지가 적분 간격에 맞춰진다. 이 양자화가 정상상태 리밋 사이클 리플의 원인이었고(TB04·TB04B), 0.625 ns 이하에서 기준을 만족한다. TB06–TB20은 2.5 ns(TB06은 5 ns)로 과도와 한계를 판정했다.",
          "**Stage A 등가.** TB08–TB13의 V_A는 이상 전원(V_bat/2 + 13.2 mΩ + 1.5 µH)이다. TB16–TB20은 이를 Stage A 회로로 바꿔 등가가 맞음을 확인했다. 정적 등가의 유효 범위는 V_A 노드 공진(주기 약 30 µs)보다 느린 외란이다.",
          "**Stage A 모듈 수.** TB16–TB19는 모듈 하나(2위상)로 계산했다. 4모듈 8위상은 TB07·TB20이다. 모듈 셰딩과 위상 셰딩의 조합은 회로로 확인하지 않았다.",
          "**바이패스와 소프트 투입.** 바이패스·제동 저항 루프의 기생 인덕턴스와 바이패스 셀 출력용량은 넣지 않았다(투입 펄스는 상한 쪽 값). 소프트 투입은 가변 저항으로 모델링해 게이트 전압·채널 저항 관계와 소자 온도는 모델 밖이다.",
          "**시간 축 단축.** 400 V 부하 분리·감발은 시간 지연 뒤 정전력 부하가 줄어드는 것으로 모델링했고, TB09–TB19는 그 시간을 3 ms로 줄였다(평균모델 기본 20 ms). TB20은 충전기 정지 시간을 3 ms로 줄였다(규격 30 ms, 흡수 에너지는 E26).",
          "**충전기·부하.** 충전기는 이상 전류원, 400 V 부하는 정전력 등가다. 충전기의 출력 커패시터·전압 제한 루프·케이블 인덕턴스와 압축기·인버터의 스위칭 맥동은 넣지 않았다.",
          "**해석기.** 후진 오일러는 공진망에 수치 감쇠를 만든다(TB05). 조정형 Stage C의 수 MHz 레그 공진도 감쇠되지만, 가변 간격 해석과의 대조(TB14 사례 A)에서 10 µs 평균의 차는 없었다. DAB 손실은 회로 저항분만 남는다."]:
    BL(x)

# ---------------------------------------------------------------- 15
H1("15. 가설 충족 현황과 한계")
H2("15.1 가설별 현황")
P("다섯 가설 가운데 네 가설은 해당 모델 범위에서 충족했고, 기준 구조 대비 이점(H5)은 사양 팩에서 기각되어 적용 범위와 산업 방식 대비 성립 조건으로 대체했다(표 {t:status}). 모든 판정은 해당 모델과 조건 안에서만 유효하며, 하드웨어 성능을 뜻하지 않는다.")
TB("표 {t:status}. 가설별 현재 상태", [2.0, 1.9, 4.9, 2.6],
   ["가설", "상태", "근거", "남은 검증"],
   [["H1 정격 분리", "충족", "주행 링크 정상 최대 6.44 kW·과도 7.35 kW(평균)·7.19 kW(스위칭), 충전 중 정적 6.68 kW·과도 7.49 kW. 충전전류는 Stage B 비경유(회로 TB07에서 확인)", "—"],
    ["H2 강건 제어", "충족(모델 범위)", "평균모델·독립 구현·스위칭 모델 전부 통과, 회로 대표 사례 일치(TB04–TB08). 창 조정 모듈 공차 포함 456/456·264/264. 실제 Stage A·조정형 Stage C를 넣은 R2 통합 회로 TB16 3/3·TB17 2/2·TB19 2/2", "HIL·시제품"],
    ["H3 충전 중 보조버스", "충족(조건 1개)", "동시 운전 Tier-1 460/460·Tier-2 78/78, 모드 전환 240/240, 스위칭 48/48, 회로 한계 7/7(E16, TB07). 충전 중 Stage A 정지 순서와 V_A 클램프(E26 32/32, TB20 3/4)", "조건: 충전전류 증가 램프 ≥ 100 µs. 영교차 게이트 방향 반전 처리"],
    ["H4 부하 승인", "충족(축약 모델)", "예산 초과 0, 승인 지연 최대 17 ms, 미공급 7.0 %(E8)", "분리·감발 명령 연동, 전압 의존 예산"],
    ["H5 기준 구조 대비 이점", "기각(사양 팩)", "③은 ④에 손실·VA·반도체 수 모두 열세(E15)", "—"],
    ["Q3 적용 범위·산업 방식 대비", "조건부 성립", "창 조정 모듈이 B_420의 200–216s, B_470의 224–240s에서 성립 구조 중 최소 손실(E18). 400 V급 보조부품 조건에서 R2가 모터 승압 구조보다 보조 손실 26 % 작음, 800 V급 부품 설계 대비 이점 없음(E25)", "하드웨어 효율·비용"]],
   "", fs=15)
H2("15.2 현재 근거의 한계")
for x in ["**모델 수준.** 모든 결과는 시뮬레이션이다. 회로 모델의 스위치 셀은 이상 스위치, 다이오드와 선형 출력용량으로 구성되며, 소자 스위칭 손실, 게이트 드라이버, 배선 기생성분, 열, 절연과 전자기 간섭은 포함하지 않는다.",
          "**손실·정격 비교.** E15·E18·E25는 설계 단계 추정이다(대표 소자, 자성체 비율 규칙, 정적 성립성). 측정된 2:1 하드웨어(전부하 97.4 %)와 모델(99.7 %)의 차가 커서 상대 비교로만 쓴다. 모터 승압의 상저항·영상 인덕턴스는 공개 값이 없어 범위로 두었고, 리플 철손·자석 손실을 넣지 않아 모터 승압에 유리하다. 열·기생 성분·비용은 넣지 않았다.",
          "**조정형 Stage C의 하드웨어 값.** 데드타임 창의 폭이 20–30 ns라 GaN의 비선형 출력용량과 게이트 구동 지연 편차로 다시 정해야 한다. 역방향 0.6–0.74 kW에서 이득이 0.96–0.97로 기준을 최대 약 1 %p 벗어난다. 변압기 권선 용량은 넣지 않았다.",
          "**Stage A.** 통합 회로는 모듈 하나로 계산했다. 모듈 셰딩과 위상 셰딩의 조합, 위상별 공진주파수 공차에서의 셰딩 문턱, 멈춘 위상 플라잉 커패시터의 누설은 확인하지 않았다.",
          "**영교차 게이트의 방향 반전.** 반주기 첨두가 무장 문턱(2.5 A)보다 작은 방향 반전에서 턴오프 전류가 1 A를 조금 넘을 수 있다(TB20 사례 D, 1.01 A). 게이트 개선은 아직 적용하지 않았다.",
          "**충전 중 정지.** 충전기 반응 시간은 CHAdeMO 계열 규격[16]의 30 ms를 썼다. CCS 계열 규격의 비상 정지 시간은 이 조사에서 값을 확인하지 못했고, 다르면 흡수 에너지가 비례해 바뀐다. 클램프 문턱 여유가 0.6 V 수준이라 비교기·분압기 정확도가 중요하다.",
          "**보호 하드웨어.** V_A 클램프(7 kJ·220 kW), 링크 제동 저항의 펄스 정격과 반복 고장(고장당 ≤ 22 J), 바이패스 소자의 선형 영역 안전동작영역, 누설 인덕터·변압기 포화 전류(강등 중 링크 쪽 약 70 A 이상), 필터 인덕터 포화 전류(≥ 150 A)는 정격 확인이 남아 있다.",
          "**부하 쪽 응답과 범위.** 400 V 부하가 20 ms 안에 분리·감발한다고 가정했다. 창 조정 모듈의 회로 확인은 R2-W460만 했다(R2-W410은 평균모델과 스위칭 모의). 선행 조사는 12건이며 IEEE Xplore·특허 전수 검색은 하지 않았다."]:
    BL(x)

# ---------------------------------------------------------------- 16
H1("16. 향후 계획")
H2("16.1 남은 작업")
P("최종 보고(2026년 11월 말 예정)까지 남은 작업과 완료 기준은 표 {t:plan}과 같다. P0는 최종 보고에 필수인 과제, P1은 보고 전에 확인하면 주장이 단단해지는 과제, P2는 한계와 후속 과제로 넘길 항목이다.")
TB("표 {t:plan}. 남은 작업, 필요성과 완료 기준", [2.8, 0.8, 4.0, 3.8],
   ["작업", "우선", "필요성", "완료 기준"],
   [["최종 보고서", "P0", "연구 주장을 “Stage A 중심 다기능 허브 + 팩 등급 조건부 창 조정 모듈(R2)”과 그 성립 조건으로 정리", "구조·검증 범위·필요성 중심. H5 기각, 산업 방식 대비 조건, 회로의 불통과 사례를 함께 보고"],
    ["영교차 게이트 방향 반전 처리", "P1", "TB20 사례 D: 반주기 첨두가 무장 문턱보다 작은 방향 반전에서 턴오프 1.01 A", "무장하지 못한 반주기를 공칭 도통시간에 끄는 게이트로 같은 사례를 새 테스트벤치에서 재판정"],
    ["하드웨어 정격 정리", "P1", "V_A 클램프, 제동 저항, 바이패스 선형 영역, 누설·필터 인덕터 포화 전류, Stage C 데드타임을 부품 사양으로 넘겨야 한다", "데이터시트 대조와 정격 표, 반복 고장 열 계산"],
    ["Stage A 모듈·위상 셰딩 조합과 공차", "P2", "4모듈 8위상의 경부하 운전 순서와 공진주파수 공차에서의 문턱", "모듈 셰딩 + 위상 셰딩 상태기계, 공차 표본 시험"],
    ["SALS 분리·감발 연동", "P2", "강등 순서가 400 V 부하 분리·감발 명령에 의존한다", "보호 상태기계 → SALS 명령 → 부하 응답 지연 포함 시험"],
    ["DAB 지령표 연속화", "P2", "TB13의 전이 여유 5 %는 지령표에서 이웃한 칸의 최적 (D1, 위상)이 크게 다른 데서 나온다", "전류 방향 연속 제약을 둔 지령표로 전이 여유 없이 회로 1.5배 통과"],
    ["선행기술 전수 검색", "P2", "기여 주장은 12건 조사 범위의 결과다", "IEEE Xplore·특허 데이터베이스 검색과 청구항 대조"],
    ["하드웨어 실증", "후속", "실제 지연·잡음·열·전자기 간섭은 시뮬레이션으로 확인할 수 없다", "HIL, 축소전력 시제품"]],
   "", fs=15)
H2("16.2 수행 순서")
P("최종 보고서 작성을 우선한다. 영교차 게이트의 방향 반전 처리는 Stage A 게이트 함수의 작은 변경이고 회로 사례 하나로 판정할 수 있어 보고서 작성과 병행한다. 하드웨어 정격은 본 보고의 설계 요구(3.1절, 12.3절)를 부품 사양 표로 정리한다. P2 항목은 최종 보고서의 한계와 후속 과제로 넘긴다. 단계마다 대표 사례를 새 Simulink 테스트벤치로 확인하는 방식은 그대로 유지한다.")

# ---------------------------------------------------------------- 17
H1("17. 결론")
P("PRISM-Hub는 고정비 대전력 경로와 부분전력 조정을 결합해, 800 V급 차량의 충전 호환과 다중 전압 보조전원을 하나의 직류 전력 구조로 다루는 아키텍처다. 현재까지의 검증으로 연구 질문의 답이 다음과 같이 정리되었다.")
BL("**Q1(정격 분리): 긍정적.** 주행과 150 kW 충전 중 모두 링크전력이 8 kW 안이고, 충전전류는 조정단을 지나지 않는다. R2에서는 충전기가 Stage A 출력 노드에 직접 붙으므로, 충전 중 Stage A 정지를 충전기 차단과 협조시키는 V_A 클램프와 정지 순서를 함께 정했다.")
BL("**Q2(강건 제어와 부하 관리): 긍정적.** 같은 제어기가 기존 구성과 창 조정 모듈 모두에서 공차·지연을 포함한 기준을 지켰다. 고장 조건에서는 측정 기반 상태기계가 Stage A를 멈추지 않고 Stage B를 우회하며, 실제 Stage A·조정형 Stage C를 넣은 통합 회로에서도 강등 중 48 V가 ±0.03 % 안이었다. 회로 확인에서 드러난 현상(DAB 순환전류, 데드타임, 지령 전이, Stage C 영전압 전이, 역방향 경부하 이득, Stage A 경부하 영전류 스위칭)은 모두 검증 모델로 재현한 뒤 설계를 고쳤다. 영교차 게이트의 방향 반전 1건이 남았다.")
BL("**Q3(기준 구조 대비 이점): 조건부.** 전 범위 400 V 조정은 손실·정격 면에서 이점이 없어 H5가 기각되었다. 팩 등급 조건부 창 조정 모듈은 좁은 범위에서 성립 구조 가운데 손실이 가장 작다. 산업 방식과 비교하면 R2의 이점은 400 V급 보조부품을 재사용하는 조건에서만 성립한다. 이 조건에서 모터·인버터 승압 구조보다 보조 경로 손실이 26 % 작고 충전 손실도 작지만, 800 V급 보조부품 설계보다는 보조 손실이 크다. 구성 원리는 선행이 있고, 기여는 그 조합과 성립 조건, 검증으로 얻은 설계 규칙이다.")
P("이에 따라 아키텍처를 “Stage A 중심 다기능 허브 + 팩 등급 조건부 창 조정 모듈(R2)”로 정하고, 기본형(Stage A + 조정형 Stage C)까지 통합 회로에서 확인했다. 부정적 결과(H5 기각, 800 V급 부품 설계 대비 손실 열세, 회로의 불통과 사례)는 지우지 않고 설계 변경과 성립 조건의 근거로 남겼다. 남은 기간에는 이 결과를 최종 보고서로 정리한다.")

# ---------------------------------------------------------------- appendices
PB()
H1("부록 A. 주요 약어 및 용어")
TB("표 A-1. 주요 약어 및 용어", [2.0, 9.4], ["약어", "뜻"],
   [["B_420, B_470", "ISO 21498-1의 400 V급 부품 전압 하위 등급(상한 420 V, 470 V)"],
    ["CLLC", "변압기 양쪽에 인덕터와 커패시터 공진망을 두는 양방향 절연 공진형 변환기"],
    ["C_oss, C_o(tr)", "소자 출력용량과 그 시간 등가 값"],
    ["DAB", "Dual-Active-Bridge. 변압기 양쪽의 능동 브리지를 이용하는 절연형 양방향 직류-직류 변환기"],
    ["DCX", "DC Transformer. 공진점 고정 주파수로 운전해 이득이 1에 가까운 공진형 변환기(직류변압기)"],
    ["EPS", "Extended Phase Shift. DAB 한쪽 브리지의 두 레그 사이에도 위상차를 주는 변조(1차 내부 위상천이)"],
    ["HRPWM", "High-Resolution PWM. 클록 주기보다 작은 단계로 PWM 에지를 놓는 기능"],
    ["ODE", "Ordinary Differential Equation. 시간에 따른 회로 상태를 표현하는 상미분방정식"],
    ["R2, R2-W410·W460", "개선 구조와 그 창 조정 모듈(창 기준 410·460 V)"],
    ["RSC", "Resonant Switched-Capacitor Converter. 공진전류와 스위치드 커패시터를 이용하는 고정비 변환기"],
    ["SALS", "Saturation-Aware Anticipatory Load Shaping. 조정단의 정격을 고려해 지연 가능한 부하를 승인·제한하는 상위 계층"],
    ["SPS", "Single-Phase Shift. DAB 양쪽 브리지의 위상차로 전력을 조절하는 단일 위상천이 방식"],
    ["TB", "Testbench. 검증 단계별로 남긴 Simulink 회로 모델 파일"],
    ["Tier-1 / Tier-2", "계약 내 부하 변화 / 계약 위반·고장 포락선의 과도 시험 등급"],
    ["V_A, V_W", "Stage A 출력·충전기 접속 노드의 전압 / 창 조정 기준전압"],
    ["V_A 클램프", "충전 중 배터리 경로를 잃었을 때 V_A 노드의 충전기 전류를 저항으로 받는 보호 회로(468/463 V, 1 Ω)"],
    ["영교차 추종 게이트", "위상마다 공진전류의 영교차를 검출해 다음 구간을 켜는 Stage A 게이트(검출 문턱 0.5 A)"],
    ["위상 셰딩", "경부하에서 Stage A 모듈의 두 위상 중 하나를 멈추는 운전"],
    ["ZCS / ZVS", "Zero-Current / Zero-Voltage Switching. 영전류·영전압 스위칭"],
    ["①–⑥", "① 전용 승압기 + 800→400 V 강압기, ② Stage A + 전전력 조정기, ③ 기존 구성, ③′ 창 조정 변형(버스 ≤ 410 V), ④ 비조정 구조(버스 = V_A, R2 기본형), ⑤ 모터·인버터 승압 + 800→400 V 강압기, ⑥ 모터·인버터 승압 + 800 V급 보조부품"]],
   "", fs=16)
H1("부록 B. 참고문헌")
REFS = [
 "I. Aghabali, J. Bauman, P. J. Kollmeyer, Y. Wang, B. Bilgin, A. Emadi, “800-V Electric Vehicle Powertrains: Review and Analysis of Benefits, Challenges, and Future Trends,” IEEE Transactions on Transportation Electrification, vol. 7, no. 3, pp. 927–948, 2021. DOI: 10.1109/TTE.2020.3044938.",
 "B. Zhao, Q. Song, W. Liu, Y. Sun, “Overview of Dual-Active-Bridge Isolated Bidirectional DC–DC Converter for High-Frequency-Link Power-Conversion System,” IEEE Transactions on Power Electronics, vol. 29, no. 8, pp. 4091–4106, 2014. DOI: 10.1109/TPEL.2013.2289913.",
 "Z. Ni, Y. Li, C. Liu, M. Wei, D. Cao, “A 100-kW SiC Switched Tank Converter for Transportation Electrification,” IEEE Transactions on Power Electronics, vol. 35, no. 6, pp. 5770–5784, 2020. DOI: 10.1109/TPEL.2019.2954801.",
 "Y. He, S. Jiang, C. Nan, “Switched Tank Converter Based Partial Power Architecture for Voltage Regulation Applications,” IEEE APEC, pp. 91–97, 2018. DOI: 10.1109/APEC.2018.8340993.",
 "Z. Ni, Y. Li, J. Johnson, M. Wei, C. Liu, X. Lyu, D. Cao, “A GaN Switched Tank Converter with Partial Power Voltage Regulation for Electric Vehicle Applications,” IEEE APEC, pp. 1682–1689, 2019. DOI: 10.1109/APEC.2019.8722301.",
 "P. Wang, M. Chen, “Analysis and Design of Series Voltage Compensator for Differential Power Processing,” IEEE Journal of Emerging and Selected Topics in Power Electronics, vol. 10, no. 6, pp. 7890–7903, 2022. DOI: 10.1109/JESTPE.2021.3116091.",
 "S. Bibian, H. Jin, “Time Delay Compensation of Digital Control for DC Switchmode Power Supplies Using Prediction Techniques,” IEEE Transactions on Power Electronics, vol. 15, no. 5, pp. 835–842, 2000. DOI: 10.1109/63.867672.",
 "I. Kolmanovsky, E. Garone, S. Di Cairano, “Reference and Command Governors: A Tutorial on Their Theory and Automotive Applications,” American Control Conference, pp. 226–241, 2014. DOI: 10.1109/ACC.2014.6859176.",
 "ISO 21498-1:2021, “Electrically propelled road vehicles — Electrical specifications and tests for voltage class B systems and components — Part 1: Voltage sub-classes and characteristics,” Table 1.",
 "ISO 21780:2020, “Road vehicles — Supply voltage of 48 V — Electrical requirements and tests,” Clause 5.",
 "H. Chen, H. Kim, R. Erickson, D. Maksimović, “Electrified Automotive Powertrain Architecture Using Composite DC–DC Converters,” IEEE Transactions on Power Electronics, vol. 32, no. 1, pp. 98–116, 2017.",
 "Wolfspeed, “C3M0016120K Silicon Carbide Power MOSFET, 1200 V, 16 mΩ,” datasheet.",
 "onsemi (UnitedSiC), “UJ4SC075006K4S 750 V, 5.9 mΩ G4 SiC FET,” datasheet.",
 "GaN Systems (Infineon), “GS66516T Top-side cooled 650 V E-mode GaN transistor,” datasheet Rev. 210727.",
 "Efficient Power Conversion, “EPC2305 – Enhancement Mode Power Transistor (150 V, 2.2 mΩ),” datasheet(I_D,pulse 329 A at 25 °C·300 µs, V_SD 1.4 V).",
 "IEEE Std 2030.1.1-2015, “IEEE Standard Technical Specifications of a DC Quick Charger for Use with Electric Vehicles.” 시험 항목 요약: IEEE SA, “Test Cases for DC Quick Charger for Use with Electric Vehicles”(충전 허가 신호가 꺼진 뒤 30 ms 안에 출력전류 5 A 이하, 차량 접촉기는 5 A 이하까지 유지, 접촉기 차단 시 커넥터 전압 ≤ 600 V).",
 "J.-H. Jung, H.-S. Kim, M.-H. Ryu, J.-W. Baek, “Design Methodology of Bidirectional CLLC Resonant Converter for High-Frequency Isolation of DC Distribution Systems,” IEEE Transactions on Power Electronics, vol. 28, no. 4, pp. 1741–1755, 2013. DOI: 10.1109/TPEL.2012.2213346.",
 "N. Zanatta, T. Caldognetto, D. Biadene, G. Spiazzi, P. Mattavelli, “Design and Implementation of a Two-Stage Resonant Converter for Wide Output Range Operation,” IEEE Transactions on Industry Applications, 2022. DOI: 10.1109/TIA.2022.3199195.",
 "C.-E. Kim, “Minimization of Abnormal Output Voltage Rising for LLC Resonant Converter at Very Light Load,” IEEE Transactions on Industrial Electronics, vol. 67, no. 12, pp. 10295–10303, 2020. DOI: 10.1109/TIE.2019.2960730.",
 "R. D. Middlebrook, “Input Filter Considerations in Design and Application of Switching Regulators,” Proc. IEEE Industry Applications Society Annual Meeting, 1976.",
 "A. Emadi, A. Khaligh, C. H. Rivetta, G. A. Williamson, “Constant Power Loads and Negative Impedance Instability in Automotive Systems: Definition, Modeling, Stability, and Control of Power Electronic Converters and Motor Drives,” IEEE Transactions on Vehicular Technology, vol. 55, no. 4, pp. 1112–1125, 2006. DOI: 10.1109/TVT.2006.877483.",
 "K. Kesarwani, R. Sangwan, J. T. Stauth, “Resonant-Switched Capacitor Converters for Chip-Scale Power Delivery: Design and Implementation,” IEEE Transactions on Power Electronics, vol. 30, no. 12, pp. 6966–6977, 2015.",
 "Y. Ahn, I. Jeon, J. Roh, “A Multiphase Buck Converter With a Rotating Phase-Shedding Scheme For Efficient Light-Load Control,” IEEE Journal of Solid-State Circuits, vol. 49, no. 11, pp. 2673–2683, 2014. DOI: 10.1109/JSSC.2014.2360400.",
 "Hyundai Motor Group, E-GMP 플랫폼 소개(제조사 공개 자료), 2020.",
 "Lucid Group, “Lucid Gravity: Combining 450 miles EPA Range, 400 kW Fast Charging, and Access to 20,000+ Superchargers,” 보도자료, 2025.",
 "Preh GmbH, “High-Voltage Booster — Efficient charging of 800V vehicles at 400V charging stations,” 제품 소개(제조사 공개 자료).",
 "G. Qiu, V. Khadkikar, M. R. Mohammed, B. Zahawi, “Power Transfer from 400V Charging Piles to 800V Electric Vehicles Using Motor Winding and Inverter,” Proc. IEEE PEDES, 2024. DOI: 10.1109/PEDES61459.2024.10961770.",
 "M. Eull, L. Zhou, M. Jahnes, M. Preindl, “Bidirectional Nonisolated Fast Charger Integrated in the Electric Vehicle Traction Drivetrain,” IEEE Transactions on Transportation Electrification, vol. 8, no. 1, pp. 180–195, 2022. DOI: 10.1109/TTE.2021.3124936.",
 "Porsche AG, “The charging process: Quick, comfortable, intelligent and universal,” Porsche Newsroom, 2019.",
 "M. Shen, F. Guo (NIO USA), “Systems and methods for regulating charging of electric vehicles,” US Patent 10,363,828 B1 / US 10,632,863 B2.",
 "Karma Automotive, “Combined converter circuit,” US Patent 11,235,676 B2 / EP 3987646.",
]
B.append({"t": "refs", "items": REFS})
PB()
H1("부록 C. 검증 근거 목록")
P("본문의 수치는 다음 검증 근거에서 얻었다. 각 근거는 입력 조건, 판정 기준과 결과를 함께 보관하며 같은 조건에서 재현할 수 있다. 검증 코드(MATLAB, Python)와 Simulink 테스트벤치는 같은 번호 체계로 정리했다.")
TB("표 C-1. 검증 근거 목록", [1.0, 3.4, 5.2, 1.8], ["번호", "근거", "내용", "도구"],
   [["E1", "Stage A 스위칭 시험", "8위상 RSC, 고정 타이밍과 영교차 추종의 부품 공차 표본, 손실·모듈 셰딩·프리차지", "MATLAB, Python"],
    ["E2", "Stage B 평균모델 정합성", "에너지 보존, 평형점 잔차, 적분간격 수렴, 이중 구현 대조", "Python, MATLAB"],
    ["E3", "25 kW 정상상태 전력수지", "640–920 V 평형점의 경로전류, 직렬전압, 링크전력", "Python"],
    ["E4", "요구사항 분석", "부하 입력범위와 규격 대조, 보장 최소 배터리 전압", "Python"],
    ["E5–E7", "제어기 검증·지연 여유·추가 강건성", "Tier-1·Tier-2 552건, 표본화 선형화, 복합 공차 128개 코너, 부하 계약 최악 시퀀스", "Python"],
    ["E8", "부하 승인 시험", "무작위 시나리오 200개, 메시지 지연·손실, 관리 방식 3종 비교", "Python"],
    ["E9", "제어기 설계 대안 비교", "대역폭·극 배치 변경과 전압항 포화", "Python"],
    ["E10", "Stage C 스위칭 시험", "3 kW CLLC의 전압이득, 입력 변동, ZVS 여유", "MATLAB, Python"],
    ["E11", "채택 제어기 독립 구현", "MATLAB 재구현과 1,542건 대조", "MATLAB(Octave), Python"],
    ["E12", "Stage B 스위칭 모델", "PWM·데드타임·출력용량·DAB SPS, DAB 전류 제한, 데드타임 보상, 센서 사양, 게이트 시간 분해능", "Python(Numba)"],
    ["E13", "기준 구조 예비 비교", "③·③′·④의 정적 범위, Tier 시험, 감쇠기 설계", "Python"],
    ["E14", "Stage B 보호·기동", "정지·기동 전이, 링크 프리차지, 센서 고장과 타당성 감시", "Python"],
    ["E15", "기준 구조 손실·정격", "①–④의 손실(프로파일 가중), 반도체 수, 스위치 VA, H5 판정, 감도 7종", "Python"],
    ["E16", "충전 중 보조버스", "정적 범위, 동시 운전, 모드 전환, 전체 순서, 스위칭 모델", "Python(Numba)"],
    ["E17", "보호 상태기계 결합", "감시 회귀, R2 측정 기반 상태기계 117건, 정책 비교와 감도", "Python"],
    ["E18", "팩 등급별 가치 지도", "180–240s × B_420·B_470의 성립성·손실·정격, 500 V 충전기 호환", "Python"],
    ["E19", "창 조정 모듈", "DAB 정격 규칙, 공차 포함 Tier, 모드 전환, 고장 강등", "Python"],
    ["E20", "DAB 고장 모드 변조", "SPS·EPS 정확 해석과 지령표, 강등 방식 비교 40건", "Python"],
    ["E21", "고장 모드 변조의 회로 여유", "데드타임·출력용량·역방향 도통 스위칭 정상상태, TB10 재현, 첨두 표, 강등 방식 P3s·P3t(전이 여유)", "Python(Numba)"],
    ["E22", "조정형 Stage C 5 kW", "후보 손실 비교, 직류변압기 정상상태, 레그 출력용량 모델(자화 인덕턴스·데드타임), 역방향 경부하 이득, 제어 시험 8종", "Python, ngspice"],
    ["E23", "R2 통합 회로", "기본형 버스 + 조정형 Stage C 평균모델, Middlebrook 임피던스, 강등 버스 궤적의 48 V, Stage A 경부하 영전류 스위칭", "Python"],
    ["E24", "Stage A 경부하 위상 셰딩", "문턱 설계, 데드타임 전류 소멸 처리, 정상 운전점 26점, 전환 과도 10사례", "Python(Numba)"],
    ["E25", "산업 방식 대비 구조 비교", "모터·인버터 승압 충전 손실(96조합), 800 V급 보조부품 구조, 손실 에너지 예시, Stage A 손실 감도", "Python"],
    ["E26", "충전 중 Stage A 정지 협조", "모듈 과부하(스위칭 모델), V_A 노드 사건 32건(클램프 유무, 충전기 반응, 통신 지연)", "Python(Numba)"],
    ["TB01–TB05", "단별 회로", "Stage A 1위상, Stage B 개루프·폐루프(출력용량·게이트 격자), Stage C", "Simulink"],
    ["TB06–TB07", "통합 회로", "주행(Stage A 모듈 1 + B + C), 충전(8위상 + 충전기)", "Simulink"],
    ["TB08–TB13", "창 조정 모듈 회로", "창 조정·전환·DAB 고장 강등, 보호 상태기계, 고장 모드 변조, 데드타임 반영 첨두 표, EPS 지령 전이, 전이 여유", "Simulink"],
    ["TB14–TB15", "조정형 Stage C 회로", "동기 벅 + CLLC 직류변압기, 영전압 스위칭, 역방향 경부하, 두 브리지 구동", "Simulink"],
    ["TB16–TB17", "R2 통합 회로", "기본형(Stage A + 감쇠기 + 조정형 Stage C), R2-W460 강등 중 48 V", "Simulink"],
    ["TB18–TB19", "Stage A 위상 셰딩 회로", "셰딩 게이트의 전환 과도, R2-W460 강등 중 셰딩", "Simulink"],
    ["TB20", "충전 중 정지 회로", "Stage A 4모듈 + 충전기 + V_A 클램프, 경로 상실·모듈 고장·충전기 램프", "Simulink"]],
   "", fs=16)
