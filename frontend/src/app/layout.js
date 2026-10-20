import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata = {
  title: "SentimentLens — Public Sentiment Analysis",
  description:
    "Explore comprehensive public perception and sentiment data surrounding major energy infrastructure projects.",
  keywords: [
    "sentiment analysis",
    "public perception",
    "energy infrastructure",
    "data analysis",
    "research",
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
