/**
 * PageShell — Kerangka halaman yang dipakai bersama oleh LANDING dan LOADING.
 *
 * Isinya: background animasi (orb + grid), navbar, area konten di tengah,
 * dan footer. Dengan komponen ini, landing & loading dijamin tampil seragam.
 *
 * Props:
 * - animateFooter : footer muncul dengan animasi fade-in (true di landing)
 * - children      : isi halaman (hero landing atau animasi loading)
 * - overlay       : elemen yang dirender di luar <main>, mis. pop-up
 */
import Link from "next/link";
import styles from "./layout.module.css";

export default function PageShell({ animateFooter = false, children, overlay }) {
  return (
    <div className={styles.pageWrapper}>
      <AnimatedBackground />

      <nav className={styles.navbar} aria-label="Main navigation">
        <Link href="/" className={styles.logo}>
          SentimentLens
        </Link>
      </nav>

      <main className={styles.main}>{children}</main>

      <footer className={`${styles.footer} ${animateFooter ? styles.footerAnimated : ""}`}>
        <div className={styles.footerInner}>
          <p className={styles.footerText}>
            Sentiment insights from public online discussions
          </p>
          <span className={styles.footerText}>© 2024 Research Insight Lab</span>
        </div>
      </footer>

      {overlay}
    </div>
  );
}

/** Background gradasi dengan 3 orb yang melayang + pola titik halus. */
function AnimatedBackground() {
  return (
    <div className={styles.animatedBg} aria-hidden="true">
      <div className={`${styles.orb} ${styles.orb1}`} />
      <div className={`${styles.orb} ${styles.orb2}`} />
      <div className={`${styles.orb} ${styles.orb3}`} />
      <div className={styles.gridOverlay} />
    </div>
  );
}
