import asyncio
import random
import urllib.parse
from typing import Set, Callable, Awaitable, List

import aiohttp
from aiohttp import ClientSession, ClientResponseError

from config import config, logger
from parser import parse_article_html, parse_search_results
from query_config import KEYWORD_TARGET_MAP

class AsyncFetcher:
    """
    Manages concurrent HTTP requests, User-Agent rotation, 
    and handles anti-bot rate limiting and cooldowns.
    """
    def __init__(self):
        # Limit concurrent connections to avoid overwhelming the server
        self.semaphore = asyncio.Semaphore(config.max_workers)
        self.is_cooling_down = False

    def _get_random_headers(self) -> dict:
        return {
            "User-Agent": random.choice(config.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    async def fetch_html(self, session: ClientSession, url: str) -> str:
        """Fetches HTML with retry logic and Cloudflare block detection."""
        for attempt in range(1, config.max_attempts + 1):
            # If another worker triggered a cooldown, wait before proceeding
            while self.is_cooling_down:
                await asyncio.sleep(5)

            async with self.semaphore:
                try:
                    # Random delay between 0.5 and 1.5 seconds to mimic human browsing
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    async with session.get(url, headers=self._get_random_headers(), timeout=config.request_timeout) as response:
                        status = response.status
                        html = await response.text()

                        # Detect HTTP rate limits or server bans
                        if status in (403, 429, 503) or any(marker in html.lower() for marker in config.block_markers):
                            logger.warning(f"Block detected on attempt {attempt} for {url} (HTTP {status})")
                            await self._trigger_cooldown()
                            continue # Retry after cooldown

                        response.raise_for_status()
                        return html

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.error(f"Network error on {url} (Attempt {attempt}/{config.max_attempts}): {type(e).__name__}")
                    await asyncio.sleep(2 ** attempt) # Exponential backoff: 2s, 4s, 8s
                    
        return "" # Return empty string if all attempts fail

    async def _trigger_cooldown(self):
        """Pauses all workers if the server detects bot activity."""
        if not self.is_cooling_down:
            self.is_cooling_down = True
            logger.error(f"Initiating cooldown for {config.cooldown_sec} seconds...")
            await asyncio.sleep(config.cooldown_sec)
            self.is_cooling_down = False
            logger.info("Cooldown finished. Resuming tasks.")


async def process_article(
    session: ClientSession,
    fetcher: AsyncFetcher,
    url: str,
    save_callback: Callable[[dict], Awaitable[None]],
    keyword: str,
):
    """Fetches an article, parses it, checks for PLTN/PLTU keywords, and saves if relevant."""
    try:
        html = await fetcher.fetch_html(session, url)
        if not html:
            return

        target = KEYWORD_TARGET_MAP.get(keyword, "UMUM")
        article_data = parse_article_html(html, url, keyword, target)

        # article_data is only returned if it passed the contains_keywords() and date-range gatekeepers in parser.py
        if article_data:
            logger.info(f"MATCH FOUND: {article_data['title']}")
            await save_callback(article_data)
    except Exception as e:
        # A single bad response (e.g. a malformed/never-closing SSL stream) must not
        # take down the whole asyncio.gather() batch for this search page.
        logger.error(f"Failed to process {url}: {type(e).__name__}: {e}")


async def crawl_search_results(
    keyword: str, 
    session: ClientSession, 
    fetcher: AsyncFetcher, 
    seen_urls: Set[str], 
    save_callback: Callable[[dict], Awaitable[None]]
):
    """Paginates through Detik's search results for a specific keyword."""
    logger.info(f"Starting search crawl for keyword: '{keyword}'")
    
    for page in range(1, config.max_search_pages + 1):
        # Detik search URL format (sortby=time ensures chronological scraping)
        query_params = urllib.parse.urlencode({
            "query": keyword,
            "sortby": "time",
            "page": page
        })
        search_url = f"{config.search_url}?{query_params}"
        
        logger.info(f"Fetching search page {page}: {search_url}")
        html = await fetcher.fetch_html(session, search_url)
        
        if not html:
            break

        article_urls = parse_search_results(html)
        
        # If no articles are found on the page, we've reached the end of the search results
        if not article_urls:
            logger.info(f"No more results found for '{keyword}' at page {page}. Ending keyword search.")
            break

        # Filter out URLs we've already scraped in previous runs
        new_urls = [url for url in article_urls if url not in seen_urls]
        logger.info(f"Page {page} found {len(article_urls)} links ({len(new_urls)} new).")

        # Create concurrent tasks for all new URLs on this search page
        tasks = []
        for url in new_urls:
            seen_urls.add(url) # Mark as seen immediately so concurrent workers don't duplicate
            tasks.append(process_article(session, fetcher, url, save_callback, keyword))
            
        if tasks:
            # Run all article fetches for this page concurrently
            await asyncio.gather(*tasks)


async def run_crawler(seen_urls: Set[str], save_callback: Callable[[dict], Awaitable[None]]):
    """Main entrypoint for the crawler."""
    fetcher = AsyncFetcher()
    
    # TCPConnector configures DNS caching and limits to maximize connection stability
    connector = aiohttp.TCPConnector(limit=config.max_workers, keepalive_timeout=30)
    
    async with ClientSession(connector=connector) as session:
        for keyword in config.target_keywords:
            await crawl_search_results(keyword, session, fetcher, seen_urls, save_callback)