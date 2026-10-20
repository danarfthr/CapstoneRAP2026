import "./globals.css";

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
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
