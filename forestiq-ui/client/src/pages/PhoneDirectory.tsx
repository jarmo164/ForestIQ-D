import { FormEvent, useCallback, useEffect, useState } from "react";
import { PhoneCall, Plus, Search, Trash2 } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type Contact = {
  id: number;
  source: string;
  name: string;
  phone: string;
  address: string;
  code: string;
};

const emptyContact = { source: "", name: "", phone: "", address: "", code: "" };

export default function PhoneDirectory() {
  const [query, setQuery] = useState("");
  const [records, setRecords] = useState<Contact[]>([]);
  const [draft, setDraft] = useState(emptyContact);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (search = query) => {
    setError("");
    try {
      const suffix = search.trim() ? `?query=${encodeURIComponent(search.trim())}` : "";
      setRecords(await api.get<Contact[]>(`/services/persons-dump${suffix}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kontaktide laadimine ebaõnnestus.");
    }
  }, [query]);

  useEffect(() => {
    void load("");
  }, [load]);

  async function addContact(event: FormEvent) {
    event.preventDefault();
    if (!draft.name.trim() && !draft.phone.trim()) {
      setError("Sisesta vähemalt nimi või telefoninumber.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.post<{ id: number }>("/services/persons-dump", draft);
      setDraft(emptyContact);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kontakti lisamine ebaõnnestus.");
    } finally {
      setBusy(false);
    }
  }

  async function removeContact(contact: Contact) {
    if (!window.confirm(`Kustutada kontakt ${contact.name || contact.phone}?`)) return;
    setBusy(true);
    setError("");
    try {
      await api.delete<void>(`/services/persons-dump/${contact.id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kontakti kustutamine ebaõnnestus.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Kontaktide register" eyebrow="FORESTIQ / KONTAKTID">
      <section className="workspace-intro">
        <PhoneCall size={24} />
        <div>
          <h2>Otsi, lisa ja eemalda metsandusega seotud kontakte.</h2>
          <p>Vaade kasutab organisatsioonipõhist kontaktiregistrit ega kuva enam toorest JSON-i.</p>
        </div>
      </section>

      {error && <div className="connection-warning">{error}</div>}

      <section className="table-panel">
        <form className="table-toolbar" onSubmit={(event) => { event.preventDefault(); void load(); }}>
          <span><Search size={16} /></span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nimi, telefon või isiku-/registrikood" />
          <button type="submit" disabled={busy}>Otsi</button>
          <button type="button" onClick={() => { setQuery(""); void load(""); }} disabled={busy}>Tühjenda</button>
        </form>

        <div className="work-card-grid">
          {records.map((contact) => (
            <article className="work-card" key={contact.id}>
              <div>
                <h3>{contact.name || "Nimetu kontakt"}</h3>
                <p>{contact.phone || "Telefon puudub"}</p>
                {contact.code && <p>Kood: {contact.code}</p>}
                {contact.address && <p>{contact.address}</p>}
                {contact.source && <small>Allikas: {contact.source}</small>}
              </div>
              <button type="button" onClick={() => void removeContact(contact)} disabled={busy} aria-label={`Kustuta ${contact.name}`}>
                <Trash2 size={16} /> Kustuta
              </button>
            </article>
          ))}
          {!records.length && <div className="empty-state">Sobivaid kontakte ei leitud.</div>}
        </div>
      </section>

      <section className="table-panel">
        <div className="table-toolbar"><Plus size={16} /> Lisa kontakt</div>
        <form onSubmit={addContact} className="generic-records">
          <label>Nimi<input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} /></label>
          <label>Telefon<input value={draft.phone} onChange={(event) => setDraft({ ...draft, phone: event.target.value })} /></label>
          <label>Aadress<input value={draft.address} onChange={(event) => setDraft({ ...draft, address: event.target.value })} /></label>
          <label>Isiku-/registrikood<input value={draft.code} onChange={(event) => setDraft({ ...draft, code: event.target.value })} /></label>
          <label>Allikas<input value={draft.source} onChange={(event) => setDraft({ ...draft, source: event.target.value })} /></label>
          <button type="submit" disabled={busy}>{busy ? "Salvestan…" : "Salvesta kontakt"}</button>
        </form>
      </section>
    </AppShell>
  );
}
