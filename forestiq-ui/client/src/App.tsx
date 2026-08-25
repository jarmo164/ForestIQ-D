/** ForestIQ Landscape Desk design: route shell prioritizes operational access and API-authenticated flows. */
import { Route, Switch, Redirect } from "wouter";
import { lazy, Suspense } from "react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "@/components/ErrorBoundary";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Owners from "@/pages/Owners";
import OwnerDetail from "@/pages/OwnerDetail";
import Reminders from "@/pages/Reminders";
import Messages from "@/pages/Messages";
import Admin from "@/pages/Admin";
import { GenericWorkspace, OwnerWorkspace } from "@/pages/Workspaces";

const MapWorkspace = lazy(() => import("@/pages/MapWorkspace"));

function Protected({ children }: { children: React.ReactNode }) { const { user, ready } = useAuth(); if (!ready) return <div className="app-loading">Laadin ForestIQ töölauda…</div>; return user ? <>{children}</> : <Redirect to="/" />; }
function Routes() { return <Switch><Route path="/" component={Login} /><Route path="/home"><Protected><Dashboard /></Protected></Route><Route path="/owners"><Protected><Owners /></Protected></Route><Route path="/owners/:id"><Protected><OwnerDetail /></Protected></Route><Route path="/map"><Protected><Suspense fallback={<div className="app-loading">Laadin kaarditöölauda…</div>}><MapWorkspace /></Suspense></Protected></Route><Route path="/workdesk/caller"><Protected><OwnerWorkspace kind="caller" /></Protected></Route><Route path="/workdesk/evaluator"><Protected><OwnerWorkspace kind="evaluator" /></Protected></Route><Route path="/workdesk/admin"><Protected><OwnerWorkspace kind="admin" /></Protected></Route><Route path="/reminders"><Protected><Reminders /></Protected></Route><Route path="/messages"><Protected><Messages /></Protected></Route><Route path="/admin"><Protected><Admin /></Protected></Route><Route path="/contracts"><Protected><GenericWorkspace kind="contracts" /></Protected></Route><Route path="/phones"><Protected><GenericWorkspace kind="phones" /></Protected></Route><Route path="/me"><Protected><GenericWorkspace kind="me" /></Protected></Route><Route path="/reminders-dashboard"><Protected><Reminders /></Protected></Route><Route><Redirect to="/home" /></Route></Switch>; }
export default function App() { return <ErrorBoundary><AuthProvider><TooltipProvider><Routes /><Toaster position="bottom-right" /></TooltipProvider></AuthProvider></ErrorBoundary>; }
