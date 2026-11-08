/**
 * DatasetSection — Satu blok Data View untuk satu jenis pembangkit (PLTU / PLTN):
 * judul + total corpus, bar filter, lalu tabel per platform yang dipilih.
 *
 *   Platform dipilih  | Tabel           | Dropdown Sentiment
 *   ------------------|-----------------|-------------------
 *   YouTube + News    | YouTube, News   | tampil (News ikut kosong kalau sentimen dipilih,
 *                     |                 |         karena berita tidak punya sentimen)
 *   YouTube saja      | YouTube         | tampil
 *   News saja         | News            | disembunyikan (berita tidak punya sentimen)
 */
"use client";

import { Badge } from "@/components/dashboard/Card";
import { SENTIMENT_FILTERS, STANCE_FILTERS, EMPTY_DATASET_FILTER, filterRows } from "@/lib/dataset";
import DatasetTable from "./DatasetTable";
import styles from "./dataview.module.css";

/** Pengaturan tabel per platform (key = value di PLATFORMS). */
const TABLES = {
  youtube: {
    title: "Youtube",
    subtitle: "Direct public discussions & user commentaries collected across key energy streams",
    tone: "youtube",
    columns: [
      { header: "Text", width: "48%", render: (row) => row.text },
      {
        header: "Source",
        width: "22%",
        render: (row) => (
          <div className={styles.videoSource}>
            <a href={row.videoUrl} target="_blank" rel="noopener noreferrer" className={styles.chip}>
              Link Source
            </a>
            <span className={styles.videoTitle}>&ldquo;{row.videoTitle}&rdquo;</span>
          </div>
        ),
      },
      {
        header: "Stance",
        width: "15%",
        align: "center",
        render: (row) => <Badge value={row.stance} className={styles.badge} />,
      },
      {
        header: "Sentiment",
        width: "15%",
        align: "center",
        render: (row) => <Badge value={row.sentiment} className={styles.badge} />,
      },
    ],
  },
  news: {
    title: "News",
    subtitle: "Mainstream press coverage, actor entity mappings, and verbatim contextual evidence",
    tone: "news",
    columns: [
      {
        header: "Text",
        width: "25%",
        render: (row) => <span className={styles.newsTitle}>{row.title}</span>,
      },
      {
        header: "Src",
        width: "13%",
        render: (row) => <span className={styles.sourceChip}>{row.source}</span>,
      },
      { header: "Actor", width: "18%", render: (row) => row.actors.join(", ") },
      {
        header: "Stance",
        width: "10%",
        align: "center",
        render: (row) => <Badge value={row.stance} className={styles.badge} />,
      },
      {
        header: "Evidence",
        width: "34%",
        className: styles.evidenceCell,
        render: (row) => <span className={styles.evidence}>&ldquo;{row.evidence}&rdquo;</span>,
      },
    ],
  },
};

export default function DatasetSection({
  type,
  data,
  platforms,
  filter,
  onFilterChange,
  sectionRef,
}) {
  if (!data) return null;

  const hasYoutube = platforms.some((platform) => platform.value === "youtube");
  const totalCorpus = platforms.reduce(
    (total, platform) => total + (data[platform.value]?.length ?? 0),
    0
  );
  // Ganti halaman tabel ke 1 setiap kali filter berubah
  const filterKey = `${filter.search}|${filter.sentiment}|${filter.stance}`;

  const update = (field) => (event) => onFilterChange({ ...filter, [field]: event.target.value });

  return (
    <section id={type.value} ref={sectionRef} className={styles.section}>
      {/* Judul dataset + total corpus */}
      <div className={styles.datasetHeader}>
        <div>
          <span className={styles.activeTag}>Active Dataset</span>
          <h2 className={styles.datasetTitle}>{type.label} Public Dataset &amp; Annotations</h2>
          <p className={styles.datasetDescription}>
            Granular inspection of multi-platform social listening data. Structured layout
            displaying annotated YouTube comment threads and verified news publisher items
            categorized by NLP stance and sentiment models.
          </p>
        </div>
        <div className={styles.corpusBox}>
          <span className={styles.corpusLabel}>Total Corpus</span>
          <p>
            <strong>{totalCorpus.toLocaleString("en-US")}</strong> records
          </p>
        </div>
      </div>

      {/* Bar filter */}
      <div className={styles.filterBar}>
        <label className={styles.searchBox}>
          <SearchIcon />
          <span className="sr-only">Search {type.label} dataset</span>
          <input
            type="search"
            value={filter.search}
            onChange={update("search")}
            placeholder="Search by text, entity actor (e.g. Prabowo, Bahlil), or source..."
          />
        </label>

        {hasYoutube && (
          <label className={styles.filterSelect}>
            <span>Sentiment:</span>
            <select value={filter.sentiment} onChange={update("sentiment")}>
              {SENTIMENT_FILTERS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        )}

        <label className={styles.filterSelect}>
          <span>Stance:</span>
          <select value={filter.stance} onChange={update("stance")}>
            {STANCE_FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className={styles.resetButton}
          onClick={() => onFilterChange(EMPTY_DATASET_FILTER)}
        >
          Reset Filters
        </button>
      </div>

      {/* Tabel per platform yang dipilih */}
      {platforms.map((platform) => (
        <DatasetTable
          key={platform.value}
          resetKey={filterKey}
          {...TABLES[platform.value]}
          rows={filterRows(data[platform.value], platform.value, filter)}
        />
      ))}
    </section>
  );
}

function SearchIcon() {
  return (
    <svg className={styles.searchIcon} width="15" height="15" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="M20 20l-3.5-3.5" />
    </svg>
  );
}
