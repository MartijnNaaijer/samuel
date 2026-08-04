# Samuel — Masoretic Text ∥ Dead Sea Scrolls

A verse-by-verse parallel edition of the book of Samuel: the **Masoretic Text**
(from the ETCBC BHSA database) shown together with the four main **Qumran
manuscripts** of Samuel, for close reading by Hebraists.

## View it online

The pages are plain static HTML — open **`index.html`**, or visit the published site:

https://martijnnaaijer.github.io/samuel

## What's inside

One page per chapter (1 Samuel 1–31, 2 Samuel 1–24) plus an index. For each verse
the pointed **Masoretic Text** is shown on top and the **Dead Sea Scroll**
reading(s) directly beneath it.

- **Reconstruction is marked** in the scroll text, following the critical editions:
  - `[ … ]` (grey) — editorially reconstructed letters
  - a dot above a letter — an uncertain reading
  - `°` — a letter preserved only as illegible traces
  - `.` — a lost letter inside a lacuna
- **Hover over any word** to see its morphology: part of speech, verbal stem and
  tense (for verbs), person, gender, and number.
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

- **Masoretic Text:** the ETCBC [BHSA](https://github.com/ETCBC/bhsa) Text-Fabric dataset (version 2021).
- **Dead Sea Scrolls:** the ETCBC [dss](https://github.com/ETCBC/dss) Text-Fabric dataset (Martin Abegg's transcription).
- Generated with [Text-Fabric](https://github.com/annotation/text-fabric).

Please consult and respect the license and attribution terms of the BHSA and DSS
datasets before reusing this material.

## How it was made

The pages are produced by a single Python script that loads both datasets through
Text-Fabric and writes the HTML — no build step or server required.

## Lisence

This work is licensed under a Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).

