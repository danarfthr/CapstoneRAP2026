/**
 * TopActorDetail — Bagian detail aktor teratas di berita
 * Menampilkan berita-berita dengan tab Negative/Neutral/Positive
 * Setiap berita menampilkan aktor, judul, sumber, tanggal, dan snippet
 */
"use client";

import { useState } from "react";

export default function TopActorDetail({ data }) {
  const [activeActor, setActiveActor] = useState(data?.actors?.[0] ?? "");

  if (!data) return null;

  const activeData = data.newsPerActor?.[activeActor] || [];

  return (
    <div className="card actor-detail-card">
      <div className="card-heading">
        <h3 className="card-title">Top Actor in News</h3>
        <button className="icon-button" type="button" aria-label="More news options" title="More options">⋮</button>
      </div>
      <label className="actor-select-label">
        <span className="sr-only">Select top actor</span>
        <select value={activeActor} onChange={(event) => setActiveActor(event.target.value)}>
          {data.actors.map((actor) => (
            <option key={actor} value={actor}>{actor}</option>
          ))}
        </select>
      </label>
      <div className="table-scroll">
        <table className="data-table actor-news-table">
          <thead><tr><th>News</th><th>Stance</th></tr></thead>
          <tbody>
            {activeData.map((item, index) => (
              <tr key={`${activeActor}-${index}`}>
                <td>{item.news}</td>
                <td><span className={`stance-badge ${item.stance}`}>{item.stance}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
