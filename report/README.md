# 최종 중간보고서 빌드 소스

- `content1.py`–`content3.py`: 보고서 본문(블록 목록). 표·그림 캡션과 \"자료:\" 출처 줄 포함.
- `build_json.py` → `report.json`, `build_docx.js`(Node, docx 9.x) → docx.
- `toc_cache.py`, `find_pages.py`: 목차 필드에 캐시 항목과 쪽번호를 넣는다(LibreOffice 렌더 기준). Word는 문서를 열 때 목차 필드를 갱신한다.
- 전체 빌드: `report/make.sh` (LibreOffice `soffice` 필요, 없으면 `python3 build_json.py && node build_docx.js out.docx`만 실행해도 된다).
- 그림은 `python python/report_figures.py`로 먼저 생성한다(docs/fig/report/).
