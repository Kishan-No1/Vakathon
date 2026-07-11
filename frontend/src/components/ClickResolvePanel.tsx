import { useEffect, useState } from "react";
import {
  api,
  stateAbbr,
  type Attribution,
  type Plume,
  type ReportSummary,
} from "../api/client";
import ComplaintLetter from "./ComplaintLetter";
import CosignButton from "../community/CosignButton";
import ReportForm from "../community/ReportForm";
import ReportsList from "../community/ReportsList";

export default function ClickResolvePanel({ plume }: { plume: Plume }) {
  const [attr, setAttr] = useState<Attribution | null>(null);
  const [reports, setReports] = useState<ReportSummary | null>(null);
  const [cosignCount, setCosignCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setAttr(null);
    setReports(null);
    setError(null);
    api.attribution(plume.plume_id).then(setAttr).catch((e) => setError(String(e)));
    api.reports(plume.plume_id).then(setReports).catch(() => {});
  }, [plume.plume_id]);

  if (error) return <div className="error-note">Attribution failed: {error}</div>;
  if (!attr) return <div className="panel-loading">Resolving source…</div>;

  const displayedConfidence =
    attr.confidence != null
      ? Math.min(1, attr.confidence + (reports?.confidence_bump ?? 0))
      : null;

  return (
    <div className="resolve-panel">
      <header className="panel-header">
        <span className={`state-chip state-${stateAbbr(plume.state).toLowerCase()}`}>{plume.state}</span>
        <div>
          <h2>{plume.place}, {plume.state}</h2>
          <div className="plume-id">{plume.plume_id}</div>
        </div>
      </header>

      <section className="panel-section">
        <h3>Detection</h3>
        <dl className="kv">
          <dt>Leak rate</dt><dd>{Math.round(plume.leak_rate_kg_hr)} kg CH₄/hr</dd>
          <dt>Detected</dt><dd>{plume.detected_date} · {plume.source}</dd>
          <dt>Coordinates</dt><dd>{plume.lat.toFixed(4)}, {plume.lon.toFixed(4)}</dd>
        </dl>
      </section>

      <section className="panel-section">
        <h3>Attributed source</h3>
        {attr.matched && attr.facility_name ? (
          <>
            <div className="operator-name">{attr.operator}</div>
            <dl className="kv">
              <dt>Facility</dt><dd>{attr.facility_name}</dd>
              <dt>Distance</dt><dd>{attr.distance_m} m from plume</dd>
              <dt>Confidence</dt>
              <dd>
                <span className="confidence-value">
                  {displayedConfidence != null ? `${(displayedConfidence * 100).toFixed(0)}%` : "—"}
                </span>
                {(reports?.confidence_bump ?? 0) > 0 && (
                  <span className="bump-tag">▲ community-corroborated</span>
                )}
                <span className="method-tag">
                  {attr.confidence_method === "trained_model" ? "ML model" : "rule-based scorer"}
                </span>
              </dd>
            </dl>
          </>
        ) : (
          <div className="no-match">{attr.display_statement}</div>
        )}
      </section>

      <section className="panel-section">
        <h3>Regulator &amp; rule</h3>
        <dl className="kv">
          <dt>Jurisdiction</dt><dd>{attr.regulator.regulator_name}</dd>
          <dt>Rule</dt><dd>{attr.regulator.applicable_rule}</dd>
          <dt>Summary</dt><dd>{attr.regulator.rule_summary}</dd>
          <dt>How to file</dt><dd>{attr.regulator.complaint_mechanism}</dd>
        </dl>
      </section>

      <section className="panel-section">
        <h3>Community</h3>
        {reports && <ReportsList summary={reports} />}
        <ReportForm plumeId={plume.plume_id} onSubmitted={setReports} />
        <CosignButton plumeId={plume.plume_id} onCountChange={setCosignCount} />
      </section>

      <ComplaintLetter plumeId={plume.plume_id} cosignCount={cosignCount} />
    </div>
  );
}
