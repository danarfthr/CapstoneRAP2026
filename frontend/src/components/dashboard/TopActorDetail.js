/**
 * TopActorDetail — Daftar berita untuk aktor yang dipilih di dropdown,
 * beserta stance tiap berita.
 */
"use client";

import { useState } from "react";
import { Badge, Card } from "./Card";
import styles from "./dashboard.module.css";

export default function TopActorDetail({ data }) {
  const [activeActor, setActiveActor] = useState(data?.actors?.[0] ?? "");
  if (!data) return null;

  const news = data.newsPerActor?.[activeActor] || [];

  return (
    <Card
      title="Top Actor in News"
      icon="⋮"
      iconLabel="More news options"
      className={styles.cardSpaced}
    >
      <label className={styles.actorSelect}>
        <span className="sr-only">Select top actor</span>
        <select value={activeActor} onChange={(event) => setActiveActor(event.target.value)}>
          {data.actors.map((actor) => (
            <option key={actor} value={actor}>
              {actor}
            </option>
          ))}
        </select>
      </label>

      <div className={styles.tableScroll}>
        <table className={`${styles.table} ${styles.tableTwoCol}`}>
          <thead>
            <tr>
              <th>News</th>
              <th>Stance</th>
            </tr>
          </thead>
          <tbody>
            {news.map((item, index) => (
              <tr key={`${activeActor}-${index}`}>
                <td>{item.news}</td>
                <td>
                  <Badge value={item.stance} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
