"""Full-run stance + sentiment komentar YouTube (produksi, BUKAN evaluasi).

Menjalankan prompt Pedoman v2 (v2_ctx: stance + sentiment sekaligus) pada SEMUA komentar
relevan (comment_relevancy == True dari pipeline relevansi) -> ~13.199 komentar.

Beda dengan stance_v2.py:
  * stance_v2.py  = evaluasi di 124 komentar gold (ada label manusia, hitung akurasi).
  * run_full_youtube.py = produksi di 13.199 komentar relevan (TANPA label, hanya menghasilkan prediksi).

Engine (panggilan API, throttle, retry, resume, parser, prompt) DIPINJAM dari stance_v2.py,
tidak ditulis ulang. Output siap dipetakan ke gold.yt_comment_label oleh
Database/gold_from_youtube_fullrun.py.

Contoh (dari folder CapstoneRAP2026):
  # lihat prompt batch pertama, tanpa API:
  python nlp/stance/youtube/run_full_youtube.py --dry-run
  # uji alur penuh dengan model palsu (tanpa API, cepat):
  python nlp/stance/youtube/run_full_youtube.py --stub --limit 40
  # UJI KECIL dengan API asli (20 komentar) sebelum full-run:
  python nlp/stance/youtube/run_full_youtube.py --limit 20
  # FULL-RUN 13.199 komentar (butuh API key GEMMA, ~1-2 jam, bisa dihentikan & dilanjutkan):
  python nlp/stance/youtube/run_full_youtube.py

API key dibaca dari environment variable GEMMA / GOOGLE_API_KEY / GEMINI_API_KEY.
Hasil disimpan bertahap tiap batch -> aman di-Ctrl+C lalu dilanjutkan (resume otomatis).
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stance_v2 as sv  # engine: make_items, build_prompt, run_api_config, GenAIClient, dll.

PROJECT_ROOT = HERE.parents[3]           # .../Proyek Capstone
DEFAULT_INPUT = PROJECT_ROOT / "Dataset" / "Output Relevansi" / "relevancy_labeled.csv"
DEFAULT_VCTX = sv.SHARED / "video_context.csv"
CONFIG_NAME = "full_v2_ctx"              # nama berkas keluaran: preds_stance_full_v2_ctx__<model>.csv


def load_relevant(input_path: Path) -> pd.DataFrame:
    """Komentar relevan saja, dengan kolom yang dibutuhkan make_items()."""
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    if "comment_relevancy" not in df.columns:
        raise SystemExit(f"Kolom 'comment_relevancy' tidak ada di {input_path}. "
                         "File ini harus hasil pipeline relevansi (Model 1).")
    rel = df[df["comment_relevancy"].str.lower() == "true"].copy()
    rel["is_reply"] = (rel["reply"].str.lower() == "true").astype(int)
    need = {"cid", "text", "target", "video_id", "video_title"}
    missing = need - set(rel.columns)
    if missing:
        raise SystemExit(f"Kolom hilang di input: {missing}")
    return rel.reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=str(DEFAULT_INPUT),
                    help="CSV hasil relevansi (default: Dataset/Output Relevansi/relevancy_labeled.csv)")
    ap.add_argument("--video-context", default=str(DEFAULT_VCTX))
    ap.add_argument("--model", default="gemma-4-26b-a4b-it")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--rpm", type=int, default=25, help="batas panggilan/menit (free tier: 30)")
    ap.add_argument("--tpm", type=int, default=13000, help="batas token/menit (free tier: 16000)")
    ap.add_argument("--min-gap", type=float, default=2.0, help="jeda minimum antar panggilan (detik)")
    ap.add_argument("--max-retries", type=int, default=6)
    ap.add_argument("--limit", type=int, help="ambil N komentar acak saja (uji coba)")
    ap.add_argument("--shards", type=int, default=1,
                    help="bagi komentar relevan jadi N bagian supaya bisa dikerjakan beberapa orang/API key paralel")
    ap.add_argument("--shard", type=int, default=0, help="bagian ke-K (0..shards-1) yang dikerjakan proses ini")
    ap.add_argument("--no-resume", action="store_true", help="abaikan hasil lama, mulai dari nol")
    ap.add_argument("--no-json-mode", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="cetak prompt batch pertama saja, tanpa API")
    ap.add_argument("--stub", action="store_true", help="pakai model palsu untuk menguji alur (tanpa API)")
    ap.add_argument("--out-dir", default=str(HERE / "results"))
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if args.stub:
        sv.SLEEP_SCALE = 0.0
        args.model = "stub"

    rel = load_relevant(Path(args.input))
    if args.limit:
        rel = rel.sample(min(args.limit, len(rel)), random_state=1).reset_index(drop=True)

    vctx = sv.load_video_context(Path(args.video_context))
    items = sv.make_items(rel, vctx)
    total = len(items)

    if args.shards > 1:
        if not (0 <= args.shard < args.shards):
            raise SystemExit(f"--shard harus 0..{args.shards - 1}")
        items = [it for it in items if it["i"] % args.shards == args.shard]
        # 'i' tetap indeks dari daftar penuh -> tiap shard tidak tumpang tindih, cid unik antar-shard.
    run_name = CONFIG_NAME if args.shards == 1 else f"{CONFIG_NAME}_shard{args.shard}of{args.shards}"

    n_ctx = len({it["video_id"] for it in items if it["desc"]})
    shard_info = f" | shard {args.shard}/{args.shards} ({len(items)} dari {total})" if args.shards > 1 else ""
    print(f"komentar relevan: {len(items)}{shard_info} | video dengan deskripsi: {n_ctx} | model: {args.model}")

    cfg = dict(sv.CONFIGS["v2_ctx"])            # template v2 + context full
    if args.batch_size:
        cfg["batch"] = args.batch_size
    template = (HERE / "prompts" / cfg["template"]).read_text(encoding="utf-8")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        first = sv.make_batches(items, cfg["batch"])[0]
        prompt = sv.build_prompt(template, first, cfg["context"])
        (out_dir / "prompt_preview_full.txt").write_text(prompt, encoding="utf-8")
        print(f"\n{'=' * 30} batch pertama ({len(first)} komentar), ~{sv.est_tokens(prompt)} token {'=' * 30}\n{prompt}")
        print(f"\nPratinjau disimpan di {out_dir}/prompt_preview_full.txt")
        return

    if args.stub:
        client = sv.StubClient()
        throttle = sv.Throttle(10 ** 6, 10 ** 9, 0.0)
    else:
        client = sv.GenAIClient(args.model, sv.get_api_key(), args.temperature, json_mode=not args.no_json_mode)
        throttle = sv.Throttle(args.rpm, args.tpm, args.min_gap)

    preds = sv.run_api_config(run_name, cfg, template, items, client, throttle, args, out_dir)

    done = sum(1 for it in items if it["i"] in preds)
    path = sv.preds_path(out_dir, run_name, args.model)
    print(f"\nSelesai: {done}/{len(items)} komentar terprediksi. Hasil: {path}")
    if done < len(items):
        print(f"  {len(items) - done} komentar belum terbaca -> jalankan ulang perintah yang sama untuk melanjutkan (resume).")
    print("Langkah berikutnya: jalankan juga run_sentiment_full.py (pipeline sentiment khusus, "
          "lebih akurat untuk sentiment), lalu petakan KEDUANYA sekali jalan ke Gold:\n"
          "  python Database/gold_from_youtube_fullrun.py --preds \"" + str(path) +
          "\" --sentiment-preds <preds_sentiment_full...csv>")


if __name__ == "__main__":
    main()
