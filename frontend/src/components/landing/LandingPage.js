/**
 * LandingPage — [1] LANDING (route "/")
 *
 * Halaman pembuka dengan judul, deskripsi, dan tombol "Start Analysis".
 * Tombol membuka [2] POP-UP (AnalysisFilterModal). Setelah user menekan
 * "Apply Selection", filter dibawa ke [3] LOADING lewat URL.
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import PageShell from "@/components/layout/PageShell";
import AnalysisFilterModal from "@/components/popup/AnalysisFilterModal";
import { filterToQuery } from "@/lib/analysisFilter";
import styles from "./landing.module.css";

export default function LandingPage() {
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Pop-up → Loading: kirim filter sebagai query string.
  // Pop-up ditutup dulu, karena Next.js menyimpan halaman sebelumnya; tanpa ini
  // pop-up masih terbuka saat user kembali ke landing.
  const handleApply = (filter) => {
    setIsModalOpen(false);
    router.push(`/loading?${filterToQuery(filter)}`);
  };

  return (
    <PageShell
      animateFooter
      overlay={
        isModalOpen && (
          <AnalysisFilterModal
            onApply={handleApply}
            onClose={() => setIsModalOpen(false)}
          />
        )
      }
    >
      <div className={styles.heroContent}>
        <h1 className={styles.heroTitle}>Public Sentiment Analysis</h1>
        <p className={styles.heroSubtitle}>
          Explore comprehensive public perception and sentiment data
          surrounding major energy infrastructure projects.
        </p>
        <button
          type="button"
          className={styles.ctaButton}
          onClick={() => setIsModalOpen(true)}
        >
          Start Analysis
          <span className={styles.ctaArrow} aria-hidden="true">
            →
          </span>
        </button>
      </div>
    </PageShell>
  );
}
