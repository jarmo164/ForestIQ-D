/** ForestIQ Landscape Desk design: reusable workbenches for operational workflows. */
import { type FormEvent, useEffect, useState } from "react";
import { BarChart3, ClipboardCheck, LogOut, PhoneCall, Search, ShieldCheck, Trash2, UserRoundPlus } from "lucide-react";
import { Link } from "wouter";

import { AppShell } from "@/components/AppShell";
import { StatusPill } from "@/components/StatusPill";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";
import type { Owner } from "@/lib/types";

const config = {
  caller: { title: "Minu tööjärjekord", eyebrow: "TÖÖLAUD / HELISTAJA", endpoint: "/services/my-work", icon: ClipboardCheck, lead: "Täienda omanike töölogi ning vii iga kontakt järgmise otsuseni." },
  evaluator: { title: "Hindamise töölaud", eyebrow: "TÖÖLAUD / HINDAJA", endpoint: "/services/owners-in-need-of-evaluation", icon: BarChart3, lead: "Need omanikud ootavad kinnistu ja pakkumise hindamist." },
  admin: { title: "Tööde jaotamine", eyebrow: "TÖÖLAUD / HALDUS", endpoint: "/services/admin-workdesk/owners-search", icon: ShieldCheck, lead: "Otsi, filtreeri ja suuna omanike töö järgmisele vastutajale." },
} as const;

export function OwnerWorkspace({ kind }: { kind: keyof typeof config }) {
  const current = config[kind]; const Icon = current.icon;
  const [owners, setOwners] = useState<Owner[]>([]); const [error, setError] = useState("");
  useEffect(() => { api.get<Owner[]>(current.endpoint).then(setOwners).catch((err: Error) => setError(err.message)); }, [current.endpoint]);
  return <AppShell title={current.title} eyebrow={current.eyebrow}>
    <section className="workspace-intro"><Icon size={24} /><div><h2>{current.lead}</h2><p>Vali kirje, et avada detailne töökaart ja teha järgmine toiming.</p></div><div className="workspace-count">{owners.length}<small>tulemust</small></div></section>
    {error && <div className="connection-warning">{error}</div>}
    <section className="work-card-grid">{owners.map((owner) => <Link href={`/owners/${owner.id}`} key={owner.id} className="work-card"><div><StatusPill value={owner.status} /><h3>{owner.name}</h3><p>{owner.id}</p></div><span>AVA TÖÖKAART →</span></Link>)}{!owners.length && <div className="empty-state">Töölaud on tühi või õigused ei võimalda neid andmeid lugeda.</div>}</section>
  </AppShell>;
}

type PhonebookRecord = { id: number; source?: string; name: string; phone?: string; address?: string; code?: string };
const emptyContact = { name: "", phone: "", code: "", address: "", source: "MANUAL" };

export function PhonebookWorkspace() {
  const [records, setRecords] = useState<PhonebookRecord[]>([]); const [query, setQuery] = useState("");
  const [draft, setDraft] = useState(emptyContact); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const load = async (search = query) => { setError(""); const suffix = search.trim() ? `?query=${encodeURIComponent(search.trim())}` : ""; try { setRecords(await api.get<PhonebookRecord[]>(`/services/persons-dump${suffix}`)); } catch (requestError) { setError((requestError as Error).message); } };
  useEffect(() => { void load(""); }, []);
  const addContact = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(""); try { await api.post<PhonebookRecord>("/services/persons-dump", draft); setDraft(emptyContact); await load(); } catch (requestError) { setError((requestError as Error).message); } finally { setBusy(false); } };
  const removeContact = async (id: number) => { setBusy(true); setError(""); try { await api.delete<void>(`/services/persons-dump/${id}`); await load(); } catch (requestError) { setError((requestError as Error).message); } finally { setBusy(false); } };
  return <AppShell title="Kontaktide register" eyebrow="FORESTIQ / KONTAKTID">
    <section className="workspace-intro"><PhoneCall size={24} /><div><h2>Otsi, lisa ja eemalda telefoniraamatu kontakte.</h2><p>Kontaktid on organisatsiooni põhised ning muudatused lähevad otse Django API-sse.</p></div></section>
    {error && <div className="connection-warning">{error}</div>}
    <section className="table-panel generic-records">
      <form className="table-toolbar" onSubmit={(event) => { event.preventDefault(); void load(); }}><label><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nimi, telefon või kood" /></label><button type="submit">Otsi</button></form>
      {records.map((record) => <article className="work-card" key={record.id}><div><h3>{record.name || "Nimetu kontakt"}</h3><p>{record.phone || "Telefon puudub"}</p><p>{record.code || record.address || record.source || ""}</p></div><button type="button" disabled={busy} onClick={() => void removeContact(record.id)} aria-label={`Kustuta ${record.name}`}><Trash2 size={16} /> Kustuta</button></article>)}
      {!records.length && <div className="empty-state">Otsingule vastavaid kontakte ei leitud.</div>}
    </section>
    <section className="table-panel generic-records"><div className="table-toolbar"><span><UserRoundPlus size={16} /> Lisa kontakt</span></div><form onSubmit={addContact} className="workspace-form"><input required value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} placeholder="Nimi" /><input value={draft.phone} onChange={(event) => setDraft({ ...draft, phone: event.target.value })} placeholder="Telefon" /><input value={draft.code} onChange={(event) => setDraft({ ...draft, code: event.target.value })} placeholder="Isiku- või registrikood" /><input value={draft.address} onChange={(event) => setDraft({ ...draft, address: event.target.value })} placeholder="Aadress" /><button type="submit" disabled={busy || !draft.name.trim()}>Salvesta kontakt</button></form></section>
  </AppShell>;
}

type AccountProfile = { user: { id: string; name: string }; organization: { id: string; slug: string; name: string }; roles: string[]; privileges: string[]; security: { sessionType: string; passwordChangeAvailable: boolean } };

export function AccountWorkspace() {
  const { logout } = useAuth(); const [profile, setProfile] = useState<AccountProfile | null>(null); const [error, setError] = useState("");
  const [oldPassword, setOldPassword] = useState(""); const [newPassword, setNewPassword] = useState(""); const [newPasswordAgain, setNewPasswordAgain] = useState(""); const [message, setMessage] = useState("");
  useEffect(() => { api.get<AccountProfile>("/services/account").then(setProfile).catch((err: Error) => setError(err.message)); }, []);
  const changePassword = async (event: FormEvent) => { event.preventDefault(); setError(""); setMessage(""); try { await api.post("/services/change-my-password", { oldPassword, newPassword, newPasswordAgain }); setOldPassword(""); setNewPassword(""); setNewPasswordAgain(""); setMessage("Parool on muudetud."); } catch (requestError) { setError((requestError as Error).message); } };
  return <AppShell title="Minu konto" eyebrow="FORESTIQ / KASUTAJA">
    <section className="workspace-intro"><ShieldCheck size={24} /><div><h2>Konto, organisatsioon, rollid ja sessiooni turvatoimingud.</h2><p>Siin kuvatakse kasutajale arusaadav konto info, mitte API toor-JSON.</p></div></section>
    {error && <div className="connection-warning">{error}</div>}{message && <div className="success-message">{message}</div>}
    {profile && <section className="work-card-grid"><article className="work-card"><div><p className="eyebrow">KASUTAJA</p><h3>{profile.user.name}</h3><p>{profile.user.id}</p></div></article><article className="work-card"><div><p className="eyebrow">ORGANISATSIOON</p><h3>{profile.organization.name}</h3><p>{profile.organization.slug}</p></div></article><article className="work-card"><div><p className="eyebrow">ROLLID</p><h3>{profile.roles.length ? profile.roles.join(", ") : "Rollid puuduvad"}</h3><p>{profile.privileges.length ? `Õigused: ${profile.privileges.join(", ")}` : "Täiendavaid õigusi pole"}</p></div></article></section>}
    <section className="table-panel generic-records"><div className="table-toolbar"><span><ShieldCheck size={16} /> Sessiooni turvalisus</span></div><button type="button" onClick={() => { logout(); window.location.assign("/"); }}><LogOut size={16} /> Logi välja</button>{profile?.security.passwordChangeAvailable && <form className="workspace-form" onSubmit={changePassword}><input type="password" required value={oldPassword} onChange={(event) => setOldPassword(event.target.value)} placeholder="Praegune parool" /><input type="password" required minLength={12} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} placeholder="Uus parool" /><input type="password" required minLength={12} value={newPasswordAgain} onChange={(event) => setNewPasswordAgain(event.target.value)} placeholder="Uus parool uuesti" /><button type="submit" disabled={newPassword.length < 12 || newPassword !== newPasswordAgain}>Muuda parooli</button></form>}</section>
  </AppShell>;
}
