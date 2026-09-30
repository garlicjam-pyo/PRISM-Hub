from content2 import B, H1, H2, P, BL, TB, FG, PB

# ---------------------------------------------------------------- 7
H1("7. 한계와 기술 성숙도")
H2("7.1 현재 근거의 한계")
for x in ["모델 수준: Stage B 평균모델에는 PWM, 데드타임, 스위칭 리플, 소자 기생성분, 게이트 구동, 영전압 스위칭(Zero-Voltage Switching, ZVS), 고장 차단과 프리차지가 포함되지 않는다. DAB 효율은 방향별 96 % 고정값이며 정밀 손실지도가 아니고, 링크 커패시터 2 mF와 필터 5 µH는 잠정값이다.",
          "제어: 채택 제어기의 결과는 Python 평균모델에서 얻었으며 MATLAB 독립 구현과의 교차검증 전이다. 예측은 공칭 모델을 쓰므로 PWM 리플, 센서 잡음과 양자화가 예측 오차로 나타날 수 있고, 온도와 배터리 전압의 운전 중 변화는 아직 적용하지 않았다. 복합 공차 코너의 Tier-2 전류 여유가 부족하다(6.3절).",
          "통합: 충전기, Stage A, Stage B, 400 V 보조부하와 Stage C를 하나의 모델에서 연결한 모드 전환 시험이 없다. 충전기 접속·해제, 적분기 초기화, 무충격 전환(bumpless transfer), 회생 중 고장과 보조전원 유지가 검증되지 않았다.",
          "부하 승인: 1 ms 축약 부하 모델에서 검증했으며 전기모델과 결합하지 않았다. 예산은 배터리 전압과 무관한 정적 값이고, 난방·제상·예열의 서비스 허용치(열 모델)가 정의되지 않았다. 부하 계약 값은 설계 할당이므로 실제 부품 사양으로 확인해야 한다.",
          "비교: 효율, 부피, 질량과 비용을 동일 조건의 기준 구조와 비교하지 않았다. 자기소자 정격의 감소를 제품 부피나 원가 감소로 직접 환산할 수 없으며, 비교에는 RSC 커패시터, 공진 인덕터, 버스바, 구동기, 센서, 냉각과 전자기 간섭 대책을 모두 포함해야 한다."]:
    BL(x)
H2("7.2 기술 성숙도")
P("현재 PRISM-Hub는 재현 가능한 해석, 평균모델과 스위칭 ODE 모델을 갖춘 시뮬레이션 기반 설계 검증 단계다. 확정한 요구사항과 수락 기준에서 Stage A의 양방향 ZCS, Stage B의 정격 분리와 제어기의 전류·지연 여유, 부하 승인 계층의 예산 준수를 모델 수준에서 확인했다. 스위칭 회로, 열, 보호, 전체 모드 통합, 기준 구조 대비 이점과 시제품 검증은 후속 단계다.")

# ---------------------------------------------------------------- 8
H1("8. 향후 연구 계획")
H2("8.1 가설별 수락 기준")
P("후속 설계와 비교는 표 {t:accept}의 수락 기준으로 판정한다. 기준은 3장의 요구사항에서 도출했으며, 현재 상태는 평균모델과 1 ms 축약 부하 모델의 판정이다.")
TB("표 {t:accept}. 가설별 수락 기준과 현재 상태", [2.0, 2.8, 3.6, 3.0],
   ["가설(질문)", "판정 지표", "수락 기준", "현재 상태"],
   [["H1 정격 분리(Q1)", "640–920 V·25 kW에서 Stage B 링크전력, 충전전류 경로", "링크 ≤ 8 kW(정상·Tier-1·Tier-2, 공차 포함), 충전전류 Stage B 비경유", "부분 충족: 정상 6.44 kW, 과도 최대 7.22 kW. 충전 중 동시 운전 미검증"],
    ["H2 강건 제어(Q2)", "Tier-1·Tier-2, 파라미터 ±10 % 공차, 지연 예산", "Tier-1: 전압 품질 + 경로·필터 ≤ 90 A. Tier-2: 물리정격 + ≤ 93.75 A + 384–416 V. 공차 집합과 추가 지연 3.0 µs에서 Tier-1 유지", "충족(평균모델): Tier-1 460건, Tier-2 78건 통과, 추가 지연 여유 4.1 µs. 스위칭 모델 검증 전"],
    ["H3 충전 중 보조버스(Q1)", "150 kW(375 A 제한) 충전 + 25 kW 보조부하, 충전기 접속·해제", "동시 운전에서 Tier-1, 모드 전환에서 Tier-2", "미검증"],
    ["H4 부하 승인(Q2)", "표 {t:loads}의 계약, 메시지 지연 1–5 ms, 손실 0–20 %", "예산 초과 0. 컴프레서 승인 지연 ≤ 25 ms(손실 없음), 99 % ≤ 50 ms(손실 시). 지연 가능 부하 첫 허용 ≤ 200 ms. 미공급이 정적 예약보다 작을 것", "충족(축약 모델): 초과 0, 승인 지연 최대 17 ms, 손실 시 99 % 25.4 ms, 미공급 7.0 %(정적 예약 35.2 %)"],
    ["H5 기준 구조 대비 이점(Q3)", "기준 구조 ①·④와 변형 ③′ 대비 동일 경계 비교", "손실·정격 VA·반도체 수 중 2개 이상에서 ④와 ③′보다 우수, 서비스(버스 창, 48 V 품질, 부품 전압 등급) 동등 이상", "미평가"]],
   "자료: 저자 작성.", fs=16)
H2("8.2 Stage B 스위칭 회로와 제어기 구현 검증")
P("평균모델에서 확인한 전류·지연 여유가 실제 스위칭 회로에서도 성립하는지 확인해야 한다. DAB와 4상한 H-브리지의 스위칭 결선을 구축하고 펄스폭변조, 데드타임, 전류 리플, 실효·피크전류, ZVS·ZCS, 프리차지, 과전류와 단락 차단을 검증한다. 제어기는 같은 이득과 예측 구조를 이식하고, MATLAB 독립 구현으로 평균모델 결과를 교차검증한다. 복합 공차 코너의 Tier-2 전류 여유는 경로전류 제한 기능으로 보완하되, 전압 비례항의 포화는 불안정 영역이 있으므로 쓰지 않는다. 링크 커패시터와 필터는 실제 부품을 선정해 손실, 온도, 체적과 공차를 평가한다.")
P("완료 기준은 정격·과도·회생과 0 V 통과 조건에서 리플을 포함한 경로·필터 전류 순시 피크가 Tier-1 98 A, Tier-2 100 A 이하이고, 링크 80 A·8 kW와 변조율 0.95 이내이며, 표 {t:req}의 전압 기준을 추가 지연 3.0 µs에서 만족하고, 과전류·단락 시 정의된 안전상태로 전환되는 것이다.")
H2("8.3 충전과 보조전원의 통합 검증")
P("충전 중에도 보조버스가 유지되는지는 N1과 H3의 핵심 조건이다. 통합은 두 수준으로 진행한다. 먼저 Stage A 평균모델(2:1 고정비와 등가저항), Stage B 6상태 모델, 충전기 모델(전압·전류·전력 한계와 CC/CV), 400 V 부하와 Stage C 평균모델을 연결해 모드 전환과 동시 운전을 시험한다. 다음으로 Stage B를 스위칭 회로 모델로 교체하고 Stage A 위상 모델을 추가한다. 충전기 접속·해제, 150 kW 전력상한, 375 A 전류상한, 모듈 투입, 회생 전환, 적분기 초기화와 무충격 전환을 포함하며, 완료 기준은 150 kW(또는 375 A 제한) 충전과 25 kW 보조부하 동시 운전에서 Tier-1, 모드 전환 중 Tier-2를 만족하는 것이다.")
H2("8.4 Stage C 5 kW 재설계")
P("48 V 3 kW와 12 V 1.5 kW 동시부하를 충족하도록 공진탱크와 변압기를 재설계한다. 정류 손실, 자화전류, ZVS, 경부하 운전, 열설계와 48 V 회생 전류 폐루프를 검증한다. 완료 기준은 보조버스 Tier-2 창(384–416 V)을 포함한 입력전압 범위, 48 V와 12 V 동시 최대부하 및 회생 조건에서 48 V 출력 편차 ±2 % 이내이고 소자 정격과 온도 요구를 만족하는 것이다.")
H2("8.5 부하 승인 계층의 고도화")
P("부하 승인 계층을 실제 차량 조건에 맞추기 위해 세 가지를 보완한다. (1) 정적 예산을 배터리 전압과 현재 부하에 따른 동적 과도 여유로 확장하되, 공차·지연 여유를 차감한 보수 값을 쓴다. (2) 측정 합계가 최악값 경계를 넘으면 계약 위반으로 판단해 지연 가능 부하를 차단하는 감시 기능을 추가한다. (3) 전기모델과 결합해 부하 관리 없음, 반응형 제한, 정적 예약, 계약 기반 승인과 하드웨어 정격 증대안을 같은 서비스 조건에서 비교한다. 완료 기준은 표 {t:accept}의 H4 기준과 함께 난방, 제상, 배터리 예열의 미공급 수요가 열 모델로 정한 허용범위 안에 있는 것이다.")
H2("8.6 기준 구조 비교, 신규성 검증과 실증")
P("PRISM-Hub의 가치는 더 단순한 구조와의 비교로만 입증된다. 동일한 반도체 기술, 절연, 냉각, 온도와 부하 프로파일에서 다섯 구조를 비교한다. ① 전전력 승압기와 별도 보조전원모듈, ② 고정비 변환기와 별도 전전력 조정기, ③ PRISM-Hub(400 V 고정 조정), ③′ 보조버스를 410 V 이하로만 제한하는 창 조정 변형(3.2절), ④ 비조정 고정비 V_A에 400 V 부하를 직접 연결하고 광입력 저전압 변환기를 쓰는 구조다. ③′와 ④는 400 V 부하에 B_470급 부품이나 넓은 입력범위를, Stage C에 입력 조정을 요구하므로 부품 전압 등급과 48 V 품질도 비교 항목에 넣는다. PRISM-Hub가 ④와 ③′보다 이점을 보이지 못하면 400±8 V 조정의 가치와 Stage B의 필요성은 성립하지 않는다.")
P("1차 비교는 평균모델과 손실 모델 수준에서 수행하고, 같은 배터리 전압범위, 충전전력, 보조부하 프로파일과 서비스 요구에서 효율지도, 처리전력, 정격 VA, 부품 수와 부품 전압 등급을 평가한다. 예상 신규성은 표 {t:accept}의 기준으로 채택하거나 기각하며, 특허 가능성은 기술 비교와 별도로 청구항 대조표로 판단한다. HIL, 축소전력 시제품과 차량 운전 시나리오 시험은 이 단계의 결과로 가설이 유지될 때 후속 단계에서 수행한다.")
H2("8.7 진척과 일정")
P("18주 계획 대비 작업패키지(Work Package, WP)별 상태는 표 {t:wp}, 남은 기간의 일정은 표 {t:sched}와 같다. P0는 다음 단계 진행에 필요한 필수 과제, P1은 시스템 성능의 완결에 필요한 과제다.")
TB("표 {t:wp}. 작업패키지별 진척(9월 29일 기준)", [3.4, 1.6, 6.4],
   ["작업패키지", "상태", "주요 결과와 남은 작업"],
   [["WP1 요구사항·구조·파라미터 확정", "완료", "충전기 V_A 접속, 포트별 정격, 요구사항·부하 등급·수락 기준 확정. 충전·Stage C 입력은 잠정"],
    ["WP2 평균모델·제어·상태기계", "진행 중", "Stage B 6상태 모델과 지연 보상 제어기(평균모델 기준 충족). MATLAB 교차검증, 통합 상태기계 남음"],
    ["WP3 스위칭 회로 모델", "진행 중", "Stage A 스위칭 ODE 완료. Stage A·B·C 스위칭 회로 모델 남음"],
    ["WP4 시나리오·기준 구조 검증", "진행 중", "Stage B 동특성·강건성 시험 완료. 충전 통합과 기준 구조 비교 남음"],
    ["WP4.5 부하 관리 계층", "진행 중", "계약 기반 승인 절차와 축약 모델 시험 완료. 전기모델 결합과 동적 예산 남음"],
    ["WP5 손실·열·전력밀도", "착수", "Stage A 손실 예측값 확보"],
    ["WP6 문서화·재현자료", "진행 중", "검증 근거와 본 보고서"]],
   "자료: 저자 작성.")
TB("표 {t:sched}. 남은 기간의 우선순위와 일정", [2.6, 1.0, 4.4, 3.4],
   ["기간", "우선순위", "주요 작업", "완료 판단"],
   [["9월 30일–10월 9일", "P0", "제어기 MATLAB 교차검증, 기준 구조 ③′·④ 평균모델 구축", "Python·MATLAB 판정 일치, 비교 모델 준비"],
    ["10월 10일–30일", "P0", "Stage B 스위칭·보호·프리차지 모델과 제어기 이식", "리플 포함 Tier-1 98 A·Tier-2 100 A 통과"],
    ["10월 31일–11월 20일", "P0", "충전기–Stage A–B 통합과 모드 전환, Stage A 위상 모델", "충전·보조부하 동시 운전(H3)"],
    ["11월 21일–12월 4일", "P0", "기준 구조 ①·③′·④ 대비 1차 비교(평균모델·손실 모델)", "동일 경계의 정량 비교표(H5 1차 판정)"],
    ["12월 5일–18일", "P1", "Stage C 5 kW 재설계", "48 V·12 V 동시 최대부하 통과"],
    ["12월 19일–1월 1일", "P1", "부하 승인 계층의 동적 예산, 위반 감시, 전기모델 결합", "H4 기준(전기모델) 판정"],
    ["1월 2일–8일", "P0", "재현성 점검과 최종 보고서", "결과와 근거의 상호 일치"]],
   "자료: 저자 작성.", fs=16)

# ---------------------------------------------------------------- 9
H1("9. 결론")
P("PRISM-Hub는 고정비 대전력 경로와 부분전력 직렬 조정을 결합해 800 V 차량의 400 V 충전 호환과 다중 전압 보조전원을 하나의 직류 전력 구조로 다루는 아키텍처다. 개별 원리에는 선행연구와 특허가 있으므로, 과제의 가치는 이 원리들을 차량 운전조건에 배치하고 포트 정격, 제어 여유와 부하 관리를 정량 기준으로 설계·검증하는 데 있다.")
P("세 연구 질문에 대한 현재의 답은 다음과 같다. Q1(정격 분리)은 평균모델 수준에서 긍정적이다. 25 kW 보조버스에서 Stage B 처리전력은 최대 6.44 kW였고 충전전류는 조정단을 지나지 않지만, 충전 중 동시 운전은 검증되지 않았다. Q2(강건 제어와 부하 승인)도 평균모델 수준에서 긍정적이다. 연산 지연을 보상한 제어기는 공차와 3.0 µs 추가 지연을 포함한 Tier-1·Tier-2 기준을 만족했고, 계약 기반 부하 승인은 예산 초과 없이 서비스 손실을 줄였다. 다만 스위칭 회로와 전기모델에 결합한 검증이 남아 있다. Q3(기준 구조 대비 이점)은 아직 평가하지 않았다. 400±8 V 조정이 외부 요구가 아닌 파생 요구이므로, 조정 없는 구조(④)와 창 조정 변형(③′)과의 비교가 Stage B의 가치를 결정한다.")
P("따라서 다음 단계는 스위칭 수준의 Stage B와 제어기 구현 검증, 충전·보조전원 통합, 기준 구조 비교를 거쳐 예상 신규성을 검증된 기여로 전환하거나 기각하는 것이다.")

# ---------------------------------------------------------------- appendices
PB()
H1("부록 A. 주요 약어 및 용어")
TB("표 A-1. 주요 약어 및 용어", [2.0, 9.4], ["약어", "뜻"],
   [["APM", "Auxiliary Power Module. 고전압 배터리에서 48 V 또는 12 V 전원을 공급하는 보조전원모듈"],
    ["BMS", "Battery Management System. 배터리 상태를 감시하고 충전 한계를 결정하는 관리 시스템"],
    ["CC/CV", "Constant Current / Constant Voltage. 정전류·정전압 충전 방식"],
    ["CLLC", "변압기 양쪽에 인덕터와 커패시터 공진망을 두는 양방향 절연 공진형 변환기"],
    ["DAB", "Dual-Active-Bridge. 변압기 양쪽의 능동 브리지를 이용하는 절연형 양방향 직류-직류 변환기"],
    ["ECU", "Electronic Control Unit. 차량 부하 또는 기능을 제어하고 상태를 통신하는 전자제어기"],
    ["EMI", "Electromagnetic Interference. 전자기 간섭"],
    ["HIL", "Hardware-in-the-Loop. 실제 제어기와 실시간 시뮬레이터를 연결하는 검증 방식"],
    ["LC", "Inductor-Capacitor. 인덕터와 커패시터로 구성한 필터 또는 공진망"],
    ["ODE", "Ordinary Differential Equation. 시간에 따른 회로 상태를 표현하는 상미분방정식"],
    ["PMSM", "Permanent Magnet Synchronous Motor. 영구자석 동기전동기. 차량용 전동 컴프레서의 구동 전동기"],
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
H1("부록 C. 검증 근거 목록")
P("본문의 수치는 다음 검증 근거에서 얻었다. 각 근거는 입력 조건, 판정 기준과 결과를 함께 보관하며 동일 조건에서 재현할 수 있다. 근거별 계산 코드와 실행 방법은 같은 번호 체계로 정리한 검증 코드 묶음(MATLAB, Python)에 수록했다.")
TB("표 C-1. 검증 근거 목록", [0.9, 4.0, 4.6, 1.9], ["번호", "근거", "내용", "도구"],
   [["E1", "Stage A 스위칭 ODE 시험", "8위상 RSC, 고정 타이밍과 영교차 추종의 부품 공차 표본(정·역방향 각 20건), 손실·모듈 셰딩·프리차지", "MATLAB, Python"],
    ["E2", "Stage B 평균모델 정합성", "에너지 보존(임의 상태 1,000개), 평형점 잔차(24점), 적분간격 수렴, Python·MATLAB 이중 구현 대조(12개 동적 사례, 80개 시험조건)", "Python, MATLAB"],
    ["E3", "25 kW 정상상태 전력수지", "640–920 V, 10 V 간격 평형점의 경로전류, 직렬전압, 링크전력과 처리 비율", "Python"],
    ["E4", "요구사항 분석", "부하 입력범위와 규격 대조, 보장 최소 배터리 전압(정적·동적), 창 조정 변형의 처리전력", "Python"],
    ["E5", "제어기 검증 격자", "Tier-1·Tier-2 552건(7개 전압, 공차·민감도 16종, 추가 지연 3.0 µs), 채택 설계와 비교 설계", "Python"],
    ["E6", "지연 여유 분석", "제어주기 폐루프 사상의 표본화 선형화(24개 운전점), 비선형 추가 지연 경계(640·920 V)", "Python"],
    ["E7", "추가 강건성 시험", "복합 공차 128개 코너(640 V), 필터 인덕터 공차 ±5 % 재시험, 부하 계약 최악 시퀀스 48건", "Python"],
    ["E8", "부하 승인 시험", "무작위 시나리오 200개(각 20 s), 메시지 지연 1–5 ms, 손실 0–20 %, 관리 없음·정적 예약·계약 기반 승인 비교", "Python"],
    ["E9", "제어기 설계 대안 비교", "극배치 대역폭·극 배치 변경과 전압항 포화의 지연 여유·전류·안정성", "Python"],
    ["E10", "Stage C 스위칭 ODE 시험", "3 kW CLLC 후보 설계의 전압이득(0.3–3 kW, 스위칭주파수/공진주파수 0.9–1.1, 기본파 근사 대조), 입력 ±2 %, ZVS 여유", "MATLAB, Python"]],
   "자료: 저자 작성.", fs=16)
