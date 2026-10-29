"""TB31 기준값 생성: Stage C 일시 정지(P6)와 이중 고장 400 V 부하 정지(F2)를 R2-W460 회로 조건으로 계산한다(검증 코드 E38).

TB23과 같은 강등 순서(E21 P3t)·SALS 계약 응답·시간 축소(ks = 0.15: 메시지 지연 5 → 0.75 ms, 접촉기 20 → 3 ms 등)에 다음을 더한다.
  - Stage C 일시 정지(E17 sc_pause): 링크 붕괴 시작 때 Stage C 입력(양의 전력)을 4 kW/ms로 0까지, 강등 0.5 ms 뒤 같은 변화율로 재개.
    허브 내부 명령이므로 시간 축소하지 않는다.
  - 400 V 부하 정지(E17 load_stop): 이중 고장 진입 때 400 V 부하 전체를 E38 f2가 고른 램프(전용 배선 신호, 시간 축소하지 않음)로 0까지.
  - C_A 2.4 mF(A25R), 이중 고장의 V_A 노드 방전 저항 없음.
상태기계 파라미터 71개(70 Stage C 일시 정지, 71 부하 정지), 부하 블록 파라미터 23개(23 정지 램프).
사례(R2-W460, 고장 0.5 ms)
  A31  930 V, 25 kW(M0 9.1 kW), H-브리지 개방, 메시지 지연 5 ms(축소 0.75 ms), Stage C 일시 정지: TB23 A와 같은 사건에서 소프트 투입이
       붕괴 끝(링크 0.5 V)에서 시작하는지
  E31  1008 V, 25 kW, DAB 고장 → 제동 유지 중(검출 0.5 ms 뒤) H-브리지 차단(이중 고장) → 접촉기 분리 + SALS 감발 + Stage A 정지(5 µs)
       + 링크 제동 저항 과전압 보호 + 400 V 부하 정지(E38 선정 램프). TB23 E와 같은 사건(C_A 2.4 mF, 부하 정지 추가)
결과: TB31_<사례>_init.json, _avg.csv(1 µs, 부하 전력 열 포함), _metrics.json, TB31_eps_table.json, TB31_ref_summary.json
실행: python make_ref_TB31.py <검증 코드 python 폴더> [E38 f2.json](먼저 E21_dab_switching_margin.py table이 스위칭 표를 만든다)
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
import E34_parts_rating as E34                    # noqa: E402
FO = E34.epc_foster()                             # EPC2305 Z_thJC Foster(바이패스 소프트 투입 소자 온도, E34 P6와 같음)
from controller_adopted import K_ADOPTED          # noqa: E402
from model_stage_b import equilibrium             # noqa: E402

CASE = "W460_240s"
F2 = json.load(open(sys.argv[2] if len(sys.argv) > 2 else "../../../../submission/verification_code/results/E38/f2.json", encoding="utf-8"))
RAMP = F2["selected_ramp_ms"] * 1e-3                 # E38 f2 선정 램프
CA_R = 2.4e-3
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
    "A31_930V_MX_S5_pause": dict(V=930., event="hb_open", policy="clamp_brk", sals=scfg(MX, E29.SCEN["S5"]), sc_pause=True, t_pad=1.2e-3),
    "E31_1008V_dab_double_stop": dict(V=1008., event="dab", policy="brk_hold", sals=scfg(MX, E29.SCEN["S5"]),
                                      event2=E17.T_EV + E29.dab_det(CASE, 1008.) + E29.T_EV2, astop=dict(E29.ASTOP, C_A=CA_R),
                                      fs_brake=True, load_stop=RAMP, t_after2=8e-3),
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
json.dump(tab, open("TB31_eps_table.json", "w"))


def sals_prm(s):
    """회로 블록 prism_sals_loads.m 파라미터 22개(시간·변화율은 축소된 값). 'all' 손실 → −1."""
    lk = lambda v: -1. if v == "all" else float(v)
    mx = s["mix_W"]
    return ([mx["sc"], mx["v2l"], mx["comp"], mx["ptc"], mx["bh"]]
            + [s["delay_s"][k] for k in ("comp", "ptc", "bh")]
            + [lk(s["lost"][k]) for k in ("comp", "ptc", "bh")] + [lk(s["lost_r"][k]) for k in ("comp", "ptc", "bh")]
            + [s["period_s"], s["wd_s"], s["up_W_per_s"], s["dn_W_per_s"], s["t_sc_s"] if s["sc_block"] else 1e9,
               s["sc_slew_W_per_s"], E17.LOAD_MIN_V - 10, E17.LOAD_MIN_V - 10])
# (2026-10-28 TB31 1차 실행 뒤 수정) 회로 블록에는 회생 차단 켬·끔 인자가 없다. 끔은 시작 지연 t_sc = 10⁹ s로 나타낸다.
# 1차 실행에서는 사례 C에도 차단이 걸려(블록이 감발 비트로 차단을 시작) 사실상 D와 같은 조건이었다.


out = {}
for name, cs in CASES.items():
    mix = cs["sals"]["loads"]["mix"]; P = sum(mix.values())
    j = dict(case=CASE, V=cs["V"], P=P, event=cs["event"], policy=cs["policy"], t_shed=T_SHED_TB, sals=cs["sals"], keep=True,
             duration=E17.T_EV + 30e-3, **P3)
    for k in ("event2", "astop", "fs_brake", "sc_pause", "load_stop"):
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
           cs["astop"]["delay"] if "astop" in cs else -1., p.Cb + E17.C_DMP, .2e-3, P / x0[2],
           1. if cs.get("sc_pause") else 0., 1. if cs.get("load_stop") else 0.]
    assert len(sup) == 71
    prot = [E17.T_HW, E17.I_HW, E17.VL_HW, E17.VS_HW, c["upper"], FTYPE[cs["event"]], E17.T_EV, E17.T_GDF,
            cs.get("event2", 1e30)]
    eps_prm = [1., p.turns, p.Ldab, p.fs, PKD * pk_rated, tab["r0"], tab["dr"], tab["j0"], tab["dj"]]
    init = dict(case=name, vbat=V, P0=P, t_end=t_end, x0=x0[:6].tolist(), vcd0=float(x0[2]),
                u0=u0.tolist(), q0=q0, st0=st0, VW=c["VW"], upper=c["upper"], dab_rated_W=p.power_max, turns=p.turns, Ldab=p.Ldab,
                eta=p.eta, R_bypass=E17.R_BYP, Vd=E17.VD, Rbrk=E17.R_BRK, Rdmp=E17.R_DMP, Cdmp=E17.C_DMP,
                sup_prm=sup, prot_prm=prot, eps_prm=eps_prm, sals_prm=sals_prm(m["sals"]) + [cs.get("load_stop") or 1.],
                event=cs["event"], policy=cs["policy"], rated_pk=pk_rated, pk_max=PKD * pk_rated, C_A=CA_R, ks=KS, mix=mix, scen=sv["loads"],
                sc_pause=bool(cs.get("sc_pause")), load_stop=cs.get("load_stop"),
                foster=dict(zip(("R", "tau"), (list(map(float, FO["R"])), list(map(float, FO["tau"]))))), T_C=E34.T_C_SEMI, T_lim=150.)
    json.dump(init, open(f"TB31_{name}_init.json", "w"), indent=1)
    Lg = tr["log"]; t = tr["t"]
    SLd = E29.rebuild(m["sals"])
    if m["sals"].get("t_pause") is not None:
        SLd.sc_pause(m["sals"]["t_pause"])
        if m["sals"].get("t_resume") is not None:
            SLd.sc_resume(m["sals"]["t_resume"])
    if m["sals"].get("t_stop") is not None:
        SLd.load_stop(m["sals"]["t_stop"], m["sals"]["stop_ramp"])
    pl = np.array([SLd.power(tt, c_ > .5) if vb >= E17.LOAD_MIN_V - 10 else 0. for tt, c_, vb in zip(t, Lg[:, 7], Lg[:, 2])])
    np.savetxt(f"TB31_{name}_avg.csv", np.column_stack([t, Lg[:, :6], Lg[:, 6], Lg[:, 7], Lg[:, 8], Lg[:, 9], pl]), delimiter=",",
               header="t_s,ip,vs,vbus,ih,vlink,idab,ibyp,loads400,bridge,Pbrk,Pload", comments="", fmt="%.9g")
    ch = E29.fault_checks(m) if cs["event"] == "hb_open" else E29.fs_judge(m, tr)[0]
    if cs["event"] == "hb_open":                      # (E38 P6) 바이패스 소프트 투입 소자 EPC2305 1개 온도
        pw = np.abs(Lg[:, 1] * Lg[:, 6]); dTs = E34.foster_dT(FO, t, pw)
        m["P6_Tj"] = float(E34.T_C_SEMI + dTs.max()); m["P6_P_pk_W"] = float(pw.max())
        ch["P6_epc_150C"] = bool(m["P6_Tj"] <= 150.)
    else:
        m["ip_zero_ms"] = E29.fs_judge(m, tr)[1]
    m["checks_tb23"] = ch; m["pass_tb23"] = bool(all(ch.values()))
    json.dump({k: v for k, v in m.items()}, open(f"TB31_{name}_metrics.json", "w"), indent=1, default=float)
    out[name] = dict(pass_=m["pass_tb23"], failed=[k for k, v in ch.items() if not v], events=m["events"],
                     path_peak=m["path_peak"], bridge_peak=m["bridge_peak"], vbus_min=m["vbus_min"], vbus_max=m["vbus_max"],
                     vbus_max_loaded=m["vbus_max_loaded"], vlink_max=m["vlink_max"], brk_energy_J=m["brk_energy_J"],
                     soft_energy_J=m.get("soft_energy_J"), dab_sec_peak=m.get("dab_sec_peak"), t_end=t_end)
    print(name, "PASS" if out[name]["pass_"] else "FAIL", out[name])
json.dump(out, open("TB31_ref_summary.json", "w"), indent=1, default=float)
