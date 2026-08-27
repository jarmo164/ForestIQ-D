# Kriitiliste töövoogude käsitsi kontroll

## MapLibre’i kaart → katastri detail

Playwright katab kaarditööruumi laadimise ja kasutajajuhise. Katastrikihi klikki ning detailakna avamist kontrollitakse praegu käsitsi, sest headless Chromiumi MapLibre’i canvas ei renderda interaktiivseid GeoJSON-kihte järjepidevalt.

| Samm | Kontroll | Oodatud tulemus |
|---|---|---|
| 1 | Sisene ForestIQ arenduskontoga ja ava **Kaart**. | Kuvatakse pealkiri **Metsa- ja katastrivaade** ning kaardil on kihid nähtavad. |
| 2 | Suumi vähemalt tasemele 8 ning oota nähtava ala andmete laadimist. | Katastriüksuste kihi loendur suureneb, kui nähtaval alal on andmeid. |
| 3 | Klõpsa nähtaval katastriüksusel. | Avaneb dialoog **Katastriüksuse detailvaade**. |
| 4 | Kontrolli detailakna kokkuvõtet ja sektsioone. | Kuvatakse katastri, omanike/kliendisuhte, tegevuste, teatiste ja Metsaregistri andmed või nende selged tühjad olekud. |
| 5 | Sulge detailaken. | Kaarditööruum jääb avatuks ning valitud objekti olek ei põhjusta JavaScripti vigu ega uut sisselogimist. |

## Automaatne katvus

Playwrighti `pnpm test:e2e` kontrollib deterministlike API-fixture’idega sisselogimist, hindamine → pakkumine → lepingu draft töövoogu, pärimisjuhtumi töötlust, omanike faili inspect → preview → commit importi, rollikeeldu ning kaarditööruumi esmast laadimist. Vitest katab lisaks õiguste maatriksi ja autentimis-/403-vaadete komponendid.
