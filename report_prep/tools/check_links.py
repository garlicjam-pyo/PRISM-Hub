"""report_prep/ 아래 마크다운의 상대 링크·그림이 실제 파일을 가리키는지 확인한다.

실행: python report_prep/tools/check_links.py   (저장소 최상위에서)
깨진 링크가 있으면 목록을 출력하고 종료 코드 1을 돌려준다.
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "report_prep"
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")


def main():
    bad, n = [], 0
    for md in sorted(BASE.rglob("*.md")):
        for k, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for m in LINK.finditer(line):
                t = m.group(1)
                if t.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                n += 1
                p = (md.parent / unquote(t.split("#")[0])).resolve()
                if not p.exists():
                    bad.append("%s:%d  %s" % (md.relative_to(ROOT).as_posix(), k, t))
    print("링크 %d개 확인, 깨진 링크 %d개" % (n, len(bad)))
    for b in bad:
        print("  " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
