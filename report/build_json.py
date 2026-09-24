import json, sys
from PIL import Image
sys.path.insert(0, ".")
from content3 import B
from content1 import COVER
from pathlib import Path
FIG = str(Path(__file__).resolve().parents[1] / "docs" / "fig" / "report") + "/"
for b in B:
    if b["t"] == "fig":
        im = Image.open(FIG + b["img"]); b["wpx"], b["hpx"] = im.size; b["path"] = FIG + b["img"]
json.dump({"cover": COVER, "blocks": B}, open("report.json", "w"), ensure_ascii=False, indent=0)
print(len(B), "blocks;", sum(1 for b in B if b["t"]=="table"), "tables;", sum(1 for b in B if b["t"]=="fig"), "figures")
