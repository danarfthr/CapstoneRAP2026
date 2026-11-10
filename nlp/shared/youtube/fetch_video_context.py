"""Ambil konteks video YouTube (deskripsi, tanggal upload, tags, kategori) lewat yt-dlp.

Dua kegunaan:
  1. Memberi konteks video ke model relevansi komentar (judul saja sering tidak cukup).
  2. Mengisi video_upload_date yang kosong 100% di crawler (extract_flat tidak mengembalikannya),
     sehingga filter rentang tahun bisa benar-benar bekerja.

Contoh (jalankan dari folder CapstoneRAP2026):
  python nlp/fetch_video_context.py --input nlp/data/gold_yt_v2.csv
  python nlp/fetch_video_context.py --input nlp/data/gold_yt_v2.csv "<path>/relevancy_labeled.csv"

Input boleh lebih dari satu; video dari input pertama diambil lebih dulu. CSV input cukup punya
kolom video_url atau video_id (video_id di file raw bisa rusak '#NAME?', jadi URL diutamakan).
Hasil di nlp/data/video_context.csv. Aman dijalankan ulang: video yang sudah berhasil dilewati.
"""
import argparse
import csv
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from yt_dlp import YoutubeDL

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "data" / "video_context.csv"
FIELDS = [
    "video_id", "video_url", "title", "channel", "channel_id", "upload_date", "duration",
    "view_count", "categories", "tags", "description", "status", "error", "fetched_at",
]
ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")


def collect_ids(path: str) -> list[str]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False,
                     usecols=lambda c: c in ("video_url", "video_id"))
    ids: list[str] = []
    if "video_url" in df:
        ids += df["video_url"].str.extract(r"[?&]v=([A-Za-z0-9_-]{11})")[0].dropna().tolist()
    if "video_id" in df:
        ids += [v for v in df["video_id"] if ID_RE.fullmatch(v or "")]
    return list(dict.fromkeys(ids))


def load_done(out: Path) -> set[str]:
    if not out.exists():
        return set()
    done = pd.read_csv(out, dtype=str, keep_default_na=False)
    return set(done.loc[done["status"] == "ok", "video_id"])


def fetch_one(ydl: YoutubeDL, vid: str) -> dict:
    url = f"https://www.youtube.com/watch?v={vid}"
    row = {k: "" for k in FIELDS}
    row.update(video_id=vid, video_url=url, fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    try:
        info = ydl.extract_info(url, download=False)
    except Exception as e:  # video privat/dihapus, kena rate limit, dsb.
        row.update(status="error", error=f"{type(e).__name__}: {str(e)[:200]}")
        return row
    if not info:
        row.update(status="error", error="tidak ada info")
        return row
    if not (info.get("channel") or info.get("uploader") or info.get("upload_date")):
        # yt-dlp mengembalikan placeholder ("youtube video #id") untuk video yang dihapus/privat/dibatasi
        row.update(status="empty", error="metadata kosong (video dihapus/privat/dibatasi?)")
        return row
    row.update(
        title=info.get("title") or "",
        channel=info.get("channel") or info.get("uploader") or "",
        channel_id=info.get("channel_id") or "",
        upload_date=info.get("upload_date") or "",
        duration=info.get("duration") or "",
        view_count=info.get("view_count") or "",
        categories="|".join(info.get("categories") or []),
        tags="|".join(info.get("tags") or []),
        description=(info.get("description") or "").replace("\r", ""),
        status="ok",
    )
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", nargs="+", required=True, help="CSV dengan kolom video_url / video_id")
    ap.add_argument("--output", default=str(DEFAULT_OUT))
    ap.add_argument("--limit", type=int, default=None, help="hanya N video pertama (untuk uji coba)")
    ap.add_argument("--sleep", type=float, default=0.8, help="jeda antar video (detik)")
    args = ap.parse_args()

    ids: list[str] = []
    for p in args.input:
        ids += collect_ids(p)
    ids = list(dict.fromkeys(ids))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = load_done(out)
    todo = [v for v in ids if v not in done][: args.limit]
    print(f"video unik: {len(ids)} | sudah ok: {len(done)} | diambil sekarang: {len(todo)}", flush=True)

    opts = {
        "quiet": True, "no_warnings": True, "skip_download": True,
        "ignore_no_formats_error": True,  # kita hanya butuh metadata, bukan stream
        "socket_timeout": 20, "retries": 3,
    }
    new_file = not out.exists()
    n_ok = n_err = 0
    with YoutubeDL(opts) as ydl, open(out, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, quoting=csv.QUOTE_ALL)
        if new_file:
            w.writeheader()
        for i, vid in enumerate(todo, 1):
            row = fetch_one(ydl, vid)
            w.writerow(row)
            f.flush()
            if row["status"] == "ok":
                n_ok += 1
            else:
                n_err += 1
            if i % 10 == 0 or i == len(todo):
                print(f"[{i}/{len(todo)}] ok={n_ok} error={n_err} | terakhir: {row['title'][:50] or row['error'][:60]}", flush=True)
            time.sleep(args.sleep)
    print(f"selesai. ok={n_ok} error={n_err} -> {out}")


if __name__ == "__main__":
    sys.exit(main())
