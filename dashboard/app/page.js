/**
 * page.js — Halaman utama Dashboard SentimentLens
 *
 * Menampilkan analisis sentimen & stance untuk PLTU dan PLTN.
 * Data diambil dari endpoint /api/dashboard.
 * Header sticky dengan tombol PLTU/PLTN untuk scroll ke section terkait.
 */
"use client";

import { useState, useEffect, useRef } from "react";

// Import semua komponen dashboard
import SentimentDistribution from "./components/SentimentDistribution";
import StanceDistribution from "./components/StanceDistribution";
import TopDiscussionTopics from "./components/TopDiscussionTopics";
import TopActorSummary from "./components/TopActorSummary";
import StanceSources from "./components/StanceSources";
import TopActorDetail from "./components/TopActorDetail";
import MostDiscussedTopics from "./components/MostDiscussedTopics";
import SentimentStanceBreakdown from "./components/SentimentStanceBreakdown";

export default function DashboardPage() {
  // State untuk data, loading, dan error
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // State untuk tombol aktif di header
  const [activeSection, setActiveSection] = useState("pltu");

  // Refs untuk scroll-to-section
  const pltuRef = useRef(null);
  const pltnRef = useRef(null);

  /**
   * Fetch data dari API endpoint
   */
  const getDashboardData = async () => {
    const response = await fetch("/api/dashboard");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  };

  const fetchData = async () => {
    try {
      setError(null);
      setData(await getDashboardData());
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    getDashboardData()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) {
          console.error("Failed to fetch dashboard data:", err);
          setError(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  /**
   * Scroll ke section dan update tombol aktif
   */
  const scrollToSection = (section) => {
    setActiveSection(section);
    const ref = section === "pltu" ? pltuRef : pltnRef;
    if (ref.current) {
      ref.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  /**
   * Observer untuk update tombol aktif saat user scroll manual
   */
  useEffect(() => {
    if (!pltuRef.current || !pltnRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: "-100px 0px -50% 0px", threshold: 0 }
    );

    observer.observe(pltuRef.current);
    observer.observe(pltnRef.current);

    return () => observer.disconnect();
  }, [data]);

  // ---- Render States ----

  if (loading) {
    return (
      <>
        <Header activeSection={activeSection} onNavigate={scrollToSection} />
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Memuat data dashboard...</p>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Header activeSection={activeSection} onNavigate={scrollToSection} />
        <div className="error-container">
          <p className="error-text">Gagal memuat data: {error}</p>
          <button
            className="error-retry-btn"
            onClick={() => {
              setLoading(true);
              setError(null);
              fetchData();
            }}
          >
            Coba Lagi
          </button>
        </div>
      </>
    );
  }

  // ---- Main Render ----

  return (
    <>
      {/* Sticky Header */}
      <Header activeSection={activeSection} onNavigate={scrollToSection} />

      <main className="main-container">
        {/* ========== PLTU SECTION ========== */}
        <section id="pltu" ref={pltuRef} className="analysis-section">
          <h1 className="section-title">PLTU Public Analysis</h1>
          <p className="section-description">{data.pltu.description}</p>

          {/* Row 1: Sentiment + Stance Distribution */}
          <div className="distribution-grid">
            <SentimentDistribution data={data.pltu.sentimentDistribution} />
            <StanceDistribution data={data.pltu.stanceDistribution} />
          </div>

          {/* Row 2: Top Topics + Top Actors + Stance Sources */}
          <div className="topics-actors-grid">
            <TopDiscussionTopics data={data.pltu.topDiscussionTopics} />
            <TopActorSummary data={data.pltu.topActorSummary} />
            <StanceSources data={data.pltu.stanceSources} />
          </div>

          {/* Row 3: Top Actor Detail (tabbed) */}
          <TopActorDetail data={data.pltu.topActorDetail} />

          {/* Row 4: Most Discussed Specific Topics */}
          <MostDiscussedTopics data={data.pltu.mostDiscussedTopics} />

          {/* Row 5: Sentiment & Stance Breakdown */}
          <SentimentStanceBreakdown
            data={data.pltu.sentimentStanceBreakdown}
          />
        </section>

        {/* Divider antar section */}
        <hr className="section-divider" />

        {/* ========== PLTN SECTION ========== */}
        <section id="pltn" ref={pltnRef} className="analysis-section">
          <h1 className="section-title">PLTN Public Analysis</h1>
          <p className="section-description">{data.pltn.description}</p>

          {/* Row 1: Sentiment + Stance Distribution */}
          <div className="distribution-grid">
            <SentimentDistribution data={data.pltn.sentimentDistribution} />
            <StanceDistribution data={data.pltn.stanceDistribution} />
          </div>

          {/* Row 2: Top Topics + Top Actors + Stance Sources */}
          <div className="topics-actors-grid">
            <TopDiscussionTopics data={data.pltn.topDiscussionTopics} />
            <TopActorSummary data={data.pltn.topActorSummary} />
            <StanceSources data={data.pltn.stanceSources} />
          </div>

          {/* Row 3: Top Actor Detail (tabbed) */}
          <TopActorDetail data={data.pltn.topActorDetail} />

          {/* Row 4: Most Discussed Specific Topics */}
          <MostDiscussedTopics data={data.pltn.mostDiscussedTopics} />

          {/* Row 5: Sentiment & Stance Breakdown */}
          <SentimentStanceBreakdown
            data={data.pltn.sentimentStanceBreakdown}
          />
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        SentimentLens © 2026 — Proyek Capstone RAP | Ilmu Komputer, FMIPA,
        Universitas Gadjah Mada
      </footer>
    </>
  );
}

/**
 * Header — Komponen sticky header dengan branding dan navigasi PLTU/PLTN
 */
function Header({ activeSection, onNavigate }) {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-logo">
          SentimentLens
        </div>
        <nav className="header-nav">
          <button
            className={`header-nav-btn ${
              activeSection === "pltu" ? "active" : ""
            }`}
            onClick={() => onNavigate("pltu")}
          >
            PLTU
          </button>
          <button
            className={`header-nav-btn ${
              activeSection === "pltn" ? "active" : ""
            }`}
            onClick={() => onNavigate("pltn")}
          >
            PLTN
          </button>
        </nav>
        <div className="header-actions">
          <button
            className="view-data-btn"
            onClick={() => document.querySelector(".main-container")?.scrollIntoView({ behavior: "smooth" })}
          >
            <span aria-hidden="true">◉</span> View Data
          </button>
          <a
            className="home-btn"
            href={process.env.NEXT_PUBLIC_FRONTEND_URL || "http://localhost:3001"}
          >
            ← <span>Back to Homepage</span>
          </a>
        </div>
      </div>
    </header>
  );
}
