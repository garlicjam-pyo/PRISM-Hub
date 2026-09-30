"""[E4] 요구사항 분석: 보조버스 조정 요구의 근거와 보장 최소 배터리 전압.

■ 목적
  (R1) 400 V 보조버스를 정밀 조정해야 하는 이유가 외부 부하·규격에서 나오는지 확인한다(보고서 3.2절).
  (R3) 25 kW를 보장할 수 있는 최소 배터리 전압 V_g를 정적·동적으로 구한다(보고서 3.3절).

■ 왜 필요한가
  Stage B는 "보조버스를 배터리 전압과 무관하게 400 V로 유지"하기 위해 존재한다. 이 요구가 외부
  요구인지 설계 선택에서 생긴 파생 요구인지를 밝혀야 Stage B의 존재 이유와 비교 대상(창 조정 변형)을
  정할 수 있다. 또 배터리 운전범위 하한(640 V)은 모든 동특성 시험의 설계 코너이므로 그 근거가 필요하다.

■ 방법
  R1  비조정 V_A(= V_bat/2 − R·I)를 400 V급 부하의 공개 입력범위(보고서 참고문헌 [19]–[21])와 비교하고,
      ISO 21498-1 B_420 상한(420 V), 고정이득 Stage C(400/48)를 거친 48 V 출력과 ISO 21780 상한(52 V)을
      넘는 배터리 전압을 구한다. 창 조정 변형 ③′(버스 = min(V_A, 410 V))의 Stage B 처리전력도 계산한다.
  R3  V_g,static : 링크 90 V(대역 하한), 경로저항 +10 %에서 25 kW 정상점이 성립하는 최소 V_bat
                   (경로전류 ≤ 90 A, 직렬 ±90 V, 변조율 ≤ 0.95, DAB 한계) — 이분 탐색
      저하 운전   : 버스 기준을 390 V로 낮췄을 때의 정적 한계(25 kW, 필수부하 15.1 kW)
      V_g,dynamic: 공칭 조건에서 Tier-1 최악 스텝(15→25 kW)이 통과하는 최소 V_bat — 이분 탐색(분해능 0.05 V)
                   채택 설계와 비교 설계 각각 계산한다.

■ 판정 기준
  정적 한계가 동적 한계보다 높으면 정적 조건이 보장 하한을 결정한다. 보장 하한 640 V는
  V_g,static에 약 8 V 여유를 더한 값이다.

■ 실행   python E4_requirements.py      (약 1분)
■ 결과   results/E4/requirements.json
■ 보고서 수치: B_420 초과 V_bat 840 V, 48 V 상한 초과 866.7 V, ③′ 최대 링크전력 2.69 kW(920 V),
         SHS33 Gen2 상한 위반 864 V 초과, V_g,static 631.7 V, 저하 운전 정적 한계 613.1 V, V_g,dynamic(Tier-1) 622.2 V
"""
from dataclasses import replace

from scipy.optimize import brentq

from model_stage_b import Parameters, equilibrium, current_limit, continuous_power_limit
from controller_reference import NOMINAL
from stage_b_tests import sim, judge
from common import save_json, verdict

P = Parameters()
N_STAGE_C = 400 / 48          # 고정이득 CLLC 권선비(공칭 버스 / 공칭 48 V)
V_CAP = 410.                  # 창 조정 변형의 버스 상한: 410 + 8 V 과도 < 420 V(B_420)

# 공개 사양의 허용 입력전압 범위 [V DC] (보고서 표 3.2, 참고문헌 [19]–[21])
COMPONENTS = [
    dict(name="Sanden SHS33 Gen2 전동 컴프레서", vmin=165, vmax=432, ref="[19]"),
    dict(name="Sanden SHS33 Gen3 전동 컴프레서", vmin=165, vmax=470, ref="[19]"),
    dict(name="Sanden SHS45 전동 컴프레서(냉방 10 kW)", vmin=260, vmax=470, ref="[19]"),
    dict(name="Sanden SEE27 전동 컴프레서", vmin=155, vmax=460, ref="[19]"),
    dict(name="Webasto HVH 50/70 고전압 히터(5/7 kW)", vmin=100, vmax=490, ref="[20]"),
    dict(name="BorgWarner Gen5 HV DC/DC(1.2 kW)", vmin=220, vmax=800, ref="[21]"),
]
ISO21498_B420, ISO21498_B470 = 420., 470.     # ISO 21498-1 전압 하위등급 상한 [22]
ISO21780_48V = (36., 52.)                       # ISO 21780 48 V 공칭 운전범위 [23]


def v_a(vbat, power=25000., p=P):
    """부하 시 Stage A 출력: 이상 2:1 전압 − 경로 저항강하."""
    return vbat / 2 - p.R * power / (vbat / 2)


def static_ok(vbat, power, p, path_limit):
    """정상점이 경로전류·직렬전압·변조율·DAB 한계를 모두 만족하는지."""
    x, u = equilibrium(vbat, power, p)
    return bool(abs(x[0]) <= path_limit and abs(x[1]) <= p.series_max and abs(u[0]) <= p.modulation_max
                and abs(x[5]) <= current_limit(x[2], x[4], p) and abs(x[4] * x[5]) <= p.power_max)


def min_vbat(p, power=25000., path_limit=90., lo=560., hi=700.):
    """정상점이 성립하는 최소 배터리 전압(이분 탐색 60회)."""
    assert static_ok(hi, power, p, path_limit) and not static_ok(lo, power, p, path_limit)
    for _ in range(60):
        mid = (lo + hi) / 2
        if static_ok(mid, power, p, path_limit): hi = mid
        else: lo = mid
    return hi


def window_variant(vbat, power=25000., p=P):
    """창 조정 변형 ③′: 버스 = min(V_A, 410 V). Stage B는 V_A > 410 V일 때만 동작."""
    va = v_a(vbat, power, p)
    if va <= V_CAP:
        return dict(vbat=vbat, bus_V=va, series_V=0., link_power_W=0., active=False)
    x, u = equilibrium(vbat, power, replace(p, vref=V_CAP))
    return dict(vbat=vbat, bus_V=V_CAP, series_V=float(x[1]), link_power_W=float(x[4] * x[5]),
                path_A=float(x[0]), active=True)


def vg_dynamic(design, lo=600., hi=640., tol_v=.05):
    """공칭 조건 Tier-1 최악 스텝(15→25 kW)이 통과하는 최소 V_bat. 정상점이 성립하지 않으면 실패로 본다."""
    def ok(v):
        try:
            return judge(1, sim(v, 15000, 25000, NOMINAL, design=design))["pass_"]
        except ValueError:          # 초기 정상점이 운전 범위 밖
            return False
    if not ok(hi): return None
    if ok(lo): return lo
    while hi - lo > tol_v:
        mid = (lo + hi) / 2
        if ok(mid): hi = mid
        else: lo = mid
    return hi


def main():
    print("[E4] 요구사항 분석")
    grid = sorted(set(list(range(600, 921, 20)) + [640, 866, 920]))
    # ---------------- R1: 조정 요구의 근거
    va_rows = []
    for v in grid:
        va0, va25 = v / 2, v_a(v)
        va_rows.append(dict(vbat=v, VA_noload=va0, VA_25kW=va25, v48_fixed_gain_noload=va0 / N_STAGE_C,
                            components_violated=[c["name"] for c in COMPONENTS if not (c["vmin"] <= va25 and va0 <= c["vmax"])],
                            above_B420=va0 > ISO21498_B420, above_B470=va0 > ISO21498_B470))
    vbat_b420 = 2 * ISO21498_B420
    vbat_48v = 2 * ISO21780_48V[1] * N_STAGE_C
    print(f"   비조정 V_A: 25 kW {v_a(640):.1f}–{v_a(920):.1f} V, 무부하 320–460 V")
    for c in COMPONENTS:
        v_hi = 2 * c["vmax"]                                         # 무부하 V_A = V_bat/2 가 상한을 넘는 V_bat
        v_lo = brentq(lambda v: v_a(v) - c["vmin"], 200., 2000.)     # 25 kW V_A가 하한 아래로 내려가는 V_bat
        msg = []
        if v_hi < 920: msg.append(f"V_bat {v_hi:.0f} V 초과에서 상한 위반")
        if v_lo > 640: msg.append(f"V_bat {v_lo:.1f} V 미만에서 하한 위반")
        print(f"   {c['name']:36s} {c['vmin']}–{c['vmax']} V : " + (", ".join(msg) if msg else "640–920 V 전 범위 수용"))
    print(f"   B_420 상한 초과: V_bat > {vbat_b420:.0f} V,  고정이득 48 V 출력 52 V 초과: V_bat > {vbat_48v:.1f} V")
    win = [window_variant(float(v)) for v in range(640, 921, 10)]
    wmax = max(win, key=lambda w: abs(w["link_power_W"]))
    v_on = brentq(lambda v: v_a(v) - V_CAP, 700., 920.)             # V_A(25 kW) = 410 V가 되는 V_bat
    print(f"   창 조정 변형 ③′: Stage B 동작 시작 V_bat {v_on:.1f} V, "
          f"최대 링크전력 {abs(wmax['link_power_W'])/1e3:.2f} kW @ {wmax['vbat']} V")

    # ---------------- R3: 보장 최소 배터리 전압
    tol = replace(P, R=P.R * 1.1, vlink=90.)          # 최악: 경로저항 +10 %, 링크 90 V
    vg_static = min_vbat(tol)
    vg_nominal = min_vbat(P, path_limit=P.path_max)   # 참고: 공칭 링크 100 V, 공칭 저항, 포트 한계만
    vdeg390 = min_vbat(replace(tol, vref=390.))
    vdeg390_mand = min_vbat(replace(tol, vref=390.), power=15100., lo=540.)
    x_g, u_g = equilibrium(vg_static, 25000., tol)
    print(f"   V_g,static = {vg_static:.1f} V (경로 {x_g[0]:.1f} A, 변조율 {u_g[0]:.3f}), 참고: 공칭 조건 {vg_nominal:.1f} V")
    print(f"   저하 운전(버스 390 V): 25 kW {vdeg390:.1f} V, 필수부하 15.1 kW {vdeg390_mand:.1f} V")
    vg_dyn = {d: vg_dynamic(d) for d in ("adopted", "reference")}
    fmt = lambda v: "해당 없음" if v is None else f"{v:.1f} V"
    print(f"   V_g,dynamic(Tier-1 15→25 kW, 공칭, 분해능 0.05 V): 채택 설계 {fmt(vg_dyn['adopted'])}, 비교 설계 {fmt(vg_dyn['reference'])}")
    verdict("정적 한계가 동적 한계보다 높다(정적 조건이 보장 하한을 결정)",
            all(v is None or v < vg_static for v in vg_dyn.values()))
    verdict("보장 하한 640 V는 V_g,static보다 약 8 V 높다", 640 - vg_static >= 8.0, f"여유 {640 - vg_static:.1f} V")

    save_json("E4", "requirements", dict(
        R1=dict(components=COMPONENTS, iso21498_upper_limits_V=dict(B_420=ISO21498_B420, B_470=ISO21498_B470),
                iso21780_48V_V=ISO21780_48V, stage_c_ratio=N_STAGE_C, vbat_where_VA_exceeds_B420=vbat_b420,
                vbat_where_fixed_gain_48V_exceeds_52V=vbat_48v, va_table=va_rows,
                window_variant=dict(v_cap=V_CAP, rows=win)),
        R3=dict(assumptions=dict(power_W=25000., link_V=90., R_ohm=tol.R, modulation_max=P.modulation_max, path_limit_A=90.),
                V_g_static=vg_static, V_static_nominal=vg_nominal, V_degraded_ref390=vdeg390,
                V_degraded_ref390_mandatory_15p1kW=vdeg390_mand,
                point_at_V_g=dict(path_A=x_g[0], series_V=x_g[1], modulation=u_g[0], link_A=x_g[5], link_power_W=x_g[4] * x_g[5]),
                V_g_dynamic_tier1=vg_dyn,
                continuous_limit_W={str(v): continuous_power_limit(float(v)) for v in [600, 615, 620, 625, 630, 640]})))


if __name__ == "__main__":
    main()
