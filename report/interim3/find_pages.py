"""Heading -> page numbers from the rendered PDF (pages after the TOC)."""
import json, re, subprocess, sys
pdf, out = sys.argv[1], sys.argv[2]
data = json.load(open("report.json"))
heads = [b["x"] for b in data["blocks"] if b["t"] in ("h1", "h2")]
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
txt = [subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), "-layout", pdf, "-"], capture_output=True, text=True).stdout for k in range(1, n + 1)]
norm = lambda s: re.sub(r"\s+", "", s)
toc_pages = [k + 1 for k, t in enumerate(txt) if t.count("....") >= 5]
start = (max(toc_pages) if toc_pages else 2)  # 0-based index of first body page = last TOC page number
res, k = {}, start
for h in heads:
    key = norm(h)[:40]
    while k < n and key not in norm(txt[k]): k += 1
    if k >= n: res[h] = "?"; k = start; continue
    res[h] = str(k + 1)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=0)
print("pages:", n, "TOC pages:", toc_pages, "missing:", [h for h, v in res.items() if v == "?"])
