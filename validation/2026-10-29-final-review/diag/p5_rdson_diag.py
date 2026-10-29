"""진단(판정 아님): P5 클램프 스위치 CAB530M12BM3의 온도가 R_DS(on) 배율에 얼마나 민감한지(최종 검토 A1, docs/45).

E39 근거 파일(spec.json, hv.json)의 변형별 최악 사건 손실(P, E_on, E_off, E_cond)을 그대로 쓰고, 도통 에너지만 배율 k로 키운다.
열은 E39 규칙(케이스 100 °C + R_thJC 0.065 × 1.2 = 0.078 K/W)이다. 최악 조합·사건을 고정한 근사다(배율을 바꾸면 최악 사건이 바뀔 수 있다).
k: 1.0(E39), 1.2(E39가 값 하나뿐인 열저항에 쓴 배율), 1.33(데이터시트 25 °C 최대/전형 = 3.55/2.67).
실행: python p5_rdson_diag.py  (저장소 최상위 기준 경로를 씀) → p5_rdson_diag.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
E39 = ROOT / "validation" / "2026-10-29-clamp-switch" / "E39"
RTH = 0.065 * 1.2
T_C = 100.
out = []
for part in ("spec", "hv"):
    d = json.load(open(E39 / f"{part}.json", encoding="utf-8"))
    for r in d["rows"]:
        if not r["C1"]:
            continue
        w = r["switches"]["CAB530M12BM3"]["worst"]
        if not w:
            continue
        tot = w["E_on"] + w["E_off"] + w["E_cond"]
        row = dict(part=part, n=r["n"], R_b=r["R_b"], off=r["off"], combo=w["combo"], kind=w["kind"],
                   cond_share=w["E_cond"] / tot, i_branch_max=r["i_branch_max"], T={})
        for k in (1.0, 1.116, 1.167, 1.2, 1.33):
            P = w["P"] * (w["E_on"] + w["E_off"] + k * w["E_cond"]) / tot
            row["T"]["%.3f" % k] = T_C + P * RTH
        # 통과에 필요한 최대 배율
        row["k_limit"] = ((150. - T_C) / RTH / w["P"] * tot - w["E_on"] - w["E_off"]) / w["E_cond"]
        out.append(row)
        print("%-4s n %d R_b %.1f 끔 %.0f: 도통 몫 %.2f, T(k=1/1.2/1.33) %.1f/%.1f/%.1f °C, 통과 한계 k %.3f"
              % (part, row["n"], row["R_b"], row["off"], row["cond_share"], row["T"]["1.000"], row["T"]["1.200"],
                 row["T"]["1.330"], row["k_limit"]))
json.dump(out, open(Path(__file__).with_suffix(".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
