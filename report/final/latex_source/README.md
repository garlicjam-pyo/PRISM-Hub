# 제출용 보고서 원고

PRISM-Hub 졸업작품의 제출본 원고다(Springer Nature `sn-jnl` 양식, 한국어). 이전 판인 `../tex`(120쪽)와 `../paper`(학회 2단 6쪽)는 이력으로만 남겼으며, 2026-11-10 이후 검토에서 고친 표현이 반영되어 있지 않다.

| 폴더(같은 이름의 zip) | 내용 | 빌드 | 결과 |
|---|---|---|---|
| `PRISM-Hub_full_source/` | 상세보고서(요약, 20개 장, 부록 A 약어·용어, 부록 B 검증 근거 목록, 참고문헌 60건) | `cd PRISM-Hub_full_source/report/final/tex && latexmk -xelatex main.tex` | `main.pdf` 83쪽 |
| `PRISM-Hub_Summary_source/` | 요약보고서(참고문헌 11건) | `sh PRISM-Hub_Summary_source/make_summary.sh` | `main.pdf` 10쪽 |

- zip 두 개는 같은 이름의 폴더를 그대로 압축한 것이다. 2026-11-13 제출 전 점검에서 zip을 푼 내용이 폴더와 같고, 푼 상태에서 그대로 빌드되는 것을 확인했다(미해결 참조·인용 0, 누락 글자 0, Overfull 0, 모든 글꼴 PDF 포함).
- 필요한 것: TeX Live(XeLaTeX, latexmk, `xetexko`), Noto Serif CJK KR·Noto Sans CJK KR·DejaVu Serif·DejaVu Sans Mono 글꼴.
- `prism_sn_compat.tex`가 장(chapter)을 절 단위로 바꾸고 한국어 글꼴을 설정한다. 상세보고서의 그림 파일은 `PRISM-Hub_full_source/docs/fig/report/`에 있다.
- 저자란은 조형준(2020073063)·이아윤(2023039798), 소속 한양대학교 전기공학부다. 지도교수·목차·영문 캡션 표기(Fig., Table, Appendix, References)는 제출처 양식에 따라 확인한다.
