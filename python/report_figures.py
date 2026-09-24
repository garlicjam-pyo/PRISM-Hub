"""Figures for the final interim report (Korean labels). Reads repository evidence JSON and
report_analysis.json; re-runs only the frozen-controller traces and the SALS counterexample schedule."""
from pathlib import Path
import json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT=Path(__file__).resolve().parents[1]; FIG=ROOT/"docs"/"fig"/"report"; FIG.mkdir(parents=True,exist_ok=True)
for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc","/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    try: fm.fontManager.addfont(f)
    except Exception: pass
plt.rcParams.update({"font.family":"Noto Sans CJK JP","axes.unicode_minus":False,"font.size":9,
                     "axes.titlesize":9.5,"axes.labelsize":9,"legend.fontsize":8,"xtick.labelsize":8,"ytick.labelsize":8,
                     "savefig.dpi":220,"axes.grid":True,"grid.alpha":0.3})
C={"blue":"#1f4e79","orange":"#c55a11","green":"#548235","red":"#c00000","gray":"#7f7f7f","lblue":"#deebf7","lorange":"#fbe5d6","lgreen":"#e2f0d9","lgray":"#f2f2f2"}

def box(ax,x,y,w,h,text,fc,ec="#404040",fs=8.5,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.08",fc=fc,ec=ec,lw=1.1))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=fs,fontweight="bold" if bold else "normal",linespacing=1.25)
def arrow(ax,p1,p2,color="#404040",lw=1.4,style="-|>",ls="-",both=False,rad=0.0):
    a=FancyArrowPatch(p1,p2,arrowstyle=("<|-|>" if both else style),mutation_scale=10,color=color,lw=lw,linestyle=ls,
                      connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)

def fig1_architecture():
    fig,ax=plt.subplots(figsize=(7.2,3.9)); ax.set_xlim(0,14.4); ax.set_ylim(0,7.8); ax.axis("off")
    box(ax,0.2,3.3,1.9,1.3,"800 V 배터리\n640–920 V",C["lgray"],bold=True)
    box(ax,2.8,3.3,2.3,1.3,"Stage A\n2:1 고정비 RSC\n150 kW (4×37.5 kW)",C["lblue"])
    ax.add_patch(plt.Circle((6.0,3.95),0.16,color=C["blue"])); ax.text(6.0,3.45,"V_A 노드\n320–460 V",ha="center",va="top",fontsize=8)
    box(ax,6.8,3.3,2.2,1.3,"Stage B\n직렬 포트\n±90 V",C["lorange"])
    box(ax,9.7,3.3,2.0,1.3,"400 V\n보조버스\n(조정)",C["lgreen"],bold=True)
    box(ax,12.3,5.3,1.9,1.1,"400 V 부하\n압축기·PTC·V2L",C["lgray"],fs=7.8)
    box(ax,12.3,3.4,1.9,1.1,"Stage C\nCLLC → 48 V",C["lblue"],fs=7.8)
    box(ax,12.3,1.5,1.9,1.1,"48→12 V\n강압 → 12 V",C["lblue"],fs=7.8)
    box(ax,4.9,6.1,2.3,1.1,"400 V급 충전기\n(CC/CV, ≤150 kW, ≤375 A)",C["lgray"],fs=7.8)
    box(ax,6.8,0.7,2.2,1.2,"DAB + 100 V 링크\n(8 kW, 80 A)",C["lorange"],fs=7.8)
    box(ax,9.7,0.4,2.0,1.1,"SALS\n부하 승인 계층",C["lgreen"],fs=7.8)
    arrow(ax,(2.1,3.95),(2.8,3.95),both=True); arrow(ax,(5.1,3.95),(5.84,3.95),both=True)
    arrow(ax,(6.16,3.95),(6.8,3.95),both=True); arrow(ax,(9.0,3.95),(9.7,3.95),both=True)
    arrow(ax,(11.7,4.3),(12.3,5.8)); arrow(ax,(11.7,3.95),(12.3,3.95),both=True); arrow(ax,(13.25,3.4),(13.25,2.6))
    arrow(ax,(6.0,6.1),(6.0,4.12),color=C["red"],lw=2.0)
    arrow(ax,(10.7,3.3),(8.4,1.9),color=C["orange"],ls="--"); arrow(ax,(7.9,1.9),(7.9,3.3),color=C["orange"],ls="--")
    ax.text(10.05,2.45,"DAB 입력(버스→링크)",fontsize=7.2,color=C["orange"],rotation=0)
    ax.text(6.9,2.5,"직렬 보상",fontsize=7.2,color=C["orange"])
    arrow(ax,(10.7,1.5),(12.5,5.3),color=C["green"],ls=":",lw=1.1,rad=-0.25)
    ax.text(11.1,1.55,"승인·제한",fontsize=7.2,color=C["green"])
    ax.plot([2.8,5.1],[3.05,3.05],color=C["red"],lw=2.0); ax.text(3.95,2.7,"충전 대전류 경로\n(Stage B 비경유)",ha="center",va="top",fontsize=7.2,color=C["red"])
    fig.tight_layout(); fig.savefig(FIG/"fig1_architecture.png"); plt.close(fig)

def fig2_stage_b():
    fig,ax=plt.subplots(figsize=(7.2,2.35)); ax.set_xlim(0,14.4); ax.set_ylim(0.6,5.0); ax.axis("off")
    box(ax,0.2,2.3,2.0,1.3,"400 V\n보조버스",C["lgreen"],bold=True)
    box(ax,2.9,2.3,2.4,1.3,"절연 DAB\n4:1, 200 kHz, SPS\nL = 11.1 µH",C["lorange"],fs=7.8)
    box(ax,6.0,2.3,2.1,1.3,"부유 링크\n100 V (90–110 V)\nC = 2 mF",C["lgray"],fs=7.8)
    box(ax,8.8,2.3,2.3,1.3,"4상한 H-브리지\n변조율 ≤ 0.95\n+ LC 필터 5 µH",C["lorange"],fs=7.8)
    box(ax,11.8,2.3,2.4,1.3,"직렬 포트\nv_s = ±90 V\nC_s = 100 µF",C["lorange"],fs=7.8)
    for a,b in [((2.2,2.95),(2.9,2.95)),((5.3,2.95),(6.0,2.95)),((8.1,2.95),(8.8,2.95)),((11.1,2.95),(11.8,2.95))]: arrow(ax,a,b,both=True)
    ax.text(2.9,3.85,"DAB 입력전력(버스 측, 방향별 효율 0.96)",fontsize=7.2,color=C["orange"])
    ax.text(5.7,1.4,"링크전류 i_link ≤ 80 A\n링크전력 ≤ 8 kW",fontsize=7.2,ha="center",color=C["blue"])
    ax.text(9.95,1.4,"필터전류 i_h ≤ 100 A\n지령 i_ref 포화 84 A",fontsize=7.2,ha="center",color=C["blue"])
    ax.text(13.0,1.4,"경로전류 i_p ≤ 100 A\nC_s·dv_s/dt = i_h − i_p",fontsize=7.2,ha="center",color=C["blue"])
    ax.text(13.0,3.85,"V_A–보조버스 사이 직렬 삽입",fontsize=7.2,ha="center")
    fig.tight_layout(); fig.savefig(FIG/"fig2_stage_b.png"); plt.close(fig)

def fig3_steady(an):
    s=an["steady_25kW"]; v=[r["vbat"] for r in s]
    fig,ax=plt.subplots(1,2,figsize=(7.2,2.7))
    ax[0].plot(v,[r["series_V"] for r in s],color=C["blue"],lw=1.8,label="요구 직렬전압 v_s")
    ax[0].axhline(90,color=C["red"],ls="--",lw=1); ax[0].axhline(-90,color=C["red"],ls="--",lw=1)
    ax[0].axhline(85.3,color=C["orange"],ls=":",lw=1.2); ax[0].text(760,76,"링크 90 V일 때 상한 ≈ 85.3 V",fontsize=7,color=C["orange"]); ax[0].set_ylim(-100,100)
    ax[0].text(655,-84,"포트 한계 ±90 V",fontsize=7,color=C["red"])
    ax[0].set_xlabel("배터리 전압 (V)"); ax[0].set_ylabel("직렬전압 (V)"); ax[0].set_title("(a) 25 kW 정상상태 요구 직렬전압")
    ax[1].plot(v,[r["link_power_W"]/1e3 for r in s],color=C["orange"],lw=1.8,label="링크전력")
    ax[1].axhline(8,color=C["red"],ls="--",lw=1); ax[1].axhline(-8,color=C["red"],ls="--",lw=1)
    ax2=ax[1].twinx(); ax2.plot(v,[100*r["processed_ratio"] for r in s],color=C["green"],lw=1.2,ls="-.",label="처리 비율")
    ax2.set_ylabel("처리 비율 (%, 25 kW 대비)"); ax2.grid(False); ax2.set_ylim(0,40)
    ax[1].set_xlabel("배터리 전압 (V)"); ax[1].set_ylabel("Stage B 링크전력 (kW)"); ax[1].set_title("(b) Stage B 처리전력")
    h1,l1=ax[1].get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels(); ax[1].legend(h1+h2,l1+l2,loc="upper right")
    fig.tight_layout(); fig.savefig(FIG/"fig3_steady.png"); plt.close(fig)

def fig4_traces():
    import sys; sys.path.insert(0,str(ROOT/"python"))
    from pprc_fixed_control import run
    fig,ax=plt.subplots(1,3,figsize=(7.2,2.5))
    for v,c in [(640,C["red"]),(788,C["blue"]),(920,C["green"])]:
        r=run(float(v),1000.,25000.,duration=.003,keep_trace=True); t=(r["t"]-1e-3)*1e3; m=(t>=-0.1)&(t<=1.5)
        ax[0].plot(t[m],r["x"][m,2],color=c,lw=1.2,label=f"{v} V"); ax[1].plot(t[m],r["x"][m,0],color=c,lw=1.2); ax[2].plot(t[m],r["x"][m,4],color=c,lw=1.2)
    ax[0].axhline(392,color=C["gray"],ls="--",lw=0.8); ax[0].axhline(396,color=C["gray"],ls=":",lw=0.8); ax[1].axhline(100,color=C["red"],ls="--",lw=0.8)
    ax[0].set_ylabel("버스전압 (V)"); ax[1].set_ylabel("경로전류 i_p (A)"); ax[2].set_ylabel("링크전압 (V)")
    for a,tt in zip(ax,["(a) 400 V 보조버스","(b) 직렬 경로전류","(c) 100 V 링크"]): a.set_xlabel("스텝 후 시간 (ms)"); a.set_title(tt)
    ax[0].legend(loc="lower right"); fig.tight_layout(); fig.savefig(FIG/"fig4_traces.png"); plt.close(fig)

def fig5_corner(an):
    c=an["corner_640V"]
    items=[("경로전류",c["path"][0],c["path"][1],"A","%.1f/%.0f A"),("H-브리지 전류",c["bridge"][0],c["bridge"][1],"A","%.1f/%.0f A"),
           ("링크전류",c["link_current"][0],c["link_current"][1],"A","%.1f/%.0f A"),("DAB 링크전력",c["dab_power"][0]/1e3,c["dab_power"][1]/1e3,"kW","%.2f/%.0f kW"),
           ("변조율",c["modulation"][0],c["modulation"][1],"","%.3f/%.2f"),("직렬전압",c["series"][0],c["series"][1],"V","%.1f/%.0f V")]
    fig,ax=plt.subplots(figsize=(7.2,2.4))
    names=[i[0] for i in items]; util=[100*i[1]/i[2] for i in items]
    bars=ax.barh(names,util,color=[C["red"] if u>=95 else C["orange"] if u>=90 else C["blue"] for u in util])
    for b,(n,val,lim,unit,fmt),u in zip(bars,items,util):
        ax.text(u+0.4,b.get_y()+b.get_height()/2,(fmt%(val,lim))+f"  ({u:.1f} %)",va="center",fontsize=7.5)
    ax.axvline(100,color=C["red"],ls="--",lw=1); ax.set_xlim(80,112); ax.invert_yaxis(); ax.set_xlabel("한계 대비 사용률 (%)")
    ax.set_title("640 V, 1→25 kW 정격 내 시험의 포트별 피크/한계")
    fig.tight_layout(); fig.savefig(FIG/"fig5_corner.png"); plt.close(fig)

def fig6_delay():
    d=json.load(open(ROOT/"validation/2026-09-22-fixed-control/delay_sweep.json"))
    fig,ax=plt.subplots(1,2,figsize=(7.2,2.7))
    for v,c in [(640,C["red"]),(920,C["green"])]:
        rows=[r for r in d["cases"] if r["vbat_V"]==v]; x=[r["delay_us"] for r in rows]
        ax[0].plot(x,[r["path_peak_A"] for r in rows],"o-",color=c,ms=3,lw=1.2,label=f"{v} V 경로전류")
        ax[0].plot(x,[r["bridge_peak_A"] for r in rows],"s--",color=c,ms=2.5,lw=0.9,alpha=0.7,label=f"{v} V 브리지전류")
        ax[1].plot(x,[r["droop_V"] for r in rows],"o-",color=c,ms=3,lw=1.2,label=f"{v} V")
    ax[0].axhline(100,color="k",ls="--",lw=0.8); ax[0].set_ylim(80,180); ax[0].axvspan(6.2,6.3,color=C["orange"],alpha=0.3)
    ax[0].set_xlabel("전달지연 (µs)"); ax[0].set_ylabel("피크 전류 (A)"); ax[0].set_title("(a) 전류 피크와 100 A 한계"); ax[0].legend(fontsize=6.8,loc="upper left")
    ax[1].axhline(8,color="k",ls="--",lw=0.8); ax[1].set_yscale("log"); ax[1].set_xlabel("전달지연 (µs)"); ax[1].set_ylabel("최대 전압강하 (V, 로그)")
    ax[1].set_title("(b) 버스 전압강하"); ax[1].legend(fontsize=7)
    ax[1].annotate("7.5 µs부터\n버스 조정 상실",xy=(7.5,8.3),xytext=(5.2,40),fontsize=7,arrowprops=dict(arrowstyle="->",lw=0.8))
    fig.tight_layout(); fig.savefig(FIG/"fig6_delay.png"); plt.close(fig)

def fig7_capability(an):
    caps=[c for c in an["transient_capability_from_5kW"] if c.get("max_power1_W")]
    s=an["steady_25kW"]
    fig,ax=plt.subplots(figsize=(7.2,2.7))
    ax.plot([c["vbat"] for c in caps],[c["max_power1_W"]/1e3 for c in caps],"o-",color=C["blue"],lw=1.6,ms=4,label="과도 허용 최종전력(5 kW에서 스텝, 20 ms 판정)")
    ax.plot([r["vbat"] for r in s],[r["continuous_limit_W"]/1e3 for r in s],color=C["gray"],lw=1.4,ls="--",label="정적 연속 한계(정격 25 kW로 상한)")
    ax.axhline(29,color=C["orange"],ls=":",lw=1); ax.text(645,29.3,"기존 과부하 시험 29 kW",fontsize=7,color=C["orange"])
    ax.axvspan(640,710,color=C["lgray"],alpha=0.9,zorder=0); ax.text(645,32.6,"640–700 V: 1 ms 회복 기준이\n먼저 제한",fontsize=7)
    ax.text(722,33.3,"720–920 V: 경로전류 100 A가 먼저 제한",fontsize=7)
    ax.set_xlabel("배터리 전압 (V)"); ax.set_ylabel("보조버스 전력 (kW)"); ax.set_title("공통 고정이득 제어기의 전압 의존 과도 허용 전력")
    ax.legend(loc="lower right"); fig.tight_layout(); fig.savefig(FIG/"fig7_capability.png"); plt.close(fig)

def fig8_sals():
    import sys; sys.path.insert(0,str(ROOT/"python"))
    import sals_montecarlo as legacy
    e=dict(Vbat=800.,Imax=95.,base=14.9,t_c=.050,d_c=.020,seen_delay=.030,k_s=2.39,P_c=24.9,t_v=0.,v2l=True,sus=np.zeros(legacy.n),
           req={'PTC':(17.5,.030,1.),'BH':(17.5,.030,.7),'V48':(3.75,.030,.5)})
    names,al=legacy.schedule(e); tg=legacy.tg; nd=legacy.nondef(e,tg); t=tg*1e3
    base=np.full_like(tg,e["base"]); v2l=np.where(tg>=e["t_v"]+.005,9.0,0.0); comp=np.clip(nd-base-v2l,0,None); dfr=al.sum(axis=1)
    fig,ax=plt.subplots(figsize=(7.2,2.8))
    ax.stackplot(t,base+v2l,comp,dfr,step="post",colors=[C["lgray"],C["lorange"],C["lblue"]],
                 labels=["기본부하 + V2L (비지연)","컴프레서 (비지연, 서지 포함)","승인된 지연 가능 부하"],edgecolor="#606060",linewidth=0.4)
    ax.axhline(59.375,color=C["orange"],ls="--",lw=1.2,label="현재 정적 부하예산 59.375 A")
    ax.axhline(95,color=C["gray"],ls="-.",lw=1.0,label="이전 창 기반 스케줄러 상한 95 A")
    ax.axvspan(70,80,color=C["red"],alpha=0.12)
    for x,lab in [(50,"명령 50 ms"),(70,"서지 시작 70 ms"),(80,"SALS 관측 80 ms")]:
        ax.axvline(x,color="k",lw=0.6,ls=":"); ax.text(x+0.8,131,lab,fontsize=7,rotation=90,va="top")
    ax.annotate("122.2 A = 비지연 83.4 A\n+ 지연 가능 38.8 A",xy=(72,122),xytext=(100,112),fontsize=7.2,arrowprops=dict(arrowstyle="->",lw=0.8))
    ax.set_xlim(20,160); ax.set_ylim(0,135); ax.set_xlabel("시간 (ms)"); ax.set_ylabel("요구전류 (A, 400 V 기준)")
    ax.legend(loc="upper right",fontsize=6.8,ncol=1,bbox_to_anchor=(1.0,0.86))
    fig.tight_layout(); fig.savefig(FIG/"fig8_sals.png"); plt.close(fig)
    k=int(np.argmax(np.where((tg>=.07)&(tg<.08),nd+dfr,-1)))
    return dict(peak=float((nd+dfr)[k]),mandatory=float(nd[k]),deferrable=float(dfr[k]))

if __name__=="__main__":
    an=json.load(open(ROOT/"validation/2026-09-25-final-report/report_analysis.json"))
    fig1_architecture(); fig2_stage_b(); fig3_steady(an); fig4_traces(); fig5_corner(an); fig6_delay(); fig7_capability(an); print(fig8_sals())
    print("figures:", sorted(p.name for p in FIG.glob("*.png")))
