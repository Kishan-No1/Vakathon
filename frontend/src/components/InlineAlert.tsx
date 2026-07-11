import type { ReactNode } from "react";

export default function InlineAlert({ children }: { children: ReactNode }) {
  return (
    <div className="inline-alert" role="alert">
      {children}
    </div>
  );
}
