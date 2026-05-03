import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

import aiohttp
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# You can set these environment variables to use a real search API
# BING_SEARCH_ENDPOINT:   https://api.bing.microsoft.com/v7.0/search
# BING_SEARCH_KEY:        your-bing-api-key
# For a quick demo the script falls back to DuckDuckGo HTML scraping.

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("deepresearch")

# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------
@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    published: Optional[datetime] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _extract_date(text: str) -> Optional[datetime]:
    """Try to parse a date from a string using common patterns."""
    date_patterns = [
        r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",  # 2023-09-15 or 2023/09/15
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",  # 15/09/2023
        r"(\w{3,9})\s+(\d{1,2}),\s+(\d{4})",   # September 15, 2023
    ]
    for pat in date_patterns:
        m = re.search(pat, text)
        if m:
            try:
                return datetime.strptime(" ".join(m.groups()), "%Y %m %d")
            except Exception:
                try:
                    return datetime.strptime(" ".join(m.groups()), "%d %m %Y")
                except Exception:
                    try:
                        return datetime.strptime(" ".join(m.groups()), "%B %d %Y")
                    except Exception:
                        continue
    return None


async def fetch(session: aiohttp.ClientSession, url: str, **kwargs) -> Optional[str]:
    """Fetch a URL with a timeout, return text or None."""
    try:
        async with session.get(url, timeout=30, **kwargs) as resp:
            if resp.status != 200:
                log.warning("Non‑200 response %s from %s", resp.status, url)
                return None
            return await resp.text()
    except Exception as exc:
        log.error("Error fetching %s: %s", url, exc)
        return None


# ----------------------------------------------------------------------
# Search back‑ends
# ----------------------------------------------------------------------
class SearchEngine:
    """Abstract search engine."""

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        raise NotImplementedError


class BingSearchEngine(SearchEngine):
    """Bing Web Search API (requires BING_SEARCH_KEY env var)."""

    ENDPOINT = os.getenv("BING_SEARCH_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")
    API_KEY = os.getenv("BING_SEARCH_KEY")

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        if not self.API_KEY:
            raise RuntimeError("BING_SEARCH_KEY not set")
        headers = {
            "Ocp-Apim-Subscription-Key": self.API_KEY,
            "User-Agent": DEFAULT_USER_AGENT,
        }
        params = {"q": query, "count": max_results}
        async with aiohttp.ClientSession(headers=headers) as session:
            data = await fetch(session, self.ENDPOINT, params=params)
        if not data:
            return []
        payload = json.loads(data)
        results = []
        for item in payload.get("webPages", {}).get("value", []):
            results.append(
                SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                )
            )
        return results


class DuckDuckGoHTMLSearchEngine(SearchEngine):
    """Fallback HTML scraper for DuckDuckGo."""

    SEARCH_URL = "https://html.duckduckgo.com/html/"

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        params = {"q": query}
        async with aiohttp.ClientSession(headers={"User-Agent": DEFAULT_USER_AGENT}) as session:
            html = await fetch(session, self.SEARCH_URL, params=params)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        results = []
        for res in soup.select("div.result"):
            if len(results) >= max_results:
                break
            a_tag = res.select_one("a.result__a")
            snippet_tag = res.select_one("a.result__snippet")
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            url = a_tag["href"]
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet))
        return results


# ----------------------------------------------------------------------
# Content extraction
# ----------------------------------------------------------------------
async def extract_main_content(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Very naive article extraction – fetches the page and keeps <p> text."""
    html = await fetch(session, url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts/style
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    # Heuristic: longest consecutive <p> block
    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    content = "\n\n".join(paragraphs)
    return content if content else None


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
class DeepResearch:
    """Collects up‑to‑date sources for a given query."""

    def __init__(self, engine: Optional[SearchEngine] = None):
        self.engine = engine or self._detect_engine()

    @staticmethod
    def _detect_engine() -> SearchEngine:
        if BingSearchEngine.API_KEY:
            log.info("Using BingSearchEngine")
            return BingSearchEngine()
        log.info("Falling back to DuckDuckGoHTMLSearchEngine")
        return DuckDuckGoHTMLSearchEngine()

    async def gather(self, query: str, max_results: int = 10, fetch_content: bool = True) -> List[SearchResult]:
        log.info("Searching for: %s", query)
        results = await self.engine.search(query, max_results=max_results)

        if fetch_content:
            async with aiohttp.ClientSession(headers={"User-Agent": DEFAULT_USER_AGENT}) as session:
                tasks = [
                    self._enrich_result(session, r) for r in results
                ]
                await asyncio.gather(*tasks)

        # Sort by most recent if we managed to extract a date
        results.sort(
            key=lambda r: r.published or datetime.min,
            reverse=True,
        )
        return results

    async def _enrich_result(self, session: aiohttp.ClientSession, result: SearchResult):
        content = await extract_main_content(session, result.url)
        result.content = content
        # Try to get a publish date from snippet or title
        for source in (result.snippet, result.title):
            dt = _extract_date(source)
            if dt:
                result.published = dt
                break
        # Add a simple metadata entry (UTC, timezone-aware)
        result.metadata["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    async def overview(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Return a concise overview (title + short summary) for each result."""
        results = await self.gather(query, max_results=max_results, fetch_content=True)
        overviews = []
        for res in results:
            # Prefer extracted content; fall back to snippet; finally title only
            source_text = res.content or res.snippet or res.title
            # Very simple summary: first two sentences
            sentences = re.split(r'(?<=[.!?])\s+', source_text.strip())
            summary = " ".join(sentences[:2]) if sentences else source_text.strip()
            overviews.append({
                "title": res.title,
                "url": res.url,
                "summary": summary,
                "published": res.published.isoformat() if res.published else "unknown"
            })
        return overviews


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _format_result(res: SearchResult) -> str:
    # Safe handling of None content
    content_preview = ""
    if res.content:
        content_preview = res.content[:1000] + ("..." if len(res.content) > 1000 else "")

    lines = [
        f"Title: {res.title}",
        f"URL: {res.url}",
        f"Published: {res.published.isoformat() if res.published else 'unknown'}",
        f"Snippet: {res.snippet}",
        "",
        "Content:",
        content_preview,
        "",
        f"Metadata: {json.dumps(res.metadata, indent=2)}",
        "-" * 80,
    ]
    return "\n".join(lines)


def _format_overview(ov: Dict[str, str]) -> str:
    lines = [
        f"Title: {ov['title']}",
        f"URL: {ov['url']}",
        f"Published: {ov['published']}",
        f"Summary: {ov['summary']}",
        "-" * 80,
    ]
    return "\n".join(lines)


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="DeepResearch – fetch latest web sources for a query")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--no-content", action="store_true", help="Skip fetching full page content")
    parser.add_argument("--overview", action="store_true", help="Show concise overviews instead of full results")
    args = parser.parse_args()

    dr = DeepResearch()
    if args.overview:
        overviews = await dr.overview(args.query, max_results=args.num)
        for ov in overviews:
            print(_format_overview(ov))
    else:
        results = await dr.gather(
            args.query,
            max_results=args.num,
            fetch_content=not args.no_content,
        )
        for r in results:
            print(_format_result(r))


if __name__ == "__main__":
    asyncio.run(main())