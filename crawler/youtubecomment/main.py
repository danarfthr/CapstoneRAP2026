from config import logger
from scraper import run_scraper
from exporter import run_export


def main() -> None:
    logger.info("=== Starting YouTube Comment Scraper Pipeline ===")

    run_scraper()
    run_export()


if __name__ == "__main__":
    main()
