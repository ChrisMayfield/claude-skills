# Word layout rules

`scripts/build_docx.js` turns the teacher and student Markdown into US Letter Word documents that print cleanly and also work in Google Docs. Each rule below exists because a layout without it printed badly.

## Reading the Markdown

- **Classify `&nbsp;` lines before anything else touches them.** An indented `&nbsp;` is student writing space; an un-indented one is a section separator. The indentation is the only thing that tells them apart, and a generic Markdown converter discards it.
- **Question numbers are literal text** followed by a tab, in a paragraph with a hanging indent. Word's list numbering is not used: renderers restart lists or ignore start values, and in one attempt every question printed as "1." Literal numbers also keep global numbering (Model 2 continuing from Model 1) exactly as written.
- The script is a purpose-built reader for the shape this skill writes, not a general Markdown parser. It handles headings, paragraphs, bullets, numbered questions, lettered sub-items, blockquote samples (including fenced code inside them), fenced code, pipe tables, `![alt](file.png)` images on their own line, and HTML comments (ignored, except the code-answer marker). If an activity needs something else, extend the reader rather than working around it in the Markdown.

## Answer boxes

- Each run of writing-space lines becomes one **answer box**: a single-cell table with a row height of *at least* `BOX_BASE + lines × BOX_PER_LINE`, so it prints sized to the expected answer and grows as a student types. A box is used rather than ruled lines because lines dictate handwriting size and suggest how many lines to write. (Ruled lines made of bottom borders also fail: Word and LibreOffice merge consecutive identical borders and draw only the last.)
- The box's empty paragraph carries the formatting typed text picks up: the body font, or Consolas at single spacing for a code answer (marked by `<!-- answer: code -->`, at least `CODE_BOX_MIN_LINES` tall).
- If pages do not pack, tune `BOX_PER_LINE` and `BOX_BASE`.

## Keeping the two versions aligned

The two documents match page for page up to the Facilitation Notes, so an instructor can lay them side by side. Three things make that work:

- **The teacher sample is printed in a box of the same height.** `writingLinesFor()` in `build_docx.js` is a copy of `writing_lines_for()` in the student script; if you change one, change the other.
- **A sample never stretches its box.** The line count is never less than the printed lines the sample wraps to (`WRAP_CHARS`). Without this floor, a 120-character sample overflowed its two-line box and pushed every later question down.
- **The separator after a sample is dropped in both versions.**

After changing either script, check alignment: the `atLeast` row heights in the two `document.xml` files should be identical in order, and each question number should land at the same position in both PDFs (`pdftotext -bbox-layout`).

## Keeping things together

- **A question keeps with its answer box.** The question paragraph and any lettered sub-items have keep-with-next, and the box's row cannot split, so a question never ends a page with its box stranded on the next one.
- **A paragraph keeps with the next block** unless a separator (`&nbsp;`) or heading follows it, since a paragraph almost always introduces what comes next (a table, the first exercise, the Problem's box). Keying this on a trailing colon was not enough; lead-ins ending in periods were stranded at the foot of a page.
- **Headings keep with the next paragraph.**
- **Code blocks** are shaded, and every line but the last keeps with the next, so a block never splits.
- **Tables** have DXA column widths on both the table and each cell (renderers disagree about which one they honor), rows that cannot split, and keep-with-next on every row but the last, so small data tables stay whole.
- **Sample answers** (teacher version) are purple `7B1FA2` in a shaded box with a purple left edge, with no "Sample:" label; the label exists only in the Markdown, as the student script's marker. Red read as errors at a glance, and green reaches AAA contrast only when so dark it is hard to tell from black, especially with red-green color vision deficiency. Any replacement must keep 7:1 against the `FAFAFA` shading (WCAG AAA).

## Google Docs

Faculty may upload the student `.docx` to Google Docs so students can type their answers. Everything the script emits is chosen to survive that import: literal question numbers, plain tables with a minimum row height, keep-with-next, page-break-before, and inline images. Do not add text boxes, shapes, fields other than the page number, or Word content controls (checkboxes, fill-in fields).

## Page breaks

- A page break comes before each `## Model N:` heading and before `# Facilitation Notes`, and nowhere else.
- Not before `## Exercises`: a forced break there once left a page holding a single question. The exercises flow on after the last model question, and keep-together rules handle the rest.

