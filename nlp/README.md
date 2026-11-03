# nlp/ — relevansi komentar YouTube (prompt v2 + konteks video)

Status: **belum di-commit**. Folder ini dibuat 3 November 2026 untuk persiapan laporan Capstone.

| Berkas | Fungsi |
| --- | --- |
| `relevance_v2.py` | Evaluasi prompt v1 (lama) vs v2 (Pedoman Anotasi v2), dengan/tanpa konteks video, terhadap set gold |
| `fetch_video_context.py` | Ambil deskripsi, tanggal upload, tag, kategori video lewat yt-dlp |
| `prompts/relevance_youtube_v1.txt` | Prompt lama apa adanya (untuk pembanding) |
| `prompts/relevance_youtube_v2.txt` | Prompt baru berbasis Pedoman v2. **Boleh diedit tanpa menyentuh kode** |
| `data/gold_yt_v2.csv` | 124 komentar berlabel Pedoman v2 (sheet `YT` di `anotasi youtube baru.xlsx`) |
| `data/video_context.csv` | Konteks 318 dari 319 video (judul, channel, deskripsi, tanggal upload, tag); 1 video sudah dihapus/privat |
| `data/keyword_audit_youtube.csv` | Yield relevan per keyword (label model v1, 70.773 komentar) |
| `data/video_audit.csv` | Per video: jumlah komentar, yield, tanggal upload, lolos gerbang atau tidak |
| `results/` | Keluaran evaluasi (`summary_latest.csv`, `errors_*.csv`, `compare_all.csv`) |

## Menjalankan evaluasi

Lokal (dari folder `CapstoneRAP2026`):

```bash
pip install google-genai pandas
export GEMMA="<api key AI Studio>"          # PowerShell: $env:GEMMA="..."
python nlp/relevance_v2.py --dry-run         # lihat prompt saja, tidak memanggil API
python nlp/relevance_v2.py                   # v1_title, v2_title, v2_ctx (±8-10 menit di free tier)
```

Colab: upload folder `nlp/`, lalu

```python
!pip install -q google-genai
!python nlp/relevance_v2.py          # API key dibaca dari Colab Secrets bernama GEMMA
```

Opsi yang sering dipakai: `--configs v2_ctx`, `--model <nama model>` (mis. model berbayar),
`--rpm 100 --tpm 200000` (kalau limit lebih longgar), `--limit 30` (uji cepat),
`--prompt-file prompts/punya_saya.txt --configs custom` (prompt buatan sendiri; wajib memuat `{{ITEMS}}`).
Hasil tersimpan per komentar, jadi kalau terputus cukup jalankan ulang (lanjut dari yang sudah selesai).

## Cara membaca hasil

- Set gold **80% relevan** karena dirancang seimbang per kelas stance, jadi akurasi mentahnya menyesatkan.
  Lihat `recall` (berapa dari yang relevan tertangkap) dan `specificity` (berapa dari yang tidak relevan tertolak).
  Kolom `prec@20%` / `prec@30%` = perkiraan presisi bila di data asli hanya 20% / 30% komentar yang relevan.
- N=124 kecil: perhatikan kolom `recall_95CI` / `spec_95CI`. Selisih beberapa poin antar konfigurasi belum tentu nyata.
- `unknown` = komentar yang gagal diproses setelah semua retry. Itu **bukan** False dan tidak ikut dihitung.
- `errors_<config>.csv` berisi komentar yang salah beserta alasan model (sebut kode aturan Pedoman) untuk dicek annotator.

## Catatan jujur

- Prompt v2 memuat contoh kata dari Pedoman B6 (mis. "belum saatnya", "maksudnya"); beberapa komentar gold memuat kata yang sama.
  Labelnya tetap bergantung pada konteks video, tapi jangan jadikan ini bukti tunggal.
- Set gold yang dipakai adalah sampel baru (96 dari 124 komentar tidak ada di anotasi lama), jadi angka v1 di sini tidak
  bisa dibandingkan langsung dengan angka lama (akurasi 64%, recall 53% pada anotasi lama).
- Perbaikan prompt di-tuning dari galat model v1 pada gold yang sama (18 FN + 5 FP). Untuk klaim akhir, ukur ulang pada
  set uji baru yang belum pernah dilihat (lembar `Sheet5`/`Sheet6` di file anotasi, setelah dilabeli).
