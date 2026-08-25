# Celery andmevärskendus

ForestIQ kasutab **Celery + Redis** järjekorda. Redis kannab järjekorras olevat tööd; püsiv ja varundatav käivitusaudit säilib samas PostgreSQL/PostGIS andmebaasis nagu rakenduse põhiandmed. Rakenduse API, `worker` ja `beat` on eraldi Compose-teenused. API lisab töö järjekorda, worker käivitab selle ning iga käivitus jääb tabelisse `data_sync_runs` koos Celery töö-ID, staatuse, tulemuste ja veateatega.

| Allikas | Vaikimisi kasutus | Seotud ForestIQ andmed | Autentimine |
|---|---|---|---|
| Maa- ja Ruumiameti WFS | `kataster:ky_kehtiv` ühe täpse katastritunnusega | aadress, asukoht, pindala, kõlvikud, metsamaa, geomeetria | ei vaja |
| Metsaregistri WFS | `metsaregister:eraldis` ühe `katastri_nr` väärtusega | eraldised, puuliik, pindala, tagavara ja geomeetria | ei vaja |
| SOOS WFS | valikuline, keskkonnamuutujate kaudu | lähteatribuudid ja geomeetria `ForestRegistryFeature` kirjetena | sõltub teenusest |
| Forestek / Weasel | valikuline katastripõhine omanike päring | `Owner` ja `OwnerCadastre` seosed | teenusekonto Bearer-token |
| Pärimus | valikuline täpne isikukoodipäring | auditiga `InheritanceSignal` teated | ForestIQ-le määratud Bearer-token |

> Avaliku WFS-i andmed on ruumiandmete lähteandmed. ForestIQ ei kustuta automaatselt käsitsi lisatud omanik–katastri seoseid ega asenda kasutaja sisestatud kinnistu nime. GeoJSON geomeetria valideeritakse GEOS-i abil ja talletatakse PostGIS-is EPSG:3301 geomeetriana; varasem JSON-väli jääb API tagasühilduvuseks. Pärimus- ja Foresteki-päringud käivituvad ainult siis, kui nende URL ning token on selgesõnaliselt seadistatud.

## Esmakordne käivitus

Kopeeri `.env.example` failiks `.env`, määra Django ja PostgreSQL saladused ning käivita täisstack. Celery Beat lisab portfelli sünkroniseerimise automaatselt igal päeval Redis-järjekorda; selle intervalli vaikimisi väärtus on 86400 sekundit ja seda saab arenduses muuta `FORESTIQ_PORTFOLIO_SYNC_INTERVAL_SECONDS` abil.

```bash
docker compose -f docker-compose-full-stack.yml up --build db redis api worker beat
```

Beat lisab igale olemasolevale katastriüksusele eraldi tausttöö, mitte üht suurt monoliitset päringut. See lubab vea korral töö üksusena korrata ning säilitab tulemuse `data_sync_runs` tabelis.

Ühe katastriüksuse kontrollitud käsitsi värskendamiseks kasutatakse administraatori API-t:

```bash
curl -X POST http://localhost:8000/api/services/admin/cadastres/10501:001:0001/sync \
  -H "Authorization: Bearer <admin-access-token>"
```

Arenduses või testis võib töö käivitada samas protsessis:

```bash
FORESTIQ_TASKS_INLINE=true python manage.py test forestry -v 2
```

Administraator võib sama töö esitada ka `POST /api/services/admin/cadastres/{katastritunnus}/sync` kaudu. Viimased tööd on saadaval `GET /api/services/admin/sync-runs` otspunktis.

## Autenditud allikad

Forestek nõuab dokumenteeritud teenusekontot. Määra `FORESTEK_API_URL` Weaseli lepingu järgi ning `FORESTEK_API_TOKEN` keskkonnamuutujana; loginilehe kraapimine ei ole toetatud. Pärimuse jaoks määra `PARIMUS_API_URL` Pärimuse rakenduse juuraadressiks ning `PARIMUS_API_TOKEN` sama väärtusega, mille Pärimus kontrollib `FORESTIQ_INHERITANCE_API_TOKEN` seadetes. Mõlemad tokenid peavad olema eraldi, vähimate õigustega teenusemandaadid ning neid ei tohi Git’i lisada.

## Viited

1. [Maa- ja Ruumiameti katastri WFS metaandmed](https://metadata.geoportaal.ee/geonetwork/srv/api/records/1591a3f4-a4f2-4dcd-8d1f-3d966eb8655e)
2. [Keskkonnaportaali GeoServeri WFS-i juhend](https://keskkonnaportaal.ee/et/avaandmed/geoserver)
3. [Maa-ameti avalike ruumiandmeteenuste ülevaade](https://geoportaal.maaamet.ee/eng/services/public-wms-wfs-p346.html)
