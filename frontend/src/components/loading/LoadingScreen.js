/**
 * LoadingScreen — [3] LOADING (route "/loading")
 *
 * Animasi progress "Preparing Analysis Dashboard..." setelah user menekan
 * "Apply Selection" di pop-up. Saat progress mencapai 100%, user diarahkan
 * ke [4] DASHBOARD dengan filter (query string) yang sama.
 */
"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import PageShell from "@/components/layout/PageShell";
import styles from "./loading.module.css";

const LOADING_MESSAGES = [
  "Fetching data from social listening APIs...",
  "Processing sentiment data...",
  "Analyzing public perception...",
  "Building visualizations...",
];

const TICK_MS = 400; // jeda antar update progress
const REDIRECT_DELAY_MS = 350; // jeda setelah 100% sebelum pindah halaman

export default function LoadingScreen() {
  const router = useRouter();
  const query = useSearchParams().toString();
  const [progress, setProgress] = useState(0);

  // Naikkan progress secara acak, lalu pindah ke dashboard saat 100%
  useEffect(() => {
    let current = 0;
    let redirectTimer;

    const interval = setInterval(() => {
      current = Math.min(current + Math.random() * 12 + 3, 100);
      setProgress(current);

      if (current === 100) {
        clearInterval(interval);
        // replace (bukan push) supaya tombol Back dari dashboard
        // kembali ke landing, bukan ke layar loading lagi
        redirectTimer = setTimeout(
          () => router.replace(`/dashboard?${query}`),
          REDIRECT_DELAY_MS
        );
      }
    }, TICK_MS);

    return () => {
      clearInterval(interval);
      clearTimeout(redirectTimer);
    };
  }, [router, query]);

  // Pesan berganti tiap 25% progress
  const message =
    LOADING_MESSAGES[Math.min(Math.floor(progress / 25), LOADING_MESSAGES.length - 1)];

  return (
    <PageShell>
      <div className={styles.content}>
        <LoadingIcon />

        <div
          className={styles.progressTrack}
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(progress)}
        >
          <div className={styles.progressBar} style={{ width: `${progress}%` }} />
        </div>

        <h1 className={styles.title}>Preparing Analysis Dashboard...</h1>
        <p className={styles.subtitle} aria-live="polite">
          {message}
        </p>
      </div>
    </PageShell>
  );
}

/** Ikon grafik + kaca pembesar dengan animasi garis. */
function LoadingIcon() {
  return (
    <div className={styles.icon}>
      <svg width="64" height="64" viewBox="0 0 64 64" fill="none" aria-hidden="true">
        <path
          d="M8 48 L18 32 L28 40 L38 20 L48 28 L56 16"
          stroke="currentColor"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={styles.chartLine}
        />
        <circle cx="44" cy="44" r="10" stroke="currentColor" strokeWidth="3" />
        <line x1="51" y1="51" x2="58" y2="58" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
    </div>
  );
}
