"""report_prep/의 정리 문서를 노션 가져오기용 한 페이지(notion/PRISM-Hub_보고서_정리.md)로 묶는다.

- 노션의 Markdown 가져오기는 저장소 상대 링크·그림을 옮기지 못하므로, 링크는 글자만 남기고 그림 줄은 뺀다.
- 원문은 01–07 파일이다. 노션 페이지를 고칠 일이 생기면 원문을 고치고 이 스크립트를 다시 실행한다.

실행: python report_prep/tools/build_notion.py   (저장소 최상위에서, build_index.py 다음에)
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "report_prep"
OUT = BASE / "notion" / "PRISM-Hub_보고서_정리.md"

HEAD = """# PRISM-Hub 최종 보고서 작성 정리

> 2026-10-28 기준. 검증 E1–E29, 회로 TB01–TB23까지의 문서·검증 기록(GitHub `final-report` 브랜치 커밋 eae5863)을 최종 보고서 작성용으로 정리했다. 같은 내용이 링크와 함께 GitHub `report-prep` 브랜치의 `report_prep/` 폴더에 있다. 이 페이지는 그 폴더에서 자동으로 만든 것이다.

## 한눈에 보기

- **남은 일**: 검증 과제 5 부품 정격 표(11월 중순) → 과제 6 최종 보고서(11월 말). 검증 과제 1–4(게이트 방향 반전, 선행기술 검색, Stage A 4모듈, 보호–SALS 연동)는 10-27·10-28에 끝났다.
- **가설**: H1 정격 분리 충족, H2 강건 제어 충족(Stage B 모델 범위), H3 충전 중 보조버스 충족(충전전류 램프 ≥ 100 µs, 충전 전 Stage A 사전 기동), H4 부하 승인 충족(축약 모델, 보호 연동 74/74), **H5 기각**.
- **연구 주장**: Stage A 2:1 단 중심의 다기능 허브 + 팩 등급 조건부 창 조정 모듈(R2). 이점은 400 V급 보조부품을 재사용하는 조건에서만 성립한다.
- **최종 보고서에서 반드시 고칠 것**: 중간보고서 10-26판의 "같은 2:1 단을 주행 중에도 계속 쓰는 구조는 찾지 못했다"(선행 있음, docs/33) → 기여 1 문구 교체. 17장 Q2의 "방향 반전 1건이 남았다" → 해결됨.
- **10-26판 이후 새로 넣을 결과**: E27·TB21(12장), E28·TB22(11장), E29·TB23(9장), 부품 정격 표(새 14장).
- **작성 규칙**: 본문에 저장소 URL·경로를 쓰지 않는다. 생성형 AI 사용 절을 넣지 않는다. 불통과 결과를 지우지 않고 기준을 사후에 바꾸지 않는다. 통과 판정에는 모델 수준을 함께 적는다.

## 이 페이지의 구성

1. 최종 보고서 구성안 · 2. 기여·가설·정정 · 3. 핵심 수치와 출처 · 4. 불통과·한계 · 5. 남은 과제와 부품 정격 표 입력값 · 6. 그림 배치 · 7. 검증 현황표(E1–E29, TB01–TB23)
"""

PARTS = [  # (파일, 이 페이지의 절 번호, 잘라낼 시작 제목 — 이 제목부터 끝까지 뺀다)
    ("01_최종보고서_구성안.md", 1, None),
    ("04_기여_가설_정정.md", 2, None),
    ("03_핵심수치_출처.md", 3, None),
    ("05_불통과_한계_목록.md", 4, None),
    ("07_남은과제_부품정격표_입력.md", 5, None),
    ("06_그림_목록.md", 6, "## 2. 새 그림 미리 보기"),
    ("02_검증_현황표.md", 7, None),
]


def strip_links(s):
    s = re.sub(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$", "", s, flags=re.M)      # 그림 줄
    s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)                      # 링크 → 글자
    return s


def part(fname, no, cut):
    s = (BASE / fname).read_text(encoding="utf-8")
    if cut:
        s = s.split(cut)[0]
    s = strip_links(s)
    lines = s.splitlines()
    title = lines[0].lstrip("# ").strip()
    body = []
    for l in lines[1:]:
        m = re.match(r"^(#{2,5}) (.*)", l)
        if m:
            h = re.sub(r"^(\d+)\. ", lambda k: "%d.%s " % (no, k.group(1)), m.group(2)) if len(m.group(1)) == 2 else m.group(2)
            body.append("#" * (len(m.group(1)) + 1) + " " + h)
        else:
            body.append(l)
    txt = "\n".join(body).strip("\n")
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return "---\n\n## %d. %s\n\n> 원문: report_prep/%s\n\n%s\n" % (no, title, fname, txt)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    s = HEAD + "\n" + "\n".join(part(*p) for p in PARTS)
    OUT.write_text(s, encoding="utf-8")
    print("%s: %d줄" % (OUT.relative_to(ROOT).as_posix(), s.count("\n")))
