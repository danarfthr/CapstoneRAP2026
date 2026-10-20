/**
 * SentimentDistribution — Horizontal stacked bar chart untuk distribusi sentimen
 * Menampilkan persentase Positive, Negative, Neutral dari komentar YouTube
 */
"use client";

export default function SentimentDistribution({ data }) {
  if (!data) return null;

  const { positive, negative, neutral } = data;

  return (
    <div className="card">
      <h3 className="card-title">Sentiment Distribution</h3>

      {/* Horizontal stacked bar */}
      <div className="distribution-bar-wrapper">
        <div className="distribution-bar">
          <div
            className="distribution-bar-segment negative"
            style={{ flex: negative.percentage }}
            title={`Negative: ${negative.percentage}%`}
          >
            {negative.percentage}%
          </div>
          <div
            className="distribution-bar-segment neutral"
            style={{ flex: neutral.percentage }}
            title={`Neutral: ${neutral.percentage}%`}
          >
            {neutral.percentage}%
          </div>
          <div
            className="distribution-bar-segment positive"
            style={{ flex: positive.percentage }}
            title={`Positive: ${positive.percentage}%`}
          >
            {positive.percentage}%
          </div>
        </div>

        {/* Legend */}
        <div className="distribution-legend">
          <div className="legend-item">
            <span className="legend-dot negative"></span>
            Negative ({negative.percentage}%)
          </div>
          <div className="legend-item">
            <span className="legend-dot neutral"></span>
            Neutral ({neutral.percentage}%)
          </div>
          <div className="legend-item">
            <span className="legend-dot positive"></span>
            Positive ({positive.percentage}%)
          </div>
        </div>
      </div>
    </div>
  );
}
