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
