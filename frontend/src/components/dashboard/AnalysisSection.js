/**
 * AnalysisSection — Satu blok analisis lengkap untuk satu jenis pembangkit.
 * Dipakai untuk PLTU dan PLTN (isi & urutan kartu sama, hanya datanya beda).
 *
 * Kartu yang tampil tergantung platform yang dipilih di pop-up:
 *
 *   Kartu                         | YouTube + News | YouTube saja | News saja
 *   ------------------------------|----------------|--------------|----------
 *   Sentiment Distribution        |       ✓        |      ✓       |    –
 *   Stance Distribution           |       ✓        |      ✓       |    ✓
 *   Top Discussion Topics         |   ✓ sentimen   | ✓ sentimen (lebar) | ✓ stance
 *   Top Actor in News (ringkasan) |   ✓ sentimen   |      –       | ✓ stance
 *   Stance Sources                |       ✓        |      –       |    –
 *   Top Actor in News (detail)    |       ✓        |      –       |    ✓
 *   Most Discussed Topics         |   + sentimen   |  + sentimen  | + stance
 *   Breakdown                     | Sentiment & Stance | Sentiment & Stance | Stance saja
 *
 * Alasannya: sentimen berasal dari komentar YouTube, aktor berasal dari
 * berita, dan Stance Sources membandingkan sumber (butuh ≥ 2 sumber).
 */
"use client";

import DistributionCard from "./DistributionCard";
import RankedListCard, { SENTIMENT_OPTIONS, STANCE_OPTIONS } from "./RankedListCard";
import StanceSources from "./StanceSources";
import TopActorDetail from "./TopActorDetail";
import MostDiscussedTopics from "./MostDiscussedTopics";
import SentimentStanceBreakdown from "./SentimentStanceBreakdown";
import styles from "./dashboard.module.css";

// Urutan & label segmen di bar distribusi (key = key data dari API)
const SENTIMENT_SEGMENTS = [
  { key: "negative", label: "Negative" },
  { key: "neutral", label: "Neutral" },
  { key: "positive", label: "Positive" },
];

const STANCE_SEGMENTS = [
  { key: "against", label: "Oppose" },
  { key: "neutral", label: "Neutral" },
  { key: "support", label: "Support" },
];

// Ikon kecil di samping dropdown "Top Negative/Neutral/Positive"
const TOPIC_MARKS = { negative: "⊗", neutral: "•", positive: "+" };
const TOPIC_STANCE_MARKS = { oppose: "⊗", neutral: "•", support: "+" };
const ACTOR_MARKS = { negative: "♟", neutral: "♟", positive: "♟" };
const ACTOR_STANCE_MARKS = { oppose: "♟", neutral: "♟", support: "♟" };

export default function AnalysisSection({ type, data, platforms, sectionRef }) {
  if (!data) return null;

  const hasYoutube = platforms.includes("youtube");
  const hasNews = platforms.includes("news");

  // Aturan tampil per kartu (lihat tabel di atas)
  const show = {
    sentiment: hasYoutube,
    actors: hasNews,
    sources: hasYoutube && hasNews,
  };

  // Baris 1 & 2: daftar kartu yang tampil, supaya jumlah kolom grid pas
  const distributionCards = [
    show.sentiment && (
      <DistributionCard
        key="sentiment"
        title="Sentiment Distribution"
        segments={SENTIMENT_SEGMENTS}
        data={data.sentimentDistribution}
      />
    ),
    <DistributionCard
      key="stance"
      title="Stance Distribution"
      segments={STANCE_SEGMENTS}
      data={data.stanceDistribution}
    />,
  ].filter(Boolean);

  const summaryCards = [
    // Ada data sentimen (YouTube) → dropdown sentimen; News saja → dropdown stance.
    // key dibedakan supaya pilihan dropdown ter-reset saat mode berganti.
    show.sentiment ? (
      <RankedListCard
        key="topics-sentiment"
        title="Top Discussion Topics & Sentiment"
        data={data.topDiscussionTopics}
        labelKey="topic"
        marks={TOPIC_MARKS}
        options={SENTIMENT_OPTIONS}
      />
    ) : (
      <RankedListCard
        key="topics-stance"
        title="Top Discussion Topics & Stance"
        data={data.topDiscussionTopicsByStance}
        labelKey="topic"
        marks={TOPIC_STANCE_MARKS}
        options={STANCE_OPTIONS}
      />
    ),
    show.actors &&
      (show.sentiment ? (
        <RankedListCard
          key="actors-sentiment"
          title="Top Actor in News"
          data={data.topActorSummary}
          labelKey="name"
          marks={ACTOR_MARKS}
          options={SENTIMENT_OPTIONS}
        />
      ) : (
        <RankedListCard
          key="actors-stance"
          title="Top Actor in News"
          data={data.topActorSummaryByStance}
          labelKey="name"
          marks={ACTOR_STANCE_MARKS}
          options={STANCE_OPTIONS}
        />
      )),
    show.sources && <StanceSources key="sources" data={data.stanceSources} />,
  ].filter(Boolean);

  return (
    <section id={type.value} ref={sectionRef} className={styles.section}>
      <h2 className={styles.sectionTitle}>{type.label} Public Analysis</h2>
      <p className={styles.sectionDescription}>{data.description}</p>

      {/* Baris 1: distribusi sentimen / stance */}
      <div className={styles.cardGrid} data-columns={distributionCards.length}>
        {distributionCards}
      </div>

      {/* Baris 2: top topik, top aktor, sumber stance */}
      <div className={styles.cardGrid} data-columns={summaryCards.length}>
        {summaryCards}
      </div>

      {/* Baris 3–5 */}
      {show.actors && <TopActorDetail data={data.topActorDetail} />}
      <MostDiscussedTopics data={data.mostDiscussedTopics} showSentiment={show.sentiment} />
      <SentimentStanceBreakdown
        data={data.sentimentStanceBreakdown}
        showSentiment={show.sentiment}
      />
    </section>
  );
}
