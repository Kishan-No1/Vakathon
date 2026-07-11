import { useEffect, useState } from "react";
import { api, type Attribution } from "../api/client";
import Skeleton from "./Skeleton";

// The real cross-border demo pair: same Tanager-1 overpass 2026-06-07, ~5 km apart
export const DEMO_PAIR = {
  NM: "tan20260607t190346c80s4001-F",
  TX: "tan20260607t190346c80s4001-K",
};

function Side({ attr, state }: { attr: Attribution; state: "NM" | "TX" }) {
  return (
    <div className={`compare-side compare-${state.toLowerCase()}`}>
      <div className={`state-chip state-${state.toLowerCase()}`}>{state}</div>
      <h3>{state === "NM" ? "Jal, New Mexico" : "Mentone, Texas"}</h3>
      <div className="compare-plume-id">{attr.plume_id}</div>

      <div className="compare-row">
        <span className="compare-label">Operator</span>
        {attr.matched ? (
          <strong>{attr.operator}</strong>
        ) : (
          <em className="muted">Not identified</em>
        )}
      </div>
      <div className="compare-row">
        <span className="compare-label">Regulator</span>
        <span>{attr.regulator.regulator_name}</span>
      </div>
      <div className="compare-row">
        <span className="compare-label">Rule</span>
        <span>{attr.regulator.applicable_rule}</span>
      </div>
      <div className="compare-row">
        <span className="compare-label">What it requires</span>
        <span>{attr.regulator.rule_summary}</span>
      </div>
      <div className="compare-verdict">
        {state === "NM"
          ? "✓ Named operator, 98% gas-capture mandate, enforceable complaint path"
          : "✗ No capture mandate, flaring exceptions routine, no operator accountability"}
      </div>
    </div>
  );
}

export default function ComparisonView({ onClose }: { onClose: () => void }) {
  const [nm, setNm] = useState<Attribution | null>(null);
  const [tx, setTx] = useState<Attribution | null>(null);

  useEffect(() => {
    api.attribution(DEMO_PAIR.NM).then(setNm);
    api.attribution(DEMO_PAIR.TX).then(setTx);
  }, []);

  return (
    <div className="compare-overlay" onClick={onClose}>
      <div className="compare-modal" onClick={(e) => e.stopPropagation()}>
        <header className="compare-header">
          <div>
            <h2>Same basin. Same day. 5 km apart. Different rules.</h2>
            <p>
              Two methane plumes from the same Tanager-1 overpass on 2026-06-07,
              straddling the TX/NM state line in the Permian basin.
            </p>
          </div>
          <button className="btn" onClick={onClose}>✕ Close</button>
        </header>

        {nm && tx ? (
          <div className="compare-grid">
            <Side attr={nm} state="NM" />
            <Side attr={tx} state="TX" />
          </div>
        ) : (
          <Skeleton lines={6} />
        )}

        <footer className="compare-footer">
          The gap isn't detection — both plumes are equally visible from space.
          The gap is what a resident can do about them.
        </footer>
      </div>
    </div>
  );
}
