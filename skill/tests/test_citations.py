#!/usr/bin/env python3
"""Tests for citations.py — citation/reference tracker."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from citations import extract_citations, load_references, build_report, render_bibliography

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def test_extract_simple_key():
    keys = extract_citations("Body [@Rowland2011].")
    assert keys == ["Rowland2011"], keys


def test_extract_with_locator():
    keys = extract_citations("See [@Rowland2011, p. 12] for detail.")
    assert keys == ["Rowland2011"], keys


def test_extract_multiple_grouped():
    keys = extract_citations("Linked [@Rowland2011; @Wilkinson1975] here.")
    assert sorted(keys) == ["Rowland2011", "Wilkinson1975"], keys


def test_extract_across_files():
    keys = extract_citations([
        "x [@Rowland2011]",
        "y [@Goodman2020, p. 1] and [@Wilkinson1975]",
    ])
    assert sorted(keys) == ["Goodman2020", "Rowland2011", "Wilkinson1975"], keys


def test_no_false_positive_on_email():
    keys = extract_citations("Contact me at user [@host] no wait that's not a cite.")
    # [@host] with bare word — should be captured as a key (lenient). Email uses @ not [@]
    # Ensure mail@host.com is NOT captured
    keys2 = extract_citations("Email mail@host.com here.")
    assert keys2 == [], keys2


def test_load_references():
    refs = load_references(os.path.join(FIX, "references.md"))
    assert "Rowland2011" in refs
    assert "Wilkinson1975" in refs
    assert "Goodman2020" in refs
    assert "UnusedRef1999" in refs
    assert "Rowland2011" in refs and "Lippincott" in refs["Rowland2011"]


def test_report_cited_but_undefined():
    cited = ["Rowland2011", "GhostMissing"]
    defined = {"Rowland2011": "...", "UnusedRef1999": "..."}
    rep = build_report(cited, defined)
    assert "GhostMissing" in rep["undefined"]
    assert rep["undefined"] == ["GhostMissing"]


def test_report_defined_but_uncited():
    cited = ["Rowland2011"]
    defined = {"Rowland2011": "...", "UnusedRef1999": "..."}
    rep = build_report(cited, defined)
    assert "UnusedRef1999" in rep["uncited"]


def test_render_bibliography_only_cited():
    cited = ["Goodman2020", "Rowland2011"]
    defined = {
        "Rowland2011": "Rowland entry",
        "Goodman2020": "Goodman entry",
        "UnusedRef1999": "ghost",
    }
    bib = render_bibliography(cited, defined)
    assert "Rowland entry" in bib
    assert "Goodman entry" in bib
    assert "ghost" not in bib  # uncited excluded


def test_render_bibliography_sorted():
    cited = ["Goodman2020", "Rowland2011"]
    defined = {"Rowland2011": "Rowland", "Goodman2020": "Goodman"}
    bib = render_bibliography(cited, defined)
    # sorted by key
    assert bib.index("Goodman") < bib.index("Rowland")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
