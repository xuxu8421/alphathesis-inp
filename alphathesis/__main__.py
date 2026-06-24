"""CLI: python -m alphathesis --data data/inp_knowledge.json --out reports"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agents import run_pipeline
from .report import render_html, render_markdown


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="alphathesis",
        description="Thematic supply-chain research agent (an AlphaAnalyst extension).",
    )
    ap.add_argument("--data", default="data/inp_knowledge.json",
                    help="Path to the theme knowledge base JSON.")
    ap.add_argument("--out", default="reports",
                    help="Output directory for the generated memo.")
    ap.add_argument("--name", default=None,
                    help="Output file stem (default: <theme_id>_research_memo).")
    ap.add_argument("--strict", action="store_true",
                    help="Exit non-zero if the citation validator fails (CI gate).")
    args = ap.parse_args(argv)

    if not Path(args.data).exists():
        print(f"error: data file not found: {args.data}", file=sys.stderr)
        return 2

    memo = run_pipeline(args.data)
    stem = args.name or f"{memo.kb.theme_id}_research_memo"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    md_path = out / f"{stem}.md"
    html_path = out / f"{stem}.html"
    md_path.write_text(render_markdown(memo), encoding="utf-8")
    html_path.write_text(render_html(memo), encoding="utf-8")

    v = memo.validation
    print("AlphaThesis pipeline complete.")
    print(f"  theme           : {memo.kb.title}")
    print(f"  bull pillars    : {len(memo.bull)}  ({sum(len(p.claims) for p in memo.bull)} claims)")
    print(f"  bear rebuttals  : {len(memo.rebuttals)} ({sum(len(r.claims) for r in memo.rebuttals)} claims)")
    print(f"  blind spots     : {', '.join(memo.blind_spots) or 'none'}")
    print(f"  citation coverage: {v.coverage*100:.0f}%  ({v.cited_facts}/{v.fact_claims})  "
          f"validator={'PASS' if v.passed else 'FAIL'}")
    if v.failures:
        for cid, reason in v.failures:
            print(f"    - FAIL {cid}: {reason}")
    print(f"  wrote           : {md_path}")
    print(f"  wrote           : {html_path}")

    if args.strict and not v.passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
