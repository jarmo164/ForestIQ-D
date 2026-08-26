# Renderi kasutuselevõtt

Projekt sisaldab Render Blueprinti failis [`render.yaml`](../render.yaml). See loob ühe Django API veebiteenuse, ühe Celery workeri, ühe Celery Beati, Render Key Value Redis’e, Render PostgreSQL andmebaasi ning eraldi staatilise MapLibre’i kasutajaliidese.

## Kasutuselevõtu sammud

Renderi töölaual vali **New → Blueprint**, ühenda GitHubi hoidla `jarmo164/ForestIQ-D` ning vali haru `main`. Render loeb hoidla juurfaili `render.yaml`, näitab loodavaid teenuseid ning küsib enne loomist kinnitust.

API eelkäivitus käivitab skripti `scripts/render-predeploy.sh`. Skript aktiveerib Render PostgreSQL andmebaasis PostGIS-i laiendi ja rakendab Django migratsioonid enne Gunicorni käivitamist. Render PostgreSQL toetab PostGIS-i; laiend tuleb igas andmebaasis eraldi aktiveerida käsuga `CREATE EXTENSION postgis`.[1]

## Keskkond ja turve

Blueprint genereerib ühise `DJANGO_SECRET_KEY` väärtuse ning jagab selle API, workeri ja Beati vahel. Andmebaasi ja Redis’e ühendusstringid tulevad teenuste sisemistest viidetest, mitte versioonihalduses olevatest väärtustest. Foresteki ja Pärimuse tokenid jäävad teadlikult Blueprintist välja; kui neid hiljem kasutatakse, lisa need Renderi keskkonnarühma või teenuse keskkonnamuutujatena.

Staatilise kliendi `VITE_API_BASE` on kompileerimisajal API Renderi URL. Kui muudate teenusenimesid või lisate kohandatud domeeni, uuendage koos `VITE_API_BASE`, `DJANGO_CORS_ALLOWED_ORIGINS` ja vajaduse korral `DJANGO_ALLOWED_HOSTS` väärtusi ning käivitage staatilise kliendi uus deploy. Kliendi ja API eraldi domeenide tõttu on Django CORS lubatud ainult eksplitsiitselt määratud päritoludele.

## Failid ja tausttööd

Kohalik lepingufailide salvestus kasutab API veebiteenuse püsiketast `/app/media`. Celery worker ja Beat ei jaga seda ketast; tausttööd ei tohi sellele tugineda dokumentide kirjutamiseks. Horisontaalse skaleerimise või eraldi workerite failikirjutuse vajaduse korral tuleb mediafailid viia S3-ühilduvasse objektisalvestusse.

Celery Beat käivitab metsaregistri CQL-deltakontrolli vaikimisi kord tunnis. Foresteki import on jätkuvalt ühekordne käsitsi algimport ja ei kuulu perioodilisse Renderi töövoogu.

## Käitusjärgne kontroll

Pärast Blueprinti valmimist kontrollige API tervist aadressil `/api/services/status`, looge Django administraator ning avage staatiline kasutajaliides. Esmane suuremahuline metsaregistri import tuleks käivitada kontrollitult workeris või ühekordse halduskäsuna, mitte API HTTP päringu kaudu.

## Viited

[1]: https://render.com/docs/postgresql-extensions "Supported Extensions for Render Postgres"
