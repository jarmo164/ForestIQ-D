/** ForestIQ Landscape Desk design: authenticated operational context without hidden state. */
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, decodeToken } from "@/lib/api";
import type { AppUser } from "@/lib/types";
type AuthState = { user: AppUser | null; ready: boolean; login: (id: string, password: string, code: string) => Promise<void>; logout: () => void };
const AuthContext = createContext<AuthState | null>(null);
export function AuthProvider({ children }: { children: React.ReactNode }) { const [user, setUser] = useState<AppUser | null>(null); const [ready, setReady] = useState(false); useEffect(() => { setUser(decodeToken(localStorage.getItem("forestiq_access_token") || "")); setReady(true); const handler = () => { api.logout(); setUser(null); }; window.addEventListener("forestiq:unauthorized", handler); return () => window.removeEventListener("forestiq:unauthorized", handler); }, []); const value = useMemo(() => ({ user, ready, login: async (id: string, password: string, code: string) => { const preAuth = await api.passwordLogin(id, password); const nextUser = await api.verifyTotp(preAuth.token, code); setUser(nextUser); }, logout: () => { api.logout(); setUser(null); } }), [user, ready]); return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>; }
export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error("useAuth must be used inside AuthProvider"); return context; }
