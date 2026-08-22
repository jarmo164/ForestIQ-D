# ForestIQ ruumiandmete allikate märkmed

## Kinnitatud Maa-ameti katastri WFS

Maa-ameti uus katastri WFS-i teenusepõhi on `https://gsavalik.envir.ee/geoserver/kataster/wfs`. Teenuse GetCapabilities päring kasutab WFS 2.0.0 protokolli. Katastriüksuste andmed sisaldavad muu hulgas tunnust, EHAK koodi, maakonda, omavalitsust, asustusüksust, lähiaadressi, registreerimise ja muutmise kuupäevi, pindala, kõlvikuid, omandivormi ning maksustamishinda. Teenuse andmed uuenevad öösiti ning pakuvad CRS-e EPSG:3301, EPSG:3857 ja EPSG:4326.

Maa-amet soovitab vana `maaamet` katastrikaarditeenuse asemel kasutada seda uut `kataster` WFS-i. Laadija peab kasutama väikesemahulisi tunnusepõhiseid `GetFeature` päringuid, piirama `count` väärtust ning töötlema vastuseid EPSG:3301 geomeetriaga.

Tegelik näidisobjekt kihilt `kataster:ky_kehtiv` sisaldas välju `tunnus`, `l_aadress`, `mk_nimi`, `ov_nimi`, `ay_nimi`, `pindala`, `mets`, `haritav`, `rohumaa`, `ouemaa`, `muumaa`, `maks_hind`, `omvorm`, `kinnistu`, `marked`, `muudet` ja `geom_muudet`. Need on ForestIQ `Cadastre` mudeli esmane väljade kaart.

## Kinnitatud metsaregistri WFS

Metsaregistri WFS-i teenusepõhi on `https://gsavalik.envir.ee/geoserver/metsaregister/ows`. ForestIQ jaoks vajalikud kihid on vähemalt `metsaregister:eraldis`, `metsaregister:eraldis_element`, `metsaregister:teatis`, `metsaregister:kahjustused`, `metsaregister:isearasused` ja vajaduse korral `metsaregister:mke`. Kehtiva eraldise näidisobjekt sisaldas välju `id`, `katastri_nr`, `eraldise_nr`, `pindala`, `invent_kp`, `registreerimise_kp`, `peapuuliik_kood`, `kasvukoht_kood`, `keskm_vanus`, `korgus`, `taius_1`, `tagavara_1_ha`, `tagavara_l_ha`, `omandivorm_kood` ja `versioon`.

Metsaregistri eraldised tuleb siduda ForestIQ katastriüksusega `katastri_nr` väärtuse järgi. Kõik algsed atribuudid ja GeoJSON geomeetria säilitatakse `ForestRegistryFeature` mudelis; portfelli koondnäitajaid ei tohi päritoluandmete arvelt üle kirjutada.

## Varasema MetsIS-i töövoo säilitamine

Rewrite-haru eelmine Java teenus küsis katastripõhiselt metsateatisi aadressilt `https://register.metsad.ee/api/rest/teatis/puu?katastriNr={tunnus}&naitaAegunud=true`, teatise detaili aadressilt `https://register.metsad.ee/api/rest/teatis/teatisVaatamine/{id}` ja eraldiste puu aadressilt `https://register.metsad.ee/api/rest/eraldis/puu?katastriNr={tunnus}`. Uus lahendus eelistab avalikku WFS-i, kuid säilitab need REST-i lõpp-punktid konfiguratsioonis valikulise süvitsi värskenduse jaoks, sest need annavad varasemale kasutajaliidesele vajalikud teatiste detailid.

## Forestek ja Weasel

Weaseli OpenAPI leping kirjeldab katastripõhist omanike otsingut `GET /owners?cadastre={tunnus}` ning omanike omandamist `GET /owners/{cadastre}`. Lepingu haldusosa kirjeldab eraldi omanike, katastri, metsateatiste, metsaplaanide ja katastriplaanide sünkroniseerimistoiminguid. ForestIQ adapter käsitleb Foresteki/Weaseli vastust omaniku-katastri seoste autoriteetse sisendina ainult siis, kui seadistatud on dokumenteeritud teenuse URL ja turvaline autentimine. Avalik Foresteki leht nõuab sisselogimist ning seda ei kraabita.

## Pärimus

Pärimuse rakendus pakub tokeniga kaitstud JSON API-t: `GET /api/v1/notices/?personal_code={11-kohaline isikukood}`. Vastus sisaldab teadaande numbrit ja kuupäevi, pärandaja isikukoodi, notari andmeid ning pärijate nime, isikukoodi, registrikoodi ja pärandiosa. ForestIQ päring seob teateid ainult sama täpse 11-kohalise isikukoodi abil ning talletab päritolu URL-i ja JSON-i lähteandmed auditiks.

## Tähelepanek Foresteki kohta

`https://forestek.metsis.io` suunab autentimist nõudvale MetsIS-EE sisselogimisvaatele. Seetõttu ei tohi tausttöö kasutada seda lehte kraapimiseks; omaniku-katastri seoste sünkroniseerimine peab kasutama dokumenteeritud teenusekontot või juba olemasolevat kontrollitud andmeekspordi liidest.

## Viited

1. Maa- ja Ruumiamet, avalikud WMS/WFS teenused: https://geoportaal.maaamet.ee/eng/services/public-wms-wfs-p346.html
2. Eesti katastriüksuste WFS metaandmed: https://metadata.geoportaal.ee/geonetwork/srv/api/records/1591a3f4-a4f2-4dcd-8d1f-3d966eb8655e
3. Katastri kaarditeenuste muudatused: https://kataster.ee/uudised/katastri-kaarditeenuste-muudatused
