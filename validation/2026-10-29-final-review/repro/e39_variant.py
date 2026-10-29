"""Reviewer driver: run one E39 spec variant (n=2, R_b=1.6, off 463 V) exactly as spec() does, and compare to stored spec.json.
usage: python e39_variant.py reuse|fresh
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "verification_code" / "python"))

import E26_charging_stop as E26  # noqa: E402
import E38_review_response as E38  # noqa: E402
import E39_clamp_switch_rejudge as E39  # noqa: E402

mode = sys.argv[1]
t0 = time.time()
evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
sws, rules = E39.switches39()
reuse = None
if mode == "reuse":
    raw = json.load(open(E39.E38_CLAMP, encoding="utf-8"))["raw"]
    reuse = {"max": raw["2_1.6_463_max"], "min": raw["2_1.6_463_min"]}
j, recs = E39.variant(2, 1.6, 468., 463., evs, E38.V_LIM, sws, reuse=reuse, tag="spec")
wall = time.time() - t0
stored = json.load(open("/home/claude/PRISM-Hub/validation/2026-10-29-clamp-switch/E39/spec.json", encoding="utf-8"))
s = next(r for r in stored["rows"] if r["n"] == 2 and r["R_b"] == 1.6 and r["off"] == 463.)
j = json.loads(json.dumps(j))  # normalise tuples/np types like save_json
out = dict(mode=mode, wall_s=wall, n_events=len(evs), row=j)
json.dump(out, open(HERE / f"e39_variant_{mode}.json", "w"), ensure_ascii=False, indent=1)
print(E39.line(j))
print("wall %.1f s" % wall)
for sn in j["switches"]:
    a, b = j["switches"][sn]["T_vj"], s["switches"][sn]["T_vj"]
    print("  %-14s T_vj new %.6f stored %.6f diff %.3g  ok %s/%s" % (sn, a, b, a - b, j["switches"][sn]["ok"], s["switches"][sn]["ok"]))
for k in ("C1_V", "i_branch_max", "E_branch_max_J", "E_hi_obs", "E_lo_obs", "R_max", "R_min"):
    print("  %-15s new %.9g stored %.9g diff %.3g" % (k, j[k], s[k], j[k] - s[k]))
print("  C1_by", j["C1_by"], "stored", s["C1_by"])
print("  ok_variant", j["ok_variant"], s["ok_variant"], "pick", E39.pick_switch(j, "FF450R12ME4P"))
