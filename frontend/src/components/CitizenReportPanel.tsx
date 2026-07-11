import { useEffect, useState } from "react";
import {
  stateAbbr,
  type CitizenReportInput,
  type Plume,
  type ReportSummary,
} from "../api/client";
import ComplaintLetter from "./ComplaintLetter";
import ReportForm from "../community/ReportForm";

/**
 * Citizen Report mode: the resident clicks a plume, describes what they
 * personally observed, and gets a complaint letter grounded in THEIR input
 * (the satellite detection is cited as supporting context, not the lead).
 */
export default function CitizenReportPanel({ plume }: { plume: Plume }) {
  const [details, setDetails] = useState<CitizenReportInput | null>(null);
  const [summary, setSummary] = useState<ReportSummary | null>(null);

  // A new plume selection starts a fresh report
  useEffect(() => {
    setDetails(null);
    setSummary(null);
  }, [plume.plume_id]);

  return (
    <div className="resolve-panel">
      <header className="panel-header">
        <span className={`state-chip state-${stateAbbr(plume.state).toLowerCase()}`}>
          {plume.state}
        </span>
        <div>
          <h2>
            {plume.place}, {plume.state}
          </h2>
          <div className="plume-id">{plume.plume_id}</div>
        </div>
      </header>

      <div className="panel-summary">
        <p className="citizen-intro">
          Tell us what <strong>you</strong> saw, smelled, or heard near this
          site. Your first-hand report becomes the basis of the complaint
          letter — the satellite detection ({Math.round(plume.leak_rate_kg_hr)}{" "}
          kg CH₄/hr on {plume.detected_date}) is cited as supporting evidence.
        </p>
      </div>

      <section className="panel-section">
        <h3>Your observations</h3>
        <ReportForm
          plumeId={plume.plume_id}
          onSubmitted={setSummary}
          onDetails={setDetails}
          alwaysOpen
        />
        {summary && (
          <div className="form-hint">
            ✓ Report saved — {summary.count} community report
            {summary.count === 1 ? "" : "s"} on this plume so far.
          </div>
        )}
      </section>

      {details ? (
        <ComplaintLetter
          plumeId={plume.plume_id}
          cosignCount={0}
          citizenReport={details}
        />
      ) : (
        <section className="panel-section">
          <h3>Complaint letter</h3>
          <div className="form-hint">
            Submit your observations above to unlock a letter based on your
            report.
          </div>
        </section>
      )}
    </div>
  );
}
