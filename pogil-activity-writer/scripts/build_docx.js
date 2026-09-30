#!/usr/bin/env node
// Build a Word version of an activity from its Markdown source, for printing or
// for uploading to Google Docs so students can type their answers.
//
// Usage:
//     node build_docx.js <input.md> <output.docx> [--teacher | --student]
//
// The mode comes from the input filename (`_Teacher.md` or `_Student.md`) unless a
// flag overrides it. Requires the `docx` package (npm install docx).
//
// This is a purpose-built reader for the Markdown this skill writes, not a general
// parser. The reasons behind its layout rules are in references/docx-layout.md.

const fs = require("fs");
const path = require("path");

let docx;
try {
  docx = require("docx");
} catch (e) {
  console.error("Error: the 'docx' package is not installed. Run: npm install docx");
  process.exit(1);
}
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  HeadingLevel, WidthType, BorderStyle, ShadingType, AlignmentType,
  PageNumber, Footer, HeightRule,
} = docx;

const BODY_FONT = "Calibri";
const MONO_FONT = "Consolas";
const BODY_SIZE = 21;       // half-points (10.5pt)
const MONO_SIZE = 17;       // 8.5pt
const CONTENT_WIDTH = 9360; // DXA: 12240 page - 2 * 1440 margins

const PAGE_BREAK_BEFORE = [/^Model \d+\s*:/, /^Facilitation Notes\b/];

const QUESTION_INDENT = { left: 400, hanging: 400 };
const BODY_INDENT = { left: 400 };
const SUBITEM_INDENT = { left: 700 };

// Answer boxes: one-cell tables with a minimum row height, so they print at a size
// proportional to the answer and grow as a student types. Tune these if pages do
// not pack.
const BOX_BASE = 100;          // DXA
const BOX_PER_LINE = 360;      // DXA per writing-space line (0.25 in)
const CODE_BOX_MIN_LINES = 4;  // code answers need room for several lines
const BOX_BORDER = { style: BorderStyle.SINGLE, size: 6, color: "A6A6A6" };

// Each teacher sample sits in a box the same height as the student's, so the two
// versions line up page for page. writingLinesFor() must stay in step with
// writing_lines_for() in generate_student_version.py.
const CHARS_PER_LINE = 70;
const MIN_WRITING_LINES = 2;
const MAX_WRITING_LINES = 8;
const WRAP_CHARS = 90;

function writingLinesFor(sampleText, renderedLines) {
  const estimated = sampleText.trim()
    ? Math.floor(sampleText.length / CHARS_PER_LINE) + 1
    : MIN_WRITING_LINES;
  const clamped = Math.max(MIN_WRITING_LINES, Math.min(MAX_WRITING_LINES, estimated));
  return Math.max(clamped, renderedLines);
}

// The sample marker, matched as tolerantly as the student script matches it.
const SAMPLE_MARKER = /^(\s*)>\s*(.*?)\*\*\*Sample\b[^*]*\*\*\*(.*?)\s*$/;
const CANONICAL_MARKER = /^\s*> \*\*\*Sample:\*\*\*<br>\s*$/;

// Sample answers are purple: 7.9:1 on the shading (WCAG AAA). See the reference
// for why not red or green.
const SAMPLE_COLOR = "7B1FA2";
const SAMPLE_FILL = "FAFAFA";

// ---------------------------------------------------------------- inline runs

// Handles `code`, ***bold italic***, **bold**, *italic*, [links](url), and drops <br>.
function runs(text, base = {}) {
  const out = [];
  const re = /(`[^`]+`)|(\*\*\*[^*]+\*\*\*)|(\*\*[^*]+\*\*)|(\*[^*]+\*)/g;
  // Hide backslash escapes (`\*`) from the emphasis match behind private-use
  // placeholders; restore them bare in prose and with the backslash in code spans.
  text = text.replace(/\\([\\`*_{}\[\]()#+\-.!|])/g,
    (_, c) => String.fromCharCode(0xe000 + c.charCodeAt(0)));
  const restore = (s, keepBackslash) => s.replace(/[\ue000-\ue07f]/g,
    (p) => (keepBackslash ? "\\" : "") + String.fromCharCode(p.charCodeAt(0) - 0xe000));
  const clean = (s) => restore(s
    .replace(/<br\s*\/?>/g, "")
    .replace(/&nbsp;/g, "\u00a0")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1"), false);
  const push = (t, opts) => {
    if (!t) return;
    out.push(new TextRun({
      text: t,
      font: opts.mono ? MONO_FONT : BODY_FONT,
      size: opts.mono ? MONO_SIZE : (base.size || BODY_SIZE),
      bold: opts.bold || base.bold,
      italics: opts.italics || base.italics,
      color: base.color,
    }));
  };
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    push(clean(text.slice(last, m.index)), {});
    if (m[1]) push(restore(m[1].slice(1, -1), true), { mono: true });
    else if (m[2]) push(clean(m[2].slice(3, -3)), { bold: true, italics: true });
    else if (m[3]) push(clean(m[3].slice(2, -2)), { bold: true });
    else if (m[4]) push(clean(m[4].slice(1, -1)), { italics: true });
    last = re.lastIndex;
  }
  push(clean(text.slice(last)), {});
  return out;
}

// ------------------------------------------------------------------- builders

function para(text, opts = {}) {
  return new Paragraph({
    children: runs(text, opts),
    spacing: { before: opts.before ?? 40, after: opts.after ?? 60, line: 264 },
    indent: opts.indent,
    keepNext: opts.keepNext,
    keepLines: true,
  });
}

function heading(text, level, pageBreakBefore) {
  return new Paragraph({
    children: runs(text, { bold: true, size: level === 1 ? 30 : level === 2 ? 25 : 22 }),
    heading: level === 1 ? HeadingLevel.HEADING_1
      : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
    spacing: { before: level === 1 ? 0 : 260, after: 110 },
    keepNext: true,
    keepLines: true,
    pageBreakBefore,
    border: level === 1
      ? { bottom: { style: BorderStyle.SINGLE, size: 8, color: "444444", space: 3 } }
      : undefined,
  });
}

function question(number, text) {
  return new Paragraph({
    children: [
      new TextRun({ text: `${number}.\t`, font: BODY_FONT, size: BODY_SIZE }),
      ...runs(text),
    ],
    spacing: { before: 160, after: 60, line: 264 },
    indent: QUESTION_INDENT,
    keepLines: true,
    keepNext: true,
  });
}

function codeBlock(lines, indented) {
  return lines.map((line, i) => new Paragraph({
    children: [new TextRun({ text: line || " ", font: MONO_FONT, size: MONO_SIZE })],
    spacing: { before: i === 0 ? 80 : 0, after: i === lines.length - 1 ? 100 : 0, line: 230 },
    indent: { left: indented ? 600 : 200 },
    keepLines: true,
    keepNext: i < lines.length - 1,
    shading: { type: ShadingType.CLEAR, fill: "F4F4F4" },
  }));
}

// Split a sample block into the lines to print, and size its box the way the
// student script does.
function parseSample(rawLines) {
  const marker = rawLines[0].match(SAMPLE_MARKER);
  let sampleText = "";
  if (!CANONICAL_MARKER.test(rawLines[0])) {
    sampleText = " " + `${marker[2]} ${marker[3]}`.replace(/<br>/g, "").trim();
  }
  const items = [];
  let wrapped = 0;
  let inFence = false;
  let code = false;
  for (const raw of rawLines.slice(1)) {
    const content = raw.trim().replace(/^>+/, "").trim();
    const line = raw.replace(/^\s*>\s?/, "");
    sampleText += " " + content;
    if (content.startsWith("```")) { code = true; inFence = !inFence; continue; }
    if (inFence) items.push({ code: true, text: line });
    else if (content) items.push({ code: false, text: line });
    else continue;
    wrapped += Math.max(1, Math.ceil(content.length / WRAP_CHARS));
  }
  return { items, code, lines: writingLinesFor(sampleText, wrapped) };
}

// No "Sample:" label: the color and shaded box already mark the answer.
function sampleParagraphs(items) {
  if (items.length === 0) return [new Paragraph({ children: [] })];
  return items.map((item) => new Paragraph({
    children: item.code
      ? [new TextRun({ text: item.text || " ", font: MONO_FONT, size: MONO_SIZE, color: SAMPLE_COLOR })]
      : runs(item.text, { size: 20, color: SAMPLE_COLOR }),
    spacing: { before: 0, after: 0, line: item.code ? 230 : 250 },
  }));
}

// Student: an empty paragraph whose formatting typed text picks up.
// Teacher: the sample, shaded, with a purple left edge.
function answerBox(lines, code, sample) {
  const n = code ? Math.max(lines, CODE_BOX_MIN_LINES) : lines;
  const width = CONTENT_WIDTH - BODY_INDENT.left;
  const empty = code
    ? new Paragraph({
      run: { font: MONO_FONT, size: BODY_SIZE },
      spacing: { before: 0, after: 0, line: 240 },
    })
    : new Paragraph({
      run: { font: BODY_FONT, size: BODY_SIZE },
      spacing: { before: 0, after: 60, line: 264 },
    });
  return new Table({
    columnWidths: [width],
    width: { size: width, type: WidthType.DXA },
    indent: { size: BODY_INDENT.left, type: WidthType.DXA },
    rows: [new TableRow({
      height: { value: BOX_BASE + n * BOX_PER_LINE, rule: HeightRule.ATLEAST },
      cantSplit: true,
      children: [new TableCell({
        width: { size: width, type: WidthType.DXA },
        borders: {
          top: BOX_BORDER,
          bottom: BOX_BORDER,
          right: BOX_BORDER,
          left: sample ? { style: BorderStyle.SINGLE, size: 12, color: SAMPLE_COLOR } : BOX_BORDER,
        },
        shading: sample ? { type: ShadingType.CLEAR, fill: SAMPLE_FILL } : undefined,
        margins: { top: 80, bottom: 80, left: 115, right: 115 },
        children: sample || [empty],
      })],
    })],
  });
}

// A blockquote that is not a sample answer (a quotation in a model, say).
function quoteBlock(lines, indented) {
  return lines.filter((t) => t.trim()).map((line, i, all) => new Paragraph({
    children: runs(line),
    spacing: { before: i === 0 ? 60 : 0, after: i === all.length - 1 ? 120 : 0, line: 264 },
    indent: { left: (indented ? BODY_INDENT.left : 0) + 200 },
    keepLines: true,
    keepNext: i < all.length - 1,
    border: { left: { style: BorderStyle.SINGLE, size: 12, color: "BBBBBB", space: 6 } },
  }));
}

function spacer() {
  return new Paragraph({ children: [new TextRun({ text: "", size: 12 })], spacing: { after: 0 } });
}

function bullet(text, level) {
  return new Paragraph({
    children: runs(text),
    bullet: { level },
    spacing: { before: 20, after: 40, line: 264 },
    keepLines: true,
    keepNext: /:$/.test(text.trim()),
  });
}

function mdTable(rows) {
  const cols = Math.max(...rows.map((r) => r.length));
  rows = rows.map((r) => r.concat(new Array(cols - r.length).fill("")));
  const widths = new Array(cols).fill(0);
  rows.forEach((r) => r.forEach((c, i) => { widths[i] = Math.max(widths[i], c.length, 3); }));
  const total = widths.reduce((a, b) => a + b, 0);
  // Size the table to its content (these are usually narrow data samples), capped
  // at the text column, then scale columns so their widths sum to the table width.
  const tableWidth = Math.min(CONTENT_WIDTH - 200, Math.round(total * 115) + 400);
  let colWidths = widths.map((w) => Math.max(700, Math.round((w / total) * tableWidth)));
  const scale = Math.min(1, (CONTENT_WIDTH - 200) / colWidths.reduce((a, b) => a + b, 0));
  colWidths = colWidths.map((w) => Math.floor(w * scale));
  const sum = colWidths.reduce((a, b) => a + b, 0);

  return new Table({
    columnWidths: colWidths,
    width: { size: sum, type: WidthType.DXA },
    indent: { size: 200, type: WidthType.DXA },
    rows: rows.map((cells, ri) => new TableRow({
      tableHeader: ri === 0,
      cantSplit: true,
      children: cells.map((cell, ci) => new TableCell({
        width: { size: colWidths[ci], type: WidthType.DXA },
        shading: ri === 0 ? { type: ShadingType.CLEAR, fill: "EEEEEE" } : undefined,
        margins: { top: 30, bottom: 30, left: 90, right: 90 },
        children: [new Paragraph({
          children: runs(cell, { bold: ri === 0, size: 19 }),
          spacing: { before: 0, after: 0, line: 240 },
          // Keeping every row but the last with the next holds the table together.
          keepNext: ri < rows.length - 1,
        })],
      })),
    })),
  });
}

// Pixel dimensions from a PNG or JPEG header, or null if it cannot be parsed.
function imageSize(buf) {
  if (buf.length >= 24 && buf.readUInt32BE(0) === 0x89504e47) {
    return { type: "png", width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
  }
  if (buf.length >= 4 && buf[0] === 0xff && buf[1] === 0xd8) {
    let i = 2;
    while (i + 3 < buf.length) {
      if (buf[i] !== 0xff) return null;        // lost sync with the marker stream
      const marker = buf[i + 1];
      if (marker === 0xff) { i++; continue; }  // fill byte before a marker
      if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd8)) {
        i += 2;                                // standalone marker, no length
        continue;
      }
      if (marker === 0xd9 || marker === 0xda) return null; // image data, no frame found
      const len = buf.readUInt16BE(i + 2);
      if (len < 2) return null;
      // Start-of-frame markers carry the dimensions: C0-CF except DHT (C4),
      // JPG (C8), and DAC (CC).
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        if (i + 9 > buf.length) return null;
        return { type: "jpg", height: buf.readUInt16BE(i + 5), width: buf.readUInt16BE(i + 7) };
      }
      i += 2 + len;
    }
  }
  return null;
}

function image(file, baseDir) {
  const full = path.resolve(baseDir, file);
  if (!fs.existsSync(full)) {
    console.error(`Warning: image not found, skipped: ${full}`);
    return null;
  }
  const data = fs.readFileSync(full);
  const size = imageSize(data);
  if (!size) {
    console.error(`Warning: not a readable PNG or JPEG, skipped: ${full}`);
    return null;
  }
  const maxWidth = 576; // docx-js sizes images in pixels at 96 dpi; 6 in = 576 px
  const scale = Math.min(1, maxWidth / size.width);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 100 },
    keepNext: true,
    children: [new ImageRun({
      type: size.type,
      data,
      transformation: {
        width: Math.round(size.width * scale),
        height: Math.round(size.height * scale),
      },
    })],
  });
}

// --------------------------------------------------------------------- parser

const WRITING = /^\s+&nbsp;\s*$/;
const CODE_ANSWER = /^\s*<!--\s*answer:\s*code\s*-->\s*$/;
const COMMENT = /^\s*<!--.*-->\s*$/;
const SEPARATOR = /^&nbsp;\s*$/;
const BLOCK_START = /^(\s*```|\s*\||#{1,4}\s|\s*[-*]\s|\s*>|\s*\d+\.\s|\s*[a-z]\.\s|\s*!\[)/;

function convert(mdPath, student) {
  const lines = fs.readFileSync(mdPath, "utf8").replace(/\r\n/g, "\n").split("\n");
  const baseDir = path.dirname(mdPath);
  const children = [];
  const add = (el) => { if (el) children.push(el); };
  let mermaidWarned = false;
  let codeAnswer = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;
    const indented = /^\s/.test(line);

    // Fenced code block (possibly indented under a question)
    const fence = line.match(/^(\s*)```\s*(\w*)/);
    if (fence) {
      if (fence[2] === "mermaid" && !mermaidWarned) {
        console.error("Warning: a mermaid block is printed as source text. "
          + "Render it to PNG and reference it with ![alt](file.png) instead.");
        mermaidWarned = true;
      }
      const pad = fence[1].length;
      const buf = [];
      i++;
      while (i < lines.length && !/^\s*```/.test(lines[i])) buf.push(lines[i++].slice(pad));
      codeBlock(buf, pad > 0).forEach(add);
      continue;
    }

    // Table
    if (/^\s*\|/.test(line)) {
      const rows = [];
      while (i < lines.length && /^\s*\|/.test(lines[i])) {
        const cells = lines[i].trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
        if (!cells.every((c) => /^:?-{2,}:?$/.test(c))) rows.push(cells);
        i++;
      }
      i--;
      add(mdTable(rows));
      add(spacer());
      continue;
    }

    // Heading
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      const text = h[2].trim();
      const brk = PAGE_BREAK_BEFORE.some((re) => re.test(text));
      add(heading(text, Math.min(h[1].length, 3), brk));
      continue;
    }

    // Indented &nbsp; is writing space; un-indented is a separator.
    if (WRITING.test(line)) {
      if (student) {
        let count = 1;
        let j = i + 1;
        for (;;) {
          while (j < lines.length && !lines[j].trim()) j++;
          if (j < lines.length && WRITING.test(lines[j])) { count++; j++; } else break;
        }
        i = j - 1;
        add(answerBox(count, codeAnswer));
        codeAnswer = false;
      } else {
        // Matches the student script, which un-indents these into separators.
        add(spacer());
      }
      continue;
    }
    if (CODE_ANSWER.test(line)) { codeAnswer = true; continue; }
    if (COMMENT.test(line)) continue;
    if (SEPARATOR.test(line)) {
      add(spacer());
      continue;
    }

    // Image on its own line
    const img = line.match(/^\s*!\[[^\]]*\]\(([^)\s]+)[^)]*\)\s*$/);
    if (img) { add(image(img[1], baseDir)); continue; }

    // Blockquote: a sample answer (teacher version) or an ordinary quotation
    if (/^\s*>/.test(line)) {
      const raw = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) raw.push(lines[i++]);
      i--;
      if (SAMPLE_MARKER.test(raw[0])) {
        const sample = parseSample(raw);
        add(answerBox(sample.lines, sample.code, sampleParagraphs(sample.items)));
        // Skip the separator after the sample, as the student script does.
        let j = i + 1;
        while (j < lines.length && !lines[j].trim()) j++;
        if (j < lines.length && /^\s*&nbsp;\s*$/.test(lines[j])) i = j;
      } else {
        quoteBlock(raw.map((t) => t.replace(/^\s*>\s?/, "")), indented).forEach(add);
      }
      continue;
    }

    // Bullet (two or more spaces of indentation nests it one level)
    const b = line.match(/^(\s*)[-*]\s+(.*)$/);
    if (b) { add(bullet(b[2], b[1].length >= 2 ? 1 : 0)); continue; }

    // Numbered question: keep the number exactly as written
    const q = line.match(/^(\d+)\.\s+(.*)$/);
    if (q) { add(question(q[1], q[2])); continue; }

    // Lettered sub-item inside a question
    const sub = line.match(/^\s+([a-z])\.\s+(.*)$/);
    if (sub) {
      add(para(`${sub[1]}. ${sub[2]}`, { indent: SUBITEM_INDENT, keepNext: true, before: 60 }));
      continue;
    }

    // Plain paragraph: consecutive sentence-per-line text.
    const buf = [line.trim()];
    while (i + 1 < lines.length && lines[i + 1].trim()
      && !BLOCK_START.test(lines[i + 1]) && !/&nbsp;/.test(lines[i + 1])) {
      buf.push(lines[++i].trim());
    }
    // A paragraph introduces what follows it, so it keeps with it unless a
    // separator or heading comes next.
    let k = i + 1;
    while (k < lines.length && !lines[k].trim()) k++;
    const endsSection = k >= lines.length || SEPARATOR.test(lines[k]) || /^#{1,4}\s/.test(lines[k]);
    add(para(buf.join(" "), {
      indent: indented ? BODY_INDENT : undefined,
      keepNext: !endsSection,
    }));
  }

  // Word requires a paragraph after a table that ends the document.
  if (children[children.length - 1] instanceof Table) add(spacer());

  return new Document({
    styles: {
      default: {
        document: { run: { font: BODY_FONT, size: BODY_SIZE } },
      },
    },
    sections: [{
      properties: {
        page: {
          size: { width: 12240, height: 15840 }, // US Letter
          margin: { top: 1080, bottom: 1080, left: 1440, right: 1440 },
        },
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ children: [PageNumber.CURRENT], size: 17, color: "777777" })],
          })],
        }),
      },
      children,
    }],
  });
}

// ----------------------------------------------------------------------- main

function main(argv) {
  const flags = argv.filter((a) => a.startsWith("--"));
  const args = argv.filter((a) => !a.startsWith("--"));
  if (args.length !== 2 || flags.some((f) => f !== "--teacher" && f !== "--student")) {
    console.error("Usage: node build_docx.js <input.md> <output.docx> [--teacher | --student]");
    return 2;
  }
  const [input, output] = args.map((p) => path.resolve(p));
  if (!fs.existsSync(input)) {
    console.error(`Error: file not found: ${input}`);
    return 1;
  }

  let student;
  if (flags.includes("--student")) student = true;
  else if (flags.includes("--teacher")) student = false;
  else if (/_Student\.md$/.test(input)) student = true;
  else if (/_Teacher\.md$/.test(input)) student = false;
  else {
    console.error("Error: cannot tell teacher from student by filename; pass --teacher or --student.");
    return 1;
  }

  const doc = convert(input, student);
  return Packer.toBuffer(doc).then((buf) => {
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, buf);
    console.log(`Wrote: ${output}`);
    return 0;
  });
}

Promise.resolve(main(process.argv.slice(2))).then((code) => { process.exitCode = code; });
