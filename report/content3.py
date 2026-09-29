from content2 import B, H1, H2, P, BL, TB, FG, PB

# ---------------------------------------------------------------- 7
H1("7. 현재까지의 성과, 한계 및 기술 성숙도")
H2("7.1 현재까지 확보한 성과")
for x in ["Stage B의 DAB 입력전력, 유한 링크 저장에너지와 방향별 효율을 반영한 에너지 보존 평균모델과 포트별 정격 판정 체계를 구축했다.",
          "25 kW 보조버스에서 Stage B 처리전력이 최대 6.44 kW(25.7 %)이고 충전전류가 조정단을 지나지 않음을 평균모델에서 확인했다(가설 H1의 부분 근거).",
          "하나의 고정 제어이득으로 공칭 지연 조건의 정상시험 41건(회생·0 V 통과 포함)과 단일 변수 공차시험 28건을 통과했고, 640 V 코너 여유·지연 실패 양상·전압별 과도 허용 전력을 정량화해 재설계 목표를 정했다.",
          "Stage A 스위칭 ODE 모델에서 위상별 자기발진 영교차 추종으로 정·역방향 공차 표본의 ZCS를 확보했다.",
          "실패 조건(과부하, 제어 여유 제거, 추가 지연, SALS 관측 전 사건)을 회귀시험으로 보존하고, Python·MATLAB 별도 구현으로 판정 재현성을 확인했다.",
          "부하 입력범위와 전압 등급 규격으로 보조버스 조정 요구를 파생 요구로 재분류하고, 부하 등급 계약, 전력예산, Tier-1·Tier-2 과도 기준, 보장 최소 배터리 전압(640 V)과 지연 예산(+3.0 µs)을 확정했다(3장).",
          "고속 상태 1주기 예측과 주 극점 감쇠 재배치로 재설계 제어기 R1을 도출해, 확정 기준의 Tier-1·Tier-2 시험과 +3.0 µs 추가 지연을 평균모델에서 충족했다(6.10절).",
          "SALS를 예약·핸드셰이크·워치독·인과적 최악값 경계의 승인 프로토콜로 재구성하고, 계약 내 200회 시험에서 예산 초과 0건과 지연 가능 부하 서비스 개선을 확인했다(6.11절)."]:
    BL(x)
H2("7.2 남은 한계와 위험")
for x in ["요구사항: 부하 계약 값은 설계 할당이므로 실제 부품(컴프레서 인버터의 기동 특성, V2L 변환기, Stage C)의 사양으로 확인해야 한다. 충전 요구와 Stage C 입력은 잠정이며, 400±8 V의 가치는 기준 구조 비교(H5) 전까지 판정되지 않는다.",
          "제어: R1은 평균모델에서 확정 기준을 충족했으나 MATLAB 교차검증 전이다. 예측은 공칭 모델을 쓰므로 PWM 리플, 센서 잡음과 양자화가 예측 오차로 나타날 수 있고, 온도와 배터리 전압의 운전 중 변화는 아직 적용하지 않았다.",
          "모델 수준: 평균 H-브리지와 DAB 모델에는 PWM, 데드타임, 스위칭 리플, 소자 기생성분, 게이트 구동, 영전압 스위칭(Zero-Voltage Switching, ZVS), 고장 차단과 프리차지가 포함되지 않았다. 고정 96 % DAB 효율은 정밀 손실지도가 아니며, 2 mF 링크 커패시터와 5 µH 필터는 잠정 모델값이다.",
          "통합: 충전기, Stage A, Stage B, 400 V 보조부하와 Stage C를 하나의 모델에서 연결한 모드 전환시험이 없다. 충전기 접속·해제, 적분기 초기화, 무충격 전환(bumpless transfer), 회생 중 고장과 보조전원 유지가 미검증이다.",
          "SALS: 계약 기반 승인은 1 ms 축약 부하 모델에서 검증했으며 전기모델과 결합하지 않았다. 예산은 배터리 전압과 무관한 정적 값이고, 난방·제상·예열의 서비스 허용치(열 모델)가 정의되지 않았다. 계약을 위반하는 부하는 승인으로 막을 수 없다.",
          "비교: 효율, 부피, 질량과 비용의 비교가 동일 조건의 기준 구조와 수행되지 않았다. 자기소자 정격의 감소를 제품 부피나 원가 감소로 직접 환산할 수 없으며, RSC의 커패시터, 공진 인덕터, 버스바, 구동기, 센서, 냉각과 전자기 간섭 대책을 모두 포함해야 한다."]:
    BL(x)
H2("7.3 현재 기술성숙도 판정")
P("현재 PRISM-Hub는 재현 가능한 평균모델, 스위칭 ODE 모델과 실패 회귀시험을 갖춘 시뮬레이션 기반 연구 개발 단계다. 전력수지와 Stage B 후보 제어기의 공칭 조건 운전 가능성은 확인됐으나, 스위칭 회로, 열, 보호, 전체 모드 통합, 시제품과 차량 검증은 후속 단계로 남아 있다.")
P("현재 증거가 지지하는 결론은 “확정한 요구사항과 수락 기준에서 Stage B 2단 후보와 재설계 제어기 R1의 평균모델상 운전 가능성과 전류·지연 여유를 확인했다”는 것이다. 전체 아키텍처, 전 운전영역 강건성, 실측 효율, 기준 구조 대비 부피·비용 및 모든 통신 지연에 대한 안전성은 후속 검증 항목이다.")
H2("7.4 최초 계획 대비 진척")
P("보고일은 18주 계획의 4주차 중간이다. 작업패키지(Work Package, WP)별 상태는 표 {t:14}와 같다.")
TB("표 {t:14}. 최초 계획 대비 작업패키지별 진척", [3.4, 1.6, 6.4],
   ["작업패키지(최초 계획)", "현재 상태", "주요 결과와 남은 작업"],
   [["WP1 요구사항·구조·파라미터 확정", "완료(9월 28일)", "V_A 접속, 바이패스 폐지, 포트별 정격 재정의, 요구사항·부하 등급·수락 기준 확정(docs/14). 충전·Stage C 입력은 잠정"],
    ["WP2 평균모델·제어·상태기계", "진행 중", "Stage B 6상태 모델과 재설계 제어기 R1(평균모델 기준 충족) 완료. MATLAB 교차검증, 통합 상태기계 미완료"],
    ["WP3 Simscape 스위칭 모델", "미착수", "선행으로 Stage A 스위칭 ODE 완료. Stage A·B·C Simscape 미착수"],
    ["WP4 시나리오·기준 구조 검증", "진행 중", "Stage B 동특성과 경계, 과도 허용 전력 확보. 기준 구조 비교 미착수"],
    ["WP4.5 선행 조정·부하 관리", "범위 변경", "학습 기반 예측 피드포워드(ARL) 폐기, 계약 기반 인과적 부하 승인(SALS) 프로토콜과 축약 모델 시험 완료"],
    ["WP5 손실·열·전력밀도", "예비 착수", "Stage A 예비 손실값만 확보"],
    ["WP6 문서화·재현자료", "진행 중", "실행 근거, 실패 회귀시험, 본 보고서"]],
   "자료: 저자 작성. 최초 계획은 저장소 docs/01 제안서 4.3절의 18주 일정이다.")
P("현재까지의 핵심 진전은 구성요소 모델의 수를 늘린 데 있지 않고, 기존 모델의 전력수지 오류와 인과성 문제를 찾아 설계경계를 수정한 데 있다. 1차 보고 후 요구사항 확정과 제어기 재설계를 마쳤으므로, 다음 우선순위는 R1 교차검증, WP3의 스위칭 모델과 WP4의 통합·기준 구조 비교다.")

# ---------------------------------------------------------------- 8
H1("8. 향후 연구 계획")
H2("8.1 요구사항, 부하 등급과 수락 기준 확정(완료)")
P("1차 보고에서 첫 과제로 정한 네 항목(보조버스 조정 요구의 근거, 부하 등급과 단시간 정격, 보장 최소 배터리 전압, 가설별 수락 기준)을 9월 28일 확정했다(3장, docs/14). 단시간 과부하 정격은 두지 않고 비지연 부하의 서지를 계약으로 제한했다. 확정한 수락 기준과 현재 상태는 표 {t:15}와 같으며, 이후 설계와 비교는 이 기준으로 판정한다.")
TB("표 {t:15}. 가설별 수락 기준(확정)과 현재 상태", [2.0, 2.8, 3.6, 3.0],
   ["가설(질문)", "판정 지표", "수락 기준", "현재 상태(9월 29일)"],
   [["H1 정격 분리(Q1)", "640–920 V·25 kW에서 Stage B 링크전력, 충전전류 경로", "링크 ≤ 8 kW(정상·Tier-1·Tier-2, 공차 포함), 충전전류 Stage B 비경유", "부분 충족: R1에서 정상 6.44 kW, 과도 최대 7.22 kW. 충전 중 동시 운전 미검증"],
    ["H2 강건 제어(Q2)", "Tier-1·Tier-2, 파라미터 ±10 % 공차, 지연 예산", "Tier-1: 전압 품질 + 경로·필터 ≤ 90 A. Tier-2: 물리정격 + ≤ 93.75 A + 384–416 V. 공차 집합과 추가 지연 +3.0 µs에서 Tier-1 유지", "충족(평균모델, R1): Tier-1 460/460(최대 87.6 A), Tier-2 78/78(최대 92.7 A), 선형화 지연 여유 ≥ 4.1 µs(24개 운전점). 기존 제어기는 미충족"],
    ["H3 충전 중 보조버스(Q1)", "150 kW(375 A 제한) 충전 + 25 kW 보조부하, 충전기 접속·해제", "동시 운전에서 Tier-1, 모드 전환에서 Tier-2", "미검증"],
    ["H4 부하 승인(Q2)", "표 {t:5} 계약, 메시지 지연 1–5 ms, 손실 0–20 %", "예산 초과 0. M1 승인 지연 ≤ 25 ms(손실 없음), 99 % ≤ 50 ms(손실 시). D 첫 허용 ≤ 200 ms. D 미공급이 정적 예약보다 작을 것", "충족(축약 모델): 초과 0, 승인 지연 최대 17 ms, 손실 시 99 % 25.4 ms, D 미공급 7.0 %(정적 예약 35.2 %)"],
    ["H5 기준 구조 대비 이점(Q3)", "기준 구조 ①·④와 변형 ③′ 대비 동일 경계 비교", "손실·정격 VA·반도체 수 중 2개 이상에서 ④와 ③′보다 우수, 서비스(버스 창, 48 V 품질, 부품 전압 등급) 동등 이상", "미평가"]],
   "자료: docs/14 표 R-6, validation/2026-09-28-requirements/, validation/2026-09-29-controller/를 바탕으로 저자 작성. 현재 상태는 평균모델과 1 ms 축약 부하 모델의 판정이다.", fs=16)
H2("8.2 Stage B 스위칭 회로와 부품 설계")
P("DAB와 4상한 H-브리지의 실제 스위칭 결선을 구축하고 펄스폭변조, 데드타임, 전류 리플, 실효·피크전류, ZVS·ZCS, 프리차지, 과전류와 단락 차단을 검증한다. 2 mF 링크 커패시터와 5 µH 필터는 실제 부품을 선정해 손실, 온도, 질량, 체적, 수명과 공차를 평가한다. 완료 기준은 정격·과도·회생과 0 V 통과 조건에서 스위칭 리플을 포함한 경로·필터 전류 순시 피크가 Tier-1 98 A, Tier-2 100 A 이하, 링크 80 A·8 kW와 변조율 0.95 이내이고, 소자 전압·온도가 선정 부품 정격 안에 있으며, 과전류·단락 시 정의된 안전상태로 전환되는 것이다.")
H2("8.3 제어기 R1의 구현 수준 검증")
P("R1은 평균모델에서 확정 기준을 충족했다(6.10절). 남은 검증은 네 가지다. (1) MATLAB 독립 구현과의 교차검증, (2) Stage B 스위칭 모델에서 PWM 리플, 데드타임과 양자화가 예측 오차와 감쇠에 주는 영향, (3) 센서 오차·잡음, 온도와 배터리 전압의 운전 중 변화를 결합한 시험, (4) 과전류 보호와의 상호작용, (5) 기준 외 복합 공차 코너의 Tier-2 초과(최대 95.8 A)와 지연·저전압 중첩 사례를 해결하는 경로전류 제한 기능이다. 전압 비례항의 포화는 불안정 영역이 있으므로 쓰지 않는다(6.10절). 완료 기준은 스위칭 모델에서 리플을 포함한 경로·필터 전류가 Tier-1 98 A, Tier-2 100 A 이하이고 표 {t:2}의 전압 기준을 추가 지연 +3.0 µs에서 만족하는 것이다.")
H2("8.4 충전과 보조전원의 통합 검증")
P("통합은 Simulink에서 두 수준으로 진행한다. 먼저 Stage A 평균모델(2:1 고정비와 등가저항), Stage B 6상태 모델, 충전기 모델(전압·전류·전력 한계와 CC/CV), 400 V 부하와 Stage C 평균모델을 연결해 모드 전환과 동시 운전을 시험한다. 다음으로 Stage B를 Simscape 스위칭 모델로 교체하고, Stage A는 스위칭 ODE 결과와 대조할 수 있는 Simscape 위상 모델을 추가한다. 충전기 접속·해제, 150 kW 전력상한, 375 A 전류상한, 모듈 투입, 보조버스 조정, 회생 전환, 적분기 초기화와 무충격 전환을 포함한다. 완료 기준은 150 kW(또는 375 A 제한) 충전과 25 kW 보조부하 동시 운전에서 보조버스 400±8 V와 포트 정격을 만족하고, 모드 전환 중 경로전류가 100 A 이하인 것이다.")
H2("8.5 Stage C 5 kW 재설계")
P("48 V 3 kW와 12 V 1.5 kW 동시부하를 충족하도록 공진탱크와 변압기를 재설계한다. 정류 손실, 자화전류, ZVS, 경부하 운전, 열설계와 48 V 회생 전류 폐루프를 검증한다. 완료 기준은 보조버스 Tier-2 창(384–416 V)을 포함해 이 재설계에서 확정할 입력전압 범위, 48 V와 12 V 동시 최대부하 및 회생 조건에서 48 V 출력 편차 ±2 % 이내이고 소자 정격과 온도 요구를 만족하는 것이다.")
H2("8.6 SALS의 인과적 구현과 서비스 평가")
P("부하 등급 계약과 사전 승인 프로토콜은 축약 모델에서 구현했다(6.11절). 남은 과제는 다음과 같다. (1) 정적 예산을 6.6절의 과도 허용 전력 지도처럼 배터리 전압과 현재 부하에 따른 동적 여유로 확장하되, 공차·지연 여유를 차감한 보수 값을 쓴다. (2) 측정 합계가 최악값 경계를 넘으면 계약 위반으로 판단해 지연 가능 부하를 차단하는 감시 기능을 추가한다. (3) 부하 관리 없음, 반응형 제한, 정적 예약, 계약 기반 승인과 하드웨어 정격 증대안을 전기모델과 결합해 같은 서비스 조건에서 비교한다. 완료 기준은 표 {t:15}의 H4 기준과 함께 난방, 제상, 배터리 예열의 미공급 수요가 열 모델로 정한 허용범위 안에 있는 것이다.")
H2("8.7 기준 구조 비교, 신규성 검증과 하드웨어 실증")
P("동일한 반도체 기술, 절연, 냉각, 온도와 부하 프로파일에서 다음 다섯 구조를 비교한다. ① 전전력 승압기와 별도 보조전원모듈, ② 고정비 변환기와 별도 전전력 조정기, ③ PRISM-Hub 후보(400 V 고정 조정), ③′ 보조버스를 410 V 이하로만 제한하는 창 조정 변형(3.2절), ④ 비조정 고정비 V_A에 400 V 부하를 직접 연결하고 광입력 저전압 변환기를 쓰는 구조(2.5절의 산업계 구조)다. ③′와 ④는 400 V 부하에 B_470급 부품이나 넓은 입력범위를, Stage C에 입력 조정을 요구하므로 부품 전압 등급과 48 V 품질도 비교 항목에 넣는다. ④는 가장 단순한 경쟁 구조이므로, PRISM-Hub가 ④보다 이점을 보이지 못하면 보조버스 조정의 필요성(3.2절)과 Stage B의 가치는 성립하지 않는다.")
P("1차 비교는 평균모델과 손실 모델 수준에서 P0 과제로 먼저 수행하고, 같은 배터리 전압범위, 충전전력, 보조부하 프로파일과 서비스 요구에서 효율지도, 처리전력, 정격 VA, 부품 수와 부품 전압 등급을 평가한다. 예상 신규성은 표 {t:15}의 기준으로 채택하거나 기각하며, 특허 가능성은 기술 비교와 별도로 기능·구성요소·연결관계의 청구항 대조표로 판단한다. HIL, 축소전력 시제품, 목표 정격 시제품과 차량 운전 시나리오 시험은 이 단계의 결과로 가설이 유지될 때 후속 단계에서 수행한다.")
H2("8.8 남은 기간의 우선순위와 일정")
P("1차 보고 검토 결과에 따라 요구사항·수락 기준 확정을 첫 과제로 추가하고, 기준 구조 비교를 앞당겨 P0로 올렸다. 첫 과제와 제어기 재설계는 9월 29일에 마쳤으며, 이후 일정은 표 {t:16}과 같다.")
TB("표 {t:16}. 남은 기간의 우선순위와 일정", [2.6, 1.0, 4.4, 3.4],
   ["기간", "우선순위", "주요 작업", "완료 판단"],
   [["9월 26일–29일", "P0", "요구사항·부하 등급·수락 기준 확정, 제어기 재설계", "완료: 표 {t:2}·{t:5}·{t:15} 확정, R1 평균모델 기준 충족"],
    ["9월 30일–10월 9일", "P0", "R1 MATLAB 교차검증, 기준 구조 ③′·④ 평균모델 구축", "Python·MATLAB 판정 일치, 비교 모델 준비"],
    ["10월 10일–30일", "P0", "Stage B Simscape 스위칭·보호·프리차지 모델과 R1 이식", "리플 포함 Tier-1 98 A·Tier-2 100 A 통과"],
    ["10월 31일–11월 20일", "P0", "충전기–Stage A–B 통합과 모드 전환, Stage A Simscape 위상 모델", "충전·보조부하 동시 운전 재현(H3)"],
    ["11월 21일–12월 4일", "P0", "기준 구조 ①·③′·④ 대비 1차 비교(평균모델·손실 모델)", "동일 경계의 정량 비교표(H5 1차 판정)"],
    ["12월 5일–18일", "P1", "Stage C 5 kW 재설계", "48 V·12 V 동시 최대부하 통과"],
    ["12월 19일–1월 1일", "P1", "SALS 전압 의존 예산, 계약 위반 감시, 전기모델 결합 서비스 평가", "H4 기준(전기모델) 판정"],
    ["1월 2일–8일", "P0", "재현성 점검과 최종 보고서", "결과·코드·근거 파일 상호 일치"]],
   "자료: 저자 작성.", fs=16)
P("P0는 다음 단계 진행에 필요한 필수 과제이며, P1은 시스템 성능의 완결에 필요한 과제다. HIL과 시제품 제작은 부품·장비 확보 일정에 따라 18주 계획 이후의 후속 실증으로 이어진다.")

# ---------------------------------------------------------------- 9
H1("9. 결론")
P("PRISM-Hub는 고정비 대전력 경로와 부분전력 직렬 조정을 결합해 800 V 차량의 충전 호환과 다중 전압 보조전원을 하나의 직류 전력 구조로 다루는 아키텍처다. 개별 원리에는 선행연구와 특허가 있으므로, 프로젝트의 가치는 이 원리들을 차량 운전조건에 배치하고 포트 정격과 실패 경계를 재현 가능한 체계에서 정량화하는 데 있다.")
P("세 연구 질문에 대한 현재의 답은 다음과 같다. Q1(정격 분리)은 평균모델 수준에서 부분적으로 긍정적이다. 25 kW 보조버스에서 Stage B 처리전력은 최대 6.44 kW(25.7 %)였고 충전전류는 조정단을 지나지 않지만, 충전 중 동시 운전은 검증되지 않았다. Q2(강건 제어와 부하 승인)는 평균모델 수준에서 긍정적이다. 확정한 기준에서 재설계 제어기 R1은 Tier-1·Tier-2 시험과 +3.0 µs 추가 지연을 충족했고, 계약 기반 SALS는 축약 모델에서 예산 초과 없이 지연 가능 부하의 서비스를 개선했다. 다만 스위칭 모델, MATLAB 교차검증과 전기모델에 결합한 승인 시험은 남아 있다. Q3(기준 구조 대비 이점)은 아직 평가하지 않았다. 요구사항 검토에서 400±8 V 조정이 외부 요구가 아닌 파생 요구로 확인되었으므로, 조정 없는 구조(④)와 창 조정 변형(③′)과의 비교가 Stage B의 가치를 결정한다.")
P("따라서 다음 단계는 R1의 교차검증과 스위칭 수준 검증, 충전·보조전원 통합, 기준 구조 비교를 거쳐 예상 신규성을 검증된 기여로 전환하거나 기각하는 것이다.")

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
    ["PMSM", "Permanent Magnet Synchronous Motor. 영구자석 동기전동기. 차량용 전동 컴프레서의 구동 전동기"],
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
 "Sanden International, “Electric Compressors — Expanded Range,” manufacturer brochure, 2025, https://sanden.com/wp-content/uploads/2023/08/sanden-2025_Expanded_Range_Electric_Compressor_Brochure.pdf (accessed 2026-09-28). 제조사 공개자료.",
 "Webasto, “400 Volt High Voltage Heater HVH 50/70 Gen 1.5,” product specification, https://www.webasto.com/en-us/heating/high-voltage-heaters/400v-hvh.html (accessed 2026-09-28). 제조사 공개자료.",
 "BorgWarner, “Gen5 High Voltage DC/DC Converter — Product Manual,” Table 2 (accessed 2026-09-28). 제조사 공개자료.",
 "ISO 21498-1:2021, “Electrically propelled road vehicles — Electrical specifications and tests for voltage class B systems and components — Part 1: Voltage sub-classes and characteristics,” Table 1.",
 "ISO 21780:2020, “Road vehicles — Supply voltage of 48 V — Electrical requirements and tests,” Clause 5.",
 "Z. Wang, K. Lu, F. Blaabjerg, “A Simple Startup Strategy Based on Current Regulation for Back-EMF-Based Sensorless Control of PMSM,” IEEE Transactions on Power Electronics, vol. 27, no. 8, pp. 3817–3825, 2012. DOI: 10.1109/TPEL.2012.2186464.",
 "Texas Instruments, “AMC1301 Precision, ±250-mV Input, Reinforced Isolated Amplifier,” datasheet, Switching Characteristics. 제조사 공개자료.",
 "Texas Instruments, “UCC21710-Q1 Isolated Gate Driver,” datasheet, Switching Characteristics. 제조사 공개자료.",
 "Texas Instruments, “TMS320F2837xD Dual-Core Real-Time Microcontrollers,” datasheet, ADC section. 제조사 공개자료.",
 "S. Bibian, H. Jin, “Time Delay Compensation of Digital Control for DC Switchmode Power Supplies Using Prediction Techniques,” IEEE Transactions on Power Electronics, vol. 15, no. 5, pp. 835–842, 2000. DOI: 10.1109/63.867672.",
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
    ["docs/14_요구사항_부하등급_수락기준.md, validation/2026-09-28-requirements/", "요구사항·부하 등급·수락 기준, Tier-1·Tier-2 격자, 계약 시퀀스, SALS 계약 시험", "v1.2 추가"],
    ["python/ctrl_linear.py, ctrl_redesign.py, ctrl_validate.py, ctrl_explore.py, validation/2026-09-29-controller/", "표본화 선형화, 재설계 제어기 R1, 격자·지연·복합 공차·시퀀스 검증, 기각 대안 탐색", "v1.2 추가"],
    ["python/report_figures.py, docs/fig/report/", "본 보고서 그림 {f:1}–{f:ctrl} 생성 스크립트와 그림 파일", "본 보고서 추가"]],
   "자료: 저자 작성. “본 보고서 추가” 항목은 이 보고서와 함께 저장소에 반영한다.", fs=16)
P("재현 절차(저장소 루트에서 실행):")
for x in ["python python/validate_fixed_control.py — 공통 고정이득 제어기 80개 시험조건",
          "python python/validate_sals_contract.py — SALS 반례와 정적 승인 조건",
          "python python/report_final_analysis.py — 본 보고서 추가 분석(정상상태 스윕, 코너 여유, 과도 허용 전력)",
          "python python/req_static.py, req_dynamic.py, req_delay.py, req_sequence.py, sals_contract.py — 요구사항 확정 근거(v1.2)",
          "python python/ctrl_validate.py, ctrl_explore.py — 재설계 제어기 R1 검증과 기각 대안 탐색(v1.2)",
          "python python/report_figures.py — 본 보고서 그림 {f:1}–{f:ctrl}",
          "MATLAB: matlab/validate_fixed_control.m, validate_two_stage.m — Python 결과와의 교차검증"]:
    B.append({"t": "b", "x": x, "lvl": 0, "left": True})
