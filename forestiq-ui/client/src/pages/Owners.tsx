/** ForestIQ owner register with server-side cursor/keyset search. */
import { useEffect, useState } from "react";
import { Filter, Search, SlidersHorizontal, UsersRound } from "lucide-react";
import { Link } from "wouter";

import { AppShell } from "@/components/AppShell";
import { StatusPill } from "@/components/StatusPill";
import { api } from "@/lib/api";
import type { Owner } from "@/lib/types";

type OwnerPage = { items: Owner[]; nextCursor: string | null; pageSize: number };

export default function Owners() {
  const [owners, setOwners] = useState<Owner[]>([]);
  const [query, setQuery] = useState("");
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async (cursor?: string | null, append = false) => {
    try {
      setLoading(true); setError("");
      const params = new URLSearchParams({ limit: "50" });
      if (query.trim()) params.set("q", query.trim());
      if (cursor) params.set("cursor", cursor);
      const page = await api.get<OwnerPage>(`/services/owners?${params}`);
      setOwners((current) => append ? [...current, ...page.items] : page.items);
      setNextCursor(page.nextCursor);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Omanike registrit ei saanud laadida.");
    } finally { setLoading(false); }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(null, false); }, 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  return <AppShell title="Omanikud" eyebrow="FORESTIQ / OMANIKE REGISTER">
    <section className="section-lead"><div><p>Leia kontakt cursor-põhisest registrist, ava katastri seosed ning registreeri järgmine otsus.</p><strong><UsersRound size={17} /> {owners.length} laaditud kirjet</strong></div><div className="search-bar"><Search size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Otsi nime, isikukoodi, telefoni või e-posti järgi" /><button aria-label="Filtreeri"><SlidersHorizontal size={18} /></button></div></section>
    {error && <div className="connection-warning">{error}</div>}
    <section className="table-panel"><div className="table-toolbar"><span><Filter size={16} /> Stabiilne cursor-lehestus</span><small>Maksimaalselt 50 kirjet lehel</small></div><div className="data-table"><div className="table-head"><span>Omanik</span><span>Kontakt</span><span>Staatus</span><span>Määratud</span><span /></div>{owners.map((owner) => <Link key={owner.id} href={`/owners/${owner.id}`} className="table-row owner-register-row"><span className="owner-cell"><i /><b>{owner.name}</b><small>{owner.id}</small><small className="owner-mobile-meta">{owner.phone || "telefon puudub"} · {owner.email || "e-post puudub"} · vastutaja {owner.assignee?.name || "määramata"}</small></span><span><b>{owner.phone || "—"}</b><small>{owner.email || "e-post puudub"}</small></span><span><StatusPill value={owner.status} /></span><span>{owner.assignee?.name || "Määramata"}</span><span>→</span></Link>)}{loading && <div className="empty-state">Laadin omanike registrit…</div>}{!loading && !owners.length && <div className="empty-state">Selle otsinguga omanikke ei leitud.</div>}</div>{nextCursor && <div className="p-4 text-center"><button className="secondary-action" disabled={loading} onClick={() => void load(nextCursor, true)}>Laadi järgmised 50</button></div>}</section>
  </AppShell>;
}
