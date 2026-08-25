# ForestIQ

ForestIQ on metsaostjate töölaud. Haru `rewrite` server on ümber ehitatud **Python 3.12, Django, Django REST Frameworki ning PostgreSQL/PostGIS-i** peale; kasutajaliides on **React 19, TypeScripti, Vite’i ja MapLibre’i** peal. Uus kasutajaliides säilitab Django `api/` ja `api/services/` lepingud, JWT/TOTP sisselogimise ning metsaomanike töövood.

## Uus arhitektuur

| Kiht | Tehnoloogia | Vastutus |
|---|---|---|
| Kasutajaliides | React 19 + TypeScript + Vite | Metsaomanike, katastri, töölaudade, sõnumite, meeldetuletuste ja halduse operatiivne töölaud |
| API | Django + Django REST Framework | REST liides, domeeniloogika, õigused ja JWT autentimine |
| Andmebaas | PostgreSQL 16 + PostGIS 3.4 | Omanikud, katastriüksused, ruumiandmed, töölogid, sõnumid, lepingud ja muu püsiv domeeniinfo |
| Tausttööd | Celery + Redis + Celery Beat | Auditiga WFS-i, metsaregistri ja volitatud välisallikate sünkroniseerimine |
| Kaart | GeoDjango + MapLibre | Geomeetria valideerimine, PostGIS-i ristumispäringud ja interaktiivsed GeoJSON-kihid |
| Käitus | Docker Compose + Gunicorn + Nginx | Korratav kasutajaliidese, API, workeri ja andmebaasi ühtne käivitus |

Django rakendused on jagatud selgete domeenipiiridega: `accounts` haldab identiteeti ja õigusi, `forestry` metsaomanike ning katastri domeeni, `operations` meeldetuletusi, sõnumeid ja lepinguid ning `api` säilitab REST-liidese ühilduvuse.

## Main-haru funktsioonide pariteet

Django ümberkirjutus sisaldab nüüd lisaks omaniku-, katastri- ja kaartetöövoole kommertstehinguid, hindamist, pakkumiste revisjone, võidu/kaotuse olekuid ning võidetud tehingust lepingu drafti loomist. Pärimisjuhtum sisaldab ametliku teate kontrolli, juhtumi staatust, määramist, pärijate andmeid ja auditeeritud sündmusi. Kõik toimingud rakendavad olemasolevat ForestIQ õigust ning jätavad omaniku või juhtumi tööajalukku kirje.

| Töövoog | Reacti vaade | Olulised Django API-teed |
|---|---|---|
| Tehing ja hindamine | Omanikukaart ning `/deals` | `/services/deals/*`, `/services/contracts/deals/{id}/draft` |
| Pärimisjuhtum | Omanikukaart ning `/inheritance` | `/services/inheritance/*` |
| Omanike import | `/owners/import` | `/services/owners/imports/inspect`, `preview`, `commit` |
| Müügitöö | `/sales` | `/services/sales-workspace/*` |
| Integratsioonid ja värskus | `/integrations` | `/services/admin/integrations/*`, `/services/registry/*` |

Omanike import toetab UTF-8 CSV- ja XLSX-faile. Fail kontrollitakse enne salvestamist, nõuab eelvaate SHA-256 kinnitust ning jätab vigaste ridade loendi auditeeritud impordipartiisse. Välisteenuste tööriistad jäävad opt-in põhimõttele: tegelik Foresteki või Pärimuse päring käivitub alles siis, kui vajalik URL ja vähimate õigustega token on keskkonnas seadistatud. Täielik moodulite võrdlus on failis [`docs/MAIN_FUNCTIONAL_PARITY.md`](docs/MAIN_FUNCTIONAL_PARITY.md).

## Lokaalne käivitus

Kopeeri keskkonnamuutujad ning vali arenduseks pikk juhuslik saladus.

```sh
cp .env.example .env
# muuda vähemalt DJANGO_SECRET_KEY ja POSTGRES_PASSWORD
```

Käivita PostGIS, Redis, Django API, Celery worker ja Celery Beat.

```sh
docker compose -f docker-compose-full-stack.yml up --build db redis api worker beat
```

API seisukorda saab kontrollida aadressilt `http://localhost:8000/api/services/status`. Täisstack käivitab Reacti töölauda pordil 80 ning Nginx suunab selle `/api/` päringud samal domeenil Django API-le.

```sh
docker compose -f docker-compose-full-stack.yml up --build
```

Reacti kasutajaliidest saab arendada eraldi järgmiselt. Vite puhverserver suunab arenduses `/api/` päringud vaikimisi aadressile `http://127.0.0.1:8000`; vajadusel saab sihtaadressi määrata muutujaga `VITE_API_PROXY_TARGET`.

```sh
cd forestiq-ui
pnpm install --frozen-lockfile
pnpm dev
```

Arenduskeskkonnas loob käivitus `autocreated` administraatori. Kasutajanimi ja parool on mõlemad `autocreated`; see konto tuleb enne mis tahes pärisandmete kasutamist asendada või eemaldada.

## WFS ja registriandmete värskendamine

Maa- ja Ruumiameti katastri WFS ning metsaregistri WFS on seadistatud vaikimisi avalikeks allikateks. Celery worker värskendab need katastriüksuse kaupa ning säilitab iga käivituse auditi mudelis `DataSyncRun`; Celery Beat paneb portfelli sünkroniseerimise iga 24 tunni järel automaatselt järjekorda. Arenduses saab intervalli muuta muutujaga `FORESTIQ_PORTFOLIO_SYNC_INTERVAL_SECONDS`.

Üksikut katastriüksust saab värskendada administraatori API kaudu (`POST /api/services/admin/cadastres/{id}/sync`). Foresteki omaniku-katastri seosed, SOOS-i WFS ja Pärimuse päringud on tahtlikult opt-in: need käivituvad alles siis, kui nende teenuse URL ja eraldi vähimate õigustega token on `.env` failis seadistatud. Täpne andmevoog, auditeerimine ja migratsioonisammud on failis [`docs/DJANGO_REWRITE_ARCHITECTURE.md`](docs/DJANGO_REWRITE_ARCHITECTURE.md).

### Käsitsi impordiskriptid

Käsud käivitavad importimise samas protsessis ning loovad iga tegelikult töödeldud katastriüksuse kohta `DataSyncRun` auditirea. Alusta alati kuivkäivitusega; see kontrollib konfiguratsiooni ja valitud ulatust, kuid **ei tee välispäringuid ega kirjuta andmebaasi**.

```sh
cd django_backend

# Avalikud WFS-i allikad: katastriüksus, metsaregister ning seadistatud SOOS.
python manage.py import_wfs_sources --cadastre 79501:001:0001 --source all --dry-run
python manage.py import_wfs_sources --cadastre 79501:001:0001 --source cadastre
python manage.py import_wfs_sources --all --source metsaregister --limit 50 --continue-on-error

# Volitatud API-allikad: enne on vaja seadistada FORESTEK_API_URL/TOKEN või PARIMUS_API_URL/TOKEN.
python manage.py import_external_api_sources --cadastre 79501:001:0001 --source forestek --dry-run
python manage.py import_external_api_sources --all --source parimus --limit 25 --continue-on-error
```

`import_wfs_sources` toetab allikaid `cadastre`, `metsaregister`, `soos` ja `all`. Valiku `all` korral jäetakse seadistamata SOOS teadlikult vahele; eraldi `--source soos` nõuab selle URL-i ja kihi seadistust. `import_external_api_sources` toetab `forestek`, `parimus` ja `all`; ükski volitatud API-päring ei käivitu enne URL-i ning tokeni eelkontrolli läbimist. Tõrked talletatakse auditireal ning `--continue-on-error` lubab töödelda järgmisi üksusi.

**Forestek on ühekordne algimport.** Käivita `import_external_api_sources --all --source forestek` ainult pärast Foresteki URL-i ja tokeni seadistamist ning enne esimese eduka Foresteki impordi tekkimist. Pärast esimest edukat importi keeldub käsk kordusest. Forestek on eemaldatud Celery Beat’i ajakavast, tavapärasest katastri-/metsaregistri värskendusest ja integratsioonide käivitus-API-st; jätkuvad andmeuuendused tulevad metsaregistri WFS-i eraldiste ning teatiste voost.

### Metsaregistri esmane täisimport ja uued teatised

Kui metsaregister on põhiandmeallikas, käivita esmalt täisimport. Käsk loeb `FORESTIQ_METSAREGISTER_FULL_WFS_LAYER` kihist kõik eraldised lehekülgede kaupa. Iga eraldis salvestatakse `CadastreSubPart`-ina; ainult juhul, kui kombinatsiooni **katastriüksus + eraldise number** veel andmebaasis ei ole, tehakse teatiste kihile sihitud CQL-päring. Juba olemasolevate eraldiste teatisi ei laadita selle käsuga uuesti.

```sh
cd django_backend

# Kontrollib seadistuse ja kavandatud voo, kuid ei tee WFS-päringuid.
python manage.py import_metsaregister_full --dry-run

# Esmane täielik eraldiste import ning uute eraldiste teatised.
python manage.py import_metsaregister_full --page-size 1000

# Ainult eraldiste täisimport, kui teatiste kiht ei ole veel seadistatud.
python manage.py import_metsaregister_full --without-notifications
```

Teatiste automaatseks järelpäringuks seadista lisaks metsaregistri URL-ile ja eraldiste kihile `FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER`. Vajadusel saab CQL-väljade nimed määrata muutujatega `FORESTIQ_METSAREGISTER_NOTIFICATION_CADASTRE_FIELD` ja `FORESTIQ_METSAREGISTER_NOTIFICATION_SUBPART_FIELD`; vaikimisi kasutatakse `katastri_nr` ja `eraldis_nr`. Käsk jätab kogu täisimpordi kohta ühe `DataSyncRun` auditikirje, mis sisaldab eraldiste, uute eraldiste ja imporditud teatiste arvu.

## Andmebaasi migratsioon vanast MetsIS-ist

Enne ümberlülitust tee lähte- ja sihtandmebaasist varukoopiad. Uue skeemi loovad Django migratsioonid. Vana PostgreSQL andmebaasi sisu saab kopeerida idempotentse käsuga, mis kasutab ainult lugemisühendust `LEGACY_DATABASE_URL` kaudu.

```sh
cd django_backend
python manage.py migrate
export LEGACY_DATABASE_URL='postgresql://readonly_user:password@legacy-host:5432/metsis'
python manage.py import_legacy_metsis --confirm
```

Käsk säilitab stabiilsed kasutaja-, omaniku-, katastri- ja lepingute identifikaatorid ning vana BCrypt-parooliräsi. Soovitatav tootmises kasutuselevõtu järjekord on järgmine.

1. Käivita uus PostgreSQL ning tee sinna `migrate`.
2. Impordi kontrollitud koopiast andmed käsuga `import_legacy_metsis --confirm`.
3. Võrdle enne ümberlülitust tabelite ridu ja tee sisselogimise, õiguste ning omaniku-katastri kontrolltestid.
4. Suuna puhverserver Django API konteinerile ning jälgi `api/services/status` vastust.

## Turve

Django API kasutab Bearer JWT autentimist. Reacti töölaud kasutab parooliga sisselogimise eeltokenit, TOTP kontrolli ning tavapäraseid ja värskendustokeneid. Õigused `ADMIN`, `OWNER_PROFILE`, `ASSIGNED_OWNERS`, `PHONES` ja `EVALUATION` on andmebaasis eraldiseisvad ning sünkroniseeritakse vastavatesse Django gruppidesse. Seega saavad tavapärased Django `Group` ja `Permission` kontrollid töötada paralleelselt olemasolevate ressursiõigustega; OIDC/Keycloak on dokumenteeritud järgmise etapina.

Ära kasuta `.env.example` väärtusi tootmises. Määra unikaalne `DJANGO_SECRET_KEY`, tugev PostgreSQL parool, `DJANGO_DEBUG=false`, korrektne `DJANGO_ALLOWED_HOSTS` ning päris TOTP saladused.

## Kontrollimine

Django ruumiandmete migratsioon ning kaart eeldavad PostGIS-i, seega kontrolli integraatsiooni Compose’i PostGIS-teenusega.

```sh
docker compose -f docker-compose-full-stack.yml exec api python manage.py check
docker compose -f docker-compose-full-stack.yml exec api python manage.py test api forestry accounts -v 2
```

Kasutajaliidese kontrollimiseks käivita:

```sh
cd forestiq-ui
pnpm check
pnpm build
```

Lisateavet ümberehituse domeenijaotuse, ühilduvuse, väliste registriühenduste ning käivituse kohta on failides [`docs/DJANGO_MIGRATION.md`](docs/DJANGO_MIGRATION.md) ja [`docs/DJANGO_REWRITE_ARCHITECTURE.md`](docs/DJANGO_REWRITE_ARCHITECTURE.md).
