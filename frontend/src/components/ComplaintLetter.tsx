import { useState } from "react";
import { api, type CitizenReportInput } from "../api/client";
import InlineAlert from "./InlineAlert";
import Spinner from "./Spinner";
import StatusTracker from "./StatusTracker";

interface Props {
  plumeId: string;
  cosignCount: number;
  /** When set, the letter is a first-person citizen report grounded in these observations. */
  citizenReport?: CitizenReportInput;
}

export default function ComplaintLetter({ plumeId, cosignCount, citizenReport }: Props) {
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
      const res = await api.generateComplaint(plumeId, cosignCount, citizenReport);
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
          {loading && <Spinner />} {loading ? "Drafting…" : "Generate complaint letter"}
        </button>
      )}
      {error && <InlineAlert>{error}</InlineAlert>}
      {letter && (
        <>
          <div className="letter-meta">
            drafted by {generator === "claude" ? "Claude" : "template (offline fallback)"}
            {cosignCount > 0 && ` · ${cosignCount} co-signer${cosignCount > 1 ? "s" : ""} included`}
          </div>
          <pre className="letter-body">{letter}</pre>
          <div className="btn-row">
            <button className="btn" onClick={generate} disabled={loading}>
              {loading && <Spinner />} {loading ? "Drafting…" : "Regenerate"}
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
