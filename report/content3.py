from content2 import B, H1, H2, P, BL, TB, FG, PB

# ---------------------------------------------------------------- 7
H1("7. 현재까지의 성과, 한계 및 기술 성숙도")
H2("7.1 현재까지 확보한 성과")
for x in ["Stage B의 DAB 입력전력, 유한 링크 저장에너지와 방향별 효율을 반영한 에너지 보존 평균모델과 포트별 정격 판정 체계를 구축했다.",
          "25 kW 보조버스에서 Stage B 처리전력이 최대 6.44 kW(25.7 %)이고 충전전류가 조정단을 지나지 않음을 평균모델에서 확인했다(가설 H1의 부분 근거).",
          "하나의 고정 제어이득으로 공칭 지연 조건의 정상시험 41건(회생·0 V 통과 포함)과 단일 변수 공차시험 28건을 통과했고, 640 V 코너 여유·지연 실패 양상·전압별 과도 허용 전력을 정량화해 재설계 목표를 정했다.",
          "Stage A 스위칭 ODE 모델에서 위상별 자기발진 영교차 추종으로 정·역방향 공차 표본의 ZCS를 확보했다.",
          "실패 조건(과부하, 제어 여유 제거, 추가 지연, SALS 관측 전 사건)을 회귀시험으로 보존하고, Python·MATLAB 별도 구현으로 판정 재현성을 확인했다."]:
    BL(x)
H2("7.2 남은 한계와 위험")
for x in ["요구사항: 보조버스 조정(400±8 V)의 근거, 부하 등급과 단시간 정격, 640 V 보장 하한이 확정되지 않았다. 스트레스 부하의 비지연 최악값(91.16 A)은 25 kW 연속정격을 넘는다.",
          "제어 여유: 640 V 코너의 전류 여유가 약 2 A, 감쇠·지연 여유가 1.5–2.5 µs에 그친다. 공차시험은 단일 변수만 변경했으며, 복합 공차, 온도, 센서 오차와 잡음, 배터리 전압의 운전 중 변화와 실제 구동지연을 함께 적용하지 않았다.",
          "모델 수준: 평균 H-브리지와 DAB 모델에는 PWM, 데드타임, 스위칭 리플, 소자 기생성분, 게이트 구동, 영전압 스위칭(Zero-Voltage Switching, ZVS), 고장 차단과 프리차지가 포함되지 않았다. 고정 96 % DAB 효율은 정밀 손실지도가 아니며, 2 mF 링크 커패시터와 5 µH 필터는 잠정 모델값이다.",
          "통합: 충전기, Stage A, Stage B, 400 V 보조부하와 Stage C를 하나의 모델에서 연결한 모드 전환시험이 없다. 충전기 접속·해제, 적분기 초기화, 무충격 전환(bumpless transfer), 회생 중 고장과 보조전원 유지가 미검증이다.",
          "SALS: 현재 구현은 전압과 무관한 정적 예산을 쓰며, 과도 허용 전력, 부하 등급별 최대 지연과 부하 측 ECU의 선행 승인 절차가 구현되지 않았다. 전압 안정성과 서비스 품질을 보증하지 않는다.",
          "비교: 효율, 부피, 질량과 비용의 비교가 동일 조건의 기준 구조와 수행되지 않았다. 자기소자 정격의 감소를 제품 부피나 원가 감소로 직접 환산할 수 없으며, RSC의 커패시터, 공진 인덕터, 버스바, 구동기, 센서, 냉각과 전자기 간섭 대책을 모두 포함해야 한다."]:
    BL(x)
H2("7.3 현재 기술성숙도 판정")
P("현재 PRISM-Hub는 재현 가능한 평균모델, 스위칭 ODE 모델과 실패 회귀시험을 갖춘 시뮬레이션 기반 연구 개발 단계다. 전력수지와 Stage B 후보 제어기의 공칭 조건 운전 가능성은 확인됐으나, 스위칭 회로, 열, 보호, 전체 모드 통합, 시제품과 차량 검증은 후속 단계로 남아 있다.")
P("현재 증거가 지지하는 결론은 “공칭 지연과 단일 변수 공차 조건에서 Stage B 2단 후보의 평균모델상 운전 가능성을 확인했으며, 640 V 코너의 여유는 부족하다”는 것이다. 전체 아키텍처, 전 운전영역 강건성, 실측 효율, 기준 구조 대비 부피·비용 및 모든 통신 지연에 대한 안전성은 후속 검증 항목이다.")
H2("7.4 최초 계획 대비 진척")
P("보고일은 18주 계획의 3주차 종료 시점이다. 작업패키지(Work Package, WP)별 상태는 표 14와 같다.")
TB("표 14. 최초 계획 대비 작업패키지별 진척", [3.4, 1.6, 6.4],
   ["작업패키지(최초 계획)", "현재 상태", "주요 결과와 남은 작업"],
   [["WP1 요구사항·구조·파라미터 확정", "개정 중", "V_A 접속, 바이패스 폐지, 포트별 정격 재정의 완료. 보조버스 조정 근거, 부하 등급, 보장 하한 미확정"],
    ["WP2 평균모델·제어·상태기계", "진행 중", "Stage B 6상태 모델과 고정 제어기 완료. 통합 상태기계 미완료"],
    ["WP3 Simscape 스위칭 모델", "미착수", "선행으로 Stage A 스위칭 ODE 완료. Stage A·B·C Simscape 미착수"],
    ["WP4 시나리오·기준 구조 검증", "진행 중", "Stage B 동특성과 경계, 과도 허용 전력 확보. 기준 구조 비교 미착수"],
    ["WP4.5 선행 조정·부하 관리", "범위 변경", "학습 기반 예측 피드포워드(ARL) 폐기, 인과적 부하 승인(SALS)으로 전환"],
    ["WP5 손실·열·전력밀도", "예비 착수", "Stage A 예비 손실값만 확보"],
    ["WP6 문서화·재현자료", "진행 중", "실행 근거, 실패 회귀시험, 본 보고서"]],
   "자료: 저자 작성. 최초 계획은 저장소 docs/01 제안서 4.3절의 18주 일정이다.")
P("현재까지의 핵심 진전은 구성요소 모델의 수를 늘린 데 있지 않고, 기존 모델의 전력수지 오류와 인과성 문제를 찾아 설계경계를 수정한 데 있다. 이에 따라 요구사항·수락 기준 확정, 제어기 재설계, WP3의 스위칭 모델과 WP4의 통합·기준 구조 비교를 다음 우선순위로 배치했다.")

# ---------------------------------------------------------------- 8
H1("8. 향후 연구 계획")
H2("8.1 요구사항, 부하 등급과 수락 기준 확정")
P("다음 네 항목을 첫 과제로 확정한다. (1) 400 V 부하와 저전압 변환기의 허용 입력범위를 부품 사양으로 확인해 보조버스 조정 요구(3.2절)를 확정하거나 완화한다. (2) 부하별 연속·단시간 정격, 서지 계수와 지속시간, 부하 등급과 등급별 최대 지연을 정의하고 25 kW 연속정격과의 관계를 정한다(3.5절). (3) 부하, 저항강하, 링크전압 하한과 공차를 포함해 보장 최소 배터리 전압을 정한다. (4) 가설별 수락 기준을 확정한다. 수락 기준은 설계 목표가 되므로 기준 구조 비교 전에 정한다. 표 15는 이번 보고에서 제안하는 잠정 기준이다.")
TB("표 15. 가설별 잠정 수락 기준(안)", [2.2, 3.0, 3.4, 2.8],
   ["가설(질문)", "판정 지표", "잠정 기준(안)", "현재 상태"],
   [["H1 정격 분리(Q1)", "640–920 V·25 kW에서 Stage B 링크전력, 충전전류 경로", "링크 ≤ 8 kW(정상·과도), 충전전류 Stage B 비경유", "모델상 충족(정상 6.44 kW, 과도 7.41 kW). 충전 중 동시 운전 미검증"],
    ["H2 강건 제어(Q2)", "복합 공차·추가 지연에서 포트 정격과 전압 품질", "경로·필터 ≤ 90 A, 추가 지연 +2.5 µs에서 전압 기준 만족", "미충족(경로 98.0 A, 전 기준 통과 지연 여유 +1.2 µs)"],
    ["H3 충전 중 보조버스(Q1)", "150 kW(375 A 제한) 충전 + 25 kW 보조부하 동시 운전", "400±8 V, 포트 정격 만족, 모드 전환 시 경로 ≤ 100 A", "미검증"],
    ["H4 부하 승인(Q2)", "정의된 부하 등급·지연 범위의 스트레스 시험", "정격 초과 0건, 비지연 부하 기동 지연 ≤ 20 ms, 지연 가능 부하 최대 지연 ≤ 200 ms", "미충족(정적 예산, 반례 존재)"],
    ["H5 기준 구조 대비 이점(Q3)", "기준 구조 ①·④ 대비 동일 경계 비교", "손실·정격 VA·부품 수 중 2개 이상 개선, 서비스 품질 동등", "미평가"]],
   "자료: 저자 작성. 기준값은 8.1절에서 확정할 제안값이며, 이번 보고의 판정 근거가 아니다.", fs=16)
P("완료 기준은 모든 운전 모드의 포트 전압·전류·전력 방향, 연속·피크 정격, 접촉기 상태와 고장 시 안전상태가 하나의 사양표와 회로도에서 일치하고, 표 15의 기준이 수치로 확정된 상태다.")
H2("8.2 Stage B 스위칭 회로와 부품 설계")
P("DAB와 4상한 H-브리지의 실제 스위칭 결선을 구축하고 펄스폭변조, 데드타임, 전류 리플, 실효·피크전류, ZVS·ZCS, 프리차지, 과전류와 단락 차단을 검증한다. 2 mF 링크 커패시터와 5 µH 필터는 실제 부품을 선정해 손실, 온도, 질량, 체적, 수명과 공차를 평가한다. 완료 기준은 정격·과도·회생과 0 V 통과 조건에서 스위칭 리플을 포함한 경로·필터 전류 피크가 90 A 이하, 링크 80 A·8 kW와 변조율 0.95 이내이고, 소자 전압·온도가 선정 부품 정격 안에 있으며, 과전류·단락 시 정의된 안전상태로 전환되는 것이다.")
H2("8.3 공통 제어기의 강건성 확보")
P("재설계는 두 목표를 따로 다룬다. 첫째, 640 V 코너의 전류 여유를 확보한다. 전류지령 포화값을 목표 여유에서 다시 도출하고, 전류 루프 구조와 필요하면 링크·필터 파라미터를 조정한다. 둘째, 감쇠·지연 여유를 확보한다. 지연 예산은 목표 디지털 구현(ADC 변환, 센서 필터, 연산, PWM·DAB 위상 갱신, 게이트 구동)에서 먼저 산정하고, 그 값에 여유를 더해 설계한다. 복합 공차, 센서 오차와 잡음, 온도 변화, 배터리 전압의 동적 변화와 부하 램프를 결합해 시험한다. 완료 기준은 사전에 정의한 복합 공차·지연 집합에서 경로·필터 전류 90 A 이하와 표 2의 전압 기준을 만족하고, 공칭 대비 +2.5 µs 추가 지연에서도 통과하는 것이다.")
H2("8.4 충전과 보조전원의 통합 검증")
P("통합은 Simulink에서 두 수준으로 진행한다. 먼저 Stage A 평균모델(2:1 고정비와 등가저항), Stage B 6상태 모델, 충전기 모델(전압·전류·전력 한계와 CC/CV), 400 V 부하와 Stage C 평균모델을 연결해 모드 전환과 동시 운전을 시험한다. 다음으로 Stage B를 Simscape 스위칭 모델로 교체하고, Stage A는 스위칭 ODE 결과와 대조할 수 있는 Simscape 위상 모델을 추가한다. 충전기 접속·해제, 150 kW 전력상한, 375 A 전류상한, 모듈 투입, 보조버스 조정, 회생 전환, 적분기 초기화와 무충격 전환을 포함한다. 완료 기준은 150 kW(또는 375 A 제한) 충전과 25 kW 보조부하 동시 운전에서 보조버스 400±8 V와 포트 정격을 만족하고, 모드 전환 중 경로전류가 100 A 이하인 것이다.")
H2("8.5 Stage C 5 kW 재설계")
P("48 V 3 kW와 12 V 1.5 kW 동시부하를 충족하도록 공진탱크와 변압기를 재설계한다. 정류 손실, 자화전류, ZVS, 경부하 운전, 열설계와 48 V 회생 전류 폐루프를 검증한다. 완료 기준은 8.1절에서 확정한 입력전압 범위, 48 V와 12 V 동시 최대부하 및 회생 조건에서 48 V 출력 편차 ±2 % 이내이고 소자 정격과 온도 요구를 만족하는 것이다.")
H2("8.6 SALS의 인과적 구현과 서비스 평가")
P("(1) 부하 등급과 등급별 최대 지연을 반영하고, 부하 측 ECU가 승인 후 기동하는 절차를 구현한다. (2) 정적 예산을 6.6절의 과도 허용 전력 지도처럼 배터리 전압과 현재 부하에 따른 동적 여유로 확장하되, 공차·지연 여유를 차감한 보수 값을 쓴다. (3) 인과성 문제만 분리한 반례를 다시 구성한다. (4) 부하 관리 없음, 반응형 제한, 단일 시점 우선순위 승인, 창 기반 승인, 동적 여유 기반 승인과 하드웨어 정격 증대안을 같은 전기모델과 같은 서비스 조건에서 비교한다. 완료 기준은 표 15의 H4 기준과 함께 난방, 제상, 배터리 예열의 미공급 수요가 허용범위 안에 있는 것이다.")
H2("8.7 기준 구조 비교, 신규성 검증과 하드웨어 실증")
P("동일한 반도체 기술, 절연, 냉각, 온도와 부하 프로파일에서 다음 네 구조를 비교한다. ① 전전력 승압기와 별도 보조전원모듈, ② 고정비 변환기와 별도 전전력 조정기, ③ PRISM-Hub 후보, ④ 비조정 고정비 V_A에 400 V 부하를 직접 연결하고 광입력 저전압 변환기를 쓰는 구조(2.5절의 산업계 구조)다. ④는 가장 단순한 경쟁 구조이므로, PRISM-Hub가 ④보다 이점을 보이지 못하면 보조버스 조정의 필요성(3.2절)과 Stage B의 가치는 성립하지 않는다.")
P("1차 비교는 평균모델과 손실 모델 수준에서 P0 과제로 먼저 수행하고, 같은 배터리 전압범위, 충전전력, 보조부하 프로파일과 서비스 요구에서 효율지도, 처리전력, 정격 VA, 부품 수를 평가한다. 예상 신규성은 표 15의 기준으로 채택하거나 기각하며, 특허 가능성은 기술 비교와 별도로 기능·구성요소·연결관계의 청구항 대조표로 판단한다. HIL, 축소전력 시제품, 목표 정격 시제품과 차량 운전 시나리오 시험은 이 단계의 결과로 가설이 유지될 때 후속 단계에서 수행한다.")
H2("8.8 남은 기간의 우선순위와 일정")
P("1차 보고 검토 결과에 따라 요구사항·수락 기준 확정을 첫 과제로 추가하고, 기준 구조 비교를 앞당겨 P0로 올렸다(표 16).")
TB("표 16. 남은 기간의 우선순위와 일정", [2.6, 1.0, 4.4, 3.4],
   ["기간", "우선순위", "주요 작업", "완료 판단"],
   [["9월 26일–10월 9일", "P0", "요구사항·부하 등급·수락 기준 확정, 전류·지연 여유 목표의 제어기 재설계", "표 2·5·15 확정, 전류 여유와 지연 예산 제시"],
    ["10월 10일–30일", "P0", "Stage B Simscape 스위칭·보호·프리차지 모델", "스위칭 리플 포함 포트 정격 통과"],
    ["10월 31일–11월 20일", "P0", "충전기–Stage A–B 통합과 모드 전환, Stage A Simscape 위상 모델", "충전·보조부하 동시 운전 재현(H3)"],
    ["11월 21일–12월 4일", "P0", "기준 구조 ①·④ 대비 1차 비교(평균모델·손실 모델)", "동일 경계의 정량 비교표(H5 1차 판정)"],
    ["12월 5일–18일", "P1", "Stage C 5 kW 재설계", "48 V·12 V 동시 최대부하 통과"],
    ["12월 19일–1월 1일", "P1", "SALS 동적 여유 기반 승인과 서비스 품질 평가", "H4 기준 판정"],
    ["1월 2일–8일", "P0", "재현성 점검과 최종 보고서", "결과·코드·근거 파일 상호 일치"]],
   "자료: 저자 작성.", fs=16)
P("P0는 다음 단계 진행에 필요한 필수 과제이며, P1은 시스템 성능의 완결에 필요한 과제다. HIL과 시제품 제작은 부품·장비 확보 일정에 따라 18주 계획 이후의 후속 실증으로 이어진다.")

# ---------------------------------------------------------------- 9
H1("9. 결론")
P("PRISM-Hub는 고정비 대전력 경로와 부분전력 직렬 조정을 결합해 800 V 차량의 충전 호환과 다중 전압 보조전원을 하나의 직류 전력 구조로 다루는 아키텍처다. 개별 원리에는 선행연구와 특허가 있으므로, 프로젝트의 가치는 이 원리들을 차량 운전조건에 배치하고 포트 정격과 실패 경계를 재현 가능한 체계에서 정량화하는 데 있다.")
P("세 연구 질문에 대한 현재의 답은 다음과 같다. Q1(정격 분리)은 평균모델 수준에서 부분적으로 긍정적이다. 25 kW 보조버스에서 Stage B 처리전력은 최대 6.44 kW(25.7 %)였고 충전전류는 조정단을 지나지 않지만, 충전 중 동시 운전은 검증되지 않았다. Q2(강건 제어와 부하 승인)는 공칭 조건에서만 성립한다. 고정 제어기는 공칭 지연에서 정상·단일 공차 시험을 통과했으나 640 V 코너의 전류 여유가 약 2 A, 지연 여유가 1.5–2.5 µs에 그친다. 부하 승인은 정적 예산 단계이며, 현재 스트레스 부하 정의에서는 비지연 부하만으로 예산을 넘는다. Q3(기준 구조 대비 이점)은 아직 평가하지 않았고, 특히 조정 없는 고정비 버스 구조와의 비교가 보조버스 조정의 필요성을 결정한다.")
P("따라서 다음 단계는 요구사항과 수락 기준을 먼저 확정하고, 전류·지연 여유를 확보한 제어기, 스위칭 수준의 Stage B, 충전·보조전원 통합과 기준 구조 비교를 거쳐 예상 신규성을 검증된 기여로 전환하거나 기각하는 것이다.")

# ---------------------------------------------------------------- appendices
PB()
H1("부록 A. 주요 약어 및 용어")
TB("표 A-1. 주요 약어 및 용어", [2.0, 9.4], ["약어", "뜻"],
   [["APM", "Auxiliary Power Module. 고전압 배터리에서 48 V 또는 12 V 전원을 공급하는 보조전원모듈"],
    ["ARL", "Anticipatory Regulation Layer. 초기 계획의 학습 기반 선행 조정 계층(폐기)"],
    ["BMS", "Battery Management System. 배터리 상태를 감시하고 충전 한계를 결정하는 관리 시스템"],
    ["CC/CV", "Constant Current / Constant Voltage. 정전류·정전압 충전 방식"],
    ["CLLC", "변압기 양쪽에 인덕터와 커패시터 공진망을 두는 양방향 절연 공진형 변환기"],
    ["DAB", "Dual-Active-Bridge. 변압기 양쪽의 능동 브리지를 이용하는 절연형 양방향 직류-직류 변환기"],
    ["ECU", "Electronic Control Unit. 차량 부하 또는 기능을 제어하고 상태를 통신하는 전자제어기"],
    ["EMI", "Electromagnetic Interference. 전자기 간섭"],
    ["HIL", "Hardware-in-the-Loop. 실제 제어기와 실시간 시뮬레이터를 연결하는 검증 방식"],
    ["LC", "Inductor-Capacitor. 인덕터와 커패시터로 구성한 필터 또는 공진망"],
    ["ODE", "Ordinary Differential Equation. 시간에 따른 회로 상태를 표현하는 상미분방정식"],
    ["PPP", "Partial Power Processing. 전체 전력 중 조정에 필요한 일부만 변환하는 부분전력처리 원리"],
    ["PPRC", "Partial-Power Regulating Converter. 직렬 보상전압을 만들어 버스전압을 조정하는 부분전력 조정 변환기"],
    ["PTC", "Positive Temperature Coefficient. 온도가 오르면 저항이 증가하는 정온도계수 특성 또는 이를 이용한 히터"],
    ["PWM", "Pulse-Width Modulation. 스위치의 켜짐 시간을 조절해 평균전압을 제어하는 펄스폭변조"],
    ["RSC", "Resonant Switched-Capacitor Converter. 공진전류와 스위치드 커패시터를 이용하는 고정비 변환기"],
    ["SALS", "Saturation-Aware Anticipatory Load Shaping. 조정단의 정격을 고려해 지연 가능한 부하를 승인·제한하는 상위 계층"],
    ["SPS", "Single-Phase Shift. DAB 양쪽 브리지의 위상차로 전력을 조절하는 단일 위상천이 방식"],
    ["STC", "Switched-Tank Converter. 공진 탱크와 커패시터 연결을 이용하는 고정비 변환기 계열의 명칭"],
    ["V_A", "Stage A의 2:1 고정비 출력과 400 V급 충전기가 접속하는 내부 직류 노드"],
    ["WP", "Work Package. 작업패키지"],
    ["ZCS / ZVS", "Zero-Current / Zero-Voltage Switching. 스위치 전환 시 전류 또는 전압을 0에 가깝게 만드는 소프트 스위칭"]],
   "", fs=16)
H1("부록 B. 참고문헌")
REFS = [
 "I. Aghabali, J. Bauman, P. J. Kollmeyer, Y. Wang, B. Bilgin, A. Emadi, “800-V Electric Vehicle Powertrains: Review and Analysis of Benefits, Challenges, and Future Trends,” IEEE Transactions on Transportation Electrification, vol. 7, no. 3, pp. 927–948, 2021. DOI: 10.1109/TTE.2020.3044938.",
 "B. Zhao, Q. Song, W. Liu, Y. Sun, “Overview of Dual-Active-Bridge Isolated Bidirectional DC–DC Converter for High-Frequency-Link Power-Conversion System,” IEEE Transactions on Power Electronics, vol. 29, no. 8, pp. 4091–4106, 2014. DOI: 10.1109/TPEL.2013.2289913.",
 "Z. Ni, Y. Li, C. Liu, M. Wei, D. Cao, “A 100-kW SiC Switched Tank Converter for Transportation Electrification,” IEEE Transactions on Power Electronics, vol. 35, no. 6, pp. 5770–5784, 2020. DOI: 10.1109/TPEL.2019.2954801.",
 "X. Liu, M. Wei, M. Qiu, K. Hobbs, A. Dahneem, D. Cao, “500 kW 3-Phase Interleaved SiC Switched Tank Converter for Transportation Electrification,” IEEE APEC, pp. 1017–1023, 2023. DOI: 10.1109/APEC43580.2023.10131540.",
 "X. Liu, M. Qiu, K. Hobbs, A. Dahneem, H. Meng, D. Cao, “Experimental Verification of 500kW Resonant Switched-Capacitor Converter for Electric Trucks and Electric Aircraft Application,” IEEE APEC, pp. 830–837, 2024. DOI: 10.1109/APEC48139.2024.10509275.",
 "Y. He, S. Jiang, C. Nan, “Switched Tank Converter Based Partial Power Architecture for Voltage Regulation Applications,” IEEE APEC, pp. 91–97, 2018. DOI: 10.1109/APEC.2018.8340993.",
 "Z. Ni, Y. Li, J. Johnson, M. Wei, C. Liu, X. Lyu, D. Cao, “A GaN Switched Tank Converter with Partial Power Voltage Regulation for Electric Vehicle Applications,” IEEE APEC, pp. 1682–1689, 2019. DOI: 10.1109/APEC.2019.8722301.",
 "P. Wang, M. Chen, “Analysis and Design of Series Voltage Compensator for Differential Power Processing,” IEEE Journal of Emerging and Selected Topics in Power Electronics, vol. 10, no. 6, pp. 7890–7903, 2022. DOI: 10.1109/JESTPE.2021.3116091.",
 "N. Hassanpour, A. Chub, A. Blinov, D. Vinnikov, “Soft-Switching Bidirectional Step-Up/Down Partial Power Converter With Reduced Components Stress,” IEEE Transactions on Power Electronics, vol. 38, no. 11, pp. 14166–14177, 2023. DOI: 10.1109/TPEL.2023.3289061.",
 "Y. Li, X. Lyu, Z. Ni, D. Cao, C. Nan, S. Jiang, “Adaptive On-Time Control for High Efficiency Switched-Tank Converter,” IEEE WiPDA Asia, pp. 169–175, 2018. DOI: 10.1109/WiPDAAsia.2018.8734623.",
 "H. Chen, H. Kim, R. W. Erickson, D. Maksimović, “Electrified Automotive Powertrain Architecture Using Composite DC–DC Converters,” IEEE Transactions on Power Electronics, vol. 32, no. 1, pp. 98–116, 2017. DOI: 10.1109/TPEL.2016.2533347.",
 "Vicor Corp., “Case study: Powering 400V accessory loads” (NBM9280, 2024), https://automotive.vicorpower.com/en_US/resources/case-study-powering-400v-accessory-loads; M. Jenks, “Adapting 400V and 800V architectures – bidirectional conversion,” SAE WCX 2023 presentation, https://www.vicorpower.com/press-room/wcx-2023-event (accessed 2026-09-24). 제조사 공개자료.",
 "Preh GmbH, “Combo Box – Highly Integrated Power Electronics,” manufacturer product information, https://www.preh.com/en/products/e-mobility/combo-box/en (accessed 2026-09-24). 제조사 공개자료.",
 "NIO USA Inc. (original assignee; inventors M. Shen and F. Guo), “Systems and Methods for Regulating Charging of Electric Vehicles,” US10363828B1, 2019; US10632863B2, 2020.",
 "Karma Automotive LLC (original assignee), “Combined Converter Circuit,” US11235676B2, 2022; WO2020257534A1; EP3987646A1/A4.",
 "Jaguar Land Rover Ltd., “Electrical Load Management Method and Apparatus,” US20190023203A1, 2019; US10829067B2, 2020.",
 "Robert Bosch GmbH, “Method and Device for Controlling Electric Consumers in a Motor Vehicle,” EP1053129A1, 2000.",
 "I. Kolmanovsky, E. Garone, S. Di Cairano, “Reference and Command Governors: A Tutorial on Their Theory and Automotive Applications,” American Control Conference, pp. 226–241, 2014. DOI: 10.1109/ACC.2014.6859176.",
]
B.append({"t": "refs", "items": REFS})
H1("부록 C. 검증 근거 파일")
TB("표 C-1. 검증 근거 파일", [5.0, 4.6, 1.8], ["파일·폴더", "내용", "기준"],
   [["docs/10_검토대응_통합개발.md", "유한 링크 2단 PPRC 모델, SALS 인과성 검토, 선행기술 정정", "v1.0-interim"],
    ["docs/11_공통제어기_60A_검증.md", "공통 고정이득 제어기, 60 A 상당 부하, 공차와 지연 시험", "v1.0-interim"],
    ["validation/2026-09-22-integration/", "2단 평균모델, 에너지 수지, 정상상태, SALS 계약, Python/MATLAB 대조", "v1.0-interim"],
    ["validation/2026-09-22-fixed-control/", "80개 시험조건, 공차·민감도, Python/MATLAB 대조, delay_sweep.json", "v1.0-interim"],
    ["validation/2026-09-22/", "Simulink 4상태 평균모델(prism_pprc_average_tb.slx), Stage A 실행 결과", "v1.0-interim"],
    ["docs/reviews/2026-09-21/", "독립 엔지니어링 검토, 분야별 재현자료와 선행기술 분석", "v1.0-interim"],
    ["python/report_final_analysis.py, validation/2026-09-25-final-report/", "정상상태 스윕, 640 V 코너 여유, 과도 허용 전력(Python)", "본 보고서 추가"],
    ["python/report_figures.py, docs/fig/report/", "본 보고서 그림 1–8 생성 스크립트와 그림 파일", "본 보고서 추가"]],
   "자료: 저자 작성. “본 보고서 추가” 항목은 이 보고서와 함께 저장소에 반영한다.", fs=16)
P("재현 절차(저장소 루트에서 실행):")
for x in ["python python/validate_fixed_control.py — 공통 고정이득 제어기 80개 시험조건",
          "python python/validate_sals_contract.py — SALS 반례와 정적 승인 조건",
          "python python/report_final_analysis.py — 본 보고서 추가 분석(정상상태 스윕, 코너 여유, 과도 허용 전력)",
          "python python/report_figures.py — 본 보고서 그림 1–8",
          "MATLAB: matlab/validate_fixed_control.m, validate_two_stage.m — Python 결과와의 교차검증"]:
    B.append({"t": "b", "x": x, "lvl": 0, "left": True})
