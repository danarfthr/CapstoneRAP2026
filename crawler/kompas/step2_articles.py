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
from collections import defaultdict

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
# Semua "limiter" di script ini dikumpulin di sini biar gampang dicari.

MAX_SESI_PARALEL = 1      
JEDA_ANTAR_REQUEST = (4.0, 8.0)  
BATCH_SIZE = 20           
MAX_RETRY = 3              
JEDA_RETRY_AWAL = 5       
WAIT_FOR_TIMEOUT = 10000  
PAGE_TIMEOUT = 30000
URL_TIMEOUT = 120  
TARGET_ARTICLES = 10_000    

# True  = simpan tiap batch (20 URL) DAN tiap tahun selesai
# False = simpan HANYA tiap tahun selesai (jarak antar save bisa lama)
SIMPAN_TIAP_BATCH = True

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
    """Tulis ke file sementara dulu, baru ditukar ke articles.json. Jadi
    kalau proses mati pas lagi nulis, file lama nggak rusak/setengah."""
    IN_DIR.mkdir(exist_ok=True)
    tmp = OUT_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(list(hasil_map.values()), f, ensure_ascii=False, indent=2)
    tmp.replace(OUT_FILE)


# ------------------------------------------------------------------ crawling
MAX_CONSECUTIVE_TIMEOUTS = 5
JEDA_SETELAH_BANYAK_TIMEOUT = 30


def buat_dispatcher() -> MemoryAdaptiveDispatcher:
    return MemoryAdaptiveDispatcher(
        memory_threshold_percent=95.0,
        max_session_permit=MAX_SESI_PARALEL,
        rate_limiter=RateLimiter(
            base_delay=JEDA_ANTAR_REQUEST
        ),
    )


async def ambil_satu(crawler, cfg, dispatcher, url):
    try:
        cfg_stream = cfg.clone(stream=True)

        async with asyncio.timeout(URL_TIMEOUT):
            async for res in await crawler.arun_many(
                [url],
                config=cfg_stream,
                dispatcher=dispatcher
            ):
                if not res.success:
                    return None, False

                try:
                    items = json.loads(
                        res.extracted_content or "[]"
                    )
                except json.JSONDecodeError:
                    return None, False

                if not items or not (
                    items[0].get("content") or ""
                ).strip():
                    return None, False

                return items[0], False

    except TimeoutError:
        print(
            f"⏰ TIMEOUT ({URL_TIMEOUT}s): {url}"
        )
        return None, True

    except Exception as e:
        print(f"✗ ERROR: {url} -> {e}")
        return None, False


async def ambil_batch(crawler, cfg, dispatcher, urls):
    sukses = {}
    gagal = []
    timeout = []

    consecutive_timeouts = 0

    for url in urls:
        print(f"→ mengambil: {url}")

        extracted, is_timeout = await ambil_satu(
            crawler,
            cfg,
            dispatcher,
            url
        )

        if extracted is None:

            if is_timeout:
                timeout.append(url)
                consecutive_timeouts += 1

                print(
                    f"   timeout berturut-turut: "
                    f"{consecutive_timeouts}/"
                    f"{MAX_CONSECUTIVE_TIMEOUTS}"
                )

                # Kalau terlalu banyak timeout berturut-turut,
                # beri waktu sebelum lanjut.
                if (
                    consecutive_timeouts
                    >= MAX_CONSECUTIVE_TIMEOUTS
                ):
                    print(
                        "\n⚠️ Terlalu banyak timeout "
                        "berturut-turut."
                    )

                    print(
                        f"   Menunggu "
                        f"{JEDA_SETELAH_BANYAK_TIMEOUT}s "
                        "sebelum lanjut...\n"
                    )

                    await asyncio.sleep(
                        JEDA_SETELAH_BANYAK_TIMEOUT
                    )

                    consecutive_timeouts = 0

            else:
                gagal.append(url)

                # Error biasa memutus rangkaian timeout.
                consecutive_timeouts = 0

            continue

        # Berhasil → reset counter timeout.
        consecutive_timeouts = 0

        sukses[url] = extracted

        print(f"✓ {url}")

    return sukses, gagal, timeout


async def ambil_dengan_retry(
    crawler,
    cfg,
    dispatcher,
    urls: list[str]
):
    """Retry hanya URL yang gagal biasa.
    URL yang timeout tidak di-retry.
    """

    sukses: dict[str, dict] = {}

    sisa = urls
    timeout_permanen = []

    jeda = JEDA_RETRY_AWAL

    for percobaan in range(
        1,
        MAX_RETRY + 1
    ):

        if not sisa:
            break

        s, g, t = await ambil_batch(
            crawler,
            cfg,
            dispatcher,
            sisa
        )

        sukses.update(s)

        # Timeout langsung dianggap gagal permanen
        # untuk run ini.
        timeout_permanen.extend(t)

        # Hanya error biasa yang masuk retry berikutnya.
        sisa = g

        if sisa and percobaan < MAX_RETRY:

            print(
                f"    [retry {percobaan}/{MAX_RETRY}] "
                f"{len(sisa)} url gagal biasa - "
                f"tunggu {jeda}s"
            )

            await asyncio.sleep(jeda)

            jeda *= 2

    # Gabungkan:
    # - gagal biasa setelah semua retry
    # - timeout
    gagal_permanen = (
        sisa + timeout_permanen
    )

    return sukses, gagal_permanen


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

    # Hitung jumlah artikel yang SUDAH tersimpan untuk setiap tahun
    jumlah_per_tahun = defaultdict(int)

    for item in hasil_map.values():
        tahun = item.get("tahun")
        if tahun is not None:
            jumlah_per_tahun[int(tahun)] += 1

    # Target akhir dibagi rata ke semua tahun.
    tahun_target = sorted(per_tahun.keys()) if 'per_tahun' in locals() else sorted(
        {it.get("tahun") for it in urls_meta if it.get("tahun") is not None}
    )

    TARGET_PER_TAHUN = TARGET_ARTICLES // len(tahun_target)

    print("\nJumlah artikel yang sudah ada:")
    for tahun in tahun_target:
        print(f"  {tahun}: {jumlah_per_tahun[tahun]:,}")

    print(f"\nTarget per tahun: {TARGET_PER_TAHUN:,}")

    if len(hasil_map) >= TARGET_ARTICLES:
        print(
            f"Target {TARGET_ARTICLES:,} artikel sudah tercapai "
            f"({len(hasil_map):,} tersimpan)."
        )
        simpan(hasil_map)
        return

    if not belum_selesai:
        print("nggak ada yang perlu diambil, selesai.")
        return

     # ---------------------------------------------------------------
    # Kelompokkan URL yang belum selesai berdasarkan tahun
    # ---------------------------------------------------------------
    per_tahun: dict[int, list[str]] = defaultdict(list)

    for u in belum_selesai:
        tahun = meta_by_url[u].get("tahun") or 0

    if tahun in TAHUN_TARGET:
        per_tahun[tahun].append(u)

    # ---------------------------------------------------------------
    # Hitung jumlah artikel yang SUDAH tersimpan per tahun
    # ---------------------------------------------------------------
    jumlah_per_tahun: dict[int, int] = defaultdict(int)

    for item in hasil_map.values():
        tahun = item.get("tahun")
        if tahun is not None:
            jumlah_per_tahun[int(tahun)] += 1

    # ---------------------------------------------------------------
    # Target artikel per tahun
    # ---------------------------------------------------------------
    TAHUN_TARGET = list(range(2021, 2027))

    semua_tahun = TAHUN_TARGET
    semua_tahun = sorted(
        set(per_tahun.keys()) | set(jumlah_per_tahun.keys())
    )

    TARGET_PER_TAHUN = TARGET_ARTICLES // len(semua_tahun)

    print("\n===== DISTRIBUSI ARTIKEL =====")
    print(f"Target total       : {TARGET_ARTICLES:,}")
    print(f"Jumlah tahun       : {len(semua_tahun)}")
    print(f"Target per tahun   : {TARGET_PER_TAHUN:,}")

    for tahun in semua_tahun:
        sudah = jumlah_per_tahun[tahun]
        kurang = max(0, TARGET_PER_TAHUN - sudah)

        print(
            f"  {tahun}: "
            f"{sudah:,} sudah ada, "
            f"{kurang:,} masih dibutuhkan"
        )

    print("==============================\n")

    browser = BrowserConfig(
        headless=True,
        text_mode=True,
        user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"),
    )
    cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(ARTICLE_SCHEMA),
        wait_for=ARTICLE_WAIT_FOR,
        wait_for_timeout=WAIT_FOR_TIMEOUT,
        page_timeout=PAGE_TIMEOUT,
    )

    async with AsyncWebCrawler(config=browser) as crawler:
        dispatcher = buat_dispatcher()

        for tahun in sorted(per_tahun, reverse=True):

            # Berapa artikel tahun ini yang sudah ada?
            jumlah_tahun = jumlah_per_tahun[tahun]

            # Berapa artikel tahun ini yang masih diperlukan?
            masih_dibutuhkan = max(
                0,
                TARGET_PER_TAHUN - jumlah_tahun
            )

            # Tahun ini sudah memenuhi kuota
            if masih_dibutuhkan <= 0:
                print(
                    f"\n✓ {tahun} sudah mencapai target "
                    f"({jumlah_tahun:,}/{TARGET_PER_TAHUN:,}), skip."
                )
                continue

            # Ambil hanya URL sebanyak yang masih diperlukan.
            urls_tahun = per_tahun[tahun][:masih_dibutuhkan]

            total_batch = (
                (len(urls_tahun) - 1) // BATCH_SIZE + 1
            )

            print(
                f"\n{'=' * 60}\n"
                f"=== MULAI TAHUN {tahun} ===\n"
                f"Sudah ada : {jumlah_tahun:,}\n"
                f"Target    : {TARGET_PER_TAHUN:,}\n"
                f"Kurang    : {masih_dibutuhkan:,}\n"
                f"URL siap  : {len(urls_tahun):,}\n"
                f"{'=' * 60}"
            )

            total_batch = (len(urls_tahun) - 1) // BATCH_SIZE + 1
            print(
                f"\n{'=' * 60}\n"
                f"=== MULAI TAHUN {tahun} ===\n"
                f"Sudah ada : {jumlah_tahun:,}\n"
                f"Target    : {TARGET_PER_TAHUN:,}\n"
                f"Kurang    : {masih_dibutuhkan:,}\n"
                f"URL siap  : {len(urls_tahun):,}\n"
                f"{'=' * 60}"
            )

            sukses_tahun = 0
            gagal_tahun = 0

            for awal in range(0, len(urls_tahun), BATCH_SIZE):
                batch = urls_tahun[awal:awal + BATCH_SIZE]
                no_batch = awal // BATCH_SIZE + 1
                print(f"=== {tahun} batch {no_batch}/{total_batch} "
                      f"({len(batch)} url) ===")

                sukses, gagal = await ambil_dengan_retry(
                    crawler, cfg, dispatcher, batch)

                for u, extracted in sukses.items():
                    item = dict(meta_by_url[u])
                    item.update(extracted)
                    hasil_map[u] = item

                gagal_permanen.extend(gagal)
                sukses_tahun += len(sukses)
                gagal_tahun += len(gagal)

                if SIMPAN_TIAP_BATCH:
                    simpan(hasil_map)

                print(f"    sukses: {len(sukses)}  gagal: {len(gagal)}  "
                      f"(total tersimpan: {len(hasil_map)})\n")

                # Update jumlah artikel tahun ini
                jumlah_per_tahun[tahun] += len(sukses)

                # Update target progress
                jumlah_tahun = jumlah_per_tahun[tahun]
                masih_dibutuhkan = max(
                    0,
                    TARGET_PER_TAHUN - jumlah_tahun
                )

                # Global safety cutoff
                if len(hasil_map) >= TARGET_ARTICLES:
                    print(
                        f"🎯 TARGET TOTAL TERCAPAI: "
                        f"{len(hasil_map):,}/{TARGET_ARTICLES:,}"
                    )
                    simpan(hasil_map)
                    return

                # Tahun ini sudah memenuhi kuota
                if masih_dibutuhkan <= 0:
                    print(
                        f"✓ TARGET TAHUN {tahun} TERCAPAI: "
                        f"{jumlah_tahun:,}/{TARGET_PER_TAHUN:,}"
                    )
                    break

            # simpan tiap satu tahun selesai
            simpan(hasil_map)
            print(f"##### tahun {tahun} selesai: sukses {sukses_tahun}, "
                  f"gagal {gagal_tahun} -> disimpan ke {OUT_FILE.name} #####\n")

    # --- laporan ------------------------------------------------------
    print(f"{'=' * 55}")
    print(f"total tersimpan   : {len(hasil_map)}  ->  {OUT_FILE}")
    if gagal_permanen:
        print(f"\ngagal permanen ({len(gagal_permanen)}), contoh:")
        for u in gagal_permanen[:10]:
            print("   ", u)
        print("\n(URL yang gagal nggak disimpan, jadi otomatis dicoba lagi "
              "kalau script dijalankan ulang)")


if __name__ == "__main__":
    asyncio.run(main())