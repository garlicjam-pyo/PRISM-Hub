"""E36 정정(2026-10-29, 검증 정리의 독립 검토에서 발견): 모터 승압 대비 충전 손실 손익분기 상저항을 격자 전체로 다시 계산한다.

배경
- E25·E36의 손익분기 상저항(Rph_breakeven_best)은 "R_ph = 0에서 권선 외 손실이 가장 작은 조합"(L0 100 µH·10 kHz·n 6)
  하나에 대해서만 구했다. 그런데 상저항이 커지면 권선 리플 손실이 작은 다른 조합(L0가 큰 조합)이 더 유리해진다.
  그래서 "상저항이 이 값보다 크면 Stage A가 모터 승압보다 작다"는 문장은 격자의 다른 조합에서 성립하지 않을 수 있다.
  예: 920 V의 하한(R_ph = 5 mΩ, 633 W)은 L0 400 µH 조합의 값이고, 그 전압에서 A25R Stage A(639 W)가 더 크다.
- 여기서는 E25와 같은 손실 식(E25.motor_boost_loss)과 같은 격자(L0·f·n)로, 각 배터리 전압에서
  "모든 조합의 모터 승압 손실이 Stage A 충전 손실보다 커지는 상저항"(격자 최소 손실 = Stage A)을 구한다.
- 판정 기준을 바꾸는 시험이 아니다. E25·E36의 결론 문장 4개(e25_statements)는 그대로 두고, 문서의 상저항 문장만 고친다.

입력: E36 e25_comparison.json의 Stage A 충전 손실(A25R), 150 kHz 원 설계는 E25 결과(497 W, 전압 무관)
출력: results/E36/e25_breakeven_grid.json (근거 사본: validation/2026-10-28-a25r-impact/E36)

결과(2026-10-29 실행, E36_breakeven_grid.log)
- 격자 손익분기 상저항 640·800·920 V: A25R 3.93·4.57·5.12 mΩ, 150 kHz 원 설계(497 W) 3.45·2.75·2.24 mΩ
- 5 mΩ에서 격자 최소는 L0 400 µH·10 kHz·n 6 조합(571.5·606.7·633.3 W)
- 문서의 "가장 유리한 조합" 값(800 V A25R 3.02 mΩ, 150 kHz 1.87 mΩ)은 R_ph = 0에서 고른 한 조합의 값이라 격자 전체 값보다 작다.
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import E25_motor_boost_comparison as E25  # noqa: E402
from scipy.optimize import brentq  # noqa: E402

D = os.path.join(HERE, "..", "results", "E36")   # (2026-10-29 정리) 제출 폴더 안 결과에서 읽고 쓴다(이전에는 저장소 validation/에 썼다)
COMBOS = [dict(L0=L0, f=f, n=n) for L0, f, n in itertools.product(E25.GRID["L0"], E25.GRID["f"], E25.GRID["n"])]


def grid_min(V, rph):
    vals = [(E25.motor_boost_loss(V, Rph=rph, **c)["total"], c) for c in COMBOS]
    return min(vals, key=lambda x: x[0])


def breakeven(V, pA):
    """격자 최소 모터 승압 손실 = pA가 되는 상저항 [mΩ]. 격자 최소는 R_ph에 대해 단조 증가."""
    f = lambda r: grid_min(V, r)[0] - pA
    if f(0.0) >= 0:
        return 0.0
    return 1e3 * brentq(f, 0.0, 0.05, xtol=1e-7)


def main():
    e25 = json.load(open(os.path.join(D, "e25_comparison.json"), encoding="utf-8"))
    out = dict(note="격자 전체(L0·f·n) 최소 모터 승압 손실 = Stage A 충전 손실인 상저항. E25 손실 식 그대로",
               grid=E25.GRID, rows={})
    for key, V in (("640V", 640.), ("800V", 800.), ("920V", 920.)):
        pA = e25["charge"][key]["stageA"]
        rA = breakeven(V, pA)
        r150 = breakeven(V, 497.0)
        lo5, c5 = grid_min(V, 0.005)
        out["rows"][key] = dict(stageA_A25R_W=pA, Rph_grid_A25R_mOhm=rA, Rph_grid_150kHz_mOhm=r150,
                                grid_min_at_5mOhm_W=lo5, combo_at_5mOhm=c5,
                                best_combo_A25R=grid_min(V, rA / 1e3)[1])
        print("%s: Stage A %.1f W, 격자 손익분기 A25R %.2f mΩ, 150 kHz(497 W) %.2f mΩ, 5 mΩ 격자 최소 %.1f W %s"
              % (key, pA, rA, r150, lo5, c5))
    p = os.path.join(D, "e25_breakeven_grid.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", p)


if __name__ == "__main__":
    main()
