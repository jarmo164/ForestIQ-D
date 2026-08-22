# ForestIQ Django ja PostgreSQL-i migratsioon

## Eesmärk

Java/Spark-põhine `metsis-ee-api` asendatakse **Python 3.11, Django, Django REST Frameworki ja PostgreSQL-i** teenusega. Olemasolev Angulari kasutajaliides jääb eraldi kliendiks, sest see tarbib juba JSON REST-liidest. Django API säilitab URL-i eesliited `api/` ja `api/services/`, JWT päringupäise vormi ning vastuste põhiväljad, et klient saaks üle minna ilma korraga tehtava kasutajaliidese ümberkirjutuseta.

> Migratsioon ei kasuta vana andmebaasi Liquibase'i skeemi Django käivitamisel. Django omab uut skeemi ja migratsioone. Eraldi halduskäsk võimaldab olemasoleva PostgreSQL-andmebaasi andmed kontrollitult üle tuua.

## Rakenduste jaotus

| Django rakendus | Vastutus | Vana teenuseala |
|---|---|---|
| `accounts` | kohandatud kasutaja, õigused, JWT, TOTP ja administraator | `security`, `admin`, `users` |
| `forestry` | omanikud, katastriüksused, metsaandmed, töölauad ja statistika | `owners`, `callerworkdesk`, `evaluatorworkdesk`, `adminworkdesk` |
| `operations` | meeldetuletused, sõnumid, kontaktide väljavõte ja lepingute ajalugu | `reminders`, `messages`, `personsdump`, `contracts` |
| `api` | URL-konfiguratsioon, ühilduvuse vaated, veavorming ja seisukorra kontroll | kõik HTTP-käsitlejad |

## Andmemudel

PostgreSQL on primaarne andmebaas. Mudelid katavad senise skeemi põhientiteed: kasutajad ja õigused, omanikud, katastriüksused, omaniku-katastri seosed, staatuste ajalugu, töökanded, katastrisildid, metsateatised, metsamajandamiskava alamüksused, registriobjektid, meeldetuletused, rakendusesisesed sõnumid, kontaktide register ning lepingute ajalugu. Geomeetria ja väliste registrite mittevormilised atribuudid salvestatakse JSON-ina, et vältida String-serialiseerimisega seotud andmekadu.

## Turve ja ühilduvus

Kasutajaõigused on samad domeeniväärtused nagu senises teenuses: `ADMIN`, `OWNER_PROFILE`, `ASSIGNED_OWNERS`, `PHONES` ja `EVALUATION`. Kõik `api/services/` aadressid nõuavad Bearer JWT-d. Tokenite vastus säilitab vana kliendi jaoks väljad `actualToken.token` ja `refreshToken.token`; JWT sisaldab samuti välju `userId`, `userName` ja `privileges`.

## Andmete üleviimine

Andmete üleviimine toimub pärast uue skeemi loomist eraldi `import_legacy_metsis` halduskäsuga. Käsk loeb vana skeemi eraldi `LEGACY_DATABASE_URL` ühenduse kaudu, kontrollib tabelite olemasolu ja kopeerib andmed idempotentselt. Parooliräsid säilitatakse muutmata kujul, sest Django parooliräsi adapter toetab vana BCrypti vormingut. Enne tootmises ümberlülitust tuleb teha andmebaasi varukoopia, prooviviide ja ridade arvu võrdlus.

## Käivitamine

Kohalik arendus kasutab `docker compose up --build`. Django kuulab konteineris pordil 8000 ja PostgreSQL on eraldi `db` teenus. Vajalikud keskkonnamuutujad on kirjeldatud failis `.env.example`. Arenduskeskkonnas luuakse käsuga `seed_demo_data` minimaalne administraator `autocreated` ning algsed omaniku staatused.

## Katvus ja teadlikult eraldi seadistatavad integratsioonid

Django teisendamine katab kohaliku domeeniloogika ja API lepingu. Välised Maa-ameti, PRIA, metsaregistri ja SIMO ühendused on eraldi seadistatavad adapterid: nende pääsupunktid ja saladused tulevad keskkonnamuutujatest ning puuduvate volituste korral tagastatakse selge teenuse kättesaamatuse viga, mitte vaikiv näiv tulemus.
