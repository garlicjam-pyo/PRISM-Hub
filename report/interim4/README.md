# 중간보고서(2026-10-26) 빌드 소스

10-25 보고(`report/interim3`)의 구성에 10–13장(E22–E26, TB14–TB20)과 14–17장 갱신을 더한 판이다.

- `content_a.py`: 표지, 요약, 1–4장(변경 표, 2.6절 Stage A·Stage C 제어와 충전 중 정지 순서, 요구사항 추가)
- `content_b.py`, `content_c.py`: 5–9장(10-25 보고와 같은 내용, 장 제목·그림 경로만 갱신)
- `content_d.py`: 10–13장(조정형 Stage C·R2 통합 회로, Stage A 위상 셰딩, 충전 중 정지 협조, 선행연구 대비 위치)
- `content_e.py`: 14–17장, 부록 A–C(참고문헌 [16]–[31] 추가)
- `figs.py`: `docs/fig/report/fig12b_r2_architecture.png`(V\_A 클램프·위상 셰딩·조정형 Stage C 표기), `fig13b_fault_sequence.png`
- 빌드: `bash make.sh`(LibreOffice 필요). 결과 `final.docx`(48쪽), `final.pdf`
