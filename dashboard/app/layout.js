import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata = {
  title: "SentimentLens — Analisis Sentimen PLTU vs PLTN",
  description:
    "Dashboard analisis sentimen dan stance publik terhadap PLTU dan PLTN di Indonesia. Proyek Capstone RAP 2026 — Ilmu Komputer, FMIPA, Universitas Gadjah Mada.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="id" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
