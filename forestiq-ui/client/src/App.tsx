/** ForestIQ Landscape Desk route shell with authorization-aware navigation guards. */
import { Redirect, Route, Switch } from "wouter";
import { lazy, Suspense } from "react";

import { Toaster } from "@/components/ui/sonner";
import { IntegrationsHealthDashboard } from "@/components/IntegrationsHealthDashboard";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "@/components/ErrorBoundary";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { hasAccess, type AccessRequirement } from "@/lib/authorization";
import { AccessDenied, AuthenticationRequired } from "@/pages/AccessState";
import Admin from "@/pages/Admin";
import Dashboard from "@/pages/Dashboard";
import Login from "@/pages/Login";
import InheritanceDetail from "@/pages/InheritanceDetail";
import Messages from "@/pages/Messages";
import NotFound from "@/pages/NotFound";
import OwnerDetail from "@/pages/OwnerDetail";
import Owners from "@/pages/Owners";
import {
  DealsWorkspace,
  InheritanceWorkspace,
  OwnerImportWorkspace,
  SalesWorkspace,
} from "@/pages/ParityWorkspaces";
import Reminders from "@/pages/Reminders";
import { GenericWorkspace, OwnerWorkspace } from "@/pages/Workspaces";

const MapWorkspace = lazy(() => import("@/pages/MapWorkspace"));

type ProtectedProps = {
  children: React.ReactNode;
  requirement?: AccessRequirement;
};

function Protected({ children, requirement }: ProtectedProps) {
  const { user, ready } = useAuth();
  if (!ready)
    return <div className="app-loading">Laadin ForestIQ töölauda…</div>;
  if (!user) return <AuthenticationRequired />;
  if (!hasAccess(user, requirement)) return <AccessDenied />;
  return <>{children}</>;
}

const requirePrivileges = (
  ...anyPrivileges: NonNullable<AccessRequirement["anyPrivileges"]>
): AccessRequirement => ({ anyPrivileges });

function Routes() {
  return (
    <Switch>
      <Route path="/" component={Login} />
      <Route path="/home">
        <Protected>
          <Dashboard />
        </Protected>
      </Route>
      <Route path="/owners">
        <Protected
          requirement={requirePrivileges(
            "ADMIN",
            "OWNER_PROFILE",
            "ASSIGNED_OWNERS",
          )}
        >
          <Owners />
        </Protected>
      </Route>
      <Route path="/owners/import">
        <Protected
          requirement={requirePrivileges(
            "ADMIN",
            "OWNER_PROFILE",
            "ASSIGNED_OWNERS",
          )}
        >
          <OwnerImportWorkspace />
        </Protected>
      </Route>
      <Route path="/owners/:id">
        <Protected
          requirement={requirePrivileges(
            "ADMIN",
            "OWNER_PROFILE",
            "ASSIGNED_OWNERS",
          )}
        >
          <OwnerDetail />
        </Protected>
      </Route>
      <Route path="/map">
        <Protected
          requirement={requirePrivileges(
            "ADMIN",
            "OWNER_PROFILE",
            "ASSIGNED_OWNERS",
            "EVALUATION",
          )}
        >
          <Suspense
            fallback={<div className="app-loading">Laadin kaarditöölauda…</div>}
          >
            <MapWorkspace />
          </Suspense>
        </Protected>
      </Route>
      <Route path="/deals">
        <Protected
          requirement={requirePrivileges(
            "ADMIN",
            "OWNER_PROFILE",
            "EVALUATION",
          )}
        >
          <DealsWorkspace />
        </Protected>
      </Route>
      <Route path="/inheritance/:id">
        <Protected
          requirement={requirePrivileges(
            "ADMIN",
            "OWNER_PROFILE",
            "ASSIGNED_OWNERS",
          )}
        >
          <InheritanceDetail />
        </Protected>
      </Route>
      <Route path="/inheritance">
        <Protected
          requirement={requirePrivileges(
            "ADMIN",
            "OWNER_PROFILE",
            "ASSIGNED_OWNERS",
          )}
        >
          <InheritanceWorkspace />
        </Protected>
      </Route>
      <Route path="/sales">
        <Protected
          requirement={requirePrivileges(
            "ADMIN",
            "OWNER_PROFILE",
            "ASSIGNED_OWNERS",
          )}
        >
          <SalesWorkspace />
        </Protected>
      </Route>
      <Route path="/integrations">
        <Protected requirement={requirePrivileges("ADMIN")}>
          <IntegrationsHealthDashboard />
        </Protected>
      </Route>
      <Route path="/workdesk/caller">
        <Protected requirement={requirePrivileges("ADMIN", "ASSIGNED_OWNERS")}>
          <OwnerWorkspace kind="caller" />
        </Protected>
      </Route>
      <Route path="/workdesk/evaluator">
        <Protected requirement={requirePrivileges("ADMIN", "EVALUATION")}>
          <OwnerWorkspace kind="evaluator" />
        </Protected>
      </Route>
      <Route path="/workdesk/admin">
        <Protected requirement={requirePrivileges("ADMIN")}>
          <OwnerWorkspace kind="admin" />
        </Protected>
      </Route>
      <Route path="/reminders">
        <Protected>
          <Reminders />
        </Protected>
      </Route>
      <Route path="/messages">
        <Protected>
          <Messages />
        </Protected>
      </Route>
      <Route path="/admin">
        <Protected requirement={requirePrivileges("ADMIN")}>
          <Admin />
        </Protected>
      </Route>
      <Route path="/contracts">
        <Protected requirement={requirePrivileges("ADMIN", "OWNER_PROFILE")}>
          <GenericWorkspace kind="contracts" />
        </Protected>
      </Route>
      <Route path="/phones">
        <Protected requirement={requirePrivileges("ADMIN", "PHONES")}>
          <GenericWorkspace kind="phones" />
        </Protected>
      </Route>
      <Route path="/me">
        <Protected>
          <GenericWorkspace kind="me" />
        </Protected>
      </Route>
      <Route path="/reminders-dashboard">
        <Protected>
          <Reminders />
        </Protected>
      </Route>
      <Route>
        <NotFound />
      </Route>
    </Switch>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <TooltipProvider>
          <Routes />
          <Toaster position="bottom-right" />
        </TooltipProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}
