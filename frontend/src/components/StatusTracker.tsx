import { useEffect, useState } from "react";

// Mocked complaint lifecycle (plan: no real regulator integration).
// Advances submitted → acknowledged on a timer to demo the flow.
const STAGES = ["submitted", "acknowledged", "resolved"] as const;

export default function StatusTracker({ complaintKey }: { complaintKey: string }) {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    setStage(0);
    const t = setTimeout(() => setStage(1), 6000); // mock acknowledgement
    return () => clearTimeout(t);
  }, [complaintKey]);

  return (
    <div className="status-tracker">
      {STAGES.map((s, i) => (
        <div key={s} className={`status-step ${i <= stage ? "done" : ""}`}>
          <span className="status-dot" />
          <span className="status-label">{s}</span>
          {i < STAGES.length - 1 && <span className="status-bar" />}
        </div>
      ))}
      <div className="status-note">status tracking is mocked for the demo</div>
    </div>
  );
}
