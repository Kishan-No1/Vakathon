import { useState } from "react";
import { api, type ReportSummary } from "../api/client";
import { getIdentity } from "./identity";

interface Props {
  plumeId: string;
  onSubmitted: (summary: ReportSummary) => void;
}

export default function ReportForm({ plumeId, onSubmitted }: Props) {
  const [open, setOpen] = useState(false);
  const [smell, setSmell] = useState(false);
  const [flare, setFlare] = useState(false);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    const id = getIdentity(true);
    if (!id) return;
    setBusy(true);
    setError(null);

    // Geolocation is best-effort — deny/timeout just submits without coords
    const coords = await new Promise<{ lat: number | null; lon: number | null }>(
      (resolve) => {
        if (!navigator.geolocation) return resolve({ lat: null, lon: null });
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
          () => resolve({ lat: null, lon: null }),
          { timeout: 3000 },
        );
      },
    );

    try {
      const summary = await api.submitReport({
        plume_id: plumeId,
        name: id.name,
        zip_code: id.zip,
        smell,
        visible_flare: flare,
        notes,
        ...coords,
      });
      onSubmitted(summary);
      setOpen(false);
      setSmell(false);
      setFlare(false);
      setNotes("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "submit failed");
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button className="btn" onClick={() => setOpen(true)}>
        Report what you see near this site
      </button>
    );
  }

  return (
    <div className="report-form">
      <label>
        <input type="checkbox" checked={smell} onChange={(e) => setSmell(e.target.checked)} />
        I smell gas / rotten-egg odor
      </label>
      <label>
        <input type="checkbox" checked={flare} onChange={(e) => setFlare(e.target.checked)} />
        I can see a flare, venting, or haze
      </label>
      <textarea
        placeholder="Anything else you noticed (optional)"
        value={notes}
        maxLength={500}
        onChange={(e) => setNotes(e.target.value)}
      />
      {error && <div className="error-note">{error}</div>}
      <div className="btn-row">
        <button className="btn btn-primary" onClick={submit} disabled={busy || (!smell && !flare && !notes)}>
          {busy ? "Submitting…" : "Submit report"}
        </button>
        <button className="btn" onClick={() => setOpen(false)}>Cancel</button>
      </div>
      <div className="form-hint">Your location is attached if you allow it — it helps corroborate the detection.</div>
    </div>
  );
}
