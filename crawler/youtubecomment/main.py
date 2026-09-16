import csv
import json

from config import config, logger
from scraper import run_scraper, stream_cache_records, VIDEO_FIELDS

CSV_HEADERS = VIDEO_FIELDS + [
    "cid", "author", "channel", "text", "time", "time_parsed",
    "votes", "replies", "heart", "reply", "paid"
]


def export_to_csv() -> int:
    """Converts the JSONL cache into a CSV file for spreadsheet/analysis tools."""
    logger.info(f"Starting CSV export to {config.final_csv}...")

    count = 0
    with open(config.final_csv, "w", encoding="utf-8", newline="") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=CSV_HEADERS, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for record in stream_cache_records():
            writer.writerow({key: _format_value(record.get(key)) for key in CSV_HEADERS})
            count += 1

    logger.info(f"CSV export complete. Saved {count} rows.")
    return count


def export_to_json_array() -> None:
    """Converts the JSONL cache into a standard JSON array file."""
    logger.info(f"Starting JSON Array export to {config.final_json}...")

    with open(config.final_json, "w", encoding="utf-8") as f_json:
        f_json.write("[\n")
        first = True
        for record in stream_cache_records():
            if not first:
                f_json.write(",\n")
            f_json.write(json.dumps(record, ensure_ascii=False, indent=4))
            first = False
        f_json.write("\n]")

    logger.info("JSON Array export complete.")


def _format_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def run_export() -> None:
    if not config.cache_file.exists():
        logger.error(f"Cache file {config.cache_file} does not exist. Nothing to export.")
        return

    total = export_to_csv()
    if total > 0:
        export_to_json_array()
        logger.info(f"Pipeline finished! Final datasets available in: {config.cache_file.parent}")


def main() -> None:
    logger.info("=== Starting YouTube Comment Scraper Pipeline ===")

    run_scraper()
    run_export()


if __name__ == "__main__":
    main()
