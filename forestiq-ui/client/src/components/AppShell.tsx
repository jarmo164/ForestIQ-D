/** ForestIQ Landscape Desk design: fixed dark spruce navigation and a spacious operational surface. */
import { BadgeEuro, BarChart3, Bell, BookOpenText, ChevronRight, ClipboardList, Compass, FileText, Gauge, Gavel, LayoutDashboard, LogOut, MapPinned, MessagesSquare, Phone, Settings2, UsersRound, type LucideIcon } from "lucide-react";
import { Link, useLocation } from "wouter";

import { useAuth } from "@/contexts/AuthContext";
import { hasAccess, navigationItems } from "@/lib/authorization";

import { ForestMark } from "./ForestMark";

const navigationIcons: Record<string, LucideIcon> = {
  "/home": LayoutDashboard,
  "/owners": UsersRound,
  "/sales": ClipboardList,
  "/deals": BadgeEuro,
  "/inheritance": Gavel,
  "/map": MapPinned,
  "/workdesk/evaluator": Compass,
  "/reminders": Bell,
  "/messages": MessagesSquare,
  "/contracts": FileText,
  "/phones": Phone,
  "/owners/import": FileText,
  "/integrations": Gauge,
  "/management": BarChart3,
  "/admin": Settings2,
} as const;

export function AppShell({ children, title, eyebrow }: { children: React.ReactNode; title: string; eyebrow?: string }) {
  const [location] = useLocation();
  const { user, logout } = useAuth();
  const visibleNavigation = navigationItems.filter((item) => hasAccess(user, item.requirement));

  return <div className="app-frame"><aside className="sidebar"><Link href="/home" className="brand"><ForestMark size={42} /><span><strong>Forest</strong><em>IQ</em><small>maastiku töölaud</small></span></Link><nav>{visibleNavigation.map(({ label, href }) => { const Icon = navigationIcons[href]; return <Link key={href} href={href} className={`nav-link ${location.startsWith(href) ? "active" : ""}`}><Icon size={18} /><span>{label}</span><ChevronRight size={14} /></Link>; })}</nav><div className="sidebar-foot"><div className="user-card"><div className="avatar">{user?.name?.slice(0, 1) || "?"}</div><div><strong>{user?.name || "Kasutaja"}</strong><span>{user?.id}</span></div></div><button className="logout" onClick={logout}><LogOut size={16} /> Välju</button></div></aside><main className="main-surface"><header className="topbar"><div><p className="eyebrow">{eyebrow || "FORESTIQ / OPERATSIOONID"}</p><h1>{title}</h1></div><div className="topbar-actions"><div className="sync-dot"><span /> API ühendus</div><Link href="/me" className="profile-link"><BookOpenText size={17} /> Minu konto</Link></div></header><div className="page-content">{children}</div></main></div>;
}
