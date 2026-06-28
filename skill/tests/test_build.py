#!/usr/bin/env python3
"""Tests for build.py — md chapters -> single inlined HTML."""
import sys
import os
import re
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

SKILL_DIR = os.path.join(os.path.dirname(__file__), "..")
FIX = os.path.join(os.path.dirname(__file__), "fixtures")
TPL = os.path.join(SKILL_DIR, "templates")


def test_build_produces_single_html(tmp_path=None):
    import build
    out = build.build_module(
        src_dir=FIX,
        templates_dir=TPL,
        out_path=os.path.join(tempfile.mkdtemp(), "module.html"),
    )
    assert os.path.exists(out)
    with open(out) as f:
        html = f.read()
    assert "<html" in html.lower()
    assert "</html>" in html.lower()


def test_css_inlined_no_external_link():
    import build
    out = build.build_module(
        src_dir=FIX, templates_dir=TPL,
        out_path=os.path.join(tempfile.mkdtemp(), "module.html"),
    )
    with open(out) as f:
        html = f.read()
    # no external stylesheet link (relative)
    assert not re.search(r'<link[^>]+href=["\'][^"\']+\.css', html), "external CSS link found"
    assert "<style" in html, "no <style> block inlined"


def test_js_inlined_no_external_src():
    import build
    out = build.build_module(
        src_dir=FIX, templates_dir=TPL,
        out_path=os.path.join(tempfile.mkdtemp(), "module.html"),
    )
    with open(out) as f:
        html = f.read()
    assert not re.search(r'<script[^>]+src=["\'][^"\']+\.js', html), "external JS src found"
    assert "<script" in html, "no <script> block inlined"


def test_toc_has_headings():
    import build
    out = build.build_module(
        src_dir=FIX, templates_dir=TPL,
        out_path=os.path.join(tempfile.mkdtemp(), "module.html"),
    )
    with open(out) as f:
        html = f.read()
    # headings from fixtures: Introduction, Absorption, Distribution, Elimination, Half-life, Renal clearance
    for needle in ["Introduction", "Absorption", "Elimination", "Half-life"]:
        assert needle in html, f"missing heading in TOC/content: {needle}"


def test_bibliography_section_present():
    import build
    out = build.build_module(
        src_dir=FIX, templates_dir=TPL,
        out_path=os.path.join(tempfile.mkdtemp(), "module.html"),
    )
    with open(out) as f:
        html = f.read()
    assert "references" in html.lower() or "bibliography" in html.lower(), "no references section"
    # cited entry present
    assert "Rowland" in html
    # uncited entry absent
    assert "Never cited" not in html and "Phantom Journal" not in html


def test_images_inlined_as_data_uri():
    import build
    out = build.build_module(
        src_dir=FIX, templates_dir=TPL,
        out_path=os.path.join(tempfile.mkdtemp(), "module.html"),
    )
    with open(out) as f:
        html = f.read()
    # the sample.png reference should be a data: URI
    assert re.search(r'src=["\']data:image', html), "no inlined data URI image found"
    # original relative path should be gone
    assert 'src="sample.png"' not in html


def test_output_passes_validation():
    import build
    import validate
    out = build.build_module(
        src_dir=FIX, templates_dir=TPL,
        out_path=os.path.join(tempfile.mkdtemp(), "module.html"),
    )
    with open(out) as f:
        html = f.read()
    errors = validate.validate_html(html)
    assert errors == [], f"built HTML has structural errors: {errors}"


def test_meta_title_appears():
    import build
    out = build.build_module(
        src_dir=FIX, templates_dir=TPL,
        out_path=os.path.join(tempfile.mkdtemp(), "module.html"),
    )
    with open(out) as f:
        html = f.read()
    assert "Clinical Pharmacokinetics" in html


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
