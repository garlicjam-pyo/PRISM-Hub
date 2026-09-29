import json, re, sys
from PIL import Image
sys.path.insert(0, ".")
from content3 import B
from content1 import COVER
from pathlib import Path
FIG = str(Path(__file__).resolve().parents[1] / "docs" / "fig" / "report") + "/"

# Table/figure labels {t:key} / {f:key} are numbered in order of appearance of their captions.
num = {"t": {}, "f": {}}
for b in B:
    key = ("t", b.get("cap", "")) if b["t"] == "table" else ("f", b.get("cap", "")) if b["t"] == "fig" else None
    if key is None: continue
    m = re.match(r"(?:표|그림) \{([tf]):([^}]+)\}\.", key[1])
    if m and m.group(2) not in num[m.group(1)]:
        num[m.group(1)][m.group(2)] = str(len(num[m.group(1)]) + 1)

def resolve(o):
    if isinstance(o, str):
        def rep(m):
            kind, k = m.group(1), m.group(2)
            if k not in num[kind]: raise KeyError(f"undefined label {{{kind}:{k}}}")
            return num[kind][k]
        return re.sub(r"\{([tf]):([^}]+)\}", rep, o)
    if isinstance(o, list): return [resolve(x) for x in o]
    if isinstance(o, dict): return {k: resolve(v) for k, v in o.items()}
    return o

B2, COVER2 = resolve(B), resolve(COVER)
for b in B2:
    if b["t"] == "fig":
        im = Image.open(FIG + b["img"]); b["wpx"], b["hpx"] = im.size; b["path"] = FIG + b["img"]
json.dump({"cover": COVER2, "blocks": B2}, open("report.json", "w"), ensure_ascii=False, indent=0)
json.dump(num, open("labels.json", "w"), ensure_ascii=False, indent=0)
print(len(B2), "blocks;", sum(1 for b in B2 if b["t"] == "table"), "tables;", sum(1 for b in B2 if b["t"] == "fig"), "figures")
