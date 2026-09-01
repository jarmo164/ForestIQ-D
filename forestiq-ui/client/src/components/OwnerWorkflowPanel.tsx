import { useEffect, useState } from "react";
import { BadgeEuro, FileText, Gavel, Plus, RefreshCw, ShieldCheck } from "lucide-react";
import { Link } from "wouter";

import { api } from "@/lib/api";
import type { Deal, InheritanceCase, Owner } from "@/lib/types";

type OwnershipEvent = { id: string; cadastreId?: string | null; type: string; occurredAt?: number | null; sourceReference?: string | null };

export function OwnerWorkflowPanel({ owner }: { owner: Owner }) {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [cases, setCases] = useState<InheritanceCase[]>([]);
  const [transitions, setTransitions] = useState<OwnershipEvent[]>([]);
  const [error, setError] = useState("");
  const [evaluationAmount, setEvaluationAmount] = useState("");
  const [offerAmount, setOfferAmount] = useState("");

  const refresh = () => Promise.all([
    api.get<Deal[]>(`/services/deals/owners/${owner.id}`),
    api.get<InheritanceCase[]>(`/services/inheritance/owners/${owner.id}`),
    api.get<OwnershipEvent[]>(`/services/ownership-transitions/owners/${owner.id}`),
  ]).then(([dealData, caseData, transitionData]) => {
    setDeals(dealData);
    setCases(caseData);
    setTransitions(transitionData);
  }).catch((err) => setError(err.message));

  useEffect(() => { void refresh(); }, [owner.id]);

  const createDeal = async () => {
    try {
      await api.post(`/services/deals/owners/${owner.id}`, {
        saleSubject: "FOREST", parcelIds: owner.cadastres?.map((item) => item.id) || [], requestEvaluation: true,
        qualificationNotes: "Created from owner workspace.",
      });
      void refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Tehingu loomine ebaõnnestus."); }
  };

  const approveEvaluation = async (deal: Deal) => {
    try {
      const amount = Number(evaluationAmount);
      if (!Number.isFinite(amount) || amount <= 0) { setError("Sisesta hindamise positiivne pakkumishind."); return; }
      await api.post(`/services/deals/${deal.id}/evaluations`, { status: "APPROVED", proposedOfferPrice: amount, recommendedPurchasePrice: amount, version: deal.version });
      setEvaluationAmount("");
      void refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Hindamise kinnitamine ebaõnnestus."); }
  };

  const sendOffer = async (deal: Deal) => {
    try {
      const amount = Number(offerAmount);
      if (!Number.isFinite(amount) || amount <= 0) { setError("Sisesta pakkumise positiivne summa."); return; }
      const created = await api.post<{ offer: { id: string }; state: { version: number } }>(`/services/deals/${deal.id}/commercial/offers`, { amount, terms: "ForestIQ tööruumist saadetud pakkumine.", version: deal.version });
      await api.post(`/services/deals/${deal.id}/commercial/offers/send`, { offerId: created.offer.id, version: created.state.version });
      setOfferAmount("");
      void refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Pakkumise saatmine ebaõnnestus."); }
  };

  const checkNotice = async () => {
    try { await api.post(`/services/inheritance/owners/${owner.id}/official-notices/check`, {}); void refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "Pärimisteadet ei saanud kontrollida."); }
  };
  const createCase = async () => {
    try { await api.post(`/services/inheritance/owners/${owner.id}`, { sourceNoticeNumber: "", notaryName: "" }); void refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "Pärimisjuhtumi loomine ebaõnnestus."); }
  };
  const startCase = async (inheritanceCase: InheritanceCase) => {
    try { await api.patch(`/services/inheritance/cases/${inheritanceCase.id}/status`, { status: "IN_PROGRESS", comment: "Juhtum võeti omanikuvaates töösse.", version: inheritanceCase.version }); void refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "Juhtumi uuendamine ebaõnnestus."); }
  };

  return <section className="mt-6 grid gap-6 xl:grid-cols-3">
    {error && <div className="connection-warning xl:col-span-3">{error}</div>}
    <article className="panel p-5">
      <div className="panel-heading"><div><p className="eyebrow">KOMMERTS</p><h3>Tehingud</h3></div><BadgeEuro size={19} /></div>
      <p className="mb-4 text-sm text-muted-foreground">Loo valitud omaniku kinnistutele hinnatav tehing ning vii pakkumine läbi hindamise järgmisse etappi.</p>
      <button className="secondary-action" disabled={!owner.cadastres?.length} onClick={() => void createDeal()}><Plus size={16} /> Loo hindamise tehing</button>
      <div className="mt-4 space-y-2">
        {deals.map((deal) => <div className="rounded-xl bg-muted p-3 text-sm" key={deal.id}>
          <strong>{deal.stage.replaceAll("_", " ")}</strong><p>{deal.saleSubject} · {deal.parcels.length} kinnistut · {deal.offers.length} pakkumist</p>
          {deal.stage === "EVALUATION" && <div className="mt-3 flex gap-2"><input aria-label="Hindamise pakkumishind" className="min-w-0 rounded-md border bg-background px-2 py-1" inputMode="decimal" value={evaluationAmount} onChange={(event) => setEvaluationAmount(event.target.value)} placeholder="Hind EUR" /><button className="secondary-action" onClick={() => void approveEvaluation(deal)}>Kinnita hindamine</button></div>}
          {deal.stage === "NEGOTIATION" && <div className="mt-3 flex gap-2"><input aria-label="Pakkumise summa" className="min-w-0 rounded-md border bg-background px-2 py-1" inputMode="decimal" value={offerAmount} onChange={(event) => setOfferAmount(event.target.value)} placeholder="EUR" /><button className="secondary-action" onClick={() => void sendOffer(deal)}>Saada pakkumine</button></div>}
          {deal.stage === "WON" && <Link className="secondary-action mt-3" href={`/contracts?dealId=${encodeURIComponent(deal.id)}`}><FileText size={16} /> Koosta leping</Link>}
        </div>)}
        {!deals.length && <p className="text-sm text-muted-foreground">Aktiivseid tehinguid ei ole.</p>}
      </div>
    </article>
    <article className="panel p-5">
      <div className="panel-heading"><div><p className="eyebrow">PÄRIMINE</p><h3>Pärimisjuhtumid</h3></div><Gavel size={19} /></div>
      <p className="mb-4 text-sm text-muted-foreground">Kontrolli lubatud ametlikku teadet või ava käsitsi hallatav pärimisjuhtum.</p>
      <div className="flex flex-wrap gap-2"><button className="secondary-action" onClick={() => void checkNotice()}><RefreshCw size={16} /> Kontrolli teadet</button><button className="secondary-action" onClick={() => void createCase()}><Plus size={16} /> Loo juhtum</button></div>
      <div className="mt-4 space-y-2">{cases.map((item) => <div className="rounded-xl bg-muted p-3 text-sm" key={item.id}><strong>{item.status.replaceAll("_", " ")}</strong><p>{item.sourceNoticeNumber || "Käsitsi avatud"} · {item.heirs.length} pärijat</p>{item.status === "NEW" && <button className="secondary-action mt-2" onClick={() => void startCase(item)}>Võta töösse</button>}</div>)}{!cases.length && <p className="text-sm text-muted-foreground">Pärimisjuhtumeid ei ole.</p>}</div>
    </article>
    <article className="panel p-5">
      <div className="panel-heading"><div><p className="eyebrow">OMANDIMUUTUS</p><h3>Auditeeritud sündmused</h3></div><ShieldCheck size={19} /></div>
      <p className="mb-4 text-sm text-muted-foreground">Omanikuga seotud välise omandimuutuse sündmused ilmuvad pärast volitatud sünkroniseerimist.</p>
      <div className="space-y-2">{transitions.map((item) => <div className="rounded-xl bg-muted p-3 text-sm" key={item.id}><strong>{item.type}</strong><p>{item.cadastreId || "kinnistu määramata"} · {item.sourceReference || "allikaviide puudub"}</p></div>)}{!transitions.length && <p className="text-sm text-muted-foreground">Sündmuseid pole veel imporditud.</p>}</div>
    </article>
  </section>;
}
