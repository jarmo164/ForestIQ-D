import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api, decodeToken, type OidcConfiguration } from "@/lib/api";
import type { AppUser } from "@/lib/types";

type AuthState = {
  user: AppUser | null;
  ready: boolean;
  oidc: OidcConfiguration | null;
  login: (id: string, password: string, code: string) => Promise<void>;
  startOidcLogin: () => Promise<void>;
  completeOidcLogin: (code: string, state: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [oidc, setOidc] = useState<OidcConfiguration | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    setUser(decodeToken(localStorage.getItem("forestiq_access_token") || ""));
    api
      .oidcConfiguration()
      .then((config) => {
        if (active) setOidc(config);
      })
      .catch(() => {
        if (active) setOidc({ enabled: false, localLoginEnabled: false });
      })
      .finally(() => {
        if (active) setReady(true);
      });
    const handler = () => {
      api.logout();
      setUser(null);
    };
    window.addEventListener("forestiq:unauthorized", handler);
    return () => {
      active = false;
      window.removeEventListener("forestiq:unauthorized", handler);
    };
  }, []);

  const value = useMemo(
    () => ({
      user,
      ready,
      oidc,
      login: async (id: string, password: string, code: string) => {
        const preAuth = await api.passwordLogin(id, password);
        const nextUser = await api.verifyTotp(preAuth.token, code);
        setUser(nextUser);
      },
      startOidcLogin: async () => {
        if (!oidc) throw new Error("Sisselogimisseadistus ei ole veel saadaval.");
        await api.startOidcLogin(oidc);
      },
      completeOidcLogin: async (code: string, state: string) => {
        const nextUser = await api.completeOidcLogin(code, state);
        setUser(nextUser);
      },
      logout: () => {
        api.logout();
        setUser(null);
      },
    }),
    [oidc, ready, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
