"""
Gabungkan artikel berita dari CNN Indonesia, Detik, dan Kompas jadi satu
file dengan skema kolom yang seragam.

YouTube tidak digabung di sini karena unit datanya beda (komentar per
video, bukan artikel) - lihat crawler/youtubecomment/ untuk output-nya
sendiri.

Baca langsung dari cache/output tiap sumber (bukan mengubahnya), jadi bisa
dijalankan ulang kapan saja untuk me-refresh gabungan, termasuk saat
crawler sumber lain masih berjalan.

Jalankan dari folder ini:
    python merge_articles.py

Output: data/articles_merged.json & data/articles_merged.csv
"""

import csv
import json
from pathlib import Path
from typing import Dict, Iterator, Optional

BASE_DIR = Path(__file__).parent

CNN_CACHE = BASE_DIR / "cnnindonesia" / "cnn_energy_cache.jsonl"
DETIK_CACHE = BASE_DIR / "detik" / "data" / "detik_energy_cache.jsonl"
KOMPAS_ARTICLES = BASE_DIR / "kompas" / "data" / "articles.json"

OUT_DIR = BASE_DIR / "data"
OUT_JSON = OUT_DIR / "articles_merged.json"
OUT_CSV = OUT_DIR / "articles_merged.csv"

CSV_HEADERS = ["source", "url", "title", "date", "keyword", "target", "author", "tags", "content"]


def read_jsonl(path: Path) -> Iterator[Dict]:
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def normalize_cnn(record: Dict) -> Dict:
    return {
        "source": "cnnindonesia",
        "url": record.get("url", ""),
        "title": record.get("judul", ""),
        "date": record.get("tanggal", ""),
        "keyword": record.get("kata_kunci", ""),
        "target": record.get("target", ""),
        "author": "",
        "tags": "",
        "content": record.get("isi", ""),
    }


def normalize_detik(record: Dict) -> Dict:
    tags = record.get("tags", [])
    return {
        "source": "detik",
        "url": record.get("url", ""),
        "title": record.get("title", ""),
        "date": record.get("date", ""),
        "keyword": record.get("keyword", ""),
        "target": record.get("target", ""),
        "author": "",
        "tags": " | ".join(tags) if isinstance(tags, list) else "",
        "content": record.get("body", ""),
    }


def normalize_kompas(record: Dict) -> Dict:
    # date_raw datang dari halaman artikel (step2, lebih presisi);
    # date dari halaman pencarian (step1) dipakai sebagai fallback.
    date = record.get("date_raw") or record.get("date", "")
    return {
        "source": "kompas",
        "url": record.get("url", ""),
        "title": record.get("title", ""),
        "date": date,
        "keyword": record.get("keyword", ""),
        "target": record.get("target", ""),
        "author": record.get("author", ""),
        "tags": "",
        "content": record.get("content", ""),
    }


def load_kompas() -> Iterator[Dict]:
    if not KOMPAS_ARTICLES.exists():
        return
    with open(KOMPAS_ARTICLES, "r", encoding="utf-8") as f:
        data = json.load(f)
    for record in data:
        yield record


def merge() -> list:
    """Gabungkan ketiga sumber, dedup per (source, url) - kalau ada duplikat
    (mis. dari run sebelumnya di luar rentang tahun saat ini), yang terakhir
    di file yang menang (paling baru ditulis)."""
    merged: Dict[tuple, Dict] = {}

    for record in read_jsonl(CNN_CACHE):
        norm = normalize_cnn(record)
        merged[(norm["source"], norm["url"])] = norm

    for record in read_jsonl(DETIK_CACHE):
        norm = normalize_detik(record)
        merged[(norm["source"], norm["url"])] = norm

    for record in load_kompas():
        norm = normalize_kompas(record)
        merged[(norm["source"], norm["url"])] = norm

    return list(merged.values())


def write_outputs(records: list) -> None:
    OUT_DIR.mkdir(exist_ok=True)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def main() -> None:
    records = merge()
    write_outputs(records)

    per_source = {}
    for r in records:
        per_source[r["source"]] = per_source.get(r["source"], 0) + 1

    print(f"Total artikel gabungan: {len(records)}")
    for source, count in sorted(per_source.items()):
        print(f"  {source}: {count}")
    print(f"\nOutput: {OUT_JSON}")
    print(f"Output: {OUT_CSV}")


if __name__ == "__main__":
    main()
