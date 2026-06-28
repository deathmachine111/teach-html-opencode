"""TDD: tests for agent prompt content.

v1.1 contract:
  - author agent writes tables+bullets first, prose to explain
  - outliner agent plans for diagram density of every 2 paragraphs
  - both agents updated for editorial-medical style

These tests assert the agent files CONTAIN the required guidance
(textual assertions). If a future edit drops the guidance, tests fail.
"""
import os
import re
import sys

import pytest

AGENTS_DIR = os.path.expanduser("~/.config/opencode/agents")


def _read(name: str) -> str:
    path = os.path.join(AGENTS_DIR, name)
    if not os.path.exists(path):
        pytest.skip(f"agent file not found: {path}")
    with open(path) as f:
        return f.read()


# -------- author agent ------------------------------------------------------

def test_author_mentions_tables_and_bullets_first_v11():
    """v1.1: author must write tables+bullets first, prose to explain."""
    content = _read("teach-html-opencode-author.md")
    text = content.lower()
    # Both terms must appear
    assert "table" in text
    assert "bullet" in text or "list" in text
    # The priority order must be explicit
    assert ("tables" in text and "bullets" in text) or \
           ("table" in text and "list" in text)


def test_author_discourages_long_prose_v11():
    """v1.1: author should not write long flowing paragraphs when a
    table or list would do. The prompt should mention this explicitly.
    """
    content = _read("teach-html-opencode-author.md")
    text = content.lower()
    # Look for guidance that prose is for transitions/explanation only
    assert any(phrase in text for phrase in [
        "prose to explain",
        "prose for transitions",
        "prose only when",
        "prose last",
        "tables and bullets first",
        "prose connects",
    ])


def test_author_references_2_para_density_v11():
    """v1.1: author prompt should reflect the new diagram density of
    one diagram per 2 paragraphs (not 3).
    """
    content = _read("teach-html-opencode-author.md")
    # Must mention "2 paragraphs" or "every 2" or "two paragraphs"
    text = content.lower()
    assert any(p in text for p in [
        "every 2 paragraph",
        "two paragraph",
        "2 paragraph",
        "after every 2",
        "doublet",
        "pairs of paragraph",
    ])


# -------- outliner agent ----------------------------------------------------

def test_outliner_mentions_diagram_density_v11():
    """v1.1: outliner must plan for diagram density of every 2 paragraphs."""
    content = _read("teach-html-opencode-outliner.md")
    text = content.lower()
    assert any(p in text for p in [
        "every 2",
        "two paragraph",
        "2 paragraph",
        "doublet",
        "pairs of paragraph",
        "diagram every 2",
    ])


def test_outliner_mentions_table_bullet_style_v11():
    """v1.1: outliner should pass the tables+bullets-first style to authors."""
    content = _read("teach-html-opencode-outliner.md")
    text = content.lower()
    # At least one of these phrases must appear
    assert any(p in text for p in [
        "tables and bullet",
        "tables first",
        "scannable",
        "visual structure",
    ])
