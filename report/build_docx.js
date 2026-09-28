const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Header, Footer,
  AlignmentType, HeadingLevel, WidthType, ShadingType, BorderStyle, VerticalAlign, PageNumber,
  LevelFormat, TableOfContents, PageBreak,
} = require("docx");

const data = JSON.parse(fs.readFileSync(__dirname + "/report.json", "utf8"));
const FONT = { ascii: "Malgun Gothic", eastAsia: "Malgun Gothic", hAnsi: "Malgun Gothic", cs: "Malgun Gothic" };
const CONTENT_W = 9026; // A4 11906 - 2 x 1440
const GRAY = "404040";

function runs(text, opts = {}) {
  const out = [];
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g);
  for (const p of parts) {
    if (!p) continue;
    if (p.startsWith("**") && p.endsWith("**")) out.push(new TextRun({ text: p.slice(2, -2), bold: true, ...opts }));
    else out.push(new TextRun({ text: p, ...opts }));
  }
  return out;
}

const border = (size, color) => ({ style: BorderStyle.SINGLE, size, color });
function makeTable(b) {
  const tot = b.cols.reduce((a, c) => a + c, 0);
  const widths = b.cols.map((c) => Math.floor((c / tot) * CONTENT_W));
  widths[widths.length - 1] += CONTENT_W - widths.reduce((a, c) => a + c, 0);
  const fs_ = b.fs || 17;
  const al = (i) => (b.align && b.align[i] === "c" ? AlignmentType.CENTER : AlignmentType.LEFT);
  const cell = (txt, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { fill: "D9E2F3", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: head ? AlignmentType.CENTER : al(i), spacing: { before: 0, after: 0, line: 260 },
      children: runs(txt, { size: fs_, bold: head ? true : undefined }) })],
  });
  const rows = [];
  if (b.head && b.head.length) rows.push(new TableRow({ tableHeader: true, cantSplit: true, children: b.head.map((h, i) => cell(h, i, true)) }));
  for (const r of b.rows) rows.push(new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, i, false)) }));
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths, rows,
    borders: { top: border(8, GRAY), bottom: border(8, GRAY), left: border(2, "A6A6A6"), right: border(2, "A6A6A6"),
      insideHorizontal: border(2, "A6A6A6"), insideVertical: border(2, "A6A6A6") },
  });
}

const children = [];
// ---------------- cover
const C = data.cover;
children.push(new Paragraph({ spacing: { before: 2200, after: 120 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "PRISM-Hub 프로젝트", bold: true, size: 44, color: "1F3864" })] }));
children.push(new Paragraph({ spacing: { before: 0, after: 360 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "기술 개요 및 연구 진행 상황 보고서", bold: true, size: 40, color: "1F3864" })] }));
children.push(new Paragraph({ spacing: { before: 0, after: 1200 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: C.subtitle, size: 28, color: "404040" })] }));
{
  const w = [2300, CONTENT_W - 2300];
  children.push(new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: w,
    borders: { top: border(8, GRAY), bottom: border(8, GRAY), left: border(0, "FFFFFF"), right: border(0, "FFFFFF"),
      insideHorizontal: border(2, "A6A6A6"), insideVertical: border(2, "A6A6A6") },
    rows: C.rows.map(([k, v]) => new TableRow({ cantSplit: true, children: [
      new TableCell({ width: { size: w[0], type: WidthType.DXA }, shading: { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" },
        margins: { top: 70, bottom: 70, left: 110, right: 110 }, verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: k, bold: true, size: 19 })] })] }),
      new TableCell({ width: { size: w[1], type: WidthType.DXA }, margins: { top: 70, bottom: 70, left: 110, right: 110 },
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({ spacing: { after: 0, line: 270 }, children: [new TextRun({ text: v, size: 19 })] })] }),
    ] })),
  }));
}
children.push(new Paragraph({ children: [new PageBreak()] }));
// ---------------- TOC
children.push(new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: "목차", bold: true, size: 30, color: "1F3864" })] }));
children.push(new TableOfContents("목차", { hyperlink: true, headingStyleRange: "1-2" }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---------------- body
for (const b of data.blocks) {
  if (b.t === "h1") children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(b.x) }));
  else if (b.t === "h2") children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(b.x) }));
  else if (b.t === "p") children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, children: runs(b.x) }));
  else if (b.t === "b") children.push(new Paragraph({ alignment: b.left ? AlignmentType.LEFT : AlignmentType.JUSTIFIED, numbering: { reference: "bullets", level: b.lvl || 0 },
    spacing: { after: 60 }, children: runs(b.x) }));
  else if (b.t === "pb") children.push(new Paragraph({ children: [new PageBreak()] }));
  else if (b.t === "table") {
    if (b.cap) children.push(new Paragraph({ style: "Caption", alignment: AlignmentType.CENTER, keepNext: true, keepLines: true, children: runs(b.cap) }));
    children.push(makeTable(b));
    children.push(new Paragraph({ style: "SourceNote", children: runs(b.src || "") }));
  } else if (b.t === "fig") {
    const wpx = Math.round((b.wcm / 2.54) * 96), hpx = Math.round(wpx * b.hpx / b.wpx);
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60, line: 240, lineRule: "auto" },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(b.path), transformation: { width: wpx, height: hpx },
        altText: { title: b.cap, description: b.cap, name: b.img } })] }));
    children.push(new Paragraph({ style: "Caption", alignment: AlignmentType.CENTER, keepNext: true, children: runs(b.cap) }));
    children.push(new Paragraph({ style: "SourceNote", children: runs(b.src) }));
  } else if (b.t === "refs") {
    b.items.forEach((r, i) => children.push(new Paragraph({ indent: { left: 567, hanging: 567 }, spacing: { after: 80, line: 270 },
      children: [new TextRun({ text: `[${i + 1}]\t`, size: 18 }), new TextRun({ text: r, size: 18 })],
      tabStops: [{ type: "left", position: 567 }] })));
  }
}

const header = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6", space: 4 } },
  children: [new TextRun({ text: "PRISM-Hub 중간 연구 진행 보고서 · v1.1", size: 16, color: "7F7F7F" })] })] });
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "– ", size: 18, color: "7F7F7F" }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "7F7F7F" }),
    new TextRun({ text: " –", size: 18, color: "7F7F7F" })] })] });
const empty = () => new Header({ children: [new Paragraph({ children: [] })] });

const doc = new Document({
  creator: "PRISM-Hub 프로젝트팀", title: C.title, description: "PRISM-Hub 1차 중간 연구 진행 보고서(최종본 v1.1)",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 21 }, paragraph: { spacing: { line: 300, after: 110 } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 30, bold: true, color: "1F3864" }, paragraph: { spacing: { before: 420, after: 200 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true, color: "1F3864" }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1, keepNext: true } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 19, bold: true }, paragraph: { spacing: { before: 160, after: 80 } } },
      { id: "TOC1", name: "toc 1", basedOn: "Normal", next: "Normal", run: { font: FONT, size: 21, bold: true },
        paragraph: { spacing: { before: 100, after: 40, line: 260 } } },
      { id: "TOC2", name: "toc 2", basedOn: "Normal", next: "Normal", run: { font: FONT, size: 20 },
        paragraph: { indent: { left: 440 }, spacing: { before: 0, after: 30, line: 250 } } },
      { id: "SourceNote", name: "Source Note", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 16, color: "404040" }, paragraph: { spacing: { before: 60, after: 240, line: 250 } } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [
    { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 260 } } } },
    { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 800, hanging: 260 } } } },
  ] }] },
  sections: [{
    properties: { titlePage: true, page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440, header: 720, footer: 720 } } },
    headers: { default: header, first: empty() }, footers: { default: footer, first: new Footer({ children: [new Paragraph({ children: [] })] }) },
    children,
  }],
});

const out = process.argv[2] || "/mnt/user-data/outputs/PRISM-Hub_중간보고서_최종본.docx";
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("written", out, buf.length, "bytes"); });
