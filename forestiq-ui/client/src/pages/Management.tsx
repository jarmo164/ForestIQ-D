/** Role-gated management dashboards backed by compact tenant-scoped APIs. */
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, BarChart3, BellRing, ChevronRight, ClipboardCheck, Clock3, FileWarning, Layers3, UsersRound } from "lucide-react";
import { Link } from "wouter";

import { AppShell } from "@/components/AppShell";
import { Metric } from "@/components/Metric";
import { useAuth } from "@/contexts/AuthContext";
import {
  type DashboardStats,
  type SalesManagementOverview,
  filterSalesInterventions,
  filterSalesTeam,
  interventionLabel,
} from "@/lib/managementOverview";
import { api } from "@/lib/api";

function ApiError({ error }: { error: string }) {
  return error ? <div className="connection-warning">Juhtimisandmete laadimine ebaõnnestus: {error}</div> : null;
}

function ManagementDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [focus, setFocus] = useState<"OVERVIEW" | "DEADLINES" | "DEALS">("OVERVIEW");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<DashboardStats>("/services/admin/dashboard-stats").then(setStats).catch((requestError: Error) => setError(requestError.message));
  }, []);

  return (
    <section className="management-section">
      <div className="management-toolbar">
        <div><p className="eyebrow">ORGANISATSIOONI ÜLEVAADE</p><h2>Juhtimise töölaud</h2></div>
        <div className="management-filter-options" aria-label="Juhtimisvaate fookus">
          {["OVERVIEW", "DEADLINES", "DEALS"].map((option) => <button type="button" key={option} className={focus === option ? "active" : ""} aria-pressed={focus === option} onClick={() => setFocus(option as typeof focus)}>{option === "OVERVIEW" ? "Ülevaade" : option === "DEADLINES" ? "Tähtajad" : "Tehingud"}</button>)}
        </div>
      </div>
      <ApiError error={error} />
      {!stats && !error && <div className="empty-state">Laadin organisatsiooni koondnäitajaid…</div>}
      {stats && <>
        {(focus === "OVERVIEW" || focus === "DEADLINES") && <section className="metrics-grid management-metrics">
          <Metric icon={AlertTriangle} label="Hilinenud tähtajad" value={stats.deadlines.overdue} detail="vajavad sekkumist" tone="rose" />
          <Metric icon={BellRing} label="Tähtaeg 7 päeva" value={stats.deadlines.nextSevenDays} detail="järgmised tegevused" tone="ochre" />
          <Metric icon={UsersRound} label="Aktiivsed omanikud" value={stats.activeOwners} detail={`${stats.newLeads} uut müügivihjet`} tone="moss" />
          <Metric icon={ClipboardCheck} label="Hindamise ootel" value={stats.evaluationPending} detail="vajab hinnangut" />
        </section>}
        {(focus === "OVERVIEW" || focus === "DEADLINES") && <section className="management-breakdown" aria-label="Tähtaegade jaotus">
          <header><div><p className="eyebrow">DRILL-DOWN</p><h3>Tähtaegade liigid</h3></div><Link href="/reminders">Ava tähtajad <ChevronRight size={16} /></Link></header>
          <div className="management-breakdown-grid">
            {[
              ["Meeldetuletused", stats.deadlines.reminders, "/reminders"],
              ["Pärimisjuhtumid", stats.deadlines.inheritance, "/inheritance"],
              ["Pakkumised", stats.deadlines.offers, "/deals"],
            ].map(([label, values, href]) => {
              const deadline = values as { overdue: number; nextSevenDays: number };
              return <Link href={href as string} key={label as string} className="management-breakdown-card"><strong>{label as string}</strong><span>{deadline.overdue} hilinenud</span><small>{deadline.nextSevenDays} järgmise 7 päeva jooksul</small></Link>;
            })}
          </div>
        </section>}
        {(focus === "OVERVIEW" || focus === "DEALS") && <section className="management-breakdown" aria-label="Tehingute etapid">
          <header><div><p className="eyebrow">DRILL-DOWN</p><h3>Tehingute etapid</h3></div><Link href="/deals">Ava tehingud <ChevronRight size={16} /></Link></header>
          <div className="management-stage-grid">{Object.entries(stats.dealStages).map(([stage, count]) => <Link href="/deals" key={stage} className="management-stage"><span>{stage.replaceAll("_", " ")}</span><strong>{count}</strong></Link>)}</div>
        </section>}
      </>}
    </section>
  );
}

function SalesManagement() {
  const [overview, setOverview] = useState<SalesManagementOverview | null>(null);
  const [memberId, setMemberId] = useState("ALL");
  const [kind, setKind] = useState("ALL");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<SalesManagementOverview>("/services/admin/sales-management-overview").then(setOverview).catch((requestError: Error) => setError(requestError.message));
  }, []);

  const team = useMemo(() => overview ? filterSalesTeam(overview.team, memberId) : [], [overview, memberId]);
  const interventions = useMemo(() => overview ? filterSalesInterventions(overview.interventions, memberId, kind) : [], [overview, memberId, kind]);

  return (
    <section className="management-section">
      <div className="management-toolbar sales-management-heading"><div><p className="eyebrow">MÜÜGIJUHTIMINE</p><h2>Meeskonna tulemused ja sekkumised</h2><p>Kontaktitulemused viimase 30 päeva jooksul ning aktiivne töökoormus.</p></div></div>
      <ApiError error={error} />
      {!overview && !error && <div className="empty-state">Laadin müügijuhtimise ülevaadet…</div>}
      {overview && <>
        <section className="sales-filter-panel" aria-label="Müügijuhtimise filtrid">
          <label>Meeskonnaliige<select value={memberId} onChange={(event) => setMemberId(event.target.value)}><option value="ALL">Kõik liikmed</option>{overview.team.map((member) => <option value={member.member.id} key={member.member.id}>{member.member.name}</option>)}</select></label>
          <label>Sekkumise liik<select value={kind} onChange={(event) => setKind(event.target.value)}><option value="ALL">Kõik sekkumised</option><option value="UNASSIGNED_EVALUATION">Hindaja määramata</option><option value="EXPIRED_OFFER">Pakkumine aegunud</option><option value="OVERDUE_REMINDER">Meeldetuletus hilinenud</option></select></label>
          <strong><FileWarning size={16} /> {interventions.length} sekkumist</strong>
        </section>
        <section className="sales-team-grid" aria-label="Meeskonna töökoormus">{team.map((member) => <article className="sales-team-card" key={member.member.id}><header><div><p className="eyebrow">MEESKONNALIIGE</p><h3>{member.member.name}</h3></div><UsersRound size={20} /></header><div className="sales-workload"><span><strong>{member.workload.assignedOwners}</strong> määratud omanikku</span><span><strong>{member.workload.activeDeals}</strong> aktiivset tehingut</span><span><strong>{member.workload.evaluationDeals}</strong> hindamist</span><span><strong>{member.workload.overdueReminders}</strong> hilinenud tähtaega</span></div><div className="sales-outcomes"><p>Kontaktitulemused</p>{Object.entries(member.contactOutcomes).filter(([, count]) => count > 0).map(([outcome, count]) => <span key={outcome}>{outcome.replaceAll("_", " ")} <strong>{count}</strong></span>)}{!Object.values(member.contactOutcomes).some((count) => count > 0) && <small>Kontaktitulemusi pole.</small>}</div></article>)}{!team.length && <div className="empty-state">Valitud liikmel puudub nähtav müügitöö.</div>}</section>
        <section className="management-breakdown sales-interventions" aria-label="Sekkumiste tööjärjekord"><header><div><p className="eyebrow">SEKKUMISED</p><h3>Prioriteetsed tegevused</h3></div><span>{interventions.length} kirjet</span></header><div className="sales-intervention-list">{interventions.map((intervention) => <Link href={`/owners/${intervention.ownerId}`} key={`${intervention.kind}-${intervention.dealId || intervention.reminderId}`} className="sales-intervention"><Clock3 size={17} /><div><strong>{interventionLabel(intervention.kind)}</strong><p>{intervention.ownerName}</p></div><span>{intervention.dueAt ? new Date(intervention.dueAt).toLocaleDateString("et-EE") : "Määra hindaja"}</span><ChevronRight size={16} /></Link>)}{!interventions.length && <div className="empty-state">Valitud filtritega sekkumisi ei ole.</div>}</div></section>
      </>}
    </section>
  );
}

export default function Management() {
  const { user } = useAuth();
  const isAdmin = Boolean(user?.privileges.includes("ADMIN"));
  const isSalesManager = Boolean(user?.roles.some((role) => ["ORG_OWNER", "ORG_ADMIN", "CRM_MANAGER"].includes(role)) || user?.privileges.includes("ADMIN"));
  const [view, setView] = useState<"DASHBOARD" | "SALES">(isSalesManager && !isAdmin ? "SALES" : "DASHBOARD");

  return (
    <AppShell title="Juhtimisvaated" eyebrow="FORESTIQ / JUHTIMINE">
      <section className="management-hero"><div><p className="eyebrow light">ROLLIPÕHINE JUHTIMINE</p><h2>Organisatsiooni tervikpilt ja müügitöö sekkumised.</h2><p>Vaata ainult neid juhtimisandmeid, milleks sinu rollil on õigus.</p></div><BarChart3 size={42} /></section>
      <div className="management-view-tabs" role="tablist" aria-label="Juhtimisvaate valik">
        {isAdmin && <button type="button" role="tab" aria-selected={view === "DASHBOARD"} className={view === "DASHBOARD" ? "active" : ""} onClick={() => setView("DASHBOARD")}>Organisatsiooni ülevaade</button>}
        {isSalesManager && <button type="button" role="tab" aria-selected={view === "SALES"} className={view === "SALES" ? "active" : ""} onClick={() => setView("SALES")}>Müügijuhtimine</button>}
      </div>
      {view === "DASHBOARD" && isAdmin ? <ManagementDashboard /> : null}
      {view === "SALES" && isSalesManager ? <SalesManagement /> : null}
    </AppShell>
  );
}
