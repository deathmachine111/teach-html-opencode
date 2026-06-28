#!/usr/bin/env python3
"""Tests for validate.py — structural HTML validation."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from validate import validate_html

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name):
    with open(os.path.join(FIX, name)) as f:
        return f.read()


def test_valid_html_no_errors():
    errors = validate_html(_read("valid.html"))
    assert errors == [], errors


def test_unclosed_div_caught():
    errors = validate_html(_read("broken_div.html"))
    assert len(errors) >= 1, "expected at least one error for unclosed div"
    # should mention the leaking tag
    assert any("div" in e.lower() or "leak" in e.lower() or "unclosed" in e.lower() or "mismatch" in e.lower() for e in errors), errors


def test_mismatched_nesting_caught():
    errors = validate_html(_read("broken_mismatch.html"))
    assert len(errors) >= 1, errors


def test_self_closing_ok():
    html = "<!DOCTYPE html><html><body><img src='x'/><br/><hr/><p>ok</p></body></html>"
    errors = validate_html(html)
    assert errors == [], errors


def test_void_elements_not_flagged():
    # void elements (area, base, br, col, embed, hr, img, input, link, meta, source, track, wbr)
    html = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body><p>line<br>break</p></body></html>"
    errors = validate_html(html)
    assert errors == [], errors


def test_stray_close_caught():
    html = "<!DOCTYPE html><html><body><p>ok</p></span></body></html>"
    errors = validate_html(html)
    assert len(errors) >= 1, errors


def test_returns_list_of_strings():
    errors = validate_html(_read("valid.html"))
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)


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
