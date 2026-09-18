/** ForestIQ owner record with spatial, commercial and inheritance workflows in one operational view. */
import { useEffect, useState } from "react";
import { useLocation, useRoute } from "wouter";
import { AlertTriangle, ArrowLeft, BarChart3, Bookmark, CalendarClock, Clock3, FileText, GitBranch, Layers3, Map, MessageSquareText, Plus, Save, ShieldCheck, Trees } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { OwnerP1Panel } from "@/components/OwnerP1Panel";
import { OwnerWorkflowPanel } from "@/components/OwnerWorkflowPanel";
import { StatusPill } from "@/components/StatusPill";
import { api } from "@/lib/api";
import type { Owner, OwnerPortfolio, OwnerStatus } from "@/lib/types";

type OwnershipTransition = {
  id: string;
  cadastreId: string | null;
  type: string;
  occurredAt: number | null;
  sourceReference: string | null;
  recordedAt: number;
};
type Owner360Summary = {
  contactCompleteness: number;
  cadastreCount: number;
  relations: { active: number; historical: number };
  openNextActionCount: number;
  activeDealCount: number;
  signalCount: number;
  signals: { code: string; severity: string; message: string }[];
};
type Owner360Workflow = {
  nextActions: { id: string; text: string; dueAt: number; status: string; assignee?: { name: string } | null }[];
  activeDeals: { id: string; stage: string; value?: number | null; healthy: boolean; health: { code: string; severity: string; message: string }[] }[];
  recentOwnershipChanges: OwnershipTransition[];
  signals: { code: string; severity: string; message: string; target?: Record<string, unknown> }[];
};
type Owner360TimelineItem = {
  id: string;
  type: string;
  source: string;
  occurredAt: number | null;
  title: string;
  description: string;
  actor?: { name: string } | null;
};
type Owner360MapLayer = { type: "FeatureCollection"; features: { id: string; properties: { cadastreId: string; name?: string | null; area?: number | null; active: boolean; source: string } }[] };

const dateTime = (value: number | null) => value ? new Date(value).toLocaleString("et-EE") : "kuupäev puudub";
const observed = (value: number | string | null | undefined) => typeof value === "number" ? new Date(value).toLocaleDateString("et-EE") : value ? new Date(value).toLocaleDateString("et-EE") : "puudub";
const metric = (value: number | null | undefined, suffix = "") => value === null || value === undefined ? "—" : `${new Intl.NumberFormat("et-EE", { maximumFractionDigits: 2 }).format(value)}${suffix}`;

export default function OwnerDetail() {
  const [, params] = useRoute("/owners/:id");
  const [, setLocation] = useLocation();
  const ownerId = params?.id || "";
  const [owner, setOwner] = useState<Owner | null>(null);
  const [portfolio, setPortfolio] = useState<OwnerPortfolio | null>(null);
  const [summary360, setSummary360] = useState<Owner360Summary | null>(null);
  const [workflow360, setWorkflow360] = useState<Owner360Workflow | null>(null);
  const [timeline360, setTimeline360] = useState<Owner360TimelineItem[]>([]);
  const [map360, setMap360] = useState<Owner360MapLayer | null>(null);
  const [statuses, setStatuses] = useState<OwnerStatus[]>([]);
  const [transitions, setTransitions] = useState<OwnershipTransition[]>([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const refresh = () => api.get<Owner>(`/services/owners/${ownerId}`).then(setOwner).catch((err) => setError(err.message));

  useEffect(() => {
    void refresh();
    setSummary360(null); setWorkflow360(null); setTimeline360([]); setMap360(null);
    void api.get<OwnerPortfolio>(`/services/owners/${ownerId}/portfolio`).then(setPortfolio).catch(() => undefined);
    void api.get<Owner360Summary>(`/services/owners/${ownerId}/360/summary`).then(setSummary360).catch(() => undefined);
    void api.get<Owner360Workflow>(`/services/owners/${ownerId}/360/workflow`).then(setWorkflow360).catch(() => undefined);
    void api.get<Owner360TimelineItem[]>(`/services/owners/${ownerId}/360/timeline?limit=40`).then(setTimeline360).catch(() => undefined);
    void api.get<Owner360MapLayer>(`/services/owners/${ownerId}/360/map`).then(setMap360).catch(() => undefined);
    void api.get<OwnerStatus[]>("/services/owner-statuses").then(setStatuses).catch(() => undefined);
    void api.get<OwnershipTransition[]>(`/services/ownership-transitions/owners/${ownerId}`).then(setTransitions).catch(() => undefined);
  }, [ownerId]);

  const changeStatus = async (code: string) => { if (!owner) return; await api.post(`/services/owners/${ownerId}/change-status`, { code, version: owner.version }); void refresh(); };
  const addLog = async () => { if (!note.trim()) return; await api.post(`/services/owners/${ownerId}/log`, { message: note }); setNote(""); };

  if (!owner) return <AppShell title="Omaniku töökaart"><div className="empty-state">Laadin omaniku andmeid… {error}</div></AppShell>;

  return <AppShell title={owner.name} eyebrow={`OMANIK / ${owner.id}`}>
    <button className="back-link" onClick={() => setLocation("/owners")}><ArrowLeft size={16} /> Tagasi registrisse</button>
    {error && <div className="connection-warning">{error}</div>}
    <section className="owner-hero"><div className="owner-identity"><div className="owner-monogram">{owner.name.slice(0, 1)}</div><div><p className="eyebrow">{owner.type || "OMANIK"}</p><h2>{owner.name}</h2><div className="owner-contact">{owner.phone || "telefon puudub"}<i />{owner.email || "e-post puudub"}<i />{owner.address || "aadress puudub"}</div></div></div><div className="owner-status-action"><StatusPill value={owner.status} /><select value={owner.status || ""} onChange={(event) => void changeStatus(event.target.value)}><option value="">Vali staatus</option>{statuses.map((status) => <option value={status.id} key={status.id}>{status.id.replaceAll("_", " ")}</option>)}</select></div></section>
    <section className="panel owner-360-summary"><div className="panel-heading"><div><p className="eyebrow">OWNER 360</p><h3>Kiirülevaade</h3></div><ShieldCheck size={19} /></div>{summary360 ? <><div className="metrics-grid compact"><div><strong>{summary360.contactCompleteness}%</strong><span>kontaktandmed</span></div><div><strong>{summary360.cadastreCount}</strong><span>õiguspõhist kinnistut</span></div><div><strong>{summary360.relations.active}</strong><span>aktiivset seost</span></div><div><strong>{summary360.relations.historical}</strong><span>ajaloolist seost</span></div><div><strong>{summary360.openNextActionCount}</strong><span>järgmist tegevust</span></div><div><strong>{summary360.activeDealCount}</strong><span>aktiivset tehingut</span></div></div>{summary360.signals.length ? <div className="owner-360-signals">{summary360.signals.map((signal) => <span className="status-pill warning" key={signal.code}>{signal.severity} · {signal.message}</span>)}</div> : <div className="empty-state">Kiirülevaates kriitilisi signaale ei ole.</div>}</> : <div className="empty-state">Laadin Owner 360 kiirülevaadet…</div>}</section>
    {portfolio && <section className="panel owner-decision-panel"><div className="panel-heading"><div><p className="eyebrow">OTSUSETUGI</p><h3>Portfelli koondvaade ja signaalid</h3></div><BarChart3 size={19} /></div><div className="metrics-grid compact"><div><strong>{portfolio.summary.cadastreCount}</strong><span>kinnistut</span></div><div><strong>{metric(portfolio.summary.totalArea, " ha")}</strong><span>kogupindala</span></div><div><strong>{metric(portfolio.summary.forestArea, " ha")}</strong><span>metsamaa</span></div><div><strong>{metric(portfolio.summary.knownVolume, " tm")}</strong><span>teadaolev maht</span></div><div><strong>{portfolio.summary.activeNoticeCount}</strong><span>aktiivset teatist</span></div><div><strong>{portfolio.summary.activeDealCount}</strong><span>aktiivset tehingut</span></div></div><div className="owner-decision-grid"><div><h4><Clock3 size={15} /> Andmevärskus</h4>{portfolio.freshness.map((item) => <div className="decision-row" key={item.source}><span>{item.source}</span><b>{item.status}</b><small>{observed(item.observedAt)}</small></div>)}</div><div><h4><AlertTriangle size={15} /> Selgitatavad signaalid</h4>{portfolio.signals.length ? portfolio.signals.map((signal) => <div className="decision-signal" key={`${signal.code}-${signal.source}-${signal.observedAt || ""}`}><div><span className="status-pill warning">{signal.severity}</span><strong>{signal.code.replaceAll("_", " ")}</strong></div><p>{signal.reason}</p><small>{signal.source} · {observed(signal.observedAt)} · {signal.recommendedAction}</small></div>) : <div className="empty-state">Tähelepanusignaale ei ole.</div>}</div></div></section>}
    <section className="detail-grid"><article className="panel property-panel"><div className="panel-heading"><div><p className="eyebrow">KINNISTUD</p><h3>Omandiportfell</h3></div><span className="count-label">{owner.cadastres?.length || 0}</span></div><div className="property-image" style={{ backgroundImage: "linear-gradient(0deg, rgba(11,43,35,.72), rgba(11,43,35,.06)), url('/manus-storage/forestiq-forest-parcel_037fa144.jpg')" }}><span><Trees size={17} /> Ruumiandmete ülevaade</span></div><div className="cadastre-list">{owner.cadastres?.map((cadastre) => <div key={cadastre.id} className="cadastre-row"><Map size={17} /><div><strong>{cadastre.name || cadastre.id}</strong><small>{cadastre.id} · {cadastre.area ? `${cadastre.area} ha` : "pindala puudub"}</small></div><Bookmark size={16} className={cadastre.marked ? "marked" : ""} /></div>) || <div className="empty-state">Katastriüksusi ei ole lisatud.</div>}</div></article><article className="panel log-panel"><div className="panel-heading"><div><p className="eyebrow">VANA KONTAKTLOGI</p><h3>Vaba tekstiga märkus</h3></div><FileText size={19} /></div><textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Lisa legacy-märkus…" /><button className="secondary-action" onClick={() => void addLog()}><Plus size={16} /> Lisa töölogisse</button><div className="quick-actions"><button><MessageSquareText size={16} /> Saada sõnum</button><button><Save size={16} /> Salvesta muudatused</button></div></article></section>
    <OwnerP1Panel ownerId={ownerId} />
    <section className="detail-grid owner-360-grid"><article className="panel"><div className="panel-heading"><div><p className="eyebrow">KAARDIKIHT</p><h3>Õiguspõhised kinnistud</h3></div><Layers3 size={19} /></div>{map360 ? <div className="cadastre-list">{map360.features.map((feature) => <div className="cadastre-row" key={feature.id}><Map size={17} /><div><strong>{feature.properties.name || feature.properties.cadastreId}</strong><small>{feature.properties.cadastreId} · {feature.properties.area ? `${feature.properties.area} ha` : "pindala puudub"} · {feature.properties.source}</small></div><span className="status-pill">{feature.properties.active ? "AKTIIVNE" : "AJALOOLINE"}</span></div>)}{!map360.features.length && <div className="empty-state">Õiguspõhiseid kaardiobjekte ei leitud.</div>}</div> : <div className="empty-state">Laadin kaardikihti…</div>}</article><article className="panel"><div className="panel-heading"><div><p className="eyebrow">TÖÖVOOG</p><h3>Järgmised tegevused ja signaalid</h3></div><CalendarClock size={19} /></div>{workflow360 ? <div className="cadastre-list">{workflow360.nextActions.map((action) => <div className="cadastre-row" key={action.id}><CalendarClock size={17} /><div><strong>{action.text}</strong><small>{dateTime(action.dueAt)} · {action.assignee?.name || "vastutaja puudub"}</small></div><span className="status-pill">{action.status}</span></div>)}{workflow360.activeDeals.map((deal) => <div className="cadastre-row" key={deal.id}><GitBranch size={17} /><div><strong>{deal.stage.replaceAll("_", " ")}</strong><small>{deal.value ? `${deal.value} €` : "väärtus puudub"} · {deal.healthy ? "terve" : `${deal.health.length} signaali`}</small></div><span className={`status-pill ${deal.healthy ? "" : "warning"}`}>{deal.healthy ? "OK" : "RISK"}</span></div>)}{workflow360.signals.slice(0, 5).map((signal) => <div className="decision-signal" key={`${signal.code}-${signal.message}`}><div><span className="status-pill warning">{signal.severity}</span><strong>{signal.code.replaceAll("_", " ")}</strong></div><p>{signal.message}</p></div>)}{!workflow360.nextActions.length && !workflow360.activeDeals.length && !workflow360.signals.length && <div className="empty-state">Aktiivset töövoogu ei ole.</div>}</div> : <div className="empty-state">Laadin töövoo kokkuvõtet…</div>}</article></section>
    <section className="panel ownership-audit-panel"><div className="panel-heading"><div><p className="eyebrow">OWNER 360 AJAJOON</p><h3>Normaliseeritud sündmused</h3></div><Clock3 size={19} /></div><div className="ownership-audit-list">{timeline360.map((item) => <div className="ownership-audit-row" key={item.id}><div><strong>{item.title}</strong><small>{item.type.replaceAll("_", " ")} · {item.source.replaceAll("_", " ")} · {item.actor?.name || "süsteem"}</small></div><div><span>{item.description || "lisainfo puudub"}</span><small>{dateTime(item.occurredAt)}</small></div></div>)}{!timeline360.length && <div className="empty-state">Laadin normaliseeritud ajajoont…</div>}</div></section>
    <section className="panel ownership-audit-panel"><div className="panel-heading"><div><p className="eyebrow">OMANDIMUUTUSTE AUDIT</p><h3>Allikas ja töötluse aeg</h3></div><ShieldCheck size={19} /></div><div className="ownership-audit-list">{transitions.map((transition) => <div className="ownership-audit-row" key={transition.id}><div><strong>{transition.type.replaceAll("_", " ")}</strong><small>{transition.cadastreId || "katastriüksus puudub"} · sündmus {dateTime(transition.occurredAt)}</small></div><div><span>{transition.sourceReference || "allikaviide puudub"}</span><small>Töödeldud {dateTime(transition.recordedAt)}</small></div></div>)}{!transitions.length && <div className="empty-state">Selle omaniku omandimuutuste auditikirjed puuduvad.</div>}</div></section>
    <OwnerWorkflowPanel owner={owner} />
  </AppShell>;
}
