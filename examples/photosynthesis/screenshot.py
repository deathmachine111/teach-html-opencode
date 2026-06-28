"""Capture a full-page screenshot of the built demo HTML."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

html = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(f"file://{html}")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(out), full_page=True)
    browser.close()
print(f"screenshot: {out}")
