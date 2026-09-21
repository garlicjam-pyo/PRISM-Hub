# PRISM-Hub 하드웨어 선행기술 및 참고문헌 검토

검토일: 2026-09-21\
검토 대상: garlicjam-pyo/PRISM-Hub, commit `959efdfb8fa504d407309eb9b1217041dd93f15d`\
대상 문서: `docs/02_엔지니어링_설계검증서.md` 2.5절·7장, `docs/03_논문_구조안.md`\
범위: 회로·시스템 하드웨어 신규성, 비교 기준, 중요 참고문헌의 실재성과 주장 적합성. 제어 알고리즘 코드 검증은 별도 검토에 해당한다.

## 1. 판정

**고정비 공진 SC/STC + 부분전력 조정, 400/800 V 고정비 충전 인터페이스, 양방향 버스 공급, 부스터와 APM 통합, 공진 공차를 보상하는 적응형 on-time 제어는 각각 이미 알려져 있다.** 따라서 “유일한 아이디어” 또는 이 요소 자체의 최초 제안으로 주장할 근거는 없다.

PRISM-Hub의 남는 기여 후보는 **주행·400 V 충전·800 V 충전의 서로 다른 요구를 하나의 구체적인 전력회로로 만족시키면서 PPRC 정격·손실·부피·안정성·부하 지연 사이의 설계 관계를 입증하는 것**이다. 하지만 현재 저장소의 블록도와 부분별 시뮬레이션만으로 그러한 시스템 기여가 완성되었다고 판단할 수 없다. 아래에 제시한 각 선행기술이 PRISM 전체와 완전히 같다는 뜻은 아니다. 반대로 이번 공개자료 검색에서 완전히 같은 회로를 찾지 못했다고 해서 유일성을 증명하는 것도 아니다.

“단일 박스 통합”과 “새 전력회로/새 제어 원리”는 구별해야 한다. 전자는 제품 설계의 가치가 될 수 있지만 이미 판매업체가 제시하는 기능이어서 단독으로 강한 논문 신규성을 구성하기 어렵다.

## 2. 가장 가까운 선행기술과 차이

| 선행기술 | 검증된 내용 | PRISM과 겹치는 부분 | PRISM이 추가 입증해야 할 차이 |
|---|---|---|---|
| He, Jiang, Nan, APEC 2018 [H1] | 고정비 STC와 조정 컨버터를 부분전력 구조로 결합. 공개 저자 소속기관 초록에 48→12 V, 500 W, peak 98.4%, 약 800 W/in³ 시제품이 명시됨 | 대전력 고효율 비조정 경로와 작은 조정 경로의 역할 분담 | 150 kW EV 조건, 정확한 결선, 모드 전환, 회생, 보조부하 공급을 별도 입증 |
| Ni et al., APEC 2019 [H2] | EV용 STC+PPVR. 200–400 V 입력, 1200 V 출력, 4 kW 시제품. STC 6배 변환과 buck PPVR. 설계 전부하 효율 97.71% | EV 적용, 광범위 배터리 전압 조정, GaN, 비조정 STC와 부분전력 조정의 결합 | 단순 EV 적용/저전압 소자 사용은 차별점이 아님. 2:1 양방향 허브의 실제 기능과 비용을 비교해야 함 |
| Ni et al., TPEL 2020 [H3] | 300↔600 V, 100 kW 양방향 SiC STC. 실측 peak 98.7%@약30 kW, 98.5%@50 kW, 97.4%@100 kW, 주회로 42 kW/L | 2:1 대전력 STC, 교통전동화, SiC, ZCS | 99.69% 계산치를 근거로 대전력 STC의 손실 문제가 해결됐다고 볼 수 없음. ESR·버스바·온도·구동 손실을 같은 경계에서 비교 |
| Liu et al., APEC 2023/2024 [H4] | 800/1600 V, 500 kW급 다상 STC 설계와 후속 실험 논문 존재. 2023 IEEE 초록은 99.3%, 135 kW/L를 **추정치**라고 명시 | 다상 interleaving을 통한 고전력·고밀도 확장 | 150 kW, 8위상이라는 스케일/위상 수만으로 신규성을 만들 수 없음. 2024 전부하 실험 수치는 원문 추가 확보 후 비교 |
| Li et al., WiPDA Asia 2018 [H5] | 공진 탱크 불일치 문제, 적응형 on-time으로 soft switching 확보. 1.2 kW 6:1 시제품과 효율 개선 실험 | 공차 때문에 고정 50% 구동이 부적합하고 ZCS 추종이 필요하다는 발견 | PRISM의 자기발진/블랭킹 구현이 기존 방식보다 무엇을 보장하는지, 다상 동기·current sharing·센서 오프셋 하에서 비교 |
| Wang & Chen, JESTPE 2022 [H6] | 직렬 전압 보상기로 DPP 버스 차동전압을 부분전력 조정. 정격과 추가 전력변환 스트레스, 적용 가능 범위를 분석 | 고정된/준고정된 주경로에 작은 직렬 전압을 더하거나 빼는 역할 | DPP 다중 부하와 EV 허브는 다르지만 “작은 직렬 보상으로 전압 조정”은 기존 원리 |
| Hassanpour et al., RTUCON 2021/TPEL 2023 [H7] | DAB 기반 직렬 PPC 및 양극성 series-port를 갖는 전류원 기반 step-up/down PPC. 2023 논문은 near-zero series voltage, 소자응력, 보호·soft-start를 핵심으로 삼음 | 절연 셀을 통한 직렬 부분전력 보상과 양극성 조정 | 일반 DAB가 양방향 전력을 다룬다는 사실만으로 ±90 V DC 출력을 보장할 수 없음. PRISM의 bipolar 회로를 실제 구현하고 0 V 통과와 소자응력을 비교 |
| Vicor 고정비 모듈의 battery virtualization [H8] | 37.5 kW, 400/800 V, 양방향 2:1 모듈; 병렬 확장; peak 99%; 충전기에 Vbat/2가 보이고 비충전 시 400 V 부하 공급 | 고정비 400/800 V 충전, 대전력 모듈 병렬화, 충전/주행 경로 공유 | PRISM의 추가 가치는 정밀 400 V 조정·포트 통합의 비용/성능으로 입증해야 함 |
| Preh Combo Box [H9] | 800 V booster + PDU + 3.5 kW DC/DC를 하나의 제품으로 통합한다고 공식 공개 | 부스터·보조전원·분배 기능의 허브/박스 통합 | 장치 수 2→1이 업계 최신 구조 대비 고유 장점이라는 주장은 부적절 |
| Wood/Vicor, MPEL 2025 [H10] | 고정비 양방향 HV→48 V 모듈을 EV 전력망과 회생 부하에 적용 | Stage C를 DC transformer처럼 사용하고 48 V 회생을 수용하는 접근 | 실제 48 V 창·포트 전류 제한·과전압 억제를 정합성 있게 검증 |
| Sathri, Virginia Tech 석사학위논문 2025 [H11] | 모듈형 CLLC 부분전력 구조에 bypass 제어로 넓은 전압 범위와 양방향 전력 흐름 제공; 시뮬레이션과 하드웨어 검증 | 모드별 bypass와 공진 컨버터의 부분전력 통합이라는 넓은 발상 | PRISM의 bypass 위치·목적은 다르므로 동일 회로로 단정 불가. 다만 “bypass + partial power + CLLC” 조합 자체도 폭넓게 검색해야 함 |

### 중요한 해석

- 저장소 2.5절은 STC+PPP가 알려진 원리라고 인정한다. 이 수정은 타당하다. 다만 “차별점은 통합·역할 전환·바이패스”라는 새 주장도 [H8]·[H9]·[H11]과 대조해야 하며, 그것만으로 신규성이 확보되는 것은 아니다.
- [H2]의 구조를 “비절연 buck”이라고만 줄이면 비교가 불충분하다. 비교표에 전체 STC+PPVR 결선, 입력/출력 전압 창, 처리전력 비율, 쌍방향 여부, 전압 극성, 소자별 정격을 포함해야 한다.
- [H1]의 결선은 공개 본문 설명상 STC와 인덕터형 컨버터의 **입력 직렬·출력 병렬(ISOP)** 구성이다. 따라서 이를 PRISM 직렬 출력 주입과 완전히 같은 결선으로 그려서는 안 된다. 같은 점은 “고정비+부분전력 조정 원리”, 다른 점은 구체 결선과 전력 흐름이다.
- [H5]가 이미 탱크 공차와 on-time 보상을 실험했다. PRISM에서 이를 다시 확인한 것은 좋은 설계 검증이지만 새로운 현상 발견으로 표현하기 어렵다.
- [H3]의 실측 전부하 97.4%가 모든 STC의 한계라는 뜻은 아니다. 다만 PRISM의 99.69%가 동일 원리의 필연적 결과가 아니라 부품·열·배선·제어를 검증해야 하는 설계 예측임을 보여준다.
- [H7]의 연구는 PRISM 설계를 구체화하는 데도 유용하다. bipolar series port, near-zero conversion ratio, 부호 반전 구간의 순환전력/전류 스트레스가 실제 회로 문제로 다뤄져 있다.

## 3. 비교 결과에서 과장되기 쉬운 부분

### 3.1 고정된 97% DAB baseline은 최신 최적 대안이 아니다

2014 DAB review 하나를 근거로 “현행 150 kW booster는 97%, PRISM은 99.67%”라고 일반화할 수 없다. 특히 PRISM 충전 경로는 비절연이고, 기준 회로는 고주파 절연 DAB를 가정하므로 기능·제약이 다르다. 동일한 절연 요구 하에서 비절연 인터리브 boost, 3-level/flying-capacitor 방식, 상용 fixed-ratio 경로 [H8], 해당 부스터와 APM 통합 제품 [H9]도 포함해야 한다.

최소 비교군은 다음과 같다.

1. 전통적 풀전력 구조: 현재 문서의 DAB+독립 APM.
2. 실제 자동차에 적합한 비절연 조정형 구조.
3. 2:1 고정비 DCX/STC + 별도 보조전원/정전압 조정부.
4. PRISM의 주행·충전 공유 구조.

효율은 같은 입력/출력 전압, 같은 전력·온도·냉각·EMI 필터·접촉기·보조전력 경계에서 비교해야 한다. “시뮬레이션상 예상 우위”와 “하드웨어로 확인된 개선”을 표에서 구별해야 한다.

### 3.2 “8 kW = 150 kW의 5.3%”는 처리전력 비교의 유일한 지표가 아니다

충전 시 PPRC를 bypass한다면 8/150은 허브의 서로 다른 모드 정격의 비다. 주행 중 25 kW 보조부하를 조정하는 회로의 정격 비는 8/25 = 32%다. 실제 처리전력 비는 공급 방향과 결선에 따라 별도 계산해야 한다. [H6]과 [H7] 및 검토한 [8] review의 취지상 유효전력만 줄었다고 자기소자 VA·RMS·실리콘 면적이 동일 비율로 줄어드는 것은 아니다.

### 3.3 “자기소자 VA 93% 감소”는 곧 부피·원가 93% 감소가 아니다

STC는 공진 L, 고 RMS flying capacitor, 입출력 capacitor, 다수 스위치, driver, 센서, busbar를 요구한다. [H3]은 그러한 실제 구성을 포함하는 직접 비교 대상으로 적합하다. VA 산술합은 서로 다른 주파수·파형·냉각의 변압기와 공진 인덕터 부피를 공정하게 비교하는 지표가 아니다. 동일 정격으로 최적화한 실제 BOM/체적/질량/손실/냉각을 산정해야 한다.

## 4. 특허·제품 검색에서 확인한 중복 영역

특허 자료는 공개된 기술 구성을 확인하는 데 사용했다. 다음은 PRISM과 일대일 동일한 청구항을 찾았다는 판정도, 특허 유효성·침해 여부 판단도 아니다.

| 공개문헌 | 이번 검토에서 확인한 기술 내용 | 관련성 |
|---|---|---|
| [EP3046242A1](https://patents.google.com/patent/EP3046242A1/en), 2016 공개 | 차량용 양방향 DC-DC partial power; 배터리–DC link 전압 차이에 해당하는 일부 전력만 변환하고 나머지 전력은 미처리 경로로 전달하는 구성 | 차량용 양방향 부분전력이라는 넓은 개념은 이미 공개 |
| [WO2020056534A1](https://patents.google.com/patent/WO2020056534A1/en), 2020 공개 | EV 급속충전기용 transformerless PPC, floating capacitor H-bridge, 양/음 전압 주입 및 bypass 상태, interleaved 다중 채널 | bipolar 보상·bypass·interleaving의 개별 조합이 이미 존재. PRISM은 온보드이고 STC 및 절연 셀이 있어 동일 구성은 아님 |
| [US12325327B2](https://patents.google.com/patent/US12325327B2/en), 2025 공개, GM | 차량·충전에서 다른 배터리 전압을 부분전력 변환으로 공통 버스에 맞춤. 절연/비절연 구현, 양극성 출력용 스위치 및 APM/OBC 제어기 연계 설명 | EV의 절연 부분전력 전압 보상·통합 제어라는 넓은 주장 범위를 제한 |
| [WO2026053513A1](https://patents.google.com/patent/WO2026053513A1/en), 2026 공개 | 800/1600 V 대전력 RSC를 선행기술로 논의하며 interleaved 회로·결합 인덕터 등을 다룸 | 고전압 RSC 다상화/정격 반감 소자 사용에 대한 최근 특허 검색도 필요 |

공개일은 각 문헌 공개기록에 근거한다. 신규성 검토의 기준일은 PRISM의 실제 최초 공개/출원일과 함께 정해야 한다. 단순 CPC H02M3/07, B60L 키워드 몇 개 검색을 “전수 검색”이라고 표현해서는 안 된다. 적어도 직접 인용/피인용, 특허 family, 명세서 도면·독립청구항 단위 비교가 필요하다.

## 5. 저장소 참고문헌 검증표

서지 확인에는 출판사 페이지, 저자 소속기관 자료 및 출판사가 Crossref에 등록한 DOI metadata를 사용했다. “논문이 실재함”과 “그 논문이 저장소 수치/주장을 지지함”은 다른 판정이다.

| 저장소 번호 | 서지 검증 | 주장 적합성 및 수정 |
|---|---|---|
| [8] | DOI 실재. **1저자는 Niwton Gabriel Feliciani dos Santos**이며 J. R. R. Zientarski, M. L. da Silva Martins가 공저자. JESTPE 10(6), **7825–7838**, Dec. 2022 | 저장소 “J. Zientarski et al.”과 끝 페이지 7842를 수정. 유효/비유효 처리전력과 설계 범위를 다루므로 단순 유효전력만으로 소자 VA를 축소하는 주장에 오히려 주의를 요구하는 문헌. [DOI](https://doi.org/10.1109/JESTPE.2021.3082869), [Crossref](https://api.crossref.org/works/10.1109/JESTPE.2021.3082869) |
| [12] | W. Xie, W. Xi, S. Li, K. M. Smedley, X. Zhu, Y. Dai; TPEL 40(1), 1441–1456, Jan. 2025. DOI **10.1109/TPEL.2024.3463962** | 제목/저자/권호 맞음. RSCC 전압조정의 load-dependent multi-parameter DC model·손실 추정 연구. PRISM 전체 효율의 이론적 증명으로 확대 해석하지 말 것. 이번 검토에서는 서지/공개 초록 범위. [저자 소속기관 목록](https://eee.wzu.edu.cn/xiewenhao2026.pdf), [Crossref](https://api.crossref.org/works/10.1109/TPEL.2024.3463962) |
| [13] | Y. He, S. Jiang, C. Nan; APEC 2018, **91–97**; DOI 맞음 | 500 W 하드웨어 실증까지 공개. 고정비 STC+PPP 원리의 직접 선행기술이며 ISOP 결선을 구별해야 함. [Google Research](https://research.google/pubs/switched-tank-converter-based-partial-power-architecture-for-voltage-regulation-applications/), [DOI](https://doi.org/10.1109/APEC.2018.8340993) |
| [14] | 제목/7인 저자/2019/1682–1689 맞음. DOI **10.1109/APEC.2019.8722301** | EV STC+PPVR의 직접 선행기술. 공개 저자 원고상 4 kW, 200–400→1200 V, 전부하 97.71% 설계. PRISM Stage A 150 kW 99.3%+를 보장하는 데이터가 아님. [NSF 저자 원고](https://par.nsf.gov/servlets/purl/10109862), [Crossref](https://api.crossref.org/works/10.1109/APEC.2019.8722301) |
| [20] | Maury Wood, MPEL 12(2), 39–45, June 2025 맞음. DOI **10.1109/MPEL.2025.3555168** | 산업체 저자의 기술 기사. 독립적인 PRISM 검증이 아니라 경쟁 구조/고정비 APM 적용 근거. [Vicor 원문 재게시](https://edit.vicorpower.com/resource-library/articles/automotive/high-voltage-power-modules-for-ev-48v-pdns), [DOI](https://doi.org/10.1109/MPEL.2025.3555168) |
| [21a] | Kang Li et al.; *Case Studies in Thermal Engineering* **27, 101308 (2021)**. DOI **10.1016/j.csite.2021.101308** | 불완전한 “DOI 접두”를 완전 DOI로 수정. 저온 히트펌프 성능·주행거리 실험은 확인되나 PRISM에서 사용한 **2배 전기적 기동 서지, 20 ms 지속, 20–200 ms CAN 지연**의 직접 근거로 확인되지 않음. [출판사](https://www.sciencedirect.com/science/article/pii/S2214157X21004718) |
| [21b] | *Energy consumption analysis and performance evaluation of electric vehicle integrated thermal management system experiments*, Tianying Wang et al.; ATE **269, 126002 (2025)**; DOI **10.1016/j.applthermaleng.2025.126002** | 실제 실험 논문은 존재. thermal-system 에너지/운전모드 근거와 ms 기동 전류 파형 근거는 다름. [출판사](https://www.sciencedirect.com/science/article/pii/S1359431125005939) |
| [21c] | 문서 자체도 “저널판 서지 확인 필요”라고 표시하며 저자·제목·DOI가 없음 | “참고문헌 검증됨” 아래 둘 수 없음. 확인 전 삭제 또는 “설계 가정”으로 분리. 특허의 모터 연속 정격도 특정 차량의 입력 전류 서지 파형을 보증하지 않음 |
| [24] | **Lorenzo Berzi, David Delichristov, Tommaso Favilli, Marco Pierini, Matthieu Ponchant, Albi Qehajaj, Luca Pugi**, EEEIC/I&CPS Europe 2020, pp.1–6. DOI **10.1109/EEEIC/ICPSEurope49358.2020.9160762** | 소속기관 초록은 traction과 auxiliary 부하 동시 인가에 따른 storage 전력 수요를 평활화한다고 명시. 전체 원문이 없으므로 “converter 제약·worst-case window·LP가 없음”이라는 저장소 단정은 이번 검토에서 확정하지 못함. “공개 초록에는 명시되지 않음”으로 낮출 것. [Florence 기관 저장소](https://flore.unifi.it/handle/2158/1206151) |

[21]은 세 문헌/자료를 하나의 번호로 묶어 어떤 값이 어느 자료에 있는지 추적하기 어렵다. 부하별 최소한의 표를 만들어 “연속 전기입력 kW, 최대 서지 A, 지속시간, 운전조건, 제어기 ramp, 출처의 page/figure/table”을 따로 기록해야 한다. 실측 근거를 확보하기 전 SALS 사건 분포는 “실차 근거가 있는 분포”가 아니라 **저자가 구성한 stress-test 분포**로 표기하는 것이 타당하다.

## 6. 추가해야 할 핵심 문헌 목록

- **[H1]** Y. He, S. Jiang, C. Nan, APEC 2018, 91–97, [10.1109/APEC.2018.8340993](https://doi.org/10.1109/APEC.2018.8340993). [Google 저자기관 초록](https://research.google/pubs/switched-tank-converter-based-partial-power-architecture-for-voltage-regulation-applications/). 결선 설명은 공개 논문 원고의 ISOP 설명에서 확인.
- **[H2]** Z. Ni et al., APEC 2019, 1682–1689, [10.1109/APEC.2019.8722301](https://doi.org/10.1109/APEC.2019.8722301). [NSF 저자 원고](https://par.nsf.gov/servlets/purl/10109862). 이번 도구로 PDF 직접 열기는 timeout이었으나 원고 검색 색인에서 초록·회로 설명·설계 조건을 확인. 원고 전체 정밀 검토를 했다고 표현하지 않는다.
- **[H3]** Z. Ni, Y. Li, C. Liu, M. Wei, D. Cao, “A 100-kW SiC Switched Tank Converter for Transportation Electrification,” TPEL 35(6), 5770–5784, 2020, [10.1109/TPEL.2019.2954801](https://doi.org/10.1109/TPEL.2019.2954801). [IEEE 초록](https://ieeexplore.ieee.org/document/8908760/). 실제 실험 효율을 출판사 초록에서 확인.
- **[H4a]** X. Liu et al., “500 kW 3-Phase Interleaved SiC Switched Tank Converter for Transportation Electrification,” APEC 2023, [10.1109/APEC43580.2023.10131540](https://doi.org/10.1109/APEC43580.2023.10131540). 출판사 초록 확인; 숫자는 추정 성능.
- **[H4b]** X. Liu, M. Qiu, K. Hobbs, A. Dahneem, H. Meng, D. Cao, “Experimental Verification of 500kW Resonant Switched-Capacitor Converter for Electric Trucks and Electric Aircraft Application,” APEC 2024, 830–837, [10.1109/APEC48139.2024.10509275](https://doi.org/10.1109/APEC48139.2024.10509275). [APEC 공식 프로그램](https://apec-conf.org/wp-content/uploads/2024/05/APEC2024_Program_Book_Final_Web1.pdf)과 Crossref 서지 확인. 이번 검색에서 본문/실측 숫자는 1차 출판사 원문에서 직접 검증하지 못했으므로 숫자 비교에는 사용하지 않는다.
- **[H5]** Y. Li, X. Lyu, Z. Ni, D. Cao, C. Nan, S. Jiang, “Adaptive On-Time Control for High Efficiency Switched-Tank Converter,” WiPDA Asia 2018, 169–175, [10.1109/WiPDAAsia.2018.8734623](https://doi.org/10.1109/WiPDAAsia.2018.8734623). 출판사 초록에서 적응 제어·1.2 kW 실험을 확인.
- **[H6]** P. Wang, M. Chen, “Analysis and Design of Series Voltage Compensator for Differential Power Processing,” JESTPE 10(6), 7890–7903, 2022, [10.1109/JESTPE.2021.3116091](https://doi.org/10.1109/JESTPE.2021.3116091). [Princeton 기관 페이지](https://collaborate.princeton.edu/en/publications/analysis-and-design-of-series-voltage-compensator-for-differentia/).
- **[H7a]** N. Hassanpour et al., “A Series Partial Power Converter Based on Dual Active Bridge Converter for Residential Battery Energy Storage System,” RTUCON 2021, 1–6, [10.1109/RTUCON53541.2021.9711725](https://doi.org/10.1109/RTUCON53541.2021.9711725). [TalTech 서지](https://ws.lib.ttu.ee/publikatsioonid/et/Publ/Item/e6354a79-86f1-4207-9f1a-7515d6504244).
- **[H7b]** N. Hassanpour, A. Chub, A. Blinov, D. Vinnikov, “Soft-Switching Bidirectional Step-Up/Down Partial Power Converter With Reduced Components Stress,” TPEL 38(11), 14166–14177, 2023, [10.1109/TPEL.2023.3289061](https://doi.org/10.1109/TPEL.2023.3289061). [TalTech 기관 서지](https://ws.lib.ttu.ee/publikatsioonid/en/publ/item/5390d7a2-eb2e-4144-9123-7b08cad2536c), [연구진 강연 자료](https://ener.ee/wp-content/uploads/2026/01/AC3E-PPC-Slides.pdf). 후자는 4상한 PPC 구현에 four-quadrant switch 또는 series-port unfoldor가 필요함을 명시하며 전류원 구조와 DAB+unfoldor를 비교.
- **[H8]** Vicor, Seishi Tsukimoto, [Power modules provide high-efficiency conversion between 400V and 800V systems for electric vehicles](https://www.vicorpower.cn/resource-library/articles/automotive/power-modules-provide-high-efficiency-conversion). 공식 제조사 자료; product claim과 독립적인 측정 검증은 구분.
- **[H9]** Preh, [Combo Box – highly integrated power electronics](https://www.preh.com/en/products/e-mobility/combo-box/en). 공식 제조사 자료; 내부 회로 동일성은 공개되지 않음.
- **[H10]** M. Wood, MPEL 12(2), 39–45, 2025, [10.1109/MPEL.2025.3555168](https://doi.org/10.1109/MPEL.2025.3555168). [Vicor 재게시](https://edit.vicorpower.com/resource-library/articles/automotive/high-voltage-power-modules-for-ev-48v-pdns).
- **[H11]** J. D. Sathri, “Investigation of Modular CLLC DC/DC Converter using Bypass Control for Wide Output Voltage Regulation,” Virginia Tech 석사논문, 2025-04-14, [기관 원문 페이지](https://vtechworks.lib.vt.edu/items/12d41153-3b83-482c-9b54-4bb76cfb25f4). 초록까지 확인; 학술지 논문과 증거 등급을 구별.
- **[H12]** H. Chen, H. Kim, R. W. Erickson, D. Maksimović, “Electrified Automotive Powertrain Architecture Using Composite DC–DC Converters,” TPEL 32(1), 98–116, 2017, [10.1109/TPEL.2016.2533347](https://doi.org/10.1109/TPEL.2016.2533347). [Colorado 연구진 설명](https://www.colorado.edu/faculty/erickson/research/electric-vehicles). 차량용 composite power conversion과 운전주기 가중 평가의 중요한 선행기술.
- **[H13]** W. Xie et al., “A Family of Quasi-Parallel DC–DC Converter With Three-Port Resonant Switched-Capacitor Circuit,” TPEL 41(1), 640–652, 2026, [10.1109/TPEL.2025.3605488](https://doi.org/10.1109/TPEL.2025.3605488). [저자기관 목록](https://eee.wzu.edu.cn/xiewenhao2026.pdf). 제목·서지만 확인했으며 전체 구조를 PRISM과 동일하다고 주장하지 않음. 최근 후속 연구 검색에 반드시 포함.

## 7. 현재 방어 가능한 기여 표현과 검증 과제

현재 단계의 합리적인 표현:

> “기존의 고정비 공진 SC와 직렬 부분전력 조정 원리를 이용하여 800 V 차량의 충전 및 보조전원 운전 모드를 공유하는 전력 허브를 설계하고, 모드별 정격·손실·과도 제약과 부하 스케줄링의 관계를 시뮬레이션으로 검토한다.”

아직 방어하기 어려운 표현:

- “새로운/유일한 전력변환 원리”
- “고정비 STC와 PPRC를 EV에 최초 적용”
- “통합 허브 자체가 최초”
- “8 kW 셀이 150 kW를 5% 처리로 조정”
- “자기소자 부피 93% 절감”
- “99.67%를 달성했다” — 하드웨어 실측이 없으면 계산/모델 예측이라고 써야 함
- “전수 검색 결과 동일 아이디어 없음”

새 기여로 인정받으려면 다음 결과를 제시하는 것이 유효하다.

1. bipolar PPRC를 포함한 transistor-level 회로·모드별 스위치 상태와 모든 포트 전력수지.
2. 충전 bypass 때 고정비로 바뀌는 버스가 400 V 부하와 48 V 포트 사양을 동시에 만족하는 방법.
3. 같은 부품 기술·온도·EMI·절연 경계의 최신 baseline과 물리적인 BOM/열/체적 비교.
4. STC 공차 추종과 다상 interleaving/current sharing의 양립성 및 불량 센서/모듈 탈락 시 응답.
5. near-zero series voltage와 polarity reversal을 포함한 PPRC 실험 또는 검증된 switching-level model.
6. 부하 스케줄링 때문에 늘어나는 지연·서비스 품질 손실과 절감되는 정격/체적 사이의 Pareto 결과.

따라서 **유일성은 부정확한 질문이고, “어떤 좁은 기술적 차이를 새롭게 입증하는가”로 바꾸는 것이 생산적**이다. 현 단계에서는 시스템 설계 연구로 발전시킬 여지가 있으나, 선행기술 대비 개선의 수치와 완성도는 아직 검증 과제다.
