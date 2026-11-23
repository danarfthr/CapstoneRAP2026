/**
 * DistributionCard — Bar horizontal bertumpuk untuk distribusi persentase.
 * Dipakai untuk "Sentiment Distribution" (komentar YouTube) dan
 * "Stance Distribution" (artikel berita).
 *
 * Props:
 * - segments : [{ key, label }] urutan segmen dari kiri ke kanan
 * - data     : { [key]: { count, percentage } } dari API
 */
"use client";

import { Card } from "./Card";
import styles from "./dashboard.module.css";

export default function DistributionCard({ title, segments, data }) {
  if (!data) return null;

  return (
    <Card title={title}>
      <div className={styles.distributionBar}>
        {segments.map(({ key, label }) => (
          <div
            key={key}
            className={`${styles.distributionSegment} ${styles[key]}`}
            style={{ flex: data[key].percentage }}
            title={`${label}: ${data[key].percentage}%`}
          />
        ))}
      </div>

      <div className={styles.legend}>
        {segments.map(({ key, label }) => (
          <div key={key} className={styles.legendItem}>
            <span className={`${styles.legendDot} ${styles[key]}`} />
            {label} ({data[key].percentage}%)
          </div>
        ))}
      </div>
    </Card>
  );
}
