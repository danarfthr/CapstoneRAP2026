/**
 * layout.js — Root layout untuk seluruh aplikasi SentimentLens.
 *
 * Membungkus semua halaman (landing, loading, dashboard): memasang font Inter,
 * design token global (globals.css), dan metadata default.
 */
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata = {
  title: {
    default: "SentimentLens — Public Sentiment Analysis",
    template: "%s — SentimentLens",
  },
  description:
    "Explore comprehensive public perception and sentiment data surrounding major energy infrastructure projects.",
  keywords: [
    "sentiment analysis",
    "public perception",
    "energy infrastructure",
    "PLTU",
    "PLTN",
  ],
  authors: [{ name: "Research Insight Lab" }],
  openGraph: {
    title: "SentimentLens — Public Sentiment Analysis",
    description:
      "Explore comprehensive public perception and sentiment data surrounding major energy infrastructure projects.",
    type: "website",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
