/** ForestIQ inbox combines direct messages with realtime application notifications. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Archive, BellRing, MailOpen, MessageSquareText, Send } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { api, realtimeWebSocketUrl } from "@/lib/api";
import type { Message } from "@/lib/types";

type ApplicationMessage = {
  id: number;
  text: string;
  category?: string | null;
  createdAt: number;
  readAt?: number | null;
  archivedAt?: number | null;
};
type ApplicationMessagePage = { items: ApplicationMessage[]; unreadCount: number };
type RealtimeEnvelope = {
  eventId: string;
  eventType: string;
  payload: { unreadCount?: number; [key: string]: unknown };
};

export default function Messages() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [applicationMessages, setApplicationMessages] = useState<ApplicationMessage[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [error, setError] = useState("");
  const seenEvents = useRef(new Set<string>());

  const loadApplicationMessages = useCallback(async () => {
    const page = await api.get<ApplicationMessagePage>("/services/application-messages");
    setApplicationMessages(page.items);
    setUnreadCount(page.unreadCount);
  }, []);

  useEffect(() => {
    api.get<Message[]>("/services/messages/received?page=0&size=50").then(setMessages).catch((err) => setError(err.message));
    void loadApplicationMessages().catch((err: Error) => setError(err.message));
  }, [loadApplicationMessages]);

  useEffect(() => {
    let active = true;
    let socket: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let retry = 0;

    const connect = () => {
      const url = realtimeWebSocketUrl();
      if (!url || !active) return;
      socket = new WebSocket(url);
      socket.onopen = () => { retry = 0; };
      socket.onmessage = (event) => {
        try {
          const envelope = JSON.parse(event.data) as RealtimeEnvelope;
          if (!envelope.eventId || seenEvents.current.has(envelope.eventId)) return;
          seenEvents.current.add(envelope.eventId);
          if (seenEvents.current.size > 500) {
            const oldest = seenEvents.current.values().next().value as string | undefined;
            if (oldest) seenEvents.current.delete(oldest);
          }
          if (envelope.eventType === "APPLICATION_MESSAGE" || envelope.eventType === "APPLICATION_MESSAGE_COUNT") {
            if (typeof envelope.payload.unreadCount === "number") setUnreadCount(envelope.payload.unreadCount);
            void loadApplicationMessages();
          }
        } catch {
          // Ignore malformed transport frames; HTTP remains the source of truth.
        }
      };
      socket.onclose = () => {
        if (!active) return;
        const delay = Math.min(1000 * 2 ** retry, 15000);
        retry += 1;
        timer = setTimeout(connect, delay);
      };
    };
    connect();
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
      socket?.close();
    };
  }, [loadApplicationMessages]);

  const markRead = async (id: number) => {
    await api.patch(`/services/application-messages/${id}`, { operation: "READ" });
    await loadApplicationMessages();
  };
  const archive = async (id: number) => {
    await api.patch(`/services/application-messages/${id}`, { operation: "ARCHIVE" });
    await loadApplicationMessages();
  };

  return (
    <AppShell title="Sõnumid" eyebrow="FORESTIQ / POSTKAST">
      <section className="mb-5 rounded-2xl border border-border bg-card p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2"><BellRing size={18} /><strong>Rakendusteavitused</strong></div>
          <span className="status-pill">{unreadCount} lugemata</span>
        </div>
        <div className="space-y-2">
          {applicationMessages.map((message) => (
            <article className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border p-3" key={message.id}>
              <button className="min-w-0 flex-1 text-left" onClick={() => void markRead(message.id)}>
                <strong>{message.category || "Süsteem"}</strong>
                <p className="truncate text-sm">{message.text}</p>
                <small>{new Date(message.createdAt).toLocaleString("et-EE")}</small>
              </button>
              <div className="flex items-center gap-2">
                {!message.readAt && <span className="status-pill warning">UUS</span>}
                <button className="secondary-action" onClick={() => void archive(message.id)}><Archive size={14} /> Arhiveeri</button>
              </div>
            </article>
          ))}
          {!applicationMessages.length && <div className="empty-state">Rakendusteavitusi ei ole.</div>}
        </div>
      </section>

      <section className="message-layout">
        <aside>
          <div className="inbox-label"><MailOpen size={17} /> Saabunud</div>
          {messages.map((message) => (
            <button className="message-preview" key={message.id}>
              <strong>{message.sender?.name || message.sender?.id || "Süsteem"}</strong>
              <span>{message.message}</span>
              <small>{new Date(message.createdAt).toLocaleDateString("et-EE")}</small>
            </button>
          ))}
          {!messages.length && <div className="empty-state">Saabunud sõnumeid ei ole.</div>}
        </aside>
        <article className="message-empty">
          <MessageSquareText size={36} /><h2>Vali sõnum</h2>
          <p>Rakendussõnumid ja meeskonna teated püsivad samas turvatud töövoos.</p>
          <button className="secondary-action"><Send size={16} /> Koosta sõnum</button>
          {error && <div className="connection-warning">{error}</div>}
        </article>
      </section>
    </AppShell>
  );
}
