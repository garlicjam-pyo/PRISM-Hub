"""TB25 실행 뒤 진단(판정을 바꾸지 않음): T3 기준값(E1 고정 타이밍 46.875 A, 출력용량 없음)의 적분 간격 의존.

make_ref_TB25.py는 E1을 주기당 340단계(Nstep)로 계산했다. f_r이 낮으면 간격이 길어진다(75 kHz 40 ns, 25 kHz 120 ns).
그러면 데드타임 100 ns가 80·120 ns로 양자화되고 영교차 부근 해상도가 떨어진다. 간격을 150 kHz와 같은 약 20 ns로 둔 값과,
데드타임 전류 소멸 처리(dead_fix)를 켠 값을 함께 출력한다. 출력용량 있음 기준(T2)의 정확해는 출력 노드를 이상 전압원으로
두므로 회로의 C_out 400 µF 리플(25 kHz 1위상 약 2.3 V p-p)은 들어가지 않는다는 점도 함께 적는다.
실행: python diag_e1_step_TB25.py <검증 코드 python 폴더>  → ../results/TB25_e1_step_diag.txt
"""
import json
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E31_stage_a_coss as E31      # noqa: E402
import model_stage_a as SA          # noqa: E402

C = json.load(open("TB25_cases.json"))
S = json.load(open("../results/TB25_summary.json"))
lines = ["TB25 T3 reference diagnostic (E1 fixed timing, 46.875 A, no C_oss): loss [W] vs integration step"]
lines.append("%-4s %10s %14s %14s %14s %12s" % ("des", "Simulink", "E1 Nstep 340", "E1 dt~20 ns", "dt~20 ns+fix", "ripple_pp V"))
for name, d in C["designs"].items():
    keep = {k: SA.BASE[k] for k in ("Lr", "Cfly", "Rds")}; fr0 = SA.FR0
    SA.BASE.update(Lr=d["Lr"], Cfly=d["Cfly"], Rds=d["Rds"]); SA.FR0 = 1 / (2 * np.pi * np.sqrt(d["Lr"] * d["Cfly"]))
    vals = []
    try:
        n2 = int(round(340 * 150e3 / d["fr"]))
        for Nstep, fix in ((340, False), (n2, False), (n2, True)):
            r = SA.sim_array(N=1, Vbat=800., Iload=375 / 8, Cbus=400e-6, mode="fixed", fratio=1 / (d["T"] * SA.FR0), ncyc=60,
                             Nstep=Nstep, dead_fix=fix)
            p = E31.ph_parts(r)[0]
            vals.append(p["Pc"] + p["Pd"])
            rip = float(np.ptp(r["vb"][-Nstep * 2:]))
    finally:
        SA.BASE.update(keep); SA.FR0 = fr0
    sim = S["case"][f"{name}_ld_0"]["loss_W"]
    lines.append("%-4s %10.2f %14.2f %14.2f %14.2f %12.2f" % (name, sim, *vals, rip))
open("../results/TB25_e1_step_diag.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
