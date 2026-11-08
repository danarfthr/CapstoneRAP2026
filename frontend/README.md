# SentimentLens — Frontend & Dashboard

Aplikasi web (Next.js) untuk menampilkan analisis sentimen & stance publik terhadap PLTU dan PLTN.
Landing page, pop-up filter, layar loading, dan dashboard semuanya ada di **satu aplikasi** ini.

## Menjalankan

```bash
cd frontend
npm install
npm run dev
```

Buka <http://localhost:3000>.

## Alur halaman

```
[1] LANDING  ──klik "Start Analysis"──▶  [2] POP-UP  ──"Apply Selection"──▶  [3] LOADING  ──100%──▶  [4] DASHBOARD  ──"View Data"──▶  [5] DATA VIEW
     /                                     (di atas /)                         /loading?…               /dashboard?…                    /data?…
```

Filter yang dipilih di pop-up (PLTU/PLTN, platform, rentang waktu) dibawa lewat **query string**,
misalnya `/dashboard?types=pltu&platforms=youtube&range=3m`. Jadi dashboard bisa di-refresh atau
dibagikan tanpa kehilangan filter. Kalau `types` kosong, PLTU dan PLTN dua-duanya ditampilkan.

## Letak kode

| Tahap | Route (URL) | File route (`src/app/`) | Komponen & style (`src/components/`) |
| --- | --- | --- | --- |
| **[1] Landing** | `/` | `page.js` | `landing/LandingPage.js`, `landing/landing.module.css` |
| **[2] Pop-up** | (modal di `/`) | — | `popup/AnalysisFilterModal.js`, `popup/popup.module.css` |
| **[3] Loading** | `/loading` | `loading/page.js` | `loading/LoadingScreen.js`, `loading/loading.module.css` |
| **[4] Dashboard** | `/dashboard` | `dashboard/page.js` | `dashboard/*` (lihat di bawah) |
| **[5] Data View** | `/data` | `data/page.js` | `dataview/*` (tabel YouTube & News + Export CSV) |
| API data | `/api/dashboard`, `/api/dataset` | `api/dashboard/route.js`, `api/dataset/route.js` | — |

```
src/
├── app/                              ← ROUTE: tiap folder = satu URL. File di sini dibuat setipis mungkin.
│   ├── layout.js                     ← root layout: font Inter, metadata, import globals.css
│   ├── globals.css                   ← design token (warna, spasi, font) + reset, dipakai SEMUA halaman
│   ├── page.js                       ← [1]+[2] "/"          → <LandingPage />
│   ├── loading/page.js               ← [3]     "/loading"   → <LoadingScreen />
│   ├── dashboard/page.js             ← [4]     "/dashboard" → <DashboardPage />
│   ├── data/page.js                  ← [5]     "/data"      → <DataViewPage />
│   ├── api/dashboard/route.js        ← GET /api/dashboard (masih data dummy)
│   └── api/dataset/route.js          ← GET /api/dataset   (data per baris untuk Data View, masih dummy)
│
├── components/                       ← TAMPILAN: dikelompokkan per tahap alur
│   ├── layout/
│   │   ├── PageShell.js              ← kerangka bersama landing & loading: background, navbar, footer
│   │   └── layout.module.css
│   ├── landing/
│   │   ├── LandingPage.js            ← [1] hero + tombol "Start Analysis", membuka pop-up
│   │   └── landing.module.css
│   ├── popup/
│   │   ├── AnalysisFilterModal.js    ← [2] pilih PLTU/PLTN, platform, tanggal, quick select
│   │   └── popup.module.css
│   ├── loading/
│   │   ├── LoadingScreen.js          ← [3] progress bar, lalu redirect ke dashboard
│   │   └── loading.module.css
│   ├── dashboard/
│       ├── DashboardPage.js          ← [4] ambil data API, atur state loading/error, render section
│       ├── DashboardHeader.js        ← header sticky: logo, tombol PLTU/PLTN, tombol aksi (dipakai juga di Data View)
│       ├── AnalysisSection.js        ← satu blok lengkap per jenis pembangkit (dipakai PLTU & PLTN)
│       ├── Card.js                   ← <Card> & <Badge>, elemen dasar semua kartu
│       ├── DistributionCard.js       ← bar Sentiment Distribution / Stance Distribution
│       ├── RankedListCard.js         ← Top Discussion Topics / Top Actor (dropdown Top Negative…)
│       ├── StanceSources.js          ← porsi & breakdown per sumber (YouTube/News)
│       ├── TopActorDetail.js         ← daftar berita per aktor + stance
│       ├── MostDiscussedTopics.js    ← tabel topik spesifik + visibility
│       ├── SentimentStanceBreakdown.js ← tabel komentar/berita + pagination
│       └── dashboard.module.css
│   └── dataview/
│       ├── DataViewPage.js           ← [5] ambil /api/dataset, state filter per section, Export CSV
│       ├── DatasetSection.js         ← judul + total corpus + bar filter + tabel per platform
│       ├── DatasetTable.js           ← kartu tabel + jumlah entri + pagination
│       └── dataview.module.css
│
└── lib/
    ├── analysisFilter.js             ← opsi filter + konversi filter ⇄ query string
    ├── dataset.js                    ← filter baris (search/sentimen/stance) + Export CSV untuk Data View
    └── useSectionNav.js              ← tombol PLTU/PLTN di header: scroll + tanda aktif
```

## Aturan supaya tetap rapi

- **`src/app/` hanya untuk route.** Isi tampilan ditaruh di `src/components/<tahap>/`.
- **Style pakai CSS Modules** (`*.module.css`) per tahap, jadi nama class tidak bentrok antarhalaman.
- **Warna, spasi, dan font diambil dari token** di `src/app/globals.css` (`var(--color-…)`).
  Warna sentimen/stance juga ada di sana (`--color-negative`, `--color-positive`, dst.).
- **Opsi filter cuma didefinisikan di `src/lib/analysisFilter.js`.** Kalau mau menambah pilihan
  (misalnya platform baru), cukup ubah di file itu; pop-up dan dashboard ikut menyesuaikan.
- Data dari backend: ganti isi `src/app/api/dashboard/route.js`. Bentuk JSON-nya harus tetap
  `{ pltu: {...}, pltn: {...} }` seperti data dummy yang ada sekarang.
