# AlphaThesis

**A thematic / supply-chain research agent — an extension of [AlphaAnalyst](https://github.com/kbhujbal/AlphaAnalyst-open-source-autonomous-equity-research-agent).**

AlphaAnalyst turns a single stock ticker into an analyst-grade memo using a
multi-agent pipeline, a **Devil's Advocate** model forced to disagree, and a
**citation validator** that refuses to print hallucinated numbers.

AlphaThesis keeps that philosophy but **lifts the unit of analysis from one ticker
to a supply-chain *theme*** — the questions a top-down tech investor actually
asks: *where is the bottleneck, who controls it, what breaks the thesis, and what
do I monitor?* The shipped example is **indium phosphide (InP)** — the optical /
laser-substrate chokepoint behind AI optical interconnects.

> Built as a work sample: it demonstrates an auditable, no-hallucinated-numbers
> research pipeline rather than another chat wrapper.

---

## What it does

```
Sourcer ─▶ ClaimExtractor ─▶ BullAnalyst ─┐
                                          ├▶ CitationValidator ─▶ Synthesizer ─▶ memo (.md + .html)
                          DevilsAdvocate ─┘
```

- **Sourcer** loads a structured, cited knowledge base. (In a live build this is
  where AlphaAnalyst's SEC EDGAR / FMP-transcript / news fetchers feed in.)
- **BullAnalyst** assembles the constructive thesis into pillars.
- **DevilsAdvocate** is *forced to disagree*: it supplies the bear case and, using
  an explicit `counters` mapping, flags any bull pillar with **no** opposing
  evidence as a **blind spot** (so the analyst goes and finds the missing bear
  case instead of trusting the narrative).
- **CitationValidator** is the headline gate: every numeric *fact* claim must
  resolve to a real source id, or it fails. Opinions are allowed but must be
  labelled `inference` — an inference that smuggles in a hard number also fails.
- **Synthesizer** produces a deterministic, auditable verdict (a function of cited
  bull pillars vs. live risks), then renders Markdown + a standalone styled HTML memo.

Deterministic by default → **reproducible and zero hallucinated numbers**. An LLM
composer can be dropped in behind the same interface for narrative polish without
touching the validation gate.

## Quickstart

No dependencies — standard library only:

```bash
python3 -m alphathesis --data data/inp_knowledge.json --out reports --strict
```

`--strict` makes the citation validator a CI gate (non-zero exit on failure).

Outputs:

- `reports/inp_research_memo.md`
- `reports/inp_research_memo.html`  (open in a browser — has an **EN / 中文** toggle in the top-right)

Run the tests:

```bash
python3 tests/test_pipeline.py      # or: python3 -m pytest -q
```

## Example output (InP)

- 5 bull pillars / 14 cited claims, 5 bear rebuttals, **100% citation coverage (18/18)**.
- One honest blind spot surfaced: **Physics moat** — the irreplaceability claim has
  no near-term counter in the current sources (the long-dated risk, lasers-on-silicon,
  isn't yet in the KB — exactly the gap the tool is meant to flag).

## Add another theme

Drop a new `data/<theme>.json` with the same shape (`sources`, `entities`,
`claims` with `stance`/`pillar`/`kind`/`source`, bear claims carrying `counters`),
then:

```bash
python3 -m alphathesis --data data/<theme>.json
```

## Relationship to AlphaAnalyst

This is a **companion/extension**, not a fork of the UI. It reuses AlphaAnalyst's
core ideas — multi-agent structure, a different-model-family Devil's Advocate, and
strict citation validation — and generalises them from single-equity memos to
supply-chain theses. Credit to the original project:
`kbhujbal/AlphaAnalyst-open-source-autonomous-equity-research-agent`.

## Layout

```
alphathesis/   models.py · agents.py · report.py · __main__.py
data/          inp_knowledge.json   (cited knowledge base)
reports/       generated memos (.md / .html)
tests/         pipeline invariants (citation coverage, devil's advocate, blind spots)
PITCH.md       how to talk about this in an interview
```
