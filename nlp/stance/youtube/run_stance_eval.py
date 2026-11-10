"""Berkas arsip run: evaluasi stance komentar YouTube (majority vs zero_shot vs v2_ctx).
Jalankan dari folder CapstoneRAP2026, setelah API key di-set (PowerShell: $env:GEMMA="..."):
  python nlp/run_stance_eval.py
Untuk run lain dengan parameter berbeda (model lain, prompt yang sudah dituning, dst), salin berkas ini jadi run_stance_eval_v3.py dkk dan ubah RUN_* di bawah. Jangan menimpa run yang sudah tercatat di run_log_stance.md, agar riwayat percobaan tidak hilang.
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent

# Parameter run ini (terkunci)
RUN_LABEL = "stance v2 - run pertama (majority vs zero_shot vs v2_ctx)"
RUN_CONFIGS = ["majority", "zero_shot", "v2_ctx"]
RUN_MODEL = "gemma-4-26b-a4b-it"
RUN_TEMPERATURE = 0.0
RUN_EXTRA_ARGS: list = [] 
RUN_NOTE = (
    "Prompt v2_ctx belum dituning, masih transkripsi lurus dari Pedoman bagian D (belum diperbaiki "
    "dari galat model seperti relevansi v2 kemarin). Tujuan run ini: pastikan pipeline jalan di data "
    "asli + lihat angka awal sebelum masuk tahap tuning prompt."
)

LOG_PATH = HERE / "results" / "run_log_stance.md"
LOG_HEADER = (
    "# Log run evaluasi stance YouTube\n\n"
    "Riwayat tiap kali `run_stance_eval.py` (atau variannya) dijalankan: parameter yang dipakai dan "
    "ringkasan hasilnya. Angka mentah per komentar ada di `preds_stance_*.csv` / `compare_stance_all.csv`; "
    "berkas ini hanya ringkasan supaya riwayat run bisa dibaca tanpa membuka CSV.\n"
)


def git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE,
                              capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return "?"


def fmt(v) -> str:
    return f"{v:.1%}" if isinstance(v, float) and v == v else "-"


def append_log(summary: pd.DataFrame, cmd: list) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## {stamp} -- {RUN_LABEL}", "",
              f"- Commit: `{git_commit()}`",
              f"- Model: `{RUN_MODEL}` | temperature: {RUN_TEMPERATURE}",
              f"- Configs: {', '.join(RUN_CONFIGS)}",
              f"- Perintah: `{' '.join(cmd)}`",
              "",
              "| config | n | unknown | accuracy | macro_F1 | Support_F1 | Oppose_F1 | Neutral_F1 |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in summary.itertuples(index=False):
        lines.append(f"| {r.config} | {r.n} | {r.unknown} | {fmt(r.accuracy)} | {fmt(r.macro_F1)} | "
                      f"{fmt(r.Support_F1)} | {fmt(r.Oppose_F1)} | {fmt(r.Neutral_F1)} |")
    if RUN_NOTE:
        lines += ["", f"Catatan: {RUN_NOTE}"]

    is_new = not LOG_PATH.exists()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        if is_new:
            f.write(LOG_HEADER)
        f.write("\n".join(lines) + "\n")
    print(f"\n[run_stance_eval] log ditambahkan ke {LOG_PATH}")


def main() -> None:
    cmd = [sys.executable, str(HERE / "stance_v2.py"),
           "--configs", *RUN_CONFIGS,
           "--model", RUN_MODEL,
           "--temperature", str(RUN_TEMPERATURE),
           *RUN_EXTRA_ARGS]
    print(f"[run_stance_eval] {RUN_LABEL}")
    print(f"[run_stance_eval] perintah: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(f"stance_v2.py keluar dengan kode {result.returncode}; log tidak ditambahkan.")

    summary = pd.read_csv(HERE / "results" / "summary_stance_latest.csv")
    append_log(summary, cmd)


if __name__ == "__main__":
    main()
