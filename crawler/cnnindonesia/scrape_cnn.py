"""Scraper artikel CNN Indonesia untuk analisis sentimen PLTN & PLTU.

Mengambil artikel berita dari hasil pencarian CNN Indonesia berdasarkan kata kunci energi (nuklir & batu bara), lalu menyimpan judul, tanggal, dan isi artikel ke berkas JSON untuk analisis sentimen/opini penulis.

Catatan teknis: hasil pencarian CNN dimuat lewat JavaScript (skeleton loader),jadi crawler menunggu konten dinamis termuat sebelum mengambil tautan artikel.
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin, urlparse

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig


# Konfigurasi
BASE_URL = "https://www.cnnindonesia.com"
SEARCH_URL = "https://www.cnnindonesia.com/search?query={query}"

# Kata kunci yang mengarah pada sentimen energi nuklir & batu bara.
KEYWORDS = ["PLTN", "PLTU", "nuklir", "batu bara"]

# Jumlah artikel yang diambil per kata kunci. Naikkan nilainya untuk dataset yang lebih besar (mis. 50). Mulai dari 15 untuk pengujian.
ARTICLE_LIMIT_PER_KEYWORD = 15

OUTPUT_FILE = "hasil_scraping_cnn.json"

# Waktu tunggu maksimum saat memuat halaman (ms). Halaman berat JS -> lebih lama.
PAGE_TIMEOUT = 60000

# Jeda antar-permintaan (detik) agar sopan terhadap server CNN.
REQUEST_DELAY = 1.5

# Pola ID artikel CNN pada URL
ARTICLE_ID_PATTERN = re.compile(r"/\d{12,}-\d+-\d+/")


def build_search_config() -> CrawlerRunConfig:
    """Konfigurasi crawl untuk halaman pencarian.
    Menunggu tautan artikel benar-benar muncul (bukan skeleton loader).
    """
    return CrawlerRunConfig(
        wait_for=(
            "js:() => document.querySelectorAll("
            "'article a[href*=cnnindonesia]').length > 0"
        ),
        page_timeout=PAGE_TIMEOUT,
    )

def extract_article_urls(html: str, limit: int) -> list[str]:
    """Ambil URL artikel dari halaman hasil pencarian CNN."""
    soup = BeautifulSoup(html, "html.parser")
    article_urls: list[str] = []

    for link in soup.select("article a[href]"):
        href = link.get("href")
        if not href:
            continue

        article_url = urljoin(BASE_URL, href).split("#", maxsplit=1)[0]
        parsed_url = urlparse(article_url)

        # Hanya domain CNN dan hanya tautan yang berpola ID artikel.
        if "cnnindonesia.com" not in parsed_url.netloc:
            continue
        if not ARTICLE_ID_PATTERN.search(article_url):
            continue
        # Lewati galeri foto/video jika tidak diinginkan (opsional): biarkan semua rubrik ikut untuk sekarang.
        if article_url not in article_urls:
            article_urls.append(article_url)
        if len(article_urls) >= limit:
            break

    return article_urls


def extract_article_data(html: str, url: str) -> dict:
    """Ekstrak judul, tanggal, dan isi dari satu halaman artikel."""
    soup = BeautifulSoup(html, "html.parser")

    # Judul: heading utama, fallback ke <title> halaman.
    heading = soup.select_one("h1")
    title = heading.get_text(strip=True) if heading else ""
    if not title:
        title_tag = soup.select_one("title")
        title = title_tag.get_text(strip=True) if title_tag else url

    # Tanggal terbit: elemen kecil abu-abu di bawah judul.
    date_el = soup.select_one(".text-cnn_grey.text-sm") or soup.select_one(
        "[class*=date]"
    )
    published = date_el.get_text(strip=True) if date_el else ""

    # Isi artikel: kontainer .detail-text. Buang elemen pengganggu.
    body_el = soup.select_one(".detail-text")
    content = ""
    if body_el:
        # Hapus skrip, iklan, dan kotak "baca juga" / artikel terkait.
        for junk in body_el.select(
            "script, style, .para_caption, .ads, "
            "[class*=baca], [class*=linksisip], [class*=read], table"
        ):
            junk.decompose()
        # Gabungkan paragraf menjadi teks bersih.
        paragraphs = [
            p.get_text(" ", strip=True) for p in body_el.select("p")
        ]
        content = "\n\n".join(par for par in paragraphs if par)
        # Fallback bila tidak ada tag <p>.
        if not content:
            content = body_el.get_text("\n", strip=True)

    return {
        "url": url,
        "judul": title,
        "tanggal": published,
        "isi": content,
        "jumlah_karakter_isi": len(content),
    }

async def collect_urls_for_keyword(
    crawler: AsyncWebCrawler, keyword: str, limit: int
) -> list[str]:
    """Jalankan pencarian untuk satu kata kunci dan kembalikan URL artikel."""
    search_url = SEARCH_URL.format(query=quote_plus(keyword))
    print(f"\n=== Kata kunci: '{keyword}' ===")
    print(f"    Pencarian: {search_url}")

    result = await crawler.arun(url=search_url, config=build_search_config())
    if not result.success:
        print(f"    GAGAL memuat pencarian: {result.error_message}")
        return []

    urls = extract_article_urls(result.html, limit)
    print(f"    Ditemukan {len(urls)} URL artikel.")
    return urls

async def main() -> None:
    all_articles: list[dict] = []
    seen_urls: set[str] = set()

    async with AsyncWebCrawler() as crawler:
        # 1. Kumpulkan URL artikel dari tiap kata kunci.
        keyword_to_urls: dict[str, list[str]] = {}
        for keyword in KEYWORDS:
            urls = await collect_urls_for_keyword(
                crawler, keyword, ARTICLE_LIMIT_PER_KEYWORD
            )
            keyword_to_urls[keyword] = urls
            await asyncio.sleep(REQUEST_DELAY)

        # 2. Crawl tiap artikel (dedup lintas kata kunci).
        article_config = CrawlerRunConfig(page_timeout=PAGE_TIMEOUT)
        for keyword, urls in keyword_to_urls.items():
            for url in urls:
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                result = await crawler.arun(url=url, config=article_config)
                if not result.success:
                    print(f"    [x] GAGAL: {url} ({result.error_message})")
                    await asyncio.sleep(REQUEST_DELAY)
                    continue

                data = extract_article_data(result.html, url)
                data["kata_kunci"] = keyword
                data["urutan"] = len(all_articles) + 1
                all_articles.append(data)
                print(f"    [{len(all_articles)}] OK: {data['judul'][:70]}")
                await asyncio.sleep(REQUEST_DELAY)

    # 3. Simpan hasil ke JSON.
    output = {
        "sumber": BASE_URL,
        "kata_kunci": KEYWORDS,
        "batas_per_kata_kunci": ARTICLE_LIMIT_PER_KEYWORD,
        "diambil_pada": datetime.now(timezone.utc).isoformat(),
        "jumlah_artikel": len(all_articles),
        "artikel": all_articles,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as output_file:
        json.dump(output, output_file, ensure_ascii=False, indent=2)

    print(f"\nSelesai. {len(all_articles)} artikel disimpan ke: {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())