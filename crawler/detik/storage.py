import json
import asyncio
from typing import Set, Dict
from config import config, logger

class StorageManager:
    """
    Manages data persistence and deduplication.
    Uses an append-only JSON Lines (JSONL) format for crash resilience.
    """
    def __init__(self):
        self.cache_path = config.cache_file
        # Lock to prevent concurrent workers from writing at the exact same time
        self._write_lock = asyncio.Lock()

    def load_seen_urls(self) -> Set[str]:
        """
        Reads the existing JSONL cache line-by-line to rebuild 
        the set of already scraped URLs. 
        
        Using `for line in f` prevents the Memory Overflow issue seen in 
        the TypeScript version, allowing it to read gigabytes of data safely.
        """
        seen_urls = set()
        
        if not self.cache_path.exists():
            logger.info(f"No existing cache found at {self.cache_path}. Starting fresh.")
            return seen_urls

        logger.info(f"Reading existing cache from {self.cache_path}...")
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if "url" in record:
                            seen_urls.add(record["url"])
                    except json.JSONDecodeError:
                        logger.warning(f"Skipped corrupted JSON on line {line_num}")
                        
        except Exception as e:
            logger.error(f"Critical error reading cache: {e}")
            
        logger.info(f"Loaded {len(seen_urls)} previously scraped URLs into memory.")
        return seen_urls

    async def save_article(self, article_data: Dict) -> None:
        """
        Thread-safe async append to the JSONL cache.
        Triggered immediately after parsing so no data is lost if the process crashes.
        """
        # Acquire the lock so only one worker can write to the file at a time
        async with self._write_lock:
            try:
                # Offload the blocking disk I/O to a background thread 
                # so it doesn't freeze the async network requests in crawler.py
                await asyncio.to_thread(self._write_to_disk, article_data)
            except Exception as e:
                logger.error(f"Failed to save article {article_data.get('url')}: {e}")

    def _write_to_disk(self, article_data: Dict):
        """Synchronous write function executed inside the background thread."""
        with open(self.cache_path, "a", encoding="utf-8") as f:
            # ensure_ascii=False prevents Indonesian characters from turning into unicode escapes (\uXXXX)
            json_string = json.dumps(article_data, ensure_ascii=False)
            f.write(json_string + "\n")
            f.flush()  # Force OS to write to disk immediately

# Instantiate a global storage object to be used as a callback in crawler.py
storage = StorageManager()