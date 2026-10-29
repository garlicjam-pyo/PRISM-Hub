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

> 2026-10-29 기준(검증 정리·외부 검토 대응 반영). 검증 E1–E38, 회로 TB01–TB31까지의 문서·검증 기록을 최종 보고서 작성용으로 정리했다. 같은 내용이 링크와 함께 GitHub `report-prep` 브랜치의 `report_prep/` 폴더에 있다. 이 페이지는 그 폴더에서 자동으로 만든 것이다. 최종 설계와 결론의 원문은 docs/20 요약·0절(최종판)이다.

## 한눈에 보기

- **최종 구조**: R2. Stage A(2:1 공진 SC, 4모듈 8위상)가 충전 호환·400 V 중간버스·48 V 단의 공급원을 함께 맡고, 48 V는 조정형 Stage C, Stage B는 V\\_A가 400 V급 부품 상한을 넘는 팩에만 붙이는 1–5 kW 창 조정 모듈. **Stage A 최종 설계 A25R**(25 kHz, C\\_A 2.4 mF, V\\_A 클램프 가지 2개 × 1.6 Ω + SiC, 224·240s 511/506 V).
- **가설**: H1·H2·H4 충족, H3 충족(조건: 충전 전 사전 기동·충전전류 램프 ≥ 600 µs), **H5 기각**(A25R로 다시 계산해도 같음).
- **핵심 수치(최종, E38)**: ④ 보조 101.5 W(⑤ 모터 승압보다 12 % 작고 ⑥ 800 V 부품보다 19 W 큼), 375 A 충전(입력 120–172.5 kW) 0.52–0.64 kW(920 V는 모터 승압 하한보다 6 W 큼). 10-26판의 85.0 W·0.50 kW·26 %·클램프 1 Ω·램프 100 µs는 150 kHz 값이라 바꾼다(2절 2.2).
- **남은 불통과 없음(E38)**: 바이패스 소프트 투입은 Stage C 일시 정지, 이중 고장 경로전류는 400 V 부하 정지 3 ms로 통과(회로 TB31 2/2). 이 둘은 새 인터페이스 요구다. 외부 검토 지적 6곳은 모두 재현했고 대응했다(docs/43).
- **새로 넣을 장**: 13 Stage A 출력용량 손실과 설계 수정(E31–E35), 14 최종 설계로 다시 계산한 결론(E36), 16 부품 정격 표(E34·E37·E38). 기여 1은 docs/33 5절의 E38 반영 문구.
- **작성 규칙**: 본문에 저장소 URL·경로를 쓰지 않는다. 생성형 AI 사용 절을 넣지 않는다. 불통과 결과를 지우지 않고 기준을 사후에 바꾸지 않는다. 통과 판정에는 모델 수준을 함께 적는다.

## 이 페이지의 구성

1. 최종 보고서 구성안 · 2. 기여·가설·정정 · 3. 핵심 수치와 출처 · 4. 불통과·한계 · 5. 남은 과제와 부품 정격 표 · 6. 그림 배치 · 7. 검증 현황표(E1–E38, TB01–TB31)
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
