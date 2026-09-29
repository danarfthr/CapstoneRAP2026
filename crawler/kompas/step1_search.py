"""
Step 1 — Kumpulkan judul + URL artikel dari halaman search.

Selector & pola URL diambil dari config.py (khas per sumber).
Daftar query & rentang tahun diambil dari crawler/query_config.py (dipakai
bareng semua sumber: cnnindonesia/detik/kompas/youtubecomment).

Query dijalankan per-tahun (start_date/end_date) supaya sebaran tahun
terjamin, bukan cuma ngandelin pagination dari hasil "semua waktu" yang
didominasi artikel terbaru.

Jalankan dari folder ini:
    python step1_search.py

Output: data/urls.json
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
import re
from collections import Counter

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    JsonCssExtractionStrategy,
)

from config import SOURCE, SEARCH_SCHEMA, WAIT_FOR, search_url, valid_artikel
from query_config import KEYWORDS, KEYWORDS_TEST, START_YEAR, END_YEAR

# ---------------------------------------------------------------- konfigurasi

MODE_TEST = False          # True = pakai KEYWORDS_TEST (5 query saja)
MAX_PAGE_PER_TAHUN = None     # jaring pengaman - halaman_maks (dari total hasil
                            # asli Kompas) yang beneran nyetop paginasi
TAHUN_MIN = 2021
TAHUN_MAX = 2026
JEDA_ANTAR_HALAMAN = 3     # detik
MAX_RETRY = 3
JEDA_RETRY_AWAL = 5        # detik, dilipatgandakan tiap retry (backoff)
MAX_PAGE_HARD_CAP = 200

OUT_DIR = Path(__file__).parent / "data"
OUT_FILE = OUT_DIR / "urls.json"
PROGRESS_FILE = OUT_DIR / "progress.json"

# ------------------------------------------------------------------- helpers


def tahun_dari_url(u: str):
    """Kompas punya dua pola URL:
         baru : /read/2026/09/13/164234078/...
         lama : /read/xml/2011/04/30/18175286/...
    """
    m = re.search(r"/read/(?:xml/)?(\d{4})/(\d{2})/(\d{2})/", u or "")
    return int(m.group(1)) if m else None


def bersihkan_url(u: str) -> str:
    """Buang query string & fragment biar dedup akurat."""
    if not u:
        return ""
    return u.split("?")[0].split("#")[0].rstrip("/")


def total_hasil_dari_html(html: str):
    """Baca total hasil pencarian asli dari span headArticle-count di
    halaman 1. Dipakai buat mbatesin halaman maksimum -- kalau kita minta
    halaman di luar rentang hasil asli, Kompas nggak kasih empty state yang
    rapi, tapi hang total (HTML kosong, .articleItem nggak pernah muncul
    walau ditunggu 45s+). Ketauan lewat tag [ANTIBOT] crawl4ai, padahal
    bukan soal kedeteksi bot - cuma quirk pagination di luar rentang."""
    m = re.search(r"headArticle-count[^>]*>([^<]+)<", html or "")
    if not m:
        return None
    digit = re.sub(r"[^\d]", "", m.group(1))
    return int(digit) if digit else None


# ------------------------------------------------------------------ crawling


async def arun_dengan_retry(crawler, url, cfg):
    """crawl4ai kadang timeout nunggu .articleItem di request awal (cold
    browser context). Retry dengan backoff sebelum nyerah."""
    jeda = JEDA_RETRY_AWAL
    for percobaan in range(1, MAX_RETRY + 1):
        res = await crawler.arun(url, config=cfg)
        if res.success:
            return res
        if percobaan == MAX_RETRY:
            return res
        print(f"    [retry {percobaan}/{MAX_RETRY}] {res.error_message} "
              f"- tunggu {jeda}s")
        await asyncio.sleep(jeda)
        jeda *= 2
    return res


async def collect_links_tahun(crawler, keyword: str, target: str,
                               tahun: int) -> tuple[list[dict], bool]:
    """Ambil SEMUA artikel asli untuk satu (keyword, tahun). Return (hasil,
    selesai) - selesai=False kalau berhenti gara-gara request gagal (browser
    crash, timeout habis retry), biar batch ini nggak ditandai 'done' dan
    dicoba lagi pas restart."""
    cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(SEARCH_SCHEMA),
        wait_for=WAIT_FOR,
        wait_for_timeout=20000,
        scan_full_page=False,
        page_timeout=60000,
        delay_before_return_html=1.5,
    )

    start_date = f"{tahun}-01-01"
    end_date = f"{tahun}-12-31"

    hasil: list[dict] = []
    url_halaman_sebelumnya: set[str] = set()
    halaman_maks = None
    selesai = True

    page = 1

    while True:
        url = search_url(keyword, page, start_date, end_date)
        res = await arun_dengan_retry(crawler, url, cfg)

        if not res.success:
            print(f"    [gagal] {tahun} p{page} - {res.error_message}")
            selesai = False
            break

        if "headArticle-count" not in (res.html or ""):
            print(f"    [kosong] {tahun} p{page}: 0 hasil asli "
                  f"(halaman fallback trending, dibuang)")
            break

        items = json.loads(res.extracted_content or "[]")
        if not items:
            break

        if page == 1:
            total = total_hasil_dari_html(res.html)
            if total is not None and items:
                halaman_maks = -(-total // len(items))

        url_sekarang = {bersihkan_url(it.get("url", "")) for it in items}

        if page > 1 and url_sekarang == url_halaman_sebelumnya:
            print(f"    [!] {tahun} p{page} identik dengan p{page-1}")
            break

        url_halaman_sebelumnya = url_sekarang

        for it in items:
            it["keyword"] = keyword
            it["target"] = target
            it["source"] = SOURCE
            hasil.append(it)

        print(f"    [ok] {tahun} p{page}: {len(items)} item")

        if halaman_maks is not None and page >= halaman_maks:
            print(f"    [selesai] {tahun}: udah nyampe halaman_maks ({halaman_maks})")
            break

        if page >= MAX_PAGE_HARD_CAP:
            print(f"    [!] {tahun}: nyampe hard cap ({MAX_PAGE_HARD_CAP}), berhenti paksa")
            break

        await asyncio.sleep(JEDA_ANTAR_HALAMAN)
        page = page + 1

    return hasil, selesai


# ------------------------------------------------------------------ main


async def main():
    daftar = KEYWORDS_TEST if MODE_TEST else KEYWORDS
    tahun_list = list(range(TAHUN_MAX, TAHUN_MIN - 1, -1))
    print(f"sumber: {SOURCE} | {len(daftar)} query | tahun {TAHUN_MIN}-{TAHUN_MAX}\n")

    browser = BrowserConfig(
        headless=True,
        user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"),
    )

    terpilih: list[dict] = []
    if OUT_FILE.exists():
        with open(OUT_FILE, encoding="utf-8") as f:
            terpilih = json.load(f)
        print(f"lanjut dari run sebelumnya: {len(terpilih)} artikel udah ada\n")

    selesai_set: set[str] = set()
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            selesai_set = set(json.load(f))
        print(f"progress sebelumnya: {len(selesai_set)} (keyword, tahun) udah selesai\n")

    seen: set[str] = {it["url"] for it in terpilih}
    gagal_parse: list[str] = []
    mentah = 0

    OUT_DIR.mkdir(exist_ok=True)

    def simpan():
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(terpilih, f, ensure_ascii=False, indent=2)
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(selesai_set), f, ensure_ascii=False, indent=2)

    async with AsyncWebCrawler(config=browser) as crawler:
        for kw, target in daftar:
            print(f"=== [{target}] {kw} ===")
            for tahun in tahun_list:
                progress_key = f"{kw}||{tahun}"
                if progress_key in selesai_set:
                    print(f"    [skip] {tahun}: udah selesai run sebelumnya")
                    continue

                items, selesai = await collect_links_tahun(crawler, kw, target, tahun)
                mentah += len(items)

                for it in items:
                    u = bersihkan_url(it.get("url", ""))
                    if not valid_artikel(u) or u in seen:
                        continue

                    th = tahun_dari_url(u)
                    if th is None:
                        gagal_parse.append(u)
                        continue
                    if th != tahun:
                        continue

                    seen.add(u)
                    it["url"] = u
                    it["tahun"] = th
                    terpilih.append(it)

                if selesai:
                    selesai_set.add(progress_key)

                simpan()

    simpan()

    # --- laporan ----------------------------------------------------------
    print(f"\n{'=' * 55}")
    print(f"mentah   : {mentah}")
    print(f"terpilih : {len(terpilih)}  ->  {OUT_FILE}")

    if gagal_parse:
        print(f"\nURL tanpa tanggal ({len(gagal_parse)}), contoh:")
        for u in gagal_parse[:5]:
            print("   ", u)

    print("\nsebaran per tahun:")
    per_tahun = Counter(it["tahun"] for it in terpilih)
    for th in sorted(per_tahun):
        print(f"  {th}: {per_tahun[th]:4d}  {'#' * (per_tahun[th] // 5)}")

    print("\nsebaran per target:")
    for tgt, n in Counter(it["target"] for it in terpilih).most_common():
        print(f"  {tgt:6s}: {n}")


if __name__ == "__main__":
    asyncio.run(main())
