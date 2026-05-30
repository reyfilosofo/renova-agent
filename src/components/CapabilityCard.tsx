import type { AgentCapability } from "@/lib/renova";

export function CapabilityCard({ capability }: { capability: AgentCapability }) {
  return (
    <article className="card">
      <div className="cardHeader">
        <h3>{capability.name}</h3>
        <span className="status">{capability.status}</span>
      </div>
      <p>{capability.description}</p>
    </article>
  );
}
