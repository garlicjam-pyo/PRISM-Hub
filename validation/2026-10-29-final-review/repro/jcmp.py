"""Compare two JSON files numerically: max abs/rel diff over numeric leaves, structural/string mismatches."""
import json
import math
import sys


def walk(a, b, path, acc):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if k not in a or k not in b:
                acc["struct"].append(f"{path}/{k}: only in {'A' if k in a else 'B'}")
            else:
                walk(a[k], b[k], f"{path}/{k}", acc)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            acc["struct"].append(f"{path}: len {len(a)} vs {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", acc)
    elif isinstance(a, bool) or isinstance(b, bool):
        if a != b:
            acc["other"].append(f"{path}: {a!r} vs {b!r}")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        acc["n"] += 1
        if (isinstance(a, float) and math.isnan(a)) or (isinstance(b, float) and math.isnan(b)):
            if not (isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b)):
                acc["other"].append(f"{path}: {a} vs {b}")
            return
        d = abs(a - b)
        r = d / max(abs(b), 1e-300) if d else 0.0
        if d > acc["abs"][0]:
            acc["abs"] = (d, path, a, b)
        if r > acc["rel"][0]:
            acc["rel"] = (r, path, a, b)
    else:
        if a != b:
            acc["other"].append(f"{path}: {str(a)[:60]!r} vs {str(b)[:60]!r}")


def compare(fa, fb, skip=()):
    A = json.load(open(fa, encoding="utf-8")); B = json.load(open(fb, encoding="utf-8"))
    for k in skip:
        A.pop(k, None); B.pop(k, None)
    acc = dict(n=0, abs=(0.0, None, None, None), rel=(0.0, None, None, None), struct=[], other=[])
    walk(A, B, "", acc)
    return acc


if __name__ == "__main__":
    fa, fb = sys.argv[1], sys.argv[2]
    skip = sys.argv[3].split(",") if len(sys.argv) > 3 else ()
    acc = compare(fa, fb, skip)
    print(f"{fa.split('/')[-1]}: numeric leaves {acc['n']}, max abs {acc['abs'][0]:.3g} at {acc['abs'][1]}, "
          f"max rel {acc['rel'][0]:.3g} at {acc['rel'][1]}; struct {len(acc['struct'])}, other {len(acc['other'])}")
    for s in (acc["struct"] + acc["other"])[:8]:
        print("   ", s)
