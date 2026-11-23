/**
 * dataset.js — Logika filter & export untuk halaman Data View (/data).
 *
 * Bentuk baris data (dari /api/dataset):
 *   youtube : { text, videoTitle, videoUrl, stance, sentiment }
 *   news    : { title, source, actors: [], stance, evidence }
 *
 * Catatan: berita tidak punya sentimen, jadi kalau filter sentimen dipilih
 * (selain "All Sentiments"), tabel News ikut kosong.
 */

export const SENTIMENT_FILTERS = [
  { value: "all", label: "All Sentiments" },
  { value: "positive", label: "Positive" },
  { value: "neutral", label: "Neutral" },
  { value: "negative", label: "Negative" },
];

export const STANCE_FILTERS = [
  { value: "all", label: "All Stances" },
  { value: "support", label: "Support" },
  { value: "neutral", label: "Neutral" },
  { value: "oppose", label: "Oppose" },
];

export const EMPTY_DATASET_FILTER = { search: "", sentiment: "all", stance: "all" };

/** Teks yang dicari oleh kotak search, per platform. */
const SEARCHABLE_FIELDS = {
  youtube: (row) => [row.text, row.videoTitle],
  news: (row) => [row.title, row.source, row.actors.join(" "), row.evidence],
};

/** Saring baris satu platform berdasarkan search, sentimen, dan stance. */
export function filterRows(rows = [], platform, filter) {
  const keyword = filter.search.trim().toLowerCase();

  return rows.filter((row) => {
    if (filter.stance !== "all" && row.stance !== filter.stance) return false;
    if (filter.sentiment !== "all" && row.sentiment !== filter.sentiment) return false;
    if (!keyword) return true;
    return SEARCHABLE_FIELDS[platform](row).some((value) =>
      String(value ?? "").toLowerCase().includes(keyword)
    );
  });
}

// ---------------------------------------------------------------------------
// Export CSV
// ---------------------------------------------------------------------------

const CSV_HEADER = [
  "type",
  "platform",
  "text",
  "source",
  "source_url",
  "actor",
  "stance",
  "sentiment",
  "evidence",
];

/** Satu baris data → kolom CSV (kolom yang tidak berlaku dibiarkan kosong). */
const toCsvColumns = {
  youtube: (type, row) => [
    type,
    "YouTube",
    row.text,
    row.videoTitle,
    row.videoUrl,
    "",
    row.stance,
    row.sentiment,
    "",
  ],
  news: (type, row) => [
    type,
    "News",
    row.title,
    row.source,
    "",
    row.actors.join(", "),
    row.stance,
    "",
    row.evidence,
  ],
};

const escapeCsv = (value) => {
  const text = String(value ?? "");
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};

/**
 * Buat isi CSV dari blok yang sedang tampil.
 * blocks: [{ type: "PLTU", platform: "youtube", rows: [...] }]
 */
export function buildCsv(blocks) {
  const lines = [CSV_HEADER];
  blocks.forEach(({ type, platform, rows }) => {
    rows.forEach((row) => lines.push(toCsvColumns[platform](type, row)));
  });
  return lines.map((columns) => columns.map(escapeCsv).join(",")).join("\r\n");
}

/** Unduh teks CSV sebagai file (BOM supaya Excel membaca UTF-8 dengan benar). */
export function downloadCsv(csv, filename) {
  const blob = new Blob(["﻿", csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
