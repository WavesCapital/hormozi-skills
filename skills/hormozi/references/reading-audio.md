# Original audio access

## Read Original Audio

Use `scripts/audio_source.py` for original audiobooks and audio-only files. These sources are separate from YouTube and printed editions. A file manifest can show zero page records while its `audio_transcripts` entry points to the full saved audio evidence. Do not treat that page count as a missing transcript.

Set `CORPUS` to the checked library root. `ORIGINALS` is the known original-source folder from the source records or the user's supplied path, not a guessed folder. List returns source IDs without transcript bodies. Choose the matching title, then keep its returned catalog hash for the read and search calls.

```bash
python3 "$HORMOZI_SKILL_DIR/scripts/audio_source.py" list --corpus-root "$CORPUS"
python3 "$HORMOZI_SKILL_DIR/scripts/audio_source.py" search --corpus-root "$CORPUS" --source-root "$ORIGINALS" --source-id "EXACT_ID" --expected-catalog-sha256 "RETURNED_HASH" --query "words to find"
python3 "$HORMOZI_SKILL_DIR/scripts/audio_source.py" read --corpus-root "$CORPUS" --source-root "$ORIGINALS" --source-id "EXACT_ID" --expected-catalog-sha256 "RETURNED_HASH" --start-seconds START --end-seconds END
```

Search matches all supplied words in a segment. Try fewer words or another term if it misses. Read the nearby span to check the thought, not just the matching line. Calls check the original file, its owning manifest, saved receipts and transcript hashes. Missing or changed evidence is an access gap; do not silently substitute a print edition.

Times are seconds in the original file, including for short rechecks. The default `--version full` reads the full recording's transcript. `related_rechecks` shows any separate passes and saved review notes for the requested span. To read one, repeat the span with its exact `--version` ID. A recheck is another machine pass, not a silent correction or a fresh listen. Check both when their disagreement could change the answer. State an unresolved number or wording conflict rather than fixing the source from what seems plausible.

Packets contain whole segments, up to 80 segments and 20,000 text characters by default. Follow `next_offset` with the same source, version, span or query, catalog hash and returned `--expected-content-sha256`. The offset counts segments. Finish all needed packets before claiming a span was read.

Cite the returned `original_path` as a clickable title and give the exact supporting time span. Do not invent a player time-jump URL. Saved transcripts and review notes support paraphrases with their stated limits; they do not prove a fresh listen, exact spoken wording, or that the written edition says the same thing. If listening is needed to settle an important conflict, use an available audio-capable tool and record what was actually checked.
