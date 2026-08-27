# Katvuse ja tarneahela turvalisuse kvaliteedivärav

**Autor:** Manus AI

**Kehtivus:** QA-05

**Seis:** rakendatud

## Eesmärk

ForestIQ-D pull request ei tohi ühineda, kui kriitiliste õiguste, tervise- või sünkroonimiskooditeede testikate langeb alla kinnitatud läve, sõltuvusraportis esineb heaks kiitmata haavatavus või Git-ajaloost leitakse saladus. Need kontrollid on osa kohustuslikust **All quality checks passed** koondväravast.

| Valdkond | Kriitiline ulatus | Merge’i blokeeriv lävi | Käsk |
| --- | --- | ---: | --- |
| Frontend | `authorization.ts`, `AccessState.tsx` | read 85%, laused 85%, harud 85%, funktsioonid 70% | `pnpm test:coverage:critical` |
| Backend | health, Redis single-flight, MVT cache, WFS klient, Metsaregistri import ja Celery sünkroonimistööd | koondkatvus 60% | `bash scripts/run_backend_critical_coverage.sh` |

Frontendi lävendid põhinevad praegusel kriitiliste moodulite mõõtmisel; eraldi `test:e2e` jääb funktsionaalseks kasutajateekonna kontrolliks. Backend’i käsk kasutab Quality Gate’i päris PostGIS-i ja Redise teenuseid ning väljastab XML-raporti `coverage/backend-critical.xml`.

## Sõltuvuste ja saladuste skaneerimine

Turvatöö kasutab eraldi Quality Gate’i tööd. Pythoni nõudeid kontrollitakse `pip-audit` abil ning iga teadaolev advisory on vaikimisi merge’i blokeeriv. Frontendi audit loeb `pnpm audit --json` raportit ja blokeerib `high` ning `critical` raskusastme advisories. Gitleaks kontrollib täielikku Git-ajalugu ning ei kasuta üldisi regexi-, tee- ega commit-allowlist’e.

> Auditiskannerid tuvastavad teadaolevaid advisories’e ja potentsiaalseid saladusi; need ei asenda sõltuvuste õigeaegset uuendamist, koodiarvustust ega tootmiskeskkonna saladuste haldust.

## Ajutised erandid

Fail `security-exceptions.json` on ainsaks ajutiste sõltuvusauditi erandite registriks. Enne skaneerimist valideerib kvaliteedivärav selle `scripts/validate_security_exceptions.py` abil. Iga kirje peab sisaldama järgmist teavet.

```json
{
  "id": "GHSA-xxxx-xxxx-xxxx",
  "scanner": "pnpm-audit",
  "reference": "#123",
  "rationale": "Vähemalt 20 tähemärki selgitust riskist ja parandusteest.",
  "expires_on": "YYYY-MM-DD"
}
```

Kirje `scanner` võib olla `pip-audit`, `pnpm-audit` või `gitleaks`. Erand peab viitama GitHubi issue’le või HTTPS allikale, sisaldama sisulist põhjendust ja aeguma maksimaalselt 90 päeva pärast lisamist. Aegunud, dubleeritud või vigase vormiga kirje katkestab merge’i. Gitleaksi tegelik leid tuleb esmalt eemaldada või roteerida; erandiregister dokumenteerib otsuse ja selle aegumise, kuid ei tohi muuta saladuste skaneerijat üldise allowlist’i abil pimedaks.

## Kohalik kontroll

```bash
python scripts/validate_security_exceptions.py security-exceptions.json
pip-audit --strict --requirement requirements.txt
bash scripts/run_backend_critical_coverage.sh
cd forestiq-ui
pnpm test:coverage:critical
pnpm audit --json
```

Sõltuvuse parandamine on alati eelistatud erandile. Kui parandust ei ole võimalik kohe kasutada, tuleb luua jälgitav issue, lisada võimalikult kitsas erand ning eemaldada see enne aegumiskuupäeva.
