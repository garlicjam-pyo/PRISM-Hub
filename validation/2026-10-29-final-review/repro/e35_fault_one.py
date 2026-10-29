"""Reviewer driver: run one E35 fault case (FG_920V_charge_m1, seed 1 -> stored phase peak 105.5 A) exactly as E35 fault() does."""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "verification_code" / "python"))
import E35_a25r_verify  # noqa: E402,F401  (patches E33.configure to the A25R design, as `python E35_a25r_verify.py fault` does)
import E33_stage_a_25k_dynamics as E33  # noqa: E402

sys.path.insert(0, str(HERE.parent))
import jcmp  # noqa: E402

name, seed = "FG_920V_charge_m1", 1
t0 = time.time()
E33.configure()
m = E33._fault((name, seed))
wall = time.time() - t0
m = json.loads(json.dumps(m, default=float))
stored = json.load(open("/home/claude/PRISM-Hub/validation/2026-10-28-stage-a-25k/E35/fault.json", encoding="utf-8"))
s = next(c for c in stored["cases"] if c["case"] == name and c["seed"] == seed)
json.dump(m, open(HERE / "_e35_new.json", "w")); json.dump(s, open(HERE / "_e35_old.json", "w"))
acc = jcmp.compare(str(HERE / "_e35_new.json"), str(HERE / "_e35_old.json"))
print("wall %.1f s; phase_peak new %.6f stored %.6f; passed %s/%s" % (wall, m["phase_peak"], s["phase_peak"], m["passed"], s["passed"]))
print("full compare: leaves %d, max abs %.3g at %s, max rel %.3g; struct %s other %s"
      % (acc["n"], acc["abs"][0], acc["abs"][1], acc["rel"][0], acc["struct"][:3], acc["other"][:3]))
