/**
 * AnalysisFilterModal — [2] POP-UP "Select Analysis Detail"
 *
 * Dibuka dari tombol "Start Analysis" di landing. User memilih:
 *   - jenis pembangkit (PLTU / PLTN)
 *   - platform (Youtube / News)
 *   - rentang tanggal (From–To) ATAU pilihan cepat (3 bulan / 6 bulan / semua)
 *
 * State filter hidup di dalam modal ini, jadi saat modal ditutup (Cancel/X/klik
 * di luar) semuanya otomatis ter-reset. "Apply Selection" memanggil onApply(filter).
 */
"use client";

import { useEffect, useState } from "react";
import {
  DEFAULT_FILTER,
  PLANT_TYPES,
  PLATFORMS,
  TIME_RANGES,
} from "@/lib/analysisFilter";
import styles from "./popup.module.css";

export default function AnalysisFilterModal({ onApply, onClose }) {
  const [filter, setFilter] = useState(DEFAULT_FILTER);
  const canApply = filter.types.length > 0;

  // Tutup pop-up dengan tombol Escape
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Tambah/hapus nilai dari daftar pilihan (multi-select)
  const toggleValue = (key, value) => {
    setFilter((prev) => ({
      ...prev,
      [key]: prev[key].includes(value)
        ? prev[key].filter((item) => item !== value)
        : [...prev[key], value],
    }));
  };

  // Pilih tanggal manual → matikan quick select
  const setDate = (key, value) => {
    setFilter((prev) => ({ ...prev, [key]: value, range: "" }));
  };

  // Pilih quick select → kosongkan tanggal manual
  const setRange = (range) => {
    setFilter((prev) => ({ ...prev, range, from: "", to: "" }));
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div
        className={styles.container}
        role="dialog"
        aria-modal="true"
        aria-labelledby="filter-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        {/* Header */}
        <div className={styles.header}>
          <h2 id="filter-modal-title" className={styles.title}>
            Select Analysis Detail
          </h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close modal"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {/* PLTU / PLTN */}
        <ChipGroup
          label="PLTU/PLTN"
          options={PLANT_TYPES}
          isActive={(value) => filter.types.includes(value)}
          onSelect={(value) => toggleValue("types", value)}
        />

        {/* Platform */}
        <ChipGroup
          label="Select Platform"
          options={PLATFORMS}
          isActive={(value) => filter.platforms.includes(value)}
          onSelect={(value) => toggleValue("platforms", value)}
        />

        {/* Rentang tanggal */}
        <div className={`${styles.section} ${styles.dateRow}`}>
          <DateField id="date-from" label="From" value={filter.from} onChange={(value) => setDate("from", value)} />
          <DateField id="date-to" label="To" value={filter.to} onChange={(value) => setDate("to", value)} />
        </div>

        {/* Quick select waktu */}
        <ChipGroup
          label="Quick Select time"
          options={TIME_RANGES}
          isActive={(value) => filter.range === value}
          onSelect={setRange}
        />

        {/* Tombol aksi — Apply aktif hanya jika minimal PLTU atau PLTN dipilih */}
        <div className={styles.actions}>
          {!canApply && <span className={styles.hint}>Pilih PLTU dan/atau PLTN</span>}
          <button type="button" className={styles.cancelButton} onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className={styles.applyButton}
            onClick={() => onApply(filter)}
            disabled={!canApply}
          >
            Apply Selection
          </button>
        </div>
      </div>
    </div>
  );
}

/** Sekelompok tombol chip dengan label di atasnya. */
function ChipGroup({ label, options, isActive, onSelect }) {
  return (
    <div className={styles.section} role="group" aria-label={label}>
      <span className={styles.label}>{label}</span>
      <div className={styles.chipGroup}>
        {options.map((option) => {
          const active = isActive(option.value);
          return (
            <button
              key={option.value}
              type="button"
              className={`${styles.chip} ${active ? styles.chipActive : ""}`}
              aria-pressed={active}
              onClick={() => onSelect(option.value)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/** Input tanggal dengan label. */
function DateField({ id, label, value, onChange }) {
  return (
    <div className={styles.dateField}>
      <label className={styles.label} htmlFor={id}>
        {label}
      </label>
      <input
        type="date"
        id={id}
        className={styles.dateInput}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
