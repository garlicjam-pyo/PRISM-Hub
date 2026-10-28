"""[E36] Stage A 설계 A25R(25 kHz, C_A 2.4 mF)로 바뀐 이전 결론의 재계산·재확인.

■ 목적
  E15–E30은 150 kHz Stage A(R1, 위치당 6 mΩ 가정, 출력용량 손실 4·E_oss·f_s)와 V_A 노드 커패시터 C_A 400 µF로 계산했다.
  Stage A를 A25R로 정했으므로(docs/40), 그 결론 가운데 Stage A 손실·출력저항·C_A에 기대는 것을 다시 계산한다.
  결론이 바뀌는지, 바뀌면 얼마나 바뀌는지를 보고한다.

■ 왜 필요한가
  최종 보고서의 손실 이점(H5 결론, ⑤ 대비 보조 경로, 모터 승압 대비 충전), 가치 지도(E18), 충전 중 보조버스(H3), R2 기본형
  버스와 48 V(E23), 충전 중 정지(E26), 이중 고장 Stage A 정지(E29)가 모두 Stage A 모델을 쓴다. 바뀐 설계로 다시 확인하지 않으면
  보고서의 수치와 판정이 서로 다른 설계에 근거하게 된다.

■ A25R Stage A 모델(이 시험에서 쓰는 값)
  손실·V_A 강하 표: E32 loss_grid_raw(A25 직접 모의, 640–920 V × 위상당 1–50 A, 충전 375 A)와 위상 셰딩 I_off 20 A(E32 문턱).
    E18용 사양 밖 배터리 전압(540·580·960·1010 V)은 같은 방법(E32._e15_point)으로 새로 계산한다.
  모듈 출력저항 R_A = 9.0 mΩ(E32 design 800 V 2위상 V_A 강하 기울기, 150 kHz는 10.2 mΩ).  C_A = 2.4 mF.
  C_A는 손실 표에 영향이 없다(이상 커패시터). E25의 Stage A 감도(수동소자 저항 2배)도 A25 설계로 다시 계산한다.

■ 부분과 판정(실행 전에 고정)
  L1 e15   : E15 evaluate·ratings·judge·breakeven을 A25R 표로 다시. 판정 함수와 기준(H5: ③이 ④·③′보다 세 지표 중 2개 이상 우수)은
             E15와 같다. 보고: H5 판정이 E15(기각)와 같은가, 구조별 손실·충전 손실.
  L2 e25   : E25 비교(①·④·⑤·⑥ 보조 손실, 충전 손실과 모터 승압 기준점·범위, 손익분기 상저항, 손실 에너지 예시)를 A25R 표로.
             판정 없음(값 보고). 결론 문장 대조: ④ < ⑤ 보조, ④ > ⑥ 보조, 충전 ④ < 모터 승압 기준점, 충전 ④ < 모터 승압 하한(R_ph ≥ 5 mΩ).
  L3 e18   : E18 가치 지도를 R1 표(E18 확장 격자, 셰딩 없음 = E18 원 계산)와 A25R 표(셰딩 I_off 20 A)로 각각 계산해
             팩 등급·부품 등급별 성립 구조와 최선 구조를 비교. 판정 없음(바뀐 칸 보고). 차이에는 셰딩 효과도 들어 있다.
  D1 e16   : E16 static·concurrent·transition·sequence를 R_A 9.0 mΩ로. 판정 기준은 E16과 같다(동시 운전 Tier-1 460·Tier-2 78,
             모드 전환 Tier-2 240, 전체 순서 30, 정적 4,118점 성립).
  D2 e23   : E23 base(사례 A·B·C)·zbus를 R_A 9.0 mΩ, C_A 2.4 mF로. 기준은 E23과 같다(48 V 대역, 버스 대역·안정, Stage C 전류,
             |Z_bus| ≤ |Z_in|/2). Stage A 기준값(정보)은 A25 설계로 계산한다.
  D3 e26   : E26 클램프 없는 사건 8개(R2·R2-W × 640·920 V × 부하 2)를 C_A 2.4 mF·R_A 9.0 mΩ로. 판정 없음(470·600·650 V 도달 시간
             보고).
             클램프 있는 사건은 E35 clamp에서 계산했다.
  D4 e29   : E29 이중 고장 F2(Stage A 정지 + 부하 차단 + 제동 유지) 4사례를 Stage A 정지 뒤 V_A 노드 C_A 2.4 mF로. 기준은 E29 failsafe와
             같다(경로·필터 ≤ 100 A, 직렬 ≤ 120 V, 링크 ≤ 120 V, 400 V 부하 연결 중 버스 ≤ 상한, 제동 ≤ 64 J, Stage A 정지 뒤 5 ms 안에
             |i_p| ≤ 1 A로 유지). E29는 1/4 통과였다.
  D5 dropout: 충전기 급정지(새 사례). A25R 4모듈 정격 충전(375 A + 버스 15 kW, 처음부터 충전 요청) 중 2.0 ms에 충전기 전류가 10 µs에
             0이 된다(커넥터 분리·충전기 고장). 충전 요청은 1 ms 뒤(3.0 ms)에 끝난다. 640·800·920 V × 공칭·표본 1, 4.5 ms.
             판정(E30 고장 판정 F2·F3과 같은 한계): 1.9 ms 이후 위상 첨두 ≤ 1.5 × P_rated(표본별), 사건 뒤 V_A가 사건 직전 공진 한 주기
             평균 ± 10 V 안이고 ≤ 470 V. 턴오프 전류는 정보(600 µs 램프 요구 밖의 고장 사건).

■ 실행 결과(2026-10-28, 기준은 바꾸지 않았다. 괄호 안은 150 kHz 설계의 원 시험 값)
  L1 e15  : H5 기각 유지(엄격·동등범위 3 % 모두 E15와 같음). 주행 대표 ① 114.6, ② 133.3(123.8), ③ 143.2(133.8),
            ③′ 123.4(114.1), ④ 94.4(85.0) W. 충전 ④ 520·586·630 W(640·800·900 V, E15 497 W). ③ = ④ 손익분기 배율 0.228(같음).
  L2 e25  : 보조 ④ 94.4 W(⑤ 114.6, ⑥ 70.1 W). 충전 ④ 520/586/639 W, 모터 승압 기준점 1027/1165/1285 W, 하한 571/607/633 W.
            결론 문장 4개 가운데 "충전 ④ < 모터 승압 하한"이 920 V에서 바뀜(639 > 633 W). 손익분기 상저항 3.02(1.87)·2.46(1.31) mΩ.
  L3 e18  : 바뀐 칸 2개(216s·사양 팩 B_420의 최선 W410 → ①). 사양 팩 ④ 94.4(85.0), W410 123.7(114.4), ① 114.6 W.
  D1 e16  : 모두 통과(정적, 동시 운전 Tier-1 460·Tier-2 78, 모드 전환 240, 전체 순서 30). 경로 첨두·버스 범위가 E16과 0.9 A·0.2 V 안.
  D2 e23  : base 3/3, Stage A ZCS 최대 4.00 %, zbus 최소 여유 49.9 dB — 통과.
  D3 e26  : 470 V 도달 R2 640 V 1.72·2.08 ms(0.90·1.09), R2-W 640 V 0.95·1.15 ms(0.16·0.19), 920 V 0.06–0.09 ms(0.01).
  D4 e29  : F2 0/4(E29 1/4). 경로전류 ≤ 1 A까지 7.6·8.8 ms이거나 끝까지 안 됨, 직렬 120.1–123.3 V(3사례 > 120 V).
  D5      : 충전기 급정지 6/6. 첨두 65.0–71.7 A, V_A −3.7·+0.9 V, 턴오프 위반 6–15번·최대 4.1 A(정보).

■ 실행   python E36_a25r_impact.py tables e15 e25 e18 e16 e23 e26 e29 dropout   (2코어 약 1시간)
■ 결과   results/E36/*.json
"""
import os
import sys
from multiprocessing import Pool

import numpy as np

from common import load_json, outdir, save_json, verdict, workers

EID = "E36"
RA_A25 = 9.0e-3
CA_R = 2.4e-3
V_EXTRA = [540., 580., 960., 1010.]
I_OFF = 20.


def _save(prefix):
    return lambda eid, name, obj: save_json(EID, prefix + name, obj)


# ======================================================================================================
# A25R Stage A 표
# ======================================================================================================
def _grid_point(args):
    import E32_stage_a_25k as E32
    return E32._e15_point(args)


def _grid_point_x2(args):
    """수동소자 저항(ESR·RL·Rmisc) 2배 A25(E25 Stage A 감도와 같은 변경)."""
    V, iph, sign = args
    import model_stage_a as A
    import E32_stage_a_25k as E32
    A.set_design(E32.DESIGN)
    for k in ("ESR", "RL", "Rmisc"):
        A.BASE[k] *= 2
    r = A.sim_array(N=2, Vbat=V, Iload=sign * 2 * iph, Cbus=400e-6, mode="zcp", ncyc=60, dead_fix=True, unarmed_stop=E32.GATE)
    ph, bus = A.analyze(r)
    A.set_design(E32.DESIGN)
    return dict(V=V, iph=iph, sign=sign, ploss_ph=float(np.mean([p["Ploss"] for p in ph])), dvA=float(V / 2 - bus["Vbus"]))


def tables():
    import E15_baseline_loss_rating as E15
    raw = load_json("E32", "loss_grid_raw")
    jobs = [(V, i, 1.) for V in V_EXTRA for i in E15.IGRID] + [(V, 375. / 8, -1.) for V in V_EXTRA]
    with Pool(workers()) as p:
        ext = p.map(_grid_point, jobs, chunksize=1)
    save_json(EID, "a25_grid", dict(spec=raw, extra=ext, V_extra=V_EXTRA, I=list(E15.IGRID)))
    jobs = [(V, i, 1.) for V in E15.VGRID for i in E15.IGRID] + [(V, 375. / 8, -1.) for V in E15.VGRID]
    with Pool(workers()) as p:
        x2 = p.map(_grid_point_x2, jobs, chunksize=1)
    save_json(EID, "a25_grid_Rpass_x2", x2)


def _T_from(res):
    import E15_baseline_loss_rating as E15
    fw = [r for r in res if r["sign"] > 0]
    return dict(P=np.array([r["ploss_ph"] for r in fw]).reshape(len(E15.VGRID), len(E15.IGRID)),
                D=np.array([r["dvA"] for r in fw]).reshape(len(E15.VGRID), len(E15.IGRID)),
                charge={r["V"]: r for r in res if r["sign"] < 0})


def _T_spec():
    return _T_from(load_json(EID, "a25_grid")["spec"])


def _SA():
    import E32_stage_a_25k as E32
    return E32.StageAs(_T_spec(), I_OFF)


# ======================================================================================================
# L1 E15
# ======================================================================================================
def e15():
    import E15_baseline_loss_rating as E15
    SAm = _SA()
    res = E15.evaluate(SAm); rat = E15.ratings(SAm)
    jd = E15.judge(res, rat); jd_band = E15.judge(res, rat, band=0.03)
    jd_prof = {pk: E15.judge(res, rat, pk) for pk in E15.PROFILES}
    try:
        be = E15.breakeven(SAm)
    except ValueError as e:                                      # 0–1 구간에서 부호가 바뀌지 않으면(손익분기 없음)
        be = dict(stageB_nc_breakeven=None, note=str(e))
    ref = load_json("E15", "comparison")
    save_json(EID, "e15_comparison", dict(results=res, ratings=rat, judge=jd, judge_band3=jd_band, judge_by_profile=jd_prof,
                                          breakeven=be, stage_a="A25R(E32 표, 셰딩 I_off 20 A)"))
    print("구조   주행 대표(A25R / E15) | 충전 800 V(A25R / E15)")
    for s in E15.STRUCTS:
        print("  %-3s %7.1f / %7.1f W | %6.0f / %6.0f W" % (s, res[s]["drive_typ"]["avg_loss_W"], ref["results"][s]["drive_typ"]["avg_loss_W"],
                                                        res[s]["charge_W"]["800V"], ref["results"][s]["charge_W"]["800V"]))
    for tag, j, j0 in (("엄격", jd, ref["judge"]), ("동등범위 3 %", jd_band, ref["judge_band3"])):
        for b in ("4", "3w"):
            print("  [%s] ③ vs %s: 우수 %s → %s (E15 %s)" % (tag, b, j[b]["wins"], "통과" if j[b]["pass_"] else "불통과",
                                                       "통과" if j0[b]["pass_"] else "불통과"))
        verdict("(L1 %s) H5 판정이 E15와 같음" % tag, j["H5_metric_pass"] == j0["H5_metric_pass"],
                "A25R %s, E15 %s" % ("충족" if j["H5_metric_pass"] else "불충족(기각)", "충족" if j0["H5_metric_pass"] else "불충족(기각)"))
    print("  ③ = ④ 손익분기 Stage B 비도통 손실 배율: %s(E15 %.3f)" % (be["stageB_nc_breakeven"], ref["breakeven"]["stageB_nc_breakeven"]))


# ======================================================================================================
# L2 E25
# ======================================================================================================
def e25():
    import E15_baseline_loss_rating as E15
    import E25_motor_boost_comparison as E25
    import E32_stage_a_25k as E32
    T = _T_spec()
    grid = dict(P_phase=T["P"].tolist(), dvA=T["D"].tolist(), charge={str(k): v for k, v in T["charge"].items()})
    c15 = load_json(EID, "e15_comparison")

    def lj(eid, name):
        if (eid, name) == ("E15", "stage_a_grid"):
            return grid
        if (eid, name) == ("E15", "comparison"):
            return c15
        return load_json(eid, name)
    def sens(SAm, aux, ch800):                                  # E25 stage_a_sensitivity와 같은 항목을 A25 설계로
        import model_stage_a as A
        SA2 = E32.StageAs(_T_from(load_json(EID, "a25_grid_Rpass_x2")), I_OFF)
        aux4_2, _ = E25.aux_avg(lambda V, P: E15.path_struct("4", SA2, V, P, E15.P48)["loss"])
        A.set_design(E32.DESIGN); fs = A.FR0
        fixed = 4 * A.qoss_pos(400.) * 400. * fs + 4 * A.BASE["Qg_E"] * fs   # 800 V(위치 전압 400 V)
        return dict(Rpass_x2=dict(aux4_W=aux4_2, charge800_W=E15.charge_loss("4", SA2, 800.)),
                    dP_eq5_W=(aux["5"]["avg_W"] - aux["4"]["avg_W"]) / 2, dP_eq6_W=(aux["6"]["avg_W"] - aux["4"]["avg_W"]) / 2,
                    fixed_per_phase_W=fixed, core_rule_W=0.001 * 150e3 / 8, dP_charge_W_per_W=8.)
    E25.load_json = lj
    E25.save_json = _save("e25_")
    E25.EID = EID
    E25.stage_a_sensitivity = sens
    SA0 = E15.StageA
    E15.StageA = lambda T_: E32.StageAs(T_, I_OFF)            # E25 안의 Stage A를 셰딩 있는 A25R로
    try:
        E25.main()
    finally:
        E15.StageA = SA0
    os.replace(outdir(EID) / "E25_motor_boost.png", outdir(EID) / "e25_motor_boost.png")
    out = load_json(EID, "e25_comparison"); ref = load_json("E25", "comparison")
    a, a0 = out["aux"], ref["aux"]
    print("  보조 평균(A25R / E25): ① %.1f/%.1f, ④ %.1f/%.1f, ⑤ %.1f/%.1f, ⑥ %.1f/%.1f W"
          % (a["1"]["avg_W"], a0["1"]["avg_W"], a["4"]["avg_W"], a0["4"]["avg_W"], a["5"]["avg_W"], a0["5"]["avg_W"], a["6"]["avg_W"], a0["6"]["avg_W"]))
    for V in ("640V", "800V", "920V"):
        c, c0 = out["charge"][V], ref["charge"][V]
        print("  충전 %s: ④ %.0f(E25 %.0f) W, 모터 기준점 %.0f, 하한 %.0f, 전용 승압기 %.0f W"
              % (V, c["stageA"], c0["stageA"], c["motor_base"], c["motor_range"]["min_Rph5"], c["booster"]))
    st = dict(aux4_lt_5=a["4"]["avg_W"] < a["5"]["avg_W"], aux4_gt_6=a["4"]["avg_W"] > a["6"]["avg_W"],
              charge_lt_motor_base={V: out["charge"][V]["stageA"] < out["charge"][V]["motor_base"] for V in out["charge"]},
              charge_lt_motor_min={V: out["charge"][V]["stageA"] < out["charge"][V]["motor_range"]["min_Rph5"] for V in out["charge"]})
    st0 = dict(aux4_lt_5=a0["4"]["avg_W"] < a0["5"]["avg_W"], aux4_gt_6=a0["4"]["avg_W"] > a0["6"]["avg_W"],
               charge_lt_motor_base={V: ref["charge"][V]["stageA"] < ref["charge"][V]["motor_base"] for V in ref["charge"]},
               charge_lt_motor_min={V: ref["charge"][V]["stageA"] < ref["charge"][V]["motor_range"]["min_Rph5"] for V in ref["charge"]})
    print("  결론 문장 대조(A25R / E25):", st, "/", st0)
    print("  손익분기 상저항(A25R / E25): %.2f / %.2f mΩ(가장 유리한 조합), %.2f / %.2f mΩ(기준점)"
          % (out["breakeven"]["Rph_breakeven_best_mOhm"], ref["breakeven"]["Rph_breakeven_best_mOhm"],
             out["breakeven"]["Rph_breakeven_base_mOhm"], ref["breakeven"]["Rph_breakeven_base_mOhm"]))
    save_json(EID, "e25_statements", dict(A25R=st, E25=st0))


# ======================================================================================================
# L3 E18
# ======================================================================================================
def _ext_model(kind):
    import E18_industry_value_map as E18
    if kind == "R1":
        g = load_json("E18", "stage_a_grid_ext")
        return E18.StageAX(g["V"], np.array(g["P_phase"]), np.array(g["dvA"]), {float(k): v for k, v in g["charge"].items()})
    import E15_baseline_loss_rating as E15
    G = load_json(EID, "a25_grid")
    rows = {}
    for r in G["spec"] + G["extra"]:
        if r["sign"] > 0:
            rows.setdefault(float(r["V"]), {})[r["iph"]] = (r["ploss_ph"], r["dvA"])
    VG = sorted(rows)
    P = np.array([[rows[v][i][0] for i in E15.IGRID] for v in VG]); D = np.array([[rows[v][i][1] for i in E15.IGRID] for v in VG])
    charge = {float(r["V"]): r for r in G["spec"] + G["extra"] if r["sign"] < 0}

    class StageAXs(E18.StageAX):
        def drive(self, V, I, nph=2):
            if abs(I) < I_OFF:
                nph = 1
            return super().drive(V, I, nph)
    return StageAXs(VG, P, D, charge)


def e18():
    import E18_industry_value_map as E18
    c15a = load_json(EID, "e15_comparison")
    for kind in ("R1", "A25R"):
        SAm = _ext_model(kind)
        E18.stage_a_model = lambda S=SAm: S
        E18.save_json = _save("e18_%s_" % kind)
        E18.outdir = lambda eid: outdir(EID)
        if kind == "A25R":
            E18.load_json = lambda eid, name: c15a if (eid, name) == ("E15", "comparison") else load_json(eid, name)
        print("==== E18 가치 지도: Stage A %s ====" % kind)
        E18.main()
        os.replace(outdir(EID) / "E18_value_map.png", outdir(EID) / ("e18_%s_value_map.png" % kind))
    a, b = load_json(EID, "e18_R1_value_map"), load_json(EID, "e18_A25R_value_map")
    diff = []
    for pk in a["packs"]:
        for c in a["packs"][pk]["best"]:
            x, y = a["packs"][pk]["best"][c], b["packs"][pk]["best"][c]
            if x["best"] != y["best"] or sorted(x["feasible"]) != sorted(y["feasible"]):
                diff.append(dict(pack=pk, cls=c, R1=x, A25R=y))
    loss = {pk: {s: [a["packs"][pk]["structs"][s]["loss"]["avg_W"], b["packs"][pk]["structs"][s]["loss"]["avg_W"]]
                 for s in a["packs"][pk]["structs"]} for pk in a["packs"]}
    chg = {pk: [a["packs"][pk]["charging"].get("loss_150kW_W"), b["packs"][pk]["charging"].get("loss_150kW_W")] for pk in a["packs"]}
    print("  성립·최선 구조가 바뀐 칸: %d" % len(diff))
    for d in diff:
        print("   ", d["pack"], d["cls"], "R1:", d["R1"], "→ A25R:", d["A25R"])
    save_json(EID, "e18_compare", dict(changed=diff, loss_R1_A25R=loss, charge150_R1_A25R=chg))


# ======================================================================================================
# D1 E16
# ======================================================================================================
def e16():
    import E16_charging_integration as E16
    E16.RA_MOD = RA_A25
    E16.save_json = _save("e16_")
    for part in ("static", "concurrent", "transition", "sequence"):
        print("==== E16 %s (R_A %.1f mΩ) ====" % (part, RA_A25 * 1e3), flush=True)
        E16.PARTS[part]()


# ======================================================================================================
# D2 E23
# ======================================================================================================
def _stage_a_ref_a25(vbat, iout, N=2):
    """E23 stage_a_ref와 같은 계산을 A25(E32 설정: 데드 보정, 자화 게이트)·C_A 2.4 mF로."""
    import model_stage_a as A
    import E32_stage_a_25k as E32
    A.set_design(E32.DESIGN)
    r = A.sim_array(N=N, Vbat=vbat, Iload=iout, Cbus=CA_R, mode="zcp", ncyc=80, dead_fix=True, unarmed_stop=E32.GATE)
    ph, bus = A.analyze(r, ncyc_last=10)
    return dict(iout=float(iout), vA_mean=bus["Vbus"], vA_ripple=bus["ripple"],
                zcs=[float(p["zcs"]) for p in ph], Ipk=[float(p["Ipk"]) for p in ph], Iavg=[float(p["Iavg"]) for p in ph],
                fs=[float(p["fs"]) for p in ph], vA_ideal=vbat / 2)


def e23():
    import E23_r2_integrated as E23
    E23.RA = RA_A25; E23.CA = CA_R
    E23.zbus_ca.__defaults__ = (RA_A25,)                        # 기본 인자는 정의 때 묶이므로 따로 바꾼다
    E23.stage_a_ref = _stage_a_ref_a25
    E23.save_json = _save("e23_")
    E23.base(); E23.zbus()


# ======================================================================================================
# D3 E26
# ======================================================================================================
def _ev26(kw):
    import E26_charging_stop as E26
    E26.BUS["CA"] = CA_R; E26.RA_MOD = RA_A25
    r = E26.run_event(**kw)
    r.pop("trace", None)
    return r


def e26():
    import E26_charging_stop as E26
    evs = [e for e in E26.EVENTS if not e["clamp"] and not e.get("nmod_after")]
    for e in evs:
        e["tend"] = 30e-3                                          # C_A가 커 도달이 늦으므로 계산 시간을 늘린다
    with Pool(workers()) as p:
        rows = p.map(_ev26, evs)
    ref = {(r["arch"], r["Vbat"], r["P400"]): r for r in load_json("E26", "event_summary")["rows"]
           if not r["clamp"] and not r.get("nmod_after")}
    for r in rows:
        r0 = ref.get((r["arch"], r["Vbat"], r["P400"]))
        print("  %-3s %4.0f V 부하 %2.0f+%1.0f kW: 470/600/650 V 도달 %s ms (C_A 400 µF: %s ms)"
              % (r["arch"], r["Vbat"], r["P400"] / 1e3, r["PC"] / 1e3, [r["t_hit_ms"][k] for k in ("470", "600", "650")],
                 [r0["t_hit_ms"][k] for k in ("470", "600", "650")] if r0 else None))
    save_json(EID, "e26_noclamp", dict(rows=rows, CA=CA_R))


# ======================================================================================================
# D4 E29 F2
# ======================================================================================================
def _fs(job):
    import E29_sals_degradation as E29
    return E29._run_fs(job)


def e29():
    import E17_protection_integration as E17
    import E29_sals_degradation as E29
    det = load_json("E29", "failsafe")["dab_det_ms"]
    astop = dict(E29.ASTOP, C_A=CA_R)
    js = []
    for case, V in E29.FS_PACKS:
        t2 = E17.T_EV + det["%s_%.0f" % (case, V)] * 1e-3 + E29.T_EV2
        js.append(dict(case=case, V=V, P=E29.P0, event="dab", policy="brk_hold", event2=t2, duration=t2 + 10e-3, keep=True,
                       _tag="%s_%.0f_F2" % (case, V), _extra=dict(pol="F2", dab_det_ms=det["%s_%.0f" % (case, V)], t2_ms=(t2 - E17.T_EV) * 1e3),
                       sals=E29.sals_cfg(case, E29.MIXES["MX"], E29.SCEN["S5"]), fs_brake=True, astop=astop, **E29.P3T))
    with Pool(workers()) as p:
        rows = p.map(_fs, js, chunksize=1)
    ref = {r["tag"]: r for r in load_json("E29", "failsafe")["rows"]}
    for r in rows:
        r0 = ref[r["tag"]]
        bad = [k for k, v in r["checks"].items() if not v]
        print("  %-22s %s 링크 %.1f V, 경로 %.1f A, 직렬 %.1f V, 제동 %.1f J, |i_p| ≤ 1 A까지 %s ms (C_A 400 µF: %s, %s ms) %s"
              % (r["tag"], "통과" if r["pass_"] else "불통과", r["vlink_max"], r["path_peak"], r["series_peak"], r["brk_energy_J"],
                 r["ip_zero_ms"], "통과" if r0["pass_"] else "불통과", r0["ip_zero_ms"], bad))
    verdict("(D4) 이중 고장 F2, C_A 2.4 mF", all(r["pass_"] for r in rows), "%d/%d(E29 %d/4)" % (sum(r["pass_"] for r in rows), len(rows),
                                                                                         sum(ref[r["tag"]]["pass_"] for r in rows)))
    save_json(EID, "e29_failsafe_F2", dict(rows=rows, ASTOP=astop))


# ======================================================================================================
# D5 충전기 급정지
# ======================================================================================================
T_DO = 2.0e-3


def _dropout(args):
    V, seed = args
    import E24_stage_a_shedding as E24
    import E28_stage_a_modules as E28
    import E35_a25r_verify as E35
    E35.configure()
    name = "DO_%.0fV" % V
    E28.CASES[name] = dict(V=V, prof=([0, T_DO, T_DO + 10e-6, 1], [-375., -375., 0., 0.]), bus=([0, 1], [15e3, 15e3]),
                           chg=(0., T_DO + 1e-3), tend=4.5e-3, n_end=1, add_max=0, rem_max=3)
    r = E28.run_case(name, seed)
    t = r["t"]; w = t >= T_DO - 0.1e-3
    pre = (t >= T_DO - E28.T) & (t < T_DO)                      # 사건 직전 공진 한 주기
    vpre = float(r["vb"][pre].mean()); post = t >= T_DO
    to = E24.turnoffs(r, T_DO - 0.1e-3)
    bad = [x for x in to if abs(x[2]) > max(0.05 * x[3], E28.I_ABS)]
    pk = float(np.abs(r["i"][w]).max()); lim = 1.5 * E28.p_rated(seed)
    vmin, vmax = float(r["vb"][post].min()), float(r["vb"][post].max())
    L = dict(peak=pk <= lim, vA=abs(vmin - vpre) <= 10. and abs(vmax - vpre) <= 10. and vmax <= 470.)
    na = r["nact"].astype(int); ch = np.where(np.diff(na) != 0)[0]
    return dict(V=V, seed=seed, peak=pk, limit=lim, vA_pre=vpre, vA=[vmin, vmax], n_turnoff=len(to), n_bad=len(bad),
                ioff_max=max(abs(x[2]) for x in to), events=[(round(float(t[k + 1]) * 1e3, 4), int(na[k + 1])) for k in ch],
                limits=L, passed=all(L.values()))


def dropout():
    import E33_stage_a_25k_dynamics as E33
    jobs = [(V, s) for V in (640., 800., 920.) for s in E33.SEEDS]
    with Pool(workers()) as p:
        rows = p.map(_dropout, jobs, chunksize=1)
    for x in rows:
        print("  %4.0f V 공차 %-4s %s 첨두 %.1f A(한도 %.1f), V_A %.2f → %.2f–%.2f V, 턴오프 %d(위반 %d, 최대 %.2f A, 정보), 모듈 %s"
              % (x["V"], x["seed"], "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v]), x["peak"],
                 x["limit"], x["vA_pre"], x["vA"][0], x["vA"][1], x["n_turnoff"], x["n_bad"], x["ioff_max"], x["events"]))
    verdict("(D5) 충전기 급정지(10 µs)", all(x["passed"] for x in rows), "%d/%d" % (sum(x["passed"] for x in rows), len(rows)))
    save_json(EID, "dropout", dict(rows=rows, t_dropout=T_DO))


if __name__ == "__main__":
    for part in sys.argv[1:] or ["tables", "e15", "e25", "e18", "e16", "e23", "e26", "e29", "dropout"]:
        print("E36", part, "...", flush=True)
        globals()[part]()
