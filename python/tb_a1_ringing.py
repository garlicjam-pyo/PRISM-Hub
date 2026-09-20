"""TB-A1x: device peak voltage in the 2:1 RSC phase cell (why the 520 V limit holds, and what it depends on).
Physics (ZCS turn-off): residual current i_off in L_r (144 nH) charges the leg node capacitance C_n (~300 pF, two devices):
  V_reach = i_off*sqrt(L_r/C_n)  -> for i_off <= 17.6 A this is < V_dc (460 V): the transition is INCOMPLETE, no overshoot from L_r.
The complementary device then hard-turns-on and completes the swing (dV = V_dc - V_reach). The off device's V_ds rings through the
package/loop inductance L_pkg with its C_oss, excited by the turn-on edge of duration t_rise (gate-resistor controlled).
Peak = V_dc + overshoot(dV, t_rise, L_pkg, C_oss, R_loop). We sweep t_rise and L_pkg.
"""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
FIG="../docs/fig"; Vdc=460.; Lr=144e-9; Cn=300e-12
out={}
print("V_reach = i_off*sqrt(Lr/Cn):", {i: round(i*np.sqrt(Lr/Cn),0) for i in [2.6,6.8,17.6]}, "-> all < 460 V: no overshoot from L_r")
def ring(dV,trise,Lp,Coss,R,dt=1e-11,n=10000):
    v=0.; i=0.; vl=np.zeros(n); t=np.arange(n)*dt
    for k in range(n):
        vin=dV*min(1.0,t[k]/trise)
        di=(vin-v-R*i)/Lp; dv=i/Coss; i+=dt*di; v+=dt*dv; vl[k]=v
    return vl.max()
rows=[]
for Lp in [5e-9,10e-9,20e-9]:
    for trise in [5e-9,10e-9,20e-9,40e-9]:
        for ioff,lab in [(2.6,"0.98fr"),(6.8,"fr")]:
            dV=Vdc-ioff*np.sqrt(Lr/Cn); ov=ring(dV,trise,Lp,150e-12,0.5)-dV; pk=Vdc+ov
            rows.append((Lp*1e9,trise*1e9,lab,dV,ov,pk))
print("L_pkg[nH] t_rise[ns] case   dV[V]  overshoot[V]  V_peak[V]")
for r in rows: print("%6.0f %8.0f %8s %6.0f %8.1f %9.1f"%r)
out["rows"]=rows
# figure: peak vs t_rise for L_pkg 5/10/20 nH (case 0.98fr)
fig,ax=plt.subplots(figsize=(6.5,3.6))
for Lp in [5,10,20]:
    rs=[r for r in rows if r[0]==Lp and r[2]=="0.98fr"]; ax.plot([r[1] for r in rs],[r[5] for r in rs],"o-",label=f"L_pkg {Lp} nH")
ax.axhline(520,color="r",ls="--",label="70 % of 750 V (design limit)"); ax.axhline(600,color="orange",ls=":",label="80 %")
ax.set_xlabel("complementary turn-on edge t_rise (ns)"); ax.set_ylabel("off-device V_ds peak (V)"); ax.grid(True); ax.legend(fontsize=8)
ax.set_title("TB-A1x: turn-on-induced ringing on the off device (V_dc 460 V, ZCS residual 2.6 A)")
fig.tight_layout(); fig.savefig(f"{FIG}/tba1x_ringing.png",dpi=140); plt.close(fig)
json.dump(out,open("results/tba1x_ringing.json","w"),indent=1)
