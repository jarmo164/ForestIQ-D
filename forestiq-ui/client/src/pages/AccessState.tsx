import { Link } from "wouter";

export function AuthenticationRequired() {
  return (
    <main className="access-state" aria-labelledby="authentication-required-title">
      <p className="eyebrow">FORESTIQ / SISSELUGIMINE</p>
      <h1 id="authentication-required-title">Sisselogimine on vajalik</h1>
      <p>See tööruum vajab kehtivat ForestIQ seanssi. Sisene jätkamiseks oma kontoga.</p>
      <Link href="/" className="access-state-action">Ava sisselogimine</Link>
    </main>
  );
}

export function AccessDenied() {
  return (
    <main className="access-state" aria-labelledby="access-denied-title">
      <p className="eyebrow">FORESTIQ / ÕIGUSED</p>
      <h1 id="access-denied-title">403 — puudub ligipääsuõigus</h1>
      <p>Sinu aktiivsel rollil ei ole sellele tööruumile õigust. Keelatud lehe andmeid ei ole laaditud.</p>
      <Link href="/home" className="access-state-action">Tagasi töölauale</Link>
    </main>
  );
}
