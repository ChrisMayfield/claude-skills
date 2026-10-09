#!/usr/bin/env node
// Build a Word version of an activity from its Markdown source, for printing or
// for uploading to Google Docs so students can type their answers.
//
// Usage:
//     node build_docx.js <input.md> <output.docx> [--teacher | --student]
//
// The mode comes from the input filename (`_Teacher.md` or `_Student.md`) unless a
// flag overrides it. Requires the `docx` npm package.
//
// This is a purpose-built reader for the Markdown this skill writes, not a general
// parser. The reasons behind its layout rules are in references/docx-layout.md.

const fs = require("fs");
const path = require("path");

let docx;
try {
  docx = require("docx");
} catch (e) {
  console.error(
    "Error: the 'docx' package is not installed. Run: npm install --prefix <dir> docx, " +
    "then rerun with NODE_PATH=<dir>/node_modules"
  );
  process.exit(1);
}
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  HeadingLevel, WidthType, BorderStyle, ShadingType, AlignmentType,
  PageNumber, Footer, HeightRule, Tab, TabStopType, LineRuleType,
} = docx;

const BODY_FONT = "Calibri";
const MONO_FONT = "Consolas";
const BODY_SIZE = 22;       // half-points (11pt)
const MONO_SIZE = 18;       // 9pt; Consolas looks about as large as Calibri 11pt
const TABLE_SIZE = 20;      // 10pt
const HEADING_SIZES = [32, 28, 24]; // 16pt, 14pt, 12pt
const CONTENT_WIDTH = 9360; // DXA: 12240 page - 2 * 1440 margins
const LANGUAGE = "en-US";   // so screen readers pronounce the text correctly

const PAGE_BREAK_BEFORE = [/^Model \d+\s*:/, /^Facilitation Notes\b/];

const QUESTION_INDENT = { left: 400, hanging: 400 };
const BODY_INDENT = { left: 400 };
const SUBITEM_INDENT = { left: 700 };

// Answer boxes: one-cell tables with an exact row height, the same in both
// versions. Tune BOX_BASE and BOX_PER_LINE if pages do not pack.
const BOX_BASE = 100;          // DXA
const BOX_PER_LINE = 360;      // DXA per writing-space line (0.25 in)
const CODE_BOX_MIN_LINES = 4;  // code answers need room for several lines
// Space above a box, in addition to the 60 after the paragraph that leads into
// it: about 1em (11pt = 220 DXA) from the question to the student's writing.
const BOX_GAP = 160;           // DXA
const BOX_ABOVE = 60 + BOX_GAP; // total space above a box
const NO_BORDER = { style: BorderStyle.NONE, size: 0, color: "auto" };

// The space-before of the block a line starts, so the gap after a box can top it
// up to at least BOX_ABOVE. Keep in step with the builders' spacing.before.
function spaceBefore(line) {
  if (line === undefined) return BOX_ABOVE;
  if (/^#{2,4}\s/.test(line)) return 260;
  if (/^#\s/.test(line)) return BOX_ABOVE; // starts a new page
  if (/^\d+\.\s/.test(line)) return 160;
  if (/^\s*```/.test(line)) return 80;
  if (/^\s+[a-z]\.\s/.test(line)) return 60;
  if (/^\s*[-*]\s/.test(line)) return 20;
  return 40;
}

// Box sizing. These constants and writingLinesFor() must stay in step with
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

// Colors meet WCAG 2.1 AA: text at least 4.5:1 against its background, and lines
// that mark out content at least 3:1 against white. The check below enforces this.
const HEADING_COLOR = "1F4D78";  // 8.8:1 on white
const ANSWER_COLOR = HEADING_COLOR; // 8.4:1 on SAMPLE_FILL
const SAMPLE_FILL = "FAFAFA";
const FOOTER_COLOR = "595959";   // 7.0:1 on white
const CODE_FILL = "F4F4F4";      // black text 19:1
const TABLE_HEAD_FILL = "EEEEEE"; // black text 18:1
const RULE_COLOR = "444444";     // 9.7:1
const QUOTE_COLOR = "8C8C8C";    // 3.4:1

// WCAG 2.1 contrast ratio of two "RRGGBB" colors.
function contrastRatio(a, b) {
  const lum = (hex) => {
    const [r, g, bl] = [0, 2, 4].map((i) => {
      const c = parseInt(hex.slice(i, i + 2), 16) / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * bl;
  };
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// Guard against a color change that breaks contrast: [foreground, background, minimum].
for (const [fg, bg, min] of [
  [ANSWER_COLOR, SAMPLE_FILL, 4.5], [ANSWER_COLOR, "FFFFFF", 4.5], [HEADING_COLOR, "FFFFFF", 4.5],
  [FOOTER_COLOR, "FFFFFF", 4.5], ["000000", CODE_FILL, 4.5], ["000000", TABLE_HEAD_FILL, 4.5],
  [RULE_COLOR, "FFFFFF", 3], [QUOTE_COLOR, "FFFFFF", 3],
]) {
  if (contrastRatio(fg, bg) < min) throw new Error(`Contrast of ${fg} on ${bg} is below ${min}:1`);
}

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
    children: runs(text, { bold: true, size: HEADING_SIZES[level - 1], color: HEADING_COLOR }),
    heading: level === 1 ? HeadingLevel.HEADING_1
      : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
    spacing: { before: level === 1 ? 0 : 260, after: 110 },
    keepNext: true,
    keepLines: true,
    pageBreakBefore,
    border: level === 1
      ? { bottom: { style: BorderStyle.SINGLE, size: 8, color: RULE_COLOR, space: 3 } }
      : undefined,
  });
}

// The number is followed by a real tab element (a "\t" in the text survives Word
// and LibreOffice but Google Docs drops it) to an explicit tab stop at the hanging
// indent (Google Docs does not treat the indent as an implicit stop).
function question(number, text) {
  return new Paragraph({
    children: [
      new TextRun({ children: [`${number}.`, new Tab()], font: BODY_FONT, size: BODY_SIZE }),
      ...runs(text),
    ],
    spacing: { before: 160, after: 60, line: 264 },
    indent: QUESTION_INDENT,
    tabStops: [{ type: TabStopType.LEFT, position: QUESTION_INDENT.left }],
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
    shading: { type: ShadingType.CLEAR, fill: CODE_FILL },
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
  let extra = 0;
  let inFence = false;
  let code = false;
  for (const raw of rawLines.slice(1)) {
    const content = raw.trim().replace(/^>+/, "").trim();
    const line = raw.replace(/^\s*>\s?/, "");
    sampleText += " " + content;
    if (content.startsWith("```")) { code = true; inFence = !inFence; continue; }
    if (inFence) items.push({ code: true, text: line });
    else if (content) items.push({ code: false, text: line });
    else { extra++; continue; }
    wrapped += Math.max(1, Math.ceil(content.length / WRAP_CHARS));
  }
  return { items, code, lines: writingLinesFor(sampleText, wrapped) + extra };
}

// The formatting of answer text: body text or code, in the answer color.
function answerRun(code) {
  return code
    ? { font: MONO_FONT, size: MONO_SIZE, color: ANSWER_COLOR }
    : { font: BODY_FONT, size: BODY_SIZE, color: ANSWER_COLOR };
}

// A space for typed text to inherit its formatting from; Google Docs ignores the
// formatting of an empty paragraph.
function seedRun(code) {
  return new TextRun({ text: " ", ...answerRun(code) });
}

// A paragraph inside an answer box. Teacher samples and the paragraph a student
// types into share this formatting, so typed text matches the sample.
function answerParagraph(code, children = []) {
  return new Paragraph({
    children,
    run: answerRun(code),
    spacing: { before: 0, after: 0, line: code ? 230 : 264 },
  });
}

// No "Sample:" label: the color and shaded box already mark the answer.
function sampleParagraphs(items) {
  if (items.length === 0) return [answerParagraph(false)];
  return items.map((item) => answerParagraph(item.code, item.code
    ? [new TextRun({ text: item.text || " ", ...answerRun(true) })]
    : runs(item.text, { color: ANSWER_COLOR })));
}

// Student: an empty paragraph whose formatting typed text picks up, with no
// borders, so the box prints as blank space. Teacher: the sample, shaded, with a
// blue left edge. A box under a question is indented with the question's text; a
// box under an un-indented prompt (the Problem) spans the full text width.
function answerBox(lines, code, sample, indented, next) {
  const n = code ? Math.max(lines, CODE_BOX_MIN_LINES) : lines;
  const indent = indented ? BODY_INDENT.left : 0;
  const width = CONTENT_WIDTH - indent;
  // A fixed gap above the box, the same in both versions so they stay aligned.
  const gap = (height, keepNext) => new Paragraph({
    children: [],
    spacing: { before: 0, after: 0, line: height, lineRule: LineRuleType.EXACT },
    keepNext,
  });
  // Below the box, at least as much space as above it.
  const below = BOX_ABOVE - spaceBefore(next);
  const box = new Table({
    columnWidths: [width],
    width: { size: width, type: WidthType.DXA },
    indent: { size: indent, type: WidthType.DXA },
    rows: [new TableRow({
      height: { value: BOX_BASE + n * BOX_PER_LINE, rule: HeightRule.EXACT },
      cantSplit: true,
      children: [new TableCell({
        width: { size: width, type: WidthType.DXA },
        borders: {
          top: NO_BORDER,
          bottom: NO_BORDER,
          right: NO_BORDER,
          left: sample ? { style: BorderStyle.SINGLE, size: 12, color: ANSWER_COLOR } : NO_BORDER,
        },
        shading: sample ? { type: ShadingType.CLEAR, fill: SAMPLE_FILL } : undefined,
        // Student writing starts flush with the question text; the teacher's
        // shaded box keeps its padding.
        margins: sample
          ? { top: 80, bottom: 80, left: 115, right: 115 }
          : { top: 0, bottom: 0, left: 0, right: 0 },
        children: sample || [answerParagraph(code, [seedRun(code)])],
      })],
    })],
  });
  return [gap(BOX_GAP, true), box, ...(below > 0 ? [gap(below, false)] : [])];
}

// A blockquote that is not a sample answer (a quotation in a model, say).
function quoteBlock(lines, indented) {
  return lines.filter((t) => t.trim()).map((line, i, all) => new Paragraph({
    children: runs(line),
    spacing: { before: i === 0 ? 60 : 0, after: i === all.length - 1 ? 120 : 0, line: 264 },
    indent: { left: (indented ? BODY_INDENT.left : 0) + 200 },
    keepLines: true,
    keepNext: i < all.length - 1,
    border: { left: { style: BorderStyle.SINGLE, size: 12, color: QUOTE_COLOR, space: 6 } },
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

const TABLE_CHAR = 110;     // DXA per character: wide enough for bold 10pt and Consolas 9pt
const TABLE_CELL_PAD = 380; // DXA: 180 of cell margins plus 200 of slack

// Shrink the widest columns first until the widths fit in max, so narrow columns
// keep their natural width and only long text wraps.
function fitColumns(wanted, max) {
  const widths = wanted.slice();
  let over = widths.reduce((a, b) => a + b, 0) - max;
  while (over > 0) {
    const top = Math.max(...widths);
    const wide = widths.filter((w) => w === top).length;
    const next = Math.max(0, ...widths.filter((w) => w < top));
    const cut = Math.min(top - next, Math.ceil(over / wide));
    widths.forEach((w, i) => { if (w === top) widths[i] -= cut; });
    over -= cut * wide;
  }
  return widths.map(Math.floor);
}

function mdTable(rows) {
  const cols = Math.max(...rows.map((r) => r.length));
  rows = rows.map((r) => r.concat(new Array(cols - r.length).fill("")));
  // Size each column to its longest cell (Markdown markup not counted) at a
  // generous width per character, plus the cell margins and some slack, so short
  // headers such as `team_id` do not wrap.
  const chars = new Array(cols).fill(3);
  rows.forEach((r) => r.forEach((c, i) => {
    chars[i] = Math.max(chars[i], c.replace(/[`*]|\\(?=.)/g, "").length);
  }));
  const colWidths = fitColumns(chars.map((n) => n * TABLE_CHAR + TABLE_CELL_PAD), CONTENT_WIDTH - 200);
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
        shading: ri === 0 ? { type: ShadingType.CLEAR, fill: TABLE_HEAD_FILL } : undefined,
        margins: { top: 30, bottom: 30, left: 90, right: 90 },
        children: [new Paragraph({
          children: runs(cell, { bold: ri === 0, size: TABLE_SIZE }),
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

function image(file, alt, baseDir) {
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
      altText: { name: path.basename(file), title: alt, description: alt },
      transformation: {
        width: Math.round(size.width * scale),
        height: Math.round(size.height * scale),
      },
    })],
  });
}

// --------------------------------------------------------------------- parser

const WRITING = /^\s+&nbsp;\s*$/;
const NBSP = /^\s*&nbsp;\s*$/;
const ANSWER = /^\s*<!--\s*answer(:\s*code)?\s*-->\s*$/;
const COMMENT = /^\s*<!--.*-->\s*$/;
const SEPARATOR = /^&nbsp;\s*$/;
const BLOCK_START = /^(\s*```|\s*\||#{1,4}\s|\s*[-*]\s|\s*>|\s*\d+\.\s|\s*[a-z]\.\s|\s*!\[)/;

// The index of the first non-blank line at or after i (lines.length if none).
function nextLine(lines, i) {
  while (i < lines.length && !lines[i].trim()) i++;
  return i;
}

function convert(mdPath, student) {
  const lines = fs.readFileSync(mdPath, "utf8").replace(/\r\n/g, "\n").split("\n");
  const baseDir = path.dirname(mdPath);
  const children = [];
  const add = (el) => { if (el) children.push(el); };
  let mermaidWarned = false;
  let codeAnswer = false;
  let answerMarked = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;
    const indented = /^\s/.test(line);
    // An answer marker applies only to the writing space right after it, so any
    // other line clears it.
    const marked = answerMarked;
    const code = codeAnswer;
    answerMarked = false;
    codeAnswer = false;

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

    // Indented &nbsp; is writing space; un-indented is a separator, unless an
    // answer marker comes first (writing space for an un-indented sample).
    if (WRITING.test(line) || (marked && NBSP.test(line))) {
      if (student) {
        const pad = line.match(/^\s*/)[0];
        let count = 1;
        let j = nextLine(lines, i + 1);
        while (j < lines.length && NBSP.test(lines[j]) && lines[j].match(/^\s*/)[0] === pad) {
          count++;
          j = nextLine(lines, j + 1);
        }
        i = j - 1;
        answerBox(count, code, undefined, indented, lines[j]).forEach(add);
      } else {
        // Matches the student script, which un-indents these into separators.
        add(spacer());
      }
      continue;
    }
    const marker = line.match(ANSWER);
    if (marker) { answerMarked = true; codeAnswer = Boolean(marker[1]); continue; }
    if (COMMENT.test(line)) continue;
    if (SEPARATOR.test(line)) {
      add(spacer());
      continue;
    }

    // Image on its own line
    const img = line.match(/^\s*!\[([^\]]*)\]\(([^)\s]+)[^)]*\)\s*$/);
    if (img) {
      if (!img[1].trim()) console.error(`Warning: image has no alt text: ${img[2]}`);
      add(image(img[2], img[1].trim(), baseDir));
      continue;
    }

    // Blockquote: a sample answer (teacher version) or an ordinary quotation
    if (/^\s*>/.test(line)) {
      const raw = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) raw.push(lines[i++]);
      i--;
      if (SAMPLE_MARKER.test(raw[0])) {
        const sample = parseSample(raw);
        // Skip the separator after the sample, as the student script does.
        const j = nextLine(lines, i + 1);
        if (j < lines.length && NBSP.test(lines[j])) i = j;
        const next = lines[nextLine(lines, i + 1)];
        answerBox(sample.lines, sample.code, sampleParagraphs(sample.items), indented, next)
          .forEach(add);
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
    const k = nextLine(lines, i + 1);
    const endsSection = k >= lines.length || SEPARATOR.test(lines[k]) || /^#{1,4}\s/.test(lines[k]);
    add(para(buf.join(" "), {
      indent: indented ? BODY_INDENT : undefined,
      keepNext: !endsSection,
    }));
  }

  // Word requires a paragraph after a table that ends the document.
  if (children[children.length - 1] instanceof Table) add(spacer());

  // The first top-level heading is the document title that screen readers announce.
  const titleLine = lines.find((t) => /^#\s/.test(t));
  const title = titleLine
    ? titleLine.replace(/^#\s+/, "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/[`*]|<br\s*\/?>/g, "").replace(/\\(.)/g, "$1").trim()
    : path.basename(mdPath, ".md");

  return new Document({
    title,
    styles: {
      default: {
        document: { run: { font: BODY_FONT, size: BODY_SIZE, language: { value: LANGUAGE } } },
        // Word's built-in heading colors, set explicitly so their contrast is known.
        heading1: { run: { color: HEADING_COLOR } },
        heading2: { run: { color: HEADING_COLOR } },
        heading3: { run: { color: HEADING_COLOR } },
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
            children: [new TextRun({ children: [PageNumber.CURRENT], font: BODY_FONT, size: 18, color: FOOTER_COLOR })],
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
