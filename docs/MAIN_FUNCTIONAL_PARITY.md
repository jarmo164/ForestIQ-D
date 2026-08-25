# Main-haru funktsionaalse pariteedi audit

## Lähtekoht

Audit võrdleb `main`-haru Spring Booti ja Next.js teostust Django/React ümberkirjutusega. Esimene Django laine kandis üle identiteedi, omanikud, katastriüksused, metsaregistri andmed, meeldetuletused, sõnumid, põhilise lepinguvoo, WFS-sünkroniseerimise ja kaardivaate. `main` sisaldab lisaks uuemat kommertstehingute, pärimisjuhtumite, importimise, integratsioonide ning müügitöö ruumi.

| Maini moodul | Django praegune vaste | Seis | Järgmine töö |
|---|---|---|---|
| Kasutajad, õigused ja sisselogimine | `accounts`, JWT/TOTP, Django grupid | Olemas | Hoida OIDC/Keycloak teadliku järgmise etapina. |
| Omanikud, kinnistud ja töölaud | `forestry`, `api`, töölaudade Reacti vaated | Olemas | Täiendada tehingu- ja müügitöö seostega. |
| Registri- ja WFS-sünkroniseerimine | GeoDjango, Celery, `DataSyncRun` | Olemas | Lisada värskuse juhtpaneel ning käsitsi taastamine. |
| Kaart ja kinnistu ruumiandmed | MapLibre, GeoJSON, PostGIS | Olemas | Siduda tehingute märgitud kinnistud detailvaatega. |
| Kommertstehingud ja hinnastamine | `Deal`, `DealOffer`, hindamis- ja kommerts-API | Olemas | Omanikukaart toetab hindamist, pakkumise saatmist ning võidetud tehingu lepingu drafti. |
| Pärimisjuhtumi käsitlus | `InheritanceCase`, pärijad, sündmused ja teate import | Olemas | Juhtumi staatus, määramine, pärijad ning tööajaloo sündmused on auditeeritavad. |
| Omanike CSV/XLSX import | Kontrollitud inspect/preview/commit ja `OwnerImportBatch` | Olemas | Enne commit’i võrreldakse SHA-256 kinnitust ning vigased read säilivad eraldi. |
| Müügitöö prioriteedijärjekord | `sales-workspace` Django API ja Reacti vaade | Olemas | Standardne kontaktitulemus ning tagasihelistamise järeltegevus loovad meeldetuletuse. |
| Omandimuutuste töövoog | Sündmuse mudel, omanikuvaade ja volitatud portfellisünkroniseerimise alus | Olemas alus | Konkreetne üleminekuallikas jääb opt-in välisteenuseks. |
| Integratsioonide haldus ja andmete värskus | Integratsioonitööde loend, käivitus, värskus ning taastamine | Olemas | Välisteenuse mandaat aktiveerib tegeliku andmepäringu. |

## Sihitud API pariteet

Järgmine laine lisab Django REST API teed, mille semantika järgib `main`-haru olulisi töövooge. Teekonnad hoitakse `api/services/` nimeruumis, et jääda kooskõlla Django ümberkirjutuse kehtiva kliendilepinguga. Iga olekumuutus kontrollib olemasolevaid ForestIQ õigusi ja jätab auditeeritava kirje.

| Töövoog | Django API siht |
|---|---|
| Tehingud | `services/deals/owners/{ownerId}`, `services/deals/{dealId}/commercial` ja hindamisjärjekord |
| Pärimine | `services/inheritance/cases`, juhtumi detail, staatus, määramine, pärijad ning sündmused |
| Omanike import | `services/owners/imports/inspect`, `preview`, `commit`, partii ajalugu ja vigade CSV |
| Müügitöö | `services/sales-workspace/queue` ning `owners/{ownerId}/outcome` |
| Omandimuutus | `services/ownership-transitions/sync` ning omaniku sündmuste loend |
| Integratsioonid | `services/admin/integrations` ja `services/registry/freshness` |

> Arhitektuur hoiab väliste teenuste juurdepääsu opt-in põhimõttel. Esimesena lisatakse töövoogude püsiv mudel, õiguskontroll, auditeerimine ja käsitsi juhitav API. Andmeallika konkreetne klient aktiveeritakse vaid siis, kui vastava teenuse URL ja vähimate õigustega mandaat on seadistatud.

## Teadlikud erinevused

`main` kasutab organisatsioonipõhist Keycloak/OIDC konteksti, S3 dokumendisalvestust ja Springi teenusepiire. Django ümberkirjutus kasutab kasutajate, gruppide ja õiguste lähtepunkti ning lokaalseid lepingufaile vastavalt ümberkirjutuse tehnoloogianõuetele. Seetõttu ei kopeerita Keycloaki administraatoriteenust ega S3 taristut üks-ühele; nende lisamine jääb järgmisse infrastruktuurietappi. Kõik üle toodud töövood kontrollivad siiski samaväärset ForestIQ privileegi, jätavad püsiva auditi ning on REST API kaudu kasutatavad.
