"""TB10–TB13 회로 결과 요약을 읽어 보고서 표 {t:tb11}·{t:tb12}·{t:tb13}의 행·판정 문자열을 만든다(수치를 손으로 옮기지 않기 위해)."""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TB = ROOT / "simulink" / "tb"
N = 4.6
RATED = 45.8281
CASES = ["A_1008V_hbopen_25kW", "B_930V_hbopen_25kW"]


def _load(tb, folder, case):
    res = TB / folder / "results"
    f = res / f"{tb}_{case}_summary.json"
    if not f.exists():
        return None
    S = json.loads(f.read_text(encoding="utf-8"))
    Z = np.loadtxt(res / f"{tb}_{case}_periods.csv", delimiter=",")
    st = np.round(Z[:, 15]); pk = N * Z[:, 13]; post = Z[:, 0] > 0.5e-3
    S["pk_state"] = {s: float(pk[(st == s) & post].max()) for s in (9, 10, 11) if ((st == s) & post).any()}
    fq = np.isin(st, [9, 10, 11]) & post
    S["n_over"] = int((pk[fq] > 1.5 * RATED).sum()); S["n_fault"] = int(fq.sum())
    srt = np.sort(pk[fq])[::-1]
    S["pk_2nd"] = float(srt[1]) if len(srt) > 1 else float("nan")
    tr = {t["state"]: t["ms"] for t in S["transitions"]}
    S["deg_ms"] = tr.get("DEGRADED")
    return S


def _f(x, d=1):
    return ("%%.%df" % d) % x


def table(tb, folder, ref_name, refs):
    R = [_load(tb, folder, c) for c in CASES]
    if not all(R):
        return dict(rows=[["(실행 중)", "—", "—", "—"]], verdict="실행 중", ready=False, R=R)
    def ps(S):
        p = S["pk_state"]
        return "%s / %s / %s A" % tuple(_f(p.get(s, float("nan"))) for s in (9, 10, 11))
    def pair(fn, fmt):
        return fmt % tuple(fn(S) for S in refs)
    rows = [
        ["회로 판정(1.5배 기준 포함)"] + [("통과" if S["verdict"] == "PASS" else "불통과") for S in R] + [pair(lambda S: "통과" if S["verdict"] == "PASS" else "불통과", "%s / %s")],
        ["DAB 링크 쪽 첨두(유지 / 붕괴 / 소프트 투입)"] + [ps(S) for S in R] + ["최대 %s / %s A" % tuple(_f(S["dab"]["sec_peak_A"]) for S in refs)],
        ["1.5배(68.7 A) 초과 주기 / 강등 상태 주기"] + ["%d / %d" % (S["n_over"], S["n_fault"]) for S in R] + ["%d / %d" % (refs[0]["n_over"], refs[1]["n_over"])],
        ["1차 첨두"] + ["%s A" % _f(S["dab"]["prim_peak_A"]) for S in R] + [pair(lambda S: _f(S["dab"]["prim_peak_A"]), "%s / %s A")],
        ["경로·필터 순시 최대"] + ["%s A" % _f(max(S["peaks"]["ip_A"], S["peaks"]["ih_A"])) for S in R] + [pair(lambda S: _f(max(S["peaks"]["ip_A"], S["peaks"]["ih_A"])), "%s / %s A")],
        ["버스 최저(5 µs 평균)"] + ["%s V" % _f(S["peaks"]["bus_min_V"]) for S in R] + [pair(lambda S: _f(S["peaks"]["bus_min_V"]), "%s / %s V")],
        ["소프트 투입 진입 링크 / 소자 에너지"] + ["%s V / %s J" % (_f(S["soft"]["vl_V"], 2), _f(S["soft"]["energy_J"], 3)) for S in R] + ["%s·%s V / %s·%s J" % (_f(refs[0]["soft"]["vl_V"], 2), _f(refs[1]["soft"]["vl_V"], 2), _f(refs[0]["soft"]["energy_J"], 3), _f(refs[1]["soft"]["energy_J"], 3))],
        ["제동 저항 에너지(분리 3 ms)"] + ["%s J" % _f(S["peaks"]["brake_J"]) for S in R] + [pair(lambda S: _f(S["peaks"]["brake_J"]), "%s / %s J")],
        ["강등 완료(사건 0.5 ms 기준 시각)"] + ["%s ms" % _f(S["deg_ms"], 2) for S in R] + [pair(lambda S: _f(S["deg_ms"], 2), "%s / %s ms")],
    ]
    npass = sum(S["verdict"] == "PASS" for S in R)
    allpass = npass == len(R)
    worst = max(S["dab"]["sec_peak_A"] for S in R)
    pk2 = tuple(_f(S["dab"]["sec_peak_A"]) for S in R)
    if allpass:
        verdict = "통과 2/2(1.5배 기준), DAB 첨두 %s·%s A" % pk2
    elif npass:
        verdict = "%d/2 통과(1.5배 기준), DAB 첨두 %s·%s A" % ((npass,) + pk2)
    else:
        verdict = "불통과(DAB 첨두 %s·%s A)" % pk2
    return dict(rows=rows, verdict=verdict, ready=True, allpass=allpass, worst=worst, R=R)


T10 = [_load("TB10", "TB10_R2_FaultMod", c) for c in CASES]
T11 = table("TB11", "TB11_R2_FaultMod_SW", "TB10", T10)
T12 = table("TB12", "TB12_R2_FaultMod_TR", "TB11", T11["R"]) if T11["ready"] else dict(rows=[["(실행 중)", "—", "—", "—"]], verdict="실행 중", ready=False)
T13 = table("TB13", "TB13_R2_FaultMod_TA", "TB12", T12["R"]) if T12["ready"] else dict(rows=[["(실행 중)", "—", "—", "—"]], verdict="실행 중", ready=False)


def _t12_text():
    if not T12.get("ready"):
        return "TB12 회로 실행 중이다."
    R = T12["R"]; Q = T11["R"]
    pk = [S["dab"]["sec_peak_A"] for S in R]
    lim = 1.455 * RATED
    return ("**TB12는 사례 B만 통과했다(1/2).** 전이 첨두는 TB11의 %s·%s A에서 %s·%s A로 줄었고, 1.5배를 넘은 주기도 %d·%d개에서 %d·%d개로 줄었다. "
            "사례 A는 5.26 ms에 시작한 한 전이의 끝 세 주기에서 최대 %s A로 기준(68.7 A)을 1.3 A 넘었다. 남은 초과는 변화율 상한으로 나눠 옮긴 전이의 끝에 생긴다: "
            "전이 경로 중간의 (D1, 위상)은 정상 상한 칸보다 첨두가 조금 높고, D1 변화의 직류 편류가 몇 A 남는다(표 {t:gate}의 ≤ 2.7 A). 두 사례에서 전이 주기 첨두는 "
            "정상 주기 상한(%s A) 위로 최대 %s %%였다. 경로전류(%s·%s A), 소프트 투입 에너지(%s·%s J), 강등 완료 시각(%s·%s ms)은 TB11과 같은 수준이다." % (
                _f(Q[0]["dab"]["sec_peak_A"]), _f(Q[1]["dab"]["sec_peak_A"]), _f(pk[0]), _f(pk[1]), Q[0]["n_over"], Q[1]["n_over"], R[0]["n_over"], R[1]["n_over"],
                _f(pk[0]), _f(lim), _f(100 * (max(pk) / lim - 1)),
                _f(max(R[0]["peaks"]["ip_A"], R[0]["peaks"]["ih_A"])), _f(max(R[1]["peaks"]["ip_A"], R[1]["peaks"]["ih_A"])),
                _f(R[0]["soft"]["energy_J"], 3), _f(R[1]["soft"]["energy_J"], 3), _f(R[0]["deg_ms"], 2), _f(R[1]["deg_ms"], 2)))


def _t13_text():
    if not T13.get("ready"):
        return "TB13 회로 실행 중이다."
    R = T13["R"]; Q = T12["R"]
    pk = [S["dab"]["sec_peak_A"] for S in R]
    lim = 1.387 * RATED
    common = ("강등 중 DAB 링크 쪽 첨두는 %s·%s A(정상 주기 상한 %s A 위로 최대 %s %%), 1.5배를 넘은 주기는 %d·%d개였다. 경로전류는 %s·%s A, 소프트 투입 "
              "진입 링크는 %s·%s V, 소자 에너지는 %s·%s J(TB12 %s·%s J), 강등 완료는 %s·%s ms였다." % (
                  _f(pk[0]), _f(pk[1]), _f(lim), _f(100 * (max(pk) / lim - 1)), R[0]["n_over"], R[1]["n_over"],
                  _f(max(R[0]["peaks"]["ip_A"], R[0]["peaks"]["ih_A"])), _f(max(R[1]["peaks"]["ip_A"], R[1]["peaks"]["ih_A"])),
                  _f(R[0]["soft"]["vl_V"], 2), _f(R[1]["soft"]["vl_V"], 2), _f(R[0]["soft"]["energy_J"], 3), _f(R[1]["soft"]["energy_J"], 3),
                  _f(Q[0]["soft"]["energy_J"], 3), _f(Q[1]["soft"]["energy_J"], 3), _f(R[0]["deg_ms"], 2), _f(R[1]["deg_ms"], 2)))
    if T13["allpass"]:
        return ("**TB13은 두 사례 모두 1.5배 기준을 포함한 회로 판정을 통과했다.** " + common +
                " 기준까지 여유는 %s A다. 이로써 강등 중 DAB 첨두는 해석(정상상태 최적 지령표) → 스위칭 정상상태(데드타임·출력용량, 3 %%) → "
                "지령 전이(변화율 상한과 여유 5 %%)의 세 단계를 거쳐 회로에서 설계 목표 안에 들었다. 대가는 붕괴 구간의 DAB 전류가 약 5 %% 줄어 "
                "링크가 시간 상한(10 ms) 안에 덜 내려간 것이다. 사례 A는 소프트 투입 진입 링크가 %s V(TB12 %s V)여서 소자 에너지가 %s J로 늘었고, "
                "소프트 투입 중 DAB 첨두도 %s A가 되었다. 사례 B는 붕괴가 시간 상한에 닿아 강등 완료가 %s ms에서 %s ms로 늦어졌다." % (
                    _f(1.5 * RATED - max(pk)), _f(R[0]["soft"]["vl_V"], 2), _f(Q[0]["soft"]["vl_V"], 2), _f(R[0]["soft"]["energy_J"], 3),
                    _f(R[0]["pk_state"][11]), _f(Q[1]["deg_ms"], 2), _f(R[1]["deg_ms"], 2)))
    return ("**TB13도 1.5배 기준에서 %s였다.** " % T13["verdict"]) + common


T12_TEXT = _t12_text()
T13_TEXT = _t13_text()
