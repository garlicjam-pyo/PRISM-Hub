"""검증 스크립트 공용 도구: 결과 폴더 경로, JSON 저장, 판정 출력."""
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent          # 패키지 최상위 폴더
RESULTS = ROOT / "results"


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
    print(f"  → 저장: {path.relative_to(ROOT)}")
    return path


def load_json(eid, name):
    return json.loads((RESULTS / eid / f"{name}.json").read_text(encoding="utf-8"))


def verdict(label, ok, detail=""):
    """판정 결과를 한 줄로 출력한다."""
    print(f"  [{'통과' if ok else '실패'}] {label}" + (f"  ({detail})" if detail else ""))
    return bool(ok)


def workers():
    """병렬 작업 수. 환경변수 PRISM_WORKERS로 바꿀 수 있다(기본: CPU 수)."""
    return int(os.environ.get("PRISM_WORKERS", os.cpu_count() or 1))
