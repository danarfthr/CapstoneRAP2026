"""Evaluasi Stance komentar YouTube (Support / Oppose / Neutral) terhadap target PLTU/PLTN.

  * Hanya komentar relevan yang dinilai (Pedoman A1: Irrelevant -> stance Irrelevant otomatis).
  * Stance dinilai terhadap kolom target (PLTU/PLTN/UMUM) -> model diberi target sebagai acuan (Pedoman D10).
  * Prompt gabungan, model mengeluarkan stance + sentiment, tetapi skrip ini mengukur stance dulu.
  * Baseline pembanding: 'majority' (tebak kelas mayoritas, tanpa API) dan 'zero_shot' (prompt ringkas tanpa pedoman).
  * Hasil berupa confusion matrix 3x3, akurasi, macro-F1, dan precision/recall/F1 per kelas (+ selang kepercayaan).
  * Panggilan API, throttle, retry, resume, dan parser JSON toleran dipinjam dari relevance_v2.py (tidak ditulis ulang).

Contoh (dari folder CapstoneRAP2026):
  python nlp/stance_v2.py --dry-run  # hanya lihat prompt, tanpa API
  python nlp/stance_v2.py --stub  # uji alur dengan model palsu, tanpa API
  python nlp/stance_v2.py  # majority, zero_shot, v2_ctx pada set gold
  python nlp/stance_v2.py --configs v2_ctx --temperature 0.2
  python nlp/stance_v2.py --prompt-file nlp/prompts/stance_saya.txt --configs custom

API key dibaca dari environment variable GEMMA / GOOGLE_API_KEY / GEMINI_API_KEY, atau dari Colab Secrets
bernama GEMMA. Di Colab: !pip install -q google-genai
"""
import argparse
import json
import math
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent.parent / "shared" / "youtube"  # data mentah YouTube dipakai bersama relevance/stance/sentiment

# Pinjam engine dari pipeline relevansi (folder beda: nlp/relevance/youtube/)
sys.path.insert(0, str(HERE.parent.parent / "relevance" / "youtube"))
from relevance_v2 import (
    FatalAPIError, GenAIClient, Throttle, backoff_seconds, clean_description,
    est_tokens, get_api_key, load_video_context, wilson,
)

SLEEP_SCALE = 1.0

STANCES = ["Support", "Oppose", "Neutral"]  # kelas yang dinilai (komentar sudah relevan)

CONFIGS = {
    # tebak kelas mayoritas gold untuk semua komentar baseline
    "majority": {"kind": "majority"},
    # prompt ringkas tanpa pedoman, hanya judul video lalu ukur stance
    "zero_shot": {"template": "stance_youtube_v1.txt", "context": "title", "batch": 10},
    # prompt berbasis Pedoman D + judul + channel + deskripsi + tag untuk mengukur efek pedoman + konteks
    "v2_ctx": {"template": "stance_youtube_v2.txt", "context": "full", "batch": 8},
}


def pause(sec: float) -> None:
    time.sleep(sec * SLEEP_SCALE)


# Data
def make_items(gold: pd.DataFrame, vctx: dict) -> list:
    items = []
    for i, r in enumerate(gold.itertuples(index=False)):
        v = vctx.get(r.video_id, {})
        items.append({
            "i": i,
            "cid": r.cid,
            "text": re.sub(r"\s+", " ", str(r.text)).strip()[:600],
            "is_reply": bool(int(r.is_reply)),
            "target": r.target,
            "video_id": r.video_id,
            "title": v.get("title") or r.video_title,
            "channel": v.get("channel", ""),
            "desc": v.get("desc", ""),
            "tags": v.get("tags", ""),
        })
    return items


# Prompt
def render_items(items: list, context: str) -> str:
    """Komentar dikelompokkan per video agar judul/deskripsi cukup ditulis sekali dan target menempel di tiap komentar."""
    by_video: dict = {}
    for it in items:
        by_video.setdefault(it["video_id"], []).append(it)
    out = ["== VIDEO DAN KOMENTAR =="]
    for n, group in enumerate(by_video.values(), 1):
        g0 = group[0]
        out.append(f"\nVideo {n}")
        out.append(f"Judul: {g0['title']}")
        if context == "full":
            if g0["channel"]:
                out.append(f"Channel: {g0['channel']}")
            if g0["desc"]:
                out.append(f"Deskripsi: {g0['desc']}")
            if g0["tags"]:
                out.append(f"Tag: {g0['tags']}")
        out.append("Komentar:")
        for it in group:
            jenis = "reply" if it["is_reply"] else "komentar"
            out.append(f"[{it['i']}] (target: {it['target']}) ({jenis}) {it['text']}")
    return "\n".join(out)


def build_prompt(template: str, items: list, context: str) -> str:
    return template.replace("{{ITEMS}}", render_items(items, context))


def make_batches(items: list, size: int) -> list:
    seq = sorted(items, key=lambda x: (x["video_id"], x["i"]))
    return [seq[k:k + size] for k in range(0, len(seq), size)]


# Parsing
FENCE_RE = re.compile(r"```(?:json)?", re.I)
_STANCE_MAP = {
    "support": "Support", "mendukung": "Support", "dukung": "Support", "pro": "Support", "setuju": "Support",
    "oppose": "Oppose", "menolak": "Oppose", "tolak": "Oppose", "kontra": "Oppose", "against": "Oppose",
    "neutral": "Neutral", "netral": "Neutral",
}
_SENT_MAP = {
    "positive": "Positive", "positif": "Positive",
    "negative": "Negative", "negatif": "Negative",
    "neutral": "Neutral", "netral": "Neutral",
}


def _norm(value, mapping):
    if not isinstance(value, str):
        return None
    return mapping.get(value.strip().lower())


def parse_response(text: str, expected: set) -> dict:
    """{id: (stance, sentiment, alasan)} untuk id yang diminta. Toleran terhadap pagar ```, teks pembuka, dan karakter sisa di belakang JSON. id dengan stance tak dikenal diabaikan."""
    if not text:
        return {}
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
            stance = _norm(it.get("stance", it.get("sikap")), _STANCE_MAP)
            if i in expected and stance is not None:
                sentiment = _norm(it.get("sentiment", it.get("sentimen")), _SENT_MAP)
                out[i] = (stance, sentiment, str(it.get("alasan", ""))[:160])
        if out:
            return out
    return {}

# Uji alur
class StubClient:
    """Menguji alur tanpa API"""
    OPPOSE = re.compile(r"jangan|tolak|tutup|pensiun|batal|bahaya|ngeri|mending ga|stop", re.I)
    SUPPORT = re.compile(r"bangun|lanjut|dukung|setuju|bagus|manfaat|perlu|wajib|aman", re.I)

    def __init__(self):
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if self.calls % 5 == 0:
            raise RuntimeError("500 INTERNAL. Internal error encountered.")
        rows = re.findall(r"^\[(\d+)\] \(target: [^)]*\) \((?:komentar|reply)\) (.*)$", prompt, re.M)
        res = []
        for a, b in rows:
            if self.OPPOSE.search(b):
                st, se = "Oppose", "Negative"
            elif self.SUPPORT.search(b):
                st, se = "Support", "Positive"
            else:
                st, se = "Neutral", "Neutral"
            res.append({"id": int(a), "alasan": "stub", "stance": st, "sentiment": se})
        if self.calls % 7 == 0:
            return "```json\n" + json.dumps(res) + "\n```\nSemoga membantu"
        if self.calls % 11 == 0 and len(res) > 1:
            res = res[:-1]
        return json.dumps(res)

# Run
def classify_batch(client, throttle, template, context, batch, max_retries, tag):
    """Mengembalikan ({i: (stance, sentiment, alasan)}, jumlah_error). Item yang tetap gagal tidak ada di hasil."""
    got, pending, attempt, errs = {}, list(batch), 0, 0
    while pending and attempt <= max_retries:
        prompt = build_prompt(template, pending, context)
        throttle.wait(est_tokens(prompt))
        try:
            text = client.generate(prompt)
        except FatalAPIError:
            raise
        except Exception as e:
            errs += 1
            wait = backoff_seconds(e, attempt)
            print(f"    ! {tag}: {type(e).__name__}: {str(e)[:110]} -> ulang {wait:.0f}s ({attempt + 1}/{max_retries})")
            pause(wait)
            attempt += 1
            continue
        parsed = parse_response(text, {it["i"] for it in pending})
        if not parsed:
            errs += 1
            print(f"    ! {tag}: jawaban tidak terbaca ({text[:70]!r}) -> ulang ({attempt + 1}/{max_retries})")
            pause(backoff_seconds(RuntimeError(""), attempt))
            attempt += 1
            continue
        got.update(parsed)
        pending = [it for it in pending if it["i"] not in parsed]
        if pending:  # jawaban parsial, ulangi hanya yang hilang
            attempt += 1
    return got, errs


def preds_path(out_dir: Path, config: str, model: str) -> Path:
    return out_dir / f"preds_stance_{config}__{re.sub(r'[^A-Za-z0-9._-]', '_', model)}.csv"


def load_preds(path: Path) -> dict:
    if not path.exists():
        return {}
    d = pd.read_csv(path, dtype=str, keep_default_na=False)
    return {int(r.i): (r.pred_stance, r.pred_sentiment or None, r.alasan)
            for r in d.itertuples(index=False) if r.pred_stance in STANCES}


def save_preds(path: Path, items: list, preds: dict) -> None:
    rows = [{"i": it["i"], "cid": it["cid"], "target": it["target"],
             "pred_stance": preds[it["i"]][0] if it["i"] in preds else "",
             "pred_sentiment": (preds[it["i"]][1] or "") if it["i"] in preds else "",
             "alasan": preds.get(it["i"], (None, None, ""))[2]} for it in items]
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


def run_api_config(name, cfg, template, items, client, throttle, args, out_dir):
    path = preds_path(out_dir, name, args.model)
    preds = {} if args.no_resume else load_preds(path)
    todo = [it for it in items if it["i"] not in preds]
    size = args.batch_size or cfg["batch"]
    batches = make_batches(todo, size)
    print(f"\n[{name}] {len(items)} komentar | sudah ada {len(preds)} | batch {size} -> {len(batches)} panggilan")
    errs_total = 0
    for n, b in enumerate(batches, 1):
        got, errs = classify_batch(client, throttle, template, cfg["context"], b, args.max_retries, f"{name} b{n}")
        preds.update(got)
        errs_total += errs
        save_preds(path, items, preds)
        print(f"  batch {n}/{len(batches)}: {len(got)}/{len(b)} terbaca" + (f" ({errs} error/ulang)" if errs else ""))
    return preds


def run_majority(y: list, items: list) -> dict:
    """Prediksi kelas mayoritas gold untuk semua komentar. Lantai baseline (optimis karena dihitung di set yang sama)."""
    top = Counter(y).most_common(1)[0][0]
    return {it["i"]: (top, None, f"majority={top}") for it in items}


# Metrics
def confusion(y: list, p: list, labels: list) -> dict:
    """{gold: {pred: n}} hanya untuk pasangan yang prediksinya ada (bukan None/unknown)."""
    cm = {g: {q: 0 for q in labels} for g in labels}
    for a, b in zip(y, p):
        if b is not None and a in labels and b in labels:
            cm[a][b] += 1
    return cm


def metrics(y: list, p: list, labels: list) -> dict:
    """y: label gold (str); p: str/None (None = gagal/unknown, dihitung terpisah, bukan salah)."""
    cm = confusion(y, p, labels)
    n = sum(cm[g][q] for g in labels for q in labels)
    per = {}
    f1s = []
    for c in labels:
        tp = cm[c][c]
        fp = sum(cm[g][c] for g in labels if g != c)
        fn = sum(cm[c][q] for q in labels if q != c)
        prec = tp / (tp + fp) if tp + fp else float("nan")
        rec = tp / (tp + fn) if tp + fn else float("nan")
        # F1 undefined (kelas tak pernah ditebak / tak ada di gold) dihitung 0 untuk macro-F1, sesuai konvensi.
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else float("nan")
        lo, hi = wilson(tp, tp + fn)
        per[c] = {"support": tp + fn, "precision": prec, "recall": rec, "F1": f1,
                  "recall_95CI": f"{lo:.0%}-{hi:.0%}" if tp + fn else "-"}
        if tp + fn:  # kelas yang ada di gold ikut macro-F1; F1 undefined -> 0
            f1s.append(f1 if f1 == f1 else 0.0)
    correct = sum(cm[c][c] for c in labels)
    return {
        "n": n,
        "unknown": sum(1 for b in p if b is None),
        "accuracy": correct / n if n else float("nan"),
        "macro_F1": sum(f1s) / len(f1s) if f1s else float("nan"),
        "per_class": per,
        "cm": cm,
    }


def pct(x) -> str:
    return f"{x:.0%}" if isinstance(x, float) and x == x else "-"


def print_confusion(cm: dict, labels: list) -> None:
    head = "gold\\pred".ljust(10) + "".join(c[:8].rjust(9) for c in labels) + "    total"
    print(head)
    for g in labels:
        row = sum(cm[g].values())
        print(g.ljust(10) + "".join(str(cm[g][q]).rjust(9) for q in labels) + str(row).rjust(9))


# Main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold", default=str(SHARED / "gold_yt_v2.csv"))
    ap.add_argument("--video-context", default=str(SHARED / "video_context.csv"))
    ap.add_argument("--configs", nargs="+", default=["majority", "zero_shot", "v2_ctx"])
    ap.add_argument("--prompt-file", help="template prompt sendiri (pakai {{ITEMS}}); dipakai oleh config 'custom'")
    ap.add_argument("--model", default="gemma-4-26b-a4b-it")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--batch-size", type=int, help="menimpa ukuran batch semua config")
    ap.add_argument("--rpm", type=int, default=25, help="batas panggilan/menit (free tier: 30)")
    ap.add_argument("--tpm", type=int, default=13000, help="batas token/menit (free tier: 16000)")
    ap.add_argument("--min-gap", type=float, default=2.0, help="jeda minimum antar panggilan (detik)")
    ap.add_argument("--max-retries", type=int, default=6)
    ap.add_argument("--limit", type=int, help="ambil N komentar acak saja (uji coba cepat)")
    ap.add_argument("--no-resume", action="store_true", help="abaikan hasil lama, mulai dari nol")
    ap.add_argument("--no-json-mode", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="cetak prompt saja, tanpa memanggil API")
    ap.add_argument("--stub", action="store_true", help="pakai model palsu untuk menguji alur")
    ap.add_argument("--out-dir", default=str(HERE / "results"))
    args = ap.parse_args()

    global SLEEP_SCALE
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if args.stub:
        SLEEP_SCALE = 0.0
        args.model = "stub"

    cfgs = dict(CONFIGS)
    if args.prompt_file:
        cfgs["custom"] = {"template": str(Path(args.prompt_file).resolve()), "context": "full", "batch": 8}
    unknown = [c for c in args.configs if c not in cfgs]
    if unknown:
        raise SystemExit(f"config tidak dikenal: {unknown}. Pilihan: {list(cfgs)}")

    # Hanya komentar relevan yang dinilai stance (Pedoman A1). 
    # Baris stance kosong/di luar 3 kelas akan di drop.
    gold = pd.read_csv(args.gold, dtype=str, keep_default_na=False)
    gold = gold[gold["relevan"] == "1"].reset_index(drop=True)
    bad = gold[~gold["stance"].isin(STANCES)]
    if len(bad):
        print(f"! {len(bad)} komentar relevan di-drop karena stance kosong/tak dikenal: "
              + ", ".join(bad["cid"].head(10)) + (" ..." if len(bad) > 10 else ""))
        gold = gold[gold["stance"].isin(STANCES)].reset_index(drop=True)
    if args.limit:
        gold = gold.sample(min(args.limit, len(gold)), random_state=1).reset_index(drop=True)

    vctx = load_video_context(Path(args.video_context))
    items = make_items(gold, vctx)
    y = list(gold["stance"])
    dist = Counter(y)
    n_ctx = len({it["video_id"] for it in items if it["desc"]})
    print(f"gold stance: {len(gold)} komentar relevan | distribusi {dict(dist)} | "
          f"video dengan deskripsi: {n_ctx}/{gold['video_id'].nunique()} | model: {args.model}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def template_of(cfg):
        p = Path(cfg["template"])
        return (p if p.is_absolute() else HERE / "prompts" / p).read_text(encoding="utf-8")

    if args.dry_run:
        for name in args.configs:
            cfg = cfgs[name]
            if cfg.get("kind") == "majority":
                print(f"\n{'=' * 30} {name}: tanpa prompt (tebak kelas mayoritas) {'=' * 30}")
                continue
            size = args.batch_size or cfg["batch"]
            first = make_batches(items, size)[0]
            prompt = build_prompt(template_of(cfg), first, cfg["context"])
            (out_dir / f"prompt_preview_stance_{name}.txt").write_text(prompt, encoding="utf-8")
            print(f"\n{'=' * 30} {name}: batch pertama ({len(first)} komentar), ±{est_tokens(prompt)} token {'=' * 30}\n{prompt}")
        print(f"\nPratinjau disimpan di {out_dir}")
        return

    need_api = any(cfgs[c].get("kind") != "majority" for c in args.configs)
    client = throttle = None
    if need_api:
        if args.stub:
            client = StubClient()
            throttle = Throttle(10 ** 6, 10 ** 9, 0.0)
        else:
            client = GenAIClient(args.model, get_api_key(), args.temperature, json_mode=not args.no_json_mode)
            throttle = Throttle(args.rpm, args.tpm, args.min_gap)

    rows, all_preds = [], {}
    for name in args.configs:
        cfg = cfgs[name]
        if cfg.get("kind") == "majority":
            preds = run_majority(y, items)
        else:
            preds = run_api_config(name, cfg, template_of(cfg), items, client, throttle, args, out_dir)
        all_preds[name] = preds
        p = [preds[i][0] if i in preds else None for i in range(len(items))]
        m = metrics(y, p, STANCES)
        rows.append({"config": name, "n": m["n"], "unknown": m["unknown"],
                     "accuracy": m["accuracy"], "macro_F1": m["macro_F1"],
                     **{f"{c}_F1": m["per_class"][c]["F1"] for c in STANCES}})

    summary = pd.DataFrame(rows)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary.to_csv(out_dir / f"summary_stance_{stamp}.csv", index=False, encoding="utf-8")
    summary.to_csv(out_dir / "summary_stance_latest.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    fmt = {c: (lambda v: f"{v:.1%}" if isinstance(v, float) and v == v else "-")
           for c in ["accuracy", "macro_F1"] + [f"{s}_F1" for s in STANCES]}
    print("\n" + "=" * 100 + f"\nHASIL STANCE pada {len(gold)} komentar relevan (Pedoman v2) | model {args.model}\n" + "=" * 100)
    print(summary.to_string(index=False, formatters=fmt))

    # Rincian per kelas, Confusion matrix, Daftar error untuk audit annotator
    compare = gold[["cid", "target", "video_title", "text", "stance"]].copy()
    for name, preds in all_preds.items():
        p = [preds[i][0] if i in preds else None for i in range(len(items))]
        m = metrics(y, p, STANCES)
        print(f"\n--- {name}: akurasi {m['accuracy']:.1%} | macro-F1 {m['macro_F1']:.1%} | unknown {m['unknown']}")
        for c in STANCES:
            pc = m["per_class"][c]
            print(f"    {c:<8} n={pc['support']:<3} P={pct(pc['precision'])} R={pct(pc['recall'])} "
                  f"F1={pct(pc['F1'])} (recall 95%CI {pc['recall_95CI']})")
        print("  confusion matrix:")
        print_confusion(m["cm"], STANCES)

        compare[f"pred_{name}"] = p
        compare[f"alasan_{name}"] = [preds[i][2] if i in preds else "" for i in range(len(items))]
        wrong = compare[[(p[i] is not None) and (p[i] != y[i]) for i in range(len(items))]].copy()
        wrong.insert(0, "pred", [p[i] for i in range(len(items)) if p[i] is not None and p[i] != y[i]])
        wrong.to_csv(out_dir / f"errors_stance_{name}.csv", index=False, encoding="utf-8")

    compare.to_csv(out_dir / "compare_stance_all.csv", index=False, encoding="utf-8")
    print(f"\nCatatan: Neutral dominan ({dist.get('Neutral', 0)}/{len(y)}), jadi lihat macro-F1 dan F1 per kelas, "
          "bukan akurasi mentah. N kecil -> perhatikan recall_95CI.")
    print(f"File di {out_dir}: summary_stance_latest.csv, errors_stance_<config>.csv, compare_stance_all.csv, preds_stance_*.csv")


if __name__ == "__main__":
    main()
