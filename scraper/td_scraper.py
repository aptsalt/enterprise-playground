"""
TD Bank Website Scraper
========================
Captures HTML, screenshots, and structural data from TD.com personal banking pages.
Uses Playwright for JavaScript-rendered content.

Modes:
    Configured:  Scrape predefined URLs from WORKFLOW_CATEGORIES
    Discovery:   Auto-discover all reachable pages under /ca/en/personal-banking/

Usage:
    python -m scraper.td_scraper                        # Scrape configured URLs
    python -m scraper.td_scraper --discover             # Auto-discover + scrape
    python -m scraper.td_scraper --discover --max-pages 80
    python -m scraper.td_scraper --category accounts    # Scrape one category
    python -m scraper.td_scraper --url /banking/accounts/chequing-accounts
"""

import asyncio
import json
import random
import re
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse

import click
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    TD_BASE_URL, SCRAPE_DELAY, SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT,
    RAW_DIR, SCREENSHOTS_DIR, STRUCTURED_DIR, WORKFLOW_CATEGORIES,
    DISCOVER_MAX_DEPTH, DISCOVER_MAX_PAGES,
)

console = Console()

# URL scope for discovery
ALLOWED_PREFIXES = [
    "/ca/en/personal-banking/products/",
    "/ca/en/personal-banking/personal-investing/",
    "/ca/en/personal-banking/solutions/",
    "/ca/en/personal-banking/help-centre/",
]

EXCLUDED_PATTERNS = [
    "/login", "/sign-in", "/sign-on", ".pdf", "/fr/",
    "/privacy", "/legal", "/sitemap", "/search", "/careers",
    "/accessibility", "/security", "?icid=", "&icid=",
    "/api/", ".xml", ".json", "/404", "/error",
    "/business-banking/", "/commercial-banking/",
    "/wealth/", "/easyweb", "/webbroker",
]

# Category inference from URL path
CATEGORY_RULES = [
    ("accounts", ["/bank-accounts", "/chequing", "/savings"]),
    ("credit_cards", ["/credit-cards", "/credit-card"]),
    ("mortgages", ["/mortgages", "/mortgage", "/home-equity"]),
    ("loans", ["/borrowing", "/line-of-credit", "/loans"]),
    ("investing", ["/investing", "/tfsa", "/rrsp", "/gic", "/mutual-fund", "/fhsa", "/resp"]),
    ("insurance", ["/insurance"]),
    ("tools", ["/calculator", "/goal-builder"]),
    ("segments", ["/solutions/", "/new-to-canada", "/student", "/newcomer", "/youth"]),
]


class TDScraper:
    def __init__(self):
        self.base_url = TD_BASE_URL
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.pages_captured = 0
        self.errors = []

    async def start(self):
        """Initialize browser with realistic context."""
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": SCREENSHOT_WIDTH, "height": SCREENSHOT_HEIGHT},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-CA",
            timezone_id="America/Toronto",
        )
        console.print("[green]Browser started[/green]")

    async def stop(self):
        """Close browser."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    # ── Auto-Discovery ──────────────────────────────────────────────

    async def discover_urls(
        self,
        seed_urls: list[str] = None,
        max_depth: int = None,
        max_pages: int = None,
    ) -> set[str]:
        """
        Spider TD.com to discover all reachable personal banking pages.
        Starts from seed URLs and follows links within the allowed scope.
        """
        max_depth = max_depth or DISCOVER_MAX_DEPTH
        max_pages = max_pages or DISCOVER_MAX_PAGES

        # Build seed URLs from all configured categories
        if not seed_urls:
            seed_urls = []
            for cat in WORKFLOW_CATEGORIES.values():
                seed_urls.extend(cat["urls"])
            # Add the homepage
            seed_urls.append("")

        discovered = set()
        visited = set()
        queue = [(url, 0) for url in seed_urls]

        page = await self.context.new_page()

        console.print(f"[bold cyan]Discovering URLs (max_depth={max_depth}, max_pages={max_pages})...[/bold cyan]")

        try:
            while queue and len(discovered) < max_pages:
                url_path, depth = queue.pop(0)

                # Normalize
                url_path = url_path.rstrip("/")
                if url_path in visited or depth > max_depth:
                    continue
                visited.add(url_path)

                full_url = self._make_url(url_path)
                try:
                    await page.goto(full_url, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(1000)

                    # Dismiss overlays
                    await self._dismiss_overlays(page)

                    # Extract all links
                    links = await page.evaluate("""() => {
                        return [...document.querySelectorAll('a[href]')]
                            .map(a => {
                                try { return new URL(a.href).pathname; }
                                catch(e) { return null; }
                            })
                            .filter(Boolean);
                    }""")

                    new_count = 0
                    for link in links:
                        normalized = link.rstrip("/")
                        if self._is_in_scope(normalized) and normalized not in visited:
                            discovered.add(normalized)
                            if depth < max_depth:
                                queue.append((normalized, depth + 1))
                            new_count += 1

                    discovered.add(url_path)
                    console.print(
                        f"  [dim]Depth {depth}[/dim] {url_path[:70]} "
                        f"[green]+{new_count} links[/green] "
                        f"[dim]({len(discovered)}/{max_pages} total)[/dim]"
                    )

                    # Polite delay with jitter
                    await asyncio.sleep(SCRAPE_DELAY + random.uniform(0, 1))

                except Exception as e:
                    self.errors.append(f"Discovery failed: {url_path}: {e}")
                    console.print(f"  [red]Skip: {url_path} ({e})[/red]")

        finally:
            await page.close()

        console.print(f"[bold green]Discovered {len(discovered)} URLs[/bold green]")
        return discovered

    def _is_in_scope(self, url_path: str) -> bool:
        """Check if a URL is within the allowed scraping scope."""
        path_lower = url_path.lower()
        # Must match at least one allowed prefix
        if not any(path_lower.startswith(p) for p in ALLOWED_PREFIXES):
            return False
        # Must not match any excluded pattern
        if any(ex in path_lower for ex in EXCLUDED_PATTERNS):
            return False
        return True

    def auto_categorize(self, url_path: str) -> str:
        """Infer category from URL path."""
        path_lower = url_path.lower()
        for category, patterns in CATEGORY_RULES:
            if any(p in path_lower for p in patterns):
                return category
        return "general"

    async def scrape_discovered(self, max_pages: int = None) -> dict:
        """Full pipeline: discover URLs, then scrape all of them."""
        max_pages = max_pages or DISCOVER_MAX_PAGES

        # Step 1: Discover
        discovered = await self.discover_urls(max_pages=max_pages)
        urls = sorted(discovered)[:max_pages]

        console.print(f"\n[bold cyan]Scraping {len(urls)} discovered pages...[/bold cyan]")

        # Step 2: Scrape each
        all_results = {}
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Scraping", total=len(urls))

            for url_path in urls:
                category = self.auto_categorize(url_path)
                result = await self.capture_page(url_path, category)
                if result:
                    all_results.setdefault(category, []).append(result)
                progress.update(task, advance=1, description=f"[{category}] {url_path[:50]}")

        # Step 3: Save master index
        self._save_index(all_results)
        return all_results

    # ── Page Capture ────────────────────────────────────────────────

    async def capture_page(self, url_path: str, category: str) -> dict:
        """Capture a single page: HTML, screenshot, and structured data."""
        full_url = self._make_url(url_path)
        page = await self.context.new_page()

        try:
            console.print(f"  Navigating to: {full_url}")
            await page.goto(full_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(1500)

            # Dismiss cookie banners / overlays
            await self._dismiss_overlays(page)

            # Scroll to bottom to trigger lazy-loaded content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

            # Generate filename from URL
            slug = re.sub(r'[^a-z0-9]+', '-', url_path.strip('/').lower()).strip('-') or 'home'
            slug = slug[:80]  # Cap length

            # Save HTML
            html_content = await page.content()
            html_path = RAW_DIR / f"{category}_{slug}.html"
            html_path.write_text(html_content, encoding="utf-8")

            # Save screenshot
            screenshot_path = SCREENSHOTS_DIR / f"{category}_{slug}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

            # Extract structured data
            structured = await self._extract_structure(page, full_url, category)
            structured["raw_html_path"] = str(html_path)
            structured["screenshot_path"] = str(screenshot_path)
            structured["url_path"] = url_path

            # Save structured JSON
            json_path = STRUCTURED_DIR / f"{category}_{slug}.json"
            json_path.write_text(json.dumps(structured, indent=2, default=str), encoding="utf-8")

            self.pages_captured += 1
            console.print(f"  [green]Captured:[/green] {structured['title']}")
            return structured

        except Exception as e:
            error_msg = f"Failed to capture {full_url}: {e}"
            self.errors.append(error_msg)
            console.print(f"  [red]{error_msg}[/red]")
            return None
        finally:
            await page.close()
            await asyncio.sleep(SCRAPE_DELAY)

    async def _dismiss_overlays(self, page: Page):
        """Dismiss cookie banners and modal overlays."""
        for selector in [
            "#onetrust-accept-btn-handler",
            ".cookie-accept",
            "[data-testid='close-button']",
            "button[aria-label='Close']",
            ".modal-close",
        ]:
            try:
                btn = page.locator(selector)
                if await btn.is_visible(timeout=1500):
                    await btn.click()
                    await page.wait_for_timeout(300)
            except Exception:
                pass

    async def _extract_structure(self, page: Page, url: str, category: str) -> dict:
        """Extract structured data from a page."""
        data = await page.evaluate("""() => {
            const result = {
                title: document.title || '',
                meta_description: '',
                breadcrumbs: [],
                headings: [],
                links: [],
                buttons: [],
                forms: [],
                sections: [],
                images: [],
                navigation: [],
                tables: [],
                cards: [],
            };

            // Meta description
            const metaDesc = document.querySelector('meta[name="description"]');
            if (metaDesc) result.meta_description = metaDesc.getAttribute('content') || '';

            // Breadcrumbs
            document.querySelectorAll('nav[aria-label*="breadcrumb"] a, .breadcrumb a, [class*="breadcrumb"] a').forEach(a => {
                result.breadcrumbs.push({label: a.textContent.trim(), url: a.href});
            });

            // Headings
            document.querySelectorAll('h1, h2, h3').forEach(h => {
                result.headings.push({
                    level: parseInt(h.tagName[1]),
                    text: h.textContent.trim().substring(0, 200)
                });
            });

            // Links (all page links, not just main)
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.getAttribute('href');
                if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                    const label = a.textContent.trim().substring(0, 100);
                    if (label) {
                        result.links.push({
                            label: label,
                            url: a.href,
                            is_cta: a.classList.contains('cta') || a.classList.contains('btn') ||
                                    a.getAttribute('role') === 'button' ||
                                    a.closest('[class*="cta"]') !== null
                        });
                    }
                }
            });

            // Buttons
            document.querySelectorAll('button, [role="button"], input[type="submit"]').forEach(btn => {
                const label = (btn.textContent || btn.value || btn.getAttribute('aria-label') || '').trim();
                if (label) {
                    result.buttons.push({
                        label: label.substring(0, 100),
                        type: btn.type || 'button',
                        disabled: btn.disabled || false
                    });
                }
            });

            // Forms
            document.querySelectorAll('form').forEach(form => {
                const fields = [];
                form.querySelectorAll('input, select, textarea').forEach(input => {
                    if (input.type === 'hidden') return;
                    fields.push({
                        name: input.name || input.id || '',
                        type: input.type || input.tagName.toLowerCase(),
                        label: (document.querySelector('label[for="' + input.id + '"]')?.textContent || '').trim(),
                        required: input.required || false,
                        placeholder: input.placeholder || ''
                    });
                });
                if (fields.length > 0) {
                    result.forms.push({
                        action: form.action || '',
                        method: form.method || 'get',
                        fields: fields
                    });
                }
            });

            // Content sections
            document.querySelectorAll('section, [class*="section"], [class*="module"], [class*="Section"]').forEach((section, idx) => {
                const heading = section.querySelector('h1, h2, h3');
                const text = section.textContent.trim().substring(0, 500);
                if (text.length > 20) {
                    result.sections.push({
                        id: section.id || 'section-' + idx,
                        title: heading ? heading.textContent.trim() : '',
                        content_preview: text.substring(0, 300),
                        has_cta: section.querySelector('.cta, .btn, [role="button"], a[class*="btn"]') !== null
                    });
                }
            });

            // Cards (product cards, feature cards)
            document.querySelectorAll('[class*="card"], [class*="Card"], [class*="product-item"]').forEach(card => {
                const title = card.querySelector('h2, h3, h4, [class*="title"], [class*="Title"]');
                const desc = card.querySelector('p, [class*="description"], [class*="Description"]');
                if (title) {
                    result.cards.push({
                        title: title.textContent.trim().substring(0, 100),
                        description: desc ? desc.textContent.trim().substring(0, 200) : '',
                        link: card.querySelector('a')?.href || ''
                    });
                }
            });

            // Tables
            document.querySelectorAll('table').forEach((table, idx) => {
                const headers = [...table.querySelectorAll('th')].map(th => th.textContent.trim());
                const rowCount = table.querySelectorAll('tr').length;
                if (headers.length > 0 || rowCount > 1) {
                    result.tables.push({
                        id: table.id || 'table-' + idx,
                        headers: headers.slice(0, 10),
                        row_count: rowCount,
                        caption: table.querySelector('caption')?.textContent.trim() || ''
                    });
                }
            });

            return result;
        }""")

        data["url"] = url
        data["category"] = category
        data["captured_at"] = datetime.now().isoformat()
        return data

    # ── Category Scraping ───────────────────────────────────────────

    async def scrape_category(self, category_key: str) -> list[dict]:
        """Scrape all pages in a workflow category."""
        if category_key not in WORKFLOW_CATEGORIES:
            console.print(f"[red]Unknown category: {category_key}[/red]")
            return []

        cat = WORKFLOW_CATEGORIES[category_key]
        console.print(f"\n[bold cyan]Scraping: {cat['name']}[/bold cyan]")
        results = []
        for url_path in cat["urls"]:
            result = await self.capture_page(url_path, category_key)
            if result:
                results.append(result)
        return results

    async def scrape_all(self) -> dict:
        """Scrape all configured workflow categories."""
        all_results = {}
        for category_key in WORKFLOW_CATEGORIES:
            cat = WORKFLOW_CATEGORIES[category_key]
            if not cat["urls"]:
                continue
            results = await self.scrape_category(category_key)
            all_results[category_key] = results

        self._save_index(all_results)
        return all_results

    # ── Helpers ─────────────────────────────────────────────────────

    def _make_url(self, url_path: str) -> str:
        """Build full URL from a path."""
        if url_path.startswith("http"):
            return url_path
        # Absolute path from root (e.g. /ca/en/personal-banking/...)
        if url_path.startswith("/"):
            return f"https://www.td.com{url_path}"
        # Relative path (e.g. products/bank-accounts)
        return urljoin(self.base_url + "/", url_path)

    def _save_index(self, all_results: dict):
        """Save master index of all captured pages."""
        index = {
            "source": "TD Canada Trust - Personal Banking",
            "base_url": self.base_url,
            "categories": {k: len(v) for k, v in all_results.items()},
            "total_pages": self.pages_captured,
            "errors": self.errors,
            "captured_at": datetime.now().isoformat(),
        }
        index_path = STRUCTURED_DIR / "_index.json"
        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

        console.print(f"\n[bold green]Scraping complete![/bold green]")
        console.print(f"  Pages captured: {self.pages_captured}")
        console.print(f"  Errors: {len(self.errors)}")
        console.print(f"  Index saved: {index_path}")


@click.command()
@click.option("--category", "-c", default=None, help="Scrape a specific category")
@click.option("--url", "-u", default=None, help="Scrape a single URL path")
@click.option("--discover", is_flag=True, help="Auto-discover and scrape all reachable pages")
@click.option("--max-pages", default=None, type=int, help="Maximum pages in discovery mode")
def main(category: str, url: str, discover: bool, max_pages: int):
    """Scrape TD Bank personal banking pages."""
    async def run():
        scraper = TDScraper()
        await scraper.start()
        try:
            if discover:
                await scraper.scrape_discovered(max_pages=max_pages)
            elif url:
                await scraper.capture_page(url, category or "custom")
            elif category:
                await scraper.scrape_category(category)
            else:
                await scraper.scrape_all()
        finally:
            await scraper.stop()

    asyncio.run(run())


if __name__ == "__main__":
    main()
