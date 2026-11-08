/**
 * MostDiscussedTopics — Tabel topik/narasi spesifik yang paling banyak dibahas.
 *
 * Kolom kedua tergantung platform yang dipilih:
 * - ada YouTube (showSentiment = true)  → Avg. Sentiment (dari komentar YouTube)
 * - hanya News  (showSentiment = false) → Stance (dari berita)
 */
"use client";

import { Badge, Card } from "./Card";
import styles from "./dashboard.module.css";

export default function MostDiscussedTopics({ data, showSentiment = true }) {
  if (!data?.length) return null;

  return (
    <Card title="Most Discussed Specific Topics" className={styles.cardSpaced}>
      <div className={styles.tableScroll}>
        <table className={`${styles.table} ${styles.tableTwoCol}`}>
          <thead>
            <tr>
              <th>Discussion Topic / Narrative</th>
              <th>{showSentiment ? "Avg. Sentiment" : "Stance"}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.topic}>
                <td>{item.topic}</td>
                <td>
                  <Badge value={showSentiment ? item.avgSentiment : item.stance} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
