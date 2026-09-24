# Proyek Capstone Kelas RAP | Analisis Sentimen & Stance PLTU vs PLTN

**Mata Kuliah:** PACS262525 | Proyek Capstone Kelas RAP  
**Dosen:** Rifki Afina Putri, S.T., M.S., Ph.D.  
**Program Studi:** Ilmu Komputer, FMIPA, Universitas Gadjah Mada

<!-- ## Daftar Isi

- [Tim](#tim)
- [Ringkasan Proyek](#ringkasan-proyek)
- [Produk yang Dikembangkan](#produk-yang-dikembangkan)
- [Metodologi](#metodologi)
- [Sumber Data](#sumber-data)
- [Struktur Tim & Pembagian Peran](#struktur-tim--pembagian-peran)
- [Struktur Direktori](#struktur-direktori)
- [Cara Menjalankan Crawler](#cara-menjalankan-crawler)
- [Dokumen & Tautan Penting](#dokumen--tautan-terkait)
- [Status Saat Ini (update 16 September 2026)](#status-saat-ini) -->

## Tim

- **Adzrha Auryn Alius** — 24/533582/PA/22594
- **Gilbert Nathaniel** — 24/533877/PA/22623
- **Danar Fathurahman** — 24/538200/PA/22828
- **Jessy Marcia Anabel** — 24/538431/PA/22846
- **Mikail Achmad** — 24/542370/PA/23026
- **Evan Razzan Adytaputra** — 24/545257/PA/23166

## Ringkasan Proyek

Indonesia saat ini berada dalam masa transisi energi: sekitar 55-60% pasokan listrik nasional masih bergantung pada PLTU berbasis batu bara, sementara pemerintah mulai merintis PLTN sebagai opsi energi rendah karbon menuju target Net Zero Emission 2060, dengan target operasi komersial PLTN pertama pada 2032.

Pergeseran ini memunculkan polarisasi opini publik, baik pada kolom komentar YouTube maupun pada framing penulis artikel berita terhadap penerimaan PLTU dan PLTN. Sulit menemukan gambaran umum yang komprehensif dari opini yang tersebar dan terpolarisasi ini.

**Tujuan proyek:** mengidentifikasi dan membandingkan kecenderungan sentimen publik Indonesia terhadap PLTU dan PLTN, berdasarkan:

1. Opini pada kolom komentar video YouTube (pro, kontra, atau netral), dan
2. Posisi/stance penulis pada artikel berita nasional (mendukung, menolak, atau netral).

Hasil analisis ditujukan sebagai bahan pertimbangan bagi pemegang kebijakan serta peneliti dalam memahami penerimaan masyarakat terhadap arah transisi energi Indonesia.

## Produk yang Dikembangkan

Situs web dashboard analisis sentimen interaktif dengan fitur:

- **Pengumpulan & Analisis Data**: crawling artikel berita dan komentar YouTube, diproses dengan NLP/LLM untuk sentiment analysis dan stance detection.
- **Dashboard Analisis Sentimen**: visualisasi distribusi sentimen positif/netral/negatif (komentar YouTube) dan posisi mendukung/netral/menolak (artikel berita), beserta topik-topik pokok yang banyak dibahas.
- **Filter Topik & Periode Waktu**: pengguna dapat memilih objek analisis (PLTU atau PLTN) serta rentang waktu publish komentar/artikel.
- **Perbandingan PLTU vs PLTN**: perbandingan hasil sentimen dan frame penulis antar kedua jenis pembangkit.

## Metodologi

Proyek ini menggunakan dua pendekatan analisis berbeda sesuai karakteristik masing-masing sumber teks:

### Komentar YouTube

- **Sentiment analysis**: komentar bersifat singkat, informal, dan sarat opini personal sehingga cocok dianalisis sentimennya secara langsung (label: `positive` / `negative` / `neutral`) dengan model yang relatif ringan secara komputasi.
- **Stance detection**: dilakukan juga pada komentar (label: `oppose` / `support` / `neutral`), dengan hasil sentiment analysis dipakai sebagai fitur penunjang.

### Artikel Berita

- Artikel berita dominan netral dan objektif, sehingga sentiment analysis langsung kurang efektif untuk teks yang panjang seperti ini.
- Sebagai gantinya, tim melakukan **ekstraksi aktor** terlebih dahulu, lalu **stance detection per aktor** melalui kutipan dan konteks tindakan aktor dalam berita.
- Output: `aktor`, `stance` (`oppose` / `support` / `neutral`), dan `bukti` (potongan teks pendukung agar hasil bisa ditelusuri ke isi artikel asli).

**Arsitektur pipeline:** Crawling → Preprocessing/Feature Engineering → Analisis Sentimen/Stance → Dashboard.
Flowchart lengkap tersedia di tautan Miro pada bagian [Dokumen & Tautan Terkait](#dokumen--tautan-terkait).

## Sumber Data

Target awal proposal: **10 video YouTube terpilih** (komentar) + **50 artikel berita** dari 3 portal berita nasional.

| Sumber        | Jenis            | Lokasi Kode                                          | Status                                           |
| ------------- | ---------------- | ---------------------------------------------------- | ------------------------------------------------ |
| CNN Indonesia | Artikel berita   | [`crawler/cnnindonesia/`](crawler/cnnindonesia/)     | Aktif, lihat [Status Saat Ini](#status-saat-ini) |
| Detik         | Artikel berita   | [`crawler/detik/`](crawler/detik/)                   | Siap jalan                                       |
| Kompas        | Artikel berita   | [`crawler/kompas/`](crawler/kompas/)                 | Aktif, lihat [Status Saat Ini](#status-saat-ini) |
| YouTube       | Video + komentar | [`crawler/youtubecomment/`](crawler/youtubecomment/) | Aktif, lihat [Status Saat Ini](#status-saat-ini) |

Semua sumber menggunakan kata kunci seputar PLTN, PLTU, energi nuklir, dan transisi energi Indonesia agar cakupan topik konsisten antar sumber.

## Struktur Tim & Pembagian Peran

Pelaksanaan proyek dibagi menjadi dua subtim berdasarkan objek riset, masing-masing dengan PIC yang memahami karakteristik data dan kebutuhan sistemnya, namun pengembangan tetap terintegrasi.

| Subtim   | Anggota                                       |
| -------- | --------------------------------------------- |
| **PLTN** | Danar Fathurahman, Mikail Achmad, Evan Razzan |
| **PLTU** | Gilbert Nathaniel, Jessy Marcia, Adzrha Auryn |

**Fase 1: Pengembangan Data & Model** (sebelum UTS, Agustus–Oktober):

| Peran           | Tanggung Jawab                                          | PLTN        | PLTU            |
| --------------- | ------------------------------------------------------- | ----------- | --------------- |
| Data Engineer   | Data pipeline, crawling, pengolahan awal, basis data    | Danar, Evan | Jessy, Adzrha   |
| NLP Engineer    | Sistem & evaluasi sentiment analysis / stance detection | Miko, Evan  | Gilbert, Adzrha |
| Project Manager | Koordinasi & pemantauan target per subtim               | Danar, Miko | Gilbert         |

**Fase 2: Pengembangan & Integrasi Sistem** (setelah UTS, Oktober–November): Front-end Developer, Back-end Developer (seluruh anggota), Project Manager (Danar dan Miko untuk PLTN; Gilbert untuk PLTU) untuk integrasi dashboard.

## Struktur Direktori

```
CapstoneRAP2026/
├── README.md
└── crawler/
    ├── query_config.py   # Shared config: kata kunci PLTN/PLTU/UMUM + rentang tahun (dipakai 4 crawler)
    ├── merge_articles.py # Gabungkan artikel CNN+Detik+Kompas -> data/articles_merged.json/.csv
    ├── cnnindonesia/     # Scraper artikel CNN Indonesia
    ├── detik/            # Scraper artikel Detik (production-grade)
    ├── kompas/           # Scraper artikel Kompas (2 tahap: cari URL, lalu ambil isi)
    └── youtubecomment/   # Scraper video + komentar YouTube
```

Kata kunci pencarian & rentang tahun (`START_YEAR`/`END_YEAR`) untuk keempat crawler didefinisikan satu kali di [`crawler/query_config.py`](crawler/query_config.py), supaya keempatnya konsisten menyasar topik PLTN/PLTU/UMUM yang sama dan tidak lagi terpisah-pisah.

Artikel berita dari CNN, Detik, dan Kompas bisa digabung jadi satu file dengan skema kolom seragam (`source`, `url`, `title`, `date`, `keyword`, `target`, `author`, `tags`, `content`) lewat [`crawler/merge_articles.py`](crawler/merge_articles.py) — baca langsung dari cache tiap sumber jadi aman dijalankan ulang kapan saja, termasuk saat crawler masih jalan. YouTube tidak ikut digabung karena unit datanya beda (komentar per video, bukan artikel); outputnya tetap terpisah di `crawler/youtubecomment/data/`.

### [`crawler/cnnindonesia/`](crawler/cnnindonesia/)

**[`scrape_cnn.py`](crawler/cnnindonesia/scrape_cnn.py)** — scraper satu file berbasis pencarian CNN (`?query=...&page=N`):
- Paginasi otomatis sampai hasil habis (dibatasi `MAX_PAGES_PER_KEYWORD` sebagai jaring pengaman).
- **Resumable**: cache JSONL ([`cnn_energy_cache.jsonl`](crawler/cnnindonesia/cnn_energy_cache.jsonl)) menyimpan tiap artikel begitu berhasil, sehingga proses bisa dihentikan dan dilanjutkan kapan saja tanpa scraping ulang.
- Retry + backoff eksponensial untuk kegagalan jaringan/anti-bot.
- **Filter rentang tahun** (`START_DATE`/`END_DATE`, dari `crawler/query_config.py`) — artikel di luar rentang dilewati sebelum halamannya dibuka (tahun ditebak dari ID artikel di URL), lalu dicek ulang dengan tanggal asli.
- Output akhir: [`hasil_scraping_cnn_attempt2.json`](crawler/cnnindonesia/hasil_scraping_cnn_attempt2.json) & `.csv`, tiap artikel berisi `url`, `judul`, `tanggal`, `isi`, `kata_kunci`, `target` (label `PLTN`/`PLTU`/`UMUM` untuk anotasi sentimen).

### [`crawler/detik/`](crawler/detik/)

Scraper modular production-grade dengan pemisahan tanggung jawab per file:

| File                                       | Fungsi                                                                                                                     |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| [`config.py`](crawler/detik/config.py)     | Konfigurasi terpusat: kata kunci & rentang tahun (dari `crawler/query_config.py`), limit halaman, user-agent pool, path output |
| [`crawler.py`](crawler/detik/crawler.py)   | Fetcher async (aiohttp) dengan rotasi User-Agent, retry, dan cooldown otomatis 5 menit saat terdeteksi anti-bot/Cloudflare |
| [`parser.py`](crawler/detik/parser.py)     | Ekstraksi judul/tanggal/isi/tag, filter artikel berdasarkan kemunculan kata kunci (regex word-boundary) & rentang tahun    |
| [`storage.py`](crawler/detik/storage.py)   | Cache JSONL append-only, thread-safe, resumable                                                                            |
| [`exporter.py`](crawler/detik/exporter.py) | Konversi cache JSONL → CSV & JSON array (streaming, hemat memori)                                                          |
| [`main.py`](crawler/detik/main.py)         | Entry point: jalankan crawler lalu ekspor otomatis                                                                         |

### [`crawler/kompas/`](crawler/kompas/)

Scraper dua tahap berbasis `crawl4ai`, resumable di tiap tahap:

| File                                             | Fungsi                                                                                                    |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| [`config.py`](crawler/kompas/config.py)          | Selector CSS pencarian & artikel, builder URL pencarian dengan filter tanggal                              |
| [`step1_search.py`](crawler/kompas/step1_search.py) | Kumpulkan judul + URL artikel per kata kunci per tahun (dari `crawler/query_config.py`) → `data/urls.json` |
| [`step2_articles.py`](crawler/kompas/step2_articles.py) | Ambil isi lengkap tiap URL hasil step 1 → `data/articles.json`                                          |

### [`crawler/youtubecomment/`](crawler/youtubecomment/)

| File                                                          | Fungsi                                                                                                                                                                                                                             |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`config.py`](crawler/youtubecomment/config.py)               | Kata kunci pencarian (dari `crawler/query_config.py`), limit video/komentar per kata kunci, path output                                                                                                                            |
| [`scraper.py`](crawler/youtubecomment/scraper.py)             | `YouTubeSearcher` (via `yt-dlp`, pencarian `ytsearchN:`) untuk menemukan video, `CommentScraper` (via `youtube-comment-downloader`) untuk mengambil komentar; video di luar rentang tahun dilewati; state per-video disimpan agar video yang sudah selesai tidak diulang |
| [`exporter.py`](crawler/youtubecomment/exporter.py)           | Ekspor cache JSONL komentar → CSV & JSON array                                                                                                                                                                                     |
| [`main.py`](crawler/youtubecomment/main.py)                   | Entry point pipeline lengkap                                                                                                                                                                                                       |
| [`requirements.txt`](crawler/youtubecomment/requirements.txt) | `yt-dlp`, `youtube-comment-downloader`, `dateparser`                                                                                                                                                                               |

## Cara Menjalankan Crawler

```bash
# CNN Indonesia
cd crawler/cnnindonesia
python scrape_cnn.py

# Detik
cd crawler/detik
python main.py

# Kompas
cd crawler/kompas
python step1_search.py    # tahap 1: kumpulkan URL
python step2_articles.py  # tahap 2: scrape isi artikel

# YouTube (video + komentar)
cd crawler/youtubecomment
pip install -r requirements.txt
python main.py

# Gabungkan artikel CNN+Detik+Kompas jadi satu file (bisa dijalankan ulang kapan saja)
cd crawler
python merge_articles.py
```

## Dokumen & Tautan Penting

- **Proposal Project Capstone:** https://docs.google.com/document/d/1G4KeM_Ei9nYRxofEf8R7oo43xJtqxHpURBiQHXzrsYw/edit?usp=sharing_
- **Timeline / Gantt Chart (Google Sheets):** https://docs.google.com/spreadsheets/d/1uUyMNYzIS8GGlzlv8sgwmwW2dDUcrbSpzC-fXN0Dld4/edit?usp=sharing
- **Flowchart Arsitektur Sistem (Miro):** https://miro.com/app/board/uXjVHoqqU-U=/

## Status Saat Ini (update 23 September 2026)

- Kata kunci & rentang tahun crawling (2021-2026) sekarang disatukan di [`crawler/query_config.py`](crawler/query_config.py) dan dipakai keempat crawler, menggantikan daftar kata kunci yang sebelumnya berbeda-beda per sumber.
- **CNN Indonesia**: satu implementasi (`scrape_cnn.py`) setelah menggabungkan pipeline eksperimen `discovery.py`/`crawler.py` yang sebelumnya tidak pernah benar-benar jalan. 693 artikel tersimpan dari run sebelumnya (rentang tahun 2019-2026); crawling ulang dengan rentang 2021-2026 & kata kunci baru sedang berjalan.
- **Kompas**: dua-tahap (`step1_search.py` lalu `step2_articles.py`), sudah punya data hasil run sebelumnya (`data/urls.json`, `data/articles.json`); crawling ulang dengan rentang 2021-2026 sedang berjalan.
- **Detik**: kode scraper siap (fitur anti-bot & resumable cache paling lengkap di antara semua crawler); filter rentang tahun (sebelumnya cuma placeholder di config) sekarang benar-benar diterapkan di `parser.py`.
- **YouTube**: ±4.100 komentar tersimpan di cache dari run sebelumnya; sekarang video di luar rentang tahun 2021-2026 dilewati sebelum komentarnya di-scrape.
- Tahap saat ini masih **Fase 1 (pengumpulan & pengolahan data)**, sedangkan fase seperti preprocessing, feature engineering, dan model NLP/LLM untuk sentiment analysis & stance detection belum dimulai.

> Tolong untuk status selalu diupdate setiap minggu ya ges ya :)
