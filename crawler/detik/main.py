import asyncio
from config import logger
from storage import storage
from crawler import run_crawler
from exporter import run_export

async def main():
    logger.info("=== Starting Detik Energy Scraper Pipeline ===")
    
    # 1. Load seen URLs from the JSONL cache to avoid duplicate scraping
    seen_urls = storage.load_seen_urls()
    
    # 2. Run the asynchronous crawler (Option B Strategy via Detik Search)
    # Pass the storage.save_article function as the callback to save data instantly
    await run_crawler(seen_urls=seen_urls, save_callback=storage.save_article)
    
    logger.info("=== Crawl Complete. Starting Data Export ===")
    
    # 3. Convert the JSONL cache into final .csv and .json files
    run_export()

if __name__ == "__main__":
    # Ensure Windows doesn't throw ProactorEventLoop errors
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())