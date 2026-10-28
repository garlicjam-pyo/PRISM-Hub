"""보고서 정리 브랜치의 검증 현황표(02_검증_현황표.md)와 그림 전체 목록(06_그림_목록.md의 부록)을 저장소에서 다시 만든다.

- 검증 시험(E1–E29, 선행기술 검색): docs/20 6절 "검증 결과 이력" 표의 행을 그대로 옮기고, 시험 번호마다 근거 문서·근거 폴더를 붙인다.
  결과·판정 문구는 docs/20의 것을 바꾸지 않는다(수치의 출처를 하나로 두기 위해).
- 회로 테스트벤치(TB01–TB23): simulink/README.md의 "테스트벤치 진행 상태" 표에서 이름·상태를 옮기고 근거 문서를 붙인다.
- 그림: validation/ 아래 PNG와 simulink/tb/*/results/ 아래 응답 그림(*_response.png, *_waveforms.png)을 폴더별로 모은다.

실행: python report_prep/tools/build_index.py   (저장소 최상위에서)
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "report_prep"

# 시험 번호 → (근거 문서, 근거 폴더). E1–E10은 1차 중간보고서(9월) 부록 C가 근거다.
E_SRC = {
    "E1": ("docs/12, docs/13(1차 중간보고서 부록 C)", "validation/2026-09-22"),
    "E2": ("docs/12, docs/13", "validation/2026-09-22"),
    "E3": ("docs/14", "validation/2026-09-28-requirements"),
    "E4": ("docs/14", "validation/2026-09-28-requirements"),
    "E5–E7": ("docs/15", "validation/2026-09-29-controller"),
    "E8": ("docs/14", "validation/2026-09-28-requirements"),
    "E9": ("docs/12, docs/13", "validation/2026-09-25-final-report"),
    "E10": ("docs/12, docs/13", "validation/2026-09-25-final-report"),
    "E11": ("docs/16", "validation/2026-10-11-matlab-switching"),
    "E12": ("docs/16", "validation/2026-10-11-matlab-switching"),
    "E13": ("docs/17", "validation/2026-10-12-baseline-structures"),
    "E14": ("docs/18", "validation/2026-10-12-protection-startup"),
    "E15": ("docs/21", "validation/2026-10-22-baseline-loss-rating"),
    "E16": ("docs/22", "validation/2026-10-22-charging-integration"),
    "E17": ("docs/24", "validation/2026-10-24-protection-r2"),
    "E18": ("docs/23", "validation/2026-10-22-industry-value-r2"),
    "E19": ("docs/23", "validation/2026-10-22-industry-value-r2"),
    "E20": ("docs/25", "validation/2026-10-24-dab-fault-modulation"),
    "E21": ("docs/26", "validation/2026-10-25-dab-switching-margin"),
    "E22": ("docs/27", "validation/2026-10-25-stage-c-regulated"),
    "E23": ("docs/28", "validation/2026-10-25-r2-integrated"),
    "E24": ("docs/29", "validation/2026-10-26-stage-a-shedding"),
    "E25": ("docs/30", "validation/2026-10-26-positioning"),
    "E26": ("docs/31", "validation/2026-10-26-charging-stop"),
    "E27": ("docs/32", "validation/2026-10-27-zcp-reversal"),
    "E28": ("docs/34", "validation/2026-10-28-stage-a-modules"),
    "E29": ("docs/35", "validation/2026-10-28-sals-link"),
    "TB08": ("docs/23", "simulink/tb/TB08_R2_WindowModule"),
    "선행기술": ("docs/33", "—"),
}
TB_DOC = {"TB01": "docs/19", "TB02": "docs/19", "TB03": "docs/19", "TB04": "docs/19", "TB04B": "docs/19", "TB05": "docs/19",
          "TB06": "docs/19", "TB07": "docs/22", "TB08": "docs/23", "TB09": "docs/24", "TB10": "docs/25", "TB11": "docs/26",
          "TB12": "docs/26", "TB13": "docs/26", "TB14": "docs/27", "TB15": "docs/27", "TB16": "docs/28", "TB17": "docs/28",
          "TB18": "docs/29", "TB19": "docs/29", "TB20": "docs/31", "TB21": "docs/32", "TB22": "docs/34", "TB23": "docs/35"}
DOC_FILES = {p.name[:2]: p.name for p in (ROOT / "docs").glob("[0-9][0-9]_*")}


def cells(line):
    """표 한 줄을 칸으로 나눈다. 칸 안의 이스케이프된 세로줄(\\|)은 나누지 않는다."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def doc_link(ref):
    """'docs/24' → 상대 링크(report_prep에서 본 경로). 여러 개면 각각."""
    out = []
    for m in re.finditer(r"docs/(\d\d)", ref):
        f = DOC_FILES.get(m.group(1))
        out.append("[docs/%s](../docs/%s)" % (m.group(1), f) if f else "docs/" + m.group(1))
    rest = re.sub(r"docs/\d\d(, )?", "", ref).strip()
    return ", ".join(out) + (" " + rest if rest else "")


def folder_link(p):
    if p == "—":
        return "—"
    return "[%s](../%s)" % (p.split("/")[-1], p)


def e_rows():
    lines = (ROOT / "docs" / "20_종합보고서_아키텍처_설계검증.md").read_text(encoding="utf-8").splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("## 6. 검증 결과 이력"))
    rows = []
    for l in lines[i:]:
        if l.startswith("## 7."):
            break
        if not l.startswith("| 20"):
            continue
        cols = cells(l)
        date, test, purpose, result, verdict = cols[:5]
        m = re.match(r"(E\d+(?:–E\d+)?|TB08|선행기술)", test)
        key = m.group(1) if m else test
        rows.append(dict(date=date, test=test, key=key, verdict=verdict, result=result))
    return rows


def tb_rows():
    lines = (ROOT / "simulink" / "README.md").read_text(encoding="utf-8").splitlines()
    rows = []
    for l in lines:
        m = re.match(r"\| \[(TB\w+)\]\((tb/[^)]+)\) \| (.*)", l)
        if not m:
            continue
        cols = cells(l)
        rows.append(dict(tb=m.group(1), path="simulink/" + m.group(2).replace("/README.md", ""), what=cols[1], ref=cols[2], state=cols[-1]))
    return rows


def short(s, n=150):
    s = re.sub(r"\s+", " ", s)
    return s if len(s) <= n else s[:n].rstrip() + "…"


def build_status():
    er = e_rows(); tr = tb_rows()
    out = ["# 검증 현황표(자동 생성)", "",
           "> `report_prep/tools/build_index.py`가 docs/20 6절과 simulink/README.md에서 만든다. 결과·판정 문구는 원문 그대로다(수치를 고칠 때는 원문을 고치고 다시 생성).",
           "> 시험 이름의 상세 결과는 원문 표(docs/20 6절)에 있다. 여기서는 판정과 근거 위치를 한눈에 보도록 줄였다.", "",
           "## 1. 검증 시험(E1–E29)", "",
           "| 날짜 | 시험 | 판정(docs/20 원문) | 근거 문서 | 근거 폴더 |", "|---|---|---|---|---|"]
    for r in er:
        src = E_SRC.get(r["key"], ("", "—"))
        out.append("| %s | %s | %s | %s | %s |" % (r["date"], r["test"], r["verdict"], doc_link(src[0]) if src[0] else "—", folder_link(src[1])))
    out += ["", "## 2. 회로 테스트벤치(TB01–TB23)", "",
            "| TB | 내용(요약) | 기준 | 상태(simulink/README 원문 요약) | 근거 문서 |", "|---|---|---|---|---|"]
    for r in tr:
        out.append("| [%s](../%s/README.md) | %s | %s | %s | %s |" % (r["tb"], r["path"], short(r["what"], 110), short(r["ref"], 70),
                                                              short(r["state"], 200), doc_link(TB_DOC.get(r["tb"], ""))))
    out += ["", "## 3. 시험 수", "", "- 검증 시험 행: %d개(docs/20 6절)" % len(er), "- 회로 테스트벤치: %d개(simulink/README)" % len(tr), ""]
    (OUT / "02_검증_현황표.md").write_text("\n".join(out), encoding="utf-8")
    return len(er), len(tr)


def build_fig_list():
    out = ["", "## 부록. 저장소의 그림 전체 목록(자동 생성)", "",
           "검증 코드 그림(validation)과 회로 응답 그림(simulink/tb/*/results의 *_response.png, *_waveforms.png)이다.", ""]
    for d in sorted((ROOT / "validation").iterdir()):
        figs = sorted(d.rglob("*.png"))
        if figs:
            out.append("- **%s**: " % d.name + ", ".join("[%s](../%s)" % (f.name, f.relative_to(ROOT).as_posix()) for f in figs))
    for d in sorted((ROOT / "simulink" / "tb").iterdir()):
        figs = sorted([f for f in (d / "results").glob("*.png") if re.search(r"_(response|waveforms)\.png$", f.name)]) if (d / "results").exists() else []
        if figs:
            out.append("- **%s**: " % d.name + ", ".join("[%s](../%s)" % (f.name, f.relative_to(ROOT).as_posix()) for f in figs))
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    ne, nt = build_status()
    f = OUT / "06_그림_목록.md"
    s = f.read_text(encoding="utf-8")
    s = s.split("\n## 부록. 저장소의 그림 전체 목록(자동 생성)")[0].rstrip("\n") + "\n" + build_fig_list()
    f.write_text(s, encoding="utf-8")
    print("검증 시험 %d행, 테스트벤치 %d개, 그림 목록 갱신" % (ne, nt))
