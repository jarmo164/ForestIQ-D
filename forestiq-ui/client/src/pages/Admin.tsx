/** ForestIQ administration: identity, workflow configuration and WFS generation controls. */
import { useCallback, useEffect, useState } from "react";
import { BarChart3, Database, RefreshCw, RotateCcw, ShieldCheck, UserCog } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { OwnerStatus } from "@/lib/types";

type AdminUser = { id: string; name: string; privileges: string[] };
type WfsGeneration = {
  id: string;
  sequence: number;
  status: string;
  featureCount: number;
  cadastreCount: number;
  validation: Record<string, unknown>;
  observedAt?: number | null;
  publishedAt?: number | null;
};
type WfsManifest = {
  id: string;
  key: string;
  sourceLayer: string;
  enabled: boolean;
  allowSchemaDrift: boolean;
  health: string;
  freshnessAt?: number | null;
  lastVerifiedAt?: number | null;
  activeGeneration?: WfsGeneration | null;
  latestGeneration?: WfsGeneration | null;
  rollbackGeneration?: WfsGeneration | null;
};

const dateTime = (value?: number | null) =>
  value ? new Intl.DateTimeFormat("et-EE", { dateStyle: "short", timeStyle: "short" }).format(new Date(value)) : "—";

export default function Admin() {
  const [statuses, setStatuses] = useState<OwnerStatus[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [wfsLayers, setWfsLayers] = useState<WfsManifest[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadWfs = useCallback(async () => {
    const records = await api.get<WfsManifest[]>("/services/admin/wfs/layers");
    setWfsLayers(records);
  }, []);

  useEffect(() => {
    Promise.all([
      api.get<OwnerStatus[]>("/services/owner-statuses"),
      api.get<AdminUser[]>("/services/admin/users"),
      api.get<WfsManifest[]>("/services/admin/wfs/layers"),
    ])
      .then(([ownerStatuses, allUsers, layers]) => {
        setStatuses(ownerStatuses);
        setUsers(allUsers);
        setWfsLayers(layers);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const refreshLayer = async (id: string) => {
    try {
      setError("");
      await api.post(`/services/admin/wfs/layers/${id}/refresh`, {});
      setNotice("WFS kihi uus staging-generatsioon pandi järjekorda.");
      await loadWfs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "WFS värskendust ei saanud käivitada.");
    }
  };

  const refreshAll = async () => {
    try {
      setError("");
      await api.post("/services/admin/wfs/layers/refresh-all", {});
      setNotice("Kõigi lubatud WFS kihtide generatsioonivärskendus pandi järjekorda.");
      await loadWfs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Täisvärskendust ei saanud käivitada.");
    }
  };

  const verifyLayer = async (id: string) => {
    try {
      setError("");
      const result = await api.post<{ verification: { ok: boolean } }>(`/services/admin/wfs/layers/${id}/verify`, {});
      setNotice(result.verification.ok ? "Aktiivne WFS generatsioon läbis süvaverifitseerimise." : "Süvaverifitseerimine leidis erinevuse.");
      await loadWfs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Süvaverifitseerimine ebaõnnestus.");
    }
  };

  const rollback = async (generationId: string) => {
    try {
      setError("");
      await api.post(`/services/admin/wfs/generations/${generationId}/rollback`, {});
      setNotice("Eelmine toimiv WFS generatsioon taastati aktiivseks.");
      await loadWfs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rollback ebaõnnestus.");
    }
  };

  const approveSchemaDrift = async (generationId: string) => {
    const reason = window.prompt("Sisesta skeeminihke kinnitamise auditi põhjus");
    if (!reason?.trim()) return;
    try {
      setError("");
      await api.post(`/services/admin/wfs/generations/${generationId}/approve-schema-drift`, { reason: reason.trim() });
      await api.post(`/services/admin/wfs/generations/${generationId}/publish`, {});
      setNotice("Skeeminihe kinnitati auditeeritult ja generatsioon avaldati.");
      await loadWfs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Skeeminihke kinnitamine ebaõnnestus.");
    }
  };

  return (
    <AppShell title="Haldus" eyebrow="FORESTIQ / SÜSTEEMI SEADED">
      {notice && <div className="success-notice">{notice}</div>}
      {error && <div className="connection-warning">{error}</div>}

      <section className="admin-grid">
        <article className="panel">
          <div className="panel-heading"><div><p className="eyebrow">KASUTAJAD</p><h3>Meeskonna õigused</h3></div><UserCog size={20} /></div>
          {users.map((user) => <div className="admin-row" key={user.id}><div><strong>{user.name}</strong><small>{user.id}</small></div><span>{user.privileges.join(" · ") || "õigusi pole"}</span></div>)}
        </article>
        <article className="panel">
          <div className="panel-heading"><div><p className="eyebrow">STAATUSED</p><h3>Omaniku töövoog</h3></div><ShieldCheck size={20} /></div>
          {statuses.map((status) => <div className="admin-row" key={status.id}><div className="status-code"><i style={{ background: `#${status.colorHex}` }} /><strong>{status.id.replaceAll("_", " ")}</strong></div><span>{status.durationDays} päeva</span></div>)}
        </article>
        <article className="panel insight-card"><BarChart3 size={26} /><p className="eyebrow">STATISTIKA</p><h3>Vaata muutuste ajalugu</h3><p>Kasuta kasutajastatistikat, et näha staatusemuudatusi ja töökoormuse liikumist.</p></article>
      </section>

      <section className="panel mt-6 p-5">
        <div className="panel-heading">
          <div><p className="eyebrow">METSAREGISTER WFS</p><h3>Generatsioonid ja tervis</h3></div>
          <div className="flex items-center gap-2"><Database size={20} /><button className="secondary-action" onClick={() => void refreshAll()}><RefreshCw size={15} /> Täisvärskendus</button></div>
        </div>
        <div className="space-y-3">
          {wfsLayers.map((layer) => (
            <article key={layer.id} className="rounded-xl border border-border p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2"><strong>{layer.sourceLayer}</strong><span className={`status-pill ${layer.health === "HEALTHY" ? "" : "warning"}`}>{layer.health}</span></div>
                  <small>Värskus {dateTime(layer.freshnessAt)} · kontroll {dateTime(layer.lastVerifiedAt)}</small>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Aktiivne: {layer.activeGeneration ? `#${layer.activeGeneration.sequence} · ${layer.activeGeneration.featureCount} objekti / ${layer.activeGeneration.cadastreCount} katastrit` : "puudub"}
                  </p>
                  {layer.latestGeneration?.validation?.schemaDrift === true && (
                    <p className="mt-1 text-xs text-destructive">Uusim generatsioon on blokeeritud skeeminihke tõttu.</p>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="secondary-action" onClick={() => void refreshLayer(layer.id)}><RefreshCw size={14} /> Värskenda</button>
                  <button className="secondary-action" onClick={() => void verifyLayer(layer.id)}>Kontrolli</button>
                  {layer.rollbackGeneration && <button className="secondary-action" onClick={() => void rollback(layer.rollbackGeneration!.id)}><RotateCcw size={14} /> Rollback</button>}
                  {layer.allowSchemaDrift && layer.latestGeneration?.status === "FAILED" && layer.latestGeneration.validation?.schemaDrift === true && (
                    <button className="secondary-action" onClick={() => void approveSchemaDrift(layer.latestGeneration!.id)}>Kinnita skeeminihe</button>
                  )}
                </div>
              </div>
            </article>
          ))}
          {!wfsLayers.length && <div className="empty-state">WFS manifestid puuduvad.</div>}
        </div>
      </section>
    </AppShell>
  );
}
