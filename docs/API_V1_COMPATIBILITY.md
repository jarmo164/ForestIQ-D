# API v1 ühilduvusmaatriks

## Eesmärk ja tõlgendus

See dokument lukustab ForestIQ Java avalike HTTP- ja WebSocket-liideste pariteediseisu Django ümberkirjutuse versioonitud nimeruumis. Lähteinventar on [`endpoints.md`](../endpoints.md). Märgend **`equivalent`** tähendab, et avalik töövoog on saadaval sama sisulise käitumisega teel `/api/v1`; **`intentional difference`** tähendab teadlikku, dokumenteeritud erinevust; ja **`missing`** tähendab, et täpset avalikku vastet ei ole.

Kõik tabelis olevad HTTP vasted eeldavad tavapärast API juurprefiksit `/api/v1`. Õiguste kontroll ja organisatsiooniisolatsioon jäävad Django API olemasoleva autentimiskihi ülesandeks.

## Pariteediseis

| Java avalik endpoint | Django v1 vaste või seis | Märgend | Selgitus |
|---|---|---|---|
| `POST /password-login` | `POST /password-login` | `equivalent` | Lokaalne kasutajanime/parooli sisselogimine. |
| `POST /token-refresh` | `POST /services/token-refresh` | `equivalent` | JWT värskendus on säilitatud API teenuseruumis. |
| `POST /totp` | `POST /services/totp` | `equivalent` | TOTP sisselogimine on säilitatud API teenuseruumis. |
| `POST /change-my-password` | `POST /services/change-my-password` | `equivalent` | Kasutaja enda parooli muutmine. |
| `GET /admin/users` | `GET /services/admin/users` | `equivalent` | Administraatori kasutajate loend. |
| `POST /admin/users` | `POST /services/admin/users` | `equivalent` | Administraatori kasutaja loomine. |
| `DELETE /admin/users/:user` | `DELETE /services/admin/users/{user_id}` | `equivalent` | Administraatori kasutaja eemaldamine. |
| `POST /admin/users/:user` | `POST /services/admin/users/{user_id}` | `equivalent` | Administraatori kasutaja õiguste muutmine. |
| `GET /admin/userstatistics/owner-status-change` | `GET /services/admin/userstatistics/owner-status-change` | `equivalent` | Omaniku staatuse muudatuste statistika. |
| `GET /admin/userstatistics/prep-data` | `GET /services/admin/userstatistics/prep-data` | `equivalent` | Statistika tööruumi eeltäiteandmed. |
| `GET /owner-statuses` | `GET /services/owner-statuses` | `equivalent` | Omaniku staatuste loend. |
| `DELETE /owner-statuses/:id` | `DELETE /services/owner-statuses/{status_id}` | `equivalent` | Omaniku staatuse eemaldamine. |
| `POST /owner-statuses` | `POST /services/owner-statuses` | `equivalent` | Omaniku staatuse loomine või muutmine. |
| `POST /admin-workdesk/assign` | `POST /services/admin-workdesk/assign` | `equivalent` | Omanike massmääramine. |
| `GET /admin-workdesk/owners-search` | `GET /services/admin-workdesk/owners-search` | `equivalent` | Töölauda toetav omanike otsing. |
| `GET /admin-workdesk/prepare` | `GET /services/admin-workdesk/prepare` | `equivalent` | Töölauda toetavad eeltäiteandmed. |
| `GET /contract-starter` | `GET /services/contract-starter` | `equivalent` | Lepingu algatamise andmed. |
| `GET /contracts` | `GET /services/contracts` | `equivalent` | Lepingute loend. |
| `POST /contracts` | `POST /services/contracts` | `equivalent` | Lepingu salvestamine. |
| `GET /contracts/:id` | `GET /services/contracts/{contract_id}` | `equivalent` | Lepingu detail. |
| `DELETE /contracts/:id` | `DELETE /services/contracts/{contract_id}` | `equivalent` | Lepingu eemaldamine. |
| `GET /contracts/:id/pdf` | `GET /services/contracts/{contract_id}/pdf` | `equivalent` | Lepingu PDF-i allalaadimine. |
| `GET /contracts/suggestors/cadastre/:id` | `GET /services/contracts/suggestors/cadastre/{cadastre_id}` | `equivalent` | Katastriüksuse soovitused. |
| `GET /contracts/cadastre-details/:id` | `GET /services/contracts/cadastre-details/{cadastre_id}` | `equivalent` | Katastriüksuse lepinguandmed. |
| `GET /contracts/suggestors/owner/:id` | `GET /services/contracts/suggestors/owner/{owner_id}` | `equivalent` | Omaniku soovitused. |
| `GET /contracts/owner-details/:id` | `GET /services/contracts/owner-details/{owner_id}` | `equivalent` | Omaniku lepinguandmed. |
| `GET /owners-in-need-of-evaluation` | `GET /services/owners-in-need-of-evaluation` | `equivalent` | Hindamist vajavate omanike järjekord. |
| `DELETE /application-messages/:id` | Puudub | `missing` | Täpset vana rakendussõnumi REST-ressurssi ei ole üle toodud. |
| `WS /application-messages` | Puudub | `missing` | Django ümberkirjutus pakub REST-sõnumeid, mitte samaväärset WebSocketi kanalit. |
| `POST /cadastres/:id/labels/:label` | `POST /services/cadastres/{cadastre_id}/labels/{label}` | `equivalent` | Katastriüksuse märgendi lisamine. |
| `GET /cadastres/:id/labels` | `GET /services/cadastres/{cadastre_id}/labels` | `equivalent` | Katastriüksuse märgendite loend. |
| `DELETE /cadastres/:id/labels/:label` | `DELETE /services/cadastres/{cadastre_id}/labels/{label}` | `equivalent` | Katastriüksuse märgendi eemaldamine. |
| `GET /cadastres/:id/notifications` | `GET /services/cadastres/{cadastre_id}/notifications` | `equivalent` | Metsateatiste loend. |
| `GET /cadastres/:id/mkdata` | `GET /services/cadastres/{cadastre_id}/mkdata` | `equivalent` | Metsaregistri andmed. |
| `GET /cadastres/:id/areas` | `GET /services/cadastres/{cadastre_id}/areas` | `equivalent` | Pindalade andmed. |
| `GET /owners` | `GET /services/owners` | `equivalent` | Omanike otsing ja loend. |
| `GET /owners/:id` | `GET /services/owners/{owner_id}` | `equivalent` | Omaniku detail. |
| `POST /owners/:id` | `POST /services/owners/{owner_id}` | `equivalent` | Omaniku andmete muutmine. |
| `GET /owner/:id/status` | `GET /services/owner/{owner_id}/status` | `equivalent` | Omaniku praegune staatus. |
| `POST /owners/:id/change-status` | `POST /services/owners/{owner_id}/change-status` | `equivalent` | Omaniku staatuse muutmine. |
| `POST /owners/:id/mark-cadastres` | `POST /services/owners/{owner_id}/mark-cadastres` | `equivalent` | Omaniku huvipakkuvate katastriüksuste märkimine. |
| `POST /owners/:id/refresh-cadastres` | `POST /services/registry/cadastres/{cadastre_id}/maaamet/refresh` | `intentional difference` | Vana omanikupõhine välisvärskendus on asendatud auditeeritava administraatori katastriüksusepõhise registrivärskendusega. |
| `POST /owners/:id/add` | `POST /services/owners/{owner_id}/add` | `equivalent` | Omaniku lisamine. |
| `POST /owners/:id/log` | `POST /services/owners/{owner_id}/log` | `equivalent` | Omaniku tööajaloo sissekande loomine. |
| `GET /owners/:id/log` | `GET /services/owners/{owner_id}/log` | `equivalent` | Omaniku tööajaloo loend. |
| `POST /owner/:id/assignee` | `POST /services/owner/{owner_id}/assignee` | `equivalent` | Omaniku määramine kasutajale. |
| `GET /my-work/next-owner` | `GET /services/my-work/next-owner` | `equivalent` | Järgmine määratud omanik. |
| `GET /my-work` | `GET /services/my-work` | `equivalent` | Määratud omanike tööloend. |
| `GET /caller-workdesk-prep-data` | `GET /services/caller-workdesk-prep-data` | `equivalent` | Helistaja töölauda toetavad eeltäiteandmed. |
| `POST /reminders` | `POST /services/reminders` | `equivalent` | Meeldetuletuse loomine. |
| `DELETE /reminders/:id` | `DELETE /services/reminders/{reminder_id}` | `equivalent` | Meeldetuletuse eemaldamine. |
| `GET /reminders` | `GET /services/reminders` | `equivalent` | Kasutaja meeldetuletuste loend. |
| `GET /persons-dump` | `GET /services/persons-dump` | `equivalent` | Õigusega piiratud kontaktide loend. |
| `GET /status` | `GET /services/status` | `equivalent` | Teenuse seisundi kontroll. |

## Lepingu kasutus

`/api/v1/schema/` väljastab sama nimeruumi OpenAPI 3 skeemi. CI genereerib skeemi sellest URL-conf’ist ning võrdleb tulemust versioonihalduses oleva snapshot’iga [`api_contracts/openapi-v1.yaml`](../api_contracts/openapi-v1.yaml). Seetõttu ei saa lepingut muuta märkamatult: iga marsruudi, meetodi või genereeritud OpenAPI sisu muutus katkestab kvaliteedivärava, kuni snapshot muudetakse teadlikult samas pull request’is.

> Maatriks on teadlikult eraldi OpenAPI skeemist. Skeem on täidetav, masinloetav leping; maatriks jäädvustab ka WebSocketi ning teadlikult erineva või puuduva Java liidese seisundi.
