"""Screenshot the demo HTML for visual verification.

Writes examples/photosynthesis/photosynthesis.png (full page) and
photosynthesis_top.png (above-the-fold).
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "photosynthesis.html"
PNG_FULL = ROOT / "photosynthesis.png"
PNG_TOP = ROOT / "photosynthesis_top.png"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto(f"file://{HTML}")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(PNG_TOP), full_page=False)
        await page.screenshot(path=str(PNG_FULL), full_page=True)
        await browser.close()
    print(f"wrote: {PNG_TOP}")
    print(f"wrote: {PNG_FULL}")


if __name__ == "__main__":
    asyncio.run(main())
