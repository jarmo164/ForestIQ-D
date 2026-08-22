/** ForestIQ Landscape Desk design: neutral metric cards, offset by a narrow operational color bar. */
import type { LucideIcon } from "lucide-react";
export function Metric({ label, value, detail, icon: Icon, tone = "green" }: { label: string; value: string | number; detail: string; icon: LucideIcon; tone?: "green" | "moss" | "ochre" | "rose" }) { return <article className={`metric-card ${tone}`}><div className="metric-icon"><Icon size={18} /></div><p>{label}</p><strong>{value}</strong><span>{detail}</span></article>; }
