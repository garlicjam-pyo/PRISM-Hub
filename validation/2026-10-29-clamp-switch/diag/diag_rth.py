"""진단(판정 아님): 재검토 P1 재현 — 최대 열저항, 가지 저항 불균형."""
import sys, json, copy
sys.path.insert(0, "/home/claude/PRISM-Hub/submission/verification_code/python")
from multiprocessing import Pool
import E38_review_response as E
B = "/home/claude/PRISM-Hub/validation/2026-10-29-review-response/E38/"
c = json.load(open(B + "clamp.json")); hv = json.load(open(B + "hv.json"))
sws = E.switches()
# 최대 열저항 판(데이터시트에 최대값이 있으면 최대값)
import glob
ds = {}
for p in glob.glob(str(E.E34.DS_DIR / "E37_sic_*.json")):
    d = json.load(open(p)); ds[d["part"]] = d["mosfet"]
def with_max(sw, name):
    s = copy.deepcopy(sw); m = ds.get(name, {})
    if m.get("R_thJC_max_KperW"):
        s["therm"] = [(E.E34.T_C_SEMI, m["R_thJC_max_KperW"])]
    return s
def T_of(rows, sw):
    t = E.thermal(rows, sw); return t.get("T")
out = {}
for key, raw, label in (("2_1.6_463", c["raw"], "spec 2x1.6"),):
    rmax, rmin = raw[key + "_max"], raw[key + "_min"]
    for sn, sw in sws.items():
        out.setdefault(label, {})[sn] = dict(T_typ=max(T_of(rmax, sw), T_of(rmin, sw)), T_maxRth=max(T_of(rmax, with_max(sw, sn)), T_of(rmin, with_max(sw, sn))), T_lim=sw["T_max"])
print(json.dumps(out, indent=1))
print(hv.keys(), hv["W460"].keys())

# ---- 가지 저항 불균형(한 가지 작은 저항, 다른 가지 큰 저항) ----
def mixed(n_b, Rb, on, off, events):
    cr = E.corners(2, Rb); R1, R2 = cr["min"]["R"], cr["max"]["R"]
    Req = R1 * R2 / (R1 + R2); f = R2 / (R1 + R2)          # 작은 저항 가지의 전류 몫(스위치 강하 0으로 근사)
    jobs = [(1, Req, 0., on, off, e) for e in events]
    with Pool(8) as p:
        rows = p.map(E._ev, jobs)
    br = []
    for r in rows:
        r = dict(r); r["S_on"] *= f; r["S_off"] *= f; r["S_i"] *= f; r["S_i2"] *= f * f; r["i_max"] *= f; r["E_branch_J"] *= f
        br.append(r)
    res = dict(R1=R1, R2=R2, f=f, C1=max(max(r["vA_max"], r["vb_max"]) for r in rows), i_branch_max=max(r["i_max"] for r in br),
               E_branch_max=max(r["E_branch_J"] for r in br), sw={})
    for sn, sw in sws.items():
        res["sw"][sn] = dict(T_typ=T_of(br, sw), T_maxRth=T_of(br, with_max(sw, sn)), T_lim=sw["T_max"])
    return res
if __name__ == "__main__":
    import E26_charging_stop as E26
    evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
    m = mixed(2, 1.6, 468., 463., evs)
    print("spec 2x1.6 mixed:", json.dumps(m, indent=1))
    w = hv["W460"]; evw = w["events"]
    print(type(evw), (evw[0] if isinstance(evw, list) else list(evw)[:3]))
    mw = mixed(2, 1.8, w["on"], w["off"], evw)
    print("W460 2x1.8 mixed:", json.dumps(mw, indent=1))
    rw = json.load(open(B + "hv.json"))["W460"]
    json.dump(dict(spec_mixed=m, w460_mixed=mw), open("/tmp/claude-0/-home-claude/da9402e8-2184-5116-b738-273f79e82c5b/scratchpad/rev3/diag_rth.json", "w"), indent=1)
