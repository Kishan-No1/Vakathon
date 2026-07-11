import { useState } from "react";

interface Props {
  onSubmit: (name: string, zip: string) => void;
  onCancel: () => void;
}

export default function IdentityModal({ onSubmit, onCancel }: Props) {
  const [name, setName] = useState("");
  const [zip, setZip] = useState("");

  const submit = () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    onSubmit(trimmed, zip.trim());
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h2>Identify yourself to neighbors</h2>
        <p className="modal-hint">
          Shown alongside your report or co-sign so neighbors know it's a real resident.
        </p>
        <label className="modal-field">
          Your name
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Jane Rivera"
          />
        </label>
        <label className="modal-field">
          ZIP code
          <input
            value={zip}
            onChange={(e) => setZip(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="79701"
          />
        </label>
        <div className="btn-row">
          <button className="btn btn-primary" onClick={submit} disabled={!name.trim()}>
            Continue
          </button>
          <button className="btn" onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  );
}
