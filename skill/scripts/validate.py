#!/usr/bin/env python3
"""Structural HTML validator.

Catches: unclosed tags, mismatched nesting, stray closing tags.
Uses a stack-based walk over html.parser events. Void and self-closing
elements never enter the stack. Returns a list of human-readable error
strings (empty == valid).

Public API:
    validate_html(html_str) -> list[str]
"""
from html.parser import HTMLParser

VOID = {
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr',
}


class _Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass  # <foo/> self-closing — never stacked

    def handle_endtag(self, tag):
        if tag in VOID:
            self.errors.append(
                f"Stray closing </{tag}> (line {self.getpos()[0]}): void element has no end tag")
            return
        open_tags = [t for t, _ in self.stack]
        if tag not in open_tags:
            self.errors.append(
                f"Stray closing </{tag}> with no matching open tag (line {self.getpos()[0]})")
            return
        while self.stack:
            t, ln = self.stack.pop()
            if t == tag:
                break
            self.errors.append(
                f"</{tag}> closes but <{t}> (opened line {ln}) was left unclosed "
                f"(mismatch at line {self.getpos()[0]})")


def validate_html(html_str):
    c = _Checker()
    c.feed(html_str)
    c.close()
    for t, ln in c.stack:
        c.errors.append(f"<{t}> (opened line {ln}) never closed")
    return c.errors


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("usage: validate.py <file.html>", file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding='utf-8') as f:
        errs = validate_html(f.read())
    if errs:
        for e in errs:
            print("ERROR:", e)
        sys.exit(1)
    print("OK: structurally valid")
