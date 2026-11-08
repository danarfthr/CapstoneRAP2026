/**
 * RankedListCard — Daftar peringkat dengan dropdown (mis. Top Negative/Neutral/Positive).
 * Dipakai untuk "Top Discussion Topics" dan "Top Actor in News".
 *
 * Props:
 * - options  : pilihan dropdown, [{ value, label, tone }]
 *              value = key di data, tone = warna (negative | neutral | positive)
 * - data     : { [value]: [...] }, tiap item: { rank, mentions, [labelKey] }
 * - labelKey : nama field yang ditampilkan ("topic" atau "name")
 * - marks    : ikon kecil per value di samping dropdown
 */
"use client";

import { useState } from "react";
import { Card } from "./Card";
import styles from "./dashboard.module.css";

/** Pilihan dropdown berdasarkan sentimen (komentar YouTube). */
export const SENTIMENT_OPTIONS = [
  { value: "negative", label: "Top Negative", tone: "negative" },
  { value: "neutral", label: "Top Neutral", tone: "neutral" },
  { value: "positive", label: "Top Positive", tone: "positive" },
];

/** Pilihan dropdown berdasarkan stance (artikel berita). */
export const STANCE_OPTIONS = [
  { value: "oppose", label: "Top Oppose", tone: "negative" },
  { value: "neutral", label: "Top Neutral", tone: "neutral" },
  { value: "support", label: "Top Support", tone: "positive" },
];

/** 34200 → "34.2k" */
const formatMentions = (mentions) => `${(mentions / 1000).toFixed(1)}k`;

export default function RankedListCard({
  title,
  data,
  labelKey,
  marks,
  options = SENTIMENT_OPTIONS,
}) {
  const [selected, setSelected] = useState(options[0].value);
  if (!data) return null;

  const items = data[selected] || [];
  const tone = options.find((option) => option.value === selected)?.tone;

  return (
    <Card title={title} icon="⋮" iconLabel="More options" className={styles.cardTall}>
      <label className={styles.sentimentFilter}>
        <span className={styles.filterMark} data-sentiment={tone} aria-hidden="true">
          {marks[selected]}
        </span>
        <span className="sr-only">Filter {title}</span>
        <select value={selected} onChange={(event) => setSelected(event.target.value)}>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <ol className={styles.rankedList} data-sentiment={tone}>
        {items.map((item) => (
          <li key={item.rank} className={item.rank === 1 ? styles.highlighted : ""}>
            <span>{item[labelKey]}</span>
            <strong>{formatMentions(item.mentions)}</strong>
          </li>
        ))}
      </ol>
    </Card>
  );
}
