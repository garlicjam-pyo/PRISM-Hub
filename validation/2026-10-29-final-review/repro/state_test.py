"""Reviewer checks: (1) two original E26 events vs stored event_summary; (2) in-process state/order dependence of E26/E38/E39."""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "verification_code" / "python"))
import E26_charging_stop as E26  # noqa: E402

KEYS = ("vA0", "vA_max", "vb_max", "E_clamp_J", "P_clamp_pk_W", "t_clamp_on_ms")
stored = json.load(open("/home/claude/PRISM-Hub/validation/2026-10-26-charging-stop/E26/event_summary.json", encoding="utf-8"))["rows"]


def match(ev):
    return next(r for r in stored if all(r[k] == ev[k] for k in ("arch", "Vbat", "P400", "PC", "clamp", "prof", "t_comm"))
                and (r.get("nmod_after") or 0) == (ev.get("nmod_after") or 0))


def cmp(new, old):
    d = {k: new[k] - old[k] for k in KEYS}
    for k in ("470", "600", "650"):
        a, b = new["t_hit_ms"][k], old["t_hit_ms"][k]
        d["t_hit_" + k] = None if (a is None and b is None) else (a - b if a is not None and b is not None else "None-mismatch")
    return d


out = {}
# (1) original E26 design (module defaults: C_A 400 uF, R_A 10.2 mOhm, clamp 1.0 Ohm): no-clamp R2 640 V and the worst clamp event
ev_a = next(e for e in E26.EVENTS if e["arch"] == "R2" and e["Vbat"] == 640. and e["P400"] == 0. and not e["clamp"])
worst = max((r for r in stored if r["clamp"] and not r.get("nmod_after")), key=lambda r: r["vA_max"])
ev_b = next(e for e in E26.EVENTS if all(e[k] == worst[k] for k in ("arch", "Vbat", "P400", "PC", "clamp", "prof", "t_comm"))
            and not e.get("nmod_after"))
for tag, ev in (("e26_noclamp_R2_640_P0", ev_a), ("e26_worst_clamp", ev_b)):
    t = time.time(); r = E26.run_event(**ev); r.pop("trace", None); w = time.time() - t
    s = match(ev)
    out[tag] = dict(event={k: ev[k] for k in ("arch", "Vbat", "P400", "PC", "clamp", "prof", "t_comm")}, wall_s=w,
                    new={k: r[k] for k in KEYS + ("t_hit_ms",)}, stored={k: s[k] for k in KEYS + ("t_hit_ms",)}, diff=cmp(r, s))
    print(tag, out[tag]["event"], "wall %.1f s" % w, "diff", out[tag]["diff"])
    print("   new vA_max %.6f t470 %s | stored vA_max %.6f t470 %s" % (r["vA_max"], r["t_hit_ms"]["470"], s["vA_max"], s["t_hit_ms"]["470"]))

# (2) state/order dependence
import E38_review_response as E38  # noqa: E402
import E39_clamp_switch_rejudge as E39  # noqa: E402
raw = json.load(open(E39.E38_CLAMP, encoding="utf-8"))["raw"]
evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
c = E38.corners(2, 1.6)["max"]
args = (2, c["R"], c["vdrop"], 468., 463., evs[0])
fields = ("vA_max", "vb_max", "E_branch_J", "S_on", "S_off", "S_i", "S_i2", "i_max", "span_s")
A = E38._ev(args)                                           # after E26 run above (module state mutated by E38._ev itself)
dA = max(abs(A[k] - raw["2_1.6_463_max"][0][k]) for k in fields)
c39 = E39.corners39(2, 1.6)
E39._ev39(([("lo", c39["Rmin"], 0., 1), ("hi", c39["Rmax"], E38.V_DROP_MAX, 1)], 468., 463., evs[0]))  # leaves CL["branches"]
B = E38._ev(args)                                           # no pop: the documented state leak
dB = max(abs(B[k] - raw["2_1.6_463_max"][0][k]) for k in fields)
E26.CL.pop("branches", None)
C = E38._ev(args)
dC = max(abs(C[k] - raw["2_1.6_463_max"][0][k]) for k in fields)
out["leak"] = dict(E38_ev_fresh_vs_raw=dA, E38_ev_after_E39_ev39_no_pop_vs_raw=dB, E38_ev_after_pop_vs_raw=dC,
                   vA_max=[A["vA_max"], B["vA_max"], C["vA_max"]], E_branch=[A["E_branch_J"], B["E_branch_J"], C["E_branch_J"]])
print("leak", out["leak"])
# E26 defaults after E38/E39 calls in the same process (BUS CA, RA_MOD, CL mutated module-wide)
print("E26 globals now: BUS CA %s RA_MOD %s CL %s" % (E26.BUS["CA"], E26.RA_MOD, {k: v for k, v in E26.CL.items() if k != "branches"}))
r = E26.run_event(**ev_a); r.pop("trace", None)
out["e26_after_E38_same_process"] = dict(new=r["t_hit_ms"], vA_max=r["vA_max"], diff=cmp(r, match(ev_a)))
print("E26 R2 640 V no-clamp rerun after E38/E39 in same process: t_hit", r["t_hit_ms"], "diff vs stored", out["e26_after_E38_same_process"]["diff"])
json.dump(out, open(HERE / "state_test.json", "w"), ensure_ascii=False, indent=1, default=str)
