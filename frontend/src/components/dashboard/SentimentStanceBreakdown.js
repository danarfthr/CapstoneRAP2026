/**
 * SentimentStanceBreakdown — Tabel per komentar/berita dengan stance dan
 * sentimennya, dibagi per halaman (pagination Back/Next).
 *
 * Jika showSentiment = false (user hanya memilih News), kartu berubah menjadi
 * "Stance Breakdown": kolom sentimen disembunyikan.
 */
"use client";

import { useState } from "react";
import { Badge, Card } from "./Card";
import styles from "./dashboard.module.css";

export default function SentimentStanceBreakdown({ data, showSentiment = true }) {
  const [page, setPage] = useState(1);
  if (!data?.data?.length) return null;

  // Jumlah halaman dihitung dari data yang benar-benar ada, supaya
  // tidak muncul halaman kosong
  const perPage = data.perPage || 4;
  const totalPages = Math.ceil(data.data.length / perPage);
  const visibleItems = data.data.slice((page - 1) * perPage, page * perPage);

  return (
    <Card title={showSentiment ? "Sentiment & Stance Breakdown" : "Stance Breakdown"}>
      <div className={styles.tableScroll}>
        <table
          className={`${styles.table} ${showSentiment ? styles.tableThreeCol : styles.tableTwoCol}`}
        >
          <thead>
            <tr>
              <th>{showSentiment ? "Comment/news" : "News"}</th>
              <th>Stance</th>
              {showSentiment && <th>Avg. Sentiment</th>}
            </tr>
          </thead>
          <tbody>
            {visibleItems.map((item, index) => (
              <tr key={`${page}-${index}`}>
                <td>{item.commentNews}</td>
                <td>
                  <Badge value={item.stance} />
                </td>
                {showSentiment && (
                  <td>
                    <Badge value={item.avgSentiment} />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className={styles.pagination}>
        <span>
          Page {page} of {totalPages}
        </span>
        <div>
          <button type="button" onClick={() => setPage(page - 1)} disabled={page === 1}>
            Back
          </button>
          <button type="button" onClick={() => setPage(page + 1)} disabled={page === totalPages}>
            Next
          </button>
        </div>
      </div>
    </Card>
  );
}
