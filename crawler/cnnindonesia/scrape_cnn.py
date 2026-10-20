"""Scraper artikel CNN Indonesia untuk analisis sentimen PLTN & PLTU.

Mencari artikel lewat halaman pencarian CNN Indonesia untuk tiap kata kunci,
menelusuri seluruh halaman hasil (paginasi) sampai batas aman, lalu mengambil
judul/tanggal/isi tiap artikel dan menyimpannya untuk analisis sentimen/opini
penulis.

Desain tahan-gangguan (terinspirasi folder crawler/detik, disederhanakan
untuk satu file):
  - Cache JSONL (append-only) -> tiap artikel langsung disimpan begitu
    berhasil di-scrape, jadi kalau proses berhenti di tengah jalan
    (Ctrl+C, anti-bot, koneksi putus), tinggal dijalankan ulang: artikel
    yang sudah ada di cache otomatis dilewati.
  - Retry dengan backoff untuk kegagalan jaringan / deteksi anti-bot CNN.
  - Paginasi berhenti otomatis begitu satu halaman tidak lagi membawa URL
    baru, dibatasi MAX_PAGES_PER_KEYWORD sebagai jaring pengaman (hasil
    pencarian CNN mulai melenceng dari topik di halaman yang sangat jauh).

Catatan teknis: hasil pencarian CNN dimuat lewat JavaScript (skeleton
loader), jadi crawler menunggu konten dinamis termuat sebelum mengambil
tautan artikel.
"""

import argparse
import asyncio
import csv
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus, urljoin, urlparse

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

sys.path.insert(0, str(Path(__file__).parent.parent))
from query_config import KEYWORDS as ALL_KEYWORDS, START_DATE, END_DATE

# Konfigurasi
BASE_URL = "https://www.cnnindonesia.com"
SEARCH_URL_TEMPLATE = "https://www.cnnindonesia.com/search?query={query}&page={page}"

# --shard N --shards M: jalankan beberapa proses scrape_cnn.py paralel,
# masing-masing menggarap 1/M kata kunci (diselang-seling KEYWORDS[N::M] biar
# kategori PLTN/PLTU/UMUM merata di tiap proses). Tiap shard punya file
# cache/checkpoint/output sendiri (nggak rebutan satu file yang sama), lalu
# digabung lewat merge_articles.py di akhir. Default shard=0 shards=1 =
# perilaku lama, satu proses menggarap semua kata kunci.
_parser = argparse.ArgumentParser()
_parser.add_argument("--shard", type=int, default=0)
_parser.add_argument("--shards", type=int, default=1)
_args, _ = _parser.parse_known_args()
SHARD, SHARDS = _args.shard, _args.shards

KEYWORDS: list[tuple[str, str]] = ALL_KEYWORDS[SHARD::SHARDS]
_suffix = f"_shard{SHARD}" if SHARDS > 1 else ""

# Kata kunci & rentang tahun: lihat crawler/query_config.py (dipakai bareng semua sumber).

# Jaring pengaman jumlah halaman pencarian per kata kunci. Pencarian akan berhenti lebih cepat begitu satu halaman tidak membawa URL baru, tapi angka ini mencegah crawl "tak berujung" ke halaman yang sudah tidak relevan (hasil pengujian: relevansi menurun tajam setelah ~halaman 80).
MAX_PAGES_PER_KEYWORD = 50

# Berkas cache JSONL: satu baris = satu artikel. Dipakai untuk resume.
CACHE_FILE = Path(f"cnn_energy_cache{_suffix}.jsonl")

# Checkpoint: kata kunci yang sudah tuntas (semua halaman pencarian + semua
# artikelnya sudah dicoba). Dilewati kalau run berikutnya nemu kata kunci ini
# lagi, jadi restart nggak perlu re-paginasi ulang kata kunci yang sudah selesai.
COMPLETED_KEYWORDS_FILE = Path(f"cnn_completed_keywords{_suffix}.json")

# Hasil akhir setelah cache diekspor.
OUTPUT_JSON = Path(f"hasil_scraping_cnn_attempt2{_suffix}.json")
OUTPUT_CSV = Path(f"hasil_scraping_cnn_attempt2{_suffix}.csv")

# Waktu tunggu maksimum saat memuat halaman (ms).
PAGE_TIMEOUT = 30000

# Jeda antar-permintaan (detik) agar sopan terhadap server CNN.
REQUEST_DELAY = 1.0

# Retry untuk kegagalan jaringan / anti-bot.
MAX_FETCH_ATTEMPTS = 3
RETRY_BASE_DELAY = 5.0  # detik; backoff eksponensial: 5s, 10s, 20s, ...

# Pola ID artikel CNN pada URL
ARTICLE_ID_PATTERN = re.compile(r"/\d{12,}-\d+-\d+/")
# 4 digit pertama dari ID artikel adalah tahun terbit.
ARTICLE_YEAR_PATTERN = re.compile(r"/(\d{4})\d{8,}-\d+-\d+/")

INDONESIAN_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6,
    "jul": 7, "agu": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12,
}

def extract_year_from_url(url: str) -> Optional[int]:
    """Ambil tahun dari ID artikel di URL"""
    match = ARTICLE_YEAR_PATTERN.search(url)
    return int(match.group(1)) if match else None

def parse_cnn_date(text: str) -> Optional[date]:
    """Parse tanggal format CNN, mis. 'Rabu, 02 Sep 2026 11:15 WIB' -> date."""
    match = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if not match:
        return None
    day, month_name, year = match.groups()
    month = INDONESIAN_MONTHS.get(month_name.lower()[:3])
    if not month:
        return None
    try:
        return date(int(year), month, int(day))
    except ValueError:
        return None

def is_year_within_range(year: Optional[int]) -> bool:
    """True bila tahun tidak diketahui atau berada dalam rentang START_DATE..END_DATE."""
    if year is None:
        return True
    if START_DATE and year < date.fromisoformat(START_DATE).year:
        return False
    if END_DATE and year > date.fromisoformat(END_DATE).year:
        return False
    return True

def build_search_config() -> CrawlerRunConfig:
    """Konfigurasi crawl untuk halaman pencarian. Menunggu tautan artikel benar-benar muncul .
    """
    return CrawlerRunConfig(
        wait_for=(
            "js:() => document.querySelectorAll("
            "'article a[href*=cnnindonesia]').length > 0"
        ),
        page_timeout=PAGE_TIMEOUT,
    )

ARTICLE_CONFIG = CrawlerRunConfig(page_timeout=PAGE_TIMEOUT)

async def fetch_with_retry(
    crawler: AsyncWebCrawler, url: str, config: CrawlerRunConfig
):
    """Jalankan crawler.arun() dengan retry + backoff eksponensial.
    Menangani baik result.success == False maupun exception yang
    dilempar crawl4ai sendiri saat CNN mendeteksi trafik tidak wajar.
    """
    for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
        try:
            result = await crawler.arun(url=url, config=config)
            if result.success:
                return result
            print(f"      [!] Gagal (percobaan {attempt}): {result.error_message}")
        except Exception as exc:  # crawl4ai kadang raise,
            print(f"      [!] Error (percobaan {attempt}): {type(exc).__name__}: {exc}")

        if attempt < MAX_FETCH_ATTEMPTS:
            backoff = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            print(f"      Menunggu {backoff:.0f}s sebelum mencoba lagi...")
            await asyncio.sleep(backoff)

    return None

def extract_article_urls(html: str) -> list[str]:
    """Ambil semua URL artikel dari satu halaman hasil pencarian CNN."""
    soup = BeautifulSoup(html, "html.parser")
    article_urls: list[str] = []

    for link in soup.select("article a[href]"):
        href = link.get("href")
        if not href:
            continue

        article_url = urljoin(BASE_URL, href).split("#", maxsplit=1)[0]
        parsed_url = urlparse(article_url)

        if "cnnindonesia.com" not in parsed_url.netloc:
            continue
        if not ARTICLE_ID_PATTERN.search(article_url):
            continue
        if article_url not in article_urls:
            article_urls.append(article_url)

    return article_urls

def extract_article_data(html: str, url: str) -> dict:
    """Ekstrak judul, tanggal, dan isi dari satu halaman artikel."""
    soup = BeautifulSoup(html, "html.parser")

    heading = soup.select_one("h1")
    title = heading.get_text(strip=True) if heading else ""
    if not title:
        title_tag = soup.select_one("title")
        title = title_tag.get_text(strip=True) if title_tag else url

    date_el = soup.select_one(".text-cnn_grey.text-sm") or soup.select_one(
        "[class*=date]"
    )
    published = date_el.get_text(strip=True) if date_el else ""

    body_el = soup.select_one(".detail-text")
    content = ""
    if body_el:
        for junk in body_el.select(
            "script, style, .para_caption, .ads, "
            "[class*=baca], [class*=linksisip], [class*=read], table"
        ):
            junk.decompose()
        paragraphs = [p.get_text(" ", strip=True) for p in body_el.select("p")]
        content = "\n\n".join(par for par in paragraphs if par)
        if not content:
            content = body_el.get_text("\n", strip=True)

    return {
        "url": url,
        "judul": title,
        "tanggal": published,
        "isi": content,
        "jumlah_karakter_isi": len(content),
    }

class ResilientCrawler:
    """Bungkus AsyncWebCrawler dengan auto-recovery. Setelah berjam-jam jalan
    terus-menerus, browser Chromium di baliknya kadang mati sendiri (muncul
    sebagai 'Target crashed' / 'Connection closed while reading from the
    driver' pada SETIAP request berikutnya, bukan cuma sekali - retry di
    fetch_with_retry() tidak menolong karena browser-nya sendiri yang rusak).
    Kalau gagal total beberapa kali berturut-turut, browser dianggap rusak
    dan dibuat ulang otomatis, supaya crawl bisa lanjut tanpa restart manual.
    """

    def __init__(self, restart_after_failures: int = 5):
        self.restart_after_failures = restart_after_failures
        self.consecutive_failures = 0
        self.crawler = AsyncWebCrawler()

    async def start(self):
        await self.crawler.start()

    async def close(self):
        await self.crawler.close()

    async def _restart_browser(self):
        print(
            f"    [!] {self.consecutive_failures} kegagalan beruntun - browser "
            f"sepertinya rusak (crash/connection closed), membuat ulang sesi browser..."
        )
        try:
            await self.crawler.close()
        except Exception:
            pass  # browser yang sudah rusak kadang gagal ditutup dengan bersih
        self.crawler = AsyncWebCrawler()
        await self.crawler.start()
        self.consecutive_failures = 0

    async def fetch(self, url: str, config: CrawlerRunConfig):
        result = await fetch_with_retry(self.crawler, url, config)
        if result is None:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.restart_after_failures:
                await self._restart_browser()
        else:
            self.consecutive_failures = 0
        return result

async def collect_urls_for_keyword(
    resilient: ResilientCrawler, query: str
) -> list[str]:
    """Telusuri semua halaman pencarian untuk satu kata kunci. Berhenti begitu satu halaman tidak membawa URL baru, atau setelah MAX_PAGES_PER_KEYWORD halaman (jaring pengaman).
    """
    print(f"\n=== Kata kunci: '{query}' ===")
    all_urls: list[str] = []
    seen_in_keyword: set[str] = set()

    for page in range(1, MAX_PAGES_PER_KEYWORD + 1):
        search_url = SEARCH_URL_TEMPLATE.format(query=quote_plus(query), page=page)
        result = await resilient.fetch(search_url, build_search_config())

        if result is None:
            print(f"    Halaman {page}: gagal total setelah retry, hentikan paginasi.")
            break

        page_urls = extract_article_urls(result.html)
        new_urls = [u for u in page_urls if u not in seen_in_keyword]

        if not new_urls:
            print(f"    Halaman {page}: tidak ada URL baru, paginasi selesai.")
            break

        seen_in_keyword.update(new_urls)
        all_urls.extend(new_urls)
        print(f"    Halaman {page}: +{len(new_urls)} URL baru (total {len(all_urls)}).")
        await asyncio.sleep(REQUEST_DELAY)

    return all_urls

def load_seen_urls() -> set[str]:
    """Baca SEMUA cache JSONL (punya shard ini + shard lain + cache lama
    sebelum sharding) biar antar-shard nggak rebutan scrape URL yang sama."""
    seen: set[str] = set()
    for cache_path in sorted(Path(".").glob("cnn_energy_cache*.jsonl")):
        with open(cache_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    seen.add(record["url"])
                except (json.JSONDecodeError, KeyError):
                    continue

    print(f"Ditemukan cache: {len(seen)} artikel sudah pernah di-scrape sebelumnya (semua shard).")
    return seen

def append_to_cache(article: dict) -> None:
    """Tambahkan satu artikel ke cache JSONL."""
    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(article, ensure_ascii=False) + "\n")
        f.flush()

def load_completed_keywords() -> set[str]:
    """Gabungan checkpoint punya shard ini + shard lain + checkpoint lama
    sebelum sharding - satu kata kunci cuma pernah masuk ke satu shard, jadi
    aman digabung tanpa risiko shard lain kerja dobel."""
    completed: set[str] = set()
    for path in Path(".").glob("cnn_completed_keywords*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                completed.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    return completed

def save_completed_keywords(completed: set[str]) -> None:
    with open(COMPLETED_KEYWORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(completed), f, ensure_ascii=False, indent=2)

def export_cache_to_final_files() -> int:
    """Ubah cache JSONL menjadi berkas JSON array + CSV akhir."""
    if not CACHE_FILE.exists():
        print("Tidak ada cache untuk diekspor.")
        return 0

    records = []
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    output = {
        "sumber": BASE_URL,
        "kata_kunci": KEYWORDS,
        "batas_halaman_per_kata_kunci": MAX_PAGES_PER_KEYWORD,
        "diambil_pada": datetime.now(timezone.utc).isoformat(),
        "jumlah_artikel": len(records),
        "artikel": records,
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    headers = ["url", "judul", "tanggal", "kata_kunci", "target", "isi"]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key, "") for key in headers})

    print(f"\nEkspor selesai: {len(records)} artikel -> {OUTPUT_JSON} dan {OUTPUT_CSV}")
    return len(records)

async def main() -> None:
    seen_urls = load_seen_urls()
    completed_keywords = load_completed_keywords()
    if completed_keywords:
        print(f"Kata kunci sudah tuntas dari run sebelumnya: {len(completed_keywords)}/{len(KEYWORDS)} - dilewati\n")

    resilient = ResilientCrawler()
    await resilient.start()

    try:
        for query, target in KEYWORDS:
            if query in completed_keywords:
                continue

            urls = await collect_urls_for_keyword(resilient, query)

            new_urls = [u for u in urls if u not in seen_urls]

            # Buang URL di luar rentang tahun berdasarkan ID artikel, sebelum halamannya dibuka.
            candidate_urls = []
            skipped_out_of_range = 0
            for url in new_urls:
                if not is_year_within_range(extract_year_from_url(url)):
                    skipped_out_of_range += 1
                    seen_urls.add(url)
                    continue
                candidate_urls.append(url)

            print(
                f"    -> {len(urls)} URL ditemukan, {len(candidate_urls)} baru "
                f"untuk diambil ({skipped_out_of_range} dilewati di luar rentang tahun, "
                f"sisanya sudah ada di cache)."
            )

            for url in candidate_urls:
                result = await resilient.fetch(url, ARTICLE_CONFIG)
                seen_urls.add(url)  # tandai sudah dicoba, sukses ataupun gagal

                if result is None:
                    print(f"    [x] Lewati (gagal total): {url}")
                    continue

                data = extract_article_data(result.html, url)

                # Cek ulang dengan tanggal asli dari halaman.
                real_year = parse_cnn_date(data["tanggal"])
                real_year = real_year.year if real_year else extract_year_from_url(url)
                if not is_year_within_range(real_year):
                    print(f"    [-] Lewati (di luar rentang tahun): {data['judul'][:70]}")
                    continue

                data["kata_kunci"] = query
                data["target"] = target
                append_to_cache(data)
                print(f"    [v] Tersimpan: {data['judul'][:70]}")
                await asyncio.sleep(REQUEST_DELAY)

            # Checkpoint: kata kunci ini tuntas (semua halaman + semua
            # artikelnya sudah dicoba). Simpan sekarang & ekspor ulang file
            # akhir, supaya restart nggak perlu re-paginasi kata kunci yang
            # sudah selesai, dan file hasil selalu fresh untuk diserahkan.
            completed_keywords.add(query)
            save_completed_keywords(completed_keywords)
            export_cache_to_final_files()
            print(f"    [checkpoint] '{query}': tuntas, file hasil sudah di-refresh")
    finally:
        await resilient.close()

    export_cache_to_final_files()

if __name__ == "__main__":
    asyncio.run(main())