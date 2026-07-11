import { useRef, useState } from "react";
import IdentityModal from "./IdentityModal";
import { getIdentity, setIdentity, type Identity } from "./identity";

export function useIdentityModal() {
  const [open, setOpen] = useState(false);
  const resolverRef = useRef<((id: Identity | null) => void) | null>(null);

  const ensureIdentity = (): Promise<Identity | null> => {
    const existing = getIdentity();
    if (existing) return Promise.resolve(existing);
    setOpen(true);
    return new Promise((resolve) => {
      resolverRef.current = resolve;
    });
  };

  const handleSubmit = (name: string, zip: string) => {
    const id = { name, zip };
    setIdentity(id);
    setOpen(false);
    resolverRef.current?.(id);
    resolverRef.current = null;
  };

  const handleCancel = () => {
    setOpen(false);
    resolverRef.current?.(null);
    resolverRef.current = null;
  };

  const modal = open ? (
    <IdentityModal onSubmit={handleSubmit} onCancel={handleCancel} />
  ) : null;

  return { ensureIdentity, modal };
}
