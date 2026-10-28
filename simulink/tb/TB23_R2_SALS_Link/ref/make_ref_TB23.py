"""TB23 기준값 생성: 보호 상태기계 ↔ SALS 연동(검증 코드 E29)을 R2-W460 회로 조건으로 계산한다.

강등 순서는 E21 P3t(TB13과 같음: 전압비 정합 유지, EPS, 스위칭 반영 첨두 표, 설계 상한 1.387 × 정격점, 소프트 투입 시간 상한 →
이중 고장)다. 400 V 부하는 E17 r2_run의 sals 인자(공용 모듈 sals_loads.py)로 등급별 계약 응답을 따른다.
회로 계산 시간 때문에 SALS 시간을 ks = 0.15로 줄인다(TB09–TB13의 분리 20 ms → 3 ms와 같은 비율):
  메시지 지연 5 → 0.75 ms, 재송신 주기 10 → 1.5 ms, D 워치독 50 → 7.5 ms, M1·D 감소 0.5 → 3.33 kW/ms·증가 0.06 → 0.4 kW/ms,
  T_CUR_MAX 30 → 4.5 ms, 접촉기 분리 20 → 3 ms. 전기 측정(확인 지속 0.2 ms, 부하전류 추정 필터 0.2 ms)과 Stage C 회생 차단은
  줄이지 않는다.

사례(R2-W460, 고장 0.5 ms)
  A  930 V, 25 kW(M0 9.1 kW), H-브리지 개방, 메시지 지연 5 ms(축소 0.75 ms): SALS 감발 → 부하전류 추정으로 유지 끝 → 붕괴 → 소프트 투입
     → 강등 → 0.5 ms 뒤 SALS 되돌림
  B  930 V, 같은 부하, 감발 메시지 모두 손실: D는 워치독, M1은 줄지 않음 → T_CUR_MAX에 접촉기 분리 → 분리 뒤 붕괴 → 강등(되돌림 없음)
  C  930 V, 고장 순간 버스 순부하 −3.2 kW(Stage C 48 V 회생만), H-브리지 개방, Stage C 회생 차단 없음(E29에서 버스 480.6 V로 불통과)
  D  C와 같고 Stage C 회생 차단(고장 검출 0.1 ms 뒤 4 kW/ms로 0까지)
  E  1008 V, 25 kW, DAB 고장 → 제동 저항 유지 중(검출 0.5 ms 뒤) H-브리지 차단(이중 고장) → 접촉기 분리 + SALS 감발 + Stage A 정지(5 µs)
     + 링크 제동 저항 과전압 보호
결과: TB23_<사례>_init.json, _avg.csv(1 µs, 부하 전력 열 포함), _metrics.json, TB23_eps_table.json, TB23_ref_summary.json
실행: python make_ref_TB23.py <검증 코드 python 폴더>(먼저 E21_dab_switching_margin.py table이 스위칭 표를 만든다)
"""
import json
import math
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E17_protection_integration as E17          # noqa: E402
import E19_r2_window_module as E19                # noqa: E402
import E29_sals_degradation as E29                # noqa: E402
import dab_modulation as DM                       # noqa: E402
from controller_adopted import K_ADOPTED          # noqa: E402
from model_stage_b import equilibrium             # noqa: E402

CASE = "W460_240s"
KS = 0.15
T_SHED_TB = E17.T_SHED * KS                       # 3 ms
PKD = round(1.5 / (1.03 * 1.05), 3)
P3 = dict(E29.P3T)
EV = {"enable": 1, "disable": 2, "dab": 3, "hb_open": 4, "m_pos": 5, "m_neg": 6}
POL = {"now": 1, "collapse_now": 2, "clamp": 3, "clamp_brk": 4, "clamp_brk_hard": 5, "ramp": 1, "brk_hold": 2}
FTYPE = {"hb_open": 1, "dab": 2}
MX = E29.MIXES["MX"]
R1 = dict(sc=-3200., v2l=0., comp=0., ptc=0., bh=0.)


def scfg(mix, scen, sc_block=True):
    return E29.sals_cfg(CASE, mix, scen, ks=KS, sc_block=sc_block)


CASES = {
    "A_930V_MX_S5": dict(V=930., event="hb_open", policy="clamp_brk", sals=scfg(MX, E29.SCEN["S5"]), t_pad=1.2e-3),
    "B_930V_MX_LA": dict(V=930., event="hb_open", policy="clamp_brk", sals=scfg(MX, E29.SCEN["LA"]), t_pad=0.6e-3),
    "C_930V_R1_noblock": dict(V=930., event="hb_open", policy="clamp_brk", sals=scfg(R1, E29.SCEN["S5"], sc_block=False), t_pad=1.2e-3),
    "D_930V_R1_block": dict(V=930., event="hb_open", policy="clamp_brk", sals=scfg(R1, E29.SCEN["S5"]), t_pad=1.2e-3),
    "E_1008V_dab_double": dict(V=1008., event="dab", policy="brk_hold", sals=scfg(MX, E29.SCEN["S5"]),
                               event2=E17.T_EV + E29.dab_det(CASE, 1008.) + E29.T_EV2, astop=E29.ASTOP, fs_brake=True, t_after2=6e-3),
}

c = E19.CASES[CASE]; p, cp = E19.plant(CASE)
K = np.asarray(K_ADOPTED, float)
pk_rated = E17.dab_sps_peak(c["VW"], 100., p.power_max / 100., p)

# ---- 회로 지령표(TB13과 같음) ---------------------------------------------------------------------------------------------
T = DM.eps_table()
J = np.asarray(T["j"]); keep = J <= 1e-9
d = np.asarray(T["d"])[:, keep]; a = np.asarray(T["a"])[:, keep]
d[:, -1] = d[:, -2]; a[:, -1] = a[:, -2]
pk = np.asarray(DM.sw_table(p)["pk_sw"])
phi = np.vectorize(lambda aa, dd: math.remainder(aa + (1 - dd / np.pi) * np.pi, 2 * np.pi))(a, d)
tab = dict(r0=float(T["r"][0]), dr=float(T["r"][1] - T["r"][0]), j0=float(J[keep][0]), dj=float(J[1] - J[0]),
           d=d.tolist(), phi=phi.tolist(), pk=pk.tolist(), pk_max=PKD * pk_rated, rated_pk=pk_rated)
json.dump(tab, open("TB23_eps_table.json", "w"))


def sals_prm(s):
    """회로 블록 prism_sals_loads.m 파라미터 22개(시간·변화율은 축소된 값). 'all' 손실 → −1."""
    lk = lambda v: -1. if v == "all" else float(v)
    mx = s["mix_W"]
    return ([mx["sc"], mx["v2l"], mx["comp"], mx["ptc"], mx["bh"]]
            + [s["delay_s"][k] for k in ("comp", "ptc", "bh")]
            + [lk(s["lost"][k]) for k in ("comp", "ptc", "bh")] + [lk(s["lost_r"][k]) for k in ("comp", "ptc", "bh")]
            + [s["period_s"], s["wd_s"], s["up_W_per_s"], s["dn_W_per_s"], s["t_sc_s"] if s["sc_block"] else 1e9,
               s["sc_slew_W_per_s"], E17.LOAD_MIN_V - 10, E17.LOAD_MIN_V - 10])
# (2026-10-28 TB23 1차 실행 뒤 수정) 회로 블록에는 회생 차단 켬·끔 인자가 없다. 끔은 시작 지연 t_sc = 10⁹ s로 나타낸다.
# 1차 실행에서는 사례 C에도 차단이 걸려(블록이 감발 비트로 차단을 시작) 사실상 D와 같은 조건이었다.


out = {}
for name, cs in CASES.items():
    mix = cs["sals"]["loads"]["mix"]; P = sum(mix.values())
    j = dict(case=CASE, V=cs["V"], P=P, event=cs["event"], policy=cs["policy"], t_shed=T_SHED_TB, sals=cs["sals"], keep=True,
             duration=E17.T_EV + 30e-3, **P3)
    for k in ("event2", "astop", "fs_brake"):
        if k in cs:
            j[k] = cs[k]
    m = E17.r2_run(j)
    # 회로 계산 끝: 강등(또는 이중 고장) 뒤 여유만큼
    t_last = max(e[1] for e in m["events"]) * 1e-3
    t_end = (cs["event2"] + cs["t_after2"]) if "t_after2" in cs else (t_last + cs["t_pad"])
    j["duration"] = t_end
    m = E17.r2_run(j)
    tr = m.pop("trace")
    V = cs["V"]
    xe, ue = equilibrium(V, P, p); x0 = np.array(xe, float); st0 = 3
    u0 = np.array([x0[1] / x0[4], 0.])
    q0 = float(-(x0[0] + K[:4] @ x0[:4]) / K[4])
    sv = cs["sals"]
    sup = [c["VW"], c["upper"], E17.H, p.R, p.Rh, p.Cs, p.Lh, p.inner_tau, p.Clink, E17.VD,
           E17.T_EV, EV[cs["event"]], POL[cs["policy"]], 0., 0., E17.T_PREP, E17.T_WAIT,
           E17.RAMP, E17.HOLD, E17.ZERO, T_SHED_TB, E17.RATE_COL, E17.VL_SOFT, E17.T_SOFT,
           E17.R_SOFT0, E17.R_BYP, E17.T_COL_MAX, E17.VL_SW[0], E17.VL_SW[1], E17.T_SW, E17.VB_SW, E17.T_VB,
           E17.KP_B, E17.KI_B, E17.QB_MAX, E17.W_L, E17.TAU_ST, 1e6, p.power_max, p.link_max, p.turns, p.phase_max,
           p.fs, p.Ldab, V, st0, p.Ts, E17.VS_GATE, E17.T_GATE, E17.T_GATE_MAX,
           E17.VL_STALL, E17.T_STALL, E17.DV_STALL, E17.DI_SOFT, E17.K_UP, E17.T_SOFT_MAX,
           1., 1., 1., E17.T_RESTORE,
           1., sv["i_col"], sv["t_conf"], sv["t_cur_max"], 1. if cs.get("fs_brake") else 0.,
           cs["astop"]["delay"] if "astop" in cs else -1., p.Cb + E17.C_DMP, .2e-3, P / x0[2]]
    assert len(sup) == 69
    prot = [E17.T_HW, E17.I_HW, E17.VL_HW, E17.VS_HW, c["upper"], FTYPE[cs["event"]], E17.T_EV, E17.T_GDF,
            cs.get("event2", 1e30)]
    eps_prm = [1., p.turns, p.Ldab, p.fs, PKD * pk_rated, tab["r0"], tab["dr"], tab["j0"], tab["dj"]]
    init = dict(case=name, vbat=V, P0=P, t_end=t_end, x0=x0[:6].tolist(), vcd0=float(x0[2]),
                u0=u0.tolist(), q0=q0, st0=st0, VW=c["VW"], upper=c["upper"], dab_rated_W=p.power_max, turns=p.turns, Ldab=p.Ldab,
                eta=p.eta, R_bypass=E17.R_BYP, Vd=E17.VD, Rbrk=E17.R_BRK, Rdmp=E17.R_DMP, Cdmp=E17.C_DMP,
                sup_prm=sup, prot_prm=prot, eps_prm=eps_prm, sals_prm=sals_prm(m["sals"]), event=cs["event"], policy=cs["policy"],
                rated_pk=pk_rated, pk_max=PKD * pk_rated, C_A=E29.ASTOP["C_A"], ks=KS, mix=mix, scen=sv["loads"])
    json.dump(init, open(f"TB23_{name}_init.json", "w"), indent=1)
    Lg = tr["log"]; t = tr["t"]
    SLd = E29.rebuild(m["sals"])
    pl = np.array([SLd.power(tt, c_ > .5) if vb >= E17.LOAD_MIN_V - 10 else 0. for tt, c_, vb in zip(t, Lg[:, 7], Lg[:, 2])])
    np.savetxt(f"TB23_{name}_avg.csv", np.column_stack([t, Lg[:, :6], Lg[:, 6], Lg[:, 7], Lg[:, 8], Lg[:, 9], pl]), delimiter=",",
               header="t_s,ip,vs,vbus,ih,vlink,idab,ibyp,loads400,bridge,Pbrk,Pload", comments="", fmt="%.9g")
    ch = E29.fault_checks(m) if cs["event"] == "hb_open" else E29.fs_judge(m, tr)[0]
    m["checks_tb23"] = ch; m["pass_tb23"] = bool(all(ch.values()))
    json.dump({k: v for k, v in m.items()}, open(f"TB23_{name}_metrics.json", "w"), indent=1, default=float)
    out[name] = dict(pass_=m["pass_tb23"], failed=[k for k, v in ch.items() if not v], events=m["events"],
                     path_peak=m["path_peak"], bridge_peak=m["bridge_peak"], vbus_min=m["vbus_min"], vbus_max=m["vbus_max"],
                     vbus_max_loaded=m["vbus_max_loaded"], vlink_max=m["vlink_max"], brk_energy_J=m["brk_energy_J"],
                     soft_energy_J=m.get("soft_energy_J"), dab_sec_peak=m.get("dab_sec_peak"), t_end=t_end)
    print(name, "PASS" if out[name]["pass_"] else "FAIL", out[name])
json.dump(out, open("TB23_ref_summary.json", "w"), indent=1, default=float)
