"""The AlphaThesis multi-agent pipeline.

Design mirrors AlphaAnalyst's "constructive agents + a Devil's Advocate forced to
disagree + a citation validator" structure, adapted from single-ticker equity
research to a supply-chain *theme*.

The composer is deterministic by default (auditable, reproducible, zero
hallucinated numbers). An optional LLM composer can be dropped in behind the same
interface — see ``llm.py`` notes in the README — without changing the pipeline.
"""
from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field

from .models import Claim, KnowledgeBase

_NUMBER_RE = re.compile(r"(?<![A-Za-z])(\$|US\$)?\d[\d,\.]*\s*(%|x|×|bn|B|billion|million|M|k|GW|TWh|nm|inch)?")


# --------------------------------------------------------------------------- #
# Sourcer + ClaimExtractor
# --------------------------------------------------------------------------- #
class Sourcer:
    """Loads the knowledge base. In a live build this is where AlphaAnalyst's
    data fetchers (SEC EDGAR, FMP transcripts, news) would feed documents in."""

    @staticmethod
    def load(path: str) -> KnowledgeBase:
        return KnowledgeBase.load(path)


class ClaimExtractor:
    """Groups atomic claims by pillar, preserving order."""

    @staticmethod
    def by_pillar(claims: list[Claim]) -> "OrderedDict[str, list[Claim]]":
        out: "OrderedDict[str, list[Claim]]" = OrderedDict()
        for c in claims:
            out.setdefault(c.pillar, []).append(c)
        return out


# --------------------------------------------------------------------------- #
# Constructive analyst (bull)
# --------------------------------------------------------------------------- #
@dataclass
class Pillar:
    name: str
    claims: list[Claim] = field(default_factory=list)


class BullAnalyst:
    """Builds the constructive thesis: bull-stance claims grouped into pillars."""

    def build(self, kb: KnowledgeBase) -> list[Pillar]:
        grouped = ClaimExtractor.by_pillar([c for c in kb.claims if c.stance == "bull"])
        return [Pillar(name=name, claims=claims) for name, claims in grouped.items()]


# --------------------------------------------------------------------------- #
# Devil's Advocate
# --------------------------------------------------------------------------- #
@dataclass
class Rebuttal:
    pillar: str
    claims: list[Claim] = field(default_factory=list)


class DevilsAdvocate:
    """Forced to disagree. Collects bear claims and pairs them against the bull
    pillars; flags any bull pillar that has *no* counter-argument (a blind spot)."""

    def build(self, kb: KnowledgeBase, bull: list[Pillar]) -> tuple[list[Rebuttal], list[str]]:
        bear_claims = [c for c in kb.claims if c.stance == "bear"]
        grouped = ClaimExtractor.by_pillar(bear_claims)
        rebuttals = [Rebuttal(pillar=name, claims=claims) for name, claims in grouped.items()]

        # Blind-spot check: a bull pillar is "covered" only if some bear claim
        # explicitly declares it rebuts that pillar (via `counters`). Pillars with
        # no declared counter are surfaced as unchallenged — prompting the analyst
        # to go find the missing bear evidence rather than trusting a keyword match.
        bull_pillars = {p.name for p in bull}
        covered: set[str] = set()
        for c in bear_claims:
            covered.update(c.counters)
        blind_spots = sorted(bull_pillars - covered)
        return rebuttals, blind_spots


# --------------------------------------------------------------------------- #
# Citation validator  (the "no hallucinated numbers" gate)
# --------------------------------------------------------------------------- #
@dataclass
class ValidationReport:
    total_claims: int
    fact_claims: int
    cited_facts: int
    inference_claims: int
    failures: list[tuple[str, str]] = field(default_factory=list)  # (claim_id, reason)

    @property
    def coverage(self) -> float:
        return 0.0 if self.fact_claims == 0 else self.cited_facts / self.fact_claims

    @property
    def passed(self) -> bool:
        return not self.failures


class CitationValidator:
    """Every numeric *fact* claim must resolve to a real source id. Any claim that
    states a number but carries no valid citation is a failure (the exact failure
    mode AlphaAnalyst's citation validator is built to stop)."""

    def validate(self, kb: KnowledgeBase) -> ValidationReport:
        fact_claims = [c for c in kb.claims if c.is_fact]
        inference_claims = [c for c in kb.claims if not c.is_fact]
        failures: list[tuple[str, str]] = []
        cited = 0

        for c in fact_claims:
            has_source = bool(c.source) and c.source in kb.sources
            states_number = bool(c.value) or bool(_NUMBER_RE.search(c.text))
            if has_source:
                cited += 1
            if states_number and not has_source:
                failures.append((c.id, "numeric claim without a valid source id"))
            elif not has_source:
                failures.append((c.id, "fact claim without a valid source id"))

        # An inference claim that sneaks in a hard number is also a failure:
        for c in inference_claims:
            if (c.value or _NUMBER_RE.search(c.text)) and not c.source:
                # allowed only if it is clearly framed as opinion
                if "analyst view" not in c.text.lower() and "unsourced" not in c.text.lower():
                    failures.append((c.id, "inference states a number but is not labelled as opinion"))

        return ValidationReport(
            total_claims=len(kb.claims),
            fact_claims=len(fact_claims),
            cited_facts=cited,
            inference_claims=len(inference_claims),
            failures=failures,
        )


# --------------------------------------------------------------------------- #
# Synthesizer
# --------------------------------------------------------------------------- #
@dataclass
class Memo:
    kb: KnowledgeBase
    bull: list[Pillar]
    rebuttals: list[Rebuttal]
    blind_spots: list[str]
    validation: ValidationReport
    verdict: str
    conviction: str
    verdict_zh: str = ""
    conviction_zh: str = ""


class Synthesizer:
    """Produces the final structured verdict. Deterministic: the verdict is a
    function of cited bull pillars vs. live risks, so it is fully auditable."""

    def compose(
        self,
        kb: KnowledgeBase,
        bull: list[Pillar],
        rebuttals: list[Rebuttal],
        blind_spots: list[str],
        validation: ValidationReport,
    ) -> Memo:
        n_bull = sum(len(p.claims) for p in bull)
        n_bear = sum(len(r.claims) for r in rebuttals)

        if validation.coverage >= 0.9 and n_bull >= 2 * max(n_bear, 1):
            verdict = (
                "Structurally bullish on the InP substrate / optical-interconnect bottleneck. "
                "The shortage is supply-side, certification-gated and concentrated, and it is "
                "anchored by hard hyperscaler capex commitments — not a narrative."
            )
            verdict_zh = (
                "对 InP 衬底 / 光互连瓶颈结构性看多。短缺源于供给侧、受认证周期约束且高度集中,"
                "并由超大规模厂商的硬性资本开支承诺背书——不是讲故事。"
            )
            conviction = "High (supply-chain), with timing risk concentrated in CPO ramp and AI-capex durability."
            conviction_zh = "高(供应链层面),时间风险集中在 CPO 量产节奏与 AI 资本开支的持续性。"
        elif n_bull > n_bear:
            verdict = "Constructive but timing-sensitive — own the bottleneck, size for the cyclicality."
            verdict_zh = "建设性但对时点敏感——拿住瓶颈,按周期性控制仓位。"
            conviction = "Medium."
            conviction_zh = "中。"
        else:
            verdict = "Balanced — the bear case on capacity catch-up and capex cyclicality is live."
            verdict_zh = "中性——产能追赶与资本开支周期性的空头逻辑仍然成立。"
            conviction = "Low / watch."
            conviction_zh = "低 / 观察。"

        return Memo(
            kb=kb,
            bull=bull,
            rebuttals=rebuttals,
            blind_spots=blind_spots,
            validation=validation,
            verdict=verdict,
            conviction=conviction,
            verdict_zh=verdict_zh,
            conviction_zh=conviction_zh,
        )


# --------------------------------------------------------------------------- #
# Pipeline orchestrator
# --------------------------------------------------------------------------- #
def run_pipeline(data_path: str) -> Memo:
    kb = Sourcer.load(data_path)
    bull = BullAnalyst().build(kb)
    rebuttals, blind_spots = DevilsAdvocate().build(kb, bull)
    validation = CitationValidator().validate(kb)
    return Synthesizer().compose(kb, bull, rebuttals, blind_spots, validation)
