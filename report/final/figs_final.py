"""최종 보고서 그림: 2-1 최종 구조 R2(E40 클램프·최대 켜짐 시간, C_A 2.4 mF, W460 설정, 400 V 부하 정지, Stage C 일시 정지),
9-1 보호 강등 순서(최종: Stage C 일시 정지·이중 고장 400 V 부하 정지), 6-2 최종 손실 비교(E41 공정 비교·민감도, 충전 경로).

입력: 제출 검증 코드 결과(results/E40/p5.json, results/E41/fair.json)
실행: python3 figs_final.py  → docs/fig/report/fig2_1_r2_final.png, fig9_1_fault_sequence_final.png, fig6_2_loss_final.png
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
import report_figures as RF                       # noqa: E402  같은 글꼴·색·상자 함수
from report_figures import box, arrow, C, FIG, plt   # noqa: E402

RES = ROOT / "submission" / "verification_code" / "results"


def _clamp():
    p5 = json.loads((RES / "E40" / "p5.json").read_text(encoding="utf-8"))
    s, w = p5["spec"]["selected"], p5["W460"]["selected"]
    return s, w, p5["t_on_max_ms"]


def fig2_1():
    s, w, ton = _clamp()
    fig, ax = plt.subplots(figsize=(7.4, 4.6)); ax.set_xlim(0, 14.8); ax.set_ylim(0, 9.2); ax.axis("off")
    box(ax, 0.2, 3.9, 1.9, 1.3, "고전압 배터리\n640–1008 V", C["lgray"], bold=True)
    box(ax, 2.8, 3.9, 2.3, 1.3, "Stage A(A25R)\n2:1 공진 SC, 25 kHz\n8위상 150 kW\n위상 셰딩·모듈 관리기", C["lblue"], fs=7.4)
    ax.add_patch(plt.Circle((6.0, 4.55), 0.16, color=C["blue"]))
    ax.text(6.0, 4.05, "V_A 노드\nC_A 2.4 mF", ha="center", va="top", fontsize=7.6)
    box(ax, 4.85, 7.3, 2.3, 1.1, "400·500 V급 충전기\n(≤ 375 A)", C["lgray"], fs=7.8)
    ax.add_patch(plt.Rectangle((6.55, 1.2), 3.2, 4.75, fill=False, ls="--", lw=1.0, ec=C["orange"]))
    ax.text(8.15, 6.3, "선택: 창 조정 모듈 R2-W(V_A > V_W인 팩만)", ha="center", va="center", fontsize=7.2, color=C["orange"])
    box(ax, 7.0, 3.9, 2.3, 1.3, "Stage B 직렬 포트\n음(−)의 보상\n(창 조정)", C["lorange"], fs=7.8)
    box(ax, 7.0, 1.5, 2.3, 1.1, "DAB 1–5 kW\n+ 링크·제동 저항", C["lorange"], fs=7.6)
    ax.plot([6.6, 9.7], [5.45, 5.45], color=C["gray"], lw=1.6)
    ax.text(8.15, 5.55, "바이패스 스위치(V_A ≤ V_W·고장 시)", ha="center", va="bottom", fontsize=6.8, color=C["gray"])
    box(ax, 10.3, 3.9, 2.0, 1.3, "400 V 버스\nV_A 또는 V_W\n(RC 감쇠기)", C["lgreen"], fs=7.8, bold=True)
    box(ax, 10.3, 6.6, 2.0, 1.2, "400 V 부하\n분리·감발(SALS)\n이중 고장: 3 ms 정지", C["lgray"], fs=7.0)
    box(ax, 12.7, 3.9, 1.9, 1.3, "조정형 Stage C\n벅 + CLLC 4.8:1\n→ 48 V, 5 kW", C["lblue"], fs=7.0)
    box(ax, 12.7, 1.6, 1.9, 1.1, "48→12 V\n강압", C["lblue"], fs=7.6)
    box(ax, 12.7, 6.6, 1.9, 1.2, "보호 상태기계\nStage C 일시 정지\n(붕괴·투입 중)", C["lgreen"], fs=7.0)
    arrow(ax, (2.1, 4.55), (2.8, 4.55), both=True); arrow(ax, (5.1, 4.55), (5.84, 4.55), both=True)
    arrow(ax, (6.16, 4.55), (7.0, 4.55), both=True); arrow(ax, (9.3, 4.55), (10.3, 4.55), both=True)
    arrow(ax, (6.3, 4.7), (6.6, 5.45), color=C["gray"], style="-"); arrow(ax, (9.7, 5.45), (10.6, 5.2), color=C["gray"])
    arrow(ax, (6.0, 7.3), (6.0, 4.72), color=C["red"], lw=2.0)
    arrow(ax, (11.3, 5.2), (11.3, 6.6)); arrow(ax, (12.3, 4.55), (12.7, 4.55), both=True); arrow(ax, (13.65, 3.9), (13.65, 2.7))
    arrow(ax, (8.15, 2.6), (8.15, 3.9), color=C["orange"], ls="--"); arrow(ax, (10.6, 3.9), (9.3, 2.2), color=C["orange"], ls="--")
    arrow(ax, (12.7, 7.2), (12.3, 7.2), color=C["green"], ls=":", lw=1.2)
    arrow(ax, (13.65, 6.6), (13.65, 5.2), color=C["green"], ls=":", lw=1.2)
    ax.plot([2.8, 5.1], [3.65, 3.65], color=C["red"], lw=2.0)
    ax.text(3.95, 3.3, "충전 대전류 경로\n(Stage B 비경유)", ha="center", va="top", fontsize=7.0, color=C["red"])
    txt = ("V_A 클램프: 가지 %d개 × %.1f Ω + SiC %s\n468/463 V(≤ 920 V 팩), W460 가지 %d개 × %.1f Ω·511/506 V\n최대 연속 켜짐 %.1f ms"
           % (s["n"], s["R_b"], s["switch"], w["n"], w["R_b"], ton))
    box(ax, 3.0, 0.25, 3.4, 1.55, txt, C["lorange"], fs=6.6)
    arrow(ax, (5.95, 3.25), (5.3, 1.8), color=C["orange"])
    ax.text(4.7, 2.15, "충전 중 배터리\n경로 상실 시", ha="center", va="center", fontsize=6.4, color=C["orange"])
    fig.tight_layout(); fig.savefig(FIG / "fig2_1_r2_final.png"); plt.close(fig)


def fig9_1():
    fig, ax = plt.subplots(figsize=(7.4, 2.9)); ax.set_xlim(0, 14.8); ax.set_ylim(0.0, 4.9); ax.axis("off")
    steps = [("① 검출\n구동기 고장 신호\n하드웨어 비교기", C["lgray"]),
             ("② 유지\n다이오드 클램프\nDAB 전압비 정합", C["lorange"]),
             ("③ 분리·감발\n400 V 부하(SALS)\nStage C 회생 차단", C["lgreen"]),
             ("④ 링크 붕괴\nEPS·첨두 상한·제동\nStage C 일시 정지", C["lorange"]),
             ("⑤ 소프트 투입\n전류 조절 바이패스\nStage C 일시 정지", C["lblue"]),
             ("⑥ 강등 운전\n버스 = V_A\nStage C·부하 복귀", C["lgray"])]
    w, gap = 2.15, 0.33
    for k, (t, fc) in enumerate(steps):
        x = 0.15 + k * (w + gap)
        box(ax, x, 2.75, w, 2.0, t, fc, fs=7.0)
        if k:
            arrow(ax, (x - gap, 3.75), (x, 3.75))
    ax.text(7.4, 2.2, "상태 9(유지) → 10(붕괴) → 11(소프트 투입) → 12(강등). 소프트 투입이 5 ms 안에 끝나지 않으면 13(이중 고장)",
            ha="center", va="center", fontsize=7.8)
    ax.text(7.4, 1.6, "이중 고장(13): Stage A 협조 정지 + 전용 배선 신호로 400 V 부하 3 ms 안에 0 + 제동 저항 유지(경로전류 5 ms 안에 1 A 아래)",
            ha="center", va="center", fontsize=7.8, color=C["red"])
    ax.text(7.4, 1.0, "Stage C 일시 정지: 링크 붕괴·소프트 투입 동안 4 kW/ms로 0, 최대 12.4 ms(48 V 배터리가 최대 66 J 공급)",
            ha="center", va="center", fontsize=7.8, color=C["orange"])
    ax.text(7.4, 0.4, "회로 확인: TB09–TB13(순서·EPS 첨두), TB17·TB19(실제 Stage A·조정형 Stage C), TB23(SALS 연동), TB31(일시 정지·부하 정지)",
            ha="center", va="center", fontsize=7.6, color=C["gray"])
    fig.tight_layout(); fig.savefig(FIG / "fig9_1_fault_sequence_final.png"); plt.close(fig)


def fig6_2():
    d = json.loads((RES / "E41" / "fair.json").read_text(encoding="utf-8"))
    cases = d["cases"]; fair = cases["공정 기준(F1)"]["drive_typ"]; old = cases["E38 기준(셰딩 없음)"]["drive_typ"]
    sens = [k for k in cases if k not in ("E38 기준(셰딩 없음)",)]
    lo = {s: min(cases[k]["drive_typ"][s] for k in sens) for s in ("4", "5", "6")}
    hi = {s: max(cases[k]["drive_typ"][s] for k in sens) for s in ("4", "5", "6")}
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.4), gridspec_kw=dict(width_ratios=[1.15, 1]))
    lab = {"4": "④ R2 기본형", "5": "⑤ 모터 승압\n+ 400 V 부품", "6": "⑥ 800 V\n부품"}
    col = {"4": C["orange"], "5": C["green"], "6": C["blue"]}
    xs = [0, 1, 2]
    for x, s in zip(xs, ("4", "5", "6")):
        ax[0].bar(x, fair[s], color=col[s], width=0.55)
        ax[0].errorbar(x, fair[s], yerr=[[fair[s] - lo[s]], [hi[s] - fair[s]]], color="k", capsize=4, lw=1)
        ax[0].text(x, 8, "%.1f W" % fair[s], ha="center", va="bottom", fontsize=7.6, color="white", fontweight="bold")
    ax[0].plot([1 - 0.3, 1 + 0.3], [old["5"]] * 2, color="k", ls=":", lw=1.2)
    ax[0].text(1.33, old["5"], "이전 비교\n(⑤ 셰딩 없음)\n%.1f W" % old["5"], fontsize=6.2, va="center", ha="left")
    ax[0].set_xticks(xs); ax[0].set_xticklabels([lab[s] for s in ("4", "5", "6")], fontsize=7.4)
    ax[0].set_ylabel("보조 경로 평균 손실 [W]"); ax[0].set_ylim(0, 160)
    ax[0].set_title("(a) 보조 경로(주행 대표, 공정 기준·민감도 범위)", fontsize=8.4)
    ch = d["charge"]; Vs = ("640V", "800V", "920V"); x = range(3)
    ax[1].plot(x, [ch[v]["stageA_W"] for v in Vs], "o-", color=C["orange"], label="④ Stage A")
    for f, ls in (("16", ":"), ("50", "--")):
        ax[1].plot(x, [ch[v]["booster_W"][f] for v in Vs], ls, color=C["gray"], marker="s", ms=3, label="전용 승압기 %s kHz" % f)
    ax[1].plot(x, [ch[v]["motor_base_W"] for v in Vs], "^-", color=C["green"], label="모터 승압 기준점")
    ax[1].plot(x, [ch[v]["motor_min_Rph5_W"] for v in Vs], "v:", color=C["green"], label="모터 승압 하한(5 mΩ)")
    ax[1].set_xticks(list(x)); ax[1].set_xticklabels(["640 V", "800 V", "920 V"])
    ax[1].set_ylabel("375 A 충전 경로 손실 [W]"); ax[1].set_ylim(0, 2000)
    ax[1].legend(fontsize=6.2, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    ax[1].set_title("(b) 충전 경로(375 A)", fontsize=8.4)
    fig.tight_layout(); fig.savefig(FIG / "fig6_2_loss_final.png"); plt.close(fig)


if __name__ == "__main__":
    fig6_2(); fig9_1(); fig2_1(); print("saved")
