"""AlphaThesis — a thematic / supply-chain research agent.

An extension of AlphaAnalyst (kbhujbal/AlphaAnalyst), which produces analyst-grade
equity memos for a single ticker with a multi-agent pipeline, a Devil's Advocate
model and strict citation validation ("no hallucinated numbers").

AlphaThesis keeps that philosophy but lifts the unit of analysis from a single
stock to a *supply-chain theme* (e.g. indium phosphide / AI optical interconnect):

    Sourcer -> ClaimExtractor -> BullAnalyst -> DevilsAdvocate
            -> CitationValidator -> Synthesizer -> (Markdown / HTML memo)

Every numeric ("fact") claim must resolve to a real source id or it is flagged by
the CitationValidator; opinion ("inference") claims are allowed but labelled.
"""

__version__ = "0.1.0"
