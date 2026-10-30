"""[E26] 충전 중 Stage A 정지와 충전기 전류 차단의 협조(R2).

■ 목적
  R2에서 400–500 V급 충전기는 Stage A 출력 노드 V_A에 붙고, Stage A가 2:1로 배터리를 충전한다(375 A, 150 kW).
  충전 중 Stage A가 멈추면 충전기 전류가 갈 곳이 없어 V_A 노드 커패시터로 들어간다. 그러면 V_A가 빠르게 오른다.
  V_A에는 400 V급 보조부품(B_470 상한 470 V)과 조정형 Stage C가 붙어 있다. 충전기는 정지 요청을 받아도 바로 멈추지
  않는다. CHAdeMO(IEEE Std 2030.1.1-2015)는 정지 신호 뒤 30 ms 안에 5 A 이하로 줄이라고 요구한다. 그동안 V_A를
  붙잡을 수단과 정지 순서를 정해야 한다(docs/20 7절, docs/22에서 넘긴 보호 항목).

■ 왜 필요한가
  Stage A 스위치가 모두 꺼지면 바디 다이오드는 V_A > V_bat에서야 도통한다(V_A → S2 → A → S1 → V_bat). 따라서
  400–470 V 부품을 지키는 자연 클램프가 없다. 충전기 정지 요구 시간(30 ms) 동안 375 A가 흐르면 전하는 약 11 C다.
  커패시터로는 받을 수 없으므로, 에너지를 받을 곳(V_A 클램프)과 그것을 쓰는 조건을 정해야 한다.

■ 정지 상황과 순서(시험 전에 정함)
  (P-a) 계획 정지(충전 완료·사용자 정지): 차량이 전류 0을 요청 → 충전기가 줄임 → 5 A 이하에서 접촉기 개방 →
        Stage A는 그 뒤 주행 모드(모듈 셰딩)로. 이 순서에서는 Stage A가 끝까지 동작하므로 V_A 과도가 없다.
  (P-b) 모듈 1개 고장: 고장 모듈만 게이트를 끄고 나머지 3개가 충전전류를 받는다. 차량은 충전 전류 지령을 3/4로
        다시 요청한다(정상 통신). 비상 정지는 하지 않는다. → overload에서 모듈 과부하의 위상 첨두·ZCS를 확인.
  (P-c) 배터리 경로 상실(BMS가 배터리 접촉기 개방, 모듈 2개 이상 고장 등): V_A 클램프(저항 + 스위치, 히스테리시스)를
        켜고 비상 정지 신호를 보낸다 → 충전기 30 ms 안에 5 A 이하 → 5 A 이하에서 차량 DC 접촉기 개방 → 클램프 끔.
        → event에서 V_A 최고, 클램프 에너지·첨두 전력을 계산.

■ 모델
  overload  Stage A 스위칭 ODE(model_stage_a, 영교차 추종, dead_fix=True). 모듈 하나(2위상)에 충전 방향 전류
            375/4·375/3·375/2 A, 배터리 640·800·920 V. 위상 첨두, 턴오프 전류/피크, 모듈 손실.
  event     V_A 노드 평균모델(시간 간격 0.25 µs, 고정 간격 RK4).
            R2 기본형: V_A(C_A 400 µF) — 배선 3 mΩ·1.5 µH — 버스(C_b 400 µF ∥ R_d 48.6 mΩ + C_d 1.6 mF) — 400 V 정전력 부하
                       + Stage C 정전력(입력 5 kW 또는 0). E23·TB16과 같은 버스.
            R2-W: 버스가 Stage B 뒤에 있어 V_A 노드에는 C_A만 있다(가장 빠른 상승).
            Stage A: 동작 중이면 V_A = V_bat/2 + R_A·i_A(R_A = 10.2 mΩ/동작 모듈 수, E16), 정지하면 i_A = 0.
            충전기: 전류원. 정지 신호 뒤 지연 t_comm(0·10 ms)이 지나고 (i) 30 ms 동안 375 A를 유지한 뒤 5 A로(규격이 허용하는
            가장 나쁜 경우) 또는 (ii) 30 ms 선형 감소. 5 A 이하가 되면 차량 접촉기를 연다(충전기 전류 0).
            V_A 클램프: V_A ≥ 468 V에서 켜고 ≤ 463 V에서 끈다(스위치 지연 1 µs), 저항 1.0 Ω(468 V에서 468 A ≥ 375 A).
            문턱은 920 V 충전의 정상 V_A(약 461 V) 위, B_470 상한 아래다.
            비상 정지 신호: Stage A 정지 판정 순간(또는 V_A ≥ 468 V 중 빠른 것).

■ 판정 기준(시험 전에 고정)
  (C1) V_A·버스 ≤ 470 V(B_470 부품 상한), 커넥터 ≤ 600 V(IEEE 2030.1.1 접촉기 차단 전압)
  (C2) 모듈 1개 고장(P-b): 남은 모듈의 위상 첨두 ≤ 1.5 × 76.4 A = 114.6 A, 턴오프 전류/피크 ≤ 5 %
  (C3) 클램프 크기(요구 도출): 흡수 에너지, 첨두 전력, 동작 시간을 보고한다(통과·불통과 대상 아님)
  클램프가 없을 때 V_A가 470·600·650 V(Stage C 650 V GaN)에 닿는 시간도 보고한다.

■ 실행   python E26_charging_stop.py [overload] [event] [figures]   (2코어 약 3분)
■ 결과   results/E26/overload.json, event.json, E26_charging_stop.png
"""
import sys
from multiprocessing import Pool

import numpy as np

import model_stage_a as A
from common import save_json, load_json, outdir, workers

EID = "E26"
I_CH = 375.
RATED_PK = 76.4                    # 위상 정격 첨두 [A](E24)
PK_LIM = 1.5 * RATED_PK            # (C2)
RA_MOD = 10.2e-3                   # 모듈 출력저항(E16)
BUS = dict(CA=400e-6, Rw=3e-3, Lw=1.5e-6, Cb=400e-6, Rd=48.6e-3, Cd=1.6e-3, vmin=200.)
V_LIM = 470.; V_CONN = 600.; V_GAN = 650.
CL = dict(on=468., off=463., R=1.0, delay=1e-6)
# (2026-10-29 정리) 처음 값. 다른 시험(E35–E40)이 같은 프로세스에서 BUS·RA_MOD·CL을 바꾸므로, 클램프 설정은 이 값에서 새로 만들고
# event()·overload()는 시작할 때 처음 값으로 되돌린다(최종 검토 R5).
CL_DEFAULT = dict(CL); BUS_DEFAULT = dict(BUS); RA_DEFAULT = RA_MOD


def reset():
    global CL, RA_MOD
    CL = dict(CL_DEFAULT); BUS.clear(); BUS.update(BUS_DEFAULT); RA_MOD = RA_DEFAULT


def _cl_i(v):
    """클램프 전류. (E39) CL["branches"] = [(R, 강하, 개수), ...]이면 가지별 합, 없으면 이전 식(가지 수 n, 강하 vdrop)."""
    br = CL.get("branches")
    if br:
        return sum(m * max(v - vd, 0.) / R for R, vd, m in br)
    return CL.get("n", 1) * max(v - CL.get("vdrop", 0.), 0.) / CL["R"]


def _cl_p(v):
    """클램프 저항 전력(강하 제외)."""
    br = CL.get("branches")
    if br:
        return sum(m * max(v - vd, 0.) ** 2 / R for R, vd, m in br)
    return CL.get("n", 1) * max(v - CL.get("vdrop", 0.), 0.) ** 2 / CL["R"]
T_STOP = 30e-3                     # 충전기 5 A 이하까지(IEEE 2030.1.1)
T0 = 1e-3                          # 사건 시각
DT = 0.25e-6


# ============================================================================================================
# overload: 모듈 과부하(스위칭 ODE)
# ============================================================================================================
def _ovl(args):
    V, nmod = args
    imod = I_CH / nmod
    r = A.sim_array(N=2, Vbat=V, Iload=-imod, Cbus=400e-6, mode="zcp", ncyc=80, dead_fix=True)
    ph, bus = A.analyze(r)
    return dict(V=V, n_mod=nmod, I_mod=imod, Ipk=max(p["Ipk"] for p in ph), zcs=max(p["zcs"] for p in ph),
                loss_mod=sum(p["Ploss"] for p in ph), VA=bus["Vbus"])


def overload():
    reset()
    jobs = [(V, n) for V in (640., 800., 920.) for n in (4, 3, 2)]
    with Pool(workers()) as p:
        rows = p.map(_ovl, jobs)
    for r in rows:
        r["ok_C2"] = bool(r["Ipk"] <= PK_LIM and r["zcs"] <= 0.05)
    save_json(EID, "overload", dict(rows=rows, PK_LIM=PK_LIM))
    print("모듈 과부하(충전 375 A를 n개 모듈이 받을 때, 모듈 하나):")
    for r in rows:
        print("  %4.0f V, 모듈 %d개: 모듈 %.1f A, 위상 첨두 %.1f A, ZCS %.2f %%, 모듈 손실 %.0f W%s" % (
            r["V"], r["n_mod"], r["I_mod"], r["Ipk"], 100 * r["zcs"], r["loss_mod"],
            "" if r["n_mod"] == 4 else ("  (C2 %s)" % ("통과" if r["ok_C2"] else "불통과"))))
    return rows


# ============================================================================================================
# event: V_A 노드 평균모델
# ============================================================================================================
def run_event(Vbat, P400, PC, arch="R2", clamp=True, prof="hold", t_comm=0., nmod_after=0, tend=60e-3, I0=I_CH,
              t0=T0, t_stop=T_STOP, ich_pwl=None, rec_every=40, full_trace=False):
    """반환: 시간 이력(축약)과 지표. nmod_after: 사건 뒤 동작 모듈 수(0 = 배터리 경로 상실).
    t0: 사건 시각, t_stop: 충전기가 5 A 이하가 되는 시간(규격 30 ms, 회로 대조 TB20은 3 ms로 줄임).
    ich_pwl = (시각, 전류) 구간 선형 충전기 전류(주면 비상 정지·접촉기 논리 대신 이것을 그대로 쓴다. TB20 회로와 같은 정의).
    rec_every: 기록 간격(적분 간격 수), full_trace: True면 기록을 줄이지 않는다."""
    b = BUS
    has_bus = arch == "R2"
    RA4 = RA_MOD / 4
    # 초기 정상상태: V_A = V_bat/2 + R_A·(i_ch − i_load), 버스 = V_A − R_w·i_load
    il = (P400 + PC) / (Vbat / 2)
    Ii = I0 if ich_pwl is None else float(np.interp(0., ich_pwl[0], ich_pwl[1]))
    for _ in range(50):
        vA = Vbat / 2 + RA4 * (Ii - il)
        vb = vA - b["Rw"] * il if has_bus else vA
        il = (P400 + PC) / max(vb, b["vmin"]) if has_bus else (P400 + PC) / max(vA, b["vmin"])
    x = np.array([vA, il, vb, vb]) if has_bus else np.array([vA, 0., vA, vA])   # [vA, iw, vb, vd]
    if not has_bus:
        x[1] = 0.
    t = 0.; n = int(tend / DT)
    clamp_on = False; pend = None              # 클램프 스위치 지연
    # (E40) 선택: CL["t_on_max"] 최대 연속 켜짐 시간(이 시간 켜져 있으면 끈다, 그 뒤 보통 비교기 논리),
    #       CL["force_on_at"] 이 시각에 비교기와 무관하게 게이트를 켠다(오동작 사건). 둘 다 없으면 이전과 같은 계산이다.
    t_on_max = CL.get("t_on_max"); force_at = CL.get("force_on_at"); forced_done = False
    t_on_start = 0.; t_cont_max = 0.; n_forced = 0; n_on_after_forced = 0
    t_sig = None                               # 비상 정지 신호 시각
    contactor_open = False
    E_cl = 0.; Pcl_pk = 0.; t_cl_on = 0.
    rec = []; vA_max = x[0]; vb_max = x[2]
    t_hit = {k: None for k in (V_LIM, V_CONN, V_GAN)}

    def ich(tt):
        if ich_pwl is not None:
            return float(np.interp(tt, ich_pwl[0], ich_pwl[1]))
        if contactor_open:
            return 0.
        if t_sig is None or tt < t_sig + t_comm:
            return I0
        s = tt - (t_sig + t_comm)
        if prof == "hold":
            return I0 if s < t_stop else 5.
        return max(I0 * (1 - s / t_stop), 5.)

    def deriv(xx, tt, running, nmod, cl):
        vA, iw, vb, vd = xx
        iA = (vA - Vbat / 2) / (RA_MOD / nmod) if running else 0.
        icl = _cl_i(vA) if cl else 0.   # (E38) 가지 수 n·스위치 강하(기본 1·0 V), (E39) 가지별 저항·강하
        if has_bus:
            iload = (P400 + PC) / max(vb, b["vmin"])
            id_ = (vb - vd) / b["Rd"]
            dvA = (ich(tt) - iA - iw - icl) / b["CA"]
            diw = (vA - vb - b["Rw"] * iw) / b["Lw"]
            dvb = (iw - iload - id_) / b["Cb"]
            dvd = id_ / b["Cd"]
        else:
            iload = (P400 + PC) / max(vA, b["vmin"])
            dvA = (ich(tt) - iA - iload - icl) / b["CA"]
            diw = dvb = dvd = 0.
        return np.array([dvA, diw, dvb, dvd]), iA, icl

    for k in range(n):
        running = t < t0 or nmod_after > 0
        nmod = 4 if t < t0 else max(nmod_after, 1)
        if t >= t0 and t_sig is None and nmod_after == 0:
            t_sig = t                                          # Stage A 정지 판정 = 비상 정지 신호
        if clamp:
            if force_at is not None and not forced_done and t >= force_at:
                forced_done = True
                if not clamp_on:
                    clamp_on = True; pend = None; t_on_start = t
                    if t_sig is None:
                        t_sig = t
            cut = clamp_on and t_on_max is not None and (t - t_on_start) >= t_on_max
            want = ((x[0] >= CL["on"]) or (clamp_on and x[0] > CL["off"])) and not cut
            if want != clamp_on:
                if pend is None or pend[0] != want:
                    pend = (want, t + CL["delay"])
                elif t >= pend[1]:
                    clamp_on = want; pend = None
                    if clamp_on:
                        t_on_start = t
                        if n_forced:
                            n_on_after_forced += 1
                    else:
                        t_cont_max = max(t_cont_max, t - t_on_start)
                        if cut:
                            n_forced += 1
                    if clamp_on and t_sig is None:
                        t_sig = t
            else:
                pend = None
        if ich_pwl is None and not contactor_open and t_sig is not None and ich(t) <= 5. and t > t_sig:
            contactor_open = True
        k1, iA, icl = deriv(x, t, running, nmod, clamp_on)
        k2, _, _ = deriv(x + DT / 2 * k1, t + DT / 2, running, nmod, clamp_on)
        k3, _, _ = deriv(x + DT / 2 * k2, t + DT / 2, running, nmod, clamp_on)
        k4, _, _ = deriv(x + DT * k3, t + DT, running, nmod, clamp_on)
        x = x + DT / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        t += DT
        if clamp_on:
            p = _cl_p(x[0]); E_cl += p * DT; Pcl_pk = max(Pcl_pk, p); t_cl_on += DT
        vA_max = max(vA_max, x[0]); vb_max = max(vb_max, x[2])
        for lim in t_hit:
            if t_hit[lim] is None and x[0] >= lim:
                t_hit[lim] = t - t0
        if k % rec_every == 0:
            rec.append((t, x[0], x[2], ich(t), iA, icl))
        if x[0] > 2000.:                                       # 클램프 없음: 발산 확인 뒤 중단
            break
    rec = np.array(rec)
    if clamp_on:
        t_cont_max = max(t_cont_max, t - t_on_start)
    return dict(Vbat=Vbat, P400=P400, PC=PC, arch=arch, clamp=clamp, prof=prof, t_comm=t_comm, nmod_after=nmod_after,
                t_on_cont_max_ms=1e3 * t_cont_max, n_forced_off=n_forced, n_on_after_forced=n_on_after_forced,
                clamp_on_end=bool(clamp_on),
                vA0=float(rec[0, 1]), vA_max=float(vA_max), vb_max=float(vb_max), E_clamp_J=E_cl, P_clamp_pk_W=Pcl_pk,
                t_clamp_on_ms=1e3 * t_cl_on, t_hit_ms={str(int(k)): (None if v is None else 1e3 * v) for k, v in t_hit.items()},
                ok_C1=bool(vA_max <= V_LIM and vb_max <= V_LIM),
                trace=(rec if (full_trace or (Vbat == 920. and P400 == 0.)) else rec[::20]).tolist())


EVENTS = []
for arch in ("R2", "R2W"):
    for Vb in (640., 920.):
        for P400, PC in ((0., 0.), (20e3, 5e3)):
            EVENTS.append(dict(Vbat=Vb, P400=P400, PC=PC, arch=arch, clamp=False, prof="hold", t_comm=0., tend=5e-3))
            for prof in ("hold", "ramp"):
                for tc in (0., 10e-3):
                    EVENTS.append(dict(Vbat=Vb, P400=P400, PC=PC, arch=arch, clamp=True, prof=prof, t_comm=tc,
                                       tend=(T_STOP + tc + 8e-3)))
# 모듈 1개 고장(P-b): 평균모델로 V_A 변화만 확인(비상 정지 없음)
for Vb in (640., 920.):
    EVENTS.append(dict(Vbat=Vb, P400=20e3, PC=5e3, arch="R2", clamp=True, prof="hold", t_comm=0., nmod_after=3, tend=5e-3))


def _ev(kw):
    return run_event(**kw)


def event():
    reset()
    with Pool(workers()) as p:
        rows = p.map(_ev, EVENTS)
    save_json(EID, "event", dict(rows=rows, CL=CL, BUS=BUS, T_STOP=T_STOP))
    # (2026-10-29 정리) 이력을 뺀 요약. E36 e26이 이 파일을 읽는다(이전에는 따로 만든 파일이었다)
    save_json(EID, "event_summary", dict(rows=[{k: v for k, v in r.items() if k != "trace"} for r in rows], CL=CL, BUS=BUS, T_STOP=T_STOP))
    print("사건(배터리 경로 상실 또는 모듈 고장):")
    for r in rows:
        tag = "%s %4.0f V 부하 %2.0f+%1.0f kW %s %s t_comm %2.0f ms 모듈 %d" % (
            r["arch"], r["Vbat"], r["P400"] / 1e3, r["PC"] / 1e3, "클램프" if r["clamp"] else "클램프 없음",
            r["prof"], 1e3 * r["t_comm"], r["nmod_after"])
        if r["clamp"] or r["nmod_after"]:
            print("  %s: V_A %.1f → 최고 %.1f V, 버스 최고 %.1f V, 클램프 %.0f J·첨두 %.0f kW·%.1f ms  (C1 %s)" % (
                tag, r["vA0"], r["vA_max"], r["vb_max"], r["E_clamp_J"], r["P_clamp_pk_W"] / 1e3, r["t_clamp_on_ms"],
                "통과" if r["ok_C1"] else "불통과"))
        else:
            h = r["t_hit_ms"]
            print("  %s: V_A %.1f V, 470 V까지 %s ms, 600 V %s ms, 650 V %s ms" % (
                tag, r["vA0"], *["%.3f" % h[k] if h[k] is not None else "–" for k in ("470", "600", "650")]))
    return rows


def figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    ev = load_json(EID, "event")["rows"]
    ov = load_json(EID, "overload")["rows"]
    fig, ax = plt.subplots(1, 3, figsize=(14, 3.9))
    for r, col, lab in ((next(x for x in ev if x["arch"] == "R2" and x["Vbat"] == 920. and x["P400"] == 0. and not x["clamp"]),
                         C["red"], "클램프 없음(R2 기본형)"),
                        (next(x for x in ev if x["arch"] == "R2W" and x["Vbat"] == 920. and x["P400"] == 0. and not x["clamp"]),
                         C["orange"], "클램프 없음(R2-W, C_A만)")):
        tr = np.array(r["trace"])
        ax[0].plot(1e3 * (tr[:, 0] - T0), tr[:, 1], color=col, label=lab)
    ax[0].axhline(V_LIM, color="k", ls=":"); ax[0].axhline(V_GAN, color="k", ls="--", lw=0.8)
    ax[0].set_xlim(-0.2, 3); ax[0].set_ylim(440, 700); ax[0].set_xlabel("배터리 경로 상실 뒤 시간 [ms]"); ax[0].set_ylabel("V_A [V]")
    ax[0].set_title("(a) 920 V 충전 375 A, 부하 0: 클램프 없음"); ax[0].legend()
    r = next(x for x in ev if x["arch"] == "R2" and x["Vbat"] == 920. and x["P400"] == 0. and x["clamp"] and x["prof"] == "hold"
             and x["t_comm"] == 0.)
    tr = np.array(r["trace"])
    a2 = ax[1].twinx()
    ax[1].plot(1e3 * (tr[:, 0] - T0), tr[:, 1], color=C["blue"], lw=0.4, label="V_A")
    a2.plot(1e3 * (tr[:, 0] - T0), tr[:, 3], color=C["green"], label="충전기 전류")
    w = 20                                                       # 200 µs 이동평균(클램프는 수십 µs 주기로 켜고 끈다)
    icl_avg = np.convolve(tr[:, 5], np.ones(w) / w, mode="same")
    a2.plot(1e3 * (tr[:, 0] - T0), icl_avg, color=C["orange"], label="클램프 전류(200 µs 평균)")
    a2.grid(False); a2.set_ylabel("[A]")
    ax[1].set_xlabel("시간 [ms]"); ax[1].set_ylabel("V_A [V]"); ax[1].set_ylim(455, 472)
    ax[1].set_title("(b) 클램프 468/463 V·1 Ω, 충전기 30 ms 유지 뒤 정지")
    h1, l1 = ax[1].get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels(); ax[1].legend(h1 + h2, l1 + l2, loc="lower right")
    for n, mk in ((4, "o"), (3, "s"), (2, "^")):
        rr = [x for x in ov if x["n_mod"] == n]
        ax[2].plot([x["V"] for x in rr], [x["Ipk"] for x in rr], marker=mk, label="모듈 %d개" % n)
    ax[2].axhline(PK_LIM, color="k", ls=":", label="1.5 × 정격 첨두")
    ax[2].set_xlabel("배터리 [V]"); ax[2].set_ylabel("위상 첨두 [A]"); ax[2].set_title("(c) 충전 375 A, 남은 모듈 수별 위상 첨두")
    ax[2].legend()
    fig.tight_layout(); fig.savefig(outdir(EID) / "E26_charging_stop.png"); plt.close(fig)


PARTS = dict(overload=overload, event=event, figures=figures)

if __name__ == "__main__":
    for name in (sys.argv[1:] or list(PARTS)):
        PARTS[name]()
