/**
 * MostDiscussedTopics — Daftar topik spesifik yang paling banyak dibahas
 * Setiap topik menampilkan nama, deskripsi, bar sentimen mini, dan persentase
 */
"use client";

export default function MostDiscussedTopics({ data }) {
  if (!data || data.length === 0) return null;

  return (
    <div className="card most-discussed-card">
      <h3 className="card-title">Most Discussed Specific Topics</h3>
      <div className="table-scroll">
        <table className="data-table topics-table">
          <thead><tr><th>Discussion Topic / Narrative</th><th>Visibility</th><th>Avg. Sentiment</th></tr></thead>
          <tbody>{data.map((item) => (
            <tr key={item.topic}>
              <td>{item.topic}</td>
              <td>
                <span
                  className={`visibility-value ${item.visibility}`}
                  aria-label={`Visibility: ${item.visibility}`}
                >
                  <span className="visibility-track" aria-hidden="true">
                    <i />
                  </span>
                  <span>{item.visibility === "med" ? "Med" : item.visibility.charAt(0).toUpperCase() + item.visibility.slice(1)}</span>
                </span>
              </td>
              <td><span className={`sentiment-badge ${item.avgSentiment}`}>{item.avgSentiment}</span></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  );
}
