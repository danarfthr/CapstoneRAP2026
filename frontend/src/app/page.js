"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import styles from "./page.module.css";

export default function Home() {
  const [showModal, setShowModal] = useState(false);
  const [showLoading, setShowLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingText, setLoadingText] = useState("Fetching data from social listening APIs...");

  // Selection state
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [quickSelect, setQuickSelect] = useState("all");

  // Toggle multi-select for PLTU/PLTN
  const toggleType = (type) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  // Toggle multi-select for platforms
  const togglePlatform = (platform) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platform)
        ? prev.filter((p) => p !== platform)
        : [...prev, platform]
    );
  };

  // Handle quick select time
  const handleQuickSelect = (value) => {
    setQuickSelect(value);
    setDateFrom("");
    setDateTo("");
  };

  // Handle Apply Selection
  const handleApply = () => {
    setShowModal(false);
    setShowLoading(true);
    setLoadingProgress(0);
  };

  // Handle Cancel
  const handleCancel = () => {
    setShowModal(false);
    setSelectedTypes([]);
    setSelectedPlatforms([]);
    setDateFrom("");
    setDateTo("");
    setQuickSelect("all");
  };

  // Loading progress animation
  useEffect(() => {
    if (!showLoading) return;

    const loadingMessages = [
      "Fetching data from social listening APIs...",
      "Processing sentiment data...",
      "Analyzing public perception...",
      "Building visualizations...",
    ];

    let progress = 0;
    let msgIndex = 0;

    const interval = setInterval(() => {
      progress += Math.random() * 12 + 3;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        window.setTimeout(() => {
          window.location.assign(
            process.env.NEXT_PUBLIC_DASHBOARD_URL || "http://localhost:3000"
          );
        }, 350);
      }
      setLoadingProgress(Math.min(progress, 100));

      const newMsgIndex = Math.min(
        Math.floor(progress / 25),
        loadingMessages.length - 1
      );
      if (newMsgIndex !== msgIndex) {
        msgIndex = newMsgIndex;
        setLoadingText(loadingMessages[msgIndex]);
      }
    }, 400);

    return () => clearInterval(interval);
  }, [showLoading]);

  // =================== LOADING PAGE ===================
  if (showLoading) {
    return (
      <div className={styles.pageWrapper}>
        <div className={styles.animatedBg}>
          <div className={`${styles.orb} ${styles.orb1}`} />
          <div className={`${styles.orb} ${styles.orb2}`} />
          <div className={`${styles.orb} ${styles.orb3}`} />
          <div className={styles.gridOverlay} />
        </div>

        {/* Navbar */}
        <nav className={styles.navbar} role="navigation">
          <Link href="/" className={styles.logo} id="logo-loading">
            SentimentLens
          </Link>
        </nav>

        {/* Loading Content */}
        <main className={styles.hero}>
          <div className={styles.loadingContent}>
            {/* Analytics Icon */}
            <div className={styles.loadingIcon}>
              <svg
                width="64"
                height="64"
                viewBox="0 0 64 64"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Chart line */}
                <path
                  d="M8 48 L18 32 L28 40 L38 20 L48 28 L56 16"
                  stroke="#111827"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  fill="none"
                  className={styles.chartLine}
                />
                {/* Magnifying glass */}
                <circle
                  cx="44"
                  cy="44"
                  r="10"
                  stroke="#111827"
                  strokeWidth="3"
                  fill="none"
                />
                <line
                  x1="51"
                  y1="51"
                  x2="58"
                  y2="58"
                  stroke="#111827"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
            </div>

            {/* Progress Bar */}
            <div className={styles.progressBarContainer}>
              <div
                className={styles.progressBar}
                style={{ width: `${loadingProgress}%` }}
              />
            </div>

            <h1 className={styles.loadingTitle}>
              Preparing Analysis Dashboard...
            </h1>
            <p className={styles.loadingSubtitle}>{loadingText}</p>
          </div>
        </main>

        {/* Footer */}
        <footer className={styles.footerLoading}>
          <div className={styles.footerInner}>
            <p className={styles.footerLeft}>
              Sentiment insights from public online discussions
            </p>
            <div className={styles.footerRight}>
              <span className={styles.footerCopyright}>
                © 2024 Research Insight Lab.
              </span>
            </div>
          </div>
        </footer>
      </div>
    );
  }

  // =================== LANDING PAGE ===================
  return (
    <div className={styles.pageWrapper}>
      {/* Animated Background */}
      <div className={styles.animatedBg}>
        <div className={`${styles.orb} ${styles.orb1}`} />
        <div className={`${styles.orb} ${styles.orb2}`} />
        <div className={`${styles.orb} ${styles.orb3}`} />
        <div className={styles.gridOverlay} />
      </div>

      {/* Navbar */}
      <nav
        className={styles.navbar}
        role="navigation"
        aria-label="Main navigation"
      >
        <Link href="/" className={styles.logo} id="logo">
          SentimentLens
        </Link>
        <ul className={styles.navLinks}>
          <li>
            <a
              href="#methodology"
              className={styles.navLink}
              id="nav-methodology"
            >
              Methodology
            </a>
          </li>
          <li>
            <a href="#privacy" className={styles.navLink} id="nav-privacy">
              Data Privacy
            </a>
          </li>
          <li>
            <a href="#about" className={styles.navLink} id="nav-about">
              About
            </a>
          </li>
        </ul>
      </nav>

      {/* Hero Section */}
      <main className={styles.hero}>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>Public Sentiment Analysis</h1>
          <p className={styles.heroSubtitle}>
            Explore comprehensive public perception and sentiment data
            surrounding major energy infrastructure projects.
          </p>
          <button
            className={styles.ctaButton}
            id="cta-start-analysis"
            type="button"
            onClick={() => setShowModal(true)}
          >
            Start Analysis
            <span className={styles.ctaArrow} aria-hidden="true">
              →
            </span>
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <p className={styles.footerLeft}>
            Sentiment insights from public online discussions
          </p>
          <div className={styles.footerRight}>
            <a
              href="#methodology"
              className={styles.footerLink}
              id="footer-methodology"
            >
              Methodology
            </a>
            <a
              href="#privacy"
              className={styles.footerLink}
              id="footer-privacy"
            >
              Data Privacy
            </a>
            <span className={styles.footerCopyright}>
              © 2024 Research Insight Lab
            </span>
          </div>
        </div>
      </footer>

      {/* ========== MODAL ========== */}
      {showModal && (
        <div className={styles.modalOverlay} onClick={handleCancel}>
          <div
            className={styles.modalContainer}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>Select Analysis Detail</h2>
              <button
                className={styles.modalClose}
                onClick={handleCancel}
                id="modal-close"
                type="button"
                aria-label="Close modal"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path
                    d="M15 5L5 15M5 5l10 10"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>

            {/* PLTU / PLTN */}
            <div className={styles.modalSection}>
              <label className={styles.modalLabel}>PLTU/PLTN</label>
              <div className={styles.chipGroup}>
                <button
                  type="button"
                  className={`${styles.chip} ${
                    selectedTypes.includes("PLTU") ? styles.chipActive : ""
                  }`}
                  onClick={() => toggleType("PLTU")}
                  id="chip-pltu"
                >
                  PLTU
                </button>
                <button
                  type="button"
                  className={`${styles.chip} ${
                    selectedTypes.includes("PLTN") ? styles.chipActive : ""
                  }`}
                  onClick={() => toggleType("PLTN")}
                  id="chip-pltn"
                >
                  PLTN
                </button>
              </div>
            </div>

            {/* Select Platform */}
            <div className={styles.modalSection}>
              <label className={styles.modalLabel}>Select Platform</label>
              <div className={styles.chipGroup}>
                <button
                  type="button"
                  className={`${styles.chip} ${
                    selectedPlatforms.includes("Youtube")
                      ? styles.chipActive
                      : ""
                  }`}
                  onClick={() => togglePlatform("Youtube")}
                  id="chip-youtube"
                >
                  Youtube
                </button>
                <button
                  type="button"
                  className={`${styles.chip} ${
                    selectedPlatforms.includes("News") ? styles.chipActive : ""
                  }`}
                  onClick={() => togglePlatform("News")}
                  id="chip-news"
                >
                  News
                </button>
              </div>
            </div>

            {/* Date Range */}
            <div className={styles.modalSection}>
              <div className={styles.dateRow}>
                <div className={styles.dateField}>
                  <label className={styles.modalLabel} htmlFor="date-from">
                    From
                  </label>
                  <input
                    type="date"
                    id="date-from"
                    className={styles.dateInput}
                    value={dateFrom}
                    onChange={(e) => {
                      setDateFrom(e.target.value);
                      setQuickSelect("");
                    }}
                    placeholder="mm/dd/yyyy"
                  />
                </div>
                <div className={styles.dateField}>
                  <label className={styles.modalLabel} htmlFor="date-to">
                    To
                  </label>
                  <input
                    type="date"
                    id="date-to"
                    className={styles.dateInput}
                    value={dateTo}
                    onChange={(e) => {
                      setDateTo(e.target.value);
                      setQuickSelect("");
                    }}
                    placeholder="mm/dd/yyyy"
                  />
                </div>
              </div>
            </div>

            {/* Quick Select Time */}
            <div className={styles.modalSection}>
              <label className={styles.modalLabel}>Quick Select time</label>
              <div className={styles.chipGroup}>
                <button
                  type="button"
                  className={`${styles.chip} ${
                    quickSelect === "3m" ? styles.chipActive : ""
                  }`}
                  onClick={() => handleQuickSelect("3m")}
                  id="chip-3months"
                >
                  Last 3 Months
                </button>
                <button
                  type="button"
                  className={`${styles.chip} ${
                    quickSelect === "6m" ? styles.chipActive : ""
                  }`}
                  onClick={() => handleQuickSelect("6m")}
                  id="chip-6months"
                >
                  Last 6 Months
                </button>
                <button
                  type="button"
                  className={`${styles.chip} ${
                    quickSelect === "all" ? styles.chipActive : ""
                  }`}
                  onClick={() => handleQuickSelect("all")}
                  id="chip-alltime"
                >
                  All Time
                </button>
              </div>
            </div>

            {/* Modal Actions */}
            <div className={styles.modalActions}>
              <button
                type="button"
                className={styles.btnCancel}
                onClick={handleCancel}
                id="btn-cancel"
              >
                Cancel
              </button>
              <button
                type="button"
                className={styles.btnApply}
                onClick={handleApply}
                id="btn-apply"
              >
                Apply Selection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
