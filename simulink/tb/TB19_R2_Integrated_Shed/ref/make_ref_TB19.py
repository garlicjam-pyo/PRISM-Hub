"""TB19 기준값: TB17(R2-W460 통합 강등)과 같은 회로·사례에 Stage A 셰딩 게이트(E24)를 넣는다.

보호·강등·48 V 기준값은 TB17과 같다(TB17/ref의 TB17_* 파일을 TB19_*로 복사, 만든 코드는 TB17/ref/make_ref_TB17.py).
Stage A 기준값만 데드타임 소멸 처리를 켠 모델(E24와 같음)로 다시 계산한다. 끝 구간은 셰딩 문턱에 따라 위상 수를 정한다
(사례 A 끝 약 10 A < I_off 15 A → 위상 하나, 사례 B 끝 약 54 A → 두 위상).
결과: TB19_<사례>_stageA_df.json(pre·final: 위상별 턴오프 전류/첨두, V_A 평균, 첨두, 위상 수), TB19_shed.json(셰딩 파라미터)
실행: python make_ref_TB19.py <검증 코드 python 폴더>
"""
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E24_stage_a_shedding as E      # noqa: E402
import model_stage_a as A             # noqa: E402

src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "TB17_R2_Integrated", "ref")
for f in glob.glob(os.path.join(src, "TB17_*")):
    shutil.copy(f, os.path.basename(f).replace("TB17_", "TB19_"))


def ref(V, I, N):
    r = A.sim_array(N=N, Vbat=V, Iload=I, Cbus=E.CA, mode="zcp", ncyc=80, dead_fix=True)
    ph, bus = A.analyze(r, ncyc_last=10)
    return dict(iout=float(I), phases=N, vA_mean=bus["Vbus"], zcs=[float(p["zcs"]) for p in ph],
                Ipk=[float(p["Ipk"]) for p in ph], Iavg=[float(p["Iavg"]) for p in ph])


for name in ("A_1008V_hbopen", "B_930V_hbopen"):
    sa = json.load(open(f"TB19_{name}_stageA.json"))
    V = json.load(open(f"TB19_{name}_init.json"))["vbat"]
    ip, ie = sa["pre"]["iout"], sa["final"]["iout"]
    Nf = 1 if abs(ie) < E.SHED["I_off"] else 2
    out = dict(pre=ref(V, ip, 2), final=ref(V, ie, Nf))
    json.dump(out, open(f"TB19_{name}_stageA_df.json", "w"), indent=1)
    print(name, "pre %.1f A ZCS %s V_A %.3f, final %.1f A (%d phase) ZCS %s V_A %.3f" % (
        ip, [round(100 * z, 2) for z in out["pre"]["zcs"]], out["pre"]["vA_mean"], ie, Nf,
        [round(100 * z, 2) for z in out["final"]["zcs"]], out["final"]["vA_mean"]))
json.dump(dict(E.SHED, rated_pk=E.RATED_PK, i_abs=E.I_ABS), open("TB19_shed.json", "w"), indent=1)
