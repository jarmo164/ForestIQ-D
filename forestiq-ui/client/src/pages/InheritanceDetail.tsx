/** Detailed inheritance workspace with in-place refresh after each supported mutation. */
import { useCallback, useEffect, useState } from "react";
import { CalendarClock, ChevronLeft, ExternalLink, Gavel, History, Plus, Save, UserRound, UsersRound } from "lucide-react";
import { Link, useRoute } from "wouter";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { InheritanceCase } from "@/lib/types";

const statusOptions = ["NEW", "IN_PROGRESS", "WAITING", "COMPLETED", "CLOSED"] as const;

function statusLabel(status: string): string {
  return status.replaceAll("_", " ");
}

function dateLabel(value?: string | null): string {
  if (!value) return "—";
  return new Date(`${value}T00:00:00`).toLocaleDateString("et-EE", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function timestampLabel(value?: number | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("et-EE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function InheritanceDetail() {
  const [, params] = useRoute("/inheritance/:id");
  const caseId = params?.id;
  const [inheritanceCase, setInheritanceCase] = useState<InheritanceCase | null>(null);
  const [status, setStatus] = useState("NEW");
  const [note, setNote] = useState("");
  const [heirName, setHeirName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const refresh = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const freshCase = await api.get<InheritanceCase>(`/services/inheritance/cases/${caseId}`);
      setInheritanceCase(freshCase);
      setStatus(freshCase.status);
      setError("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Pärimisjuhtumit ei saanud laadida.");
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const saveStatus = async () => {
    if (!inheritanceCase || status === inheritanceCase.status) return;
    setSaving(true);
    try {
      const updatedCase = await api.patch<InheritanceCase>(`/services/inheritance/cases/${inheritanceCase.id}/status`, {
        status,
        version: inheritanceCase.version,
        comment: `Juhtumi staatus muudeti väärtuseks ${statusLabel(status)}.`,
      });
      setInheritanceCase(updatedCase);
      setStatus(updatedCase.status);
      setError("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Juhtumi staatust ei saanud muuta.");
      await refresh();
    } finally {
      setSaving(false);
    }
  };

  const addNote = async () => {
    if (!inheritanceCase || !note.trim()) return;
    setSaving(true);
    try {
      await api.post(`/services/inheritance/cases/${inheritanceCase.id}/events`, {
        content: note.trim(),
        version: inheritanceCase.version,
      });
      setNote("");
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Märkust ei saanud lisada.");
      await refresh();
    } finally {
      setSaving(false);
    }
  };

  const addHeir = async () => {
    if (!inheritanceCase || !heirName.trim()) return;
    setSaving(true);
    try {
      await api.post(`/services/inheritance/cases/${inheritanceCase.id}/heirs`, {
        displayName: heirName.trim(),
        version: inheritanceCase.version,
      });
      setHeirName("");
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Pärijat ei saanud lisada.");
      await refresh();
    } finally {
      setSaving(false);
    }
  };

  if (loading && !inheritanceCase) {
    return <AppShell title="Pärimisjuhtum" eyebrow="JUHTUMID / PÄRIMINE"><div className="empty-state">Laadin pärimisjuhtumit…</div></AppShell>;
  }

  if (!inheritanceCase) {
    return <AppShell title="Pärimisjuhtum" eyebrow="JUHTUMID / PÄRIMINE"><Link className="back-link" href="/inheritance"><ChevronLeft size={16} /> Tagasi pärimisjuhtumitesse</Link><div className="connection-warning">{error || "Pärimisjuhtumit ei leitud."}</div></AppShell>;
  }

  return (
    <AppShell title="Pärimisjuhtumi detail" eyebrow="JUHTUMID / PÄRIMINE">
      <Link className="back-link" href="/inheritance"><ChevronLeft size={16} /> Tagasi pärimisjuhtumitesse</Link>
      {error && <div className="connection-warning">{error}</div>}

      <section className="inheritance-case-hero">
        <div>
          <p className="eyebrow">PÄRIMISJUHTUM</p>
          <h2>{inheritanceCase.owner.name}</h2>
          <p>{inheritanceCase.sourceNoticeNumber ? `Ametlik teade ${inheritanceCase.sourceNoticeNumber}` : "Käsitsi avatud pärimisjuhtum"}</p>
          <Link href={`/owners/${inheritanceCase.owner.id}`} className="inheritance-owner-link">Ava omanikukaart <ExternalLink size={14} /></Link>
        </div>
        <div className="inheritance-status-card">
          <span>Juhtumi staatus</span>
          <strong>{statusLabel(inheritanceCase.status)}</strong>
          <small>Viimati uuendatud {timestampLabel(inheritanceCase.updatedAt)}</small>
        </div>
      </section>

      <section className="inheritance-detail-grid">
        <article className="inheritance-detail-panel">
          <div className="inheritance-panel-heading"><div><p className="eyebrow">TEADE JA TÄHTAJAD</p><h3><Gavel size={18} /> Ametlik teade</h3></div></div>
          <dl className="inheritance-facts">
            <div><dt>Teate number</dt><dd>{inheritanceCase.sourceNoticeNumber || "Puudub"}</dd></div>
            <div><dt>Avaldamise kuupäev</dt><dd>{dateLabel(inheritanceCase.announcementDate)}</dd></div>
            <div><dt>Surmakuupäev</dt><dd>{dateLabel(inheritanceCase.deathDate)}</dd></div>
            <div><dt>Sertifitseerimise tähtaeg</dt><dd className={inheritanceCase.certificationDeadline ? "deadline-value" : ""}>{dateLabel(inheritanceCase.certificationDeadline)}</dd></div>
            <div><dt>Notar</dt><dd>{inheritanceCase.notaryName || "Määramata"}{inheritanceCase.notaryPhone ? ` · ${inheritanceCase.notaryPhone}` : ""}</dd></div>
            <div><dt>Juhtumi algus</dt><dd>{timestampLabel(inheritanceCase.startedAt)}</dd></div>
          </dl>
          {inheritanceCase.sourceUrl && <a className="official-notice-link" href={inheritanceCase.sourceUrl} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Ava ametlik teade</a>}
        </article>

        <article className="inheritance-detail-panel">
          <div className="inheritance-panel-heading"><div><p className="eyebrow">VASTUTUS</p><h3><UserRound size={18} /> Juhtimine</h3></div></div>
          <div className="inheritance-assignee"><span>Vastutaja</span><strong>{inheritanceCase.assignedTo?.name || "Määramata"}</strong></div>
          <label className="inheritance-control-label" htmlFor="inheritance-status">Staatus
            <select id="inheritance-status" value={status} disabled={saving} onChange={(event) => setStatus(event.target.value)}>
              {statusOptions.map((option) => <option key={option} value={option}>{statusLabel(option)}</option>)}
            </select>
          </label>
          <button className="secondary-action inheritance-save-status" disabled={saving || status === inheritanceCase.status} onClick={() => void saveStatus()}><Save size={15} /> Salvesta staatus</button>
        </article>

        <article className="inheritance-detail-panel inheritance-wide-panel">
          <div className="inheritance-panel-heading"><div><p className="eyebrow">PÄRIJAD</p><h3><UsersRound size={18} /> Pärijad</h3></div><span>{inheritanceCase.heirs.length} pärijat</span></div>
          <div className="inheritance-heir-list">
            {inheritanceCase.heirs.map((heir) => <div className="inheritance-heir" key={heir.id}><div><strong>{heir.displayName}</strong><p>{heir.relationToDeceased || "Seos täpsustamata"}{heir.inheritanceShare ? ` · ${heir.inheritanceShare}` : ""}</p></div><div><span>{heir.contactStatus || "Kontaktistaatus puudub"}</span><small>{heir.assignedTo?.name || "Vastutaja puudub"}</small></div></div>)}
            {!inheritanceCase.heirs.length && <div className="empty-state">Pärijaid ei ole veel lisatud.</div>}
          </div>
          <div className="inheritance-inline-form">
            <label htmlFor="inheritance-heir">Lisa pärija</label>
            <input id="inheritance-heir" value={heirName} disabled={saving} onChange={(event) => setHeirName(event.target.value)} placeholder="Pärija nimi" />
            <button className="secondary-action" disabled={saving || !heirName.trim()} onClick={() => void addHeir()}><Plus size={15} /> Lisa</button>
          </div>
        </article>

        <article className="inheritance-detail-panel inheritance-wide-panel">
          <div className="inheritance-panel-heading"><div><p className="eyebrow">SÜNDMUSED</p><h3><History size={18} /> Juhtumi ajalugu</h3></div><span>{inheritanceCase.events.length} sündmust</span></div>
          <div className="inheritance-event-list">
            {inheritanceCase.events.map((event) => <div className="inheritance-event" key={event.id}><div><strong>{statusLabel(event.type)}</strong><p>{event.description}</p></div><small>{timestampLabel(event.createdAt)}{event.createdBy?.name ? ` · ${event.createdBy.name}` : ""}</small></div>)}
            {!inheritanceCase.events.length && <div className="empty-state">Juhtumi sündmuseid ei ole veel talletatud.</div>}
          </div>
          <div className="inheritance-note-form">
            <label htmlFor="inheritance-note">Lisa sündmus või märkus</label>
            <textarea id="inheritance-note" value={note} disabled={saving} onChange={(event) => setNote(event.target.value)} placeholder="Kirjelda järgmist sammu või kokkulepet…" />
            <button className="secondary-action" disabled={saving || !note.trim()} onClick={() => void addNote()}><Plus size={15} /> Lisa sündmus</button>
          </div>
        </article>
      </section>
    </AppShell>
  );
}
