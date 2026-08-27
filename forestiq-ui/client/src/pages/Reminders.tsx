/** ForestIQ deadline overview groups work by due date, responsible person and owner. */
import { useEffect, useMemo, useState } from "react";
import { BellRing, CalendarClock, ChevronRight, Clock3, UserRound } from "lucide-react";
import { Link } from "wouter";

import { AppShell } from "@/components/AppShell";
import {
  type ReminderWindow,
  groupRemindersByDeadlineAssigneeAndOwner,
  remindersForWindow,
} from "@/lib/reminderOverview";
import { api } from "@/lib/api";
import type { Reminder } from "@/lib/types";

const windowOptions: { value: ReminderWindow; label: string; description: string }[] = [
  { value: "OVERDUE", label: "Hilinenud", description: "Tähtaeg on möödunud" },
  { value: "NEXT_7_DAYS", label: "7 päeva", description: "Järgmise seitsme päeva tööd" },
  { value: "NEXT_30_DAYS", label: "30 päeva", description: "Järgmise 30 päeva tööd" },
];

function dueTimeLabel(value: number): string {
  return new Date(value).toLocaleTimeString("et-EE", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Reminders() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [window, setWindow] = useState<ReminderWindow>("NEXT_7_DAYS");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    api
      .get<Reminder[]>("/services/reminders")
      .then((records) => {
        if (active) setReminders(records);
      })
      .catch((requestError: Error) => {
        if (active) setError(requestError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const visibleReminders = useMemo(
    () => remindersForWindow(reminders, window),
    [reminders, window],
  );
  const groups = useMemo(
    () => groupRemindersByDeadlineAssigneeAndOwner(visibleReminders),
    [visibleReminders],
  );
  const selectedWindow = windowOptions.find((option) => option.value === window)!;

  return (
    <AppShell title="Tähtaegade ülevaade" eyebrow="FORESTIQ / TÄHTAJAD">
      <section className="reminder-overview-lead">
        <div>
          <p className="eyebrow">TÖÖVOO JUHTIMINE</p>
          <h2>Vaata tegevusi tähtaja, vastutaja ja omaniku järgi.</h2>
          <p>Kasuta ajafiltrit, et hoida järelkõned, kokkulepped ja tähtajad ühes töövaates.</p>
        </div>
        <div className="reminder-overview-count" aria-live="polite">
          <BellRing size={19} />
          <strong>{visibleReminders.length}</strong>
          <span>{selectedWindow.label.toLowerCase()}</span>
        </div>
      </section>

      <section className="reminder-filter-panel" aria-label="Tähtaegade ajavahemik">
        <div>
          <p className="eyebrow">AJAVAHED</p>
          <strong>{selectedWindow.description}</strong>
        </div>
        <div className="reminder-filter-options">
          {windowOptions.map((option) => (
            <button
              type="button"
              key={option.value}
              className={`reminder-filter ${window === option.value ? "active" : ""}`}
              aria-pressed={window === option.value}
              onClick={() => setWindow(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </section>

      {error && <div className="connection-warning">Meeldetuletuste laadimine ebaõnnestus: {error}</div>}
      {loading && <div className="empty-state">Laadin tähtaegade ülevaadet…</div>}

      {!loading && !error && (
        <section className="deadline-groups" aria-label="Rühmitatud tähtajad">
          {groups.map((deadline) => (
            <article className="deadline-group" key={deadline.dateKey}>
              <header className="deadline-group-heading">
                <div>
                  <p className="eyebrow">TÄHTAEG</p>
                  <h3><CalendarClock size={18} /> {deadline.dateLabel}</h3>
                </div>
                <span>{deadline.assignees.reduce((total, assignee) => total + assignee.owners.reduce((ownerTotal, owner) => ownerTotal + owner.reminders.length, 0), 0)} tegevust</span>
              </header>

              {deadline.assignees.map((assignee) => (
                <section className="assignee-group" key={`${deadline.dateKey}-${assignee.assigneeId}`}>
                  <div className="assignee-heading">
                    <UserRound size={15} />
                    <span>Vastutaja</span>
                    <strong>{assignee.assigneeName}</strong>
                  </div>
                  {assignee.owners.map((owner) => (
                    <div className="reminder-owner-group" key={`${assignee.assigneeId}-${owner.ownerId}`}>
                      <div className="reminder-owner-heading">
                        <div>
                          <span>Omanik</span>
                          {owner.ownerId === "no-owner" ? (
                            <strong>{owner.ownerName}</strong>
                          ) : (
                            <Link href={`/owners/${owner.ownerId}`}>{owner.ownerName}<ChevronRight size={14} /></Link>
                          )}
                        </div>
                        <small>{owner.reminders.length} {owner.reminders.length === 1 ? "tegevus" : "tegevust"}</small>
                      </div>
                      <div className="reminder-task-list">
                        {owner.reminders.map((reminder) => (
                          <div className="reminder-task" key={reminder.id}>
                            <Clock3 size={15} />
                            <div>
                              <strong>{reminder.text || "Kirjelduseta meeldetuletus"}</strong>
                              <small>{dueTimeLabel(reminder.dueTime)}{reminder.propertyName ? ` · ${reminder.propertyName}` : ""}{reminder.cadastre ? ` · ${reminder.cadastre}` : ""}</small>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </section>
              ))}
            </article>
          ))}
          {!groups.length && (
            <div className="empty-state">Selles ajavahemikus ei ole ühtegi meeldetuletust.</div>
          )}
        </section>
      )}
    </AppShell>
  );
}
