/**
 * StanceSources — Porsi tiap sumber data (YouTube/News) dan
 * breakdown sentimen per sumber (positive/neutral/negative).
 */
"use client";

import { Card } from "./Card";
import styles from "./dashboard.module.css";

export default function StanceSources({ data }) {
  if (!data) return null;

  return (
    <Card title="Stance Sources" icon="☰" iconLabel="Filter sources" className={styles.cardTall}>
      {/* Persentase tiap sumber */}
      <div className={styles.shareList}>
        {data.sourcePercentage.map((item) => (
          <div key={item.source} className={styles.shareRow}>
            <span>{item.source}</span>
            <div className={styles.shareTrack}>
              <span style={{ width: `${item.percentage}%` }} />
            </div>
            <strong>{item.percentage}%</strong>
          </div>
        ))}
      </div>

      {/* Breakdown sentimen per sumber */}
      <div className={styles.breakdownList}>
        {data.sourceBreakdown.map((item) => (
          <div key={item.source} className={styles.breakdownRow}>
            <span>{item.source}</span>
            <div
              className={styles.stackedBar}
              aria-label={`${item.source}: ${item.positive}% positive, ${item.neutral}% neutral, ${item.negative}% negative`}
            >
              <i className={styles.positive} style={{ flex: item.positive }} />
              <i className={styles.neutral} style={{ flex: item.neutral }} />
              <i className={styles.negative} style={{ flex: item.negative }} />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
