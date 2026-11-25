# TODO — Full-run Stance & Sentiment YouTube (Silver → Gold)

**Konteks (per 23 Nov 2026, update terakhir):**
- Silver YouTube (relevansi) **sudah penuh**: 70.773 komentar dilabel model v1 → 13.199 relevan.
- **Keputusan tim**: Gold manusia pakai Pedoman v2 (`gold_yt_v2.csv`), dan sentiment dapat pipeline terpisah dari stance (F1 lebih tinggi, 80% vs ~72%).
- **Sudah dikerjakan** (Mikail, pegang API key GEMMA untuk full-run):
  - `gold.yt_comment_label` manusia dimigrasikan ke Pedoman v2 — sumber ganti dari `ANOTASI YOUTUBE FINAL.xlsx` (109 komentar) ke `gold_yt_v2.csv` (124 komentar). `precheck.py`: 89 OK, 0 error. Bonus: akurasi gemma vs gold v2 yang lebih lengkap naik jadi **81,5%** (n=124).
  - Script produksi **stance** (`nlp/stance/youtube/run_full_youtube.py`) dan **sentiment** (`nlp/sentiment/youtube/run_sentiment_full.py`) sudah dibuat, dites tanpa API (dry-run + stub), siap full-run. Estimasi murni dari limit token: stance ±6,1 jam, sentiment ±4,4 jam (bisa lebih karena retry; keduanya resumable, bisa dihentikan & dilanjutkan).
  - Mapper `Database/gold_from_youtube_fullrun.py` sudah dites menggabungkan 2 file preds (stance + sentiment) jadi 1 baris model per komentar, FK & enum lolos `precheck.py`.
- **Masih harus dijalankan manusia** (butuh API key, berjam-jam): full-run 13.199 komentar untuk stance & sentiment (lihat perintah di masing-masing script `--help`).

---

## A. NLP — sebelum full-run
- [x] **Putuskan gold standar**: Pedoman v2 — sudah dimigrasikan ke `transform.py`
- [x] Pipeline sentiment terpisah dari stance — `run_sentiment_full.py` dibuat
- [ ] Tuning prompt **stance** v2 dari `stance/youtube/results/errors_stance_*.csv` (celah: D8 sarkasme, D4/D6, D12 co-firing) — opsional, di luar scope saat ini
- [ ] Tuning prompt **sentiment** v2 — sudah F1 80%, opsional

## B. NLP — full-run (yang bikin Gold bisa diisi)
- [x] Script siap: `run_full_youtube.py` (stance) & `run_sentiment_full.py` (sentiment)
- [ ] **Jalankan** `run_full_youtube.py` pada 13.199 komentar relevan (API key GEMMA, ±6 jam, resumable)
- [ ] **Jalankan** `run_sentiment_full.py` pada 13.199 komentar relevan (±4-5 jam, resumable)
- [ ] Output otomatis tersimpan di `results/preds_stance_full_v2_ctx__*.csv` dan `results/preds_sentiment_full_v2_pedoman__*.csv`

## C. Database (Peran A → Peran B)
- [x] `gold_from_youtube_fullrun.py` siap & teruji (gabung 2 file preds, tambah `ref.labeler` otomatis, idempoten)
- [ ] Setelah B selesai: `python Database/gold_from_youtube_fullrun.py --preds <preds_stance...> --sentiment-preds <preds_sentiment...>`
- [ ] `precheck.py` 0 error → serahkan ke Peran B
- [ ] Peran B: **load Gold YouTube ke Supabase**, cek jumlah baris cocok

## D. Terbuka
- [ ] Konfirmasi selisih confusion matrix relevansi YouTube (CSV 46/38/1/24 vs gambar 49/35/2/23) — sudah ditanyakan ke tim Colab, tunggu jawaban
