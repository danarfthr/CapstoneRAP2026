/**
 * SentimentStanceBreakdown — Breakdown detail sentimen & stance
 * Setiap item menampilkan label, kategori, progress bar, dan nilai persentase
 */
"use client";

import { useState } from "react";

export default function SentimentStanceBreakdown({ data }) {
  const [page, setPage] = useState(1);
  if (!data?.data?.length) return null;

  const itemsPerPage = data.perPage || 4;
  const totalPages = data.totalPages || Math.ceil(data.data.length / itemsPerPage);
  const visibleItems = data.data.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  return (
    <div className="card sentiment-breakdown-card">
      <h3 className="card-title">Sentiment &amp; Stance Breakdown</h3>
      <div className="table-scroll">
        <table className="data-table breakdown-table">
          <thead><tr><th>Comment/news</th><th>Stance</th><th>Avg. Sentiment</th></tr></thead>
          <tbody>{visibleItems.map((item, index) => (
            <tr key={`${item.commentNews}-${index}`}>
              <td>{item.commentNews}</td>
              <td><span className={`stance-badge ${item.stance}`}>{item.stance}</span></td>
              <td><span className={`sentiment-badge ${item.avgSentiment}`}>{item.avgSentiment}</span></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
      <div className="pagination">
        <span>Page {page} of {totalPages}</span>
        <div>
          <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>Back</button>
          <button type="button" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page === totalPages}>Next</button>
        </div>
      </div>
    </div>
  );
}
