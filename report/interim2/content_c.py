# 2차 중간보고서 본문(3): 8–10장, 부록
from content_b import B, H1, H2, P, BL, TB, FG, PB

# ---------------------------------------------------------------- 8
H1("8. 가설 충족 현황과 한계")
H2("8.1 가설별 현황")
P("다섯 가설 가운데 Stage B 자체의 동작을 묻는 H2는 여러 수준의 모델에서 충족했다. 충전 통합(H3)과 기준 구조 대비 가치(H5)가 아직 열려 있다(표 {t:status}). 모든 판정은 해당 모델과 조건 안에서만 유효하며, 하드웨어 성능을 뜻하지 않는다.")
TB("표 {t:status}. 가설별 현재 상태(10월 15일)", [2.0, 1.9, 4.6, 2.9],
   ["가설", "상태", "근거", "남은 검증"],
   [["H1 정격 분리", "부분 충족", "주행 중 링크 정상 최대 6.44 kW, 과도 최대 7.35 kW(평균모델)·7.19 kW(스위칭 모델) ≤ 8 kW. 충전전류는 구조상 Stage B 비경유(E3, E5, E12)", "충전 중 동시 운전의 링크전력(H3 통합)"],
    ["H2 강건 제어", "충족(Stage B 모델 범위)", "평균모델 Tier-1 460/460·Tier-2 78/78, 독립 구현 1,542건 일치, 스위칭 모델 Tier-1 480/480·Tier-2 96/96, 요구 사양 센서 168/168, 회로 모델 대표 사례 일치(E5–E7, E11, E12, TB04·TB04B)", "보호 상태기계·감시 포함 재계산, 통합 모델"],
    ["H3 충전 중 보조버스", "미검증", "—", "충전기–Stage A–B 통합, 접속·해제와 모드 전환"],
    ["H4 부하 승인", "충족(축약 모델)", "예산 초과 0, 승인 지연 최대 17 ms, 미공급 7.0 %(정적 예약 35.2 %)(E8)", "전압 의존 예산, 위반 감시, 전기모델 결합"],
    ["H5 기준 구조 대비 이점", "1차 비교만 완료", "400 V 조정만 고정이득 Stage C와 B_420을 함께 허용, 비조정 구조는 감쇠기 또는 Stage A 과도 정격 상향 필요(E13)", "손실·정격 VA·반도체 수의 동일 경계 비교"]],
   "자료: 저자 작성(부록 C).", fs=16)
H2("8.2 현재 근거의 한계")
for x in ["**모델 수준.** 모든 결과는 시뮬레이션이다. 회로 모델의 스위치 셀은 이상 스위치, 다이오드와 선형 출력용량으로 구성되며, 소자 스위칭 손실, 게이트 드라이버, 배선 기생성분, 열, 절연과 전자기 간섭은 포함하지 않는다.",
          "**Stage A 결합.** Stage B·C 검증에서 Stage A는 이상 2:1 전압원과 경로 저항·인덕턴스로 두었다. Stage A 위상 모델과의 결합은 TB06과 충전 통합(H3)에서 확인한다.",
          "**회로 모델의 범위.** 회로 모델은 단계별 대표 사례에서 검증 모델과의 일치를 보였다. 넓은 시험 격자(수백–수천 건)의 판정은 검증 모델이 맡는다.",
          "**보호.** 정지·기동 전이는 평균모델에서 시험했다. 차단 소자의 동작 시간과 탈포화 검출 지연은 포함하지 않았다. 타당성 감시를 켠 상태의 스위칭 모델 전체 재계산도 남아 있다.",
          "**여유.** 복합 공차 Tier-2 코너의 전류 여유는 물리정격 대비 2.7 A다. Tier-2 기준에는 감지 오차 여유가 없으므로 보호 설계와 함께 다시 확인한다.",
          "**Stage C와 SALS.** Stage C는 3 kW 후보 설계만 검증했고, SALS는 1 ms 축약 부하 모델에서 전기모델과 결합하지 않고 검증했다.",
          "**비교.** 효율, 정격 VA, 반도체 수, 부피와 비용을 기준 구조와 같은 조건에서 비교하지 않았다. 자기소자 정격의 감소를 제품 부피나 원가 감소로 직접 환산할 수 없다."]:
    BL(x)

# ---------------------------------------------------------------- 9
H1("9. 향후 계획")
H2("9.1 남은 작업 개요")
P("남은 작업은 여섯 가지이며, 각 작업이 답하는 질문과 완료 기준은 표 {t:plan}과 같다. P0는 다음 단계 진행이나 가설 판정에 필수인 과제이고, P1은 시스템 성능의 완결에 필요한 과제다.")
TB("표 {t:plan}. 남은 작업, 필요성과 완료 기준", [2.7, 0.9, 4.0, 3.8],
   ["작업", "순위", "필요한 이유", "완료 기준"],
   [["통합 회로 모델(TB06)", "P0", "따로 검증한 세 단을 한 회로로 연결해 단 사이 상호작용을 확인하고 제출용 최종 모델을 만든다", "Tier-1 대표 스텝의 과도 응답, 전류·전압 한계 통과, Stage A ZCS 유지"],
    ["보호 상태기계 결합", "P0", "P1–P6이 스위칭 수준과 차단 지연을 포함해도 성립해야 한다", "정지·기동·고장 전이에서 포트 정격과 버스 260–420 V, 감시 포함 판정 유지"],
    ["충전 통합(H3)", "P0", "충전 대전류가 조정단을 지나지 않는다는 배치의 핵심 전제를 동시 운전에서 확인한다", "150 kW(375 A 제한) 충전 + 25 kW 보조부하에서 Tier-1, 모드 전환에서 Tier-2"],
    ["기준 구조 손실·정격 비교(H5)", "P0", "400 V 조정이 파생 요구이므로 Stage B의 가치는 비교로만 입증된다", "구조 ①·②·③·③′·④의 동일 경계 정량 비교와 H5 판정"],
    ["Stage C 5 kW 재설계", "P1", "48 V 3 kW와 12 V 1.5 kW 동시 공급에 약 4.55 kW가 필요하다", "입력 384–416 V, 동시 최대부하·회생에서 48 V 편차 ±2 % 이내"],
    ["SALS 고도화", "P1", "정적 예산을 전압 의존 여유로 넓히고 전기모델에서 승인 논리를 확인한다", "H4 기준을 전기모델 결합 상태에서 만족"]],
   "자료: 저자 작성.", align=["l", "c", "l", "l"], fs=16)
H2("9.2 통합 회로 모델(TB06)")
P("TB06은 주행 모드의 통합 회로 모델이다. 구성은 다음과 같다.")
BL("Stage A 1모듈(2위상, 영교차 추종 게이트)")
BL("Stage B 회로(TB04B, 후보 소자 출력용량)")
BL("Stage C 회로(TB05)")
BL("400 V 정전력 부하")
P("세 단을 한 회로로 묶어 다음 세 가지 단 사이 상호작용을 확인한다.")
BL("Stage A 출력 리플과 출력 임피던스가 Stage B 경로전류와 버스전압에 주는 영향")
BL("Stage B가 끌어가는 경로전류에서 Stage A ZCS가 유지되는지")
BL("Stage C 입력전류 리플과 버스 커패시터의 상호작용")
P("기준값은 같은 조건으로 결합한 검증 모델 계산(Stage A 스위칭 모델, E12, Stage C 식)으로 둔다.")
P("세 단을 함께 계산하려면 적분 간격 5 ns를 써야 한다. 그런데 TB04B에서 보였듯이 이 간격은 게이트 격자이기도 해서, 정상상태 리플이 실제보다 큰 리밋 사이클로 나타난다. 따라서 TB06에서 마지막 1 ms 리플은 판정하지 않고 정보로만 기록한다. 판정은 과도 응답, 전류·전압 한계와 단 사이 상호작용으로 한다. 정상상태 리플 기준은 0.625 ns 격자의 TB04B와 검증 모델 계산을 근거로 한다. Stage C의 5 ns 결과에는 후진 오일러 수치 감쇠에 의한 등가 손실(3 kW에서 약 34 W)을 함께 적는다. TB06은 제출용 최종 통합 모델이 된다.")
H2("9.3 보호 상태기계 결합과 스위칭 모델 재계산")
P("E14에서 도출한 P1–P6을 하나의 보호·기동 상태기계로 구현하고 Stage B 스위칭 모델(E12)에 결합한다. 상태기계가 다루는 동작은 다음과 같다.")
BL("제어 정지")
BL("Stage A 협조 정지")
BL("기동 인계")
BL("링크 프리차지")
BL("센서 고장 대응")
P("평균모델에 없던 두 지연을 함께 반영한다. 하나는 차단 소자의 동작 시간이고, 다른 하나는 게이트 드라이버의 탈포화 검출 지연이다. 링크전류 센서 타당성 감시를 켠 상태로 E12의 전체 시험(약 3,200건)을 다시 계산해, 감시가 정상 운전의 판정을 바꾸지 않는지 확인한다. 대표 정지·기동·고장 전이는 회로 모델 테스트벤치로 재현한다.")
H2("9.4 충전 통합(H3)")
P("충전기 모델(전압·전류·전력 한계와 CC/CV, 응답 시간), Stage A, Stage B(E12), 400 V 부하와 Stage C를 연결해 다음 상황을 시험한다.")
BL("150 kW(375 A 제한) 충전과 25 kW 보조부하의 동시 운전")
BL("충전기 접속·해제")
BL("충전 중 보조부하 스텝")
BL("회생 전환과 모듈 투입")
BL("적분기 초기화와 무충격 전환")
P("이 시험으로 충전 중 Stage B 링크전력이 8 kW 이하인지 확인해 H1을 완결한다. 또 충전기 전류 요청에 보조부하 몫을 더하는 차량 측 절차가 버스 품질을 지키는지 확인한다. 넓은 시나리오 판정은 통합 평균모델과 스위칭 모델이 맡고, 대표 접속·해제 사례는 회로 모델로 확인한다.")
H2("9.5 기준 구조 대비 손실·정격 비교(H5)")
P("다섯 구조를 같은 반도체 기술, 냉각, 부하 계약과 운전 프로파일로 비교한다.")
BL("① 전전력 승압기 + 별도 보조전원모듈")
BL("② 고정비 변환기 + 별도 전전력 조정기")
BL("③ PRISM-Hub")
BL("③′ 창 조정")
BL("④ 비조정")
P("비교 항목은 다음과 같다.")
BL("운전 프로파일(배터리 전압 분포와 부하 분포)로 가중한 손실")
BL("정격 VA와 반도체 수")
BL("부품 전압 등급")
BL("구조별 추가 부품: ③′의 바이패스 스위치, ④의 감쇠기, ③′·④의 조정형 Stage C")
BL("고장 시 서비스 연속성")
P("③′는 Stage B가 동작하는 시간이 배터리 전압 분포에 따라 크게 달라지므로, 프로파일 가정의 민감도를 함께 보고한다. PRISM-Hub가 ④와 ③′보다 수락 기준만큼의 이점을 보이지 못하면 400±8 V 조정의 가치와 Stage B의 필요성은 성립하지 않는 것으로 판정한다.")
H2("9.6 Stage C 5 kW 재설계")
P("48 V 3 kW와 12 V 1.5 kW 동시부하(400 V 측 약 4.55 kW)를 충족하도록 공진탱크와 변압기를 약 5 kW로 재설계한다. 검증 항목은 다음과 같다.")
BL("정류 손실과 자화전류")
BL("경부하 ZVS")
BL("보조버스 Tier-2 창(384–416 V)에서의 출력")
BL("48 V 회생 방향의 전류 폐루프")
P("설계 스윕은 스위칭 수준 모델로 하고, 선정 설계는 회로 모델 테스트벤치로 확인한다.")
H2("9.7 부하 승인 계층 고도화")
P("세 가지를 보완한다.")
BL("정적 예산을 배터리 전압과 현재 부하에 따른 동적 여유로 확장한다. 공차·지연 여유는 차감한다.")
BL("측정 합계가 최악값 경계를 넘으면 계약 위반으로 판단해 지연 가능 부하를 차단하는 감시 기능을 추가한다.")
BL("SALS를 평균모델과 결합해 승인 논리와 전기적 과도를 함께 판정한다.")
P("난방·제상·배터리 예열의 서비스 허용치는 열 모델로 정한다.")
H2("9.8 검증 도구 구성")
P("남은 작업도 4.1절의 계층을 따르며, 두 층으로 나누어 진행한다.")
BL("**넓은 판정.** 수백–수천 건의 시험 격자는 계산이 빠른 평균모델과 스위칭 수준 모델(Python·MATLAB)이 맡는다.")
BL("**대표 확인.** 각 단계의 대표 사례는 Simulink 회로 테스트벤치로 다시 확인하고 제출물로 남긴다.")
P("회로 모델은 사례당 계산 시간이 검증 모델보다 길다. 그래서 전 격자를 회로 모델로 반복하기보다, 두 층의 일치를 대표 사례에서 확인하는 방식이 일정 안에서 신뢰도를 가장 높인다. TB04B처럼 두 층이 어긋나면 원인을 분리하고, 필요하면 검증 모델 쪽에 모델 요소를 더해 넓은 격자에서 다시 판정한다(표 {t:tools}).")
TB("표 {t:tools}. 남은 작업의 도구 구성", [2.8, 4.4, 4.2],
   ["작업", "넓은 판정(검증 모델)", "대표 확인(Simulink 회로 모델)"],
   [["통합 모델", "결합 검증 모델(Stage A 스위칭 모델 + E12 + Stage C 식)", "TB06: Stage A 1모듈 + B + C + 부하"],
    ["보호·기동", "E12 + 보호 상태기계, 감시 포함 전체 재계산", "대표 정지·기동·고장 전이"],
    ["충전 통합(H3)", "통합 평균모델 + E12, 모드 전환 시나리오", "충전기 접속·해제, 동시 운전 대표 사례"],
    ["기준 구조 비교(H5)", "평균모델·손실 모델, 운전 프로파일 가중", "손실 모델 검산용 대표 운전점"],
    ["Stage C 5 kW", "스위칭 수준 모델 설계 스윕", "선정 설계의 CLLC 테스트벤치"],
    ["SALS", "축약 모델 + 평균모델 결합", "필요 시 대표 부하 시나리오"]],
   "자료: 저자 작성.", fs=16)
H2("9.9 일정과 작업패키지")
P("작업패키지(Work Package, WP)별 진척은 표 {t:wp}, 남은 기간의 일정은 표 {t:sched}와 같다. 1차 보고의 일정과 비교하면 다음과 같다.")
BL("9월 30일–10월 9일의 교차검증과 기준 구조 모델은 계획대로 끝났다.")
BL("10월 10일–30일 구간의 Stage B 스위칭 검증과 회로 모델 TB01–TB05는 앞당겨 마쳤다.")
BL("남은 보호 상태기계 결합과 TB06을 같은 구간에 마치면, 이후 일정은 1차 보고와 같다.")
P("위험 요인은 TB06의 계산 시간과 세 단 결합에서 생길 수 있는 수치 문제다. 이 경우 Stage A를 등가 모델로 둔 축소 통합을 먼저 판정하고, 위상 모델 결합은 충전 통합 구간에서 이어 간다.")
TB("표 {t:wp}. 작업패키지별 진척(10월 15일 기준)", [3.4, 1.4, 6.6],
   ["작업패키지", "상태", "주요 결과와 남은 작업"],
   [["WP1 요구사항·구조·파라미터 확정", "완료", "요구사항·부하 등급·수락 기준 확정, 센서·게이트·보호 하위 요구 추가. 충전·Stage C 입력은 잠정"],
    ["WP2 평균모델·제어·상태기계", "진행 중", "채택 제어기 MATLAB 교차검증 완료(E11), 보호·기동 요구 도출(E14). 보호 상태기계 구현·결합 남음"],
    ["WP3 스위칭 회로 모델", "진행 중", "Stage B 스위칭 모델(E12), Simulink TB01–TB05 완료. 통합 모델 TB06 남음"],
    ["WP4 시나리오·기준 구조 검증", "진행 중", "기준 구조 ③′·④ 1차 비교 완료(E13). 충전 통합(H3), 손실·정격 비교(H5) 남음"],
    ["WP4.5 부하 관리 계층", "진행 중", "계약 기반 승인과 축약 모델 시험 완료. 동적 예산·위반 감시·전기모델 결합 남음"],
    ["WP5 손실·열·전력밀도", "착수", "Stage A 손실 예측값 확보. H5 손실 모델과 함께 진행"],
    ["WP6 문서화·재현자료", "진행 중", "검증 근거 E1–E14와 테스트벤치 TB01–TB05 정리, 본 보고서"]],
   "자료: 저자 작성.", fs=16)
TB("표 {t:sched}. 남은 기간의 일정", [2.6, 1.0, 4.6, 3.2],
   ["기간", "순위", "주요 작업", "완료 판단"],
   [["10월 16일–30일", "P0", "통합 회로 모델 TB06. 보호 상태기계를 스위칭 모델에 결합하고 감시를 켠 E12 전체 재계산", "TB06 과도·한계 판정, 감시·보호 포함 판정 유지"],
    ["10월 31일–11월 20일", "P0", "충전기–Stage A–B 통합과 모드 전환(H3), 대표 사례 회로 확인", "충전·보조부하 동시 운전 Tier-1, 전환 Tier-2"],
    ["11월 21일–12월 4일", "P0", "기준 구조 ①·②·③′·④ 대비 손실·정격 비교(H5)", "동일 경계 정량 비교표, H5 판정"],
    ["12월 5일–18일", "P1", "Stage C 5 kW 재설계와 회로 확인", "48 V·12 V 동시 최대부하 통과"],
    ["12월 19일–1월 1일", "P1", "SALS 동적 예산, 위반 감시, 전기모델 결합", "H4(전기모델) 판정"],
    ["1월 2일–8일", "P0", "재현성 점검과 최종 보고서", "결과와 근거의 상호 일치"]],
   "자료: 저자 작성.", fs=16)

# ---------------------------------------------------------------- 10
H1("10. 결론")
P("PRISM-Hub는 고정비 대전력 경로와 직렬 부분전력 조정을 결합해, 800 V 차량의 400 V 충전 호환과 다중 전압 보조전원을 하나의 직류 전력 구조로 다루는 아키텍처다. 개별 원리에는 선행연구가 있으므로, 과제의 가치는 이 원리들을 차량 운전조건에 배치하고 포트 정격, 제어 여유와 부하 관리를 정량 기준으로 설계·검증하는 데 있다.")
P("1차 보고 이후 Stage B의 근거는 평균모델 단일 구현에서 네 수준으로 넓어졌다.")
BL("독립 구현(E11)")
BL("스위칭 수준 모델(E12)")
BL("보호·기동 해석(E14)")
BL("소자 수준 회로 모델(TB01–TB05)")
P("세 연구 질문에 대한 현재의 답은 다음과 같다.")
BL("**Q2(강건 제어와 부하 관리): 긍정적.** 채택 제어기는 리플, 데드타임, 출력용량, 센서 오차와 공차·지연을 포함한 조건에서 전압 품질과 포트 정격을 지켰다. 회로 모델에서도 같은 응답이 재현되었다.")
BL("**Q1(정격 분리): 주행 조건에서 긍정적.** 충전 중 동시 운전은 남아 있다.")
BL("**Q3(기준 구조 대비 이점): 판단 근거 일부 확보.** 400 V 조정의 가치가 과도 전압 품질이 아니라 정적 전압 범위와 경로전류 제어에서 나온다는 판단 근거를 얻었다. 손실·정격 비교는 남아 있다.")
P("검증 과정에서 설계에 반영할 하위 요구도 구체화되었다.")
BL("DAB 링크전류의 측정 기반 보정")
BL("데드타임 부분 보상")
BL("16비트 센서 사양")
BL("게이트 시간 분해능 0.625 ns 이하")
BL("보호·기동 절차 P1–P6")
P("남은 기간에는 통합 회로 모델과 보호 결합으로 Stage B 검증을 마무리한다. 이어서 충전 통합(H3)과 기준 구조 대비 손실·정격 비교(H5)로 예상 이점을 검증된 기여로 전환하거나 기각한다.")

# ---------------------------------------------------------------- appendices
PB()
H1("부록 A. 주요 약어 및 용어")
TB("표 A-1. 주요 약어 및 용어", [2.0, 9.4], ["약어", "뜻"],
   [["ADC", "Analog-to-Digital Converter. 아날로그–디지털 변환기"],
    ["CC/CV", "Constant Current / Constant Voltage. 정전류·정전압 충전 방식"],
    ["CLLC", "변압기 양쪽에 인덕터와 커패시터 공진망을 두는 양방향 절연 공진형 변환기"],
    ["C_oss, C_o(tr), C_o(er)", "소자 출력용량과 그 시간 등가·에너지 등가 값"],
    ["DAB", "Dual-Active-Bridge. 변압기 양쪽의 능동 브리지를 이용하는 절연형 양방향 직류-직류 변환기"],
    ["HIL", "Hardware-in-the-Loop. 실제 제어기와 실시간 시뮬레이터를 연결하는 검증 방식"],
    ["HRPWM, MEP", "High-Resolution PWM, Micro Edge Positioning. 클록 주기보다 작은 단계로 PWM 에지를 놓는 기능과 그 단계"],
    ["ODE", "Ordinary Differential Equation. 시간에 따른 회로 상태를 표현하는 상미분방정식"],
    ["PWM", "Pulse-Width Modulation. 스위치의 켜짐 시간을 조절해 평균전압을 제어하는 펄스폭변조"],
    ["RSC", "Resonant Switched-Capacitor Converter. 공진전류와 스위치드 커패시터를 이용하는 고정비 변환기"],
    ["SALS", "Saturation-Aware Anticipatory Load Shaping. 조정단의 정격을 고려해 지연 가능한 부하를 승인·제한하는 상위 계층"],
    ["SPS", "Single-Phase Shift. DAB 양쪽 브리지의 위상차로 전력을 조절하는 단일 위상천이 방식"],
    ["TB", "Testbench. 검증 단계별로 남긴 Simulink 회로 모델 파일"],
    ["Tier-1 / Tier-2", "계약 내 부하 변화 / 계약 위반·고장 포락선의 과도 시험 등급"],
    ["V_A", "Stage A의 2:1 고정비 출력과 400 V급 충전기가 접속하는 내부 직류 노드"],
    ["ZCS / ZVS", "Zero-Current / Zero-Voltage Switching. 스위치 전환 시 전류 또는 전압을 0에 가깝게 만드는 소프트 스위칭"],
    ["③, ③′, ④", "기준선(400 V 고정 조정), 창 조정 변형(버스 ≤ 410 V), 비조정 구조(버스 = V_A)"]],
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
 "Y. Li, X. Lyu, Z. Ni, D. Cao, C. Nan, S. Jiang, “Adaptive On-Time Control for High Efficiency Switched-Tank Converter,” IEEE WiPDA Asia, pp. 169–175, 2018. DOI: 10.1109/WiPDAAsia.2018.8734623.",
 "R. D. Middlebrook, “Input Filter Considerations in Design and Application of Switching Regulators,” IEEE Industry Applications Society Annual Meeting, pp. 366–382, 1976.",
 "R. W. Erickson, D. Maksimović, Fundamentals of Power Electronics, 3rd ed., Springer, 2020, chapter “Input Filter Design.”",
 "A. Emadi, A. Khaligh, C. H. Rivetta, G. A. Williamson, “Constant Power Loads and Negative Impedance Instability in Automotive Systems: Definition, Modeling, Stability, and Control of Power Electronic Converters and Motor Drives,” IEEE Transactions on Vehicular Technology, vol. 55, no. 4, pp. 1112–1125, 2006. DOI: 10.1109/TVT.2006.877483.",
 "GaN Systems (Infineon), “GS66516T Top-side cooled 650 V E-mode GaN transistor,” datasheet Rev. 210727, C_O(TR)·C_O(ER) at V_DS 0–400 V. 제조사 공개자료.",
 "Efficient Power Conversion, “EPC2305 – Enhancement Mode Power Transistor (150 V, 2.2 mΩ),” datasheet, C_OSS(TR)·C_OSS(ER) at V_DS 0–75 V. 제조사 공개자료.",
 "A. V. Peterchev, S. R. Sanders, “Quantization Resolution and Limit Cycling in Digitally Controlled PWM Converters,” IEEE Transactions on Power Electronics, vol. 18, no. 1, pp. 301–308, 2003. DOI: 10.1109/TPEL.2002.807092.",
 "Texas Instruments, “Functional Safety Information: TMS320F280015x Real-Time Microcontrollers,” SFFS222, HRPWM section (MEP step on the order of 150 ps). 제조사 공개자료.",
]
B.append({"t": "refs", "items": REFS})
PB()
H1("부록 C. 검증 근거 목록")
P("본문의 수치는 다음 검증 근거에서 얻었다. 각 근거는 입력 조건, 판정 기준과 결과를 함께 보관하며 같은 조건에서 재현할 수 있다. 검증 코드(MATLAB, Python)와 Simulink 테스트벤치는 같은 번호 체계로 정리했다.")
TB("표 C-1. 검증 근거 목록", [1.0, 3.4, 5.2, 1.8], ["번호", "근거", "내용", "도구"],
   [["E1", "Stage A 스위칭 시험", "8위상 RSC, 고정 타이밍과 영교차 추종의 부품 공차 표본(정·역방향 각 20건), 손실·모듈 셰딩·프리차지", "MATLAB, Python"],
    ["E2", "Stage B 평균모델 정합성", "에너지 보존, 평형점 잔차, 적분간격 수렴, Python·MATLAB 이중 구현 대조", "Python, MATLAB"],
    ["E3", "25 kW 정상상태 전력수지", "640–920 V 평형점의 경로전류, 직렬전압, 링크전력과 처리 비율", "Python"],
    ["E4", "요구사항 분석", "부하 입력범위와 규격 대조, 보장 최소 배터리 전압, 창 조정 변형의 처리전력", "Python"],
    ["E5", "제어기 검증 격자", "Tier-1·Tier-2 552건(7개 전압, 공차·민감도 16종, 추가 지연 3.0 µs), 채택·비교 설계", "Python"],
    ["E6", "지연 여유 분석", "제어주기 폐루프 사상의 표본화 선형화(24개 운전점), 비선형 추가 지연 경계", "Python"],
    ["E7", "추가 강건성 시험", "복합 공차 128개 코너, 필터 인덕터 공차 ±5 % 재시험, 부하 계약 최악 시퀀스 48건", "Python"],
    ["E8", "부하 승인 시험", "무작위 시나리오 200개(각 20 s), 메시지 지연·손실, 관리 방식 3종 비교", "Python"],
    ["E9", "제어기 설계 대안 비교", "대역폭·극 배치 변경과 전압항 포화의 지연 여유·전류·안정성", "Python"],
    ["E10", "Stage C 스위칭 시험", "3 kW CLLC 후보 설계의 전압이득, 입력 변동, ZVS 여유", "MATLAB, Python"],
    ["E11", "채택 제어기 독립 구현", "MATLAB 재구현과 1,542건 판정·세부 항목·지표 대조", "MATLAB(Octave), Python"],
    ["E12", "Stage B 스위칭 모델", "PWM·데드타임·출력용량·DAB SPS, 시험 격자·코너·시퀀스, DAB 전류 제한, 데드타임 보상, 센서 사양, 게이트 시간 분해능", "Python(Numba)"],
    ["E13", "기준 구조 1차 비교", "③·③′·④의 정적 범위, Tier 시험, 감쇠기 설계, 정전력 부하 안정성", "Python"],
    ["E14", "Stage B 보호·기동", "정지·기동 전이, 링크 프리차지, 링크전류 센서 고장과 타당성 감시", "Python"],
    ["TB01", "Stage A 1위상 회로", "고정 타이밍 공진전류·턴오프 전류, E1 대조", "Simulink"],
    ["TB02", "Stage B H-브리지 회로", "데드타임·출력용량 전압오차, 교정표 대조", "Simulink"],
    ["TB03", "Stage B DAB 회로", "위상 계단, 변압기 직류 편류, 데드타임 영역, E12 대조", "Simulink"],
    ["TB04", "Stage B 폐루프 회로", "채택 제어기 결합, Tier-1 대표 스텝 2건, E12 대조", "Simulink"],
    ["TB04B", "Stage B 폐루프(후보 소자 출력용량)", "DAB C_oss 데이터시트 값, 게이트 격자 5–0.625 ns", "Simulink"],
    ["TB05", "Stage C CLLC 회로", "3·1.5·0.3 kW 이득·전류·ZVS, 해석기 수치 감쇠", "Simulink"]],
   "자료: 저자 작성.", fs=16)
