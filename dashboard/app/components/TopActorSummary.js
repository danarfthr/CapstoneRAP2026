/**
 * TopActorSummary — Tabel ringkasan aktor teratas di berita
 * Menampilkan nama aktor dan label sentimen (badge warna)
 */
"use client";

import { useState } from "react";

export default function TopActorSummary({ data }) {
  const [sentiment, setSentiment] = useState("negative");
  if (!data) return null;

  const actors = data[sentiment] || [];

  return (
    <div className="card summary-card">
      <div className="card-heading">
        <h3 className="card-title">Top Actor in News</h3>
        <button className="icon-button" type="button" aria-label="More actor options" title="More options">⋮</button>
      </div>
      <label className="summary-filter">
        <span className={`filter-mark ${sentiment}`} aria-hidden="true">♟</span>
        <span className="sr-only">Filter actors by sentiment</span>
        <select value={sentiment} onChange={(event) => setSentiment(event.target.value)}>
          <option value="negative">Top Negative</option>
          <option value="neutral">Top Neutral</option>
          <option value="positive">Top Positive</option>
        </select>
      </label>
      <ol className="ranked-list">
        {actors.map((item) => (
          <li className={item.rank === 1 ? "highlighted" : ""} key={item.rank}>
            <span>{item.name}</span>
            <strong>{(item.mentions / 1000).toFixed(1)}k</strong>
          </li>
        ))}
      </ol>
    </div>
  );
}
