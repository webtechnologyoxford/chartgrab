"""Capture a snapshot from a page with Playwright (Chromium/Firefox/WebKit, any OS).

Two modes:
  * capture_url(url): open a fresh browser (optionally with a saved storage state for
    sites you are logged into) and snapshot the page.
  * capture_cdp(endpoint, url_substring): attach to an already-running Chrome started with
    --remote-debugging-port and snapshot the matching tab, without navigating it.
"""
from __future__ import annotations

from typing import Optional

from ..snapshot import collector_expression


def capture_url(url: str, wait_ms: int = 3000, storage_state: Optional[str] = None,
                viewport=(1600, 1000), options: Optional[dict] = None) -> dict:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(storage_state=storage_state,
                                  viewport={"width": viewport[0], "height": viewport[1]})
        page = ctx.new_page()
        page.goto(url)
        page.wait_for_timeout(wait_ms)
        data = page.evaluate(collector_expression(options))
        browser.close()
        return data


def capture_cdp(endpoint: str, url_substring: str, options: Optional[dict] = None) -> dict:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        pages = [pg for c in browser.contexts for pg in c.pages if url_substring in pg.url]
        if len(pages) != 1:
            raise RuntimeError(f"expected exactly one tab matching {url_substring!r}, found {len(pages)}")
        return pages[0].evaluate(collector_expression(options))
