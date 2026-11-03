# PRISM-Hub 최종 보고서 LaTeX 원고

800 V급 전기자동차용 통합 직류 전력 허브(PRISM-Hub) 최종 보고서의 LaTeX 원고다. 요약, 20개 장, 부록 A–C(용어, 참고문헌, 검증 근거 목록)로 되어 있다.

## 빌드

```sh
./make.sh            # = latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

- 결과는 `build/main.pdf`(약 100쪽)다. `build/`는 저장소에 올리지 않는다.
- 필요한 것: TeX Live(XeLaTeX, latexmk), `xetexko`(Debian·Ubuntu는 `texlive-lang-korean`), Noto Serif CJK KR·Noto Sans CJK KR·DejaVu Serif 글꼴.
- 그림은 저장소의 `docs/fig/report/`, `validation/`, `simulink/tb/` 아래 파일을 그대로 읽는다(`preamble.tex`의 `\repo` = `../../..`). 그래서 이 폴더만 따로 떼어 빌드할 수 없고, 저장소 전체가 있어야 한다.

## 구성

| 파일 | 내용 |
|---|---|
| `main.tex` | 문서 틀(표지, 목차, 표·그림 목차, 요약, 1–20장, 부록) |
| `preamble.tex` | 조판 설정: A4, xetexko, Noto 글꼴, longtable·booktabs 표, 장 번호를 붙인 표·그림 번호(“표 2-1”), 머리말·꼬리말, `\srcnote`(주·자료 줄) |
| `chapters/cover.tex` | 표지 |
| `chapters/ch00_summary.tex` | 요약 |
| `chapters/ch01_overview.tex` – `ch04_verification.tex` | 개요, 아키텍처, 요구사항과 판정 기준, 검증 체계 |
| `chapters/ch05_baseline.tex` – `ch16_parts.tex` | 검증 결과(기본 검증, H5, 가치 지도, 충전 중 보조버스, 보호·고장 강등, 조정형 Stage C, Stage A 경부하·모듈, 충전 중 정지·클램프, 출력용량 손실과 A25R, 최종 설계 재계산), 선행연구 대비 위치와 기여, 부품 정격 표 |
| `chapters/ch17_simulink.tex` – `ch20_conclusion.tex` | 소자 수준 회로 모델 현황, 가설 판정과 한계, 향후 계획, 결론 |
| `chapters/appA_terms.tex`, `appB_refs.tex`, `appC_evidence.tex` | 부록 A–C |

## 작성 규칙

- 수치는 최종 설계(A25R) 값을 쓰고, 150 kHz 원설계 값과 바뀐 이유는 14장 대조표에 모은다.
- 근거는 “검증 근거 E42”, “회로 모델 TB33”처럼 번호로만 적고, 번호별 내용은 부록 C에 둔다. 본문에 저장소 경로·URL을 쓰지 않는다.
- 판정 기준은 시험 전에 정한 것을 그대로 쓰고, 불통과·부정적 결과를 지우지 않는다.
- 근거 문서는 `docs/20`(최종판)과 `docs/41`–`docs/47`이다.
