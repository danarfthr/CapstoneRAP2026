import asyncio
import json
import os
import random

from datetime import datetime

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig
)

from crawl4ai.content_filter_strategy import (
    PruningContentFilter
)

from crawl4ai.markdown_generation_strategy import (
    DefaultMarkdownGenerator
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

INPUT_FILE = "data/discovered_urls.json"
OUTPUT_FILE = "data/articles.json"

MIN_DELAY = 3
MAX_DELAY = 6

URL_FILE = "data/discovered_urls.json"
OUTPUT_FILE = "data/articles.json"


# --------------------------------------------------
# Load URLs
# --------------------------------------------------

def load_urls():

    if not os.path.exists(INPUT_FILE):

        print(
            f"[ERROR] {INPUT_FILE} does not exist."
        )

        print(
            "Run discovery.py first."
        )

        return []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# --------------------------------------------------
# Load existing articles
# --------------------------------------------------

def load_existing_articles():

    if not os.path.exists(OUTPUT_FILE):

        return {}

    with open(
        OUTPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        articles = json.load(file)

    # Convert list into dictionary indexed by URL.
    #
    # This makes checking for duplicates easy.

    return {
        article["url"]: article
        for article in articles
    }


# --------------------------------------------------
# Save articles
# --------------------------------------------------

def save_articles(articles):

    os.makedirs("data", exist_ok=True)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            list(articles.values()),
            file,
            ensure_ascii=False,
            indent=2
        )


# --------------------------------------------------
# Crawl one article
# --------------------------------------------------
content_filter = PruningContentFilter(
    threshold=0.45,
    threshold_type="dynamic"
)

markdown_generator = DefaultMarkdownGenerator(
    content_filter=content_filter,
    options={
        "ignore_links": True
    }
)

crawl_config = CrawlerRunConfig(
    markdown_generator=markdown_generator,

    # Remove things that are almost certainly
    # irrelevant to the article body.
    excluded_tags=[
        "nav",
        "footer",
        "header",
        "script",
        "style"
    ],

    # Ignore tiny text blocks.
    word_count_threshold=10
)

def clean_article_content(content):
    """
    Clean unwanted CNN Indonesia website UI elements
    from the extracted article content.
    """

    lines = content.splitlines()

    cleaned_lines = []

    unwanted_exact = {
        "login",
        "register",
        "logout",
        "ADVERTISEMENT",
        "SCROLL TO CONTINUE WITH CONTENT",
        "URL berhasil disalin",
        "Bagikan:",
    }

    skip_lihat_juga = False

    for line in lines:

        stripped = line.strip()

        # --------------------------------------------------
        # Handle "Lihat Juga" recommendation blocks
        # --------------------------------------------------

        if "Lihat Juga" in stripped:
            skip_lihat_juga = True
            continue

        if skip_lihat_juga:

            # The recommendation block usually ends
            # at the markdown table separator.
            if stripped == "| --- |":
                skip_lihat_juga = False

            continue

        # --------------------------------------------------
        # Remove unwanted UI text
        # --------------------------------------------------

        if stripped in unwanted_exact:
            continue

        # --------------------------------------------------
        # Remove leftover table/separator artifacts
        # --------------------------------------------------

        if stripped == "|":
            continue

        if stripped == "| --- |":
            continue

        # --------------------------------------------------
        # Keep everything else
        # --------------------------------------------------

        cleaned_lines.append(line)

    # --------------------------------------------------
    # Remove excessive blank lines
    # --------------------------------------------------

    final_lines = []

    previous_blank = False

    for line in cleaned_lines:

        if not line.strip():

            if previous_blank:
                continue

            previous_blank = True
            final_lines.append("")

        else:

            previous_blank = False
            final_lines.append(line)

    return "\n".join(final_lines).strip()


async def crawl_article(crawler, url, crawl_config):
    """
    Crawl one CNN Indonesia article and extract its main content.
    """

    print(f"[INFO] Crawling: {url}")

    try:

        result = await crawler.arun(
            url=url,
            config=crawl_config
        )

        if not result.success:

            print(
                f"[ERROR] Failed to crawl:\n"
                f"{url}\n"
                f"Reason: {result.error_message}"
            )

            return None

        # Get filtered Markdown from Crawl4AI
        content = result.markdown.fit_markdown

        # Clean CNN Indonesia UI elements
        content = clean_article_content(content)

        # Get page title
        title = result.metadata.get("title")

        article = {
            "url": url,
            "title": title,
            "scraped_at": datetime.now().isoformat(),
            "content": content
        }

        print(
            f"[SUCCESS] Article scraped: "
            f"{title}"
        )

        return article

    except Exception as e:

        print(
            f"[ERROR] Exception while crawling "
            f"{url}: {e}"
        )

        return None

def create_crawl_config():
    """
    Create the Crawl4AI configuration used
    for CNN Indonesia article pages.
    """

    content_filter = PruningContentFilter(
        threshold=0.45,
        threshold_type="dynamic"
    )

    markdown_generator = DefaultMarkdownGenerator(
        content_filter=content_filter,
        options={
            "ignore_links": True
        }
    )

    crawl_config = CrawlerRunConfig(
        markdown_generator=markdown_generator,

        excluded_tags=[
            "nav",
            "footer",
            "header",
            "script",
            "style",
            "form"
        ],

        word_count_threshold=10
    )

    return crawl_config


# --------------------------------------------------
# Main crawling process
# --------------------------------------------------

async def crawl_all():
    """
    Crawl all discovered URLs that have not
    already been scraped.
    """

    urls = load_urls()

    articles = load_existing_articles()

    print(
        f"[INFO] URLs discovered: "
        f"{len(urls)}"
    )

    print(
        f"[INFO] Articles already stored: "
        f"{len(articles)}"
    )

    crawl_config = create_crawl_config()

    async with AsyncWebCrawler() as crawler:

        for url in urls:

            # Skip URLs that have already been crawled
            if url in articles:

                print(
                    f"[SKIP] Already scraped: "
                    f"{url}"
                )

                continue

            article = await crawl_article(
                crawler,
                url,
                crawl_config
            )

            if article is not None:

                articles[url] = article

                save_articles(articles)

                print(
                    f"[INFO] Saved article."
                )

            # Wait before crawling another article
            delay = random.uniform(
                MIN_DELAY,
                MAX_DELAY
            )

            print(
                f"[INFO] Waiting "
                f"{delay:.1f} seconds..."
            )

            await asyncio.sleep(delay)

    print("\n==============================")
    print("CRAWLING COMPLETE")
    print("==============================")

    print(
        f"Total articles stored: "
        f"{len(articles)}"
    )



async def main():

    await crawl_all()

if __name__ == "__main__":
    asyncio.run(main())