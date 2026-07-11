import { useState } from "react";
import type { ReportedPlume } from "../api/client";

interface Props {
  onAdd: (p: Omit<ReportedPlume, "id">) => void;
  count: number;
}

/**
 * "Report a new plume" mode: a resident reports methane emissions at a spot
 * that ISN'T in the satellite data. Collects the same observations as a
 * citizen report plus manual lat/lon, then plots a RED dot on the map. It
 * deliberately does NOT generate a complaint letter or hit the backend —
 * these are session-local markers of potential new plumes for follow-up.
 */
export default function NewPlumePanel({ onAdd, count }: Props) {
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [smell, setSmell] = useState(false);
  const [flare, setFlare] = useState(false);
  const [notes, setNotes] = useState("");
  const [justAdded, setJustAdded] = useState(false);

  const latN = parseFloat(lat);
  const lonN = parseFloat(lon);
  const coordsValid =
    Number.isFinite(latN) && latN >= -90 && latN <= 90 &&
    Number.isFinite(lonN) && lonN >= -180 && lonN <= 180;
  const hasObs = smell || flare || notes.trim().length > 0;

  const touch = () => setJustAdded(false);

  const add = () => {
    if (!coordsValid || !hasObs) return;
    onAdd({ lat: latN, lon: lonN, smell, visible_flare: flare, notes: notes.trim() });
    setLat("");
    setLon("");
    setSmell(false);
    setFlare(false);
    setNotes("");
    setJustAdded(true);
  };

  return (
    <div className="resolve-panel">
      <header className="panel-header">
        <span className="state-chip state-reported">NEW</span>
        <div>
          <h2>Report a new plume</h2>
          <div className="plume-id">not yet detected by satellite</div>
        </div>
      </header>

      <div className="panel-summary">
        <p className="citizen-intro">
          Seeing methane emissions somewhere that isn't on the map? Enter the
          location and what you noticed — it appears as a{" "}
          <strong>red dot</strong> marking a potential new plume for follow-up.
          No complaint letter is generated here.
        </p>
      </div>

      <section className="panel-section">
        <h3>Location</h3>
        <div className="coord-row">
          <label>
            Latitude
            <input
              type="number"
              step="any"
              placeholder="e.g. 32.05"
              value={lat}
              onChange={(e) => { setLat(e.target.value); touch(); }}
            />
          </label>
          <label>
            Longitude
            <input
              type="number"
              step="any"
              placeholder="e.g. -103.60"
              value={lon}
              onChange={(e) => { setLon(e.target.value); touch(); }}
            />
          </label>
        </div>
        {lat !== "" && lon !== "" && !coordsValid && (
          <div className="form-hint">
            Enter a valid latitude (−90…90) and longitude (−180…180).
          </div>
        )}
      </section>

      <section className="panel-section">
        <h3>What you noticed</h3>
        <div className="report-form">
          <label>
            <input
              type="checkbox"
              checked={smell}
              onChange={(e) => { setSmell(e.target.checked); touch(); }}
            />
            I smell gas / rotten-egg odor
          </label>
          <label>
            <input
              type="checkbox"
              checked={flare}
              onChange={(e) => { setFlare(e.target.checked); touch(); }}
            />
            I can see a flare, venting, or haze
          </label>
          <textarea
            placeholder="Anything else you noticed (optional)"
            value={notes}
            maxLength={500}
            onChange={(e) => { setNotes(e.target.value); touch(); }}
          />
          <div className="btn-row">
            <button
              className="btn btn-primary"
              onClick={add}
              disabled={!coordsValid || !hasObs}
            >
              Add plume to map
            </button>
          </div>
          {justAdded && (
            <div className="form-hint">
              ✓ Red marker added — {count} reported plume{count === 1 ? "" : "s"}{" "}
              this session.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
