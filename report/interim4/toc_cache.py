"""Insert cached TOC entries (text + page) into the docx-js TOC field so that viewers that do not
update fields still show a table of contents. Word regenerates the field on open (updateFields)."""
import json, re, sys, zipfile, shutil, subprocess, os, html
src, dst, pages_json = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else None)
data = json.load(open("report.json"))
heads = [(1 if b["t"] == "h1" else 2, b["x"]) for b in data["blocks"] if b["t"] in ("h1", "h2")]
pages = json.load(open(pages_json)) if pages_json and os.path.exists(pages_json) else {}
def para(level, text, page):
    t = html.escape(text, quote=False)
    return ('<w:p><w:pPr><w:pStyle w:val="TOC%d"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9016"/></w:tabs></w:pPr>'
            '<w:r><w:t xml:space="preserve">%s</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>%s</w:t></w:r></w:p>') % (level, t, page)
tmp = dst + ".tmpdir"; shutil.rmtree(tmp, ignore_errors=True)
with zipfile.ZipFile(src) as z: z.extractall(tmp)
p = os.path.join(tmp, "word", "document.xml"); x = open(p, encoding="utf-8").read()
i = x.find('>TOC '); assert i > 0, "TOC field not found"
j = x.find('</w:p>', i) + len('</w:p>')
entries = "".join(para(l, t, pages.get(t, "")) for l, t in heads)
x = x[:j] + entries + x[j:]
open(p, "w", encoding="utf-8").write(x)
if os.path.exists(dst): os.remove(dst)
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    # [Content_Types].xml first, as Word expects
    order = ["[Content_Types].xml"]
    for root, _, files in os.walk(tmp):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), tmp)
            if rel not in order: order.append(rel)
    for rel in order: z.write(os.path.join(tmp, rel), rel)
shutil.rmtree(tmp)
print("cached", len(heads), "TOC entries ->", dst)
