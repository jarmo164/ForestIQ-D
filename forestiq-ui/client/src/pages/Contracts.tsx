import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Download, Eye, FilePlus2, FileStack, Plus, Search, Settings2 } from "lucide-react";
import { Link, useLocation } from "wouter";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { CompanyProfile, ContractDraft, ContractHistoryRecord, ContractTemplate } from "@/lib/types";

type Tab = "history" | "create" | "settings";
type TemplateForm = { templateKey: string; name: string; description: string; html: string; companyProfileId: string };
type ProfileForm = { legalName: string; registryCode: string; address: string; email: string; phone: string; iban: string; signatoryName: string; website: string };

const blankTemplate: TemplateForm = { templateKey: "", name: "", description: "", html: "<h1>Ostu-müügileping</h1>\n<p>{{company.legalName}}</p>\n<p>{{deal.sellerName}}</p>", companyProfileId: "" };
const blankProfile: ProfileForm = { legalName: "", registryCode: "", address: "", email: "", phone: "", iban: "", signatoryName: "", website: "" };

function apiError(error: unknown, fallback: string) { return error instanceof Error ? error.message : fallback; }
function formatDate(value?: number | string | null) { if (!value) return "—"; const date = new Date(typeof value === "number" && value < 1_000_000_000_000 ? value * 1000 : value); return Number.isNaN(date.valueOf()) ? "—" : new Intl.DateTimeFormat("et-EE", { dateStyle: "medium", timeStyle: "short" }).format(date); }
function inputDate(value?: string | number | null) { if (!value) return ""; const date = new Date(typeof value === "number" && value < 1_000_000_000_000 ? value * 1000 : value); return Number.isNaN(date.valueOf()) ? "" : date.toISOString().slice(0, 10); }

export default function Contracts() {
  const [, navigate] = useLocation();
  const initialDealId = new URLSearchParams(window.location.search).get("dealId") || "";
  const [tab, setTab] = useState<Tab>(initialDealId ? "create" : "history");
  const [contracts, setContracts] = useState<ContractHistoryRecord[]>([]);
  const [templates, setTemplates] = useState<ContractTemplate[]>([]);
  const [profiles, setProfiles] = useState<CompanyProfile[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("ALL");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [selected, setSelected] = useState<ContractHistoryRecord | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [dealId, setDealId] = useState(initialDealId);
  const [draft, setDraft] = useState<ContractDraft | null>(null);
  const [templateId, setTemplateId] = useState("");
  const [contractNumber, setContractNumber] = useState("");
  const [previewHtml, setPreviewHtml] = useState("");
  const [templateForm, setTemplateForm] = useState<TemplateForm>(blankTemplate);
  const [profileForm, setProfileForm] = useState<ProfileForm>(blankProfile);
  const [editingTemplate, setEditingTemplate] = useState<ContractTemplate | null>(null);
  const [editingProfile, setEditingProfile] = useState<CompanyProfile | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const parameters = new URLSearchParams();
      if (status !== "ALL") parameters.set("status", status);
      if (fromDate) parameters.set("from", fromDate);
      if (toDate) parameters.set("to", toDate);
      const suffix = parameters.toString() ? `?${parameters}` : "";
      const [history, activeTemplates, companyProfiles] = await Promise.all([
        api.get<ContractHistoryRecord[]>(`/services/contracts${suffix}`),
        api.get<ContractTemplate[]>("/services/contract-templates"),
        api.get<CompanyProfile[]>("/services/company-profiles"),
      ]);
      setContracts(history); setTemplates(activeTemplates); setProfiles(companyProfiles);
      const firstActiveTemplate = activeTemplates.find((template) => template.isActive);
      if (!templateId && firstActiveTemplate) setTemplateId(firstActiveTemplate.id);
    } catch (reason) { setError(apiError(reason, "Lepingute andmeid ei saanud laadida.")); }
    finally { setLoading(false); }
  }, [fromDate, status, templateId, toDate]);

  useEffect(() => { void refresh(); }, [refresh]);

  const filteredContracts = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("et-EE");
    if (!normalized) return contracts;
    return contracts.filter((contract) => [contract.contractNo, contract.sellers, contract.buyer, contract.ownerId, contract.dealId, contract.status].filter(Boolean).join(" ").toLocaleLowerCase("et-EE").includes(normalized));
  }, [contracts, query]);
  const activeTemplates = templates.filter((template) => template.isActive);
  const chosenTemplate = activeTemplates.find((template) => template.id === templateId) || null;
  const chosenProfile = profiles.find((profile) => profile.id === chosenTemplate?.companyProfileId) || null;

  const loadDraft = async () => {
    if (!dealId.trim()) { setError("Sisesta tehingu tunnus või ava lepingu koostamine tehingu töökaardilt."); return; }
    try {
      setError("");
      const nextDraft = await api.get<ContractDraft>(`/services/contracts/deals/${encodeURIComponent(dealId.trim())}/draft`);
      setDraft(nextDraft);
      setContractNumber(`FIQ-${new Date().getFullYear()}-${nextDraft.dealId.slice(0, 8).toUpperCase()}`);
      setPreviewHtml("");
    } catch (reason) { setDraft(null); setError(apiError(reason, "Lepingu lähteandmeid ei saanud laadida.")); }
  };

  const preview = async () => {
    if (!draft || !chosenTemplate) { setError("Vali sobiv tehing ja aktiivne lepingumall."); return; }
    try {
      setError("");
      const result = await api.post<{ html: string }>(`/services/contract-templates/${chosenTemplate.id}/preview`, { dealId: draft.dealId });
      setPreviewHtml(result.html);
    } catch (reason) { setError(apiError(reason, "Malli eelvaadet ei saanud koostada.")); }
  };

  const generate = async () => {
    if (!draft || !chosenTemplate || !contractNumber.trim()) { setError("Sisesta lepingu number ning vali tehing ja aktiivne mall."); return; }
    try {
      setError("");
      const result = await api.post<{ contractId: string; pdf: string }>("/services/contracts/generate-from-deal", { dealId: draft.dealId, version: draft.dealVersion, contractNumber: contractNumber.trim(), templateId: chosenTemplate.id, buyer: chosenProfile?.legalName || "ForestIQ buyer" });
      setNotice(`Leping ${result.contractId} loodi serveripoolse PDF-iga.`);
      await refresh();
      navigate(`/contracts?contractId=${encodeURIComponent(result.contractId)}`);
      setTab("history");
    } catch (reason) { setError(apiError(reason, "Lepingut ei saanud genereerida.")); }
  };

  const openDetail = async (contract: ContractHistoryRecord) => {
    setSelected(contract); setDetail(null); setError("");
    try { setDetail(await api.get<Record<string, unknown>>(`/services/contracts/${encodeURIComponent(contract.id)}`)); }
    catch (reason) { setError(apiError(reason, "Lepingu detaili ei saanud laadida.")); }
  };

  const archive = async (contract: ContractHistoryRecord) => {
    if (contract.version == null) { setError("Orvuks jäänud lepingut ei saa kasutajaliidesest arhiveerida."); return; }
    try { await api.patch(`/services/contracts/${encodeURIComponent(contract.id)}`, { status: "ARCHIVED", version: contract.version }); setNotice(`Leping ${contract.contractNo} arhiveeriti.`); setSelected(null); await refresh(); }
    catch (reason) { setError(apiError(reason, "Lepingut ei saanud arhiveerida.")); }
  };

  const createProfile = async (event: FormEvent) => {
    event.preventDefault();
    try {
      if (editingProfile) await api.patch<CompanyProfile>(`/services/company-profiles/${editingProfile.id}`, { ...profileForm, version: editingProfile.version });
      else await api.post<CompanyProfile>("/services/company-profiles", profileForm);
      setProfileForm(blankProfile); setEditingProfile(null); setNotice(editingProfile ? "Ettevõtteprofiil uuendati." : "Ettevõtteprofiil lisati."); await refresh();
    } catch (reason) { setError(apiError(reason, "Ettevõtteprofiili ei saanud salvestada.")); }
  };

  const createTemplate = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const payload = { ...templateForm, companyProfileId: templateForm.companyProfileId || null };
      if (editingTemplate) await api.patch<ContractTemplate>(`/services/contract-templates/${editingTemplate.id}`, { ...payload, version: editingTemplate.version });
      else await api.post<ContractTemplate>("/services/contract-templates", payload);
      setTemplateForm(blankTemplate); setEditingTemplate(null); setNotice(editingTemplate ? "Lepingumallil loodi uus versioon." : "Lepingumall lisati."); await refresh();
    } catch (reason) { setError(apiError(reason, "Lepingumalli ei saanud salvestada.")); }
  };

  const beginProfileEdit = (profile: CompanyProfile) => {
    setEditingProfile(profile);
    setProfileForm({ legalName: profile.legalName, registryCode: profile.registryCode || "", address: profile.address || "", email: profile.email || "", phone: profile.phone || "", iban: profile.iban || "", signatoryName: profile.signatoryName || "", website: profile.website || "" });
  };
  const beginTemplateEdit = (template: ContractTemplate) => {
    setEditingTemplate(template);
    setTemplateForm({ templateKey: template.templateKey, name: template.name, description: template.description || "", html: template.html, companyProfileId: template.companyProfileId || "" });
  };
  const archiveTemplate = async (template: ContractTemplate) => {
    try { await api.delete<ContractTemplate>(`/services/contract-templates/${template.id}`, { version: template.version }); setNotice(`Mall ${template.name} arhiveeriti.`); await refresh(); }
    catch (reason) { setError(apiError(reason, "Lepingumalli ei saanud arhiveerida.")); }
  };
  const deleteProfile = async (profile: CompanyProfile) => {
    try { await api.delete(`/services/company-profiles/${profile.id}`); setNotice(`Ettevõtteprofiil ${profile.legalName} kustutati.`); await refresh(); }
    catch (reason) { setError(apiError(reason, "Ettevõtteprofiili ei saanud kustutada.")); }
  };

  return <AppShell title="Lepingute tööala" eyebrow="KOMMERTS / LEPINGUD">
    <section className="workspace-intro contracts-intro"><FileStack size={24} /><div><h2>Lepingud, eelvaated ja mallid ühel tööpinnal</h2><p>Otsi ning laadi alla lepinguid, koosta võidetud tehingust mallipõhine PDF ja halda ettevõtteprofiile.</p></div><div className="workspace-count">{contracts.length}<small>lepingut</small></div></section>
    {notice && <div className="success-notice">{notice}</div>}{error && <div className="connection-warning">{error}</div>}
    <div className="contracts-tabs" role="tablist" aria-label="Lepingute tööala vaated">
      <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")} role="tab" aria-selected={tab === "history"}>Lepingute register</button>
      <button className={tab === "create" ? "active" : ""} onClick={() => setTab("create")} role="tab" aria-selected={tab === "create"}>Koosta leping</button>
      <button className={tab === "settings" ? "active" : ""} onClick={() => setTab("settings")} role="tab" aria-selected={tab === "settings"}>Mallid ja ettevõtted</button>
    </div>

    {tab === "history" && <section className="panel contracts-panel"><div className="table-toolbar contracts-filters"><label><Search size={16} /><input aria-label="Otsi lepinguid" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Otsi numbri, müüja või ostja järgi" /></label><label>Olek<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="ALL">Kõik</option><option value="ACTIVE">Aktiivne</option><option value="ARCHIVED">Arhiveeritud</option></select></label><label>Alates<input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} /></label><label>Kuni<input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} /></label></div>
      {loading ? <div className="empty-state">Laadin lepingute registrit…</div> : <div className="data-table"><div className="table-row table-header"><span>Leping</span><span>Pooled</span><span>Koostatud</span><span>Olek</span><span>Toimingud</span></div>{filteredContracts.map((contract) => <div className="table-row" key={contract.id}><span><strong>{contract.contractNo || contract.id}</strong><small>{contract.templateVersion?.name || "Mallita ajalookirje"}</small></span><span>{contract.sellers || "—"}<small>{contract.buyer || "Ostja puudub"}</small></span><span>{formatDate(contract.created)}</span><span><span className={`status-pill ${contract.status === "ARCHIVED" ? "warning" : ""}`}>{contract.status}</span></span><span className="contract-actions"><button className="secondary-action" onClick={() => void openDetail(contract)}><Eye size={15} /> Vaata</button><button className="secondary-action" onClick={() => void api.download(`/services/contracts/${encodeURIComponent(contract.id)}/pdf`, `${contract.contractNo || contract.id}.pdf`).catch((reason) => setError(apiError(reason, "PDF-i ei saanud alla laadida.")))}><Download size={15} /> PDF</button></span></div>)}{!filteredContracts.length && <div className="empty-state">Filtritele vastavaid lepinguid ei leitud.</div>}</div>}
    </section>}

    {tab === "create" && <section className="contracts-grid"><article className="panel p-5"><div className="panel-heading"><div><p className="eyebrow">1. TEHING</p><h3>Vali võidetud tehing</h3></div><FilePlus2 size={19} /></div><p className="mb-4 text-sm text-muted-foreground">Ava see vaade omaniku töökaardilt või sisesta tehingu tunnus. Server kontrollib aktsepteeritud pakkumist ja kaasatud kinnistuid.</p><div className="contract-inline-form"><input aria-label="Tehingu tunnus" value={dealId} onChange={(event) => setDealId(event.target.value)} placeholder="Tehingu UUID" /><button className="secondary-action" onClick={() => void loadDraft()}>Laadi tehing</button></div>{draft && <div className="contract-draft"><strong>{draft.seller.name}</strong><p>{draft.parcels.length} kinnistut · aktsepteeritud hind {draft.acceptedPrice ?? "—"} €</p><p>{draft.parcels.map((parcel) => parcel.cadastralCode).join(", ")}</p></div>}</article>
      <article className="panel p-5"><div className="panel-heading"><div><p className="eyebrow">2. MALL JA ETTEVÕTE</p><h3>Koosta eelvaade</h3></div><Settings2 size={19} /></div><label className="contract-field">Lepingumall<select aria-label="Lepingumall" value={templateId} onChange={(event) => { setTemplateId(event.target.value); setPreviewHtml(""); }}><option value="">Vali aktiivne mall</option>{activeTemplates.map((template) => <option key={template.id} value={template.id}>{template.name} · v{template.version}</option>)}</select></label>{chosenTemplate && <div className="contract-draft"><strong>{chosenProfile?.legalName || "Ettevõtteprofiilita mall"}</strong><p>{chosenTemplate.description || "Malli kirjeldus puudub."}</p></div>}<label className="contract-field">Lepingu number<input value={contractNumber} onChange={(event) => setContractNumber(event.target.value)} placeholder="FIQ-2026-0001" /></label><div className="mt-4 flex flex-wrap gap-2"><button className="secondary-action" disabled={!draft || !chosenTemplate} onClick={() => void preview()}><Eye size={16} /> Eelvaade</button><button className="primary-action" disabled={!draft || !chosenTemplate || !contractNumber.trim()} onClick={() => void generate()}><FilePlus2 size={16} /> Genereeri PDF</button></div></article>
      {previewHtml && <article className="panel p-5 contracts-preview"><p className="eyebrow">MALLI EELVAADE</p><iframe title="Lepingumalli eelvaade" sandbox="" srcDoc={previewHtml} /></article>}
    </section>}

    {tab === "settings" && <section className="contracts-grid"><article className="panel p-5"><div className="panel-heading"><div><p className="eyebrow">ETTEVÕTTEPROFIILID</p><h3>{editingProfile ? "Muuda ettevõtet" : "Lisa ettevõte"}</h3></div><Plus size={19} /></div><form className="contract-form" onSubmit={createProfile}><input required value={profileForm.legalName} onChange={(event) => setProfileForm({ ...profileForm, legalName: event.target.value })} placeholder="Juriidiline nimi" /><input value={profileForm.registryCode} onChange={(event) => setProfileForm({ ...profileForm, registryCode: event.target.value })} placeholder="Registrikood" /><input value={profileForm.address} onChange={(event) => setProfileForm({ ...profileForm, address: event.target.value })} placeholder="Aadress" /><input type="email" value={profileForm.email} onChange={(event) => setProfileForm({ ...profileForm, email: event.target.value })} placeholder="E-post" /><input value={profileForm.phone} onChange={(event) => setProfileForm({ ...profileForm, phone: event.target.value })} placeholder="Telefon" /><input value={profileForm.iban} onChange={(event) => setProfileForm({ ...profileForm, iban: event.target.value })} placeholder="IBAN" /><input value={profileForm.signatoryName} onChange={(event) => setProfileForm({ ...profileForm, signatoryName: event.target.value })} placeholder="Allkirjastaja nimi" /><input value={profileForm.website} onChange={(event) => setProfileForm({ ...profileForm, website: event.target.value })} placeholder="Veebileht" /><div className="contract-form-actions"><button className="primary-action" type="submit">{editingProfile ? "Uuenda ettevõte" : "Salvesta ettevõte"}</button>{editingProfile && <button className="secondary-action" type="button" onClick={() => { setEditingProfile(null); setProfileForm(blankProfile); }}>Tühista</button>}</div></form><div className="contract-list">{profiles.map((profile) => <div key={profile.id}><div><strong>{profile.legalName}</strong><span>{profile.registryCode || "Registrikood puudub"}</span></div><div className="contract-list-actions"><button type="button" onClick={() => beginProfileEdit(profile)}>Muuda</button><button type="button" onClick={() => void deleteProfile(profile)}>Kustuta</button></div></div>)}{!profiles.length && <p>Ettevõtteprofiile pole veel lisatud.</p>}</div></article>
      <article className="panel p-5"><div className="panel-heading"><div><p className="eyebrow">LEPINGUMALLID</p><h3>{editingTemplate ? "Reviseeri malli" : "Lisa aktiivne mall"}</h3></div><Plus size={19} /></div><form className="contract-form" onSubmit={createTemplate}><input required value={templateForm.templateKey} onChange={(event) => setTemplateForm({ ...templateForm, templateKey: event.target.value })} placeholder="Malli võti, nt ostu-muuk" /><input required value={templateForm.name} onChange={(event) => setTemplateForm({ ...templateForm, name: event.target.value })} placeholder="Malli nimi" /><select value={templateForm.companyProfileId} onChange={(event) => setTemplateForm({ ...templateForm, companyProfileId: event.target.value })}><option value="">Ettevõtteprofiil puudub</option>{profiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.legalName}</option>)}</select><textarea required value={templateForm.description} onChange={(event) => setTemplateForm({ ...templateForm, description: event.target.value })} placeholder="Kirjeldus" /><textarea required value={templateForm.html} onChange={(event) => setTemplateForm({ ...templateForm, html: event.target.value })} placeholder="Malli HTML" rows={9} /><div className="contract-form-actions"><button className="primary-action" type="submit">{editingTemplate ? "Loo uus malliversioon" : "Salvesta mall"}</button>{editingTemplate && <button className="secondary-action" type="button" onClick={() => { setEditingTemplate(null); setTemplateForm(blankTemplate); }}>Tühista</button>}</div></form><div className="contract-list">{templates.map((template) => <div key={template.id}><div><strong>{template.name}</strong><span>{template.templateKey} · v{template.version} · {template.isActive ? "aktiivne" : "arhiveeritud"}</span></div>{template.isActive && <div className="contract-list-actions"><button type="button" onClick={() => beginTemplateEdit(template)}>Muuda</button><button type="button" onClick={() => void archiveTemplate(template)}>Arhiveeri</button></div>}</div>)}{!templates.length && <p>Aktiivseid malle pole veel lisatud.</p>}</div></article>
    </section>}

    {selected && <div className="contract-modal-backdrop" role="presentation" onMouseDown={() => setSelected(null)}><article className="panel contract-modal" role="dialog" aria-modal="true" aria-labelledby="contract-detail-title" onMouseDown={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">LEPINGU DETAIL</p><h3 id="contract-detail-title">{selected.contractNo || selected.id}</h3></div><button className="secondary-action" onClick={() => setSelected(null)}>Sulge</button></div><dl><dt>Müüja</dt><dd>{selected.sellers || "—"}</dd><dt>Ostja</dt><dd>{selected.buyer || "—"}</dd><dt>Koostatud</dt><dd>{formatDate(selected.created)}</dd><dt>Säilitustähtaeg</dt><dd>{formatDate(selected.retentionUntil)}</dd><dt>Mall</dt><dd>{selected.templateVersion?.name || "Ajalooline mall puudub"}</dd></dl>{detail && <details><summary>Tehnilised lepinguandmed</summary><pre>{JSON.stringify(detail, null, 2)}</pre></details>}<div className="mt-5 flex flex-wrap gap-2"><button className="secondary-action" onClick={() => void api.download(`/services/contracts/${encodeURIComponent(selected.id)}/pdf`, `${selected.contractNo || selected.id}.pdf`).catch((reason) => setError(apiError(reason, "PDF-i ei saanud alla laadida.")))}><Download size={16} /> Laadi PDF</button>{selected.status === "ACTIVE" && <button className="secondary-action" onClick={() => void archive(selected)}>Arhiveeri</button>}{selected.ownerId && <Link className="secondary-action" href={`/owners/${selected.ownerId}`}>Ava omanik</Link>}</div></article></div>}
  </AppShell>;
}
