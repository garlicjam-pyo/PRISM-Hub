"""검증 스크립트 공용 도구: 결과 폴더 경로, JSON 저장, 판정 출력, 작업자 풀, 입력 해시, 엄격 비교."""
import hashlib
import json
import math
import multiprocessing as _mp
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent          # 패키지 최상위 폴더
RESULTS = Path(os.environ["PRISM_RESULTS_DIR"]).resolve() if os.environ.get("PRISM_RESULTS_DIR") else ROOT / "results"
# (2026-11-07 E47) PRISM_RESULTS_DIR로 결과 폴더를 바꿀 수 있다(검증기 오류 주입 시험이 복사본에서만 실행하도록).


def outdir(eid):
    """근거 번호(E1, E2 ...)별 결과 폴더를 만들고 경로를 돌려준다."""
    d = RESULTS / eid
    d.mkdir(parents=True, exist_ok=True)
    return d


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    return o


def save_json(eid, name, obj):
    """results/<eid>/<name>.json 으로 저장한다."""
    path = outdir(eid) / f"{name}.json"
    path.write_text(json.dumps(_clean(obj), indent=1, ensure_ascii=False), encoding="utf-8")
    try:
        shown = path.relative_to(ROOT)
    except ValueError:
        shown = path
    print(f"  → 저장: {shown}")
    return path


def load_json(eid, name):
    return json.loads((RESULTS / eid / f"{name}.json").read_text(encoding="utf-8"))


GATE_FAILS = []          # (2026-11-06 두 번째 통합 검토 V02) 필수 판정(gate=True)의 실패 목록. 실행 끝에 exit_status()로 비정상 종료


def verdict(label, ok, detail="", gate=False):
    """판정 결과를 한 줄로 출력한다. gate=True는 저장 결과 재현·검증기처럼 반드시 맞아야 하는 판정이며,
    실패하면 GATE_FAILS에 남겨 실행 끝에 종료 코드 1을 돌려준다(설계 판정의 '불통과' 결과와 구별)."""
    print(f"  [{'통과' if ok else '실패'}] {label}" + (f"  ({detail})" if detail else ""))
    if gate and not ok:
        GATE_FAILS.append(label)
    return bool(ok)


def exit_status():
    """필수 판정이 하나라도 실패했으면 1, 아니면 0."""
    if GATE_FAILS:
        print("\n필수 판정 실패 %d건: %s" % (len(GATE_FAILS), "; ".join(GATE_FAILS)))
        return 1
    return 0


def workers():
    """병렬 작업 수. 환경변수 PRISM_WORKERS로 바꿀 수 있다(기본: CPU 수)."""
    return int(os.environ.get("PRISM_WORKERS", os.cpu_count() or 1))


# ------------------------------------------------------------------------------------------------------
# 작업자 풀(2026-11-06 통합 수정안 7절). 여러 시험은 부모 프로세스에서 모듈 전역(설계값, 버스 용량, 모듈 저항 등)을 바꾼 뒤
# 작업자를 띄운다. spawn(Windows 기본, macOS 기본, Python 3.14 이후 Linux 기본은 forkserver)은 작업자에서 모듈을 새로 읽어
# 이 설정을 잃는다. 그래서 모든 시험은 이 Pool을 쓴다: fork를 쓸 수 있으면 fork 문맥으로, 없으면 같은 프로세스에서 차례로
# 실행한다(작업자 초기화 함수도 같은 프로세스에서 한 번 실행). 환경변수 PRISM_POOL=serial이면 어디서나 차례 실행이다.
# ------------------------------------------------------------------------------------------------------
class SerialPool:
    """multiprocessing.Pool과 같은 사용법(map·starmap·imap)으로 같은 프로세스에서 차례로 실행한다."""
    def __init__(self, processes=None, initializer=None, initargs=(), **kw):
        if initializer is not None:
            initializer(*initargs)

    def map(self, f, it, chunksize=None):
        return [f(x) for x in it]

    def starmap(self, f, it, chunksize=None):
        return [f(*x) for x in it]

    def imap(self, f, it, chunksize=1):
        return (f(x) for x in it)

    imap_unordered = imap

    def close(self):
        pass

    def join(self):
        pass

    def terminate(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def pool_mode():
    m = os.environ.get("PRISM_POOL", "").strip().lower()
    have_fork = "fork" in _mp.get_all_start_methods()
    if m == "serial":
        return "serial"
    if m == "fork":
        if not have_fork:
            raise RuntimeError("PRISM_POOL=fork 이지만 이 운영체제에는 fork가 없다")
        return "fork"
    if m:
        raise RuntimeError("PRISM_POOL은 fork 또는 serial만 쓸 수 있다: %r" % m)
    return "fork" if have_fork else "serial"


def Pool(processes=None, initializer=None, initargs=(), **kw):
    if pool_mode() == "serial":
        return SerialPool(processes, initializer, initargs)
    return _mp.get_context("fork").Pool(processes, initializer, initargs, **kw)


class SerialExecutor:
    """concurrent.futures.ProcessPoolExecutor와 같은 사용법(map·submit·with)을 같은 프로세스에서 차례로 실행한다."""

    def __init__(self, max_workers=None, *a, **k):
        pass

    def map(self, fn, *iterables, timeout=None, chunksize=1):
        return iter([fn(*args) for args in zip(*iterables)])

    def submit(self, fn, *args, **kwargs):
        from concurrent.futures import Future
        f = Future()
        try:
            f.set_result(fn(*args, **kwargs))
        except BaseException as e:            # noqa: BLE001  (Future에 그대로 담는다)
            f.set_exception(e)
        return f

    def shutdown(self, wait=True, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def Executor(max_workers=None, **kw):
    """ProcessPoolExecutor 대신 쓴다(2026-11-06). fork 문맥을 명시하거나(같은 부모 설정 상속), fork가 없으면 같은 프로세스에서 차례로 실행한다.
    spawn·forkserver(Windows·macOS 기본, Python 3.14 이후 Linux 기본)에서는 부모의 설정 교체가 자식에 전해지지 않기 때문이다."""
    if pool_mode() == "serial":
        return SerialExecutor(max_workers)
    from concurrent.futures import ProcessPoolExecutor
    kw.pop("mp_context", None)
    return ProcessPoolExecutor(max_workers, mp_context=_mp.get_context("fork"), **kw)


# ------------------------------------------------------------------------------------------------------
# 입력 출처 기록과 엄격 비교(통합 수정안 8절)
# ------------------------------------------------------------------------------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_file_lf(path):
    """(2026-11-07 E47) 줄바꿈을 LF로 정규화한 해시(CRLF → LF). 저장소는 텍스트를 LF로 배포하지만(.gitattributes eol=lf)
    Windows 작업 사본은 CRLF일 수 있어, 원시 바이트 해시(sha256)만으로는 같은 내용이 다르게 보인다. 이진 파일에는 쓰지 않는다."""
    with open(path, "rb") as f:
        b = f.read()
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def input_record(path, kind):
    """kind: 'archived'(날짜별 validation·회로 저장 파형) 또는 'fresh'(이번 실행의 results/)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError("입력 없음: %s (먼저 선행 시험을 실행하거나 저장 자료를 준비할 것)" % p)
    try:
        rel = str(p.resolve().relative_to(ROOT.parent.parent))
    except ValueError:
        rel = str(p)
    rec = dict(path=rel, kind=kind, sha256=sha256_file(p), bytes=p.stat().st_size)
    if p.suffix.lower() in (".csv", ".json", ".txt", ".log", ".m"):
        rec["sha256_lf"] = sha256_file_lf(p)          # 줄바꿈 정규화 해시(배포본·Windows 사본 공통)
    return rec


STRICT_RTOL = 1e-6           # 숫자: |a − b| ≤ 1e-6 × max(1, |a|)
STRICT_SKIP = ("sec", "wall_s", "elapsed", "time_s")      # 실행 시간 항목만 제외


def strict_diff(a, b, path="", out=None, rtol=STRICT_RTOL, skip=STRICT_SKIP):
    """두 JSON 값을 엄격하게 비교한다: 키 집합, 배열 길이, 형(문자·불리언·숫자·None), 문자열·불리언 값, 유한 수 여부,
    숫자 상대 차(rtol × max(1, |a|)). 차이 목록 [(경로, 이유, a, b)]를 돌려준다."""
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        ka = {k for k in a if k not in skip}; kb = {k for k in b if k not in skip}
        for k in sorted(ka - kb):
            out.append((path + "/" + str(k), "키가 앞에만 있음", None, None))
        for k in sorted(kb - ka):
            out.append((path + "/" + str(k), "키가 뒤에만 있음", None, None))
        for k in sorted(ka & kb):
            strict_diff(a[k], b[k], path + "/" + str(k), out, rtol, skip)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path, "배열 길이 다름", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            strict_diff(x, y, path + "[%d]" % i, out, rtol, skip)
    elif isinstance(a, bool) or isinstance(b, bool):
        if not (isinstance(a, bool) and isinstance(b, bool)) or a != b:
            out.append((path, "불리언 다름", a, b))
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        fa, fb = float(a), float(b)
        if math.isfinite(fa) != math.isfinite(fb) or (not math.isfinite(fa) and not (fa == fb)):
            out.append((path, "유한 수 여부 다름", a, b))
        elif math.isfinite(fa) and abs(fa - fb) > rtol * max(1., abs(fa)):
            out.append((path, "숫자 차", a, b))
    elif type(a) is not type(b):
        out.append((path, "형 다름", a, b))
    elif a != b:
        out.append((path, "값 다름", a, b))
    return out


def strict_selftest():
    """비교기 자체 시험: 키 삭제·문자열 변경·NaN·길이·불리언 변경은 차이로 잡혀야 한다."""
    base = dict(a=1.0, b="최선", c=[1, 2], d=True, e=dict(x=0.5))
    cases = dict(key_del={k: v for k, v in base.items() if k != "a"}, str_change=dict(base, b="같은 수준"),
                 nan=dict(base, a=float("nan")), length=dict(base, c=[1, 2, 3]), bool_flip=dict(base, d=False),
                 num=dict(base, e=dict(x=0.5 + 1e-3)), type_change=dict(base, d=1))
    res = {k: len(strict_diff(base, v)) > 0 for k, v in cases.items()}
    res["same"] = len(strict_diff(base, json.loads(json.dumps(base)))) == 0
    return res
