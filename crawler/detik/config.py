import logging
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Set, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from query_config import KEYWORDS, START_DATE, END_DATE

@dataclass
class ScraperConfig:
    # --- 1. Target URLs & Strategy ---
    base_url: str = "https://www.detik.com/"
    # Detik's internal search endpoint (Option B Strategy)
    search_url: str = "https://www.detik.com/search/searchall"

    # --- 2. Energy Keywords & Synonyms ---
    # The crawler will search for these terms or filter articles containing them.
    # Sourced from crawler/query_config.py (shared across cnnindonesia/detik/kompas/youtubecomment).
    target_keywords: List[str] = field(default_factory=lambda: [kw for kw, _ in KEYWORDS])

    # --- 3. Date Range ---
    # Format: "YYYY-MM-DD". Set to None if you want to scrape all available time.
    start_date: Optional[str] = START_DATE
    end_date: Optional[str] = END_DATE

    # --- 4. Navigation Filters (For Index Crawling fallback) ---
    # Narrowed down from 17 root sections to focus strictly on hard news and economy.
    root_sections: Set[str] = field(default_factory=lambda: {
        "news", "finance", "edu", "properti"
    })
    
    ignored_categories: Set[str] = field(default_factory=lambda: {
        "home", "indeks", "video", "foto", "infografis", "oto galeri"
    })
    
    # --- 5. Request Limits & Concurrency ---
    max_workers: int = 8          # Concurrent async downloads
    max_attempts: int = 3         # Retries for failed pages
    max_search_pages: int = 200   # Max pages to paginate through Detik search results
    request_timeout: int = 20     # Seconds before giving up on a request
    cooldown_sec: int = 300       # 5-minute pause if Cloudflare triggers a block
    
    # --- 6. User-Agent Pools (Anti-Bot Disguises) ---
    user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ])

    # --- 7. Anti-Bot & Noise Markers ---
    block_markers: List[str] = field(default_factory=lambda: [
        "access denied", "unusual traffic", "captcha", "are you a robot", 
        "request blocked", "akses ditolak"
    ])
    
    noise_paragraphs: List[str] = field(default_factory=lambda: [
        "SCROLL TO CONTINUE WITH CONTENT",
        "ADVERTISEMENT",
        "ADVERTISEMENT SKIP"
    ])
    
    # --- 8. File Paths ---
    output_dir: Path = Path("data")
    cache_file: Path = Path("data/detik_energy_cache.jsonl")
    final_json: Path = Path("data/detik_energy_articles.json")
    final_csv: Path = Path("data/detik_energy_articles.csv")

    def __post_init__(self):
        # Automatically create the 'data' folder when config is initialized
        self.output_dir.mkdir(parents=True, exist_ok=True)

# Instantiate a global config object to import into other modules
config = ScraperConfig()

# Standardized logging setup so all modules use the exact same output format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("detik_energy_scraper")