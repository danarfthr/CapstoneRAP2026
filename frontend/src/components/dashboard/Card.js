/**
 * Card & Badge — Elemen dasar yang dipakai semua kartu dashboard.
 *
 * Card  : kotak putih dengan judul (+ tombol ikon opsional di kanan)
 * Badge : label berwarna untuk sentimen/stance (negative, neutral, positive,
 *         support, oppose/against)
 */
import styles from "./dashboard.module.css";

export function Card({ title, icon, iconLabel, className = "", children }) {
  return (
    <div className={`${styles.card} ${className}`}>
      <div className={styles.cardHeading}>
        <h3 className={styles.cardTitle}>{title}</h3>
        {icon && (
          <button
            type="button"
            className={styles.iconButton}
            aria-label={iconLabel}
            title={iconLabel}
          >
            {icon}
          </button>
        )}
      </div>
      {children}
    </div>
  );
}

export function Badge({ value, className = "" }) {
  return (
    <span className={`${styles.badge} ${styles[value] ?? ""} ${className}`}>{value}</span>
  );
}
