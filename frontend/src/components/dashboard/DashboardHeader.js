/**
 * DashboardHeader — Header sticky (dipakai Dashboard & Data View)
 * Logo, tombol navigasi per section (PLTU/PLTN), dan tombol aksi di kanan.
 *
 * Tombol aksi dikirim lewat `actions`, pakai <HeaderAction>:
 *   Dashboard : View Data, Back to Homepage
 *   Data View : Export CSV, Back to Dashboard
 */
"use client";

import Link from "next/link";
import styles from "./dashboard.module.css";

export default function DashboardHeader({ sections, activeSection, onNavigate, actions }) {
  return (
    <header className={styles.header}>
      <div className={styles.headerInner}>
        <Link href="/" className={styles.logo}>
          SentimentLens
        </Link>

        <nav className={styles.headerNav} aria-label="Dashboard sections">
          {sections.map((section) => (
            <button
              key={section.value}
              type="button"
              className={`${styles.headerNavButton} ${
                activeSection === section.value ? styles.active : ""
              }`}
              onClick={() => onNavigate(section.value)}
            >
              {section.label}
            </button>
          ))}
        </nav>

        <div className={styles.headerActions}>{actions}</div>
      </div>
    </header>
  );
}

/**
 * Tombol aksi di header. Pakai `href` untuk pindah halaman, atau `onClick`.
 * primary = tombol gelap (mis. Back to …). Di layar kecil hanya ikon yang tampil.
 */
export function HeaderAction({ href, onClick, icon, label, primary = false }) {
  const className = `${styles.headerAction} ${primary ? styles.headerActionPrimary : ""}`;
  const content = (
    <>
      <span aria-hidden="true">{icon}</span>
      <span className={styles.headerActionLabel}>{label}</span>
    </>
  );

  return href ? (
    <Link href={href} className={className} aria-label={label}>
      {content}
    </Link>
  ) : (
    <button type="button" className={className} onClick={onClick} aria-label={label}>
      {content}
    </button>
  );
}
