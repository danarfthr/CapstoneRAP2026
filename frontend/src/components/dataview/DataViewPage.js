/**
 * DataViewPage — [5] DATA VIEW (route "/data")
 *
 * Menampilkan data mentah (komentar YouTube & berita) beserta anotasi
 * stance/sentimen. Filter dari pop-up ikut dibawa lewat query string:
 *   - types     → section PLTU / PLTN yang tampil (dan tombol di header)
 *   - platforms → tabel YouTube / News yang tampil
 * Data diambil dari endpoint /api/dataset.
 *
 * Susunan halaman:
 *   DashboardHeader → logo, tombol PLTU/PLTN, Export CSV, Back to Dashboard
 *   DatasetSection  → satu blok per jenis pembangkit (judul, filter, tabel)
 *   footer
 *
 * State filter (search/sentimen/stance) disimpan di sini per section, supaya
 * Export CSV mengekspor baris yang sama dengan yang sedang tampil.
 */
"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { PLANT_TYPES, PLATFORMS, queryToFilter } from "@/lib/analysisFilter";
import { EMPTY_DATASET_FILTER, buildCsv, downloadCsv, filterRows } from "@/lib/dataset";
import useSectionNav from "@/lib/useSectionNav";
import DashboardHeader, { HeaderAction } from "@/components/dashboard/DashboardHeader";
import dashboardStyles from "@/components/dashboard/dashboard.module.css";
import DatasetSection from "./DatasetSection";
import styles from "./dataview.module.css";

export default function DataViewPage() {
  const searchParams = useSearchParams();
  const query = searchParams.toString();

  const { types, platforms } = queryToFilter(searchParams);
  const sections = PLANT_TYPES.filter((type) => types.includes(type.value));
  const visiblePlatforms = PLATFORMS.filter((platform) => platforms.includes(platform.value));

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [filters, setFilters] = useState({}); // { pltu: { search, sentiment, stance }, ... }

  const { activeSection, scrollToSection, registerSection } = useSectionNav(sections, data);

  // Ambil data (diulang saat filter URL berubah atau tombol "Coba Lagi")
  useEffect(() => {
    let cancelled = false;

    fetch(`/api/dataset?${query}`)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
      })
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error("Failed to fetch dataset:", err);
        setError(err.message);
      });

    return () => {
      cancelled = true;
    };
  }, [query, reloadKey]);

  const getFilter = (type) => filters[type] ?? EMPTY_DATASET_FILTER;
  const setFilter = (type, filter) => setFilters((current) => ({ ...current, [type]: filter }));

  const retry = () => {
    setError(null);
    setData(null);
    setReloadKey((key) => key + 1);
  };

  // Export CSV: semua baris yang sedang lolos filter, dari semua section & platform yang tampil
  const exportCsv = () => {
    if (!data) return;
    const blocks = sections.flatMap((type) =>
      visiblePlatforms.map((platform) => ({
        type: type.label,
        platform: platform.value,
        rows: filterRows(data[type.value]?.[platform.value], platform.value, getFilter(type.value)),
      }))
    );
    const name = sections.map((type) => type.value).join("-");
    downloadCsv(buildCsv(blocks), `sentimentlens-dataset-${name}.csv`);
  };

  return (
    <div className={styles.page}>
      <DashboardHeader
        sections={sections}
        activeSection={activeSection}
        onNavigate={scrollToSection}
        actions={
          <>
            <HeaderAction onClick={exportCsv} icon={<DownloadIcon />} label="Export CSV" />
            <HeaderAction
              href={`/dashboard?${query}`}
              icon="←"
              label="Back to Dashboard"
              primary
            />
          </>
        }
      />

      {error ? (
        <div className={dashboardStyles.stateContainer}>
          <p className={dashboardStyles.errorText}>Gagal memuat data: {error}</p>
          <button type="button" className={dashboardStyles.retryButton} onClick={retry}>
            Coba Lagi
          </button>
        </div>
      ) : !data ? (
        <div className={dashboardStyles.stateContainer}>
          <div className={dashboardStyles.spinner} />
          <p>Memuat data...</p>
        </div>
      ) : (
        <main className={styles.main}>
          {sections.map((type) => (
            <DatasetSection
              key={type.value}
              type={type}
              data={data[type.value]}
              platforms={visiblePlatforms}
              filter={getFilter(type.value)}
              onFilterChange={(filter) => setFilter(type.value, filter)}
              sectionRef={registerSection(type.value)}
            />
          ))}
        </main>
      )}

      <footer className={dashboardStyles.footer}>
        SentimentLens © 2026 — Proyek Capstone RAP | Ilmu Komputer, FMIPA,
        Universitas Gadjah Mada
      </footer>
    </div>
  );
}

function DownloadIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: "block" }}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="M7 10l5 5 5-5" />
      <path d="M12 15V3" />
    </svg>
  );
}
