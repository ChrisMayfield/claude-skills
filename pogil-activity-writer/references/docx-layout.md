# Word layout rules

`scripts/build_docx.js` turns the teacher Markdown into teacher and student US Letter Word documents that print cleanly and also work in Google Docs. Each rule below exists because a layout without it printed badly.

## Reading the Markdown

- **Both versions come from one pass over the teacher Markdown.** The student pass differs in only two ways: each answer box is left empty, and the pass stops at `# Facilitation Notes`. Everything else, including every box's size, is computed by the same code. (An earlier design derived a student Markdown file first, with a second copy of the box sizing that had to be kept in step, and comment markers to carry what the indentation of `&nbsp;` lines could not.)
- **A sample marker is found tolerantly** (`SAMPLE_MARKER`), with a warning for anything but the exact `> ***Sample:***<br>`, so extra text on the line cannot leak an answer. A `***Sample` label outside a blockquote stops the build.
- **Every `&nbsp;` line is spacing.** The one right after a sample is dropped, since the box has its own spacing.
- **Question numbers are literal text** followed by a tab, in a paragraph with a hanging indent. The tab must be a real `<w:tab/>` element (docx-js `new Tab()`), with an explicit tab stop at the hanging indent: Google Docs dropped a `\t` written inside the text, which ran "1.Which" together and left the hanging indent showing only from line 2. Word's list numbering is not used: renderers restart lists or ignore start values, and in one attempt every question printed as "1." Literal numbers also keep global numbering (Model 2 continuing from Model 1) exactly as written.
- The script is a purpose-built reader for the shape this skill writes, not a general Markdown parser. It handles headings, paragraphs, bullets, numbered questions, lettered sub-items, blockquote samples (including fenced code inside them), fenced code, pipe tables, `![alt](file.png)` images on their own line, and HTML comments (ignored). If an activity needs something else, extend the reader rather than working around it in the Markdown.

## Answer boxes

- Each sample becomes one **answer box**: a single-cell table with a row height of `BOX_BASE + lines × BOX_PER_LINE`, so it prints sized to the expected answer. Blank space is used rather than ruled lines because lines dictate handwriting size and suggest how many lines to write. (Ruled lines made of bottom borders also fail: Word and LibreOffice merge consecutive identical borders and draw only the last.)
- **Boxes are fixed in size.** The row height is *exact* in both versions, so a student typing a long answer in Word cannot push later questions onto the next page (text past the bottom of the box is hidden rather than reflowed), and a teacher sample can never make its box taller than the student's.
- **The student box is invisible**: no borders and no cell padding, so it prints as plain blank space and typed text lines up with the question text. The teacher box keeps its padding inside the shading.
- **A fixed gap comes before every box**: an empty paragraph exactly `BOX_GAP` tall, which with the 60 after the lead-in paragraph puts the student's writing about 1em (11pt) below the question. A second fixed gap after the box makes the space below it at least as tall as the space above, given the space-before of whatever comes next (`spaceBefore()`, which must stay in step with the builders). Both gaps are identical in both versions, so they do not affect alignment.
- **A box under a question is indented** with the question's text. A box under an un-indented prompt, such as the Problem, spans the full text width. The box follows the indentation of the sample.
- The box's paragraph carries the formatting typed text picks up: Calibri 11pt, or Consolas 9pt for a code answer, in the answer color. A sample with a fenced code block gets a code box, at least `CODE_BOX_MIN_LINES` tall. `answerParagraph()` builds both this paragraph and every teacher sample paragraph, so what a student types matches the sample's font, size, color, and line spacing. (The student code box once typed in Consolas 11pt while the sample printed at 9pt.) The paragraph is not left empty: it holds one space in the box's font and the answer color (`seedRun()`), because Google Docs ignores an empty paragraph's formatting and types in its default black Calibri 11pt (it typed code in Calibri). The cost is that a typed answer may start one space in, depending on where the student clicks. (A zero-width space also worked, but LibreOffice draws a gray mark for each one on screen.)
- If pages do not pack, tune `BOX_PER_LINE` and `BOX_BASE`.

## Keeping the two versions aligned

The two documents match page for page up to the Facilitation Notes, so an instructor can lay them side by side. The versions differ only in what is inside each box, and the teacher sample's blue left edge does not affect the box's height.

**A sample fits its box.** The line count (`writingLinesFor()`) is never less than the printed lines the sample wraps to (`WRAP_CHARS`). Without this floor, a 120-character sample overflowed its two-line box. The estimate can still fall short for a sample with many short lines or wide characters. The author then adds an empty `>` line to the sample, once for each line of room needed; each empty `>` line outside a code fence adds one line to both boxes.

After changing the script, check alignment: the row heights in the two `document.xml` files should be identical in order, and each question number should land at the same position in both PDFs (`pdftotext -bbox-layout`).

## Keeping things together

- **A question keeps with its answer box.** The question paragraph and any lettered sub-items have keep-with-next, and the box's row cannot split, so a question never ends a page with its box stranded on the next one.
- **A paragraph keeps with the next block** unless a separator (`&nbsp;`) or heading follows it, since a paragraph almost always introduces what comes next (a table, the first exercise, the Problem's box). Keying this on a trailing colon was not enough; lead-ins ending in periods were stranded at the foot of a page.
- **Headings keep with the next paragraph.**
- **Code blocks** are shaded, and every line but the last keeps with the next, so a block never splits.
- **Table columns** are sized to their longest cell, at `TABLE_CHAR` per character plus `TABLE_CELL_PAD` for margins and slack; a tighter estimate wrapped short headers (`team_i` / `d`). If a table would be wider than the text column, `fitColumns()` shrinks the widest columns first, so only long text wraps.
- **Tables** have DXA column widths on both the table and each cell (renderers disagree about which one they honor), rows that cannot split, and keep-with-next on every row but the last, so small data tables stay whole.

## Type

Body text is Calibri 11pt. Headings are bold, 16pt, 14pt, and 12pt for levels 1 to 3. Code is Consolas 9pt, which looks about as large as Calibri 11pt because Consolas has a larger x-height. Table text is 10pt. Sample answers are the same size as body text, so if the body size changes, check that `WRAP_CHARS` still matches how many characters fit on a printed sample line; an underestimate cuts off the end of a teacher sample.

## Color

Answers are blue in both versions (`ANSWER_COLOR`, the heading blue `1F4D78`), so they are easy to tell from the black questions: teacher samples in a shaded box with a blue left edge, and whatever a student types. Samples have no "Sample:" label; the label exists only in the Markdown, as the build script's marker. One accent color for headings and answers keeps the page from looking busy; headings are bold and larger, so the two are not confused. The blue is 8.8:1 on white and 8.4:1 on the `FAFAFA` shading (WCAG AAA). Red read as errors at a glance, and green reaches AAA contrast only when so dark it is hard to tell from black, especially with red-green color vision deficiency. A brighter blue such as `2E74B5` stands out more but only just passes AA (4.7:1 on the shading); keep any replacement at 7:1.

## Accessibility

Both documents meet WCAG 2.1 AA:

- **Contrast.** Every text color is at least 4.5:1 against its background, and lines that mark out content (the blue sample edge, the quote edge, the title rule) are at least 3:1. The colors are named constants at the top of `build_docx.js`, and the script refuses to run if one falls below its minimum, so check a new color with `contrastRatio()` before using it. The footer page number was once `777777`, which is 4.48:1 and fails.
- **Structure.** Headings use Word's Heading 1–3 styles, so they appear in the navigation pane and screen readers can jump between them. Data tables repeat a header row. Answer boxes are single-cell layout tables with no header.
- **Metadata.** The document title is taken from the `#` heading, and the language is `en-US`.
- **Images** carry their Markdown alt text (`![alt](file.png)`); the script warns about an image with none.
- Meaning is never carried by color alone: a teacher sample is also marked by its shaded box.

## Google Docs

Faculty may upload the student `.docx` to Google Docs so students can type their answers, usually switching to pageless format, so Google Docs pagination does not matter (it also turns exact row heights into minimums, so boxes grow there). Everything the script emits is chosen to survive that import: literal question numbers, plain tables with a set row height, keep-with-next, page-break-before, and inline images. Do not add text boxes, shapes, fields other than the page number, or Word content controls (checkboxes, fill-in fields).

## Page breaks

- A page break comes before each `## Model N:` heading and before `# Facilitation Notes`, and nowhere else.
- Not before `## Exercises`: a forced break there once left a page holding a single question. The exercises flow on after the last model question, and keep-together rules handle the rest.

