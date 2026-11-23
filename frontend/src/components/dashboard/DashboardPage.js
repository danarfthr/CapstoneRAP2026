/**
 * DashboardPage — [4] DASHBOARD (route "/dashboard")
 *
 * Menampilkan analisis sentimen & stance untuk PLTU dan/atau PLTN sesuai
 * pilihan user di pop-up (dibaca dari query string, mis. ?types=pltu).
 * Data diambil dari endpoint /api/dashboard.
 *
 * Susunan halaman:
 *   DashboardHeader  → logo, tombol PLTU/PLTN (scroll ke section), View Data, Back to Homepage
 *   AnalysisSection  → satu blok lengkap per jenis pembangkit (PLTU / PLTN)
 *   footer
 */
"use client";

import { Fragment, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { PLANT_TYPES, queryToFilter } from "@/lib/analysisFilter";
import useSectionNav from "@/lib/useSectionNav";
import DashboardHeader, { HeaderAction } from "./DashboardHeader";
import AnalysisSection from "./AnalysisSection";
import styles from "./dashboard.module.css";

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const query = searchParams.toString();

  // Section yang ditampilkan mengikuti pilihan PLTU/PLTN di pop-up.
  // platforms kosong di URL = YouTube + News (lihat queryToFilter).
  const { types, platforms } = queryToFilter(searchParams);
  const sections = PLANT_TYPES.filter((type) => types.includes(type.value));

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  // Tombol PLTU/PLTN di header: scroll ke section + tanda aktif saat scroll
  const { activeSection, scrollToSection, registerSection } = useSectionNav(sections, data);

  // Ambil data dashboard (diulang saat filter berubah atau tombol "Coba Lagi")
  useEffect(() => {
    let cancelled = false;

    fetch(`/api/dashboard?${query}`)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
      })
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error("Failed to fetch dashboard data:", err);
        setError(err.message);
      });

    return () => {
      cancelled = true;
    };
  }, [query, reloadKey]);

  const retry = () => {
    setError(null);
    setData(null);
    setReloadKey((key) => key + 1);
  };

  return (
    <>
      <DashboardHeader
        sections={sections}
        activeSection={activeSection}
        onNavigate={scrollToSection}
        actions={
          <>
            {/* Data View membawa filter yang sama (PLTU/PLTN, platform, waktu) */}
            <HeaderAction href={`/data?${query}`} icon="◉" label="View Data" />
            <HeaderAction href="/" icon="←" label="Back to Homepage" primary />
          </>
        }
      />

      {error ? (
        <div className={styles.stateContainer}>
          <p className={styles.errorText}>Gagal memuat data: {error}</p>
          <button type="button" className={styles.retryButton} onClick={retry}>
            Coba Lagi
          </button>
        </div>
      ) : !data ? (
        <div className={styles.stateContainer}>
          <div className={styles.spinner} />
          <p>Memuat data dashboard...</p>
        </div>
      ) : (
        <main className={styles.main}>
          <h1 className="sr-only">SentimentLens Dashboard</h1>
          {sections.map((type, index) => (
            <Fragment key={type.value}>
              {index > 0 && <hr className={styles.sectionDivider} />}
              <AnalysisSection
                type={type}
                data={data[type.value]}
                platforms={platforms}
                sectionRef={registerSection(type.value)}
              />
            </Fragment>
          ))}
        </main>
      )}

      <footer className={styles.footer}>
        SentimentLens © 2026 — Proyek Capstone RAP | Ilmu Komputer, FMIPA,
        Universitas Gadjah Mada
      </footer>
    </>
  );
}
