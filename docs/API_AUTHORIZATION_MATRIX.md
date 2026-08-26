# ForestIQ-D API autoriseerimismaatriks

**Autor:** Manus AI  
**Kehtivus:** API-04 — objektitaseme õiguste regressioonimaatriks  
**Seis:** rakendatud

## Eesmärk ja põhimõtted

See dokument määratleb ForestIQ-D API organisatsioonipõhise autoriseerimise kontrollitava lepingu. Iga autentitud päring seotakse tokenis oleva aktiivse organisatsiooniliikmesusega. Pärandkasutaja globaalsed Django grupid ei saa anda õigust teise organisatsiooni andmetele.

> Andmekiht filtreerib organisatsioonivälise objekti enne ressursikontrolli. Seetõttu tagastab olemasoleva, kuid teise organisatsiooni kuuluva detailobjekti päring `404`, mitte `403`.

Õiguste klass lõpetab päringu enne objektiotsingut vastusega `403`, kui rollil puudub endpointiperekonna kasutamiseks vajalik privileeg. Seega on mõlemad vastused tahtlikud: `403` tähendab keelatud toimingut, `404` tähendab organisatsioonikontekstis nähtamatut ressurssi.

## Rollide ja domeeniõiguste kaart

| Roll | Tuletatud domeeniõigused | Andmeulatus |
| --- | --- | --- |
| `ORG_OWNER`, `ORG_ADMIN` | `ADMIN`, `OWNER_PROFILE`, `ASSIGNED_OWNERS`, `PHONES`, `EVALUATION` | Kõik oma organisatsiooni töövood, konfiguratsioon ning haldusendpointid. |
| `CRM_MANAGER` | `OWNER_PROFILE`, `ASSIGNED_OWNERS` | Kõik oma organisatsiooni omaniku-, katastri-, tehingu- ja pärimisandmed; haldus ning hindamisjärjekord on keelatud. |
| `EVALUATOR` | `EVALUATION` | Hindamisjärjekord ja ainult talle määratud `Deal`-ide hindamisvoog. Omaniku CRM-detailid ei ole nähtavad. |
| `CALLER` | `ASSIGNED_OWNERS`, `PHONES` | Ainult talle määratud omanikega seotud CRM- ja helistamistöö; teised omanikud jäävad keelatuks. |
| `ORG_MEMBER`, `VIEWER` | puuduvad kirjutamisõigused | Selgelt lubatud üldised lugemis- ja sõnumiendpointid. CRM, hindamine, telefonid ja haldus on keelatud. |

## Endpointiperekondade maatriks

| Endpointiperekond | Lubatud rollid | Objektitaseme reegel | Keelatud või organisatsiooniväline tulemus |
| --- | --- | --- | --- |
| Üldteenus, kaart ja sõnumid | Kõik liikmesusega rollid | Ainult aktiivse organisatsiooni read | `403` rollita kasutajale; organisatsioonivälised read puuduvad tulemusest. |
| Omanikud, katastri tööruum ja CRM | Admin, CRM manager, caller | Admin ja CRM manager näevad kogu organisatsiooni; caller ainult `assignee == request.user` | Puuduv CRM-õigus `403`; teise organisatsiooni detail `404`; callerile määramata oma organisatsiooni omanik `403`. |
| Deal’i hindamisjärjekord | Admin, evaluator | Evaluator näeb ainult talle määratud või määramata hindamisi | Manager, caller ja viewer saavad `403`. |
| Deal’i detail- ja hindamisoperatsioonid | Admin, CRM manager, assigned caller, assigned evaluator | Evaluator pääseb ainult `deal.evaluator == request.user`; CRM/caller ulatus pärineb Owneri kontrollist | Oma organisatsiooni, kuid hindajale määramata Deal `403`; teise organisatsiooni Deal `404`. |
| Pakkumised ja Deal’i sulgemine | Admin, CRM manager, assigned caller | Ulatus pärineb seotud Ownerist | Evaluator ja viewer `403`; teise organisatsiooni Deal `404`. |
| Pärimisjuhtumid | Admin, CRM manager, assigned caller | Ulatus pärineb seotud Ownerist | Keelatud roll `403`; teise organisatsiooni juhtum `404`. |
| Telefonikataloog ja caller-töölaud | Admin, caller | Organisatsioonipõhine ning callerile määratud omaniku ulatus | CRM manager, evaluator ja viewer `403`, kui `PHONES` õigus puudub. |
| Lepingud ja lepingudraftid | Admin | Ainult organisatsiooni lepingud ning seotud Deal’id | Kõik muud rollid `403`; teise organisatsiooni detail `404`. |
| Kasutajate, importide, integratsioonide ja registri haldus | Admin | Ainult organisatsiooni süsteemiread | Kõik muud rollid `403`. |

## Regressioonikontrollid

`django_backend/api/tests.py` sisaldab kahte API-04 testikihti.

| Testiklass | Katvus |
| --- | --- |
| `ObjectAuthorizationMatrixTests` | Käitab admini, CRM manageri, hindaja, helistaja ja vaatleja lubatud/keelatud stsenaariumid üld-, CRM-, hindamis- ning haldusendpointiperekondades. Kontrollib eraldi caller’i määratud omaniku ulatust, hindaja määratud Deal’i ulatust, kirjutusõigusi ning teise organisatsiooni detailobjektide nähtamatust. |
| `EndpointAuthorizationInventoryTests` | Läbib kõik `services/*` URL-id ning katkestab testi, kui äriline endpoint ei deklareeri mitteavalikku õiguste klassi. Ainult TOTP ja tokeni värskendamise autentimisabi route’id on teadlikult avalikus erandiloendis. |

Maatriksis kasutatud viis rolli on testis eksplitsiitselt nimega: `admin`, `manager`, `evaluator`, `caller` ja `viewer`. See väldib olukorda, kus tulevane rollide või endpointide muudatus vähendab märkamatult testkatet.

## Muudatuse kontrollnimekiri

Uue API endpointi lisamisel tuleb täita järgmised tingimused. Endpoint peab kasutama konkreetset `permission_classes` määratlust; organisatsioonilise detailobjekti otsing peab kasutama vaikimisi scoped manager’it; Owneri, Deal’i või InheritanceCase’i töövoog peab kasutama objektiulatuse abifunktsiooni; ning uus endpointiperekond tuleb lisada `ObjectAuthorizationMatrixTests` lubatud, keelatud ja teise organisatsiooni stsenaariumiga.

Kriitilise agregaadi kirjutus peab lisaks järgima API-03 versioonilepingut: kliendi `version` peab vastama salvestatud versioonile, vastasel juhul tagastatakse `409 version_conflict`.
