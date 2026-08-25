# ForestIQ Django ümberkirjutuse arhitektuur

## Eesmärk ja ühilduvus

Haru `rewrite` säilitab metsaomanike, katastri, töölaudade, meeldetuletuste, sõnumite, lepingute ning väliste registrite andmevood, mis olid `main`-harus kasutuses. REST-vastuste olemasolevad teed jäävad alles ning uus ruumiandmete punkt `GET /api/services/map/cadastres` annab kaardile ainult valideeritud GeoJSON-geomeetria.

| Kiht | Rakenduslik valik | Miks |
|---|---|---|
| API ja domeen | Python 3.12, Django 5.1+, Django REST Framework | Standardne autentimine, õigused, migratsioonid ja säilitatud REST-lepingud. |
| Ruumilised andmed | PostgreSQL 16, PostGIS 3.4, GeoDjango, EPSG:3301 | Katastriüksuste ja metsaregistri geomeetriad on valideeritud ning ristumispäringud toimuvad andmebaasis. |
| Taustatöö | Celery, Redis, Celery Beat | WFS- ja registrisünkroniseerimine on mittesünkroonne, korduskatsetatav ja auditeeritud. |
| Frontend | React 19, Vite, MapLibre | Kiire töölaud ning vabalt kasutatav interaktiivne GeoJSON-kaart. |
| Failid | Django `FileSystemStorage`, jagatud Compose’i maht | Lepingud paiknevad alguses lokaalselt; andmebaasi jääb ainult failiviide. |

## Andmevood

Katastri sünkroniseerimise taotlus loob esmalt `DataSyncRun` kirje. Celery töö salvestab selle järjekorra identifikaatori, seisundi, algus- ja lõpuaja, tulemuse ning võimaliku vea. Worker loeb WFS-ist GeoJSON-i, valideerib selle GEOS-i kaudu, teisendab polügooni vajadusel `MultiPolygon`-iks ning salvestab selle SRID-ga 3301 PostGIS-i väljale. Päring `GET /api/services/map/cadastres?bbox=west,south,east,north` teisendab MapLibre’i WGS84 vaateakna EPSG:3301-ks, kasutab `boundary__intersects` GIS-päringut ning annab geomeetria tagasi WGS84 GeoJSON-na.

> Vanad JSON-väljad `polygon`, `centroid` ja `geometry` jäävad alles olemasolevate REST-tarbijate ühilduvuseks. Uued GeoDjango väljad on autoriteetne ruumilise päringu ja valideerimise kiht.

## Õigused ning hilisem OIDC/Keycloak

Kohalik lähtepunkt on Django kasutajamudel, `Group` ja `Permission`. ForestIQ varasemad privilegeerõngad sünkroniseeritakse automaatselt hallatavatesse Django gruppidesse ning senised ressursipõhised kontrollid, näiteks kasutajale määratud omanike piirang, säilivad. OIDC/Keycloak lisatakse järgnevas etapis `django-allauth` või `mozilla-django-oidc` kaudu ning olemasolev kasutaja seotakse stabiilse `sub` nõudega, mitte muutuva e-posti aadressiga.

## Lokaalne käivitus

Kopeeri `.env.example` failiks `.env`, määra `DJANGO_SECRET_KEY` ja `POSTGRES_PASSWORD`, seejärel käivita `docker compose -f docker-compose-full-stack.yml up --build`. Teenused on `db` (PostGIS), `redis`, `api`, `worker`, `beat` ja `ui`. API rakendab migratsioonid enne Gunicorni käivitamist ning dokumentide kataloog `media/` on API ning workeri vahel jagatud Compose’i mahuna `forestiq_media`.

Lepingufail lisatakse administraatori õigusega vormipostitusena `POST /api/services/contracts/{id}/document` väljal `file`. Ainult PDF on lubatud. Faili allalaadimine jätkub teel `GET /api/services/contracts/{id}/pdf`; uus lokaalset faili kasutav tee on sama prioriteediga kui varasem andmebaasi binaarväljal põhinev tagasikohalduvus.

## Migratsioon ja kontroll

Enne tootmisandmete migratsiooni tee PostGIS-i andmebaasist varukoopia. Käivita `python manage.py migrate`, laadi vana süsteemi andmed dokumenteeritud impordikäsuga ning käivita iga olemasoleva katastri jaoks nõudmisel sünkroniseerimine, et täita uued ruumiandmete väljad. See väldib varasema JSON-geomeetria vaikset eeldamist ilma GEOS-i valideerimiseta.

| Kontroll | Käsk |
|---|---|
| Django süsteemikontroll | `docker compose -f docker-compose-full-stack.yml exec api python manage.py check` |
| Backendi testid | `docker compose -f docker-compose-full-stack.yml exec api python manage.py test api forestry accounts -v 2` |
| Frontendi tüübid | `cd forestiq-ui && pnpm check` |
| Frontendi tootmiskooste | `cd forestiq-ui && pnpm build` |
