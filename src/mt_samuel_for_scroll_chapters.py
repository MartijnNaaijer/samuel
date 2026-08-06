#!/usr/bin/env python3
"""
Samuel: Masoretic Text (BHSA) parallel with the Dead Sea Scrolls (ETCBC/dss).

Produces, for EVERY chapter of Samuel, an HTML page that sets the BHSA verse
(pointed Masoretic Text) beside the text of the four main Qumran Samuel scrolls
(4Q51, 4Q52, 4Q53, 1Q7) wherever they preserve that verse.  Reconstructed and
uncertain material in the scrolls is clearly marked, for close reading by
Hebraists.  Also (re)produces the verse-level MT CSV from the earlier step.

Marking in the scroll column (as in the critical editions):
    [ ... ]  reconstructed letters (grey)          - sign feature rec == 1
    .        a lost letter inside a lacuna
    °        a letter present only as traces (illegible)
    ẋ        an identified but uncertain reading (dot above)

The scrolls attest 54 of Samuel's 55 chapters (only 1 Samuel 13 is absent);
its page is generated too, noting the absence of scroll evidence.

Output goes straight into ../docs/, which is what GitHub Pages publishes.
Running this script therefore updates the site; nothing has to be copied by hand.

Data access uses Context-Fabric (https://context-fabric.ai), the successor to
Text-Fabric.  Its core API (F, L, T) is the same, but it memory-maps the corpus
instead of unpickling it, so both datasets fit comfortably in one process and
this script no longer needs the subprocess split it used under Text-Fabric.

Context-Fabric has no app layer and does NOT download corpora, so both datasets
must already be present locally as .tf directories.  The defaults below point at
the usual text-fabric-data cache; override with $DSS_TF and $BHSA_TF.  The first
run on a given corpus compiles .tf to memory-mapped .cfm (slow, a few minutes for
the DSS); every run after that loads in about a second.

    git clone --depth 1 https://github.com/ETCBC/dss.git
    git clone --depth 1 https://github.com/ETCBC/bhsa.git

Requires:  pip install context-fabric
"""

from __future__ import annotations

import csv
import html as H
import os
import sys
from pathlib import Path

from cfabric import Fabric

# ---------------------------------------------------------------------------
# Paths.  Everything is anchored to this file, not to the current working
# directory, so the script can be run from anywhere.
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUTDIR = REPO / "docs"                                   # published by GitHub Pages
CSV_OUT = REPO / "mt_samuel_for_scroll_chapters.csv"

DSS_TF = os.environ.get("DSS_TF", "~/text-fabric-data/github/ETCBC/dss/tf/2.0")
BHSA_TF = os.environ.get("BHSA_TF", "~/text-fabric-data/github/ETCBC/bhsa/tf/2021")

DSS_VERSION = Path(DSS_TF).name
BHSA_VERSION = Path(BHSA_TF).name

DSS_FEATURES = (
    "otype oslots scroll book chapter verse glyph type rec unc after "
    "lex_etcbc sp_etcbc nu_etcbc gn_etcbc ps_etcbc vs_etcbc vt_etcbc"
)
BHSA_FEATURES = (
    "otype oslots book chapter verse g_word_utf8 g_cons_utf8 trailer_utf8 "
    "lex sp vs vt ps gn nu"
)

SCROLLS = ["4Q51", "4Q52", "4Q53", "1Q7"]
SCROLL_NAME = {"4Q51": "4QSamᵃ", "4Q52": "4QSamᵇ", "4Q53": "4QSamᶜ", "1Q7": "1QSam"}
SCROLL_ORDER = ["4QSamᵃ", "4QSamᵇ", "4QSamᶜ", "1QSam"]
DSS2MT_BOOK = {"1Sam": "1 Samuel", "2Sam": "2 Samuel"}
BHSA2OUT = {"1_Samuel": "1 Samuel", "2_Samuel": "2 Samuel"}
CHAPTERS = [("1 Samuel", n) for n in range(1, 32)] + [("2 Samuel", n) for n in range(1, 25)]

DOT_ABOVE = "̇"      # combining dot above (escaped: the literal is invisible)
GLYPH_TYPES = {"cons", "numr", "foreign", "punct", "add"}
SOF_PASUQ = "׃"      # ׃ verse divider; dropped at the end of a scroll verse


def load_corpus(location: str, features: str, what: str):
    """Load a local .tf corpus, failing with a usable message if it is not there."""
    path = Path(location).expanduser()
    if not path.is_dir():
        sys.exit(
            f"{what} not found at {path}\n"
            f"Context-Fabric does not download corpora. Clone the dataset and point\n"
            f"the matching environment variable at its .tf directory."
        )
    api = Fabric(locations=str(path), silent="deep").load(features, silent="deep")
    if api is False:
        sys.exit(f"could not load {what} from {path} (missing features?)")
    return api


# ===========================================================================
# PHASE 1: reconstruct each scroll's Samuel verses as marked-up HTML.
# ===========================================================================
def scan_dss():
    api = load_corpus(DSS_TF, DSS_FEATURES, f"DSS {DSS_VERSION}")
    F, L = api.F, api.L

    def tip_dss(w):
        def c(x):
            return x if x and x not in ("NA", "unknown") else None

        # the lexeme (ETCBC transliteration, as in BHSA: KL/, JD<[) comes first
        rows = [("lexeme", c(F.lex_etcbc.v(w)) or "–"),
                ("part of speech", c(F.sp_etcbc.v(w)) or "–")]
        for lbl, v in (("verbal stem", c(F.vs_etcbc.v(w))),
                       ("verbal tense", c(F.vt_etcbc.v(w))),
                       ("person", c(F.ps_etcbc.v(w))),
                       ("gender", c(F.gn_etcbc.v(w))),
                       ("number", c(F.nu_etcbc.v(w)))):
            if v:
                rows.append((lbl, v))
        inner = "".join('<span class="row"><span class="lbl">' + lbl +
                        '</span><span class="val">' + H.escape(val, quote=True) +
                        "</span></span>" for lbl, val in rows)
        return '<span class="tip">' + inner + "</span>"

    def sign_info(s):
        """Return (html_chunk, reconstructed?) or None for spacing signs."""
        t, g = F.type.v(s), (F.glyph.v(s) or "")
        rec = F.rec.v(s) == 1
        if t in ("empty", "sep", "term"):
            return None
        if t == "missing":
            return (".", True)                            # lost letter in a lacuna
        if t == "unc":
            return ('<span class="unid">°</span>', rec)   # illegible (traces only)
        if g and t in GLYPH_TYPES:
            ch = H.escape(g)
            if F.unc.v(s):                                # identified but uncertain
                ch = ch + DOT_ABOVE
            return (ch, rec)
        return None

    def trailing_sof_pasuq(vwords):
        """Sign nodes of the verse-final ׃ (or ׃׃), which we do not print."""
        drop = set()
        signs = [s for w in vwords for s in L.d(w, otype="sign")]
        for s in reversed(signs):
            t = F.type.v(s)
            if t in ("empty", "sep", "term"):
                continue                                  # never rendered anyway
            if t == "missing":
                continue                                  # a lost letter after the divider
            if t == "punct" and (F.glyph.v(s) or "").strip(SOF_PASUQ) == "":
                drop.add(s)
                continue                                  # keep going: ׃׃ is two signs
            break                                         # real text: stop here
        return drop

    def verse_html(vwords):
        # Two passes.  The first renders every sign to a (chunk, reconstructed) pair,
        # leaving out the verse-final sof pasuq.  The second works out the maximal
        # runs of reconstructed material so that, in a run covering three or more
        # words, the words in the middle can be hidden while still taking up their
        # space, leaving only the first and last word of the lacuna legible.
        drop = trailing_sof_pasuq(vwords)

        wchunks = []                          # per word: [[chunk, rec, hidden], ...]
        for w in vwords:
            row = []
            for s in L.d(w, otype="sign"):
                if s in drop:
                    continue
                info = sign_info(s)
                if info is None:
                    continue
                chunk, rec = info
                row.append([chunk, rec, False])
            wchunks.append(row)

        runs, run = [], []                    # maximal reconstructed runs, across words
        for wi, row in enumerate(wchunks):
            for ci, (_, rec, _) in enumerate(row):
                if rec:
                    run.append((wi, ci))
                elif run:
                    runs.append(run)
                    run = []
        if run:
            runs.append(run)

        for run in runs:
            touched = sorted({wi for wi, _ in run})
            if len(touched) >= 3:             # hide everything but first and last word
                middle = set(touched[1:-1])
                for wi, ci in run:
                    if wi in middle:
                        wchunks[wi][ci][2] = True

        # Reconstruction brackets [ ] are emitted as plain TEXT at the boundaries of a
        # run (so a lacuna spanning several words is bracketed once), while the grey
        # colouring is applied per word: a <span class="rec"> never crosses a word
        # boundary, so nesting with the per-word hover span is always valid.
        parts, inrec, open_span = [], False, None

        def close():
            nonlocal open_span
            if open_span:
                parts.append("</span>")
                open_span = None

        for wi, w in enumerate(vwords):
            row = wchunks[wi]
            blank = bool(row) and all(c[2] for c in row)   # nothing of it is legible
            parts.append('<span class="w blank">' if blank else '<span class="w">')
            for chunk, rec, hidden in row:
                if rec and not inrec:
                    close(); parts.append("["); inrec = True           # open lacuna
                elif (not rec) and inrec:
                    close(); parts.append("]"); inrec = False          # close lacuna
                want = ("rec mid" if hidden else "rec") if rec else None
                if want != open_span:
                    close()
                    if want:
                        parts.append(f'<span class="{want}">')
                        open_span = want
                parts.append(chunk)
            close()                                        # word boundary
            parts.append(tip_dss(w))
            parts.append("</span>")
            aft = F.after.v(w)                             # ' ' divider or None
            if aft:
                parts.append(aft)
        if inrec:
            parts.append("]")
        return "".join(parts).strip()

    # A handful of sigla in the DSS occur on more than one scroll node (4Q88,
    # 4Q483, 11Q5, 11Q6), so collect nodes per siglum rather than keeping only
    # the last one.  None of the four Samuel scrolls is affected, but a dict
    # comprehension keyed on the siglum would silently drop text if that changed.
    scroll_nodes: dict[str, list[int]] = {}
    for s in api.F.otype.s("scroll"):
        scroll_nodes.setdefault(F.scroll.v(s), []).append(s)

    chapters: dict[str, set[str]] = {}
    verses: dict[str, set[str]] = {}
    dss_html: dict[str, dict[str, str]] = {}

    for sig in SCROLLS:
        nodes = scroll_nodes.get(sig)
        if not nodes:
            sys.exit(f"scroll {sig} not found in the DSS dataset at {DSS_TF}")
        # group this scroll's words by verse
        vwords: dict[str, list[int]] = {}
        for node in nodes:
            for w in L.d(node, otype="word"):
                b, c, v = F.book.v(w), F.chapter.v(w), F.verse.v(w)
                if b in DSS2MT_BOOK and c and v:
                    key = f"{DSS2MT_BOOK[b]}|{int(c)}|{int(v)}"
                    vwords.setdefault(key, []).append(w)
        for key, ws in vwords.items():
            ob, c, v = key.split("|")
            chapters.setdefault(f"{ob}|{c}", set()).add(SCROLL_NAME[sig])
            verses.setdefault(key, set()).add(SCROLL_NAME[sig])
            dss_html.setdefault(key, {})[SCROLL_NAME[sig]] = verse_html(ws)

    return ({k: sorted(v) for k, v in chapters.items()}, verses, dss_html)


# ===========================================================================
# PHASE 2: BHSA MT text + build the parallel HTML pages.
# ===========================================================================
CSS = r"""
:root { --rec:#9aa0a6; --illeg:#c3c7cc; }
* { box-sizing:border-box; }
body { margin:0; font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
       color:#1f2328; background:#fafafa; }
.hebrew { font-family:"Frank Ruhl Libre","SBL Hebrew","Ezra SIL","Taamey Frank CLM",
          "David","Times New Roman",serif; }
header { position:sticky; top:0; background:#fff; border-bottom:1px solid #e3e3e3;
         padding:14px 22px; z-index:5; }
header h1 { margin:0 0 4px; font-size:1.5rem; }
header .att { color:#556; font-size:.9rem; }
nav { margin-top:8px; font-size:.9rem; }
nav a { text-decoration:none; color:#2563eb; margin-right:14px; }
nav a.disabled { color:#bbb; pointer-events:none; }
.legend { margin:16px auto; padding:12px 16px; background:#fff; border:1px solid #e3e3e3;
          border-radius:8px; font-size:.9rem; line-height:1.7; max-width:1000px; }
.legend b { font-weight:600; }
.legend .hd { font-weight:600; }
.legend ul { list-style:none; margin:6px 0 0; padding:0; }
.legend li { padding:2px 0 2px 14px; text-indent:-14px; }
.legend .key { font-weight:600; }
.sample { font-size:1.15rem; }
.chapter { max-width:1000px; margin:0 auto 40px; background:#fff; border:1px solid #ececec;
           border-radius:8px; }
.verse { padding:12px 20px 14px; border-bottom:1px solid #eee; }
.verse:last-child { border-bottom:none; }
.verse:target { background:#fff7e6; }
.vhead { font-size:1rem; font-weight:600; color:#6b7280; text-align:right; margin-bottom:7px;
         font-variant-numeric:tabular-nums; }
.line { display:flex; gap:14px; align-items:baseline; padding:2px 0; }
.badge { flex:0 0 auto; min-width:84px; text-align:center; direction:ltr; unicode-bidi:isolate;
         font-family:-apple-system,Segoe UI,sans-serif; font-size:.98rem; font-weight:600;
         letter-spacing:.02em; padding:6px 14px; border-radius:13px; color:#fff;
         align-self:flex-start; margin-top:.3em; }
.badge.mt  { background:#111827; }
.badge.sig { background:#4b5563; }
.txt { flex:1 1 auto; direction:rtl; text-align:right; }
.w { position:relative; cursor:help; }
.w:hover { background:#eaf1ff; border-radius:3px; }
.tip { display:none; position:fixed; z-index:30; direction:ltr; text-align:left;
       background:#1f2937; color:#f9fafb; border-radius:10px; padding:9px 13px;
       box-shadow:0 10px 28px rgba(0,0,0,.24); pointer-events:none; white-space:nowrap;
       font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
       font-size:1rem; line-height:1.5; }
.tip .row { display:flex; gap:12px; }
.tip .lbl { color:#9ca3af; min-width:112px; }
.tip .val { color:#f9fafb; font-weight:500; }
/* MT vocalization / cantillation slider */
.voc-cb { position:absolute; opacity:0; width:0; height:0; pointer-events:none; }
.mtline .cons { display:none; }
#voc:checked ~ .chapter .mtline .voc { display:none; }
#voc:checked ~ .chapter .mtline .cons { display:inline; }
.switch { display:inline-flex; align-items:center; gap:10px; cursor:pointer; margin-top:10px;
          font-size:.88rem; color:#374151; user-select:none; }
.switch .track { width:42px; height:24px; background:#cbd5e1; border-radius:999px;
                 position:relative; transition:background .15s; flex:0 0 auto; }
.switch .thumb { position:absolute; top:3px; left:3px; width:18px; height:18px; background:#fff;
                 border-radius:50%; box-shadow:0 1px 3px rgba(0,0,0,.3); transition:transform .15s; }
#voc:checked ~ header .switch .track { background:#2563eb; }
#voc:checked ~ header .switch .thumb { transform:translateX(18px); }
.mtline  .txt { font-size:1.55rem; line-height:1.9; }
.dssline .txt { font-size:1.5rem;  line-height:1.9; }
.none { color:#b8bcc2; font-size:.95rem; font-style:italic; padding-inline-start:76px; }
.rec  { color:var(--rec); }                    /* reconstructed letters */
.rec.mid { visibility:hidden; }                /* inside a long lacuna: keeps its width */
.blank:hover { background:none; cursor:default; }
.unid { color:var(--illeg); }                  /* illegible letter (traces) */
footer { color:#8a8f98; font-size:.82rem; padding:0 22px 40px; max-width:1000px; margin:0 auto; }
"""

LEGEND = (
    '<div class="legend">'
    '<div class="hd">Reading the scroll lines</div>'
    '<ul>'
    '<li>ETCBC/DSS transcription, consonantal.</li>'
    '<li><span class="key">Black</span> &ndash; letters preserved on the manuscript.</li>'
    '<li><span class="hebrew sample rec">[&#8202;grey / in brackets&#8202;]</span> &ndash; '
    'editorially <b>reconstructed</b>. In a lacuna running over three or more words only the '
    'first and the last word are shown; the words between them are left blank but keep their '
    'width, so the size of the gap stays visible.</li>'
    '<li><span class="hebrew sample">א' + DOT_ABOVE + '</span> (dot above the letter) &ndash; an '
    'identified but <b>uncertain</b> reading.</li>'
    '<li><span class="hebrew sample unid">°</span> &ndash; a letter present only as illegible '
    'traces.</li>'
    '<li><span class="hebrew sample">.</span> &ndash; a lost letter inside a lacuna.</li>'
    '<li>The verse-final <span class="hebrew sample">׃</span> is not printed in the scroll '
    'lines.</li>'
    '<li>Each verse shows the <span class="badge mt" style="margin:0">MT</span> (pointed BHSA '
    'text) on top and the scroll line(s) beneath it, keyed by siglum, for direct comparison.</li>'
    '<li><b>Hover over any word</b> to see its lexeme (in ETCBC transliteration), part of '
    'speech, verbal stem &amp; tense (for verbs), person, gender and number.</li>'
    '<li>The slider above switches the MT between full pointing and consonants only.</li>'
    '</ul></div>'
)


def fname(book, ch):
    return f'{book.replace(" ", "")}_{ch:02d}.html'


def page(book, ch, verses, chap_scrolls, prev_ch, next_ch):
    scrolls = chap_scrolls.get(f"{book}|{ch}", [])
    chapter_has_dss = bool(scrolls)
    att = ("Preserved in: " + ", ".join(scrolls)) if scrolls else \
          "No Dead Sea Scroll evidence for this chapter."
    prev_a = (f'<a href="{fname(*prev_ch)}">&#8592; {prev_ch[0]} {prev_ch[1]}</a>'
              if prev_ch else '<a class="disabled">&#8592;</a>')
    next_a = (f'<a href="{fname(*next_ch)}">{next_ch[0]} {next_ch[1]} &#8594;</a>'
              if next_ch else '<a class="disabled">&#8594;</a>')

    blocks = []
    for vs, mt_html_str, dss_by_scroll in verses:
        lines = [f'<div class="vhead">{book} {ch}:{vs}</div>',
                 '<div class="line mtline"><span class="badge mt">MT</span>'
                 f'<span class="txt hebrew">{mt_html_str}</span></div>']
        if dss_by_scroll:
            for sig in SCROLL_ORDER:
                if sig in dss_by_scroll:
                    lines.append('<div class="line dssline">'
                                 f'<span class="badge sig">{sig}</span>'
                                 f'<span class="txt hebrew">{dss_by_scroll[sig]}</span></div>')
        elif chapter_has_dss:
            lines.append('<div class="none">— not preserved in a scroll —</div>')
        blocks.append(f'<div class="verse" id="v{vs}">{"".join(lines)}</div>')

    return f"""<!doctype html>
<html lang="en" dir="ltr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{book} {ch} — MT ∥ DSS</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body>
<input type="checkbox" id="voc" class="voc-cb">
<header>
  <h1>{book} {ch}</h1>
  <div class="att">{att}</div>
  <nav>{prev_a}<a href="index.html">Index</a>{next_a}</nav>
  <label for="voc" class="switch"><span>consonants only (hide vowels &amp; cantillation)</span><span class="track"><span class="thumb"></span></span></label>
</header>
{LEGEND}
<div class="chapter">
  {''.join(blocks)}
</div>
<footer>Masoretic Text: ETCBC BHSA ({BHSA_VERSION}). Dead Sea Scrolls: ETCBC/DSS {DSS_VERSION}
(Martin Abegg&#8217;s transcription). Reconstruction/uncertainty as encoded in that dataset.
Built with Context-Fabric.</footer>
<script>
document.addEventListener('mouseover', function(e) {{
  var w = e.target.closest && e.target.closest('.w'); if (!w) return;
  var tip = w.querySelector('.tip'); if (!tip) return;
  tip.style.display = 'block';
  var wr = w.getBoundingClientRect(), tr = tip.getBoundingClientRect(),
      vw = document.documentElement.clientWidth, vh = window.innerHeight, pad = 10;
  var left = wr.left + wr.width / 2 - tr.width / 2;
  if (left + tr.width > vw - pad) left = vw - pad - tr.width;
  if (left < pad) left = pad;
  var top = wr.bottom + 8;
  if (top + tr.height > vh - pad) top = wr.top - tr.height - 8;
  tip.style.left = left + 'px';
  tip.style.top = top + 'px';
}});
document.addEventListener('mouseout', function(e) {{
  var w = e.target.closest && e.target.closest('.w'); if (!w) return;
  if (w.contains(e.relatedTarget)) return;
  var tip = w.querySelector('.tip'); if (tip) tip.style.display = 'none';
}});
</script>
</body></html>"""


def index_page(chap_scrolls):
    items = []
    for (book, ch) in CHAPTERS:
        scr = chap_scrolls.get(f"{book}|{ch}", [])
        tag = (" &middot; " + ", ".join(scr)) if scr else ' &middot; <span class="none">MT only</span>'
        items.append(f'<li><a href="{fname(book, ch)}">{book} {ch}</a>'
                     f'<span style="color:#8a8f98;font-size:.85rem">{tag}</span></li>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Samuel — MT ∥ DSS parallel</title><style>{CSS}
ul.idx {{ columns:2; max-width:900px; margin:20px 22px; padding-inline-start:20px; }}
ul.idx li {{ margin:4px 0; }} ul.idx a {{ text-decoration:none; color:#2563eb; }}
</style></head><body>
<header><h1>Samuel — Masoretic Text (BHSA) ∥ Dead Sea Scrolls</h1>
<div class="att">One parallel page per chapter. Scrolls: 4QSamᵃ (4Q51), 4QSamᵇ (4Q52),
4QSamᶜ (4Q53), 1QSam (1Q7). 54 of 55 chapters have scroll evidence (1 Samuel 13 does not).</div></header>
<ul class="idx">{''.join(items)}</ul></body></html>"""


def build(chap_scrolls, verse_scrolls, dss_html):
    api = load_corpus(BHSA_TF, BHSA_FEATURES, f"BHSA {BHSA_VERSION}")
    F, L, T = api.F, api.L, api.T

    def cons(vn):
        return " ".join(F.g_cons_utf8.v(w) for w in L.d(vn, otype="word") if F.g_cons_utf8.v(w))

    def tip_mt(w):
        def c(x):
            return x if x and x not in ("NA", "unknown") else None

        rows = [("lexeme", c(F.lex.v(w)) or "–"),
                ("part of speech", c(F.sp.v(w)) or "–")]
        for lbl, v in (("verbal stem", c(F.vs.v(w))),
                       ("verbal tense", c(F.vt.v(w))),
                       ("person", c(F.ps.v(w))),
                       ("gender", c(F.gn.v(w))),
                       ("number", c(F.nu.v(w)))):
            if v:
                rows.append((lbl, v))
        inner = "".join('<span class="row"><span class="lbl">' + lbl +
                        '</span><span class="val">' + H.escape(val, quote=True) +
                        "</span></span>" for lbl, val in rows)
        return '<span class="tip">' + inner + "</span>"

    def mt_word_html(vn):
        # each word carries BOTH the pointed (voc) and consonantal (cons) form — the
        # slider toggles which is shown — plus a hover card with its morphology. The
        # original trailer (space, maqqef, sof-pasuq) is kept between words.
        out = []
        for w in L.d(vn, otype="word"):
            voc = H.escape(F.g_word_utf8.v(w) or "")
            cns = H.escape(F.g_cons_utf8.v(w) or "")
            out.append('<span class="w"><span class="voc">' + voc + "</span>"
                       '<span class="cons">' + cns + "</span>" + tip_mt(w) + "</span>")
            out.append(H.escape(F.trailer_utf8.v(w) or ""))
        return "".join(out).strip()

    # collect MT verses per chapter
    mt: dict[tuple[str, int], list] = {}
    csv_rows = []
    for vn in F.otype.s("verse"):
        bk, ch, vs = T.sectionFromNode(vn)
        if bk not in BHSA2OUT:
            continue
        ob = BHSA2OUT[bk]
        pointed = T.text(vn).strip()
        key = f"{ob}|{ch}|{vs}"
        mt.setdefault((ob, ch), []).append((int(vs), mt_word_html(vn), dss_html.get(key, {})))
        scr = sorted(verse_scrolls.get(key, []))
        if f"{ob}|{ch}" in chap_scrolls:                    # keep CSV scope = attested chapters
            csv_rows.append({"book": ob, "chapter": ch, "verse": vs, "verse_node": vn,
                             "mt_consonantal": cons(vn), "mt_pointed": pointed,
                             "attested_in_scroll": "yes" if scr else "no",
                             "scrolls": ";".join(scr)})

    OUTDIR.mkdir(parents=True, exist_ok=True)
    for i, (book, ch) in enumerate(CHAPTERS):
        verses = sorted(mt.get((book, ch), []), key=lambda t: t[0])
        prev_ch = CHAPTERS[i - 1] if i > 0 else None
        next_ch = CHAPTERS[i + 1] if i < len(CHAPTERS) - 1 else None
        (OUTDIR / fname(book, ch)).write_text(
            page(book, ch, verses, chap_scrolls, prev_ch, next_ch), encoding="utf-8")
    (OUTDIR / "index.html").write_text(index_page(chap_scrolls), encoding="utf-8")

    # keep the MT csv as well
    csv_rows.sort(key=lambda r: (0 if r["book"] == "1 Samuel" else 1, int(r["chapter"]), int(r["verse"])))
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["book", "chapter", "verse", "verse_node",
              "mt_consonantal", "mt_pointed", "attested_in_scroll", "scrolls"])
        w.writeheader()
        w.writerows(csv_rows)

    n_att = sum(1 for r in csv_rows if r["attested_in_scroll"] == "yes")
    print(f"chapters written: {len(CHAPTERS)} HTML pages + index in {OUTDIR}")
    print(f"MT verses (attested chapters): {len(csv_rows)}  (preserved in a scroll: {n_att})")
    print(f"CSV: {CSV_OUT}")


def main():
    print(f"DSS  {DSS_VERSION}: {Path(DSS_TF).expanduser()}")
    print(f"BHSA {BHSA_VERSION}: {Path(BHSA_TF).expanduser()}")
    chap_scrolls, verse_scrolls, dss_html = scan_dss()
    print(f"scroll chapters with evidence: {len(chap_scrolls)} of {len(CHAPTERS)}")
    build(chap_scrolls, verse_scrolls, dss_html)


if __name__ == "__main__":
    main()
