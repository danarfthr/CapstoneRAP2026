/**
 * DatasetTable — Kartu tabel Data View (YouTube / News) dengan jumlah entri,
 * pilihan jumlah baris per halaman (5 / 10 / 25 / All), dan pagination Back/Next.
 *
 * Props:
 * - title, subtitle : judul & keterangan kartu
 * - tone            : warna titik di label jumlah entri ("youtube" | "news")
 * - rows            : baris yang sudah difilter
 * - columns         : [{ header, width, align, className, render(row) }]
 * - resetKey        : kalau berubah (filter diganti), kembali ke halaman 1;
 *                     pilihan rows per page tetap dipertahankan
 */
"use client";

import { useState } from "react";
import styles from "./dataview.module.css";

/** Pilihan jumlah baris per halaman ("all" = semua baris di satu halaman). */
const PER_PAGE_OPTIONS = [
  { value: "5", label: "5" },
  { value: "10", label: "10" },
  { value: "25", label: "25" },
  { value: "all", label: "All" },
];

export default function DatasetTable({ title, subtitle, tone, rows, columns, resetKey }) {
  const [page, setPage] = useState(1);
  const [perPageOption, setPerPageOption] = useState(PER_PAGE_OPTIONS[0].value);

  // Filter berubah → kembali ke halaman 1
  const [lastResetKey, setLastResetKey] = useState(resetKey);
  if (resetKey !== lastResetKey) {
    setLastResetKey(resetKey);
    setPage(1);
  }

  const perPage = perPageOption === "all" ? Math.max(rows.length, 1) : Number(perPageOption);
  const totalPages = Math.max(1, Math.ceil(rows.length / perPage));
  const visibleRows = rows.slice((page - 1) * perPage, page * perPage);

  const changePerPage = (event) => {
    setPerPageOption(event.target.value);
    setPage(1);
  };

  return (
    <div className={styles.tableCard}>
      <div className={styles.tableHeading}>
        <div>
          <h3 className={styles.tableTitle}>{title}</h3>
          <p className={styles.tableSubtitle}>{subtitle}</p>
        </div>
        <span className={styles.entryCount}>
          <span className={styles.entryDot} data-tone={tone} aria-hidden="true" />
          {rows.length.toLocaleString("en-US")} Total Entries
        </span>
      </div>

      <div className={styles.tableScroll}>
        <table className={styles.table} data-tone={tone}>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.header} style={{ width: column.width }} data-align={column.align}>
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRows.length ? (
              visibleRows.map((row) => (
                <tr key={row.id}>
                  {columns.map((column) => (
                    <td key={column.header} data-align={column.align} className={column.className}>
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className={styles.emptyCell}>
                  No entries match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className={styles.pagination}>
        <span>
          Page {page} of {totalPages}
        </span>
        <div className={styles.paginationControls}>
          <label className={styles.perPageSelect}>
            <span>Rows per page:</span>
            <select value={perPageOption} onChange={changePerPage}>
              {PER_PAGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={() => setPage(page - 1)} disabled={page === 1}>
            Back
          </button>
          <button type="button" onClick={() => setPage(page + 1)} disabled={page === totalPages}>
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
