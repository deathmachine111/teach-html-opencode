#!/usr/bin/env python3
"""Citation/reference tracker.

Convention: pandoc-style inline citations.
    [@Key]                 -> cite Key
    [@Key, p. 12]          -> cite Key with locator
    [@Key1; @Key2]         -> cite multiple

References file (references.md) uses pandoc reference-definition:
    [Key]: Full bibliographic entry text.

Public API:
    extract_citations(text_or_list) -> list[str]   # keys in order of appearance
    load_references(path)           -> dict        # {key: entry}
    build_report(cited, defined)     -> dict        # {undefined, uncited}
    render_bibliography(cited, defined) -> str      # HTML, cited-only, sorted
"""
import re

_CITE_BRACKET = re.compile(r'\[([^\]]*)\]')
_CITE_KEY = re.compile(r'@([A-Za-z][\w-]*)')
_REF_DEF = re.compile(r'^\[([A-Za-z][\w-]*)\]:\s*(.+)$')


def extract_citations(text):
    """Return citation keys found in text, in order of appearance (with dups)."""
    if isinstance(text, (list, tuple)):
        keys = []
        for t in text:
            keys.extend(extract_citations(t))
        return keys
    keys = []
    for m in _CITE_BRACKET.finditer(text):
        content = m.group(1)
        if not content.startswith('@'):
            continue
        for km in _CITE_KEY.finditer(content):
            keys.append(km.group(1))
    return keys


def load_references(path):
    refs = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = _REF_DEF.match(line)
            if m:
                refs[m.group(1)] = m.group(2).strip()
    return refs


def build_report(cited, defined):
    cited_set, defined_set = set(cited), set(defined)
    return {
        "undefined": sorted(cited_set - defined_set),
        "uncited": sorted(defined_set - cited_set),
    }


def render_bibliography(cited, defined):
    seen, out = [], []
    for k in cited:
        if k in defined and k not in seen:
            seen.append(k)
    for k in sorted(seen):
        out.append(f'<div class="ref" id="ref-{k}">{defined[k]}</div>')
    return '\n'.join(out)


def _read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


if __name__ == '__main__':
    import sys, os, json
    if len(sys.argv) < 2:
        print("usage: citations.py <src_dir>  # scans ch*.md + references.md")
        sys.exit(2)
    d = sys.argv[1]
    chap_files = sorted(f for f in os.listdir(d) if re.match(r'ch\d', f) and f.endswith('.md'))
    texts = [_read(os.path.join(d, f)) for f in chap_files]
    cited = extract_citations(texts)
    ref_path = os.path.join(d, 'references.md')
    defined = load_references(ref_path) if os.path.exists(ref_path) else {}
    rep = build_report(cited, defined)
    print(json.dumps({
        "cited_count": len(set(cited)),
        "defined_count": len(defined),
        "undefined": rep["undefined"],
        "uncited": rep["uncited"],
    }, indent=2))
    if rep["undefined"]:
        print("WARNING: cited but not defined:", rep["undefined"], file=sys.stderr)
        sys.exit(1)
