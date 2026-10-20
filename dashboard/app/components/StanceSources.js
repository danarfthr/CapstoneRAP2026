/**
 * StanceSources — Tabel sumber berita dan stance mereka
 * Menampilkan nama sumber, stance (support/against/neutral), jumlah artikel
 */
"use client";

export default function StanceSources({ data }) {
  if (!data) return null;

  return (
    <div className="card source-card">
      <div className="card-heading">
        <h3 className="card-title">Stance Sources</h3>
        <button className="icon-button" type="button" aria-label="Filter sources" title="Filter sources">☰</button>
      </div>
      <div className="source-share-list">
        {data.sourcePercentage.map((item) => (
          <div className="source-share" key={item.source}>
            <span>{item.source}</span>
            <div className="source-share-track"><span style={{ width: `${item.percentage}%` }} /></div>
            <strong>{item.percentage}%</strong>
          </div>
        ))}
      </div>
      <div className="source-breakdown-list">
        {data.sourceBreakdown.map((item) => (
          <div className="source-breakdown" key={item.source}>
            <span>{item.source}</span>
            <div className="source-stacked-bar" aria-label={`${item.source}: ${item.positive}% positive, ${item.neutral}% neutral, ${item.negative}% negative`}>
              <i className="positive" style={{ flex: item.positive }} />
              <i className="neutral" style={{ flex: item.neutral }} />
              <i className="negative" style={{ flex: item.negative }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
