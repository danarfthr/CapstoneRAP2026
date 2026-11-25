"""Full-run SENTIMENT komentar YouTube (produksi, BUKAN evaluasi) - prompt v2_pedoman.

Prompt `prompts/sentiment_youtube_v2.txt` diekstrak APA ADANYA dari
`Result_Sentiment_Pipeline_NLP_YouTube_Comment.ipynb` (variabel PROMPT_V2), yaitu
prompt yang dievaluasi dan mendapat accuracy 80% / macro-F1 80% pada 91 komentar gold
(lihat nlp/sentiment/youtube/results/summary_sentiment_latest.csv). Pipeline sentiment
sebelumnya HANYA ada sebagai notebook Colab untuk evaluasi; skrip ini versi terminal
untuk PRODUKSI di seluruh komentar relevan (13.199), dengan resume otomatis seperti
run_full_youtube.py (stance).

Kenapa terpisah dari run_full_youtube.py (stance), bukan satu panggilan API sekaligus:
hasil evaluasi menunjukkan prompt sentiment khusus (v2_pedoman, F1 80%) lebih baik
daripada sentiment yang ikut terbawa dari prompt stance gabungan (v2_ctx). Konsekuensinya
dua kali biaya panggilan API untuk 13.199 komentar yang sama -- lihat README.md nlp/
bagian "Cara membaca hasil evaluasi" soal alasan tiap tugas dievaluasi sendiri-sendiri.

Engine (panggilan API, throttle, retry, resume, render item per-video) DIPINJAM dari
stance_v2.py / relevance_v2.py, tidak ditulis ulang. Hanya parser JSON yang beda
(hasil sentiment-only, bukan stance+sentiment).

Contoh (dari folder CapstoneRAP2026):
  python nlp/sentiment/youtube/run_sentiment_full.py --dry-run
  python nlp/sentiment/youtube/run_sentiment_full.py --stub --limit 40
  python nlp/sentiment/youtube/run_sentiment_full.py --limit 20     # uji kecil, API asli
  python nlp/sentiment/youtube/run_sentiment_full.py                # full-run 13.199 komentar

API key dibaca dari environment variable GEMMA / GOOGLE_API_KEY / GEMINI_API_KEY.
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "stance" / "youtube"))
sys.path.insert(0, str(HERE.parent.parent / "relevance" / "youtube"))
import stance_v2 as sv  # pinjam engine: make_items, render_items, build_prompt, GenAIClient, Throttle, dll.

PROJECT_ROOT = HERE.parents[3]  # .../Proyek Capstone
DEFAULT_INPUT = PROJECT_ROOT / "Dataset" / "Output Relevansi" / "relevancy_labeled.csv"
DEFAULT_VCTX = sv.SHARED / "video_context.csv"
PROMPT_FILE = HERE / "prompts" / "sentiment_youtube_v2.txt"
CONFIG_NAME = "full_v2_pedoman"
SENTIMENTS = ["Positive", "Neutral", "Negative"]

_SENT_MAP = {
    "positive": "Positive", "positif": "Positive",
    "negative": "Negative", "negatif": "Negative",
    "neutral": "Neutral", "netral": "Neutral",
}
FENCE_RE = re.compile(r"```(?:json)?", re.I)


def parse_sentiment_response(text: str, expected: set) -> dict:
    """{id: (sentiment, alasan)} untuk id yang diminta. Sama strukturnya dengan
    stance_v2.parse_response, tapi field wajibnya 'sentiment' (bukan 'stance')."""
    if not text:
        return {}
    import json
    t = FENCE_RE.sub("", text)
    dec = json.JSONDecoder()
    for m in re.finditer(r"[\[{]", t):
        try:
            data, _ = dec.raw_decode(t[m.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            data = data.get("results", data.get("hasil", [data]))
        if not isinstance(data, list):
            continue
        out = {}
        for it in data:
            if not isinstance(it, dict):
                continue
            try:
                i = int(it.get("id"))
            except (TypeError, ValueError):
                continue
            raw = it.get("sentiment", it.get("sentimen"))
            lab = _SENT_MAP.get(raw.strip().lower()) if isinstance(raw, str) else None
            if i in expected and lab is not None:
                out[i] = (lab, str(it.get("alasan", ""))[:160])
        if out:
            return out
    return {}


def classify_batch(client, throttle, template, context, batch, max_retries, tag):
    got, pending, attempt, errs = {}, list(batch), 0, 0
    while pending and attempt <= max_retries:
        prompt = sv.build_prompt(template, pending, context)
        throttle.wait(sv.est_tokens(prompt))
        try:
            text = client.generate(prompt)
        except sv.FatalAPIError:
            raise
        except Exception as e:
            errs += 1
            wait = sv.backoff_seconds(e, attempt)
            print(f"    ! {tag}: {type(e).__name__}: {str(e)[:110]} -> ulang {wait:.0f}s ({attempt + 1}/{max_retries})")
            sv.pause(wait)
            attempt += 1
            continue
        parsed = parse_sentiment_response(text, {it["i"] for it in pending})
        if not parsed:
            errs += 1
            print(f"    ! {tag}: jawaban tidak terbaca ({text[:70]!r}) -> ulang ({attempt + 1}/{max_retries})")
            sv.pause(sv.backoff_seconds(RuntimeError(""), attempt))
            attempt += 1
            continue
        got.update(parsed)
        pending = [it for it in pending if it["i"] not in parsed]
        if pending:
            attempt += 1
    return got, errs


def preds_path(out_dir: Path, model: str, shard_tag: str = "") -> Path:
    return out_dir / f"preds_sentiment_{CONFIG_NAME}{shard_tag}__{re.sub(r'[^A-Za-z0-9._-]', '_', model)}.csv"


def load_preds(path: Path) -> dict:
    if not path.exists():
        return {}
    d = pd.read_csv(path, dtype=str, keep_default_na=False)
    return {int(r.i): (r.pred_sentiment, r.alasan) for r in d.itertuples(index=False) if r.pred_sentiment in SENTIMENTS}


def save_preds(path: Path, items: list, preds: dict) -> None:
    rows = [{"i": it["i"], "cid": it["cid"], "target": it["target"],
             "pred_sentiment": preds[it["i"]][0] if it["i"] in preds else "",
             "alasan": preds.get(it["i"], (None, ""))[1]} for it in items]
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


def load_relevant(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    if "comment_relevancy" not in df.columns:
        raise SystemExit(f"Kolom 'comment_relevancy' tidak ada di {input_path}.")
    rel = df[df["comment_relevancy"].str.lower() == "true"].copy()
    rel["is_reply"] = (rel["reply"].str.lower() == "true").astype(int)
    return rel.reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=str(DEFAULT_INPUT))
    ap.add_argument("--video-context", default=str(DEFAULT_VCTX))
    ap.add_argument("--model", default="gemma-4-26b-a4b-it")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--rpm", type=int, default=25)
    ap.add_argument("--tpm", type=int, default=13000)
    ap.add_argument("--min-gap", type=float, default=4.0,
                    help="jeda minimum antar panggilan (detik). 4.0 = nilai yang dipakai & terbukti stabil di notebook evaluasi.")
    ap.add_argument("--max-retries", type=int, default=6)
    ap.add_argument("--limit", type=int, help="ambil N komentar acak saja (uji coba)")
    ap.add_argument("--shards", type=int, default=1,
                    help="bagi komentar relevan jadi N bagian supaya bisa dikerjakan beberapa orang/API key paralel")
    ap.add_argument("--shard", type=int, default=0, help="bagian ke-K (0..shards-1) yang dikerjakan proses ini")
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--no-json-mode", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stub", action="store_true")
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
    shard_tag = "" if args.shards == 1 else f"_shard{args.shard}of{args.shards}"
    shard_info = f" | shard {args.shard}/{args.shards} ({len(items)} dari {total})" if args.shards > 1 else ""
    print(f"komentar relevan: {len(items)}{shard_info} | model: {args.model}")

    template = PROMPT_FILE.read_text(encoding="utf-8")
    context = "full"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        first = sv.make_batches(items, args.batch_size)[0]
        prompt = sv.build_prompt(template, first, context)
        (out_dir / "prompt_preview_sentiment_full.txt").write_text(prompt, encoding="utf-8")
        print(f"\n{'=' * 30} batch pertama ({len(first)} komentar), ~{sv.est_tokens(prompt)} token {'=' * 30}\n{prompt}")
        return

    if args.stub:
        client = sv.StubClient()
        throttle = sv.Throttle(10 ** 6, 10 ** 9, 0.0)
    else:
        client = sv.GenAIClient(args.model, sv.get_api_key(), args.temperature, json_mode=not args.no_json_mode)
        throttle = sv.Throttle(args.rpm, args.tpm, args.min_gap)

    path = preds_path(out_dir, args.model, shard_tag)
    preds = {} if args.no_resume else load_preds(path)
    todo = [it for it in items if it["i"] not in preds]
    batches = sv.make_batches(todo, args.batch_size)
    print(f"[{CONFIG_NAME}] {len(items)} komentar | sudah ada {len(preds)} | batch {args.batch_size} -> {len(batches)} panggilan")
    for n, b in enumerate(batches, 1):
        got, errs = classify_batch(client, throttle, template, context, b, args.max_retries, f"b{n}")
        preds.update(got)
        save_preds(path, items, preds)
        print(f"  batch {n}/{len(batches)}: {len(got)}/{len(b)} terbaca" + (f" ({errs} error/ulang)" if errs else ""))

    done = sum(1 for it in items if it["i"] in preds)
    print(f"\nSelesai: {done}/{len(items)} komentar terprediksi. Hasil: {path}")
    if done < len(items):
        print(f"  {len(items) - done} komentar belum terbaca -> jalankan ulang perintah yang sama untuk melanjutkan (resume).")
    print("Langkah berikutnya: gabungkan dengan hasil stance (run_full_youtube.py) via "
          "`python Database/gold_from_youtube_fullrun.py --preds <preds_stance_full...csv> "
          "--sentiment-preds \"" + str(path) + "\"`")


if __name__ == "__main__":
    main()
