import asyncio
import json
import os
import random
import re
from urllib.parse import quote

from crawl4ai import AsyncWebCrawler


# --------------------------------------------------
# Configuration
# --------------------------------------------------

KEYWORDS = [
    "PLTN",
    "pembangkit listrik tenaga nuklir",
    "energi nuklir",
    "nuklir Indonesia",

    "PLTU",
    "pembangkit listrik tenaga uap",
    "batu bara",
    "batubara",

    "transisi energi",
    "dekarbonisasi",
]


OUTPUT_FILE = "data/discovered_urls.json"

# Delay between discovery requests.
# This is intentionally conservative.
MIN_DELAY = 3
MAX_DELAY = 6


# --------------------------------------------------
# Utility functions
# --------------------------------------------------

def load_existing_urls():
    """
    Load URLs that we discovered during previous runs.

    This prevents us from repeatedly storing the same URLs.
    """

    if not os.path.exists(OUTPUT_FILE):
        return set()

    with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
        urls = json.load(file)

    return set(urls)


def save_urls(urls):
    """
    Save discovered URLs to JSON.
    """

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            sorted(urls),
            file,
            ensure_ascii=False,
            indent=2
        )


def extract_cnn_urls(markdown):

    pattern = (
        r'https?://www\.cnnindonesia\.com/'
        r'[a-zA-Z0-9_-]+/'
        r'\d{14}-\d+-\d+/'
        r'[a-zA-Z0-9_-]+'
    )

    matches = re.findall(
        pattern,
        markdown
    )

    urls = set()

    for url in matches:

        url = url.rstrip(
            ".,;:!?"
        )

        urls.add(url)

    return urls


# --------------------------------------------------
# Search CNN
# --------------------------------------------------

async def discover_keyword(crawler, keyword):

    print(f"\n[SEARCH] Keyword: {keyword}")

    # CNN Indonesia's search URL.
    #
    # NOTE:
    # This URL structure may change if CNN changes
    # its website.
    search_url = (
    "https://www.cnnindonesia.com/search?"
    f"query={quote(keyword)}"
    )

    try:

        result = await crawler.arun(
            url=search_url
        )

        if not result.success:

            print(
                f"[ERROR] Search failed: {keyword}"
            )

            print(
                result.error_message
            )

            return set()

        urls = extract_cnn_urls(
            result.markdown
        )

        print(
            f"[FOUND] {len(urls)} URLs"
        )

        return urls

    except Exception as error:

        print(
            f"[ERROR] Exception while searching "
            f"{keyword}: {error}"
        )

        return set()


# --------------------------------------------------
# Main discovery process
# --------------------------------------------------

async def discover():

    existing_urls = load_existing_urls()

    print(
        f"[INFO] Existing URLs: "
        f"{len(existing_urls)}"
    )

    # List = preserves order
    all_urls = list(existing_urls)

    # Set = makes duplicate checking fast
    known_urls = set(existing_urls)

    MAX_URLS = 3

    async with AsyncWebCrawler() as crawler:

        for keyword in KEYWORDS:

            # Stop if global limit has been reached
            if len(all_urls) >= MAX_URLS:
                break

            urls = await discover_keyword(
                crawler,
                keyword
            )

            new_urls = 0

            for url in urls:

                if url not in known_urls:

                    all_urls.append(url)
                    known_urls.add(url)

                    new_urls += 1

                # Global limit
                if len(all_urls) >= MAX_URLS:
                    break

            print(
                f"[INFO] New URLs: {new_urls}"
            )

            print(
                f"[INFO] Total URLs: "
                f"{len(all_urls)}/{MAX_URLS}"
            )

            # Stop if limit reached
            if len(all_urls) >= MAX_URLS:
                print(
                    f"[INFO] Maximum of "
                    f"{MAX_URLS} URLs reached."
                )
                break

            # Wait before next keyword
            delay = random.uniform(
                MIN_DELAY,
                MAX_DELAY
            )

            print(
                f"[INFO] Waiting "
                f"{delay:.1f} seconds..."
            )

            await asyncio.sleep(delay)

    # Save only the first MAX_URLS
    all_urls = all_urls[:MAX_URLS]

    save_urls(all_urls)

    print("\n==============================")
    print("DISCOVERY COMPLETE")
    print("==============================")

    print(
        f"Total unique URLs: "
        f"{len(all_urls)}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":

    asyncio.run(discover())