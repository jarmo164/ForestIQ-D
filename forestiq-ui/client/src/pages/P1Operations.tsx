import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, BadgeEuro, CheckCircle2, FileSignature, ListChecks, RefreshCw, Settings2 } from "lucide-react";
import { Link } from "wouter";

import { AppShell } from "@/components/AppShell";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { useAuth } from "@/contexts/AuthContext";
import { api, apiErrorMessage } from "@/lib/api";
import { lossAnalysisCsv, lossAnalysisQuery, type LossAnalysisRow } from "@/lib/p1Operations";


type DealHealthReason = { code: string; severity: string; message: string };
type DealWorkItem = {
  id: string;
  version: number;
  owner: { id: string; name: string };
  stage: string;
  value: number | null;
  responsible: { id: string; name: string } | null;
  nextAction: { id: string; text: string; dueAt: number; status: string; assignee: { id: string; name: string } | null } | null;
  evaluationDueAt: number | null;
  offerValidUntil: string | null;
  updatedAt: number;
  health: DealHealthReason[];
  healthy: boolean;
};

type LossReason = { id: string; code: string; label: string; description: string | null; active: boolean; sortOrder: number };
type QualityScanRun = { id: string; status: string; trigger: string; detected: number; created: number; autoResolved: number; processedOwners: number; processedDeals: number; error: string | null; startedAt: number; finishedAt: number | null };
type QualityScanStatus = { lastRun: QualityScanRun | null; queueSize: number };
type QualityIssue = {
  id: string;
  type: string;
  severity: string;
  status: string;
  owner: { id: string; name: string } | null;
  dealId: string | null;
  description: string;
  evidence: Record<string, unknown>;
  suggestedAssignee: { id: string; name: string } | null;
  assignee: { id: string; name: string } | null;
  resolutionNote: string | null;
  updatedAt: number;
};

type ContractRecord = { id: string; contractNo?: string; status: string; version?: number; sellers?: string; buyer?: string };
type Signing = {
  contractId: string;
  state: string;
  responsible: { id: string; name: string } | null;
  dueAt: number | null;
  delayReason: string | null;
  finalDocument: string | null;
  finalUrl: string | null;
  finalContentType: string | null;
  verification: {
    status: "NOT_SUBMITTED" | "PENDING" | "VERIFIED" | "FAILED";
    documentSha256: string | null;
    verifiedAt: number | null;
    reference: string | null;
    signer: { identifier?: string; name?: string } | null;
    certificate: { serialNumber?: string } | null;
    failureReason: string | null;
    integrityValid: boolean | null;
  };
  version: number;
  updatedAt: number;
  events: { fromState: string | null; toState: string; reason: string | null; createdAt: number }[];
};
type ContractVersion = { id: string; version: number; pdfSha256: string; replacement: boolean; changeReason: string | null; createdAt: number };
type Tab = "deals" | "quality" | "losses" | "contracts";

type DealDraft = { text: string; dueAt: string; evaluationDueAt: string; lossReason: string; lossNote: string; followUpAt: string };

const emptyDraft = (): DealDraft => ({ text: "", dueAt: "", evaluationDueAt: "", lossReason: "", lossNote: "", followUpAt: "" });
const dateTime = (value?: number | null) => value ? new Intl.DateTimeFormat("et-EE", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";
const money = (value?: number | null) => value == null ? "—" : new Intl.NumberFormat("et-EE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
const tabs: { id: Tab; label: string }[] = [
  { id: "deals", label: "Tehingu tervis" },
  { id: "quality", label: "Andmekvaliteet" },
  { id: "losses", label: "Kaotuse põhjused" },
  { id: "contracts", label: "Lepingukontroll" },
];

export default function P1Operations() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("deals");
  const [deals, setDeals] = useState<DealWorkItem[]>([]);
  const [lossReasons, setLossReasons] = useState<LossReason[]>([]);
  const [lossAnalysis, setLossAnalysis] = useState<LossAnalysisRow[]>([]);
  const [quality, setQuality] = useState<QualityIssue[]>([]);
  const [qualityScan, setQualityScan] = useState<QualityScanStatus | null>(null);
  const [contracts, setContracts] = useState<ContractRecord[]>([]);
  const [selectedContract, setSelectedContract] = useState<ContractRecord | null>(null);
  const [signing, setSigning] = useState<Signing | null>(null);
  const [versions, setVersions] = useState<ContractVersion[]>([]);
  const [drafts, setDrafts] = useState<Record<string, DealDraft>>({});
  const [stageFilter, setStageFilter] = useState("");
  const [healthFilter, setHealthFilter] = useState("");
  const [responsibleFilter, setResponsibleFilter] = useState("");
  const [minValue, setMinValue] = useState("");
  const [maxValue, setMaxValue] = useState("");
  const [deadlineBefore, setDeadlineBefore] = useState("");
  const [qualityStatus, setQualityStatus] = useState("OPEN");
  const [lossFrom, setLossFrom] = useState("");
  const [lossTo, setLossTo] = useState("");
  const [lossSeller, setLossSeller] = useState("");
  const [lossStage, setLossStage] = useState("");
  const [newReasonCode, setNewReasonCode] = useState("");
  const [newReasonLabel, setNewReasonLabel] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [dealsLoading, setDealsLoading] = useState(true);
  const [qualityLoading, setQualityLoading] = useState(true);
  const [referenceLoading, setReferenceLoading] = useState(true);
  const [dealsError, setDealsError] = useState("");
  const [qualityError, setQualityError] = useState("");
  const [referenceError, setReferenceError] = useState("");
  const [pendingLostDeal, setPendingLostDeal] = useState<DealWorkItem | null>(null);
  const [lostBusy, setLostBusy] = useState(false);

  const draftFor = (dealId: string) => drafts[dealId] || emptyDraft();
  const patchDraft = (dealId: string, patch: Partial<DealDraft>) => setDrafts((current) => ({ ...current, [dealId]: { ...draftFor(dealId), ...patch } }));

  const refreshDeals = useCallback(async () => {
    setDealsLoading(true);
    setDealsError("");
    try {
      const params = new URLSearchParams();
      if (stageFilter) params.set("stage", stageFilter);
      if (healthFilter) params.set("health", healthFilter);
      if (responsibleFilter) params.set("responsibleId", responsibleFilter);
      if (minValue) params.set("minValue", minValue);
      if (maxValue) params.set("maxValue", maxValue);
      if (deadlineBefore) params.set("deadlineBefore", new Date(`${deadlineBefore}T23:59:59`).toISOString());
      const suffix = params.toString() ? `?${params}` : "";
      setDeals(await api.get<DealWorkItem[]>(`/services/deals/workbench${suffix}`));
    } catch (reason) {
      setDeals([]);
      setDealsError(apiErrorMessage(reason, "Tehingute tervist ei saanud laadida."));
    } finally { setDealsLoading(false); }
  }, [deadlineBefore, healthFilter, maxValue, minValue, responsibleFilter, stageFilter]);

  const refreshQuality = useCallback(async () => {
    setQualityLoading(true);
    setQualityError("");
    try {
      const suffix = qualityStatus ? `?status=${encodeURIComponent(qualityStatus)}` : "";
      const [issues, scan] = await Promise.all([
        api.get<QualityIssue[]>(`/services/admin/data-quality/issues${suffix}`),
        api.get<QualityScanStatus>("/services/admin/data-quality/scan"),
      ]);
      setQuality(issues);
      setQualityScan(scan);
    } catch (reason) {
      setQuality([]);
      setQualityError(apiErrorMessage(reason, "Andmekvaliteedi järjekorda ei saanud laadida."));
    } finally { setQualityLoading(false); }
  }, [qualityStatus]);

  const refreshLossAnalysis = useCallback(async () => {
    try {
      const query = lossAnalysisQuery({ from: lossFrom, to: lossTo, sellerId: lossSeller, previousStage: lossStage });
      const suffix = query ? `?${query}` : "";
      setLossAnalysis(await api.get<LossAnalysisRow[]>(`/services/admin/loss-analysis${suffix}`));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Kaotuste analüüsi ei saanud laadida."); }
  }, [lossFrom, lossSeller, lossStage, lossTo]);

  const refreshReferenceData = useCallback(async () => {
    setReferenceLoading(true);
    setReferenceError("");
    try {
      const [reasons, contractData] = await Promise.all([
        api.get<LossReason[]>("/services/admin/loss-reasons?active=false"),
        api.get<ContractRecord[]>("/services/contracts"),
      ]);
      setLossReasons(reasons);
      setContracts(contractData);
    } catch (reason) {
      setLossReasons([]);
      setContracts([]);
      setReferenceError(apiErrorMessage(reason, "P1 viiteandmeid ei saanud laadida."));
    } finally { setReferenceLoading(false); }
  }, []);

  useEffect(() => { void refreshDeals(); }, [refreshDeals]);
  useEffect(() => { void refreshQuality(); }, [refreshQuality]);
  useEffect(() => { void refreshLossAnalysis(); }, [refreshLossAnalysis]);
  useEffect(() => { void refreshReferenceData(); }, [refreshReferenceData]);

  const setNextAction = async (deal: DealWorkItem) => {
    const draft = draftFor(deal.id);
    if (!draft.text.trim() || !draft.dueAt) { setError("Järgmine tegevus ja tähtaeg on kohustuslikud."); return; }
    try {
      await api.post(`/services/deals/${deal.id}/next-action`, {
        text: draft.text.trim(),
        dueAt: new Date(draft.dueAt).toISOString(),
        assigneeId: user?.id,
        ...(draft.evaluationDueAt ? { evaluationDueAt: new Date(draft.evaluationDueAt).toISOString() } : {}),
      });
      patchDraft(deal.id, { text: "", dueAt: "", evaluationDueAt: "" });
      setNotice("Järgmine tegevus ja hindamise tähtaeg salvestati.");
      await refreshDeals();
    } catch (reason) { setError(apiErrorMessage(reason, "Järgmist tegevust ei saanud salvestada.")); }
  };

  const markLost = (deal: DealWorkItem) => {
    const draft = draftFor(deal.id);
    if (!draft.lossReason) { setError("Vali hallatav kaotuse põhjus."); return; }
    setPendingLostDeal(deal);
  };

  const confirmMarkLost = async () => {
    if (!pendingLostDeal || lostBusy) return;
    const deal = pendingLostDeal;
    const draft = draftFor(deal.id);
    setLostBusy(true);
    setError("");
    try {
      await api.post(`/services/deals/${deal.id}/commercial/lost`, {
        version: deal.version,
        reasonCode: draft.lossReason,
        note: draft.lossNote.trim(),
        ...(draft.followUpAt ? { followUpAt: new Date(draft.followUpAt).toISOString() } : {}),
      });
      setNotice("Tehing märgiti kaotatuks struktureeritud põhjusega.");
      setPendingLostDeal(null);
      await refreshDeals();
    } catch (reason) {
      setError(apiErrorMessage(reason, "Tehingut ei saanud sulgeda."));
    } finally { setLostBusy(false); }
  };

  const runQualityScan = async () => {
    try {
      const result = await api.post<QualityScanRun & { queueSize: number }>("/services/admin/data-quality/scan", {});
      setNotice(`Andmekvaliteedi kontroll: ${result.detected} probleemi, ${result.created} uut, ${result.autoResolved} automaatselt lahendatud.`);
      await refreshQuality();
    } catch (reason) { setError(apiErrorMessage(reason, "Andmekvaliteedi kontroll ebaõnnestus.")); }
  };

  const qualityAction = async (issue: QualityIssue, operation: "ASSIGN" | "RELEASE" | "RESOLVE") => {
    const reason = operation === "RESOLVE" ? window.prompt("Lahendamise põhjendus")?.trim() : "";
    if (operation === "RESOLVE" && !reason) return;
    try {
      await api.patch(`/services/admin/data-quality/issues/${issue.id}`, {
        operation,
        ...(operation === "ASSIGN" ? { assigneeId: user?.id } : {}),
        ...(reason ? { reason } : {}),
      });
      await refreshQuality();
    } catch (cause) { setError(apiErrorMessage(cause, "Andmekvaliteedi kirjet ei saanud uuendada.")); }
  };

  const addLossReason = async () => {
    if (!newReasonCode.trim() || !newReasonLabel.trim()) return;
    try {
      await api.post("/services/admin/loss-reasons", { code: newReasonCode.trim().toUpperCase(), label: newReasonLabel.trim() });
      setNewReasonCode(""); setNewReasonLabel("");
      setNotice("Kaotuse põhjus lisati.");
      await refreshReferenceData();
    } catch (reason) { setError(apiErrorMessage(reason, "Kaotuse põhjust ei saanud lisada.")); }
  };

  const toggleLossReason = async (reason: LossReason) => {
    try {
      await api.patch(`/services/admin/loss-reasons/${reason.id}`, { active: !reason.active });
      await refreshReferenceData();
    } catch (cause) { setError(apiErrorMessage(cause, "Kaotuse põhjust ei saanud muuta.")); }
  };

  const openContract = async (contract: ContractRecord) => {
    try {
      setSelectedContract(contract);
      const [signingData, versionData] = await Promise.all([
        api.get<Signing>(`/services/contracts/${encodeURIComponent(contract.id)}/signing`),
        api.get<ContractVersion[]>(`/services/contracts/${encodeURIComponent(contract.id)}/versions`),
      ]);
      setSigning(signingData); setVersions(versionData);
    } catch (reason) { setError(apiErrorMessage(reason, "Lepingu P1 olekut ei saanud laadida.")); }
  };

  const sendForSignature = async () => {
    if (!selectedContract || !signing) return;
    try {
      const due = new Date(Date.now() + 3 * 86400000).toISOString();
      const result = await api.patch<Signing>(`/services/contracts/${encodeURIComponent(selectedContract.id)}/signing`, { version: signing.version, state: "SENT_FOR_SIGNATURE", responsibleId: user?.id, dueAt: due });
      setSigning(result); setNotice("Leping saadeti allkirjastamise töövoogu.");
    } catch (reason) { setError(apiErrorMessage(reason, "Allkirjastamist ei saanud alustada.")); }
  };

  const uploadSignature = async (file: File) => {
    if (!selectedContract) return;
    const form = new FormData(); form.append("file", file);
    try {
      const result = await api.upload<Signing>(`/services/contracts/${encodeURIComponent(selectedContract.id)}/signing/document`, form);
      setSigning(result); setNotice("Lõppdokument salvestati ja ootab kontrollitud allkirjatõendit.");
    } catch (reason) { setError(apiErrorMessage(reason, "Allkirjastatud dokumenti ei saanud salvestada.")); }
  };

  const createReplacementVersion = async () => {
    if (!selectedContract) return;
    const reason = window.prompt("Asendusversiooni muudatuse põhjus")?.trim();
    if (!reason) return;
    try {
      const version = await api.post<ContractVersion>(`/services/contracts/${encodeURIComponent(selectedContract.id)}/versions`, {
        version: selectedContract.version,
        reason,
        checklist: { priceMatched: true, termsMatched: true, sellerMatched: true, parcelsMatched: true },
      });
      setVersions((current) => [...current, version]);
      setSelectedContract((current) => current ? { ...current, version: (current.version || 1) + 1 } : current);
      setNotice(`Lepingu kontrollitud versioon ${version.version} loodi.`);
    } catch (cause) { setError(apiErrorMessage(cause, "Asendusversiooni ei saanud luua.")); }
  };

  const healthCodes = useMemo(() => Array.from(new Set(deals.flatMap((deal) => deal.health.map((reason) => reason.code)))).sort(), [deals]);

  const exportLossAnalysis = () => {
    const url = URL.createObjectURL(new Blob([lossAnalysisCsv(lossAnalysis)], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "forestiq-loss-analysis.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  return <AppShell title="Operatsioonide kontroll" eyebrow="P1 / MÜÜK JA LEPINGUD">
    <section className="workspace-intro"><ListChecks size={24} /><div><h2>Järgmine tegevus, tervis, kvaliteet ja lepingukontroll</h2><p>P1 töölaud koondab igapäevase müügi- ja lepingutöö kontrollpunktid ühte auditeeritavasse vaatesse.</p></div></section>
    {notice && <div className="success-notice" role="status" aria-live="polite">{notice}</div>}{error && <div className="connection-warning" role="alert" aria-live="assertive">{error}</div>}
    <div className="contracts-tabs" role="tablist" aria-label="P1 operatsioonide vaated">
      {tabs.map((item) => <button key={item.id} id={`p1-tab-${item.id}`} role="tab" type="button" className={tab === item.id ? "active" : ""} aria-selected={tab === item.id} aria-controls={`p1-panel-${item.id}`} tabIndex={tab === item.id ? 0 : -1} onClick={() => setTab(item.id)}>{item.label}</button>)}
    </div>

    {tab === "deals" && <section id="p1-panel-deals" role="tabpanel" aria-labelledby="p1-tab-deals" className="space-y-4">
      <div className="panel p-4"><div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6"><select value={stageFilter} onChange={(event) => setStageFilter(event.target.value)}><option value="">Kõik etapid</option><option value="QUALIFICATION">Qualification</option><option value="EVALUATION">Evaluation</option><option value="NEGOTIATION">Negotiation</option></select><select value={healthFilter} onChange={(event) => setHealthFilter(event.target.value)}><option value="">Kõik tervised</option>{healthCodes.map((code) => <option value={code} key={code}>{code}</option>)}</select><input value={responsibleFilter} onChange={(event) => setResponsibleFilter(event.target.value)} placeholder="Vastutaja ID" /><input inputMode="decimal" value={minValue} onChange={(event) => setMinValue(event.target.value)} placeholder="Min väärtus" /><input inputMode="decimal" value={maxValue} onChange={(event) => setMaxValue(event.target.value)} placeholder="Max väärtus" /><input type="date" value={deadlineBefore} onChange={(event) => setDeadlineBefore(event.target.value)} /></div><button className="secondary-action mt-3" onClick={() => void refreshDeals()}><RefreshCw size={15} /> Rakenda filtrid</button></div>
      {dealsError ? <div className="connection-warning" role="alert"><p>{dealsError}</p><button className="secondary-action mt-2" onClick={() => void refreshDeals()}><RefreshCw size={14} /> Proovi uuesti</button></div> : dealsLoading ? <div className="empty-state" role="status">Laadin aktiivseid tehinguid…</div> : <div className="work-card-grid">{deals.map((deal) => { const draft = draftFor(deal.id); return <article className="work-card" key={deal.id}><div><div className="flex flex-wrap gap-2"><span className="status-pill">{deal.stage}</span>{deal.health.map((reason) => <span className="status-pill warning" key={reason.code} title={reason.message}>{reason.code}</span>)}</div><h3>{deal.owner.name}</h3><p>{money(deal.value)} · vastutaja {deal.responsible?.name || "määramata"}</p>{deal.nextAction && <p className="mt-2 text-sm"><strong>Järgmine:</strong> {deal.nextAction.text} · {dateTime(deal.nextAction.dueAt)}</p>}</div><div className="mt-3 grid gap-2"><input value={draft.text} onChange={(event) => patchDraft(deal.id, { text: event.target.value })} placeholder="Järgmine tegevus" /><input type="datetime-local" value={draft.dueAt} onChange={(event) => patchDraft(deal.id, { dueAt: event.target.value })} /><input type="datetime-local" value={draft.evaluationDueAt} onChange={(event) => patchDraft(deal.id, { evaluationDueAt: event.target.value })} placeholder="Hindamise tähtaeg" /><button className="secondary-action" onClick={() => void setNextAction(deal)}>Salvesta järgmine samm</button><div className="grid grid-cols-2 gap-2"><select value={draft.lossReason} onChange={(event) => patchDraft(deal.id, { lossReason: event.target.value })}><option value="">Kaotuse põhjus</option>{lossReasons.filter((reason) => reason.active).map((reason) => <option value={reason.code} key={reason.id}>{reason.label}</option>)}</select><input value={draft.lossNote} onChange={(event) => patchDraft(deal.id, { lossNote: event.target.value })} placeholder="Märkus" /></div><input type="datetime-local" value={draft.followUpAt} onChange={(event) => patchDraft(deal.id, { followUpAt: event.target.value })} /><div className="flex justify-between gap-2"><button className="secondary-action" onClick={() => void markLost(deal)}>Märgi kaotatuks</button><Link href={`/owners/${deal.owner.id}`}>AVA OMANIK →</Link></div></div></article>; })}{!deals.length && <div className="empty-state">Filtritele vastavaid aktiivseid tehinguid ei ole.</div>}</div>}
    </section>}

    {tab === "quality" && <section id="p1-panel-quality" role="tabpanel" aria-labelledby="p1-tab-quality" className="panel p-5"><div className="panel-heading"><div><p className="eyebrow">ANDMEKVALITEET</p><h3>Auditeeritud probleemijärjekord</h3></div><AlertTriangle size={19} /></div>{qualityScan?.lastRun && <div className="mb-4 grid gap-2 rounded-xl bg-muted p-3 text-sm md:grid-cols-4"><div><strong>{qualityScan.lastRun.status}</strong><small className="block">viimane skann · {dateTime(qualityScan.lastRun.finishedAt || qualityScan.lastRun.startedAt)}</small></div><div><strong>{qualityScan.lastRun.detected}</strong><small className="block">tuvastatud</small></div><div><strong>{qualityScan.lastRun.created} / {qualityScan.lastRun.autoResolved}</strong><small className="block">uut / automaatselt lahendatud</small></div><div><strong>{qualityScan.queueSize}</strong><small className="block">aktiivses järjekorras</small></div>{qualityScan.lastRun.error && <p className="text-destructive md:col-span-4">{qualityScan.lastRun.error}</p>}</div>}<div className="mb-4 flex flex-wrap gap-2"><select value={qualityStatus} onChange={(event) => setQualityStatus(event.target.value)}><option value="OPEN">Avatud</option><option value="ASSIGNED">Määratud</option><option value="RESOLVED">Lahendatud</option><option value="">Kõik</option></select><button className="secondary-action" onClick={() => void runQualityScan()}><RefreshCw size={15} /> Käivita kontroll</button></div>{qualityError ? <div className="connection-warning" role="alert"><p>{qualityError}</p><button className="secondary-action mt-2" onClick={() => void refreshQuality()}><RefreshCw size={14} /> Proovi uuesti</button></div> : qualityLoading ? <div className="empty-state" role="status">Laadin andmekvaliteedi järjekorda…</div> : <div className="space-y-2">{quality.map((issue) => <article className="rounded-xl border border-border p-3" key={issue.id}><div className="flex flex-wrap items-center justify-between gap-2"><div><span className="status-pill warning">{issue.severity}</span><strong className="ml-2">{issue.type.replaceAll("_", " ")}</strong></div><span>{issue.status}</span></div><p className="mt-2 text-sm">{issue.description}</p><small>{issue.owner?.name || issue.dealId || "mitme omaniku kontroll"} · vastutaja {issue.assignee?.name || issue.suggestedAssignee?.name || "määramata"}</small><div className="mt-3 flex flex-wrap gap-2">{issue.status !== "ASSIGNED" && issue.status !== "RESOLVED" && <button className="secondary-action" onClick={() => void qualityAction(issue, "ASSIGN")}>Määra mulle</button>}{issue.status === "ASSIGNED" && <button className="secondary-action" onClick={() => void qualityAction(issue, "RELEASE")}>Vabasta</button>}{issue.status !== "RESOLVED" && <button className="secondary-action" onClick={() => void qualityAction(issue, "RESOLVE")}><CheckCircle2 size={14} /> Lahenda</button>}</div></article>)}{!quality.length && <div className="empty-state">Selles olekus andmekvaliteedi probleeme ei ole.</div>}</div>}</section>}

    {tab === "losses" && <section id="p1-panel-losses" role="tabpanel" aria-labelledby="p1-tab-losses" className="panel p-5">{referenceError ? <div className="connection-warning" role="alert"><p>{referenceError}</p><button className="secondary-action mt-2" onClick={() => void refreshReferenceData()}><RefreshCw size={14} /> Proovi uuesti</button></div> : referenceLoading ? <div className="empty-state" role="status">Laadin kaotuse põhjuseid…</div> : <><div className="panel-heading"><div><p className="eyebrow">KAOTUSE ANALÜÜS</p><h3>Põhjused, müüjad ja eelnev etapp</h3></div><Settings2 size={19} /></div><div className="mb-5 grid gap-2 md:grid-cols-5"><input type="date" value={lossFrom} onChange={(event) => setLossFrom(event.target.value)} aria-label="Kaotuste perioodi algus" /><input type="date" value={lossTo} onChange={(event) => setLossTo(event.target.value)} aria-label="Kaotuste perioodi lõpp" /><input value={lossSeller} onChange={(event) => setLossSeller(event.target.value)} placeholder="Müüja ID" aria-label="Müüja ID" /><select value={lossStage} onChange={(event) => setLossStage(event.target.value)} aria-label="Eelnev etapp"><option value="">Kõik etapid</option><option value="QUALIFICATION">Qualification</option><option value="EVALUATION">Evaluation</option><option value="NEGOTIATION">Negotiation</option></select><div className="flex gap-2"><button className="secondary-action" onClick={() => void refreshLossAnalysis()}>Rakenda</button><button className="secondary-action" onClick={exportLossAnalysis} disabled={!lossAnalysis.length}>CSV</button></div></div><div className="mb-6 overflow-x-auto"><table className="w-full text-sm"><thead><tr><th className="text-left">Põhjus</th><th className="text-left">Müüja</th><th className="text-left">Eelnev etapp</th><th className="text-right">Arv</th></tr></thead><tbody>{lossAnalysis.map((row) => <tr key={`${row.reasonCode}-${row.sellerId}-${row.previousStage}`}><td>{row.reasonLabel}</td><td>{row.sellerId || "—"}</td><td>{row.previousStage || "—"}</td><td className="text-right">{row.count}</td></tr>)}</tbody></table>{!lossAnalysis.length && <div className="empty-state">Valitud filtritega kaotusi ei ole.</div>}</div><div className="panel-heading"><div><p className="eyebrow">KLASSIFIKAATOR</p><h3>Hallatavad kaotuse põhjused</h3></div></div><div className="mb-5 grid gap-2 md:grid-cols-[220px_1fr_auto]"><input value={newReasonCode} onChange={(event) => setNewReasonCode(event.target.value)} placeholder="Kood, nt ACCESS" /><input value={newReasonLabel} onChange={(event) => setNewReasonLabel(event.target.value)} placeholder="Kasutajale nähtav põhjus" /><button className="secondary-action" onClick={() => void addLossReason()}>Lisa põhjus</button></div><div className="space-y-2">{lossReasons.map((reason) => <div className="flex items-center justify-between rounded-xl border border-border p-3" key={reason.id}><div><strong>{reason.code} · {reason.label}</strong><small className="block">{reason.description || "kirjeldus puudub"}</small></div><button className="secondary-action" onClick={() => void toggleLossReason(reason)}>{reason.active ? "Deaktiveeri" : "Aktiveeri"}</button></div>)}</div></>}</section>}

    {tab === "contracts" && (referenceError ? <section id="p1-panel-contracts" role="tabpanel" aria-labelledby="p1-tab-contracts" className="panel p-5"><div className="connection-warning" role="alert"><p>{referenceError}</p><button className="secondary-action mt-2" onClick={() => void refreshReferenceData()}><RefreshCw size={14} /> Proovi uuesti</button></div></section> : referenceLoading ? <section id="p1-panel-contracts" role="tabpanel" aria-labelledby="p1-tab-contracts" className="panel p-5"><div className="empty-state" role="status">Laadin lepingukontrolli andmeid…</div></section> : <section id="p1-panel-contracts" role="tabpanel" aria-labelledby="p1-tab-contracts" className="grid gap-5 xl:grid-cols-[1fr_1.2fr]"><article className="panel p-5"><div className="panel-heading"><div><p className="eyebrow">LEPINGUD</p><h3>Vali kontrollitav leping</h3></div><BadgeEuro size={19} /></div><div className="space-y-2">{contracts.map((contract) => <button className="flex w-full items-center justify-between rounded-xl border border-border p-3 text-left" key={contract.id} onClick={() => void openContract(contract)}><span><strong>{contract.contractNo || contract.id}</strong><small className="block">{contract.sellers || "müüja"} · {contract.status}</small></span><span>→</span></button>)}</div></article><article className="panel p-5"><div className="panel-heading"><div><p className="eyebrow">ALLKIRJASTAMINE JA VERSIOONID</p><h3>{selectedContract?.contractNo || selectedContract?.id || "Vali leping"}</h3></div><FileSignature size={19} /></div>{signing ? <><div className="mb-4 rounded-xl bg-muted p-3"><strong>{signing.state.replaceAll("_", " ")}</strong><p className="text-sm">Vastutaja {signing.responsible?.name || "määramata"} · tähtaeg {dateTime(signing.dueAt)}</p><p className="text-sm">Allkirjakontroll: {signing.verification.status.replaceAll("_", " ")}{signing.verification.verifiedAt ? ` · ${dateTime(signing.verification.verifiedAt)}` : ""}</p>{signing.verification.signer?.name && <p className="text-sm">Allkirjastaja {signing.verification.signer.name}</p>}{signing.verification.documentSha256 && <small className="block">Dokumendi SHA-256 {signing.verification.documentSha256.slice(0, 16)}…{signing.verification.integrityValid === false ? " · FAILI SISU ON MUUTUNUD" : ""}</small>}{signing.verification.failureReason && <p className="text-sm text-destructive">{signing.verification.failureReason}</p>}{signing.finalUrl && <p className="text-sm">{signing.finalUrl}</p>}</div><div className="flex flex-wrap gap-2">{signing.state === "PREPARING" && <button className="secondary-action" onClick={() => void sendForSignature()}>Saada allkirjastamisele</button>}{signing.state === "SENT_FOR_SIGNATURE" && <label className="secondary-action cursor-pointer">Lisa PDF/ASiC-E<input className="hidden" type="file" accept=".pdf,.asice" onChange={(event) => { const file = event.target.files?.[0]; if (file) void uploadSignature(file); }} /></label>}<button className="secondary-action" disabled={!selectedContract?.version || !versions.length} onClick={() => void createReplacementVersion()}>Loo kontrollitud asendusversioon</button></div><div className="mt-5 space-y-2">{versions.map((version) => <div className="rounded-lg border border-border p-2 text-sm" key={version.id}><strong>Versioon {version.version}</strong> · {version.replacement ? "asendus" : "algne"}<small className="block">SHA-256 {version.pdfSha256.slice(0, 16)}… · {dateTime(version.createdAt)}</small>{version.changeReason && <p>{version.changeReason}</p>}</div>)}{!versions.length && <div className="empty-state">Kontrollitud lepinguversioone ei ole.</div>}</div></> : <div className="empty-state">Vali vasakult leping.</div>}</article></section>)}
    <ConfirmDialog
      open={Boolean(pendingLostDeal)}
      title="Märgi tehing kaotatuks?"
      description={pendingLostDeal ? `${pendingLostDeal.owner.name} tehing liigub olekusse LOST. Põhjus ja muudatus jäävad auditisse; taastamine nõuab uut auditeeritud töövoomuudatust.` : ""}
      confirmLabel="Märgi kaotatuks"
      destructive
      busy={lostBusy}
      onCancel={() => { if (!lostBusy) setPendingLostDeal(null); }}
      onConfirm={() => void confirmMarkLost()}
    />
  </AppShell>;
}
