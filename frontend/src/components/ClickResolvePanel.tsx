import { useEffect, useState } from "react";
import {
  api,
  stateAbbr,
  type Attribution,
  type Plume,
  type ReportSummary,
} from "../api/client";
import Collapsible from "./Collapsible";
import ComplaintLetter from "./ComplaintLetter";
import InlineAlert from "./InlineAlert";
import Skeleton from "./Skeleton";
import CosignButton from "../community/CosignButton";
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

  if (error) return <InlineAlert>Attribution failed: {error}</InlineAlert>;
  if (!attr) return <Skeleton lines={5} />;

  const displayedConfidence =
    attr.confidence != null
      ? Math.min(1, attr.confidence + (reports?.confidence_bump ?? 0))
      : null;
  const confidenceBump = reports?.confidence_bump ?? 0;

  return (
    <div className="resolve-panel">
      <header className="panel-header">
        <span className={`state-chip state-${stateAbbr(plume.state).toLowerCase()}`}>{plume.state}</span>
        <div>
          <h2>{plume.place}, {plume.state}</h2>
          <div className="plume-id">{plume.plume_id}</div>
        </div>
      </header>

      <div className="panel-summary">
        {attr.matched && attr.facility_name ? (
          <>
            <div className="operator-name">{attr.operator}</div>
            <div className="facility-name">{attr.facility_name}</div>
          </>
        ) : (
          <div className="no-match">{attr.display_statement}</div>
        )}
        <div className="stat-chips">
          <span className="stat-chip">{Math.round(plume.leak_rate_kg_hr)} kg CH₄/hr</span>
          {attr.matched && displayedConfidence != null && (
            <span className="stat-chip">{(displayedConfidence * 100).toFixed(0)}% confidence</span>
          )}
          {confidenceBump > 0 && (
            <span className="stat-chip stat-chip-bump">▲ community-corroborated</span>
          )}
          {attr.matched && attr.distance_m != null && (
            <span className="stat-chip">{attr.distance_m} m away</span>
          )}
          <span className="stat-chip stat-chip-rule">
            {attr.regulator.regulator_name} · {attr.regulator.applicable_rule}
          </span>
        </div>
      </div>

      <Collapsible title="Detection details">
        <dl className="kv">
          <dt>Detected</dt><dd>{plume.detected_date} · {plume.source}</dd>
          <dt>Coordinates</dt><dd>{plume.lat.toFixed(4)}, {plume.lon.toFixed(4)}</dd>
          {attr.matched && (
            <>
              <dt>Method</dt>
              <dd>{attr.confidence_method === "trained_model" ? "ML model" : "rule-based scorer"}</dd>
            </>
          )}
        </dl>
      </Collapsible>

      <Collapsible title="Full rule & how to file">
        <dl className="kv">
          <dt>Summary</dt><dd>{attr.regulator.rule_summary}</dd>
          <dt>How to file</dt><dd>{attr.regulator.complaint_mechanism}</dd>
        </dl>
      </Collapsible>

      <section className="panel-section">
        <h3>Community</h3>
        {reports && <ReportsList summary={reports} />}
        <div className="form-hint">
          Saw something yourself? Switch to <strong>Citizen Report</strong> (top
          right) to file a first-hand report.
        </div>
        <CosignButton plumeId={plume.plume_id} onCountChange={setCosignCount} />
      </section>

      <ComplaintLetter plumeId={plume.plume_id} cosignCount={cosignCount} />
    </div>
  );
}
