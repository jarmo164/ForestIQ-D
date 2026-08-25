/** ForestIQ owner record with spatial, commercial and inheritance workflows in one operational view. */
import { useEffect, useState } from "react";
import { useLocation, useRoute } from "wouter";
import { ArrowLeft, Bookmark, FileText, Map, MessageSquareText, Plus, Save, Trees } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { OwnerWorkflowPanel } from "@/components/OwnerWorkflowPanel";
import { StatusPill } from "@/components/StatusPill";
import { api } from "@/lib/api";
import type { Owner, OwnerStatus } from "@/lib/types";

export default function OwnerDetail() {
  const [, params] = useRoute("/owners/:id");
  const [, setLocation] = useLocation();
  const ownerId = params?.id || "";
  const [owner, setOwner] = useState<Owner | null>(null);
  const [statuses, setStatuses] = useState<OwnerStatus[]>([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const refresh = () => api.get<Owner>(`/services/owners/${ownerId}`).then(setOwner).catch((err) => setError(err.message));

  useEffect(() => {
    void refresh();
    void api.get<OwnerStatus[]>("/services/owner-statuses").then(setStatuses).catch(() => undefined);
  }, [ownerId]);

  const changeStatus = async (code: string) => { await api.post(`/services/owners/${ownerId}/change-status`, { code }); void refresh(); };
  const addLog = async () => { if (!note.trim()) return; await api.post(`/services/owners/${ownerId}/log`, { message: note }); setNote(""); };

  if (!owner) return <AppShell title="Omaniku töökaart"><div className="empty-state">Laadin omaniku andmeid… {error}</div></AppShell>;

  return <AppShell title={owner.name} eyebrow={`OMANIK / ${owner.id}`}>
    <button className="back-link" onClick={() => setLocation("/owners")}><ArrowLeft size={16} /> Tagasi registrisse</button>
    {error && <div className="connection-warning">{error}</div>}
    <section className="owner-hero"><div className="owner-identity"><div className="owner-monogram">{owner.name.slice(0, 1)}</div><div><p className="eyebrow">{owner.type || "OMANIK"}</p><h2>{owner.name}</h2><div className="owner-contact">{owner.phone || "telefon puudub"}<i />{owner.email || "e-post puudub"}<i />{owner.address || "aadress puudub"}</div></div></div><div className="owner-status-action"><StatusPill value={owner.status} /><select value={owner.status || ""} onChange={(event) => void changeStatus(event.target.value)}><option value="">Vali staatus</option>{statuses.map((status) => <option value={status.id} key={status.id}>{status.id.replaceAll("_", " ")}</option>)}</select></div></section>
    <section className="detail-grid"><article className="panel property-panel"><div className="panel-heading"><div><p className="eyebrow">KINNISTUD</p><h3>Omandiportfell</h3></div><span className="count-label">{owner.cadastres?.length || 0}</span></div><div className="property-image" style={{ backgroundImage: "linear-gradient(0deg, rgba(11,43,35,.72), rgba(11,43,35,.06)), url('/manus-storage/forestiq-forest-parcel_037fa144.jpg')" }}><span><Trees size={17} /> Ruumiandmete ülevaade</span></div><div className="cadastre-list">{owner.cadastres?.map((cadastre) => <div key={cadastre.id} className="cadastre-row"><Map size={17} /><div><strong>{cadastre.name || cadastre.id}</strong><small>{cadastre.id} · {cadastre.area ? `${cadastre.area} ha` : "pindala puudub"}</small></div><Bookmark size={16} className={cadastre.marked ? "marked" : ""} /></div>) || <div className="empty-state">Katastriüksusi ei ole lisatud.</div>}</div></article><article className="panel log-panel"><div className="panel-heading"><div><p className="eyebrow">KONTAKTLOGI</p><h3>Järgmine tähelepanek</h3></div><FileText size={19} /></div><textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Lisa kõne, kokkulepe või järgmine tegevus…" /><button className="secondary-action" onClick={() => void addLog()}><Plus size={16} /> Lisa töölogisse</button><div className="quick-actions"><button><MessageSquareText size={16} /> Saada sõnum</button><button><Save size={16} /> Salvesta muudatused</button></div></article></section>
    <OwnerWorkflowPanel owner={owner} />
  </AppShell>;
}
