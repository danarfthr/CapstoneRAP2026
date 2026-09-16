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

- **Adzraha Auryn Alius** — 24/533582/PA/22594
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
| Detik         | Artikel berita   | [`crawler/detik/`](crawler/detik/)                   | Siap jalan, belum dieksekusi                     |
| Kompas        | Artikel berita   | [`crawler/kompas/`](crawler/kompas/)                 | Belum diimplementasikan                          |
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
    ├── cnnindonesia/   # Scraper artikel CNN Indonesia (2 implementasi)
    ├── detik/          # Scraper artikel Detik (production-grade)
    ├── kompas/         # Placeholder, belum diimplementasikan
    └── youtubecomment/ # Scraper video + komentar YouTube
```

### [`crawler/cnnindonesia/`](crawler/cnnindonesia/)

Berisi **dua implementasi berbeda** yang saat ini hidup berdampingan:

1. **[`scrape_cnn.py`](crawler/cnnindonesia/scrape_cnn.py)** — scraper satu file berbasis pencarian CNN (`?query=...&page=N`):
   - Paginasi otomatis sampai hasil habis (dibatasi `MAX_PAGES_PER_KEYWORD` sebagai jaring pengaman).
   - **Resumable**: cache JSONL ([`cnn_energy_cache.jsonl`](crawler/cnnindonesia/cnn_energy_cache.jsonl)) menyimpan tiap artikel begitu berhasil, sehingga proses bisa dihentikan dan dilanjutkan kapan saja tanpa scraping ulang.
   - Retry + backoff eksponensial untuk kegagalan jaringan/anti-bot.
   - **Filter rentang tahun** (`START_DATE` / `END_DATE` di bagian konfigurasi) — artikel di luar rentang dilewati sebelum halamannya dibuka (tahun ditebak dari ID artikel di URL), lalu dicek ulang dengan tanggal asli.
   - Output akhir: [`hasil_scraping_cnn_attempt2.json`](crawler/cnnindonesia/hasil_scraping_cnn_attempt2.json) & `.csv`, tiap artikel berisi `url`, `judul`, `tanggal`, `isi`, `kata_kunci`, `target` (label `PLTN`/`PLTU`/`UMUM` untuk anotasi sentimen).

2. **[`discovery.py`](crawler/cnnindonesia/discovery.py) + [`crawler.py`](crawler/cnnindonesia/crawler.py)** — pipeline dua tahap berbasis markdown:
   - `discovery.py` mencari URL artikel per kata kunci lewat hasil pencarian CNN (markdown, bukan HTML), menyimpan daftar URL unik ke [`data/discovered_urls.json`](crawler/cnnindonesia/data/discovered_urls.json).
   - `crawler.py` membuka tiap URL yang ditemukan, membersihkan markdown (buang blok "Lihat Juga", iklan, elemen UI) dengan `PruningContentFilter`, lalu menyimpan ke [`data/articles.json`](crawler/cnnindonesia/data/articles.json).

### [`crawler/detik/`](crawler/detik/)

Scraper modular production-grade dengan pemisahan tanggung jawab per file:

| File                                       | Fungsi                                                                                                                     |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| [`config.py`](crawler/detik/config.py)     | Konfigurasi terpusat: kata kunci, rentang tahun (`start_date`/`end_date`), limit halaman, user-agent pool, path output     |
| [`crawler.py`](crawler/detik/crawler.py)   | Fetcher async (aiohttp) dengan rotasi User-Agent, retry, dan cooldown otomatis 5 menit saat terdeteksi anti-bot/Cloudflare |
| [`parser.py`](crawler/detik/parser.py)     | Ekstraksi judul/tanggal/isi/tag, filter artikel berdasarkan kemunculan kata kunci (regex word-boundary)                    |
| [`storage.py`](crawler/detik/storage.py)   | Cache JSONL append-only, thread-safe, resumable                                                                            |
| [`exporter.py`](crawler/detik/exporter.py) | Konversi cache JSONL → CSV & JSON array (streaming, hemat memori)                                                          |
| [`main.py`](crawler/detik/main.py)         | Entry point: jalankan crawler lalu ekspor otomatis                                                                         |

### [`crawler/kompas/`](crawler/kompas/)

Belum ada implementasi scraper.

### [`crawler/youtubecomment/`](crawler/youtubecomment/)

| File                                                          | Fungsi                                                                                                                                                                                                                             |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`config.py`](crawler/youtubecomment/config.py)               | Kata kunci pencarian (selaras dengan `crawler/detik`), limit video/komentar per kata kunci, path output                                                                                                                            |
| [`scraper.py`](crawler/youtubecomment/scraper.py)             | `YouTubeSearcher` (via `yt-dlp`, pencarian `ytsearchN:`) untuk menemukan video, `CommentScraper` (via `youtube-comment-downloader`) untuk mengambil komentar; state per-video disimpan agar video yang sudah selesai tidak diulang |
| [`exporter.py`](crawler/youtubecomment/exporter.py)           | Ekspor cache JSONL komentar → CSV & JSON array                                                                                                                                                                                     |
| [`main.py`](crawler/youtubecomment/main.py)                   | Entry point pipeline lengkap                                                                                                                                                                                                       |
| [`requirements.txt`](crawler/youtubecomment/requirements.txt) | `yt-dlp`, `youtube-comment-downloader`, `dateparser`                                                                                                                                                                               |

## Cara Menjalankan Crawler

```bash
# CNN Indonesia (versi resumable, satu file)
cd crawler/cnnindonesia
python scrape_cnn.py

# CNN Indonesia (versi discovery + markdown)
cd crawler/cnnindonesia
python discovery.py   # tahap 1: kumpulkan URL
python crawler.py     # tahap 2: scrape isi artikel

# Detik
cd crawler/detik
python main.py

# YouTube (video + komentar)
cd crawler/youtubecomment
pip install -r requirements.txt
python main.py
```

## Dokumen & Tautan Penting

- **Proposal Project Capstone:** https://docs.google.com/document/d/1G4KeM_Ei9nYRxofEf8R7oo43xJtqxHpURBiQHXzrsYw/edit?usp=sharing_
- **Timeline / Gantt Chart (Google Sheets):** https://docs.google.com/spreadsheets/d/1uUyMNYzIS8GGlzlv8sgwmwW2dDUcrbSpzC-fXN0Dld4/edit?usp=sharing
- **Flowchart Arsitektur Sistem (Miro):** https://miro.com/app/board/uXjVHoqqU-U=/

## Status Saat Ini (update 16 September 2026)

- **CNN Indonesia**: 693 artikel tersimpan (rentang tahun 2019-2026, hasil filter dari 834 baris cache setelah pembersihan duplikat & artikel di bawah 2019). Kata kunci di bidang PLTN yang dominan adalah `PLTN`, `energi nuklir`, dan `rencana pembangunan PLTN`, sedangkan kata kunci di bidang PLTU (`PLTU`, `tolak PLTU`, `emisi PLTU`, dll.) belum menghasilkan artikel yang memadai. Perlu investigasi lebih lanjut apakah karena keterbatasan mesin pencari CNN atau memang minim liputan dengan frasa tersebut.
- **YouTube**: 8 video sudah discrape, ±4.100 komentar tersimpan di cache.
- **Detik**: kode scraper sudah siap (fitur anti-bot & resumable cache paling lengkap di antara semua crawler), namun belum pernah dieksekusi di lingkungan ini.
- **Kompas**: belum diimplementasikan sama sekali.
- Tahap saat ini masih **Fase 1 (pengumpulan & pengolahan data)**, sedangkan fase seperti preprocessing, feature engineering, dan model NLP/LLM untuk sentiment analysis & stance detection belum dimulai.

> Tolong untuk status selalu diupdate setiap minggu ya ges ya :)
