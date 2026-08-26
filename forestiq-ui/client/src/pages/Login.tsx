/** ForestIQ Landscape Desk authentication entry point. */
import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { ArrowRight, KeyRound, LockKeyhole, MapPinned, ScanLine, ShieldCheck, UserRound } from "lucide-react";

import { ForestMark } from "@/components/ForestMark";
import { useAuth } from "@/contexts/AuthContext";
import "./login.css";

export default function Login() {
  const { completeOidcLogin, login, oidc, ready, startOidcLogin } = useAuth();
  const [, setLocation] = useLocation();
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const authorizationCode = query.get("code");
    const state = query.get("state");
    const providerError = query.get("error_description") || query.get("error");
    if (providerError) {
      setError(`Keycloak’i sisselogimine katkestati: ${providerError}`);
      window.history.replaceState({}, document.title, window.location.pathname);
      return;
    }
    if (!authorizationCode || !state) return;

    setLoading(true);
    completeOidcLogin(authorizationCode, state)
      .then(() => {
        window.history.replaceState({}, document.title, window.location.pathname);
        setLocation("/home");
      })
      .catch((reason) => {
        setError(reason instanceof Error ? reason.message : "Keycloak’i sisselogimine ebaõnnestus.");
        window.history.replaceState({}, document.title, window.location.pathname);
      })
      .finally(() => setLoading(false));
  }, [completeOidcLogin, setLocation]);

  const submitLocalLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(userId, password, code);
      setLocation("/home");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sisselogimine ebaõnnestus.");
    } finally {
      setLoading(false);
    }
  };

  const submitOidcLogin = async () => {
    setLoading(true);
    setError("");
    try {
      await startOidcLogin();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Keycloak’i sisselogimist ei saanud alustada.");
      setLoading(false);
    }
  };

  const showLocalLogin = Boolean(oidc?.localLoginEnabled);
  const showOidcLogin = Boolean(oidc?.enabled);

  return (
    <div className="login-page">
      <div
        className="login-art"
        style={{
          backgroundImage:
            "linear-gradient(90deg, rgba(11,42,34,.94) 0%, rgba(11,42,34,.68) 44%, rgba(11,42,34,.12) 100%), url('/manus-storage/forestiq-topographic-workspace_6494ef7a.jpg')",
        }}
      >
        <div className="login-copy">
          <div className="login-brand">
            <span className="mark-orbit"><ForestMark size={62} /></span>
            <span><strong>Forest</strong><em>IQ</em></span>
          </div>
          <p className="eyebrow">METSAANDMETE OPERATSIOONID</p>
          <h1>Näe metsa.<br /><i>Juhi järgmist sammu.</i></h1>
          <p>Üks tööpind omanike, kinnistute, hindamiste ja otsuste jaoks.</p>
          <div className="login-map-readout">
            <span><MapPinned size={14} /> Katastri kontekst</span>
            <span><ScanLine size={14} /> Otsuste töövoog</span>
          </div>
          <div className="login-note"><span /> Turvaline töölaud metsaostu meeskonnale</div>
        </div>
      </div>
      <section className="login-form-wrap">
        <div className="contour-field contour-one" />
        <div className="contour-field contour-two" />
        <div className="entry-coordinates">58° 35′ N&nbsp;&nbsp;•&nbsp;&nbsp;25° 01′ E</div>
        <div className="login-form">
          <p className="eyebrow">TURVALINE TÖÖALA</p>
          <h2>Ava oma otsustetöölaud.</h2>
          <p className="form-intro">Tuvasta ennast, et jätkata omanike, kinnistute ja järgnevate tegevuste töövooga.</p>
          <div className="workspace-key"><span><i /> Mets — aktiivne tööala</span><span><i /> Kinnistu — ruumiline kontekst</span></div>
          {error && <div className="form-error">{error}</div>}
          {!ready && <p className="form-footnote">Kontrollin sisselogimisseadistust…</p>}
          {ready && showOidcLogin && (
            <button type="button" className="primary-action" onClick={submitOidcLogin} disabled={loading}>
              <ShieldCheck size={18} />
              {loading ? "Suunamine Keycloak’i…" : "Sisene Keycloakiga"}
              <ArrowRight size={18} />
            </button>
          )}
          {ready && showLocalLogin && (
            <form onSubmit={submitLocalLogin}>
              {showOidcLogin && <p className="form-footnote">Või kasuta ainult arenduseks mõeldud kohalikku kontot.</p>}
              <label><span><UserRound size={15} /> Kasutajatunnus</span><input value={userId} onChange={(event) => setUserId(event.target.value)} autoComplete="username" required /></label>
              <label><span><LockKeyhole size={15} /> Parool</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /></label>
              <label><span><KeyRound size={15} /> TOTP turvakood</span><input inputMode="numeric" value={code} onChange={(event) => setCode(event.target.value)} placeholder="000000" required /></label>
              <button className="primary-action" disabled={loading}>
                {loading ? "Kontrollin…" : "Ava arendustöölaud"}
                <ArrowRight size={18} />
              </button>
              <p className="form-footnote">Arenduskeskkonna konto kasutab koodi <strong>000000</strong>.</p>
            </form>
          )}
          {ready && !showOidcLogin && !showLocalLogin && <p className="form-error">Sisselogimine ei ole selles keskkonnas seadistatud.</p>}
        </div>
      </section>
    </div>
  );
}
