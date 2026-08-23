import type { ReactNode } from "react";

export default function MetricCard({ label, value, detail, icon }: { label: string; value: string | number; detail?: string; icon?: ReactNode }) {
  return (
    <article className="metric-card">
      <div className="metric-label"><span>{label}</span>{icon}</div>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </article>
  );
}

