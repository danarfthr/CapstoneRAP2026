/**
 * TopDiscussionTopics — Tabel topik diskusi teratas dengan sentimen
 * Menampilkan breakdown Negative/Neutral/Positive per topik
 */
"use client";

import { useState } from "react";

export default function TopDiscussionTopics({ data }) {
  const [sentiment, setSentiment] = useState("negative");
  if (!data) return null;

  const topics = data[sentiment] || [];

  return (
    <div className="card summary-card">
      <div className="card-heading">
        <h3 className="card-title">Top Discussion Topics &amp;</h3>
        <button className="icon-button" type="button" aria-label="More topic options" title="More options">⋮</button>
      </div>
      <label className="summary-filter">
        <span className={`filter-mark ${sentiment}`} aria-hidden="true">{sentiment === "negative" ? "⊗" : sentiment === "positive" ? "+" : "•"}</span>
        <span className="sr-only">Filter discussion topics by sentiment</span>
        <select value={sentiment} onChange={(event) => setSentiment(event.target.value)}>
          <option value="negative">Top Negative</option>
          <option value="neutral">Top Neutral</option>
          <option value="positive">Top Positive</option>
        </select>
      </label>
      <ol className="ranked-list">
        {topics.map((item) => (
          <li className={item.rank === 1 ? "highlighted" : ""} key={item.rank}>
            <span>{item.topic}</span>
            <strong>{(item.mentions / 1000).toFixed(1)}k</strong>
          </li>
        ))}
      </ol>
    </div>
  );
}
