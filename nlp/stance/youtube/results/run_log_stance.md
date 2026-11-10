# Log run evaluasi stance YouTube

Riwayat tiap kali `run_stance_eval.py` (atau variannya) dijalankan: parameter yang dipakai dan ringkasan hasilnya. Angka mentah per komentar ada di `preds_stance_*.csv` / `compare_stance_all.csv`; berkas ini hanya ringkasan supaya riwayat run bisa dibaca tanpa membuka CSV.

## 2026-11-10 14:33 -- stance v2 - run pertama (majority vs zero_shot vs v2_ctx)

- Commit: `91d0ccd`
- Model: `gemma-4-26b-a4b-it` | temperature: 0.0
- Configs: majority, zero_shot, v2_ctx
- Perintah: `C:\Users\Mikail Achmad\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe D:\Kuliah\Tugas dan Projek\Proyek Capstone\CapstoneRAP2026\nlp\stance_v2.py --configs majority zero_shot v2_ctx --model gemma-4-26b-a4b-it --temperature 0.0`

| config | n | unknown | accuracy | macro_F1 | Support_F1 | Oppose_F1 | Neutral_F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| majority | 98 | 0 | 44.9% | 20.7% | 0.0% | 0.0% | 62.0% |
| zero_shot | 68 | 30 | 76.5% | 74.9% | 70.6% | 72.2% | 81.8% |
| v2_ctx | 90 | 8 | 73.3% | 72.0% | 68.0% | 69.8% | 78.2% |

Catatan: Prompt v2_ctx belum dituning, masih transkripsi lurus dari Pedoman bagian D (belum diperbaiki dari galat model seperti relevansi v2 kemarin). Tujuan run ini: pastikan pipeline jalan di data asli + lihat angka awal sebelum masuk tahap tuning prompt.
