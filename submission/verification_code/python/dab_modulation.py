"""DAB 변조 해석: 단일 위상천이(SPS)와 1차 내부 위상천이(EPS)의 정상상태 인덕터 전류(이상 소자, 데드타임 없음).

정규화(2차 환산): 1차 전압 V1' = v_bus/n, 2차(링크) 전압 V2 = v_link, 누설 L' = L_dab/n², ωL' = 2π f_s L'.
전류 기준 I_b = V1'/(ωL'), 전압비 r = V2/V1', 정규화 링크전류 j = I2/I_b(+ = 1차 → 링크, − = 링크 → 1차).

파형(반주기 대칭: i(θ + π) = −i(θ), 한 주기 2π)
  1차 브리지: θ ∈ [0, d)에서 +1, [d, π)에서 0(두 레그 같은 쪽 = 영상태). d = π면 SPS(2레벨)
  2차 브리지: θ ∈ [α, α + π)에서 +1, 나머지 −1(2레벨 구형파)
  인덕터 전압 = V1'·s1 − V2·s2, 링크로 가는 직류전류 = 평균(s2·i)
반주기 안에서 전류는 구간마다 직선이므로 꺾이는 점 {0, d, β, π}(β = 2차 전환점)에서 정확히 계산한다.

EPS 표: 각 (r, j)에서 첨두 |i|가 가장 작은 (d, α)를 격자 탐색으로 고른다. SPS는 d = π인 특수 경우이므로
EPS 최적 첨두 ≤ SPS 첨두다. 표는 results/E20/eps_table.json에 저장해 다시 쓴다(검증 코드 E17·E20, 회로 TB10).
"""
import json
import math

import numpy as np

from common import RESULTS, outdir

R_GRID = np.round(np.arange(0., 1.4001, 0.02), 4)        # 전압비 r = V2/V1'
J_GRID = np.round(np.arange(-0.78, 0.7801, 0.01), 4)       # 정규화 링크전류


def wave_norm(r, d, a):
    """정규화 파형(V1' = 1, ωL' = 1). r, d, a는 같은 모양으로 브로드캐스트되는 배열.
    반환: (평균 링크전류 j, 첨두 |i|, 실효 i)."""
    r, d, a = np.broadcast_arrays(np.asarray(r, float), np.asarray(d, float), np.asarray(a, float))
    a = np.mod(a, 2 * np.pi)
    beta = np.where(a < np.pi, a, a - np.pi)                  # 반주기 [0, π) 안의 2차 전환점
    p1 = np.minimum(d, beta); p2 = np.maximum(d, beta)
    pts = [np.zeros_like(d), p1, p2, np.full_like(d, np.pi)]

    def s2(th):
        return np.where(np.mod(th - a, 2 * np.pi) < np.pi, 1., -1.)

    seg = []
    for k in range(3):
        lo, hi = pts[k], pts[k + 1]
        m = 0.5 * (lo + hi)
        s1 = np.where(m < d, 1., 0.); sg = s2(m)
        seg.append((hi - lo, s1 - r * sg, sg))                 # 길이, 기울기, s2
    phi = sum(L * k for L, k, _ in seg)
    i0 = -phi / 2                                              # 반주기 대칭
    ii = [i0]; acc = i0; j = np.zeros_like(d); q = np.zeros_like(d)
    for L, k, sg in seg:
        i1 = acc + k * L
        j = j + sg * 0.5 * (acc + i1) * L                      # ∫ s2·i
        q = q + L * (acc * acc + acc * i1 + i1 * i1) / 3.      # ∫ i²
        ii.append(i1); acc = i1
    pk = np.max(np.abs(np.stack(ii)), axis=0)
    return j / np.pi, pk, np.sqrt(q / np.pi)


def sps_phase(jn):
    """SPS: 정규화 링크전류 j를 내는 위상 φ(|φ| ≤ π/2). j = φ(1 − |φ|/π)."""
    a = np.clip(np.abs(jn) / (np.pi / 4), 0., 1.)
    return np.pi / 2 * (1 - np.sqrt(1 - a)) * np.sign(jn)


def sps_peak_norm(r, jn):
    _, pk, rms = wave_norm(r, np.pi, np.mod(sps_phase(jn), 2 * np.pi))
    return pk, rms


def build_table(nd=600, na=1440, tol=0.004):
    """(r, j) 격자마다 첨두 최소 (d, α). 반환 dict(r, j, d, a, pk, rms, ok)."""
    D = np.linspace(np.pi / nd, np.pi, nd); A = np.linspace(0., 2 * np.pi, na, endpoint=False)
    DD, AA = np.meshgrid(D, A, indexing="ij")
    nr, nj = len(R_GRID), len(J_GRID)
    out = {k: np.full((nr, nj), np.nan) for k in ("d", "a", "pk", "rms")}
    ok = np.zeros((nr, nj), bool)
    for ir, r in enumerate(R_GRID):
        jj, pk, rms = wave_norm(r, DD, AA)
        jf, pf, rf, df, af = jj.ravel(), pk.ravel(), rms.ravel(), DD.ravel(), AA.ravel()
        order = np.argsort(jf); jf, pf, rf, df, af = jf[order], pf[order], rf[order], df[order], af[order]
        for ij, jt in enumerate(J_GRID):
            lo, hi = np.searchsorted(jf, jt - tol), np.searchsorted(jf, jt + tol)
            if hi <= lo:
                continue
            k = lo + int(np.argmin(pf[lo:hi]))
            out["d"][ir, ij], out["a"][ir, ij], out["pk"][ir, ij], out["rms"][ir, ij] = df[k], af[k], pf[k], rf[k]
            ok[ir, ij] = True
    return dict(r=R_GRID.tolist(), j=J_GRID.tolist(), d=out["d"].tolist(), a=out["a"].tolist(),
                pk=out["pk"].tolist(), rms=out["rms"].tolist(), ok=ok.tolist(), nd=nd, na=na, tol=tol)


_TAB = None


def eps_table():
    """EPS 표를 읽는다(없으면 만들어 results/E20/eps_table.json에 저장, 2코어 약 2분)."""
    global _TAB
    if _TAB is None:
        f = RESULTS / "E20" / "eps_table.json"
        if f.exists():
            T = json.loads(f.read_text(encoding="utf-8"))
        else:
            T = build_table()
            outdir("E20"); f.write_text(json.dumps(T), encoding="utf-8")
        _TAB = {k: (np.array(v, float) if isinstance(v, list) else v) for k, v in T.items()}
    return _TAB


def _interp(T, key, r, jn):
    """표 쌍선형 보간. 표 밖은 가장자리 값(r ≤ 1.4, |j| ≤ 0.78)."""
    R, J, Z = T["r"], T["j"], T[key]
    r = min(max(r, R[0]), R[-1]); jn = min(max(jn, J[0]), J[-1])
    ir = min(int((r - R[0]) / (R[1] - R[0])), len(R) - 2); ij = min(int((jn - J[0]) / (J[1] - J[0])), len(J) - 2)
    fr = (r - R[ir]) / (R[1] - R[0]); fj = (jn - J[ij]) / (J[1] - J[0])
    z = Z[ir:ir + 2, ij:ij + 2]
    if np.isnan(z).any():
        return float(np.nanmax(z)) if not np.isnan(z).all() else float("nan")
    return float((1 - fr) * (1 - fj) * z[0, 0] + (1 - fr) * fj * z[0, 1] + fr * (1 - fj) * z[1, 0] + fr * fj * z[1, 1])


def peak_A(vb, vl, idab, p, mode="sps"):
    """링크 쪽 순시 첨두 [A]. mode 'sps'(E17 dab_sps_peak와 같음) 또는 'eps'(표의 최적 첨두)."""
    n, wl = p.turns, 2 * np.pi * p.fs * p.Ldab / p.turns ** 2
    v1 = max(vb, 1.) / n; Ib = v1 / wl
    r = max(vl, 0.) / v1; jn = idab / Ib
    if mode == "sps":
        return float(sps_peak_norm(r, jn)[0]) * Ib
    return _interp(eps_table(), "pk", r, jn) * Ib


def eps_params(vb, vl, idab, p):
    """EPS 지령: (1차 펄스 폭 d, 2차 위상 α, 1차 내부 위상비 D1 = 1 − d/π, 등가 SPS 위상 φ = α − D1·π를 (−π, π]로)."""
    n, wl = p.turns, 2 * np.pi * p.fs * p.Ldab / p.turns ** 2
    v1 = max(vb, 1.) / n; Ib = v1 / wl
    r = max(vl, 0.) / v1; jn = idab / Ib
    T = eps_table()
    d = _interp(T, "d", r, jn); a = _interp(T, "a", r, jn)
    D1 = 1 - d / np.pi
    phi = math.remainder(a + D1 * np.pi, 2 * np.pi)
    return d, a, D1, phi


def eps_ilim(vb, vl, p, pk_max):
    """EPS로 첨두 ≤ pk_max [A]를 지키며 링크에서 뺄 수 있는 최대 전류 크기 [A](표의 j < 0 쪽, r은 선형 보간)."""
    n, wl = p.turns, 2 * np.pi * p.fs * p.Ldab / p.turns ** 2
    v1 = max(vb, 1.) / n; Ib = v1 / wl
    T = eps_table(); R, J, PK = T["r"], T["j"], T["pk"]
    r = min(max(max(vl, 0.) / v1, R[0]), R[-1])
    ir = min(int((r - R[0]) / (R[1] - R[0])), len(R) - 2); fr = (r - R[ir]) / (R[1] - R[0])
    row = (1 - fr) * PK[ir] + fr * PK[ir + 1]
    tgt = pk_max / Ib
    i0 = int(np.searchsorted(J, 0.))                       # j = 0
    jl = 0.
    for k in range(i0, -1, -1):                             # j = 0 → −0.78
        if not np.isfinite(row[k]) or row[k] > tgt:
            break
        jl = -J[k]
    return jl * Ib


# ---- 회로 지령 블록(simulink/ctrl/prism_dab_eps_map.m)과 같은 계산 ---------------------------------------------------------
def circuit_tables(pk_key="pk"):
    """회로가 쓰는 j ≤ 0 표: d, 등가 위상 φ = α + D1·π((−π, π]), 첨두(pk_key 열). j = 0 열(퇴화)은 j = −0.01 열로 채운다.
    반환 dict(d, phi, pk, r0, dr, j0, dj)."""
    T = eps_table()
    J = np.asarray(T["j"]); keep = J <= 1e-9
    d = np.array(T["d"])[:, keep]; a = np.array(T["a"])[:, keep]; pk = np.array(T[pk_key] if pk_key in T else T["pk"])[:, keep]
    d[:, -1] = d[:, -2]; a[:, -1] = a[:, -2]; pk[:, -1] = pk[:, -2]
    phi = np.vectorize(lambda aa, dd: math.remainder(aa + (1 - dd / np.pi) * np.pi, 2 * np.pi))(a, d)
    R = np.asarray(T["r"])
    return dict(d=d, phi=phi, pk=pk, r0=float(R[0]), dr=float(R[1] - R[0]), j0=float(J[keep][0]), dj=float(J[1] - J[0]))


def _lim_row(row, tgt, j0, dj):
    jl = 0.
    for k in range(row.size - 1, -1, -1):
        if row[k] > tgt:
            break
        jl = -(j0 + k * dj)
    return jl


def circuit_map(vb, vl, icmd, p, pk_max, tab):
    """회로 블록과 같은 순서: 첨두 상한 탐색(같은 r에서 tK ≤ pk_max/I_b인 최대 |j|) → 지령 클립 → (d, φ) 쌍선형 보간 → D1 ≤ 0.95.
    반환 (D1, φ, 지령 링크전류 [A], I_b [A])."""
    d, ph, pk = tab["d"], tab["phi"], tab["pk"]
    r0, dr, j0, dj = tab["r0"], tab["dr"], tab["j0"], tab["dj"]
    nr, nj = d.shape
    n, wl = p.turns, 2 * np.pi * p.fs * p.Ldab / p.turns ** 2
    v1 = max(vb, 1.) / n; Ib = v1 / wl
    r = min(max(vl / v1, r0), r0 + (nr - 1) * dr)
    ir = min(int((r - r0) / dr), nr - 2); fr = (r - r0) / dr - ir
    jl = _lim_row((1 - fr) * pk[ir] + fr * pk[ir + 1], pk_max / Ib, j0, dj)
    jn = min(max(icmd / Ib, -jl), 0.); jn = max(jn, j0)
    ij = min(int((jn - j0) / dj), nj - 2); fj = (jn - j0) / dj - ij
    bil = lambda z: ((1 - fr) * (1 - fj) * z[ir, ij] + (1 - fr) * fj * z[ir, ij + 1] + fr * (1 - fj) * z[ir + 1, ij] + fr * fj * z[ir + 1, ij + 1])
    D1 = min(max(1 - bil(d) / np.pi, 0.), 0.95)
    return D1, float(bil(ph)), jn * Ib, Ib


# ---- 스위칭 반영 표(E21: 데드타임·출력용량·역방향 도통, dab_switching.py) --------------------------------------------------
_SW = {}


def sw_table(p=None):
    """스위칭 반영 표(results/E21/sw_table_n<권선비>.json, 없으면 dab_switching.build_sw_table로 만든다). 모듈마다(권선비·누설 L) 따로다.
    pk_sw(첨두, 버스 380·440·500 V 가운데 최대)와 j_sw(실제 링크전류, 평균)는 회로 지령표와 같은 격자(r × j ≤ 0)이고,
    칸마다 회로 블록이 내는 (D1, φ)를 그대로 쓴 값이다. p가 없으면 R2-W460."""
    if p is None:
        import E19_r2_window_module as E19
        p, _ = E19.plant("W460_240s")
    key = "n%.1f" % p.turns
    if key not in _SW:
        f = RESULTS / "E21" / ("sw_table_%s.json" % key)
        if not f.exists():
            import dab_switching as SW
            T = SW.build_sw_table(p)
            outdir("E21"); f.write_text(json.dumps(T), encoding="utf-8")
        T = json.loads(f.read_text(encoding="utf-8"))
        pk = np.array(T["pk_sw"]); js = np.array(T["j_sw"])
        js[0] = js[1]                                     # r = 0(링크 0 V)은 평균전류를 전력/전압으로 구할 수 없어 r = 0.02 행으로
        _SW[key] = dict(T, pk_sw=pk, j_sw=js)
    return _SW[key]


def _sw_rowcol(T, vb, vl, p):
    n, wl = p.turns, 2 * np.pi * p.fs * p.Ldab / p.turns ** 2
    v1 = max(vb, 1.) / n; Ib = v1 / wl
    nr = T["pk_sw"].shape[0]
    r = min(max(max(vl, 0.) / v1, T["r0"]), T["r0"] + (nr - 1) * T["dr"])
    ir = min(int((r - T["r0"]) / T["dr"]), nr - 2); fr = (r - T["r0"]) / T["dr"] - ir
    return Ib, ir, fr


def _sw_bil(T, key, ir, fr, jn):
    Z = T[key]; nj = Z.shape[1]
    jn = min(max(jn, T["j0"]), 0.)
    ij = min(int((jn - T["j0"]) / T["dj"]), nj - 2); fj = (jn - T["j0"]) / T["dj"] - ij
    return float((1 - fr) * (1 - fj) * Z[ir, ij] + (1 - fr) * fj * Z[ir, ij + 1] + fr * (1 - fj) * Z[ir + 1, ij] + fr * fj * Z[ir + 1, ij + 1])


def sw_ilim(vb, vl, p, pk_max):
    """회로 블록과 같은 탐색을 스위칭 반영 첨두(pk_sw)로: 첨두 ≤ pk_max [A]인 최대 지령 전류 크기 [A]."""
    T = sw_table(p); Ib, ir, fr = _sw_rowcol(T, vb, vl, p)
    P = T["pk_sw"]; tgt = pk_max / Ib
    jl = _lim_row((1 - fr) * P[ir] + fr * P[ir + 1], tgt, T["j0"], T["dj"])
    return jl * Ib


def sw_peak_A(vb, vl, icmd, p):
    """지령 링크전류 icmd(≤ 0)에서 스위칭 반영 링크 쪽 첨두 [A]."""
    T = sw_table(p); Ib, ir, fr = _sw_rowcol(T, vb, vl, p)
    return _sw_bil(T, "pk_sw", ir, fr, icmd / Ib) * Ib


def sw_current(vb, vl, icmd, p):
    """지령 링크전류 icmd(≤ 0)에서 회로 DAB가 실제로 내는 링크 평균전류 [A](데드타임 영향)."""
    T = sw_table(p); Ib, ir, fr = _sw_rowcol(T, vb, vl, p)
    return _sw_bil(T, "j_sw", ir, fr, icmd / Ib) * Ib
