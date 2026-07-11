import { useState } from "react";
import { api } from "../api/client";
import StatusTracker from "./StatusTracker";

interface Props {
  plumeId: string;
  cosignCount: number;
}

export default function ComplaintLetter({ plumeId, cosignCount }: Props) {
  const [letter, setLetter] = useState<string | null>(null);
  const [generator, setGenerator] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const generate = async () => {
    setLoading(true);
    setError(null);
    setSubmitted(false);
    try {
      const res = await api.generateComplaint(plumeId, cosignCount);
      setLetter(res.letter);
      setGenerator(res.generator);
    } catch (e) {
      setError(e instanceof Error ? e.message : "generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel-section">
      <h3>Complaint letter</h3>
      {!letter && (
        <button className="btn btn-primary" onClick={generate} disabled={loading}>
          {loading ? "Drafting…" : "Generate complaint letter"}
        </button>
      )}
      {error && <div className="error-note">{error}</div>}
      {letter && (
        <>
          <div className="letter-meta">
            drafted by {generator === "claude" ? "Claude" : "template (offline fallback)"}
            {cosignCount > 0 && ` · ${cosignCount} co-signer${cosignCount > 1 ? "s" : ""} included`}
          </div>
          <pre className="letter-body">{letter}</pre>
          <div className="btn-row">
            <button className="btn" onClick={generate} disabled={loading}>
              {loading ? "Drafting…" : "Regenerate"}
            </button>
            {!submitted && (
              <button className="btn btn-primary" onClick={() => setSubmitted(true)}>
                Submit to regulator
              </button>
            )}
          </div>
          {submitted && <StatusTracker complaintKey={`${plumeId}-${letter.length}`} />}
        </>
      )}
    </section>
  );
}
