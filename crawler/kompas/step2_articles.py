"""
Step 2 -- Ambil isi lengkap tiap artikel dari daftar URL hasil step1.

Selector & field diambil dari ARTICLE_SCHEMA di config.py (title/date_raw/
author/content) -- semuanya disimpan mentah, parsing (tanggal, pembersihan
teks) menyusul di step terpisah.

Dijalankan lewat arun_many + MemoryAdaptiveDispatcher (maks 3 sesi paralel)
+ RateLimiter (jeda 2-5s per domain) supaya nggak nembak Kompas kebanyakan
sekaligus.

Resumable: kalau output sudah ada isinya (dari run sebelumnya yang berhenti
di tengah jalan), URL yang udah sukses diambil bakal dilewati, jadi bisa
lanjut tanpa ngulang dari nol. Progres juga disimpan tiap batch (bukan cuma
di akhir) biar nggak hilang semua kalau proses keputus.

Jalankan dari folder ini:
    python step2_articles.py

Input : data/urls.json  (hasil step1_search.py)
Output: data/articles.json
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    JsonCssExtractionStrategy,
    MemoryAdaptiveDispatcher,
    RateLimiter,
)

from config import ARTICLE_SCHEMA, ARTICLE_WAIT_FOR

# ---------------------------------------------------------------- konfigurasi

MAX_SESI_PARALEL = 3       # sesuai rencana: maks 3 request bersamaan
JEDA_ANTAR_REQUEST = (2.0, 5.0)  # detik, per domain (acak dalam rentang ini)
BATCH_SIZE = 200            # URL per panggilan arun_many + checkpoint save
MAX_RETRY = 3
JEDA_RETRY_AWAL = 5         # detik, dilipatgandakan tiap ronde retry

IN_DIR = Path(__file__).parent / "data"
IN_FILE = IN_DIR / "urls.json"
OUT_FILE = IN_DIR / "articles.json"

# ------------------------------------------------------------------- helpers


def muat_urls() -> list[dict]:
    with open(IN_FILE, encoding="utf-8") as f:
        data = json.load(f)
    seen = set()
    unik = []
    for it in data:
        u = it.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        unik.append(it)
    return unik


def muat_progres_lama() -> dict[str, dict]:
    """Kalau ada hasil dari run sebelumnya, pakai buat skip URL yang udah
    sukses -- resume, bukan ngulang dari nol."""
    if not OUT_FILE.exists():
        return {}
    with open(OUT_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return {it["url"]: it for it in data}


def simpan(hasil_map: dict[str, dict]) -> None:
    IN_DIR.mkdir(exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(hasil_map.values()), f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------ crawling


def buat_dispatcher() -> MemoryAdaptiveDispatcher:
    return MemoryAdaptiveDispatcher(
        max_session_permit=MAX_SESI_PARALEL,
        rate_limiter=RateLimiter(base_delay=JEDA_ANTAR_REQUEST),
    )


async def ambil_batch(crawler, cfg, dispatcher, urls: list[str]):
    """Jalankan satu batch, return {url: item_hasil} untuk yang sukses +
    list url yang gagal (buat diretry)."""
    sukses: dict[str, dict] = {}
    gagal: list[str] = []

    hasil = await crawler.arun_many(urls, config=cfg, dispatcher=dispatcher)

    for res in hasil:
        if not res.success:
            gagal.append(res.url)
            continue

        items = json.loads(res.extracted_content or "[]")
        if not items or not (items[0].get("content") or "").strip():
            gagal.append(res.url)
            continue

        sukses[res.url] = items[0]

    return sukses, gagal


async def ambil_dengan_retry(crawler, cfg, dispatcher, urls: list[str]):
    """Retry ronde-ronde dengan backoff untuk URL yang gagal di ronde
    sebelumnya. Return (sukses: dict[url, item], gagal_permanen: list[url])."""
    sukses: dict[str, dict] = {}
    sisa = urls
    jeda = JEDA_RETRY_AWAL

    for percobaan in range(1, MAX_RETRY + 1):
        if not sisa:
            break
        s, g = await ambil_batch(crawler, cfg, dispatcher, sisa)
        sukses.update(s)
        sisa = g
        if sisa and percobaan < MAX_RETRY:
            print(f"    [retry {percobaan}/{MAX_RETRY}] {len(sisa)} url gagal "
                  f"- tunggu {jeda}s")
            await asyncio.sleep(jeda)
            jeda *= 2

    return sukses, sisa


# ------------------------------------------------------------------ main


async def main():
    urls_meta = muat_urls()
    progres_lama = muat_progres_lama()

    meta_by_url = {it["url"]: it for it in urls_meta}
    belum_selesai = [u for u in meta_by_url if u not in progres_lama]

    print(f"total url         : {len(meta_by_url)}")
    print(f"udah selesai      : {len(progres_lama)} (dari run sebelumnya)")
    print(f"perlu diambil     : {len(belum_selesai)}\n")

    hasil_map: dict[str, dict] = dict(progres_lama)
    gagal_permanen: list[str] = []

    if not belum_selesai:
        print("nggak ada yang perlu diambil, selesai.")
        return

    browser = BrowserConfig(
        headless=True,
        user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"),
    )
    cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(ARTICLE_SCHEMA),
        wait_for=ARTICLE_WAIT_FOR,
        wait_for_timeout=20000,
        page_timeout=60000,
    )

    async with AsyncWebCrawler(config=browser) as crawler:
        dispatcher = buat_dispatcher()

        for awal in range(0, len(belum_selesai), BATCH_SIZE):
            batch = belum_selesai[awal:awal + BATCH_SIZE]
            no_batch = awal // BATCH_SIZE + 1
            total_batch = (len(belum_selesai) - 1) // BATCH_SIZE + 1
            print(f"=== batch {no_batch}/{total_batch} ({len(batch)} url) ===")

            sukses, gagal = await ambil_dengan_retry(crawler, cfg, dispatcher, batch)

            for u, extracted in sukses.items():
                item = dict(meta_by_url[u])
                item.update(extracted)
                hasil_map[u] = item

            gagal_permanen.extend(gagal)

            simpan(hasil_map)  # checkpoint tiap batch
            print(f"    sukses: {len(sukses)}  gagal: {len(gagal)}  "
                  f"(total tersimpan: {len(hasil_map)})\n")

    # --- laporan ------------------------------------------------------
    print(f"{'=' * 55}")
    print(f"total tersimpan   : {len(hasil_map)}  ->  {OUT_FILE}")
    if gagal_permanen:
        print(f"\ngagal permanen ({len(gagal_permanen)}), contoh:")
        for u in gagal_permanen[:10]:
            print("   ", u)


if __name__ == "__main__":
    asyncio.run(main())
