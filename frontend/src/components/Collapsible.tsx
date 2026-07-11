import type { ReactNode } from "react";

interface Props {
  title: string;
  defaultOpen?: boolean;
  children: ReactNode;
}

export default function Collapsible({ title, defaultOpen = false, children }: Props) {
  return (
    <details className="collapsible" open={defaultOpen}>
      <summary className="collapsible-summary">
        {title}
        <span className="chevron">▾</span>
      </summary>
      <div className="collapsible-body">{children}</div>
    </details>
  );
}
