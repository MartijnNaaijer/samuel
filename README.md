# Samuel — Masoretic Text ∥ Dead Sea Scrolls

A verse-by-verse parallel edition of the book of Samuel: the **Masoretic Text**
(from the ETCBC BHSA database) shown together with the four main **Qumran
manuscripts** of Samuel, for close reading by Hebraists.

## View it online

Visit the published site:

https://martijnnaaijer.github.io/samuel

The pages are static HTML with no build step and no external libraries — the only
script is a few lines inline, which position the hover cards — so
**`docs/index.html`** can also be opened straight from disk. The one thing they do
fetch over the network is the Hebrew webfont (Frank Ruhl Libre, from Google Fonts);
offline they fall back to whatever Hebrew serif font is installed locally.

## What's inside

One page per chapter (1 Samuel 1–31, 2 Samuel 1–24) plus an index. For each verse
the pointed **Masoretic Text** is shown on top and the **Dead Sea Scroll**
reading(s) directly beneath it.

- **Reconstruction is marked** in the scroll text, following the critical editions:
  - `[ … ]` (grey) — editorially reconstructed letters
  - a dot above a letter — an uncertain reading
  - `°` — a letter preserved only as illegible traces
  - `.` — a lost letter inside a lacuna
- **Hover over any word** to see its lexeme — in ETCBC transliteration, so that the
  Masoretic and scroll lines can be compared in one notation — and its morphology:
  part of speech, verbal stem and tense (for verbs), person, gender, and number.
- **Vocalization slider** — switch the Masoretic Text between full pointing /
  cantillation and consonants only.

The four scrolls attest 54 of Samuel's 55 chapters; only 1 Samuel 13 has no scroll evidence.

## The scrolls

| Siglum  | Number |
| ------- | ------ |
| 4QSamᵃ  | 4Q51   |
| 4QSamᵇ  | 4Q52   |
| 4QSamᶜ  | 4Q53   |
| 1QSam   | 1Q7    |

## Sources & credits

- **Masoretic Text:** the ETCBC [BHSA](https://github.com/ETCBC/bhsa) dataset (version 2021).
- **Dead Sea Scrolls:** the ETCBC [dss](https://github.com/ETCBC/dss) dataset, version 2.0 (Martin Abegg's transcription).
- Both are distributed in Text-Fabric (`.tf`) format and are read here with
  [Context-Fabric](https://context-fabric.ai), the successor to
  [Text-Fabric](https://github.com/annotation/text-fabric).

Please consult and respect the license and attribution terms of the BHSA and DSS
datasets before reusing this material.

## How it was made

The pages are produced by a single Python script, `src/mt_samuel_for_scroll_chapters.py`,
that loads both datasets through Context-Fabric and writes the HTML directly into
`docs/` — no build step, no server, no templates.

To reproduce them you need the two datasets on disk. Context-Fabric does not download
corpora, so clone them and point the script at the `.tf` directories:

```bash
pip install -r requirements.txt        # Context-Fabric; the rest is the stdlib

git clone --depth 1 https://github.com/ETCBC/dss.git
git clone --depth 1 https://github.com/ETCBC/bhsa.git

DSS_TF=dss/tf/2.0 BHSA_TF=bhsa/tf/2021 python src/mt_samuel_for_scroll_chapters.py
```

Both variables default to the usual `~/text-fabric-data` cache, so if the datasets are
already there the script can be run with no arguments at all. The first run compiles
each corpus to Context-Fabric's memory-mapped format — a few minutes for the DSS —
and every run after that loads in about a second.

Alongside the HTML the script writes `mt_samuel_for_scroll_chapters.csv`: one row per
MT verse of the chapters with scroll evidence (1,483 verses, of which 733 are
preserved in at least one scroll), with the consonantal and pointed text and the
sigla attesting it.

## License

This work is licensed under a Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).

