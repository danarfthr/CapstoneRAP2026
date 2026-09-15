import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ScraperConfig:
    # --- 1. Search Keywords ---
    # Matches crawler/detik keyword list so both datasets cover the same topics.
    target_keywords: List[str] = field(default_factory=lambda: [
        "PLTN",
        "PLTU",
        "Pembangkit Listrik Tenaga Nuklir",
        "Pembangkit Listrik Tenaga Uap",
        "Energi Nuklir",
        "Reaktor Nuklir",
        "Pembangkit Listrik Batubara"
    ])

    # --- 2. Search Limits ---
    max_videos_per_keyword: int = 10   # Videos taken from yt-dlp results per keyword

    # --- 3. Comment Limits & Timing ---
    max_comments_per_video: Optional[int] = None  # None = download all comments
    comment_sort: int = 1              # 0 = popular, 1 = recent (SORT_BY_RECENT)
    comment_language: Optional[str] = None  # None lets YouTube decide; "id" forces generated text
    request_sleep_sec: float = 0.1     # Pause between comment pagination requests
    video_sleep_sec: float = 1.0       # Pause between videos to reduce rate-limit risk

    # --- 4. File Paths ---
    # Anchored to this file's directory so the pipeline can run from anywhere.
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent)
    cache_file: Path = field(init=False)
    final_json: Path = field(init=False)
    final_csv: Path = field(init=False)

    def __post_init__(self):
        self.cache_file = self.base_dir / "data" / "youtube_comments_cache.jsonl"
        self.final_json = self.base_dir / "data" / "youtube_comments.json"
        self.final_csv = self.base_dir / "data" / "youtube_comments.csv"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

# Instantiate a global config object to import into other modules
config = ScraperConfig()

# Standardized logging setup so all modules use the exact same output format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("youtube_comment_scraper")
