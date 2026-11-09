"""Evaluasi relevansi komentar YouTube: prompt v1 (lama) vs v2 (Pedoman Anotasi v2), dengan/tanpa konteks video.

Yang diperbaiki dibanding notebook lama:
  * Panggilan API gagal (500/429/JSON rusak) di-retry; jika tetap gagal hasilnya 'unknown', TIDAK dianggap False.
  * Parser JSON toleran terhadap ```json ... ``` dan sisa teks di belakang JSON.
  * Model, suhu, ukuran batch, dan prompt tidak hardcoded: prompt ada di nlp/prompts/*.txt.
  * Batch dikelompokkan per video sehingga judul/deskripsi video cukup ditulis sekali.
  * Hasil berupa confusion matrix, recall/presisi/F1 kelas relevan (+ selang kepercayaan), dan daftar error.

Contoh (dari folder CapstoneRAP2026):
  python nlp/relevance_v2.py --dry-run                         # hanya lihat prompt, tanpa API
  python nlp/relevance_v2.py                                   # v1_title, v2_title, v2_ctx pada set gold
  python nlp/relevance_v2.py --configs v2_ctx --model gemini-2.5-flash --rpm 100 --tpm 200000
  python nlp/relevance_v2.py --prompt-file nlp/prompts/prompt_saya.txt --configs custom

API key dibaca dari environment variable GEMMA / GOOGLE_API_KEY / GEMINI_API_KEY, atau dari Colab Secrets
bernama GEMMA. Di Colab: !pip install -q google-genai
"""
import argparse
import json
import math
import os
import re
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SLEEP_SCALE = 1.0  # 0 saat --stub supaya uji alur tidak menunggu

CONFIGS = {
    # prompt lama apa adanya (judul video saja), batch 20 seperti di notebook
    "v1_title": {"template": "relevance_youtube_v1.txt", "style": "v1", "context": "title", "batch": 20},
    # prompt baru berbasis Pedoman v2, hanya judul video -> mengukur efek prompt saja
    "v2_title": {"template": "relevance_youtube_v2.txt", "style": "v2", "context": "title", "batch": 8},
    # prompt baru + judul + channel + deskripsi + tag -> mengukur tambahan efek konteks video
    "v2_ctx": {"template": "relevance_youtube_v2.txt", "style": "v2", "context": "full", "batch": 8},
}


def pause(sec: float) -> None:
    time.sleep(sec * SLEEP_SCALE)


# Data
URL_RE = re.compile(r"https?://\S+|www\.\S+")
EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
HASH_RE = re.compile(r"#\w+")
TS_RE = re.compile(r"^\(?\d{1,2}:\d{2}(?::\d{2})?\)?\s*[-:–—]?")
NOISE_RE = re.compile(
    r"subscribe|follow|instagram|facebook|twitter|tiktok|whatsapp|business|sponsor|endorse|donasi|"
    r"support us|join (this )?channel|copyright|all rights reserved", re.I)


def clean_description(desc: str, max_chars: int = 450) -> str:
    """Buang URL, timestamp bab, hashtag, email, dan baris promosi; potong di batas kata."""
    keep = []
    for ln in (desc or "").replace("\r", "").split("\n"):
        ln = EMAIL_RE.sub(" ", HASH_RE.sub(" ", URL_RE.sub(" ", ln)))
        ln = re.sub(r"\s+", " ", ln).strip()
        if not ln or TS_RE.match(ln) or (NOISE_RE.search(ln) and len(ln) < 90):
            continue
        keep.append(ln)
    text = " ".join(keep)
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "..."
    return text


def load_video_context(path: Path) -> dict:
    if not path.exists():
        print(f"! {path} tidak ada -> konteks video hanya judul. Jalankan nlp/fetch_video_context.py dulu.")
        return {}
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df = df[df["status"] == "ok"]
    out = {}
    for r in df.itertuples(index=False):
        out[r.video_id] = {
            "title": r.title,
            "channel": r.channel,
            "desc": clean_description(r.description),
            "tags": ", ".join([t for t in r.tags.split("|") if t][:6]),
        }
    return out


def make_items(gold: pd.DataFrame, vctx: dict) -> list:
    items = []
    for i, r in enumerate(gold.itertuples(index=False)):
        v = vctx.get(r.video_id, {})
        items.append({
            "i": i,
            "cid": r.cid,
            "text": re.sub(r"\s+", " ", str(r.text)).strip()[:600],
            "is_reply": bool(int(r.is_reply)),
            "video_id": r.video_id,
            "title": v.get("title") or r.video_title,
            "channel": v.get("channel", ""),
            "desc": v.get("desc", ""),
            "tags": v.get("tags", ""),
        })
    return items


# Prompt
def render_items(items: list, style: str, context: str) -> str:
    if style == "v1":
        return "\n".join(f"ID: {it['i']} | Title: {it['title']} | Comment: {it['text']}" for it in items)
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
            out.append(f"[{it['i']}] ({'reply' if it['is_reply'] else 'komentar'}) {it['text']}")
    return "\n".join(out)


def build_prompt(template: str, items: list, style: str, context: str) -> str:
    return template.replace("{{ITEMS}}", render_items(items, style, context))


def est_tokens(prompt: str) -> int:
    return int(len(prompt) / 3.0) + 350  # +350 untuk cadangan keluaran


def make_batches(items: list, size: int, style: str) -> list:
    seq = sorted(items, key=lambda x: (x["video_id"], x["i"])) if style == "v2" else items
    return [seq[k:k + size] for k in range(0, len(seq), size)]


# Parsing
FENCE_RE = re.compile(r"```(?:json)?", re.I)


def _to_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "ya", "yes", "relevan", "1"):
            return True
        if s in ("false", "tidak", "no", "tidak relevan", "irrelevant", "0"):
            return False
    return None


def parse_response(text: str, expected: set) -> dict:
    """{id: (relevan, alasan)} untuk id yang diminta. Toleran terhadap pagar ```, teks pembuka,
    dan karakter sisa di belakang JSON (penyebab error 'trailing characters' di notebook lama)."""
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
            val = _to_bool(it.get("relevan", it.get("relevancy", it.get("relevant"))))
            if i in expected and val is not None:
                out[i] = (val, str(it.get("alasan", ""))[:160])
        if out:
            return out
    return {}


# API
class FatalAPIError(RuntimeError):
    """Kesalahan yang tidak ada gunanya di-retry (API key salah, izin ditolak)."""


class Throttle:
    """Menjaga RPM dan TPM (free tier AI Studio: 30 RPM, 16k TPM) supaya tidak kena 429."""

    def __init__(self, rpm: int, tpm: int, min_gap: float):
        self.rpm, self.tpm, self.min_gap = rpm, tpm, min_gap
        self.calls: deque = deque()
        self.last = 0.0

    def wait(self, tokens: int) -> None:
        tokens = min(tokens, self.tpm)
        while True:
            now = time.time()
            while self.calls and now - self.calls[0][0] > 60:
                self.calls.popleft()
            used = sum(t for _, t in self.calls)
            if len(self.calls) < self.rpm and used + tokens <= self.tpm and now - self.last >= self.min_gap:
                break
            time.sleep(0.5)
        self.last = time.time()
        self.calls.append((self.last, tokens))


class GenAIClient:
    def __init__(self, model: str, api_key: str, temperature: float, json_mode: bool = True):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise SystemExit("Paket google-genai belum terpasang. Jalankan: pip install -q google-genai")
        self.types = types
        self.client = genai.Client(api_key=api_key)
        self.model, self.temperature, self.json_mode = model, temperature, json_mode
        self.calls = 0

    def generate(self, prompt: str) -> str:
        kwargs = {"temperature": self.temperature}
        if self.json_mode:
            kwargs["response_mime_type"] = "application/json"
        self.calls += 1
        try:
            resp = self.client.models.generate_content(
                model=self.model, contents=prompt, config=self.types.GenerateContentConfig(**kwargs))
        except Exception as e:
            msg = str(e)
            if re.search(r"API key|API_KEY_INVALID|UNAUTHENTICATED|PERMISSION_DENIED|\b401\b|\b403\b", msg):
                raise FatalAPIError(msg[:300])
            if self.json_mode and re.search(r"mime|json mode|response_schema", msg, re.I) and "429" not in msg:
                print("  ! model ini tidak mendukung JSON mode; lanjut tanpa JSON mode")
                self.json_mode = False
                return self.generate(prompt)
            raise
        return resp.text or ""


class StubClient:
    """Model palsu untuk menguji alur tanpa API: aturan kata kunci sederhana + kegagalan yang sengaja disuntik
    (error 500, JSON berpagar ``` dengan sisa teks, jawaban parsial)."""
    TOPIC = re.compile(r"pltn|pltu|nuklir|nuclear|batu ?bara|reaktor|pembangkit", re.I)

    def __init__(self):
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if self.calls % 5 == 0:
            raise RuntimeError("500 INTERNAL. Internal error encountered.")
        rows = re.findall(r"^\[(\d+)\] \((?:komentar|reply)\) (.*)$", prompt, re.M)
        rows += re.findall(r"^ID: (\d+) \| Title: .*? \| Comment: (.*)$", prompt, re.M)
        res = [{"id": int(a), "alasan": "stub", "relevan": bool(self.TOPIC.search(b))} for a, b in rows]
        if self.calls % 7 == 0:
            return "```json\n" + json.dumps(res) + "\n```\nSemoga membantu"
        if self.calls % 11 == 0 and len(res) > 1:
            res = res[:-1]
        return json.dumps(res)


def get_api_key() -> str:
    for name in ("GEMMA", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
        if os.environ.get(name):
            return os.environ[name]
    try:
        from google.colab import userdata  # hanya ada di Colab
        return userdata.get("GEMMA")
    except Exception:
        raise SystemExit("API key tidak ditemukan. Set environment variable GEMMA (atau GOOGLE_API_KEY), "
                         "atau simpan di Colab Secrets dengan nama GEMMA. Jangan tempel key di chat/kode.")


def backoff_seconds(err: Exception, attempt: int) -> float:
    if re.search(r"429|RESOURCE_EXHAUSTED|quota", str(err), re.I):
        return 30 + 10 * attempt
    return min(5 * (2 ** attempt), 60)


# Run
def classify_batch(client, throttle, template, style, context, batch, max_retries, tag):
    """Mengembalikan ({i: (relevan, alasan)}, jumlah_error). Item yang tetap gagal TIDAK ada di hasil."""
    got, pending, attempt, errs = {}, list(batch), 0, 0
    while pending and attempt <= max_retries:
        prompt = build_prompt(template, pending, style, context)
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
        if pending:  # jawaban parsial: ulangi hanya yang hilang
            attempt += 1
    return got, errs


def preds_path(out_dir: Path, config: str, model: str) -> Path:
    return out_dir / f"preds_{config}__{re.sub(r'[^A-Za-z0-9._-]', '_', model)}.csv"


def load_preds(path: Path) -> dict:
    if not path.exists():
        return {}
    d = pd.read_csv(path, dtype=str, keep_default_na=False)
    return {int(r.i): (r.pred == "1", r.alasan) for r in d.itertuples(index=False) if r.pred in ("0", "1")}


def save_preds(path: Path, items: list, preds: dict) -> None:
    rows = [{"i": it["i"], "cid": it["cid"], "pred": ("" if it["i"] not in preds else int(preds[it["i"]][0])),
             "alasan": preds.get(it["i"], (None, ""))[1]} for it in items]
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


def run_config(name, cfg, template, items, client, throttle, args, out_dir):
    path = preds_path(out_dir, name, args.model)
    preds = {} if args.no_resume else load_preds(path)
    todo = [it for it in items if it["i"] not in preds]
    size = args.batch_size or cfg["batch"]
    batches = make_batches(todo, size, cfg["style"])
    print(f"\n[{name}] {len(items)} komentar | sudah ada {len(preds)} | batch {size} -> {len(batches)} panggilan")
    errs_total = 0
    for n, b in enumerate(batches, 1):
        got, errs = classify_batch(client, throttle, template, cfg["style"], cfg["context"], b,
                                   args.max_retries, f"{name} b{n}")
        preds.update(got)
        errs_total += errs
        save_preds(path, items, preds)
        print(f"  batch {n}/{len(batches)}: {len(got)}/{len(b)} terbaca" + (f" ({errs} error/ulang)" if errs else ""))
    return preds, errs_total


# Metrics
def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return float("nan"), float("nan")
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def metrics(y: list, p: list) -> dict:
    """y: 1/0 gold; p: True/False/None (None = gagal/unknown, dihitung terpisah, bukan False)."""
    pairs = [(a, b) for a, b in zip(y, p) if b is not None]
    tp = sum(1 for a, b in pairs if a and b)
    fn = sum(1 for a, b in pairs if a and not b)
    fp = sum(1 for a, b in pairs if not a and b)
    tn = sum(1 for a, b in pairs if not a and not b)
    n = tp + fn + fp + tn

    def div(a, b):
        return a / b if b else float("nan")

    rec, spec, prec = div(tp, tp + fn), div(tn, tn + fp), div(tp, tp + fp)
    out = {"n": n, "unknown": sum(1 for b in p if b is None), "TP": tp, "FN": fn, "FP": fp, "TN": tn,
           "accuracy": div(tp + tn, n), "recall": rec, "precision": prec, "specificity": spec,
           "F1": div(2 * tp, 2 * tp + fp + fn)}
    lo, hi = wilson(tp, tp + fn)
    out["recall_95CI"] = f"{lo:.0%}-{hi:.0%}"
    lo, hi = wilson(tn, tn + fp)
    out["spec_95CI"] = f"{lo:.0%}-{hi:.0%}"
    for pi in (0.2, 0.3):  # presisi bila di data asli hanya 20%/30% yang relevan (set gold 80% relevan)
        out[f"prec@{int(pi * 100)}%"] = div(rec * pi, rec * pi + (1 - spec) * (1 - pi)) if rec == rec and spec == spec else float("nan")
    return out


# Main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold", default=str(HERE / "data" / "gold_yt_v2.csv"))
    ap.add_argument("--video-context", default=str(HERE / "data" / "video_context.csv"))
    ap.add_argument("--configs", nargs="+", default=["v1_title", "v2_title", "v2_ctx"])
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
        cfgs["custom"] = {"template": str(Path(args.prompt_file).resolve()), "style": "v2", "context": "full", "batch": 8}
    unknown = [c for c in args.configs if c not in cfgs]
    if unknown:
        raise SystemExit(f"config tidak dikenal: {unknown}. Pilihan: {list(cfgs)}")

    gold = pd.read_csv(args.gold, dtype=str, keep_default_na=False)
    if args.limit:
        gold = gold.sample(min(args.limit, len(gold)), random_state=1).reset_index(drop=True)
    vctx = load_video_context(Path(args.video_context))
    items = make_items(gold, vctx)
    y = [int(v) for v in gold["relevan"]]
    n_ctx = sum(1 for it in items if it["desc"])
    print(f"gold: {len(gold)} komentar ({sum(y)} relevan) | video dengan deskripsi: "
          f"{len({it['video_id'] for it in items if it['desc']})}/{gold['video_id'].nunique()} | model: {args.model}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def template_of(cfg):
        p = Path(cfg["template"])
        return (p if p.is_absolute() else HERE / "prompts" / p).read_text(encoding="utf-8")

    if args.dry_run:
        for name in args.configs:
            cfg = cfgs[name]
            size = args.batch_size or cfg["batch"]
            first = make_batches(items, size, cfg["style"])[0]
            prompt = build_prompt(template_of(cfg), first, cfg["style"], cfg["context"])
            (out_dir / f"prompt_preview_{name}.txt").write_text(prompt, encoding="utf-8")
            print(f"\n{'=' * 30} {name}: batch pertama ({len(first)} komentar), ±{est_tokens(prompt)} token {'=' * 30}\n{prompt}")
        print(f"\nPratinjau disimpan di {out_dir}")
        return

    if args.stub:
        client = StubClient()
    else:
        client = GenAIClient(args.model, get_api_key(), args.temperature, json_mode=not args.no_json_mode)
    throttle = Throttle(10 ** 6, 10 ** 9, 0.0) if args.stub else Throttle(args.rpm, args.tpm, args.min_gap)

    rows, all_preds = [], {}
    if "v1_original" in gold:
        rows.append({"config": "v1_original (run lama, 70k)", **metrics(y, [bool(int(v)) for v in gold["v1_original"]])})
    for name in args.configs:
        cfg = cfgs[name]
        preds, errs = run_config(name, cfg, template_of(cfg), items, client, throttle, args, out_dir)
        all_preds[name] = preds
        rows.append({"config": name, **metrics(y, [preds[i][0] if i in preds else None for i in range(len(items))])})

    summary = pd.DataFrame(rows)
    cols = ["config", "n", "unknown", "TP", "FN", "FP", "TN", "accuracy", "recall", "recall_95CI", "precision",
            "specificity", "spec_95CI", "F1", "prec@20%", "prec@30%"]
    summary = summary[cols]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary.to_csv(out_dir / f"summary_{stamp}.csv", index=False, encoding="utf-8")
    summary.to_csv(out_dir / "summary_latest.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    fmt = {c: "{:.1%}".format for c in ["accuracy", "recall", "precision", "specificity", "F1", "prec@20%", "prec@30%"]}
    print("\n" + "=" * 100 + f"\nHASIL pada {len(gold)} komentar gold (Pedoman v2) | model {args.model}\n" + "=" * 100)
    print(summary.to_string(index=False, formatters=fmt))
    print("\nCatatan: set gold 80% relevan karena dirancang seimbang per kelas stance; gunakan recall/spesifisitas, "
          "dan kolom prec@20%/30% untuk perkiraan presisi di data asli.")

    # Daftar error + tabel perbandingan untuk audit annotator
    compare = gold[["cid", "video_title", "text", "stance", "relevan"]].copy()
    for name, preds in all_preds.items():
        compare[f"pred_{name}"] = [int(preds[i][0]) if i in preds else "" for i in range(len(items))]
        compare[f"alasan_{name}"] = [preds[i][1] if i in preds else "" for i in range(len(items))]
        wrong = compare[[(i in preds) and (int(preds[i][0]) != int(y[i])) for i in range(len(items))]].copy()
        wrong.insert(0, "jenis", ["FN" if int(v) == 1 else "FP" for v in wrong["relevan"]])
        wrong.to_csv(out_dir / f"errors_{name}.csv", index=False, encoding="utf-8")
    compare.to_csv(out_dir / "compare_all.csv", index=False, encoding="utf-8")
    print(f"\nFile di {out_dir}: summary_latest.csv, errors_<config>.csv, compare_all.csv, preds_<config>__*.csv")


if __name__ == "__main__":
    main()
