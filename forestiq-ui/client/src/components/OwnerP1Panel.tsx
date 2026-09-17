import { useCallback, useEffect, useState } from "react";
import { CalendarClock, CheckCircle2, GitBranch, History, Link2, PhoneCall, Plus, ShieldCheck } from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";


type NextAction = {
  id: string;
  text: string;
  dueAt: number;
  status: string;
  assignee: { id: string; name: string } | null;
};

type Activity = {
  id: string;
  channel: string;
  outcomeCode: string;
  outcomeReason: string | null;
  note: string | null;
  createdAt: number;
  createdBy: { id: string; name: string } | null;
  nextActions: NextAction[];
};

type Relation = {
  id: string;
  cadastre: { id: string; name: string | null; area: number | null };
  source: string;
  validFrom: number;
  validTo: number | null;
  endedReason: string | null;
  protected: boolean;
  active: boolean;
  events: { type: string; reason: string | null; createdAt: number }[];
};

type RelationPage = { items: Relation[]; nextCursor: string | null; pageSize: number };
type TimelineEvent = { id: string; type: string; payload: Record<string, unknown>; createdAt: number; actor: { id: string; name: string } | null };

const formatDateTime = (value?: number | null) => value ? new Intl.DateTimeFormat("et-EE", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";

export function OwnerP1Panel({ ownerId }: { ownerId: string }) {
  const { user } = useAuth();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [relations, setRelations] = useState<Relation[]>([]);
  const [relationCursor, setRelationCursor] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [channel, setChannel] = useState("PHONE");
  const [outcome, setOutcome] = useState("CALLBACK");
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [nextText, setNextText] = useState("");
  const [nextDue, setNextDue] = useState("");
  const [cadastreId, setCadastreId] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      setError("");
      const [activityData, relationData, timelineData] = await Promise.all([
        api.get<Activity[]>(`/services/owners/${ownerId}/activities`),
        api.get<RelationPage>(`/services/owners/${ownerId}/ownership-relations?limit=20`),
        api.get<TimelineEvent[]>(`/services/owners/${ownerId}/timeline`),
      ]);
      setActivities(activityData);
      setRelations(relationData.items);
      setRelationCursor(relationData.nextCursor);
      setTimeline(timelineData);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "P1 töövoo andmeid ei saanud laadida.");
    }
  }, [ownerId]);

  useEffect(() => { void refresh(); }, [refresh]);

  const addActivity = async () => {
    if (!outcome.trim()) return;
    try {
      setError("");
      const nextAction = nextText.trim() && nextDue ? {
        text: nextText.trim(),
        dueAt: new Date(nextDue).toISOString(),
        assigneeId: user?.id,
      } : undefined;
      await api.post(`/services/owners/${ownerId}/activities`, {
        channel,
        outcomeCode: outcome.trim().toUpperCase(),
        outcomeReason: reason.trim(),
        note: note.trim(),
        ...(nextAction ? { nextAction } : {}),
      });
      setReason(""); setNote(""); setNextText(""); setNextDue("");
      setNotice("Kontakt ja järgmine tegevus salvestati auditeeritavalt.");
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Kontakti ei saanud salvestada.");
    }
  };

  const completeAction = async (actionId: string) => {
    try {
      await api.patch(`/services/next-actions/${actionId}`, { operation: "COMPLETE" });
      setNotice("Järgmine tegevus märgiti tehtuks.");
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Tegevust ei saanud lõpetada."); }
  };

  const postponeAction = async (actionId: string) => {
    const value = window.prompt("Uus tähtaeg (YYYY-MM-DD HH:MM)");
    if (!value) return;
    const parsed = new Date(value.replace(" ", "T"));
    if (Number.isNaN(parsed.valueOf())) { setError("Tähtaeg ei ole korrektne."); return; }
    try {
      await api.patch(`/services/next-actions/${actionId}`, { operation: "POSTPONE", dueAt: parsed.toISOString() });
      setNotice("Tegevuse tähtaeg lükati edasi.");
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Tähtaega ei saanud muuta."); }
  };

  const addRelation = async () => {
    if (!cadastreId.trim()) return;
    try {
      await api.post(`/services/owners/${ownerId}/ownership-relations`, {
        cadastreId: cadastreId.trim(),
        protected: true,
        reason: "Käsitsi kinnitatud seos",
      });
      setCadastreId("");
      setNotice("Kaitstud omaniku–katastri seos salvestati.");
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Seost ei saanud salvestada."); }
  };

  const endRelation = async (relation: Relation) => {
    const endingReason = window.prompt("Sisesta seose lõpetamise põhjus");
    if (!endingReason?.trim()) return;
    try {
      await api.patch(`/services/ownership-relations/${relation.id}`, { operation: "END", reason: endingReason.trim(), protected: true });
      setNotice("Seos lõpetati ajalugu kustutamata ja kaitsti välissünkroniseerimise eest.");
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Seost ei saanud lõpetada."); }
  };

  const reactivateRelation = async (relation: Relation) => {
    try {
      await api.patch(`/services/ownership-relations/${relation.id}`, { operation: "REACTIVATE", reason: "Käsitsi taasaktiveeritud" });
      setNotice("Seos taasaktiveeriti.");
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Seost ei saanud taasaktiveerida."); }
  };

  const loadMoreRelations = async () => {
    if (!relationCursor) return;
    try {
      const page = await api.get<RelationPage>(`/services/owners/${ownerId}/ownership-relations?limit=20&cursor=${encodeURIComponent(relationCursor)}`);
      setRelations((current) => [...current, ...page.items]);
      setRelationCursor(page.nextCursor);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Järgmist seoste lehte ei saanud laadida."); }
  };

  return <section className="space-y-5">
    {notice && <div className="success-notice">{notice}</div>}
    {error && <div className="connection-warning">{error}</div>}

    <section className="panel p-5">
      <div className="panel-heading"><div><p className="eyebrow">STRUKTUREERITUD KONTAKT</p><h3>Kontakt ja järgmine tegevus</h3></div><PhoneCall size={19} /></div>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="text-sm">Kanal<select className="mt-1 w-full" value={channel} onChange={(event) => setChannel(event.target.value)}><option value="PHONE">Telefon</option><option value="EMAIL">E-post</option><option value="MEETING">Kohtumine</option></select></label>
        <label className="text-sm">Tulemus<input className="mt-1 w-full" value={outcome} onChange={(event) => setOutcome(event.target.value)} placeholder="CALLBACK / INTERESTED" /></label>
        <label className="text-sm">Põhjendus<input className="mt-1 w-full" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Lühike põhjendus" /></label>
      </div>
      <textarea className="mt-3 w-full" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Kontakti märkus" />
      <div className="mt-3 grid gap-3 md:grid-cols-[1fr_240px_auto]">
        <input value={nextText} onChange={(event) => setNextText(event.target.value)} placeholder="Järgmine tegevus (valikuline)" />
        <input type="datetime-local" value={nextDue} onChange={(event) => setNextDue(event.target.value)} />
        <button className="secondary-action" onClick={() => void addActivity()}><Plus size={16} /> Salvesta</button>
      </div>
      <div className="mt-5 space-y-3">{activities.slice(0, 12).map((activity) => <article key={activity.id} className="rounded-xl border border-border p-3"><div className="flex flex-wrap items-center justify-between gap-2"><div><strong>{activity.channel} · {activity.outcomeCode}</strong><small className="ml-2 text-muted-foreground">{formatDateTime(activity.createdAt)}</small></div><span className="status-pill">{activity.createdBy?.name || "kasutaja"}</span></div>{activity.outcomeReason && <p className="mt-2 text-sm">{activity.outcomeReason}</p>}{activity.note && <p className="mt-1 text-sm text-muted-foreground">{activity.note}</p>}{activity.nextActions.map((action) => <div key={action.id} className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg bg-muted p-2 text-sm"><span><CalendarClock size={15} className="mr-1 inline" />{action.text} · {formatDateTime(action.dueAt)} · {action.assignee?.name}</span><span className="flex gap-2"><span className="status-pill">{action.status}</span>{action.status !== "DONE" && <><button className="secondary-action" onClick={() => void postponeAction(action.id)}>Lükka edasi</button><button className="secondary-action" onClick={() => void completeAction(action.id)}><CheckCircle2 size={14} /> Tehtud</button></>}</span></div>)}</article>)}{!activities.length && <div className="empty-state">Struktureeritud kontakte ei ole veel salvestatud.</div>}</div>
    </section>

    <section className="panel p-5">
      <div className="panel-heading"><div><p className="eyebrow">OMANDISUHTE ELUTSÜKKEL</p><h3>Aktiivsed ja ajaloolised seosed</h3></div><GitBranch size={19} /></div>
      <div className="mb-4 flex gap-2"><input className="flex-1" value={cadastreId} onChange={(event) => setCadastreId(event.target.value)} placeholder="Katastritunnus uue käsitsi kinnitatud seose jaoks" /><button className="secondary-action" onClick={() => void addRelation()}><Link2 size={15} /> Lisa seos</button></div>
      <div className="space-y-2">{relations.map((relation) => <article className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border p-3" key={relation.id}><div><div className="flex items-center gap-2"><strong>{relation.cadastre.name || relation.cadastre.id}</strong><span className={`status-pill ${relation.active ? "" : "warning"}`}>{relation.active ? "AKTIIVNE" : "AJALOOLINE"}</span>{relation.protected && <span title="Käsitsi kaitstud"><ShieldCheck size={15} /></span>}</div><small>{relation.cadastre.id} · {relation.source} · alates {formatDateTime(relation.validFrom)}</small>{relation.endedReason && <p className="mt-1 text-sm text-muted-foreground">{relation.endedReason}</p>}</div>{relation.active ? <button className="secondary-action" onClick={() => void endRelation(relation)}>Lõpeta seos</button> : <button className="secondary-action" onClick={() => void reactivateRelation(relation)}>Taasaktiveeri</button>}</article>)}{!relations.length && <div className="empty-state">Omandisuhteid ei ole.</div>}</div>
      {relationCursor && <button className="secondary-action mt-3" onClick={() => void loadMoreRelations()}>Laadi järgmised seosed</button>}
    </section>

    <section className="panel p-5">
      <div className="panel-heading"><div><p className="eyebrow">AUDIT</p><h3>Struktureeritud töövoo ajajoon</h3></div><History size={19} /></div>
      <div className="space-y-2">{timeline.slice(0, 20).map((event) => <div className="flex items-center justify-between gap-3 border-b border-border py-2 text-sm" key={event.id}><span><strong>{event.type.replaceAll("_", " ")}</strong><small className="ml-2 text-muted-foreground">{event.actor?.name || "süsteem"}</small></span><span>{formatDateTime(event.createdAt)}</span></div>)}{!timeline.length && <div className="empty-state">Uue töövoo auditikirjeid ei ole.</div>}</div>
    </section>
  </section>;
}
