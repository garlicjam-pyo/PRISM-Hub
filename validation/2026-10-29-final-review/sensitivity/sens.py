import sys, copy
sys.path.insert(0, '/home/claude/PRISM-Hub/submission/verification_code/python')
import numpy as np
import E15_baseline_loss_rating as E15
import E36_a25r_impact as E36
import E38_review_response as E38
import E32_stage_a_25k as E32
sc, orig, _, _, _ = E38.stage_c_models()
E15.stage_c = sc
SAm = E36._SA()
def avg(s, SA=SAm, prof="drive_typ"):
    pr = E15.PROFILES[prof]
    L = np.array([[E15.path_struct(s, SA, V, P, E15.P48)["loss"] for P in E15.P400] for V in pr["V"]])
    return float(np.mean(L @ E15.W400)), L.mean(0)
K0 = dict(E15.K)
def run(tag, **kw):
    E15.K.update(K0); E15.K.update(kw)
    a1, b1 = avg("1"); a4, b4 = avg("4")
    print("%-28s ①/⑤ %6.1f  ④ %6.1f  diff %5.1f (%4.1f%%)" % (tag, a1, a4, a1-a4, 100*(a1-a4)/a1))
    return a1, a4
run("base")
run("mag x0.5", mag_ind_cu=0.00075, mag_ind_core=0.0005, mag_tr_cu=0.0015, mag_tr_core=0.001)
run("mag x2", mag_ind_cu=0.003, mag_ind_core=0.002, mag_tr_cu=0.006, mag_tr_core=0.004)
run("ctrl 0", ctrl=0.)
run("esw x0.7", esw=0.7)
E15.K.update(K0)
# per-load breakdown
a1,b1=avg("1"); a4,b4=avg("4")
print("by load P400:", E15.P400, "W:", E15.W400)
print("① by load", np.round(b1,1)); print("④ by load", np.round(b4,1))
# aux buck with phase shedding: 1 phase below 8 kW
orig_hs = E15.hs_converter
def hs_shed(kind, Vin, Vout, P, dev, f, nph, Prated, Vnom, ripple=0.3):
    if kind == "buck" and Prated == 25000. and P < 8000.:
        return orig_hs(kind, Vin, Vout, P, dev, f, 1, Prated/2, Vnom, ripple)
    return orig_hs(kind, Vin, Vout, P, dev, f, nph, Prated, Vnom, ripple)
E15.hs_converter = hs_shed
run("aux buck shed (1ph<8kW)")
E15.hs_converter = orig_hs
# Stage A fixed loss +20%: scale Stage A table P by adding 0.2*fixed per running phase approx -> scale whole light-load P
import E32_stage_a_25k as E32m
T = E36._T_spec()
fixed = 31.2124
for fac in (0.2, 0.3):
    T2 = dict(T); T2["P"] = T["P"] + fac*fixed
    SA2 = E32m.StageAs(T2, E36.I_OFF)
    a4, _ = avg("4", SA2); a1,_=avg("1")
    print("StageA fixed +%d%% per phase: ④ %.1f vs ① %.1f" % (fac*100, a4, a1))
# combined: mag x0.5 and fixed+20%
E15.K.update(K0); E15.K.update(dict(mag_ind_cu=0.00075, mag_ind_core=0.0005, mag_tr_cu=0.0015, mag_tr_core=0.001))
T2 = dict(T); T2["P"] = T["P"] + 0.2*fixed; SA2 = E32m.StageAs(T2, E36.I_OFF)
print("mag x0.5 + fixed+20%%: ④ %.1f vs ① %.1f" % (avg("4", SA2)[0], avg("1")[0]))
E15.K.update(K0)
for prof in E15.PROFILES:
    print(prof, "① %.1f ④ %.1f" % (avg("1", prof=prof)[0], avg("4", prof=prof)[0]))
