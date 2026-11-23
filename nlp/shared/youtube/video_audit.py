"""Audit tingkat VIDEO: seberapa besar video di luar topik/di luar rentang tahun mendominasi data komentar.

Menggabungkan konteks video (nlp/data/video_context.csv) dengan label relevansi model per komentar, lalu:
  1. menandai video di luar rentang tahun (tanggal upload dari yt-dlp; kolom ini kosong 100% di crawler),
  2. menguji gerbang sederhana berbasis judul/deskripsi/tag (topik pembangkit DAN penanda Indonesia, Pedoman B1/B6/B7),
  3. membandingkan gerbang itu dengan label manusia pada set gold.
Gerbang regex ini hanya simulasi (what-if). Versi produksi sebaiknya klasifikasi LLM atas judul+deskripsi.

Contoh (dari folder CapstoneRAP2026):
  python nlp/video_audit.py --labeled "../Dataset/Output Relevansi/relevancy_labeled.csv"
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
TOPIC = re.compile(
    r"pltn|pltu|nuklir|nuclear|reaktor|reactor|batu ?bara|batubara|coal|pembangkit|power plant|"
    r"\bplt[a-z]{1,2}\b|\bpln\b|thorium|torium|uranium", re.I)
INDO = re.compile(
    r"indonesia|\bri\b|prabowo|jokowi|bahlil|\bpln\b|\bbrin\b|bapeten|batan|esdm|nusantara|jawa|sumatra|"
    r"sumatera|kalimantan|bangka|babel|muria|jepara|paiton|suralaya|cirebon|batang|\bdpr\b|danantara|pertamina", re.I)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labeled", required=True, help="relevancy_labeled.csv (label model v1 per komentar)")
    ap.add_argument("--context", default=str(HERE / "data" / "video_context.csv"))
    ap.add_argument("--gold", default=str(HERE / "data" / "gold_yt_v2.csv"))
    ap.add_argument("--out", default=str(HERE / "data" / "video_audit.csv"))
    ap.add_argument("--start-year", type=int, default=2021)
    ap.add_argument("--end-year", type=int, default=2026)
    ap.add_argument("--mega", type=int, default=1000, help="ambang komentar untuk 'video raksasa'")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    m = pd.read_csv(args.labeled, dtype=str, keep_default_na=False,
                    usecols=["video_url", "video_title", "keyword", "cid", "comment_relevancy"])
    m["rel"] = m["comment_relevancy"].eq("True")
    m["video_id"] = m["video_url"].str.extract(r"[?&]v=([A-Za-z0-9_-]{11})")[0]
    v = m.groupby("video_id").agg(
        keyword=("keyword", lambda s: "|".join(sorted(set(s)))[:80]),
        judul_crawler=("video_title", "first"),
        komentar=("cid", "size"), relevan_model=("rel", "sum"))
    v["yield_relevan"] = v["relevan_model"] / v["komentar"]

    c = pd.read_csv(args.context, dtype=str, keep_default_na=False)
    c = c[c["status"] == "ok"].drop_duplicates("video_id").set_index("video_id")
    v = v.join(c[["title", "channel", "upload_date", "description", "tags"]], how="left")
    v["ada_konteks"] = v["title"].notna()
    v["title"] = v["title"].fillna(v["judul_crawler"])  # video tanpa konteks: pakai judul dari crawler
    v["tahun"] = pd.to_numeric(v["upload_date"].str[:4], errors="coerce")
    v["di_luar_tahun"] = (v["tahun"] < args.start_year) | (v["tahun"] > args.end_year)
    blob = (v["title"].fillna("") + " " + v["tags"].fillna("") + " " + v["description"].fillna("").str[:600])
    v["topik"] = blob.str.contains(TOPIC)
    v["indonesia"] = blob.str.contains(INDO)
    v["lolos_gerbang"] = v["topik"] & v["indonesia"]
    tot_c, tot_r = int(v["komentar"].sum()), int(v["relevan_model"].sum())

    print(f"video: {len(v)} (dengan konteks: {int(v.ada_konteks.sum())}) | komentar: {tot_c} | relevan (model v1): {tot_r} ({tot_r / tot_c:.1%})")

    out = v[v["di_luar_tahun"]]
    print(f"\n[1] Rentang tahun {args.start_year}-{args.end_year}: {len(out)} video ({out.komentar.sum()} komentar, "
          f"{out.komentar.sum() / tot_c:.1%}) diupload di luar rentang. Tahun terlama: {int(v.tahun.min())}.")
    print("    Sebaran tahun upload (video):", v["tahun"].value_counts().sort_index().astype(int).to_dict())

    mega = v[v["komentar"] >= args.mega]
    off = mega[mega["yield_relevan"] < 0.08]
    print(f"\n[2] Video raksasa (>= {args.mega} komentar): {len(mega)} video = {mega.komentar.sum() / tot_c:.0%} komentar. "
          f"Yang yield <8%: {len(off)} video = {off.komentar.sum() / tot_c:.0%} komentar tetapi hanya "
          f"{off.relevan_model.sum() / tot_r:.1%} dari komentar relevan.")
    print(f"    Dari {len(off)} video raksasa di luar topik itu, yang LOLOS gerbang regex: {int(off.lolos_gerbang.sum())} "
          f"({', '.join(off[off.lolos_gerbang].title.fillna('?').str[:40]) or '-'})")

    keep = v[v["lolos_gerbang"]]
    print(f"\n[3] Gerbang regex (topik DAN penanda Indonesia di judul/tag/deskripsi): lolos {len(keep)}/{len(v)} video")
    print(f"    komentar tersisa {keep.komentar.sum() / tot_c:.0%} | relevan (model) tersisa {keep.relevan_model.sum() / tot_r:.0%} | "
          f"yield {tot_r / tot_c:.1%} -> {keep.relevan_model.sum() / keep.komentar.sum():.1%}")
    both = v[v["lolos_gerbang"] & ~v["di_luar_tahun"]]
    print(f"    + filter tahun: komentar tersisa {both.komentar.sum() / tot_c:.0%} | relevan tersisa {both.relevan_model.sum() / tot_r:.0%} | "
          f"yield {both.relevan_model.sum() / both.komentar.sum():.1%}")

    g = pd.read_csv(args.gold, dtype=str, keep_default_na=False)
    g["relevan"] = g["relevan"].astype(int)
    g = g.merge(v[["lolos_gerbang", "di_luar_tahun"]], left_on="video_id", right_index=True, how="left")
    gr, gi = g[g.relevan == 1], g[g.relevan == 0]
    print(f"\n[4] Cek ke label manusia (gold, N={len(g)}): gerbang meloloskan {int((gr.lolos_gerbang == True).sum())}/{len(gr)} "
          f"komentar relevan ({(gr.lolos_gerbang == True).mean():.0%}) dan membuang {int((gi.lolos_gerbang != True).sum())}/{len(gi)} "
          f"komentar tidak relevan ({(gi.lolos_gerbang != True).mean():.0%}).")
    lost = gr[gr.lolos_gerbang != True]
    for _, r in lost.head(6).iterrows():
        print(f"    relevan tapi terbuang: «{r['text'][:60]}» | video: {r['video_title'][:55]}")

    cols = ["keyword", "title", "channel", "upload_date", "komentar", "relevan_model", "yield_relevan",
            "topik", "indonesia", "lolos_gerbang", "di_luar_tahun"]
    v.reset_index().sort_values("komentar", ascending=False)[["video_id"] + cols].round(3).to_csv(
        args.out, index=False, encoding="utf-8")
    print(f"\nTabel per video -> {args.out}")


if __name__ == "__main__":
    main()
