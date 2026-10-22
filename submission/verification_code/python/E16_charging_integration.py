"""[E16] 충전 중 보조버스(H3) — 평균모델 검증(보고서 이후 추가 검증).

■ 목적
  400 V급 급속충전(충전기 375 A, 최대 150 kW) 중에도 Stage B가 400 V 보조버스를 조정하고(H3), 충전 대전류가
  Stage B를 지나지 않는지(H1의 충전 부분)를 확인한다. 충전기 접속·해제와 Stage A 모듈 기동·셰딩 같은
  모드 전환에서 버스전압과 소자 전류 한계를 지키는지도 판정한다.

■ 왜 필요한가
  지금까지의 Stage B 검증(E5–E7, E12)은 주행 모드, 즉 Stage A 모듈 1개(2위상)가 V_A를 만드는 경우만 다뤘다.
  충전 중에는 두 가지가 달라진다.
    (1) Stage A 4모듈이 모두 동작해 V_A의 출력저항이 10.2 → 2.55 mΩ으로 작아진다. 제어기는 공칭 경로저항
        13.2 mΩ(모듈 1 + 배선)을 쓰므로, 플랜트의 경로저항 5.55 mΩ은 공칭의 42 %다. E7의 공차(±10 %)를
        크게 벗어나며, 경로저항은 경로 L–버스 C 공진의 자연 감쇠를 정한다.
    (2) 충전기가 V_A 노드에 전류를 넣는다. V_A = V_bat/2 + R_A·(i_ch − i_p)이므로 충전전류가 바뀌면
        경로 전원이 R_A·Δi_ch(375 A에서 약 0.96 V)만큼 계단처럼 움직인다. 비상 정지처럼 충전전류가
        갑자기 끊기는 경우가 가장 빠른 외란이다.
  충전기는 V_A에 직접 붙고 400 V 버스는 직렬 포트 뒤에 있으므로, 충전전류는 구조상 Stage B를 지나지 않는다.
  남는 질문은 위 두 변화에서 제어기를 바꾸지 않고(모드 정보 없이) 기준을 지키는가다.

■ 모델
  Stage B 6상태 평균모델(model_stage_b.simulate)과 채택 제어기(E5–E7과 같음, 공칭 파라미터·이득 고정).
  경로 전원만 바꾼다(source_fn):
      L di_p/dt = v_src(t) − R(t)·i_p + v_s − v_bus,   v_src = V_bat/2 + R_A(n)·i_ch(t),   R = R_A(n) + R_w
      R_A(n) = 10.2 mΩ / n (동작 모듈 수 n, 설계검증서·TB06의 모듈 출력저항),  R_w = 3.0 mΩ(배선)
  충전기는 CCS 충전기처럼 스스로 전류를 제어하는 전류원으로 둔다(전류 지령 프로파일을 그대로 따름).
  V_A 노드 커패시터(400 µF)와 R_A의 시정수(약 1 µs)는 제어주기(5 µs)보다 짧아 정적 관계로 둔다.
  충전전류 상한 i_ch,max = min(375 A, 150 kW / (V_bat/2)).

■ 구성
  static      정적 범위: V_bat 632·640–920 V × 부하 −3.2–25 kW(200 W) × 모드(주행 n = 1, 충전 n = 4·i_ch,max).
              직렬전압, 링크전력, 경로전류, 변조율, 충전기 단자전압 V_A, 배터리 충전전류, ④(버스 = V_A) 버스 범위
  concurrent  충전 중 Tier-1·Tier-2: E5와 같은 구성(7개 전압 × 공칭·지연 +3.0 µs, 640·920 V × 단일 변수 공차 16종)
              × Tier-1 스텝 10종·Tier-2 스텝 2종 = 552건. 플랜트 경로저항은 충전값 × 공차 배율.
              판정 범위는 H2(E5)와 같다: Tier-1 460건(지연 포함), Tier-2 78건(지연 없음). 지연 +3.0 µs의 Tier-2 14건은 정보
  transition  모드 전환(Tier-2 판정) × 5개 전압 × 부하 4종(−3.2·1·10·25 kW) × 공칭·지연 +3.0 µs:
              charger_on_step   충전전류 0 → i_ch,max, 10 µs(경계 사례)       charger_on_ramp   같은 변화, 1 ms
              charger_off_step  i_ch,max → 0, 10 µs(비상 정지·접속 해제)    charger_off_ramp  같은 변화, 1 ms
              modules_up        모듈 1 → 4(1 ms 간격 순차 기동, 충전전류 0)  modules_down      모듈 4 → 1
  sequence    전체 순서 1회: 주행 → 모듈 기동(1·2·3 ms) → 충전전류 1 ms 램프(4–5 ms) → 충전 중 +10 kW 계단(8 ms)
              → 충전 비상 정지(12 ms, 10 µs) → 모듈 셰딩(15·16·17 ms). 5개 전압 × 시작 부하 3종 × 공칭·지연
  switching   스위칭 모델(E12 엔진, 5 ns): 충전 중 Tier-1·Tier-2(640·788·920 V, 공칭 36건, 지연 +3.0 µs Tier-2 4건),
              충전기 접속·비상 정지 10 µs(640·920 V × 1·25 kW, 8건). 판정은 E12와 같다(순시 98·100 A)
  variants    가장 불리한 Tier-2 사례(1 → 25 kW, 지연 +3.0 µs)에서 충전 모드를 아는 제어기와 비교, 저하 운전 영역 632 V를
              기준전압 390 V(docs/14 D4)로 운전할 때
  figures     대표 파형

■ 판정(docs/14 H3 기준)
  동시 운전: E5와 같은 Tier-1(전압 품질 6항목 + 경로·필터 ≤ 90 A), Tier-2(경로·필터 ≤ 93.75 A, 버스 384–416 V,
            20 ms 시점 400 ± 4 V). 공통으로 포트 물리 한계와 내부 진동 검사.
  모드 전환·전체 순서: Tier-2 기준. Tier-1 전압 품질 항목은 정보로 기록한다.
  정적: 직렬 ±90 V, 링크 ≤ 8 kW, 경로 ≤ 84 A(지령 포화값), 변조율 ≤ 0.95, 충전기 단자 V_A ∈ 200–500 V.

■ 실행   python E16_charging_integration.py                    (전체, 2코어 약 20분)
         python E16_charging_integration.py static transition    (일부)
■ 결과   results/E16/*.json, results/E16/E16_*.png

■ 보고서 수치(2026-10-22 실행)
  정적: 640–920 V × −3.2–25 kW 4,118점 성립, 직렬 −60.9 ~ +83.5 V, 링크 ≤ 6.68 kW, 충전기 단자 316.8–460.8 V
  동시 운전: Tier-1 460/460(최대 87.43 A), Tier-2 78/78(최대 92.74 A). 정보: Tier-2 + 지연 +3.0 µs 13/14(632 V 93.96 A,
            주행 모드 같은 조건 94.08 A)
  모드 전환 240/240(최대 86.83 A), 전체 순서 30/30(최대 87.04 A), 스위칭 모델 48/48(순시 최대 96.26 A)
  변형: 충전 모드를 아는 제어기는 Tier-2 + 지연에서 1.3 A 나쁨(94.93 대 93.62 A, 640 V) → 제어기는 바꾸지 않는다

■ 한계
  평균모델이다. Stage A는 테브난 등가(V_bat/2, R_A)이고 모듈 기동은 출력저항의 계단 변화로 둔다(실제로는 모듈당
  1 ms 소프트스타트라 더 완만하다). 충전기 동특성은 지령 프로파일로 대신하고, 충전기 출력 필터·케이블과의 상호작용,
  Stage A 정지 중 충전전류(보호 영역)는 다루지 않는다. Stage A는 정적 등가라 V_A 노드 공진(C_A–Stage A 공진 회로,
  주기 약 30 µs, 회로 모델 TB07)이 없으므로, 충전전류 변화가 100 µs보다 빠르면 경로전류 첨두를 작게 본다.
"""
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np

from common import save_json, outdir, workers, verdict
from controller_adopted import make, K_ADOPTED, CP
from controller_reference import NOMINAL, assess
from model_stage_b import simulate, equilibrium, steady_feasible, current_limit
import stage_b_tests as T

EID = "E16"
RA_MOD = 10.2e-3          # Stage A 모듈(2위상) 출력저항 [Ω] — 스위칭 모델 E1·TB06에서 확인
RW = 3.0e-3               # V_A → 직렬 포트 배선 [Ω]
NMOD = 4                  # 충전 중 동작 모듈 수
ICH_MAX, PCH_MAX = 375., 150e3
V_TR = [640., 700., 788., 860., 920.]          # 모드 전환 시험 전압
LOADS_TR = [-3200., 1000., 10000., 25000.]
T_EDGE = 1e-3                                   # 전환 시작 시각


def ra(n):
    return RA_MOD / n


def ich_max(V):
    """충전전류 상한: 375 A, 150 kW(충전기 단자 약 V_bat/2 기준) 중 작은 값."""
    return min(ICH_MAX, PCH_MAX / (V / 2))


class Source:
    """경로 전원 프로파일(피클 가능). ich: [(t, i_ch)] 구간 선형, nmod: [(t, n)] 계단, f: 경로저항 공차 배율."""
    def __init__(self, V, ich, nmod, f=1.0):
        self.V = V; self.ti = np.array([a for a, _ in ich]); self.ii = np.array([b for _, b in ich])
        self.tn = [a for a, _ in nmod]; self.nn = [b for _, b in nmod]; self.f = f

    def ich(self, t):
        return float(np.interp(t, self.ti, self.ii))

    def n(self, t):
        k = 0
        for j, tj in enumerate(self.tn):
            if t >= tj:
                k = j
        return self.nn[k]

    def __call__(self, t):
        n = self.n(t)
        return self.V / 2 + ra(n) * self.f * self.ich(t), (ra(n) + RW) * self.f


class Load:
    """부하 프로파일(계단, 피클 가능): [(t, P)]"""
    def __init__(self, pts):
        self.pts = pts

    def __call__(self, t):
        P = self.pts[0][1]
        for tj, Pj in self.pts:
            if t >= tj:
                P = Pj
        return P


def unreg_bus(vsrc, R, P):
    """④(버스 = V_A, 직렬 포트 없음)의 정상 버스전압: v·i = P, v = v_src − R·i."""
    ip = (vsrc - np.sqrt(vsrc ** 2 - 4 * R * P)) / (2 * R)
    return float(vsrc - R * ip)


# --------------------------------------------------------------------------------------
# 1. 정적 범위
# --------------------------------------------------------------------------------------
def static():
    Vs = [632.] + list(np.arange(640., 921., 10.))
    Ps = np.arange(-3200., 25001., 200.)
    out = {}
    for mode in ("drive", "charge"):
        rows = []
        for V in Vs:
            n = 1 if mode == "drive" else NMOD
            ich = 0. if mode == "drive" else ich_max(V)
            vsrc = V / 2 + ra(n) * ich; p = replace(NOMINAL, R=ra(n) + RW)
            for P in Ps:
                x, u = equilibrium(2 * vsrc, P, p)
                ip, vs = x[0], x[1]
                vA = V / 2 + ra(n) * (ich - ip)
                rows.append(dict(V=V, P=P, ich=ich, ip=ip, vs=vs, plink=x[4] * x[5], m=u[0], vA=vA,
                                 ibat=(ich - ip) / 2 if mode == "charge" else -ip / 2,
                                 feasible=steady_feasible(2 * vsrc, P, p),
                                 vA_unreg=unreg_bus(vsrc, ra(n) + RW, P)))
        a = lambda k: np.array([r[k] for r in rows])
        main = a("V") >= 640
        out[mode] = dict(
            n_points=len(rows), feasible=int(sum(r["feasible"] for r in rows)),
            feasible_640_920=int(sum(r["feasible"] for r in rows if r["V"] >= 640)), n_640_920=int(main.sum()),
            series_V=[float(a("vs").min()), float(a("vs").max())],
            link_kW_max=float(np.abs(a("plink")).max() / 1e3), path_A_max=float(np.abs(a("ip")).max()),
            mod_max=float(np.abs(a("m")).max()), vA_range=[float(a("vA").min()), float(a("vA").max())],
            ibat_range=[float(a("ibat").min()), float(a("ibat").max())],
            unreg_bus_range=[float(a("vA_unreg")[main].min()), float(a("vA_unreg")[main].max())],
            link_at_640_25kW=float([r["plink"] for r in rows if r["V"] == 640 and abs(r["P"] - 25000) < 1][0] / 1e3),
            series_at_640_25kW=float([r["vs"] for r in rows if r["V"] == 640 and abs(r["P"] - 25000) < 1][0]))
    d, c = out["drive"], out["charge"]
    print("정적 범위(주행 / 충전):")
    for k in ("feasible_640_920", "series_V", "link_kW_max", "path_A_max", "mod_max", "vA_range", "ibat_range", "unreg_bus_range"):
        print("  %-18s %s / %s" % (k, np.round(d[k], 3), np.round(c[k], 3)))
    ok = (c["feasible_640_920"] == c["n_640_920"] and c["link_kW_max"] <= 8 and abs(c["series_V"][0]) <= 90
          and c["series_V"][1] <= 90 and 200 <= c["vA_range"][0] and c["vA_range"][1] <= 500)
    verdict("E16 정적(충전 중 640–920 V × −3.2–25 kW 전부 성립, 링크 ≤ 8 kW, 충전기 단자 200–500 V)", ok)
    out["pass_"] = bool(ok)
    save_json(EID, "static", out)
    return out


# --------------------------------------------------------------------------------------
# 2. 동특성 공통 실행
# --------------------------------------------------------------------------------------
def run_case(job):
    """job = (구분, 이름, 등급, V_bat, 플랜트 Parameters, Source, Load, 정보 dict)"""
    kind, name, tier, V, p, src, load, info = job
    dt = 1e-7 if abs(p.delay / 2e-7 - round(p.delay / 2e-7)) > 1e-9 else 2e-7
    t0 = time.time()
    r = simulate(V, load(0.), load(0.), p=p, K=K_ADOPTED, control_p=CP, duration=.02, dt=dt, keep_trace=True,
                 controller=make(V), power_fn=load, source_fn=src, step=T_EDGE)
    r.update(assess(r["t"], r["x"], T_EDGE, r["completed"], r["within_port_limits"]))
    row = T.judge(tier, r)
    t = r["t"]; ip = r["x"][:, 0]
    ich = np.interp(t, src.ti, src.ii)
    nn = np.array(src.nn)[np.searchsorted(src.tn, t, side="right") - 1]        # 시각별 동작 모듈 수
    vA = V / 2 + RA_MOD / nn * src.f * (ich - ip)                             # 충전기 단자(= V_A)
    row.update(kind=kind, name=name, tier=tier, V=V, info=info, vA_min=float(vA.min()), vA_max=float(vA.max()),
               voltage_quality_pass=bool(r["requirements_pass"]), wall_s=time.time() - t0)
    return row


def params(name, base):
    """충전 중 플랜트: 공차 집합의 R 배율을 충전 경로저항에 적용한다(나머지 공차는 그대로)."""
    f = base.R / NOMINAL.R
    return replace(base, R=(ra(NMOD) + RW) * f), f


def concurrent_jobs():
    sets, tol = T.param_sets()
    js = []
    def add(V, name, base):
        p, f = params(name, base)
        src = Source(V, [(0., ich_max(V))], [(0., NMOD)], f)
        for a, b in T.T1_STEPS:
            js.append(("concurrent", name, 1, V, p, src, Load([(0., a), (T_EDGE, b)]), dict(P0=a, P1=b)))
        for a, b in T.T2_STEPS:
            js.append(("concurrent", name, 2, V, p, src, Load([(0., a), (T_EDGE, b)]), dict(P0=a, P1=b)))
    for V in T.V_ALL:
        for name, base in sets.items():
            add(float(V), name, base)
    for V in T.V_TOL:
        for name, base in tol.items():
            add(float(V), name, base)
    return js


def transition_jobs():
    sets, _ = T.param_sets()
    js = []
    for V in V_TR:
        im = ich_max(V)
        prof = {
            "charger_on_step": ([(0., 0.), (T_EDGE, 0.), (T_EDGE + 10e-6, im)], [(0., NMOD)]),
            "charger_on_ramp": ([(0., 0.), (T_EDGE, 0.), (T_EDGE + 1e-3, im)], [(0., NMOD)]),
            "charger_off_step": ([(0., im), (T_EDGE, im), (T_EDGE + 10e-6, 0.)], [(0., NMOD)]),
            "charger_off_ramp": ([(0., im), (T_EDGE, im), (T_EDGE + 1e-3, 0.)], [(0., NMOD)]),
            "modules_up": ([(0., 0.)], [(0., 1), (T_EDGE, 2), (T_EDGE + 1e-3, 3), (T_EDGE + 2e-3, 4)]),
            "modules_down": ([(0., 0.)], [(0., 4), (T_EDGE, 3), (T_EDGE + 1e-3, 2), (T_EDGE + 2e-3, 1)]),
        }
        for kind, (ich, nm) in prof.items():
            for P in LOADS_TR:
                for name, base in sets.items():
                    js.append((kind, name, 2, V, base, Source(V, ich, nm), Load([(0., P)]), dict(P=P)))
    return js


def sequence_jobs():
    sets, _ = T.param_sets()
    js = []
    for V in V_TR:
        im = ich_max(V)
        ich = [(0., 0.), (4e-3, 0.), (5e-3, im), (12e-3, im), (12e-3 + 10e-6, 0.)]
        nm = [(0., 1), (1e-3, 2), (2e-3, 3), (3e-3, 4), (15e-3, 3), (16e-3, 2), (17e-3, 1)]
        for P0 in (5000., 12500., 15000.):
            for name, base in sets.items():
                js.append(("sequence", name, 2, V, base, Source(V, ich, nm), Load([(0., P0), (8e-3, P0 + 10000.)]),
                           dict(P0=P0, P1=P0 + 10000.)))
    return js


def run_jobs(tag, js):
    t0 = time.time()
    with ProcessPoolExecutor(workers()) as ex:
        rows = list(ex.map(run_case, js, chunksize=2))
    print("  %s: %d건, %.0f s" % (tag, len(rows), time.time() - t0))
    return rows


def summarize(rows, by=("kind", "tier")):
    out = {}
    for r in rows:
        key = "|".join(str(r[k]) for k in by)
        s = out.setdefault(key, dict(n=0, passed=0, path_max=0., bus_min=1e9, bus_max=0., vq_pass=0, vA_min=1e9, vA_max=0.,
                                     link_max=0., failed=[]))
        s["n"] += 1; s["passed"] += int(r["pass_"]); s["vq_pass"] += int(r["voltage_quality_pass"])
        s["path_max"] = max(s["path_max"], r["path_peak"], r["bridge_peak"])
        s["bus_min"] = min(s["bus_min"], r["vbus_min_post"]); s["bus_max"] = max(s["bus_max"], r["vbus_max_post"])
        s["vA_min"] = min(s["vA_min"], r["vA_min"]); s["vA_max"] = max(s["vA_max"], r["vA_max"])
        s["link_max"] = max(s["link_max"], r["link_peak"])
        if not r["pass_"]:
            s["failed"].append(dict(name=r["name"], V=r["V"], info=r["info"], failed=r["failed"]))
    return out


def concurrent_summary(rows):
    """판정 범위는 H2(E5)와 같다: Tier-1은 공차·지연 +3.0 µs 포함 460건, Tier-2는 지연 없는 78건.
    지연 +3.0 µs의 Tier-2 14건은 정보로 기록한다(주행 모드 E5에서도 같은 범위로 판정했고, 그 최대는 94.08 A)."""
    for r in rows:
        r["delay"] = r["name"] == "delay+3.0us"
    s = summarize(rows, by=("kind", "tier", "delay"))
    judged = [k for k in s if not k.endswith("|2|True")]
    for k, v in s.items():
        print("  %-22s %d/%d 통과, 최대 전류 %.2f A, 버스 %.2f–%.2f V%s" % (k, v["passed"], v["n"], v["path_max"], v["bus_min"],
                                                                     v["bus_max"], "" if k in judged else " (정보)"))
    ok = all(s[k]["passed"] == s[k]["n"] for k in judged)
    return s, judged, ok


def concurrent():
    rows = run_jobs("concurrent", concurrent_jobs())
    s, judged, ok = concurrent_summary(rows)
    verdict("E16 충전 중 동시 운전: Tier-1 460건(지연 포함)·Tier-2 78건", ok)
    save_json(EID, "concurrent", dict(summary=s, judged=judged, rows=rows, pass_=ok,
                                      note="Tier-2 with +3.0 us delay is information only (same scope as H2/E5)"))
    return s


def transition():
    rows = run_jobs("transition", transition_jobs())
    s = summarize(rows, by=("kind",))
    for k, v in s.items():
        print("  %-17s %d/%d 통과(Tier-2), 전압 품질 %d/%d, 최대 전류 %.2f A, 버스 %.2f–%.2f V, V_A %.2f–%.2f V"
              % (k, v["passed"], v["n"], v["vq_pass"], v["n"], v["path_max"], v["bus_min"], v["bus_max"], v["vA_min"], v["vA_max"]))
    ok = all(v["passed"] == v["n"] for v in s.values())
    verdict("E16 모드 전환(충전기 접속·해제, 모듈 기동·셰딩) Tier-2", ok)
    save_json(EID, "transition", dict(summary=s, rows=rows, pass_=ok))
    return s


def sequence():
    rows = run_jobs("sequence", sequence_jobs())
    s = summarize(rows, by=("kind",))
    for k, v in s.items():
        print("  %-17s %d/%d 통과(Tier-2), 전압 품질 %d/%d, 최대 전류 %.2f A, 버스 %.2f–%.2f V"
              % (k, v["passed"], v["n"], v["vq_pass"], v["n"], v["path_max"], v["bus_min"], v["bus_max"]))
    ok = all(v["passed"] == v["n"] for v in s.values())
    verdict("E16 전체 순서(주행 → 충전 → 비상 정지 → 주행)", ok)
    save_json(EID, "sequence", dict(summary=s, rows=rows, pass_=ok))
    return s


# --------------------------------------------------------------------------------------
# 3. 스위칭 모델(E12 엔진) 대표 사례
# --------------------------------------------------------------------------------------
def _sw_case(job):
    """job = (구분, 이름, 등급, V_bat, 플랜트 Parameters, P0, P1, 시작 충전전류, 끝 충전전류, 전환 시각)"""
    from model_stage_b_switching import simulate_switching
    from E12_switching_verification import judge_sw
    kind, name, tier, V, p, P0, P1, i0, i1, t_sw = job
    vb0 = V + 2 * ra(NMOD) * i0; vb1 = V + 2 * ra(NMOD) * i1          # 플랜트 경로 전원 2·v_src
    sw = dict(ctrl_vbat=V)
    if i0 != i1:
        sw.update(src_t0=t_sw, src_t1=t_sw + 10e-6, src_vbat1=vb1)
    t0 = time.time()
    r = simulate_switching(vb0, P0, P1, p, CP, K_ADOPTED, predict=True, sw=sw)
    row = dict(kind=kind, name=name, tier=tier, V=V, P0=P0, P1=P1, ich0=i0, ich1=i1)
    row.update(judge_sw(tier, r, p)); row["wall_s"] = time.time() - t0
    return row


def switching():
    """충전 중 동시 운전(Tier-1·Tier-2)과 충전기 접속·비상 정지(10 µs)를 스위칭 모델로 확인한다.
    판정은 E12와 같다(순시 Tier-1 ≤ 98 A, Tier-2 ≤ 100 A, 전압은 5 µs 주기 평균)."""
    sets, _ = T.param_sets()
    js = []
    for V in (640., 788., 920.):
        im = ich_max(V)
        p, _f = params("nominal", NOMINAL)
        js += [("concurrent", "nominal", 1, V, p, a, b, im, im, 1.) for a, b in T.T1_STEPS]
        js += [("concurrent", "nominal", 2, V, p, a, b, im, im, 1.) for a, b in T.T2_STEPS]
    for V in (640., 920.):
        im = ich_max(V)
        p, _f = params("delay+3.0us", sets["delay+3.0us"])
        js += [("concurrent", "delay+3.0us", 2, V, p, a, b, im, im, 1.) for a, b in T.T2_STEPS]
        for P in (1000., 25000.):
            pn, _f = params("nominal", NOMINAL)
            js.append(("charger_on_step", "nominal", 2, V, pn, P, P, 0., im, 1e-3))
            js.append(("charger_off_step", "nominal", 2, V, pn, P, P, im, 0., 1e-3))
    t0 = time.time()
    with ProcessPoolExecutor(workers()) as ex:
        rows = list(ex.map(_sw_case, js, chunksize=1))
    print("  switching: %d건, %.0f s" % (len(rows), time.time() - t0))
    s = {}
    for r in rows:
        k = "%s|%s|T%d" % (r["kind"], r["name"], r["tier"])
        v = s.setdefault(k, dict(n=0, passed=0, inst_max=0., avg_max=0., bus_min=1e9, bus_max=0., failed=[]))
        v["n"] += 1; v["passed"] += int(r["pass_"])
        v["inst_max"] = max(v["inst_max"], r["path_inst"], r["bridge_inst"]); v["avg_max"] = max(v["avg_max"], r["path_avg"], r["bridge_avg"])
        v["bus_min"] = min(v["bus_min"], r["vbus_min_post"]); v["bus_max"] = max(v["bus_max"], r["vbus_max_post"])
        if not r["pass_"]:
            v["failed"].append(dict(V=r["V"], P0=r["P0"], P1=r["P1"], ports=r["ports_violated"]))
    for k, v in s.items():
        print("  %-30s %d/%d 통과, 순시 최대 %.2f A(주기 평균 %.2f A), 버스 %.2f–%.2f V" % (k, v["passed"], v["n"], v["inst_max"], v["avg_max"], v["bus_min"], v["bus_max"]))
    ok = all(v["passed"] == v["n"] for v in s.values())
    verdict("E16 스위칭 모델: 충전 중 동시 운전·충전기 접속·비상 정지", ok)
    save_json(EID, "switching", dict(summary=s, rows=rows, pass_=ok))
    return s


# --------------------------------------------------------------------------------------
# 4. 설계 변형 확인(가장 불리한 Tier-2 사례)
# --------------------------------------------------------------------------------------
def variants():
    """(1) 충전 모드를 아는 제어기(예측 모델의 경로저항 5.55 mΩ, V_bat 대신 충전 경로 전원)와 그대로 쓰는 제어기 비교,
    (2) 저하 운전 영역(632 V)에서 기준전압 390 V(docs/14 D4)로 운전할 때. 모두 지연 +3.0 µs, Tier-2 1 → 25 kW."""
    from controller_adopted import StageBController
    out = []
    for V, vref in ((632., 400.), (640., 400.), (632., 390.)):
        base = replace(NOMINAL, delay=NOMINAL.delay + T.DELAY_BUDGET, vref=vref)
        p, f = params("delay+3.0us", base)
        src = Source(V, [(0., ich_max(V))], [(0., NMOD)], f)
        load = Load([(0., 1000.), (T_EDGE, 25000.)])
        cp0 = replace(CP, vref=vref)
        modes = [("unchanged", StageBController(K_ADOPTED, cp0, V, predict=True))]
        if vref == 400.:
            modes.append(("mode_aware", StageBController(K_ADOPTED, replace(cp0, R=ra(NMOD) + RW),
                                                         V + 2 * ra(NMOD) * ich_max(V), predict=True)))
        for mode, c in modes:
            r = simulate(V, 1000., 1000., p=p, K=K_ADOPTED, control_p=cp0, duration=.02, dt=2e-7, keep_trace=True,
                         controller=c, power_fn=load, source_fn=src, step=T_EDGE)
            post = r["x"][r["t"] >= T_EDGE, 2]
            row = dict(V=V, vref=vref, controller=mode, path_peak=r["path_peak"], bridge_peak=r["bridge_peak"],
                       vbus_min=float(post.min()), vbus_max=float(post.max()), vbus_end=float(r["x"][-1, 2]),
                       ports_ok=bool(r["within_port_limits"]),
                       pass_current=bool(max(r["path_peak"], r["bridge_peak"]) <= T.T2_LIMIT_A),
                       pass_band=bool(vref - 16 <= post.min() and post.max() <= vref + 16))
            out.append(row)
            print("  %.0f V, 기준 %.0f V, 제어기 %-10s 경로 %.2f A, 필터 %.2f A, 버스 %.2f–%.2f V" % (
                V, vref, mode, row["path_peak"], row["bridge_peak"], row["vbus_min"], row["vbus_max"]))
    save_json(EID, "variants", dict(rows=out, note="Tier-2 1->25 kW, delay +3.0 us, charging 4 modules; limit 93.75 A"))
    return out


def trace(V, src, load, p=NOMINAL):
    r = simulate(V, load(0.), load(0.), p=p, K=K_ADOPTED, control_p=CP, duration=.02, dt=2e-7, keep_trace=True,
                 controller=make(V), power_fn=load, source_fn=src, step=T_EDGE)
    t = r["t"]; ich = np.interp(t, src.ti, src.ii)
    return t, r["x"], ich


def figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    fig, ax = plt.subplots(3, 2, figsize=(12, 7.5), sharex="col")
    # (왼쪽) 전체 순서, 640 V, 15 kW → 25 kW
    V = 640.; im = ich_max(V)
    src = Source(V, [(0., 0.), (4e-3, 0.), (5e-3, im), (12e-3, im), (12e-3 + 10e-6, 0.)],
                 [(0., 1), (1e-3, 2), (2e-3, 3), (3e-3, 4), (15e-3, 3), (16e-3, 2), (17e-3, 1)])
    t, x, ich = trace(V, src, Load([(0., 15000.), (8e-3, 25000.)]))
    ms = t * 1e3
    ax[0, 0].plot(ms, x[:, 2], color=C["blue"]); ax[0, 0].axhspan(392, 408, color=C["green"], alpha=.08)
    ax[0, 0].set_ylabel("버스전압 [V]"); ax[0, 0].set_ylim(390, 410)
    ax[0, 0].set_title("(a) 전체 순서, 배터리 640 V: 모듈 기동 → 충전 375 A → +10 kW → 충전 비상 정지 → 셰딩")
    ax[1, 0].plot(ms, x[:, 0], color=C["orange"], label="경로전류 i_p"); ax[1, 0].plot(ms, x[:, 3], color=C["gray"], lw=.8, label="필터 전류 i_h")
    ax[1, 0].axhline(90, color=C["red"], ls="--", lw=.8); ax[1, 0].set_ylabel("전류 [A]"); ax[1, 0].legend(loc="lower right")
    a2 = ax[2, 0]; a2.plot(ms, ich, color=C["green"], label="충전전류 i_ch"); a2.set_ylabel("충전전류 [A]")
    a2b = a2.twinx(); a2b.plot(ms, x[:, 1], color=C["blue"], lw=.9, label="직렬전압 v_s"); a2b.set_ylabel("직렬전압 [V]"); a2b.grid(False)
    a2.set_xlabel("시간 [ms]")
    h1, l1 = a2.get_legend_handles_labels(); h2, l2 = a2b.get_legend_handles_labels(); a2.legend(h1 + h2, l1 + l2, loc="center right")
    # (오른쪽) 충전기 비상 정지(10 µs), 920 V 25 kW, 공칭과 지연 +3 µs
    V = 920.; im = ich_max(V)
    for p, lab, c in ((NOMINAL, "공칭", C["blue"]), (replace(NOMINAL, delay=NOMINAL.delay + 3e-6), "지연 +3.0 µs", C["orange"])):
        src = Source(V, [(0., im), (T_EDGE, im), (T_EDGE + 10e-6, 0.)], [(0., NMOD)])
        t, x, ich = trace(V, src, Load([(0., 25000.)]), p)
        ms = t * 1e3; sel = (ms > .8) & (ms < 3.)
        ax[0, 1].plot(ms[sel], x[sel, 2], color=c, label=lab); ax[1, 1].plot(ms[sel], x[sel, 0], color=c, label=lab)
        ax[2, 1].plot(ms[sel], x[sel, 1], color=c, label=lab)
    ax[0, 1].set_title("(b) 충전 비상 정지(%.0f A → 0, 10 µs), 배터리 920 V, 부하 25 kW" % im)
    ax[0, 1].set_ylabel("버스전압 [V]"); ax[0, 1].legend(); ax[1, 1].set_ylabel("경로전류 [A]"); ax[2, 1].set_ylabel("직렬전압 [V]")
    ax[2, 1].set_xlabel("시간 [ms]")
    fig.tight_layout(); fig.savefig(outdir(EID) / "E16_charging_transients.png"); plt.close(fig)


PARTS = dict(static=static, concurrent=concurrent, transition=transition, sequence=sequence, switching=switching,
             variants=variants, figures=figures)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E16 %s ====" % w, flush=True)
        PARTS[w]()
