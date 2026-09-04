import { FormEvent, useState } from "react";
import { KeyRound, LogOut, ShieldCheck } from "lucide-react";
import { useLocation } from "wouter";

import { AppShell } from "@/components/AppShell";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";

export default function Account() {
  const { user, oidc, logout } = useAuth();
  const [, navigate] = useLocation();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordAgain, setNewPasswordAgain] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function changePassword(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await api.post("/services/change-my-password", { oldPassword, newPassword, newPasswordAgain });
      setOldPassword("");
      setNewPassword("");
      setNewPasswordAgain("");
      setMessage("Parool on muudetud. Uue Keycloak-seansi puhul halda parooli identiteediteenuses.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Parooli muutmine ebaõnnestus.");
    } finally {
      setBusy(false);
    }
  }

  function signOut() {
    logout();
    navigate("/");
  }

  return (
    <AppShell title="Minu konto" eyebrow="FORESTIQ / KASUTAJA">
      <section className="workspace-intro">
        <ShieldCheck size={24} />
        <div>
          <h2>Rollid, organisatsioon ja turvaseansi toimingud.</h2>
          <p>Kontoandmed pärinevad sisselogimisel väljastatud organisatsioonipõhisest tokenist.</p>
        </div>
      </section>

      {error && <div className="connection-warning">{error}</div>}
      {message && <div className="connection-warning">{message}</div>}

      <section className="table-panel generic-records">
        <h3>{user?.name || user?.id}</h3>
        <p>Kasutaja ID: {user?.id}</p>
        <p>Organisatsioon: {user?.organizationId || "—"}</p>
        <p>Rollid: {user?.roles?.length ? user.roles.join(", ") : "—"}</p>
        <p>Õigused: {user?.privileges?.length ? user.privileges.join(", ") : "—"}</p>
        <p>Autentimine: {oidc?.enabled ? "Keycloak OIDC" : "lokaalne arenduslogin"}</p>
        <button type="button" onClick={signOut}><LogOut size={16} /> Logi välja</button>
      </section>

      {!oidc?.enabled && (
        <section className="table-panel">
          <div className="table-toolbar"><KeyRound size={16} /> Muuda lokaalset parooli</div>
          <form className="generic-records" onSubmit={changePassword}>
            <label>Praegune parool<input type="password" value={oldPassword} onChange={(event) => setOldPassword(event.target.value)} /></label>
            <label>Uus parool<input type="password" minLength={12} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /></label>
            <label>Uus parool uuesti<input type="password" minLength={12} value={newPasswordAgain} onChange={(event) => setNewPasswordAgain(event.target.value)} /></label>
            <button type="submit" disabled={busy}>{busy ? "Muudan…" : "Muuda parool"}</button>
          </form>
        </section>
      )}
    </AppShell>
  );
}
