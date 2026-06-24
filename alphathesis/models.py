"""Core data models for AlphaThesis.

Kept dependency-free (stdlib only) so the pipeline runs offline with no install.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    publisher: str
    url: str
    date: str

    def cite(self) -> str:
        return f"[{self.id}] {self.publisher}, \"{self.title}\" ({self.date}). {self.url}"


@dataclass(frozen=True)
class Claim:
    id: str
    text: str
    stance: str          # "bull" | "bear"
    pillar: str
    kind: str = "fact"   # "fact" (must be cited) | "inference" (opinion, may be uncited)
    value: str | None = None
    source: str | None = None
    counters: tuple[str, ...] = ()  # bull pillar names this bear claim rebuts
    text_zh: str = ""

    @property
    def is_fact(self) -> bool:
        return self.kind == "fact"


@dataclass(frozen=True)
class Entity:
    name: str
    role: str
    note: str
    sources: list[str] = field(default_factory=list)
    role_zh: str = ""
    note_zh: str = ""


@dataclass
class KnowledgeBase:
    theme_id: str
    title: str
    subtitle: str
    as_of: str
    one_liner: str
    sources: dict[str, Source]
    claims: list[Claim]
    entities: list[Entity]
    monitorables: list[str]
    title_zh: str = ""
    subtitle_zh: str = ""
    one_liner_zh: str = ""
    pillars_zh: dict[str, str] = field(default_factory=dict)
    monitorables_zh: list[str] = field(default_factory=list)

    def pillar_zh(self, name: str) -> str:
        return self.pillars_zh.get(name, name)

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeBase":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        sources = {s["id"]: Source(**s) for s in raw["sources"]}
        claims = [
            Claim(
                id=c["id"],
                text=c["text"],
                stance=c["stance"],
                pillar=c["pillar"],
                kind=c.get("kind", "fact"),
                value=c.get("value"),
                source=c.get("source"),
                counters=tuple(c.get("counters", ())),
                text_zh=c.get("text_zh", ""),
            )
            for c in raw["claims"]
        ]
        entities = [
            Entity(
                name=e["name"],
                role=e["role"],
                note=e["note"],
                sources=e.get("sources", []),
                role_zh=e.get("role_zh", ""),
                note_zh=e.get("note_zh", ""),
            )
            for e in raw["entities"]
        ]
        return cls(
            theme_id=raw["theme_id"],
            title=raw["title"],
            subtitle=raw["subtitle"],
            as_of=raw["as_of"],
            one_liner=raw["one_liner"],
            sources=sources,
            claims=claims,
            entities=entities,
            monitorables=raw.get("monitorables", []),
            title_zh=raw.get("title_zh", ""),
            subtitle_zh=raw.get("subtitle_zh", ""),
            one_liner_zh=raw.get("one_liner_zh", ""),
            pillars_zh=raw.get("pillars_zh", {}),
            monitorables_zh=raw.get("monitorables_zh", []),
        )
