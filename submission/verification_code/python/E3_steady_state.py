"""[E3] 25 kW 정상상태 전력수지: Stage B가 처리하는 전력(정격 분리, 가설 H1).

■ 목적
  배터리 전압 640–920 V(10 V 간격)에서 25 kW 보조버스 부하의 평형점을 구해, Stage B가 실제로
  처리해야 하는 전력(링크전력)과 요구 직렬전압을 계산한다(보고서 6.2절, 표 6.2, 그림 3).

■ 왜 필요한가
  PRISM-Hub의 핵심 주장(H1)은 "보조버스 전력 대부분은 Stage A의 2:1 경로로 흐르고, Stage B는
  V_bat/2와 400 V의 차이만 보상하므로 작은 정격(8 kW)으로 충분하다"는 것이다. 이를 전 전압 범위의
  평형점에서 확인해야 Stage B 정격(8 kW, ±90 V, 100 A)이 정당화된다. 640 V가 가장 큰 보상을 요구하는
  설계 코너임도 여기서 드러난다.

■ 방법
  model_stage_b.equilibrium(): 버스 400 V 유지 조건에서 전력수지
      v_ref·i_p = P_load + P_DAB,in,   v_s = v_ref − V_bat/2 + R·i_p
  를 풀어 경로전류 i_p, 직렬전압 v_s, 링크전류·전력, 버스 측 DAB 전력(효율 0.96 반영)을 구한다.
  처리 비율 = |링크전력| / 25 kW.

■ 판정 기준
  25 kW 정상점에서 직렬전압 ±90 V 이내, 링크전력 8 kW 이내, 링크전류가 DAB 한계 이내(지령 여유 포함).

■ 실행   python E3_steady_state.py      (수 초)
■ 결과   results/E3/steady_25kW.json, results/E3/fig3_steady.png
■ 보고서 수치: 640 V +81.05 V·6.44 kW(25.7 %), 788 V +6.84 V·0.44 kW, 920 V −59.28 V·−3.24 kW
"""
from model_stage_b import equilibrium, steady_feasible, continuous_power_limit
from controller_reference import NOMINAL
from common import save_json, verdict, outdir
from plotstyle import korean, COLOR as C


def steady_sweep(p=NOMINAL, power=25000., voltages=None):
    rows = []
    for vbat in voltages or list(range(640, 921, 10)) + [648, 788, 907]:
        x, u = equilibrium(float(vbat), power, p)
        plink = x[4] * x[5]
        rows.append(dict(vbat=vbat, path_A=x[0], series_V=x[1], link_A=x[5], link_power_W=plink,
                         bus_side_dab_W=(plink / p.eta if plink >= 0 else plink * p.eta),   # 버스에서 본 DAB 전력
                         processed_ratio=abs(plink) / power, modulation=u[0],
                         feasible_with_reserve=steady_feasible(float(vbat), power, p, True),
                         continuous_limit_W=continuous_power_limit(float(vbat), p)))
    return sorted(rows, key=lambda r: r["vbat"])


if __name__ == "__main__":
    print("[E3] 25 kW 정상상태 전력수지")
    rows = steady_sweep()
    print("   V_bat   경로전류  직렬전압   링크전류  링크전력  버스측DAB  처리비율")
    for r in rows:
        if r["vbat"] in (640, 648, 788, 800, 907, 920):
            print(f"   {r['vbat']:4d} V  {r['path_A']:6.1f} A  {r['series_V']:+7.2f} V  {r['link_A']:6.1f} A  "
                  f"{r['link_power_W']/1e3:5.2f} kW  {r['bus_side_dab_W']/1e3:5.2f} kW  {r['processed_ratio']*100:5.1f} %")
    verdict("전 범위에서 25 kW 정상점이 포트 한계(지령 여유 포함) 이내", all(r["feasible_with_reserve"] for r in rows))
    verdict("최대 링크전력 ≤ 8 kW", max(abs(r["link_power_W"]) for r in rows) <= 8000,
            f"{max(abs(r['link_power_W']) for r in rows)/1e3:.2f} kW @ 640 V")
    save_json("E3", "steady_25kW", dict(power_W=25000., rows=rows))

    # 보고서 그림 3
    plt = korean()
    s = [r for r in rows if r["vbat"] % 10 == 0]; v = [r["vbat"] for r in s]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7))
    ax[0].plot(v, [r["series_V"] for r in s], color=C["blue"], lw=1.8)
    ax[0].axhline(90, color=C["red"], ls="--", lw=1); ax[0].axhline(-90, color=C["red"], ls="--", lw=1)
    ax[0].axhline(85.3, color=C["orange"], ls=":", lw=1.2)
    ax[0].text(760, 80, "링크 90 V일 때 상한 ≈ 85.3 V", fontsize=7, color=C["orange"], va="top"); ax[0].set_ylim(-100, 100)
    ax[0].text(655, -84, "포트 한계 ±90 V", fontsize=7, color=C["red"])
    ax[0].set_xlabel("배터리 전압 (V)"); ax[0].set_ylabel("직렬전압 (V)"); ax[0].set_title("(a) 25 kW 정상상태 요구 직렬전압")
    ax[1].plot(v, [r["link_power_W"] / 1e3 for r in s], color=C["orange"], lw=1.8, label="링크전력")
    ax[1].axhline(8, color=C["red"], ls="--", lw=1); ax[1].axhline(-8, color=C["red"], ls="--", lw=1)
    ax2 = ax[1].twinx(); ax2.plot(v, [100 * r["processed_ratio"] for r in s], color=C["green"], lw=1.2, ls="-.", label="처리 비율")
    ax2.set_ylabel("처리 비율 (%, 25 kW 대비)"); ax2.grid(False); ax2.set_ylim(0, 40)
    ax[1].set_xlabel("배터리 전압 (V)"); ax[1].set_ylabel("Stage B 링크전력 (kW)"); ax[1].set_title("(b) Stage B 처리전력")
    h1, l1 = ax[1].get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax[1].legend(h1 + h2, l1 + l2, loc="upper right")
    fig.tight_layout(); fig.savefig(outdir("E3") / "fig3_steady.png"); plt.close(fig)
