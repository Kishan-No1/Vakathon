import { useEffect, useState } from "react";
import { api, type CosignSummary } from "../api/client";
import { getIdentity } from "./identity";

interface Props {
  plumeId: string;
  onCountChange: (count: number) => void;
}

export default function CosignButton({ plumeId, onCountChange }: Props) {
  const [summary, setSummary] = useState<CosignSummary | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.cosigns(plumeId).then((s) => {
      setSummary(s);
      onCountChange(s.count);
    });
  }, [plumeId]);

  const identity = getIdentity();
  const alreadySigned = summary?.signers.some(
    (s) => s.name === identity?.name && s.zip === identity?.zip,
  );

  const sign = async () => {
    const id = getIdentity(true); // prompts for name+zip if not stored
    if (!id) return;
    setBusy(true);
    try {
      const s = await api.cosign(plumeId, id.name, id.zip);
      setSummary(s);
      onCountChange(s.count);
    } finally {
      setBusy(false);
    }
  };

  const count = summary?.count ?? 0;
  return (
    <div className="cosign">
      <button
        className="btn btn-cosign"
        onClick={sign}
        disabled={busy || alreadySigned}
      >
        {alreadySigned ? "✓ You co-signed" : "Co-sign this complaint"}
      </button>
      <span className="cosign-count">
        <strong>{count}</strong> resident{count === 1 ? "" : "s"} co-signed
      </span>
    </div>
  );
}
