/** ForestIQ Landscape Desk design: compact, semantically meaningful field-status markers. */
const palette: Record<string, string> = { ASSIGNED: "assigned", WAITS_FOR_EVALUATION: "evaluate", IN_PROGRESS: "progress", DEAL: "deal", NOT_INTERESTED: "risk", UNREACHABLE: "risk", EVALUATED_NEEDS_ACTION: "attention" };
export function StatusPill({ value }: { value?: string | null }) { return <span className={`status-pill ${palette[value || ""] || "neutral"}`}><i />{(value || "MÄÄRAMATA").replaceAll("_", " ")}</span>; }
