#!/bin/bash
# full build: content -> JSON -> docx-js -> cached TOC (2 passes) -> PDF check
set -e
cd "$(dirname "$0")"
SOFF="${SOFFICE:-soffice} --headless --convert-to pdf"   # LibreOffice: cached TOC page numbers only
python3 build_json.py
node build_docx.js raw.docx >/dev/null
python3 toc_cache.py raw.docx it1.docx >/dev/null
timeout 170 $SOFF it1.docx --outdir . >/dev/null 2>&1
python3 find_pages.py it1.pdf pages.json
python3 toc_cache.py raw.docx final.docx pages.json >/dev/null
timeout 170 $SOFF final.docx --outdir . >/dev/null 2>&1
python3 find_pages.py final.pdf pages_check.json
python3 -c "import json;a=json.load(open('pages.json'));b=json.load(open('pages_check.json'));print('TOC pages stable' if a==b else 'TOC pages CHANGED')"
echo "built: $(pwd)/final.docx (Word updates the TOC field on open)"
