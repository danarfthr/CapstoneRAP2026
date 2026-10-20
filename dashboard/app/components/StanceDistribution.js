/**
 * StanceDistribution — Horizontal stacked bar chart untuk distribusi stance
 * Menampilkan persentase Support, Against, Neutral dari artikel berita
 */
"use client";

export default function StanceDistribution({ data }) {
  if (!data) return null;

  const { support, against, neutral } = data;

  return (
    <div className="card">
      <h3 className="card-title">Stance Distribution</h3>

      {/* Horizontal stacked bar */}
      <div className="distribution-bar-wrapper">
        <div className="distribution-bar">
          <div
            className="distribution-bar-segment against"
            style={{ flex: against.percentage }}
            title={`Against: ${against.percentage}%`}
          >
            {against.percentage}%
          </div>
          <div
            className="distribution-bar-segment neutral"
            style={{ flex: neutral.percentage }}
            title={`Neutral: ${neutral.percentage}%`}
          >
            {neutral.percentage}%
          </div>
          <div
            className="distribution-bar-segment support"
            style={{ flex: support.percentage }}
            title={`Support: ${support.percentage}%`}
          >
            {support.percentage}%
          </div>
        </div>

        {/* Legend */}
        <div className="distribution-legend">
          <div className="legend-item">
            <span className="legend-dot against"></span>
            Oppose ({against.percentage}%)
          </div>
          <div className="legend-item">
            <span className="legend-dot neutral"></span>
            Neutral ({neutral.percentage}%)
          </div>
          <div className="legend-item">
            <span className="legend-dot support"></span>
            Support ({support.percentage}%)
          </div>
        </div>
      </div>
    </div>
  );
}
