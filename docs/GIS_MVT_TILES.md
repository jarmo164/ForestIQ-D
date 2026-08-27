# GIS MVT tile endpoint

**Autor:** Manus AI  
**Kehtivus:** GIS-01 — organisatsiooni- ja filtriteadlikud Mapbox Vector Tile’id  
**Seis:** rakendatud

## Eesmärk

GIS-01 lisab ForestIQ-D kaarditeenusele PostGIS-põhise Mapbox Vector Tile’i ehk MVT endpointi suurte katastri- ja eraldisekihtide jaoks. Endpoint teeb geomeetria üldistamise, tile’i lõikamise ja binaarse serialiseerimise andmebaasis. See väldib ühe suure GeoJSON kogumi laadimist serverisse või kliendibrauserisse.

## Endpoint

```
GET /api/services/map/tiles/{layer}/{z}/{x}/{y}.pbf
```

Vastus kasutab sisu tüüpi `application/vnd.mapbox-vector-tile`, lühikest privaatset vahemälu direktiivi ning SHA-256 põhist `ETag` väärtust. Toetatud kihid on `cadastres`, `subparts` ja `registry`. Sama `If-None-Match` tingimuspäring tagastab `304 Not Modified`. Tundmatu kiht tagastab `404`; ebakorrektne tile’i koordinaat tagastab `400`.

| Kiht | MVT omadused | Geomeetria |
| --- | --- | --- |
| `cadastres` | `id`, `name`, `county`, `municipality`, `area` | Katastri `boundary` |
| `subparts` | `id`, `cadastre_id`, `sub_part_code`, `tree_type_code`, `area` | Eraldise `boundary` |
| `registry` | `id`, `cadastre_id`, `subpart_code`, `title`, `work_code`, `decision`, `area`, `volume` | Metsaregistri `spatial_geometry` |

## Katastri summary

```
GET /api/services/cadastres/{cadastre_id}/summary
```

Õiguspõhine summary tagastab kaardipaneelile kompaktse koondi: nähtavate omanike ja kliendiomanike arv, eraldiste arv ja kogupindala, teatiste koguarv ning aktiivsete teadete arv, samuti aktiivsete ja võidetud tehingute arv ning etapipõhine jaotus. See ei lae tööruumi tegevusajalugu, registriobjektide loendit ega kontaktandmeid.

## Andmeulatus ja filtrid

Endpoint kasutab sama `_map_cadastre_queryset` loogikat kui olemasolevad GeoJSON endpointid. Organisatsiooni scoped manager piirab päringu aktiivse organisatsiooniga. Admin ja CRM manager näevad organisatsiooni kõiki lubatud katastriandmeid; piiratud õigusega kasutaja näeb vaid talle määratud omanike katastriandmeid.

Samad kaardifiltrid töötavad ka tile’i päringul: `customer`, `activeDeal`, `dealStage` ja `activityDays`. Filtreerimine toimub enne tile’i SQL-i koostamist, seega ei jõua välja teise organisatsiooni ega filtrist välja jäävad read.

## PostGIS SQL-i leping

Endpoint koostab piiratud Django queryseti SQL-iks ja ümbritseb selle MVT päringuga. Tile’i piir saadakse `ST_TileEnvelope(z, x, y)` abil; EPSG:3301 geomeetria teisendatakse Web Mercatorisse; `ST_AsMVTGeom` lõikab ning lihtsustab geomeetria tile’i alale; ning `ST_AsMVT` tagastab binaarse `.pbf` vastuse.

> Tootmises peab kasutusel olema PostGIS. SpatiaLite’i või muu andmebaasi korral tagastab endpoint teadliku `501`, sest MVT PostgreSQL-funktsioonid puuduvad.

## Cache ja kontrollitud invalidatsioon

Serveri MVT cache’i võti hõlmab organisatsiooni, aktiivset kasutajat, lubatud kaardifiltreid, kihti, tile’i koordinaate ning kihiversiooni. `FORESTIQ_MVT_CACHE_TTL_SECONDS` juhib lühikest private cache’i aegumist. Katastri, metsaeraldise, Metsaregistri või omaniku–katastri seose muutus tõstab ainult mõjutatud organisatsiooni kihiversiooni; eelmise versiooni võtmed muutuvad kohe kättesaamatuks ning aeguvad tavapärase TTL-iga.

## Indeksid ja p95 jõudluseelarve

PostGIS loob ruumilistele väljadele `Cadastre.boundary`, `CadastreSubPart.boundary` ja `ForestRegistryFeature.spatial_geometry` GiST-indeksid. Lisaks kasutavad kaartfiltrid ning summary organisatsiooni-katastri B-tree indekseid `cad_org_id_idx`, `subpart_org_cad_idx`, `notif_org_cad_idx`, olemasolevat `deal_organization_owner_idx` ja `deal_organization_stage_idx` ning omaniku-katastri seostabeli unikaalset organisatsioonivõtit.

Kvaliteedivärav käitab `GisPerformanceBudgetTests` päris PostGIS-i vastu. Test loob alati 64 geomeetriaga katastriüksusest koosneva fikseeritud korpuse, mõõdab 15 uncached MVT `cadastres` päringut ja 15 summary päringut ning jõustab nearest-rank p95 eelarve. Vaikimisi lävi on `FORESTIQ_GIS_PERFORMANCE_P95_MS=500`; test väljastab logisse mõõdetud p95 väärtused koos korpuse suuruse ja lävega.

## Kontrollimine

GIS-regressioonid asuvad `forestry.tests.MapFeatureTests` testiklassis ning jõudlustest `forestry.tests_gis_performance.GisPerformanceBudgetTests` testiklassis. Need kontrollivad tile’i koordinaatide valideerimist, sisu tüüpi, SQL-is kasutatavaid `ST_TileEnvelope`, `ST_AsMVTGeom` ja `ST_AsMVT` funktsioone, organisatsiooniscopingut, cache-hit’i, ETagi, tingimuslikku `304` vastust, invalidatsiooni, summary koondandmeid ja mõõdetud p95 eelarvet.

MapLibre’i suured katastri-, eraldise- ja Metsaregistri kihid kasutavad MVT vector source’i. Väikese mahuga uute eraldiste ja teatiste detail-/sündmuskihid jäävad teadlikult olemasolevale GeoJSON fallback-liidesele.
