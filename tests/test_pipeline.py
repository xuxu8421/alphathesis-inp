"""Smoke + invariant tests for the AlphaThesis pipeline.

Run: python3 -m pytest -q   (or)   python3 tests/test_pipeline.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from alphathesis.agents import run_pipeline  # noqa: E402

DATA = ROOT / "data" / "inp_knowledge.json"


def test_validator_passes_and_full_coverage():
    memo = run_pipeline(str(DATA))
    assert memo.validation.passed, memo.validation.failures
    assert memo.validation.coverage == 1.0


def test_every_numeric_fact_is_cited():
    memo = run_pipeline(str(DATA))
    for c in memo.kb.claims:
        if c.is_fact and c.value:
            assert c.source in memo.kb.sources, f"{c.id} numeric fact without valid source"


def test_devils_advocate_present():
    memo = run_pipeline(str(DATA))
    assert sum(len(r.claims) for r in memo.rebuttals) >= 3, "Devil's Advocate must supply a real bear case"


def test_blind_spots_are_explicit():
    # only pillars with no declared counter should surface; here: exactly 'Physics moat'
    memo = run_pipeline(str(DATA))
    assert memo.blind_spots == ["Physics moat"], memo.blind_spots


if __name__ == "__main__":
    test_validator_passes_and_full_coverage()
    test_every_numeric_fact_is_cited()
    test_devils_advocate_present()
    test_blind_spots_are_explicit()
    print("all tests passed")
