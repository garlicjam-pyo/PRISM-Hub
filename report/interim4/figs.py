"""중간보고서(10-26) 전용 그림: 개선 구조 R2의 전력 경로(V_A 클램프·위상 셰딩·조정형 Stage C 포함), H-브리지 고장 강등 순서.
실행: python3 figs.py  → docs/fig/report/fig12b_r2_architecture.png, fig13b_fault_sequence.png(10-25 보고의 fig12·fig13은 그대로 둔다)"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
import report_figures as RF                       # 같은 글꼴·색·상자 함수
from report_figures import box, arrow, C, FIG, plt


def fig12_r2_architecture():
    fig, ax = plt.subplots(figsize=(7.4, 4.3)); ax.set_xlim(0, 14.8); ax.set_ylim(0, 8.6); ax.axis("off")
    box(ax, 0.2, 3.6, 1.9, 1.3, "고전압 배터리\n640–1008 V", C["lgray"], bold=True)
    box(ax, 2.8, 3.6, 2.3, 1.3, "Stage A\n2:1 고정비 RSC\n8위상, 150 kW\n경부하 위상 셰딩", C["lblue"], fs=7.8)
    ax.add_patch(plt.Circle((6.0, 4.25), 0.16, color=C["blue"])); ax.text(6.0, 3.75, "V_A 노드\n(V_bat/2)", ha="center", va="top", fontsize=8)
    box(ax, 4.85, 6.6, 2.3, 1.1, "400·500 V급 충전기\n(≤ 375 A)", C["lgray"], fs=7.8)
    # 창 조정 모듈(점선 테두리)
    ax.add_patch(plt.Rectangle((6.55, 1.0), 3.2, 4.65, fill=False, ls="--", lw=1.0, ec=C["orange"]))
    ax.text(8.15, 6.05, "선택: 창 조정 모듈 R2-W(V_A > V_W인 팩만)", ha="center", va="center", fontsize=7.4, color=C["orange"])
    box(ax, 7.0, 3.6, 2.3, 1.3, "Stage B 직렬 포트\n음(−)의 보상\n(창 조정)", C["lorange"], fs=8)
    box(ax, 7.0, 1.3, 2.3, 1.1, "DAB 1–5 kW\n+ 링크·제동 저항", C["lorange"], fs=7.6)
    ax.plot([6.6, 9.7], [5.15, 5.15], color=C["gray"], lw=1.6)
    ax.text(8.15, 5.25, "바이패스 스위치(V_A ≤ V_W·고장 시)", ha="center", va="bottom", fontsize=7, color=C["gray"])
    box(ax, 10.3, 3.6, 2.0, 1.3, "400 V 버스\nV_A 또는 V_W\n(RC 감쇠기)", C["lgreen"], fs=8, bold=True)
    box(ax, 10.3, 6.3, 2.0, 1.1, "400 V 부하\n(분리·감발 가능)", C["lgray"], fs=7.6)
    box(ax, 12.7, 3.6, 1.9, 1.3, "조정형 Stage C\n벅 + CLLC 4.8:1\n→ 48 V, 5 kW", C["lblue"], fs=7.2)
    box(ax, 12.7, 1.4, 1.9, 1.1, "48→12 V\n강압", C["lblue"], fs=7.6)
    box(ax, 12.7, 6.3, 1.9, 1.1, "SALS·보호\n상태기계", C["lgreen"], fs=7.6)
    arrow(ax, (2.1, 4.25), (2.8, 4.25), both=True); arrow(ax, (5.1, 4.25), (5.84, 4.25), both=True)
    arrow(ax, (6.16, 4.25), (7.0, 4.25), both=True); arrow(ax, (9.3, 4.25), (10.3, 4.25), both=True)
    arrow(ax, (6.3, 4.4), (6.6, 5.15), color=C["gray"], style="-"); arrow(ax, (9.7, 5.15), (10.6, 4.9), color=C["gray"])
    arrow(ax, (6.0, 6.6), (6.0, 4.42), color=C["red"], lw=2.0)
    arrow(ax, (11.3, 4.9), (11.3, 6.3)); arrow(ax, (12.3, 4.25), (12.7, 4.25), both=True); arrow(ax, (13.65, 3.7), (13.65, 2.5))
    arrow(ax, (8.15, 2.4), (8.15, 3.6), color=C["orange"], ls="--"); arrow(ax, (10.6, 3.6), (9.3, 2.0), color=C["orange"], ls="--")
    arrow(ax, (12.7, 6.85), (12.3, 6.85), color=C["green"], ls=":", lw=1.2)
    ax.text(12.5, 7.55, "분리·감발 명령", ha="center", fontsize=7, color=C["green"])
    ax.plot([2.8, 5.1], [3.35, 3.35], color=C["red"], lw=2.0)
    ax.text(3.95, 3.0, "충전 대전류 경로\n(Stage B 비경유)", ha="center", va="top", fontsize=7.2, color=C["red"])
    # 충전 중 정지 보호: V_A 클램프(E26)
    box(ax, 4.4, 0.75, 1.75, 1.1, "V_A 클램프\n468/463 V, 1 Ω", C["lorange"], fs=7.2)
    arrow(ax, (5.95, 2.95), (5.45, 1.85), color=C["orange"])
    ax.text(5.27, 0.55, "충전 중 배터리 경로 상실 시", ha="center", va="top", fontsize=6.6, color=C["orange"])
    fig.tight_layout(); fig.savefig(FIG / "fig12b_r2_architecture.png"); plt.close(fig)


def fig13_fault_sequence():
    fig, ax = plt.subplots(figsize=(7.4, 2.5)); ax.set_xlim(0, 14.8); ax.set_ylim(0.3, 4.7); ax.axis("off")
    steps = [("① 검출\n구동기 고장 신호·\n하드웨어 비교기", C["lgray"]),
             ("② 유지\n다이오드 클램프 +\nDAB 전압비 정합", C["lorange"]),
             ("③ 분리·감발\n400 V 부하 출력\n축소(SALS)", C["lgreen"]),
             ("④ 링크 붕괴\nEPS·첨두 상한\n+ 제동 저항", C["lorange"]),
             ("⑤ 소프트 투입\n경로전류 조절\n바이패스", C["lblue"]),
             ("⑥ 강등 운전\n버스 = V_A,\n부하 되돌림", C["lgray"])]
    w, gap = 2.15, 0.33
    for k, (t, fc) in enumerate(steps):
        x = 0.15 + k * (w + gap)
        box(ax, x, 2.55, w, 2.0, t, fc, fs=8.6)
        if k:
            arrow(ax, (x - gap, 3.55), (x, 3.55))
    ax.text(7.4, 1.95, "상태 9(유지) → 10(붕괴) → 11(소프트 투입) → 12(강등). 소프트 투입이 5 ms 안에 끝나지 않으면 13(이중 고장: Stage A 협조 정지)",
            ha="center", va="center", fontsize=8)
    ax.text(7.4, 1.35, "DAB는 상태 9–11에서 1차 내부 위상천이(EPS)로 바꾸고, 링크 쪽 순시 첨두 ≤ 1.5 × 정격점이 되는 전류까지만 지령한다",
            ha="center", va="center", fontsize=8, color=C["orange"])
    ax.text(7.4, 0.75, "회로 확인: TB09(순서), TB10–TB13(EPS·데드타임 반영 첨두 표·지령 전이), TB17·TB19(실제 Stage A·조정형 Stage C)",
            ha="center", va="center", fontsize=8, color=C["gray"])
    fig.tight_layout(); fig.savefig(FIG / "fig13b_fault_sequence.png"); plt.close(fig)


if __name__ == "__main__":
    fig12_r2_architecture(); fig13_fault_sequence(); print("saved")
