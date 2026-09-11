# Read the Source Behind a Search Hit

Search finds the likely source. Read checks what it says.

Match reading scope to the question. A question about one fact may need only a short span. A review of a source's main plan needs its material parts, not just the first topic that search finds. Use the source's outline or recap to check coverage, then read the relevant sections and any update that changes the plan. Do not describe selected search hits as a full review. If a required part remains unread, keep the review partial and name the gap.

Before sending a source-based answer, compare the finished draft with the supporting passages. Keep each condition that could change the choice, including a limit added at the end of the answer. Cut repeat wording, not those limits. If a paragraph joins claims from different parts of a source, put each link beside the claim it supports; one early time link does not cover a later reason.

For a source formula or stop rule, distinguish what the page states from the rule you propose. If a cost lacks a denominator, adding “per lead” changes the claim. If a threshold lacks an outcome or time condition, do not fill it in and attribute the completed rule to the author. Keep the source's ambiguity brief and explicit, then calculate what the supplied facts do settle. Your useful recommendation can be clear even when the printed rule is not.

When the user names a book, check the hit's title and source key before reading. A master file may rank above the named book. Use `query --source-key "EXACT_KEY"` to search just that source. Get the key from a matching hit or the file manifest's `source_id`; do not guess it. A search can miss. Try other terms or check the saved source before saying it has no support. Do not change a source's name to fit the request.

Use `--corpus-root` for an exact-file search. It searches that file's saved pages, even when the same text is in other files. It also keeps matching notes about page images from the index. The exact-file search keeps the named file's own title and page links. Search does not prove anyone read the text or checked the image.

Cite the title and page of the file you read. If another file supplies useful context, name it as a separate source. Internal locators such as `file:SOURCE:p0014` are lookup keys, not clickable URLs. The file reader returns `citation_target.markdown_link`, with the actual title and an extracted-text label when needed. Use that link, then add the supporting record's physical page or section. Its checked destination remains in `citation_target.path`. Use a verified original or page image when available; do not invent a PDF page jump. A ready link proves neither that the passage was read nor that it supports the claim.

Use the exact locator from `corpus.py query`. Do not guess a page from a title. Use the root returned by `corpus.py locate`.

```bash
python3 "$HORMOZI_SKILL_DIR/scripts/corpus.py" read --corpus-root /known/corpus/root --locator "EXACT_LOCATOR_FROM_QUERY" --context 1
```

The read gives that page and one page on each side. For a short fact, use `--context 0`. Read more when the rule needs more context. Each call can give up to three nearby pages on each side. This cap does not limit how much you may study.

## Finish the Packet

Each reply gives up to 20,000 text characters. A cut-off page does not count as a full read.

If `next_offset` is not null, call read again with that value as `--offset`. Keep the same locator, context and source-root options. Pass the returned `content_sha256` as `--expected-content-sha256`. This checks the text and, for file sources, the saved records and checked source metadata. A text limit does not include metadata; `packet_complete` means this call returned all packet text, not that images or full source layout were reviewed.

Each record keeps its own locator. It also shows how much of its text this call returned. A blank page is not proof that an image was blank too.

Use the locator for the page that supports the claim. Do not cite a nearby page just because it came in the same packet.

## Read an E-book

An EPUB is an e-book, not a set of fixed pages. The reader keeps old section links stable but returns nearby sections in the book's own reading order. Use its chapter title and `spine_position` when citing a chapter. The `section` number is an extract ID, not a printed page.

The native extract keeps list labels and marks crossed-out or hidden text. Do not treat a crossed-out price as the current offer. `epub_images` links the original image files and checks their saved hashes. Open a needed image before claiming you viewed it; a matching hash alone does not check what it shows. `extraction_warnings` flags layout or styles the text reader cannot fully preserve. Check the original when a warning could change the answer. Older extracts without these fields still need their original structure checked.

## What the Checks Mean

### Workbooks with native rows

Some workbooks have both converted pages and native sheet rows. The reader keeps these views apart. Native section IDs are not page numbers. Cite the sheet name and exact cells instead.

For the Money Models Book Launch Run of Show Blackbook, use [the workbook reading map](doctrine/launch-workbook-review.md) to find its separate tables, key and diagrams. Then check the original cells or images that support the answer. The map is not a substitute for that check.

`xlsx_native` keeps each value with its cell address. It includes the cell's style, note and formula when present. Saved formula results are not a fresh calculation. Recognizable dates use the workbook's own date system; raw date numbers remain intact. Check warnings for dates that cannot be read safely.

`workbook_context` holds shared sheet details and cell styles once per packet. Match each row's `sheet_id` and each cell's `style_index` to those entries. This keeps nearby rows readable without dropping their values or hiding their styles. Plain unformatted text is not repeated as rich text. The full checked catalog and records retain the original detail.

Read the headers and any color key before joining fields. A nearby note can be a separate list. A color may name a sender or draft state; it does not prove a message was sent. `images` gives checked local image paths. Open the image when arrows or layout matter. The checked `native_workbook_supplement.catalog_path` holds the full sheet metadata, styles and themes. These fields help read the original; they do not replace its visuals.

### Word files with native sections

Some Word files have two views: converted pages and native Word sections. Keep their links distinct. Native sections use Word body-block IDs, not printed page numbers. They restore text and table cells that conversion can clip. The reader keeps nearby pages and nearby native sections in separate groups.

`docx_native` shows table row/cell structure, source paragraph numbers, direct crossed-out or hidden marks, links and original image files. Crossed-out draft copy is not an approved claim. Image hashes prove file identity, not visual review. List IDs and levels are retained, but visible list numbering is not guessed; use the original or converted page when the number matters. Follow the returned warnings for layout, inherited styles, notes or drawings. The native body extract supplements the original; it does not replace it.

A tool that ends with no content does not prove a read. Check what it shows before saying you checked text, images or format. If output is blank or cut off, try a safe read again. If you still cannot check it, say what is missing.

For a checked local image path, use the available image-viewing tool (for example, `view_image`) so the image itself reaches the model. A shell command that outputs image bytes or opens a desktop app does not do that. Read a diagram by following its relevant arrows and branch conditions, then explain the path in plain words. Keep exact box labels only where they help the user match your explanation to the image. If no image-capable tool is available, keep the visual check incomplete rather than presenting a saved note as a fresh view.

- File reads check the page's source ID and hash against the source list. A hash is a code used to check if a file changed.
- A page image may have a saved hash. A hash match checks the file, not its meaning. Open the image when needed.
- Missing images stay marked missing. No reader step creates or repairs them.
- Originals may live outside the library. Give `--source-root /known/originals/root` to check them. Do not guess this path.
- An entry with `bundled_original` stores that original under `files/originals/`. The reader checks its hash there without an external root. A missing or changed bundled file is an error, not permission to use a same-named file elsewhere.
- Some image paths use the saved `$HORMOZI_SOURCE_ROOT/` marker. The reader needs that same known root to open them. Without it, image access stays unchecked; a text read is not an image review.
- An original hash match does not prove the text extract is correct. Check the page image when the text is weak or layout matters.
- `saved_visual_review` is a prior human or agent's page-image note, kept apart from extracted text. It may explain a chart or flag wrong OCR. It is not a direct quote or proof that you viewed the image now. Check `image_verified_now` and open the image when it could change the answer. Keep an error printed in the original distinct from an error made while extracting it.
- For a text index, use `--index /known/index.sqlite`. An index holds text for search. Give its known source root to check that text against the source file.
- The legacy indexed video reader gives chunks, not verified raw segments. Use the scoped video helper below for video work. Neither tool proves who spoke or what the video shows.
