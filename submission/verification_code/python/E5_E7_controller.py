"""[E5–E7] Stage B 제어기 검증: 시험 격자(E5), 지연 여유(E6), 추가 강건성(E7).

■ 목적
  보조버스 제어기가 부하 변화·부품 공차·디지털 제어 지연이 겹쳐도 전압 품질과 소자 정격을
  동시에 지키는지 확인한다(가설 H2, 보고서 4.5절·6.3절). 채택 설계(연산 지연 보상 + 감쇠비 0.95)와
  비교 설계(보상 없음, 감쇠비 0.7)를 같은 시험으로 판정해 보상의 효과를 보인다.

■ 왜 필요한가
  - 전압만 보면 통과하는 제어기가 실제 경로전류로는 정격을 넘을 수 있다 → 전류 기준(90/93.75 A) 판정
  - 모델에 넣은 지연(갱신 5 µs + 전달 5 µs) 밖의 지연(센서·게이트 드라이버·ADC, 보고서 3.5절 예산 3.0 µs)이
    실제 구현에 더해지므로, 지연 여유가 부족하면 하드웨어에서 발진할 수 있다 → 지연 여유 분석
  - 단일 변수 공차만으로는 공차가 겹친 최악 조합을 놓칠 수 있다 → 복합 공차 코너
  - Tier-1 단일 스텝이 실제 부하 계약의 최악 변화를 대표하는지 확인해야 한다 → 계약 시퀀스

■ 구성(파트)과 방법
  E5 grid        Tier-1·Tier-2 격자 552건(stage_b_tests.py 설명 참고). 20 ms, 1 ms에 스텝.
  E6 linear      표본화 선형화(linearize.py): 6개 전압 × 4개 부하(−3.2, 0, 10, 25 kW)에서
                 추가 지연 여유(0.1 µs 상향 탐색)와 스펙트럼 반경(공칭, +3.0 µs). 두 설계 모두.
  E6 delay       비선형 시뮬레이션의 추가 지연 경계: 640·920 V, Tier-1 대표 3 스텝(15→25, 25→15, 0→10 kW),
                 적분간격 0.1 µs. 선형화 결과를 비선형으로 확인한다.
  E7 corners     7개 파라미터를 동시에 ±10 %로 바꾼 2⁷ = 128개 복합 코너(640 V):
                 Tier-1 15→25 kW(추가 지연 +3.0 µs), Tier-2 1→25 kW(공칭 지연)
  E7 corners_lh5 Tier-2 실패 코너를 필터 인덕터 L_h 공차 ±5 %로 좁혀 재시험(부품 공차 할당으로 해결되는지)
  E7 sequences   부하 계약 최악 시퀀스 4종 × 3개 전압(632, 640, 920 V) × 4개 집합(공칭, L_h −10 %, L +10 %, 지연 +3.0 µs)
  figures        보고서 그림 9(보상 효과), 그림 11(640 V 포트별 사용률)

■ 판정 기준 (stage_b_tests.py)
  Tier-1: 전압 품질 6항목 + 포트 한계 + 경로·필터 전류 ≤ 90 A + 내부 진동 검사
  Tier-2: 포트 한계 + ≤ 93.75 A + 버스 384–416 V + 최종 ±4 V + 내부 진동 검사
  지연 여유: ≥ 3.0 µs (지연 예산)

■ 실행
  python E5_E7_controller.py                         보고서 전체 세트(2코어 약 40–60분)
  python E5_E7_controller.py grid delay --design reference   특정 파트·설계만
  병렬 작업 수는 환경변수 PRISM_WORKERS(기본: CPU 수)로 정한다.
■ 결과   results/E5/grid_<설계>.json, results/E6/linear.json, results/E6/delay_<설계>.json,
         results/E7/corners.json, corners_lh5.json, sequences_<설계>.json, results/E5/fig9·fig11
■ 보고서 수치(채택 설계): Tier-1 390/390(최대 86.77 A), 지연 +3.0 µs 70/70(87.62 A), Tier-2 78/78(92.70 A),
  선형화 지연 여유 최소 4.1 µs(비교 설계 1.4 µs), 비선형 경계 +4.1 통과·+4.2 실패(비교 +1.4/+1.5),
  복합 코너 Tier-1 128/128(89.08 A)·Tier-2 102/128(95.8 A), L_h ±5 % 재시험 18/26(94.3 A), 시퀀스 48/48(84.26 A)
"""
import argparse
import itertools
import time
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

from controller_reference import NOMINAL
from controller_adopted import make, K_ADOPTED, ZETA, POLES, CP
from linearize import delay_margin_ctrl, rho_ctrl
from model_stage_b import current_limit
import stage_b_tests as st
from common import save_json, load_json, verdict, workers, RESULTS, outdir

DESIGN_NAME = {"adopted": "채택 설계", "reference": "비교 설계"}


def _pool():
    return Pool(workers())


# ------------------------------------------------------------------ E5 격자
def grid_job(args):
    design, (tier, name, v, a, b, p) = args
    row = dict(tier=tier, set=name, vbat=v, p0=a, p1=b)
    row.update(st.judge(tier, st.sim(v, a, b, p, design=design)))
    return row


def part_grid(design):
    with _pool() as pool:
        rows = pool.map(grid_job, [(design, j) for j in st.grid_jobs()], chunksize=4)
    summ = {}
    for tier in (1, 2):
        for name in sorted({r["set"] for r in rows}):
            sel = [r for r in rows if r["tier"] == tier and r["set"] == name]
            summ[f"T{tier}:{name}"] = dict(total=len(sel), passed=sum(r["pass_"] for r in sel),
                                           max_path_A=max(r["path_peak"] for r in sel),
                                           max_bridge_A=max(r["bridge_peak"] for r in sel),
                                           max_droop_V=max(r["droop"] for r in sel),
                                           fails=[(r["vbat"], r["p0"], r["p1"], r["failed"]) for r in sel if not r["pass_"]])

    def agg(tier, delay):
        sel = [r for r in rows if r["tier"] == tier and (r["set"] == "delay+3.0us") == delay]
        return dict(total=len(sel), passed=sum(r["pass_"] for r in sel),
                    max_current_A=max(max(r["path_peak"], r["bridge_peak"]) for r in sel))
    overall = {"T1_no_delay": agg(1, False), "T1_delay+3.0us": agg(1, True),
               "T2_no_delay": agg(2, False), "T2_delay+3.0us": agg(2, True)}
    t2 = [r for r in rows if r["tier"] == 2 and r["set"] != "delay+3.0us"]
    overall["T2_bus_range_V"] = (min(r["vbus_min_post"] for r in t2), max(r["vbus_max_post"] for r in t2))
    dev = lambda r: max(400 - r["vbus_min_post"], r["vbus_max_post"] - 400)
    overall["max_deviation_V"] = dict(T1=max(dev(r) for r in rows if r["tier"] == 1 and r["set"] != "delay+3.0us"),
                                      T2=max(dev(r) for r in t2))
    overall["max_link_power_W_640_920V"] = max(r["dab_power_peak"] for r in rows if r["vbat"] >= 640)
    # 보고서 표 6.3(공칭 조건 대표 결과)
    table = []
    for v in (640, 700, 788, 860, 920):
        t1 = [r for r in rows if r["tier"] == 1 and r["set"] == "nominal" and r["vbat"] == v]
        t2v = [r for r in rows if r["tier"] == 2 and r["set"] == "nominal" and r["vbat"] == v]
        up = next(r for r in t2v if r["p0"] == 1000)
        table.append(dict(vbat=v, T1_max_path_A=max(r["path_peak"] for r in t1), T1_max_dev_V=max(dev(r) for r in t1),
                          T2_up_path_A=up["path_peak"], T2_max_dev_V=max(dev(r) for r in t2v), T2_up_recovery_us=up["recovery_s"] * 1e6))
    print(f"   [{DESIGN_NAME[design]}] Tier-1(지연 제외) {overall['T1_no_delay']['passed']}/{overall['T1_no_delay']['total']}, "
          f"최대 {overall['T1_no_delay']['max_current_A']:.2f} A | 지연 +3.0 µs {overall['T1_delay+3.0us']['passed']}/{overall['T1_delay+3.0us']['total']}, "
          f"최대 {overall['T1_delay+3.0us']['max_current_A']:.2f} A | Tier-2 {overall['T2_no_delay']['passed']}/{overall['T2_no_delay']['total']}, "
          f"최대 {overall['T2_no_delay']['max_current_A']:.2f} A, 버스 {overall['T2_bus_range_V'][0]:.1f}–{overall['T2_bus_range_V'][1]:.1f} V")
    print(f"   최대 편차 Tier-1 {overall['max_deviation_V']['T1']:.2f} V / Tier-2 {overall['max_deviation_V']['T2']:.2f} V, "
          f"640–920 V 링크전력 최대 {overall['max_link_power_W_640_920V']/1e3:.2f} kW")
    print("   V_bat | T1 최대 경로전류 | T1 최대 편차 | T2 경로전류(1→25) | T2 최대 편차 | T2 회복")
    for t in table:
        print(f"   {t['vbat']:4d} V | {t['T1_max_path_A']:6.1f} A | {t['T1_max_dev_V']:5.2f} V | {t['T2_up_path_A']:6.1f} A | "
              f"{t['T2_max_dev_V']:5.2f} V | {t['T2_up_recovery_us']:4.0f} µs")
    return dict(summary=summ, overall=overall, table_nominal=table, rows=rows)


# ------------------------------------------------------------------ E6 선형화 지연 여유
def lin_job(args):
    v, P, design = args
    mk = lambda vb: make(vb, design)
    dm = delay_margin_ctrl(v, P, NOMINAL, mk)
    r0, f0 = rho_ctrl(v, P, NOMINAL, mk)
    r3, f3 = rho_ctrl(v, P, replace(NOMINAL, delay=NOMINAL.delay + 3e-6), mk)
    return dict(vbat=v, power=P, design=design, delay_margin_us=dm * 1e6, rho_nominal=r0, mode_hz_nominal=f0,
                rho_plus3us=r3, mode_hz_plus3us=f3)


def part_linear(designs=("reference", "adopted")):
    js = [(v, P, d) for d in designs for v in (632., 640., 700., 788., 860., 920.) for P in (-3200., 0., 10000., 25000.)]
    with _pool() as pool:
        rows = pool.map(lin_job, js)
    mm = {d: min(r["delay_margin_us"] for r in rows if r["design"] == d) for d in designs}
    for d in designs:
        worst = min((r for r in rows if r["design"] == d), key=lambda r: r["delay_margin_us"])
        print(f"   [{DESIGN_NAME[d]}] 선형화 추가 지연 여유 최소 {mm[d]:.1f} µs "
              f"({worst['vbat']:.0f} V, {worst['power']/1e3:.1f} kW), +3.0 µs에서 최대 스펙트럼 반경 "
              f"{max(r['rho_plus3us'] for r in rows if r['design'] == d):.3f}")
        verdict(f"{DESIGN_NAME[d]} 지연 여유 ≥ 예산 3.0 µs", mm[d] >= 3.0 - 1e-9)
    return dict(rows=rows, min_margin_us=mm)


# ------------------------------------------------------------------ E6 비선형 지연 경계
DELAY_EXTRAS = {"reference": [1.0, 1.2, 1.3, 1.4, 1.5, 1.6, 2.0, 3.0],
                "adopted": [3.0, 3.5, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.5, 5.0]}


def delay_job(args):
    design, v, extra, a, b = args
    p = replace(NOMINAL, delay=round((NOMINAL.delay + extra * 1e-6) / 1e-7) * 1e-7)
    row = dict(vbat=v, added_us=extra, p0=a, p1=b)
    row.update(st.judge(1, st.sim(v, a, b, p, dt=1e-7, design=design)))
    return row


def part_delay(design):
    extras = DELAY_EXTRAS[design]
    js = [(design, v, e, a, b) for v in (640, 920) for e in extras for a, b in [(15000, 25000), (25000, 15000), (0, 10000)]]
    with _pool() as pool:
        rows = pool.map(delay_job, js)
    bound = {}
    for v in (640, 920):
        ok = [e for e in extras if all(r["pass_"] for r in rows if r["vbat"] == v and r["added_us"] == e)]
        bad = [e for e in extras if e not in ok]
        bound[str(v)] = dict(last_pass_added_us=max([e for e in ok if not bad or e < min(bad)], default=None),
                             first_fail_added_us=min(bad, default=None))
        print(f"   [{DESIGN_NAME[design]}] {v} V: 추가 지연 +{bound[str(v)]['last_pass_added_us']} µs 통과, "
              f"+{bound[str(v)]['first_fail_added_us']} µs 실패")
    return dict(boundary=bound, rows=rows)


# ------------------------------------------------------------------ E7 복합 공차 코너
def corner_p(signs, tol):
    return replace(NOMINAL, **{f: getattr(NOMINAL, f) * (1 + tol[f] * s) for f, s in zip(st.FIELDS, signs)})


def corner_job(args):
    signs, tier = args
    extra = 3e-6 if tier == 1 else 0.
    p = replace(corner_p(signs, {f: .1 for f in st.FIELDS}), delay=NOMINAL.delay + extra)
    a, b = (15000, 25000) if tier == 1 else (1000, 25000)
    row = dict(signs=signs, tier=tier, vbat=640, p0=a, p1=b, added_delay_us=extra * 1e6)
    row.update(st.judge(tier, st.sim(640., a, b, p)))
    return row


def part_corners():
    js = [(s, t) for s in itertools.product([-1, 1], repeat=7) for t in (1, 2)]
    with _pool() as pool:
        rows = pool.map(corner_job, js, chunksize=4)
    out = {}
    for t in (1, 2):
        sel = [r for r in rows if r["tier"] == t]
        w = max(sel, key=lambda r: max(r["path_peak"], r["bridge_peak"]))
        out[f"T{t}"] = dict(total=len(sel), passed=sum(r["pass_"] for r in sel), worst=w)
        print(f"   복합 코너 Tier-{t}: {out[f'T{t}']['passed']}/{len(sel)} 통과, 최대 {max(w['path_peak'], w['bridge_peak']):.2f} A "
              f"(부호 {dict(zip(st.FIELDS, w['signs']))})")
    fails = [r for r in rows if r["tier"] == 2 and not r["pass_"]]
    common = {f: sorted({r["signs"][i] for r in fails}) for i, f in enumerate(st.FIELDS)}
    print(f"   Tier-2 실패 코너의 공통 부호: {common}")
    return dict(summary=out, rows=rows)


def lh5_job(signs):
    tol = {f: (.05 if f == "Lh" else .1) for f in st.FIELDS}
    row = dict(signs=signs, tier=2, vbat=640, p0=1000, p1=25000)
    row.update(st.judge(2, st.sim(640., 1000, 25000, corner_p(signs, tol))))
    return row


def part_corners_lh5():
    prev = load_json("E7", "corners")
    fails = [tuple(r["signs"]) for r in prev["rows"] if r["tier"] == 2 and not r["pass_"]]
    with _pool() as pool:
        rows = pool.map(lh5_job, fails)
    res = dict(passed=sum(r["pass_"] for r in rows), total=len(rows), max_path_A=max(r["path_peak"] for r in rows), rows=rows)
    print(f"   L_h ±5 % 재시험: {res['passed']}/{res['total']} 통과, 최대 {res['max_path_A']:.2f} A")
    return res


# ------------------------------------------------------------------ E7 부하 계약 시퀀스
def seq_job(args):
    design, v, pname, p, fn = args
    f = st.SEQUENCES[fn]; p0 = f(0.)
    row = dict(vbat=v, set=pname, sequence=fn)
    row.update(st.judge(1, st.sim(v, p0, p0, p, power_fn=f, design=design)))
    return row


def part_sequences(design):
    sets = {"nominal": NOMINAL, "Lhx0.9": replace(NOMINAL, Lh=NOMINAL.Lh * .9), "Lx1.1": replace(NOMINAL, L=NOMINAL.L * 1.1),
            "delay+3.0us": replace(NOMINAL, delay=NOMINAL.delay + 3e-6)}
    js = [(design, v, n, p, fn) for v in (632., 640., 920.) for n, p in sets.items() for fn in st.SEQUENCES]
    with _pool() as pool:
        rows = pool.map(seq_job, js)
    res = dict(passed=sum(r["pass_"] for r in rows), total=len(rows),
               worst=max(rows, key=lambda r: max(r["path_peak"], r["bridge_peak"])), rows=rows)
    w = res["worst"]
    print(f"   [{DESIGN_NAME[design]}] 계약 시퀀스 {res['passed']}/{res['total']} 통과, 최대 {max(w['path_peak'], w['bridge_peak']):.2f} A")
    return res


# ------------------------------------------------------------------ 보고서 그림 9·11
def part_figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    lin = load_json("E6", "linear")
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.55))
    for design, col, lab in [("reference", C["gray"], "지연 보상 없음(비교 설계)"), ("adopted", C["blue"], "채택 설계")]:
        r = st.sim(640., 1000, 25000, NOMINAL, design=design); t = (r["t"] - .001) * 1e3
        ax[0].plot(t, r["x"][:, 0], color=col, lw=1.1, label=lab)
        r = st.sim(640., 15000, 25000, replace(NOMINAL, delay=NOMINAL.delay + 3e-6), design=design); t = (r["t"] - .001) * 1e3
        ax[1].plot(t, r["x"][:, 2], color=col, lw=1.0, label=lab)
    ax[0].axhline(93.75, color=C["red"], ls="--", lw=.9); ax[0].axhline(100, color=C["red"], ls=":", lw=.9)
    ax[0].text(1.95, 92.2, "Tier-2 기준 93.75 A", fontsize=7, color=C["red"], ha="right", va="top")
    ax[0].set_xlim(-.1, 2); ax[0].set_ylim(0, 105)
    ax[0].set_xlabel("스텝 후 시간 (ms)"); ax[0].set_ylabel("경로전류 (A)"); ax[0].set_title("(a) 640 V, 1→25 kW, 공칭 지연")
    ax[0].legend(loc="lower right")
    ax[1].axhline(392, color=C["red"], ls="--", lw=.9); ax[1].axhline(408, color=C["red"], ls="--", lw=.9)
    ax[1].set_xlim(-.1, 3); ax[1].set_ylim(380, 420); ax[1].set_xlabel("스텝 후 시간 (ms)"); ax[1].set_ylabel("버스 전압 (V)")
    ax[1].set_title("(b) 640 V, 15→25 kW, 지연 +3.0 µs")
    V = sorted({r["vbat"] for r in lin["rows"]})
    for design, col, lab, mk in [("reference", C["gray"], "지연 보상 없음(비교 설계)", "o"), ("adopted", C["blue"], "채택 설계", "s")]:
        dm = [min(r["delay_margin_us"] for r in lin["rows"] if r["design"] == design and r["vbat"] == v) for v in V]
        ax[2].plot(V, dm, marker=mk, ms=3.5, color=col, lw=1.1, label=lab)
    ax[2].axhline(3.0, color=C["red"], ls="--", lw=.9); ax[2].text(645, 3.1, "지연 예산 +3.0 µs", fontsize=7, color=C["red"])
    ax[2].set_ylim(0, 5); ax[2].set_xlabel("배터리 전압 (V)"); ax[2].set_ylabel("추가 지연 여유 (µs)"); ax[2].set_title("(c) 선형화 추가 지연 여유")
    ax[2].legend(loc="lower right")
    fig.tight_layout(); fig.savefig(outdir("E5") / "fig9_controller.png"); plt.close(fig)

    # 그림 11: 640 V 설계 코너(공칭)의 포트별 사용률
    res = []
    for lab, a, b in [("Tier-1 (15→25 kW)", 15000, 25000), ("Tier-2 (1→25 kW)", 1000, 25000)]:
        r = st.sim(640., a, b, NOMINAL)
        res.append((lab, [("경로전류", r["path_peak"], 100), ("브리지 필터 전류", r["bridge_peak"], 100),
                          ("DAB 링크전류", r["link_peak"], 80), ("DAB 링크전력", r["dab_power_peak"] / 1e3, 8),
                          ("변조율", r["modulation_peak"], .95), ("직렬전압", r["series_peak"], 90)]))
    names = [n for n, _, _ in res[0][1]]; y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    for k, (lab, items) in enumerate(res):
        u = [100 * v / l for _, v, l in items]
        bars = ax.barh(y + (k - .5) * .36, u, height=.34, color=[C["blue"], C["orange"]][k], label=lab)
        for i, (bb, uu) in enumerate(zip(bars, u)):
            xm = max(uu, (90, 93.75)[k]) if i < 2 else uu        # 전류 행은 판정 기준 표시선 오른쪽에 라벨
            ax.text(xm + .5, bb.get_y() + bb.get_height() / 2, f"{uu:.1f} %", va="center", fontsize=6.8)
    ax.axvline(100, color=C["red"], ls="--", lw=1)
    for yy in (0, 1):
        ax.plot([90, 90], [yy - .36, yy], color=C["blue"], lw=2); ax.plot([93.75, 93.75], [yy, yy + .36], color=C["orange"], lw=2)
    ax.text(100.5, .5, "전류 판정 기준\nTier-1 90 %\nTier-2 93.75 %", fontsize=6.5, va="center")
    ax.set_yticks(y); ax.set_yticklabels(names); ax.set_xlim(40, 110); ax.set_ylim(len(names) - .4, -.6)
    ax.set_xlabel("물리 한계 대비 사용률 (%)"); ax.set_title("640 V 설계 코너의 포트별 사용률(채택 제어기, 공칭 조건)")
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.24), ncol=2, fontsize=7)
    fig.tight_layout(); fig.savefig(outdir("E5") / "fig11_corner.png"); plt.close(fig)
    print("   → 그림: results/E5/fig9_controller.png, results/E5/fig11_corner.png")
    return None


# ------------------------------------------------------------------ 실행
CONTROLLER_INFO = dict(K_adopted=K_ADOPTED.tolist(), zeta=ZETA, poles=POLES, bus_bw_Hz=CP.bus_bw, design_point=[788, 5000],
                       prediction="1주기, [i_p, v_s, i_h], 공칭 모델, 중점법 1 µs × 5단계")
# 결과 파일 위치: 파트 → (근거 번호, 파일 이름 틀)
WHERE = {"grid": ("E5", "grid_{d}"), "delay": ("E6", "delay_{d}"), "linear": ("E6", "linear"),
         "corners": ("E7", "corners"), "corners_lh5": ("E7", "corners_lh5"), "sequences": ("E7", "sequences_{d}")}
REPORT_SET = [("grid", "adopted"), ("grid", "reference"), ("linear", None), ("delay", "adopted"), ("delay", "reference"),
              ("corners", "adopted"), ("corners_lh5", "adopted"), ("sequences", "adopted"), ("figures", None)]

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Stage B 제어기 검증(E5–E7)")
    ap.add_argument("parts", nargs="*", help="grid delay linear corners corners_lh5 sequences figures (생략 시 보고서 전체 세트)")
    ap.add_argument("--design", choices=["adopted", "reference"], default="adopted")
    args = ap.parse_args()
    todo = REPORT_SET if not args.parts else [(p, args.design) for p in args.parts]
    print("[E5–E7] Stage B 제어기 검증")
    for part, design in todo:
        t0 = time.time()
        print(f"-- {part}" + (f" ({DESIGN_NAME[design]})" if design and part not in ("linear", "figures", "corners", "corners_lh5") else ""))
        if part == "grid": res = part_grid(design)
        elif part == "delay": res = part_delay(design)
        elif part == "sequences": res = part_sequences(design)
        elif part == "linear": res = part_linear()
        elif part == "corners": res = part_corners()
        elif part == "corners_lh5": res = part_corners_lh5()
        elif part == "figures": res = part_figures()
        else: raise SystemExit(f"알 수 없는 파트: {part}")
        if res is not None:
            eid, name = WHERE[part]
            res["controller"] = CONTROLLER_INFO if (design == "adopted" or part == "linear") else dict(design="reference")
            save_json(eid, name.format(d=design), res)
        print(f"   ({time.time() - t0:.0f} s)", flush=True)
