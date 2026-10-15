# 중간보고서 빌드 소스

- `content_a.py`(표지·요약·1–4장), `content_b.py`(5–7장), `content_c.py`(8–10장·부록): 보고서 본문 블록.
- 그림 경로는 저장소 루트 기준이다(기존 보고서 그림, 검증 근거 그림, Simulink 테스트벤치 결과 그림).
- 전체 빌드: `bash make.sh` → `final.docx`(LibreOffice `soffice`로 목차 쪽번호 캐시와 PDF 확인). Word는 문서를 열 때 목차 필드를 갱신한다.
