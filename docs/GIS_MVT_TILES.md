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

Vastus kasutab sisu tüüpi `application/vnd.mapbox-vector-tile` ja lühikest privaatset vahemälu direktiivi. Toetatud kihid on `cadastres` ning `subparts`. Tundmatu kiht tagastab `404`; ebakorrektne tile’i koordinaat tagastab `400`.

| Kiht | MVT omadused | Geomeetria |
| --- | --- | --- |
| `cadastres` | `id`, `name`, `county`, `municipality`, `area` | Katastri `boundary` |
| `subparts` | `id`, `cadastre_id`, `sub_part_code`, `tree_type_code`, `area` | Eraldise `boundary` |

## Andmeulatus ja filtrid

Endpoint kasutab sama `_map_cadastre_queryset` loogikat kui olemasolevad GeoJSON endpointid. Organisatsiooni scoped manager piirab päringu aktiivse organisatsiooniga. Admin ja CRM manager näevad organisatsiooni kõiki lubatud katastriandmeid; piiratud õigusega kasutaja näeb vaid talle määratud omanike katastriandmeid.

Samad kaardifiltrid töötavad ka tile’i päringul: `customer`, `activeDeal`, `dealStage` ja `activityDays`. Filtreerimine toimub enne tile’i SQL-i koostamist, seega ei jõua välja teise organisatsiooni ega filtrist välja jäävad read.

## PostGIS SQL-i leping

Endpoint koostab piiratud Django queryseti SQL-iks ja ümbritseb selle MVT päringuga. Tile’i piir saadakse `ST_TileEnvelope(z, x, y)` abil; EPSG:3301 geomeetria teisendatakse Web Mercatorisse; `ST_AsMVTGeom` lõikab ning lihtsustab geomeetria tile’i alale; ning `ST_AsMVT` tagastab binaarse `.pbf` vastuse.

> Tootmises peab kasutusel olema PostGIS. SpatiaLite’i või muu andmebaasi korral tagastab endpoint teadliku `501`, sest MVT PostgreSQL-funktsioonid puuduvad.

## Kontrollimine

GIS-regressioonid asuvad `forestry.tests.MapFeatureTests` testiklassis. Need kontrollivad tile’i koordinaatide valideerimist, sisu tüüpi, SQL-is kasutatavaid `ST_TileEnvelope`, `ST_AsMVTGeom` ja `ST_AsMVT` funktsioone ning organisatsiooni ID jõudmist piiratud queryseti SQL-parameetritesse.

Kliendipoolne suurte GeoJSON kihtide vahetamine MapLibre vector source’iks kuulub järgnevasse sõltuvasse töösse GIS-02. GeoJSON detail- ja väikesed sündmuskihid jäävad selle ajani olemasolevale endpointile.
