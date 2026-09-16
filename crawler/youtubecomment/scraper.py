import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Set

from yt_dlp import YoutubeDL
from youtube_comment_downloader import YoutubeCommentDownloader

from config import config, logger

COMMENT_FIELDS = [
    "cid", "text", "time", "time_parsed", "author", "channel",
    "votes", "replies", "photo", "heart", "reply", "paid"
]

VIDEO_FIELDS = [
    "video_id", "video_title", "video_url", "video_channel",
    "video_channel_id", "video_view_count", "video_upload_date",
    "video_duration", "keyword"
]

class YouTubeSearcher:
    """Finds YouTube videos for a keyword using yt-dlp's ytsearch."""

    def __init__(self):
        self.ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }

    def search(self, keyword: str) -> List[Dict]:
        """Returns metadata for up to max_videos_per_keyword videos matching the keyword."""
        query = f"ytsearch{config.max_videos_per_keyword}:{keyword}"
        logger.info(f"Searching YouTube for '{keyword}' (max {config.max_videos_per_keyword} videos)...")

        with YoutubeDL(self.ydl_opts) as ydl:
            result = ydl.extract_info(query, download=False)

        entries = [e for e in (result or {}).get("entries", []) if e]
        videos = []
        for entry in entries:
            video_id = entry.get("id")
            if not video_id:
                continue
            videos.append({
                "video_id": video_id,
                "video_title": entry.get("title") or "",
                "video_url": entry.get("url") or f"https://www.youtube.com/watch?v={video_id}",
                "video_channel": entry.get("channel") or entry.get("uploader") or "",
                "video_channel_id": entry.get("channel_id") or entry.get("uploader_id") or "",
                "video_view_count": entry.get("view_count"),
                "video_upload_date": entry.get("upload_date"),
                "video_duration": entry.get("duration"),
                "keyword": keyword,
            })

        logger.info(f"Found {len(videos)} videos for '{keyword}'.")
        return videos


class CommentScraper:
    """Downloads comments for videos and enriches them with video context."""

    def __init__(self):
        self.downloader = YoutubeCommentDownloader()

    def scrape_video(self, video: Dict, on_comment) -> int:
        """
        Downloads comments for one video, calling on_comment(record) per comment.
        Returns the number of comments saved. Failures are logged and skipped.
        """
        logger.info(f"Scraping comments for: {video['video_title']} ({video['video_id']})")
        saved = 0
        try:
            comments = self.downloader.get_comments_from_url(
                video["video_url"],
                sort_by=config.comment_sort,
                language=config.comment_language,
                sleep=config.request_sleep_sec,
            )
            for comment in comments:
                if config.max_comments_per_video is not None and saved >= config.max_comments_per_video:
                    logger.info(f"Reached comment limit ({config.max_comments_per_video}) for {video['video_id']}.")
                    break
                on_comment(self._build_record(comment, video))
                saved += 1
        except RuntimeError as e:
            # YouTube raises "Failed to set sorting" when a video has comments disabled or none.
            logger.warning(f"Skipping {video['video_id']}: {e}")
        except Exception as e:
            logger.error(f"Failed to scrape {video['video_id']}: {type(e).__name__}: {e}")

        logger.info(f"Saved {saved} comments for {video['video_id']}.")
        return saved

    @staticmethod
    def _build_record(comment: Dict, video: Dict) -> Dict:
        record = {field: comment.get(field) for field in COMMENT_FIELDS}
        record["votes"] = (record.get("votes") or "0").strip() or "0"
        record["replies"] = record.get("replies") or "0"
        record["text"] = (record.get("text") or "").replace("\n", " ").strip()
        if record.get("time_parsed"):
            record["time_parsed"] = datetime.fromtimestamp(
                record["time_parsed"], tz=timezone.utc
            ).isoformat()
        if record.get("paid") is None:
            record.pop("paid")
        record.update(video)
        return record


class StorageManager:
    """
    Append-only JSON Lines persistence for comments, plus a small state file
    that tracks which videos were fully scraped so reruns skip them.
    """

    def __init__(self):
        self.cache_path = config.cache_file
        self.state_path: Path = config.base_dir / "data" / "scraped_videos.json"

    def load_seen_comment_ids(self) -> Set[str]:
        """Rebuilds the set of comment IDs already saved, reading the JSONL line-by-line."""
        seen = set()
        if not self.cache_path.exists():
            logger.info(f"No existing cache found at {self.cache_path}. Starting fresh.")
            return seen

        logger.info(f"Reading existing cache from {self.cache_path}...")
        with open(self.cache_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    cid = json.loads(line).get("cid")
                    if cid:
                        seen.add(cid)
                except json.JSONDecodeError:
                    logger.warning(f"Skipped corrupted JSON on line {line_num}")

        logger.info(f"Loaded {len(seen)} previously scraped comments.")
        return seen

    def load_scraped_videos(self) -> Set[str]:
        """Loads video IDs that were fully scraped in previous runs."""
        if not self.state_path.exists():
            return set()
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read {self.state_path}: {e}")
            return set()

    def mark_video_scraped(self, video_id: str, scraped: Set[str]) -> None:
        scraped.add(video_id)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(sorted(scraped), f)

    def save_comment(self, record: Dict) -> None:
        """Appends one comment to the JSONL cache and flushes immediately."""
        with open(self.cache_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()


def stream_cache_records() -> Iterator[Dict]:
    """Generator reading the JSONL cache line-by-line to keep memory usage flat."""
    if not config.cache_file.exists():
        logger.error(f"Cache file {config.cache_file} does not exist. Run the scraper first.")
        return

    with open(config.cache_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                logger.warning(f"Skipped corrupted JSON on line {line_num} during export.")


def run_scraper() -> None:
    """Main crawl loop: search each keyword, then scrape unseen videos' comments."""
    storage = StorageManager()
    searcher = YouTubeSearcher()
    scraper = CommentScraper()

    seen_comments = storage.load_seen_comment_ids()
    scraped_videos = storage.load_scraped_videos()

    for keyword in config.target_keywords:
        for video in searcher.search(keyword):
            video_id = video["video_id"]
            if video_id in scraped_videos:
                logger.info(f"Skipping already scraped video {video_id}.")
                continue

            def save_unique(record: Dict) -> None:
                if record["cid"] in seen_comments:
                    return
                seen_comments.add(record["cid"])
                storage.save_comment(record)

            saved = scraper.scrape_video(video, on_comment=save_unique)
            storage.mark_video_scraped(video_id, scraped_videos)

            if saved:
                time.sleep(config.video_sleep_sec)

    logger.info("Crawl complete.")
