import type { ReportSummary } from "../api/client";

export default function ReportsList({ summary }: { summary: ReportSummary }) {
  if (summary.count === 0) {
    return <div className="reports-empty">No ground-truth reports from neighbors yet.</div>;
  }
  return (
    <div className="reports-list">
      {summary.confidence_bump > 0 && (
        <div className="confidence-bump">
          ▲ Attribution confidence boosted +{(summary.confidence_bump * 100).toFixed(0)}% —{" "}
          {summary.count} corroborating resident reports
        </div>
      )}
      {summary.reports.map((r, i) => (
        <div key={i} className="report-item">
          <strong>{r.name}</strong> <span className="report-zip">({r.zip_code})</span>
          <div className="report-flags">
            {r.smell && <span className="tag">gas odor</span>}
            {r.visible_flare && <span className="tag">visible flare/venting</span>}
          </div>
          {r.notes && <div className="report-notes">“{r.notes}”</div>}
        </div>
      ))}
    </div>
  );
}
