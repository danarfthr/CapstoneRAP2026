# nlp/ — pipeline NLP komentar YouTube & berita (relevansi, stance, sentiment)

Dikategorikan per **tugas** (relevance / stance / sentiment), lalu per **sumber data** (youtube / news).
Data mentah YouTube yang dipakai bersama oleh ketiga tugas ada di `shared/youtube/`.

```
nlp/
├── shared/youtube/          # data mentah dipakai bersama (gold, konteks video)
├── relevance/
│   ├── youtube/             # pipeline relevansi komentar YouTube (terminal, relevance_v2.py)
│   └── news/                # pipeline relevansi komentar berita (Colab, punya tim News)
├── stance/youtube/          # pipeline stance komentar YouTube (terminal, stance_v2.py)
└── sentiment/youtube/       # pipeline sentiment komentar YouTube (Colab notebook)
```

## shared/youtube/ — data mentah bersama

| Berkas | Fungsi |
| --- | --- |
| `gold_yt_v2.csv` | 124 komentar berlabel Pedoman v2 (relevan/stance/sentiment) — sheet `YT` di `anotasi youtube baru.xlsx` |
| `video_context.csv` | Konteks 318/319 video (judul, channel, deskripsi, tanggal upload, tag) |
| `keyword_audit_youtube.csv` | Yield relevan per keyword (label model v1, 70.773 komentar) |
| `video_audit.csv` | Per video: jumlah komentar, yield, tanggal upload, lolos gerbang atau tidak |
| `stance_sentiment_input_yt.csv` | 99 komentar relevan + konteks video, format siap-upload untuk notebook Colab stance/sentiment |
| `fetch_video_context.py` / `video_audit.py` | Skrip pembuat `video_context.csv` / `video_audit.csv` (yt-dlp) |

## relevance/youtube/ — relevansi komentar YouTube

Evaluasi prompt v1 (lama) vs v2 (Pedoman Anotasi v2 bagian B), dengan/tanpa konteks video, pada 124 komentar gold (biner).

```bash
# dari folder CapstoneRAP2026
pip install google-genai pandas
export GEMMA="<api key AI Studio>"          # PowerShell: $env:GEMMA="..."
python nlp/relevance/youtube/relevance_v2.py --dry-run   # lihat prompt saja, tidak memanggil API
python nlp/relevance/youtube/relevance_v2.py              # v1_title, v2_title, v2_ctx (±8-10 menit)
```

Alternatif Colab: `nlp/relevance/youtube/Relevancy_Pipeline_NLP_YouTube_Comment.ipynb` (upload `shared/youtube/...` + prompts sebagai input, key dari Colab Secrets `GEMMA`).

Hasil terbaru (lihat `results/summary_latest.csv`): prompt v2 jauh lebih disiplin (specificity 92-96%) dibanding v1 (42% — asal cap "relevan"); `v2_ctx` paling sedikit gagal parse (`unknown`=8 dari 124).

## stance/youtube/ — stance komentar YouTube (Support/Oppose/Neutral)

Evaluasi `majority` (baseline) vs `zero_shot` (tanpa pedoman) vs `v2_ctx` (Pedoman v2 bagian D + konteks video + target), pada 98 komentar relevan.

```bash
python nlp/stance/youtube/run_stance_eval.py   # parameter terkunci, log otomatis ke results/run_log_stance.md
# atau langsung:
python nlp/stance/youtube/stance_v2.py --dry-run
```

Alternatif Colab: `nlp/stance/youtube/Stance_Pipeline_NLP_YouTube_Comment.ipynb` — **catatan**: Colab sempat berkali-kali macet (server/koneksi), run resmi akhirnya lewat terminal.

Hasil terbaru (lihat `results/summary_stance_latest.csv`): `v2_ctx` lebih *robust* (unknown=8/98) walau `zero_shot` tampak unggul di angka mentah (tapi cuma dihitung dari 68/98 sampel "termudah"). Tiga celah untuk tuning: aturan D8 (bantahan argumen → Support) terlalu longgar ke sarkasme, D4 vs D6 kurang tegas, D12 (ganti bahan bakar total) bertentangan dengan gold di kasus co-firing.

## sentiment/youtube/ — sentiment komentar YouTube (Positive/Neutral/Negative)

Evaluasi `majority` vs `zero_shot` vs `v2_pedoman` (Pedoman v2 bagian C + konteks video), pada 91 komentar berlabel sentiment valid. Dijalankan di Colab: `Sentiment_Pipeline_NLP_YouTube_Comment.ipynb` (template) → `Result_Sentiment_Pipeline_NLP_YouTube_Comment.ipynb` (hasil run).

Hasil (lihat `results/summary_sentiment_latest.csv`): `v2_pedoman` accuracy 80% / macro-F1 80%, unggul dari `zero_shot` (78%/78%) dan jauh dari `majority` (44%/20%).

## relevance/news/ — relevansi komentar berita (punya tim News)

`Relevancy_Pipeline_NLP_News_Comment_v2.ipynb` — notebook Colab milik rekan tim untuk berita (bukan YouTube). Lihat isinya untuk detail; arsitektur serupa (KWIC + Rubric-Based Prompt).

## Cara membaca hasil evaluasi (semua pipeline)

- **Relevansi**: set gold 80% relevan → akurasi mentah menyesatkan. Lihat `recall`/`specificity`, serta `prec@20%`/`prec@30%` (perkiraan presisi bila data asli cuma 20-30% relevan).
- **Stance/Sentiment**: kelas tidak seimbang (Neutral dominan) → lihat `macro_F1` dan F1 per kelas, bukan akurasi mentah.
- **N kecil** (98-124): perhatikan kolom `*_95CI`. Selisih beberapa poin antar konfigurasi belum tentu nyata.
- `unknown` = komentar yang gagal diproses setelah semua retry. **Bukan** otomatis salah, tidak ikut dihitung di akurasi — tapi makin banyak `unknown`, makin kecil & makin bias sampel yang dievaluasi (lihat kasus `zero_shot` stance).
- `errors_<config>.csv` di tiap `results/`: komentar yang salah + alasan model (sebut kode aturan Pedoman), untuk audit annotator & bahan tuning prompt.

## Status tuning (per 2026-11-10)

Ketiga prompt v2 (relevansi, stance, sentiment) **masih transkripsi lurus dari Pedoman**, belum di-tuning dari analisis error spesifik — kecuali relevansi yang sudah sempat satu putaran tuning dari galat v1 (18 FN + 5 FP, lihat `relevance/youtube/results/audit_model_v1_vs_gold.xlsx`). Tuning lanjutan sebaiknya fokus ke pola error yang sudah teridentifikasi di `errors_*.csv` masing-masing tugas.
