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

## Renderi kasutuselevõtt

Render Blueprint on failis [`render.yaml`](render.yaml). See loob Django API, Celery workeri, Celery Beati, Redis’e, PostgreSQL/PostGIS-i ning eraldi MapLibre’i staatilise kliendi. Täielik kasutuselevõtu, PostGIS-i aktiveerimise, keskkonnamuutujate ja lokaalsete mediafailide piirangute juhend on failis [`docs/RENDER_DEPLOY.md`](docs/RENDER_DEPLOY.md).

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

Maa- ja Ruumiameti katastri WFS ning metsaregistri WFS on seadistatud vaikimisi avalikeks allikateks. Celery worker värskendab need katastriüksuse kaupa ning säilitab iga käivituse auditi mudelis `DataSyncRun`; Celery Beat loetleb aktiivsed organisatsioonid ja paneb iga organisatsiooni portfelli sünkroniseerimise eraldi järjekorda. Arenduses saab intervalli muuta muutujaga `FORESTIQ_PORTFOLIO_SYNC_INTERVAL_SECONDS`.

Üksikut katastriüksust saab värskendada administraatori API kaudu (`POST /api/services/admin/cadastres/{id}/sync`). Foresteki omaniku-katastri seosed, SOOS-i WFS ja Pärimuse päringud on tahtlikult opt-in: need käivituvad alles siis, kui nende teenuse URL ja eraldi vähimate õigustega token on `.env` failis seadistatud. Täpne andmevoog, auditeerimine ja migratsioonisammud on failis [`docs/DJANGO_REWRITE_ARCHITECTURE.md`](docs/DJANGO_REWRITE_ARCHITECTURE.md).

### Käsitsi impordiskriptid

Käsud käivitavad importimise samas protsessis ning loovad iga tegelikult töödeldud katastriüksuse kohta `DataSyncRun` auditirea. Alusta alati kuivkäivitusega; see kontrollib konfiguratsiooni ja valitud ulatust, kuid **ei tee välispäringuid ega kirjuta andmebaasi**.

```sh
cd django_backend

# Avalikud WFS-i allikad: katastriüksus, metsaregister ning seadistatud SOOS.
python manage.py import_wfs_sources --organization forestiq-default --cadastre 79501:001:0001 --source all --dry-run
python manage.py import_wfs_sources --organization forestiq-default --cadastre 79501:001:0001 --source cadastre
python manage.py import_wfs_sources --organization forestiq-default --all --source metsaregister --limit 50 --continue-on-error

# Volitatud API-allikad: enne on vaja seadistada FORESTEK_API_URL/TOKEN või PARIMUS_API_URL/TOKEN.
python manage.py import_external_api_sources --organization forestiq-default --cadastre 79501:001:0001 --source forestek --dry-run
python manage.py import_external_api_sources --organization forestiq-default --all --source parimus --limit 25 --continue-on-error
```

`import_wfs_sources` toetab allikaid `cadastre`, `metsaregister`, `soos` ja `all`. Valiku `all` korral jäetakse seadistamata SOOS teadlikult vahele; eraldi `--source soos` nõuab selle URL-i ja kihi seadistust. `import_external_api_sources` toetab `forestek`, `parimus` ja `all`; ükski volitatud API-päring ei käivitu enne URL-i ning tokeni eelkontrolli läbimist. Tõrked talletatakse auditireal ning `--continue-on-error` lubab töödelda järgmisi üksusi.

**Forestek on ühekordne algimport.** Käivita `import_external_api_sources --all --source forestek` ainult pärast Foresteki URL-i ja tokeni seadistamist ning enne esimese eduka Foresteki impordi tekkimist. Pärast esimest edukat importi keeldub käsk kordusest. Forestek on eemaldatud Celery Beat’i ajakavast, tavapärasest katastri-/metsaregistri värskendusest ja integratsioonide käivitus-API-st; jätkuvad andmeuuendused tulevad metsaregistri WFS-i eraldiste ning teatiste voost.

### Metsaregistri esmane täisimport ja uued teatised

Kui metsaregister on põhiandmeallikas, käivita esmalt täisimport. Käsk loeb `FORESTIQ_METSAREGISTER_FULL_WFS_LAYER` kihist kõik eraldised lehekülgede kaupa. Iga eraldis salvestatakse `CadastreSubPart`-ina; ainult juhul, kui kombinatsiooni **katastriüksus + eraldise number** veel andmebaasis ei ole, tehakse teatiste kihile sihitud CQL-päring. Juba olemasolevate eraldiste teatisi ei laadita selle käsuga uuesti.

```sh
cd django_backend

# Kontrollib seadistuse ja kavandatud voo, kuid ei tee WFS-päringuid.
python manage.py import_metsaregister_full --organization forestiq-default --dry-run

# Esmane täielik eraldiste import ning uute eraldiste teatised.
python manage.py import_metsaregister_full --organization forestiq-default --page-size 1000

# Ainult eraldiste täisimport, kui teatiste kiht ei ole veel seadistatud.
python manage.py import_metsaregister_full --organization forestiq-default --without-notifications
```

Teatiste automaatseks järelpäringuks seadista lisaks metsaregistri URL-ile ja eraldiste kihile `FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER`. Vajadusel saab CQL-väljade nimed määrata muutujatega `FORESTIQ_METSAREGISTER_NOTIFICATION_CADASTRE_FIELD` ja `FORESTIQ_METSAREGISTER_NOTIFICATION_SUBPART_FIELD`; vaikimisi kasutatakse `katastri_nr` ja `eraldis_nr`. Käsk jätab kogu täisimpordi kohta ühe `DataSyncRun` auditikirje, mis sisaldab eraldiste, uute eraldiste ja imporditud teatiste arvu.

### Perioodiline metsaregistri CQL-deltakontroll

Celery Beat käivitab organisatsioonide dispetšeri vaikimisi iga tunni järel. Dispetšer loob iga aktiivse organisatsiooni jaoks eraldi `run_metsaregister_delta_check` töö ja auditirea. Iga töö kasutab WFS-i eraldiste kihil CQL-filtrit kujul `registreerimise_kp >= '<UTC-aeg>'`, kus alguspunkt on sama organisatsiooni eelmise eduka kontrolli lõpetamisaeg koos väikese kattuvusakna (`FORESTIQ_METSAREGISTER_DELTA_OVERLAP_MINUTES`) võrra. Esimesel käivitamisel kasutatakse piiratud tagasivaateakent (`FORESTIQ_METSAREGISTER_DELTA_LOOKBACK_HOURS`). Kattuvus teeb töö idempotentseks: muutunud või juba nähtud eraldised uuendatakse, kuid teatiste CQL-päring tehakse ainult lokaalselt uutele eraldistele.

```sh
cd django_backend

# Käivita sama kontroll üks kord käsitsi.
python manage.py check_metsaregister_delta --organization forestiq-default
```

Ajastust saab muuta keskkonnamuutujaga `FORESTIQ_METSAREGISTER_DELTA_INTERVAL_SECONDS`; CQL-is kasutatavat muutmisvälja määrab `FORESTIQ_METSAREGISTER_DELTA_FIELD`, mille vaikimisi väärtus on `registreerimise_kp`. Iga jooks salvestatakse eraldi `DataSyncRun` kirjeks allikaga `celery:metsaregister-cql-delta`, koos kasutatud algusaja, tuvastatud uute eraldiste ja imporditud teatiste arvuga.

### MapLibre ja GeoDjango kaardikihid

Reacti kaarditööruum aadressil `/map` kasutab MapLibre’i ning laeb ruumiandmed ainult autoriseeritud Django REST-liidese kaudu. Katastriüksused tulevad otspunktist `GET /api/services/map/cadastres`; GeoDjango eraldised, metsaregistri objektid ja teatiste markerid tulevad vastavalt otspunktidest `GET /api/services/map/layers/subparts`, `registry` ja `notifications`. Kõik geomeetriad teisendatakse serveris EPSG:4326 GeoJSON-iks ning MapLibre ei pöördu otse välise WFS-teenuse poole.

Kihipaneeliga saab katastriüksused, metsaeraldised, metsaregistri objektid ja teatised eraldi sisse või välja lülitada. Kaardilt valitud objekti atribuudid kuvatakse samas tööruumis. Teatis markerina paikneb seotud eraldise tsentroidil, sest teatisel endal ei ole eraldi geomeetriavälja.

Kaart sisaldab ka eraldi **uute eraldiste** kihti (`GET /api/services/map/layers/new-subparts`). See näitab vaikimisi viimase seitsme päeva jooksul CQL-deltakontrolli või täisimpordiga avastatud eraldisi; ajaakent juhib `FORESTIQ_MAP_NEW_SUBPART_HOURS`. Uuel eraldisel, metsaregistri objektil või teatise markeril klõpsamine avab MapLibre popupi. Teatise popup ühendab teatise numbri, töö liigi ja staatuse seotud eraldise katastritunnuse, puuliigi, pindala ning avastamisajaga.

Katastriüksuse klõpsamine avab kaardikeskse tervikvaate. Klient laadib selleks õiguspõhise koondvastuse `GET /api/services/cadastres/<katastritunnus>/workspace`. Detailaken hõlmab vara põhiandmeid, ligipääsetavaid omanikke ja nende kontaktandmeid, kliendisuhte seisu (aktiivsed ning võidetud tehingud), omanike tegevusajalugu ja meeldetuletusi, teatisi ning metsaregistri objekte. Kaasomaniku andmed, millele kasutajal puudub ligipääs, jäetakse vastusest välja.

### Suurte kaardikihtide jõudlus

MapLibre ei lae enam kõiki katastri- ja polügooniobjekte korraga. Pärast kaardi liikumise lõppu uuendatakse kihte ühe debounced päringutsükliga ning API saab ainult nähtava kaardiala `bbox`-i. Katastriüksused ning uued eraldised ilmuvad alates suumist 8, teatised suumist 9 ning polügoonitihedad eraldiste ja metsaregistri kihid suumist 10. Iga serverivastus on piiratud konfigureeritava `limit`-iga; serveri vaikimisi piirid on `FORESTIQ_MAP_CADASTRE_LIMIT=750`, `FORESTIQ_MAP_FEATURE_LIMIT=1500` ja absoluutne ülempiir `FORESTIQ_MAP_MAX_FEATURE_LIMIT=3000`.

Kaarditööruumi filtrid piiravad kõiki nähtaval alal laetavaid kihte samade õiguspõhiste katastriüksustega. Filtreid saab kombineerida **võidetud tehingu/kliendisuhte**, **aktiivse tehingu**, kindla **tehinguetapi** ja viimase 7, 30, 90 või 365 päeva **tegevusajaloo** järgi. Filtri muutmine käivitab sama debounced vaatealapõhise päringutsükli ega lae kogu ruumiandmestikku uuesti.

## Andmebaasi migratsioon vanast MetsIS-ist

Enne ümberlülitust tee lähte- ja sihtandmebaasist varukoopiad. Uue skeemi loovad Django migratsioonid. Vana PostgreSQL andmebaasi sisu saab kopeerida idempotentse käsuga, mis kasutab ainult lugemisühendust `LEGACY_DATABASE_URL` kaudu.

```sh
cd django_backend
python manage.py migrate
export LEGACY_DATABASE_URL='postgresql://readonly_user:password@legacy-host:5432/metsis'
python manage.py import_legacy_metsis --confirm --organization forestiq-default
```

Käsk säilitab stabiilsed kasutaja-, omaniku-, katastri- ja lepingute identifikaatorid ning vana BCrypt-parooliräsi. Soovitatav tootmises kasutuselevõtu järjekord on järgmine.

1. Käivita uus PostgreSQL ning tee sinna `migrate`.
2. Impordi kontrollitud koopiast andmed käsuga `import_legacy_metsis --confirm --organization forestiq-default`.
3. Võrdle enne ümberlülitust tabelite ridu ja tee sisselogimise, õiguste ning omaniku-katastri kontrolltestid.
4. Suuna puhverserver Django API konteinerile ning jälgi `api/services/status` vastust.

### Organisatsioonivõtme backfill (AUTH-01)

AUTH-01 migratsioon lisab `Organization` mudeli, kasutaja organisatsiooniliikmesuse ja organisatsioonivõtme kõigile omaniku-, katastri-, tehingu-, lepingu-, pärimis- ning auditikirjetele. Juba olemasolevad read seotakse idempotentselt organisatsiooniga `forestiq-default` (UUID `00000000-0000-4000-8000-000000000001`); see säilitab praeguse ühe organisatsiooni töövoo kuni järgmine etapp lisab taotlusepõhise organisatsioonikonteksti.

Pärast tootmismigratsiooni kontrolli tulemust ainult lugemisrežiimis. Käsk ei tee muudatusi; `--fail-on-issues` sobib kasutuselevõtu kontrollväravasse.

```sh
cd django_backend
python manage.py migrate
python manage.py verify_organization_backfill --fail-on-issues
```

Organisatsiooniga seotud alamkirjete loomisel pärineb võti nende ärilise vanemagregaadi järgi. Näiteks omaniku tegevuslogi, tehing, pakkumine, leping, pärimisjuhtum ning pärija ei saa salvestuda omaniku või tehinguga erinevasse organisatsiooni; ka ristorganisatsiooniline omaniku–katastri seos katkestatakse enne relatsiooni loomist.

### Organisatsioonipõhine API- ja tööisolatsioon (AUTH-02)

Iga Bearer JWT sisaldab välju `organization_id` ja `organizationId`. Django kontrollib, et tokeni kasutajal on aktiivne liikmesus nimetatud organisatsioonis, ning aktiveerib päringu ajaks fail-closed organisatsioonikonteksti. Kõigi organisatsioonivõtmega ärimudelite tavapärased queryset’id filtreeritakse selle konteksti järgi; teise organisatsiooni detailobjekt tagastab seega `404`, enne eraldi ressurssiõiguse kontrolli.

Celery tööde, WFS-i ja API-importide signatuurid nõuavad samuti eksplitsiitset organisatsioonivõtit. Beat’i globaalne dispetšer ei töötle äriridu otse, vaid väljastab iga aktiivse organisatsiooni jaoks eraldi scoped töö. Kõik käsitsi impordi- ja sünkroonikäsud nõuavad `--organization <UUID-või-slug>` argumenti; `forestiq-default` on AUTH-01 backfill’i üleminekuorganisatsioon.

### Keycloak, liikmesusrollid ja õigused (AUTH-03)

AUTH-03 kasutab **Authorization Code + PKCE (`S256`)** voogu. React küsib brauserile ohutu seadistuse teelt `GET /api/oidc/config`, genereerib krüptograafiliselt juhusliku `state`, `nonce` ja `code_verifier` väärtuse ning suunab kasutaja Keycloaki. Tagasisuunamisel saadetakse kood koos verifier’iga ainult Django teele `POST /api/oidc/exchange`. Django vahetab koodi serveris, kontrollib ID tokeni allkirja Keycloaki JWKS-i, `iss`, `aud` ja `nonce` väärtust ning väljastab seejärel ForestIQ sisemise, lühiajalise JWT.

Keycloaki `sub` talletatakse muutumatu `oidc_subject` väljana. Iga sisselogimine seob kasutaja aktiivse organisatsiooniga tokeni seadistatavast `organization_id` claim’ist ning värskendab üksnes selle organisatsiooniliikmesuse rolle. API ei usalda vana tokeni õiguste claim’i: päringu autentimine loeb kehtiva liikmesuse andmebaasist, nii et rolli või liikmesuse eemaldamine jõustub kohe järgmisel API päringul.

| Keycloak’i roll | ForestIQ liikmesusõigused | Endpointi ja andmete ulatus |
| --- | --- | --- |
| `ORG_OWNER`, `ORG_ADMIN` | `ADMIN`, `OWNER_PROFILE`, `ASSIGNED_OWNERS`, `PHONES`, `EVALUATION` | Täielik haldus organisatsiooni piires. |
| `CRM_MANAGER` | `OWNER_PROFILE`, `ASSIGNED_OWNERS` | Kõik organisatsiooni omaniku- ja CRM-andmed; haldusendpointid jäävad keelatuks. |
| `EVALUATOR` | `EVALUATION` | Hindamisjärjekord ja talle määratud hindamiste töövoog. |
| `CALLER` | `ASSIGNED_OWNERS`, `PHONES` | Ainult talle määratud omanike andmed ning telefonikataloog. |
| `ORG_MEMBER`, `VIEWER` | Puuduvad kirjutamisõigused | Ainult selgelt lubatud üldised lugemis- ja sõnumiendpointid; omaniku- ning CRM-andmed on keelatud. |

Seadista tootmises järgmised keskkonnamuutujad ning registreeri Keycloakis täpne Reacti tagasisuunamise URI, näiteks `https://app.example.ee/login`. `KEYCLOAK_ISSUER` peab tootmises kasutama HTTPS-i. `KEYCLOAK_ORGANIZATION_CLAIM` toetab punktnotatsiooni, näiteks `organization.id`.

```sh
KEYCLOAK_OIDC_ENABLED=true
KEYCLOAK_ISSUER=https://sso.example.ee/realms/forestiq
KEYCLOAK_CLIENT_ID=forestiq-web
KEYCLOAK_ORGANIZATION_CLAIM=organization_id
# Valikuline: KEYCLOAK_SCOPES=openid profile email
```

Kohalik parooli- ja TOTP-vool jääb ainult arenduse ühilduvuseks. `FORESTIQ_DEVMODE=true` toimib üksnes koos `DJANGO_DEBUG=true`; tootmises (`DJANGO_DEBUG=false`) tagastavad kohalikud `password-login`, TOTP ja paroolivahetuse endpointid vastuse `403`, sõltumata keskkonnamuutujast.

### Optimistlik lukustus kriitilistel agregaatidel (API-03)

`Owner`, `Deal`, `Contract` ja `InheritanceCase` sisaldavad täisarvulist välja `version`, mille algväärtus on `1`. Iga detail- ja töövoovastus tagastab selle versiooni. Kriitiline kirjutus peab JSON-kehas saatma samaväärtusliku `version` välja; alternatiivina toetab API standardset `If-Match` päist. Puuduv või vigane versioon tagastab `428` koos koodiga `version_required`.

Server rakendab muudatuse ühe tingimusliku andmebaasivärskendusena: muudatus õnnestub ainult siis, kui salvestatud versioon vastab kliendi eeldatud versioonile. Eduka kirjutuse järel versioon suureneb ühe võrra. Kui teine kasutaja on vahepeal sama agregaati muutnud, jääb vana kirjutus andmebaasist välja ning API tagastab `409` koos koodiga `version_conflict`, kliendi oodatud versiooni ja viimase teadaoleva versiooniga.

| Agregaat | Kaitstud muutused | Kliendi ootus konflikti korral |
| --- | --- | --- |
| `Owner` | Detailandmed, staatus, vastutaja | Laadi omanik uuesti ning esita muudatus kasutaja kinnitusega. |
| `Deal` | Hindamine, pakkumised, sulgemine ja lepingudrafti genereerimine | Värskenda töövoo olek ning ära jätka vananenud pakkumisega. |
| `Contract` | Olemasoleva lepingu andmed, fail ja kustutamine | Laadi lepingu detail uuesti; failimuudatust ei rakendata vanale versioonile. |
| `InheritanceCase` | Staatus, määramine, pärijad ja märkmed | Värskenda juhtum koos sündmuste ja pärijate viimase seisuga. |

## Turve

Django API kasutab organisatsiooniga seotud sisemist Bearer JWT-d. Reacti töölaud kasutab tootmises Keycloak’i Authorization Code + PKCE voogu; kohalik parooli/TOTP voog on ainult arenduseks. Õigused `ADMIN`, `OWNER_PROFILE`, `ASSIGNED_OWNERS`, `PHONES` ja `EVALUATION` tulenevad aktiivse organisatsiooniliikmesuse rollidest ning pärandõigused sünkroniseeritakse endiselt vastavatesse Django gruppidesse. Seega töötavad tavapärased Django `Group` ja `Permission` kontrollid paralleelselt liikmesusepõhise ressursiõigusega, kuid tenantide vahelist pääsu ei saa globaalne grupp anda.

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
