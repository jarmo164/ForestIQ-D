# ForestIQ

ForestIQ on metsaostjate töölaud. Selle haru server on ümber ehitatud **Python 3.12, Django, Django REST Frameworki ja PostgreSQL-i** peale ning kasutajaliides **React 19, TypeScripti ja Vite’i** peale. Uus kasutajaliides säilitab Django `api/` ja `api/services/` lepingud, JWT/TOTP sisselogimise ning metsaomanike töövood.

## Uus arhitektuur

| Kiht | Tehnoloogia | Vastutus |
|---|---|---|
| Kasutajaliides | React 19 + TypeScript + Vite | Metsaomanike, katastri, töölaudade, sõnumite, meeldetuletuste ja halduse operatiivne töölaud |
| API | Django + Django REST Framework | REST liides, domeeniloogika, õigused ja JWT autentimine |
| Andmebaas | PostgreSQL 16 | Omanikud, katastriüksused, töölogid, sõnumid, lepingud ja muu püsiv domeeniinfo |
| Käitus | Docker Compose + Gunicorn + Nginx | Korratav kohaliku või serveripõhise rakenduse ja API ühtne käivitus |

Django rakendused on jagatud selgete domeenipiiridega: `accounts` haldab identiteeti ja õigusi, `forestry` metsaomanike ning katastri domeeni, `operations` meeldetuletusi, sõnumeid ja lepinguid ning `api` säilitab REST-liidese ühilduvuse.

## Lokaalne käivitus

Kopeeri keskkonnamuutujad ning vali arenduseks pikk juhuslik saladus.

```sh
cp .env.example .env
# muuda vähemalt DJANGO_SECRET_KEY ja POSTGRES_PASSWORD
```

Käivita andmebaas ja Django API.

```sh
docker compose -f docker-compose-full-stack.yml up --build db api
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

Django API kasutab Bearer JWT autentimist. Reacti töölaud kasutab parooliga sisselogimise eeltokenit, TOTP kontrolli ning tavapäraseid ja värskendustokeneid. Õigused `ADMIN`, `OWNER_PROFILE`, `ASSIGNED_OWNERS`, `PHONES` ja `EVALUATION` on andmebaasis eraldiseisvad ning `ASSIGNED_OWNERS` piirab omanikuandmed kasutaja enda töödega.

Ära kasuta `.env.example` väärtusi tootmises. Määra unikaalne `DJANGO_SECRET_KEY`, tugev PostgreSQL parool, `DJANGO_DEBUG=false`, korrektne `DJANGO_ALLOWED_HOSTS` ning päris TOTP saladused.

## Kontrollimine

Django kontroll ja testid töötavad ilma kohaliku PostgreSQL serverita SQLite-põhise testandmebaasiga; tegelik rakenduse andmebaas on siiski PostgreSQL.

```sh
cd django_backend
USE_SQLITE_FOR_TESTS=1 python manage.py check
USE_SQLITE_FOR_TESTS=1 python manage.py test api -v 2
```

Kasutajaliidese kontrollimiseks käivita:

```sh
cd forestiq-ui
pnpm check
pnpm build
```

Lisateavet ümberehituse domeenijaotuse, ühilduvuse ja väliste registriühenduste kohta on failis [`docs/DJANGO_MIGRATION.md`](docs/DJANGO_MIGRATION.md).
