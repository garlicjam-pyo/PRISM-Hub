"""E36 정정: E18 가치 지도의 인덕터 저장에너지에 A25R 공진 인덕턴스를 넣어 다시 계산한다.

실행 경과(2026-10-29, 검증 정리 중 발견)
- E36 L3(E18 가치 지도, A25R 표)는 손실·성립·정격을 A25R Stage A 표로 계산했다.
  그러나 E18.magnetics()의 Stage A 공진 인덕터 저장에너지는 L_r을 상수 144 nH(150 kHz 설계)로
  고정해 두었고, E36에서 이 상수를 바꾸지 않았다. 그래서 e18_A25R_value_map.json의
  "Stage A 공진 L(8위상)" 항목(3.15–3.18 mJ)은 A25R(L_r 864.6 nH)의 값이 아니다.
- 저장에너지 규칙은 E18과 같다: 8위상 × 0.5 × L_r × I_pk², I_pk는 충전 격자 위상 첨두의 최대값.
  L_r에 비례하므로, 같은 I_pk에서 864.6/144 배로 다시 계산한다.
- 이 항목은 어떤 판정에도 쓰이지 않는다(가치 지도의 최선 구조는 보조 경로 손실로 고른다).
  문서 docs/23의 저장에너지 수치와 비율 문장만 바뀐다.

입력: validation/2026-10-28-a25r-impact/E36/e18_A25R_value_map.json
출력: validation/2026-10-28-a25r-impact/E36/e18_A25R_magnetics_fix.json

결과(2026-10-29 실행)
- Stage A 공진 L(8위상): 3.15–3.18 mJ → 18.91–19.09 mJ(팩별)
- 사양 팩 합계: ① 3,929 mJ(그대로), ② 226 → 242 mJ, ③ 33 → 49 mJ, R2-W410 44 → 60 mJ, ④ 18 → 34 mJ
- 팩 전체: ③·R2-W·④ 31.9–62.3 mJ(150 kHz 값 16–47 mJ), ② 216–380 mJ(150 kHz 값 200–365 mJ)
- 비율: Stage A 공진 L 18.9 mJ는 150 kW 충전 승압기(3.3 J)의 약 1/175(150 kHz 값 약 1/1000),
  사양 팩 R2-W410 합계는 ①의 약 1/66(150 kHz 값 약 1/90)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D = os.path.join(ROOT, "validation", "2026-10-28-a25r-impact", "E36")
KEY = "Stage A 공진 L(8위상)"
L_OLD = 144e-9      # E18.magnetics() 상수
L_NEW = 864.6e-9    # A25R


def main():
    src = json.load(open(os.path.join(D, "e18_A25R_value_map.json"), encoding="utf-8"))
    out = dict(rule="8 x 0.5 x L_r x I_pk^2 (E18.magnetics와 같음), L_r 144 nH -> 864.6 nH",
               scale=L_NEW / L_OLD, packs={})
    for pk, pv in src["packs"].items():
        row = {}
        for s, sv in pv["structs"].items():
            m = sv.get("magnetics")
            if not m:
                continue
            parts = dict(m["parts_mJ"])
            old_tot = m["total_mJ"]
            if KEY in parts:
                old = parts[KEY]
                new = old * L_NEW / L_OLD
                parts[KEY] = round(new, 2)
                new_tot = old_tot - old + new
            else:
                new_tot = old_tot
            row[s] = dict(total_old_mJ=round(old_tot, 2), total_new_mJ=round(new_tot, 2), parts_new_mJ=parts)
        out["packs"][pk] = row
    p = os.path.join(D, "e18_A25R_magnetics_fix.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for pk, row in out["packs"].items():
        print(pk, {s: (v["total_old_mJ"], v["total_new_mJ"]) for s, v in row.items()})
    print("saved", p)


if __name__ == "__main__":
    main()
