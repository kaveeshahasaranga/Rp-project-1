"""
Async Playwright-based DOM extractor for the touch-target service.

Launches a headless Chromium browser, navigates to the target URL, and
extracts bounding-box and style information for every interactive element
matching the WCAG-relevant CSS selector.
"""

from __future__ import annotations

import asyncio
import logging

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# Elements that require touch-target evaluation per WCAG 2.5.5 / 2.5.8.
INTERACTIVE_SELECTOR = (
    "button, "
    "a[href], "
    "input, "
    "select, "
    "textarea, "
    "[role='button'], "
    "[role='link'], "
    "[role='checkbox'], "
    "[role='menuitem'], "
    "[role='tab'], "
    "[tabindex='0']"
)


async def _extract(url: str) -> list[dict]:
    """
    Internal async coroutine that drives Playwright.

    Parameters
    ----------
    url:
        Fully-qualified http(s) URL to analyse.

    Returns
    -------
    list[dict]
        Each dict contains: tag, role, text, x, y, width, height,
        display, visibility, opacity.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            page = await browser.new_page(viewport={"width": 1440, "height": 900})
            logger.info("Navigating to %s", url)
            await page.goto(url, wait_until="networkidle", timeout=30_000)

            elements: list[dict] = await page.locator(INTERACTIVE_SELECTOR).evaluate_all(
                """
                elements => elements.map(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return {
                        tag:        el.tagName.toLowerCase(),
                        role:       el.getAttribute('role') || '',
                        text:       (
                                        el.innerText ||
                                        el.value ||
                                        el.getAttribute('aria-label') ||
                                        ''
                                    ).trim().slice(0, 80),
                        x:          Math.round(rect.x + window.scrollX),
                        y:          Math.round(rect.y + window.scrollY),
                        width:      Math.round(rect.width),
                        height:     Math.round(rect.height),
                        display:    style.display,
                        visibility: style.visibility,
                        opacity:    style.opacity
                    };
                })
                """
            )
            logger.info("Extracted %d elements from %s", len(elements), url)
            return elements
        finally:
            await browser.close()


def extract_elements(url: str) -> list[dict]:
    """
    Synchronous wrapper around the async Playwright extractor.

    Runs the async coroutine inside a fresh event loop so it can be called
    from synchronous Flask request handlers.

    Parameters
    ----------
    url:
        Fully-qualified http(s) URL to analyse.

    Returns
    -------
    list[dict]
        Interactive element descriptors.  Each dict has the keys:
        ``tag``, ``role``, ``text``, ``x``, ``y``, ``width``, ``height``,
        ``display``, ``visibility``, ``opacity``.
    """
    return asyncio.run(_extract(url))
