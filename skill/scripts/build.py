#!/usr/bin/env python3
"""Build a single self-contained HTML module from markdown chapters.

Pipeline:
    src_dir/ch*.md  +  references.md  +  meta.json
        -> markdown -> HTML per chapter
        -> inline images as data URIs
        -> extract citations, render bibliography (cited only)
        -> wrap in editorial template (CSS + JS inlined)
    -> out_path (single .html, no external deps)

Public API:
    build_module(src_dir, templates_dir, out_path) -> out_path
"""
import os
import re
import json
import base64
import mimetypes

import markdown
from bs4 import BeautifulSoup

from citations import extract_citations, load_references, render_bibliography


def _read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def _chapter_files(src_dir):
    return sorted(f for f in os.listdir(src_dir)
                  if re.match(r'ch\d', f) and f.endswith('.md'))


_CITE_BRACKET = re.compile(r'\[([^\]]*)\]')
_CITE_KEY = re.compile(r'@([A-Za-z][\w-]*)')


def _linkify_citations(md_text):
    """Turn pandoc cites [@Key], [@K1; @K2], [@Key, p.12] into anchored
    superscripts pointing at the rendered bibliography (id=ref-Key).
    Only brackets whose content starts with '@' are touched, so markdown
    links and reference defs survive untouched."""
    def repl(m):
        inner = m.group(1)
        if not inner.startswith('@'):
            return m.group(0)
        keys = _CITE_KEY.findall(inner)
        if not keys:
            return m.group(0)
        links = '; '.join(f'<a href="#ref-{k}">{k}</a>' for k in keys)
        return f'<sup class="cite">[{links}]</sup>'
    return _CITE_BRACKET.sub(repl, md_text)


def _md_to_html(md_text):
    return markdown.markdown(
        _linkify_citations(md_text),
        extensions=['tables', 'fenced_code', 'toc', 'attr_list', 'smarty'],
    )


def _inline_images(soup, src_dir):
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src.startswith(('http://', 'https://', 'data:')):
            continue
        path = os.path.join(src_dir, src)
        if os.path.exists(path):
            mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
            b64 = base64.b64encode(open(path, 'rb').read()).decode()
            img['src'] = f'data:{mime};base64,{b64}'
    return soup


def _build_toc(soup):
    parts = []
    for h in soup.find_all(['h1', 'h2', 'h3']):
        hid = h.get('id')
        if not hid:
            continue
        level = int(h.name[1])
        parts.append(f'<a class="toc-l{level}" href="#{hid}">{h.get_text()}</a>')
    return '\n'.join(parts)


def build_module(src_dir, templates_dir, out_path):
    meta = {}
    mpath = os.path.join(src_dir, 'meta.json')
    if os.path.exists(mpath):
        meta = json.loads(_read(mpath))
    title = meta.get('title', os.path.basename(os.path.abspath(src_dir)))
    subtitle = meta.get('subtitle', '')
    author = meta.get('author', '')

    chap_files = _chapter_files(src_dir)
    chapter_html = [_md_to_html(_read(os.path.join(src_dir, f))) for f in chap_files]

    cited, bib_html = [], ''
    ref_path = os.path.join(src_dir, 'references.md')
    if os.path.exists(ref_path):
        defined = load_references(ref_path)
        texts = [_read(os.path.join(src_dir, f)) for f in chap_files]
        cited = extract_citations(texts)
        bib_html = render_bibliography(cited, defined)

    content_soup = BeautifulSoup('\n'.join(chapter_html), 'html.parser')
    content_soup = _inline_images(content_soup, src_dir)
    content_html = str(content_soup)
    toc_html = _build_toc(content_soup)

    css = _read(os.path.join(templates_dir, 'module.css'))
    js = _read(os.path.join(templates_dir, 'module.js'))

    subtitle_line = f'<p class="subtitle">{subtitle}</p>' if subtitle else ''
    byline_line = f'<p class="byline">{author}</p>' if author else ''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
<div class="page">
  <aside class="toc" id="toc">
    <div class="toc-brand">{title}</div>
    <nav class="toc-nav">
{toc_html}
    </nav>
  </aside>
  <main class="content" id="content">
    <header class="masthead">
      <h1 class="doc-title">{title}</h1>
      {subtitle_line}
      {byline_line}
    </header>
{content_html}
    <section class="bibliography" id="references">
      <h2>References</h2>
      <div class="refs">
{bib_html}
      </div>
    </section>
  </main>
</div>
<script>
{js}
</script>
</body>
</html>'''

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return out_path


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 4:
        print("usage: build.py <src_dir> <templates_dir> <out_path>", file=sys.stderr)
        sys.exit(2)
    out = build_module(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"built: {out}")
