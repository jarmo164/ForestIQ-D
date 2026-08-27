import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  DatabaseZap,
  RefreshCw,
  RotateCcw,
  X,
} from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type {
  IntegrationHealth,
  IntegrationsHealthResponse,
  SyncRun,
} from "@/lib/types";

const statusLabels: Record<string, string> = {
  OK: "TÖÖKORRAS",
  DEGRADED: "VAJAB TÄHELEPANU",
  SUCCESS: "ÕNNESTUS",
  PARTIAL: "OSALINE",
  FAILED: "EBAÕNNESTUS",
  SKIPPED: "VAHELE JÄETUD",
  QUEUED: "JÄRJEKORRAS",
  RUNNING: "TÖÖS",
};

function formatDate(value: string | null | undefined): string {
  if (!value) return "andmed puuduvad";
  return new Intl.DateTimeFormat("et-EE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatDuration(value: number | null): string {
  if (value == null) return "—";
  if (value < 60) return `${Math.round(value)} s`;
  if (value < 3600) return `${Math.round(value / 60)} min`;
  return `${(value / 3600).toFixed(1)} h`;
}

function HealthCard({
  item,
  run,
  onOpenRun,
  onRetry,
  retrying,
}: {
  item: IntegrationHealth;
  run?: SyncRun;
  onOpenRun: (run: SyncRun) => void;
  onRetry: (run: SyncRun) => void;
  retrying: number | null;
}) {
  const degraded = item.health === "DEGRADED";
  const canRetry =
    !!run &&
    (run.status === "PARTIAL" || run.status === "FAILED") &&
    !!run.cadastre;
  return (
    <article className="work-card" aria-label={`${item.source} tervis`}>
      <div className="flex min-w-0 items-start gap-3">
        <span className={`status-pill ${degraded ? "warning" : ""}`}>
          {statusLabels[item.health]}
        </span>
        <div className="min-w-0">
          <h3>{item.source}</h3>
          <p>
            {degraded
              ? "Värskus või viimaste jooksude seis vajab kontrolli."
              : "Viimane auditijooks on värske ja õnnestunud."}
          </p>
        </div>
      </div>
      <dl className="mt-5 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <div>
          <dt className="text-muted-foreground">Viimane edu</dt>
          <dd className="font-medium">{formatDate(item.lastSuccessAt)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Viimane olek</dt>
          <dd className="font-medium">
            {statusLabels[item.lastStatus] || item.lastStatus}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Failure streak</dt>
          <dd className="font-medium">{item.failureStreak}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Järjekord</dt>
          <dd className="font-medium">{item.backlogSize}</dd>
        </div>
        <div className="col-span-2">
          <dt className="text-muted-foreground">Cursor lag</dt>
          <dd className="font-medium">{formatDuration(item.lagSeconds)}</dd>
        </div>
      </dl>
      <div className="mt-5 flex flex-wrap gap-2">
        {run && (
          <button
            className="secondary-action"
            type="button"
            onClick={() => onOpenRun(run)}
          >
            Ava jooksu detail
          </button>
        )}
        {canRetry && (
          <button
            className="secondary-action"
            type="button"
            disabled={retrying === run.id}
            onClick={() => onRetry(run)}
          >
            <RotateCcw size={16} />{" "}
            {retrying === run.id ? "Käivitamine…" : "Käivita recovery"}
          </button>
        )}
      </div>
    </article>
  );
}

function SyncRunDialog({
  run,
  onClose,
}: {
  run: SyncRun;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4"
      role="presentation"
      onMouseDown={onClose}
    >
      <section
        className="panel max-h-[85vh] w-full max-w-2xl overflow-y-auto p-6 shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="sync-run-detail-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-6">
          <div>
            <p className="eyebrow">AUDIT / SÜNKRONISEERIMISJOOKS</p>
            <h2 id="sync-run-detail-title">{run.source}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Jooks #{run.id} · {statusLabels[run.status] || run.status}
            </p>
          </div>
          <button
            className="secondary-action"
            type="button"
            aria-label="Sulge detail"
            onClick={onClose}
          >
            <X size={16} />
          </button>
        </div>
        <dl className="mt-6 grid grid-cols-1 gap-x-6 gap-y-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Alustatud</dt>
            <dd className="font-medium">{formatDate(run.startedAt)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Lõpetatud</dt>
            <dd className="font-medium">{formatDate(run.finishedAt)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Töödeldud lehti / ridu</dt>
            <dd className="font-medium">
              {run.pagesProcessed} / {run.rowsProcessed}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Retry / backlog</dt>
            <dd className="font-medium">
              {run.retryCount} / {run.backlogSize}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Cursor</dt>
            <dd className="break-all font-medium">{run.cursor || "—"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Lag</dt>
            <dd className="font-medium">{formatDuration(run.lagSeconds)}</dd>
          </div>
          {run.correlationId && (
            <div className="sm:col-span-2">
              <dt className="text-muted-foreground">Correlation ID</dt>
              <dd className="break-all font-mono text-xs">
                {run.correlationId}
              </dd>
            </div>
          )}
          {run.error && (
            <div className="sm:col-span-2">
              <dt className="text-muted-foreground">Viga</dt>
              <dd className="mt-1 rounded-md bg-destructive/10 p-3 text-destructive">
                {run.error}
              </dd>
            </div>
          )}
        </dl>
      </section>
    </div>
  );
}

export function IntegrationsHealthDashboard() {
  const [health, setHealth] = useState<IntegrationsHealthResponse | null>(null);
  const [runs, setRuns] = useState<SyncRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<SyncRun | null>(null);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [retrying, setRetrying] = useState<number | null>(null);

  const refresh = async () => {
    setRefreshing(true);
    setError("");
    try {
      const [healthPayload, runPayload] = await Promise.all([
        api.get<IntegrationsHealthResponse>(
          "/services/admin/integrations/health",
        ),
        api.get<{ results: SyncRun[] }>("/services/admin/sync-runs"),
      ]);
      setHealth(healthPayload);
      setRuns(runPayload.results);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Integratsioonide terviseandmeid ei saanud laadida.",
      );
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const latestRunBySource = useMemo(
    () =>
      new Map(
        health?.integrations.map((item) => [
          item.source,
          runs.find((run) => run.source.includes(item.source)),
        ]),
      ),
    [health, runs],
  );
  const recoverStale = async () => {
    setError("");
    try {
      await api.post("/services/registry/freshness/recover", { batchSize: 25 });
      await refresh();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Aegunud andmete taastamist ei saanud käivitada.",
      );
    }
  };
  const retryRun = async (run: SyncRun) => {
    setRetrying(run.id);
    setError("");
    try {
      const queued = await api.post<SyncRun>(
        `/services/admin/sync-runs/${run.id}/retry`,
        {},
      );
      setSelectedRun(queued);
      await refresh();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Sünkroonimisjooksu recovery’t ei saanud käivitada.",
      );
    } finally {
      setRetrying(null);
    }
  };

  const degradedCount = health?.degradedSources.length || 0;
  const totalBacklog =
    health?.integrations.reduce((total, item) => total + item.backlogSize, 0) ||
    0;
  return (
    <AppShell
      title="Integratsioonide ja värskuse haldus"
      eyebrow="HALDUS / ANDMEVOOD"
    >
      <section className="workspace-intro">
        <Activity size={24} />
        <div>
          <h2>Andmete värskus ja integratsioonide tervis</h2>
          <p>
            Seis tuletatakse auditeeritud sünkroonimisjooksudest;
            välisandmeallikaid selles vaates ei probe’ita.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="secondary-action"
            type="button"
            disabled={refreshing}
            onClick={() => void refresh()}
          >
            <RefreshCw size={16} /> Värskenda
          </button>
          <button
            className="secondary-action"
            type="button"
            onClick={() => void recoverStale()}
          >
            <DatabaseZap size={16} /> Taasta aegunud
          </button>
        </div>
      </section>
      {error && (
        <div className="connection-warning" role="alert">
          {error}
        </div>
      )}
      <section
        className="metrics-grid"
        aria-label="Integratsioonide koondnäitajad"
      >
        <div className="metric-card">
          <span>Andmeallikaid</span>
          <strong>{health?.integrations.length ?? "—"}</strong>
        </div>
        <div className="metric-card">
          <span>Vajab tähelepanu</span>
          <strong>{degradedCount}</strong>
        </div>
        <div className="metric-card">
          <span>Järjekorras või töös</span>
          <strong>{totalBacklog}</strong>
        </div>
      </section>
      {!health && !error && (
        <div className="empty-state">
          <Clock3 size={18} /> Laadin integratsioonide terviseandmeid…
        </div>
      )}
      {health?.integrations.length ? (
        <section className="work-card-grid">
          {health.integrations.map((item) => (
            <HealthCard
              key={item.source}
              item={item}
              run={latestRunBySource.get(item.source)}
              onOpenRun={setSelectedRun}
              onRetry={(run) => void retryRun(run)}
              retrying={retrying}
            />
          ))}
        </section>
      ) : (
        health && (
          <div className="empty-state">
            <AlertTriangle size={18} /> Auditeeritud integratsioonijookse ei ole
            veel saadaval.
          </div>
        )
      )}
      {health?.status === "OK" && health.integrations.length > 0 && (
        <p className="mt-5 flex items-center gap-2 text-sm text-emerald-700">
          <CheckCircle2 size={17} /> Kõik auditeeritud integratsioonid on
          värsked.
        </p>
      )}
      {selectedRun && (
        <SyncRunDialog run={selectedRun} onClose={() => setSelectedRun(null)} />
      )}
    </AppShell>
  );
}
